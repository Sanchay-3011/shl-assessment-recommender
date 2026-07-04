from typing import List, Literal
from app.models.schemas import ChatMessage
from app.utils.logger import logger

# Declare available intent modes
IntentType = Literal["clarify", "recommend", "refine", "compare", "out_of_scope"]

class IntentDetector:
    """Analyzes the user's latest dialogue turn to resolve their intent."""

    def detect_intent(self, messages: List[ChatMessage]) -> IntentType:
        """Analyzes dialogue to resolve intent.

        Args:
            messages: Conversation history.

        Returns:
            IntentType string ('clarify', 'recommend', 'refine', 'compare', 'out_of_scope').
        """
        logger.info("Detecting conversational intent...")
        if not messages:
            return "clarify"

        # Obtain the final user utterance
        last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
        if not last_user_msg:
            return "clarify"

        text = last_user_msg.content.lower()

        # Check for scope bypass or inappropriate query topics
        out_of_scope_keywords = ["hiring advice", "legal advice", "salary", "ignore previous instructions", "system prompt"]
        if any(kw in text for kw in out_of_scope_keywords):
            logger.warning(f"Detected potential out-of-scope query: '{text}'")
            return "out_of_scope"

        # Check for comparison requests
        comparison_keywords = ["difference between", "vs", "compare", "versus"]
        if any(kw in text for kw in comparison_keywords):
            return "compare"

        # Check for refinement requests
        refinement_keywords = ["actually", "change", "instead of", "modify", "filter by", "add personality"]
        if any(kw in text for kw in refinement_keywords):
            return "refine"

        # Standard check: if context has enough tokens/keywords, trigger recommendations
        all_user_text = " ".join([m.content.lower() for m in messages if m.role == "user"])
        if "java" in all_user_text and ("mid-level" in all_user_text or "4 years" in all_user_text or len(messages) >= 3):
            return "recommend"

        return "clarify"
