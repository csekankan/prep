"""
Consistent hashing — add/remove shards without reshuffling the whole keyspace.

Each physical node gets many virtual nodes on the ring for even load spread.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field


def _hash32(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)


@dataclass
class HashRing:
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
        if not self.ring:
            raise RuntimeError("empty ring")
        h = _hash32(key)
        idx = bisect.bisect(self.ring, h)
        if idx == len(self.ring):
            idx = 0
        return self.owners[self.ring[idx]]

    def key_move_fraction(self, keys: list[str], before: list[str], after: list[str]) -> float:
        """Fraction of keys that change shard when ring membership changes."""
        ring_before = HashRing(self.vnodes_per_node)
        for n in before:
            ring_before.add_node(n)
        ring_after = HashRing(self.vnodes_per_node)
        for n in after:
            ring_after.add_node(n)
        moved = sum(1 for k in keys if ring_before.get_node(k) != ring_after.get_node(k))
        return moved / len(keys)
