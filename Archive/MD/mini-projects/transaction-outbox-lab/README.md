# Transaction outbox lab

Maps to `MD/event-driven-architecture/` and fanout async streams — **same DB transaction** writes business row + outbox row; relay publishes to message bus.

```bash
pip install -e ".[dev]"
pytest -q
```
