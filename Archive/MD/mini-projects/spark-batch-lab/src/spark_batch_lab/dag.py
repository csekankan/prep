"""
Toy Spark batch planner: lazy DAG, shuffle stages, salted group-by for skew.

No JVM — teaches narrow vs wide and partition skew mitigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class OpKind(str, Enum):
    NARROW = "narrow"
    WIDE = "wide"  # shuffle


@dataclass
class Op:
    name: str
    kind: OpKind
    fn: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]


@dataclass
class BatchJob:
    partitions: list[list[dict[str, Any]]]
    ops: list[Op] = field(default_factory=list)
    shuffle_count: int = 0

    def filter(self, name: str, pred: Callable[[dict[str, Any]], bool]) -> BatchJob:
        self.ops.append(
            Op(name, OpKind.NARROW, lambda rows: [r for r in rows if pred(r)])
        )
        return self

    def map_rows(self, name: str, mapper: Callable[[dict[str, Any]], dict[str, Any]]) -> BatchJob:
        self.ops.append(Op(name, OpKind.NARROW, lambda rows: [mapper(r) for r in rows]))
        return self

    def group_sum(self, name: str, key: str, value_field: str) -> BatchJob:
        self.shuffle_count += 1

        def wide_placeholder(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return rows  # shuffle + aggregate happen in run()

        self.ops.append(Op(name, OpKind.WIDE, wide_placeholder))
        self._pending_group = (key, value_field, name)
        return self

    def run(self) -> dict[str, Any]:
        data = [list(p) for p in self.partitions]
        stages: list[list[str]] = []
        current_stage: list[str] = []
        pending_group: tuple[str, str, str] | None = getattr(self, "_pending_group", None)

        for op in self.ops:
            if op.kind == OpKind.NARROW:
                current_stage.append(op.name)
                data = [op.fn(part) for part in data]
            else:
                if current_stage:
                    stages.append(current_stage)
                    current_stage = []
                stages.append([op.name + " (shuffle)"])
                key, val, _ = pending_group or ("", "", "")
                combined: dict[str, float] = {}
                for part in data:
                    for row in part:
                        k = str(row.get(key))
                        combined[k] = combined.get(k, 0.0) + float(row.get(val, 0))
                aggregated = [{key: k, val: v} for k, v in sorted(combined.items())]
                # repartition into 2 fake partitions for teaching
                mid = max(1, len(aggregated) // 2)
                data = [aggregated[:mid], aggregated[mid:]] if aggregated else [[], []]
        if current_stage:
            stages.append(current_stage)

        flat = [r for part in data for r in part]
        return {
            "result": flat,
            "shuffle_count": self.shuffle_count,
            "stages": stages,
        }


def salted_group_sum(
    rows: list[dict[str, Any]], key: str, value_field: str, salts: int = 4
) -> list[dict[str, Any]]:
    """Two-phase aggregate: add salt to spread hot keys, then merge."""
    partial: dict[tuple[str, int], float] = {}
    for row in rows:
        base = str(row[key])
        # Map each row to one salt bucket (spreads hot keys across reducers)
        s = abs(hash((base, id(row)))) % salts
        partial[(base, s)] = partial.get((base, s), 0.0) + float(row[value_field])
    merged: dict[str, float] = {}
    for (base, _), v in partial.items():
        merged[base] = merged.get(base, 0.0) + v
    return [{key: k, value_field: v} for k, v in sorted(merged.items())]
