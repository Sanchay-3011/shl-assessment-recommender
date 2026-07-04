from app.models.schemas import ConversationContext

class PolicyEngine:
    """Thin decision router mapping ConversationContext states directly to execution policies."""

    def determine_policy(self, context: ConversationContext) -> str:
        """Maps ConversationContext attributes to a string execution policy mode."""
        if context.current_intent == "prompt_injection":
            return "PROMPT_INJECTION"
        
        if context.current_intent == "out_of_scope":
            return "REFUSAL"
            
        if context.current_intent == "greeting":
            return "GREETING"
            
        if context.current_intent == "compare":
            return "COMPARISON"
            
        if context.current_intent == "lookup":
            return "LOOKUP"
            
        if context.conversation_complete:
            return "END_CONVERSATION"

        if context.needs_clarification:
            return "CLARIFICATION"
            
        return "RECOMMENDATION"
