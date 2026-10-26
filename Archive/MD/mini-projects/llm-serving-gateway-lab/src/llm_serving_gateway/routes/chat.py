"""
OpenAI-compatible chat completions route (non-stream + SSE stub).

WHY gateway owns this endpoint:
- Central place for rate limits, idempotency, auth, and routing to the right
  model pool (prefill-heavy vs decode-heavy) before traffic hits KV memory.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from llm_serving_gateway.idempotency import (
    IdempotencyConflict,
    IdempotencyInFlight,
    IdempotencyStore,
)
from llm_serving_gateway.rate_limit import TenantRateLimiter
from llm_serving_gateway.upstream_pool import UpstreamPool, UpstreamUnavailable

logger = logging.getLogger("llm_serving_gateway.chat")

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "mock-llm"
    messages: list[ChatMessage]
    stream: bool = False
    max_tokens: int | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)


def _get_limiter(request: Request) -> TenantRateLimiter:
    return request.app.state.tenant_limiter


def _get_pool(request: Request) -> UpstreamPool:
    return request.app.state.upstream_pool


def _get_idempotency(request: Request) -> IdempotencyStore:
    return request.app.state.idempotency_store


@router.post("/chat/completions")
async def create_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> Any:
    limiter = _get_limiter(request)
    pool = _get_pool(request)
    store = _get_idempotency(request)

    allowed, retry_after = limiter.check(x_tenant_id)
    if not allowed:
        # 429: tenant contract — not the same as worker KV exhaustion (often 503).
        logger.info(
            "rate_limited",
            extra={"tenant_id": x_tenant_id, "retry_after": retry_after},
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "message": "Rate limit exceeded for tenant",
                    "type": "rate_limit_error",
                    "code": "rate_limit_exceeded",
                }
            },
            headers={"Retry-After": str(int(max(1, retry_after)))},
        )

    payload = body.model_dump()

    if idempotency_key:
        try:
            cached = store.begin(idempotency_key, payload)
            if cached is not None and cached.response_body is not None:
                replay = cached.response_body
                status = cached.response_status or 200
                logger.info(
                    "idempotency_replay",
                    extra={"tenant_id": x_tenant_id, "idempotency_key": idempotency_key},
                )
                if body.stream:
                    return _stream_replay(replay)
                return JSONResponse(status_code=status, content=replay)
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except IdempotencyInFlight as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    if body.stream:
        return await _handle_stream(request, pool, store, idempotency_key, payload, x_tenant_id)

    try:
        result = await pool.chat_completion(payload)
    except UpstreamUnavailable as exc:
        logger.warning("upstream_unavailable", extra={"tenant_id": x_tenant_id, "detail": str(exc)})
        if idempotency_key:
            store.fail(idempotency_key)
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Upstream model workers unavailable",
                    "type": "server_error",
                    "code": "upstream_unavailable",
                }
            },
        ) from exc

    if idempotency_key:
        store.complete(idempotency_key, 200, result)

    return JSONResponse(content=result)


async def _handle_stream(
    request: Request,
    pool: UpstreamPool,
    store: IdempotencyStore,
    idempotency_key: str | None,
    payload: dict[str, Any],
    tenant_id: str,
) -> StreamingResponse:
    try:
        chunks = await pool.chat_completion_stream_chunks(payload)
    except UpstreamUnavailable as exc:
        if idempotency_key:
            store.fail(idempotency_key)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if idempotency_key:
        # Store minimal completion for replay (non-stream body shape).
        full = await pool.chat_completion(payload)
        store.complete(idempotency_key, 200, full)

    async def event_generator():
        for line in chunks:
            yield f"{line}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _stream_replay(body: dict[str, Any]) -> StreamingResponse:
    text = body["choices"][0]["message"]["content"]

    async def gen():
        for piece in text.split():
            chunk = {
                "object": "chat.completion.chunk",
                "choices": [{"delta": {"content": piece + " "}}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
