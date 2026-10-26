"""Metric behavior: good vs bad retrieval and grounding."""

from __future__ import annotations

from rag_eval_pipeline.generator import generate_answer_stub
from rag_eval_pipeline.metrics import (
    answer_relevance,
    context_recall,
    faithfulness,
    score_all,
)
from rag_eval_pipeline.retriever import InMemoryRetriever


QUESTION = "What is the refund window for purchases?"
REFERENCE = [
    "Section 4 — Refunds: Customers may request refunds within 30 days of purchase."
]
GOOD_CORPUS = [
    "Section 4 — Refunds: Customers may request refunds within 30 days of purchase. Receipt required.",
    "Section 9 — Shipping: Standard delivery takes 5-7 business days.",
]
BAD_CORPUS = [
    "Section 9 — Shipping: Standard delivery takes 5-7 business days.",
    "Employee handbook: Parking is available in lot B.",
]


def _retrieve_contexts(corpus: list[str], top_k: int = 2) -> list[str]:
    r = InMemoryRetriever()
    r.ingest_documents(corpus)
    return r.context_strings(r.retrieve(QUESTION, top_k=top_k))


def test_context_recall_good_beats_bad_retrieval() -> None:
    good_ctx = _retrieve_contexts(GOOD_CORPUS)
    bad_ctx = _retrieve_contexts(BAD_CORPUS)
    good_score = context_recall(REFERENCE, good_ctx)
    bad_score = context_recall(REFERENCE, bad_ctx)
    assert good_score > bad_score
    assert good_score >= 0.5
    assert bad_score < 0.3


def test_faithfulness_grounded_answer_beats_hallucination() -> None:
    contexts = _retrieve_contexts(GOOD_CORPUS)
    grounded = generate_answer_stub(QUESTION, contexts)
    hallucinated = (
        "Refunds are never allowed and all sales are final after 24 hours."
    )
    assert faithfulness(grounded, contexts) > faithfulness(hallucinated, contexts)


def test_answer_relevance_question_alignment() -> None:
    contexts = _retrieve_contexts(GOOD_CORPUS)
    on_topic = generate_answer_stub(QUESTION, contexts)
    off_topic = "Parking is available in lot B near the main entrance."
    assert answer_relevance(QUESTION, on_topic) > answer_relevance(QUESTION, off_topic)


def test_score_all_monotonic_with_retrieval_quality() -> None:
    good = score_all(
        QUESTION,
        generate_answer_stub(QUESTION, _retrieve_contexts(GOOD_CORPUS)),
        REFERENCE,
        _retrieve_contexts(GOOD_CORPUS),
    )
    bad = score_all(
        QUESTION,
        generate_answer_stub(QUESTION, _retrieve_contexts(BAD_CORPUS)),
        REFERENCE,
        _retrieve_contexts(BAD_CORPUS),
    )
    assert good.context_recall > bad.context_recall
    assert good.mean > bad.mean
