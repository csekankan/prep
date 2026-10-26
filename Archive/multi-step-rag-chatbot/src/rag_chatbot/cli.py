"""
Interactive terminal chat — best way to learn the multi-step flow.

Use /debug to print routing + retrieval metadata after each turn.
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from rag_chatbot.graph.builder import build_graph
from rag_chatbot.ingestion.pipeline import ingest
from rag_chatbot.logging_setup import configure_logging


def main() -> None:
    configure_logging()
    console = Console()
    console.print(
        Panel.fit(
            "[bold]Multi-Step RAG Chatbot[/bold]\n"
            "Commands: [cyan]/ingest[/cyan] re-index docs, [cyan]/debug[/cyan] toggle metadata, [cyan]/quit[/cyan]",
            border_style="green",
        )
    )

    # Ensure index exists on first run
    try:
        ingest()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]Ingest skipped or failed: {exc}[/yellow]")

    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    debug = False

    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/quit", "quit", "exit"}:
            break
        if user_input.lower() == "/ingest":
            n = ingest(reset=True)
            console.print(f"[green]Re-indexed {n} chunks.[/green]")
            continue
        if user_input.lower() == "/debug":
            debug = not debug
            console.print(f"[cyan]Debug mode: {debug}[/cyan]")
            continue

        result: dict[str, Any] = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        messages = result.get("messages") or []
        reply = messages[-1].content if messages else ""

        if debug:
            analysis = result.get("analysis")
            console.print(Panel(str(analysis), title="Route analysis", border_style="magenta"))
            console.print(Panel(result.get("thinking_notes") or "", title="Thinking notes"))
            console.print("Citations:", result.get("citations"))

        console.print(Panel(Markdown(reply if isinstance(reply, str) else str(reply)), title="Assistant"))


if __name__ == "__main__":
    main()
