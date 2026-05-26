# Caching Practical Challenges — Everything That Breaks in Production

> Every problem here has happened in real production systems. These aren't theoretical — they're the nightmares that wake up on-call engineers at 3 AM.

---

## Table of Contents

1. [Cache Stampede (Thundering Herd)](#1-cache-stampede-thundering-herd)
2. [Cache Avalanche (Mass Expiration)](#2-cache-avalanche-mass-expiration)
3. [Cache Penetration (Querying Non-Existent Data)](#3-cache-penetration-querying-non-existent-data)
4. [Cache Breakdown (Hot Key Expiry)](#4-cache-breakdown-hot-key-expiry)
5. [Cache Poisoning (Stale Data Resurrection)](#5-cache-poisoning-stale-data-resurrection)
6. [Cache-Database Inconsistency Race Conditions](#6-cache-database-inconsistency-race-conditions)
7. [Hot Key Problem](#7-hot-key-problem)
8. [Big Key Problem](#8-big-key-problem)
9. [Cold Start Problem](#9-cold-start-problem)
10. [Data Collisions (Replicated Cache)](#10-data-collisions-replicated-cache)
11. [Split Brain (Network Partition)](#11-split-brain-network-partition)
12. [Multi-Layer Cache Inconsistency](#12-multi-layer-cache-inconsistency)
13. [Memory Fragmentation](#13-memory-fragmentation)
14. [Serialization Overhead](#14-serialization-overhead)
15. [Cache Capacity Planning Failures](#15-cache-capacity-planning-failures)
16. [Cascading Failures](#16-cascading-failures)
17. [Write Amplification](#17-write-amplification)
18. [TTL Hell (Time-to-Live Misconfigurations)](#18-ttl-hell-time-to-live-misconfigurations)
19. [Dogpile Effect](#19-dogpile-effect)
20. [Connection Pool Exhaustion](#20-connection-pool-exhaustion)
21. [Summary Matrix](#21-summary-matrix)

---

## 1. Cache Stampede (Thundering Herd)

### What Happens

A popular cache key expires. Thousands of concurrent requests all see the miss at the same time and simultaneously query the database.

```
NORMAL OPERATION:
  1000 requests/sec → Cache HIT → return cached value
  DB load: 0 queries/sec

KEY EXPIRES (T+0):
  1000 requests/sec → Cache MISS → ALL hit the database
  DB load: 1000 queries/sec (instantaneous spike)

  ┌──────────────────────────────────────────────┐
  │  Request 1 → cache miss → query DB ─┐        │
  │  Request 2 → cache miss → query DB ─┤        │
  │  Request 3 → cache miss → query DB ─┼──► DB  │
  │  Request 4 → cache miss → query DB ─┤  💀    │
  │  ...                                 │ CRUSHED│
  │  Request 1000 → cache miss → query DB┘        │
  └──────────────────────────────────────────────┘

  DB overwhelmed → timeouts → more retries → DB dies
  → cache never gets repopulated → system-wide outage
```

### Why It's Dangerous

This isn't just "slow responses." The stampede creates a **positive feedback loop:**
1. DB overloaded → queries take longer
2. More requests arrive while DB is slow → queue grows
3. Timeouts trigger retries → even more DB load
4. DB crashes → complete outage

### Solutions

#### Solution 1: Distributed Lock (Mutex)

```
Request 1 → cache miss → acquire lock → query DB → write cache → release lock
Request 2 → cache miss → lock taken → WAIT → lock released → read from cache
Request 3 → cache miss → lock taken → WAIT → lock released → read from cache

Only ONE request hits the DB. Others wait for the cache to be populated.
```

```python
def get_with_lock(key):
    value = cache.get(key)
    if value is not None:
        return value
    
    lock_key = f"lock:{key}"
    if cache.set(lock_key, "1", nx=True, ex=5):  # acquire lock, 5s timeout
        try:
            value = database.query(key)
            cache.set(key, value, ex=300)
            return value
        finally:
            cache.delete(lock_key)
    else:
        time.sleep(0.05)  # brief wait
        return cache.get(key)  # retry — hopefully populated by lock holder
```

**Trade-off:** Lock holder becomes a single point. If it crashes, others wait forever. Need lock timeout.

#### Solution 2: Staggered Expiration (TTL Jitter)

```python
base_ttl = 300  # 5 minutes
jitter = random.randint(0, 60)  # 0-60 seconds random
cache.set(key, value, ex=base_ttl + jitter)

# Key A expires at 300s, Key B at 347s, Key C at 312s
# No two keys expire at exactly the same moment
```

**Trade-off:** Simple but doesn't prevent stampede on a single hot key.

#### Solution 3: Early Recomputation (Probabilistic)

```
Key TTL = 300s, current age = 280s (almost expired)

Request arrives:
  remaining_ttl = 20 seconds
  probability_of_refresh = exp(-remaining_ttl * beta)
  
  If random() < probability_of_refresh:
    Recompute and refresh cache (proactively)
  Else:
    Return current cached value

The closer to expiration, the higher the probability that a request
triggers a background refresh — BEFORE the key actually expires.
```

**Trade-off:** May recompute unnecessarily, but prevents the cliff-edge expiration stampede.

#### Solution 4: Never Expire (Background Refresh)

```
Cache key: NO TTL (never expires)
Background worker: refreshes every N seconds

  ┌──────────────┐     always returns cached data
  │   Requests   │────────────────────────────────► Cache
  └──────────────┘
  
  ┌──────────────┐     updates cache periodically
  │   Background │────► DB ────► Cache
  │   Worker     │     (every 30s)
  └──────────────┘

No expiration = no stampede. Ever.
```

**Trade-off:** Data can be stale for up to refresh interval. Requires background infrastructure.

---

## 2. Cache Avalanche (Mass Expiration)

### What Happens

Unlike stampede (one key), avalanche is when **thousands of keys expire at the same time**, causing a massive wave of DB queries.

```
T+0:00   System starts, loads 100,000 keys with TTL = 3600s (1 hour)
T+60:00  ALL 100,000 keys expire simultaneously

  ┌─────────────────────────────────────────┐
  │  100,000 cache misses at the same second │
  │  → 100,000 concurrent DB queries         │
  │  → DB: 💀                                │
  └─────────────────────────────────────────┘
```

### Common Trigger

```
# THE MISTAKE: All keys set with identical TTL
for item in all_items:
    cache.set(item.key, item.value, ex=3600)  # all expire together!

# After 1 hour: AVALANCHE
```

### Solutions

#### Solution 1: TTL Jitter (Primary Defense)

```python
for item in all_items:
    ttl = 3600 + random.randint(-300, 300)  # 55-65 minutes
    cache.set(item.key, item.value, ex=ttl)

# Keys expire over a 10-minute window instead of one instant
```

#### Solution 2: Multi-Level TTL

```
Level 1 (L1): Local cache,  TTL = 30 seconds
Level 2 (L2): Redis,         TTL = 1 hour + jitter
Level 3 (L3): Database

L2 key expires → only L2-miss requests hit DB (L1 still serving!)
L1 expires 30s later → hits L2 (now repopulated) → no DB hit
```

#### Solution 3: Cache Warming Before Expiration

```
Background job monitors keys approaching expiration:

  Key "product:123" → TTL remaining: 120s → REFRESH NOW
  Key "product:456" → TTL remaining: 90s  → REFRESH NOW
  Key "product:789" → TTL remaining: 3500s → skip (still fresh)
```

---

## 3. Cache Penetration (Querying Non-Existent Data)

### What Happens

Requests keep asking for data that **doesn't exist** in the cache OR the database. Every request is a miss, and every miss hits the DB — which also returns nothing.

```
Attacker or bug: request user_id = -1 (doesn't exist)

  Request → Cache MISS → DB query → NOT FOUND → return null
  Request → Cache MISS → DB query → NOT FOUND → return null
  Request → Cache MISS → DB query → NOT FOUND → return null
  ... 10,000 times per second

  DB is hammered with queries that always return empty.
  Cache never helps because there's nothing to cache.
```

### Why It's Especially Dangerous

- **DDoS vector:** Attacker sends random IDs that will never exist
- **Infinite miss loop:** Cache can never warm up
- **DB protection useless:** No amount of cache helps against non-existent keys

### Solutions

#### Solution 1: Cache Null Values

```python
def get_user(user_id):
    cached = cache.get(f"user:{user_id}")
    if cached == "NULL_SENTINEL":
        return None  # we know it doesn't exist
    if cached is not None:
        return cached
    
    user = database.get_user(user_id)
    if user is None:
        cache.set(f"user:{user_id}", "NULL_SENTINEL", ex=60)  # short TTL
        return None
    
    cache.set(f"user:{user_id}", user, ex=3600)
    return user
```

**Trade-off:** Memory used for null entries. Short TTL needed so that if the item is later created, stale "doesn't exist" entry expires.

#### Solution 2: Bloom Filter

```
A Bloom filter is a probabilistic data structure that can tell you:
  - "Definitely NOT in the set" (100% accurate)
  - "Probably in the set" (small false positive rate)

┌──────────┐     ┌──────────────┐     ┌───────┐     ┌──────┐
│ Request  │────►│ Bloom Filter │────►│ Cache │────►│  DB  │
│ user:999 │     │              │     │       │     │      │
└──────────┘     │ "user:999    │     │       │     │      │
                 │  exists?"    │     └───────┘     └──────┘
                 │              │
                 │ NO → reject  │  ← never hits cache or DB
                 │ YES → proceed│  ← may be false positive, but rare
                 └──────────────┘

Bloom filter size: ~1.2 bytes per entry for 1% false positive rate
1 million users = 1.2 MB of memory → blocks all non-existent key attacks
```

**Trade-off:** Need to maintain the Bloom filter (add new IDs, rebuild periodically). False positives still hit DB but are rare (~1%).

#### Solution 3: Input Validation

```python
def get_user(user_id):
    if user_id < 0 or user_id > MAX_USER_ID:
        return None  # reject obviously invalid IDs
    # ... proceed with cache lookup
```

**Trade-off:** Only blocks simple invalid IDs, not valid-looking non-existent ones.

---

## 4. Cache Breakdown (Hot Key Expiry)

### What Happens

A **single extremely popular key** expires, and that one key causes a stampede on the database. Similar to stampede but focused on one key.

```
Key "homepage_trending_products" → 50,000 reads/sec

Key expires:
  50,000 requests/sec → all miss → all query DB for the same data
  DB: 💀
```

### How It Differs from Stampede and Avalanche

| Problem | Keys affected | Trigger |
|---|---|---|
| **Stampede** | One or few keys | Key expiration under high concurrency |
| **Avalanche** | Thousands of keys | Mass expiration at same time |
| **Breakdown** | One extremely hot key | The one key everyone reads expires |

### Solutions

Same as Stampede solutions (mutex lock, early refresh, never-expire), plus:

#### Hot Key Detection + Pre-Emptive Refresh

```python
# Track access frequency
access_counts = {}

def get(key):
    access_counts[key] = access_counts.get(key, 0) + 1
    
    if access_counts[key] > HOT_THRESHOLD:
        remaining_ttl = cache.ttl(key)
        if remaining_ttl < REFRESH_BEFORE_SECONDS:
            refresh_in_background(key)  # proactively refresh hot keys
    
    return cache.get(key)
```

---

## 5. Cache Poisoning (Stale Data Resurrection)

### What Happens

Correct data is written to the database, but **stale data gets written back into the cache**, undoing the update. The cache now has permanently wrong data until TTL expires.

```
POISON SCENARIO:

T+0.000s  Thread A: DELETE cache key "user:123" (invalidation)
T+0.001s  Thread B: cache miss for "user:123" → reads DB
          BUT: Thread A's DB UPDATE hasn't committed yet
          Thread B reads OLD value from DB
T+0.002s  Thread A: UPDATE DB → commits new value
T+0.003s  Thread B: SET cache "user:123" = OLD VALUE with fresh TTL

Result: DB has new value, cache has OLD value
        Cache is POISONED for the entire TTL duration (e.g., 1 hour)

Timeline:
  DB:    [old] ──────► [NEW] ──────────────────────► [NEW]
  Cache: [old] → [del] → [old resurrected] ──────► [old for 1 hour!]
                           ↑
                      POISON POINT
```

### Why It's Insidious

- No errors in logs — everything "succeeded"
- Users see stale data with no indication anything is wrong
- Debugging is extremely hard (inconsistency is intermittent, depends on timing)
- In financial systems: wrong balances, duplicate charges

### Solutions

#### Solution 1: Delayed Double Deletion

```
1. Update database
2. Delete cache key
3. Wait 300-500ms (let in-flight reads complete)
4. Delete cache key AGAIN

Step 4 clears any stale value that was re-inserted between steps 1 and 3.
```

```python
async def update_user(user_id, new_data):
    database.update(user_id, new_data)      # 1. Update DB
    cache.delete(f"user:{user_id}")          # 2. First delete
    await asyncio.sleep(0.5)                 # 3. Wait 500ms
    cache.delete(f"user:{user_id}")          # 4. Second delete (clears poison)
```

**Trade-off:** The 500ms delay doesn't guarantee safety if DB replication lag is longer. Also adds latency.

#### Solution 2: Version Stamp

```python
def update_user(user_id, new_data):
    version = generate_version()  # monotonic timestamp or counter
    database.update(user_id, new_data, version=version)
    cache.set(f"user:{user_id}", {**new_data, "version": version})

def get_user(user_id):
    cached = cache.get(f"user:{user_id}")
    if cached:
        db_version = database.get_version(user_id)
        if cached["version"] >= db_version:
            return cached  # fresh
        else:
            cache.delete(f"user:{user_id}")  # stale, invalidate
    # ... fallback to DB
```

**Trade-off:** Every read needs a lightweight version check (but this can be just a hash or timestamp, very fast).

#### Solution 3: Write-Through (Bypass the Race)

```
Instead of: Update DB → Delete Cache → Hope nobody re-fills with stale data

Do: Update DB → Update Cache atomically

  database.update(user_id, new_data)
  cache.set(f"user:{user_id}", new_data, ex=3600)

No gap for stale reads to poison the cache.
```

**Trade-off:** If DB update succeeds but cache update fails, cache has old data. Need retry mechanism.

---

## 6. Cache-Database Inconsistency Race Conditions

### The Classic Race: Cache-Aside Pattern

```
THE STANDARD "CACHE-ASIDE" PATTERN:
  Read:  Check cache → miss → read DB → write to cache
  Write: Update DB → delete cache

RACE CONDITION #1: Read-Write Race

  Thread A (read):                  Thread B (write):
  ──────────────                    ──────────────────
  1. cache miss
  2. read DB (gets old value)
                                    3. update DB (new value)
                                    4. delete cache
  5. write old value to cache
     ↑ CACHE POISONED

Thread A's stale read arrives AFTER Thread B's invalidation.
Cache now has old value, DB has new value.
```

```
RACE CONDITION #2: Write-Write Race

  Thread A (write):                 Thread B (write):
  ──────────────────                ──────────────────
  1. update DB (value = 100)
                                    2. update DB (value = 200)
                                    3. delete cache
  4. delete cache (already deleted)
  
  Next read: cache miss → reads DB → gets 200 → OK
  
  BUT if order is different:
  1. update DB (value = 100)
                                    2. update DB (value = 200)
  3. set cache (value = 100)        ← writing to cache instead of delete
                                    4. set cache (value = 200)
  
  Race: if step 4 happens before step 3:
  Final cache = 100 (Thread A's value), DB = 200 (Thread B's value)
  INCONSISTENT.
```

### Strategies for Cache-Database Consistency

#### Strategy 1: Delete, Don't Update

```
ALWAYS delete cache on write, NEVER update it.

Write: Update DB → Delete cache
Read:  Cache miss → Read DB → Set cache

Why: Deleting is idempotent. Two concurrent deletes = same result.
     Two concurrent SETS can race (last-write-wins may be wrong order).
```

#### Strategy 2: Delete After DB Write (Not Before)

```
WRONG ORDER:
  1. Delete cache
  2. Update DB    ← if this fails, cache is empty, DB has old data
                     next read fills cache with old data = correct
                     BUT: gap between 1 and 2 allows stale reads

RIGHT ORDER:
  1. Update DB
  2. Delete cache  ← if this fails, cache has old data temporarily
                     BUT: TTL will eventually expire it
                     safer default
```

#### Strategy 3: Transactional Outbox Pattern

```
Instead of directly deleting cache after DB update:

1. Update DB + write "invalidation event" in same transaction
   (both in same DB transaction = atomic)

2. Background worker reads outbox table → deletes cache keys

  ┌──────────────┐     ┌──────────────┐     ┌──────────┐
  │  DB Update   │     │   Outbox     │     │  Cache    │
  │  + outbox    │────►│  Processor   │────►│  Delete   │
  │  (atomic)    │     │  (async)     │     │          │
  └──────────────┘     └──────────────┘     └──────────┘

No race: the invalidation event is guaranteed to exist if DB updated.
```

**Trade-off:** Added complexity, slight delay, but guaranteed consistency.

---

## 7. Hot Key Problem

### What Happens

One key receives enormously disproportionate traffic. In a sharded cache, all that traffic hits **one shard**, overwhelming it while other shards sit idle.

```
Redis Cluster (3 shards):

  Shard 1: product:1, product:2, product:3     → 100 req/s (normal)
  Shard 2: product:4, product:5, product:6     → 100 req/s (normal)
  Shard 3: product:7, FLASH_SALE_PRODUCT:8     → 500,000 req/s (💀)
                        ↑
                  Flash sale started, everyone viewing this product

  Shard 3 CPU: 100%
  Shard 3 latency: 500ms+ (should be <1ms)
  Other shards: fine
```

### Solutions

#### Solution 1: Client-Side (Local) Cache for Hot Keys

```
┌──────────────┐
│  Service     │
│              │
│ ┌──────────┐ │     Caffeine / Guava cache
│ │ Local    │ │     TTL = 1-5 seconds
│ │ L1 Cache │ │     Capacity = 100 entries
│ └─────┬────┘ │
│       │ miss │     Only hot keys go here
│       ▼      │
│ ┌──────────┐ │
│ │  Redis   │ │
│ │  Client  │ │
│ └──────────┘ │
└──────────────┘

99% of requests served from local memory.
Redis only hit on L1 miss (every few seconds per key).
```

#### Solution 2: Hot Key Replication (Key Splitting)

```python
REPLICAS = 8

def set_hot_key(key, value, ttl):
    for i in range(REPLICAS):
        cache.set(f"{key}:replica_{i}", value, ex=ttl)

def get_hot_key(key):
    replica = random.randint(0, REPLICAS - 1)
    return cache.get(f"{key}:replica_{replica}")

# "product:8" becomes:
#   "product:8:replica_0" → Shard 1
#   "product:8:replica_1" → Shard 2
#   "product:8:replica_2" → Shard 3
#   ...
# Traffic spread across all shards!
```

**Trade-off:** N replicas = N times memory usage. Invalidation must hit all replicas. Application complexity.

#### Solution 3: Read Replicas

```
Redis primary (writes) → Redis replica 1 (reads)
                       → Redis replica 2 (reads)
                       → Redis replica 3 (reads)

Route hot key reads to replicas. Spread the load.
```

---

## 8. Big Key Problem

### What Happens

A single cache entry is **very large** (e.g., a 10MB JSON blob or a list with 1 million elements). Operations on this key are slow and block the single-threaded Redis event loop.

```
Normal key: GET product:123 → 0.1ms
Big key:    GET user_feed:456 → 150ms (10MB serialized JSON)

During that 150ms, Redis can't serve ANY other request.
All clients blocked. Effective throughput: 0.
```

### Common Culprits

| Pattern | Size | Problem |
|---|---|---|
| Entire user feed cached as one list | 1M items | Slow read/write, blocks event loop |
| All products for a category | 50MB JSON | Serialization takes 200ms |
| Session with accumulated data | 5MB per session | Millions of sessions = memory crisis |
| Sorted set with all user scores | 10M members | ZRANGE blocks for seconds |

### Why DELETE Is Also Dangerous

```
DEL big_key  → Redis must free 10MB of memory
             → Single-threaded, blocks everything
             → If key has 1M list elements, each must be freed
             → Can block for 1-2 SECONDS

Same problem with EXPIRE — when a big key expires, Redis blocks during cleanup.
```

### Solutions

#### Solution 1: Chunked Storage

```python
# Instead of one big key:
# cache.set("user_feed:123", [item1, item2, ..., item1000000])

# Split into chunks:
CHUNK_SIZE = 1000

def set_feed(user_id, items):
    for i in range(0, len(items), CHUNK_SIZE):
        chunk = items[i:i + CHUNK_SIZE]
        cache.set(f"feed:{user_id}:chunk:{i // CHUNK_SIZE}", chunk, ex=3600)
    cache.set(f"feed:{user_id}:total_chunks", len(items) // CHUNK_SIZE + 1)

def get_feed_page(user_id, page):
    return cache.get(f"feed:{user_id}:chunk:{page}")
```

#### Solution 2: UNLINK Instead of DEL

```
DEL big_key    → synchronous, blocks event loop
UNLINK big_key → asynchronous, frees memory in background thread

Always use UNLINK for big keys (Redis 4.0+).
```

#### Solution 3: Lazy Expiration with OBJECT IDLETIME

```
Instead of TTL-based expiration (which blocks on expire):

1. Set no TTL on big keys
2. Background job checks OBJECT IDLETIME
3. If idle > threshold, UNLINK (async delete)
```

---

## 9. Cold Start Problem

### What Happens

After deployment, restart, or failure recovery, the cache is completely empty. All requests hit the database until the cache warms up.

```
NORMAL:     Cache hit rate 99% → DB handles 1% of traffic → happy
COLD START: Cache hit rate 0%  → DB handles 100% of traffic → 💀

If DB was sized for 1% of traffic (because cache handles 99%),
a cold start means 100x the expected DB load.
DB collapses. Cascading failure.
```

### Solutions

#### Solution 1: Cache Warming (Pre-Loading)

```python
async def warm_cache():
    """Run BEFORE accepting traffic after deployment."""
    hot_keys = get_most_accessed_keys(limit=10000)  # from access logs
    
    for key in hot_keys:
        value = database.get(key)
        cache.set(key, value, ex=3600 + random.randint(0, 300))
    
    logger.info(f"Cache warmed with {len(hot_keys)} keys")
    # NOW start accepting traffic
```

#### Solution 2: Gradual Traffic Ramp

```
Deploy new instance:
  T+0:    Accept 1% of traffic (cache warming naturally)
  T+30s:  Accept 10% of traffic
  T+60s:  Accept 50% of traffic
  T+120s: Accept 100% of traffic

Load balancer gradually increases weight.
Cache warms naturally from real traffic without overwhelming DB.
```

#### Solution 3: Persistent Cache (RDB/AOF in Redis)

```
Redis with AOF persistence:
  - Every write is logged to disk
  - On restart, Redis replays the AOF file
  - Cache restored from disk (warm, not cold)
  
Trade-off: AOF recovery can take minutes for large datasets.
           Data may be slightly stale (last few writes before crash).
```

#### Solution 4: Agoda's Approach (Pre-Caching)

```
Never let the cache be cold. Background system continuously populates.
Cache is ALWAYS hot — independent of service restarts.
(See pds-distributed-cache-deep-dive.md for full details)
```

---

## 10. Data Collisions (Replicated Cache)

### What Happens

In replicated caches, two instances update the same key concurrently. Both replications cross in-flight, and one update is lost.

```
Instance A:                    Instance B:
  read inventory = 700           read inventory = 700
  write inventory = 690          write inventory = 695
  replicate 690 → B             replicate 695 → A

  Instance A receives 695       Instance B receives 690
  (overwrites 690)              (overwrites 695)

  Final: A = 695, B = 690 (or both = last received)
  Correct: should be 685 (700 - 10 - 5)

  10 units of inventory VANISHED.
```

### Collision Probability Formula

```
Rate ≈ N × (U² / S) × L

N = number of instances
U = updates per second
S = total cache entries
L = replication latency (seconds)
```

### When Collisions Matter vs. Don't

| Scenario | Collision Impact | Acceptable? |
|---|---|---|
| View counter | Off by a few | Yes |
| Inventory count | Lost units | NO |
| User preferences | Last write wins | Usually yes |
| Financial balance | Money appears/disappears | ABSOLUTELY NOT |
| Session data | Login state inconsistent | No |

---

## 11. Split Brain (Network Partition)

### What Happens

Network partition divides cache cluster into two groups that can't communicate. Each group continues operating independently, diverging in state.

```
BEFORE PARTITION:
  [Node A] ←──── replication ────→ [Node B]
  [Node C] ←──── replication ────→ [Node D]
  All four nodes consistent.

DURING PARTITION:
  ┌──────────────┐    ╳╳╳╳╳╳╳    ┌──────────────┐
  │ Partition 1  │    network     │ Partition 2  │
  │ Node A       │    split       │ Node C       │
  │ Node B       │               │ Node D       │
  │              │               │              │
  │ key X = 100  │               │ key X = 100  │
  │ (updated to  │               │ (updated to  │
  │  110)        │               │  95)         │
  └──────────────┘               └──────────────┘

  Users hitting Partition 1: see X = 110
  Users hitting Partition 2: see X = 95

AFTER PARTITION HEALS:
  Merge conflict: X = 110 or X = 95?
  
  Resolution strategies:
  - Last-write-wins (by timestamp) — can lose data
  - Higher value wins — domain-specific, not general
  - Larger partition wins — arbitrary
  - Manual resolution — doesn't scale
```

### Hazelcast Real-World Example (from Jepsen Testing)

Jepsen testing found that in Hazelcast 3.8.3 during network partitions:
- Map updates can be lost silently
- "Unique" IDs generated by ID generators can duplicate
- AtomicLong operations aren't actually atomic
- Locks aren't actually exclusive
- When clusters merge, built-in merge policies use non-commutative heuristics that can lose committed updates

**Lesson:** Don't trust distributed caches for strong consistency without understanding their partition behavior.

---

## 12. Multi-Layer Cache Inconsistency

### What Happens

Modern systems have multiple cache layers. Each layer can be stale independently.

```
Request → Browser Cache → CDN Cache → API Gateway Cache → App Cache (L1) → Redis (L2) → DB

SIX LAYERS. Any one can be stale.

Scenario:
  DB: price = $120 (updated 5 minutes ago)
  Redis: price = $120 (refreshed 3 minutes ago)
  App L1: price = $115 (TTL hasn't expired yet)
  API Gateway: price = $110 (cached 10 minutes ago)
  CDN: price = $100 (cached 30 minutes ago)
  Browser: price = $95 (cached yesterday)

  User sees: $95
  Correct price: $120

  User clears browser cache → sees $100 (CDN)
  Hard refresh → sees $110 (API Gateway)
  New incognito tab → sees $115 (App L1)
  
  FOUR DIFFERENT PRICES. All "correct" from their cache's perspective.
```

### Solutions

#### Solution 1: Cache-Control Headers

```
Cache-Control: max-age=60, s-maxage=300, stale-while-revalidate=30

Browser cache: 60 seconds
CDN cache: 300 seconds
Stale-while-revalidate: serve stale for 30s while fetching fresh
```

#### Solution 2: Cache Busting (Version in URL)

```
/api/products/123?v=20260519014400

Version changes → CDN and browser treat as new resource → cache miss → fresh data.
```

#### Solution 3: Propagating Invalidation Top-Down

```
DB updated
  → Invalidate Redis
  → Publish invalidation event
  → API Gateway purges its cache
  → CDN purge API called
  → Client-side: versioned ETags force revalidation

Each layer must be explicitly told to invalidate.
Miss any layer → stale data persists.
```

---

## 13. Memory Fragmentation

### What Happens

Redis (or any in-memory cache) allocates memory in fixed-size chunks via `jemalloc`. When keys of varying sizes are created and deleted, the freed memory has "holes" that can't be efficiently reused.

```
Memory layout (simplified):

ALLOCATED:  [4KB][free][4KB][free][free][4KB][free][4KB]
                  ↑         ↑     ↑          ↑
              fragmented holes — too small for new allocations

used_memory: 16KB (actual data)
RSS (physical): 40KB (what OS allocated)
fragmentation_ratio: 40/16 = 2.5x

You're using 2.5x more memory than your data needs!
```

### Common Causes

| Cause | Why |
|---|---|
| Variable key sizes with different TTLs | Keys expire at different times, leaving irregular holes |
| High churn (frequent set/delete) | Creates many small holes |
| Large values replaced by small values | Large slot partially freed, unusable |
| Sorted sets with frequent member changes | Internal reallocation |

### Detection

```bash
redis-cli INFO memory

# Look for:
# mem_fragmentation_ratio:2.50  ← anything >1.5 is concerning
# used_memory:1073741824        ← actual data
# used_memory_rss:2684354560    ← physical memory (2.5x higher!)
```

### Solutions

| Solution | How |
|---|---|
| `activedefrag yes` | Redis 4.0+ can defragment in background |
| Uniform key sizes | Pad or normalize value sizes |
| Scheduled restarts | Restart Redis periodically (with persistence) |
| `maxmemory-policy allkeys-lru` | Evict before fragmentation gets bad |

---

## 14. Serialization Overhead

### What Happens

Every cache read/write requires serializing objects to bytes (write) and deserializing bytes to objects (read). For complex or large objects, this can dominate latency.

```
Cache write:
  Python dict → JSON string → bytes → Redis SET
  
  Small object (100 bytes):  ~0.01ms serialization
  Medium object (10KB):      ~0.5ms serialization
  Large object (1MB):        ~50ms serialization  ← this is the problem

If Redis GET takes 1ms but deserialization takes 50ms,
Redis isn't the bottleneck — your code is.
```

### Solutions

| Solution | Benefit | Trade-off |
|---|---|---|
| Use MessagePack instead of JSON | 2-3x faster, 30% smaller | Not human-readable |
| Use Protocol Buffers | 5-10x faster, smallest size | Schema required, complex |
| Cache pre-serialized bytes | Zero deserialization on read | Can't inspect cached data |
| Compress with LZ4 | 50-70% size reduction, fast | CPU cost, need decompress |
| Store only needed fields | Less to serialize | More complex cache logic |

---

## 15. Cache Capacity Planning Failures

### What Happens

Cache is provisioned too small. Eviction rate is high, hit rate drops, and the cache becomes useless.

```
Provisioned: 1GB cache
Working set: 5GB of active data

Result:
  Cache can hold: 20% of working set
  Hit rate: ~20% (constant eviction via LRU)
  Effective improvement: minimal
  Cost: paid for cache infrastructure + still hitting DB 80% of the time

  WORSE THAN NO CACHE: you pay for cache + still pay for DB load
  + added latency of checking cache before DB (miss penalty)
```

### The Math

```
                                  ┌─────────────────────┐
Hit rate vs capacity:             │                     │
                                  │   100%   ___________│
                                  │         /           │
                                  │   80%  /            │
  Hit rate                        │       /             │
                                  │  60% /              │
                                  │     /               │
                                  │ 40%/                │
                                  │   /                 │
                                  │20/                  │
                                  │ /                   │
                                  │/___________________│
                                  0%   50%  100%  150%
                                     Cache / Working Set

Sweet spot: cache ≥ 80% of working set → 95%+ hit rate
Below 50%: hit rate drops rapidly, cache barely helps
```

### Planning Formula

```
Required cache size = active_item_count × avg_item_size × safety_margin

Example:
  Active hotels: 5 million
  Avg metadata size: 5KB
  Safety margin: 1.3x (for overhead, fragmentation)
  
  Required: 5M × 5KB × 1.3 = 32.5 GB

  If you provision 8GB: cache holds 24% → hit rate ~30% → BAD
  If you provision 32GB: cache holds 98% → hit rate ~99% → GOOD
```

---

## 16. Cascading Failures

### What Happens

Cache failure causes DB overload, which causes timeouts, which causes retries, which causes more DB load, which causes more timeouts...

```
FAILURE CASCADE:

1. Cache node fails
   ↓
2. All requests hit DB (cache miss)
   ↓
3. DB overwhelmed → response times spike to 5s
   ↓
4. Client timeouts trigger retries (2-3x more requests)
   ↓
5. DB load now 3x expected → some queries timeout entirely
   ↓
6. Service returns 503 errors
   ↓
7. Upstream services retry failed requests
   ↓
8. DB load now 10x expected → DB crashes
   ↓
9. All dependent services fail → SYSTEM-WIDE OUTAGE

Time from step 1 to step 9: often < 60 seconds
```

### Solutions

| Solution | How |
|---|---|
| **Circuit breaker** | After N failures, stop querying DB for X seconds. Return degraded response. |
| **Fallback to stale cache** | If cache fails, serve last-known-good data (even if old) |
| **Rate limiting to DB** | Cap concurrent DB queries (e.g., max 100). Excess requests wait or fail fast. |
| **Bulkhead pattern** | Isolate DB connection pools per feature. Cache failure for "search" doesn't starve "checkout." |
| **Graceful degradation** | Serve partial data, placeholder content, or cached-from-disk data |

```python
# Circuit Breaker Example
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=30):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure = 0
        self.state = "CLOSED"  # CLOSED = normal, OPEN = blocking
    
    def call(self, func, fallback):
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.recovery_time:
                self.state = "HALF_OPEN"  # try one request
            else:
                return fallback()  # circuit open, use fallback
        
        try:
            result = func()
            self.failures = 0
            self.state = "CLOSED"
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "OPEN"
            return fallback()
```

---

## 17. Write Amplification

### What Happens

A single logical update triggers cache invalidation across multiple keys, cache layers, and services.

```
User updates their profile name:

1. Update DB: user_profiles table     ← 1 write
2. Invalidate Redis: user:123         ← 1 delete
3. Invalidate Redis: user_feed:123    ← 1 delete (name appears in feed)
4. Invalidate Redis: user_search:123  ← 1 delete (search index)
5. Invalidate CDN: /api/users/123     ← 1 purge
6. Publish event: user.updated        ← 1 message
7. Aggregation cache: update all docs containing user 123 ← N updates

1 logical change → 6 + N physical operations

If any of these fail silently → inconsistency
```

### Solutions

| Solution | How |
|---|---|
| **Event-driven invalidation** | Publish one event, let each cache layer listen and invalidate itself |
| **Cache key dependencies** | Track which keys depend on which entities. One invalidation cascades. |
| **Coarse-grained invalidation** | Invalidate entire cache prefix (`user:123:*`) instead of individual keys |
| **Accept eventual consistency** | Use TTL as backstop; don't chase every cache layer |

---

## 18. TTL Hell (Time-to-Live Misconfigurations)

### Problem 1: TTL Too Short

```
TTL = 1 second

  Cache write → 1 second → expired → cache miss → DB query → cache write → 1 second → expired...

  Effective hit rate: depends on traffic. At 100 req/s → ~99% hit rate.
  At 1 req/s → 0% hit rate (always expired before next request).

  If DB query takes 200ms and TTL is 1s, 20% of the TTL is spent computing.
```

### Problem 2: TTL Too Long

```
TTL = 24 hours

  Data changes at 10am. Cache won't reflect until 10am TOMORROW.
  Users see stale data for up to 24 hours.
  
  For pricing, inventory, availability → unacceptable.
  For static content (images, CSS) → probably fine.
```

### Problem 3: No TTL (Infinite Cache)

```
cache.set("user:123", data)  # no expiration

If user data changes → cache NEVER updates (unless explicitly invalidated)
If invalidation logic has a bug → stale data FOREVER
If key is orphaned (user deleted) → memory leak (key never freed)
```

### Problem 4: Same TTL on Everything

```
# THE MISTAKE
for item in all_items:
    cache.set(item.key, item.value, ex=3600)  # all = 1 hour

# Result: cache avalanche every hour on the hour
```

### TTL Strategy Guide

| Data Type | Recommended TTL | Rationale |
|---|---|---|
| Session tokens | 15-30 minutes | Security: sessions should expire |
| User preferences | 5-15 minutes | Changes infrequently, brief staleness OK |
| Product catalog | 1-5 minutes + jitter | Changes somewhat frequently |
| Pricing/inventory | 30-60 seconds | Must be fresh, business-critical |
| Static config | 1-24 hours | Rarely changes |
| Null entries (penetration defense) | 30-60 seconds | Don't want to permanently cache "not found" |
| Computed aggregations | 5-10 minutes + jitter | Expensive to compute, some staleness OK |

---

## 19. Dogpile Effect

### What Happens

Similar to stampede but specifically about the **computation cost** of regenerating a cache entry. If regeneration takes 5 seconds and the cache entry serves 1000 req/s, expiration triggers 5000 concurrent regeneration attempts.

```
Cache entry: "expensive_report" → takes 5 seconds to compute
Traffic: 1000 req/s

Key expires:
  T+0.000s: 1000 requests see miss → all start computing the report
  T+0.001s: 1000 more requests → all start computing
  T+0.002s: 1000 more → ...
  
  5 seconds × 1000 req/s = 5000 concurrent computations
  
  Each computation: queries 10 DB tables, runs aggregation
  DB load: 5000 × 10 = 50,000 concurrent queries
  
  TOTAL WASTED WORK: 4999 of those computations produce the same result.
  Only 1 was needed.
```

### Difference from Stampede

| Aspect | Stampede | Dogpile |
|---|---|---|
| Focus | DB overload from concurrent queries | Wasted compute from redundant regeneration |
| Duration | Brief (DB query is fast) | Extended (regeneration takes seconds) |
| Resource wasted | DB connections | CPU, DB, memory, network |

### Solutions

Same as stampede (lock, early refresh), plus:

#### Semaphore-Based Regeneration

```python
import asyncio

regeneration_semaphore = asyncio.Semaphore(1)  # only 1 concurrent regeneration

async def get_expensive_report():
    cached = cache.get("expensive_report")
    if cached is not None:
        return cached
    
    async with regeneration_semaphore:
        # Double-check after acquiring semaphore
        cached = cache.get("expensive_report")
        if cached is not None:
            return cached  # another task already regenerated
        
        report = await compute_expensive_report()  # 5 seconds
        cache.set("expensive_report", report, ex=300)
        return report
```

---

## 20. Connection Pool Exhaustion

### What Happens

Each service instance has a pool of connections to the cache cluster. Under high load or stampede conditions, all connections are used and new requests wait (or fail).

```
Connection pool: max_connections = 100

Normal: 30 active connections → everything works
Stampede: 1000 concurrent cache operations → 100 connections saturated
          → 900 requests waiting in queue
          → Queue grows faster than connections free up
          → Timeout → errors cascade

Even if the cache is fast, the connection pool is the bottleneck.
```

### Solutions

| Solution | How |
|---|---|
| **Pipeline commands** | Batch multiple cache operations into one round-trip |
| **Connection pool sizing** | Size pool to expected peak concurrency, not average |
| **Connection pool per shard** | In clustered Redis, separate pools per shard |
| **Fail fast** | Short connection timeout (50-100ms). Better to fail fast than queue forever. |
| **Request coalescing** | Multiple requests for the same key share one cache lookup |

---

## 21. Summary Matrix

```
┌──────────────────────────┬─────────────────────┬───────────────────────────┐
│ Challenge                │ Severity            │ Primary Solution          │
├──────────────────────────┼─────────────────────┼───────────────────────────┤
│ Cache Stampede           │ 🔴 Critical          │ Distributed lock + jitter │
│ Cache Avalanche          │ 🔴 Critical          │ TTL jitter                │
│ Cache Penetration        │ 🔴 Critical          │ Bloom filter + null cache │
│ Cache Breakdown          │ 🔴 Critical          │ Lock + early refresh      │
│ Cache Poisoning          │ 🔴 Critical          │ Delayed double delete     │
│ DB Inconsistency Race    │ 🔴 Critical          │ Delete-after-write + TTL  │
│ Cascading Failure        │ 🔴 Critical          │ Circuit breaker           │
│ Split Brain              │ 🟠 High              │ CP topology choice        │
│ Cold Start               │ 🟠 High              │ Cache warming / pre-cache │
│ Hot Key                  │ 🟠 High              │ Local cache + key split   │
│ Big Key                  │ 🟠 High              │ Chunking + UNLINK        │
│ Data Collisions          │ 🟠 High              │ CAS / queue writes       │
│ Multi-Layer Stale Data   │ 🟡 Medium            │ Coordinated invalidation  │
│ Memory Fragmentation     │ 🟡 Medium            │ Active defrag            │
│ Write Amplification      │ 🟡 Medium            │ Event-driven invalidation │
│ TTL Misconfiguration     │ 🟡 Medium            │ Per-type TTL + jitter    │
│ Dogpile Effect           │ 🟡 Medium            │ Semaphore + early refresh │
│ Serialization Overhead   │ 🟢 Low (but sneaky)  │ Binary format (protobuf) │
│ Capacity Misplanning     │ 🟢 Low (but costly)  │ Working set analysis     │
│ Connection Pool Exhaust  │ 🟢 Low (but sudden)  │ Pool sizing + pipelining │
└──────────────────────────┴─────────────────────┴───────────────────────────┘
```

### The Golden Rules

1. **Never set the same TTL on all keys.** Always add jitter.
2. **Never trust a cache for strong consistency.** Design for eventual consistency.
3. **Always have a fallback.** Cache is an optimization, not a requirement.
4. **Delete cache entries; don't update them.** Deletion is idempotent, updates race.
5. **Monitor hit rate, not just latency.** A fast cache with 20% hit rate is useless.
6. **Size your cache for the working set, not the average.** Undersized cache = expensive paperweight.
7. **Test cache failure.** Kill Redis in staging. See what breaks. Fix it before production.
8. **Never use `KEYS *` in production.** O(N) scan blocks Redis. Use `SCAN` instead.
9. **Every cache layer is a consistency risk.** More layers = more ways to be wrong.
10. **The hardest problem in caching isn't caching — it's invalidation.**

---

*Related: [microservices-caching-strategies.md](./microservices-caching-strategies.md) for topology theory*
*Related: [pds-distributed-cache-deep-dive.md](./pds-distributed-cache-deep-dive.md) for Agoda's real-world implementation*
