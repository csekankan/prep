"""Structured logging — same messages you'd ship to Datadog/CloudWatch in production."""

import logging
import sys

from rag_chatbot.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Basic format: timestamp | level | logger | message
    # In production you'd add JSON formatters + trace IDs from OpenTelemetry.
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )

    # Chroma and sentence-transformers can be noisy at INFO.
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
