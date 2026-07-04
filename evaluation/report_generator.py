import json
import os
from typing import Dict, Any

class ReportGenerator:
    def __init__(self, trace_path: str = "evaluation/datasets/official_traces.json") -> None:
        self.trace_path = trace_path

    def generate_reports(self) -> None:
        if not os.path.exists(self.trace_path):
            print(f"Error: Trace file not found at {self.trace_path}. Run the benchmark first.")
            return

        with open(self.trace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Print Console Dashboard
        console_report = self._build_console_report(data)
        print(console_report)

        # 2. Write Markdown report
        md_report = self._build_markdown_report(data)
        with open("evaluation/reports/evaluation_report.md", "w", encoding="utf-8") as f:
            f.write(md_report)

        # 3. Write JSON report
        json_report = {
            "total_scenarios": data["total_scenarios"],
            "successful_scenarios": data["successful_scenarios"],
            "overall_success_rate": data["overall_success_rate"],
            "conversation_accuracy": data["conversation_accuracy"],
            "retrieval_quality": data["retrieval_quality"],
            "grounding_quality": data["grounding_quality"],
            "response_quality": data["response_quality"],
            "latency": data["latency"]
        }
        with open("evaluation/reports/evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=2)

        # 4. Write CSV report
        csv_report = self._build_csv_report(data)
        with open("evaluation/reports/evaluation_report.csv", "w", encoding="utf-8") as f:
            f.write(csv_report)

        print("Reports exported successfully to evaluation/reports/evaluation_report.md, evaluation_report.json, and evaluation_report.csv.")

    def _build_console_report(self, data: Dict[str, Any]) -> str:
        convo = data.get("conversation_accuracy", {})
        retrieval = data.get("retrieval_quality", {})
        grounding = data.get("grounding_quality", {})
        quality = data.get("response_quality", {})
        latency = data.get("latency", {})

        intent_accuracy = convo.get("intent_accuracy", 0.0)
        policy_accuracy = convo.get("policy_accuracy", 0.0)
        clarification_acc = convo.get("clarification_accuracy", 0.0)
        comparison_acc = convo.get("comparison_accuracy", 0.0)
        refinement_acc = convo.get("refinement_accuracy", 0.0)

        recall_at_10 = retrieval.get("recall_at_10", 0.0)
        precision_at_5 = retrieval.get("precision_at_5", 0.0)
        mrr = retrieval.get("mrr", 0.0)
        ndcg_at_10 = retrieval.get("ndcg_at_10", 0.0)

        hallucination_rate = grounding.get("hallucination_rate", 0.0)
        invalid_url_rate = grounding.get("invalid_url_rate", 0.0)
        grounding_success_rate = grounding.get("grounding_success_rate", 0.0)

        response_completeness = quality.get("response_completeness", data.get("response_completeness", 0.0))
        recommendation_coverage = quality.get("recommendation_coverage", 0.0)

        average_latency = latency.get("average_total_latency_sec", 0.0)
        p50_latency = latency.get("p50_latency_sec", 0.0)
        p95_latency = latency.get("p95_latency_sec", 0.0)
        max_latency = latency.get("max_latency_sec", 0.0)

        lines = [
            "=========================================================",
            "             SHL RECOMMITTER AI EVALUATION REPORT        ",
            "=========================================================",
            f"Total Scenarios Run   : {data.get('total_scenarios', 0)}",
            f"Successful Scenarios : {data.get('successful_scenarios', 0)}",
            f"Overall Success Rate : {data.get('overall_success_rate', 0.0) * 100:.2f}%",
            "---------------------------------------------------------",
            "CONVERSATION QUALITY",
            f"  Intent Accuracy     : {intent_accuracy * 100:.2f}%",
            f"  Policy Accuracy     : {policy_accuracy * 100:.2f}%",
            f"  Clarification Acc   : {clarification_acc * 100:.2f}%",
            f"  Comparison Acc      : {comparison_acc * 100:.2f}%",
            f"  Refinement Acc      : {refinement_acc * 100:.2f}%",
            "---------------------------------------------------------",
            "RETRIEVAL QUALITY (RETRIEVAL-ACTIVE CASES)",
            f"  Recall@10           : {recall_at_10 * 100:.2f}%",
            f"  Precision@5         : {precision_at_5 * 100:.2f}%",
            f"  MRR                 : {mrr:.4f}",
            f"  NDCG@10             : {ndcg_at_10 * 100:.2f}%",
            "---------------------------------------------------------",
            "GROUNDING QUALITY",
            f"  Hallucination Rate  : {hallucination_rate * 100:.2f}%",
            f"  Invalid URL Rate    : {invalid_url_rate * 100:.2f}%",
            f"  Grounding Success   : {grounding_success_rate * 100:.2f}%",
            "---------------------------------------------------------",
            "RESPONSE QUALITY",
            f"  Completeness Rate   : {response_completeness * 100:.2f}%",
            f"  Recomm. Coverage    : {recommendation_coverage * 100:.2f}%",
            "---------------------------------------------------------",
            "PERFORMANCE LATENCY",
            f"  Avg Latency         : {average_latency:.4f}s",
            f"  P50 Latency         : {p50_latency:.4f}s",
            f"  P95 Latency         : {p95_latency:.4f}s",
            f"  Max Latency         : {max_latency:.4f}s",
            "========================================================="
        ]
        return "\n".join(lines)

    def _build_markdown_report(self, data: Dict[str, Any]) -> str:
        convo = data.get("conversation_accuracy", {})
        retrieval = data.get("retrieval_quality", {})
        grounding = data.get("grounding_quality", {})
        quality = data.get("response_quality", {})
        latency = data.get("latency", {})
        failures = data.get("failures", [])

        intent_accuracy = convo.get("intent_accuracy", 0.0)
        policy_accuracy = convo.get("policy_accuracy", 0.0)
        clarification_acc = convo.get("clarification_accuracy", 0.0)
        comparison_acc = convo.get("comparison_accuracy", 0.0)
        refinement_acc = convo.get("refinement_accuracy", 0.0)

        recall_at_10 = retrieval.get("recall_at_10", 0.0)
        precision_at_5 = retrieval.get("precision_at_5", 0.0)
        mrr = retrieval.get("mrr", 0.0)
        ndcg_at_10 = retrieval.get("ndcg_at_10", 0.0)

        hallucination_rate = grounding.get("hallucination_rate", 0.0)
        invalid_url_rate = grounding.get("invalid_url_rate", 0.0)
        grounding_success_rate = grounding.get("grounding_success_rate", 0.0)

        response_completeness = quality.get("response_completeness", data.get("response_completeness", 0.0))
        recommendation_coverage = quality.get("recommendation_coverage", 0.0)

        average_latency = latency.get("average_total_latency_sec", 0.0)
        p50_latency = latency.get("p50_latency_sec", 0.0)
        p95_latency = latency.get("p95_latency_sec", 0.0)
        max_latency = latency.get("max_latency_sec", 0.0)

        md = f"""# SHL Assessment Recommender AI Evaluation Report

## Executive Summary

| Metric | Target | Value |
|---|---|---|
| **Total Scenarios** | - | {data.get('total_scenarios', 0)} |
| **Successful Scenarios** | - | {data.get('successful_scenarios', 0)} |
| **Overall End-to-End Success Rate** | 100.0% | **{data.get('overall_success_rate', 0.0) * 100:.2f}%** |

---

## Metric Breakdowns

### 1. Conversation Quality

* **Intent Prediction Accuracy**: {intent_accuracy * 100:.2f}%
* **Policy Engine Accuracy**: {policy_accuracy * 100:.2f}%
* **Clarification Sub-Accuracy**: {clarification_acc * 100:.2f}%
* **Comparison Sub-Accuracy**: {comparison_acc * 100:.2f}%
* **Refinement Sub-Accuracy**: {refinement_acc * 100:.2f}%

### 2. Retrieval Quality (Evaluated on Retrieval-Active Queries)

* **Recall@10**: {recall_at_10 * 100:.2f}%
* **Precision@5**: {precision_at_5 * 100:.2f}%
* **Mean Reciprocal Rank (MRR)**: {mrr:.4f}
* **NDCG@10**: {ndcg_at_10 * 100:.2f}%

### 3. Grounding and Integrity

* **Hallucination Rate** *(Target: 0%)*: {hallucination_rate * 100:.2f}%
* **Invalid Link URL Rate** *(Target: 0%)*: {invalid_url_rate * 100:.2f}%
* **Grounding Success Rate** *(Target: 100%)*: {grounding_success_rate * 100:.2f}%

### 4. Response & Recommendation Format Quality

* **Response Completeness Rate**: {response_completeness * 100:.2f}%
* **Recommendation Coverage**: {recommendation_coverage * 100:.2f}%

### 5. Execution Performance

* **Average Latency**: {average_latency:.4f} seconds
* **P50 Latency (Median)**: {p50_latency:.4f} seconds
* **P95 Latency**: {p95_latency:.4f} seconds
* **Maximum Latency**: {max_latency:.4f} seconds

---

## Failure Analysis

"""
        if not failures:
            md += "> [!NOTE]\n> **No failed scenarios detected.** The system successfully met all E2E specifications with 100% success rate.\n"
        else:
            for idx, fail in enumerate(failures, 1):
                md += f"""### Failure {idx}: Scenario ID `{fail['scenario_id']}`

* **Conversation**: 
```json
{json.dumps(fail['conversation'], indent=2)}
```
* **Expected Behavior**: {fail['expected_behavior']}
* **Actual Behavior**: {fail['actual_behavior']}
* **Root Cause**: {fail['root_cause']}
* **Suggested Fix**: {fail['suggested_fix']}

"""
        return md

    def _build_csv_report(self, data: Dict[str, Any]) -> str:
        convo = data.get("conversation_accuracy", {})
        retrieval = data.get("retrieval_quality", {})
        grounding = data.get("grounding_quality", {})
        quality = data.get("response_quality", {})
        latency = data.get("latency", {})

        intent_accuracy = convo.get("intent_accuracy", 0.0)
        policy_accuracy = convo.get("policy_accuracy", 0.0)
        clarification_acc = convo.get("clarification_accuracy", 0.0)
        comparison_acc = convo.get("comparison_accuracy", 0.0)
        refinement_acc = convo.get("refinement_accuracy", 0.0)

        recall_at_10 = retrieval.get("recall_at_10", 0.0)
        precision_at_5 = retrieval.get("precision_at_5", 0.0)
        mrr = retrieval.get("mrr", 0.0)
        ndcg_at_10 = retrieval.get("ndcg_at_10", 0.0)

        hallucination_rate = grounding.get("hallucination_rate", 0.0)
        invalid_url_rate = grounding.get("invalid_url_rate", 0.0)
        grounding_success_rate = grounding.get("grounding_success_rate", 0.0)

        response_completeness = quality.get("response_completeness", data.get("response_completeness", 0.0))
        recommendation_coverage = quality.get("recommendation_coverage", 0.0)

        average_latency = latency.get("average_total_latency_sec", 0.0)
        p50_latency = latency.get("p50_latency_sec", 0.0)
        p95_latency = latency.get("p95_latency_sec", 0.0)
        max_latency = latency.get("max_latency_sec", 0.0)

        lines = [
            "Metric,Value",
            f"Total Scenarios,{data.get('total_scenarios', 0)}",
            f"Successful Scenarios,{data.get('successful_scenarios', 0)}",
            f"Overall End-to-End Success Rate,{data.get('overall_success_rate', 0.0) * 100:.2f}%",
            f"Intent Accuracy,{intent_accuracy * 100:.2f}%",
            f"Policy Accuracy,{policy_accuracy * 100:.2f}%",
            f"Clarification Accuracy,{clarification_acc * 100:.2f}%",
            f"Comparison Accuracy,{comparison_acc * 100:.2f}%",
            f"Refinement Accuracy,{refinement_acc * 100:.2f}%",
            f"Recall@10,{recall_at_10 * 100:.2f}%",
            f"Precision@5,{precision_at_5 * 100:.2f}%",
            f"MRR,{mrr:.4f}",
            f"NDCG@10,{ndcg_at_10 * 100:.2f}%",
            f"Hallucination Rate,{hallucination_rate * 100:.2f}%",
            f"Invalid URL Rate,{invalid_url_rate * 100:.2f}%",
            f"Grounding Success Rate,{grounding_success_rate * 100:.2f}%",
            f"Response Completeness,{response_completeness * 100:.2f}%",
            f"Recommendation Coverage,{recommendation_coverage * 100:.2f}%",
            f"Average Latency,{average_latency:.4f}s",
            f"P50 Latency,{p50_latency:.4f}s",
            f"P95 Latency,{p95_latency:.4f}s",
            f"Max Latency,{max_latency:.4f}s"
        ]
        return "\n".join(lines)

if __name__ == "__main__":
    generator = ReportGenerator()
    generator.generate_reports()
