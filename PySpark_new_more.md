# PySpark — Complete Guide (Beginner → Staff Engineer)

> Distributed data processing with Python, from "what even is Spark" to production tuning.
> Every concept explained with intuition first, then code, then a real sample output.

---

## Table of Contents

0. [Beginner Primer — Read This First](#0-beginner-primer--read-this-first)
1. [Spark Architecture](#1-spark-architecture)
2. [RDDs — The Foundation](#2-rdds--the-foundation)
3. [DataFrames & Spark SQL](#3-dataframes--spark-sql)
4. [Transformations vs Actions & Lazy Evaluation](#4-transformations-vs-actions--lazy-evaluation)
5. [Reading & Writing Data](#5-reading--writing-data)
6. [Joins & Shuffles](#6-joins--shuffles)
7. [Partitioning & Data Skew](#7-partitioning--data-skew)
8. [Caching & Persistence](#8-caching--persistence)
9. [User-Defined Functions (UDFs) & Performance](#9-user-defined-functions-udfs--performance)
10. [Window Functions](#10-window-functions)
11. [Structured Streaming](#11-structured-streaming)
12. [Performance Tuning & Debugging](#12-performance-tuning--debugging)
13. [Running Spark in Production](#13-running-spark-in-production)
14. [Interview Questions](#14-interview-questions)

---

## 0. Beginner Primer — Read This First

### What problem does Spark actually solve?

```
You have a CSV file with 5 rows. You'd open it in pandas, `df.groupby(...)`, done in milliseconds.

You have 500 GB of log files spread across 10,000 files in cloud storage. It doesn't fit in ONE
machine's RAM. Even if it did, processing it on one CPU core would take hours. Spark exists to solve
EXACTLY this: split a huge dataset into pieces, spread those pieces across many machines (a
"cluster"), and process all the pieces in parallel — turning an hours-long single-machine job into a
minutes-long job across 50 machines.
```

Pandas and Spark's DataFrame API look deliberately similar on purpose (so pandas users feel at home),
but they solve different-scale problems: pandas = fits on one machine; Spark = doesn't.

### The cast of characters: Driver, Cluster Manager, Executors

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DRIVER                                                                   │
│  The process running YOUR code (the .py script you wrote). It doesn't    │
│  process data itself — it plans the work and coordinates everyone else.  │
└──────────────────────────────┬─────────────────────────────────────────────┘
                                │ "I need 20 executors with 4 cores each"
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  CLUSTER MANAGER  (YARN, Kubernetes, or Spark's own standalone mode)     │
│  Decides WHICH physical machines to actually give the driver for its job │
└──────────────────────────────┬─────────────────────────────────────────────┘
                                │ allocates
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  EXECUTORS  (many, spread across many machines)                          │
│  Node 1: [Executor] [Executor]     Node 2: [Executor]     Node 3: [Executor]│
│  Each executor holds a SLICE of your data and does the actual computation │
└──────────────────────────────────────────────────────────────────────────┘
```

This is the SAME "one coordinator, many workers doing the real work" shape you've likely seen
elsewhere (e.g. a load balancer + many API servers) — Spark just applies it to DATA PROCESSING instead
of serving HTTP requests.

### Key vocabulary you'll see constantly

```
Partition       One SLICE of your dataset — the unit of parallelism. If your data has 200
                partitions, up to 200 pieces of work can run truly simultaneously (given enough
                executor cores). Too few partitions = wasted parallelism; too many = overhead.

Shuffle         Redistributing data ACROSS partitions/machines mid-job — e.g. a `groupBy` needs
                every row with the same key to end up on the same machine, which usually means
                sending data over the network between machines. This is almost always the
                SLOWEST part of a Spark job — most performance tuning is about minimizing shuffles.

Lazy evaluation Spark doesn't actually DO any work when you write `df.filter(...).select(...)` —
                it just builds a PLAN. Work only actually happens when you call an "action" (like
                `.show()` or `.write()`). Section 4 covers exactly why this matters.

Driver OOM      A very common beginner bug: calling `.collect()` pulls ALL the distributed data
                back into the single driver process's memory — if your dataset is 500GB and your
                driver has 8GB of RAM, this crashes. Distributed data should mostly STAY
                distributed; only pull small, aggregated results back to the driver.
```

### How to read this document

Sections 1-4 are the conceptual foundation (architecture, RDDs vs DataFrames, laziness) — read these
first even if you're impatient to write code, because almost every confusing Spark behavior traces
back to one of these four ideas. Sections 5-11 are the practical toolkit; Sections 12-13 are the
production/performance concerns that separate "it works on my laptop" from "it survives a 10TB job."

---

## 1. Spark Architecture

**Beginner recap:** Formalizes the Driver/Cluster Manager/Executor picture from the primer above, and
introduces the `SparkSession` — the one object your code uses to talk to all of it.

### Starting a Spark session

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("my-first-spark-job")
    # a human-readable name for this job — shows up in the Spark UI (a web dashboard) and in
    # cluster manager logs, so you can find YOUR job among everyone else's running jobs
    .master("local[*]")
    # "local[*]" means: don't use a real cluster at all — simulate one on THIS machine, using
    # all available CPU cores as "executors." This is exactly how you develop/test Spark code
    # on your laptop before submitting it to a real cluster (Section 13 covers real clusters).
    .config("spark.sql.shuffle.partitions", "200")
    # controls how many partitions a shuffle (e.g. groupBy, join) produces — 200 is Spark's
    # historical default, tuned for large clusters; for small local testing this is often
    # oversized (see Section 12 for tuning guidance)
    .getOrCreate()
    # creates a NEW SparkSession, or reuses an existing one if this code runs somewhere that
    # already has one active (e.g. inside a notebook) — avoids accidentally creating duplicates
)

print(spark.version)
# Sample output: 3.5.1
```

### The three-tier data structure hierarchy

```
SparkContext   → the original, lowest-level entry point (rarely used directly today)
SparkSession   → the modern unified entry point (wraps SparkContext) — THIS is what you use
DataFrame      → what you actually work with day-to-day: a distributed table with named columns
                 (created via spark.read, spark.sql, or by transforming another DataFrame)
```

---

## 2. RDDs — The Foundation

**Beginner recap:** RDD (Resilient Distributed Dataset) is Spark's ORIGINAL core abstraction — a
distributed collection of Python objects with no notion of "columns" or "schema," just like a plain
Python list, except spread across many machines. Nearly all modern PySpark code uses the higher-level
DataFrame API instead (Section 3) — but DataFrames are secretly BUILT on top of RDDs, and understanding
RDDs explains why certain DataFrame operations behave the way they do (especially around partitioning
and shuffling).

```python
rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5], numSlices=2)
# parallelize() takes a normal Python list (living only on the driver) and DISTRIBUTES it across
# the cluster as an RDD — here split into 2 partitions, e.g. [1, 2, 3] on one executor and [4, 5]
# on another. In real jobs, RDDs/DataFrames get created by READING data (Section 5), not by
# parallelizing an in-memory Python list — this is purely for illustrating the concept.

squared = rdd.map(lambda x: x * x)
# map() is a TRANSFORMATION — describes "square every element," but per Section 4's laziness
# rule, nothing actually runs yet. Each executor will eventually apply this function to ONLY
# the partition(s) it holds, independently and in parallel.

result = squared.collect()
# collect() is an ACTION — THIS is what actually triggers execution, gathering every partition's
# results back to the driver into one plain Python list.
print(result)
# Sample output: [1, 4, 9, 16, 25]
```

**"Resilient"** in the name refers to fault tolerance: Spark remembers the CHAIN of transformations
that produced each partition (called "lineage"), so if a machine holding one partition crashes mid-job,
Spark can recompute just that lost partition from scratch, from the original data — instead of failing
the entire job or needing to replicate everything upfront.

---

## 3. DataFrames & Spark SQL

**Beginner recap:** A DataFrame is an RDD PLUS a schema (named, typed columns) — the difference matters
a lot in practice: because Spark KNOWS the column types and structure, it can optimize your query (via
something called the Catalyst optimizer) far better than it can optimize an opaque RDD of arbitrary
Python objects. In virtually all modern PySpark code, you work with DataFrames, not raw RDDs.

```python
df = spark.read.csv("orders.csv", header=True, inferSchema=True)
# header=True: treat the first row as column names, not data
# inferSchema=True: Spark scans the data to guess column types (int, string, etc.) automatically —
# convenient for exploration, but costs an extra pass over the data; in production pipelines you
# usually declare the schema explicitly instead (faster, and protects against Spark guessing wrong)

df.printSchema()
# Sample output:
# root
#  |-- order_id: integer (nullable = true)
#  |-- customer_id: integer (nullable = true)
#  |-- amount: double (nullable = true)
#  |-- status: string (nullable = true)

high_value = df.filter(df.amount > 100).select("order_id", "customer_id", "amount")
# filter() keeps only rows matching the condition; select() picks which columns survive —
# both are TRANSFORMATIONS (lazy — see Section 4), so nothing has actually run yet

high_value.show(3)
# Sample output:
# +--------+-----------+------+
# |order_id|customer_id|amount|
# +--------+-----------+------+
# |    1002|        501|150.00|
# |    1007|        502|299.99|
# |    1011|        501|110.50|
# +--------+-----------+------+
# only showing top 3 rows

# The exact same query, written as SQL instead — Spark SQL is NOT a separate system, it compiles
# down to the identical execution plan as the DataFrame API above:
df.createOrReplaceTempView("orders")
spark.sql("SELECT order_id, customer_id, amount FROM orders WHERE amount > 100").show(3)
# Produces IDENTICAL output to the .filter().select() version above — pick whichever reads more
# naturally for a given query; there's no performance difference between the two syntaxes.
```

---

## 4. Transformations vs Actions & Lazy Evaluation

**Beginner recap:** This is the single most important mental model in Spark, and the source of most
beginner confusion. Every DataFrame operation is either a **transformation** (describes a step, does
NOT run yet — `.filter()`, `.select()`, `.groupBy()`, `.join()`) or an **action** (actually triggers
computation and produces a real result — `.show()`, `.collect()`, `.count()`, `.write()`).

```python
df2 = df.filter(df.amount > 100)     # transformation — instant, no data touched yet
df3 = df2.select("order_id")          # transformation — still nothing has run
df3.explain()
# Sample output (an execution PLAN, not data):
# == Physical Plan ==
# *(1) Project [order_id#0]
# +- *(1) Filter (isnotnull(amount#2) AND (amount#2 > 100.0))
#    +- FileScan csv [order_id#0,amount#2] Batched: false, ...

count = df3.count()                    # ACTION — only NOW does Spark actually read the CSV,
                                        # apply the filter, and count matching rows
print(count)
# Sample output: 47
```

**Why does Spark bother being lazy instead of just running each step immediately?** Because it can
look at the WHOLE chain of transformations before running anything, and optimize across all of them
at once — e.g. if you `.filter()` then `.select()` a few columns, Spark can push the filter down and
avoid ever reading the unneeded columns from disk in the first place (this is what `.explain()` above
is showing you: the optimized PHYSICAL plan, which may look quite different from the order you wrote
the code in).

---

## 5. Reading & Writing Data

**Beginner recap:** How data actually gets IN and OUT of Spark — and why the FILE FORMAT you choose
matters enormously for performance (this connects directly to the "File Formats" section of the
DATA_ENGINEERING doc — Parquet in particular is the de facto standard for a reason explained there).

```python
# Reading — Parquet is strongly preferred over CSV/JSON for large data (columnar, compressed,
# stores its own schema, and lets Spark skip whole column groups it doesn't need)
df = spark.read.parquet("s3://my-bucket/orders/")

# Writing, partitioned by a column — this creates one SUBFOLDER per distinct date value on disk,
# so a later query filtering `WHERE order_date = '2026-08-01'` can skip reading every OTHER
# date's files entirely ("partition pruning") instead of scanning the whole dataset
df.write.partitionBy("order_date").mode("overwrite").parquet("s3://my-bucket/orders_clean/")

# Resulting folder structure on disk:
# s3://my-bucket/orders_clean/
#   order_date=2026-07-30/part-00000.parquet
#   order_date=2026-07-31/part-00000.parquet
#   order_date=2026-08-01/part-00000.parquet
```

**Used in production?** Yes — this exact "read Parquet, transform, write back out partitioned by date"
pattern is the backbone of the vast majority of real-world nightly batch ETL jobs at companies running
Spark (this is precisely what Airflow, covered in the DATA_ENGINEERING doc's Section 8, typically
schedules and triggers on a nightly basis).

---

## 6. Joins & Shuffles

**Beginner recap:** A join across two DataFrames usually requires a **shuffle** — rows with matching
join keys have to end up on the SAME machine to actually be compared and combined, which typically means
sending data over the network. This is why joins are often the single slowest part of a Spark job, and
why the optimization below (broadcast join) exists specifically to AVOID the shuffle in one common case.

```python
orders = spark.read.parquet("orders/")           # large: 500 million rows
customers = spark.read.parquet("customers/")     # small: 50,000 rows

# A normal join: both sides get shuffled/repartitioned by the join key so matching rows co-locate
result = orders.join(customers, "customer_id")

# A BROADCAST join: if one side is small enough to fit in memory, Spark instead sends a FULL COPY
# of the small table to EVERY executor — no shuffle needed at all for the large side
from pyspark.sql.functions import broadcast
result = orders.join(broadcast(customers), "customer_id")
# Spark actually does this AUTOMATICALLY for tables under `spark.sql.autoBroadcastJoinThreshold`
# (default 10MB) — the explicit broadcast() hint above is for cases where Spark's own size
# estimate is wrong and you know better

result.explain()
# Sample output (note "BroadcastHashJoin" instead of "SortMergeJoin" — confirms no shuffle
# happened for the large side):
# == Physical Plan ==
# *(2) BroadcastHashJoin [customer_id#12], [customer_id#45], Inner, BuildRight
# :- *(2) FileScan parquet [customer_id#12,...] orders/
# +- BroadcastExchange HashedRelationBroadcastMode(...)
#    +- *(1) FileScan parquet [customer_id#45,...] customers/
```

---

## 7. Partitioning & Data Skew

**Beginner recap:** "Skew" means some partitions end up with FAR more data than others (e.g. one
customer_id has 40% of all orders) — since a Spark stage only finishes when its SLOWEST partition
finishes, one skewed partition can single-handedly make an otherwise-fast job take 10x longer, while
every other executor sits idle waiting.

```python
# Diagnosing skew: how many rows landed in each partition after a groupBy?
from pyspark.sql.functions import spark_partition_id

df.groupBy(spark_partition_id()).count().orderBy("count", ascending=False).show(5)
# Sample output — partition 42 has 40x more rows than the others, confirming skew:
# +--------------------+-----+
# |SPARK_PARTITION_ID()|count|
# +--------------------+-----+
# |                  42|8000000|
# |                  17|  210000|
# |                   3|  198500|
# +--------------------+-----+

# Fix — "salting": artificially split the hot key into several sub-keys so its rows spread
# across multiple partitions instead of piling into one
from pyspark.sql.functions import rand, concat, lit, floor

salted = df.withColumn("salt", floor(rand() * 10))   # random salt 0-9 per row
salted = salted.withColumn("salted_key", concat(df.customer_id, lit("_"), salted.salt))
# now groupBy("salted_key") spreads the previously-hot customer_id across ~10 partitions instead
# of 1; a second aggregation step re-combines the salted partial results back into final totals

# Since Spark 3.0+, Adaptive Query Execution (AQE) can often detect and fix skewed joins
# AUTOMATICALLY, without manual salting:
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

---

## 8. Caching & Persistence

**Beginner recap:** Because of lazy evaluation (Section 4), if you use the SAME DataFrame in two
different actions, Spark by default RECOMPUTES it from scratch both times (re-reading files,
re-running every transformation). `.cache()` tells Spark "keep this one in memory after the first
computation, so later reuses are free."

```python
df = spark.read.parquet("orders/").filter(...)
df.cache()             # marks df for caching — but per laziness, caching doesn't happen yet either!

df.count()              # ACTION #1 — this is what actually triggers computation AND populates the cache
df.groupBy("status").count().show()   # ACTION #2 — reuses the CACHED data, doesn't re-read from disk

# Rule of thumb: only cache a DataFrame you'll use 3+ times; caching something used once just adds
# overhead for no benefit. Also remember to release it when done, in long-running jobs/notebooks:
df.unpersist()
```

---

## 9. User-Defined Functions (UDFs) & Performance

**Beginner recap:** Spark's built-in functions (`filter`, `withColumn` with built-in expressions) run
inside the JVM and are heavily optimized. A UDF lets you plug in ARBITRARY Python logic Spark has no
functions for — but that Python code has to run OUTSIDE the JVM, in a separate Python process, with
data serialized back and forth between them. This makes UDFs meaningfully SLOWER than built-in
functions — always prefer a built-in function if one exists for what you need.

```python
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType

def categorize(amount):
    if amount > 1000:
        return "large"
    elif amount > 100:
        return "medium"
    return "small"

categorize_udf = udf(categorize, StringType())
# wraps the plain Python function so Spark can call it per-row across the cluster; StringType()
# tells Spark what type to expect BACK — Spark can't infer this from Python's dynamic typing

df = df.withColumn("size_category", categorize_udf(col("amount")))
df.select("amount", "size_category").show(3)
# Sample output:
# +------+-------------+
# |amount|size_category|
# +------+-------------+
# |150.00|       medium|
# |299.99|       medium|
# |1200.0|        large|
# +------+-------------+

# Better alternative for THIS specific case — a built-in expression avoids the Python round-trip
# entirely and runs noticeably faster at scale:
from pyspark.sql.functions import when
df = df.withColumn(
    "size_category",
    when(col("amount") > 1000, "large").when(col("amount") > 100, "medium").otherwise("small"),
)
```

**Used in production?** UDFs are common but deliberately minimized in performance-sensitive production
pipelines — a frequent staff-level review comment on a Spark PR is "can this UDF be rewritten with
built-in functions?" Pandas UDFs (vectorized, operating on a whole batch of rows via Arrow instead of
row-by-row) are a faster middle ground when custom Python logic is unavoidable.

---

## 10. Window Functions

**Beginner recap:** A normal `groupBy` collapses many rows into one row PER group (e.g. "total revenue
per customer"). A window function instead computes something ACROSS a group of related rows while
keeping every original row intact — e.g. "this order's rank among this customer's orders," attached
to every individual order row.

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import rank, sum as _sum

window_spec = Window.partitionBy("customer_id").orderBy(df.amount.desc())
# partitionBy: group rows by customer (like groupBy, but rows stay separate)
# orderBy: within each customer's group, order by amount descending

ranked = df.withColumn("rank_within_customer", rank().over(window_spec))
ranked.select("customer_id", "amount", "rank_within_customer").show(5)
# Sample output:
# +-----------+------+---------------------+
# |customer_id|amount|rank_within_customer |
# +-----------+------+---------------------+
# |        501|299.99|                    1|
# |        501|150.00|                    2|
# |        501|110.50|                    3|
# |        502|500.00|                    1|
# |        502| 45.00|                    2|
# +-----------+------+---------------------+

# Running total per customer, ordered by date — a very common real-world use case
running_window = Window.partitionBy("customer_id").orderBy("order_date")
ranked = ranked.withColumn("running_total", _sum("amount").over(running_window))
```

---

## 11. Structured Streaming

**Beginner recap:** Everything so far has been BATCH processing (a fixed, finite dataset). Structured
Streaming applies the exact same DataFrame API to an UNBOUNDED, continuously-arriving stream of data
(e.g. reading from Kafka) — the code looks almost identical to batch code, which is a deliberate design
goal: Spark treats a stream as "a table that keeps growing," so most of what you already learned above
about DataFrames transfers directly.

```python
stream_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker1:9092")
    .option("subscribe", "orders-topic")
    .load()
)

# Same DataFrame operations as batch — this is the whole point of "structured" streaming
parsed = stream_df.selectExpr("CAST(value AS STRING) as json_str")
counts = parsed.groupBy("json_str").count()

query = (
    counts.writeStream
    .outputMode("complete")     # "complete": rewrite the full result table each trigger (fine
                                  # for aggregations); "append" is used for non-aggregated data
    .format("console")
    .trigger(processingTime="10 seconds")   # re-check for new data and update output every 10s
    .start()
)

query.awaitTermination()
# Sample console output, printed every ~10 seconds as new Kafka messages arrive:
# -------------------------------------------
# Batch: 3
# -------------------------------------------
# +--------------------+-----+
# |json_str             |count|
# +--------------------+-----+
# |{"status":"shipped"} |  142|
# |{"status":"pending"} |   38|
# +--------------------+-----+
```

**Used in production?** Yes — Structured Streaming (as opposed to the older, lower-level "DStreams"
API) is the modern standard way to build streaming pipelines on Spark, commonly consuming from Kafka
and writing continuously-updated aggregates to a database or another Kafka topic. It directly overlaps
with, and is a real alternative to, the Flink option covered in the DATA_ENGINEERING doc's Section 5 —
teams often pick one or the other based on which one their team already has Spark/Flink expertise in.

---

## 12. Performance Tuning & Debugging

**Beginner recap:** "It's slow" is a guess; the Spark UI (a web dashboard the driver runs, usually at
`http://localhost:4040` during local runs) is the proof — it shows every stage of your job, how long
each took, and how much data each partition handled, which is where you'd actually SEE the skew
symptoms described in Section 7.

```
Checklist for a slow Spark job:

1. Open the Spark UI → SQL tab → find the slow stage. Is one task taking way longer than the
   others in the same stage? → partition skew (Section 7).

2. Too many small files being read/written? → "small file problem" — coalesce/repartition before
   writing, since each tiny file adds fixed overhead per file that adds up across thousands of files.

3. Are you calling .collect() on something huge? → driver OOM waiting to happen (see Section 0's
   glossary) — aggregate/sample BEFORE collecting, not after.

4. Shuffle partitions (spark.sql.shuffle.partitions, default 200) way too high for your data size?
   → hundreds of nearly-empty partitions add scheduling overhead for no benefit; way too LOW for a
   huge dataset → each partition too big, risking spill-to-disk or OOM. Tune based on data volume,
   not blindly leaving the default.

5. Data not cached but reused 3+ times? → see Section 8.
```

---

## 13. Running Spark in Production

**Beginner recap:** The `local[*]` mode from Section 1 is for development only — real jobs run on an
actual cluster, submitted via `spark-submit`, typically orchestrated by a scheduler (Airflow) on a
recurring schedule.

```bash
# Submitting a job to a real cluster (here, Kubernetes as the cluster manager)
spark-submit \
  --master k8s://https://my-cluster-api-server:443 \
  --deploy-mode cluster \
  --conf spark.executor.instances=20 \
  --conf spark.executor.memory=8g \
  --conf spark.executor.cores=4 \
  --conf spark.kubernetes.container.image=my-registry/spark-job:latest \
  s3://my-bucket/jobs/nightly_orders_etl.py
```

**Used in production?** Yes — this is close to a literal real-world command for a scheduled batch job.
Companies running Spark at real scale (Uber, Netflix, Airbnb, and many others) typically run it on
either a managed cloud service (AWS EMR, Databricks, Google Dataproc) or self-managed on Kubernetes/YARN,
almost always triggered by an orchestrator like Airflow rather than a human manually running
`spark-submit` — see the DATA_ENGINEERING doc's Section 8 for how that scheduling layer works.

---

## 14. Interview Questions

1. **"What's the difference between an RDD and a DataFrame?"** — DataFrame adds a schema (named,
   typed columns), which lets Spark's Catalyst optimizer generate a much more efficient execution
   plan than it can for an opaque RDD of arbitrary objects (Sections 2-3).
2. **"Why is `.collect()` dangerous?"** — it pulls the ENTIRE distributed result back into the single
   driver process's memory, which can OOM the driver if the result is large (Section 0's glossary).
3. **"What causes a shuffle, and why is it expensive?"** — operations that need rows with the same
   key co-located (`groupBy`, `join`, `distinct`) — expensive because it moves data over the network
   between machines, and typically also to disk (Section 6).
4. **"How would you fix a data skew problem?"** — diagnose via partition row counts or the Spark UI,
   then salt the hot key or enable Adaptive Query Execution's automatic skew handling (Section 7).
5. **"When would you use a UDF vs a built-in function?"** — only when no built-in function/expression
   can express the logic — UDFs cross the JVM/Python boundary and are measurably slower at scale
   (Section 9).
