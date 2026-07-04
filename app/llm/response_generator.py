from typing import Any, Dict, List, Optional
from app.models.schemas import ChatResponse, RecommendationItem
from app.utils.logger import logger

class GroundedResponseGenerator:
    """Interacts with LLM APIs to generate conversational replies grounded in SHL catalog data."""

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initializes the generator with an optional LLM provider client (e.g., Groq).

        Args:
            llm_client: LLM driver/client instance.
        """
        self.llm_client = llm_client

    def generate(
        self,
        prompt: str,
        intent: str,
        catalog_context: List[Dict[str, Any]]
    ) -> ChatResponse:
        """Generates grounded responses.

        Args:
            prompt: Built prompt.
            intent: Detected intent.
            catalog_context: Scraped catalog records retrieved for grounding.

        Returns:
            ChatResponse schema model.
        """
        logger.info(f"Generating grounded agent response for intent: {intent}")

        # Refusal flow for out-of-scope queries
        if intent == "out_of_scope":
            return ChatResponse(
                reply="I can only assist you with SHL product catalog assessments. I cannot provide general hiring advice, legal reviews, or answer off-topic queries.",
                recommendations=[],
                end_of_conversation=False
            )

        # Comparison reply flow
        if intent == "compare":
            compared_names = [item.get("name", "Assessment") for item in catalog_context[:2]]
            compared_str = " and ".join(compared_names) if compared_names else "assessments"
            return ChatResponse(
                reply=f"Here is a grounded comparison between {compared_str} drawn from catalog data. Let me know if you want to compare different tools.",
                recommendations=[],
                end_of_conversation=False
            )

        # Recommendation/Refinement reply flow
        if intent in ("recommend", "refine") and catalog_context:
            recommendations_list = []
            
            # Formulate up to 5 recommendations
            for doc in catalog_context[:5]:
                keys = doc.get("keys", [])
                
                # Heuristic mapping for test_type
                test_type = "K"  # Default 'K' for Knowledge & Skills
                if "Personality & Behavior" in keys:
                    test_type = "P"
                elif "Ability & Aptitude" in keys:
                    test_type = "A"
                elif "Simulations" in keys:
                    test_type = "S"

                recommendations_list.append(
                    RecommendationItem(
                        name=doc.get("name", "Assessment"),
                        url=doc.get("link", "https://www.shl.com/"),
                        test_type=test_type
                    )
                )

            return ChatResponse(
                reply=f"Here is a shortlist of {len(recommendations_list)} assessments that fit your requirements.",
                recommendations=recommendations_list,
                end_of_conversation=True
            )

        # Default clarification reply flow
        return ChatResponse(
            reply="Could you clarify the job role seniority or target skill constraints for the assessment?",
            recommendations=[],
            end_of_conversation=False
        )
