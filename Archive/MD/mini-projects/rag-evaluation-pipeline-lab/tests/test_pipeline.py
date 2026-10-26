"""End-to-end pipeline smoke tests."""

from __future__ import annotations

from pathlib import Path

from rag_eval_pipeline.pipeline import Thresholds, run_pipeline


def test_sample_dataset_pipeline_produces_passing_cases() -> None:
    dataset = Path(__file__).resolve().parents[1] / "sample_data" / "eval_set.jsonl"
    report = run_pipeline(
        dataset,
        thresholds=Thresholds(
            faithfulness=0.2,
            context_recall=0.4,
            answer_relevance=0.15,
        ),
    )
    assert report.num_cases >= 5
    assert report.pass_rate >= 0.8
    assert report.aggregate.context_recall >= 0.5
