from typing import List, Dict, Any, Set

def recall_at_k(retrieved: List[str], expected: List[str], k: int = 10) -> float:
    """Calculates Recall@k.

    Recall@k = (count of expected items in retrieved[:k]) / total count of expected items
    """
    if not expected:
        return 1.0
    retrieved_k = set(retrieved[:k])
    intersect = retrieved_k.intersection(expected)
    return len(intersect) / len(expected)

def precision_at_k(retrieved: List[str], expected: List[str], k: int = 5) -> float:
    """Calculates standard Precision@k.

    Precision@k = (count of expected items in retrieved[:k]) / k
    """
    if not expected:
        return 1.0
    retrieved_k = set(retrieved[:k])
    intersect = retrieved_k.intersection(expected)
    return len(intersect) / k

def mean_reciprocal_rank(retrieved: List[str], expected: List[str]) -> float:
    """Calculates Reciprocal Rank (RR) for a single query.

    RR = 1 / rank of the first expected item found in retrieved (1-indexed).
    """
    if not expected:
        return 1.0
    for idx, item in enumerate(retrieved, 1):
        if item in expected:
            return 1.0 / idx
    return 0.0

def calculate_accuracy(predictions: List[Any], targets: List[Any]) -> float:
    """Calculates general prediction accuracy."""
    if not targets:
        return 1.0
    correct = sum(1 for p, t in zip(predictions, targets) if p == t)
    return correct / len(targets)

def calculate_grounding_metrics(
    recommendations: List[Dict[str, Any]],
    catalog_names: Set[str],
    catalog_urls: Set[str],
    retrieved_names: Set[str]
) -> Dict[str, float]:
    """Calculates grounding metrics: hallucination, invalid URL, and grounding success."""
    total = len(recommendations)
    if total == 0:
        return {
            "hallucination_rate": 0.0,
            "invalid_url_rate": 0.0,
            "grounding_success_rate": 1.0
        }

    hallucinations = 0
    invalid_urls = 0
    grounded_successes = 0

    for rec in recommendations:
        name = rec.get("name", "").strip()
        url = rec.get("url", "").strip()

        # Check in catalog
        if name not in catalog_names:
            hallucinations += 1
        else:
            if url not in catalog_urls:
                invalid_urls += 1

        if name in retrieved_names:
            grounded_successes += 1

    return {
        "hallucination_rate": hallucinations / total,
        "invalid_url_rate": invalid_urls / total,
        "grounding_success_rate": grounded_successes / total
    }

def verify_response_completeness(reply: str, recommendations: List[Dict[str, Any]]) -> float:
    """Returns 1.0 if response has a conversational reply and every recommendation has name/url."""
    if not reply or not reply.strip():
        return 0.0
    for rec in recommendations:
        if not rec.get("name") or not rec.get("url"):
            return 0.0
    return 1.0

def calculate_recommendation_coverage(recommendations: List[Dict[str, Any]], expected: List[str]) -> float:
    """Calculates recommendation coverage."""
    if not expected:
        return 1.0
    rec_names = {r.get("name", "").strip() for r in recommendations}
    intersect = rec_names.intersection(expected)
    return len(intersect) / len(expected)

import math
def ndcg_at_k(retrieved: List[str], expected: List[str], k: int = 10) -> float:
    """Calculates NDCG@k using binary relevance (1 if expected, 0 if not)."""
    if not expected:
        return 1.0
    dcg = 0.0
    for idx, item in enumerate(retrieved[:k], 1):
        if item in expected:
            dcg += 1.0 / math.log2(idx + 1)
    idcg = 0.0
    for idx in range(1, min(k, len(expected)) + 1):
        idcg += 1.0 / math.log2(idx + 1)
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

