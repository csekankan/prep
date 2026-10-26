from agent_tool_loop_lab.loop import run_agent
from agent_tool_loop_lab.tools import Tool, ToolRegistry


def test_policy_query_uses_search() -> None:
    reg = ToolRegistry()
    reg.register(Tool("search_docs", "kb", lambda q: "refund within 30 days"))
    run = run_agent("refund policy", reg)
    assert run.steps[0].tool_name == "search_docs"
    assert "30 days" in (run.final_answer or "")
