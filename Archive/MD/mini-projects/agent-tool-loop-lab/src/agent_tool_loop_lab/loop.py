"""
Agent loop: user goal → (plan) → tool call → observation → repeat.

Real systems call an LLM; we use a tiny rule-based planner so tests are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_tool_loop_lab.tools import ToolRegistry


@dataclass
class AgentStep:
    thought: str
    tool_name: str | None = None
    tool_args: dict | None = None
    observation: str | None = None


@dataclass
class AgentRun:
    steps: list[AgentStep] = field(default_factory=list)
    final_answer: str | None = None


def run_agent(user_query: str, registry: ToolRegistry, max_steps: int = 5) -> AgentRun:
    run = AgentRun()
    context = user_query

    for _ in range(max_steps):
        # Stub "model" chooses tool from keywords
        if "weather" in context.lower():
            step = AgentStep(thought="Need live weather", tool_name="get_weather", tool_args={"city": "Paris"})
        elif "policy" in context.lower():
            step = AgentStep(thought="Lookup policy doc", tool_name="search_docs", tool_args={"q": "refund"})
        else:
            run.final_answer = context
            break

        tool = registry.get(step.tool_name)
        step.observation = str(tool.run(**step.tool_args))
        run.steps.append(step)
        context = f"{context}\nObservation: {step.observation}"

        if "refund within 30 days" in step.observation:
            run.final_answer = step.observation
            break

    return run
