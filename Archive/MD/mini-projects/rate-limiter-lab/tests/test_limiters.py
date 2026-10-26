from rate_limiter_lab.sliding_window import SlidingWindowLog
from rate_limiter_lab.token_bucket import TokenBucket


def test_token_bucket_burst() -> None:
    b = TokenBucket.create(capacity=3, refill_rate=100)
    assert b.allow() and b.allow() and b.allow()
    assert not b.allow()


def test_sliding_window() -> None:
    w = SlidingWindowLog(limit=2, window_seconds=60)
    assert w.allow("u1") and w.allow("u1")
    assert not w.allow("u1")
