#!/usr/bin/env python3
from rich.console import Console

from consistent_hash_lab.ring import HashRing

console = Console()


def main() -> None:
    keys = [f"user:{i}" for i in range(10_000)]
    before = ["shard-a", "shard-b", "shard-c"]
    after = ["shard-a", "shard-b", "shard-c", "shard-d"]
    ring = HashRing()
    frac = ring.key_move_fraction(keys, before, after)
    console.print(f"Adding shard-d moves ~{frac*100:.1f}% of keys (modulo hashing would move ~75%)")


if __name__ == "__main__":
    main()
