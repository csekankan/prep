"""
Structured outputs — Pydantic models the LLM must fill.

WHY structured output?
  - Routing (RAG vs smalltalk) is a *classification* task — JSON schema reduces parse errors.
  - You can unit-test validators without calling the model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    """
    First graph step: decide HOW to handle the user message.

    route:
      - rag: need company docs (policies, product, runbook)
      - chat: general greeting / no doc lookup
      - clarify: user question too vague
    """

    route: Literal["rag", "chat", "clarify"] = Field(
        description="Whether to retrieve documents, reply directly, or ask a clarifying question."
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if critical details are missing from the user question.",
    )
    sub_questions: list[str] = Field(
        default_factory=list,
        description="For RAG: decompose complex questions into simpler retrieval queries.",
    )
    reasoning: str = Field(
        default="",
        description="Short internal note (shown in DEBUG / 'thinking' UI).",
    )
