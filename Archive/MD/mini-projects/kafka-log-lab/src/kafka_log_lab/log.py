"""
Minimal partitioned log + consumer groups (Kafka teaching model).

Production: Apache Kafka brokers, ISR, transactions. Here: correctness patterns only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Iterator


@dataclass(frozen=True)
class Record:
    key: str | None
    value: dict
    offset: int
    partition: int


@dataclass
class PartitionedLog:
    """Append-only logs sharded by partition."""

    num_partitions: int
    _logs: list[list[dict]] = field(default_factory=list)
    _next_offset: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.num_partitions < 1:
            raise ValueError("num_partitions must be >= 1")
        if not self._logs:
            self._logs = [[] for _ in range(self.num_partitions)]
            self._next_offset = [0 for _ in range(self.num_partitions)]

    def _partition_for(self, key: str | None) -> int:
        if key is None:
            # round-robin via current smallest length (teaching simplification)
            return min(range(self.num_partitions), key=lambda p: len(self._logs[p]))
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return h % self.num_partitions

    def append(self, key: str | None, value: dict) -> Record:
        p = self._partition_for(key)
        off = self._next_offset[p]
        self._logs[p].append({"key": key, "value": value})
        self._next_offset[p] += 1
        return Record(key=key, value=value, offset=off, partition=p)

    def read(self, partition: int, start_offset: int) -> list[Record]:
        out: list[Record] = []
        for i, raw in enumerate(self._logs[partition][start_offset:]):
            out.append(
                Record(
                    key=raw["key"],
                    value=raw["value"],
                    offset=start_offset + i,
                    partition=partition,
                )
            )
        return out


@dataclass
class ConsumerGroup:
    """
    Tracks committed offsets per (group, partition).
    Assigns partitions across members in the group.
    """

    group_id: str
    committed: dict[tuple[str, int], int] = field(default_factory=dict)

    def assign_partitions(self, member_id: str, member_ids: list[str], num_partitions: int) -> list[int]:
        """Simple stable assignment: sort members, round-robin partitions."""
        ordered = sorted(member_ids)
        idx = ordered.index(member_id)
        return [p for p in range(num_partitions) if p % len(ordered) == idx]

    def committed_offset(self, partition: int) -> int:
        return self.committed.get((self.group_id, partition), 0)

    def commit(self, partition: int, next_offset: int) -> None:
        self.committed[(self.group_id, partition)] = next_offset


def consume_idempotent(
    log: PartitionedLog,
    group: ConsumerGroup,
    partition: int,
    handler: Callable[[Record], None],
    seen_ids: set[str],
) -> int:
    """
    At-least-once style: process then commit.
    `seen_ids` makes handler idempotent on event_id (production: DB unique key).
    """
    start = group.committed_offset(partition)
    records = log.read(partition, start)
    last = start
    for rec in records:
        event_id = rec.value.get("event_id")
        if event_id and event_id in seen_ids:
            last = rec.offset + 1
            continue
        handler(rec)
        if event_id:
            seen_ids.add(event_id)
        last = rec.offset + 1
    group.commit(partition, last)
    return len(records)


def replay_from_beginning(log: PartitionedLog, partition: int) -> Iterator[Record]:
    yield from log.read(partition, 0)
