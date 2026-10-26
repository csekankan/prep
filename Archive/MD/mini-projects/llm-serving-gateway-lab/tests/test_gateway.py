"""Integration tests for gateway HTTP semantics."""

from __future__ import annotations

from fastapi.testclient import TestClient

from llm_serving_gateway.app import create_app
from llm_serving_gateway.config import Settings
from tests.conftest import make_failing_pool

CHAT_BODY = {
    "model": "mock-llm",
    "messages": [{"role": "user", "content": "ping"}],
}


def test_rate_limit_returns_429(client: TestClient) -> None:
    headers = {"X-Tenant-Id": "burst-tenant"}
    for _ in range(2):
        r = client.post("/v1/chat/completions", json=CHAT_BODY, headers=headers)
        assert r.status_code == 200

    r = client.post("/v1/chat/completions", json=CHAT_BODY, headers=headers)
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limit_exceeded"
    assert "Retry-After" in r.headers


def test_circuit_opens_after_failures() -> None:
    settings = Settings(
        circuit_failure_threshold=3,
        circuit_open_seconds=60.0,
        worker_count=1,
        worker_base_latency_ms=1.0,
        rate_limit_capacity=100,
        rate_limit_refill_per_sec=100,
        log_json=False,
    )
    app = create_app(settings)
    app.state.upstream_pool = make_failing_pool(settings)

    with TestClient(app) as client:
        for _ in range(3):
            r = client.post("/v1/chat/completions", json=CHAT_BODY, headers={"X-Tenant-Id": "cb"})
            assert r.status_code == 503

        r = client.post("/v1/chat/completions", json=CHAT_BODY, headers={"X-Tenant-Id": "cb"})
        assert r.status_code == 503
        worker = app.state.upstream_pool.workers[0]
        assert worker.breaker.is_open


def test_idempotent_replay_same_response(client: TestClient) -> None:
    headers = {
        "X-Tenant-Id": "idem",
        "Idempotency-Key": "key-abc",
    }
    r1 = client.post("/v1/chat/completions", json=CHAT_BODY, headers=headers)
    assert r1.status_code == 200
    body1 = r1.json()

    r2 = client.post("/v1/chat/completions", json=CHAT_BODY, headers=headers)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body1["id"] == body2["id"]
    assert body1["choices"] == body2["choices"]


def test_trace_headers_present(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", json=CHAT_BODY, headers={"X-Tenant-Id": "trace"})
    assert r.status_code == 200
    assert r.headers.get("X-Request-Id")
    assert r.headers.get("traceparent", "").startswith("00-")


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}
