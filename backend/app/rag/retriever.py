"""
FAISS retriever — query interface for the medical knowledge index.
"""

import json
import os
from typing import Optional

import numpy as np

from app.config import get_settings
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class FAISSRetriever:
    """Query the FAISS index for relevant medical knowledge documents."""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
        self.settings = get_settings()
        self.index = None
        self.documents: list[dict] = []

    def load(self) -> bool:
        """Load the FAISS index and documents."""
        if not FAISS_AVAILABLE:
            return False

        index_path = os.path.join(self.settings.FAISS_INDEX_PATH, "index.faiss")
        docs_path = os.path.join(self.settings.FAISS_INDEX_PATH, "documents.json")

        if not os.path.exists(index_path):
            logger.warning(f"Index file not found: {index_path}")
            return False

        self.index = faiss.read_index(index_path)
        with open(docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        logger.info(f"Retriever loaded {self.index.ntotal} vectors")
        return True

    async def search(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """
        Embed a query and return the top-k matching documents.

        Returns list of dicts with keys: document, distance, rank.
        """
        if self.index is None:
            return []

        k = top_k or self.settings.RAG_TOP_K
        query_vec = await self.gemini.embed_text(query)
        query_np = np.array([query_vec], dtype=np.float32)

        distances, indices = self.index.search(query_np, k)

        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.documents):
                continue
            results.append({
                "document": self.documents[idx],
                "distance": float(dist),
                "rank": rank + 1,
            })

        return results
