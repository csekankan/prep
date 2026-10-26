"""Quorum writes/reads and simulated node failure."""

from __future__ import annotations

import pytest

from distributed_shard_coordinator import HashRing, QuorumConfig, ShardCoordinator
from distributed_shard_coordinator.errors import QuorumNotMetError, StaleReadError


def _cluster(node_count: int = 5) -> ShardCoordinator:
    ring = HashRing(vnodes_per_node=32)
    coord = ShardCoordinator(
        ring=ring,
        nodes={},
        quorum=QuorumConfig(replication_factor=3, write_quorum=2, read_quorum=2),
    )
    for i in range(node_count):
        coord.register_node(f"node-{i}")
    return coord


def test_quorum_write_and_read_round_trip() -> None:
    coord = _cluster()
    wr = coord.put("user:42", "alice")
    assert wr.replicas_written >= 2
    assert wr.version == 1

    rr = coord.get("user:42")
    assert rr.value == "alice"
    assert rr.replicas_read >= 2


def test_write_requires_w_alive_or_handoff() -> None:
    coord = _cluster()
    # Only one survivor cannot satisfy W=2 distinct replica acks.
    for i in range(4):
        coord.kill_node(f"node-{i}")
    with pytest.raises(QuorumNotMetError) as exc:
        coord.put("k", "v")
    assert exc.value.operation == "write"


def test_reads_succeed_after_replica_failure() -> None:
    """
    RF=3, W=2, R=2: write while healthy, kill one preference-list replica, read still OK.
    """
    coord = _cluster()
    key = "session:abc"
    coord.put(key, "token-1")

    pref = coord.ring.replica_nodes(key, 3)
    victim = pref[0]
    coord.kill_node(victim)

    rr = coord.get(key)
    assert rr.value == "token-1"
    assert rr.replicas_read >= 2


def test_strict_read_detects_divergent_versions() -> None:
    coord = _cluster()
    coord.strict_reads = True
    key = "cart:1"
    pref = coord.ring.replica_nodes(key, 3)

    # Manually create replica divergence (simulates partial write / clock skew).
    from distributed_shard_coordinator.types import StoredRecord

    coord.nodes[pref[0]].local_put(key, StoredRecord("a", 1))
    coord.nodes[pref[1]].local_put(key, StoredRecord("b", 2))

    with pytest.raises(StaleReadError):
        coord.get(key)


def test_revive_applies_hinted_handoff() -> None:
    coord = _cluster()
    key = "hint:key"
    pref = coord.ring.replica_nodes(key, 3)
    down = pref[1]
    coord.kill_node(down)

    coord.put(key, "hinted-value")

    assert coord.nodes[down].data.get(key) is None
    coord.revive_node(down)
    revived = coord.nodes[down].local_get(key)
    assert revived is not None
    assert revived.value == "hinted-value"
