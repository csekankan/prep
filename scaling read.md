# Scaling Reads — System Design Pattern Deep Dive

> Covers why read traffic dominates write traffic, the three-stage progression for
> handling it (optimize → replicate/shard → cache), the database/cache internals
> underneath each stage (buffer pools, MVCC, consistent hashing, eviction
> policies), the hot-key/stampede failure modes that show up once you *do* add
> caching, CQRS-style precomputed read models, real production architectures
> (Facebook TAO, Twitter fan-out, Netflix EVCache, LinkedIn Voldemort, Pinterest,
> DynamoDB DAX, Discord), and how it all maps onto the classic interview problems
> (Bitly, Ticketmaster, Instagram, YouTube, etc.).
> **If you're new to this pattern:** read [Section 1](#1-the-core-problem--why-reads-dominate) first, then jump straight to whichever "Problem Breakdown" matches your interview.

---

## Table of Contents

1. [The Core Problem — Why Reads Dominate](#1-the-core-problem--why-reads-dominate)
2. [The Solution Progression](#2-the-solution-progression)
3. [Stage 1 — Optimize Within Your Database](#3-stage-1--optimize-within-your-database)
4. [Stage 2 — Scale Your Database Horizontally](#4-stage-2--scale-your-database-horizontally)
5. [Stage 3 — Add External Caching Layers](#5-stage-3--add-external-caching-layers)
6. [The Hot Key Problem](#6-the-hot-key-problem)
7. [Cache Stampede (Thundering Herd on Expiry)](#7-cache-stampede-thundering-herd-on-expiry)
8. [Cache Invalidation — Doing It Right](#8-cache-invalidation--doing-it-right)
9. [CQRS & Precomputed Read Models](#9-cqrs--precomputed-read-models)
10. [Real-World Architecture Case Studies](#10-real-world-architecture-case-studies)
11. [When to Use / When Not to Use This Pattern](#11-when-to-use--when-not-to-use-this-pattern)
12. [Problem Breakdowns](#12-problem-breakdowns)
13. [Interview Deep-Dive Q&A](#13-interview-deep-dive-qa)
14. [Numbers to Know — Cheat Sheet](#14-numbers-to-know--cheat-sheet)
15. [Conclusion](#15-conclusion)

---

## 1. The Core Problem — Why Reads Dominate

### The imbalance

```
Instagram feed load:
  1 photo posted per day       (1 write)
  100+ read operations         (metadata, user info, likes, comment previews)
  ── just to render ONE feed open ──

Typical read:write ratios:
  General apps          ~10:1
  Content-heavy apps     ~100:1  (Twitter, YouTube, Amazon product pages)
```

For every tweet posted, thousands read it. For every product uploaded, hundreds
browse it. YouTube serves billions of views daily on millions of uploads.
**Writes create data. Reads consume it — repeatedly, by orders of magnitude more people.**

### Why this is physics, not a bug

```
CPU        → finite instructions/sec
Memory     → finite bytes held in RAM
Disk I/O   → bounded by SSD write cycles / platter speed
Network    → finite bytes/sec out of a NIC
```

Once you hit these physical ceilings, no amount of clever application code
saves you — you must either (a) do less work per read, (b) spread the work
across more machines, or (c) avoid repeating the same work altogether
(caching). That's the entire pattern, condensed.

---

## 2. The Solution Progression

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. OPTIMIZE WITHIN YOUR DATABASE                                 │
│    Indexing → Hardware → Denormalization → Materialized Views   │
│    (cheapest, do this FIRST, most headroom is here)              │
├─────────────────────────────────────────────────────────────────┤
│ 2. SCALE HORIZONTALLY                                            │
│    Read Replicas → Database Sharding                              │
│    (needed past ~50k-100k reads/sec on one well-indexed DB)      │
├─────────────────────────────────────────────────────────────────┤
│ 3. ADD EXTERNAL CACHING LAYERS                                    │
│    App-level cache (Redis/Memcached) → CDN / Edge caching         │
│    (best perf, but adds staleness + invalidation complexity)      │
└─────────────────────────────────────────────────────────────────┘
```

Most candidates jump straight to "add Redis." Strong candidates show they
understand there's a progression, and justify *why* they're skipping straight
to caching if they do (e.g. "read/write ratio here is so extreme that caching
is a day-one requirement, not an optimization").

---

## 3. Stage 1 — Optimize Within Your Database

### Indexing

An index is a sorted lookup structure that points at rows in your actual
table — like a book's index instead of reading every page.

```
Without index (full table scan):           With index (index scan):
  O(n) — read every row                       O(log n) — binary-search-like lookup
  1,000,000 rows scanned                       ~20 index entries checked
```

```
Disk
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Page 1│ │Page 2│ │Page 3│ │Page 4│ │Page 5│ │Page 6│ │Page 7│
└──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
              ▲
              │ Step 3: fetch the page
Memory   ┌────┴────┐
         │  Index   │ ← Step 1: load index (small, fits in memory)
         └────┬────┘
              │ Step 2: look up the right page from the index
```

- **B-tree** — the default for most engines; great for range queries,
  sorting, and general lookups.
- **Hash index** — fastest for exact-match lookups (`WHERE id = 5`), useless
  for ranges or sorting.
- **Specialized** — full-text indexes (search), geospatial indexes
  (`GEOHASH`/R-tree for "near me" queries).

**Rule of thumb:** index every column you frequently `WHERE`, `JOIN ON`, or
`ORDER BY`. The old fear of "too many indexes slows down writes" is
dramatically overblown on modern hardware — **under-indexing kills more
real applications than over-indexing ever does.** In an interview, add
indexes confidently for your access patterns.

```sql
-- Before: full table scan
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';
-- Seq Scan on users (cost=0.00..412000.00 rows=1)

CREATE INDEX idx_users_email ON users(email);

-- After: index scan
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';
-- Index Scan using idx_users_email (cost=0.43..8.45 rows=1)
```

Composite index column order matters: an index on `(status, created_at)`
helps queries filtering on `status` alone AND `status + created_at` together,
but does **not** help a query that filters on `created_at` alone.

### Hardware upgrades (vertical scaling)

```
Database (db.m6g.large)          Database (db.r6g.4xlarge)
  8 GB RAM                  →      128 GB RAM
  100 GB Disk (spinning)    →      16 TB Disk (SSD)
```

- SSD vs spinning disk → 10-100x faster random I/O
- More RAM → more of the working set stays in memory, fewer disk hits
- Faster/more CPU cores → more concurrent queries handled

Boring, but often the fastest way to buy breathing room. Worth *mentioning*
in an interview, but it rarely satisfies the interviewer alone since it
sidesteps the actual design question.

### Denormalization

Normalization reduces redundancy via separate tables + joins. Read-heavy
systems flip this: **trade storage for speed** by storing redundant data so
reads become single-table lookups.

```sql
-- Normalized: 3-way join on every order page view
SELECT u.name, o.order_date, p.product_name, p.price
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.id = 12345;

-- Denormalized: single-table read
SELECT user_name, order_date, product_name, price
FROM order_summary
WHERE order_id = 12345;
```

```
Normalized                              Denormalized
┌────────┐ ┌────────┐ ┌────────┐        ┌──────────────────────────────┐
│ Users  │ │ Orders │ │Products│        │  order_summary                │
├────────┤ ├────────┤ ├────────┤   →    │  {name: Evan, location: ...,  │
│ Evan   │ │ Evan → │ │ Table  │        │   product: Table, cost: $100} │
│ Glenn  │ │  Table │ │ Chair  │        └──────────────────────────────┘
└────────┘ └────────┘ └────────┘        (no joins needed to read)
```

**Trade-off:** writes get more complex (update user name → update it
everywhere it's duplicated), but for a system reading far more than it
writes, that's an easy trade. Always check your read/write ratio before
denormalizing — if writes are frequent too, the update complexity may not
be worth it.

### Materialized views

Precompute expensive aggregations once (via a background job) instead of
recomputing them on every request.

```sql
-- Expensive on every page load:
SELECT p.id, AVG(r.rating) AS avg_rating
FROM products p JOIN reviews r ON p.id = r.product_id
GROUP BY p.id;

-- Precomputed once, read many times:
CREATE MATERIALIZED VIEW product_ratings AS
SELECT p.id, AVG(r.rating) AS avg_rating
FROM products p JOIN reviews r ON p.id = r.product_id
GROUP BY p.id;
```

Especially powerful for analytics-style queries across large datasets
(dashboards, "trending" lists, leaderboards).

### Database internals — what actually happens when a read executes

Understanding the machinery beneath "add an index" makes you far more
credible in a deep dive. Here's what a single `SELECT` actually does inside
a relational engine like Postgres or MySQL/InnoDB:

```
1. Parser        → SQL text becomes an abstract syntax tree
2. Planner/       → Optimizer picks an execution plan (seq scan vs index
   Optimizer         scan vs index-only scan) using table statistics
3. Executor       → Walks the chosen plan, requesting pages
4. Buffer Pool    → "Is this page already in memory?"
                      HIT  → return it directly, no disk I/O
                      MISS → ask the storage layer to fetch it
5. Storage/Disk   → Reads the 8KB/16KB page from disk into the buffer pool
6. Row filtering  → Executor applies WHERE predicates on rows in the page
```

```
┌──────────────────────────── Database Process ────────────────────────────┐
│                                                                             │
│   ┌───────────┐     ┌────────────┐     ┌───────────────────────────┐    │
│   │  Parser    │ →   │  Planner    │ →   │  Executor                   │    │
│   └───────────┘     └────────────┘     └─────────────┬─────────────┘    │
│                                                          │                   │
│                                          ┌───────────────▼───────────────┐  │
│                                          │  Buffer Pool (in RAM)          │  │
│                                          │  recently-used pages cached    │  │
│                                          └───────────────┬───────────────┘  │
│                                       page hit │              │ page miss   │
│                                     (fast, no disk) return    ▼             │
│                                                          ┌──────────┐       │
│                                                          │   Disk    │       │
│                                                          └──────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

**The buffer pool is the single biggest lever you have besides indexing.**
It's just an LRU-ish cache of disk pages living inside the DB process's own
memory. This is *why* "add more RAM" (vertical scaling) works so well for
reads: a bigger buffer pool means more of your working set never touches
disk at all. A database with a 128GB buffer pool serving a 40GB active
dataset essentially never hits disk for reads — it behaves like an
in-memory database even though it's "just" Postgres.

**MVCC (Multi-Version Concurrency Control)** is *why* reads don't block on
writes in Postgres/MySQL. Instead of readers waiting for writer locks, each
row keeps multiple versions tagged with transaction IDs; a read simply sees
the version that was committed at the time its own transaction started.
This is what lets a long-running analytical read run concurrently with
writes without either blocking the other — extremely relevant when you're
explaining why reads scale independently of write throughput in the same DB.

**Write-Ahead Log (WAL)** is how the engine stays durable and crash-safe:
every change is appended to a sequential log *before* it's applied to the
actual data pages. This log is also the exact mechanism that powers
**physical streaming replication** to read replicas (Section 4) — a
follower is, at its core, a process continuously replaying the leader's WAL.

**Covering indexes** — an index that includes every column the query needs
(not just the filter column) lets the engine answer entirely from the index
without ever touching the underlying table (an "index-only scan"). This is
one of the highest-leverage, most underused indexing tricks:

```sql
-- Query only needs user_id and email
SELECT user_id, email FROM users WHERE status = 'active';

-- A normal index on (status) still requires a lookup back to the table
-- for `email`. A covering index avoids that extra hop entirely:
CREATE INDEX idx_users_status_covering ON users(status) INCLUDE (user_id, email);
```

### Connection pooling & the N+1 query problem

Two extremely common "invisible" read scaling killers that have nothing to
do with indexes:

**Connection pooling.** Every DB connection costs real memory on the server
(Postgres: several MB per connection for its backend process) and the
handshake/auth to open one isn't free. An application that opens a fresh
connection per request collapses under concurrency long before it runs out
of CPU. The fix is a connection pool — a fixed, reused set of open
connections shared across requests (via `pgbouncer`/`pgpool` in front of
Postgres, or a client-side pool like `SQLAlchemy`'s `QueuePool`, HikariCP in
the JVM world, or Node's `pg-pool`).

```
Without pooling:                     With pooling (e.g. PgBouncer):
  Request → open conn → query        Request → borrow conn from pool → query
          → close conn                        → return conn to pool
  (connection setup cost paid        (connection setup cost paid ONCE,
   on every single request)           amortized across thousands of requests)
```

`PgBouncer` in *transaction* pooling mode can let a handful of real DB
connections serve thousands of concurrent app-level "connections," because
most connections are idle between queries — a database sized for 100
physical connections can easily back an app with 5,000 concurrent
short-lived transactions.

**The N+1 query problem.** This is the single most common accidental
read-amplifier in real codebases, ORMs especially:

```python
# N+1 in the wild: 1 query for posts, then N more for each post's author
posts = db.query("SELECT * FROM posts LIMIT 20")     # 1 query
for post in posts:
    author = db.query(                                 # 20 MORE queries!
        "SELECT * FROM users WHERE id = ?", post.author_id
    )
```

A page that "feels" like one read is secretly 21 round trips to the
database — and this is exactly the kind of hidden read amplification the
Instagram feed example in Section 1 is describing under the hood. Fixes, in
order of preference:

```python
# Fix 1: batch it into a single query with a JOIN or WHERE IN
author_ids = [p.author_id for p in posts]
authors = db.query("SELECT * FROM users WHERE id IN (?)", author_ids)  # 1 query total

# Fix 2 (GraphQL/microservices world): DataLoader-style batching + caching
# collects individual .load(id) calls made during one request tick into
# a single batched fetch, then fans the results back out to each caller.
class UserLoader(DataLoader):
    async def batch_load_fn(self, user_ids: list[str]) -> list[dict]:
        users = await db.query("SELECT * FROM users WHERE id IN (?)", user_ids)
        by_id = {u["id"]: u for u in users}
        return [by_id[uid] for uid in user_ids]   # preserve input order
```

DataLoader-style batching is effectively **request coalescing (Section 6)
applied at the per-request level** instead of across concurrent users — the
same core idea (don't issue the same/overlapping work N times when one
batched call will do) shows up at every layer of the stack.

---

## 4. Stage 2 — Scale Your Database Horizontally

**Rule of thumb:** consider horizontal scaling (or caching) once you exceed
roughly **50,000–100,000 reads/sec** on a single, properly indexed database.
This is a rough estimate — good enough to justify a decision in an interview,
but the real number depends on data model, hardware, and access patterns.

### Read replicas (leader-follower replication)

```
                    ┌──────────────┐
        writes  →   │   Leader      │
                    │  (all data)   │
                    └──────┬───────┘
             replication (sync or async)
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │ Follower 1   │    │ Follower 2   │    │ Follower 3   │
 │ (all data)   │    │ (all data)   │    │ (all data)   │
 └─────────────┘    └─────────────┘    └─────────────┘
        ▲                  ▲                  ▲
        └──────────── reads spread across ─────┘
```

- All **writes** go to the leader.
- **Reads** can be served by any follower → load distributed.
- Bonus: if the leader dies, promote a follower → reduces downtime.

**Replication lag** is the central trade-off:
- **Synchronous** — leader waits for follower ack before confirming the
  write. Strongly consistent, but adds write latency and reduces availability
  if a follower is slow/down.
- **Asynchronous** — leader confirms immediately, replicates in the
  background. Fast writes, but a user might not see their *own* write if
  routed to a lagging replica (classic "why did my comment disappear after I
  posted it" bug — a **read-your-writes consistency** problem).

### Database sharding

Read replicas copy the *whole* dataset — they don't shrink it. If the
dataset itself is too large for fast queries even with indexes, shard it.

**Functional sharding** — split by business domain:

```
        ┌────────┐
        │ Client  │
        └───┬────┘
            ▼
       ┌─────────┐
       │  Server  │
       └──┬──┬──┬─┘
   Fetch Post│  │Fetch Likes
        ▼    ▼Fetch User  ▼
     ┌─────┐ ┌─────┐ ┌─────┐
     │DB1  │ │DB2  │ │DB3  │
     │Posts│ │Users│ │Likes│
     └─────┘ └─────┘ └─────┘
```
Now a "fetch user profile" query only ever touches the smaller Users DB.

**Geographic sharding** — split by region:

```
   ┌───────┐  ┌────────┐  ┌───────┐  ┌────────┐
   │ US DB │  │LATAM DB│  │ASIA DB│  │AFRICA DB│
   └───────┘  └────────┘  └───────┘  └────────┘
```
Users read from the nearest region → lower latency + load spread across
independent databases.

**Caveat:** sharding is primarily a *write*-scaling technique and adds real
operational complexity (cross-shard joins, rebalancing, hot shards). For pure
read scaling, adding caching is usually easier and more effective — reach for
sharding when the *dataset size itself* (not just read QPS) is the
bottleneck.

### How you actually route to the right shard/replica: consistent hashing

Naive sharding (`shard = hash(key) % num_shards`) works fine until you add
or remove a shard — then `% num_shards` changes for almost every key, and
you have to re-shuffle nearly your entire dataset. **Consistent hashing**
solves this by placing both shards and keys on the same conceptual ring, so
adding/removing a node only remaps the keys immediately next to it.

```
                     hash ring (0 → 2^32-1, wraps around)

                              ┌───┐
                        ┌────▶│ B │
                    ┌───┘     └─┬─┘
              ┌───┐ │            │
              │ A │◀┘            ▼
              └─┬─┘          ┌───┐
                 │            │ C │
                 ▼            └─┬─┘
             key "x" hashes      │
             here → walk         ▼
             clockwise to     ┌───┐
             first node → B   │ D │
                              └───┘

Add a new node E between C and D:
  Only keys that hashed into the C→D arc move to E.
  Everything else (A, B, and the rest of C, D's ranges) is untouched.
```

This is exactly how Amazon **DynamoDB**, **Cassandra**, **Riak**, and
**Redis Cluster** decide which physical node owns a given key, and it's why
a distributed cache/DB can scale its node count up or down without a full
data reshuffle. In practice, each physical node is given **multiple points**
on the ring ("virtual nodes"/vnodes) so that when a node does leave, its load
is spread evenly across *many* remaining nodes rather than dumping it all on
whichever single node happens to be clockwise-next.

### Read consistency levels & quorum reads (Dynamo-style systems)

Once data is replicated across N nodes (whether that's Postgres followers or
a Dynamo-style store), "how many replicas must agree before we return a
read" becomes a tunable trade-off, not a fixed answer:

```
N = 3 replicas hold a copy of the data.

Read from 1 replica  (R=1):  fastest, but might return stale data if that
                              replica hasn't received the latest write yet.
Read from a QUORUM   (R=2):  W + R > N guarantees the read set overlaps
                              with the write set → always sees the latest
                              write. This is "strong-ish" consistency
                              without needing ALL N replicas to respond.
Read from ALL        (R=N):  strongest guarantee, slowest, least available
                              (any one replica being down blocks the read).
```

This `W + R > N` rule (used by Dynamo, Cassandra, Riak, and Cosmos DB) is
the formal version of the sync-vs-async replication trade-off from the
read-replica discussion above — it just makes the "how many copies must
agree" dial explicit and tunable per-query instead of being a single global
setting for the whole database.

---

## 5. Stage 3 — Add External Caching Layers

Access patterns are almost always skewed — millions read the same viral
tweet, thousands view the same popular product. You're repeatedly querying
for **identical data that rarely changes.** Caches exploit exactly this.

```
Database read:  disk I/O + query execution  → tens of milliseconds
Cache read:      pre-computed value from RAM → sub-millisecond
```

### Application-level caching (cache-aside pattern)

```
        ┌────────┐        1. check cache first        ┌───────┐
        │ Client  │ ─────────────────────────────────→ │ Cache  │
        └───┬────┘                                     └───┬───┘
            │                                    hit ──────┘  → return
            ▼
        ┌────────┐   2. on cache MISS, check DB    ┌──────────┐
        │ Server  │ ───────────────────────────────→│ Database  │
        └────────┘   3. populate cache for next time└──────────┘
```

```python
async def get_user_profile(user_id: str) -> dict:
    cached = await cache.get(f"user:{user_id}")
    if cached is not None:
        return cached  # sub-millisecond hit

    profile = await db.fetch_user(user_id)   # tens of ms on miss
    await cache.set(f"user:{user_id}", profile, ttl=300)
    return profile
```

Popular data (celebrity profiles) stays cached continuously due to constant
access. Rarely-viewed data only gets cached when touched, then expires via
TTL — the cache naturally mirrors your access-pattern skew.

### CDN and edge caching

```
        ┌────────┐
        │ Client  │  ── read from closest CDN edge
        └───┬────┘
            ▼
   ┌─────┐ ┌─────┐ ┌─────┐        (only cache MISSES travel
   │ CDN │ │ CDN │ │ CDN │    →     all the way back to origin)
   │Tokyo│ │ NYC │ │ LDN │
   └──┬──┘ └──┬──┘ └──┬──┘
      └────────┴────────┘
               ▼
        ┌────────────┐
        │ Origin Server │
        └────────────┘
```

A Tokyo user hitting a Tokyo edge cache goes from ~200ms round trip to a
distant origin down to **<10ms**, and the origin sees zero load for that
request. For read-heavy apps, CDN caching can cut origin load by **90%+**.

**Only cache multi-reader content on a CDN** — product pages, public posts,
search results. Never cache user-specific data (private messages, personal
settings) at the edge; a single reader gets zero benefit from a cache hit
rate and you're just adding staleness risk for nothing.

### Cache eviction policies — what gets thrown out when the cache is full

RAM is finite, so once a cache is full, adding a new entry means evicting
an old one. *Which* one you evict has a massive effect on hit rate:

```
LRU (Least Recently Used)
  Evict whichever key hasn't been touched in the longest time.
  Simple (doubly-linked list + hash map, O(1) get/put). Redis and
  Memcached both default to LRU-family eviction.
  Weakness: a single large sequential scan ("scan pollution") can flush
  your entire hot working set out of cache in one pass.

LFU (Least Frequently Used)
  Evict whichever key has been accessed the fewest total times.
  Better for stable "always-popular" hot sets, but slow to adapt when
  what's popular changes (a key that WAS popular yesterday can look
  falsely "hot" and refuse to be evicted) — needs a decay/aging factor.

ARC (Adaptive Replacement Cache)
  Used internally by ZFS and some DB buffer pools. Dynamically balances
  between recency (LRU) and frequency (LFU) based on observed workload,
  rather than committing to one policy up front.

W-TinyLFU (used by Caffeine, the standard Java cache library)
  Approximates LFU cheaply using a compact frequency sketch, combined
  with a small LRU "admission window" so brand-new items get a fair
  chance before being judged on frequency. Consistently outperforms
  plain LRU/LFU in published benchmarks and is the modern default for
  high-performance embedded caches.
```

```python
# Minimal LRU cache — the data structure every "design an LRU cache"
# interview question and every real cache library builds on
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.store: OrderedDict[str, object] = OrderedDict()

    def get(self, key: str):
        if key not in self.store:
            return None
        self.store.move_to_end(key)   # mark as recently used
        return self.store[key]

    def put(self, key: str, value) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)   # evict least-recently-used
```

Redis in practice uses an **approximated LRU** (samples a handful of random
keys and evicts the oldest among them) rather than true LRU, because
maintaining a perfectly ordered access list for millions of keys costs more
memory/CPU than the accuracy gain is worth — a good example of trading
theoretical precision for real-world throughput.

### Cache cluster architecture — how Redis/Memcached scale past one box

A single Redis or Memcached node is bounded by one machine's RAM and one
core's (or a few cores') throughput. Scaling the cache itself follows the
same consistent-hashing idea from Section 4:

```
Client-side hashing (classic Memcached approach):
  Client library hashes the key itself and picks which of N Memcached
  nodes to talk to. The nodes don't know about each other at all — no
  cluster protocol, no coordination. Simple, but the client must be kept
  in sync with the node list, and rebalancing on node add/remove is
  entirely the client library's problem (usually solved with the same
  consistent-hashing ring from Section 4).

Redis Cluster (server-side):
  Keyspace is split into 16,384 fixed "hash slots". Each node owns a
  subset of slots. A client can ask ANY node "who owns this key's slot?"
  and gets redirected (MOVED) to the right node. Each shard can also have
  its own replicas for read scaling + failover, so a "Redis Cluster" node
  count is really (shards × replication factor).
```

```
                Redis Cluster (3 shards, 1 replica each)

   Shard A               Shard B               Shard C
  slots 0-5460          slots 5461-10922      slots 10923-16383
 ┌───────────┐          ┌───────────┐          ┌───────────┐
 │ Primary A  │          │ Primary B  │          │ Primary C  │
 └─────┬─────┘          └─────┬─────┘          └─────┬─────┘
       │ replicates            │ replicates            │ replicates
       ▼                       ▼                       ▼
 ┌───────────┐          ┌───────────┐          ┌───────────┐
 │ Replica A  │          │ Replica B  │          │ Replica C  │
 │ (reads)    │          │ (reads)    │          │ (reads)    │
 └───────────┘          └───────────┘          └───────────┘
```

This is the same leader-follower idea from Section 4's read replicas,
applied to the cache layer itself — read traffic can be spread across cache
replicas exactly like DB read traffic is spread across DB followers, and a
replica can be promoted if its primary dies.

---

## 6. The Hot Key Problem

*"How do you handle millions of concurrent reads for the same cached key?"*

A celebrity posts something. Your cache, normally doing 50,000 req/s, is
suddenly asked for **one key** 500,000 times/sec. Even though the data is in
RAM, a single cache node's CPU/network can't serialize and ship that key out
half a million times a second — traditional caching assumes load spreads
across *many* keys, and that assumption just broke.

### Fix 1 — Request coalescing

Combine many concurrent requests for the *same key* into a single backend
fetch; all waiters share the one result.

```python
class CoalescingCache:
    def __init__(self):
        self.inflight: dict[str, asyncio.Future] = {}

    async def get(self, key: str):
        if key in self.inflight:
            return await self.inflight[key]      # piggyback on the in-flight fetch

        future = asyncio.Future()
        self.inflight[key] = future
        try:
            value = await fetch_from_backend(key)
            future.set_result(value)
            return value
        finally:
            del self.inflight[key]
```

This bounds backend load to **N**, where N = number of application servers
doing the coalescing — not the number of end users, which could be millions.

### Fix 2 — Cache key fanout

When even coalescing isn't enough, spread the *same* value across multiple
cache keys so requests fan out across shards instead of hammering one:

```python
def hot_key_for(base_key: str, replicas: int = 10) -> str:
    return f"{base_key}:{random.randint(1, replicas)}"

# writer: store the same value under N keys
for i in range(1, replicas + 1):
    await cache.set(f"feed:taylor-swift:{i}", value, ttl=60)

# reader: pick one at random
key = hot_key_for("feed:taylor-swift")
value = await cache.get(key)
```

500,000 req/s ÷ 10 replicated keys = 50,000 req/s per key — a load any
single cache shard can absorb. **Trade-off:** more memory usage (N copies)
and more complex invalidation (must clear all N copies) — a small price to
pay to stay online during a hot-key spike.

---

## 7. Cache Stampede (Thundering Herd on Expiry)

*"What happens when a hot cache entry expires and everyone rebuilds it at once?"*

```
Cache entry TTL = 1 hour, 100,000 req/s, all served from cache.
At minute 60: entry expires → ALL 100,000 req/s simultaneously miss
             → all 100,000 hit the DB at once
             → DB sized for ~1,000 qps (normal miss rate) falls over
```

This is a **self-inflicted DDoS**: cache expiration is binary (there one
moment, gone the next), so a popular key creates a synchronized stampede the
instant it expires.

### Fix 1 — Distributed lock on rebuild

Only the first request that notices the miss rebuilds; everyone else waits.
Protects the backend, but is fragile — a slow/failed rebuild means thousands
of requests time out waiting on the lock, requiring careful fallback logic.

### Fix 2 — Probabilistic early refresh (preferred)

Serve the cached value while occasionally, probabilistically, refreshing it
in the background **before** it actually expires — spreading refreshes over
a window instead of a single instant.

```python
import random
import time

async def get_with_early_refresh(key: str, ttl: int, rebuild_fn):
    entry = await cache.get_with_meta(key)   # (value, created_at)
    if entry is None:
        value = await rebuild_fn()
        await cache.set(key, value, ttl=ttl)
        return value

    value, created_at = entry
    age = time.time() - created_at
    # chance of early refresh grows as the entry approaches expiry
    refresh_probability = max(0, (age / ttl) - 0.8) * 5   # ramps 0 → 1 in last 20% of TTL

    if random.random() < refresh_probability:
        asyncio.create_task(_refresh_in_background(key, ttl, rebuild_fn))

    return value  # always return the (possibly slightly stale) cached value immediately
```

At minute 50 of a 60-minute TTL, maybe 1% of requests trigger a refresh; at
minute 59, maybe 20% do. Instead of 100,000 simultaneous DB hits at minute
60, refreshes spread across the last ~10-15 minutes, and most users still
get an instant cache hit.

### Fix 3 — Scheduled background refresh (for your most critical keys)

For content that truly cannot risk a stampede or serve even slightly stale
probabilistic data (homepage, top navigation), run a background job that
proactively refreshes the entry every N minutes, well before its TTL — no
user request ever triggers a rebuild. Costs some wasted work refreshing data
nobody may request that instant, but guarantees zero stampedes for your
hottest content.

---

## 8. Cache Invalidation — Doing It Right

Data is often cached in multiple layers simultaneously — app cache (Redis),
CDN edge, browser — and invalidating all of them consistently is famously
hard.

### The naive approach and its problems

"Delete the cache entry after a write" sounds simple but breaks down:
- Which caches do you delete from — app, CDN, browser?
- What if the invalidation call itself fails?
- **Race condition:** a request that started *before* your write lands might
  finish computing stale data and re-populate the cache *after* your delete —
  now you're serving stale data again, indefinitely.

### Strategy comparison

| Strategy | How it works | Best for | Downside |
|---|---|---|---|
| **TTL expiration** | Fixed lifetime per entry | Predictable staleness tolerance | Serves stale data until expiry |
| **Write-through** | Update/delete cache synchronously on write | Strong consistency needs | Adds write latency |
| **Write-behind** | Queue invalidation, process async | Write-latency sensitive systems | Window of staleness |
| **Tagged invalidation** | Invalidate all entries sharing a tag (`user:123:posts`) | Complex, related-entry dependencies | Must maintain tag graph |
| **Versioned keys** | Bump a version number, old keys become unreachable | Single-entity data (profiles, products) | Extra lookup, key churn |

Most production systems layer these: a short TTL (5-15 min) as a blanket
safety net, plus active invalidation for critical entities (inventory,
account settings). Less critical data (recommendation scores) can rely on
TTL alone. **Derive your TTL from your staleness requirement**, not the other
way around — "search results must be ≤30s stale" *is* your TTL.

### Cache versioning, in depth

Instead of deleting stale entries (racy), make them **unreachable** by
changing the key whenever the underlying row changes.

```
event:123:v42     ← before update
event:123:v43     ← after update (v42 is simply never read again)
```

**On write** (single DB transaction):
1. `BEGIN`
2. `UPDATE events SET address = ... WHERE id = 123`
3. `UPDATE events SET version = version + 1 WHERE id = 123`
4. `COMMIT`
5. Write the new data to `event:123:v43`

**On read:**
1. Read the (cached, tiny) version key for `event:123` → `43`
2. Read `event:123:v43` from cache
3. On miss, fetch from DB and populate `event:123:v43`

```python
async def get_event(event_id: int) -> dict:
    version = await cache.get(f"event:{event_id}:version")
    if version is None:
        version = await db.get_version(event_id)
        await cache.set(f"event:{event_id}:version", version, ttl=60)

    key = f"event:{event_id}:v{version}"
    cached = await cache.get(key)
    if cached is not None:
        return cached

    data = await db.get_event(event_id)
    await cache.set(key, data, ttl=3600)
    return data
```

**Why it works:** no delete-then-race window — the DB's atomic version
increment is the single source of truth, so a "late writer" can never
overwrite fresher data with stale data under the same key; readers simply
move to the new version once it exists. **Trade-off:** two cache lookups per
read (version + data), and old versions accumulate until their own TTL
expires them — this shines for single-entity lookups (profiles, listings)
but doesn't directly help computed/aggregate data like feeds or search
results, where "what changed" isn't a single row's version.

### Deleted-items cache (for computed/aggregate data)

For feeds, search results, or anything aggregated across many rows,
per-item versioning doesn't cleanly apply. Instead, maintain a **small,
fast cache of recently deleted/hidden/changed IDs.** When serving a large
cached feed or result set, filter out anything present in this small
cache — giving you mostly-correct data immediately while the bigger
structure is properly rebuilt/invalidated in the background. Very effective
for content moderation and privacy-driven removals.

### CDN-specific invalidation

CDN invalidation must propagate across potentially hundreds of edge
locations — CDN purge APIs help, but propagation isn't instant. For
truly critical updates, use cache-control headers to bypass CDN caching
entirely (trading performance for consistency); for less critical content,
keep a shorter edge TTL while your app-level cache keeps a longer one.

---

## 9. CQRS & Precomputed Read Models

Everything so far has been about making an *existing* read path faster.
**CQRS (Command Query Responsibility Segregation)** is the more radical
move: stop trying to serve reads and writes from the same schema at all.

```
Traditional (single model):                CQRS (split models):

   ┌─────────┐                                ┌─────────┐
   │  App     │                                │  App     │
   └───┬─────┘                                └───┬─────┘
       │ read + write                    write     │      read
       ▼                                    ▼               ▼
  ┌───────────┐                       ┌──────────┐   ┌────────────────┐
  │ One schema │                       │  Write DB  │   │  Read Model(s)  │
  │ (normalized│                       │ (normalized│   │ (denormalized,  │
  │  for       │                       │  for       │   │  shaped exactly │
  │  writes)   │                       │  writes)   │──▶│  for each query)│
  └───────────┘                       └──────────┘   └────────────────┘
                                              events/CDC stream
```

The write side stays normalized and transactionally correct (it's optimized
for correctness, not query convenience). Every write also emits an event
(often via **Change Data Capture / CDC** — e.g. Debezium tailing a database's
WAL/binlog) that asynchronously updates one or more **read models**, each
shaped exactly for a specific query pattern:

```
Write:  INSERT INTO orders (...)  -- normalized, ACID, one source of truth

CDC picks up the change from the WAL/binlog and asynchronously projects
it into purpose-built read models:
  → order_summary_view      (denormalized, for the "view my order" page)
  → user_order_count_cache  (a running counter, for profile badges)
  → search_index            (Elasticsearch document, for order search)
```

This is denormalization (Section 3) and materialized views taken to their
logical extreme: instead of one denormalized table bolted onto your OLTP
schema, you maintain **N independently-scaled read models**, each tuned for
one access pattern, updated asynchronously from a single write path. The
cost is the same one every technique in this document eventually pays:
**eventual consistency** — the read model lags the write by however long
the CDC pipeline takes (usually milliseconds to low seconds).

CQRS is the architecture underneath why Facebook's TAO, Twitter's timeline
cache, and Netflix's viewing-history services all look the way they do —
see the case studies below.

---

## 10. Real-World Architecture Case Studies

Reading how actual production systems at scale solved this exact problem
tends to stick better than any abstract pattern description. These are
simplified but directionally accurate descriptions of well-documented public
architectures.

### Facebook TAO — the canonical "cache is the database" architecture

Facebook's social graph (friends, likes, comments, check-ins) is read
roughly **two orders of magnitude** more than it's written, at a scale where
even MySQL read replicas alone weren't enough. **TAO** (The Associations and
Objects store) sits in front of a sharded MySQL fleet as a graph-aware
caching layer:

```
   ┌────────┐    read/write     ┌───────────────┐
   │ Clients │ ────────────────▶ │ TAO Cache Tier │  (huge fleet, in-memory,
   └────────┘                   └──────┬────────┘   graph-shaped: objects +
                                        │ on miss / async write-through   "associations")
                                        ▼
                               ┌─────────────────┐
                               │ Sharded MySQL     │  (source of truth)
                               │ (regional masters)│
                               └─────────────────┘
```

Key ideas: reads almost always hit the cache tier and never touch MySQL at
all (this is CQRS's read-model idea, but the read model *is* a cache, not
another database). Writes go through the cache tier too (write-through),
which then asynchronously replicates to a regional master and out to other
regions. TAO explicitly favors *availability and low latency* over strict
consistency for most social-graph reads — showing a friend's slightly-stale
like count is a perfectly acceptable trade-off at Facebook's scale.

### Twitter/X — timeline caching & fan-out on write

A tweet from a hot account needs to appear in millions of followers' home
timelines almost instantly. Twitter's historical approach: on every tweet, a
service asynchronously **pushes ("fans out") the tweet ID into a
precomputed timeline list in Redis for every one of that user's followers**
— so reading a timeline is just "read this one pre-built Redis list," not
"compute a personalized ranking across everyone I follow, live, on every
page load."

```
Tweet posted by @user (10M followers)
        │
        ▼
 Fan-out service: for each follower_id in followers(@user):
        │              → LPUSH timeline:{follower_id} tweet_id
        ▼
 Redis: timeline:alice → [tweet_9, tweet_8, tweet_7, ...]
        timeline:bob   → [tweet_9, tweet_6, tweet_5, ...]
```

**The celebrity problem:** fanning out to 10M+ followers on every tweet from
a huge account is itself enormously expensive — this is why large platforms
use a **hybrid fan-out**: fan-out-on-write for normal accounts (cheap,
followers are few), but fan-out-on-*read* for celebrity accounts (merge
their tweets into a reader's timeline live, at read time, since there are
far fewer celebrities being read than there are their followers doing the
reading).

### Netflix — EVCache and multi-region read-through caching

Netflix built **EVCache** (an open-sourced wrapper around Memcached) to
solve read scaling across a globally distributed, multi-AWS-region
footprint. The core techniques it layers on top of plain Memcached map
directly onto this document's sections: client-side **consistent hashing**
across a Memcached cluster (Section 5), **replication across AWS
availability zones** so a single zone outage doesn't cause a cache-miss
stampede (Section 7), and aggressive use of **read-through/cache-aside**
for metadata (title info, artwork, personalization scores) that changes
rarely relative to how often it's viewed.

### LinkedIn — Espresso & Voldemort as precomputed read stores

LinkedIn's **Voldemort** (a Dynamo-style key-value store) is used
specifically to serve **precomputed, offline-batch-generated** read data —
things like "people you may know" recommendations, computed by a nightly
Hadoop job and then bulk-loaded into Voldemort purely for fast online reads.
This is CQRS in its purest form: the *write* path is an entirely offline
batch pipeline, and the *read* path is a key-value store optimized for
nothing but low-latency point lookups of precomputed results.

### Pinterest — sharded MySQL + Memcache + feed fan-out

Pinterest's classic architecture combines several of this document's
techniques at once: **functional + hash-based sharding** of MySQL for pins
and boards (Section 4), a large **Memcache fleet** in front of MySQL for
hot reads (Section 5), and **fan-out-on-write for home feeds** (similar to
Twitter's approach) so opening the home feed is a fast read of a
precomputed structure rather than a live query across everyone you follow.

### Amazon DynamoDB Accelerator (DAX) — a managed read-through cache

DAX is a fully-managed, DynamoDB-API-compatible in-memory cache that sits
directly in front of DynamoDB with **zero application code changes** for
existing DynamoDB clients — it's a productized version of exactly the
cache-aside pattern from Section 5, but implemented as a transparent proxy
rather than something your application code has to manage (check cache,
fall back to DB, populate cache) by hand.

### Discord — read/write splitting under extreme fan-out

Discord's largest servers (channels) can have hundreds of thousands of
members reading the same handful of active channels simultaneously —
another hot-key problem (Section 6) at the "channel" granularity instead of
a single record. Discord has published on moving hot data (recent messages,
read-state) into Cassandra/ScyllaDB specifically because it handles
extremely read-heavy, high-fan-out access patterns with predictable latency
better than a single relational primary would, effectively choosing
horizontal, replica-heavy scaling (Section 4) as the primary lever rather
than layering a cache in front of a relational database.

### The common thread

Every one of these systems reaches the same three conclusions, just tuned
to their own read/write ratio and consistency needs:
1. The **source of truth stays small, normalized, and correct** (sharded
   MySQL, DynamoDB, an offline batch job).
2. **Reads almost never touch it directly** — they hit a cache, a
   precomputed read model, or a purpose-built read-optimized store instead.
3. **Staleness is accepted deliberately and bounded**, not accidentally —
   every one of these companies made an explicit, documented decision about
   exactly how stale a read is allowed to be for each type of data.

---

## 11. When to Use / When Not to Use This Pattern

### Use it when
- Read/write ratio is high (10:1 or greater) — social feeds, product
  catalogs, URL shorteners, video platforms.
- Access is skewed — a small set of "hot" items get most of the traffic.
- Some staleness is tolerable (bounded by a clear non-functional requirement).

### Don't reach for it when
- **Write-heavy systems** — e.g. Uber driver location updates every few
  seconds; read/write ratio may be ~1:1 or 2:1. Focus on write scaling
  (sharding, write-optimized storage) instead.
- **Small scale** — "design for 1,000 users" doesn't need distributed
  caching. A single well-indexed DB handles thousands of QPS. Jumping
  straight to Redis + CDN here signals you're solving an imagined problem,
  not the stated one.
- **Strongly consistent domains** — financial transactions, inventory/seat
  counts. You may still cache *metadata* around these (event details,
  product descriptions) but never the consistency-critical number itself
  without very aggressive invalidation and short TTLs.
- **Real-time collaborative systems** — Google Docs-style apps need
  every keystroke visible immediately; caching actively hurts here. This is
  a job for the [SSE/WebSocket pattern](./SSE_WEBSOCKET_SCALABLE_SYSTEMS_new_more.md), not read scaling.

Remember: this pattern is about **reducing database load**, not simply
"making things fast." If your DB handles load fine but you need lower
per-request latency, that's a different problem (edge compute, service
mesh, protocol-level optimization).

---

## 12. Problem Breakdowns

How the pattern maps onto classic interview prompts. For each, the key move
is identifying *which* stage of the progression matters most.

### Bitly / URL Shortener
Read/write ratio is *extreme* — a URL is shortened once, then read millions
of times. This is a caching dream scenario:
- Cache `short_code → long_url` in Redis **with no expiration** (the mapping
  never changes once created).
- Put a CDN in front for global low-latency redirects.
- DB is only ever hit on a cache miss for an unpopular/never-cached link.
- Read replicas are almost unnecessary here — caching alone absorbs nearly
  all traffic.

### Ticketmaster
Event pages get hammered the instant tickets go on sale — thousands refresh
the same page. Cache event details, venue info, and seating charts
aggressively (they don't change often). **Critical exception:** actual seat
*availability* cannot be cached without risking overselling — that read
must go to the strongly consistent write path (or a very short-TTL/real-time
mechanism). Use read replicas for general browsing traffic while writes
(purchases) go through the primary.

### Instagram (feed load)
One feed open = 100+ reads (post metadata, user info, like counts, comment
previews). Denormalize aggressively (embed author info directly on post
records), cache hot posts/profiles, and precompute like/comment counters
via materialized-view-style counters updated asynchronously rather than
`COUNT()`'d live on every read.

### Facebook News Feed
Feed generation is inherently read-intensive and personalized. Pre-compute
(fan-out-on-write) feeds for active users, cache recent posts from followed
accounts, and paginate smartly — users mostly read only the first few items,
so aggressively caching *just the head of the feed* pays off disproportionately.

### YouTube Top K (trending videos)
A classic "compute once, read many" problem. Precompute the top-K list on a
schedule (materialized view / background job) rather than ranking live on
every homepage load; cache the resulting list with a TTL matched to how
fresh "trending" needs to feel (minutes, not seconds).

### Yelp
Geo-based search ("restaurants near me") benefits from geospatial indexes
(for the DB layer) plus caching popular search-box results (e.g. "restaurants
in downtown Seattle") — a small number of geographic cells account for a
large share of queries, so cache by geohash bucket.

### Distributed Cache (as the interview subject itself)
When asked to *design* a cache (not just use one): the pattern's Sections
6-8 above (hot keys, stampedes, invalidation) are the actual meat of the
interview — consistent hashing for shard placement, LRU/LFU eviction,
replication for availability, and read-through vs cache-aside as the
access pattern.

### Rate Limiter
Ironically write-heavy on the surface (every request "writes" a counter
increment), but the *check* is a read on every single request — so this
lives entirely in a low-latency in-memory store (Redis with `INCR` +
`EXPIRE`, or a sliding-window/token-bucket structure) rather than a
relational DB at all. The "caching layer" *is* the primary store here.

### YouTube (general platform)
Video metadata (titles, descriptions, thumbnails) rarely changes — cache
aggressively and serve thumbnails via CDN. View counts can be **eventually
consistent** — batch-updated every few minutes rather than incremented
synchronously on every play, trading exact real-time counts for massively
reduced write/read amplification.

### Facebook Post Search
Full-text search needs a specialized index (Elasticsearch/inverted index)
rather than a relational B-tree — but once results are computed, cache
popular query results (common hashtags, trending searches) since the same
queries repeat constantly.

### Local Delivery Service
Reads here are geo + time sensitive ("restaurants open near me now") —
geographic sharding keeps regional data close to regional demand, and
short-TTL caching (driver/restaurant availability) balances freshness
against read load, since availability changes minute-to-minute.

### News Aggregator
Similar to feed systems — precompute/rank articles on a schedule, cache
aggressively (news articles are immutable once published), and use CDN
caching heavily since the same articles are read by huge numbers of
geographically distributed readers.

### Metrics Monitoring
Dashboards re-query the same aggregated time windows repeatedly. Precompute
rollups (materialized views / pre-aggregated time buckets) rather than
scanning raw metric rows per dashboard load, and cache dashboard queries with
a TTL matched to your metrics' collection interval.

---

## 13. Interview Deep-Dive Q&A

```
Q: Your app launched with 10K users and was snappy. Now at 10M users,
   simple lookups take 30 seconds and DB CPU sits at 100% even for
   "basic" queries. What's happening and how do you fix it?
A: Missing indexes. Without one, finding a user by email means scanning
   every row (10M rows × 200 bytes ≈ 2GB read just to find one match),
   multiplied across every concurrent login. Joins compound this —
   fetching a user's orders unindexed means a full scan of BOTH tables.
   Fix: index the columns you filter/join/sort on (e.g. `email`), turning
   an O(n) seq scan into an O(log n) index scan. For compound filters,
   order composite index columns to match your most common query shape.

Q: How do you handle millions of concurrent reads hitting the exact same
   cache key (a viral post, a celebrity profile)?
A: Request coalescing first (collapse concurrent identical fetches into
   one backend call, bounding load to N app servers instead of N users).
   If that's still not enough at extreme scale, fan the hot key out across
   multiple replica keys (e.g. `feed:x:1..10`) and have readers pick one at
   random, spreading load across cache shards.

Q: What happens when a hot cache entry's TTL expires and every request
   tries to rebuild it at the same instant?
A: Cache stampede — a self-inflicted DDoS on your DB. Mitigate with
   probabilistic early refresh (background-refresh with rising probability
   as the entry nears expiry, spreading rebuilds over a window) for most
   cases, or a distributed lock on rebuild (simpler, but fragile under
   failure) for lower-traffic keys, or continuous scheduled background
   refresh for your handful of most critical keys.

Q: How do you make a cache update immediately visible everywhere (Redis,
   CDN, browser) without race conditions?
A: Cache versioning. Store a version number on the DB row; increment it
   atomically in the same transaction as the write. Cache keys embed the
   version (`event:123:v43`); a "late" writer can never resurrect a stale
   version because the DB forces monotonically increasing version numbers.
   Old versions simply age out via TTL rather than being explicitly (and
   racily) deleted. For aggregate/computed data where per-row versioning
   doesn't apply (feeds, search results), use a small "deleted/changed
   items" cache to filter stale entries out of large cached structures
   while the underlying structure is rebuilt in the background.

Q: When would you pick read replicas over caching, or vice versa?
A: Read replicas preserve full query flexibility (any WHERE/JOIN/ORDER BY
   still works) at the cost of replication lag and needing full copies of
   the dataset per replica. Caching gives the best possible latency and
   the most load reduction, but only for the specific access patterns
   you've chosen to cache, and introduces staleness/invalidation
   complexity. Use replicas when query patterns are diverse/unpredictable;
   use caching when a small number of query shapes account for most
   traffic (which is the common case for content-heavy apps).

Q: How would you decide a cache TTL instead of guessing a "reasonable"
   number?
A: Derive it from the non-functional requirement, not the other way
   around. If the spec says "search results must be ≤30s stale," your
   TTL is 30 seconds. If user profiles tolerate 5 minutes of staleness,
   TTL is 5 minutes. This turns a vague design choice into a direct
   consequence of a stated requirement — which is exactly what
   interviewers want to see you do.

Q: How does adding or removing a cache/DB node avoid reshuffling your
   entire dataset?
A: Consistent hashing. Naive `hash(key) % N` remaps almost every key when
   N changes. Placing nodes and keys on a hash ring means adding/removing a
   node only affects the keys in its immediate neighborhood on the ring —
   everything else stays put. Virtual nodes (each physical node gets many
   ring positions) further ensure a departing node's load spreads evenly
   across many survivors instead of dogpiling onto one neighbor.

Q: Your cache is full. Why would you choose LFU over LRU, or vice versa?
A: LRU is simpler and handles "recency = relevance" workloads well (most
   social/feed data), but a single big sequential scan can flush your
   entire hot set. LFU protects genuinely-popular long-term hot items
   from being evicted by one-off scans, but adapts slowly when what's
   popular actually changes, and needs a decay mechanism so yesterday's
   hits don't keep an item falsely "hot" forever. Modern systems (Caffeine,
   some CDNs) use hybrid policies like W-TinyLFU that get most of LFU's
   benefit at LRU-like cost.

Q: How would you use CQRS to speed up a slow, complex read query instead
   of just adding an index?
A: If the query is a multi-table aggregation that's fundamentally
   expensive no matter how it's indexed (e.g. "top 10 products by revenue
   in the last hour across millions of orders"), stop trying to make that
   query fast on the write-side schema. Emit a change event on every write
   (via CDC off the WAL/binlog), and asynchronously maintain a
   purpose-built, denormalized read model that already has the answer
   precomputed. The read becomes a cheap point lookup; the cost moves to
   an async pipeline that tolerates a small consistency lag.

Q: Why did Twitter/Facebook-scale systems build a graph-aware cache (TAO)
   instead of just putting Redis in front of MySQL?
A: A generic key-value cache doesn't understand relationships — "get all
   of Alice's friends" or "get the last 20 comments on this post" needs the
   cache itself to model associations, not just flat key→value pairs, or
   you end up doing N cache lookups plus manual aggregation in the app
   layer for every graph traversal. TAO bakes "objects and associations"
   into the cache's own data model so a single graph-shaped read is a
   single cache-tier request.

Q: A single celebrity account has 20M followers. Why not just fan out
   their tweet to all 20M timeline caches the instant they post?
A: That's 20M writes triggered by one write — a massive amplification that
   can overwhelm your cache tier and takes real time to complete, delaying
   visibility. The standard fix is hybrid fan-out: fan out on WRITE for
   normal accounts (few followers, cheap), but fan out on READ for
   celebrity accounts — merge their recent tweets into a follower's
   timeline live, at read time, since there are vastly fewer celebrities
   being read than followers doing the reading.
```

---

## 14. Numbers to Know — Cheat Sheet

```
Full table scan vs indexed lookup:     O(n) → O(log n)
SSD vs spinning disk random I/O:       10-100x faster
DB → horizontal scale trigger point:   ~50,000-100,000 reads/sec (single, well-indexed DB)
DB query latency (well-optimized):     ~tens of ms
In-memory cache read latency:          sub-millisecond
CDN edge vs distant origin latency:    ~200ms → <10ms
CDN origin load reduction potential:   90%+ for cacheable content
Common read:write ratios:              10:1 baseline, 100:1+ for content-heavy apps
Safety-net TTL range (typical):        5-15 minutes
Postgres connection memory cost:       ~5-10 MB per open backend connection
PgBouncer connection multiplexing:     ~100 real DB conns → thousands of app conns
Redis Cluster hash slots:              16,384 fixed slots, distributed across shards
Facebook TAO read:write ratio:         ~500:1 (social graph reads vs writes)
DAX vs raw DynamoDB latency:           single-digit ms → microseconds on cache hit
Quorum read/write rule:                W + R > N guarantees latest-write visibility
```

---

## 15. Conclusion

Read scaling is the single most common scaling conversation in system design
interviews because it shows up in nearly every content-heavy application.
The core insight: **read traffic grows faster than write traffic, and
eventually physics wins** — no clever code substitutes for exceeding a CPU,
memory, or I/O ceiling.

The progression is deliberate and worth stating out loud in an interview:
1. **Optimize first** — indexing and denormalization solve more problems
   than people expect, and cost nothing operationally.
2. **Scale horizontally** — read replicas (and, for dataset-size problems,
   sharding) once a single optimized DB genuinely can't keep up.
3. **Cache last** — the biggest performance win, but also the most
   operational complexity (staleness, invalidation, hot keys, stampedes).

Show the interviewer you understand *both* the performance upside and the
operational cost at each stage — and that you know exactly which one to
reach for first, rather than defaulting straight to "add Redis."
