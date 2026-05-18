# Agoda PDS — Distributed Cache with Couchbase: Deep Dive

> **Source:** "Improving Performance Using Distributed Cache with Couchbase" — Agoda Engineering, Oct 2023
> **Author:** Johan Tiesinga

---

## Table of Contents

1. [System Context](#1-system-context)
2. [Problem Identification](#2-problem-identification)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Cache Topology Selection](#4-cache-topology-selection)
5. [Why Couchbase](#5-why-couchbase)
6. [Caching Strategy Selection](#6-caching-strategy-selection)
7. [Pre-Caching Implementation](#7-pre-caching-implementation)
8. [Kafka Consumer Group Mechanics](#8-kafka-consumer-group-mechanics)
9. [Results](#9-results)
10. [Data Center Failover](#10-data-center-failover)
11. [CDC — The Next Evolution](#11-cdc--the-next-evolution)
12. [Key Concepts Glossary](#12-key-concepts-glossary)

---

## 1. System Context

**Price Delivery System (PDS)** serves hotel room prices to Agoda's web, mobile, and affiliate APIs.

| Dimension | Detail |
|---|---|
| Scale | 1M+ requests/second |
| Data centers | 4 globally distributed |
| Edge clients | Web, Mobile, Affiliate APIs |
| Two main flows | Metadata retrieval (I/O-bound) and Price calculation (CPU-bound) |

Affiliate traffic is the key stress factor — third-party partners perform **broad availability and price searches**, causing high variation in which hotels are requested. This contrasts with web/mobile traffic where popular hotels dominate.

---

## 2. Problem Identification

### Metrics Before Optimization

| Metric | Value |
|---|---|
| P99 total API response time | **460 ms** |
| P99 metadata retrieval time | **110 ms** (24% of total) |
| Cache hit ratio | **50%** |

A 50% hit rate meant half of all requests fell through to the database. Cold starts (instance restarts) made it worse — empty caches caused thundering herd effects on the DB.

---

## 3. Root Cause Analysis

### The Chain

```
Affiliate broad searches
        ↓
High variation in requested hotel IDs
        ↓
Working set >> cache capacity per instance
        ↓
Aggressive LRU evictions
        ↓
50% cache hit rate
        ↓
Half of requests hit the database
        ↓
High P99 latency
```

### LRU Thrashing Example

Cache holds 4 items, requests cycle through 5:

```
Request stream: A B C D E A B C D E ...
Cache (size 4):

Step 1: [A _ _ _]  ← miss
Step 2: [A B _ _]  ← miss
Step 3: [A B C _]  ← miss
Step 4: [A B C D]  ← miss (full)
Step 5: [B C D E]  ← miss, evict A
Step 6: [C D E A]  ← miss, evict B ← A was JUST evicted
Step 7: [D E A B]  ← miss, evict C ← B was JUST evicted

Hit rate: 0% — catastrophic thrashing
```

When the working set barely exceeds capacity, LRU collapses. This is what affiliate traffic did to PDS.

### Capacity Gap

Complete metadata set: ~5 GB, growing with new pricing features. Individual instances couldn't hold all of it in memory.

---

## 4. Cache Topology Selection

### Topology 1: Standalone In-Memory Cache (Existing)

```
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  PDS Node 1 │   │  PDS Node 2 │   │  PDS Node 3 │
  │ ┌─────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │
  │ │Cache 1GB│ │   │ │Cache 1GB│ │   │ │Cache 1GB│ │
  │ └─────────┘ │   │ └─────────┘ │   │ └─────────┘ │
  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
         └─────────────────┼─────────────────┘
                    ┌──────▼──────┐
                    │  Database   │
                    └─────────────┘
```

- Each node is an island — no sharing
- Node 1 fetches Hotel X, but Node 2 must fetch it again independently
- Massive redundant DB load across hundreds of instances

### Topology 2: Distributed (Client-Server) Cache — SELECTED

```
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  PDS Node 1 │   │  PDS Node 2 │   │  PDS Node 3 │
  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
         └────────┬────────┴────────┬────────┘
           ┌──────▼──────────▼──────────┐
           │     COUCHBASE CLUSTER       │
           │  Node A   Node B   Node C   │
           │  [2GB]    [2GB]    [2GB]    │
           │     Total: 6GB pooled       │
           └────────────────────────────┘
```

- Pooled memory (6GB shared > 3 × 1GB isolated)
- Single copy of each item, no duplication
- No cold start per instance (cache is external)
- **Trade-off:** Every read now pays network latency (~5-15ms vs ~0.1ms local)
- But eliminating the 50% of requests that cost 50-200ms (DB hits) makes overall P99 **7x faster**

### Topology 3: Replicated (In-Process) Cache — REJECTED

```
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │ ┌─────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │
  │ │Cache 5GB│◄├───┤►│Cache 5GB│◄├───┤►│Cache 5GB│ │
  │ └─────────┘ │   │ └─────────┘ │   │ └─────────┘ │
  └─────────────┘   └─────────────┘   └─────────────┘
       ▲                  ▲                  ▲
       └──── async replication ──────────────┘
```

**Rejected because:**

- **Memory multiplication:** 200 instances × 5GB = 1TB total RAM (vs 30GB for a 6-node Couchbase cluster — 33x savings)
- **Replication bandwidth:** 1000 changes/sec × 5KB × 200 instances = 1GB/s internal traffic
- **Inconsistency window:** Async replication means different nodes briefly show different prices — unacceptable for a pricing system
- **Doesn't solve capacity:** Each instance still needs enough RAM for the full dataset

### Topology 4: Near-Cache Hybrid — NOT SELECTED

```
  ┌─────────────────────────────────┐
  │          PDS Node               │
  │  ┌───────────┐  ← L1: 100MB    │
  │  │ Local     │    (hot items)   │
  │  └─────┬─────┘                  │
  │        │ miss                   │
  │  ┌─────▼─────┐  ← L2: Couchbase│
  │  │ Remote    │    (full dataset)│
  │  └─────┬─────┘                  │
  │        │ miss                   │
  │  ┌─────▼─────┐                  │
  │  │ Database  │                  │
  │  └───────────┘                  │
  └─────────────────────────────────┘
```

Best theoretical performance, but rejected for:

- **Diminishing returns:** Couchbase at 15ms P99 already meets SLA; L1 saves 15ms per hit
- **L1 invalidation complexity:** TTL-based (staleness), event-based (pub/sub overhead), version-based (partial network cost defeat)
- **Operational complexity:** Two cache layers to monitor, tune, and debug at 1M RPS across 4 DCs

### Decision Matrix

| Requirement | Standalone | Distributed | Replicated | Near-Cache |
|---|---|---|---|---|
| High capacity | No | **Yes** | No | Yes |
| Fast reads | **Yes** | Moderate | **Yes** | Yes/Moderate |
| Data consistency | N/A | **Yes** | No (async) | Moderate |
| High update rate | **Yes** | **Yes** | Problematic | Moderate |
| Fault tolerance | No | With replication | Yes | Yes |

PDS needed: **fast + high capacity + consistent + high update rate** → **Distributed**.

---

## 5. Why Couchbase

| Property | How It Helps PDS |
|---|---|
| Memory-first architecture | Sub-millisecond to low-ms KV reads |
| Key-value storage model | Simple get-by-key (hotel_id → metadata) — no complex queries |
| High concurrency | Handles 1M+ concurrent requests |
| Fault tolerance via replication | Data replicated across nodes; node failure doesn't lose data |
| Masterless architecture | Every node handles reads/writes; no single bottleneck; easy horizontal scaling |
| Already in Agoda's ecosystem | Existing operational expertise, monitoring, client libraries |

### vBucket Internals

Couchbase divides keyspace into **1024 virtual buckets (vBuckets)**. Each document hashes to a vBucket. Each vBucket has an **active** copy on one node and **replica** copies on other nodes.

```
hotel_id "H_12345" → hash → vBucket 217 → active: Node A, replica: Node B
hotel_id "H_67890" → hash → vBucket 850 → active: Node C, replica: Node A
```

Client SDK maintains a **cluster map** showing which node owns which vBucket. On node failure, the map updates automatically.

---

## 6. Caching Strategy Selection

### Read-Through
On miss, cache fetches from DB, stores, returns. **Bad for:** cold starts still hit DB hard.

### Write-Through
Writes go to cache first, then sync to DB. **Not relevant:** PDS metadata is read-heavy.

### Write-Behind (Existing)
On miss, read DB; async write to cache. **Bad for:** high variability traffic (affiliates). Each cache fill is wasted if the next request is for a different hotel.

### Pre-Caching — SELECTED
Load data into cache **before** serving requests. **Hot cache** = entire dataset loaded.

```
Write-behind + variable traffic:
  Hotel A → miss → DB → cache A → Hotel B → miss → DB → cache B
  (never revisits A → wasted work)

Pre-caching + variable traffic:
  ALL hotels pre-loaded → Hotel A hit, Hotel B hit, Hotel C hit
  100% hit rate, zero DB fallback
```

---

## 7. Pre-Caching Implementation

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scheduled   │────►│    Apache    │────►│  Pre-cache   │────►│  Couchbase   │
│  Producer    │     │    Kafka     │     │  Builders    │     │  Cluster     │
│ (every 20min)│     │(shared queue)│     │(N consumers) │     │(per DC)      │
└──────────────┘     └──────────────┘     └──────┬───────┘     └──────────────┘
                                                 │
                                          ┌──────▼───────┐
                                          │   Source     │
                                          │   Database   │
                                          └──────────────┘
```

| Component | Role |
|---|---|
| **Scheduled Producer** | Emits all hotel IDs into Kafka every 20 minutes |
| **Kafka** | Buffers hotel IDs, enables parallel consumption, controls DB load rate |
| **Pre-cache Builders** | Multiple consumers read hotel IDs, fetch metadata from DB, write to Couchbase |
| **Couchbase Clusters** | Separate cluster per DC (4 total) to avoid cross-DC latency |

### Full Sync Strategy

Entire dataset refreshed every 20 minutes. No delta/diff tracking.

**Why not delta sync initially:**
- Metadata computed from many related tables (rates, taxes, promotions, rate plans, blackout dates, commissions, surcharges, currency rules)
- Tracking which row change in which table affects which hotel = substantial project
- Full sync: simpler, reliable, guaranteed fresh

---

## 8. Kafka Consumer Group Mechanics

### Partition Assignment

```
KAFKA TOPIC: "hotel-sync" (e.g., 50 partitions)

  Partition 0  → Builder 1
  Partition 1  → Builder 2
  Partition 2  → Builder 3
  ...
  Partition 49 → Builder 10 (gets multiple partitions)
```

Rule: each partition consumed by **exactly one** consumer in the group. No duplicate processing.

### Offset Tracking

```
Partition 0: [H_1] [H_4] [H_7] [H_10] [H_13] ...
                                  ↑
                    Consumer offset = 3 (processed H_1, H_4, H_7)
```

If consumer crashes → restarts from last committed offset. Reprocessing is safe because Couchbase upserts are idempotent.

### Rebalancing

When a consumer joins/leaves, Kafka redistributes partitions:

```
Before (3 consumers):    After Builder 3 crashes (2 consumers):
  Builder 1 → P0, P1      Builder 1 → P0, P1, P4  ← picks up P4
  Builder 2 → P2, P3      Builder 2 → P2, P3, P5  ← picks up P5
  Builder 3 → P4, P5      (automatic redistribution)
```

### Rate Control (Preventing Cache Stampede)

Without Kafka: Producer emits 5M IDs → all builders blast the DB simultaneously → DB overloads.

With Kafka:
- `max.poll.records` limits messages per poll (e.g., 100)
- Each builder: poll 100 IDs → query DB → write Couchbase → poll 100 more
- DB sees steady ~1000 queries/sec instead of burst 50,000/sec

### Why Kafka Over Simpler Queues

| Feature | Kafka | RabbitMQ/SQS | Redis List |
|---|---|---|---|
| Throughput | Millions/sec | Tens of thousands/sec | Hundreds of thousands/sec |
| Durability | Disk-based log, replicated | Disk-based | Memory (loss risk) |
| Replayability | **Yes** (messages retained) | No | No |
| Consumer groups | Native | Manual ACK | Manual |
| Ordering | Per-partition guaranteed | Per-queue | FIFO |

---

## 9. Results

| Metric | Before | After | Improvement |
|---|---|---|---|
| P99 total API response | 460 ms | ~368 ms | **~20% faster** |
| P99 metadata retrieval | 110 ms | ~15 ms | **~87% faster (7.3x)** |
| Cache hit ratio | 50% | ~100% | **Eliminated DB fallback** |
| Cold start impact | Thundering herd | None | **No DB spikes** |

---

## 10. Data Center Failover

### Architecture: 4 Independent DCs

```
        DC-1 (Singapore)    DC-2 (Hong Kong)    DC-3 (US-East)    DC-4 (EU-West)
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
        │ PDS Instances│    │ PDS Instances│    │ PDS Instances│   │ PDS Instances│
        │ Couchbase    │    │ Couchbase    │    │ Couchbase    │   │ Couchbase    │
        │ Kafka        │    │ Kafka        │    │ Kafka        │   │ Kafka        │
        │ Pre-cache    │    │ Pre-cache    │    │ Pre-cache    │   │ Pre-cache    │
        └──────────────┘    └──────────────┘    └──────────────┘   └──────────────┘
```

Each DC is self-contained for cache serving. Cross-DC queries are never attempted (50-200ms latency would defeat the purpose).

### Failure Scenarios

#### Couchbase Node Failure (Within DC)

- vBucket replicas on surviving nodes are **promoted to active** (~30 sec)
- Client SDK gets updated cluster map, redirects reads automatically
- **Zero data loss**, brief blip during failover
- Cluster enters degraded state (missing replicas) until failed node recovers or is replaced

#### Entire Couchbase Cluster Down (Within DC)

- PDS falls back to source database (degraded latency: 15ms → 50-200ms)
- Global load balancer detects DC health failure, reroutes traffic to nearest healthy DC
- Both happen simultaneously — no hard user-facing failure

#### Pre-cache Builder Failure

- Couchbase retains all existing data (persistent, not just in-memory)
- PDS continues serving with 100% hit rate
- Data gets progressively stale, but hotel prices rarely change minute-to-minute
- Kafka retains unprocessed messages until builders recover
- On recovery: builders consume backlog and catch up

#### Source Database Failure

- Couchbase serves ALL requests from existing cache — **users unaffected**
- Pre-cache Builders fail to sync, data gets stale over hours
- Most prices remain correct (infrequent changes)
- On DB recovery: full sync completes in ~15 minutes

#### Kafka Failure

- Producer can't publish, builders have no work
- Couchbase serves existing data (up to 20 min stale initially, growing)
- Kafka itself is a distributed replicated system — designed for high availability

#### Entire DC Failure

- GeoDNS/load balancer reroutes to nearest healthy DC (~1-5 min)
- Users experience slightly higher network latency but full functionality

### Failure Impact Summary

| Component Failed | Serves Requests? | Data Freshness | Recovery |
|---|---|---|---|
| 1 Couchbase node | Yes (brief blip) | Fresh | ~30 sec (auto) |
| All CB nodes in DC | Yes (degraded/rerouted) | Fresh (other DC) | Minutes |
| Pre-cache Builders | Yes | Stale (grows) | Auto on restart |
| Kafka cluster | Yes | Stale (grows) | Auto on recovery |
| Source Database | Yes | Stale (hours ok) | Depends on DB |
| Entire DC | Yes (other DCs) | Fresh | GeoDNS ~1-5 min |

**Key insight:** In every failure scenario, PDS continues serving. Worst case is stale data, never downtime. This is **graceful degradation** — trading freshness for availability, the right trade-off for pricing.

---

## 11. CDC — The Next Evolution

### The Problem with Full Sync

```
Every 20 minutes: read ALL 5M hotels → write ALL to Couchbase

Reality: only ~10,000 hotels changed in the last 20 minutes

Waste ratio: 5,000,000 / 10,000 = 500x unnecessary work
```

Three compounding issues:
1. **DB load:** 5M reads every 20 min on a database also serving live traffic
2. **Sync duration:** As hotels grow (5M → 10M), sync may exceed 20-minute window
3. **Freshness lag:** Up to 19 minutes of serving stale prices after a change

### What Is CDC?

**Change Data Capture** — captures row-level changes in a database as a stream of events. SQL Server's built-in CDC reads the transaction log (already written for ACID compliance) and copies changes to dedicated **change tables**. No triggers, no app code changes, minimal performance impact.

```
SQL Server Transaction Log
        │
        ▼
CDC Capture Process (reads log)
        │
        ▼
Change Tables (cdc.hotel_rates_CT)
  - __$operation: 2=INSERT, 3=before-update, 4=after-update, 1=DELETE
  - __$start_lsn: log sequence number (position marker)
  - All original columns
```

### Why CDC Was Hard Initially

PDS metadata is computed from **many related tables**:

```
hotel_rates → base prices
hotel_taxes → tax rules per region
promotions  → discounts, deals
rate_plans  → package configs
blackout_dates → unavailability
commission  → affiliate rates
surcharges  → extra fees
currency_rules → exchange configs
```

A change in ANY table can affect hotel metadata. The **change-to-hotel mapping** problem:

```
promotions.row_changed(promo_id=999)
  → Which hotels use promo 999?
  → Requires: promotions → promo_hotel_mapping → rate_plans → hotel_rates
  → Result: [H_123, H_456, H_789, ...]
  → Action: recompute ONLY these hotels
```

Each source table needs its own correlation logic. Some changes (like currency rule updates) can affect hundreds of thousands of hotels.

### CDC-Based Architecture

```
Source Tables (with CDC enabled)
        │
        ▼
CDC Reader / Poller (every ~30 seconds)
        │
        ▼
Change-to-Hotel Mapper (correlates row changes to affected hotels, deduplicates)
        │
        ▼
Kafka (only changed hotel IDs — ~10K instead of 5M)
        │
        ▼
Pre-cache Builders (same as before, but 500x less work)
        │
        ▼
Couchbase (upsert only changed docs)
```

### Full Sync vs. CDC Comparison

| Dimension | Full Sync | CDC |
|---|---|---|
| Hotels per cycle | 5,000,000 | ~10,000 |
| Cycle interval | 20 minutes | ~30 seconds |
| DB queries per cycle | 5,000,000 | ~10,000 |
| Max staleness | 20 minutes | ~30 seconds |
| DB load | ~4,200 queries/sec | ~333 queries/sec (12.5x less) |

### CDC Edge Cases

**Fan-out problem:** A single change (global tax update) can affect 800K hotels → near-full-sync load. Mitigated by priority queuing and batching.

**Ordering:** Kafka guarantees order within a partition. Partition by hotel_id → all changes for one hotel are ordered correctly.

**Idempotency:** Couchbase upserts are idempotent → at-least-once delivery from Kafka is safe (no need for exactly-once complexity).

**Schema evolution:** Adding a new source table requires enabling CDC on it, adding mapping logic, running one full sync for backfill, then switching to CDC.

**LSN management:** Log Sequence Numbers track "where we left off." Must be checkpointed durably — if lost, CDC data may have been cleaned up past the retention period.

---

## 12. Key Concepts Glossary

| Concept | Definition |
|---|---|
| **P99 latency** | 99th percentile — 99% of requests are faster than this value. Represents the "worst case" for 1 in 100 users. |
| **LRU (Least Recently Used)** | Eviction policy that removes the item accessed longest ago. Fails when working set exceeds capacity (thrashing). |
| **Cache stampede / thundering herd** | When a cold cache causes all requests to simultaneously hit the database, potentially overwhelming it. |
| **Working set** | The set of items that are actively being accessed. If larger than cache, hit rate collapses. |
| **vBucket** | Couchbase's virtual partition unit. 1024 vBuckets divide the keyspace. Each has active + replica copies on different nodes. |
| **Masterless architecture** | Every node can handle reads and writes. No single master bottleneck. Easy horizontal scaling. |
| **Pre-caching** | Loading data into cache before application serves requests. Hot cache = entire dataset loaded. |
| **Write-behind** | On cache miss, data read from DB and asynchronously written to cache. Fails with variable traffic patterns. |
| **CDC (Change Data Capture)** | Pattern that captures row-level DB changes as event streams. SQL Server reads its own transaction log. |
| **LSN (Log Sequence Number)** | Position marker in SQL Server's transaction log. Used by CDC to track "where we left off." |
| **Consumer group** | Kafka concept where multiple consumers share work on a topic. Each partition assigned to exactly one consumer. |
| **Rebalancing** | Kafka's automatic redistribution of partitions when consumers join/leave a group. |
| **Idempotent** | An operation that produces the same result whether executed once or multiple times. Couchbase upserts are idempotent. |
| **Graceful degradation** | System continues operating at reduced quality (stale data) rather than failing completely. |
| **GeoDNS** | DNS that routes users to the nearest data center based on geographic location. Enables DC-level failover. |

---

## System Evolution Timeline

```
Phase 1 (Original):
  Standalone in-memory cache + write-behind
  → 50% hit rate, cold start stampedes

Phase 2 (Article):
  Distributed Couchbase + pre-caching + full sync via Kafka
  → 100% hit rate, 20% faster total response, 15ms P99 metadata

Phase 3 (Future):
  Same architecture + CDC-based delta sync
  → 12x less DB load, 30-second staleness

Phase 4 (Speculative):
  Near-cache hybrid (local L1 + Couchbase L2) + CDC
  → Sub-ms for hot data, 30-second freshness
```

---

*Related: See [01-beginner.md](./01-beginner.md), [02-intermediate.md](./02-intermediate.md), [03-expert.md](./03-expert.md) for Agoda's Image Platform — a different system that also uses Couchbase for serving enriched image metadata.*
