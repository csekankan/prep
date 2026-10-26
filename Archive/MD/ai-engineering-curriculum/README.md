# AI / Agent Engineering Curriculum (Study Notes)

> **Audience:** **Senior software engineers** becoming **AI / agent engineers** — you already ship services, tests, and on-call; these notes teach LLM **systems** (agents, RAG, guardrails, gateways, eval, memory, red team, cloud capstones).  
> **Style:** Each module starts with **plain-language concepts**, then **code**, **math where it matters**, **industry patterns**, and **senior pitfalls**.  
> **Course map:** ~32 sections • 279 lectures • ~83h (LangChain, LangGraph, guardrails, gateways, eval, memory, PyRIT, Redis, GCP/AWS/HR/Databricks projects).

**Related docs in this repo:** `MD/llm-ops/` · `MD/interview-questions/ai-ml-and-llm.md` · `MD/interview-questions/rag-and-vector-search.md` · `MD/FAANG_INSIDER_KNOWLEDGE.md`

---

## If you are new to LLMs (15-minute primer)

| Term | What it is | SWE parallel |
|------|-----------|-------------|
| **Token** | Smallest unit the model reads/writes (~¾ of a word). "Hello world" ≈ 2 tokens. **You pay per token** — both input and output. | Like characters in a byte stream, but coarser |
| **Context window** | Max tokens the model can handle in one call (prompt + response). GPT-4o: 128k tokens. Exceed it → request fails. | Like a max request body size |
| **Prompt** | The full text you send: system instructions + user message + any retrieved context. | Like the HTTP request body |
| **Embedding** | An array of floats (e.g. 1536 numbers) representing text "meaning." Similar text → similar vectors. Used to find relevant documents. | Like a semantic hash — similar inputs → similar outputs |
| **Vector database** | Database optimized for storing embeddings and finding similar ones fast. Examples: Pinecone, Weaviate, pgvector. | Like a specialized index (think GIN for full-text search, but for meaning) |
| **RAG** | **Retrieval-Augmented Generation:** retrieve relevant docs from a vector DB → paste into prompt → model answers from your docs. This is how you give an LLM access to your company data without retraining. | Like a search-backed template-render pipeline |
| **Agent** | Loop: model reasons → decides to call a **tool** (API, DB, search) → reads result → decides next step. Runs until done. | Like a state machine where the LLM picks transitions |
| **Guardrail** | Code that checks input/output around the LLM — blocks PII, prompt injection, toxic content, invalid JSON. Think: middleware for LLMs. | Like request/response validation middleware |
| **PII** | **Personally Identifiable Information** — names, emails, SSNs, credit cards. Must be redacted before logging. | You already handle this in databases — same rules apply to prompts and traces |
| **Prompt injection** | Attacker puts "ignore all instructions" in user text or a RAG document to hijack the model. | Like SQL injection — untrusted input overrides instructions |
| **Grounding** | Checking that the model's answer is supported by the source documents. Ungrounded = hallucination = model made it up. | Like asserting a report cites its sources |
| **Schema validation** | Ensuring model's JSON output has the right fields and types. | Same as REST API response validation — Pydantic, JSON Schema |
| **Eval** | Automated quality tests on a dataset — faithfulness, relevance, toxicity scores. Not optional in prod. | Like integration tests + quality metrics |
| **Fine-tuning** | Training the model further on your data to change behavior (style, format). Does NOT teach facts — use RAG for that. | Like customizing a framework's defaults |
| **LoRA** | Lightweight fine-tuning — trains small adapter matrices instead of all weights. Multiple LoRAs can share one base model. | Like a plugin that modifies behavior without forking |
| **TTFT** | **Time to First Token** — how long until the first token streams. The main UX metric. | Like Time to First Byte (TTFB) |

You do **not** need to train models from scratch for this course — you **orchestrate** and **harden** them like any external API. The `llm-ops-fundamentals.md` glossary has even more terms with deeper explanations.

---

## Prerequisites (read first if new to LLMs)

| # | File | What you will know after |
|---|------|--------------------------|
| A1 | [A1-embeddings-vector-databases-rag-foundations.md](./A1-embeddings-vector-databases-rag-foundations.md) | Embeddings, vector DBs, chunking, basic RAG pipeline |
| A2 | [A2-prompt-engineering-patterns.md](./A2-prompt-engineering-patterns.md) | System prompts, few-shot, CoT, ReAct, prompt versioning |

Skip A1/A2 if you have already built a RAG pipeline and versioned prompts in production.

---

## Module index (read in order first time)

| # | File | What you will be able to do after |
|---|------|-----------------------------------|
| 00 | [00-introduction-security-agentic-architecture.md](./00-introduction-security-agentic-architecture.md) | Draw agentic architecture; threat-model GenAI |
| 01 | [01-langchain-fundamentals.md](./01-langchain-fundamentals.md) | Messages, tools, streaming, basic agent invoke |
| 02 | [02-structured-output-and-middleware.md](./02-structured-output-and-middleware.md) | Pydantic outputs; summarization/HITL middleware |
| 03 | [03-langgraph-agents-memory-mcp.md](./03-langgraph-agents-memory-mcp.md) | Build graphs, checkpoints, multi-agent, MCP |
| 04 | [04-observability-langsmith-logfire.md](./04-observability-langsmith-logfire.md) | Trace RAG/agents; debug production issues |
| 05 | [05-guardrails-nemo-and-guardrails-ai.md](./05-guardrails-nemo-and-guardrails-ai.md) | NeMo rails + Guardrails AI validators |
| 06 | [06-aws-bedrock-guardrails.md](./06-aws-bedrock-guardrails.md) | Bedrock guardrails, grounding, PII filters |
| 07 | [07-llm-gateways.md](./07-llm-gateways.md) | Route, fallback, cache via gateways |
| 08 | [08-evaluation-ragas-deepeval.md](./08-evaluation-ragas-deepeval.md) | RAGAS + DeepEval CI gates |
| 09 | [09-agent-memory.md](./09-agent-memory.md) | Memory types; Mem0/LangMem patterns |
| 10 | [10-red-teaming-pyrit.md](./10-red-teaming-pyrit.md) | PyRIT attacks; secure agents/RAG |
| 11 | [11-redis-for-ai.md](./11-redis-for-ai.md) | Exact/semantic cache; rate limits |
| 12 | [12-capstone-projects-architecture.md](./12-capstone-projects-architecture.md) | GCP / AWS / HR project architectures |
| 13 | [13-claude-deep-agents-governance.md](./13-claude-deep-agents-governance.md) | Deep agents; Sentience Governor |
| 14 | [14-databricks-agentic-rag.md](./14-databricks-agentic-rag.md) | Lakehouse agentic RAG + Unity Catalog |

---

## Quality bar (what “good depth” means here)

Every module includes these sections (in order):

1. **Learning objectives** — 2-3 sentences: what you can do after this module.
2. **Concepts + code** — beginner-readable definitions, then runnable Python patterns.
3. **Math / trade-offs** — tokens, latency, thresholds, cost formulas where decisions matter.
4. **Industry patterns** — how real teams (FAANG-scale) structure the same problem.
5. **Production notes** — deployment, config, monitoring, error handling, incident patterns.
6. **Senior pitfalls** — table of mistakes and fixes from real production experience.
7. **Practice** — quick hands-on exercises.
8. **Production-grade practice** — exercises simulating real work (build, deploy, debug, measure).
9. **Lecture map** — tie back to course videos for revision.

All modules A1–A2 and 00–14 follow this template. Capstones 12–14 add architecture diagrams, deploy checklists, cost models, and runbook templates.

---

## Environment setup

```bash
# Python 3.11+ recommended
curl -LsSf https://astral.sh/uv/install.sh | sh
cd your-project
uv venv .venv && source .venv/bin/activate
uv pip install langchain langchain-openai langgraph pydantic python-dotenv
# Add per module: ragas deepeval guardrails-ai redis logfire ...
```

`.env` (never commit):

```bash
OPENAI_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...   # LangSmith
```

---

## 9-week study plan (~10h/week)

| Week | Modules | Deliverable |
|------|---------|-------------|
| 0 | A1–A2 | Embed 3 sentences; build mini RAG; version a prompt in YAML |
| 1 | 00–01 | Hello agent + traced invoke |
| 2 | 02–03 | LangGraph with tools + checkpoint |
| 3 | 04–05 | Traces + input/output guardrail |
| 4 | 06–07 | Bedrock or gateway experiment |
| 5 | 08 | Eval dataset + pytest gate |
| 6 | 09–11 | Memory + Redis cache demo |
| 7 | 12 | One capstone architecture doc + deploy checklist |
| 8 | 13–14 | Governance notes + Databricks skim |

**Week 0 is optional** — skip if you have already built a RAG pipeline and versioned prompts.

---

## Full course section → module map

| Course block | Modules |
|--------------|---------|
| Prerequisite: embeddings, vector DBs, RAG | A1 |
| Prerequisite: prompt engineering patterns | A2 |
| Intro, security, agentic architecture | 00 |
| LangChain (UV, agents, models, stream, tools, messages) | 01 |
| Structured output, middleware, guardrails intro | 02 |
| LangGraph, Studio, multi-agent, MCP, LangSmith debug | 03, 04 |
| Logfire tracing | 04 |
| NeMo Guardrails, Guardrails AI, HR bot | 05 |
| AWS Bedrock Guardrails M1–M5 | 06 |
| Portkey, TensorZero, Bifrost, MeshAPI | 07 |
| RAGAS, DeepEval, agent evals | 08 |
| Memory (LangChain, Mem0, LangMem) | 09 |
| PyRIT red teaming | 10 |
| Redis for AI | 11 |
| GCP agentic RAG, AWS Terraform project, HR phases | 12 |
| Claude / deep agents / governance | 13 |
| Databricks agentic RAG | 14 |
