# Python Design Fundamentals for LLD

> Master the building blocks that separate production-grade Python designs from toy scripts.
> Every concept is paired with runnable code so you can experiment in your own REPL.

---

## Table of Contents

1. [Dependency Injection](#1-dependency-injection)
2. [Encapsulation in Python](#2-encapsulation-in-python)
3. [Abstraction in Python](#3-abstraction-in-python)
4. [Polymorphism in Python](#4-polymorphism-in-python)
5. [Protocols & Structural Typing](#5-protocols--structural-typing)
6. [Interface Segregation using Protocols](#6-interface-segregation-using-protocols)
7. [Dependency Inversion in Python](#7-dependency-inversion-in-python)
8. [Open/Closed Principle](#8-openclosed-principle)
9. [Error Handling Strategies](#9-error-handling-strategies)
10. [Domain Modelling](#10-domain-modelling)
11. [Extensibility](#11-extensibility)
12. [Testability](#12-testability)
13. [Writing Maintainable Code](#13-writing-maintainable-code)
14. [Code Smells in LLD](#14-code-smells-in-lld)
15. [Why Most Python LLD Solutions Fail](#15-why-most-python-lld-solutions-fail)

---

## 1. Dependency Injection

Dependency Injection (DI) is a technique where an object receives its dependencies from
external code rather than constructing them itself. This decouples object creation from
object use, making code more testable, flexible, and aligned with the Dependency Inversion
Principle.

### 1.1 Constructor Injection

The most common and generally preferred form. Dependencies are provided through the
`__init__` method, guaranteeing the object is fully configured at construction time.

```python
from typing import Protocol


class Logger(Protocol):
    def log(self, message: str) -> None: ...


class ConsoleLogger:
    def log(self, message: str) -> None:
        print(f"[CONSOLE] {message}")


class FileLogger:
    def __init__(self, path: str) -> None:
        self._path = path

    def log(self, message: str) -> None:
        with open(self._path, "a") as f:
            f.write(f"[FILE] {message}\n")


class OrderService:
    """Service that depends on a Logger — injected via constructor."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def place_order(self, item: str, qty: int) -> None:
        self._logger.log(f"Placing order: {qty}x {item}")
        # ... business logic ...
        self._logger.log(f"Order placed successfully for {item}")


# --- Usage ---
console_service = OrderService(ConsoleLogger())
console_service.place_order("Laptop", 1)

file_service = OrderService(FileLogger("/tmp/orders.log"))
file_service.place_order("Phone", 2)
```

**Why constructor injection is preferred:**

- The object is *never* in a half-initialised state.
- Dependencies are obvious from the signature.
- Immutability is easy: store dependencies as `_private` and never reassign.

### 1.2 Method Injection

Dependencies are passed per-call when they vary between invocations or when the
dependency is only needed for a specific operation.

```python
from typing import Protocol
from dataclasses import dataclass


class TaxCalculator(Protocol):
    def calculate(self, amount: float) -> float: ...


class USTaxCalculator:
    def calculate(self, amount: float) -> float:
        return amount * 0.08

class UKTaxCalculator:
    def calculate(self, amount: float) -> float:
        return amount * 0.20

class INTaxCalculator:
    def calculate(self, amount: float) -> float:
        return amount * 0.18


@dataclass
class Invoice:
    subtotal: float
    customer_country: str

    def total_with_tax(self, tax_calculator: TaxCalculator) -> float:
        """Tax strategy changes per customer — method injection is ideal."""
        tax = tax_calculator.calculate(self.subtotal)
        return self.subtotal + tax


# --- Usage ---
invoice = Invoice(subtotal=100.0, customer_country="US")
print(invoice.total_with_tax(USTaxCalculator()))   # 108.0
print(invoice.total_with_tax(UKTaxCalculator()))   # 120.0
print(invoice.total_with_tax(INTaxCalculator()))   # 118.0
```

### 1.3 Property Injection

The dependency is set via a property or setter after construction. Useful when the
dependency is optional or can be swapped at runtime, but risky because the object can
exist without a required dependency.

```python
from typing import Protocol, Optional


class NotificationChannel(Protocol):
    def send(self, recipient: str, body: str) -> None: ...


class EmailChannel:
    def send(self, recipient: str, body: str) -> None:
        print(f"Email to {recipient}: {body}")


class SMSChannel:
    def send(self, recipient: str, body: str) -> None:
        print(f"SMS to {recipient}: {body}")


class AlertService:
    def __init__(self) -> None:
        self._channel: Optional[NotificationChannel] = None

    @property
    def channel(self) -> Optional[NotificationChannel]:
        return self._channel

    @channel.setter
    def channel(self, ch: NotificationChannel) -> None:
        self._channel = ch

    def fire_alert(self, recipient: str, message: str) -> None:
        if self._channel is None:
            raise RuntimeError("No notification channel configured")
        self._channel.send(recipient, message)


# --- Usage ---
alert = AlertService()
alert.channel = EmailChannel()
alert.fire_alert("admin@co.com", "Server CPU > 90%")

alert.channel = SMSChannel()
alert.fire_alert("+1234567890", "Server CPU > 90%")
```

**Caveat:** Property injection introduces temporal coupling — the caller must remember to
set the property before calling methods that depend on it. Prefer constructor injection
unless there is a compelling reason.

### 1.4 DI Containers in Python

A DI container (or IoC container) automates the wiring of dependencies. Python does not
have a built-in container, but the pattern is straightforward to implement and libraries
like `dependency-injector` exist.

#### Minimal hand-rolled container

```python
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


class Container:
    """A minimal dependency injection container."""

    def __init__(self) -> None:
        self._factories: Dict[Type, Callable[..., Any]] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type[T], factory: Callable[..., T]) -> None:
        self._factories[interface] = factory

    def register_singleton(self, interface: Type[T], factory: Callable[..., T]) -> None:
        self._factories[interface] = factory
        self._singletons[interface] = None  # sentinel

    def resolve(self, interface: Type[T]) -> T:
        if interface in self._singletons:
            if self._singletons[interface] is None:
                self._singletons[interface] = self._factories[interface](self)
            return self._singletons[interface]
        if interface not in self._factories:
            raise KeyError(f"No registration for {interface}")
        return self._factories[interface](self)


# --- Registration ---
class DatabaseConnection:
    def query(self, sql: str) -> list:
        return [{"id": 1}]

class UserRepository:
    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    def find_by_id(self, user_id: int) -> dict:
        return self._db.query(f"SELECT * FROM users WHERE id={user_id}")[0]

class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_user(self, user_id: int) -> dict:
        return self._repo.find_by_id(user_id)


container = Container()
container.register_singleton(DatabaseConnection, lambda c: DatabaseConnection())
container.register(UserRepository, lambda c: UserRepository(c.resolve(DatabaseConnection)))
container.register(UserService, lambda c: UserService(c.resolve(UserRepository)))

service = container.resolve(UserService)
print(service.get_user(1))  # {'id': 1}
```

### 1.5 Real LLD Example — Payment System with Injectable Gateways

```python
from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import uuid


# --- Value Objects ---
class Currency(Enum):
    USD = auto()
    EUR = auto()
    INR = auto()

@dataclass(frozen=True)
class Money:
    amount: float
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    transaction_id: str
    message: str


# --- Gateway Protocol (the abstraction) ---
class PaymentGateway(Protocol):
    def charge(self, amount: Money, card_token: str) -> PaymentResult: ...
    def refund(self, transaction_id: str, amount: Money) -> PaymentResult: ...


# --- Concrete Gateways ---
class StripeGateway:
    def charge(self, amount: Money, card_token: str) -> PaymentResult:
        txn_id = f"stripe_{uuid.uuid4().hex[:12]}"
        print(f"[Stripe] Charging {amount.amount} {amount.currency.name} — token {card_token}")
        return PaymentResult(success=True, transaction_id=txn_id, message="Stripe charge OK")

    def refund(self, transaction_id: str, amount: Money) -> PaymentResult:
        print(f"[Stripe] Refunding {amount.amount} {amount.currency.name} for txn {transaction_id}")
        return PaymentResult(success=True, transaction_id=transaction_id, message="Stripe refund OK")


class RazorpayGateway:
    def charge(self, amount: Money, card_token: str) -> PaymentResult:
        txn_id = f"rzp_{uuid.uuid4().hex[:12]}"
        print(f"[Razorpay] Charging {amount.amount} {amount.currency.name}")
        return PaymentResult(success=True, transaction_id=txn_id, message="Razorpay charge OK")

    def refund(self, transaction_id: str, amount: Money) -> PaymentResult:
        print(f"[Razorpay] Refunding txn {transaction_id}")
        return PaymentResult(success=True, transaction_id=transaction_id, message="Razorpay refund OK")


# --- Domain Entity ---
@dataclass
class Payment:
    payment_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    amount: Money = field(default_factory=lambda: Money(0, Currency.USD))
    status: str = "pending"
    transaction_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)


# --- Service (depends on the abstraction, not the concrete) ---
class PaymentService:
    def __init__(self, gateway: PaymentGateway) -> None:   # constructor injection
        self._gateway = gateway

    def process_payment(self, amount: Money, card_token: str) -> Payment:
        payment = Payment(amount=amount)
        result = self._gateway.charge(amount, card_token)

        if result.success:
            payment.status = "completed"
            payment.transaction_id = result.transaction_id
        else:
            payment.status = "failed"

        return payment

    def refund_payment(self, payment: Payment) -> Payment:
        if payment.status != "completed":
            raise ValueError("Can only refund completed payments")

        result = self._gateway.refund(payment.transaction_id, payment.amount)
        if result.success:
            payment.status = "refunded"
        return payment


# --- Client code ---
stripe_service = PaymentService(StripeGateway())
p = stripe_service.process_payment(Money(49.99, Currency.USD), "tok_visa_123")
print(f"Payment {p.payment_id}: {p.status} (txn: {p.transaction_id})")

rzp_service = PaymentService(RazorpayGateway())
p2 = rzp_service.process_payment(Money(999, Currency.INR), "tok_upi_456")
print(f"Payment {p2.payment_id}: {p2.status} (txn: {p2.transaction_id})")
```

**Key takeaway:** `PaymentService` knows *nothing* about Stripe or Razorpay. Swapping
gateways requires zero changes inside the service — only the wiring code changes.

---

## 2. Encapsulation in Python

Encapsulation is the bundling of data with the methods that operate on that data, combined
with restricting direct access to some of the object's components. Python approaches
encapsulation through *convention and cooperation* rather than strict compiler enforcement.

### 2.1 Private vs Protected vs Public Conventions

| Convention    | Syntax          | Meaning                                                |
|---------------|-----------------|--------------------------------------------------------|
| **Public**    | `self.name`     | Part of the class API; safe for external use.          |
| **Protected** | `self._name`    | Internal detail; external code *should not* use it.    |
| **Private**   | `self.__name`   | Name-mangled; very hard to access from outside.        |

```python
class Account:
    def __init__(self, owner: str, balance: float) -> None:
        self.owner = owner           # public
        self._account_type = "savings"  # protected by convention
        self.__balance = balance     # name-mangled to _Account__balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.__balance += amount

    def get_balance(self) -> float:
        return self.__balance


acct = Account("Alice", 1000)

# Public — works fine
print(acct.owner)

# Protected — works but signals "don't touch"
print(acct._account_type)

# Private — AttributeError
try:
    print(acct.__balance)
except AttributeError as e:
    print(f"Cannot access: {e}")

# Name-mangled access (possible but strongly discouraged)
print(acct._Account__balance)  # 1000
```

### 2.2 Name Mangling (`__var`)

When Python sees a name starting with two underscores and ending with at most one
underscore, it rewrites it internally to `_ClassName__name`. This prevents accidental
name collisions in subclasses rather than enforcing security.

```python
class Base:
    def __init__(self) -> None:
        self.__secret = 42

    def reveal(self) -> int:
        return self.__secret


class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.__secret = 99  # this creates _Child__secret, NOT _Base__secret

    def child_reveal(self) -> int:
        return self.__secret


obj = Child()
print(obj.reveal())        # 42 — accesses _Base__secret
print(obj.child_reveal())  # 99 — accesses _Child__secret

# Under the hood
print(obj.__dict__)
# {'_Base__secret': 42, '_Child__secret': 99}
```

**When to use name mangling:**

- You have a deep inheritance hierarchy and want to avoid subclasses accidentally
  overwriting internal state.
- Never use it as a "security" mechanism — it is trivially bypassed.

### 2.3 Properties (`@property`, `@setter`)

Properties let you expose attribute-like access while running validation or computation
behind the scenes. They are the Pythonic replacement for explicit getter/setter methods.

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self.celsius = celsius  # triggers the setter

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("Temperature below absolute zero is impossible")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        self.celsius = (value - 32) * 5 / 9

    def __repr__(self) -> str:
        return f"Temperature({self._celsius}°C / {self.fahrenheit}°F)"


t = Temperature(100)
print(t)              # Temperature(100°C / 212.0°F)
t.fahrenheit = 32
print(t)              # Temperature(0.0°C / 32.0°F)

try:
    t.celsius = -300
except ValueError as e:
    print(e)          # Temperature below absolute zero is impossible
```

#### Read-only properties

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    name: str
    _created_at: datetime = None

    def __post_init__(self) -> None:
        self._created_at = datetime.now()

    @property
    def created_at(self) -> datetime:
        """Read-only timestamp — no setter defined."""
        return self._created_at


event = Event("Signup")
print(event.created_at)

try:
    event.created_at = datetime(2000, 1, 1)
except AttributeError as e:
    print(f"Blocked: {e}")  # property 'created_at' of 'Event' object has no setter
```

### 2.4 Why Python's Encapsulation Is Different from Java / C++

| Aspect                | Java / C++                          | Python                                    |
|-----------------------|-------------------------------------|-------------------------------------------|
| Access modifiers      | `private`, `protected`, `public`    | Convention only (`_`, `__`)               |
| Compiler enforcement  | Yes — compile error on violation    | No — runtime name mangling at best        |
| Philosophy            | *Protect programmers from themselves* | *We're all consenting adults here*        |
| Reflection bypass     | Possible but verbose                | Trivial (`obj.__dict__`, `getattr`)       |
| Properties            | Explicit `getX()` / `setX()` methods| `@property` decorator — Pythonic          |

Python trusts the developer. A single underscore `_` is a *social contract*: "This is
internal; use it at your own risk." The language deliberately avoids the ceremony of
access modifiers, favouring readability and rapid development.

### 2.5 Practical Encapsulation in LLD

```python
from __future__ import annotations
from typing import List
from dataclasses import dataclass, field


@dataclass
class CartItem:
    product_name: str
    unit_price: float
    quantity: int

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity


class ShoppingCart:
    """
    Encapsulates the internal list of items.
    External code cannot directly mutate the list — it must go through
    add_item / remove_item which enforce business rules.
    """

    def __init__(self, max_items: int = 50) -> None:
        self._items: List[CartItem] = []
        self._max_items = max_items

    @property
    def items(self) -> tuple:
        """Return an immutable view so callers cannot mutate the internal list."""
        return tuple(self._items)

    @property
    def total(self) -> float:
        return sum(item.line_total for item in self._items)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self._items)

    def add_item(self, product_name: str, unit_price: float, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.item_count + quantity > self._max_items:
            raise ValueError(f"Cart cannot exceed {self._max_items} items")

        for item in self._items:
            if item.product_name == product_name:
                item.quantity += quantity
                return

        self._items.append(CartItem(product_name, unit_price, quantity))

    def remove_item(self, product_name: str) -> None:
        self._items = [i for i in self._items if i.product_name != product_name]

    def clear(self) -> None:
        self._items.clear()

    def __repr__(self) -> str:
        return f"ShoppingCart({self.item_count} items, total=${self.total:.2f})"


cart = ShoppingCart(max_items=10)
cart.add_item("Keyboard", 75.0)
cart.add_item("Mouse", 25.0, quantity=2)
cart.add_item("Keyboard", 75.0)  # increments existing
print(cart)        # ShoppingCart(4 items, total=$200.00)
print(cart.items)  # immutable tuple

# External code cannot break invariants
try:
    cart.add_item("Monitors", 500.0, quantity=20)
except ValueError as e:
    print(e)  # Cart cannot exceed 10 items
```

---

## 3. Abstraction in Python

Abstraction hides complex implementation details and exposes only what is necessary.
In Python, the primary tool for enforcing abstraction is the `abc` module.

### 3.1 The ABC Module

```python
from abc import ABC, abstractmethod


class Shape(ABC):
    """Abstract base class — cannot be instantiated."""

    @abstractmethod
    def area(self) -> float:
        """Subclasses MUST implement this."""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        ...

    def describe(self) -> str:
        """Concrete method available to all subclasses."""
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self._radius = radius

    def area(self) -> float:
        import math
        return math.pi * self._radius ** 2

    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self._radius


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        self._width = width
        self._height = height

    def area(self) -> float:
        return self._width * self._height

    def perimeter(self) -> float:
        return 2 * (self._width + self._height)


# Cannot instantiate abstract class
try:
    s = Shape()
except TypeError as e:
    print(e)  # Can't instantiate abstract class Shape with abstract methods area, perimeter

# Concrete subclasses work fine
shapes = [Circle(5), Rectangle(4, 6)]
for s in shapes:
    print(s.describe())
```

### 3.2 `@abstractmethod` and Abstract Properties

```python
from abc import ABC, abstractmethod


class Vehicle(ABC):
    @property
    @abstractmethod
    def max_speed(self) -> float:
        """Every vehicle must declare its max speed."""
        ...

    @abstractmethod
    def start_engine(self) -> str:
        ...

    @abstractmethod
    def stop_engine(self) -> str:
        ...


class Car(Vehicle):
    @property
    def max_speed(self) -> float:
        return 220.0

    def start_engine(self) -> str:
        return "Car engine started — vroom!"

    def stop_engine(self) -> str:
        return "Car engine stopped."


class ElectricScooter(Vehicle):
    @property
    def max_speed(self) -> float:
        return 45.0

    def start_engine(self) -> str:
        return "Electric scooter motor engaged — whirr"

    def stop_engine(self) -> str:
        return "Motor disengaged."


for v in [Car(), ElectricScooter()]:
    print(f"{v.__class__.__name__}: max {v.max_speed} km/h — {v.start_engine()}")
```

### 3.3 Abstract vs Concrete Classes

| Trait                  | Abstract Class             | Concrete Class            |
|------------------------|----------------------------|---------------------------|
| Instantiable?          | No                         | Yes                       |
| Has abstract methods?  | At least one               | None                      |
| Can have concrete code?| Yes (shared logic)         | Yes                       |
| Purpose                | Define a contract + shared behaviour | Full implementation |

**Rule of thumb:** If two or more classes share behaviour but differ in specifics,
extract the shared parts into an abstract base and push the varying parts into abstract
methods.

### 3.4 Levels of Abstraction in System Design

Good LLD designs have clear *layers* of abstraction. Each layer hides the complexity
beneath it.

```
┌──────────────────────────────────┐
│      Application Layer           │  ← orchestrates use cases
├──────────────────────────────────┤
│      Domain / Service Layer      │  ← business rules
├──────────────────────────────────┤
│      Repository / Data Layer     │  ← data access
├──────────────────────────────────┤
│      Infrastructure Layer        │  ← databases, APIs, file I/O
└──────────────────────────────────┘
```

Each layer communicates through abstractions (Protocols or ABCs), never concrete
implementations from a lower layer.

### 3.5 Example — Notification System with Proper Abstraction

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from enum import Enum, auto


class Priority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class Notification:
    recipient: str
    subject: str
    body: str
    priority: Priority = Priority.MEDIUM


# --- Abstract Layer ---
class NotificationSender(ABC):
    @abstractmethod
    def send(self, notification: Notification) -> bool:
        ...

    @abstractmethod
    def supports_priority(self, priority: Priority) -> bool:
        ...


class NotificationFilter(ABC):
    @abstractmethod
    def should_send(self, notification: Notification) -> bool:
        ...


# --- Concrete Senders ---
class EmailSender(NotificationSender):
    def send(self, notification: Notification) -> bool:
        print(f"  [Email] To: {notification.recipient} | Subject: {notification.subject}")
        return True

    def supports_priority(self, priority: Priority) -> bool:
        return True  # email handles all priorities


class SMSSender(NotificationSender):
    def send(self, notification: Notification) -> bool:
        print(f"  [SMS] To: {notification.recipient} | {notification.body[:50]}")
        return True

    def supports_priority(self, priority: Priority) -> bool:
        return priority in (Priority.HIGH, Priority.CRITICAL)


class PushNotificationSender(NotificationSender):
    def send(self, notification: Notification) -> bool:
        print(f"  [Push] To: {notification.recipient} | {notification.subject}")
        return True

    def supports_priority(self, priority: Priority) -> bool:
        return priority != Priority.LOW


# --- Concrete Filters ---
class QuietHoursFilter(NotificationFilter):
    def __init__(self, quiet_start: int = 22, quiet_end: int = 7) -> None:
        self._start = quiet_start
        self._end = quiet_end

    def should_send(self, notification: Notification) -> bool:
        from datetime import datetime
        hour = datetime.now().hour
        in_quiet = (hour >= self._start or hour < self._end)
        if in_quiet and notification.priority not in (Priority.HIGH, Priority.CRITICAL):
            print(f"  [Filter] Suppressed during quiet hours: {notification.subject}")
            return False
        return True


class RateLimitFilter(NotificationFilter):
    def __init__(self, max_per_minute: int = 10) -> None:
        self._max = max_per_minute
        self._count = 0

    def should_send(self, notification: Notification) -> bool:
        if self._count >= self._max:
            print(f"  [Filter] Rate limited: {notification.subject}")
            return False
        self._count += 1
        return True


# --- Orchestrator ---
class NotificationService:
    """
    High-level service that knows nothing about HOW notifications are sent or
    filtered. It depends only on abstractions.
    """

    def __init__(
        self,
        senders: List[NotificationSender],
        filters: List[NotificationFilter] | None = None,
    ) -> None:
        self._senders = senders
        self._filters = filters or []

    def notify(self, notification: Notification) -> None:
        print(f"Processing: {notification.subject} [{notification.priority.name}]")

        for f in self._filters:
            if not f.should_send(notification):
                return

        sent_via = []
        for sender in self._senders:
            if sender.supports_priority(notification.priority):
                if sender.send(notification):
                    sent_via.append(sender.__class__.__name__)

        print(f"  → Delivered via: {', '.join(sent_via) or 'none'}\n")


# --- Wiring and usage ---
service = NotificationService(
    senders=[EmailSender(), SMSSender(), PushNotificationSender()],
    filters=[RateLimitFilter(max_per_minute=5)],
)

service.notify(Notification("alice@co.com", "Welcome!", "Thanks for signing up", Priority.LOW))
service.notify(Notification("bob@co.com", "Server Down", "DB unreachable", Priority.CRITICAL))
service.notify(Notification("carol@co.com", "Weekly Digest", "Here's your summary", Priority.MEDIUM))
```

---

## 4. Polymorphism in Python

Polymorphism means "many forms" — a single interface can be backed by multiple
implementations. Python supports polymorphism more naturally than most languages because
of duck typing.

### 4.1 Duck Typing

> "If it walks like a duck and quacks like a duck, it is a duck."

Python does not require objects to share a common base class. Any object that has the
right methods can be used interchangeably.

```python
class Dog:
    def speak(self) -> str:
        return "Woof!"

class Cat:
    def speak(self) -> str:
        return "Meow!"

class Robot:
    def speak(self) -> str:
        return "BEEP BOOP"


def make_them_speak(entities: list) -> None:
    for entity in entities:
        print(entity.speak())


# No shared base class, but they all have .speak()
make_them_speak([Dog(), Cat(), Robot()])
```

### 4.2 Method Overriding

Subclasses provide specific implementations of methods defined in a parent class.

```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def sound(self) -> str:
        return "..."

    def describe(self) -> str:
        return f"{self.name} says {self.sound()}"


class Dog(Animal):
    def sound(self) -> str:
        return "Woof!"


class Cat(Animal):
    def sound(self) -> str:
        return "Meow!"


class Duck(Animal):
    def sound(self) -> str:
        return "Quack!"

    def describe(self) -> str:
        base = super().describe()
        return f"{base} (and can swim!)"


animals = [Dog("Rex"), Cat("Whiskers"), Duck("Donald")]
for a in animals:
    print(a.describe())
# Rex says Woof!
# Whiskers says Meow!
# Donald says Quack! (and can swim!)
```

### 4.3 Operator Overloading

Python lets classes define behaviour for built-in operators via dunder (double underscore)
methods.

```python
from __future__ import annotations


class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector:
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector:
        return self.__mul__(scalar)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __abs__(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __bool__(self) -> bool:
        return self.x != 0 or self.y != 0


v1 = Vector(3, 4)
v2 = Vector(1, 2)

print(v1 + v2)        # Vector(4, 6)
print(v1 - v2)        # Vector(2, 2)
print(v1 * 3)         # Vector(9, 12)
print(3 * v1)          # Vector(9, 12)  — __rmul__
print(abs(v1))         # 5.0
print(v1 == Vector(3, 4))  # True
print(bool(Vector(0, 0)))  # False
```

#### Common dunder methods for operator overloading

| Operator    | Method            | Example               |
|-------------|-------------------|-----------------------|
| `+`         | `__add__`         | `a + b`               |
| `-`         | `__sub__`         | `a - b`               |
| `*`         | `__mul__`         | `a * b`               |
| `==`        | `__eq__`          | `a == b`              |
| `!=`        | `__ne__`          | `a != b`              |
| `<`         | `__lt__`          | `a < b`               |
| `<=`        | `__le__`          | `a <= b`              |
| `len()`     | `__len__`         | `len(a)`              |
| `[]`        | `__getitem__`     | `a[key]`              |
| `in`        | `__contains__`    | `x in a`              |
| `str()`     | `__str__`         | `str(a)`              |
| `repr()`    | `__repr__`        | `repr(a)`             |
| `hash()`    | `__hash__`        | `hash(a)`             |
| `bool()`    | `__bool__`        | `bool(a)`             |
| `()`        | `__call__`        | `a()`                 |

### 4.4 Protocol-Based Polymorphism

Using `typing.Protocol`, you can define the *shape* required without inheritance:

```python
from typing import Protocol, List


class Renderable(Protocol):
    def render(self) -> str: ...


class HTMLWidget:
    def __init__(self, tag: str, content: str) -> None:
        self._tag = tag
        self._content = content

    def render(self) -> str:
        return f"<{self._tag}>{self._content}</{self._tag}>"


class MarkdownBlock:
    def __init__(self, text: str, level: int = 1) -> None:
        self._text = text
        self._level = level

    def render(self) -> str:
        return f"{'#' * self._level} {self._text}"


class PlainText:
    def __init__(self, text: str) -> None:
        self._text = text

    def render(self) -> str:
        return self._text


def render_page(components: List[Renderable]) -> str:
    return "\n".join(c.render() for c in components)


page = render_page([
    MarkdownBlock("Welcome", level=1),
    HTMLWidget("p", "This is a paragraph."),
    PlainText("--- Footer ---"),
])
print(page)
```

### 4.5 Runtime Polymorphism Patterns

#### Strategy pattern via callables

```python
from typing import Callable, List


SortKey = Callable[[dict], any]


def sort_users(users: List[dict], key_fn: SortKey, reverse: bool = False) -> List[dict]:
    return sorted(users, key=key_fn, reverse=reverse)


users = [
    {"name": "Charlie", "age": 30, "score": 85},
    {"name": "Alice", "age": 25, "score": 92},
    {"name": "Bob", "age": 28, "score": 88},
]

by_name  = lambda u: u["name"]
by_age   = lambda u: u["age"]
by_score = lambda u: u["score"]

print("By name: ", [u["name"] for u in sort_users(users, by_name)])
print("By age:  ", [u["name"] for u in sort_users(users, by_age)])
print("By score:", [u["name"] for u in sort_users(users, by_score, reverse=True)])
```

#### Dispatch table (replacing if/elif chains)

```python
from typing import Dict, Callable


class MathOperation:
    _operations: Dict[str, Callable[[float, float], float]] = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else float("inf"),
    }

    @classmethod
    def execute(cls, op: str, a: float, b: float) -> float:
        if op not in cls._operations:
            raise ValueError(f"Unknown operation: {op}")
        return cls._operations[op](a, b)

    @classmethod
    def register(cls, name: str, fn: Callable[[float, float], float]) -> None:
        cls._operations[name] = fn


print(MathOperation.execute("add", 10, 3))  # 13
print(MathOperation.execute("mul", 4, 5))   # 20

MathOperation.register("pow", lambda a, b: a ** b)
print(MathOperation.execute("pow", 2, 10))  # 1024
```

---

## 5. Protocols & Structural Typing

### 5.1 `typing.Protocol` Deep Dive

`Protocol` was introduced in PEP 544 (Python 3.8+). It brings **structural subtyping**
to Python's type system. A class is considered a subtype of a Protocol if it has the
matching attributes and methods — *no inheritance required*.

```python
from typing import Protocol, runtime_checkable


class Closeable(Protocol):
    def close(self) -> None: ...


class DatabaseConnection:
    def close(self) -> None:
        print("DB connection closed")

    def query(self, sql: str) -> list:
        return []


class FileHandle:
    def close(self) -> None:
        print("File closed")

    def read(self) -> bytes:
        return b""


def cleanup(resource: Closeable) -> None:
    """Accepts ANY object with a .close() method."""
    resource.close()


cleanup(DatabaseConnection())  # works
cleanup(FileHandle())          # works
```

### 5.2 `runtime_checkable`

By default, Protocol is a static-only concept. Adding `@runtime_checkable` lets you
use `isinstance` and `issubclass` checks at runtime.

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None: ...


class Circle:
    def draw(self) -> None:
        print("Drawing circle")


class Square:
    def draw(self) -> None:
        print("Drawing square")


class NotDrawable:
    def move(self) -> None:
        pass


print(isinstance(Circle(), Drawable))      # True
print(isinstance(NotDrawable(), Drawable))  # False

# Filter a list to only drawable objects
objects = [Circle(), NotDrawable(), Square()]
drawables = [obj for obj in objects if isinstance(obj, Drawable)]
for d in drawables:
    d.draw()
```

**Caveat:** `runtime_checkable` only checks method *names*, not signatures. Type
checkers (mypy, pyright) do full signature verification at static analysis time.

### 5.3 Protocol vs ABC Comparison

| Feature                    | Protocol                    | ABC                          |
|----------------------------|-----------------------------|------------------------------|
| Requires inheritance?      | No (structural)             | Yes (nominal)                |
| `isinstance` support       | With `@runtime_checkable`   | Yes (built-in)               |
| Can have concrete methods? | Yes                         | Yes                          |
| Works with third-party code| Yes (no changes needed)     | No (must subclass)           |
| Enforced at instantiation  | No (static checker only)    | Yes (`TypeError`)            |
| Best for                   | Loose coupling, duck typing | Framework hierarchies        |

#### When to choose what

- **Protocol**: When you want to *describe a shape* that existing or third-party classes
  already satisfy. Ideal for LLD where you want maximum decoupling.
- **ABC**: When you control the class hierarchy and want *runtime enforcement* plus shared
  concrete logic.

### 5.4 Structural Subtyping Explained

In **nominal typing** (Java/C++), `class Dog extends Animal` means Dog IS-A Animal.
In **structural typing**, if Dog has the same methods and attributes that the protocol
demands, Dog satisfies the protocol — regardless of its inheritance tree.

```python
from typing import Protocol


class Hashable(Protocol):
    def __hash__(self) -> int: ...


class UserID:
    def __init__(self, value: int) -> None:
        self._value = value

    def __hash__(self) -> int:
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UserID) and self._value == other._value


def cache_key(obj: Hashable) -> int:
    return hash(obj)


print(cache_key(UserID(42)))   # works — UserID structurally satisfies Hashable
print(cache_key("hello"))      # works — str has __hash__
print(cache_key(3.14))         # works — float has __hash__
```

### 5.5 When to Use Protocols in LLD

1. **Repository interfaces** — `UserRepository` protocol lets you swap DB, file, or
   in-memory implementations.
2. **Strategy injection** — Define the *shape* of a strategy without forcing inheritance.
3. **Plugin systems** — Third-party plugins satisfy your Protocol without importing your
   base class.
4. **Testing** — Create minimal test doubles that match the Protocol.
5. **Cross-boundary contracts** — Define the interface between microservices or modules
   without shared base classes.

### 5.6 Real Example — Plugin System Using Protocols

```python
from __future__ import annotations
from typing import Protocol, Dict, Type, runtime_checkable
import importlib


@runtime_checkable
class Plugin(Protocol):
    """Any class with these methods is a valid plugin."""
    name: str

    def initialize(self) -> None: ...
    def execute(self, data: dict) -> dict: ...
    def shutdown(self) -> None: ...


# --- Concrete plugins (no inheritance!) ---
class LoggingPlugin:
    name = "logging"

    def initialize(self) -> None:
        print(f"[{self.name}] Initialized")

    def execute(self, data: dict) -> dict:
        print(f"[{self.name}] Processing: {data}")
        return {**data, "logged": True}

    def shutdown(self) -> None:
        print(f"[{self.name}] Shut down")


class ValidationPlugin:
    name = "validation"

    def initialize(self) -> None:
        print(f"[{self.name}] Initialized")

    def execute(self, data: dict) -> dict:
        if "email" not in data:
            raise ValueError("Missing required field: email")
        print(f"[{self.name}] Validated: {data}")
        return {**data, "validated": True}

    def shutdown(self) -> None:
        print(f"[{self.name}] Shut down")


class MetricsPlugin:
    name = "metrics"

    def initialize(self) -> None:
        self._count = 0
        print(f"[{self.name}] Initialized")

    def execute(self, data: dict) -> dict:
        self._count += 1
        print(f"[{self.name}] Request #{self._count}")
        return {**data, "request_number": self._count}

    def shutdown(self) -> None:
        print(f"[{self.name}] Total requests: {self._count}")


# --- Plugin Manager ---
class PluginManager:
    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if not isinstance(plugin, Plugin):
            raise TypeError(f"{plugin} does not satisfy the Plugin protocol")
        self._plugins[plugin.name] = plugin

    def initialize_all(self) -> None:
        for plugin in self._plugins.values():
            plugin.initialize()

    def run_pipeline(self, data: dict) -> dict:
        result = data
        for plugin in self._plugins.values():
            result = plugin.execute(result)
        return result

    def shutdown_all(self) -> None:
        for plugin in reversed(list(self._plugins.values())):
            plugin.shutdown()


# --- Usage ---
manager = PluginManager()
manager.register(LoggingPlugin())
manager.register(ValidationPlugin())
manager.register(MetricsPlugin())

manager.initialize_all()

result = manager.run_pipeline({"email": "alice@example.com", "action": "signup"})
print(f"\nFinal result: {result}")

manager.shutdown_all()
```

---

## 6. Interface Segregation Using Protocols

The Interface Segregation Principle (ISP) states: *No client should be forced to depend
on methods it does not use.*

### 6.1 The Fat Interface Problem

```python
from abc import ABC, abstractmethod


class Machine(ABC):
    """Fat interface — forces every machine to implement everything."""

    @abstractmethod
    def print_document(self, doc: str) -> None: ...

    @abstractmethod
    def scan_document(self) -> str: ...

    @abstractmethod
    def fax_document(self, doc: str, number: str) -> None: ...

    @abstractmethod
    def staple_document(self, doc: str) -> None: ...


class OldPrinter(Machine):
    def print_document(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_document(self) -> str:
        raise NotImplementedError("Old printer can't scan!")  # violation!

    def fax_document(self, doc: str, number: str) -> None:
        raise NotImplementedError("Old printer can't fax!")   # violation!

    def staple_document(self, doc: str) -> None:
        raise NotImplementedError("Old printer can't staple!")  # violation!
```

This is a textbook ISP violation. `OldPrinter` is forced to implement methods it cannot
support, leading to `NotImplementedError` landmines.

### 6.2 Splitting Interfaces with Protocols

```python
from typing import Protocol


class Printer(Protocol):
    def print_document(self, doc: str) -> None: ...


class Scanner(Protocol):
    def scan_document(self) -> str: ...


class Faxer(Protocol):
    def fax_document(self, doc: str, number: str) -> None: ...


class Stapler(Protocol):
    def staple_document(self, doc: str) -> None: ...


# --- Concrete implementations only implement what they support ---

class SimplePrinter:
    def print_document(self, doc: str) -> None:
        print(f"[SimplePrinter] {doc}")


class AllInOneMachine:
    def print_document(self, doc: str) -> None:
        print(f"[AllInOne] Printing: {doc}")

    def scan_document(self) -> str:
        return "[AllInOne] Scanned document content"

    def fax_document(self, doc: str, number: str) -> None:
        print(f"[AllInOne] Faxing to {number}: {doc}")

    def staple_document(self, doc: str) -> None:
        print(f"[AllInOne] Stapling: {doc}")


class ModernPrinterScanner:
    def print_document(self, doc: str) -> None:
        print(f"[Modern] Printing: {doc}")

    def scan_document(self) -> str:
        return "[Modern] Scanned content"


# --- Functions depend only on what they need ---
def print_job(printer: Printer) -> None:
    printer.print_document("Quarterly Report")


def scan_job(scanner: Scanner) -> str:
    return scanner.scan_document()


def print_and_scan(device: Printer) -> None:
    """Only needs printing capability."""
    device.print_document("Invoice")


# All of these work without forcing unnecessary implementations
print_job(SimplePrinter())
print_job(AllInOneMachine())
print_job(ModernPrinterScanner())

print(scan_job(AllInOneMachine()))
print(scan_job(ModernPrinterScanner()))
```

### 6.3 Multiple Protocol Inheritance

You can compose Protocols to create combined interfaces when a function truly needs
multiple capabilities:

```python
from typing import Protocol


class Readable(Protocol):
    def read(self) -> str: ...

class Writable(Protocol):
    def write(self, data: str) -> None: ...

class Seekable(Protocol):
    def seek(self, position: int) -> None: ...


class ReadWritable(Readable, Writable, Protocol):
    """Combined protocol for read-write capable objects."""
    ...


class ReadWriteSeekable(Readable, Writable, Seekable, Protocol):
    """Combined protocol for full random-access I/O."""
    ...


class InMemoryBuffer:
    def __init__(self) -> None:
        self._data = ""
        self._pos = 0

    def read(self) -> str:
        return self._data[self._pos:]

    def write(self, data: str) -> None:
        self._data += data

    def seek(self, position: int) -> None:
        self._pos = min(position, len(self._data))


def copy_data(source: Readable, dest: Writable) -> None:
    dest.write(source.read())


def process_file(f: ReadWriteSeekable) -> None:
    f.write("Hello, World!")
    f.seek(0)
    print(f.read())


buf = InMemoryBuffer()
process_file(buf)
```

### 6.4 Example — Printer/Scanner/Fax Segregation (Full)

```python
from typing import Protocol, List


class Printable(Protocol):
    def print_doc(self, doc: str) -> None: ...

class Scannable(Protocol):
    def scan_doc(self) -> str: ...

class Faxable(Protocol):
    def fax_doc(self, doc: str, number: str) -> None: ...

class Copyable(Printable, Scannable, Protocol):
    """A device that can copy must be able to print and scan."""
    ...


class BasicPrinter:
    def print_doc(self, doc: str) -> None:
        print(f"🖨️ Printing: {doc}")


class OfficeCopier:
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_doc(self) -> str:
        content = "Scanned page content"
        print(f"Scanning... got: {content}")
        return content


class EnterpriseDevice:
    def print_doc(self, doc: str) -> None:
        print(f"[Enterprise] Print: {doc}")

    def scan_doc(self) -> str:
        return "[Enterprise] Scanned content"

    def fax_doc(self, doc: str, number: str) -> None:
        print(f"[Enterprise] Fax to {number}: {doc}")


def batch_print(printers: List[Printable], document: str) -> None:
    for p in printers:
        p.print_doc(document)


def copy_document(copier: Copyable) -> None:
    content = copier.scan_doc()
    copier.print_doc(content)


# Works — each function only requires the capabilities it uses
batch_print([BasicPrinter(), OfficeCopier(), EnterpriseDevice()], "Annual Report")
copy_document(OfficeCopier())
copy_document(EnterpriseDevice())
```

### 6.5 Best Practices

1. **Start with fine-grained Protocols.** Compose them when needed — don't start big.
2. **One role per Protocol.** `Printable`, `Scannable`, `Faxable` — not `Machine`.
3. **Functions should accept the *narrowest* Protocol** that covers their needs.
4. **Avoid "marker" Protocols** with zero methods — they add noise without value.
5. **Name Protocols after capabilities**, not implementations: `Serializable`,
   `Renderable`, `Cacheable`.

---

## 7. Dependency Inversion in Python

The Dependency Inversion Principle (DIP):

> A. High-level modules should not depend on low-level modules. Both should depend on
>    abstractions.
> B. Abstractions should not depend on details. Details should depend on abstractions.

### 7.1 High-Level Modules Should Not Depend on Low-Level Modules

**Violation:**

```python
# Low-level module
class MySQLDatabase:
    def execute(self, query: str) -> list:
        print(f"[MySQL] Executing: {query}")
        return [{"id": 1, "name": "Alice"}]


# High-level module directly depends on low-level module
class UserService:
    def __init__(self) -> None:
        self._db = MySQLDatabase()  # tightly coupled!

    def get_user(self, user_id: int) -> dict:
        return self._db.execute(f"SELECT * FROM users WHERE id = {user_id}")[0]
```

**Fixed with DIP:**

```python
from typing import Protocol, List


# Abstraction (owned by the high-level module)
class Database(Protocol):
    def execute(self, query: str) -> list: ...


# Low-level module implements the abstraction
class MySQLDatabase:
    def execute(self, query: str) -> list:
        print(f"[MySQL] {query}")
        return [{"id": 1, "name": "Alice"}]


class PostgresDatabase:
    def execute(self, query: str) -> list:
        print(f"[Postgres] {query}")
        return [{"id": 1, "name": "Alice"}]


class InMemoryDatabase:
    def __init__(self) -> None:
        self._data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def execute(self, query: str) -> list:
        return self._data


# High-level module depends on the abstraction
class UserService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_user(self, user_id: int) -> dict:
        return self._db.execute(f"SELECT * FROM users WHERE id = {user_id}")[0]


# Wiring can use any implementation
service = UserService(PostgresDatabase())
print(service.get_user(1))
```

### 7.2 Abstractions Should Not Depend on Details

The abstraction (`Database` Protocol) defines the interface. It knows nothing about
MySQL, Postgres, or in-memory storage. The concrete classes (details) conform to the
abstraction — not the other way around.

### 7.3 Python Implementation with Protocols

```python
from typing import Protocol, List
from dataclasses import dataclass


@dataclass
class Email:
    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, email: Email) -> bool: ...


class EmailTemplateEngine(Protocol):
    def render(self, template_name: str, context: dict) -> str: ...


# High-level module
class WelcomeEmailService:
    def __init__(self, sender: EmailSender, template_engine: EmailTemplateEngine) -> None:
        self._sender = sender
        self._template_engine = template_engine

    def send_welcome(self, user_email: str, user_name: str) -> bool:
        body = self._template_engine.render("welcome", {"name": user_name})
        email = Email(to=user_email, subject="Welcome!", body=body)
        return self._sender.send(email)


# Low-level modules
class SMTPSender:
    def send(self, email: Email) -> bool:
        print(f"[SMTP] Sending to {email.to}: {email.subject}")
        return True


class JinjaTemplateEngine:
    def render(self, template_name: str, context: dict) -> str:
        return f"Hello {context.get('name', 'User')}! Welcome aboard."


class SendGridSender:
    def send(self, email: Email) -> bool:
        print(f"[SendGrid API] Sending to {email.to}: {email.subject}")
        return True


# Wiring
service = WelcomeEmailService(SMTPSender(), JinjaTemplateEngine())
service.send_welcome("alice@example.com", "Alice")

service2 = WelcomeEmailService(SendGridSender(), JinjaTemplateEngine())
service2.send_welcome("bob@example.com", "Bob")
```

### 7.4 Example — Repository Pattern with DIP

```python
from __future__ import annotations
from typing import Protocol, Optional, List
from dataclasses import dataclass, field
import uuid


@dataclass
class Product:
    product_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    price: float = 0.0
    category: str = ""


class ProductRepository(Protocol):
    def save(self, product: Product) -> None: ...
    def find_by_id(self, product_id: str) -> Optional[Product]: ...
    def find_all(self) -> List[Product]: ...
    def delete(self, product_id: str) -> bool: ...


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._store: dict[str, Product] = {}

    def save(self, product: Product) -> None:
        self._store[product.product_id] = product

    def find_by_id(self, product_id: str) -> Optional[Product]:
        return self._store.get(product_id)

    def find_all(self) -> List[Product]:
        return list(self._store.values())

    def delete(self, product_id: str) -> bool:
        return self._store.pop(product_id, None) is not None


class SQLProductRepository:
    def save(self, product: Product) -> None:
        print(f"[SQL] INSERT INTO products VALUES ('{product.product_id}', '{product.name}', {product.price})")

    def find_by_id(self, product_id: str) -> Optional[Product]:
        print(f"[SQL] SELECT * FROM products WHERE id = '{product_id}'")
        return Product(product_id=product_id, name="Mock Product", price=9.99)

    def find_all(self) -> List[Product]:
        print("[SQL] SELECT * FROM products")
        return []

    def delete(self, product_id: str) -> bool:
        print(f"[SQL] DELETE FROM products WHERE id = '{product_id}'")
        return True


class ProductService:
    """High-level service depending on ProductRepository abstraction."""

    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def create_product(self, name: str, price: float, category: str) -> Product:
        product = Product(name=name, price=price, category=category)
        self._repo.save(product)
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._repo.find_by_id(product_id)

    def list_products(self) -> List[Product]:
        return self._repo.find_all()


# In tests — use in-memory
repo = InMemoryProductRepository()
service = ProductService(repo)
p = service.create_product("Widget", 12.99, "Gadgets")
print(service.get_product(p.product_id))

# In production — use SQL
prod_service = ProductService(SQLProductRepository())
prod_service.create_product("Widget", 12.99, "Gadgets")
```

### 7.5 Layered Architecture Example

```python
from typing import Protocol, List, Optional
from dataclasses import dataclass


# ============================================================
# Layer 1: Domain (innermost — no external dependencies)
# ============================================================
@dataclass
class Order:
    order_id: str
    customer_id: str
    items: List[str]
    total: float
    status: str = "pending"


# ============================================================
# Layer 2: Application (depends on domain abstractions)
# ============================================================
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def find_by_id(self, order_id: str) -> Optional[Order]: ...

class PaymentProcessor(Protocol):
    def charge(self, customer_id: str, amount: float) -> bool: ...

class NotificationService(Protocol):
    def notify(self, customer_id: str, message: str) -> None: ...


class PlaceOrderUseCase:
    def __init__(
        self,
        repo: OrderRepository,
        payment: PaymentProcessor,
        notifier: NotificationService,
    ) -> None:
        self._repo = repo
        self._payment = payment
        self._notifier = notifier

    def execute(self, order: Order) -> Order:
        charged = self._payment.charge(order.customer_id, order.total)
        if not charged:
            order.status = "payment_failed"
            return order

        order.status = "confirmed"
        self._repo.save(order)
        self._notifier.notify(order.customer_id, f"Order {order.order_id} confirmed!")
        return order


# ============================================================
# Layer 3: Infrastructure (implements the abstractions)
# ============================================================
class DictOrderRepository:
    def __init__(self) -> None:
        self._store: dict = {}

    def save(self, order: Order) -> None:
        self._store[order.order_id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)


class FakePaymentProcessor:
    def charge(self, customer_id: str, amount: float) -> bool:
        print(f"[Payment] Charging {customer_id} ${amount}")
        return True


class ConsoleNotifier:
    def notify(self, customer_id: str, message: str) -> None:
        print(f"[Notify {customer_id}] {message}")


# ============================================================
# Composition Root (wiring everything together)
# ============================================================
use_case = PlaceOrderUseCase(
    repo=DictOrderRepository(),
    payment=FakePaymentProcessor(),
    notifier=ConsoleNotifier(),
)

order = Order(order_id="ORD-001", customer_id="CUST-42", items=["Laptop", "Mouse"], total=1299.99)
result = use_case.execute(order)
print(f"Order status: {result.status}")
```

---

## 8. Open/Closed Principle

> Software entities should be **open for extension** but **closed for modification**.

You should be able to add new behaviour without changing existing, tested code.

### 8.1 Open for Extension, Closed for Modification

**Violation — every new discount type requires modifying existing code:**

```python
# BAD: violates OCP
class DiscountCalculator:
    def calculate(self, order_total: float, discount_type: str) -> float:
        if discount_type == "percentage":
            return order_total * 0.10
        elif discount_type == "flat":
            return 25.0
        elif discount_type == "buy_one_get_one":
            return order_total * 0.50
        # Adding a new type means editing this method (modification!)
        else:
            return 0.0
```

### 8.2 Strategy Pattern Implementation

```python
from typing import Protocol


class DiscountStrategy(Protocol):
    def calculate(self, order_total: float) -> float: ...


class PercentageDiscount:
    def __init__(self, percent: float) -> None:
        self._percent = percent

    def calculate(self, order_total: float) -> float:
        return order_total * (self._percent / 100)


class FlatDiscount:
    def __init__(self, amount: float) -> None:
        self._amount = amount

    def calculate(self, order_total: float) -> float:
        return min(self._amount, order_total)


class BuyOneGetOneFree:
    def calculate(self, order_total: float) -> float:
        return order_total * 0.50


class TieredDiscount:
    """New strategy added WITHOUT modifying any existing code."""
    def calculate(self, order_total: float) -> float:
        if order_total > 500:
            return order_total * 0.15
        elif order_total > 200:
            return order_total * 0.10
        elif order_total > 100:
            return order_total * 0.05
        return 0.0


class SeasonalDiscount:
    def __init__(self, base_percent: float, seasonal_bonus: float) -> None:
        self._base = base_percent
        self._bonus = seasonal_bonus

    def calculate(self, order_total: float) -> float:
        return order_total * ((self._base + self._bonus) / 100)


# The calculator is CLOSED for modification — it never needs to change
class DiscountCalculator:
    def __init__(self, strategy: DiscountStrategy) -> None:
        self._strategy = strategy

    def apply_discount(self, order_total: float) -> float:
        discount = self._strategy.calculate(order_total)
        return max(0, order_total - discount)


# Usage
calc = DiscountCalculator(PercentageDiscount(10))
print(f"10% off $200: ${calc.apply_discount(200):.2f}")  # $180.00

calc = DiscountCalculator(TieredDiscount())
print(f"Tiered on $600: ${calc.apply_discount(600):.2f}")  # $510.00

calc = DiscountCalculator(SeasonalDiscount(10, 5))
print(f"Seasonal on $300: ${calc.apply_discount(300):.2f}")  # $255.00
```

### 8.3 Plugin Architecture

```python
from typing import Protocol, Dict, Callable, Any
import functools


class Middleware(Protocol):
    def process(self, request: dict, next_handler: Callable) -> dict: ...


class AuthMiddleware:
    def process(self, request: dict, next_handler: Callable) -> dict:
        if "auth_token" not in request:
            return {"error": "Unauthorized", "status": 401}
        print("[Auth] Token verified")
        return next_handler(request)


class LoggingMiddleware:
    def process(self, request: dict, next_handler: Callable) -> dict:
        print(f"[Log] Request: {request.get('path', '/')}")
        response = next_handler(request)
        print(f"[Log] Response status: {response.get('status', 200)}")
        return response


class RateLimitMiddleware:
    def __init__(self, max_requests: int = 100) -> None:
        self._count = 0
        self._max = max_requests

    def process(self, request: dict, next_handler: Callable) -> dict:
        self._count += 1
        if self._count > self._max:
            return {"error": "Rate limited", "status": 429}
        return next_handler(request)


class WebServer:
    """Open for extension (add new middleware) without modifying this class."""

    def __init__(self) -> None:
        self._middlewares: list[Middleware] = []
        self._routes: Dict[str, Callable] = {}

    def use(self, middleware: Middleware) -> None:
        self._middlewares.append(middleware)

    def route(self, path: str, handler: Callable) -> None:
        self._routes[path] = handler

    def handle_request(self, request: dict) -> dict:
        path = request.get("path", "/")
        handler = self._routes.get(path, lambda r: {"status": 404, "error": "Not Found"})

        chain = handler
        for mw in reversed(self._middlewares):
            prev = chain
            chain = functools.partial(mw.process, next_handler=prev)

        return chain(request)


# Setup
app = WebServer()
app.use(LoggingMiddleware())
app.use(AuthMiddleware())
app.use(RateLimitMiddleware(max_requests=5))

app.route("/api/users", lambda r: {"status": 200, "data": [{"name": "Alice"}]})
app.route("/api/health", lambda r: {"status": 200, "data": "OK"})

# Test
print(app.handle_request({"path": "/api/users", "auth_token": "abc123"}))
print(app.handle_request({"path": "/api/health"}))  # missing auth
```

### 8.4 Example — Discount Calculator That Follows OCP

Combining multiple discount strategies via composition:

```python
from typing import Protocol, List


class DiscountRule(Protocol):
    def applies_to(self, order: dict) -> bool: ...
    def calculate(self, order: dict) -> float: ...


class NewCustomerDiscount:
    def applies_to(self, order: dict) -> bool:
        return order.get("is_new_customer", False)

    def calculate(self, order: dict) -> float:
        return order["total"] * 0.15


class LoyaltyDiscount:
    def applies_to(self, order: dict) -> bool:
        return order.get("loyalty_years", 0) >= 2

    def calculate(self, order: dict) -> float:
        years = order["loyalty_years"]
        return order["total"] * min(0.02 * years, 0.10)


class BulkDiscount:
    def applies_to(self, order: dict) -> bool:
        return order.get("item_count", 0) >= 10

    def calculate(self, order: dict) -> float:
        return order["total"] * 0.08


class CouponDiscount:
    VALID_COUPONS = {"SAVE20": 20.0, "FLAT50": 50.0, "VIP10": 10.0}

    def applies_to(self, order: dict) -> bool:
        return order.get("coupon") in self.VALID_COUPONS

    def calculate(self, order: dict) -> float:
        return self.VALID_COUPONS[order["coupon"]]


class DiscountEngine:
    """
    Closed for modification: you never edit this class.
    Open for extension: just create a new DiscountRule class.
    """

    def __init__(self, rules: List[DiscountRule]) -> None:
        self._rules = rules

    def best_discount(self, order: dict) -> float:
        applicable = [r.calculate(order) for r in self._rules if r.applies_to(order)]
        return max(applicable, default=0.0)

    def total_discount(self, order: dict) -> float:
        return sum(r.calculate(order) for r in self._rules if r.applies_to(order))


engine = DiscountEngine([
    NewCustomerDiscount(),
    LoyaltyDiscount(),
    BulkDiscount(),
    CouponDiscount(),
])

order = {
    "total": 500.0,
    "is_new_customer": True,
    "loyalty_years": 0,
    "item_count": 15,
    "coupon": "SAVE20",
}

print(f"Best single discount: ${engine.best_discount(order):.2f}")   # $75.00 (15%)
print(f"Combined discounts:   ${engine.total_discount(order):.2f}")  # $75+$40+$20 = $135
```

### 8.5 Anti-Patterns That Violate OCP

| Anti-Pattern                     | Why it violates OCP                              |
|----------------------------------|--------------------------------------------------|
| Giant if/elif chains on types    | Every new type modifies the function             |
| `isinstance` checks scattered   | New subclass → update every check site           |
| Hardcoded class names            | Can't swap implementations without editing code  |
| Monolithic functions             | Any new feature means editing a 500-line function|
| Enum-driven dispatch without map | Adding an enum value forces code changes          |

---

## 9. Error Handling Strategies

### 9.1 Exception Hierarchy Design

Design domain-specific exceptions that form a clean hierarchy:

```python
class AppError(Exception):
    """Root exception for the entire application."""

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.code = code


class DomainError(AppError):
    """Errors related to business rule violations."""
    pass


class InfrastructureError(AppError):
    """Errors from external systems (DB, APIs, file I/O)."""
    pass


class ValidationError(DomainError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation failed for '{field}': {message}", code="VALIDATION_ERROR")
        self.field = field


class EntityNotFoundError(DomainError):
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} with id '{entity_id}' not found", code="NOT_FOUND")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(DomainError):
    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(f"{entity_type} '{identifier}' already exists", code="DUPLICATE")


class DatabaseError(InfrastructureError):
    pass


class ExternalAPIError(InfrastructureError):
    def __init__(self, service: str, status_code: int, message: str) -> None:
        super().__init__(f"[{service}] HTTP {status_code}: {message}", code="EXTERNAL_API_ERROR")
        self.service = service
        self.status_code = status_code


class RateLimitError(InfrastructureError):
    def __init__(self, service: str, retry_after: int) -> None:
        super().__init__(f"Rate limited by {service}. Retry after {retry_after}s", code="RATE_LIMITED")
        self.retry_after = retry_after
```

### 9.2 Custom Exceptions for Domains

```python
class PaymentError(DomainError):
    pass

class InsufficientFundsError(PaymentError):
    def __init__(self, required: float, available: float) -> None:
        super().__init__(
            f"Insufficient funds: required ${required:.2f}, available ${available:.2f}",
            code="INSUFFICIENT_FUNDS",
        )
        self.required = required
        self.available = available

class PaymentDeclinedError(PaymentError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Payment declined: {reason}", code="PAYMENT_DECLINED")

class InvalidCardError(PaymentError):
    def __init__(self) -> None:
        super().__init__("Invalid card details provided", code="INVALID_CARD")


# Usage in service
class WalletService:
    def __init__(self, balance: float) -> None:
        self._balance = balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValidationError("amount", "Must be positive")
        if amount > self._balance:
            raise InsufficientFundsError(required=amount, available=self._balance)
        self._balance -= amount
        return self._balance

    @property
    def balance(self) -> float:
        return self._balance


wallet = WalletService(100.0)
try:
    wallet.withdraw(150.0)
except InsufficientFundsError as e:
    print(f"Error [{e.code}]: {e}")
    print(f"  Need ${e.required:.2f}, have ${e.available:.2f}")
```

### 9.3 Result Pattern (Success / Failure)

An alternative to exceptions for expected failure cases. Especially useful when failures
are common and expected (validation, business rules) rather than exceptional.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False

    def map(self, fn: Callable[[T], any]) -> Result:
        return Success(fn(self.value))

    def flat_map(self, fn: Callable[[T], Result]) -> Result:
        return fn(self.value)

    def or_else(self, default: T) -> T:
        return self.value


@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True

    def map(self, fn: Callable) -> Result:
        return self  # propagate the failure

    def flat_map(self, fn: Callable) -> Result:
        return self

    def or_else(self, default) -> any:
        return default


Result = Success | Failure


# --- Usage ---
def parse_age(value: str) -> Result:
    try:
        age = int(value)
    except ValueError:
        return Failure(f"'{value}' is not a valid integer")
    if age < 0 or age > 150:
        return Failure(f"Age {age} is out of range (0-150)")
    return Success(age)


def categorize_age(age: int) -> str:
    if age < 18:
        return "minor"
    elif age < 65:
        return "adult"
    return "senior"


# Chain operations
result = parse_age("25").map(categorize_age)
print(result)  # Success(value='adult')

result = parse_age("abc")
print(result)  # Failure(error="'abc' is not a valid integer")

result = parse_age("-5")
print(result)  # Failure(error='Age -5 is out of range (0-150)')

# Using or_else for defaults
category = parse_age("30").map(categorize_age).or_else("unknown")
print(f"Category: {category}")  # adult

category = parse_age("xyz").map(categorize_age).or_else("unknown")
print(f"Category: {category}")  # unknown
```

### 9.4 Error Propagation Strategies

```python
from typing import Protocol, Optional
import logging

logger = logging.getLogger(__name__)


class UserRepository(Protocol):
    def find_by_email(self, email: str) -> Optional[dict]: ...


class InMemoryUserRepo:
    _users = {"alice@co.com": {"id": 1, "name": "Alice", "email": "alice@co.com"}}

    def find_by_email(self, email: str) -> Optional[dict]:
        return self._users.get(email)


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_user_by_email(self, email: str) -> dict:
        if not email or "@" not in email:
            raise ValidationError("email", "Invalid email format")

        user = self._repo.find_by_email(email)
        if user is None:
            raise EntityNotFoundError("User", email)

        return user


class UserController:
    """
    Top-level handler — catches domain errors and converts them
    to user-friendly responses. Infrastructure errors bubble up
    to the global handler.
    """

    def __init__(self, service: UserService) -> None:
        self._service = service

    def get_user(self, email: str) -> dict:
        try:
            user = self._service.get_user_by_email(email)
            return {"status": 200, "data": user}
        except ValidationError as e:
            return {"status": 400, "error": str(e), "code": e.code}
        except EntityNotFoundError as e:
            return {"status": 404, "error": str(e), "code": e.code}
        except AppError as e:
            logger.error(f"Unexpected app error: {e}", exc_info=True)
            return {"status": 500, "error": "Internal server error"}


controller = UserController(UserService(InMemoryUserRepo()))

print(controller.get_user("alice@co.com"))    # 200
print(controller.get_user("unknown@co.com"))  # 404
print(controller.get_user("invalid"))         # 400
```

### 9.5 Graceful Degradation

```python
from typing import Protocol, Optional, List
import time


class RecommendationEngine(Protocol):
    def recommend(self, user_id: str) -> List[str]: ...


class MLRecommendationEngine:
    def recommend(self, user_id: str) -> List[str]:
        # Simulates an ML service that might be slow or fail
        raise ConnectionError("ML service unavailable")


class PopularItemsFallback:
    def recommend(self, user_id: str) -> List[str]:
        return ["Best Seller #1", "Trending Item", "Editor's Pick"]


class RecommendationService:
    def __init__(
        self,
        primary: RecommendationEngine,
        fallback: RecommendationEngine,
        timeout: float = 2.0,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._timeout = timeout

    def get_recommendations(self, user_id: str) -> List[str]:
        try:
            return self._primary.recommend(user_id)
        except Exception as e:
            print(f"[Degradation] Primary engine failed ({e}), using fallback")
            return self._fallback.recommend(user_id)


service = RecommendationService(
    primary=MLRecommendationEngine(),
    fallback=PopularItemsFallback(),
)

recs = service.get_recommendations("user-42")
print(f"Recommendations: {recs}")
```

### 9.6 Example — Order Processing with Proper Error Handling

```python
from __future__ import annotations
from typing import Protocol, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid


class OrderStatus(Enum):
    PENDING = auto()
    VALIDATED = auto()
    PAID = auto()
    SHIPPED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class OrderItem:
    product_id: str
    name: str
    price: float
    quantity: int


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    customer_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    failure_reason: str = ""

    @property
    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)


# Exceptions
class OrderError(Exception):
    pass

class OrderValidationError(OrderError):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")

class PaymentFailedError(OrderError):
    pass

class InventoryError(OrderError):
    pass


# Protocols
class InventoryService(Protocol):
    def check_availability(self, product_id: str, quantity: int) -> bool: ...
    def reserve(self, product_id: str, quantity: int) -> bool: ...
    def release(self, product_id: str, quantity: int) -> None: ...

class PaymentService(Protocol):
    def charge(self, customer_id: str, amount: float) -> str: ...
    def refund(self, transaction_id: str) -> bool: ...


# Concrete implementations
class SimpleInventory:
    def __init__(self) -> None:
        self._stock = {"P001": 10, "P002": 5, "P003": 0}

    def check_availability(self, product_id: str, quantity: int) -> bool:
        return self._stock.get(product_id, 0) >= quantity

    def reserve(self, product_id: str, quantity: int) -> bool:
        if not self.check_availability(product_id, quantity):
            return False
        self._stock[product_id] -= quantity
        return True

    def release(self, product_id: str, quantity: int) -> None:
        self._stock[product_id] = self._stock.get(product_id, 0) + quantity


class SimplePayment:
    def charge(self, customer_id: str, amount: float) -> str:
        if amount > 10000:
            raise PaymentFailedError(f"Amount ${amount} exceeds limit")
        return f"txn_{uuid.uuid4().hex[:8]}"

    def refund(self, transaction_id: str) -> bool:
        print(f"Refunded {transaction_id}")
        return True


class OrderProcessor:
    def __init__(self, inventory: InventoryService, payment: PaymentService) -> None:
        self._inventory = inventory
        self._payment = payment

    def process(self, order: Order) -> Order:
        try:
            self._validate(order)
            order.status = OrderStatus.VALIDATED

            self._reserve_inventory(order)
            self._process_payment(order)
            order.status = OrderStatus.PAID

            print(f"Order {order.order_id} processed successfully!")
            return order

        except OrderValidationError as e:
            order.status = OrderStatus.FAILED
            order.failure_reason = str(e)
            print(f"Validation error: {e}")
            return order

        except InventoryError as e:
            order.status = OrderStatus.FAILED
            order.failure_reason = str(e)
            print(f"Inventory error: {e}")
            return order

        except PaymentFailedError as e:
            self._rollback_inventory(order)
            order.status = OrderStatus.FAILED
            order.failure_reason = str(e)
            print(f"Payment error (inventory rolled back): {e}")
            return order

    def _validate(self, order: Order) -> None:
        errors = []
        if not order.customer_id:
            errors.append("Customer ID is required")
        if not order.items:
            errors.append("Order must have at least one item")
        for item in order.items:
            if item.quantity <= 0:
                errors.append(f"Invalid quantity for {item.name}")
            if item.price < 0:
                errors.append(f"Invalid price for {item.name}")
        if errors:
            raise OrderValidationError(errors)

    def _reserve_inventory(self, order: Order) -> None:
        reserved = []
        try:
            for item in order.items:
                if not self._inventory.reserve(item.product_id, item.quantity):
                    raise InventoryError(f"Insufficient stock for {item.name} (product {item.product_id})")
                reserved.append(item)
        except InventoryError:
            for item in reserved:
                self._inventory.release(item.product_id, item.quantity)
            raise

    def _process_payment(self, order: Order) -> None:
        self._payment.charge(order.customer_id, order.total)

    def _rollback_inventory(self, order: Order) -> None:
        for item in order.items:
            self._inventory.release(item.product_id, item.quantity)


# --- Usage ---
processor = OrderProcessor(SimpleInventory(), SimplePayment())

good_order = Order(
    customer_id="C001",
    items=[
        OrderItem("P001", "Widget", 29.99, 2),
        OrderItem("P002", "Gadget", 49.99, 1),
    ],
)
result = processor.process(good_order)
print(f"  Status: {result.status.name}, Total: ${result.total:.2f}\n")

# Out of stock
bad_order = Order(
    customer_id="C002",
    items=[OrderItem("P003", "Rare Item", 199.99, 1)],
)
result = processor.process(bad_order)
print(f"  Status: {result.status.name}, Reason: {result.failure_reason}\n")

# Validation failure
empty_order = Order(customer_id="", items=[])
result = processor.process(empty_order)
print(f"  Status: {result.status.name}, Reason: {result.failure_reason}")
```

---

## 10. Domain Modelling

Domain-Driven Design (DDD) concepts applied to Python LLD.

### 10.1 Entities vs Value Objects

**Entity** — has a unique identity that persists across state changes.  
**Value Object** — defined by its attributes; two value objects with the same attributes
are considered equal.

```python
from __future__ import annotations
from dataclasses import dataclass, field
import uuid


# --- Value Objects (frozen=True makes them immutable and hashable) ---

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: float) -> Money:
        return Money(round(self.amount * factor, 2), self.currency)


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

    def one_line(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value or "." not in self.value.split("@")[1]:
            raise ValueError(f"Invalid email: {self.value}")


# --- Entity (has identity) ---

@dataclass
class Customer:
    customer_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    email: EmailAddress = field(default_factory=lambda: EmailAddress("default@example.com"))
    shipping_address: Address | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self.customer_id == other.customer_id

    def __hash__(self) -> int:
        return hash(self.customer_id)


# Value objects: equality is by value
m1 = Money(100, "USD")
m2 = Money(100, "USD")
print(f"Same money? {m1 == m2}")  # True — same attributes

# Entities: equality is by identity
c1 = Customer(customer_id="C001", name="Alice")
c2 = Customer(customer_id="C001", name="Alice Updated")
c3 = Customer(customer_id="C002", name="Alice")

print(f"Same customer? {c1 == c2}")  # True — same ID
print(f"Same customer? {c1 == c3}")  # False — different ID
```

### 10.2 Aggregates and Aggregate Roots

An **Aggregate** is a cluster of domain objects treated as a single unit. The
**Aggregate Root** is the only entry point for external access.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "USD"

    def add(self, other: Money) -> Money:
        assert self.currency == other.currency
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> Money:
        return Money(self.amount * factor, self.currency)


@dataclass
class OrderLine:
    """Part of the Order aggregate — NOT accessed directly from outside."""
    line_id: str = field(default_factory=lambda: uuid.uuid4().hex[:6])
    product_id: str = ""
    product_name: str = ""
    unit_price: Money = field(default_factory=lambda: Money(0))
    quantity: int = 1

    @property
    def line_total(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass
class Order:
    """
    AGGREGATE ROOT — all external interaction goes through this class.
    It protects the invariants of its child entities (OrderLines).
    """
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    customer_id: str = ""
    _lines: List[OrderLine] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)

    MAX_LINES = 20

    @property
    def lines(self) -> tuple:
        return tuple(self._lines)

    @property
    def total(self) -> Money:
        if not self._lines:
            return Money(0)
        result = Money(0)
        for line in self._lines:
            result = result.add(line.line_total)
        return result

    def add_line(self, product_id: str, name: str, price: Money, qty: int) -> OrderLine:
        if self.status != "draft":
            raise ValueError("Cannot modify a non-draft order")
        if len(self._lines) >= self.MAX_LINES:
            raise ValueError(f"Order cannot have more than {self.MAX_LINES} lines")
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        existing = next((l for l in self._lines if l.product_id == product_id), None)
        if existing:
            existing.quantity += qty
            return existing

        line = OrderLine(product_id=product_id, product_name=name, unit_price=price, quantity=qty)
        self._lines.append(line)
        return line

    def remove_line(self, product_id: str) -> None:
        if self.status != "draft":
            raise ValueError("Cannot modify a non-draft order")
        self._lines = [l for l in self._lines if l.product_id != product_id]

    def submit(self) -> None:
        if not self._lines:
            raise ValueError("Cannot submit an empty order")
        if self.status != "draft":
            raise ValueError(f"Cannot submit order in '{self.status}' status")
        self.status = "submitted"

    def cancel(self) -> None:
        if self.status in ("shipped", "delivered"):
            raise ValueError(f"Cannot cancel order in '{self.status}' status")
        self.status = "cancelled"


# Usage
order = Order(customer_id="C001")
order.add_line("P001", "Laptop", Money(999.99), 1)
order.add_line("P002", "Mouse", Money(29.99), 2)
order.add_line("P001", "Laptop", Money(999.99), 1)  # adds to existing

print(f"Order {order.order_id}: {len(order.lines)} lines, total ${order.total.amount:.2f}")
# 2 lines (laptop qty=2, mouse qty=2), total = 2*999.99 + 2*29.99 = $2059.96

order.submit()
print(f"Status: {order.status}")

try:
    order.add_line("P003", "Keyboard", Money(79.99), 1)
except ValueError as e:
    print(f"Blocked: {e}")
```

### 10.3 Domain Events

Domain events capture something meaningful that happened in the domain. They are useful
for decoupling side effects from core logic.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Callable, Dict
import uuid


@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    total: float = 0.0


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    order_id: str = ""
    amount: float = 0.0
    transaction_id: str = ""


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[type, List[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)


# Event handlers
def send_order_confirmation(event: OrderPlaced) -> None:
    print(f"[Email] Order confirmation sent to customer {event.customer_id} for order {event.order_id}")


def update_inventory(event: OrderPlaced) -> None:
    print(f"[Inventory] Reserving items for order {event.order_id}")


def notify_warehouse(event: PaymentReceived) -> None:
    print(f"[Warehouse] Prepare shipment for order {event.order_id}")


def process_refund(event: OrderCancelled) -> None:
    print(f"[Refund] Processing refund for order {event.order_id}: {event.reason}")


# Wiring
bus = EventBus()
bus.subscribe(OrderPlaced, send_order_confirmation)
bus.subscribe(OrderPlaced, update_inventory)
bus.subscribe(PaymentReceived, notify_warehouse)
bus.subscribe(OrderCancelled, process_refund)

# Publishing events
bus.publish(OrderPlaced(order_id="ORD-001", customer_id="C042", total=299.99))
print()
bus.publish(PaymentReceived(order_id="ORD-001", amount=299.99, transaction_id="txn_abc"))
print()
bus.publish(OrderCancelled(order_id="ORD-002", reason="Customer requested"))
```

### 10.4 Ubiquitous Language

Ubiquitous Language means using the same terms in code that domain experts use in
conversation. Avoid technical jargon; model the domain's vocabulary directly.

| Domain Expert Says         | Bad Code Name           | Good Code Name         |
|----------------------------|-------------------------|------------------------|
| "Place an order"           | `create_record()`       | `place_order()`        |
| "Ship the package"         | `update_status(3)`      | `ship_order()`         |
| "Apply a coupon"           | `process_discount()`    | `apply_coupon()`       |
| "Cancel the subscription"  | `set_flag(False)`       | `cancel_subscription()`|
| "Reserve a seat"           | `decrement_counter()`   | `reserve_seat()`       |

```python
# BAD: Technical jargon
class DataProcessor:
    def process(self, record: dict, flag: int) -> dict:
        if flag == 1:
            record["status"] = 2
        return record


# GOOD: Ubiquitous language
class OrderService:
    def ship_order(self, order: Order) -> Order:
        order.status = "shipped"
        return order

    def cancel_order(self, order: Order, reason: str) -> Order:
        order.cancel()
        return order
```

### 10.5 Example — E-Commerce Domain Model

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum, auto
import uuid


# ==================== Value Objects ====================

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "USD"

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(round(self.amount + other.amount, 2), self.currency)

    def subtract(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(round(self.amount - other.amount, 2), self.currency)

    def multiply(self, factor: float) -> Money:
        return Money(round(self.amount * factor, 2), self.currency)

    def __str__(self) -> str:
        return f"${self.amount:.2f} {self.currency}"


@dataclass(frozen=True)
class SKU:
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) < 3:
            raise ValueError(f"Invalid SKU: {self.value}")


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")


# ==================== Entities ====================

class ProductStatus(Enum):
    ACTIVE = auto()
    DISCONTINUED = auto()
    OUT_OF_STOCK = auto()


@dataclass
class Product:
    product_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    sku: SKU = field(default_factory=lambda: SKU("DEFAULT"))
    name: str = ""
    description: str = ""
    price: Money = field(default_factory=lambda: Money(0))
    status: ProductStatus = ProductStatus.ACTIVE

    def is_available(self) -> bool:
        return self.status == ProductStatus.ACTIVE

    def discontinue(self) -> None:
        self.status = ProductStatus.DISCONTINUED


@dataclass
class CartItem:
    product: Product
    quantity: Quantity

    @property
    def subtotal(self) -> Money:
        return self.product.price.multiply(self.quantity.value)


# ==================== Aggregate: Shopping Cart ====================

class CartStatus(Enum):
    ACTIVE = auto()
    CHECKED_OUT = auto()
    ABANDONED = auto()


@dataclass
class ShoppingCart:
    """Aggregate root for the cart context."""
    cart_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    customer_id: str = ""
    _items: List[CartItem] = field(default_factory=list)
    status: CartStatus = CartStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def items(self) -> tuple:
        return tuple(self._items)

    @property
    def total(self) -> Money:
        result = Money(0)
        for item in self._items:
            result = result.add(item.subtotal)
        return result

    @property
    def item_count(self) -> int:
        return sum(item.quantity.value for item in self._items)

    def add_product(self, product: Product, quantity: int = 1) -> None:
        if self.status != CartStatus.ACTIVE:
            raise ValueError("Cannot modify a non-active cart")
        if not product.is_available():
            raise ValueError(f"Product {product.name} is not available")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        for item in self._items:
            if item.product.product_id == product.product_id:
                new_qty = item.quantity.value + quantity
                self._items[self._items.index(item)] = CartItem(product, Quantity(new_qty))
                return

        self._items.append(CartItem(product, Quantity(quantity)))

    def remove_product(self, product_id: str) -> None:
        if self.status != CartStatus.ACTIVE:
            raise ValueError("Cannot modify a non-active cart")
        self._items = [i for i in self._items if i.product.product_id != product_id]

    def update_quantity(self, product_id: str, new_quantity: int) -> None:
        if self.status != CartStatus.ACTIVE:
            raise ValueError("Cannot modify a non-active cart")
        if new_quantity <= 0:
            self.remove_product(product_id)
            return

        for idx, item in enumerate(self._items):
            if item.product.product_id == product_id:
                self._items[idx] = CartItem(item.product, Quantity(new_quantity))
                return

        raise ValueError(f"Product {product_id} not in cart")

    def checkout(self) -> None:
        if not self._items:
            raise ValueError("Cannot checkout an empty cart")
        self.status = CartStatus.CHECKED_OUT

    def abandon(self) -> None:
        self.status = CartStatus.ABANDONED

    def __str__(self) -> str:
        lines = [f"Cart {self.cart_id} ({self.status.name}):"]
        for item in self._items:
            lines.append(f"  {item.product.name} x{item.quantity.value} = {item.subtotal}")
        lines.append(f"  TOTAL: {self.total}")
        return "\n".join(lines)


# ==================== Usage ====================

laptop = Product(name="Laptop", sku=SKU("LAP-001"), price=Money(999.99))
mouse = Product(name="Mouse", sku=SKU("MOU-001"), price=Money(29.99))
keyboard = Product(name="Keyboard", sku=SKU("KEY-001"), price=Money(79.99))

cart = ShoppingCart(customer_id="C001")
cart.add_product(laptop, 1)
cart.add_product(mouse, 2)
cart.add_product(keyboard, 1)
print(cart)

cart.update_quantity(mouse.product_id, 1)
print(f"\nAfter updating mouse qty to 1:")
print(cart)

cart.checkout()
print(f"\nStatus: {cart.status.name}")

try:
    cart.add_product(laptop, 1)
except ValueError as e:
    print(f"Blocked: {e}")
```

---

## 11. Extensibility

Extensibility is the ability to add new features or modify behaviour without rewriting
existing code. It is the practical outcome of following OCP, DIP, and proper abstraction.

### 11.1 Plugin Architecture

```python
from __future__ import annotations
from typing import Protocol, Dict, List, runtime_checkable
from dataclasses import dataclass
import importlib


@runtime_checkable
class DataTransformer(Protocol):
    """Plugin interface for data transformation."""
    name: str
    def transform(self, data: dict) -> dict: ...


class UpperCaseTransformer:
    name = "uppercase"
    def transform(self, data: dict) -> dict:
        return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}


class TrimTransformer:
    name = "trim"
    def transform(self, data: dict) -> dict:
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}


class MaskEmailTransformer:
    name = "mask_email"
    def transform(self, data: dict) -> dict:
        result = dict(data)
        for k, v in result.items():
            if isinstance(v, str) and "@" in v:
                local, domain = v.split("@", 1)
                masked = local[0] + "***" + local[-1] if len(local) > 1 else "***"
                result[k] = f"{masked}@{domain}"
        return result


class TransformPipeline:
    """Extensible pipeline — add new transformers without modifying this class."""

    def __init__(self) -> None:
        self._transformers: Dict[str, DataTransformer] = {}

    def register(self, transformer: DataTransformer) -> None:
        if not isinstance(transformer, DataTransformer):
            raise TypeError(f"{transformer} does not satisfy DataTransformer protocol")
        self._transformers[transformer.name] = transformer
        print(f"  Registered transformer: {transformer.name}")

    def apply(self, data: dict, steps: List[str] | None = None) -> dict:
        targets = steps or list(self._transformers.keys())
        result = dict(data)
        for step in targets:
            if step in self._transformers:
                result = self._transformers[step].transform(result)
        return result


# Setup
pipeline = TransformPipeline()
pipeline.register(TrimTransformer())
pipeline.register(UpperCaseTransformer())
pipeline.register(MaskEmailTransformer())

data = {"name": "  Alice  ", "email": "alice.smith@example.com", "role": "  admin  "}

print(f"\nOriginal:    {data}")
print(f"After trim:  {pipeline.apply(data, ['trim'])}")
print(f"After upper: {pipeline.apply(data, ['trim', 'uppercase'])}")
print(f"After mask:  {pipeline.apply(data, ['trim', 'mask_email'])}")
print(f"Full pipeline: {pipeline.apply(data)}")
```

### 11.2 Hook Points

Hook points are named extension points where custom logic can be injected.

```python
from typing import Callable, List, Dict, Any


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, hook_name: str, callback: Callable) -> None:
        self._hooks.setdefault(hook_name, []).append(callback)

    def trigger(self, hook_name: str, **kwargs: Any) -> List[Any]:
        results = []
        for callback in self._hooks.get(hook_name, []):
            results.append(callback(**kwargs))
        return results


class UserRegistration:
    def __init__(self) -> None:
        self.hooks = HookRegistry()

    def register_user(self, username: str, email: str) -> dict:
        user = {"username": username, "email": email, "id": hash(username) % 10000}

        self.hooks.trigger("before_save", user=user)

        print(f"Saving user: {user['username']}")

        self.hooks.trigger("after_save", user=user)
        self.hooks.trigger("on_welcome", user=user)

        return user


# Register hooks
reg = UserRegistration()

reg.hooks.register("before_save", lambda user: print(f"  [Validate] Checking {user['username']}"))
reg.hooks.register("after_save", lambda user: print(f"  [Audit] User {user['username']} created"))
reg.hooks.register("after_save", lambda user: print(f"  [Analytics] Track signup for {user['email']}"))
reg.hooks.register("on_welcome", lambda user: print(f"  [Email] Welcome email sent to {user['email']}"))

reg.register_user("alice", "alice@example.com")
```

### 11.3 Event-Driven Extensibility

```python
from __future__ import annotations
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventEmitter:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Event], None]]] = {}

    def on(self, event_name: str, listener: Callable[[Event], None]) -> None:
        self._listeners.setdefault(event_name, []).append(listener)

    def off(self, event_name: str, listener: Callable[[Event], None]) -> None:
        if event_name in self._listeners:
            self._listeners[event_name] = [l for l in self._listeners[event_name] if l is not listener]

    def emit(self, event_name: str, **data: Any) -> None:
        event = Event(name=event_name, data=data)
        for listener in self._listeners.get(event_name, []):
            listener(event)
        for listener in self._listeners.get("*", []):
            listener(event)


class FileUploadService(EventEmitter):
    def upload(self, filename: str, size: int) -> None:
        self.emit("upload:start", filename=filename, size=size)

        print(f"Uploading {filename} ({size} bytes)...")

        if size > 100_000_000:
            self.emit("upload:error", filename=filename, error="File too large")
            return

        self.emit("upload:progress", filename=filename, percent=100)
        self.emit("upload:complete", filename=filename, size=size)


# Extend with listeners
svc = FileUploadService()

svc.on("upload:start", lambda e: print(f"  [Log] Upload started: {e.data['filename']}"))
svc.on("upload:complete", lambda e: print(f"  [Thumbnail] Generating for {e.data['filename']}"))
svc.on("upload:complete", lambda e: print(f"  [Index] Adding to search index"))
svc.on("upload:error", lambda e: print(f"  [Alert] Upload failed: {e.data['error']}"))
svc.on("*", lambda e: print(f"  [Metrics] Event: {e.name}"))

svc.upload("photo.jpg", 5_000_000)
print()
svc.upload("huge_video.mp4", 500_000_000)
```

### 11.4 Template Method for Extensibility

The Template Method pattern defines the skeleton of an algorithm in a base class and
lets subclasses override specific steps.

```python
from abc import ABC, abstractmethod
from typing import List


class DataExporter(ABC):
    """Template method pattern — the skeleton is fixed; steps are customisable."""

    def export(self, data: List[dict]) -> str:
        self.validate(data)
        header = self.build_header(data)
        body = self.build_body(data)
        footer = self.build_footer(data)
        result = self.assemble(header, body, footer)
        self.post_process(result)
        return result

    def validate(self, data: List[dict]) -> None:
        if not data:
            raise ValueError("No data to export")

    @abstractmethod
    def build_header(self, data: List[dict]) -> str:
        ...

    @abstractmethod
    def build_body(self, data: List[dict]) -> str:
        ...

    def build_footer(self, data: List[dict]) -> str:
        return ""

    def assemble(self, header: str, body: str, footer: str) -> str:
        parts = [p for p in [header, body, footer] if p]
        return "\n".join(parts)

    def post_process(self, result: str) -> None:
        pass


class CSVExporter(DataExporter):
    def build_header(self, data: List[dict]) -> str:
        return ",".join(data[0].keys())

    def build_body(self, data: List[dict]) -> str:
        lines = []
        for row in data:
            lines.append(",".join(str(v) for v in row.values()))
        return "\n".join(lines)


class JSONExporter(DataExporter):
    def build_header(self, data: List[dict]) -> str:
        return "["

    def build_body(self, data: List[dict]) -> str:
        import json
        items = [f"  {json.dumps(row)}" for row in data]
        return ",\n".join(items)

    def build_footer(self, data: List[dict]) -> str:
        return "]"


class HTMLTableExporter(DataExporter):
    def build_header(self, data: List[dict]) -> str:
        headers = "".join(f"<th>{k}</th>" for k in data[0].keys())
        return f"<table>\n<tr>{headers}</tr>"

    def build_body(self, data: List[dict]) -> str:
        rows = []
        for row in data:
            cells = "".join(f"<td>{v}</td>" for v in row.values())
            rows.append(f"<tr>{cells}</tr>")
        return "\n".join(rows)

    def build_footer(self, data: List[dict]) -> str:
        return "</table>"

    def post_process(self, result: str) -> None:
        print(f"[HTMLExporter] Generated {result.count('<tr>')} rows")


# Usage
sample = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"},
]

for exporter in [CSVExporter(), JSONExporter(), HTMLTableExporter()]:
    print(f"\n--- {exporter.__class__.__name__} ---")
    print(exporter.export(sample))
```

### 11.5 Example — Extensible Logging Framework

```python
from __future__ import annotations
from typing import Protocol, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogRecord:
    level: LogLevel
    message: str
    logger_name: str = "root"
    timestamp: datetime = field(default_factory=datetime.now)
    extra: dict = field(default_factory=dict)


class LogFormatter(Protocol):
    def format(self, record: LogRecord) -> str: ...


class LogHandler(Protocol):
    def handle(self, record: LogRecord) -> None: ...


class LogFilter(Protocol):
    def should_log(self, record: LogRecord) -> bool: ...


# --- Formatters ---
class SimpleFormatter:
    def format(self, record: LogRecord) -> str:
        ts = record.timestamp.strftime("%H:%M:%S")
        return f"[{ts}] {record.level.name}: {record.message}"


class DetailedFormatter:
    def format(self, record: LogRecord) -> str:
        ts = record.timestamp.isoformat()
        extra_str = f" | {record.extra}" if record.extra else ""
        return f"{ts} [{record.logger_name}] {record.level.name}: {record.message}{extra_str}"


# --- Handlers ---
class ConsoleHandler:
    def __init__(self, formatter: LogFormatter | None = None) -> None:
        self._formatter = formatter or SimpleFormatter()

    def handle(self, record: LogRecord) -> None:
        print(self._formatter.format(record))


class FileHandler:
    def __init__(self, filepath: str, formatter: LogFormatter | None = None) -> None:
        self._filepath = filepath
        self._formatter = formatter or DetailedFormatter()

    def handle(self, record: LogRecord) -> None:
        line = self._formatter.format(record)
        # In a real system this would write to file
        print(f"  [→ {self._filepath}] {line}")


class InMemoryHandler:
    def __init__(self, max_records: int = 1000) -> None:
        self._records: List[LogRecord] = []
        self._max = max_records

    def handle(self, record: LogRecord) -> None:
        if len(self._records) >= self._max:
            self._records.pop(0)
        self._records.append(record)

    @property
    def records(self) -> List[LogRecord]:
        return list(self._records)


# --- Filters ---
class LevelFilter:
    def __init__(self, min_level: LogLevel = LogLevel.DEBUG) -> None:
        self._min = min_level

    def should_log(self, record: LogRecord) -> bool:
        return record.level >= self._min


class KeywordFilter:
    def __init__(self, blocked_keywords: List[str]) -> None:
        self._blocked = [kw.lower() for kw in blocked_keywords]

    def should_log(self, record: LogRecord) -> bool:
        msg_lower = record.message.lower()
        return not any(kw in msg_lower for kw in self._blocked)


# --- Logger (extensible core) ---
class Logger:
    def __init__(self, name: str = "root") -> None:
        self.name = name
        self._handlers: List[LogHandler] = []
        self._filters: List[LogFilter] = []

    def add_handler(self, handler: LogHandler) -> Logger:
        self._handlers.append(handler)
        return self

    def add_filter(self, log_filter: LogFilter) -> Logger:
        self._filters.append(log_filter)
        return self

    def _log(self, level: LogLevel, message: str, **extra) -> None:
        record = LogRecord(level=level, message=message, logger_name=self.name, extra=extra)

        for f in self._filters:
            if not f.should_log(record):
                return

        for handler in self._handlers:
            handler.handle(record)

    def debug(self, msg: str, **extra) -> None:
        self._log(LogLevel.DEBUG, msg, **extra)

    def info(self, msg: str, **extra) -> None:
        self._log(LogLevel.INFO, msg, **extra)

    def warning(self, msg: str, **extra) -> None:
        self._log(LogLevel.WARNING, msg, **extra)

    def error(self, msg: str, **extra) -> None:
        self._log(LogLevel.ERROR, msg, **extra)

    def critical(self, msg: str, **extra) -> None:
        self._log(LogLevel.CRITICAL, msg, **extra)


# --- Usage ---
memory = InMemoryHandler()

logger = (
    Logger("app")
    .add_filter(LevelFilter(LogLevel.INFO))
    .add_filter(KeywordFilter(["password", "secret"]))
    .add_handler(ConsoleHandler(SimpleFormatter()))
    .add_handler(FileHandler("/var/log/app.log"))
    .add_handler(memory)
)

logger.debug("This won't appear (below INFO)")
logger.info("Application started", version="2.1")
logger.warning("Disk usage above 80%")
logger.error("Failed to connect to database", host="db.local", port=5432)
logger.info("User changed password")  # blocked by keyword filter

print(f"\nIn-memory records: {len(memory.records)}")
```

---

## 12. Testability

Designing code for testability means making it easy to isolate units, inject fakes, and
verify behaviour without relying on external systems.

### 12.1 Designing for Testability

**Principles:**

1. **Depend on abstractions** — inject dependencies so tests can provide fakes.
2. **Avoid global state** — singletons and module-level state make tests flaky.
3. **Separate I/O from logic** — pure functions are trivial to test.
4. **Small, focused functions** — each does one thing → one test per behaviour.
5. **Avoid `datetime.now()` inside business logic** — inject a clock.

```python
from typing import Protocol
from datetime import datetime, timedelta


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now()


class FakeClock:
    def __init__(self, fixed: datetime) -> None:
        self._now = fixed

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs) -> None:
        self._now += timedelta(**kwargs)


class TrialManager:
    TRIAL_DAYS = 14

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def is_trial_active(self, trial_start: datetime) -> bool:
        elapsed = self._clock.now() - trial_start
        return elapsed <= timedelta(days=self.TRIAL_DAYS)

    def days_remaining(self, trial_start: datetime) -> int:
        elapsed = self._clock.now() - trial_start
        remaining = self.TRIAL_DAYS - elapsed.days
        return max(0, remaining)


# In production
manager = TrialManager(SystemClock())

# In tests — deterministic
clock = FakeClock(datetime(2025, 1, 1, 12, 0))
manager = TrialManager(clock)
trial_start = datetime(2025, 1, 1, 12, 0)

assert manager.is_trial_active(trial_start) is True
assert manager.days_remaining(trial_start) == 14

clock.advance(days=10)
assert manager.is_trial_active(trial_start) is True
assert manager.days_remaining(trial_start) == 4

clock.advance(days=5)
assert manager.is_trial_active(trial_start) is False
assert manager.days_remaining(trial_start) == 0

print("All trial manager tests passed!")
```

### 12.2 Dependency Injection for Testing

```python
from typing import Protocol, Optional, List
from dataclasses import dataclass


@dataclass
class User:
    user_id: str
    name: str
    email: str


class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> Optional[User]: ...
    def find_by_email(self, email: str) -> Optional[User]: ...


class EmailService(Protocol):
    def send(self, to: str, subject: str, body: str) -> bool: ...


class UserRegistrationService:
    def __init__(self, repo: UserRepository, email_service: EmailService) -> None:
        self._repo = repo
        self._email = email_service

    def register(self, name: str, email: str) -> User:
        if not name or not email:
            raise ValueError("Name and email are required")

        existing = self._repo.find_by_email(email)
        if existing:
            raise ValueError(f"Email {email} is already registered")

        user = User(user_id=f"U{hash(email) % 10000:04d}", name=name, email=email)
        self._repo.save(user)
        self._email.send(email, "Welcome!", f"Hello {name}, welcome aboard!")
        return user


# --- Test doubles ---
class FakeUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self.save_called_with: List[User] = []

    def save(self, user: User) -> None:
        self._users[user.user_id] = user
        self.save_called_with.append(user)

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._users.values() if u.email == email), None)

    def seed(self, *users: User) -> None:
        for u in users:
            self._users[u.user_id] = u


class FakeEmailService:
    def __init__(self) -> None:
        self.sent_emails: List[dict] = []

    def send(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


# --- Tests ---
def test_register_new_user():
    repo = FakeUserRepository()
    email_svc = FakeEmailService()
    service = UserRegistrationService(repo, email_svc)

    user = service.register("Alice", "alice@example.com")

    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert len(repo.save_called_with) == 1
    assert repo.save_called_with[0].name == "Alice"
    assert len(email_svc.sent_emails) == 1
    assert email_svc.sent_emails[0]["to"] == "alice@example.com"
    print("test_register_new_user PASSED")


def test_register_duplicate_email():
    repo = FakeUserRepository()
    repo.seed(User("U0001", "Bob", "bob@example.com"))
    email_svc = FakeEmailService()
    service = UserRegistrationService(repo, email_svc)

    try:
        service.register("Bob2", "bob@example.com")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "already registered" in str(e)
    assert len(email_svc.sent_emails) == 0  # no email sent
    print("test_register_duplicate_email PASSED")


def test_register_empty_fields():
    repo = FakeUserRepository()
    email_svc = FakeEmailService()
    service = UserRegistrationService(repo, email_svc)

    try:
        service.register("", "alice@example.com")
        assert False
    except ValueError:
        pass

    try:
        service.register("Alice", "")
        assert False
    except ValueError:
        pass
    print("test_register_empty_fields PASSED")


test_register_new_user()
test_register_duplicate_email()
test_register_empty_fields()
```

### 12.3 Mocking and Stubs

```python
from unittest.mock import Mock, patch, MagicMock
from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, amount: float, card_token: str) -> dict: ...


class PaymentProcessor:
    def __init__(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    def process(self, amount: float, card_token: str) -> dict:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        result = self._gateway.charge(amount, card_token)
        if result["success"]:
            return {"status": "paid", "transaction_id": result["txn_id"]}
        return {"status": "failed", "reason": result.get("error", "Unknown")}


# --- Test with Mock ---
def test_successful_payment():
    mock_gateway = Mock()
    mock_gateway.charge.return_value = {"success": True, "txn_id": "txn_123"}

    processor = PaymentProcessor(mock_gateway)
    result = processor.process(100.0, "tok_abc")

    assert result["status"] == "paid"
    assert result["transaction_id"] == "txn_123"
    mock_gateway.charge.assert_called_once_with(100.0, "tok_abc")
    print("test_successful_payment PASSED")


def test_failed_payment():
    mock_gateway = Mock()
    mock_gateway.charge.return_value = {"success": False, "error": "Card declined"}

    processor = PaymentProcessor(mock_gateway)
    result = processor.process(50.0, "tok_bad")

    assert result["status"] == "failed"
    assert result["reason"] == "Card declined"
    print("test_failed_payment PASSED")


def test_invalid_amount():
    mock_gateway = Mock()
    processor = PaymentProcessor(mock_gateway)

    try:
        processor.process(-10.0, "tok_abc")
        assert False
    except ValueError:
        pass
    mock_gateway.charge.assert_not_called()
    print("test_invalid_amount PASSED")


test_successful_payment()
test_failed_payment()
test_invalid_amount()
```

### 12.4 Test Doubles

| Double Type  | Purpose                                              | Example                    |
|-------------|------------------------------------------------------|----------------------------|
| **Dummy**   | Placeholder — never actually used                    | `None` or empty object     |
| **Stub**    | Returns canned responses                             | `FakeRepo` with seed data  |
| **Spy**     | Records calls for later assertion                    | `FakeEmailService`         |
| **Mock**    | Pre-programmed with expectations                     | `unittest.mock.Mock()`     |
| **Fake**    | Lightweight working implementation                   | In-memory database         |

```python
from typing import Optional


# DUMMY — satisfies a type requirement but is never used
class DummyLogger:
    def log(self, message: str) -> None:
        pass


# STUB — returns predetermined data
class StubPricingService:
    def get_price(self, product_id: str) -> float:
        return 99.99  # always returns the same price


# SPY — records interactions for verification
class SpyAuditLog:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, action: str, user_id: str) -> None:
        self.entries.append({"action": action, "user_id": user_id})


# FAKE — simple but functional implementation
class FakeCache:
    def __init__(self) -> None:
        self._store: dict = {}

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: int = 0) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


# --- Using test doubles ---
def test_caching_service():
    cache = FakeCache()
    audit = SpyAuditLog()

    cache.set("user:1", "Alice")
    audit.record("cache_set", "system")

    assert cache.get("user:1") == "Alice"
    assert cache.get("user:999") is None
    assert len(audit.entries) == 1
    assert audit.entries[0]["action"] == "cache_set"

    cache.delete("user:1")
    assert cache.get("user:1") is None

    print("test_caching_service PASSED")

test_caching_service()
```

### 12.5 Example — Testing a Payment Service

```python
from __future__ import annotations
from typing import Protocol, Optional
from dataclasses import dataclass
from enum import Enum, auto
from unittest.mock import Mock


class ChargeStatus(Enum):
    SUCCESS = auto()
    DECLINED = auto()
    NETWORK_ERROR = auto()


@dataclass
class ChargeResult:
    status: ChargeStatus
    transaction_id: str = ""
    error_message: str = ""


class Gateway(Protocol):
    def charge(self, amount: float, currency: str, token: str) -> ChargeResult: ...

class FraudChecker(Protocol):
    def is_fraudulent(self, amount: float, token: str) -> bool: ...

class AuditLogger(Protocol):
    def log_charge(self, amount: float, result: ChargeResult) -> None: ...


class PaymentService:
    def __init__(self, gateway: Gateway, fraud: FraudChecker, audit: AuditLogger) -> None:
        self._gateway = gateway
        self._fraud = fraud
        self._audit = audit

    def charge_customer(self, amount: float, currency: str, token: str) -> ChargeResult:
        if amount <= 0:
            return ChargeResult(status=ChargeStatus.DECLINED, error_message="Invalid amount")

        if self._fraud.is_fraudulent(amount, token):
            result = ChargeResult(status=ChargeStatus.DECLINED, error_message="Suspected fraud")
            self._audit.log_charge(amount, result)
            return result

        try:
            result = self._gateway.charge(amount, currency, token)
        except Exception as e:
            result = ChargeResult(status=ChargeStatus.NETWORK_ERROR, error_message=str(e))

        self._audit.log_charge(amount, result)
        return result


# === TESTS ===

def test_successful_charge():
    gateway = Mock()
    gateway.charge.return_value = ChargeResult(
        status=ChargeStatus.SUCCESS, transaction_id="txn_abc"
    )
    fraud = Mock()
    fraud.is_fraudulent.return_value = False
    audit = Mock()

    service = PaymentService(gateway, fraud, audit)
    result = service.charge_customer(100.0, "USD", "tok_visa")

    assert result.status == ChargeStatus.SUCCESS
    assert result.transaction_id == "txn_abc"
    gateway.charge.assert_called_once_with(100.0, "USD", "tok_visa")
    fraud.is_fraudulent.assert_called_once_with(100.0, "tok_visa")
    audit.log_charge.assert_called_once()
    print("test_successful_charge PASSED")


def test_fraud_detected():
    gateway = Mock()
    fraud = Mock()
    fraud.is_fraudulent.return_value = True
    audit = Mock()

    service = PaymentService(gateway, fraud, audit)
    result = service.charge_customer(5000.0, "USD", "tok_stolen")

    assert result.status == ChargeStatus.DECLINED
    assert "fraud" in result.error_message.lower()
    gateway.charge.assert_not_called()
    audit.log_charge.assert_called_once()
    print("test_fraud_detected PASSED")


def test_gateway_network_error():
    gateway = Mock()
    gateway.charge.side_effect = ConnectionError("Timeout")
    fraud = Mock()
    fraud.is_fraudulent.return_value = False
    audit = Mock()

    service = PaymentService(gateway, fraud, audit)
    result = service.charge_customer(75.0, "USD", "tok_visa")

    assert result.status == ChargeStatus.NETWORK_ERROR
    assert "Timeout" in result.error_message
    audit.log_charge.assert_called_once()
    print("test_gateway_network_error PASSED")


def test_invalid_amount():
    gateway = Mock()
    fraud = Mock()
    audit = Mock()

    service = PaymentService(gateway, fraud, audit)
    result = service.charge_customer(-10.0, "USD", "tok_visa")

    assert result.status == ChargeStatus.DECLINED
    gateway.charge.assert_not_called()
    fraud.is_fraudulent.assert_not_called()
    print("test_invalid_amount PASSED")


test_successful_charge()
test_fraud_detected()
test_gateway_network_error()
test_invalid_amount()
```

---

## 13. Writing Maintainable Code

### 13.1 Single Responsibility at Function Level

Each function should do exactly one thing. If you can describe what a function does
using "and", it probably does too much.

```python
# BAD: Does validation AND saving AND notification
def process_user_signup(name: str, email: str, db, mailer) -> dict:
    if not name or len(name) < 2:
        raise ValueError("Invalid name")
    if "@" not in email:
        raise ValueError("Invalid email")
    user_id = db.execute(f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')")
    mailer.send(email, "Welcome!", f"Hi {name}")
    return {"id": user_id, "name": name, "email": email}


# GOOD: Each function has a single responsibility
def validate_signup_data(name: str, email: str) -> None:
    if not name or len(name) < 2:
        raise ValueError("Invalid name: must be at least 2 characters")
    if "@" not in email:
        raise ValueError("Invalid email format")


def create_user(name: str, email: str, repo) -> dict:
    user = {"name": name, "email": email}
    repo.save(user)
    return user


def send_welcome_email(email: str, name: str, mailer) -> None:
    mailer.send(email, "Welcome!", f"Hi {name}")


def register_user(name: str, email: str, repo, mailer) -> dict:
    validate_signup_data(name, email)
    user = create_user(name, email, repo)
    send_welcome_email(email, name, mailer)
    return user
```

### 13.2 Meaningful Naming

```python
# BAD
def proc(d: list, f: int) -> list:
    r = []
    for i in d:
        if i["s"] > f:
            r.append(i)
    return r

# GOOD
def filter_active_users_above_score(users: list[dict], min_score: int) -> list[dict]:
    return [user for user in users if user["score"] > min_score]


# BAD
class Mgr:
    def do(self, x):
        ...

# GOOD
class SubscriptionManager:
    def cancel_subscription(self, subscription_id: str) -> None:
        ...


# Naming conventions summary:
# - Variables/functions: snake_case, descriptive  (user_count, calculate_tax)
# - Classes: PascalCase, noun-based              (PaymentGateway, UserService)
# - Constants: UPPER_SNAKE_CASE                  (MAX_RETRIES, DEFAULT_TIMEOUT)
# - Booleans: is_/has_/can_/should_ prefix       (is_active, has_access)
# - Private: single underscore prefix            (_internal_state)
```

### 13.3 Function Size and Complexity

**Rules of thumb:**

- A function should fit on one screen (~25 lines of logic).
- Cyclomatic complexity ≤ 5 for most functions.
- No more than 3 levels of nesting.
- No more than 3–4 parameters (use dataclasses or dicts for more).

```python
from dataclasses import dataclass
from typing import Optional


# BAD: Too many params, deeply nested, multiple concerns
def create_order(
    customer_name, customer_email, customer_phone,
    product_name, product_price, quantity,
    discount_code, shipping_method, gift_wrap,
    note, priority, express
):
    if customer_name:
        if customer_email:
            if product_name:
                if quantity > 0:
                    if product_price > 0:
                        total = product_price * quantity
                        if discount_code == "SAVE10":
                            total *= 0.9
                        elif discount_code == "SAVE20":
                            total *= 0.8
                        # ... 50 more lines ...


# GOOD: Structured inputs, flat logic, delegated concerns
@dataclass
class OrderRequest:
    customer_name: str
    customer_email: str
    product_name: str
    unit_price: float
    quantity: int
    discount_code: Optional[str] = None
    shipping_method: str = "standard"
    gift_wrap: bool = False


def validate_order_request(request: OrderRequest) -> None:
    if not request.customer_name:
        raise ValueError("Customer name is required")
    if not request.customer_email:
        raise ValueError("Customer email is required")
    if request.quantity <= 0:
        raise ValueError("Quantity must be positive")
    if request.unit_price <= 0:
        raise ValueError("Price must be positive")


def calculate_subtotal(price: float, quantity: int) -> float:
    return price * quantity


def apply_discount(subtotal: float, code: Optional[str]) -> float:
    discounts = {"SAVE10": 0.10, "SAVE20": 0.20, "VIP30": 0.30}
    if code and code in discounts:
        return subtotal * (1 - discounts[code])
    return subtotal


def create_order(request: OrderRequest) -> dict:
    validate_order_request(request)
    subtotal = calculate_subtotal(request.unit_price, request.quantity)
    total = apply_discount(subtotal, request.discount_code)
    return {
        "customer": request.customer_name,
        "product": request.product_name,
        "quantity": request.quantity,
        "subtotal": subtotal,
        "total": total,
    }


order = create_order(OrderRequest(
    customer_name="Alice",
    customer_email="alice@co.com",
    product_name="Widget",
    unit_price=29.99,
    quantity=3,
    discount_code="SAVE10",
))
print(order)
```

### 13.4 Code Organisation Patterns

```
project/
├── domain/                # Business entities and rules (no I/O)
│   ├── models.py          # Entities, value objects
│   ├── events.py          # Domain events
│   └── exceptions.py      # Domain-specific errors
├── application/           # Use cases / services
│   ├── services.py        # Application services
│   └── ports.py           # Protocols (interfaces)
├── infrastructure/        # External concerns
│   ├── repositories.py    # Database implementations
│   ├── email.py           # Email sender implementations
│   └── api_clients.py     # Third-party API clients
├── api/                   # Entry points
│   ├── routes.py          # HTTP handlers
│   └── schemas.py         # Request/response schemas
└── config.py              # Wiring / composition root
```

### 13.5 Refactoring Techniques

#### Extract Method

```python
# Before
class ReportGenerator:
    def generate(self, data: list) -> str:
        # Header
        header = "=" * 40 + "\n"
        header += "SALES REPORT\n"
        header += f"Generated: 2025-01-01\n"
        header += "=" * 40 + "\n"

        # Body
        body = ""
        total = 0
        for item in data:
            line = f"{item['product']}: ${item['amount']:.2f}\n"
            body += line
            total += item['amount']

        # Footer
        footer = "-" * 40 + "\n"
        footer += f"TOTAL: ${total:.2f}\n"
        footer += "=" * 40

        return header + body + footer


# After — extracted into focused methods
class ReportGenerator:
    def generate(self, data: list) -> str:
        return self._header() + self._body(data) + self._footer(data)

    def _header(self) -> str:
        return (
            f"{'=' * 40}\n"
            f"SALES REPORT\n"
            f"Generated: 2025-01-01\n"
            f"{'=' * 40}\n"
        )

    def _body(self, data: list) -> str:
        return "".join(f"{item['product']}: ${item['amount']:.2f}\n" for item in data)

    def _footer(self, data: list) -> str:
        total = sum(item["amount"] for item in data)
        return f"{'-' * 40}\nTOTAL: ${total:.2f}\n{'=' * 40}"
```

#### Replace Conditional with Polymorphism

```python
# Before
class NotificationSender:
    def send(self, channel: str, message: str, recipient: str) -> None:
        if channel == "email":
            print(f"Email to {recipient}: {message}")
        elif channel == "sms":
            print(f"SMS to {recipient}: {message}")
        elif channel == "push":
            print(f"Push to {recipient}: {message}")
        elif channel == "slack":
            print(f"Slack to {recipient}: {message}")


# After
from typing import Protocol, Dict


class NotificationChannel(Protocol):
    def send(self, message: str, recipient: str) -> None: ...


class EmailChannel:
    def send(self, message: str, recipient: str) -> None:
        print(f"Email to {recipient}: {message}")


class SMSChannel:
    def send(self, message: str, recipient: str) -> None:
        print(f"SMS to {recipient}: {message}")


class PushChannel:
    def send(self, message: str, recipient: str) -> None:
        print(f"Push to {recipient}: {message}")


class SlackChannel:
    def send(self, message: str, recipient: str) -> None:
        print(f"Slack to {recipient}: {message}")


class NotificationSender:
    def __init__(self) -> None:
        self._channels: Dict[str, NotificationChannel] = {}

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        self._channels[name] = channel

    def send(self, channel: str, message: str, recipient: str) -> None:
        if channel not in self._channels:
            raise ValueError(f"Unknown channel: {channel}")
        self._channels[channel].send(message, recipient)


sender = NotificationSender()
sender.register_channel("email", EmailChannel())
sender.register_channel("sms", SMSChannel())
sender.register_channel("push", PushChannel())
sender.register_channel("slack", SlackChannel())

sender.send("email", "Hello!", "alice@co.com")
sender.send("slack", "Deploy complete", "#engineering")
```

#### Introduce Parameter Object

```python
from dataclasses import dataclass
from typing import Optional


# Before: too many parameters
def search_products(
    query: str,
    category: str,
    min_price: float,
    max_price: float,
    in_stock: bool,
    sort_by: str,
    sort_order: str,
    page: int,
    page_size: int,
) -> list:
    ...


# After: parameter object
@dataclass
class ProductSearchCriteria:
    query: str
    category: Optional[str] = None
    min_price: float = 0.0
    max_price: float = float("inf")
    in_stock_only: bool = False
    sort_by: str = "relevance"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20


def search_products(criteria: ProductSearchCriteria) -> list:
    print(f"Searching: '{criteria.query}' in {criteria.category or 'all categories'}")
    print(f"  Price: ${criteria.min_price} - ${criteria.max_price}")
    print(f"  Sort: {criteria.sort_by} ({criteria.sort_order})")
    return []


search_products(ProductSearchCriteria(
    query="laptop",
    category="electronics",
    min_price=500,
    max_price=2000,
    in_stock_only=True,
))
```

---

## 14. Code Smells in LLD

Code smells are surface indicators of deeper design problems. They don't necessarily
mean the code is broken, but they suggest the design could be improved.

### 14.1 God Class

A class that knows too much or does too much. It centralises too many responsibilities.

```python
# SMELL: God Class
class ApplicationManager:
    def __init__(self):
        self.users = {}
        self.products = {}
        self.orders = {}
        self.payments = {}
        self.emails_sent = []
        self.db_connection = None

    def register_user(self, name, email): ...
    def authenticate_user(self, email, password): ...
    def create_product(self, name, price): ...
    def update_inventory(self, product_id, qty): ...
    def place_order(self, user_id, items): ...
    def process_payment(self, order_id, card): ...
    def send_email(self, to, subject, body): ...
    def generate_report(self, report_type): ...
    def backup_database(self): ...
    def clear_cache(self): ...


# FIX: Split into focused classes
class UserService:
    def register(self, name: str, email: str) -> dict: ...
    def authenticate(self, email: str, password: str) -> dict: ...

class ProductService:
    def create(self, name: str, price: float) -> dict: ...
    def update_inventory(self, product_id: str, qty: int) -> None: ...

class OrderService:
    def place_order(self, user_id: str, items: list) -> dict: ...

class PaymentService:
    def process(self, order_id: str, card: str) -> dict: ...

class EmailService:
    def send(self, to: str, subject: str, body: str) -> None: ...

class ReportService:
    def generate(self, report_type: str) -> str: ...
```

### 14.2 Feature Envy

A method that uses more data from another class than from its own.

```python
# SMELL: Feature Envy — calculate_shipping uses Order's data extensively
class ShippingCalculator:
    def calculate_shipping(self, order) -> float:
        weight = sum(item.weight * item.quantity for item in order.items)
        destination = order.customer.address.country
        is_fragile = any(item.is_fragile for item in order.items)
        subtotal = order.subtotal

        if destination == "US":
            rate = 0.5
        elif destination == "EU":
            rate = 1.2
        else:
            rate = 2.0

        cost = weight * rate
        if is_fragile:
            cost *= 1.5
        if subtotal > 100:
            cost *= 0.8
        return cost


# FIX: Move the logic closer to the data it uses
from dataclasses import dataclass
from typing import List


@dataclass
class OrderItem:
    name: str
    weight: float
    quantity: int
    is_fragile: bool
    price: float


class Order:
    def __init__(self, items: List[OrderItem], destination_country: str) -> None:
        self._items = items
        self._destination = destination_country

    @property
    def total_weight(self) -> float:
        return sum(item.weight * item.quantity for item in self._items)

    @property
    def has_fragile_items(self) -> bool:
        return any(item.is_fragile for item in self._items)

    @property
    def subtotal(self) -> float:
        return sum(item.price * item.quantity for item in self._items)

    @property
    def destination_country(self) -> str:
        return self._destination


class ShippingCalculator:
    RATES = {"US": 0.5, "EU": 1.2}
    DEFAULT_RATE = 2.0

    def calculate(self, order: Order) -> float:
        rate = self.RATES.get(order.destination_country, self.DEFAULT_RATE)
        cost = order.total_weight * rate
        if order.has_fragile_items:
            cost *= 1.5
        if order.subtotal > 100:
            cost *= 0.8
        return round(cost, 2)
```

### 14.3 Long Parameter List

```python
# SMELL
def create_employee(
    first_name, last_name, email, phone,
    street, city, state, zip_code, country,
    department, title, salary, start_date,
    manager_id, is_remote, has_parking
):
    ...


# FIX: Group related parameters into value objects
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class PersonalInfo:
    first_name: str
    last_name: str
    email: str
    phone: str


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str


@dataclass(frozen=True)
class EmploymentDetails:
    department: str
    title: str
    salary: float
    start_date: date
    manager_id: Optional[str] = None
    is_remote: bool = False


def create_employee(
    personal: PersonalInfo,
    address: Address,
    employment: EmploymentDetails,
) -> dict:
    return {
        "name": f"{personal.first_name} {personal.last_name}",
        "email": personal.email,
        "department": employment.department,
        "title": employment.title,
    }
```

### 14.4 Primitive Obsession

Using primitive types (str, int, float) where domain-specific types would be clearer
and safer.

```python
# SMELL: Primitives everywhere — easy to mix up parameters
def transfer_money(from_account: str, to_account: str, amount: float, currency: str) -> None:
    # from_account and to_account could easily be swapped
    # amount could be negative
    # currency could be any string
    ...


# FIX: Domain types prevent misuse
from dataclasses import dataclass


@dataclass(frozen=True)
class AccountId:
    value: str
    def __post_init__(self) -> None:
        if not self.value.startswith("ACC-"):
            raise ValueError(f"Invalid account ID: {self.value}")

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in ("USD", "EUR", "GBP", "INR"):
            raise ValueError(f"Unsupported currency: {self.currency}")

@dataclass(frozen=True)
class EmailAddress:
    value: str
    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise ValueError(f"Invalid email: {self.value}")

@dataclass(frozen=True)
class PhoneNumber:
    value: str
    def __post_init__(self) -> None:
        digits = "".join(c for c in self.value if c.isdigit())
        if len(digits) < 10:
            raise ValueError(f"Invalid phone number: {self.value}")


def transfer_money(from_account: AccountId, to_account: AccountId, amount: Money) -> None:
    print(f"Transferring {amount.amount} {amount.currency} from {from_account.value} to {to_account.value}")


# Type safety catches bugs at construction time
transfer_money(
    AccountId("ACC-001"),
    AccountId("ACC-002"),
    Money(100.0, "USD"),
)

# These would raise ValueError immediately:
try:
    Money(-50, "USD")
except ValueError as e:
    print(f"Caught: {e}")

try:
    AccountId("invalid")
except ValueError as e:
    print(f"Caught: {e}")
```

### 14.5 Shotgun Surgery

A single change requires editing many different classes/files. This indicates scattered
responsibilities.

```python
# SMELL: Adding a new user field requires changes in 5+ places

# In UserModel:       add field
# In UserSerializer:  add field to JSON
# In UserValidator:   add validation rule
# In UserForm:        add form field
# In UserDB:          alter migration
# In UserAPI:         update endpoint
# In UserTest:        update test data


# FIX: Centralise related concerns

from dataclasses import dataclass, fields
from typing import Dict, Any, List


@dataclass
class UserSchema:
    """Single source of truth for user fields and validation."""
    name: str
    email: str
    age: int

    VALIDATION_RULES: dict = None

    def __post_init__(self):
        self.VALIDATION_RULES = {
            "name": lambda v: isinstance(v, str) and len(v) >= 2,
            "email": lambda v: isinstance(v, str) and "@" in v,
            "age": lambda v: isinstance(v, int) and 0 < v < 150,
        }

    def validate(self) -> List[str]:
        errors = []
        for field_info in fields(self):
            if field_info.name == "VALIDATION_RULES":
                continue
            value = getattr(self, field_info.name)
            rule = self.VALIDATION_RULES.get(field_info.name)
            if rule and not rule(value):
                errors.append(f"Invalid {field_info.name}: {value}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self) if f.name != "VALIDATION_RULES"}

    @classmethod
    def from_dict(cls, data: dict) -> "UserSchema":
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name != "VALIDATION_RULES"})


user = UserSchema(name="Alice", email="alice@co.com", age=30)
print(f"Valid: {user.validate()}")      # []
print(f"Dict:  {user.to_dict()}")

bad_user = UserSchema(name="", email="nope", age=-5)
print(f"Errors: {bad_user.validate()}")  # 3 errors
```

### 14.6 How to Fix Each Smell — Summary

| Smell                | Detection Signal                         | Fix                                          |
|----------------------|------------------------------------------|-----------------------------------------------|
| God Class            | Class has 10+ methods, 5+ responsibilities | Split into focused classes                   |
| Feature Envy         | Method uses another object's data heavily | Move method to the class that owns the data  |
| Long Parameter List  | Function has 5+ parameters               | Introduce Parameter Object / dataclass        |
| Primitive Obsession  | Business values stored as raw str/int    | Create value object types                     |
| Shotgun Surgery      | One change touches 5+ files              | Centralise the scattered concern              |
| Data Clumps          | Same group of fields always appear together | Extract into a value object                 |
| Divergent Change      | One class changed for multiple unrelated reasons | Split by reason for change            |
| Refused Bequest      | Subclass doesn't use inherited methods   | Use composition instead of inheritance        |
| Message Chains       | `a.b().c().d()`                          | Apply Law of Demeter; provide direct methods  |
| Speculative Generality | Unused abstractions "just in case"     | Delete until actually needed (YAGNI)          |

---

## 15. Why Most Python LLD Solutions Fail

### 15.1 Common Mistakes in Interviews

1. **Jumping straight into code** — No upfront design, class identification, or
   relationship mapping.
2. **No abstractions** — Everything is concrete; swapping implementations means rewriting.
3. **Giant classes** — A single class with 200+ lines that does everything.
4. **No error handling** — Happy path only; no validation, no edge cases.
5. **Ignoring data modelling** — Using dicts everywhere instead of proper entities/VOs.
6. **Tight coupling** — Classes directly instantiate their dependencies.
7. **No separation of concerns** — Business logic mixed with I/O and formatting.
8. **Forgetting about concurrency** — No thread safety for shared mutable state.

### 15.2 Over-Engineering vs Under-Engineering

| Over-Engineering                              | Under-Engineering                             |
|-----------------------------------------------|-----------------------------------------------|
| Abstract Factory for 2 classes                | No interfaces at all                          |
| 7 design patterns in a parking lot system     | Single 500-line function                      |
| Generic framework for a specific problem      | Hardcoded values everywhere                   |
| 15 files for a simple feature                 | Everything in one file                        |
| Premature optimization                        | No thought about performance                  |

**The sweet spot:**

- Use patterns when they solve a *real* complexity problem, not to impress.
- Start simple, then refactor when complexity demands it.
- Follow SOLID principles naturally — don't force them.

```python
# Over-engineered for a simple need:
class AbstractLoggerFactory(ABC):
    @abstractmethod
    def create_logger(self) -> "AbstractLogger": ...

class AbstractLogger(ABC):
    @abstractmethod
    def log(self, msg: str) -> None: ...

class ConsoleLoggerFactory(AbstractLoggerFactory):
    def create_logger(self) -> "ConsoleLogger":
        return ConsoleLogger()

class ConsoleLogger(AbstractLogger):
    def log(self, msg: str) -> None:
        print(msg)

# Right-sized:
def log(msg: str) -> None:
    print(msg)

# Or if you need multiple loggers later, start with a Protocol:
from typing import Protocol

class Logger(Protocol):
    def log(self, msg: str) -> None: ...
```

### 15.3 Missing Error Handling

```python
# FAILING SOLUTION: No error handling
class ATM:
    def __init__(self, balance: float):
        self.balance = balance

    def withdraw(self, amount: float) -> float:
        self.balance -= amount  # what if amount > balance? Negative? Zero?
        return amount


# PASSING SOLUTION: Proper error handling
class ATMError(Exception):
    pass

class InsufficientFundsError(ATMError):
    pass

class InvalidAmountError(ATMError):
    pass


class ATM:
    MIN_WITHDRAWAL = 10
    MAX_WITHDRAWAL = 10000

    def __init__(self, balance: float) -> None:
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive")
        if amount < self.MIN_WITHDRAWAL:
            raise InvalidAmountError(f"Minimum withdrawal is ${self.MIN_WITHDRAWAL}")
        if amount > self.MAX_WITHDRAWAL:
            raise InvalidAmountError(f"Maximum withdrawal is ${self.MAX_WITHDRAWAL}")
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Cannot withdraw ${amount:.2f}. Available balance: ${self._balance:.2f}"
            )
        self._balance -= amount
        return amount


atm = ATM(500)
print(f"Balance: ${atm.balance}")

try:
    atm.withdraw(200)
    print(f"Withdrawn $200. Balance: ${atm.balance}")
except ATMError as e:
    print(f"Error: {e}")

try:
    atm.withdraw(400)
except InsufficientFundsError as e:
    print(f"Error: {e}")
```

### 15.4 Ignoring Concurrency

```python
import threading
from typing import Dict


# FAILING: Not thread-safe
class UnsafeCounter:
    def __init__(self) -> None:
        self.count = 0

    def increment(self) -> None:
        current = self.count
        self.count = current + 1  # race condition!


# PASSING: Thread-safe
class ThreadSafeCounter:
    def __init__(self) -> None:
        self._count = 0
        self._lock = threading.Lock()

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    def increment(self) -> None:
        with self._lock:
            self._count += 1

    def decrement(self) -> None:
        with self._lock:
            if self._count <= 0:
                raise ValueError("Counter cannot go below zero")
            self._count -= 1


class ThreadSafeCache:
    def __init__(self, max_size: int = 100) -> None:
        self._store: Dict[str, str] = {}
        self._lock = threading.RLock()
        self._max_size = max_size

    def get(self, key: str) -> str | None:
        with self._lock:
            return self._store.get(key)

    def put(self, key: str, value: str) -> None:
        with self._lock:
            if len(self._store) >= self._max_size and key not in self._store:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            self._store[key] = value

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Demonstrate thread safety
counter = ThreadSafeCounter()
threads = [threading.Thread(target=counter.increment) for _ in range(1000)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"Thread-safe count: {counter.count}")  # always 1000
```

### 15.5 Not Following SOLID

A quick reference for how SOLID maps to Python LLD:

| Principle               | Python Tool                            | Interview Signal                      |
|-------------------------|----------------------------------------|---------------------------------------|
| Single Responsibility   | Small focused classes                  | Each class has one reason to change   |
| Open/Closed             | Protocols + Strategy pattern           | New features = new classes, not edits |
| Liskov Substitution     | Proper inheritance, duck typing        | Subtypes honour parent's contract     |
| Interface Segregation   | Fine-grained Protocols                 | Clients depend only on what they use  |
| Dependency Inversion    | Constructor injection + Protocols      | High-level doesn't import low-level   |

### 15.6 Template for a Passing LLD Solution

Use this checklist / structure as a starting point for any LLD interview problem:

```python
"""
LLD Solution Template

Problem: [Name of the system]
Key requirements:
  1. ...
  2. ...
  3. ...
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import uuid
import threading


# ============================================================
# Step 1: Identify Enums (statuses, types, categories)
# ============================================================
class Status(Enum):
    ACTIVE = auto()
    INACTIVE = auto()


# ============================================================
# Step 2: Define Value Objects (immutable, equality by value)
# ============================================================
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)


# ============================================================
# Step 3: Define Entities (identity-based, mutable)
# ============================================================
@dataclass
class Entity:
    entity_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.entity_id == other.entity_id

    def __hash__(self) -> int:
        return hash(self.entity_id)


# ============================================================
# Step 4: Define Abstractions (Protocols for dependencies)
# ============================================================
class Repository(Protocol):
    def save(self, entity: Entity) -> None: ...
    def find_by_id(self, entity_id: str) -> Optional[Entity]: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, data: dict) -> None: ...


# ============================================================
# Step 5: Define Domain Exceptions
# ============================================================
class DomainException(Exception):
    pass

class ValidationException(DomainException):
    pass

class NotFoundException(DomainException):
    pass


# ============================================================
# Step 6: Implement Core Business Logic (Services)
# ============================================================
class CoreService:
    def __init__(
        self,
        repo: Repository,
        publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._publisher = publisher
        self._lock = threading.Lock()

    def create(self, **kwargs) -> Entity:
        # Validate
        self._validate(kwargs)

        # Create entity
        entity = Entity()

        # Persist
        with self._lock:
            self._repo.save(entity)

        # Publish event
        self._publisher.publish("entity.created", {"id": entity.entity_id})

        return entity

    def _validate(self, data: dict) -> None:
        errors = []
        # Add validation rules
        if errors:
            raise ValidationException(f"Validation failed: {', '.join(errors)}")


# ============================================================
# Step 7: Implement Infrastructure (concrete implementations)
# ============================================================
class InMemoryRepository:
    def __init__(self) -> None:
        self._store: Dict[str, Entity] = {}

    def save(self, entity: Entity) -> None:
        self._store[entity.entity_id] = entity

    def find_by_id(self, entity_id: str) -> Optional[Entity]:
        return self._store.get(entity_id)


class ConsoleEventPublisher:
    def publish(self, event_name: str, data: dict) -> None:
        print(f"[Event] {event_name}: {data}")


# ============================================================
# Step 8: Composition Root (wire everything together)
# ============================================================
def create_app() -> CoreService:
    repo = InMemoryRepository()
    publisher = ConsoleEventPublisher()
    return CoreService(repo=repo, publisher=publisher)


# ============================================================
# Step 9: Demonstrate Usage
# ============================================================
if __name__ == "__main__":
    service = create_app()
    entity = service.create()
    print(f"Created entity: {entity.entity_id}")
```

### Interview Execution Checklist

Before writing code, walk through this on paper or whiteboard:

1. **Clarify requirements** — Ask about scale, edge cases, and scope boundaries.
2. **Identify entities and value objects** — What are the nouns?
3. **Define relationships** — One-to-many? Aggregation? Composition?
4. **Identify behaviours** — What are the verbs? Which entity owns each?
5. **Spot abstractions** — Where do you need Protocols or ABCs?
6. **Design for extensibility** — Which requirements might change?
7. **Handle errors** — What can go wrong? Define exception types.
8. **Think about concurrency** — Is shared mutable state involved?
9. **Code top-down** — Start from the use case and drill into details.
10. **Walk through a scenario** — Trace a full happy path and one error path.

---

## Summary — Quick Reference Card

| Concept                  | Python Tool                 | Key Benefit                        |
|--------------------------|-----------------------------|------------------------------------|
| Dependency Injection     | Constructor params          | Testability, flexibility           |
| Encapsulation            | `_`, `__`, `@property`      | Invariant protection               |
| Abstraction              | ABC, @abstractmethod        | Contract enforcement               |
| Polymorphism             | Duck typing, overriding     | Interchangeable implementations    |
| Protocols                | `typing.Protocol`           | Structural subtyping               |
| Interface Segregation    | Fine-grained Protocols      | Clients depend only on what's used |
| Dependency Inversion     | Protocol + constructor DI   | Decoupled layers                   |
| Open/Closed              | Strategy + plugin patterns  | Extend without modifying           |
| Error Handling           | Custom exception hierarchy  | Clear failure semantics            |
| Domain Modelling         | Entities + Value Objects    | Business logic clarity             |
| Extensibility            | Hooks, events, plugins      | Future-proof design                |
| Testability              | DI + test doubles           | Fast, reliable tests               |
| Maintainability          | SRP, naming, small funcs    | Readable, changeable code          |
| Code Smells              | Pattern recognition         | Early detection of debt            |

> **Golden rule for Python LLD interviews:** Write code that another developer can read,
> test, and extend — without reading a single comment.

---

*Next up: [03 - Creational Design Patterns →](03-creational-design-patterns.md)*
