from typing import Any, Dict, List
from app.utils.logger import logger

class ComparisonPlanner:
    """Extracts features and compares multiple assessments from the catalog."""

    def plan_comparison(self, query: str, catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolves which assessments need comparison and maps their metadata.

        Args:
            query: User's comparative question content.
            catalog: Full parsed SHL product catalog database.

        Returns:
            Dict containing comparison facts.
        """
        logger.info("Planning comparative summary of assessments...")

        query_lower = query.lower()
        items_to_compare = []

        # Find candidate assessments explicitly or implicitly named in query
        for doc in catalog:
            name = doc.get("name", "").lower()
            # Match acronyms (e.g., OPQ, GSA) or partial names
            if name in query_lower or (len(name) > 3 and name[:4] in query_lower):
                items_to_compare.append(doc)

        # Fallback dummy comparison if none matched explicitly
        if not items_to_compare and len(catalog) >= 2:
            items_to_compare = [catalog[0], catalog[1]]

        plan_result = {
            "items": items_to_compare,
            "dimensions": ["name", "description", "duration", "test_type"],
            "has_comparisons": len(items_to_compare) > 0
        }

        logger.info(f"Formulated comparison plan: {plan_result}")
        return plan_result
