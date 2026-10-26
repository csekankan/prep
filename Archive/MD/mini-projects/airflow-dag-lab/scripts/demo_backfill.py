#!/usr/bin/env python3
from datetime import date

from airflow_dag_lab.dag import Dag, Task, TaskState

log: list[str] = []


def extract() -> None:
    log.append("extract")


def transform() -> None:
    log.append("transform")


def load() -> None:
    log.append("load")


dag = Dag(dag_id="daily_etl")
dag.add_task(Task("extract", extract))
dag.add_task(Task("transform", transform))
dag.add_task(Task("load", load))
dag.set_upstream("transform", "extract")
dag.set_upstream("load", "transform")

for run in dag.backfill(date(2025, 1, 1), date(2025, 1, 3)):
    ok = all(ti.state == TaskState.SUCCESS for ti in run.instances.values())
    print(run.logical_date, "OK" if ok else "FAIL", list(run.instances.keys()))
