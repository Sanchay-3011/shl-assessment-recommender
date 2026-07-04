import os
import time
from typing import Any, Dict, List, Optional
from app.retrieval.faiss_index import FAISSRetriever
from app.models.schemas import PreprocessedDocument, ScoredDocument, HiringConstraints
from app.utils.logger import logger

SENIORITY_HIERARCHY = [
    "entry-level",
    "graduate",
    "mid-professional",
    "professional",
    "manager",
    "director",
    "executive"
]

class SemanticRetriever:
    """Production FAISS-only semantic search engine.

    Features metadata scaling, competing language penalty, and fast ranking.
    """

    def __init__(self, faiss_retriever: FAISSRetriever) -> None:
        """Initializes SemanticRetriever with vector search handler.

        Args:
            faiss_retriever: Vector search handler.
        """
        self.faiss = faiss_retriever
        self.last_debug_info = None
        self.debug_mode = os.getenv("DEBUG_RETRIEVAL", "false").lower() == "true"

    def fit(self, documents: List[PreprocessedDocument]) -> None:
        """Fits underlying FAISS retriever on the preprocessed corpus."""
        self.faiss.fit(documents)

    def save(self, faiss_path: str) -> None:
        """Serializes FAISS index."""
        self.faiss.save(faiss_path)

    def load(self, faiss_path: str) -> None:
        """Lazy loads indices from disk."""
        self.faiss.load(faiss_path)

    def _match_filters(self, doc: PreprocessedDocument, filters: Dict[str, Any]) -> bool:
        """Evaluates whether a document matches target metadata constraints.

        # NOTE: Job-level is NOT hard-filtered here to ensure we don't drop
        # good technical matches that are missing a specific job level tag.
        # Supports: language, duration, adaptive, and remote checks.
        """
        if not filters:
            return True

        # 1. Language constraint match (hard filter)
        req_lang = filters.get("language")
        if req_lang and isinstance(req_lang, str):
            req_lang_clean = req_lang.strip().lower()
            if doc.languages and req_lang_clean not in [l.lower() for l in doc.languages]:
                return False

        # 2. Maximum duration minutes match
        req_duration = filters.get("duration")
        if req_duration is not None:
            try:
                max_dur = int(req_duration)
                if doc.duration_minutes is not None and doc.duration_minutes > max_dur:
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid duration constraint filter format: {req_duration}")

        # 3. Adaptive constraint match ('yes' / 'no')
        req_adaptive = filters.get("adaptive")
        if req_adaptive and isinstance(req_adaptive, str):
            if doc.adaptive.lower() != req_adaptive.strip().lower():
                return False

        # 4. Remote constraint match ('yes' / 'no')
        req_remote = filters.get("remote")
        if req_remote and isinstance(req_remote, str):
            if doc.remote.lower() != req_remote.strip().lower():
                return False

        return True

    def query(
        self,
        query: str,
        top_n: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        constraints: Optional[HiringConstraints] = None
    ) -> List[ScoredDocument]:
        """Queries semantic index, filters, applies scalars and ranks candidates.

        Args:
            query: Input user query string.
            top_n: Number of final recommendations to return.
            filters: Explicit metadata constraints.
            constraints: Conversation constraints to detect target technologies and roles.

        Returns:
            List of ScoredDocument models ranked by score.
        """
        pool_size = 100

        faiss_start = time.perf_counter()
        faiss_candidates = self.faiss.query(query, top_n=pool_size)
        faiss_time = time.perf_counter() - faiss_start

        filtering_start = time.perf_counter()
        if filters:
            filtered_faiss = [c for c in faiss_candidates if self._match_filters(c.document, filters)]
        else:
            filtered_faiss = list(faiss_candidates)
        filtering_time = time.perf_counter() - filtering_start

        tech_words = []
        target_job_level = None
        if constraints:
            if constraints.programming_languages:
                tech_words.extend([lang.lower() for lang in constraints.programming_languages])
            if constraints.job_level:
                target_job_level = constraints.job_level.lower()

        scoring_start = time.perf_counter()
        final_candidates = []
        
        competing_langs = {
            "java", "python", "javascript", "typescript", "c", "ruby", "go", "php", "sql", "r", 
            "swift", "kotlin", "html", "css", "visual basic", "asp.net", "abap", "cobol", "perl", "unix", "linux",
            "ios", "android", "objective", "node", "react", "angular", "vue",
            "selenium", "appdynamics", "git", "photoshop", "typing", "cisco",
            "hadoop", "spark", "hive", "kafka", "pig", "aws", "azure", "docker", "kubernetes", "jenkins", "maven",
            "spring", "django", "struts", "hibernate", "mongodb", "oracle", "teradata", "informatica",
            "sap", "salesforce", "pega", "mulesoft", "uipath", "biztalk", "sharepoint",
            "accounting", "finance", "medical", "nursing", "aerospace"
        }
        
        for candidate in filtered_faiss:
            doc = candidate.document
            
            # Use original FAISS distance as base score (cosine similarity typically 0 to 1)
            score = float(candidate.score)
            
            # A. Small scalar boost for exact job level matches
            if target_job_level and doc.job_levels:
                doc_levels = [l.lower() for l in doc.job_levels]
                if target_job_level in doc_levels:
                    score *= 1.2 # 20% boost
                    
            # B. Language Modifiers
            if tech_words:
                is_competing = any(lang in doc.keyword_tokens for lang in competing_langs if not any(lang in tw for tw in tech_words))
                is_matching = any(req in doc.keyword_tokens for req in tech_words)
                
                # Identify generic coding tests (like Automata) that support many languages
                doc_text = (doc.name + " " + (doc.description or "")).lower()
                is_generic_coding = any(word in doc_text for word in ["programming", "coding", "software", "developer", "algorithm"])
                
                if is_competing and not is_matching:
                    if self.debug_mode:
                        logger.info(f"[DEBUG_RETRIEVAL] Penalizing {doc.name} (competing language detected)")
                    score *= 0.1 # Severe penalty
                elif not is_matching and not is_generic_coding:
                    if self.debug_mode:
                        logger.info(f"[DEBUG_RETRIEVAL] Penalizing {doc.name} (unrelated to requested tech)")
                    score *= 0.1 # Severe penalty
                elif is_matching:
                    if self.debug_mode:
                        logger.info(f"[DEBUG_RETRIEVAL] Boosting {doc.name} (matching language detected)")
                    score *= 2.0 # Massive boost
                    
            final_candidates.append(ScoredDocument(document=doc, score=score))

        final_candidates.sort(key=lambda x: x.score, reverse=True)
        results = final_candidates[:top_n]
        scoring_time = time.perf_counter() - scoring_start

        if self.debug_mode:
            logger.info("=== [DEBUG_RETRIEVAL] RETRIEVAL RELEVANCE AUDIT REPORT ===")
            logger.info(f"Generated Retrieval Query: '{query}'")
            logger.info(f"Applied Metadata Filters: {filters}")
            if constraints:
                logger.info(
                    f"ConversationContext: role={constraints.role or 'N/A'}, "
                    f"langs={constraints.programming_languages}, skills={constraints.skills}, "
                    f"level={constraints.job_level}"
                )
            logger.info("[DEBUG_RETRIEVAL] FAISS Final Top 10 Ranking:")
            for i, res in enumerate(results[:10]):
                logger.info(f"  - Rank {i+1}: {res.document.name} (Final Score: {res.score:.4f})")
            logger.info(
                f"Retrieval profiling timings | "
                f"FAISS: {faiss_time:.6f}s | "
                f"Filtering: {filtering_time:.6f}s | "
                f"Scoring: {scoring_time:.6f}s"
            )

        self.last_debug_info = {
            "query": query,
            "filters": filters,
            "candidates": [
                {
                    "name": res.document.name,
                    "score": float(res.score),
                    "faiss_score": float(res.score) # For compatibility with tests
                }
                for res in results
            ]
        }

        return results
