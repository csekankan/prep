# Data Engineering & Big Data — Staff Engineer Reference

> From raw bytes to reliable data products at petabyte scale.
> Architecture decisions, system internals, trade-offs, and production patterns.
> Read top-to-bottom once; use as a reference thereafter.

---

## Table of Contents

1. [Data Engineering Mental Model](#1-data-engineering-mental-model)
2. [Storage Foundations](#2-storage-foundations)
3. [File Formats](#3-file-formats)
4. [Batch Processing — Spark](#4-batch-processing--spark)
5. [Stream Processing — Kafka & Flink](#5-stream-processing--kafka--flink)
6. [Data Warehouse Architecture](#6-data-warehouse-architecture)
7. [Data Lakehouse — Delta Lake / Iceberg / Hudi](#7-data-lakehouse)
8. [Pipelines & Orchestration — Airflow](#8-pipelines--orchestration--airflow)
9. [Data Modeling](#9-data-modeling)
10. [dbt — Analytics Engineering](#10-dbt--analytics-engineering)
11. [Distributed Systems Fundamentals](#11-distributed-systems-fundamentals)
12. [Query Engines](#12-query-engines)
13. [Data Quality & Observability](#13-data-quality--observability)
14. [CDC & Replication](#14-cdc--replication)
15. [Real-Time Analytics](#15-real-time-analytics)
16. [Cloud Data Platforms](#16-cloud-data-platforms)
17. [Security & Governance](#17-security--governance)
18. [Performance & Cost Optimisation](#18-performance--cost-optimisation)
19. [Enterprise Data Architecture](#19-enterprise-data-architecture)
20. [Critical Papers & Systems Cheat-Sheet](#20-critical-papers--systems-cheat-sheet)
21. [Glossary](#21-glossary)

---

## 1. Data Engineering Mental Model

### What Data Engineers Actually Build

```
Raw Data Sources          Ingestion             Storage              Serving
─────────────────         ─────────             ───────              ───────
Operational DBs    ──►    CDC / ETL    ──►    Data Lake      ──►   Dashboards
Event Streams      ──►    Kafka        ──►    Data Warehouse ──►   ML Features
APIs / SaaS        ──►    Batch Pull   ──►    Feature Store  ──►   Ad-hoc SQL
Logs / Metrics     ──►    Streaming    ──►    Data Mart      ──►   Downstream APIs
Files / Uploads    ──►    Landing Zone ──►    OLAP Cube      ──►   Reports
```

### The Three V's (and Three More)

```
Volume:    how much data (GB → TB → PB → EB)
Velocity:  how fast it arrives (batch daily → near-real-time → streaming <1s)
Variety:   structured (SQL), semi-structured (JSON/Avro), unstructured (text/images)

Veracity:  how trustworthy (quality, completeness, consistency)
Value:     does it answer business questions?
Variability: does schema/volume change unpredictably?
```

### ETL vs ELT

```
ETL (Extract-Transform-Load):
  Transform BEFORE loading into the warehouse
  Use when: target is expensive to query (old MPP warehouses)
  Tools: Informatica, Talend, custom Spark jobs

ELT (Extract-Load-Transform):
  Load raw → transform INSIDE the warehouse with SQL
  Use when: target is cheap to compute (Snowflake, BigQuery, Redshift)
  Tools: Fivetran (EL) + dbt (T)

Modern recommendation: ELT for most cases
  - Raw data preserved (replayable)
  - SQL skills available in more teams
  - Warehouse compute is cheap and scalable
```

### Lambda vs Kappa Architecture

```
Lambda Architecture (Nathan Marz, 2011):
  Batch Layer:   recompute everything periodically (high accuracy, high latency)
  Speed Layer:   process recent data with streaming (low latency, approximate)
  Serving Layer: merge batch views + speed layer views

  Problem: two codepaths to maintain (batch Spark + streaming Kafka/Flink)
           same business logic written twice, divergence over time

Kappa Architecture (Jay Kreps, 2014):
  Single streaming layer for everything
  Reprocessing = replay Kafka topic from beginning with new job
  Serving Layer: real-time views only

  Problem: reprocessing large datasets via streaming is slow
           some computations are fundamentally batch (ML training)

Reality: most enterprises run a hybrid
  Streaming for: near-real-time dashboards, fraud detection, alerting
  Batch for:     large historical computations, ML training, complex joins
```

---

## 2. Storage Foundations

### Object Storage (S3 / GCS / ADLS)

The de-facto data lake storage. Cheap, durable, scalable.

```
Properties:
  Durability:    99.999999999% (11 9s) — 3+ copies across AZs
  Availability:  99.99%
  Cost:          ~$0.023/GB/month (S3 Standard)
  Throughput:    3,500 PUT/s and 5,500 GET/s per prefix (S3)
  Latency:       first byte ~10-20ms (vs <1ms for local disk)

Key concepts:
  Bucket:        top-level namespace (globally unique for S3)
  Prefix:        "path" (S3 is flat key-value, prefix mimics folders)
  Eventual consistency: S3 is strongly consistent since Dec 2020
  Storage classes: Standard → Intelligent-Tiering → Standard-IA → Glacier

S3 performance tips:
  - Randomise prefixes to distribute across partitions (pre-2018)
    Now unnecessary — strong consistency + no prefix hot spots
  - Enable S3 Transfer Acceleration for cross-region uploads
  - Use S3 Select to filter data server-side (reduce data transfer)
  - Multipart upload for objects > 100MB (parallelise, resume on failure)
  - Request Pays: requester pays for data egress (useful for public datasets)
```

### HDFS vs Object Storage

```
HDFS (Hadoop Distributed File System):
  - Data locality: compute moves to data (Hadoop MapReduce era)
  - 128MB blocks, 3× replication by default
  - NameNode: metadata (single point of failure → HA NameNode)
  - DataNode: actual data blocks
  - Strong consistency
  - Good: iterative processing with local reads
  - Bad: scaling storage separately from compute, cloud cost

Object Storage (modern):
  - Compute and storage separated (scale independently)
  - No data locality → network is the bottleneck
  - Mitigated by: fast networking (100Gbps+), vectorised reads, columnar formats
  - Cloud-native, virtually unlimited scale
  - Good: cost, durability, scalability, cloud integration
  - Bad: latency-sensitive workloads, small file problem

Migration: Databricks, EMR moved workloads from HDFS to S3
           Spark on S3 is now the default pattern
```

### Storage Hierarchy (Data Lake Zones)

```
Landing / Raw Zone:
  - Exact copy of source data, compressed
  - Never modified, append-only
  - Format: source format (JSON, CSV, Avro) → compressed (gzip, snappy)
  - Retention: 7 years (compliance)

Bronze / Cleaned Zone:
  - Parsed, typed, deduplicated
  - Schema validated
  - Partitioned by ingest date
  - Format: Parquet or Delta Lake

Silver / Enriched Zone:
  - Business logic applied: joins, aggregations, business keys
  - Conformed dimensions
  - Format: Delta Lake / Iceberg

Gold / Serving Zone:
  - Aggregated, purpose-built for specific use cases
  - Data marts, feature tables
  - Format: Delta Lake / Iceberg (or loaded into warehouse)

Naming conventions:
  s3://company-data-lake/
    landing/source=salesforce/entity=opportunities/year=2026/month=04/day=07/
    bronze/domain=crm/table=opportunities/year=2026/month=04/
    silver/domain=crm/table=opportunities/
    gold/domain=revenue/table=monthly_arr/
```

---

## 3. File Formats

### Format Comparison

```
┌──────────────┬──────────┬──────────┬────────────┬──────────┬─────────────┐
│ Format       │ Encoding │ Schema   │ Splittable │ Col-Push │ Best Use    │
├──────────────┼──────────┼──────────┼────────────┼──────────┼─────────────┤
│ CSV          │ Row      │ None     │ Yes*       │ No       │ Interchange │
│ JSON/JSONL   │ Row      │ None     │ JSONL only │ No       │ APIs, logs  │
│ Avro         │ Row      │ Embedded │ Yes        │ No       │ Kafka msgs  │
│ Parquet      │ Column   │ Embedded │ Yes        │ Yes      │ Analytics   │
│ ORC          │ Column   │ Embedded │ Yes        │ Yes      │ Hive/Hudi   │
│ Delta Lake   │ Column   │ Embedded │ Yes        │ Yes      │ Lakehouse   │
│ Iceberg      │ Column   │ Embedded │ Yes        │ Yes      │ Lakehouse   │
└──────────────┴──────────┴──────────┴────────────┴──────────┴─────────────┘
```

### Parquet — The Analytics Format

```
Columnar storage: values for a column stored contiguously
  Row format:    [id=1, name="Alice", age=30] [id=2, name="Bob", age=25]
  Column format: [id: 1,2] [name: "Alice","Bob"] [age: 30,25]

Why columnar wins for analytics:
  SELECT age, sum(revenue) FROM orders WHERE status = 'completed'
  → reads only 2 of 50 columns → 96% less I/O
  → values of same type → better compression
  → SIMD vectorised operations on column batches

Parquet internals:
  File → Row Group (128MB default) → Column Chunk → Pages (1MB default)
  
  Row Group footer: min/max stats per column → predicate pushdown
  Dict encoding: map repeated values to integers (good for low cardinality)
  RLE: run-length encoding for repeated values / booleans
  Delta encoding: store differences (good for monotonic IDs/timestamps)
  ZSTD compression: better ratio than Snappy at ~same speed (preferred)

Reading: read only columns needed + skip row groups via stats
  "I need age > 50" → skip row groups where max(age) ≤ 50

File size recommendation:
  128MB–1GB per Parquet file (not too small, not too large)
  Small files → high metadata overhead, many S3 requests
  Large files → slow partial reads, long recovery on failure
```

### Avro — The Streaming Format

```
Row-based, schema-embedded
Schema stored in file header (or separately in Schema Registry)

Avro schema (JSON):
{
  "type": "record",
  "name": "Order",
  "namespace": "com.example",
  "fields": [
    {"name": "id",       "type": "string"},
    {"name": "user_id",  "type": "string"},
    {"name": "amount",   "type": "double"},
    {"name": "status",   "type": {"type": "enum", "name": "Status",
                                  "symbols": ["PENDING","COMPLETED","FAILED"]}},
    {"name": "created_at", "type": {"type": "long", "logicalType": "timestamp-millis"}},
    {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}],
                         "default": null}   # nullable field
  ]
}

Why Avro for Kafka:
  Compact binary (no field names per row)
  Schema evolution: add fields with defaults, remove optional fields
  Works with Schema Registry for contract enforcement
```

### Schema Evolution Rules

```
Avro/Protobuf/Parquet compatibility levels:
  BACKWARD:  new schema can read old data
             → add fields with defaults, remove optional fields
  FORWARD:   old schema can read new data
             → add optional fields, remove fields with defaults
  FULL:      both backward + forward compatible
             → add fields with defaults only

Breaking changes (always avoid):
  Rename a field
  Change a field's type (int → string)
  Remove a required field
  Add a required field without default

Safe changes:
  Add a new optional field with a default value
  Rename by adding alias (Avro alias, Protobuf reserved)
  Widen a type (int → long in some systems)
```

---

## 4. Batch Processing — Spark

### Spark Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Spark Application                         │
│                                                                  │
│  ┌─────────────┐                                                 │
│  │   Driver    │   SparkContext / SparkSession                   │
│  │             │   Builds DAG of transformations                 │
│  │  DAGScheduler│  Splits into stages at shuffle boundaries      │
│  │  TaskScheduler│ Dispatches tasks to executors                 │
│  └──────┬──────┘                                                 │
│         │ (via Cluster Manager)                                  │
│  ┌──────▼──────────────────────────────────────────────────┐    │
│  │                  Cluster Manager                          │    │
│  │         (YARN / Kubernetes / Standalone / Mesos)          │    │
│  └──────┬──────────────────────────────────────────────────┘    │
│         │                                                        │
│  ┌──────▼──────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Executor 1  │  │  Executor 2  │  │  Executor N  │            │
│  │  [Task][Task]│  │  [Task][Task]│  │  [Task][Task]│            │
│  │  Memory:     │  │  Memory:     │  │  Memory:     │            │
│  │  Storage 60% │  │  Storage 60% │  │  Storage 60% │            │
│  │  Execution 40│  │  Execution 40│  │  Execution 40│            │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### RDD vs DataFrame vs Dataset

```
RDD (Resilient Distributed Dataset):
  - Low-level API, immutable distributed collection
  - No schema, no optimisation
  - Use only for low-level control or non-tabular data
  - Fault-tolerant via lineage (recompute from source)

DataFrame:
  - Distributed table with named, typed columns
  - Catalyst optimiser: query planning, predicate pushdown, join reordering
  - Tungsten execution engine: code generation, off-heap memory
  - Python/Scala/Java/R APIs (same performance — optimiser runs on JVM)

Dataset (Scala/Java):
  - Type-safe DataFrame (compile-time checks)
  - Same optimiser as DataFrame
  - Not available in Python (PySpark)

Recommendation: Always use DataFrame/SQL API
```

### Spark Execution Model

```
Transformation vs Action:
  Transformations: lazy — build the DAG (filter, select, join, groupBy, withColumn)
  Actions:         trigger execution — run the DAG (count, collect, write, show)

DAG → Stages → Tasks:
  Stage boundary: whenever a shuffle is required (groupBy, join, repartition)
  Task:           one partition processed by one executor core

Partition = unit of parallelism:
  Default parallelism: spark.sql.shuffle.partitions (default 200, usually too high)
  Reading: determined by file size, block size, HDFS splits
  After shuffle: spark.sql.shuffle.partitions
  Target: 128MB–512MB per partition (sweet spot)
```

### Spark Optimisations — Production Must-Knows

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("production-job") \
    .config("spark.sql.shuffle.partitions", "400") \
    .config("spark.sql.adaptive.enabled", "true")         # AQE
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
    .config("spark.sql.adaptive.skewJoin.enabled", "true")
    .config("spark.sql.files.maxPartitionBytes", "134217728")  # 128MB
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    .getOrCreate()
```

**Adaptive Query Execution (AQE) — Spark 3.x:**
```
AQE re-optimises the query plan at runtime using actual partition statistics:
  1. Coalesce shuffle partitions: merge small partitions after shuffle
  2. Convert sort-merge join → broadcast join if one side fits in memory
  3. Skew join optimisation: split large partitions automatically

Enable always: spark.sql.adaptive.enabled = true
```

**Broadcast Join (most important optimisation):**
```python
# If one table is small (<200MB by default), Spark broadcasts it to all executors
# No shuffle needed for the small table

# Automatic: Spark does this if table < spark.sql.autoBroadcastJoinThreshold
# Manual hint:
from pyspark.sql.functions import broadcast

result = large_df.join(broadcast(small_df), "key")

# spark.sql.autoBroadcastJoinThreshold = 10MB (default)
# Increase carefully: large broadcasts → executor OOM
```

**Partitioning:**
```python
# Repartition: full shuffle, produces exactly N equal partitions
df = df.repartition(200, "date")    # partition by column (puts same keys together)

# Coalesce: no shuffle, reduces partitions by merging
df = df.coalesce(50)                # use to reduce partitions before write

# Sort within partitions (avoids global sort)
df = df.repartition(200, "user_id").sortWithinPartitions("timestamp")

# Check skew
df.groupBy(F.spark_partition_id()).count().orderBy("count", ascending=False).show()
```

**Caching:**
```python
# Cache when reusing a DataFrame multiple times
df.cache()                              # MEMORY_AND_DISK
df.persist(StorageLevel.MEMORY_ONLY)   # choose level explicitly
df.unpersist()                         # release when done

# Check if it's worth caching:
# Yes: if reused 3+ times and fits in memory
# No: if used once, or computation is trivial (cache overhead > recompute cost)
```

**Window Functions:**
```python
from pyspark.sql.window import Window

# Most recent event per user
w = Window.partitionBy("user_id").orderBy(F.desc("event_time"))
df = df.withColumn("rank", F.row_number().over(w)) \
       .filter(F.col("rank") == 1)

# Running total per category
w_cumulative = Window.partitionBy("category") \
                     .orderBy("date") \
                     .rowsBetween(Window.unboundedPreceding, Window.currentRow)
df = df.withColumn("cumulative_sales", F.sum("sales").over(w_cumulative))

# 7-day rolling average
w_rolling = Window.partitionBy("store_id") \
                  .orderBy(F.col("date").cast("long")) \
                  .rangeBetween(-7 * 86400, 0)   # 7 days in seconds
df = df.withColumn("rolling_avg_7d", F.avg("revenue").over(w_rolling))
```

**Handling Skew (the #1 production problem):**
```python
# Salting: add random prefix to skewed keys to distribute across partitions
SALT_FACTOR = 50

# Skewed side: replicate key with salt
df_large = df_large.withColumn("salt", (F.rand() * SALT_FACTOR).cast("int")) \
                   .withColumn("key_salted", F.concat("key", F.lit("_"), "salt"))

# Small side: explode key to all salt values
from pyspark.sql.functions import explode, array
df_small = df_small.withColumn("salt", explode(array([F.lit(i) for i in range(SALT_FACTOR)]))) \
                   .withColumn("key_salted", F.concat("key", F.lit("_"), "salt"))

result = df_large.join(df_small, "key_salted").drop("salt", "key_salted")

# AQE skew join (Spark 3+): automatic, no manual salting needed
# spark.sql.adaptive.skewJoin.enabled = true
# spark.sql.adaptive.skewJoin.skewedPartitionFactor = 5
```

**Writing Optimally:**
```python
# Write Parquet partitioned by date
df.write \
  .mode("overwrite") \
  .partitionBy("year", "month", "day") \
  .option("compression", "zstd") \
  .option("maxRecordsPerFile", 1_000_000) \   # limit file size
  .parquet("s3://bucket/table/")

# For Delta Lake:
df.write \
  .format("delta") \
  .mode("overwrite") \
  .option("overwriteSchema", "true") \
  .partitionBy("date") \
  .save("s3://bucket/delta/orders/")

# Dynamic partition overwrite (only replace partitions present in data)
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
df.write.mode("overwrite").partitionBy("date").parquet("s3://bucket/table/")
```

### Spark on Kubernetes

```yaml
# Submit Spark job to Kubernetes
spark-submit \
  --master k8s://https://k8s-api-server:443 \
  --deploy-mode cluster \
  --name my-spark-job \
  --class com.example.MyJob \
  --conf spark.executor.instances=20 \
  --conf spark.kubernetes.container.image=my-spark:3.5.0 \
  --conf spark.kubernetes.namespace=spark-jobs \
  --conf spark.kubernetes.executor.deleteOnTermination=true \
  --conf spark.kubernetes.driver.pod.name=my-spark-job-driver \
  --conf spark.executor.memory=8g \
  --conf spark.executor.cores=4 \
  --conf spark.driver.memory=4g \
  local:///opt/spark/jars/my-job.jar
```

---

## 5. Stream Processing — Kafka & Flink

### Apache Kafka — The Backbone

```
┌─────────────────────────────────────────────────────────────────┐
│                      Kafka Cluster                               │
│                                                                  │
│  Topic: orders (partitions=12, replication_factor=3)             │
│                                                                  │
│  Partition 0: [msg0][msg1][msg2]...[msg1M]  → Broker 1 (Leader)│
│               └──────────────────────────── → Broker 2 (Follower│
│               └──────────────────────────── → Broker 3 (Follower│
│                                                                  │
│  Partition 1: [msg0][msg1]...               → Broker 2 (Leader) │
│  ...                                                             │
│                                                                  │
│  ZooKeeper (pre-3.x) or KRaft (3.x+): metadata, leader election │
└─────────────────────────────────────────────────────────────────┘
```

**Core Kafka Concepts:**
```
Topic:      named stream of records
Partition:  ordered, immutable log; unit of parallelism
Offset:     position within a partition (monotonically increasing)
Consumer Group: N consumers share partition assignment; each partition → 1 consumer
              → max parallelism = number of partitions
Replication: leader handles all reads/writes; followers replicate
ISR:         In-Sync Replicas — followers within replica.lag.time.max.ms
Retention:   by time (7 days default) or size; offsets persist past consumer reads
Compaction:  keep only latest record per key (for changelog / snapshot topics)
```

**Producer Configuration:**
```python
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'kafka-1:9092,kafka-2:9092,kafka-3:9092',
    
    # Durability
    'acks': 'all',                  # wait for all ISR to acknowledge
    'enable.idempotence': True,     # exactly-once at producer level
    'retries': 2147483647,          # retry forever (let timeout control)
    'max.in.flight.requests.per.connection': 5,  # idempotent: max 5
    
    # Performance
    'linger.ms': 5,                 # wait 5ms to batch messages
    'batch.size': 131072,           # 128KB batch size
    'compression.type': 'lz4',     # snappy | lz4 | zstd | gzip
    'buffer.memory': 33554432,      # 32MB producer buffer
    
    # Timeouts
    'delivery.timeout.ms': 120000,  # 2 minutes total retry window
    'request.timeout.ms': 30000,
})

def delivery_callback(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

producer.produce(
    topic='orders',
    key=order.id.encode(),          # key determines partition
    value=avro_serialise(order),    # Avro/JSON/Protobuf
    callback=delivery_callback
)
producer.poll(0)                    # trigger callbacks
producer.flush()                    # wait for all messages delivered
```

**Consumer Configuration:**
```python
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'kafka-1:9092',
    'group.id': 'order-processor-v1',
    
    # Offset management
    'enable.auto.commit': False,    # manual commit for at-least-once
    'auto.offset.reset': 'earliest', # start from beginning if no committed offset
    
    # Session management
    'session.timeout.ms': 30000,    # heartbeat must arrive within this
    'heartbeat.interval.ms': 3000,  # 1/3 of session.timeout
    'max.poll.interval.ms': 300000, # max time between polls (processing time)
    
    # Performance
    'fetch.min.bytes': 1024,        # wait for 1KB before returning
    'fetch.max.wait.ms': 500,
    'max.poll.records': 500,
})

consumer.subscribe(['orders'])

try:
    while True:
        messages = consumer.consume(num_messages=500, timeout=1.0)
        for msg in messages:
            if msg.error():
                handle_error(msg.error())
                continue
            process(msg)
        
        # Commit after successful processing (at-least-once)
        consumer.commit(asynchronous=False)
finally:
    consumer.close()
```

**Kafka Topic Design:**
```
Partition count:
  - More partitions = higher parallelism (consumer group throughput)
  - Recommendation: start with 12 or 24 (easy to scale consumers)
  - Rule: partitions >= max_consumers_in_group
  - Hard limit: ~4000 partitions per broker (ZooKeeper era), much higher with KRaft

Message key selection (determines partition):
  - Use business entity key (user_id, order_id) for ordering guarantees
  - Messages with same key go to same partition → ordered within key
  - Null key → round-robin distribution

Retention policy:
  log.retention.hours=168           # 7 days (default)
  log.retention.bytes=10737418240   # 10GB per partition
  log.cleanup.policy=compact        # for changelog topics (keeps latest per key)

Replication factor:
  rf=3 for production (tolerates 1 broker failure)
  min.insync.replicas=2 (ensures 2 ISRs acknowledge — used with acks=all)
```

### Apache Flink — Stateful Stream Processing

```
Flink concepts:
  DataStream: unbounded stream of events
  DataSet:    bounded batch (legacy — Flink 1.18+ uses unified API)
  Operator:   transformation on stream (map, filter, keyBy, window, join)
  Task:       unit of execution (operator or chain of operators)
  Slot:       unit of resource (one slot per parallelism unit)
  JobManager: coordinator (like Spark Driver)
  TaskManager: worker (like Spark Executor)
  State:      per-key or per-operator state persisted to checkpoint
  Checkpoint: snapshot of all state → S3/HDFS for fault tolerance
```

**Flink Python (PyFlink) Example:**
```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common import Duration

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(12)
env.enable_checkpointing(60000)   # checkpoint every 60s

# Read from Kafka with event-time watermarks
source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("orders") \
    .set_group_id("flink-order-processor") \
    .set_starting_offsets(KafkaOffsetsInitializer.committed_offsets()) \
    .set_value_only_deserializer(AvroDeserializer(Order)) \
    .build()

watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(10)) \  # 10s allowed lateness
    .with_timestamp_assigner(lambda e, _: e.event_time_ms)

stream = env.from_source(source, watermark_strategy, "Kafka Orders")

# Keyed windowed aggregation
result = stream \
    .key_by(lambda order: order.merchant_id) \
    .window(TumblingEventTimeWindows.of(Time.minutes(5))) \
    .aggregate(SumRevenue())  # custom AggregateFunction

# Write results
result.sink_to(kafka_sink)

env.execute("Order Revenue 5-min Windows")
```

**Time in Streaming (Critical Concept):**
```
Event Time:    time the event occurred (embedded in the record)
               → deterministic results regardless of processing order
               → requires watermarks to handle late data

Processing Time: time the event is processed by the system
               → non-deterministic (depends on lag, restarts)
               → simple, no watermarks needed

Ingestion Time: time Kafka received the event
               → middle ground

Watermark:     "I believe all events before T-delay have arrived"
               → triggers window computation
               → late events: process, discard, or send to side output

W(t) = max(event_time_seen) - allowed_lateness

If event arrives after watermark (late): routed to side output by default
```

**Flink State:**
```python
# ValueState: single value per key
class CountPerUser(KeyedProcessFunction):
    def open(self, runtime_context):
        self.count_state = runtime_context.get_state(
            ValueStateDescriptor("count", Types.INT())
        )
    
    def process_element(self, event, ctx):
        count = self.count_state.value() or 0
        count += 1
        self.count_state.update(count)
        yield (event.user_id, count)

# MapState: key-value store per key (for sessionisation)
# ListState: list per key
# ReducingState: automatically reduces values (running sum, max)

# State backend:
# HashMapStateBackend: in-memory (fast, limited by heap)
# EmbeddedRocksDBStateBackend: on-disk (handles TB of state, slower)
```

**Exactly-Once Semantics:**
```
Flink + Kafka: two-phase commit (2PC) for exactly-once end-to-end

Flink guarantees exactly-once internally via checkpoints
Kafka sink: FlinkKafkaProducer with Semantic.EXACTLY_ONCE
  - Kafka transactions used
  - On checkpoint: commit transaction
  - On failure: abort transaction, rollback to last checkpoint

Cost: increased latency (waits for checkpoint to commit)
      Kafka transaction timeout must exceed checkpoint interval

At-least-once: simpler, more common in practice
  - Checkpoint state, retry from last checkpoint on failure
  - Deduplicate downstream (idempotent writes, dedup keys)
```

### Kafka Streams (for simpler use cases)

```java
// Kafka Streams: embedded library, no separate cluster needed
StreamsBuilder builder = new StreamsBuilder();

KStream<String, Order> orders = builder.stream("orders");

// Stateful aggregation with local RocksDB state
KTable<Windowed<String>, Long> orderCounts = orders
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))
    .count(Materialized.as("order-counts-store"));

orderCounts.toStream()
    .map((key, count) -> KeyValue.pair(key.key(), count))
    .to("order-counts-output");

KafkaStreams streams = new KafkaStreams(builder.build(), config);
streams.start();

// Interactive queries: query local state store
ReadOnlyWindowStore<String, Long> store = streams.store(
    StoreQueryParameters.fromNameAndType("order-counts-store",
    QueryableStoreTypes.windowStore())
);
```

---

## 6. Data Warehouse Architecture

### OLTP vs OLAP

```
OLTP (Online Transaction Processing):
  - Transactional workloads: INSERT/UPDATE/DELETE
  - Row-oriented storage (fast single-row access)
  - Normalised schema (3NF) — minimise redundancy
  - Many small queries, high concurrency
  - Examples: PostgreSQL, MySQL, DynamoDB

OLAP (Online Analytical Processing):
  - Analytical workloads: aggregations over millions of rows
  - Column-oriented storage (fast columnar scans)
  - Denormalised schema (star/snowflake) — minimise joins
  - Few large queries, lower concurrency
  - Examples: Snowflake, BigQuery, Redshift, ClickHouse

You need both: OLTP for application, OLAP for analytics
Bridge: CDC (Debezium) or EL tools (Fivetran) from OLTP → OLAP
```

### MPP — Massively Parallel Processing

```
Shared-nothing architecture:
  Each node has its own CPU, memory, local disk (or network-attached storage)
  No shared resources between nodes (except the network)
  Scale-out: add nodes to increase capacity

Query execution:
  Query → distributed query plan → each node processes its slice of data
  Results aggregated at coordinator node

Distribution keys:
  Hash distribution: hash(key) % num_nodes → determines which node stores a row
  Round-robin: distribute evenly (no skew, but no co-location)
  Replicated: copy entire table to all nodes (for small dimension tables)

Colocation: if two tables are distributed on the same key, their joins
            are local (no data shuffled across network) → critical for performance

Snowflake: pure cloud, separates compute (virtual warehouses) from storage (S3)
BigQuery:  serverless, no cluster management; Dremel query engine; columnar
Redshift:  traditional MPP with RA3 nodes (compute + managed S3 storage)
```

### Star Schema Design

```
Fact table: business events (orders, page_views, transactions)
  - High row count (millions-billions)
  - Measures (numeric: revenue, quantity, duration)
  - Foreign keys to dimensions

Dimension table: descriptive attributes (customers, products, time, location)
  - Lower row count (thousands-millions)
  - Attributes used for filtering/grouping
  - Slowly Changing Dimensions (SCD)

Example star schema:
  fact_orders (order_id, customer_key, product_key, date_key, store_key,
               quantity, unit_price, discount, net_revenue)
  
  dim_customer (customer_key, customer_id, name, email, country, segment, signup_date)
  dim_product  (product_key, sku, name, category, brand, cost)
  dim_date     (date_key, date, year, quarter, month, week, day_of_week, is_holiday)
  dim_store    (store_key, store_id, name, city, state, country, region)
```

### Slowly Changing Dimensions (SCD)

```
SCD Type 1 — Overwrite:
  Update the row in place (lose history)
  Use: non-analytical changes, corrections
  
  dim_customer: customer_id=123, country="US" → UPDATE → country="CA"
  Query: current value only

SCD Type 2 — Versioned Rows (most common):
  Add new row with effective_date, is_current flag
  
  customer_key | customer_id | country | effective_from | effective_to  | is_current
  1            | 123         | US      | 2020-01-01     | 2023-06-14    | false
  2            | 123         | CA      | 2023-06-15     | 9999-12-31    | true
  
  Fact table points to customer_key at time of event → historical accuracy

SCD Type 3 — Add Previous Column:
  Add "previous_value" column
  Use: when only one prior value matters
  
  customer_key | country | previous_country | changed_date
  1            | CA      | US               | 2023-06-15

SCD Type 4 — History Table:
  Separate history table; current table has only latest values
  
SCD Type 6 — Hybrid (1+2+3):
  Most complex; has current value + historical rows + previous_value
```

---

## 7. Data Lakehouse

### The Problem with Data Lakes and Warehouses

```
Data Lake problems:
  - No ACID transactions (concurrent writes corrupt data)
  - No schema enforcement (swamp of inconsistent files)
  - No efficient upserts/deletes (must rewrite entire partition)
  - No time travel (can't query historical state)
  - Small file proliferation (streaming writes → millions of tiny files)

Data Warehouse problems:
  - Expensive to store all raw data
  - Vendor lock-in (proprietary format)
  - Limited support for ML workloads (unstructured data, Python access)
  - Full copy of data from lake (duplication, staleness)

Lakehouse = best of both:
  - Data lives in open format on object storage (lake economics)
  - ACID transactions, schema enforcement (warehouse reliability)
  - Supports BI SQL and ML workloads (unified)
```

### Delta Lake (Databricks)

```
Delta Lake adds a transaction log (_delta_log/) on top of Parquet files.

_delta_log/
  00000000000000000000.json   ← initial commit (table creation)
  00000000000000000001.json   ← add files
  00000000000000000002.json   ← delete files (tombstone)
  00000000000000000003.json   ← schema change
  00000000000000000010.checkpoint.parquet   ← snapshot every 10 commits

Each commit JSON records:
  add:     files added (with stats: min/max per column, row count)
  remove:  files logically deleted (soft delete, physical file remains)
  metaData: schema changes
  protocol: reader/writer requirements

Transaction protocol:
  1. Read current version
  2. Read + write data files
  3. Attempt to commit (check for conflicts)
  4. If conflict: retry or fail
```

**Delta Lake Operations:**
```python
from delta.tables import DeltaTable

# Upsert (MERGE) — idempotent, at-least-once safe
deltaTable = DeltaTable.forPath(spark, "s3://bucket/delta/orders/")

new_data = spark.createDataFrame(new_orders)

deltaTable.alias("target").merge(
    new_data.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdate(set={
    "status": "source.status",
    "updated_at": "source.updated_at"
}).whenNotMatchedInsertAll().execute()

# Time travel
df_yesterday = spark.read.format("delta") \
    .option("versionAsOf", 42) \
    .load("s3://bucket/delta/orders/")

df_yesterday = spark.read.format("delta") \
    .option("timestampAsOf", "2026-04-06") \
    .load("s3://bucket/delta/orders/")

# Optimize: compact small files into larger ones
deltaTable.optimize().executeCompaction()

# Z-ORDER: co-locate related data within files (multi-dimensional clustering)
deltaTable.optimize().executeZOrderBy("user_id", "event_time")

# Vacuum: remove files no longer referenced (respect retention window)
deltaTable.vacuum(retentionHours=168)   # 7 days

# History
deltaTable.history().show(20, truncate=False)
```

**Delta Lake Data Skipping:**
```
Every Parquet file has column-level statistics in the transaction log:
  min, max, null_count, num_records per column

Query: WHERE user_id = 'u-123' AND event_date = '2026-04-07'
  → scan transaction log (fast, in-memory)
  → skip files where max(user_id) < 'u-123' or min(user_id) > 'u-123'
  → read only relevant files

Z-ORDER clustering maximises data skipping effectiveness:
  Groups records with similar values of the Z-ORDER columns into the same files
  → much higher skip rate vs random file layout
```

### Apache Iceberg (Netflix, Apple)

```
Iceberg improvements over Delta:
  - Full schema evolution without rewrite (rename, reorder, type promotion)
  - Hidden partitioning: query without knowing partition columns
  - Partition evolution: change partitioning without rewrite
  - Multi-engine support: Spark, Trino, Flink, Hive, BigQuery, Snowflake
  - Row-level deletes: deletion vectors (don't rewrite data files)

Iceberg metadata:
  catalog → metadata.json → manifest list → manifest files → data files

Iceberg hidden partitioning:
  Table partitioned by months(event_time)
  Query: WHERE event_time BETWEEN '2026-01-01' AND '2026-04-07'
  → Iceberg automatically prunes to relevant month partitions
  → No need to filter on partition column explicitly

Partition evolution:
  Old partitioning: PARTITIONED BY (days(event_time))
  New partitioning: PARTITIONED BY (hours(event_time))
  Old data: still queryable with old partition spec
  New data: written with new partition spec
  No rewrite required!
```

**Delta vs Iceberg vs Hudi:**
```
┌──────────────────┬───────────────────┬───────────────────┬────────────────┐
│ Feature          │ Delta Lake        │ Apache Iceberg    │ Apache Hudi    │
├──────────────────┼───────────────────┼───────────────────┼────────────────┤
│ ACID             │ Yes               │ Yes               │ Yes            │
│ Time Travel      │ Version + ts      │ Version + ts      │ Point-in-time  │
│ Schema Evolution │ Limited           │ Full              │ Limited        │
│ Partition Evol.  │ No (replace all)  │ Yes               │ Partial        │
│ Engine Support   │ Spark-first       │ Multi-engine      │ Spark-first    │
│ Upsert Speed     │ Good              │ Good              │ Best (CoW/MoR) │
│ Streaming        │ Structured Stream │ Flink (native)    │ DeltaStreamer  │
│ Compaction       │ Manual OPTIMIZE   │ Manual/auto       │ Auto (async)   │
│ Best For         │ Databricks shops  │ Multi-engine/open │ CDC/upsert-heavy│
└──────────────────┴───────────────────┴───────────────────┴────────────────┘

Hudi table types:
  Copy-on-Write (CoW): rewrite Parquet files on upsert; fast reads, slow writes
  Merge-on-Read (MoR): write delta logs, merge at read time; fast writes, slower reads
```

---

## 8. Pipelines & Orchestration — Airflow

### Airflow Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       Airflow                                   │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Webserver  │  │ Scheduler  │  │  Triggerer │               │
│  │ (UI/API)   │  │ (DAG parse │  │ (async     │               │
│  │            │  │  + schedule│  │  sensors)  │               │
│  └────────────┘  └──────┬─────┘  └────────────┘               │
│                         │                                       │
│                   ┌─────▼──────┐                               │
│                   │  Metadata  │   PostgreSQL or MySQL          │
│                   │  Database  │   (DAG runs, task states,      │
│                   └─────┬──────┘    XComs, connections)         │
│                         │                                       │
│                   ┌─────▼──────┐                               │
│                   │   Message  │   Redis or RabbitMQ            │
│                   │   Broker   │   (task queue)                 │
│                   └─────┬──────┘                               │
│                         │                                       │
│  ┌──────────┐  ┌────────▼──┐  ┌──────────┐                    │
│  │ Worker 1  │  │ Worker 2  │  │ Worker N  │   Celery/K8s     │
│  └──────────┘  └───────────┘  └──────────┘                    │
└────────────────────────────────────────────────────────────────┘
```

### Production DAG Patterns

```python
from airflow import DAG
from airflow.decorators import task, dag
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta

# Default args applied to all tasks
default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": True,
    "email": ["data-alerts@company.com"],
    "execution_timeout": timedelta(hours=2),
    "depends_on_past": False,
}

@dag(
    dag_id="orders_etl",
    description="Load orders from S3 to Data Warehouse",
    schedule="0 6 * * *",              # 6am UTC daily
    start_date=datetime(2026, 1, 1),
    catchup=False,                     # don't backfill historical runs
    max_active_runs=1,                 # prevent concurrent runs
    default_args=default_args,
    tags=["orders", "production", "finance"],
    doc_md="""
    ## Orders ETL Pipeline
    Loads daily orders from S3 landing zone → Bronze → Silver → Gold
    **SLA**: Must complete by 8am UTC
    **Owner**: data-engineering@company.com
    """,
)
def orders_etl():
    
    # Sensor: wait for upstream data to land
    wait_for_data = S3KeySensor(
        task_id="wait_for_orders_file",
        bucket_name="company-landing",
        bucket_key="orders/{{ ds }}/orders_*.parquet",
        wildcard_match=True,
        poke_interval=300,             # check every 5 minutes
        timeout=7200,                  # fail after 2 hours
        mode="reschedule",             # release worker slot while waiting!
        soft_fail=False,
    )
    
    # Spark job on EMR/Glue
    bronze_load = GlueJobOperator(
        task_id="load_bronze",
        job_name="orders-bronze-load",
        script_args={
            "--date": "{{ ds }}",
            "--source_bucket": "company-landing",
            "--dest_bucket": "company-data-lake",
        },
        num_of_dpus=10,
        wait_for_completion=True,
    )
    
    # dbt model run
    @task
    def run_silver_models():
        from airflow.providers.dbt.cloud.hooks.dbt import DbtCloudHook
        hook = DbtCloudHook(dbt_cloud_conn_id="dbt_cloud")
        run = hook.trigger_job_run(
            job_id=12345,
            cause="Airflow: {{ ds }}",
        )
        hook.wait_for_job_run_status(run["data"]["id"], expected_statuses={"Success"})
    
    # Notification on success
    notify_success = SlackWebhookOperator(
        task_id="notify_success",
        slack_webhook_conn_id="slack_data_team",
        message=":white_check_mark: Orders ETL complete for {{ ds }}",
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )
    
    # Notification on failure
    notify_failure = SlackWebhookOperator(
        task_id="notify_failure",
        slack_webhook_conn_id="slack_data_team",
        message=":red_circle: Orders ETL FAILED for {{ ds }} — check Airflow",
        trigger_rule=TriggerRule.ONE_FAILED,
    )
    
    # Define dependencies
    wait_for_data >> bronze_load >> run_silver_models() >> [notify_success, notify_failure]

orders_etl()
```

**Airflow Best Practices:**
```python
# 1. Idempotency: re-running the same DAG run produces the same result
#    - Use partition overwrite, MERGE/UPSERT, not INSERT
#    - DELETE + INSERT is acceptable if wrapped in a transaction

# 2. Use TaskFlow API (@task) for Python tasks (cleaner than PythonOperator)

# 3. Don't put business logic in DAG file — import from library
#    DAG file should only define orchestration, not transformation

# 4. Use datasets / data-aware scheduling (Airflow 2.4+)
from airflow import Dataset

ORDERS_BRONZE = Dataset("s3://data-lake/bronze/orders/")
ORDERS_SILVER = Dataset("s3://data-lake/silver/orders/")

@dag(schedule=[ORDERS_BRONZE])   # trigger when bronze is updated
def silver_transform():
    @task(outlets=[ORDERS_SILVER])
    def transform():
        ...

# 5. Dynamic DAGs: generate DAGs programmatically for similar pipelines
for table in ["orders", "products", "customers"]:
    with DAG(f"load_{table}", ...) as dag:
        ...

# 6. Sensors: always use mode="reschedule" (not "poke") for long waits
#    poke: holds a worker slot the entire wait
#    reschedule: releases worker, checks periodically

# 7. XCom: only for small data (task metadata, not DataFrames!)
#    Large data: write to S3 or database, pass the path/key via XCom
```

### Alternatives to Airflow

```
Prefect 2.x:
  Python-native, dynamic workflows, excellent local dev experience
  Hybrid execution: agents run anywhere
  Better error handling than Airflow

Dagster:
  Asset-centric (thinks in data assets, not tasks)
  Built-in data quality, lineage, partitioning
  Strong type system
  Excellent for mature data teams

Temporal:
  Workflow engine (not just data pipelines)
  Durable execution: survives process failures
  Good for: long-running processes, microservice orchestration

Metaflow (Netflix):
  Data science workflows
  Tight AWS integration
  Version management built in

Recommendation:
  New team starting: Dagster (best developer experience)
  Large Airflow investment: stick with Airflow 2.x
  Complex business processes: Temporal
```

---

## 9. Data Modeling

### Kimball vs Inmon

```
Kimball (bottom-up):
  Build data marts for specific business areas first
  Integrate through conformed dimensions (common customer_key)
  Star schema, denormalised, fast queries
  Faster time-to-value, used in most organisations

Inmon (top-down):
  Enterprise Data Warehouse first (3NF, normalised)
  Data marts derived from EDW
  More consistent, harder to build, longer time-to-value

Modern approach: One Big Table (OBT) for simple use cases,
                 star schema for complex analytical workloads,
                 ELT + dbt for flexibility
```

### Data Vault 2.0

```
For highly audited, source-agnostic enterprise warehouses.
Three object types:

Hub:     business keys (customer_id, order_id) + hash key + load_date + source
         - Immutable, append-only
         - One hub per business concept

Link:    relationships between hubs (order-customer, order-product)
         - Foreign keys to hubs
         - Append-only (relationships may end, never deleted)

Satellite: descriptive attributes + context (history of values)
           - Attached to Hub or Link
           - Append-only, each row has load_date
           - Drives SCD Type 2 automatically

Benefits: parallel loads, full audit trail, source-agnostic, schema flexibility
Drawbacks: complex to query (many joins), requires business marts layer
```

### Grain Definition

```
"The grain defines what a single row in the fact table represents"

Getting grain wrong is the most common data modeling mistake.

Example:
  Grain: one row per order line item
  NOT: one row per order (different grain!)
  
  fact_order_lines:
    order_id, line_id, product_id, customer_id, quantity, unit_price
    → allows per-product analysis

  Mixing grains in one fact table is always wrong.
  Multiple grains → separate fact tables → joined in mart layer.

Factless fact table:
  Records events with no measures
  Example: student enrolled in course (no numeric measure)
  student_key, course_key, enroll_date
  → use COUNT to count enrollments
```

---

## 10. dbt — Analytics Engineering

### dbt Mental Model

```
dbt transforms raw data in your warehouse using SELECT statements.
It handles:
  - Materialisation (table, view, incremental, ephemeral)
  - Testing (not null, unique, accepted_values, referential integrity)
  - Documentation (auto-generated from schema.yml)
  - Lineage DAG (visual dependency graph)
  - Environments (dev, staging, production)
  - Modularity (ref() function creates dependencies)
```

### Project Structure

```
my_dbt_project/
├── dbt_project.yml          # project config, materialisation defaults
├── profiles.yml             # warehouse connections (usually ~/.dbt/profiles.yml)
├── packages.yml             # external packages (dbt_utils, dbt_expectations)
├── models/
│   ├── staging/             # 1:1 with source (rename, cast, light cleaning)
│   │   ├── _sources.yml     # define raw sources + freshness checks
│   │   ├── stg_orders.sql
│   │   └── stg_customers.sql
│   ├── intermediate/        # complex business logic, reusable components
│   │   ├── int_orders_enriched.sql
│   │   └── int_customer_lifetime_value.sql
│   ├── marts/               # purpose-built, consumer-facing
│   │   ├── finance/
│   │   │   ├── _schema.yml  # tests + documentation
│   │   │   ├── fct_revenue.sql
│   │   │   └── dim_customer.sql
│   │   └── marketing/
├── tests/                   # custom singular tests (SQL files)
├── macros/                  # reusable Jinja2 SQL macros
├── seeds/                   # static CSV data loaded to warehouse
├── snapshots/               # SCD Type 2 snapshots
└── analyses/                # ad-hoc SQL (compiled but not run)
```

### dbt Models

```sql
-- models/staging/stg_orders.sql
-- Materialised as VIEW by default

{{ config(materialized='view') }}

with source as (
    select * from {{ source('postgres', 'orders') }}
),
renamed as (
    select
        id::varchar                     as order_id,
        user_id::varchar                as customer_id,
        created_at::timestamp           as order_created_at,
        updated_at::timestamp           as order_updated_at,
        status::varchar                 as order_status,
        total_amount_cents / 100.0      as order_amount_usd,
        currency_code                   as currency,
        -- Standardise nulls
        nullif(trim(coupon_code), '')   as coupon_code,
        -- Loaded metadata
        _dbt_loaded_at
    from source
    where id is not null
)
select * from renamed
```

```sql
-- models/marts/finance/fct_revenue.sql
-- Materialised as TABLE for performance

{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='append_new_columns',
    cluster_by=['order_date'],
    partition_by={
        'field': 'order_date',
        'data_type': 'date',
        'granularity': 'day'
    }
) }}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where order_updated_at > (select max(order_updated_at) from {{ this }})
    {% endif %}
),
customers as (
    select * from {{ ref('dim_customer') }}
),
final as (
    select
        o.order_id,
        o.order_created_at::date        as order_date,
        o.customer_id,
        c.customer_segment,
        c.acquisition_channel,
        o.order_status,
        o.order_amount_usd,
        case
            when o.order_status = 'completed'  then o.order_amount_usd
            else 0
        end                             as recognised_revenue_usd,
        o.coupon_code,
        o.order_updated_at,
        current_timestamp()             as dbt_updated_at
    from orders o
    left join customers c on o.customer_id = c.customer_id
)
select * from final
```

### dbt Tests & Documentation

```yaml
# models/marts/finance/_schema.yml
version: 2

models:
  - name: fct_revenue
    description: "One row per order. Grain: order_id."
    meta:
      owner: "@finance-data"
      freshness_sla_hours: 24

    columns:
      - name: order_id
        description: "Unique order identifier from source system"
        tests:
          - not_null
          - unique

      - name: order_status
        tests:
          - accepted_values:
              values: ["pending", "completed", "cancelled", "refunded"]

      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_id

      - name: recognised_revenue_usd
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

    tests:
      # Row count check (custom singular test or dbt_expectations)
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          max_value: 10000000

sources:
  - name: postgres
    database: prod_db
    schema: public
    freshness:
      warn_after: {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    loaded_at_field: _loaded_at
    tables:
      - name: orders
        description: "Raw orders from Postgres operational DB (via Fivetran)"
```

**Macros:**
```sql
-- macros/generate_schema_name.sql (override dbt default)
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

-- macros/date_spine.sql
{% macro date_spine(start_date, end_date) %}
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date=start_date,
        end_date=end_date
    ) }}
{% endmacro %}
```

**dbt Snapshots (SCD Type 2):**
```sql
-- snapshots/dim_customer_snapshot.sql
{% snapshot dim_customer_snapshot %}
{{
    config(
        target_schema='snapshots',
        strategy='timestamp',
        unique_key='customer_id',
        updated_at='updated_at',
    )
}}
select * from {{ source('postgres', 'customers') }}
{% endsnapshot %}
-- dbt creates: dbt_scd_id, dbt_updated_at, dbt_valid_from, dbt_valid_to, dbt_is_current
```

---

## 11. Distributed Systems Fundamentals

### CAP Theorem

```
In a distributed system, you can only guarantee 2 of 3:
  Consistency:   every read sees the most recent write
  Availability:  every request gets a response (not necessarily latest data)
  Partition Tolerance: system continues operating despite network partitions

Network partitions WILL happen → real choice is CP vs AP

CP (Consistency + Partition Tolerance): HBase, ZooKeeper, etcd
  → on partition: system rejects reads/writes rather than return stale data

AP (Availability + Partition Tolerance): Cassandra, DynamoDB, CouchDB
  → on partition: system continues, may return stale data

CA (Consistency + Availability): PostgreSQL, MySQL (single node)
  → not partition tolerant: acceptable for single-node or same-AZ

Modern nuance (PACELC theorem): even without partition, you trade
latency vs consistency (Cassandra: low latency but eventual consistency)
```

### ACID Properties

```
Atomicity:    transaction completes fully or not at all (no partial writes)
Consistency:  database invariants maintained before/after transaction
Isolation:    concurrent transactions don't see each other's intermediate state
Durability:   committed transactions survive crashes (WAL / fsync)

Isolation levels (weakest to strongest):
  Read Uncommitted: can see dirty reads (other txn's uncommitted data)
  Read Committed:   no dirty reads; default in PostgreSQL, Oracle
  Repeatable Read:  same query returns same results within txn; default MySQL InnoDB
  Serialisable:     transactions execute as if serial; prevents all anomalies

Anomalies:
  Dirty read:       read uncommitted data that may be rolled back
  Non-repeatable:   read same row twice, see different values
  Phantom read:     read same range twice, see different rows
  Write skew:       two txns read same data, write to different rows based on stale read
```

### BASE vs ACID

```
BASE (distributed NoSQL databases):
  Basically Available:  system guarantees availability
  Soft state:           state may change without input (due to replication)
  Eventual Consistency: given enough time, all replicas converge

Trade-off: higher availability and scalability, at cost of strong consistency

When to use:
  ACID: financial transactions, inventory (correctness critical)
  BASE: social feeds, product recommendations, analytics (availability critical)
```

### Consistent Hashing

```
Problem: with N servers, how to distribute keys such that
         adding/removing a server only remaps k/N keys?

Naive hash: key % N → adding server remaps almost all keys

Consistent hashing:
  1. Map servers to a ring of 0-2³²
  2. Each key maps to the nearest server clockwise
  3. Add server: only keys between new server and predecessor move
  4. Remove server: only keys of removed server move to successor

Virtual nodes (vnodes): each physical server maps to many ring positions
  → balances load better when nodes have different capacity
  → Cassandra uses 256 vnodes per server by default
```

### Data Replication

```
Synchronous replication:
  Leader waits for follower acknowledgment before confirming write
  Pros: no data loss on leader failure
  Cons: write latency = max(leader, follower) latency
  
Asynchronous replication:
  Leader confirms write without waiting for follower
  Pros: low write latency
  Cons: data loss if leader fails before follower catches up

Semi-synchronous:
  Wait for at least 1 follower (MySQL default)
  Balance between safety and latency

Replication lag:
  Follower may be seconds/minutes behind leader
  Reading from follower may return stale data
  Mitigation: read-your-writes (route user's reads to leader after their write)
              monotonic reads (route to same replica for a session)
```

### Partitioning (Sharding)

```
Range partitioning: partition by key range (A-M, N-Z)
  Pros: range queries efficient
  Cons: hot spots if access is skewed (all users with name starting with "A")

Hash partitioning: hash(key) → partition
  Pros: even distribution
  Cons: range queries scan all partitions

Directory-based: lookup table maps keys to partitions
  Pros: flexible (can rebalance without rehashing)
  Cons: lookup table is a bottleneck / single point of failure

Secondary index partitioning:
  Local index: each partition indexes its own data (scatter-gather for queries)
  Global index: partitioned by index term (write to multiple partitions)
```

---

## 12. Query Engines

### Presto / Trino Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Trino Cluster                                │
│                                                                 │
│  ┌────────────────┐                                             │
│  │  Coordinator   │  Parses SQL, builds query plan,            │
│  │                │  schedules stages to workers               │
│  └───────┬────────┘                                             │
│          │                                                      │
│  ┌───────▼────┐  ┌────────────┐  ┌────────────┐               │
│  │  Worker 1  │  │  Worker 2  │  │  Worker N  │               │
│  │  Stage 1   │  │  Stage 1   │  │  Stage 1   │               │
│  │  Stage 2   │  │  Stage 2   │  │  Stage 2   │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│                                                                 │
│  Connectors: Hive (S3/HDFS), Iceberg, Delta, PostgreSQL,       │
│              Kafka, Elasticsearch, MongoDB, Cassandra, BigQuery │
└───────────────────────────────────────────────────────────────┘

Trino is memory-bound: spills to disk for large queries
Exchange: data moved between stages via HTTP (no disk)
Pipelining: stages execute concurrently, pipeline between them
```

**ClickHouse — OLAP at Scale:**
```sql
-- ClickHouse: columnar, vectorised, single-node can do billions of rows/second

-- MergeTree: primary table engine
CREATE TABLE orders
(
    order_id     String,
    customer_id  String,
    event_date   Date,
    amount       Decimal(18,2),
    status       LowCardinality(String)     -- dictionary encoding for low-cardinality
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (customer_id, event_date)          -- primary sort key (sparse index)
SETTINGS index_granularity = 8192;          -- rows per index mark

-- ReplicatedMergeTree for HA
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/orders', '{replica}')

-- AggregatingMergeTree: materialised aggregations
-- CollapsingMergeTree: efficient upserts (sign column)
-- SummingMergeTree: pre-aggregate on insert (for metrics)

-- Extremely fast for: time-series, web analytics, ad-tech, monitoring
-- Not good for: OLTP, complex JOINs, frequent updates
```

**DuckDB — In-Process OLAP:**
```python
import duckdb

# Query Parquet/CSV/JSON directly from S3 — no server needed
conn = duckdb.connect()

# Query S3 Parquet with predicate pushdown
result = conn.execute("""
    SELECT 
        date_trunc('month', order_date) as month,
        sum(amount) as total_revenue,
        count(*) as num_orders
    FROM read_parquet('s3://bucket/orders/year=2026/month=04/*.parquet')
    WHERE status = 'completed'
    GROUP BY 1
    ORDER BY 1
""").df()

# Register in-memory DataFrames
conn.register("my_df", pandas_df)
result = conn.execute("SELECT * FROM my_df WHERE amount > 100").df()

# Copy to Parquet
conn.execute("COPY (SELECT ...) TO 'output.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")

# Great for: local analytics, replacing pandas for large files, CI pipeline testing
```

---

## 13. Data Quality & Observability

### Data Quality Dimensions

```
Completeness:  are all expected records present? (no missing rows)
Accuracy:      do values reflect reality? (correct values)
Consistency:   do values agree across systems? (A=B in all sources)
Timeliness:    is data fresh enough for use? (SLA met)
Validity:      do values conform to rules? (valid email, date in range)
Uniqueness:    are there duplicate records?
Integrity:     are referential constraints satisfied? (FK exists)
```

### Great Expectations (Python)

```python
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

context = ge.get_context()

# Define expectations
validator = context.get_validator(
    batch_request=RuntimeBatchRequest(
        datasource_name="spark_datasource",
        data_connector_name="runtime_data_connector",
        data_asset_name="orders",
        runtime_parameters={"batch_data": orders_df},
        batch_identifiers={"run_id": "2026-04-07"},
    ),
    expectation_suite_name="orders.critical",
)

validator.expect_column_to_exist("order_id")
validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_be_unique("order_id")
validator.expect_column_values_to_be_between("amount", min_value=0, max_value=100000)
validator.expect_column_values_to_be_in_set("status", ["pending","completed","cancelled"])
validator.expect_column_pair_values_a_to_be_greater_than_b(
    "updated_at", "created_at"
)
validator.expect_table_row_count_to_be_between(min_value=1000, max_value=10_000_000)

# Run validations
results = validator.validate()
if not results["success"]:
    # Alert, fail pipeline
    raise Exception(f"Data quality check failed: {results}")
```

### Soda Core / Monte Carlo — Data Observability

```yaml
# soda scan (soda-core): SQL-based data quality checks
checks for orders:
  - row_count > 0
  - missing_count(order_id) = 0
  - unique_count(order_id) = row_count
  - invalid_count(status) = 0:
      valid values: [pending, completed, cancelled, refunded]
  - min(amount) >= 0
  - max(amount) < 1000000
  - freshness(updated_at) < 24h
  - schema:
      name: Expected order columns
      fail:
        when required column missing:
          - order_id
          - customer_id
          - amount
```

**Monte Carlo / Bigeye / Acceldata — Automated Anomaly Detection:**
```
ML-based data observability:
  - Detect volume drops/spikes (orders table has 20% fewer rows than yesterday)
  - Detect distribution shifts (revenue values shifted by 2σ)
  - Schema change alerts (new column, column type changed)
  - Freshness monitoring (table not updated in 25 hours vs expected 24)
  - Lineage: downstream impact of data quality issues

Key metrics tracked:
  Row count over time
  Null rate per column
  Distinct value count (cardinality)
  Min/max/mean/stddev of numeric columns
  Distribution of categorical columns
```

### Data Lineage

```
Column-level lineage: track which source columns contribute to each output column
  Tools: OpenLineage (standard), Marquez (server), Datahub, Amundsen, Atlas

OpenLineage integration (Spark):
  spark.extraListeners = io.openlineage.spark.agent.OpenLineageSparkListener
  spark.openlineage.transport.url = http://marquez:5000/api/v1/lineage

Benefits:
  Impact analysis: if this column changes, what dashboards break?
  Root cause: which source caused this quality issue?
  Compliance: where does this PII data flow?
  Debugging: why does this metric look wrong?
```

---

## 14. CDC & Replication

### Change Data Capture (CDC)

```
CDC captures row-level changes in a database and streams them as events.

Methods:
  Query-based (polling): SELECT * WHERE updated_at > last_run
    Pros: simple, no DB access needed
    Cons: misses deletes, high DB load, depends on updated_at column

  Log-based (WAL): read database transaction log (WAL/binlog/redo log)
    Pros: captures inserts+updates+deletes, no DB load, no column dependency
    Cons: requires DB permissions, more complex setup
    Tools: Debezium (open source), AWS DMS, Fivetran, Airbyte
```

**Debezium (Kafka Connect):**
```json
// PostgreSQL source connector (reads WAL)
{
  "name": "postgres-orders-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres.prod.internal",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${file:/etc/kafka/connect-creds.properties:db.password}",
    "database.dbname": "production",
    "database.server.name": "prod-postgres",
    "plugin.name": "pgoutput",                    // replication plugin
    "table.include.list": "public.orders,public.customers",
    "slot.name": "debezium_slot",
    "publication.autocreate.mode": "filtered",
    
    // Schema registry
    "key.converter": "io.confluent.kafka.serializers.KafkaAvroSerializer",
    "value.converter": "io.confluent.kafka.serializers.KafkaAvroSerializer",
    "key.converter.schema.registry.url": "http://schema-registry:8081",
    "value.converter.schema.registry.url": "http://schema-registry:8081",
    
    // Heartbeat (prevent WAL accumulation when no changes)
    "heartbeat.interval.ms": "60000",
    
    // Snapshot: initial load of existing data
    "snapshot.mode": "initial"     // initial | always | never | exported
  }
}
```

**Debezium Event Format:**
```json
{
  "before": {"order_id": "ord-123", "status": "pending", "amount": 99.99},
  "after":  {"order_id": "ord-123", "status": "completed", "amount": 99.99},
  "op": "u",          // c=create, u=update, d=delete, r=read(snapshot)
  "ts_ms": 1712447432000,
  "source": {
    "db": "production",
    "table": "orders",
    "lsn": 12345678   // WAL log position
  }
}
```

**Processing CDC Events with Flink:**
```python
# Convert CDC stream to Delta Lake upserts
orders_cdc_stream \
    .filter(lambda e: e["op"] in ["c", "u", "d"]) \
    .map(transform_cdc_to_delta_record) \
    .sink_to(DeltaLakeSink("s3://lake/orders/", merge_key="order_id"))
```

---

## 15. Real-Time Analytics

### Lambda Architecture with Pinot / Druid

```
Real-time OLAP (RTOLAP) stores:
  - Sub-second queries on freshly ingested data
  - Columnar, pre-aggregated indexes
  - Trade: less flexible (pre-defined aggregations) for speed

Apache Pinot:
  Real-time segment: queries in-memory ingested from Kafka (seconds fresh)
  Offline segment: compact, indexed historical data from S3
  Star-tree index: pre-aggregated multi-level rollup for ultra-fast aggregations

Apache Druid:
  Similar to Pinot, strong at time-series rollups
  Excellent for: web analytics, ad impressions, monitoring dashboards

ClickHouse (also RTOLAP):
  Can ingest from Kafka via Kafka Engine table
  Better for: ad-hoc queries, less pre-schema required
```

### Feature Store

```
Problem: ML models need features computed in real-time (for inference)
         and historically (for training). Two paths, often divergent.

Feature Store unifies:
  Offline store: historical feature values (Parquet/Delta on S3)
  Online store:  latest feature values for low-latency serving (Redis, DynamoDB)
  Feature pipeline: computes + writes to both stores simultaneously

Feast (open source):
  feature_repo/
    feature_store.yaml
    features.py         # feature views + entities
    
  from feast import FeatureStore
  fs = FeatureStore("feature_repo/")
  
  # Historical training data
  training_df = fs.get_historical_features(
      entity_df=entities_with_timestamps,
      features=["user_features:lifetime_orders", "user_features:avg_order_value"]
  ).to_df()
  
  # Online inference
  features = fs.get_online_features(
      features=["user_features:lifetime_orders"],
      entity_rows=[{"user_id": "u-123"}]
  ).to_dict()

Tecton / Hopsworks: managed feature stores for production ML
```

---

## 16. Cloud Data Platforms

### AWS Data Stack

```
Ingestion:
  Kinesis Data Streams:   real-time streaming (Kafka alternative, managed)
  Kinesis Firehose:       EL to S3/Redshift/ES without consumers
  AWS DMS:                database migration + CDC
  Glue:                   serverless ETL (Spark-based), crawlers for cataloguing
  AppFlow:                SaaS → S3/Redshift connectors (Salesforce, etc.)

Storage:
  S3:                     data lake (all raw data here)
  Redshift:               MPP data warehouse, RA3 = compute+managed-storage
  RDS Aurora:             OLTP, Postgres/MySQL compatible
  DynamoDB:               NoSQL, key-value, millisecond latency

Processing:
  EMR:                    managed Hadoop/Spark/Flink cluster
  Glue Spark:             serverless Spark (no cluster management)
  Athena:                 serverless Trino (query S3 directly)
  Lambda:                 serverless function (for small transformations)

Orchestration:
  MWAA (Managed Airflow): managed Airflow
  Step Functions:         AWS-native workflow orchestration
  EventBridge:            event-driven triggers

Catalogue & Governance:
  Glue Data Catalog:      Hive Metastore for S3
  Lake Formation:         column-level access control, row filters
  Macie:                  PII detection in S3

BI:
  QuickSight:             managed BI (less powerful than Looker/Tableau)
```

### GCP Data Stack

```
Ingestion:      Pub/Sub (Kafka-managed), Dataflow (Beam), Data Fusion
Storage:        GCS (object), BigQuery (warehouse+lake), Bigtable (NoSQL), Spanner (OLTP)
Processing:     Dataproc (managed Spark), Dataflow (Apache Beam, serverless)
Orchestration:  Cloud Composer (managed Airflow), Workflows
Catalogue:      Dataplex, Data Catalog
BI:             Looker (GA), Looker Studio

BigQuery specifics:
  Serverless: no cluster management, pay per byte scanned
  Columnar storage (Capacitor format), Dremel query engine
  Separation of storage and compute (Editions: Standard/Enterprise/Enterprise+)
  Slots: unit of compute (1 slot = 1 vCPU); reservations or on-demand
  Partitioning: ingestion time or column-based (DATE, TIMESTAMP, INTEGER)
  Clustering: sorted index within partitions (up to 4 columns)
  INFORMATION_SCHEMA: query job history, slot utilisation
  BQML: run ML models in SQL
  External tables: query GCS/Bigtable/Drive without loading
```

### Snowflake Architecture

```
Three-layer architecture:
  Storage:  centralised columnar storage (Snowflake-managed S3/GCS/Azure)
  Compute:  Virtual Warehouses (isolated Spark-like clusters, auto-suspend)
  Services: metadata, query optimisation, access control, transactions

Virtual Warehouses:
  XS(1 server), S(2), M(4), L(8), XL(16), 2XL(32), ...
  Auto-suspend: pause after N minutes idle (no charge when paused)
  Auto-resume: on first query
  Multi-cluster: auto-scale out for concurrent users (Enterprise+)
  Cost: credits/hour, 1 credit ≈ $2-4 depending on cloud/region

Key features:
  Zero-copy cloning: instant copy (no data copied, share storage) → dev/test from prod
  Time Travel: query historical data (1-90 days)
  Fail-safe: 7-day emergency recovery (Snowflake-managed, not user-accessible)
  Data sharing: share data with other Snowflake accounts without copying
  External tables: query S3/GCS/Azure files via Snowpipe
  Snowpipe: micro-batch loading from S3 (triggered by SQS/SNS)
  Streams: CDC on Snowflake tables (track changes)
  Tasks: scheduled SQL execution (like a simple cron)
  Materialized views: auto-maintained, query optimizer uses transparently
```

---

## 17. Security & Governance

### Column-Level Security

```sql
-- Snowflake: dynamic data masking
CREATE MASKING POLICY mask_email AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ANALYST', 'DATA_SCIENTIST') THEN
      REGEXP_REPLACE(val, '(^[^@]+)', '***')  -- hide local part
    WHEN CURRENT_ROLE() = 'ENGINEER' THEN val  -- show full
    ELSE '***REDACTED***'
  END;

ALTER TABLE customers MODIFY COLUMN email
SET MASKING POLICY mask_email;

-- Row-Level Security
CREATE ROW ACCESS POLICY region_access AS (region_col VARCHAR) RETURNS BOOLEAN ->
  'DATA_ADMIN' = CURRENT_ROLE()
  OR region_col = CURRENT_USER()  -- or from a mapping table
  OR EXISTS (SELECT 1 FROM region_access_map
             WHERE user = CURRENT_USER() AND region = region_col);

ALTER TABLE sales ADD ROW ACCESS POLICY region_access ON (region);
```

### PII Management

```python
# Detect and tag PII before loading
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymise_column(text: str) -> str:
    results = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=results).text

# Pseudonymisation: replace PII with consistent token (reversible with key)
import hashlib, hmac

def pseudonymise(value: str, secret_key: bytes) -> str:
    return hmac.new(secret_key, value.encode(), hashlib.sha256).hexdigest()[:16]

# Tokenisation: replace with random token, lookup table in secure vault
# Generalisation: age=34 → age_bucket="30-39"
# Suppression: remove the column entirely

# PII tagging in data catalog:
# - Tag columns with PII classifications (email, phone, SSN, credit_card)
# - Enforce access control based on tags
# - Audit access to tagged columns
```

### Data Mesh

```
Principle 1 — Domain Ownership:
  Each business domain (orders, inventory, customers) owns its data products
  Domain teams are responsible for quality, SLAs, documentation
  No central data team bottleneck

Principle 2 — Data as a Product:
  Data is treated like a product (discoverable, usable, trustworthy)
  Data product contract: schema, SLA, ownership, quality guarantees
  Published to data catalog (Datahub, Alation, Atlan)

Principle 3 — Self-Serve Data Platform:
  Platform team provides infrastructure (catalog, pipeline framework, quality tooling)
  Domain teams use self-serve tools (no tickets to data engineering)

Principle 4 — Federated Computational Governance:
  Global policies (PII, access control, lineage) applied automatically
  Local autonomy within global boundaries

When to apply:
  Large orgs (200+ engineers) with multiple business domains
  Central data team becoming bottleneck
  Need for domain expertise in data products
  NOT for: small teams (overhead > benefit)
```

---

## 18. Performance & Cost Optimisation

### Partitioning Strategy

```
Partition by the column most commonly used for filtering:
  Time-based: date, year/month/day (most common for analytics)
  Entity-based: region, country (for geo-filtered queries)
  Status: rarely (low cardinality → too few partitions)

Partition pruning: query planner skips partitions not matching WHERE clause
  Works only if WHERE clause uses partition column directly
  DOES NOT work: WHERE DATE(created_at) = '2026-04-07' (function on column)
  WORKS:         WHERE created_at >= '2026-04-07' AND created_at < '2026-04-08'

Partition granularity:
  Too coarse (year): partitions too large, limited pruning
  Too fine (hour): partition overhead, too many small files
  Sweet spot: day for most datasets, month for large ones

Hive-style partitions on S3:
  s3://bucket/table/year=2026/month=04/day=07/file.parquet
  ← Spark, Athena, Trino infer partition columns from path
```

### Small File Problem

```
Problem: thousands of small files (KB-sized) → high metadata overhead
  - S3: each LIST/GET is a request (cost + latency)
  - Parquet: file footer (schema, stats) overhead per file
  - Spark: one task per file → too many tasks, task overhead dominates

Causes:
  - Streaming writes (Kafka → S3 every few minutes)
  - Spark writing too many partitions (200 partitions × many jobs)
  - Poorly tuned repartition

Solutions:
  1. Compaction job: read many small files, write fewer large ones
     spark.read.parquet("s3://...").coalesce(100).write.parquet("s3://...")
  
  2. Delta Lake OPTIMIZE:
     OPTIMIZE table ZORDER BY (date, user_id);
  
  3. Tune shuffle partitions:
     spark.sql.shuffle.partitions = 200   # default; reduce for small datasets
  
  4. Auto-compaction (Delta Lake):
     delta.autoCompact.enabled = true
     delta.targetFileSize = 134217728     # 128MB

Target file size: 128MB–1GB per file
```

### Query Optimisation (SQL)

```sql
-- BAD: function on indexed/partition column prevents pruning
WHERE YEAR(order_date) = 2026

-- GOOD: range filter on raw column
WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01'

-- BAD: SELECT * (reads all columns, all Parquet column chunks)
SELECT * FROM orders WHERE customer_id = 'c-123'

-- GOOD: project only needed columns
SELECT order_id, amount, status FROM orders WHERE customer_id = 'c-123'

-- BAD: DISTINCT on large table (expensive dedup)
SELECT DISTINCT customer_id FROM orders

-- GOOD: if approximation OK
SELECT APPROX_COUNT_DISTINCT(customer_id) FROM orders   -- HyperLogLog

-- BAD: correlated subquery (N+1 pattern)
SELECT *, (SELECT MAX(amount) FROM orders o2 WHERE o2.customer_id = o.customer_id)
FROM orders o

-- GOOD: window function (single pass)
SELECT *, MAX(amount) OVER (PARTITION BY customer_id) as max_order
FROM orders

-- BAD: implicit cross join
SELECT * FROM a, b WHERE a.id = b.id   -- ambiguous, easy to make cross join

-- GOOD: explicit join
SELECT * FROM a INNER JOIN b ON a.id = b.id

-- Materialise intermediate results (avoid recomputing)
WITH expensive_cte AS MATERIALIZED (   -- Postgres hint; Snowflake: automatic
    SELECT customer_id, SUM(amount) as ltv
    FROM orders WHERE status = 'completed'
    GROUP BY 1
)
SELECT ...

-- Use EXPLAIN ANALYZE to understand the query plan
EXPLAIN ANALYZE SELECT ...
```

### Data Skew Mitigation

```sql
-- Identify skewed keys
SELECT customer_id, COUNT(*) as cnt
FROM orders
GROUP BY 1
ORDER BY cnt DESC
LIMIT 20;

-- Salting in SQL (for Spark SQL or Presto)
-- Broadcast join (Snowflake, BigQuery automatically optimise)
-- ClickHouse: pre-aggregate + distributed join settings

-- Snowflake: search optimisation service for high-cardinality columns
ALTER TABLE orders ADD SEARCH OPTIMIZATION ON EQUALITY(customer_id);
```

### Cost Per Query Optimisation (Snowflake/BigQuery)

```sql
-- BigQuery: partition expiry (auto-delete old partitions)
ALTER TABLE orders SET OPTIONS (
  partition_expiration_days = 365
);

-- BigQuery: cached results (1000% free, 24h TTL)
-- Avoid: ORDER BY without LIMIT (sorts everything), SELECT * on wide tables

-- Snowflake: query result cache (24h, free if data unchanged)
-- Snowflake: cluster keys (like Z-ORDER for tables)
ALTER TABLE orders CLUSTER BY (DATE_TRUNC('day', order_date), customer_id);

-- Snowflake: materialized views (auto-refresh, query optimizer uses transparently)
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT DATE_TRUNC('day', order_date) as day, SUM(amount) as revenue
FROM orders GROUP BY 1;
```

---

## 19. Enterprise Data Architecture

### Modern Data Stack Reference Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE DATA PLATFORM                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Data Sources                                   │   │
│  │  Postgres/MySQL   SaaS (Salesforce, Stripe)   Kafka Streams     │   │
│  │  Mobile Events    Web Clickstream              Third-party APIs  │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                              │                                          │
│  ┌───────────────────────────▼──────────────────────────────────────┐  │
│  │                    Ingestion Layer                                 │  │
│  │  Fivetran/Airbyte (SaaS EL)  │  Debezium CDC  │  Kafka Connect  │  │
│  │  Kafka + Schema Registry     │  Event Collector (Segment/Rudder) │  │
│  └───────────────────────────┬──────────────────────────────────────┘  │
│                               │                                         │
│  ┌────────────────────────────▼─────────────────────────────────────┐  │
│  │                    Data Lake (S3/GCS)                              │  │
│  │  Landing: raw, immutable, compressed                               │  │
│  │  Bronze:  parsed, typed, partitioned (Delta Lake/Iceberg)         │  │
│  │  Silver:  business logic, enriched, conformed                     │  │
│  │  Gold:    aggregated, purpose-built marts                         │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────▼────────────────────────────────────┐  │
│  │                 Transformation Layer (dbt)                         │  │
│  │  Staging models → Intermediate → Marts (Finance/Marketing/Product)│  │
│  │  Tests, Documentation, Lineage, Version Control (Git)             │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                 │                                       │
│  ┌──────────────────────────────▼───────────────────────────────────┐  │
│  │                 Serving Layer                                      │  │
│  │  ┌────────────────┐ ┌───────────────┐ ┌──────────────────────┐  │  │
│  │  │ Data Warehouse  │ │  Feature Store│ │ Real-Time OLAP       │  │  │
│  │  │ (Snowflake/BQ)  │ │  (Feast/Tecton│ │ (Pinot/Druid/CH)     │  │  │
│  │  └────────────────┘ └───────────────┘ └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               Platform Services                                  │    │
│  │  Airflow/Dagster (orchestration)   OpenLineage (lineage)        │    │
│  │  Great Expectations (quality)      Monte Carlo (observability)  │    │
│  │  Datahub/Alation (catalog)         Terraform (IaC for infra)    │    │
│  └────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

### SLAs for Data Products

```
Data SLA = Freshness + Completeness + Accuracy + Availability

Example SLA (orders data product):
  Freshness:     available in Silver layer within 2 hours of creation
  Completeness:  >99.9% of source orders present
  Accuracy:      reconciles with source within 0.01% on revenue totals
  Availability:  queryable 99.9% of the time (schema doesn't break)

Measure and alert on:
  Table last updated timestamp
  Row count vs yesterday (±20%)
  Revenue reconciliation vs source (nightly)
  Null rate on critical columns
  Schema drift detection
```

### Data Contract

```yaml
# data-contract.yaml — enforced by schema registry / dbt tests
data_contract_version: 0.9.3
id: orders-v1
info:
  title: Orders Data Product
  version: 2.1.0
  owner: data-engineering@company.com
  status: active

terms:
  usage: "Internal analytics and ML. Not for production transactional use."
  billing_unit: "per 1TB query scanned"
  sla: "Available by 08:00 UTC, 99.9% uptime"

servers:
  production:
    type: snowflake
    account: company.us-east-1
    database: PROD_DW
    schema: ORDERS

models:
  - name: fct_orders
    type: table
    description: "One row per order, updated daily"
    fields:
      - name: order_id
        type: string
        required: true
        unique: true
      - name: amount_usd
        type: number
        required: true
        minimum: 0
      - name: status
        type: string
        enum: [pending, completed, cancelled, refunded]
    quality:
      - type: row_count
        mustBeBetween: [1000, 100000000]
      - type: freshness
        mustNotExceedHours: 25
```

---

## 20. Critical Papers & Systems Cheat-Sheet

### Landmark Papers

```
Storage & Formats:
  "The Google File System" (Ghemawat et al., 2003) → HDFS
  "Bigtable: A Distributed Storage System" (Chang et al., 2006) → HBase/Cassandra
  "Dynamo: Amazon's Highly Available Key-Value Store" (DeCandia et al., 2007) → DynamoDB/Cassandra
  "The Snowflake Elastic Data Warehouse" (Dageville et al., 2016) → Snowflake

Processing:
  "MapReduce: Simplified Data Processing on Large Clusters" (Dean et al., 2004) → Hadoop
  "Dremel: Interactive Analysis of Web-Scale Datasets" (Melnik et al., 2010) → BigQuery
  "Resilient Distributed Datasets" (Zaharia et al., 2012) → Apache Spark
  "Structured Streaming: A Declarative API for Real-Time Applications" (Armbrust et al., 2018)

Streaming:
  "The Log: What every software engineer should know" (Kreps, 2013) → Kafka
  "Apache Kafka: A Distributed Messaging System" (Kreps et al., 2011)
  "Streaming Systems" (Akidau et al.) → Apache Flink/Beam time model
  "One SQL to Rule Them All" (Begoli et al., 2019) → unified batch+streaming SQL

Architecture:
  "Delta Lake: High-Performance ACID Table Storage" (Armbrust et al., 2020)
  "Apache Iceberg: A New Table Format for Hadoop" (Apache, 2018)
  "Data Mesh" (Dehghani, 2019)
  "Emerging Architectures for Modern Data Infrastructure" (a16z, 2020)

Databases:
  "Architecture of a Database System" (Hellerstein et al., 2007) → foundational
  "ARIES: A Transaction Recovery Method" (Mohan et al., 1992) → WAL
  "Spanner: Google's Globally Distributed Database" (Corbett et al., 2012)
  "F1: A Distributed SQL Database That Scales" (Shute et al., 2013)
```

### Technology Decision Matrix

```
Workload             → Recommended Tool
─────────────────────────────────────────────────────────────────
OLTP (transactional) → PostgreSQL / Aurora / CockroachDB
OLAP (analytical)    → Snowflake / BigQuery / Redshift
Real-time analytics  → ClickHouse / Pinot / Druid
NoSQL KV             → DynamoDB / Redis
NoSQL wide-col       → Cassandra / Bigtable
Search               → Elasticsearch / OpenSearch
Graph                → Neo4j / Amazon Neptune
Time-series          → InfluxDB / TimescaleDB / ClickHouse
Data lake storage    → S3 + Delta Lake / Iceberg
Batch processing     → Spark (PySpark / Scala)
Stream processing    → Kafka + Flink / Kafka Streams
Data warehouse       → Snowflake (multi-cloud) / BigQuery (GCP) / Redshift (AWS)
Orchestration        → Dagster / Airflow 2.x
EL (SaaS)           → Fivetran / Airbyte
Transform            → dbt
Reverse ETL          → Census / Hightouch
BI                   → Looker / Tableau / Metabase
Data catalog         → Datahub / Alation / Atlan
Data quality         → Great Expectations / Soda / Monte Carlo
Feature store        → Feast / Tecton / Hopsworks
ML platform          → MLflow + Databricks / SageMaker / Vertex AI
```

---

## 21. Glossary

| Term | Definition |
|------|-----------|
| **ACID** | Atomicity, Consistency, Isolation, Durability — transactional guarantees |
| **BASE** | Basically Available, Soft State, Eventual Consistency — NoSQL trade-off |
| **CAP Theorem** | Can only guarantee 2 of: Consistency, Availability, Partition Tolerance |
| **ETL** | Extract-Transform-Load; transform before loading |
| **ELT** | Extract-Load-Transform; load raw then transform in warehouse |
| **Data Lakehouse** | Combines data lake storage with warehouse reliability (ACID, schema) |
| **Delta Lake** | Open table format on Parquet adding ACID, time travel, Z-ORDER |
| **Iceberg** | Open table format; full schema/partition evolution, multi-engine |
| **Parquet** | Columnar binary file format; primary analytics format |
| **Avro** | Row-based binary format with embedded schema; primary streaming format |
| **Schema Registry** | Central store for Avro/Protobuf schemas; enables schema evolution |
| **Partition Pruning** | Skipping partitions at query time using WHERE clause |
| **Predicate Pushdown** | Pushing filters to storage layer to read less data |
| **Column Pruning** | Reading only requested columns from columnar storage |
| **Data Skew** | Uneven data distribution; certain keys have far more records |
| **Salting** | Adding random prefix to skewed keys to distribute across partitions |
| **Shuffle** | All-to-all data exchange between Spark stages (expensive) |
| **Stage** | Group of tasks in Spark separated by shuffle boundaries |
| **Broadcast Join** | Copy small table to all executors; avoid shuffling large table |
| **AQE** | Adaptive Query Execution; re-optimises Spark plan at runtime using stats |
| **Z-ORDER** | Multi-dimensional clustering of data files to improve data skipping |
| **Compaction** | Merging small files into larger files to reduce overhead |
| **Watermark** | Upper bound on event time lag; triggers window computation in streaming |
| **Checkpoint** | Snapshot of Flink/Spark Streaming state for fault tolerance |
| **Exactly-Once** | Each record processed exactly once despite failures (via 2PC + idempotency) |
| **CDC** | Change Data Capture; capture row-level changes from database WAL |
| **WAL** | Write-Ahead Log; database durability mechanism; source for CDC |
| **Debezium** | CDC platform that reads PostgreSQL/MySQL/MongoDB WAL → Kafka |
| **KRaft** | Kafka without ZooKeeper; Raft-based controller (Kafka 3.3+) |
| **Consumer Group** | Group of consumers sharing partition assignment for a topic |
| **ISR** | In-Sync Replicas; Kafka replicas within acceptable lag |
| **Consistent Hashing** | Hash ring that minimises remapping when nodes are added/removed |
| **Replication Lag** | How far behind a replica is from the leader |
| **OLTP** | Online Transaction Processing; row-oriented, many small reads/writes |
| **OLAP** | Online Analytical Processing; columnar, large aggregation queries |
| **MPP** | Massively Parallel Processing; shared-nothing distributed query |
| **Star Schema** | Fact table at centre, dimension tables around it (denormalised) |
| **SCD Type 2** | Slowly Changing Dimension; versioned rows for historical accuracy |
| **Data Vault** | Hub-Link-Satellite modeling for auditable enterprise warehouses |
| **Data Mesh** | Decentralised data ownership by domain teams |
| **Data Contract** | Formal agreement on schema, SLAs, ownership between producer and consumer |
| **Lineage** | Track data flow from source to consumption (table and column level) |
| **Data Catalog** | Metadata store: schema, ownership, lineage, quality, access control |
| **Feature Store** | Shared repo of ML features; unified offline (training) + online (serving) |
| **Medallion Architecture** | Bronze → Silver → Gold data lake zones (Databricks pattern) |
| **dbt** | Data Build Tool; SQL-based transformation with tests and documentation |
| **Fivetran** | Managed EL connectors (SaaS → warehouse); automated schema migration |
| **Great Expectations** | Python data quality framework; expectation suites on DataFrames |
| **OpenLineage** | Open standard for data lineage metadata |
| **Snowflake Virtual Warehouse** | Isolated compute cluster; auto-suspend/resume; pay-per-use |
| **BigQuery Slot** | Unit of BigQuery compute (1 slot ≈ 1 vCPU); can reserve or pay on-demand |
| **DuckDB** | In-process OLAP database; query Parquet/CSV without a server |
| **ClickHouse** | Column-oriented DBMS; billions of rows/second on single node |
| **Trino** | Distributed SQL query engine; federated queries across many data sources |
| **HTAP** | Hybrid Transactional/Analytical Processing; serve both OLTP and OLAP |

---

*Last updated: 2026. Covers Spark 3.5, Kafka 3.7, Flink 1.19, Delta Lake 3.x, Iceberg 1.5, dbt 1.8, Airflow 2.9.*
*Architectures validated on AWS, GCP, and Azure enterprise deployments.*
