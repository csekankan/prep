# Concurrency Fundamentals in Python — Complete Guide

> **Scope**: 20 essential concurrency topics, each with theory, runnable Python code, pitfalls, interview tips, and performance notes.
> **Python version**: 3.10+ (3.12+ features noted where relevant).

---

## Table of Contents

1. [Global Interpreter Lock (GIL)](#1-global-interpreter-lock-gil)
2. [CPU-Bound vs I/O-Bound Workloads](#2-cpu-bound-vs-io-bound-workloads)
3. [Threading Module](#3-threading-module)
4. [Multiprocessing Module](#4-multiprocessing-module)
5. [ThreadPoolExecutor](#5-threadpoolexecutor)
6. [ProcessPoolExecutor](#6-processpoolexecutor)
7. [Locks (threading.Lock)](#7-locks-threadinglock)
8. [Reentrant Locks (RLock)](#8-reentrant-locks-rlock)
9. [Semaphores](#9-semaphores)
10. [Conditions (threading.Condition)](#10-conditions-threadingcondition)
11. [Events (threading.Event)](#11-events-threadingevent)
12. [Barriers (threading.Barrier)](#12-barriers-threadingbarrier)
13. [Queues (queue module)](#13-queues-queue-module)
14. [Race Conditions](#14-race-conditions)
15. [Deadlocks](#15-deadlocks)
16. [Starvation](#16-starvation)
17. [Thread Safety](#17-thread-safety)
18. [Immutability](#18-immutability)
19. [Lock Contention](#19-lock-contention)
20. [Synchronization Strategies](#20-synchronization-strategies)

---

## 1. Global Interpreter Lock (GIL)

### 1.1 What the GIL Is and Why It Exists

The **Global Interpreter Lock (GIL)** is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes simultaneously in a single process. Only one thread holds the GIL at any time, even on multi-core machines.

**Why it exists:**

- CPython's memory management (reference counting) is **not thread-safe**. Every `Py_INCREF` / `Py_DECREF` call would need its own lock without the GIL.
- Retrofitting fine-grained locking into CPython was attempted (the "free-threading" patches in early 2000s) but caused a **~40 % slowdown** on single-threaded code because of per-object lock overhead.
- Many C extension modules assume they can access Python objects without additional locking; the GIL makes them safe by default.

```python
"""Demonstrate GIL: two CPU-bound threads do NOT run in parallel."""

import threading
import time


def cpu_work(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


COUNT = 20_000_000

# --- Sequential ---
start = time.perf_counter()
cpu_work(COUNT)
cpu_work(COUNT)
seq_time = time.perf_counter() - start

# --- Threaded ---
start = time.perf_counter()
t1 = threading.Thread(target=cpu_work, args=(COUNT,))
t2 = threading.Thread(target=cpu_work, args=(COUNT,))
t1.start(); t2.start()
t1.join(); t2.join()
thr_time = time.perf_counter() - start

print(f"Sequential : {seq_time:.3f}s")
print(f"Threaded   : {thr_time:.3f}s")
# Threaded is NOT faster — often slightly slower due to context-switch overhead.
```

### 1.2 How the GIL Affects Threading

| Scenario | GIL Impact |
|---|---|
| CPU-bound threads | Only one runs at a time → **no parallelism** |
| I/O-bound threads | GIL is released during I/O → **true concurrency** |
| C extensions that release GIL | Parallel execution is possible (e.g., NumPy) |

When a thread performs I/O (network, disk, `time.sleep`), CPython **releases the GIL** so another thread can acquire it and run.

### 1.3 GIL and CPU-Bound vs I/O-Bound Work

```python
"""I/O-bound threads DO benefit from threading despite the GIL."""

import threading
import time


def io_task(task_id: int) -> None:
    print(f"Task {task_id} starting I/O")
    time.sleep(2)          # GIL released during sleep
    print(f"Task {task_id} done")


start = time.perf_counter()
threads = [threading.Thread(target=io_task, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
elapsed = time.perf_counter() - start

print(f"5 × 2s I/O-bound tasks with threads: {elapsed:.2f}s")
# ≈ 2 s (parallel), not 10 s (sequential)
```

### 1.4 GIL Release Points

The GIL is released in several situations:

1. **I/O operations**: `socket.recv()`, `file.read()`, `time.sleep()`
2. **C extensions** that explicitly call `Py_BEGIN_ALLOW_THREADS` / `Py_END_ALLOW_THREADS`
3. **Periodic check interval**: every `sys.getswitchinterval()` seconds (default 5 ms), the interpreter checks whether another thread is waiting for the GIL

```python
import sys

print(f"Switch interval: {sys.getswitchinterval()} seconds")
# Default: 0.005 (5 ms)

# You can change it (rarely needed):
sys.setswitchinterval(0.001)  # 1 ms
```

### 1.5 Python 3.12+ GIL Improvements (Per-Interpreter GIL)

Python 3.12 introduced **per-interpreter GIL** (PEP 684). Each sub-interpreter gets its own GIL, enabling true parallelism for CPU-bound Python code within the same process.

Python 3.13 introduced **free-threaded mode** (PEP 703, experimental) — a build option that disables the GIL entirely.

```python
"""Per-interpreter GIL concept (Python 3.12+).

The C API allows creating interpreters with their own GIL.
The 'interpreters' module (PEP 554, still evolving) exposes
this from Python, but as of 3.12 it remains provisional.
"""

# Conceptual usage — real API may differ across versions:
# import _interpreters as interpreters
#
# interp = interpreters.create()
# interpreters.run_string(interp, """
# import math
# result = sum(math.factorial(i) for i in range(500))
# """)

# Free-threaded CPython (3.13+):
# Build with: ./configure --disable-gil
# At runtime: python -X gil=0 script.py
import sys
print(f"GIL enabled: {sys._is_gil_enabled()}" if hasattr(sys, '_is_gil_enabled') else "Pre-3.13")
```

### 1.6 Workarounds for GIL Limitations

| Strategy | How |
|---|---|
| `multiprocessing` | Separate processes, each with its own GIL |
| C extensions (NumPy, etc.) | Release GIL during computation |
| `ctypes` / `cffi` | Call C code that releases GIL |
| `concurrent.futures.ProcessPoolExecutor` | High-level multiprocess API |
| Sub-interpreters (3.12+) | Per-interpreter GIL |
| Free-threaded CPython (3.13+) | Disable GIL at build time |
| Alternative runtimes | Jython, IronPython (no GIL) |

### Common Pitfalls

- Assuming threads give you parallel CPU execution in CPython.
- Increasing the switch interval to "fix" the GIL — it only changes context-switch granularity.
- Ignoring the GIL when using C extensions — not all extensions release the GIL.

### Interview Tips

- "The GIL is a **process-level** mutex on the CPython interpreter, not a language-level feature."
- "I/O-bound work benefits from threading; CPU-bound work benefits from multiprocessing."
- "Python 3.12 introduced per-interpreter GIL; Python 3.13 has an experimental no-GIL build."

---

## 2. CPU-Bound vs I/O-Bound Workloads

### 2.1 Definitions

**CPU-bound**: The bottleneck is computation — the CPU is fully utilized.

- Image processing, encryption, mathematical simulations, data compression, machine-learning training.

**I/O-bound**: The bottleneck is waiting for an external resource.

- Network requests, database queries, file reads/writes, user input.

### 2.2 How to Identify Your Workload

```python
"""Profile a function to determine if it's CPU or I/O bound."""

import cProfile
import time
import hashlib


def cpu_bound_task() -> None:
    """Hash a large byte string — pure CPU work."""
    data = b"x" * 10_000_000
    for _ in range(50):
        hashlib.sha256(data)


def io_bound_task() -> None:
    """Simulate network latency — pure I/O wait."""
    for _ in range(5):
        time.sleep(0.5)


# Profile CPU-bound:
print("=== CPU-bound profile ===")
cProfile.run("cpu_bound_task()", sort="cumulative")

# Profile I/O-bound:
print("=== I/O-bound profile ===")
cProfile.run("io_bound_task()", sort="cumulative")

# CPU-bound: tottime ≈ cumtime (busy the whole time)
# I/O-bound: tottime ≪ cumtime (most time spent waiting)
```

### 2.3 Choosing the Right Concurrency Model

| Workload | Best Model | Why |
|---|---|---|
| I/O-bound | `threading` or `asyncio` | GIL is released during I/O |
| CPU-bound | `multiprocessing` | Separate processes bypass the GIL |
| Mixed | Hybrid | I/O in threads, CPU in processes |
| High-concurrency I/O | `asyncio` | Lower overhead than OS threads |

### 2.4 Benchmarking Examples

```python
"""Benchmark threading vs multiprocessing for CPU-bound and I/O-bound work."""

import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# --- CPU-bound benchmark ---

def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def bench_cpu() -> None:
    N = 34
    TASKS = 4

    # Sequential
    start = time.perf_counter()
    for _ in range(TASKS):
        fib(N)
    print(f"  Sequential     : {time.perf_counter() - start:.2f}s")

    # Threads
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=TASKS) as ex:
        list(ex.map(fib, [N] * TASKS))
    print(f"  ThreadPool     : {time.perf_counter() - start:.2f}s")

    # Processes
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=TASKS) as ex:
        list(ex.map(fib, [N] * TASKS))
    print(f"  ProcessPool    : {time.perf_counter() - start:.2f}s")


# --- I/O-bound benchmark ---

def fake_io(seconds: float = 1.0) -> str:
    time.sleep(seconds)
    return "done"


def bench_io() -> None:
    TASKS = 8

    start = time.perf_counter()
    for _ in range(TASKS):
        fake_io()
    print(f"  Sequential     : {time.perf_counter() - start:.2f}s")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=TASKS) as ex:
        list(ex.map(fake_io, [1.0] * TASKS))
    print(f"  ThreadPool     : {time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    print("CPU-bound (fib(34) × 4):")
    bench_cpu()
    print("\nI/O-bound (sleep(1) × 8):")
    bench_io()
```

### 2.5 Decision Matrix

```
                           ┌──────────────────────┐
                           │  Is work CPU-bound?   │
                           └──────────┬───────────┘
                              yes/    \no
                              ▼        ▼
                 ┌──────────────┐  ┌──────────────────┐
                 │multiprocessing│  │ High concurrency? │
                 │  or C ext.   │  └────────┬─────────┘
                 └──────────────┘     yes/    \no
                                     ▼        ▼
                            ┌──────────┐  ┌──────────┐
                            │  asyncio │  │ threading │
                            └──────────┘  └──────────┘
```

### Common Pitfalls

- Using threads for CPU-bound work and wondering why it is not faster.
- Using multiprocessing for I/O-bound work — process startup overhead dominates.
- Not measuring — always benchmark before choosing.

### Interview Tips

- "I'd profile first with `cProfile` or `time.perf_counter` to classify the bottleneck."
- "For a web scraper (I/O), I'd use threads or asyncio. For image processing (CPU), I'd use multiprocessing."

---

## 3. Threading Module

### 3.1 Thread Creation (Thread Class, Target Function)

```python
import threading


def greet(name: str) -> None:
    print(f"Hello, {name}! (thread={threading.current_thread().name})")


# Pass a callable and its arguments
t = threading.Thread(target=greet, args=("Alice",), name="greeter-1")
t.start()
t.join()
```

### 3.2 Thread Subclassing

```python
import threading
import time


class PeriodicPrinter(threading.Thread):
    """Custom thread that prints a message periodically."""

    def __init__(self, message: str, interval: float, count: int) -> None:
        super().__init__(daemon=True)
        self.message = message
        self.interval = interval
        self.count = count

    def run(self) -> None:
        for i in range(self.count):
            print(f"[{i}] {self.message}")
            time.sleep(self.interval)


printer = PeriodicPrinter("tick", 0.5, 5)
printer.start()
printer.join()
```

### 3.3 Daemon Threads

Daemon threads are **automatically killed** when the main thread exits. They are useful for background tasks that should not prevent the program from shutting down.

```python
import threading
import time


def background_monitor() -> None:
    while True:
        print("Monitoring...")
        time.sleep(1)


monitor = threading.Thread(target=background_monitor, daemon=True)
monitor.start()

time.sleep(3)
print("Main thread exiting — daemon dies automatically.")
# No need to join(); the daemon thread is killed on exit.
```

**Key rules:**

- Set `daemon=True` *before* calling `start()`.
- Daemon threads do **not** run `finally` blocks or `atexit` handlers on shutdown.
- Never use daemon threads for work that must complete (file writes, transactions).

### 3.4 Thread Naming and Identification

```python
import threading


def worker() -> None:
    t = threading.current_thread()
    print(f"Name: {t.name}, ID: {t.ident}, Native ID: {t.native_id}")


threads = []
for i in range(3):
    t = threading.Thread(target=worker, name=f"worker-{i}")
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Enumerate all alive threads:
print(f"\nActive threads: {threading.active_count()}")
for t in threading.enumerate():
    print(f"  {t.name} (daemon={t.daemon})")
```

### 3.5 thread.join() and Timeouts

```python
import threading
import time


def slow_task() -> None:
    time.sleep(5)
    print("slow_task completed")


t = threading.Thread(target=slow_task)
t.start()

# Wait at most 2 seconds
t.join(timeout=2.0)

if t.is_alive():
    print("Thread is still running after 2s timeout!")
    # Note: there is NO way to forcefully kill a thread in Python.
    # You must use a cooperative cancellation mechanism (Event, flag, etc.)
else:
    print("Thread finished within timeout.")
```

### 3.6 Thread-Local Data

`threading.local()` gives each thread its **own copy** of an attribute.

```python
import threading
import time

local_data = threading.local()


def process_request(request_id: int) -> None:
    local_data.request_id = request_id        # Each thread gets its own value
    time.sleep(0.1)
    handle_subroutine()


def handle_subroutine() -> None:
    # Accesses the same thread-local — no argument passing needed
    print(f"Handling sub-routine for request {local_data.request_id} "
          f"on thread {threading.current_thread().name}")


threads = [
    threading.Thread(target=process_request, args=(rid,))
    for rid in range(5)
]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 3.7 Complete Example: Parallel File Downloader

```python
"""Simulated parallel file downloader using threads."""

import threading
import time
import random


def download_file(url: str, results: dict, lock: threading.Lock) -> None:
    thread_name = threading.current_thread().name
    print(f"[{thread_name}] Downloading {url}...")
    latency = random.uniform(0.5, 2.0)
    time.sleep(latency)       # Simulate network I/O
    data = f"content-of-{url}"

    with lock:
        results[url] = data
    print(f"[{thread_name}] Finished {url} in {latency:.2f}s")


urls = [f"https://example.com/file{i}.txt" for i in range(8)]
results: dict[str, str] = {}
lock = threading.Lock()

threads = [
    threading.Thread(target=download_file, args=(url, results, lock), name=f"dl-{i}")
    for i, url in enumerate(urls)
]

start = time.perf_counter()
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"\nDownloaded {len(results)} files in {time.perf_counter() - start:.2f}s")
```

### Common Pitfalls

- Forgetting `t.join()` — main thread may exit before workers finish.
- Setting `daemon=True` on threads that do important work.
- Sharing mutable state without locks.
- Trying to return values from threads — `Thread.run()` ignores return values. Use a shared data structure or `concurrent.futures`.

### Interview Tips

- "Python threads are real OS threads, not green threads."
- "The `threading` module is best for I/O-bound concurrency."
- "I prefer `concurrent.futures.ThreadPoolExecutor` for production code — it handles return values, exceptions, and pool management."

---

## 4. Multiprocessing Module

### 4.1 Process Creation

```python
import multiprocessing
import os


def worker(n: int) -> None:
    print(f"Worker {n}: PID={os.getpid()}, Parent PID={os.getppid()}")


if __name__ == "__main__":
    processes = []
    for i in range(4):
        p = multiprocessing.Process(target=worker, args=(i,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print(f"Main process PID={os.getpid()}")
```

### 4.2 Process Pools

```python
import multiprocessing
import math


def compute_factorial(n: int) -> int:
    return math.factorial(n)


if __name__ == "__main__":
    with multiprocessing.Pool(processes=4) as pool:
        # map — ordered results
        results = pool.map(compute_factorial, range(20, 30))
        print("Factorials:", [len(str(r)) for r in results], "(digit counts)")

        # imap_unordered — results as they complete
        for result in pool.imap_unordered(compute_factorial, range(20, 30)):
            print(f"  Got result with {len(str(result))} digits")

        # apply_async — single task, non-blocking
        future = pool.apply_async(compute_factorial, (100,))
        print(f"100! has {len(str(future.get()))} digits")
```

### 4.3 Shared Memory (Value, Array)

Processes do **not** share memory by default. `Value` and `Array` use shared memory backed by `mmap`.

```python
import multiprocessing


def increment(counter: multiprocessing.Value, n: int) -> None:
    for _ in range(n):
        with counter.get_lock():     # Value has a built-in lock
            counter.value += 1


if __name__ == "__main__":
    counter = multiprocessing.Value("i", 0)   # 'i' = signed int
    procs = [
        multiprocessing.Process(target=increment, args=(counter, 100_000))
        for _ in range(4)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"Counter = {counter.value}")   # Exactly 400000
```

```python
"""Shared Array example."""

import multiprocessing
import ctypes


def fill_array(arr: multiprocessing.Array, start: int, end: int, value: int) -> None:
    for i in range(start, end):
        arr[i] = value


if __name__ == "__main__":
    size = 20
    shared_arr = multiprocessing.Array(ctypes.c_int, size)

    p1 = multiprocessing.Process(target=fill_array, args=(shared_arr, 0, 10, 1))
    p2 = multiprocessing.Process(target=fill_array, args=(shared_arr, 10, 20, 2))
    p1.start(); p2.start()
    p1.join(); p2.join()

    print(list(shared_arr))
    # [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
```

### 4.4 Manager Objects

`Manager` creates a server process that hosts shared objects (lists, dicts, etc.) and proxies access over IPC.

```python
import multiprocessing


def add_items(shared_list: list, items: list) -> None:
    for item in items:
        shared_list.append(item)


if __name__ == "__main__":
    with multiprocessing.Manager() as manager:
        shared_list = manager.list()
        shared_dict = manager.dict()

        p1 = multiprocessing.Process(
            target=add_items, args=(shared_list, [1, 2, 3])
        )
        p2 = multiprocessing.Process(
            target=add_items, args=(shared_list, [4, 5, 6])
        )
        p1.start(); p2.start()
        p1.join(); p2.join()

        print(f"Shared list: {list(shared_list)}")
        # Order may vary: [1, 2, 3, 4, 5, 6] or interleaved
```

### 4.5 Pipes and Queues for IPC

```python
"""Pipe — bidirectional communication between two processes."""

import multiprocessing


def sender(conn: multiprocessing.Connection) -> None:
    messages = ["hello", "world", "done"]
    for msg in messages:
        conn.send(msg)
    conn.close()


def receiver(conn: multiprocessing.Connection) -> None:
    while True:
        try:
            msg = conn.recv()
            print(f"Received: {msg}")
            if msg == "done":
                break
        except EOFError:
            break
    conn.close()


if __name__ == "__main__":
    parent_conn, child_conn = multiprocessing.Pipe()

    p1 = multiprocessing.Process(target=sender, args=(parent_conn,))
    p2 = multiprocessing.Process(target=receiver, args=(child_conn,))
    p1.start(); p2.start()
    p1.join(); p2.join()
```

```python
"""Queue — multi-producer, multi-consumer."""

import multiprocessing
import time
import random


def producer(q: multiprocessing.Queue, producer_id: int) -> None:
    for i in range(5):
        item = f"item-{producer_id}-{i}"
        q.put(item)
        time.sleep(random.uniform(0.01, 0.1))
    q.put(None)   # Sentinel


def consumer(q: multiprocessing.Queue, consumer_id: int) -> None:
    while True:
        item = q.get()
        if item is None:
            q.put(None)       # Re-broadcast sentinel for other consumers
            break
        print(f"Consumer {consumer_id} got {item}")


if __name__ == "__main__":
    q = multiprocessing.Queue()

    producers = [
        multiprocessing.Process(target=producer, args=(q, i))
        for i in range(2)
    ]
    consumers = [
        multiprocessing.Process(target=consumer, args=(q, i))
        for i in range(3)
    ]

    for p in producers + consumers:
        p.start()
    for p in producers:
        p.join()

    q.put(None)       # Initial sentinel after all producers are done
    for c in consumers:
        c.join()
```

### 4.6 Process Synchronization

```python
"""Using multiprocessing.Lock to synchronize file writes."""

import multiprocessing


def write_to_file(lock: multiprocessing.Lock, filename: str, data: str) -> None:
    with lock:
        with open(filename, "a") as f:
            f.write(data + "\n")


if __name__ == "__main__":
    lock = multiprocessing.Lock()
    filename = "/tmp/mp_output.txt"

    # Clear file
    open(filename, "w").close()

    procs = [
        multiprocessing.Process(
            target=write_to_file,
            args=(lock, filename, f"Line from process {i}")
        )
        for i in range(10)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    with open(filename) as f:
        print(f.read())
```

### 4.7 When to Use Multiprocessing vs Threading

| Factor | Threading | Multiprocessing |
|---|---|---|
| GIL constraint | Yes — limits CPU parallelism | No — separate GIL per process |
| Memory | Shared (efficient) | Separate (higher memory usage) |
| Startup cost | Low (~ms) | High (~100ms+ per process) |
| IPC | Shared objects (need locks) | Queues, Pipes, shared memory |
| Best for | I/O-bound | CPU-bound |
| Debugging | Easier | Harder (separate address spaces) |

### Common Pitfalls

- Forgetting `if __name__ == "__main__":` guard — causes infinite process spawning on Windows/macOS.
- Passing non-picklable objects to processes (lambdas, open files, sockets).
- Using `Manager` for high-throughput data — proxy overhead is significant. Prefer `Value`/`Array` or `multiprocessing.Queue`.
- Not joining processes — zombie processes accumulate.

### Interview Tips

- "Each process has its own GIL, so CPU-bound work runs in true parallel."
- "`multiprocessing.Queue` is the safest way to communicate between processes."
- "For large NumPy arrays, I'd use `multiprocessing.shared_memory` (3.8+) to avoid serialization overhead."

---

## 5. ThreadPoolExecutor

### 5.1 concurrent.futures Interface

`concurrent.futures` provides a **uniform API** for both thread and process pools. The two key classes are `ThreadPoolExecutor` and `ProcessPoolExecutor`.

### 5.2 Creating and Configuring a Pool

```python
from concurrent.futures import ThreadPoolExecutor
import os

# Default max_workers = min(32, os.cpu_count() + 4) in Python 3.8+
executor = ThreadPoolExecutor(
    max_workers=10,
    thread_name_prefix="http-pool",
)

# Always use as a context manager to ensure clean shutdown:
with ThreadPoolExecutor(max_workers=5) as executor:
    pass   # tasks here

# Or manually:
executor = ThreadPoolExecutor(max_workers=5)
# ... submit tasks ...
executor.shutdown(wait=True)     # Blocks until all tasks complete
```

### 5.3 submit() vs map()

```python
"""submit() gives you a Future; map() gives you an iterator of results."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def fetch_url(url: str) -> str:
    time.sleep(0.5)            # Simulated I/O
    return f"Response from {url}"


urls = [f"https://api.example.com/item/{i}" for i in range(10)]

# --- Using submit() ---
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_url, url): url for url in urls}

    for future in as_completed(futures):
        url = futures[future]
        try:
            result = future.result()
            print(f"  {url} → {result}")
        except Exception as e:
            print(f"  {url} → ERROR: {e}")

# --- Using map() ---
with ThreadPoolExecutor(max_workers=5) as executor:
    # Results are in the SAME ORDER as the input
    results = executor.map(fetch_url, urls, timeout=10)
    for url, result in zip(urls, results):
        print(f"  {url} → {result}")
```

### 5.4 Future Objects

```python
from concurrent.futures import ThreadPoolExecutor, Future
import time


def compute(x: int) -> int:
    time.sleep(1)
    if x == 3:
        raise ValueError(f"Bad input: {x}")
    return x * x


with ThreadPoolExecutor(max_workers=4) as executor:
    future: Future = executor.submit(compute, 5)

    print(f"Done?    {future.done()}")        # False (still running)
    print(f"Running? {future.running()}")      # True

    result = future.result(timeout=5)          # Blocks until done
    print(f"Result:  {result}")                # 25
    print(f"Done?    {future.done()}")         # True

    # Exception propagation:
    bad_future = executor.submit(compute, 3)
    try:
        bad_future.result()
    except ValueError as e:
        print(f"Caught: {e}")

    # You can also check without blocking:
    print(f"Exception: {bad_future.exception()}")
```

### 5.5 as_completed() and wait()

```python
from concurrent.futures import (
    ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED, ALL_COMPLETED
)
import time
import random


def task(task_id: int) -> int:
    duration = random.uniform(0.5, 3.0)
    time.sleep(duration)
    return task_id


with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(task, i) for i in range(10)]

    # --- as_completed: yields futures as they finish ---
    print("=== as_completed ===")
    for future in as_completed(futures):
        print(f"  Task {future.result()} completed")

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(task, i) for i in range(10)]

    # --- wait: block until condition is met ---
    print("\n=== wait(FIRST_COMPLETED) ===")
    done, not_done = wait(futures, return_when=FIRST_COMPLETED)
    print(f"  {len(done)} done, {len(not_done)} pending")

    print("\n=== wait(ALL_COMPLETED) ===")
    done, not_done = wait(futures, return_when=ALL_COMPLETED)
    print(f"  {len(done)} done, {len(not_done)} pending")
```

### 5.6 Exception Handling

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def risky_task(x: int) -> float:
    if x == 0:
        raise ZeroDivisionError("cannot divide by zero")
    return 100 / x


with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(risky_task, x): x for x in range(-2, 3)}

    for future in as_completed(futures):
        x = futures[future]
        try:
            result = future.result()
            print(f"  risky_task({x}) = {result:.2f}")
        except ZeroDivisionError as e:
            print(f"  risky_task({x}) raised {e}")
        except Exception as e:
            print(f"  risky_task({x}) unexpected error: {e}")
```

### 5.7 Real Example: Parallel HTTP Requests

```python
"""Parallel HTTP requests with ThreadPoolExecutor."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import time


def fetch(url: str) -> tuple[str, int, float]:
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as response:
        data = response.read()
    elapsed = time.perf_counter() - start
    return url, len(data), elapsed


URLS = [
    "https://www.python.org",
    "https://docs.python.org",
    "https://pypi.org",
    "https://peps.python.org",
    "https://packaging.python.org",
]


def main() -> None:
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch, url): url for url in URLS}

        for future in as_completed(future_to_url):
            try:
                url, size, elapsed = future.result()
                print(f"  {url}: {size:,} bytes in {elapsed:.2f}s")
            except Exception as e:
                url = future_to_url[future]
                print(f"  {url}: ERROR — {e}")

    total = time.perf_counter() - start
    print(f"\nTotal: {total:.2f}s (vs ~{sum(2 for _ in URLS)}s sequential)")


if __name__ == "__main__":
    main()
```

### Common Pitfalls

- Setting `max_workers` too high for I/O — hundreds of threads can exhaust memory.
- Forgetting `executor.shutdown()` or not using `with` — tasks may not complete.
- Calling `future.result()` without a timeout in production code.
- Not handling exceptions from futures — they are **silently swallowed** if you never call `.result()` or `.exception()`.

### Interview Tips

- "`submit()` returns a `Future`, giving me control over individual task results and errors."
- "`map()` preserves input order, while `as_completed()` gives results as they finish."
- "I'd set `max_workers` based on the target service's capacity, not just `cpu_count()`."

---

## 6. ProcessPoolExecutor

### 6.1 Same Interface, Different Execution

```python
from concurrent.futures import ProcessPoolExecutor
import math


def heavy_computation(n: int) -> int:
    return sum(math.isqrt(i) for i in range(n))


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(heavy_computation, 5_000_000) for _ in range(4)]
        for f in futures:
            print(f"Result: {f.result()}")
```

### 6.2 Serialization Requirements (pickle)

All arguments and return values must be **picklable**.

```python
import pickle
from concurrent.futures import ProcessPoolExecutor


# ✅ Picklable — top-level function
def square(x: int) -> int:
    return x * x


# ❌ Not picklable — lambda
bad_func = lambda x: x * x


# ❌ Not picklable — closure over non-picklable object
import threading
lock = threading.Lock()
# Can't send `lock` to another process


# Verify picklability:
try:
    pickle.dumps(square)
    print("square is picklable ✓")
except pickle.PicklingError as e:
    print(f"square is NOT picklable: {e}")

try:
    pickle.dumps(bad_func)
    print("lambda is picklable ✓")
except (pickle.PicklingError, AttributeError) as e:
    print(f"lambda is NOT picklable: {e}")
```

### 6.3 Overhead Considerations

```python
"""Demonstrate process pool overhead for small tasks."""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time


def tiny_task(x: int) -> int:
    return x + 1


if __name__ == "__main__":
    N = 10_000

    # Threads — lightweight
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(tiny_task, range(N)))
    print(f"ThreadPool ({N} tiny tasks): {time.perf_counter() - start:.3f}s")

    # Processes — significant overhead from serialization + IPC
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as ex:
        list(ex.map(tiny_task, range(N), chunksize=100))
    print(f"ProcessPool ({N} tiny tasks): {time.perf_counter() - start:.3f}s")
    # ProcessPool is MUCH slower for tiny tasks
    # Use chunksize to amortize overhead when using map()
```

### 6.4 When to Use ProcessPoolExecutor

| Use ProcessPoolExecutor | Don't Use ProcessPoolExecutor |
|---|---|
| CPU-bound computation | I/O-bound work (use threads) |
| Data is easily serializable | Large non-serializable state |
| Tasks are coarse-grained | Tasks are very small/fast |
| Need true parallelism | Low latency required |

### 6.5 Real Example: Parallel Data Processing

```python
"""Process CSV chunks in parallel."""

from concurrent.futures import ProcessPoolExecutor
import csv
import io
import statistics


def generate_csv_data(num_rows: int) -> str:
    """Generate synthetic CSV data."""
    import random
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "value", "category"])
    for i in range(num_rows):
        writer.writerow([i, random.gauss(100, 15), random.choice(["A", "B", "C"])])
    return output.getvalue()


def process_chunk(csv_text: str) -> dict:
    """Process a CSV chunk and return statistics."""
    reader = csv.DictReader(io.StringIO(csv_text))
    values = [float(row["value"]) for row in reader]
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
    }


def chunk_csv(csv_text: str, num_chunks: int) -> list[str]:
    """Split CSV into chunks, preserving the header in each."""
    lines = csv_text.strip().split("\n")
    header = lines[0]
    data_lines = lines[1:]
    chunk_size = len(data_lines) // num_chunks

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size if i < num_chunks - 1 else len(data_lines)
        chunk = header + "\n" + "\n".join(data_lines[start:end])
        chunks.append(chunk)
    return chunks


if __name__ == "__main__":
    csv_data = generate_csv_data(100_000)
    chunks = chunk_csv(csv_data, 4)

    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_chunk, chunks))

    total_count = sum(r["count"] for r in results)
    overall_mean = sum(r["mean"] * r["count"] for r in results) / total_count

    print(f"Processed {total_count} rows across {len(chunks)} chunks")
    print(f"Overall mean: {overall_mean:.2f}")
    for i, r in enumerate(results):
        print(f"  Chunk {i}: count={r['count']}, mean={r['mean']:.2f}, "
              f"stdev={r['stdev']:.2f}")
```

### Common Pitfalls

- Not using `chunksize` with `map()` — each task incurs IPC overhead.
- Returning huge objects from worker processes — serialization is expensive.
- Forgetting `if __name__ == "__main__":` guard.
- Using `ProcessPoolExecutor` when `ThreadPoolExecutor` would suffice.

### Interview Tips

- "ProcessPoolExecutor is my go-to for CPU-bound parallelism because each worker has its own GIL."
- "The `chunksize` parameter in `map()` is critical for performance when processing many small items."
- "I always verify that my arguments and return values are picklable before using process pools."

---

## 7. Locks (threading.Lock)

### 7.1 What a Lock Protects

A lock (mutex) ensures that only **one thread** can execute a critical section at a time. Without locks, concurrent access to shared mutable state leads to **race conditions**.

### 7.2 acquire() and release()

```python
import threading

lock = threading.Lock()

# Explicit acquire/release:
lock.acquire()
try:
    # critical section
    pass
finally:
    lock.release()

# Better — context manager (equivalent to above):
with lock:
    # critical section
    pass
```

### 7.3 Context Manager Usage

```python
import threading

counter = 0
lock = threading.Lock()


def increment(n: int) -> None:
    global counter
    for _ in range(n):
        with lock:           # Automatically acquires and releases
            counter += 1


threads = [threading.Thread(target=increment, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Counter = {counter}")   # Always 400000
```

### 7.4 Non-Blocking Acquire

```python
import threading
import time

lock = threading.Lock()


def try_work(worker_id: int) -> None:
    acquired = lock.acquire(blocking=False)
    if acquired:
        try:
            print(f"Worker {worker_id}: acquired lock, working...")
            time.sleep(1)
        finally:
            lock.release()
    else:
        print(f"Worker {worker_id}: lock busy, doing something else")


# With timeout:
def try_work_timeout(worker_id: int) -> None:
    acquired = lock.acquire(timeout=0.5)
    if acquired:
        try:
            print(f"Worker {worker_id}: got lock within timeout")
            time.sleep(1)
        finally:
            lock.release()
    else:
        print(f"Worker {worker_id}: timed out waiting for lock")


threads = [threading.Thread(target=try_work, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 7.5 Performance Implications

- Locks **serialize** access — only one thread runs the critical section at a time.
- The critical section should be as **short** as possible.
- Holding a lock during I/O is almost always a mistake.

```python
"""Good vs bad lock usage."""

import threading
import time

lock = threading.Lock()
data = []

# ❌ BAD — lock held during I/O
def bad_fetch_and_store(url: str) -> None:
    with lock:
        time.sleep(1)           # Simulated I/O under lock!
        data.append(f"result-{url}")

# ✅ GOOD — lock only for the mutation
def good_fetch_and_store(url: str) -> None:
    time.sleep(1)               # I/O without lock
    result = f"result-{url}"
    with lock:                  # Lock only for the shared write
        data.append(result)
```

### 7.6 Example: Thread-Safe Counter

```python
import threading


class ThreadSafeCounter:
    """A counter that can be safely incremented from multiple threads."""

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    def decrement(self, amount: int = 1) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def __repr__(self) -> str:
        return f"ThreadSafeCounter({self.value})"


counter = ThreadSafeCounter()

def worker(n: int) -> None:
    for _ in range(n):
        counter.increment()

threads = [threading.Thread(target=worker, args=(100_000,)) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Final count: {counter.value}")   # 800000
```

### 7.7 Example: Bank Account

```python
import threading
import time
import random


class BankAccount:
    def __init__(self, owner: str, balance: float) -> None:
        self.owner = owner
        self.balance = balance
        self.lock = threading.Lock()

    def deposit(self, amount: float) -> None:
        with self.lock:
            current = self.balance
            time.sleep(0.001)         # Simulate processing delay
            self.balance = current + amount

    def withdraw(self, amount: float) -> bool:
        with self.lock:
            if self.balance >= amount:
                current = self.balance
                time.sleep(0.001)
                self.balance = current - amount
                return True
            return False

    def __repr__(self) -> str:
        return f"BankAccount({self.owner}, balance={self.balance:.2f})"


account = BankAccount("Alice", 1000.0)

def random_transactions() -> None:
    for _ in range(100):
        if random.random() < 0.5:
            account.deposit(10.0)
        else:
            account.withdraw(10.0)

threads = [threading.Thread(target=random_transactions) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(account)   # Balance is always consistent
```

### Common Pitfalls

- **Forgetting to release**: always use `with lock:` instead of manual `acquire/release`.
- **Deadlock**: acquiring multiple locks in different orders across threads.
- **Holding too long**: keeping the lock during I/O or computation that doesn't need it.
- **Double acquire**: `Lock` is NOT reentrant — acquiring it twice from the same thread causes a deadlock. Use `RLock` if you need reentrancy.

### Interview Tips

- "A lock is the simplest synchronization primitive — mutual exclusion for a critical section."
- "I always use the context manager form (`with lock:`) to guarantee release."
- "The critical section should be as short as possible to minimize contention."

---

## 8. Reentrant Locks (RLock)

### 8.1 Why Regular Lock Deadlocks on Re-Entry

```python
import threading

lock = threading.Lock()

def outer() -> None:
    with lock:
        print("outer acquired lock")
        inner()       # 💀 DEADLOCK — same thread tries to acquire again

def inner() -> None:
    with lock:        # Blocks forever — Lock does not track ownership
        print("inner acquired lock")

# outer()   # Would deadlock!
```

### 8.2 How RLock Works

An `RLock` (reentrant lock) tracks **which thread** owns it and how many times it has been acquired. The same thread can acquire it multiple times without deadlocking. It must release it the same number of times.

```python
import threading

rlock = threading.RLock()

def outer() -> None:
    with rlock:
        print("outer acquired RLock")
        inner()       # ✅ Same thread — RLock allows re-entry

def inner() -> None:
    with rlock:        # Increments internal counter; doesn't block
        print("inner acquired RLock")

outer()
# Output:
# outer acquired RLock
# inner acquired RLock
```

### 8.3 Ownership Tracking

```python
import threading

rlock = threading.RLock()

def recursive_sum(n: int) -> int:
    with rlock:       # Acquired n+1 times by the same thread
        if n <= 0:
            return 0
        return n + recursive_sum(n - 1)

result = recursive_sum(10)
print(f"Sum = {result}")   # 55
```

### 8.4 Use Cases

- **Recursive algorithms** on shared data structures.
- **Layered APIs** where a public method calls another public method, both needing synchronization.
- **Libraries** that cannot control whether callers already hold a lock.

### 8.5 Example: Recursive Data Structure Access

```python
import threading
from typing import Any


class ThreadSafeTree:
    """A thread-safe tree where traversal methods may call each other."""

    def __init__(self, value: Any) -> None:
        self.value = value
        self.children: list["ThreadSafeTree"] = []
        self._lock = threading.RLock()

    def add_child(self, value: Any) -> "ThreadSafeTree":
        with self._lock:
            child = ThreadSafeTree(value)
            self.children.append(child)
            return child

    def find(self, target: Any) -> bool:
        """Recursively search the tree. Needs reentrant locking."""
        with self._lock:
            if self.value == target:
                return True
            return any(child.find(target) for child in self.children)

    def depth(self) -> int:
        with self._lock:
            if not self.children:
                return 0
            return 1 + max(child.depth() for child in self.children)

    def to_list(self) -> list:
        """Pre-order traversal."""
        with self._lock:
            result = [self.value]
            for child in self.children:
                result.extend(child.to_list())   # Re-enters lock
            return result


root = ThreadSafeTree("root")
a = root.add_child("A")
b = root.add_child("B")
a.add_child("A1")
a.add_child("A2")
b.add_child("B1")

print(f"Tree: {root.to_list()}")
print(f"Depth: {root.depth()}")
print(f"Find 'A2': {root.find('A2')}")
print(f"Find 'C': {root.find('C')}")
```

### Common Pitfalls

- Using `RLock` when `Lock` suffices — `RLock` has slightly more overhead.
- Forgetting that `RLock` must be released the same number of times it is acquired.
- A different thread cannot release an `RLock` — only the owner can.

### Interview Tips

- "RLock tracks ownership, so the same thread can acquire it multiple times without deadlocking."
- "I use RLock when methods that hold the lock need to call other synchronized methods."
- "RLock has slightly higher overhead than Lock — use Lock when reentrancy is not needed."

---

## 9. Semaphores

### 9.1 Counting Semaphore Concept

A **semaphore** maintains an internal counter. `acquire()` decrements the counter (blocking if it would go below zero), and `release()` increments it. Unlike a lock, a semaphore allows **multiple threads** (up to the counter value) to enter a section simultaneously.

```python
import threading
import time

semaphore = threading.Semaphore(3)   # Allow 3 concurrent threads


def limited_access(thread_id: int) -> None:
    print(f"Thread {thread_id} waiting to acquire...")
    with semaphore:
        print(f"Thread {thread_id} acquired (slots in use)")
        time.sleep(2)
    print(f"Thread {thread_id} released")


threads = [threading.Thread(target=limited_access, args=(i,)) for i in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()
# Only 3 threads run concurrently; others wait.
```

### 9.2 BoundedSemaphore

A `BoundedSemaphore` raises `ValueError` if you release more times than you acquire. This catches programming errors.

```python
import threading

sem = threading.BoundedSemaphore(2)

sem.acquire()
sem.release()

# Extra release → error:
try:
    sem.release()   # One too many
except ValueError as e:
    print(f"BoundedSemaphore caught error: {e}")
    # "Semaphore released too many times"
```

### 9.3 Use Case: Connection Pool

```python
import threading
import time
import random
from collections import deque


class ConnectionPool:
    """Thread-safe database connection pool using a semaphore."""

    def __init__(self, max_connections: int) -> None:
        self._semaphore = threading.BoundedSemaphore(max_connections)
        self._lock = threading.Lock()
        self._connections: deque[str] = deque(
            f"conn-{i}" for i in range(max_connections)
        )

    def acquire_connection(self) -> str:
        self._semaphore.acquire()      # Block if no connections available
        with self._lock:
            return self._connections.popleft()

    def release_connection(self, conn: str) -> None:
        with self._lock:
            self._connections.append(conn)
        self._semaphore.release()


pool = ConnectionPool(max_connections=3)


def db_query(query_id: int) -> None:
    conn = pool.acquire_connection()
    try:
        print(f"Query {query_id} using {conn}")
        time.sleep(random.uniform(0.5, 1.5))   # Simulate query
        print(f"Query {query_id} done with {conn}")
    finally:
        pool.release_connection(conn)


threads = [threading.Thread(target=db_query, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("All queries complete.")
```

### 9.4 Use Case: Rate Limiting

```python
import threading
import time


class RateLimiter:
    """Token-bucket rate limiter using a semaphore."""

    def __init__(self, max_requests: int, refill_interval: float) -> None:
        self._semaphore = threading.Semaphore(max_requests)
        self._max = max_requests
        self._interval = refill_interval
        self._refiller = threading.Thread(target=self._refill, daemon=True)
        self._refiller.start()

    def _refill(self) -> None:
        while True:
            time.sleep(self._interval)
            for _ in range(self._max):
                try:
                    self._semaphore.release()
                except ValueError:
                    break     # Already at max (BoundedSemaphore)

    def acquire(self) -> None:
        self._semaphore.acquire()


limiter = RateLimiter(max_requests=5, refill_interval=1.0)


def make_request(req_id: int) -> None:
    limiter.acquire()
    print(f"[{time.strftime('%H:%M:%S')}] Request {req_id} executed")


threads = [threading.Thread(target=make_request, args=(i,)) for i in range(15)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 9.5 Semaphore vs Lock Comparison

| Feature | Lock | Semaphore |
|---|---|---|
| Max concurrent holders | 1 | N (configurable) |
| Ownership | Not tracked (Lock) | Not tracked |
| Use case | Mutual exclusion | Resource limiting |
| Reentrant variant | RLock | — |
| Over-release detection | No | BoundedSemaphore: Yes |

### Common Pitfalls

- Using `Semaphore` instead of `BoundedSemaphore` — extra releases go undetected and inflate the counter.
- Using a semaphore with count=1 instead of a Lock — works, but Lock is clearer and slightly more efficient.
- Not using `try/finally` or context manager — release may be skipped on exception.

### Interview Tips

- "A semaphore is a generalized lock — it allows N concurrent accessors instead of just one."
- "I'd use `BoundedSemaphore` in production to catch accidental extra releases."
- "Connection pools and rate limiters are classic semaphore use cases."

---

## 10. Conditions (threading.Condition)

### 10.1 wait(), notify(), notify_all()

A `Condition` combines a lock with a **wait/notify** mechanism. Threads can:

- `wait()`: release the lock and block until notified.
- `notify(n=1)`: wake up `n` waiting threads.
- `notify_all()`: wake up **all** waiting threads.

```python
import threading
import time

condition = threading.Condition()
data_ready = False
shared_data = None


def producer() -> None:
    global data_ready, shared_data
    time.sleep(1)          # Simulate preparation

    with condition:
        shared_data = {"result": 42}
        data_ready = True
        print("Producer: data is ready, notifying consumers")
        condition.notify_all()


def consumer(consumer_id: int) -> None:
    with condition:
        while not data_ready:           # Always check in a loop (spurious wakeups)
            print(f"Consumer {consumer_id}: waiting...")
            condition.wait()
        print(f"Consumer {consumer_id}: got data = {shared_data}")


threads = [
    threading.Thread(target=consumer, args=(i,))
    for i in range(3)
]
threads.append(threading.Thread(target=producer))

for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 10.2 wait_for() — Predicate-Based Waiting

```python
import threading

condition = threading.Condition()
items: list[int] = []


def consumer() -> None:
    with condition:
        # wait_for takes a predicate — cleaner than a while loop
        condition.wait_for(lambda: len(items) >= 3)
        print(f"Consumer: got {items}")


def producer() -> None:
    for i in range(5):
        with condition:
            items.append(i)
            print(f"Producer: added {i}, total = {len(items)}")
            condition.notify()


t1 = threading.Thread(target=consumer)
t2 = threading.Thread(target=producer)
t1.start(); t2.start()
t1.join(); t2.join()
```

### 10.3 Spurious Wakeups

A thread may wake up from `wait()` even though no thread called `notify()`. This is a property of many threading implementations (including POSIX threads). **Always** use a predicate loop:

```python
# ❌ BAD — no predicate check
with condition:
    condition.wait()
    process(data)

# ✅ GOOD — loop with predicate
with condition:
    while not data_ready:
        condition.wait()
    process(data)

# ✅ ALSO GOOD — wait_for handles the loop
with condition:
    condition.wait_for(lambda: data_ready)
    process(data)
```

### 10.4 Complete Example: Bounded Buffer (Producer-Consumer)

```python
import threading
import time
import random


class BoundedBuffer:
    """Thread-safe bounded buffer using Condition variables."""

    def __init__(self, capacity: int) -> None:
        self._buffer: list = []
        self._capacity = capacity
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def put(self, item) -> None:
        with self._not_full:
            while len(self._buffer) >= self._capacity:
                print(f"  Buffer full, producer waiting...")
                self._not_full.wait()
            self._buffer.append(item)
            print(f"  Produced: {item}  (buffer size: {len(self._buffer)})")
            self._not_empty.notify()

    def get(self):
        with self._not_empty:
            while len(self._buffer) == 0:
                print(f"  Buffer empty, consumer waiting...")
                self._not_empty.wait()
            item = self._buffer.pop(0)
            print(f"  Consumed: {item}  (buffer size: {len(self._buffer)})")
            self._not_full.notify()
            return item

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)


buffer = BoundedBuffer(capacity=5)


def producer(producer_id: int, count: int) -> None:
    for i in range(count):
        item = f"P{producer_id}-{i}"
        buffer.put(item)
        time.sleep(random.uniform(0.05, 0.2))


def consumer(consumer_id: int, count: int) -> None:
    for _ in range(count):
        item = buffer.get()
        time.sleep(random.uniform(0.1, 0.3))


producers = [threading.Thread(target=producer, args=(i, 5)) for i in range(2)]
consumers = [threading.Thread(target=consumer, args=(i, 5)) for i in range(2)]

for t in producers + consumers:
    t.start()
for t in producers + consumers:
    t.join()

print(f"Final buffer size: {buffer.size}")
```

### Common Pitfalls

- Not using a predicate loop — spurious wakeups cause bugs.
- Calling `notify()` without holding the lock — raises `RuntimeError`.
- Using `notify()` when `notify_all()` is needed — some waiters may never wake up.
- Forgetting that `wait()` releases and re-acquires the lock.

### Interview Tips

- "A Condition is a lock + wait/notify. I always check my predicate in a while loop to handle spurious wakeups."
- "`wait_for(predicate)` is a cleaner alternative to manual while loops."
- "Bounded buffer (producer-consumer) is the classic Condition use case."

---

## 11. Events (threading.Event)

### 11.1 set(), clear(), wait()

An `Event` is a simple flag: it is either **set** (True) or **cleared** (False). Threads can wait for it to become set.

```python
import threading
import time

event = threading.Event()


def waiter(name: str) -> None:
    print(f"{name}: waiting for event...")
    event.wait()              # Blocks until event.set()
    print(f"{name}: event received!")


def setter() -> None:
    print("Setter: preparing...")
    time.sleep(2)
    print("Setter: setting event!")
    event.set()               # All waiters wake up


threads = [threading.Thread(target=waiter, args=(f"W{i}",)) for i in range(3)]
threads.append(threading.Thread(target=setter))

for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 11.2 One-Shot Signaling

```python
import threading
import time


class ServiceCoordinator:
    """Coordinate service startup using Events."""

    def __init__(self) -> None:
        self.db_ready = threading.Event()
        self.cache_ready = threading.Event()
        self.all_ready = threading.Event()

    def start_database(self) -> None:
        print("Database: starting...")
        time.sleep(2)
        print("Database: ready ✓")
        self.db_ready.set()

    def start_cache(self) -> None:
        print("Cache: waiting for database...")
        self.db_ready.wait()      # Cache depends on DB
        print("Cache: starting...")
        time.sleep(1)
        print("Cache: ready ✓")
        self.cache_ready.set()

    def start_api(self) -> None:
        print("API: waiting for all services...")
        self.db_ready.wait()
        self.cache_ready.wait()
        print("API: all dependencies ready, starting...")
        time.sleep(0.5)
        print("API: ready ✓")
        self.all_ready.set()


coordinator = ServiceCoordinator()

threads = [
    threading.Thread(target=coordinator.start_database, name="db"),
    threading.Thread(target=coordinator.start_cache, name="cache"),
    threading.Thread(target=coordinator.start_api, name="api"),
]

for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"\nAll services up: {coordinator.all_ready.is_set()}")
```

### 11.3 wait() with Timeout

```python
import threading

event = threading.Event()

result = event.wait(timeout=2.0)
if result:
    print("Event was set!")
else:
    print("Timed out after 2 seconds.")
```

### 11.4 Resettable Event (set → clear → set)

```python
import threading
import time


def traffic_light(event: threading.Event) -> None:
    """Alternates between green and red."""
    while True:
        event.set()
        print("🟢 Green — go!")
        time.sleep(2)
        event.clear()
        print("🔴 Red — stop!")
        time.sleep(2)


def car(car_id: int, event: threading.Event) -> None:
    for _ in range(3):
        event.wait()           # Wait for green light
        print(f"  Car {car_id}: driving through")
        time.sleep(0.5)


event = threading.Event()
light = threading.Thread(target=traffic_light, args=(event,), daemon=True)
light.start()

cars = [threading.Thread(target=car, args=(i, event)) for i in range(3)]
for c in cars:
    c.start()
for c in cars:
    c.join()
```

### 11.5 Event vs Condition Comparison

| Feature | Event | Condition |
|---|---|---|
| State | Binary (set/cleared) | Arbitrary predicate |
| Multiple predicates | No | Yes |
| Notify specific threads | No (all waiters) | Yes (`notify(n)`) |
| Use case | Simple signaling | Complex coordination |
| Complexity | Very low | Moderate |

### Common Pitfalls

- Using `Event` when you need `Condition` — Events cannot encode complex state.
- Forgetting to `clear()` an Event before reuse.
- Race condition between `clear()` and `wait()` — threads may miss the event.

### Interview Tips

- "Event is the simplest signaling primitive — a thread-safe boolean flag."
- "I use Events for one-shot signals like 'database is ready' or 'shutdown requested'."
- "For recurring or stateful coordination, I'd use a Condition instead."

---

## 12. Barriers (threading.Barrier)

### 12.1 Synchronization Point

A `Barrier` blocks threads until a fixed number of them have all called `wait()`. Then all are released simultaneously.

```python
import threading
import time
import random

barrier = threading.Barrier(4)


def worker(worker_id: int) -> None:
    # Phase 1: each worker does its own setup
    setup_time = random.uniform(0.5, 2.0)
    print(f"Worker {worker_id}: setting up ({setup_time:.1f}s)...")
    time.sleep(setup_time)

    print(f"Worker {worker_id}: waiting at barrier")
    barrier.wait()

    # Phase 2: all workers proceed together
    print(f"Worker {worker_id}: barrier passed, working together!")


threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 12.2 Barrier with Action

```python
import threading
import time

def barrier_action() -> None:
    """Called by exactly one thread when the barrier is tripped."""
    print("=== All threads reached the barrier — starting next phase ===")

barrier = threading.Barrier(3, action=barrier_action)


def phase_worker(worker_id: int) -> None:
    for phase in range(3):
        print(f"Worker {worker_id}: executing phase {phase}")
        time.sleep(0.5)
        barrier.wait()     # Synchronize between phases


threads = [threading.Thread(target=phase_worker, args=(i,)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 12.3 Broken Barriers

If a thread waiting at the barrier is interrupted or times out, the barrier enters a **broken** state. All current and future waiters receive `BrokenBarrierError`.

```python
import threading

barrier = threading.Barrier(3, timeout=2)


def worker(worker_id: int) -> None:
    try:
        print(f"Worker {worker_id}: waiting at barrier")
        barrier.wait()
        print(f"Worker {worker_id}: passed!")
    except threading.BrokenBarrierError:
        print(f"Worker {worker_id}: barrier is broken!")


# Only 2 threads — the 3rd never arrives
threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Barrier broken: {barrier.broken}")

# Reset the barrier for reuse:
barrier.reset()
print(f"After reset — broken: {barrier.broken}")
```

### 12.4 Example: Parallel Computation Phases

```python
"""MapReduce-style parallel computation with barrier synchronization."""

import threading
import random

NUM_WORKERS = 4
DATA_SIZE = 100

barrier = threading.Barrier(NUM_WORKERS)
local_sums = [0] * NUM_WORKERS
data = [random.randint(1, 100) for _ in range(DATA_SIZE)]


def map_reduce_worker(worker_id: int) -> None:
    chunk_size = DATA_SIZE // NUM_WORKERS
    start = worker_id * chunk_size
    end = start + chunk_size if worker_id < NUM_WORKERS - 1 else DATA_SIZE

    # Phase 1: Map — compute local sum
    local_sums[worker_id] = sum(data[start:end])
    print(f"Worker {worker_id}: local sum of data[{start}:{end}] = {local_sums[worker_id]}")

    barrier.wait()     # Synchronize — all local sums are ready

    # Phase 2: Reduce — only worker 0 aggregates
    if worker_id == 0:
        total = sum(local_sums)
        print(f"\nTotal sum: {total}")
        print(f"Verification: {sum(data)}")


threads = [threading.Thread(target=map_reduce_worker, args=(i,)) for i in range(NUM_WORKERS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Common Pitfalls

- Not handling `BrokenBarrierError` — if one thread crashes, all others hang or get an unhandled exception.
- Using barriers with daemon threads — the daemon may be killed before reaching the barrier.
- Setting the wrong party count — deadlock if too many, `BrokenBarrierError` if too few.

### Interview Tips

- "A Barrier synchronizes N threads at a common point — like a meeting point."
- "The `action` parameter lets one thread perform setup between phases."
- "I always handle `BrokenBarrierError` and set a timeout to prevent indefinite hangs."

---

## 13. Queues (queue module)

### 13.1 Queue, LifoQueue, PriorityQueue

```python
import queue

# FIFO (First In, First Out) — default
fifo = queue.Queue(maxsize=10)
fifo.put("first")
fifo.put("second")
print(fifo.get())          # "first"

# LIFO (Last In, First Out) — stack
lifo = queue.LifoQueue()
lifo.put("first")
lifo.put("second")
print(lifo.get())          # "second"

# Priority Queue — lowest priority number first
pq = queue.PriorityQueue()
pq.put((3, "low priority"))
pq.put((1, "high priority"))
pq.put((2, "medium priority"))
print(pq.get())            # (1, "high priority")
print(pq.get())            # (2, "medium priority")
```

### 13.2 Thread-Safe by Design

All `queue.Queue` methods are **thread-safe** — no external locking needed.

### 13.3 put(), get(), task_done(), join()

```python
import queue
import threading
import time


q = queue.Queue()

def worker() -> None:
    while True:
        item = q.get()               # Blocks until an item is available
        if item is None:             # Sentinel to stop
            q.task_done()
            break
        print(f"Processing {item}")
        time.sleep(0.1)
        q.task_done()                # Signal that this item is done


# Start workers
threads = [threading.Thread(target=worker, daemon=True) for _ in range(3)]
for t in threads:
    t.start()

# Enqueue work
for i in range(10):
    q.put(f"task-{i}")

# Wait for all tasks to be processed
q.join()
print("All tasks processed!")

# Stop workers
for _ in threads:
    q.put(None)
for t in threads:
    t.join()
```

### 13.4 Non-Blocking and Timeout Operations

```python
import queue

q = queue.Queue(maxsize=2)

# Non-blocking put
q.put("a")
q.put("b")
try:
    q.put("c", block=False)         # Queue is full
except queue.Full:
    print("Queue is full!")

# Non-blocking get
print(q.get(block=False))           # "a"
print(q.get(block=False))           # "b"
try:
    q.get(block=False)              # Queue is empty
except queue.Empty:
    print("Queue is empty!")

# With timeout
q2 = queue.Queue()
try:
    q2.get(timeout=1.0)             # Wait 1 second, then raise
except queue.Empty:
    print("Timed out after 1 second")
```

### 13.5 Producer-Consumer Pattern

```python
import queue
import threading
import time
import random


def producer(q: queue.Queue, producer_id: int, num_items: int) -> None:
    for i in range(num_items):
        item = {"producer": producer_id, "item": i, "data": random.random()}
        q.put(item)
        print(f"  P{producer_id} produced item {i}")
        time.sleep(random.uniform(0.01, 0.1))
    print(f"  P{producer_id} finished")


def consumer(q: queue.Queue, consumer_id: int) -> None:
    while True:
        try:
            item = q.get(timeout=2.0)
        except queue.Empty:
            print(f"  C{consumer_id}: no items for 2s, shutting down")
            break
        print(f"  C{consumer_id} consumed: {item}")
        q.task_done()
        time.sleep(random.uniform(0.05, 0.15))


q = queue.Queue(maxsize=5)

producers = [
    threading.Thread(target=producer, args=(q, i, 5))
    for i in range(2)
]
consumers = [
    threading.Thread(target=consumer, args=(q, i))
    for i in range(3)
]

for t in producers + consumers:
    t.start()
for t in producers:
    t.join()

q.join()      # Wait until all items are processed
print("All items processed.")
```

### 13.6 Example: Task Pipeline (Multi-Stage)

```python
"""Multi-stage processing pipeline using queues."""

import queue
import threading
import time


def stage_1_fetch(input_q: queue.Queue, output_q: queue.Queue) -> None:
    """Fetch raw data."""
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            input_q.task_done()
            break
        result = f"fetched({item})"
        output_q.put(result)
        input_q.task_done()
        time.sleep(0.05)


def stage_2_transform(input_q: queue.Queue, output_q: queue.Queue) -> None:
    """Transform data."""
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            input_q.task_done()
            break
        result = f"transformed({item})"
        output_q.put(result)
        input_q.task_done()
        time.sleep(0.03)


def stage_3_store(input_q: queue.Queue, results: list) -> None:
    """Store processed data."""
    while True:
        item = input_q.get()
        if item is None:
            input_q.task_done()
            break
        result = f"stored({item})"
        results.append(result)
        input_q.task_done()
        time.sleep(0.02)


q1 = queue.Queue()
q2 = queue.Queue()
q3 = queue.Queue()
final_results: list[str] = []

t1 = threading.Thread(target=stage_1_fetch, args=(q1, q2))
t2 = threading.Thread(target=stage_2_transform, args=(q2, q3))
t3 = threading.Thread(target=stage_3_store, args=(q3, final_results))

t1.start(); t2.start(); t3.start()

for i in range(10):
    q1.put(f"data-{i}")
q1.put(None)      # Sentinel

t1.join(); t2.join(); t3.join()

print(f"Pipeline produced {len(final_results)} results:")
for r in final_results:
    print(f"  {r}")
```

### 13.7 Example: Worker Pool

```python
"""Generic worker pool using queue.Queue."""

import queue
import threading
import time
import random
from typing import Callable, Any


class WorkerPool:
    def __init__(self, num_workers: int, task_handler: Callable) -> None:
        self._task_queue: queue.Queue = queue.Queue()
        self._result_queue: queue.Queue = queue.Queue()
        self._workers: list[threading.Thread] = []
        self._task_handler = task_handler

        for i in range(num_workers):
            t = threading.Thread(
                target=self._worker_loop, args=(i,), daemon=True
            )
            self._workers.append(t)
            t.start()

    def _worker_loop(self, worker_id: int) -> None:
        while True:
            task = self._task_queue.get()
            if task is None:
                self._task_queue.task_done()
                break
            try:
                result = self._task_handler(task)
                self._result_queue.put(("ok", task, result))
            except Exception as e:
                self._result_queue.put(("error", task, e))
            finally:
                self._task_queue.task_done()

    def submit(self, task: Any) -> None:
        self._task_queue.put(task)

    def wait_completion(self) -> list:
        self._task_queue.join()
        results = []
        while not self._result_queue.empty():
            results.append(self._result_queue.get())
        return results

    def shutdown(self) -> None:
        for _ in self._workers:
            self._task_queue.put(None)
        for w in self._workers:
            w.join()


def process_task(task: dict) -> str:
    time.sleep(random.uniform(0.1, 0.5))
    return f"Processed {task['name']} = {task['value'] * 2}"


pool = WorkerPool(num_workers=4, task_handler=process_task)

for i in range(20):
    pool.submit({"name": f"task-{i}", "value": i})

results = pool.wait_completion()
pool.shutdown()

for status, task, result in results:
    print(f"  [{status}] {task['name']}: {result}")
```

### Common Pitfalls

- Calling `q.join()` without matching `task_done()` calls — hangs forever.
- Using a `dict` or `list` instead of `queue.Queue` for thread communication — not thread-safe.
- Not using sentinel values to signal worker shutdown.
- Using `q.empty()` for control flow — it is **not reliable** in concurrent code (TOCTOU race).

### Interview Tips

- "`queue.Queue` is thread-safe by design and is the canonical way to communicate between threads."
- "`task_done()` and `join()` let me wait for all submitted work to complete."
- "For multi-stage pipelines, I chain queues between stages."

---

## 14. Race Conditions

### 14.1 What is a Race Condition?

A **race condition** occurs when the behavior of a program depends on the **relative timing** of threads, leading to incorrect results.

### 14.2 Check-Then-Act Race

```python
"""Check-then-act race condition: checking and acting are not atomic."""

import threading
import time


class UnsafeUniqueIDGenerator:
    def __init__(self) -> None:
        self._ids: set[int] = set()
        self._next_id = 0

    def generate(self) -> int:
        """NOT thread-safe — race between check and increment."""
        current = self._next_id        # Read
        time.sleep(0.0001)             # Amplify the race window
        self._next_id = current + 1    # Write — another thread may have read same value
        self._ids.add(current)
        return current


class SafeUniqueIDGenerator:
    def __init__(self) -> None:
        self._ids: set[int] = set()
        self._next_id = 0
        self._lock = threading.Lock()

    def generate(self) -> int:
        with self._lock:
            current = self._next_id
            self._next_id = current + 1
            self._ids.add(current)
            return current


# Demonstrate the race:
unsafe_gen = UnsafeUniqueIDGenerator()
safe_gen = SafeUniqueIDGenerator()

unsafe_results: list[int] = []
safe_results: list[int] = []


def generate_ids(gen, results: list, count: int) -> None:
    for _ in range(count):
        results.append(gen.generate())


threads = [
    threading.Thread(target=generate_ids, args=(unsafe_gen, unsafe_results, 100))
    for _ in range(4)
]
for t in threads:
    t.start()
for t in threads:
    t.join()

threads = [
    threading.Thread(target=generate_ids, args=(safe_gen, safe_results, 100))
    for _ in range(4)
]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Unsafe: {len(unsafe_results)} IDs, {len(set(unsafe_results))} unique")
print(f"Safe:   {len(safe_results)} IDs, {len(set(safe_results))} unique")
# Unsafe will have duplicates; Safe will not.
```

### 14.3 Read-Modify-Write Race

```python
"""Classic read-modify-write race: counter += 1 is NOT atomic."""

import threading

counter = 0


def unsafe_increment(n: int) -> None:
    global counter
    for _ in range(n):
        counter += 1       # Read → Modify → Write (three operations!)


threads = [threading.Thread(target=unsafe_increment, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Expected: 400000, Got: {counter}")
# Typically less than 400000 due to lost updates.
```

**Why `counter += 1` is not atomic:**

```
Thread A: READ counter (=0)
Thread B: READ counter (=0)
Thread A: WRITE counter (=1)
Thread B: WRITE counter (=1)   # Overwrites A's update!
```

### 14.4 Time-of-Check-to-Time-of-Use (TOCTOU)

```python
"""TOCTOU: the state changes between checking and using."""

import threading
import os
import tempfile

lock = threading.Lock()


def unsafe_write(filepath: str, data: str) -> None:
    """TOCTOU bug: file may be created between check and write."""
    if not os.path.exists(filepath):       # Check
        # Another thread could create the file here!
        with open(filepath, "w") as f:      # Use
            f.write(data)


def safe_write(filepath: str, data: str) -> None:
    """Fix: use atomic operations or locks."""
    with lock:
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(data)


# Even better: use os.open with O_CREAT | O_EXCL for atomic file creation
def atomic_write(filepath: str, data: str) -> bool:
    try:
        fd = os.open(filepath, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(data)
        return True
    except FileExistsError:
        return False
```

### 14.5 Detection Strategies

1. **Code review**: look for shared mutable state accessed without locks.
2. **ThreadSanitizer**: available via `clang -fsanitize=thread` for C extensions.
3. **Stress testing**: run concurrent code thousands of times with `time.sleep(0)` to increase context-switch frequency.
4. **Static analysis**: tools like `pylint` and `mypy` don't catch races, but custom linters can flag unprotected globals.

```python
"""Stress-test to detect races."""

import threading
import sys

sys.setswitchinterval(0.000001)     # Increase context switches


def stress_test(iterations: int = 100) -> None:
    for i in range(iterations):
        counter = [0]        # Use list to share mutable state
        lock = threading.Lock()

        def increment() -> None:
            for _ in range(10_000):
                # Try both with and without lock to compare:
                with lock:
                    counter[0] += 1

        threads = [threading.Thread(target=increment) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = 40_000
        if counter[0] != expected:
            print(f"Race detected on iteration {i}! "
                  f"Expected {expected}, got {counter[0]}")
            return

    print(f"No race detected in {iterations} iterations (with lock).")


stress_test()
```

### 14.6 Prevention with Various Synchronization Primitives

| Primitive | Use When |
|---|---|
| `Lock` | Mutual exclusion for any critical section |
| `RLock` | Recursive or layered locking needed |
| `Semaphore` | Limit concurrent access to N |
| `Condition` | Complex wait/notify coordination |
| `Queue` | Producer-consumer data passing |
| `Event` | Simple signaling |
| Immutable objects | Eliminate shared mutable state entirely |

### Common Pitfalls

- Assuming Python operations are atomic — `list.append()` is (due to GIL), but `counter += 1` is not.
- Testing concurrency with small inputs — races are timing-dependent and may not appear in trivial tests.
- Using `time.sleep()` to "fix" races — this is never correct, only makes them less frequent.

### Interview Tips

- "A race condition means the outcome depends on thread scheduling, which is non-deterministic."
- "The three classic types are check-then-act, read-modify-write, and TOCTOU."
- "I prevent races with locks, immutable data structures, or message-passing (queues)."

---

## 15. Deadlocks

### 15.1 What is a Deadlock?

A **deadlock** occurs when two or more threads are each waiting for a resource held by the other, creating a cycle of dependencies where none can proceed.

### 15.2 Four Coffman Conditions

All four conditions must hold **simultaneously** for deadlock to occur:

1. **Mutual exclusion**: resources can only be held by one thread at a time.
2. **Hold and wait**: a thread holds one resource while waiting for another.
3. **No preemption**: resources cannot be forcibly taken from a thread.
4. **Circular wait**: a cycle exists in the resource-wait graph.

Breaking **any one** condition prevents deadlock.

### 15.3 Classic Deadlock Example

```python
"""Classic deadlock: two threads, two locks, opposite order."""

import threading
import time

lock_a = threading.Lock()
lock_b = threading.Lock()


def thread_1() -> None:
    print("T1: acquiring lock_a...")
    with lock_a:
        print("T1: acquired lock_a, sleeping...")
        time.sleep(0.1)     # Increase likelihood of deadlock
        print("T1: acquiring lock_b...")
        with lock_b:        # 💀 Blocks — T2 holds lock_b
            print("T1: acquired both locks!")


def thread_2() -> None:
    print("T2: acquiring lock_b...")
    with lock_b:
        print("T2: acquired lock_b, sleeping...")
        time.sleep(0.1)
        print("T2: acquiring lock_a...")
        with lock_a:        # 💀 Blocks — T1 holds lock_a
            print("T2: acquired both locks!")


# WARNING: This WILL deadlock. Only uncomment to demonstrate.
# t1 = threading.Thread(target=thread_1)
# t2 = threading.Thread(target=thread_2)
# t1.start(); t2.start()
# t1.join(); t2.join()

print("(Deadlock example — commented out to avoid hanging)")
```

### 15.4 Lock Ordering to Prevent Deadlock

Break the **circular wait** condition by always acquiring locks in the same order.

```python
import threading
import time


lock_a = threading.Lock()
lock_b = threading.Lock()


def safe_thread_1() -> None:
    with lock_a:           # Always acquire A before B
        time.sleep(0.1)
        with lock_b:
            print("T1: acquired both locks (A then B)")


def safe_thread_2() -> None:
    with lock_a:           # Same order: A before B
        time.sleep(0.1)
        with lock_b:
            print("T2: acquired both locks (A then B)")


t1 = threading.Thread(target=safe_thread_1)
t2 = threading.Thread(target=safe_thread_2)
t1.start(); t2.start()
t1.join(); t2.join()
print("No deadlock!")
```

### 15.5 Generalized Lock Ordering

```python
import threading
from contextlib import contextmanager
from typing import Generator


@contextmanager
def acquire_locks(*locks: threading.Lock) -> Generator[None, None, None]:
    """Acquire multiple locks in a consistent order (by id) to prevent deadlock."""
    sorted_locks = sorted(locks, key=id)
    try:
        for lock in sorted_locks:
            lock.acquire()
        yield
    finally:
        for lock in reversed(sorted_locks):
            lock.release()


lock_x = threading.Lock()
lock_y = threading.Lock()
lock_z = threading.Lock()


def worker_a() -> None:
    with acquire_locks(lock_z, lock_x, lock_y):     # Order doesn't matter
        print("Worker A: holding all three locks")


def worker_b() -> None:
    with acquire_locks(lock_y, lock_z, lock_x):     # Different call order, same acquire order
        print("Worker B: holding all three locks")


t1 = threading.Thread(target=worker_a)
t2 = threading.Thread(target=worker_b)
t1.start(); t2.start()
t1.join(); t2.join()
```

### 15.6 Timeout-Based Prevention

Break the **hold and wait** condition using timeouts.

```python
import threading
import time


lock_a = threading.Lock()
lock_b = threading.Lock()


def try_acquire_both(name: str, first: threading.Lock, second: threading.Lock) -> bool:
    """Try to acquire both locks with timeout — back off on failure."""
    for attempt in range(5):
        acquired_first = first.acquire(timeout=0.1)
        if not acquired_first:
            continue

        acquired_second = second.acquire(timeout=0.1)
        if acquired_second:
            return True        # Got both
        else:
            first.release()    # Release first to avoid hold-and-wait
            time.sleep(0.01 * (attempt + 1))    # Back off

    return False


def worker(name: str, first: threading.Lock, second: threading.Lock) -> None:
    if try_acquire_both(name, first, second):
        try:
            print(f"{name}: acquired both locks!")
            time.sleep(0.1)
        finally:
            second.release()
            first.release()
    else:
        print(f"{name}: could not acquire both locks, giving up.")


t1 = threading.Thread(target=worker, args=("T1", lock_a, lock_b))
t2 = threading.Thread(target=worker, args=("T2", lock_b, lock_a))
t1.start(); t2.start()
t1.join(); t2.join()
```

### 15.7 Example: Dining Philosophers

```python
"""Dining Philosophers — deadlock-free with lock ordering."""

import threading
import time
import random

NUM_PHILOSOPHERS = 5
forks = [threading.Lock() for _ in range(NUM_PHILOSOPHERS)]


def philosopher(phil_id: int, meals: int) -> None:
    left = phil_id
    right = (phil_id + 1) % NUM_PHILOSOPHERS

    # Always pick up the lower-numbered fork first → breaks circular wait
    first = min(left, right)
    second = max(left, right)

    for meal in range(meals):
        # Think
        time.sleep(random.uniform(0.01, 0.05))

        # Eat
        with forks[first]:
            with forks[second]:
                print(f"Philosopher {phil_id} is eating meal {meal + 1}")
                time.sleep(random.uniform(0.01, 0.03))


threads = [
    threading.Thread(target=philosopher, args=(i, 3))
    for i in range(NUM_PHILOSOPHERS)
]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("All philosophers finished eating.")
```

### 15.8 Example: Bank Transfer (Deadlock-Free)

```python
import threading
import time


class Account:
    _next_id = 0
    _id_lock = threading.Lock()

    def __init__(self, owner: str, balance: float) -> None:
        with Account._id_lock:
            self._id = Account._next_id
            Account._next_id += 1
        self.owner = owner
        self.balance = balance
        self.lock = threading.Lock()

    def __repr__(self) -> str:
        return f"Account({self.owner}, {self.balance:.2f})"


def transfer(from_acc: Account, to_acc: Account, amount: float) -> bool:
    """Transfer money between accounts without deadlock."""
    # Lock ordering by account ID
    first, second = sorted([from_acc, to_acc], key=lambda a: a._id)

    with first.lock:
        with second.lock:
            if from_acc.balance >= amount:
                from_acc.balance -= amount
                to_acc.balance += amount
                return True
            return False


alice = Account("Alice", 1000)
bob = Account("Bob", 1000)

def transfer_loop(src: Account, dst: Account) -> None:
    for _ in range(100):
        transfer(src, dst, 10)
        time.sleep(0.001)

t1 = threading.Thread(target=transfer_loop, args=(alice, bob))
t2 = threading.Thread(target=transfer_loop, args=(bob, alice))
t1.start(); t2.start()
t1.join(); t2.join()

print(f"Alice: {alice.balance}, Bob: {bob.balance}")
print(f"Total: {alice.balance + bob.balance} (should be 2000)")
```

### Common Pitfalls

- Acquiring locks in inconsistent order across different code paths.
- Calling external code (callbacks, plugins) while holding a lock.
- Using `Lock` instead of `RLock` when a method needs to re-enter its own lock.
- Not setting timeouts on lock acquisition in production code.

### Interview Tips

- "I prevent deadlocks by enforcing a global lock ordering — always acquire the lower-ID lock first."
- "The four Coffman conditions are necessary and sufficient for deadlock."
- "Timeout-based acquisition with backoff is my fallback when strict ordering is impractical."

---

## 16. Starvation

### 16.1 What Causes Starvation

**Starvation** occurs when a thread is perpetually denied access to a resource, even though deadlock has not occurred. The system makes progress, but one or more threads never get their turn.

Common causes:

- **Priority scheduling**: high-priority threads always run first.
- **Unfair locks**: no guarantee of FIFO ordering.
- **Greedy threads**: one thread repeatedly acquires a lock before others can.

### 16.2 Priority Inversion

**Priority inversion** occurs when a low-priority thread holds a lock needed by a high-priority thread, while a medium-priority thread runs instead.

```
High-priority thread:   BLOCKED (waiting for lock held by Low)
Medium-priority thread: RUNNING (does not need the lock)
Low-priority thread:    READY (cannot run because Medium has higher priority)
```

**Solution**: **Priority inheritance** — temporarily boost the lock-holder's priority.

### 16.3 Example: Reader-Writer Starvation

```python
"""Readers-Writer lock: writers can starve if readers are continuous."""

import threading
import time
import random


class ReadWriteLock:
    """
    Simple RW lock. Writers can starve if readers arrive continuously.
    """

    def __init__(self) -> None:
        self._readers = 0
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()

    def acquire_read(self) -> None:
        with self._lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self) -> None:
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self) -> None:
        self._write_lock.acquire()

    def release_write(self) -> None:
        self._write_lock.release()


class FairReadWriteLock:
    """
    Fair RW lock: writers are not starved.
    New readers block if a writer is waiting.
    """

    def __init__(self) -> None:
        self._readers = 0
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._read_gate = threading.Lock()   # Blocks new readers when writer waits

    def acquire_read(self) -> None:
        with self._read_gate:    # If a writer holds this, new readers wait
            with self._lock:
                self._readers += 1
                if self._readers == 1:
                    self._write_lock.acquire()

    def release_read(self) -> None:
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self) -> None:
        self._read_gate.acquire()     # Block new readers
        self._write_lock.acquire()     # Wait for existing readers to finish

    def release_write(self) -> None:
        self._write_lock.release()
        self._read_gate.release()      # Allow new readers


shared_data = {"value": 0}
rw_lock = FairReadWriteLock()


def reader(reader_id: int) -> None:
    for _ in range(5):
        rw_lock.acquire_read()
        try:
            print(f"Reader {reader_id}: value = {shared_data['value']}")
            time.sleep(random.uniform(0.01, 0.05))
        finally:
            rw_lock.release_read()


def writer(writer_id: int) -> None:
    for _ in range(3):
        rw_lock.acquire_write()
        try:
            shared_data["value"] += 1
            print(f"Writer {writer_id}: set value = {shared_data['value']}")
            time.sleep(random.uniform(0.01, 0.05))
        finally:
            rw_lock.release_write()


threads = (
    [threading.Thread(target=reader, args=(i,)) for i in range(5)] +
    [threading.Thread(target=writer, args=(i,)) for i in range(2)]
)

for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Final value: {shared_data['value']}")
```

### 16.4 Solutions to Starvation

| Solution | How It Works |
|---|---|
| Fair locks (FIFO) | Threads acquire the lock in arrival order |
| Priority inheritance | Boost lock-holder's priority to match highest waiter |
| Timeouts | Give up and retry after a bounded wait |
| Lock-free algorithms | Avoid locks entirely |
| Work-stealing | Idle threads steal work from busy queues |

### Common Pitfalls

- Confusing starvation with deadlock — in starvation, the system makes progress; in deadlock, it doesn't.
- Ignoring writer starvation in reader-heavy systems.
- Assuming OS thread scheduling is fair — it is not guaranteed.

### Interview Tips

- "Starvation means a thread can never access the resource, even though the system is not deadlocked."
- "The classic example is reader-writer starvation, where continuous readers prevent writers from ever acquiring the lock."
- "I mitigate starvation with fair locks or by blocking new readers when a writer is waiting."

---

## 17. Thread Safety

### 17.1 What Makes Code Thread-Safe

Code is **thread-safe** if it behaves correctly when called from multiple threads simultaneously, without requiring the caller to provide external synchronization.

Thread-safe strategies:

1. **No shared state** — each thread works on its own data.
2. **Immutable shared state** — data cannot be modified after creation.
3. **Synchronized access** — locks, semaphores, etc. protect mutable state.
4. **Thread-local storage** — each thread has its own copy.
5. **Atomic operations** — single indivisible operations.

### 17.2 Immutable Objects

Python's built-in immutable types (`int`, `float`, `str`, `tuple`, `frozenset`, `bytes`) are inherently thread-safe for reads. However, **rebinding** a name (`x = x + 1`) is **not** atomic.

### 17.3 Thread-Local Storage

```python
import threading

local = threading.local()


class DatabaseSession:
    """Each thread gets its own database session via thread-local storage."""

    _local = threading.local()

    @classmethod
    def get_session(cls) -> str:
        if not hasattr(cls._local, "session"):
            cls._local.session = f"session-{threading.current_thread().name}"
            print(f"Created {cls._local.session}")
        return cls._local.session


def worker() -> None:
    session = DatabaseSession.get_session()
    print(f"  {threading.current_thread().name} uses {session}")
    # Call again — returns the same session for this thread
    session2 = DatabaseSession.get_session()
    assert session is session2


threads = [threading.Thread(target=worker, name=f"worker-{i}") for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 17.4 Atomic Operations in Python

Due to the GIL, some operations are **effectively atomic** in CPython:

```python
import dis

# These are single bytecodes (atomic under GIL):
my_list = [1, 2, 3]
my_dict = {}

# list.append() — single CALL bytecode
my_list.append(4)

# dict assignment — STORE_SUBSCR
my_dict["key"] = "value"

# But compound operations are NOT atomic:
counter = 0
counter += 1   # LOAD_FAST, BINARY_ADD, STORE_FAST — three bytecodes!

# Verify:
def increment():
    global counter
    counter += 1

dis.dis(increment)
```

**Important**: Even though some operations are atomic under the GIL, relying on this is **fragile and non-portable**. Always use explicit synchronization.

### 17.5 Thread-Safe Data Structures

| Data Structure | Thread-Safe? | Notes |
|---|---|---|
| `queue.Queue` | ✅ Yes | Designed for inter-thread communication |
| `collections.deque` | ✅ Partially | `append` and `popleft` are atomic under GIL |
| `dict` | ⚠️ GIL-safe only | Single operations are atomic; compound operations are not |
| `list` | ⚠️ GIL-safe only | `append` is atomic; `sort`, iteration are not |
| `set` | ❌ No | Not safe for concurrent modification |

### 17.6 Designing Thread-Safe Classes

```python
import threading
from typing import Any


class ThreadSafeDict:
    """A dictionary wrapper with explicit thread safety."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def get_or_set(self, key: str, default_factory: callable) -> Any:
        """Atomic get-or-create operation."""
        with self._lock:
            if key not in self._data:
                self._data[key] = default_factory()
            return self._data[key]

    def update_if_present(self, key: str, func: callable) -> bool:
        """Atomically update a value if the key exists."""
        with self._lock:
            if key in self._data:
                self._data[key] = func(self._data[key])
                return True
            return False

    def items(self) -> list[tuple[str, Any]]:
        with self._lock:
            return list(self._data.items())     # Return a snapshot


# Usage:
config = ThreadSafeDict()

def writer(key: str, value: str) -> None:
    for i in range(100):
        config.set(f"{key}-{i}", f"{value}-{i}")

def reader() -> None:
    for _ in range(100):
        snapshot = config.items()

threads = [
    threading.Thread(target=writer, args=("key", "val")),
    threading.Thread(target=reader),
]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"ThreadSafeDict has {len(config.items())} items")
```

### Common Pitfalls

- Assuming GIL-atomicity is sufficient — it is an implementation detail of CPython, not guaranteed by the language.
- Making only some methods thread-safe — one unprotected method is enough to cause a race.
- Returning mutable references from synchronized methods — callers can modify the object without the lock.

### Interview Tips

- "Thread-safe code works correctly under concurrent access without external synchronization."
- "I use four strategies: immutability, locking, thread-local storage, and message-passing."
- "I never rely on GIL atomicity for correctness — it's a CPython implementation detail."

---

## 18. Immutability

### 18.1 Immutable Objects in Python

Python has several built-in immutable types:

```python
# Immutable types:
x: int = 42
s: str = "hello"
t: tuple = (1, 2, 3)
f: frozenset = frozenset({1, 2, 3})
b: bytes = b"hello"

# Mutable types (NOT thread-safe by default):
l: list = [1, 2, 3]
d: dict = {"a": 1}
st: set = {1, 2, 3}
ba: bytearray = bytearray(b"hello")
```

### 18.2 Creating Immutable Classes

```python
from typing import Any


class ImmutablePoint:
    """An immutable point using __slots__ and property overrides."""

    __slots__ = ("_x", "_y")

    def __init__(self, x: float, y: float) -> None:
        object.__setattr__(self, "_x", x)
        object.__setattr__(self, "_y", y)

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("ImmutablePoint instances are immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("ImmutablePoint instances are immutable")

    def __repr__(self) -> str:
        return f"ImmutablePoint({self._x}, {self._y})"

    def translate(self, dx: float, dy: float) -> "ImmutablePoint":
        """Return a NEW point — does not modify self."""
        return ImmutablePoint(self._x + dx, self._y + dy)


p = ImmutablePoint(3, 4)
print(p)                     # ImmutablePoint(3, 4)
p2 = p.translate(1, 2)
print(p2)                    # ImmutablePoint(4, 6)

try:
    p.x = 10
except AttributeError as e:
    print(f"Cannot modify: {e}")
```

### 18.3 Frozen Dataclasses

```python
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class Config:
    """Immutable configuration — thread-safe by construction."""
    host: str
    port: int
    debug: bool = False
    allowed_origins: Tuple[str, ...] = ()     # Tuple, not list!

    def with_debug(self, debug: bool) -> "Config":
        """Create a new Config with modified debug flag."""
        return Config(
            host=self.host,
            port=self.port,
            debug=debug,
            allowed_origins=self.allowed_origins,
        )


config = Config(host="localhost", port=8080, allowed_origins=("http://example.com",))
print(config)

# Immutable:
try:
    config.port = 9090
except AttributeError as e:
    print(f"Cannot modify: {e}")

# Create modified copy:
dev_config = config.with_debug(True)
print(dev_config)
```

### 18.4 Named Tuples (Lightweight Immutability)

```python
from typing import NamedTuple


class Color(NamedTuple):
    red: int
    green: int
    blue: int
    alpha: float = 1.0

    @property
    def hex(self) -> str:
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"


RED = Color(255, 0, 0)
print(f"{RED} → {RED.hex}")     # Color(red=255, green=0, blue=0, alpha=1.0) → #ff0000

try:
    RED.red = 128
except AttributeError as e:
    print(f"Cannot modify: {e}")
```

### 18.5 Benefits for Concurrency

```python
"""Immutable objects are inherently thread-safe — no locks needed."""

import threading


@dataclass(frozen=True)
class AppState:
    counter: int
    users: Tuple[str, ...]
    settings: Config


# Shared immutable state — multiple threads can read safely
current_state = AppState(
    counter=0,
    users=("alice", "bob"),
    settings=Config(host="localhost", port=8080),
)


def reader(thread_id: int) -> None:
    state = current_state      # Read a reference (atomic)
    print(f"Thread {thread_id}: counter={state.counter}, users={state.users}")


threads = [threading.Thread(target=reader, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 18.6 Copy-on-Write Pattern

```python
"""Copy-on-write: share immutable snapshots, replace atomically."""

import threading
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SharedState:
    version: int
    data: Tuple[int, ...]


class CopyOnWriteStore:
    def __init__(self) -> None:
        self._state = SharedState(version=0, data=())
        self._lock = threading.Lock()

    def read(self) -> SharedState:
        """Lock-free read — always returns a consistent snapshot."""
        return self._state

    def append(self, value: int) -> SharedState:
        """Write creates a new immutable state object."""
        with self._lock:
            old = self._state
            self._state = SharedState(
                version=old.version + 1,
                data=old.data + (value,),
            )
            return self._state


store = CopyOnWriteStore()


def writer() -> None:
    for i in range(100):
        store.append(i)


def reader() -> None:
    for _ in range(100):
        state = store.read()     # No lock needed!
        _ = len(state.data)      # Consistent snapshot


threads = [
    threading.Thread(target=writer),
    threading.Thread(target=reader),
    threading.Thread(target=reader),
]
for t in threads:
    t.start()
for t in threads:
    t.join()

final = store.read()
print(f"Final state: version={final.version}, data_len={len(final.data)}")
```

### 18.7 Example: Immutable Value Objects

```python
from dataclasses import dataclass
from functools import cached_property


@dataclass(frozen=True, order=True)
class Money:
    amount: int           # Store in cents to avoid float issues
    currency: str

    @cached_property
    def display(self) -> str:
        dollars = self.amount / 100
        return f"${dollars:,.2f} {self.currency}"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | float) -> "Money":
        return Money(int(self.amount * factor), self.currency)


price = Money(1999, "USD")
tax = price * 0.08
total = price + tax
print(f"Price: {price.display}")
print(f"Tax:   {tax.display}")
print(f"Total: {total.display}")
```

### Common Pitfalls

- Freezing a dataclass that contains mutable fields (lists, dicts) — the container is frozen but its contents are not.
- Using `tuple` of mutable objects — the tuple is immutable, but its elements can be modified.
- Performance: creating new objects on every update can be expensive for large data structures.

### Interview Tips

- "Immutable objects are inherently thread-safe — no synchronization needed for reads."
- "I use `frozen=True` dataclasses and tuples to enforce immutability at the type level."
- "Copy-on-write gives me lock-free reads with synchronized writes."

---

## 19. Lock Contention

### 19.1 What is Contention?

**Lock contention** occurs when multiple threads compete for the same lock. High contention means threads spend significant time waiting for the lock instead of doing useful work.

```python
"""Measure lock contention."""

import threading
import time


class ContendedCounter:
    def __init__(self) -> None:
        self.value = 0
        self.lock = threading.Lock()
        self.wait_time = 0.0
        self.acquisitions = 0

    def increment(self) -> None:
        start = time.perf_counter()
        with self.lock:
            wait = time.perf_counter() - start
            self.wait_time += wait
            self.acquisitions += 1
            self.value += 1

    @property
    def avg_wait(self) -> float:
        return self.wait_time / max(self.acquisitions, 1)


counter = ContendedCounter()


def worker(n: int) -> None:
    for _ in range(n):
        counter.increment()


THREADS = 8
N = 100_000

start = time.perf_counter()
threads = [threading.Thread(target=worker, args=(N,)) for _ in range(THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
elapsed = time.perf_counter() - start

print(f"Counter: {counter.value}")
print(f"Total time: {elapsed:.3f}s")
print(f"Total lock wait: {counter.wait_time:.3f}s")
print(f"Avg wait per acquire: {counter.avg_wait * 1_000_000:.1f}µs")
```

### 19.2 Reducing Contention: Lock Splitting

Divide one lock into multiple locks that protect different data.

```python
import threading


class SingleLockStore:
    """One lock for everything — high contention."""

    def __init__(self) -> None:
        self._data: dict[str, int] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> int:
        with self._lock:
            return self._data.get(key, 0)

    def set(self, key: str, value: int) -> None:
        with self._lock:
            self._data[key] = value


class SplitLockStore:
    """Separate locks for separate categories — less contention."""

    def __init__(self) -> None:
        self._users: dict[str, int] = {}
        self._users_lock = threading.Lock()
        self._orders: dict[str, int] = {}
        self._orders_lock = threading.Lock()

    def get_user(self, key: str) -> int:
        with self._users_lock:
            return self._users.get(key, 0)

    def set_user(self, key: str, value: int) -> None:
        with self._users_lock:
            self._users[key] = value

    def get_order(self, key: str) -> int:
        with self._orders_lock:
            return self._orders.get(key, 0)

    def set_order(self, key: str, value: int) -> None:
        with self._orders_lock:
            self._orders[key] = value
```

### 19.3 Reducing Contention: Lock Striping

Use a hash to distribute keys across multiple locks.

```python
import threading
from typing import Any


class StripedMap:
    """Hash map with lock striping — like Java's ConcurrentHashMap."""

    def __init__(self, num_stripes: int = 16) -> None:
        self._num_stripes = num_stripes
        self._stripes = [threading.Lock() for _ in range(num_stripes)]
        self._data: dict[str, Any] = {}

    def _get_stripe(self, key: str) -> threading.Lock:
        return self._stripes[hash(key) % self._num_stripes]

    def get(self, key: str) -> Any:
        with self._get_stripe(key):
            return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._get_stripe(key):
            self._data[key] = value

    def delete(self, key: str) -> None:
        with self._get_stripe(key):
            self._data.pop(key, None)

    def size(self) -> int:
        """Requires all stripes — expensive."""
        total = 0
        for stripe in self._stripes:
            stripe.acquire()
        try:
            total = len(self._data)
        finally:
            for stripe in self._stripes:
                stripe.release()
        return total


# Benchmark
import time

striped = StripedMap(num_stripes=32)
single = SingleLockStore()


def bench_write(store, n: int, prefix: str) -> None:
    for i in range(n):
        if hasattr(store, "set"):
            store.set(f"{prefix}-{i}", i)


N = 50_000
THREADS = 8

# Striped
start = time.perf_counter()
threads = [threading.Thread(target=bench_write, args=(striped, N, f"t{i}")) for i in range(THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"StripedMap ({THREADS} threads × {N} writes): {time.perf_counter() - start:.3f}s")

# Single lock
start = time.perf_counter()
threads = [threading.Thread(target=bench_write, args=(single, N, f"t{i}")) for i in range(THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"SingleLock ({THREADS} threads × {N} writes): {time.perf_counter() - start:.3f}s")
```

### 19.4 Lock-Free Alternatives

```python
"""Lock-free counter using threading — approximate techniques."""

import threading
from collections import defaultdict


class PerThreadCounter:
    """Each thread increments its own counter; aggregate on read.
    Write: O(1), no contention.
    Read: O(threads), requires summing.
    """

    def __init__(self) -> None:
        self._local = threading.local()
        self._counters: dict[int, list[int]] = defaultdict(lambda: [0])
        self._lock = threading.Lock()

    def increment(self) -> None:
        tid = threading.current_thread().ident
        if not hasattr(self._local, "counter"):
            self._local.counter = [0]
            with self._lock:
                self._counters[tid] = self._local.counter
        self._local.counter[0] += 1

    @property
    def value(self) -> int:
        with self._lock:
            return sum(c[0] for c in self._counters.values())


counter = PerThreadCounter()


def worker(n: int) -> None:
    for _ in range(n):
        counter.increment()


N = 1_000_000
THREADS = 8

import time
start = time.perf_counter()
threads = [threading.Thread(target=worker, args=(N,)) for _ in range(THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
elapsed = time.perf_counter() - start

print(f"PerThreadCounter: {counter.value} in {elapsed:.3f}s")
# Much faster than a single locked counter under high concurrency.
```

### 19.5 Performance Analysis

```python
"""Compare contention levels."""

import threading
import time


def bench_contention(num_threads: int, iterations: int) -> tuple[float, int]:
    counter = {"value": 0}
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(iterations):
            with lock:
                counter["value"] += 1

    start = time.perf_counter()
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    return elapsed, counter["value"]


print(f"{'Threads':>8} {'Time (s)':>10} {'Ops/sec':>12}")
print("-" * 35)

for num_threads in [1, 2, 4, 8, 16]:
    elapsed, count = bench_contention(num_threads, 100_000)
    ops_per_sec = count / elapsed
    print(f"{num_threads:>8} {elapsed:>10.3f} {ops_per_sec:>12,.0f}")
```

### Common Pitfalls

- Over-synchronizing — locking more data than necessary.
- Using a single global lock for all shared state.
- Not measuring contention before optimizing.
- Premature lock-free optimization — correct lock-free code is very hard to write.

### Interview Tips

- "Lock contention is the primary scalability bottleneck in concurrent programs."
- "I reduce contention with lock splitting (separate locks for separate data) or lock striping (hash-based lock distribution)."
- "Per-thread counters with aggregation is a common lock-free pattern for high-throughput metrics."

---

## 20. Synchronization Strategies

### 20.1 Pessimistic vs Optimistic Locking

**Pessimistic locking**: acquire the lock **before** accessing data, assuming contention.

```python
import threading

data = {"balance": 1000}
lock = threading.Lock()


def pessimistic_transfer(amount: int) -> None:
    with lock:                                  # Lock first, then read/write
        if data["balance"] >= amount:
            data["balance"] -= amount
```

**Optimistic locking**: read without locking, then verify no changes occurred before committing.

```python
import threading


class OptimisticStore:
    """Optimistic concurrency control using version numbers."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[int, any]] = {}    # key → (version, value)
        self._lock = threading.Lock()

    def read(self, key: str) -> tuple[int, any]:
        """Read value and its version — no lock needed."""
        return self._data.get(key, (0, None))

    def write(self, key: str, value: any, expected_version: int) -> bool:
        """Write only if version matches — atomic check-and-set."""
        with self._lock:
            current_version, _ = self._data.get(key, (0, None))
            if current_version != expected_version:
                return False         # Conflict — caller must retry
            self._data[key] = (current_version + 1, value)
            return True

    def read_modify_write(self, key: str, modifier) -> any:
        """Retry loop for optimistic updates."""
        while True:
            version, value = self.read(key)
            new_value = modifier(value)
            if self.write(key, new_value, version):
                return new_value
            # Conflict — retry with new version


store = OptimisticStore()
store.write("counter", 0, 0)


def increment_optimistic() -> None:
    for _ in range(10_000):
        store.read_modify_write("counter", lambda v: v + 1)


threads = [threading.Thread(target=increment_optimistic) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

_, final_value = store.read("counter")
print(f"Optimistic counter: {final_value}")   # 40000
```

### 20.2 Fine-Grained vs Coarse-Grained Locking

```python
import threading


class CoarseGrainedCache:
    """One lock for the entire cache — simple but high contention."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> str | None:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._cache[key] = value

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)


class FineGrainedCache:
    """Per-bucket locks — lower contention, higher complexity."""

    def __init__(self, num_buckets: int = 16) -> None:
        self._num_buckets = num_buckets
        self._buckets: list[dict[str, str]] = [{} for _ in range(num_buckets)]
        self._locks: list[threading.Lock] = [threading.Lock() for _ in range(num_buckets)]

    def _bucket_index(self, key: str) -> int:
        return hash(key) % self._num_buckets

    def get(self, key: str) -> str | None:
        idx = self._bucket_index(key)
        with self._locks[idx]:
            return self._buckets[idx].get(key)

    def set(self, key: str, value: str) -> None:
        idx = self._bucket_index(key)
        with self._locks[idx]:
            self._buckets[idx][key] = value

    def delete(self, key: str) -> None:
        idx = self._bucket_index(key)
        with self._locks[idx]:
            self._buckets[idx].pop(key, None)
```

### 20.3 Lock-Free Programming Concepts

Lock-free algorithms guarantee that **at least one thread** makes progress in a finite number of steps, even if other threads are delayed. They rely on **atomic** compare-and-swap (CAS) operations.

```python
"""Simulating CAS in Python (not truly lock-free due to GIL, but demonstrates the concept)."""

import threading


class AtomicReference:
    """Compare-and-swap reference holder."""

    def __init__(self, initial_value=None) -> None:
        self._value = initial_value
        self._lock = threading.Lock()     # Python doesn't have native CAS

    def get(self):
        return self._value

    def compare_and_swap(self, expected, new_value) -> bool:
        """Atomically set to new_value if current value == expected."""
        with self._lock:
            if self._value is expected or self._value == expected:
                self._value = new_value
                return True
            return False

    def get_and_set(self, new_value):
        with self._lock:
            old = self._value
            self._value = new_value
            return old


class CASCounter:
    """Lock-free counter using compare-and-swap."""

    def __init__(self) -> None:
        self._value = AtomicReference(0)

    def increment(self) -> int:
        while True:
            current = self._value.get()
            if self._value.compare_and_swap(current, current + 1):
                return current + 1

    def get(self) -> int:
        return self._value.get()


counter = CASCounter()


def worker(n: int) -> None:
    for _ in range(n):
        counter.increment()


threads = [threading.Thread(target=worker, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"CAS Counter: {counter.get()}")   # 400000
```

### 20.4 Lock-Free Stack (Treiber Stack)

```python
import threading
from typing import Any, Optional


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value: Any, next_node: Optional["Node"] = None) -> None:
        self.value = value
        self.next = next_node


class TreiberStack:
    """Lock-free stack using compare-and-swap."""

    def __init__(self) -> None:
        self._head = AtomicReference(None)

    def push(self, value: Any) -> None:
        while True:
            old_head = self._head.get()
            new_head = Node(value, old_head)
            if self._head.compare_and_swap(old_head, new_head):
                return

    def pop(self) -> Optional[Any]:
        while True:
            old_head = self._head.get()
            if old_head is None:
                return None
            new_head = old_head.next
            if self._head.compare_and_swap(old_head, new_head):
                return old_head.value


stack = TreiberStack()

def pusher(prefix: str, count: int) -> None:
    for i in range(count):
        stack.push(f"{prefix}-{i}")

def popper(results: list, count: int) -> None:
    for _ in range(count):
        val = stack.pop()
        if val is not None:
            results.append(val)


results: list[str] = []

pushers = [threading.Thread(target=pusher, args=(f"P{i}", 1000)) for i in range(4)]
poppers = [threading.Thread(target=popper, args=(results, 1000)) for _ in range(4)]

for t in pushers:
    t.start()
for t in pushers:
    t.join()
for t in poppers:
    t.start()
for t in poppers:
    t.join()

print(f"Pushed 4000, popped {len(results)}")
```

### 20.5 Choosing the Right Strategy

| Criteria | Pessimistic | Optimistic | Lock-Free |
|---|---|---|---|
| **Contention level** | Any | Low to moderate | High |
| **Complexity** | Low | Moderate | High |
| **Performance (low contention)** | Good | Best | Good |
| **Performance (high contention)** | Fair (waiting) | Poor (retries) | Best |
| **Correctness difficulty** | Easy | Moderate | Very hard |
| **Starvation risk** | With unfair locks | With many retries | Low |

### 20.6 Complete Decision Framework

```
                ┌────────────────────────┐
                │  Is shared state       │
                │  needed?               │
                └────────────┬───────────┘
                         yes │        no
                             ▼         ▼
                   ┌───────────┐   Use message passing
                   │ Mutable?  │   (queues) or immutable
                   └─────┬─────┘   data.
                    yes  │   no
                         ▼    ▼
              ┌──────────┐   Immutable — no sync needed.
              │ Contention│
              │ expected? │
              └─────┬─────┘
               low  │  high
                    ▼    ▼
          ┌──────────┐  ┌───────────────────┐
          │Optimistic│  │ Single resource?   │
          │ locking  │  └─────────┬─────────┘
          └──────────┘       yes  │   no
                                  ▼    ▼
                        ┌──────────┐  ┌────────────┐
                        │Fine-grain│  │Lock striping│
                        │  lock    │  │  or per-   │
                        └──────────┘  │thread data │
                                      └────────────┘
```

### 20.7 Practical Guidelines

```python
"""Summary of synchronization strategies with example usage."""

import threading
import queue
from dataclasses import dataclass
from typing import Any


# Strategy 1: Message Passing (preferred for most use cases)
task_queue = queue.Queue()
result_queue = queue.Queue()


# Strategy 2: Immutable Shared State
@dataclass(frozen=True)
class AppConfig:
    db_url: str
    max_connections: int


# Strategy 3: Lock per resource
class UserService:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get_user(self, user_id: str) -> dict | None:
        with self._lock:
            return self._users.get(user_id)


# Strategy 4: Read-Write Lock for read-heavy workloads
# (use the FairReadWriteLock from Section 16)

# Strategy 5: Per-thread state for independent computation
thread_local = threading.local()


# Strategy 6: Atomic-style operations via CAS
# (use the AtomicReference from Section 20.3)


# Decision checklist:
GUIDELINES = """
Synchronization Strategy Checklist:
1. Can I eliminate shared mutable state?
   → Use immutable objects or message passing
2. Is the workload read-heavy?
   → Use a read-write lock
3. Is contention expected to be low?
   → Use optimistic locking (version-based CAS)
4. Is the critical section short?
   → Use a simple Lock
5. Do multiple methods need the same lock?
   → Use RLock
6. Do I need to limit concurrency?
   → Use Semaphore
7. Is this a producer-consumer pattern?
   → Use queue.Queue
8. Do I need to signal between threads?
   → Use Event (simple) or Condition (complex)
"""

print(GUIDELINES)
```

### Common Pitfalls

- Using pessimistic locking everywhere — high contention kills throughput.
- Implementing lock-free algorithms incorrectly — subtle bugs that only appear under load.
- Mixing strategies inconsistently within the same system.
- Not considering the "no shared state" option first.

### Interview Tips

- "I start by asking whether shared mutable state is necessary. If I can use immutable data or message passing, I avoid synchronization entirely."
- "For read-heavy workloads, I use a read-write lock. For write-heavy workloads with low contention, optimistic locking with CAS."
- "Lock-free algorithms give the best throughput under high contention, but they're hard to implement correctly. I only reach for them when profiling shows lock contention is the bottleneck."
- "In practice, `queue.Queue` with a producer-consumer pattern solves most threading coordination problems cleanly and correctly."

---

## Quick Reference: When to Use What

| Problem | Best Tool |
|---|---|
| I/O-bound concurrency | `threading` / `asyncio` |
| CPU-bound parallelism | `multiprocessing` |
| Thread-safe data passing | `queue.Queue` |
| Mutual exclusion | `threading.Lock` |
| Recursive locking | `threading.RLock` |
| Limit concurrent access | `threading.Semaphore` |
| Complex coordination | `threading.Condition` |
| Simple signaling | `threading.Event` |
| Phase synchronization | `threading.Barrier` |
| Pool of thread workers | `ThreadPoolExecutor` |
| Pool of process workers | `ProcessPoolExecutor` |
| Prevent races | Locks, immutability, message passing |
| Prevent deadlocks | Lock ordering, timeouts |
| Reduce contention | Lock splitting, lock striping, per-thread data |
| Read-heavy workloads | Read-write locks |
| High-throughput counters | Per-thread counters with aggregation |

---

## Further Reading

- [Python `threading` documentation](https://docs.python.org/3/library/threading.html)
- [Python `multiprocessing` documentation](https://docs.python.org/3/library/multiprocessing.html)
- [Python `concurrent.futures` documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [PEP 684 — Per-Interpreter GIL](https://peps.python.org/pep-0684/)
- [PEP 703 — Making the GIL Optional](https://peps.python.org/pep-0703/)
- *Java Concurrency in Practice* by Brian Goetz — many concepts transfer directly to Python
- *The Art of Multiprocessor Programming* by Herlihy & Shavit — deep dive into lock-free algorithms

---

*End of Concurrency Fundamentals Guide.*
