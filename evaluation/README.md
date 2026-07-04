# SHL Assessment Recommender AI Evaluation Framework

This package provides a production-quality AI evaluation suite for measuring the quality, grounding, and performance of the recommender agent pipeline.

---

## 1. Metrics Definitions

### Retrieval Quality
* **Recall@10**: Percent of expected catalog options retrieved in the top 10 search outputs.
* **Precision@5**: Percent of the top 5 retrieved items that match the target expectations.
* **Mean Reciprocal Rank (MRR)**: Measures the positional effectiveness of first-match retrievals.

### Conversational Flow Accuracy
* **Intent Accuracy**: Verifies whether predicted intent tags match the golden datasets.
* **Policy Accuracy**: Validates E2E execution policies (Clarification, Refusal, Greeting, Recommendation).

### Grounding Integrity
* **Hallucination Rate**: Rate of recommended tests missing from the catalog (must be 0%).
* **Invalid URL Rate**: Rate of recommended URLs mismatched from the catalog links (must be 0%).
* **Grounding Success Rate**: Rate of recommendations originating from the retrieved shortlist candidates.

### Performance
* **Total Latency**: Total request turnaround duration.

---

## 2. Benchmark Execution

To run the full evaluation suite and generate reports:

```bash
venv\Scripts\python -m evaluation.benchmark_runner
venv\Scripts\python -m evaluation.report_generator
```

This generates:
- `evaluation/datasets/official_traces.json` (Traces log output)
- `evaluation/reports/evaluation_report.json` (Structured JSON report)
- `evaluation/reports/evaluation_report.md` (Markdown Summary report)
- `evaluation/reports/evaluation_report.csv` (CSV flat metric report)
