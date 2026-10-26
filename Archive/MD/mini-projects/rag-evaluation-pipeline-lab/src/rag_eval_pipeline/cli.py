"""CLI entrypoint with Rich tables."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from rag_eval_pipeline.logging_config import configure_logging
from rag_eval_pipeline.pipeline import Thresholds, run_pipeline, write_report

console = Console()


def _default_dataset() -> Path:
    return Path(__file__).resolve().parents[2] / "sample_data" / "eval_set.jsonl"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run offline RAG evaluation (RAGAS-like metrics, no API)."
    )
    p.add_argument(
        "--dataset",
        type=Path,
        default=_default_dataset(),
        help="JSONL file of EvalCase rows",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("reports/eval_report.json"),
        help="JSON report path",
    )
    p.add_argument("--top-k", type=int, default=3, help="Retrieval depth")
    p.add_argument("--faithfulness-min", type=float, default=0.35)
    p.add_argument("--context-recall-min", type=float, default=0.45)
    p.add_argument("--answer-relevance-min", type=float, default=0.25)
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    p.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="Exit 1 if pass_rate is below this fraction (CI gate)",
    )
    return p


def _print_report_table(report) -> None:
    table = Table(title="RAG evaluation results")
    table.add_column("Case")
    table.add_column("Faithfulness", justify="right")
    table.add_column("Ctx recall", justify="right")
    table.add_column("Ans relevance", justify="right")
    table.add_column("Pass", justify="center")
    for r in report.results:
        table.add_row(
            r.case_id,
            f"{r.scores.faithfulness:.2f}",
            f"{r.scores.context_recall:.2f}",
            f"{r.scores.answer_relevance:.2f}",
            "✓" if r.passed else "✗",
        )
    table.add_section()
    table.add_row(
        "MEAN",
        f"{report.aggregate.faithfulness:.2f}",
        f"{report.aggregate.context_recall:.2f}",
        f"{report.aggregate.answer_relevance:.2f}",
        f"{report.pass_rate * 100:.0f}%",
    )
    console.print(table)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(getattr(logging, args.log_level))
    thresholds = Thresholds(
        faithfulness=args.faithfulness_min,
        context_recall=args.context_recall_min,
        answer_relevance=args.answer_relevance_min,
    )
    if not args.dataset.is_file():
        console.print(f"[red]Dataset not found:[/red] {args.dataset}")
        return 2
    report = run_pipeline(args.dataset, top_k=args.top_k, thresholds=thresholds)
    write_report(report, args.output)
    _print_report_table(report)
    console.print(f"\nReport written to [bold]{args.output}[/bold]")
    if args.fail_under is not None and report.pass_rate < args.fail_under:
        console.print(
            f"[red]Pass rate {report.pass_rate:.2f} below gate {args.fail_under}[/red]"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
