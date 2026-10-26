"""
Central configuration — production apps avoid scattering os.getenv() calls.

We use pydantic-settings so:
  - Types are validated at startup (fail fast).
  - .env is loaded once in a predictable order.
  - Tests can override settings without touching the filesystem.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All environment-driven knobs for the demo app."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    chat_model: str = Field(default="gpt-4o-mini", alias="CHAT_MODEL")

    # --- Embeddings ---
    # "local" = Sentence-Transformers (free, good for learning).
    # "openai" = paid API, closer to many production stacks.
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")

    # --- Vector store ---
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma"),
        alias="CHROMA_PERSIST_DIR",
    )
    chroma_collection: str = Field(default="acme_knowledge", alias="CHROMA_COLLECTION")

    # --- Retrieval ---
    # How many chunks to pull into the "thinking" step.
    retrieval_top_k: int = 4
    # Minimum similarity score (Chroma returns distance; we convert in retriever).
    retrieval_min_score: float = 0.35

    # --- Paths ---
    sample_docs_dir: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent / "sample_docs"
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def llm_enabled(self) -> bool:
        """True when we can call OpenAI; False triggers MOCK answers for offline demos."""
        return bool(self.openai_api_key and self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe to call from any module."""
    return Settings()
