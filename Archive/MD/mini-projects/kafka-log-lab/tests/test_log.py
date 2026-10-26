from kafka_log_lab.log import ConsumerGroup, PartitionedLog, consume_idempotent


def test_same_key_same_partition() -> None:
    log = PartitionedLog(num_partitions=4)
    r1 = log.append("user-1", {"event_id": "a", "n": 1})
    r2 = log.append("user-1", {"event_id": "b", "n": 2})
    assert r1.partition == r2.partition


def test_consumer_group_commit_and_resume() -> None:
    log = PartitionedLog(num_partitions=2)
    log.append("k", {"event_id": "1", "x": 1})
    log.append("k", {"event_id": "2", "x": 2})
    g = ConsumerGroup(group_id="billing")
    p = log.append("k", {"event_id": "1", "x": 1}).partition
    seen: set[str] = set()
    processed: list[int] = []

    def handle(rec):
        processed.append(rec.value["x"])

    n = consume_idempotent(log, g, p, handle, seen)
    assert n == 3
    assert processed == [1, 2]  # duplicate event_id skipped
    processed.clear()
    n2 = consume_idempotent(log, g, p, handle, seen)
    assert n2 == 0
    assert processed == []


def test_idempotent_skips_duplicate_event_id() -> None:
    log = PartitionedLog(num_partitions=1)
    log.append(None, {"event_id": "dup", "v": 1})
    log.append(None, {"event_id": "dup", "v": 2})
    g = ConsumerGroup(group_id="g1")
    seen: set[str] = set()
    vals: list[int] = []

    def handle(rec):
        vals.append(rec.value["v"])

    consume_idempotent(log, g, 0, handle, seen)
    assert vals == [1]
