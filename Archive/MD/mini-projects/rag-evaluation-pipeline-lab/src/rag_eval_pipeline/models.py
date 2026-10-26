"""Pydantic models for evaluation cases, results, and batch reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """One row in an evaluation dataset (question + references + corpus to index)."""

    id: str
    question: str
    reference_answer: str = Field(
        description="Gold answer used for regression checks and optional metric hints."
    )
    reference_contexts: list[str] = Field(
        default_factory=list,
        description="Contexts that *should* be retrieved for full context recall.",
    )
    corpus: list[str] = Field(
        description="Documents indexed before retrieval for this case.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricScores(BaseModel):
    """RAGAS-inspired scores in [0, 1] (higher is better)."""

    faithfulness: float = Field(ge=0.0, le=1.0)
    context_recall: float = Field(ge=0.0, le=1.0)
    answer_relevance: float = Field(ge=0.0, le=1.0)

    @property
    def mean(self) -> float:
        return (self.faithfulness + self.context_recall + self.answer_relevance) / 3.0


class EvalResult(BaseModel):
    """Outcome of running the pipeline on a single EvalCase."""

    case_id: str
    question: str
    retrieved_contexts: list[str]
    generated_answer: str
    scores: MetricScores
    passed: bool = Field(
        description="True when all metrics meet configured thresholds."
    )


class EvalReport(BaseModel):
    """Batch evaluation summary suitable for JSON export and CI gates."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dataset_path: str | None = None
    num_cases: int
    results: list[EvalResult]
    aggregate: MetricScores
    pass_rate: float = Field(ge=0.0, le=1.0)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
