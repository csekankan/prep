"""
Mini stream processor: tumbling event-time windows + watermarks.

Production Flink does this distributed with checkpointed state; here we process
a sorted batch of events to make window boundaries easy to test and debug.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from stream_window_lab.models import StreamEvent, WindowResult


@dataclass
class WindowEngine:
    """
    Tumbling windows on event time.

    window_size_ms: bucket width (e.g. 60_000 = 1 minute)
    allowed_lateness_ms: after watermark passes window end, still accept late events
    watermark_lag_ms: watermark = max_event_time_seen - lag (simulates bounded disorder)
    """

    window_size_ms: int
    allowed_lateness_ms: int = 0
    watermark_lag_ms: int = 0
    _max_event_time: int = 0
    _buffers: dict[tuple[str, int], list[StreamEvent]] = field(default_factory=lambda: defaultdict(list))
    _last_emitted_sum: dict[tuple[str, int], float] = field(default_factory=dict)
    results: list[WindowResult] = field(default_factory=list)
    late_dropped: int = 0

    def _window_start(self, event_time_ms: int) -> int:
        return (event_time_ms // self.window_size_ms) * self.window_size_ms

    def _watermark(self) -> int:
        return max(0, self._max_event_time - self.watermark_lag_ms)

    def ingest(self, event: StreamEvent) -> list[WindowResult]:
        """
        Process one event; may emit zero or more closed window aggregates.

        Returns newly emitted WindowResult rows (on-time or late correction).
        """
        self._max_event_time = max(self._max_event_time, event.event_time_ms)
        w_start = self._window_start(event.event_time_ms)
        w_end = w_start + self.window_size_ms
        key = (event.key, w_start)

        wm = self._watermark()
        # Past allowed lateness: watermark moved beyond window_end + lateness
        if wm > w_end + self.allowed_lateness_ms and key in self._last_emitted_sum:
            self.late_dropped += 1
            return []

        self._buffers[key].append(event)
        return self._flush_ready_windows()

    def _flush_ready_windows(self) -> list[WindowResult]:
        """Emit windows whose end (+ lateness) is <= current watermark."""
        wm = self._watermark()
        new: list[WindowResult] = []
        for (k, w_start), events in list(self._buffers.items()):
            w_end = w_start + self.window_size_ms
            if w_end + self.allowed_lateness_ms > wm:
                continue
            if not events:
                continue
            total = sum(e.value for e in events)
            prev = self._last_emitted_sum.get((k, w_start))
            if prev is not None and prev == total:
                continue
            self._last_emitted_sum[(k, w_start)] = total
            on_time = w_end <= wm
            res = WindowResult(
                window_start_ms=w_start,
                window_end_ms=w_end,
                key=k,
                sum_value=total,
                count=len(events),
                on_time=on_time,
            )
            new.append(res)
            self.results.append(res)
        return new

    def finalize(self) -> list[WindowResult]:
        """End of stream: force watermark to infinity and flush remaining."""
        self._max_event_time += 10**15
        return self._flush_ready_windows()
