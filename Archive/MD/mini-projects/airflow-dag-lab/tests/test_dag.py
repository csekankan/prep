from datetime import date

from airflow_dag_lab.dag import Dag, Task, TaskState


def test_runs_extract_transform_load_order() -> None:
    order: list[str] = []

    dag = Dag("t")
    dag.add_task(Task("extract", lambda: order.append("e")))
    dag.add_task(Task("transform", lambda: order.append("t")))
    dag.add_task(Task("load", lambda: order.append("l")))
    dag.set_upstream("transform", "extract")
    dag.set_upstream("load", "transform")
    dag.run(date(2025, 6, 1))
    assert order == ["e", "t", "l"]


def test_retry_then_success() -> None:
    attempts = {"n": 0}

    def flaky() -> None:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise RuntimeError("transient")

    dag = Dag("retry")
    dag.add_task(Task("only", flaky, retries=2))
    run = dag.run(date(2025, 1, 1))
    assert run.instances["only"].state == TaskState.SUCCESS
    assert attempts["n"] == 2


def test_backfill_three_days() -> None:
    dag = Dag("bf")
    dag.add_task(Task("a", lambda: None))
    runs = dag.backfill(date(2025, 1, 1), date(2025, 1, 3))
    assert len(runs) == 3
    assert runs[0].logical_date == date(2025, 1, 1)
    assert runs[-1].logical_date == date(2025, 1, 3)
