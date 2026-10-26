"""
Circuit breaker per upstream worker.

WHY breakers on inference workers:
- A GPU with bad ECC, OOM loops, or stuck NCCL collectives can absorb retries and
  amplify tail latency for the whole fleet. Opening the circuit sheds load fast.
- This is distinct from **KV pool exhaustion**: that often returns 503 with
  "capacity" semantics but the process is alive — breakers target *unhealthy*
  endpoints (error storms), not intentional admission denial.

States:
- CLOSED: normal traffic
- OPEN: fail fast (503 at gateway) until cooldown
- HALF_OPEN: probe with limited calls before fully closing again
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int
    open_seconds: float
    half_open_max_calls: int = 1

    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0
    half_open_calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.opened_at >= self.open_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
                return False
            # HALF_OPEN
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self.consecutive_failures = 0
            if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                self.state = CircuitState.CLOSED
                self.half_open_calls = 0

    def record_failure(self) -> None:
        with self._lock:
            self.consecutive_failures += 1
            if self.state == CircuitState.HALF_OPEN:
                self._trip()
                return
            if self.state == CircuitState.CLOSED and self.consecutive_failures >= self.failure_threshold:
                self._trip()

    def _trip(self) -> None:
        self.state = CircuitState.OPEN
        self.opened_at = time.monotonic()
        self.half_open_calls = 0

    @property
    def is_open(self) -> bool:
        with self._lock:
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.opened_at >= self.open_seconds:
                    return False
                return True
            return False
