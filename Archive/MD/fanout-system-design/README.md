# Fanout System Design — Study Notes

> **Audience:** Senior software engineers preparing for FAANG system design interviews. Written in **plain language** — every concept explained before it's used.  
> **Source:** Fanout System Design course (Modules 04–18).  
> **Style:** Each module covers concepts → code → diagrams → FAANG deep dive → senior pitfalls → production practice.

---

## Modules

| # | File | Topics | Core theme |
|---|------|--------|------------|
| 04 | [04-nosql-partitioning-ids.md](./04-nosql-partitioning-ids.md) | 14 | NoSQL choices, sharding, consistent hashing, ID generation, Bloom filters |
| 05 | [05-caching-and-fast-reads.md](./05-caching-and-fast-reads.md) | 6 | Cache layers, eviction, TTL, concurrency, availability |
| 06 | [06-distributed-coordination.md](./06-distributed-coordination.md) | 13 | Consistency, replication, CAP, consensus, locks, circuit breakers |
| 07 | [07-storage-engines.md](./07-storage-engines.md) | 20 | LSM-trees, Bitcask, SSTables, object storage, S3, durability |
| 08 | [08-async-work-and-streams.md](./08-async-work-and-streams.md) | 10 | Task queues, event streams, DAG orchestration, fanout |
| 09 | [09-search-and-retrieval.md](./09-search-and-retrieval.md) | 17 | Inverted index, BM25, vector search, autocomplete, crawlers |
| 10 | [10-analytics-and-sketches.md](./10-analytics-and-sketches.md) | 13 | HyperLogLog, Count-Min, t-digest, sampling, heavy hitters |
| 11 | [11-realtime-social-feeds.md](./11-realtime-social-feeds.md) | 10 | WebSockets, social graph, feed fanout, live commentary |
| 12 | [12-geo-matching-recs.md](./12-geo-matching-recs.md) | 8 | Geohash, H3/S2, geofencing, Bloom seen-filter, matching |
| 13 | [13-media-files-cdn.md](./13-media-files-cdn.md) | 11 | Uploads, transcoding, CDN, ABR, WebRTC, file sync |
| 14 | [14-reliability-and-operations.md](./14-reliability-and-operations.md) | 13 | Observability, SLOs, incidents, deployments, rate limiting, multi-tenant |
| 15 | [15-service-and-data-designs.md](./15-service-and-data-designs.md) | 7 | URL shortener, rate limiter, collaborative editor, object store, Kafka |
| 16 | [16-product-designs.md](./16-product-designs.md) | 8 | Notification, booking, payment, search, chat, feed, nearby |
| 17 | [17-media-and-ops-designs.md](./17-media-and-ops-designs.md) | 6 | Media pipeline designs, ops designs |
| 18 | [18-engineering-case-studies.md](./18-engineering-case-studies.md) | 5 | Instagram, Stripe, Discord, Amazon Dynamo, GitLab |

---

## How to study

1. **Read in order** — modules build on each other (04 → 07 foundations before 15–16 designs).
2. **Draw every diagram** by hand at least once — interviewers watch you diagram.
3. **Do every practice exercise** — reading ≠ understanding; building = understanding.
4. **Senior Pitfalls tables** — memorize these; interviewers test for production awareness.

---

## Quality bar

Every module includes:

| Section | Purpose |
|---------|---------|
| Plain-language explanation | Understand the concept without jargon |
| Code examples | Working snippets you can run |
| Mermaid diagrams | Visual architecture — paste into any Markdown renderer |
| FAANG Interview Deep Dive | What interviewers actually ask and expect |
| Senior Pitfalls | Common production mistakes and fixes |
| Production-grade Practice | Exercises that simulate real engineering work |

---

## Related docs in this repo

- `MD/distributed-systems/` — Consensus, replication, data patterns
- `MD/databases-internals/` — Storage, indexing, transactions
- `MD/caching-and-performance/` — Thundering herd, distributed locks
- `MD/event-driven-architecture/` — Event sourcing, outbox, CEP
- `MD/observability/` — OTel, sampling, high cardinality
- `MD/reliability-and-resilience/` — Game days, SLOs, cascading failure
- `MD/ai-engineering-curriculum/` — AI/LLM engineering (separate track)
