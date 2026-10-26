"""Document chunking for in-memory RAG indexing."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A slice of source text with stable id for retrieval logging."""

    chunk_id: str
    text: str
    source_doc_index: int


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def chunk_documents(
    documents: list[str],
    max_chars: int = 400,
    overlap_chars: int = 40,
) -> list[Chunk]:
    """
    Split documents into overlapping character windows.

    Production systems often use token-based chunking; char windows keep this lab
    dependency-free while still modeling multi-chunk corpora.
    """
    chunks: list[Chunk] = []
    for doc_idx, doc in enumerate(documents):
        text = _normalize_whitespace(doc)
        if not text:
            continue
        if len(text) <= max_chars:
            chunks.append(Chunk(f"{doc_idx}-0", text, doc_idx))
            continue
        start = 0
        part = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            slice_text = text[start:end]
            chunks.append(Chunk(f"{doc_idx}-{part}", slice_text, doc_idx))
            if end >= len(text):
                break
            start = max(0, end - overlap_chars)
            part += 1
    return chunks
