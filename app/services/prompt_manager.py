import os
from typing import List
from app.models.schemas import ConversationContext, ScoredDocument

class PromptManager:
    """Loads prompt templates from disk and composes system prompts and user inputs for LLM providers."""

    def __init__(self, prompts_dir: str = "app/prompts") -> None:
        self.prompts_dir = prompts_dir
        self.templates = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Loads prompt text files from the prompts directory."""
        names = ["system", "recommendation", "comparison", "clarification", "greeting", "refusal"]
        for name in names:
            filepath = os.path.join(self.prompts_dir, f"{name}.txt")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    self.templates[name] = f.read()
            else:
                self.templates[name] = ""

    def construct_prompt(self, context: ConversationContext, shortlist: List[ScoredDocument], policy: str) -> str:
        """Composes a single grounded prompt string by combining loaded templates, constraints, logs, and summaries."""
        # 1. System instruction block
        system_tmpl = self.templates.get("system", "")

        # 2. Match policy template
        policy_lower = policy.lower()
        policy_tmpl = ""
        if "greeting" in policy_lower:
            policy_tmpl = self.templates.get("greeting", "")
        elif "clarification" in policy_lower:
            policy_tmpl = self.templates.get("clarification", "")
        elif "comparison" in policy_lower:
            policy_tmpl = self.templates.get("comparison", "")
        elif "refusal" in policy_lower or "injection" in policy_lower:
            policy_tmpl = self.templates.get("refusal", "")
        else: # RECOMMENDATION or REFINE
            policy_tmpl = self.templates.get("recommendation", "")

        # 3. Format structured assessments shortlist metadata section
        shortlist_sections = []
        if shortlist:
            for i, item in enumerate(shortlist, 1):
                section = (
                    f"=== Selected Assessment {i} ===\n"
                    f"Name: {item.document.name}\n"
                    f"URL: {item.document.link}\n"
                    f"Job Levels: {', '.join(item.document.job_levels)}\n"
                    f"Languages: {', '.join(item.document.languages)}\n"
                    f"Duration: {item.document.duration}\n"
                    f"Remote: {item.document.remote}\n"
                    f"Adaptive: {item.document.adaptive}\n"
                    f"Description: {item.document.description}\n"
                    f"Retrieval Reasoning: {item.reasoning}\n"
                )
                shortlist_sections.append(section)
        shortlist_str = "\n".join(shortlist_sections) if shortlist_sections else "None (No matching assessments found)."

        # 4. Context info details
        constraints = context.extracted_constraints
        context_details = (
            f"=== Conversation Context ===\n"
            f"Intent: {context.current_intent}\n"
            f"Clarification Question Needed: {context.clarification_question or 'N/A'}\n"
            f"Comparison Targets: {', '.join(context.comparison_targets) or 'None'}\n"
            f"Refusal Reason: {context.refusal_reason or 'N/A'}\n"
            f"Extracted Constraints: role={constraints.role}, job_level={constraints.job_level}, "
            f"duration={constraints.duration}, language={constraints.language}, remote={constraints.remote}, "
            f"adaptive={constraints.adaptive}, keys={constraints.assessment_keys}\n"
        )

        # Combine system prompt, context details, structured assessment summaries, and policy prompt guidelines
        prompt = (
            f"=== SYSTEM INSTRUCTIONS ===\n"
            f"{system_tmpl}\n\n"
            f"{context_details}\n"
            f"=== GROUNDED SHORTLIST ASSESSMENTS ===\n"
            f"{shortlist_str}\n\n"
            f"=== POLICY SPECIFIC GENERATION RULES ===\n"
            f"{policy_tmpl}\n"
        )
        return prompt
