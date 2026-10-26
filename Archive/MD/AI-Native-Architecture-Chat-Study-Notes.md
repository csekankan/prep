# AI-Native Architecture — Revision Notes (detailed)

Study notes from chat walkthroughs. Written so you can **revise without re-reading the whole thread**.

**Sources:** `AI-Native-Architecture-Notes.md`, Algoroq PDFs (Ch 3–7).

---

## How to use this doc

1. Read **Course map** once.  
2. For exams/design reviews: **Ch2 one turn** + **Ch3 RAG** + **Ch4 PQ/filters** + **§1.3.1 CIs** when talking evals/ship gates.  
3. Deep sections match how we explained in chat (examples, not just bullets).

---

## Course map (7 chapters)

| Ch | Title | Covered in chat |
|----|--------|-----------------|
| 1 | What AI-Native Means | Yes (+ temperature, caching, evals, **confidence intervals §1.3.1**) |
| 2 | Reference Architecture | Yes (+ ACL, cache fingerprint) |
| 3 | RAG | Yes (tutorial + PDF→index) |
| 4 | Vector Search | Yes (4.3–4.9; PQ/int8/binary in depth) |
| 5 | Serving & Inference | Yes (5.1–5.8) |
| 6 | Agents | Not yet |
| 7 | Evals & Ops | Not yet |

**One idea for the whole course:** same input does **not** mean same output. You design for **distributions**, **retrieval**, **ACL**, **measurement**, and **GPU memory** — not just “call the API.”

---

# Chapter 1 — AI-native mindset

## 1.1 Determinism is gone

Normal code: same input → same output.  
LLM: same input → **one sample** from many valid answers.

**What breaks:**

| Old assumption | With LLM | Fix |
|----------------|----------|-----|
| Cache key = hash(input) | Freezes one random answer | Semantic cache + TTL + quality gate |
| Retry fixes bug | New sample | Only if **aleatoric**; else fix prompt/retrieval |
| Unit test proves path | One draw | Eval set + confidence interval |

**Two failure types:**

- **Aleatoric** — bad luck (sampling). Retry *might* help.  
- **Systematic** — bad retrieval, vague prompt. Same wrong answer every retry. **Change input**, don’t burn retries.

**Rule:** cap retries at **1–2**.

## 1.2 Temperature (worked mini-example)

Model has logits for next word after “The weather is”:

| Word | Logit (T=1) |
|------|-------------|
| sunny | high |
| cloudy | medium |

Formula: \(p_i = e^{z_i/T} / \sum e^{z_j/T}\)

- **T = 0.2** → almost always “sunny”.  
- **T = 1.0** → more variety.  
- **T = 0** on API ≠ perfect replay (GPU math).

## 1.3 Evals and judges (plain English)

**Eval** = run many test questions, measure **% good enough**.

**Judge** = who scores “good enough”:

| Judge | Use |
|-------|-----|
| **Programmatic** | JSON schema, exact ID in answer — every PR |
| **Human** | Ship / major model change — golden set |
| **LLM-as-judge** | Nightly trends — **after** you checked it agrees with humans on ~100 examples |

**Four eval sets:** golden, regression (past bugs), adversarial, live replay.

**Chain reliability:** 5 steps × 95% each ≈ **77%** end-to-end. Validator between steps often beats “smarter model.”

**Gate on worst slice, not the mean.** A +2% overall pass rate can hide **−15%** on one tenant, language, or doc type. Ship decisions use **per-slice floors** for slices the business cares about.

### 1.3.1 Confidence intervals (not “conditional interval”)

In chat we kept saying **confidence interval (CI)** — how wide your measured **%** might be wrong because you only tested **n** examples. Evals estimate a **rate** (pass %, recall@k); every dashboard number has a CI whether the UI shows it or not.

**Plain English:** You ran 100 questions; 85 passed → you report **85%**. With only 100 cases, the **true** rate might plausibly be ~78%–92% (95% CI). A “+2% improvement” after a prompt tweak might be **noise**, not a real win.

**Unpaired pass rate (one run, baseline only):**

- Each item pass/fail → **binomial**.  
- Standard error: `SE = √(p(1−p) / n)` where `p` = observed pass rate, `n` = number of items.  
- **95% CI half-width** ≈ `1.96 × SE` (roughly “± points” on the pass rate).

| n cases | ±pts on pass rate (95% CI) at **p ≈ 90%** |
|---------|---------------------------------------------|
| 100     | ±6                                          |
| 1,000   | ±2                                          |

| n cases | ±pts on pass rate (95% CI) at **p ≈ 85%** |
|---------|---------------------------------------------|
| 50      | ±10                                         |
| 100     | ±7                                          |
| 200     | ±5                                          |
| 400     | ±3.5                                        |
| **1,000** | **±2.2**                                  |
| 2,000   | ±1.6                                        |

**Design takeaway:** At **n = 50**, a real drop from **85% → 78%** can look like “within noise.” Teams ship on “+2” — at that size that’s often a **coin flip dressed as a metric**.

**Same idea for RAG — golden set `recall@5`:** If true recall@5 ≈ **0.84**, the 95% CI half-width on the **measured** recall (in percentage points) is:

| n (queries) | ±pp half-width |
|-------------|----------------|
| 50          | ±10.2          |
| 100         | ±7.2           |
| 200         | ±5.1           |
| 500         | ±3.2           |
| **1,000**   | **±2.2**       |
| 2,000       | ±1.6           |

A chunker or fusion tweak worth **~2 points** is **invisible** until you have **roughly n ≥ 500–1,000** labeled queries. Fix retrieval metrics **before** tuning the LLM.

**Pooled vs paired (A/B on evals or retrieval):**

| Approach | What you do | Problem |
|----------|-------------|---------|
| **Pooled** | Run baseline on n items, candidate on **another** n items; compare two averages | Each average has its own ± noise → small true changes hide |
| **Paired** | Run **both** on the **same** n items | Only **discordant** items matter (one passes, other fails) |

**McNemar (paired sign test for pass/fail):** Count flips only.

- `b` = items that were **pass → fail** (regression)  
- `c` = items that were **fail → pass** (improvement)  
- Items that **both pass** or **both fail** add **no** comparison noise.

**Worked example (from course notes):** n = 300, both versions ~85% pass **pooled** → each has ~±4 pts → a **3-point** drop is invisible.

**Paired:** 14 flipped pass→fail, 4 flipped fail→pass. McNemar with continuity correction:

```
(|14 − 4| − 1)² / (14 + 4)  =  81 / 18  =  4.5    > 3.84  →  p < 0.05
```

Same 300 items **can** detect a real regression when you count **flips**, not when you stare at two noisy percentages.

**Three fixes when CI is too wide (order of leverage):**

1. **Paired compare** baseline vs candidate on identical inputs (McNemar on discordant cases).  
2. **Multiple runs per item** (k = 3–5) if temperature > 0 — score pass-rate **per item**; unstable items flag prompt issues, not the change.  
3. **Slice before average** — gate on **slice floors**; oversample rare slices in the suite (see below).

**Slice sizing:** A **5%** slice of a 1,000-item suite is only **50** items → back to the **±10** row. **Stratified oversampling:** every slice you **gate** on should have **hundreds** of items; reweight to production mix only for the **headline** report. The suite is **unrepresentative on purpose** — its job is to catch expensive regressions, not mirror traffic exactly.

**Minimum detectable effect (HLD):** Decide first — e.g. “we must catch a **5-point** drop on any gated slice” — then derive **n per slice** from the tables above (Ch7 goes further into power: α=0.05, 80% power).

**Eval vs unit test (one line):** Unit test = deterministic property of **your** code. Eval = estimate of quality of a **component you often don’t own** (model name stable, behavior not).

## 1.4 Latency and cost

- **TTFT** = time until **first token** (what user feels when streaming).  
- **Total** = through last token.  
- **Agents:** many LLM calls **before** any stream → multi-second spinner.

**Chat cost:** resend full history every turn → cost grows **~quadratically** in turns.  
**Prefix cache:** provider discounts **identical leading bytes** of prompt — use **append-only** history, not sliding window at front.

## 1.5 Four failure modes

Hallucination, prompt injection, model drift, non-reproducibility — all can return **HTTP 200**. Monitor **quality**, not only uptime.

## 1.6 Prefix cache vs response cache (don’t confuse)

### Prefix / KV cache (inside LLM provider or your GPU)

- **What matches:** exact **token ID sequence** from position 0 (not “similar meaning”).  
- **What is stored:** K and V **activations** per layer per token (not model weights).  
- **Your app:** build prompt; send full text; engine reuses math if bytes/tokens match last time.

```
Turn 2 prompt tokens: [system][turn1][turn2]
Turn 3 prompt tokens: [system][turn1][turn2][turn3]
                      ^^^^^^^^^^^^^^^^^^^^^ same prefix → cache hit on that part
```

### Response cache (your Redis)

- **What matches:** hash(tenant + **acl_fingerprint** + question + prompt_version + model).  
- **What is stored:** final **answer string**.  
- Wrong key (`tenant + question` only) → User B gets User A’s finance answer.

---

# Chapter 2 — Reference architecture

## 2.1 Five lanes (what each does)

```
USER → Experience (gateway, SSE)
     → Orchestration (YOUR product: prompt, tools, guards)
     → Intelligence (LLM API, embed, rerank)  +  Knowledge (vector DB, history DB)
     → Trust/Ops wraps all (traces, evals)
```

**Don’t** split into 5 microservices on day one. One orchestrator process is fine early.

## 2.2 ACL explained (revision)

**ACL** = “can this user read this document/chunk?”

**RAG index is a copy** of docs + permission tags. Tags can be **stale** after revoke.

**Wrong:**

```python
hits = search(all_10M_vectors, top_k=50)
hits = [h for h in hits if user_can_read(h)]  # post-filter
# User with 2% visibility: often 0 chunks → model guesses
```

**Right:**

```python
hits = search(
    vector=query_vec,
    top_k=50,
    filter={"allowed_groups": {"$in": user["groups"]}},
)
```

## 2.3 Cache fingerprint (Alice finance vs Bob engineering)

```python
def acl_fingerprint_from_groups(user):
    return "|".join(sorted(user["groups"]))   # "finance" or "engineering"

# Alice groups ["finance"]  → material "finance"  → hash → KEY_A
# Bob   groups ["engineering"] → different hash → KEY_B
# Same question text, different cache slots → no leak
```

**Stricter:** fingerprint = hash(sorted(**allowed_doc_ids**)) after IAM resolve.

**Shared cache is OK** when two users have the **same groups** and same question — they’re allowed the same answer.

## 2.4 One complete turn (checklist)

1. Client: `conversation_id`, message, JWT.  
2. Gateway: `trace_id`, **deadline**, tenant.  
3. Orch: `history = DB.load(conversation_id)`.  
4. Retrieve: same embed model as index + **ACL in filter**.  
5. Hybrid + rerank + assemble context (§3.8).  
6. LLM: **pinned** `model_id`, check `finish_reason != length` on JSON routes.  
7. Stream; save user + assistant messages.  
8. Log `retrieved_doc_ids`, version tuple.

**You do NOT:** look up “similar prefix” in a KV store in application code.

## 2.5 Conversation memory + summary

- Store full turns in DB by `conversation_id`.  
- **Append-only** in prompt for prefix cache.  
- When too long: **one** compaction — replace oldest block with **English summary paragraph**; one cache miss, then append again.

## 2.6 Request path order

```
Admit → Guard IN → Cache READ (scoped key) → Retrieve (ACL pre-filter)
  → Route model → Generate (stream) → Guard OUT → Cache WRITE (if grounded)
```

---

# Chapter 3 — RAG

## 3.1 Why retrieve (not only fine-tune)

| | Fine-tune | Long context | RAG |
|--|-----------|--------------|-----|
| Update facts | Weeks | Next request | Re-index minutes |
| Delete bad data | Hard | Omit from prompt | Delete chunk |
| Per-user docs | One model | Expensive | ACL at search |

Fine-tune = **behavior**. RAG = **facts**.

## 3.2 Two pipelines

**Offline:** parse → chunk → embed → upsert (throughput, freshness SLO).  
**Online:** embed query → search → rerank → prompt → LLM (latency, **this user**).

**Delete lag:** CDC + embed queue + index merge + **answer cache TTL** = exposure window.

## 3.3 PDF → chunk → index (walkthrough)

1. **Parse** `refund-policy.pdf` → sections, tables.  
2. **Chunk** with header: `[Document: Refund 2026 | §2 EU]\nRefunds within 30 days...`  
3. **Embed** with `embed_model=v2` → vector.  
4. **Upsert** payload: `chunk_id`, `doc_id`, `allowed_groups`, `embed_model`, text.  
5. **Edit §1 only** → re-embed **that chunk** if structural chunking (not whole doc).

## 3.4 Hybrid + RRF (intuition)

- Dense: “money back” ≈ “refund”.  
- BM25: exact `SKU-7731`.  
- **RRF:** add `1/(60+rank)` from each list — don’t add raw cosine + BM25 scores.

## 3.5 Rerank

ANN top **50** → cross-encoder scores pairs → top **5** → LLM.  
**Dedupe** before rerank (same chunk from dense and BM25).

## 3.6 Hallucination triage

```
Wrong answer?
  Gold chunk in top-k?  NO → fix retrieval/chunking
  In final prompt?      NO → fix rerank/budget
  In prompt but wrong?  YES → prompt/abstain
```

Measure **recall@k** on golden set **before** tuning the LLM.

**Golden set size:** See **§1.3.1** — at recall@5 ≈ 0.84 you need **~1,000** queries to see a **±2.2 pp** move; compare pipelines **paired** (McNemar on queries one finds and the other misses). Prefer **production-mined** queries stratified by class; synthetic “questions from the chunk” **inflate** dense recall.

## 3.8 Context assembly

- Token **budget** (knapsack).  
- **Best chunk first** (lost in the middle).  
- **Cite** `chunk_id` in prompt; validate citations in output.  
- Drop superseded doc versions before LLM.

---

# Chapter 4 — Vector search (revision focus)

## 4.3 Why approximate (ANN)

Exact: compare query to **every** vector = read **gigabytes per query**.  
Interactive RAG needs **milliseconds** → **ANN** (approximate nearest neighbors).

ANN recall@k = overlap with exact top-k — measure in prod; drift over time.

## 4.4 HNSW vs 4.5 IVF (memory hook)

| | HNSW | IVF |
|--|------|-----|
| Structure | **Graph** of neighbors | **k-means buckets** + lists |
| Query | Random hops, load full vec in **RAM** | Scan **few cells** sequentially |
| Tune | M, ef_search | nlist, nprobe |
| Risk | Tombstones, graph too sparse | Centroid stale, cell boundaries |

**Not the same:** IVF **clusters** explicitly; HNSW **links** nearby points without one cluster per point.

## 4.6 Quantization — int8, PQ, binary (DETAILED)

### Starting point

```
Chunk "EU refunds 30 days"
v = [0.8, -0.2, 0.5, 0.1, ...]   # 768 floats ≈ 3 KB
```

### A) int8 scalar

**Encode** (per dimension, with corpus min/max e.g. -1..+1):

```
byte = round((value - min) / (max - min) * 255)
0.8 → 230
```

**Search:** compare query int8 to every stored int8 (or top R then float rescore).  
**Quality:** small loss — many tiny differences collapse to same byte.  
**Not** “multiply float by 255” without min/max — that’s wrong.

### B) PQ — codebooks step by step

**Split** 768-d into **32 sub-vectors** of 24 dims (example uses 4-d → 2 parts for teaching).

**Train codebooks (offline, once):**

1. Take **sample** of 1M vectors from your index.  
2. For **part 0**, collect all 2-d (or 24-d) slices.  
3. Run **k-means with K=256** → centers = `codebook[0][0..255]`.  
4. Repeat for parts 1..31.

**Encode one vector:**

```
part0 = [0.8, -0.2]  → nearest prototype is #0 → byte 0
part1 = [0.5,  0.1]  → nearest prototype is #2 → byte 2
stored PQ code = [0, 2, ...]  # 32 bytes total
```

You **cannot** perfectly reconstruct original floats from `[0,2,...]` — only approximations.

**Search (online):**

1. Split query q into same parts.  
2. For each part j, precompute `table[j][0..255]` = distance from q_part to each prototype.  
3. For each chunk with code `[b0,b1,...]`:  
   `approx_dist = table[0][b0] + table[1][b1] + ...`  
4. Sort all chunks by approx_dist → take top **R = 500**.  
5. Load **500 full float vectors** from SSD/RAM.  
6. **Exact cosine** → final top **k = 10**.

```
PQ = cheap rough sort
Rescore R = expensive truth for shortlist
```

**If you skip step 5–6:** wrong chunks can win (quality drop).

### C) Binary

Each dimension: ≥0 → bit 1, else 0.  
768 bits ≈ 96 bytes.  
Distance = **Hamming** (count differing bits).  
**Coarse** — 0.8 and 0.01 both → 1.  
Use only with **test on your embed model** + rescore.

### Quality ranking (before rescore)

```
float32  >  int8  >  PQ  >  binary
```

### 1B vectors size (illustrative)

| Format | ~RAM |
|--------|------|
| fp32 | 3 TB |
| int8 + HNSW | ~0.9 TB |
| IVF-PQ ~100 B/vec | ~100 GB |

---

## 4.7 Filters and selectivity **f**

**f** = fraction of index rows matching filter **for this query**.

Example: 10M vectors, seller sees **2%** → f = 0.02.

**Post-filter** ANN top 50:

```
expected survivors = 50 × 0.02 = 1
P(zero) ≈ 36%  → empty context → "hallucination"
```

| f | Strategy |
|---|----------|
| **< ~1%** | Pre-filter → exact scan on subset (ACL, one seller) |
| **1–30%** | Filter during graph walk (engine support + test) |
| **> ~30%** | ANN + oversample then filter |

**ACL:** always **pre-filter** — never security via post-filter only.

**pgvector pattern:**

```sql
SELECT chunk_id, embedding <=> $1 AS dist
FROM chunks
WHERE tenant_id = $2
  AND embed_model = $3
  AND allowed_groups && $4::text[]
ORDER BY embedding <=> $1
LIMIT 50;
```

---

## 4.8 Sharding and freshness (does one query search all shards?)

**Shard** = one **slice** of the vector index (millions of vectors) on one machine/partition. Each shard has its own ANN index (HNSW/IVF).

**Answer: it depends how you split data — not always “all shards.”**

### A) Tenant sharding (default for SaaS) → **NO, one shard**

```
All Acme chunks live ONLY on Shard 7
Query: tenant=acme → router sends search ONLY to Shard 7
Shards 1,2,3,...6,8,... are NOT searched
```

**Why:** routing key = `tenant_id`. You already know where Acme’s vectors are.

**Good for:** ACL, delete tenant (= drop one partition), no 32-way fan-out.

**Bad:** one huge tenant can overload one shard → dedicated shard or bounded spill (Ch2).

### B) Hash / random sharding → **YES, all S shards, then merge**

```
Chunk placement: shard_id = hash(chunk_id) % 32   (no business meaning)
Query: send SAME embedding to ALL 32 shards
Each returns local top-10 → coordinator merges → global top-10
```

**Why all shards:** you don’t know which shard holds the true nearest neighbor (Acme chunk might be on shard 3, 11, 28…).

**Cost:** latency = **slowest** shard (tail problem).

```
P(at least one shard in its p99) ≈ 1 - (1 - 0.01)^32 ≈ 27.5%
→ p50 can look fine while user p99 hurts
```

**Levers:** fewer shards (bigger nodes + PQ); tenant routing instead; hedge slow shard replica; partial merge (31/32 OK for RAG) + log `missing_shards`.

### C) One cluster + metadata filter (not “32 servers”)

Single service, `WHERE tenant_id = acme` inside index — **one query**, pre-filter (§4.7). Not the same as fan-out to 32 machines unless backend still shards underneath.

### Mini example (hash, 4 shards)

```
c_finance → hash → Shard 2
c_sports  → hash → Shard 0
Query "Q3 revenue?" → must query 0,1,2,3 → merge → c_finance wins on Shard 2
```

If you only searched Shard 2 without hash routing, you’d miss vectors on other shards.

### Freshness (writes)

```
Upload → vectors in small "buffer" segment (searchable quickly)
       → background MERGE into big index (seconds–minutes)
Bulk import → separate build + swap; don't flood live merge (hurts query p99)
```

**Exposure:** delete at source ≠ instant in index; include **answer cache TTL** in revoke window (Ch3).

---

## 4.9 Choosing index

Ask first:

1. Vectors per **tenant partition** (not global)?  
2. **Bytes/vector** after quant?  
3. **Churn** (% updated/day)?

| Partition size | Start here |
|----------------|------------|
| < ~1M | **pgvector** + HNSW + SQL `WHERE` |
| 1M–100M | HNSW int8 in RAM |
| 100M+ | IVF-PQ or disk graph + **rescore R** |

---

# Chapter 5 — Serving (revision)

## Request inside vLLM-class engine

```
1 QUEUE     — KV budget free? else 429/wait
2 PREFILL   — all prompt tokens → sets TTFT (compute-heavy)
3 KV CACHE  — grows with context × concurrent requests
4 DECODE    — one token/step; read ALL weights each step (bandwidth)
5 STREAM    — SSE to client
```

**KV pinned until stream closes** — user reading tab still holds GPU memory.

**KV-seconds** = `context_tokens × seconds_alive` — use for fair rate limits, not just “requests/sec.”

**Continuous batching:** new requests join each decode step — why hosted inference $/token works.

**Weight FP8:** often buys **more concurrent users** (room for KV), not 2× faster for one user at high batch.

**128k unique context in prompt** vs **4k RAG chunks:** can be **~32×** fewer concurrent users on same GPU — unless **shared prefix** (prefix cache).

## 5.4 Quantization (three knobs)

| Knob | Main win |
|------|----------|
| **Weight FP8/INT8** | Smaller weights → **more KV RAM** → more concurrent chats |
| **Weight 4-bit** | Max compression; JSON/code tail risk — gate on **your** evals |
| **KV FP8** | Half KV bytes → ~2× context or concurrency at long ctx |

At **high batch**, weight quant helps **latency** less (~1.4× not 2×); **KV quant** matters more for 32k+.

## 5.5 Speculative decoding

Cheap **draft** k tokens → target **verifies** in one pass → accept prefix.

- **High α:** code, JSON, quoting input (RAG)  
- **Low α:** creative prose, temp 1.0  
- **High batch:** speculation can **slow** you — enable per route, disable when queue deep

## 5.6–5.8 Fleet & buy

- **step_time** ≈ weight_read + batch × per-seq KV work — tune batch, max_tokens, context.  
- Route by **conversation_id** / prefix hash for prefix cache hits (self-host).  
- **Don't** autoscale on TTFT spike right after adding replicas (cold cache).  
- **Rent API** for bursty interactive; self-host when flat util / residency / prefix-heavy fleet.

---

# Quick revision drills

1. **Aleatoric vs systematic** — when to retry?  
2. **Prefix cache match rule** — token IDs or cosine?  
3. **Why post-filter ACL at f=2% fails?**  
4. **PQ codebook training** — k-means on what?  
5. **Why rescore R after PQ?**  
6. **IVF vs HNSW** — bucket scan vs graph hops?  
7. **One turn** — where does ACL run?  
8. **95% CI at n=100, p=85%** — roughly ± how many points? (**~±7**)  
9. **Pooled vs paired** — which uses discordant pass/fail flips? (**paired / McNemar**)  
10. **recall@5 tweak +2 pp** — need about how many golden queries to see it? (**~500–1,000**)  
11. **Tenant shard vs hash shard** — does one Acme query hit all shards? (**No — one tenant shard; yes if hash-sharded corpus**)  
12. **IVF-PQ one query** — what is R for? (**Rescore count: load full vectors, exact distance, fix PQ order**)  
13. **Weight FP8 on serving fleet** — 2× faster per user or more concurrent users? (**Usually more concurrency / KV budget**)  
14. **Spec decode at batch 256, low α** — help or hurt? (**Often hurt — extra verify compute**)

---

# Files

- Notes: `/Users/kjana/Downloads/AI-Native-Architecture-Notes.md`  
- This doc: `/Users/kjana/Downloads/docs/MD/AI-Native-Architecture-Chat-Study-Notes.md`

*Last expanded: Ch5 §5.4–5.8 + revision drills (chat).*
