# Vector retrieval lab

Maps to:

- [`ai-engineering-deep-dive/02-embeddings-and-retrieval/06-vector-search.md`](../../ai-engineering-deep-dive/02-embeddings-and-retrieval/06-vector-search.md)
- [`fanout-system-design/09-search-and-retrieval.md`](../../fanout-system-design/09-search-and-retrieval.md) (ANN section)

```bash
cd MD/mini-projects/vector-retrieval-lab
pip install -e ".[dev]"
python scripts/run_search_compare.py
pytest -q
```

**What you build:** chunk → embed (hashing trick vectors) → brute-force top-k vs IVF (k-means clusters) with recall@k metrics.
