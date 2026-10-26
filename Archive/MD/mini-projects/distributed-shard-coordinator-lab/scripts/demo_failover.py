#!/usr/bin/env python3
"""
Demo: 5 nodes, RF=3, W=2, R=2 — kill a replica mid-flight, reads still succeed.

Run from project root:
  python scripts/demo_failover.py
  # or: pip install -e . && python scripts/demo_failover.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without install when executed from repo root.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from distributed_shard_coordinator import HashRing, QuorumConfig, ShardCoordinator


def main() -> None:
    ring = HashRing(vnodes_per_node=64)
    coord = ShardCoordinator(
        ring=ring,
        nodes={},
        quorum=QuorumConfig(replication_factor=3, write_quorum=2, read_quorum=2),
    )
    for i in range(5):
        coord.register_node(f"node-{i}")

    key = "product:sku-9001"
    print("Cluster: 5 nodes | RF=3 | W=2 | R=2")
    print(f"Preference list for {key!r}: {ring.replica_nodes(key, 3)}\n")

    wr = coord.put(key, "in-stock")
    print(f"PUT ok — version={wr.version}, replicas_written={wr.replicas_written}, hints={wr.hinted}")

    rr = coord.get(key)
    print(f"GET (healthy) — value={rr.value!r}, replicas_read={rr.replicas_read}\n")

    victim = ring.replica_nodes(key, 3)[0]
    print(f"*** Simulating failure: killing {victim} ***")
    coord.kill_node(victim)

    wr2 = coord.put(key, "low-stock")
    print(f"PUT after failure — version={wr2.version}, replicas_written={wr2.replicas_written}")

    rr2 = coord.get(key)
    print(f"GET after failure — value={rr2.value!r}, replicas_read={rr2.replicas_read}")
    print("\nReads still meet R=2 quorum despite one dead replica (CAP: choose A + tunable consistency).")


if __name__ == "__main__":
    main()
