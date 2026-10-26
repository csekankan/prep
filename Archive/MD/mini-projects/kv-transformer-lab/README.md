# KV Transformer Lab

NumPy-only mini engine pieces that mirror [`KV-Cache-Transformer-Prerequisites.md`](../../KV-Cache-Transformer-Prerequisites.md).

## Mental model

```text
Token IDs → embeddings → [DecoderLayer × N] → logits
                              ↑
                    K,V appended per layer during decode
```

## Run demos

From this directory (after `pip install -e .`):

| Script | Teaches |
|--------|---------|
| `scripts/run_attention_demo.py` | Causal self-attention weights on a toy sentence |
| `scripts/run_decoder_demo.py` | One decoder block forward pass + tensor shapes |
| `scripts/run_kv_compare.py` | Naive full-sequence recompute vs KV cache (work counters) |
| `scripts/run_capacity_planner.py` | 8k RAG KV GB, blocks, concurrent slots on 80GB GPU |
| `scripts/run_paged_pool_demo.py` | vLLM-style block pool + prefix sharing |

## Tests

```bash
pytest -q
```

Tests lock the **capacity formulas** and **block allocator** behavior to the numbers in Part D of the doc.
