"""Simplified HyperLogLog — estimate distinct count in O(1) memory."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field


def _hash64(item: str) -> int:
    return int(hashlib.sha256(item.encode()).hexdigest()[:16], 16)


@dataclass
class HyperLogLog:
    """
    p = precision → m = 2^p registers.

    Each item hashes to (bucket, leading_zeros); we keep max leading zeros per bucket.
    """

    precision: int = 14
    registers: list[int] = field(init=False)

    def __post_init__(self) -> None:
        m = 1 << self.precision
        self.registers = [0] * m

    def add(self, item: str) -> None:
        h = _hash64(item)
        idx = h & ((1 << self.precision) - 1)
        w = h >> self.precision
        # Leading zeros in the upper (64 - p) bits, plus one (standard HLL ρ)
        tail_bits = 64 - self.precision
        mask = (1 << tail_bits) - 1
        w_tail = w & mask
        if w_tail == 0:
            rho = tail_bits + 1
        else:
            rho = tail_bits - w_tail.bit_length() + 1
        if rho > self.registers[idx]:
            self.registers[idx] = rho

    def estimate(self) -> float:
        m = len(self.registers)
        alpha = 0.7213 / (1 + 1.079 / m)
        z = sum(2.0 ** (-r) for r in self.registers)
        e = alpha * m * m / z
        # Small-range correction (many zero registers → raw estimate is high)
        if e <= 2.5 * m:
            v = sum(1 for r in self.registers if r == 0)
            if v:
                e = m * math.log(m / v)
        return e
