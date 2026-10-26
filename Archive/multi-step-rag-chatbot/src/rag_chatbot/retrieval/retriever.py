"""
Semantic retrieval — turn a user question into the most relevant chunks.

FLOW:
  1. Embed the query (same model as ingest!).
  2. Nearest-neighbor search in Chroma.
  3. Filter by minimum similarity so we don't hallucinate on irrelevant context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from rag_chatbot.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScoredChunk:
    """One retrieved passage plus score for logging and UI citations."""

    document: Document
    score: float  # Higher = more similar (we convert Chroma distance → similarity)


class DocumentRetriever:
    def __init__(self, store: VectorStore, settings: Settings | None = None) -> None:
        self._store = store
        self._settings = settings or get_settings()

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        k = top_k or self._settings.retrieval_top_k

        # similarity_search_with_relevance_scores returns (doc, score in [0,1]) for cosine setups.
        pairs = self._store.similarity_search_with_relevance_scores(query, k=k)

        results: list[ScoredChunk] = []
        for doc, score in pairs:
            if score < self._settings.retrieval_min_score:
                logger.debug("Skipping low-score chunk %.3f from %s", score, doc.metadata.get("source"))
                continue
            results.append(ScoredChunk(document=doc, score=score))

        logger.info(
            "Retrieved %d/%d chunks for query (min_score=%.2f)",
            len(results),
            k,
            self._settings.retrieval_min_score,
        )
        return results
