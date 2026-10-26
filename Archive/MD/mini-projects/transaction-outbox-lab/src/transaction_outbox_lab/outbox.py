"""
In-memory "database" with outbox table + background relay.

Production: Postgres outbox + Debezium / custom poller → Kafka.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"


@dataclass
class Order:
    id: str
    amount: int


@dataclass
class OutboxMessage:
    id: str
    topic: str
    payload: dict
    status: OutboxStatus = OutboxStatus.PENDING


@dataclass
class FakeDB:
    orders: dict[str, Order] = field(default_factory=dict)
    outbox: list[OutboxMessage] = field(default_factory=list)

    def place_order_in_transaction(self, amount: int) -> Order:
        """Atomic write: order + outbox event in one commit."""
        order = Order(id=str(uuid.uuid4()), amount=amount)
        self.orders[order.id] = order
        self.outbox.append(
            OutboxMessage(
                id=str(uuid.uuid4()),
                topic="orders.created",
                payload={"order_id": order.id, "amount": amount},
            )
        )
        return order


@dataclass
class OutboxRelay:
    published: list[OutboxMessage] = field(default_factory=list)

    def poll_and_publish(self, db: FakeDB) -> int:
        count = 0
        for msg in db.outbox:
            if msg.status == OutboxStatus.PENDING:
                self.published.append(msg)
                msg.status = OutboxStatus.PUBLISHED
                count += 1
        return count
