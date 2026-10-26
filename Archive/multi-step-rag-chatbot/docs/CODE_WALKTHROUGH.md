# Code Walkthrough (one question, end to end)

**User asks:** "Can support refund $150 without manager approval?"

## 1. CLI or API receives text

- CLI: `graph.invoke({"messages": [HumanMessage(...)]}, config={"configurable": {"thread_id": "..."}})`
- `thread_id` ties into **MemorySaver** so follow-up questions see prior messages.

## 2. Node `analyze`

File: `graph/nodes.py` → `make_analyze_node`

- LLM with **structured output** → `QueryAnalysis` (`graph/schemas.py`).
- Expected: `route="rag"`, `sub_questions=["refund policy under 200", ...]`.
- If API key missing, **heuristic** keyword router still sends policy questions to RAG.

## 3. Conditional edge

File: `graph/builder.py` → `route_after_analyze`

- Returns `"retrieve"` when `route == "rag"`.

## 4. Node `retrieve`

File: `retrieval/retriever.py`

- Embeds each sub-question (same model as ingest).
- Chroma **similarity search** → chunks from `01-company-policies.md`.
- Drops chunks below `retrieval_min_score` (config).

## 5. Node `think`

- LLM reads excerpts only; writes bullet **analyst notes** (stored in `thinking_notes`).
- Separating think vs answer reduces mixing user tone with internal reasoning.

## 6. Node `answer`

- LLM gets: user question + analyst notes + raw excerpts.
- System prompt requires **Sources:** line → ties to RAG grounding discipline.

## 7. State returned

- `messages` ends with `AIMessage` (what user sees).
- `/debug` in CLI also shows `analysis`, `thinking_notes`, `citations`.

## Where each concept lives

| Concept | Where in code |
|---------|----------------|
| Chunking | `ingestion/chunker.py` |
| Embeddings | `llm_factory.py` → `build_embeddings` |
| Vector DB | `ingestion/vector_store.py` |
| LangGraph state | `graph/state.py` |
| Multi-step edges | `graph/builder.py` |
| Prompts as config | `graph/prompts.py` |
| Settings / env | `config.py` |
