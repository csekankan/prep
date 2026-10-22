# Database Types — Deep Dive for HLD Interviews

A complete reference for **which database to pick, why, and how to explain it** in system design interviews.

Covers **every major database and storage type** used in real systems — with internals, tradeoffs, scenarios, and interview scripts.

---

## Complete Taxonomy — All Database Types

```
STORAGE & DATABASE LANDSCAPE
│
├── OLTP (Online Transaction Processing) — fast reads/writes, row-level
│   ├── Relational (SQL)          → Postgres, MySQL, Oracle
│   ├── NewSQL                      → Spanner, CockroachDB, YugabyteDB
│   ├── Document                    → MongoDB, CouchDB, Firestore
│   ├── Key-Value                   → Redis, DynamoDB, Riak, etcd
│   ├── Wide-Column                 → Cassandra, HBase, ScyllaDB
│   ├── Graph                       → Neo4j, Neptune, JanusGraph
│   ├── Multi-Model                 → Cosmos DB, ArangoDB, Fauna
│   ├── Embedded / Edge             → SQLite, Realm, IndexedDB
│   └── Real-Time Sync              → Firebase, CouchDB, Supabase Realtime
│
├── OLAP (Online Analytical Processing) — aggregations over huge data
│   ├── Data Warehouse              → Snowflake, BigQuery, Redshift
│   ├── Columnar OLAP               → ClickHouse, Druid, Pinot
│   └── HTAP (Hybrid OLTP+OLAP)     → TiDB, SingleStore, AlloyDB
│
├── SPECIALIZED QUERY ENGINES
│   ├── Time-Series                 → InfluxDB, Prometheus, TimescaleDB
│   ├── Full-Text / Search          → Elasticsearch, Solr, Meilisearch
│   ├── Vector / ANN                → Pinecone, Milvus, pgvector, Weaviate
│   ├── Spatial / GIS                 → PostGIS, MongoDB Geo, Elasticsearch geo
│   ├── Graph Analytics             → TigerGraph, Neo4j GDS
│   └── Federated SQL               → Presto, Trino, Drill
│
├── DATA LAKE & LAKEHOUSE
│   ├── Object Storage (data lake)  → S3, GCS, Azure Blob, MinIO
│   ├── Table formats               → Delta Lake, Apache Iceberg, Apache Hudi
│   └── Lakehouse query             → Databricks, Athena, Snowflake external tables
│
├── IMMUTABLE & EVENT-DRIVEN
│   ├── Append-only ledger          → QLDB, immudb
│   ├── Event log / stream          → Kafka, Pulsar, Kinesis
│   └── Event sourcing stores       → EventStoreDB, Marten
│
├── CACHE & IN-MEMORY LAYER
│   ├── In-memory KV cache          → Redis, Memcached, KeyDB
│   ├── In-memory SQL               → SAP HANA, SingleStore (rowstore)
│   └── CDN / edge cache            → CloudFront, Fastly (not a DB, but storage layer)
│
├── BLOB & FILE STORAGE (not DBs, but always in HLD)
│   ├── Object storage              → S3, GCS (images, video, backups)
│   ├── Block storage               → EBS, persistent disks (DB under the hood)
│   └── File / NAS                  → NFS, EFS, HDFS
│
├── LEGACY / NICHE (know the name, rarely pick in new designs)
│   ├── Hierarchical                → IBM IMS (1960s mainframe)
│   ├── Network (CODASYL)           → IDMS (1970s)
│   ├── Object-Oriented DB          → db4o, ObjectStore
│   ├── XML-native                  → BaseX, eXist-db
│   └── RDF / Triple store          → Apache Jena, Virtuoso, Blazegraph
│
└── BLOCKCHAIN / DISTRIBUTED LEDGER
    └── Immutable chain             → Hyperledger, Ethereum (on-chain state)
```

**25+ types covered in this guide.** If an interviewer asks "what types of databases exist?" — start with the taxonomy above, then drill into 2-3 relevant to the problem.

---

## Table of Contents

1. [How to Answer in an HLD Interview](#how-to-answer-in-an-hld-interview)
2. [Foundations Every Interview Expects](#foundations-every-interview-expects)
3. [How Databases Are Built Internally](#how-databases-are-built-internally)
4. **[Deep Internals — Senior-Level Insights](#deep-internals--senior-level-insights)** *(new — isolation, MVCC, Raft, CRDT, LSM amp, CDC, pitfalls)*
   - [Transaction Isolation Levels & Anomalies](#1-transaction-isolation-levels--the-real-meat-of-acid)
   - [MVCC Mechanics](#2-mvcc--how-postgres--oracle-give-you-snapshot-reads-without-blocking-writers)
   - [Consensus: Paxos, Raft, 2PC, Saga](#3-consensus--paxos-raft-2pc-and-why-spanner-needs-atomic-clocks)
   - [Clocks, CRDTs, TrueTime](#4-clock-problems--lamport-vector-hlc-truetime)
   - [LSM Compaction & Amplification](#5-lsm-internals--compaction-amplification-bloom-filters)
   - [Query Optimizer & Joins](#6-query-optimizer--explain-plans-you-must-understand)
   - [Indexes Deep Dive](#7-indexes-deep-dive-beyond-add-an-index)
   - [CDC & Outbox Pattern](#8-change-data-capture-cdc--the-outbox-pattern)
   - [Partitioning & Hot Partitions](#9-partitioning-strategies-beyond-shard-by-user_id)
   - [Cache Stampede Solutions](#10-cache-stampede--thundering-herd--three-real-solutions)
   - [Backup, RPO, RTO](#11-backup-dr-rpo-rto--know-the-terms)
   - [Multi-Tenancy Strategies](#12-multi-tenancy--three-strategies)
   - [Message Queue Comparison](#13-message-queue-comparison-always-comes-up-with-kafka)
   - [Latency Numbers](#14-latency-numbers-every-engineer-should-memorize)
   - [DB Capacity Benchmarks](#15-capacity-numbers--rough-db-benchmarks)
   - [Per-DB Pitfalls](#16-database-specific-pitfalls-quote-these--instant-credibility)
   - [Idempotency Patterns](#17-idempotency--dedup-at-scale)
   - [Dynamo Quorum Math](#18-the-dynamo-quorum-math-interviewer-favorite)
   - ["Why Not X?" Answers](#20-when-interviewer-asks-why-not-x)
   - **[Signature Features Per DB](#21-signature-features-per-db--the-vocabulary-interviewers-expect)** *(Cassandra gossip/snitch/LWT, TSDB rollups/hypertables, Postgres JSONB/RLS, Redis streams/modules, Dynamo GSI/DAX, ES ILM, Kafka ISR/compaction, Snowflake time-travel, Spanner TrueTime, Vector HNSW/RRF, Iceberg time-travel)*
   - [Honest DB Scorecard](#22-the-honest-database-scorecard)
5. [OLTP Databases](#oltp-databases)
   - [Relational (SQL)](#1-relational-sql-databases)
   - [Wide-Column (Cassandra)](#2-wide-column--column-family-cassandra-hbase)
   - [Document (MongoDB)](#3-document-databases-mongodb)
   - [Key-Value (Redis, DynamoDB)](#4-key-value-stores-redis-dynamodb)
   - [Graph (Neo4j)](#6-graph-databases-neo4j)
   - [Multi-Model (Cosmos DB)](#14-multi-model-databases-cosmos-db-arangodb)
   - [Embedded / Edge (SQLite)](#11-embedded--edge-sqlite)
   - [Real-Time Sync (Firebase)](#15-real-time-sync-databases-firebase-couchdb)
6. [Specialized Query Engines](#specialized-query-engines)
   - [Time-Series](#5-time-series-databases-influxdb-timescaledb)
   - [Vector (pgvector)](#7-vector-databases-pinecone-pgvector)
   - [Search (Elasticsearch)](#8-search--full-text-engines-elasticsearch)
   - [Spatial / GIS (PostGIS)](#16-spatial--gis-databases-postgis)
7. [Analytics & Big Data](#analytics--big-data)
   - [OLAP / Warehouse](#9-olap--data-warehouses-bigquery-snowflake)
   - [HTAP](#17-htap-hybrid-transactional--analytical)
   - [Data Lake & Lakehouse](#18-data-lake--lakehouse-s3-delta-iceberg)
   - [Federated Query (Trino)](#19-federated-query-engines-presto-trino)
8. [Distributed SQL](#distributed-sql)
   - [NewSQL (Spanner)](#10-newsql-spanner-cockroachdb)
9. [Immutable & Event Stores](#immutable--event-stores)
   - [Ledger (QLDB)](#12-ledger--immutable-stores)
   - [Message Log (Kafka)](#13-message--log-stores-kafka-as-storage)
   - [Event Sourcing DB](#20-event-sourcing-databases-eventstoredb)
10. [Cache & In-Memory](#cache--in-memory)
    - [In-Memory SQL (HANA)](#21-in-memory-databases-sap-hana)
11. [Blob & File Storage](#blob--file-storage-not-databases-but-required-in-hld)
12. [Niche & Legacy](#niche--legacy-know-for-completeness)
    - [RDF / Triple Store](#22-rdf--triple-stores-semantic-web)
    - [Blockchain Ledger](#23-blockchain--distributed-ledger)
13. [Industry Examples at Scale](#industry-examples-at-scale--who-uses-what)
14. [Scale-Wise: Which DB Wins](#scale-wise-which-db-wins-at-what-size)
15. [Critical Problem Playbook](#critical-problem-playbook--flash-sale-payment-booking)
16. [Article Insights You Must Know](#article-insights-you-must-know)
17. [Master Comparison Table](#master-comparison-table)
18. [Scenario Playbook](#scenario-playbook--what-to-pick-when)
19. [Polyglot Persistence](#polyglot-persistence--real-system-examples)
20. [Interview Traps](#common-interview-traps-and-strong-answers)
21. [Complete Cheat Sheet](#complete-cheat-sheet--all-27-types)

---

## How to Answer in an HLD Interview

Never start with "I'll use MongoDB." Start with **requirements**, then **access patterns**, then **tradeoffs**.

### The 5-step script (memorize this)

```
1. DATA SHAPE     — What does a record look like? Fixed schema or flexible?
2. ACCESS PATTERN — Read-heavy? Write-heavy? Point lookup vs scan vs join?
3. CONSISTENCY    — Must reads see latest write immediately?
4. SCALE          — QPS, data size, growth, multi-region?
5. QUERY TYPE     — SQL joins? Time range? Graph traversal? Semantic search?
```

Then say:

> "Given [requirements], I'd use [DB] for [component] because [access pattern match].
> I'd also add [second DB] for [different pattern] — polyglot persistence."

**Interviewers reward:** naming tradeoffs, not picking one DB for everything.

---

## Foundations Every Interview Expects

### ACID (Relational default)

| Property | Meaning | Interview example |
|----------|---------|-------------------|
| **A**tomicity | All or nothing | Money transfer: debit + credit both succeed or both roll back |
| **C**onsistency | Rules always hold | Balance never negative; foreign keys valid |
| **I**solation | Concurrent txs don't corrupt each other | Two users booking same seat — one wins |
| **D**urability | Committed data survives crash | After "payment success", it stays even if server dies |

### BASE (Many NoSQL systems)

| Property | Meaning |
|----------|---------|
| **BA**sically available | System stays up even during partition |
| **S**oft state | State may change without input (replication lag) |
| **E**ventual consistency | Replicas converge over time |

**Say this:** "ACID for money and inventory. BASE for feeds, metrics, caches — where stale-by-seconds is OK."

### CAP Theorem

During a **network partition**, you can have at most **2 of 3**:

```
         Consistency
            /\
           /  \
          /    \
         /  ?   \
        /________\
 Availability   Partition tolerance
```

- **Partition tolerance** is non-negotiable in distributed systems → real choice is **CP vs AP**
- **CP:** refuse requests or return errors to stay consistent (banking, Spanner)
- **AP:** stay available, accept stale reads (social feed, Cassandra writes)

### PACELC (better than CAP for interviews)

> If **P**artition → choose **A** or **C**.
> **E**lse (normal operation) → choose **L**atency or **C**onsistency.

Example: DynamoDB is **PA/EL** — available during partition, favors latency over strong consistency by default.

### Read/Write patterns that drive DB choice

| Pattern | Best fit |
|---------|----------|
| Point read by ID | Key-value, SQL PK lookup, Cassandra partition key |
| Range scan by time | Time-series DB, Cassandra clustering key |
| Ad-hoc joins across entities | Relational SQL |
| Full-text search | Elasticsearch, OpenSearch |
| "Similar to this" | Vector DB |
| Friend-of-friend, shortest path | Graph DB |
| Aggregations over billions of rows | OLAP warehouse |
| High write throughput, denormalized | Cassandra, Kafka + OLAP |

---

## How Databases Are Built Internally

Interviewers love when you explain **why** a DB behaves the way it does.

### B-Tree (PostgreSQL, MySQL InnoDB, SQLite)

```
         [ 50 ]
        /      \
    [20,30]    [70,90]
    /  |  \    /  |  \
  rows on disk pages (ordered)
```

- **Optimized for:** range scans, ordered reads, moderate write rate
- **Writes:** find leaf page → update in place (with WAL for durability)
- **Reads:** O(log n) to find row; great for `WHERE id = ?` and `BETWEEN`
- **Problem at scale:** random writes to same page → lock contention

### LSM-Tree (Cassandra, RocksDB, LevelDB, DynamoDB storage)

```
WRITE PATH:
  memtable (RAM) → flush → SSTable (disk, immutable)
                         → compaction merges files

READ PATH:
  check memtable → check SSTables (newest first) → bloom filter skips
```

- **Optimized for:** **write-heavy** workloads (append, not random update)
- **Writes:** fast sequential append to memtable
- **Reads:** slower than B-tree (may check multiple SSTables) — mitigated by bloom filters
- **Compaction:** background merge — causes latency spikes if not tuned

**Say:** "Cassandra is LSM-based — great for append-only event logs and high ingest; less ideal for frequent updates to same row."

### Storage layout comparison

| Engine | Write speed | Read speed | Update same row | Typical DBs |
|--------|-------------|------------|-----------------|-------------|
| B-Tree | Moderate | Fast | Good | Postgres, MySQL |
| LSM-Tree | Very fast | Moderate | Poor (rewrite) | Cassandra, RocksDB |
| Columnar | Batch only | Analytics fast | Bad for OLTP | Parquet, ClickHouse |
| In-memory | Fastest | Fastest | Good (if fits RAM) | Redis |

### Replication models

| Model | How it works | Consistency |
|-------|--------------|-------------|
| **Primary-replica** | Writes to leader, async copy to followers | Eventual (followers lag) |
| **Sync replica** | Write waits for N replicas | Stronger, higher latency |
| **Multi-leader** | Multiple nodes accept writes | Conflict resolution needed |
| **Leaderless (quorum)** | W nodes write, R nodes read, W+R>N | Tunable (Cassandra) |

### Sharding (horizontal partitioning)

```
         Router / consistent hash
              |
    +---------+---------+---------+
 Shard 0    Shard 1    Shard 2
 users      users      users
 0-33M      33-66M     66-100M
```

- **Key choice matters:** shard by `user_id` → all user data co-located
- **Bad shard key:** `created_at` → hot shard on today's date
- **Resharding** is painful — plan key design upfront

---

## Deep Internals — Senior-Level Insights

*What separates a strong HLD answer from a mediocre one. These are the topics interviewers push on once you name a DB.*

### 1. Transaction Isolation Levels — the real meat of ACID

The "I" in ACID is **tunable**. Picking the wrong level causes subtle production bugs that only show up at scale.

| Level | Dirty read | Non-repeatable read | Phantom read | Lost update | Write skew | Postgres default | Who uses |
|-------|------------|---------------------|--------------|-------------|------------|------------------|----------|
| **Read Uncommitted** | ✗ possible | ✗ | ✗ | ✗ | ✗ | — | Almost never |
| **Read Committed** | ✓ prevented | ✗ possible | ✗ | ✗ | ✗ | **Postgres, Oracle** | Default — most apps |
| **Repeatable Read** | ✓ | ✓ | ✗ (SQL std) ✓ (Postgres uses snapshot) | ✓ (Postgres) | ✗ possible | **MySQL InnoDB default** | Reports needing stable read |
| **Snapshot Isolation** | ✓ | ✓ | ✓ | ✓ | ✗ possible | Postgres `REPEATABLE READ` | Multi-row business invariants |
| **Serializable** | ✓ | ✓ | ✓ | ✓ | ✓ | Postgres SSI | Money, inventory, booking |

#### The anomalies — concrete examples (memorize these timelines)

Each example is a tx1 / tx2 timeline. **Time flows top-to-bottom.** Watch what breaks.

---

##### 🔴 Anomaly 1: Dirty Read (allowed only at Read Uncommitted)

**Setup:** Account balance table. `UPDATE accounts SET balance = 500 WHERE id = 1` — starts at 1000.

```
Time │ TX1 (Alice withdraws)                    │ TX2 (Bob checks Alice's balance)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN;                                   │
 t2  │ UPDATE balance = 500 WHERE id=1;         │
 t3  │  -- not committed yet                    │ BEGIN;
 t4  │                                          │ SELECT balance → reads 500 ❌
 t5  │ ROLLBACK;  -- tx failed                  │
 t6  │                                          │ -- Bob acted on 500, but reality is 1000
```

**Problem:** Bob saw a value that **never existed** in the committed database.
**Real impact:** Bob rejected Alice's loan based on $500 balance; actual balance was $1000.
**Prevented by:** Read Committed and above (every mainstream DB default).

---

##### 🟠 Anomaly 2: Non-Repeatable Read (allowed at Read Committed)

**Setup:** Monthly report queries same account twice during tx.

```
Time │ TX1 (Report generator)                  │ TX2 (Payment processor)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN; -- isolation = READ COMMITTED     │
 t2  │ SELECT balance FROM accounts WHERE id=1  │
 t3  │   → 1000                                 │
 t4  │                                          │ BEGIN;
 t5  │                                          │ UPDATE balance = 1200 WHERE id=1;
 t6  │                                          │ COMMIT;
 t7  │ -- some processing...                    │
 t8  │ SELECT balance FROM accounts WHERE id=1  │
 t9  │   → 1200 ❌ (different from t3!)        │
 t10 │ -- Report shows inconsistent totals       │
```

**Problem:** Same `SELECT`, same row, **different values** in one transaction.
**Real impact:** Invoice shows two different totals on the same page.
**Prevented by:** Repeatable Read and above.
**Why `REPEATABLE READ` fixes it:** Postgres/MySQL freeze a snapshot at tx start. Re-reads return the same version even if others committed changes.

---

##### 🟠 Anomaly 3: Phantom Read (SQL-standard behavior at Repeatable Read)

**Setup:** Match `WHERE amount > 1000` twice; a new matching row inserted between.

```
Time │ TX1 (Audit sum of large txns)           │ TX2 (New payment arrives)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN; -- REPEATABLE READ (SQL spec)     │
 t2  │ SELECT SUM(amount) WHERE amount > 1000   │
 t3  │   → 5000  (5 rows summed)                │
 t4  │                                          │ BEGIN;
 t5  │                                          │ INSERT INTO txns(amount) VALUES(2000);
 t6  │                                          │ COMMIT;
 t7  │ SELECT COUNT(*) WHERE amount > 1000      │
 t8  │   → 6 rows ❌ (was 5 at t3!)             │
 t9  │ -- Count and sum disagree                │
```

**Problem:** The predicate (`amount > 1000`) matched a **different set of rows** across reads — a "phantom row" appeared.
**Real impact:** Audit report inconsistent; invariants that depend on row set break.

> ⚠️ **PG quirk — this is where candidates lose points:**
> Postgres's `REPEATABLE READ` is actually **Snapshot Isolation**, which **does prevent phantoms** (because tx sees a frozen snapshot — the INSERT at t5 is invisible). MySQL InnoDB `REPEATABLE READ` also prevents phantoms via **gap locks** (locks ranges of index values).
>
> **So SQL-spec RR allows phantoms; Postgres and MySQL both strengthen it to disallow them. Serializable is needed for the next anomaly.**

---

##### 🔴 Anomaly 4: Lost Update (allowed at Read Committed; even at Repeatable Read in some DBs)

**The classic counter bug.** Two txs read-modify-write the same row.

```
Time │ TX1 (Increment likes +1)                │ TX2 (Increment likes +1)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN;                                   │
 t2  │ SELECT likes FROM post WHERE id=1        │
 t3  │   → 100                                  │
 t4  │                                          │ BEGIN;
 t5  │                                          │ SELECT likes FROM post WHERE id=1
 t6  │                                          │   → 100
 t7  │ UPDATE post SET likes=101 WHERE id=1;    │
 t8  │ COMMIT;                                  │
 t9  │                                          │ UPDATE post SET likes=101 WHERE id=1;
 t10 │                                          │ COMMIT;
 t11 │ -- Final value: 101 ❌  (should be 102!) │
```

**Problem:** Two increments → final value increased by 1 instead of 2. **One like was silently lost.**
**Real impact:** View counters, inventory decrement, credit balance — classic silent corruption.

**Fixes (pick one):**

```sql
-- Fix A: Pessimistic lock
BEGIN;
SELECT likes FROM post WHERE id=1 FOR UPDATE;  -- blocks other tx
UPDATE post SET likes = likes + 1 WHERE id=1;
COMMIT;

-- Fix B: Atomic update (no read-modify-write!)
UPDATE post SET likes = likes + 1 WHERE id=1;  -- one statement, no race

-- Fix C: Optimistic version column + retry
UPDATE post SET likes = likes + 1, version = version + 1
WHERE id = 1 AND version = @expected_version;
-- if 0 rows updated → re-read, retry

-- Fix D: Postgres REPEATABLE READ (snapshot isolation)
-- Second tx's UPDATE will FAIL with "could not serialize access" → retry
```

> **PG specifically:** Postgres **Repeatable Read prevents lost updates** by aborting the second committer with a serialization error. MySQL InnoDB **does not** at RR — you still get the bug unless you use `SELECT ... FOR UPDATE` or `UPDATE ... WHERE value = @old`.

---

##### 🔴 Anomaly 5: Write Skew (the sneakiest — allowed even at Snapshot Isolation)

**The one most engineers get wrong.** Each tx reads a set of rows, checks an invariant, writes a *different* row. Individually valid; together they violate the invariant.

**Classic example: on-call rotation. Rule — at least one doctor must stay on call.**

```sql
CREATE TABLE doctors (id INT, name TEXT, on_call BOOL);
INSERT INTO doctors VALUES (1, 'Alice', true), (2, 'Bob', true);
```

```
Time │ TX1 (Alice wants to leave)              │ TX2 (Bob wants to leave)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN;  -- REPEATABLE READ / SI          │
 t2  │ SELECT COUNT(*) FROM doctors             │
 t3  │   WHERE on_call = true → 2               │
 t4  │ -- "2 doctors on call, I can leave"      │
 t5  │                                          │ BEGIN;  -- REPEATABLE READ / SI
 t6  │                                          │ SELECT COUNT(*) FROM doctors
 t7  │                                          │   WHERE on_call = true → 2
 t8  │                                          │ -- "2 doctors on call, I can leave"
 t9  │ UPDATE doctors SET on_call=false         │
     │   WHERE id=1;  -- Alice leaves           │
 t10 │ COMMIT;                                  │
 t11 │                                          │ UPDATE doctors SET on_call=false
     │                                          │   WHERE id=2;  -- Bob leaves
 t12 │                                          │ COMMIT;
 t13 │ -- RESULT: 0 doctors on call ❌         │
```

**Why Snapshot Isolation doesn't catch it:**
- TX1 and TX2 **wrote different rows** (id=1 and id=2) — no update conflict.
- Each tx's read snapshot said "2 on call" — their decision was valid *in isolation*.
- The invariant (`count(on_call) ≥ 1`) spans multiple rows — SI only checks per-row conflicts.

**Real-world write skews that have caused outages:**

| Scenario | The invariant | The write skew |
|----------|---------------|----------------|
| Doctor on-call | ≥1 on call | Both doctors sign out |
| Bank account overdraft | sum(balances) ≥ 0 | Two withdrawals each OK, total goes negative |
| Meeting room double-book | one booking per time slot | Two users book same room; different rows |
| Username claim | unique username | Two users check "free", both insert |
| Inventory reservation | stock ≥ sum(holds) | Two holds each OK individually, total exceeds stock |
| Flight overselling | seats ≥ sum(bookings) | Two bookings against different seat IDs, invariant on sum |

**Fixes (strongest first):**

```sql
-- Fix A: Serializable isolation (Postgres SSI, Cockroach, Spanner)
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT COUNT(*) FROM doctors WHERE on_call = true;  -- → 2
UPDATE doctors SET on_call = false WHERE id = 1;
COMMIT;  -- Postgres SSI will ABORT one of the two txs → caller retries

-- Fix B: Materialize the conflict (lock the predicate)
--   Introduce a row that both tx must lock.
BEGIN;
SELECT * FROM shifts WHERE id='tonight' FOR UPDATE;  -- single serialization point
SELECT COUNT(*) ...;  -- same check
UPDATE doctors ...;
COMMIT;

-- Fix C: Lock all read rows (promote reads to writes)
BEGIN;
SELECT * FROM doctors WHERE on_call = true FOR UPDATE;  -- lock all on-call rows
-- Now the other tx blocks until this commits
UPDATE doctors SET on_call = false WHERE id = 1;
COMMIT;
```

**Interview trap:** *"My app runs at Repeatable Read, so it's safe, right?"* **Wrong.** RR / SI stops lost updates on *the same row* but **not write skew across rows**. Only **Serializable** (or an explicit lock on the predicate) prevents it.

---

##### 🟡 Anomaly 6: Read Skew (observed inconsistency, between RC and RR)

Two queries in one tx see inconsistent state because of a commit in between.

```
Time │ TX1 (Alice views total)                 │ TX2 (Transfer $100 A→B)
─────┼─────────────────────────────────────────┼──────────────────────────────────
 t1  │ BEGIN; -- READ COMMITTED                 │
 t2  │ SELECT balance FROM accounts WHERE id=A  │
 t3  │   → 500                                  │
 t4  │                                          │ BEGIN;
 t5  │                                          │ UPDATE A SET balance = 400;
 t6  │                                          │ UPDATE B SET balance = 600;
 t7  │                                          │ COMMIT;
 t8  │ SELECT balance FROM accounts WHERE id=B  │
 t9  │   → 600 ❌  (sum A+B = 1000 before,     │
     │             but Alice reads 500+600=1100)│
```

**Fix:** Repeatable Read / Snapshot isolation → both reads at same snapshot → consistent sum.

---

#### Summary — anomalies vs levels (crisp)

| Anomaly | RU | RC | RR (SQL) | RR (Postgres SI) | RR (MySQL InnoDB) | Serializable |
|---------|----|----|----------|------------------|-------------------|--------------|
| Dirty read | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Non-repeatable read | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Phantom read | ❌ | ❌ | ❌ | ✅ (SI) | ✅ (gap locks) | ✅ |
| Lost update | ❌ | ❌ | depends | ✅ (aborts) | ❌ (silent) | ✅ |
| Write skew | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Read skew | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

> **The two surprises most candidates miss:**
> 1. **Postgres's `REPEATABLE READ` is really Snapshot Isolation** — stronger than SQL standard RR. Prevents phantoms + lost updates, but **not** write skew.
> 2. **MySQL InnoDB's `REPEATABLE READ` prevents phantoms via gap locks**, but **does not** prevent lost updates (unlike Postgres). So MySQL at RR + `UPDATE ... WHERE value = @old` or explicit lock is still required for counters.

#### How to fix each — the cheat card

| Anomaly | Minimum fix |
|---------|-------------|
| Dirty read | Use Read Committed or above (default everywhere mainstream) |
| Non-repeatable read | Repeatable Read, or move to atomic single statement |
| Phantom read | Postgres RR (SI) / MySQL RR (gap lock) / Serializable |
| Lost update | `SELECT ... FOR UPDATE`, atomic `UPDATE SET x = x+1`, or optimistic version column + retry |
| Write skew | **Serializable**, or lock the predicate (shift row, inventory row, materialized conflict row) |
| Read skew | Repeatable Read / Snapshot isolation |

#### Interview script (payments + booking)

> "I'd run idempotency insert at **Read Committed** with a unique constraint — simple and fast.
> For a **counter / like / inventory decrement**, I'd use atomic `UPDATE SET x = x + 1`, not read-modify-write, to kill the lost update class entirely.
> For **booking a seat**, I'd use `SELECT ... FOR UPDATE` on the seat row — pessimistic lock, no write skew possible.
> For **cross-row invariants** (on-call rotation, overdraft protection), **Snapshot Isolation is not enough — write skew will bite.** I'd use Postgres **Serializable (SSI)**, or Cockroach/Spanner, which abort offending txs — then the app retries."

---

#### Which real DB defaults to what?

| DB | Default level | What "RR" actually means there |
|----|---------------|-------------------------------|
| **PostgreSQL** | Read Committed | `REPEATABLE READ` = Snapshot Isolation (no phantoms, aborts lost updates) |
| **PostgreSQL (SSI)** | opt-in | True Serializable via SSI (predicate conflict tracking) |
| **MySQL InnoDB** | Repeatable Read | RR + gap locks (no phantoms, but silent lost updates) |
| **Oracle** | Read Committed | `SERIALIZABLE` is actually Snapshot Isolation (write skew possible!) |
| **SQL Server** | Read Committed (locking) | `SNAPSHOT` is SI; `SERIALIZABLE` is 2PL serializable |
| **CockroachDB / Spanner** | **Serializable** | True Serializable always |
| **DynamoDB** | eventual read | `TransactWriteItems` = serializable within tx |
| **MongoDB** | per operation | Multi-doc tx = snapshot; no serializable option |

---

### 2. MVCC — how Postgres & Oracle give you snapshot reads without blocking writers

**Multi-Version Concurrency Control:** every write creates a **new row version** tagged with transaction ID (xmin/xmax). Readers see the version visible to their snapshot.

```
Row:  (id=1, name='A', xmin=100, xmax=NULL)       ← committed at tx 100
After UPDATE at tx 200:
     (id=1, name='A', xmin=100, xmax=200)         ← old version, marked deleted
     (id=1, name='B', xmin=200, xmax=NULL)        ← new version

Reader at tx 150 → sees 'A'  (xmax 200 > 150, old version still visible)
Reader at tx 250 → sees 'B'  (xmax 200 < 250, old version invisible)
```

#### Consequences

- **No read locks** — readers never block writers, writers never block readers.
- **Bloat** — dead row versions accumulate. **Postgres VACUUM** reclaims them.
- **Long-running tx = disaster** — holds back `xmin` horizon, prevents vacuum, bloat explodes. **Never run a 1-hour analytical tx on your OLTP primary.**
- **Index bloat** — every update creates new row → new index entry (unless HOT update, see below).

#### Postgres-specific optimizations to mention

- **HOT update** (Heap-Only Tuple): if no indexed column changed, new version goes on same page, no index update. Enable with lower `FILLFACTOR` (e.g. 70) to leave room.
- **TOAST** (The Oversized Attribute Storage Technique): large values stored out-of-line and compressed.
- **autovacuum** tuning: must keep up with write rate or table bloats.

#### MySQL InnoDB

- Also MVCC via undo log (not row-level copies).
- `REPEATABLE READ` default uses snapshot — but has famous **phantom-via-gap-lock** behavior.

---

### 3. Consensus — Paxos, Raft, 2PC, and why Spanner needs atomic clocks

Every distributed DB that offers strong consistency uses a **consensus protocol**. You should be able to name the right one.

| Protocol | Where used | Property |
|----------|------------|----------|
| **Paxos** (classic) | Google Chubby, Spanner | Theoretically foundational, hard to implement |
| **Multi-Paxos** | Spanner, early distributed systems | Leader-based optimization |
| **Raft** | **etcd, Consul, CockroachDB, TiKV, MongoDB config servers** | Easier to understand, dominant today |
| **ZAB** | ZooKeeper | Pre-Raft, similar guarantees |
| **2PC (Two-Phase Commit)** | Distributed SQL cross-shard | Blocking on coordinator failure |
| **3PC** | Rare | Non-blocking but needs synchronous network |
| **Saga** | Microservices | Not consensus — long-lived business tx with compensations |

#### Raft in 60 seconds (interview answer)

1. **Leader election:** nodes vote; majority wins; one leader at a time.
2. **Log replication:** leader appends to its log, replicates to followers.
3. **Commit:** entry committed when **majority** acknowledge. Then applied to state machine.
4. **Safety:** term numbers prevent split-brain; leader must have all committed entries.

**Say this:** "etcd uses Raft. A write isn't acknowledged until majority replicated. That's why cross-region etcd is slow — RTT × majority."

#### 2PC vs Saga — critical for microservices

| | 2PC | Saga |
|---|-----|------|
| Guarantees | Atomic across services | Eventual, with compensations |
| Blocking | Coordinator failure blocks everyone | Non-blocking, forward progress |
| Modern use | Rare in microservices | Standard pattern |
| Example | Spanner cross-shard tx | Order → payment → shipping, compensate on failure |
| Interview flag | "2PC in microservices" = red flag | "Saga + outbox" = senior answer |

#### Saga patterns

- **Orchestration:** central coordinator issues commands, handles failures. Easier to debug.
- **Choreography:** services react to events, publish next events. Decoupled, hard to trace.

---

### 4. Clock Problems — Lamport, Vector, HLC, TrueTime

Distributed systems can't trust wall clocks. This underlies **every ordering guarantee**.

| Clock | Property | Used by |
|-------|----------|---------|
| **Lamport timestamp** | Logical counter; `a → b` implies `L(a) < L(b)`; no concurrency detection | Theoretical foundation |
| **Vector clock** | Per-node counter; detects concurrent updates | Dynamo, Riak, CRDTs |
| **Hybrid Logical Clock (HLC)** | Lamport + physical time; close to real time | CockroachDB, YugabyteDB |
| **TrueTime** | GPS + atomic clock bounded uncertainty `[earliest, latest]` | **Google Spanner only** |

#### Why this matters in interviews

- **Last-write-wins (LWW) based on wall clock** = silent data loss when clocks skew. Cassandra's LWW is why bulk-loading with wrong NTP corrupts data.
- **TrueTime lets Spanner give external consistency without 2PC overhead** — commit waits out the clock uncertainty window (~7ms).
- **Vector clocks** are how Dynamo-style systems detect concurrent writes to the shopping cart and merge them.

#### CRDTs — Conflict-free Replicated Data Types

Data structures that **merge automatically** without coordination. Used in Redis Enterprise (CRDB), Riak, Yjs, Automerge, collaborative editors.

| CRDT | Example | Use |
|------|---------|-----|
| **G-Counter** | Grow-only counter | Page views, likes (increments only) |
| **PN-Counter** | Increment + decrement | Shopping cart item count |
| **G-Set** | Grow-only set | Followers |
| **OR-Set** | Add + remove set | Chat participants |
| **LWW-Register** | Last-write-wins value | User preference |
| **RGA / Yjs** | Collaborative text | Google Docs, Figma |

**Say:** "For a collaborative editor, I'd use CRDTs instead of Operational Transform — simpler conflict model, works offline."

---

### 5. LSM Internals — compaction, amplification, bloom filters

The B-Tree vs LSM comparison is table stakes. These are the senior nuances:

#### Three amplifications (always comes up)

| Metric | Definition | B-Tree | LSM |
|--------|------------|--------|-----|
| **Write amplification** | Physical writes / logical writes | ~2× (data + WAL) | **10–30×** (memtable → L0 → L1 → ... via compaction) |
| **Read amplification** | Pages read / logical rows | ~1 (seek) | **~N** (may check all levels) |
| **Space amplification** | Disk used / logical data | ~1.3× (bloat) | **1.1–2×** depending on compaction |

#### Compaction strategies (Cassandra, RocksDB)

| Strategy | When | Tradeoff |
|----------|------|----------|
| **Size-tiered (STCS)** | Default Cassandra | Low write amp, high space amp, large temporary disk use |
| **Leveled (LCS)** | Read-heavy workloads | Low read & space amp, 10–20× write amp |
| **Time-window (TWCS)** | Time-series data | Compacts only within time window, perfect for TTL expiry |

**Interview answer:** "For IoT with TTL, use **TWCS** — expired SSTables drop whole, no tombstone problem."

#### Bloom filter

Probabilistic data structure: "key definitely not in this file" or "maybe in this file." Avoids disk read for miss.

- False positive rate ~1% at 10 bits/key.
- **Why it matters:** LSM point reads would be O(levels) disk I/O without bloom filters. With them, usually 1 I/O.
- Postgres also has **Bloom index** extension for multi-column equality lookups.

#### Tombstones — the Cassandra tar pit

Delete in LSM = **write a tombstone marker**. Actual delete happens at compaction.

- Problem: many tombstones in one partition → read scans them all → latency explodes.
- **`gc_grace_seconds`** (default 10 days) — tombstones kept this long to prevent zombie data.
- **Rule:** **never model Cassandra tables where you delete > 1000 rows per partition.** Use TTL on inserts instead.

---

### 6. Query Optimizer — EXPLAIN plans you must understand

Interviewers love "your query is slow — why?"

#### Join algorithms

| Algorithm | When optimizer picks | Cost |
|-----------|---------------------|------|
| **Nested loop** | Small outer, indexed inner | O(N × log M) |
| **Hash join** | No index, equi-join, enough RAM | O(N + M) — build hash on smaller side |
| **Merge join** | Both sides sorted on join key | O(N + M) after sort |
| **Index-only scan** | All required columns in index | Fastest — no heap fetch |

#### Postgres statistics

- `ANALYZE` collects **histograms** (`pg_statistic`). Optimizer uses to estimate rows.
- **Stale stats** → bad plan → full table scan → outage. Autovacuum runs ANALYZE; verify it keeps up.
- `EXPLAIN (ANALYZE, BUFFERS)` — compare **estimated vs actual rows**. 100× off = stats problem.

#### Common slow-query causes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Seq scan on big table | Missing index, or index not selective | Add index; check row estimate |
| Nested loop over 1M rows | Optimizer thought outer was small | ANALYZE; raise `default_statistics_target` |
| Sort to disk | `work_mem` too small | Raise `work_mem` per-session |
| High `shared_hit` vs `read` | Working set > buffer cache | More RAM or partition |
| Lock wait | Long tx holding row | Kill the tx; shorten txs |

---

### 7. Indexes Deep Dive (beyond "add an index")

| Index type | Postgres syntax | Use for |
|------------|-----------------|---------|
| **B-Tree** | default | Equality + range on scalar |
| **Hash** | `USING HASH` | Equality only; rarely better than B-tree |
| **GIN** | `USING GIN` | JSONB, arrays, full-text (`tsvector`) |
| **GiST** | `USING GIST` | Geometry (PostGIS), range types, trigram fuzzy |
| **BRIN** | `USING BRIN` | Huge sequential tables (append-only logs) — tiny index |
| **Partial** | `WHERE active = true` | Index only hot subset |
| **Expression** | `ON (lower(email))` | Case-insensitive lookup |
| **Covering** | `INCLUDE (col)` | Index-only scan, avoid heap fetch |
| **Multi-column** | `(a, b, c)` | Only useful left-to-right (`a`, `a,b`, `a,b,c`) |

#### The "which column first" rule

For `WHERE tenant_id = ? AND created_at > ?`:
- `(tenant_id, created_at)` → good: equality then range.
- `(created_at, tenant_id)` → bad: range first destroys selectivity for tenant.

#### When indexes hurt

- Every index = extra write + bloat.
- Rule: **start with no indexes beyond PK**, add based on `pg_stat_user_tables` + slow query log.
- Over-indexed table = write amplification + bloat + planner confusion.

---

### 8. Change Data Capture (CDC) & the Outbox Pattern

How mature systems **reliably propagate** DB changes to search, cache, analytics, other services.

#### CDC

```
Postgres WAL → Debezium → Kafka → consumers (ES, ClickHouse, cache invalidate)
MySQL binlog → Debezium → Kafka → ...
MongoDB oplog → change streams → ...
```

- **Benefit:** downstream systems get every change, in order, exactly once (per topic).
- **No dual-writes** from app code → no "wrote to DB but not Kafka" bugs.

#### Outbox pattern (critical for microservices)

Problem: service must update DB **and** publish event. If you do both separately, failure between them = inconsistency.

Solution:

```sql
BEGIN;
  INSERT INTO orders (...);
  INSERT INTO outbox (event_type, payload) VALUES ('OrderCreated', ...);
COMMIT;
-- Debezium reads outbox table, publishes to Kafka, deletes row.
```

- One tx → both state and event committed atomically.
- Outbox relay is **idempotent**.
- **Interview phrase:** "outbox + CDC = reliable event publishing without 2PC."

---

### 9. Partitioning Strategies (beyond "shard by user_id")

| Strategy | How | Good for | Bad for |
|----------|-----|----------|---------|
| **Range** | `[0–100] [100–200]` | Range scans | Hot partition on recent IDs |
| **Hash** | `hash(key) % N` | Even distribution | Range scans impossible |
| **List** | By value: `region = 'EU'` | Multi-tenancy | Skewed tenants |
| **Composite** | `hash(tenant_id)` + range on time | Multi-tenant time series | Complex query planning |
| **Consistent hashing** | Hash ring with virtual nodes | Minimizing data movement on resize | More complex client |
| **Geo-partition** | By user's region | Low latency, GDPR | Cross-region queries slow |

#### Hot partition — the deepest fix

When one key gets 1000× traffic:

1. **Pre-aggregate** on client side (counters, buckets).
2. **Key splitting:** `product:X:shard:0..N`, writes random shard, reads sum all shards. (Twitter does this for celebrity timelines.)
3. **Dedicated hot cache** per hot key in local app memory.
4. **DynamoDB adaptive capacity** — automatic for them, but costs you.
5. **Request coalescing** at the app layer — single flight pattern.

---

### 10. Cache Stampede / Thundering Herd — three real solutions

Cache expires → 10,000 concurrent requests all miss → all hit DB → DB dies.

| Pattern | How | When |
|---------|-----|------|
| **Mutex / single-flight** | First miss acquires lock, rebuilds; others wait | Default, works everywhere |
| **Probabilistic early expiration** | Each request has small chance of refreshing before TTL ends | High-QPS steady state |
| **Request coalescing** | App layer merges concurrent misses for same key | Downstream app code |
| **Stale-while-revalidate** | Serve stale, refresh in background | Non-critical freshness |
| **Pre-warming** | Scheduled job refreshes hot keys | Flash sale, known hot content |

**Alibaba Double 11 uses all five** at different layers.

---

### 11. Backup, DR, RPO, RTO — know the terms

| Term | Means |
|------|-------|
| **RPO** (Recovery Point Objective) | How much data can you afford to lose? (last backup → crash) |
| **RTO** (Recovery Time Objective) | How long to restore service? |
| **PITR** (Point-In-Time Recovery) | Restore to any second via WAL replay |

| Strategy | RPO | RTO | Cost |
|----------|-----|-----|------|
| Nightly dump | 24 hours | hours | $ |
| Streaming replica | seconds | minutes | $$ |
| Sync replica (multi-AZ) | 0 | seconds | $$$ |
| Multi-region sync | 0 | seconds | $$$$ |

**Say:** "For payments, RPO=0 required → sync replica. For analytics, RPO=1 day fine → S3 nightly."

---

### 12. Multi-Tenancy — three strategies

| Model | Isolation | Cost | Noisy neighbor |
|-------|-----------|------|----------------|
| **Shared schema, tenant_id column** | Weak | Lowest | High |
| **Schema per tenant** | Medium (Postgres schemas) | Medium | Medium |
| **Database per tenant** | Strong | High | None |

**Rule of thumb:**
- Startup → shared schema + `tenant_id` on every table and every index.
- Enterprise SaaS → DB per tenant for compliance.
- Hybrid → shared for free tier, isolated for enterprise.

---

### 13. Message Queue Comparison (always comes up with Kafka)

| | Kafka | RabbitMQ | AWS SQS | Pulsar | NATS |
|---|-------|----------|---------|--------|------|
| Model | Log, consumer pull | Broker, push | Queue, pull | Log + queue | Pub/sub |
| Ordering | Per partition | Per queue | FIFO queues only | Per partition | None by default |
| Replay | ✓ (retention) | ✗ | ✗ | ✓ | ✗ |
| Throughput | Millions/sec | ~50K/sec | High (managed) | Millions/sec | Millions/sec |
| Delivery | At-least-once (exactly-once with care) | At-least-once | At-least-once | Both | At-most / at-least |
| Best for | Event streaming, log, big data | Classic work queue, routing | AWS-native simple queue | Multi-tenant streaming | Low-latency pub/sub |
| Downside | Ops complexity | Scale ceiling | AWS lock-in | Still maturing | No persistence by default |

**Say:** "Kafka when I need replay, high throughput, or multiple independent consumers. RabbitMQ when I need per-message routing and work queues. SQS for simple AWS-native fan-out."

---

### 14. Latency Numbers Every Engineer Should Memorize

(Updated Jeff Dean numbers — know these for back-of-envelope.)

| Operation | Time |
|-----------|------|
| L1 cache reference | 0.5 ns |
| L2 cache reference | 7 ns |
| Mutex lock/unlock | 25 ns |
| Main memory reference | 100 ns |
| Compress 1 KB with zippy | 2 µs |
| Send 2 KB over 1 Gbps network | 20 µs |
| **Redis GET (local)** | **~100 µs** |
| **Postgres indexed lookup (hot cache)** | **~500 µs – 1 ms** |
| SSD random read (4 KB) | 150 µs |
| Round trip in same datacenter | 500 µs |
| **Postgres row insert (committed)** | **~1–3 ms** |
| **DynamoDB P50** | **~5–10 ms** |
| Disk seek (HDD) | 10 ms |
| Round trip CA → Netherlands | 150 ms |
| **Full table scan 1M rows** | **~1 s** |

**Use in interviews:** "100K QPS × 1ms Postgres read = 100 CPU-seconds/sec = ~100 cores. Need read replicas or cache."

---

### 15. Capacity Numbers — rough DB benchmarks

Memorize these ranges. Interviewers accept rough numbers; vagueness looks weak.

| DB | Reads/sec (single node, hot) | Writes/sec | Data per node |
|----|------------------------------|------------|---------------|
| **PostgreSQL** | 50K–100K | 5K–20K | 1–5 TB comfortable |
| **MySQL InnoDB** | 50K–100K | 10K–30K | 1–5 TB |
| **Redis** | 100K–1M (single thread) | 100K–500K | RAM-bound (hundreds GB) |
| **Cassandra** | 10K–50K per node | 50K–100K | 1–3 TB per node (density matters) |
| **MongoDB** | 20K–50K | 10K–30K | 1–3 TB |
| **DynamoDB** | Unlimited (partition-limited) | Partition: 1000 writes/sec | Unlimited |
| **Elasticsearch** | ~5K–20K search QPS/shard | ~10K indexing/shard | 20–50 GB per shard ideal |
| **ClickHouse** | Billions rows scanned/sec | Batch inserts preferred | 100 TB+ comfortable |
| **Kafka** | 1M+ msg/sec per broker | Same | Terabytes retention |

**Rule:** Single-node Postgres handles most startups to **~1M users**. After that, add replicas, cache, and shard.

---

### 16. Database-Specific Pitfalls (quote these = instant credibility)

#### PostgreSQL

- **Autovacuum tuning:** default `autovacuum_vacuum_scale_factor=0.2` means vacuum runs when 20% dead — way too late for high-churn tables. Set to 0.05 for hot tables.
- **TXID wraparound:** Postgres has 4-byte xids. If not vacuumed in time → emergency shutdown. Monitor `pg_stat_database.datfrozenxid`.
- **Replication slot bloat:** inactive replication slot pins WAL → disk fills → outage. Monitor `pg_replication_slots.active`.
- **TOAST compression** of large text columns — can accidentally dominate storage.
- **Connection limit:** ~500 effective max. Use **PgBouncer** in transaction mode.

#### MySQL

- **Gap locks** in RR isolation cause deadlocks nobody expects. Switch to Read Committed if deadlocks hurt.
- **InnoDB clustered index:** PK order = disk order. UUID v4 PK = write amplification. Use UUID v7 or auto-increment.
- **Online DDL** has caveats (`ALGORITHM=INPLACE` + `LOCK=NONE`). Use **pt-online-schema-change** or **gh-ost** for safe production migrations.

#### Cassandra

- **Tombstone-threatened reads:** 1000 tombstones per partition → warning; 100,000 → fail. Model to append, never delete.
- **Large partitions:** >100 MB per partition = GC pressure, repair failures. Bucket by month if needed.
- **Secondary indexes are not real indexes** — they are per-node. Avoid; use denormalized table instead.
- **LWT (Lightweight Transactions, Paxos):** 4× slower than normal write. Use only when truly needed.
- **Repair required** periodically or data diverges. `nodetool repair` is operational homework.

#### MongoDB

- **16 MB document limit** — bite you when embedding grows.
- **Oplog window:** replica set must catch up within oplog retention. Big writes burn window fast.
- **$lookup joins** are slow. Denormalize or move to relational for that part.
- **Index intersection** is weak — use compound indexes, not multiple singles.

#### Redis

- **Single thread** = one slow command (`KEYS *`, large `HGETALL`) blocks everyone. Use `SCAN`.
- **`EXPIRE` on hot keys** → thundering herd on expiry. Add random jitter.
- **No cluster-wide transactions** across slots. Hash-tag keys with `{}` for colocation.
- **`maxmemory` + eviction policy** — set to `allkeys-lru` or `volatile-lru`, never let it crash with OOM.

#### DynamoDB

- **Hot partition:** 3,000 RCU / 1,000 WCU per partition cap. Design partition key for distribution.
- **Scan is poison** — pay for every byte read. Always use Query or GSI.
- **Item size:** 400 KB max. Store blobs in S3, pointer in DynamoDB.
- **Eventually consistent reads are default** — set `ConsistentRead=true` where it matters, costs 2× RCU.

---

### 17. Idempotency & Dedup at Scale

| Pattern | How | Use |
|---------|-----|-----|
| **Idempotency key** | Client sends UUID; server stores response | HTTP APIs, payments |
| **Unique constraint** | `UNIQUE (order_id, item_id)` | DB-enforced dedup |
| **Deterministic ID** | `hash(user_id + action + minute)` | Natural dedup |
| **Dedup window in stream** | Kafka Streams, Flink state TTL | Event processing |
| **Bloom filter dedup** | Membership "probably seen" | Low-memory, 1% false positive OK |
| **Exactly-once semantics (Kafka)** | Idempotent producer + transactional writes | Within Kafka ecosystem |

**Interview wisdom:** "Exactly-once is a myth across systems. **At-least-once + idempotent consumer** is how you actually get effectively-once."

---

### 18. The Dynamo Quorum Math (interviewer favorite)

- **N** = replicas, **W** = write ack count, **R** = read quorum.
- **Strong consistency** when `W + R > N`.
- Common: N=3, W=2, R=2 → tolerates 1 node failure with consistency.
- `W=1` = fast write, stale reads possible.
- `R=1` = fast read, may miss recent writes.
- `W=N` = slow write, fast read.

**Say:** "For Cassandra user profiles, I'd pick N=3, W=QUORUM(2), R=QUORUM(2) in each DC. Local quorum keeps latency low while surviving one node loss."

---

### 19. ACID vs BASE — the senior nuance

- **ACID is not binary.** Postgres default = Read Committed (not Serializable). Most "ACID" code has write skew bugs waiting to happen.
- **BASE systems can be made strongly consistent** with quorum, LWT, or client-side locks — but you pay for it.
- Real system: **mix per table**. Payments table serializable; feed table eventual.

---

### 20. When Interviewer Asks "Why Not X?"

Expect counter-questions. Have the real reason ready.

| Question | Strong answer |
|----------|---------------|
| "Why not just MongoDB?" | Weak joins, document lock on hot aggregates, write skew without serializable |
| "Why not Cassandra for everything?" | No cross-partition tx, tombstone problem, denormalization explosion |
| "Why not DynamoDB?" | Hot partition throttling, scan cost, vendor lock-in |
| "Why not just one Postgres?" | Vertical scale ceiling ~50K writes/sec; multi-region hurts |
| "Why Redis if we have Postgres cache?" | Latency floor and atomic ops (`INCR`, `ZADD`) not possible in SQL cheaply |
| "Why Kafka if we have RabbitMQ?" | Replay, multiple independent consumers, log retention |
| "Why not blockchain for audit?" | Overhead for single-org, Kafka + hash-chain gives same without consensus |

---

### 21. Signature Features Per DB — the vocabulary interviewers expect

Every DB has 10-20 **signature concepts** that only exist (or only matter) in that system. Naming them unprompted is how you prove depth.

---

#### Cassandra signature features

| Mechanism | What it does | Interview phrase |
|-----------|--------------|------------------|
| **Gossip protocol** | Nodes exchange cluster state every second | "Peer-to-peer, no master" |
| **Snitch** (SimpleSnitch, GossipingPropertyFileSnitch, Ec2Snitch) | Tells C* which node is in which rack/DC | "DC-aware routing + rack-aware replica placement" |
| **Virtual nodes (vnodes)** | 256 tokens/node by default | "Smaller resharding blast radius than physical tokens" |
| **Hinted handoff** | Coordinator stores writes for down nodes, replays when back | "Low RF availability without read repair" |
| **Read repair** | During read, compare replicas; fix stale ones (sync at CL level, or async background) | "Blocking vs non-blocking read repair chance" |
| **Anti-entropy repair** (`nodetool repair`) | Merkle tree comparison across replicas; must run within `gc_grace_seconds` | "Operational homework — skip it and tombstones return as zombies" |
| **Consistency levels** | `ONE`, `QUORUM`, `LOCAL_QUORUM`, `EACH_QUORUM`, `ALL`, `ANY` per query | "`LOCAL_QUORUM` for most apps — local-DC strong, cross-DC async" |
| **Materialized views** | DB-maintained denormalized table | "Experimental in 3.x, use CDC + app-level view instead for prod" |
| **Secondary indexes** (2i, SASI, SAI) | Per-node index, scatter-gather read | "SAI in C* 5.0 fixes most of 2i's problems; avoid 2i otherwise" |
| **Counter columns** | Special PN-counter type for increments | "Not idempotent — retries double-count. Use regular column + CAS instead when exactness matters" |
| **Batch (LOGGED vs UNLOGGED)** | LOGGED = atomic across partitions via batchlog; UNLOGGED = perf hack for same partition | "LOGGED batch = 30% slower; use only when truly atomic across partitions" |
| **Lightweight Transactions (LWT / Paxos)** | `INSERT ... IF NOT EXISTS` | 4 round-trips, 4× slower; use sparingly |
| **Prepared statements + token-aware driver** | Client sends query directly to replica owning the token | "Skips coordinator hop" |
| **ALLOW FILTERING** | Bypass partition-key rule | "Red flag in production — always full-cluster scan" |
| **Collections** (list, set, map, UDT, frozen) | Nested types inside a cell | "Frozen = read as blob (fast); unfrozen = per-element update (expensive)" |
| **Compaction strategies** | STCS, LCS, TWCS, UCS (5.0) | Discussed in §5; pick by workload |
| **TTL per column** | `USING TTL 3600` on insert | Great for ephemeral data; expiry creates tombstones |
| **Row cache + key cache** | Row cache = full row in RAM; key cache = partition offset in SSTable | "Row cache rarely helps real workloads; key cache always on" |
| **Speculative retry** | Query same read on second replica if first slow | Smooths p99 |

**"Prove you know Cassandra" question:** *"Why can't you query without the partition key?"*
> "Because data placement is `hash(partition_key) → token → node`. Without it, the coordinator doesn't know which node has the row, so it has to scatter-gather all nodes. CQL blocks this with the partition-key rule unless you add `ALLOW FILTERING`."

---

#### Time-Series DB signature features

| Mechanism | What it does | Example / phrase |
|-----------|--------------|------------------|
| **Hypertable** (TimescaleDB) | Auto-chunked table by time (and optionally space) | `SELECT create_hypertable('metrics', 'time', chunk_time_interval => '1 day')` |
| **Chunk exclusion / pruning** | Query planner skips chunks outside time range | Scans 1 day of chunks for 1-day query, not full table |
| **Continuous aggregates** (TimescaleDB) | Incrementally maintained materialized view of rollups | `CREATE MATERIALIZED VIEW metrics_1h WITH (timescaledb.continuous) AS ...` |
| **Compression policy** | TimescaleDB columnar compression on old chunks | **10-100× smaller**; trade query latency on compressed chunks |
| **Retention policy** | Auto-drop chunks older than N days | `add_retention_policy('metrics', INTERVAL '30 days')` |
| **Downsampling / rollups** | 1s raw → 1m avg → 1h avg → 1d avg | Hot/warm/cold tiers with different resolution |
| **Recording rules** (Prometheus) | Pre-compute expensive queries on schedule, store as new series | `instance:node_cpu:avg_rate1m` |
| **Alerting rules** (Prometheus) | PromQL expressions → Alertmanager | Separates "what to alert on" from "how to notify" |
| **Push vs Pull** | InfluxDB = push (client sends); Prometheus = pull (server scrapes) | "Pull is better for health checks; push for serverless where you can't scrape" |
| **Remote write / long-term storage** | Prometheus → Thanos / Cortex / Mimir / VictoriaMetrics for multi-year retention | Local Prometheus = 15 days; remote = years |
| **High-cardinality explosion** | Tags with unique values (user_id, request_id) blow up series count | **Never put request_id or UUID as a label** |
| **Gorilla / delta-of-delta compression** | Facebook paper; timestamps + float values pack to ~1.37 bytes each | Why TSDBs are 10-100× smaller than Postgres |
| **Last-point / last-value query** | "Latest reading per device" | TSDBs optimize this; naive SQL does `DISTINCT ON ... ORDER BY time DESC` |
| **Shard key = (metric, time range)** | Writes always to current time chunk → no cross-shard writes | Flip side: current chunk is write-hot |
| **PromQL / Flux / InfluxQL** | Domain-specific query languages (vector math, rate, histogram_quantile) | `histogram_quantile(0.99, rate(http_duration_bucket[5m]))` |

**Rollup strategy (interview answer):**
> "I keep **raw at 10s resolution for 7 days**, **1-minute rollups for 90 days**, **1-hour rollups for 2 years**. Continuous aggregates or Prometheus recording rules compute them incrementally. Grafana queries the right resolution automatically based on the dashboard time range."

---

#### PostgreSQL signature features

| Feature | What it does | Interview phrase |
|---------|--------------|------------------|
| **MVCC + xmin/xmax** | Snapshot isolation without read locks | Covered in §2 |
| **WAL (Write-Ahead Log)** | Durability + replication + PITR | "Streaming or logical replication both read WAL" |
| **Streaming replication** | Physical WAL ship to replica | Byte-identical replica; no selective tables |
| **Logical replication / `pg_logical`** | Decode WAL to per-table changes; publish/subscribe | Selective replication, cross-version — basis for Debezium CDC |
| **Logical decoding** | WAL → row-level change events | How CDC works |
| **Declarative partitioning** | `PARTITION BY RANGE (created_at)` | Native since v10; use with pg_partman for automation |
| **Foreign Data Wrappers (FDW)** | Query external data as if local tables | `postgres_fdw`, `mongo_fdw`, `file_fdw` |
| **JSONB** | Binary JSON with GIN indexing | `WHERE data @> '{"status":"paid"}'` — indexed path lookup |
| **GIN / GiST indexes** | GIN for arrays/JSON/text search; GiST for geo/range | PostGIS, pg_trgm fuzzy search |
| **Full-text search** (`tsvector`, `tsquery`) | Built-in inverted index | Good up to millions of docs; past that use Elasticsearch |
| **Advisory locks** (`pg_advisory_lock`) | Named locks outside the row model | Distributed cron coordination; be careful about leaks |
| **LISTEN / NOTIFY** | Lightweight pub/sub inside Postgres | Small payloads, no persistence — use for cache invalidation |
| **Common Table Expressions (CTE)** | `WITH ... AS` subqueries | Readable; **not** optimization barriers since PG 12 |
| **Materialized views** | Snapshot of query result | Manual `REFRESH`, or incremental via extension |
| **Row-Level Security (RLS)** | Per-row ACL via `CREATE POLICY` | Multi-tenant with `tenant_id` + policy automatically filters |
| **Extensions** | PostGIS, pgvector, pg_cron, pg_stat_statements, TimescaleDB, Citus | Postgres is the "swiss army knife" of DBs |
| **HOT updates** | New row version on same page, no index update | Needs lower FILLFACTOR + no indexed col change |
| **TOAST** | Oversized attribute storage (compressed, out-of-line) | Automatic for columns > 2 KB |
| **VACUUM / autovacuum** | Reclaim dead tuples, update visibility map, prevent xid wraparound | **Monitor autovacuum lag** |
| **pg_stat_statements** | Per-query performance stats | First tool to enable on any Postgres install |
| **Prepared statements + plan caching** | Avoid re-planning | Watch for custom-vs-generic plan flip at 5 executions |
| **Partial / expression / covering indexes** | `WHERE active`, `ON (lower(email))`, `INCLUDE (col)` | Shrink index size + enable index-only scans |

**"Prove you know Postgres" question:** *"Your write throughput dropped suddenly."*
> "First check autovacuum lag — `pg_stat_user_tables`. Dead tuples bloating hot tables → sequential scans. Next check replication slots — abandoned slot pins WAL. Then `pg_stat_statements` for a slow query hogging shared buffers."

---

#### MongoDB signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Replica set** | Primary + secondaries, auto-failover via election | "Writes only to primary; reads tunable via read preference" |
| **Sharded cluster** | mongos router + config servers + shard replica sets | "Shard key choice is permanent — plan carefully" |
| **Change streams** | Watch collection for inserts/updates/deletes | Built on oplog; basis for real-time sync |
| **Oplog** | Capped collection of write ops on primary | **Oplog window** = how far behind a secondary can be |
| **Aggregation pipeline** | `$match → $group → $lookup → $facet` chainable stages | MongoDB's SQL replacement |
| **$lookup** | Left outer join (weak) | Avoid at hot path; denormalize or move to SQL |
| **Index types** | single, compound, multikey (arrays), text, 2dsphere, hashed, wildcard, **TTL**, **sparse**, **partial** | TTL index = auto-delete; sparse = only index docs with field |
| **Capped collection** | Fixed-size circular buffer | Log pattern inside Mongo |
| **GridFS** | Chunked file storage over Mongo | Rarely the right answer vs S3 |
| **Write concern** (`w: majority, j: true`) | Durability knob per write | `w:1` fast / `w:majority` safe |
| **Read preference** | `primary, primaryPreferred, secondary, secondaryPreferred, nearest` | Reads from secondary = stale |
| **Causal consistency sessions** | Monotonic reads across operations | Required when writing then reading from secondary |
| **Multi-document ACID transactions** (v4.0+) | `withTransaction` block | Cost: ~5-10× latency; keep tx short |
| **Chunk balancer** | Moves chunks between shards for even distribution | Can be disabled during peak load |
| **Hashed shard key** | Random distribution, no range scans | Trade off scans for even write |
| **MongoDB Atlas Search** | Lucene-powered inside Mongo | Replaces separate Elasticsearch for simple cases |

---

#### Redis signature features (far beyond "cache")

| Feature | What it does | Pattern |
|---------|--------------|---------|
| **Data structures** | String, Hash, List, Set, Sorted Set, Stream, Bitmap, HyperLogLog, GEO | Each matches a problem shape |
| **Sorted Set (ZSET)** | Score-ordered set with O(log N) rank | **Leaderboard, rate-limit sliding window, delayed queue** |
| **Streams (XADD/XREAD/XREADGROUP)** | Append-only log with consumer groups | Kafka-lite inside Redis; at-least-once delivery |
| **Pub/Sub** | Fire-and-forget channels | No persistence; use Streams for durable |
| **Lua scripting (EVAL)** | Atomic multi-key logic | Flash-sale inventory deduct |
| **Pipelining** | Batch commands over one connection | 10-100× throughput vs round-trip per command |
| **Transactions (MULTI/EXEC/WATCH)** | Optimistic concurrency; WATCH aborts if key changed | Not isolated — commands queue, then run |
| **Redis Cluster** | 16384 hash slots across nodes; `{tag}` for key colocation | Transactions and multi-key only within one slot |
| **Hash tags** `user:{123}:profile` | Force keys to same slot | Required for multi-key atomic ops in cluster |
| **TTL / EXPIRE** | Auto-expire; passive + active expiration | Session store, hold tokens, caches |
| **Keyspace notifications** | Pub/sub events on key operations (`__keyevent@0__:expired`) | React to TTL expiry (e.g. "hold expired → release seat") |
| **Eviction policies** | `noeviction, allkeys-lru, allkeys-lfu, volatile-lru, volatile-ttl, allkeys-random` | **Always set `maxmemory` + policy** — never let OOM-kill |
| **AOF + RDB persistence** | Hybrid: periodic snapshot + append-only log | AOF `everysec` is the practical durability sweet spot |
| **Replication** (`replicaof`) | Async primary → replicas | `WAIT N timeout` for sync-ish writes |
| **Redis Sentinel** | HA monitoring + automatic failover | Legacy; Cluster is more common now |
| **Modules** | **RedisJSON**, **RediSearch** (secondary index + full-text + vector), **RedisTimeSeries**, **RedisBloom**, **RedisGraph** | Turns Redis into multi-model |
| **RedisSearch** | Secondary indexing + full-text + vector in Redis | "Elasticsearch-lite" if latency matters more than analytics |
| **Lazy freeing** (`UNLINK`) | Delete big keys without blocking | `DEL` on 1GB key = multi-second block |
| **Scripting EVALSHA** | Cache Lua script by SHA | Avoid re-sending full script |
| **Cluster-safe libraries** | Driver reads MOVED/ASK redirects | Jedis cluster-aware, lettuce reactive |

**"Prove you know Redis" question:** *"You have a seat-hold TTL that must trigger inventory release. How?"*
> "Enable **keyspace notifications** for expired events (`notify-keyspace-events Ex`), subscribe to `__keyevent@0__:expired`, when `seat:{show}:{id}` expires publish release to app. Not delivery-guaranteed, so also run a periodic sweeper as backup."

---

#### DynamoDB signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Partition key + Sort key** | PK alone (hash) or PK+SK (range) | Composite = multiple access patterns on one table |
| **GSI (Global Secondary Index)** | Alternate PK/SK, async replicated | Add anytime; eventual consistency; separate throughput |
| **LSI (Local Secondary Index)** | Alt sort key, same PK, strong consistent | Max 5; must declare at table creation |
| **Single-table design** | All entities in one table with discriminator SK | AWS-recommended; harder to understand but cheaper |
| **Conditional writes** | `attribute_not_exists`, `=`, `<`, etc. | Optimistic concurrency, idempotency |
| **Transactions** (`TransactWriteItems`) | ACID across up to 100 items | 2× cost; latency ~2× |
| **TTL** | Delete items after timestamp | Lazy — up to 48h delay before actual removal |
| **DynamoDB Streams** | Change feed consumable by Lambda / Kinesis | 24h retention; basis for CDC |
| **Global Tables** | Multi-region active-active with LWW | Eventual consistency across regions |
| **Adaptive capacity** | Auto-shifts throughput to hot partition | Not a substitute for good PK design |
| **On-demand vs Provisioned** | Pay-per-request vs reserved RCU/WCU | On-demand = 7× more expensive at sustained load |
| **DAX (DynamoDB Accelerator)** | In-memory cache cluster for Dynamo | Sub-ms reads; eventual (write-through optional) |
| **PITR (point-in-time recovery)** | Restore to any second in last 35 days | Enable always |
| **PartiQL** | SQL-ish syntax on Dynamo | Avoid for perf — hides scan cost |
| **Export to S3** | Dump to Parquet for Athena/Glue | OLAP without touching production |
| **Burst capacity** | 5 min of 2× capacity accumulated during idle | Soaks small spikes for free |

---

#### Elasticsearch signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Shards + replicas** | Primary shard count fixed at index creation | Reshard = reindex |
| **Analyzers** (standard, keyword, edge_ngram, synonym, language-specific) | Text → tokens | "Keyword is exact match; text is analyzed — choose at mapping time" |
| **Mapping — text vs keyword** | `text` analyzed for search; `keyword` for exact/aggregate | **Multi-field** = both at once |
| **Inverted index** | token → doc list | Why `LIKE '%foo%'` on SQL dies and ES wins |
| **BM25 scoring** | Replaces TF-IDF (default since v5) | Tune `k1`, `b` for length normalization |
| **Function score / script score** | Blend relevance + business signals | Boost by recency, popularity, price |
| **Aggregations** | Metric (sum, avg, p99), bucket (terms, histogram, date_histogram), pipeline (derivative, cumulative) | Analytics UI backend |
| **Index Lifecycle Management (ILM)** | Hot → warm → cold → frozen → delete | Shrinks index, moves to cheaper nodes, deletes |
| **Rollover** | Switch write alias when index size/age/doc count hit | Time-series pattern in ES |
| **Snapshot / restore** | To S3 / GCS | Backup via `_snapshot` API |
| **Reindex API** | Copy index → new index with new mapping | Mapping changes require reindex (brutal) |
| **Suggesters** | Completion, phrase, term | Autocomplete |
| **Cross-cluster search / replication** | Query / replicate across clusters | Multi-region |
| **Routing** | `_routing=user_id` → put related docs on same shard | Faster aggregations within a user |
| **Hot threads API** | `_nodes/hot_threads` | First diagnostic for perf issues |
| **Painless scripting** | Safe scripting for aggregations | Avoid at hot path — compiles per node |

---

#### Kafka signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Topic + partition** | Partition = unit of parallelism and ordering | Order guaranteed per partition only |
| **Consumer groups** | Each partition consumed by exactly one consumer in group | Scale = add consumers (up to #partitions) |
| **Partition assignment** (range, round-robin, sticky, **cooperative-sticky**) | How partitions divide across consumers | Cooperative-sticky avoids stop-the-world rebalance |
| **Offset commit** | Consumer tracks position; `enable.auto.commit=false` + manual commit | Manual commit = exactly-once in practice |
| **ISR (In-Sync Replicas)** | Replicas caught up to leader | `min.insync.replicas=2` + `acks=all` = no data loss |
| **`acks`** | `0`(fire-forget), `1`(leader), `all`(all ISR) | **Always `acks=all` for durability** |
| **Idempotent producer** (`enable.idempotence=true`) | Dedupes retries via producer ID + seq | Default since 3.0 |
| **Transactional producer** | Atomic writes across partitions + offset commit | Enables exactly-once stream processing |
| **Log compaction** | Keep only latest value per key (vs retention by time) | Changelog topics, CDC, state snapshots |
| **Compacted topic** | `cleanup.policy=compact` | Materialize current state from infinite log |
| **Tiered storage** (Kafka 3.6+, Confluent) | Hot segments on broker, cold on S3 | Cheap long retention |
| **KRaft mode** | Replaces ZooKeeper with Raft inside Kafka | 3.3+ GA; new clusters only |
| **Schema Registry** (Avro / Protobuf / JSON Schema) | Enforce schema compatibility | Prevents breaking consumers |
| **Kafka Streams / ksqlDB** | Stream processing library + SQL | Alternative to Flink for Kafka-only pipelines |
| **MirrorMaker 2** | Cross-cluster replication | DR, multi-region |
| **Rebalance protocol** | When consumer joins/leaves, partitions reassigned | Classic rebalance = stop-the-world; cooperative = incremental |
| **Leader epoch** | Prevents divergent writes after leader failover | Fixes historical "lost data on unclean leader election" |

---

#### Neo4j / Graph signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Cypher** | ASCII-art pattern query language | `MATCH (a)-[:FOLLOWS*2..3]-(b)` |
| **Index-free adjacency** | Each node has pointers to its relationships | O(1) hop vs SQL join cost per hop |
| **Native graph storage** | Fixed-size records + double-linked relationship list | Why 6-hop queries are fast |
| **Labels + properties** | `(:User {name:'Alice'})` | Multi-label indexes |
| **APOC** | Standard library for utility procedures | `apoc.periodic.iterate` for batched updates |
| **Graph Data Science (GDS)** | PageRank, community detection, shortest path, node embeddings | Analytics on graph |
| **Causal cluster** (enterprise) | Core servers (Raft) + read replicas | HA + bookmarks for causal consistency |
| **Bookmarks** | Client token for "read your writes" across cluster | `tx.commit(); next session uses bookmark` |
| **Patterns** | `MATCH`, `OPTIONAL MATCH`, `MERGE` (upsert), `WHERE` | `MERGE` creates if not exists — careful about index backing |
| **Variable-length paths** | `[:FOLLOWS*2..5]` | Set a hop limit — infinite can OOM |
| **Full-text / vector indexes** | Lucene inside Neo4j | For hybrid "graph + search" |

---

#### Snowflake / BigQuery signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **Micro-partitions** (Snowflake) | 50-500 MB immutable file units | Column pruning + partition elimination automatic |
| **Clustering keys** | Co-locate rows by column (reclustering is auto) | No manual partition design like BigQuery |
| **Partitioning + clustering** (BigQuery) | Partition by date, cluster by up to 4 cols | **Must declare at table creation** |
| **Time travel** | Query data `AT (TIMESTAMP => ...)` (Snowflake 90 days, BQ 7 days) | Oops-recovery, audit |
| **Zero-copy clones** | Instant branch of a table / schema / database | Dev environments without data copy cost |
| **Streams and Tasks** (Snowflake) | Change tracking + scheduled transforms | In-warehouse CDC + ELT |
| **External tables** | SQL over Parquet in S3 / GCS | Lakehouse pattern |
| **Materialized views** | Pre-computed incrementally | Auto-refresh in both |
| **Approximate functions** | `APPROX_COUNT_DISTINCT` (HLL), `APPROX_QUANTILES` | 10-100× faster on billions of rows |
| **Separation of storage and compute** | Virtual warehouses scale independently | Pause when idle = save money |
| **Multi-cluster warehouse** (Snowflake) | Auto-scale concurrent queries | For bursty analyst load |
| **Cost model** | Snowflake: credits per warehouse-second. BigQuery: on-demand bytes scanned OR slots | **Always `LIMIT`-guard dev queries** |

---

#### Spanner / CockroachDB signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **TrueTime** (Spanner only) | GPS + atomic clock bounded uncertainty | Enables external consistency without consensus for reads |
| **Commit wait** | Transaction waits out clock uncertainty (~7ms) | Price of external consistency |
| **Interleaved tables** | Store child rows adjacent to parent → single-split joins | Critical for 1:N relationships |
| **Read-only transactions** | Lock-free, choose snapshot timestamp | Analytical queries don't block OLTP |
| **Bounded staleness reads** | `READ_TIMESTAMP = now - 5s` | Faster than strong read; still consistent |
| **Change streams** (Spanner) / **CDC** (CockroachDB) | Native change feed | For event-driven downstreams |
| **Range splits** | Automatic rebalancing of key ranges | No manual sharding |
| **Follower reads** | Read from nearest replica at stale timestamp | Low latency globally |
| **Multi-region configs** | `nam3`, `eur3`, etc. | Pick latency-vs-availability tradeoff |

---

#### Vector DB signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **HNSW** params `M`, `ef_construction`, `ef_search` | Graph connectivity; recall/latency knobs | Higher ef = better recall, slower query |
| **IVF** params `nlist`, `nprobe` | Cluster count; clusters to probe at query | Needs training on sample data |
| **Quantization** (PQ, SQ, binary) | Compress vectors 4-32× | Loses ~1-5% recall; needed at billion-scale |
| **Metadata filter** | Combine ANN with `tenant_id = 'X'` | **Pre-filter** (slow) vs **post-filter** (may return <k) |
| **Hybrid search** | Dense vector + BM25 sparse, fused via **Reciprocal Rank Fusion (RRF)** | Semantic + keyword best of both |
| **Reranker stage** | Top-K retrieved → cross-encoder rerank → top-N | Trade $ for quality |
| **Namespaces / collections** | Logical partition per tenant / doc type | Required for multi-tenant RAG |
| **Vector + payload** | Embedding + JSON metadata in same record | Avoid extra DB lookup |
| **Index build vs query** | HNSW build is slow + RAM-heavy | Build offline, serve from read-only replicas |

---

#### Delta Lake / Iceberg / Hudi (table format) signature features

| Feature | What it does | Phrase |
|---------|--------------|--------|
| **ACID on object storage** | Metadata + manifest files add transactions to Parquet | S3 as a database |
| **Time travel** | `VERSION AS OF 42` | Rollback bad batch, audit |
| **Schema evolution** | Add/rename/drop column without rewrite | Columns tracked by ID in Iceberg |
| **Partition evolution** (Iceberg) | Change partitioning without rewrite | Delta/Hudi don't support cleanly |
| **Hidden partitioning** (Iceberg) | Partition by `day(ts)` without extra column | No `WHERE partition_col = ...` boilerplate |
| **Z-ordering** (Delta) | Multi-dimensional clustering | Faster multi-column filter |
| **Compaction / OPTIMIZE** | Merge small files | Mandatory ops job for streaming ingest |
| **Vacuum** | Delete old versions past retention | Reclaim S3 space |
| **CDC output** (Delta Change Data Feed) | Stream row-level changes | Powers downstream pipelines |

---

### 22. The Honest Database Scorecard

A seasoned engineer admits every DB's weakness. Use these in interviews — honesty beats salesmanship.

| DB | Honest weakness most people miss |
|----|----------------------------------|
| PostgreSQL | TXID wraparound, replication slot bloat, PgBouncer required past 500 conns |
| MySQL | Gap locks, UUID PK write-amp, online DDL caveats |
| Cassandra | Tombstones, repairs are operational burden, no joins ever |
| MongoDB | 16MB doc cliff, oplog window pressure, mediocre joins |
| Redis | Single-thread blocking, hot key problem, no cluster-wide tx |
| DynamoDB | Partition heat, scan cost, 400KB item cap |
| Elasticsearch | Not durable source of truth, JVM heap tuning hell, reindex pain |
| Kafka | Ops complexity, no per-message TTL, consumer rebalance pauses |
| Neo4j | Hard to shard, enterprise license for clustering, limited analytics |
| Spanner | Price, cross-region latency floor, limited ecosystem |

---

## OLTP Databases

*Online Transaction Processing — fast row-level reads and writes for live applications.*

---

## 1. Relational (SQL) Databases

**Examples:** PostgreSQL, MySQL, MariaDB, Oracle, SQL Server

### What it is

Data in **tables** (rows + columns) with a **fixed schema**. Relationships via **foreign keys**. Queries via **SQL** — joins, aggregations, transactions.

### How it's built

```
Client → connection pool → query planner → executor
                              ↓
                    B-Tree indexes + heap pages
                              ↓
                    WAL (Write-Ahead Log) → disk
                              ↓
                    Replication (streaming) → replicas
```

- **Query optimizer** picks index scan vs seq scan — huge advantage for complex queries
- **MVCC** (Postgres): readers don't block writers; each tx sees snapshot
- **Indexes:** B-Tree (default), GIN/GiST (Postgres for JSON, full-text), partial indexes

### Data model

```sql
CREATE TABLE bookings (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id),
    showtime_id UUID NOT NULL REFERENCES showtimes(id),
    status      TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

### Advantages

| Advantage | Why it matters |
|-----------|----------------|
| ACID transactions | Money, inventory, seat booking |
| Flexible queries | Ad-hoc reporting without redesign |
| Joins | Normalize data, avoid duplication |
| Mature ecosystem | Backups, migrations, monitoring |
| Strong constraints | DB enforces integrity, not just app code |

### Disadvantages

| Disadvantage | When it hurts |
|--------------|---------------|
| Vertical scaling limits | Single node ~ few TB, ~50k TPS |
| Schema migrations | Fast iteration on early product |
| Joins at billions of rows | Need sharding + denormalization |
| Multi-region writes | Leader in one region → cross-region latency |

### When to use

- **Transactions matter:** payments, bookings, accounts
- **Relationships matter:** e-commerce orders ↔ items ↔ users
- **Query patterns evolve:** you don't know all queries upfront
- **Moderate scale:** < few TB, < ~50k writes/sec on one primary

### When NOT to use

- Billions of writes/day append-only (→ Cassandra/Kafka)
- Sub-ms reads at millions QPS (→ Redis)
- Graph traversal (→ Neo4j)
- Time-range analytics on metrics (→ time-series DB)

### HLD scenarios

| System | Why SQL |
|--------|---------|
| Movie ticket booking | ACID seat hold + payment; `SELECT ... FOR UPDATE` |
| E-commerce checkout | Order + inventory decrement in one tx |
| User accounts / auth | Strong consistency on credentials |
| Admin dashboards | Ad-hoc SQL reports |

### Interview answer template

> "Core booking and payment state lives in **PostgreSQL** for ACID. A user holds seats, pays, and confirms in a transaction — we can't have double booking. Reads for show listings can be cached in Redis, but the source of truth is relational."

### Scaling SQL (mention these)

1. **Read replicas** — scale reads, eventual consistency on replica
2. **Connection pooling** — PgBouncer; don't open 10k connections
3. **Sharding** — by `user_id` or `tenant_id` (Vitess, Citus, app-level)
4. **Caching** — Redis in front for hot reads
5. **CQRS** — SQL for writes, search index / warehouse for reads

---

### 🔬 PostgreSQL Deep Dive — the DB you'll be asked about most

Postgres is the default source-of-truth in 80% of system designs. Interviewers push on these internals.

#### Write path — step by step

```
1. Client sends INSERT/UPDATE over TCP
2. Backend process parses + plans
3. Row acquires lock (if needed): row-level, no table lock
4. Row written to shared_buffers (RAM page cache, usually 25% of RAM)
5. Change written to WAL buffer (Write-Ahead Log, in RAM)
6. COMMIT:
     a. WAL flushed to disk (fsync, durable now)
     b. commit returned to client
7. (async) BGWriter periodically writes dirty pages to data files
8. (async) Checkpointer every ~5 min: force all dirty pages to disk, truncate WAL
9. (async) WAL sender streams WAL to replicas
```

**Key insight:** commit returns as soon as **WAL is on disk**, not when the data page is. Data pages get flushed lazily. If server crashes, Postgres replays WAL on restart (**crash recovery**).

#### Read path — the three caches

```
Query → shared_buffers (8KB pages)      → HIT: return immediately (ns)
                                        → MISS:
                                             OS page cache (free RAM)  → HIT (µs)
                                             → MISS: disk read (SSD ~150µs, HDD ~10ms)
                                             → fill shared_buffers → return
```

**Rule:** working set should fit in `shared_buffers + OS cache`. Query `pg_stat_database.blks_read` vs `blks_hit` — ratio > 95% hit is healthy.

#### Lock types (named, know all 5)

| Lock | Scope | When | Blocks |
|------|-------|------|--------|
| **Row lock** (`FOR UPDATE`) | one row | explicit or via UPDATE | other UPDATE/FOR UPDATE on same row |
| **Advisory lock** (`pg_advisory_lock(123)`) | app-defined ID | explicit | same ID holder |
| **Table lock** (`LOCK TABLE`) | whole table | DDL, explicit | varies by mode (8 levels) |
| **Predicate lock** (SSI) | logical predicate | auto in SERIALIZABLE | conflicting predicate reads/writes |
| **SIReadLock** | tracked for SSI | SERIALIZABLE only | tracks potential conflicts |

**Common question:** *"How do I implement a job queue in Postgres?"*

```sql
-- Worker atomically grabs next unclaimed job without blocking others
UPDATE jobs
SET status = 'processing', worker_id = $1
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'queued'
  ORDER BY created_at
  LIMIT 1
  FOR UPDATE SKIP LOCKED      -- ← the magic: skip rows other workers locked
)
RETURNING *;
```

`FOR UPDATE SKIP LOCKED` is Postgres's killer feature for queue-in-DB patterns. No need for Redis/SQS for small-to-medium queues.

#### VACUUM internals (the #1 cause of Postgres outages)

Every `UPDATE` or `DELETE` creates **dead tuples** (old row versions). VACUUM reclaims them.

```
VACUUM phases:
  1. Scan heap: find dead tuples via visibility map
  2. Scan all indexes: mark index entries for dead tuples
  3. Scan heap again: physically remove dead tuples, free space
  4. Update free-space map and visibility map
  5. Truncate trailing empty pages back to OS (if any)

VACUUM FULL: rewrites entire table (locks it) — rarely needed, use pg_repack instead
```

**Autovacuum** runs when:
- Table has > `autovacuum_vacuum_threshold` (50) + `autovacuum_vacuum_scale_factor` (0.2) × row_count dead tuples
- Age approaching `autovacuum_freeze_max_age` (200M txns) → **anti-wraparound vacuum** (cannot be disabled)

**When autovacuum falls behind:**
- Dead tuples accumulate → **bloat** → table 10× its necessary size
- Sequential scans slow down → whole queries slow
- Index bloat → index-only scans fail
- Eventually: TXID wraparound → **emergency shutdown**

**Monitoring queries:**
```sql
-- Check bloat
SELECT schemaname, relname, n_dead_tup, n_live_tup,
       round(n_dead_tup::numeric / NULLIF(n_live_tup,0) * 100, 1) AS pct_dead
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;

-- Check autovacuum lag
SELECT relname, last_autovacuum, autovacuum_count
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Check TXID age (danger if > 500M)
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY age(datfrozenxid) DESC;
```

**Tuning for hot tables:**
```sql
ALTER TABLE events SET (
  autovacuum_vacuum_scale_factor = 0.05,     -- vacuum at 5% dead, not 20%
  autovacuum_analyze_scale_factor = 0.02,
  fillfactor = 70                            -- leave 30% space for HOT updates
);
```

#### WAL internals and replication

```
LSN (Log Sequence Number) — monotonically increasing byte offset in WAL
  Replica tracks its LSN; primary knows how far behind each replica is.

Streaming replication:
  Primary → WAL sender → network → WAL receiver → startup process
                                                → replays into replica

Replication modes:
  async        → fast, replica may lag seconds (data loss window on primary crash)
  sync (ANY 1) → wait for 1 replica to confirm
  sync (ANY 2) → wait for 2 replicas
  remote_apply → wait until replica actually applied (slowest, strongest)
```

**Logical replication** (basis for Debezium CDC):
- WAL decoded into row-level change events (INSERT/UPDATE/DELETE per table)
- Subscriber consumes via `pg_logical_slot_get_changes` or replication protocol
- **Replication slot pins WAL** — abandoned slot = disk fills = outage

**Replication slot query (must monitor):**
```sql
SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots;
```

#### Connection management — the hard scaling ceiling

| Connections | Reality |
|-------------|---------|
| 10–100 | Fine, direct |
| 100–500 | Need connection pool (pgbouncer) |
| 500+ | **Pgbouncer in transaction mode** — share backend connections across clients |
| 10k clients | Pgbouncer front, ~500 Postgres backends; each client claims backend only during active tx |

**Why connections are expensive in Postgres:** each connection = full OS process + ~10MB RAM + context switches. (Unlike MySQL thread model.)

**Pgbouncer modes:**
- `session` — client holds connection for whole session (no pooling benefit)
- `transaction` — connection returned to pool after each COMMIT (**default for apps**)
- `statement` — pooled per statement (breaks tx — rarely used)

#### EXPLAIN ANALYZE — read it like this

```
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders o JOIN users u ON u.id = o.user_id
WHERE o.created_at > now() - interval '7 days';

                                     QUERY PLAN
-------------------------------------------------------------------------------------
 Hash Join  (cost=1.09..24.42 rows=12 width=72) (actual time=0.038..0.049 rows=12 loops=1)
   Hash Cond: (o.user_id = u.id)
   Buffers: shared hit=5
   ->  Seq Scan on orders o  (cost=0.00..23.00 rows=12 width=40) (actual time=0.012..0.019 rows=12 loops=1)
         Filter: (created_at > (now() - '7 days'::interval))
         Rows Removed by Filter: 988
         Buffers: shared hit=4
   ->  Hash  (cost=1.04..1.04 rows=4 width=36) (actual time=0.012..0.013 rows=4 loops=1)
         ->  Seq Scan on users u
 Planning Time: 0.287 ms
 Execution Time: 0.098 ms
```

**What to read:**
- `cost=...` → optimizer's estimate (**ignore absolute, compare ratios**)
- `actual time=startup..total rows=X loops=Y` → the truth
- `Rows Removed by Filter: 988` → 988 rows scanned to find 12. **Missing index.**
- `Buffers: shared hit=5` → came from cache. **`read=` instead = disk.**
- **If estimated rows and actual rows differ 10×+ → stale statistics → ANALYZE**

#### Partitioning (declarative since v10)

```sql
-- Range partition by month
CREATE TABLE events (
  id BIGSERIAL,
  created_at TIMESTAMPTZ NOT NULL,
  user_id UUID,
  payload JSONB
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2026_01 PARTITION OF events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE events_2026_02 PARTITION OF events
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Index on each partition (not inherited; create per partition or on parent)
CREATE INDEX ON events (user_id, created_at);
```

**Benefits:**
- `DROP TABLE events_2024_01` = instant deletion of old data (vs `DELETE WHERE created_at < ...` = full table scan + bloat)
- Partition pruning: `WHERE created_at > '2026-02-01'` only scans one partition
- **Automate with `pg_partman`** — pre-creates future partitions, drops old ones

#### Sharding options (when single node runs out)

| Tool | Model | Status |
|------|-------|--------|
| **Citus** (Microsoft) | Distributed table + reference table; coordinator + workers | Mature, Azure-managed |
| **Vitess** | MySQL-focused but used with Postgres via adapter | YouTube-scale |
| **Postgres-XL** | Fork with distributed query | Smaller community |
| **Spanner / CockroachDB** | Postgres wire protocol, fully distributed | Different DB, drop-in client |
| **App-level sharding** | Partition by `tenant_id`, pick shard in app | Most control, most work |

**Sharding anti-pattern:** cross-shard JOIN. Design to avoid.

#### Postgres-specific tunables (interview-worthy)

| Setting | Default | What to set | Why |
|---------|---------|-------------|-----|
| `shared_buffers` | 128MB | 25% of RAM | Primary cache |
| `effective_cache_size` | 4GB | 50-75% of RAM | Planner uses to estimate index value |
| `work_mem` | 4MB | 32-64MB | Sort/hash per operator — too high + 1000 queries = OOM |
| `maintenance_work_mem` | 64MB | 1-2GB | VACUUM, CREATE INDEX speed |
| `max_connections` | 100 | 100-300 + pgbouncer | Beyond this needs pooler |
| `wal_level` | replica | `logical` for CDC | Enables logical replication |
| `random_page_cost` | 4.0 | 1.1 on SSD | Default assumes HDD; makes planner avoid indexes |
| `checkpoint_timeout` | 5min | 15-30min | Smoother I/O for high write |
| `max_wal_size` | 1GB | 4-16GB | More headroom between checkpoints |

#### Postgres anti-patterns (red flags)

| Anti-pattern | Why bad | Do instead |
|--------------|---------|------------|
| UUID v4 as PK | random inserts into B-tree = page splits + write amp | UUID v7 (time-ordered) or `BIGSERIAL` |
| `SELECT *` in production | Returns bloat, breaks index-only scans | Column list |
| OR in WHERE across different columns | Can't use index | Split into UNION, or GIN multi-column |
| `COUNT(*)` on huge table | Seq scan always (no stored count) | Approximate via `pg_class.reltuples` or counter table |
| `OFFSET 1000000 LIMIT 20` | Scans 1M+20 rows | Keyset pagination: `WHERE id > :last_id LIMIT 20` |
| Many-column indexes "just in case" | Each index += write cost + bloat | Build on evidence from `pg_stat_user_indexes` |
| Long-running tx | Pins xmin → blocks VACUUM → bloat | Keep tx < seconds; don't do analytics on OLTP |
| `TEXT` for enums | No validation, no stats | `CREATE TYPE AS ENUM` or FK to lookup table |

#### Realistic Postgres capacity

| Hardware | Reasonable load |
|----------|-----------------|
| 4 vCPU, 16GB RAM, NVMe | 5K TPS writes, 20K QPS indexed reads, 500GB data |
| 16 vCPU, 64GB, NVMe | 20K TPS, 100K QPS, 2TB data |
| 32 vCPU, 256GB, NVMe + RAID | 50K TPS, 500K QPS, 5TB data |
| Beyond that | Shard or move hot path to Cassandra/Redis |

#### The question interviewers ask

1. *"Your writes slowed to 10% overnight. First check?"*
   → Autovacuum lag + replication slot + long-running tx.
2. *"How would you do a job queue in Postgres?"*
   → `FOR UPDATE SKIP LOCKED` + a `status` enum + partial index on `status='queued'`.
3. *"Why not use `SELECT COUNT(*)` for pagination?"*
   → Always seq scan. Approximate via `pg_class.reltuples` or maintain a counter.
4. *"How do you shard Postgres?"*
   → Avoid as long as you can. Then: Citus for app-transparent distribution, or app-level by `tenant_id`.
5. *"Why did your query that worked yesterday do a seq scan today?"*
   → Stale stats. `ANALYZE table_name`. Or `random_page_cost` set wrong.

---

## 2. Wide-Column / Column-Family (Cassandra, HBase)

**Examples:** Apache Cassandra, ScyllaDB, HBase, Amazon Keyspaces

### What it is

No SQL joins. Data stored in **wide rows** keyed by **partition key** + **clustering columns**. Optimized for **distributed writes** and **partition-local reads**.

### How it's built

```
                    Coordinator node
                          |
            +-------------+-------------+
            |             |             |
        Node A        Node B        Node C
     (token ring / consistent hashing)
     
Each node:
  LSM-Tree (SSTables) + commit log
  Gossip protocol for cluster membership
  Hinted handoff, read repair for consistency
```

- **Dynamo-inspired:** quorum reads/writes (R + W > N)
- **No master:** any node can coordinate (peer-to-peer)
- **Tunable consistency:** `ONE`, `QUORUM`, `ALL`

### Data model (Cassandra)

```sql
-- Partition key: user_id (all data for user on same node)
-- Clustering key: created_at (sorted within partition)
CREATE TABLE user_events (
    user_id     UUID,
    created_at  TIMESTAMP,
    event_type  TEXT,
    payload     TEXT,
    PRIMARY KEY (user_id, created_at)
);
```

**Critical rule:** every query must include the **partition key**. No partition key = full cluster scan = disaster.

### Advantages

| Advantage | Details |
|-----------|---------|
| Write throughput | LSM + no leader bottleneck |
| Linear horizontal scale | Add nodes → more capacity |
| Multi-datacenter | Native replication per DC |
| Always-on | AP system — survives node failures |
| Time-series friendly | Clustering by timestamp within partition |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| No joins | Denormalize upfront or read multiple tables |
| No ad-hoc queries | Design tables per query pattern |
| Eventual consistency | Stale reads unless QUORUM + LWT |
| Updates/deletes are tombstones | Compaction needed; never delete-heavy without care |
| Hot partitions | Bad partition key → one node overloaded |

### When to use

- **Write-heavy** event logs, activity feeds, IoT ingest
- **Known access patterns** at design time
- **Multi-region** with local reads
- **High availability** over strong consistency

### When NOT to use

- Complex joins and ad-hoc analytics
- Strong ACID across rows (use LWT sparingly — slow)
- Frequent updates to same cell

### HLD scenarios

| System | Cassandra design |
|--------|------------------|
| **Twitter/X timeline** | `PRIMARY KEY (user_id, tweet_id)` — all tweets for user in one partition |
| **Instagram feed** | Denormalized: write fan-out table per follower |
| **IoT sensor data** | `PRIMARY KEY (device_id, timestamp)` |
| **Chat messages** | `PRIMARY KEY (conversation_id, message_id)` |
| **Netflix viewing history** | Append-only per user partition |

### Interview answer template

> "User activity events go to **Cassandra** — append-only, millions of writes/sec, query by `user_id` + time range. We denormalize: one table for 'events by user', another for 'events by type' if needed. Core account balance stays in Postgres."

### Cassandra vs HBase

| | Cassandra | HBase |
|---|-----------|-------|
| Consistency | Tunable quorum | Strong within row |
| Query | CQL, limited | Scan-oriented |
| Ecosystem | Standalone | Hadoop/HDFS |
| Best for | Real-time apps | Batch + random read on big data |

---

### 🔬 Cassandra Deep Dive — the write-scale beast

#### Write path — step by step (why writes are so fast)

```
1. Client sends INSERT with CL=QUORUM (consistency level)
2. Any node receives → becomes coordinator for this request
3. Coordinator uses partition key → consistent hash → finds N replicas
4. Coordinator sends write to ALL N replicas in parallel
5. Each replica:
     a. Append to commit log (durable, sequential disk write)
     b. Insert into memtable (sorted structure in RAM)
     c. ACK coordinator
6. Coordinator waits for N/2+1 ACKs (QUORUM) → ACK client
7. (async) When memtable full → flush to SSTable (immutable disk file)
8. (async) Compaction merges SSTables (background)
```

**Why fast:** no leader election per write, no index update, no update-in-place. **Sequential writes only.**

#### Read path — why reads are harder than writes

```
1. Client sends SELECT with partition key, CL=QUORUM
2. Coordinator finds N replicas
3. Coordinator sends read to R replicas (R = CL)
4. Each replica:
     a. Check row cache (if enabled)
     b. Check memtable
     c. For each SSTable (newest first):
        - Check bloom filter → skip if definitely not here
        - Check key cache → skip to offset
        - Read partition index → read partition summary → read data
     d. Merge all versions (last-write-wins by timestamp)
     e. Return to coordinator
6. Coordinator compares replica responses:
     - If mismatch → read repair (async: fix stale replica)
     - Return newest version to client
```

**Why reads can be slow:** worst case, you touch many SSTables. **Mitigations:** bloom filter (skip SSTable 99% of time), key cache, row cache, leveled compaction (fewer SSTables per read).

#### Data modeling methodology — "query-first design"

**Rule:** design one table per query. **Never** try to make one table serve multiple access patterns.

**Example: chat app with 3 queries**

```
Query 1: Get all messages in a conversation (newest first)
Query 2: Get all conversations a user is in
Query 3: Get unread count per user

→ 3 tables, NOT 1 messages table:

CREATE TABLE messages_by_conversation (
  conversation_id UUID,
  message_id TIMEUUID,         -- timeUUID = timestamp + unique
  sender_id UUID,
  content TEXT,
  PRIMARY KEY (conversation_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
-- Partition: conversation_id. Clustered: message_id. Newest first.

CREATE TABLE conversations_by_user (
  user_id UUID,
  conversation_id UUID,
  last_message_at TIMESTAMP,
  PRIMARY KEY (user_id, last_message_at, conversation_id)
) WITH CLUSTERING ORDER BY (last_message_at DESC);

CREATE TABLE unread_count_by_user (
  user_id UUID PRIMARY KEY,
  count COUNTER                -- special counter column
);
```

**Writes become fan-out:** sending a message = 3 writes (1 per table). Trade write amplification for read speed.

#### Partition sizing — the hard limits

| Metric | Soft limit | Hard limit |
|--------|-----------|-----------|
| Partition size | 10 MB | 100 MB |
| Rows per partition | 10K | 100K |
| Tombstones per partition read | 1K (warn) | 100K (fail) |
| Cells per partition | 100K | 2 billion |

**Hot partition problem:** `PRIMARY KEY (country, event_time)` → USA gets 100× more events than Luxembourg → one node overloaded.

**Fix: composite partition key with bucketing**

```sql
-- Bad: country partitions get skewed
CREATE TABLE events_bad (
  country TEXT,
  event_time TIMESTAMP,
  payload TEXT,
  PRIMARY KEY (country, event_time)
);

-- Good: bucket by day → bounded partition size, even distribution
CREATE TABLE events_good (
  country TEXT,
  day DATE,                   -- bucket
  event_time TIMESTAMP,
  payload TEXT,
  PRIMARY KEY ((country, day), event_time)   -- composite partition key
);
-- Query: WHERE country='US' AND day='2026-10-09'
```

#### Consistency level cheat sheet

| CL | Writes | Reads | When |
|----|--------|-------|------|
| `ONE` | 1 replica | 1 replica | Metrics, logs — fastest, loosest |
| `QUORUM` | majority | majority | **Default for most apps** — strong consistency when W+R > N |
| `LOCAL_QUORUM` | majority in local DC | same | Multi-DC — fast local reads, cross-DC async |
| `EACH_QUORUM` | majority in each DC | — | Writes only — cross-DC durability |
| `ALL` | all replicas | all | Rarely — any node down = failure |
| `SERIAL` | Paxos LWT | linearizable read | `IF NOT EXISTS` — 4× slower |

**Formula:** W + R > N → strongly consistent read-after-write. (RF=3 → QUORUM reads+writes = always see latest.)

#### Repair — the operational burden you must mention

```
nodetool repair -pr   # primary range repair, run on every node once per gc_grace_seconds
```

- Compares Merkle trees across replicas
- Streams missing/stale data
- **Must complete within `gc_grace_seconds` (default 10 days)** — otherwise deleted data can resurrect ("zombie data")
- Full-cluster repair takes **hours to days** at TB scale
- **Reaper tool** (Cassandra Reaper) automates and parallelizes repairs — essential for production

#### Anti-patterns (interview red flags)

| Anti-pattern | Why bad | Do instead |
|--------------|---------|------------|
| `ALLOW FILTERING` | Full cluster scan | Add proper partition key |
| Secondary index on high-cardinality column | Per-node scatter-gather | Denormalize to new table |
| Secondary index on low-cardinality column | One node holds all matches = hot | Same — denormalize |
| Delete-heavy workloads | Tombstones kill reads | Use TTL on inserts; design append-only |
| Large partitions (>100 MB) | GC pauses, repair failures | Bucket by time/hash |
| `BATCH` for performance | LOGGED batch is 30% slower | Use async writes |
| LWT for every write | 4× latency, 4 round-trips | Only when `IF NOT EXISTS` truly required |
| Reads with CL=ALL | Any down node = failure | QUORUM |
| Updating same cell millions of times | Compaction can't keep up | Model append-only |
| Not running repair | Zombie data | Schedule Reaper |

#### "Prove you know Cassandra" questions

1. *"How does Cassandra achieve such high write throughput?"*
   → LSM tree + commit log + no leader. Every write = sequential disk append. No read before write. Coordinator fans out in parallel.
2. *"You see read latency spike after a deploy that added more writes."*
   → Compaction can't keep up → more SSTables per read → more disk I/O. Check `nodetool compactionstats`. Consider LCS or more compaction threads.
3. *"How would you model Instagram's feed?"*
   → `PRIMARY KEY (user_id, post_timestamp)` with reverse clustering. Fan-out on write for normal users; fan-out on read for celebrities.
4. *"Your table has tombstones warnings in logs — why?"*
   → Delete-heavy workload or TTL+rewrite pattern. Tombstones stick around for `gc_grace_seconds`. Fix: model as append-only + partition by time bucket.
5. *"Compare `QUORUM` vs `LOCAL_QUORUM`."*
   → QUORUM waits for N/2+1 across all DCs (cross-DC latency). LOCAL_QUORUM waits only within local DC. **Always use LOCAL_QUORUM in multi-DC.**

---

## 3. Document Databases (MongoDB)

**Examples:** MongoDB, CouchDB, Amazon DocumentDB, Firebase Firestore

### What it is

Data stored as **JSON-like documents** (BSON). **Flexible schema** — documents in same collection can differ. **No joins** by default ( `$lookup` exists but is expensive).

### How it's built

```
mongod → WiredTiger storage engine (B-Tree)
       → document-level locking
       → replica set (primary + secondaries)
       → sharded cluster (mongos router + config servers)
```

- Documents stored contiguously — reading one doc is fast
- Indexes on any field (single, compound, multikey for arrays)
- Change streams for real-time sync

### Data model

```json
{
  "_id": "showtime-123",
  "movie": { "title": "Inception", "duration": 148 },
  "theater": "IMAX-1",
  "seats": [
    { "id": "A1", "type": "PREMIUM", "state": "AVAILABLE" },
    { "id": "A2", "type": "PREMIUM", "state": "HELD" }
  ],
  "pricing": { "PREMIUM": 1500, "REGULAR": 800 }
}
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Flexible schema | Product iteration without migrations |
| Nested data | One read gets whole aggregate (showtime + seats) |
| Developer speed | Maps naturally to JSON APIs |
| Horizontal sharding | Built into MongoDB |
| Rich query language | vs pure key-value |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Document size limit | 16 MB max per document |
| Joins are weak | Denormalization → stale embedded data |
| Multi-doc ACID | Only since v4.0, with performance cost |
| Memory hungry | Indexes + working set should fit RAM |

### When to use

- **Content management:** blogs, catalogs, product configs
- **Aggregates:** one document = one thing you always read together
- **Rapid prototyping:** schema not stable
- **Mobile sync:** document maps to client state

### When NOT to use

- Heavy relational reporting across entities
- High-frequency updates to large arrays (seat map in one doc → write contention)
- Financial transactions needing strict ACID (prefer SQL)

### HLD scenarios

| System | MongoDB design |
|--------|----------------|
| **Product catalog** | One doc per product with variants, images, specs |
| **User profiles** | Nested preferences, addresses, settings |
| **CMS** | Article with embedded comments (or separate collection) |
| **Game state** | Player inventory as nested document |

### Movie booking note

For seat booking, MongoDB is **risky** if entire seat map is one document — 200 seats updated concurrently = document-level lock. Better: **SQL row per seat** or **Redis per seat**.

### Interview answer template

> "Movie **catalog** (title, cast, posters, metadata) in **MongoDB** — read-heavy, schema varies by content type. **Seat inventory** in Postgres or Redis — needs atomic per-seat updates, not whole-document writes."

---

## 4. Key-Value Stores (Redis, DynamoDB)

### 4a. In-Memory Key-Value (Redis, Memcached)

**Examples:** Redis, Memcached, KeyDB

### How it's built

```
All data in RAM (mostly)
  → hash table: key → value
  → optional persistence: RDB snapshots + AOF log
  → single-threaded event loop (Redis) = no lock contention per key
  → cluster mode: hash slot → node
```

**Redis data structures:** string, hash, list, set, sorted set, stream, HyperLogLog, GEO

### Advantages

| Advantage | Details |
|-----------|---------|
| Sub-millisecond latency | RAM-speed |
| Atomic operations | `INCR`, `SETNX`, sorted set ops |
| TTL built-in | Auto-expire sessions, holds |
| Pub/sub, streams | Real-time features |
| Lua scripts | Atomic multi-key logic |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Memory cost | $$$ at TB scale |
| Durability optional | Not primary source of truth (usually) |
| Limited query | Only by key (or scan — slow) |
| Hot key problem | One viral key → one shard overload |

### When to use

| Use case | Redis pattern |
|----------|---------------|
| **Session cache** | `SET session:{id} JSON EX 3600` |
| **Rate limiting** | `INCR` + TTL sliding window |
| **Seat hold (TTL)** | `SET seat:{show}:{id} hold_id EX 600` |
| **Leaderboard** | Sorted set `ZADD leaderboard score user` |
| **Pub/sub notifications** | `PUBLISH channel msg` |
| **Distributed lock** | Redlock (with caveats) |

### Movie booking example

```
HOLD flow:
  SETNX seat:show123:A1 hold-uuid EX 600   → atomic grab
  if OK → proceed to payment
  on confirm → DELETE key + write Postgres
  on timeout → key auto-expires → seat free
```

---

### 🔬 Redis Deep Dive — the swiss army knife (far beyond cache)

Interviewers push on data structures and cluster behavior.

#### Data structure → use case mapping

| Structure | Op cost | Killer use case |
|-----------|---------|-----------------|
| **String** | O(1) | Cache, counter (`INCR`), lock (`SETNX`), bitmap ops |
| **Hash** | O(1) per field | Store object with partial updates (`HSET user:1 name Alice`) |
| **List** | O(1) at ends | Job queue (`LPUSH/BRPOP`), timeline, latest-N |
| **Set** | O(1) add/member | Unique tags, mutual friends (`SINTER`) |
| **Sorted Set (ZSET)** | O(log N) | **Leaderboard, sliding-window rate limit, delayed queue, geo** |
| **Stream** | O(1) append | Kafka-lite inside Redis, consumer groups, at-least-once |
| **Bitmap** | O(1) bit op | DAU tracking (1 bit per user per day) |
| **HyperLogLog** | O(1), 12KB fixed | Cardinality estimate (unique visitors) with 0.81% error |
| **GEO** | O(log N) | Nearest driver, store locator (geohash + sorted set) |
| **Bitfield** | O(1) | Compact counters, feature flags |

#### Classic patterns (interview-ready code)

**Sliding-window rate limiter (ZSET):**

```python
# Allow 100 requests per 60 seconds per user
now = time.time()
key = f"rl:{user_id}"
pipe = r.pipeline()
pipe.zremrangebyscore(key, 0, now - 60)   # drop old entries
pipe.zadd(key, {str(uuid4()): now})       # add this request
pipe.zcard(key)                            # count in window
pipe.expire(key, 60)
_, _, count, _ = pipe.execute()
if count > 100:
    raise RateLimitExceeded()
```

**Leaderboard (ZSET):**

```redis
ZADD leaderboard 2500 user:alice
ZADD leaderboard 2700 user:bob
ZREVRANGE leaderboard 0 9 WITHSCORES   # top 10
ZREVRANK leaderboard user:alice        # alice's rank
```

**Delayed job queue (ZSET with timestamp score):**

```redis
# Schedule job to run in 5 min
ZADD jobs:scheduled {timestamp_in_5min} "{job_payload}"

# Worker loop
WATCH jobs:scheduled
ZRANGEBYSCORE jobs:scheduled -inf {now} LIMIT 0 1
# → if found, atomically ZREM + process
```

**Distributed lock (SET with NX + EX):**

```redis
SET lock:resource:X {uuid} NX EX 30     # acquire or fail
# ... do work ...
# Release ONLY if still owner (Lua for atomicity):
EVAL "if redis.call('GET',KEYS[1])==ARGV[1] then
        return redis.call('DEL',KEYS[1])
      else return 0 end" 1 lock:resource:X {uuid}
```

> **Redlock caveat:** fine for non-critical locks. For bank transfers, use Postgres advisory locks or Spanner — Redlock has famous disputed safety under GC pauses.

**Atomic flash-sale inventory (Lua):**

```lua
-- KEYS[1]=inventory key, ARGV[1]=quantity
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock and stock >= tonumber(ARGV[1]) then
  return redis.call('DECRBY', KEYS[1], ARGV[1])
end
return -1
```

**Streams (Kafka-lite inside Redis):**

```redis
XADD orders * user_id 123 amount 500
XGROUP CREATE orders payment-group $ MKSTREAM
XREADGROUP GROUP payment-group worker-1 COUNT 10 BLOCK 2000 STREAMS orders >
XACK orders payment-group {entry_id}   # commit
```

- Persistent (unlike pub/sub) → survives restart
- Consumer groups → load balance across workers
- At-least-once delivery with ACK
- Up to ~1M msg/sec per stream — but Kafka wins at 10M+

#### Redis Cluster internals

```
Keyspace split into 16384 hash slots:
  slot = CRC16(key) % 16384
  
Each master owns a range of slots (e.g. 0-5460)
Clients send command → cluster node:
  - If slot owned → execute
  - If not → return MOVED <slot> <ip:port> → client retries at correct node
  
Replicas: each master has 0+ replicas (replicate async)
Failover: cluster detects master down → promote replica

Hash tags: force keys to same slot
  user:{123}:profile and user:{123}:settings → both hash on "{123}"
  Required for MULTI, Lua on multiple keys, pipelining optimization
```

**Rebalancing (adding a node):**
1. New master joins
2. Move slots: `CLUSTER SETSLOT <slot> IMPORTING <node>` on target
3. For each key in slot: `MIGRATE` from old → new
4. `CLUSTER SETSLOT <slot> NODE <new_node>` to finalize
5. **Online, no downtime** — but migration throttled

#### Memory optimization (critical at TB scale)

| Optimization | What |
|--------------|------|
| **ziplist / listpack** | Small lists/hashes stored as packed array, not hash table (saves 10×+ memory for < 128 entries) |
| **intset** | Set of only integers → packed sorted array |
| **No value → use key** | `SADD users:active 123` instead of `SET active:123 "1"` |
| **Hash instead of top-level keys** | `HSET user:1 name Alice email a@b.com` beats `SET user:1:name` + `SET user:1:email` (less overhead) |
| **Short field names** | `n` instead of `name` (serious in millions of records) |
| **Compression at app layer** | Snappy/LZ4 the value before SET |
| **TTL on everything** | Avoid "forever" keys that accumulate |
| **UNLINK not DEL** | Async free for big keys (lazy freeing) |

Check: `MEMORY USAGE key` and `MEMORY STATS`.

#### Persistence — RDB vs AOF

| Option | Pro | Con |
|--------|-----|-----|
| **RDB only** (snapshots) | Smallest file, fastest restart | Lose minutes of data on crash |
| **AOF only** (log every write) | Lose <1 sec with `fsync everysec` | Larger file, slower restart |
| **Hybrid** (RDB base + AOF tail) | **Best of both — default since 7.0** | Slightly more disk |

**Fsync policies:**
- `always` — every write synced (safest, slowest, ~100 writes/sec)
- `everysec` — flush each second (**default sweet spot**, up to 1s loss)
- `no` — OS decides (fastest, data loss on crash)

#### Eviction policies (when `maxmemory` hit)

| Policy | Behavior | Use when |
|--------|----------|----------|
| `noeviction` | Reject writes with error | **Dangerous default** — crashes app |
| `allkeys-lru` | Evict least-recently-used from any key | General cache |
| `allkeys-lfu` | Evict least-frequently-used | Hot keys stay (**best cache for most**) |
| `volatile-lru` | LRU among keys with TTL | Mixed cache + persistent data |
| `volatile-ttl` | Evict earliest-expiring | Hint lifetime via TTL |
| `allkeys-random` | Random | Rarely useful |

**Rule:** always set `maxmemory` + `allkeys-lfu` for cache. Never leave `noeviction`.

#### Single-threaded gotchas

Redis's event loop runs commands **one at a time** on the main thread. **Any slow command blocks everything.**

**Blocking culprits:**
- `KEYS *` on big keyspace → O(N) full scan → use `SCAN` with cursor
- `HGETALL` on a hash with 1M fields → serialize MB of data
- `DEL` of a 1 GB key → multi-second block → use `UNLINK` (lazy free)
- `FLUSHDB` without `ASYNC`
- Lua script that loops over millions of keys
- Big pipelines with slow I/O

**Diagnostic:** `SLOWLOG GET 10` shows slowest recent commands.

#### Pipelining — the throughput multiplier

```python
# Without pipeline: 10K commands × 0.5ms RTT = 5 seconds
for i in range(10000):
    r.set(f"k:{i}", "v")

# With pipeline: 1 batch RTT + command processing
pipe = r.pipeline(transaction=False)
for i in range(10000):
    pipe.set(f"k:{i}", "v")
pipe.execute()  # 50ms total
```

**100× speedup** typical. Use for bulk loads, batched caches.

#### Redis vs Memcached (common question)

| | Redis | Memcached |
|---|-------|-----------|
| Data structures | 10+ (list, hash, zset, stream...) | String only |
| Persistence | Yes (RDB/AOF) | No |
| Replication | Yes | No |
| Cluster | Yes | Client-side only |
| Threads | Single + I/O helpers | Multi-threaded |
| Max value | 512 MB | 1 MB |
| Best for | Anything beyond simple cache | Pure in-memory LRU cache, extremely high throughput |

**Say:** "Redis unless the use case is literally cache-only with no need for atomic ops or data structures."

#### "Prove you know Redis" questions

1. *"How would you build a rate limiter?"*
   → ZSET sliding window (shown above) or token bucket with `INCR` + TTL. ZSET gives precise sliding, INCR gives fast fixed-window.
2. *"Your Redis p99 jumped from 1ms to 500ms. Debug."*
   → `SLOWLOG` — look for big `DEL`, `KEYS`, `HGETALL`, Lua loops. Check `INFO memory` for swapping. Check `latency doctor`.
3. *"Should I use Redis Streams or Kafka?"*
   → Redis Streams if < 1M msg/sec, retention measured in GB, want simplicity. Kafka if multi-consumer, replay, infinite retention, or already using Kafka.
4. *"How does Redis Cluster handle a dead master?"*
   → Replicas detect via cluster bus heartbeat → vote → elect new master → clients get MOVED on next request → update slot map.

---

### 4b. Managed Key-Value (DynamoDB)

**Amazon DynamoDB** — serverless key-value + document, partition key + optional sort key.

### How it's built

```
Partition key → hash → storage partition (LSM-based)
Sort key → range within partition
DAX cache layer for hot reads
Global tables for multi-region
```

### Advantages

- Auto-scales, no server management
- Predictable performance at any scale (if designed right)
- Single-digit ms at millions of requests
- Streams → Lambda / Kinesis integration

### Disadvantages

- **Expensive** if misdesigned (scans, wrong keys)
- No SQL joins
- 400 KB item limit
- Hot partition = throttling

### DynamoDB access pattern design

```
Table: Orders
  PK: user_id
  SK: order_id

GSI: by status
  PK: status
  SK: created_at
```

**Rule:** design tables **backwards from queries**, like Cassandra.

### Interview answer template

> "**Redis** for seat holds with 10-min TTL — sub-ms atomic grab, auto-release on timeout. **Postgres** for confirmed bookings. **DynamoDB** if we need serverless session store at massive scale with no ops."

---

## Specialized Query Engines

*Optimized for one query pattern — time, text, vectors, or geography.*

---

## 5. Time-Series Databases (InfluxDB, TimescaleDB)

**Examples:** InfluxDB, TimescaleDB, Prometheus, OpenTSDB, QuestDB, Amazon Timestream

### What it is

Optimized for **timestamped metrics** — append-only, compress old data, aggregate over time ranges.

### How it's built

```
WRITE:  batch points → in-memory buffer → compressed chunks on disk
        (delta encoding, gorilla compression)

READ:   time-range scan → downsample → aggregate (avg, p99, sum)

RETENTION: hot (7d full res) → warm (90d 1min) → cold (1y 1hr)
```

**TimescaleDB** = PostgreSQL extension (hypertables chunk by time) — best when you want SQL + time-series.

**Prometheus** = pull-based metrics, in-memory + local TSDB block files.

### Data model

```
measurement: cpu_usage
tags:   host=server1, region=us-east
fields: value=72.5, core=0
time:   2026-10-08T10:00:00Z
```

Tags are indexed (low cardinality). Fields are values.

### Advantages

| Advantage | Details |
|-----------|---------|
| Compression | 10-100x vs raw JSON in SQL |
| Fast range queries | `WHERE time > now() - 1h` |
| Built-in downsampling | Roll up 1s → 1m → 1h |
| Retention policies | Auto-delete old data |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Not for OLTP | Don't store user profiles here |
| Cardinality explosion | Too many unique tag combos → slow |
| Updates rare | Metrics are append; corrections are awkward |

### When to use

- Server / app **metrics** (CPU, latency, error rate)
- **IoT** sensor streams
- **Finance** tick data, OHLC candles
- **Monitoring** dashboards (Grafana + Prometheus/Influx)

### When NOT to use

- General application data
- Low-volume transactional records

### HLD scenarios

| System | Choice |
|--------|--------|
| **Uber trip metrics** | Time-series for GPS pings aggregation |
| **Datadog-style monitoring** | Prometheus + long-term Thanos/Mimir |
| **Stock prices** | QuestDB or TimescaleDB |
| **App analytics events** | ClickHouse (OLAP) or Influx |

### Interview answer template

> "Request latency and error rates go to **Prometheus** / **TimescaleDB** — millions of data points, queried by time range and tags. Business transactions stay in Postgres. We never mix the two."

---

### 🔬 Time-Series Deep Dive — IoT, metrics, finance

#### Why a general-purpose DB fails for time-series

Postgres on 1 billion metrics table:
- Index on `(timestamp)` becomes huge (gigabytes just for index)
- `SELECT avg(value) WHERE time > now()-1h GROUP BY device_id` → tens of seconds
- Compression ratio: ~1-2× (JSON/raw)
- Delete-after-30-days = massive DELETE + VACUUM

**Time-series DB wins because:**
1. **Compression 10-100×** via delta-of-delta on timestamps + Gorilla float encoding (XOR consecutive values; most bits identical when values close)
2. **Columnar storage per metric** — `avg(value)` reads only value column
3. **Chunking by time** — `WHERE time > X` prunes chunks whole, no scan
4. **TTL as DROP** — delete 30d of data = `DROP TABLE chunk_2026_09`, instant

#### Two time-series models (pick the right one)

| Model | Example | Best for |
|-------|---------|----------|
| **Metrics** (regular sampled, numeric) | CPU %, HTTP latency every 10s | Monitoring, dashboards — **Prometheus, InfluxDB** |
| **Events** (irregular, mixed types) | User click with props, trade tick | Analytics, audit — **ClickHouse, TimescaleDB** |

**Rule:** if the schema is "measurement + tags + value + timestamp" → metrics DB. If arbitrary JSON per row → event DB.

#### Rollup / downsampling pipeline (the signature pattern)

```
RAW:    10-second resolution, 7-day retention        → 60 GB / month
WARM:   1-minute aggregates (avg/p50/p95/p99/sum)    → 1 GB / month
                                      90-day retention
COLD:   1-hour aggregates, 2-year retention           → 60 MB / month

Total storage: ~62 GB for 2 years of 10-sec metrics × thousands of series
(vs ~15 TB raw — 240× smaller)
```

**TimescaleDB continuous aggregate — the magic:**

```sql
-- Create 1-minute rollup, auto-maintained incrementally
CREATE MATERIALIZED VIEW metrics_1min
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 minute', time) AS bucket,
  device_id,
  avg(value), max(value), min(value),
  percentile_disc(0.99) WITHIN GROUP (ORDER BY value) AS p99
FROM metrics
GROUP BY bucket, device_id;

-- Refresh policy: refresh 1-min buckets older than 1 min, up to 1 hour behind
SELECT add_continuous_aggregate_policy('metrics_1min',
  start_offset => INTERVAL '1 hour',
  end_offset   => INTERVAL '1 minute',
  schedule_interval => INTERVAL '1 minute');

-- Compression on raw chunks older than 7 days
SELECT add_compression_policy('metrics', INTERVAL '7 days');
-- Compressed chunks: 10-20× smaller, read-only, slower queries (OK since older)

-- Retention: drop raw after 7 days (rollup remains)
SELECT add_retention_policy('metrics', INTERVAL '7 days');
```

**Grafana query trick:** use `$__interval` macro — Grafana picks resolution based on dashboard time range → auto-select raw / 1min / 1hr table. Fast dashboards from seconds to years.

#### Prometheus internals (metrics, pull-based)

```
Scrape: every 15s, Prometheus GETs /metrics endpoint from each target
       → parses text format into (name, labels, value, timestamp)
       → appends to in-memory head block
       → every 2h: flush head → immutable 2h block on disk
       → every 24h: compact into larger blocks (hourly → daily)

Query: PromQL → range query → read blocks overlapping time range
```

**Why pull is good for monitoring:**
- Prometheus knows if target is up (scrape failed = alert)
- No agent config in app — app only exposes `/metrics`
- Natural service discovery (Kubernetes labels)

**Why push wins elsewhere:**
- Short-lived processes (serverless, CI jobs) — nothing to scrape
- Behind NAT, no inbound — push through firewall
- → Use **Pushgateway** or switch to InfluxDB-style push

#### PromQL critical patterns

```promql
# Rate (per-second) of a counter over 5m window
rate(http_requests_total[5m])

# p99 latency from histogram
histogram_quantile(0.99,
  sum by (le) (rate(http_duration_seconds_bucket[5m])))

# Top 10 noisy pods by CPU
topk(10, rate(container_cpu_usage_seconds_total[5m]))

# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m])) * 100

# Alert expression: error rate > 1% for 10 min
expr: ... > 0.01
for: 10m
```

**Recording rules** pre-compute expensive queries at scrape interval, write back as new series — dashboards become cheap.

#### Cardinality explosion — the #1 time-series killer

Every unique combination of label values = **one time series**. Series count = memory + storage + query cost.

| Label dimensions | Series count |
|------------------|--------------|
| 100 services × 10 pods × 20 endpoints × 5 statuses | 100K series — fine |
| + `user_id` label (1M users) | 1 billion series — **killed** |
| + `request_id` label | ∞ — immediate OOM |

**Never label with:**
- user_id, request_id, trace_id, email, UUID
- URL paths with IDs (`/orders/12345`)
- Error messages with stack traces

**Fix:** aggregate at app layer or push high-cardinality to log/trace system (Elastic, Loki, Jaeger).

#### Time-series DB comparison (deep)

| | Prometheus | InfluxDB | TimescaleDB | ClickHouse | VictoriaMetrics |
|---|-----------|----------|-------------|------------|------------------|
| Model | Pull | Push | Push (SQL) | Push (SQL) | Pull/push |
| Query | PromQL | Flux/InfluxQL | **SQL** | **SQL** | PromQL+MetricsQL |
| Compression | ~1-2 bytes/sample | ~2-3 | Columnar ~10× | Best — columnar | ~0.5 bytes/sample |
| Scale | Single node up to ~10M samples/sec; need Thanos/Cortex/Mimir for HA | Horizontal scaling via clustering | Postgres scale + hypertables | Horizontal, massive | Single-node to 10M+ samples/sec |
| HA / long-term | Thanos, Cortex, Mimir, VictoriaMetrics | InfluxDB Cloud or OSS cluster | Postgres streaming replication | Cluster | Native cluster |
| Best for | Infra monitoring, Kubernetes | IoT, apps, ops | Mixed OLTP + metrics (join with Postgres data) | Analytics on metrics + events | Massive-scale metrics replacement for Prometheus |

#### Long-term storage architecture (interview-worthy)

```
Prometheus (local, 15d retention, HA pair per cluster)
     ↓ remote write every 15s
Thanos Receiver / Cortex / Mimir / VictoriaMetrics
     ↓ compact + downsample + dedup
Object storage (S3 / GCS)
     ↓ query via
Thanos Querier / Grafana Mimir Query → PromQL from Grafana
```

**Why this pattern:** local Prometheus stays small/fast. Remote system handles multi-cluster aggregation, downsampling, infinite retention on cheap S3.

#### Industry choices

| System | Stack |
|--------|-------|
| **Datadog** | Custom time-series DB (proprietary) + Druid for analytics |
| **Netflix Atlas** | In-memory TSDB for metrics; S3 for cold |
| **Uber M3** | M3DB (open source) — distributed Prometheus-compatible |
| **Grafana Cloud** | Grafana Mimir — Prometheus long-term at scale |
| **Shopify** | Prometheus → Thanos → S3 |

#### "Prove you know time-series" questions

1. *"How do you store 1 million IoT devices sampling every second for 5 years?"*
   → 1M × 86400 × 365 × 5 = 157 trillion points. Time-series DB with rollups: raw 7d, 1min 90d, 1hr forever. Partition by `(device_bucket, time_bucket)` to avoid hot writes.
2. *"Why can't I use `user_id` as a Prometheus label?"*
   → Cardinality explosion — 1M users = 1M series per metric × every unique combination. Store in logs/traces instead.
3. *"Grafana dashboards are slow."*
   → Not querying rollups. Use recording rules or continuous aggregates; use `$__interval` to pick resolution.
4. *"Prometheus vs InfluxDB?"*
   → Prometheus for infra/K8s monitoring (pull + PromQL + service discovery). InfluxDB for IoT and app events (push + SQL-ish). Both can work; team familiarity matters.

---

## 6. Graph Databases (Neo4j)

**Examples:** Neo4j, Amazon Neptune, JanusGraph, ArangoDB (multi-model)

### What it is

Data as **nodes** (entities) and **edges** (relationships). Optimized for **traversal** — "friends of friends", shortest path, recommendations.

### How it's built

```
Native graph storage:
  Node records + relationship records (doubly linked)
  → O(1) to follow an edge (no expensive join)

Index-free adjacency:
  Each node points directly to its relationships
  vs SQL: join tables at every hop
```

### Data model

```
(User {id: 1, name: "Alice"})
  -[:FOLLOWS {since: 2020}]->
(User {id: 2, name: "Bob"})
  -[:FOLLOWS]->
(User {id: 3, name: "Carol"})

Query: "friends of friends of Alice, excluding already-followed"
  → 2-hop traversal in milliseconds
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Multi-hop queries | 3-6 hops painful in SQL, natural in graph |
| Relationship-first | Social, fraud, knowledge graphs |
| Flexible schema | Add edge types without migration hell |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Not for bulk analytics | Billions of nodes OK; complex aggregations → warehouse |
| Sharding is hard | Graph partitioning breaks locality |
| Overkill for simple CRUD | Don't use for user login table |

### When to use

- **Social networks:** follow suggestions, mutual friends
- **Fraud detection:** account → device → IP → other accounts
- **Knowledge graphs:** RAG entity relationships
- **Network topology:** dependencies, blast radius
- **Recommendation:** "users who bought X also bought Y" (with graph algorithms)

### When NOT to use

- Simple parent-child (use SQL foreign key)
- Time-series metrics
- Full-text document search

### HLD scenarios

| System | Graph use |
|--------|-----------|
| **LinkedIn** | Connections, "people you may know" (also uses other DBs) |
| **PayPal fraud** | Transaction graph traversal |
| **Airport routes** | Shortest path with constraints |

### Interview answer template

> "Fraud check traverses **device → IP → accounts** in 3 hops — **Neo4j** or in-memory graph for real-time. User profile and transactions still in SQL. Graph is a specialized read model, not the system of record."

---

## 7. Vector Databases (Pinecone, pgvector)

**Examples:** Pinecone, Weaviate, Milvus, Qdrant, pgvector (Postgres extension), Chroma

### What it is

Stores **embeddings** (high-dimensional vectors) and finds **nearest neighbors** by similarity (cosine, dot product, L2).

### How it's built

```
Embedding model → vector [0.12, -0.34, ..., 0.89]  (768 or 1536 dims)

Index structures:
  HNSW (Hierarchical Navigable Small World) — fast approximate NN
  IVF (Inverted File) — cluster then search
  LSH (Locality Sensitive Hashing) — older approach

Query: "find top-K vectors closest to query vector"
  → ANN (Approximate Nearest Neighbor) — trade accuracy for speed
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Semantic search | "refund policy" matches "money back guarantee" |
| RAG pipelines | Retrieve relevant docs for LLM context |
| Similarity | images, audio, recommendations |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Approximate | Not 100% recall; tune ef_search |
| Needs embedding pipeline | Model choice affects quality |
| Not a general DB | Store metadata elsewhere |
| Re-indexing cost | Model change → re-embed everything |

### When to use

- **RAG / AI apps:** chatbots over company docs
- **Semantic product search**
- **Image similarity** (duplicates, moderation)
- **Recommendation** by embedding similarity

### When NOT to use

- Exact keyword match (→ Elasticsearch)
- Transactional data
- Primary data store

### HLD scenarios (AI-native)

```
User query → embed → vector DB (top 20 chunks)
                  → metadata filter (tenant_id, doc_type)
                  → rerank → LLM prompt
Metadata + ACL: Postgres
Original docs: S3
```

### Interview answer template

> "Document chunks embedded and stored in **pgvector** or **Pinecone** for semantic retrieval. Postgres holds doc metadata, permissions, and audit log. Vector DB is the index, not source of truth."

---

## 8. Search / Full-Text Engines (Elasticsearch)

**Examples:** Elasticsearch, OpenSearch, Solr, Meilisearch, Typesense

### What it is

**Inverted index** for full-text search, filtering, aggregations. Not a primary database — a **search replica** of your data.

### How it's built

```
Document → analyzer (tokenize, stem, lowercase)
        → inverted index:
            "inception" → [doc1, doc5, doc99]
            "movie"     → [doc1, doc2, ...]

Query → Boolean + TF-IDF / BM25 scoring → ranked results

Distributed: shards + replicas per index
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Full-text search | Prefix, fuzzy, phrase, synonyms |
| Faceted search | Filter by genre, price range, rating |
| Aggregations | "count by category" for analytics UI |
| Near real-time | Index within seconds of write |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Not ACID | Eventual consistency; not source of truth |
| Expensive | JVM heap, many shards = ops burden |
| Reindex pain | Mapping changes need rebuild |
| Split-brain / cluster issues | Needs expertise |

### When to use

- **Product / movie search** with filters
- **Log analytics** (ELK stack)
- **Autocomplete**
- Any **read model** where SQL `LIKE '%foo%'` fails

### When NOT to use

- Primary storage
- Strong consistency requirements
- Simple PK lookups (overkill)

### HLD scenarios

| System | Elasticsearch role |
|--------|---------------------|
| **Netflix** | Search titles, actors, genres |
| **E-commerce** | Product search + facets |
| **Uber** | Trip / driver search |

### Interview answer template

> "Movies written to **Postgres**; changes streamed via Kafka to **Elasticsearch** for search and autocomplete. Search index can rebuild from Postgres — it's a derived view."

---

## 9. OLAP / Data Warehouses (BigQuery, Snowflake)

**Examples:** Snowflake, BigQuery, Redshift, ClickHouse, Apache Druid, Pinot

### What it is

**Columnar storage** for **analytical queries** over billions of rows — aggregations, reports, BI dashboards. **Not** for OLTP.

### How it's built

```
ROW-ORIENTED (OLTP):     [id|name|city|salary]  ← one row together
COLUMN-ORIENTED (OLAP):  [id,id,id...] [name,name...] [salary,salary...]
                         ↑ read only salary column = fast + compressible

Query: SELECT region, SUM(revenue) GROUP BY region
  → scan only revenue + region columns
  → SIMD vectorized execution
  → distributed across nodes
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Fast aggregations | SUM, COUNT, GROUP BY over huge data |
| Compression | Same-type columns compress 10x+ |
| Separation from OLTP | Analytics don't slow production DB |
| Historical data | Years of events cheaply stored |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| High latency per query | Seconds, not milliseconds |
| Not for point updates | Batch loads, streaming inserts |
| Stale | Minutes behind real-time (usually) |
| Cost at scale | Scan-heavy queries expensive |

### When to use

- Business intelligence dashboards
- "How many bookings per city last quarter?"
- Data science / ML feature pipelines
- Log analysis at petabyte scale

### OLAP options compared

| | ClickHouse | BigQuery | Snowflake |
|---|------------|----------|-----------|
| Ops | Self-host or cloud | Serverless | Managed |
| Latency | Sub-second | Seconds | Seconds |
| Best for | Real-time analytics | GCP ecosystem | Enterprise BI |
| SQL | Yes | Yes | Yes |

### Interview answer template

> "Production writes go to **Postgres**. Events stream to **Kafka → ClickHouse/BigQuery** for analytics. CEO dashboard queries never touch the OLTP database."

---

## 10. NewSQL (Spanner, CockroachDB)

**Examples:** Google Spanner, CockroachDB, TiDB, YugabyteDB

### What it is

**SQL + horizontal scale + strong consistency** — tries to fix "you can't have both SQL and scale."

### How it's built (Spanner example)

```
TrueTime API (GPS + atomic clocks)
  → globally synchronized timestamps
  → external consistency: transactions ordered globally

Paxos replication per shard
  → quorum writes across datacenters
  → survives datacenter failure
```

CockroachDB uses **Raft** + **serializable isolation** without special hardware.

### Advantages

| Advantage | Details |
|-----------|---------|
| SQL you know | Migrations, joins, ACID |
| Horizontal scale | Sharded by design |
| Multi-region strong consistency | Global bank accounts |
| No custom sharding logic | DB handles it |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Latency | Cross-region tx = slow (physics) |
| Cost | Spanner is expensive |
| Maturity | Fewer tools than Postgres |
| Throughput ceiling | vs Cassandra for pure writes |

### When to use

- Global app needing **strong consistency** + SQL
- Financial ledger across regions
- Replacing self-managed sharded MySQL

### Interview answer template

> "If we need **global ACID** without building our own sharding, **CockroachDB/Spanner**. For most startups, **Postgres + read replicas** is enough until proven otherwise."

---

## 11. Embedded / Edge (SQLite)

### What it is

Single-file SQL database in-process. No server. Zero config.

### When to use

- Mobile apps (iOS, Android)
- Browser (WASM SQLite)
- Edge caching with SQL
- Tests and local dev
- Low-QPS embedded devices

### When NOT to use

- Multi-writer server backend (one writer at a time)
- High concurrent writes from many clients

---

## 12. Ledger / Immutable Stores

**Examples:** Amazon QLDB, immudb, event sourcing with Kafka

### What it is

**Append-only, cryptographically verifiable** history. You never UPDATE — only INSERT new version.

### When to use

- Audit trail (who changed what when)
- Financial ledger
- Compliance (healthcare, finance)
- Event sourcing as primary pattern

### Interview angle

> "Booking state is current view in Postgres; **immutable event log** in Kafka for audit and replay."

---

## 13. Message / Log Stores (Kafka as Storage)

**Apache Kafka** is not a database, but in HLD interviews it appears as **durable ordered log storage**.

### When Kafka is the right "database"

- Event sourcing (source of truth = log)
- Stream processing (Flink, ksqlDB)
- Decouple producers/consumers
- Replay history

### Pattern

```
Service A → Kafka topic (retained 7d or forever)
              → Flink → Cassandra (materialized view)
              → ClickHouse (analytics)
              → Elasticsearch (search)
```

**Say:** "Kafka is the **nervous system**, not the **memory**. Materialized views in proper DBs serve queries."

---

## 14. Multi-Model Databases (Cosmos DB, ArangoDB)

**Examples:** Azure Cosmos DB, ArangoDB, Fauna, OrientDB, Amazon DocumentDB (document-only subset)

### What it is

One database engine exposing **multiple data models** — document, key-value, graph, column-family — under one API and billing account.

### How it's built (Cosmos DB example)

```
Request → gateway → partition (replicated via Paxos-like quorum)
                  → storage layout depends on API chosen:
                      SQL API    → JSON documents, indexed
                      Cassandra  → wide-column compatible
                      MongoDB    → wire protocol compatible
                      Gremlin    → graph traversal

Global distribution: multi-region writes with session/strong consistency tiers
```

### Advantages

| Advantage | Details |
|-----------|---------|
| One vendor, many models | Start document, add graph later without new infra |
| Global distribution | Built-in multi-region replication |
| Elastic scale | Auto-scale throughput (RU/s in Cosmos) |
| SLA-backed latency | P99 guarantees on managed offerings |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Cost | Cosmos RU pricing surprises at scale |
| Jack of all trades | Not best-in-class vs specialized DB per model |
| Vendor lock-in | Proprietary APIs |
| Query limits | Cross-partition queries expensive |

### When to use

- Enterprise on Azure needing document + global distribution
- Prototype where model may shift (document → graph)
- Fauna for global ACID + document + relational queries

### When NOT to use

- Best performance per workload (dedicated Cassandra beats Cosmos Cassandra API)
- Tight budget startup (Postgres + Redis cheaper)
- Deep graph analytics (dedicated Neo4j)

### Interview answer

> "For MVP I'd use **Postgres + Redis**. If we're Azure-native, multi-region, and model is uncertain, **Cosmos DB** is defensible — but I'd still split search to Elasticsearch and analytics to ClickHouse."

---

## 15. Real-Time Sync Databases (Firebase, CouchDB)

**Examples:** Firebase Realtime Database, Firestore, CouchDB, PouchDB, Supabase Realtime, Electric SQL

### What it is

Databases designed for **live sync** between server and clients (mobile, web, offline-first).

### How it's built

```
Client subscribes to document/path
  → WebSocket or long-poll push on change
  → local replica (PouchDB on device) syncs when online
  → conflict resolution: last-write-wins or custom merge
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Offline-first | Mobile apps work without network |
| Real-time UI | Chat, collaborative docs update instantly |
| Low backend code | SDK handles sync |
| Security rules | Declarative per-document ACL (Firestore) |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Query limits | Firestore: no joins; compound index explosion |
| Cost at scale | Per-read/write pricing |
| Not for server OLTP | Complex transactions weak |
| Data modeling rigidity | Must design for sync, not SQL normalization |

### When to use

- Mobile chat, live dashboards, collaborative editing
- IoT device shadow state
- Rapid MVP with real-time needs

### When NOT to use

- Financial transactions, inventory (use SQL)
- Complex reporting (sync to warehouse)
- High-write fan-out (millions of subscribers on one doc)

### HLD scenario

| Component | Choice |
|-----------|--------|
| Chat messages (live) | Firestore / Firebase |
| User billing | Postgres |
| Message search | Elasticsearch |

---

## 16. Spatial / GIS Databases (PostGIS)

**Examples:** PostGIS (Postgres extension), MongoDB geospatial indexes, Elasticsearch geo, Redis GEO, Oracle Spatial

### What it is

Stores and queries **geographic data** — points, polygons, routes — with spatial indexes and operations.

### How it's built

```
Geometries stored as WKB/WKT (Well-Known Binary/Text)
Spatial index: R-Tree or GiST (PostGIS)
Queries: ST_DWithin, ST_Contains, ST_Intersects
Redis GEO: geohash + sorted set for radius search
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Radius search | "Drivers within 5 km" |
| Polygon ops | "Is point inside delivery zone?" |
| Route distance | PostGIS + pgRouting |
| Industry standard | PostGIS is the default answer |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Index tuning | Complex geometries need care |
| Not for live tracking alone | Pair with Redis GEO for sub-second updates |
| CRS complexity | Coordinate systems confuse teams |

### When to use

- Uber/Lyft driver matching, delivery zones
- Store locator ("nearest 10 branches")
- Geofencing alerts
- Maps, logistics, real estate

### Interview answer

> "Live driver positions in **Redis GEO** (updated every second). Historical routes and geofence polygons in **PostGIS**. Analytics in ClickHouse."

---

### 🔬 Spatial / Geo Deep Dive — Uber, DoorDash, maps

#### The three spatial problems you'll be asked

1. **k-nearest neighbors (kNN)** — "5 closest drivers to pickup point"
2. **Geofence containment** — "Is this GPS inside delivery zone?"
3. **Routing / distance** — "ETA from A to B via road network"

Each has a different index structure.

#### Spatial index structures (name them)

| Structure | How | Best for |
|-----------|-----|----------|
| **R-Tree** | Hierarchical bounding rectangles | Polygon containment, overlap (PostGIS, SQLite R*Tree) |
| **Geohash** | Encode (lat, lon) → base32 string; prefix = same region | kNN via Redis GEO, DynamoDB; "nearby" by prefix |
| **S2 cells** (Google) | Hilbert curve on sphere → 64-bit cell IDs; hierarchy up to 30 levels | Google Maps, planet-scale, uniform cells |
| **H3** (Uber) | Hexagonal grid on sphere, 16 resolutions | Uber surge pricing, aggregation by hex cell |
| **Quadtree** | Recursively subdivide 2D space into 4 | Game maps, moderate size |
| **GiST** (PostGIS) | Generalized search tree, supports R-tree-like ops | Any geometry type in Postgres |
| **BRIN** (Postgres) | Block range on spatial sort | Append-only sorted geo data (massive) |

#### Why Uber built H3 (interview-ready story)

- Rectangular grids (geohash) have **neighbor distance variance** — the cell to the NE is farther than the cell to the E.
- Hexagons have **uniform distance to all 6 neighbors** → cleaner "nearby" queries.
- H3 enables fluid aggregation: hex at resolution 9 = ~0.1 km²; roll up to resolution 7 = ~5 km² by truncating the ID.
- Open source — Uber publishes H3 bindings for every language.

#### PostGIS cheat sheet

```sql
CREATE EXTENSION postgis;

CREATE TABLE drivers (
  id UUID PRIMARY KEY,
  location GEOGRAPHY(POINT, 4326)   -- WGS84 lat/lon
);
CREATE INDEX ON drivers USING GIST(location);

-- Insert
INSERT INTO drivers (id, location)
VALUES ('a1', ST_MakePoint(-122.4194, 37.7749));   -- SF

-- Find 10 closest drivers within 5 km
SELECT id, ST_Distance(location, ST_MakePoint(-122.42, 37.77)::geography) AS meters
FROM drivers
WHERE ST_DWithin(location, ST_MakePoint(-122.42, 37.77)::geography, 5000)
ORDER BY location <-> ST_MakePoint(-122.42, 37.77)::geography   -- KNN operator
LIMIT 10;

-- Geofence: is a point inside a polygon?
SELECT zone_id FROM delivery_zones
WHERE ST_Contains(area, ST_MakePoint(-122.42, 37.77));

-- Create a 500 m buffer around a route
SELECT ST_Buffer(route::geography, 500) FROM delivery_routes WHERE id = 'r1';
```

**Geography vs Geometry:**
- `GEOGRAPHY` — spherical calculations (slower but accurate for large distances)
- `GEOMETRY` — planar (faster, needs projection, breaks over long distances)
- **Rule:** use `GEOGRAPHY` for lat/lon unless you're in a projected coordinate system.

#### Redis GEO (sub-millisecond "nearest" lookups)

```redis
GEOADD drivers -122.42 37.77 "driver:a1"
GEOADD drivers -122.41 37.78 "driver:a2"

# 10 closest within 5 km, with coords + distance
GEOSEARCH drivers FROMLONLAT -122.42 37.77
  BYRADIUS 5 km ASC COUNT 10 WITHCOORD WITHDIST

# Driver updates position every 5 sec → GEOADD overwrites
```

**How it works internally:** Redis GEO is a thin layer over sorted set — key is driver_id, score is 52-bit interleaved geohash. ZRANGE + bbox filter + haversine.

**Scale:** millions of entities, 100K+ ops/sec on single node.

#### Uber dispatch architecture (deep)

```
Driver GPS → every 4 sec → Redis GEO (keyed by city) 
                        → H3 cell indexing (bucketed by hex)

Rider request:
  1. Convert pickup → H3 cell at resolution 9 (~0.1 km²)
  2. Query drivers in cell + ring of 2 neighboring cells
  3. Filter by: online, matching tier, not already assigned
  4. Rank by ETA (not just distance) using road graph
  5. Push offer to top driver via WebSocket
  
Historical GPS → Cassandra (append-only, partition by driver_day)
Trip metadata → Postgres (ACID)
Surge pricing → ClickHouse aggregates H3 cells × time
Routing → OSRM / Valhalla with pre-computed graph
```

#### The 5 geo use cases + what to use

| Use case | Pattern | DB choice |
|----------|---------|-----------|
| Live location tracking | GPS updates every N sec | **Redis GEO** (ephemeral, overwrite) |
| Nearest neighbors (kNN) | "5 closest X to point Y" | Redis GEO, PostGIS KNN, DynamoDB with geohash |
| Geofence containment | "Is point in polygon?" | **PostGIS** (ST_Contains) |
| Routing / ETA | Shortest path through road graph | **OSRM, Valhalla, Google Maps API** (not a DB) |
| Spatial analytics | "Rides per hex per hour" | **H3 + ClickHouse / BigQuery** |
| Historical trajectory | "Where was driver X on day Y?" | **Cassandra** append-only or **TimescaleDB** |

#### Common anti-patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| B-tree index on `(lat, lon)` | Can't do range on both | GiST / R-tree spatial index |
| Storing lat/lon as two FLOAT columns | No spatial ops | `GEOGRAPHY(POINT)` |
| Querying "nearby" by lat/lon bbox | Earth is curved; wrong near poles | `ST_DWithin` with geography |
| Polygon with 100K points | Slow containment check | Simplify (`ST_SimplifyPreserveTopology`) |
| No spatial index | Full table scan on every query | `CREATE INDEX USING GIST(location)` |

#### "Prove you know geo" questions

1. *"How does Uber match riders to drivers in <1 second with 10M drivers worldwide?"*
   → City-sharded Redis GEO for live positions + H3 cell lookup + ring expansion + ETA ranking via road graph. Not single global index — too slow.
2. *"Why not just use `WHERE lat BETWEEN ... AND lon BETWEEN ...` on Postgres?"*
   → Bounding box ignores curvature; no index can do range on two columns together; distance ≠ bbox size at different latitudes. GiST spatial index is purpose-built.
3. *"How would you power 'show hotels in map viewport' as user pans?"*
   → Elasticsearch geo_shape or PostGIS with GiST, filter by bbox + sort by rating. Debounce the pan event. Cache responses by rounded bbox.
4. *"H3 vs Geohash?"*
   → Geohash is rectangular → distance to neighbors varies. H3 hexagonal → equidistant neighbors, better for aggregation and ring queries. Uber's choice.

---

## 17. HTAP (Hybrid Transactional + Analytical)

**Examples:** TiDB, SingleStore (MemSQL), Google AlloyDB, Oracle HeatWave, ClickHouse with recent OLTP features

### What it is

**One system** handles both OLTP (row-level writes) and OLAP (columnar analytics) without ETL to a separate warehouse.

### How it's built (TiDB example)

```
TiDB (SQL layer) → TiKV (distributed row store, OLTP)
                → TiFlash (columnar replica, OLAP)
                → Raft replication across nodes

Query optimizer routes:
  point lookup → row store
  aggregation  → columnar replica (async sync)
```

### Advantages

| Advantage | Details |
|-----------|---------|
| No ETL lag | Analytics on near-real-time data |
| One SQL dialect | Simpler than Postgres + BigQuery |
| Operational simplicity | Fewer moving parts |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Neither best OLTP nor best OLAP | vs dedicated Postgres + ClickHouse |
| Resource contention | Heavy analytics can slow writes |
| Younger ecosystem | vs mature warehouse tools |

### When to use

- Mid-size company wanting real-time dashboards without Kafka pipeline
- Replacing MySQL + nightly ETL
- TiDB as drop-in MySQL scale-out

### When NOT to use

- Petabyte analytics (dedicated warehouse cheaper)
- Extreme write scale (Cassandra still wins)
- Simple app (Postgres enough)

---

## 18. Data Lake & Lakehouse (S3, Delta, Iceberg)

**Examples:** Amazon S3 + Athena, Databricks + Delta Lake, Apache Iceberg, Apache Hudi, Snowflake external tables

### What it is

**Data lake:** cheap object storage (S3) holding raw files (Parquet, JSON, CSV).
**Lakehouse:** table format layer (Delta/Iceberg) adding ACID, schema evolution, time travel on top of the lake.

### How it's built

```
Ingest → S3 (Parquet files, partitioned by date/region)
       → Iceberg/Delta metadata layer (manifest files, snapshots)
       → Query engine: Spark, Trino, Athena, Databricks SQL
       → optional: CDC from Postgres → Debezium → Kafka → S3
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Cheap storage | Pennies per GB vs warehouse |
| Schema-on-read | Store everything, structure later |
| Time travel | Delta: query data as of yesterday |
| Decoupled compute | Spin up Spark only when needed |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Not OLTP | No single-row updates for apps |
| Latency | Seconds to minutes per query |
| Ops complexity | Spark, partitioning, small file problem |
| Data quality | "Swamp" without governance |

### When to use

- ML training data at petabyte scale
- Log archive, clickstream history
- Data science sandbox
- Compliance archive (cheap retention)

### Lake vs Warehouse vs Lakehouse

| | Data Lake | Data Warehouse | Lakehouse |
|---|-----------|----------------|-----------|
| Storage | S3 raw files | Proprietary columnar | S3 + table format |
| Schema | On read | On write | Evolvable |
| OLTP | No | No | No |
| Best for | ML, archive | BI, SQL analysts | Unified analytics + ML |

### Interview answer

> "App data in **Postgres**. All events land in **S3 via Kafka** as Parquet. **Iceberg** gives us ACID batches. **Trino/Athena** for ad-hoc SQL. **Snowflake** only if analysts need managed BI with SLA."

---

## 19. Federated Query Engines (Presto, Trino)

**Examples:** Trino (formerly PrestoSQL), Apache Drill, Dremio, AWS Athena

### What it is

**Query engine only** — no storage. Runs SQL across **multiple heterogeneous sources** in one query.

### How it's built

```
SQL query → coordinator parses plan
         → workers read from: S3 Parquet + Postgres + MySQL + Cassandra
         → pushdown predicates where connector supports it
         → aggregate in memory / spill to disk
         → return unified result
```

### Advantages

| Advantage | Details |
|-----------|---------|
| No data movement | Query in place |
| One SQL interface | Join S3 logs with Postgres users |
| Interactive | Faster than batch Spark for ad-hoc |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Not for app serving | Too slow for user-facing APIs |
| Cross-source joins expensive | Data locality matters |
| No writes (mostly) | Read-only analytics |

### When to use

- "Join S3 click logs with Postgres user table"
- Data mesh — query without copying everything to warehouse
- Athena for serverless S3 SQL

---

## 20. Event Sourcing Databases (EventStoreDB)

**Examples:** EventStoreDB, Marten (.NET), Axon Server, Kafka + ksqlDB materialized views

### What it is

**Source of truth = stream of events**, not current state. Current state is a **projection** rebuilt by replaying events.

### How it's built

```
Command → validate → append event to stream (per aggregate ID)
                  → event: BookingCreated, SeatHeld, PaymentReceived
Projections (async):
  → relational view for queries
  → cache update
  → analytics pipeline

Snapshotting: periodic state snapshot to avoid full replay
```

### Advantages

| Advantage | Details |
|-----------|---------|
| Full audit history | Every state change recorded |
| Temporal queries | "What did inventory look like at 3pm?" |
| Replay / rebuild | Fix bug in projection → replay events |
| Event-driven natural fit | CQRS, microservices |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Complexity | Team must understand event modeling |
| Query current state | Needs projections (extra infra) |
| Schema evolution | Event versioning painful if careless |
| Storage growth | Never delete events |

### When to use

- Banking ledger, audit-heavy domains
- Complex workflows with history requirements
- Systems already on Kafka event-driven architecture

### When NOT to use

- Simple CRUD app
- Team has no event sourcing experience

---

## 21. In-Memory Databases (SAP HANA)

**Examples:** SAP HANA, SingleStore rowstore, Oracle TimesTen, VoltDB

### What it is

Primary data stored in **RAM** for microsecond-millisecond latency. Durability via periodic snapshots + WAL.

### Advantages

| Advantage | Details |
|-----------|---------|
| Extreme speed | Trading, telco billing |
| HTAP in one box | HANA: row + column in memory |
| Predictable latency | No disk seek |

### Disadvantages

| Disadvantage | Details |
|--------------|---------|
| Cost | RAM is expensive |
| Dataset must fit | Or tiered storage (HANA extension) |
| Recovery time | Reload from snapshot after crash |

### When to use

- High-frequency trading, real-time billing
- SAP ERP landscape (HANA)
- When Redis is too simple but disk DB too slow

### Redis vs In-Memory DB

| | Redis | SAP HANA / VoltDB |
|---|-------|-------------------|
| Model | Key-value + structures | Full SQL ACID |
| Durability | Optional | Designed durable |
| Use | Cache, locks, sessions | Primary transactional store |

---

## 🔬 Real-Time Analytics Databases (Druid, Pinot, ClickHouse, Materialize)

This is the **"sub-second analytics on fresh data"** category. OLAP warehouses (Snowflake, BigQuery) answer in seconds; real-time analytics answers in **milliseconds** on **data from seconds ago**.

### The problem they solve

Classic split:
- **OLTP (Postgres)** — row reads/writes, no analytics
- **OLAP (Snowflake, BigQuery)** — great analytics but **minutes-to-hours stale**, **seconds per query**

**Real-time analytics gap:** user-facing dashboards and in-app analytics need:
- Fresh data (< 10 seconds old)
- Low-latency queries (< 1 second p99)
- High QPS (hundreds to thousands of concurrent dashboard queries)
- Aggregations over billions of rows

**Examples:** LinkedIn "Who viewed your profile", Uber real-time surge pricing dashboard, Netflix A/B test results, Airbnb host dashboard, user-facing analytics in SaaS products (Mixpanel, Amplitude, Posthog).

### The main players

| | Druid | Pinot | ClickHouse | Materialize | RisingWave |
|---|-------|-------|------------|-------------|------------|
| Origin | Metamarkets → Apache | LinkedIn → Apache | Yandex → open | MIT → commercial | commercial |
| Model | Columnar + inverted indexes | Columnar + star-tree index | Columnar MergeTree | **Streaming materialized views** | **Streaming SQL** |
| Ingest | Streaming (Kafka) + batch | Streaming + batch | Batch-optimized, streaming OK | **Pull from Kafka/Debezium** | Pull from streams |
| Latency | ms–seconds | **ms (fastest)** | sub-second | sub-second (continuously updated views) | similar |
| QPS | 100s | **1000s** | 100s | depends on view count | similar |
| SQL | SQL | SQL (limited) | **Full SQL + joins** | **Standard Postgres SQL** | Postgres SQL |
| Updates | Immutable segments | Immutable segments | Mutable (ReplacingMergeTree) | Streaming view auto-updates | Same |
| Best for | Druid dashboards (time + dim slicing) | LinkedIn-style low-latency | Analytics at any scale, flexible | Keep a materialized view always fresh | Same |

### How it works — Druid example

```
Kafka topic (user events, 100K/sec)
     ↓
Druid real-time ingestion:
  → middleManager builds in-memory indexes
  → every 1-10 min: hand off to historical nodes as immutable segment on S3
  → broker routes queries, scatters to historical + realtime nodes

Query path:
  broker → scatter to data nodes → each node pre-aggregates partial → merge
       → return in milliseconds
```

**Internal tricks:**
- Columnar: scan only columns needed
- Bitmap inverted indexes on dimension columns (fast WHERE filters)
- Pre-aggregation at ingest (optional)
- Approximate algorithms: HLL for count-distinct, DataSketches for quantiles

### How it works — ClickHouse (fastest OLAP engine most teams can run)

```
MergeTree engine:
  INSERT → write to in-memory part → flush to disk as sorted file (part)
         → background: merge parts (like LSM compaction)
         
Queries:
  → vectorized execution (SIMD on columns)
  → parallelism per core per shard
  → aggregates billions of rows/sec per node
```

**ClickHouse insert pattern (critical):**
- Never insert single rows → one small part per row = disaster
- **Batch inserts** every 1-10 sec, 10K-100K rows per batch
- Use **async_insert** or buffer in Kafka → consumer batches

**ClickHouse MergeTree variants:**
- `MergeTree` — basic append-only
- `ReplacingMergeTree` — dedup by sort key during merge
- `AggregatingMergeTree` — rollup during merge (sum, avg, HLL state)
- `SummingMergeTree` — sum numeric columns on merge
- `CollapsingMergeTree` — mark rows as deleted via `sign` column

**ClickHouse materialized views:**

```sql
-- Source table: raw events
CREATE TABLE events (ts DateTime, user_id UInt64, action String, value Float64)
ENGINE = MergeTree() PARTITION BY toYYYYMM(ts) ORDER BY (user_id, ts);

-- Materialized view: pre-aggregated every insert
CREATE MATERIALIZED VIEW events_hourly
ENGINE = SummingMergeTree() PARTITION BY toYYYYMM(hour) ORDER BY (hour, action)
AS SELECT toStartOfHour(ts) AS hour, action, count() AS c, sum(value) AS total
   FROM events GROUP BY hour, action;

-- Dashboard queries hit events_hourly (tiny, fast) not events
```

### How Materialize / RisingWave differ (streaming SQL)

**Druid/Pinot/ClickHouse:** store data, run query when asked.
**Materialize:** write SQL once, result **continuously updates** as new rows arrive via CDC/Kafka.

```sql
-- Postgres → Debezium → Kafka → Materialize
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT date_trunc('day', ts), sum(amount)
FROM orders
WHERE status = 'paid'
GROUP BY 1;

-- Dashboards SELECT from this view → always current, sub-ms
-- Materialize maintains it incrementally using differential dataflow
```

**Use when:** dashboard query is well-known, must be fresh; worth the engine complexity vs batch warehouse.

### Industry choices

| Company | Choice | Why |
|---------|--------|-----|
| **LinkedIn** | Built **Pinot** | Member-facing analytics, 1000s of concurrent queries, p99 < 100ms |
| **Uber** | **Pinot + Druid** | Real-time dashboards, surge pricing |
| **Netflix** | **Druid** | Playback metrics, infrastructure dashboards |
| **Airbnb** | Druid | Host dashboards |
| **Cloudflare** | **ClickHouse** | Trillions of log rows, analytics API |
| **Yandex** | ClickHouse (built it) | Web analytics at Google-scale |
| **Mixpanel / Amplitude / Posthog** | Custom + ClickHouse | Product analytics as a service |

### When to pick which

| Need | Pick |
|------|------|
| Analytics dashboard, time + dimensions, low ops | **Druid** |
| User-facing analytics inside your product, sub-100ms, 1000s QPS | **Pinot** |
| General-purpose OLAP, logs, flexible SQL + joins, you can run it | **ClickHouse** |
| Continuously fresh materialized view of complex SQL | **Materialize / RisingWave** |
| CEO dashboards, warehouse ops, nightly batch OK | **Snowflake / BigQuery** |
| Metrics-only time-series | **Prometheus / InfluxDB** (not these) |

### "Prove you know real-time analytics" questions

1. *"User-facing analytics page shows views per hour. 10K companies. Must be fresh and fast."*
   → ClickHouse or Pinot. Columnar + pre-aggregated materialized view on `(company_id, hour)`. Postgres can't do this at scale.
2. *"Why not just query Postgres with a materialized view refreshed every minute?"*
   → Works until data > few GB per view, concurrent queries > tens, or query latency > seconds. Columnar engines are 10-1000× faster for aggregations.
3. *"Druid vs ClickHouse?"*
   → Druid = turnkey (segment management, scatter-gather, built for streaming time-series). ClickHouse = more flexible SQL, better joins, needs more ops. Both scale enormously.
4. *"How do you keep the real-time DB fresh from Postgres?"*
   → Postgres → **Debezium** → Kafka → ClickHouse/Pinot/Druid Kafka ingest. Or Materialize subscribing to Kafka directly.

---

## 🔬 Big Data / Spark / Hadoop — The Batch-Processing Universe

Not a database per se — a **compute framework** that reads from and writes to many databases. Shows up in HLD when problem involves:
- Terabytes to petabytes of historical data
- Nightly ETL / ELT jobs
- ML training data preparation
- Ad-hoc queries over data lake
- Processing data that doesn't fit in any one database

### The ecosystem

```
STORAGE LAYER        COMPUTE LAYER       SCHEDULING/CATALOG
---------------      --------------      -------------------
HDFS (legacy)        MapReduce (dead)    YARN (legacy)
S3 / GCS / ADLS      Hive (SQL on map)   Hive Metastore
                     Spark               Airflow / Dagster / Prefect
                     Flink (stream)      Databricks / EMR
                     Trino / Presto      Snowflake / BigQuery (serverless Spark alt)
                     Dask / Ray
```

### Apache Spark — the dominant framework

**What it is:** distributed in-memory data processing engine. Scala/Java/Python/SQL API. Replaces MapReduce for most use cases.

**Core abstractions:**
- **RDD** (Resilient Distributed Dataset) — low-level, immutable partitioned collection. Rarely used directly now.
- **DataFrame** — like a Postgres table, typed by schema, optimized by Catalyst query planner. **Main API today.**
- **Dataset** — DataFrame + static typing (Scala/Java only).
- **Spark SQL** — SQL on DataFrames; backed by Catalyst + Tungsten (code generation).

### Spark execution model

```
Driver program (your code)
   ↓ builds DAG of transformations (lazy, no execution yet)
Action triggers execution (collect, write, count):
   ↓ Catalyst optimizer rewrites logical plan → physical plan
   ↓ DAG scheduler splits into STAGES at shuffle boundaries
   ↓ Each stage → TASKS (one per partition)
   ↓ Task scheduler assigns tasks to executors across cluster
Executors run tasks in parallel, cache intermediate data in RAM
Results sent back to driver (or written to storage)
```

**Key concepts:**
- **Narrow transformation** (map, filter) — no shuffle, each partition independent → fast
- **Wide transformation** (groupBy, join, distinct) — shuffle required → expensive, write to disk between stages
- **Shuffle = sort + repartition across network** — the #1 cost in big data jobs. Minimize it.
- **Partitioning strategy** matters: too few = under-parallelized; too many = scheduling overhead. Rule: 2-4× cores in cluster.

### Spark SQL example

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum

spark = SparkSession.builder.appName("daily_revenue").getOrCreate()

# Read Parquet from S3 (schema inferred from files)
orders = spark.read.parquet("s3://data/orders/year=2026/month=10/")

# Join with product catalog (small table — broadcast join hint)
products = spark.read.parquet("s3://data/products/")
joined = orders.join(products.hint("broadcast"), "product_id")

# Aggregate — this triggers a shuffle
daily = (joined
    .groupBy("order_date", "category")
    .agg(_sum("amount").alias("revenue")))

# Write back as Parquet partitioned by date
daily.write.partitionBy("order_date").parquet("s3://data/revenue/daily/")
```

### Spark + Delta Lake / Iceberg (modern big data stack)

```
Raw events → S3 (bronze: raw JSON/CSV)
     ↓ Spark job
Delta Lake / Iceberg (silver: cleansed, typed, deduped)
     ↓ Spark job
Delta Lake / Iceberg (gold: business-level aggregates)
     ↓ Serve via Trino / Databricks SQL / Snowflake external table
```

**Why Delta/Iceberg + S3 killed Hadoop:**
- S3 is cheaper and more durable than HDFS
- Delta/Iceberg add ACID + time travel + schema evolution on object storage
- No HDFS cluster to operate — serverless Spark via Databricks/EMR

### Apache Flink — Spark's streaming competitor

**Flink vs Spark Streaming:**
- Flink: **true streaming** (event-by-event, millisecond latency)
- Spark Structured Streaming: **micro-batch** (groups of records every ~1s)
- Flink wins for: sub-second latency, exactly-once with low overhead, complex event-time windowing
- Spark wins for: batch + streaming same code, Python-first, Databricks ecosystem

**Flink killer features:**
- **Event time windows** with watermarks (handles late data correctly)
- **Stateful stream processing** (RocksDB state backend survives failures)
- **CEP** (complex event processing) — "detect pattern X in stream"
- **Exactly-once** semantics without heroics

### When to use Spark vs alternatives

| Use case | Tool |
|----------|------|
| Nightly batch ETL at TB scale | **Spark on S3 + Delta/Iceberg** |
| Real-time stream processing | **Flink** (preferred) or Spark Structured Streaming |
| SQL on data lake (interactive) | **Trino / Athena / Databricks SQL** (not Spark directly) |
| Small data (< 100 GB) | **Pandas / Polars / DuckDB** (no cluster needed!) |
| ML training data | **Spark + MLflow** or **Ray** |
| Dashboards on big data | Pre-aggregate with Spark → serve from **ClickHouse / BigQuery** |
| ETL for a startup | Avoid Spark. Use dbt + Snowflake/BigQuery. |

### DuckDB — the "no-cluster big data" surprise

For data up to ~1 TB on a single node, **DuckDB** reads Parquet from S3 and runs analytical SQL faster than most Spark clusters. **Mention it when interviewer asks "big data" prematurely** — many startups don't need Spark at all.

### Big data use cases (interview scenarios)

| Scenario | Pipeline |
|----------|----------|
| **Ad targeting** | Clickstream → Kafka → Flink (session windows) → Druid (serving) + S3 (training data) |
| **Fraud ML pipeline** | Transactions → Kafka → Spark job hourly → feature store (Feast) → model training (Spark MLlib) → serve via API |
| **Netflix recommendations** | Watch events → Kafka → Spark on S3 → Iceberg → model training → serving via microservice |
| **Spotify discover weekly** | Listening history → Spark batch job weekly → Cassandra for serving |
| **Pinterest home feed ranking** | User interactions → Kafka → Flink → features in Redis + offline features in S3 → ML model |
| **Uber surge pricing** | GPS pings → Kafka → Flink (time windows + geo) → Pinot for dashboard + decision |

### "Prove you know big data" questions

1. *"We have 100 TB of logs. How do we query 'top 10 errors by service last month'?"*
   → Store as Parquet in S3 partitioned by date + service. Query with **Trino/Athena** for ad-hoc, or Spark job to pre-aggregate into ClickHouse for dashboards.
2. *"Why not just put logs in Elasticsearch?"*
   → At 100 TB, ES becomes expensive and operationally heavy. S3 + Parquet + Athena is 1/10 the cost for occasional queries. Use ES for last 7 days only.
3. *"When would you use Spark vs just Postgres with partitioning?"*
   → Postgres fine up to ~5-10 TB with partitions. Beyond that, I/O bandwidth of one machine isn't enough — need parallelism across nodes.
4. *"Why Flink over Spark Streaming?"*
   → If latency < 100ms matters: Flink. Both great; team familiarity usually wins.
5. *"Explain shuffle in Spark."*
   → When partitions must be re-arranged across the cluster (groupBy, join without broadcast). All rows with the same key must land on the same executor → sort + network transfer + write to disk. #1 cost of big data jobs.

---

## 🔬 Aggregation Patterns — the "GROUP BY at scale" problem

Every system eventually needs to count, sum, average, or roll up. The DB choice depends on **when** the aggregation runs.

### The 4 aggregation strategies

| Pattern | When | Freshness | Query latency | Example |
|---------|------|-----------|---------------|---------|
| **On-the-fly (query-time)** | SQL `GROUP BY` on raw data | Always fresh | Slow at scale | Postgres small reports |
| **Materialized view (periodic)** | Refresh every N min | Minutes stale | Fast | Postgres mat view, Snowflake mat view |
| **Incremental materialized (streaming)** | Updated on every write | Seconds stale | Fast | Materialize, Flink, Kafka Streams, ClickHouse MV |
| **Pre-aggregated at ingest** | Compute during write | Live | Fastest | Druid rollup, Prometheus recording rules, Redis HLL/ZSET |

### Pattern 1: On-the-fly (OLTP)

```sql
-- Fine for small data
SELECT category, SUM(amount) FROM orders
WHERE created_at > now() - interval '1 day'
GROUP BY category;
```

Breaks when: data > few GB, concurrent queries > tens, aggregates many rows. **Add index on `(created_at, category) INCLUDE (amount)` to help.**

### Pattern 2: Periodic materialized views

```sql
-- Postgres
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT date_trunc('day', created_at) AS day, category, sum(amount)
FROM orders
GROUP BY 1, 2;

-- Refresh (locks table during refresh unless CONCURRENTLY)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;
```

**Trade:** staleness for query speed. Snowflake auto-refreshes; Postgres needs cron.

### Pattern 3: Streaming materialized (real-time)

```sql
-- Materialize (Postgres wire protocol)
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT date_trunc('day', created_at), category, sum(amount)
FROM orders WHERE status = 'paid'
GROUP BY 1, 2;
-- Automatically maintained from Kafka source. Query → sub-ms, always fresh.

-- ClickHouse  
CREATE MATERIALIZED VIEW events_hourly
ENGINE = SummingMergeTree() ORDER BY (hour, type)
AS SELECT toStartOfHour(ts) AS hour, type, count() AS c
   FROM events GROUP BY 1, 2;
-- Updated on every INSERT into events; dashboard queries hit events_hourly.
```

### Pattern 4: Pre-aggregate at ingest

**Druid rollup at ingest time:**

```json
{
  "granularitySpec": {"queryGranularity": "minute", "rollup": true},
  "metricsSpec": [
    {"type": "longSum", "name": "count", "fieldName": "count"},
    {"type": "doubleSum", "name": "revenue", "fieldName": "amount"},
    {"type": "hyperUnique", "name": "unique_users", "fieldName": "user_id"}
  ]
}
```

Billions of raw events → stored as one row per minute per dimension combo. **10-1000× storage savings** + instant queries.

### Approximate aggregations (the senior move)

Exact distinct counts over billions = expensive. Approximate algorithms give 95-99% accuracy with ~KB of memory.

| Algorithm | Purpose | Error | Memory |
|-----------|---------|-------|--------|
| **HyperLogLog (HLL)** | count distinct | ~0.81% | 12 KB fixed |
| **CountMin Sketch** | frequency of items | ~1% | few KB |
| **T-Digest / DDSketch** | quantiles (p50, p99) | ~1% | few KB |
| **Theta Sketch** | distinct + union/intersect | ~1% | few KB |
| **Bloom filter** | set membership | ~1% FP | ~1 byte per item |

**Where supported:**
- Postgres: `postgresql-hll` extension
- Redis: `PFADD` / `PFCOUNT` (HyperLogLog native)
- ClickHouse: `uniqHLL12`, `quantileTDigest`
- Druid, Pinot, Snowflake, BigQuery: `APPROX_COUNT_DISTINCT`, `APPROX_QUANTILES`

**Interview answer:** "For 'daily unique visitors across 100M users', I'd use HyperLogLog — 12 KB per day gives 1% error vs gigabytes of exact storage."

### Aggregation anti-patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| `COUNT(*)` on billion-row OLTP table | Full table scan | Approximate (`pg_class.reltuples`) or counter table |
| Postgres mat view refreshed every minute, 100 users querying | Lock during refresh + stale | ClickHouse MV or Materialize |
| `GROUP BY user_id` with 10M users in Postgres | Massive hash table in RAM | Partition by user_id or move to ClickHouse |
| Exact distinct count across all time | O(unique rows) memory | HLL — 12 KB and done |
| Pre-aggregate everything "just in case" | Storage explosion, every dim combo | Pre-aggregate only hot queries |

### "Prove you know aggregation" questions

1. *"Dashboard showing total revenue by hour, 100M events/day. How?"*
   → Pre-aggregate on ingest. ClickHouse `SummingMergeTree` MV on `(hour, category)` → query reads thousands of rows not billions.
2. *"Monthly active users across 1B users, must be exact?"*
   → Rarely must. **HyperLogLog** gives 0.81% error for 12 KB per month. Exact needs full user_id bitmap (125 MB) or distinct scan.
3. *"Live counter for 'likes' on viral post?"*
   → Redis `INCR` (not DB) + flush to Postgres every N seconds. Or Redis Streams + consumer that batches updates.
4. *"How does Prometheus compute `rate(http_requests_total[5m])` so fast?"*
   → Counter is monotonic. Query loads the samples in the 5-min window from the TSDB block (columnar, compressed), computes diff/elapsed. No GROUP BY — just two timestamp reads per series.

---

## Blob & File Storage (Not Databases, but Required in HLD)

Interviewers expect you to mention these alongside databases.

### Object Storage (S3, GCS, Azure Blob, MinIO)

| Aspect | Details |
|--------|---------|
| Model | Key → blob (up to 5 TB per object in S3) |
| Built | Distributed key-value metadata + erasure-coded chunks on disk |
| Use | Images, video, PDFs, backups, data lake files, static assets |
| Not for | Querying inside files, frequent small updates, listing millions fast |
| Pattern | DB stores metadata + S3 URL; CDN (CloudFront) caches blobs |

### Block Storage (EBS, Persistent Disk)

- Raw disk volumes attached to VMs
- **Under the hood of every database** — Postgres on EBS, Cassandra on local SSD
- Say: "Database runs on NVMe-backed EBS with provisioned IOPS"

### File / NAS (NFS, EFS, HDFS)

| System | Use |
|--------|-----|
| **HDFS** | Hadoop ecosystem, batch processing input |
| **EFS/NFS** | Shared files across servers |
| **Not** | Application primary data store in modern cloud apps |

### CDN (CloudFront, Akamai)

- Edge cache for static content — not a database
- Say: "Postgres for metadata, S3 for origin, CDN for delivery"

---

## Niche & Legacy (Know for Completeness)

### 22. RDF / Triple Stores (Semantic Web)

**Examples:** Apache Jena, Virtuoso, Blazegraph, Amazon Neptune (RDF mode)

**Model:** Subject → Predicate → Object triples: `(Alice, knows, Bob)`

| Use | Skip |
|-----|------|
| Knowledge graphs with formal ontologies | Normal social graph (use Neo4j) |
| Government/health interoperability (FHIR RDF) | E-commerce catalog |
| Semantic web research | Startup MVP |

### 23. Blockchain / Distributed Ledger

**Examples:** Hyperledger Fabric, Ethereum, Corda

**Model:** Append-only chain of blocks, consensus across untrusted parties, immutable.

| Use | Skip |
|-----|------|
| Multi-party trust without central authority | Internal app with one company owning DB |
| Supply chain provenance, cross-org settlement | High-TPS payment (too slow/expensive) |
| Crypto / DeFi | Traditional booking system |

**Say:** "For audit within our system, **Kafka + immutable log** is enough. Blockchain adds consensus overhead we don't need without untrusted parties."

### Legacy types (rarely chosen today)

| Type | Era | Modern replacement |
|------|-----|-------------------|
| Hierarchical (IMS) | 1960s | Relational |
| Network (CODASYL) | 1970s | Relational + graph |
| Object-Oriented DB | 1990s | Document DB + OOP in app layer |
| XML-native DB | 2000s | JSON document DB |

---

## OLTP vs OLAP vs Specialized — Decision Framework

```
                    START
                      │
         Is it user-facing transactional data?
                    /   \
                  YES    NO
                  /        \
            Need ACID?    Is it metrics over time?
            /      \           /        \
          YES      NO        YES         NO
          /          \        /            \
      Postgres    Cassandra  Time-Series   Is it search/text?
      NewSQL      Document       DB              /        \
      Redis*      DynamoDB                    YES         NO
                                              /              \
                                        Elasticsearch    Is it ML similarity?
                                                              /        \
                                                            YES         NO
                                                            /            \
                                                      Vector DB      Is it analytics?
                                                                        /        \
                                                                      YES         NO
                                                                      /            \
                                                                 OLAP/Lakehouse   Graph traversal?
                                                                                    /        \
                                                                                  YES         NO
                                                                                  /            \
                                                                            Graph DB      S3 blob / Kafka log
```

*Redis for ephemeral transactional patterns (locks, holds), not durable source of truth.

---

## Master Comparison Table — All Types

| # | Type | Examples | Data model | Consistency | Scale | Best query | Weak at |
|---|------|----------|------------|-------------|-------|------------|---------|
| 1 | **Relational (OLTP)** | Postgres, MySQL, Aurora | Tables, rows | ACID strong | Vertical + replicas | Joins, ad-hoc SQL | Write scale, schema changes |
| 2 | **Wide-column** | Cassandra, HBase, Scylla | Partition + clustering | Tunable eventual | Linear horizontal | Partition key + range | Joins, ad-hoc, cross-partition |
| 3 | **Document** | MongoDB, CouchDB | JSON/BSON docs | Eventual (optional ACID) | Sharded | Doc by ID, nested read | Joins, large array updates |
| 4 | **Key-value** | Redis, DynamoDB, etcd | Key → value | Per-key / eventual | Very high | O(1) get/set | Queries, relationships |
| 5 | **Time-series** | InfluxDB, Prometheus, TimescaleDB | Timestamp + tags + fields | Eventual | High ingest | Time range aggregates | OLTP, high-cardinality tags |
| 6 | **Graph** | Neo4j, Neptune, JanusGraph | Nodes + edges | ACID (per graph) | Moderate | Multi-hop traversal | Bulk analytics, easy sharding |
| 7 | **Vector** | Pinecone, Milvus, pgvector | Embedding vectors | Eventual | High ANN QPS | Similarity / semantic search | Exact match, transactions |
| 8 | **Search** | Elasticsearch, Solr | Inverted index | Eventual | Horizontal | Full-text, facets, autocomplete | Source of truth, ACID |
| 9 | **OLAP / Warehouse** | Snowflake, BigQuery, Redshift | Columnar tables | Eventual | Petabyte | GROUP BY, BI dashboards | OLTP, low-latency point reads |
| 10 | **Columnar OLAP** | ClickHouse, Druid, Pinot | Columnar | Eventual | Very high ingest + query | Real-time analytics | Updates, transactions |
| 11 | **NewSQL** | Spanner, CockroachDB, Yugabyte | SQL tables, distributed | Strong global | Horizontal | SQL + global ACID | Cost, cross-region latency |
| 12 | **HTAP** | TiDB, SingleStore, AlloyDB | Row + column replica | Strong / near-strong | Horizontal | OLTP + analytics same DB | Neither best OLTP nor OLAP alone |
| 13 | **Multi-model** | Cosmos DB, ArangoDB, Fauna | Doc + KV + graph APIs | Tunable | Global distributed | Flexible model per API | Cost, not best per model |
| 14 | **Embedded** | SQLite, Realm | SQL / object file | ACID local | Single process | Local SQL | Multi-writer server |
| 15 | **Real-time sync** | Firestore, Firebase, CouchDB | JSON + live push | Eventual | Managed scale | Offline-first sync | Complex queries, server OLTP |
| 16 | **Spatial / GIS** | PostGIS, Redis GEO | Points, polygons | Follows backing DB | Moderate | Radius, contains, distance | Pure live tracking alone |
| 17 | **Ledger / Immutable** | QLDB, immudb | Append-only verifiable | Strong | Moderate | Audit history | Mutable current-state queries |
| 18 | **Event log** | Kafka, Pulsar, Kinesis | Ordered log | Ordered per partition | Massive throughput | Replay, stream consume | Random access, queries |
| 19 | **Event sourcing DB** | EventStoreDB, Marten | Event streams | Strong per stream | Moderate | Replay, projections | Simple CRUD, team learning curve |
| 20 | **Data lake** | S3, GCS, MinIO | Files (Parquet, JSON) | Eventual | Unlimited cheap | Batch scan | OLTP, interactive SQL alone |
| 21 | **Lakehouse** | Delta Lake, Iceberg, Hudi | Files + table metadata | Snapshot ACID | Petabyte | SQL on lake, time travel | Low-latency serving |
| 22 | **Federated SQL** | Trino, Athena, Presto | None (engine only) | Depends on source | Query-bound | Cross-source SQL joins | App serving, writes |
| 23 | **In-memory SQL** | SAP HANA, VoltDB | Rows in RAM | ACID | RAM-limited | Ultra-low latency OLTP | Cost, dataset size |
| 24 | **Cache** | Redis, Memcached | KV in RAM | Eventual | Very high | Hot key reads | Durability, complex queries |
| 25 | **Object storage** | S3, GCS, Azure Blob | Key → blob | Strong durability | Unlimited | Store/retrieve blobs | Query, list at scale, small files |
| 26 | **RDF / Triple** | Jena, Virtuoso, Neptune RDF | Subject-predicate-object | Varies | Moderate | SPARQL, ontologies | General app development |
| 27 | **Blockchain** | Hyperledger, Ethereum | Block chain | Consensus-based | Low TPS | Trustless audit | Performance, cost, private apps |

---

## Industry Examples at Scale — Who Uses What

Real companies, real numbers, real lessons. Cite these in interviews.

### Netflix

| Component | Database | Scale / insight |
|-----------|----------|-----------------|
| Viewing history, user data, metadata | **Cassandra** (4-region active-active) | Default choice for almost everything durable |
| Hot reads (homepage, recommendations) | **EVCache** (Memcached) | Petabytes cached, sub-100µs latency |
| Billing, subscriptions, revenue | **MySQL** | Relational where money matters |
| Multi-region transactions | **CockroachDB** | Global tx workflows |
| Metrics | **Atlas** (custom time-series) | Built in-house for monitoring |
| Media, logs | **S3 + Iceberg** | Blobs and big data |
| Abstraction layer | **Data Gateway / KV Service** | One API over Cassandra, EVCache, DynamoDB, RocksDB |

**Key lesson:** Netflix tried building a custom in-memory stateful tier for viewing data, regretted the complexity, and moved back to **Cassandra + cache**. Don't reinvent distributed systems — use proven stores and add a platform abstraction on top.

Sources: [Netflix Tech Blog — viewing data](https://netflixtechblog.com/netflixs-viewing-data-how-we-know-where-you-are-in-house-of-cards-608dd61077da), [KV abstraction layer](https://netflixtechblog.com/introducing-netflixs-key-value-data-abstraction-layer-1ea8a0a11b30), [Data Gateway](https://netflixtechblog.medium.com/data-gateway-a-platform-for-growing-and-protecting-the-data-tier-f1ed8db8f5c6)

---

### Uber

| Era | Component | Database | Why they switched |
|-----|-----------|----------|-------------------|
| Early | Monolith trips | **PostgreSQL** (single instance) | Fine until ~2014; became bottleneck |
| Scale | Trip data (Schemaless) | **Sharded MySQL** + JSON blobs | Migrated off single Postgres; horizontal scale |
| High volume | Marketplace OLTP | **Cassandra** + **Redis** | Millions QPS, petabytes; AP, availability-first |
| Fulfillment re-arch | Trip/supply state | **Google Cloud Spanner** | Cassandra+Redis couldn't give transactional consistency |

**Key lesson:** Uber ran Cassandra at massive scale for years, then **moved fulfillment to Spanner** when they needed **ACID across entities** — not just availability. Availability-first (Cassandra) and consistency-first (Spanner) are different problems.

Uber on Cassandra: millions of queries/sec, multi-region, 6+ years in production — [Uber Cassandra blog](https://www.uber.com/blog/how-uber-optimized-cassandra-operations-at-scale/)

Uber fulfillment → Spanner: [Fulfillment platform rearchitecture](https://www.uber.com/blog/fulfillment-platform-rearchitecture/)

---

### Pinterest (2011–2012 crisis → lesson)

| Before | After | Result |
|--------|-------|--------|
| Cassandra, Membase, MongoDB — all failing nightly | **Sharded MySQL** + Redis + Memcache | Only MySQL never lost data |
| 3 engineers, 6 storage technologies | Shard ID encoded in 64-bit object ID | No lookup service needed |

**Key lesson:** Pinterest **ripped out failing NoSQL** and went back to sharded SQL. NoSQL is not automatically "more scalable." Operational maturity and data model fit matter more than hype. MySQL + smart sharding scaled to billions of objects.

Source: [Pinterest MySQL sharding](https://sujeet.pro/articles/pinterest-mysql-sharding)

---

### Alibaba (Double 11 / Tmall flash sales)

| Metric | Number |
|--------|--------|
| Peak transactions (2020) | **583,000 orders/sec** |
| Traffic vs 2009 first Double 11 | **1,457× higher** |
| Redis inventory deduction | **>100,000 QPS** (Lua atomic scripts) |
| Request filtering layer | **>600,000 QPS** rejects invalid orders |

**Stack:** CDN + browser cache → Redis filter → Redis inventory (Lua `HINCRBY`) → async queue → DB persistence

**Key lesson:** During flash sales, **99.9% of traffic is reads checking inventory; only 0.1% are successful writes**. DB row locks die instantly. Redis does atomic deduct; DB catches up async.

Sources: [Alibaba flash sale architecture](https://www.alibabacloud.com/blog/system-stability-assurance-for-large-scale-flash-sales_596968), [Redis flash sale guide](https://www.alibabacloud.com/help/en/redis/use-cases/use-apsaradb-for-redis-to-build-a-business-system-that-can-handle-flash-sales)

---

### Stripe (payments)

| Component | Database | Why |
|-----------|----------|-----|
| High-volume API objects (charges, customers) | **DocDB** (custom DBaaS on MongoDB) | 5M+ QPS, 2000+ shards, petabytes |
| Idempotency keys | **PostgreSQL** | Row-level lock on `(account_id, idempotency_key)` |
| Events | **Kafka** | Async pipeline |
| Real-time analytics | **Apache Pinot** + **Flink** | OLAP on event stream |

**Key lesson:** Stripe uses **MongoDB-derived DocDB for volume** but **Postgres for idempotency** — the exact operation that prevents double-charging. Split by consistency requirement, not by "one DB for everything."

Migration pattern they invented: **dual-write → backfill → dual-read → cutover** (zero downtime).

Sources: [Stripe DocDB blog](https://stripe.dev/blog/how-stripes-document-databases-supported-99.999-uptime-with-zero-downtime-data-migrations), [Online migrations](https://stripe.com/blog/online-migrations)

---

### Amazon (origin of Dynamo → DynamoDB)

| Service | Design choice |
|---------|---------------|
| Shopping cart | **Always writable** — never reject an "add to cart" |
| Consistency | **Eventual** — merge conflicting cart versions on read |
| Conflict resolution | Application-level, not DB-level |
| Modern form | **DynamoDB** (managed Dynamo principles) |

**Key lesson from the [Dynamo paper (2007)](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf):** Shopping carts choose **AP over CP**. A deleted item temporarily reappearing is acceptable; rejecting a write is not. **Payments and inventory are the opposite** — CP required.

---

### Instagram / Meta

| Component | Evolution |
|-----------|-----------|
| Photos metadata | **PostgreSQL** → sharded |
| Feed / activity | **Cassandra** (write-heavy) |
| Cassandra storage engine | Replaced Java heap with **RocksDB** (SSD) to cut GC pauses |
| Cache | **Memcached** |

**Key lesson:** Even Cassandra needed a **storage engine swap** (RocksDB) at Instagram scale to fix latency tail.

---

### Twitter / X

| Component | Database |
|-----------|----------|
| Tweets (historical) | **Manhattan** (custom distributed KV) → **Twitter DB** |
| Timeline | Fan-out on write + **Redis** cache |
| Search | **Earlybird** (Lucene-based) |

**Key lesson:** At extreme scale, companies build **custom KV layers** — but only after exhausting Cassandra/MySQL. Not a startup move.

---

### Summary: What industry actually does

```
STARTUP (< 1M users)     → Postgres + Redis. Done.
GROWTH (1M–100M)         → Add Elasticsearch, Kafka, read replicas
HYPERSCALE (100M+)       → Cassandra/DynamoDB for hot paths, polyglot everything
MONEY / INVENTORY        → SQL or Spanner ALWAYS for source of truth
FLASH SALE HOT PATH      → Redis Lua, async DB
NEVER                    → One DB for whole system
```

---

## Scale-Wise: Which DB Wins at What Size

Use this when interviewer asks "at what scale do you switch?"

### By write throughput (sustained)

| Writes/sec | Winner | Why | Example |
|------------|--------|-----|---------|
| < 1K | **PostgreSQL** | Simple, ACID, cheap | Startup booking app |
| 1K – 50K | **PostgreSQL** + partitioning | Still fine with good indexes | Medium e-commerce |
| 50K – 500K | **PostgreSQL sharded** or **Cassandra** | Single node saturates | Large marketplace |
| 500K – 1M+ | **Cassandra / DynamoDB / Kafka** | LSM, no leader bottleneck | Uber trips, Netflix events |
| 1M+ (burst) | **Redis** (ephemeral) + async persist | Absorb spike, queue to DB | Alibaba Double 11 |

### By read throughput

| Reads/sec | Winner | Pattern |
|-----------|--------|---------|
| < 10K | Postgres + optional Redis | Cache-aside |
| 10K – 100K | Redis/Memcached in front | 95%+ cache hit rate |
| 100K – 1M | Redis cluster + read replicas | Shard cache by key |
| 1M+ | CDN (static) + edge cache + Redis | Push reads to edge |

### By data size

| Data size | OLTP winner | Analytics winner |
|-----------|-------------|-------------------|
| < 100 GB | PostgreSQL | Postgres or ClickHouse |
| 100 GB – 10 TB | Sharded Postgres / Cassandra | ClickHouse, BigQuery |
| 10 TB – 1 PB | Cassandra, DynamoDB | Snowflake, BigQuery, S3+Iceberg |
| 1 PB+ | Cassandra + S3 (cold) | Data lake + warehouse |

### By latency requirement

| Latency target | Pick | Avoid |
|----------------|------|-------|
| < 1 ms | Redis, in-memory | Disk DB direct |
| 1–10 ms | Redis → Postgres, DynamoDB | Cross-region sync write |
| 10–50 ms | Postgres, Cassandra (same region) | Unsharded SQL at scale |
| 50 ms – 1 s | Elasticsearch, graph traversal | — |
| Seconds+ | OLAP, data lake | Using warehouse for user-facing API |

### By consistency requirement

| Requirement | Must use | Never use alone |
|-------------|----------|-----------------|
| **Strong ACID** (money, seats) | Postgres, Spanner, CockroachDB | Cassandra default, DynamoDB default |
| **Per-key linearizable** | DynamoDB strong read, etcd, Redis SETNX | Eventual Cassandra ONE |
| **Eventual OK** (feeds, views) | Cassandra, DynamoDB, CouchDB | Over-engineering with Spanner |
| **Audit immutable** | Kafka, QLDB, event log | Mutable SQL without log |

### Scale crossover points (rules of thumb)

```
Postgres single node comfortable until:
  ~ 10K writes/sec OR ~ 5TB OR ~ 10K concurrent connections (with PgBouncer)

Add Redis when:
  same keys read >> written (10:1 ratio) OR need TTL OR need sub-ms

Add Cassandra when:
  writes > 50K/sec sustained OR multi-DC AP required OR append-only events

Add Elasticsearch when:
  full-text search OR faceted browse OR SQL LIKE is too slow

Add Kafka when:
  need replay OR decouple services OR event sourcing OR peak >> sustained

Add Spanner/Cockroach when:
  global ACID across shards AND budget exists AND latency tolerance ~50ms+

Add ClickHouse/BigQuery when:
  analytics queries slow down OLTP OR data > few TB for reporting
```

---

## Critical Problem Playbook — Flash Sale, Payment, Booking

These are the **highest-value HLD scenarios**. Interviewers test whether you match DB to the **failure mode**, not just the feature.

---

### Problem 1: Flash Sale (limited inventory, 1M users, 1000 items)

**The failure:** Row-level lock on `inventory` table → all threads queue → DB melts → 0 orders succeed.

**The math:** 1,000,000 users, 1,000 items = **99.9% of requests are wasted reads**. Only 0.1% are successful writes.

#### Architecture (Alibaba pattern)

```
Layer 1: CDN + browser cache     → absorb page refresh storm
Layer 2: Redis read replica      → filter "already sold out" (>600K QPS reject)
Layer 3: Redis master + Lua      → atomic inventory deduct (>100K QPS)
Layer 4: Redis list queue        → order messages async
Layer 5: DB workers              → persist orders, final inventory reconcile
```

#### Redis Lua script (core idea)

```lua
-- KEYS[1] = inventory hash key
-- ARGV[1] = quantity to deduct
local available = tonumber(redis.call('HGET', KEYS[1], 'available'))
if available >= tonumber(ARGV[1]) then
    redis.call('HINCRBY', KEYS[1], 'booked', ARGV[1])
    return 1  -- success
end
return 0  -- sold out
```

#### DB choice per layer

| Layer | DB | Why |
|-------|-----|-----|
| Inventory hot path | **Redis** | Single-threaded atomic Lua, no lock contention |
| Order persistence | **PostgreSQL** (async) | ACID for final record; not on critical path |
| Product page | **CDN + cache** | Static/semi-static |
| Anti-bot / rate limit | **Redis INCR** | Per-user throttle |

#### Critical problems to mention

| Problem | Solution |
|---------|----------|
| **Overselling** | Lua atomic deduct; DB reconcile with Redis as source during sale |
| **Hot key** (one viral SKU) | Local cache pre-warm + single Redis key still bottleneck → shard inventory key or segment stock |
| **Cache breakdown** | Never expire all keys at once; random TTL jitter; mutex on rebuild |
| **Thundering herd** | Return "sold out" from cache without hitting DB |
| **Duplicate orders** | Idempotency key per user+SKU in Redis SETNX |
| **DB catch-up lag** | Accept queue depth metric; scale workers; cap sale duration |

#### Interview script

> "Flash sale is **0.1% write, 99.9% read**. Postgres row locks fail at 10K concurrent. I'd put inventory in **Redis with Lua atomic deduct**, filter sold-out at cache layer, **async queue orders to Postgres** for durable record. Redis is source of truth during the 10-minute sale window; DB reconciles after."

---

### Problem 2: Payment (must never double-charge)

**The failure:** Network retry sends same charge twice → customer charged $200 instead of $100.

#### Architecture (Stripe pattern)

```
Client → API with Idempotency-Key header
       → Postgres: SELECT ... FOR UPDATE on (account_id, idempotency_key)
       → if exists: return cached response
       → if new: process payment, store result, commit
       → DocDB/MongoDB: store charge object (high volume)
       → Kafka: emit payment.succeeded event
```

#### DB choice

| Component | DB | Why |
|-----------|-----|-----|
| Idempotency store | **PostgreSQL** | Row lock, transactional, `(account_id, key)` unique |
| Charge/customer objects | **MongoDB/DocDB** or **Postgres** | Flexible schema at volume |
| Payment events | **Kafka** | Immutable audit, downstream consumers |
| Analytics | **Pinot/ClickHouse** | Not on payment path |

#### Critical problems

| Problem | Solution |
|---------|----------|
| **Double charge** | Idempotency key + DB unique constraint |
| **Partial failure** | `recovery_point` column — resume from last step (Stripe pattern) |
| **Concurrent retries** | `locked_at` column — row-level lock blocks parallel processing |
| **Lost response** | Store response body in idempotency table; replay same response |
| **Exactly-once illusion** | Idempotent consumers + at-least-once Kafka = effectively exactly-once |

#### What NOT to do

| Bad choice | Why |
|------------|-----|
| DynamoDB without conditional writes for idempotency | Possible with conditions, but Postgres row lock is clearer |
| Redis alone for payment state | Durability risk; use as lock only, not source of truth |
| Cassandra LWT for every payment | Too slow at payment QPS |
| Eventual consistency | Double charge window exists |

#### Interview script

> "Payments need **strong consistency on idempotency**. I'd use **Postgres with a unique (account_id, idempotency_key)** and row lock. High-volume charge objects can live in document store. **Never** process payment without idempotency check in same transaction as state update."

---

### Problem 3: Seat / Ticket Booking (double booking)

**The failure:** Two users click "Book" on seat A1 at same millisecond → both get confirmation.

#### Architecture (your repo's pattern — correct)

```
HOLD (fast, locked):
  Redis SETNX seat:{showtime}:{seat_id} hold_uuid EX 600
  OR Postgres: UPDATE seats SET state='HELD' WHERE id=? AND state='AVAILABLE'

PAY (slow, NO lock):
  Payment gateway ~500ms — lock NOT held

CONFIRM (fast, locked):
  Postgres transaction: seat BOOKED + insert reservation + delete Redis hold
```

#### DB choice

| Approach | DB | Pros | Cons |
|----------|-----|------|------|
| **Row per seat (SQL)** | PostgreSQL | ACID, `FOR UPDATE`, auditable | Slower than Redis at extreme scale |
| **Redis SETNX + TTL** | Redis | Sub-ms, auto-expire holds | Must sync confirm to SQL |
| **Whole seat map in one doc** | MongoDB | ❌ Bad | Document lock → all seats contend |
| **Cassandra per seat** | Cassandra | Scales | LWT too slow; eventual = oversell risk |

#### Critical problems

| Problem | Solution |
|---------|----------|
| **Double booking** | Atomic check-and-set: `UPDATE ... WHERE state='AVAILABLE'` — check `rows_affected == 1` |
| **Hold never released** | TTL on Redis key (10 min); background job expires stale holds in SQL |
| **Pay during hold expiry** | On confirm: re-check seat still held by this user |
| **Admin blocks seat** | Strong consistency read before hold |
| **Same user double-click** | Idempotency key on hold request |

#### Interview script

> "Seat booking is **optimistic concurrency on a row per seat**. `UPDATE seats SET status='held' WHERE id=? AND status='available'` — if zero rows updated, someone else got it. Hold expires in 10 minutes via Redis TTL. Payment runs **outside** the lock. Confirm is a single Postgres transaction."

---

### Problem 4: Social Feed (write-heavy, read-heavy)

| Scale | Strategy | DB |
|-------|----------|-----|
| < 1M users | Fan-out on read | Postgres + cache |
| 1M–100M | Fan-out on write (push to followers' inbox) | Cassandra `PRIMARY KEY (user_id, post_id)` |
| Celebrity post (10M followers) | Hybrid: normal users fan-out on write; celebrities fan-out on read | Cassandra + Redis |

**Twitter lesson:** Fan-out on write for normal users; fan-out on read for celebrities — otherwise one tweet writes 10M Cassandra rows.

---

### Problem 5: Live Leaderboard / Gaming score

| Requirement | DB |
|-------------|-----|
| Top 100 scores, updated 100K/sec | **Redis Sorted Set** `ZADD leaderboard score user_id` |
| Historical scores | Cassandra append |
| Persistent rank (end of season) | Postgres snapshot from Redis |

**Why not SQL:** `ORDER BY score LIMIT 100` on every update = full table sort. Redis ZSET is O(log N).

---

### Problem 6: Rate Limiting / API throttle

```
Redis: INCR rate:{user_id}:{minute} EX 60
if count > 100 → 429 Too Many Requests
```

**Why Redis:** Atomic INCR, TTL auto-reset, millions of keys, sub-ms.

---

### Problem 7: Distributed Lock

| Use case | Tool | Caveat |
|----------|------|--------|
| Short lock (seat hold) | Redis `SETNX` + TTL | TTL prevents deadlock; not 100% safe without Redlock debate |
| Critical financial | **Postgres advisory lock** or **Spanner** | Stronger guarantees |
| Leader election | **etcd**, **ZooKeeper** | Consensus-based |

**Interview nuance:** Redis locks are fine for **holds with TTL**. Don't use Redis Redlock for **bank transfers**.

---

### Problem 8: Global inventory across regions

| Strategy | DB | Tradeoff |
|----------|-----|----------|
| Single region source of truth | Postgres primary in one region | Cross-region latency on write |
| Partition inventory by region | DynamoDB per region | Can't sell region A stock to region B user |
| Reserve + async sync | Spanner global | Strong but ~50ms+ cross-region |
| Oversell + compensate | Cassandra AP + reconciliation | Availability over perfect accuracy |

**Flash sale globally:** Pre-allocate inventory per region in Redis; no cross-region deduct during peak.

---

### Critical Problem → DB Quick Map

| Problem | Hot path DB | Durable DB | Never use alone |
|---------|-------------|------------|-----------------|
| Flash sale inventory | **Redis (Lua)** | Postgres (async) | Postgres row lock |
| Payment / idempotency | **Postgres** (sync) | Postgres + Kafka | Cassandra, Redis |
| Seat booking | **Redis SETNX** or **Postgres row** | Postgres | MongoDB whole doc |
| Shopping cart | **DynamoDB** (AP) | — | Strong SQL (reject writes on partition) |
| Social feed write | **Cassandra** | — | Single Postgres |
| Live leaderboard | **Redis ZSET** | Postgres snapshot | SQL ORDER BY |
| Fraud graph check | **Neo4j** / in-memory | Postgres accounts | SQL 6-hop join |
| Search autocomplete | **Elasticsearch** | Postgres source | SQL LIKE |
| Metrics dashboard | **Prometheus** | — | Postgres time queries |
| File upload | **S3** | Postgres metadata | DB BLOB column |

---

## Article Insights You Must Know

Distilled from engineering blogs and classic papers — the "why" behind the choices.

### 1. Dynamo paper (Amazon, 2007) — birth of NoSQL thinking

- **Shopping cart is AP, not CP.** Always accept writes; merge conflicts on read.
- **Implication:** Don't use Dynamo pattern for inventory or payments.
- **Descendants:** DynamoDB, Cassandra, Riak, Voldemort.

### 2. Pinterest "MySQL wins" (2012)

- Cassandra, MongoDB, Membase caused **data corruption and nightly outages**.
- MySQL + Redis + Memcache ran for **10+ years** after.
- **Insight:** Boring technology that ops team can run beats trendy DB that fails at 3am.

### 3. Uber Cassandra → Spanner (2020s)

- Cassandra optimized for **availability**; fulfillment needed **transactional consistency**.
- Mirrored Cassandra clusters + Redis cache = complexity without strong guarantees.
- **Insight:** Migration trigger is **consistency requirement change**, not "we got too big."

### 4. Alibaba Double 11 — flash sale math

- **583K orders/sec** peak (2020).
- **99.9% reads, 0.1% writes** during flash sale.
- Redis Lua for atomic deduct; DB is **async**, not on critical path.
- **Three-level cache:** local pre-warm → hot-key sensor → Tair/Redis full cache.

### 5. Stripe idempotency (payments bible)

- **Postgres row lock** on idempotency key — not MongoDB, not Redis.
- `recovery_point` field for **resumable** multi-step payment flows.
- **Dual-write migration:** write both → backfill → read new → delete old (zero downtime).
- 99.999% uptime on **DocDB** (Mongo-derived) for volume; Postgres for correctness-critical paths.

### 6. Netflix "we built our own cache tier and regretted it"

- Custom stateful tier for viewing data → hot spots, multi-region complexity.
- Moved to **Cassandra + EVCache** — mature beats custom.
- Built **Data Gateway** abstraction so apps don't couple to Cassandra API directly.

### 7. PACELC in one sentence

- **If Partition:** choose A or C.
- **Else:** choose Latency or Consistency.
- DynamoDB = PA/EL. Spanner = PC/EC. Cassandra = PA/EL (default).

### 8. LSM vs B-Tree at scale

- **Write-heavy** (feeds, logs, metrics) → LSM (Cassandra, RocksDB).
- **Read-heavy balanced** (user profiles, orders) → B-Tree (Postgres).
- Instagram swapped Cassandra's Java heap storage for **RocksDB on SSD** — GC pauses were killing p99.

### 9. Hot key problem (every hyperscaler hits this)

- One key (viral product, celebrity tweet) → one Redis/Cassandra partition overloaded.
- Fixes: **local cache**, **key splitting** (`inventory:sku` → `inventory:sku:shard0..N`), **read replicas** for hot keys.

### 10. Cache-aside vs read-through vs write-through

| Pattern | When | Risk |
|---------|------|------|
| **Cache-aside** | General purpose | Cache miss stampede |
| **Read-through** | Always want cache warm | Cache failure = read failure |
| **Write-through** | Strong cache-DB consistency | Write latency += cache write |
| **Write-behind** | Flash sale async persist | Data loss window if cache dies |

### 11. CQRS — why big systems split read/write DBs

- **Write:** Postgres (normalized, ACID).
- **Read:** Elasticsearch (search), Redis (hot), ClickHouse (analytics).
- Sync via Kafka CDC. Each optimized for its query pattern.

### 12. The "one database" fallacy

Every hyperscaler blog post ends the same way:
> "We use Postgres/MySQL for money, Cassandra for volume, Redis for speed, Elasticsearch for search, Kafka for events, S3 for blobs."

That's the answer. Not one DB.

---

## Scenario Playbook — What to Pick When

### Social media (Twitter / Instagram)

| Component | DB | Why |
|-----------|-----|-----|
| User accounts | Postgres / MySQL | ACID, relationships |
| Tweet/post write | Cassandra | High write rate, by user_id |
| Timeline read | Redis cache + Cassandra | Fan-out on write or read |
| Media | S3 + CDN | Blobs not in DB |
| Search users/posts | Elasticsearch | Full-text |
| Metrics | Prometheus / Kafka → ClickHouse | Time-series / analytics |

### E-commerce (Amazon-style)

| Component | DB | Why |
|-----------|-----|-----|
| Orders, inventory | Postgres | ACID checkout |
| Product catalog | MongoDB or Postgres JSON | Flexible attributes |
| Product search | Elasticsearch | Facets, fuzzy |
| Cart / session | Redis | TTL, fast |
| Recommendations | Vector DB + batch ML | Similarity |
| Analytics | BigQuery / ClickHouse | OLAP |

### Movie ticket booking (this repo's domain)

| Component | DB | Why |
|-----------|-----|-----|
| Seat inventory | **Postgres** (row per seat) or **Redis** (SETNX + TTL) | Atomic hold — no double book |
| Confirmed booking | Postgres | ACID, audit |
| Show/movie catalog | Postgres or MongoDB | Read-heavy metadata |
| Search movies | Elasticsearch | Title, actor, genre |
| Payment | Postgres | Transactional |
| Monitoring | Prometheus | Latency, error rates |

### Uber / ride-sharing

| Component | DB | Why |
|-----------|-----|-----|
| Trip state machine | Postgres / DynamoDB | Strong per-trip consistency |
| Driver location (live) | Redis GEO / specialized | Sub-second updates |
| Location history | Cassandra / time-series | Append GPS pings |
| Pricing / routing graph | Graph or in-memory | Shortest path |
| Analytics | ClickHouse | Trip aggregates |

### IoT platform

| Component | DB | Why |
|-----------|-----|-----|
| Sensor ingest | Cassandra / Kafka | Millions writes/sec |
| Time-range queries | InfluxDB / TimescaleDB | Compression, downsampling |
| Device registry | Postgres | Relational metadata |
| Alerts | Redis + stream processor | Real-time thresholds |

### Banking / payments

| Component | DB | Why |
|-----------|-----|-----|
| Account balances | Postgres / Spanner | ACID, serializable |
| Transaction log | Ledger / event store | Immutable audit |
| Fraud graph | Neo4j | Multi-hop device linkage |
| Statements / reports | OLAP warehouse | Historical aggregates |

### RAG / AI chatbot

| Component | DB | Why |
|-----------|-----|-----|
| Users, billing, ACL | Postgres | OLTP |
| Documents | S3 | Blob storage |
| Chunk embeddings | Pinecone / pgvector | Semantic retrieval |
| Chat history | Postgres or Cassandra | By user_id partition |
| Keyword fallback | Elasticsearch | Exact term match |

### Notification system

| Component | DB | Why |
|-----------|-----|-----|
| User preferences | Postgres | Relational |
| Delivery queue | Kafka / SQS | Ordered, durable |
| Unread count | Redis | Fast INCR |
| Delivery log | Cassandra | Append-only per user |

---

## Polyglot Persistence — Real System Examples

**One database per job.** Mature systems use 5-10 storage types.

```
                    ┌─────────────┐
                    │   API GW    │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      ┌─────────┐    ┌──────────┐    ┌───────────┐
      │  Redis  │    │ Postgres │    │    S3     │
      │ cache / │    │ source   │    │  media /  │
      │  locks  │    │ of truth │    │  exports  │
      └─────────┘    └────┬─────┘    └───────────┘
                          │ CDC / Kafka
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        Elasticsearch  ClickHouse  Vector DB
        (search)       (analytics)  (AI/RAG)
```

### CQRS pattern (say this in interviews)

- **Command side:** write to OLTP DB (Postgres)
- **Query side:** async replicate to search (ES), cache (Redis), analytics (ClickHouse)
- Reads and writes optimized independently

---

## Common Interview Traps and Strong Answers

### Trap: "Just use MongoDB for everything"

**Answer:** "MongoDB is great for document-shaped aggregates with flexible schema. For seat booking I need row-level atomicity — Postgres or Redis per seat, not a 200-seat document with write contention."

### Trap: "Cassandra is faster than SQL"

**Answer:** "Cassandra is faster for **append-heavy, partition-key lookups** at scale. It's slower and wrong for ad-hoc joins and cross-partition queries. Different tool."

### Trap: "We need strong consistency everywhere"

**Answer:** "Strong consistency has a latency and availability cost. Payments: strong. Movie plot synopsis: eventual OK. I match consistency to business requirement."

### Trap: "Elasticsearch replaces SQL"

**Answer:** "Elasticsearch is a **search index** — rebuilt from the source of truth. If ES loses data, we replay from Postgres/Kafka."

### Trap: "Redis as primary database"

**Answer:** "Redis is my **fast ephemeral layer** — sessions, locks, rate limits. Durability-sensitive state goes to Postgres with Redis as cache, cache-aside pattern."

### Trap: No mention of access pattern

**Answer:** Always state the query first: "We query by `user_id` + time range" → then pick Cassandra/Postgres accordingly.

---

## Complete Cheat Sheet — All 27 Types

| # | If you need… | Pick this |
|---|--------------|-----------|
| 1 | ACID transactions, joins, relationships | **PostgreSQL / MySQL** |
| 2 | Billions of writes/sec, partition-key access | **Cassandra / ScyllaDB** |
| 3 | Flexible JSON, nested documents | **MongoDB** |
| 4 | Sub-ms reads, TTL, locks, leaderboards | **Redis** |
| 5 | Serverless KV, AWS-native scale | **DynamoDB** |
| 6 | Metrics, monitoring, time-range queries | **Prometheus / InfluxDB / TimescaleDB** |
| 7 | Multi-hop relationships, fraud graphs | **Neo4j** |
| 8 | Semantic / AI similarity search | **pgvector / Pinecone / Milvus** |
| 9 | Full-text search, autocomplete, facets | **Elasticsearch** |
| 10 | BI dashboards, SQL on billions of rows | **Snowflake / BigQuery** |
| 11 | Real-time analytics, fast aggregations | **ClickHouse / Druid** |
| 12 | Global SQL + strong consistency | **Spanner / CockroachDB** |
| 13 | OLTP + analytics without separate warehouse | **TiDB / SingleStore (HTAP)** |
| 14 | Multiple models, global Azure app | **Cosmos DB / ArangoDB** |
| 15 | Mobile offline-first, live sync | **Firestore / CouchDB** |
| 16 | "Drivers within 5 km", geofencing | **PostGIS + Redis GEO** |
| 17 | Cryptographic audit trail | **QLDB / immudb** |
| 18 | Event stream, replay, decouple services | **Kafka / Pulsar** |
| 19 | Event sourcing as source of truth | **EventStoreDB + projections** |
| 20 | Cheap storage of raw files at petabyte scale | **S3 / GCS (data lake)** |
| 21 | ACID + time travel on lake files | **Delta Lake / Iceberg** |
| 22 | SQL across S3 + Postgres + MySQL | **Trino / Athena** |
| 23 | Microsecond trading / billing OLTP | **SAP HANA / VoltDB** |
| 24 | Hot read cache in front of DB | **Redis / Memcached** |
| 25 | Images, video, PDFs, backups | **S3 + CDN** |
| 26 | Formal knowledge graphs, ontologies | **RDF triple store / Neptune** |
| 27 | Multi-party trust without central DB | **Hyperledger / blockchain** |
| — | Phone app, local SQL, no server | **SQLite** |
| — | Config / service discovery | **etcd / Consul** (KV) |

### OLTP vs OLAP one-liner

| Workload | Category | Pick |
|----------|----------|------|
| User clicks "Book seat" | OLTP | Postgres, Redis |
| CEO asks "revenue by city last quarter" | OLAP | BigQuery, ClickHouse |
| Engineer asks "p99 latency last hour" | Time-series | Prometheus |
| User searches "inception movie" | Search | Elasticsearch |
| AI asks "similar documents to this query" | Vector | pgvector, Pinecone |

### The one line interviewers want

> "I'll use **the right store per access pattern** — Postgres for transactions, Redis for speed, Cassandra for write scale, Elasticsearch for search, S3 for blobs, Kafka to connect them, and ClickHouse for analytics — not one database for everything."

---

## 🎯 Case Study — Nike-style Color Master Data (Real Document Walkthrough)

A real interview-style exercise. You're handed this document and asked: *"Design the storage and query layer."*

```json
{
  "_score": 0.8056386,
  "colorComments": "BLK DENIM BU01",
  "redNumber": 255,
  "modifier": "wcconversion@nike.com",
  "title": "color",
  "objectType": "COLOR",
  "modifyTimestamp": "2023-10-21T17:46:26Z",
  "createTimestamp": "2018-12-08T09:49:04Z",
  "division": ["10"],
  "colorPrimaryId": 10225,
  "greenNumber": 255,
  "state": 1,
  "UUID": "893467f2-2694-5f9b-8a07-efd881242522",
  "objectId": "10225",
  "changeTimestamp": "2023-10-21T17:46:26Z",
  "creator": "wcconversion@nike.com",
  "_docVersion": 1780422127357,
  "_status": {
    "cache": { "lastCachedDate": 1780422156514, "lastCachedDateStr": "2026-06-02T17:42:36.514Z" }
  }
}
```

### Step 1 — What this document actually is (read the fields)

| Clue | What it tells you |
|------|-------------------|
| `_score: 0.8056386` | **Elasticsearch/OpenSearch search hit** — only search engines return a relevance score at the document level |
| `UUID` + `objectId` + `objectType` | Generic **master data / PIM entity envelope** (Product Information Management) — same shape for COLOR, STYLE, MATERIAL, etc. |
| `colorPrimaryId`, `redNumber`, `greenNumber`, `colorComments` | Domain fields — this specific doc is a **color definition in a product catalog** |
| `creator` / `modifier` / `createTimestamp` / `modifyTimestamp` / `changeTimestamp` | **Audit trail** required by enterprise data governance |
| `_docVersion: 1780422127357` | **Optimistic concurrency token** (ms epoch) — used for ETag-style conditional updates |
| `_status.cache.lastCachedDate` | Document was served through a **read-through cache** layer in front of the store |
| `division: ["10"]` | **Multi-tenant / organizational scoping** — array means a doc can belong to multiple orgs |
| `state: 1` | Soft-delete / lifecycle flag (1 = active) |

**One-line summary:** this is a **master-data item** (color) from an enterprise PIM, served from Elasticsearch via a cache, with versioning and audit fields.

### Step 2 — Access patterns (always ask this first)

For PIM/master data at Nike-like scale:

| Pattern | Who | QPS | Latency SLA |
|---------|-----|-----|-------------|
| **Lookup by UUID / objectId** | Downstream apps | 10K–100K/s | < 10 ms p99 |
| **Full-text search** ("find colors matching 'denim'") | Internal tools, APIs | 100–1K/s | < 200 ms |
| **Filter by division + state + objectType** | Catalog browsing | 1K–10K/s | < 100 ms |
| **Point-in-time write with concurrency check** | Admin UI, bulk importers | 10–100/s | < 500 ms |
| **Audit — "all changes to this UUID"** | Compliance | low | seconds OK |
| **Analytics — "colors added per month per division"** | BI dashboards | low | seconds OK |

### Step 3 — The database choice (polyglot answer)

**Wrong answer:** "Put it all in Elasticsearch."
**Right answer:** Elasticsearch is the **query/serving layer**, not the system of record.

```
            ┌─────────────────────────────────────────────┐
            │  Admin UI / Importers (writes with version) │
            └──────────────────────┬──────────────────────┘
                                   ▼
         ┌─────────────────────────────────────────────────┐
         │  System of Record (SOR):                        │
         │     PostgreSQL  or  MongoDB  or  DynamoDB       │
         │   - ACID writes, strong UUID lookup             │
         │   - Enforces _docVersion check (OCC)            │
         │   - Full audit log table                        │
         └──────────┬──────────────────────┬───────────────┘
                    │                      │
                    ▼  (CDC via Debezium)  ▼
            ┌──────────────┐        ┌─────────────┐
            │   Kafka      │        │  Audit log  │
            │  (topic:     │        │  (append    │
            │  pim.color)  │        │   only)     │
            └──────┬───────┘        └─────────────┘
                   │
       ┌───────────┼───────────┬─────────────────┐
       ▼           ▼           ▼                 ▼
 ┌──────────┐ ┌────────┐ ┌──────────┐    ┌────────────┐
 │Elasticsrch│ │ Redis  │ │ClickHouse│    │  S3 (cold  │
 │ (search  │ │(cache  │ │(analytics│    │   backup / │
 │  + facets)│ │ by UUID│ │ GROUP BY)│    │  data lake)│
 └──────────┘ └────────┘ └──────────┘    └────────────┘
```

**Why each store:**
| Layer | Choice | Why |
|-------|--------|-----|
| **System of record** | **Postgres** (recommended) | Transactional writes, OCC via `_docVersion`, FK to related entities, cheap, operationally simple. MongoDB OK if schema varies wildly across `objectType`. DynamoDB OK if Nike is already AWS-native and needs massive write throughput. |
| **Search / facets** | **Elasticsearch** | The `_score` in the sample proves this is already the query layer. Full-text on `colorComments`, filters on `division`, `state`, `objectType`. |
| **Cache** | **Redis** | The `_status.cache` field is literal evidence. Cache by UUID with TTL; invalidate on CDC event. |
| **Analytics** | **ClickHouse / Snowflake** | "Colors added per month per division" — columnar aggregation. |
| **Audit** | **Append-only Postgres table** or **S3+Parquet** | Immutable history keyed by `(UUID, changeTimestamp)`. |
| **Cold archive** | **S3** | Entire JSON dumps for compliance / replay. |

### Step 4 — Concrete schemas in 4 databases

#### 4a. PostgreSQL (recommended SOR)

```sql
-- Core entity table (one row per master-data object across all types)
CREATE TABLE pim_object (
    uuid              UUID         PRIMARY KEY,
    object_type       TEXT         NOT NULL,          -- 'COLOR', 'STYLE', ...
    object_id         TEXT         NOT NULL,          -- '10225'
    title             TEXT,
    state             SMALLINT     NOT NULL DEFAULT 1,
    divisions         TEXT[]       NOT NULL DEFAULT '{}',
    payload           JSONB        NOT NULL,          -- type-specific fields
    doc_version       BIGINT       NOT NULL,          -- optimistic concurrency token
    creator           TEXT         NOT NULL,
    modifier          TEXT         NOT NULL,
    create_timestamp  TIMESTAMPTZ  NOT NULL,
    modify_timestamp  TIMESTAMPTZ  NOT NULL,
    change_timestamp  TIMESTAMPTZ  NOT NULL,
    CONSTRAINT uq_type_objid UNIQUE (object_type, object_id)
);

-- Fast lookups
CREATE INDEX idx_pim_type_state ON pim_object (object_type, state);
CREATE INDEX idx_pim_divisions   ON pim_object USING GIN (divisions);
CREATE INDEX idx_pim_payload     ON pim_object USING GIN (payload jsonb_path_ops);
CREATE INDEX idx_pim_modified    ON pim_object (modify_timestamp DESC);

-- Append-only audit (never UPDATE, only INSERT)
CREATE TABLE pim_object_history (
    uuid              UUID         NOT NULL,
    doc_version       BIGINT       NOT NULL,
    change_timestamp  TIMESTAMPTZ  NOT NULL,
    modifier          TEXT         NOT NULL,
    payload_before    JSONB,
    payload_after     JSONB        NOT NULL,
    PRIMARY KEY (uuid, doc_version)
) PARTITION BY RANGE (change_timestamp);

-- Optimistic concurrency UPDATE (fail if someone else wrote)
UPDATE pim_object
SET    payload = $1, doc_version = $2, modify_timestamp = now(),
       modifier = $3, change_timestamp = now()
WHERE  uuid = $4 AND doc_version = $5;    -- ← OCC guard
-- If 0 rows affected → 409 Conflict to client
```

#### 4b. Elasticsearch (search / serving)

```json
PUT /pim_color
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "color_text": { "type": "custom", "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"] }
      }
    }
  },
  "mappings": {
    "properties": {
      "UUID":             { "type": "keyword" },
      "objectType":       { "type": "keyword" },
      "objectId":         { "type": "keyword" },
      "colorPrimaryId":   { "type": "long" },
      "colorComments":    { "type": "text", "analyzer": "color_text",
                            "fields": { "raw": { "type": "keyword" } } },
      "title":            { "type": "text",
                            "fields": { "raw": { "type": "keyword" } } },
      "redNumber":        { "type": "short" },
      "greenNumber":      { "type": "short" },
      "blueNumber":       { "type": "short" },
      "division":         { "type": "keyword" },
      "state":            { "type": "byte" },
      "creator":          { "type": "keyword" },
      "modifier":         { "type": "keyword" },
      "createTimestamp":  { "type": "date" },
      "modifyTimestamp":  { "type": "date" },
      "changeTimestamp":  { "type": "date" },
      "_docVersion":      { "type": "long" }
    }
  }
}
```

**Example queries:**

```json
# 1. Full-text + filter + sort by freshness
POST /pim_color/_search
{
  "query": {
    "bool": {
      "must":   [ { "match": { "colorComments": "denim" } } ],
      "filter": [
        { "term":  { "objectType": "COLOR" } },
        { "term":  { "state": 1 } },
        { "terms": { "division": ["10", "20"] } }
      ]
    }
  },
  "sort": [ { "_score": "desc" }, { "modifyTimestamp": "desc" } ],
  "size": 20
}

# 2. Faceted navigation (counts per division)
POST /pim_color/_search
{ "size": 0,
  "query": { "term": { "state": 1 } },
  "aggs":  { "by_division": { "terms": { "field": "division", "size": 50 } } } }
```

**Why ES mapping choices matter:**
- `UUID`, `objectId`, `division` as `keyword` → exact-match filters, no analysis
- `colorComments` as `text` + `.raw` keyword subfield → both full-text and exact-match
- `redNumber` as `short` not `integer` → 2 bytes instead of 4 (billions of docs matter)
- Shards = 3 for a small master-data index — don't over-shard

#### 4c. MongoDB (if schema varies a lot across objectTypes)

```javascript
// Collection: pim_object (one collection for all object types)
db.pim_object.createIndex({ UUID: 1 }, { unique: true })
db.pim_object.createIndex({ objectType: 1, objectId: 1 }, { unique: true })
db.pim_object.createIndex({ objectType: 1, state: 1, modifyTimestamp: -1 })
db.pim_object.createIndex({ division: 1 })
db.pim_object.createIndex({ "colorComments": "text" })  // text index

// Optimistic concurrency update
db.pim_object.updateOne(
  { UUID: "893467f2-...", _docVersion: 1780422127357 },  // guard
  { $set: { colorComments: "BLK DENIM BU02",
            modifier: "jane@nike.com",
            modifyTimestamp: new Date(),
            _docVersion: Date.now() } }
)
// If matchedCount === 0 → version conflict
```

#### 4d. DynamoDB (if AWS-native, massive scale)

```
Table:  pim_object
PK:     UUID                       (partition key)
SK:     "META"                     (fixed — single item per UUID)

GSI1:   objectType-objectId-index
        PK = objectType  SK = objectId         # lookup by business ID

GSI2:   division-modifyTimestamp-index
        PK = division    SK = modifyTimestamp  # recent changes per division

Attributes: all document fields + docVersion (number)

Conditional update (OCC):
UpdateItem(
  Key = { UUID: "..." },
  UpdateExpression = "SET colorComments = :c, docVersion = :newv",
  ConditionExpression = "docVersion = :oldv"
)
# ConditionalCheckFailedException on version mismatch
```

**For search:** stream DynamoDB → Lambda → Elasticsearch (DynamoDB has no full-text search).

### Step 5 — The full write + read flow

**Write path (admin updates a color):**

```
1. Client PUT /colors/{uuid}, body + If-Match: "1780422127357"
2. API checks auth, loads current doc from Postgres
3. Optimistic UPDATE: WHERE uuid=? AND doc_version=?
   - 0 rows → 409 Conflict
   - 1 row  → success, new _docVersion = epoch_ms_now
4. INSERT into pim_object_history (immutable audit trail)
5. Debezium picks up Postgres WAL change → publishes to Kafka topic `pim.color`
6. Three consumers fan-out:
     - ES indexer:    upsert doc into pim_color index (version = _docVersion)
     - Cache invalidator: Redis DEL pim:color:{uuid}
     - Analytics loader:  append row to ClickHouse pim_changes table
7. Return 200 + new _docVersion to client
```

**Read path (API serves a color by UUID):**

```
1. GET /colors/{uuid}
2. Try Redis: GET pim:color:{uuid}
   HIT  → return (set _status.cache.lastCachedDate from stored value)
   MISS → GET from Elasticsearch (or Postgres for strict freshness)
          SET pim:color:{uuid} with TTL 10 min
          return
```

**Search path:**

```
GET /colors/search?q=denim&division=10&state=1
→ hits Elasticsearch directly
→ response includes _score per hit (that's where the sample's _score came from)
→ hydrate missing fields from Redis if needed
```

### Step 6 — Capacity sketch (what a senior candidate adds)

Assume Nike-scale PIM:
- **~5M master-data objects total**, ~1M colors
- **1 KB per doc** → ~5 GB total → fits in RAM on one Postgres box
- **Reads: ~50K QPS** (downstream apps hitting cache)
- **Writes: ~10/s** sustained, ~1K/s during bulk import
- **Search: ~500 QPS** peak

→ Postgres: 1 primary + 2 read replicas, boring and done
→ Redis: 3-node cluster, 10 GB RAM, 95%+ hit rate
→ ES: 3 data nodes, 3 shards × 2 replicas, under 10 GB per index
→ Kafka: 1 topic per objectType, 6 partitions each
→ CDC lag SLA: < 2 seconds p99 (Postgres → ES)

### Step 7 — Common interviewer follow-ups on this doc

1. *"How do you prevent two admins overwriting each other?"*
   → `_docVersion` is an OCC token. Client must send `If-Match: <version>`; server rejects with 409 if mismatched. Alternative: `SELECT ... FOR UPDATE` pessimistic lock — avoid, hurts throughput.
2. *"How does Elasticsearch stay in sync with Postgres?"*
   → **Debezium → Kafka → ES indexer** (CDC). Never dual-write from the app — that creates split-brain. Use `_docVersion` in ES `version_type: external` to make reindex idempotent and out-of-order safe.
3. *"Why not just use Elasticsearch as the system of record?"*
   → ES has weak durability guarantees vs Postgres, limited transactional support, segment merges can lose uncommitted writes on crash, and refresh model means reads can lag writes. Fine for search; wrong for SOR.
4. *"How do you support audit — 'show me every change to this UUID'?"*
   → Append-only `pim_object_history` table keyed by `(UUID, _docVersion)`, partitioned by month. Or event-sourcing style: Kafka topic is the source of truth, replay to rebuild state.
5. *"What's the cache invalidation strategy?"*
   → **Write-through cache with CDC invalidation**. On every Postgres change, Debezium emits event → consumer `DEL`s Redis key. Simpler than TTL-only. The `_status.cache.lastCachedDate` field in the sample is literally the observability for this.
6. *"division is an array. Any gotcha?"*
   → In Postgres use `TEXT[]` + GIN index. In ES use `keyword` (arrays work natively). In Mongo multikey index works. In DynamoDB arrays can't be partition keys — denormalize into multiple rows if you need per-division lookup.
7. *"How would you handle 100× more object types without redesigning?"*
   → Keep the envelope (`UUID`, `objectType`, `objectId`, `_docVersion`, audit fields) stable; put type-specific fields inside `payload` JSONB (Postgres) / document (Mongo). One `pim_object` table/collection; separate ES index per objectType for mapping flexibility.
8. *"How much does `_docVersion` as epoch-ms hurt?"*
   → Two writers in the same millisecond would collide. For Nike-scale writes it's fine, but a monotonic counter (`SELECT nextval`) or Postgres `xmin` is more correct. For global scale use a Snowflake ID or HLC.

### Step 8 — Red flags you'd call out in a review

| Flag | Risk | Fix |
|------|------|-----|
| Document shows cache metadata inline | Clients may trust stale cache timestamps | Keep `_status` server-side only, strip before returning |
| `_docVersion` is a wall-clock ms | Clock skew / dup writes | Use monotonic sequence or HLC |
| `creator`/`modifier` are plain strings | Can't rename users, no FK | Store user UUID instead; join at render time |
| `division` as string array | Loses hierarchy if divisions nest | Store as array of IDs + separate divisions table |
| No explicit `tenantId` | Multi-tenant leakage risk | Add `tenantId` as first index column and in every WHERE |

### Step 9 — The one-line interview answer

> "This is a search-indexed hit of a master-data entity. I'd keep **Postgres as the system of record** with an append-only history table, propagate changes via **Debezium → Kafka** to **Elasticsearch** (for the `_score` queries), **Redis** (for the sub-10ms UUID lookups the `_status.cache` field already proves they do), and **ClickHouse** for analytics. Writes use `_docVersion` as an **optimistic concurrency token**. One SOR, many purpose-built query layers — classic polyglot persistence."

---

## Appendix A: CAP + Consistency Levels — All Systems

| System | Type | Default | Strong option |
|--------|------|---------|---------------|
| PostgreSQL | Relational | CP (single leader) | Sync replica |
| MySQL / Aurora | Relational | CP | Aurora multi-AZ sync |
| Cassandra | Wide-column | AP | QUORUM, LWT |
| MongoDB | Document | CP (primary) | Write concern majority |
| Redis | Key-value cache | CP (single primary) | Wait + AOF fsync |
| DynamoDB | Key-value | AP | `ConsistentRead=true` |
| Elasticsearch | Search | AP | N/A |
| Neo4j | Graph | CP (cluster) | Causal cluster |
| Spanner | NewSQL | CP (global) | Default |
| CockroachDB | NewSQL | CP | Serializable default |
| Cosmos DB | Multi-model | Tunable | Strong / bounded staleness |
| Kafka | Event log | CP (per partition) | `acks=all` |
| Firestore | Real-time sync | CP (per doc) | Transactions (limited) |
| ClickHouse | OLAP | Eventual | N/A |
| S3 | Object storage | CP (durability) | Read-after-write (new objects) |

## Appendix B: How They're Built — Storage Engine Map

| Storage engine | Used by | Optimized for |
|----------------|---------|---------------|
| B-Tree | Postgres, MySQL InnoDB, SQLite | Balanced read/write, range scans |
| LSM-Tree | Cassandra, RocksDB, DynamoDB, LevelDB | Write-heavy append |
| Columnar | ClickHouse, Parquet, BigQuery | Analytics aggregations |
| Inverted index | Elasticsearch, Lucene | Full-text search |
| HNSW / IVF | Vector DBs | Approximate nearest neighbor |
| Geohash + R-Tree | PostGIS, Redis GEO | Spatial queries |
| Merkle tree + chain | QLDB, blockchain | Verifiable history |
| Log-structured | Kafka, WAL everywhere | Sequential writes, replay |

## Appendix C: Interview — "Name all database types"

**30-second answer:**

> "Broadly: **OLTP** — relational, document, key-value, wide-column, graph, multi-model.
> **OLAP** — warehouses and columnar engines like ClickHouse.
> **Specialized** — time-series, search, vector, spatial.
> **Immutable** — ledgers, event logs, event sourcing.
> **Storage layers** — object storage for blobs, data lakes for raw files, lakehouse formats on top.
> In practice every large system uses **polyglot persistence** — right DB per access pattern, connected by Kafka or CDC."

---

*Built for HLD interview prep — all 27 database and storage types with internals, scenarios, and tradeoffs.*
