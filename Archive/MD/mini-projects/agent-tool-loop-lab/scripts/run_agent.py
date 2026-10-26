#!/usr/bin/env python3
from rich.console import Console

from agent_tool_loop_lab.loop import run_agent
from agent_tool_loop_lab.tools import Tool, ToolRegistry

console = Console()

registry = ToolRegistry()
registry.register(Tool("get_weather", "City weather", lambda city: f"Sunny in {city}"))
registry.register(
    Tool("search_docs", "Internal KB", lambda q: "refund within 30 days with receipt")
)

run = run_agent("What is our refund policy?", registry)
for i, s in enumerate(run.steps):
    console.print(f"[bold]Step {i+1}[/bold] {s.thought} → {s.tool_name} → {s.observation}")
console.print(f"\n[green]Answer:[/green] {run.final_answer}")
