# Data Engineering Labs

Companion projects for this folder. Each lab is **stdlib or light deps**, with **tests** and a **demo script**.

| Lab | Concepts practiced | Markdown |
|-----|-------------------|----------|
| [kafka-log-lab](../mini-projects/kafka-log-lab/) | Partitions, consumer groups, offsets, idempotent consume | [kafka/detailed.md](./kafka/detailed.md) |
| [etl-pipeline-lab](../mini-projects/etl-pipeline-lab/) | Bronze/silver/gold, validation, incremental load | [etl-elt/detailed.md](./etl-elt/detailed.md) |
| [spark-batch-lab](../mini-projects/spark-batch-lab/) | Lazy DAG, narrow/wide ops, shuffle, skew hints | [spark-pyspark/detailed.md](./spark-pyspark/detailed.md) |
| [stream-window-lab](../mini-projects/stream-window-lab/) | Event time, watermarks, windows, late data | [flink/detailed.md](./flink/detailed.md) |
| [airflow-dag-lab](../mini-projects/airflow-dag-lab/) | DAG scheduling, retries, backfill, task states | [airflow/detailed.md](./airflow/detailed.md) |

## Smoke all DE labs

```bash
cd MD/mini-projects
for d in kafka-log-lab etl-pipeline-lab spark-batch-lab stream-window-lab airflow-dag-lab; do
  echo "=== $d ==="
  (cd "$d" && pip install -q -e ".[dev]" && pytest -q) || exit 1
done
```

Also see [transaction-outbox-lab](../mini-projects/transaction-outbox-lab/) for **reliable publish to a log** (pairs with Kafka guide).
