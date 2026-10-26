"""
Airflow-style DAG execution without Airflow installed.

Maps to concepts in data-engineering/airflow/detailed.md:
  - Task dependencies (upstream → downstream)
  - TaskInstance states: pending → running → success | failed | up_for_retry
  - DagRun per logical_date; catchup backfill over a date range
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
    SKIPPED = "skipped"


@dataclass
class Task:
    task_id: str
    callable: Callable[[], None]
    retries: int = 0
    upstream: set[str] = field(default_factory=set)


@dataclass
class TaskInstance:
    task_id: str
    logical_date: date
    state: TaskState = TaskState.PENDING
    try_number: int = 0


@dataclass
class DagRun:
    logical_date: date
    instances: dict[str, TaskInstance] = field(default_factory=dict)


@dataclass
class Dag:
    dag_id: str
    tasks: dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> Task:
        self.tasks[task.task_id] = task
        return task

    def set_upstream(self, downstream_id: str, upstream_id: str) -> None:
        self.tasks[downstream_id].upstream.add(upstream_id)

    def _topo_order(self) -> list[str]:
        indeg = {tid: len(t.upstream) for tid, t in self.tasks.items()}
        children: dict[str, list[str]] = {tid: [] for tid in self.tasks}
        for tid, t in self.tasks.items():
            for u in t.upstream:
                children[u].append(tid)
        q = deque([tid for tid, d in indeg.items() if d == 0])
        order: list[str] = []
        while q:
            n = q.popleft()
            order.append(n)
            for c in children[n]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        if len(order) != len(self.tasks):
            raise ValueError("cycle in DAG")
        return order

    def run(self, logical_date: date) -> DagRun:
        """Execute one DagRun — all tasks in dependency order with retries."""
        run = DagRun(logical_date=logical_date)
        for tid in self.tasks:
            run.instances[tid] = TaskInstance(task_id=tid, logical_date=logical_date)

        for tid in self._topo_order():
            task = self.tasks[tid]
            ti = run.instances[tid]
            # Skip if any upstream failed
            if any(run.instances[u].state == TaskState.FAILED for u in task.upstream):
                ti.state = TaskState.SKIPPED
                continue

            while True:
                ti.state = TaskState.RUNNING
                ti.try_number += 1
                try:
                    task.callable()
                    ti.state = TaskState.SUCCESS
                    break
                except Exception:
                    if ti.try_number <= task.retries:
                        ti.state = TaskState.UP_FOR_RETRY
                        continue
                    ti.state = TaskState.FAILED
                    break
        return run

    def backfill(self, start: date, end: date) -> list[DagRun]:
        """catchup=True style: one DagRun per day inclusive."""
        runs: list[DagRun] = []
        d = start
        while d <= end:
            runs.append(self.run(d))
            d += timedelta(days=1)
        return runs
