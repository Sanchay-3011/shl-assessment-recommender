from typing import Any, Dict
from app.utils.logger import logger

class RecommendationPlanner:
    """Plans queries and retrieval actions for the recommendation engine."""

    def plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves what criteria should guide search index queries.

        Args:
            state: Extracted dialog state from ConversationAnalyzer.

        Returns:
            Dict containing query configuration parameters.
        """
        logger.info("Generating recommendation plan configurations...")

        job_role = state.get("job_role")
        seniority = state.get("seniority")

        # Basic planning logic to create retrieval queries
        query_tokens = []
        if job_role:
            query_tokens.append(job_role)
        if seniority:
            query_tokens.append(seniority)

        search_query = " ".join(query_tokens) if query_tokens else "general assessment"
        
        # Map state constraints to backend filters
        filters = {}
        if state.get("job_levels"):
            filters["job_levels"] = state["job_levels"]

        plan_result = {
            "search_query": search_query,
            "filters": filters,
            "target_limit": 5,
            "ready_to_recommend": bool(job_role and seniority)
        }

        logger.info(f"Formulated recommendation plan: {plan_result}")
        return plan_result
