# Analytics sketches lab

Maps to [`fanout-system-design/10-analytics-and-sketches.md`](../../fanout-system-design/10-analytics-and-sketches.md).

HyperLogLog (cardinality) + Count-Min (frequency estimates) with heavy comments.

```bash
pip install -e ".[dev]"
pytest -q
python scripts/demo_cardinality.py
```
