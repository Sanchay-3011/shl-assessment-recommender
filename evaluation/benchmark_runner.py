import os
import json
import time
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.orchestrator import AgentOrchestrator
from evaluation.metrics import (
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    calculate_accuracy,
    calculate_grounding_metrics,
    verify_response_completeness,
    calculate_recommendation_coverage,
    ndcg_at_k
)

# Global spy slots
spy_data = {
    "intent": None,
    "policy": None,
    "candidates": [],
    "shortlist": []
}

original_chat = AgentOrchestrator.chat

def spy_orchestrator_chat(self, messages):
    global spy_data
    # Capture intermediate state
    ctx = self.conversation_engine.process_conversation(messages)
    policy = self.policy_engine.determine_policy(ctx)
    
    candidates = []
    shortlist = []
    if policy in ("RECOMMENDATION", "REFINE", "END_CONVERSATION") and ctx.retrieval_query:
        candidates = self.hybrid_retriever.query(
            query=ctx.retrieval_query.query_text,
            top_n=10,
            filters=ctx.retrieval_query.filters,
            constraints=ctx.extracted_constraints
        )
        shortlist = self.selector.select_shortlist(candidates, ctx.extracted_constraints)
        ctx = self.conversation_engine.refine_with_retrieval(ctx, shortlist)
        if ctx.needs_clarification:
            policy = "CLARIFICATION"
            shortlist = []
            
    spy_data["intent"] = ctx.current_intent
    spy_data["policy"] = policy
    spy_data["candidates"] = [c.document.name for c in candidates]
    spy_data["shortlist"] = [s.document.name for s in shortlist]
    
    return original_chat(self, messages)

class BenchmarkRunner:
    def __init__(self, dataset_path: str = "evaluation/datasets/benchmark_dataset.json", catalog_path: str = "data/shl_assessment_catalog.md") -> None:
        os.environ["GROQ_MODEL"] = "llama-3.3-70b-versatile"
        os.environ["GROQ_API_KEY"] = "gsk_dummy_test_key_for_routing"
        
        self.dataset_path = dataset_path
        self.catalog_path = catalog_path
        self.client = TestClient(app)
        self.catalog_names = set()
        self.catalog_urls = set()
        self._load_catalog()

    def _load_catalog(self) -> None:
        if os.path.exists(self.catalog_path):
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple regex parser for markdown catalog to get names and urls
            import re
            blocks = content.split("## Assessment")
            for block in blocks[1:]:
                name_match = re.search(r'- \*\*Name:\*\* (.*?)\n', block)
                link_match = re.search(r'- \*\*Link:\*\* (.*?)\n', block)
                if name_match:
                    name = name_match.group(1).strip()
                    if name:
                        self.catalog_names.add(name)
                if link_match:
                    url = link_match.group(1).strip()
                    if url:
                        self.catalog_urls.add(url)

    def run_benchmark(self) -> Dict[str, Any]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)

        traces = []
        failures = []
        
        # Patch orchestrator to spy on pipeline properties
        with patch.object(AgentOrchestrator, "chat", spy_orchestrator_chat):
            for case in scenarios:
                global spy_data
                spy_data = {
                    "intent": None,
                    "policy": None,
                    "candidates": [],
                    "shortlist": []
                }
                
                # Execute E2E HTTP turn
                t0 = time.perf_counter()
                response = self.client.post("/chat", json={"messages": case["messages"]})
                total_latency = time.perf_counter() - t0
                
                status_code = response.status_code
                reply = ""
                recs = []
                end_of_convo = False
                
                if status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "")
                    recs = data.get("recommendations", [])
                    end_of_convo = data.get("end_of_conversation", False)
                
                # Capture metrics outputs
                intent_pred = spy_data["intent"] or "unknown"
                policy_pred = spy_data["policy"] or "unknown"
                candidates_pred = spy_data["candidates"]
                shortlist_pred = spy_data["shortlist"]
                
                # Expected values
                intent_exp = case.get("expected_intent")
                policy_exp = case.get("expected_policy")
                recommendations_exp = case.get("expected_recommendations", [])
                
                # Compute retrieval metrics
                rec10 = recall_at_k(candidates_pred, recommendations_exp, 10)
                prec5 = precision_at_k(candidates_pred, recommendations_exp, 5)
                mrr = mean_reciprocal_rank(candidates_pred, recommendations_exp)
                ndcg10 = ndcg_at_k(candidates_pred, recommendations_exp, 10)
                relevant_retrieved = list(set(candidates_pred).intersection(recommendations_exp))
                relevant_missed = list(set(recommendations_exp) - set(candidates_pred))
                ranking_positions = {item: candidates_pred.index(item) + 1 for item in recommendations_exp if item in candidates_pred}
                
                # Compute grounding and completeness metrics
                grounding = calculate_grounding_metrics(recs, self.catalog_names, self.catalog_urls, set(shortlist_pred))
                completeness = verify_response_completeness(reply, recs)
                coverage = calculate_recommendation_coverage(recs, recommendations_exp)
                
                # Success criteria
                success = (
                    (intent_pred == intent_exp) and
                    (policy_pred == policy_exp) and
                    (grounding["hallucination_rate"] == 0.0) and
                    (grounding["invalid_url_rate"] == 0.0) and
                    (completeness == 1.0)
                )
                
                if not success:
                    # Failure analysis documentation
                    fail_info = {
                        "scenario_id": case["id"],
                        "conversation": case["messages"],
                        "expected_behavior": f"Intent: {intent_exp} | Policy: {policy_exp} | Expected Recommendations: {recommendations_exp}",
                        "actual_behavior": f"Intent: {intent_pred} | Policy: {policy_pred} | Recommendations: {[r.get('name') for r in recs]} | Grounding: {grounding}",
                        "root_cause": "Mismatch between predicted intent/policy or validation error.",
                        "suggested_fix": "Refine the slot extraction vocabulary or update the policy rules."
                    }
                    failures.append(fail_info)

                trace = {
                    "id": case["id"],
                    "scenario": case["scenario"],
                    "latency": total_latency,
                    "status_code": status_code,
                    "success": success,
                    "intent": {
                        "expected": intent_exp,
                        "predicted": intent_pred
                    },
                    "policy": {
                        "expected": policy_exp,
                        "predicted": policy_pred
                    },
                    "retrieval": {
                        "candidates": candidates_pred,
                        "expected": recommendations_exp,
                        "recall_at_10": rec10,
                        "precision_at_5": prec5,
                        "mrr": mrr,
                        "ndcg_at_10": ndcg10,
                        "candidate_pool_size": len(candidates_pred),
                        "relevant_retrieved": relevant_retrieved,
                        "relevant_missed": relevant_missed,
                        "ranking_positions": ranking_positions
                    },
                    "grounding": {
                        "hallucination_rate": grounding["hallucination_rate"],
                        "invalid_url_rate": grounding["invalid_url_rate"],
                        "grounding_success_rate": grounding["grounding_success_rate"]
                    },
                    "completeness": completeness,
                    "coverage": coverage
                }
                traces.append(trace)

        # Aggregate summary metrics
        total_cases = len(scenarios)
        successful_cases = sum(1 for t in traces if t["success"])
        
        # Conversation accuracies
        intent_acc = calculate_accuracy([t["intent"]["predicted"] for t in traces], [t["intent"]["expected"] for t in traces])
        policy_acc = calculate_accuracy([t["policy"]["predicted"] for t in traces], [t["policy"]["expected"] for t in traces])
        
        # Filter sub-policy accuracy
        clarification_cases = [t for t in traces if t["scenario"] == "clarification"]
        clarification_acc = calculate_accuracy([t["policy"]["predicted"] for t in clarification_cases], [t["policy"]["expected"] for t in clarification_cases]) if clarification_cases else 1.0
        
        comparison_cases = [t for t in traces if t["scenario"] == "comparison"]
        comparison_acc = calculate_accuracy([t["policy"]["predicted"] for t in comparison_cases], [t["policy"]["expected"] for t in comparison_cases]) if comparison_cases else 1.0
        
        refinement_cases = [t for t in traces if t["scenario"] == "refinement"]
        refinement_acc = calculate_accuracy([t["policy"]["predicted"] for t in refinement_cases], [t["policy"]["expected"] for t in refinement_cases]) if refinement_cases else 1.0

        # Retrieval quality (Exclude non-retrieval scenarios like out of scope / greeting where expected is empty)
        retrieval_active_cases = [t for t in traces if t["retrieval"]["expected"]]
        if retrieval_active_cases:
            avg_recall10 = sum(t["retrieval"]["recall_at_10"] for t in retrieval_active_cases) / len(retrieval_active_cases)
            avg_precision5 = sum(t["retrieval"]["precision_at_5"] for t in retrieval_active_cases) / len(retrieval_active_cases)
            avg_mrr = sum(t["retrieval"]["mrr"] for t in retrieval_active_cases) / len(retrieval_active_cases)
            avg_ndcg10 = sum(t["retrieval"]["ndcg_at_10"] for t in retrieval_active_cases) / len(retrieval_active_cases)
        else:
            avg_recall10, avg_precision5, avg_mrr, avg_ndcg10 = 1.0, 1.0, 1.0, 1.0
        
        avg_hallucination = sum(t["grounding"]["hallucination_rate"] for t in traces) / total_cases
        avg_invalid_url = sum(t["grounding"]["invalid_url_rate"] for t in traces) / total_cases
        avg_grounding_success = sum(t["grounding"]["grounding_success_rate"] for t in traces) / total_cases
        
        avg_completeness = sum(t["completeness"] for t in traces) / total_cases
        avg_coverage = sum(t["coverage"] for t in traces) / total_cases
        
        # Latency statistics
        latencies = [t["latency"] for t in traces]
        avg_latency = float(np.mean(latencies)) if latencies else 0.0
        p50_latency = float(np.percentile(latencies, 50)) if latencies else 0.0
        p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
        max_latency = float(np.max(latencies)) if latencies else 0.0
        
        overall_success_rate = successful_cases / total_cases if total_cases > 0 else 0.0

        summary = {
            "total_scenarios": total_cases,
            "successful_scenarios": successful_cases,
            "overall_success_rate": overall_success_rate,
            "conversation_accuracy": {
                "intent_accuracy": intent_acc,
                "policy_accuracy": policy_acc,
                "clarification_accuracy": clarification_acc,
                "comparison_accuracy": comparison_acc,
                "refinement_accuracy": refinement_acc
            },
            "retrieval_quality": {
                "recall_at_10": avg_recall10,
                "precision_at_5": avg_precision5,
                "mrr": avg_mrr,
                "ndcg_at_10": avg_ndcg10
            },
            "grounding_quality": {
                "hallucination_rate": avg_hallucination,
                "invalid_url_rate": avg_invalid_url,
                "grounding_success_rate": avg_grounding_success
            },
            "response_quality": {
                "response_completeness": avg_completeness,
                "recommendation_coverage": avg_coverage
            },
            "latency": {
                "average_total_latency_sec": avg_latency,
                "p50_latency_sec": p50_latency,
                "p95_latency_sec": p95_latency,
                "max_latency_sec": max_latency
            },
            "failures": failures,
            "traces": traces
        }

        # Save trace logs to datasets directory
        with open("evaluation/datasets/official_traces.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        with open("evaluation/datasets/synthetic_traces.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Generate retrieval failure analysis markdown report
        failed_retrieval_cases = [t for t in retrieval_active_cases if t["retrieval"]["recall_at_10"] < 1.0]
        md_lines = [
            "# Retrieval Failure Analysis Report",
            "",
            f"**Total Retrieval Active Cases**: {len(retrieval_active_cases)}",
            f"**Failed Retrieval Cases (Recall@10 < 100%)**: {len(failed_retrieval_cases)}",
            "",
            "| Scenario ID | Original Query | Expected Assessments | Retrieved (Top 10) | Missed Relevant | Pipeline Stage Responsible | Recommended Fix |",
            "|---|---|---|---|---|---|---|",
        ]
        for t in failed_retrieval_cases:
            messages = next((c["messages"] for c in scenarios if c["id"] == t["id"]), [])
            user_msg = messages[-1]["content"] if messages else ""
            
            expected = ", ".join(t["retrieval"]["expected"])
            retrieved = ", ".join(t["retrieval"]["candidates"])
            missed = ", ".join(t["retrieval"]["relevant_missed"])
            
            md_lines.append(
                f"| {t['id']} | {user_msg} | {expected} | {retrieved} | {missed} | "
                f"HybridRetriever / Filtering | Relax hard filtering constraints on metadata attributes. |"
            )
            
        reports_dir = "evaluation/reports"
        os.makedirs(reports_dir, exist_ok=True)
        with open(os.path.join(reports_dir, "retrieval_failure_analysis.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        with open("evaluation/reports/latest_run.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

if __name__ == "__main__":
    runner = BenchmarkRunner()
    results = runner.run_benchmark()
    print("Benchmark run complete. Success rate:", results["overall_success_rate"])
