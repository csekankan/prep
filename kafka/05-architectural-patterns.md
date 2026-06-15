# Architectural Patterns for Python Engineers

> A comprehensive, interview-ready guide to ten architectural patterns every backend
> engineer should know — with complete Python implementations, sequence diagrams,
> trade-off analysis, and real-world examples.

---

## Table of Contents

1. [Registry Pattern](#1-registry-pattern)
2. [Dependency Injection Pattern](#2-dependency-injection-pattern)
3. [Service Locator Pattern](#3-service-locator-pattern)
4. [Event Sourcing Pattern](#4-event-sourcing-pattern)
5. [CQRS (Command Query Responsibility Segregation)](#5-cqrs-command-query-responsibility-segregation)
6. [Retry Pattern](#6-retry-pattern)
7. [Circuit Breaker Pattern](#7-circuit-breaker-pattern)
8. [Bulkhead Pattern](#8-bulkhead-pattern)
9. [Saga Pattern](#9-saga-pattern)
10. [Jitter and Backoff Pattern](#10-jitter-and-backoff-pattern)

---

## 1. Registry Pattern

### Problem Statement

You have an open-ended set of implementations (plugins, handlers, serializers,
strategies) and you need a way to:

- **Discover** them at runtime without hard-coding import paths.
- **Add** new ones without modifying existing code (Open/Closed Principle).
- **Look up** the right implementation by a key (string name, enum, MIME type, etc.).

Hard-coding a giant `if/elif` chain or a manual dictionary violates OCP and becomes a
maintenance nightmare as the number of implementations grows.

### Solution Overview

A **Registry** is a mapping from keys to classes (or callables). Implementations
*register themselves* — typically via a class decorator or a metaclass hook — so that
client code never needs to know every concrete class.

```
┌──────────────┐   registers   ┌──────────────┐
│  ConcreteA   │──────────────▶│              │
└──────────────┘               │   Registry   │
┌──────────────┐   registers   │  {key: cls}  │
│  ConcreteB   │──────────────▶│              │
└──────────────┘               └──────┬───────┘
                                      │ lookup(key)
                                      ▼
                               ┌──────────────┐
                               │  Client Code │
                               └──────────────┘
```

### Global Registry vs Scoped Registry

| Aspect | Global Registry | Scoped Registry |
|--------|----------------|-----------------|
| Lifetime | Module-level singleton | Created per context (app, test, request) |
| Isolation | Shared across the entire process | Each scope has its own set of entries |
| Testing | Harder — must monkey-patch or reset | Easy — create a fresh registry per test |
| Thread safety | Must guard with a lock | Often single-threaded within scope |
| Use case | Plugin systems, CLI sub-commands | Per-tenant feature flags, test fixtures |

### Implementation — Global Registry with Class Decorator

```python
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class Registry:
    """A thread-safe, decorator-based class registry."""

    def __init__(self, name: str = "default") -> None:
        self._name = name
        self._store: Dict[str, Type] = {}
        self._lock = threading.Lock()

    # ---- decorator ----
    def register(self, key: Optional[str] = None) -> Callable:
        """Class decorator that registers the decorated class under *key*.

        If *key* is omitted the class's ``__name__`` is used (lower-cased).
        """
        def decorator(cls: Type[T]) -> Type[T]:
            registration_key = key or cls.__name__.lower()
            with self._lock:
                if registration_key in self._store:
                    raise ValueError(
                        f"[{self._name}] Key '{registration_key}' is already "
                        f"registered to {self._store[registration_key]}"
                    )
                self._store[registration_key] = cls
            return cls
        return decorator

    # ---- lookup ----
    def get(self, key: str) -> Type:
        with self._lock:
            if key not in self._store:
                raise KeyError(
                    f"[{self._name}] No registration for key '{key}'. "
                    f"Available: {list(self._store)}"
                )
            return self._store[key]

    def create(self, key: str, *args: Any, **kwargs: Any) -> Any:
        """Shortcut: look up *key* and instantiate the class."""
        cls = self.get(key)
        return cls(*args, **kwargs)

    # ---- introspection ----
    def keys(self) -> list[str]:
        with self._lock:
            return list(self._store)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def __repr__(self) -> str:
        return f"Registry({self._name!r}, keys={self.keys()})"
```

### Auto-Registration with a Base-Class Hook

Instead of decorating every subclass, you can use `__init_subclass__` so that
*inheriting* from a base class is enough.

```python
class AutoRegistered:
    """Any subclass is automatically registered in the class-level registry."""

    _registry: Dict[str, Type[AutoRegistered]] = {}

    def __init_subclass__(cls, registry_key: str | None = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        key = registry_key or cls.__name__.lower()
        if key in AutoRegistered._registry:
            raise ValueError(f"Duplicate registry key: {key}")
        AutoRegistered._registry[key] = cls

    @classmethod
    def get(cls, key: str) -> Type[AutoRegistered]:
        return cls._registry[key]


# Subclasses register themselves just by existing:
class JsonSerializer(AutoRegistered, registry_key="json"):
    def serialize(self, data: dict) -> str:
        import json
        return json.dumps(data)


class XmlSerializer(AutoRegistered, registry_key="xml"):
    def serialize(self, data: dict) -> str:
        return "<data>...</data>"


# Usage
serializer_cls = AutoRegistered.get("json")
serializer = serializer_cls()
print(serializer.serialize({"a": 1}))  # '{"a": 1}'
```

### Real Example — Plugin Registry

```python
handler_registry = Registry("handlers")


class BaseHandler:
    def handle(self, request: dict) -> dict:
        raise NotImplementedError


@handler_registry.register("create_user")
class CreateUserHandler(BaseHandler):
    def handle(self, request: dict) -> dict:
        username = request["username"]
        # ... persistence logic ...
        return {"status": "created", "username": username}


@handler_registry.register("delete_user")
class DeleteUserHandler(BaseHandler):
    def handle(self, request: dict) -> dict:
        user_id = request["user_id"]
        # ... deletion logic ...
        return {"status": "deleted", "user_id": user_id}


def dispatch(action: str, request: dict) -> dict:
    """Dispatcher that never needs modification when new handlers are added."""
    handler = handler_registry.create(action)
    return handler.handle(request)


print(dispatch("create_user", {"username": "alice"}))
# {'status': 'created', 'username': 'alice'}
```

### Thread-Safety Considerations

- **Read-heavy workloads**: Replace `threading.Lock` with `threading.RLock` or
  `concurrent.futures`-style read-write locks for better concurrency.
- **Import-time registration**: In CPython, the GIL serialises module imports, so
  decorator-based registration during import is inherently thread-safe *for that
  specific phase*. Post-import dynamic registration still needs the lock.
- **Frozen registries**: Once the application has started, call a `freeze()` method
  that converts the internal dict to `types.MappingProxyType` — no lock needed for
  reads after that.

```python
import types

class FreezableRegistry(Registry):
    _frozen_view: types.MappingProxyType | None = None

    def freeze(self) -> None:
        with self._lock:
            self._frozen_view = types.MappingProxyType(self._store)

    def get(self, key: str) -> Type:
        if self._frozen_view is not None:
            if key not in self._frozen_view:
                raise KeyError(key)
            return self._frozen_view[key]
        return super().get(key)
```

### Sequence Diagram

```
Client          Registry          ConcreteHandler
  │                │                    │
  │  dispatch(key) │                    │
  │───────────────▶│                    │
  │                │  get(key)          │
  │                │───────┐            │
  │                │◀──────┘ cls found  │
  │                │                    │
  │                │  cls(*args)        │
  │                │───────────────────▶│
  │                │    instance        │
  │                │◀───────────────────│
  │  instance      │                    │
  │◀───────────────│                    │
  │                │                    │
  │  instance.handle(request)           │
  │────────────────────────────────────▶│
  │              response               │
  │◀────────────────────────────────────│
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| You have a growing set of implementations behind a common interface | You have ≤ 3 static implementations — a dict literal is simpler |
| Plugin systems where third-party code registers handlers | Registration order matters and must be deterministic |
| Frameworks that need extension points (e.g., Django admin, Flask blueprints) | You need compile-time guarantees (registries are runtime-only) |

### Common Mistakes

1. **Forgetting to import the module** that contains the `@register` decorator call.
   The class won't register if its module is never imported. Solution: use explicit
   `import_module` calls or entry-point metadata (`importlib.metadata`).
2. **Allowing silent overwrites** — two plugins registering the same key should raise,
   not silently replace.
3. **Storing instances instead of classes** — registries should store *types* and
   create instances on demand to avoid shared mutable state.

### Interview Tips

- Mention that Flask's `@app.route` and pytest's plugin manager both use registries.
- Highlight thread-safety and the freeze optimisation.
- Relate registries to the **Strategy** and **Factory** patterns — a registry is
  essentially a *named factory* with dynamic registration.

---

## 2. Dependency Injection Pattern

### Problem Statement

Classes that create their own collaborators are **tightly coupled** to concrete
implementations. This makes unit testing hard (you can't swap a real database for a
fake), violates the Dependency Inversion Principle, and turns refactoring into a
cascading nightmare.

```python
# Tightly coupled — impossible to unit-test without a real DB.
class OrderService:
    def __init__(self):
        self.db = PostgresDatabase()         # hard-coded
        self.mailer = SmtpMailer()            # hard-coded
        self.logger = FileLogger("/var/log")  # hard-coded
```

### Solution Overview

**Dependency Injection (DI)** means passing collaborators *in* rather than creating
them inside the class. The three flavours:

| Style | Mechanism |
|-------|-----------|
| **Constructor injection** | Deps passed via `__init__` |
| **Method injection** | Deps passed per method call |
| **Interface injection** | Deps set via a setter / protocol method |

### Constructor Injection (Preferred)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol


class Database(Protocol):
    def execute(self, query: str, params: tuple = ()) -> list[dict]: ...


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class Logger(Protocol):
    def info(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...


@dataclass
class OrderService:
    db: Database
    mailer: Mailer
    logger: Logger

    def place_order(self, user_id: int, items: list[dict]) -> int:
        self.logger.info(f"Placing order for user {user_id}")
        order_id = self._persist(user_id, items)
        self._notify(user_id, order_id)
        return order_id

    def _persist(self, user_id: int, items: list[dict]) -> int:
        rows = self.db.execute(
            "INSERT INTO orders (user_id) VALUES (%s) RETURNING id",
            (user_id,),
        )
        order_id = rows[0]["id"]
        for item in items:
            self.db.execute(
                "INSERT INTO order_items (order_id, sku, qty) VALUES (%s,%s,%s)",
                (order_id, item["sku"], item["qty"]),
            )
        return order_id

    def _notify(self, user_id: int, order_id: int) -> None:
        self.mailer.send(
            to=f"user-{user_id}@example.com",
            subject="Order Confirmation",
            body=f"Your order #{order_id} has been placed.",
        )
```

### Method Injection

Use when a dependency is relevant only for one call.

```python
class ReportGenerator:
    def generate(self, data: list[dict], formatter: Formatter) -> str:
        """formatter is injected per call — different reports, different formats."""
        return formatter.format(data)
```

### Interface Injection

Use when the dependency might change during the object's lifetime (rare in Python).

```python
class Configurable:
    _config: Config | None = None

    def set_config(self, config: Config) -> None:
        self._config = config

    @property
    def config(self) -> Config:
        if self._config is None:
            raise RuntimeError("Config not injected yet")
        return self._config
```

### Building a DI Container from Scratch

A DI container automates the wiring. Here is a minimal but functional one:

```python
from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Type, TypeVar, get_type_hints

T = TypeVar("T")


class DIContainer:
    """A minimal dependency-injection container with singleton support."""

    def __init__(self) -> None:
        self._factories: Dict[type, Callable[..., Any]] = {}
        self._singletons: Dict[type, Any] = {}
        self._singleton_types: set[type] = set()

    # ---- registration ----
    def register(
        self,
        interface: type,
        factory: Callable[..., Any] | None = None,
        *,
        singleton: bool = False,
    ) -> None:
        """Register a factory (or concrete class) for *interface*."""
        self._factories[interface] = factory or interface
        if singleton:
            self._singleton_types.add(interface)

    def register_instance(self, interface: type, instance: Any) -> None:
        """Register an already-constructed instance as a singleton."""
        self._singletons[interface] = instance
        self._factories[interface] = lambda: instance

    # ---- resolution ----
    def resolve(self, interface: Type[T]) -> T:
        if interface in self._singletons:
            return self._singletons[interface]

        if interface not in self._factories:
            raise KeyError(f"No registration for {interface}")

        factory = self._factories[interface]
        instance = self._build(factory)

        if interface in self._singleton_types:
            self._singletons[interface] = instance

        return instance

    def _build(self, factory: Callable) -> Any:
        hints = get_type_hints(factory.__init__ if isinstance(factory, type) else factory)
        hints.pop("return", None)

        sig = inspect.signature(factory)
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            dep_type = hints.get(name)
            if dep_type and dep_type in self._factories:
                kwargs[name] = self.resolve(dep_type)
        return factory(**kwargs)

    # ---- convenience ----
    def __getitem__(self, interface: Type[T]) -> T:
        return self.resolve(interface)
```

### Using the Container

```python
# --- Concrete implementations ---
class PostgresDatabase:
    def execute(self, query: str, params: tuple = ()) -> list[dict]:
        print(f"  [Postgres] {query} {params}")
        return [{"id": 42}]


class SmtpMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        print(f"  [SMTP] → {to}: {subject}")


class ConsoleLogger:
    def info(self, msg: str) -> None:
        print(f"  [INFO] {msg}")

    def error(self, msg: str) -> None:
        print(f"  [ERROR] {msg}")


# --- Wire up ---
container = DIContainer()
container.register(Database, PostgresDatabase, singleton=True)
container.register(Mailer, SmtpMailer)
container.register(Logger, ConsoleLogger, singleton=True)
container.register(OrderService)

# --- Resolve ---
service = container.resolve(OrderService)
service.place_order(7, [{"sku": "WIDGET-1", "qty": 3}])
# [INFO] Placing order for user 7
# [Postgres] INSERT INTO orders ...
# [SMTP] → user-7@example.com: Order Confirmation
```

### Testing Benefits

```python
# In tests you swap out real implementations for fakes:

class FakeDatabase:
    def __init__(self):
        self.queries: list[tuple[str, tuple]] = []

    def execute(self, query: str, params: tuple = ()) -> list[dict]:
        self.queries.append((query, params))
        return [{"id": 1}]


class FakeMailer:
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


class FakeLogger:
    def info(self, msg: str) -> None: pass
    def error(self, msg: str) -> None: pass


def test_place_order():
    db = FakeDatabase()
    mailer = FakeMailer()
    svc = OrderService(db=db, mailer=mailer, logger=FakeLogger())

    order_id = svc.place_order(99, [{"sku": "X", "qty": 1}])

    assert order_id == 1
    assert len(db.queries) == 2          # one INSERT orders + one INSERT items
    assert mailer.sent[0]["to"] == "user-99@example.com"
```

### Sequence Diagram

```
Application        DIContainer       PostgresDB   SmtpMailer   ConsoleLogger
    │                  │                 │            │              │
    │ resolve(OrderSvc)│                 │            │              │
    │─────────────────▶│                 │            │              │
    │                  │ resolve(DB)     │            │              │
    │                  │────────────────▶│            │              │
    │                  │   instance      │            │              │
    │                  │◀────────────────│            │              │
    │                  │ resolve(Mailer) │            │              │
    │                  │─────────────────────────────▶│              │
    │                  │   instance      │            │              │
    │                  │◀─────────────────────────────│              │
    │                  │ resolve(Logger) │            │              │
    │                  │────────────────────────────────────────────▶│
    │                  │   instance      │            │              │
    │                  │◀────────────────────────────────────────────│
    │                  │                 │            │              │
    │                  │ OrderSvc(db, mailer, logger) │              │
    │  OrderSvc inst.  │                 │            │              │
    │◀─────────────────│                 │            │              │
```

### Library-Based DI — `dependency-injector` Concepts

The popular `dependency-injector` library uses **Provider** objects. Here's a
conceptual equivalent showing the idea:

```python
class Provider:
    """Wraps a factory and caches if singleton."""
    def __init__(self, factory: Callable, *, singleton: bool = False):
        self._factory = factory
        self._singleton = singleton
        self._instance: Any = None

    def __call__(self, **overrides: Any) -> Any:
        if self._singleton and self._instance is not None:
            return self._instance
        instance = self._factory(**overrides)
        if self._singleton:
            self._instance = instance
        return instance


class Container:
    db: Provider = Provider(PostgresDatabase, singleton=True)
    mailer: Provider = Provider(SmtpMailer)
    logger: Provider = Provider(ConsoleLogger, singleton=True)

    @property
    def order_service(self) -> Provider:
        return Provider(
            lambda: OrderService(
                db=self.db(), mailer=self.mailer(), logger=self.logger()
            )
        )


c = Container()
svc = c.order_service()
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Unit-test isolation is a priority | Tiny scripts or one-off utilities |
| Multiple implementations of the same interface exist | Over-engineering CRUD apps |
| Configuring different wiring for dev/staging/prod | The dependency graph is trivial (≤ 2 deps) |

### Common Mistakes

1. **Service Locator in disguise** — passing the container itself as a dependency
   hides what the class actually needs.
2. **Too many constructor parameters** — if a class needs 8+ deps, it's doing too
   much. Split it.
3. **Circular dependencies** — A depends on B depends on A. Use lazy resolution
   (`Provider` / `Callable`) to break the cycle.

### Interview Tips

- Emphasise that DI is about **inversion of control**: the caller decides what
  concrete types to use, not the callee.
- Python's duck typing and `Protocol` make DI natural — no need for Java-style
  interfaces.
- Mention that FastAPI's `Depends()` is constructor injection for route handlers.

---

## 3. Service Locator Pattern

### Problem Statement

You need a central place to *look up* services at runtime — similar to DI, but instead
of having dependencies pushed in, the consumer *pulls* them from a well-known locator.

### Solution Overview

A **Service Locator** is a global (or scoped) object that maps interface types to
concrete instances. Any code that needs a service asks the locator for it.

```python
from __future__ import annotations
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class ServiceLocator:
    """A simple service locator (global registry of instances)."""

    _services: Dict[type, Any] = {}

    @classmethod
    def register(cls, interface: type, instance: Any) -> None:
        cls._services[interface] = instance

    @classmethod
    def get(cls, interface: Type[T]) -> T:
        if interface not in cls._services:
            raise KeyError(f"Service not found: {interface}")
        return cls._services[interface]

    @classmethod
    def reset(cls) -> None:
        cls._services.clear()
```

### Using the Service Locator

```python
# At startup
ServiceLocator.register(Database, PostgresDatabase())
ServiceLocator.register(Mailer, SmtpMailer())
ServiceLocator.register(Logger, ConsoleLogger())


class OrderServiceSL:
    """Uses the service locator to obtain its dependencies."""

    def place_order(self, user_id: int, items: list[dict]) -> int:
        db = ServiceLocator.get(Database)
        mailer = ServiceLocator.get(Mailer)
        logger = ServiceLocator.get(Logger)

        logger.info(f"Placing order for user {user_id}")
        rows = db.execute(
            "INSERT INTO orders (user_id) VALUES (%s) RETURNING id",
            (user_id,),
        )
        order_id = rows[0]["id"]
        mailer.send(
            to=f"user-{user_id}@example.com",
            subject="Order Confirmation",
            body=f"Your order #{order_id} has been placed.",
        )
        return order_id
```

### Why It's Considered an Anti-Pattern

1. **Hidden dependencies** — You can't tell what `OrderServiceSL` needs by looking at
   its constructor. The dependency list is implicit, scattered across method bodies.
2. **Global mutable state** — `ServiceLocator._services` is a shared mutable
   dictionary. Tests must remember to `reset()` or they'll leak state.
3. **Harder to test** — You must register fakes *into the locator* before every test
   and clean up after.
4. **Violates the Dependency Inversion Principle** — the class depends on the locator
   (a concrete framework detail), not on abstractions alone.

### When It's Still Useful

- **Legacy codebases** where adding constructor injection everywhere is infeasible.
- **Framework internals** where the user never sees the locator (e.g., Django's
  `apps.get_app_config()`).
- **Cross-cutting concerns** like logging or metrics where threading a logger through
  50 call layers is impractical — a scoped service locator or context variable is
  pragmatic.

### Comparison with Dependency Injection

| Aspect | Dependency Injection | Service Locator |
|--------|---------------------|-----------------|
| Dependency visibility | Explicit (constructor signature) | Hidden (inside method bodies) |
| Testability | Easy — pass fakes directly | Requires locator setup/teardown |
| Coupling | Coupled to abstractions only | Coupled to the locator itself |
| Refactoring safety | IDE can trace all deps from the constructor | Must grep for `ServiceLocator.get(...)` |
| When deps are resolved | At object creation time | At first use (lazy) |
| Framework overhead | Needs a container or manual wiring | Trivially simple to implement |

### Sequence Diagram

```
Client             ServiceLocator           Database         Mailer
  │                     │                      │               │
  │ place_order(...)    │                      │               │
  │                     │                      │               │
  │  get(Database)      │                      │               │
  │────────────────────▶│                      │               │
  │   db instance       │                      │               │
  │◀────────────────────│                      │               │
  │                     │                      │               │
  │  get(Mailer)        │                      │               │
  │────────────────────▶│                      │               │
  │   mailer instance   │                      │               │
  │◀────────────────────│                      │               │
  │                     │                      │               │
  │  db.execute(...)    │                      │               │
  │────────────────────────────────────────────▶│               │
  │   result            │                      │               │
  │◀────────────────────────────────────────────│               │
  │                     │                      │               │
  │  mailer.send(...)   │                      │               │
  │────────────────────────────────────────────────────────────▶│
  │                     │                      │               │
```

### Common Mistakes

1. **Not resetting in tests** — leftover registrations cause phantom failures.
2. **Registering the same interface twice** silently — add an overwrite guard or at
   least a warning.
3. **Using it when DI is trivially possible** — if you control object construction,
   prefer DI.

### Interview Tips

- Say: "Service Locator inverts *lookup*, but not *control*. DI inverts both."
- If asked when to choose SL over DI, cite legacy migration and cross-cutting
  infrastructure.
- Mention that Martin Fowler's article calls SL an acceptable alternative to DI when
  the framework can't do constructor injection.

---

## 4. Event Sourcing Pattern

### Problem Statement

Traditional CRUD systems overwrite rows in place. You lose the *history* of how the
current state came to be. Auditing, debugging, and temporal queries become difficult or
impossible.

### Solution Overview

**Event Sourcing** persists every state change as an immutable **event** in an
append-only **event store**. The current state is derived by *replaying* the event
stream. Optionally, **snapshots** cache the state at a point in time to speed up
replay.

```
  ┌─────────┐   append   ┌──────────────────────────────────────────┐
  │ Command │───────────▶│ Event Store (append-only log)            │
  └─────────┘            │ [Created, Deposited, Withdrawn, ...]     │
                         └────────────────┬─────────────────────────┘
                                          │ replay
                                          ▼
                         ┌──────────────────────────────────────────┐
                         │ Current State (rebuilt from events)       │
                         └──────────────────────────────────────────┘
```

### Event Store Implementation

```python
from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Event:
    event_type: str
    aggregate_id: str
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: float = field(default_factory=time.time)
    version: int = 0

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "data": self.data,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "version": self.version,
        }


class EventStore:
    """In-memory event store with optimistic concurrency control."""

    def __init__(self) -> None:
        self._streams: Dict[str, List[Event]] = {}
        self._all_events: List[Event] = []

    def append(
        self, aggregate_id: str, events: List[Event], expected_version: int
    ) -> None:
        stream = self._streams.setdefault(aggregate_id, [])
        current_version = len(stream)
        if current_version != expected_version:
            raise ConcurrencyError(
                f"Expected version {expected_version}, "
                f"but stream is at {current_version}"
            )
        for i, event in enumerate(events):
            versioned = Event(
                event_type=event.event_type,
                aggregate_id=aggregate_id,
                data=event.data,
                event_id=event.event_id,
                timestamp=event.timestamp,
                version=current_version + i + 1,
            )
            stream.append(versioned)
            self._all_events.append(versioned)

    def load_stream(self, aggregate_id: str) -> List[Event]:
        return list(self._streams.get(aggregate_id, []))

    def load_all(self) -> List[Event]:
        return list(self._all_events)


class ConcurrencyError(Exception):
    pass
```

### Aggregate — Rebuilding State from Events

```python
class BankAccount:
    """Aggregate that derives its state from events."""

    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self.balance: float = 0.0
        self.is_open: bool = False
        self.version: int = 0
        self._pending_events: List[Event] = []

    # ---- Commands (produce events) ----
    def open(self, initial_deposit: float) -> None:
        if self.is_open:
            raise ValueError("Account already open")
        if initial_deposit < 0:
            raise ValueError("Initial deposit must be non-negative")
        self._apply(Event(
            event_type="AccountOpened",
            aggregate_id=self.account_id,
            data={"initial_deposit": initial_deposit},
        ))

    def deposit(self, amount: float) -> None:
        self._assert_open()
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._apply(Event(
            event_type="MoneyDeposited",
            aggregate_id=self.account_id,
            data={"amount": amount},
        ))

    def withdraw(self, amount: float) -> None:
        self._assert_open()
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self._apply(Event(
            event_type="MoneyWithdrawn",
            aggregate_id=self.account_id,
            data={"amount": amount},
        ))

    def close(self) -> None:
        self._assert_open()
        if self.balance != 0:
            raise ValueError("Balance must be zero to close")
        self._apply(Event(
            event_type="AccountClosed",
            aggregate_id=self.account_id,
            data={},
        ))

    # ---- Event application ----
    def _apply(self, event: Event) -> None:
        self._mutate(event)
        self._pending_events.append(event)

    def _mutate(self, event: Event) -> None:
        handler = getattr(self, f"_on_{event.event_type}", None)
        if handler is None:
            raise ValueError(f"Unknown event type: {event.event_type}")
        handler(event)
        self.version += 1

    def _on_AccountOpened(self, event: Event) -> None:
        self.is_open = True
        self.balance = event.data["initial_deposit"]

    def _on_MoneyDeposited(self, event: Event) -> None:
        self.balance += event.data["amount"]

    def _on_MoneyWithdrawn(self, event: Event) -> None:
        self.balance -= event.data["amount"]

    def _on_AccountClosed(self, event: Event) -> None:
        self.is_open = False

    def _assert_open(self) -> None:
        if not self.is_open:
            raise ValueError("Account is not open")

    # ---- Persistence helpers ----
    def flush_pending(self) -> List[Event]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    @classmethod
    def from_events(cls, account_id: str, events: List[Event]) -> BankAccount:
        account = cls(account_id)
        for event in events:
            account._mutate(event)
        return account

    def __repr__(self) -> str:
        return (
            f"BankAccount(id={self.account_id}, "
            f"balance={self.balance:.2f}, "
            f"open={self.is_open}, v={self.version})"
        )
```

### Snapshots for Performance

When an aggregate has thousands of events, replaying from the beginning is slow.
A **snapshot** saves the aggregate's state at a known version.

```python
@dataclass
class Snapshot:
    aggregate_id: str
    version: int
    state: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: Dict[str, Snapshot] = {}

    def save(self, snapshot: Snapshot) -> None:
        self._snapshots[snapshot.aggregate_id] = snapshot

    def load(self, aggregate_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(aggregate_id)


class BankAccountRepository:
    SNAPSHOT_INTERVAL = 50

    def __init__(self, event_store: EventStore, snapshot_store: SnapshotStore) -> None:
        self._event_store = event_store
        self._snapshot_store = snapshot_store

    def load(self, account_id: str) -> BankAccount:
        snapshot = self._snapshot_store.load(account_id)
        if snapshot:
            account = BankAccount(account_id)
            account.balance = snapshot.state["balance"]
            account.is_open = snapshot.state["is_open"]
            account.version = snapshot.version
            events = self._event_store.load_stream(account_id)
            remaining = [e for e in events if e.version > snapshot.version]
            for event in remaining:
                account._mutate(event)
        else:
            events = self._event_store.load_stream(account_id)
            account = BankAccount.from_events(account_id, events)
        return account

    def save(self, account: BankAccount) -> None:
        pending = account.flush_pending()
        if not pending:
            return
        expected_version = account.version - len(pending)
        self._event_store.append(account.account_id, pending, expected_version)

        if account.version % self.SNAPSHOT_INTERVAL == 0:
            self._snapshot_store.save(Snapshot(
                aggregate_id=account.account_id,
                version=account.version,
                state={"balance": account.balance, "is_open": account.is_open},
            ))
```

### Full Example — Bank Account with Event Sourcing

```python
def demo_event_sourcing():
    store = EventStore()
    snapshots = SnapshotStore()
    repo = BankAccountRepository(store, snapshots)

    # Open account and transact
    account = BankAccount("acct-001")
    account.open(initial_deposit=100.0)
    account.deposit(50.0)
    account.withdraw(30.0)
    repo.save(account)

    print(f"After transactions: {account}")
    # BankAccount(id=acct-001, balance=120.00, open=True, v=3)

    # Reload from event store — state rebuilt from scratch
    reloaded = repo.load("acct-001")
    print(f"Reloaded: {reloaded}")
    # BankAccount(id=acct-001, balance=120.00, open=True, v=3)

    # Full audit trail
    print("\nEvent log:")
    for event in store.load_stream("acct-001"):
        print(f"  v{event.version} {event.event_type}: {event.data}")


demo_event_sourcing()
```

### Sequence Diagram

```
Client          BankAccount        EventStore        SnapshotStore
  │                 │                  │                   │
  │  open(100)      │                  │                   │
  │────────────────▶│                  │                   │
  │                 │ (apply event)    │                   │
  │                 │                  │                   │
  │  deposit(50)    │                  │                   │
  │────────────────▶│                  │                   │
  │                 │ (apply event)    │                   │
  │                 │                  │                   │
  │  repo.save()    │                  │                   │
  │─────────────────┼─────────────────▶│                   │
  │                 │  append(events)  │                   │
  │                 │                  │                   │
  │  repo.load()    │                  │                   │
  │─────────────────┼────────────────┐ │                   │
  │                 │                │ │ load_snapshot()   │
  │                 │                │ │──────────────────▶│
  │                 │                │ │  snapshot / None  │
  │                 │                │ │◀──────────────────│
  │                 │                │ │ load_stream()     │
  │                 │                │ │──┐                │
  │                 │                │ │◀─┘ events         │
  │                 │  replay        │ │                   │
  │  account        │◀───────────────┘ │                   │
  │◀────────────────│                  │                   │
```

### Pros / Cons and When to Use

| Pros | Cons |
|------|------|
| Complete audit trail | Increased storage requirements |
| Time-travel debugging | Eventual consistency is harder to reason about |
| Easy to add new projections (read models) | Event schema evolution (upcasting) is non-trivial |
| Natural fit for CQRS | Learning curve for the team |

**Use when**: Financial systems, audit-heavy domains, systems needing temporal queries.
**Avoid when**: Simple CRUD, high-throughput systems where storage cost matters, teams
unfamiliar with the pattern.

### Common Mistakes

1. **Putting business logic in event handlers** — event handlers should only *mutate
   state*. Validation belongs in the command methods.
2. **Not versioning events** — when event schemas change, you need upcasters.
3. **Replaying without idempotency** — side-effects in event handlers (sending emails)
   must be guarded.

### Interview Tips

- Clearly distinguish *commands* (intent) from *events* (facts that happened).
- Mention optimistic concurrency via `expected_version`.
- Snapshots are an optimisation, not a requirement.
- Event sourcing pairs naturally with CQRS (next section).

---

## 5. CQRS (Command Query Responsibility Segregation)

### Problem Statement

In many applications the read model and the write model have vastly different
requirements:

- **Writes** need strong consistency, validations, and domain logic.
- **Reads** need denormalized, pre-computed views optimized for specific queries.

Forcing both through a single model leads to compromises on both sides.

### Solution Overview

**CQRS** separates the write side (**Commands**) from the read side (**Queries**) into
distinct models and, optionally, distinct data stores.

```
               ┌────────────────────────────────────────────────┐
               │                  Application                   │
               │                                                │
  Command ────▶│  ┌──────────────┐        ┌──────────────────┐  │◀──── Query
               │  │ Write Model  │──event─▶│  Read Model(s)   │  │
               │  │ (normalized) │        │ (denormalized)   │  │
               │  └──────────────┘        └──────────────────┘  │
               └────────────────────────────────────────────────┘
```

### Command and Query Models

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


# ─── Value Objects / DTOs ───

class OrderStatus(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


@dataclass(frozen=True)
class OrderItem:
    sku: str
    name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


# ─── Commands ───

@dataclass(frozen=True)
class CreateOrderCommand:
    customer_id: str
    items: List[OrderItem]


@dataclass(frozen=True)
class ConfirmOrderCommand:
    order_id: str


@dataclass(frozen=True)
class ShipOrderCommand:
    order_id: str
    tracking_number: str


@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: str
    reason: str


# ─── Events ───

@dataclass(frozen=True)
class OrderCreated:
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total: float
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class OrderConfirmed:
    order_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class OrderShipped:
    order_id: str
    tracking_number: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class OrderCancelled:
    order_id: str
    reason: str
    timestamp: float = field(default_factory=time.time)
```

### Command Handlers (Write Side)

```python
class OrderWriteModel:
    """Handles commands, enforces invariants, emits events."""

    def __init__(self) -> None:
        self._orders: Dict[str, dict] = {}
        self._event_bus: EventBus = EventBus()

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    def handle_create(self, cmd: CreateOrderCommand) -> str:
        order_id = str(uuid4())
        total = sum(item.subtotal for item in cmd.items)
        self._orders[order_id] = {
            "status": OrderStatus.PENDING,
            "customer_id": cmd.customer_id,
            "items": cmd.items,
            "total": total,
        }
        self._event_bus.publish(OrderCreated(
            order_id=order_id,
            customer_id=cmd.customer_id,
            items=cmd.items,
            total=total,
        ))
        return order_id

    def handle_confirm(self, cmd: ConfirmOrderCommand) -> None:
        order = self._get_order(cmd.order_id)
        if order["status"] != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {order['status']} state")
        order["status"] = OrderStatus.CONFIRMED
        self._event_bus.publish(OrderConfirmed(order_id=cmd.order_id))

    def handle_ship(self, cmd: ShipOrderCommand) -> None:
        order = self._get_order(cmd.order_id)
        if order["status"] != OrderStatus.CONFIRMED:
            raise ValueError(f"Cannot ship order in {order['status']} state")
        order["status"] = OrderStatus.SHIPPED
        self._event_bus.publish(OrderShipped(
            order_id=cmd.order_id,
            tracking_number=cmd.tracking_number,
        ))

    def handle_cancel(self, cmd: CancelOrderCommand) -> None:
        order = self._get_order(cmd.order_id)
        if order["status"] in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise ValueError("Cannot cancel shipped/delivered orders")
        order["status"] = OrderStatus.CANCELLED
        self._event_bus.publish(OrderCancelled(
            order_id=cmd.order_id,
            reason=cmd.reason,
        ))

    def _get_order(self, order_id: str) -> dict:
        if order_id not in self._orders:
            raise KeyError(f"Order {order_id} not found")
        return self._orders[order_id]
```

### Event Bus

```python
class EventBus:
    """Simple in-process pub/sub event bus."""

    def __init__(self) -> None:
        self._handlers: Dict[type, List[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Any) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)
```

### Query Handlers (Read Side)

```python
@dataclass
class OrderSummaryView:
    order_id: str
    customer_id: str
    item_count: int
    total: float
    status: str
    tracking_number: Optional[str] = None
    cancel_reason: Optional[str] = None


class OrderReadModel:
    """Maintains a denormalized read model updated by events."""

    def __init__(self) -> None:
        self._views: Dict[str, OrderSummaryView] = {}
        self._by_customer: Dict[str, List[str]] = {}

    # ─── Event handlers (projections) ───

    def on_order_created(self, event: OrderCreated) -> None:
        view = OrderSummaryView(
            order_id=event.order_id,
            customer_id=event.customer_id,
            item_count=sum(i.quantity for i in event.items),
            total=event.total,
            status="PENDING",
        )
        self._views[event.order_id] = view
        self._by_customer.setdefault(event.customer_id, []).append(event.order_id)

    def on_order_confirmed(self, event: OrderConfirmed) -> None:
        self._views[event.order_id].status = "CONFIRMED"

    def on_order_shipped(self, event: OrderShipped) -> None:
        view = self._views[event.order_id]
        view.status = "SHIPPED"
        view.tracking_number = event.tracking_number

    def on_order_cancelled(self, event: OrderCancelled) -> None:
        view = self._views[event.order_id]
        view.status = "CANCELLED"
        view.cancel_reason = event.reason

    # ─── Queries ───

    def get_order(self, order_id: str) -> OrderSummaryView:
        if order_id not in self._views:
            raise KeyError(f"Order {order_id} not found")
        return self._views[order_id]

    def get_customer_orders(self, customer_id: str) -> List[OrderSummaryView]:
        ids = self._by_customer.get(customer_id, [])
        return [self._views[oid] for oid in ids]

    def get_orders_by_status(self, status: str) -> List[OrderSummaryView]:
        return [v for v in self._views.values() if v.status == status]
```

### Wiring It Together

```python
def demo_cqrs():
    write_model = OrderWriteModel()
    read_model = OrderReadModel()

    bus = write_model.event_bus
    bus.subscribe(OrderCreated, read_model.on_order_created)
    bus.subscribe(OrderConfirmed, read_model.on_order_confirmed)
    bus.subscribe(OrderShipped, read_model.on_order_shipped)
    bus.subscribe(OrderCancelled, read_model.on_order_cancelled)

    # Create an order
    order_id = write_model.handle_create(CreateOrderCommand(
        customer_id="cust-42",
        items=[
            OrderItem(sku="WIDGET-A", name="Widget A", quantity=2, unit_price=9.99),
            OrderItem(sku="GADGET-B", name="Gadget B", quantity=1, unit_price=24.99),
        ],
    ))

    # Query the read model
    summary = read_model.get_order(order_id)
    print(f"Created: {summary}")

    # Confirm
    write_model.handle_confirm(ConfirmOrderCommand(order_id=order_id))
    print(f"Confirmed: {read_model.get_order(order_id)}")

    # Ship
    write_model.handle_ship(ShipOrderCommand(
        order_id=order_id, tracking_number="TRACK-123"
    ))
    print(f"Shipped: {read_model.get_order(order_id)}")


demo_cqrs()
```

### Sequence Diagram

```
Client        WriteModel       EventBus        ReadModel
  │               │                │               │
  │ CreateOrder   │                │               │
  │──────────────▶│                │               │
  │               │ validate       │               │
  │               │ persist        │               │
  │               │ OrderCreated   │               │
  │               │───────────────▶│               │
  │               │                │  project      │
  │               │                │──────────────▶│
  │   order_id    │                │               │
  │◀──────────────│                │               │
  │               │                │               │
  │ GetOrder(id)  │                │               │
  │────────────────────────────────────────────────▶│
  │  OrderSummary │                │               │
  │◀────────────────────────────────────────────────│
```

### When CQRS Adds Unnecessary Complexity

- **Simple CRUD apps** where read and write models are identical.
- **Small teams** that don't have the bandwidth to maintain two models.
- **Low traffic** systems where a single normalized DB serves both reads and writes
  well.
- **When eventual consistency is unacceptable** — CQRS with separate data stores
  introduces a propagation delay.

### Common Mistakes

1. **Applying CQRS everywhere** — it's a strategic pattern for complex domains, not a
   blanket architecture.
2. **Ignoring eventual consistency** — the read model may lag behind the write model.
   Design the UI accordingly (optimistic updates, loading states).
3. **Not idempotent projections** — if an event is replayed, the projection must
   produce the same result.

### Interview Tips

- CQRS does **not** require event sourcing, but they pair well.
- Highlight that the read model can use a completely different storage engine (e.g.,
  Elasticsearch for full-text search while the write model uses Postgres).
- Mention that CQRS enables independent scaling of read and write workloads.

---

## 6. Retry Pattern

### Problem Statement

Distributed systems experience **transient failures**: network timeouts, HTTP 503s,
database connection resets, rate-limiting (429). A single failure should not crash the
entire operation if a retry would succeed.

### Solution Overview

Wrap unreliable calls in a retry loop with configurable:

- **Max attempts**
- **Delay strategy** (fixed, linear, exponential, with jitter)
- **Retry condition** (which exceptions to retry on)
- **Idempotency** (the operation must be safe to repeat)

### Simple Retry

```python
import time
import random
from functools import wraps
from typing import Callable, Tuple, Type


def simple_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Retry with a fixed delay between attempts."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(
                            f"  [retry] attempt {attempt}/{max_attempts} "
                            f"failed: {e}. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
```

### Retry with Exponential Backoff

```python
def retry_with_backoff(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Retry with exponential backoff and optional jitter."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )
                    if jitter:
                        delay = random.uniform(0, delay)
                    print(
                        f"  [retry] attempt {attempt}/{max_attempts} "
                        f"failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
```

### Retry Budget

A **retry budget** limits the fraction of total requests that can be retries, preventing
retry storms.

```python
import threading


class RetryBudget:
    """Token-bucket style retry budget.

    Allows at most *budget_ratio* of recent requests to be retries.
    """

    def __init__(self, budget_ratio: float = 0.1, window_size: int = 100) -> None:
        self._budget_ratio = budget_ratio
        self._window_size = window_size
        self._total_requests = 0
        self._retry_requests = 0
        self._lock = threading.Lock()

    def can_retry(self) -> bool:
        with self._lock:
            if self._total_requests == 0:
                return True
            ratio = self._retry_requests / self._total_requests
            return ratio < self._budget_ratio

    def record_request(self, is_retry: bool = False) -> None:
        with self._lock:
            self._total_requests += 1
            if is_retry:
                self._retry_requests += 1
            if self._total_requests > self._window_size:
                self._total_requests = self._window_size // 2
                self._retry_requests = max(0, self._retry_requests // 2)


def retry_with_budget(
    budget: RetryBudget,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                is_retry = attempt > 1
                if is_retry and not budget.can_retry():
                    raise RuntimeError(
                        "Retry budget exhausted — too many retries"
                    )
                budget.record_request(is_retry=is_retry)
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(base_delay * attempt)
            raise last_exception
        return wrapper
    return decorator
```

### Idempotency Requirements

Retries are only safe if the operation is **idempotent** — calling it N times has the
same effect as calling it once.

| Operation | Idempotent? | How to Make Idempotent |
|-----------|-------------|----------------------|
| `GET /resource/123` | Yes | Read-only by nature |
| `PUT /resource/123 {data}` | Yes | Overwrites with the same data |
| `DELETE /resource/123` | Yes | Deleting twice = same result |
| `POST /orders` | **No** | Use an idempotency key (client-generated UUID) |

```python
class IdempotentOrderCreator:
    """Ensures an order is only created once per idempotency key."""

    def __init__(self):
        self._processed_keys: dict[str, int] = {}

    def create_order(self, idempotency_key: str, order_data: dict) -> int:
        if idempotency_key in self._processed_keys:
            return self._processed_keys[idempotency_key]

        order_id = self._persist(order_data)
        self._processed_keys[idempotency_key] = order_id
        return order_id

    def _persist(self, order_data: dict) -> int:
        import random
        return random.randint(1000, 9999)
```

### Real Example — HTTP Client with Retry

```python
import urllib.request
import urllib.error


class HttpClient:
    """HTTP client with built-in retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
        retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
    ):
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._retryable = retryable_status_codes

    def get(self, url: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read().decode()

            except urllib.error.HTTPError as e:
                last_error = e
                if e.code not in self._retryable:
                    raise
                retry_after = e.headers.get("Retry-After")
                delay = (
                    float(retry_after)
                    if retry_after
                    else self._base_delay * (2 ** (attempt - 1))
                )
                delay = min(delay + random.uniform(0, 1), 60)
                print(
                    f"  [HTTP] {e.code} on attempt {attempt}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

            except (urllib.error.URLError, TimeoutError) as e:
                last_error = e
                delay = self._base_delay * (2 ** (attempt - 1))
                print(
                    f"  [HTTP] Network error on attempt {attempt}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        raise last_error  # type: ignore[misc]
```

### Sequence Diagram

```
Client          RetryDecorator       ExternalService
  │                  │                     │
  │  call()          │                     │
  │─────────────────▶│                     │
  │                  │  attempt 1          │
  │                  │────────────────────▶│
  │                  │  500 Server Error   │
  │                  │◀────────────────────│
  │                  │                     │
  │                  │  sleep(1s)          │
  │                  │                     │
  │                  │  attempt 2          │
  │                  │────────────────────▶│
  │                  │  503 Unavailable    │
  │                  │◀────────────────────│
  │                  │                     │
  │                  │  sleep(2s)          │
  │                  │                     │
  │                  │  attempt 3          │
  │                  │────────────────────▶│
  │                  │  200 OK + body      │
  │                  │◀────────────────────│
  │  result          │                     │
  │◀─────────────────│                     │
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Transient failures are expected (network, rate limits) | The operation is **not** idempotent and you can't add idempotency keys |
| The downstream service is known to have occasional blips | The failure is **deterministic** (4xx client error, validation failure) |
| You need to meet an SLA despite imperfect infrastructure | Retries would cause a **thundering herd** (use jitter + budgets) |

### Common Mistakes

1. **Retrying non-transient errors** — a 400 Bad Request will fail every time.
2. **No backoff** — hammering the server immediately makes things worse.
3. **Unbounded retries** — always set `max_attempts`.
4. **Ignoring `Retry-After` headers** — the server is telling you when to retry.
5. **Not making operations idempotent** — retrying a non-idempotent `POST` can create
   duplicates.

### Interview Tips

- Always pair retry with **idempotency**.
- Know the difference between retry and circuit breaker — retry is per-call, circuit
  breaker is per-target.
- Mention retry budgets as a protection against retry storms.

---

## 7. Circuit Breaker Pattern

### Problem Statement

When a downstream service is failing, retrying every call wastes resources and can
cascade the failure upstream. You need a way to **fast-fail** when a service is
known to be down, then **probe** periodically to check if it's recovered.

### Solution Overview

A circuit breaker has three states:

```
       success
  ┌───────────────┐
  │               ▼
  │    ┌────────────────┐
  │    │    CLOSED      │ ← Normal operation
  │    │ (requests flow)│
  │    └───────┬────────┘
  │            │ failure_count ≥ threshold
  │            ▼
  │    ┌────────────────┐
  │    │     OPEN       │ ← Fast-fail all requests
  │    │  (no requests) │
  │    └───────┬────────┘
  │            │ timeout expires
  │            ▼
  │    ┌────────────────┐
  └────│   HALF-OPEN    │ ← Allow ONE probe request
       │ (one request)  │
       └───────┬────────┘
               │ probe fails → back to OPEN
```

### Python Implementation

```python
from __future__ import annotations

import threading
import time
from enum import Enum, auto
from typing import Any, Callable, Tuple, Type


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit is open and calls are rejected."""
    pass


class CircuitBreaker:
    """Thread-safe circuit breaker with configurable thresholds."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        name: str = "default",
    ) -> None:
        self._name = name
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout
        self._expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._lock = threading.Lock()

        self._listeners: list[Callable[[CircuitState, CircuitState], None]] = []

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and time.time() - self._last_failure_time >= self._timeout
            ):
                self._transition(CircuitState.HALF_OPEN)
            return self._state

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and time.time() - self._last_failure_time >= self._timeout
            ):
                self._transition(CircuitState.HALF_OPEN)

            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit '{self._name}' is OPEN — call rejected"
                )

        try:
            result = func(*args, **kwargs)
        except self._expected_exceptions as e:
            self._record_failure()
            raise
        else:
            self._record_success()
            return result

    def _record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._success_count = 0
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.OPEN)
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self._failure_threshold
            ):
                self._transition(CircuitState.OPEN)

    def _record_success(self) -> None:
        with self._lock:
            self._success_count += 1
            self._failure_count = 0
            if (
                self._state == CircuitState.HALF_OPEN
                and self._success_count >= self._success_threshold
            ):
                self._transition(CircuitState.CLOSED)

    def _transition(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        self._failure_count = 0
        self._success_count = 0
        for listener in self._listeners:
            listener(old_state, new_state)
        print(
            f"  [circuit:{self._name}] {old_state.name} → {new_state.name}"
        )

    def on_state_change(
        self, listener: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        self._listeners.append(listener)

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker({self._name!r}, state={self._state.name}, "
            f"failures={self._failure_count})"
        )
```

### Circuit Breaker as a Decorator

```python
def circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 30.0,
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        expected_exceptions=expected_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cb.call(func, *args, **kwargs)

        wrapper.circuit_breaker = cb  # type: ignore[attr-defined]
        return wrapper

    return decorator
```

### Integration with Retry

The retry decorator goes **inside** the circuit breaker so that failed retries count
toward the breaker's threshold.

```python
@circuit_breaker(failure_threshold=3, timeout=10.0)
@retry_with_backoff(max_attempts=2, base_delay=0.5)
def call_payment_service(order_id: str, amount: float) -> dict:
    """Each failed retry-set increments the circuit breaker's failure count."""
    import urllib.request
    resp = urllib.request.urlopen(
        f"https://payments.example.com/charge?order={order_id}&amount={amount}",
        timeout=5,
    )
    return {"status": "charged"}
```

### Real Example — External Service Call Protection

```python
class ExternalPricingService:
    """Wraps calls to an unreliable third-party pricing API."""

    def __init__(self) -> None:
        self._cb = CircuitBreaker(
            failure_threshold=3,
            success_threshold=2,
            timeout=15.0,
            expected_exceptions=(ConnectionError, TimeoutError),
            name="pricing-service",
        )
        self._fallback_prices = {"WIDGET-A": 9.99, "GADGET-B": 24.99}

    def get_price(self, sku: str) -> float:
        try:
            return self._cb.call(self._fetch_price, sku)
        except CircuitBreakerOpenError:
            print(f"  [pricing] Circuit open — using fallback for {sku}")
            return self._fallback_prices.get(sku, 0.0)
        except (ConnectionError, TimeoutError):
            print(f"  [pricing] Call failed — using fallback for {sku}")
            return self._fallback_prices.get(sku, 0.0)

    def _fetch_price(self, sku: str) -> float:
        # Simulates an unreliable service
        import random
        if random.random() < 0.6:
            raise ConnectionError("pricing service unavailable")
        return self._fallback_prices.get(sku, 0.0) * 1.1


def demo_circuit_breaker():
    svc = ExternalPricingService()
    for i in range(15):
        price = svc.get_price("WIDGET-A")
        print(f"  Call {i+1}: price={price:.2f}")
        time.sleep(0.3)


demo_circuit_breaker()
```

### Monitoring and Alerting

```python
class CircuitBreakerMonitor:
    """Collects metrics from circuit breakers for observability."""

    def __init__(self) -> None:
        self._state_changes: list[dict] = []
        self._breakers: dict[str, CircuitBreaker] = {}

    def register(self, cb: CircuitBreaker) -> None:
        self._breakers[cb._name] = cb
        cb.on_state_change(lambda old, new: self._on_change(cb._name, old, new))

    def _on_change(
        self, name: str, old: CircuitState, new: CircuitState
    ) -> None:
        record = {
            "breaker": name,
            "from": old.name,
            "to": new.name,
            "timestamp": time.time(),
        }
        self._state_changes.append(record)
        if new == CircuitState.OPEN:
            self._alert(f"ALERT: Circuit '{name}' opened!")

    def _alert(self, message: str) -> None:
        print(f"  🚨 {message}")

    def report(self) -> list[dict]:
        return list(self._state_changes)
```

### Sequence Diagram

```
Client         CircuitBreaker        ExternalService
  │                 │                      │
  │  call(fn)       │  [CLOSED]            │
  │────────────────▶│                      │
  │                 │  fn()                │
  │                 │─────────────────────▶│
  │                 │  error               │
  │                 │◀─────────────────────│
  │                 │  failure_count++     │
  │  exception      │                      │
  │◀────────────────│                      │
  │                 │                      │
  │  ... (failures reach threshold) ...    │
  │                 │                      │
  │  call(fn)       │  [OPEN]              │
  │────────────────▶│                      │
  │  CircuitOpen!   │  (no call made)      │
  │◀────────────────│                      │
  │                 │                      │
  │  ... (timeout expires) ...             │
  │                 │                      │
  │  call(fn)       │  [HALF-OPEN]         │
  │────────────────▶│                      │
  │                 │  fn() (probe)        │
  │                 │─────────────────────▶│
  │                 │  200 OK              │
  │                 │◀─────────────────────│
  │                 │  → CLOSED            │
  │  result         │                      │
  │◀────────────────│                      │
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Calling remote services that can be slow or flaky | The downstream failure is always transient and resolves in <1s |
| You have a meaningful fallback (cache, default, degraded response) | There is no fallback — failing fast just shifts the error |
| You want to protect shared resources (thread pool, connection pool) | Intra-process calls between tightly-coupled components |

### Common Mistakes

1. **Threshold too low** — a single transient error opens the circuit.
2. **Timeout too long** — the circuit stays open minutes after the service has recovered.
3. **No fallback** — the circuit breaker rejects the call, but the client has nothing
   to return.
4. **Not monitoring state transitions** — you need to know when circuits open in
   production.

### Interview Tips

- Name the three states and their transitions.
- Mention that Netflix Hystrix popularised the pattern.
- The circuit breaker wraps the retry, not the other way around.
- Discuss fallback strategies: cached value, degraded response, queuing for later.

---

## 8. Bulkhead Pattern

### Problem Statement

A single failing downstream service can consume all threads or connections in a shared
pool, causing **cascading failure** across unrelated services. Even healthy services
become unreachable because the pool is exhausted.

### Solution Overview

The **Bulkhead** pattern isolates resource pools so that a failure in one area cannot
drain resources from another — just like watertight compartments in a ship's hull.

```
  ┌─────────────────────────────────────────┐
  │              Application                │
  │                                         │
  │   ┌──────────┐   ┌──────────┐          │
  │   │ Pool A   │   │ Pool B   │          │
  │   │ (max=5)  │   │ (max=5)  │          │
  │   └────┬─────┘   └────┬─────┘          │
  │        │              │                 │
  │        ▼              ▼                 │
  │   Service A      Service B              │
  │   (failing)      (healthy)              │
  │                                         │
  │   Pool A full → Pool B unaffected       │
  └─────────────────────────────────────────┘
```

### Semaphore Bulkhead

Limits concurrency with a bounded semaphore.

```python
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


class SemaphoreBulkhead:
    """Limits concurrent access to a resource using a semaphore."""

    def __init__(self, name: str, max_concurrent: int, max_wait: float = 5.0) -> None:
        self._name = name
        self._max_concurrent = max_concurrent
        self._max_wait = max_wait
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active = 0
        self._rejected = 0
        self._lock = threading.Lock()

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        acquired = self._semaphore.acquire(timeout=self._max_wait)
        if not acquired:
            with self._lock:
                self._rejected += 1
            raise BulkheadFullError(
                f"Bulkhead '{self._name}' is full "
                f"({self._max_concurrent} concurrent calls). "
                f"Rejected={self._rejected}"
            )
        with self._lock:
            self._active += 1
        try:
            return func(*args, **kwargs)
        finally:
            self._semaphore.release()
            with self._lock:
                self._active -= 1

    @property
    def metrics(self) -> dict:
        with self._lock:
            return {
                "name": self._name,
                "max_concurrent": self._max_concurrent,
                "active": self._active,
                "rejected": self._rejected,
            }


class BulkheadFullError(Exception):
    pass
```

### Thread Pool Bulkhead

Assigns each downstream service its own dedicated thread pool.

```python
class ThreadPoolBulkhead:
    """Each downstream service gets a dedicated thread pool."""

    def __init__(self, name: str, max_workers: int = 5, queue_size: int = 10) -> None:
        self._name = name
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"bulkhead-{name}",
        )
        self._queue_semaphore = threading.Semaphore(max_workers + queue_size)
        self._rejected = 0

    def submit(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        acquired = self._queue_semaphore.acquire(blocking=False)
        if not acquired:
            self._rejected += 1
            raise BulkheadFullError(
                f"ThreadPool bulkhead '{self._name}' is full "
                f"(rejected={self._rejected})"
            )
        future = self._executor.submit(self._run, func, *args, **kwargs)
        return future

    def _run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        finally:
            self._queue_semaphore.release()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)
```

### Real Example — Microservice Resilience

```python
class MicroserviceGateway:
    """API gateway that isolates calls to each downstream service."""

    def __init__(self) -> None:
        self._payment_bulkhead = SemaphoreBulkhead("payment", max_concurrent=3)
        self._inventory_bulkhead = SemaphoreBulkhead("inventory", max_concurrent=5)
        self._notification_bulkhead = SemaphoreBulkhead("notification", max_concurrent=2)

    def charge_payment(self, order_id: str, amount: float) -> dict:
        return self._payment_bulkhead.execute(
            self._call_payment, order_id, amount
        )

    def check_inventory(self, sku: str) -> dict:
        return self._inventory_bulkhead.execute(
            self._call_inventory, sku
        )

    def send_notification(self, user_id: str, message: str) -> dict:
        return self._notification_bulkhead.execute(
            self._call_notification, user_id, message
        )

    def _call_payment(self, order_id: str, amount: float) -> dict:
        time.sleep(2)  # simulate slow service
        return {"charged": True, "order_id": order_id}

    def _call_inventory(self, sku: str) -> dict:
        time.sleep(0.1)
        return {"available": True, "sku": sku}

    def _call_notification(self, user_id: str, message: str) -> dict:
        time.sleep(0.05)
        return {"sent": True}


def demo_bulkhead():
    gw = MicroserviceGateway()

    def make_calls(label: str):
        try:
            result = gw.charge_payment("order-1", 99.99)
            print(f"  [{label}] Payment: {result}")
        except BulkheadFullError as e:
            print(f"  [{label}] Rejected: {e}")

    threads = []
    for i in range(8):
        t = threading.Thread(target=make_calls, args=(f"thread-{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"\nPayment bulkhead metrics: {gw._payment_bulkhead.metrics}")


demo_bulkhead()
```

### Combining Bulkhead with Circuit Breaker

```python
class ResilientServiceCall:
    """Combines bulkhead + circuit breaker + retry for maximum resilience."""

    def __init__(self, name: str) -> None:
        self._bulkhead = SemaphoreBulkhead(name, max_concurrent=5, max_wait=2.0)
        self._circuit = CircuitBreaker(
            failure_threshold=3,
            timeout=15.0,
            name=name,
        )

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        return self._bulkhead.execute(self._circuit.call, func, *args, **kwargs)
```

### Sequence Diagram

```
Client        Bulkhead(max=3)     Service
  │                │                 │
  │ call 1         │                 │
  │───────────────▶│  semaphore=2    │
  │                │────────────────▶│
  │ call 2         │  semaphore=1    │
  │───────────────▶│────────────────▶│
  │ call 3         │  semaphore=0    │
  │───────────────▶│────────────────▶│
  │ call 4         │  (no permits)   │
  │───────────────▶│                 │
  │ BulkheadFull!  │                 │
  │◀───────────────│                 │
  │                │                 │
  │                │  call 1 done    │
  │◀───────────────│◀────────────────│
  │                │  semaphore=1    │
  │ call 5         │                 │
  │───────────────▶│────────────────▶│
  │                │                 │
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Multiple downstream services with different reliability profiles | A single downstream — there's nothing to isolate |
| You need to prevent cascading failures | The application is simple and has abundant resources |
| Shared thread/connection pools are a bottleneck | All downstream calls are equally critical and equally fast |

### Common Mistakes

1. **Pool sizes too small** — legitimate traffic gets rejected even when the service
   is healthy.
2. **Pool sizes too large** — defeats the purpose; a failing service can still
   consume everything.
3. **Not monitoring rejections** — you need visibility into how often the bulkhead
   rejects calls.
4. **No fallback for rejected calls** — the client needs a plan when the bulkhead
   says "no".

### Interview Tips

- The name comes from ship construction — watertight compartments.
- In Kubernetes, resource limits per pod are a form of bulkhead.
- Combine with circuit breaker: bulkhead limits *concurrency*, circuit breaker
  limits *error rate*.

---

## 9. Saga Pattern

### Problem Statement

In a microservices architecture, a business transaction spans multiple services (e.g.,
payment → inventory → shipping). You can't use a single database transaction. If the
payment succeeds but inventory fails, you need to **undo** the payment. Traditional
2-phase commit is fragile and slow.

### Solution Overview

A **Saga** is a sequence of local transactions where each step has a **compensating
action** that undoes its effect. Two coordination styles:

| Style | How It Works |
|-------|-------------|
| **Choreography** | Each service emits an event; the next service reacts. No central coordinator. |
| **Orchestration** | A central **orchestrator** tells each service what to do and handles failures. |

### Compensating Transactions

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


class SagaStepStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    COMPENSATED = auto()
    FAILED = auto()


@dataclass
class SagaStep:
    name: str
    action: Callable[..., Any]
    compensation: Callable[..., Any]
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
```

### Orchestration-Based Saga

```python
class SagaOrchestrator:
    """Executes a sequence of steps; compensates on failure."""

    def __init__(self, saga_id: str | None = None) -> None:
        self.saga_id = saga_id or str(uuid4())
        self._steps: List[SagaStep] = []
        self._executed: List[SagaStep] = []

    def add_step(
        self,
        name: str,
        action: Callable[..., Any],
        compensation: Callable[..., Any],
    ) -> "SagaOrchestrator":
        self._steps.append(SagaStep(name=name, action=action, compensation=compensation))
        return self

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[saga:{self.saga_id}] Starting saga")

        for step in self._steps:
            try:
                print(f"  [saga] Executing step: {step.name}")
                step.result = step.action(context)
                step.status = SagaStepStatus.COMPLETED
                self._executed.append(step)
                context[f"{step.name}_result"] = step.result
                print(f"  [saga] Step '{step.name}' completed: {step.result}")

            except Exception as e:
                step.status = SagaStepStatus.FAILED
                step.error = e
                print(f"  [saga] Step '{step.name}' FAILED: {e}")
                self._compensate(context)
                raise SagaFailedError(
                    f"Saga {self.saga_id} failed at step '{step.name}': {e}",
                    step_name=step.name,
                    original_error=e,
                    compensated_steps=[s.name for s in self._executed],
                ) from e

        print(f"[saga:{self.saga_id}] Saga completed successfully")
        return context

    def _compensate(self, context: Dict[str, Any]) -> None:
        print(f"  [saga] Compensating {len(self._executed)} completed steps...")
        for step in reversed(self._executed):
            try:
                print(f"  [saga] Compensating: {step.name}")
                step.compensation(context)
                step.status = SagaStepStatus.COMPENSATED
                print(f"  [saga] Compensation for '{step.name}' succeeded")
            except Exception as comp_error:
                print(
                    f"  [saga] CRITICAL: Compensation for '{step.name}' "
                    f"failed: {comp_error}"
                )
                # In production: log, alert, and add to a dead-letter queue
                # for manual intervention.


class SagaFailedError(Exception):
    def __init__(
        self,
        message: str,
        step_name: str,
        original_error: Exception,
        compensated_steps: List[str],
    ) -> None:
        super().__init__(message)
        self.step_name = step_name
        self.original_error = original_error
        self.compensated_steps = compensated_steps
```

### Choreography-Based Saga

```python
class SagaEventBus:
    """Event bus for choreography-based sagas."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, data: Dict[str, Any]) -> None:
        print(f"  [event-bus] Publishing: {event_name}")
        for handler in self._handlers.get(event_name, []):
            try:
                handler(data)
            except Exception as e:
                print(f"  [event-bus] Handler failed for {event_name}: {e}")
                failure_event = f"{event_name}_failed"
                for fail_handler in self._handlers.get(failure_event, []):
                    fail_handler({**data, "error": str(e)})


class PaymentService:
    """Listens for OrderCreated, processes payment, emits PaymentProcessed."""

    def __init__(self, bus: SagaEventBus) -> None:
        self._bus = bus
        self._payments: Dict[str, dict] = {}
        bus.subscribe("order_created", self.handle_order_created)
        bus.subscribe("inventory_reserved_failed", self.compensate)

    def handle_order_created(self, data: dict) -> None:
        order_id = data["order_id"]
        amount = data["amount"]
        print(f"  [payment] Charging ${amount} for order {order_id}")
        self._payments[order_id] = {"amount": amount, "status": "charged"}
        self._bus.publish("payment_processed", {
            "order_id": order_id,
            "payment_id": f"pay-{order_id}",
        })

    def compensate(self, data: dict) -> None:
        order_id = data["order_id"]
        if order_id in self._payments:
            print(f"  [payment] Refunding order {order_id}")
            self._payments[order_id]["status"] = "refunded"


class InventoryService:
    """Listens for PaymentProcessed, reserves stock, emits InventoryReserved."""

    def __init__(self, bus: SagaEventBus, stock: Dict[str, int]) -> None:
        self._bus = bus
        self._stock = stock
        self._reservations: Dict[str, List[dict]] = {}
        bus.subscribe("payment_processed", self.handle_payment_processed)
        bus.subscribe("shipping_arranged_failed", self.compensate)

    def handle_payment_processed(self, data: dict) -> None:
        order_id = data["order_id"]
        # In a real system, items would come from the original order context
        items = [{"sku": "WIDGET-A", "qty": 2}]
        for item in items:
            if self._stock.get(item["sku"], 0) < item["qty"]:
                raise ValueError(f"Insufficient stock for {item['sku']}")
            self._stock[item["sku"]] -= item["qty"]
        self._reservations[order_id] = items
        print(f"  [inventory] Reserved stock for order {order_id}")
        self._bus.publish("inventory_reserved", {"order_id": order_id})

    def compensate(self, data: dict) -> None:
        order_id = data["order_id"]
        if order_id in self._reservations:
            for item in self._reservations[order_id]:
                self._stock[item["sku"]] += item["qty"]
            print(f"  [inventory] Released reservation for order {order_id}")


class ShippingService:
    """Listens for InventoryReserved, arranges shipping."""

    def __init__(self, bus: SagaEventBus) -> None:
        self._bus = bus
        bus.subscribe("inventory_reserved", self.handle_inventory_reserved)

    def handle_inventory_reserved(self, data: dict) -> None:
        order_id = data["order_id"]
        tracking = f"TRACK-{order_id}"
        print(f"  [shipping] Arranged shipping for {order_id}: {tracking}")
        self._bus.publish("shipping_arranged", {
            "order_id": order_id,
            "tracking_number": tracking,
        })
```

### Real Example — Order Fulfillment Saga (Orchestration)

```python
class PaymentGateway:
    def __init__(self):
        self._charges: Dict[str, float] = {}

    def charge(self, context: dict) -> dict:
        order_id = context["order_id"]
        amount = context["amount"]
        if amount > 10000:
            raise ValueError("Amount exceeds limit")
        self._charges[order_id] = amount
        return {"payment_id": f"pay-{order_id}", "amount": amount}

    def refund(self, context: dict) -> None:
        order_id = context["order_id"]
        if order_id in self._charges:
            del self._charges[order_id]
            print(f"    Refunded order {order_id}")


class InventoryManager:
    def __init__(self, stock: Dict[str, int]):
        self._stock = stock
        self._reserved: Dict[str, List[dict]] = {}

    def reserve(self, context: dict) -> dict:
        order_id = context["order_id"]
        items = context["items"]
        for item in items:
            avail = self._stock.get(item["sku"], 0)
            if avail < item["qty"]:
                raise ValueError(
                    f"Insufficient stock for {item['sku']}: "
                    f"need {item['qty']}, have {avail}"
                )
        for item in items:
            self._stock[item["sku"]] -= item["qty"]
        self._reserved[order_id] = items
        return {"reserved": True}

    def release(self, context: dict) -> None:
        order_id = context["order_id"]
        for item in self._reserved.pop(order_id, []):
            self._stock[item["sku"]] += item["qty"]
        print(f"    Released inventory for order {order_id}")


class ShippingManager:
    def arrange(self, context: dict) -> dict:
        order_id = context["order_id"]
        return {"tracking": f"TRACK-{order_id}"}

    def cancel_shipment(self, context: dict) -> None:
        print(f"    Cancelled shipment for order {context['order_id']}")


def demo_saga():
    payment = PaymentGateway()
    inventory = InventoryManager(stock={"WIDGET-A": 10, "GADGET-B": 5})
    shipping = ShippingManager()

    # --- Happy path ---
    saga = SagaOrchestrator()
    saga.add_step("payment", payment.charge, payment.refund)
    saga.add_step("inventory", inventory.reserve, inventory.release)
    saga.add_step("shipping", shipping.arrange, shipping.cancel_shipment)

    context = {
        "order_id": "ORD-001",
        "amount": 149.99,
        "items": [{"sku": "WIDGET-A", "qty": 2}],
    }

    result = saga.execute(context)
    print(f"\nHappy path result: {result.get('shipping_result')}")

    # --- Failure path: insufficient stock ---
    print("\n--- Failure scenario ---")
    saga2 = SagaOrchestrator()
    saga2.add_step("payment", payment.charge, payment.refund)
    saga2.add_step("inventory", inventory.reserve, inventory.release)
    saga2.add_step("shipping", shipping.arrange, shipping.cancel_shipment)

    context2 = {
        "order_id": "ORD-002",
        "amount": 99.99,
        "items": [{"sku": "GADGET-B", "qty": 100}],  # more than available
    }

    try:
        saga2.execute(context2)
    except SagaFailedError as e:
        print(f"\nSaga failed: {e}")
        print(f"Compensated steps: {e.compensated_steps}")


demo_saga()
```

### Sequence Diagram — Orchestration (Happy Path)

```
Client        Orchestrator      Payment      Inventory     Shipping
  │               │                │             │             │
  │  execute()    │                │             │             │
  │──────────────▶│                │             │             │
  │               │  charge()      │             │             │
  │               │───────────────▶│             │             │
  │               │  payment_id    │             │             │
  │               │◀───────────────│             │             │
  │               │                │             │             │
  │               │  reserve()     │             │             │
  │               │───────────────────────────▶ │             │
  │               │  reserved      │             │             │
  │               │◀───────────────────────────  │             │
  │               │                │             │             │
  │               │  arrange()     │             │             │
  │               │──────────────────────────────────────────▶│
  │               │  tracking#     │             │             │
  │               │◀──────────────────────────────────────────│
  │  success      │                │             │             │
  │◀──────────────│                │             │             │
```

### Sequence Diagram — Orchestration (Failure + Compensation)

```
Client        Orchestrator      Payment      Inventory     Shipping
  │               │                │             │             │
  │  execute()    │                │             │             │
  │──────────────▶│                │             │             │
  │               │  charge()      │             │             │
  │               │───────────────▶│             │             │
  │               │  payment_id    │             │             │
  │               │◀───────────────│             │             │
  │               │                │             │             │
  │               │  reserve()     │             │             │
  │               │───────────────────────────▶ │             │
  │               │  ERROR!        │             │             │
  │               │◀───────────────────────────  │             │
  │               │                │             │             │
  │               │  === COMPENSATE ===          │             │
  │               │  refund()      │             │             │
  │               │───────────────▶│             │             │
  │               │  refunded      │             │             │
  │               │◀───────────────│             │             │
  │  SagaFailed   │                │             │             │
  │◀──────────────│                │             │             │
```

### Error Handling in Sagas

| Scenario | Strategy |
|----------|----------|
| Compensation fails | Log + dead-letter queue + manual intervention |
| Timeout in a step | Treat as failure, compensate all prior steps |
| Duplicate events (choreography) | Each handler must be **idempotent** |
| Partial failure detection | Use a saga log (saga_id + step_name + status) |

```python
class SagaLog:
    """Persistent log of saga step outcomes for recovery."""

    def __init__(self) -> None:
        self._log: List[dict] = []

    def record(self, saga_id: str, step: str, status: str, detail: Any = None) -> None:
        self._log.append({
            "saga_id": saga_id,
            "step": step,
            "status": status,
            "detail": detail,
            "timestamp": time.time(),
        })

    def get_saga(self, saga_id: str) -> List[dict]:
        return [e for e in self._log if e["saga_id"] == saga_id]

    def get_incomplete(self) -> List[str]:
        """Return saga IDs that started but never completed or failed."""
        started = set()
        finished = set()
        for entry in self._log:
            if entry["status"] == "started":
                started.add(entry["saga_id"])
            elif entry["status"] in ("completed", "failed"):
                finished.add(entry["saga_id"])
        return list(started - finished)
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Distributed transactions across multiple services | A single database can handle the transaction (just use ACID) |
| Long-running business processes (hours, days) | The consistency window must be zero (strong consistency required) |
| Each step can be compensated | Compensation is impossible or prohibitively expensive |

### Common Mistakes

1. **Forgetting compensations** — every forward step must have a reverse.
2. **Non-idempotent handlers** — duplicate events in choreography can double-charge.
3. **Ignoring compensation failures** — this needs alerts and manual recovery tooling.
4. **Choosing choreography for complex flows** — more than 4-5 steps becomes hard to
   trace. Use orchestration.

### Interview Tips

- Clearly distinguish choreography (event-driven, decentralised) from orchestration
  (central coordinator).
- Mention that sagas provide **eventual consistency**, not ACID isolation.
- The saga pattern is named after a 1987 paper by Garcia-Molina and Salem.
- In production, use a saga log / journal for crash recovery.

---

## 10. Jitter and Backoff Pattern

### Problem Statement

When many clients retry at the same time (e.g., after a service restart), they create
a **thundering herd** — a synchronized burst of requests that overwhelms the recovering
service and prevents it from recovering.

```
  Time ──────────────────────────────────────────▶

  Client A:  retry─────retry─────retry─────retry
  Client B:  retry─────retry─────retry─────retry   ← ALL at the same instant
  Client C:  retry─────retry─────retry─────retry
                  ▲         ▲         ▲
                  │         │         │
              thundering  thundering  thundering
                herd       herd       herd
```

### Solution Overview

**Backoff** increases the wait time between retries. **Jitter** randomises the wait
time so that clients don't all retry simultaneously.

### Mathematical Analysis of Backoff Strategies

Let `attempt` = the 1-indexed attempt number, `base` = base delay, `cap` = maximum
delay.

| Strategy | Formula | Spread | Collision Risk |
|----------|---------|--------|----------------|
| **Constant** | `delay = base` | None | Very high |
| **Linear** | `delay = base × attempt` | Low | High |
| **Exponential** | `delay = base × 2^(attempt−1)` | Medium | Medium |
| **Full Jitter** | `delay = random(0, base × 2^(attempt−1))` | High | Low |
| **Equal Jitter** | `half = base × 2^(attempt−1) / 2; delay = half + random(0, half)` | Medium-High | Low |
| **Decorrelated** | `delay = random(base, prev_delay × 3)` | Very High | Very Low |

### Complete Python Implementation

```python
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Tuple, Type


class BackoffStrategy(Enum):
    CONSTANT = auto()
    LINEAR = auto()
    EXPONENTIAL = auto()
    FULL_JITTER = auto()
    EQUAL_JITTER = auto()
    DECORRELATED_JITTER = auto()


@dataclass
class BackoffConfig:
    strategy: BackoffStrategy = BackoffStrategy.FULL_JITTER
    base_delay: float = 1.0
    max_delay: float = 60.0
    max_attempts: int = 5
    exponential_base: float = 2.0


class BackoffCalculator:
    """Calculates delay for each attempt based on the chosen strategy."""

    def __init__(self, config: BackoffConfig) -> None:
        self._config = config
        self._prev_delay = config.base_delay

    def delay_for(self, attempt: int) -> float:
        cfg = self._config
        raw: float

        if cfg.strategy == BackoffStrategy.CONSTANT:
            raw = cfg.base_delay

        elif cfg.strategy == BackoffStrategy.LINEAR:
            raw = cfg.base_delay * attempt

        elif cfg.strategy == BackoffStrategy.EXPONENTIAL:
            raw = cfg.base_delay * (cfg.exponential_base ** (attempt - 1))

        elif cfg.strategy == BackoffStrategy.FULL_JITTER:
            exp = cfg.base_delay * (cfg.exponential_base ** (attempt - 1))
            raw = random.uniform(0, min(exp, cfg.max_delay))

        elif cfg.strategy == BackoffStrategy.EQUAL_JITTER:
            exp = cfg.base_delay * (cfg.exponential_base ** (attempt - 1))
            capped = min(exp, cfg.max_delay)
            half = capped / 2
            raw = half + random.uniform(0, half)

        elif cfg.strategy == BackoffStrategy.DECORRELATED_JITTER:
            raw = random.uniform(cfg.base_delay, self._prev_delay * 3)
            self._prev_delay = raw

        else:
            raise ValueError(f"Unknown strategy: {cfg.strategy}")

        return min(raw, cfg.max_delay)


def retry_with_jitter(
    strategy: BackoffStrategy = BackoffStrategy.FULL_JITTER,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator: retry with the specified backoff + jitter strategy."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = BackoffConfig(
                strategy=strategy,
                base_delay=base_delay,
                max_delay=max_delay,
                max_attempts=max_attempts,
            )
            calculator = BackoffCalculator(config)
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    delay = calculator.delay_for(attempt)
                    print(
                        f"  [jitter-retry] attempt {attempt}/{max_attempts} "
                        f"failed ({e}). Strategy={strategy.name}, "
                        f"delay={delay:.3f}s"
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
```

### Visualising the Strategies

```python
def visualise_strategies(attempts: int = 8) -> None:
    """Print a table comparing delay values for each strategy."""
    strategies = list(BackoffStrategy)
    config_base = BackoffConfig(base_delay=1.0, max_delay=60.0)

    print(f"{'Attempt':<8}", end="")
    for s in strategies:
        print(f"{s.name:<22}", end="")
    print()
    print("-" * (8 + 22 * len(strategies)))

    for attempt in range(1, attempts + 1):
        print(f"{attempt:<8}", end="")
        for s in strategies:
            cfg = BackoffConfig(
                strategy=s,
                base_delay=config_base.base_delay,
                max_delay=config_base.max_delay,
            )
            calc = BackoffCalculator(cfg)
            delay = calc.delay_for(attempt)
            print(f"{delay:<22.3f}", end="")
        print()


visualise_strategies()
```

Sample output (random values will vary):

```
Attempt CONSTANT              LINEAR                EXPONENTIAL           FULL_JITTER           EQUAL_JITTER          DECORRELATED_JITTER
------------------------------------------------------------------------------------------------------------
1       1.000                 1.000                 1.000                 0.347                 0.712                 1.872
2       1.000                 2.000                 2.000                 1.218                 1.349                 3.564
3       1.000                 3.000                 4.000                 2.917                 2.841                 7.231
4       1.000                 4.000                 8.000                 5.662                 5.221                 14.822
5       1.000                 5.000                 16.000                9.143                 10.331                28.419
6       1.000                 6.000                 32.000                18.774                20.889                51.738
7       1.000                 7.000                 60.000                42.315                37.218                60.000
8       1.000                 8.000                 60.000                31.628                41.555                60.000
```

### Real Example — Rate-Limited API Client

```python
class RateLimitedAPIClient:
    """Client for a third-party API that enforces rate limits (HTTP 429)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        strategy: BackoffStrategy = BackoffStrategy.FULL_JITTER,
        max_retries: int = 6,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._max_retries = max_retries
        self._config = BackoffConfig(
            strategy=strategy,
            base_delay=1.0,
            max_delay=120.0,
            max_attempts=max_retries,
        )

    def get(self, endpoint: str) -> dict:
        url = f"{self._base_url}/{endpoint}"
        calculator = BackoffCalculator(self._config)

        for attempt in range(1, self._max_retries + 1):
            try:
                return self._do_request("GET", url)
            except RateLimitError as e:
                if attempt == self._max_retries:
                    raise
                delay = self._choose_delay(e, calculator, attempt)
                print(
                    f"  [api] Rate limited (attempt {attempt}). "
                    f"Waiting {delay:.1f}s..."
                )
                time.sleep(delay)
            except TransientError:
                if attempt == self._max_retries:
                    raise
                delay = calculator.delay_for(attempt)
                time.sleep(delay)

        raise RuntimeError("Unreachable")

    def _do_request(self, method: str, url: str) -> dict:
        """Simulates an HTTP request that may be rate-limited."""
        import random
        roll = random.random()
        if roll < 0.4:
            raise RateLimitError(retry_after=2.0)
        if roll < 0.5:
            raise TransientError("Connection reset")
        return {"data": "ok", "url": url}

    def _choose_delay(
        self,
        error: RateLimitError,
        calculator: BackoffCalculator,
        attempt: int,
    ) -> float:
        if error.retry_after is not None:
            jittered = error.retry_after + random.uniform(0, 1)
            return jittered
        return calculator.delay_for(attempt)


class RateLimitError(Exception):
    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited (retry_after={retry_after})")


class TransientError(Exception):
    pass


def demo_jitter():
    client = RateLimitedAPIClient(
        base_url="https://api.example.com",
        api_key="key-123",
        strategy=BackoffStrategy.DECORRELATED_JITTER,
    )
    try:
        result = client.get("users/42")
        print(f"  Result: {result}")
    except (RateLimitError, TransientError) as e:
        print(f"  Final failure: {e}")


demo_jitter()
```

### Choosing the Right Strategy

```
                         Low traffic          High traffic
                     ┌─────────────────┐  ┌─────────────────┐
  Few clients        │   Exponential   │  │   Full Jitter   │
  (< 10 concurrent)  │   (simple)      │  │   (safe)        │
                     └─────────────────┘  └─────────────────┘
                     ┌─────────────────┐  ┌─────────────────┐
  Many clients       │   Equal Jitter  │  │  Decorrelated   │
  (100+ concurrent)  │   (balanced)    │  │  Jitter (best)  │
                     └─────────────────┘  └─────────────────┘
```

| Strategy | Best For |
|----------|----------|
| Constant | Internal retries with guaranteed low contention |
| Linear | Predictable workloads where you know recovery takes N seconds |
| Exponential | Default starting point when you're unsure |
| Full Jitter | Most situations — best studied, AWS recommendation |
| Equal Jitter | When you want a guaranteed *minimum* wait but still need spread |
| Decorrelated Jitter | High-contention, many-client scenarios — best spread |

### Sequence Diagram

```
Client-A      Client-B      Client-C        Server
   │             │             │               │
   │  request    │             │               │
   │─────────────────────────────────────────▶│
   │             │  request    │               │
   │             │────────────────────────────▶│
   │             │             │  request      │
   │             │             │──────────────▶│
   │  429        │  429        │  429          │
   │◀─────────────────────────────────────────│
   │             │◀────────────────────────────│
   │             │             │◀──────────────│
   │             │             │               │
   │ sleep(1.3s) │             │               │
   │             │ sleep(3.7s) │               │
   │             │             │ sleep(0.8s)   │
   │             │             │               │
   │             │             │  retry        │   ← spread out!
   │             │             │──────────────▶│
   │  retry      │             │  200 OK       │
   │─────────────────────────────────────────▶│◀──────────────│
   │  200 OK     │             │               │
   │◀─────────────────────────────────────────│
   │             │  retry      │               │
   │             │────────────────────────────▶│
   │             │  200 OK     │               │
   │             │◀────────────────────────────│
```

### When to Use / When to Avoid

| Use When | Avoid When |
|----------|------------|
| Many clients retry against the same endpoint | Single-client scenarios (jitter adds no benefit) |
| The server has rate limits or limited capacity | Real-time systems where any delay is unacceptable |
| You want to be a good citizen in a shared ecosystem | The failure is permanent — no amount of waiting will help |

### Common Mistakes

1. **Exponential backoff without jitter** — correlated retries still cause herds.
2. **Forgetting `max_delay`** — exponential growth quickly reaches absurd values
   (2^20 = 1,048,576 seconds ≈ 12 days).
3. **Using `random.random()` instead of `random.uniform()`** — semantically fine,
   but `uniform` makes the range explicit.
4. **Not respecting `Retry-After`** — when the server tells you when to retry, listen.
5. **Jitter range too narrow** — `random.uniform(0.9 * delay, 1.1 * delay)` barely
   helps.

### Interview Tips

- Reference the [AWS Architecture Blog post](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
  on exponential backoff and jitter.
- Full jitter is the AWS recommendation for most cases.
- Decorrelated jitter has the best theoretical spread but is less intuitive.
- Always combine with a retry budget to prevent system-wide overload.

---

## Appendix: Pattern Comparison Matrix

| Pattern | Category | Complexity | When to Reach For It |
|---------|----------|------------|---------------------|
| Registry | Structural | Low | Plugin systems, extensible frameworks |
| Dependency Injection | Structural | Low–Medium | Any app that needs testability |
| Service Locator | Structural | Low | Legacy code migration |
| Event Sourcing | Data | High | Audit trails, temporal queries, finance |
| CQRS | Architectural | Medium–High | Complex domains with divergent read/write needs |
| Retry | Resilience | Low | Any distributed call |
| Circuit Breaker | Resilience | Medium | Protecting against failing downstream services |
| Bulkhead | Resilience | Medium | Microservice gateways, shared resource pools |
| Saga | Distributed Tx | High | Multi-service business transactions |
| Jitter & Backoff | Resilience | Low | High-concurrency retry scenarios |

### Combining Patterns — A Resilient Microservice Call

```python
class ResilientClient:
    """Demonstrates combining multiple resilience patterns."""

    def __init__(self, service_name: str) -> None:
        self._bulkhead = SemaphoreBulkhead(service_name, max_concurrent=10)
        self._circuit = CircuitBreaker(
            failure_threshold=5,
            timeout=30.0,
            name=service_name,
        )
        self._backoff_config = BackoffConfig(
            strategy=BackoffStrategy.FULL_JITTER,
            base_delay=0.5,
            max_delay=30.0,
            max_attempts=3,
        )

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execution order:
          1. Bulkhead — limits concurrency
          2. Circuit Breaker — fast-fails if downstream is known-bad
          3. Retry with jitter — handles transient failures
        """
        return self._bulkhead.execute(
            self._circuit.call,
            self._retry_wrapper(func),
            *args,
            **kwargs,
        )

    def _retry_wrapper(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            calculator = BackoffCalculator(self._backoff_config)
            last_err = None
            for attempt in range(1, self._backoff_config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < self._backoff_config.max_attempts:
                        delay = calculator.delay_for(attempt)
                        time.sleep(delay)
            raise last_err  # type: ignore[misc]
        return wrapper
```

### Execution Flow

```
Request
   │
   ▼
┌──────────────┐   full?   ┌──────────┐
│   Bulkhead   │──────────▶│  Reject  │
└──────┬───────┘           └──────────┘
       │ permit
       ▼
┌──────────────┐   open?   ┌──────────┐
│   Circuit    │──────────▶│Fast-Fail │
│   Breaker    │           └──────────┘
└──────┬───────┘
       │ closed/half-open
       ▼
┌──────────────┐  success  ┌──────────┐
│  Retry with  │──────────▶│  Return  │
│  Jitter      │           │  Result  │
└──────┬───────┘           └──────────┘
       │ all attempts failed
       ▼
┌──────────────┐
│  Raise Error │
│  (CB records │
│   failure)   │
└──────────────┘
```

---

## Final Interview Cheat Sheet

| Question | Key Points |
|----------|-----------|
| "What is a registry?" | Named factory with dynamic registration via decorators. Mention `__init_subclass__`. |
| "Explain DI" | Constructor injection preferred. Protocols for interfaces. Show a DIContainer. |
| "DI vs Service Locator?" | DI pushes deps in (explicit). SL pulls deps out (hidden). DI preferred. |
| "What is event sourcing?" | Append-only event log → replay → current state. Snapshots for speed. |
| "When to use CQRS?" | When read and write models have very different shapes or scaling needs. |
| "How do you handle retries?" | Exponential backoff + jitter + idempotency + retry budget. |
| "Explain circuit breaker" | Three states: Closed → Open → Half-Open. Prevents cascading failure. |
| "What is a bulkhead?" | Isolates resource pools. Semaphore or thread-pool based. |
| "Saga pattern?" | Sequence of local transactions with compensations. Orchestration vs choreography. |
| "Thundering herd solution?" | Jitter. Full jitter (AWS recommendation) or decorrelated jitter. |

---

*End of Architectural Patterns Guide — approximately 2,700 lines of content covering
10 patterns with complete Python implementations, sequence diagrams, and interview
preparation material.*
