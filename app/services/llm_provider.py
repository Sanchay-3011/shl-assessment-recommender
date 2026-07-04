import os
import time
import json
import traceback as tb
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import ChatResponse, RecommendationItem, ScoredDocument, ConversationContext
from app.utils.logger import logger
import openai

# DEBUG mode flag
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

class BaseLLMProvider(ABC):
    """Abstract base class for LLM client providers."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        shortlist: List[ScoredDocument],
        policy: str,
        context: ConversationContext
    ) -> ChatResponse:
        """Generates a conversational response matching the policy guidelines."""
        pass

class MockLLMProvider(BaseLLMProvider):
    """Deterministic LLM mock generating responses strictly from grounded shortlist items."""

    def generate_response(
        self,
        prompt: str,
        shortlist: List[ScoredDocument],
        policy: str,
        context: ConversationContext
    ) -> ChatResponse:
        # Refusal flows
        if policy == "PROMPT_INJECTION":
            return ChatResponse(
                reply=context.refusal_reason or "Safety protocol triggered. Request refused.",
                recommendations=[],
                end_of_conversation=False
            )
            
        if policy == "REFUSAL":
            return ChatResponse(
                reply=context.refusal_reason or "Request out of scope.",
                recommendations=[],
                end_of_conversation=False
            )

        # Greeting flow
        if policy == "GREETING":
            return ChatResponse(
                reply=context.clarification_question or "Hello! Could you specify the job role or skill you target?",
                recommendations=[],
                end_of_conversation=False
            )

        # Clarification flow
        if policy == "CLARIFICATION":
            return ChatResponse(
                reply=context.clarification_question or "Could you clarify the job role seniority or skills requirements?",
                recommendations=[],
                end_of_conversation=False
            )

        # Comparison flow
        if policy == "COMPARISON":
            targets_str = " and ".join(context.comparison_targets)
            return ChatResponse(
                reply=f"Here is a comparison between {targets_str} drawn from catalog data. Let me know if you want details on other assessments.",
                recommendations=[],
                end_of_conversation=False
            )

        # Recommendations / Refine / End conversation flows
        recommendations_list = []
        for doc in shortlist:
            keys = doc.document.keys
            test_type = "K"
            if "Personality & Behavior" in keys:
                test_type = "P"
            elif "Ability & Aptitude" in keys:
                test_type = "A"
            elif "Simulations" in keys:
                test_type = "S"

            recommendations_list.append(
                RecommendationItem(
                    name=doc.document.name,
                    url=doc.document.link,
                    test_type=test_type
                )
            )

        reply = f"Based on your requirements, I recommend these {len(recommendations_list)} assessments."
        role_part = f"a {context.extracted_constraints.role} role" if context.extracted_constraints.role else "your criteria"
        
        techs = []
        if context.extracted_constraints.programming_languages:
            techs.extend(context.extracted_constraints.programming_languages)
        if context.extracted_constraints.skills:
            techs.extend(context.extracted_constraints.skills)
            
        tech_part = f" for {', '.join(techs)}" if techs else ""
        
        reply = f"Here are {len(recommendations_list)} assessments that fit {role_part}{tech_part}."

        return ChatResponse(
            reply=reply,
            recommendations=recommendations_list,
            end_of_conversation=(policy == "END_CONVERSATION")
        )

class OpenRouterProvider(BaseLLMProvider):
    """Production OpenRouter LLM Client Provider with retry logic and JSON schema validation."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        
        # Initialize client if API key is present
        self.client = None
        if self.api_key:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                timeout=120.0
            )
        
        # Track last error for diagnostics
        self._last_error: Optional[str] = None

    def generate_response(
        self,
        prompt: str,
        shortlist: List[ScoredDocument],
        policy: str,
        context: ConversationContext
    ) -> ChatResponse:
        """Invokes OpenRouter API securely, parsing and validating outputs under retry policies."""
        # 1. Dummy API key check for local test routing
        is_mocked = "Mock" in type(self.client).__name__ or "MagicMock" in type(self.client).__name__
        if self.api_key and self.api_key.startswith("gsk_dummy") and not is_mocked:
            logger.info("OPENROUTER_API_KEY is dummy key. Delegating response to MockLLMProvider.")
            mock = MockLLMProvider()
            return mock.generate_response(prompt, shortlist, policy, context)

        # 2. Production missing API key/client fallback check
        if not self.client:
            logger.warning("OPENROUTER_API_KEY is missing. Falling back to safety error response.")
            return self._get_fallback_reply()

        # Execute call with transient retry logic
        response_text = self._call_api_with_retry(prompt)
        if not response_text:
            logger.error(f"OpenRouter API failed after retry logic. Last error: {self._last_error}. Invoking fallback response.")
            return self._get_fallback_reply()

        # Try parsing response
        try:
            return self._parse_and_validate_response(response_text)
        except Exception as e:
            logger.warning(f"Initial JSON validation failed: {e}. Executing correction retry once.")
            # Retry exactly once with a correction prompt
            correction_prompt = (
                f"{prompt}\n\n"
                f"Your previous output was invalid JSON or did not match the required schema: {response_text}\n"
                f"Please correct it and output strictly valid JSON conforming to the schema:\n"
                f"{{\n"
                f"  \"reply\": \"string\",\n"
                f"  \"recommendations\": [ {{\"name\": \"string\", \"url\": \"string\", \"test_type\": \"string\"}} ],\n"
                f"  \"end_of_conversation\": boolean\n"
                f"}}\n"
            )
            retry_text = self._call_api_with_retry(correction_prompt)
            if not retry_text:
                return self._get_fallback_reply()
            try:
                return self._parse_and_validate_response(retry_text)
            except Exception as ex:
                logger.error(f"Correction retry failed: {ex}. Falling back.")
                return self._get_fallback_reply()

    def _call_api_with_retry(self, prompt: str) -> Optional[str]:
        """Calls OpenRouter API with exponential backoff on transient errors (timeouts, rate limits)."""
        max_attempts = 3
        backoff_delay = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content
            except openai.APIConnectionError as e:
                self._last_error = f"[Transient] {type(e).__name__}: {e}"
                logger.warning(f"Transient OpenRouter API error on attempt {attempt}: {e}")
                if attempt == max_attempts:
                    break
                time.sleep(backoff_delay)
                backoff_delay *= 2.0
            except openai.APIStatusError as e:
                self._last_error = f"[APIError] status={getattr(e, 'status_code', '?')}: {e}"
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    logger.error(f"Non-transient OpenRouter API error (status={e.status_code}): {e}")
                    if DEBUG:
                        logger.error(f"[PIPELINE DEBUG] OpenRouterProvider stack trace:\n{tb.format_exc()}")
                    break
                logger.warning(f"OpenRouter API error on attempt {attempt}: {e}")
                if attempt == max_attempts:
                    break
                time.sleep(backoff_delay)
                backoff_delay *= 2.0
            except Exception as e:
                self._last_error = f"[Unexpected] {type(e).__name__}: {e}"
                logger.error(f"Unexpected API error on attempt {attempt}: {e}\n{tb.format_exc()}")
                break

        return None

    def _parse_and_validate_response(self, text: str) -> ChatResponse:
        """Parses LLM response, extracting JSON structure robustly."""
        import re
        cleaned_text = text.strip()
        
        # Remove <think> blocks if present
        cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL).strip()
        
        # Remove Markdown fences if present anywhere
        cleaned_text = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', cleaned_text, flags=re.DOTALL).strip()
        
        # Extract the JSON block if wrapped in other text
        match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(0)

        # Pydantic schema validation check
        response_model = ChatResponse.model_validate_json(cleaned_text)
        return response_model

    def _get_fallback_reply(self) -> ChatResponse:
        """Fallback ChatResponse on connection, timeout, or parsing failures."""
        error_detail = self._last_error or "Unknown error"
        logger.error(f"OpenRouterProvider returning fallback response. Root cause: {error_detail}")
        return ChatResponse(
            reply="I encountered an issue verifying the recommendation details. What specific skill or seniority level are you targeting?",
            recommendations=[],
            end_of_conversation=False
        )
