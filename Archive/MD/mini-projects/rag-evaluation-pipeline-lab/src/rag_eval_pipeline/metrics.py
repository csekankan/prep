"""Deterministic RAGAS-like metrics (no LLM-as-judge)."""

from __future__ import annotations

import re
from functools import lru_cache

from rag_eval_pipeline.embeddings import cosine_similarity, text_to_vector
from rag_eval_pipeline.models import MetricScores

_STOPWORDS = frozenset(
    """
    a an the and or but if in on at to for of is are was were be been being
    it this that with as by from into about than then so do does did has have had
    what which who how when where why can could should would will
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, stopwords removed."""
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in raw if t not in _STOPWORDS and len(t) > 1]


@lru_cache(maxsize=1)
def _content_tokens(text: str) -> frozenset[str]:
    return frozenset(tokenize(text))


def faithfulness(answer: str, retrieved_contexts: list[str]) -> float:
    """
    RAGAS **faithfulness** heuristic: fraction of answer content tokens supported by context.

    Full RAGAS decomposes claims and uses an LLM judge; here we approximate support as
    lexical overlap between the answer and the union of retrieved chunks.
    """
    answer_tokens = _content_tokens(answer)
    if not answer_tokens:
        return 0.0
    context_blob = " ".join(retrieved_contexts)
    ctx_tokens = _content_tokens(context_blob)
    if not ctx_tokens:
        return 0.0
    supported = sum(1 for t in answer_tokens if t in ctx_tokens)
    return supported / len(answer_tokens)


def context_recall(reference_contexts: list[str], retrieved_contexts: list[str]) -> float:
    """
    RAGAS **context recall** heuristic: coverage of reference context tokens in retrieval.

    Measures whether retrieval surfaced the information present in gold contexts
    (token recall over reference content).
    """
    ref_tokens: set[str] = set()
    for ref in reference_contexts:
        ref_tokens |= set(_content_tokens(ref))
    if not ref_tokens:
        return 1.0
    retrieved_blob = " ".join(retrieved_contexts)
    ret_tokens = set(_content_tokens(retrieved_blob))
    hit = sum(1 for t in ref_tokens if t in ret_tokens)
    return hit / len(ref_tokens)


def answer_relevance(question: str, answer: str) -> float:
    """
    RAGAS **answer relevancy** heuristic: semantic + lexical alignment of answer to question.

    Production RAGAS often embeds question/answer with a model and scores similarity;
    we blend hash-embedding cosine similarity with token overlap for stability offline.
    """
    q_toks = set(tokenize(question))
    a_toks = set(tokenize(answer))
    if not q_toks or not a_toks:
        return 0.0
    overlap = len(q_toks & a_toks) / len(q_toks)
    embed_sim = cosine_similarity(text_to_vector(question), text_to_vector(answer))
    embed_sim = max(0.0, min(1.0, (embed_sim + 1.0) / 2.0))
    return 0.5 * overlap + 0.5 * embed_sim


def score_all(
    question: str,
    answer: str,
    reference_contexts: list[str],
    retrieved_contexts: list[str],
) -> MetricScores:
    """Compute all metrics for one pipeline step."""
    return MetricScores(
        faithfulness=faithfulness(answer, retrieved_contexts),
        context_recall=context_recall(reference_contexts, retrieved_contexts),
        answer_relevance=answer_relevance(question, answer),
    )


def aggregate_scores(rows: list[MetricScores]) -> MetricScores:
    """Mean of each metric across cases."""
    if not rows:
        return MetricScores(faithfulness=0.0, context_recall=0.0, answer_relevance=0.0)
    n = len(rows)
    return MetricScores(
        faithfulness=sum(r.faithfulness for r in rows) / n,
        context_recall=sum(r.context_recall for r in rows) / n,
        answer_relevance=sum(r.answer_relevance for r in rows) / n,
    )
