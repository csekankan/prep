# LLM Serving Gateway Lab

A **teaching mini-gateway** that sits in front of mock model workers. It mirrors patterns you see at OpenAI-scale inference edges: per-tenant token buckets, circuit breakers on unhealthy GPUs, hedged retries for tail latency, and Stripe-style idempotency for chat completions.

No real GPU — upstream workers are simulated with configurable latency and failure rates.

## Related reading (in this repo)

- [Inference engineering — prefill, decode, KV cache](../../inference-engineering/space-02-how-llm-inference-works/03-prefill-decode-kv-cache.md)
- [KV-Cache transformer prerequisites](../../KV-Cache-Transformer-Prerequisites.md)

## Quick start

```bash
cd MD/mini-projects/llm-serving-gateway-lab
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
uvicorn llm_serving_gateway.app:app --reload
```

### Example request

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: acme" \
  -H "Idempotency-Key: chat-001" \
  -d '{"model":"mock-llm","messages":[{"role":"user","content":"hello"}]}' | jq
```

Headers echoed for observability:

- `X-Request-Id` — gateway request id
- `traceparent` — W3C trace context stub (OpenTelemetry-compatible shape)

## HTTP semantics (429 vs 503)

| Status | Meaning in this lab |
|--------|---------------------|
| **429** | Tenant exceeded token-bucket rate — **client should back off**; the gateway is healthy. |
| **503** | Upstream workers unavailable (circuit open or all hedged attempts failed) — **retry with care**; capacity or health issue. |

## Layout

```
src/llm_serving_gateway/   # gateway implementation
tests/                     # httpx TestClient integration tests
scripts/                   # local demos
```

## License

Educational use within the docs monorepo.
