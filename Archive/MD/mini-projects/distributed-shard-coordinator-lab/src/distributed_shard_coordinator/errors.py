"""
Typed errors for the data plane.

Production systems surface distinct failure modes so callers can retry,
fail over, or surface SLA violations. This lab mirrors Dynamo-style
distinctions: quorum not met vs. node down vs. stale read policy.
"""

from __future__ import annotations


class CoordinatorError(Exception):
    """Base for all coordinator / shard errors."""


class EmptyRingError(CoordinatorError):
    """No nodes are registered on the hash ring (or not enough for RF)."""


class QuorumNotMetError(CoordinatorError):
    """Fewer than W (write) or R (read) replicas acknowledged the operation."""

    def __init__(self, operation: str, required: int, achieved: int) -> None:
        self.operation = operation
        self.required = required
        self.achieved = achieved
        super().__init__(
            f"{operation} quorum not met: need {required} replica(s), got {achieved}"
        )


class NodeUnavailableError(CoordinatorError):
    """Target replica is marked down (simulated crash / network partition)."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"node unavailable: {node_id}")


class StaleReadError(CoordinatorError):
    """
    Returned when strict consistency is requested but replicas disagree.

    In production you usually pick the highest version (eventual consistency)
    and optionally schedule read repair; this error teaches detection.
    """

    def __init__(self, key: str, versions: list[int]) -> None:
        self.key = key
        self.versions = versions
        super().__init__(f"stale read detected for {key!r}: versions {versions}")


class VersionConflictError(CoordinatorError):
    """Replica rejected a write because an equal-or-newer version already exists."""

    def __init__(self, key: str, existing_version: int, attempted: int) -> None:
        self.key = key
        self.existing_version = existing_version
        self.attempted = attempted
        super().__init__(
            f"version conflict on {key!r}: have {existing_version}, tried {attempted}"
        )
