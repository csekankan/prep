# Microservices Caching Strategies — Complete Guide

> **Based on:** Mark Richards' O'Reilly Training "Microservices Caching Strategies"
> **Format:** 3-Hour Workshop (O'Reilly Live Training / Corporate)
> **Tools demonstrated:** Apache Ignite, Hazelcast
> **Supplementary:** Developer to Architect Lessons 76-80, 149, 174

---

## Table of Contents

1. [Why Caching in Microservices](#1-why-caching-in-microservices)
2. [Data Access Costs: LAC vs RAC](#2-data-access-costs-lac-vs-rac)
3. [Cache Implementation: IMDG vs IMDB](#3-cache-implementation-imdg-vs-imdb)
4. [Caching Strategies: Read/Write Flows](#4-caching-strategies-readwrite-flows)
5. [Caching Topologies](#5-caching-topologies)
6. [Caching Patterns and Use Cases](#6-caching-patterns-and-use-cases)
7. [Data Collisions](#7-data-collisions)
8. [Cache Eviction Policies](#8-cache-eviction-policies)
9. [Caching and CAP Theorem](#9-caching-and-cap-theorem)
10. [Topology Selection Framework](#10-topology-selection-framework)
11. [Real-World Case Study: Agoda PDS](#11-real-world-case-study-agoda-pds)

---

## 1. Why Caching in Microservices

Caching in microservices is fundamentally different from caching in monoliths because of **two additional dimensions of complexity:**

```
MONOLITH:                           MICROSERVICES:
┌─────────────────┐                 ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Application   │                 │Service A │  │Service B │  │Service C │
│                 │                 │          │  │          │  │          │
│   ┌─────────┐   │                 └────┬─────┘  └────┬─────┘  └────┬─────┘
│   │  Cache   │   │                     │  ↕ RAC      │  ↕ RAC      │
│   └────┬────┘   │                     │  (network)   │  (network)  │
│        │ LAC    │                     │             │             │
│   ┌────▼────┐   │                 ┌───▼──┐    ┌───▼──┐    ┌───▼──┐
│   │   DB    │   │                 │ DB A │    │ DB B │    │ DB C │
│   └─────────┘   │                 └──────┘    └──────┘    └──────┘
└─────────────────┘
                                    Each service owns its data
Only LAC to worry about             (bounded context), but needs
                                    data from OTHER services too
```

### What caching solves in microservices:

| Benefit | How |
|---|---|
| **Performance** | Serve from memory instead of DB or remote API |
| **Scalability** | Offload repeated reads from data stores |
| **Reduce inter-service chatter** | Cache remote data locally, avoid repeated API calls |
| **Partial decoupling** | If owner service is down, cached data still serves reads |

### What caching introduces:

| Challenge | Why |
|---|---|
| **Consistency** | Cached data can become stale |
| **Collisions** | Multiple instances/services writing same key |
| **Bounded context violation** | Caching another service's data can bypass its domain logic |
| **Eviction complexity** | Deciding what to remove when cache is full |

---

## 2. Data Access Costs: LAC vs RAC

### LAC (Local Access Cost)

The time to query and retrieve data between application code and its **own** database.

```
┌──────────────────────┐
│   Order Service      │
│                      │
│   app code           │
│      │               │
│      │ LAC           │  Depends on:
│      │ (query time)  │  - Data size
│      ▼               │  - Relational complexity (JOINs)
│   ┌────────┐         │  - Index quality
│   │  DB    │         │  - DB technology
│   └────────┘         │
└──────────────────────┘
```

**In monoliths:** LAC is the dominant cost — large tables, complex JOINs.
**In microservices:** LAC decreases (smaller datasets per service, fewer relations) but RAC appears.

### RAC (Remote Access Cost)

The network cost of fetching data from **another** microservice.

```
┌──────────────┐         ┌──────────────┐
│ Order Service│  RAC    │Product Service│
│              │─────────│              │
│ "I need     │ HTTP/   │ "Here's the  │
│  product    │ gRPC    │  product     │
│  names for  │ call    │  data"       │
│  this       │         │              │
│  invoice"   │         │    ┌──────┐  │
│              │         │    │ DB   │  │
└──────────────┘         │    └──────┘  │
                         └──────────────┘

RAC = network latency + serialization + remote LAC
```

**RAC always includes some LAC** — the remote service still hits its own DB. You pay:
- Network transfer cost
- Serialization/deserialization
- The remote service's own LAC

### Solutions for RAC

#### Solution 1: Data Replication

```
┌──────────────┐                    ┌──────────────┐
│ Order Service│  events / CDC      │Product Service│
│              │◄───────────────────│              │
│ ┌──────────┐ │                    │              │
│ │ Local    │ │  "I keep a read-   │    ┌──────┐  │
│ │ copy of  │ │   only copy of     │    │ DB   │  │
│ │ products │ │   product data     │    └──────┘  │
│ └──────────┘ │   in my own DB"    └──────────────┘
│              │
│ RAC = 0      │  ← eliminated entirely
└──────────────┘
```

**When:** Very high frequency data need between two specific services.
**How:** DB replication tools, CDC, or message broker events.
**Trade-off:** Storage duplication, sync complexity.

#### Solution 2: Middleware Caching

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Order Service│   │Invoice Service│  │Search Service│
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │  read-only
                   ┌──────▼───────┐
                   │    REDIS /   │  ← centralized cache
                   │   Hazelcast  │     holds product data
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │Product Service│  ← still the owner
                   │  (writes)     │    writes go through here
                   └──────────────┘
```

**When:** One service's data needed by many other services.
**How:** Central read-only cache, owner service pushes updates.
**Trade-off:** Looks "monolithic" but is fundamentally different — read-only, high-perf, scalable, no direct DB access.

---

## 3. Cache Implementation: IMDG vs IMDB

Two broad categories of caching technology:

### IMDG (In-Memory Data Grid)

A distributed **key-value store** kept entirely in RAM.

```
IMDG:
┌──────────────────────────┐
│  Key        │  Value     │
├─────────────┼────────────┤
│ "user:123"  │ {json...}  │
│ "prod:456"  │ {json...}  │
│ "order:789" │ {json...}  │
└──────────────────────────┘

Operations: GET, PUT, DELETE, getAll
No JOINs, no SQL, no indexing overhead
```

**Examples:** Hazelcast, Apache Ignite (grid mode), Infinispan, Oracle Coherence, GemFire
**Best for:** Simple key-based lookups, maximum speed, minimal overhead

### IMDB (In-Memory Database)

An in-memory system that supports **SQL-like queries**, indexing, JOINs, aggregations.

```
IMDB:
┌──────────────────────────────────────────┐
│  SELECT p.name, c.category_name          │
│  FROM products p                         │
│  JOIN categories c ON p.cat_id = c.id    │
│  WHERE p.price > 100                     │
│  ORDER BY p.rating DESC                  │
│                                          │
│  ← Full query engine running in memory   │
└──────────────────────────────────────────┘
```

**Examples:** Apache Ignite (SQL mode), VoltDB, MemSQL/SingleStore
**Best for:** Complex queries on cached data, analytics on hot data

### Decision: IMDG vs IMDB

| Factor | IMDG | IMDB |
|---|---|---|
| Data model | Key-value pairs | Relational/table-like |
| Query capability | Get by key only | SQL, JOINs, aggregations |
| Performance | Fastest (minimal overhead) | Slower (indexing, query engine) |
| Memory usage | Lower | Higher (indexes, query metadata) |
| Complexity | Simple | More complex |
| Use when | 90%+ of lookups are by key | Need to filter, sort, join cached data |

**Rule of thumb:** If your cache access is "give me the data for key X" → IMDG. If it's "give me all items matching these criteria" → IMDB.

---

## 4. Caching Strategies: Read/Write Flows

These describe **how data flows** between service, cache, and database. Applicable to any topology.

### Read-Through

```
Service → Cache → (miss?) → DB
                     │
                     ▼
              Cache stores it
                     │
                     ▼
              Returns to service

Service ONLY talks to cache, never directly to DB for reads.
```

| Aspect | Detail |
|---|---|
| Flow | Service reads cache; on miss, cache fetches from DB, stores, returns |
| Pros | Simplifies read logic — service only knows about cache |
| Cons | On miss, slower (cache + DB round trip). Can bypass domain logic if reading another service's DB |
| Best for | Read-heavy, own-domain data |

### Write-Through

```
Service → Cache → DB (synchronous)
              │
              └── "I don't return until DB confirms"
```

| Aspect | Detail |
|---|---|
| Flow | Service writes to cache; cache synchronously writes to DB |
| Pros | Cache and DB always consistent |
| Cons | Slow writes (must wait for DB). Can break bounded context if writing to another service's DB |
| Best for | Data where consistency is critical, low write volume |

### Write-Behind (Write-Back)

```
Service → Cache → returns immediately
              │
              └── async ──► DB (later)
```

| Aspect | Detail |
|---|---|
| Flow | Service writes to cache, returns fast; cache async-writes to DB |
| Pros | Fast writes (no DB wait) |
| Cons | **Data loss risk** if cache node fails before persisting. Timing issues if other systems expect immediate DB writes |
| Best for | High write throughput where brief inconsistency is acceptable |

### Bounded Context Warning

```
⚠️ DANGER ZONE:

  Order Service → cache → Product Service's DB
                              ↑
                    This BYPASSES Product Service's
                    domain logic, validation, events.
                    Violates bounded context!

  ✅ SAFE ALTERNATIVES:
  - Cache your OWN domain data
  - Use read-only caching for external data
  - Use Data Sidecar or Data Sharing patterns
```

---

## 5. Caching Topologies

The **physical architecture** of where cache data lives. This is the core of Mark Richards' teaching.

### Topology 1: Single In-Memory Cache

```
  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │  Service Inst 1  │    │  Service Inst 2  │    │  Service Inst 3  │
  │                  │    │                  │    │                  │
  │  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
  │  │ Local Cache│  │    │  │ Local Cache│  │    │  │ Local Cache│  │
  │  │ {A,B,C}    │  │    │  │ {A,D,E}    │  │    │  │ {B,C,F}    │  │
  │  └─────┬──────┘  │    │  └─────┬──────┘  │    │  └─────┬──────┘  │
  │        │         │    │        │         │    │        │         │
  │  ┌─────▼──────┐  │    │  ┌─────▼──────┐  │    │  ┌─────▼──────┐  │
  │  │    DB      │  │    │  │    DB      │  │    │  │    DB      │  │
  │  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │
  └──────────────────┘    └──────────────────┘    └──────────────────┘

  Each instance is an island. No synchronization between caches.
```

| Aspect | Detail |
|---|---|
| **Performance** | Fastest possible — data in same process memory, zero network |
| **Consistency** | None across instances — each has its own view |
| **Scalability** | Limited by single instance memory |
| **Fault tolerance** | None — instance dies, cache is gone |
| **Update rate** | Very low — no propagation mechanism |
| **Best for** | Small, static, rarely-changing data (country codes, config, enums) |
| **Avoid when** | Multiple instances need consistent view, data changes frequently |

**The critical question:** What happens when you scale to multiple instances?

```
Instance 1 cache: product_123.price = $100
Instance 2 cache: product_123.price = $95   ← updated 2 min ago
Instance 3 cache: product_123.price = $100

User A hits Instance 1 → sees $100
User B hits Instance 2 → sees $95
User C hits Instance 3 → sees $100

Three users, same product, different prices. UNACCEPTABLE for many use cases.
```

---

### Topology 2: Distributed Cache (Client-Server)

```
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ Service      │   │ Service      │   │ Service      │
  │ Instance 1   │   │ Instance 2   │   │ Instance 3   │
  │              │   │              │   │              │
  │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
  │ │ Client   │ │   │ │ Client   │ │   │ │ Client   │ │
  │ │ Library  │ │   │ │ Library  │ │   │ │ Library  │ │
  │ └─────┬────┘ │   │ └─────┬────┘ │   │ └─────┬────┘ │
  └───────┼──────┘   └───────┼──────┘   └───────┼──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │  proprietary protocol
                      ┌──────▼──────────────────────┐
                      │   EXTERNAL CACHE CLUSTER     │
                      │                              │
                      │  ┌────────┐  ┌────────┐     │
                      │  │Node 1  │  │Node 2  │     │
                      │  │{A,B,C} │  │{D,E,F} │     │  ← data sharded
                      │  └────────┘  └────────┘     │     across nodes
                      │                              │
                      │  One unified view for all    │
                      │  service instances            │
                      └──────────────────────────────┘
```

| Aspect | Detail |
|---|---|
| **Performance** | Slower than local (network hop: ~1-5ms per operation) |
| **Consistency** | Strong — all instances read/write the same central store |
| **Scalability** | High — cluster can shard data across many nodes |
| **Fault tolerance** | Depends on cluster config — can replicate across nodes |
| **Update rate** | Handles high writes well (single source of truth) |
| **Best for** | Most microservice caching scenarios. The "default" choice. |
| **Technologies** | Redis, Memcached, Hazelcast (client-server), Ignite (client-server) |

**CAP trade-off:** Distributed cache is a **CP system** (consistency + partition tolerance). If a network partition occurs, the cache may become unavailable to maintain consistency. If you choose AP (availability + partition tolerance), you risk serving stale data during partitions.

---

### Topology 3: Replicated Cache (In-Process)

```
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ Service      │   │ Service      │   │ Service      │
  │ Instance 1   │   │ Instance 2   │   │ Instance 3   │
  │              │   │              │   │              │
  │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
  │ │ Cache    │ │   │ │ Cache    │ │   │ │ Cache    │ │
  │ │{A,B,C,D,│◄├───┤►│{A,B,C,D,│◄├───┤►│{A,B,C,D,│ │
  │ │ E,F}    │ │   │ │ E,F}    │ │   │ │ E,F}    │ │
  │ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
  └──────────────┘   └──────────────┘   └──────────────┘
         ▲                  ▲                  ▲
         └──── replication protocol ───────────┘
               (async, proprietary)

  EVERY instance has the FULL dataset.
  Write to one → propagates to all others.
```

| Aspect | Detail |
|---|---|
| **Performance** | Extremely fast reads — nanosecond-level (same process memory) |
| **Consistency** | Eventual — replication lag means brief inconsistency windows |
| **Scalability** | Poor for large datasets — every instance stores everything |
| **Fault tolerance** | High — any node has the complete data |
| **Update rate** | Moderate — high update rates cause collision risk |
| **Best for** | Small-to-medium read-heavy datasets across many instances |
| **Technologies** | Hazelcast, Apache Ignite, Infinispan, Oracle Coherence |

**CAP trade-off:** Replicated cache is an **AP system** (availability + partition tolerance). During a network partition, each node continues serving its local copy (available), but they may diverge (inconsistent). When the partition heals, they reconcile.

**The collision problem:** (detailed in Section 7)

```
T+0.000s: Instance 1 reads inventory = 700
T+0.000s: Instance 2 reads inventory = 700
T+0.001s: Instance 1 writes inventory = 690 (decremented by 10)
T+0.001s: Instance 2 writes inventory = 695 (decremented by 5)
T+0.050s: Replication propagates...

Result: Final value is either 690 or 695 (last write wins)
Correct answer: should be 685 (700 - 10 - 5)

This is a DATA COLLISION.
```

---

### Topology 4: Near-Cache Hybrid

```
  ┌────────────────────────────────────────────┐
  │         Service Instance 1                  │
  │                                             │
  │  ┌───────────────┐                          │
  │  │ FRONT CACHE   │  ← small, local, fast   │
  │  │ (L1: near)    │    LRU/LFU eviction     │
  │  │ {hot items}   │    TTL expiration        │
  │  └───────┬───────┘                          │
  │          │ miss                             │
  │          ▼                                  │
  │  ┌───────────────┐                          │
  │  │ Client lib    │──── network ────┐        │
  │  └───────────────┘                 │        │
  └────────────────────────────────────│────────┘
                                       │
                                ┌──────▼──────────────────────┐
                                │   BACKING CACHE (L2)         │
                                │   (distributed cluster)      │
                                │   {full dataset}             │
                                │                              │
                                │   On write: backing cache    │
                                │   sends invalidation to      │
                                │   all front caches           │
                                └──────────────────────────────┘
```

| Aspect | Detail |
|---|---|
| **Performance** | L1 hit: nanoseconds (local). L1 miss: milliseconds (network to L2) |
| **Consistency** | Brief staleness in L1 until invalidation propagates |
| **Scalability** | High — L2 is distributed, L1 is bounded (only hot items) |
| **Fault tolerance** | Partial — L2 replication covers backing store |
| **Update rate** | Moderate to high — writes go to L2, L1 gets invalidations |
| **Best for** | High read volume with clear "hot" item patterns |
| **Technologies** | Hazelcast (near-cache config), Ignite (near-cache) |

**Invalidation flow:**

```
1. Service Instance 1 writes key "X" to backing cache (L2)
2. L2 stores the update
3. L2 sends invalidation message to ALL front caches (L1)
4. Instance 2's L1 receives invalidation → removes "X" from local cache
5. Next read of "X" on Instance 2 → L1 miss → fetches fresh from L2

Window of staleness: time between step 1 and step 4 (~ms)
```

---

### Topologies Comparison Matrix

```
                    Single        Distributed      Replicated      Near-Cache
                    In-Memory     (Client-Server)  (In-Process)    (Hybrid)
                    ──────────    ───────────────  ──────────────  ──────────
Read Speed          ★★★★★         ★★★              ★★★★★           ★★★★ (L1)
                    (ns, local)   (ms, network)    (ns, local)     ★★★ (L2)

Write Speed         ★★★★★         ★★★★             ★★★             ★★★★
                    (local only)  (single write)   (must replicate) (write to L2)

Consistency         ★              ★★★★★            ★★              ★★★
                    (none across   (single truth)   (eventual,      (brief L1
                     instances)                      collisions)     staleness)

Scalability         ★              ★★★★★            ★★              ★★★★
(data volume)       (per-instance  (cluster can     (every node     (L2 scales,
                     memory)        shard)           stores all)     L1 bounded)

Fault Tolerance     ★              ★★★              ★★★★★           ★★★★
                    (instance      (cluster config   (any node has   (L2 replicated,
                     dies = gone)   dependent)        full copy)      L1 ephemeral)

Update Rate         ★★             ★★★★★            ★★★             ★★★★
Support             (no sync)      (handles high)   (collision      (L2 handles
                                                     risk)           writes well)

Complexity          ★              ★★★              ★★★★            ★★★★★
                    (trivial)      (external infra)  (replication    (two tiers,
                                                     protocol)       invalidation)

CAP Position        N/A            CP               AP              CP (L2) +
                                   (or AP config)                    AP (L1)
```

---

## 6. Caching Patterns and Use Cases

Higher-level, application-focused patterns built on top of topologies.

### Pattern 1: Data Sharing

**Problem:** Order Service needs product data owned by Product Service. Calling Product Service's API on every request is a bottleneck.

```
┌──────────────┐                        ┌──────────────┐
│Order Service │   1. Check local       │Product Service│
│              │      cache             │ (data owner) │
│  ┌────────┐  │   2. On miss, call     │              │
│  │ Cache  │  │──────API ──────────────│  ┌────────┐  │
│  │(read-  │  │   3. Cache response    │  │  DB    │  │
│  │ only)  │  │      locally           │  └────────┘  │
│  └────────┘  │                        │              │
│              │   ⚠️ NEVER writes to   │              │
│              │     Product DB         │              │
└──────────────┘                        └──────────────┘
```

| Pros | Cons |
|---|---|
| Respects bounded context | Eventual consistency (stale reads) |
| Fast reads (local cache) | Must decide TTL/refresh strategy |
| Fault tolerant (works if Product Service is down) | Memory overhead for large datasets |

**Avoid if:** Product data is write-heavy (cache constantly stale).

### Pattern 2: Data Sidecar

**Problem:** Profile Service data is needed by **many** other services. Data Sharing pattern means each service caches independently — wasteful and inconsistent.

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Order Service │  │Invoice Service│ │Search Service│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │  read-only
                  ┌──────▼──────────┐
                  │   SIDECAR CACHE │  ← distributed cache
                  │   (Redis /      │     holds Profile data
                  │    Hazelcast)   │     read-only for consumers
                  └──────▲──────────┘
                         │  writes/updates
                  ┌──────┴──────────┐
                  │ Profile Service │  ← sole owner
                  │ (pushes changes │     writes domain events
                  │  to sidecar)    │     or directly updates cache
                  └─────────────────┘
```

| Pros | Cons |
|---|---|
| All consumers see consistent data | Cache node failure = all consumers lose data |
| Less load on Profile Service | Extra complexity in push/refresh logic |
| Scalable (distributed cache) | Need event-driven or polling sync |
| Respects bounded context | |

**Difference from Data Sharing:** In Data Sharing, each consumer caches independently (N copies). In Data Sidecar, one central cache serves all consumers (1 copy, owned/updated by the source service).

### Pattern 3: Multi-Instance Caching

**Problem:** Order Service scaled to 10 containers. All need the same domain data. Single in-memory cache means 10 inconsistent caches.

```
┌──────────┐ ┌──────────┐ ┌──────────┐     ┌──────────┐
│ Order-1  │ │ Order-2  │ │ Order-3  │ ... │ Order-10 │
│ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │     │ ┌──────┐ │
│ │Cache │◄├─┤►│Cache │◄├─┤►│Cache │◄├─...─┤►│Cache │ │
│ └──────┘ │ │ └──────┘ │ │ └──────┘ │     │ └──────┘ │
└──────────┘ └──────────┘ └──────────┘     └──────────┘
     Replicated: all store full set
     Near-cache: each stores hot subset + shared backing store
```

**Solution:** Use replicated or near-cache topology so changes propagate across instances automatically.

| Replicated approach | Near-cache approach |
|---|---|
| All 10 instances store full dataset | Each stores hot subset locally |
| Fast reads everywhere | L1 fast, L2 on miss |
| High memory usage (10x) | Lower per-instance memory |
| Collision risk on concurrent writes | L2 serializes writes |

### Pattern 4: Tuple-Space (Space-Based Architecture)

**Problem:** System needs ultra-low latency for everything — reads AND writes. Can't afford DB round trips at all. Examples: stock trading, real-time bidding, flash sales.

```
┌────────────────────────────────────────────────────────┐
│                 TUPLE-SPACE ARCHITECTURE                 │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Processing │  │Processing │  │Processing │             │
│  │  Unit 1   │  │  Unit 2   │  │  Unit 3   │  (stateless)│
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘             │
│        │              │              │                    │
│        └──────────────┼──────────────┘                    │
│                       │                                   │
│               ┌───────▼───────┐                           │
│               │   DATA GRID   │  ← ALL data in memory    │
│               │  (in-memory)  │     sharded & replicated  │
│               │               │     this IS the database  │
│               │  Reads: ns    │     for hot-path ops      │
│               │  Writes: ns   │                           │
│               └───────┬───────┘                           │
│                       │                                   │
│               ┌───────▼───────┐                           │
│               │ Persistence   │  ← async to disk         │
│               │ Agent         │     for recovery only     │
│               └───────────────┘                           │
└────────────────────────────────────────────────────────┘
```

| Pros | Cons |
|---|---|
| Ultra-fast reads AND writes | Massive memory cost (everything in RAM) |
| No DB bottleneck on hot path | Complex write concurrency |
| Extreme elasticity (add/remove processing units) | Eventual consistency to persistent store |
| Handles traffic spikes gracefully | Data loss risk if grid fails before persistence |

**Use cases:** Stock trading, real-time analytics, flash sales, session-heavy portals, gaming leaderboards, bidding engines.

---

## 7. Data Collisions

### What Are Data Collisions?

Collisions occur in **replicated caching** (or multi-master distributed caching) when two instances update the same record concurrently, and replication messages cross in-flight.

```
Timeline:

T+0.000s  Instance A reads: inventory = 700
T+0.000s  Instance B reads: inventory = 700

T+0.001s  Instance A writes: inventory = 690  (decremented 10)
T+0.001s  Instance B writes: inventory = 695  (decremented 5)

T+0.050s  Replication:
          A's update (690) arrives at B → B overwrites 695 with 690
          B's update (695) arrives at A → A overwrites 690 with 695

Final: Both show 695 (or 690, depending on race)
Correct: Should be 685 (700 - 10 - 5)

Lost update! 10 units of inventory vanished.
```

### Collision Probability Formula

```
Collision_Rate ≈ N × (U² / S) × L

Where:
  N = Number of instances
  U = Update rate (writes per second)
  S = Cache size (total distinct entries)
  L = Replication latency (in seconds)
```

**Worked example:**

```
N = 8 instances
U = 300 writes/sec
S = 30,000 entries
L = 0.050 sec (50ms)

Collision_Rate = 8 × (300² / 30,000) × 0.050
              = 8 × (90,000 / 30,000) × 0.050
              = 8 × 3 × 0.050
              = 1.2 collisions/sec

At 1.2 collisions/sec → HIGH RISK → need concurrency controls
```

**Interpretation:**

```
Collision Rate    Risk Level    Action
─────────────     ──────────    ──────
< 0.01/sec        Low          Acceptable for most use cases
0.01 - 1.0/sec    Medium       Monitor, consider mitigation
> 1.0/sec         High         Must implement concurrency controls
```

### How to Reduce Collision Rate

From the formula: `N × (U² / S) × L`

| Lever | How | Impact |
|---|---|---|
| Reduce N | Fewer instances | Less parallelism (bad for throughput) |
| Reduce U | Fewer writes | May not be controllable |
| Increase S | More cache entries | Dilutes collision probability |
| Reduce L | Faster replication | Hardware/network improvement |
| **Change topology** | Switch to distributed | **Eliminates collisions entirely** |

### Collision Avoidance Strategies

#### Strategy 1: Queueing

```
Instance A ─┐
             ├──► Message Queue ──► Single Writer ──► Cache
Instance B ─┘       (serialized)

All writes go through a queue.
Single writer processes them sequentially.
No collisions possible.
Trade-off: eventual consistency (queue introduces delay).
```

#### Strategy 2: Compare-and-Set (CAS / Optimistic Locking)

```
1. Read: value = 700, version = 5
2. Compute: new_value = 690
3. Write: "SET value = 690 WHERE version = 5"
4. If version changed (another instance wrote first) → RETRY from step 1

Instance A: read(700, v5) → write(690, v5) → SUCCESS (v6)
Instance B: read(700, v5) → write(695, v5) → FAIL (v is now 6) → RETRY
Instance B: read(690, v6) → write(685, v6) → SUCCESS (v7)

Final: 685 ← CORRECT
```

---

## 8. Cache Eviction Policies

When the cache is full, something must be removed. The policy determines **what** gets evicted.

### TTL (Time-To-Live)

```
Entry created at T+0, TTL = 60 seconds

T+0s    T+30s    T+60s
│────────│────────│
 cached    cached   EXPIRED → removed

Next request → cache miss → re-fetch from source
```

| Pros | Cons |
|---|---|
| Simple, predictable | Doesn't handle "cache full" — only handles staleness |
| Good for naturally time-sensitive data | May refresh unnecessarily (data didn't change) |
| Tunable per entry | May serve stale data within TTL window |

**Best for:** Real-time data (prices, stock quotes), session data.

### ARC (Archive) Policy

```
Keep entries younger than X (e.g., 6 months)

Entry age:
  Order from 2 days ago    → KEEP
  Order from 3 months ago  → KEEP
  Order from 7 months ago  → EVICT (older than 6 months)
```

| Pros | Cons |
|---|---|
| Perfect for "recent data" use cases | Doesn't handle "cache full" if all data is recent |
| Auto-discards old data | Fixed age threshold may not match access patterns |
| Great for transaction history, audit logs | |

**Best for:** Order history, recent transactions, audit trails.

### LFU (Least Frequently Used)

```
Entry access counts:
  product_A: 1000 accesses  ← keep (popular)
  product_B: 500 accesses   ← keep
  product_C: 3 accesses     ← EVICT (rarely accessed)

Cache full + new entry → evict product_C (lowest frequency)
```

| Pros | Cons |
|---|---|
| Keeps popular items in cache | New items start with count 0 → vulnerable to immediate eviction |
| Good for stable, skewed access patterns | Slow to adapt when popularity shifts |
| Optimal hit rate for read-heavy, stable workloads | Counter management overhead |

**Gotcha:** "Put-heavy" workloads reset counters. A burst of inserts can evict previously popular items.

### LRU (Least Recently Used)

```
Access order (most recent first): D, A, C, B, E

Cache full + new entry F:
  Evict E (least recently accessed)
  Cache: F, D, A, C, B

Next: access B
  Cache: B, F, D, A, C  (B moves to front)
```

| Pros | Cons |
|---|---|
| Most intuitive — recently used = likely needed again | Overhead of tracking recency (linked list / timestamps) |
| Adapts quickly to changing patterns | Can evict frequently-used items during access gaps |
| Default choice for most scenarios | Thrashes when working set > cache size |

**Most common default** for near-cache front caches.

### RR (Random Replacement)

```
Cache full + new entry:
  Pick a random existing entry → EVICT it
  Insert new entry

No tracking, no counters, no linked lists.
```

| Pros | Cons |
|---|---|
| Minimal overhead, fastest eviction | No intelligence about usage patterns |
| Good baseline for benchmarking | Can evict the most popular item |
| Surprisingly effective for uniform access patterns | |

### Adaptive Replacement Cache (ARC) — Advanced

Not the same as "Archive." ARC is a sophisticated algorithm that **dynamically balances recency and frequency**.

```
ARC maintains 4 lists:

T1: Recently accessed entries (recency-focused)
T2: Frequently accessed entries (frequency-focused)
B1: Ghost list — recently evicted from T1 (tracks what WOULD have been useful)
B2: Ghost list — recently evicted from T2

  ┌──────────────────────────────────────────┐
  │           ACTUAL CACHE                    │
  │  ┌────────────────┬────────────────┐      │
  │  │  T1 (recent)   │  T2 (frequent) │      │
  │  │  newer items   │  proven items  │      │
  │  └────────────────┴────────────────┘      │
  │                                            │
  │           GHOST LISTS (metadata only)      │
  │  ┌────────────────┬────────────────┐      │
  │  │  B1 (evicted   │  B2 (evicted   │      │
  │  │   from T1)     │   from T2)     │      │
  │  └────────────────┴────────────────┘      │
  └──────────────────────────────────────────┘

Adaptation:
  - Hit in B1 → "I should have kept recent items longer"
    → grow T1, shrink T2
  - Hit in B2 → "I should have kept frequent items longer"
    → grow T2, shrink T1
```

| Pros | Cons |
|---|---|
| Self-tuning — no parameters to configure | Patented (IBM) — some implementations limited |
| Scan-resistant (one-time scans don't pollute cache) | More complex than LRU/LFU |
| Outperforms LRU by 2-3x on mixed workloads | Higher memory overhead (ghost lists) |
| Constant time per operation (like LRU) | |

### Eviction Policy Selection Guide

```
START
  │
  ├── Unknown access pattern?
  │       └── Start with RR → measure hit rates
  │
  ├── Data has natural expiration?
  │       └── Use TTL (sessions, tokens, prices)
  │
  ├── Need only recent data?
  │       └── Use ARC/Archive (transactions, logs)
  │
  ├── Stable popularity distribution?
  │   (some items always popular)
  │       └── Use LFU
  │
  ├── Temporal locality?
  │   (recently used = likely used again soon)
  │       └── Use LRU
  │
  └── Mixed/unpredictable workload?
          └── Use Adaptive Replacement Cache (ARC)
```

---

## 9. Caching and CAP Theorem

Mark Richards (Lesson 149) specifically addresses how CAP theorem applies to caching topologies.

### CAP Recap

```
         Consistency (C)
              ╱╲
             ╱  ╲
            ╱    ╲
           ╱  CP  ╲
          ╱        ╲
         ╱──────────╲
        ╱     CA      ╲
       ╱   (rarely     ╲
      ╱    exists in    ╲
     ╱   distributed)    ╲
    ╱                      ╲
   ╱          AP            ╲
  ╱────────────────────────╲
Availability (A)    Partition Tolerance (P)

In distributed systems, P is non-negotiable (networks fail).
So the real choice is: CP or AP.
```

### CAP Applied to Cache Topologies

#### Distributed Cache → CP (Consistency + Partition Tolerance)

```
Normal operation:
  Service A → Cache Cluster → "value = 100" ← consistent read
  Service B → Cache Cluster → "value = 100" ← same value

Network partition:
  ┌──────────────┐     ╳╳╳     ┌──────────────┐
  │ Cache Node 1 │     ╳╳╳     │ Cache Node 2 │
  │ (partition A)│   network   │ (partition B)│
  └──────────────┘    split    └──────────────┘

  CP behavior: Cache returns errors to services in partition B
               (unavailable, but consistent — no stale data served)

  AP behavior (if configured): Both partitions serve independently
               (available, but may return different values — inconsistent)
```

#### Replicated Cache → AP (Availability + Partition Tolerance)

```
Normal operation:
  Instance A cache: value = 100 ← replication keeps in sync
  Instance B cache: value = 100

Network partition:
  Instance A: value updated to 110 (can't replicate to B)
  Instance B: value updated to 105 (can't replicate to A)

  Both instances AVAILABLE (serve local data)
  But INCONSISTENT (110 vs 105)

  When partition heals: reconciliation needed (last-write-wins? merge?)
```

#### Near-Cache → Hybrid

```
L1 (front cache): AP behavior — serves local data, may be stale
L2 (backing cache): CP behavior — consistent central store

The "brief staleness" in L1 is the AP trade-off.
The L2 consistency is the CP guarantee.
```

### CAP Implications Table

| Topology | CAP Position | During Partition | Recovery |
|---|---|---|---|
| Distributed | CP (default) | May become unavailable | Automatic when partition heals |
| Distributed | AP (config) | Serves potentially stale data | Reconciliation needed |
| Replicated | AP | Continues serving, may diverge | Merge/reconcile on heal |
| Near-cache | L1=AP, L2=CP | L1 serves stale, L2 may be unavailable | L1 refreshes from L2 |

---

## 10. Topology Selection Framework

Mark Richards' decision framework (Lesson 80):

### Step 1: Is this for microservices?

```
Single in-memory cache:
  - Works ONLY for single-instance services or static data
  - NOT suitable for scaled microservices (multiple instances)
  - If you have 1 instance and data is small/static → use this
  - Otherwise → move to Step 2
```

### Step 2: What matters more — speed or consistency?

```
                 ┌──────────────────────────────┐
                 │ Do you need sub-millisecond   │
                 │ reads AND can tolerate         │
                 │ brief inconsistency?           │
                 └──────────┬───────────────────┘
                            │
                  ┌─────────┼─────────┐
                  ▼                   ▼
                 YES                  NO
                  │                   │
                  ▼                   ▼
          Replicated OR        Distributed
          Near-Cache           (client-server)
                  │
                  ▼
          ┌─────────────────┐
          │ Is dataset small │
          │ enough for each  │
          │ instance to hold │
          │ in memory?       │
          └────────┬────────┘
                   │
          ┌────────┼────────┐
          ▼                 ▼
         YES               NO
          │                 │
          ▼                 ▼
      Replicated        Near-Cache
```

### Step 3: Check constraints

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOPOLOGY DECISION TREE                         │
│                                                                  │
│  1. Single instance + small data?                                │
│     └── YES → Single In-Memory                                   │
│                                                                  │
│  2. Multiple instances + need consistency?                        │
│     └── YES → Distributed (Client-Server)                        │
│                                                                  │
│  3. Multiple instances + need speed + small dataset?             │
│     └── YES → Replicated (check collision probability first!)    │
│                                                                  │
│  4. Multiple instances + need speed + large dataset?             │
│     └── YES → Near-Cache Hybrid                                  │
│                                                                  │
│  5. Extreme performance + all data in memory?                    │
│     └── YES → Tuple-Space (Space-Based Architecture)             │
│                                                                  │
│  6. Default / unsure?                                            │
│     └── Distributed (safest, most widely supported)              │
└─────────────────────────────────────────────────────────────────┘
```

### Quick Reference: When to Use What

| Scenario | Topology | Why |
|---|---|---|
| Config/reference data, 1 instance | Single In-Memory | Simplest, fastest |
| Shared session store, multi-instance | Distributed (Redis) | Consistency, no collisions |
| Product catalog, many readers | Distributed + Data Sidecar | Scalable, consistent |
| Real-time pricing, 10 instances | Replicated (if small) or Near-Cache | Speed, but check collisions |
| Stock trading platform | Tuple-Space | All-in-memory, max performance |
| "I'm not sure" | Distributed | Safe default, widely supported |

---

## 11. Real-World Case Study: Agoda PDS

Agoda's Price Delivery System demonstrates these concepts at extreme scale.

| Concept from Course | Agoda PDS Implementation |
|---|---|
| **LAC** | 110ms P99 metadata retrieval from DB |
| **Single In-Memory topology** | Original architecture — 50% hit rate, LRU thrashing |
| **Distributed topology** | New architecture — Couchbase cluster per DC |
| **Pre-caching strategy** | Hot cache: entire dataset loaded via Kafka pipeline |
| **LRU eviction** | Original LRU failed due to affiliate traffic variability |
| **Data collision** | N/A — they chose distributed (no replication collisions) |
| **CAP trade-off** | CP — Couchbase prioritizes consistency with node replication |
| **Near-cache (future)** | Speculative Phase 4: local L1 + Couchbase L2 |
| **Tuple-space** | Not applicable — metadata retrieval, not computation-heavy |

**Why Agoda chose Distributed over Replicated:**
- 5GB metadata × 200+ instances = 1TB RAM (replicated) vs 30GB (distributed cluster)
- Pricing requires consistency (no collisions — can't show different prices)
- High update rate (every 20 min full sync)
- Collision probability with replicated would be unacceptable at their scale

For the full Agoda PDS deep dive, see [pds-distributed-cache-deep-dive.md](./pds-distributed-cache-deep-dive.md).

---

## References

- Mark Richards, **Microservices Caching Strategies** — O'Reilly Live Training
- Mark Richards, **Developer to Architect** Lessons 76-80 (Caching Topologies), 149 (Caching & CAP), 174 (Data Collisions)
- Mark Richards, **Software Architecture: The Hard Parts** (O'Reilly)
- Mark Richards, **Fundamentals of Software Architecture** (O'Reilly)
- Mehmed Ali Çalışkan, **The Essential Guide to Caching in Microservices Architecture** (Hexaworks-Papers)
- Johan Tiesinga, **Improving Performance Using Distributed Cache with Couchbase** (Agoda Engineering)
