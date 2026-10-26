# ETL pipeline lab

**Bronze / silver / gold** flow with **Pydantic validation**, **incremental watermark**, and **merge-by-key** into silver—patterns behind production lakehouse ELT.

## Curriculum

[`../../data-engineering/etl-elt/detailed.md`](../../data-engineering/etl-elt/detailed.md)

## Quick start

```bash
cd MD/mini-projects/etl-pipeline-lab
pip install -e ".[dev]"
pytest -q
python scripts/demo_run.py
```
