"""
FastAPI HTTP API — how you'd expose the graph to a web UI or Slack bot.

Production extras you'd add next:
  - Auth (JWT / API keys)
  - Rate limiting
  - Request ID middleware → structured logs
  - Streaming SSE for token-by-token answers
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from rag_chatbot.graph.builder import build_graph
from rag_chatbot.logging_setup import configure_logging

configure_logging()

app = FastAPI(
    title="Multi-Step RAG Chatbot",
    description="Demo API: LangGraph router + retrieval + think + answer",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    thread_id: str = Field(default="default", description="Conversation id for checkpoint memory")


class ChatResponse(BaseModel):
    reply: str
    route: str | None = None
    thinking_notes: str | None = None
    citations: list[str] = Field(default_factory=list)


@lru_cache
def get_graph():
    return build_graph()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    graph = get_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        result: dict[str, Any] = graph.invoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages = result.get("messages") or []
    last = messages[-1] if messages else None
    reply = getattr(last, "content", "") if last else ""

    analysis = result.get("analysis")
    route = analysis.route if analysis else None

    return ChatResponse(
        reply=reply if isinstance(reply, str) else str(reply),
        route=route,
        thinking_notes=result.get("thinking_notes"),
        citations=result.get("citations") or [],
    )
