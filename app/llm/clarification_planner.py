from typing import Any, Dict, List
from app.utils.logger import logger

class ClarificationPlanner:
    """Plans questions to ask the user to resolve missing variables/slots."""

    def plan_clarification(self, state: Dict[str, Any]) -> List[str]:
        """Checks dialog state to identify missing context dimensions.

        Args:
            state: Extracted dialogue state.

        Returns:
            List of missing parameters requiring clarification.
        """
        logger.info("Evaluating state for missing parameters...")
        missing_slots = []

        if not state.get("job_role"):
            missing_slots.append("job_role")
        if not state.get("seniority"):
            missing_slots.append("seniority")

        logger.info(f"Missing slots to resolve: {missing_slots}")
        return missing_slots
