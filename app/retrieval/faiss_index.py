import os
import pickle
import time
import numpy as np
import faiss
from typing import Any, Dict, List, Optional
from sentence_transformers import SentenceTransformer
from app.utils.logger import logger
from app.models.schemas import PreprocessedDocument, ScoredDocument

class FAISSRetriever:
    """Production-grade dense semantic search retriever using FAISS IndexFlatIP (Cosine Similarity)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.documents: List[PreprocessedDocument] = []
        self._loaded: bool = False

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading of SentenceTransformer."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit(self, documents: List[PreprocessedDocument]) -> None:
        """Computes embeddings for documents and builds the FAISS Cosine Index.

        Args:
            documents: List of preprocessed documents.
        """
        self.documents = documents
        texts = [doc.embedding_text for doc in documents]

        logger.info(f"Generating dense embeddings for {len(texts)} documents using {self.model_name}...")
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        
        # Normalize embeddings for Cosine Similarity (IndexFlatIP requires normalized vectors)
        faiss.normalize_L2(embeddings)
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self._loaded = True
        logger.info(f"FAISS Cosine index successfully built with {self.index.ntotal} vectors.")

    def save(self, filepath: str) -> None:
        """Serializes the FAISS binary index and metadata schema list.

        Args:
            filepath: Destination index file path.
        """
        if self.index is None:
            raise ValueError("FAISS index must be fitted before saving.")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Write binary FAISS index file
        faiss.write_index(self.index, filepath)
        
        # Dump document definitions as raw dicts to ensure long-term pickle stability
        meta_path = f"{filepath}.meta"
        serialized_docs = [doc.model_dump() for doc in self.documents]
        
        with open(meta_path, "wb") as f:
            pickle.dump(serialized_docs, f)
            
        logger.info(f"FAISS index saved to {filepath} (meta saved to {meta_path})")

    def load(self, filepath: str) -> None:
        """Loads FAISS index from disk. Implements caching by checking load flag.

        Args:
            filepath: Target index file path.
        """
        if self._loaded:
            logger.debug("FAISS index already cached in memory. Skipping load.")
            return

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"FAISS serialized index not found at {filepath}")

        meta_path = f"{filepath}.meta"
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"FAISS metadata mapping file not found at {meta_path}")

        logger.info(f"Loading FAISS index from disk: {filepath}")
        self.index = faiss.read_index(filepath)
        
        with open(meta_path, "rb") as f:
            serialized_docs = pickle.load(f)
            self.documents = [PreprocessedDocument(**d) for d in serialized_docs]
            
        self._loaded = True
        logger.info(f"Successfully loaded and cached FAISS index containing {self.index.ntotal} items.")

    def query(self, query: str, top_n: int = 5) -> List[ScoredDocument]:
        """Runs a semantic vector search query, returning a ranked List of ScoredDocuments.

        Args:
            query: Input user search text.
            top_n: Maximum results to return.

        Returns:
            List of ScoredDocument models.
        """
        start_time = time.perf_counter()

        if not self._loaded or self.index is None:
            logger.warning("FAISS query triggered, but retriever is not loaded.")
            return []

        # Encode and normalize query vector
        query_vec = self.model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(query_vec)

        # Query vector search
        scores, indices = self.index.search(query_vec, top_n)
        
        # Assemble typed ScoredDocument models
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.documents):
                continue
            results.append(
                ScoredDocument(
                    document=self.documents[idx],
                    score=float(score)
                )
            )

        duration = time.perf_counter() - start_time
        logger.info(f"FAISS Retrieval timing: {duration:.6f} seconds | Query: '{query}'")
        return results
