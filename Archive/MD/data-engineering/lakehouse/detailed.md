# Data Lakehouse — Detailed Guide

> **One sentence:** A **lakehouse** keeps cheap **object storage** (S3/ADLS) as the main store but adds **table layers** (Delta Lake, Iceberg, Hudi) so you get **ACID transactions**, **time travel**, and **schema evolution**—warehouse discipline on a data lake budget.

---

## Concepts

### Lake vs warehouse vs lakehouse

| | **Data lake** | **Warehouse** | **Lakehouse** |
|---|---------------|---------------|---------------|
| Storage | Cheap objects (Parquet files) | Proprietary / managed | Objects + **table format** |
| ACID | No (eventually consistent mess) | Yes | **Yes** (per table format) |
| Workloads | Spark ML, raw dumps | SQL BI | **Both** |
| Cost | Lowest $/TB | Higher | Middle |

### Why Parquet alone is not enough

Raw Parquet folders:

- No atomic **multi-file commit** → readers see half-written job output.
- **UPDATE/DELETE** painful (rewrite many files).
- No standard **schema evolution** story.

**Table formats** fix this with a **metadata layer** (transaction log or manifest).

### The big three formats

| Format | Origin | Notes |
|--------|--------|-------|
| **Delta Lake** | Databricks | `_delta_log`, tight Spark integration |
| **Apache Iceberg** | Netflix | Engine-neutral, hidden partitioning |
| **Apache Hudi** | Uber | Incremental processing, record-level |

All sit on **Parquet** (usually) under the hood.

---

## Deep dive

### Transaction log (Delta mental model)

```text
s3://bucket/orders/
  part-000.parquet
  part-001.parquet
  _delta_log/
    00000000000000000000.json
    00000000000000000001.json
```

Each log entry describes **add/remove files**—readers see **snapshot** at commit boundary.

### Iceberg snapshots

**Manifest list** → manifest files → data files. **Snapshot id** for time travel:

```sql
SELECT * FROM orders VERSION AS OF 12345;
-- or timestamp travel (engine-dependent)
```

### Operations you care about

| Op | What happens |
|----|----------------|
| **Append** | New files, new commit |
| **Overwrite partition** | Replace `dt=2026-10-26` atomically |
| **MERGE** | Upsert by key (CDC gold standard) |
| **OPTIMIZE / compact** | Small files → fewer larger files |
| **VACUUM** | Remove old files no longer referenced |

### Partitioning vs hidden partitioning (Iceberg)

**Hive-style** `dt=2026-10-26/` — user must filter correctly.

**Hidden partitioning** — Iceberg derives partition from transform (`day(event_time)`)—fewer foot-guns in queries.

### Time travel & audit

- Debug “what did table look like before bad deploy?”
- **Reproducible** ML training snapshots.
- Compliance: prove **what was stored** at date X.

Retention: old snapshots consume storage until **expire** policy runs.

---

## Advanced

### Concurrent writers

Table format uses **optimistic concurrency**—two jobs conflict if they touch same files; one retries. Design jobs to **partition** writes.

### Schema evolution

Add column, change nullability (with care), **rename** (Iceberg/Delta features vary). **Breaking** changes need coordinated producer/consumer rollout.

### Streaming upserts

Flink/Spark Structured Streaming **MERGE** into Delta/Iceberg—**silver** layer from Kafka CDC.

### Z-order / clustering (Delta)

Co-locate related columns in files for **data skipping**—massive win for selective queries on huge tables.

### Unity Catalog / Glue / Polaris

**Governance** layer: catalog, ACLs, lineage—not a replacement for Iceberg, but **where** table metadata lives in enterprise.

---

## High scale

### Small file problem

Streaming ingest → thousands of 1MB files → metadata explosion + slow lists.

**Fix:** scheduled **compaction** (AUTO OPTIMIZE), target file size, **bin-packing**.

### Table maintenance SLOs

| Job | Frequency |
|-----|-----------|
| Compact | Hourly/daily |
| Expire snapshots | Weekly |
| Rewrite manifests (Iceberg) | As needed |

### Query engines on same table

Iceberg’s pitch: **Spark, Trino, Flink, Snowflake** read same table—avoid **copy** to warehouse for every use case (reality: still some duplication for BI concurrency).

### Cost

Storage cheap; **LIST** operations and **metadata** size matter at billions of files. Compaction is **non-optional** at scale.

---

## FAANG insights

1. **One copy of truth on object storage** — Warehouses as **compute** attached to lake (Snowflake external tables, BigQuery BigLake patterns).
2. **Medallion on lakehouse** — Bronze/silver/gold as **separate tables**, not separate silos.
3. **MERGE is the CDC endgame** — Binlog → Kafka → **MERGE** silver/gold.
4. **Test compaction** in staging—bad compact job can **block** writers.
5. **Lineage + ACL at catalog** — Table format doesn’t replace **who can read PII**.

**Interview angles:**

- Why not plain Parquet?
- ACID on S3—how?
- Delta vs Iceberg tradeoffs?
- Small files symptom and fix?

**Labs:** [etl-pipeline-lab](../../mini-projects/etl-pipeline-lab/), [spark-batch-lab](../../mini-projects/spark-batch-lab/).

**Related:** [data-engineering-fundamentals.md](../data-engineering-fundamentals.md), [spark-pyspark/detailed.md](../spark-pyspark/detailed.md).
