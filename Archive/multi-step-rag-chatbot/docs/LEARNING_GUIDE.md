# Learning Guide — Multi-Step RAG Chatbot

This project mirrors patterns from your **AI engineering curriculum** docs: messages API, RAG, LangGraph routing, checkpoints, and production hygiene (config, logging, API boundary).

## What to read first

| Order | File | Concept |
|-------|------|---------|
| 1 | `sample_docs/*.md` | Ground truth the bot retrieves |
| 2 | `src/rag_chatbot/ingestion/pipeline.py` | Ingest = chunk + embed + store |
| 3 | `src/rag_chatbot/graph/builder.py` | Multi-step graph wiring |
| 4 | `src/rag_chatbot/graph/nodes.py` | Each step's behavior |
| 5 | `src/rag_chatbot/api/main.py` | HTTP wrapper |

## Multi-step vs "one-shot RAG"

**Naive RAG:** user question → retrieve → stuff context → one LLM call.

**This demo (agentic / multi-step RAG):**

1. **Analyze** — Should we retrieve? Decompose into sub-questions?
2. **Retrieve** — Vector search (only if needed).
3. **Think** — Internal notes from chunks (improves grounding).
4. **Answer** — User-facing reply with sources.

Skipping retrieve on "hello" saves latency and reduces **hallucination surface** (no random docs in context).

## Key terms

- **Embedding:** Text → vector; similar meaning → close vectors.
- **Chunk:** Small piece of a doc; retrieval unit.
- **Chroma:** Local vector DB (persisted under `data/chroma`).
- **LangGraph state:** Shared dict passed between nodes; `messages` append via `add_messages`.
- **Checkpoint / thread_id:** Multi-turn memory key.

## Experiments to try

1. Ask: *"What's the PTO policy?"* — watch `/debug` for `route=rag` and citations.
2. Ask: *"Hi"* — should `route=chat` with no retrieval.
3. Edit `sample_docs/01-company-policies.md`, run `/ingest`, ask again.
4. Set `LOG_LEVEL=DEBUG` and see similarity filtering in logs.
5. Add a 4th markdown file and re-ingest — no code changes required.

## Production upgrades (not implemented here)

- **Eval:** RAGAS / DeepEval in CI on fixed question sets.
- **Guardrails:** Block PII in outputs; validate tool calls.
- **Streaming:** `graph.stream()` → SSE to UI.
- **Hosted vector DB + auth** on `/chat`.
- **Hybrid search:** BM25 + vectors for keyword-heavy queries (SKU IDs, error codes).

## Relation to your notes folder

Concepts align with:

- `MD/ai-engineering-curriculum/A1-embeddings-vector-databases-rag-foundations.md`
- `MD/ai-engineering-curriculum/01-langchain-fundamentals.md`
- `MD/ai-engineering-curriculum/03-langgraph-agents-memory-mcp.md`
