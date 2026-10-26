"""
KV capacity math for design reviews (Part C §17, Part D §22–27).

This module is deliberately boring production code: typed models, pure functions,
unit tests—exactly what you'd put in a serving team's `capacity/` package.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field


class ModelKVProfile(BaseModel):
    """Architecture knobs that determine KV bytes per token."""

    num_layers: int = Field(80, description="Decoder layers (70B-class ≈ 80)")
    num_kv_heads: int = Field(8, description="GQA: fewer KV heads than Q heads")
    head_dim: int = Field(128, description="d_model / num_q_heads in many configs")
    bytes_per_element: int = Field(2, description="2=FP16 KV, 1=FP8 KV")
    kv_bytes_per_token_override: int | None = Field(
        None,
        description="If set, skip formula and use doc's round ~320KB/token",
    )

    def kv_bytes_per_token(self) -> int:
        if self.kv_bytes_per_token_override is not None:
            return self.kv_bytes_per_token_override
        return 2 * self.num_layers * self.num_kv_heads * self.head_dim * self.bytes_per_element


class RAGPromptBreakdown(BaseModel):
    """Part D §23 — token budget inside an 8k context."""

    system_and_tools: int = 800
    rag_chunks: int = 3200
    user_question: int = 200
    conversation_summary: int = 1500
    slack: int = 2492

    def total_tokens(self) -> int:
        return (
            self.system_and_tools
            + self.rag_chunks
            + self.user_question
            + self.conversation_summary
            + self.slack
        )


class GPUCapacityPlan(BaseModel):
    """Single-GPU concurrency sketch (Part D §27)."""

    gpu_hbm_gib: float = 80.0
    weight_gib: float = 70.0
    kv_pool_gib: float | None = None

    def effective_kv_pool_gib(self) -> float:
        if self.kv_pool_gib is not None:
            return self.kv_pool_gib
        return max(0.0, self.gpu_hbm_gib - self.weight_gib)


class KVSequenceEstimate(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    profile: ModelKVProfile
    block_size: int = 16

    def kv_gib_prefill(self) -> float:
        bpt = self.profile.kv_bytes_per_token()
        return (self.prompt_tokens * bpt) / (1024**3)

    def kv_gib_total_streaming(self) -> float:
        bpt = self.profile.kv_bytes_per_token()
        total_tokens = self.prompt_tokens + self.completion_tokens
        return (total_tokens * bpt) / (1024**3)

    def block_count(self, tokens: int) -> int:
        """Full blocks only (partial block still occupies a physical block in vLLM)."""
        return math.ceil(tokens / self.block_size)

    def blocks_for_prompt(self) -> int:
        return self.block_count(self.prompt_tokens)

    def blocks_for_streaming(self) -> int:
        return self.block_count(self.prompt_tokens + self.completion_tokens)


def max_concurrent_sequences(
    kv_pool_gib: float,
    sequence_kv_gib: float,
) -> int:
    """floor(pool / per_sequence) — request N+1 queues when pool is full."""
    if sequence_kv_gib <= 0:
        return 0
    return int(kv_pool_gib // sequence_kv_gib)


def format_ledger(estimate: KVSequenceEstimate, plan: GPUCapacityPlan) -> str:
    """Part D §30 one-page ledger as text."""
    pool = plan.effective_kv_pool_gib()
    prefill = estimate.kv_gib_prefill()
    streaming = estimate.kv_gib_total_streaming()
    concurrent = max_concurrent_sequences(pool, prefill)
    profile = estimate.profile
    bpt = profile.kv_bytes_per_token()
    lines = [
        "=== KV ledger (teaching lab) ===",
        f"KV bytes/token: {bpt:,} ({bpt/1024:.1f} KiB)",
        f"Prompt tokens: {estimate.prompt_tokens:,}",
        f"Prefill KV: {prefill:.2f} GiB",
        f"Blocks @ {estimate.block_size} tok/block: {estimate.blocks_for_prompt()}",
        f"+{estimate.completion_tokens} decode tokens → {streaming:.2f} GiB while streaming",
        f"KV pool (GPU): {pool:.1f} GiB → ~{concurrent} concurrent {estimate.prompt_tokens//1024}k-ish prompts",
    ]
    return "\n".join(lines)


# Preset matching the doc's worked example
DOC_70B_FP16 = ModelKVProfile(
    num_layers=80,
    num_kv_heads=8,
    head_dim=128,
    bytes_per_element=2,
    kv_bytes_per_token_override=320 * 1024,
)

DOC_8K_RAG = KVSequenceEstimate(
    prompt_tokens=8192,
    completion_tokens=150,
    profile=DOC_70B_FP16,
    block_size=16,
)

DOC_80GB_GPU = GPUCapacityPlan(gpu_hbm_gib=80, weight_gib=70)
