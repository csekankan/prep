#!/usr/bin/env python3
"""Demo: two consumer group passes — second pass skips committed offsets."""

from kafka_log_lab.log import ConsumerGroup, PartitionedLog, consume_idempotent


def main() -> None:
    log = PartitionedLog(num_partitions=3)
    for i in range(6):
        log.append(f"user-{i % 2}", {"event_id": f"e{i}", "amount": i * 10})

    group = ConsumerGroup(group_id="warehouse-loader")
    seen: set[str] = set()
    totals: list[int] = []

    def handle(rec):
        totals.append(rec.value["amount"])
        print(f"  p={rec.partition} off={rec.offset} amount={rec.value['amount']}")

    print("First poll:")
    for p in range(3):
        consume_idempotent(log, group, p, handle, seen)

    print("Second poll (no new data):")
    for p in range(3):
        n = consume_idempotent(log, group, p, handle, seen)
        print(f"  partition {p}: {n} records")

    print(f"Total processed amounts: {sum(totals)}")


if __name__ == "__main__":
    main()
