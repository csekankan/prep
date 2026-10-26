"""
Token bucket — smooth bursts for per-tenant admission control.

WHY token bucket at the LLM gateway (not fixed window):
- Chat bursts (many users clicking "regenerate") are bursty; buckets allow short
  spikes without starving steady traffic.
- KV memory pressure on workers is *not* the same as request count — production
  gateways often charge "tokens" per request. Here we use one token per HTTP
  completion for simplicity; the same machinery scales to weighted costs.

429 vs 503:
- **429** means "you exceeded *your* contract" — gateway is up, workers may be fine.
- **503** means "we cannot serve *anyone* right now" — often upstream or KV exhaustion.
  Do not confuse them in client retry logic (429 → backoff; 503 → jitter + failover).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float
    tokens: float
    last_refill: float

    @classmethod
    def create(cls, capacity: float, refill_rate: float) -> TokenBucket:
        now = time.monotonic()
        return cls(capacity=capacity, refill_rate=refill_rate, tokens=capacity, last_refill=now)

    def _refill(self, now: float) -> None:
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def allow(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        self._refill(now)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def retry_after_seconds(self, cost: float = 1.0) -> float:
        """Hint for Retry-After header when allow() is False."""
        now = time.monotonic()
        self._refill(now)
        deficit = cost - self.tokens
        if deficit <= 0:
            return 0.0
        return deficit / self.refill_rate if self.refill_rate > 0 else 60.0
