# Domain-Driven Design — Complete Reference Guide

Everything from Eric Evans' "Domain-Driven Design: Tackling Complexity in the Heart of Software" — distilled with Python examples so you can skip the 560-page book.

---

## Table of Contents

1. [What Is DDD & When To Use It](#1-what-is-ddd--when-to-use-it)
2. [Knowledge Crunching](#2-knowledge-crunching)
3. [Ubiquitous Language](#3-ubiquitous-language)
4. [Model-Driven Design](#4-model-driven-design)
5. [Layered Architecture](#5-layered-architecture)
6. [Entities](#6-entities)
7. [Value Objects](#7-value-objects)
8. [Domain Services](#8-domain-services)
9. [Modules (Packages)](#9-modules-packages)
10. [Aggregates](#10-aggregates)
11. [Factories](#11-factories)
12. [Repositories](#12-repositories)
13. [Domain Events](#13-domain-events)
14. [Specification Pattern](#14-specification-pattern)
15. [Strategy / Policy Pattern](#15-strategy--policy-pattern)
16. [Bounded Context](#16-bounded-context)
17. [Context Map](#17-context-map)
18. [Anti-Corruption Layer](#18-anti-corruption-layer)
19. [Shared Kernel](#19-shared-kernel)
20. [Customer-Supplier](#20-customer-supplier)
21. [Conformist](#21-conformist)
22. [Open Host Service & Published Language](#22-open-host-service--published-language)
23. [Separate Ways](#23-separate-ways)
24. [Supple Design](#24-supple-design)
25. [Distillation — Core Domain](#25-distillation--core-domain)
26. [Large-Scale Structure](#26-large-scale-structure)
27. [Full Example: E-Commerce System](#27-full-example-e-commerce-system)
28. [Full Example: Ride-Sharing System](#28-full-example-ride-sharing-system)
29. [DDD Decision Cheatsheet](#29-ddd-decision-cheatsheet)

---

## 1. What Is DDD & When To Use It

DDD is **not** a technology or framework. It is a way of thinking about software design that puts the **business domain** at the center.

```
Core Idea:
  The structure of your code should mirror the structure of the business problem.
  The language your code uses should be the language the business uses.
```

### When to Use DDD

```
✓ Complex business logic (not CRUD)
✓ Domain experts are available for collaboration
✓ Long-lived project that will evolve
✓ Multiple teams working on the same large system

✗ Simple CRUD apps → use Transaction Script or Smart UI
✗ No access to domain experts
✗ Short-lived throwaway prototypes
✗ Pure technical/infrastructure projects
```

### The Two Halves of DDD

```
Strategic DDD (the big picture):
  How to divide a large system into Bounded Contexts
  How teams relate to each other
  Where the Core Domain is

Tactical DDD (the building blocks):
  Entities, Value Objects, Aggregates, Repositories, Services, Factories, Domain Events
  How to structure code inside one Bounded Context
```

---

## 2. Knowledge Crunching

The process of developers and domain experts collaborating intensively to distill a useful model from a torrent of domain information.

```
Process:
  1. Talk to domain experts repeatedly
  2. Sketch models (diagrams, scenarios)
  3. Try them out in code (prototype)
  4. Get feedback — does it feel right to the expert?
  5. Refine — drop irrelevant concepts, sharpen important ones
  6. Repeat continuously

Key Insight: The model is NOT a data schema.
  It captures behavior, rules, and processes — not just nouns.
```

### Example: Cargo Shipping

Evans describes how the shipping team first modeled cargo as "moving containers from place to place." After months of knowledge crunching, the deeper model emerged: shipping is really about **transferring responsibility** from entity to entity (shipper → carrier → carrier → consignee). This shift transformed the software.

```python
class Cargo:
    """Initial shallow model — just tracks location."""
    def __init__(self, tracking_id: str, origin: str, destination: str):
        self.tracking_id = tracking_id
        self.origin = origin
        self.destination = destination
        self.current_location = origin

class Cargo:
    """Deeper model — tracks responsibility transfers."""
    def __init__(self, tracking_id: str, route_spec: "RouteSpecification"):
        self.tracking_id = tracking_id
        self.route_spec = route_spec
        self.custody_history: list["CustodyTransfer"] = []

    @property
    def current_custodian(self) -> "Party":
        return self.custody_history[-1].to_party if self.custody_history else None

    def transfer_custody(self, from_party: "Party", to_party: "Party", doc: "BillOfLading"):
        transfer = CustodyTransfer(from_party, to_party, doc)
        self.custody_history.append(transfer)
```

---

## 3. Ubiquitous Language

A shared language between developers and domain experts, used in conversation, documentation, AND code.

```
Rules:
  1. Use the SAME terms in code, in meetings, and in docs
  2. When the language changes, the code changes (rename classes, methods)
  3. When the code changes, update the team's vocabulary
  4. No translation layers between developer-speak and business-speak
  5. If a domain expert can't understand the model, something is WRONG
```

### Bad vs Good

```
BAD (developer-speak):
  "We'll delete all rows in the shipment table with that cargo ID,
   then pass origin and destination into the Routing Service,
   and it will re-populate the table."

GOOD (ubiquitous language):
  "When the Route Specification changes, we'll check if the
   current Itinerary still satisfies the Specification.
   If not, the Routing Service generates a new Itinerary."
```

### In Code

```python
class OverbookingPolicy:
    """
    Policy is the DDD term for the Strategy pattern.
    This name came directly from domain expert conversations.
    """
    MAX_OVERBOOKING_RATIO = 1.10

    def is_allowed(self, cargo: "Cargo", voyage: "Voyage") -> bool:
        max_booking = voyage.capacity * self.MAX_OVERBOOKING_RATIO
        return (voyage.booked_cargo_size + cargo.size) <= max_booking
```

---

## 4. Model-Driven Design

There is ONE model that serves both analysis AND implementation. No separate "analysis model" and "design model."

```
Principle:
  If the design or code does not map to the domain model,
  that model is of little value.

  The code IS the model. The model IS the code.

  A change in understanding → change the model → change the code.
  A change needed in the code → rethink the model → update the shared language.
```

---

## 5. Layered Architecture

Isolate the domain logic from everything else.

```
┌─────────────────────────────────────────────┐
│           Presentation / UI Layer           │  ← Displays info, interprets user input
├─────────────────────────────────────────────┤
│            Application Layer                │  ← Thin. Orchestrates use cases.
│   (No business logic here — only workflow)  │     Coordinates domain objects.
├─────────────────────────────────────────────┤
│              Domain Layer                   │  ← THE HEART. All business rules,
│     (Entities, VOs, Services, Events)       │     domain logic, invariants live here.
├─────────────────────────────────────────────┤
│           Infrastructure Layer              │  ← DB, messaging, file I/O, email,
│    (Repos implementation, ORM, APIs)        │     external service adapters.
└─────────────────────────────────────────────┘

Key rules:
  • Each layer depends ONLY on layers below it
  • Domain layer has ZERO dependency on infrastructure
  • Application layer is THIN — no business rules
  • Domain layer NEVER imports from presentation
```

### Example: Folder Structure

```
order_service/
├── application/           # Application layer
│   ├── place_order.py     # Use case / command handler
│   └── get_order.py       # Query handler
├── domain/                # Domain layer
│   ├── model/
│   │   ├── order.py       # Entity (Aggregate Root)
│   │   ├── order_item.py  # Entity (inside Aggregate)
│   │   ├── money.py       # Value Object
│   │   └── address.py     # Value Object
│   ├── service/
│   │   └── pricing.py     # Domain Service
│   ├── event/
│   │   └── order_placed.py
│   └── repository/
│       └── order_repo.py  # Interface (abstract)
├── infrastructure/        # Infrastructure layer
│   ├── persistence/
│   │   └── sql_order_repo.py  # Implements order_repo interface
│   └── messaging/
│       └── kafka_publisher.py
└── presentation/          # UI / API layer
    └── api/
        └── order_api.py
```

### Application Layer (thin orchestrator)

```python
class PlaceOrderUseCase:
    def __init__(self, order_repo: OrderRepository, pricing: PricingService):
        self._order_repo = order_repo
        self._pricing = pricing

    def execute(self, cmd: PlaceOrderCommand) -> str:
        order = Order.create(
            customer_id=cmd.customer_id,
            items=cmd.items,
            shipping_address=cmd.shipping_address,
        )
        self._pricing.apply_discounts(order)
        self._order_repo.save(order)
        return order.order_id
```

---

## 6. Entities

Objects defined by their **identity**, not their attributes. They have a life cycle — they're born, change state, and die.

```
Key traits:
  • Has a unique identity (ID) that persists across time
  • Two Entities with the same attributes but different IDs are DIFFERENT
  • Two references with the same ID are the SAME entity, even if attributes differ
  • Must implement equality based on identity, not attributes
  • Identity is immutable; attributes can change
```

### When Is It an Entity?

```
"Does the user of the application CARE if this is the same thing they saw before?"
  YES → Entity
  NO  → Value Object

Examples:
  Customer → Entity (we track them by ID)
  Order    → Entity (each order is unique, tracked by order number)
  Bank Transaction → Entity (two $50 deposits are distinct events)
  Seat (assigned seating) → Entity (seat A12 is specific)
  Seat (general admission) → NOT Entity (any seat will do)
```

### Template

```python
from dataclasses import dataclass, field
from uuid import uuid4


class Entity:
    """Base class for all Entities."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Customer(Entity):
    def __init__(self, customer_id: str, name: str, email: str):
        self.id = customer_id          # identity — immutable
        self.name = name               # can change
        self.email = email             # can change
        self._credit_score: int = 0    # internal state

    def update_email(self, new_email: str):
        if "@" not in new_email:
            raise ValueError("Invalid email")
        self.email = new_email

    def __repr__(self):
        return f"Customer(id={self.id})"


c1 = Customer("CUST-001", "Alice", "alice@mail.com")
c2 = Customer("CUST-001", "Alice Smith", "alice.smith@mail.com")
assert c1 == c2  # Same identity → same entity, even though name/email differ
```

### Identity Strategies

```
1. Natural key:     ISBN for books, SSN for people (risky — can change)
2. Surrogate key:   UUID, auto-increment DB ID (most common)
3. Domain-assigned:  Tracking number, booking confirmation code
4. External system:  Tax ID, passport number
```

---

## 7. Value Objects

Objects defined by their **attributes**, not identity. They describe some characteristic of a thing. They are **immutable**.

```
Key traits:
  • No identity — two VOs with same attributes are EQUAL and INTERCHANGEABLE
  • Immutable — once created, never modified. Change = create new one.
  • Side-effect free — methods return new VOs, don't modify self
  • Can contain other VOs
  • Can reference Entities (but not the reverse being the norm)
  • Often numerous — design them for sharing, copying, flyweight
```

### When Is It a Value Object?

```
"Do I care WHICH one I have, or only WHAT it is?"
  Care about which → Entity
  Care about what  → Value Object

Examples:
  Money($50)         → VO (any $50 is as good as another)
  Address            → VO (usually — describes where, not tracked independently)
  Color(255, 0, 0)   → VO
  DateRange           → VO
  GPS Coordinate      → VO
  Temperature         → VO
  Email("a@b.com")    → VO

But: Address in a postal service app → might be Entity (each address has a life cycle)
```

### Template

```python
from dataclasses import dataclass


@dataclass(frozen=True)  # frozen=True → immutable
class Money:
    amount: float
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: float) -> "Money":
        return Money(round(self.amount * factor, 2), self.currency)


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str


price = Money(100.00, "USD")
tax = price.multiply(0.08)
total = price.add(tax)

a1 = Address("123 Main", "NYC", "NY", "10001", "US")
a2 = Address("123 Main", "NYC", "NY", "10001", "US")
assert a1 == a2    # Same attributes → equal (interchangeable)
assert a1 is not a2  # Different instances, but that doesn't matter
```

### Entity vs Value Object Cheatsheet

| Aspect | Entity | Value Object |
|---|---|---|
| Defined by | Identity | Attributes |
| Equality | Same ID | Same attributes |
| Mutability | Mutable | Immutable |
| Life cycle | Born, lives, dies | Created, used, discarded |
| Example | `Customer(id="C1")` | `Money(100, "USD")` |
| Sharing | Never (each is unique) | Freely (interchangeable) |
| Storage | Own row/document | Embedded in Entity or own table |

---

## 8. Domain Services

Operations that don't naturally belong to any Entity or Value Object. They represent **verbs** (actions) in the domain, not **nouns**.

```
Three characteristics of a Domain Service:
  1. The operation relates to a domain concept that isn't a natural part of an Entity or VO
  2. The interface is defined in terms of domain model elements
  3. The operation is stateless

Naming: Use verbs/actions — TransferFunds, CalculateRoute, ValidateOrder
NOT: FundsManager, RouteHelper (those are code smells)
```

### Three Kinds of Services

```
Layer             Example                    What it does
─────────────     ────────────────────────    ──────────────────────────────
Domain Service    FundsTransferService        Business rules for transferring money
Application Svc   TransferFundsAppService     Coordinates: parse input → call domain → notify
Infrastructure    EmailNotificationService    Sends actual email (no business meaning)
```

### Template

```python
from abc import ABC, abstractmethod


class PricingService:
    """Domain Service — encapsulates pricing rules that span multiple Entities."""

    def __init__(self, tax_calculator: "TaxCalculator", discount_repo: "DiscountRepository"):
        self._tax = tax_calculator
        self._discounts = discount_repo

    def calculate_order_total(self, order: "Order") -> Money:
        subtotal = Money(0, "USD")
        for item in order.items:
            subtotal = subtotal.add(item.line_total)

        discount = self._discounts.find_applicable(order.customer_id)
        if discount:
            subtotal = subtotal.multiply(1 - discount.percentage)

        tax = self._tax.calculate(subtotal, order.shipping_address)
        return subtotal.add(tax)


class FundsTransferService:
    """Domain Service — operation that involves two Accounts (neither should own it)."""

    def transfer(self, source: "Account", target: "Account", amount: Money):
        if source.balance.amount < amount.amount:
            raise InsufficientFundsError(source.id, amount)
        source.debit(amount)
        target.credit(amount)
```

### When NOT to Use a Service

```
If the behavior naturally belongs to an Entity or VO, PUT IT THERE.

BAD:  OrderValidationService.validate(order)   ← Order should validate itself
GOOD: order.validate()

BAD:  MoneyCalculator.add(m1, m2)              ← Money should know how to add
GOOD: m1.add(m2)

Only extract to a Service when the operation:
  • Spans multiple Aggregates
  • Doesn't belong to any single Entity
  • Represents a domain process (transfer, route, match)
```

---

## 9. Modules (Packages)

Modules are chapters in the story your model tells. They should reflect domain concepts, not technical categories.

```
BAD (grouped by pattern):
  entities/
    customer.py, order.py, product.py
  value_objects/
    money.py, address.py
  services/
    pricing.py, shipping.py
  repositories/
    customer_repo.py, order_repo.py

GOOD (grouped by domain concept):
  ordering/
    order.py, order_item.py, order_repo.py, pricing_service.py
  shipping/
    shipment.py, carrier.py, tracking_service.py
  billing/
    invoice.py, payment.py, billing_service.py
  customer/
    customer.py, customer_repo.py

Rule: Module names should be part of the Ubiquitous Language.
"Let's talk about the ordering module" makes sense to business experts.
"Let's talk about the entities package" does NOT.
```

---

## 10. Aggregates

The most critical tactical pattern. An Aggregate is a **cluster of Entities and Value Objects** treated as a single unit for data changes.

```
Key concepts:
  • Every Aggregate has exactly ONE root Entity (the Aggregate Root)
  • The root is the ONLY entry point — outside objects hold references ONLY to the root
  • The root controls all access and enforces invariants
  • Objects inside the boundary can reference each other freely
  • Objects inside can reference OTHER Aggregate roots
  • Delete the root → delete EVERYTHING inside the boundary
  • All invariants within the boundary must be consistent after each transaction
  • Cross-Aggregate consistency is EVENTUAL (not immediate)
```

### Rules for Aggregates

```
1. Reference other Aggregates by ID only (not direct object reference)
2. One transaction = one Aggregate
3. Keep Aggregates SMALL (prefer fewer Entities inside)
4. Design based on invariants, not data structure
5. Don't model Aggregates based on UI or reports
```

### Template

```python
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderItem:
    """Entity inside the Aggregate — has local identity only."""
    item_id: str
    product_id: str     # reference to another Aggregate by ID
    product_name: str
    quantity: int
    unit_price: Money

    @property
    def line_total(self) -> Money:
        return self.unit_price.multiply(self.quantity)


class Order:
    """Aggregate Root — controls all access and invariants."""
    MAX_ITEMS = 50

    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id          # Aggregate Root identity
        self.customer_id = customer_id    # reference to Customer Aggregate by ID
        self._items: list[OrderItem] = []
        self._status = "DRAFT"
        self._created_at = datetime.utcnow()
        self._events: list = []

    @property
    def items(self) -> tuple[OrderItem, ...]:
        return tuple(self._items)

    @property
    def total(self) -> Money:
        result = Money(0, "USD")
        for item in self._items:
            result = result.add(item.line_total)
        return result

    def add_item(self, product_id: str, name: str, qty: int, price: Money):
        if self._status != "DRAFT":
            raise InvalidOperationError("Cannot modify a placed order")
        if len(self._items) >= self.MAX_ITEMS:
            raise BusinessRuleViolation("Order cannot exceed 50 items")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        item = OrderItem(
            item_id=str(uuid4()),
            product_id=product_id,
            product_name=name,
            quantity=qty,
            unit_price=price,
        )
        self._items.append(item)

    def remove_item(self, item_id: str):
        if self._status != "DRAFT":
            raise InvalidOperationError("Cannot modify a placed order")
        self._items = [i for i in self._items if i.item_id != item_id]

    def place(self):
        """Transition to PLACED — enforces invariant: must have items."""
        if not self._items:
            raise BusinessRuleViolation("Cannot place an empty order")
        self._status = "PLACED"
        self._events.append(OrderPlaced(self.order_id, self.customer_id, self.total))

    def cancel(self):
        if self._status not in ("DRAFT", "PLACED"):
            raise InvalidOperationError(f"Cannot cancel order in {self._status} state")
        self._status = "CANCELLED"

    def collect_events(self) -> list:
        events = self._events.copy()
        self._events.clear()
        return events
```

### Aggregate Design: Purchase Order Example (from the book)

Evans' key example: A Purchase Order (PO) has Line Items. The invariant is that the sum of Line Item prices must not exceed the PO's approval limit.

```
Problem: If Line Items are in their own Aggregate, two users can simultaneously
add items that individually are fine but together violate the limit.

Solution: PO and its Line Items are ONE Aggregate.
  The PO (root) enforces the invariant on every change.

But: Parts (products) referenced by Line Items are in SEPARATE Aggregates.
  Their prices are COPIED into the Line Item at creation time.
  A Part price change does NOT automatically update existing POs.
  (Eventual consistency — a nightly job flags outdated prices.)
```

```
  ┌── Order Aggregate ────────────────┐
  │                                   │
  │  Order (Root)                     │
  │    │                              │
  │    ├── OrderItem (local Entity)   │
  │    ├── OrderItem                  │
  │    └── ShippingAddress (VO)       │
  │                                   │
  └───────────────────────────────────┘
         │ references by ID
         ▼
  ┌── Product Aggregate ──┐   ┌── Customer Aggregate ──┐
  │  Product (Root)       │   │  Customer (Root)        │
  │    └── Price (VO)     │   │    └── Address (VO)     │
  └───────────────────────┘   └─────────────────────────┘
```

---

## 11. Factories

Encapsulate complex object creation. A Factory's job is to produce a valid Aggregate in one atomic operation.

```
Use a Factory when:
  • Construction is complex (multiple objects, rules, wiring)
  • You want to hide the concrete class (polymorphism)
  • Creating an Aggregate requires enforcing invariants across multiple objects
  • You need to reconstitute objects from storage (deserialization)

Don't use a Factory when:
  • Construction is simple (just use __init__)
  • The class is concrete and not part of a hierarchy
  • All attributes are straightforward
```

### Types of Factories

```
1. Factory Method on Aggregate Root — root creates internal objects
2. Factory Method on related Entity — spawns another Aggregate
3. Standalone Factory (class) — creates entire Aggregate from scratch
```

### Template

```python
class OrderFactory:
    """Standalone Factory — creates a complete, valid Order Aggregate."""

    @staticmethod
    def create_new(customer_id: str, items: list[dict]) -> Order:
        order = Order(
            order_id=str(uuid4()),
            customer_id=customer_id,
        )
        for item in items:
            order.add_item(
                product_id=item["product_id"],
                name=item["name"],
                qty=item["quantity"],
                price=Money(item["price"], "USD"),
            )
        return order

    @staticmethod
    def reconstitute(data: dict) -> Order:
        """Reconstitute from storage — does NOT generate new ID."""
        order = Order(
            order_id=data["order_id"],
            customer_id=data["customer_id"],
        )
        order._status = data["status"]
        order._created_at = data["created_at"]
        for item_data in data["items"]:
            order._items.append(OrderItem(
                item_id=item_data["item_id"],
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_price=Money(item_data["unit_price"], item_data["currency"]),
            ))
        return order


class BrokerageAccount:
    """Factory Method on Entity — spawns another Aggregate."""

    def create_trade_order(self, stock: str, qty: int, order_type: str) -> "TradeOrder":
        if not self.is_active:
            raise AccountInactiveError(self.account_id)
        return TradeOrder(
            order_id=str(uuid4()),
            account_id=self.account_id,
            stock_symbol=stock,
            quantity=qty,
            order_type=order_type,
        )
```

### Factory vs Reconstitution

```
Creation (new object):
  • Generates new identity
  • Enforces ALL invariants or rejects
  • Returns brand new Aggregate

Reconstitution (from storage):
  • Uses EXISTING identity from data
  • Must handle violations gracefully (data may be legacy)
  • Restores mid-life-cycle object — it's the "same" conceptual entity
```

---

## 12. Repositories

Provide the illusion of an in-memory collection of Aggregates. The client thinks it's just getting objects from a collection — the Repository hides all persistence details.

```
Rules:
  • One Repository per Aggregate Root (NOT per Entity or VO)
  • Interface defined in the Domain layer (abstract class)
  • Implementation lives in the Infrastructure layer
  • Returns fully reconstituted Aggregate Roots
  • Client code is the same whether data is in SQL, Mongo, or memory
  • Leave transaction control to the client (don't commit inside Repository)
```

### Template

```python
from abc import ABC, abstractmethod


class OrderRepository(ABC):
    """Domain layer — defines the interface only."""

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def find_by_customer(self, customer_id: str) -> list[Order]: ...

    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def delete(self, order: Order) -> None: ...

    @abstractmethod
    def next_id(self) -> str: ...


class SqlOrderRepository(OrderRepository):
    """Infrastructure layer — implements persistence."""

    def __init__(self, session):
        self._session = session

    def find_by_id(self, order_id: str) -> Order | None:
        row = self._session.execute(
            "SELECT * FROM orders WHERE order_id = :id", {"id": order_id}
        ).fetchone()
        if not row:
            return None
        items = self._session.execute(
            "SELECT * FROM order_items WHERE order_id = :id", {"id": order_id}
        ).fetchall()
        return OrderFactory.reconstitute({"order_id": row.order_id, ...})

    def save(self, order: Order) -> None:
        self._session.execute("INSERT INTO orders ...", {...})
        for item in order.items:
            self._session.execute("INSERT INTO order_items ...", {...})

    def next_id(self) -> str:
        return str(uuid4())


class InMemoryOrderRepository(OrderRepository):
    """For testing — no database needed."""

    def __init__(self):
        self._store: dict[str, Order] = {}

    def find_by_id(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    def find_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._store.values() if o.customer_id == customer_id]

    def save(self, order: Order) -> None:
        self._store[order.order_id] = order

    def delete(self, order: Order) -> None:
        self._store.pop(order.order_id, None)

    def next_id(self) -> str:
        return str(uuid4())
```

### Repository vs Factory

```
Factory   → creates NEW objects or reconstitutes from raw data
Repository → finds EXISTING objects (manages middle + end of life cycle)

  Factory creates      →  Repository stores
  Client requests new  →  Client finds existing
  One-time operation   →  Ongoing retrieval

  A Repository may DELEGATE reconstitution to a Factory internally.
```

---

## 13. Domain Events

Something that happened in the domain that domain experts care about. Not in Evans' original book but universally adopted as a DDD building block.

```
Key traits:
  • Named in past tense (OrderPlaced, PaymentReceived, ItemShipped)
  • Immutable — describes something that already happened
  • Contains all information needed by subscribers
  • Used for cross-Aggregate communication (eventual consistency)
  • Part of the Ubiquitous Language
```

### Template

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str
    customer_id: str
    total: Money


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    order_id: str
    amount: Money
    payment_method: str


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    order_id: str
    tracking_number: str
    carrier: str


class Order:
    """Aggregate root collects events; Application layer publishes them."""

    def place(self):
        if not self._items:
            raise BusinessRuleViolation("Cannot place empty order")
        self._status = "PLACED"
        self._events.append(OrderPlaced(
            occurred_at=datetime.utcnow(),
            order_id=self.order_id,
            customer_id=self.customer_id,
            total=self.total,
        ))

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events


class PlaceOrderUseCase:
    """Application layer publishes events after persisting."""

    def execute(self, cmd):
        order = OrderFactory.create_new(cmd.customer_id, cmd.items)
        order.place()
        self._order_repo.save(order)
        for event in order.collect_events():
            self._event_bus.publish(event)
```

---

## 14. Specification Pattern

Encapsulates a business rule as an object that can be combined with other rules and reused.

```
Use when:
  • Business rules for selection/filtering/validation are complex
  • Rules need to be combined (AND, OR, NOT)
  • Same rule is used in multiple places (validation + querying)
```

### Template

```python
from abc import ABC, abstractmethod


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool: ...

    def and_(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def not_(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self._spec = spec

    def is_satisfied_by(self, candidate) -> bool:
        return not self._spec.is_satisfied_by(candidate)


class DeliverySpecification(Specification):
    """From Evans' cargo shipping example."""

    def __init__(self, destination: str, arrival_deadline: datetime):
        self.destination = destination
        self.arrival_deadline = arrival_deadline

    def is_satisfied_by(self, itinerary: "Itinerary") -> bool:
        return (
            itinerary.final_destination == self.destination
            and itinerary.estimated_arrival <= self.arrival_deadline
        )


class HighValueCustomerSpec(Specification):
    def is_satisfied_by(self, customer) -> bool:
        return customer.total_purchases > 10000 and customer.account_age_days > 365


class HasValidPaymentSpec(Specification):
    def is_satisfied_by(self, customer) -> bool:
        return customer.payment_method is not None and customer.payment_method.is_valid


eligible = HighValueCustomerSpec().and_(HasValidPaymentSpec())
vip_customers = [c for c in customers if eligible.is_satisfied_by(c)]
```

---

## 15. Strategy / Policy Pattern

In DDD, a **Policy** is the domain-specific name for the Strategy pattern. It expresses a business rule that can vary.

```python
from abc import ABC, abstractmethod


class RoutingPolicy(ABC):
    """Policy = Strategy. Business rule that governs route selection."""

    @abstractmethod
    def leg_magnitude(self, leg: "Leg") -> float: ...


class CheapestRoutePolicy(RoutingPolicy):
    def leg_magnitude(self, leg: "Leg") -> float:
        return leg.cost


class FastestRoutePolicy(RoutingPolicy):
    def leg_magnitude(self, leg: "Leg") -> float:
        return leg.transit_time_hours


class BalancedRoutePolicy(RoutingPolicy):
    def __init__(self, cost_weight: float = 0.5):
        self._cost_weight = cost_weight

    def leg_magnitude(self, leg: "Leg") -> float:
        return (self._cost_weight * leg.cost) + ((1 - self._cost_weight) * leg.transit_time_hours)


class RoutingService:
    """Domain Service using a Policy."""

    def find_itinerary(self, spec: "RouteSpecification", policy: RoutingPolicy) -> "Itinerary":
        candidates = self._generate_routes(spec)
        return min(candidates, key=lambda route: sum(policy.leg_magnitude(leg) for leg in route.legs))
```

---

## 16. Bounded Context

The most important strategic DDD pattern. A **Bounded Context** is a boundary within which a particular model is defined and applicable.

```
Core idea:
  Different parts of a large system have DIFFERENT models.
  "Customer" in Sales is not the same as "Customer" in Shipping.
  That's OK. Each has its own Bounded Context.

  Within a context: one model, one Ubiquitous Language, full consistency.
  Across contexts: translation, eventual consistency, explicit mapping.
```

### Why?

```
In a large system, trying to have ONE unified model:
  • Becomes bloated (god objects)
  • Creates confusion (same term means different things)
  • Creates coupling (a change in billing breaks shipping)
  • Slows all teams down (everyone waits on everyone)

Solution: Explicit boundaries. Each context owns its model.
```

### Examples

```
E-Commerce Platform:

  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
  │   Catalog BC     │  │   Ordering BC    │  │   Shipping BC    │
  │                  │  │                  │  │                  │
  │  Product         │  │  Order           │  │  Shipment        │
  │  Category        │  │  OrderItem       │  │  Package         │
  │  Price           │  │  Customer (ref)  │  │  Address         │
  │  Description     │  │  Payment         │  │  TrackingNumber  │
  └─────────────────┘  └─────────────────┘  └─────────────────┘

  "Product" in Catalog = name, description, images, categories, SEO
  "Product" in Ordering = product_id, name, price (snapshot at order time)
  "Product" in Shipping = product_id, weight, dimensions

  Same real-world thing, THREE different models. Each perfect for its context.
```

### One Team, One Bounded Context

```
General rule: One team per Bounded Context.
  One team CAN maintain multiple contexts.
  Multiple teams should NOT share one context (leads to model corruption).
```

---

## 17. Context Map

A visual map of all Bounded Contexts and the relationships between them. It shows how models translate across boundaries.

```
Purpose:
  • See the big picture at a glance
  • Make integration points explicit
  • Identify where translation (mapping) is needed
  • Understand power dynamics between teams
```

### Relationship Patterns

```
Pattern                      Description                                  Power Dynamic
─────────────────────       ──────────────────────────────────────       ─────────────────
Shared Kernel               Two BCs share a subset of the model          Equal partnership
Customer-Supplier           Downstream needs drive upstream changes       Negotiated
Conformist                  Downstream conforms to upstream model         Upstream dictates
Anti-Corruption Layer       Downstream translates to protect its model    Downstream independent
Open Host Service           Upstream offers a stable protocol/API         Upstream serves many
Published Language          Shared language (e.g., JSON schema, XML)      Standard
Separate Ways               No integration at all                         Fully independent
Big Ball of Mud             No boundaries (legacy mess)                   Chaos
```

### Visual Example

```
  ┌──────────┐    Customer/Supplier    ┌──────────┐
  │ Ordering │ ◄────────────────────── │ Catalog  │
  │   (DS)   │                         │   (US)   │
  └────┬─────┘                         └──────────┘
       │
       │  Anti-Corruption Layer
       │
  ┌────▼─────┐   Conformist   ┌──────────────┐
  │ Billing  │ ◄───────────── │ Payment GW   │
  │          │                │ (external)   │
  └──────────┘                └──────────────┘

  DS = Downstream, US = Upstream
```

---

## 18. Anti-Corruption Layer

A translation layer that protects your model from being contaminated by an external or legacy system's model.

```
When to use:
  • Integrating with a legacy system
  • Integrating with a third-party API whose model is alien to yours
  • Two teams with very different models
  • When you do NOT want to conform to the upstream model
```

### Template

```python
from dataclasses import dataclass


@dataclass
class LegacyCustomerDTO:
    """What the legacy system gives us — ugly, flat, inconsistent."""
    CUST_NUM: str
    FNAME: str
    LNAME: str
    ADDR1: str
    ADDR2: str
    CITY: str
    ST: str
    ZIP: str
    CUST_TYPE: int   # 1=individual, 2=corporate — magic number


@dataclass(frozen=True)
class Address:
    """Our clean Value Object."""
    street: str
    city: str
    state: str
    zip_code: str


class Customer:
    """Our clean Entity."""
    def __init__(self, customer_id: str, name: str, address: Address, is_corporate: bool):
        self.id = customer_id
        self.name = name
        self.address = address
        self.is_corporate = is_corporate


class CustomerAntiCorruptionLayer:
    """Translates between the legacy model and our domain model."""

    def __init__(self, legacy_api):
        self._legacy = legacy_api

    def find_customer(self, customer_id: str) -> Customer | None:
        dto = self._legacy.get_customer(customer_id)
        if dto is None:
            return None
        return self._translate(dto)

    def _translate(self, dto: LegacyCustomerDTO) -> Customer:
        return Customer(
            customer_id=dto.CUST_NUM,
            name=f"{dto.FNAME} {dto.LNAME}".strip(),
            address=Address(
                street=f"{dto.ADDR1} {dto.ADDR2}".strip(),
                city=dto.CITY,
                state=dto.ST,
                zip_code=dto.ZIP,
            ),
            is_corporate=(dto.CUST_TYPE == 2),
        )
```

### ACL Components

```
Anti-Corruption Layer typically consists of:

  1. Facade    — simplified interface for the external system
  2. Adapter   — translates between protocols
  3. Translator — maps between models (the core)

  Your Code  →  ACL (Facade + Translator)  →  External System
                     ↑
              Your model stays clean.
              External model's mess stays outside.
```

---

## 19. Shared Kernel

Two Bounded Contexts share a small subset of the model. Both teams must agree on any changes to the shared part.

```
When to use:
  • Two contexts have significant overlap
  • Teams can coordinate closely
  • The shared part is small and stable

Risks:
  • Any change to the kernel requires coordination
  • Needs shared test suite
  • Can slow both teams down if the kernel is too large

Rule of thumb: Keep the Shared Kernel as SMALL as possible.
```

```python
class Money:
    """Shared Kernel — used by both Ordering and Billing contexts.
    Changes require agreement from both teams + shared test suite."""
    ...

class CustomerId:
    """Shared Kernel — both contexts use the same customer identity."""
    def __init__(self, value: str):
        if not value.startswith("CUST-"):
            raise ValueError("Invalid customer ID format")
        self.value = value
```

---

## 20. Customer-Supplier

Upstream (supplier) serves downstream (customer). The downstream team's needs influence the upstream team's priorities.

```
How it works:
  • Downstream team communicates requirements to upstream
  • Upstream team plans work to satisfy downstream needs
  • Both teams agree on automated acceptance tests
  • Upstream publishes a versioned API

Example:
  Catalog Service (upstream) supplies product data
  Ordering Service (downstream) consumes it
  Ordering team tells Catalog team: "We need product weight for shipping calculations"
  Catalog team adds weight to their API in the next sprint
```

---

## 21. Conformist

Downstream team gives up and adopts the upstream model as-is. No translation.

```
When:
  • Upstream team has no motivation to accommodate you
  • The upstream model is "good enough"
  • Building an ACL would cost more than just conforming
  • You have no political power to influence upstream

Example:
  Your app integrates with Stripe's API.
  You model your Payment entity to match Stripe's concepts
  (PaymentIntent, Charge, Refund) because fighting it isn't worth it.
```

---

## 22. Open Host Service & Published Language

**Open Host Service**: The upstream system provides a well-defined, stable protocol (API) for all consumers.

**Published Language**: A shared, documented language (e.g., JSON schema, XML, Protobuf) for exchanging data.

```
Example:
  Your Payment Service exposes a REST API (Open Host Service)
  using a documented JSON schema (Published Language)
  that any downstream context can integrate with.

  POST /payments
  {
    "order_id": "ORD-123",
    "amount": { "value": 99.99, "currency": "USD" },
    "method": "CREDIT_CARD",
    "card_token": "tok_abc123"
  }
```

---

## 23. Separate Ways

Two Bounded Contexts have no integration. Each operates completely independently.

```
When:
  • The cost of integration exceeds its benefits
  • The contexts serve fundamentally different purposes
  • Teams are in different organizations or geographies
  • Some duplication of effort is acceptable

Trade-off: Duplicated data/logic vs. zero coordination overhead.
```

---

## 24. Supple Design

A set of principles from Evans for making the domain model easy to work with over time.

### Intention-Revealing Interfaces

```python
class Account:
    def debit(self, amount: Money): ...        # clear intent
    def credit(self, amount: Money): ...       # clear intent
    def update_balance(self, amount, type): ... # BAD: not intention-revealing
```

### Side-Effect-Free Functions

```python
@dataclass(frozen=True)
class Money:
    def add(self, other: "Money") -> "Money":
        """Returns NEW Money, does NOT modify self."""
        return Money(self.amount + other.amount, self.currency)
```

### Assertions

```python
class Account:
    def debit(self, amount: Money):
        """Post-condition: balance decreases by exactly 'amount'."""
        new_balance = self.balance.subtract(amount)
        if new_balance.amount < 0:
            raise InsufficientFunds()
        self.balance = new_balance
```

### Conceptual Contours

```
Break the model along natural seams in the domain.
If two concepts change for different reasons → separate them.
If two concepts always change together → keep them together.
```

### Standalone Classes

```
A class should be understandable without needing to look at other classes.
Minimize dependencies. The fewer collaborators, the easier to understand and test.
```

### Closure of Operations

```python
@dataclass(frozen=True)
class Money:
    """Operations on Money return Money — closed under the operation."""
    def add(self, other: "Money") -> "Money": ...
    def multiply(self, factor: float) -> "Money": ...
```

---

## 25. Distillation — Core Domain

Not all parts of the domain are equally important. Identify the **Core Domain** — the thing that gives your business its competitive advantage — and invest your best talent there.

```
Categories:
  Core Domain      — THE differentiator. Where the best developers work.
                     Custom-built. Highest investment.
  Supporting Domain — Necessary but not differentiating. Can outsource or buy.
  Generic Domain   — Solved problems. Use off-the-shelf (auth, payments, email).

Example (Ride-sharing):
  Core: Matching algorithm, surge pricing, ETA prediction
  Supporting: Driver onboarding, vehicle management
  Generic: Auth, payments, notifications, mapping (Google Maps API)
```

### Distillation Techniques

```
1. Domain Vision Statement — one-page description of Core Domain's value
2. Highlighted Core — mark the core elements in the model
3. Cohesive Mechanisms — extract complex algorithms into their own modules
4. Segregated Core — physically separate core from supporting code
5. Abstract Core — extract the essential concepts into a separate module
```

---

## 26. Large-Scale Structure

Optional patterns for organizing very large systems.

### Evolving Order

```
Don't impose a rigid structure up front.
Let the structure emerge and evolve as understanding deepens.
```

### Responsibility Layers

```
Common layers for enterprise systems:

  Decision Support  — planning, analysis, what-if scenarios
  Policy            — business rules and goals
  Operations        — what is actually happening
  Capability        — what could we do (resources, assets)

Each layer depends only on layers below it.
```

---

## 27. Full Example: E-Commerce System

### Context Map

```
  ┌────────────┐  Open Host   ┌────────────┐
  │  Catalog   │ ────────────►│  Ordering   │
  │  Context   │  (Product    │  Context    │
  │            │   events)    │            │
  └────────────┘              └─────┬──────┘
                                    │ Domain Events
                              ┌─────▼──────┐
                              │  Billing   │
                              │  Context   │
                              └─────┬──────┘
                                    │ ACL
                              ┌─────▼──────┐
                              │  Stripe    │
                              │ (external) │
                              └────────────┘
```

### Ordering Context — Full Implementation

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4


# ─── Value Objects ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "USD"

    def add(self, other: Money) -> Money:
        assert self.currency == other.currency
        return Money(round(self.amount + other.amount, 2), self.currency)

    def multiply(self, factor: float) -> Money:
        return Money(round(self.amount * factor, 2), self.currency)


@dataclass(frozen=True)
class ShippingAddress:
    recipient: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str


@dataclass(frozen=True)
class ProductSnapshot:
    """Snapshot of product data at order time — decoupled from Catalog context."""
    product_id: str
    name: str
    unit_price: Money


# ─── Domain Events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str
    customer_id: str
    total: Money

@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: str
    reason: str


# ─── Entities & Aggregate ────────────────────────────────────────────────────

class OrderStatus(Enum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderItem:
    """Entity with local identity inside the Order Aggregate."""
    item_id: str
    product: ProductSnapshot
    quantity: int

    @property
    def line_total(self) -> Money:
        return self.product.unit_price.multiply(self.quantity)


class Order:
    """Aggregate Root for the Ordering context."""

    def __init__(self, order_id: str, customer_id: str, shipping: ShippingAddress):
        self.order_id = order_id
        self.customer_id = customer_id
        self.shipping = shipping
        self._items: list[OrderItem] = []
        self._status = OrderStatus.DRAFT
        self._placed_at: datetime | None = None
        self._events: list[DomainEvent] = []

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def items(self) -> tuple[OrderItem, ...]:
        return tuple(self._items)

    @property
    def subtotal(self) -> Money:
        total = Money(0)
        for item in self._items:
            total = total.add(item.line_total)
        return total

    def add_item(self, product: ProductSnapshot, quantity: int):
        if self._status != OrderStatus.DRAFT:
            raise Exception("Cannot modify a placed order")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        existing = next((i for i in self._items if i.product.product_id == product.product_id), None)
        if existing:
            self._items.remove(existing)
            quantity += existing.quantity
        self._items.append(OrderItem(item_id=str(uuid4()), product=product, quantity=quantity))

    def place(self):
        if not self._items:
            raise Exception("Cannot place an empty order")
        self._status = OrderStatus.PLACED
        self._placed_at = datetime.utcnow()
        self._events.append(OrderPlaced(
            occurred_at=self._placed_at,
            order_id=self.order_id,
            customer_id=self.customer_id,
            total=self.subtotal,
        ))

    def mark_paid(self):
        if self._status != OrderStatus.PLACED:
            raise Exception(f"Cannot pay order in {self._status.value} state")
        self._status = OrderStatus.PAID

    def cancel(self, reason: str):
        if self._status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise Exception("Cannot cancel shipped/delivered order")
        self._status = OrderStatus.CANCELLED
        self._events.append(OrderCancelled(
            occurred_at=datetime.utcnow(),
            order_id=self.order_id,
            reason=reason,
        ))

    def collect_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def __eq__(self, other):
        return isinstance(other, Order) and self.order_id == other.order_id

    def __hash__(self):
        return hash(self.order_id)


# ─── Repository Interface (Domain Layer) ─────────────────────────────────────

class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None: ...
    @abstractmethod
    def save(self, order: Order) -> None: ...


# ─── Domain Service ──────────────────────────────────────────────────────────

class OrderPricingService:
    def __init__(self, tax_rate: float = 0.08):
        self._tax_rate = tax_rate

    def calculate_total(self, order: Order) -> Money:
        subtotal = order.subtotal
        tax = subtotal.multiply(self._tax_rate)
        return subtotal.add(tax)


# ─── Application Layer (Use Case) ────────────────────────────────────────────

class PlaceOrderUseCase:
    def __init__(self, repo: OrderRepository, pricing: OrderPricingService, event_bus):
        self._repo = repo
        self._pricing = pricing
        self._bus = event_bus

    def execute(self, customer_id: str, items: list[dict], address: dict) -> str:
        shipping = ShippingAddress(**address)
        order = Order(order_id=str(uuid4()), customer_id=customer_id, shipping=shipping)
        for item in items:
            product = ProductSnapshot(
                product_id=item["product_id"],
                name=item["name"],
                unit_price=Money(item["price"]),
            )
            order.add_item(product, item["quantity"])
        order.place()
        self._repo.save(order)
        for event in order.collect_events():
            self._bus.publish(event)
        return order.order_id
```

---

## 28. Full Example: Ride-Sharing System

### Bounded Contexts

```
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │   Rider BC   │    │  Matching BC │    │  Driver BC   │
  │              │───►│  (CORE)      │◄───│              │
  │  RideRequest │    │  TripMatch   │    │  Driver      │
  │  Rider       │    │  Pricing     │    │  Vehicle     │
  │  Payment     │    │  SurgePolicy │    │  Availability│
  └──────────────┘    └──────┬───────┘    └──────────────┘
                             │
                      ┌──────▼───────┐
                      │   Trip BC    │
                      │              │
                      │  Trip (AR)   │
                      │  Route       │
                      │  Fare        │
                      └──────────────┘
```

### Matching Context (Core Domain)

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import radians, sin, cos, sqrt, atan2


# ─── Value Objects ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float

    def distance_km(self, other: GeoPoint) -> float:
        R = 6371
        dlat = radians(other.lat - self.lat)
        dlng = radians(other.lng - self.lng)
        a = sin(dlat/2)**2 + cos(radians(self.lat)) * cos(radians(other.lat)) * sin(dlng/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))


@dataclass(frozen=True)
class Fare:
    base: float
    per_km: float
    per_minute: float
    surge_multiplier: float = 1.0

    def calculate(self, distance_km: float, duration_minutes: float) -> Money:
        raw = self.base + (self.per_km * distance_km) + (self.per_minute * duration_minutes)
        return Money(round(raw * self.surge_multiplier, 2))


@dataclass(frozen=True)
class RideRequest:
    request_id: str
    rider_id: str
    pickup: GeoPoint
    dropoff: GeoPoint
    requested_at: datetime
    vehicle_type: str


# ─── Policies (Strategies) ───────────────────────────────────────────────────

class SurgePolicy:
    """Policy pattern — determines surge pricing multiplier."""

    def __init__(self, demand_threshold: int = 10, supply_threshold: int = 5):
        self._demand_threshold = demand_threshold
        self._supply_threshold = supply_threshold

    def calculate_multiplier(self, active_requests: int, available_drivers: int) -> float:
        if available_drivers == 0:
            return 3.0
        ratio = active_requests / available_drivers
        if ratio > 3:
            return 2.5
        elif ratio > 2:
            return 1.8
        elif ratio > 1.5:
            return 1.3
        return 1.0


class DriverMatchingPolicy:
    """Policy for selecting the best driver for a ride request."""

    MAX_PICKUP_DISTANCE_KM = 10.0

    def find_best_match(
        self,
        request: RideRequest,
        available_drivers: list[DriverAvailability],
    ) -> DriverAvailability | None:
        candidates = [
            d for d in available_drivers
            if d.vehicle_type == request.vehicle_type
            and d.location.distance_km(request.pickup) <= self.MAX_PICKUP_DISTANCE_KM
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda d: d.location.distance_km(request.pickup))


@dataclass(frozen=True)
class DriverAvailability:
    driver_id: str
    location: GeoPoint
    vehicle_type: str
    rating: float


# ─── Domain Service ──────────────────────────────────────────────────────────

class RideMatchingService:
    """Core Domain Service — the competitive advantage."""

    def __init__(self, matching_policy: DriverMatchingPolicy, surge_policy: SurgePolicy):
        self._matching = matching_policy
        self._surge = surge_policy

    def match(
        self,
        request: RideRequest,
        available_drivers: list[DriverAvailability],
        active_requests_count: int,
    ) -> MatchResult | None:
        driver = self._matching.find_best_match(request, available_drivers)
        if not driver:
            return None
        surge = self._surge.calculate_multiplier(active_requests_count, len(available_drivers))
        pickup_distance = driver.location.distance_km(request.pickup)
        return MatchResult(
            request_id=request.request_id,
            driver_id=driver.driver_id,
            pickup_distance_km=pickup_distance,
            surge_multiplier=surge,
            estimated_pickup_minutes=pickup_distance * 2,
        )


@dataclass(frozen=True)
class MatchResult:
    request_id: str
    driver_id: str
    pickup_distance_km: float
    surge_multiplier: float
    estimated_pickup_minutes: float
```

### Trip Aggregate (Trip Context)

```python
class TripStatus(Enum):
    MATCHED = "MATCHED"
    DRIVER_EN_ROUTE = "DRIVER_EN_ROUTE"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Trip:
    """Aggregate Root — tracks the lifecycle of a ride."""

    def __init__(self, trip_id: str, rider_id: str, driver_id: str,
                 pickup: GeoPoint, dropoff: GeoPoint, fare: Fare):
        self.trip_id = trip_id
        self.rider_id = rider_id
        self.driver_id = driver_id
        self.pickup = pickup
        self.dropoff = dropoff
        self.fare = fare
        self._status = TripStatus.MATCHED
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._actual_route: list[GeoPoint] = []
        self._events: list[DomainEvent] = []

    def driver_arrived(self):
        self._assert_status(TripStatus.DRIVER_EN_ROUTE)
        self._status = TripStatus.ARRIVED

    def start(self):
        self._assert_status(TripStatus.ARRIVED)
        self._status = TripStatus.IN_PROGRESS
        self._started_at = datetime.utcnow()

    def complete(self, actual_distance_km: float, duration_minutes: float):
        self._assert_status(TripStatus.IN_PROGRESS)
        self._status = TripStatus.COMPLETED
        self._completed_at = datetime.utcnow()
        total_fare = self.fare.calculate(actual_distance_km, duration_minutes)
        self._events.append(TripCompleted(
            occurred_at=self._completed_at,
            trip_id=self.trip_id,
            rider_id=self.rider_id,
            driver_id=self.driver_id,
            total_fare=total_fare,
        ))

    def cancel(self, cancelled_by: str, reason: str):
        if self._status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            raise Exception(f"Cannot cancel trip in {self._status.value} state")
        self._status = TripStatus.CANCELLED

    def _assert_status(self, expected: TripStatus):
        if self._status != expected:
            raise Exception(f"Expected {expected.value}, got {self._status.value}")

    def collect_events(self) -> list:
        events = list(self._events)
        self._events.clear()
        return events


@dataclass(frozen=True)
class TripCompleted(DomainEvent):
    trip_id: str
    rider_id: str
    driver_id: str
    total_fare: Money
```

---

## 29. DDD Decision Cheatsheet

### "Is it an Entity or Value Object?"

```
Q: Does it have a unique identity that matters?           → Entity
Q: Are two instances with same attributes interchangeable? → Value Object
Q: Does it have a lifecycle (created, modified, deleted)?  → Entity
Q: Is it immutable once created?                          → Value Object
```

### "Where should this logic go?"

```
Q: Does it naturally belong to one Entity/VO?             → Put it there
Q: Does it span multiple Aggregates?                      → Domain Service
Q: Is it a coordination/workflow step?                    → Application Service
Q: Is it purely technical (email, DB, file)?              → Infrastructure Service
```

### "How should I draw Aggregate boundaries?"

```
1. Start with invariants — what must be consistent in a single transaction?
2. Include the minimum number of objects to enforce those invariants
3. Prefer SMALL Aggregates (1 root + a few VOs is ideal)
4. Reference other Aggregates by ID, not direct object reference
5. One transaction = one Aggregate (cross-Aggregate = eventual consistency)
```

### "Do I need a Repository?"

```
Only for Aggregate Roots. Never for internal Entities or Value Objects.
Q: Does external code need to look up this object by itself?  → Repository
Q: Is it always reached by traversing from another object?    → No repository needed
```

### "When do I need an Anti-Corruption Layer?"

```
Q: Am I integrating with a system whose model is significantly different? → ACL
Q: Would conforming to their model corrupt my clean domain model?        → ACL
Q: Is it a third-party API I can't influence?                            → ACL
Q: Is the upstream model close enough that conforming is OK?             → Conformist (no ACL)
```

### Tactical Patterns Summary

```
┌─────────────────┬──────────────────────────────────────────────────┐
│ Pattern         │ One-Line Summary                                │
├─────────────────┼──────────────────────────────────────────────────┤
│ Entity          │ Has identity. Tracked through lifecycle.         │
│ Value Object    │ No identity. Immutable. Defined by attributes.   │
│ Aggregate       │ Consistency boundary. One root. Transactional.   │
│ Repository      │ Illusion of in-memory collection of Aggregates. │
│ Factory         │ Complex creation logic. Returns valid Aggregate. │
│ Domain Service  │ Stateless operation spanning multiple objects.   │
│ Domain Event    │ Something that happened. Past tense. Immutable.  │
│ Specification   │ Business rule as object. Composable.             │
│ Policy/Strategy │ Varying business rule. Pluggable.                │
│ Module          │ Domain-concept-based package structure.          │
└─────────────────┴──────────────────────────────────────────────────┘
```

### Strategic Patterns Summary

```
┌──────────────────────┬───────────────────────────────────────────────────┐
│ Pattern              │ One-Line Summary                                  │
├──────────────────────┼───────────────────────────────────────────────────┤
│ Bounded Context      │ Boundary where one model + language applies.      │
│ Ubiquitous Language  │ Shared vocabulary in code, speech, and docs.      │
│ Context Map          │ Visual map of all BCs and their relationships.    │
│ Shared Kernel        │ Small shared model subset. Both teams coordinate. │
│ Customer-Supplier    │ Upstream serves downstream. Negotiated priority.  │
│ Conformist           │ Downstream adopts upstream model as-is.           │
│ Anti-Corruption Layer│ Translation layer protecting your model.          │
│ Open Host Service    │ Stable, well-defined API for all consumers.       │
│ Published Language   │ Shared schema/format (JSON, Protobuf, XML).       │
│ Separate Ways        │ No integration. Fully independent.                │
│ Core Domain          │ The competitive differentiator. Invest here.      │
│ Distillation         │ Separate core from supporting/generic.            │
└──────────────────────┴───────────────────────────────────────────────────┘
```

---

*Based on "Domain-Driven Design: Tackling Complexity in the Heart of Software" by Eric Evans (2003). Distilled with examples for engineers who want the substance without the 560 pages.*
