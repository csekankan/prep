"""
Mock model worker pool with latency, failures, circuit breakers, and hedged retry.

WHY hedged retry:
- Tail latency dominates user-perceived quality in LLM APIs (p99 >> p50). A hedge
  sends a duplicate request to another worker if the first is slow — you pay extra
  compute on the duplicate but often win on latency. Production systems cap hedges
  to avoid doubling KV footprint.

WHY mock workers:
- Lab focuses on gateway behavior (429/503, idempotency, tracing) without GPUs.
- Real workers would expose queue depth, KV bytes used, and prefill/decode phase —
  we simulate with sleep() and random failures.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from llm_serving_gateway.circuit_breaker import CircuitBreaker
from llm_serving_gateway.config import Settings, get_settings

logger = logging.getLogger("llm_serving_gateway.upstream")


class UpstreamError(Exception):
    """Worker returned error or timed out."""


class UpstreamUnavailable(UpstreamError):
    """All workers rejected (circuit open or hedge failed)."""


@dataclass
class MockWorker:
    worker_id: str
    base_latency_ms: float
    failure_rate: float
    breaker: CircuitBreaker
    # Test hooks — force slow path for hedge demos.
    extra_latency_ms: float = 0.0
    force_fail: bool = False

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.breaker.allow_request():
            logger.warning("circuit_open", extra={"worker_id": self.worker_id})
            raise UpstreamUnavailable(f"worker {self.worker_id} circuit open")

        latency = (self.base_latency_ms + self.extra_latency_ms) / 1000.0
        await asyncio.sleep(latency)

        if self.force_fail or (self.failure_rate > 0 and random.random() < self.failure_rate):
            self.breaker.record_failure()
            logger.warning("worker_failure", extra={"worker_id": self.worker_id})
            raise UpstreamError(f"worker {self.worker_id} failed")

        self.breaker.record_success()
        content = _mock_completion_text(payload)
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": payload.get("model", "mock-llm"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": len(content.split()), "total_tokens": 20},
            "worker_id": self.worker_id,
        }


def _mock_completion_text(payload: dict[str, Any]) -> str:
    messages = payload.get("messages") or []
    user_bits = [m.get("content", "") for m in messages if m.get("role") == "user"]
    prompt = user_bits[-1] if user_bits else "hello"
    return f"[mock] echo: {prompt[:200]}"


@dataclass
class UpstreamPool:
    settings: Settings = field(default_factory=get_settings)
    workers: list[MockWorker] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.workers:
            self.workers = [
                MockWorker(
                    worker_id=f"worker-{i}",
                    base_latency_ms=self.settings.worker_base_latency_ms,
                    failure_rate=self.settings.worker_failure_rate,
                    breaker=CircuitBreaker(
                        failure_threshold=self.settings.circuit_failure_threshold,
                        open_seconds=self.settings.circuit_open_seconds,
                        half_open_max_calls=self.settings.circuit_half_open_max_calls,
                    ),
                )
                for i in range(self.settings.worker_count)
            ]

    def _pick_workers(self, count: int) -> list[MockWorker]:
        available = [w for w in self.workers if w.breaker.allow_request()]
        if not available:
            raise UpstreamUnavailable("no workers available")
        random.shuffle(available)
        return available[:count]

    async def _call_worker(self, worker: MockWorker, payload: dict[str, Any]) -> dict[str, Any]:
        timeout = self.settings.upstream_timeout_ms / 1000.0
        return await asyncio.wait_for(worker.complete(payload), timeout=timeout)

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Primary call with optional hedged duplicate after hedge_delay_ms.

        First successful response wins; losing tasks are cancelled.
        """
        workers = self._pick_workers(min(2, len(self.workers)))
        primary = workers[0]
        hedge_worker = workers[1] if len(workers) > 1 else None

        hedge_delay = self.settings.hedge_delay_ms / 1000.0
        tasks: list[asyncio.Task[dict[str, Any]]] = []

        async def run_primary() -> dict[str, Any]:
            return await self._call_worker(primary, payload)

        tasks.append(asyncio.create_task(run_primary()))

        async def maybe_hedge() -> dict[str, Any]:
            await asyncio.sleep(hedge_delay)
            if hedge_worker is None:
                raise UpstreamUnavailable("no hedge worker")
            logger.info(
                "hedge_fired",
                extra={"primary": primary.worker_id, "hedge": hedge_worker.worker_id},
            )
            return await self._call_worker(hedge_worker, payload)

        if hedge_worker is not None:
            tasks.append(asyncio.create_task(maybe_hedge()))

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                exc = task.exception()
                if exc is not None:
                    continue
                return task.result()
            # All completed tasks failed
            raise UpstreamUnavailable("all upstream attempts failed")
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

    async def chat_completion_stream_chunks(self, payload: dict[str, Any]) -> list[str]:
        """
        SSE stub: build chunk strings after one upstream completion.

        Real streaming would proxy token deltas as decode proceeds; here we split
        the final text to teach the wire format without a GPU decode loop.
        """
        result = await self.chat_completion(payload)
        text = result["choices"][0]["message"]["content"]
        chunks: list[str] = []
        for piece in text.split():
            chunk = {
                "id": result["id"],
                "object": "chat.completion.chunk",
                "choices": [{"index": 0, "delta": {"content": piece + " "}, "finish_reason": None}],
            }
            chunks.append(f"data: {json.dumps(chunk)}")
        chunks.append("data: [DONE]")
        return chunks
