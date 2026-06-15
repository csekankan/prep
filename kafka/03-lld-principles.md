# LLD Principles — The Foundation of Great Design

> *"Any fool can write code that a computer can understand. Good programmers write code that humans can understand."* — Martin Fowler

Low-Level Design is not about memorizing patterns — it is about **internalizing principles** that guide every design decision you make. Patterns are solutions; principles are the *reasoning* behind those solutions. When you understand why a pattern exists, you can invent new ones on the fly during interviews and on the job.

This guide covers the ten foundational principles that every LLD practitioner must master. Each principle includes the formal definition, the reasoning behind it, concrete Python code examples (bad → good), interview tips, and common violations you will encounter in production codebases.

---

## Table of Contents

1. [SOLID Principles](#1-solid-principles)
   - [Single Responsibility Principle (SRP)](#s---single-responsibility-principle-srp)
   - [Open/Closed Principle (OCP)](#o---openclosed-principle-ocp)
   - [Liskov Substitution Principle (LSP)](#l---liskov-substitution-principle-lsp)
   - [Interface Segregation Principle (ISP)](#i---interface-segregation-principle-isp)
   - [Dependency Inversion Principle (DIP)](#d---dependency-inversion-principle-dip)
2. [DRY (Don't Repeat Yourself)](#2-dry-dont-repeat-yourself)
3. [KISS (Keep It Simple, Stupid)](#3-kiss-keep-it-simple-stupid)
4. [YAGNI (You Aren't Gonna Need It)](#4-yagni-you-arent-gonna-need-it)
5. [Composition over Inheritance](#5-composition-over-inheritance)
6. [Law of Demeter](#6-law-of-demeter-principle-of-least-knowledge)
7. [Separation of Concerns](#7-separation-of-concerns-soc)
8. [High Cohesion, Low Coupling](#8-high-cohesion-low-coupling)
9. [Design for Change](#9-design-for-change)
10. [Fail-Fast Principle](#10-fail-fast-principle)

---

## 1. SOLID Principles

SOLID is an acronym coined by Robert C. Martin (Uncle Bob) representing five principles that, when applied together, make software systems easier to maintain, extend, and reason about. They are not rules — they are guidelines that help you make trade-offs consciously.

---

### S — Single Responsibility Principle (SRP)

#### Definition

> *"A class should have one, and only one, reason to change."* — Robert C. Martin

A "reason to change" maps to a **stakeholder** or **actor** in the system. If two different people (or teams) could request changes that affect the same class, that class has more than one responsibility.

#### Why It Matters

- **Reduced blast radius**: When a class has one job, a bug fix or feature change is isolated. You do not accidentally break billing logic when modifying email templates.
- **Easier testing**: Single-responsibility classes have focused test suites. You test one behavior, not a tangled web.
- **Better naming**: If you struggle to name a class without using "And" or "Manager", it probably does too much.
- **Team scalability**: Two developers can work on two responsibilities without merge conflicts if those responsibilities live in separate classes.

#### BAD Example — A God Class

```python
import smtplib
import json
from datetime import datetime


class User:
    """Handles everything related to a user — a classic SRP violation."""

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.created_at = datetime.now()

    def save(self):
        """Persist user to the database."""
        # Direct database access — this class knows SQL
        query = f"INSERT INTO users (name, email) VALUES ('{self.name}', '{self.email}')"
        # execute query...
        print(f"Saved user {self.name} to database")

    def send_welcome_email(self):
        """Send a welcome email — this class knows SMTP details."""
        server = smtplib.SMTP("smtp.example.com", 587)
        server.starttls()
        server.login("admin@example.com", "password123")
        message = f"Subject: Welcome!\n\nHi {self.name}, welcome aboard!"
        server.sendmail("admin@example.com", self.email, message)
        server.quit()

    def to_json(self) -> str:
        """Serialize to JSON — this class knows serialization format."""
        return json.dumps({
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        })

    def validate(self) -> bool:
        """Validate user data — mixes validation with domain logic."""
        if "@" not in self.email:
            return False
        if len(self.name) < 2:
            return False
        return True

    def generate_report(self) -> str:
        """Generate an activity report — why does User know about reports?"""
        return f"Report for {self.name}: 0 activities"
```

**What is wrong**: This `User` class has **five reasons to change** — the DBA wants to switch databases, the DevOps team changes the mail provider, the API team changes the serialization format, validation rules evolve, and the analytics team changes report structure. Each change forces modifications to the same file.

#### GOOD Example — Separated Responsibilities

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


# --- Domain Entity: only holds user data and core business rules ---
@dataclass
class User:
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

    def is_valid(self) -> bool:
        """Intrinsic validation that is part of what it means to BE a user."""
        return "@" in self.email and len(self.name) >= 2


# --- Persistence: knows HOW to save, not WHAT a user is ---
class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def find_by_email(self, email: str) -> User | None: ...


class PostgresUserRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def save(self, user: User) -> None:
        print(f"INSERT INTO users ... (via {self.connection_string})")

    def find_by_email(self, email: str) -> User | None:
        print(f"SELECT * FROM users WHERE email = '{email}'")
        return None


# --- Notification: knows HOW to send messages ---
class NotificationService(Protocol):
    def send_welcome(self, user: User) -> None: ...


class EmailNotificationService:
    def __init__(self, smtp_host: str, smtp_port: int):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_welcome(self, user: User) -> None:
        print(f"Sending welcome email to {user.email} via {self.smtp_host}")


# --- Serialization: knows HOW to transform data formats ---
class UserSerializer:
    @staticmethod
    def to_json(user: User) -> dict:
        return {
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }


# --- Orchestrator: coordinates the workflow ---
class UserRegistrationService:
    def __init__(
        self,
        repository: UserRepository,
        notifier: NotificationService,
    ):
        self.repository = repository
        self.notifier = notifier

    def register(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        if not user.is_valid():
            raise ValueError(f"Invalid user data: {name}, {email}")
        self.repository.save(user)
        self.notifier.send_welcome(user)
        return user
```

Now each class has exactly **one reason to change**, and each can be tested, deployed, and modified independently.

#### How to Identify SRP Violations

| Smell | What It Means |
|---|---|
| Class name contains "And", "Or", "Manager", "Handler", "Processor" | Multiple responsibilities hiding behind a vague name |
| More than ~200 lines | Too much behavior in one place |
| Multiple unrelated `import` groups | Touching different subsystems (DB, HTTP, filesystem) |
| Tests require complex setup with many mocks | Class depends on too many external systems |
| Changes in one method break unrelated tests | Responsibilities are entangled |

#### Real LLD Application

In a **Parking Lot** system, a `ParkingLot` class should not also handle payment processing, ticket printing, and notification sending. Separate into `ParkingLot` (manages spots), `TicketService` (issues and validates tickets), `PaymentProcessor` (handles money), and `DisplayBoard` (shows availability).

> **Interview Tip**: When the interviewer says "design a class for X", resist the urge to put everything in one class. Immediately identify the actors (who causes change?) and separate accordingly. Saying *"I'm applying SRP here because the payment logic and the booking logic have different reasons to change"* signals senior thinking.

---

### O — Open/Closed Principle (OCP)

#### Definition

> *"Software entities should be open for extension, but closed for modification."* — Bertrand Meyer

You should be able to add new behavior **without changing existing, tested code**. The mechanism is abstraction — define a stable interface, and let new implementations plug in.

#### Why It Matters

- **Stability**: Existing code that works stays untouched. No regression risk.
- **Parallel development**: New features are new classes, not edits to old ones. Teams work independently.
- **Plugin architectures**: Think VS Code extensions, Django middleware, pytest plugins — all OCP at work.

#### BAD Example — Modification Required for Every New Type

```python
class DiscountCalculator:
    """Every new discount type requires editing this class."""

    def calculate(self, order_total: float, customer_type: str) -> float:
        if customer_type == "regular":
            return order_total * 0.05
        elif customer_type == "premium":
            return order_total * 0.10
        elif customer_type == "vip":
            return order_total * 0.15
        elif customer_type == "employee":
            return order_total * 0.25
        # Next month: "student" discount?
        # Next quarter: "seasonal" discount?
        # This if/elif chain grows forever...
        else:
            return 0.0
```

**What is wrong**: Every new discount type forces a modification to `DiscountCalculator`. This violates OCP because the class is **not closed for modification**. It also violates SRP — the calculator "knows" about every customer type.

#### GOOD Example — Strategy Pattern as OCP Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class DiscountStrategy(ABC):
    """Stable abstraction — closed for modification."""

    @abstractmethod
    def calculate(self, order_total: float) -> float: ...

    @abstractmethod
    def description(self) -> str: ...


class RegularDiscount(DiscountStrategy):
    def calculate(self, order_total: float) -> float:
        return order_total * 0.05

    def description(self) -> str:
        return "Regular customer: 5% off"


class PremiumDiscount(DiscountStrategy):
    def calculate(self, order_total: float) -> float:
        return order_total * 0.10

    def description(self) -> str:
        return "Premium customer: 10% off"


class VIPDiscount(DiscountStrategy):
    def calculate(self, order_total: float) -> float:
        return order_total * 0.15

    def description(self) -> str:
        return "VIP customer: 15% off"


class SeasonalDiscount(DiscountStrategy):
    """Added months later — zero changes to existing code."""

    def __init__(self, season_multiplier: float = 0.20):
        self.season_multiplier = season_multiplier

    def calculate(self, order_total: float) -> float:
        return order_total * self.season_multiplier

    def description(self) -> str:
        return f"Seasonal: {self.season_multiplier:.0%} off"


@dataclass
class Order:
    total: float
    discount_strategy: DiscountStrategy

    def final_price(self) -> float:
        discount = self.discount_strategy.calculate(self.total)
        return self.total - discount


# Usage — extending behavior without modifying any existing class
order = Order(total=100.0, discount_strategy=SeasonalDiscount(0.30))
print(f"Final: ${order.final_price():.2f}")  # Final: $70.00
```

#### Plugin Systems — OCP in Architecture

```python
from typing import Protocol


class PaymentGateway(Protocol):
    """Any new payment provider just implements this protocol."""

    def charge(self, amount: float, token: str) -> bool: ...
    def refund(self, transaction_id: str, amount: float) -> bool: ...


class StripeGateway:
    def charge(self, amount: float, token: str) -> bool:
        print(f"Stripe: charging ${amount:.2f}")
        return True

    def refund(self, transaction_id: str, amount: float) -> bool:
        print(f"Stripe: refunding ${amount:.2f} for {transaction_id}")
        return True


class PayPalGateway:
    def charge(self, amount: float, token: str) -> bool:
        print(f"PayPal: charging ${amount:.2f}")
        return True

    def refund(self, transaction_id: str, amount: float) -> bool:
        print(f"PayPal: refunding ${amount:.2f} for {transaction_id}")
        return True


class RazorpayGateway:
    """Added six months later — no changes to PaymentService."""

    def charge(self, amount: float, token: str) -> bool:
        print(f"Razorpay: charging ${amount:.2f}")
        return True

    def refund(self, transaction_id: str, amount: float) -> bool:
        print(f"Razorpay: refunding ${amount:.2f} for {transaction_id}")
        return True


class PaymentService:
    """Closed for modification — works with ANY gateway."""

    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    def process_payment(self, amount: float, token: str) -> bool:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return self.gateway.charge(amount, token)
```

#### Common Violations

| Violation | Fix |
|---|---|
| `if/elif` chains on a type field | Strategy or Registry pattern |
| `isinstance()` checks in business logic | Polymorphism — let the object decide |
| Hardcoded algorithm selection | Inject the algorithm as a dependency |
| Giant `switch` on an enum | Map enum values to strategy objects |

> **Interview Tip**: When you see an `if/elif` chain growing, say *"This violates OCP — I'll introduce a strategy interface so new types are new classes, not new branches."* This is one of the most impactful refactoring moves you can demonstrate.

---

### L — Liskov Substitution Principle (LSP)

#### Definition

> *"If S is a subtype of T, then objects of type T may be replaced with objects of type S without altering any of the desirable properties of the program."* — Barbara Liskov, 1987

In simpler terms: a subclass must be **perfectly substitutable** for its parent class. Code that works with the parent must work identically with any child — no surprises, no broken contracts.

#### The Formal Contract

LSP defines strict rules about what subclasses can and cannot do:

| Rule | Meaning |
|---|---|
| **Preconditions cannot be strengthened** | A subclass cannot demand MORE from callers than the parent does |
| **Postconditions cannot be weakened** | A subclass cannot promise LESS than the parent guarantees |
| **Invariants must be preserved** | Properties that are always true in the parent must remain true |
| **History constraint** | A subclass cannot introduce state changes the parent would not allow |

#### BAD Example — The Classic Rectangle/Square Violation

```python
class Rectangle:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value

    def area(self) -> float:
        return self._width * self._height


class Square(Rectangle):
    """Mathematically, a square IS-A rectangle. But in OOP, this breaks LSP."""

    def __init__(self, side: float):
        super().__init__(side, side)

    @Rectangle.width.setter
    def width(self, value: float) -> None:
        # VIOLATION: setting width also sets height — surprising side effect
        self._width = value
        self._height = value

    @Rectangle.height.setter
    def height(self, value: float) -> None:
        self._width = value
        self._height = value


def print_area_after_resize(rect: Rectangle) -> None:
    """This function has a reasonable expectation about Rectangle behavior."""
    rect.width = 5
    rect.height = 10
    # For a Rectangle, area should be 50
    # For a Square, area is 100 — the last setter wins!
    print(f"Expected area: 50, Actual area: {rect.area()}")


r = Rectangle(2, 3)
print_area_after_resize(r)  # Expected area: 50, Actual area: 50 ✓

s = Square(2)
print_area_after_resize(s)  # Expected area: 50, Actual area: 100 ✗ — LSP VIOLATED
```

**What is wrong**: `Square` changes the behavior of `width.setter` and `height.setter` in a way that surprises code written for `Rectangle`. The postcondition "setting width does not change height" is **broken** by the subclass.

#### GOOD Example — Separate Abstractions

```python
from abc import ABC, abstractmethod
import math


class Shape(ABC):
    """Common abstraction — no mutable dimension coupling."""

    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...


class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        if width <= 0 or height <= 0:
            raise ValueError("Dimensions must be positive")
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Square(Shape):
    """Square is NOT a subclass of Rectangle — it's a sibling under Shape."""

    def __init__(self, side: float):
        if side <= 0:
            raise ValueError("Side must be positive")
        self.side = side

    def area(self) -> float:
        return self.side ** 2

    def perimeter(self) -> float:
        return 4 * self.side


class Circle(Shape):
    def __init__(self, radius: float):
        if radius <= 0:
            raise ValueError("Radius must be positive")
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius


def total_area(shapes: list[Shape]) -> float:
    """Works with ANY shape — LSP is satisfied."""
    return sum(s.area() for s in shapes)


shapes = [Rectangle(5, 10), Square(7), Circle(3)]
print(f"Total area: {total_area(shapes):.2f}")  # Works perfectly
```

#### Python-Specific LSP Considerations

```python
from typing import Protocol


class Drawable(Protocol):
    def draw(self, canvas: "Canvas") -> None: ...


class Canvas:
    pass


class Button:
    def draw(self, canvas: Canvas) -> None:
        print("Drawing button")


class Icon:
    def draw(self, canvas: Canvas) -> None:
        print("Drawing icon")


class BrokenWidget:
    def draw(self, canvas: Canvas, color: str = "red") -> None:
        # EXTRA REQUIRED parameter (even with default) changes the signature
        # In strict typing this CAN work, but the intent is fragile
        print(f"Drawing in {color}")

    def draw_special(self) -> None:
        # This does NOT satisfy Drawable — different method name
        pass


def render_all(widgets: list[Drawable], canvas: Canvas) -> None:
    for w in widgets:
        w.draw(canvas)  # Every widget must honor this exact contract
```

**Key Python-specific LSP pitfalls**:

1. **Raising unexpected exceptions**: If the parent's `save()` raises `IOError`, the child should not raise `TypeError`.
2. **Returning different types**: If parent returns `list[str]`, child should not return `set[str]` or `None`.
3. **Side effects**: If parent is pure (no side effects), child should remain pure.
4. **Optional parameters becoming required**: Adding a required parameter in the override breaks callers.

#### Common Violations

| Violation | Description |
|---|---|
| Overriding a method to raise `NotImplementedError` | The child refuses to do what the parent promised |
| Strengthening preconditions | Child rejects inputs the parent accepted |
| Weakening postconditions | Child returns `None` where parent always returned a value |
| Changing side effects | Child writes to DB where parent only read |

> **Interview Tip**: If your subclass needs to override a method with `raise NotImplementedError`, that is an LSP violation. The interface promises behavior the subclass cannot deliver. Instead, rethink the hierarchy — often the parent interface is too broad (which leads us to ISP next).

---

### I — Interface Segregation Principle (ISP)

#### Definition

> *"No client should be forced to depend on methods it does not use."* — Robert C. Martin

If an interface has 10 methods but most implementers only need 3, the interface is too fat. Break it into smaller, focused interfaces (called **role interfaces**).

#### Why It Matters

- **Reduced implementation burden**: Implementers only need to write code they actually use.
- **Reduced recompilation**: Changing one method does not affect clients that don't use it.
- **Better mocking in tests**: Smaller interfaces are easier to stub.
- **Clearer contracts**: Each interface communicates a specific capability.

#### BAD Example — Fat Interface

```python
from abc import ABC, abstractmethod


class Worker(ABC):
    """Forces every worker to implement ALL methods — even irrelevant ones."""

    @abstractmethod
    def write_code(self) -> None: ...

    @abstractmethod
    def review_code(self) -> None: ...

    @abstractmethod
    def attend_meeting(self) -> None: ...

    @abstractmethod
    def manage_team(self) -> None: ...

    @abstractmethod
    def prepare_budget(self) -> None: ...

    @abstractmethod
    def design_architecture(self) -> None: ...


class JuniorDeveloper(Worker):
    def write_code(self) -> None:
        print("Writing code")

    def review_code(self) -> None:
        print("Reviewing code")

    def attend_meeting(self) -> None:
        print("Attending standup")

    def manage_team(self) -> None:
        # FORCED to implement this — but juniors don't manage teams!
        raise NotImplementedError("Juniors don't manage teams")

    def prepare_budget(self) -> None:
        raise NotImplementedError("Juniors don't prepare budgets")

    def design_architecture(self) -> None:
        raise NotImplementedError("Juniors don't design architecture")
```

**What is wrong**: `JuniorDeveloper` is forced to implement `manage_team()` and `prepare_budget()` — methods it will never use. The `NotImplementedError` stubs are a code smell that screams ISP violation (and LSP violation too).

#### GOOD Example — Focused Protocol Interfaces

```python
from typing import Protocol


class Coder(Protocol):
    def write_code(self) -> None: ...
    def review_code(self) -> None: ...


class MeetingAttendee(Protocol):
    def attend_meeting(self) -> None: ...


class TeamManager(Protocol):
    def manage_team(self) -> None: ...
    def prepare_budget(self) -> None: ...


class Architect(Protocol):
    def design_architecture(self) -> None: ...
    def review_code(self) -> None: ...


# --- Concrete Classes Only Implement What They Actually Do ---

class JuniorDeveloper:
    """Satisfies Coder and MeetingAttendee — nothing more."""

    def write_code(self) -> None:
        print("Writing code with enthusiasm")

    def review_code(self) -> None:
        print("Reviewing peer's code")

    def attend_meeting(self) -> None:
        print("Attending standup")


class SeniorDeveloper:
    """Satisfies Coder, MeetingAttendee, and Architect."""

    def write_code(self) -> None:
        print("Writing production code")

    def review_code(self) -> None:
        print("Thorough code review")

    def attend_meeting(self) -> None:
        print("Leading technical discussion")

    def design_architecture(self) -> None:
        print("Designing system architecture")


class EngineeringManager:
    """Satisfies TeamManager and MeetingAttendee — does not code."""

    def manage_team(self) -> None:
        print("Managing team")

    def prepare_budget(self) -> None:
        print("Preparing Q3 budget")

    def attend_meeting(self) -> None:
        print("Attending leadership meeting")


# --- Functions depend only on the capability they need ---

def run_sprint(coders: list[Coder]) -> None:
    for coder in coders:
        coder.write_code()


def hold_standup(attendees: list[MeetingAttendee]) -> None:
    for attendee in attendees:
        attendee.attend_meeting()


def plan_architecture(architects: list[Architect]) -> None:
    for architect in architects:
        architect.design_architecture()
```

#### Role Interfaces — A Practical Pattern

```python
from typing import Protocol


class Readable(Protocol):
    def read(self) -> bytes: ...


class Writable(Protocol):
    def write(self, data: bytes) -> int: ...


class Seekable(Protocol):
    def seek(self, position: int) -> None: ...
    def tell(self) -> int: ...


class Closeable(Protocol):
    def close(self) -> None: ...


# A file supports all four; a network socket supports read/write/close but not seek.
# A read-only memory buffer supports read/seek but not write.
# Each function asks for ONLY the capability it needs:

def copy_stream(source: Readable, destination: Writable) -> int:
    data = source.read()
    return destination.write(data)


def read_at_position(source: Readable & Seekable, position: int) -> bytes:
    source.seek(position)
    return source.read()
```

#### Common Violations

| Violation | Fix |
|---|---|
| Interface with 10+ methods | Split into role-based protocols |
| Implementers raising `NotImplementedError` | They should not implement that interface |
| Type hints requiring a fat base class | Use `Protocol` with only needed methods |
| "God interface" passed everywhere | Create purpose-specific interfaces per use case |

> **Interview Tip**: Python's `Protocol` (from `typing`) is your best friend for ISP. Unlike ABC, protocols use structural subtyping — a class satisfies a protocol if it has the right methods, no explicit inheritance needed. Mention this in interviews to show you understand Python's type system.

---

### D — Dependency Inversion Principle (DIP)

#### Definition

> *"High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions."* — Robert C. Martin

"High-level" means business logic (the *what*). "Low-level" means infrastructure (the *how* — databases, APIs, file systems). The principle says: **business logic should define the interface it needs, and infrastructure should conform to it** — not the other way around.

#### Why It Matters

- **Testability**: Swap a real database for an in-memory fake in tests — same interface.
- **Flexibility**: Switch from PostgreSQL to MongoDB without touching business logic.
- **Decoupling**: Business rules do not import infrastructure libraries.
- **Deployability**: Different environments (dev, staging, prod) use different implementations.

#### BAD Example — Direct Dependency on Low-Level Module

```python
import psycopg2  # Direct dependency on PostgreSQL driver


class OrderService:
    """High-level business logic directly depends on PostgreSQL."""

    def __init__(self):
        # Hardcoded connection — cannot swap for testing or different DB
        self.conn = psycopg2.connect(
            host="localhost", database="orders", user="admin", password="secret"
        )

    def place_order(self, user_id: int, items: list[dict]) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, status) VALUES (%s, 'pending') RETURNING id",
            (user_id,),
        )
        order_id = cursor.fetchone()[0]

        for item in items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, qty) VALUES (%s, %s, %s)",
                (order_id, item["product_id"], item["quantity"]),
            )

        # Hardcoded email sending
        self._send_confirmation_email(user_id, order_id)
        self.conn.commit()
        return order_id

    def _send_confirmation_email(self, user_id: int, order_id: int) -> None:
        print(f"Sending email for order {order_id} to user {user_id}")
```

**What is wrong**: `OrderService` directly imports and instantiates `psycopg2`. Testing requires a running PostgreSQL instance. Switching to MySQL means rewriting the service. The high-level module (business logic) depends on a low-level module (database driver).

#### GOOD Example — Dependency Inversion with Repository Pattern

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol
from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    product_id: int
    quantity: int
    unit_price: float


@dataclass
class Order:
    user_id: int
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    order_id: int | None = None

    @property
    def total(self) -> float:
        return sum(item.quantity * item.unit_price for item in self.items)


# --- Abstractions defined by the HIGH-LEVEL module ---

class OrderRepository(Protocol):
    """The business layer defines WHAT it needs from persistence."""

    def save(self, order: Order) -> int: ...
    def find_by_id(self, order_id: int) -> Order | None: ...
    def find_by_user(self, user_id: int) -> list[Order]: ...


class NotificationService(Protocol):
    """The business layer defines WHAT it needs from notifications."""

    def notify_order_placed(self, order: Order) -> None: ...


# --- High-level business logic depends ONLY on abstractions ---

class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        notifier: NotificationService,
    ):
        self.repository = repository
        self.notifier = notifier

    def place_order(self, user_id: int, items: list[OrderItem]) -> Order:
        order = Order(user_id=user_id, items=items)

        if not order.items:
            raise ValueError("Order must have at least one item")
        if order.total <= 0:
            raise ValueError("Order total must be positive")

        order.order_id = self.repository.save(order)
        order.status = OrderStatus.CONFIRMED
        self.notifier.notify_order_placed(order)
        return order


# --- Low-level implementations depend on abstractions ---

class PostgresOrderRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def save(self, order: Order) -> int:
        print(f"PostgreSQL: saving order for user {order.user_id}")
        return 1  # simulated ID

    def find_by_id(self, order_id: int) -> Order | None:
        print(f"PostgreSQL: finding order {order_id}")
        return None

    def find_by_user(self, user_id: int) -> list[Order]:
        print(f"PostgreSQL: finding orders for user {user_id}")
        return []


class InMemoryOrderRepository:
    """Used in tests — no database needed."""

    def __init__(self):
        self._orders: dict[int, Order] = {}
        self._next_id = 1

    def save(self, order: Order) -> int:
        order_id = self._next_id
        self._next_id += 1
        self._orders[order_id] = order
        return order_id

    def find_by_id(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def find_by_user(self, user_id: int) -> list[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]


class EmailNotifier:
    def notify_order_placed(self, order: Order) -> None:
        print(f"Email: Order #{order.order_id} confirmed, total ${order.total:.2f}")


class SMSNotifier:
    def notify_order_placed(self, order: Order) -> None:
        print(f"SMS: Your order #{order.order_id} is confirmed!")


# --- Composition Root: wire dependencies at the application boundary ---

def create_production_order_service() -> OrderService:
    return OrderService(
        repository=PostgresOrderRepository("postgresql://localhost/orders"),
        notifier=EmailNotifier(),
    )


def create_test_order_service() -> tuple[OrderService, InMemoryOrderRepository]:
    repo = InMemoryOrderRepository()
    service = OrderService(repository=repo, notifier=SMSNotifier())
    return service, repo
```

The dependency arrows now point **inward** — from infrastructure toward business logic, not the other way around.

#### Common Violations

| Violation | Fix |
|---|---|
| Importing `psycopg2` / `boto3` / `requests` in business logic | Define a Protocol; import the driver only in the implementation |
| Constructing dependencies inside the class (`self.db = Database()`) | Inject via constructor |
| Using singletons for infrastructure | Pass instances through the dependency graph |
| Business logic reading environment variables | Inject configuration as parameters |

> **Interview Tip**: Whenever you say *"I'll create a repository interface"* or *"I'll inject the notification service"*, you are applying DIP. State it explicitly: *"The business logic defines the contract via a Protocol, and the infrastructure implements it — this is Dependency Inversion."*

---

## 2. DRY (Don't Repeat Yourself)

### Definition

> *"Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."* — Andy Hunt & Dave Thomas, *The Pragmatic Programmer*

DRY is often misunderstood as "don't copy-paste code." It is actually about **knowledge** — if a business rule, algorithm, or data transformation is expressed in more than one place, it violates DRY.

### What Counts as Repetition

| Type of Repetition | Example | Fix |
|---|---|---|
| **Knowledge duplication** | Tax rate hardcoded in 3 places | Single constant or config |
| **Logic duplication** | Same validation in API handler AND service layer | Single validation function |
| **Structural duplication** | Same data mapping in serializer AND deserializer | Single schema definition |
| **Incidental similarity** | Two functions that happen to look alike but serve different domains | Leave them separate — they are not the same knowledge |

### BAD Example — Duplicated Knowledge

```python
class InvoiceService:
    def calculate_total(self, items: list[dict]) -> float:
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        tax = subtotal * 0.18  # 18% GST hardcoded here
        return subtotal + tax

    def generate_invoice_text(self, items: list[dict]) -> str:
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        tax = subtotal * 0.18  # 18% GST hardcoded again!
        total = subtotal + tax
        return f"Subtotal: {subtotal}, Tax (18%): {tax}, Total: {total}"

    def validate_order_total(self, items: list[dict], expected_total: float) -> bool:
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        tax = subtotal * 0.18  # 18% GST hardcoded a THIRD time!
        actual_total = subtotal + tax
        return abs(actual_total - expected_total) < 0.01
```

**What is wrong**: The tax rate `0.18` and the subtotal calculation appear three times. When India changes GST rates, you must find and update all three. Miss one, and you have a billing bug.

### GOOD Example — Single Source of Truth

```python
from dataclasses import dataclass


TAX_RATE = 0.18  # Single source of truth for tax rate


@dataclass
class LineItem:
    price: float
    quantity: int

    @property
    def line_total(self) -> float:
        return self.price * self.quantity


class TaxCalculator:
    """Single place that knows how tax works."""

    def __init__(self, rate: float = TAX_RATE):
        self.rate = rate

    def compute(self, subtotal: float) -> float:
        return subtotal * self.rate


class OrderCalculator:
    def __init__(self, tax_calculator: TaxCalculator | None = None):
        self.tax_calculator = tax_calculator or TaxCalculator()

    def subtotal(self, items: list[LineItem]) -> float:
        return sum(item.line_total for item in items)

    def total(self, items: list[LineItem]) -> float:
        sub = self.subtotal(items)
        return sub + self.tax_calculator.compute(sub)

    def breakdown(self, items: list[LineItem]) -> dict:
        sub = self.subtotal(items)
        tax = self.tax_calculator.compute(sub)
        return {"subtotal": sub, "tax": tax, "total": sub + tax}


class InvoiceService:
    def __init__(self):
        self.calculator = OrderCalculator()

    def calculate_total(self, items: list[LineItem]) -> float:
        return self.calculator.total(items)

    def generate_invoice_text(self, items: list[LineItem]) -> str:
        bd = self.calculator.breakdown(items)
        return f"Subtotal: {bd['subtotal']}, Tax: {bd['tax']}, Total: {bd['total']}"

    def validate_order_total(self, items: list[LineItem], expected: float) -> bool:
        return abs(self.calculator.total(items) - expected) < 0.01
```

### When DRY Goes Too Far — Wrong Abstractions

```python
# OVER-DRY: Forcing unrelated things into the same abstraction

class GenericProcessor:
    """
    Handles orders, refunds, returns, and subscriptions
    through a single 'process' method with flags.
    This is the WRONG abstraction — DRY taken too far.
    """

    def process(
        self,
        entity_type: str,
        action: str,
        data: dict,
        notify: bool = True,
        validate: bool = True,
        async_mode: bool = False,
    ) -> dict:
        if entity_type == "order" and action == "create":
            pass  # ... order creation logic
        elif entity_type == "order" and action == "cancel":
            pass  # ... order cancellation logic
        elif entity_type == "refund" and action == "create":
            pass  # ... refund logic
        # 50 more branches...
        return {}
```

**The fix**: Sometimes duplication is better than the wrong abstraction. If two pieces of code look similar but change for different reasons, keep them separate. The rule of three is helpful — wait until you see the pattern three times before extracting.

### Python-Specific DRY Patterns

```python
import functools
import time
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")


# --- Decorators eliminate cross-cutting duplication ---

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry logic defined once, applied everywhere."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception  # type: ignore
        return wrapper
    return decorator


def validate_positive_amount(func: Callable[P, T]) -> Callable[P, T]:
    """Validation logic defined once."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        for arg in args[1:]:  # skip self
            if isinstance(arg, (int, float)) and arg <= 0:
                raise ValueError(f"Amount must be positive, got {arg}")
        return func(*args, **kwargs)
    return wrapper


class PaymentService:
    @retry(max_attempts=3, delay=0.5)
    @validate_positive_amount
    def charge(self, amount: float) -> bool:
        print(f"Charging ${amount:.2f}")
        return True

    @retry(max_attempts=3, delay=0.5)
    @validate_positive_amount
    def refund(self, amount: float) -> bool:
        print(f"Refunding ${amount:.2f}")
        return True
```

> **Interview Tip**: When refactoring, explicitly say *"I'm extracting this into a single function because the tax calculation is knowledge — it should live in one place. If the tax rate changes, I fix it once."* But also show maturity by noting: *"I wouldn't extract just because two code blocks look similar — they must represent the same piece of knowledge."*

---

## 3. KISS (Keep It Simple, Stupid)

### Definition

> *"Simplicity is the ultimate sophistication."* — Leonardo da Vinci

Every piece of code should be as simple as possible — but no simpler. Complexity is the primary enemy of software. The more complex a system is, the harder it is to understand, debug, extend, and maintain.

### Accidental Complexity vs Essential Complexity

| Type | Definition | Example |
|---|---|---|
| **Essential complexity** | Inherent to the problem domain. You cannot eliminate it. | Tax rules with 50 brackets are complex because taxes are complex. |
| **Accidental complexity** | Introduced by our tools, decisions, or over-engineering. | A custom ORM when SQLAlchemy works fine. A microservice for a 2-page app. |

The goal of KISS is to **eliminate accidental complexity** while managing essential complexity clearly.

### Simple vs Easy

- **Simple**: Few intertwined concepts. A function that does one thing.
- **Easy**: Familiar, low effort. Copy-pasting code is "easy" but not "simple" — it creates hidden coupling.

A simple solution may require more upfront thought. An easy solution may create a mess later.

### BAD Example — Over-Engineered Configuration

```python
from abc import ABC, abstractmethod
from typing import Any


class ConfigProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any: ...


class ConfigValidator(ABC):
    @abstractmethod
    def validate(self, key: str, value: Any) -> bool: ...


class ConfigTransformer(ABC):
    @abstractmethod
    def transform(self, key: str, value: Any) -> Any: ...


class ConfigCache(ABC):
    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None: ...


class EnvironmentConfigProvider(ConfigProvider):
    def get(self, key: str) -> Any:
        import os
        return os.environ.get(key)


class TypeConfigValidator(ConfigValidator):
    def __init__(self, type_map: dict[str, type]):
        self.type_map = type_map

    def validate(self, key: str, value: Any) -> bool:
        expected_type = self.type_map.get(key)
        return expected_type is None or isinstance(value, expected_type)


class UpperCaseTransformer(ConfigTransformer):
    def transform(self, key: str, value: Any) -> Any:
        return value.upper() if isinstance(value, str) else value


class InMemoryConfigCache(ConfigCache):
    def __init__(self):
        self._cache: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value


class ConfigManager:
    """Look at all these abstractions... for reading env vars."""

    def __init__(
        self,
        provider: ConfigProvider,
        validator: ConfigValidator,
        transformer: ConfigTransformer,
        cache: ConfigCache,
    ):
        self.provider = provider
        self.validator = validator
        self.transformer = transformer
        self.cache = cache

    def get(self, key: str) -> Any:
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        value = self.provider.get(key)
        if value and self.validator.validate(key, value):
            value = self.transformer.transform(key, value)
            self.cache.set(key, value)
        return value
```

**What is wrong**: This is a **90-line framework** for reading environment variables. It has 5 abstract classes, 4 concrete implementations, and a manager class — for something Python does in one line.

### GOOD Example — Simple and Direct

```python
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Simple, typed, immutable configuration."""

    database_url: str
    redis_url: str
    debug: bool
    max_connections: int
    api_key: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
            debug=os.environ.get("DEBUG", "false").lower() == "true",
            max_connections=int(os.environ.get("MAX_CONNECTIONS", "10")),
            api_key=os.environ["API_KEY"],
        )


# Usage
config = AppConfig.from_env()
print(config.database_url)  # Typed, documented, simple
```

When you actually need caching, validation, or multiple providers — add them. Not before.

### KISS in Python — Pythonic Code

```python
# --- OVER-COMPLICATED ---
def get_active_users_complicated(users: list[dict]) -> list[str]:
    result = []
    for i in range(len(users)):
        user = users[i]
        if user.get("is_active") is not None:
            if user["is_active"] == True:
                name = user.get("name")
                if name is not None:
                    result.append(name)
    return result


# --- PYTHONIC (KISS) ---
def get_active_users(users: list[dict]) -> list[str]:
    return [u["name"] for u in users if u.get("is_active") and u.get("name")]


# --- OVER-COMPLICATED ---
class Singleton:
    _instance = None
    _lock = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


# --- PYTHONIC (KISS) --- just use a module-level instance
# config.py
_config = None

def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config
```

### Over-Engineering Examples and Fixes

| Over-Engineering | KISS Alternative |
|---|---|
| Abstract factory for creating two concrete types | Simple `if/else` or dictionary lookup |
| Custom event bus for 3 components | Direct method calls |
| Microservices for a team of 2 | Monolith with clean modules |
| Custom ORM wrapper | Use SQLAlchemy or raw queries |
| Observer pattern for a single listener | Direct callback |

> **Interview Tip**: Show restraint. When designing, say *"I could add an abstract factory here, but since we only have two payment types, a simple dictionary mapping is more appropriate. I'll introduce the pattern when complexity demands it."* This signals that you think about trade-offs, not just pattern application.

---

## 4. YAGNI (You Aren't Gonna Need It)

### Definition

> *"Always implement things when you actually need them, never when you just foresee that you might need them."* — Ron Jeffries

YAGNI is the antidote to speculative generality. Do not build features, abstractions, or flexibility for future requirements that may never come.

### Why It Matters

- **Unused code is a liability**: It still needs maintenance, testing, and mental overhead.
- **Predictions are wrong**: Most anticipated requirements never materialize or arrive in a different form.
- **Opportunity cost**: Time spent on speculative features is time not spent on real needs.
- **Increased complexity**: Every abstraction layer added "just in case" makes the system harder to understand.

### Premature Abstraction — The Code Smell

```python
# YAGNI VIOLATION: Building a plugin system for one notification method

from abc import ABC, abstractmethod
from typing import Any


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str, **kwargs: Any) -> bool: ...

    @abstractmethod
    def supports_rich_content(self) -> bool: ...

    @abstractmethod
    def max_message_length(self) -> int: ...

    @abstractmethod
    def retry_policy(self) -> dict: ...


class NotificationRouter:
    def __init__(self):
        self._channels: dict[str, NotificationChannel] = {}
        self._fallback_chain: list[str] = []
        self._rate_limiters: dict[str, Any] = {}

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        self._channels[name] = channel

    def set_fallback_chain(self, chain: list[str]) -> None:
        self._fallback_chain = chain

    def send(
        self, channel_name: str, recipient: str, message: str, **kwargs: Any
    ) -> bool:
        # Complex routing, fallback, rate limiting...
        channel = self._channels.get(channel_name)
        if not channel:
            for fallback in self._fallback_chain:
                channel = self._channels.get(fallback)
                if channel:
                    break
        if not channel:
            raise ValueError("No channel available")
        return channel.send(recipient, message, **kwargs)


class EmailChannel(NotificationChannel):
    def send(self, recipient: str, message: str, **kwargs: Any) -> bool:
        print(f"Email to {recipient}: {message}")
        return True

    def supports_rich_content(self) -> bool:
        return True

    def max_message_length(self) -> int:
        return 100_000

    def retry_policy(self) -> dict:
        return {"max_retries": 3, "backoff": "exponential"}


# All this infrastructure... for sending a single email.
```

### What You Actually Need Right Now

```python
def send_welcome_email(recipient: str, name: str) -> bool:
    """Send a welcome email. That's it. That's all we need right now."""
    message = f"Hi {name}, welcome aboard!"
    print(f"Sending email to {recipient}: {message}")
    return True


# When (IF) you need SMS support later, THEN add the abstraction.
# When (IF) you need fallback routing, THEN add the router.
# Not now. Not "just in case."
```

### YAGNI vs Extensibility — The Balance

YAGNI does not mean "never plan ahead." It means "don't build ahead." There is a difference:

```python
# GOOD: Designing for extensibility without building for it
# Use dependency injection — this ENABLES future extension without BUILDING it

from typing import Protocol


class Notifier(Protocol):
    def notify(self, recipient: str, message: str) -> bool: ...


class OrderService:
    def __init__(self, notifier: Notifier):
        self.notifier = notifier  # Injected — easy to swap later

    def place_order(self, user_email: str) -> None:
        # ... business logic ...
        self.notifier.notify(user_email, "Order placed!")


class EmailNotifier:
    def notify(self, recipient: str, message: str) -> bool:
        print(f"Email to {recipient}: {message}")
        return True


# TODAY: EmailNotifier is the only implementation.
# TOMORROW (if needed): SMSNotifier, PushNotifier — zero changes to OrderService.
# The abstraction is "free" because we'd inject the dependency anyway for testing.
```

The key insight: **dependency injection is not YAGNI** because it also serves testing. Building a `NotificationRouter` with fallback chains IS YAGNI when you have one channel.

### Speculative Generality — Code Smells

| Smell | Description |
|---|---|
| Unused parameters | `def process(data, format="json", compress=False, encrypt=False)` — if only `json` is ever used |
| Abstract classes with one implementation | The abstraction exists "in case" a second one appears |
| Configurable everything | Feature flags for features no one asked for |
| Generic frameworks for specific problems | Building a "workflow engine" for two sequential steps |
| Methods that are never called | "We might need this later" |

> **Interview Tip**: When designing, say *"I'll keep it simple for now and only add the abstraction when a second use case appears."* But also show awareness: *"I'm using dependency injection here, which makes future extension easy without building anything speculative."*

---

## 5. Composition over Inheritance

### Definition

> *"Favor object composition over class inheritance."* — Gang of Four, *Design Patterns*

Instead of building behavior through a deep class hierarchy (IS-A), build behavior by combining objects that each handle one aspect (HAS-A). Inheritance is the tightest form of coupling in OOP — composition is far more flexible.

### Why Inheritance Creates Coupling

```python
# The fragile base class problem

class Animal:
    def __init__(self, name: str):
        self.name = name
        self.energy = 100

    def eat(self, food: str) -> None:
        self.energy += 10
        print(f"{self.name} eats {food}")

    def move(self) -> None:
        self.energy -= 5
        print(f"{self.name} moves")

    def speak(self) -> None:
        print(f"{self.name} makes a sound")


class Dog(Animal):
    def speak(self) -> None:
        print(f"{self.name} barks")

    def fetch(self, item: str) -> None:
        self.move()  # Depends on parent's move()
        print(f"{self.name} fetches {item}")


class RobotDog(Dog):
    """A robot dog — doesn't eat, doesn't have energy, but we inherit both."""

    def eat(self, food: str) -> None:
        raise NotImplementedError("Robots don't eat!")  # LSP violation

    def move(self) -> None:
        # Robots don't lose energy... but parent assumes energy exists
        print(f"{self.name} rolls on wheels")
        # Forgot to handle self.energy — bug!
```

**Problems with this hierarchy**:
1. `RobotDog` inherits `eat()` and `energy` — concepts that don't apply to it.
2. Changing `Animal.move()` can break `Dog.fetch()` — fragile base class.
3. `RobotDog` violates LSP by raising `NotImplementedError`.
4. Adding `SwimmingAnimal` creates the diamond problem.

### Composition with Delegation

```python
from dataclasses import dataclass, field
from typing import Protocol


# --- Capabilities as composable objects ---

class MovementStrategy(Protocol):
    def move(self, name: str) -> None: ...


class SoundStrategy(Protocol):
    def make_sound(self, name: str) -> None: ...


class EatingStrategy(Protocol):
    def eat(self, name: str, food: str) -> None: ...


# --- Concrete strategies ---

class WalkMovement:
    def move(self, name: str) -> None:
        print(f"{name} walks on four legs")


class WheelMovement:
    def move(self, name: str) -> None:
        print(f"{name} rolls on wheels")


class FlyMovement:
    def move(self, name: str) -> None:
        print(f"{name} flies through the air")


class BarkSound:
    def make_sound(self, name: str) -> None:
        print(f"{name} barks: Woof!")


class BeepSound:
    def make_sound(self, name: str) -> None:
        print(f"{name} beeps: Beep boop!")


class SilentSound:
    def make_sound(self, name: str) -> None:
        pass  # No sound


class OrganicEating:
    def eat(self, name: str, food: str) -> None:
        print(f"{name} eats {food}")


class BatteryCharging:
    def eat(self, name: str, food: str) -> None:
        print(f"{name} charges battery")


# --- Composed entity ---

@dataclass
class Creature:
    name: str
    movement: MovementStrategy
    sound: SoundStrategy
    eating: EatingStrategy

    def move(self) -> None:
        self.movement.move(self.name)

    def speak(self) -> None:
        self.sound.make_sound(self.name)

    def eat(self, food: str) -> None:
        self.eating.eat(self.name, food)


# --- Creating diverse creatures by mixing behaviors ---

dog = Creature(
    name="Rex",
    movement=WalkMovement(),
    sound=BarkSound(),
    eating=OrganicEating(),
)

robot_dog = Creature(
    name="K-9",
    movement=WheelMovement(),
    sound=BeepSound(),
    eating=BatteryCharging(),
)

flying_silent_creature = Creature(
    name="Owl",
    movement=FlyMovement(),
    sound=SilentSound(),
    eating=OrganicEating(),
)

dog.move()       # Rex walks on four legs
robot_dog.move() # K-9 rolls on wheels
```

No deep hierarchy. No fragile base class. No diamond problem. New behaviors are new strategy objects, not new subclasses.

### Mixins as Compromise

Python supports multiple inheritance, and **mixins** are a controlled use of it:

```python
import json
import logging
from typing import Any


class JsonSerializableMixin:
    """Adds JSON serialization capability to any class."""

    def to_json(self) -> str:
        data = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                data[key] = value
        return json.dumps(data, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "JsonSerializableMixin":
        data = json.loads(json_str)
        return cls(**data)


class LoggableMixin:
    """Adds structured logging capability."""

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def log_info(self, message: str) -> None:
        self._logger.info(f"[{self.__class__.__name__}] {message}")


class TimestampMixin:
    """Adds created/updated timestamps."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kw: Any) -> None:
            from datetime import datetime
            original_init(self, *args, **kw)
            if not hasattr(self, "created_at"):
                self.created_at = datetime.now()
            self.updated_at = datetime.now()

        cls.__init__ = new_init  # type: ignore


class Product(JsonSerializableMixin, LoggableMixin, TimestampMixin):
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def apply_discount(self, percent: float) -> None:
        self.price *= (1 - percent / 100)
        self.log_info(f"Discount {percent}% applied, new price: {self.price}")


p = Product("Widget", 29.99)
p.apply_discount(10)
print(p.to_json())
```

**Rules for mixins**: Keep them small, stateless (or minimal state), and focused on a single cross-cutting concern. If a mixin grows beyond ~30 lines, it should probably be a composed object instead.

### Complete Refactoring — Inheritance to Composition

```python
# BEFORE: Deep inheritance hierarchy for notifications

class BaseNotification:
    def __init__(self, recipient: str, message: str):
        self.recipient = recipient
        self.message = message

    def validate(self) -> bool:
        return bool(self.recipient and self.message)

    def format_message(self) -> str:
        return self.message

    def send(self) -> bool:
        raise NotImplementedError


class EmailNotification(BaseNotification):
    def __init__(self, recipient: str, message: str, subject: str):
        super().__init__(recipient, message)
        self.subject = subject

    def format_message(self) -> str:
        return f"Subject: {self.subject}\n\n{self.message}"

    def send(self) -> bool:
        print(f"Email to {self.recipient}: {self.format_message()}")
        return True


class UrgentEmailNotification(EmailNotification):
    def format_message(self) -> str:
        return f"[URGENT] {super().format_message()}"


class HTMLEmailNotification(EmailNotification):
    def format_message(self) -> str:
        return f"<html><body>{self.message}</body></html>"


class UrgentHTMLEmailNotification(UrgentEmailNotification, HTMLEmailNotification):
    # Diamond problem! Which format_message() wins?
    pass
```

```python
# AFTER: Composition — behaviors are pluggable objects

from dataclasses import dataclass
from typing import Protocol


class MessageFormatter(Protocol):
    def format(self, message: str) -> str: ...


class DeliveryChannel(Protocol):
    def deliver(self, recipient: str, formatted_message: str) -> bool: ...


class PlainTextFormatter:
    def format(self, message: str) -> str:
        return message


class HTMLFormatter:
    def format(self, message: str) -> str:
        return f"<html><body>{message}</body></html>"


class UrgentDecorator:
    def __init__(self, inner: MessageFormatter):
        self.inner = inner

    def format(self, message: str) -> str:
        return f"[URGENT] {self.inner.format(message)}"


class EmailChannel:
    def __init__(self, subject: str = ""):
        self.subject = subject

    def deliver(self, recipient: str, formatted_message: str) -> bool:
        print(f"Email to {recipient} (Subject: {self.subject}): {formatted_message}")
        return True


class SMSChannel:
    def deliver(self, recipient: str, formatted_message: str) -> bool:
        print(f"SMS to {recipient}: {formatted_message[:160]}")
        return True


@dataclass
class Notification:
    recipient: str
    message: str
    formatter: MessageFormatter
    channel: DeliveryChannel

    def send(self) -> bool:
        if not self.recipient or not self.message:
            raise ValueError("Recipient and message are required")
        formatted = self.formatter.format(self.message)
        return self.channel.deliver(self.recipient, formatted)


# Mix and match any combination — no class explosion
urgent_html_email = Notification(
    recipient="alice@example.com",
    message="Server is down!",
    formatter=UrgentDecorator(HTMLFormatter()),
    channel=EmailChannel(subject="ALERT"),
)
urgent_html_email.send()
# Email to alice@example.com (Subject: ALERT): [URGENT] <html><body>Server is down!</body></html>

plain_sms = Notification(
    recipient="+1234567890",
    message="Your order shipped",
    formatter=PlainTextFormatter(),
    channel=SMSChannel(),
)
plain_sms.send()
# SMS to +1234567890: Your order shipped
```

> **Interview Tip**: If the interviewer's design starts growing an inheritance tree deeper than 2 levels, suggest composition: *"Instead of subclassing further, I'd compose behavior from smaller objects. This avoids the fragile base class problem and lets us mix capabilities freely."*

---

## 6. Law of Demeter (Principle of Least Knowledge)

### Definition

> *"Only talk to your immediate friends. Don't talk to strangers."*

A method `M` of object `O` should only call methods on:
1. `O` itself
2. Objects passed as arguments to `M`
3. Objects created inside `M`
4. `O`'s direct component objects (fields)

It should **not** call methods on objects returned by other methods — that is reaching through an object to get to another object, creating hidden coupling.

### The Train Wreck Anti-Pattern

```python
class Engine:
    def __init__(self, horsepower: int):
        self.horsepower = horsepower
        self.temperature = 90.0

    def is_overheating(self) -> bool:
        return self.temperature > 100.0


class Car:
    def __init__(self, engine: Engine):
        self.engine = engine


class Driver:
    def __init__(self, car: Car):
        self.car = car


class RaceManager:
    def check_safety(self, driver: Driver) -> bool:
        # VIOLATION: reaching through 3 objects — driver.car.engine.temperature
        # This creates coupling to the ENTIRE chain of internal structure
        if driver.car.engine.temperature > 100.0:
            print("Car is overheating!")
            return False

        # Even worse — what if Engine's internal representation changes?
        # What if temperature becomes a method? Or gets moved to a Sensor object?
        if driver.car.engine.horsepower < 100:
            print("Car too slow for racing")
            return False

        return True
```

**What is wrong**: `RaceManager` knows the internal structure of `Driver`, `Car`, AND `Engine`. If `Engine` changes its API, `RaceManager` breaks — even though `RaceManager` should have no business knowing about engine internals.

### How to Fix Demeter Violations

```python
from dataclasses import dataclass


@dataclass
class Engine:
    horsepower: int
    temperature: float = 90.0

    def is_overheating(self) -> bool:
        return self.temperature > 100.0

    def is_powerful_enough(self, min_hp: int) -> bool:
        return self.horsepower >= min_hp


@dataclass
class Car:
    engine: Engine
    model: str = "Unknown"

    def is_safe_to_race(self) -> bool:
        """Car knows how to check its own safety — delegates to engine internally."""
        return not self.engine.is_overheating() and self.engine.is_powerful_enough(100)

    def is_overheating(self) -> bool:
        """Expose a high-level query — hide the engine detail."""
        return self.engine.is_overheating()


@dataclass
class Driver:
    name: str
    car: Car

    def can_race(self) -> bool:
        """Driver delegates to car — doesn't reach into engine."""
        return self.car.is_safe_to_race()


class RaceManager:
    def check_safety(self, driver: Driver) -> bool:
        # CLEAN: ask driver, don't dig into internals
        if not driver.can_race():
            print(f"{driver.name} cannot race — car not safe")
            return False
        print(f"{driver.name} cleared for racing!")
        return True


engine = Engine(horsepower=150, temperature=95.0)
car = Car(engine=engine, model="Ferrari")
driver = Driver(name="Max", car=car)

manager = RaceManager()
manager.check_safety(driver)  # Max cleared for racing!
```

Each object only talks to its **direct neighbors**. `RaceManager` asks `Driver`, `Driver` asks `Car`, `Car` asks `Engine`. If `Engine`'s internals change, only `Car` needs updating.

### Python Property Chains and Demeter

```python
# Common in Django/SQLAlchemy — but still a Demeter violation:
# user.profile.address.city.name

# Fix with delegation:

class UserProfile:
    def __init__(self, address: "Address"):
        self._address = address

    @property
    def city_name(self) -> str:
        """Expose what callers need — hide the structure."""
        return self._address.city_name


class Address:
    def __init__(self, city: "City"):
        self._city = city

    @property
    def city_name(self) -> str:
        return self._city.name


class City:
    def __init__(self, name: str):
        self.name = name


class User:
    def __init__(self, profile: UserProfile):
        self._profile = profile

    @property
    def city_name(self) -> str:
        """user.city_name instead of user.profile.address.city.name"""
        return self._profile.city_name
```

### Real Example with Refactoring

```python
# BEFORE: E-commerce checkout violating Demeter

class CheckoutService:
    def calculate_shipping(self, order) -> float:
        # Reaching deep into order internals
        weight = sum(
            item.product.weight * item.quantity
            for item in order.cart.items  # order → cart → items → product → weight
        )
        zone = order.customer.address.shipping_zone  # customer → address → zone
        rate = zone.rate_calculator.calculate(weight)  # zone → calculator
        return rate


# AFTER: Each object provides what its callers need

class ShippingZone:
    def __init__(self, name: str, base_rate: float, per_kg_rate: float):
        self.name = name
        self.base_rate = base_rate
        self.per_kg_rate = per_kg_rate

    def calculate_shipping(self, total_weight_kg: float) -> float:
        return self.base_rate + (self.per_kg_rate * total_weight_kg)


class Address:
    def __init__(self, zone: ShippingZone):
        self._zone = zone

    def calculate_shipping(self, weight_kg: float) -> float:
        return self._zone.calculate_shipping(weight_kg)


class Customer:
    def __init__(self, address: Address):
        self._address = address

    def calculate_shipping(self, weight_kg: float) -> float:
        return self._address.calculate_shipping(weight_kg)


class Cart:
    def __init__(self, items: list[tuple[float, int]]):
        self._items = items  # (weight_per_unit, quantity)

    @property
    def total_weight(self) -> float:
        return sum(weight * qty for weight, qty in self._items)


class Order:
    def __init__(self, cart: Cart, customer: Customer):
        self._cart = cart
        self._customer = customer

    def shipping_cost(self) -> float:
        return self._customer.calculate_shipping(self._cart.total_weight)


class CheckoutService:
    def calculate_shipping(self, order: Order) -> float:
        return order.shipping_cost()  # One level deep — clean!
```

> **Interview Tip**: When you catch yourself writing `a.b.c.d`, stop and say *"This is a Demeter violation — I'm coupling to the internal structure of three objects. I'll add a delegation method so each object only talks to its neighbor."*

---

## 7. Separation of Concerns (SoC)

### Definition

> *"Let each component address a separate concern, and let the boundaries between concerns be clear and well-defined."*

A **concern** is a distinct area of functionality or a distinct reason for the system to exist. Authentication is a concern. Data persistence is a concern. Input validation is a concern. Business rules are a concern.

### Horizontal vs Vertical Separation

| Separation Type | Description | Example |
|---|---|---|
| **Horizontal (layered)** | Separate by technical function | Presentation → Business Logic → Data Access |
| **Vertical (feature-based)** | Separate by business domain | Users module, Orders module, Products module |

Best practice: use **both**. Vertical slices for features, horizontal layers within each slice.

### Layered Architecture

```python
# Layer 1: Domain / Business Logic (knows NOTHING about HTTP or databases)

from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task:
    title: str
    description: str
    status: TaskStatus = TaskStatus.TODO
    task_id: str | None = None
    created_at: datetime | None = None

    def mark_in_progress(self) -> None:
        if self.status != TaskStatus.TODO:
            raise ValueError(f"Cannot start task in {self.status.value} state")
        self.status = TaskStatus.IN_PROGRESS

    def mark_done(self) -> None:
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete task in {self.status.value} state")
        self.status = TaskStatus.DONE


# Layer 2: Application / Use Cases (orchestrates domain, depends on abstractions)

from typing import Protocol


class TaskRepository(Protocol):
    def save(self, task: Task) -> str: ...
    def find_by_id(self, task_id: str) -> Task | None: ...
    def find_all(self) -> list[Task]: ...


class TaskService:
    """Application service — pure business orchestration."""

    def __init__(self, repository: TaskRepository):
        self._repo = repository

    def create_task(self, title: str, description: str) -> Task:
        task = Task(title=title, description=description, created_at=datetime.now())
        task.task_id = self._repo.save(task)
        return task

    def start_task(self, task_id: str) -> Task:
        task = self._repo.find_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        task.mark_in_progress()
        self._repo.save(task)
        return task

    def complete_task(self, task_id: str) -> Task:
        task = self._repo.find_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        task.mark_done()
        self._repo.save(task)
        return task

    def list_tasks(self) -> list[Task]:
        return self._repo.find_all()


# Layer 3: Infrastructure (database, external services)

import uuid


class InMemoryTaskRepository:
    def __init__(self):
        self._store: dict[str, Task] = {}

    def save(self, task: Task) -> str:
        if task.task_id is None:
            task.task_id = str(uuid.uuid4())
        self._store[task.task_id] = task
        return task.task_id

    def find_by_id(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def find_all(self) -> list[Task]:
        return list(self._store.values())


# Layer 4: Presentation (HTTP handlers, CLI, etc.)
# This layer translates external requests into service calls.

class TaskCLI:
    """Presentation concern — handles user input/output."""

    def __init__(self, service: TaskService):
        self._service = service

    def handle_create(self, title: str, description: str) -> None:
        task = self._service.create_task(title, description)
        print(f"Created task: {task.task_id} — {task.title}")

    def handle_list(self) -> None:
        tasks = self._service.list_tasks()
        for task in tasks:
            print(f"[{task.status.value}] {task.task_id}: {task.title}")

    def handle_start(self, task_id: str) -> None:
        try:
            task = self._service.start_task(task_id)
            print(f"Started task: {task.title}")
        except ValueError as e:
            print(f"Error: {e}")


# Wiring (composition root)

repo = InMemoryTaskRepository()
service = TaskService(repository=repo)
cli = TaskCLI(service=service)

cli.handle_create("Write docs", "Write LLD principles documentation")
cli.handle_list()
```

### Python Package Structure for SoC

```
myproject/
├── domain/                   # Business logic — no framework imports
│   ├── __init__.py
│   ├── entities.py           # Domain objects (Task, User, Order)
│   ├── value_objects.py      # Immutable value types (Money, Email)
│   ├── events.py             # Domain events (OrderPlaced, TaskCompleted)
│   └── services.py           # Domain services (pure business logic)
│
├── application/              # Use cases — orchestrates domain
│   ├── __init__.py
│   ├── ports.py              # Interfaces (Protocol classes) for repositories, services
│   ├── task_service.py       # Application services / use cases
│   └── dto.py                # Data Transfer Objects for input/output
│
├── infrastructure/           # Technical implementations
│   ├── __init__.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── postgres_repo.py  # PostgreSQL implementation
│   │   └── redis_cache.py    # Redis caching implementation
│   ├── messaging/
│   │   ├── __init__.py
│   │   └── kafka_publisher.py
│   └── external/
│       ├── __init__.py
│       └── stripe_gateway.py
│
├── presentation/             # User-facing interfaces
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── serializers.py
│   └── cli/
│       ├── __init__.py
│       └── commands.py
│
└── config.py                 # Composition root — wires everything together
```

**Key rule**: Dependencies point **inward** — `presentation` → `application` → `domain`. Never the reverse. `domain` has zero imports from `infrastructure` or `presentation`.

> **Interview Tip**: When designing a system, draw the layers before writing code. Say *"I'll separate concerns into domain, application, and infrastructure layers. The domain layer has no external dependencies — it's pure business logic. Infrastructure implements the interfaces the domain defines."*

---

## 8. High Cohesion, Low Coupling

### Definitions

- **Cohesion**: How closely related the responsibilities within a single module are. High cohesion means everything in the class belongs together.
- **Coupling**: How much one module depends on the internals of another. Low coupling means modules interact through narrow, stable interfaces.

The goal: **high cohesion within modules, low coupling between modules.**

### Measuring Cohesion (LCOM)

LCOM (Lack of Cohesion of Methods) informally measures how many "clusters" of related methods exist in a class. If a class has two groups of methods that access completely different sets of instance variables, it should probably be two classes.

```python
# LOW COHESION — two unrelated clusters of methods

class UserManager:
    def __init__(self):
        self.users: dict[int, dict] = {}       # Cluster A uses this
        self.email_config: dict = {}            # Cluster B uses this
        self.email_templates: dict[str, str] = {}  # Cluster B uses this

    # --- Cluster A: user management ---
    def create_user(self, name: str, email: str) -> int:
        user_id = len(self.users) + 1
        self.users[user_id] = {"name": name, "email": email}
        return user_id

    def delete_user(self, user_id: int) -> None:
        del self.users[user_id]

    def find_user(self, user_id: int) -> dict | None:
        return self.users.get(user_id)

    # --- Cluster B: email operations — unrelated to user CRUD ---
    def configure_email(self, smtp_host: str, port: int) -> None:
        self.email_config = {"host": smtp_host, "port": port}

    def add_template(self, name: str, body: str) -> None:
        self.email_templates[name] = body

    def send_email(self, to: str, template_name: str) -> None:
        template = self.email_templates.get(template_name, "")
        print(f"Sending '{template}' to {to} via {self.email_config}")
```

```python
# HIGH COHESION — each class has one focused responsibility

from dataclasses import dataclass, field


class UserRepository:
    """All methods use self._users — high cohesion."""

    def __init__(self):
        self._users: dict[int, dict] = {}
        self._next_id = 1

    def create(self, name: str, email: str) -> int:
        user_id = self._next_id
        self._next_id += 1
        self._users[user_id] = {"name": name, "email": email}
        return user_id

    def delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    def find(self, user_id: int) -> dict | None:
        return self._users.get(user_id)

    def exists(self, user_id: int) -> bool:
        return user_id in self._users


@dataclass
class EmailService:
    """All methods relate to sending emails — high cohesion."""

    smtp_host: str
    smtp_port: int
    templates: dict[str, str] = field(default_factory=dict)

    def add_template(self, name: str, body: str) -> None:
        self.templates[name] = body

    def send(self, to: str, template_name: str, **context: str) -> None:
        template = self.templates.get(template_name, "")
        body = template.format(**context) if context else template
        print(f"Sending to {to} via {self.smtp_host}:{self.smtp_port}: {body}")
```

### Types of Coupling (Weakest to Strongest)

| Type | Description | Example | Severity |
|---|---|---|---|
| **Data coupling** | Modules share simple data (primitives) | `calculate_tax(amount: float)` | Acceptable |
| **Stamp coupling** | Modules share a data structure but only use part of it | Passing an entire `User` when only `email` is needed | Mild concern |
| **Control coupling** | One module controls another's behavior via a flag | `process(data, mode="fast")` | Moderate concern |
| **Common coupling** | Modules share global state | Two modules reading/writing a global variable | Bad |
| **Content coupling** | One module directly accesses another's internals | `obj._private_field = 42` | Terrible |

```python
# CONTENT COUPLING (worst) — directly accessing private state

class Account:
    def __init__(self, balance: float):
        self._balance = balance


class TransferService:
    def transfer(self, source: Account, target: Account, amount: float) -> None:
        # Directly manipulating private state — fragile coupling
        source._balance -= amount  # BAD: bypasses any validation
        target._balance += amount  # BAD: breaks encapsulation


# DATA COUPLING (best) — share only what's needed

class Account:
    def __init__(self, balance: float):
        self._balance = balance

    def withdraw(self, amount: float) -> float:
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        return amount

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._balance += amount

    @property
    def balance(self) -> float:
        return self._balance


class TransferService:
    def transfer(self, source: Account, target: Account, amount: float) -> None:
        withdrawn = source.withdraw(amount)  # Uses public API
        target.deposit(withdrawn)            # Uses public API
```

### Refactoring for Better Coupling

```python
# TIGHTLY COUPLED — Payment processor knows about order internals,
# database schema, and email format

class TightPaymentProcessor:
    def process(self, order_dict: dict) -> None:
        amount = order_dict["items_total"] + order_dict["tax"] + order_dict["shipping"]
        # Knows the database schema
        query = f"INSERT INTO payments (order_id, amount) VALUES ({order_dict['id']}, {amount})"
        print(f"Executing: {query}")
        # Knows the email format
        print(f"Email: Dear {order_dict['customer']['name']}, paid ${amount}")


# LOOSELY COUPLED — interacts through well-defined interfaces

from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentRequest:
    order_id: str
    amount: float
    currency: str = "USD"


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    transaction_id: str
    message: str


class PaymentGateway(Protocol):
    def charge(self, request: PaymentRequest) -> PaymentResult: ...


class PaymentRecorder(Protocol):
    def record(self, request: PaymentRequest, result: PaymentResult) -> None: ...


class LoosePaymentProcessor:
    """Knows only about PaymentRequest and its two collaborators."""

    def __init__(self, gateway: PaymentGateway, recorder: PaymentRecorder):
        self._gateway = gateway
        self._recorder = recorder

    def process(self, request: PaymentRequest) -> PaymentResult:
        result = self._gateway.charge(request)
        self._recorder.record(request, result)
        return result
```

> **Interview Tip**: When discussing your design, say *"This module has high cohesion — all its methods work with the same data and serve the same purpose. And it's loosely coupled to its collaborators through a Protocol interface, so we can swap implementations without touching this code."*

---

## 9. Design for Change

### Definition

> *"The only constant in software is change."*

Design for Change means structuring your code so that the **most likely changes** require the **least amount of modification**. Identify what will vary, and encapsulate it behind a stable interface.

### Identifying Axes of Change

Before designing, ask: *"What is likely to change?"*

| In a payment system... | What changes | What stays stable |
|---|---|---|
| Payment providers | Stripe → PayPal → Razorpay | The concept of "charging money" |
| Tax rules | Rates, brackets, exemptions | The concept of "applying tax" |
| Notification channels | Email → SMS → Push | The concept of "notifying a user" |
| Data storage | PostgreSQL → MongoDB → DynamoDB | The concept of "persisting data" |
| Discount strategies | Flat, percentage, seasonal, bundled | The concept of "applying a discount" |

**Encapsulate what varies** behind an abstraction. The stable concept becomes the interface; the variable implementations are interchangeable.

### Information Hiding

```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime


# The "what" is stable; the "how" is hidden

class PricingEngine(Protocol):
    """Stable interface — callers don't know HOW prices are calculated."""

    def calculate_price(self, base_price: float, context: "PricingContext") -> float: ...


@dataclass
class PricingContext:
    customer_tier: str
    order_date: datetime
    quantity: int
    promo_code: str | None = None


class SimplePricing:
    """Today's implementation — might be replaced tomorrow."""

    def calculate_price(self, base_price: float, context: PricingContext) -> float:
        discount = 0.0
        if context.customer_tier == "premium":
            discount = 0.10
        if context.quantity >= 10:
            discount += 0.05
        return base_price * (1 - discount)


class DynamicPricing:
    """Tomorrow's implementation — slot it in, zero changes to callers."""

    def __init__(self, rules: list[dict]):
        self._rules = rules

    def calculate_price(self, base_price: float, context: PricingContext) -> float:
        price = base_price
        for rule in self._rules:
            if self._rule_applies(rule, context):
                price *= (1 - rule["discount"])
        return price

    def _rule_applies(self, rule: dict, context: PricingContext) -> bool:
        return context.customer_tier in rule.get("tiers", [context.customer_tier])
```

### Stable vs Unstable Dependencies

**Depend on stable things. Isolate unstable things.**

```python
# STABLE: Python's built-in types, your own domain model, well-established libraries
# UNSTABLE: Third-party APIs, configuration formats, UI frameworks

# Wrap unstable dependencies

from typing import Protocol


class CurrencyConverter(Protocol):
    """Stable interface defined by US."""

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float: ...


class FixerIOConverter:
    """Unstable dependency — this API might change, go down, or get replaced."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        # Wrap the unstable third-party API call
        print(f"Calling fixer.io API to convert {amount} {from_currency} → {to_currency}")
        return amount * 1.1  # Simulated


class CachedConverter:
    """Decorator that adds caching — doesn't change the interface."""

    def __init__(self, inner: CurrencyConverter, cache_ttl: int = 3600):
        self._inner = inner
        self._cache: dict[str, tuple[float, float]] = {}

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        key = f"{from_currency}:{to_currency}"
        if key in self._cache:
            rate, _ = self._cache[key]
            return amount * rate
        result = self._inner.convert(1.0, from_currency, to_currency)
        self._cache[key] = (result, 0)
        return amount * result
```

### Complete Example — Payment System Designed for Change

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
import uuid


# --- Stable domain model ---

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    payment_id: str
    order_id: str
    amount: float
    currency: str
    status: PaymentStatus
    gateway_name: str
    created_at: datetime = field(default_factory=datetime.now)
    gateway_transaction_id: str | None = None
    failure_reason: str | None = None


# --- Axes of change identified and encapsulated ---

# Axis 1: Payment gateway (Stripe, PayPal, etc.)
class PaymentGateway(Protocol):
    @property
    def name(self) -> str: ...
    def charge(self, amount: float, currency: str, token: str) -> dict: ...
    def refund(self, transaction_id: str, amount: float) -> dict: ...


# Axis 2: Fraud detection (rules change frequently)
class FraudChecker(Protocol):
    def is_fraudulent(self, amount: float, customer_id: str) -> bool: ...


# Axis 3: Payment recording (database might change)
class PaymentStore(Protocol):
    def save(self, payment: Payment) -> None: ...
    def find_by_order(self, order_id: str) -> list[Payment]: ...


# Axis 4: Notification (channels change)
class PaymentNotifier(Protocol):
    def notify_success(self, payment: Payment) -> None: ...
    def notify_failure(self, payment: Payment) -> None: ...


# --- Stable orchestration layer ---

class PaymentService:
    """This class changes VERY RARELY — it only orchestrates."""

    def __init__(
        self,
        gateway: PaymentGateway,
        fraud_checker: FraudChecker,
        store: PaymentStore,
        notifier: PaymentNotifier,
    ):
        self._gateway = gateway
        self._fraud_checker = fraud_checker
        self._store = store
        self._notifier = notifier

    def process_payment(
        self, order_id: str, amount: float, currency: str,
        customer_id: str, payment_token: str,
    ) -> Payment:
        payment = Payment(
            payment_id=str(uuid.uuid4()),
            order_id=order_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            gateway_name=self._gateway.name,
        )

        if self._fraud_checker.is_fraudulent(amount, customer_id):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Fraud detected"
            self._store.save(payment)
            self._notifier.notify_failure(payment)
            return payment

        try:
            result = self._gateway.charge(amount, currency, payment_token)
            payment.status = PaymentStatus.COMPLETED
            payment.gateway_transaction_id = result.get("transaction_id")
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)

        self._store.save(payment)

        if payment.status == PaymentStatus.COMPLETED:
            self._notifier.notify_success(payment)
        else:
            self._notifier.notify_failure(payment)

        return payment


# --- Implementations (each can change independently) ---

class StripeGateway:
    name = "stripe"

    def charge(self, amount: float, currency: str, token: str) -> dict:
        print(f"Stripe: charging {currency} {amount:.2f}")
        return {"transaction_id": f"stripe_{uuid.uuid4().hex[:8]}"}

    def refund(self, transaction_id: str, amount: float) -> dict:
        print(f"Stripe: refunding {amount:.2f} for {transaction_id}")
        return {"refund_id": f"ref_{uuid.uuid4().hex[:8]}"}


class SimpleFraudChecker:
    def __init__(self, max_amount: float = 10_000):
        self._max_amount = max_amount

    def is_fraudulent(self, amount: float, customer_id: str) -> bool:
        return amount > self._max_amount


class InMemoryPaymentStore:
    def __init__(self):
        self._payments: list[Payment] = []

    def save(self, payment: Payment) -> None:
        self._payments.append(payment)

    def find_by_order(self, order_id: str) -> list[Payment]:
        return [p for p in self._payments if p.order_id == order_id]


class ConsolePaymentNotifier:
    def notify_success(self, payment: Payment) -> None:
        print(f"Payment {payment.payment_id} succeeded: {payment.currency} {payment.amount:.2f}")

    def notify_failure(self, payment: Payment) -> None:
        print(f"Payment {payment.payment_id} failed: {payment.failure_reason}")


# --- Composition root ---
service = PaymentService(
    gateway=StripeGateway(),
    fraud_checker=SimpleFraudChecker(max_amount=5000),
    store=InMemoryPaymentStore(),
    notifier=ConsolePaymentNotifier(),
)

payment = service.process_payment(
    order_id="ORD-001",
    amount=99.99,
    currency="USD",
    customer_id="CUST-42",
    payment_token="tok_visa_4242",
)
```

**Why this design handles change well**: Switching from Stripe to PayPal? Write `PayPalGateway` and inject it. Adding ML-based fraud detection? Write `MLFraudChecker`. Switching to PostgreSQL? Write `PostgresPaymentStore`. None of these changes touch `PaymentService`.

> **Interview Tip**: Before coding, say *"Let me identify the axes of change: the payment gateway, fraud rules, and storage engine are all likely to change independently, so I'll put each behind an abstraction."* This demonstrates strategic thinking.

---

## 10. Fail-Fast Principle

### Definition

> *"If something is going to fail, it should fail as early as possible, as loudly as possible, with a clear message about what went wrong."*

Fail-fast means **validating inputs and preconditions at the boundary** — the moment data enters your system — rather than letting bad data propagate through layers until it causes a cryptic error deep in the stack.

### Why It Matters

- **Easier debugging**: The error points to the actual problem, not a downstream symptom.
- **Data integrity**: Bad data never reaches the database or external services.
- **Security**: Invalid inputs are rejected before they can cause damage.
- **Better error messages**: Users and callers get actionable feedback immediately.

### BAD Example — Fail-Late

```python
class OrderProcessor:
    def process(self, order_data: dict) -> None:
        # No validation at entry point — bad data flows through the entire system

        # Somewhere deep in processing...
        items = order_data["items"]  # KeyError if missing
        for item in items:
            price = item["price"]  # KeyError if missing
            quantity = item["quantity"]
            subtotal = price * quantity  # TypeError if price is a string

            # Even deeper...
            if subtotal < 0:
                # By now we've already done work, maybe even called external services
                print("Something went wrong")  # Vague, unhelpful

        # Much later, a database insertion fails because user_id is None
        user_id = order_data.get("user_id")
        # INSERT INTO orders (user_id, ...) VALUES (None, ...)
        # → IntegrityError: NOT NULL constraint failed
```

**What is wrong**: The error manifests as a database constraint violation — far from where the actual problem is (missing `user_id` in the input). Debugging requires tracing through the entire call stack.

### GOOD Example — Fail-Fast with Clear Messages

```python
from dataclasses import dataclass
from typing import Any


class ValidationError(Exception):
    """Clear, specific error with context."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error on '{field}': {message} (got: {value!r})")


@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float

    def __post_init__(self) -> None:
        if not self.product_id:
            raise ValidationError("product_id", "must not be empty")
        if self.quantity <= 0:
            raise ValidationError("quantity", "must be positive", self.quantity)
        if self.unit_price < 0:
            raise ValidationError("unit_price", "must be non-negative", self.unit_price)


@dataclass(frozen=True)
class OrderRequest:
    user_id: str
    items: list[OrderItem]
    shipping_address: str

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValidationError("user_id", "must not be empty")
        if not self.items:
            raise ValidationError("items", "must contain at least one item")
        if not self.shipping_address:
            raise ValidationError("shipping_address", "must not be empty")

    @classmethod
    def from_dict(cls, data: dict) -> "OrderRequest":
        """Parse and validate at the boundary — fail fast."""
        required_fields = ["user_id", "items", "shipping_address"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValidationError(field_name, "is required but missing")

        if not isinstance(data["items"], list):
            raise ValidationError("items", "must be a list", type(data["items"]).__name__)

        items = []
        for i, item_data in enumerate(data["items"]):
            try:
                items.append(OrderItem(
                    product_id=item_data["product_id"],
                    quantity=int(item_data["quantity"]),
                    unit_price=float(item_data["unit_price"]),
                ))
            except KeyError as e:
                raise ValidationError(f"items[{i}]", f"missing field: {e}")
            except (ValueError, TypeError) as e:
                raise ValidationError(f"items[{i}]", f"invalid data: {e}")

        return cls(
            user_id=str(data["user_id"]),
            items=items,
            shipping_address=str(data["shipping_address"]),
        )
```

### Guards and Validators

```python
from typing import TypeVar, Callable

T = TypeVar("T")


def guard(condition: bool, message: str) -> None:
    """Simple guard — fails immediately with a clear message."""
    if not condition:
        raise ValueError(message)


def guard_not_none(value: T | None, name: str) -> T:
    """Ensures a value is not None, with a meaningful error."""
    if value is None:
        raise ValueError(f"{name} must not be None")
    return value


def guard_positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def guard_in_range(value: float, min_val: float, max_val: float, name: str) -> float:
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
    return value


class MoneyTransfer:
    def execute(self, from_account_id: str, to_account_id: str, amount: float) -> None:
        # All preconditions checked upfront — fail fast
        guard(bool(from_account_id), "from_account_id must not be empty")
        guard(bool(to_account_id), "to_account_id must not be empty")
        guard(from_account_id != to_account_id, "Cannot transfer to the same account")
        guard_positive(amount, "transfer amount")
        guard_in_range(amount, 0.01, 1_000_000, "transfer amount")

        # If we reach here, all inputs are valid
        print(f"Transferring ${amount:.2f} from {from_account_id} to {to_account_id}")
```

### Order Validation Pipeline

```python
from dataclasses import dataclass
from typing import Protocol
from datetime import datetime, timedelta


@dataclass
class Order:
    order_id: str
    user_id: str
    items: list[dict]
    total: float
    created_at: datetime


class OrderValidator(Protocol):
    def validate(self, order: Order) -> None:
        """Raises ValueError if validation fails."""
        ...


class NonEmptyItemsValidator:
    def validate(self, order: Order) -> None:
        if not order.items:
            raise ValueError("Order must have at least one item")


class PositiveTotalValidator:
    def validate(self, order: Order) -> None:
        if order.total <= 0:
            raise ValueError(f"Order total must be positive, got {order.total}")


class MaxAmountValidator:
    def __init__(self, max_amount: float):
        self._max = max_amount

    def validate(self, order: Order) -> None:
        if order.total > self._max:
            raise ValueError(
                f"Order total {order.total} exceeds maximum {self._max}"
            )


class NotExpiredValidator:
    def __init__(self, max_age: timedelta = timedelta(hours=24)):
        self._max_age = max_age

    def validate(self, order: Order) -> None:
        age = datetime.now() - order.created_at
        if age > self._max_age:
            raise ValueError(f"Order expired: created {age} ago (max: {self._max_age})")


class ItemQuantityValidator:
    def validate(self, order: Order) -> None:
        for i, item in enumerate(order.items):
            qty = item.get("quantity", 0)
            if qty <= 0:
                raise ValueError(f"Item {i} has invalid quantity: {qty}")


class ValidationPipeline:
    """Runs all validators — collects ALL errors, not just the first one."""

    def __init__(self, validators: list[OrderValidator]):
        self._validators = validators

    def validate(self, order: Order) -> list[str]:
        errors: list[str] = []
        for validator in self._validators:
            try:
                validator.validate(order)
            except ValueError as e:
                errors.append(str(e))
        return errors

    def validate_or_raise(self, order: Order) -> None:
        errors = self.validate(order)
        if errors:
            raise ValueError(
                f"Order validation failed with {len(errors)} error(s):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )


# --- Usage ---

pipeline = ValidationPipeline([
    NonEmptyItemsValidator(),
    PositiveTotalValidator(),
    MaxAmountValidator(max_amount=50_000),
    NotExpiredValidator(max_age=timedelta(hours=24)),
    ItemQuantityValidator(),
])

order = Order(
    order_id="ORD-001",
    user_id="USR-42",
    items=[{"product_id": "P1", "quantity": 0}],  # Bad quantity
    total=-50,  # Negative total
    created_at=datetime.now() - timedelta(hours=48),  # Expired
)

errors = pipeline.validate(order)
for error in errors:
    print(f"  ✗ {error}")

# Output:
#   ✗ Order total must be positive, got -50
#   ✗ Order expired: created 2 days, 0:00:00 ago (max: 1 day, 0:00:00)
#   ✗ Item 0 has invalid quantity: 0
```

### Python Implementation Patterns for Fail-Fast

```python
# 1. Use __post_init__ in dataclasses
from dataclasses import dataclass


@dataclass
class Email:
    address: str

    def __post_init__(self) -> None:
        if "@" not in self.address:
            raise ValueError(f"Invalid email: {self.address}")
        local, domain = self.address.rsplit("@", 1)
        if not local or not domain or "." not in domain:
            raise ValueError(f"Invalid email format: {self.address}")


# 2. Use descriptors for reusable validation
class PositiveFloat:
    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._storage_name = f"_{name}"

    def __get__(self, obj: object, objtype: type | None = None) -> float:
        if obj is None:
            return self  # type: ignore
        return getattr(obj, self._storage_name)

    def __set__(self, obj: object, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self._name} must be a number, got {type(value).__name__}")
        if value <= 0:
            raise ValueError(f"{self._name} must be positive, got {value}")
        setattr(obj, self._storage_name, float(value))


class Product:
    price = PositiveFloat()
    weight = PositiveFloat()

    def __init__(self, name: str, price: float, weight: float):
        self.name = name
        self.price = price    # Validated automatically
        self.weight = weight  # Validated automatically


try:
    p = Product("Widget", -5.0, 1.0)  # Fails immediately
except ValueError as e:
    print(e)  # price must be positive, got -5.0


# 3. Use assertions for programmer errors (not user input)
def binary_search(arr: list[int], target: int) -> int:
    assert arr == sorted(arr), "binary_search requires a sorted array"
    # ... implementation
    return -1
```

> **Interview Tip**: When designing any public-facing method, start with validation: *"I'll validate all inputs at the boundary — user_id is not empty, amount is positive, items list is non-empty. This way, any business logic downstream can assume valid data."* Interviewers love seeing defensive programming at system boundaries.

---

## Summary — Principles at a Glance

| Principle | One-Line Summary | Key Question to Ask |
|---|---|---|
| **SRP** | One class, one reason to change | "Who might ask for changes to this class?" |
| **OCP** | Extend without modifying | "Can I add new behavior without touching existing code?" |
| **LSP** | Subtypes must be substitutable | "Can I use this subclass everywhere the parent is used?" |
| **ISP** | Small, focused interfaces | "Does this class implement methods it never uses?" |
| **DIP** | Depend on abstractions | "Does my business logic import infrastructure?" |
| **DRY** | One place for each piece of knowledge | "If this rule changes, how many files do I edit?" |
| **KISS** | Simple over clever | "Could a new team member understand this in 5 minutes?" |
| **YAGNI** | Build it when you need it | "Do I have a concrete requirement for this, right now?" |
| **Composition > Inheritance** | Prefer HAS-A over IS-A | "Would a strategy/delegate be more flexible here?" |
| **Law of Demeter** | Don't reach through objects | "Am I accessing a friend-of-a-friend's methods?" |
| **Separation of Concerns** | Clear boundaries between responsibilities | "Does this module mix presentation with business logic?" |
| **High Cohesion, Low Coupling** | Related things together, clear interfaces between | "Do all methods in this class use the same data?" |
| **Design for Change** | Encapsulate what varies | "What is most likely to change, and is it behind an abstraction?" |
| **Fail Fast** | Validate early, fail loudly | "If this input is invalid, when do we find out?" |

---

## Principles in Combination — How They Work Together

These principles are not isolated. In practice, they reinforce each other:

- **SRP + DIP**: Single-responsibility classes with injected dependencies are easy to test and swap.
- **OCP + Composition**: New behavior via new strategy objects (composition) without modifying existing code (OCP).
- **ISP + LSP**: Small interfaces (ISP) make it easy for subtypes to fully implement them (LSP).
- **KISS + YAGNI**: Keep it simple (KISS) by not building what you don't need (YAGNI).
- **Fail Fast + SoC**: Validate at the boundary (fail fast) so inner layers (SoC) can assume clean data.
- **DRY + Composition**: Extract shared behavior into composed objects instead of duplicating across a hierarchy.
- **Demeter + Low Coupling**: Limiting knowledge of internals (Demeter) naturally reduces coupling.
- **Design for Change + DIP**: Identifying axes of change leads naturally to abstractions and dependency inversion.

Mastering these principles is not about applying all of them all the time — it is about recognizing **which principle applies to the design decision you are making right now** and making a conscious trade-off.

---

> *"There are only two hard things in Computer Science: cache invalidation, naming things, and off-by-one errors."* — Phil Karlton (extended)

The principles in this guide will not eliminate complexity — but they will help you **manage** it, **isolate** it, and **reason** about it. That is the foundation of great design.
