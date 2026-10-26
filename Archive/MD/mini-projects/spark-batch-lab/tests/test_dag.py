from spark_batch_lab.dag import BatchJob, salted_group_sum


def test_lazy_job_runs_group_with_shuffle() -> None:
    parts = [
        [{"country": "US", "rev": 10}, {"country": "UK", "rev": 5}],
        [{"country": "US", "rev": 7}],
    ]
    job = BatchJob(partitions=parts)
    job.filter("active", lambda r: r["rev"] > 0).group_sum("sum_by_country", "country", "rev")
    out = job.run()
    assert out["shuffle_count"] == 1
    by = {r["country"]: r["rev"] for r in out["result"]}
    assert by["US"] == 17.0
    assert by["UK"] == 5.0


def test_salted_group_matches_plain() -> None:
    rows = [{"k": "hot", "v": 100}] * 50 + [{"k": "cold", "v": 1}]
    plain = sum(r["v"] for r in rows if r["k"] == "hot")
    agg = salted_group_sum(rows, "k", "v", salts=8)
    by_k = {r["k"]: r["v"] for r in agg}
    assert by_k["hot"] == plain
