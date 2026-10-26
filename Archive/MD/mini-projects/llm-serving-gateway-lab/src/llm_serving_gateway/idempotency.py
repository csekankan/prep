"""
Stripe-style idempotency for POST /v1/chat/completions.

WHY idempotency at the LLM gateway:
- Clients retry on timeouts (mobile networks, long decode). Without idempotency,
  a retry can **double-bill** tokens and double-append assistant messages.
- Same pattern as Stripe: Idempotency-Key header + request body fingerprint.

Production: Redis/Dynamo with TTL; in-flight requests return 409 or block until complete.
This lab uses in-memory storage (see idempotency-api-lab in the monorepo).
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class IdempotencyStatus(str, Enum):
    STARTED = "started"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class IdempotencyRecord:
    key: str
    status: IdempotencyStatus
    request_fingerprint: str
    response_status: int | None = None
    response_body: dict[str, Any] | None = None
    created_at: float = 0.0


class IdempotencyConflict(ValueError):
    """Key reused with different body."""


class IdempotencyInFlight(RuntimeError):
    """Another request with same key is executing."""


class IdempotencyStore:
    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._data: dict[str, IdempotencyRecord] = {}

    def fingerprint(self, body: dict[str, Any]) -> str:
        return json.dumps(body, sort_keys=True)

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, v in self._data.items() if now - v.created_at > self._ttl]
        for k in expired:
            del self._data[k]

    def begin(self, key: str, body: dict[str, Any]) -> IdempotencyRecord | None:
        """
        None → this caller should execute the handler.
        Record → replay stored response.
        """
        fp = self.fingerprint(body)
        with self._lock:
            self._purge_expired()
            existing = self._data.get(key)
            if existing is None:
                rec = IdempotencyRecord(
                    key=key,
                    status=IdempotencyStatus.STARTED,
                    request_fingerprint=fp,
                    created_at=time.time(),
                )
                self._data[key] = rec
                return None
            if existing.request_fingerprint != fp:
                raise IdempotencyConflict("idempotency key reused with different request body")
            if existing.status == IdempotencyStatus.COMPLETE:
                return existing
            if existing.status == IdempotencyStatus.STARTED:
                raise IdempotencyInFlight("request_in_flight")
        return None

    def complete(self, key: str, status_code: int, body: dict[str, Any]) -> None:
        with self._lock:
            rec = self._data[key]
            rec.status = IdempotencyStatus.COMPLETE
            rec.response_status = status_code
            rec.response_body = body

    def fail(self, key: str) -> None:
        with self._lock:
            if key in self._data:
                self._data[key].status = IdempotencyStatus.FAILED
