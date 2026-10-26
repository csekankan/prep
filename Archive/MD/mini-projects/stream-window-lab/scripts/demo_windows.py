#!/usr/bin/env python3
"""Tumbling 1-minute windows — on-time vs late event."""

from stream_window_lab.engine import WindowEngine
from stream_window_lab.models import StreamEvent

engine = WindowEngine(window_size_ms=60_000, allowed_lateness_ms=5_000, watermark_lag_ms=1_000)
events = [
    StreamEvent(key="user-1", value=10, event_time_ms=0),
    StreamEvent(key="user-1", value=5, event_time_ms=30_000),
    StreamEvent(key="user-1", value=100, event_time_ms=90_000),  # next window
]
for e in events:
    out = engine.ingest(e)
    for r in out:
        print(f"emit window [{r.window_start_ms},{r.window_end_ms}) sum={r.sum_value}")
engine.finalize()
