"""
Chroma vector store wrapper.

Chroma is an embedded DB (SQLite + vectors on disk) — great for learning and
small/medium production workloads. At very large scale you'd consider Pinecone,
pgvector, Weaviate, etc. The *retrieval interface* stays similar in LangChain.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from rag_chatbot.config import Settings, get_settings


def get_vector_store(
    embeddings: Embeddings,
    settings: Settings | None = None,
) -> VectorStore:
    settings = settings or get_settings()
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )
