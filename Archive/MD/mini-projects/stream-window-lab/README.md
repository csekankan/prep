# Stream window lab

Companion to [`data-engineering/flink/detailed.md`](../../data-engineering/flink/detailed.md).

Teaches **event time**, **watermarks**, **tumbling windows**, and **allowed lateness** without a JVM.

```bash
cd MD/mini-projects/stream-window-lab
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 scripts/demo_windows.py
```
