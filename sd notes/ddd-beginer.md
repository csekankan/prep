# Domain-Driven Design — A Beginner's Guide

**Based on:** *Domain-Driven Design: Tackling Complexity in the Heart of Software* by Eric Evans (2003)  
**Audience:** Developers new to DDD who want to understand the core ideas and see how they shape real API design.

---

## 1. What Is Domain-Driven Design?

DDD is an approach to building software that says: **start from the business problem, not the database**.

Most projects start with tables, frameworks, or a tech stack. DDD flips that — you talk to the people who understand the business, learn their language, and let that language drive your code, your APIs, and your architecture.

**Why bother?**

- Code stays understandable to non-engineers (PMs, domain experts).
- Changes to business rules don't require rewriting half the system.
- Teams can work independently because boundaries are clear.

**One sentence:** DDD is about **modeling the real world accurately in code** and **drawing clear lines** between different parts of the business.

---

## 2. The Building Blocks (with examples)

We'll use a running example: **an online bookstore** — customers browse, order books, and the store manages inventory, shipping, and payments.

---

### 2.1 Ubiquitous Language

**What it is:** A shared vocabulary that developers and business people use consistently — in conversations, in code, in APIs, in docs.

**Why it matters:** When the PM says "Order" and the developer's code says `PurchaseTransaction`, every conversation requires mental translation. Bugs hide in that gap.

**Example:**

Bad — the code ignores business language:

```python
class PurchaseTransaction:
    def __init__(self, tx_id, item_refs, total_amt):
        self.tx_id = tx_id
        self.item_refs = item_refs
        self.total_amt = total_amt
```

Good — the code mirrors how the business talks:

```python
class Order:
    def __init__(self, order_id, line_items, total_price):
        self.order_id = order_id
        self.line_items = line_items
        self.total_price = total_price
```

**Rule:** If you can't explain your class name to a PM without saying "well, technically it means…" — rename it.

---

### 2.2 Entities

**What it is:** An object that has a **unique identity** that persists over time. Two entities with the same data but different IDs are **different things**.

**Example:** A `Customer` is an entity. Even if two customers share the same name, they are different people with different accounts.

```python
class Customer:
    def __init__(self, customer_id: str, name: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email

    def __eq__(self, other):
        return self.customer_id == other.customer_id
```

**API:**

```
GET /customers/cust-42
→ { "customerId": "cust-42", "name": "Alice", "email": "alice@example.com" }
```

The identity (`cust-42`) is what matters — Alice can change her name or email and she's still the same customer.

---

### 2.3 Value Objects

**What it is:** An object defined entirely by its **attributes**, not by an ID. Two value objects with the same data are considered equal. They are usually **immutable** — you don't change them, you replace them.

**Example:** A `Money` value object — $10 USD is $10 USD regardless of "which" ten dollars it is.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

price_a = Money(29.99, "USD")
price_b = Money(29.99, "USD")
assert price_a == price_b  # True — same value, same thing
```

**Another example:** A shipping `Address` is a value object. You don't track "address #47" — you care about the street, city, and zip code together.

```python
@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str
```

**Why not just use raw strings?** Because `Money("ten", "dollars")` would compile but make no sense. Value objects let you attach validation and meaning.

---

### 2.4 Aggregates and Aggregate Roots

**What it is:** A cluster of related objects treated as **one unit** for changes. The **aggregate root** is the single entry point — you never reach inside and modify a child object directly.

**Why:** Aggregates protect **invariants** (rules that must always be true). If you let anyone modify any piece independently, rules get broken.

**Example:** An `Order` aggregate with `OrderLine` items inside it.

```python
class OrderLine:
    def __init__(self, book_id: str, title: str, quantity: int, unit_price: Money):
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self.book_id = book_id
        self.title = title
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def line_total(self) -> Money:
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


class Order:
    """Aggregate root — all changes to the order go through here."""

    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.lines: list[OrderLine] = []
        self.status = "draft"

    def add_line(self, book_id: str, title: str, quantity: int, unit_price: Money):
        if self.status != "draft":
            raise Exception("Cannot modify a submitted order")
        self.lines.append(OrderLine(book_id, title, quantity, unit_price))

    def submit(self):
        if not self.lines:
            raise Exception("Cannot submit an empty order")
        self.status = "submitted"

    @property
    def total(self) -> Money:
        currency = self.lines[0].unit_price.currency if self.lines else "USD"
        return Money(sum(line.line_total.amount for line in self.lines), currency)
```

**Key rules (invariants) enforced here:**

- You can't add items to a submitted order.
- You can't submit an empty order.
- Quantity must be at least 1.

**API reflecting the aggregate:**

```
POST /orders
→ { "orderId": "ord-101", "customerId": "cust-42", "status": "draft" }

POST /orders/ord-101/lines
Body: { "bookId": "book-7", "title": "DDD by Eric Evans", "quantity": 1, "unitPrice": 59.99 }

POST /orders/ord-101/submit
→ { "orderId": "ord-101", "status": "submitted", "total": 59.99 }
```

Notice: you interact with the **Order** (the root), not with order lines directly. The Order decides what's allowed.

---

### 2.5 Repositories

**What it is:** An abstraction that lets you **load and save** aggregates without your domain code knowing about databases, SQL, or ORMs.

**Think of it as:** A collection-like interface. You ask for an Order, you get an Order. You save an Order, it's persisted. How? The domain doesn't care.

```python
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: str) -> Order:
        ...

    @abstractmethod
    def save(self, order: Order) -> None:
        ...


class PostgresOrderRepository(OrderRepository):
    def __init__(self, db_connection):
        self.db = db_connection

    def find_by_id(self, order_id: str) -> Order:
        row = self.db.query("SELECT ... FROM orders WHERE id = %s", order_id)
        return self._to_domain(row)

    def save(self, order: Order) -> None:
        self.db.execute("INSERT INTO orders ...", self._to_row(order))

    def _to_domain(self, row):
        ...  # map DB row → Order object

    def _to_row(self, order):
        ...  # map Order object → DB row
```

**Why this matters:** If you later switch from Postgres to DynamoDB, you write a new repository implementation. Your domain logic (Order, OrderLine, rules) doesn't change at all.

---

### 2.6 Domain Services

**What it is:** Logic that doesn't naturally belong to any single entity or value object. It operates across multiple objects or involves external coordination.

**Example:** Checking whether a book is in stock before confirming an order involves both the Order and Inventory — it doesn't belong inside either one.

```python
class OrderFulfillmentService:
    def __init__(self, order_repo: OrderRepository, inventory_client):
        self.order_repo = order_repo
        self.inventory = inventory_client

    def submit_order(self, order_id: str):
        order = self.order_repo.find_by_id(order_id)

        for line in order.lines:
            if not self.inventory.is_available(line.book_id, line.quantity):
                raise Exception(f"Book {line.book_id} is out of stock")

        order.submit()
        self.order_repo.save(order)
```

**Not a domain service:** A "service" class that just wraps getters and setters with no real logic. That's anemic — avoid it.

---

### 2.7 Domain Events

**What it is:** A record that **something meaningful happened** in the domain. Events use past tense because they describe facts that already occurred.

**Examples:**

- `OrderSubmitted` — not `SubmitOrder` (that's a command)
- `PaymentReceived`
- `BookShipped`

```python
@dataclass
class OrderSubmitted:
    order_id: str
    customer_id: str
    total: Money
    submitted_at: str
```

**Why events matter:**

- Other parts of the system can **react** without being tightly coupled. The order service doesn't need to know about emails, analytics, or warehouse picking.
- They make the system's behavior **visible** and **auditable**.

**Event-driven API flow:**

```
1. Customer submits order
   POST /orders/ord-101/submit → 200 OK

2. System publishes event:
   Event: OrderSubmitted { orderId: "ord-101", total: 59.99 }

3. Subscribers react independently:
   - Email service → sends confirmation
   - Warehouse service → starts picking
   - Analytics service → records conversion
```

---

### 2.8 Factories

**What it is:** Encapsulate complex object creation. When constructing an aggregate requires multiple steps, validations, or defaults, put that logic in a factory rather than a bloated constructor.

```python
class OrderFactory:
    @staticmethod
    def create_from_cart(cart, customer_id: str) -> Order:
        order = Order(
            order_id=generate_id(),
            customer_id=customer_id
        )
        for item in cart.items:
            order.add_line(
                book_id=item.book_id,
                title=item.title,
                quantity=item.quantity,
                unit_price=item.price
            )
        return order
```

---

## 3. Bounded Contexts — The Most Important Strategic Concept

### 3.1 The Problem

In a small app, one "Order" model works fine. But as the business grows, different departments start meaning different things by the same word:

| Who | What "Order" means to them |
|-----|---------------------------|
| **Checkout** | A customer's purchase commitment — items, prices, discounts |
| **Warehouse** | A pick list — which shelves, which boxes, partial shipments |
| **Payments** | A charge authorization — amounts, retries, refund eligibility |
| **Support** | A case reference — complaints, returns, goodwill credits |

If you force all of these into **one Order class**, it becomes a 2000-line monster that no single team can safely change.

### 3.2 The Solution: Bounded Contexts

A **bounded context** draws a line around one consistent model. Inside that line, every term has exactly one meaning. Outside, the same English word might mean something else — and that's fine.

```
┌─────────────────────┐     ┌─────────────────────┐
│   Checkout Context   │     │  Warehouse Context   │
│                      │     │                      │
│  Order = customer    │     │  Shipment = physical │
│  commitment with     │────▶│  pick and pack       │
│  prices & discounts  │     │  instructions        │
│                      │     │                      │
└─────────────────────┘     └─────────────────────┘
         │
         │ OrderPlaced event
         ▼
┌─────────────────────┐
│  Payments Context    │
│                      │
│  PaymentRequest =    │
│  auth + capture      │
│  against an order    │
└─────────────────────┘
```

### 3.3 Bounded Context APIs

Each context exposes its **own** API using **its own** language:

**Checkout context:**

```
POST /checkout/orders
Body: {
  "customerId": "cust-42",
  "lines": [
    { "bookId": "book-7", "quantity": 1 }
  ],
  "promoCode": "SAVE10"
}
→ 201 Created
{
  "orderId": "ord-101",
  "status": "placed",
  "total": { "amount": 53.99, "currency": "USD" }
}
```

**Warehouse context** (reacts to the OrderPlaced event, has its own model):

```
GET /warehouse/shipments?orderId=ord-101
→ {
  "shipmentId": "shp-500",
  "orderId": "ord-101",
  "status": "picking",
  "lines": [
    { "bookId": "book-7", "binLocation": "A3-12", "quantity": 1 }
  ]
}
```

**Payments context:**

```
POST /payments/charges
Body: {
  "orderId": "ord-101",
  "amount": { "amount": 53.99, "currency": "USD" },
  "paymentMethod": "card-xyz"
}
→ { "chargeId": "chg-200", "status": "authorized" }
```

Notice: each context owns **different nouns** (Order vs Shipment vs Charge), even though they all relate to the same customer purchase. They link to each other through **IDs** (`orderId`), not by sharing one giant model.

---

## 4. Context Mapping — How Bounded Contexts Talk to Each Other

Contexts are not islands. They need to exchange information. DDD defines several relationship patterns:

### 4.1 Anti-Corruption Layer (ACL)

**When:** You integrate with an external or legacy system whose model doesn't match yours.

**What:** A translation layer at the boundary that converts foreign concepts into your domain's language.

**Example:** Your bookstore integrates with a third-party supplier API that uses completely different field names.

```python
class SupplierBookData:
    """What the external supplier API returns — their language."""
    def __init__(self, sku, desc, list_price_cents, avail_qty):
        self.sku = sku
        self.desc = desc
        self.list_price_cents = list_price_cents
        self.avail_qty = avail_qty


class SupplierACL:
    """Translates supplier language → our Catalog language."""

    def __init__(self, supplier_client):
        self.client = supplier_client

    def get_book(self, book_id: str):
        raw = self.client.fetch_item(book_id)
        return Book(
            book_id=raw.sku,
            title=raw.desc,
            price=Money(raw.list_price_cents / 100, "USD"),
            stock=raw.avail_qty
        )
```

Without an ACL, the supplier's weird field names (`desc`, `list_price_cents`) would leak into your domain code.

### 4.2 Open Host Service / Published Language

**When:** Your context is consumed by many other contexts.

**What:** You publish a well-defined, versioned API (the open host) and a clear schema/contract (the published language) so consumers have a stable integration point.

**Example:** The Catalog context publishes a stable API for other contexts:

```
GET /catalog/books/{bookId}
→ {
  "bookId": "book-7",
  "title": "Domain-Driven Design",
  "author": "Eric Evans",
  "price": { "amount": 59.99, "currency": "USD" },
  "availability": "in_stock"
}
```

Checkout, recommendations, and search all consume this API. The Catalog team commits to not breaking it (versioning, backward-compatible changes).

### 4.3 Shared Kernel

**When:** Two closely collaborating teams share a small piece of the model.

**What:** A small, explicitly agreed-upon set of code or schemas that both teams own together. Changes require both teams to agree.

**Example:** Both the Checkout and Warehouse contexts share the `Money` value object and `BookId` type — explicitly, in a shared library.

**Warning:** Keep the shared kernel **small**. If it grows, you're building a monolith disguised as two services.

### 4.4 Customer–Supplier

**When:** One context (upstream/supplier) produces data another context (downstream/customer) needs.

**What:** The upstream team considers the downstream team's needs when evolving the API.

**Example:** Catalog (upstream) and Checkout (downstream). Checkout needs book prices and availability. The Catalog team includes Checkout's requirements in their roadmap.

---

## 5. Putting It All Together — Full API Design Example

Let's design a bookstore system using DDD principles, showing how each context has its own model and API.

### 5.1 Identify the Bounded Contexts

| Context | Owns | Key Nouns |
|---------|------|-----------|
| **Catalog** | Book definitions, pricing, categories | Book, Author, Category, Price |
| **Inventory** | Stock levels, warehouse locations | StockItem, Warehouse, Reorder |
| **Ordering** | Customer orders, checkout flow | Order, OrderLine, Cart |
| **Payments** | Charges, refunds | Charge, Refund, PaymentMethod |
| **Shipping** | Deliveries, tracking | Shipment, TrackingNumber, Carrier |

### 5.2 API for Each Context

#### Catalog Context

```
# Browse and search books
GET    /catalog/books?author=evans&category=software
GET    /catalog/books/{bookId}

# Admin: manage catalog (different audience, could be a separate sub-API)
POST   /catalog/books
PATCH  /catalog/books/{bookId}
```

Response:

```json
{
  "bookId": "book-7",
  "title": "Domain-Driven Design",
  "author": { "name": "Eric Evans" },
  "category": "Software Engineering",
  "price": { "amount": 59.99, "currency": "USD" },
  "publishedYear": 2003
}
```

#### Ordering Context

```
# Cart management
POST   /ordering/carts
POST   /ordering/carts/{cartId}/items
DELETE /ordering/carts/{cartId}/items/{itemId}

# Place order from cart
POST   /ordering/orders
GET    /ordering/orders/{orderId}

# Business-meaningful action, not generic PATCH
POST   /ordering/orders/{orderId}/cancel
```

Create order from cart:

```
POST /ordering/orders
Body: {
  "cartId": "cart-88",
  "customerId": "cust-42",
  "shippingAddress": {
    "street": "123 Main St",
    "city": "Portland",
    "state": "OR",
    "zipCode": "97201",
    "country": "US"
  }
}
→ 201 Created
{
  "orderId": "ord-101",
  "status": "placed",
  "lines": [
    {
      "bookId": "book-7",
      "title": "Domain-Driven Design",
      "quantity": 1,
      "unitPrice": { "amount": 59.99, "currency": "USD" }
    }
  ],
  "total": { "amount": 59.99, "currency": "USD" },
  "placedAt": "2026-04-12T10:30:00Z"
}
```

Notice `POST /orders/{id}/cancel` — not `PATCH /orders/{id} { "status": "cancelled" }`. Cancellation is a business action with rules (refund eligibility, warehouse notification), not a field update.

#### Inventory Context

```
GET  /inventory/stock/{bookId}
POST /inventory/stock/{bookId}/receive    # books arrived from supplier
POST /inventory/stock/{bookId}/reserve    # hold stock for an order
POST /inventory/stock/{bookId}/release    # release a reservation
```

```json
{
  "bookId": "book-7",
  "available": 42,
  "reserved": 3,
  "warehouseId": "wh-portland"
}
```

#### Payments Context

```
POST /payments/charges
POST /payments/charges/{chargeId}/capture
POST /payments/charges/{chargeId}/refund
GET  /payments/charges/{chargeId}
```

#### Shipping Context

```
POST /shipping/shipments
GET  /shipping/shipments/{shipmentId}
GET  /shipping/shipments/{shipmentId}/tracking
POST /shipping/shipments/{shipmentId}/mark-dispatched
```

### 5.3 How They Connect (Events)

```
Ordering emits:   OrderPlaced    → Inventory reserves stock
                                 → Payments creates a charge
                                 → Shipping prepares a shipment

Payments emits:   PaymentCaptured → Shipping dispatches
                  PaymentFailed   → Ordering marks order failed
                                  → Inventory releases reservation

Shipping emits:   ShipmentDelivered → Ordering marks order complete
```

Each context **reacts** to events — it doesn't call into another context's internals.

---

## 6. Layered Architecture — Where DDD Code Lives

DDD recommends separating your code into layers:

```
┌──────────────────────────────────────────┐
│              Interface Layer             │  ← API controllers, request/response
├──────────────────────────────────────────┤
│            Application Layer             │  ← Use cases, orchestration, no business rules
├──────────────────────────────────────────┤
│              Domain Layer                │  ← Entities, value objects, aggregates,
│                                          │     domain services, events — THE CORE
├──────────────────────────────────────────┤
│          Infrastructure Layer            │  ← Database, message queues, external APIs
└──────────────────────────────────────────┘
```

**Example folder structure for the Ordering context:**

```
ordering/
├── api/                    # Interface layer
│   ├── order_routes.py
│   └── schemas.py          # Request/response shapes
├── application/            # Application layer
│   ├── place_order.py      # Use case: orchestrates domain + infra
│   └── cancel_order.py
├── domain/                 # Domain layer (no imports from infra!)
│   ├── order.py            # Order aggregate
│   ├── order_line.py       # OrderLine entity
│   ├── money.py            # Money value object
│   ├── events.py           # OrderPlaced, OrderCancelled
│   └── order_repository.py # Abstract repository interface
└── infrastructure/         # Infrastructure layer
    ├── postgres_order_repo.py
    └── event_publisher.py
```

The critical rule: **the domain layer depends on nothing else**. It doesn't import Flask, SQLAlchemy, or Kafka. Everything flows inward.

---

## 7. Common Mistakes Beginners Make

### 7.1 Anemic Domain Model

**What it looks like:** Entities are just data holders (getters/setters). All logic lives in "service" classes.

```python
# BAD: anemic — Order is just a data bag
class Order:
    def __init__(self):
        self.status = "draft"
        self.lines = []

class OrderService:
    def submit(self, order):
        if len(order.lines) == 0:
            raise Exception("Empty")
        order.status = "submitted"
```

```python
# GOOD: rich domain model — Order enforces its own rules
class Order:
    def submit(self):
        if not self.lines:
            raise Exception("Cannot submit an empty order")
        self.status = "submitted"
```

### 7.2 One Model for Everything

Using a single `Order` class across checkout, warehouse, and payments. It becomes a 50-field monster that no one understands. Use bounded contexts — each gets its own model.

### 7.3 CRUD APIs Disguised as DDD

```
# BAD: generic CRUD — no business meaning
PATCH /orders/ord-101
Body: { "status": "cancelled" }

# GOOD: intention-revealing — business action with rules
POST /orders/ord-101/cancel
Body: { "reason": "changed_mind" }
```

The second version can enforce rules: Is the order eligible for cancellation? Should a refund be triggered? The first version just blindly updates a field.

### 7.4 Giant Aggregates

If your aggregate has 15 entities inside it, it's probably too big. Large aggregates mean:

- Slow saves (lots of data to lock and write).
- High contention (many users touching the same aggregate).
- Unclear ownership.

**Rule of thumb:** An aggregate should be as small as possible while still protecting its invariants.

---

## 8. When to Use DDD (and When Not To)

### Use DDD when:

- The business logic is **complex** (not just CRUD).
- Multiple teams work on the same system.
- The domain has **rich rules** that change over time.
- Getting the model wrong is **expensive** (financial, safety, legal).

### Skip full DDD when:

- It's a simple CRUD app with no real business rules.
- One small team, short-lived project.
- The "domain" is just storing and retrieving data.

Even in simple projects, two ideas from DDD are always worth applying:

1. **Use the business's language in your code.**
2. **Don't let one word mean two things.**

---

## 9. Quick Reference — DDD Vocabulary

| Term | Plain English | Example |
|------|--------------|---------|
| **Ubiquitous Language** | Shared vocabulary between devs and business | "Order" means the same thing in code, docs, and meetings |
| **Entity** | Object with a unique identity | Customer, Order |
| **Value Object** | Object defined by its attributes, no ID | Money, Address |
| **Aggregate** | Cluster of objects updated as one unit | Order + its OrderLines |
| **Aggregate Root** | The single entry point to an aggregate | Order (you go through Order to change OrderLines) |
| **Repository** | Abstraction for loading/saving aggregates | OrderRepository |
| **Domain Event** | Record of something that happened | OrderPlaced, PaymentReceived |
| **Domain Service** | Logic spanning multiple aggregates | OrderFulfillmentService |
| **Factory** | Encapsulates complex object creation | OrderFactory.create_from_cart() |
| **Bounded Context** | Boundary where one model is consistent | Checkout context vs Warehouse context |
| **Context Map** | How bounded contexts relate to each other | Checkout is upstream to Payments |
| **Anti-Corruption Layer** | Translator protecting your model from external models | SupplierACL converts supplier data to your Book model |
| **Subdomain** | A slice of the overall business problem | Core (ordering), Supporting (notifications), Generic (auth) |

---

## 10. Further Reading

- **Eric Evans** — *Domain-Driven Design: Tackling Complexity in the Heart of Software* (the original, dense but foundational)
- **Vaughn Vernon** — *Domain-Driven Design Distilled* (shorter, more accessible intro)
- **Vaughn Vernon** — *Implementing Domain-Driven Design* (practical companion to Evans)
- **Scott Millett & Nick Tune** — *Patterns, Principles, and Practices of Domain-Driven Design* (modern, example-heavy)

---

*This guide covers the essentials. For advanced topics like event sourcing, CQRS, saga patterns, and strategic design at organizational scale, see the staff engineer companion guide.*
