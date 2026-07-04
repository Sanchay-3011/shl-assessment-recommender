import os
import json
import pytest
from evaluation.metrics import (
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    calculate_accuracy,
    calculate_grounding_metrics,
    verify_response_completeness
)
from evaluation.report_generator import ReportGenerator

def test_metrics_calculations() -> None:
    # 1. Recall
    assert recall_at_k(["A", "B", "C"], ["A", "D"], k=2) == 0.5
    assert recall_at_k(["A", "B"], [], k=2) == 1.0
    
    # 2. Precision
    assert precision_at_k(["A", "B", "C"], ["A", "B"], k=2) == 1.0
    assert precision_at_k(["A", "B", "C"], ["A"], k=5) == 0.2
    
    # 3. MRR
    assert mean_reciprocal_rank(["A", "B"], ["B"]) == 0.5
    assert mean_reciprocal_rank(["A", "B"], ["C"]) == 0.0
    
    # 4. Accuracy
    assert calculate_accuracy([1, 2], [1, 3]) == 0.5

def test_grounding_metrics() -> None:
    catalog_names = {"Test A", "Test B"}
    catalog_urls = {"http://a.com", "http://b.com"}
    retrieved_names = {"Test A"}

    recs = [
        {"name": "Test A", "url": "http://a.com"},
        {"name": "Test C", "url": "http://c.com"} # Hallucinated
    ]
    res = calculate_grounding_metrics(recs, catalog_names, catalog_urls, retrieved_names)
    assert res["hallucination_rate"] == 0.5
    assert res["grounding_success_rate"] == 0.5

def test_completeness_metrics() -> None:
    # Empty reply is incomplete
    assert verify_response_completeness("", []) == 0.0
    # Valid reply with missing urls is incomplete
    assert verify_response_completeness("Here are recommendations", [{"name": "Test A"}]) == 0.0
    # Fully correct is complete
    assert verify_response_completeness("Here are recommendations", [{"name": "Test A", "url": "http://a.com"}]) == 1.0

def test_dataset_loading() -> None:
    path = "evaluation/benchmark_dataset.json"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) > 0
    for case in data:
        assert "id" in case
        assert "scenario" in case
        assert "messages" in case
        assert "expected_intent" in case
        assert "expected_policy" in case

def test_report_generation(tmp_path) -> None:
    # Create mock official traces file
    mock_data = {
        "total_scenarios": 1,
        "successful_scenarios": 1,
        "overall_success_rate": 1.0,
        "conversation_accuracy": {
            "intent_accuracy": 1.0,
            "policy_accuracy": 1.0
        },
        "retrieval_quality": {
            "recall_at_10": 1.0,
            "precision_at_5": 1.0,
            "mrr": 1.0
        },
        "grounding_quality": {
            "hallucination_rate": 0.0,
            "invalid_url_rate": 0.0,
            "grounding_success_rate": 1.0
        },
        "response_completeness": 1.0,
        "latency": {
            "average_total_latency_sec": 0.1
        },
        "traces": []
    }
    
    trace_file = tmp_path / "mock_traces.json"
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        
    generator = ReportGenerator(trace_path=str(trace_file))
    console_out = generator._build_console_report(mock_data)
    md_out = generator._build_markdown_report(mock_data)
    
    assert "EVALUATION REPORT" in console_out
    assert "# SHL Assessment Recommender" in md_out
