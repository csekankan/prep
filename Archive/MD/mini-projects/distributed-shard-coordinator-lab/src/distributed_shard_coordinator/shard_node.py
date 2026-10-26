"""
In-memory shard replica — simulates a partition on one physical node.

Production analog: a Dynamo storage node holding SSTables / memtables,
or a Redis shard with AOF. We keep version integers instead of vector
clocks for clarity; the coordinator still performs last-write-wins merge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from distributed_shard_coordinator.errors import NodeUnavailableError, VersionConflictError
from distributed_shard_coordinator.types import StoredRecord


@dataclass
class Hint:
    """
    Hinted handoff payload.

    When the intended replica is down, another node temporarily stores
    (target_node, key, record) until the target returns — then the hint
    is delivered and deleted (Dynamo paper §4.6).
    """

    target_node: str
    key: str
    record: StoredRecord


@dataclass
class ShardNode:
    node_id: str
    alive: bool = True
    # Local authoritative data for keys this node owns (or has replicated).
    data: dict[str, StoredRecord] = field(default_factory=dict)
    # Hints we are holding for peers that were unavailable during a write.
    hints: list[Hint] = field(default_factory=list)

    def kill(self) -> None:
        """Simulate crash / network isolation."""
        self.alive = False

    def revive(self) -> None:
        self.alive = True

    def _check_alive(self) -> None:
        if not self.alive:
            raise NodeUnavailableError(self.node_id)

    def local_put(self, key: str, record: StoredRecord) -> None:
        """
        Apply a write at this replica (idempotent if version is newer).

        Replicas reject strictly older versions so concurrent writers cannot
        roll back state — production systems use timestamps + node ids tie-break.
        """
        self._check_alive()
        existing = self.data.get(key)
        if existing is not None and record.version < existing.version:
            raise VersionConflictError(key, existing.version, record.version)
        if existing is not None and record.version == existing.version:
            return  # idempotent retry
        self.data[key] = record

    def local_get(self, key: str) -> StoredRecord | None:
        self._check_alive()
        return self.data.get(key)

    def store_hint(self, hint: Hint) -> None:
        """Accept hinted handoff while `hint.target_node` is down."""
        self._check_alive()
        self.hints.append(hint)

    def deliver_hints_for(self, target_node: str) -> int:
        """
        On recovery, push hinted writes to `target_node` and clear local hints.

        Returns count of hints delivered (coordinator calls this after revive).
        """
        self._check_alive()
        pending = [h for h in self.hints if h.target_node == target_node]
        self.hints = [h for h in self.hints if h.target_node != target_node]
        return len(pending)

    def pending_hints(self) -> list[Hint]:
        return list(self.hints)
