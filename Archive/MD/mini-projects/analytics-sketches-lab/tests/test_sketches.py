from analytics_sketches_lab.count_min import CountMinSketch
from analytics_sketches_lab.hyperloglog import HyperLogLog


def test_hll_within_ballpark() -> None:
    h = HyperLogLog(precision=14)
    for i in range(10_000):
        h.add(str(i))
    est = h.estimate()
    assert 8_000 < est < 12_500


def test_count_min_overestimate() -> None:
    cms = CountMinSketch(width=500, depth=7)
    for _ in range(100):
        cms.add("popular")
    assert cms.estimate("popular") >= 100
