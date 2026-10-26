"""
Consistent hashing ring — same pattern as consistent-hash-lab.

Virtual nodes spread load; clockwise walk from a key's hash yields the
preference list for replication (Dynamo / Cassandra style).
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field

from distributed_shard_coordinator.errors import EmptyRingError


def _hash32(key: str) -> int:
    """MD5-based 32-bit token (teaching default; production rings use murmur3 / xxhash)."""
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)


@dataclass
class HashRing:
    """
    In-memory consistent hash ring.

    Production note: rings are usually stored in ZooKeeper / etcd and
    updated via gossip; clients cache a snapshot and refresh on mismatch.
    """

    vnodes_per_node: int = 128
    ring: list[int] = field(default_factory=list)
    owners: dict[int, str] = field(default_factory=dict)

    def add_node(self, node: str) -> None:
        for i in range(self.vnodes_per_node):
            token = f"{node}#{i}"
            h = _hash32(token)
            self.owners[h] = node
            bisect.insort(self.ring, h)

    def remove_node(self, node: str) -> None:
        to_drop = [h for h, n in self.owners.items() if n == node]
        for h in to_drop:
            del self.owners[h]
            self.ring.remove(h)

    def get_node(self, key: str) -> str:
        """Primary owner for a key (first replica in the preference list)."""
        nodes = self.replica_nodes(key, 1)
        return nodes[0]

    def replica_nodes(self, key: str, count: int) -> list[str]:
        """
        Walk the ring clockwise from hash(key) and collect `count` unique physical nodes.

        This is the **preference list** used for replication factor RF.
        """
        if not self.ring or count < 1:
            raise EmptyRingError()

        start = _hash32(key)
        idx = bisect.bisect(self.ring, start)
        if idx == len(self.ring):
            idx = 0

        seen: set[str] = set()
        result: list[str] = []
        pos = idx
        scanned = 0
        # At most one full lap; with RF <= live nodes we always terminate.
        while len(result) < count and scanned < len(self.ring):
            token = self.ring[pos]
            node = self.owners[token]
            if node not in seen:
                seen.add(node)
                result.append(node)
            pos = (pos + 1) % len(self.ring)
            scanned += 1

        if len(result) < count:
            raise EmptyRingError(
                f"ring has only {len(result)} distinct node(s), need {count}"
            )
        return result

    def successor_nodes(self, key: str, skip: set[str], count: int) -> list[str]:
        """
        Additional nodes beyond the preference list — used for sloppy quorum /
        hinted handoff when preferred replicas are down.
        """
        if not self.ring:
            raise EmptyRingError()

        start = _hash32(key)
        idx = bisect.bisect(self.ring, start)
        if idx == len(self.ring):
            idx = 0

        seen = set(skip)
        result: list[str] = []
        pos = idx
        scanned = 0
        while len(result) < count and scanned < len(self.ring):
            token = self.ring[pos]
            node = self.owners[token]
            if node not in seen:
                seen.add(node)
                result.append(node)
            pos = (pos + 1) % len(self.ring)
            scanned += 1
        return result
