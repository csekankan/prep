"""
In-memory idempotency store (Stripe pattern).

Production: Redis + TTL, or DynamoDB with conditional writes.
See: real-world-engineering-case-studies/01-stripe-idempotency-keys.md
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


class IdempotencyStore:
    """
    Thread-safe store for teaching concurrency semantics.

    - Same key + same body → return stored response
    - Same key + different body → 422 (Stripe returns error)
    - Key in STARTED → caller should poll or return 409
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, IdempotencyRecord] = {}

    def fingerprint(self, body: dict[str, Any]) -> str:
        return json.dumps(body, sort_keys=True)

    def begin(self, key: str, body: dict[str, Any]) -> IdempotencyRecord | None:
        """
        Returns None if this caller should execute the handler.
        Returns record if cached complete response should be replayed.
        Raises ValueError if key reuse with different payload.
        """
        fp = self.fingerprint(body)
        with self._lock:
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
                raise ValueError("idempotency key reused with different request body")
            if existing.status == IdempotencyStatus.COMPLETE:
                return existing
            if existing.status == IdempotencyStatus.STARTED:
                raise RuntimeError("request_in_flight")
        return None

    def complete(self, key: str, status_code: int, body: dict[str, Any]) -> None:
        with self._lock:
            rec = self._data[key]
            rec.status = IdempotencyStatus.COMPLETE
            rec.response_status = status_code
            rec.response_body = body
