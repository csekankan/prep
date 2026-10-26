from transaction_outbox_lab.outbox import FakeDB, OutboxRelay, OutboxStatus


def test_relay_publishes_once() -> None:
    db = FakeDB()
    relay = OutboxRelay()
    db.place_order_in_transaction(100)
    assert relay.poll_and_publish(db) == 1
    assert relay.poll_and_publish(db) == 0
    assert db.outbox[0].status == OutboxStatus.PUBLISHED
