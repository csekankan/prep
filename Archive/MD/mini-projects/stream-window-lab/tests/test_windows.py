from stream_window_lab.engine import WindowEngine
from stream_window_lab.models import StreamEvent


def test_tumbling_sum_per_key() -> None:
    eng = WindowEngine(window_size_ms=10, watermark_lag_ms=0)
    eng.ingest(StreamEvent(key="a", value=1, event_time_ms=1))
    eng.ingest(StreamEvent(key="a", value=2, event_time_ms=3))
    eng.ingest(StreamEvent(key="a", value=10, event_time_ms=12))
    eng.finalize()
    sums = sorted(r.sum_value for r in eng.results if r.key == "a")
    assert sums == [3.0, 10.0]


def test_late_event_within_allowed_lateness() -> None:
    # lateness must cover WM advance (200) past window end (100)
    eng = WindowEngine(window_size_ms=100, allowed_lateness_ms=150, watermark_lag_ms=0)
    eng.ingest(StreamEvent(key="k", value=1, event_time_ms=10))
    eng.ingest(StreamEvent(key="k", value=2, event_time_ms=200))  # advances WM
    eng.ingest(StreamEvent(key="k", value=3, event_time_ms=40))  # late but within lateness
    eng.finalize()
    first_window = [r for r in eng.results if r.window_start_ms == 0]
    assert first_window and first_window[-1].sum_value == 4.0
