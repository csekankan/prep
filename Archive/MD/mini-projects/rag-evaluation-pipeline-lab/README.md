# RAG evaluation pipeline lab

Offline batch evaluation for retrieval-augmented generation: chunk a corpus, retrieve with hash embeddings, generate a deterministic answer stub, and score **RAGAS-like** metrics without calling OpenAI or other judge models.

## Curriculum links

| Topic | Markdown |
|-------|----------|
| Embeddings & retrieval | [`ai-engineering-deep-dive/02-embeddings-and-retrieval/`](../../ai-engineering-deep-dive/02-embeddings-and-retrieval/) (start with [vector search](../../ai-engineering-deep-dive/02-embeddings-and-retrieval/06-vector-search.md)) |
| RAG foundations | [`ai-engineering-deep-dive/03-llm-foundations/05-retrieval-augmented-generation.md`](../../ai-engineering-deep-dive/03-llm-foundations/05-retrieval-augmented-generation.md) |
| Eval (RAGAS / DeepEval) | [`ai-engineering-curriculum/08-evaluation-ragas-deepeval.md`](../../ai-engineering-curriculum/08-evaluation-ragas-deepeval.md) |

## What you practice

- **Ingestion**: document → overlapping chunks (`chunker.py`)
- **Retrieval**: in-memory index + deterministic embeddings (`retriever.py`, `embeddings.py`)
- **Generation stub**: grounded answer template (`generator.py`) — swap for a real LLM in production
- **Metrics** (`metrics.py`): faithfulness heuristic, context recall, answer relevance (lexical + embedding similarity)
- **Batch pipeline** (`pipeline.py`): JSONL dataset → per-case results → aggregate `EvalReport` JSON
- **Production patterns**: Pydantic `EvalCase` / `EvalResult`, structured JSON logging, CLI with Rich

## Quick start

```bash
cd MD/mini-projects/rag-evaluation-pipeline-lab
pip install -e ".[dev]"
pytest -q
rag-eval --dataset sample_data/eval_set.jsonl --output reports/eval_report.json
```

CI-style gate (exit non-zero if pass rate drops):

```bash
rag-eval --fail-under 0.8
```

## Dataset format (`sample_data/eval_set.jsonl`)

Each line is one `EvalCase`:

- `id`, `question`, `reference_answer`
- `reference_contexts`: gold chunks needed for high **context recall**
- `corpus`: documents indexed before retrieval for that case

## Project layout

```
src/rag_eval_pipeline/
  chunker.py      # char windows with overlap
  embeddings.py   # feature-hash vectors (offline)
  retriever.py    # in-memory top-k cosine search
  generator.py    # no-LLM answer stub
  metrics.py      # RAGAS-inspired deterministic scores
  pipeline.py     # batch runner + JSON report
  cli.py          # rag-eval entrypoint
  models.py       # Pydantic schemas
  logging_config.py
sample_data/eval_set.jsonl
tests/
```

## Extending toward production

1. Replace hash embeddings with `sentence-transformers` or an API embedding model.
2. Swap `generate_answer_stub` for your production LLM with the same retrieved contexts.
3. Plug in [RAGAS](https://docs.ragas.io/) or DeepEval for LLM-as-judge metrics on a nightly job; keep this lab’s deterministic metrics in fast CI.
4. Store reports and diff aggregate scores on every prompt/retriever change (see curriculum doc).
