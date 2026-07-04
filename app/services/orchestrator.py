import os
import time
import traceback
from typing import Any, Dict, List
from app.models.schemas import ChatMessage, ChatResponse, ScoredDocument
from app.utils.logger import logger
from app.llm.conversation_engine import ConversationEngine
from app.retrieval.semantic import SemanticRetriever
from app.services.policy_engine import PolicyEngine
from app.services.recommendation_selector import RecommendationSelector
from app.services.prompt_manager import PromptManager
from app.services.llm_provider import BaseLLMProvider
from app.services.response_validator import OrchestratorResponseValidator

# DEBUG mode flag — set via environment variable DEBUG=True
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

class AgentOrchestrator:
    """Central agent orchestrator coordinating intent analysis, policy decisions,

    retrieval pipelines, selections, prompt templates, and validation guards.
    """

    def __init__(
        self,
        conversation_engine: ConversationEngine,
        hybrid_retriever: SemanticRetriever,
        selector: RecommendationSelector,
        prompt_manager: PromptManager,
        llm_provider: BaseLLMProvider,
        response_validator: OrchestratorResponseValidator,
        catalog: List[Dict[str, Any]]
    ) -> None:
        self.conversation_engine = conversation_engine
        self.hybrid_retriever = hybrid_retriever
        self.selector = selector
        self.prompt_manager = prompt_manager
        self.llm_provider = llm_provider
        self.response_validator = response_validator
        self.catalog = catalog
        self.policy_engine = PolicyEngine()

    def _debug_log(self, stage: str, data: Dict[str, Any], elapsed: float, success: bool) -> None:
        """Emits detailed pipeline stage trace when DEBUG=True."""
        status = "SUCCESS" if success else "FAILURE"
        logger.info(
            f"[PIPELINE DEBUG] Stage: {stage} | Status: {status} | "
            f"Elapsed: {elapsed:.4f}s | Data: {data}"
        )

    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Executes the orchestrator pipeline over a user dialogue trace."""
        start_time = time.perf_counter()
        retrieval_latency = 0.0
        shortlist: List[ScoredDocument] = []
        pipeline_trace: List[Dict[str, Any]] = []

        # 1. Conversation Engine Context Analysis
        stage = "ConversationEngine"
        t0 = time.perf_counter()
        try:
            context = self.conversation_engine.process_conversation(messages)
            
            # Enforce max turn cap of 8
            user_turn_count = sum(1 for msg in messages if msg.role == "user")
            if user_turn_count >= 8:
                context.conversation_complete = True
                context.needs_clarification = False
                if not context.retrieval_query:
                    from app.models.schemas import RetrievalQuery
                    context.retrieval_query = RetrievalQuery(query_text="Assessment", filters={})
                    
            elapsed = time.perf_counter() - t0
            stage_data = {
                "intent": context.current_intent,
                "role": context.extracted_constraints.role,
                "job_level": context.extracted_constraints.job_level,
                "duration": context.extracted_constraints.duration,
                "assessment_keys": context.extracted_constraints.assessment_keys,
                "needs_clarification": context.needs_clarification,
                "confidence_score": context.confidence_score,
                "retrieval_query": str(context.retrieval_query) if context.retrieval_query else None,
                "missing_constraints": context.missing_constraints,
                "user_turns": user_turn_count
            }
            if DEBUG:
                self._debug_log(stage, stage_data, elapsed, True)
            pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": elapsed, "data": stage_data})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
            pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
            return self.response_validator.get_fallback_response()

        # 2. Thin Policy Engine Routing
        stage = "PolicyEngine"
        t0 = time.perf_counter()
        try:
            policy = self.policy_engine.determine_policy(context)
            elapsed = time.perf_counter() - t0
            stage_data = {"policy": policy}
            if DEBUG:
                self._debug_log(stage, stage_data, elapsed, True)
            pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": elapsed, "data": stage_data})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
            pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
            return self.response_validator.get_fallback_response()

        # Resolve comparison targets to full catalog names for grounding
        if policy == "COMPARISON":
            resolved = []
            # 1. Handle ordinal references (e.g. "compare the first two")
            ordinal_targets = [t for t in context.comparison_targets if t.startswith("__ORDINAL_")]
            if ordinal_targets:
                ordinal_indices = []
                for t in ordinal_targets:
                    parts = t.split("_")
                    if len(parts) >= 3:
                        try:
                            ordinal_indices.append(int(parts[2]) - 1)
                        except ValueError:
                            pass
                if ordinal_indices:
                    # Parse the last assistant message to find previously recommended names
                    last_assistant_msg = None
                    for msg in reversed(messages):
                        if msg.role == "assistant":
                            last_assistant_msg = msg.content
                            break
                    if last_assistant_msg:
                        # Extract recommendation names from assistant reply using known catalog names
                        catalog_name_lower = {item.get("name", "").strip().lower(): item.get("name", "") for item in self.catalog}
                        found_ordered = []
                        content_lower = last_assistant_msg.lower()
                        for cname_lower, cname_actual in catalog_name_lower.items():
                            if cname_lower in content_lower:
                                found_ordered.append(cname_actual)
                        # Return the ones at the requested ordinal positions
                        for idx in ordinal_indices:
                            if idx < len(found_ordered):
                                resolved.append(found_ordered[idx])
            if not resolved:
                # 2. Standard catalog lookup for named targets
                for target in context.comparison_targets:
                    target_lower = target.lower()
                    for item in self.catalog:
                        name_str = item.get("name", "")
                        desc_str = item.get("description", "")
                        if target_lower in name_str.lower() or f"({target_lower})" in desc_str.lower() or f" {target_lower} " in desc_str.lower():
                            resolved.append(name_str)
                            break
            if resolved:
                context.comparison_targets = list(set(resolved))

        # LOOKUP policy: direct catalog search, NO LLM needed — zero hallucination risk
        if policy == "LOOKUP":
            import difflib
            lookup_name = context.retrieval_query.filters.get("__lookup__", "") if context.retrieval_query else ""
            if not lookup_name:
                lookup_name = context.retrieval_query.query_text if context.retrieval_query else ""
            
            catalog_map = {item.get("name", "").strip().lower(): item for item in self.catalog}
            catalog_names_lower = list(catalog_map.keys())
            
            # 1. Exact match
            found_item = catalog_map.get(lookup_name.strip().lower())
            
            # 2. Fuzzy match (strict cutoff to avoid false positives)
            if not found_item:
                closest = difflib.get_close_matches(lookup_name.strip().lower(), catalog_names_lower, n=1, cutoff=0.75)
                if closest:
                    found_item = catalog_map[closest[0]]
            
            # 3. Substring match as last resort
            if not found_item:
                for k, v in catalog_map.items():
                    if lookup_name.strip().lower() in k:
                        found_item = v
                        break
            
            if found_item:
                # Build grounded response directly from catalog data
                name = found_item.get("name", "")
                description = found_item.get("description", "No description available.")
                duration = found_item.get("duration", "Not specified")
                remote = "Yes" if str(found_item.get("remote", "")).lower() == "yes" else "No"
                adaptive = "Yes (Adaptive Engine)" if str(found_item.get("adaptive", "")).lower() == "yes" else "No (Fixed Form)"
                languages = ", ".join(found_item.get("languages", [])) or "Not specified"
                job_levels = ", ".join(found_item.get("job_levels", [])) or "Not specified"
                link = found_item.get("link", "")
                test_type_raw = found_item.get("test_type", "")
                test_type_map = {"K": "Knowledge & Skills", "P": "Personality & Behavior", "A": "Ability/Aptitude", "S": "Simulations"}
                test_type_label = test_type_map.get(test_type_raw, test_type_raw or "Not specified")
                
                reply = (
                    f"Here are the details for **{name}** from the SHL catalog:"
                )
                from app.models.schemas import RecommendationItem
                rec = RecommendationItem(
                    name=name,
                    url=link,
                    test_type=test_type_raw,
                    description=description,
                    duration=duration,
                    adaptive=str(found_item.get("adaptive", "")).lower() == "yes",
                    remote=str(found_item.get("remote", "")).lower() == "yes",
                    languages=found_item.get("languages", []),
                    job_levels=found_item.get("job_levels", [])
                )
                total_latency = time.perf_counter() - start_time
                logger.info(
                    f"Agent Orchestrator turn log | Intent: lookup | Policy: LOOKUP | "
                    f"Retrieval Time: 0.0000s | Selected Assessments: ['{name}'] | "
                    f"Validation Result: SUCCESS | Total Request Time: {total_latency:.4f}s"
                )
                return ChatResponse(reply=reply, recommendations=[rec], end_of_conversation=False)
            else:
                # Assessment not found — explicit not-found response, no hallucination
                total_latency = time.perf_counter() - start_time
                logger.info(
                    f"Agent Orchestrator turn log | Intent: lookup | Policy: LOOKUP | "
                    f"Retrieval Time: 0.0000s | Selected Assessments: [] | "
                    f"Validation Result: NOT_FOUND | Total Request Time: {total_latency:.4f}s"
                )
                not_found_msg = f"I couldn't find **\"{lookup_name}\"** in the SHL catalog. This assessment does not appear to exist. Would you like me to search for similar assessments instead?"
                return ChatResponse(reply=not_found_msg, recommendations=[], end_of_conversation=False)

        # 3. Hybrid Retrieval (if policy permits/requires)
        stage = "HybridRetriever"
        candidates = []
        if policy in ("RECOMMENDATION", "REFINE", "END_CONVERSATION"):
            if context.retrieval_query:
                t0 = time.perf_counter()
                try:
                    candidates = self.hybrid_retriever.query(
                        query=context.retrieval_query.query_text,
                        top_n=10,
                        filters=context.retrieval_query.filters,
                        constraints=context.extracted_constraints
                    )
                    retrieval_latency = time.perf_counter() - t0
                    stage_data = {
                        "query": context.retrieval_query.query_text,
                        "filters": context.retrieval_query.filters,
                        "candidates_returned": len(candidates),
                        "top_3": [c.document.name for c in candidates[:3]],
                    }
                    if DEBUG:
                        self._debug_log(stage, stage_data, retrieval_latency, True)
                    pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": retrieval_latency, "data": stage_data})
                except Exception as e:
                    retrieval_latency = time.perf_counter() - t0
                    logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
                    pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": retrieval_latency, "error": str(e)})
                    return self.response_validator.get_fallback_response()
            else:
                if DEBUG:
                    self._debug_log(stage, {"skipped": True, "reason": "No retrieval_query"}, 0.0, True)
                pipeline_trace.append({"stage": stage, "status": "SKIPPED", "elapsed": 0.0})
        else:
            if DEBUG:
                self._debug_log(stage, {"skipped": True, "reason": f"Policy={policy}"}, 0.0, True)
            pipeline_trace.append({"stage": stage, "status": "SKIPPED", "elapsed": 0.0})

        # 4. RecommendationSelector
        stage = "RecommendationSelector"
        did_retrieval = policy in ("RECOMMENDATION", "REFINE", "END_CONVERSATION") and context.retrieval_query is not None
        shortlist = []
        if candidates:
            t0 = time.perf_counter()
            try:
                shortlist = self.selector.select_shortlist(candidates, context.extracted_constraints)
                elapsed = time.perf_counter() - t0
                stage_data = {
                    "shortlist_count": len(shortlist),
                    "names": [s.document.name for s in shortlist],
                }
                if DEBUG:
                    self._debug_log(stage, stage_data, elapsed, True)
                pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": elapsed, "data": stage_data})
            except Exception as e:
                elapsed = time.perf_counter() - t0
                logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
                pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
                return self.response_validator.get_fallback_response()
        else:
            if DEBUG:
                self._debug_log(stage, {"skipped": True, "reason": "No candidates"}, 0.0, True)
            pipeline_trace.append({"stage": stage, "status": "SKIPPED", "elapsed": 0.0})

        # Post-retrieval confidence checks (runs even on empty candidates to trigger clarification)
        if did_retrieval:
            context = self.conversation_engine.refine_with_retrieval(context, shortlist)
            if context.needs_clarification:
                policy = "CLARIFICATION"
                shortlist = []
                if DEBUG:
                    logger.info(f"[PIPELINE DEBUG] Post-retrieval refinement switched policy to CLARIFICATION")

        # 5. Construct grounded prompts via PromptManager
        stage = "PromptManager"
        t0 = time.perf_counter()
        try:
            prompt = self.prompt_manager.construct_prompt(context, shortlist, policy)
            elapsed = time.perf_counter() - t0
            stage_data = {"prompt_length": len(prompt), "policy": policy}
            if DEBUG:
                self._debug_log(stage, stage_data, elapsed, True)
            pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": elapsed, "data": stage_data})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
            pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
            return self.response_validator.get_fallback_response()

        # 6. Generate Response via LLM Provider Abstraction
        stage = "OpenRouterProvider"
        t0 = time.perf_counter()
        try:
            response = self.llm_provider.generate_response(prompt, shortlist, policy, context)
            elapsed = time.perf_counter() - t0
            stage_data = {
                "reply_preview": response.reply[:150],
                "recommendations_count": len(response.recommendations),
                "end_of_conversation": response.end_of_conversation,
            }
            if DEBUG:
                self._debug_log(stage, stage_data, elapsed, True)
            pipeline_trace.append({"stage": stage, "status": "SUCCESS", "elapsed": elapsed, "data": stage_data})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
            pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
            return self.response_validator.get_fallback_response()

        # 7. Response Validation and Fallback Check
        stage = "ResponseValidator"
        t0 = time.perf_counter()
        try:
            is_valid = self.response_validator.validate(response, self.catalog, context, policy)
            elapsed = time.perf_counter() - t0
            stage_data = {"is_valid": is_valid, "recommendations_count": len(response.recommendations)}
            if DEBUG:
                self._debug_log(stage, stage_data, elapsed, is_valid)
            pipeline_trace.append({"stage": stage, "status": "SUCCESS" if is_valid else "VALIDATION_FAILED", "elapsed": elapsed, "data": stage_data})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[PIPELINE FAIL] {stage}: {e}\n{traceback.format_exc()}")
            pipeline_trace.append({"stage": stage, "status": "FAILURE", "elapsed": elapsed, "error": str(e)})
            is_valid = False

        if not is_valid:
            logger.warning("Agent response failed validation grounding checks. Swapping with safety fallback.")
            response = self.response_validator.get_fallback_response()
            validation_result = "FAILED"
        else:
            validation_result = "SUCCESS"

        # Deterministic grounding fallback: if LLM response has no grounded recommendations
        # but we have a valid shortlist, repopulate directly from the shortlist (zero hallucination).
        if (
            policy in ("RECOMMENDATION", "REFINE", "END_CONVERSATION")
            and len(response.recommendations) == 0
            and shortlist
        ):
            logger.warning(
                "LLM recommendations were all dropped by grounding validator. "
                "Falling back to deterministic shortlist-based recommendations."
            )
            from app.models.schemas import RecommendationItem
            grounded_recs = []
            for doc in shortlist:
                keys = doc.document.keys
                test_type = "K"
                if "Personality & Behavior" in keys:
                    test_type = "P"
                elif "Ability & Aptitude" in keys:
                    test_type = "A"
                elif "Simulations" in keys:
                    test_type = "S"
                grounded_recs.append(
                    RecommendationItem(
                        name=doc.document.name,
                        url=doc.document.link,
                        test_type=test_type,
                        description=doc.document.description,
                        duration=doc.document.duration,
                        adaptive=doc.document.adaptive == "yes",
                        remote=doc.document.remote == "yes",
                        languages=doc.document.languages,
                        job_levels=doc.document.job_levels,
                    )
                )
            response.recommendations = grounded_recs
            fallback_msg = self.response_validator.get_fallback_response().reply
            if response.reply == fallback_msg or "I encountered an issue verifying" in response.reply:
                response.reply = "Here are the recommended assessments from the SHL catalog matching your requirements:"
            validation_result = "SHORTLIST_GROUNDED"

        total_latency = time.perf_counter() - start_time

        # 8. Log structured latency and pipeline decisions
        selected_names = [item.document.name for item in shortlist]
        logger.info(
            f"Agent Orchestrator turn log | "
            f"Intent: {context.current_intent} | "
            f"Policy: {policy} | "
            f"Retrieval Time: {retrieval_latency:.4f}s | "
            f"Selected Assessments: {selected_names} | "
            f"Validation Result: {validation_result} | "
            f"Total Request Time: {total_latency:.4f}s"
        )

        # DEBUG: Emit full pipeline trace
        if DEBUG:
            logger.info(f"[PIPELINE TRACE] Full trace: {pipeline_trace}")

        # Enforce structural integrity over LLM outputs based on the policy state machine
        if policy == "END_CONVERSATION":
            response.end_of_conversation = True
        else:
            response.end_of_conversation = False

        return response
