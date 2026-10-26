# Idempotency API lab

Maps to:

- [`real-world-engineering-case-studies/01-stripe-idempotency-keys.md`](../../real-world-engineering-case-studies/01-stripe-idempotency-keys.md)
- [`fanout-system-design/16-product-designs.md`](../../fanout-system-design/16-product-designs.md) (payments)

```bash
pip install -e ".[dev]"
uvicorn idempotency_api_lab.app:app --reload
pytest -q
```

**Flow:** `Idempotency-Key` header → store `STARTED` → process → `COMPLETE` with cached JSON body. Concurrent duplicate requests wait or get 409.
