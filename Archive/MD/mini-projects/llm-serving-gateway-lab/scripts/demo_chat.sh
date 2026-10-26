#!/usr/bin/env bash
# Local smoke test against a running gateway (uvicorn llm_serving_gateway.app:app).
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"

curl -sS "${BASE}/healthz" | jq .

curl -sS "${BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -H "Idempotency-Key: demo-$(date +%s)" \
  -d '{"model":"mock-llm","messages":[{"role":"user","content":"hello gateway"}]}' | jq .
