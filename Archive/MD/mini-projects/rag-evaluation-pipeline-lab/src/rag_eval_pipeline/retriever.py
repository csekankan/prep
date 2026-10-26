"""In-memory vector retriever over hashed embeddings."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from rag_eval_pipeline.chunker import Chunk, chunk_documents
from rag_eval_pipeline.embeddings import cosine_similarity, text_to_vector


@dataclass
class RetrievalHit:
    chunk: Chunk
    score: float


class InMemoryRetriever:
    """Index chunks and retrieve top-k by cosine similarity."""

    def __init__(self, embedding_dim: int = 64) -> None:
        self.embedding_dim = embedding_dim
        self._chunks: list[Chunk] = []
        self._vectors: NDArray[np.float64] | None = None

    def ingest_documents(self, documents: list[str]) -> int:
        """Chunk and embed documents; returns number of chunks indexed."""
        self._chunks = chunk_documents(documents)
        if not self._chunks:
            self._vectors = None
            return 0
        matrix = np.vstack(
            [text_to_vector(c.text, self.embedding_dim) for c in self._chunks]
        )
        self._vectors = matrix
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        if not self._chunks or self._vectors is None:
            return []
        q = text_to_vector(query, self.embedding_dim)
        scores = [cosine_similarity(q, self._vectors[i]) for i in range(len(self._chunks))]
        ranked = sorted(
            zip(self._chunks, scores, strict=True),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            RetrievalHit(chunk=chunk, score=score)
            for chunk, score in ranked[:top_k]
        ]

    def context_strings(self, hits: list[RetrievalHit]) -> list[str]:
        return [h.chunk.text for h in hits]
