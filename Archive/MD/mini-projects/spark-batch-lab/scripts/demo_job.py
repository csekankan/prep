#!/usr/bin/env python3
from spark_batch_lab.dag import BatchJob


def main() -> None:
    parts = [
        [{"country": "US", "rev": 100}],
        [{"country": "US", "rev": 200}],
        [{"country": "IN", "rev": 50}],
    ]
    job = BatchJob(partitions=parts)
    job.filter("positive", lambda r: r["rev"] > 0).group_sum("revenue_by_country", "country", "rev")
    out = job.run()
    print("Stages:", out["stages"])
    print("Shuffles:", out["shuffle_count"])
    print("Result:", out["result"])


if __name__ == "__main__":
    main()
