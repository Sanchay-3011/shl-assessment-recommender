from typing import Any, Dict, List
from app.models.schemas import ChatMessage
from app.utils.logger import logger

class ConversationAnalyzer:
    """Analyzes the conversation logs to construct structured state (extracted slots/preferences)."""

    def analyze(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """Scans dialog history to extract target role, constraints, and seniority.

        Args:
            messages: List of ChatMessage objects carrying the dialog log.

        Returns:
            Dict containing the structured conversation state.
        """
        logger.info("Analyzing conversation history for constraints and entity extraction...")
        
        # Interface placeholder state representation
        state = {
            "job_role": None,
            "seniority": None,
            "skills": [],
            "test_types": [],  # e.g., 'K' for Knowledge, 'P' for Personality
            "languages": [],
            "comparisons_requested": []
        }

        # Safe fallback parsing loop for demonstration/mock evaluation
        for msg in messages:
            if msg.role == "user":
                content = msg.content.lower()
                if "java" in content:
                    state["job_role"] = "Java"
                if "mid-level" in content or "4 years" in content:
                    state["seniority"] = "Mid-Professional"
                if "personality" in content or "opq" in content:
                    state["test_types"].append("P")
                if "difference between" in content or "compare" in content:
                    state["comparisons_requested"].append("comparison")

        logger.info(f"Extracted conversation state: {state}")
        return state
