# Pythonic Design Patterns - Complete Guide

## Introduction: Why Design Patterns Still Matter in Python

Design patterns are reusable solutions to commonly occurring problems in software design.
They represent best practices refined over decades by experienced developers. Even in Python—a
language that renders some classical patterns trivial—understanding patterns remains essential.

### Patterns as Shared Vocabulary

When you say "let's use a Strategy here," every developer immediately understands:
- There are multiple interchangeable algorithms
- They share a common interface
- The client can swap them at runtime

This shared vocabulary accelerates design discussions, code reviews, and documentation.

### Python-Specific Idioms That Replace Some Patterns

Python's dynamic nature and first-class functions eliminate the need for some patterns entirely:

| Classical Pattern | Python Replacement |
|---|---|
| Strategy (simple) | Pass a function |
| Command (simple) | Pass a callable |
| Singleton | Module-level instance |
| Iterator | Generator functions |
| Template Method | Default arguments + callbacks |

### When Patterns Help vs Hurt

**Patterns help when:**
- The problem genuinely requires the flexibility the pattern provides
- Multiple team members need to understand the architecture
- The system will evolve and need extension points
- You're building a framework or library

**Patterns hurt when:**
- Applied prematurely ("just in case")
- The simpler Python idiom suffices
- They add layers of abstraction nobody navigates
- The team doesn't share the vocabulary

### How Patterns Come Up in LLD Interviews

In Low-Level Design interviews, patterns appear in two ways:
1. **Explicitly**: "Design a notification system using the Observer pattern"
2. **Implicitly**: The problem naturally calls for a pattern (e.g., "support undo" → Command + Memento)

The key is recognizing which pattern fits, implementing it cleanly, and articulating trade-offs.

---

## Creational Patterns

Creational patterns abstract the instantiation process, making systems independent of how
objects are created, composed, and represented.

---

## 1. Builder Pattern

### Intent
Separate the construction of a complex object from its representation, allowing the same
construction process to create different representations.

### Problem It Solves

Consider creating an object with 15+ optional parameters:

```python
# This is painful and error-prone
query = Query("users", ["name", "email"], "age > 18", "name ASC", 100, 0,
              True, False, None, "utf-8", 30, True, ["admin"], None, "v2")
```

The Builder pattern provides a step-by-step construction interface that's readable and flexible.

### UML-Style Structure

```
┌──────────┐       ┌──────────────┐       ┌─────────┐
│ Director │──────▶│   Builder    │──────▶│ Product │
└──────────┘       │  (Abstract)  │       └─────────┘
                   └──────────────┘
                          ▲
                          │
                   ┌──────────────┐
                   │ConcreteBuilder│
                   └──────────────┘
```

### Classic Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Query:
    """The product - a complex query object."""
    table: str = ""
    columns: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0
    joins: list[str] = field(default_factory=list)
    group_by: Optional[str] = None
    having: Optional[str] = None

    def to_sql(self) -> str:
        parts = []
        cols = ", ".join(self.columns) if self.columns else "*"
        parts.append(f"SELECT {cols}")
        parts.append(f"FROM {self.table}")

        for join in self.joins:
            parts.append(join)

        if self.conditions:
            parts.append("WHERE " + " AND ".join(self.conditions))

        if self.group_by:
            parts.append(f"GROUP BY {self.group_by}")

        if self.having:
            parts.append(f"HAVING {self.having}")

        if self.order_by:
            parts.append(f"ORDER BY {self.order_by}")

        if self.limit is not None:
            parts.append(f"LIMIT {self.limit}")

        if self.offset:
            parts.append(f"OFFSET {self.offset}")

        return "\n".join(parts)


class QueryBuilder(ABC):
    """Abstract builder interface."""

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def set_table(self, table: str) -> "QueryBuilder": ...

    @abstractmethod
    def set_columns(self, *columns: str) -> "QueryBuilder": ...

    @abstractmethod
    def add_condition(self, condition: str) -> "QueryBuilder": ...

    @abstractmethod
    def set_order(self, column: str, direction: str = "ASC") -> "QueryBuilder": ...

    @abstractmethod
    def set_limit(self, limit: int) -> "QueryBuilder": ...

    @abstractmethod
    def build(self) -> Query: ...


class SQLQueryBuilder(QueryBuilder):
    """Concrete builder for SQL queries."""

    def __init__(self):
        self._query = Query()

    def reset(self) -> None:
        self._query = Query()

    def set_table(self, table: str) -> "SQLQueryBuilder":
        self._query.table = table
        return self

    def set_columns(self, *columns: str) -> "SQLQueryBuilder":
        self._query.columns = list(columns)
        return self

    def add_condition(self, condition: str) -> "SQLQueryBuilder":
        self._query.conditions.append(condition)
        return self

    def add_join(self, join_clause: str) -> "SQLQueryBuilder":
        self._query.joins.append(join_clause)
        return self

    def set_order(self, column: str, direction: str = "ASC") -> "SQLQueryBuilder":
        self._query.order_by = f"{column} {direction}"
        return self

    def set_limit(self, limit: int) -> "SQLQueryBuilder":
        self._query.limit = limit
        return self

    def set_offset(self, offset: int) -> "SQLQueryBuilder":
        self._query.offset = offset
        return self

    def set_group_by(self, column: str) -> "SQLQueryBuilder":
        self._query.group_by = column
        return self

    def set_having(self, condition: str) -> "SQLQueryBuilder":
        self._query.having = condition
        return self

    def build(self) -> Query:
        result = self._query
        self.reset()
        return result
```

### Pythonic Implementation (Using dataclasses and kwargs)

```python
from dataclasses import dataclass, field
from typing import Optional, Self


@dataclass
class QueryConfig:
    """Pythonic builder using dataclass with defaults."""
    table: str
    columns: list[str] = field(default_factory=lambda: ["*"])
    conditions: list[str] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0
    joins: list[str] = field(default_factory=list)

    def where(self, condition: str) -> Self:
        """Fluent method for adding conditions."""
        self.conditions.append(condition)
        return self

    def join(self, clause: str) -> Self:
        self.joins.append(clause)
        return self

    def order(self, column: str, desc: bool = False) -> Self:
        direction = "DESC" if desc else "ASC"
        self.order_by = f"{column} {direction}"
        return self

    def paginate(self, page: int, per_page: int = 20) -> Self:
        self.limit = per_page
        self.offset = (page - 1) * per_page
        return self


# Usage - clean and Pythonic
query = (
    QueryConfig(table="users", columns=["id", "name", "email"])
    .where("age > 18")
    .where("active = true")
    .join("LEFT JOIN orders ON users.id = orders.user_id")
    .order("created_at", desc=True)
    .paginate(page=2, per_page=50)
)
```

### Fluent Builder with Method Chaining

```python
from typing import Self


class HttpRequestBuilder:
    """Fluent builder for HTTP requests."""

    def __init__(self):
        self._method: str = "GET"
        self._url: str = ""
        self._headers: dict[str, str] = {}
        self._params: dict[str, str] = {}
        self._body: Optional[str] = None
        self._timeout: int = 30
        self._retries: int = 0

    def method(self, method: str) -> Self:
        self._method = method.upper()
        return self

    def url(self, url: str) -> Self:
        self._url = url
        return self

    def header(self, key: str, value: str) -> Self:
        self._headers[key] = value
        return self

    def param(self, key: str, value: str) -> Self:
        self._params[key] = value
        return self

    def body(self, content: str) -> Self:
        self._body = content
        return self

    def timeout(self, seconds: int) -> Self:
        self._timeout = seconds
        return self

    def retries(self, count: int) -> Self:
        self._retries = count
        return self

    def build(self) -> "HttpRequest":
        if not self._url:
            raise ValueError("URL is required")
        return HttpRequest(
            method=self._method,
            url=self._url,
            headers=self._headers.copy(),
            params=self._params.copy(),
            body=self._body,
            timeout=self._timeout,
            retries=self._retries,
        )


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, str]
    body: Optional[str]
    timeout: int
    retries: int


# Usage
request = (
    HttpRequestBuilder()
    .method("POST")
    .url("https://api.example.com/users")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token123")
    .body('{"name": "Alice"}')
    .timeout(10)
    .retries(3)
    .build()
)
```

### Director Pattern

```python
class QueryDirector:
    """Director knows how to build common query patterns."""

    def __init__(self, builder: SQLQueryBuilder):
        self._builder = builder

    def build_user_list_query(self, active_only: bool = True) -> Query:
        self._builder.reset()
        self._builder.set_table("users")
        self._builder.set_columns("id", "name", "email", "created_at")
        if active_only:
            self._builder.add_condition("active = true")
        self._builder.set_order("created_at", "DESC")
        self._builder.set_limit(100)
        return self._builder.build()

    def build_user_stats_query(self) -> Query:
        self._builder.reset()
        self._builder.set_table("users")
        self._builder.set_columns("department", "COUNT(*) as count", "AVG(salary) as avg_salary")
        self._builder.add_condition("active = true")
        self._builder.set_group_by("department")
        self._builder.set_having("COUNT(*) > 5")
        self._builder.set_order("count", "DESC")
        return self._builder.build()


# Usage
builder = SQLQueryBuilder()
director = QueryDirector(builder)

user_list = director.build_user_list_query(active_only=True)
print(user_list.to_sql())

stats = director.build_user_stats_query()
print(stats.to_sql())
```

### When to Use / When NOT to Use

**Use when:**
- Object has many optional parameters (>4-5)
- Construction involves multiple steps that can vary
- You need to create different representations of the same type
- Object should be immutable once constructed

**Don't use when:**
- Object is simple (few parameters)
- Python's keyword arguments suffice
- `dataclass` with defaults covers the use case

### Common Mistakes
- Making the builder too generic (over-abstraction)
- Not resetting builder state between builds
- Allowing partially-constructed invalid objects
- Not validating in the `build()` method

---

## 2. Factory Pattern (Factory Method)

### Intent
Define an interface for creating an object, but let subclasses decide which class to instantiate.

### Problem It Solves

When object creation logic is complex, or the exact type of object to create is determined
at runtime, scattering `if/elif` chains and constructor calls across the codebase creates
tight coupling and violates the Open/Closed Principle.

### UML-Style Structure

```
┌──────────────────┐         ┌────────────────┐
│    Creator       │         │    Product     │
│  (Abstract)      │         │   (Abstract)   │
├──────────────────┤         └────────────────┘
│+ factory_method()│                  ▲
│+ operation()     │                  │
└──────────────────┘         ┌───────┴────────┐
         ▲                   │                │
         │              ┌─────────┐     ┌─────────┐
┌──────────────────┐    │ProductA │     │ProductB │
│ ConcreteCreator  │    └─────────┘     └─────────┘
├──────────────────┤
│+ factory_method()│
└──────────────────┘
```

### Simple Factory vs Factory Method

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


# --- Product hierarchy ---

class Notification(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool: ...


class EmailNotification(Notification):
    def __init__(self, smtp_host: str = "smtp.gmail.com", smtp_port: int = 587):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port

    def send(self, recipient: str, message: str) -> bool:
        if not self.validate_recipient(recipient):
            return False
        print(f"Sending email to {recipient} via {self._smtp_host}:{self._smtp_port}")
        print(f"  Message: {message}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return "@" in recipient and "." in recipient


class SMSNotification(Notification):
    def __init__(self, api_key: str = "default-key", sender_id: str = "MYAPP"):
        self._api_key = api_key
        self._sender_id = sender_id

    def send(self, recipient: str, message: str) -> bool:
        if not self.validate_recipient(recipient):
            return False
        print(f"Sending SMS to {recipient} from {self._sender_id}")
        print(f"  Message: {message[:160]}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return recipient.startswith("+") and len(recipient) >= 10


class PushNotification(Notification):
    def __init__(self, platform: str = "firebase"):
        self._platform = platform

    def send(self, recipient: str, message: str) -> bool:
        if not self.validate_recipient(recipient):
            return False
        print(f"Sending push via {self._platform} to device {recipient[:20]}...")
        print(f"  Message: {message[:256]}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return len(recipient) > 20  # Device tokens are long


# --- Simple Factory (not a GoF pattern, but common) ---

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class SimpleNotificationFactory:
    """Simple factory - just a method that creates objects."""

    @staticmethod
    def create(notification_type: NotificationType, **kwargs) -> Notification:
        factories = {
            NotificationType.EMAIL: EmailNotification,
            NotificationType.SMS: SMSNotification,
            NotificationType.PUSH: PushNotification,
        }
        factory = factories.get(notification_type)
        if factory is None:
            raise ValueError(f"Unknown notification type: {notification_type}")
        return factory(**kwargs)


# Usage
notif = SimpleNotificationFactory.create(NotificationType.EMAIL, smtp_host="mail.company.com")
notif.send("user@example.com", "Hello!")
```

### Python Implementation with Class Methods

```python
class Notification(ABC):
    """Base notification with factory method."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...

    @classmethod
    def create(cls, channel: str, **kwargs) -> "Notification":
        """Factory method using class method - very Pythonic."""
        registry = {
            "email": EmailNotification,
            "sms": SMSNotification,
            "push": PushNotification,
        }
        klass = registry.get(channel.lower())
        if klass is None:
            raise ValueError(f"Unknown channel: {channel}")
        return klass(**kwargs)
```

### Registration-Based Factory

```python
from typing import Callable, TypeVar

T = TypeVar("T")


class NotificationFactory:
    """Registration-based factory - open for extension without modification."""

    _registry: dict[str, type[Notification]] = {}

    @classmethod
    def register(cls, channel: str) -> Callable[[type[Notification]], type[Notification]]:
        """Decorator to register notification types."""
        def decorator(klass: type[Notification]) -> type[Notification]:
            cls._registry[channel.lower()] = klass
            return klass
        return decorator

    @classmethod
    def create(cls, channel: str, **kwargs) -> Notification:
        klass = cls._registry.get(channel.lower())
        if klass is None:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown channel '{channel}'. Available: {available}"
            )
        return klass(**kwargs)

    @classmethod
    def available_channels(cls) -> list[str]:
        return list(cls._registry.keys())


@NotificationFactory.register("email")
class EmailNotification(Notification):
    def __init__(self, smtp_host: str = "smtp.gmail.com", **kwargs):
        self._smtp_host = smtp_host

    def send(self, recipient: str, message: str) -> bool:
        print(f"Email to {recipient}: {message}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return "@" in recipient


@NotificationFactory.register("sms")
class SMSNotification(Notification):
    def __init__(self, api_key: str = "", **kwargs):
        self._api_key = api_key

    def send(self, recipient: str, message: str) -> bool:
        print(f"SMS to {recipient}: {message}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return recipient.startswith("+")


@NotificationFactory.register("push")
class PushNotification(Notification):
    def __init__(self, platform: str = "firebase", **kwargs):
        self._platform = platform

    def send(self, recipient: str, message: str) -> bool:
        print(f"Push to {recipient}: {message}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return len(recipient) > 10


# Now adding a new channel requires ZERO changes to existing code
@NotificationFactory.register("slack")
class SlackNotification(Notification):
    def __init__(self, webhook_url: str = "", **kwargs):
        self._webhook_url = webhook_url

    def send(self, recipient: str, message: str) -> bool:
        print(f"Slack to #{recipient}: {message}")
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return not recipient.startswith("#")


# Usage
email = NotificationFactory.create("email", smtp_host="mail.corp.com")
email.send("dev@corp.com", "Build passed!")

slack = NotificationFactory.create("slack", webhook_url="https://hooks.slack.com/...")
slack.send("engineering", "Deployment complete")

print(f"Available channels: {NotificationFactory.available_channels()}")
```

### When to Use / When NOT to Use

**Use when:**
- The exact type to create is determined at runtime
- You want to centralize and encapsulate creation logic
- Adding new types should not require modifying existing code (OCP)
- Creation involves non-trivial setup

**Don't use when:**
- Only one product type exists
- Direct instantiation is clear and simple
- The factory would have exactly one method returning one type

### Common Mistakes
- Factory that returns only one type (unnecessary indirection)
- Forgetting to validate parameters before construction
- Putting business logic inside the factory (it should only create)
- Not handling unknown types gracefully

---

## 3. Abstract Factory Pattern

### Intent
Provide an interface for creating families of related objects without specifying their
concrete classes.

### Problem It Solves

When a system must work with multiple families of related products, and you want to ensure
that products from one family aren't mixed with another. For example, a UI toolkit that
supports multiple platforms (Windows, macOS, Linux) needs buttons, checkboxes, and menus
that all belong to the same platform.

### UML-Style Structure

```
┌─────────────────────┐
│  AbstractFactory     │
├─────────────────────┤
│+ create_button()     │
│+ create_checkbox()   │
│+ create_menu()       │
└─────────────────────┘
          ▲
     ┌────┴────────────────────┐
     │                         │
┌────────────────┐    ┌────────────────┐
│ WindowsFactory │    │  MacFactory    │
├────────────────┤    ├────────────────┤
│+create_button()│    │+create_button()│
│+create_checkbox│    │+create_checkbox│
└────────────────┘    └────────────────┘
```

### Full Python Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


# --- Abstract Products ---

class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...

    @abstractmethod
    def on_click(self, handler: callable) -> None: ...


class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str: ...

    @abstractmethod
    def toggle(self) -> None: ...

    @property
    @abstractmethod
    def checked(self) -> bool: ...


class TextField(ABC):
    @abstractmethod
    def render(self) -> str: ...

    @abstractmethod
    def set_value(self, value: str) -> None: ...

    @abstractmethod
    def get_value(self) -> str: ...


# --- Concrete Products: Material Design ---

class MaterialButton(Button):
    def __init__(self, label: str):
        self._label = label
        self._handler = None

    def render(self) -> str:
        return f'<md-button elevation="2">{self._label}</md-button>'

    def on_click(self, handler: callable) -> None:
        self._handler = handler


class MaterialCheckbox(Checkbox):
    def __init__(self, label: str):
        self._label = label
        self._checked = False

    def render(self) -> str:
        state = "checked" if self._checked else ""
        return f'<md-checkbox {state}>{self._label}</md-checkbox>'

    def toggle(self) -> None:
        self._checked = not self._checked

    @property
    def checked(self) -> bool:
        return self._checked


class MaterialTextField(TextField):
    def __init__(self, placeholder: str = ""):
        self._value = ""
        self._placeholder = placeholder

    def render(self) -> str:
        return f'<md-text-field placeholder="{self._placeholder}" value="{self._value}"/>'

    def set_value(self, value: str) -> None:
        self._value = value

    def get_value(self) -> str:
        return self._value


# --- Concrete Products: iOS Style ---

class IOSButton(Button):
    def __init__(self, label: str):
        self._label = label
        self._handler = None

    def render(self) -> str:
        return f'<UIButton style="rounded">{self._label}</UIButton>'

    def on_click(self, handler: callable) -> None:
        self._handler = handler


class IOSCheckbox(Checkbox):
    def __init__(self, label: str):
        self._label = label
        self._checked = False

    def render(self) -> str:
        state = "on" if self._checked else "off"
        return f'<UISwitch state="{state}"/><UILabel>{self._label}</UILabel>'

    def toggle(self) -> None:
        self._checked = not self._checked

    @property
    def checked(self) -> bool:
        return self._checked


class IOSTextField(TextField):
    def __init__(self, placeholder: str = ""):
        self._value = ""
        self._placeholder = placeholder

    def render(self) -> str:
        return f'<UITextField placeholder="{self._placeholder}">{self._value}</UITextField>'

    def set_value(self, value: str) -> None:
        self._value = value

    def get_value(self) -> str:
        return self._value


# --- Abstract Factory ---

class UIFactory(ABC):
    @abstractmethod
    def create_button(self, label: str) -> Button: ...

    @abstractmethod
    def create_checkbox(self, label: str) -> Checkbox: ...

    @abstractmethod
    def create_text_field(self, placeholder: str = "") -> TextField: ...


class MaterialUIFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return MaterialButton(label)

    def create_checkbox(self, label: str) -> Checkbox:
        return MaterialCheckbox(label)

    def create_text_field(self, placeholder: str = "") -> TextField:
        return MaterialTextField(placeholder)


class IOSUIFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return IOSButton(label)

    def create_checkbox(self, label: str) -> Checkbox:
        return IOSCheckbox(label)

    def create_text_field(self, placeholder: str = "") -> TextField:
        return IOSTextField(placeholder)


# --- Client code works with any factory ---

class LoginForm:
    """Client that uses abstract factory - completely platform-agnostic."""

    def __init__(self, factory: UIFactory):
        self._username = factory.create_text_field("Enter username")
        self._password = factory.create_text_field("Enter password")
        self._remember_me = factory.create_checkbox("Remember me")
        self._submit = factory.create_button("Log In")
        self._submit.on_click(self._handle_submit)

    def render(self) -> str:
        return "\n".join([
            "<form>",
            f"  {self._username.render()}",
            f"  {self._password.render()}",
            f"  {self._remember_me.render()}",
            f"  {self._submit.render()}",
            "</form>",
        ])

    def _handle_submit(self):
        print(f"Logging in: {self._username.get_value()}")


# --- Factory selection ---

def get_ui_factory(platform: str) -> UIFactory:
    factories = {
        "android": MaterialUIFactory,
        "web": MaterialUIFactory,
        "ios": IOSUIFactory,
        "macos": IOSUIFactory,
    }
    factory_class = factories.get(platform.lower())
    if factory_class is None:
        raise ValueError(f"Unsupported platform: {platform}")
    return factory_class()


# Usage
factory = get_ui_factory("ios")
form = LoginForm(factory)
print(form.render())

factory = get_ui_factory("android")
form = LoginForm(factory)
print(form.render())
```

### When to Use vs Simple Factory

| Criteria | Simple Factory | Abstract Factory |
|---|---|---|
| Number of product types | One | Multiple related |
| Product families | No | Yes |
| Ensures consistency | No | Yes (all from same family) |
| Complexity | Low | Higher |

### When to Use / When NOT to Use

**Use when:**
- System must work with multiple families of related products
- You want to enforce that products from the same family are used together
- Product families will be extended with new variants

**Don't use when:**
- Only one product type exists (use Factory Method)
- Products from different families can mix freely
- The number of families is fixed and tiny (2 with no growth expected)

### Common Mistakes
- Creating an abstract factory for a single product type
- Violating the family constraint (mixing products from different factories)
- Making the factory hierarchy too deep

---

## 4. Singleton Pattern

### Intent
Ensure a class has only one instance and provide a global point of access to it.

### Problem It Solves

Some resources should exist exactly once: database connection pools, configuration managers,
logging infrastructure, hardware interface managers. Singleton ensures controlled access to
a shared resource.

### Why and When to Use (Rarely!)

Singleton is the most overused and abused pattern. Use it only when:
- Exactly one instance must coordinate actions across the system
- The instance manages a truly shared resource (connection pool, thread pool)
- The instance is stateless or its state is truly global

### UML-Style Structure

```
┌─────────────────────────────┐
│        Singleton            │
├─────────────────────────────┤
│ - _instance: Singleton      │
├─────────────────────────────┤
│ + get_instance(): Singleton │
│ - __init__()                │
└─────────────────────────────┘
```

### Module-Level Singleton (Pythonic Way)

The simplest and most Pythonic approach—Python modules are singletons by nature:

```python
# config.py - This IS a singleton. Python modules are only loaded once.

import json
from pathlib import Path


class _Config:
    """Internal config class - underscore signals 'don't instantiate directly'."""

    def __init__(self):
        self._settings: dict = {}
        self._loaded = False

    def load(self, path: str = "config.json") -> None:
        config_path = Path(path)
        if config_path.exists():
            self._settings = json.loads(config_path.read_text())
        self._loaded = True

    def get(self, key: str, default=None):
        if not self._loaded:
            self.load()
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        self._settings[key] = value


# Module-level instance - this is the singleton
config = _Config()


# Usage in other modules:
# from config import config
# db_url = config.get("database_url")
```

### `__new__`-Based Singleton

```python
class DatabasePool:
    """Singleton using __new__."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, connection_string: str = "", pool_size: int = 5):
        if self._initialized:
            return
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._connections: list = []
        self._initialized = True
        print(f"Pool created: {connection_string} (size={pool_size})")

    def get_connection(self):
        if not self._connections:
            return f"new_conn({self._connection_string})"
        return self._connections.pop()

    def release_connection(self, conn):
        if len(self._connections) < self._pool_size:
            self._connections.append(conn)


# Both variables point to the same instance
pool1 = DatabasePool("postgresql://localhost/mydb", pool_size=10)
pool2 = DatabasePool("different_string", pool_size=20)  # Ignored!
assert pool1 is pool2
```

### Metaclass-Based Singleton

```python
class SingletonMeta(type):
    """Metaclass that creates singleton classes."""

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AppLogger(metaclass=SingletonMeta):
    """Logger singleton via metaclass."""

    def __init__(self, name: str = "app"):
        self._name = name
        self._handlers: list = []
        self._level = "INFO"

    def set_level(self, level: str) -> None:
        self._level = level

    def add_handler(self, handler) -> None:
        self._handlers.append(handler)

    def log(self, level: str, message: str) -> None:
        print(f"[{self._name}] {level}: {message}")


# Same instance regardless of arguments
logger1 = AppLogger("main")
logger2 = AppLogger("other")
assert logger1 is logger2
print(logger1._name)  # "main" - first call wins
```

### Thread-Safe Singleton

```python
import threading


class ThreadSafeSingleton:
    """Thread-safe singleton using double-checked locking."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-check after acquiring lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._data = {}
        self._data_lock = threading.RLock()

    def set(self, key: str, value) -> None:
        with self._data_lock:
            self._data[key] = value

    def get(self, key: str, default=None):
        with self._data_lock:
            return self._data.get(key, default)
```

### Why Singleton Is Often an Anti-Pattern

1. **Hidden dependencies**: Code that uses a singleton has an implicit dependency
2. **Testing difficulty**: Hard to mock or replace in tests
3. **Tight coupling**: Every user is coupled to the concrete singleton class
4. **State sharing**: Global mutable state makes reasoning about code difficult
5. **Concurrency issues**: Shared mutable state requires synchronization

### Alternatives: Dependency Injection

```python
from typing import Protocol


class Logger(Protocol):
    def log(self, level: str, message: str) -> None: ...


class ConsoleLogger:
    def log(self, level: str, message: str) -> None:
        print(f"[{level}] {message}")


class FileLogger:
    def __init__(self, path: str):
        self._path = path

    def log(self, level: str, message: str) -> None:
        with open(self._path, "a") as f:
            f.write(f"[{level}] {message}\n")


class OrderService:
    """Instead of using a singleton logger, accept it as a dependency."""

    def __init__(self, logger: Logger):
        self._logger = logger

    def place_order(self, order_id: str) -> None:
        self._logger.log("INFO", f"Order placed: {order_id}")


# In production
service = OrderService(ConsoleLogger())

# In tests - easily mockable!
class MockLogger:
    def __init__(self):
        self.messages = []

    def log(self, level: str, message: str) -> None:
        self.messages.append((level, message))

test_logger = MockLogger()
service = OrderService(test_logger)
service.place_order("ORD-123")
assert test_logger.messages == [("INFO", "Order placed: ORD-123")]
```

### When to Use / When NOT to Use

**Use when:**
- Exactly one instance managing a shared resource (connection pool, hardware)
- Module-level singleton is the Pythonic default choice
- The singleton is essentially stateless (configuration reader)

**Don't use when:**
- You just want "easy global access" (use DI instead)
- The class has mutable state accessed from multiple threads
- You need different instances in tests vs production
- Multiple instances would actually be fine

### Common Mistakes
- Using singleton for convenience rather than necessity
- Not handling thread safety
- Making everything a singleton
- Forgetting that singleton state persists across test cases

---

## 5. Prototype Pattern

### Intent
Create new objects by copying existing ones, avoiding the cost of creation from scratch.

### Problem It Solves

When object creation is expensive (complex initialization, database queries, network calls)
or when you need many variations of a base configuration, cloning an existing object is
more efficient than constructing from scratch.

### UML-Style Structure

```
┌────────────────┐
│   Prototype    │
├────────────────┤
│+ clone()       │
└────────────────┘
        ▲
        │
┌────────────────┐       ┌──────────────┐
│ConcretePrototype│      │   Registry   │
├────────────────┤       ├──────────────┤
│+ clone()       │◀──────│+ get(name)   │
└────────────────┘       │+ register()  │
                         └──────────────┘
```

### Deep Copy vs Shallow Copy

```python
import copy


class Address:
    def __init__(self, street: str, city: str, country: str):
        self.street = street
        self.city = city
        self.country = country

    def __repr__(self):
        return f"{self.street}, {self.city}, {self.country}"


class Employee:
    def __init__(self, name: str, role: str, address: Address, skills: list[str]):
        self.name = name
        self.role = role
        self.address = address
        self.skills = skills

    def __repr__(self):
        return f"Employee({self.name}, {self.role}, {self.address})"


# Demonstrate the difference
original = Employee(
    name="Alice",
    role="Engineer",
    address=Address("123 Main St", "Springfield", "US"),
    skills=["Python", "SQL"],
)

# Shallow copy - nested objects are SHARED
shallow = copy.copy(original)
shallow.name = "Bob"  # Independent (immutable string)
shallow.address.city = "Shelbyville"  # SHARED - modifies original too!
print(original.address.city)  # "Shelbyville" - OOPS!

# Deep copy - completely independent
original.address.city = "Springfield"  # Fix it
deep = copy.deepcopy(original)
deep.name = "Charlie"
deep.address.city = "Capital City"  # Independent
print(original.address.city)  # "Springfield" - safe
```

### Implementation with `__copy__` and `__deepcopy__`

```python
import copy
from typing import Self


class GameCharacter:
    """Game character with custom copy behavior."""

    _id_counter = 0

    def __init__(self, name: str, char_class: str, level: int = 1):
        GameCharacter._id_counter += 1
        self.id = GameCharacter._id_counter
        self.name = name
        self.char_class = char_class
        self.level = level
        self.hp = 100 + (level * 10)
        self.inventory: list[str] = []
        self.position: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._loaded_assets: list = []  # Expensive to recreate

    def __copy__(self) -> Self:
        """Shallow copy with new ID but shared inventory."""
        new = self.__class__.__new__(self.__class__)
        GameCharacter._id_counter += 1
        new.id = GameCharacter._id_counter
        new.name = f"{self.name}_copy"
        new.char_class = self.char_class
        new.level = self.level
        new.hp = self.hp
        new.inventory = self.inventory  # Shared reference!
        new.position = self.position.copy()  # Shallow dict copy is fine for flat dicts
        new._loaded_assets = self._loaded_assets  # Share expensive assets
        return new

    def __deepcopy__(self, memo: dict) -> Self:
        """Deep copy with fully independent state."""
        new = self.__class__.__new__(self.__class__)
        memo[id(self)] = new
        GameCharacter._id_counter += 1
        new.id = GameCharacter._id_counter
        new.name = f"{self.name}_clone"
        new.char_class = self.char_class
        new.level = self.level
        new.hp = self.hp
        new.inventory = copy.deepcopy(self.inventory, memo)
        new.position = copy.deepcopy(self.position, memo)
        new._loaded_assets = self._loaded_assets  # Still share assets (immutable/expensive)
        return new

    def clone(self) -> Self:
        """Convenience method for deep copy."""
        return copy.deepcopy(self)

    def __repr__(self):
        return (f"Character(id={self.id}, name={self.name}, "
                f"class={self.char_class}, lvl={self.level})")
```

### Registry of Prototypes

```python
import copy
from typing import Any


class PrototypeRegistry:
    """Registry that stores and clones prototype objects."""

    def __init__(self):
        self._prototypes: dict[str, Any] = {}

    def register(self, name: str, prototype: Any) -> None:
        self._prototypes[name] = prototype

    def unregister(self, name: str) -> None:
        self._prototypes.pop(name, None)

    def clone(self, name: str, **overrides) -> Any:
        """Clone a registered prototype and apply overrides."""
        prototype = self._prototypes.get(name)
        if prototype is None:
            available = ", ".join(self._prototypes.keys())
            raise KeyError(f"No prototype '{name}'. Available: {available}")

        cloned = copy.deepcopy(prototype)

        for attr, value in overrides.items():
            if hasattr(cloned, attr):
                setattr(cloned, attr, value)
            else:
                raise AttributeError(
                    f"{type(cloned).__name__} has no attribute '{attr}'"
                )

        return cloned

    @property
    def available(self) -> list[str]:
        return list(self._prototypes.keys())


# --- Real Example: Game Object Cloning ---

class Enemy:
    def __init__(self, name: str, hp: int, damage: int, speed: float,
                 abilities: list[str], loot_table: dict[str, float]):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.speed = speed
        self.abilities = abilities
        self.loot_table = loot_table
        self.position = {"x": 0.0, "y": 0.0}
        self.is_alive = True

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.is_alive = False

    def __repr__(self):
        return f"Enemy({self.name}, HP={self.hp}/{self.max_hp})"


# Setup registry with base enemy templates
enemy_registry = PrototypeRegistry()

enemy_registry.register("goblin", Enemy(
    name="Goblin",
    hp=50,
    damage=10,
    speed=1.5,
    abilities=["slash", "dodge"],
    loot_table={"gold": 0.8, "dagger": 0.1, "potion": 0.3},
))

enemy_registry.register("dragon", Enemy(
    name="Dragon",
    hp=500,
    damage=80,
    speed=0.8,
    abilities=["fire_breath", "tail_sweep", "fly", "roar"],
    loot_table={"gold": 1.0, "dragon_scale": 0.5, "legendary_weapon": 0.05},
))

enemy_registry.register("skeleton", Enemy(
    name="Skeleton",
    hp=30,
    damage=15,
    speed=1.0,
    abilities=["bone_throw", "reassemble"],
    loot_table={"gold": 0.5, "bone": 0.9, "shield": 0.1},
))


# Spawn enemies by cloning prototypes
def spawn_enemies(registry: PrototypeRegistry, wave: int) -> list[Enemy]:
    """Spawn a wave of enemies by cloning prototypes."""
    enemies = []

    for i in range(5):
        goblin = registry.clone("goblin", name=f"Goblin_{wave}_{i}")
        goblin.position = {"x": float(i * 10), "y": float(wave * 5)}
        goblin.hp = int(goblin.hp * (1 + wave * 0.1))  # Scale with wave
        enemies.append(goblin)

    if wave >= 3:
        dragon = registry.clone("dragon", name=f"Dragon_Boss_{wave}")
        dragon.hp = int(dragon.hp * (1 + wave * 0.2))
        enemies.append(dragon)

    return enemies


wave_1 = spawn_enemies(enemy_registry, wave=1)
wave_5 = spawn_enemies(enemy_registry, wave=5)
print(f"Wave 1: {len(wave_1)} enemies")
print(f"Wave 5: {len(wave_5)} enemies")
print(f"Dragon boss HP: {wave_5[-1].hp}")
```

### When to Use / When NOT to Use

**Use when:**
- Object creation is expensive (parsing, DB queries, network)
- You need many similar objects with small variations
- The class hierarchy of products is not known at compile time
- You want to avoid building parallel factory hierarchies

**Don't use when:**
- Objects are cheap to create
- Objects have few circular references (deepcopy handles them but adds complexity)
- The prototype state is simple enough to just pass as constructor args

### Common Mistakes
- Using shallow copy when deep copy is needed (shared mutable state bugs)
- Not handling circular references in custom `__deepcopy__`
- Forgetting to reset unique identifiers (IDs, timestamps) after cloning
- Cloning objects that hold non-copyable resources (file handles, sockets)

---

## Structural Patterns

Structural patterns deal with object composition, creating relationships between objects
to form larger structures while keeping these structures flexible and efficient.

---

## 6. Adapter Pattern

### Intent
Convert the interface of a class into another interface that clients expect, enabling
classes with incompatible interfaces to work together.

### Problem It Solves

You have existing code that works with a specific interface, but you need to integrate a
third-party library or legacy system that has a different interface. The adapter bridges
the gap without modifying either side.

### UML-Style Structure

```
┌────────────┐       ┌────────────────┐       ┌──────────────┐
│   Client   │──────▶│   Target       │       │   Adaptee    │
│            │       │  (Interface)   │       │  (Legacy)    │
└────────────┘       └────────────────┘       └──────────────┘
                              ▲                       ▲
                              │                       │
                     ┌────────────────┐               │
                     │    Adapter     │───────────────┘
                     │               │  (delegates to adaptee)
                     └────────────────┘
```

### Class Adapter vs Object Adapter

```python
from abc import ABC, abstractmethod
from typing import Protocol


# --- Target Interface (what our system expects) ---

class PaymentProcessor(Protocol):
    """Interface our system expects for payment processing."""

    def charge(self, amount: float, currency: str, card_token: str) -> dict:
        """Charge a payment and return result."""
        ...

    def refund(self, transaction_id: str, amount: float) -> dict:
        """Refund a transaction."""
        ...

    def get_status(self, transaction_id: str) -> str:
        """Get transaction status."""
        ...


# --- Adaptee (legacy third-party API with different interface) ---

class LegacyPaymentGateway:
    """Legacy payment system with completely different interface."""

    def make_payment(self, amount_cents: int, currency_code: str,
                     card_number: str, expiry: str, cvv: str) -> str:
        """Returns transaction reference string."""
        print(f"Legacy: Charging {amount_cents} cents ({currency_code})")
        return f"TXN-{id(self)}-{amount_cents}"

    def reverse_payment(self, reference: str, amount_cents: int,
                        reason: str = "customer_request") -> bool:
        """Returns True if reversal succeeded."""
        print(f"Legacy: Reversing {reference} for {amount_cents} cents")
        return True

    def check_payment_status(self, reference: str) -> int:
        """Returns status code: 0=pending, 1=completed, 2=failed, 3=reversed."""
        return 1


# --- Object Adapter ---

class LegacyPaymentAdapter:
    """Adapts LegacyPaymentGateway to our PaymentProcessor interface."""

    STATUS_MAP = {
        0: "pending",
        1: "completed",
        2: "failed",
        3: "reversed",
    }

    def __init__(self, gateway: LegacyPaymentGateway):
        self._gateway = gateway
        self._token_to_card: dict[str, tuple[str, str, str]] = {}

    def register_card_token(self, token: str, number: str, expiry: str, cvv: str):
        """Map our token system to the legacy card details."""
        self._token_to_card[token] = (number, expiry, cvv)

    def charge(self, amount: float, currency: str, card_token: str) -> dict:
        card_info = self._token_to_card.get(card_token)
        if not card_info:
            return {"success": False, "error": "Invalid card token"}

        number, expiry, cvv = card_info
        amount_cents = int(amount * 100)

        reference = self._gateway.make_payment(
            amount_cents=amount_cents,
            currency_code=currency.upper(),
            card_number=number,
            expiry=expiry,
            cvv=cvv,
        )

        return {
            "success": True,
            "transaction_id": reference,
            "amount": amount,
            "currency": currency,
        }

    def refund(self, transaction_id: str, amount: float) -> dict:
        amount_cents = int(amount * 100)
        success = self._gateway.reverse_payment(
            reference=transaction_id,
            amount_cents=amount_cents,
        )
        return {
            "success": success,
            "transaction_id": transaction_id,
            "refunded_amount": amount if success else 0,
        }

    def get_status(self, transaction_id: str) -> str:
        status_code = self._gateway.check_payment_status(transaction_id)
        return self.STATUS_MAP.get(status_code, "unknown")


# Usage
legacy_gateway = LegacyPaymentGateway()
adapter = LegacyPaymentAdapter(legacy_gateway)
adapter.register_card_token("tok_123", "4111111111111111", "12/25", "123")

result = adapter.charge(49.99, "USD", "tok_123")
print(result)

status = adapter.get_status(result["transaction_id"])
print(f"Status: {status}")
```

### Using `__getattr__` for Transparent Adaptation

```python
class TransparentAdapter:
    """Adapter that transparently delegates unhandled calls to the adaptee."""

    def __init__(self, adaptee, interface_map: dict[str, str] = None):
        self._adaptee = adaptee
        self._interface_map = interface_map or {}

    def __getattr__(self, name: str):
        mapped_name = self._interface_map.get(name, name)
        return getattr(self._adaptee, mapped_name)


# Example: Adapt a requests-like library to our HTTP client interface
class OldHttpClient:
    def do_get(self, url, headers=None):
        return {"status": 200, "body": f"GET {url}"}

    def do_post(self, url, payload=None, headers=None):
        return {"status": 201, "body": f"POST {url}"}

    def do_delete(self, url, headers=None):
        return {"status": 204, "body": ""}


# Map our expected method names to the old client's methods
adapted = TransparentAdapter(OldHttpClient(), {
    "get": "do_get",
    "post": "do_post",
    "delete": "do_delete",
})

print(adapted.get("https://api.example.com/users"))
print(adapted.post("https://api.example.com/users", payload={"name": "Alice"}))
```

### When to Use / When NOT to Use

**Use when:**
- Integrating a third-party library with an incompatible interface
- Working with legacy code that can't be modified
- You want to create a reusable class that cooperates with unrelated classes
- You need multiple adapters for different backends (payment gateways, cloud providers)

**Don't use when:**
- You can modify the adaptee directly
- The interfaces are already compatible
- A simple function wrapper suffices

### Common Mistakes
- Putting business logic in the adapter (it should only translate)
- Creating adapters for interfaces you control (just fix the interface)
- Not handling edge cases in the translation (error codes, null values)
- Making the adapter stateful when it doesn't need to be

---

## 7. Decorator Pattern

### Intent
Attach additional responsibilities to an object dynamically. Decorators provide a flexible
alternative to subclassing for extending functionality.

### Problem It Solves

You need to add behaviors to individual objects without affecting other objects of the same
class. Subclassing creates a combinatorial explosion when multiple optional behaviors exist.

### Distinction from Python Decorators (@decorator)

The **OOP Decorator Pattern** wraps an object to add behavior at runtime.
**Python's @decorator syntax** is a function/class transformation applied at definition time.

They're related but distinct:
- OOP Decorator: Runtime object wrapping with shared interface
- @decorator: Compile-time function/class modification

### UML-Style Structure

```
┌─────────────────┐
│   Component     │
│   (Interface)   │
└─────────────────┘
         ▲
    ┌────┴──────────────────┐
    │                       │
┌──────────────┐    ┌──────────────────┐
│  Concrete    │    │   Decorator      │
│  Component   │    │  (Abstract)      │
└──────────────┘    ├──────────────────┤
                    │- wrapped: Component│
                    └──────────────────┘
                             ▲
                        ┌────┴────┐
                   ┌─────────┐ ┌─────────┐
                   │DecorA   │ │DecorB   │
                   └─────────┘ └─────────┘
```

### Classic OOP Decorator

```python
from abc import ABC, abstractmethod
from typing import Protocol
import time


# --- Component Interface ---

class DataSource(Protocol):
    def write(self, data: str) -> None: ...
    def read(self) -> str: ...


# --- Concrete Component ---

class FileDataSource:
    """Base component - reads/writes data to a file."""

    def __init__(self, filename: str):
        self._filename = filename
        self._content = ""

    def write(self, data: str) -> None:
        self._content = data
        print(f"FileDataSource: Wrote {len(data)} chars to {self._filename}")

    def read(self) -> str:
        print(f"FileDataSource: Read from {self._filename}")
        return self._content


# --- Base Decorator ---

class DataSourceDecorator:
    """Base decorator - delegates everything to wrapped component."""

    def __init__(self, source: DataSource):
        self._wrapped = source

    def write(self, data: str) -> None:
        self._wrapped.write(data)

    def read(self) -> str:
        return self._wrapped.read()


# --- Concrete Decorators ---

class EncryptionDecorator(DataSourceDecorator):
    """Adds encryption/decryption to any data source."""

    def __init__(self, source: DataSource, key: int = 3):
        super().__init__(source)
        self._key = key

    def write(self, data: str) -> None:
        encrypted = self._encrypt(data)
        print(f"EncryptionDecorator: Encrypted data")
        super().write(encrypted)

    def read(self) -> str:
        data = super().read()
        decrypted = self._decrypt(data)
        print(f"EncryptionDecorator: Decrypted data")
        return decrypted

    def _encrypt(self, data: str) -> str:
        return "".join(chr(ord(c) + self._key) for c in data)

    def _decrypt(self, data: str) -> str:
        return "".join(chr(ord(c) - self._key) for c in data)


class CompressionDecorator(DataSourceDecorator):
    """Adds compression to any data source."""

    def write(self, data: str) -> None:
        compressed = self._compress(data)
        print(f"CompressionDecorator: Compressed {len(data)} -> {len(compressed)} chars")
        super().write(compressed)

    def read(self) -> str:
        data = super().read()
        decompressed = self._decompress(data)
        print(f"CompressionDecorator: Decompressed {len(data)} -> {len(decompressed)} chars")
        return decompressed

    def _compress(self, data: str) -> str:
        import zlib, base64
        compressed = zlib.compress(data.encode())
        return base64.b64encode(compressed).decode()

    def _decompress(self, data: str) -> str:
        import zlib, base64
        decompressed = zlib.decompress(base64.b64decode(data))
        return decompressed.decode()


class LoggingDecorator(DataSourceDecorator):
    """Adds logging to any data source operation."""

    def write(self, data: str) -> None:
        start = time.time()
        super().write(data)
        elapsed = time.time() - start
        print(f"LoggingDecorator: write took {elapsed:.4f}s")

    def read(self) -> str:
        start = time.time()
        result = super().read()
        elapsed = time.time() - start
        print(f"LoggingDecorator: read took {elapsed:.4f}s, returned {len(result)} chars")
        return result


# --- Stacking Decorators ---

# Plain file
source = FileDataSource("data.txt")

# Add encryption
source = EncryptionDecorator(source, key=5)

# Add compression on top of encryption
source = CompressionDecorator(source)

# Add logging on top of everything
source = LoggingDecorator(source)

# Write goes: Logging -> Compression -> Encryption -> File
source.write("Hello, this is sensitive data that needs protection!")

# Read goes: File -> Encryption -> Compression -> Logging
result = source.read()
print(f"Final result: {result}")
```

### Python Function Decorators as Pattern Implementation

```python
import functools
import time
import logging
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator that retries a function on failure."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def cache(ttl_seconds: float = 60.0):
    """Decorator that caches function results with TTL."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        _cache: dict[tuple, tuple[float, R]] = {}

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()

            if key in _cache:
                cached_time, cached_result = _cache[key]
                if now - cached_time < ttl_seconds:
                    print(f"Cache hit for {func.__name__}")
                    return cached_result

            result = func(*args, **kwargs)
            _cache[key] = (now, result)
            return result

        wrapper.cache_clear = lambda: _cache.clear()
        return wrapper
    return decorator


def validate_args(**validators: Callable):
    """Decorator that validates function arguments."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Validation failed for '{param_name}': {value}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Stacking Python decorators
@retry(max_attempts=3, delay=0.5)
@cache(ttl_seconds=300)
@validate_args(user_id=lambda x: isinstance(x, int) and x > 0)
def get_user_profile(user_id: int) -> dict:
    """Fetch user profile from external service."""
    print(f"Fetching profile for user {user_id}")
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}


profile = get_user_profile(42)
profile_cached = get_user_profile(42)  # Cache hit
```

### When to Use / When NOT to Use

**Use when:**
- You need to add responsibilities to objects dynamically
- Extension by subclassing is impractical (too many combinations)
- You want to stack behaviors in different configurations
- Behaviors should be addable/removable at runtime

**Don't use when:**
- The component interface is very wide (many methods to delegate)
- Order of decoration matters but isn't obvious to users
- A simple subclass or mixin suffices
- The behavior is fixed and won't change

### Common Mistakes
- Breaking the interface contract in a decorator
- Deep nesting that's hard to debug (stack traces become unreadable)
- Not using `functools.wraps` in Python function decorators
- Stateful decorators that have thread-safety issues

---

## 8. Composite Pattern

### Intent
Compose objects into tree structures to represent part-whole hierarchies. Composite lets
clients treat individual objects and compositions of objects uniformly.

### Problem It Solves

When you have a tree structure (file system, UI components, organization chart) and want
to treat leaves and containers identically through a uniform interface.

### UML-Style Structure

```
┌─────────────────┐
│    Component    │
│   (Interface)   │
├─────────────────┤
│+ operation()    │
└─────────────────┘
         ▲
    ┌────┴─────────────────┐
    │                      │
┌─────────┐       ┌──────────────┐
│  Leaf   │       │  Composite   │
├─────────┤       ├──────────────┤
│+operation│      │- children    │
└─────────┘       │+ add()       │
                  │+ remove()    │
                  │+ operation() │
                  └──────────────┘
```

### Full Python Implementation

```python
from abc import ABC, abstractmethod
from typing import Iterator


class FileSystemItem(ABC):
    """Component - common interface for files and directories."""

    def __init__(self, name: str):
        self._name = name
        self._parent: "Directory | None" = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        if self._parent is None:
            return self._name
        return f"{self._parent.path}/{self._name}"

    @abstractmethod
    def get_size(self) -> int:
        """Get total size in bytes."""
        ...

    @abstractmethod
    def display(self, indent: int = 0) -> str:
        """Display tree structure."""
        ...

    @abstractmethod
    def find(self, name: str) -> list["FileSystemItem"]:
        """Find items by name."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator["FileSystemItem"]:
        """Iterate over all items."""
        ...


class File(FileSystemItem):
    """Leaf - a file in the file system."""

    def __init__(self, name: str, size: int, content: str = ""):
        super().__init__(name)
        self._size = size
        self._content = content

    def get_size(self) -> int:
        return self._size

    def display(self, indent: int = 0) -> str:
        prefix = "  " * indent
        return f"{prefix}📄 {self._name} ({self._size} bytes)"

    def find(self, name: str) -> list[FileSystemItem]:
        if name.lower() in self._name.lower():
            return [self]
        return []

    def __iter__(self) -> Iterator[FileSystemItem]:
        yield self


class Directory(FileSystemItem):
    """Composite - a directory that contains files and other directories."""

    def __init__(self, name: str):
        super().__init__(name)
        self._children: list[FileSystemItem] = []

    def add(self, item: FileSystemItem) -> "Directory":
        item._parent = self
        self._children.append(item)
        return self

    def remove(self, item: FileSystemItem) -> None:
        item._parent = None
        self._children.remove(item)

    def get_size(self) -> int:
        return sum(child.get_size() for child in self._children)

    def display(self, indent: int = 0) -> str:
        prefix = "  " * indent
        lines = [f"{prefix}📁 {self._name}/ ({self.get_size()} bytes)"]
        for child in self._children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)

    def find(self, name: str) -> list[FileSystemItem]:
        results = []
        if name.lower() in self._name.lower():
            results.append(self)
        for child in self._children:
            results.extend(child.find(name))
        return results

    def __iter__(self) -> Iterator[FileSystemItem]:
        yield self
        for child in self._children:
            yield from child

    @property
    def children(self) -> list[FileSystemItem]:
        return self._children.copy()

    def count_files(self) -> int:
        count = 0
        for item in self:
            if isinstance(item, File):
                count += 1
        return count


# Build a file system tree
root = Directory("project")
src = Directory("src")
tests = Directory("tests")

src.add(File("main.py", 1200, "# Main entry point"))
src.add(File("utils.py", 800, "# Utility functions"))
src.add(File("config.py", 450, "# Configuration"))

models = Directory("models")
models.add(File("user.py", 600))
models.add(File("order.py", 900))
models.add(File("product.py", 750))
src.add(models)

tests.add(File("test_main.py", 500))
tests.add(File("test_utils.py", 400))
tests.add(File("test_models.py", 1100))

root.add(src)
root.add(tests)
root.add(File("README.md", 2000))
root.add(File("requirements.txt", 150))

# Uniform operations on the tree
print(root.display())
print(f"\nTotal size: {root.get_size()} bytes")
print(f"Total files: {root.count_files()}")
print(f"\nSearch 'test': {[item.name for item in root.find('test')]}")
```

### Real Example: Organization Hierarchy

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class OrganizationUnit(ABC):
    """Component for organization hierarchy."""

    @abstractmethod
    def get_total_salary(self) -> float: ...

    @abstractmethod
    def get_headcount(self) -> int: ...

    @abstractmethod
    def display(self, indent: int = 0) -> str: ...


@dataclass
class Employee(OrganizationUnit):
    """Leaf - individual employee."""
    name: str
    role: str
    salary: float

    def get_total_salary(self) -> float:
        return self.salary

    def get_headcount(self) -> int:
        return 1

    def display(self, indent: int = 0) -> str:
        prefix = "  " * indent
        return f"{prefix}👤 {self.name} ({self.role}) - ${self.salary:,.0f}"


@dataclass
class Department(OrganizationUnit):
    """Composite - department containing employees and sub-departments."""
    name: str
    head: str = ""
    _members: list[OrganizationUnit] = field(default_factory=list)

    def add(self, unit: OrganizationUnit) -> "Department":
        self._members.append(unit)
        return self

    def remove(self, unit: OrganizationUnit) -> None:
        self._members.remove(unit)

    def get_total_salary(self) -> float:
        return sum(member.get_total_salary() for member in self._members)

    def get_headcount(self) -> int:
        return sum(member.get_headcount() for member in self._members)

    def display(self, indent: int = 0) -> str:
        prefix = "  " * indent
        lines = [
            f"{prefix}🏢 {self.name} (Head: {self.head}, "
            f"HC: {self.get_headcount()}, Budget: ${self.get_total_salary():,.0f})"
        ]
        for member in self._members:
            lines.append(member.display(indent + 1))
        return "\n".join(lines)


# Build organization
company = Department("TechCorp", head="CEO Alice")

engineering = Department("Engineering", head="VP Bob")
engineering.add(Employee("Charlie", "Senior Engineer", 150000))
engineering.add(Employee("Diana", "Engineer", 120000))

backend = Department("Backend Team", head="Lead Eve")
backend.add(Employee("Frank", "Backend Dev", 130000))
backend.add(Employee("Grace", "Backend Dev", 125000))
engineering.add(backend)

frontend = Department("Frontend Team", head="Lead Heidi")
frontend.add(Employee("Ivan", "Frontend Dev", 125000))
frontend.add(Employee("Judy", "Frontend Dev", 120000))
engineering.add(frontend)

marketing = Department("Marketing", head="VP Karl")
marketing.add(Employee("Leo", "Marketing Manager", 110000))
marketing.add(Employee("Mallory", "Content Writer", 85000))

company.add(engineering)
company.add(marketing)

print(company.display())
print(f"\nCompany headcount: {company.get_headcount()}")
print(f"Total salary budget: ${company.get_total_salary():,.0f}")
```

### When to Use / When NOT to Use

**Use when:**
- You have a tree/hierarchical structure
- Clients should treat leaves and composites uniformly
- You want recursive operations over the tree (size, count, search)

**Don't use when:**
- The structure is flat (no nesting)
- Leaves and composites have very different interfaces
- The hierarchy is fixed and simple (a list suffices)

### Common Mistakes
- Making the component interface too specific to either leaf or composite
- Not handling the case where a leaf is asked to add children
- Circular references (child points to parent who contains child)
- Performance issues with deep recursion on large trees

---

## 9. Facade Pattern

### Intent
Provide a unified interface to a set of interfaces in a subsystem. Facade defines a
higher-level interface that makes the subsystem easier to use.

### Problem It Solves

Complex subsystems with many interdependent classes are difficult to use correctly. A
facade provides a simplified interface for common use cases while still allowing direct
access to the subsystem for advanced needs.

### UML-Style Structure

```
┌────────────┐        ┌──────────────────────────────────────┐
│   Client   │───────▶│           Facade                     │
└────────────┘        ├──────────────────────────────────────┤
                      │+ simple_operation_a()                │
                      │+ simple_operation_b()                │
                      └──────────┬───────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │SubsystemA│ │SubsystemB│ │SubsystemC│
              └──────────┘ └──────────┘ └──────────┘
```

### Real Example: E-Commerce Checkout Facade

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# --- Complex subsystem classes ---

class InventoryService:
    """Manages product stock levels."""

    def __init__(self):
        self._stock: dict[str, int] = {
            "PROD-001": 50,
            "PROD-002": 100,
            "PROD-003": 0,
        }

    def check_availability(self, product_id: str, quantity: int) -> bool:
        available = self._stock.get(product_id, 0)
        return available >= quantity

    def reserve(self, product_id: str, quantity: int) -> str:
        """Reserve stock and return reservation ID."""
        if not self.check_availability(product_id, quantity):
            raise ValueError(f"Insufficient stock for {product_id}")
        self._stock[product_id] -= quantity
        reservation_id = f"RES-{uuid.uuid4().hex[:8]}"
        print(f"  Inventory: Reserved {quantity}x {product_id} ({reservation_id})")
        return reservation_id

    def release(self, product_id: str, quantity: int) -> None:
        """Release previously reserved stock."""
        self._stock[product_id] = self._stock.get(product_id, 0) + quantity
        print(f"  Inventory: Released {quantity}x {product_id}")


class PricingService:
    """Calculates prices, discounts, and taxes."""

    def __init__(self):
        self._prices: dict[str, float] = {
            "PROD-001": 29.99,
            "PROD-002": 49.99,
            "PROD-003": 99.99,
        }
        self._tax_rate = 0.08

    def get_price(self, product_id: str) -> float:
        return self._prices.get(product_id, 0.0)

    def calculate_subtotal(self, items: list[tuple[str, int]]) -> float:
        return sum(self.get_price(pid) * qty for pid, qty in items)

    def apply_discount(self, subtotal: float, coupon_code: Optional[str]) -> tuple[float, float]:
        """Returns (discounted_total, discount_amount)."""
        discounts = {"SAVE10": 0.10, "SAVE20": 0.20, "VIP50": 0.50}
        discount_rate = discounts.get(coupon_code, 0.0)
        discount_amount = subtotal * discount_rate
        return subtotal - discount_amount, discount_amount

    def calculate_tax(self, amount: float) -> float:
        return round(amount * self._tax_rate, 2)


class PaymentService:
    """Processes payments."""

    def authorize(self, amount: float, payment_method: dict) -> str:
        """Authorize payment and return authorization ID."""
        print(f"  Payment: Authorizing ${amount:.2f} via {payment_method['type']}")
        return f"AUTH-{uuid.uuid4().hex[:8]}"

    def capture(self, authorization_id: str) -> str:
        """Capture authorized payment."""
        print(f"  Payment: Captured {authorization_id}")
        return f"TXN-{uuid.uuid4().hex[:8]}"

    def void(self, authorization_id: str) -> None:
        """Void an authorization."""
        print(f"  Payment: Voided {authorization_id}")


class ShippingService:
    """Manages shipping calculations and label generation."""

    def calculate_shipping(self, address: dict, items: list[tuple[str, int]]) -> float:
        base_cost = 5.99
        item_cost = sum(qty * 0.50 for _, qty in items)
        return base_cost + item_cost

    def create_shipment(self, order_id: str, address: dict) -> str:
        """Create shipping label and return tracking number."""
        tracking = f"TRACK-{uuid.uuid4().hex[:8]}"
        print(f"  Shipping: Created shipment {tracking} for {order_id}")
        return tracking


class NotificationService:
    """Sends notifications to customers."""

    def send_order_confirmation(self, email: str, order_id: str, total: float) -> None:
        print(f"  Notification: Order confirmation sent to {email} (Order: {order_id})")

    def send_shipping_notification(self, email: str, tracking: str) -> None:
        print(f"  Notification: Shipping notification sent to {email} (Tracking: {tracking})")


class FraudDetectionService:
    """Checks orders for potential fraud."""

    def check(self, amount: float, payment_method: dict, address: dict) -> bool:
        """Returns True if order passes fraud check."""
        if amount > 10000:
            print("  Fraud: FLAGGED - amount exceeds threshold")
            return False
        print("  Fraud: Passed")
        return True


# --- Facade ---

@dataclass
class OrderResult:
    success: bool
    order_id: str = ""
    total: float = 0.0
    tracking_number: str = ""
    error: str = ""


class CheckoutFacade:
    """
    Facade that simplifies the complex checkout process.
    Coordinates inventory, pricing, payment, shipping, notifications, and fraud detection.
    """

    def __init__(self):
        self._inventory = InventoryService()
        self._pricing = PricingService()
        self._payment = PaymentService()
        self._shipping = ShippingService()
        self._notifications = NotificationService()
        self._fraud = FraudDetectionService()

    def checkout(
        self,
        items: list[tuple[str, int]],
        payment_method: dict,
        shipping_address: dict,
        customer_email: str,
        coupon_code: Optional[str] = None,
    ) -> OrderResult:
        """
        Complete checkout process in one call.
        Handles: inventory check, pricing, fraud, payment, shipping, notification.
        """
        order_id = f"ORD-{uuid.uuid4().hex[:8]}"
        print(f"Starting checkout: {order_id}")
        reservations: list[tuple[str, int, str]] = []

        try:
            # Step 1: Check and reserve inventory
            for product_id, quantity in items:
                if not self._inventory.check_availability(product_id, quantity):
                    return OrderResult(
                        success=False,
                        error=f"Product {product_id} out of stock",
                    )
                res_id = self._inventory.reserve(product_id, quantity)
                reservations.append((product_id, quantity, res_id))

            # Step 2: Calculate pricing
            subtotal = self._pricing.calculate_subtotal(items)
            discounted, discount_amt = self._pricing.apply_discount(subtotal, coupon_code)
            tax = self._pricing.calculate_tax(discounted)
            shipping_cost = self._shipping.calculate_shipping(shipping_address, items)
            total = discounted + tax + shipping_cost
            print(f"  Pricing: Subtotal=${subtotal:.2f}, Discount=${discount_amt:.2f}, "
                  f"Tax=${tax:.2f}, Shipping=${shipping_cost:.2f}, Total=${total:.2f}")

            # Step 3: Fraud check
            if not self._fraud.check(total, payment_method, shipping_address):
                self._rollback_reservations(reservations)
                return OrderResult(success=False, error="Order flagged for fraud review")

            # Step 4: Process payment
            auth_id = self._payment.authorize(total, payment_method)
            txn_id = self._payment.capture(auth_id)

            # Step 5: Create shipment
            tracking = self._shipping.create_shipment(order_id, shipping_address)

            # Step 6: Send notifications
            self._notifications.send_order_confirmation(customer_email, order_id, total)

            print(f"Checkout complete: {order_id}")
            return OrderResult(
                success=True,
                order_id=order_id,
                total=total,
                tracking_number=tracking,
            )

        except Exception as e:
            self._rollback_reservations(reservations)
            return OrderResult(success=False, error=str(e))

    def _rollback_reservations(self, reservations: list[tuple[str, int, str]]) -> None:
        """Rollback inventory reservations on failure."""
        for product_id, quantity, _ in reservations:
            self._inventory.release(product_id, quantity)


# Usage - complex process simplified to one call
facade = CheckoutFacade()

result = facade.checkout(
    items=[("PROD-001", 2), ("PROD-002", 1)],
    payment_method={"type": "credit_card", "token": "tok_abc123"},
    shipping_address={"street": "123 Main St", "city": "Springfield", "zip": "62701"},
    customer_email="customer@example.com",
    coupon_code="SAVE10",
)

print(f"\nResult: {result}")
```

### When Facade Becomes a God Class

Warning signs:
- Facade has 20+ public methods
- Facade has complex internal state
- Facade makes decisions that belong in the subsystem
- Every new feature requires modifying the facade

**Solution**: Split into multiple focused facades (CheckoutFacade, ReturnsFacade, AccountFacade).

### When to Use / When NOT to Use

**Use when:**
- A subsystem has many interdependent classes
- You want to provide a simple interface for common operations
- You want to layer subsystems (each layer has a facade)
- You want to decouple client code from subsystem implementation

**Don't use when:**
- The subsystem is already simple
- Clients need fine-grained control over subsystem interactions
- The facade would just delegate to a single class

### Common Mistakes
- Facade doing too much (becoming a god class)
- Not allowing direct subsystem access when needed
- Putting business logic in the facade instead of subsystem classes
- Making the facade a singleton (usually unnecessary)

---

## 10. Proxy Pattern

### Intent
Provide a surrogate or placeholder for another object to control access to it.

### Problem It Solves

Direct access to an object may be undesirable due to: cost of creation (virtual proxy),
access control requirements (protection proxy), remote location (remote proxy), or
caching needs (caching proxy).

### UML-Style Structure

```
┌────────────┐       ┌──────────────┐
│   Client   │──────▶│   Subject    │
└────────────┘       │ (Interface)  │
                     └──────────────┘
                            ▲
                       ┌────┴────┐
                       │         │
              ┌─────────────┐  ┌─────────────┐
              │ RealSubject │  │    Proxy    │
              └─────────────┘  ├─────────────┤
                               │-real_subject │
                               └─────────────┘
```

### Full Python Implementation

```python
from abc import ABC, abstractmethod
from typing import Any, Optional
import time
import threading


# --- Subject Interface ---

class Database(ABC):
    @abstractmethod
    def query(self, sql: str) -> list[dict]: ...

    @abstractmethod
    def execute(self, sql: str) -> int: ...

    @abstractmethod
    def close(self) -> None: ...


# --- Real Subject ---

class PostgresDatabase(Database):
    """Real database connection - expensive to create."""

    def __init__(self, host: str, port: int, dbname: str, user: str, password: str):
        self._host = host
        self._port = port
        self._dbname = dbname
        self._user = user
        # Simulate expensive connection
        print(f"  [PostgresDB] Connecting to {host}:{port}/{dbname}...")
        time.sleep(0.1)  # Simulate connection time
        self._connected = True
        print(f"  [PostgresDB] Connected!")

    def query(self, sql: str) -> list[dict]:
        if not self._connected:
            raise RuntimeError("Not connected")
        print(f"  [PostgresDB] Executing query: {sql}")
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def execute(self, sql: str) -> int:
        if not self._connected:
            raise RuntimeError("Not connected")
        print(f"  [PostgresDB] Executing: {sql}")
        return 1

    def close(self) -> None:
        self._connected = False
        print("  [PostgresDB] Connection closed")


# --- Virtual Proxy (Lazy Loading) ---

class LazyDatabaseProxy(Database):
    """Defers connection creation until actually needed."""

    def __init__(self, host: str, port: int, dbname: str, user: str, password: str):
        self._config = {
            "host": host, "port": port, "dbname": dbname,
            "user": user, "password": password,
        }
        self._real_db: Optional[PostgresDatabase] = None
        self._lock = threading.Lock()

    def _get_db(self) -> PostgresDatabase:
        if self._real_db is None:
            with self._lock:
                if self._real_db is None:
                    print("  [LazyProxy] First access - creating connection...")
                    self._real_db = PostgresDatabase(**self._config)
        return self._real_db

    def query(self, sql: str) -> list[dict]:
        return self._get_db().query(sql)

    def execute(self, sql: str) -> int:
        return self._get_db().execute(sql)

    def close(self) -> None:
        if self._real_db:
            self._real_db.close()
            self._real_db = None


# --- Protection Proxy (Access Control) ---

class AccessControlDatabaseProxy(Database):
    """Controls access based on user role."""

    WRITE_OPERATIONS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"}

    def __init__(self, real_db: Database, user_role: str):
        self._real_db = real_db
        self._user_role = user_role

    def _is_write_operation(self, sql: str) -> bool:
        first_word = sql.strip().split()[0].upper()
        return first_word in self.WRITE_OPERATIONS

    def _check_permission(self, sql: str) -> None:
        if self._is_write_operation(sql) and self._user_role == "readonly":
            raise PermissionError(
                f"User role '{self._user_role}' cannot execute write operations"
            )

    def query(self, sql: str) -> list[dict]:
        self._check_permission(sql)
        print(f"  [AccessProxy] Allowed query for role '{self._user_role}'")
        return self._real_db.query(sql)

    def execute(self, sql: str) -> int:
        self._check_permission(sql)
        print(f"  [AccessProxy] Allowed execute for role '{self._user_role}'")
        return self._real_db.execute(sql)

    def close(self) -> None:
        self._real_db.close()


# --- Caching Proxy ---

class CachingDatabaseProxy(Database):
    """Caches query results with TTL."""

    def __init__(self, real_db: Database, ttl_seconds: float = 60.0):
        self._real_db = real_db
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._lock = threading.Lock()

    def query(self, sql: str) -> list[dict]:
        now = time.time()

        with self._lock:
            if sql in self._cache:
                cached_time, cached_result = self._cache[sql]
                if now - cached_time < self._ttl:
                    print(f"  [CacheProxy] Cache HIT for: {sql[:50]}...")
                    return cached_result
                else:
                    del self._cache[sql]

        print(f"  [CacheProxy] Cache MISS for: {sql[:50]}...")
        result = self._real_db.query(sql)

        with self._lock:
            self._cache[sql] = (now, result)

        return result

    def execute(self, sql: str) -> int:
        with self._lock:
            self._cache.clear()
            print("  [CacheProxy] Cache cleared (write operation)")
        return self._real_db.execute(sql)

    def close(self) -> None:
        self._real_db.close()

    def invalidate(self) -> None:
        with self._lock:
            self._cache.clear()


# --- Logging Proxy ---

class LoggingDatabaseProxy(Database):
    """Logs all database operations with timing."""

    def __init__(self, real_db: Database):
        self._real_db = real_db
        self._query_log: list[dict] = []

    def query(self, sql: str) -> list[dict]:
        start = time.time()
        result = self._real_db.query(sql)
        elapsed = time.time() - start
        self._query_log.append({
            "type": "query", "sql": sql,
            "elapsed_ms": elapsed * 1000, "rows": len(result),
        })
        print(f"  [LogProxy] Query took {elapsed*1000:.2f}ms, returned {len(result)} rows")
        return result

    def execute(self, sql: str) -> int:
        start = time.time()
        affected = self._real_db.execute(sql)
        elapsed = time.time() - start
        self._query_log.append({
            "type": "execute", "sql": sql,
            "elapsed_ms": elapsed * 1000, "affected": affected,
        })
        print(f"  [LogProxy] Execute took {elapsed*1000:.2f}ms, affected {affected} rows")
        return affected

    def close(self) -> None:
        self._real_db.close()

    def get_slow_queries(self, threshold_ms: float = 100.0) -> list[dict]:
        return [q for q in self._query_log if q["elapsed_ms"] > threshold_ms]


# --- Stacking Proxies ---

# Lazy connection -> Caching -> Access Control -> Logging
db = LazyDatabaseProxy(
    host="localhost", port=5432, dbname="myapp", user="app", password="secret"
)
db = CachingDatabaseProxy(db, ttl_seconds=300)
db = AccessControlDatabaseProxy(db, user_role="readonly")
db = LoggingDatabaseProxy(db)

# First query - creates connection, misses cache
print("=== First Query ===")
result = db.query("SELECT * FROM users WHERE active = true")

# Second query - cache hit
print("\n=== Second Query (same) ===")
result = db.query("SELECT * FROM users WHERE active = true")

# Write attempt - blocked by access control
print("\n=== Write Attempt ===")
try:
    db.execute("DELETE FROM users WHERE id = 1")
except PermissionError as e:
    print(f"  Blocked: {e}")
```

### Using `__getattr__` for Generic Proxy

```python
class GenericProxy:
    """Generic proxy using __getattr__ for transparent delegation."""

    def __init__(self, target: Any):
        self._target = target

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._target, name)
        if callable(attr):
            def proxy_method(*args, **kwargs):
                print(f"  [Proxy] Calling {name}({args}, {kwargs})")
                result = attr(*args, **kwargs)
                print(f"  [Proxy] {name} returned: {result}")
                return result
            return proxy_method
        return attr
```

### When to Use / When NOT to Use

**Use when:**
- Object creation is expensive and may not always be needed (virtual/lazy)
- You need to control access based on permissions (protection)
- You want to add caching without modifying the real object
- You need logging/monitoring without coupling to the real object
- The real object is remote (remote proxy, RPC)

**Don't use when:**
- Direct access is fine and there's no cross-cutting concern
- The overhead of the proxy is significant relative to the operation
- A simple function wrapper or decorator suffices

### Common Mistakes
- Proxy that doesn't fully implement the subject interface
- Not handling the case where the real subject becomes unavailable
- Cache invalidation bugs in caching proxy
- Thread-safety issues in lazy initialization

---

## Behavioral Patterns

Behavioral patterns are concerned with algorithms and the assignment of responsibilities
between objects. They describe patterns of communication between objects.

---

## 11. Observer Pattern

### Intent
Define a one-to-many dependency between objects so that when one object changes state,
all its dependents are notified and updated automatically.

### Problem It Solves

When multiple objects need to react to changes in another object, tight coupling (direct
method calls) makes the system rigid. Observer decouples the subject from its observers.

### UML-Style Structure

```
┌─────────────────┐        ┌──────────────────┐
│    Subject      │───────▶│    Observer      │
├─────────────────┤        │   (Interface)    │
│- observers      │        ├──────────────────┤
│+ attach()       │        │+ update()        │
│+ detach()       │        └──────────────────┘
│+ notify()       │                 ▲
└─────────────────┘            ┌────┴────┐
                               │         │
                         ┌──────────┐ ┌──────────┐
                         │ObserverA │ │ObserverB │
                         └──────────┘ └──────────┘
```

### Full Python Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Protocol
from enum import Enum
import weakref


# --- Observer Protocol ---

class Observer(Protocol):
    def update(self, event: str, data: Any) -> None: ...


# --- Subject Base ---

class Subject:
    """Base subject with observer management."""

    def __init__(self):
        self._observers: dict[str, list[weakref.ref]] = {}

    def attach(self, event: str, observer: Observer) -> None:
        """Attach observer for a specific event."""
        if event not in self._observers:
            self._observers[event] = []
        self._observers[event].append(weakref.ref(observer))

    def detach(self, event: str, observer: Observer) -> None:
        """Detach observer from a specific event."""
        if event in self._observers:
            self._observers[event] = [
                ref for ref in self._observers[event]
                if ref() is not None and ref() is not observer
            ]

    def notify(self, event: str, data: Any = None) -> None:
        """Notify all observers of an event."""
        if event not in self._observers:
            return

        dead_refs = []
        for ref in self._observers[event]:
            observer = ref()
            if observer is not None:
                observer.update(event, data)
            else:
                dead_refs.append(ref)

        # Clean up dead references
        for ref in dead_refs:
            self._observers[event].remove(ref)


# --- Real Example: Stock Price Notification System ---

@dataclass
class StockPrice:
    symbol: str
    price: float
    volume: int
    timestamp: datetime = field(default_factory=datetime.now)


class StockExchange(Subject):
    """Subject - publishes stock price changes."""

    def __init__(self):
        super().__init__()
        self._prices: dict[str, StockPrice] = {}

    def update_price(self, symbol: str, price: float, volume: int) -> None:
        old_price = self._prices.get(symbol)
        new_price = StockPrice(symbol=symbol, price=price, volume=volume)
        self._prices[symbol] = new_price

        # Determine event type
        if old_price is None:
            self.notify("new_listing", new_price)
        elif price > old_price.price:
            self.notify("price_up", {"old": old_price, "new": new_price})
            self.notify(f"price_change:{symbol}", {"old": old_price, "new": new_price})
        elif price < old_price.price:
            self.notify("price_down", {"old": old_price, "new": new_price})
            self.notify(f"price_change:{symbol}", {"old": old_price, "new": new_price})

        # Check for significant moves (>5%)
        if old_price and abs(price - old_price.price) / old_price.price > 0.05:
            self.notify("significant_move", {"old": old_price, "new": new_price})

    def get_price(self, symbol: str) -> Optional[StockPrice]:
        return self._prices.get(symbol)


# --- Concrete Observers ---

class PriceAlertObserver:
    """Observer that triggers alerts on price thresholds."""

    def __init__(self, name: str):
        self.name = name
        self._alerts: list[dict] = []
        self._thresholds: dict[str, tuple[float, float]] = {}

    def set_threshold(self, symbol: str, low: float, high: float) -> None:
        self._thresholds[symbol] = (low, high)

    def update(self, event: str, data: Any) -> None:
        if not isinstance(data, dict) or "new" not in data:
            return

        new_price: StockPrice = data["new"]
        symbol = new_price.symbol

        if symbol in self._thresholds:
            low, high = self._thresholds[symbol]
            if new_price.price <= low:
                alert = f"⚠️ {symbol} dropped below ${low:.2f} (now ${new_price.price:.2f})"
                self._alerts.append({"alert": alert, "time": datetime.now()})
                print(f"  [{self.name}] {alert}")
            elif new_price.price >= high:
                alert = f"🚀 {symbol} above ${high:.2f} (now ${new_price.price:.2f})"
                self._alerts.append({"alert": alert, "time": datetime.now()})
                print(f"  [{self.name}] {alert}")


class PortfolioTracker:
    """Observer that tracks portfolio value changes."""

    def __init__(self, name: str, holdings: dict[str, int]):
        self.name = name
        self._holdings = holdings
        self._portfolio_value = 0.0

    def update(self, event: str, data: Any) -> None:
        if not isinstance(data, dict) or "new" not in data:
            return

        new_price: StockPrice = data["new"]
        old_price: StockPrice = data.get("old")

        if new_price.symbol in self._holdings:
            shares = self._holdings[new_price.symbol]
            if old_price:
                change = (new_price.price - old_price.price) * shares
                direction = "📈" if change > 0 else "📉"
                print(f"  [{self.name}] {direction} {new_price.symbol}: "
                      f"Portfolio impact: ${change:+.2f}")


class TradingBot:
    """Observer that executes trades based on signals."""

    def __init__(self, name: str, strategy: str = "momentum"):
        self.name = name
        self._strategy = strategy
        self._trades: list[dict] = []

    def update(self, event: str, data: Any) -> None:
        if event == "significant_move" and isinstance(data, dict):
            old_price: StockPrice = data["old"]
            new_price: StockPrice = data["new"]
            change_pct = (new_price.price - old_price.price) / old_price.price

            if self._strategy == "momentum":
                action = "BUY" if change_pct > 0 else "SELL"
            else:
                action = "SELL" if change_pct > 0 else "BUY"

            trade = {
                "action": action,
                "symbol": new_price.symbol,
                "price": new_price.price,
                "reason": f"{change_pct*100:.1f}% move",
            }
            self._trades.append(trade)
            print(f"  [{self.name}] 🤖 {action} {new_price.symbol} "
                  f"@ ${new_price.price:.2f} ({change_pct*100:+.1f}%)")


# Usage
exchange = StockExchange()

# Create observers
alerter = PriceAlertObserver("AlertSystem")
alerter.set_threshold("AAPL", low=150.0, high=200.0)
alerter.set_threshold("TSLA", low=200.0, high=300.0)

portfolio = PortfolioTracker("MyPortfolio", {"AAPL": 100, "TSLA": 50, "GOOGL": 25})
bot = TradingBot("MomentumBot", strategy="momentum")

# Subscribe to events
exchange.attach("price_up", alerter)
exchange.attach("price_down", alerter)
exchange.attach("price_up", portfolio)
exchange.attach("price_down", portfolio)
exchange.attach("significant_move", bot)

# Simulate price changes
print("=== Market Opens ===")
exchange.update_price("AAPL", 175.00, 1000000)
exchange.update_price("TSLA", 250.00, 2000000)

print("\n=== Price Updates ===")
exchange.update_price("AAPL", 180.50, 1500000)
exchange.update_price("TSLA", 210.00, 3000000)  # Significant drop if previous was 250
exchange.update_price("AAPL", 205.00, 2000000)  # Above threshold + significant move
```

### Event Bus Variation

```python
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """Centralized event bus - decouples publishers from subscribers entirely."""

    _instance = None

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._async_handlers: dict[str, list[Callable]] = defaultdict(list)

    @classmethod
    def get(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event: str, handler: Callable) -> Callable:
        """Subscribe to an event. Can be used as decorator."""
        self._handlers[event].append(handler)
        return handler

    def unsubscribe(self, event: str, handler: Callable) -> None:
        self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    def publish(self, event: str, **kwargs) -> None:
        """Publish event to all subscribers."""
        for handler in self._handlers.get(event, []):
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"Handler error for '{event}': {e}")

    def on(self, event: str) -> Callable:
        """Decorator for subscribing to events."""
        def decorator(func: Callable) -> Callable:
            self.subscribe(event, func)
            return func
        return decorator


# Usage with decorator syntax
bus = EventBus.get()


@bus.on("user.registered")
def send_welcome_email(user_id: str, email: str, **kwargs):
    print(f"Sending welcome email to {email}")


@bus.on("user.registered")
def create_default_settings(user_id: str, **kwargs):
    print(f"Creating default settings for user {user_id}")


@bus.on("user.registered")
def notify_admin(user_id: str, email: str, **kwargs):
    print(f"Admin notification: New user {email}")


# Publishing - publishers don't know about subscribers
bus.publish("user.registered", user_id="usr_123", email="new@example.com")
```

### When to Use / When NOT to Use

**Use when:**
- Changes to one object require updating others, and you don't know how many
- An object should notify other objects without knowing who they are
- You need loose coupling between interacting objects
- You're building an event-driven architecture

**Don't use when:**
- There's only one observer (direct callback is simpler)
- Notification order matters (observer pattern doesn't guarantee order)
- You need synchronous confirmation from observers
- The observer chain could create circular notifications

### Common Mistakes
- Memory leaks from forgotten observer references (use weak references)
- Infinite notification loops (observer modifies subject which notifies again)
- Not handling exceptions in individual observers (one failure stops all)
- Too many fine-grained events (notification storm)

---

## 12. Strategy Pattern

### Intent
Define a family of algorithms, encapsulate each one, and make them interchangeable.
Strategy lets the algorithm vary independently from clients that use it.

### Problem It Solves

When you have multiple ways to perform an operation (sorting, pricing, validation) and
need to switch between them at runtime without massive if/elif chains.

### UML-Style Structure

```
┌──────────────┐       ┌───────────────────┐
│   Context    │──────▶│    Strategy       │
├──────────────┤       │   (Interface)     │
│- strategy    │       ├───────────────────┤
│+ execute()   │       │+ execute()        │
└──────────────┘       └───────────────────┘
                                ▲
                     ┌──────────┼──────────┐
                     │          │          │
               ┌──────────┐┌──────────┐┌──────────┐
               │StrategyA ││StrategyB ││StrategyC │
               └──────────┘└──────────┘└──────────┘
```

### Full Python Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Callable
from datetime import datetime, timedelta


# --- Strategy Interface ---

class PricingStrategy(Protocol):
    """Strategy protocol for pricing calculation."""

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float: ...

    @property
    def name(self) -> str: ...


# --- Concrete Strategies ---

class RegularPricing:
    """No discounts - full price."""

    @property
    def name(self) -> str:
        return "Regular"

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float:
        return base_price * quantity


class BulkPricing:
    """Tiered discounts based on quantity."""

    TIERS = [
        (100, 0.20),  # 100+ items: 20% off
        (50, 0.15),   # 50+ items: 15% off
        (20, 0.10),   # 20+ items: 10% off
        (10, 0.05),   # 10+ items: 5% off
    ]

    @property
    def name(self) -> str:
        return "Bulk"

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float:
        discount = 0.0
        for threshold, disc in self.TIERS:
            if quantity >= threshold:
                discount = disc
                break

        total = base_price * quantity
        return total * (1 - discount)


class LoyaltyPricing:
    """Discounts based on customer loyalty tier."""

    TIER_DISCOUNTS = {
        "bronze": 0.05,
        "silver": 0.10,
        "gold": 0.15,
        "platinum": 0.25,
    }

    @property
    def name(self) -> str:
        return "Loyalty"

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float:
        discount = self.TIER_DISCOUNTS.get(customer.loyalty_tier, 0.0)
        total = base_price * quantity
        return total * (1 - discount)


class SeasonalPricing:
    """Dynamic pricing based on demand season."""

    SEASON_MULTIPLIERS = {
        "peak": 1.5,
        "high": 1.25,
        "normal": 1.0,
        "low": 0.75,
        "clearance": 0.5,
    }

    def __init__(self, season: str = "normal"):
        self._season = season

    @property
    def name(self) -> str:
        return f"Seasonal ({self._season})"

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float:
        multiplier = self.SEASON_MULTIPLIERS.get(self._season, 1.0)
        return base_price * quantity * multiplier


class CompositePricing:
    """Combines multiple strategies (best price for customer)."""

    def __init__(self, strategies: list[PricingStrategy]):
        self._strategies = strategies

    @property
    def name(self) -> str:
        return "Best Available"

    def calculate_price(self, base_price: float, customer: "Customer",
                        quantity: int) -> float:
        prices = [
            s.calculate_price(base_price, customer, quantity)
            for s in self._strategies
        ]
        return min(prices)


# --- Context ---

@dataclass
class Customer:
    id: str
    name: str
    loyalty_tier: str = "bronze"
    member_since: datetime = None


class PricingEngine:
    """Context that uses pricing strategies."""

    def __init__(self, default_strategy: PricingStrategy = None):
        self._strategy = default_strategy or RegularPricing()

    @property
    def strategy(self) -> PricingStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: PricingStrategy) -> None:
        self._strategy = strategy

    def calculate(self, base_price: float, customer: Customer,
                  quantity: int) -> dict:
        total = self._strategy.calculate_price(base_price, customer, quantity)
        regular_total = base_price * quantity
        savings = regular_total - total

        return {
            "strategy": self._strategy.name,
            "base_price": base_price,
            "quantity": quantity,
            "subtotal": regular_total,
            "total": round(total, 2),
            "savings": round(savings, 2),
            "discount_pct": round((savings / regular_total) * 100, 1) if regular_total > 0 else 0,
        }


# --- Pythonic: Functions as Strategies ---

def make_percentage_discount(pct: float) -> Callable:
    """Factory for percentage discount strategies using closures."""
    def strategy(base_price: float, customer: "Customer", quantity: int) -> float:
        return base_price * quantity * (1 - pct / 100)
    strategy.name = f"{pct}% Off"
    return strategy


def make_fixed_discount(amount: float) -> Callable:
    """Factory for fixed amount discount."""
    def strategy(base_price: float, customer: "Customer", quantity: int) -> float:
        total = base_price * quantity
        return max(0, total - amount)
    strategy.name = f"${amount} Off"
    return strategy


# Usage
customer = Customer(id="cust_1", name="Alice", loyalty_tier="gold")

engine = PricingEngine()

# Try different strategies
strategies = [
    RegularPricing(),
    BulkPricing(),
    LoyaltyPricing(),
    SeasonalPricing("low"),
    CompositePricing([BulkPricing(), LoyaltyPricing(), SeasonalPricing("low")]),
]

print(f"Customer: {customer.name} (Tier: {customer.loyalty_tier})")
print(f"Product: $25.00 x 30 units\n")

for strategy in strategies:
    engine.strategy = strategy
    result = engine.calculate(25.00, customer, 30)
    print(f"  {result['strategy']:20s}: ${result['total']:8.2f} "
          f"(save ${result['savings']:.2f}, {result['discount_pct']}% off)")
```

### Strategy vs if/else Chains

```python
# BAD: if/elif chain - violates OCP, hard to extend
def calculate_shipping_bad(weight: float, method: str, distance: float) -> float:
    if method == "standard":
        return weight * 0.5 + distance * 0.01
    elif method == "express":
        return weight * 1.0 + distance * 0.03 + 5.00
    elif method == "overnight":
        return weight * 2.0 + distance * 0.05 + 15.00
    elif method == "drone":
        return weight * 3.0 + 25.00
    else:
        raise ValueError(f"Unknown method: {method}")


# GOOD: Strategy pattern - open for extension
class ShippingStrategy(Protocol):
    def calculate(self, weight: float, distance: float) -> float: ...

class StandardShipping:
    def calculate(self, weight: float, distance: float) -> float:
        return weight * 0.5 + distance * 0.01

class ExpressShipping:
    def calculate(self, weight: float, distance: float) -> float:
        return weight * 1.0 + distance * 0.03 + 5.00

class OvernightShipping:
    def calculate(self, weight: float, distance: float) -> float:
        return weight * 2.0 + distance * 0.05 + 15.00

# Adding new strategy requires ZERO changes to existing code
class DroneShipping:
    def calculate(self, weight: float, distance: float) -> float:
        if weight > 5.0:
            raise ValueError("Drone can't carry more than 5kg")
        return weight * 3.0 + 25.00
```

### When to Use / When NOT to Use

**Use when:**
- Multiple algorithms exist for a specific task
- Algorithms can be swapped at runtime
- You want to eliminate conditional statements for selecting behavior
- Different variants of an algorithm are needed

**Don't use when:**
- Only 2-3 fixed algorithms that will never change (if/else is fine)
- The algorithm doesn't vary (premature abstraction)
- Clients don't need to know about different strategies

### Common Mistakes
- Over-engineering: creating a strategy for two simple cases
- Not defining a clear interface (strategies with different signatures)
- Context class knowing too much about strategy internals
- Making strategies stateful when they should be stateless

---

## 13. State Pattern

### Intent
Allow an object to alter its behavior when its internal state changes. The object will
appear to change its class.

### Problem It Solves

When an object's behavior depends on its state and must change at runtime, nested
conditionals (if state == X, elif state == Y) become unmanageable. State pattern
encapsulates state-specific behavior in separate classes.

### UML-Style Structure

```
┌──────────────────┐       ┌──────────────────┐
│    Context       │──────▶│     State        │
├──────────────────┤       │   (Interface)    │
│- state: State    │       ├──────────────────┤
│+ request()       │       │+ handle()        │
│+ transition_to() │       └──────────────────┘
└──────────────────┘                ▲
                            ┌───────┼───────┐
                            │       │       │
                     ┌──────────┐┌──────┐┌──────┐
                     │ StateA   ││StateB││StateC│
                     └──────────┘└──────┘└──────┘
```

### Full Python Implementation: Order State Machine

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderEvent(Enum):
    PLACE = "place"
    PAY = "pay"
    SHIP = "ship"
    DELIVER = "deliver"
    CANCEL = "cancel"
    RETURN = "return"
    REFUND = "refund"


class OrderState(ABC):
    """Abstract state for order."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    def place(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "place")

    def pay(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "pay")

    def ship(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "ship")

    def deliver(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "deliver")

    def cancel(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "cancel")

    def return_order(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "return")

    def refund(self, order: "Order") -> None:
        raise InvalidTransitionError(self.name, "refund")

    def __repr__(self):
        return f"State({self.name})"


class InvalidTransitionError(Exception):
    def __init__(self, state: str, action: str):
        super().__init__(f"Cannot '{action}' in state '{state}'")


# --- Concrete States ---

class DraftState(OrderState):
    @property
    def name(self) -> str:
        return "draft"

    def place(self, order: "Order") -> None:
        if not order.items:
            raise ValueError("Cannot place empty order")
        order._add_event("Order placed")
        order._transition_to(PendingPaymentState())

    def cancel(self, order: "Order") -> None:
        order._add_event("Draft order discarded")
        order._transition_to(CancelledState())


class PendingPaymentState(OrderState):
    @property
    def name(self) -> str:
        return "pending_payment"

    def pay(self, order: "Order") -> None:
        order._add_event(f"Payment received: ${order.total:.2f}")
        order._transition_to(PaidState())

    def cancel(self, order: "Order") -> None:
        order._add_event("Order cancelled before payment")
        order._transition_to(CancelledState())


class PaidState(OrderState):
    @property
    def name(self) -> str:
        return "paid"

    def ship(self, order: "Order") -> None:
        order._add_event("Order shipped")
        order._transition_to(ShippedState())

    def cancel(self, order: "Order") -> None:
        order._add_event("Order cancelled - refund initiated")
        order._transition_to(CancelledState())


class ShippedState(OrderState):
    @property
    def name(self) -> str:
        return "shipped"

    def deliver(self, order: "Order") -> None:
        order._add_event("Order delivered")
        order._transition_to(DeliveredState())


class DeliveredState(OrderState):
    @property
    def name(self) -> str:
        return "delivered"

    def return_order(self, order: "Order") -> None:
        order._add_event("Return initiated")
        order._transition_to(ReturnedState())


class ReturnedState(OrderState):
    @property
    def name(self) -> str:
        return "returned"

    def refund(self, order: "Order") -> None:
        order._add_event(f"Refund processed: ${order.total:.2f}")
        order._transition_to(RefundedState())


class RefundedState(OrderState):
    @property
    def name(self) -> str:
        return "refunded"


class CancelledState(OrderState):
    @property
    def name(self) -> str:
        return "cancelled"


# --- Context ---

@dataclass
class OrderItem:
    product_id: str
    name: str
    price: float
    quantity: int


class Order:
    """Context - the order whose behavior changes with state."""

    def __init__(self, order_id: str):
        self.order_id = order_id
        self.items: list[OrderItem] = []
        self._state: OrderState = DraftState()
        self._history: list[dict] = []
        self._created_at = datetime.now()

    @property
    def state(self) -> str:
        return self._state.name

    @property
    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def add_item(self, product_id: str, name: str, price: float, quantity: int = 1) -> None:
        if self.state != "draft":
            raise ValueError("Can only add items to draft orders")
        self.items.append(OrderItem(product_id, name, price, quantity))

    def place(self) -> None:
        self._state.place(self)

    def pay(self) -> None:
        self._state.pay(self)

    def ship(self) -> None:
        self._state.ship(self)

    def deliver(self) -> None:
        self._state.deliver(self)

    def cancel(self) -> None:
        self._state.cancel(self)

    def return_order(self) -> None:
        self._state.return_order(self)

    def refund(self) -> None:
        self._state.refund(self)

    def _transition_to(self, new_state: OrderState) -> None:
        old_state = self._state.name
        self._state = new_state
        self._history.append({
            "from": old_state,
            "to": new_state.name,
            "timestamp": datetime.now(),
        })
        print(f"  Order {self.order_id}: {old_state} → {new_state.name}")

    def _add_event(self, event: str) -> None:
        print(f"  [{self.order_id}] {event}")

    def get_history(self) -> list[dict]:
        return self._history.copy()


# Usage
order = Order("ORD-001")
order.add_item("PROD-1", "Widget", 29.99, 2)
order.add_item("PROD-2", "Gadget", 49.99, 1)

print(f"Order total: ${order.total:.2f}")
print(f"Current state: {order.state}\n")

order.place()
order.pay()
order.ship()
order.deliver()

print(f"\nFinal state: {order.state}")
print(f"History: {[(h['from'], h['to']) for h in order.get_history()]}")

# Try invalid transition
print("\nAttempting invalid transition:")
try:
    order.ship()  # Can't ship a delivered order
except InvalidTransitionError as e:
    print(f"  Error: {e}")
```

### State vs Strategy Comparison

| Aspect | State | Strategy |
|---|---|---|
| Purpose | Object changes behavior as state changes | Choose algorithm at creation/runtime |
| Who decides | States trigger transitions | Client picks strategy |
| Awareness | States know about each other (transitions) | Strategies are independent |
| Lifetime | State changes throughout object life | Strategy typically set once |
| Analogy | Traffic light (red→green→yellow) | Navigation (car/walk/bike route) |

### When to Use / When NOT to Use

**Use when:**
- Object behavior depends on its state and changes at runtime
- Operations have large multi-part conditionals on the object's state
- State transitions have clear rules
- You want to make state transitions explicit and auditable

**Don't use when:**
- Object has only 2-3 simple states with simple logic
- States don't have different behavior (just data flags)
- A simple enum + if/elif is clear enough

### Common Mistakes
- States knowing too much about the context (tight coupling)
- Missing transitions (orphan states with no way in/out)
- Not validating transitions (allowing invalid state sequences)
- Mutable state objects shared between contexts

---

## 14. Command Pattern

### Intent
Encapsulate a request as an object, allowing parameterization of clients with different
requests, queueing of requests, and support for undoable operations.

### Problem It Solves

When you need to decouple the object that invokes an operation from the object that
performs it, support undo/redo, queue operations, or log operations for replay.

### UML-Style Structure

```
┌──────────┐      ┌────────────────┐      ┌──────────┐
│  Invoker │─────▶│    Command     │─────▶│ Receiver │
│          │      │  (Interface)   │      │          │
└──────────┘      ├────────────────┤      └──────────┘
                  │+ execute()     │
                  │+ undo()        │
                  └────────────────┘
                          ▲
                     ┌────┴────┐
                ┌─────────┐┌─────────┐
                │CommandA ││CommandB │
                └─────────┘└─────────┘
```

### Full Python Implementation: Text Editor with Undo

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from collections import deque


# --- Command Interface ---

class Command(ABC):
    """Base command with execute and undo."""

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...

    @property
    @abstractmethod
    def description(self) -> str: ...


# --- Receiver ---

class TextDocument:
    """Receiver - the text document being edited."""

    def __init__(self, content: str = ""):
        self._content = content
        self._cursor_position = len(content)
        self._selection: Optional[tuple[int, int]] = None

    @property
    def content(self) -> str:
        return self._content

    @property
    def cursor(self) -> int:
        return self._cursor_position

    def insert_at(self, position: int, text: str) -> None:
        self._content = self._content[:position] + text + self._content[position:]
        self._cursor_position = position + len(text)

    def delete_range(self, start: int, end: int) -> str:
        deleted = self._content[start:end]
        self._content = self._content[:start] + self._content[end:]
        self._cursor_position = start
        return deleted

    def replace_range(self, start: int, end: int, new_text: str) -> str:
        old_text = self._content[start:end]
        self._content = self._content[:start] + new_text + self._content[end:]
        self._cursor_position = start + len(new_text)
        return old_text

    def move_cursor(self, position: int) -> int:
        old = self._cursor_position
        self._cursor_position = max(0, min(position, len(self._content)))
        return old

    def __repr__(self):
        before = self._content[:self._cursor_position]
        after = self._content[self._cursor_position:]
        return f'"{before}|{after}"'


# --- Concrete Commands ---

class InsertCommand(Command):
    """Insert text at cursor position."""

    def __init__(self, document: TextDocument, text: str, position: Optional[int] = None):
        self._document = document
        self._text = text
        self._position = position if position is not None else document.cursor

    def execute(self) -> None:
        self._document.insert_at(self._position, self._text)

    def undo(self) -> None:
        self._document.delete_range(self._position, self._position + len(self._text))

    @property
    def description(self) -> str:
        preview = self._text[:20] + "..." if len(self._text) > 20 else self._text
        return f"Insert '{preview}' at {self._position}"


class DeleteCommand(Command):
    """Delete text range."""

    def __init__(self, document: TextDocument, start: int, end: int):
        self._document = document
        self._start = start
        self._end = end
        self._deleted_text: str = ""

    def execute(self) -> None:
        self._deleted_text = self._document.delete_range(self._start, self._end)

    def undo(self) -> None:
        self._document.insert_at(self._start, self._deleted_text)

    @property
    def description(self) -> str:
        preview = self._deleted_text[:20] + "..." if len(self._deleted_text) > 20 else self._deleted_text
        return f"Delete '{preview}' ({self._start}:{self._end})"


class ReplaceCommand(Command):
    """Replace text in range."""

    def __init__(self, document: TextDocument, start: int, end: int, new_text: str):
        self._document = document
        self._start = start
        self._end = end
        self._new_text = new_text
        self._old_text: str = ""

    def execute(self) -> None:
        self._old_text = self._document.replace_range(self._start, self._end, self._new_text)

    def undo(self) -> None:
        self._document.replace_range(
            self._start, self._start + len(self._new_text), self._old_text
        )

    @property
    def description(self) -> str:
        return f"Replace '{self._old_text[:15]}' with '{self._new_text[:15]}'"


class MacroCommand(Command):
    """Composite command - executes multiple commands as one."""

    def __init__(self, commands: list[Command], name: str = "Macro"):
        self._commands = commands
        self._name = name
        self._executed: list[Command] = []

    def execute(self) -> None:
        self._executed.clear()
        for cmd in self._commands:
            cmd.execute()
            self._executed.append(cmd)

    def undo(self) -> None:
        for cmd in reversed(self._executed):
            cmd.undo()
        self._executed.clear()

    @property
    def description(self) -> str:
        return f"{self._name} ({len(self._commands)} actions)"


# --- Invoker with Undo/Redo ---

class TextEditor:
    """Invoker - manages command execution and undo/redo history."""

    def __init__(self, document: TextDocument):
        self.document = document
        self._undo_stack: deque[Command] = deque(maxlen=100)
        self._redo_stack: deque[Command] = deque(maxlen=100)

    def execute(self, command: Command) -> None:
        """Execute command and add to undo history."""
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()  # New action invalidates redo history

    def undo(self) -> Optional[str]:
        """Undo last command."""
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return command.description

    def redo(self) -> Optional[str]:
        """Redo last undone command."""
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        return command.description

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    # Convenience methods
    def type_text(self, text: str) -> None:
        self.execute(InsertCommand(self.document, text))

    def backspace(self, count: int = 1) -> None:
        pos = self.document.cursor
        if pos > 0:
            start = max(0, pos - count)
            self.execute(DeleteCommand(self.document, start, pos))

    def find_replace(self, find: str, replace: str) -> int:
        """Replace all occurrences - each as separate undoable command."""
        content = self.document.content
        count = 0
        offset = 0

        while True:
            idx = content.find(find, offset)
            if idx == -1:
                break
            self.execute(ReplaceCommand(
                self.document, idx, idx + len(find), replace
            ))
            content = self.document.content
            offset = idx + len(replace)
            count += 1

        return count


# Usage
doc = TextDocument()
editor = TextEditor(doc)

print("=== Typing ===")
editor.type_text("Hello, World!")
print(f"  {doc}")

editor.type_text(" How are you?")
print(f"  {doc}")

print("\n=== Undo ===")
desc = editor.undo()
print(f"  Undid: {desc}")
print(f"  {doc}")

desc = editor.undo()
print(f"  Undid: {desc}")
print(f"  {doc}")

print("\n=== Redo ===")
desc = editor.redo()
print(f"  Redid: {desc}")
print(f"  {doc}")

print("\n=== Find/Replace ===")
editor.type_text(" Hello again, Hello!")
print(f"  {doc}")
count = editor.find_replace("Hello", "Hi")
print(f"  Replaced {count} occurrences")
print(f"  {doc}")

print("\n=== Undo all replacements ===")
while editor.can_undo():
    editor.undo()
print(f"  {doc}")
```

### When to Use / When NOT to Use

**Use when:**
- You need undo/redo functionality
- You need to queue, schedule, or log operations
- You want to support macro recording (composite commands)
- Operations need to be serialized and replayed

**Don't use when:**
- Simple operations with no undo requirement
- The command would just delegate to one method with no added value
- You don't need decoupling between invoker and receiver

### Common Mistakes
- Commands that are too granular (each keystroke as a command)
- Not saving enough state for undo (partial undo that corrupts state)
- Undo stack growing unbounded (memory leak)
- Commands holding references to stale state

---

## 15. Template Method Pattern

### Intent
Define the skeleton of an algorithm in a base class, letting subclasses override specific
steps without changing the algorithm's structure.

### Problem It Solves

When multiple classes share the same algorithm structure but differ in specific steps.
Without Template Method, you'd duplicate the overall flow in each class.

### UML-Style Structure

```
┌────────────────────────────┐
│    AbstractClass           │
├────────────────────────────┤
│+ template_method()         │  ← defines algorithm skeleton
│# step_one() (abstract)     │
│# step_two() (abstract)     │
│# hook() (optional)         │
└────────────────────────────┘
              ▲
         ┌────┴────┐
    ┌─────────┐┌─────────┐
    │ ClassA  ││ ClassB  │
    ├─────────┤├─────────┤
    │#step_one││#step_one│
    │#step_two││#step_two│
    └─────────┘└─────────┘
```

### Full Python Implementation: Data Processing Pipeline

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import json
import csv
import io
from datetime import datetime


@dataclass
class ProcessingResult:
    records_read: int = 0
    records_processed: int = 0
    records_failed: int = 0
    output_path: str = ""
    duration_ms: float = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataProcessor(ABC):
    """Template Method - defines the data processing algorithm skeleton."""

    def process(self, source: str, destination: str) -> ProcessingResult:
        """Template method - the fixed algorithm structure."""
        result = ProcessingResult()
        start_time = datetime.now()

        try:
            # Step 1: Validate source
            self._validate_source(source)

            # Step 2: Extract raw data
            raw_data = self._extract(source)
            result.records_read = len(raw_data)

            # Step 3: Transform data (with optional filtering hook)
            transformed = []
            for record in raw_data:
                if self._should_include(record):  # Hook
                    try:
                        transformed_record = self._transform(record)
                        transformed.append(transformed_record)
                    except Exception as e:
                        result.records_failed += 1
                        result.errors.append(f"Transform error: {e}")
                        if not self._continue_on_error():  # Hook
                            raise

            result.records_processed = len(transformed)

            # Step 4: Load/Save processed data
            self._load(transformed, destination)
            result.output_path = destination

            # Step 5: Post-processing hook
            self._post_process(result)

        except Exception as e:
            result.errors.append(f"Pipeline error: {e}")

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    # Abstract methods - MUST be implemented by subclasses
    @abstractmethod
    def _extract(self, source: str) -> list[dict]: ...

    @abstractmethod
    def _transform(self, record: dict) -> dict: ...

    @abstractmethod
    def _load(self, data: list[dict], destination: str) -> None: ...

    # Hook methods - CAN be overridden by subclasses
    def _validate_source(self, source: str) -> None:
        """Hook: validate source before processing. Default: no-op."""
        pass

    def _should_include(self, record: dict) -> bool:
        """Hook: filter records. Default: include all."""
        return True

    def _continue_on_error(self) -> bool:
        """Hook: whether to continue on transform errors. Default: True."""
        return True

    def _post_process(self, result: ProcessingResult) -> None:
        """Hook: post-processing step. Default: no-op."""
        pass


# --- Concrete Implementations ---

class JSONToCSVProcessor(DataProcessor):
    """Processes JSON data into CSV format."""

    def __init__(self, columns: list[str], delimiter: str = ","):
        self._columns = columns
        self._delimiter = delimiter

    def _extract(self, source: str) -> list[dict]:
        data = json.loads(source)
        if isinstance(data, dict):
            data = data.get("records", data.get("data", [data]))
        print(f"  [JSON→CSV] Extracted {len(data)} records")
        return data

    def _transform(self, record: dict) -> dict:
        transformed = {}
        for col in self._columns:
            value = record.get(col, "")
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            transformed[col] = str(value)
        return transformed

    def _load(self, data: list[dict], destination: str) -> None:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self._columns,
                                delimiter=self._delimiter)
        writer.writeheader()
        writer.writerows(data)
        print(f"  [JSON→CSV] Wrote {len(data)} records to {destination}")
        print(f"  Output preview:\n{output.getvalue()[:200]}")

    def _validate_source(self, source: str) -> None:
        try:
            json.loads(source)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON source: {e}")


class UserDataAnonymizer(DataProcessor):
    """Anonymizes user data for analytics."""

    SENSITIVE_FIELDS = {"email", "phone", "ssn", "credit_card", "password"}

    def _extract(self, source: str) -> list[dict]:
        return json.loads(source)

    def _transform(self, record: dict) -> dict:
        anonymized = {}
        for key, value in record.items():
            if key in self.SENSITIVE_FIELDS:
                anonymized[key] = self._mask(key, str(value))
            else:
                anonymized[key] = value
        anonymized["_anonymized_at"] = datetime.now().isoformat()
        return anonymized

    def _mask(self, field: str, value: str) -> str:
        if field == "email":
            parts = value.split("@")
            return f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else "***"
        elif field == "phone":
            return f"***-***-{value[-4:]}" if len(value) >= 4 else "***"
        else:
            return "*" * len(value)

    def _load(self, data: list[dict], destination: str) -> None:
        output = json.dumps(data, indent=2)
        print(f"  [Anonymizer] Output: {output[:300]}")

    def _should_include(self, record: dict) -> bool:
        return record.get("consent_given", False) is True

    def _post_process(self, result: ProcessingResult) -> None:
        print(f"  [Anonymizer] Post-process: {result.records_processed} records anonymized, "
              f"{result.records_read - result.records_processed} filtered (no consent)")


# Usage
print("=== JSON to CSV ===")
json_data = json.dumps([
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35},
])

processor = JSONToCSVProcessor(columns=["id", "name", "email"])
result = processor.process(json_data, "output.csv")
print(f"  Result: {result.records_read} read, {result.records_processed} processed")

print("\n=== User Data Anonymization ===")
user_data = json.dumps([
    {"id": 1, "name": "Alice", "email": "alice@secret.com", "phone": "555-123-4567",
     "consent_given": True},
    {"id": 2, "name": "Bob", "email": "bob@private.com", "phone": "555-987-6543",
     "consent_given": False},
    {"id": 3, "name": "Charlie", "email": "charlie@hidden.com", "phone": "555-456-7890",
     "consent_given": True},
])

anonymizer = UserDataAnonymizer()
result = anonymizer.process(user_data, "anonymized.json")
print(f"  Result: {result.records_read} read, {result.records_processed} processed")
```

### Template Method vs Strategy

| Aspect | Template Method | Strategy |
|---|---|---|
| Mechanism | Inheritance | Composition |
| What varies | Steps within fixed algorithm | Entire algorithm |
| Flexibility | Subclasses override hooks | Swap entire strategy at runtime |
| Coupling | Subclass coupled to base | Strategy independent |
| Use case | Same structure, different steps | Different algorithms entirely |

### When to Use / When NOT to Use

**Use when:**
- Multiple classes share the same algorithm structure
- You want to let clients extend only particular steps
- You want to control extension points (hooks vs abstract methods)

**Don't use when:**
- Algorithm structure varies between implementations
- You need runtime flexibility (use Strategy instead)
- The hierarchy becomes too deep (prefer composition)

### Common Mistakes
- Making the template method overridable (it should be the invariant)
- Too many abstract methods (makes subclassing burdensome)
- Not providing sensible hook defaults
- Deep inheritance hierarchies (fragile base class problem)

---

## 16. Chain of Responsibility Pattern

### Intent
Avoid coupling the sender of a request to its receiver by giving more than one object a
chance to handle the request. Chain the receiving objects and pass the request along the
chain until an object handles it.

### Problem It Solves

When multiple objects can handle a request and the handler isn't known a priori, or when
you want to issue a request without specifying the receiver explicitly.

### UML-Style Structure

```
┌────────────┐      ┌─────────────────────┐
│   Client   │─────▶│      Handler        │
└────────────┘      │    (Interface)      │
                    ├─────────────────────┤
                    │- next_handler       │
                    │+ handle(request)    │
                    │+ set_next(handler)  │
                    └─────────────────────┘
                              ▲
                    ┌─────────┼─────────┐
                    │         │         │
              ┌──────────┐┌──────────┐┌──────────┐
              │HandlerA ││HandlerB ││HandlerC │
              └──────────┘└──────────┘└──────────┘
```

### Full Python Implementation: Request Validation Chain

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class Request:
    """HTTP-like request to be processed by the chain."""
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Optional[dict] = None
    ip_address: str = "0.0.0.0"
    user_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    status_code: int
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)


class Handler(ABC):
    """Abstract handler in the chain."""

    def __init__(self):
        self._next: Optional["Handler"] = None

    def set_next(self, handler: "Handler") -> "Handler":
        """Set next handler and return it (for chaining)."""
        self._next = handler
        return handler

    def handle(self, request: Request) -> Optional[Response]:
        """Handle request or pass to next handler."""
        result = self._process(request)
        if result is not None:
            return result
        if self._next is not None:
            return self._next.handle(request)
        return None

    @abstractmethod
    def _process(self, request: Request) -> Optional[Response]:
        """Process request. Return Response to stop chain, None to continue."""
        ...


# --- Concrete Handlers (Middleware Chain) ---

class RateLimitHandler(Handler):
    """Rate limiting - blocks excessive requests."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        super().__init__()
        self._max_requests = max_requests
        self._window = window_seconds
        self._request_counts: dict[str, list[float]] = {}

    def _process(self, request: Request) -> Optional[Response]:
        ip = request.ip_address
        now = datetime.now().timestamp()

        if ip not in self._request_counts:
            self._request_counts[ip] = []

        # Clean old entries
        self._request_counts[ip] = [
            t for t in self._request_counts[ip]
            if now - t < self._window
        ]

        if len(self._request_counts[ip]) >= self._max_requests:
            print(f"  [RateLimit] BLOCKED {ip} - {len(self._request_counts[ip])} requests")
            return Response(
                status_code=429,
                body={"error": "Too many requests"},
                headers={"Retry-After": str(self._window)},
            )

        self._request_counts[ip].append(now)
        print(f"  [RateLimit] OK - {ip} ({len(self._request_counts[ip])}/{self._max_requests})")
        return None


class AuthenticationHandler(Handler):
    """Validates authentication token."""

    VALID_TOKENS = {
        "token_alice": "user_alice",
        "token_bob": "user_bob",
        "token_admin": "user_admin",
    }

    def _process(self, request: Request) -> Optional[Response]:
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            # Allow unauthenticated requests to public endpoints
            if request.path.startswith("/public"):
                print("  [Auth] Public endpoint - no auth required")
                return None
            print("  [Auth] REJECTED - No authorization header")
            return Response(status_code=401, body={"error": "Authentication required"})

        token = auth_header.replace("Bearer ", "")
        user_id = self.VALID_TOKENS.get(token)

        if user_id is None:
            print(f"  [Auth] REJECTED - Invalid token")
            return Response(status_code=401, body={"error": "Invalid token"})

        request.user_id = user_id
        print(f"  [Auth] OK - Authenticated as {user_id}")
        return None


class AuthorizationHandler(Handler):
    """Checks if authenticated user has permission for the resource."""

    PERMISSIONS = {
        "user_alice": ["/api/users", "/api/orders"],
        "user_bob": ["/api/users"],
        "user_admin": ["/api/*"],
    }

    def _process(self, request: Request) -> Optional[Response]:
        if request.path.startswith("/public"):
            return None

        if not request.user_id:
            print("  [Authz] REJECTED - No user context")
            return Response(status_code=403, body={"error": "Forbidden"})

        allowed_paths = self.PERMISSIONS.get(request.user_id, [])
        is_allowed = any(
            request.path.startswith(p.replace("*", ""))
            for p in allowed_paths
        )

        if not is_allowed:
            print(f"  [Authz] REJECTED - {request.user_id} cannot access {request.path}")
            return Response(status_code=403, body={"error": "Insufficient permissions"})

        print(f"  [Authz] OK - {request.user_id} can access {request.path}")
        return None


class ValidationHandler(Handler):
    """Validates request body for write operations."""

    def _process(self, request: Request) -> Optional[Response]:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return None

        if request.body is None:
            print("  [Validation] REJECTED - No body for write operation")
            return Response(status_code=400, body={"error": "Request body required"})

        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            print("  [Validation] REJECTED - Invalid content type")
            return Response(status_code=415, body={"error": "JSON required"})

        print("  [Validation] OK")
        return None


class LoggingHandler(Handler):
    """Logs all requests (doesn't stop the chain)."""

    def __init__(self):
        super().__init__()
        self.logs: list[dict] = []

    def _process(self, request: Request) -> Optional[Response]:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "ip": request.ip_address,
            "user": request.user_id,
        }
        self.logs.append(log_entry)
        print(f"  [Log] {request.method} {request.path} from {request.ip_address}")
        return None  # Always continue


# --- Chain Builder ---

class MiddlewareChain:
    """Builds and executes a handler chain."""

    def __init__(self):
        self._first: Optional[Handler] = None
        self._last: Optional[Handler] = None

    def add(self, handler: Handler) -> "MiddlewareChain":
        if self._first is None:
            self._first = handler
            self._last = handler
        else:
            self._last.set_next(handler)
            self._last = handler
        return self

    def handle(self, request: Request) -> Response:
        if self._first is None:
            return Response(status_code=500, body={"error": "No handlers"})

        result = self._first.handle(request)
        if result is None:
            return Response(status_code=200, body={"message": "OK"})
        return result


# Build the chain
chain = MiddlewareChain()
chain.add(LoggingHandler())
chain.add(RateLimitHandler(max_requests=5))
chain.add(AuthenticationHandler())
chain.add(AuthorizationHandler())
chain.add(ValidationHandler())

# Test various requests
print("=== Public endpoint (no auth needed) ===")
response = chain.handle(Request(method="GET", path="/public/health", ip_address="1.2.3.4"))
print(f"  Response: {response.status_code}\n")

print("=== Authenticated request ===")
response = chain.handle(Request(
    method="GET", path="/api/users",
    headers={"Authorization": "Bearer token_alice"},
    ip_address="1.2.3.4",
))
print(f"  Response: {response.status_code}\n")

print("=== Unauthorized access ===")
response = chain.handle(Request(
    method="GET", path="/api/orders",
    headers={"Authorization": "Bearer token_bob"},
    ip_address="1.2.3.4",
))
print(f"  Response: {response.status_code}\n")

print("=== Invalid token ===")
response = chain.handle(Request(
    method="GET", path="/api/users",
    headers={"Authorization": "Bearer invalid_token"},
    ip_address="5.6.7.8",
))
print(f"  Response: {response.status_code}")
```

### When to Use / When NOT to Use

**Use when:**
- Multiple objects may handle a request, and the handler isn't known a priori
- You want to issue a request without specifying the receiver
- The set of handlers should be dynamically configurable
- You're building middleware pipelines

**Don't use when:**
- There's always exactly one handler (direct dispatch is simpler)
- The order of processing doesn't matter (use observer instead)
- All handlers must process every request (that's not a chain, it's a pipeline)

### Common Mistakes
- Chain with no termination (request falls through with no response)
- Handlers that are too tightly coupled to each other
- Not allowing handlers to be reordered
- Making the chain too long (performance and debugging issues)

---

## 17. Mediator Pattern

### Intent
Define an object that encapsulates how a set of objects interact. Mediator promotes loose
coupling by keeping objects from referring to each other explicitly.

### Problem It Solves

When many objects communicate in complex ways, the web of connections becomes unmanageable.
A mediator centralizes communication logic, so objects only know about the mediator.

### UML-Style Structure

```
┌────────────────┐
│    Mediator    │
│  (Interface)   │
├────────────────┤
│+ notify()      │
└────────────────┘
        ▲
        │
┌────────────────┐       ┌─────────────────┐
│ConcreteMediator│◀─────▶│   Colleague     │
│                │       │  (Component)    │
└────────────────┘       └─────────────────┘
                                 ▲
                         ┌───────┼───────┐
                    ┌──────────┐    ┌──────────┐
                    │ColleagueA│    │ColleagueB│
                    └──────────┘    └──────────┘
```

### Full Python Implementation: Chat Room

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class MessageType(Enum):
    TEXT = "text"
    WHISPER = "whisper"
    SYSTEM = "system"
    COMMAND = "command"


@dataclass
class Message:
    sender: str
    content: str
    message_type: MessageType = MessageType.TEXT
    recipient: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ChatMediator(ABC):
    """Mediator interface for chat coordination."""

    @abstractmethod
    def send_message(self, message: Message) -> None: ...

    @abstractmethod
    def add_user(self, user: "ChatUser") -> None: ...

    @abstractmethod
    def remove_user(self, user: "ChatUser") -> None: ...

    @abstractmethod
    def get_online_users(self) -> list[str]: ...


class ChatUser:
    """Colleague - a chat participant that communicates via mediator."""

    def __init__(self, username: str, mediator: ChatMediator):
        self.username = username
        self._mediator = mediator
        self._messages_received: list[Message] = []
        self._is_muted = False
        self._blocked_users: set[str] = set()

    def send(self, content: str) -> None:
        if self._is_muted:
            self.receive(Message("System", "You are muted.", MessageType.SYSTEM))
            return
        message = Message(sender=self.username, content=content)
        self._mediator.send_message(message)

    def whisper(self, recipient: str, content: str) -> None:
        message = Message(
            sender=self.username,
            content=content,
            message_type=MessageType.WHISPER,
            recipient=recipient,
        )
        self._mediator.send_message(message)

    def receive(self, message: Message) -> None:
        if message.sender in self._blocked_users:
            return
        self._messages_received.append(message)
        prefix = {
            MessageType.TEXT: f"[{message.sender}]",
            MessageType.WHISPER: f"[{message.sender} whispers]",
            MessageType.SYSTEM: "[SYSTEM]",
        }.get(message.message_type, "[???]")
        print(f"    {self.username} received: {prefix} {message.content}")

    def block(self, username: str) -> None:
        self._blocked_users.add(username)

    def mute(self) -> None:
        self._is_muted = True

    def unmute(self) -> None:
        self._is_muted = False

    @property
    def message_count(self) -> int:
        return len(self._messages_received)


class ChatRoom(ChatMediator):
    """Concrete mediator - coordinates all chat interactions."""

    def __init__(self, name: str, max_users: int = 50):
        self._name = name
        self._max_users = max_users
        self._users: dict[str, ChatUser] = {}
        self._message_history: list[Message] = []
        self._banned_words: set[str] = {"spam", "scam"}

    def add_user(self, user: ChatUser) -> None:
        if len(self._users) >= self._max_users:
            user.receive(Message("System", "Room is full.", MessageType.SYSTEM))
            return

        self._users[user.username] = user
        system_msg = Message("System", f"{user.username} joined the room.", MessageType.SYSTEM)
        self._broadcast(system_msg, exclude={user.username})
        user.receive(Message(
            "System",
            f"Welcome to {self._name}! Online: {', '.join(self._users.keys())}",
            MessageType.SYSTEM,
        ))

    def remove_user(self, user: ChatUser) -> None:
        if user.username in self._users:
            del self._users[user.username]
            system_msg = Message("System", f"{user.username} left the room.", MessageType.SYSTEM)
            self._broadcast(system_msg)

    def send_message(self, message: Message) -> None:
        if self._contains_banned_words(message.content):
            sender = self._users.get(message.sender)
            if sender:
                sender.receive(Message(
                    "System", "Message blocked: inappropriate content.", MessageType.SYSTEM
                ))
            return

        self._message_history.append(message)

        if message.message_type == MessageType.WHISPER:
            self._deliver_whisper(message)
        else:
            self._broadcast(message, exclude={message.sender})

    def get_online_users(self) -> list[str]:
        return list(self._users.keys())

    def _broadcast(self, message: Message, exclude: set[str] = None) -> None:
        exclude = exclude or set()
        for username, user in self._users.items():
            if username not in exclude:
                user.receive(message)

    def _deliver_whisper(self, message: Message) -> None:
        recipient = self._users.get(message.recipient)
        sender = self._users.get(message.sender)

        if recipient is None:
            if sender:
                sender.receive(Message(
                    "System", f"User '{message.recipient}' not found.", MessageType.SYSTEM
                ))
        else:
            recipient.receive(message)
            if sender:
                sender.receive(Message(
                    "System", f"Whisper sent to {message.recipient}.", MessageType.SYSTEM
                ))

    def _contains_banned_words(self, content: str) -> bool:
        content_lower = content.lower()
        return any(word in content_lower for word in self._banned_words)


# Usage
room = ChatRoom("Python Developers", max_users=10)

alice = ChatUser("Alice", room)
bob = ChatUser("Bob", room)
charlie = ChatUser("Charlie", room)

print("=== Users Joining ===")
room.add_user(alice)
room.add_user(bob)
room.add_user(charlie)

print("\n=== Public Messages ===")
alice.send("Hey everyone! How's it going?")
bob.send("Great! Working on design patterns.")

print("\n=== Whisper ===")
alice.whisper("Bob", "Can you review my PR?")

print("\n=== Banned Content ===")
charlie.send("Check out this spam link!")

print(f"\nOnline users: {room.get_online_users()}")
```

### When to Use / When NOT to Use

**Use when:**
- Objects communicate in complex but well-defined ways
- Reusing objects is difficult because they refer to many others
- A behavior distributed across several classes should be customizable

**Don't use when:**
- Objects have simple, direct relationships
- The mediator would just delegate calls (no coordination logic)
- It would create a god object

### Common Mistakes
- Mediator becoming a god class with too much logic
- Colleagues still communicating directly (bypassing mediator)
- Not defining clear protocols for mediator-colleague interaction
- Mediator handling unrelated concerns

---

## 18. Memento Pattern

### Intent
Without violating encapsulation, capture and externalize an object's internal state so
that the object can be restored to this state later.

### Problem It Solves

When you need to save and restore an object's state (undo, checkpoints, save games) without
exposing its internal structure.

### UML-Style Structure

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Caretaker   │────▶│   Memento    │◀────│  Originator  │
├──────────────┤     ├──────────────┤     ├──────────────┤
│- mementos[]  │     │- state       │     │- state       │
│+ save()      │     │+ get_state() │     │+ save()      │
│+ restore()   │     └──────────────┘     │+ restore()   │
└──────────────┘                          └──────────────┘
```

### Full Python Implementation: Game Save System

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import copy
import json


@dataclass(frozen=True)
class GameMemento:
    """Memento - immutable snapshot of game state."""
    _state: dict
    _timestamp: datetime
    _description: str

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def description(self) -> str:
        return self._description

    def get_state(self) -> dict:
        return copy.deepcopy(self._state)


class GameCharacter:
    """Originator - the game character whose state we save/restore."""

    def __init__(self, name: str, character_class: str):
        self.name = name
        self.character_class = character_class
        self.level = 1
        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.experience = 0
        self.gold = 0
        self.inventory: list[str] = []
        self.position: dict[str, int] = {"x": 0, "y": 0, "zone": "starting_village"}
        self.quests_completed: list[str] = []
        self.skills: dict[str, int] = {}

    def save_state(self, description: str = "") -> GameMemento:
        """Create a memento of current state."""
        state = {
            "name": self.name,
            "character_class": self.character_class,
            "level": self.level,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "experience": self.experience,
            "gold": self.gold,
            "inventory": self.inventory.copy(),
            "position": self.position.copy(),
            "quests_completed": self.quests_completed.copy(),
            "skills": self.skills.copy(),
        }
        return GameMemento(
            _state=state,
            _timestamp=datetime.now(),
            _description=description or f"Save at level {self.level}",
        )

    def restore_state(self, memento: GameMemento) -> None:
        """Restore state from memento."""
        state = memento.get_state()
        self.name = state["name"]
        self.character_class = state["character_class"]
        self.level = state["level"]
        self.hp = state["hp"]
        self.max_hp = state["max_hp"]
        self.mp = state["mp"]
        self.max_mp = state["max_mp"]
        self.experience = state["experience"]
        self.gold = state["gold"]
        self.inventory = state["inventory"]
        self.position = state["position"]
        self.quests_completed = state["quests_completed"]
        self.skills = state["skills"]

    def gain_experience(self, amount: int) -> None:
        self.experience += amount
        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_hp += 20
            self.hp = self.max_hp
            self.max_mp += 10
            self.mp = self.max_mp
            print(f"  🎉 {self.name} leveled up to {self.level}!")

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            print(f"  💀 {self.name} has been defeated!")

    def collect_item(self, item: str) -> None:
        self.inventory.append(item)
        print(f"  📦 Collected: {item}")

    def earn_gold(self, amount: int) -> None:
        self.gold += amount

    def move_to(self, x: int, y: int, zone: str) -> None:
        self.position = {"x": x, "y": y, "zone": zone}
        print(f"  🗺️ Moved to {zone} ({x}, {y})")

    def complete_quest(self, quest: str) -> None:
        self.quests_completed.append(quest)
        print(f"  ✅ Quest completed: {quest}")

    def __repr__(self):
        return (f"{self.name} (Lvl {self.level} {self.character_class}) "
                f"HP:{self.hp}/{self.max_hp} MP:{self.mp}/{self.max_mp} "
                f"Gold:{self.gold} Items:{len(self.inventory)}")


class SaveManager:
    """Caretaker - manages game saves (mementos)."""

    def __init__(self, max_saves: int = 10):
        self._saves: list[GameMemento] = []
        self._max_saves = max_saves
        self._auto_saves: list[GameMemento] = []
        self._max_auto_saves = 3

    def save(self, character: GameCharacter, description: str = "") -> int:
        """Manual save - returns save slot index."""
        memento = character.save_state(description)

        if len(self._saves) >= self._max_saves:
            self._saves.pop(0)  # Remove oldest

        self._saves.append(memento)
        slot = len(self._saves) - 1
        print(f"  💾 Game saved (slot {slot}): {memento.description}")
        return slot

    def auto_save(self, character: GameCharacter) -> None:
        """Automatic checkpoint save."""
        memento = character.save_state(f"Auto-save at level {character.level}")
        if len(self._auto_saves) >= self._max_auto_saves:
            self._auto_saves.pop(0)
        self._auto_saves.append(memento)
        print(f"  💾 Auto-saved: {memento.description}")

    def load(self, character: GameCharacter, slot: int) -> bool:
        """Load from save slot."""
        if 0 <= slot < len(self._saves):
            character.restore_state(self._saves[slot])
            print(f"  📂 Loaded save slot {slot}: {self._saves[slot].description}")
            return True
        print(f"  ❌ Invalid save slot: {slot}")
        return False

    def load_auto_save(self, character: GameCharacter) -> bool:
        """Load most recent auto-save."""
        if self._auto_saves:
            character.restore_state(self._auto_saves[-1])
            print(f"  📂 Loaded auto-save: {self._auto_saves[-1].description}")
            return True
        return False

    def list_saves(self) -> list[str]:
        """List available saves."""
        saves = []
        for i, memento in enumerate(self._saves):
            saves.append(f"  Slot {i}: {memento.description} ({memento.timestamp:%H:%M:%S})")
        return saves


# Usage
hero = GameCharacter("Aria", "Mage")
save_mgr = SaveManager()

print("=== Starting Adventure ===")
print(f"  {hero}\n")

# Save before dangerous area
save_mgr.save(hero, "Before entering dungeon")

hero.move_to(10, 20, "dark_dungeon")
hero.gain_experience(150)
hero.collect_item("Iron Sword")
hero.earn_gold(50)

print(f"\n  {hero}\n")
save_mgr.auto_save(hero)

# Boss fight goes badly
print("=== Boss Fight ===")
hero.take_damage(999)
print(f"  {hero}\n")

# Reload!
print("=== Loading Auto-Save ===")
save_mgr.load_auto_save(hero)
print(f"  {hero}\n")

# Try again successfully
print("=== Boss Fight (Round 2) ===")
hero.gain_experience(500)
hero.collect_item("Dragon Scale")
hero.earn_gold(1000)
hero.complete_quest("Defeat the Dragon")
save_mgr.save(hero, "After dragon boss")
print(f"\n  {hero}")

print("\n=== Available Saves ===")
for save in save_mgr.list_saves():
    print(save)
```

### When to Use / When NOT to Use

**Use when:**
- You need to save/restore object state (undo, checkpoints)
- Direct access to state would violate encapsulation
- You need multiple levels of undo
- You need to support "save points" or "snapshots"

**Don't use when:**
- State is trivial (just store a copy of the few fields)
- The object is immutable (no state to save)
- Saving state is extremely expensive (consider incremental saves)

### Common Mistakes
- Memento that's too large (save only what's needed)
- Not making memento immutable (mutations corrupt history)
- Keeping too many mementos (memory exhaustion)
- Shallow copies in memento (shared mutable references)

---

## 19. Visitor Pattern

### Intent
Represent an operation to be performed on elements of an object structure. Visitor lets
you define a new operation without changing the classes of the elements on which it operates.

### Problem It Solves

When you have a stable class hierarchy but frequently need to add new operations, modifying
each class for every new operation violates OCP. Visitor separates algorithms from the
objects they operate on.

### UML-Style Structure

```
┌───────────────┐         ┌────────────────────┐
│   Element     │         │     Visitor        │
│  (Interface)  │         │   (Interface)      │
├───────────────┤         ├────────────────────┤
│+ accept(v)    │         │+ visit_type_a(e)   │
└───────────────┘         │+ visit_type_b(e)   │
        ▲                 └────────────────────┘
   ┌────┴────┐                     ▲
   │         │                ┌────┴────┐
┌──────┐ ┌──────┐      ┌──────────┐ ┌──────────┐
│TypeA │ │TypeB │      │VisitorX  │ │VisitorY  │
└──────┘ └──────┘      └──────────┘ └──────────┘
```

### Full Python Implementation: AST Visitor

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


# --- Element Hierarchy (AST Nodes) ---

class ASTNode(ABC):
    """Base element - AST node that accepts visitors."""

    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        """Double dispatch - calls the appropriate visit method."""
        ...


@dataclass
class NumberNode(ASTNode):
    value: float

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_number(self)


@dataclass
class StringNode(ASTNode):
    value: str

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_string(self)


@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_unary_op(self)


@dataclass
class VariableNode(ASTNode):
    name: str

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_variable(self)


@dataclass
class AssignNode(ASTNode):
    name: str
    value: ASTNode

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_assign(self)


@dataclass
class FunctionCallNode(ASTNode):
    name: str
    arguments: list[ASTNode]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_function_call(self)


@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_branch: list[ASTNode]
    else_branch: list[ASTNode]

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_if(self)


# --- Visitor Interface ---

class ASTVisitor(ABC):
    """Visitor interface for AST operations."""

    @abstractmethod
    def visit_number(self, node: NumberNode) -> Any: ...

    @abstractmethod
    def visit_string(self, node: StringNode) -> Any: ...

    @abstractmethod
    def visit_binary_op(self, node: BinaryOpNode) -> Any: ...

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode) -> Any: ...

    @abstractmethod
    def visit_variable(self, node: VariableNode) -> Any: ...

    @abstractmethod
    def visit_assign(self, node: AssignNode) -> Any: ...

    @abstractmethod
    def visit_function_call(self, node: FunctionCallNode) -> Any: ...

    @abstractmethod
    def visit_if(self, node: IfNode) -> Any: ...


# --- Concrete Visitors ---

class Evaluator(ASTVisitor):
    """Evaluates the AST and returns results."""

    def __init__(self):
        self._variables: dict[str, Any] = {}
        self._functions: dict[str, callable] = {
            "print": print,
            "abs": abs,
            "max": max,
            "min": min,
        }

    def visit_number(self, node: NumberNode) -> float:
        return node.value

    def visit_string(self, node: StringNode) -> str:
        return node.value

    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        left = node.left.accept(self)
        right = node.right.accept(self)
        ops = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
        }
        op_func = ops.get(node.operator)
        if op_func is None:
            raise ValueError(f"Unknown operator: {node.operator}")
        return op_func(left, right)

    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        operand = node.operand.accept(self)
        if node.operator == "-":
            return -operand
        elif node.operator == "not":
            return not operand
        raise ValueError(f"Unknown unary operator: {node.operator}")

    def visit_variable(self, node: VariableNode) -> Any:
        if node.name not in self._variables:
            raise NameError(f"Undefined variable: {node.name}")
        return self._variables[node.name]

    def visit_assign(self, node: AssignNode) -> Any:
        value = node.value.accept(self)
        self._variables[node.name] = value
        return value

    def visit_function_call(self, node: FunctionCallNode) -> Any:
        func = self._functions.get(node.name)
        if func is None:
            raise NameError(f"Undefined function: {node.name}")
        args = [arg.accept(self) for arg in node.arguments]
        return func(*args)

    def visit_if(self, node: IfNode) -> Any:
        condition = node.condition.accept(self)
        if condition:
            result = None
            for stmt in node.then_branch:
                result = stmt.accept(self)
            return result
        else:
            result = None
            for stmt in node.else_branch:
                result = stmt.accept(self)
            return result


class PrettyPrinter(ASTVisitor):
    """Converts AST back to readable code."""

    def __init__(self, indent_size: int = 2):
        self._indent = 0
        self._indent_size = indent_size

    def _get_indent(self) -> str:
        return " " * (self._indent * self._indent_size)

    def visit_number(self, node: NumberNode) -> str:
        return str(node.value)

    def visit_string(self, node: StringNode) -> str:
        return f'"{node.value}"'

    def visit_binary_op(self, node: BinaryOpNode) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"({left} {node.operator} {right})"

    def visit_unary_op(self, node: UnaryOpNode) -> str:
        operand = node.operand.accept(self)
        return f"({node.operator}{operand})"

    def visit_variable(self, node: VariableNode) -> str:
        return node.name

    def visit_assign(self, node: AssignNode) -> str:
        value = node.value.accept(self)
        return f"{self._get_indent()}{node.name} = {value}"

    def visit_function_call(self, node: FunctionCallNode) -> str:
        args = ", ".join(arg.accept(self) for arg in node.arguments)
        return f"{node.name}({args})"

    def visit_if(self, node: IfNode) -> str:
        cond = node.condition.accept(self)
        lines = [f"{self._get_indent()}if {cond}:"]
        self._indent += 1
        for stmt in node.then_branch:
            lines.append(stmt.accept(self))
        self._indent -= 1
        if node.else_branch:
            lines.append(f"{self._get_indent()}else:")
            self._indent += 1
            for stmt in node.else_branch:
                lines.append(stmt.accept(self))
            self._indent -= 1
        return "\n".join(lines)


class ComplexityAnalyzer(ASTVisitor):
    """Analyzes AST complexity metrics."""

    def __init__(self):
        self.node_count = 0
        self.max_depth = 0
        self.variable_count = 0
        self.function_calls = 0
        self.operators: dict[str, int] = {}
        self._current_depth = 0

    def _track_depth(self):
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)

    def visit_number(self, node: NumberNode) -> None:
        self.node_count += 1

    def visit_string(self, node: StringNode) -> None:
        self.node_count += 1

    def visit_binary_op(self, node: BinaryOpNode) -> None:
        self.node_count += 1
        self.operators[node.operator] = self.operators.get(node.operator, 0) + 1
        self._track_depth()
        node.left.accept(self)
        node.right.accept(self)
        self._current_depth -= 1

    def visit_unary_op(self, node: UnaryOpNode) -> None:
        self.node_count += 1
        self._track_depth()
        node.operand.accept(self)
        self._current_depth -= 1

    def visit_variable(self, node: VariableNode) -> None:
        self.node_count += 1
        self.variable_count += 1

    def visit_assign(self, node: AssignNode) -> None:
        self.node_count += 1
        node.value.accept(self)

    def visit_function_call(self, node: FunctionCallNode) -> None:
        self.node_count += 1
        self.function_calls += 1
        for arg in node.arguments:
            arg.accept(self)

    def visit_if(self, node: IfNode) -> None:
        self.node_count += 1
        self._track_depth()
        node.condition.accept(self)
        for stmt in node.then_branch:
            stmt.accept(self)
        for stmt in node.else_branch:
            stmt.accept(self)
        self._current_depth -= 1

    def report(self) -> str:
        return (
            f"Complexity Report:\n"
            f"  Nodes: {self.node_count}\n"
            f"  Max depth: {self.max_depth}\n"
            f"  Variables referenced: {self.variable_count}\n"
            f"  Function calls: {self.function_calls}\n"
            f"  Operators used: {self.operators}"
        )


# --- Build and visit an AST ---

# Represents: x = (5 + 3) * 2; if x > 10: print(x)
ast = [
    AssignNode("x", BinaryOpNode(
        BinaryOpNode(NumberNode(5), "+", NumberNode(3)),
        "*",
        NumberNode(2),
    )),
    IfNode(
        condition=BinaryOpNode(VariableNode("x"), ">", NumberNode(10)),
        then_branch=[
            FunctionCallNode("print", [VariableNode("x")]),
        ],
        else_branch=[
            FunctionCallNode("print", [StringNode("x is small")]),
        ],
    ),
]

# Visit with different visitors - no changes to AST classes needed!
print("=== Pretty Print ===")
printer = PrettyPrinter()
for node in ast:
    print(node.accept(printer))

print("\n=== Evaluate ===")
evaluator = Evaluator()
for node in ast:
    node.accept(evaluator)

print("\n=== Complexity Analysis ===")
analyzer = ComplexityAnalyzer()
for node in ast:
    node.accept(analyzer)
print(analyzer.report())
```

### When to Avoid Visitor

- When the element hierarchy changes frequently (adding a new element type requires
  updating ALL visitors)
- When element classes are simple enough that adding methods is fine
- When you only need one or two operations (just add methods)
- In Python, consider using `functools.singledispatch` or pattern matching instead

### When to Use / When NOT to Use

**Use when:**
- Object structure is stable but operations change frequently
- Many distinct operations need to be performed on a structure
- You want to accumulate state across elements during traversal
- Element classes shouldn't be polluted with unrelated operations

**Don't use when:**
- Element hierarchy changes frequently
- Only one or two operations exist
- Elements need to stay simple
- Python's simpler dispatch mechanisms suffice

### Common Mistakes
- Using visitor when the hierarchy changes often (maintenance nightmare)
- Visitor accumulating too much state (hard to reason about)
- Not providing a default visit method for extensibility
- Circular dependencies between visitor and element packages

---

## Meta: Design Pattern Wisdom

---

## 20. When NOT to Use Design Patterns

### Over-Engineering Signs

1. **Pattern worship**: "We need a factory for this one class"
2. **Resume-driven development**: Using patterns to impress, not to solve
3. **Premature abstraction**: Adding flexibility that's never exercised
4. **Gold plating**: Perfect extensibility for features that won't be built

### Pattern Addiction

```python
# OVER-ENGINEERED: Factory + Strategy + Observer for a simple greeting

class GreetingStrategy(ABC):
    @abstractmethod
    def greet(self, name: str) -> str: ...

class FormalGreeting(GreetingStrategy):
    def greet(self, name: str) -> str:
        return f"Good day, {name}."

class GreetingFactory:
    @staticmethod
    def create(style: str) -> GreetingStrategy:
        if style == "formal":
            return FormalGreeting()
        raise ValueError(f"Unknown style: {style}")


# JUST RIGHT: A function
def greet(name: str, formal: bool = False) -> str:
    if formal:
        return f"Good day, {name}."
    return f"Hi, {name}!"
```

### YAGNI Applied to Patterns

**You Ain't Gonna Need It** — don't add a pattern "just in case":

```python
# YAGNI violation: abstracting for hypothetical databases
class DatabaseFactory(ABC):
    @abstractmethod
    def create_connection(self): ...

class PostgresFactory(DatabaseFactory):
    def create_connection(self):
        return PostgresConnection()

# You only use Postgres and there are no plans to change.
# Just use: connection = PostgresConnection()
```

### Python-Specific Alternatives

| Pattern | Pythonic Alternative |
|---|---|
| Singleton | Module-level instance |
| Strategy (simple) | First-class function or lambda |
| Command (simple) | Callable / closure |
| Iterator | Generator function |
| Observer (simple) | Callback list |
| Factory (simple) | Class method / `__init_subclass__` |
| Template Method | Function with callable parameters |
| Null Object | `None` with `or` / optional chaining |

```python
# Strategy with first-class functions
def sort_users(users: list[dict], key_func=lambda u: u["name"]):
    return sorted(users, key=key_func)

# Command as a callable
commands = []
commands.append(lambda: print("Hello"))
commands.append(lambda: save_file())
for cmd in commands:
    cmd()

# Iterator as generator
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Observer as callback list
class Button:
    def __init__(self):
        self._on_click: list[callable] = []

    def click(self):
        for handler in self._on_click:
            handler()
```

---

## 21. Design Pattern Tradeoffs

### Complexity vs Flexibility Matrix

| Pattern | Complexity | Flexibility | When Worth It |
|---|---|---|---|
| Singleton | Low | Low | Almost never (use module) |
| Factory Method | Low | Medium | 3+ product types |
| Abstract Factory | Medium | High | Multiple product families |
| Builder | Medium | High | 5+ construction parameters |
| Prototype | Low | Medium | Expensive object creation |
| Adapter | Low | Medium | Third-party integration |
| Decorator | Medium | High | Stackable behaviors |
| Composite | Medium | High | Tree structures |
| Facade | Low | Low | Complex subsystems |
| Proxy | Medium | Medium | Cross-cutting concerns |
| Observer | Medium | High | Event-driven systems |
| Strategy | Low | High | Algorithm swapping |
| State | Medium | High | Complex state machines |
| Command | Medium | High | Undo/redo needed |
| Template Method | Low | Medium | Shared algorithm skeleton |
| Chain of Responsibility | Medium | High | Dynamic handler pipelines |
| Mediator | Medium | Medium | Complex object interaction |
| Memento | Medium | Medium | State snapshots needed |
| Visitor | High | High | Stable hierarchy, many operations |

### Performance Implications

- **Decorator/Proxy chains**: Each layer adds a method call overhead
- **Observer**: Notification storms with many observers
- **Visitor**: Double dispatch adds indirection
- **Composite**: Deep recursion on large trees
- **Command**: Memory overhead of stored commands
- **Memento**: Memory overhead of stored states

### Testability Implications

| Pattern | Testability Impact |
|---|---|
| Strategy | Excellent - swap with test doubles |
| Factory | Good - mock the factory |
| Observer | Good - verify notifications |
| Singleton | Poor - global state bleeds between tests |
| Facade | Moderate - may hide dependencies |
| Command | Excellent - test each command in isolation |

### When to Refactor TO a Pattern

Signs you need a pattern:
1. **Growing switch/if-elif chains** → Strategy or State
2. **Copy-paste with variations** → Template Method
3. **Notifications spreading everywhere** → Observer
4. **"Can we undo that?"** → Command + Memento
5. **"It needs to work with X and Y backends"** → Adapter or Factory
6. **Complex object construction** → Builder
7. **Uncontrolled access** → Proxy

### When to Refactor AWAY from a Pattern

Signs the pattern is hurting:
1. **Only one concrete implementation exists** (premature abstraction)
2. **You can't explain why the indirection helps** (accidental complexity)
3. **New team members are confused by the structure** (over-engineering)
4. **Changes require touching many pattern classes** (wrong pattern choice)
5. **Performance-critical path with unnecessary layers** (death by abstraction)

### Decision Framework

```
1. Do I have a REAL problem (not hypothetical)?
   → No: Don't use a pattern. YAGNI.
   → Yes: Continue.

2. Is there a simpler Python idiom?
   → Yes: Use the idiom (function, generator, module, etc.)
   → No: Continue.

3. Will the pattern be used by its flexibility within 1-2 sprints?
   → No: Consider waiting. Start simple.
   → Yes: Continue.

4. Does the team understand this pattern?
   → No: Document heavily or choose simpler approach.
   → Yes: Implement it.

5. Can I test it easily?
   → No: Reconsider (especially Singleton).
   → Yes: Proceed with implementation.
```

---

## Quick Reference Card

### Pattern Selection by Problem

| Problem | Primary Pattern | Alternative |
|---|---|---|
| Too many constructor params | Builder | dataclass with defaults |
| Create objects by type name | Factory | dict of classes |
| Families of related objects | Abstract Factory | - |
| Expensive object creation | Prototype | Object pool |
| One instance globally | Singleton | Module-level instance |
| Incompatible interfaces | Adapter | Wrapper function |
| Add behavior dynamically | Decorator | @decorator |
| Tree structures | Composite | Nested dicts |
| Simplify complex API | Facade | Helper function |
| Control access/lazy load | Proxy | `__getattr__` |
| React to state changes | Observer | Callbacks/events |
| Swap algorithms | Strategy | Function parameter |
| Object changes behavior by state | State | Enum + if/elif |
| Undo/redo operations | Command + Memento | Copy on write |
| Algorithm skeleton with hooks | Template Method | Function + callbacks |
| Dynamic handler pipeline | Chain of Responsibility | List of functions |
| Reduce coupling | Mediator | Event bus |
| Save/restore state | Memento | Serialization |
| Operations on stable hierarchy | Visitor | singledispatch |

### Patterns Commonly Combined

- **Command + Memento**: Undo/redo with state snapshots
- **Factory + Strategy**: Create strategies by name
- **Composite + Visitor**: Operations on tree structures
- **Observer + Mediator**: Event-driven with coordination
- **Proxy + Decorator**: Access control with added behavior
- **Builder + Factory**: Factory creates builders for complex objects
- **State + Command**: State transitions as undoable commands

---

## Interview Tips

### What Interviewers Look For

1. **Recognition**: Can you identify which pattern fits the problem?
2. **Trade-offs**: Can you articulate why this pattern and not another?
3. **Implementation**: Can you write clean, working code?
4. **Python awareness**: Do you know when Python idioms replace patterns?
5. **Pragmatism**: Do you know when NOT to use a pattern?

### Common LLD Interview Patterns

| System | Likely Patterns |
|---|---|
| Parking Lot | Strategy, Factory, State |
| Elevator System | State, Observer, Command |
| Library Management | Factory, Observer, Strategy |
| Food Delivery | State, Observer, Strategy, Facade |
| Chat Application | Mediator, Observer, Command |
| File System | Composite, Visitor, Iterator |
| Payment System | Strategy, Factory, Adapter, Facade |
| Notification System | Observer, Factory, Strategy, Chain |
| Vending Machine | State |
| Text Editor | Command, Memento |
| Rate Limiter | Strategy, Chain of Responsibility |
| Cache System | Proxy, Strategy |

### Answering Pattern Questions

Structure your answer:
1. **Identify the pattern** (1 sentence)
2. **Explain why** it fits this problem (2-3 sentences)
3. **Draw the structure** (classes and relationships)
4. **Write the code** (clean, with interfaces)
5. **Discuss trade-offs** (what you gain and lose)
6. **Mention alternatives** (shows depth of understanding)

---

## Summary

Design patterns are tools, not rules. In Python:

- **Prefer simplicity**: Use first-class functions, generators, and modules before reaching
  for a full pattern implementation.
- **Know the vocabulary**: Even if you implement it differently, understanding patterns
  helps you communicate.
- **Apply judiciously**: A pattern should reduce complexity, not add it.
- **Stay Pythonic**: Use `Protocol` over `ABC` when possible, prefer composition over deep
  inheritance, leverage `__dunder__` methods for seamless integration.
- **Test everything**: Patterns that make testing harder are probably wrong for your situation.

The best code uses just enough design pattern to solve today's problem while leaving
tomorrow's door open—no more, no less.
