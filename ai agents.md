# AI Agent Development — Complete Tutorial Reference

> A single-document reference covering all three projects: **MCP Customer Support Agent**, **Agentic RAG Knowledge Base**, and **Hallucination & Reliability Patterns**.

---

## Table of Contents

1. [Project Overview & How They Connect](#1-project-overview)
2. [Project 1: MCP Customer Support Agent](#2-project-1-mcp-customer-support-agent)
3. [Project 2: Agentic RAG Knowledge Base](#3-project-2-agentic-rag-knowledge-base)
4. [Project 3: Hallucination & Reliability](#4-project-3-hallucination--reliability)
5. [Shared Concepts Across All Projects](#5-shared-concepts)
6. [Technology Stack Reference](#6-technology-stack-reference)
7. [Architecture Comparison](#7-architecture-comparison)
8. [Setup & Running](#8-setup--running)

---

## 1. Project Overview

```
PROJECT 1                    PROJECT 2                    PROJECT 3
MCP Agent                    Agentic RAG                  Hallucination Guard
─────────                    ───────────                  ──────────────────

"Build a tool-using          "Build a self-correcting     "Make sure the LLM
 AI agent that talks          knowledge base Q&A           doesn't lie, leak
 to a database via MCP"       with document retrieval"     data, or go rogue"

┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│ LangGraph Agent │          │ LangGraph Agent │          │ Standalone       │
│ + MCP Server    │          │ + ChromaDB      │          │ Patterns         │
│ + SQLite DB     │          │ + Embeddings    │          │ (5 techniques)   │
│ + Tool Calling  │          │ + Self-Correct  │          │                  │
└─────────────────┘          └─────────────────┘          └─────────────────┘

LEARNS:                      LEARNS:                      LEARNS:
• MCP protocol               • RAG pipeline               • Structured output
• Tool design                 • Vector stores              • Fact checking
• Agent graphs                • Document grading           • Guardrails
• Persistent memory           • Query rewriting            • Confidence scoring
                              • Hallucination detection    • PII redaction
```

**The learning path:** Project 1 teaches you agent architecture → Project 2 adds retrieval and self-correction → Project 3 adds safety and reliability layers. Together they form a production-ready AI application stack.

---

## 2. Project 1: MCP Customer Support Agent

### What It Does

A fully working customer support agent for a tech accessories store. It can search products, track orders, create/query support tickets, and hold multi-turn conversations with persistent memory.

### Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER (terminal)                             │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     LANGGRAPH AGENT (agent/)                        │
│                                                                      │
│   ┌────────────────┐    ┌─────────────────┐    ┌────────────────┐   │
│   │  call_model     │───►│ route_after_    │───►│   ToolNode     │   │
│   │  (invoke LLM    │    │ model           │    │   (execute     │   │
│   │   with system    │    │ "tools" or      │    │    MCP tool,   │   │
│   │   prompt +       │    │ "end"?          │    │    return      │   │
│   │   message        │◄───┤                 │    │    result)     │   │
│   │   history)       │    └─────────────────┘    └───────┬────────┘   │
│   └────────────────┘                                     │           │
│         ▲                                                │           │
│         └────────────────────────────────────────────────┘           │
│                        loop until no more tool calls                 │
│                                                                      │
│   State: messages[] + turn_count + last_tool + customer_name         │
│   Memory: SqliteSaver → agent_memory.db (persists across restarts)   │
└────────────────────────────────────┬─────────────────────────────────┘
                                     │ MCP (stdio, JSON-RPC 2.0)
                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    MCP SERVER (mcp_server/)                          │
│                                                                      │
│   TOOLS (callable, may have side effects):                           │
│   ┌────────────────────┐ ┌────────────────────┐ ┌────────────────┐  │
│   │ search_products    │ │ get_order_status   │ │ create_ticket  │  │
│   │ get_product_detail │ │ list_customer_     │ │ get_ticket     │  │
│   │                    │ │ orders             │ │ list_open_     │  │
│   │                    │ │                    │ │ tickets        │  │
│   └────────────────────┘ └────────────────────┘ └────────────────┘  │
│                                                                      │
│   RESOURCES (read-only, fetched by URI):                             │
│   ┌────────────────────┐ ┌────────────────────┐                      │
│   │ products://catalog │ │ tickets://open     │                      │
│   └────────────────────┘ └────────────────────┘                      │
│                                                                      │
│   PROMPTS (reusable templates):                                      │
│   ┌────────────────────────────────────┐                             │
│   │ escalation_template(name, issue)   │                             │
│   └────────────────────────────────────┘                             │
└────────────────────────────────────┬─────────────────────────────────┘
                                     │ SQLite
                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   SQLite DB (data/support.db)                        │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                        │
│   │ products │   │ orders   │   │ tickets  │                        │
│   │ (10 rows)│   │ (20 rows)│   │ (5 rows) │                        │
│   └──────────┘   └──────────┘   └──────────┘                        │
└──────────────────────────────────────────────────────────────────────┘
```

### File-by-File Breakdown

| File | Purpose | Key Concepts |
|------|---------|-------------|
| `main.py` | Entry point — loads env, validates DB, starts agent | `.env` loading, startup checks |
| `agent/state.py` | `AgentState` TypedDict | `Annotated[list, operator.add]` for append-only messages |
| `agent/nodes.py` | `call_model` + `route_after_model` | System prompt injection, ReAct routing logic |
| `agent/graph.py` | Build LangGraph, connect MCP, compile | `StateGraph`, `ToolNode`, `SqliteSaver`, `MultiServerMCPClient` |
| `mcp_server/server.py` | FastMCP server — registers tools/resources/prompts | `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()` |
| `mcp_server/database.py` | SQLite connection helper | WAL mode, `row_factory`, connection sharing |
| `mcp_server/tools/product_tools.py` | `search_products`, `get_product_detail` | Dynamic SQL, parameterised queries, error-as-return |
| `mcp_server/tools/order_tools.py` | `get_order_status`, `list_customer_orders` | JOIN queries, input normalisation |
| `mcp_server/tools/ticket_tools.py` | `create_support_ticket`, `get_ticket`, `list_open_tickets` | Side effects, ID generation, priority validation |
| `data/seed_db.py` | Creates and populates the demo database | Schema design, idempotent seeding |

### Key Concepts Taught

#### MCP (Model Context Protocol)

```
MCP defines THREE primitives:

  @mcp.tool()       → Callable functions (search, create, update)
                      The LLM sees the function name + docstring + parameter types
                      and decides when/how to call them.

  @mcp.resource()   → Read-only data by URI (products://catalog)
                      No side effects. Like a GET endpoint.

  @mcp.prompt()     → Reusable templates (escalation_template)
                      Slash commands in UIs like Claude Desktop.

Transport: stdio (subprocess, stdin/stdout JSON-RPC)
           or SSE (HTTP streaming for persistent servers)
```

#### LangGraph ReAct Loop

```
The agent follows the ReAct (Reason + Act) pattern:

  1. call_model → LLM sees messages + tools → decides: respond or use tool?
  2. route_after_model → checks last message for tool_calls
     ├── has tool_calls → go to ToolNode
     └── no tool_calls  → go to END (return response to user)
  3. ToolNode → executes the tool, appends result as ToolMessage
  4. Back to call_model → LLM sees tool result, decides next step
  
  This loop continues until the LLM generates a plain text response.
```

#### Persistent Memory

```
SqliteSaver checkpointer:
  - After EVERY node, the full state is serialised to SQLite
  - Each conversation has a thread_id
  - On next invoke with same thread_id → state is restored
  - Result: stop and restart the app → conversation history intact
```

#### MCP Tool Design Rules

```
1. Docstring IS the LLM's instruction manual (write it for the model, not humans)
2. Use type hints → FastMCP generates JSON schema → LLM sees parameter types
3. Return dicts/strings, never raw DB rows
4. Catch exceptions, return error strings (never raise inside a tool)
5. One tool = one concern (search vs. detail — two separate tools)
```

---

## 3. Project 2: Agentic RAG Knowledge Base

### What It Does

A company knowledge base Q&A system where employees ask questions about HR policies, remote work, product roadmap, and onboarding. The agent retrieves relevant document chunks, grades their relevance, generates grounded answers, checks for hallucinations, and retries if needed.

### Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                                │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     LANGGRAPH RAG AGENT                              │
│                                                                      │
│   ┌──────────────┐                                                   │
│   │ grade_question│─── "Is this a KB question or general chat?"      │
│   └──────┬───────┘                                                   │
│          │                                                           │
│    ┌─────┴─────┐                                                     │
│    ▼           ▼                                                     │
│  retrieve   direct_answer ──► END                                    │
│    │                                                                 │
│    ▼                                                                 │
│  grade_documents ─── "Are these chunks relevant to the question?"    │
│    │                                                                 │
│    ├── relevant ────────► generate ──► grade_answer                   │
│    │                                     │                           │
│    └── not relevant ──► re_retrieve      ├── grounded ──► return ──► END
│         (rewrite query,   │              │                           │
│          try again)       │              └── hallucination           │
│              │            │                   │                      │
│              └────────────┘                   └──► re_retrieve       │
│                                                                      │
│   Max retries: 2 (prevents infinite loops)                           │
│   State: question, retrieval_query, retrieved_docs, docs_relevant,   │
│          answer_grounded, draft_answer, retry_count, user_id         │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐
          │    ChromaDB      │       │   SQLite         │
          │  (vector store)  │       │  (conversation   │
          │                  │       │   history +      │
          │  Stores embedded │       │   retrieval      │
          │  document chunks │       │   audit log)     │
          └─────────────────┘       └─────────────────┘
```

### File-by-File Breakdown

| File | Purpose | Key Concepts |
|------|---------|-------------|
| `main.py` | Entry point — validates env + index, starts Q&A loop | Startup checks |
| `agent/state.py` | `RAGState` — tracks retrieval process state | `question` vs `retrieval_query` (may differ after rewrite) |
| `agent/nodes.py` | All nodes: retrieve, grade, generate, route | Structured graders, chain-of-thought, self-correction |
| `agent/graph.py` | Build the cyclic RAG graph | Conditional edges with cycles, `SqliteSaver` |
| `pipeline/indexer.py` | Load → chunk → embed → store in ChromaDB | `RecursiveCharacterTextSplitter`, `OpenAIEmbeddings`, `Chroma` |
| `pipeline/retriever.py` | 3 retrieval strategies | Similarity, MMR, Hybrid (BM25 + vector) |
| `memory/conversation.py` | Audit log for conversations + retrieval quality | Separate from LangGraph checkpointer |
| `data/seed_docs.py` | Creates sample company documents | HR policy, remote work, product roadmap, onboarding guide |

### Key Concepts Taught

#### The RAG Pipeline (Offline — Indexing)

```
  Documents (txt files)
       │
       ▼
  ┌─────────────────────────────────────┐
  │  1. LOAD                            │
  │     DirectoryLoader + TextLoader    │
  │     → Document objects with         │
  │       .page_content + .metadata     │
  └──────────┬──────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────┐
  │  2. CHUNK                           │
  │     RecursiveCharacterTextSplitter  │
  │     chunk_size=800, overlap=100     │
  │                                     │
  │     Splits at: paragraphs → lines   │
  │     → words → characters            │
  │                                     │
  │     Why 800? Small enough to be     │
  │     specific, large enough for a    │
  │     complete thought.               │
  └──────────┬──────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────┐
  │  3. EMBED                           │
  │     OpenAIEmbeddings                │
  │     (text-embedding-3-small)        │
  │                                     │
  │     Each chunk → 1536-dim vector    │
  │     that captures semantic meaning  │
  └──────────┬──────────────────────────┘
             │
             ▼
  ┌─────────────────────────────────────┐
  │  4. STORE                           │
  │     ChromaDB (local, SQLite-based)  │
  │     Stores: vector + text + metadata│
  │     Persists to disk                │
  └─────────────────────────────────────┘
```

#### Retrieval Strategies

```
STRATEGY 1: Cosine Similarity (baseline)
  Query → embed → find top-k most similar vectors
  Pro:  Fast, simple
  Con:  May return 4 chunks that all say the same thing

STRATEGY 2: MMR (Max Marginal Relevance)
  Query → embed → find 20 candidates → iteratively pick k=4
  balancing relevance AND diversity
  
  Formula: score = λ × relevance - (1-λ) × similarity_to_already_picked
  λ=0.5 → balanced
  
  Pro:  Better coverage of multi-faceted questions
  Con:  Slightly slower

STRATEGY 3: Hybrid (Vector + BM25)
  Vector search (semantic)  +  BM25 keyword search (exact match)
  Merged via Reciprocal Rank Fusion (RRF)
  
  RRF score = Σ 1/(rank + k) across both retrievers
  
  Pro:  Catches both semantic similarity AND exact keyword matches
  Con:  BM25 needs all docs in memory
```

#### Self-Correction Loop

```
The graph catches TWO major RAG failure modes:

1. WRONG RETRIEVAL (docs don't match question)
   ┌──────────────┐
   │ grade_docs:  │ → "Are these docs relevant to the question?"
   │ LLM-as-judge │   Uses structured output: GradeDocuments(relevant: bool)
   └──────┬───────┘
          │
          ├── relevant=True  → proceed to generate
          └── relevant=False → re_retrieve:
                                 - LLM rewrites the query
                                   "overtime" → "overtime pay compensation policy"
                                 - Retrieves again with new query
                                 - Loops back to grade_docs

2. HALLUCINATION (answer adds facts not in docs)
   ┌──────────────┐
   │ grade_answer: │ → "Does every claim have support in the docs?"
   │ LLM-as-judge  │   Uses structured output: GradeAnswer(grounded: bool)
   └──────┬────────┘
          │
          ├── grounded=True  → return answer to user
          └── grounded=False → re_retrieve → grade_docs → generate again
```

#### Why Separate Grader LLM Calls?

```
The generation LLM can't reliably say "I don't have enough context."
It tends to hallucinate to fill gaps.

A SEPARATE grader LLM with a DIFFERENT prompt catches this:
  - Generator prompt: "Answer helpfully from the context"
  - Grader prompt: "Find contradictions between answer and context"

Same model, different role = independent safety layer.
```

---

## 4. Project 3: Hallucination & Reliability

### What It Does

Five standalone scripts, each demonstrating a specific technique to make LLM outputs more reliable. Plus a `common_use_cases.py` that shows domain-specific patterns.

### The 5 Techniques at a Glance

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                        │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 04_GUARDRAILS   │  ← Is it a jailbreak? Off-topic?   │
│              │ (input guard)   │     PII in input?                   │
│              └────────┬────────┘                                     │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 01_STRUCTURED   │  ← Force typed output (Pydantic)   │
│              │ OUTPUTS         │     Eliminate format hallucinations │
│              └────────┬────────┘                                     │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 02_SELF_RAG     │  ← Grade docs + grade answer       │
│              │ (retrieve loop) │     Retry if retrieval fails       │
│              └────────┬────────┘                                     │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 03_FACT_CHECKER │  ← Extract claims, verify each     │
│              │ (LLM-as-judge)  │     against source document        │
│              └────────┬────────┘                                     │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 05_CONFIDENCE   │  ← Self-assess confidence          │
│              │ SCORING         │     Route low → human/disclaimer   │
│              └────────┬────────┘                                     │
│                       │                                              │
│              ┌────────▼────────┐                                     │
│              │ 04_GUARDRAILS   │  ← PII in output? Toxic? Safe?    │
│              │ (output guard)  │                                     │
│              └────────┬────────┘                                     │
│                       │                                              │
│                  SAFE RESPONSE                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Technique 1: Structured Outputs (`01_structured_outputs.py`)

**Problem:** LLM returns `{"amount": "$50.00"}` instead of `{"amount": 50.0}` — wrong type, silent bug.

**Solution:** Pydantic models + `.with_structured_output()`

```
THREE PATTERNS DEMONSTRATED:

Pattern 1: Typed Extraction
  Input:  "I spent $127.50 on a flight to NYC"
  Output: ExpenseReport(amount=127.5, category="travel", requires_approval=True)
  
  Key: @field_validator ensures business rules (amount > 0, round to 2 decimals)

Pattern 2: Chain-of-Thought via Structured Output
  Schema: SentimentAnalysis(reasoning, sentiment, confidence, key_phrases)
  
  Putting 'reasoning' BEFORE 'sentiment' forces the LLM to think first.
  This improves calibration — the model reasons, THEN decides.

Pattern 3: Mandatory Source Citation
  Schema: PolicyAnswer(found_in_policy, answer, source_doc, direct_quote)
  
  Forces the LLM to cite WHERE the answer came from.
  If it can't cite → found_in_policy=False → prevents hallucination.
```

### Technique 2: Self-RAG (`02_self_rag.py`)

**Problem:** Basic RAG always generates even when retrieval fails.

**Solution:** Grade-and-retry loop (miniature version of Project 2).

```
  retrieve → grade_docs ─── relevant ──► generate → grade_answer ─── grounded ──► return
                  │                                       │
              not relevant                           hallucination
                  │                                       │
              rewrite query ◄─────────────────────────────┘
              (max 2 retries)

  Uses a fake KB to demonstrate in isolation.
  DocGrade(relevant: bool) and AnswerGrade(grounded: bool, issue: str)
```

### Technique 3: Fact Checker (`03_fact_checker.py`)

**Problem:** LLM says "employees get 25 days leave" — source says 20.

**Solution:** Two-step LLM-as-judge pipeline.

```
Step 1: DECOMPOSE answer into atomic claims
  "Employees get 20 days leave and sick leave requires a doctor's note"
  →  Claim 1: "employees get 20 days annual leave"
  →  Claim 2: "sick leave requires a doctor's note"

Step 2: VERIFY each claim against the source document
  Claim 1: ✅ Source says "Annual leave: 20 days per year"
  Claim 2: ✅ Source says "Doctor's note required for 3+ consecutive days"

  Verdict: PASS | FAIL | UNCERTAIN
  Score:   0.0 - 1.0
  Corrections: ["Claim X → Actual: Y"]
  Unsupported: ["Claims not in source at all"]
```

### Technique 4: Guardrails (`04_guardrails.py`)

**Problem:** Prompt injection, PII leaks, off-topic abuse.

**Solution:** Input guard + output guard wrapping every LLM call.

```
INPUT GUARD (before LLM):
  ┌─────────────────────────────────────┐
  │ is_jailbreak?  "Ignore all prior   │
  │                 instructions..."    │ → BLOCK
  │                                     │
  │ is_in_scope?   "Write me Python    │
  │                 code"              │ → REFUSE (off-topic)
  │                                     │
  │ is_safe?       Abusive/harmful?    │ → BLOCK
  └─────────────────────────────────────┘

OUTPUT GUARD (after LLM):
  Layer 1: REGEX PII scan (fast, high precision)
    email:       user@example.com → [REDACTED:EMAIL]
    SSN:         123-45-6789 → [REDACTED:SSN]
    phone:       +1-555-123-4567 → [REDACTED:PHONE]
    credit_card: 4111-2222-3333-4444 → [REDACTED:CREDIT_CARD]

  Layer 2: LLM safety judge (catches unstructured PII like names/addresses)
    OutputSafetyResult(is_safe, has_pii, is_on_topic, concerns)
```

### Technique 5: Confidence Scoring (`05_confidence_scoring.py`)

**Problem:** LLMs are overconfident — they never say "I don't know."

**Solution:** Multi-layer confidence assessment + routing.

```
PATTERN 1: Self-Assessment
  Schema: ConfidentAnswer(reasoning, confidence, confidence_level, answer, caveats)
  
  Putting 'reasoning' BEFORE 'answer' forces introspection.
  confidence_level: high | medium | low | unknown

PATTERN 2: Consistency Probing
  Ask the same question 3 ways → check if answers agree.
  Inconsistency = the LLM is guessing.
  Consistent answers = higher reliability.

PATTERN 3: Confidence-Based Routing
  HIGH     → answer directly ✅
  MEDIUM   → answer + caveats ⚠️
  LOW      → answer + strong disclaimer 🔶
  UNKNOWN  → escalate to human, don't answer 🔴

  Domain-specific thresholds:
    Medical:  ≥0.95 → answer, <0.80 → escalate to doctor
    Financial: ≥0.90 → answer, <0.70 → route to live data API
    Support:  ≥0.80 → answer, <0.60 → route to human agent
```

### Common Use Cases (`common_use_cases.py`)

```
DOMAIN              HALLUCINATION RISK          MITIGATION
────────────────     ────────────────────        ──────────────────────────
Customer Support     Invents policies            RAG + citation + fact check
Financial Data       Wrong numbers               NEVER let LLM generate numbers;
                                                 retrieve from DB, LLM only formats
Code Generation      Hallucinated APIs           Self-review + execution feedback
Medical/Legal        Dangerous misinformation    High confidence threshold + human loop
Internal KB          Mixes confidential data     Scoped retrieval + output guard
```

### The Hallucination Taxonomy

```
TYPE 1: INTRINSIC — contradicts the provided context
  Source: "20 days leave" → LLM: "25 days leave"
  Fix: Fact checker (03_fact_checker.py)

TYPE 2: EXTRINSIC — adds info NOT in context (may be true or false)
  Source: says nothing about overtime → LLM answers about overtime anyway
  Fix: Structured output with citation (01_structured_outputs.py)

TYPE 3: FAITHFULNESS — technically correct but misleading/incomplete
  LLM: "Employees can take leave" (true) but omits "max 5 days/quarter" (critical)
  Fix: Completeness grader, multi-chunk retrieval

TYPE 4: FORMAT — right info, wrong format
  Expected: {"amount": 50.0} → Got: {"amount": "$50.00"}
  Fix: Pydantic validators (01_structured_outputs.py)
```

### Decision Tree: Which Technique to Use

```
Is the answer about NUMBERS or SPECIFIC FACTS?
  YES → Retrieve from DB/API. LLM only formats. Never generates numbers.

Is there a SOURCE DOCUMENT?
  YES → RAG + structured output with citation + fact checker

Is the domain HIGH STAKES (medical, legal, financial)?
  YES → Confidence scoring + human-in-the-loop for low confidence

Is the output FORMAT critical?
  YES → Pydantic structured output with validators

Is there risk of PROMPT INJECTION or PII LEAK?
  YES → Input/output guardrails

None of the above?
  → Basic LLM call is fine
```

---

## 5. Shared Concepts

### LangGraph State Pattern

All three projects use the same state management pattern:

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]  # APPEND on update
    turn_count: int                                       # REPLACE on update
```

- `Annotated[list, operator.add]` → new messages are **appended** (not replaced)
- Plain types → **replaced** on each update
- Every node receives full state, returns a partial update dict

### Structured Output Pattern

Used across all three projects for reliable LLM responses:

```python
class MySchema(BaseModel):
    field: str = Field(description="LLM reads this as instructions")

structured_llm = llm.with_structured_output(MySchema)
result: MySchema = structured_llm.invoke("...")
# result is a typed Python object, guaranteed to match schema
```

### LLM-as-Judge Pattern

The most important reliability technique (used in Project 2 and 3):

```
GENERATOR LLM:  "Answer this question helpfully"     → tries to be useful
JUDGE LLM:      "Find errors in this answer"          → tries to find flaws

Same model, different prompt = independent verification layer.

Always use structured output for the judge (binary decisions are more reliable).
```

### SQLite Dual Usage

```
Purpose 1: APPLICATION DATA
  Products, orders, tickets, documents
  → Direct SQL queries from tools

Purpose 2: AGENT MEMORY
  LangGraph SqliteSaver checkpointer
  → Serialises full graph state per thread_id
  → Restores conversation on restart
```

---

## 6. Technology Stack Reference

| Technology | Role | Used In |
|---|---|---|
| **LangChain** | LLM abstraction, prompts, tools, output parsers | All 3 |
| **LangGraph** | Stateful graph-based agent orchestration | P1, P2, P3 (02) |
| **OpenAI GPT-4o-mini** | LLM brain (tool calling, generation, grading) | All 3 |
| **MCP (FastMCP)** | Tool server protocol (tools, resources, prompts) | P1 only |
| **langchain-mcp-adapters** | Converts MCP tools → LangChain tools | P1 only |
| **ChromaDB** | Local vector store for document embeddings | P2 only |
| **OpenAI Embeddings** | text-embedding-3-small (1536 dims) | P2 only |
| **BM25** | Keyword retrieval for hybrid search | P2 only |
| **SQLite** | App data + agent memory (SqliteSaver) | P1, P2 |
| **Pydantic** | Typed schemas for structured LLM output | All 3 |
| **python-dotenv** | Load API keys from .env | All 3 |

---

## 7. Architecture Comparison

```
              Project 1 (MCP)           Project 2 (RAG)           Project 3 (Reliability)
              ───────────────           ───────────────           ─────────────────────

Graph Shape   Linear + loop             Cyclic (self-correct)     Mostly linear
              model → tools → model     grade → retrieve →        input → LLM → check
                                        grade → generate →          → output
                                        grade → retry

LLM Calls     1 per turn               4-8 per question           1-3 per technique
              (model + optional tools)  (route + retrieve +        (structured output
                                         grade + generate +         + judge)
                                         grade again)

Data Source    SQLite (structured)       ChromaDB (unstructured)   Inline test data
              SQL queries via tools     Vector similarity search   No external DB

Key Pattern   Tool calling (ReAct)      Self-correction loop      LLM-as-judge
              "Reason then Act"         "Retrieve, Grade, Retry"  "Generate then Verify"

Memory        SqliteSaver (persistent)  SqliteSaver + audit log   None (stateless demos)

Safety        None (demo scope)         Hallucination grader      Full safety stack
                                                                   (guardrails, PII,
                                                                    confidence routing)
```

---

## 8. Setup & Running

### Prerequisites

```bash
# Python 3.10+
python --version

# OpenAI API key (used by all three projects)
export OPENAI_API_KEY="sk-..."
```

### Project 1: MCP Agent

```bash
cd 01_mcp_project
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY
python data/seed_db.py        # create database with demo data
python main.py                # start the agent
```

### Project 2: Agentic RAG

```bash
cd 02_rag_project
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY
python data/seed_docs.py      # create sample documents
python -c "from pipeline.indexer import build_index; build_index()"  # embed & index
python main.py                # start the Q&A system
```

### Project 3: Hallucination & Reliability

```bash
cd 03_hallucination_reliability
pip install -r requirements.txt
# Set OPENAI_API_KEY in environment or .env

python 01_structured_outputs.py    # typed extraction patterns
python 02_self_rag.py              # self-correcting RAG loop
python 03_fact_checker.py          # LLM-as-judge verification
python 04_guardrails.py            # input/output safety
python 05_confidence_scoring.py    # confidence-based routing
python common_use_cases.py         # domain-specific patterns
```

---

## Quick Reference: What to Read for Each Topic

| I want to learn... | Read this |
|---|---|
| How to build an AI agent from scratch | P1: `agent/graph.py` → `agent/nodes.py` → `agent/state.py` |
| How MCP works | P1: `mcp_server/server.py` → `tools/*.py` |
| How to design LLM tools | P1: `mcp_server/tools/product_tools.py` (read the docstrings) |
| How RAG works end-to-end | P2: `pipeline/indexer.py` → `pipeline/retriever.py` |
| How to make RAG self-correct | P2: `agent/nodes.py` (grade_documents, grade_answer, re_retrieve) |
| How to prevent hallucinations | P3: `03_fact_checker.py` → `02_self_rag.py` |
| How to force typed LLM output | P3: `01_structured_outputs.py` |
| How to add safety guardrails | P3: `04_guardrails.py` |
| How to handle LLM uncertainty | P3: `05_confidence_scoring.py` |
| Real-world hallucination patterns | P3: `common_use_cases.py` |
| How persistent memory works | P1: `agent/graph.py` (SqliteSaver + thread_id) |
| How vector search works | P2: `pipeline/retriever.py` (similarity, MMR, hybrid) |
