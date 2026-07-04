import os
import json
from typing import Any, Dict, List, Tuple, Optional
from app.utils.logger import logger
from openai import OpenAI

class LLMReranker:
    """Reranks candidate assessment recommendations using an LLM or score normalization fallback."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initializes the OpenAI client if API key is provided or configured in env.

        Args:
            api_key: Optional OpenAI API key override.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("Initialized OpenAI client for LLMReranker.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OPENAI_API_KEY is not configured. LLMReranker will fall back to retriever scores.")

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Dict[str, Any], float]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Reranks retrieved candidates.

        Args:
            query: The user query.
            candidates: Candidates retrieved from the search index as (document, score) tuples.

        Returns:
            Reranked list of (document, relevance_score) tuples.
        """
        if not candidates:
            return []

        # If LLM is not configured, fallback to normalized retriever scores
        if not self.client:
            logger.info("Using fallback score normalization for reranking.")
            max_score = max(c[1] for c in candidates) if candidates else 1.0
            if max_score <= 0.0:
                max_score = 1.0
            return [(doc, float(score / max_score)) for doc, score in candidates]

        try:
            # Format candidate data for prompt
            items_to_rank = []
            for doc, _ in candidates:
                items_to_rank.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "description": doc.get("description")
                })

            system_instruction = (
                "You are an assessment reranking assistant. Evaluate how relevant each assessment is to the search query. "
                "Respond with a JSON object. The JSON must contain a single key 'rankings' which holds a list of items. "
                "Each item must contain 'id' (string matching the assessment id) and 'score' (float between 0.0 and 1.0 "
                "representing relevance to the query, where 1.0 is extremely relevant and 0.0 is irrelevant)."
            )

            user_prompt = f"Query: {query}\nAssessments: {json.dumps(items_to_rank)}"

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Received empty response from OpenAI.")

            data = json.loads(content)
            rankings = data.get("rankings", [])
            
            # Map score predictions back to documents
            scores_map = {r["id"]: float(r["score"]) for r in rankings if "id" in r and "score" in r}

            reranked = []
            for doc, _ in candidates:
                doc_id = doc["id"]
                score = scores_map.get(doc_id, 0.0)
                reranked.append((doc, score))

            # Sort candidate documents by LLM relevance score descending
            reranked.sort(key=lambda x: x[1], reverse=True)
            logger.info(f"Successfully reranked {len(candidates)} documents using LLM.")
            return reranked

        except Exception as e:
            logger.error(f"Error occurred during LLM reranking: {e}. Falling back to original rankings.")
            return [(doc, score) for doc, score in candidates]
