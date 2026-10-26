# Inference scheduler lab

Maps to:

- [`inference-engineering/space-02-how-llm-inference-works/03-prefill-decode-kv-cache.md`](../../inference-engineering/space-02-how-llm-inference-works/03-prefill-decode-kv-cache.md)
- [`inference-engineering/space-04-serving-engine-fundamentals/`](../../inference-engineering/space-04-serving-engine-fundamentals/)

Discrete-event sim: prefill batches (compute-heavy) vs decode steps (memory-bandwidth-heavy), KV pool exhaustion → queue.

```bash
pip install -e ".[dev]"
python scripts/run_simulation.py
pytest -q
```
