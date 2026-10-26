"""
Event-time tumbling windows with watermarks and allowed lateness (Flink teaching model).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WindowConfig:
    window_size_ms: int = 5000
    allowed_lateness_ms: int = 1000
    max_out_of_orderness_ms: int = 2000


@dataclass
class StreamProcessor:
    config: WindowConfig = field(default_factory=WindowConfig)
    _watermark_ms: int = 0
    _closed: dict[int, float] = field(default_factory=dict)  # window_start -> sum
    _emitted: list[dict[str, Any]] = field(default_factory=list)

    def _window_start(self, event_time_ms: int) -> int:
        w = self.config.window_size_ms
        return (event_time_ms // w) * w

    def on_event(self, event_time_ms: int, value: float) -> None:
        """Process one event; update watermark from event time minus max skew."""
        self._watermark_ms = max(
            self._watermark_ms,
            event_time_ms - self.config.max_out_of_orderness_ms,
        )
        wstart = self._window_start(event_time_ms)
        close_at = wstart + self.config.window_size_ms

        if event_time_ms < wstart:
            return

        # Late but within allowed lateness after window would close
        if close_at <= self._watermark_ms - self.config.allowed_lateness_ms:
            if event_time_ms < close_at:
                return  # too late, drop

        self._closed[wstart] = self._closed.get(wstart, 0.0) + value

    def flush_ready_windows(self) -> list[dict[str, Any]]:
        """Emit aggregates for windows that watermark closed (+ lateness)."""
        out: list[dict[str, Any]] = []
        w = self.config.window_size_ms
        for wstart in sorted(self._closed.keys()):
            close_at = wstart + w
            if close_at <= self._watermark_ms:
                total = self._closed.pop(wstart)
                row = {"window_start_ms": wstart, "sum": total, "watermark_ms": self._watermark_ms}
                self._emitted.append(row)
                out.append(row)
        return out
