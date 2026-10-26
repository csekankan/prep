# Airflow DAG lab

Companion to [`data-engineering/airflow/detailed.md`](../../data-engineering/airflow/detailed.md).

Pure-Python **scheduler**: topological run order, retries, DagRun logical dates, optional backfill.

```bash
cd MD/mini-projects/airflow-dag-lab
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 scripts/demo_backfill.py
```
