# A1 — Embeddings, Vector Databases, and RAG Foundations (Prerequisite)

## Learning objectives

Convert text to **vectors**, store them in a **vector database**, retrieve the most relevant chunks for a query, and build a **basic RAG pipeline** — the foundation every later module depends on.

> **Read this before module 01** if you have never used embeddings or vector search.

---

## Why this matters (SWE mental model)

| Traditional search | Vector / semantic search |
|--------------------|------------------------|
| Keyword match (SQL `LIKE`, Elasticsearch BM25) | Meaning match via **cosine similarity** of dense vectors |
| Exact: "refund policy" ≠ "return guidelines" | Semantic: both match because vectors are close |
| Schema required | Works on unstructured text, images, code |

**RAG** = Retrieval-Augmented Generation: fetch relevant chunks → inject into LLM prompt → generate grounded answer. It is the **most common production pattern** for enterprise AI apps.

---

## 1 — Embeddings

### What is an embedding?

A function \(E\) that maps text to a fixed-size vector:

\[
E(\text{"refund policy"}) \rightarrow [0.12, -0.34, 0.56, \ldots] \in \mathbb{R}^d
\]

Typical \(d\): 384 (MiniLM), 1536 (OpenAI `text-embedding-3-small`), 3072 (`text-embedding-3-large`).

### Calling an embedding API

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vec = embeddings.embed_query("What is the refund policy?")
print(len(vec))  # 1536
```

### Distance / similarity metrics

| Metric | Formula | When |
|--------|---------|------|
| **Cosine similarity** | \(\frac{a \cdot b}{\|a\|\|b\|}\) | Default for normalized embeddings |
| **Euclidean (L2)** | \(\|a - b\|_2\) | When magnitude matters |
| **Dot product** | \(a \cdot b\) | Equivalent to cosine when vectors are unit-normalized |

Most vector DBs normalize by default → **cosine ≈ dot product**.

### Choosing an embedding model

| Model | Dimensions | Speed | Quality | Cost |
|-------|-----------|-------|---------|------|
| `text-embedding-3-small` | 1536 | Fast | Good | $0.02/1M tokens |
| `text-embedding-3-large` | 3072 | Slower | Better | $0.13/1M tokens |
| Sentence-Transformers (local) | 384–768 | CPU/GPU | Good | Free |
| Cohere `embed-v3` | 1024 | Fast | Strong | Paid |

**Rule:** use the **same model** at ingest time and query time — mixing models breaks similarity.

---

## 2 — Chunking documents

### Why chunk?

LLM context windows have limits. A 50-page PDF won't fit in a single prompt. Instead:

1. **Split** document into chunks (~200–1000 tokens each).
2. **Embed** each chunk.
3. **Retrieve** relevant chunks at query time.

### Chunking strategies

| Strategy | How | Best for |
|----------|-----|----------|
| **Fixed-size** | Every N tokens with M overlap | Simple, predictable |
| **Recursive character** | Split by `\n\n`, then `\n`, then sentence | Prose documents |
| **Semantic** | Split where topic shifts (embedding delta) | Long mixed-topic docs |
| **Document-aware** | Respect headers, tables, code blocks | Structured docs (Markdown, HTML) |

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # tokens (approx)
    chunk_overlap=50,     # overlap keeps context at boundaries
    separators=["\n\n", "\n", ". ", " "],
)
chunks = splitter.split_text(long_document)
```

### Chunking math

With chunk size \(C\) tokens, overlap \(O\), document length \(D\):

\[
\text{num\_chunks} \approx \frac{D - O}{C - O}
\]

**Trade-off:** smaller chunks → more precise retrieval but less context per chunk. Larger chunks → more context but noisier matches.

### Metadata

Always store with each chunk:
- `source` (filename, URL)
- `page` or `section` (for citations)
- `doc_type` (for filtered retrieval / ACL)
- `chunk_index` (reconstruct order)

---

## 3 — Vector databases

### What they do

Store vectors + metadata → run approximate nearest neighbor (ANN) search in milliseconds.

### Common vector DBs

| DB | Type | Best for |
|----|------|----------|
| **FAISS** | Library (in-memory) | Prototyping, small datasets |
| **Qdrant** | Managed / self-hosted | Production, filtering, payloads |
| **Pinecone** | Fully managed SaaS | Zero-ops, fast start |
| **pgvector** | Postgres extension | Already running Postgres |
| **Weaviate** | Managed / self-hosted | Hybrid search built-in |
| **ChromaDB** | Library / server | Local dev, lightweight |
| **Databricks Vector Search** | Managed (Delta Sync) | Enterprise lakehouse (module 14) |

### Indexing algorithms (intuition)

| Algorithm | Idea |
|-----------|------|
| **HNSW** (Hierarchical Navigable Small World) | Graph layers — fast, most popular |
| **IVF** (Inverted File) | Cluster centroids → search subset |
| **PQ** (Product Quantization) | Compress vectors → less memory |

You don't need to implement these — know that **HNSW** is the default for most vector DBs, offers O(log n) search, and trades memory for speed.

### Minimal Qdrant example

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(":memory:")  # local; use URL for cloud
client.create_collection(
    "docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Upsert
points = [
    PointStruct(id=i, vector=embeddings.embed_query(chunk), payload={"text": chunk, "source": "policy.pdf"})
    for i, chunk in enumerate(chunks)
]
client.upsert("docs", points)

# Search
query_vec = embeddings.embed_query("refund policy")
hits = client.search("docs", query_vector=query_vec, limit=5)
for hit in hits:
    print(hit.score, hit.payload["text"][:80])
```

### LangChain vector store abstraction

```python
from langchain_qdrant import QdrantVectorStore

vectorstore = QdrantVectorStore.from_texts(
    texts=chunks,
    embedding=embeddings,
    collection_name="docs",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
docs = retriever.invoke("What is the refund policy?")
```

---

## 4 — Basic RAG pipeline

### Architecture

```mermaid
flowchart LR
  Q[User query] --> E1[Embed query]
  E1 --> VS[(Vector DB)]
  VS --> C[Top-k chunks]
  C --> P[Build prompt]
  P --> LLM[Model]
  LLM --> A[Answer]
```

### Minimal implementation

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

template = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the context below. If unsure, say 'I don't know'.\n\nContext:\n{context}"),
    ("human", "{question}"),
])

def rag(question: str) -> str:
    docs = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    chain = template | llm
    return chain.invoke({"context": context, "question": question}).content

print(rag("What is the refund window?"))
```

### What can go wrong

| Failure mode | Symptom | Fix |
|-------------|---------|-----|
| **Wrong chunks retrieved** | Answer about wrong topic | Better chunking, reranker (module 12) |
| **Hallucination** | Answer not in context — model makes up facts not supported by retrieved chunks | **Grounding** guardrail: verify each claim cites a source chunk (modules 05–06), faithfulness eval metric (08) |
| **Missing docs** | "I don't know" on valid question | Ingestion gap, hybrid search |
| **Stale data** | Outdated answer | Ingest pipeline freshness SLA |
| **Prompt injection in docs** | Malicious document contains hidden text like "ignore instructions" and the model follows it (**indirect injection / XPIA**) | Input/output rails (module 05), red team (10) |

---

## 5 — Hybrid search

Combine **keyword (BM25)** + **semantic (vector)** for better recall:

\[
\text{score\_final} = \alpha \cdot \text{score\_bm25} + (1-\alpha) \cdot \text{score\_vector}
\]

Typical \(\alpha = 0.3\)–\(0.5\). Tune on your eval dataset (module 08).

```python
# Many vector DBs support hybrid natively
# Qdrant: sparse + dense vectors
# Weaviate: hybrid search API
# Elasticsearch: knn + BM25
```

**When hybrid wins:** domain jargon, IDs, product codes — keywords the embedding model hasn't seen enough.

---

## 6 — Reranking (preview → module 12)

Bi-encoder (embedding search) is fast but coarse. **Cross-encoder reranker** scores each (query, doc) pair more accurately but is slower.

Pipeline: embed → retrieve top-50 → rerank → top-5 → prompt.

```python
# Conceptual — FlashRank or Cohere rerank
reranked = reranker.rerank(query, retrieved_docs, top_n=5)
```

---

## Production notes

### Index sizing and capacity planning

\[
\text{memory} \approx N_{\text{vectors}} \times d \times 4\text{ bytes (float32)} \times 1.5\text{ (HNSW overhead)}
\]

Example: 200k vectors × 1536 dimensions × 4B × 1.5 = ~1.8 GB. Plan for 2x headroom.

### Embedding model migration

When upgrading embedding model (e.g., `text-embedding-3-small` to `text-embedding-3-large`):

1. **Re-embed all documents** with the new model (batch job).
2. Deploy new index alongside old (blue-green).
3. Switch query embedding to new model.
4. Run eval to confirm retrieval quality improved.
5. Decommission old index.

**Never** mix models — queries embedded with model A will not match documents embedded with model B.

### Backup and disaster recovery

| Vector DB | Backup method |
|-----------|---------------|
| Qdrant Cloud | Built-in snapshots; schedule daily |
| Pinecone | Managed; built-in replication |
| pgvector | Standard Postgres backup (pg_dump) |
| FAISS | Serialize to file: `faiss.write_index()` |

### Monitoring retrieval quality

| Metric | How to measure | Action if degraded |
|--------|---------------|-------------------|
| **Recall@k** | Eval dataset with known relevant docs | Increase k, add reranker, improve chunking |
| **Latency p99** | Trace retrieval span | Optimize index (HNSW params), add replica |
| **Empty results** | Log queries with 0 hits | Missing docs or bad query embedding |
| **Stale results** | Compare ingest timestamp vs query time | Fix ingest pipeline lag |

```python
# Log retrieval quality per request
logger.info("retrieval", extra={
    "query_hash": hash(query),
    "num_results": len(hits),
    "top_score": hits[0].score if hits else 0,
    "latency_ms": elapsed_ms,
})
```

---

## Senior pitfalls

| Mistake | Impact |
|---------|--------|
| Different embedding models at ingest vs query | Zero useful results |
| No overlap in chunks | Lost context at boundaries |
| Storing embeddings without metadata | Cannot filter, cite, or debug |
| Not evaluating retrieval | Ship broken RAG; eval says "faithfulness low" but root cause is retrieval |
| Indexing everything (including junk) | Noise in results |

---

## Math summary

| Concept | Formula |
|---------|---------|
| Cosine similarity | \(\cos(\theta) = \frac{a \cdot b}{\|a\|\|b\|}\) |
| Chunk count | \(\approx \frac{D - O}{C - O}\) |
| Hybrid score | \(\alpha \cdot \text{BM25} + (1-\alpha) \cdot \text{vector}\) |
| Embedding cost | \(\frac{N_{\text{tokens}}}{10^6} \cdot p_{\text{embed}}\) |

---

## Practice

1. Embed 3 sentences and compute pairwise cosine similarity by hand (numpy).
2. Chunk a 5-page PDF with `RecursiveCharacterTextSplitter`; inspect boundary quality.
3. Build a minimal RAG over 10 FAQ entries; ask 5 questions and note which chunks are retrieved.
4. Swap embedding model; observe retrieval quality change.

## Production-grade practice

5. **Capacity plan** — calculate memory needed for 500k vectors with `text-embedding-3-large` (d=3072); compare with Qdrant Cloud pricing.
6. **Build an ingest pipeline** — parse 10 PDFs, chunk, embed, upsert to Qdrant with metadata; verify retrieval works on 5 test queries.
7. **Implement retrieval monitoring** — log `num_results`, `top_score`, `latency_ms` for every query; identify queries with 0 results in a 1-hour window.
8. **Run an embedding model migration** — re-embed all docs with a different model; deploy new collection; compare eval scores (context recall) before and after.

---

## Where this connects

| Concept | Used in module |
|---------|---------------|
| Embeddings | 11 (semantic cache), 12 (capstones), 14 (Databricks) |
| Vector DB | 09 (vector memory), 12 (Qdrant), 14 (Vector Search) |
| Basic RAG | 03 (agentic RAG graph), 04 (tracing RAG), 08 (eval) |
| Chunking | 12 (ingestion pipeline) |
| Hybrid search | 12 (HR hybrid RAG) |
| Reranking | 12 (FlashRank in GCP capstone) |

**Next:** [A2-prompt-engineering-patterns.md](./A2-prompt-engineering-patterns.md)
