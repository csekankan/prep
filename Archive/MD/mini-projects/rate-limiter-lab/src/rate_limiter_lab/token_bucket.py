"""
Token bucket — smooth burst allowance (used at API gateways).

refill_rate: tokens per second
capacity: max burst size
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
