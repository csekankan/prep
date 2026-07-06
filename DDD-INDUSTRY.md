# DDD at Industry Level — E-Commerce Order System

> From scratch. Answers: why Entities, why not just a service, and how real production apps are structured.

---

## Table of Contents

1. [The Fundamental Question: Why Entities at All?](#1-the-fundamental-question-why-entities-at-all)
2. [The Anemic vs Rich Model Trap](#2-the-anemic-vs-rich-model-trap)
3. [Industry Folder Structure](#3-industry-folder-structure)
4. [The Four Layers Explained](#4-the-four-layers-explained)
5. [Domain Layer — Full Implementation](#5-domain-layer--full-implementation)
6. [Application Layer — Use Cases](#6-application-layer--use-cases)
7. [Infrastructure Layer — Database + API](#7-infrastructure-layer--database--api)
8. [Wiring Everything with Dependency Injection](#8-wiring-everything-with-dependency-injection)
9. [Request Flow — Trace One HTTP Call End to End](#9-request-flow--trace-one-http-call-end-to-end)
10. [What Each Layer Is Allowed to Know](#10-what-each-layer-is-allowed-to-know)

---

## 1. The Fundamental Question: Why Entities at All?

You asked: *"Why not just have an `OrderService` that manages a list of orders?"*

Let's actually build that and watch it collapse.

### The "just use a service" approach

```python
# services/order_service.py  — the "simple" way
class OrderService:
    def __init__(self, db):
        self.db = db

    def create_order(self, customer_id, items, payment_method):
        # validation scattered here
        if not items:
            raise ValueError("Need items")
        total = sum(i["price"] * i["qty"] for i in items)
        if total > 50_000:
            raise ValueError("Too large")
        order_id = self.db.insert("orders", {...})
        return order_id

    def add_item(self, order_id, item):
        order = self.db.get("orders", order_id)
        # rule copied again here
        total = order["total"] + item["price"] * item["qty"]
        if total > 50_000:
            raise ValueError("Too large")
        self.db.update(...)

    def cancel_order(self, order_id):
        order = self.db.get("orders", order_id)
        # Where does the "can cancel only within 24h" rule live?
        # In this service? In a controller? In both?
        if order["status"] != "PENDING":
            raise ValueError("Can only cancel PENDING orders")
        self.db.update("orders", order_id, {"status": "CANCELLED"})

    def ship_order(self, order_id, tracking_number):
        order = self.db.get("orders", order_id)
        if order["status"] != "CONFIRMED":
            raise ValueError("Can only ship CONFIRMED orders")
        self.db.update(...)

    def confirm_order(self, order_id):
        order = self.db.get("orders", order_id)
        if order["status"] != "PENDING":
            raise ValueError("Can only confirm PENDING orders")
        self.db.update(...)
```

This looks fine at first. The problems appear when the system grows.

### What happens when this scales

```
6 months later:

services/
  order_service.py          ← 800 lines, every status transition in here
  order_admin_service.py    ← duplicate of half the rules for admin users
  order_refund_service.py   ← "can refund only if DELIVERED, and within 30 days"
                               — copied from order_service.py, slightly different

api/
  orders.py                 ← some validation duplicated here "just to be safe"
  admin_orders.py           ← different validation because "admins are different"

workers/
  auto_cancel_worker.py     ← cancels abandoned orders, copies the status check again
```

Now the "only cancel PENDING orders" rule exists in 4 places. Someone changes it in two of them. Production incident.

**This is called the Anemic Domain Model anti-pattern.**

---

## 2. The Anemic vs Rich Model Trap

### Anemic model — data bags + fat services

```
Order = { id, status, total, items, customer_id }  ← just data, no behaviour

OrderService {
    create_order()     ← ALL rules live here
    cancel_order()     ← rules duplicated
    confirm_order()    ← rules duplicated
    ship_order()       ← rules duplicated
    refund_order()     ← rules duplicated
}
```

The `Order` object has **no behaviour**. It's a struct. All logic lives in one or more fat services.

### Rich model — behaviour lives with the data that owns it

```
Order {
    id, status, lines, customer_id     ← data
    place()                            ← rule: must have lines, total ≤ 50000
    confirm()                          ← rule: must be PENDING
    cancel()                           ← rule: must be PENDING
    ship(tracking_number)              ← rule: must be CONFIRMED
    add_line(product, qty, price)      ← rule: only if PENDING, total check
}

OrderService {
    place_order()    ← orchestrates: load customer, call order.place(), save, emit event
    cancel_order()   ← orchestrates: load order, call order.cancel(), save, emit event
}
```

The `Order` entity enforces its own rules. The service **coordinates**, not **decides**.

**The key insight:**
> An Entity is responsible for rules that belong to **one** thing — its own lifecycle, its own state transitions, its own invariants. A service is responsible for **coordination** — when you need multiple things together.

---

## 3. Industry Folder Structure

Real production apps separate code into four layers. Here is the structure we'll build for an e-commerce system:

```
ecommerce/
│
├── domain/                              ← LAYER 1: Pure business logic
│   │                                      No frameworks. No DB. No HTTP.
│   │                                      This is what DDD actually is.
│   │
│   ├── order/                           ← Order bounded context
│   │   ├── __init__.py
│   │   ├── order.py                     ← Order aggregate root
│   │   ├── order_line.py                ← OrderLine entity
│   │   ├── value_objects.py             ← Money, OrderStatus, Address
│   │   ├── events.py                    ← OrderPlaced, OrderCancelled (domain events)
│   │   └── repository.py               ← IOrderRepository (Protocol — no impl here)
│   │
│   ├── customer/                        ← Customer bounded context
│   │   ├── __init__.py
│   │   ├── customer.py                  ← Customer aggregate
│   │   ├── value_objects.py             ← Email, Address
│   │   └── repository.py               ← ICustomerRepository
│   │
│   └── product/                         ← Product bounded context
│       ├── __init__.py
│       ├── product.py                   ← Product aggregate
│       └── repository.py               ← IProductRepository
│
├── application/                         ← LAYER 2: Use cases (one file per use case)
│   │                                      Orchestrates domain objects.
│   │                                      Calls repositories, emits events.
│   │
│   ├── order/
│   │   ├── place_order.py               ← PlaceOrderCommand + PlaceOrderHandler
│   │   ├── cancel_order.py              ← CancelOrderCommand + CancelOrderHandler
│   │   └── get_order.py                 ← GetOrderQuery + GetOrderHandler
│   │
│   └── customer/
│       ├── register_customer.py
│       └── update_address.py
│
├── infrastructure/                      ← LAYER 3: Adapters to the outside world
│   │                                      DB, HTTP, messaging, email, S3, etc.
│   │
│   ├── persistence/                     ← Concrete repository implementations
│   │   ├── sqlalchemy_order_repo.py     ← implements IOrderRepository with SQLAlchemy
│   │   └── sqlalchemy_customer_repo.py
│   │
│   ├── messaging/
│   │   └── kafka_event_publisher.py     ← publishes domain events to Kafka
│   │
│   └── api/                             ← FastAPI routes
│       ├── orders.py                    ← POST /orders, DELETE /orders/{id}
│       ├── customers.py
│       └── schemas.py                   ← request/response Pydantic models (NOT domain models)
│
└── main.py                              ← LAYER 4: Wiring / Dependency Injection
                                           Creates concrete impls, injects into handlers
```

---

## 4. The Four Layers Explained

```
┌─────────────────────────────────────────────────────────────┐
│  API / CLI / Worker  (infrastructure/api/)                  │
│  FastAPI routes, Celery tasks, CLI commands                 │
│  Knows about: HTTP schemas, application commands            │
└───────────────────────────┬─────────────────────────────────┘
                            │ calls with Command/Query objects
┌───────────────────────────▼─────────────────────────────────┐
│  Application Layer  (application/)                          │
│  One class per use case. Coordinates, does NOT decide.      │
│  Knows about: domain aggregates, repository Protocols       │
└───────────────────────────┬─────────────────────────────────┘
                            │ calls methods on aggregates
┌───────────────────────────▼─────────────────────────────────┐
│  Domain Layer  (domain/)                                    │
│  Entities, Aggregates, Value Objects, Domain Events         │
│  Knows about: NOTHING outside this folder                   │
│  Zero imports from application/, infrastructure/, main.py   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ implements Protocols defined in domain/
┌───────────────────────────┴─────────────────────────────────┐
│  Infrastructure Layer  (infrastructure/)                    │
│  SQLAlchemy, Redis, Kafka, FastAPI, S3, SMTP                │
│  Knows about: domain (to implement its interfaces)          │
└─────────────────────────────────────────────────────────────┘
```

The arrow of allowed imports goes **inward only**. Infrastructure can import domain. Domain cannot import infrastructure.

---

## 5. Domain Layer — Full Implementation

### 5.1 Value Objects — `domain/order/value_objects.py`

```python
# domain/order/value_objects.py
from __future__ import annotations
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, field_validator


class Money(BaseModel):
    """Monetary amount with currency.

    Immutable — arithmetic produces a new Money instance.
    Two Money objects are equal only if both amount and currency match.
    """
    amount: Decimal
    currency: str  # ISO 4217, e.g. "USD", "EUR"

    model_config = {"frozen": True}

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Money amount cannot be negative")
        return v

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount < other.amount

    @classmethod
    def zero(cls, currency: str) -> Money:
        return cls(amount=Decimal("0"), currency=currency)


class OrderStatus(str, Enum):
    """All legal states an Order can be in.

    State machine:
        PENDING → CONFIRMED → SHIPPED → DELIVERED
             ↓
         CANCELLED   (only from PENDING)
    """
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
```

### 5.2 OrderLine Entity — `domain/order/order_line.py`

```python
# domain/order/order_line.py
import uuid
from pydantic import BaseModel, Field
from domain.order.value_objects import Money


class OrderLine(BaseModel):
    """A single line item within an order.

    An OrderLine is an Entity — it has its own ID and can be
    individually referenced (e.g. for returns on specific lines).
    It exists only within the Order aggregate boundary.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    product_id: uuid.UUID
    product_name: str          # denormalised — snapshot at time of order
    quantity: int
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return Money(
            amount=self.unit_price.amount * self.quantity,
            currency=self.unit_price.currency,
        )
```

**Why is `OrderLine` an Entity and not a Value Object?**  
Because it has its own identity — you can cancel one line, or return one line, independently of the others. Two lines with the same product and quantity are still *different* lines (different IDs, different order timestamps).

### 5.3 Domain Events — `domain/order/events.py`

```python
# domain/order/events.py
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Events are facts — immutable records of something that happened.
    They are named in the past tense.
    """
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: uuid.UUID
    customer_id: uuid.UUID
    total: str          # serialised Money as "100.00 USD"


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: uuid.UUID
    customer_id: uuid.UUID
    reason: str


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    order_id: uuid.UUID
    tracking_number: str
```

### 5.4 Order Aggregate — `domain/order/order.py`

This is the core. Every state-transition rule lives here.

```python
# domain/order/order.py
from __future__ import annotations
import uuid
from pydantic import BaseModel, Field
from domain.order.order_line import OrderLine
from domain.order.value_objects import Money, OrderStatus
from domain.order.events import DomainEvent, OrderPlaced, OrderCancelled, OrderShipped

ORDER_MAX_TOTAL = Money(amount=50_000, currency="USD")


class Order(BaseModel):
    """Order aggregate root.

    Lifecycle:  PENDING → CONFIRMED → SHIPPED → DELIVERED
                       ↘ CANCELLED

    All state transitions go through this class's methods.
    The aggregate accumulates domain events that the application
    layer will publish after a successful save.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID
    status: OrderStatus = OrderStatus.PENDING
    lines: list[OrderLine] = Field(default_factory=list)
    currency: str = "USD"

    # Events collected during this session — NOT persisted in DB
    _events: list[DomainEvent] = []

    model_config = {"arbitrary_types_allowed": True}

    # ------------------------------------------------------------------ #
    # Factory — named constructor for the "place" use case               #
    # ------------------------------------------------------------------ #

    @classmethod
    def place(cls, customer_id: uuid.UUID, currency: str = "USD") -> Order:
        """Create a new order in PENDING state.

        An order with no lines is valid on creation — lines are added
        before confirmation.
        """
        order = cls(customer_id=customer_id, currency=currency)
        return order

    # ------------------------------------------------------------------ #
    # Commands — state-changing methods                                   #
    # ------------------------------------------------------------------ #

    def add_line(self, product_id: uuid.UUID, product_name: str,
                 quantity: int, unit_price: Money) -> OrderLine:
        """Add a product to this order.

        Rules:
          - Order must be PENDING (cannot modify a confirmed order).
          - Total must not exceed ORDER_MAX_TOTAL.
          - Quantity must be positive.
        """
        self._assert_status(OrderStatus.PENDING, action="add lines to")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if unit_price.currency != self.currency:
            raise ValueError(
                f"Order currency is {self.currency}, "
                f"cannot add line priced in {unit_price.currency}"
            )

        new_line = OrderLine(
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
        )
        projected_total = self.total + new_line.subtotal
        if ORDER_MAX_TOTAL < projected_total:
            raise ValueError(
                f"Adding this line would push total to {projected_total.amount} "
                f"{projected_total.currency}, exceeding the "
                f"{ORDER_MAX_TOTAL.amount} limit."
            )
        self.lines.append(new_line)
        return new_line

    def confirm(self) -> None:
        """Confirm the order — moves PENDING → CONFIRMED.

        Rule: must have at least one line before confirming.
        """
        self._assert_status(OrderStatus.PENDING, action="confirm")
        if not self.lines:
            raise ValueError("Cannot confirm an order with no lines")
        self.status = OrderStatus.CONFIRMED
        self._record(OrderPlaced(
            order_id=self.id,
            customer_id=self.customer_id,
            total=f"{self.total.amount} {self.total.currency}",
        ))

    def cancel(self, reason: str) -> None:
        """Cancel the order — only valid from PENDING state.

        Once confirmed, an order follows the return/refund process instead.
        """
        self._assert_status(OrderStatus.PENDING, action="cancel")
        self.status = OrderStatus.CANCELLED
        self._record(OrderCancelled(
            order_id=self.id,
            customer_id=self.customer_id,
            reason=reason,
        ))

    def ship(self, tracking_number: str) -> None:
        """Mark the order as shipped — moves CONFIRMED → SHIPPED."""
        self._assert_status(OrderStatus.CONFIRMED, action="ship")
        if not tracking_number:
            raise ValueError("Tracking number required to ship")
        self.status = OrderStatus.SHIPPED
        self._record(OrderShipped(order_id=self.id, tracking_number=tracking_number))

    def deliver(self) -> None:
        """Mark the order as delivered — moves SHIPPED → DELIVERED."""
        self._assert_status(OrderStatus.SHIPPED, action="deliver")
        self.status = OrderStatus.DELIVERED

    # ------------------------------------------------------------------ #
    # Queries — read-only computed properties                             #
    # ------------------------------------------------------------------ #

    @property
    def total(self) -> Money:
        if not self.lines:
            return Money.zero(self.currency)
        result = Money.zero(self.currency)
        for line in self.lines:
            result = result + line.subtotal
        return result

    def pop_events(self) -> list[DomainEvent]:
        """Return and clear accumulated domain events."""
        events, self._events = self._events, []
        return events

    # ------------------------------------------------------------------ #
    # Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _assert_status(self, expected: OrderStatus, action: str) -> None:
        if self.status != expected:
            raise ValueError(
                f"Cannot {action} an order in status {self.status.value}. "
                f"Expected {expected.value}."
            )

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)
```

### 5.5 Repository Protocol — `domain/order/repository.py`

```python
# domain/order/repository.py
import uuid
from typing import Protocol
from domain.order.order import Order


class IOrderRepository(Protocol):
    """What any Order repository must provide.

    Lives in the domain layer — the domain defines the contract.
    The infrastructure layer fulfils it.
    """

    def get(self, order_id: uuid.UUID) -> Order:
        """Load an Order by ID. Raises KeyError if not found."""
        ...

    def save(self, order: Order) -> None:
        """Persist the Order (create or update)."""
        ...

    def find_by_customer(self, customer_id: uuid.UUID) -> list[Order]:
        """All orders for a given customer."""
        ...
```

---

## 6. Application Layer — Use Cases

The application layer has **one class per use case**. It:
- Receives a plain Command or Query object (no HTTP concern)
- Loads aggregates via repositories
- Calls methods on aggregates (which enforce rules)
- Saves the result
- Publishes domain events

**It makes decisions about coordination, never about domain rules.**

### 6.1 Place Order Use Case — `application/order/place_order.py`

```python
# application/order/place_order.py
import uuid
from dataclasses import dataclass
from decimal import Decimal

from domain.order.order import Order
from domain.order.order_line import OrderLine
from domain.order.repository import IOrderRepository
from domain.order.value_objects import Money
from domain.customer.repository import ICustomerRepository


@dataclass
class PlaceOrderLineInput:
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    currency: str


@dataclass
class PlaceOrderCommand:
    """Input to the PlaceOrder use case.

    Plain dataclass — no HTTP, no Pydantic, no framework.
    """
    customer_id: uuid.UUID
    lines: list[PlaceOrderLineInput]
    currency: str = "USD"


@dataclass
class PlaceOrderResult:
    order_id: uuid.UUID
    total_amount: Decimal
    currency: str
    status: str


class PlaceOrderHandler:
    """Use case: a customer places a new order.

    Orchestrates:
      1. Verify customer exists.
      2. Create Order aggregate via factory.
      3. Add all lines through aggregate methods (rules enforced inside).
      4. Confirm the order.
      5. Persist.
      6. Return result.
    """

    def __init__(
        self,
        order_repo: IOrderRepository,
        customer_repo: ICustomerRepository,
    ) -> None:
        self._order_repo = order_repo
        self._customer_repo = customer_repo

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        # Step 1: verify the customer exists
        customer = self._customer_repo.get(command.customer_id)
        if customer is None:
            raise ValueError(f"Customer {command.customer_id} not found")

        # Step 2: create the aggregate — starts in PENDING
        order = Order.place(
            customer_id=command.customer_id,
            currency=command.currency,
        )

        # Step 3: add lines — Order enforces all invariants internally
        for line_input in command.lines:
            order.add_line(
                product_id=line_input.product_id,
                product_name=line_input.product_name,
                quantity=line_input.quantity,
                unit_price=Money(
                    amount=line_input.unit_price,
                    currency=line_input.currency,
                ),
            )

        # Step 4: confirm — Order checks "at least one line" rule
        order.confirm()

        # Step 5: persist
        self._order_repo.save(order)

        # Step 6: domain events collected by the aggregate — publish them
        # (event bus injection omitted here for brevity)
        events = order.pop_events()
        # event_bus.publish_all(events)

        return PlaceOrderResult(
            order_id=order.id,
            total_amount=order.total.amount,
            currency=order.total.currency,
            status=order.status.value,
        )
```

### 6.2 Cancel Order Use Case — `application/order/cancel_order.py`

```python
# application/order/cancel_order.py
import uuid
from dataclasses import dataclass
from domain.order.repository import IOrderRepository


@dataclass
class CancelOrderCommand:
    order_id: uuid.UUID
    customer_id: uuid.UUID     # for ownership check
    reason: str


class CancelOrderHandler:
    """Use case: a customer cancels their pending order."""

    def __init__(self, order_repo: IOrderRepository) -> None:
        self._order_repo = order_repo

    def handle(self, command: CancelOrderCommand) -> None:
        order = self._order_repo.get(command.order_id)

        # Ownership check — application-layer concern
        if order.customer_id != command.customer_id:
            raise PermissionError("You can only cancel your own orders")

        # Domain rule ("must be PENDING") enforced inside the aggregate
        order.cancel(reason=command.reason)

        self._order_repo.save(order)
        # publish order.pop_events()
```

---

## 7. Infrastructure Layer — Database + API

### 7.1 SQLAlchemy Repository — `infrastructure/persistence/sqlalchemy_order_repo.py`

```python
# infrastructure/persistence/sqlalchemy_order_repo.py
import uuid
from sqlalchemy.orm import Session
from domain.order.order import Order
from domain.order.repository import IOrderRepository
from infrastructure.persistence.models import OrderModel, OrderLineModel


class SQLAlchemyOrderRepository:
    """Concrete IOrderRepository backed by PostgreSQL via SQLAlchemy.

    Maps between the domain's Order aggregate and the ORM models.
    The domain layer has zero knowledge this file exists.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, order_id: uuid.UUID) -> Order:
        model = (
            self._session.query(OrderModel)
            .filter(OrderModel.id == str(order_id))
            .first()
        )
        if model is None:
            raise KeyError(f"Order {order_id} not found")
        return self._to_domain(model)

    def save(self, order: Order) -> None:
        existing = (
            self._session.query(OrderModel)
            .filter(OrderModel.id == str(order.id))
            .first()
        )
        if existing is None:
            self._session.add(self._to_model(order))
        else:
            self._update_model(existing, order)
        self._session.flush()

    def find_by_customer(self, customer_id: uuid.UUID) -> list[Order]:
        models = (
            self._session.query(OrderModel)
            .filter(OrderModel.customer_id == str(customer_id))
            .all()
        )
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: OrderModel) -> Order:
        # reconstruct the aggregate from ORM data
        ...

    def _to_model(self, order: Order) -> OrderModel:
        # convert aggregate to ORM model for insert
        ...

    def _update_model(self, model: OrderModel, order: Order) -> None:
        # sync ORM model fields from aggregate
        ...
```

### 7.2 API Schemas — `infrastructure/api/schemas.py`

These are **not** domain objects. They are HTTP contract models — what the outside world sees.

```python
# infrastructure/api/schemas.py
import uuid
from decimal import Decimal
from pydantic import BaseModel


class OrderLineRequest(BaseModel):
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    currency: str = "USD"


class PlaceOrderRequest(BaseModel):
    customer_id: uuid.UUID
    lines: list[OrderLineRequest]
    currency: str = "USD"


class PlaceOrderResponse(BaseModel):
    order_id: uuid.UUID
    total_amount: Decimal
    currency: str
    status: str


class CancelOrderRequest(BaseModel):
    reason: str
```

### 7.3 FastAPI Routes — `infrastructure/api/orders.py`

The route does **one job**: translate HTTP → Command, call the handler, translate result → HTTP.

```python
# infrastructure/api/orders.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from application.order.place_order import PlaceOrderCommand, PlaceOrderLineInput, PlaceOrderHandler
from application.order.cancel_order import CancelOrderCommand, CancelOrderHandler
from infrastructure.api.schemas import PlaceOrderRequest, PlaceOrderResponse, CancelOrderRequest
from infrastructure.api.dependencies import get_place_order_handler, get_cancel_order_handler

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=PlaceOrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    body: PlaceOrderRequest,
    handler: PlaceOrderHandler = Depends(get_place_order_handler),
):
    """Place a new order for a customer."""
    command = PlaceOrderCommand(
        customer_id=body.customer_id,
        currency=body.currency,
        lines=[
            PlaceOrderLineInput(
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_price=line.unit_price,
                currency=line.currency,
            )
            for line in body.lines
        ],
    )
    try:
        result = handler.handle(command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return PlaceOrderResponse(
        order_id=result.order_id,
        total_amount=result.total_amount,
        currency=result.currency,
        status=result.status,
    )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(
    order_id: uuid.UUID,
    body: CancelOrderRequest,
    customer_id: uuid.UUID,           # in real app: from JWT token
    handler: CancelOrderHandler = Depends(get_cancel_order_handler),
):
    """Cancel a pending order."""
    command = CancelOrderCommand(
        order_id=order_id,
        customer_id=customer_id,
        reason=body.reason,
    )
    try:
        handler.handle(command)
    except KeyError:
        raise HTTPException(status_code=404, detail="Order not found")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
```

---

## 8. Wiring Everything with Dependency Injection

`main.py` is the **composition root** — the single place where concrete classes are chosen and injected. Nothing else in the app names a concrete class.

```python
# main.py
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.api.orders import router as orders_router
from infrastructure.persistence.sqlalchemy_order_repo import SQLAlchemyOrderRepository
from infrastructure.persistence.sqlalchemy_customer_repo import SQLAlchemyCustomerRepository
from application.order.place_order import PlaceOrderHandler
from application.order.cancel_order import CancelOrderHandler

DATABASE_URL = "postgresql://user:pass@localhost/ecommerce"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="E-Commerce API")
app.include_router(orders_router)


# FastAPI dependency providers — called per-request
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_place_order_handler(session=Depends(get_db_session)) -> PlaceOrderHandler:
    return PlaceOrderHandler(
        order_repo=SQLAlchemyOrderRepository(session),
        customer_repo=SQLAlchemyCustomerRepository(session),
    )


def get_cancel_order_handler(session=Depends(get_db_session)) -> CancelOrderHandler:
    return CancelOrderHandler(
        order_repo=SQLAlchemyOrderRepository(session),
    )
```

---

## 9. Request Flow — Trace One HTTP Call End to End

**Scenario:** `POST /orders` — a customer places an order with 2 items.

```
1. HTTP Request arrives
   POST /orders  { customer_id, lines: [...] }

2. infrastructure/api/orders.py  — place_order()
   • Validates request body with Pydantic (PlaceOrderRequest)
   • Builds PlaceOrderCommand (no HTTP concern in command)
   • Calls handler.handle(command)

3. application/order/place_order.py  — PlaceOrderHandler.handle()
   • Calls customer_repo.get(customer_id)  → verifies customer exists
   • Calls Order.place(customer_id)        → creates aggregate in PENDING
   • For each line:
       order.add_line(...)                 → Order checks qty > 0, total ≤ 50000
   • order.confirm()                       → Order checks has lines, sets CONFIRMED
                                             records OrderPlaced event
   • order_repo.save(order)               → hands off to infrastructure

4. infrastructure/persistence/sqlalchemy_order_repo.py  — save()
   • Translates Order aggregate → ORM models
   • session.add() / session.flush()
   • session.commit() (happens in get_db_session dependency)

5. Back in handler:
   • order.pop_events()                   → get [OrderPlaced(...)]
   • event_bus.publish(OrderPlaced)       → Kafka / SNS / in-process bus

6. PlaceOrderResult returned up the stack
7. infrastructure/api/orders.py wraps it in PlaceOrderResponse
8. HTTP 201 response
```

**Where each rule fired:**

| Rule | Where it fired |
|---|---|
| Customer must exist | `PlaceOrderHandler` (application) |
| Quantity must be positive | `Order.add_line()` (domain) |
| Total ≤ 50 000 | `Order.add_line()` (domain) |
| Must have lines before confirm | `Order.confirm()` (domain) |
| Order must be PENDING to confirm | `Order._assert_status()` (domain) |
| Customer can only cancel own orders | `CancelOrderHandler` (application) |

---

## 10. What Each Layer Is Allowed to Know

```
Layer              Can import from          Cannot import from
─────────────────────────────────────────────────────────────────────
domain/            nothing outside domain   application, infrastructure, main
application/       domain                   infrastructure, main
infrastructure/    domain, application      main
main.py            everything               —
```

### Testing benefit

Because the domain layer imports nothing external:

```python
# tests/domain/test_order.py
# No database. No HTTP. No fixtures. Just the aggregate.

def test_cannot_confirm_empty_order():
    order = Order.place(customer_id=uuid.uuid4())
    with pytest.raises(ValueError, match="no lines"):
        order.confirm()

def test_cannot_exceed_max_total():
    order = Order.place(customer_id=uuid.uuid4())
    order.add_line(product_id=..., product_name="A",
                   quantity=1, unit_price=Money(amount=49_000, currency="USD"))
    with pytest.raises(ValueError, match="exceeding the"):
        order.add_line(product_id=..., product_name="B",
                       quantity=1, unit_price=Money(amount=2_000, currency="USD"))

def test_cancel_sets_status_cancelled():
    order = Order.place(customer_id=uuid.uuid4())
    order.cancel(reason="changed my mind")
    assert order.status == OrderStatus.CANCELLED

def test_cannot_cancel_confirmed_order():
    order = Order.place(customer_id=uuid.uuid4())
    order.add_line(...)
    order.confirm()
    with pytest.raises(ValueError, match="Expected PENDING"):
        order.cancel(reason="too late")
```

These tests run in microseconds. No mocking needed. The domain is 100% self-contained.

---

## 11. Where Exactly Is the Orchestrator?

This is the most common point of confusion. Let's pin it down precisely.

### The orchestrator is the Application Service — one file per use case

```
ecommerce/
├── domain/              ← DECIDES rules  (Entity, Aggregate)
├── application/         ← ORCHESTRATES   ← THE ORCHESTRATOR LIVES HERE
│   └── order/
│       └── place_order.py   ← PlaceOrderHandler  ← THIS IS THE ORCHESTRATOR
├── infrastructure/      ← EXECUTES I/O   (DB, HTTP)
└── main.py              ← WIRES everything
```

### What "orchestrate" actually means line by line

Look at `PlaceOrderHandler.handle()`. Every line does exactly one of these things — nothing more:

```python
def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:

    # ── STEP 1: Load data from storage (via repository) ──────────────
    customer = self._customer_repo.get(command.customer_id)
    #          ↑ orchestrator asks infrastructure to fetch something

    # ── STEP 2: Make a coordination decision using that data ──────────
    if customer is None:
        raise ValueError("Customer not found")
    #  ↑ orchestrator decides: should we even continue?
    #    NOT a domain rule — just "does this thing exist?"

    if customer.status == CustomerStatus.SUSPENDED:
        raise ValueError("Suspended customers cannot place orders")
    #  ↑ orchestrator reads entity state and decides to abort
    #    (or better: customer.assert_can_place_orders() — see below)

    # ── STEP 3: Call a domain factory to create an aggregate ─────────
    order = Order.place(customer_id=customer.id, currency=command.currency)
    #             ↑ orchestrator asks the domain to create something

    # ── STEP 4: Call domain methods — rules fire INSIDE the domain ───
    for line in command.lines:
        order.add_line(...)
    #   ↑ orchestrator calls the aggregate's method
    #     the "max total" rule fires INSIDE Order.add_line()
    #     the orchestrator doesn't know or care what that rule is

    order.confirm()
    #    ↑ orchestrator calls the aggregate's method
    #      the "must have lines" rule fires INSIDE Order.confirm()

    # ── STEP 5: Persist — hand off to infrastructure ─────────────────
    self._order_repo.save(order)
    #                ↑ orchestrator asks infrastructure to store it

    # ── STEP 6: Return a result ───────────────────────────────────────
    return PlaceOrderResult(order_id=order.id, ...)
```

The orchestrator **never knows a single business rule**. It just sequences:  
`load → check exists → call domain → save → return`.

### What the orchestrator does NOT do

```python
# WRONG — orchestrator enforcing a domain rule itself
def handle(self, command):
    order = Order.place(...)
    for line in command.lines:
        order.add_line(...)
    if order.total.amount > 50_000:       # ← THIS BELONGS INSIDE Order.add_line()
        raise ValueError("Too large")     #   not here in the application service
    order.confirm()
    ...

# WRONG — orchestrator mutating aggregate internals directly
def handle(self, command):
    order = self._order_repo.get(command.order_id)
    order.status = "CONFIRMED"            # ← NEVER. Call order.confirm() instead.
    self._order_repo.save(order)

# WRONG — orchestrator copying the same rule in two places
def place_order(self, command):
    if order.total > 50_000: raise ...   # copied rule
    ...

def add_express_order(self, command):
    if order.total > 50_000: raise ...   # same rule copied again — now two sources of truth
    ...
```

### Real shape of the orchestrator

```
PlaceOrderHandler
│
├── knows about:
│   ├── IOrderRepository     (Protocol — not the DB class)
│   ├── ICustomerRepository  (Protocol — not the DB class)
│   ├── Order                (to call its methods)
│   └── Customer             (to read its state)
│
├── does NOT know about:
│   ├── SQLAlchemy / Postgres
│   ├── FastAPI / HTTP
│   ├── Kafka / events bus
│   ├── "total must be ≤ 50000" (that's Order's job)
│   └── "must have lines before confirm" (that's Order's job)
│
└── its only job:
    sequence the steps, then get out of the way
```

### Comparison: where does each responsibility live?

```
Scenario: customer places an order for 3 items worth $60,000 total

HTTP layer (infrastructure/api/orders.py)
  → parses JSON body
  → calls PlaceOrderHandler.handle(command)

PlaceOrderHandler (application/order/place_order.py)   ← ORCHESTRATOR
  → loads Customer from DB
  → checks customer exists             (coordination decision)
  → checks customer.status is ACTIVE   (reads entity state)
  → creates Order.place(...)
  → calls order.add_line(item1)        (delegates to domain)
  → calls order.add_line(item2)        (delegates to domain)
  → calls order.add_line(item3)
       ↓
       Order.add_line() (domain/order/order.py)        ← DOMAIN RULE FIRES HERE
         checks: projected total $60,000 > $50,000 limit
         raises: ValueError("exceeding the 50000 limit")
       ↑
  → ValueError bubbles back up to PlaceOrderHandler
  → PlaceOrderHandler does NOT catch it — lets it propagate

HTTP layer catches ValueError → returns HTTP 400
```

---

## 12. Customer: Entity or Aggregate — and Can place_order Use Customer Data?

### Question 1: Why is Customer an Aggregate and not just an Entity?

Short answer: **it depends on what Customer owns.**

An Entity has an ID and data that changes over time. That's it.  
An Aggregate is an Entity that **also owns child objects** and enforces rules across all of them together.

So ask: does `Customer` in your system own child objects that need consistency rules?

---

**Case A — Customer owns nothing complex → it's just an Entity**

```python
# Customer has scalar fields only.
# There are no child objects to enforce rules across.
# This is perfectly fine as just an Entity.

class Customer(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str
    status: CustomerStatus   # ACTIVE, SUSPENDED, BANNED
    tier: str                # "STANDARD", "PREMIUM", "VIP"

    def suspend(self, reason: str) -> None:
        if self.status == CustomerStatus.BANNED:
            raise ValueError("Cannot suspend a banned customer")
        self.status = CustomerStatus.SUSPENDED

    def reactivate(self) -> None:
        if self.status == CustomerStatus.BANNED:
            raise ValueError("Banned customers cannot be reactivated")
        self.status = CustomerStatus.ACTIVE
```

Here `Customer` has its own lifecycle rules (`suspend`, `reactivate`) but no child object cluster. It's an entity. You can still give it its own repository — that just means it's a "trivial aggregate" with no children.

---

**Case B — Customer owns child objects with cross-child rules → it becomes an Aggregate**

```python
# Customer now owns PaymentMethods.
# Rule: "a customer can have at most 3 active payment methods"
# Rule: "cannot remove the last payment method"
# These rules span the whole list — only the Customer can enforce them.

class Customer(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str
    status: CustomerStatus
    payment_methods: list[PaymentMethod] = Field(default_factory=list)

    def add_payment_method(self, method: PaymentMethod) -> None:
        active = [m for m in self.payment_methods if m.is_active]
        if len(active) >= 3:
            raise ValueError("Cannot have more than 3 active payment methods")
        self.payment_methods.append(method)

    def remove_payment_method(self, method_id: uuid.UUID) -> None:
        if len(self.payment_methods) <= 1:
            raise ValueError("Cannot remove the only payment method")
        method = next((m for m in self.payment_methods if m.id == method_id), None)
        if method is None:
            raise KeyError("Payment method not found")
        self.payment_methods.remove(method)
```

Now `Customer` is a genuine aggregate root — it guards rules across a collection of children.

---

**The deciding question:**

```
Does this class need to enforce rules across a list of child objects?
  YES → Aggregate (owns the list, exposes methods to modify it)
  NO  → Entity (just has an ID and its own lifecycle rules)
```

In our e-commerce system, `Customer` and `Order` are separate aggregates in separate bounded contexts. `Customer` does NOT own a list of orders. The `Order` aggregate owns itself. This is why `place_order` loads them independently.

---

### Question 2: Can `place_order` application service use Customer data?

**Yes — absolutely. That is exactly what the application service is for.**

The application service is the orchestrator. It is allowed to load any aggregate it needs, read data from it, and pass that data into another aggregate's methods.

Here is a concrete expanded `PlaceOrderHandler` that actually uses the Customer:

```python
# application/order/place_order.py  — realistic version

class PlaceOrderHandler:
    def __init__(self, order_repo: IOrderRepository,
                 customer_repo: ICustomerRepository) -> None:
        self._order_repo = order_repo
        self._customer_repo = customer_repo

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        # Load the Customer — read its data
        customer = self._customer_repo.get(command.customer_id)
        if customer is None:
            raise ValueError(f"Customer {command.customer_id} not found")

        # Use Customer data to make orchestration decisions
        if customer.status == CustomerStatus.SUSPENDED:
            raise ValueError("Suspended customers cannot place orders")

        if customer.status == CustomerStatus.BANNED:
            raise ValueError("Banned customers cannot place orders")

        # Use customer's preferred currency if none specified
        currency = command.currency or customer.preferred_currency

        # Apply tier-based order limit using customer data
        max_total = _get_max_total_for_tier(customer.tier)

        # Create the Order aggregate — pass in customer-derived values
        order = Order.place(
            customer_id=customer.id,
            currency=currency,
            max_total=max_total,           # Customer tier affects Order rule
        )

        # Add lines — Order enforces its own invariants
        for line in command.lines:
            order.add_line(
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_price=Money(amount=line.unit_price, currency=currency),
            )

        order.confirm()
        self._order_repo.save(order)
        # NOTE: Customer aggregate is never saved here —
        # we only READ from it, we did not change it

        return PlaceOrderResult(...)


def _get_max_total_for_tier(tier: str) -> Money:
    limits = {
        "STANDARD": Money(amount=Decimal("5000"), currency="USD"),
        "PREMIUM":  Money(amount=Decimal("25000"), currency="USD"),
        "VIP":      Money(amount=Decimal("100000"), currency="USD"),
    }
    return limits.get(tier, limits["STANDARD"])
```

---

### The exact rules for cross-aggregate usage in application services

```
Application service CAN:
  ✓ Load multiple aggregates from their repos
  ✓ Read data from any of them
  ✓ Pass data from one aggregate into another aggregate's method
  ✓ Decide whether to proceed based on aggregate state (e.g. customer.status)
  ✓ Save one or more aggregates after modification

Application service CANNOT:
  ✗ Enforce rules that belong inside an aggregate
       BAD:  if order.lines count > 10: raise ValueError(...)  ← put this in Order
  ✗ Directly mutate aggregate internals (order.lines.append, order.status = ...)
       BAD:  order.status = "CONFIRMED"     ← call order.confirm() instead
  ✗ Contain reusable domain logic
       BAD:  same "suspended check" copy-pasted in 5 handlers
       GOOD: customer.assert_can_place_orders() — rule lives in Customer entity
```

---

### Final mental model: who is responsible for what

```
Customer entity/aggregate
  → "Am I in a state where I can do X?"
  → "Is my own data valid?"
  → "Can I add/remove from my own child list?"

Order aggregate
  → "Are my lines valid?"
  → "Can I transition to this status?"
  → "Is my total within my limit?"

PlaceOrderHandler (application service)
  → "Does this customer exist?"
  → "Is this customer allowed to order right now?"   ← read from Customer
  → "What are the parameters for this order?"        ← derive from Customer
  → "Build the Order, save it, emit events"          ← coordinate everything
```

The application service is the **traffic controller**. It does not know the rules of the road — that is the domain's job. It just directs who goes when.

---

## Summary: Why Entity, Not Just a Service?

| | Fat Service approach | Entity + Application Service |
|---|---|---|
| Where do rules live? | Scattered in every service method | Inside the entity — one place |
| What happens when you add a new endpoint? | Must remember to copy every rule | Call `order.cancel()` — rules fire automatically |
| Can you accidentally bypass a rule? | Yes — add to the list directly | No — list is private, only methods are exposed |
| How many places to update when a rule changes? | All services that copied it | One method in the entity |
| Unit test speed | Needs DB + service setup | Instantiate the class, done |
| Domain complexity | Hidden in service code | Visible and named in the entity |
