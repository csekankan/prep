"""
Factory for chat models and embeddings.

WHY a factory?
  - Swapping OpenAI vs mock vs Bedrock should not rewrite your graph nodes.
  - Unit tests inject fakes here instead of patching network calls everywhere.
"""

from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from rag_chatbot.config import Settings, get_settings

logger = logging.getLogger(__name__)


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()

    if settings.llm_enabled:
        # Deferred import: keeps `pip install` fast when only running ingest.
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.chat_model,
            temperature=0.2,  # Low temp: factual support bot, less creative drift.
            timeout=60,
        )

    # Mock LLM: deterministic text so CI and learners work without API keys.
    # LangChain's FakeListChatModel cycles through canned responses.
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    logger.warning(
        "OPENAI_API_KEY not set — using FakeListChatModel. "
        "Retrieval still runs; answers use templates in graph nodes."
    )
    return FakeListChatModel(
        responses=[
            '{"route":"rag","needs_clarification":false,"sub_questions":["What does policy say?"],"reasoning":"mock"}',
            "MOCK_THINKING: Synthesized notes from retrieved chunks.",
            "MOCK_ANSWER: See citations in state; enable OPENAI_API_KEY for real prose.",
        ]
    )


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    provider = settings.embedding_provider.lower().strip()

    if provider == "openai":
        if not settings.llm_enabled:
            raise ValueError("EMBEDDING_PROVIDER=openai requires OPENAI_API_KEY")
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model="text-embedding-3-small")

    # Default: local model — no API cost, works offline after first download.
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},  # Makes cosine ≈ dot product
    )
