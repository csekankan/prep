"""
Central configuration via pydantic-settings.

WHY settings object instead of scattered os.environ reads:
- Inference gateways deploy across regions; the same code path must accept
  different rate limits, hedge delays, and worker counts without code changes.
- Type validation fails fast at process start (misconfigured KV-heavy decode
  limits are cheaper to catch in CI than under Black Friday traffic).

Teaching tie-in: when KV pool is exhausted on workers, you often *lower* admission
at the gateway (tokens/sec per tenant) while keeping compute quotas separate —
this file is where those knobs live.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "llm-serving-gateway-lab"
    debug: bool = False

    # Per-tenant token bucket (requests/sec burst at gateway edge).
    rate_limit_capacity: float = Field(
        default=5.0,
        description="Max burst of chat completion requests per tenant.",
    )
    rate_limit_refill_per_sec: float = Field(
        default=2.0,
        description="Steady-state refill rate (tokens/sec) for the bucket.",
    )

    # Circuit breaker on each mock worker.
    circuit_failure_threshold: int = 3
    circuit_open_seconds: float = 30.0
    circuit_half_open_max_calls: int = 1

    # Hedged retry: if primary worker is slow, fire duplicate to another worker.
    hedge_delay_ms: float = 50.0
    upstream_timeout_ms: float = 5000.0

    # Idempotency record TTL (in-memory lab default).
    idempotency_ttl_seconds: float = 3600.0

    # Mock worker fleet — latency/failure injected in upstream_pool.
    worker_count: int = 3
    worker_base_latency_ms: float = 20.0
    worker_failure_rate: float = 0.0

    log_json: bool = True


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached settings (reload cache in tests via get_settings.cache_clear())."""
    return Settings()
