from typing import Any, Dict, List
from app.models.schemas import ChatMessage
from app.utils.logger import logger

class PromptBuilder:
    """Assembles prompt strings to drive LLM completion tasks."""

    def build_prompt(
        self,
        intent: str,
        state: Dict[str, Any],
        messages: List[ChatMessage],
        catalog_context: List[Dict[str, Any]],
        planner_context: Dict[str, Any]
    ) -> str:
        """Assembles prompts for LLM inference.

        Args:
            intent: Conversational intent.
            state: Extracted slot state.
            messages: Dialogue log history.
            catalog_context: Retrieved catalog records.
            planner_context: Context dictionary from planners.

        Returns:
            Formatted prompt string.
        """
        logger.info("Constructing prompt wrapper...")

        # Prompt interface template
        prompt = (
            f"[SYSTEM INSTRUCTION]\n"
            f"Active Intent: {intent}\n"
            f"Extracted Constraints: {state}\n"
            f"Planner Payload: {planner_context}\n"
            f"Catalog Matches: {[d.get('name') for d in catalog_context]}\n"
            f"[HISTORY]\n"
        )
        
        for msg in messages:
            prompt += f"{msg.role}: {msg.content}\n"

        return prompt
