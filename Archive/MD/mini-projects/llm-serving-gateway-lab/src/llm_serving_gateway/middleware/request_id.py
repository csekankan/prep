"""
Request ID + W3C traceparent middleware.

WHY trace IDs at the gateway:
- A single chat completion may span prefill on worker A, decode on worker B after
  a reschedule, and KV cache eviction — without a trace id, you cannot correlate
  503s at the edge with KV pool exhaustion logs on the worker.
- OpenTelemetry propagates `traceparent`; we emit a compatible stub so clients
  and downstream mock workers can log the same correlation key.

Tail latency debugging: compare p50 gateway time vs p99 — if p99 lacks trace ids,
you only see "slow" without knowing which hedge attempt won.
"""

from __future__ import annotations

import logging
import secrets
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("llm_serving_gateway.access")


def _new_traceparent() -> str:
    """W3C trace context version 00: traceparent: 00-{trace_id}-{span_id}-01."""
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    return f"00-{trace_id}-{span_id}-01"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Assign X-Request-Id and traceparent on every request.

    Honors inbound X-Request-Id for client retries (same id → easier log grep).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        traceparent = request.headers.get("traceparent") or _new_traceparent()

        request.state.request_id = request_id
        request.state.traceparent = traceparent

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-Id"] = request_id
        response.headers["traceparent"] = traceparent

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "traceparent": traceparent,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(elapsed_ms, 2),
            },
        )
        return response
