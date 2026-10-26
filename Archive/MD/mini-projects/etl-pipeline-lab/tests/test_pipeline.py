from datetime import datetime, timezone

from etl_pipeline_lab.pipeline import EtlPipeline, ValidationError


def _row(oid: str, cents: int, ts: datetime) -> dict:
    return {
        "order_id": oid,
        "user_id": "u1",
        "amount_cents": cents,
        "updated_at": ts,
    }


def test_medallion_happy_path() -> None:
    t0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
    t1 = datetime(2026, 10, 2, tzinfo=timezone.utc)
    pipe = EtlPipeline()
    pipe.run_incremental([_row("o1", 1000, t0)])
    assert pipe.gold_revenue_usd == 10.0
    pipe.run_incremental([_row("o1", 1500, t1)])
    assert pipe.silver["o1"].amount_usd == 15.0
    assert pipe.gold_revenue_usd == 15.0


def test_validation_rejects_bad_amount() -> None:
    t0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
    pipe = EtlPipeline()
    try:
        pipe.run_incremental([_row("o1", -1, t0)])
        assert False, "expected ValidationError"
    except ValidationError:
        pass
