# Agent tool loop lab

Maps to [`ai-engineering-deep-dive/09-mcp-and-agents/02-the-agent-loop.md`](../../ai-engineering-deep-dive/09-mcp-and-agents/02-the-agent-loop.md).

Deterministic "LLM" stub + tool registry + max-step guard (production safety).

```bash
pip install -e ".[dev]"
python scripts/run_agent.py
pytest -q
```
