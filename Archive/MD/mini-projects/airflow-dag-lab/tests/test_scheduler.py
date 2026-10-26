from datetime import date

from airflow_dag_lab.scheduler import DagDefinition, Scheduler, TaskDef, TaskState


def test_dag_runs_in_order_with_retry() -> None:
    log: list[str] = []

    def extract(d: date) -> None:
        log.append(f"extract:{d}")

    dag = DagDefinition(
        dag_id="daily_etl",
        tasks={
            "extract": TaskDef("extract", fn=extract, fail_until_attempt=1, retries=2),
            "load": TaskDef("load", upstream=["extract"], fn=lambda d: log.append(f"load:{d}")),
        },
    )
    sched = Scheduler(dag)
    states = sched.run_dag_run(date(2026, 10, 26))
    assert states["extract"] == TaskState.SUCCESS
    assert states["load"] == TaskState.SUCCESS
    assert log[0].startswith("extract")


def test_cycle_rejected() -> None:
    dag = DagDefinition(
        dag_id="bad",
        tasks={
            "a": TaskDef("a", upstream=["b"]),
            "b": TaskDef("b", upstream=["a"]),
        },
    )
    try:
        Scheduler(dag)
        assert False
    except ValueError as e:
        assert "cycle" in str(e)
