"""
Ingestion pipeline — run once (or on a schedule in production) to refresh the index.

Production pattern:
  - Event-driven: S3 upload → Lambda → embed → vector DB
  - Batch: Airflow DAG nightly
  - This demo: `rag-ingest` CLI after you edit sample_docs/
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from rag_chatbot.config import get_settings
from rag_chatbot.ingestion.chunker import chunk_documents, load_markdown_files
from rag_chatbot.ingestion.vector_store import get_vector_store
from rag_chatbot.llm_factory import build_embeddings
from rag_chatbot.logging_setup import configure_logging

logger = logging.getLogger(__name__)


def ingest(docs_dir: Path | None = None, reset: bool = False) -> int:
    """
    Load markdown, chunk, embed, and upsert into Chroma.

    Returns number of chunks indexed.
    """
    settings = get_settings()
    docs_dir = docs_dir or settings.sample_docs_dir

    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")

    raw_docs = load_markdown_files(docs_dir)
    if not raw_docs:
        logger.warning("No .md files found in %s", docs_dir)
        return 0

    chunks = chunk_documents(raw_docs)
    logger.info("Loaded %d files → %d chunks", len(raw_docs), len(chunks))

    embeddings = build_embeddings(settings)
    store = get_vector_store(embeddings, settings)

    if reset:
        # Chroma collection delete + recreate — simple for demos.
        # Production: version collections (blue/green) to avoid downtime.
        logger.info("Resetting collection %s", settings.chroma_collection)
        store.delete_collection()
        store = get_vector_store(embeddings, settings)

    # add_documents embeds each chunk and stores vector + metadata + text.
    store.add_documents(chunks)
    logger.info("Indexed %d chunks into %s", len(chunks), settings.chroma_persist_dir)
    return len(chunks)


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Ingest sample_docs into Chroma")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help="Override path to markdown folder (default: sample_docs/)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the Chroma collection before ingest",
    )
    args = parser.parse_args()
    ingest(docs_dir=args.docs_dir, reset=args.reset)


if __name__ == "__main__":
    main()
