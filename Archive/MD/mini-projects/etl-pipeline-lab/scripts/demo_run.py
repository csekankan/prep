#!/usr/bin/env python3
from datetime import datetime, timezone

from etl_pipeline_lab.pipeline import EtlPipeline


def main() -> None:
    pipe = EtlPipeline()
    t0 = datetime(2026, 10, 26, 8, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc)
    r1 = pipe.run_incremental(
        [
            {"order_id": "a", "user_id": "u1", "amount_cents": 2500, "updated_at": t0},
            {"order_id": "b", "user_id": "u2", "amount_cents": 750, "updated_at": t0},
        ]
    )
    print("Batch 1:", r1)
    r2 = pipe.run_incremental(
        [{"order_id": "a", "user_id": "u1", "amount_cents": 3000, "updated_at": t1}]
    )
    print("Batch 2 (correction on order a):", r2)


if __name__ == "__main__":
    main()
