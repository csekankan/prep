"""Classic Bloom filter — no false negatives, possible false positives."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class BloomFilter:
    size: int
    num_hashes: int = 3
    bits: bytearray | None = None

    def __post_init__(self) -> None:
        self.bits = bytearray(self.size)

    def _indexes(self, item: str) -> list[int]:
        out = []
        for i in range(self.num_hashes):
            h = hashlib.sha256(f"{i}:{item}".encode()).digest()
            out.append(int.from_bytes(h[:4], "big") % self.size)
        return out

    def add(self, item: str) -> None:
        for idx in self._indexes(item):
            self.bits[idx] = 1

    def __contains__(self, item: str) -> bool:
        return all(self.bits[idx] for idx in self._indexes(item))
