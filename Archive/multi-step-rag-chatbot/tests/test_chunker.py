"""Unit tests — chunking is deterministic and cheap to test without LLM APIs."""

from pathlib import Path

from rag_chatbot.ingestion.chunker import chunk_documents, load_markdown_files


def test_load_sample_docs():
    root = Path(__file__).resolve().parent.parent
    docs = load_markdown_files(root / "sample_docs")
    assert len(docs) >= 3
    assert all(d.metadata.get("source") for d in docs)


def test_chunk_overlap_produces_multiple_chunks():
    root = Path(__file__).resolve().parent.parent
    docs = load_markdown_files(root / "sample_docs")
    chunks = chunk_documents(docs, chunk_size=400, chunk_overlap=50)
    assert len(chunks) > len(docs)
