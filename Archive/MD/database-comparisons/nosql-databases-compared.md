# NoSQL Databases Compared: A System Design Guide

This guide covers **MongoDB**, **CouchDB**, **PostgreSQL (as SQL contrast)**, **DynamoDB**, **Apache Cassandra**, **ScyllaDB**, and **Azure Cosmos DB**—the document, wide-column, and managed NoSQL landscape for interviews and production design.

> **Key insight:** NoSQL wins when **access patterns are known upfront** and you optimize for partition keys, replication, and tunable consistency—not when you need ad-hoc relational queries across many entities.

---

## The NoSQL Landscape

| Category | Examples in this guide | Sweet spot |
|----------|------------------------|------------|
| Document | MongoDB, CouchDB, DynamoDB (document mode) | Flexible records, nested data |
| Wide-column | Cassandra, ScyllaDB, Cosmos (Cassandra API) | Massive writes, time-series, events |
| Managed key-value / document | DynamoDB, Cosmos DB | Zero ops, cloud-native scale |

```mermaid
flowchart TB
  subgraph Document["Document stores"]
    M[MongoDB - primary/shard]
    C[CouchDB - multi-master sync]
  end
  subgraph Wide["Wide-column"]
    Cas[Cassandra - JVM ring]
    Scy[ScyllaDB - C++ shard/core]
  end
  subgraph Cloud["Fully managed"]
    DDB[DynamoDB - AWS]
    Cosmos[Cosmos DB - Azure multi-API]
  end
  App[Application] --> Document
  App --> Wide
  App --> Cloud
```

---

## Database Overviews

### MongoDB

**BSON documents** in collections; schema-on-read. WiredTiger engine, document-level locking. Replica sets + **sharding** with shard keys.

**Strengths:** Flexible queries, aggregation pipeline, horizontal scale for document workloads.  
**Weaknesses:** Schema discipline is app-side; cross-shard transactions are harder than SQL.

### CouchDB

Append-only **B-tree**, **multi-master replication**, conflict resolution via document revisions. PouchDB on clients for offline-first.

**Strengths:** Offline sync, deterministic conflict handling.  
**Weaknesses:** MapReduce views vs Mongo’s aggregation; less throughput for typical server workloads.

### PostgreSQL (contrast—not NoSQL)

Schema-on-write, ACID, joins, **JSONB** for hybrid models. Horizontal writes need Citus/CockroachDB.

Use when relational integrity and complex SQL matter more than native document sharding.

### DynamoDB

AWS **managed** key-value and document store. Auto partition, 3-AZ replication, partition key + sort key + **GSI** access patterns.

**Strengths:** Single-digit ms latency at scale, zero ops.  
**Weaknesses:** Access-pattern-driven modeling; scans are expensive; AWS lock-in.

### Apache Cassandra

Peer-to-peer **ring**, consistent hashing, tunable consistency. You operate JVM, compaction, and hardware.

**Strengths:** Multi-cloud, predictable infra cost at huge scale (Apple, Netflix historically).  
**Weaknesses:** GC tail latency; heavy tuning.

### ScyllaDB

**Cassandra-compatible CQL**, C++ **shard-per-core** (Seastar), no JVM GC pauses. **Alternator** = DynamoDB-compatible API.

**Strengths:** 2–10× throughput, much lower P99 vs Cassandra; 5–10× cheaper than DynamoDB at very high OPS (with ops team).  
**Weaknesses:** AGPL license vs Apache Cassandra; smaller ecosystem.

### Azure Cosmos DB

**Multi-model** APIs (SQL, MongoDB, Cassandra, Gremlin, Table) on ARS storage. **Five consistency levels** (Strong → Eventual).

**Strengths:** Fine-grained consistency per request; multi-region writes.  
**Weaknesses:** RU pricing complexity; ecosystem smaller than DynamoDB on AWS.

---

## Architecture Differences

```mermaid
sequenceDiagram
  participant Client
  participant Mongo as MongoDB Primary
  participant Shard as MongoDB Shard

  Client->>Mongo: write
  Mongo->>Shard: route by shard key

  participant DDB as DynamoDB
  Client->>DDB: PutItem(partition_key)
  Note over DDB: Auto split partitions

  participant Cas as Cassandra Ring
  Client->>Cas: CQL (coordinator)
  Cas->>Cas: replicate RF nodes
```

| System | Replication model | Write path | Query flexibility |
|--------|-------------------|------------|-------------------|
| MongoDB | Primary per shard/replica set | Single primary per shard | High (indexes on fields) |
| CouchDB | Multi-master | Any node | Views / MapReduce |
| DynamoDB | Managed 3-AZ | Partition leader | Low (keys + GSIs) |
| Cassandra | Quorum on ring | Any coordinator | CQL by partition key |
| ScyllaDB | Same as Cassandra | Per-shard | Same as Cassandra |
| Cosmos DB | Regional replicas | Multi-region option | API-dependent |

---

## Feature Comparison Table

| Feature | MongoDB | CouchDB | DynamoDB | Cassandra | ScyllaDB | Cosmos DB |
|---------|---------|---------|----------|-----------|----------|-----------|
| Ops model | Self / Atlas | Self | Fully managed | Self | Self / cloud | Fully managed |
| Offline-first | Via sync layers | **Excellent (PouchDB)** | No | No | No | Limited |
| Ad-hoc queries | **Strong** | Moderate | **Weak** | Partition-bound | Partition-bound | API-dependent |
| Global scale | Sharding | Replication | Global Tables | Multi-DC | Multi-DC | Multi-region |
| Consistency | Tunable (replica set) | Eventual + conflicts | Strong per item / GSIs | Tunable quorum | Tunable | **5 levels** |
| License / cloud | SSPL / various | Apache | AWS only | Apache | AGPL | Azure |

---

## Performance Characteristics

| Workload | Guidance |
|----------|----------|
| Single-document read/write | **MongoDB**, **DynamoDB** |
| Complex multi-entity SQL | **PostgreSQL** (not pure NoSQL) |
| Predictable ms latency at any size | **DynamoDB**, **Cosmos DB** (SLA-backed) |
| Highest write throughput / lowest tail latency (self-hosted) | **ScyllaDB** > **Cassandra** |
| Cost at millions OPS/sec | **ScyllaDB** on hardware vs **DynamoDB** per-request |
| Offline mobile sync | **CouchDB** + PouchDB |

> **DynamoDB vs MongoDB:** DynamoDB = access patterns designed upfront (often single-table design). MongoDB = more flexible queries; cost is compute/RAM more than per-read units.

> **Discord migration:** Cassandra → ScyllaDB cut nodes (177 → 72) and improved P99 (~40–125 ms → ~15 ms).

---

## Code Examples

### MongoDB — document + aggregation

```javascript
// Node.js driver
await db.collection("orders").insertOne({
  _id: ObjectId(),
  userId: "u42",
  items: [{ sku: "A1", qty: 2 }],
  status: "placed",
});

const pipeline = [
  { $match: { status: "placed" } },
  { $group: { _id: "$userId", total: { $sum: 1 } } },
];
await db.collection("orders").aggregate(pipeline).toArray();
```

### CouchDB — replication-friendly document

```javascript
const nano = require("nano")("http://admin:pass@localhost:5984");
const db = nano.db.use("inventory");

const doc = await db.insert({ _id: "sku-1", qty: 10, type: "part" });
// Revisions (_rev) enable multi-master conflict resolution
```

### DynamoDB — partition + sort key

```javascript
import { DynamoDBClient, PutItemCommand, QueryCommand } from "@aws-sdk/client-dynamodb";

const client = new DynamoDBClient({});

await client.send(new PutItemCommand({
  TableName: "Orders",
  Item: {
    PK: { S: "USER#u42" },
    SK: { S: "ORDER#2026-001" },
    total: { N: "99.50" },
  },
}));

// Query all orders for user (access pattern must match key design)
await client.send(new QueryCommand({
  TableName: "Orders",
  KeyConditionExpression: "PK = :pk AND begins_with(SK, :prefix)",
  ExpressionAttributeValues: {
    ":pk": { S: "USER#u42" },
    ":prefix": { S: "ORDER#" },
  },
}));
```

### Cassandra / ScyllaDB — CQL wide-column

```sql
CREATE TABLE events (
  user_id UUID,
  event_time TIMESTAMP,
  event_type TEXT,
  payload TEXT,
  PRIMARY KEY ((user_id), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);

INSERT INTO events (user_id, event_time, event_type, payload)
VALUES (uuid(), toTimestamp(now()), 'click', '{"page":"/home"}');

SELECT * FROM events WHERE user_id = ? LIMIT 100;
```

### Cosmos DB — Core (SQL) API (conceptual)

```sql
-- Container with partition key /userId
SELECT c.id, c.total
FROM c
WHERE c.userId = "u42" AND c.status = "open"
```

---

## Use-Case Recommendations

| Scenario | Pick |
|----------|------|
| Product catalog, content, IoT documents | **MongoDB** |
| Field apps, offline-first sync | **CouchDB** |
| AWS serverless, known access patterns (cart, dispatch) | **DynamoDB** |
| Multi-cloud huge event store, ops team in-house | **Cassandra** |
| Cassandra compatibility + lower latency/cost | **ScyllaDB** |
| Azure, multi-API, tunable consistency | **Cosmos DB** |
| Money, reporting, joins | **PostgreSQL** (often alongside NoSQL) |

**Real-world references:** DynamoDB (Amazon cart, Lyft, Snap); MongoDB (eBay, Forbes); Cassandra (Apple scale); Cosmos (Coca-Cola, UN); ScyllaDB (Discord).

---

## Decision Matrix

| Criterion (1–5) | MongoDB | CouchDB | DynamoDB | Cassandra | ScyllaDB | Cosmos DB |
|-----------------|:-------:|:-------:|:--------:|:---------:|:--------:|:---------:|
| Query flexibility | 5 | 3 | 2 | 3 | 3 | 4 |
| Zero ops | 3 | 2 | 5 | 1 | 2 | 5 |
| Write scale / tail latency | 4 | 2 | 5 | 4 | 5 | 5 |
| Multi-cloud portability | 4 | 5 | 1 | 5 | 4 | 2 |
| Offline sync | 2 | 5 | 1 | 1 | 1 | 1 |
| Predictable cloud billing | 3 | 3 | 2 | 4 | 4 | 2 |

---

## When to Use What

| Choose | When |
|--------|------|
| **MongoDB** | Document model, rich queries, sharding without going full SQL |
| **CouchDB** | Multi-master replication and offline clients are core requirements |
| **DynamoDB** | AWS-native, massive scale, ms latency, ops-free—model keys first |
| **Cassandra** | Petabyte writes, multi-cloud, team can run distributed JVM clusters |
| **ScyllaDB** | Cassandra-like workloads with better P99 and node efficiency |
| **Cosmos DB** | Azure shop, multiple APIs, or per-request consistency tuning |
| **PostgreSQL** | Transactions, joins, and JSONB hybrid—pair with NoSQL for scale-out slices |

---

*Sources: Algoroq comparisons for MongoDB vs PostgreSQL/CouchDB, DynamoDB vs MongoDB/Cassandra, Cassandra vs ScyllaDB, ScyllaDB vs DynamoDB, Cosmos DB vs DynamoDB, and SQL vs NoSQL.*

---

## Senior Pitfalls

| Mistake | Impact | Fix |
|---------|--------|-----|
| MongoDB multi-document updates without transactions where invariants span docs | Partial updates corrupt balances or inventory | Use multi-doc transactions or single-document embedding; design idempotent compensations |
| Cassandra `ALLOW FILTERING` in API queries | Full cluster scans; latency and ops incidents | Query by partition key only; secondary indexes only for low-cardinality admin paths |
| DynamoDB GSI with write-heavy base table and many GSIs | Write amplification doubles cost and throttles | Consolidate access patterns; project only needed attributes; use sparse GSIs |
| Couchbase/CouchDB sync without conflict resolution policy | Silent LWW overwrites merge user edits | Explicit revision trees, CRDTs, or domain merge functions; test offline replay |
| Cosmos DB session consistency assumed for financial reads | Stale reads after regional failover | Pick consistency per operation; use strong or bounded staleness for money paths |
| Scylla/Cassandra repair neglected after node replace | Gradual data divergence across replicas | Automate repair schedules; monitor `pending repair`; validate with read repair metrics |

---

## Production-grade Practice

1. **Partition skew simulation:** Build a Cassandra or DynamoDB load test with 80/20 key distribution. Graph P99 latency and node-level load; redesign keys until coefficient of variation is acceptable.
2. **MongoDB schema migration:** Migrate a 200GB collection from nested arrays to reference pattern using rolling dual-read. Measure oplog lag and application error rate during each batch.
3. **NoSQL vs SQL slice:** Pick one join-heavy report currently on MongoDB. Prototype the same in PostgreSQL with JSONB; compare dev velocity, query cost, and replication story for your team.
4. **Compaction tombstone incident replay:** In Kafka/Cassandra changelog topic, reproduce tombstone-heavy delete pattern; observe read amplification and document safe `gc_grace_seconds` / compaction strategy.

---

## FAANG Interview Deep Dive

### Real-world examples

**Meta Cassandra (messaging, social graphs at scale)**  
Meta operates among the largest **Cassandra** deployments—**exabytes** on disk, **thousands** of nodes per logical cluster. Writes favor **append + TTL**; **LOCAL_QUORUM** balances **latency vs consistency**. Interview depth: **repair**, **compaction**, and **hot partitions** are ops reality—not “just add nodes.”

**Amazon DynamoDB (Prime Day)**  
DynamoDB powers **shopping cart, sessions, and high-QPS key-value** paths with **single-digit ms** at **millions of requests/s** during peaks. **On-demand** scales capacity; **partition key design** determines success—**10GB/partition** soft limit, **3000 RCU / 1000 WCU** per partition baseline on provisioned mode.

**Netflix Cassandra + Elasticsearch**  
Netflix uses **Cassandra** for **high-volume viewing activity** and **Elasticsearch** for search—**not** one NoSQL. Candidates should articulate **why wide-column** beats document store for **time-ordered append** at **petabyte** scale.

| Store | Typical hot partition symptom |
|-------|------------------------------|
| DynamoDB | Throttling on one key |
| Cassandra | Single node CPU spike |
| MongoDB | Chunk jumbo on shard |

### Interview Q&A

### Q: DynamoDB vs Cassandra—same problem?
**A:** Both **partition-first**. **DynamoDB**: managed, **per-request billing**, limited ad-hoc query. **Cassandra**: self/managed, **CQL**, multi-cloud, team owns **compaction/repair**. Pick Dynamo for **AWS-native speed**; Cassandra for **portability** and **sustained write floods** with tuned ops.

### Q: How do you choose a partition / shard key?
**A:** Key must spread **write heat** (avoid monotonic `timestamp` alone). Patterns: **hash(user_id)**, **composite (tenant_id, item_id)**, **write sharding** with suffix buckets. Validate with **top-key metrics**—one key > **10%** traffic is a redesign signal.

### Q: MongoDB when not to use?
**A:** **Multi-document ACID across shards** still harder than Postgres; **unbounded document growth** without schema discipline; **analytics** without proper indexing. Good for **flexible product catalog**, **content** with known access paths.

### Q: ScyllaDB vs Cassandra for same schema?
**A:** **Scylla** (C++ **shard-per-core**) often delivers **lower P99** and **better node efficiency** on large boxes—**fewer nodes** for same throughput. Trade-off: smaller community, migration testing, **different tuning** defaults.

### Q: Cosmos DB multi-API—benefit or trap?
**A:** Benefit: **one bill**, **global distribution**, API choice (SQL, Cassandra, Mongo). Trap: **mental model mismatch**—Cassandra API on Cosmos ≠ full OSS Cassandra semantics; **verify** conflict resolution and **RUs** pricing per pattern.

### Common mistakes candidates make

- **Celebrity key** (global counter, popular post ID) without sharding suffixes.
- **Strong consistency everywhere** on Dynamo/Cassandra—kills **multi-region** latency.
- Treating **MongoDB** as schemaless **forever**—indexes and document shape still matter.
- **Dynamo scans** for reporting instead of **Streams → warehouse**.
- Ignoring **tombstone** and **GC grace** issues in Cassandra deletes.

### Decision framework

```mermaid
flowchart TD
  W[Write rate > 100k/s?] -->|yes| WC[Wide-column / Dynamo]
  W -->|no| D[Document OK?]
  D -->|flex schema| M[MongoDB]
  D -->|AWS serverless| DD[DynamoDB]
```

**WCU math (DynamoDB):** 1 WCU = **1KB write/s**. Item **4KB** → **4 WCU** per write. **10k writes/s × 4KB** → **40k WCU** provisioned (before bursts/on-demand pricing).

### Consistency quick pick

| API call | DynamoDB | Cassandra |
|----------|----------|-----------|
| Strong read | `ConsistentRead=true` (same item) | `SERIAL` / `ALL` (rare) |
| Default fast read | Eventually consistent | `LOCAL_ONE` / `LOCAL_QUORUM` |
| Multi-item txn | TransactWriteItems (same account) | LWT on one partition |

```python
# Hot key mitigation: write sharding suffix
pk = f"user#{user_id}#bucket#{user_id % 16}"
```

**Staff signal:** Meta-scale Cassandra interviews drill **repair**, **hinted handoff**, and **gc_grace_seconds** on deletes—ops depth separates senior from staff.
