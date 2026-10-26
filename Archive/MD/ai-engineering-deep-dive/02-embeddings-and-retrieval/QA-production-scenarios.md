# Module 02 — Q&A + Production Scenarios: Embeddings & Retrieval

---

## Top 30 Interview Questions & Answers

### Q1: You have 500M product embeddings. How do you serve sub-10ms search?

**A:**
```
Architecture:
1. INDEX: IVF + PQ (Product Quantization)
   - 500M vectors × 48 bytes (PQ) = 24 GB (fits in RAM)
   - 10,000 IVF clusters, nprobe=32
   
2. SHARD: 5 shards × 100M vectors each
   - Each shard on separate machine
   - Search all in parallel → merge results
   
3. CACHE: Redis for hot queries
   - Top 10K search queries cached (covers 30% of traffic)
   
4. REPLICATE: 3 replicas per shard
   - Handle 50K QPS with round-robin

Latency breakdown:
  Embed query:     2ms (local GPU model)
  Shard routing:   0.5ms
  IVF+PQ search:   3ms (per shard, parallel)
  Merge results:   0.5ms
  Re-rank top 20:  3ms (cross-encoder on GPU)
  Total:           ~9ms ✓
  
Cost: 15 machines × $500/mo = $7,500/month for 500M vectors at 50K QPS
```

---

### Q2: Your embedding model puts "bank" (financial) and "bank" (river) close together. How do you fix this?

**A:**
```python
# Solution 1: Contextual embedding (best)
# Instead of embedding the word alone, embed it WITH context
embeddings = {
    "bad":  embed("bank"),                           # Ambiguous
    "good": embed("I deposited money at the bank"),  # Clear context
}

# Solution 2: Prepend category/context to text before embedding
def embed_with_context(text: str, category: str = None) -> list[float]:
    if category:
        text = f"[{category}] {text}"
    return embed(text)

# embed_with_context("bank", "finance")  → finance vector
# embed_with_context("bank", "geography") → geography vector

# Solution 3: Use a larger chunk size
# Instead of embedding single words, embed sentences or paragraphs
# "The bank offers 3% interest on savings" → clearly financial

# Solution 4: Fine-tune the embedding model
# Train on your domain-specific data where "bank" has clear meaning
```

---

### Q3: Your RAG system retrieves 5 documents but the answer is in document 6. How do you improve recall?

**A:**
```python
# 7 techniques to improve retrieval recall:

# 1. QUERY EXPANSION — generate multiple search queries
async def multi_query_search(question: str, top_k: int = 5):
    queries = await generate_query_variants(question, n=4)
    # "refund policy" → ["return policy", "money back guarantee", 
    #                     "how to get a refund", "cancellation and refund"]
    all_results = []
    for q in queries:
        results = await vector_search(q, top_k=top_k)
        all_results.extend(results)
    return deduplicate_and_rank(all_results)[:top_k]

# 2. HYBRID SEARCH — combine vector + keyword
# Vector search catches semantic matches
# BM25 catches exact keyword matches
# RRF merges them

# 3. INCREASE TOP-K — retrieve more, re-rank later
# Retrieve 50, re-rank to 5 (cross-encoder is more accurate)

# 4. SMALLER CHUNKS — split documents into smaller pieces
# 1000-char chunks might miss → try 300-char chunks with overlap

# 5. HYPOTHETICAL DOCUMENT EMBEDDING (HyDE)
# Generate a hypothetical answer, embed THAT instead of the question

# 6. RECURSIVE RETRIEVAL — retrieve, check, retrieve more
async def recursive_retrieve(question: str, max_rounds: int = 3):
    context = []
    for round in range(max_rounds):
        results = await search(question, exclude=context, top_k=3)
        context.extend(results)
        
        # Check if we have enough to answer
        can_answer = await check_sufficiency(question, context)
        if can_answer:
            break
    return context

# 7. FINE-TUNE EMBEDDING MODEL on your domain
# Train on (query, relevant_document) pairs from your data
```

---

### Q4: How do you handle real-time updates to a vector index serving production traffic?

**A:**
```python
class LiveUpdateableVectorIndex:
    """
    Strategy: Write to staging index, swap atomically.
    
    Pattern: Blue-Green indexing
    
    Active (serving):  index_v1 (read-only, fast)
    Staging (building): index_v2 (accumulating updates)
    
    Every N minutes or M updates:
      1. Build optimized index from staging
      2. Atomic swap: index_v2 becomes active
      3. Old index_v1 kept for rollback (30 min TTL)
    """
    
    def __init__(self):
        self.active_index = None       # Serving queries
        self.staging_buffer = []       # Accumulating updates
        self.write_lock = asyncio.Lock()
    
    async def search(self, query_vector, top_k=10):
        """Always reads from active index (no locks needed)."""
        results = self.active_index.search(query_vector, top_k)
        
        # Also search staging buffer for very recent updates
        if self.staging_buffer:
            buffer_results = brute_force_search(
                query_vector, self.staging_buffer, top_k
            )
            results = merge_results(results, buffer_results, top_k)
        
        return results
    
    async def upsert(self, doc_id: str, vector: list, metadata: dict):
        """Add to staging buffer (fast, no index rebuild)."""
        async with self.write_lock:
            self.staging_buffer.append({
                "id": doc_id, "vector": vector, "metadata": metadata
            })
        
        # Trigger rebuild if buffer is large enough
        if len(self.staging_buffer) > 1000:
            asyncio.create_task(self.rebuild_index())
    
    async def rebuild_index(self):
        """Build new optimized index and swap atomically."""
        async with self.write_lock:
            buffer = self.staging_buffer.copy()
            self.staging_buffer.clear()
        
        # Build new index (can take minutes, doesn't block reads)
        new_index = build_hnsw_index(
            existing=self.active_index,
            new_vectors=buffer
        )
        
        # Atomic swap
        old_index = self.active_index
        self.active_index = new_index
        
        # Cleanup old index after 30 minutes (rollback window)
        asyncio.get_event_loop().call_later(1800, old_index.cleanup)
```

---

### Q5: Compare vector database options for a startup vs. enterprise.

**A:**
```
STARTUP (< 1M vectors, team of 3-5):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommended: pgvector (PostgreSQL extension)

Why:
✓ You already use PostgreSQL
✓ Zero new infrastructure
✓ SQL filtering with vector search
✓ ACID transactions
✓ Your team knows SQL
✓ Free and open source

When to upgrade: > 5M vectors or need < 5ms latency

---

GROWTH (1M-100M vectors, team of 10-20):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommended: Qdrant (self-hosted)

Why:
✓ Written in Rust (fast)
✓ Rich filtering (pre-filter + post-filter)
✓ On-disk index (handles > RAM)
✓ Built-in replication
✓ Open source, no vendor lock-in
✓ $200-2000/month on own servers

Alternative: Weaviate (better for multi-modal)

---

ENTERPRISE (100M+ vectors, dedicated infra team):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommended: Pinecone (managed) or Milvus (self-hosted)

Pinecone:
✓ Fully managed (zero ops)
✓ Serverless pricing
✓ Handles billions of vectors
✗ Vendor lock-in
✗ Expensive at scale ($1000+/month)

Milvus:
✓ Battle-tested at scale (Alibaba, eBay)
✓ Distributed architecture
✓ GPU-accelerated search
✓ Open source
✗ Complex to operate
✗ Needs dedicated DevOps
```

---

### Q6: How do you measure vector search quality in production?

**A:**
```python
class RetrievalQualityMonitor:
    """
    Continuously measure retrieval quality.
    
    Key metrics:
    1. Recall@K: Are we finding the relevant documents?
    2. NDCG@K: Are the relevant documents ranked correctly?
    3. MRR: How high is the first relevant result?
    4. Latency: How fast is search?
    """
    
    async def measure_recall_at_k(self, test_set: list[dict], k: int = 10) -> float:
        """
        For each test query with known relevant docs,
        check how many we actually retrieve.
        """
        recalls = []
        for test in test_set:
            query = test["query"]
            expected_docs = set(test["relevant_doc_ids"])
            
            results = await self.search(query, top_k=k)
            retrieved_docs = set(r.id for r in results)
            
            recall = len(expected_docs & retrieved_docs) / len(expected_docs)
            recalls.append(recall)
        
        return sum(recalls) / len(recalls)
    
    async def online_quality_check(self):
        """Run on production traffic (sampled)."""
        samples = self.sample_production_queries(n=100)
        
        for query, response, sources in samples:
            # Check: Is the answer actually IN the retrieved sources?
            grounded = await self.llm_judge_grounding(response, sources)
            
            # Check: Are there better documents we missed?
            all_relevant = await self.exhaustive_search(query, top_k=100)
            top_10_retrieved = set(s.id for s in sources)
            top_10_exhaustive = set(r.id for r in all_relevant[:10])
            
            missed = top_10_exhaustive - top_10_retrieved
            if missed:
                logger.warning(f"Missed {len(missed)} relevant docs for: {query[:50]}")
```

---

### Q7: Your embedding pipeline processes 10M documents/day. Design it.

**A:**
```python
class HighThroughputEmbeddingPipeline:
    """
    Process 10M documents/day = ~115 docs/second sustained.
    
    Architecture:
    - Kafka queue for documents
    - N embedding workers (GPU or API)
    - Batch processing for efficiency
    - Checkpointing for fault tolerance
    """
    
    async def run(self):
        consumer = KafkaConsumer("documents-to-embed", group_id="embedding-workers")
        
        batch = []
        batch_deadline = time.time() + 5  # Flush every 5 seconds
        
        async for message in consumer:
            doc = json.loads(message.value)
            batch.append(doc)
            
            # Flush when batch is full OR deadline reached
            if len(batch) >= 2048 or time.time() > batch_deadline:
                try:
                    await self.process_batch(batch)
                    await consumer.commit()  # Checkpoint
                except Exception as e:
                    logger.error(f"Batch failed: {e}")
                    # Messages will be re-consumed on restart
                
                batch = []
                batch_deadline = time.time() + 5
    
    async def process_batch(self, docs: list):
        """Process a batch of documents."""
        
        # 1. Chunk all documents
        all_chunks = []
        for doc in docs:
            chunks = self.chunker.chunk(doc["text"], doc["type"])
            for chunk in chunks:
                chunk["doc_id"] = doc["id"]
                chunk["metadata"] = doc["metadata"]
            all_chunks.extend(chunks)
        
        # 2. Batch embed (2048 texts per API call)
        texts = [c["text"] for c in all_chunks]
        embeddings = await self.embed_batch(texts)
        
        # 3. Bulk upsert to vector store
        points = [
            {"id": f"{c['doc_id']}_{i}", "vector": emb, "payload": c["metadata"]}
            for i, (c, emb) in enumerate(zip(all_chunks, embeddings))
        ]
        await self.vector_store.bulk_upsert(points)
        
        logger.info(f"Processed {len(docs)} docs → {len(all_chunks)} chunks")
    
    # Throughput calculation:
    # OpenAI text-embedding-3-small:
    #   Rate limit: 5,000 RPM, 5M tokens/min (Tier 5)
    #   Batch size: 2048 texts per request
    #   Throughput: 5000 × 2048 = 10.24M texts/min
    #   
    # For 10M docs/day ÷ ~5 chunks/doc = 50M chunks
    #   50M ÷ 10.24M/min = 4.9 minutes
    #   
    # But you're bottlenecked by rate limits, so add:
    #   - Multiple API keys (round-robin)
    #   - Or self-host: sentence-transformers on 4× A100 → unlimited throughput
```

---

## Production Scenario: Multi-Tenant Vector Search (SaaS)

```python
class MultiTenantVectorSearch:
    """
    SaaS product where each customer has their own document collection.
    
    Challenge: 1000 tenants, 1K-10M docs each, strict data isolation.
    
    Options:
    1. Separate collection per tenant (simple but wasteful)
    2. Shared collection with tenant_id filter (efficient but risky)
    3. Hybrid: shared index + payload-based isolation (best)
    """
    
    # Option 3: Shared infrastructure, logical isolation
    
    async def create_tenant(self, tenant_id: str):
        """Initialize a new tenant's namespace."""
        # No new collection — just metadata
        await self.metadata_store.create_tenant(tenant_id, {
            "created_at": datetime.utcnow(),
            "doc_count": 0,
            "embedding_model": "text-embedding-3-small",
            "quota_docs": 100_000,  # Per-tenant limit
        })
    
    async def add_document(self, tenant_id: str, doc: Document):
        """Add document with tenant isolation."""
        # Check quota
        tenant = await self.metadata_store.get_tenant(tenant_id)
        if tenant["doc_count"] >= tenant["quota_docs"]:
            raise QuotaExceeded(f"Tenant {tenant_id} quota: {tenant['quota_docs']}")
        
        chunks = self.chunk(doc.text)
        embeddings = await self.embed(chunks)
        
        # Store with tenant_id in payload (for filtering)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            await self.vector_store.upsert(
                collection="shared_index",
                id=f"{tenant_id}_{doc.id}_{i}",
                vector=emb,
                payload={
                    "tenant_id": tenant_id,  # CRITICAL: isolation key
                    "text": chunk,
                    "doc_id": doc.id,
                    **doc.metadata
                }
            )
    
    async def search(self, tenant_id: str, query: str, top_k: int = 10):
        """Search ONLY within tenant's documents."""
        query_emb = await self.embed([query])
        
        results = await self.vector_store.search(
            collection="shared_index",
            vector=query_emb[0],
            filter={
                "must": [
                    {"key": "tenant_id", "match": {"value": tenant_id}}
                ]
            },
            top_k=top_k
        )
        
        return results
    
    # Security: ALWAYS filter by tenant_id
    # Never return documents from other tenants
    # Audit log every cross-tenant access attempt
```

---

## Capacity Planning Cheat Sheet

```
Documents     Vectors    Storage      Index Type        Infra           Monthly Cost
─────────     ───────    ───────      ──────────        ─────           ────────────
1K            5K         30 MB        NumPy flat        Single app      $0
10K           50K        300 MB       pgvector          Existing PG     $0
100K          500K       3 GB         pgvector/HNSW     Existing PG     $10-50
1M            5M         30 GB        Qdrant HNSW       1 server        $200-500
10M           50M        300 GB       Qdrant cluster    3 servers       $1,500-3K
100M          500M       3 TB         IVF+PQ sharded    10 servers      $5K-15K
1B            5B         6 TB (PQ)    IVF+PQ sharded    50+ servers     $25K-100K

Assumptions: 1536 dims, float16, 5 chunks per doc, HNSW M=16
```
