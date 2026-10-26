"""
LangGraph state schema.

State is the *shared memory* of the graph. Each node reads fields it needs and
returns a *partial update* dict. LangGraph merges updates into state.

`messages` uses `add_messages` reducer — new messages append instead of replace.
That's how multi-turn chat works with checkpoints (thread_id).
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from rag_chatbot.graph.schemas import QueryAnalysis
from rag_chatbot.retrieval.retriever import ScoredChunk


class GraphState(TypedDict):
    # Conversation history (HumanMessage, AIMessage, etc.)
    messages: Annotated[list[BaseMessage], add_messages]

    # --- Multi-step RAG artifacts (visible in API/CLI for learning) ---
    analysis: QueryAnalysis | None
    retrieved_chunks: list[ScoredChunk]
    thinking_notes: str
    citations: list[str]
