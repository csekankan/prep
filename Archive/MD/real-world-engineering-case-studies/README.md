# 🏗️ Real-World Engineering Case Studies

> FAANG-level deep dives into legendary engineering decisions, disasters, and innovations — explained in plain English with code, diagrams, and interview prep.

---

## 📚 Contents

| # | Case Study | Company | Core Concept |
|---|-----------|---------|--------------|
| 01 | [Stripe's Idempotency Keys](./01-stripe-idempotency-keys.md) | Stripe | Safe payment retries, recovery points, state machines |
| 02 | [Discord: Trillions of Messages](./02-discord-trillions-of-messages.md) | Discord | MongoDB → Cassandra → ScyllaDB migration, partitioning, Snowflake IDs |
| 03 | [Amazon Dynamo Paper](./03-amazon-dynamo-paper.md) | Amazon | Consistent hashing, vector clocks, sloppy quorum, eventual consistency |
| 04 | [AWS Lambda Container Loading](./04-aws-lambda-container-loading.md) | AWS | Chunking, deduplication, erasure coding, tiered caching, Firecracker |
| 05 | [GitLab Database Incident](./05-gitlab-database-incident.md) | GitLab | Backup failures, incident response, blameless post-mortems, Swiss Cheese Model |

---

## 🎯 What Makes These Special

- **Easy wording** — Complex systems explained like you're talking to a friend
- **Production code** — Not toy examples; real patterns used at scale
- **Mermaid diagrams** — Visual architecture and flow diagrams throughout
- **FAANG interview prep** — Common interview questions with structured answers
- **Failure analysis** — Learn from what went WRONG, not just what went right

---

## 🔥 Production Scenario Q&A Deep Dives

Each case study has a companion Q&A file with real production incidents, debugging workflows, and battle-tested solutions:

| # | Q&A Deep Dive | Scenarios Covered |
|---|--------------|-------------------|
| 06 | [Stripe Idempotency — Production Q&A](./06-QA-stripe-idempotency-production-scenarios.md) | Double charge race condition, server crash mid-payment, idempotency store down, table growth, bad key patterns, cross-microservice idempotency |
| 07 | [Discord Messages — Production Q&A](./07-QA-discord-messages-production-scenarios.md) | Hot partition meltdown, tombstone avalanche, Snowflake clock skew, live migration validation, search index sync, message ordering |
| 08 | [Amazon Dynamo — Production Q&A](./08-QA-amazon-dynamo-production-scenarios.md) | Shopping cart conflict resolution (CRDTs), hint backlog explosion, vector clock growth, read-your-writes violation, cross-DC partition, cascading failure on node join |
| 09 | [AWS Lambda — Production Q&A](./09-QA-aws-lambda-production-scenarios.md) | Cold start optimization, concurrency limit spikes, container cache poisoning, edge location loading, local vs prod debugging, runaway cost explosion |
| 10 | [GitLab Incident — Production Q&A](./10-QA-gitlab-incident-production-scenarios.md) | 15-minute RTO architecture, silent backup failure detection, human error prevention, replication lag auto-heal, blameless post-mortem culture |

---

## 🏗️ Large-Scale Solutions & Best Practices

Battle-tested patterns from Netflix, Google, Meta, Uber, and Amazon — explained with production code and diagrams:

| # | Deep Dive | What You'll Learn |
|---|-----------|-------------------|
| 11 | [Data Infrastructure](./11-large-scale-data-infrastructure.md) | Sharding strategies (range, hash, geo, directory), Uber's live shard splitting, replication topologies, cross-shard queries, Netflix's data stack |
| 12 | [Reliability Patterns](./12-large-scale-reliability-patterns.md) | SLOs & error budgets, graceful degradation levels, circuit breakers, chaos engineering (Simian Army), retry with backoff, rate limiting, bulkhead isolation |
| 13 | [Deployments](./13-large-scale-deployments.md) | Canary with auto-rollback, blue-green deploys, feature flags lifecycle, zero-downtime database migrations (expand-and-contract), GitOps with Argo Rollouts |
| 14 | [Caching](./14-large-scale-caching.md) | Multi-layer cache architecture, stampede prevention (lock, early refresh, stale-while-revalidate), CDC-based invalidation, Facebook's Memcached at scale, Redis cluster gotchas |
| 15 | [Observability](./15-large-scale-observability.md) | RED & USE methods, distributed tracing with OpenTelemetry, structured logging, SLO-based burn-rate alerting, dashboard hierarchy |
| 16 | [Incident Management](./16-large-scale-incident-management.md) | Incident severity levels, war room protocol, on-call best practices, runbook automation, self-healing systems, blameless post-mortem framework |

---

## 🗺️ Cross-Cutting Themes

```
Idempotency (Stripe)        ←→  Exactly-once semantics (Dynamo, Discord)
Consistent Hashing (Dynamo) ←→  Partitioning (Discord's bucket strategy)
Erasure Coding (Lambda)     ←→  Replication trade-offs (Dynamo N/R/W)
Backup Verification (GitLab)←→  Anti-entropy (Dynamo Merkle Trees)
Recovery Points (Stripe)    ←→  Disaster Recovery (GitLab runbooks)
Race Conditions (Stripe Q&A)←→  Hot Partitions (Discord Q&A)
CRDTs (Dynamo Q&A)          ←→  Conflict Resolution (all systems)
Circuit Breakers (Lambda Q&A)←→ Cascading Failures (Dynamo Q&A)
```

---

## 📊 Total Coverage

```
Case Study Files:         5 deep dives (Stripe, Discord, Dynamo, Lambda, GitLab)
Production Q&A Files:     5 scenario packs (30+ real incidents)
Large-Scale Patterns:     6 best-practice guides
Total Files:              17 (including README)
Code Examples:            100+ production-grade implementations
Mermaid Diagrams:         70+ architecture and flow diagrams
Interview Q&A:            80+ with structured answers
Production Checklists:    11 ready-to-use checklists
Total Lines:              ~12,000 lines of tutorial content
```
