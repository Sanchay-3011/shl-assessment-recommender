from typing import Any, Dict, List
from app.models.schemas import ChatResponse, ConversationContext
from app.utils.logger import logger

class OrchestratorResponseValidator:
    """Safeguards generated responses against catalog mappings and schema boundary rules."""

    def validate(
        self,
        response: ChatResponse,
        catalog: List[Dict[str, Any]],
        context: ConversationContext,
        policy: str
    ) -> bool:
        """Validates recommended items, lengths, and targets, returning True if safe."""
        logger.info("Running ResponseValidator validation pipeline...")

        # 1. Enforce Pydantic schema types
        if not isinstance(response, ChatResponse):
            logger.error("Validation Error: Response is not a valid ChatResponse instance.")
            return False

        # 2. recommendation count limit check (<= 10)
        recs = response.recommendations
        if recs and len(recs) > 10:
            logger.error(f"Validation Error: recommendations list length {len(recs)} exceeds 10 limit.")
            return False

        valid_names_map = {item.get("name", "").strip().lower(): item for item in catalog}
        valid_names_list = list(valid_names_map.keys())
        import difflib

        # 3. Grounding checks for each recommended assessment
        for item in recs:
            if not item.name or not item.url:
                logger.error("Validation Error: Recommendation item is missing required name or url.")
                return False

            name_norm = item.name.strip().lower()

            if name_norm not in valid_names_map:
                # Try fuzzy match with a generous cutoff to handle minor LLM name variations
                closest = difflib.get_close_matches(name_norm, valid_names_list, n=1, cutoff=0.82)
                if closest:
                    matched_key = closest[0]
                    correct_item = valid_names_map[matched_key]
                    logger.warning(f"Validation Warning: Fuzzy matched '{item.name}' to '{correct_item['name']}'")
                    item.name = correct_item.get("name", item.name)
                    item.url = correct_item.get("link", item.url)
                else:
                    # Try substring match — if catalog name contains the recommended name or vice-versa
                    substr_match = next(
                        (k for k in valid_names_list if name_norm in k or k in name_norm),
                        None
                    )
                    if substr_match:
                        correct_item = valid_names_map[substr_match]
                        logger.warning(f"Validation Warning: Substring matched '{item.name}' to '{correct_item['name']}'")
                        item.name = correct_item.get("name", item.name)
                        item.url = correct_item.get("link", item.url)
                    else:
                        logger.warning(f"Validation Warning: Could not ground '{item.name}' — dropping from recommendations.")
                        # Mark for removal rather than failing the whole response
                        item.name = "__DROP__"
            else:
                correct_item = valid_names_map[name_norm]
                item.name = correct_item.get("name", item.name)
                item.url = correct_item.get("link", item.url)
                
            if item.name != "__DROP__" and 'correct_item' in locals():
                item.description = correct_item.get("description")
                item.duration = correct_item.get("duration")
                item.adaptive = True if str(correct_item.get("adaptive", "")).lower() == "yes" else False
                item.remote = True if str(correct_item.get("remote", "")).lower() == "yes" else False
                item.languages = correct_item.get("languages", [])
                item.job_levels = correct_item.get("job_levels", [])

        # 4. Remove any items that couldn't be grounded
        response.recommendations = [r for r in response.recommendations if r.name != "__DROP__"]

        # 5. Validate comparison targets exist in catalog
        if policy == "COMPARISON":
            for target in context.comparison_targets:
                target_lower = target.lower()
                matched = any(target_lower in name for name in valid_names_map)
                if not matched:
                    logger.warning(f"Validation Error: Comparison target '{target}' could not be matched in catalog. Relaxing validation.")

        logger.info("Orchestrator validation completed successfully.")
        return True

    def get_fallback_response(self) -> ChatResponse:
        """Returns a deterministic safe response on validation failures."""
        return ChatResponse(
            reply="I encountered an issue verifying the recommendation details. What specific skill or seniority level are you targeting?",
            recommendations=[],
            end_of_conversation=False
        )
