# What Experienced System Engineers Know (That Tutorials Skip)

> Cross-cutting patterns seen at large-scale product companies. Pair with topic guides and [`DEEP_DIVE_COVERAGE.md`](./DEEP_DIVE_COVERAGE.md). Not company secrets—industry craft.

---

## 1. Caching & performance

- **Hit ratio is a lagging indicator**; track **origin RPS** and **miss-path p99**. A “99.9% hit rate” can still melt the DB if the 0.1% is huge keys or a stampede.
- **Invalidation is a distributed systems problem**: ordering, replica lag, and **re-fill with stale data** matter more than “publish to SNS.”
- **TTL alone is a policy**, not coherence. Jitter prevents synchronized expiry; **versioned invalidation** prevents poisoned re-fill.
- **Edge cache + personalized JSON** = wrong tool unless you segment cache keys (tier, geo, experiment bucket)—never `Vary: *` without thinking.
- **Redis is not a database** for money; **fencing tokens** for locks; **Redlock ≠ consensus**.
- **Cold start after deploy** is a cache problem: empty local + empty Redis → **prewarm** or **synthetic traffic** before shifting traffic.
- **Profiling wins** are often **N+1**, **serialization**, and **fan-out**—not shaving microseconds off hash maps.

**AWS angle:** ElastiCache **replication lag**; Global Datastore **seconds** of cross-region lag; CloudFront **SWR** and `proxy_cache_lock`; DAX only when Dynamo access pattern is stable.

---

## 2. Observability

- **Metrics = low cardinality aggregates**; **traces = high cardinality paths**; **logs = narrative**. Swapping them causes **cost explosions** or **blind spots**.
- **Tail sampling** is mandatory at scale; **head-only 0.1%** misses rare payment bugs. Budget **collector memory** for `decision_wait`.
- **Missing trace time** usually means **broken propagation** (thread pool, Kafka batch, async callback)—not “need more spans.”
- **SLOs are product decisions**: error budget burn triggers **deploy freeze**, not only pages.
- **Dashboards don’t fix incidents**—runbooks with **verification steps** and **rollback** do.
- **eBPF / continuous profiling** finds what span instrumentation missed (GC, lock contention).

**AWS angle:** ADOT on EKS; CloudWatch **metric math** vs **X-Ray** (sampling); **FireLens** for log routing; **cost** of ingesting everything to OpenSearch.

---

## 3. Distributed systems & data

- **Timeout ≠ failure**; retries need **idempotency keys** and **jitter** or you amplify outages.
- **Quorum overlap (R+W>N)** ≠ linearizability without version checks and conflict handling.
- **Leader election** without **fencing** → zombie writers after partition heal.
- **Eventual consistency** is fine for **recommendations**; not for **inventory debit** without careful design.
- **Backpressure** is a feature: bounded queues, **429**, load shed on non-critical paths.
- **Schema evolution** on events matters as much as API versioning—**compat checks in CI**.

**AWS angle:** DynamoDB **conditional writes**; SQS **visibility timeout** vs processing time; MSK **consumer lag**; Route53 **health checks** vs **real user monitoring**.

---

## 4. Event-driven & streaming

- **At-least-once** means **idempotent consumers**—always.
- **Outbox** beats dual-write; **inbox** for incoming side effects.
- **Ordering** is per-partition; redesign keys before “add more consumers.”
- **Poison messages** need **DLQ + alert**; don’t infinite retry.
- **CDC lag** is a **cache invalidation** bug waiting to happen.

**AWS angle:** MSK + **Debezium on ECS**; EventBridge **pipes**; Lambda **partial batch failure** for SQS.

---

## 5. Multi-region & reliability

- **Active-active writes** without conflict model = **data loss** or **merge hell**.
- **DNS failover** is slow; **Anycast / Global Accelerator** for connection-level failover.
- **Blast radius**: cells, shards, **failure domains**—not “one big VPC.”
- **Game days** prove runbooks; **DR without test** is fiction.
- **Cascading failure**: thread pools shared between critical and optional work—**bulkheads**.

**AWS angle:** Global Tables **last writer wins**; Aurora **global database** RPO; **Route53** failover records; **Shield** only on edge—not app logic.

---

## 6. Data stores (OLTP / OLAP)

- **Working set > RAM** → tail latency from disk; **not “add index”** alone.
- **Replication lag** on read replicas → **read-your-writes** bugs after profile update.
- **Migrations** at scale: **expand/contract**, **backfill**, **dual-write** window—never big-bang `ALTER` on huge table in prod without plan.
- **Connection pool** size is a **global** limit across pods—math: `pods × pool_size` vs DB `max_connections`.

**AWS angle:** RDS **Performance Insights**; Aurora **fast failover**; Redshift **WLM** queues; DMS for migrations.

---

## 7. AI / LLM in production

- **Eval harness** before prompt change; treat **prompt + model + retrieval index** as one **release unit**.
- **RAG** freshness vs **fine-tune** for behavior—hybrid common.
- **Token cost** and **p99 TTFT** are SLIs; **guardrails** on tool calls (IAM scope).
- **Drift** in embeddings when catalog changes—reindex strategy.

**AWS angle:** Bedrock **inference profiles**; SageMaker endpoints; **OpenSearch Serverless** vector; CloudWatch for **token usage** alarms.

---

## 8. System design interviews (staff signal)

- State **assumptions** (QPS, read/write, consistency) in first 5 minutes.
- Name **what breaks first** at 10× (DB, hot key, fan-out, cardinality).
- Give **numbers** (storage/year, bandwidth, cache RAM).
- Say **what you would NOT build** (appropriate technology rejection).
- Connect to **ops**: deploy, rollback, observability, on-call.

---

## Study loop

```mermaid
flowchart LR
  G[Topic guide] --> I[Insider bullets here]
  I --> F[FAANG or Interview Q&A in guide]
  F --> W[Whiteboard without notes]
```

AWS service names: see `cloud-ops/` and inline **AWS service map** tables in select topic guides.
