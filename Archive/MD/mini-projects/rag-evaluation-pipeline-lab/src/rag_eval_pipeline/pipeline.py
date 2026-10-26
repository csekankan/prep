"""Batch evaluation pipeline over a JSONL dataset."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from rag_eval_pipeline.generator import generate_answer_stub
from rag_eval_pipeline.logging_config import log_event
from rag_eval_pipeline.metrics import aggregate_scores, score_all
from rag_eval_pipeline.models import EvalCase, EvalReport, EvalResult, MetricScores
from rag_eval_pipeline.retriever import InMemoryRetriever

logger = logging.getLogger(__name__)


class Thresholds:
    """Per-metric minimum scores for CI-style pass/fail."""

    def __init__(
        self,
        faithfulness: float = 0.35,
        context_recall: float = 0.45,
        answer_relevance: float = 0.25,
    ) -> None:
        self.faithfulness = faithfulness
        self.context_recall = context_recall
        self.answer_relevance = answer_relevance

    def passes(self, scores: MetricScores) -> bool:
        return (
            scores.faithfulness >= self.faithfulness
            and scores.context_recall >= self.context_recall
            and scores.answer_relevance >= self.answer_relevance
        )


def load_eval_dataset(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(EvalCase.model_validate(data))
    log_event(logger, "dataset_loaded", path=str(path), num_cases=len(cases))
    return cases


def run_case(
    case: EvalCase,
    top_k: int = 3,
    thresholds: Thresholds | None = None,
) -> EvalResult:
    thresholds = thresholds or Thresholds()
    retriever = InMemoryRetriever()
    num_chunks = retriever.ingest_documents(case.corpus)
    hits = retriever.retrieve(case.question, top_k=top_k)
    contexts = retriever.context_strings(hits)
    answer = generate_answer_stub(case.question, contexts)
    scores = score_all(
        question=case.question,
        answer=answer,
        reference_contexts=case.reference_contexts,
        retrieved_contexts=contexts,
    )
    passed = thresholds.passes(scores)
    log_event(
        logger,
        "case_evaluated",
        case_id=case.id,
        chunks_indexed=num_chunks,
        retrieved=len(contexts),
        faithfulness=scores.faithfulness,
        context_recall=scores.context_recall,
        answer_relevance=scores.answer_relevance,
        passed=passed,
    )
    return EvalResult(
        case_id=case.id,
        question=case.question,
        retrieved_contexts=contexts,
        generated_answer=answer,
        scores=scores,
        passed=passed,
    )


def run_pipeline(
    dataset_path: Path,
    top_k: int = 3,
    thresholds: Thresholds | None = None,
) -> EvalReport:
    """Evaluate every case and build an aggregate report."""
    cases = load_eval_dataset(dataset_path)
    results = [run_case(c, top_k=top_k, thresholds=thresholds) for c in cases]
    aggregate = aggregate_scores([r.scores for r in results])
    passed = sum(1 for r in results if r.passed)
    pass_rate = passed / len(results) if results else 0.0
    report = EvalReport(
        dataset_path=str(dataset_path),
        num_cases=len(results),
        results=results,
        aggregate=aggregate,
        pass_rate=pass_rate,
    )
    log_event(
        logger,
        "pipeline_complete",
        num_cases=report.num_cases,
        pass_rate=report.pass_rate,
        mean_faithfulness=report.aggregate.faithfulness,
        mean_context_recall=report.aggregate.context_recall,
        mean_answer_relevance=report.aggregate.answer_relevance,
    )
    return report


def write_report(report: EvalReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log_event(logger, "report_written", path=str(output_path))
