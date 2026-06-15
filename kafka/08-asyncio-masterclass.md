# AsyncIO Masterclass - Building High-Performance Python

> A comprehensive deep-dive into Python's asyncio ecosystem, from fundamentals to production-grade async services.

---

## Table of Contents

1. [AsyncIO Overview](#1-asyncio-overview)
2. [Event Loop Internals](#2-event-loop-internals)
3. [Coroutines](#3-coroutines)
4. [Async/Await](#4-asyncawait)
5. [Tasks](#5-tasks)
6. [Futures](#6-futures)
7. [Async Queues](#7-async-queues)
8. [Async Locks](#8-async-locks)
9. [Cancellation](#9-cancellation)
10. [Backpressure](#10-backpressure)
11. [Structured Concurrency](#11-structured-concurrency)
12. [Building High-Throughput Services](#12-building-high-throughput-services)

---

## 1. AsyncIO Overview

### What is asyncio and Why It Exists

`asyncio` is Python's standard library for writing concurrent code using the async/await syntax. It provides infrastructure for writing single-threaded concurrent programs using coroutines, multiplexing I/O access over sockets and other resources, running network clients and servers, and other related primitives.

**The Core Problem asyncio Solves:**

```
Traditional Synchronous I/O:
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Request 1│───▶│  Wait... │───▶│ Response │  Total: 3 seconds
└──────────┘    └──────────┘    └──────────┘
                                     │
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Request 2│───▶│  Wait... │───▶│ Response │  Total: 6 seconds
└──────────┘    └──────────┘    └──────────┘
                                     │
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Request 3│───▶│  Wait... │───▶│ Response │  Total: 9 seconds
└──────────┘    └──────────┘    └──────────┘

Async I/O:
┌──────────┐
│ Request 1│───┐
└──────────┘   │
┌──────────┐   │    ┌──────────┐
│ Request 2│───┼───▶│  Wait... │───▶ All 3 responses: ~3 seconds
└──────────┘   │    └──────────┘
┌──────────┐   │
│ Request 3│───┘
└──────────┘
```

### Cooperative vs Preemptive Multitasking

| Aspect | Cooperative (asyncio) | Preemptive (threading) |
|--------|----------------------|----------------------|
| Context switching | Explicit (at await points) | Implicit (OS decides) |
| Race conditions | Rare (predictable yields) | Common (any point) |
| Overhead | Minimal (no thread stack) | Higher (thread creation) |
| Control | Developer controls yields | OS controls scheduling |
| GIL impact | N/A (single thread) | Limited parallelism |

```python
import asyncio
import time

# Cooperative multitasking - tasks voluntarily yield control
async def cooperative_task(name: str, work_time: float):
    print(f"[{name}] Starting work")
    # This is where we COOPERATIVELY yield to other tasks
    await asyncio.sleep(work_time)  # <-- Suspension point
    print(f"[{name}] Done!")
    return f"{name} result"

async def main():
    start = time.perf_counter()
    # All tasks run concurrently on a SINGLE thread
    results = await asyncio.gather(
        cooperative_task("A", 2.0),
        cooperative_task("B", 1.5),
        cooperative_task("C", 1.0),
    )
    elapsed = time.perf_counter() - start
    print(f"All done in {elapsed:.2f}s (not 4.5s!)")
    print(f"Results: {results}")

asyncio.run(main())
# Output:
# [A] Starting work
# [B] Starting work
# [C] Starting work
# [C] Done!
# [B] Done!
# [A] Done!
# All done in 2.00s (not 4.5s!)
# Results: ['A result', 'B result', 'C result']
```

### Single-Threaded Concurrency

asyncio achieves concurrency WITHOUT parallelism. Everything runs on one thread, but while one coroutine is waiting for I/O, others can run.

```
Single Thread Event Loop:
┌─────────────────────────────────────────────────────────────┐
│                    Event Loop (1 thread)                      │
│                                                              │
│  Time ──────────────────────────────────────────────────▶   │
│                                                              │
│  Task A: [RUN][  WAIT  ][RUN][   WAIT   ][RUN]             │
│  Task B:      [RUN][ WAIT ][RUN][WAIT][RUN]                 │
│  Task C:           [RUN][WAIT][RUN]                          │
│                                                              │
│  CPU is NEVER idle when there's runnable work!               │
└─────────────────────────────────────────────────────────────┘
```

```python
import asyncio
import threading

async def show_single_thread():
    """Prove all coroutines run on the same thread."""
    async def worker(name):
        tid = threading.current_thread().ident
        print(f"[{name}] Thread ID: {tid}")
        await asyncio.sleep(0.1)
        print(f"[{name}] Still on thread: {threading.current_thread().ident}")

    await asyncio.gather(
        worker("A"),
        worker("B"),
        worker("C"),
    )
    # All will print the SAME thread ID

asyncio.run(show_single_thread())
```

### asyncio vs threading vs multiprocessing

```python
"""
Comparison: When to use which concurrency model.
"""
import asyncio
import threading
import multiprocessing
import time

# ─── I/O-bound task (network, disk, database) ───
# asyncio WINS here - minimal overhead, maximum concurrency

async def async_io_bound():
    """Best for I/O-bound: asyncio"""
    tasks = [asyncio.sleep(1) for _ in range(1000)]
    await asyncio.gather(*tasks)  # 1000 concurrent "connections" in ~1s

def threaded_io_bound():
    """OK for I/O-bound: threading (but heavy)"""
    threads = [threading.Thread(target=time.sleep, args=(1,)) for _ in range(1000)]
    for t in threads:
        t.start()  # 1000 threads = significant memory overhead
    for t in threads:
        t.join()

# ─── CPU-bound task (computation, data processing) ───
# multiprocessing WINS here - true parallelism

def cpu_work(n):
    """Simulate CPU-intensive work."""
    return sum(i * i for i in range(n))

def multiprocess_cpu_bound():
    """Best for CPU-bound: multiprocessing"""
    with multiprocessing.Pool(4) as pool:
        results = pool.map(cpu_work, [10_000_000] * 4)

async def async_cpu_bound():
    """WRONG for CPU-bound: asyncio blocks the loop!"""
    # This BLOCKS the entire event loop - other tasks starve
    result = sum(i * i for i in range(10_000_000))
    return result
```

**Decision Matrix:**

```
┌─────────────────────────────────────────────────────────────┐
│              Which Concurrency Model to Use?                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  I/O-bound + High concurrency ──────────▶ asyncio           │
│  (web servers, scrapers, chat)                               │
│                                                              │
│  I/O-bound + Simple code ───────────────▶ threading         │
│  (few connections, legacy code)                              │
│                                                              │
│  CPU-bound ─────────────────────────────▶ multiprocessing   │
│  (data processing, ML training)                              │
│                                                              │
│  CPU-bound + I/O-bound mix ─────────────▶ asyncio +         │
│  (API server doing computation)           run_in_executor   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### When to Use asyncio

**Use asyncio when:**
- You have many I/O-bound operations (HTTP requests, database queries, file I/O)
- You need thousands of concurrent connections
- You want predictable concurrency (no race conditions from preemption)
- You're building network servers/clients
- You're working with websockets or streaming protocols

**Don't use asyncio when:**
- Your workload is purely CPU-bound
- You need true parallelism
- Your libraries don't support async (no async database driver available)
- Simple scripts with minimal concurrency needs

### History and Evolution

```
Python 3.4 (2014): asyncio introduced as provisional
  - @asyncio.coroutine decorator + yield from
  - Basic event loop, futures, tasks

Python 3.5 (2015): Native coroutines
  - async def / await syntax (PEP 492)
  - async for, async with

Python 3.6 (2016): Async generators
  - async generators (PEP 525)
  - Asynchronous comprehensions (PEP 530)

Python 3.7 (2018): High-level API
  - asyncio.run() added
  - asyncio.create_task()
  - Context variables support

Python 3.8 (2019): Refinements
  - asyncio.CancelledError now inherits BaseException
  - python -m asyncio REPL

Python 3.9 (2020): Deprecations
  - asyncio.to_thread() added
  - Many old APIs deprecated

Python 3.10 (2021): Improvements
  - aiter() and anext() builtins
  - Stricter shutdown of default executor

Python 3.11 (2022): Structured concurrency
  - TaskGroup (exception groups)
  - asyncio.Runner
  - asyncio.Barrier
  - asyncio.timeout() context manager

Python 3.12 (2023): Performance
  - Eager task factory
  - Performance improvements to event loop
  - Better error messages

Python 3.13+ (2024+): Further refinements
  - Continued performance work
  - Better typing support
```

### Interview Relevance

- **Frequently asked:** "Explain how asyncio achieves concurrency on a single thread"
- **Key insight:** asyncio is NOT parallel - it's concurrent through cooperative scheduling
- **Common follow-up:** "When would you choose asyncio over threading?"

---

## 2. Event Loop Internals

### What the Event Loop Does

The event loop is the central execution mechanism of asyncio. It:

1. Registers I/O operations and callbacks
2. Watches for I/O readiness (using OS primitives)
3. Executes ready callbacks and coroutines
4. Manages timers and scheduled calls
5. Handles signal delivery

```
┌─────────────────────────────────────────────────────────┐
│                    EVENT LOOP CYCLE                       │
│                                                          │
│  ┌─────────────┐                                        │
│  │ Check ready │◀──────────────────────────────────┐    │
│  │  callbacks  │                                   │    │
│  └──────┬──────┘                                   │    │
│         │                                          │    │
│         ▼                                          │    │
│  ┌─────────────┐                                   │    │
│  │Execute ready│                                   │    │
│  │  callbacks  │                                   │    │
│  └──────┬──────┘                                   │    │
│         │                                          │    │
│         ▼                                          │    │
│  ┌─────────────┐     ┌──────────────┐             │    │
│  │  Poll I/O   │────▶│Process events│─────────────┘    │
│  │  (select/   │     │(mark futures │                   │
│  │   epoll)    │     │  as ready)   │                   │
│  └─────────────┘     └──────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### How It Works Internally (select/poll/epoll/kqueue)

The event loop uses OS-level I/O multiplexing:

| Mechanism | OS | Scalability | How it works |
|-----------|-----|-------------|--------------|
| `select` | All | O(n) per call | Passes all FDs each time |
| `poll` | Linux/macOS | O(n) per call | No FD limit, but still scans |
| `epoll` | Linux | O(1) per event | Kernel maintains interest list |
| `kqueue` | macOS/BSD | O(1) per event | Kernel event notification |
| `IOCP` | Windows | O(1) per event | Completion ports |

```python
import asyncio
import selectors
import sys

def show_selector_info():
    """Show which I/O selector the current platform uses."""
    selector = selectors.DefaultSelector()
    print(f"Platform: {sys.platform}")
    print(f"Selector: {type(selector).__name__}")
    # Linux: EpollSelector
    # macOS: KqueueSelector
    # Windows: SelectSelector (or ProactorEventLoop uses IOCP)
    selector.close()

show_selector_info()
```

**Simplified Event Loop Implementation:**

```python
import selectors
import time
from collections import deque
from heapq import heappush, heappop

class SimplifiedEventLoop:
    """
    A minimal event loop to understand the internals.
    Real asyncio is much more complex but follows this pattern.
    """

    def __init__(self):
        self._selector = selectors.DefaultSelector()
        self._ready = deque()          # Callbacks ready to run
        self._scheduled = []           # Heap of (time, callback)
        self._stopping = False

    def call_soon(self, callback, *args):
        """Schedule callback to be called in the next iteration."""
        self._ready.append((callback, args))

    def call_later(self, delay, callback, *args):
        """Schedule callback after delay seconds."""
        when = time.monotonic() + delay
        heappush(self._scheduled, (when, callback, args))

    def _run_once(self):
        """Single iteration of the event loop."""
        # 1. Move scheduled callbacks that are due to ready queue
        now = time.monotonic()
        while self._scheduled and self._scheduled[0][0] <= now:
            _, callback, args = heappop(self._scheduled)
            self._ready.append((callback, args))

        # 2. Calculate timeout for I/O polling
        if self._ready:
            timeout = 0  # Don't block, we have work to do
        elif self._scheduled:
            timeout = max(0, self._scheduled[0][0] - now)
        else:
            timeout = None  # Block until I/O event

        # 3. Poll for I/O events (this is where select/epoll/kqueue is used)
        events = self._selector.select(timeout)
        for key, mask in events:
            callback = key.data
            self._ready.append((callback, ()))

        # 4. Execute all ready callbacks
        ntodo = len(self._ready)
        for _ in range(ntodo):
            callback, args = self._ready.popleft()
            callback(*args)

    def run_forever(self):
        """Run until stop() is called."""
        while not self._stopping:
            self._run_once()

    def stop(self):
        self._stopping = True
```

### Event Loop Lifecycle

```python
import asyncio

async def demonstrate_lifecycle():
    loop = asyncio.get_running_loop()

    print(f"Loop running: {loop.is_running()}")  # True
    print(f"Loop closed: {loop.is_closed()}")    # False
    print(f"Loop implementation: {type(loop).__name__}")

asyncio.run(demonstrate_lifecycle())

# Lifecycle:
# 1. asyncio.run() creates a NEW event loop
# 2. Sets it as the running loop for this thread
# 3. Runs the coroutine to completion
# 4. Cancels all remaining tasks
# 5. Shuts down async generators
# 6. Closes the event loop
```

### Running the Loop

```python
import asyncio

async def my_coroutine():
    await asyncio.sleep(1)
    return "done"

# ─── Method 1: asyncio.run() (recommended, Python 3.7+) ───
result = asyncio.run(my_coroutine())

# ─── Method 2: Low-level loop management ───
# (Use only when you need fine-grained control)
loop = asyncio.new_event_loop()
try:
    result = loop.run_until_complete(my_coroutine())
finally:
    loop.close()

# ─── Method 3: asyncio.Runner (Python 3.11+) ───
# Reusable runner that keeps the loop alive between calls
with asyncio.Runner() as runner:
    result1 = runner.run(my_coroutine())
    result2 = runner.run(my_coroutine())
    # Same loop used for both calls
```

### Custom Event Loop Policies

```python
import asyncio

class CustomEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """Custom policy that logs loop creation."""

    def new_event_loop(self):
        loop = super().new_event_loop()
        print(f"Created new event loop: {type(loop).__name__}")
        # Could customize: set exception handler, enable debug, etc.
        loop.set_debug(True)
        loop.slow_callback_duration = 0.05  # Warn if callback > 50ms
        return loop

# Set custom policy
asyncio.set_event_loop_policy(CustomEventLoopPolicy())

async def main():
    loop = asyncio.get_running_loop()
    print(f"Running on: {type(loop).__name__}")

asyncio.run(main())

# Reset to default
asyncio.set_event_loop_policy(None)
```

### Debug Mode

```python
import asyncio
import warnings

async def blocking_example():
    """This will trigger a warning in debug mode."""
    import time
    # This blocks the event loop! Debug mode will warn.
    time.sleep(0.2)  # BAD: synchronous sleep

async def unawaited_example():
    """Debug mode catches unawaited coroutines."""
    asyncio.sleep(1)  # Forgot to await!

async def main():
    loop = asyncio.get_running_loop()
    print(f"Debug mode: {loop.get_debug()}")

    # Intentionally block to show debug warning
    import time
    time.sleep(0.15)  # Will warn: "Executing took 0.150 seconds"

# Enable debug mode - multiple ways:
# 1. Environment variable: PYTHONASYNCIODEBUG=1
# 2. asyncio.run(main(), debug=True)
# 3. loop.set_debug(True)
# 4. python -X dev

asyncio.run(main(), debug=True)
# Warnings:
# - Slow callbacks (>100ms by default)
# - Unawaited coroutines
# - Unclosed resources
```

### Example: Understanding Event Loop Scheduling

```python
import asyncio
import time

async def trace_scheduling():
    """Demonstrates how the event loop schedules coroutines."""

    async def task(name, delay):
        print(f"  [{time.perf_counter():.3f}] {name}: started")
        await asyncio.sleep(delay)
        print(f"  [{time.perf_counter():.3f}] {name}: resumed after sleep")
        # Yielding control back explicitly
        await asyncio.sleep(0)  # Yield point - let others run
        print(f"  [{time.perf_counter():.3f}] {name}: finished")

    print("Scheduling order demonstration:")
    print("=" * 50)

    # Tasks are scheduled in order but run concurrently
    t1 = asyncio.create_task(task("Task-1", 0.3))
    t2 = asyncio.create_task(task("Task-2", 0.1))
    t3 = asyncio.create_task(task("Task-3", 0.2))

    # Current coroutine continues until it hits an await
    print(f"  [{time.perf_counter():.3f}] Main: tasks created, now awaiting")

    await asyncio.gather(t1, t2, t3)
    print(f"  [{time.perf_counter():.3f}] Main: all tasks done")

asyncio.run(trace_scheduling())
```

### Common Pitfalls

1. **Blocking the event loop** - calling sync I/O in async code
2. **Creating loops in loops** - `asyncio.run()` inside an already running loop
3. **Not closing the loop** - resource leaks
4. **Using deprecated loop APIs** - `asyncio.get_event_loop()` without running loop

### Performance Tips

- Use `uvloop` for 2-4x performance improvement on Linux/macOS
- Minimize callback overhead by batching operations
- Use `loop.call_soon()` instead of creating tasks for simple callbacks

```python
# uvloop - drop-in replacement for massive speedup
# pip install uvloop
import asyncio

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("Using uvloop - 2-4x faster!")
except ImportError:
    print("Using default event loop")
```

---

## 3. Coroutines

### What is a Coroutine

A coroutine is a specialized function that can suspend and resume its execution. In Python's asyncio, there's a critical distinction:

```python
import asyncio
import inspect

# Coroutine FUNCTION - the definition (async def creates this)
async def fetch_data(url: str) -> str:
    await asyncio.sleep(1)
    return f"Data from {url}"

# Coroutine OBJECT - calling the function creates this
coro = fetch_data("https://example.com")

print(f"Function type: {type(fetch_data)}")        # <class 'function'>
print(f"Is coroutine function: {inspect.iscoroutinefunction(fetch_data)}")  # True

print(f"Object type: {type(coro)}")                # <class 'coroutine'>
print(f"Is coroutine: {inspect.iscoroutine(coro)}")  # True

# IMPORTANT: The coroutine object must be awaited or scheduled
# Otherwise it does nothing and Python warns about it
asyncio.run(coro)
```

### async def Syntax

```python
import asyncio

# Basic coroutine function
async def simple():
    return 42

# Coroutine with parameters and return type
async def fetch(url: str, timeout: float = 5.0) -> dict:
    await asyncio.sleep(timeout)
    return {"url": url, "status": 200}

# Async method in a class
class AsyncClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get(self, path: str) -> str:
        await asyncio.sleep(0.1)  # Simulate network call
        return f"Response from {self.base_url}{path}"

    async def __aenter__(self):
        print("Opening connection")
        return self

    async def __aexit__(self, *args):
        print("Closing connection")

# Usage
async def main():
    async with AsyncClient("https://api.example.com") as client:
        response = await client.get("/users")
        print(response)

asyncio.run(main())
```

### Coroutine Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                  COROUTINE LIFECYCLE                      │
│                                                          │
│  ┌─────────┐     ┌─────────┐     ┌──────────┐          │
│  │ Created │────▶│ Running │────▶│Suspended │          │
│  │(pending)│     │         │     │(awaiting)│          │
│  └─────────┘     └────┬────┘     └─────┬────┘          │
│                        │                 │               │
│                        │       I/O ready │               │
│                        │                 │               │
│                        │          ┌──────▼────┐          │
│                        │          │  Running  │          │
│                        │          │  (again)  │          │
│                        │          └─────┬─────┘          │
│                        │                │               │
│                        ▼                ▼               │
│                  ┌──────────┐    ┌──────────┐          │
│                  │Completed │    │Completed │          │
│                  │(returned)│    │(returned)│          │
│                  └──────────┘    └──────────┘          │
│                                                          │
│  Alternative endings:                                    │
│  - Exception raised (error state)                        │
│  - CancelledError (cancelled state)                      │
│  - Never awaited (garbage collected with warning)        │
└─────────────────────────────────────────────────────────┘
```

```python
import asyncio
import inspect

async def lifecycle_demo():
    """Track coroutine through its lifecycle."""

    async def worker():
        await asyncio.sleep(0.5)
        return "done"

    # Stage 1: Created
    coro = worker()
    print(f"State after creation: {inspect.getcoroutinestate(coro)}")
    # CORO_CREATED

    # Stage 2: Running/Suspended (we need to step through manually to see this)
    # In practice, the event loop handles this
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)  # Let the task start

    # Stage 3: Task wraps the coroutine
    print(f"Task state: {task._state}")  # PENDING

    await task
    print(f"Task state after completion: {task._state}")  # FINISHED
    print(f"Task result: {task.result()}")

asyncio.run(lifecycle_demo())
```

### Coroutines vs Generators

```python
import asyncio

# Generator - yields values (pull-based)
def counter_generator(n):
    """Produces values one at a time."""
    for i in range(n):
        yield i  # Caller pulls next value

# Coroutine - awaits values (push-based scheduling)
async def counter_coroutine(n):
    """Async version - can suspend during each iteration."""
    results = []
    for i in range(n):
        await asyncio.sleep(0.01)  # Can do async work
        results.append(i)
    return results

# Async Generator - combines both! (yields AND can await)
async def async_counter(n):
    """Yields values asynchronously."""
    for i in range(n):
        await asyncio.sleep(0.01)
        yield i  # Can be consumed with `async for`

async def main():
    # Generator usage (sync)
    gen_values = list(counter_generator(5))
    print(f"Generator: {gen_values}")

    # Coroutine usage (async)
    coro_values = await counter_coroutine(5)
    print(f"Coroutine: {coro_values}")

    # Async generator usage
    async_values = []
    async for val in async_counter(5):
        async_values.append(val)
    print(f"Async Generator: {async_values}")

asyncio.run(main())
```

**Key Differences:**

| Feature | Generator | Coroutine | Async Generator |
|---------|-----------|-----------|-----------------|
| Keyword | `yield` | `await` | `yield` + `await` |
| Purpose | Produce values | Concurrent execution | Async value production |
| Iteration | `for x in gen` | `await coro` | `async for x in agen` |
| Suspension | At `yield` | At `await` | At both |
| Return | `StopIteration` | Future result | `StopAsyncIteration` |

### Inspecting Coroutines

```python
import asyncio
import inspect

async def inspectable(x, y):
    """A coroutine we can inspect."""
    local_var = x + y
    await asyncio.sleep(0.1)
    return local_var

async def main():
    coro = inspectable(3, 4)

    # Inspect the coroutine object
    print(f"Coroutine name: {coro.__name__}")
    print(f"Qualname: {coro.__qualname__}")
    print(f"State: {inspect.getcoroutinestate(coro)}")

    # Get the code object
    code = coro.cr_code
    print(f"Filename: {code.co_filename}")
    print(f"First line: {code.co_firstlineno}")
    print(f"Local vars will include: {code.co_varnames}")

    # Frame is None until running
    print(f"Frame (before run): {coro.cr_frame}")

    result = await coro
    print(f"Result: {result}")

    # After completion
    print(f"State after: {inspect.getcoroutinestate(coro)}")

asyncio.run(main())
```

### Native Coroutines vs Generator-Based (Legacy)

```python
import asyncio

# ─── Legacy (Python 3.4) - DO NOT use in new code ───
@asyncio.coroutine
def legacy_coroutine():
    """Old-style coroutine using decorator + yield from."""
    result = yield from asyncio.sleep(1)
    return "legacy result"

# ─── Native (Python 3.5+) - Always use this ───
async def native_coroutine():
    """Modern coroutine using async/await."""
    await asyncio.sleep(1)
    return "native result"

# Both work with the event loop, but native is:
# - Clearer syntax
# - Better error messages
# - Faster execution
# - Proper type checking
# - Cannot accidentally yield non-awaitable values
```

### Example: Building Coroutines from Scratch

```python
import asyncio
import time

async def retry_with_backoff(
    coro_factory,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
):
    """
    A reusable coroutine pattern: retry with exponential backoff.

    Args:
        coro_factory: Callable that returns a new coroutine each attempt
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay cap
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break

            delay = min(base_delay * (2 ** attempt), max_delay)
            print(f"  Attempt {attempt + 1} failed: {e}. "
                  f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)

    raise last_exception

async def unreliable_operation():
    """Simulates an operation that fails intermittently."""
    import random
    if random.random() < 0.7:  # 70% failure rate
        raise ConnectionError("Server unavailable")
    return "Success!"

async def main():
    print("Attempting unreliable operation with retry...")
    try:
        result = await retry_with_backoff(
            unreliable_operation,
            max_retries=5,
            base_delay=0.5,
        )
        print(f"Final result: {result}")
    except ConnectionError as e:
        print(f"All retries exhausted: {e}")

asyncio.run(main())
```

### Common Pitfalls

1. **Forgetting to await** - coroutine object is created but never executed
2. **Calling coroutine function expecting immediate execution** - it returns an object
3. **Reusing coroutine objects** - a coroutine can only be awaited once

```python
import asyncio

async def pitfall_examples():
    async def greet(name):
        return f"Hello, {name}"

    # WRONG: Forgot to await
    result = greet("World")  # This is a coroutine object, not "Hello, World"!
    print(type(result))  # <class 'coroutine'>
    # RuntimeWarning: coroutine 'greet' was never awaited

    # CORRECT:
    result = await greet("World")
    print(result)  # "Hello, World"

    # WRONG: Reusing a coroutine object
    coro = greet("Python")
    await coro  # Works first time
    # await coro  # RuntimeError: cannot reuse already awaited coroutine

asyncio.run(pitfall_examples())
```

---

## 4. Async/Await

### await Expression Semantics

The `await` keyword does three things:

1. **Suspends** the current coroutine's execution
2. **Yields control** back to the event loop
3. **Resumes** when the awaited object completes (with its result or exception)

```python
import asyncio

async def await_semantics():
    """Demonstrating what await actually does."""

    print("1. Before await - coroutine is running")

    # await does:
    # a) Checks if the awaitable is already done (fast path)
    # b) If not, registers this coroutine to be resumed when it completes
    # c) Suspends this coroutine (returns control to event loop)
    # d) Event loop runs other tasks...
    # e) When awaitable completes, event loop resumes this coroutine
    # f) The await expression evaluates to the result

    result = await asyncio.sleep(1, result="hello")

    print(f"2. After await - got result: {result}")
    # Between step 1 and 2, the event loop was free to run other tasks

asyncio.run(await_semantics())
```

### What Can Be Awaited (Awaitables)

Three types of objects can be awaited:

```python
import asyncio

# ─── 1. Coroutines ───
async def coroutine_awaitable():
    return "from coroutine"

# ─── 2. Tasks ───
async def task_awaitable():
    task = asyncio.create_task(asyncio.sleep(0.1, result="from task"))
    result = await task
    return result

# ─── 3. Futures ───
async def future_awaitable():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    # Simulate setting result after a delay
    loop.call_later(0.1, future.set_result, "from future")

    result = await future
    return result

# ─── 4. Objects with __await__ (custom awaitables) ───
class CustomAwaitable:
    """Any object with __await__ can be used with await."""

    def __init__(self, value, delay=0.1):
        self.value = value
        self.delay = delay

    def __await__(self):
        # Must return an iterator that yields to the event loop
        yield from asyncio.sleep(self.delay).__await__()
        return self.value

async def custom_awaitable_demo():
    result = await CustomAwaitable("from custom", delay=0.2)
    return result

async def main():
    r1 = await coroutine_awaitable()
    r2 = await task_awaitable()
    r3 = await future_awaitable()
    r4 = await custom_awaitable_demo()
    print(f"Results: {r1}, {r2}, {r3}, {r4}")

asyncio.run(main())
```

### Suspension Points

```python
import asyncio

async def suspension_points_demo():
    """
    Only at `await` does the coroutine suspend.
    Between awaits, code runs WITHOUT interruption.
    This is why asyncio has fewer race conditions than threading.
    """
    shared_state = {"counter": 0}

    async def safe_increment():
        # These three lines execute ATOMICALLY (no await between them)
        current = shared_state["counter"]
        current += 1
        shared_state["counter"] = current
        # No other coroutine can run between read and write!

    async def unsafe_increment():
        current = shared_state["counter"]
        await asyncio.sleep(0)  # ← SUSPENSION POINT - others can run!
        current += 1
        shared_state["counter"] = current
        # Another coroutine might have modified counter during sleep!

    # Safe: all increments are atomic
    shared_state["counter"] = 0
    await asyncio.gather(*[safe_increment() for _ in range(100)])
    print(f"Safe counter: {shared_state['counter']}")  # Always 100

    # Unsafe: race condition possible
    shared_state["counter"] = 0
    await asyncio.gather(*[unsafe_increment() for _ in range(100)])
    print(f"Unsafe counter: {shared_state['counter']}")  # Might be < 100!

asyncio.run(suspension_points_demo())
```

### Nested Awaits

```python
import asyncio

async def inner_operation(value: int) -> int:
    await asyncio.sleep(0.1)
    return value * 2

async def middle_layer(value: int) -> int:
    # Nested await - suspends until inner completes
    result = await inner_operation(value)
    return result + 10

async def outer_function() -> int:
    # Each await propagates suspension up the call chain
    result = await middle_layer(5)
    return result

async def main():
    # Call stack during suspension:
    # main() → outer_function() → middle_layer() → inner_operation() → sleep()
    # When sleep completes, execution unwinds back through each level
    final = await outer_function()
    print(f"Result: {final}")  # (5 * 2) + 10 = 20

asyncio.run(main())
```

### Common Patterns

```python
import asyncio
from typing import Any

# ─── Pattern 1: Sequential awaiting ───
async def sequential():
    """Each operation waits for the previous to complete."""
    result1 = await fetch_data("url1")  # Wait...
    result2 = await fetch_data("url2")  # Wait...
    result3 = await fetch_data("url3")  # Wait...
    return [result1, result2, result3]  # Total time: sum of all

# ─── Pattern 2: Concurrent awaiting ───
async def concurrent():
    """All operations run at the same time."""
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    )
    return results  # Total time: max of all

# ─── Pattern 3: First completed ───
async def first_completed():
    """Return as soon as any operation completes."""
    done, pending = await asyncio.wait(
        [asyncio.create_task(fetch_data(f"url{i}")) for i in range(3)],
        return_when=asyncio.FIRST_COMPLETED,
    )
    # Cancel remaining tasks
    for task in pending:
        task.cancel()
    return done.pop().result()

# ─── Pattern 4: Timeout wrapper ───
async def with_timeout():
    """Fail if operation takes too long."""
    try:
        result = await asyncio.wait_for(fetch_data("slow_url"), timeout=5.0)
        return result
    except asyncio.TimeoutError:
        return "Operation timed out"

# ─── Pattern 5: Async context manager ───
async def with_resource():
    """Acquire and release async resources."""
    async with AsyncDatabaseConnection() as db:
        result = await db.query("SELECT * FROM users")
        return result

# Helper for examples above
async def fetch_data(url: str) -> str:
    await asyncio.sleep(1)
    return f"data from {url}"

class AsyncDatabaseConnection:
    async def __aenter__(self):
        await asyncio.sleep(0.1)  # Connect
        return self

    async def __aexit__(self, *args):
        await asyncio.sleep(0.05)  # Disconnect

    async def query(self, sql: str):
        await asyncio.sleep(0.2)
        return [{"id": 1}]
```

### Anti-Patterns (Blocking the Event Loop)

```python
import asyncio
import time

async def anti_patterns():
    """Things you should NEVER do in async code."""

    # ❌ WRONG: Blocking sleep
    # time.sleep(5)  # Blocks ENTIRE event loop for 5 seconds

    # ✅ CORRECT: Async sleep
    await asyncio.sleep(5)

    # ❌ WRONG: Synchronous HTTP request
    # import requests
    # response = requests.get("https://api.example.com")  # BLOCKS!

    # ✅ CORRECT: Use aiohttp or httpx
    # async with aiohttp.ClientSession() as session:
    #     response = await session.get("https://api.example.com")

    # ❌ WRONG: CPU-intensive work directly
    # result = compute_heavy_thing()  # Blocks the loop!

    # ✅ CORRECT: Offload to thread pool
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, compute_heavy_thing)

    # ❌ WRONG: Synchronous file I/O
    # with open("big_file.txt") as f:
    #     data = f.read()  # BLOCKS!

    # ✅ CORRECT: Use aiofiles or run in executor
    # async with aiofiles.open("big_file.txt") as f:
    #     data = await f.read()

def compute_heavy_thing():
    return sum(i * i for i in range(1_000_000))
```

### Example: Sequential vs Concurrent Awaiting

```python
import asyncio
import time

async def simulate_api_call(endpoint: str, latency: float) -> dict:
    """Simulate an API call with given latency."""
    await asyncio.sleep(latency)
    return {"endpoint": endpoint, "status": 200, "latency": latency}

async def sequential_approach():
    """Fetch endpoints one after another."""
    start = time.perf_counter()

    user = await simulate_api_call("/user", 0.5)
    posts = await simulate_api_call("/posts", 0.8)
    comments = await simulate_api_call("/comments", 0.3)
    likes = await simulate_api_call("/likes", 0.4)

    elapsed = time.perf_counter() - start
    print(f"Sequential: {elapsed:.2f}s (expected ~2.0s)")
    return [user, posts, comments, likes]

async def concurrent_approach():
    """Fetch all endpoints at once."""
    start = time.perf_counter()

    user, posts, comments, likes = await asyncio.gather(
        simulate_api_call("/user", 0.5),
        simulate_api_call("/posts", 0.8),
        simulate_api_call("/comments", 0.3),
        simulate_api_call("/likes", 0.4),
    )

    elapsed = time.perf_counter() - start
    print(f"Concurrent: {elapsed:.2f}s (expected ~0.8s)")
    return [user, posts, comments, likes]

async def hybrid_approach():
    """Some operations depend on others - mix sequential and concurrent."""
    start = time.perf_counter()

    # First: get user (others depend on it)
    user = await simulate_api_call("/user", 0.5)

    # Then: fetch user's posts and likes concurrently
    posts, likes = await asyncio.gather(
        simulate_api_call(f"/user/{user}/posts", 0.8),
        simulate_api_call(f"/user/{user}/likes", 0.4),
    )

    # Finally: get comments for posts
    comments = await simulate_api_call(f"/posts/{posts}/comments", 0.3)

    elapsed = time.perf_counter() - start
    print(f"Hybrid: {elapsed:.2f}s (expected ~1.6s)")

async def main():
    await sequential_approach()   # ~2.0s
    await concurrent_approach()   # ~0.8s
    await hybrid_approach()       # ~1.6s

asyncio.run(main())
```

---

## 5. Tasks

### asyncio.create_task()

Tasks wrap coroutines and schedule them for execution on the event loop. A task runs independently and concurrently with the coroutine that created it.

```python
import asyncio

async def background_work(name: str, duration: float) -> str:
    print(f"[{name}] Starting...")
    await asyncio.sleep(duration)
    print(f"[{name}] Complete!")
    return f"{name} result"

async def main():
    # create_task() schedules the coroutine immediately
    # The task starts running at the next await point in the current coroutine
    task1 = asyncio.create_task(background_work("Task-1", 2.0))
    task2 = asyncio.create_task(background_work("Task-2", 1.0))

    print("Tasks created! Doing other work...")
    await asyncio.sleep(0.5)
    print("Still doing other work while tasks run...")

    # Await results when needed
    result1 = await task1
    result2 = await task2
    print(f"Results: {result1}, {result2}")

asyncio.run(main())
```

### Task Lifecycle and States

```python
import asyncio

async def demonstrate_task_states():
    """Show all possible task states."""

    async def sleeper():
        await asyncio.sleep(10)
        return "done"

    # PENDING: Task is scheduled but not yet complete
    task = asyncio.create_task(sleeper(), name="my-task")
    print(f"After creation: cancelled={task.cancelled()}, "
          f"done={task.done()}")

    await asyncio.sleep(0)  # Let task start running
    print(f"After start: cancelled={task.cancelled()}, "
          f"done={task.done()}")

    # CANCELLED: Task was cancelled
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print(f"After cancel: cancelled={task.cancelled()}, "
              f"done={task.done()}")

    # FINISHED (success): Task completed normally
    async def quick():
        return 42

    task2 = asyncio.create_task(quick())
    await task2
    print(f"Successful: result={task2.result()}, done={task2.done()}")

    # FINISHED (exception): Task raised an exception
    async def failing():
        raise ValueError("Something went wrong")

    task3 = asyncio.create_task(failing())
    try:
        await task3
    except ValueError:
        print(f"Failed: exception={task3.exception()}, done={task3.done()}")

asyncio.run(demonstrate_task_states())
```

### Task Groups (Python 3.11+)

```python
import asyncio

async def fetch_url(url: str) -> str:
    await asyncio.sleep(0.5)
    if "bad" in url:
        raise ValueError(f"Bad URL: {url}")
    return f"Content from {url}"

async def task_group_basic():
    """TaskGroup ensures all tasks complete or all are cancelled on error."""
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(fetch_url("https://good1.com"))
            task2 = tg.create_task(fetch_url("https://good2.com"))
            task3 = tg.create_task(fetch_url("https://good3.com"))
        # If we reach here, ALL tasks succeeded
        print(f"Results: {task1.result()}, {task2.result()}, {task3.result()}")
    except* ValueError as eg:
        # ExceptionGroup contains all task exceptions
        print(f"Some tasks failed: {eg.exceptions}")

async def task_group_with_failure():
    """When one task fails, others are cancelled."""
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(fetch_url("https://good.com"))
            task2 = tg.create_task(fetch_url("https://bad-url.com"))  # Will fail
            task3 = tg.create_task(fetch_url("https://also-good.com"))
        # Never reached!
    except* ValueError as eg:
        print(f"Failed tasks: {len(eg.exceptions)}")
        for exc in eg.exceptions:
            print(f"  - {exc}")

async def main():
    print("=== Successful TaskGroup ===")
    await task_group_basic()
    print("\n=== TaskGroup with Failure ===")
    await task_group_with_failure()

asyncio.run(main())
```

### Gathering Tasks (asyncio.gather)

```python
import asyncio

async def worker(n: int) -> int:
    await asyncio.sleep(n * 0.1)
    if n == 3:
        raise ValueError(f"Worker {n} failed!")
    return n * 10

async def gather_examples():
    # ─── Basic gather: all succeed ───
    results = await asyncio.gather(
        worker(1),
        worker(2),
        worker(4),
    )
    print(f"All succeeded: {results}")  # [10, 20, 40]

    # ─── With return_exceptions=True: collect errors ───
    results = await asyncio.gather(
        worker(1),
        worker(2),
        worker(3),  # This will raise
        worker(4),
        return_exceptions=True,
    )
    print(f"With exceptions: {results}")
    # [10, 20, ValueError('Worker 3 failed!'), 40]

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  Task {i} failed: {result}")
        else:
            print(f"  Task {i} succeeded: {result}")

    # ─── Without return_exceptions: first exception propagates ───
    try:
        results = await asyncio.gather(
            worker(1),
            worker(3),  # Raises!
            worker(4),
        )
    except ValueError as e:
        print(f"Gather failed: {e}")

asyncio.run(gather_examples())
```

### Task Naming

```python
import asyncio

async def named_task_demo():
    async def process_item(item_id: int):
        await asyncio.sleep(1)
        return f"Processed {item_id}"

    # Named tasks for better debugging
    tasks = []
    for i in range(5):
        task = asyncio.create_task(
            process_item(i),
            name=f"process-item-{i}",
        )
        tasks.append(task)

    # Inspect running tasks
    all_tasks = asyncio.all_tasks()
    for task in all_tasks:
        print(f"  Task: {task.get_name()}, Done: {task.done()}")

    await asyncio.gather(*tasks)

asyncio.run(named_task_demo())
```

### Exception Handling in Tasks

```python
import asyncio
import traceback

async def exception_handling():
    """Multiple strategies for handling task exceptions."""

    async def risky_operation(n: int):
        await asyncio.sleep(0.1)
        if n % 2 == 0:
            raise RuntimeError(f"Error in operation {n}")
        return f"Success: {n}"

    # ─── Strategy 1: Await and catch ───
    task = asyncio.create_task(risky_operation(2))
    try:
        result = await task
    except RuntimeError as e:
        print(f"Strategy 1 - Caught: {e}")

    # ─── Strategy 2: Add done callback ───
    def handle_task_result(task: asyncio.Task):
        if task.cancelled():
            print(f"  [{task.get_name()}] was cancelled")
        elif task.exception():
            print(f"  [{task.get_name()}] failed: {task.exception()}")
        else:
            print(f"  [{task.get_name()}] succeeded: {task.result()}")

    print("\nStrategy 2 - Callbacks:")
    tasks = []
    for i in range(4):
        t = asyncio.create_task(risky_operation(i), name=f"op-{i}")
        t.add_done_callback(handle_task_result)
        tasks.append(t)

    await asyncio.gather(*tasks, return_exceptions=True)

    # ─── Strategy 3: TaskGroup with except* ───
    print("\nStrategy 3 - TaskGroup:")
    try:
        async with asyncio.TaskGroup() as tg:
            for i in range(4):
                tg.create_task(risky_operation(i))
    except* RuntimeError as eg:
        print(f"  Caught {len(eg.exceptions)} errors")
        for exc in eg.exceptions:
            print(f"    - {exc}")

asyncio.run(exception_handling())
```

### Fire-and-Forget Tasks

```python
import asyncio
import weakref

# Store references to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()

async def fire_and_forget_pattern():
    """
    Schedule tasks that you don't need to await.
    IMPORTANT: Must keep a reference to prevent GC!
    """

    async def log_event(event: str):
        """Background logging that shouldn't block the caller."""
        await asyncio.sleep(0.5)  # Simulate async write
        print(f"  Logged: {event}")

    async def send_notification(user: str, message: str):
        """Non-critical notification."""
        await asyncio.sleep(0.3)
        print(f"  Notified {user}: {message}")

    def create_background_task(coro):
        """Safely create a fire-and-forget task."""
        task = asyncio.create_task(coro)
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return task

    # These tasks run in background - we don't await them
    create_background_task(log_event("user_login"))
    create_background_task(send_notification("alice", "Welcome!"))

    print("Main logic continues immediately...")
    await asyncio.sleep(0.1)
    print("Still working...")

    # Wait for background tasks to complete before exiting
    if _background_tasks:
        await asyncio.gather(*_background_tasks)
    print("All background tasks done")

asyncio.run(fire_and_forget_pattern())
```

### Example: Concurrent HTTP Fetcher with Task Fan-Out

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class FetchResult:
    url: str
    status: int
    size: int
    elapsed: float
    error: Optional[str] = None

async def fetch_url(url: str, timeout: float = 5.0) -> FetchResult:
    """Simulate fetching a URL with realistic behavior."""
    start = time.perf_counter()
    try:
        # Simulate variable network latency
        import random
        latency = random.uniform(0.1, 2.0)

        if latency > timeout:
            raise asyncio.TimeoutError()

        await asyncio.sleep(latency)

        # Simulate occasional failures
        if random.random() < 0.1:
            raise ConnectionError(f"Connection refused: {url}")

        size = random.randint(1000, 50000)
        elapsed = time.perf_counter() - start
        return FetchResult(url=url, status=200, size=size, elapsed=elapsed)

    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start
        return FetchResult(url=url, status=0, size=0, elapsed=elapsed,
                          error="Timeout")
    except ConnectionError as e:
        elapsed = time.perf_counter() - start
        return FetchResult(url=url, status=0, size=0, elapsed=elapsed,
                          error=str(e))

async def concurrent_fetcher(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: float = 5.0,
) -> list[FetchResult]:
    """
    Fetch multiple URLs concurrently with a concurrency limit.

    Uses a semaphore to limit concurrent connections (important for
    not overwhelming the target server or running out of file descriptors).
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[FetchResult] = []

    async def bounded_fetch(url: str) -> FetchResult:
        async with semaphore:
            return await fetch_url(url, timeout)

    # Fan-out: create tasks for all URLs
    tasks = [
        asyncio.create_task(bounded_fetch(url), name=f"fetch-{i}")
        for i, url in enumerate(urls)
    ]

    # Fan-in: collect all results
    results = await asyncio.gather(*tasks)
    return results

async def main():
    urls = [f"https://api.example.com/page/{i}" for i in range(50)]

    start = time.perf_counter()
    results = await concurrent_fetcher(urls, max_concurrent=10)
    total_time = time.perf_counter() - start

    # Report
    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    print(f"\n{'='*50}")
    print(f"Fetched {len(urls)} URLs in {total_time:.2f}s")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    if successful:
        avg_latency = sum(r.elapsed for r in successful) / len(successful)
        total_bytes = sum(r.size for r in successful)
        print(f"  Avg latency: {avg_latency:.3f}s")
        print(f"  Total data: {total_bytes:,} bytes")
    if failed:
        print(f"  Errors:")
        for r in failed[:5]:
            print(f"    {r.url}: {r.error}")

asyncio.run(main())
```

---

## 6. Futures

### What is a Future

A Future is a low-level awaitable object representing the result of an asynchronous operation that hasn't completed yet. It's the fundamental building block upon which Tasks are built.

```python
import asyncio

async def future_basics():
    loop = asyncio.get_running_loop()

    # Create a bare future - it has no result yet
    future = loop.create_future()

    print(f"Done: {future.done()}")        # False
    print(f"Cancelled: {future.cancelled()}")  # False

    # Set the result (normally done by some async operation)
    future.set_result(42)

    print(f"Done: {future.done()}")        # True
    print(f"Result: {future.result()}")    # 42

    # await a future returns its result
    future2 = loop.create_future()
    loop.call_later(0.5, future2.set_result, "delayed result")
    result = await future2
    print(f"Awaited result: {result}")

asyncio.run(future_basics())
```

### Future vs Task

```
┌─────────────────────────────────────────────────────────┐
│                   FUTURE vs TASK                          │
├──────────────────────┬──────────────────────────────────┤
│       Future         │           Task                    │
├──────────────────────┼──────────────────────────────────┤
│ Low-level primitive  │ High-level (subclass of Future)  │
│ Result set manually  │ Result set by coroutine return   │
│ No code execution    │ Wraps and runs a coroutine       │
│ Bridge for callbacks │ Primary async execution unit     │
│ Rarely used directly │ Used constantly                  │
└──────────────────────┴──────────────────────────────────┘

Inheritance: Task extends Future
  asyncio.Future
       ↑
  asyncio.Task (wraps a coroutine, drives it to completion)
```

```python
import asyncio

async def future_vs_task():
    loop = asyncio.get_running_loop()

    # Future: you set the result manually
    future = loop.create_future()
    # Someone/something must call future.set_result() or set_exception()
    loop.call_later(0.1, future.set_result, "manual")
    result = await future
    print(f"Future result: {result}")

    # Task: result comes from coroutine execution
    async def compute():
        await asyncio.sleep(0.1)
        return "automatic"

    task = asyncio.create_task(compute())
    # The task drives the coroutine - result is set automatically
    result = await task
    print(f"Task result: {result}")

    # Task IS a Future
    print(f"Task is Future subclass: {isinstance(task, asyncio.Future)}")

asyncio.run(future_vs_task())
```

### Setting Results and Exceptions

```python
import asyncio

async def future_results_and_exceptions():
    loop = asyncio.get_running_loop()

    # ─── Setting a result ───
    fut = loop.create_future()
    fut.set_result({"data": [1, 2, 3]})
    print(f"Result: {fut.result()}")

    # ─── Setting an exception ───
    fut2 = loop.create_future()
    fut2.set_exception(ValueError("Something went wrong"))
    try:
        result = fut2.result()  # Raises the stored exception
    except ValueError as e:
        print(f"Exception: {e}")

    # ─── Can only set once ───
    fut3 = loop.create_future()
    fut3.set_result(42)
    try:
        fut3.set_result(43)  # InvalidStateError!
    except asyncio.InvalidStateError as e:
        print(f"Cannot set twice: {e}")

    # ─── Pattern: Future as a one-shot event ───
    ready = loop.create_future()

    async def waiter():
        print("  Waiter: waiting for signal...")
        value = await ready
        print(f"  Waiter: got signal with value={value}")

    async def signaler():
        await asyncio.sleep(0.5)
        print("  Signaler: sending signal!")
        ready.set_result("go!")

    await asyncio.gather(waiter(), signaler())

asyncio.run(future_results_and_exceptions())
```

### Callbacks on Futures

```python
import asyncio

async def future_callbacks():
    loop = asyncio.get_running_loop()

    def on_complete(future: asyncio.Future):
        """Called when the future completes (with result OR exception)."""
        if future.exception():
            print(f"  Callback: future failed with {future.exception()}")
        else:
            print(f"  Callback: future resolved with {future.result()}")

    # Add callback before completion
    fut = loop.create_future()
    fut.add_done_callback(on_complete)
    fut.set_result("hello")  # Triggers callback

    await asyncio.sleep(0)  # Let callbacks execute

    # Multiple callbacks
    fut2 = loop.create_future()
    fut2.add_done_callback(lambda f: print(f"  CB1: {f.result()}"))
    fut2.add_done_callback(lambda f: print(f"  CB2: {f.result()}"))
    fut2.add_done_callback(lambda f: print(f"  CB3: {f.result()}"))
    fut2.set_result(42)

    await asyncio.sleep(0)

    # Remove callback
    fut3 = loop.create_future()
    fut3.add_done_callback(on_complete)
    removed = fut3.remove_done_callback(on_complete)
    print(f"  Removed {removed} callback(s)")
    fut3.set_result("no callback fires")

    await asyncio.sleep(0)

asyncio.run(future_callbacks())
```

### concurrent.futures Integration

```python
import asyncio
import concurrent.futures
import time
import math

def cpu_intensive(n: int) -> float:
    """CPU-bound work that should NOT run in the event loop."""
    return sum(math.sqrt(i) for i in range(n))

def blocking_io(path: str) -> str:
    """Blocking I/O that has no async equivalent."""
    time.sleep(1)  # Simulate slow disk read
    return f"Content of {path}"

async def executor_examples():
    loop = asyncio.get_running_loop()

    # ─── Thread pool executor (default for I/O-bound) ───
    print("Thread executor (I/O-bound):")
    start = time.perf_counter()
    results = await asyncio.gather(
        loop.run_in_executor(None, blocking_io, "/file1"),
        loop.run_in_executor(None, blocking_io, "/file2"),
        loop.run_in_executor(None, blocking_io, "/file3"),
    )
    print(f"  3 blocking reads in {time.perf_counter()-start:.2f}s")
    print(f"  Results: {results}")

    # ─── Process pool executor (for CPU-bound) ───
    print("\nProcess executor (CPU-bound):")
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        results = await asyncio.gather(
            loop.run_in_executor(pool, cpu_intensive, 5_000_000),
            loop.run_in_executor(pool, cpu_intensive, 5_000_000),
            loop.run_in_executor(pool, cpu_intensive, 5_000_000),
            loop.run_in_executor(pool, cpu_intensive, 5_000_000),
        )
    print(f"  4 CPU tasks in {time.perf_counter()-start:.2f}s")

    # ─── Custom thread pool with limit ───
    print("\nCustom thread pool:")
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=5,
        thread_name_prefix="async-io"
    )
    loop.set_default_executor(executor)
    result = await loop.run_in_executor(None, blocking_io, "/custom")
    print(f"  Result: {result}")
    executor.shutdown(wait=False)

asyncio.run(executor_examples())
```

### loop.run_in_executor()

```python
import asyncio
import concurrent.futures
import functools

async def run_in_executor_patterns():
    """Patterns for bridging sync and async code."""
    loop = asyncio.get_running_loop()

    # ─── Pattern 1: asyncio.to_thread (Python 3.9+, simplest) ───
    def sync_function(x, y):
        import time
        time.sleep(0.5)
        return x + y

    result = await asyncio.to_thread(sync_function, 3, 4)
    print(f"to_thread result: {result}")

    # ─── Pattern 2: Wrapping sync libraries ───
    class SyncDatabase:
        """Pretend this is a sync-only database library."""
        def query(self, sql: str) -> list:
            import time
            time.sleep(0.2)
            return [{"id": 1, "name": "Alice"}]

        def insert(self, table: str, data: dict) -> int:
            import time
            time.sleep(0.1)
            return 1

    class AsyncDatabase:
        """Async wrapper around the sync library."""
        def __init__(self):
            self._db = SyncDatabase()
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=10,
                thread_name_prefix="db"
            )

        async def query(self, sql: str) -> list:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor, self._db.query, sql
            )

        async def insert(self, table: str, data: dict) -> int:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor,
                functools.partial(self._db.insert, table, data)
            )

        async def close(self):
            self._executor.shutdown(wait=True)

    # Usage
    db = AsyncDatabase()
    results = await db.query("SELECT * FROM users")
    print(f"Query results: {results}")
    row_id = await db.insert("users", {"name": "Bob"})
    print(f"Inserted row: {row_id}")
    await db.close()

asyncio.run(run_in_executor_patterns())
```

### Example: Bridging Sync and Async Code

```python
import asyncio
import concurrent.futures
import time
from typing import Callable, TypeVar

T = TypeVar('T')

class AsyncBridge:
    """
    Complete bridge between synchronous and asynchronous worlds.
    Useful when integrating async code into existing sync applications
    or vice versa.
    """

    def __init__(self, max_threads: int = 10):
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_threads
        )

    async def run_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Run a synchronous function in a thread without blocking the loop."""
        loop = asyncio.get_running_loop()
        import functools
        bound = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(self._thread_pool, bound)

    @staticmethod
    def run_async(coro):
        """
        Run an async function from synchronous code.
        Creates a new event loop in a thread if needed.
        """
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - use nest_asyncio or thread
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                return pool.submit(asyncio.run, coro).result()
        except RuntimeError:
            # No running loop - safe to use asyncio.run
            return asyncio.run(coro)

    def close(self):
        self._thread_pool.shutdown(wait=True)

# ─── Demonstration ───

def legacy_sync_function(x: int, y: int) -> int:
    """Imagine this is deep in a sync library."""
    time.sleep(0.5)  # Blocking I/O
    return x * y

async def modern_async_function(name: str) -> str:
    """Modern async code."""
    await asyncio.sleep(0.3)
    return f"Hello, {name}!"

async def main():
    bridge = AsyncBridge()

    # Call sync from async
    result = await bridge.run_sync(legacy_sync_function, 6, 7)
    print(f"Sync→Async bridge: {result}")

    # Multiple sync calls concurrently (they run in threads)
    results = await asyncio.gather(
        bridge.run_sync(legacy_sync_function, 1, 2),
        bridge.run_sync(legacy_sync_function, 3, 4),
        bridge.run_sync(legacy_sync_function, 5, 6),
    )
    print(f"Concurrent sync calls: {results}")

    bridge.close()

asyncio.run(main())

# Call async from sync (e.g., from a script's main())
sync_result = AsyncBridge.run_async(modern_async_function("World"))
print(f"Async→Sync bridge: {sync_result}")
```

---

## 7. Async Queues

### asyncio.Queue, PriorityQueue, LifoQueue

```python
import asyncio
from dataclasses import dataclass, field
from typing import Any

async def queue_types_demo():
    """Demonstrate all three async queue types."""

    # ─── FIFO Queue (First In, First Out) ───
    fifo = asyncio.Queue(maxsize=5)
    await fifo.put("first")
    await fifo.put("second")
    await fifo.put("third")
    print(f"FIFO: {await fifo.get()}")  # "first"

    # ─── LIFO Queue (Last In, First Out / Stack) ───
    lifo = asyncio.LifoQueue(maxsize=5)
    await lifo.put("first")
    await lifo.put("second")
    await lifo.put("third")
    print(f"LIFO: {await lifo.get()}")  # "third"

    # ─── Priority Queue (lowest value first) ───
    @dataclass(order=True)
    class PrioritizedItem:
        priority: int
        item: Any = field(compare=False)

    pq = asyncio.PriorityQueue(maxsize=5)
    await pq.put(PrioritizedItem(3, "low priority"))
    await pq.put(PrioritizedItem(1, "high priority"))
    await pq.put(PrioritizedItem(2, "medium priority"))
    print(f"Priority: {(await pq.get()).item}")  # "high priority"

    # ─── Queue properties ───
    q = asyncio.Queue(maxsize=3)
    await q.put("a")
    await q.put("b")
    print(f"Size: {q.qsize()}")       # 2
    print(f"Empty: {q.empty()}")      # False
    print(f"Full: {q.full()}")        # False (need 3 for full)

asyncio.run(queue_types_demo())
```

### Producer-Consumer with Async Queues

```python
import asyncio
import random
import time

async def producer_consumer():
    """Classic producer-consumer pattern with async queue."""

    queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=10)

    async def producer(name: str, num_items: int):
        """Produces items and puts them in the queue."""
        for i in range(num_items):
            item = f"{name}-item-{i}"
            await queue.put(item)
            print(f"  [Producer {name}] Put: {item} (queue size: {queue.qsize()})")
            # Simulate variable production rate
            await asyncio.sleep(random.uniform(0.05, 0.2))
        print(f"  [Producer {name}] Done producing")

    async def consumer(name: str):
        """Consumes items from the queue."""
        while True:
            item = await queue.get()
            if item is None:  # Poison pill = shutdown signal
                queue.task_done()
                break
            # Simulate processing time
            await asyncio.sleep(random.uniform(0.1, 0.3))
            print(f"  [Consumer {name}] Processed: {item}")
            queue.task_done()
        print(f"  [Consumer {name}] Shutting down")

    # Start producers and consumers
    start = time.perf_counter()

    producers = [
        asyncio.create_task(producer("P1", 5)),
        asyncio.create_task(producer("P2", 5)),
    ]
    consumers = [
        asyncio.create_task(consumer("C1")),
        asyncio.create_task(consumer("C2")),
        asyncio.create_task(consumer("C3")),
    ]

    # Wait for all items to be produced
    await asyncio.gather(*producers)

    # Wait for all items to be processed
    await queue.join()

    # Send shutdown signals (one per consumer)
    for _ in consumers:
        await queue.put(None)

    # Wait for consumers to exit
    await asyncio.gather(*consumers)

    elapsed = time.perf_counter() - start
    print(f"\nAll done in {elapsed:.2f}s")

asyncio.run(producer_consumer())
```

### Backpressure with maxsize

```python
import asyncio
import time

async def backpressure_demo():
    """
    Queue maxsize creates natural backpressure:
    - Producer blocks when queue is full
    - This prevents unbounded memory growth
    """
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=3)

    async def fast_producer():
        """Produces items faster than they're consumed."""
        for i in range(10):
            start = time.perf_counter()
            await queue.put(i)  # BLOCKS when queue is full!
            wait_time = time.perf_counter() - start
            if wait_time > 0.01:
                print(f"  Producer: put {i} (waited {wait_time:.2f}s for space)")
            else:
                print(f"  Producer: put {i} (immediate)")

    async def slow_consumer():
        """Processes items slowly."""
        for _ in range(10):
            item = await queue.get()
            await asyncio.sleep(0.3)  # Slow processing
            print(f"  Consumer: processed {item}")
            queue.task_done()

    await asyncio.gather(fast_producer(), slow_consumer())

asyncio.run(backpressure_demo())
```

### Multiple Producers and Consumers

```python
import asyncio
import random
from dataclasses import dataclass
from typing import Optional

@dataclass
class WorkItem:
    id: int
    payload: str
    priority: int = 0

async def multi_producer_consumer():
    """Scalable pattern with multiple producers and consumers."""

    queue: asyncio.Queue[Optional[WorkItem]] = asyncio.Queue(maxsize=20)
    results: list[str] = []
    results_lock = asyncio.Lock()

    async def producer(producer_id: int, count: int):
        for i in range(count):
            item = WorkItem(
                id=producer_id * 100 + i,
                payload=f"data-{producer_id}-{i}",
                priority=random.randint(1, 5),
            )
            await queue.put(item)
            await asyncio.sleep(random.uniform(0.01, 0.05))

    async def consumer(consumer_id: int):
        processed = 0
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                break
            # Process the item
            await asyncio.sleep(random.uniform(0.02, 0.08))
            async with results_lock:
                results.append(f"C{consumer_id}:{item.id}")
            processed += 1
            queue.task_done()
        return processed

    num_producers = 3
    num_consumers = 5
    items_per_producer = 20

    # Start consumers
    consumer_tasks = [
        asyncio.create_task(consumer(i)) for i in range(num_consumers)
    ]

    # Start producers
    producer_tasks = [
        asyncio.create_task(producer(i, items_per_producer))
        for i in range(num_producers)
    ]

    # Wait for producers to finish
    await asyncio.gather(*producer_tasks)

    # Wait for queue to be fully processed
    await queue.join()

    # Send shutdown signals
    for _ in range(num_consumers):
        await queue.put(None)

    # Collect consumer results
    counts = await asyncio.gather(*consumer_tasks)

    print(f"Producers: {num_producers} × {items_per_producer} = "
          f"{num_producers * items_per_producer} items")
    print(f"Consumers processed: {dict(enumerate(counts))}")
    print(f"Total processed: {len(results)}")

asyncio.run(multi_producer_consumer())
```

### Example: Async Task Pipeline

```python
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class Document:
    id: int
    raw_text: str
    cleaned_text: Optional[str] = None
    tokens: Optional[list[str]] = None
    embedding: Optional[list[float]] = None

async def pipeline_demo():
    """
    Multi-stage async processing pipeline.

    Documents flow: Input → Clean → Tokenize → Embed → Output

    Each stage runs concurrently with its own consumer(s).
    """

    # Queues between stages
    raw_queue: asyncio.Queue[Optional[Document]] = asyncio.Queue(maxsize=10)
    cleaned_queue: asyncio.Queue[Optional[Document]] = asyncio.Queue(maxsize=10)
    tokenized_queue: asyncio.Queue[Optional[Document]] = asyncio.Queue(maxsize=10)
    output_queue: asyncio.Queue[Document] = asyncio.Queue()

    async def stage_clean(worker_id: int):
        """Stage 1: Clean raw text."""
        while True:
            doc = await raw_queue.get()
            if doc is None:
                raw_queue.task_done()
                await cleaned_queue.put(None)
                break
            await asyncio.sleep(random.uniform(0.01, 0.03))
            doc.cleaned_text = doc.raw_text.strip().lower()
            await cleaned_queue.put(doc)
            raw_queue.task_done()

    async def stage_tokenize(worker_id: int):
        """Stage 2: Tokenize cleaned text."""
        none_count = 0
        while True:
            doc = await cleaned_queue.get()
            if doc is None:
                none_count += 1
                cleaned_queue.task_done()
                if none_count >= 2:  # Wait for all cleaners
                    await tokenized_queue.put(None)
                    break
                continue
            await asyncio.sleep(random.uniform(0.02, 0.05))
            doc.tokens = doc.cleaned_text.split()
            await tokenized_queue.put(doc)
            cleaned_queue.task_done()

    async def stage_embed(worker_id: int):
        """Stage 3: Generate embedding (slow - simulates ML model)."""
        while True:
            doc = await tokenized_queue.get()
            if doc is None:
                tokenized_queue.task_done()
                break
            await asyncio.sleep(random.uniform(0.05, 0.1))
            doc.embedding = [random.random() for _ in range(4)]
            await output_queue.put(doc)
            tokenized_queue.task_done()

    # Feed documents into pipeline
    documents = [
        Document(id=i, raw_text=f"  Document {i} has SOME text  ")
        for i in range(20)
    ]

    start = time.perf_counter()

    # Start pipeline stages (multiple workers per stage)
    cleaners = [asyncio.create_task(stage_clean(i)) for i in range(2)]
    tokenizers = [asyncio.create_task(stage_tokenize(i)) for i in range(1)]
    embedders = [asyncio.create_task(stage_embed(i)) for i in range(3)]

    # Feed input
    for doc in documents:
        await raw_queue.put(doc)
    for _ in cleaners:
        await raw_queue.put(None)  # Shutdown signals

    # Wait for pipeline to complete
    await asyncio.gather(*cleaners, *tokenizers, *embedders)

    # Collect results
    results = []
    while not output_queue.empty():
        results.append(await output_queue.get())

    elapsed = time.perf_counter() - start
    print(f"Pipeline processed {len(results)} documents in {elapsed:.2f}s")
    print(f"Sample result: {results[0]}")

asyncio.run(pipeline_demo())
```

### Example: Web Crawler

```python
import asyncio
import random
from collections import defaultdict
from urllib.parse import urljoin, urlparse

async def web_crawler():
    """
    Async web crawler demonstrating queues for URL frontier management.
    """
    url_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    visited: set[str] = set()
    results: dict[str, list[str]] = {}  # url -> [links]

    async def fetch_page(url: str) -> tuple[str, list[str]]:
        """Simulate fetching a page and extracting links."""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        # Simulate finding links on the page
        domain = urlparse(url).netloc or "example.com"
        num_links = random.randint(1, 5)
        links = [
            f"https://{domain}/page/{random.randint(1, 50)}"
            for _ in range(num_links)
        ]
        return url, links

    async def crawler_worker(worker_id: int, max_pages: int):
        """Worker that crawls pages from the queue."""
        pages_crawled = 0
        while pages_crawled < max_pages:
            try:
                url = await asyncio.wait_for(url_queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                break

            if url in visited:
                url_queue.task_done()
                continue

            visited.add(url)
            try:
                page_url, links = await fetch_page(url)
                results[page_url] = links
                pages_crawled += 1

                # Add discovered links to queue
                for link in links:
                    if link not in visited and not url_queue.full():
                        try:
                            url_queue.put_nowait(link)
                        except asyncio.QueueFull:
                            pass
            finally:
                url_queue.task_done()

        return pages_crawled

    # Seed URLs
    seed_urls = [
        "https://example.com/page/1",
        "https://example.com/page/2",
        "https://example.com/page/3",
    ]
    for url in seed_urls:
        await url_queue.put(url)

    # Launch crawler workers
    workers = [
        asyncio.create_task(crawler_worker(i, max_pages=10))
        for i in range(5)
    ]

    counts = await asyncio.gather(*workers)

    print(f"Crawled {sum(counts)} pages with {len(workers)} workers")
    print(f"Total unique pages: {len(results)}")
    print(f"Worker distribution: {list(counts)}")

asyncio.run(web_crawler())
```

---

## 8. Async Locks

### asyncio.Lock

```python
import asyncio

async def lock_demo():
    """
    asyncio.Lock - mutual exclusion for coroutines.
    Ensures only one coroutine accesses a shared resource at a time.
    """
    lock = asyncio.Lock()
    shared_resource = {"balance": 1000}

    async def transfer(from_acc: str, amount: int, name: str):
        # Without lock: race condition between read and write
        async with lock:
            print(f"  [{name}] Acquired lock, balance: {shared_resource['balance']}")
            current = shared_resource["balance"]
            await asyncio.sleep(0.1)  # Simulate I/O
            shared_resource["balance"] = current - amount
            print(f"  [{name}] Withdrew {amount}, new balance: "
                  f"{shared_resource['balance']}")
        # Lock released here

    # Multiple concurrent withdrawals
    await asyncio.gather(
        transfer("main", 200, "T1"),
        transfer("main", 300, "T2"),
        transfer("main", 100, "T3"),
    )
    print(f"Final balance: {shared_resource['balance']}")  # Always 400

asyncio.run(lock_demo())
```

### asyncio.Semaphore

```python
import asyncio
import time

async def semaphore_demo():
    """
    Semaphore limits concurrent access to a resource.
    Unlike Lock (allows 1), Semaphore allows N concurrent accesses.
    """
    # Allow max 3 concurrent operations
    semaphore = asyncio.Semaphore(3)
    active = 0

    async def limited_operation(name: str):
        nonlocal active
        async with semaphore:
            active += 1
            print(f"  [{name}] Started (active: {active}/3)")
            await asyncio.sleep(0.5)
            active -= 1
            print(f"  [{name}] Done (active: {active}/3)")

    start = time.perf_counter()
    # Launch 9 tasks but only 3 run at a time
    await asyncio.gather(*[
        limited_operation(f"Op-{i}") for i in range(9)
    ])
    elapsed = time.perf_counter() - start
    print(f"Total time: {elapsed:.2f}s (expected ~1.5s for 9 ops / 3 concurrent)")

asyncio.run(semaphore_demo())
```

### asyncio.BoundedSemaphore

```python
import asyncio

async def bounded_semaphore_demo():
    """
    BoundedSemaphore: like Semaphore but raises ValueError if
    released more times than acquired. Catches bugs!
    """
    sem = asyncio.BoundedSemaphore(2)

    # Normal usage - fine
    await sem.acquire()
    sem.release()

    # Bug detection: extra release
    await sem.acquire()
    sem.release()
    try:
        sem.release()  # ValueError! Counter would exceed initial value
    except ValueError as e:
        print(f"BoundedSemaphore caught bug: {e}")

    # Regular Semaphore would silently allow this (dangerous)
    regular_sem = asyncio.Semaphore(2)
    await regular_sem.acquire()
    regular_sem.release()
    regular_sem.release()  # No error! But now allows 3 concurrent (BUG)

asyncio.run(bounded_semaphore_demo())
```

### asyncio.Event

```python
import asyncio

async def event_demo():
    """
    Event: simple signaling mechanism.
    Multiple coroutines can wait for a signal.
    """
    event = asyncio.Event()

    async def waiter(name: str):
        print(f"  [{name}] Waiting for event...")
        await event.wait()
        print(f"  [{name}] Event received! Proceeding.")

    async def setter():
        print("  [Setter] Doing setup work...")
        await asyncio.sleep(1)
        print("  [Setter] Setting event!")
        event.set()  # All waiters are unblocked

    # Multiple waiters + one setter
    await asyncio.gather(
        waiter("W1"),
        waiter("W2"),
        waiter("W3"),
        setter(),
    )

    # Event stays set - new waiters pass immediately
    print(f"\n  Event is set: {event.is_set()}")
    await event.wait()  # Returns immediately
    print("  New wait returned immediately")

    # Clear and reuse
    event.clear()
    print(f"  Event is set after clear: {event.is_set()}")

asyncio.run(event_demo())
```

### asyncio.Condition

```python
import asyncio

async def condition_demo():
    """
    Condition: combines lock + notification mechanism.
    Allows coroutines to wait for specific conditions.
    """
    condition = asyncio.Condition()
    items: list[int] = []

    async def consumer(name: str, target: int):
        """Wait until there are at least 'target' items."""
        async with condition:
            # wait_for() releases lock, waits for predicate, reacquires
            await condition.wait_for(lambda: len(items) >= target)
            consumed = items[:target]
            del items[:target]
            print(f"  [{name}] Consumed {consumed} (needed {target})")

    async def producer():
        """Produce items and notify waiters."""
        for i in range(10):
            await asyncio.sleep(0.2)
            async with condition:
                items.append(i)
                print(f"  [Producer] Added {i}, total: {len(items)}")
                condition.notify_all()  # Wake all waiters to check condition

    await asyncio.gather(
        consumer("C1", 3),  # Wants 3 items
        consumer("C2", 5),  # Wants 5 items
        producer(),
    )

asyncio.run(condition_demo())
```

### asyncio.Barrier (Python 3.11+)

```python
import asyncio

async def barrier_demo():
    """
    Barrier: synchronization point where N coroutines must
    all arrive before any can proceed.
    """
    num_workers = 4
    barrier = asyncio.Barrier(num_workers)

    async def worker(name: str, prep_time: float):
        # Phase 1: Preparation (different durations)
        print(f"  [{name}] Preparing... ({prep_time:.1f}s)")
        await asyncio.sleep(prep_time)
        print(f"  [{name}] Ready! Waiting at barrier...")

        # All workers must reach here before any can continue
        await barrier.wait()

        # Phase 2: All proceed together
        print(f"  [{name}] Barrier passed! Running synchronized work.")

    print("Workers must all reach the barrier before continuing:")
    await asyncio.gather(
        worker("W1", 0.5),
        worker("W2", 1.0),
        worker("W3", 0.3),
        worker("W4", 0.8),
    )

asyncio.run(barrier_demo())
```

### When You Need Async Locks

```python
"""
When to use each synchronization primitive:

Lock:
  - Protecting shared mutable state between await points
  - Ensuring exclusive access to a resource

Semaphore:
  - Rate limiting (max N concurrent operations)
  - Connection pooling
  - Resource pools (database connections, file handles)

Event:
  - One-time signals (initialization complete, shutdown requested)
  - Pub/sub within a single application

Condition:
  - Complex wait conditions (wait until queue has N items)
  - Producer-consumer with specific requirements

Barrier:
  - Phased computation (all workers sync before next phase)
  - Testing (synchronize test steps)
"""
```

### Example: Rate Limiter with Semaphore

```python
import asyncio
import time
from collections import deque

class AsyncRateLimiter:
    """
    Token bucket rate limiter using async primitives.
    Allows burst up to max_tokens, refills at rate tokens/second.
    """

    def __init__(self, rate: float, max_tokens: int):
        self.rate = rate            # Tokens per second
        self.max_tokens = max_tokens
        self._tokens = max_tokens
        self._lock = asyncio.Lock()
        self._last_refill = time.monotonic()

    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
            # No tokens available - wait a bit and retry
            await asyncio.sleep(1.0 / self.rate)

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * self.rate
        self._tokens = min(self.max_tokens, self._tokens + new_tokens)
        self._last_refill = now

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        pass

async def rate_limiter_demo():
    """Demonstrate rate-limited API calls."""
    # 5 requests per second, burst of 3
    limiter = AsyncRateLimiter(rate=5, max_tokens=3)
    request_times: list[float] = []

    async def make_request(request_id: int):
        async with limiter:
            now = time.perf_counter()
            request_times.append(now)
            print(f"  Request {request_id:2d} at t={now - request_times[0]:.3f}s")
            await asyncio.sleep(0.05)  # Simulate request

    start = time.perf_counter()
    # Fire 15 requests - should take ~3 seconds at 5/s
    await asyncio.gather(*[make_request(i) for i in range(15)])
    elapsed = time.perf_counter() - start
    print(f"\n  15 requests completed in {elapsed:.2f}s "
          f"(rate limited to 5/s)")

asyncio.run(rate_limiter_demo())
```

### Example: Resource Pool

```python
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Generic, TypeVar

T = TypeVar('T')

class AsyncPool(Generic[T]):
    """
    Generic async resource pool with connection lifecycle management.
    Similar to database connection pools.
    """

    def __init__(self, factory, max_size: int = 10, min_size: int = 2):
        self._factory = factory
        self._max_size = max_size
        self._min_size = min_size
        self._pool: asyncio.Queue[T] = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Pre-create minimum connections."""
        for _ in range(self._min_size):
            resource = await self._factory()
            await self._pool.put(resource)
            self._size += 1

    @asynccontextmanager
    async def acquire(self):
        """Acquire a resource from the pool."""
        resource = await self._get()
        try:
            yield resource
        finally:
            await self._pool.put(resource)

    async def _get(self) -> T:
        """Get a resource, creating new one if pool is empty and under limit."""
        try:
            return self._pool.get_nowait()
        except asyncio.QueueEmpty:
            async with self._lock:
                if self._size < self._max_size:
                    resource = await self._factory()
                    self._size += 1
                    return resource
            # At max capacity - wait for one to be returned
            return await self._pool.get()

    @property
    def stats(self) -> dict:
        return {
            "total": self._size,
            "available": self._pool.qsize(),
            "in_use": self._size - self._pool.qsize(),
        }

async def pool_demo():
    """Demonstrate connection pool usage."""

    class FakeConnection:
        _counter = 0

        def __init__(self, conn_id: int):
            self.id = conn_id
            self.queries_executed = 0

        async def query(self, sql: str) -> str:
            await asyncio.sleep(0.1)
            self.queries_executed += 1
            return f"[Conn-{self.id}] Result for: {sql}"

    async def connection_factory() -> FakeConnection:
        FakeConnection._counter += 1
        conn = FakeConnection(FakeConnection._counter)
        await asyncio.sleep(0.05)  # Simulate connection setup
        print(f"  Created connection {conn.id}")
        return conn

    # Create pool with max 3 connections
    pool = AsyncPool(connection_factory, max_size=3, min_size=1)
    await pool.initialize()

    async def do_work(task_id: int):
        async with pool.acquire() as conn:
            result = await conn.query(f"SELECT * FROM task_{task_id}")
            print(f"  Task {task_id}: {result} | Pool: {pool.stats}")

    # 6 tasks sharing 3 connections
    await asyncio.gather(*[do_work(i) for i in range(6)])
    print(f"\nFinal pool stats: {pool.stats}")

asyncio.run(pool_demo())
```

---

## 9. Cancellation

### task.cancel()

```python
import asyncio

async def cancellation_basics():
    """Basic task cancellation mechanics."""

    async def long_running():
        print("  Starting long operation...")
        try:
            await asyncio.sleep(10)
            print("  Completed!")  # Never reached
            return "result"
        except asyncio.CancelledError:
            print("  Caught cancellation!")
            raise  # MUST re-raise unless you want to suppress

    task = asyncio.create_task(long_running())

    # Let it start
    await asyncio.sleep(0.1)

    # Cancel it
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print(f"  Task was cancelled: {task.cancelled()}")

asyncio.run(cancellation_basics())
```

### CancelledError Handling

```python
import asyncio

async def cancellation_handling():
    """Different strategies for handling cancellation."""

    # ─── Strategy 1: Cleanup then re-raise ───
    async def with_cleanup():
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            print("  Cleaning up resources...")
            await asyncio.sleep(0.1)  # Async cleanup is OK!
            print("  Cleanup done")
            raise  # Always re-raise!

    # ─── Strategy 2: Suppress cancellation (rare, use carefully) ───
    async def suppress_cancel():
        """Sometimes you need to finish critical work."""
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            print("  Suppressing cancel to finish critical section...")
            # NOT re-raising - the task will NOT be cancelled
            return "completed anyway"

    # ─── Strategy 3: Partial work with cancellation ───
    async def partial_work():
        """Return partial results on cancellation."""
        results = []
        try:
            for i in range(100):
                await asyncio.sleep(0.1)
                results.append(i)
        except asyncio.CancelledError:
            print(f"  Cancelled after {len(results)} items")
            # Re-raise but the results are captured in the traceback
            raise

    # Demonstrate
    task1 = asyncio.create_task(with_cleanup())
    await asyncio.sleep(0.1)
    task1.cancel()
    try:
        await task1
    except asyncio.CancelledError:
        print("  Task1: properly cancelled after cleanup\n")

    task2 = asyncio.create_task(suppress_cancel())
    await asyncio.sleep(0.1)
    task2.cancel()
    result = await task2  # NOT cancelled!
    print(f"  Task2: suppressed, result = {result}\n")

    task3 = asyncio.create_task(partial_work())
    await asyncio.sleep(0.35)
    task3.cancel()
    try:
        await task3
    except asyncio.CancelledError:
        print("  Task3: properly cancelled")

asyncio.run(cancellation_handling())
```

### Shielding from Cancellation (asyncio.shield)

```python
import asyncio

async def shield_demo():
    """
    asyncio.shield() protects a coroutine from cancellation.
    The outer task can be cancelled, but the inner continues.
    """

    async def critical_database_write():
        """This MUST complete - don't cancel it."""
        print("  DB write starting...")
        await asyncio.sleep(0.5)
        print("  DB write completed!")
        return "data saved"

    async def shielded_task():
        try:
            # shield() wraps the inner coroutine
            result = await asyncio.shield(critical_database_write())
            return result
        except asyncio.CancelledError:
            # The outer task is cancelled, but critical_database_write
            # continues running in the background!
            print("  Outer cancelled, but DB write continues...")
            raise

    task = asyncio.create_task(shielded_task())
    await asyncio.sleep(0.1)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("  Main: task was cancelled")
        # Wait a moment for shielded coroutine to finish
        await asyncio.sleep(0.6)
        print("  Main: but the DB write should have completed")

asyncio.run(shield_demo())
```

### Cleanup on Cancellation

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource(name: str):
    """Resource that needs cleanup even on cancellation."""
    print(f"  [{name}] Acquired")
    try:
        yield name
    finally:
        # finally ALWAYS runs, even on CancelledError
        print(f"  [{name}] Releasing (cleanup)...")
        # Can do async cleanup in finally
        await asyncio.sleep(0.05)
        print(f"  [{name}] Released")

async def cleanup_on_cancel():
    """Demonstrate proper cleanup patterns."""

    async def work_with_resources():
        async with managed_resource("DB Connection") as db:
            async with managed_resource("File Handle") as fh:
                print(f"  Working with {db} and {fh}...")
                await asyncio.sleep(10)  # Long work
                print("  Work done!")  # Never reached

    task = asyncio.create_task(work_with_resources())
    await asyncio.sleep(0.1)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("  Task cancelled - resources were properly cleaned up!")

asyncio.run(cleanup_on_cancel())
```

### Timeout Patterns

```python
import asyncio

async def timeout_patterns():
    """Various timeout patterns in asyncio."""

    async def slow_operation():
        await asyncio.sleep(5)
        return "done"

    # ─── Pattern 1: asyncio.timeout (Python 3.11+, recommended) ───
    print("Pattern 1: asyncio.timeout")
    try:
        async with asyncio.timeout(1.0):
            result = await slow_operation()
    except TimeoutError:
        print("  Timed out! (asyncio.timeout)")

    # ─── Pattern 2: asyncio.wait_for (older, still useful) ───
    print("\nPattern 2: asyncio.wait_for")
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=1.0)
    except asyncio.TimeoutError:
        print("  Timed out! (wait_for)")

    # ─── Pattern 3: asyncio.timeout with deadline ───
    print("\nPattern 3: Nested timeouts")
    try:
        async with asyncio.timeout(2.0) as outer:
            print(f"  Outer deadline: {outer.when():.2f}")
            try:
                async with asyncio.timeout(0.5) as inner:
                    print(f"  Inner deadline: {inner.when():.2f}")
                    await slow_operation()
            except TimeoutError:
                print("  Inner timed out, outer still active")
                # Can continue working under outer timeout
                await asyncio.sleep(0.5)
                print("  Continued after inner timeout")
    except TimeoutError:
        print("  Outer timed out!")

    # ─── Pattern 4: Reschedule timeout ───
    print("\nPattern 4: Reschedulable timeout")
    try:
        async with asyncio.timeout(1.0) as cm:
            await asyncio.sleep(0.5)
            # Extend the deadline!
            cm.reschedule(asyncio.get_event_loop().time() + 2.0)
            await asyncio.sleep(1.5)
            print("  Completed with extended deadline!")
    except TimeoutError:
        print("  Timed out even with extension")

asyncio.run(timeout_patterns())
```

### Example: Graceful Shutdown

```python
import asyncio
import signal
from typing import Set

class GracefulService:
    """
    Service that shuts down gracefully on SIGTERM/SIGINT.
    Finishes in-flight work, cleans up resources.
    """

    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._active_tasks: Set[asyncio.Task] = set()
        self._is_healthy = True

    async def start(self):
        """Start the service with signal handling."""
        loop = asyncio.get_running_loop()

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)

        print("Service started. Press Ctrl+C to shutdown.")

        # Main service loop
        try:
            workers = [
                asyncio.create_task(self._worker(i))
                for i in range(3)
            ]
            # Wait for shutdown signal
            await self._shutdown_event.wait()

            # Graceful shutdown sequence
            print("\nShutdown initiated...")
            self._is_healthy = False

            # 1. Stop accepting new work (signal is already set)
            # 2. Wait for in-flight tasks with timeout
            print(f"  Waiting for {len(self._active_tasks)} active tasks...")
            if self._active_tasks:
                try:
                    async with asyncio.timeout(5.0):
                        await asyncio.gather(*self._active_tasks,
                                           return_exceptions=True)
                except TimeoutError:
                    print("  Timeout! Cancelling remaining tasks...")
                    for task in self._active_tasks:
                        task.cancel()
                    await asyncio.gather(*self._active_tasks,
                                       return_exceptions=True)

            # 3. Cancel workers
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

            print("  Shutdown complete!")

        except Exception as e:
            print(f"  Error during shutdown: {e}")

    def _signal_handler(self, sig):
        print(f"\n  Received signal: {sig.name}")
        self._shutdown_event.set()

    async def _worker(self, worker_id: int):
        """Simulates a worker processing requests."""
        while not self._shutdown_event.is_set():
            task = asyncio.create_task(self._handle_request(worker_id))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)
            try:
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break

    async def _handle_request(self, worker_id: int):
        """Simulate handling a single request."""
        import random
        duration = random.uniform(0.1, 0.5)
        await asyncio.sleep(duration)
        print(f"  Worker-{worker_id}: processed request ({duration:.2f}s)")

async def main():
    service = GracefulService()
    # For demo: auto-shutdown after 2 seconds
    async def auto_shutdown():
        await asyncio.sleep(2)
        service._shutdown_event.set()

    await asyncio.gather(
        service.start(),
        auto_shutdown(),
    )

asyncio.run(main())
```

### Example: Request Timeouts

```python
import asyncio
import random
from dataclasses import dataclass
from typing import Optional

@dataclass
class Response:
    status: int
    body: str
    elapsed: float

async def request_with_timeout():
    """Pattern for HTTP-like requests with proper timeout handling."""

    async def make_request(
        url: str,
        timeout: float = 5.0,
        retries: int = 3,
    ) -> Response:
        """Make a request with timeout and retries."""
        import time

        for attempt in range(retries):
            start = time.perf_counter()
            try:
                async with asyncio.timeout(timeout):
                    # Simulate variable latency
                    latency = random.uniform(0.1, 3.0)
                    await asyncio.sleep(latency)

                    if random.random() < 0.2:
                        raise ConnectionError("Server error")

                    elapsed = time.perf_counter() - start
                    return Response(200, f"OK from {url}", elapsed)

            except TimeoutError:
                elapsed = time.perf_counter() - start
                print(f"  Attempt {attempt+1}: Timeout after {elapsed:.2f}s")
                if attempt == retries - 1:
                    return Response(408, "Request Timeout", elapsed)
                # Exponential backoff before retry
                await asyncio.sleep(0.1 * (2 ** attempt))

            except ConnectionError as e:
                elapsed = time.perf_counter() - start
                print(f"  Attempt {attempt+1}: {e} after {elapsed:.2f}s")
                if attempt == retries - 1:
                    return Response(503, str(e), elapsed)
                await asyncio.sleep(0.1 * (2 ** attempt))

        return Response(500, "Unknown error", 0)

    # Make several requests concurrently
    urls = [f"https://api.example.com/resource/{i}" for i in range(5)]
    responses = await asyncio.gather(*[
        make_request(url, timeout=1.5, retries=2) for url in urls
    ])

    print("\nResults:")
    for url, resp in zip(urls, responses):
        status_emoji = "OK" if resp.status == 200 else "FAIL"
        print(f"  [{status_emoji}] {url}: status={resp.status}, "
              f"time={resp.elapsed:.2f}s")

asyncio.run(request_with_timeout())
```

---

## 10. Backpressure

### What is Backpressure

Backpressure is a mechanism for a slow consumer to signal a fast producer to slow down, preventing unbounded resource growth (memory, connections, etc.).

```
Without Backpressure:
┌──────────┐  100/s   ┌───────────────────────────┐  10/s   ┌──────────┐
│ Producer │─────────▶│ Buffer (growing forever!) │─────────▶│ Consumer │
└──────────┘          └───────────────────────────┘          └──────────┘
                       ↑ Memory keeps growing! OOM crash! ↑

With Backpressure:
┌──────────┐  10/s    ┌─────────────┐  10/s   ┌──────────┐
│ Producer │─────────▶│ Buffer (10) │─────────▶│ Consumer │
│ (slowed) │          │ (bounded)   │          │          │
└──────────┘          └─────────────┘          └──────────┘
  ↑ Producer blocks when buffer is full (or drops items)
```

### Why It Matters in Async Systems

```python
import asyncio
import sys

async def without_backpressure_demo():
    """Shows what happens without backpressure: memory explosion."""

    unbounded_buffer: list[bytes] = []

    async def fast_producer():
        """Produces data much faster than consumer processes it."""
        for i in range(1000):
            data = b"x" * 10000  # 10KB per item
            unbounded_buffer.append(data)
            await asyncio.sleep(0.001)  # 1000 items/second
            if i % 100 == 0:
                mem_mb = sys.getsizeof(unbounded_buffer) / 1024 / 1024
                print(f"  Buffer size: {len(unbounded_buffer)}, "
                      f"~{mem_mb:.1f}MB")

    async def slow_consumer():
        """Processes data slowly."""
        while True:
            if unbounded_buffer:
                unbounded_buffer.pop(0)
                await asyncio.sleep(0.1)  # Only 10 items/second!
            else:
                await asyncio.sleep(0.01)

    # Run for a short time to demonstrate
    producer = asyncio.create_task(fast_producer())
    consumer = asyncio.create_task(slow_consumer())
    await producer
    consumer.cancel()
    print(f"  Final buffer size: {len(unbounded_buffer)} items!")
    print("  In production, this leads to OOM!")

asyncio.run(without_backpressure_demo())
```

### Implementing Backpressure with Queues

```python
import asyncio
import time

async def queue_backpressure():
    """Bounded queue naturally provides backpressure."""

    stats = {"produced": 0, "consumed": 0, "producer_waits": 0}
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=5)

    async def producer():
        for i in range(30):
            start = time.perf_counter()
            await queue.put(i)  # Blocks when queue is full!
            wait = time.perf_counter() - start
            if wait > 0.01:
                stats["producer_waits"] += 1
            stats["produced"] += 1
            await asyncio.sleep(0.02)  # Fast: 50/s

    async def consumer():
        while stats["produced"] < 30 or not queue.empty():
            try:
                item = await asyncio.wait_for(queue.get(), timeout=1.0)
                await asyncio.sleep(0.1)  # Slow: 10/s
                stats["consumed"] += 1
                queue.task_done()
            except asyncio.TimeoutError:
                break

    start = time.perf_counter()
    await asyncio.gather(producer(), consumer())
    elapsed = time.perf_counter() - start

    print(f"  Produced: {stats['produced']}")
    print(f"  Consumed: {stats['consumed']}")
    print(f"  Producer blocked: {stats['producer_waits']} times")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Max buffer size was always <= 5 (queue maxsize)")

asyncio.run(queue_backpressure())
```

### Flow Control in Streams

```python
import asyncio

async def stream_flow_control():
    """
    asyncio streams have built-in flow control via
    writer.drain() and transport pause/resume.
    """

    async def handle_client(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter):
        """Echo server with flow control."""
        addr = writer.get_extra_info('peername')
        print(f"  Client connected: {addr}")

        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break

                writer.write(data)
                # drain() implements backpressure:
                # If the write buffer is too full, it pauses until
                # the OS has sent enough data
                await writer.drain()
        except ConnectionResetError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"  Client disconnected: {addr}")

    # In production, you'd start the server:
    # server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    # async with server:
    #     await server.serve_forever()
    print("  Stream flow control uses writer.drain() for backpressure")
    print("  When write buffer is full, drain() pauses the coroutine")
    print("  The OS TCP stack also provides flow control (TCP window)")

asyncio.run(stream_flow_control())
```

### Strategies: Drop, Buffer, Block, Signal

```python
import asyncio
import time
from enum import Enum
from typing import Optional

class BackpressureStrategy(Enum):
    DROP = "drop"        # Drop newest items when full
    BUFFER = "buffer"    # Bounded buffer, block when full
    BLOCK = "block"      # Block producer until consumer catches up
    SIGNAL = "signal"    # Signal producer to slow down

class AdaptiveBuffer:
    """
    Buffer with configurable backpressure strategies.
    """

    def __init__(self, maxsize: int, strategy: BackpressureStrategy):
        self.maxsize = maxsize
        self.strategy = strategy
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._dropped = 0
        self._slow_down = asyncio.Event()
        self._slow_down.set()  # Start unblocked

    async def put(self, item) -> bool:
        """Put item, returns False if dropped."""
        if self.strategy == BackpressureStrategy.DROP:
            try:
                self._queue.put_nowait(item)
                return True
            except asyncio.QueueFull:
                self._dropped += 1
                return False

        elif self.strategy == BackpressureStrategy.BLOCK:
            await self._queue.put(item)  # Blocks when full
            return True

        elif self.strategy == BackpressureStrategy.SIGNAL:
            # Wait if signaled to slow down
            await self._slow_down.wait()
            await self._queue.put(item)
            # Signal slow-down when nearly full
            if self._queue.qsize() >= self.maxsize * 0.8:
                self._slow_down.clear()
            return True

        return True

    async def get(self):
        item = await self._queue.get()
        # Un-signal when buffer drains
        if self.strategy == BackpressureStrategy.SIGNAL:
            if self._queue.qsize() < self.maxsize * 0.5:
                self._slow_down.set()
        return item

    @property
    def stats(self) -> dict:
        return {
            "size": self._queue.qsize(),
            "dropped": self._dropped,
            "capacity": self.maxsize,
        }

async def compare_strategies():
    """Compare different backpressure strategies."""

    for strategy in BackpressureStrategy:
        buf = AdaptiveBuffer(maxsize=5, strategy=strategy)
        produced = 0
        consumed = 0

        async def producer():
            nonlocal produced
            for i in range(20):
                success = await buf.put(i)
                produced += 1
                await asyncio.sleep(0.01)

        async def consumer():
            nonlocal consumed
            for _ in range(20):
                try:
                    item = await asyncio.wait_for(buf.get(), timeout=2.0)
                    consumed += 1
                    await asyncio.sleep(0.05)  # 5x slower than producer
                except asyncio.TimeoutError:
                    break

        await asyncio.gather(producer(), consumer())
        print(f"  {strategy.value:8s}: produced={produced}, consumed={consumed}, "
              f"dropped={buf.stats['dropped']}")

asyncio.run(compare_strategies())
```

### Example: Rate-Limited Consumer

```python
import asyncio
import time

async def rate_limited_consumer_demo():
    """
    Consumer that processes at a controlled rate regardless of
    how fast items arrive.
    """

    class RateLimitedConsumer:
        def __init__(self, rate_per_second: float, buffer_size: int = 100):
            self.interval = 1.0 / rate_per_second
            self._queue: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
            self._processed = 0
            self._running = True

        async def submit(self, item):
            """Submit item for processing. Blocks if buffer full."""
            await self._queue.put(item)

        async def run(self):
            """Process items at the configured rate."""
            while self._running or not self._queue.empty():
                try:
                    item = await asyncio.wait_for(
                        self._queue.get(), timeout=1.0
                    )
                    await self._process(item)
                    self._processed += 1
                    await asyncio.sleep(self.interval)
                except asyncio.TimeoutError:
                    if not self._running:
                        break

        async def _process(self, item):
            """Override for actual processing logic."""
            pass

        def stop(self):
            self._running = False

    # Demo: fast producer, rate-limited consumer
    consumer = RateLimitedConsumer(rate_per_second=5, buffer_size=10)

    async def fast_producer():
        """Produces 30 items as fast as possible."""
        for i in range(30):
            await consumer.submit(f"item-{i}")
            print(f"  Submitted item-{i} (queue: {consumer._queue.qsize()})")
            await asyncio.sleep(0.02)

    start = time.perf_counter()

    producer_task = asyncio.create_task(fast_producer())
    consumer_task = asyncio.create_task(consumer.run())

    await producer_task
    consumer.stop()
    await consumer_task

    elapsed = time.perf_counter() - start
    print(f"\n  Processed {consumer._processed} items in {elapsed:.2f}s")
    print(f"  Effective rate: {consumer._processed/elapsed:.1f}/s "
          f"(target: 5/s)")

asyncio.run(rate_limited_consumer_demo())
```

### Example: TCP Server with Backpressure

```python
import asyncio

async def tcp_backpressure_server():
    """
    TCP server demonstrating write-side backpressure.
    Pauses reading from client when write buffer is full.
    """

    HIGH_WATER = 64 * 1024   # Pause reading at 64KB pending
    LOW_WATER = 16 * 1024    # Resume reading at 16KB pending

    class BackpressureProtocol(asyncio.Protocol):
        def __init__(self):
            self.transport: asyncio.Transport = None
            self.paused = False
            self.bytes_received = 0
            self.bytes_sent = 0

        def connection_made(self, transport: asyncio.Transport):
            self.transport = transport
            # Set write buffer limits for automatic pause/resume
            transport.set_write_buffer_limits(
                high=HIGH_WATER,
                low=LOW_WATER,
            )
            peer = transport.get_extra_info('peername')
            print(f"  Connection from {peer}")

        def data_received(self, data: bytes):
            self.bytes_received += len(data)
            # Echo back (with potential backpressure)
            self.transport.write(data)
            self.bytes_sent += len(data)

        def pause_writing(self):
            """Called when write buffer exceeds high water mark."""
            print("  BACKPRESSURE: Pausing reads (buffer full)")
            self.paused = True
            self.transport.pause_reading()

        def resume_writing(self):
            """Called when write buffer drops below low water mark."""
            print("  BACKPRESSURE: Resuming reads (buffer drained)")
            self.paused = False
            self.transport.resume_reading()

        def connection_lost(self, exc):
            print(f"  Connection lost. Sent: {self.bytes_sent}, "
                  f"Received: {self.bytes_received}")

    print("TCP server with backpressure:")
    print(f"  High water mark: {HIGH_WATER} bytes")
    print(f"  Low water mark: {LOW_WATER} bytes")
    print("  When write buffer exceeds high water, reading pauses")
    print("  This prevents memory exhaustion from fast senders")

    # In production:
    # loop = asyncio.get_running_loop()
    # server = await loop.create_server(
    #     BackpressureProtocol, '0.0.0.0', 8888
    # )

asyncio.run(tcp_backpressure_server())
```

---

## 11. Structured Concurrency

### Problems with Unstructured Concurrency

```python
import asyncio

async def unstructured_problems():
    """
    Problems with fire-and-forget / unstructured concurrent code:
    1. Lost exceptions (silent failures)
    2. Resource leaks (tasks outlive their context)
    3. Unpredictable lifetimes
    4. Hard to reason about error handling
    """

    # Problem 1: Lost exception
    async def failing_task():
        await asyncio.sleep(0.1)
        raise RuntimeError("This error is LOST!")

    # Fire and forget - exception is never seen!
    task = asyncio.create_task(failing_task())
    await asyncio.sleep(0.5)
    # If we never await `task`, the exception is silently swallowed
    # (Python may print a warning at GC time, but it's easy to miss)

    # Problem 2: Task outlives its logical scope
    async def leaked_task():
        while True:
            await asyncio.sleep(1)
            print("  Still running! (leaked)")

    async def start_something():
        asyncio.create_task(leaked_task())
        # The task runs FOREVER after this function returns!
        return "done"

    result = await start_something()
    # leaked_task is still running... who will cancel it?

    print("Unstructured concurrency = bugs waiting to happen!")

# (Don't actually run this - it would leak tasks)
```

### TaskGroup (Python 3.11+)

```python
import asyncio
import random

async def task_group_comprehensive():
    """
    TaskGroup provides structured concurrency:
    - All tasks have a clear owner (the group)
    - If one fails, all others are cancelled
    - Exceptions are collected and reported together
    - Resources are cleaned up deterministically
    """

    # ─── Basic TaskGroup ───
    print("=== Basic TaskGroup ===")
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(asyncio.sleep(0.1, result="A"))
        task2 = tg.create_task(asyncio.sleep(0.2, result="B"))
        task3 = tg.create_task(asyncio.sleep(0.15, result="C"))
    # ALL tasks guaranteed complete when we exit the `async with`
    print(f"  Results: {task1.result()}, {task2.result()}, {task3.result()}")

    # ─── Dynamic task creation in a group ───
    print("\n=== Dynamic Tasks ===")
    results = []
    async with asyncio.TaskGroup() as tg:
        for i in range(5):
            async def work(n=i):
                await asyncio.sleep(random.uniform(0.1, 0.3))
                results.append(n * 10)
            tg.create_task(work())
    print(f"  Dynamic results: {sorted(results)}")

    # ─── Nested TaskGroups ───
    print("\n=== Nested TaskGroups ===")
    async def phase(name: str, subtasks: int):
        async with asyncio.TaskGroup() as tg:
            for i in range(subtasks):
                tg.create_task(asyncio.sleep(0.1, result=f"{name}-{i}"))
        print(f"  Phase {name} complete")

    async with asyncio.TaskGroup() as tg:
        tg.create_task(phase("A", 3))
        tg.create_task(phase("B", 2))
        tg.create_task(phase("C", 4))
    print("  All phases complete!")

asyncio.run(task_group_comprehensive())
```

### Exception Propagation in Groups

```python
import asyncio

async def exception_propagation():
    """
    TaskGroup collects ALL exceptions and raises ExceptionGroup.
    Uses except* syntax (Python 3.11+) for handling.
    """

    async def success_task(n: int):
        await asyncio.sleep(0.1)
        return f"success-{n}"

    async def value_error_task(n: int):
        await asyncio.sleep(0.05)
        raise ValueError(f"Bad value in task {n}")

    async def type_error_task(n: int):
        await asyncio.sleep(0.08)
        raise TypeError(f"Wrong type in task {n}")

    # ─── Multiple exceptions of different types ───
    print("=== Multiple Exception Types ===")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(success_task(1))
            tg.create_task(value_error_task(2))
            tg.create_task(type_error_task(3))
            tg.create_task(value_error_task(4))
    except* ValueError as eg:
        print(f"  ValueErrors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"    - {e}")
    except* TypeError as eg:
        print(f"  TypeErrors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"    - {e}")

    # ─── Handling all exceptions uniformly ───
    print("\n=== Uniform Handling ===")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(value_error_task(1))
            tg.create_task(type_error_task(2))
    except* (ValueError, TypeError) as eg:
        print(f"  All errors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"    - {type(e).__name__}: {e}")

asyncio.run(exception_propagation())
```

### Cancellation Semantics

```python
import asyncio

async def cancellation_in_groups():
    """
    When one task in a group fails:
    1. All other tasks are cancelled
    2. The group waits for all cancellations to complete
    3. All exceptions (including CancelledErrors from healthy tasks) are collected
    """

    async def slow_success():
        try:
            await asyncio.sleep(5)
            return "would have succeeded"
        except asyncio.CancelledError:
            print("  [slow_success] Cancelled! Cleaning up...")
            await asyncio.sleep(0.05)  # Cleanup
            print("  [slow_success] Cleanup done")
            raise

    async def fast_failure():
        await asyncio.sleep(0.1)
        raise RuntimeError("I failed quickly!")

    print("=== Cancellation on failure ===")
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(slow_success())
            t2 = tg.create_task(fast_failure())
            # When fast_failure raises, slow_success gets cancelled
    except* RuntimeError as eg:
        print(f"  Error: {eg.exceptions[0]}")
        print(f"  Task 1 cancelled: {t1.cancelled()}")
        print(f"  Task 2 done: {t2.done()}")

asyncio.run(cancellation_in_groups())
```

### Nursery Pattern (trio-style)

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def nursery():
    """
    Trio-inspired nursery pattern using TaskGroup.
    Ensures all child tasks complete before the scope exits.

    This pattern guarantees:
    - No task outlives its parent scope
    - All exceptions are propagated
    - Clean resource management
    """
    async with asyncio.TaskGroup() as tg:
        yield tg

async def nursery_pattern_demo():
    """Structured concurrency with the nursery pattern."""

    async def fetch_and_process(url: str, results: list):
        await asyncio.sleep(0.1)  # Simulate fetch
        results.append(f"processed-{url}")

    # Nursery guarantees all tasks finish before we proceed
    results = []
    async with nursery() as n:
        n.create_task(fetch_and_process("url1", results))
        n.create_task(fetch_and_process("url2", results))
        n.create_task(fetch_and_process("url3", results))
    # ALL tasks are done here
    assert len(results) == 3
    print(f"  Nursery results: {results}")

    # Nested nurseries for phased work
    print("\n  Phased execution:")
    async with nursery() as outer:
        async def phase(name: str):
            async with nursery() as inner:
                for i in range(3):
                    async def work(n=name, idx=i):
                        await asyncio.sleep(0.05)
                        print(f"    {n}-{idx} done")
                    inner.create_task(work())
            print(f"  Phase {name} complete")

        outer.create_task(phase("A"))
        outer.create_task(phase("B"))
    print("  All phases done!")

asyncio.run(nursery_pattern_demo())
```

### Example: Parallel API Calls with Error Handling

```python
import asyncio
import random
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIResponse:
    endpoint: str
    status: int
    data: Optional[dict] = None
    error: Optional[str] = None

async def parallel_api_calls():
    """
    Real-world pattern: fetch data from multiple APIs,
    handle partial failures gracefully using structured concurrency.
    """

    async def call_api(endpoint: str) -> APIResponse:
        """Simulate API call with realistic failure modes."""
        await asyncio.sleep(random.uniform(0.1, 0.5))

        failure_roll = random.random()
        if failure_roll < 0.1:
            raise ConnectionError(f"Cannot reach {endpoint}")
        elif failure_roll < 0.2:
            return APIResponse(endpoint, 500, error="Internal Server Error")
        else:
            return APIResponse(endpoint, 200, data={"result": f"data_{endpoint}"})

    async def fetch_with_fallback(
        primary: str,
        fallback: str,
    ) -> APIResponse:
        """Try primary endpoint, fall back to secondary on failure."""
        try:
            response = await call_api(primary)
            if response.status == 200:
                return response
        except ConnectionError:
            pass
        # Try fallback
        return await call_api(fallback)

    async def fetch_all_user_data(user_id: int) -> dict:
        """
        Fetch user's data from multiple services.
        Uses TaskGroup for structured error handling.
        """
        results = {}

        # Required data - all must succeed
        try:
            async with asyncio.TaskGroup() as tg:
                profile_task = tg.create_task(
                    call_api(f"/users/{user_id}/profile")
                )
                settings_task = tg.create_task(
                    call_api(f"/users/{user_id}/settings")
                )
        except* ConnectionError as eg:
            return {"error": f"Required services unavailable: {eg.exceptions}"}

        results["profile"] = profile_task.result()
        results["settings"] = settings_task.result()

        # Optional data - failures are OK
        optional_results = await asyncio.gather(
            call_api(f"/users/{user_id}/notifications"),
            call_api(f"/users/{user_id}/recommendations"),
            return_exceptions=True,
        )

        for key, result in zip(["notifications", "recs"], optional_results):
            if isinstance(result, Exception):
                results[key] = APIResponse("", 0, error=str(result))
            else:
                results[key] = result

        return results

    # Fetch data for multiple users concurrently
    print("Fetching data for 3 users:")
    async with asyncio.TaskGroup() as tg:
        user_tasks = [
            tg.create_task(fetch_all_user_data(uid))
            for uid in [101, 102, 103]
        ]

    for uid, task in zip([101, 102, 103], user_tasks):
        data = task.result()
        if "error" in data:
            print(f"  User {uid}: FAILED - {data['error']}")
        else:
            statuses = [
                f"{k}={v.status if isinstance(v, APIResponse) else '?'}"
                for k, v in data.items()
            ]
            print(f"  User {uid}: {', '.join(statuses)}")

asyncio.run(parallel_api_calls())
```

---

## 12. Building High-Throughput Services

### Architecture for Async Services

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ASYNC SERVICE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐                                                    │
│  │   Clients   │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                            │
│  ┌──────▼──────┐                                                    │
│  │ Load        │  Rate Limiter + Circuit Breaker                    │
│  │ Balancer    │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                            │
│  ┌──────▼──────────────────────────────────────────────┐            │
│  │           ASYNC SERVICE (single process)             │            │
│  │                                                      │            │
│  │  ┌──────────────────────────────────────────────┐   │            │
│  │  │              Event Loop                       │   │            │
│  │  │                                              │   │            │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │            │
│  │  │  │ Handler │  │ Handler │  │ Handler │    │   │            │
│  │  │  │ Task    │  │ Task    │  │ Task    │    │   │            │
│  │  │  └────┬────┘  └────┬────┘  └────┬────┘    │   │            │
│  │  │       │             │             │         │   │            │
│  │  │  ┌────▼─────────────▼─────────────▼────┐   │   │            │
│  │  │  │        Connection Pool               │   │   │            │
│  │  │  │   (DB / Redis / HTTP)                │   │   │            │
│  │  │  └─────────────────────────────────────┘   │   │            │
│  │  │                                              │   │            │
│  │  │  ┌──────────┐  ┌──────────┐                │   │            │
│  │  │  │ Worker   │  │ Thread   │                │   │            │
│  │  │  │ Queue    │  │ Executor │                │   │            │
│  │  │  └──────────┘  └──────────┘                │   │            │
│  │  └──────────────────────────────────────────────┘   │            │
│  │                                                      │            │
│  │  ┌──────────────────────────────────────────────┐   │            │
│  │  │  Health Check / Metrics / Graceful Shutdown  │   │            │
│  │  └──────────────────────────────────────────────┘   │            │
│  └──────────────────────────────────────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Connection Pooling

```python
import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Connection:
    id: int
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)
    queries: int = 0

    @property
    def age(self) -> float:
        return time.monotonic() - self.created_at

    @property
    def idle_time(self) -> float:
        return time.monotonic() - self.last_used

class ConnectionPool:
    """
    Production-quality async connection pool with:
    - Min/max size limits
    - Idle connection eviction
    - Connection health checking
    - Graceful overflow handling
    """

    def __init__(
        self,
        min_size: int = 5,
        max_size: int = 20,
        max_idle_time: float = 300.0,
        max_lifetime: float = 3600.0,
        acquire_timeout: float = 10.0,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        self.acquire_timeout = acquire_timeout

        self._pool: asyncio.Queue[Connection] = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._lock = asyncio.Lock()
        self._closed = False
        self._conn_counter = 0
        self._maintenance_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Create minimum connections and start maintenance."""
        for _ in range(self.min_size):
            conn = await self._create_connection()
            await self._pool.put(conn)

        self._maintenance_task = asyncio.create_task(self._maintenance_loop())

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        conn = await self._acquire()
        try:
            yield conn
        finally:
            await self._release(conn)

    async def _acquire(self) -> Connection:
        """Get a healthy connection."""
        try:
            async with asyncio.timeout(self.acquire_timeout):
                while True:
                    try:
                        conn = self._pool.get_nowait()
                    except asyncio.QueueEmpty:
                        async with self._lock:
                            if self._size < self.max_size:
                                conn = await self._create_connection()
                                return conn
                        # At capacity - wait for a return
                        conn = await self._pool.get()

                    # Validate connection
                    if self._is_healthy(conn):
                        conn.last_used = time.monotonic()
                        return conn
                    else:
                        await self._destroy_connection(conn)
        except TimeoutError:
            raise RuntimeError("Connection pool exhausted")

    async def _release(self, conn: Connection):
        """Return connection to pool."""
        if self._closed or not self._is_healthy(conn):
            await self._destroy_connection(conn)
        else:
            conn.last_used = time.monotonic()
            await self._pool.put(conn)

    def _is_healthy(self, conn: Connection) -> bool:
        """Check if connection is still valid."""
        if conn.age > self.max_lifetime:
            return False
        if conn.idle_time > self.max_idle_time:
            return False
        return True

    async def _create_connection(self) -> Connection:
        """Create a new connection."""
        self._conn_counter += 1
        self._size += 1
        await asyncio.sleep(0.05)  # Simulate connection setup
        return Connection(id=self._conn_counter)

    async def _destroy_connection(self, conn: Connection):
        """Destroy a connection."""
        self._size -= 1
        await asyncio.sleep(0.01)  # Simulate close

    async def _maintenance_loop(self):
        """Periodically clean up idle connections."""
        while not self._closed:
            await asyncio.sleep(30)
            await self._evict_idle()

    async def _evict_idle(self):
        """Remove idle connections above minimum."""
        evicted = 0
        temp = []
        while not self._pool.empty() and self._size > self.min_size:
            try:
                conn = self._pool.get_nowait()
                if not self._is_healthy(conn):
                    await self._destroy_connection(conn)
                    evicted += 1
                else:
                    temp.append(conn)
            except asyncio.QueueEmpty:
                break

        for conn in temp:
            await self._pool.put(conn)

        if evicted:
            print(f"  [Pool] Evicted {evicted} idle connections")

    async def close(self):
        """Shutdown the pool."""
        self._closed = True
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        while not self._pool.empty():
            conn = self._pool.get_nowait()
            await self._destroy_connection(conn)

    @property
    def stats(self) -> dict:
        return {
            "total": self._size,
            "available": self._pool.qsize(),
            "in_use": self._size - self._pool.qsize(),
        }

async def pool_demo():
    pool = ConnectionPool(min_size=3, max_size=10)
    await pool.initialize()
    print(f"Pool initialized: {pool.stats}")

    async def simulate_query(query_id: int):
        async with pool.acquire() as conn:
            conn.queries += 1
            await asyncio.sleep(0.1)
            return f"Query {query_id} on conn-{conn.id}"

    # Simulate concurrent database queries
    results = await asyncio.gather(*[
        simulate_query(i) for i in range(20)
    ])
    print(f"Executed {len(results)} queries")
    print(f"Pool stats after: {pool.stats}")
    await pool.close()

asyncio.run(pool_demo())
```

### Batch Processing

```python
import asyncio
import time
from typing import Callable, TypeVar

T = TypeVar('T')
R = TypeVar('R')

class AsyncBatcher:
    """
    Batches individual requests into groups for efficient processing.
    Useful for: database inserts, API calls with batch endpoints,
    ML model inference.
    """

    def __init__(
        self,
        process_batch: Callable,
        max_batch_size: int = 50,
        max_wait_ms: float = 100,
    ):
        self._process_batch = process_batch
        self._max_batch_size = max_batch_size
        self._max_wait = max_wait_ms / 1000.0
        self._pending: list[tuple] = []  # (item, future)
        self._lock = asyncio.Lock()
        self._flush_event = asyncio.Event()
        self._running = True
        self._flush_task: asyncio.Task = None

    async def start(self):
        """Start the background flush loop."""
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def submit(self, item) -> any:
        """Submit single item, returns its result when batch is processed."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async with self._lock:
            self._pending.append((item, future))
            if len(self._pending) >= self._max_batch_size:
                self._flush_event.set()

        return await future

    async def _flush_loop(self):
        """Periodically flush pending items."""
        while self._running:
            try:
                await asyncio.wait_for(
                    self._flush_event.wait(),
                    timeout=self._max_wait,
                )
            except asyncio.TimeoutError:
                pass
            self._flush_event.clear()
            await self._flush()

    async def _flush(self):
        """Process all pending items as a batch."""
        async with self._lock:
            if not self._pending:
                return
            batch = self._pending[:]
            self._pending = []

        items = [item for item, _ in batch]
        futures = [future for _, future in batch]

        try:
            results = await self._process_batch(items)
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)
        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)

    async def stop(self):
        """Flush remaining and stop."""
        self._running = False
        await self._flush()
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

async def batch_demo():
    """Demonstrate batching individual inserts into bulk operations."""

    call_count = 0

    async def bulk_insert(items: list[dict]) -> list[int]:
        """Simulate a bulk database insert."""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)  # Bulk insert is fast
        return list(range(len(items)))  # Return IDs

    batcher = AsyncBatcher(
        process_batch=bulk_insert,
        max_batch_size=10,
        max_wait_ms=50,
    )
    await batcher.start()

    # 100 individual inserts get batched automatically
    start = time.perf_counter()
    results = await asyncio.gather(*[
        batcher.submit({"name": f"item-{i}"}) for i in range(100)
    ])
    elapsed = time.perf_counter() - start

    await batcher.stop()

    print(f"  100 items processed in {elapsed:.3f}s")
    print(f"  Actual bulk calls made: {call_count}")
    print(f"  Average batch size: {100/call_count:.1f}")

asyncio.run(batch_demo())
```

### Rate Limiting

```python
import asyncio
import time
from collections import deque

class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter for async services.
    More accurate than fixed windows, prevents edge bursts.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Try to acquire a slot. Returns True if allowed."""
        async with self._lock:
            now = time.monotonic()
            # Remove expired timestamps
            while self._timestamps and self._timestamps[0] < now - self.window:
                self._timestamps.popleft()

            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
            return False

    async def wait_and_acquire(self) -> float:
        """Wait until a slot is available. Returns wait time."""
        start = time.monotonic()
        while True:
            if await self.acquire():
                return time.monotonic() - start
            # Calculate how long to wait
            async with self._lock:
                if self._timestamps:
                    oldest = self._timestamps[0]
                    wait_time = (oldest + self.window) - time.monotonic()
                    wait_time = max(0.01, wait_time)
                else:
                    wait_time = 0.01
            await asyncio.sleep(wait_time)

async def rate_limit_demo():
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)

    async def make_request(request_id: int):
        wait_time = await limiter.wait_and_acquire()
        if wait_time > 0.01:
            print(f"  Request {request_id:2d}: waited {wait_time:.3f}s")
        else:
            print(f"  Request {request_id:2d}: immediate")

    start = time.perf_counter()
    await asyncio.gather(*[make_request(i) for i in range(15)])
    elapsed = time.perf_counter() - start
    print(f"\n  15 requests at 5/s rate: {elapsed:.2f}s (expected ~3s)")

asyncio.run(rate_limit_demo())
```

### Circuit Breaking in Async Context

```python
import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitStats:
    successes: int = 0
    failures: int = 0
    last_failure_time: float = 0
    consecutive_failures: int = 0

class AsyncCircuitBreaker:
    """
    Circuit breaker pattern for async services.
    Prevents cascading failures by failing fast when a service is down.

    States:
    - CLOSED: Normal. Track failures.
    - OPEN: Service is down. Reject immediately (fail fast).
    - HALF_OPEN: Test with limited requests to see if recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = asyncio.Lock()
        self._half_open_calls = 0
        self._half_open_successes = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._stats.last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._half_open_successes = 0
        return self._state

    async def call(self, coro_factory):
        """Execute through the circuit breaker."""
        async with self._lock:
            state = self.state

            if state == CircuitState.OPEN:
                raise CircuitBreakerOpen(
                    f"Circuit is OPEN. Retry after "
                    f"{self.recovery_timeout}s"
                )

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpen("Half-open: max test calls reached")
                self._half_open_calls += 1

        try:
            result = await coro_factory()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        async with self._lock:
            self._stats.successes += 1
            self._stats.consecutive_failures = 0

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.success_threshold:
                    print("  [CB] Circuit CLOSED (recovered)")
                    self._state = CircuitState.CLOSED
                    self._stats = CircuitStats()

    async def _on_failure(self):
        async with self._lock:
            self._stats.failures += 1
            self._stats.consecutive_failures += 1
            self._stats.last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                print("  [CB] Circuit OPEN (half-open test failed)")
                self._state = CircuitState.OPEN
            elif self._stats.consecutive_failures >= self.failure_threshold:
                print("  [CB] Circuit OPEN (threshold reached)")
                self._state = CircuitState.OPEN

class CircuitBreakerOpen(Exception):
    pass

async def circuit_breaker_demo():
    cb = AsyncCircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0,
        success_threshold=2,
    )

    call_count = 0
    should_fail = True

    async def unreliable_service():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        if should_fail:
            raise ConnectionError("Service unavailable")
        return "OK"

    # Phase 1: Failures trip the circuit
    print("Phase 1: Service failing...")
    for i in range(5):
        try:
            await cb.call(unreliable_service)
        except CircuitBreakerOpen as e:
            print(f"  Request {i}: REJECTED (circuit open)")
        except ConnectionError:
            print(f"  Request {i}: FAILED (connection error)")

    # Phase 2: Circuit is open - requests rejected immediately
    print(f"\nPhase 2: Circuit state = {cb.state.value}")
    try:
        await cb.call(unreliable_service)
    except CircuitBreakerOpen:
        print("  Request rejected immediately (fast fail)")

    # Phase 3: Wait for recovery timeout, service recovers
    print(f"\nPhase 3: Waiting for recovery...")
    await asyncio.sleep(1.5)
    should_fail = False

    print(f"  Circuit state after wait: {cb.state.value}")
    for i in range(3):
        try:
            result = await cb.call(unreliable_service)
            print(f"  Test request {i}: {result}")
        except CircuitBreakerOpen as e:
            print(f"  Test request {i}: still open")

    print(f"\n  Final state: {cb.state.value}")
    print(f"  Total actual calls made: {call_count}")

asyncio.run(circuit_breaker_demo())
```

### Graceful Shutdown

```python
import asyncio
import signal
from typing import Set

class AsyncServiceLifecycle:
    """
    Manages the lifecycle of an async service with graceful shutdown.
    """

    def __init__(self, shutdown_timeout: float = 30.0):
        self._shutdown_timeout = shutdown_timeout
        self._shutdown_event = asyncio.Event()
        self._active_requests: Set[asyncio.Task] = set()
        self._is_healthy = True
        self._is_ready = False

    @property
    def is_healthy(self) -> bool:
        return self._is_healthy

    @property
    def is_ready(self) -> bool:
        return self._is_ready and not self._shutdown_event.is_set()

    async def start(self):
        """Start the service."""
        loop = asyncio.get_running_loop()

        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(self._shutdown(s))
            )

        self._is_ready = True
        print("  Service ready to accept requests")

    async def _shutdown(self, sig: signal.Signals):
        """Graceful shutdown sequence."""
        print(f"\n  Received {sig.name}, starting graceful shutdown...")

        # 1. Stop accepting new requests
        self._is_ready = False
        print(f"  Stopped accepting new requests")

        # 2. Wait for in-flight requests
        if self._active_requests:
            print(f"  Waiting for {len(self._active_requests)} "
                  f"in-flight requests...")
            try:
                async with asyncio.timeout(self._shutdown_timeout):
                    while self._active_requests:
                        await asyncio.sleep(0.1)
                print("  All requests completed")
            except TimeoutError:
                print(f"  Timeout! Cancelling {len(self._active_requests)} "
                      f"remaining requests")
                for task in self._active_requests:
                    task.cancel()
                await asyncio.gather(
                    *self._active_requests, return_exceptions=True
                )

        # 3. Cleanup resources
        print("  Cleaning up resources...")
        await asyncio.sleep(0.1)

        # 4. Signal main loop to exit
        self._is_healthy = False
        self._shutdown_event.set()
        print("  Shutdown complete")

    def track_request(self, task: asyncio.Task):
        """Register an active request for graceful shutdown tracking."""
        self._active_requests.add(task)
        task.add_done_callback(self._active_requests.discard)

    async def wait_for_shutdown(self):
        """Block until shutdown is requested."""
        await self._shutdown_event.wait()
```

### Health Checks

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Callable

@dataclass
class HealthStatus:
    healthy: bool
    checks: dict[str, bool]
    latencies: dict[str, float]
    uptime: float

class HealthChecker:
    """
    Async health checker for service dependencies.
    Supports liveness (is the process alive?) and
    readiness (can it serve traffic?) probes.
    """

    def __init__(self):
        self._checks: dict[str, Callable] = {}
        self._start_time = time.monotonic()
        self._last_status: HealthStatus = None

    def register(self, name: str, check_fn: Callable):
        """Register a health check function (must be async)."""
        self._checks[name] = check_fn

    async def check_health(self, timeout: float = 5.0) -> HealthStatus:
        """Run all health checks concurrently."""
        results = {}
        latencies = {}

        async def run_check(name: str, fn: Callable):
            start = time.perf_counter()
            try:
                async with asyncio.timeout(timeout):
                    await fn()
                    results[name] = True
            except Exception:
                results[name] = False
            latencies[name] = time.perf_counter() - start

        await asyncio.gather(*[
            run_check(name, fn) for name, fn in self._checks.items()
        ])

        status = HealthStatus(
            healthy=all(results.values()),
            checks=results,
            latencies=latencies,
            uptime=time.monotonic() - self._start_time,
        )
        self._last_status = status
        return status

async def health_check_demo():
    checker = HealthChecker()

    # Register dependency checks
    async def check_database():
        await asyncio.sleep(0.05)  # Simulated DB ping

    async def check_redis():
        await asyncio.sleep(0.02)  # Simulated Redis ping

    async def check_external_api():
        await asyncio.sleep(0.1)  # Simulated API health endpoint

    checker.register("database", check_database)
    checker.register("redis", check_redis)
    checker.register("external_api", check_external_api)

    status = await checker.check_health()
    print(f"  Healthy: {status.healthy}")
    print(f"  Checks: {status.checks}")
    print(f"  Latencies: {status.latencies}")
    print(f"  Uptime: {status.uptime:.1f}s")

asyncio.run(health_check_demo())
```

### Example: Complete Async HTTP Service

```python
import asyncio
import time
import random
import signal
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager
from collections import deque
from enum import Enum

# ═══════════════════════════════════════════════════════════════
# COMPLETE HIGH-THROUGHPUT ASYNC SERVICE
# Demonstrates: Connection Pool, Rate Limiter, Circuit Breaker,
# Graceful Shutdown, Worker Pool, Health Checks
# ═══════════════════════════════════════════════════════════════

# ─── Connection Pool ───────────────────────────────────────────

@dataclass
class DBConnection:
    id: int
    created_at: float = field(default_factory=time.monotonic)
    queries: int = 0

    async def execute(self, query: str) -> dict:
        await asyncio.sleep(random.uniform(0.01, 0.05))
        self.queries += 1
        return {"rows": random.randint(0, 100)}

class DBPool:
    def __init__(self, size: int = 10):
        self._pool: asyncio.Queue[DBConnection] = asyncio.Queue(maxsize=size)
        self._size = size
        self._counter = 0

    async def initialize(self):
        for _ in range(self._size):
            self._counter += 1
            conn = DBConnection(id=self._counter)
            await self._pool.put(conn)

    @asynccontextmanager
    async def connection(self):
        conn = await self._pool.get()
        try:
            yield conn
        finally:
            await self._pool.put(conn)

    async def close(self):
        while not self._pool.empty():
            self._pool.get_nowait()

# ─── Token Bucket Rate Limiter ─────────────────────────────────

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait_for_token(self):
        while not await self.consume():
            await asyncio.sleep(1.0 / self._rate)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._rate
        )
        self._last_refill = now

# ─── Circuit Breaker ───────────────────────────────────────────

class CBState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, threshold: int = 5, timeout: float = 10.0):
        self._threshold = threshold
        self._timeout = timeout
        self._failures = 0
        self._state = CBState.CLOSED
        self._last_failure = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CBState:
        if self._state == CBState.OPEN:
            if time.monotonic() - self._last_failure > self._timeout:
                return CBState.HALF_OPEN
        return self._state

    async def execute(self, coro_factory: Callable) -> Any:
        async with self._lock:
            if self.state == CBState.OPEN:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await coro_factory()
            async with self._lock:
                self._failures = 0
                if self._state == CBState.HALF_OPEN:
                    self._state = CBState.CLOSED
            return result
        except Exception:
            async with self._lock:
                self._failures += 1
                self._last_failure = time.monotonic()
                if self._failures >= self._threshold:
                    self._state = CBState.OPEN
            raise

# ─── Worker Pool ───────────────────────────────────────────────

class WorkerPool:
    def __init__(self, num_workers: int, queue_size: int = 1000):
        self._num_workers = num_workers
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._workers: list[asyncio.Task] = []
        self._processed = 0
        self._errors = 0

    async def start(self):
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self._num_workers)
        ]

    async def submit(self, work_fn: Callable, *args) -> asyncio.Future:
        future = asyncio.get_running_loop().create_future()
        await self._queue.put((work_fn, args, future))
        return future

    async def _worker(self, worker_id: int):
        while True:
            try:
                work_fn, args, future = await self._queue.get()
                try:
                    result = await work_fn(*args)
                    if not future.done():
                        future.set_result(result)
                    self._processed += 1
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                    self._errors += 1
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break

    async def stop(self):
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

    @property
    def stats(self) -> dict:
        return {
            "workers": self._num_workers,
            "queue_size": self._queue.qsize(),
            "processed": self._processed,
            "errors": self._errors,
        }

# ─── The Complete Service ──────────────────────────────────────

class AsyncHTTPService:
    """
    Production-grade async service combining all patterns.
    """

    def __init__(self):
        self.db_pool = DBPool(size=10)
        self.rate_limiter = TokenBucket(rate=100, capacity=200)
        self.circuit_breaker = CircuitBreaker(threshold=5, timeout=10.0)
        self.worker_pool = WorkerPool(num_workers=5, queue_size=500)
        self._shutdown_event = asyncio.Event()
        self._is_ready = False
        self._request_count = 0
        self._start_time = time.monotonic()

    async def start(self):
        """Initialize all components."""
        print("  [Service] Starting...")
        await self.db_pool.initialize()
        await self.worker_pool.start()
        self._is_ready = True
        print("  [Service] Ready!")

    async def handle_request(self, request_id: int) -> dict:
        """Process a single request through the full pipeline."""
        self._request_count += 1

        # 1. Rate limiting
        if not await self.rate_limiter.consume():
            return {"status": 429, "error": "Rate limited"}

        # 2. Circuit breaker
        try:
            result = await self.circuit_breaker.execute(
                lambda: self._process_request(request_id)
            )
            return {"status": 200, "data": result}
        except Exception as e:
            return {"status": 503, "error": str(e)}

    async def _process_request(self, request_id: int) -> dict:
        """Actual request processing logic."""
        # Use connection pool for DB access
        async with self.db_pool.connection() as conn:
            result = await conn.execute(f"SELECT * FROM items WHERE id={request_id}")

        # Simulate occasional failures
        if random.random() < 0.05:
            raise ConnectionError("Upstream service failed")

        return {"request_id": request_id, **result}

    async def health_check(self) -> dict:
        """Liveness and readiness probe."""
        return {
            "healthy": self._is_ready and not self._shutdown_event.is_set(),
            "uptime": time.monotonic() - self._start_time,
            "requests_served": self._request_count,
            "worker_stats": self.worker_pool.stats,
        }

    async def shutdown(self):
        """Graceful shutdown."""
        print("\n  [Service] Shutting down...")
        self._is_ready = False

        # Wait for in-flight requests (simulated)
        await asyncio.sleep(0.2)

        # Stop components
        await self.worker_pool.stop()
        await self.db_pool.close()
        self._shutdown_event.set()
        print("  [Service] Shutdown complete")

# ─── Run the service ───────────────────────────────────────────

async def main():
    service = AsyncHTTPService()
    await service.start()

    # Simulate load
    print("\n  Simulating 200 concurrent requests...")
    start = time.perf_counter()

    results = await asyncio.gather(*[
        service.handle_request(i) for i in range(200)
    ])

    elapsed = time.perf_counter() - start

    # Stats
    statuses = {}
    for r in results:
        s = r["status"]
        statuses[s] = statuses.get(s, 0) + 1

    print(f"\n  ╔══════════════════════════════════════╗")
    print(f"  ║     SERVICE PERFORMANCE REPORT        ║")
    print(f"  ╠══════════════════════════════════════╣")
    print(f"  ║  Total requests:  {len(results):>6}             ║")
    print(f"  ║  Duration:        {elapsed:>6.3f}s            ║")
    print(f"  ║  Throughput:      {len(results)/elapsed:>6.0f} req/s       ║")
    print(f"  ║  Status 200:      {statuses.get(200, 0):>6}             ║")
    print(f"  ║  Status 429:      {statuses.get(429, 0):>6}             ║")
    print(f"  ║  Status 503:      {statuses.get(503, 0):>6}             ║")
    print(f"  ╚══════════════════════════════════════╝")

    # Health check
    health = await service.health_check()
    print(f"\n  Health: {health}")

    # Shutdown
    await service.shutdown()

asyncio.run(main())
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                  ASYNCIO CHEAT SHEET                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RUN ASYNC CODE:                                                 │
│    asyncio.run(main())              # Entry point                │
│    await coro()                     # Inside async function      │
│                                                                  │
│  CONCURRENCY:                                                    │
│    asyncio.gather(*coros)           # Run all, collect results   │
│    asyncio.create_task(coro)        # Schedule independently     │
│    async with asyncio.TaskGroup()   # Structured (3.11+)        │
│                                                                  │
│  WAITING:                                                        │
│    asyncio.wait(tasks, ...)         # Fine-grained control       │
│    asyncio.wait_for(coro, timeout)  # With timeout              │
│    async with asyncio.timeout(s)    # Timeout scope (3.11+)     │
│                                                                  │
│  SYNCHRONIZATION:                                                │
│    asyncio.Lock()                   # Mutual exclusion           │
│    asyncio.Semaphore(n)             # Limit concurrency          │
│    asyncio.Event()                  # Signal between tasks       │
│    asyncio.Condition()              # Complex conditions         │
│    asyncio.Barrier(n)              # Sync point (3.11+)         │
│                                                                  │
│  QUEUES:                                                         │
│    asyncio.Queue(maxsize)           # FIFO with backpressure     │
│    asyncio.PriorityQueue()          # Priority ordering          │
│    asyncio.LifoQueue()              # Stack behavior             │
│                                                                  │
│  THREAD BRIDGE:                                                  │
│    asyncio.to_thread(fn, *args)     # Run sync in thread         │
│    loop.run_in_executor(pool, fn)   # Custom executor            │
│                                                                  │
│  CANCELLATION:                                                   │
│    task.cancel()                    # Request cancellation        │
│    asyncio.shield(coro)             # Protect from cancel         │
│                                                                  │
│  BEST PRACTICES:                                                 │
│    ✓ Use asyncio.run() as entry point                           │
│    ✓ Never block the event loop (time.sleep, sync I/O)          │
│    ✓ Use TaskGroup for structured concurrency                    │
│    ✓ Always await or store task references                       │
│    ✓ Use bounded queues for backpressure                         │
│    ✓ Handle CancelledError in cleanup code                       │
│    ✓ Use asyncio.timeout over wait_for (3.11+)                  │
│    ✗ Don't use asyncio.get_event_loop() in modern code          │
│    ✗ Don't forget to close resources (use async with)            │
│    ✗ Don't create tasks without storing references               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions & Answers

### Q1: How does asyncio achieve concurrency without threads?
**A:** asyncio uses cooperative multitasking on a single thread. Coroutines voluntarily yield control at `await` points, allowing the event loop to run other ready coroutines. The event loop uses OS I/O multiplexing (epoll/kqueue) to efficiently wait for multiple I/O operations simultaneously.

### Q2: What's the difference between concurrency and parallelism in Python?
**A:** Concurrency means multiple tasks make progress (interleaving). Parallelism means tasks literally execute at the same instant (multiple CPU cores). asyncio provides concurrency but NOT parallelism - it's single-threaded. For parallelism, use multiprocessing.

### Q3: When would asyncio give no benefit?
**A:** When the workload is CPU-bound. Since asyncio is single-threaded, a CPU-intensive loop blocks the event loop entirely. Use `run_in_executor` with ProcessPoolExecutor for CPU work, or use multiprocessing directly.

### Q4: Explain the relationship between Future, Task, and Coroutine.
**A:** A Coroutine is a suspendable function (async def). A Future is a low-level placeholder for a result that doesn't exist yet. A Task is a Future subclass that wraps a coroutine and drives it to completion through the event loop. In practice: you write coroutines, create Tasks to run them, and rarely use bare Futures.

### Q5: What is structured concurrency and why does it matter?
**A:** Structured concurrency (TaskGroup in Python 3.11+) ensures that concurrent tasks have a clear owner, bounded lifetime, and deterministic cleanup. If any task fails, siblings are cancelled. This prevents resource leaks, lost exceptions, and makes concurrent code easier to reason about.

### Q6: How do you handle backpressure in an async system?
**A:** Use bounded queues (asyncio.Queue with maxsize). When the queue is full, producers block until consumers catch up. This prevents unbounded memory growth and propagates slowness back to the source. Other strategies include token buckets for rate limiting and TCP flow control for network backpressure.

### Q7: What happens if you forget to await a coroutine?
**A:** The coroutine object is created but never executed. Python will emit a RuntimeWarning "coroutine was never awaited" when the object is garbage collected. The code inside the coroutine never runs, which is a common source of bugs.

### Q8: How does cancellation work in asyncio?
**A:** `task.cancel()` schedules a CancelledError to be raised at the next await point in the task. The coroutine can catch it for cleanup (but should re-raise). `asyncio.shield()` protects a coroutine from cancellation. Python 3.11+ TaskGroups cancel siblings when one task fails.

---

## Further Reading

- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [PEP 492 - Coroutines with async and await syntax](https://peps.python.org/pep-0492/)
- [PEP 3156 - Asynchronous IO Support Rebooted](https://peps.python.org/pep-3156/)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [uvloop - Ultra fast asyncio event loop](https://github.com/MagicStack/uvloop)
- [Trio - Structured concurrency library](https://trio.readthedocs.io/)
- [aiohttp - Async HTTP client/server](https://docs.aiohttp.org/)
