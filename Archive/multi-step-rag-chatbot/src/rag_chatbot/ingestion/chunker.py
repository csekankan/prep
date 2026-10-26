"""
Document chunking for RAG.

KEY IDEA: Embeddings represent a *piece* of text. If chunks are too large,
  retrieval returns vague blobs. If too small, you lose context (e.g. a table
  split across chunks).

We use LangChain's RecursiveCharacterTextSplitter — tries paragraph breaks,
  then newlines, then spaces, so splits respect document structure when possible.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_markdown_files(docs_dir: Path) -> list[Document]:
    """Read all .md files and attach metadata used for citations in answers."""
    documents: list[Document] = []
    for path in sorted(docs_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "path": str(path),
                },
            )
        )
    return documents


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[Document]:
    """
    Split documents into overlapping chunks.

    chunk_overlap: trailing text repeated in the next chunk so sentences
    spanning a boundary aren't cut in half semantically.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)
