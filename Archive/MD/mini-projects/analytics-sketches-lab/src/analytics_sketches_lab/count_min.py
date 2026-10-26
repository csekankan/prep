"""Count-Min sketch — approximate frequency with bounded memory."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class CountMinSketch:
    width: int = 1000
    depth: int = 5
    table: list[list[int]] = field(init=False)

    def __post_init__(self) -> None:
        self.table = [[0] * self.width for _ in range(self.depth)]

    def _hash(self, item: str, row: int) -> int:
        h = hashlib.md5(f"{row}:{item}".encode()).hexdigest()
        return int(h, 16) % self.width

    def add(self, item: str, count: int = 1) -> None:
        for row in range(self.depth):
            col = self._hash(item, row)
            self.table[row][col] += count

    def estimate(self, item: str) -> int:
        return min(self.table[row][self._hash(item, row)] for row in range(self.depth))
