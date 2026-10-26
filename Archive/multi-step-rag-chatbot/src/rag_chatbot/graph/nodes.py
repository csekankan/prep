"""
Graph nodes — each function is one step in the multi-step chatbot.

Think of nodes as microservices in a workflow:
  analyze → (branch) → retrieve → think → answer
"""

from __future__ import annotations

import json
import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from rag_chatbot.graph.prompts import (
    ANSWER_SYSTEM,
    CHAT_SYSTEM,
    CLARIFY_SYSTEM,
    ROUTER_SYSTEM,
    THINK_SYSTEM,
)
from rag_chatbot.graph.schemas import QueryAnalysis
from rag_chatbot.graph.state import GraphState
from rag_chatbot.retrieval.retriever import DocumentRetriever, ScoredChunk

logger = logging.getLogger(__name__)


def _last_user_text(state: GraphState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _heuristic_analysis(user_text: str) -> QueryAnalysis:
    """
    Fallback router when LLM is mock or structured output fails.

    Production still benefits from a cheap heuristic guardrail before LLM routing.
    """
    text = user_text.lower().strip()
    if not text:
        return QueryAnalysis(route="clarify", needs_clarification=True, reasoning="empty input")
    if text in {"hi", "hello", "hey", "thanks", "thank you"}:
        return QueryAnalysis(route="chat", reasoning="greeting")
    if any(k in text for k in ("policy", "refund", "pto", "sla", "partition", "on-call", "incident", "pricing")):
        return QueryAnalysis(
            route="rag",
            sub_questions=[user_text],
            reasoning="keyword match",
        )
    if "?" in text and len(text.split()) >= 3:
        return QueryAnalysis(route="rag", sub_questions=[user_text], reasoning="question mark")
    return QueryAnalysis(route="chat", reasoning="default smalltalk")


def make_analyze_node(llm: BaseChatModel):
    """Node 1: classify intent and optionally decompose the question."""

    structured = llm.with_structured_output(QueryAnalysis)

    def analyze(state: GraphState) -> dict:
        user_text = _last_user_text(state)
        logger.debug("Analyzing user text: %s", user_text[:200])

        try:
            analysis: QueryAnalysis = structured.invoke(
                [
                    SystemMessage(content=ROUTER_SYSTEM),
                    HumanMessage(content=user_text),
                ]
            )
        except Exception as exc:  # noqa: BLE001 — demo resilience
            logger.warning("Structured routing failed (%s); using heuristic", exc)
            analysis = _heuristic_analysis(user_text)

        # FakeListChatModel returns JSON string in content — parse if needed
        if isinstance(analysis, str):
            try:
                analysis = QueryAnalysis.model_validate(json.loads(analysis))
            except Exception:
                analysis = _heuristic_analysis(user_text)

        return {"analysis": analysis, "thinking_notes": analysis.reasoning}

    return analyze


def make_retrieve_node(retriever: DocumentRetriever):
    """Node 2: embedding search for each sub-question, dedupe chunks."""

    def retrieve(state: GraphState) -> dict:
        analysis = state.get("analysis")
        if not analysis or analysis.route != "rag":
            return {"retrieved_chunks": []}

        queries = analysis.sub_questions or [_last_user_text(state)]
        seen: set[str] = set()
        merged: list[ScoredChunk] = []

        for q in queries:
            for chunk in retriever.retrieve(q):
                key = chunk.document.page_content[:120]
                if key in seen:
                    continue
                seen.add(key)
                merged.append(chunk)

        citations = [
            f"{c.document.metadata.get('source', 'unknown')} (score={c.score:.2f})"
            for c in merged
        ]
        return {"retrieved_chunks": merged, "citations": citations}

    return retrieve


def make_think_node(llm: BaseChatModel):
    """
    Node 3: 'thinking' step — internal synthesis before the user-facing answer.

    This is NOT chain-of-thought you must show users; it's an intermediate
    representation that improves grounded answers (agentic RAG pattern).
    """

    def think(state: GraphState) -> dict:
        chunks = state.get("retrieved_chunks") or []
        if not chunks:
            return {"thinking_notes": "No chunks retrieved; answer should admit uncertainty."}

        context = "\n\n---\n\n".join(
            f"[{c.document.metadata.get('source')}]\n{c.document.page_content}" for c in chunks
        )
        user_text = _last_user_text(state)

        response = llm.invoke(
            [
                SystemMessage(content=THINK_SYSTEM),
                HumanMessage(content=f"Question: {user_text}\n\nExcerpts:\n{context}"),
            ]
        )
        notes = response.content if isinstance(response.content, str) else str(response.content)
        return {"thinking_notes": notes}

    return think


def make_answer_node(llm: BaseChatModel):
    """Node 4: final grounded answer with sources."""

    def answer(state: GraphState) -> dict:
        chunks = state.get("retrieved_chunks") or []
        context = "\n\n---\n\n".join(
            f"[{c.document.metadata.get('source')}]\n{c.document.page_content}" for c in chunks
        )
        user_text = _last_user_text(state)
        notes = state.get("thinking_notes") or ""

        response = llm.invoke(
            [
                SystemMessage(content=ANSWER_SYSTEM),
                HumanMessage(
                    content=(
                        f"User question: {user_text}\n\n"
                        f"Analyst notes:\n{notes}\n\n"
                        f"Context excerpts:\n{context}"
                    )
                ),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)

        # Mock LLM path: build a helpful template from real retrieval
        if text.startswith("MOCK_ANSWER"):
            text = _mock_grounded_answer(user_text, chunks, notes)

        return {"messages": [AIMessage(content=text)]}

    return answer


def _mock_grounded_answer(user_text: str, chunks: list[ScoredChunk], notes: str) -> str:
    sources = ", ".join({c.document.metadata.get("source", "?") for c in chunks}) or "none"
    snippet = chunks[0].document.page_content[:400] if chunks else "(no matching docs — run rag-ingest)"
    return (
        f"**[Demo mode — set OPENAI_API_KEY for full LLM answers]**\n\n"
        f"Question: {user_text}\n\n"
        f"From your indexed docs:\n\n{snippet}\n\n"
        f"Analyst notes: {notes[:300]}\n\n"
        f"Sources: {sources}"
    )


def make_chat_node(llm: BaseChatModel):
    """Direct reply without retrieval."""

    def chat(state: GraphState) -> dict:
        response = llm.invoke(
            [SystemMessage(content=CHAT_SYSTEM), *state["messages"][-3:]],
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        if "MOCK" in text or text.strip().startswith("{"):  # noqa: SIM114
            text = "Hello! Ask me about Acme Cloud policies, product limits, or on-call runbooks."
        return {"messages": [AIMessage(content=text)]}

    return chat


def make_clarify_node(llm: BaseChatModel):
    def clarify(state: GraphState) -> dict:
        response = llm.invoke(
            [SystemMessage(content=CLARIFY_SYSTEM), *state["messages"][-3:]],
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        if "MOCK" in text or text.strip().startswith("{"):
            text = "Could you share more detail — for example amount, timeframe, or which product tier?"
        return {"messages": [AIMessage(content=text)]}

    return clarify


def route_after_analyze(state: GraphState) -> str:
    """Conditional edge: LangGraph calls this to pick the next node name."""
    analysis = state.get("analysis")
    if not analysis:
        return "chat"
    if analysis.route == "clarify" or analysis.needs_clarification:
        return "clarify"
    if analysis.route == "rag":
        return "retrieve"
    return "chat"
