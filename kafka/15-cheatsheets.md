# Quick Reference Cheatsheets

> Five scannable cheatsheets covering everything you need for a last-minute review before an LLD interview or a quick refresher during development.

---

## Table of Contents

1. [Python Design Patterns Cheatsheet](#1-python-design-patterns-cheatsheet)
2. [AsyncIO Cheatsheet](#2-asyncio-cheatsheet)
3. [Concurrency Cheatsheet](#3-concurrency-cheatsheet)
4. [FastAPI Cheatsheet](#4-fastapi-cheatsheet)
5. [Machine Coding Cheatsheet](#5-machine-coding-cheatsheet)

---

## 1. Python Design Patterns Cheatsheet

### All 23 GoF Patterns at a Glance

#### Creational Patterns

| Pattern | Intent | Python Idiom | When to Use |
|---------|--------|-------------|-------------|
| **Singleton** | Ensure one instance globally | Module-level variable or `__new__` | Config, DB connection pool, logger |
| **Factory Method** | Defer instantiation to subclasses | `@classmethod` or standalone function | Object creation varies by input type |
| **Abstract Factory** | Create families of related objects | ABC with factory methods | Supporting multiple themes/backends |
| **Builder** | Construct complex objects step-by-step | Method chaining or `@dataclass` | Objects with many optional parameters |
| **Prototype** | Clone existing objects | `copy.deepcopy()` | Expensive-to-create objects with variants |

#### Structural Patterns

| Pattern | Intent | Python Idiom | When to Use |
|---------|--------|-------------|-------------|
| **Adapter** | Convert interface to another | Wrapper class or function | Integrating third-party libraries |
| **Bridge** | Separate abstraction from implementation | Composition over inheritance | Multiple dimensions of variation |
| **Composite** | Tree structure of uniform objects | Recursive class with children list | File systems, org charts, menus |
| **Decorator** | Add behavior dynamically | `@functools.wraps` / wrapper classes | Logging, caching, auth, retry |
| **Facade** | Simplified interface to subsystem | Single class wrapping multiple | Complex library with simple use case |
| **Flyweight** | Share state across many objects | `__slots__`, interning, caching | Millions of similar objects (game sprites) |
| **Proxy** | Control access to an object | `__getattr__` delegation | Lazy loading, access control, caching |

#### Behavioral Patterns

| Pattern | Intent | Python Idiom | When to Use |
|---------|--------|-------------|-------------|
| **Chain of Responsibility** | Pass request through handler chain | List of callables / linked handlers | Middleware, validation pipelines |
| **Command** | Encapsulate request as object | Callable class with `execute()` | Undo/redo, task queues, macros |
| **Interpreter** | Define grammar and interpreter | AST + recursive evaluation | DSLs, rule engines, query parsers |
| **Iterator** | Sequential access without exposing internals | `__iter__` / `__next__` / generators | Custom collections, lazy sequences |
| **Mediator** | Centralize complex communication | Central coordinator class | Chat rooms, event buses, form validation |
| **Memento** | Capture and restore state | Snapshot dict / `dataclass` copy | Undo, save/load, checkpointing |
| **Observer** | Notify dependents of state changes | Callback lists / `signal` libraries | Event systems, pub/sub, UI updates |
| **State** | Change behavior based on state | State classes with common interface | Vending machines, workflows, TCP states |
| **Strategy** | Swap algorithms at runtime | First-class functions or protocol classes | Sorting, pricing rules, auth methods |
| **Template Method** | Define algorithm skeleton, defer steps | ABC with concrete + abstract methods | Frameworks, ETL pipelines, test fixtures |
| **Visitor** | Add operations without modifying classes | Double dispatch with `accept()` / `visit()` | AST traversal, report generation |

### Quick Code Snippets

#### Singleton

```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Pythonic alternative: just use a module
# config.py
settings = {"debug": False, "db_url": "..."}  # Module IS the singleton
```

#### Factory Method

```python
from abc import ABC, abstractmethod

class Notification(ABC):
    @abstractmethod
    def send(self, message: str): ...

class EmailNotification(Notification):
    def send(self, message): print(f"Email: {message}")

class SMSNotification(Notification):
    def send(self, message): print(f"SMS: {message}")

def create_notification(channel: str) -> Notification:
    factories = {"email": EmailNotification, "sms": SMSNotification}
    return factories[channel]()
```

#### Abstract Factory

```python
from abc import ABC, abstractmethod

class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> "Button": ...
    @abstractmethod
    def create_checkbox(self) -> "Checkbox": ...

class DarkThemeFactory(UIFactory):
    def create_button(self): return DarkButton()
    def create_checkbox(self): return DarkCheckbox()

class LightThemeFactory(UIFactory):
    def create_button(self): return LightButton()
    def create_checkbox(self): return LightCheckbox()
```

#### Builder

```python
from dataclasses import dataclass, field

@dataclass
class QueryBuilder:
    _table: str = ""
    _conditions: list[str] = field(default_factory=list)
    _order_by: str = ""
    _limit: int | None = None

    def table(self, name):     self._table = name; return self
    def where(self, cond):     self._conditions.append(cond); return self
    def order(self, col):      self._order_by = col; return self
    def limit(self, n):        self._limit = n; return self

    def build(self) -> str:
        q = f"SELECT * FROM {self._table}"
        if self._conditions:   q += " WHERE " + " AND ".join(self._conditions)
        if self._order_by:     q += f" ORDER BY {self._order_by}"
        if self._limit:        q += f" LIMIT {self._limit}"
        return q

query = QueryBuilder().table("users").where("age > 18").order("name").limit(10).build()
```

#### Prototype

```python
import copy

class GameUnit:
    def __init__(self, name, hp, attack, abilities):
        self.name = name
        self.hp = hp
        self.attack = attack
        self.abilities = abilities  # Deep copy needed for mutable fields

    def clone(self):
        return copy.deepcopy(self)

base_warrior = GameUnit("Warrior", 100, 15, ["slash", "block"])
elite_warrior = base_warrior.clone()
elite_warrior.name = "Elite Warrior"
elite_warrior.hp = 200
```

#### Adapter

```python
class OldPaymentGateway:
    def make_payment(self, amount_cents: int): ...

class NewPaymentInterface:
    def pay(self, amount_dollars: float): ...

class PaymentAdapter(NewPaymentInterface):
    def __init__(self, old_gateway: OldPaymentGateway):
        self._gateway = old_gateway

    def pay(self, amount_dollars: float):
        cents = int(amount_dollars * 100)
        return self._gateway.make_payment(cents)
```

#### Decorator (Pythonic)

```python
import functools
import time

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

@retry(max_attempts=3, delay=0.5)
def fetch_data(url): ...
```

#### Observer

```python
from collections import defaultdict
from typing import Callable

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable):
        self._subscribers[event].append(callback)

    def publish(self, event: str, data=None):
        for callback in self._subscribers[event]:
            callback(data)

bus = EventBus()
bus.subscribe("order_placed", lambda order: print(f"New order: {order}"))
bus.publish("order_placed", {"id": 1, "total": 99.99})
```

#### Strategy

```python
from typing import Protocol

class PricingStrategy(Protocol):
    def calculate(self, base_price: float) -> float: ...

def regular_price(base_price: float) -> float:
    return base_price

def premium_discount(base_price: float) -> float:
    return base_price * 0.8

def seasonal_sale(base_price: float) -> float:
    return base_price * 0.7

class ShoppingCart:
    def __init__(self, pricing: PricingStrategy = regular_price):
        self.pricing = pricing
        self.items: list[float] = []

    def total(self) -> float:
        return sum(self.pricing(p) for p in self.items)
```

#### State

```python
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def handle(self, context: "Context"): ...

class IdleState(State):
    def handle(self, context):
        print("Starting...")
        context.state = ProcessingState()

class ProcessingState(State):
    def handle(self, context):
        print("Processing...")
        context.state = DoneState()

class DoneState(State):
    def handle(self, context):
        print("Already done")

class Context:
    def __init__(self):
        self.state: State = IdleState()

    def request(self):
        self.state.handle(self)
```

#### Command

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class InsertTextCommand(Command):
    def __init__(self, document, position, text):
        self.doc, self.pos, self.text = document, position, text

    def execute(self):
        self.doc.insert(self.pos, self.text)

    def undo(self):
        self.doc.delete(self.pos, len(self.text))

class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, cmd: Command):
        cmd.execute()
        self._history.append(cmd)

    def undo(self):
        if self._history:
            self._history.pop().undo()
```

#### Chain of Responsibility

```python
from abc import ABC, abstractmethod

class Handler(ABC):
    def __init__(self):
        self._next: Handler | None = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next = handler
        return handler

    def handle(self, request):
        if self._next:
            return self._next.handle(request)
        return None

class AuthHandler(Handler):
    def handle(self, request):
        if not request.get("token"):
            return {"error": "Unauthorized"}
        return super().handle(request)

class RateLimitHandler(Handler):
    def handle(self, request):
        if self.is_rate_limited(request):
            return {"error": "Rate limited"}
        return super().handle(request)

# Chain: Auth → RateLimit → Handler
auth = AuthHandler()
auth.set_next(RateLimitHandler())
```

#### Composite

```python
from abc import ABC, abstractmethod

class FileSystemItem(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def size(self) -> int: ...

class File(FileSystemItem):
    def __init__(self, name, size):
        super().__init__(name)
        self._size = size

    def size(self) -> int:
        return self._size

class Directory(FileSystemItem):
    def __init__(self, name):
        super().__init__(name)
        self.children: list[FileSystemItem] = []

    def add(self, item: FileSystemItem):
        self.children.append(item)

    def size(self) -> int:
        return sum(child.size() for child in self.children)
```

#### Template Method

```python
from abc import ABC, abstractmethod

class DataPipeline(ABC):
    def run(self):              # Template method — fixed sequence
        data = self.extract()
        transformed = self.transform(data)
        self.load(transformed)

    @abstractmethod
    def extract(self): ...
    @abstractmethod
    def transform(self, data): ...
    @abstractmethod
    def load(self, data): ...

class CSVToDBPipeline(DataPipeline):
    def extract(self):        return read_csv("data.csv")
    def transform(self, data): return [clean(row) for row in data]
    def load(self, data):     db.bulk_insert(data)
```

#### Mediator

```python
class ChatRoom:
    def __init__(self):
        self._users: dict[str, "User"] = {}

    def register(self, user: "User"):
        self._users[user.name] = user
        user.room = self

    def send(self, message: str, sender: "User", recipient: str = None):
        if recipient:
            self._users[recipient].receive(message, sender.name)
        else:
            for name, user in self._users.items():
                if name != sender.name:
                    user.receive(message, sender.name)

class User:
    def __init__(self, name: str):
        self.name = name
        self.room: ChatRoom | None = None

    def send(self, message, to=None):
        self.room.send(message, self, to)

    def receive(self, message, sender):
        print(f"[{self.name}] from {sender}: {message}")
```

### Pattern Decision Tree

```
What problem are you solving?
│
├── Creating objects?
│   ├── One global instance? ──────────── Singleton
│   ├── Vary type by input? ───────────── Factory Method
│   ├── Families of related objects? ──── Abstract Factory
│   ├── Complex construction? ─────────── Builder
│   └── Cloning existing objects? ──────── Prototype
│
├── Structuring classes?
│   ├── Incompatible interface? ────────── Adapter
│   ├── Two dimensions of variation? ──── Bridge
│   ├── Tree / hierarchy? ─────────────── Composite
│   ├── Add behavior dynamically? ──────── Decorator
│   ├── Simplify complex subsystem? ───── Facade
│   ├── Too many similar objects? ──────── Flyweight
│   └── Control access? ───────────────── Proxy
│
└── Managing behavior?
    ├── Pipeline of handlers? ──────────── Chain of Responsibility
    ├── Encapsulate action + undo? ─────── Command
    ├── Custom language/rules? ─────────── Interpreter
    ├── Traverse without exposing internals? ── Iterator
    ├── Centralize communication? ──────── Mediator
    ├── Save/restore state? ────────────── Memento
    ├── Notify on state change? ────────── Observer
    ├── Behavior changes with state? ───── State
    ├── Swap algorithms? ──────────────── Strategy
    ├── Fixed algorithm, varying steps? ── Template Method
    └── Operations on object structure? ── Visitor
```

---

## 2. AsyncIO Cheatsheet

### Core Primitives

| Primitive | What It Does | Key Points |
|-----------|-------------|------------|
| `async def` | Define a coroutine | Returns coroutine object; must be awaited |
| `await` | Suspend until result ready | Only inside `async def` |
| `asyncio.run()` | Entry point for async code | Creates event loop, runs coroutine, closes loop |
| `asyncio.create_task()` | Schedule coroutine concurrently | Returns `Task` object (a `Future` subclass) |
| `asyncio.gather()` | Run multiple coroutines concurrently | Returns list of results in same order |
| `asyncio.wait()` | Wait for tasks with conditions | `FIRST_COMPLETED`, `FIRST_EXCEPTION`, `ALL_COMPLETED` |
| `asyncio.sleep()` | Non-blocking sleep | Yields control to event loop |
| `asyncio.to_thread()` | Run sync func in thread | For blocking I/O in async code (3.9+) |
| `asyncio.wait_for()` | Add timeout to coroutine | Raises `TimeoutError` on expiry |
| `asyncio.shield()` | Protect from cancellation | Inner coroutine continues even if outer is cancelled |
| `asyncio.timeout()` | Context manager timeout | 3.11+; cleaner than `wait_for` |

### Running Async Code

```python
import asyncio

# Entry point
async def main():
    result = await some_coroutine()
    return result

asyncio.run(main())

# Running from sync code (e.g., in a thread)
loop = asyncio.new_event_loop()
result = loop.run_until_complete(main())
loop.close()
```

### Task Creation and Management

```python
async def main():
    # Create tasks (schedules them immediately)
    task1 = asyncio.create_task(fetch("url1"), name="fetch_url1")
    task2 = asyncio.create_task(fetch("url2"), name="fetch_url2")

    # Await results
    result1 = await task1
    result2 = await task2

    # Or gather for bulk concurrency
    results = await asyncio.gather(
        fetch("url1"),
        fetch("url2"),
        fetch("url3"),
        return_exceptions=True,  # Don't fail on individual errors
    )

    # TaskGroup (3.11+) — structured concurrency
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch("url1"))
        t2 = tg.create_task(fetch("url2"))
    # All tasks guaranteed complete here
    print(t1.result(), t2.result())
```

### Common Async Patterns

#### Fan-out / Fan-in

```python
async def fan_out_fan_in(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

#### Semaphore-Limited Concurrency

```python
sem = asyncio.Semaphore(10)  # Max 10 concurrent

async def limited_fetch(url):
    async with sem:
        async with session.get(url) as resp:
            return await resp.json()

results = await asyncio.gather(*[limited_fetch(u) for u in urls])
```

#### Producer-Consumer with Queue

```python
async def producer(queue: asyncio.Queue):
    for item in range(100):
        await queue.put(item)
    await queue.put(None)  # Sentinel

async def consumer(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process(item)
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=10)  # Bounded = backpressure
    await asyncio.gather(
        producer(queue),
        consumer(queue),
        consumer(queue),  # Multiple consumers
    )
```

#### Timeout Patterns

```python
# wait_for — raises TimeoutError
try:
    result = await asyncio.wait_for(slow_operation(), timeout=5.0)
except asyncio.TimeoutError:
    print("Operation timed out")

# timeout context manager (3.11+)
async with asyncio.timeout(5.0):
    result = await slow_operation()

# timeout with fallback
async def with_fallback(coro, timeout, fallback):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return fallback
```

#### Wait for First Result

```python
# Return first successful result, cancel the rest
async def first_success(*coros):
    tasks = [asyncio.create_task(c) for c in coros]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    return done.pop().result()

result = await first_success(
    fetch_from_cache(key),
    fetch_from_db(key),
    fetch_from_api(key),
)
```

### Error Handling Patterns

```python
# gather with return_exceptions
results = await asyncio.gather(*tasks, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        handle_error(r)
    else:
        process_result(r)

# TaskGroup — cancels all on first exception (3.11+)
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(risky_operation_1())
        tg.create_task(risky_operation_2())
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"ValueError: {exc}")
except* TypeError as eg:
    for exc in eg.exceptions:
        print(f"TypeError: {exc}")
```

### Cancellation Patterns

```python
# Cancel a single task
task = asyncio.create_task(long_running())
task.cancel()
try:
    await task
except asyncio.CancelledError:
    print("Task was cancelled")

# Graceful cancellation with cleanup
async def cancellable_worker():
    try:
        while True:
            await do_work()
    except asyncio.CancelledError:
        await cleanup()  # Save state, close connections
        raise             # Re-raise to propagate cancellation

# Shield from cancellation
async def important_save(data):
    await asyncio.shield(db.save(data))  # Continues even if caller is cancelled
```

### Synchronization Primitives

| Primitive | Usage | Example |
|-----------|-------|---------|
| `asyncio.Lock` | Mutual exclusion | Protect shared resource |
| `asyncio.Event` | Signal between coroutines | Notify when ready |
| `asyncio.Condition` | Wait for condition | Complex coordination |
| `asyncio.Semaphore` | Limit concurrency | Rate limiting |
| `asyncio.BoundedSemaphore` | Semaphore with overflow check | Strict limiting |
| `asyncio.Queue` | Async producer-consumer | Work distribution |
| `asyncio.Barrier` | Wait for N coroutines (3.11+) | Synchronized start |

```python
# Lock
lock = asyncio.Lock()
async with lock:
    await modify_shared_state()

# Event
event = asyncio.Event()
# Waiter:
await event.wait()
# Setter:
event.set()

# Semaphore
sem = asyncio.Semaphore(5)
async with sem:
    await limited_operation()

# Queue
queue = asyncio.Queue(maxsize=100)
await queue.put(item)
item = await queue.get()
queue.task_done()
await queue.join()  # Block until all items processed
```

### Common Gotchas

| Gotcha | Wrong | Right |
|--------|-------|-------|
| Forgetting to await | `result = coro()` | `result = await coro()` |
| Blocking the loop | `time.sleep(1)` | `await asyncio.sleep(1)` |
| Blocking I/O | `requests.get(url)` | `await session.get(url)` |
| Creating task but not awaiting | `asyncio.create_task(f())` and forget | Store reference or use `TaskGroup` |
| Running sync in async | `def handler(): ...` in async app | `async def handler(): ...` |
| Sharing state without lock | Direct dict mutation from tasks | `async with lock: dict[k] = v` |
| Fire-and-forget tasks | `create_task()` garbage collected | `background_tasks.add(task)` |
| CPU-bound in async | `await compute_heavy()` | `await loop.run_in_executor(pool, func)` |
| Nested `asyncio.run()` | `asyncio.run()` inside async | Use `await` or `create_task()` |

### Quick Reference Table

```
asyncio.run(coro)                    → Run entry point
asyncio.create_task(coro)            → Schedule concurrent task
asyncio.gather(*coros)               → Run all, collect results
asyncio.wait(tasks, return_when=...) → Fine-grained waiting
asyncio.wait_for(coro, timeout)      → Timeout wrapper
asyncio.sleep(seconds)               → Non-blocking sleep
asyncio.to_thread(func, *args)       → Run sync in thread
asyncio.shield(coro)                 → Protect from cancel
asyncio.timeout(seconds)             → Context manager timeout (3.11+)
asyncio.TaskGroup()                  → Structured concurrency (3.11+)
asyncio.Queue(maxsize)               → Async queue
asyncio.Lock()                       → Async mutex
asyncio.Semaphore(n)                 → Limit concurrency
asyncio.Event()                      → Signal between tasks
```

---

## 3. Concurrency Cheatsheet

### Threading vs Multiprocessing vs AsyncIO

| Feature | `threading` | `multiprocessing` | `asyncio` |
|---------|-------------|-------------------|-----------|
| **Concurrency type** | OS threads | OS processes | Coroutines (single thread) |
| **GIL impact** | Blocked (CPU-bound limited) | Bypassed (separate processes) | N/A (single thread) |
| **Best for** | I/O-bound (moderate scale) | CPU-bound | I/O-bound (high scale) |
| **Memory overhead** | ~100 KB/thread | ~30 MB/process | ~1 KB/coroutine |
| **Max practical units** | 100–500 | CPU count (4–32) | 10,000–100,000+ |
| **Shared state** | Shared (need locks) | Isolated (need IPC) | Shared (need async locks) |
| **Debugging** | Hard (race conditions) | Moderate (isolation) | Moderate (stack traces) |
| **Communication** | `queue.Queue`, shared vars | `mp.Queue`, `Pipe`, `Manager` | `asyncio.Queue` |
| **Startup cost** | Low (~1ms) | High (~50–100ms) | Very low (~0.01ms) |
| **Context switch** | ~5–15 µs | ~50–100 µs | ~0.1–0.5 µs |

### When to Use What

```
┌─────────────────────────────────────────────────────┐
│              What type of work?                     │
├─────────────────────┬───────────────────────────────┤
│   CPU-bound         │        I/O-bound              │
│                     │                               │
│   multiprocessing   │   How many concurrent?        │
│   ProcessPool       │   ┌───────────┬───────────┐   │
│   Executor          │   │ < 100     │ > 100     │   │
│                     │   │           │           │   │
│                     │   │ threading │ asyncio   │   │
│                     │   │ ThreadPool│           │   │
│                     │   │ Executor  │           │   │
│                     │   └───────────┴───────────┘   │
└─────────────────────┴───────────────────────────────┘
```

### All Synchronization Primitives

#### threading Module

| Primitive | Purpose | Key Methods |
|-----------|---------|-------------|
| `Lock` | Mutual exclusion | `acquire()`, `release()`, context manager |
| `RLock` | Reentrant lock (same thread can re-acquire) | Same as Lock |
| `Semaphore` | Allow N concurrent accesses | `acquire()`, `release()` |
| `BoundedSemaphore` | Semaphore that errors on too many releases | Same as Semaphore |
| `Event` | Signal between threads | `set()`, `clear()`, `wait()`, `is_set()` |
| `Condition` | Wait until notified + condition is true | `wait()`, `notify()`, `notify_all()` |
| `Barrier` | Wait until N threads arrive | `wait()`, `parties`, `n_waiting` |
| `Timer` | Delayed execution | `start()`, `cancel()` |

#### Quick Usage Examples

```python
import threading

# Lock — protect shared resource
lock = threading.Lock()
with lock:
    shared_counter += 1

# RLock — reentrant (for recursive functions)
rlock = threading.RLock()
def recursive_func(n):
    with rlock:
        if n > 0:
            recursive_func(n - 1)

# Semaphore — limit concurrent access
pool_sem = threading.Semaphore(5)
with pool_sem:
    use_limited_resource()

# Event — signal between threads
ready = threading.Event()
# Thread A:
ready.wait()       # Blocks until set
# Thread B:
ready.set()        # Unblocks all waiters

# Condition — wait for specific condition
cond = threading.Condition()
with cond:
    cond.wait_for(lambda: len(buffer) > 0)  # Wait until buffer has items
    item = buffer.pop()

with cond:
    buffer.append(item)
    cond.notify()   # Wake one waiter

# Barrier — synchronize N threads
barrier = threading.Barrier(3)
def worker():
    setup()
    barrier.wait()  # All 3 threads must reach here before any proceed
    do_work()
```

### Thread Safety Checklist

- [ ] All shared mutable state protected by Lock or other primitive
- [ ] No lock held while doing I/O (prevents other threads from progressing)
- [ ] Locks acquired in consistent order across all threads (prevents deadlock)
- [ ] Using `threading.local()` for thread-specific data
- [ ] Queue used for inter-thread communication (inherently thread-safe)
- [ ] Using `concurrent.futures` instead of raw threads when possible
- [ ] Immutable data preferred over shared mutable data
- [ ] No daemon threads doing important work (killed on main thread exit)
- [ ] Context managers used for lock acquisition (prevents forgetting release)
- [ ] Timeouts set on `lock.acquire(timeout=5)` (prevents infinite deadlocks)

### Deadlock Prevention Rules

| Rule | Description | Example |
|------|-------------|---------|
| **Lock ordering** | Always acquire locks in the same global order | Lock A before Lock B, everywhere |
| **Timeout** | Use `acquire(timeout=N)` | `if not lock.acquire(timeout=5): handle_failure()` |
| **Try-lock** | Non-blocking attempt | `if lock.acquire(blocking=False): ...` |
| **Single lock** | Use one coarse lock instead of many fine | Simpler but lower concurrency |
| **Lock-free** | Use `queue.Queue` or `collections.deque` | Thread-safe without explicit locks |
| **Avoid nesting** | Don't hold lock A while acquiring lock B | Restructure to release A first |

### concurrent.futures Quick Reference

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# Thread pool (I/O-bound)
with ThreadPoolExecutor(max_workers=20) as executor:
    # Submit individual tasks
    future = executor.submit(fetch_url, "https://example.com")
    result = future.result(timeout=10)

    # Map over iterable
    results = list(executor.map(fetch_url, urls, timeout=30))

    # As completed — process results as they arrive
    futures = {executor.submit(fetch_url, url): url for url in urls}
    for future in as_completed(futures):
        url = futures[future]
        try:
            data = future.result()
        except Exception as exc:
            print(f"{url} failed: {exc}")

# Process pool (CPU-bound)
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(cpu_heavy_task, data_chunks))
```

### Performance Guidelines

| Scenario | Threads | Processes | Async |
|----------|---------|-----------|-------|
| 10 API calls | 0.5s (10 threads) | 1.5s (overhead) | 0.5s |
| 100 API calls | 1.2s (50 threads) | 2.0s (overhead) | 1.0s |
| 10,000 API calls | OOM risk | N/A | 3.0s |
| Image resize × 100 | 12s (GIL) | 3s (4 cores) | N/A |
| JSON parse × 10000 | 4s (GIL) | 1.2s (4 cores) | N/A |

### multiprocessing Quick Reference

```python
import multiprocessing as mp

# Process pool
with mp.Pool(processes=4) as pool:
    results = pool.map(func, iterable)            # Blocking map
    results = pool.starmap(func, [(a, b), (c, d)]) # Multiple args
    result = pool.apply_async(func, args)          # Non-blocking

# Shared state
counter = mp.Value('i', 0)        # Shared integer
array = mp.Array('d', [0.0] * 10) # Shared array
lock = mp.Lock()

with lock:
    counter.value += 1

# Communication
queue = mp.Queue()
queue.put(item)
item = queue.get()

parent_conn, child_conn = mp.Pipe()
parent_conn.send(data)
data = child_conn.recv()

# Manager (for complex shared objects)
manager = mp.Manager()
shared_dict = manager.dict()
shared_list = manager.list()
```

---

## 4. FastAPI Cheatsheet

### Route Decorators

```python
from fastapi import FastAPI, Query, Path, Body, Header, Cookie, Form, File, UploadFile

app = FastAPI()

# HTTP methods
@app.get("/items")
@app.post("/items")
@app.put("/items/{item_id}")
@app.patch("/items/{item_id}")
@app.delete("/items/{item_id}")
@app.options("/items")
@app.head("/items")

# Path parameters
@app.get("/users/{user_id}")
async def get_user(user_id: int):                           # Auto-validated as int
    ...

@app.get("/files/{file_path:path}")                          # Catch-all path
async def get_file(file_path: str):
    ...

# Query parameters
@app.get("/items")
async def list_items(
    skip: int = 0,                                           # Optional with default
    limit: int = Query(default=10, ge=1, le=100),            # Validated range
    q: str | None = Query(default=None, min_length=3),       # Optional string
    tags: list[str] = Query(default=[]),                      # Multiple values
):
    ...

# Request body (Pydantic model)
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    tags: list[str] = []

@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    ...

# Headers, Cookies, Forms, Files
@app.post("/login")
async def login(
    x_token: str = Header(...),
    session_id: str | None = Cookie(default=None),
    username: str = Form(...),
    password: str = Form(...),
):
    ...

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    ...
```

### Dependency Injection

```python
from fastapi import Depends, HTTPException, status

# Simple dependency
async def get_db():
    db = Database()
    try:
        yield db
    finally:
        await db.close()

# Dependency with sub-dependency
async def get_current_user(
    token: str = Header(..., alias="Authorization"),
    db = Depends(get_db),
):
    user = await db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# Dependency as route parameter
@app.get("/me")
async def read_me(user = Depends(get_current_user)):
    return user

# Class-based dependency
class Paginator:
    def __init__(self, skip: int = 0, limit: int = Query(default=20, le=100)):
        self.skip = skip
        self.limit = limit

@app.get("/items")
async def list_items(page: Paginator = Depends()):
    return db.query().offset(page.skip).limit(page.limit).all()

# Global dependencies (applied to all routes)
app = FastAPI(dependencies=[Depends(verify_api_key)])

# Router-level dependencies
router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_admin)],
)
```

### Request / Response Models

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

# Request model
class UserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Must contain uppercase letter")
        return v

# Response model (controls what's exposed)
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}  # Enable ORM mode

# Different response for different use cases
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    db_user = await db.create(user)
    return db_user  # Pydantic filters out password automatically

# Response with nested models
class OrderResponse(BaseModel):
    id: int
    items: list[ItemResponse]
    total: float

# Custom responses
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse

@app.get("/custom")
async def custom():
    return JSONResponse(
        content={"msg": "custom"},
        status_code=200,
        headers={"X-Custom": "value"},
    )
```

### Middleware

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Custom middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

app.add_middleware(TimingMiddleware)

# Pure ASGI middleware (more performant)
class ASGITimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start = time.perf_counter()

        async def send_with_timing(message):
            if message["type"] == "http.response.start":
                elapsed = time.perf_counter() - start
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{elapsed:.4f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_timing)

app.add_middleware(ASGITimingMiddleware)
```

### Background Tasks

```python
from fastapi import BackgroundTasks

async def send_email(to: str, subject: str):
    await email_service.send(to, subject)

@app.post("/signup")
async def signup(user: UserCreate, bg: BackgroundTasks):
    db_user = await create_user(user)
    bg.add_task(send_email, user.email, "Welcome!")
    bg.add_task(log_signup, user.email)
    return db_user  # Response sent immediately; tasks run after
```

### WebSockets

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, message: str):
        for conn in self.connections:
            await conn.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: str):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast(f"Room {room_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
```

### Exception Handling

```python
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Built-in HTTP exception
raise HTTPException(status_code=404, detail="Item not found")
raise HTTPException(
    status_code=403,
    detail="Not authorized",
    headers={"WWW-Authenticate": "Bearer"},
)

# Custom exception + handler
class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": str(exc.retry_after)},
    )

# Override validation error format
@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
```

### Testing

```python
from fastapi.testclient import TestClient
import pytest

# Sync testing
client = TestClient(app)

def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Widget"

def test_create_item():
    response = client.post("/items", json={"name": "New", "price": 9.99})
    assert response.status_code == 201

# Async testing (pytest-asyncio)
import httpx

@pytest.mark.asyncio
async def test_async():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/items")
        assert response.status_code == 200

# Override dependencies in tests
async def override_get_db():
    return FakeDatabase()

app.dependency_overrides[get_db] = override_get_db

# Test WebSocket
def test_websocket():
    with client.websocket_connect("/ws/room1") as ws:
        ws.send_text("hello")
        data = ws.receive_text()
        assert "hello" in data
```

### Common Patterns

```python
# Pagination
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int

# API versioning
v1 = APIRouter(prefix="/api/v1")
v2 = APIRouter(prefix="/api/v2")
app.include_router(v1)
app.include_router(v2)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.2.3"}

# Startup/shutdown events
@asynccontextmanager
async def lifespan(app):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()

app = FastAPI(lifespan=lifespan)

# Rate limiting (simple in-memory)
from collections import defaultdict
import time

request_counts: dict[str, list[float]] = defaultdict(list)

async def rate_limit(request: Request):
    client_ip = request.client.host
    now = time.time()
    request_counts[client_ip] = [
        t for t in request_counts[client_ip] if now - t < 60
    ]
    if len(request_counts[client_ip]) >= 100:
        raise RateLimitExceeded(retry_after=60)
    request_counts[client_ip].append(now)
```

### FastAPI Quick Reference Table

```
@app.get/post/put/delete("/path")   → Route decorator
Path(...)                           → Path parameter validation
Query(...)                          → Query parameter validation
Body(...)                           → Request body validation
Header(...)                         → Header parameter
Cookie(...)                         → Cookie parameter
Depends(func)                       → Dependency injection
BackgroundTasks                     → Post-response tasks
HTTPException(status_code, detail)  → Error response
Response(content, status_code)      → Custom response
UploadFile                          → File upload handling
WebSocket                           → WebSocket connection
APIRouter(prefix="/api")            → Route grouping
app.include_router(router)          → Mount router
app.add_middleware(cls, **kwargs)    → Add middleware
response_model=Model                → Response serialization
status_code=201                     → Custom status code
```

---

## 5. Machine Coding Cheatsheet

### LLD Interview Template (Step-by-Step)

Follow this 6-step framework in every 45-minute machine coding round:

```
Step 1: CLARIFY (3–5 min)
├── Ask about scope: "Which features are in scope?"
├── Ask about scale: "How many concurrent users?"
├── Ask about constraints: "Any specific patterns required?"
├── Ask about edge cases: "Should I handle X?"
└── Write down assumptions

Step 2: IDENTIFY (3–5 min)
├── List all entities (nouns from requirements)
├── List all actions (verbs from requirements)
├── Identify relationships (has-a, is-a, uses)
└── Identify key interfaces

Step 3: DESIGN (5–7 min)
├── Draw class diagram (classes + relationships)
├── Identify design patterns that apply
├── Define public API / interfaces
├── Plan data structures
└── Consider thread safety if relevant

Step 4: IMPLEMENT (20–25 min)
├── Start with core models / entities
├── Implement business logic
├── Add design patterns
├── Handle edge cases
└── Keep code clean and organized

Step 5: TEST (3–5 min)
├── Walk through a happy path
├── Walk through an edge case
├── Demonstrate extensibility
└── Show thread safety (if applicable)

Step 6: DISCUSS (2–3 min)
├── Trade-offs made
├── What you'd improve with more time
├── Scalability considerations
└── Alternative approaches
```

### Common Design Patterns Mapping

| Problem Domain | Primary Pattern | Supporting Patterns |
|---------------|----------------|-------------------|
| **Parking Lot** | Strategy (pricing) | Factory (vehicle), Observer (notifications) |
| **Elevator System** | State (elevator states) | Strategy (scheduling), Observer (floor requests) |
| **Vending Machine** | State (machine states) | Strategy (payment), Factory (products) |
| **Snake & Ladder** | Template Method (game flow) | Strategy (dice), Factory (board elements) |
| **Library Management** | Observer (notifications) | Strategy (search), Factory (items) |
| **Splitwise** | Strategy (split types) | Observer (balance updates), Command (transactions) |
| **Movie Booking** | Strategy (pricing) | Observer (notifications), State (seat states) |
| **Cache (LRU/LFU)** | Strategy (eviction) | Proxy (cache wrapper), Decorator (TTL) |
| **Pub/Sub System** | Observer (core pattern) | Strategy (filtering), Factory (topics) |
| **Task Scheduler** | Command (tasks) | Strategy (scheduling), Observer (completion) |
| **Logger Framework** | Chain of Responsibility | Strategy (output), Singleton (logger instance) |
| **Auction System** | Observer (bidding) | State (auction states), Strategy (bid rules) |
| **Rate Limiter** | Strategy (algorithm) | Proxy (limit wrapper), Decorator (annotations) |
| **File System** | Composite (files/dirs) | Iterator (traversal), Visitor (operations) |
| **Chat System** | Mediator (chat room) | Observer (messages), Command (actions) |

### Class Diagram Notation Quick Reference

```
┌──────────────────┐
│ <<interface>>     │       Relationship Symbols:
│    Printable      │
├──────────────────┤       ──────▶  Association (uses)
│ + print(): void   │       ◇─────▶  Aggregation (has, can exist alone)
└────────┬─────────┘       ◆─────▶  Composition (owns, lifecycle bound)
         │ implements      ─ ─ ─ ▶  Dependency (uses temporarily)
         │                 ────────▷  Inheritance (is-a)
┌────────┴─────────┐       - - - -▷  Implements (interface)
│    Document       │
├──────────────────┤       Visibility:
│ - title: str      │       + public
│ - content: str    │       - private
│ # metadata: dict  │       # protected
├──────────────────┤
│ + save(): bool    │
│ - validate(): bool│
│ # log(): void     │
└──────────────────┘
```

### SOLID Quick Check

| Principle | Quick Check | Red Flag |
|-----------|------------|----------|
| **S**ingle Responsibility | Does this class have ONE reason to change? | Class name has "And" or "Manager" doing too much |
| **O**pen/Closed | Can I add features without modifying existing code? | `if/elif` chains that grow with new types |
| **L**iskov Substitution | Can I substitute subclass without breaking code? | Subclass throws `NotImplementedError` on parent method |
| **I**nterface Segregation | Does the client use ALL methods of the interface? | Classes implementing empty/dummy methods |
| **D**ependency Inversion | Do high-level modules depend on abstractions? | Direct instantiation of concrete classes |

### Code Organization Template

```python
"""
problem_name.py — [Problem Name] LLD Implementation
"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
import threading


# ═══════════════════════════════════════════════════
# Section 1: Enums and Constants
# ═══════════════════════════════════════════════════

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ═══════════════════════════════════════════════════
# Section 2: Core Models / Entities
# ═══════════════════════════════════════════════════

@dataclass
class Entity:
    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════
# Section 3: Interfaces / Abstract Classes
# ═══════════════════════════════════════════════════

class Repository(ABC):
    @abstractmethod
    def save(self, entity: Entity) -> None: ...

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Entity | None: ...


class NotificationService(Protocol):
    def notify(self, user_id: str, message: str) -> None: ...


# ═══════════════════════════════════════════════════
# Section 4: Implementations / Strategies
# ═══════════════════════════════════════════════════

class InMemoryRepository(Repository):
    def __init__(self):
        self._store: dict[str, Entity] = {}
        self._lock = threading.Lock()

    def save(self, entity: Entity) -> None:
        with self._lock:
            self._store[entity.id] = entity

    def find_by_id(self, entity_id: str) -> Entity | None:
        with self._lock:
            return self._store.get(entity_id)


# ═══════════════════════════════════════════════════
# Section 5: Business Logic / Service Layer
# ═══════════════════════════════════════════════════

class EntityService:
    def __init__(self, repo: Repository, notifier: NotificationService):
        self._repo = repo
        self._notifier = notifier

    def create(self, name: str) -> Entity:
        entity = Entity(id=generate_id(), name=name)
        self._repo.save(entity)
        return entity


# ═══════════════════════════════════════════════════
# Section 6: Facade / Main System Class
# ═══════════════════════════════════════════════════

class System:
    """Main entry point — Facade over all services."""

    def __init__(self):
        self._repo = InMemoryRepository()
        self._notifier = ConsoleNotifier()
        self._service = EntityService(self._repo, self._notifier)

    def create_entity(self, name: str) -> Entity:
        return self._service.create(name)


# ═══════════════════════════════════════════════════
# Section 7: Demo / Driver Code
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    system = System()
    entity = system.create_entity("Test")
    print(f"Created: {entity}")
```

### Time Management in 45-Minute Interview

```
 0:00 ┬─── Clarify requirements (3–5 min)
      │    • Ask 3-5 targeted questions
      │    • Write down assumptions
 5:00 ┬─── Identify entities & design (5–7 min)
      │    • List classes and relationships
      │    • Pick design patterns
      │    • Sketch class diagram (verbal or whiteboard)
12:00 ┬─── Implement core models (5 min)
      │    • Enums, dataclasses, base entities
17:00 ┬─── Implement business logic (15 min)
      │    • Main service/system class
      │    • Design pattern implementation
      │    • Key algorithms
32:00 ┬─── Handle edge cases & thread safety (5 min)
      │    • Add locks if concurrent
      │    • Validate inputs
      │    • Handle error cases
37:00 ┬─── Test / Demo (5 min)
      │    • Walk through happy path
      │    • Show edge case handling
      │    • Demonstrate extensibility
42:00 ┬─── Discuss trade-offs (3 min)
      │    • What you'd do differently
      │    • Scalability notes
45:00 └─── Done
```

**Priority if running out of time:**
1. Working core logic > edge cases
2. Clean design > complete features
3. One pattern well > three patterns half-done
4. Runnable code > perfect code

### Common Mistakes Checklist

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| No clarification questions | Solving wrong problem | Always ask 3+ questions first |
| Starting to code immediately | No design = messy code | Spend 10 min on design |
| God class (one class does everything) | Violates SRP, hard to extend | Split into focused classes |
| Hardcoded values | Can't configure or change | Use enums, config, constants |
| No interfaces/abstractions | Tightly coupled, hard to test | Use ABC or Protocol |
| Ignoring thread safety | Race conditions in concurrent context | Add locks to shared state |
| Over-engineering | Too many patterns, too complex | Use patterns only where needed |
| No error handling | Crashes on bad input | Validate inputs, raise meaningful errors |
| Mutable default arguments | Shared state bug | Use `field(default_factory=list)` |
| No demo/test code | Can't prove it works | Always include `if __name__ == "__main__"` |
| Using `print` for logging | Unprofessional, hard to control | Use `logging` module |
| Not mentioning trade-offs | Missed opportunity to show depth | Always discuss alternatives |

### Essential Python Patterns for Interviews

```python
# 1. Enum for fixed choices (better than string constants)
class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"

# 2. Dataclass for simple models (less boilerplate than __init__)
@dataclass
class Order:
    id: str
    items: list[str] = field(default_factory=list)
    total: float = 0.0

# 3. Protocol for duck typing (no inheritance required)
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

# 4. ABC for enforced contracts
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: float) -> bool: ...

# 5. Context manager for resource cleanup
class DatabaseConnection:
    def __enter__(self):
        self.conn = connect()
        return self.conn
    def __exit__(self, *args):
        self.conn.close()

# 6. Generator for lazy iteration
def paginate(items, page_size=10):
    for i in range(0, len(items), page_size):
        yield items[i:i + page_size]

# 7. Property for computed/validated attributes
class Account:
    def __init__(self, balance: float):
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = value

# 8. Slots for memory-efficient classes
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y

# 9. Thread-safe singleton
class ThreadSafeSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# 10. Observer with weak references (prevents memory leaks)
import weakref
class EventEmitter:
    def __init__(self):
        self._listeners = weakref.WeakSet()

    def add_listener(self, listener):
        self._listeners.add(listener)

    def emit(self, event):
        for listener in self._listeners:
            listener.on_event(event)
```

### Problem-Solving Shortcuts

```
Need to...                         → Use this...
──────────────────────────────────────────────────────────
Track order of insertion            → dict (Python 3.7+ preserves order)
Fast lookup + ordered               → dict
LRU cache                          → collections.OrderedDict or functools.lru_cache
Priority processing                 → heapq
FIFO queue                         → collections.deque
Thread-safe queue                   → queue.Queue
Unique elements, fast lookup        → set
Counting occurrences                → collections.Counter
Default values for missing keys     → collections.defaultdict
Immutable record                    → namedtuple or frozen dataclass
Generate unique IDs                 → uuid.uuid4()
Time-based operations               → datetime, time.monotonic()
Interval/scheduling                 → heapq with timestamps
Tree traversal                      → recursion or collections.deque (BFS)
Graph problems                      → dict[node, list[node]] adjacency list
State machine                       → Enum + dict[state, dict[event, state]]
```

### Interview Vocabulary Cheat Sheet

| Term | Quick Definition |
|------|-----------------|
| **Coupling** | How much one class depends on another (low is better) |
| **Cohesion** | How focused a class is on one responsibility (high is better) |
| **Encapsulation** | Hiding internal state, exposing only what's needed |
| **Polymorphism** | Same interface, different behavior (via inheritance or duck typing) |
| **Composition** | Building complex objects by combining simpler ones (prefer over inheritance) |
| **Idempotent** | Same operation applied multiple times gives same result |
| **Thread-safe** | Can be used by multiple threads without data corruption |
| **Race condition** | Bug caused by timing-dependent access to shared state |
| **Deadlock** | Two+ threads each waiting for the other to release a lock |
| **Backpressure** | Slowing producers when consumers can't keep up |
| **Circuit breaker** | Stop calling a failing service temporarily |
| **Bulkhead** | Isolate failures to prevent cascade |

---

## Quick Cross-Reference

### "I need to..." → Which Cheatsheet?

| I need to... | Go to |
|-------------|-------|
| Pick a design pattern | [Pattern Decision Tree](#pattern-decision-tree) |
| Write async code | [AsyncIO Cheatsheet](#2-asyncio-cheatsheet) |
| Choose threads vs async vs processes | [Concurrency Comparison](#threading-vs-multiprocessing-vs-asyncio) |
| Build a FastAPI endpoint | [Route Decorators](#route-decorators) |
| Structure my LLD solution | [Code Organization Template](#code-organization-template) |
| Handle sync primitives | [All Synchronization Primitives](#all-synchronization-primitives) |
| Plan my 45 minutes | [Time Management](#time-management-in-45-minute-interview) |
| Debug a deadlock | [Deadlock Prevention Rules](#deadlock-prevention-rules) |
| Add concurrency control | [Thread Safety Checklist](#thread-safety-checklist) |
| Remember async gotchas | [Common Gotchas](#common-gotchas) |

---

*Previous: [14-production-case-studies.md](14-production-case-studies.md) — Real production case studies covering FastAPI, Celery, Gunicorn, Uvicorn, Kafka, Redis, and more.*
