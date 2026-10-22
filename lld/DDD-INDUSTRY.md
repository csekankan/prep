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

---

## 13. Domain Services

### The Problem: Business Logic That Doesn't Belong to Any Single Entity

Sometimes you have a business rule that requires **multiple aggregates** to compute, but it doesn't naturally belong inside either one.

**Example:** "Calculate the final price for a customer's order based on the customer's loyalty tier, the product's category discount, and any active promotions."

- `Order` shouldn't know about `Customer` tiers — that's not its responsibility.
- `Customer` shouldn't know about pricing rules — that's not its data.
- `Product` shouldn't know about customer tiers either.

This is where a **Domain Service** lives.

### What Is a Domain Service?

A Domain Service is:
- **Pure domain logic** (lives in `domain/`, not `application/`)
- **Stateless** — no instance data, no side effects
- **Coordinates rules across multiple aggregates** without owning any of them
- **Named after the business concept** it represents (not "Manager" or "Helper")

### What a Domain Service Is NOT

| Domain Service | Application Service |
|---|---|
| Lives in `domain/` | Lives in `application/` |
| Contains **business rules** | Contains **orchestration** (load, call, save) |
| No I/O (no DB, no HTTP) | Calls repositories, publishes events |
| Other domain objects can call it | Only the application layer calls it |

### Folder Structure

```
domain/
    pricing/
        __init__.py
        pricing_service.py         ← Domain Service
        discount_policy.py         ← Strategy used by pricing service
        value_objects.py           ← Discount, PriceBreakdown
```

### Full Implementation — `domain/pricing/pricing_service.py`

```python
# domain/pricing/pricing_service.py
from __future__ import annotations
from dataclasses import dataclass
from domain.pricing.value_objects import Discount, PriceBreakdown
from domain.order.value_objects import Money
from domain.customer.customer import Customer
from domain.product.product import Product


@dataclass(frozen=True)
class PricingService:
    """Calculates final price using cross-aggregate business rules.

    This is a Domain Service because:
    1. The pricing rule spans Customer, Product, and promotion data.
    2. Neither Customer nor Product should own this logic.
    3. It's pure computation — no I/O, no side effects.
    """

    def calculate_line_price(
        self,
        product: Product,
        customer: Customer,
        quantity: int,
    ) -> PriceBreakdown:
        """Apply tier discount + category discount + volume discount."""
        base_price = product.unit_price * quantity

        tier_discount = self._tier_discount(customer.tier)
        category_discount = self._category_discount(product.category)
        volume_discount = self._volume_discount(quantity)

        # Business rule: discounts stack multiplicatively, max total 30%
        combined = min(
            tier_discount.rate + category_discount.rate + volume_discount.rate,
            0.30,
        )

        final_discount = Discount(rate=combined, reason="combined")
        final_price = base_price.subtract(base_price.multiply(combined))

        return PriceBreakdown(
            base_price=base_price,
            final_price=final_price,
            discounts_applied=[tier_discount, category_discount, volume_discount],
            effective_discount=final_discount,
        )

    def _tier_discount(self, tier: str) -> Discount:
        rates = {"STANDARD": 0.0, "PREMIUM": 0.05, "VIP": 0.10}
        rate = rates.get(tier, 0.0)
        return Discount(rate=rate, reason=f"Tier: {tier}")

    def _category_discount(self, category: str) -> Discount:
        rates = {"ELECTRONICS": 0.02, "CLOTHING": 0.05, "FOOD": 0.0}
        rate = rates.get(category, 0.0)
        return Discount(rate=rate, reason=f"Category: {category}")

    def _volume_discount(self, quantity: int) -> Discount:
        if quantity >= 100:
            return Discount(rate=0.10, reason="Volume: 100+")
        elif quantity >= 50:
            return Discount(rate=0.05, reason="Volume: 50+")
        return Discount(rate=0.0, reason="Volume: none")
```

### Value Objects for Pricing — `domain/pricing/value_objects.py`

```python
# domain/pricing/value_objects.py
from __future__ import annotations
from dataclasses import dataclass
from domain.order.value_objects import Money


@dataclass(frozen=True)
class Discount:
    rate: float       # 0.0 to 1.0
    reason: str


@dataclass(frozen=True)
class PriceBreakdown:
    base_price: Money
    final_price: Money
    discounts_applied: list[Discount]
    effective_discount: Discount
```

### How the Application Service Uses It

```python
# application/order/place_order.py  (relevant excerpt)
from domain.pricing.pricing_service import PricingService

class PlaceOrderHandler:
    def __init__(
        self,
        order_repo: IOrderRepository,
        customer_repo: ICustomerRepository,
        product_repo: IProductRepository,
        pricing_service: PricingService,    # ← injected domain service
    ) -> None:
        self._order_repo = order_repo
        self._customer_repo = customer_repo
        self._product_repo = product_repo
        self._pricing = pricing_service

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        customer = self._customer_repo.get(command.customer_id)
        order = Order.place(customer_id=customer.id, currency=command.currency)

        for line in command.lines:
            product = self._product_repo.get(line.product_id)

            # Domain service calculates price — orchestrator just passes data through
            breakdown = self._pricing.calculate_line_price(
                product=product,
                customer=customer,
                quantity=line.quantity,
            )

            order.add_line(
                product_id=product.id,
                quantity=line.quantity,
                unit_price=breakdown.final_price,
            )

        order.confirm()
        self._order_repo.save(order)
        return PlaceOrderResult(order_id=order.id)
```

### When to Use a Domain Service vs an Entity Method

| Situation | Use |
|---|---|
| Rule uses data from **one** aggregate only | Entity/Aggregate method |
| Rule spans **multiple** aggregates | Domain Service |
| Rule is a policy that might vary (discounts, taxes, shipping) | Domain Service + Strategy |
| You're tempted to inject one aggregate into another | Domain Service instead |

### Key Rule: Domain Services Have Zero I/O

```python
# WRONG — domain service doing I/O
class PricingService:
    def __init__(self, db):
        self.db = db

    def calculate(self, order_id):
        order = self.db.get(order_id)    # ← NO. Domain services don't fetch.
        ...

# RIGHT — domain service receives already-loaded data
class PricingService:
    def calculate_line_price(self, product: Product, customer: Customer, quantity: int):
        ...  # pure computation only
```

The **application service** does the loading. The **domain service** does the computation.

---

## 14. Specifications — Reusable Business Predicates

### The Problem: Scattered Business Conditions

You keep writing the same boolean checks across multiple services:

```python
# scattered across the codebase
if order.status == OrderStatus.DELIVERED and order.total.amount > 100:
    ...  # eligible for loyalty points

if order.status == OrderStatus.DELIVERED and order.total.amount > 100:
    ...  # eligible for review request email

if order.total.amount > 500 and customer.tier == "VIP":
    ...  # eligible for VIP gift
```

The business rule "eligible for loyalty points" is a **named concept** that should exist as one thing, tested once, reused everywhere.

### What Is a Specification?

A Specification encapsulates a **business predicate** (a yes/no question) into a reusable, composable, testable object.

```
"Is this order eligible for a refund?"  →  RefundEligibleSpec
"Is this customer a high-value buyer?"  →  HighValueCustomerSpec
"Can this order be expedited?"          →  ExpediteEligibleSpec
```

### Folder Structure

```
domain/
    order/
        specifications.py          ← Order-related specs
    customer/
        specifications.py          ← Customer-related specs
    shared/
        specification.py           ← Base Specification protocol
```

### Base Specification — `domain/shared/specification.py`

```python
# domain/shared/specification.py
from __future__ import annotations
from typing import Protocol, TypeVar, Generic

T = TypeVar("T")


class Specification(Protocol[T]):
    """A business predicate — answers a yes/no question about a domain object."""

    def is_satisfied_by(self, candidate: T) -> bool:
        ...


class AndSpec(Generic[T]):
    """Composite: both specs must be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpec(Generic[T]):
    """Composite: at least one spec must be satisfied."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpec(Generic[T]):
    """Composite: spec must NOT be satisfied."""

    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
```

### Order Specifications — `domain/order/specifications.py`

```python
# domain/order/specifications.py
from domain.order.order import Order
from domain.order.value_objects import OrderStatus, Money
from datetime import datetime, timedelta


class RefundEligibleSpec:
    """An order is refund-eligible if delivered within 30 days and not already refunded."""

    def is_satisfied_by(self, order: Order) -> bool:
        if order.status != OrderStatus.DELIVERED:
            return False
        if order.refunded:
            return False
        days_since_delivery = (datetime.utcnow() - order.delivered_at).days
        return days_since_delivery <= 30


class HighValueOrderSpec:
    """An order is high-value if total exceeds $500."""

    def __init__(self, threshold: Money = Money(amount=500_00, currency="USD")) -> None:
        self._threshold = threshold

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total.amount >= self._threshold.amount


class LoyaltyPointsEligibleSpec:
    """An order qualifies for loyalty points if delivered and total > $100."""

    def is_satisfied_by(self, order: Order) -> bool:
        return (
            order.status == OrderStatus.DELIVERED
            and order.total.amount > 100_00
        )
```

### Composing Specifications

```python
# Combine specs with AND / OR / NOT
high_value = HighValueOrderSpec()
refundable = RefundEligibleSpec()

# "High-value AND refundable" — used for priority refund queue
priority_refund_spec = AndSpec(high_value, refundable)

# Check it
if priority_refund_spec.is_satisfied_by(order):
    ...  # route to priority refund team
```

### Using Specifications in Application Services

```python
# application/order/request_refund.py
from domain.order.specifications import RefundEligibleSpec

class RequestRefundHandler:
    def __init__(self, order_repo: IOrderRepository) -> None:
        self._order_repo = order_repo
        self._refund_spec = RefundEligibleSpec()

    def handle(self, command: RequestRefundCommand) -> None:
        order = self._order_repo.get(command.order_id)

        if not self._refund_spec.is_satisfied_by(order):
            raise ValueError("Order is not eligible for refund")

        order.initiate_refund(reason=command.reason)
        self._order_repo.save(order)
```

### Why Not Just a Method on the Entity?

| Approach | When to Use |
|---|---|
| Entity method (`order.can_refund()`) | Simple, single rule that only this entity uses |
| Specification object | Rule is **reused** across services, **composed** with other rules, or **configured** with parameters |

Specifications shine when you need to: filter collections, compose rules dynamically, pass predicates as arguments, or test complex conditions in isolation.

---

## 15. Anti-Corruption Layer (ACL)

### The Problem: External Systems Leak Into Your Domain

Your e-commerce system integrates with a payment gateway (Stripe), a shipping provider (FedEx), and a legacy inventory system. Each has its own data model, naming conventions, and quirks.

Without an ACL:

```python
# WRONG — domain depends directly on Stripe's model
from stripe import PaymentIntent

class Order:
    def mark_paid(self, stripe_intent: PaymentIntent):  # ← Stripe model in domain!
        self.status = OrderStatus.PAID
        self.payment_id = stripe_intent.id
        self.amount_paid = stripe_intent.amount_received / 100  # ← Stripe uses cents!
```

Now your domain is **coupled to Stripe**. If Stripe changes their API, your domain breaks. If you switch to PayPal, you rewrite your domain.

### What Is an Anti-Corruption Layer?

An ACL is a **translation boundary** that converts external models into your domain's language — and vice versa. It prevents foreign concepts from corrupting your clean domain model.

```
External World (Stripe, FedEx, Legacy DB)
       │
       ▼
┌──────────────────────────────┐
│  Anti-Corruption Layer       │  ← Translates foreign → domain language
│  (infrastructure/acl/)       │
└──────────────┬───────────────┘
               │  passes domain Value Objects
               ▼
┌──────────────────────────────┐
│  Application / Domain        │  ← Knows nothing about Stripe, FedEx, etc.
└──────────────────────────────┘
```

### Folder Structure

```
infrastructure/
    acl/
        __init__.py
        payment_gateway.py          ← Translates Stripe → domain PaymentConfirmation
        shipping_provider.py        ← Translates FedEx → domain ShipmentInfo
        legacy_inventory_adapter.py ← Translates legacy API → domain ProductStock
```

### Domain Defines Its Own Interface

```python
# domain/payment/gateway.py
from __future__ import annotations
from typing import Protocol
from domain.payment.value_objects import PaymentConfirmation, PaymentRequest


class IPaymentGateway(Protocol):
    """What the domain expects from any payment provider.
    Defined in domain terms — no Stripe, no PayPal, no external leakage.
    """

    def charge(self, request: PaymentRequest) -> PaymentConfirmation:
        ...

    def refund(self, payment_id: str, amount_cents: int) -> PaymentConfirmation:
        ...
```

### Domain Value Objects — `domain/payment/value_objects.py`

```python
# domain/payment/value_objects.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"


@dataclass(frozen=True)
class PaymentRequest:
    order_id: str
    amount_cents: int
    currency: str
    customer_email: str


@dataclass(frozen=True)
class PaymentConfirmation:
    """Domain's view of a completed payment — no Stripe-specific fields."""
    payment_id: str
    status: PaymentStatus
    amount_cents: int
    currency: str
    timestamp: str
```

### ACL Implementation — `infrastructure/acl/payment_gateway.py`

```python
# infrastructure/acl/payment_gateway.py
import stripe
from domain.payment.gateway import IPaymentGateway
from domain.payment.value_objects import (
    PaymentConfirmation,
    PaymentRequest,
    PaymentStatus,
)


class StripePaymentGateway:
    """ACL: Translates between Stripe's model and our domain's PaymentConfirmation.

    The domain never sees stripe.PaymentIntent, stripe.Charge, or any Stripe-specific
    concepts. This class is the ONLY place where 'import stripe' appears.
    """

    def __init__(self, api_key: str) -> None:
        stripe.api_key = api_key

    def charge(self, request: PaymentRequest) -> PaymentConfirmation:
        # Call Stripe's API — external model
        intent = stripe.PaymentIntent.create(
            amount=request.amount_cents,
            currency=request.currency,
            receipt_email=request.customer_email,
            metadata={"order_id": request.order_id},
        )

        # Translate Stripe's response → domain's value object
        return self._to_domain(intent)

    def refund(self, payment_id: str, amount_cents: int) -> PaymentConfirmation:
        refund = stripe.Refund.create(
            payment_intent=payment_id,
            amount=amount_cents,
        )
        return PaymentConfirmation(
            payment_id=refund.payment_intent,
            status=PaymentStatus.SUCCEEDED if refund.status == "succeeded" else PaymentStatus.FAILED,
            amount_cents=refund.amount,
            currency=refund.currency,
            timestamp=str(refund.created),
        )

    def _to_domain(self, intent: stripe.PaymentIntent) -> PaymentConfirmation:
        """The translation point: Stripe model → domain model."""
        status_map = {
            "succeeded": PaymentStatus.SUCCEEDED,
            "requires_payment_method": PaymentStatus.FAILED,
            "processing": PaymentStatus.PENDING,
        }
        return PaymentConfirmation(
            payment_id=intent.id,
            status=status_map.get(intent.status, PaymentStatus.FAILED),
            amount_cents=intent.amount_received,
            currency=intent.currency,
            timestamp=str(intent.created),
        )
```

### How the Application Uses the ACL

```python
# application/order/place_order.py (excerpt)
from domain.payment.gateway import IPaymentGateway  # ← Protocol, not Stripe

class PlaceOrderHandler:
    def __init__(
        self,
        order_repo: IOrderRepository,
        payment_gateway: IPaymentGateway,    # ← injected via DI
    ) -> None:
        self._order_repo = order_repo
        self._payment = payment_gateway

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        order = Order.place(...)
        # ...add lines, confirm...

        confirmation = self._payment.charge(
            PaymentRequest(
                order_id=str(order.id),
                amount_cents=order.total.amount,
                currency=order.total.currency,
                customer_email=command.customer_email,
            )
        )

        if confirmation.status == PaymentStatus.FAILED:
            raise ValueError("Payment failed")

        order.mark_paid(payment_id=confirmation.payment_id)
        self._order_repo.save(order)
        return PlaceOrderResult(order_id=order.id)
```

### Switching Providers Is Now Trivial

```python
# main.py — swap Stripe for PayPal by changing one line
# Before:
payment_gateway = StripePaymentGateway(api_key=settings.STRIPE_KEY)

# After:
payment_gateway = PayPalPaymentGateway(client_id=settings.PAYPAL_ID)

# The application and domain code changes: ZERO.
```

### When Do You Need an ACL?

| Scenario | Need ACL? |
|---|---|
| Calling a third-party API (Stripe, Twilio, FedEx) | Yes |
| Consuming a legacy system's database/API | Yes |
| Reading from another team's microservice | Often yes |
| Using a well-known library (datetime, uuid) | No — these are universal |
| Using your own infrastructure (own DB, own queue) | Usually a repository is enough |

---

## 16. Unit of Work Pattern

### The Problem: Saving Multiple Aggregates Atomically

Your `PlaceOrderHandler` saves an `Order` and updates a `Customer`'s last-order date. What if the order saves but the customer update fails? You now have inconsistent data.

```python
# WRONG — two separate saves, no transaction guarantee
class PlaceOrderHandler:
    def handle(self, command):
        order = Order.place(...)
        self._order_repo.save(order)       # ← commits
        customer.record_order(order.id)
        self._customer_repo.save(customer) # ← fails! order is orphaned
```

### What Is a Unit of Work?

A Unit of Work tracks **all changes** made during a single business operation and commits them **together** in one database transaction — or rolls them all back if anything fails.

```
┌─────────────────────────────────────────────┐
│  Unit of Work                               │
│                                             │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │ OrderRepo    │  │ CustomerRepo       │  │
│  │ (tracked)    │  │ (tracked)          │  │
│  └──────────────┘  └────────────────────┘  │
│                                             │
│  commit() → both saved in ONE transaction   │
│  rollback() → neither is saved             │
└─────────────────────────────────────────────┘
```

### Protocol — `domain/shared/unit_of_work.py`

```python
# domain/shared/unit_of_work.py
from __future__ import annotations
from typing import Protocol
from domain.order.repository import IOrderRepository
from domain.customer.repository import ICustomerRepository


class IUnitOfWork(Protocol):
    """Abstracts a database transaction boundary.

    Provides access to all repositories that share the same transaction.
    commit() saves all changes atomically; rollback() discards everything.
    """

    orders: IOrderRepository
    customers: ICustomerRepository

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def __enter__(self) -> IUnitOfWork:
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...
```

### Infrastructure Implementation — `infrastructure/persistence/sqlalchemy_uow.py`

```python
# infrastructure/persistence/sqlalchemy_uow.py
from sqlalchemy.orm import Session, sessionmaker
from domain.shared.unit_of_work import IUnitOfWork
from infrastructure.persistence.sqlalchemy_order_repo import SQLAlchemyOrderRepository
from infrastructure.persistence.sqlalchemy_customer_repo import SQLAlchemyCustomerRepository


class SQLAlchemyUnitOfWork:
    """Concrete Unit of Work backed by a SQLAlchemy session.

    All repositories in this UoW share the same DB session.
    commit() flushes and commits everything; rollback() discards.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self._session: Session = self._session_factory()
        self.orders = SQLAlchemyOrderRepository(self._session)
        self.customers = SQLAlchemyCustomerRepository(self._session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
```

### Application Service with Unit of Work

```python
# application/order/place_order.py — using UoW
from domain.shared.unit_of_work import IUnitOfWork

class PlaceOrderHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        with self._uow as uow:
            customer = uow.customers.get(command.customer_id)

            if customer.status == CustomerStatus.SUSPENDED:
                raise ValueError("Suspended customers cannot place orders")

            order = Order.place(customer_id=customer.id, currency=command.currency)
            for line in command.lines:
                order.add_line(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
            order.confirm()

            customer.record_last_order(order.id)

            uow.orders.save(order)
            uow.customers.save(customer)
            uow.commit()  # ← both saved atomically

        return PlaceOrderResult(order_id=order.id)
```

### Wiring in `main.py`

```python
# main.py
from infrastructure.persistence.sqlalchemy_uow import SQLAlchemyUnitOfWork

def get_place_order_handler() -> PlaceOrderHandler:
    uow = SQLAlchemyUnitOfWork(session_factory=SessionLocal)
    return PlaceOrderHandler(uow=uow)
```

### Unit of Work vs Repository-per-Request

| Approach | Pros | Cons |
|---|---|---|
| Repository injected with shared session (current doc) | Simple, works for single-aggregate use cases | No explicit transaction boundary; easy to forget commits |
| Unit of Work | Explicit atomicity; groups repos under one transaction | Slightly more wiring; UoW object can grow large |

### Rules of Unit of Work

1. **One UoW per use case** — create it at the start, commit at the end.
2. **All repos come from the UoW** — never mix a UoW repo with a standalone repo.
3. **Commit once** — don't call `commit()` multiple times in one handler.
4. **Let `__exit__` handle rollback** — if an exception escapes, auto-rollback.

---

## 17. Domain Event Dispatching and Handlers

### The Problem: Side Effects Coupled to Business Logic

When an order is placed, you need to:
- Send a confirmation email
- Update analytics
- Notify the warehouse
- Award loyalty points

If you put all of this in `PlaceOrderHandler`, it becomes 200 lines of unrelated concerns glued together.

```python
# WRONG — everything crammed into one handler
class PlaceOrderHandler:
    def handle(self, command):
        order = Order.place(...)
        self._order_repo.save(order)
        self._email_service.send_confirmation(order)     # ← unrelated concern
        self._analytics.track("order_placed", order)     # ← unrelated concern
        self._warehouse.notify_new_order(order)          # ← unrelated concern
        self._loyalty.award_points(order.customer_id)    # ← unrelated concern
```

### Solution: Domain Events + Event Handlers

The aggregate **raises events** when something important happens. Separate **event handlers** listen and react independently.

```
Order.place() → raises OrderPlaced event
                    │
                    ├── SendConfirmationEmailHandler  (infrastructure)
                    ├── UpdateAnalyticsHandler         (infrastructure)
                    ├── NotifyWarehouseHandler         (infrastructure)
                    └── AwardLoyaltyPointsHandler      (application)
```

### Architecture

```
domain/
    order/
        events.py                    ← Event definitions (data classes)
    shared/
        domain_event.py              ← Base event class
        event_bus.py                 ← IEventBus Protocol

application/
    event_handlers/
        on_order_placed.py           ← Handler that awards loyalty points
        on_order_cancelled.py        ← Handler that initiates refund

infrastructure/
    messaging/
        in_memory_event_bus.py       ← Simple sync dispatcher
        kafka_event_bus.py           ← Async distributed dispatcher
    event_handlers/
        send_confirmation_email.py   ← Infrastructure-level handler
        notify_warehouse.py
```

### Base Event — `domain/shared/domain_event.py`

```python
# domain/shared/domain_event.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
```

### Order Events — `domain/order/events.py`

```python
# domain/order/events.py
from dataclasses import dataclass
from domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    total_amount: int = 0
    currency: str = "USD"


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    order_id: str = ""
    tracking_number: str = ""
```

### Aggregate Collects Events

```python
# domain/order/order.py (modified to collect events)
from domain.order.events import OrderPlaced, OrderCancelled

class Order(BaseModel):
    # ... existing fields ...
    _events: list = []

    @property
    def domain_events(self) -> list:
        return list(self._events)

    def clear_events(self) -> None:
        self._events = []

    @classmethod
    def place(cls, customer_id: uuid.UUID, currency: str) -> "Order":
        order = cls(
            customer_id=customer_id,
            currency=currency,
            status=OrderStatus.PENDING,
        )
        # Raise event — does NOT send email, just records that it happened
        order._events.append(
            OrderPlaced(
                order_id=str(order.id),
                customer_id=str(customer_id),
            )
        )
        return order

    def cancel(self, reason: str) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Can only cancel PENDING orders")
        self.status = OrderStatus.CANCELLED
        self._events.append(
            OrderCancelled(
                order_id=str(self.id),
                customer_id=str(self.customer_id),
                reason=reason,
            )
        )
```

### Event Bus Protocol — `domain/shared/event_bus.py`

```python
# domain/shared/event_bus.py
from typing import Protocol, Callable, Type
from domain.shared.domain_event import DomainEvent


class IEventBus(Protocol):
    """Dispatches domain events to registered handlers."""

    def publish(self, event: DomainEvent) -> None:
        ...

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        ...
```

### In-Memory Event Bus — `infrastructure/messaging/in_memory_event_bus.py`

```python
# infrastructure/messaging/in_memory_event_bus.py
from collections import defaultdict
from typing import Callable, Type
from domain.shared.domain_event import DomainEvent
from domain.shared.event_bus import IEventBus


class InMemoryEventBus:
    """Synchronous in-process event dispatcher.

    Good for monoliths and testing. For distributed systems, use Kafka/RabbitMQ.
    """

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
```

### Event Handler Example — `infrastructure/event_handlers/send_confirmation_email.py`

```python
# infrastructure/event_handlers/send_confirmation_email.py
from domain.order.events import OrderPlaced


class SendConfirmationEmailHandler:
    """Reacts to OrderPlaced by sending a confirmation email."""

    def __init__(self, email_client) -> None:
        self._email = email_client

    def handle(self, event: OrderPlaced) -> None:
        self._email.send(
            to=event.customer_id,  # in real app: look up email
            subject="Order Confirmed",
            body=f"Your order {event.order_id} has been placed.",
        )
```

### Application Service Dispatches Events After Save

```python
# application/order/place_order.py — with event dispatching
class PlaceOrderHandler:
    def __init__(self, uow: IUnitOfWork, event_bus: IEventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        with self._uow as uow:
            customer = uow.customers.get(command.customer_id)
            order = Order.place(customer_id=customer.id, currency=command.currency)
            # ...add lines, confirm...

            uow.orders.save(order)
            uow.commit()

        # Dispatch events AFTER successful commit
        for event in order.domain_events:
            self._event_bus.publish(event)
        order.clear_events()

        return PlaceOrderResult(order_id=order.id)
```

### Wiring in `main.py`

```python
# main.py — register event handlers
from infrastructure.messaging.in_memory_event_bus import InMemoryEventBus
from infrastructure.event_handlers.send_confirmation_email import SendConfirmationEmailHandler
from domain.order.events import OrderPlaced, OrderCancelled

event_bus = InMemoryEventBus()
event_bus.subscribe(OrderPlaced, SendConfirmationEmailHandler(email_client).handle)
event_bus.subscribe(OrderPlaced, NotifyWarehouseHandler(warehouse_client).handle)
event_bus.subscribe(OrderCancelled, InitiateRefundHandler(payment_gateway).handle)
```

### Key Rules

1. **Events are raised inside the aggregate** — they record what happened.
2. **Events are dispatched AFTER commit** — never send an email for an order that wasn't saved.
3. **Handlers are independent** — if email fails, warehouse notification still works.
4. **Handlers don't modify the same aggregate** — that would bypass invariants.

---

## 18. Shared Kernel

### The Problem: Duplicated Base Classes Across Bounded Contexts

Every bounded context (Order, Customer, Product) needs:
- A base `Entity` class with an ID
- A base `DomainEvent` class
- Common value objects like `Money`, `Email`, `Address`
- Shared types and exceptions

Without a shared kernel, you duplicate these in every context — or worse, one context imports from another, creating coupling.

### What Is a Shared Kernel?

A Shared Kernel is a **small, carefully managed** set of code that multiple bounded contexts agree to share. It contains only foundational building blocks — never business rules specific to one context.

```
domain/
    shared/                          ← SHARED KERNEL
    │                                  Owned by the team collectively.
    │                                  Changes require agreement from all contexts.
    │
    order/                           ← uses shared/
    customer/                        ← uses shared/
    product/                         ← uses shared/
```

### Folder Structure

```
domain/
    shared/
        __init__.py
        entity.py                    ← Base entity with ID and equality
        aggregate_root.py            ← Base aggregate with event collection
        value_objects.py             ← Money, Email, Address
        domain_event.py              ← Base event class
        specification.py             ← Base specification protocol
        exceptions.py                ← DomainException base class
        types.py                     ← Common type aliases
```

### Base Entity — `domain/shared/entity.py`

```python
# domain/shared/entity.py
from __future__ import annotations
import uuid
from dataclasses import dataclass, field


@dataclass
class Entity:
    """Base class for all domain entities.

    Entities are equal if and only if they have the same ID,
    regardless of their other attributes.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

### Base Aggregate Root — `domain/shared/aggregate_root.py`

```python
# domain/shared/aggregate_root.py
from __future__ import annotations
from dataclasses import dataclass, field
from domain.shared.entity import Entity
from domain.shared.domain_event import DomainEvent


@dataclass
class AggregateRoot(Entity):
    """Base class for all aggregate roots.

    Collects domain events that are dispatched after persistence.
    """

    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    @property
    def domain_events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events = []

    def _raise_event(self, event: DomainEvent) -> None:
        self._events.append(event)
```

### Common Value Objects — `domain/shared/value_objects.py`

```python
# domain/shared/value_objects.py
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Money:
    """Immutable monetary amount. Prevents floating-point currency errors."""

    amount: int       # in smallest unit (cents)
    currency: str     # ISO 4217

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter ISO code")

    def add(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        self._assert_same_currency(other)
        if self.amount < other.amount:
            raise ValueError("Cannot subtract: would result in negative money")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: int) -> Money:
        return Money(amount=self.amount * factor, currency=self.currency)

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Cannot operate on {self.currency} and {other.currency}")


@dataclass(frozen=True)
class Email:
    """Validated email address."""

    value: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email: {self.value}")


@dataclass(frozen=True)
class Address:
    """Postal address value object."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str

    def __post_init__(self) -> None:
        if not all([self.street, self.city, self.country]):
            raise ValueError("Street, city, and country are required")
```

### Domain Exceptions — `domain/shared/exceptions.py`

```python
# domain/shared/exceptions.py

class DomainException(Exception):
    """Base exception for all domain-level errors."""
    pass


class InvariantViolation(DomainException):
    """Raised when an aggregate's invariant is violated."""
    pass


class EntityNotFound(DomainException):
    """Raised when a required entity doesn't exist."""
    pass


class ConcurrencyConflict(DomainException):
    """Raised when optimistic concurrency check fails."""
    pass
```

### How Bounded Contexts Use the Shared Kernel

```python
# domain/order/order.py — imports from shared kernel
from domain.shared.aggregate_root import AggregateRoot
from domain.shared.value_objects import Money
from domain.shared.exceptions import InvariantViolation
from domain.order.events import OrderPlaced


class Order(AggregateRoot):
    """Order aggregate root — inherits ID, equality, and event collection from shared kernel."""

    def add_line(self, product_id, quantity, unit_price: Money) -> None:
        new_total = self.total.add(unit_price.multiply(quantity))
        if new_total.amount > 50_000_00:
            raise InvariantViolation("Order total cannot exceed $50,000")
        # ...
```

### Rules for the Shared Kernel

1. **Keep it minimal** — only code that ALL contexts need.
2. **No business rules** — it's infrastructure for the domain, not domain logic itself.
3. **Changes require team consensus** — since all contexts depend on it.
4. **Version it carefully** — a breaking change here breaks everything.
5. **Never put a specific context's logic here** — if only Order needs it, it belongs in `domain/order/`.

---

## 19. Testing Strategy

### The Testing Pyramid in DDD

```
          ╱╲
         ╱  ╲          E2E Tests (few)
        ╱ E2E╲         — Full HTTP round-trip
       ╱──────╲        — Slow, expensive, fragile
      ╱        ╲
     ╱Integration╲    Integration Tests (moderate)
    ╱──────────────╲   — Repos against real DB
   ╱                ╲  — ACL against real APIs (sandbox)
  ╱   Unit Tests     ╲ Unit Tests (many, fast)
 ╱────────────────────╲ — Domain logic: no DB, no framework
╱                      ╲ — Instantiate class, call method, assert
```

### Folder Structure

```
tests/
    unit/
        domain/
            order/
                test_order.py              ← aggregate invariant tests
                test_order_line.py         ← entity behavior tests
                test_value_objects.py      ← money arithmetic, validation
                test_specifications.py     ← spec logic tests
            pricing/
                test_pricing_service.py    ← domain service tests
        application/
            order/
                test_place_order.py        ← handler with mock repos
                test_cancel_order.py

    integration/
        persistence/
            test_order_repo.py             ← SQLAlchemy repo against test DB
            test_customer_repo.py
        acl/
            test_stripe_gateway.py         ← against Stripe sandbox
        messaging/
            test_kafka_publisher.py        ← against local Kafka

    e2e/
        test_place_order_api.py            ← POST /orders end-to-end
        test_cancel_order_api.py

    conftest.py                            ← shared fixtures (DB session, test client)
```

### Unit Tests — Domain Layer (Fast, No I/O)

```python
# tests/unit/domain/order/test_order.py
import pytest
from domain.order.order import Order
from domain.order.value_objects import OrderStatus, Money


class TestOrderPlacement:
    def test_new_order_is_pending(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        assert order.status == OrderStatus.PENDING

    def test_order_raises_event_on_place(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        assert len(order.domain_events) == 1
        assert order.domain_events[0].__class__.__name__ == "OrderPlaced"


class TestOrderLines:
    def test_can_add_line(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        order.add_line(product_id=uuid.uuid4(), quantity=2, unit_price=Money(1000, "USD"))
        assert len(order.lines) == 1

    def test_total_cannot_exceed_limit(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        with pytest.raises(ValueError, match="exceeding the 50000 limit"):
            order.add_line(
                product_id=uuid.uuid4(),
                quantity=1,
                unit_price=Money(50_001_00, "USD"),
            )


class TestOrderStatusTransitions:
    def test_can_cancel_pending_order(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        order.cancel(reason="changed mind")
        assert order.status == OrderStatus.CANCELLED

    def test_cannot_cancel_confirmed_order(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        order.add_line(product_id=uuid.uuid4(), quantity=1, unit_price=Money(1000, "USD"))
        order.confirm()
        with pytest.raises(ValueError, match="Can only cancel PENDING"):
            order.cancel(reason="too late")

    def test_cannot_confirm_without_lines(self):
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        with pytest.raises(ValueError, match="at least one line"):
            order.confirm()
```

### Unit Tests — Application Layer (Mock Repos)

```python
# tests/unit/application/order/test_place_order.py
import pytest
from unittest.mock import Mock, MagicMock
from application.order.place_order import PlaceOrderHandler, PlaceOrderCommand
from domain.customer.customer import Customer
from domain.customer.value_objects import CustomerStatus


class TestPlaceOrderHandler:
    def setup_method(self):
        self.uow = MagicMock()
        self.event_bus = Mock()
        self.handler = PlaceOrderHandler(uow=self.uow, event_bus=self.event_bus)

    def test_raises_if_customer_not_found(self):
        self.uow.__enter__.return_value = self.uow
        self.uow.customers.get.side_effect = KeyError("not found")

        command = PlaceOrderCommand(customer_id=uuid.uuid4(), lines=[], currency="USD")
        with pytest.raises(KeyError):
            self.handler.handle(command)

    def test_raises_if_customer_suspended(self):
        self.uow.__enter__.return_value = self.uow
        customer = Customer(status=CustomerStatus.SUSPENDED)
        self.uow.customers.get.return_value = customer

        command = PlaceOrderCommand(customer_id=customer.id, lines=[], currency="USD")
        with pytest.raises(ValueError, match="Suspended"):
            self.handler.handle(command)

    def test_successful_placement_commits_and_publishes(self):
        self.uow.__enter__.return_value = self.uow
        customer = Customer(status=CustomerStatus.ACTIVE)
        self.uow.customers.get.return_value = customer

        command = PlaceOrderCommand(
            customer_id=customer.id,
            currency="USD",
            lines=[{"product_id": uuid.uuid4(), "quantity": 1, "unit_price": 1000}],
        )
        result = self.handler.handle(command)

        self.uow.orders.save.assert_called_once()
        self.uow.commit.assert_called_once()
        self.event_bus.publish.assert_called()
        assert result.order_id is not None
```

### Integration Tests — Repository Against Real DB

```python
# tests/integration/persistence/test_order_repo.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.sqlalchemy_order_repo import SQLAlchemyOrderRepository
from domain.order.order import Order
from domain.order.value_objects import Money


@pytest.fixture
def session():
    engine = create_engine("postgresql://test:test@localhost/test_ecommerce")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestSQLAlchemyOrderRepo:
    def test_save_and_retrieve(self, session):
        repo = SQLAlchemyOrderRepository(session)
        order = Order.place(customer_id=uuid.uuid4(), currency="USD")
        order.add_line(product_id=uuid.uuid4(), quantity=2, unit_price=Money(1500, "USD"))

        repo.save(order)
        session.flush()

        retrieved = repo.get(order.id)
        assert retrieved.id == order.id
        assert len(retrieved.lines) == 1
        assert retrieved.total == Money(3000, "USD")

    def test_get_nonexistent_raises(self, session):
        repo = SQLAlchemyOrderRepository(session)
        with pytest.raises(KeyError):
            repo.get(uuid.uuid4())
```

### E2E Tests — Full HTTP Round Trip

```python
# tests/e2e/test_place_order_api.py
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestPlaceOrderAPI:
    def test_place_order_returns_201(self, client):
        response = client.post("/orders", json={
            "customer_id": "550e8400-e29b-41d4-a716-446655440000",
            "currency": "USD",
            "lines": [
                {"product_id": "...", "quantity": 2, "unit_price": 1500}
            ],
        })
        assert response.status_code == 201
        assert "order_id" in response.json()

    def test_place_order_invalid_customer_returns_404(self, client):
        response = client.post("/orders", json={
            "customer_id": "00000000-0000-0000-0000-000000000000",
            "currency": "USD",
            "lines": [{"product_id": "...", "quantity": 1, "unit_price": 1000}],
        })
        assert response.status_code == 404
```

### What Each Test Layer Validates

| Layer | Tests | Speed | Dependencies |
|---|---|---|---|
| Unit / Domain | Business rules, invariants, state transitions | Milliseconds | None |
| Unit / Application | Orchestration logic, correct calls to repos | Milliseconds | Mocks only |
| Integration | Repos map correctly to DB; ACLs translate correctly | Seconds | Real DB / sandbox API |
| E2E | Full request → response works; wiring is correct | Seconds | Full running app |

### The Golden Rule

> **Domain unit tests should NEVER need a database, HTTP server, or any framework.** If they do, your domain has leaked infrastructure.

---

## 20. Bounded Context Mapping

### The Problem: How Do Multiple Bounded Contexts Communicate?

In a real system, `Order`, `Customer`, `Product`, `Inventory`, `Shipping`, and `Billing` are separate bounded contexts. Each has its own:
- Ubiquitous language (same word, different meaning)
- Data model
- Team ownership (potentially)

How they communicate defines your architecture's resilience and coupling.

### What Is a Context Map?

A Context Map is a diagram + documentation showing **how bounded contexts relate** to each other — who depends on whom, and what style of integration they use.

### Relationship Patterns

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONTEXT MAP                                   │
│                                                                     │
│  ┌──────────┐   Shared Kernel    ┌──────────┐                      │
│  │  Order   │◄──────────────────►│ Customer │                      │
│  │ Context  │                    │ Context  │                      │
│  └────┬─────┘                    └──────────┘                      │
│       │                                                             │
│       │ Customer-Supplier                                           │
│       │ (Order is downstream)                                       │
│       ▼                                                             │
│  ┌──────────┐                    ┌──────────┐                      │
│  │Inventory │   Conformist       │ Shipping │                      │
│  │ Context  │◄───────────────────│ Context  │                      │
│  └──────────┘                    └────┬─────┘                      │
│                                       │                             │
│                                       │ ACL (Anti-Corruption Layer) │
│                                       ▼                             │
│                                  ┌──────────┐                      │
│                                  │  FedEx   │  (External system)    │
│                                  │  API     │                      │
│                                  └──────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

### The Integration Patterns Explained

#### 1. Shared Kernel

Two contexts share a small common library (value objects, base classes). Both teams own it together.

```python
# Both Order and Customer import from domain/shared/
from domain.shared.value_objects import Money, Email
```

**When to use:** Contexts are owned by the same team. Shared code is small and stable.  
**Risk:** Changes to the kernel affect all contexts.

#### 2. Customer-Supplier

One context (supplier/upstream) provides data that another (customer/downstream) consumes. The downstream team can request features from the upstream team.

```
Upstream (Supplier): Product Context — defines product catalog
Downstream (Customer): Order Context — needs product prices and availability
```

```python
# Order context consumes Product context's data via a defined interface
class IProductCatalog(Protocol):
    def get_price(self, product_id: uuid.UUID) -> Money: ...
    def check_availability(self, product_id: uuid.UUID, qty: int) -> bool: ...
```

**When to use:** Two teams with a cooperative relationship. Downstream can influence upstream's API.

#### 3. Conformist

The downstream context **accepts the upstream's model as-is** — no translation, no negotiation. You conform to their data format.

```python
# You just use their response format directly — no translation layer
# Acceptable when the upstream model is good enough and stable
```

**When to use:** The upstream is a dominant system (ERP, legacy DB). You have no power to change it, and their model is acceptable.  
**Risk:** If their model is ugly, your code becomes ugly.

#### 4. Anti-Corruption Layer (ACL)

The downstream context **translates** the upstream's foreign model into its own domain language. (Covered in detail in Section 15.)

**When to use:** External system with an incompatible model. You refuse to let their mess into your domain.

#### 5. Published Language

A context publishes a well-documented schema (JSON Schema, Protobuf, Avro) that others consume. The schema IS the contract.

```python
# Order context publishes events in a documented schema
# Other contexts consume the event, trusting the published schema

# order_placed_v1.json (Published Language)
{
    "event": "OrderPlaced",
    "version": 1,
    "schema": {
        "order_id": "string (UUID)",
        "customer_id": "string (UUID)",
        "total_cents": "integer",
        "currency": "string (ISO 4217)"
    }
}
```

**When to use:** Async communication via events/messages between contexts (especially microservices).

#### 6. Open Host Service

A context exposes a well-defined API (REST, gRPC) that multiple consumers use. The API is the stable contract.

```
Product Context exposes:
  GET /products/{id}         ← used by Order, Recommendation, Marketing
  GET /products?category=X   ← used by Search, Analytics
```

**When to use:** One context serves many consumers. Invest in a stable, versioned API.

#### 7. Separate Ways

Two contexts have **no integration** — they're completely independent. Data is duplicated where needed.

**When to use:** The cost of integration exceeds the cost of duplication.

### How Bounded Contexts Communicate in Practice

| Integration Style | Coupling | Latency | Example |
|---|---|---|---|
| Synchronous API call | High | Low | Order calls Inventory.reserve() |
| Domain Events (async) | Low | Higher | Order emits OrderPlaced → Shipping reacts |
| Shared Database | Very High | Low | AVOID — this is an anti-pattern |
| Message Queue | Low | Medium | Order publishes to Kafka → Billing subscribes |

### The Golden Rule of Context Boundaries

> **Each bounded context should be deployable independently.** If changing Order forces you to redeploy Customer, your boundary is wrong.

### Ubiquitous Language Conflicts

The same word means different things in different contexts:

| Term | In Order Context | In Shipping Context | In Billing Context |
|---|---|---|---|
| "Address" | Where customer lives | Where to ship the package | Where to send the invoice |
| "Product" | Line item with quantity | Package dimensions + weight | Billable SKU |
| "Customer" | Entity placing orders | Recipient name on label | Payer with payment method |

This is WHY bounded contexts exist — to give each concept its own precise meaning.

---

## 21. Factory Pattern

### The Problem: Complex Aggregate Creation

Creating an aggregate isn't always as simple as `Order.place(customer_id, currency)`. In real systems:
- You reconstruct aggregates **from persistence** (hydration from DB rows).
- You create aggregates **from external events** (a message from another system).
- You build aggregates with **complex initialization** (multiple validation steps, defaults, derived fields).

If this logic lives in the constructor, it becomes bloated and impossible to test in isolation.

### What Is a Factory in DDD?

A Factory encapsulates **complex object creation** so that the client doesn't need to know the details. It ensures the aggregate is **always created in a valid state**.

### Three Types of Factories

```
1. Factory Method (on the aggregate itself)      ← simplest, most common
2. Standalone Factory (separate class)           ← for complex or cross-aggregate creation
3. Repository as Factory (reconstruction)        ← for hydrating from persistence
```

### Type 1: Factory Method on the Aggregate

Already present in the document — `Order.place()` is a factory method:

```python
# domain/order/order.py
class Order(AggregateRoot):
    @classmethod
    def place(cls, customer_id: uuid.UUID, currency: str) -> "Order":
        """Factory method — guarantees Order is born in valid state."""
        order = cls(
            customer_id=customer_id,
            currency=currency,
            status=OrderStatus.PENDING,
            lines=[],
        )
        order._raise_event(OrderPlaced(order_id=str(order.id), customer_id=str(customer_id)))
        return order
```

**When to use:** Creation logic is simple, belongs to the aggregate, and doesn't require external data.

### Type 2: Standalone Factory — Complex Creation

When creating an aggregate requires data from **multiple sources** or complex rules that don't belong inside the aggregate itself.

```python
# domain/order/order_factory.py
from __future__ import annotations
import uuid
from domain.order.order import Order
from domain.order.value_objects import Money, OrderStatus
from domain.customer.customer import Customer
from domain.product.product import Product
from domain.pricing.pricing_service import PricingService


class OrderFactory:
    """Creates Order aggregates from complex inputs.

    Use when:
    - Creation needs data from multiple aggregates (Customer tier, Product price).
    - Multiple validation steps are required before the aggregate can exist.
    - Different creation paths exist (web order, import order, repeat order).
    """

    def __init__(self, pricing_service: PricingService) -> None:
        self._pricing = pricing_service

    def create_from_cart(
        self,
        customer: Customer,
        cart_items: list[dict],
        products: dict[uuid.UUID, Product],
    ) -> Order:
        """Create an order from a shopping cart.

        Applies pricing rules, validates stock, and builds the order.
        """
        if not cart_items:
            raise ValueError("Cannot create order from empty cart")

        order = Order.place(customer_id=customer.id, currency="USD")

        for item in cart_items:
            product = products[item["product_id"]]
            breakdown = self._pricing.calculate_line_price(
                product=product,
                customer=customer,
                quantity=item["quantity"],
            )
            order.add_line(
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=breakdown.final_price,
            )

        return order

    def create_repeat_order(self, customer: Customer, previous_order: Order) -> Order:
        """Create a new order by copying lines from a previous order."""
        order = Order.place(customer_id=customer.id, currency=previous_order.currency)
        for line in previous_order.lines:
            order.add_line(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
            )
        return order

    def create_from_import(self, external_data: dict) -> Order:
        """Create an order from an external system's data (e.g., legacy migration).

        Translates foreign field names and applies domain validation.
        """
        order = Order.place(
            customer_id=uuid.UUID(external_data["cust_ref"]),
            currency=external_data.get("ccy", "USD"),
        )
        for item in external_data.get("line_items", []):
            order.add_line(
                product_id=uuid.UUID(item["sku_id"]),
                quantity=item["qty"],
                unit_price=Money(amount=item["price_cents"], currency="USD"),
            )
        return order
```

### Type 3: Repository as Reconstitution Factory

When you load an aggregate from the database, the repository acts as a factory that **reconstitutes** the domain object from raw data — without triggering creation events.

```python
# infrastructure/persistence/sqlalchemy_order_repo.py (excerpt)
class SQLAlchemyOrderRepository:
    def _to_domain(self, model: OrderModel) -> Order:
        """Reconstitute an Order aggregate from database model.

        This is a factory operation — it builds a domain object from
        persistence data WITHOUT triggering OrderPlaced events.
        """
        order = Order.__new__(Order)  # bypass __init__ to avoid re-validation
        order.id = uuid.UUID(model.id)
        order.customer_id = uuid.UUID(model.customer_id)
        order.status = OrderStatus(model.status)
        order.currency = model.currency
        order.lines = [
            self._to_domain_line(line_model)
            for line_model in model.lines
        ]
        order._events = []  # no events on reconstitution
        return order
```

### Using Factory in Application Service

```python
# application/order/place_order.py — using factory
from domain.order.order_factory import OrderFactory

class PlaceOrderHandler:
    def __init__(
        self,
        uow: IUnitOfWork,
        product_repo: IProductRepository,
        order_factory: OrderFactory,
        event_bus: IEventBus,
    ) -> None:
        self._uow = uow
        self._product_repo = product_repo
        self._factory = order_factory
        self._event_bus = event_bus

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        with self._uow as uow:
            customer = uow.customers.get(command.customer_id)
            products = {
                line.product_id: self._product_repo.get(line.product_id)
                for line in command.lines
            }

            # Factory handles complex creation
            order = self._factory.create_from_cart(
                customer=customer,
                cart_items=[vars(line) for line in command.lines],
                products=products,
            )
            order.confirm()

            uow.orders.save(order)
            uow.commit()

        for event in order.domain_events:
            self._event_bus.publish(event)
        order.clear_events()
        return PlaceOrderResult(order_id=order.id)
```

### When to Use Each Type

| Scenario | Factory Type |
|---|---|
| Simple creation, no external dependencies | Factory method (`Order.place(...)`) |
| Creation needs multiple aggregates or services | Standalone Factory class |
| Multiple creation paths (from cart, from import, repeat) | Standalone Factory with multiple methods |
| Rebuilding from database/persistence | Repository's internal reconstitution method |
| Creation logic is reused across multiple use cases | Standalone Factory (shared via DI) |

---

## 22. Outbox Pattern — Reliable Event Publishing

### The Problem: Save and Publish Must Be Atomic

After placing an order, you do two things:
1. Save the order to the database
2. Publish an `OrderPlaced` event to Kafka/RabbitMQ

What happens if the DB save succeeds but the message broker is down? The order exists in the database, but no one knows about it — no email, no warehouse notification, no analytics.

What if you publish first, then the DB save fails? Now you've told the world about an order that doesn't exist.

```python
# WRONG — not atomic
def handle(self, command):
    order = Order.place(...)
    self._order_repo.save(order)          # ← succeeds
    self._event_bus.publish(OrderPlaced)   # ← broker is down! event lost forever
```

### What Is the Outbox Pattern?

Instead of publishing directly to a message broker, you **write the event to an outbox table in the same database transaction** as the aggregate. A separate background process (relay) reads the outbox and publishes to the broker.

```
┌─────────────────────────────────────────────────────────┐
│  Single Database Transaction                            │
│                                                         │
│  1. INSERT INTO orders (...)                            │
│  2. INSERT INTO outbox (event_type, payload, ...)       │
│                                                         │
│  COMMIT  ← both succeed or both fail (ACID)            │
└─────────────────────────────────────────────────────────┘
          │
          │  (later, async)
          ▼
┌─────────────────────────────────────────────────────────┐
│  Outbox Relay (background worker)                       │
│                                                         │
│  1. SELECT * FROM outbox WHERE published = false        │
│  2. Publish each event to Kafka                         │
│  3. UPDATE outbox SET published = true WHERE id = ...   │
└─────────────────────────────────────────────────────────┘
```

### Folder Structure

```
infrastructure/
    persistence/
        outbox.py                    ← Outbox repository (stores events in DB)
        outbox_model.py              ← SQLAlchemy model for outbox table
    messaging/
        outbox_relay.py              ← Background worker that publishes from outbox
        kafka_publisher.py           ← Actual Kafka publish logic
```

### Outbox DB Model — `infrastructure/persistence/outbox_model.py`

```python
# infrastructure/persistence/outbox_model.py
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from infrastructure.persistence.base import Base
import uuid
from datetime import datetime


class OutboxMessage(Base):
    """Stores domain events as outbox messages for reliable publishing."""

    __tablename__ = "outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(255), nullable=False, index=True)
    aggregate_id = Column(String(255), nullable=False, index=True)
    payload = Column(Text, nullable=False)       # JSON-serialized event
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)
```

### Outbox Repository — `infrastructure/persistence/outbox.py`

```python
# infrastructure/persistence/outbox.py
import json
from datetime import datetime
from sqlalchemy.orm import Session
from domain.shared.domain_event import DomainEvent
from infrastructure.persistence.outbox_model import OutboxMessage


class OutboxRepository:
    """Stores domain events in the outbox table within the same transaction."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def store(self, event: DomainEvent, aggregate_id: str) -> None:
        message = OutboxMessage(
            event_type=type(event).__name__,
            aggregate_id=aggregate_id,
            payload=json.dumps(self._serialize_event(event)),
        )
        self._session.add(message)

    def get_unpublished(self, batch_size: int = 100) -> list[OutboxMessage]:
        return (
            self._session.query(OutboxMessage)
            .filter(OutboxMessage.published == False)
            .order_by(OutboxMessage.created_at)
            .limit(batch_size)
            .all()
        )

    def mark_published(self, message_id) -> None:
        message = self._session.query(OutboxMessage).get(message_id)
        if message:
            message.published = True
            message.published_at = datetime.utcnow()

    def _serialize_event(self, event: DomainEvent) -> dict:
        return {
            "event_id": event.event_id,
            "occurred_at": event.occurred_at.isoformat(),
            **{k: v for k, v in vars(event).items() if k not in ("event_id", "occurred_at")},
        }
```

### Modified Unit of Work — Saves Events to Outbox

```python
# infrastructure/persistence/sqlalchemy_uow.py (modified)
class SQLAlchemyUnitOfWork:
    def __enter__(self):
        self._session = self._session_factory()
        self.orders = SQLAlchemyOrderRepository(self._session)
        self.customers = SQLAlchemyCustomerRepository(self._session)
        self.outbox = OutboxRepository(self._session)  # ← same session!
        return self

    def commit_with_events(self, events: list[DomainEvent], aggregate_id: str) -> None:
        """Commit aggregate changes AND store events in ONE transaction."""
        for event in events:
            self.outbox.store(event, aggregate_id)
        self._session.commit()  # ← both aggregate + outbox in single COMMIT
```

### Application Service Uses Outbox

```python
# application/order/place_order.py — with outbox pattern
class PlaceOrderHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    def handle(self, command: PlaceOrderCommand) -> PlaceOrderResult:
        with self._uow as uow:
            customer = uow.customers.get(command.customer_id)
            order = Order.place(customer_id=customer.id, currency=command.currency)
            # ...add lines, confirm...

            uow.orders.save(order)

            # Events stored in same DB transaction — guaranteed consistency
            uow.commit_with_events(
                events=order.domain_events,
                aggregate_id=str(order.id),
            )
            order.clear_events()

        return PlaceOrderResult(order_id=order.id)
```

### Outbox Relay — Background Worker

```python
# infrastructure/messaging/outbox_relay.py
import json
import time
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.outbox import OutboxRepository
from infrastructure.messaging.kafka_publisher import KafkaPublisher


class OutboxRelay:
    """Background process that polls outbox and publishes to Kafka.

    Run as a separate process (e.g., Celery beat, cron, or dedicated worker).
    Guarantees at-least-once delivery.
    """

    def __init__(self, session_factory: sessionmaker, publisher: KafkaPublisher) -> None:
        self._session_factory = session_factory
        self._publisher = publisher

    def run_forever(self, poll_interval_seconds: float = 1.0) -> None:
        while True:
            self._process_batch()
            time.sleep(poll_interval_seconds)

    def _process_batch(self) -> None:
        session = self._session_factory()
        try:
            outbox = OutboxRepository(session)
            messages = outbox.get_unpublished(batch_size=50)

            for message in messages:
                self._publisher.publish(
                    topic=f"domain.events.{message.event_type}",
                    key=message.aggregate_id,
                    value=message.payload,
                )
                outbox.mark_published(message.id)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

### Kafka Publisher — `infrastructure/messaging/kafka_publisher.py`

```python
# infrastructure/messaging/kafka_publisher.py
from kafka import KafkaProducer
import json


class KafkaPublisher:
    """Publishes messages to Kafka topics."""

    def __init__(self, bootstrap_servers: str) -> None:
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8") if isinstance(v, dict) else v.encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8"),
        )

    def publish(self, topic: str, key: str, value: str) -> None:
        self._producer.send(topic, key=key, value=value)
        self._producer.flush()
```

### Why Outbox Instead of Direct Publish?

| Approach | Problem |
|---|---|
| Publish first, then save | If save fails → consumers got a ghost event |
| Save first, then publish | If publish fails → event is lost |
| Outbox (save + event in one TX) | Guaranteed: if order exists → event will eventually be published |

### Delivery Guarantees

The outbox gives you **at-least-once delivery**. The relay might publish the same event twice (if it crashes after publishing but before marking as published). Consumers must be **idempotent** — processing the same event twice should produce the same result.

```python
# Consumer idempotency — check if already processed
class ShippingEventHandler:
    def handle(self, event: OrderPlaced) -> None:
        if self._already_processed(event.event_id):
            return  # skip duplicate
        self._create_shipment(event)
        self._mark_processed(event.event_id)
```

---

## 23. Complete Updated Folder Structure

With all patterns included, here is the final production-grade DDD structure:

```
ecommerce/
│
├── domain/                              ← Pure business logic (no I/O)
│   │
│   ├── shared/                          ← SHARED KERNEL
│   │   ├── __init__.py
│   │   ├── entity.py                   ← Base entity with ID + equality
│   │   ├── aggregate_root.py           ← Base aggregate with event collection
│   │   ├── value_objects.py            ← Money, Email, Address
│   │   ├── domain_event.py            ← Base DomainEvent class
│   │   ├── event_bus.py               ← IEventBus Protocol
│   │   ├── unit_of_work.py            ← IUnitOfWork Protocol
│   │   ├── specification.py           ← Base Specification + composites
│   │   └── exceptions.py              ← DomainException, InvariantViolation
│   │
│   ├── order/                          ← Order Bounded Context
│   │   ├── __init__.py
│   │   ├── order.py                   ← Order aggregate root
│   │   ├── order_line.py             ← OrderLine entity
│   │   ├── order_factory.py          ← Standalone factory for complex creation
│   │   ├── value_objects.py           ← OrderStatus, ShippingInfo
│   │   ├── events.py                  ← OrderPlaced, OrderCancelled, OrderShipped
│   │   ├── repository.py             ← IOrderRepository Protocol
│   │   └── specifications.py         ← RefundEligibleSpec, HighValueOrderSpec
│   │
│   ├── customer/                       ← Customer Bounded Context
│   │   ├── __init__.py
│   │   ├── customer.py               ← Customer entity/aggregate
│   │   ├── value_objects.py           ← CustomerStatus, Tier
│   │   ├── repository.py             ← ICustomerRepository Protocol
│   │   └── specifications.py         ← HighValueCustomerSpec
│   │
│   ├── product/                        ← Product Bounded Context
│   │   ├── __init__.py
│   │   ├── product.py                ← Product aggregate
│   │   └── repository.py             ← IProductRepository Protocol
│   │
│   ├── pricing/                        ← DOMAIN SERVICE
│   │   ├── __init__.py
│   │   ├── pricing_service.py        ← Cross-aggregate pricing rules
│   │   └── value_objects.py           ← Discount, PriceBreakdown
│   │
│   └── payment/                        ← Payment subdomain
│       ├── __init__.py
│       ├── gateway.py                 ← IPaymentGateway Protocol
│       └── value_objects.py           ← PaymentConfirmation, PaymentRequest
│
├── application/                        ← Use cases / Orchestration
│   │
│   ├── order/
│   │   ├── place_order.py            ← PlaceOrderCommand + Handler
│   │   ├── cancel_order.py           ← CancelOrderCommand + Handler
│   │   ├── request_refund.py         ← Uses specification
│   │   └── get_order.py              ← Query handler (read side)
│   │
│   ├── customer/
│   │   ├── register_customer.py
│   │   └── update_address.py
│   │
│   └── event_handlers/                ← React to domain events
│       ├── on_order_placed.py         ← Award loyalty points
│       └── on_order_cancelled.py      ← Initiate refund
│
├── infrastructure/                     ← I/O adapters
│   │
│   ├── persistence/
│   │   ├── base.py                    ← SQLAlchemy Base
│   │   ├── models.py                  ← ORM models (OrderModel, etc.)
│   │   ├── outbox_model.py           ← Outbox table model
│   │   ├── outbox.py                 ← OutboxRepository
│   │   ├── sqlalchemy_uow.py         ← Unit of Work implementation
│   │   ├── sqlalchemy_order_repo.py  ← IOrderRepository implementation
│   │   └── sqlalchemy_customer_repo.py
│   │
│   ├── acl/                           ← Anti-Corruption Layer
│   │   ├── payment_gateway.py        ← Stripe → domain translation
│   │   └── shipping_provider.py      ← FedEx → domain translation
│   │
│   ├── messaging/
│   │   ├── in_memory_event_bus.py    ← Sync dispatcher (dev/test)
│   │   ├── kafka_publisher.py        ← Kafka publish logic
│   │   └── outbox_relay.py           ← Background outbox → Kafka worker
│   │
│   ├── api/                           ← HTTP layer (FastAPI)
│   │   ├── orders.py                 ← REST routes
│   │   ├── customers.py
│   │   └── schemas.py                ← Pydantic request/response models
│   │
│   └── event_handlers/               ← Infrastructure-level handlers
│       ├── send_confirmation_email.py
│       └── notify_warehouse.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/                   ← Fast, no DB
│   │   └── application/              ← Mocked repos
│   ├── integration/
│   │   ├── persistence/              ← Real DB
│   │   └── acl/                      ← Sandbox APIs
│   └── e2e/                          ← Full HTTP round-trip
│
├── main.py                            ← Composition Root / DI wiring
├── requirements.txt
└── README.md
```

---

## Final Checklist: Complete DDD Pattern Coverage

| # | Pattern | Section | Status |
|---|---|---|---|
| 1 | Rich Domain Model (vs Anemic) | §1–2 | ✅ |
| 2 | Aggregate Roots with Invariants | §5 | ✅ |
| 3 | Value Objects (immutable, no identity) | §5.1 | ✅ |
| 4 | Domain Events | §5.4 | ✅ |
| 5 | Repository Protocol (interface in domain) | §5.5 | ✅ |
| 6 | Repository Implementation (infrastructure) | §7.1 | ✅ |
| 7 | Application Services as Orchestrators | §6, §11 | ✅ |
| 8 | CQRS-lite (Commands vs Queries) | §6 | ✅ |
| 9 | Composition Root / DI Wiring | §8 | ✅ |
| 10 | Dependency Direction (inward only) | §4, §10 | ✅ |
| 11 | Domain Services | §13 | ✅ |
| 12 | Specifications (reusable predicates) | §14 | ✅ |
| 13 | Anti-Corruption Layer (ACL) | §15 | ✅ |
| 14 | Unit of Work | §16 | ✅ |
| 15 | Domain Event Dispatching + Handlers | §17 | ✅ |
| 16 | Shared Kernel | §18 | ✅ |
| 17 | Testing Strategy (unit/integration/E2E) | §19 | ✅ |
| 18 | Bounded Context Mapping | §20 | ✅ |
| 19 | Factory Pattern | §21 | ✅ |
| 20 | Outbox Pattern (reliable event delivery) | §22 | ✅ |
