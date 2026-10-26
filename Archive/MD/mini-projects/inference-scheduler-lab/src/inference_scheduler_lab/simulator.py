"""
Teaching scheduler — not vLLM, but captures the *capacity* story.

Each request:
  1. PREFILL(prompt_tokens) — costs compute_ms ∝ prompt length
  2. DECODE(n tokens) — each step costs decode_ms, holds KV until done
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Phase(str, Enum):
    QUEUED = "queued"
    PREFILL = "prefill"
    DECODE = "decode"
    DONE = "done"


@dataclass
class Request:
    req_id: str
    prompt_tokens: int
    completion_tokens: int
    kv_gib: float
    phase: Phase = Phase.QUEUED
    tokens_generated: int = 0


@dataclass
class SchedulerMetrics:
    completed: int = 0
    rejected: int = 0
    peak_kv_gib: float = 0.0


@dataclass
class InferenceSimulator:
    kv_pool_gib: float = 10.0
    kv_used_gib: float = 0.0
    queue: list[Request] = field(default_factory=list)
    active: list[Request] = field(default_factory=list)
    metrics: SchedulerMetrics = field(default_factory=SchedulerMetrics)

    def submit(self, req: Request) -> bool:
        """Accept into queue if we might serve later (simplified)."""
        self.queue.append(req)
        return True

    def _try_admit(self, req: Request) -> bool:
        if self.kv_used_gib + req.kv_gib <= self.kv_pool_gib:
            self.kv_used_gib += req.kv_gib
            self.metrics.peak_kv_gib = max(self.metrics.peak_kv_gib, self.kv_used_gib)
            self.active.append(req)
            return True
        return False

    def tick(self) -> None:
        """One abstract time step: admit from queue, advance one decode token for active."""
        while self.queue and len(self.active) < 8:
            head = self.queue[0]
            if self._try_admit(head):
                self.queue.pop(0)
                head.phase = Phase.PREFILL
            else:
                break

        for req in list(self.active):
            if req.phase == Phase.PREFILL:
                req.phase = Phase.DECODE
                continue
            if req.phase == Phase.DECODE:
                req.tokens_generated += 1
                if req.tokens_generated >= req.completion_tokens:
                    req.phase = Phase.DONE
                    self.active.remove(req)
                    self.kv_used_gib -= req.kv_gib
                    self.metrics.completed += 1

    def run_until_done(self, max_ticks: int = 100_000) -> SchedulerMetrics:
        for _ in range(max_ticks):
            if not self.queue and not self.active:
                break
            self.tick()
        return self.metrics


def kv_gib_for_prompt(prompt_tokens: int, kb_per_token: float = 320) -> float:
    return (prompt_tokens * kb_per_token * 1024) / (1024**3)
