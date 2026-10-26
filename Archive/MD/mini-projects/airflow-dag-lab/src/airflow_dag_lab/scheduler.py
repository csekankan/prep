"""
Minimal Airflow-like DAG runner: topological order, retries, backfill dates.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Callable


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    UP_FOR_RETRY = "up_for_retry"


@dataclass
class TaskDef:
    task_id: str
    upstream: list[str] = field(default_factory=list)
    retries: int = 0
    fn: Callable[[date], None] | None = None
    fail_until_attempt: int = 0  # teaching: fail first N attempts


@dataclass
class DagDefinition:
    dag_id: str
    tasks: dict[str, TaskDef]

    def validate(self) -> None:
        for tid, t in self.tasks.items():
            for up in t.upstream:
                if up not in self.tasks:
                    raise ValueError(f"unknown upstream {up} for {tid}")
        if _has_cycle(self.tasks):
            raise ValueError("DAG has cycle")


def _has_cycle(tasks: dict[str, TaskDef]) -> bool:
    indeg = {tid: len(t.upstream) for tid, t in tasks.items()}
    children: dict[str, list[str]] = {tid: [] for tid in tasks}
    for tid, t in tasks.items():
        for up in t.upstream:
            children[up].append(tid)
    q = deque([tid for tid, d in indeg.items() if d == 0])
    seen = 0
    while q:
        n = q.popleft()
        seen += 1
        for c in children[n]:
            indeg[c] -= 1
            if indeg[c] == 0:
                q.append(c)
    return seen != len(tasks)


@dataclass
class TaskInstance:
    logical_date: date
    state: TaskState = TaskState.PENDING
    attempt: int = 0


@dataclass
class Scheduler:
    dag: DagDefinition

    def __post_init__(self) -> None:
        self.dag.validate()

    def topo_order(self) -> list[str]:
        indeg = {tid: len(t.upstream) for tid, t in self.dag.tasks.items()}
        children: dict[str, list[str]] = {tid: [] for tid in self.dag.tasks}
        for tid, t in self.dag.tasks.items():
            for up in t.upstream:
                children[up].append(tid)
        q = deque(sorted(tid for tid, d in indeg.items() if d == 0))
        order: list[str] = []
        while q:
            n = q.popleft()
            order.append(n)
            for c in sorted(children[n]):
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        return order

    def run_dag_run(self, logical_date: date) -> dict[str, TaskState]:
        instances = {tid: TaskInstance(logical_date) for tid in self.dag.tasks}
        for tid in self.topo_order():
            self._run_task(tid, instances)
            if instances[tid].state == TaskState.FAILED:
                break
        return {tid: inst.state for tid, inst in instances.items()}

    def _run_task(self, tid: str, instances: dict[str, TaskInstance]) -> None:
        tdef = self.dag.tasks[tid]
        for up in tdef.upstream:
            if instances[up].state != TaskState.SUCCESS:
                instances[tid].state = TaskState.FAILED
                return
        inst = instances[tid]
        while inst.attempt <= tdef.retries:
            inst.attempt += 1
            inst.state = TaskState.RUNNING
            try:
                if inst.attempt <= tdef.fail_until_attempt:
                    raise RuntimeError(f"simulated failure {tid}")
                if tdef.fn:
                    tdef.fn(inst.logical_date)
                inst.state = TaskState.SUCCESS
                return
            except RuntimeError:
                if inst.attempt <= tdef.retries:
                    inst.state = TaskState.UP_FOR_RETRY
                else:
                    inst.state = TaskState.FAILED
                    return

    def backfill(self, start: date, end: date) -> list[dict[str, TaskState]]:
        results = []
        d = start
        while d <= end:
            results.append(self.run_dag_run(d))
            d += timedelta(days=1)
        return results
