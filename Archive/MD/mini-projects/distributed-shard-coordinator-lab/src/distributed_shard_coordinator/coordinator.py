"""
Shard coordinator — routes keys, enforces W/R quorums, hinted handoff, read repair.

This is the **data plane control path** in miniature: no persistent WAL,
no anti-entropy Merkle trees, but the same request fan-out pattern you see
in Dynamo, Cassandra, and Riak.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from distributed_shard_coordinator.errors import (
    NodeUnavailableError,
    QuorumNotMetError,
    StaleReadError,
)
from distributed_shard_coordinator.ring import HashRing
from distributed_shard_coordinator.shard_node import Hint, ShardNode
from distributed_shard_coordinator.types import QuorumConfig, ReadResult, StoredRecord, WriteResult


@dataclass
class ShardCoordinator:
    ring: HashRing
    nodes: dict[str, ShardNode]
    quorum: QuorumConfig = field(default_factory=QuorumConfig)
    # Coordinator-side version source (Dynamo uses client clocks or coordinator time).
    _versions: dict[str, int] = field(default_factory=dict)
    strict_reads: bool = False

    def register_node(self, node_id: str) -> ShardNode:
        self.ring.add_node(node_id)
        shard = ShardNode(node_id=node_id)
        self.nodes[node_id] = shard
        return shard

    def kill_node(self, node_id: str) -> None:
        self.nodes[node_id].kill()

    def revive_node(self, node_id: str) -> int:
        """
        Bring a node back and flush hinted handoffs from every peer.

        Production: hints are replayed asynchronously with rate limits.
        """
        node = self.nodes[node_id]
        node.revive()
        delivered = 0
        for peer in self.nodes.values():
            if not peer.alive:
                continue
            for hint in [h for h in peer.hints if h.target_node == node_id]:
                try:
                    node.local_put(hint.key, hint.record)
                    delivered += 1
                except NodeUnavailableError:
                    pass
            peer.hints = [h for h in peer.hints if h.target_node != node_id]
        return delivered

    def _next_version(self, key: str) -> int:
        v = self._versions.get(key, 0) + 1
        self._versions[key] = v
        return v

    def _preference(self, key: str) -> list[str]:
        self.quorum.validate()
        return self.ring.replica_nodes(key, self.quorum.replication_factor)

    def put(self, key: str, value: str) -> WriteResult:
        """
        Quorum write: contact RF preferred replicas; use sloppy quorum + hints if needed.

        Steps (Dynamo write path simplified):
        1. Compute preference list from consistent hash.
        2. Fan out parallel puts (here: sequential for teaching clarity).
        3. Count successes until W met; if preferred node down, hint to next alive node.
        """
        version = self._next_version(key)
        record = StoredRecord(value=value, version=version)
        pref = self._preference(key)
        w = self.quorum.write_quorum

        acknowledged: set[str] = set()
        hinted = 0
        tried: set[str] = set()

        def ack(node_id: str) -> None:
            acknowledged.add(node_id)

        # First pass: preferred replicas
        for node_id in pref:
            tried.add(node_id)
            if self._try_replica_put(node_id, key, record):
                ack(node_id)
            else:
                # Hinted handoff counts toward W on the substitute node (Dynamo §4.6).
                alt = self._hint_to_alternate(key, record, pref, tried)
                if alt:
                    ack(alt)
                    hinted += 1

        # Sloppy quorum: if still short of W distinct acks, walk more nodes on the ring
        while len(acknowledged) < w:
            extra = self.ring.successor_nodes(key, tried, 1)
            if not extra:
                break
            node_id = extra[0]
            tried.add(node_id)
            if self._try_replica_put(node_id, key, record):
                ack(node_id)

        successes = len(acknowledged)
        if successes < w:
            raise QuorumNotMetError("write", w, successes)

        return WriteResult(
            key=key,
            value=value,
            version=version,
            replicas_written=successes,
            hinted=hinted,
        )

    def _try_replica_put(self, node_id: str, key: str, record: StoredRecord) -> bool:
        node = self.nodes[node_id]
        try:
            node.local_put(key, record)
            return True
        except NodeUnavailableError:
            return False

    def _hint_to_alternate(
        self,
        key: str,
        record: StoredRecord,
        pref: list[str],
        tried: set[str],
    ) -> str | None:
        """Store one hint on the next alive node not in `tried`; return that node id."""
        down_targets = [n for n in pref if not self.nodes[n].alive]
        if not down_targets:
            return None
        target = down_targets[0]
        alternates = self.ring.successor_nodes(key, tried | set(pref), 3)
        for alt_id in alternates:
            alt = self.nodes[alt_id]
            if not alt.alive:
                continue
            try:
                alt.store_hint(Hint(target_node=target, key=key, record=record))
                return alt_id
            except NodeUnavailableError:
                continue
        return None

    def get(self, key: str, *, allow_stale: bool = True) -> ReadResult:
        """
        Quorum read: fetch from R replicas, return highest version (LWW).

        If replicas disagree and `strict_reads` is True, raise StaleReadError
        instead of merging — useful for teaching detection vs. repair.
        """
        pref = self._preference(key)
        r = self.quorum.read_quorum
        # (node_id, record or None if replica is up but key is absent)
        responses: list[tuple[str, StoredRecord | None]] = []

        def contact(node_id: str) -> bool:
            node = self.nodes[node_id]
            try:
                responses.append((node_id, node.local_get(key)))
                return True
            except NodeUnavailableError:
                return False

        for node_id in pref:
            if contact(node_id) and len(responses) >= r:
                break

        tried = set(pref)
        while len(responses) < r:
            extra = self.ring.successor_nodes(key, tried, 1)
            if not extra:
                break
            node_id = extra[0]
            tried.add(node_id)
            contact(node_id)

        if len(responses) < r:
            raise QuorumNotMetError("read", r, len(responses))

        present = [(nid, rec) for nid, rec in responses if rec is not None]
        if not present:
            return ReadResult(
                key=key,
                value=None,
                version=0,
                replicas_read=len(responses),
                repaired=False,
            )

        versions = [rec.version for _, rec in present]
        if self.strict_reads and len(set(versions)) > 1:
            raise StaleReadError(key, versions)

        _, best = max(present, key=lambda pair: pair[1].version)
        repaired = self._maybe_read_repair(key, responses, best)

        return ReadResult(
            key=key,
            value=best.value,
            version=best.version,
            replicas_read=len(responses),
            repaired=repaired,
        )

    def _maybe_read_repair(
        self,
        key: str,
        responses: list[tuple[str, StoredRecord | None]],
        best: StoredRecord,
    ) -> bool:
        """
        Read repair: push the winning version to lagging replicas.

        Production systems do this asynchronous to protect tail latency.
        """
        repaired = False
        for node_id, rec in responses:
            if rec is None or rec.version < best.version:
                if self._try_replica_put(node_id, key, best):
                    repaired = True
        return repaired
