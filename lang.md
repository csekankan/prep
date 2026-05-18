# Agentic AI — Complete Concept Reference

> Everything you need to go from zero to production-grade agentic systems.
> Read top to bottom once, then use as a reference.

---

## Table of Contents

1. [The Mental Model — What is Agentic AI?](#1-the-mental-model)
2. [LLMs — The Brain](#2-llms--the-brain)
3. [LangChain — The Foundation](#3-langchain--the-foundation)
4. [LangGraph — The Orchestrator](#4-langgraph--the-orchestrator)
5. [RAG — Retrieval Augmented Generation](#5-rag--retrieval-augmented-generation)
6. [MCP — Model Context Protocol](#6-mcp--model-context-protocol)
7. [Agents & Agent Patterns](#7-agents--agent-patterns)
8. [Memory — All Four Types](#8-memory--all-four-types)
9. [Tools & Actions](#9-tools--actions)
10. [Multi-Agent Systems](#10-multi-agent-systems)
11. [Hallucination & Reliability](#11-hallucination--reliability)
12. [Production Architecture](#12-production-architecture)
13. [Glossary](#13-glossary)

---

## 1. The Mental Model

### What is an Agent?

A traditional program: `Input → fixed logic → Output`

An agent: `Input → LLM decides what to do → calls tools → observes result → LLM decides again → ... → Output`

The fundamental difference is **autonomy over the execution path**. The LLM itself decides the sequence of steps rather than a hardcoded program. This is powerful and dangerous in equal measure.

### The Stack in One Picture

```
┌─────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                      │
│                                                              │
│   User Input                                                 │
│       │                                                      │
│       ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              LangGraph (Orchestration)                │  │
│   │                                                       │  │
│   │  State ──► Node ──► Node ──► Node ──► End            │  │
│   │               │       │       │                       │  │
│   │               └───────┴───────┘  (loops, branches)   │  │
│   └──────────────────────────────────────────────────────┘  │
│       │                    │                    │            │
│       ▼                    ▼                    ▼            │
│   ┌────────┐         ┌──────────┐         ┌─────────┐       │
│   │ LLM    │         │   RAG    │         │  Tools  │       │
│   │(OpenAI │         │(ChromaDB)│         │ (MCP /  │       │
│   │ Claude)│         │          │         │ @tool)  │       │
│   └────────┘         └──────────┘         └─────────┘       │
│       │                    │                    │            │
│       └────────────────────┴────────────────────┘            │
│                            │                                 │
│                    ┌───────────────┐                         │
│                    │    Memory     │                         │
│                    │  (SQLite /    │                         │
│                    │  Vector DB)   │                         │
│                    └───────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### How the layers connect

| Layer | What it does | Key library |
|-------|-------------|-------------|
| LLM | Thinks, reasons, decides | `langchain-openai`, `langchain-anthropic` |
| LangChain | Prompts, chains, tool bindings | `langchain` |
| LangGraph | Flow control, state, loops | `langgraph` |
| RAG | Long-term knowledge retrieval | `langchain-chroma`, `chromadb` |
| MCP | Standardised external connections | `mcp`, `langchain-mcp-adapters` |
| Memory | Persistence across sessions | `langgraph-checkpoint-sqlite` |

---

## 2. LLMs — The Brain

### What an LLM actually does

An LLM is a function: `tokens_in → probability_distribution_over_next_token`

It doesn't "understand" — it predicts the most statistically likely continuation of a sequence. The fact that this produces useful reasoning is an emergent property of scale.

**Token**: smallest unit of text (roughly ¾ of a word). "Hello world" ≈ 2 tokens. "LangGraph" ≈ 3 tokens.

**Context window**: maximum tokens in+out simultaneously. GPT-4o: 128k tokens ≈ 96,000 words ≈ 300 pages of text.

### Chat models vs. completion models

**Completion model** (old): raw text in → raw text out. Predict next word.

**Chat model** (modern): structured messages in → message out.

```python
messages = [
    {"role": "system",    "content": "You are a support agent."},
    {"role": "user",      "content": "Where is my order?"},
    {"role": "assistant", "content": "Let me check..."},
    {"role": "user",      "content": "Order ID is ORD-1042"},
]
# The LLM sees ALL of these and continues the conversation
```

Every LangChain and LangGraph application uses chat models. The `system` role sets the AI's persona and instructions. The `user` role is the human. The `assistant` role is previous AI turns. The `tool` role carries tool execution results.

### Function / Tool Calling

Modern LLMs can output **structured JSON** instead of (or in addition to) plain text:

```
Normal output:  "I'll search for that product now."

Tool call output:
{
  "type": "tool_call",
  "name": "search_products",
  "arguments": {"query": "wireless earbuds", "max_price": 50.0}
}
```

The LLM doesn't execute the tool — it just requests it. Your code executes it and feeds the result back. This is the core mechanism behind all agents.

### Temperature and determinism

`temperature=0`: deterministic — same input always gives same output. Use for tool calling, grading, routing.

`temperature=0.7`: creative — varied outputs each run. Use for writing, brainstorming.

`temperature=1.0+`: very random. Rarely useful in production.

**Rule**: set `temperature=0` for any agent that makes decisions or calls tools. Set higher for creative generation nodes only.

### Choosing a model

| Model | Best for | Cost |
|-------|---------|------|
| `gpt-4o-mini` | Most agent tasks, fast tool calling | Cheap |
| `gpt-4o` | Hard reasoning, complex tool orchestration | Medium |
| `claude-3-5-sonnet` | Long context, nuanced instructions | Medium |
| `claude-3-7-sonnet` | Extended thinking, hardest tasks | Higher |
| `ollama/llama3.2` | Local, private, no API cost | Free |

**Practical pattern**: use `gpt-4o-mini` for simple nodes (routing, extraction), `gpt-4o` or `claude-3-5-sonnet` for complex reasoning nodes.

### Embeddings

An embedding model converts text to a dense vector (list of numbers):

```
"Annual leave policy" → [0.23, -0.87, 0.44, ... 1536 numbers]
"vacation days rules" → [0.21, -0.83, 0.47, ... 1536 numbers]
```

These two phrases have **similar vectors** because they mean the same thing. This is the foundation of all semantic search and RAG.

**Key embedding models:**
- `text-embedding-3-small` (OpenAI) — cheap, 1536 dimensions, great quality
- `text-embedding-3-large` (OpenAI) — higher quality, 3072 dimensions
- `all-MiniLM-L6-v2` (HuggingFace) — free, runs locally, slightly lower quality

---

## 3. LangChain — The Foundation

### What LangChain is

LangChain is a Python/JavaScript framework that provides:
- Unified interfaces to 50+ LLM providers
- Composable building blocks (`Runnable` protocol)
- Pre-built integrations for tools, document loaders, vector stores
- The LCEL pipe syntax for chaining components

It is NOT a framework you must use — it's a convenience layer. But the ecosystem and integrations make it the default choice.

### The Runnable Protocol

Every LangChain component implements `Runnable`. Every `Runnable` has:

```python
component.invoke(input)          # call once, return result
component.stream(input)          # yield tokens/chunks as they arrive
component.batch([input1, input2]) # call in parallel, return list
component.astream(input)         # async streaming (use in FastAPI/async apps)
```

This uniformity means you can swap any component (different LLM, different retriever) without changing the rest of your chain.

### LCEL — LangChain Expression Language

The pipe operator `|` composes Runnables into chains:

```python
chain = prompt | llm | output_parser
```

This is NOT function composition — it creates a lazy `RunnableSequence` that:
- Connects components so output of one feeds input of next
- Automatically handles streaming (stream propagates through the whole chain)
- Supports parallel branches with `RunnableParallel`
- Supports fallbacks with `.with_fallbacks()`

```python
# Sequential: A then B then C
chain = A | B | C

# Parallel: run A and B simultaneously, pass both results to C
chain = RunnableParallel({"result_a": A, "result_b": B}) | C

# Fallback: try expensive_model first, fall back to cheap_model on error
safe_llm = expensive_model.with_fallbacks([cheap_model])
```

### Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a support agent for {company}."),  # {company} is a variable
    ("human",  "{question}"),
])

# Invoke fills in the variables
messages = prompt.invoke({"company": "TechShop", "question": "Where is my order?"})
# Returns: [SystemMessage("You are a support agent for TechShop."),
#           HumanMessage("Where is my order?")]
```

**Why templates instead of f-strings?**
- Type-safe variable injection
- Supports few-shot examples declaratively
- Compatible with LCEL pipe syntax
- Can be serialised and loaded from files

### Structured Output — The Most Important Pattern

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class Sentiment(BaseModel):
    label:      str   = Field(description="positive | negative | neutral")
    confidence: float = Field(description="0.0 to 1.0")
    reason:     str   = Field(description="one sentence explanation")

llm = ChatOpenAI(model="gpt-4o-mini")
structured_llm = llm.with_structured_output(Sentiment)

result: Sentiment = structured_llm.invoke("I love this product!")
print(result.label)      # "positive"
print(result.confidence) # 0.95
print(result.reason)     # "The user expresses strong positive emotion."
```

**Why this matters:** Without structured output, you parse LLM text with regex or JSON parsing — fragile and error-prone. Structured output uses the LLM's native function-calling to guarantee the schema. `result` is a real typed Pydantic object with validation.

### Document Loaders

```python
from langchain_community.document_loaders import (
    TextLoader,          # .txt files
    PyPDFLoader,         # PDF files
    WebBaseLoader,       # web pages (scrapes HTML)
    CSVLoader,           # CSV rows as documents
    DirectoryLoader,     # load entire folders
    NotionDirectoryLoader, # Notion export
    GitLoader,           # git repository files
)

loader = WebBaseLoader("https://docs.langchain.com")
docs = loader.load()
# docs = [Document(page_content="...", metadata={"source": "https://..."})]
```

Every loader returns `list[Document]`. A `Document` has:
- `page_content: str` — the text content
- `metadata: dict` — source URL, page number, filename, date, etc.

Metadata is critical — it flows through to the vector store and enables source citation and filtering.

### Text Splitters

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,      # target chunk size in characters
    chunk_overlap=100,   # overlap between adjacent chunks
    separators=["\n\n", "\n", " ", ""],  # split priority (paragraph > sentence > word > char)
)

chunks = splitter.split_documents(docs)
```

**Why split?** An entire document produces one embedding vector — too coarse for retrieval. Splitting produces many vectors, each capturing a specific topic. Retrieval can then find the specific passage relevant to a query.

**chunk_size tuning:**
- Too small (<200 chars): loses context, retrieval is noisy
- Too large (>2000 chars): embeddings are less specific, slower
- Sweet spot: 600–1000 characters for most use cases

**chunk_overlap:** ensures a sentence at the boundary of chunk N also appears in chunk N+1. Prevents information loss at chunk edges.

### Output Parsers

```python
from langchain_core.output_parsers import (
    StrOutputParser,              # plain text → string
    JsonOutputParser,             # JSON string → dict
    PydanticOutputParser,         # text → validated Pydantic object (uses prompting)
    CommaSeparatedListOutputParser, # "a, b, c" → ["a", "b", "c"]
)

# Modern approach: use .with_structured_output() instead of PydanticOutputParser
# PydanticOutputParser works via prompting (fragile)
# .with_structured_output() works via function calling (reliable)
```

### LangChain Package Structure

```
langchain-core         → abstract interfaces (Runnable, BaseTool, BaseMessage)
langchain              → chains, agents, some retrievers
langchain-community    → 3rd-party integrations (100+ loaders, stores, tools)
langchain-openai       → ChatOpenAI, OpenAIEmbeddings
langchain-anthropic    → ChatAnthropic
langchain-ollama       → ChatOllama (local models)
langchain-chroma       → Chroma vector store
langchain-mcp-adapters → MCP tool conversion
langgraph              → stateful graph orchestration
```

Install only what you need. Don't install `langchain-community` unless you need a specific integration — it's large.

---

## 4. LangGraph — The Orchestrator

### Why LangGraph exists

LangChain's original `AgentExecutor` was a black box: you gave it tools and a model, it ran in a loop, and you got an answer. Fine for demos, unusable in production because:
- No control over the loop
- No ability to inject state between steps
- No human-in-the-loop
- No multi-agent coordination
- No parallel execution
- Impossible to debug

LangGraph exposes the graph explicitly. You own every node and every edge.

### Core Concepts

#### State

The state is a `TypedDict` (or Pydantic model) that flows through every node in the graph. Think of it as the agent's working memory.

```python
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # Annotated[list, operator.add] means: when a node returns {"messages": [new_msg]},
    # LangGraph APPENDS new_msg to the existing list instead of replacing it.
    # Without this, every node would overwrite the entire message history.
    messages: Annotated[list[BaseMessage], operator.add]
    
    # Normal fields are simply overwritten on each update
    turn_count: int
    last_action: str
    user_id: str
```

**The reducer pattern:** `Annotated[list, operator.add]` is the most important LangGraph pattern. The `operator.add` is the *reducer* — the function that merges a partial update into the existing value. You can write custom reducers for complex merge logic.

#### Nodes

A node is a Python function that:
1. Receives the **complete current state**
2. Does some work (call LLM, execute tool, query DB, anything)
3. Returns a **partial state update** (only the keys it changed)

```python
def call_model(state: AgentState) -> dict:
    # Receives full state
    response = model.invoke(state["messages"])
    
    # Returns PARTIAL update — only what changed
    return {
        "messages": [response],  # operator.add → appended
        "turn_count": state["turn_count"] + 1,  # → overwritten
        # "user_id" not returned → unchanged
    }
```

LangGraph merges the partial update into the global state using each field's reducer.

#### Edges

**Normal edge:** always routes from A to B.
```python
builder.add_edge("tools", "call_model")  # after tools, always go to call_model
```

**Conditional edge:** calls a router function to decide the next node.
```python
def route(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "tools"
    return "end"

builder.add_conditional_edges(
    "call_model",   # from this node
    route,          # call this function
    {"tools": "tools", "end": END}  # map return values to node names
)
```

The router function is NOT a node — it receives state and returns a string. It cannot update state.

#### Compiling and running

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

builder = StateGraph(AgentState)
builder.add_node("call_model", call_model)
builder.add_node("tools",      ToolNode(tools))
builder.set_entry_point("call_model")
builder.add_conditional_edges("call_model", route, {"tools": "tools", "end": END})
builder.add_edge("tools", "call_model")

# Compile — turns the builder into a runnable graph
app = builder.compile(checkpointer=SqliteSaver.from_conn_string("memory.db"))

# Invoke — run the graph to completion
result = app.invoke(
    {"messages": [HumanMessage(content="Hello")], "turn_count": 0, ...},
    config={"configurable": {"thread_id": "user-123"}}  # thread_id enables memory
)

# Stream — get intermediate steps as they happen
async for event in app.astream_events(input, config=config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
```

### Checkpointers — How Memory Works

The checkpointer is what makes LangGraph agents stateful across conversations.

After **every node execution**, LangGraph serialises the complete state to the checkpointer storage. On the next `invoke()` with the same `thread_id`, the state is restored.

```python
# Turn 1
app.invoke({"messages": [HumanMessage("What's the leave policy?")]}, config)
# → graph runs, state saved to SQLite with thread_id="user-123"

# Turn 2 — same thread_id
app.invoke({"messages": [HumanMessage("And what about sick leave?")]}, config)
# → LangGraph restores previous state (includes "What's the leave policy?" turn)
# → APPENDS new message to existing history (operator.add)
# → graph runs with full context

# Different user — different thread_id
app.invoke({"messages": [HumanMessage("Hello")]},
           config={"configurable": {"thread_id": "user-456"}})
# → starts fresh — no memory of user-123's conversation
```

**Available checkpointers:**
- `MemorySaver` — in-RAM, lost on restart. Dev only.
- `SqliteSaver` — SQLite file. Good for single-server production.
- `PostgresSaver` — PostgreSQL. Production, multi-server deployments.
- `RedisSaver` — Redis. High-throughput, distributed.

### Human-in-the-Loop

```python
from langgraph.types import interrupt, Command

def confirmation_node(state: AgentState):
    # This pauses the graph and surfaces state to the caller
    approval = interrupt({
        "message":    "Agent wants to send an email to all customers. Approve?",
        "action":     state["pending_action"],
        "reversible": False,
    })
    # Execution resumes here only after Command(resume=...) is called
    if approval == "yes":
        return {"approved": True}
    return {"approved": False, "messages": [AIMessage("Action cancelled by user.")]}

# In your API / UI:
# 1. Graph pauses at interrupt() and returns current state
# 2. Show state to human for review
# 3. Resume:
result = app.invoke(Command(resume="yes"), config=config)
```

### Send() — Parallel Fan-Out

```python
from langgraph.types import Send

def distribute_tasks(state: AgentState) -> list[Send]:
    # Fan out: process each item in parallel as separate graph instances
    return [
        Send("process_item", {"item": item, "item_index": i})
        for i, item in enumerate(state["items_to_process"])
    ]

builder.add_conditional_edges("distribute", distribute_tasks)
# All instances run in parallel, results collected in "join" node
```

### Subgraphs

A subgraph is a compiled LangGraph graph used as a NODE inside another graph:

```python
research_graph = build_research_subgraph().compile()
writing_graph  = build_writing_subgraph().compile()

# Use subgraphs as nodes in the orchestration graph
main_builder.add_node("research", research_graph)
main_builder.add_node("write",    writing_graph)
main_builder.add_edge("research", "write")
```

Subgraphs have their own state schemas. LangGraph handles state translation between parent and child graphs.

---

## 5. RAG — Retrieval Augmented Generation

### The Problem RAG Solves

LLMs have two fundamental limitations:
1. **Training cutoff** — they know nothing after their training date
2. **No private data** — they've never seen your internal documents

RAG (Retrieval Augmented Generation) solves both by fetching relevant information at query time and injecting it into the prompt as context.

### The Two Phases

#### Phase 1: Indexing (runs offline, once or incrementally)

```
Your Documents
      │
      ▼
   [LOAD]          TextLoader, PDFLoader, WebBaseLoader, etc.
      │             → list[Document(page_content, metadata)]
      ▼
   [CHUNK]         RecursiveCharacterTextSplitter
      │             → list[Document] (smaller chunks)
      ▼
   [EMBED]         OpenAIEmbeddings, HuggingFaceEmbeddings
      │             → each chunk → vector of 1536 floats
      ▼
   [STORE]         Chroma, Pinecone, pgvector
                    → (vector, text, metadata) stored for retrieval
```

#### Phase 2: Retrieval (runs at query time, per user question)

```
User Question: "What is the expense limit?"
      │
      ▼
   [EMBED QUERY]   Same embedding model as indexing
      │             → query vector
      ▼
   [SEARCH]        Find top-k chunks with most similar vectors
      │             → [Document("...expenses under $50..."), Document("...")]
      ▼
   [AUGMENT]       Build prompt: "Context: {docs}\nQuestion: {question}"
      │
      ▼
   [GENERATE]      LLM produces answer grounded in context
      │
      ▼
   Answer: "Expenses under $50 don't require approval."
```

### Retrieval Strategies

#### 1. Cosine Similarity Search (baseline)

Embeds the query, finds chunks with the highest dot product with the query vector. Fast and simple.

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)
```

**Limitation:** May return 4 chunks that all say the same thing.

#### 2. MMR — Max Marginal Relevance (recommended default)

Fetches many candidates by similarity, then selects a diverse subset. Balance between relevance and coverage.

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 20, "lambda_mult": 0.5}
)
# lambda_mult: 0 = max diversity, 1 = max relevance (0.5 = balanced)
```

**When to use:** Multi-aspect questions ("explain our leave policy") where you want different sections.

#### 3. Hybrid Search (vector + BM25)

Combines dense vector search with BM25 keyword ranking, merged with Reciprocal Rank Fusion.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

bm25     = BM25Retriever.from_documents(all_docs); bm25.k = 4
vector   = vectorstore.as_retriever(search_kwargs={"k": 4})
retriever = EnsembleRetriever(retrievers=[vector, bm25], weights=[0.6, 0.4])
```

**When to use:** When queries contain specific product names, codes, IDs, or exact terms that semantic search misses.

#### 4. Metadata Filtering

```python
# Only retrieve from a specific document
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4,
        "filter": {"filename": "hr_policy.txt"}  # ChromaDB metadata filter
    }
)
```

**When to use:** Multi-tenant systems (only search user A's documents), time-filtered search (only recent docs), domain routing (HR questions → HR docs only).

### Chunking Strategy Deep Dive

Chunking is one of the highest-impact decisions in a RAG system.

| Strategy | How | Best for |
|----------|-----|---------|
| Fixed-size character | Split every N chars | Simple, predictable |
| Recursive character | Split at paragraphs, then sentences, then words | Most documents |
| Token-based | Split by LLM token count | When using token limits precisely |
| Semantic | Split where meaning changes (uses embeddings) | High accuracy, slow |
| Document-structure | Split at headers/sections | Markdown, HTML, legal docs |

**Parent-child chunking:** Index small chunks (for precise retrieval) but retrieve their parent chunks (for more context). The best of both worlds.

```python
from langchain.retrievers import ParentDocumentRetriever
# Stores small chunks in vector store for retrieval precision
# But returns the full parent document chunk for LLM context
```

### Advanced RAG Patterns

#### HyDE — Hypothetical Document Embeddings

Instead of embedding the question, generate a hypothetical answer and embed that:

```
Question: "What is the sick leave policy?"
  ↓
Hypothetical answer: "The sick leave policy states employees receive 10 days per year..."
  ↓
Embed the hypothetical answer → search for similar real documents
```

Why it works: The style of a hypothetical answer matches the style of real policy documents better than the style of a question.

#### Self-RAG

The LLM grades its own retrieval and generation:
1. Retrieve docs
2. Grade: "Are these docs relevant to the question?"
3. If no → rewrite query, retrieve again
4. Generate answer
5. Grade: "Is this answer supported by the docs?"
6. If no → regenerate or retry

Implemented as a LangGraph graph with conditional edges (see `02_rag_project/`).

#### Corrective RAG (CRAG)

If retrieval quality is poor, supplement with a web search:
1. Retrieve from vector store
2. Grade document relevance
3. If high relevance → generate from docs
4. If low relevance → supplement with Tavily/Brave web search
5. Combine docs and web results → generate

#### RAPTOR — Hierarchical Summarisation

Build a tree of summaries at multiple levels:
- Level 0: raw chunks (most specific)
- Level 1: summaries of groups of chunks
- Level 2: summaries of level-1 summaries

Retrieve from the right level: big-picture questions → high level, specific questions → low level.

### Embedding Quality

The quality of your embeddings determines the ceiling of your RAG system. Signs of poor embeddings:
- Retrieval returns semantically wrong chunks consistently
- Similar questions return completely different chunks
- Domain-specific terms aren't semantically grouped correctly

**Solutions:**
- Use a domain-specific embedding model (e.g., BioBERT for medical, LegalBERT for legal)
- Fine-tune embeddings on your domain (expensive but highest quality)
- Use a reranker after retrieval to re-score with a cross-encoder (Cohere Rerank, FlashRank)

### Vector Stores — Choosing the Right One

| Vector Store | Best for | Notes |
|-------------|---------|-------|
| Chroma | Local dev, small production | SQLite-backed, zero setup |
| FAISS | Fast local search, offline | Meta's library, in-memory or file |
| Pinecone | Cloud production, scalable | Managed, expensive |
| Weaviate | Rich filtering, semantic properties | Self-hosted or cloud |
| pgvector | Already using PostgreSQL | Best for unified DB architecture |
| Qdrant | High-performance production | Open-source, cloud option |

**Decision:** Use Chroma for development. If already using PostgreSQL, use pgvector. Otherwise, Pinecone or Qdrant for production.

---

## 6. MCP — Model Context Protocol

### What Problem MCP Solves

Before MCP: If you want Claude to access GitHub, you write custom LangChain tools. If you then want to use the same GitHub integration with GPT-4o, you rewrite it. 10 models × 20 tools = 200 custom integrations.

After MCP: Write one MCP server for GitHub. Any MCP-compatible client (Claude Desktop, Cursor, your LangGraph agent) gets access automatically. 10 models + 20 tools = 30 implementations.

### Architecture

```
┌──────────────────────────────────┐
│           Host Application       │
│  (Claude Desktop, Cursor, etc.)  │
│                                  │
│  ┌────────────────────────────┐  │
│  │       MCP Client           │  │
│  │  (built into the host app) │  │
│  └────────────────────────────┘  │
│              │ JSON-RPC 2.0       │
└──────────────┼───────────────────┘
               │
     ┌─────────┴─────────┐
     │    MCP Server     │
     │  (your code or    │
     │  a community one) │
     └─────────┬─────────┘
               │
     ┌─────────┴─────────┐
     │  Real World       │
     │  (files, APIs,    │
     │   databases)      │
     └───────────────────┘
```

### The Three Primitives

#### Tools — Functions the LLM can call

```python
@mcp.tool()
def search_database(query: str, limit: int = 10) -> list[dict]:
    """
    Search the product database.
    
    Use when: user asks about products, availability, pricing.
    Returns: list of matching products.
    """
    return db.search(query, limit=limit)
```

- Has side effects (reads/writes are expected)
- LLM decides when to call it based on the docstring
- Returns structured data
- The docstring IS the LLM's decision guide — make it excellent

#### Resources — Read-only data by URI

```python
@mcp.resource("products://catalog")
def get_catalog() -> str:
    """The full product catalog."""
    return format_catalog(db.get_all_products())

@mcp.resource("orders://{order_id}")
def get_order(order_id: str) -> str:
    """Get a specific order by ID."""
    return str(db.get_order(order_id))
```

- No side effects — pure data retrieval
- Accessed by URI (like REST GET endpoints)
- The LLM requests these URIs when it needs the data
- Think of them as "files the LLM can read"

#### Prompts — Reusable templates

```python
@mcp.prompt()
def escalation_template(customer_name: str, issue: str) -> str:
    """Generate an escalation message."""
    return f"Dear {customer_name}, we're escalating your issue: {issue}..."
```

- Reusable prompt templates defined server-side
- Appear as slash commands in Claude Desktop, Cursor
- Prompt engineering packaged as a service

### Transport Mechanisms

**stdio (local):** The MCP client spawns the server as a subprocess. Communication via stdin/stdout. Zero network config. Use for:
- CLI tools
- Development
- Tools that need local filesystem access

```python
# In the client (your LangGraph agent):
{
    "my-server": {
        "command": "python",
        "args": ["mcp_server/server.py"],
        "transport": "stdio"
    }
}
```

**SSE — Server-Sent Events (network):** The server runs as an HTTP service. Clients connect to it over the network. Use for:
- Remote tools
- Multi-client access
- Cloud deployments

```python
{
    "remote-server": {
        "url": "https://my-mcp-server.com/sse",
        "transport": "sse"
    }
}
```

### Building an MCP Server with FastMCP

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> str:
    """What this tool does and when to use it."""
    result = await do_something(param)
    return str(result)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

FastMCP handles all JSON-RPC boilerplate. Your tool functions are just regular Python functions.

### Consuming MCP in LangGraph

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async with MultiServerMCPClient({
    "my-server": {"command": "python", "args": ["server.py"], "transport": "stdio"},
    "github":    {"url": "http://mcp-github:8000/sse",         "transport": "sse"},
}) as client:
    tools = await client.get_tools()   # auto-converted to LangChain tools
    agent = create_react_agent(model, tools)
    result = await agent.ainvoke({"messages": [("user", "List my GitHub PRs")]})
```

`langchain-mcp-adapters` converts MCP tool schemas into LangChain `BaseTool` objects automatically. You can use them exactly like any other LangChain tool.

### MCP vs. LangChain @tool

| | MCP Tool | LangChain @tool |
|--|---------|----------------|
| Scope | Cross-application (any MCP client can use it) | Single agent/app |
| Discovery | Automatic via MCP protocol | Manual registration |
| Transport | stdio or SSE (process boundary) | In-process function call |
| Use when | Sharing tools across multiple agents/apps | Agent-specific logic |

**Rule:** Use `@tool` for business logic specific to one agent. Use MCP when you want a tool usable by multiple agents, applications, or AI assistants.

---

## 7. Agents & Agent Patterns

### What Makes Something an "Agent"

Three requirements:
1. **LLM makes decisions** about what to do next (not hardcoded logic)
2. **Affects the environment** by calling tools or writing state
3. **Loops** — observes results and decides whether to continue or stop

A chain (prompt → LLM → output) is not an agent. An agent has a loop.

### ReAct — The Standard Pattern

ReAct = **Re**asoning + **Act**ing. The LLM interleaves reasoning and tool use:

```
Thought: The user wants to know their order status. I should call get_order_status.
Action: get_order_status({"order_id": "ORD-1042"})
Observation: {"status": "shipped", "expected": "2024-12-15"}
Thought: I have the information. I can now answer the user.
Action: Finish
Answer: Your order ORD-1042 is shipped and expected on December 15th.
```

Modern LLMs don't output explicit "Thought:" prefixes — this happens implicitly through function calling. The LLM outputs a tool call, you execute it, the result becomes a `ToolMessage` in the conversation, the LLM continues.

**LangGraph implementation:**
```
call_model → [has tool_calls?] → YES → tools → call_model (loop)
                                  NO  → END
```

### Plan-and-Execute

Splits planning and execution into separate LLM calls:

```
Planner LLM: "To answer 'research quantum computing and write a report':
  Step 1: Search for recent quantum computing papers
  Step 2: Search for commercial applications
  Step 3: Compile findings
  Step 4: Write structured report"

Executor LLM: executes each step, updating the plan as needed
```

**When to use:** Long multi-step workflows where the sequence of steps is known upfront and relatively stable. More structured and predictable than ReAct.

**When NOT to use:** Tasks where each step's output determines the next step (use ReAct instead).

### Reflexion — Self-Improvement

The agent reflects on its failures and improves:

```
Attempt 1: [agent tries task, fails]
Reflection: "I failed because I searched for the wrong keywords. 
             Next time I should search for 'quantum entanglement applications'."
Attempt 2: [agent tries again with reflection in memory]
```

Reflection is stored in episodic memory and retrieved at the start of the next attempt. Requires a task with a clear success/failure signal (code that passes tests, a factual question with a verifiable answer).

### Tool Calling Architecture (modern)

```python
# 1. Bind tools to model
model_with_tools = model.bind_tools([search_products, get_order, create_ticket])

# 2. Model outputs tool call (JSON)
response = model_with_tools.invoke(messages)
# response.tool_calls = [{"name": "search_products", "args": {"query": "earbuds"}, "id": "call_abc123"}]

# 3. Execute the tool
from langgraph.prebuilt import ToolNode
tool_node = ToolNode([search_products, get_order, create_ticket])
# ToolNode reads tool_calls from the AIMessage, executes each, returns ToolMessages

# 4. LLM sees results and continues
# The ToolMessages are added to conversation history
# Next call_model invocation has full context
```

### Agent Design Principles

**1. Minimal tool set**
Every tool is a decision point and an attack surface. The more tools, the more confused the LLM gets about which to use. Start with 3-5 tools. Add more only when you hit concrete failures.

**2. Tool docstrings are prompts**
The LLM decides which tool to use based entirely on its name and docstring. A bad docstring = wrong tool choices. A good docstring = reliable routing.

```python
# Bad docstring
@tool
def search(q: str) -> list: ...

# Good docstring
@tool
def search_product_catalog(
    query: str,
    max_price: float = 0
) -> list[dict]:
    """
    Search the product catalog by keyword and optionally filter by price.
    
    Use this tool when the customer asks about:
    - Available products or what we sell
    - Price of a specific product
    - Whether a product is in stock
    - Product features or descriptions
    
    Do NOT use for order status — use get_order_status instead.
    Returns: list of matching products with id, name, price, stock.
    """
```

**3. Max iterations**
Always set a maximum number of loop iterations. Without it, a confused agent loops forever burning API credits.

```python
# LangGraph's create_react_agent accepts recursion_limit
app = create_react_agent(model, tools)
result = app.invoke(input, config={"recursion_limit": 15})
```

**4. Idempotent tools**
Design read tools as pure functions (same input = same output, no side effects). Reserve side effects for write tools, and wrap those with human approval when possible.

**5. Error handling in tools**
Tools should NEVER raise exceptions — they should return error strings. Exceptions crash the graph; error strings let the LLM recover gracefully.

```python
@tool
def get_order(order_id: str) -> dict:
    try:
        return db.get_order(order_id)
    except OrderNotFound:
        return {"error": f"Order {order_id} not found. Check the ID."}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
```

---

## 8. Memory — All Four Types

### The Problem

Stateless LLMs remember nothing between sessions. Each call starts fresh. To build agents that learn, remember users, and maintain context — you need explicit memory management.

### Type 1: In-Context Memory (Working Memory)

**What it is:** Everything currently in the model's context window. The conversation so far, retrieved documents, tool results, system instructions.

**Capacity:** Limited by context window (128k–2M tokens for modern models).

**Lifetime:** Current invocation only. Gone when the session ends.

**Implementation:** Just the `messages` list in your LangGraph state.

```python
# In-context memory is implicit — it's your messages list
state["messages"] = [
    SystemMessage("You are a support agent."),
    HumanMessage("Where is my order?"),
    AIMessage("Let me check that."),
    ToolMessage("Order status: shipped"),
    AIMessage("Your order is shipped!"),
]
```

**When it fills up:** Use a summarisation node that compresses old messages:
```python
def summarise_history(state: AgentState) -> dict:
    if len(state["messages"]) > 20:
        old_messages = state["messages"][:-5]  # keep last 5
        summary = llm.invoke(f"Summarise: {old_messages}")
        return {"messages": [SystemMessage(f"History summary: {summary}")] + state["messages"][-5:]}
    return {}
```

### Type 2: Episodic Memory (Session History)

**What it is:** Past conversation turns stored in a database, loaded on demand.

**Capacity:** Unlimited (disk storage).

**Lifetime:** Persistent across sessions.

**Implementation:** LangGraph checkpointers.

```python
# Setup
checkpointer = SqliteSaver.from_conn_string("memory.db")
app = graph.compile(checkpointer=checkpointer)

# Thread ID = conversation ID = what separates users
config = {"configurable": {"thread_id": "user-42-session-1"}}

# Turn 1
app.invoke({"messages": [HumanMessage("My name is Alice")]}, config=config)

# Turn 2 — same thread_id, picks up where we left off
app.invoke({"messages": [HumanMessage("What's my name?")]}, config=config)
# Agent knows: "Your name is Alice" — from checkpointed history
```

### Type 3: Semantic Memory (Long-Term Facts)

**What it is:** Persistent facts, preferences, learned information stored in a vector store or key-value store. Retrieved by similarity search when relevant.

**Capacity:** Unlimited.

**Lifetime:** Permanent until explicitly deleted.

**Implementation:** LangGraph Store

```python
from langgraph.store.memory import InMemoryStore  # or PostgresStore

store = InMemoryStore()

# Save a fact (cross-thread, cross-session)
await store.aput(
    namespace=("user_profile", user_id),
    key="coding_preference",
    value={"language": "Python", "style": "concise", "dislikes": "Java"}
)

# Search relevant facts by semantic similarity
facts = await store.asearch(
    namespace=("user_profile", user_id),
    query="programming language preferences",
)

# In agent: inject relevant facts into system prompt
relevant_facts = "\n".join([f["value"] for f in facts])
system = f"User preferences:\n{relevant_facts}\n\nYou are a support agent."
```

### Type 4: Procedural Memory (Behavioral Patterns)

**What it is:** HOW to do things — encoded as system prompts, few-shot examples, or fine-tuned model weights.

**Examples:**
- "Always greet users by name"
- "When expense > $500, always escalate"
- "Format all code responses as Python"

**Implementation options:**

**System prompt (simplest):**
```python
SYSTEM = """
You are a support agent. Follow these rules:
1. Always start with "Hello {customer_name},"
2. For damaged item reports, immediately create a high-priority ticket
3. Never promise refunds — escalate to human agents
"""
```

**Few-shot examples in prompt (better for complex patterns):**
```python
SYSTEM = """
You are a support agent. Here are examples of correct responses:

Customer: "My package never arrived"
Agent: [calls get_order_status] [creates ticket with priority=high]
Response: "I've checked order ORD-1234 — it's been in transit for 15 days.
           I've created ticket TKT-0099 (high priority) for your missing package..."

Customer: "What products do you have?"
Agent: [calls search_products with empty query]
Response: "Here's what we currently carry: ..."
"""
```

**Fine-tuning (most reliable, most expensive):** Train the model on your specific interaction patterns. Reserved for production systems at scale.

### Memory Strategy for Production

```
User Input
    │
    ├── Load from episodic memory (checkpointer) → recent conversation turns
    │
    ├── Search semantic memory (Store) → relevant user facts/preferences
    │
    ├── Retrieve from RAG (vector store) → relevant knowledge base documents
    │
    └── All combined in context → LLM generates response
                                        │
                                        ├── Save turn to checkpointer (episodic)
                                        │
                                        └── Extract + save new facts to Store (semantic)
```

---

## 9. Tools & Actions

### Tool Anatomy

Every LangChain tool has:
- **Name:** used by LLM to call it (snake_case, descriptive)
- **Description / docstring:** LLM reads this to decide WHEN to call it
- **Input schema:** Pydantic model the LLM must fill in
- **Function body:** actual Python code that runs
- **Return type:** what comes back to the LLM (always serialize to string)

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query:       str   = Field(description="Keyword to search for")
    category:    str   = Field(default="", description="Optional: 'Electronics', 'Office', etc.")
    max_price:   float = Field(default=0, description="Max price in USD. 0 = no limit.")
    in_stock:    bool  = Field(default=False, description="Only return items in stock")

@tool("search_product_catalog", args_schema=SearchInput)
def search_products(query: str, category: str = "", max_price: float = 0, in_stock: bool = False) -> str:
    """
    Search the product catalog. Use this when customers ask about:
    - What products we carry
    - Product prices and availability
    - Products in a specific category
    
    Returns: JSON list of matching products.
    Does NOT use for order status — use get_order_status for that.
    """
    # ... implementation
    return json.dumps(results)
```

### Tool Categories and Considerations

#### Read tools (safe, idempotent)
```python
@tool
def get_database_record(id: str) -> dict:
    """Retrieve a record. Safe to call multiple times — read-only."""
    return db.get(id)
```

#### Write tools (side effects — needs care)
```python
@tool
def send_customer_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a customer.
    ⚠️ IRREVERSIBLE: verify details before calling.
    Only use when explicitly asked by the user.
    """
    # In production: add human approval before this executes
    email_client.send(to, subject, body)
    return f"Email sent to {to}"
```

Write tools with irreversible effects should have a human-in-the-loop interrupt before execution.

#### Computation tools (deterministic)
```python
@tool
def calculate_tax(amount: float, rate: float) -> float:
    """Calculate tax. More reliable than LLM math."""
    return round(amount * rate, 2)
```

Always use tools for math. LLMs hallucinate arithmetic.

#### External API tools
```python
@tool
def web_search(query: str) -> str:
    """Search the web for current information after LLM training cutoff."""
    results = tavily_client.search(query)
    return format_results(results)
```

### ToolNode — The Standard Executor

`ToolNode` from `langgraph.prebuilt` is the standard way to execute tools in a LangGraph graph:

```python
from langgraph.prebuilt import ToolNode

tools = [search_products, get_order, create_ticket]
tool_node = ToolNode(tools)

# In your graph:
builder.add_node("tools", tool_node)

# ToolNode does:
# 1. Reads the last AIMessage.tool_calls from state
# 2. Matches each tool_call.name to a tool in the list
# 3. Calls the tool with tool_call.args
# 4. Returns ToolMessages with results → appended to state["messages"]
```

### Parallel Tool Execution

Modern LLMs can request multiple tool calls in a single response:

```
AIMessage.tool_calls = [
    {"name": "get_weather", "args": {"city": "NYC"}},
    {"name": "get_weather", "args": {"city": "LA"}},
    {"name": "get_weather", "args": {"city": "Chicago"}},
]
```

`ToolNode` executes these in parallel (using `asyncio.gather`), which reduces latency dramatically for independent tools.

---

## 10. Multi-Agent Systems

### When to Use Multi-Agent

Single agent first — always. Add agents only when you hit:
- **Context limit:** task requires more information than fits in one context window
- **Parallel speedup:** independent subtasks that could run simultaneously
- **Expertise isolation:** a specialist agent genuinely performs better than a generalist
- **Fault isolation:** one agent's failure shouldn't crash the entire system

### Supervisor Pattern

One orchestrator LLM that routes to specialist agents:

```
User: "Research quantum computing and write a Python implementation of Grover's algorithm"
        │
        ▼
   Supervisor LLM
    "This needs research first, then coding."
        │
        ├──► Research Agent → [web search, arxiv] → "Grover's algorithm works by..."
        │
        ├──► Coding Agent → [python_repl, write_file] → "def grovers_algorithm(n):..."
        │
        └── Supervisor: "Combine and format final response"
```

```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

research_agent = create_react_agent(model, [tavily_search, arxiv], name="researcher")
coding_agent   = create_react_agent(model, [python_repl, write_file], name="coder")

supervisor = create_supervisor(
    agents=[research_agent, coding_agent],
    model=model,
    prompt="Route tasks to the most appropriate specialist."
).compile()
```

### Handoff Pattern

Agents explicitly pass control to each other:

```python
from langgraph.types import Command

def triage_agent(state: AgentState) -> Command:
    """Decide which specialist handles this."""
    category = classify_request(state["messages"][-1].content)
    
    if category == "billing":
        return Command(goto="billing_agent", update={"category": "billing"})
    elif category == "technical":
        return Command(goto="tech_agent", update={"category": "technical"})
    else:
        return Command(goto="general_agent")
```

### Parallel Fan-Out

```python
from langgraph.types import Send

def create_research_tasks(state: AgentState) -> list[Send]:
    """Fan out: research each topic in parallel."""
    topics = state["topics_to_research"]
    return [
        Send("research_topic", {"topic": topic, "index": i})
        for i, topic in enumerate(topics)
    ]

# All research tasks run simultaneously
# Results collected when all complete
# Dramatically reduces wall-clock time
```

### Agent Communication Methods

| Method | How | Use When |
|--------|-----|---------|
| Shared state | All agents in same graph, read/write same TypedDict | Tightly coupled, simple pipelines |
| Command handoff | `Command(goto="agent_b", update={...})` | Explicit sequential handoffs |
| Agent as tool | Entire agent wrapped as a `@tool` | Hierarchical, nested architectures |
| LangGraph Store | Cross-thread key-value/vector store | Long-running, cross-session shared knowledge |
| Message queue | Redis/SQS for truly async coordination | High-throughput, distributed deployments |

---

## 11. Hallucination & Reliability

### The Hallucination Taxonomy

Understanding the type of hallucination determines the fix.

#### Intrinsic Hallucination
LLM **contradicts** the provided context.
- Context: "Annual leave: 20 days"
- LLM: "You get 25 days of annual leave"
- **Fix:** Hallucination grader (LLM-as-judge comparing answer to source)

#### Extrinsic Hallucination
LLM **adds information** not in the context (may be true or false).
- Context says nothing about overtime
- LLM: "Overtime is paid at 1.5x rate"
- **Fix:** Constrain prompt ("only answer from context"), structured output with `found_in_policy: bool`

#### Faithfulness Hallucination
Technically correct but **misleading or incomplete**.
- Context: "Leave requires manager approval"
- LLM: "Yes you can take leave" (omits the approval requirement)
- **Fix:** Completeness grader, multi-chunk retrieval, "include all conditions and caveats" instruction

#### Format Hallucination
Right information, **wrong format**.
- Expected: `{"amount": 50.0, "approved": true}`
- Got: `{"amount": "$50", "approved": "yes"}`
- **Fix:** Pydantic structured output with validators

### Mitigation Strategy 1: Structured Output

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class PolicyAnswer(BaseModel):
    found_in_policy: bool   = Field(description="True ONLY if answer is in the provided policy text")
    answer:          str    = Field(description="The answer, or 'Not found' if found_in_policy=False")
    source_section:  str    = Field(description="Which section the answer came from")
    direct_quote:    str    = Field(description="Exact quote from policy supporting the answer")
    
    @field_validator("answer")
    @classmethod
    def cant_fabricate(cls, v: str, info) -> str:
        if not info.data.get("found_in_policy") and v != "Not found in policy":
            raise ValueError("Must set answer to 'Not found in policy' when found_in_policy=False")
        return v

structured_llm = llm.with_structured_output(PolicyAnswer)
```

### Mitigation Strategy 2: Self-RAG Loop

```
Retrieve → Grade docs → [not relevant] → Rewrite query → Retrieve again
               ↓
         [relevant] → Generate → Grade answer → [hallucination] → Regenerate
                                        ↓
                                   [grounded] → Return to user
```

The self-correction loop catches:
- Wrong retrieval (re-retrieve with rewritten query)
- Answer not grounded in docs (regenerate from same docs)

**Maximum retries:** Always cap at 2-3. After that, return best-effort with a disclaimer.

### Mitigation Strategy 3: LLM-as-Judge (Fact Checking)

```python
class FactCheckResult(BaseModel):
    verdict:     Literal["PASS", "FAIL", "UNCERTAIN"]
    corrections: list[str]  # "Claim X → Actual: Y (from source)"
    unsupported: list[str]  # Claims not in source at all

def fact_check(answer: str, source: str) -> FactCheckResult:
    # Step 1: Extract atomic claims from the answer
    claims = extract_claims(answer)  # ["employees get 20 days", "sick leave is 10 days", ...]
    
    # Step 2: Verify each claim against source
    return judge_llm.with_structured_output(FactCheckResult).invoke(
        f"Source:\n{source}\n\nAnswer:\n{answer}\n\nClaims:\n{claims}\n\nFact-check:"
    )
```

**Why two separate LLM calls?**
The generator tries to be helpful (may rationalise hallucinations). The judge tries to find contradictions (different objective). Same LLM, different prompt = different behaviour.

### Mitigation Strategy 4: Guardrails

**Input guardrails:** Catch jailbreaks, off-topic requests, PII before processing.

```python
class InputGuard(BaseModel):
    is_jailbreak: bool
    is_in_scope:  bool
    risk_level:   Literal["none", "low", "medium", "high"]

def screen_input(user_input: str) -> InputGuard:
    return guard_llm.with_structured_output(InputGuard).invoke(
        f"Classify this input for safety: '{user_input}'"
    )
```

**Output guardrails:** Scan output for PII, toxicity, scope violations before returning.

```python
import re
PII_PATTERNS = {
    "email":    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone":    r'\b(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})\b',
    "ssn":      r'\b\d{3}-\d{2}-\d{4}\b',
}

def redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED:{pii_type.upper()}]", text)
    return text
```

**For production:** Use dedicated safety models (Meta Llama Guard 3, Azure Content Safety API) instead of GPT-4o-mini as the guardrail — they're faster, cheaper, and purpose-built.

### Mitigation Strategy 5: Confidence Scoring

```python
class ConfidentAnswer(BaseModel):
    reasoning:   str                                          # think before committing
    confidence:  Literal["high", "medium", "low", "unknown"]
    answer:      str
    caveats:     list[str]

# Route based on confidence
def routed_answer(question: str) -> str:
    result = structured_llm.invoke(question)
    
    match result.confidence:
        case "high":    return result.answer
        case "medium":  return result.answer + f"\n\n⚠️ Please verify: {result.caveats}"
        case "low":     return f"[Low confidence]\n{result.answer}\nRecommend verifying."
        case "unknown": return "I don't have reliable information. Please consult an expert."
```

### Domain-Specific Hallucination Risks

#### Numbers and Financial Data
**Never** let the LLM generate numbers. Always retrieve from a database or API:
```python
# WRONG — LLM makes up numbers
answer = llm.invoke("What was Q3 revenue?")

# CORRECT — retrieve from DB, LLM only formats
revenue = db.query("SELECT revenue FROM financials WHERE quarter='Q3'")
formatted = llm.invoke(f"The Q3 revenue was ${revenue:,}. Explain this in context.")
```

#### Medical / Legal / Compliance
- Add confidence gating: only answer at ≥0.95 confidence
- Always include "consult a professional" disclaimer
- Log every LLM response for audit trail
- Human review for flagged responses

#### Code Generation
- Test generated code before returning (execute it, catch errors, feed back)
- Self-review step: "What APIs or methods are you uncertain about?"
- RAG against actual library documentation (not LLM training memory)

### The Reliability Hierarchy (from simple to complete)

```
Level 0: Prompt engineering ("only answer from context")
         → Reduces hallucination but doesn't eliminate it

Level 1: Structured output with Pydantic
         → Eliminates format hallucinations, adds source citation

Level 2: RAG grounding
         → Reduces factual hallucinations by providing authoritative context

Level 3: Self-RAG (grade docs + grade answer)
         → Catches retrieval failures and answer-context mismatches

Level 4: LLM-as-judge fact checking
         → Catches specific claim contradictions with source

Level 5: Confidence scoring + routing
         → Routes uncertain answers to humans before they reach users

Level 6: Human-in-the-loop for high-stakes
         → Human reviews before irreversible actions

Level 7: Input/output guardrails + audit logging
         → Catches adversarial inputs, compliance, PII
```

Apply the level appropriate to your risk tolerance and domain.

---

## 12. Production Architecture

### The Full Stack

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND: React / Next.js                                   │
│  - LangGraph JS SDK for streaming events                     │
│  - SSE for token-by-token display                           │
│  - thread_id stored per user session                        │
└──────────────────────────────────────────────────────────────┘
                          │ HTTP / SSE
┌──────────────────────────────────────────────────────────────┐
│  API LAYER: FastAPI + LangGraph Platform                     │
│  - Exposes /invoke and /stream endpoints                     │
│  - Handles auth (JWT / API key)                             │
│  - Rate limiting per user                                    │
│  - Cost tracking per user                                    │
└──────────────────────────────────────────────────────────────┘
                          │
┌──────────────────────────────────────────────────────────────┐
│  AGENT LAYER: LangGraph Compiled Graph                       │
│  - Nodes: LLM calls, tool execution, routing                │
│  - Checkpointer: PostgresSaver (per-user conversation)      │
│  - Store: PostgresStore (cross-session memory)              │
│  - Max retries, timeouts, fallbacks configured              │
└──────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────────┐   ┌──────────────┐  ┌─────────────────┐
│  LLM APIs   │   │  Vector DB   │  │  Tool Services  │
│  OpenAI     │   │  Pinecone /  │  │  MCP Servers    │
│  Anthropic  │   │  pgvector    │  │  REST APIs      │
│  (with      │   │  (RAG)       │  │  Databases      │
│  fallback)  │   │              │  │                 │
└─────────────┘   └──────────────┘  └─────────────────┘
                          │
┌──────────────────────────────────────────────────────────────┐
│  OBSERVABILITY: LangSmith / Langfuse                         │
│  - Traces every LLM call, tool invocation, token count      │
│  - Evaluation datasets, regression testing                  │
│  - Production dashboards, alert on error rates             │
└──────────────────────────────────────────────────────────────┘
```

### Serving the Agent

#### Option A: LangGraph Platform (recommended)

```python
# Deploy your compiled graph to LangGraph Platform
# It handles:
# - REST API with /runs/invoke and /runs/stream
# - Background jobs for long-running tasks
# - Checkpointer management
# - Horizontal scaling
# - Auth integration

# In your graph file, just return the compiled graph:
app = graph.compile(checkpointer=checkpointer)
# Platform picks this up automatically
```

#### Option B: FastAPI (DIY)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

api = FastAPI()

@api.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.user_id}}
    
    async def event_stream():
        async for event in app.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### Environment Setup

```bash
# Core
pip install langchain langchain-openai langchain-anthropic
pip install langgraph langgraph-checkpoint-sqlite

# RAG
pip install langchain-chroma chromadb langchain-community

# MCP
pip install mcp langchain-mcp-adapters

# Serving
pip install fastapi uvicorn python-dotenv

# Observability
pip install langsmith

# Environment variables
export OPENAI_API_KEY="sk-..."
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="ls__..."
export LANGCHAIN_PROJECT="my-agent"
```

### Observability with LangSmith

Set `LANGCHAIN_TRACING_V2=true` and every LLM call, tool invocation, and graph step is automatically traced to LangSmith. No code changes required.

What you get:
- Full input/output for every LLM call
- Token counts and cost per call
- Latency for every node
- Error traces with full context
- The ability to replay any trace as a test case

**Critical for debugging agents.** You cannot effectively debug a multi-step agent without traces.

### Cost Management

```python
# Use cheaper models for simple tasks
routing_llm    = ChatOpenAI(model="gpt-4o-mini")   # classification, routing
grading_llm    = ChatOpenAI(model="gpt-4o-mini")   # doc/answer grading
generation_llm = ChatOpenAI(model="gpt-4o")         # final answer generation

# Set max_tokens to prevent runaway responses
llm = ChatOpenAI(model="gpt-4o", max_tokens=500)

# Cache identical LLM calls (saves cost on repeated questions)
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
set_llm_cache(SQLiteCache(database_path="llm_cache.db"))

# Track cost in LangSmith or manually
from langchain_community.callbacks import get_openai_callback
with get_openai_callback() as cb:
    result = chain.invoke(input)
    print(f"Total cost: ${cb.total_cost:.4f}, Tokens: {cb.total_tokens}")
```

### Recommended Stack by Scale

| Scale | LLM | Orchestration | Vector DB | Memory | Observability |
|-------|-----|--------------|-----------|--------|---------------|
| Prototype | gpt-4o-mini | LangGraph local | Chroma | MemorySaver | LangSmith (free) |
| Small prod | gpt-4o | LangGraph local | Chroma / FAISS | SqliteSaver | LangSmith |
| Medium prod | gpt-4o + fallback | LangGraph Platform | pgvector | PostgresSaver | LangSmith / Langfuse |
| Large prod | Multi-model | LangGraph Platform | Pinecone / Weaviate | PostgresSaver + Redis | Langfuse self-hosted |

---

## 13. Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An LLM in a loop that decides what actions to take, executes them, observes results, and repeats |
| **Chain** | A linear sequence of operations (prompt → LLM → parser). Has no loop. |
| **Checkpointer** | LangGraph component that saves graph state to a DB after each node. Enables persistent memory. |
| **Chunk** | A small piece of a document produced by a text splitter. Typically 600-1000 characters. |
| **Conditional edge** | A LangGraph edge that calls a router function to decide the next node dynamically. |
| **Context window** | Maximum number of tokens an LLM can process at once (input + output combined). |
| **Cosine similarity** | Measure of angle between two vectors. 1.0 = same direction (similar meaning). Used for retrieval. |
| **Embedding** | Dense vector representation of text. Similar texts have similar vectors. |
| **Extrinsic hallucination** | LLM adds information not present in the provided context |
| **FastMCP** | High-level Python SDK for building MCP servers with decorator syntax |
| **Graph** | In LangGraph: a directed graph of nodes and edges representing agent logic |
| **HyDE** | Hypothetical Document Embeddings. Generate a hypothetical answer, embed it, use it to search. |
| **Intrinsic hallucination** | LLM contradicts information present in the provided context |
| **LCEL** | LangChain Expression Language. The `|` pipe syntax for composing Runnables. |
| **LLM** | Large Language Model. A neural network that generates text by predicting next tokens. |
| **MCP** | Model Context Protocol. Open standard for AI model ↔ tool communication. |
| **MMR** | Max Marginal Relevance. Retrieval that balances relevance with diversity to avoid redundant results. |
| **Node** | In LangGraph: a Python function that receives state and returns a partial state update. |
| **Operator.add** | Python's addition operator used as a LangGraph reducer to append lists rather than replace them. |
| **Partial state update** | A node returns only the keys it changed, not the full state. LangGraph merges it. |
| **Prompt injection** | An attack where user input tries to override the system prompt/instructions. |
| **RAG** | Retrieval Augmented Generation. Fetch relevant documents at query time, inject as LLM context. |
| **ReAct** | Reason + Act. Agent pattern where LLM alternates between reasoning and tool calls. |
| **Reducer** | Function that merges a partial update into existing state. `operator.add` for list appending. |
| **Runnable** | LangChain's universal interface. Every component has `.invoke()`, `.stream()`, `.batch()`. |
| **Self-RAG** | LLM grades its own retrieval and generation quality; retries if insufficient. |
| **State** | In LangGraph: a TypedDict that flows through every node. The agent's working memory. |
| **Structured output** | Using `.with_structured_output(PydanticModel)` to get typed objects from LLM instead of text. |
| **Temperature** | LLM randomness. 0 = deterministic. >0 = creative. Use 0 for tool calling and grading. |
| **Thread ID** | Identifier for a conversation. Same thread_id = same conversation history from checkpointer. |
| **Token** | Smallest unit of text an LLM processes. Roughly 3/4 of a word. |
| **Tool** | A Python function an LLM can request to execute. Returns result back to LLM. |
| **ToolNode** | LangGraph prebuilt node that executes tool calls from the last AIMessage. |
| **Vector store** | Database optimised for storing and searching embedding vectors. |

---

*This document covers everything needed to build production agentic AI systems. See the companion projects:*
- *`01_mcp_project/` — MCP + LangGraph customer support agent*
- *`02_rag_project/` — Agentic RAG knowledge base*
- *`03_hallucination_reliability/` — Reliability patterns with runnable examples*
