"""Stub answer generator (no LLM API)."""

from __future__ import annotations

import re

from rag_eval_pipeline.metrics import tokenize


def generate_answer_stub(question: str, contexts: list[str]) -> str:
    """
    Produce a deterministic answer from retrieved contexts.

    Mimics a grounded RAG response by stitching sentences that overlap the
    question; real systems would call an LLM with the same contexts.
    """
    if not contexts:
        return "I do not have enough context to answer."

    q_tokens = set(tokenize(question))
    chosen: list[str] = []
    for ctx in contexts:
        for sent in re.split(r"(?<=[.!?])\s+", ctx.strip()):
            sent = sent.strip()
            if not sent:
                continue
            stoks = set(tokenize(sent))
            if q_tokens & stoks:
                chosen.append(sent)
            if len(chosen) >= 2:
                break
        if len(chosen) >= 2:
            break

    if not chosen:
        first = contexts[0].strip()
        chosen = [first[:200] + ("..." if len(first) > 200 else "")]

    body = " ".join(chosen)
    return f"Based on the retrieved context: {body}"
