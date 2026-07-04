import os
import json
import re
from typing import Any, Dict, List, Optional
from app.utils.logger import logger
from app.retrieval.faiss_index import FAISSRetriever
from app.retrieval.semantic import SemanticRetriever
from app.models.schemas import ChatMessage, ChatResponse, RecommendationItem

# Import new conversational cognitive modules
from app.llm.conversation_analyzer import ConversationAnalyzer
from app.llm.intent_detector import IntentDetector
from app.llm.recommendation_planner import RecommendationPlanner
from app.llm.comparison_planner import ComparisonPlanner
from app.llm.clarification_planner import ClarificationPlanner
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_generator import GroundedResponseGenerator
from app.llm.response_validator import ResponseValidator
from app.llm.conversation_engine import ConversationEngine

class RecommendationService:
    """Orchestrates stateless conversational dialogues, query planning, retrieval, and response validation."""

    def __init__(
        self,
        catalog_path: Optional[str] = None,
        faiss_index_path: Optional[str] = None,
        bm25_index_path: Optional[str] = None
    ) -> None:
        """Initializes retrieval components and cognitive agent modules."""
        self.catalog_path = catalog_path or os.getenv("CATALOG_PATH", "data/shl_assessment_catalog.md")
        self.faiss_index_path = faiss_index_path or os.getenv("FAISS_INDEX_PATH", "indexes/faiss.index")
        self.bm25_index_path = bm25_index_path or os.getenv("BM25_INDEX_PATH", "indexes/bm25.pkl")

        # Database catalog cache
        self.catalog: List[Dict[str, Any]] = []

        # Core retrieval pipelines
        self.faiss_retriever = FAISSRetriever()
        self.hybrid_retriever = SemanticRetriever(self.faiss_retriever) # kept name hybrid_retriever internally for orchestrator compatibility

        # Conversational agent modules (cognitive pipelines)
        self.analyzer = ConversationAnalyzer()
        self.intent_detector = IntentDetector()
        self.recommendation_planner = RecommendationPlanner()
        self.comparison_planner = ComparisonPlanner()
        self.clarification_planner = ClarificationPlanner()
        self.prompt_builder = PromptBuilder()
        self.generator = GroundedResponseGenerator()
        self.validator = ResponseValidator()
        
        # Load resources
        self._load_catalog()
        self._initialize_indexes()

        # Build dynamic technology/role vocabulary from the catalog for constraint extraction
        vocab = set()
        for doc in self.catalog:
            name = doc.get("name", "")
            # Split terms by spaces/punctuation
            for word in re.findall(r'\b[A-Za-z0-9+#.-]+\b', name):
                if len(word) > 1 and not word.isdigit():
                    vocab.add(word.lower())

        self.conversation_engine = ConversationEngine(vocabulary=vocab)

        # Instantiate Orchestrator Components
        from app.services.recommendation_selector import RecommendationSelector
        from app.services.prompt_manager import PromptManager
        from app.services.llm_provider import OpenRouterProvider
        from app.services.response_validator import OrchestratorResponseValidator
        from app.services.orchestrator import AgentOrchestrator

        self.selector = RecommendationSelector()
        self.prompt_manager = PromptManager()
        self.llm_provider = OpenRouterProvider()
        self.response_validator = OrchestratorResponseValidator()

        self.orchestrator = AgentOrchestrator(
            conversation_engine=self.conversation_engine,
            hybrid_retriever=self.hybrid_retriever,
            selector=self.selector,
            prompt_manager=self.prompt_manager,
            llm_provider=self.llm_provider,
            response_validator=self.response_validator,
            catalog=self.catalog
        )

    def _load_catalog(self) -> None:
        """Loads and caches the raw catalog from the markdown source."""
        if not os.path.exists(self.catalog_path):
            logger.warning(f"Catalog Markdown not found at {self.catalog_path} during startup.")
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                markdown_text = f.read()
            
            from app.utils.preprocessing import CatalogPreprocessor
            preprocessor = CatalogPreprocessor()
            processed_docs = preprocessor.parse_markdown_catalog(markdown_text)
            
            # Cache as dictionaries to maintain compatibility with existing orchestrator logic
            self.catalog = [doc.model_dump() for doc in processed_docs]
            logger.info(f"Cached {len(self.catalog)} catalog entries successfully from markdown.")
        except Exception as e:
            logger.error(f"Failed to cache catalog entries from markdown: {e}")

    def _initialize_indexes(self) -> None:
        """Loads search indexes from disk or fits them dynamically if missing."""
        if os.path.exists(self.faiss_index_path):
            try:
                logger.info("Search indexes found. Loading retrieval indices...")
                self.hybrid_retriever.load(self.faiss_index_path)
                return
            except Exception as e:
                logger.error(f"Error loading indices: {e}. Recompiling...")

        self.rebuild_indexes()

    def rebuild_indexes(self) -> None:
        """Rebuilds FAISS search indexes from the catalog dataset."""
        if not self.catalog:
            logger.warning("Empty catalog. Skipping index rebuild.")
            self.hybrid_retriever.fit([])
            return

        logger.info(f"Rebuilding retrieval indices for {len(self.catalog)} entries...")
        
        # We can construct PreprocessedDocument directly since catalog elements have the same fields
        from app.models.schemas import PreprocessedDocument
        processed_catalog = [PreprocessedDocument(**doc) for doc in self.catalog]
        
        self.hybrid_retriever.fit(processed_catalog)
        
        try:
            self.hybrid_retriever.save(self.faiss_index_path)
            logger.info("Retrieval indices saved to disk.")
        except Exception as e:
            logger.error(f"Failed to write indices to files: {e}")

    def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Runs the stateless agent control flow over conversation history.

        Args:
            messages: List of ChatMessage objects representing the dialog logs.

        Returns:
            Validated ChatResponse schema.
        """
        return self.orchestrator.chat(messages)

    def get_recommendations(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Legacy helper to fetch raw catalog items using hybrid search.

        Args:
            query: The search query string.
            limit: Number of items to retrieve.
            filters: Optional metadata filtering criteria.

        Returns:
            List of matching catalog items.
        """
        candidates = self.hybrid_retriever.query(query, top_n=limit, filters=filters)
        return [c.document.model_dump() for c in candidates]
