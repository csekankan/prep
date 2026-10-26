"""Shared value types for coordinator responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoredRecord:
    """One versioned key-value tuple on a replica."""

    value: str
    version: int


@dataclass(frozen=True)
class QuorumConfig:
    """
    Dynamo-style tunable consistency.

    With RF=3, W=2, R=2 you get a typical AP-leaning profile (W+R > RF gives
    a chance of overlapping quorums for read-your-writes style guarantees).
    """

    replication_factor: int = 3
    write_quorum: int = 2
    read_quorum: int = 2

    def validate(self) -> None:
        if self.write_quorum < 1 or self.read_quorum < 1:
            raise ValueError("W and R must be >= 1")
        if self.replication_factor < 1:
            raise ValueError("RF must be >= 1")
        if self.write_quorum > self.replication_factor:
            raise ValueError("W cannot exceed RF")
        if self.read_quorum > self.replication_factor:
            raise ValueError("R cannot exceed RF")


@dataclass(frozen=True)
class WriteResult:
    key: str
    value: str
    version: int
    replicas_written: int
    hinted: int


@dataclass(frozen=True)
class ReadResult:
    key: str
    value: str | None
    version: int
    replicas_read: int
    repaired: bool
