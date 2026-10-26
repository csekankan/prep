"""Fixed-window counter — simple per-minute limits (Redis INCR pattern)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class SlidingWindowLog:
    limit: int
    window_seconds: float
    _events: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        q = self._events[client_id]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
