"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from llm_serving_gateway.app import create_app
from llm_serving_gateway.config import Settings, get_settings
from llm_serving_gateway.upstream_pool import MockWorker, UpstreamPool
from llm_serving_gateway.circuit_breaker import CircuitBreaker


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return Settings(
        rate_limit_capacity=2.0,
        rate_limit_refill_per_sec=0.1,
        circuit_failure_threshold=3,
        circuit_open_seconds=60.0,
        worker_count=1,
        worker_base_latency_ms=1.0,
        worker_failure_rate=0.0,
        hedge_delay_ms=5.0,
        log_json=False,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def make_failing_pool(settings: Settings) -> UpstreamPool:
    breaker = CircuitBreaker(
        failure_threshold=settings.circuit_failure_threshold,
        open_seconds=settings.circuit_open_seconds,
    )
    worker = MockWorker(
        worker_id="worker-0",
        base_latency_ms=1.0,
        failure_rate=0.0,
        breaker=breaker,
        force_fail=True,
    )
    return UpstreamPool(settings=settings, workers=[worker])
