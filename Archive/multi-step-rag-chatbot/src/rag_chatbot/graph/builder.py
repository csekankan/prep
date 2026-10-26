"""
Compile the LangGraph workflow.

MULTI-STEP FLOW (study this diagram):

    START → analyze →┬→ retrieve → think → answer → END
                     ├→ chat ─────────────────────────→ END
                     └→ clarify ──────────────────────→ END

Checkpointer (MemorySaver) stores state per thread_id — that's conversation memory.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from rag_chatbot.graph.nodes import (
    make_analyze_node,
    make_answer_node,
    make_chat_node,
    make_clarify_node,
    make_retrieve_node,
    make_think_node,
    route_after_analyze,
)
from rag_chatbot.graph.state import GraphState
from rag_chatbot.ingestion.vector_store import get_vector_store
from rag_chatbot.llm_factory import build_chat_model, build_embeddings
from rag_chatbot.retrieval.retriever import DocumentRetriever


def build_graph():
    """Return a compiled graph + checkpointer for multi-turn threads."""
    llm = build_chat_model()
    embeddings = build_embeddings()
    store = get_vector_store(embeddings)
    retriever = DocumentRetriever(store)

    builder = StateGraph(GraphState)

    builder.add_node("analyze", make_analyze_node(llm))
    builder.add_node("retrieve", make_retrieve_node(retriever))
    builder.add_node("think", make_think_node(llm))
    builder.add_node("answer", make_answer_node(llm))
    builder.add_node("chat", make_chat_node(llm))
    builder.add_node("clarify", make_clarify_node(llm))

    builder.add_edge(START, "analyze")
    builder.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {
            "retrieve": "retrieve",
            "chat": "chat",
            "clarify": "clarify",
        },
    )
    builder.add_edge("retrieve", "think")
    builder.add_edge("think", "answer")
    builder.add_edge("answer", END)
    builder.add_edge("chat", END)
    builder.add_edge("clarify", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
