# Distributed shard coordinator lab

Production-style **data plane** miniature: consistent-hash routing, replication factor **RF**, quorum writes **W** and reads **R**, simulated node failure, **hinted handoff**, **read repair**, and optional **stale read** detection. Stdlib only — no Redis, no Cassandra cluster required.

## Curriculum links

| Topic | Markdown module |
|-------|-----------------|
| Sharding, preference lists, hot keys | [`../../fanout-system-design/04-nosql-partitioning-ids.md`](../../fanout-system-design/04-nosql-partitioning-ids.md) |
| Quorum consistency, replication, CAP | [`../../fanout-system-design/06-distributed-coordination.md`](../../fanout-system-design/06-distributed-coordination.md) |

Builds on the same ring pattern as [`../consistent-hash-lab/`](../consistent-hash-lab/).

## Layout

```
src/distributed_shard_coordinator/
  ring.py           # virtual nodes + preference list walk
  shard_node.py     # in-memory replica + hints
  coordinator.py    # put/get, W/R, read repair
  errors.py         # typed failures
  types.py          # QuorumConfig, results
scripts/demo_failover.py
tests/test_quorum.py
```

## Quick start

```bash
cd MD/mini-projects/distributed-shard-coordinator-lab
pip install -e ".[dev]"
pytest -q
python scripts/demo_failover.py
```

Default topology in tests and demo: **5 physical nodes**, **RF=3**, **W=2**, **R=2**. One replica is killed mid-scenario; reads still succeed because the coordinator skips dead nodes and contacts alternates on the ring.

## What to notice (Dynamo-style)

- **Preference list** — `HashRing.replica_nodes(key, RF)` is the first RF distinct nodes clockwise from `hash(key)`.
- **Sloppy quorum** — if a preferred replica is down, writes may land on a substitute plus a **hint** for the intended owner.
- **W + R > RF** — with 3 replicas and W=R=2, read and write quorums overlap, giving practical read-your-writes behavior without a single leader.
- **Read repair** — on read, lagging replicas get the highest version (sync here; async in production).
- **strict_reads** — set on `ShardCoordinator` to raise `StaleReadError` when replicas disagree (teaching tool).

## CAP (toy framing)

This lab **favors availability** during a single node loss: writes and reads proceed when at least **W** or **R** live replicas (or handoff targets) respond. You do **not** get linearizable semantics unless you tighten W and R (e.g. W=R=RF) or route through a leader — see module 06 for when to pay that cost.
