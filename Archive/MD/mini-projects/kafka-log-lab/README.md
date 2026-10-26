# Kafka log lab

In-memory **partitioned log**, **consumer group offsets**, and **idempotent** consume-by-`event_id`—the patterns behind Kafka at-least-once processing.

## Curriculum

[`../../data-engineering/kafka/detailed.md`](../../data-engineering/kafka/detailed.md)

## Quick start

```bash
cd MD/mini-projects/kafka-log-lab
pip install -e ".[dev]"
pytest -q
python scripts/demo_consume.py
```

## Layout

```
src/kafka_log_lab/log.py   # PartitionedLog, ConsumerGroup, consume_idempotent
scripts/demo_consume.py
tests/test_log.py
```
