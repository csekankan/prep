# Mini Python labs (companion to the MD curriculum)

Production-style **teaching projects**: `pyproject.toml`, `src/`, `tests/`, `scripts/`, README with links back to the markdown that inspired them.

## Flagship labs (hard concepts, production patterns)

These are the deepest projects — multi-module, tests, and patterns you would ship (gateways, quorum storage, RAG eval pipelines).

| Lab | Difficult concept | What you practice |
|-----|-------------------|-------------------|
| [**llm-serving-gateway-lab**](./llm-serving-gateway-lab/) | Large-scale LLM **serving** | Per-tenant rate limits, circuit breaker, hedged upstream calls, idempotent completions, SSE stub, trace IDs |
| [**distributed-shard-coordinator-lab**](./distributed-shard-coordinator-lab/) | **Distributed** partition + quorum | Consistent hash, RF/W/R, node failure, read repair, hinted handoff, stale reads |
| [**rag-evaluation-pipeline-lab**](./rag-evaluation-pipeline-lab/) | **RAG quality at scale** | Batch eval, faithfulness / recall / relevance metrics, JSON reports, CI `--fail-under` |

```bash
# Example: LLM gateway
cd MD/mini-projects/llm-serving-gateway-lab
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
uvicorn llm_serving_gateway.app:app --reload
```

## Existing full app (repo root)

| Project | Doc tie-in |
|---------|------------|
| [`../../multi-step-rag-chatbot`](../../multi-step-rag-chatbot) | RAG + LangGraph — `ai-engineering-deep-dive/03-llm-foundations/05-retrieval-augmented-generation.md` |

## AI / LLM / inference

| Lab | Markdown |
|-----|----------|
| [kv-transformer-lab](./kv-transformer-lab/) | [`KV-Cache-Transformer-Prerequisites.md`](../KV-Cache-Transformer-Prerequisites.md), `ai-engineering-deep-dive/04-llm-internals/` |
| [vector-retrieval-lab](./vector-retrieval-lab/) | `ai-engineering-deep-dive/02-embeddings-and-retrieval/06-vector-search.md` |
| [inference-scheduler-lab](./inference-scheduler-lab/) | `inference-engineering/space-02-how-llm-inference-works/03-prefill-decode-kv-cache.md` |
| [agent-tool-loop-lab](./agent-tool-loop-lab/) | `ai-engineering-deep-dive/09-mcp-and-agents/02-the-agent-loop.md` |
| [rag-evaluation-pipeline-lab](./rag-evaluation-pipeline-lab/) | `ai-engineering-curriculum/08-evaluation-ragas-deepeval.md` |
| [llm-serving-gateway-lab](./llm-serving-gateway-lab/) | `inference-engineering/`, [`KV-Cache-Transformer-Prerequisites.md`](../KV-Cache-Transformer-Prerequisites.md) |

## Data engineering

| Lab | Status | Markdown |
|-----|--------|----------|
| `transaction-outbox-lab` | **Exists** (shared with fanout/Kafka narrative) | `data-engineering/kafka/detailed.md` |
| [kafka-log-lab](./kafka-log-lab/) | **Exists** | `data-engineering/kafka/detailed.md` |
| [etl-pipeline-lab](./etl-pipeline-lab/) | **Exists** | `data-engineering/etl-elt/detailed.md` |
| [spark-batch-lab](./spark-batch-lab/) | **Exists** | `data-engineering/spark-pyspark/detailed.md` |
| [stream-window-lab](./stream-window-lab/) | **Exists** | `data-engineering/flink/detailed.md` |
| [airflow-dag-lab](./airflow-dag-lab/) | **Exists** | `data-engineering/airflow/detailed.md` |

## Data engineering

| Lab | Markdown |
|-----|----------|
| [kafka-log-lab](./kafka-log-lab/) | `data-engineering/kafka/detailed.md` |
| [etl-pipeline-lab](./etl-pipeline-lab/) | `data-engineering/etl-elt/detailed.md` |
| [spark-batch-lab](./spark-batch-lab/) | `data-engineering/spark-pyspark/detailed.md` |
| [stream-window-lab](./stream-window-lab/) | `data-engineering/flink/detailed.md` |
| [airflow-dag-lab](./airflow-dag-lab/) | `data-engineering/airflow/detailed.md` |
| [transaction-outbox-lab](./transaction-outbox-lab/) | `data-engineering/kafka/detailed.md`, `event-driven-architecture/` |

## Fanout / system design

| Lab | Markdown |
|-----|----------|
| [idempotency-api-lab](./idempotency-api-lab/) | [`real-world-engineering-case-studies/01-stripe-idempotency-keys.md`](../real-world-engineering-case-studies/01-stripe-idempotency-keys.md) |
| [consistent-hash-lab](./consistent-hash-lab/) | `fanout-system-design/04-nosql-partitioning-ids.md` |
| [distributed-shard-coordinator-lab](./distributed-shard-coordinator-lab/) | `fanout-system-design/04-nosql-partitioning-ids.md`, `06-distributed-coordination.md` |
| [bloom-filter-lab](./bloom-filter-lab/) | `fanout-system-design/04-nosql-partitioning-ids.md` |
| [rate-limiter-lab](./rate-limiter-lab/) | `fanout-system-design/14-reliability-and-operations.md`, `15-service-and-data-designs.md` |
| [bm25-search-lab](./bm25-search-lab/) | `fanout-system-design/09-search-and-retrieval.md` |
| [analytics-sketches-lab](./analytics-sketches-lab/) | `fanout-system-design/10-analytics-and-sketches.md` |
| [transaction-outbox-lab](./transaction-outbox-lab/) | `fanout-system-design/08-async-work-and-streams.md`, `event-driven-architecture/` |

## Run everything (smoke)

```bash
cd MD/mini-projects
for d in */; do
  echo "=== $d ==="
  (cd "$d" && pip install -q -e ".[dev]" && pytest -q) || exit 1
done
```

## Add a new lab

1. Create `MD/mini-projects/<name>-lab/` with the standard layout.
2. Link it from the relevant `LABS.md` in the MD folder.
3. Add a row to the table above.
