# 11 — Redis for AI (Cache, Semantic Cache, Memory, Rate Limits)

## Learning objectives

Implement **exact** LLM response cache, sketch **semantic** cache with safe thresholds, and **rate-limit** by user/API key without double-counting at gateway + app.

---

## Why Redis in AI stacks

You already know Redis for sessions — in AI it also powers:

| Use | Mechanism |
|-----|-----------|
| **Exact LLM cache** | Hash(prompt+model) → response |
| **Semantic cache** | Embedding similarity → near-duplicate prompts |
| **Agent memory** | Fast thread state, TTL |
| **Rate limiting** | Token bucket per user/API key |
| **RAG cache** | Cache retrieval results for hot queries |

See also: `MD/caching-and-performance/` (system-design caching guides in this repo).

---

## Exact match caching

```python
import hashlib
import redis

r = redis.Redis(decode_responses=True)

def cache_key(model: str, messages: str) -> str:
    h = hashlib.sha256(f"{model}:{messages}".encode()).hexdigest()
    return f"llm:exact:{h}"

def get_or_call(model, messages, llm_fn):
    k = cache_key(model, messages)
    hit = r.get(k)
    if hit:
        return hit
    out = llm_fn()
    r.setex(k, 3600, out)
    return out
```

**Hit rate** high when prompts repeat (support FAQs, codegen templates).

---

## Semantic caching (intuition)

Embed query \(q\), find cached query \(q'\) if \(\text{sim}(q, q') > \tau\).

\[
\text{sim}(q, q') = \frac{q \cdot q'}{\|q\|\|q'\|}
\]

**Risk:** false positive → wrong answer served — tune \(\tau\) and **validate** with small model or rules.

Course: Redis + embeddings module + final web app demo.

---

## Rate limiting and cost control

```python
# Sliding window counter (conceptual) — prefer redis-cell or gateway quotas in prod
import time

def allow_request(r: redis.Redis, user_id: str, limit: int = 60, window_sec: int = 60) -> bool:
    key = f"ratelimit:{user_id}:{int(time.time()) // window_sec}"
    n = r.incr(key)
    if n == 1:
        r.expire(key, window_sec)
    return n <= limit
```

Align with **gateway virtual keys** — Redis at app edge, gateway at provider edge. Do not apply two independent limits with different windows unless product intends that.

**Cost math:** if cache hit rate is \(h\) and average completion costs \(c\) dollars, expected cost per request \(\approx (1-h)c\) plus embedding cost for semantic lookup.

---

## Agent conversation memory

Store `thread_id → message list` or checkpoint blob; align with LangGraph Redis checkpointer in production.

---

## Semantic cache sketch (embeddings)

```python
# Pseudocode — use Redis Stack vector search or RedisVL in production
def semantic_get(query: str, threshold: float = 0.92):
    q_vec = embed(query)
    hits = redis_vector_search(q_vec, top_k=1)
    if hits and hits[0].score >= threshold:
        return hits[0].cached_response
    return None
```

**False positive cost** can exceed cache savings — log `cache_hit_type=semantic` and sample-review weekly.

---

## Production notes

### Redis configuration for AI workloads

```conf
# redis.conf essentials for LLM cache
maxmemory 2gb
maxmemory-policy allkeys-lru      # evict least-recently-used when full
save ""                            # disable RDB if using as pure cache
appendonly no                      # disable AOF for cache-only use
# For persistent memory (agent state): enable AOF
# appendonly yes
# appendfsync everysec
```

### Cluster mode vs single instance

| Scenario | Recommendation |
|----------|---------------|
| < 10k RPM, < 1GB cache | Single instance (simpler) |
| > 10k RPM or > 2GB | Redis Cluster or managed (ElastiCache, Upstash) |
| Multi-region | Managed with replication (ElastiCache Global Datastore) |

### Monitoring Redis for AI

| Metric | Source | Alert |
|--------|--------|-------|
| `used_memory` / `maxmemory` | `INFO memory` | > 80% → plan scale-up |
| `evicted_keys` | `INFO stats` | Sustained > 0 → cache too small |
| `cache_hit_rate` | App metric | Drop > 10% → TTL or workload changed |
| `connected_clients` | `INFO clients` | Spike → connection leak |
| `latency_p99` | `redis-cli --latency` | > 5ms → network or overload |

```python
import redis

r = redis.Redis()
info = r.info("memory")
used = info["used_memory"] / (1024**3)
max_mem = info["maxmemory"] / (1024**3)
print(f"Memory: {used:.2f}GB / {max_mem:.2f}GB ({used/max_mem*100:.0f}%)")
```

### Eviction strategy for LLM cache

- **`allkeys-lru`** — best for general LLM cache (evict oldest unused).
- **`volatile-ttl`** — evict keys with shortest remaining TTL first; useful if some keys are more important.
- **Never use `noeviction`** for cache — Redis returns errors when full, causing app failures.

---

## Senior pitfalls

| Issue | Mitigation |
|-------|------------|
| Cache key ignores `model` + `temperature` | Include in hash |
| Cached wrong answer after prompt change | Version in key: `prompt_hash` |
| Redis memory eviction | Set `maxmemory-policy`; monitor evictions |

---

## Practice

Measure exact-cache hit rate on 100 repeated FAQ prompts; then try semantic cache at \(\tau=0.95\) and log one false-positive review per day.

## Production-grade practice

4. **Deploy Redis with `maxmemory` and `allkeys-lru`** — fill cache to 80%; verify eviction kicks in; monitor `evicted_keys`.
5. **Build a cache metrics dashboard** — log hit/miss/eviction counts per minute; identify peak traffic patterns.
6. **Implement a rate limiter** — sliding window per `user_id`; test with burst traffic; verify 429 responses after limit.
7. **Run a semantic cache A/B test** — serve 50% of traffic with semantic cache on, 50% off; compare latency, cost, and answer correctness (spot-check 10 semantic hits for false positives).

---

## Lecture map

Redis setup, exact cache, semantic cache, agent memory, rate limiting, RAG cache demo.

**Next:** [12-capstone-projects-architecture.md](./12-capstone-projects-architecture.md)
