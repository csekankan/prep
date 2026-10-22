# Python Backend Engineering — Senior/Staff Level Deep Dive

> A comprehensive mini-book covering CPython internals, concurrency, performance, system design,
> observability, security, and production patterns. Packed with industry examples from Instagram,
> Netflix, Stripe, Uber, Discord, Dropbox, Spotify, and other companies running Python at massive scale.

---

## Table of Contents

1. [CPython Internals](#1-cpython-internals)
2. [Memory Management](#2-memory-management)
3. [Advanced Concurrency](#3-advanced-concurrency)
4. [Free-Threading (PEP 703)](#4-free-threading-pep-703)
5. [Performance Engineering](#5-performance-engineering)
6. [Advanced Type System](#6-advanced-type-system)
7. [Metaclasses & Descriptors](#7-metaclasses--descriptors)
8. [Design Patterns at Scale](#8-design-patterns-at-scale)
9. [FastAPI Production Patterns](#9-fastapi-production-patterns)
10. [SQLAlchemy 2.0 & Database Patterns](#10-sqlalchemy-20--database-patterns)
11. [Event-Driven Architecture](#11-event-driven-architecture)
12. [Distributed Systems Patterns](#12-distributed-systems-patterns)
13. [Observability & Telemetry](#13-observability--telemetry)
14. [Testing at Scale](#14-testing-at-scale)
15. [Security Engineering](#15-security-engineering)
16. [Modern Python Tooling (2025+)](#16-modern-python-tooling-2025)
17. [Deployment & Infrastructure](#17-deployment--infrastructure)
18. [Interview Patterns](#18-interview-patterns)

---

## 1. CPython Internals

### 1.1 How Python Executes Code

#### The Theory

When you run `python script.py`, you're NOT running an interpreter that reads your code line by line like a shell script. Python is actually a **compiled language** — but it compiles to an intermediate representation (bytecode) rather than to machine code.

**Why this matters for interviews:**
- Python's "slowness" is NOT because it's interpreted — it's because bytecode runs on a virtual machine (VM) that processes one instruction at a time, with dynamic type dispatch on every operation.
- Understanding this pipeline explains why tools like Cython (compiles to C) and PyPy (JIT-compiles bytecode to machine code) can give 10-100x speedups.
- The `.pyc` files in `__pycache__/` ARE the compiled bytecode — Python caches them to skip re-compilation on subsequent runs.

**The execution pipeline:**

```
Source (.py)
    │
    ▼ [Lexer: tokenization]
Tokens
    │
    ▼ [Parser: grammar rules]
Abstract Syntax Tree (AST)
    │
    ▼ [Compiler: ast → bytecode]  ← This is the "compilation" step
Code Object (bytecode + metadata)
    │
    ▼ [Saved to __pycache__/script.cpython-312.pyc]
.pyc file
    │
    ▼ [CPython VM: ceval.c — a giant switch statement]
Execution (one bytecode instruction at a time)
```

**Key insight:** Each bytecode instruction is a simple operation (load a value, call a function, add two numbers). The VM's main loop in `ceval.c` is essentially:

```
while (1) {
    opcode = NEXT_INSTRUCTION();
    switch (opcode) {
        case LOAD_FAST: push(local_vars[arg]); break;
        case BINARY_ADD: right = pop(); left = pop(); push(left + right); break;
        case CALL_FUNCTION: ... break;
        // ~170 opcodes total
    }
}
```

#### The Code

```python
import dis
import sys

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# dis.dis() disassembles a function into human-readable bytecode
# This is what CPython ACTUALLY executes — not your source code
dis.dis(fibonacci)
```

Output explained:

```
  LINE    OFFSET  OPCODE              ARG  (HUMAN-READABLE ARG)

  4           0 LOAD_FAST                0 (n)       ← push local var 'n' onto stack
              2 LOAD_CONST               1 (1)       ← push constant 1 onto stack
              4 COMPARE_OP               1 (<=)      ← pop both, compare, push True/False
              6 POP_JUMP_IF_FALSE       12           ← if False, jump to offset 12

  5           8 LOAD_FAST                0 (n)       ← push 'n' (the return value)
             10 RETURN_VALUE                         ← return top of stack to caller

  6     >>   12 LOAD_GLOBAL              0 (fibonacci) ← look up 'fibonacci' in global scope
             14 LOAD_FAST                0 (n)         ← push n
             16 LOAD_CONST               1 (1)         ← push 1
             18 BINARY_SUBTRACT                        ← n - 1
             20 CALL_FUNCTION            1             ← call fibonacci(n-1), push result
             22 LOAD_GLOBAL              0 (fibonacci) ← look up 'fibonacci' again
             24 LOAD_FAST                0 (n)         ← push n
             26 LOAD_CONST               2 (2)         ← push 2
             28 BINARY_SUBTRACT                        ← n - 2
             30 CALL_FUNCTION            1             ← call fibonacci(n-2), push result
             32 BINARY_ADD                             ← add the two results
             34 RETURN_VALUE                           ← return sum to caller
```

**Why this matters:**
- `LOAD_GLOBAL` is expensive — it searches the global dictionary every time. That's why `fibonacci` is looked up TWICE per call. Moving a frequently-called function to a local variable speeds things up.
- `LOAD_FAST` is cheap — it's a direct array index into the local variables (that's why it's called "fast").
- Every single `BINARY_ADD` must dynamically check types (is it int + int? str + str? custom __add__?) — this is the core reason Python is slow per-operation compared to C.

**Industry example — Instagram's bytecode optimization:**
Instagram (Django-based, 2 billion users) runs one of the largest Python deployments. Their team contributed `LOAD_ATTR_ADAPTIVE` and other specializing opcodes to CPython 3.11 that gave them a **10-25% server-wide speedup** just from the bytecode improvements — no application code changes. This saved them thousands of servers. When Meta engineers talk about "Python performance," they mean bytecode-level VM improvements, not rewriting in Go.

### 1.2 Python Object Model

#### The Theory

In Python, **everything is an object** — integers, strings, functions, classes, modules, even `None`. This is not a metaphor. Every single value in Python is a heap-allocated C struct with at minimum two fields: a reference count and a type pointer.

**Why this matters:**
- An integer in C is 4-8 bytes. An integer in Python is 28+ bytes. This 4-7x overhead is the cost of "everything is an object."
- Every time you write `x = 42`, Python allocates a PyObject on the heap, sets its type to `int`, sets its refcount to 1, and stores the value 42 inside.
- This is why Python uses ~10-50x more memory than C for numeric workloads — and why NumPy (which stores raw C arrays) is essential for data science.

**What every Python object contains (at the C level):**

```c
// In CPython source: Include/object.h
// This is the MINIMUM structure for ANY Python object

typedef struct _object {
    Py_ssize_t ob_refcnt;    // 8 bytes: how many variables point to this object
                              // When it hits 0, object is immediately freed
    PyTypeObject *ob_type;    // 8 bytes: pointer to the type (int, str, list, etc.)
                              // This is how Python knows what methods an object has
} PyObject;
// Minimum: 16 bytes overhead for EVERY object (before any actual data)

typedef struct {
    PyObject ob_base;         // 16 bytes: refcount + type
    Py_ssize_t ob_size;       // 8 bytes: number of items (for lists, tuples, etc.)
} PyVarObject;
// Variable-size objects (str, list, tuple) need at least 24 bytes overhead
```

**The memory cost of "everything is an object":**

```python
import sys

# Compare Python object sizes to raw data sizes:
# A C int is 4 bytes. A Python int:
sys.getsizeof(0)        # 28 bytes (16 overhead + 4 value + padding)
sys.getsizeof(1)        # 28 bytes
sys.getsizeof(2**30)    # 32 bytes (large int needs more storage)

# A C char* "" is 1 byte. A Python str:
sys.getsizeof("")       # 49 bytes (object header + hash + length + kind + ...)
sys.getsizeof("hello")  # 54 bytes (49 + 5 chars)

# An empty C array is 0 bytes. A Python list:
sys.getsizeof([])       # 56 bytes (object header + pointer array preallocated)
sys.getsizeof({})       # 64 bytes (object header + hash table structure)
```

**Integer interning — a CPython optimization:**

```python
# CPython pre-allocates integers from -5 to 256 at startup.
# Every time you use 42, you get the SAME object (saves memory + allocation time).
a = 256
b = 256
assert a is b  # True — both point to the SAME pre-allocated int object

a = 257
b = 257
assert a is not b  # True — outside the cache, so two separate objects are created
# NOTE: 'is' checks identity (same memory address), '==' checks value equality

# This is a CPython implementation detail — NOT a language guarantee!
# Don't rely on it in production code. Always use == for value comparison.
```

**Interview gotcha: `id()`, `is`, and `==`**

```python
# id(x) returns the memory address of the object
# a is b  ←→  id(a) == id(b)  (same object in memory)
# a == b  ←→  a.__eq__(b)     (same value, possibly different objects)

a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)   # True  (same value)
print(a is b)   # False (different objects in memory)

c = a
print(a is c)   # True  (c points to the same list object as a)
c.append(4)
print(a)        # [1, 2, 3, 4] — same object, so a is also modified!
```

### 1.3 The Global Interpreter Lock (GIL)

#### The Theory

The GIL is the most misunderstood and most-asked topic in senior Python interviews. Here's the complete picture:

**What it is:** The GIL is a single mutex (lock) inside the CPython interpreter. Only the thread holding the GIL can execute Python bytecode. Other threads are blocked — they exist but can't run Python code.

**The fundamental problem it solves:** Python uses reference counting for memory management (`ob_refcnt` in every PyObject). Consider:

```
Thread A: x = some_object   →  ob_refcnt becomes 2 (one from thread A's assignment)
Thread B: del x             →  ob_refcnt becomes 1
                               But wait — what if Thread A and B modify refcnt simultaneously?
                               Without locking: refcnt could become 0 incorrectly → object freed
                               → Thread A accesses freed memory → SEGFAULT
```

The GIL prevents this by ensuring only one thread touches Python objects at a time.

**Why not use per-object locks instead?**
- Every `ob_refcnt += 1` would need a lock. That's millions of lock acquisitions per second.
- Measured performance: per-object locking makes single-threaded code **2x slower** due to lock overhead.
- The GIL makes single-threaded code FAST (no locking cost) at the expense of true parallelism.

**The critical insight for interviews:**

```
Threads in Python ARE real OS threads.
They DO run in parallel on different CPU cores.
But the GIL means only ONE can execute Python bytecode at any time.

HOWEVER: Threads release the GIL during I/O operations.
So threads ARE useful for I/O-bound work (network, disk, sleep).
They are NOT useful for CPU-bound work (number crunching).

For CPU parallelism: use multiprocessing (separate processes, separate GILs).
```

#### The Code

```python
import threading
import time

counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        counter += 1
        # counter += 1 is NOT atomic! It compiles to FOUR bytecode instructions:
        #   LOAD_GLOBAL    counter   ← read current value
        #   LOAD_CONST     1         ← load 1
        #   BINARY_ADD               ← compute counter + 1
        #   STORE_GLOBAL   counter   ← write back
        # The GIL can release BETWEEN any of these instructions!
        # Thread A reads counter=100, Thread B reads counter=100,
        # Both compute 101, both write 101. One increment is LOST.

threads = [threading.Thread(target=increment) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Expected: 4_000_000. Actual: some value < 4_000_000
# This proves: the GIL does NOT make your code thread-safe!
# The GIL prevents CRASHES (no segfaults) but NOT race conditions.
print(f"Counter: {counter}")
```

**Why the GIL exists (trade-off summary):**

| | With GIL | Without GIL (per-object locks) |
|---|---|---|
| Single-thread performance | Fast (no lock overhead) | ~2x slower |
| C extension development | Simple (no thread worries) | Complex (must handle concurrency) |
| Multi-thread CPU work | Serialized (useless) | True parallelism |
| Multi-thread I/O work | Works great (GIL releases) | Works great |
| Memory safety | Guaranteed | Must be manually ensured |

**When the GIL releases (crucial for understanding when threads help):**

```python
import sys

# The GIL releases automatically in these situations:
#
# 1. I/O operations: file read/write, network send/recv, time.sleep()
#    → This is why threads work great for web scraping, API calls, DB queries
#
# 2. Every N bytecode instructions (configurable):
print(sys.getswitchinterval())  # 0.005 seconds (5ms)
#    → Every 5ms, the running thread drops the GIL so others get a chance
#    → This prevents one thread from starving others indefinitely
#
# 3. C extensions that explicitly release it:
#    → numpy, hashlib, zlib, PIL all release the GIL during heavy computation
#    → This is why numpy can use multiple cores despite the GIL
#    → Pattern: Py_BEGIN_ALLOW_THREADS ... C code ... Py_END_ALLOW_THREADS
```

**When to use threads vs processes vs asyncio:**

```
┌──────────────────────────────────────────────────────────────┐
│ I/O-bound (network, disk, API calls):                        │
│   → asyncio (best: low overhead, thousands of connections)   │
│   → threads (good: simpler code, limited by OS thread count) │
│                                                              │
│ CPU-bound (computation, data processing):                    │
│   → multiprocessing (separate process = separate GIL)        │
│   → C extension with GIL release (numpy, Cython)            │
│   → Free-threading Python 3.13+ (experimental, no GIL)      │
│                                                              │
│ NEVER: threads for CPU-bound Python code                     │
│   → Threads share the GIL, so CPU work is actually SLOWER   │
│     than single-threaded (due to GIL contention overhead)    │
└──────────────────────────────────────────────────────────────┘
```

**Industry war stories about the GIL:**

- **Instagram (Meta):** Runs the entire app on a SINGLE process with asyncio. They DON'T fight the GIL — they work WITH it. Their Django app handles millions of requests using async I/O. CPU-heavy work (ML models, image processing) runs in separate C/Rust services.

- **Dropbox:** Their sync client used threads for file monitoring. Hit GIL issues when computing file hashes (CPU-bound). Solution: moved hashing to a C extension that releases the GIL. 4x speedup on multi-core machines.

- **YouTube (early days):** Google's original YouTube backend was Python. GIL wasn't the bottleneck because video serving is I/O-bound. They hit CPU limits at Google-scale → rewrote hot paths in C++, kept Python as the orchestration layer.

- **Discord:** Initially Flask + threads. Hit GIL limits with CPU-bound message processing. Migrated hot paths to Rust extensions. Python stayed as the "glue" for business logic. Their blog post: "We wrote a Rust library that makes our Python 10x faster."

- **Celery (industry standard):** Solves the GIL problem via multiprocessing. Each worker is a separate process with its own GIL. This is how most Python apps handle CPU-bound work in production — NOT by fighting the GIL, but by using multiple processes.

### 1.4 Bytecode Optimization

```python
import dis

# Constant folding — computed at compile time
def folded():
    return 24 * 60 * 60  # Stored as 86400 in bytecode

dis.dis(folded)
# LOAD_CONST 86400 — computed at compile time

# Peephole optimization
def peephole():
    x = 1 + 2  # Folded to 3
    if True:   # Dead branch eliminated in some cases
        return x

# LOAD_CONST is used for membership testing optimization
def membership():
    # list → compiled as frozenset for O(1) lookup
    return x in [1, 2, 3, 4, 5]  # Becomes frozenset at bytecode level
```

### 1.5 Code Objects and Frames

```python
def outer():
    x = 10
    def inner():
        return x + 1
    return inner

# Inspect code object
code = outer.__code__
print(code.co_consts)      # (None, 10, <code object inner>)
print(code.co_varnames)    # ('x', 'inner')
print(code.co_cellvars)    # ('x',) — closed over by inner
print(code.co_freevars)    # () — outer doesn't close over anything

inner_code = code.co_consts[2]
print(inner_code.co_freevars)  # ('x',) — references outer's x

# Frame inspection at runtime
import inspect

def show_frame():
    frame = inspect.currentframe()
    print(f"Function: {frame.f_code.co_name}")
    print(f"Line: {frame.f_lineno}")
    print(f"Locals: {frame.f_locals}")
    print(f"Caller: {frame.f_back.f_code.co_name}")

show_frame()
```

---

## 2. Memory Management

#### The Theory — How Python Manages Memory

Python uses a **dual strategy** for memory management that's unique among major languages:

**Strategy 1: Reference Counting (immediate, deterministic)**
- Every object has a counter (`ob_refcnt`) tracking how many references point to it.
- When a new variable points to the object: refcount increases.
- When a variable is deleted or goes out of scope: refcount decreases.
- When refcount hits 0: object is **immediately freed** (no waiting for GC).
- This is DETERMINISTIC — you know exactly when memory is freed.
- Compare to Java/Go: their garbage collectors run at unpredictable times.

**Strategy 2: Cyclic Garbage Collector (periodic, for cycles)**
- Reference counting has one fatal flaw: it can't handle cycles (A → B → A).
- Both A and B have refcount 1 (from each other), so neither ever reaches 0.
- Python's cyclic GC runs periodically to detect and collect these cycles.
- It uses a **generational** approach: objects that survive longer are checked less often.

**Why this matters for production:**
- File handles, DB connections, and locks are freed deterministically via refcounting (when the last reference dies). This is why `with` statements (context managers) work reliably.
- Memory leaks in Python are almost always caused by unintentional references (globals, caches, closures capturing large objects) that keep refcounts above 0.
- If you disable the cyclic GC (`gc.disable()`), refcounting still works — you only leak cyclic garbage.

**The memory layout:**

```
Python Process Memory:
┌─────────────────────────────────────────────┐
│  OS gives Python a heap                     │
│  ┌───────────────────────────────────────┐  │
│  │ pymalloc (objects ≤ 512 bytes)        │  │
│  │  Arena (256KB) → Pool (4KB) → Block   │  │
│  │  Handles: ints, strs, small lists     │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ malloc (objects > 512 bytes)          │  │
│  │  Large lists, numpy arrays, etc.      │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ Free lists (recycled objects)         │  │
│  │  Recently freed ints, floats, tuples  │  │
│  │  Reused without calling malloc again  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Industry examples — Memory at scale:**

- **Instagram:** Their Django app was using 60GB+ RAM per server. Investigation revealed Django's ORM was caching querysets (unintentional references). Fix: explicit `.iterator()` on large querysets + disabling the cyclic GC during request handling (shaved 10% memory). They found that GC pauses were causing latency spikes — disabling GC and relying solely on refcounting eliminated those spikes.

- **Dropbox:** Leaked memory in their Python sync daemon. Root cause: closures in event handlers captured references to large file buffers. The buffers were never freed because the closure kept them alive. Fix: use `weakref` for callbacks.

- **Reddit:** Their Python services would grow to 4GB then OOM. Root cause: `lru_cache` without `maxsize` on a function called with unbounded inputs. Fix: always set `maxsize` on caches, or use TTL-based caches.

- **Pinterest:** Reduced memory usage by 40% by switching hot data classes from regular `__dict__` to `__slots__`. With millions of Pin objects in memory, removing per-instance `__dict__` (which is ~200 bytes overhead) saved gigabytes.

### 2.1 Reference Counting

```python
import sys
import ctypes

# sys.getrefcount(x) returns the reference count of object x.
# NOTE: it always shows +1 because passing x to the function creates a temporary reference.
a = []
print(sys.getrefcount(a))  # 2 (one from 'a', one from getrefcount's parameter)

b = a
print(sys.getrefcount(a))  # 3

del b
print(sys.getrefcount(a))  # 2

# When refcount hits 0, object is immediately deallocated
# This is deterministic — unlike garbage collection in Java/Go
```

### 2.2 Cyclic Garbage Collector

#### The Theory

Reference counting has one weakness: **circular references**. If A references B, and B references A, both have refcount ≥ 1 forever — even if no external code can reach them. They become unreachable garbage that refcounting can never free.

**The generational hypothesis:** Most objects die young. An object that survives many GC passes is likely long-lived (e.g., a module-level cache). Checking long-lived objects repeatedly is wasteful.

Python's cyclic GC uses three **generations**:
- **Gen 0 (young):** Newly created objects. Collected most frequently.
- **Gen 1 (middle):** Survived at least one Gen 0 collection.
- **Gen 2 (old):** Survived at least one Gen 1 collection. Collected rarely.

**How cycle detection works (simplified):**
1. GC traverses all container objects (lists, dicts, instances — not ints/strings which can't form cycles).
2. For each object, it temporarily decrements the refcount of everything it references.
3. After traversal, objects with refcount 0 are unreachable (only reachable from the cycle itself).
4. Those objects are freed.

```python
import gc

# Create a reference cycle: A → B → A
class Node:
    def __init__(self):
        self.ref = None

a = Node()
b = Node()
a.ref = b    # a.ref points to b → b's refcount = 2
b.ref = a    # b.ref points to a → a's refcount = 2

# Delete the external references
del a, b
# Now: a's refcount = 1 (only from b.ref)
#      b's refcount = 1 (only from a.ref)
# Neither will EVER reach 0 via refcounting alone!
# The cyclic GC must detect this cycle and free both.

# GC generations — thresholds control how often each generation is collected
print(gc.get_threshold())  # (700, 10, 10) means:
# Gen 0: collected after 700 new allocations (very frequent)
# Gen 1: collected every 10 Gen-0 collections (moderate)
# Gen 2: collected every 10 Gen-1 collections (rare — roughly every 70,000 allocations)

# In production: you might tune these for latency-sensitive apps
gc.set_threshold(1000, 15, 15)  # less frequent collection = fewer GC pauses

# Manual GC control (useful in latency-critical paths)
gc.disable()    # Disable cyclic GC (refcounting STILL works for non-cyclic objects)
# ... do latency-sensitive work ...
gc.collect()    # Force a full collection when you're ready for the pause
gc.enable()

# Debugging memory leaks — find uncollectable objects
gc.set_debug(gc.DEBUG_LEAK)
gc.collect()
print(gc.garbage)  # Objects with __del__ that form cycles can't be safely collected
# Python can't determine safe destruction order: if A.__del__ needs B, and B.__del__ needs A,
# which runs first? Python gives up and puts them in gc.garbage for you to inspect.
```

**Production tip:** In web servers handling many requests, cyclic GC pauses can cause latency spikes. Some teams disable GC during request handling and run it between requests:

```python
gc.disable()
handle_request()  # no GC pause during this
gc.collect()      # collect between requests
```

### 2.3 Memory Allocator Architecture

```
+--------------------------------------------------+
|  Layer 3: Object-specific allocators             |
|  (int, float, list, dict free-lists)             |
+--------------------------------------------------+
|  Layer 2: Python object allocator (pymalloc)     |
|  - Arena (256 KB) → Pool (4 KB) → Block          |
|  - Handles allocations ≤ 512 bytes               |
+--------------------------------------------------+
|  Layer 1: Python memory allocator                |
|  - Wraps C malloc with bookkeeping               |
+--------------------------------------------------+
|  Layer 0: C standard allocator (malloc/free)     |
+--------------------------------------------------+
```

```python
# Pymalloc pools — objects ≤ 512 bytes use Python's own allocator
# Objects > 512 bytes go directly to malloc

# Free lists — recently deallocated objects are cached for reuse
# This is why creating/destroying many small objects is fast

import tracemalloc

tracemalloc.start()

# Your code here
data = [dict(key=i, value=str(i)) for i in range(10000)]

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:5]:
    print(stat)
```

### 2.4 Weak References

```python
import weakref

class ExpensiveObject:
    def __init__(self, data):
        self.data = data

# Strong reference keeps object alive
obj = ExpensiveObject("important data")

# Weak reference doesn't prevent GC
weak = weakref.ref(obj)
print(weak())  # <ExpensiveObject object>

del obj
print(weak())  # None — object was collected

# WeakValueDictionary — cache that doesn't prevent GC
cache = weakref.WeakValueDictionary()

def get_resource(key):
    if key in cache:
        return cache[key]
    resource = ExpensiveObject(f"data for {key}")
    cache[key] = resource
    return resource
```

### 2.5 `__slots__` for Memory Optimization

```python
import sys

class RegularPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SlottedPoint:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

regular = RegularPoint(1, 2)
slotted = SlottedPoint(1, 2)

print(sys.getsizeof(regular))   # 48 bytes (has __dict__)
print(sys.getsizeof(regular.__dict__))  # 104 bytes
# Total: ~152 bytes

print(sys.getsizeof(slotted))   # 48 bytes (no __dict__)
# Total: 48 bytes — 3x less memory

# With 1 million objects:
# Regular: ~152 MB
# Slotted: ~48 MB
```

---

## 3. Advanced Concurrency

#### The Theory — Why asyncio Exists and How It Works

**Industry context:** Discord handles 10+ million concurrent WebSocket connections per cluster. Spotify streams to 500M+ users. Both use async Python (or migrated hot paths FROM Python async to Rust/Go). Understanding asyncio deeply = understanding how modern internet services work.

**The problem:** You have a web server handling 10,000 simultaneous connections. Each connection spends 95% of its time WAITING (for database responses, API calls, disk I/O). Only 5% is actual computation.

**Solutions (from worst to best):**

| Approach | Memory per connection | Max connections | Context switch cost |
|---|---|---|---|
| 1 process per connection (Apache) | ~10 MB | ~1,000 | Very high (OS) |
| 1 thread per connection | ~1 MB | ~10,000 | High (OS kernel) |
| asyncio (event loop) | ~1 KB | ~100,000+ | Nearly zero (userspace) |

**How asyncio works conceptually:**

```
Traditional threading (preemptive):
  OS decides when to switch threads. You have NO control.
  Thread A running → [OS interrupts] → Thread B running → [OS interrupts] → ...

asyncio (cooperative):
  YOUR CODE decides when to yield. The event loop manages who runs next.
  Task A runs → [hits 'await'] → yields to loop → Task B runs → [hits 'await'] → yields → ...
  
  The event loop is essentially:
  while True:
      ready_tasks = check_which_IO_operations_completed()
      for task in ready_tasks:
          run_task_until_next_await(task)
```

**Key mental model:**
- `async def` defines a coroutine (a function that can be suspended and resumed).
- `await` is a suspension point — "I need to wait for this; let someone else run."
- The event loop is a scheduler — it decides which coroutine runs next (whichever is no longer waiting).
- **NOTHING runs in parallel** — it's all on ONE thread. Concurrency ≠ parallelism.
- This works because I/O waiting doesn't need CPU. While one task waits for a DB response, another can process the previous DB response.

**The critical rule:** Never block the event loop. If you do `time.sleep(5)` instead of `await asyncio.sleep(5)`, ALL 10,000 connections are frozen for 5 seconds because the single thread is blocked.

**Industry examples of asyncio in production:**

- **Discord:** Originally Flask (sync). Migrated to async Python for WebSocket handling. Each server process handles ~200K concurrent connections using asyncio. Hot path (message fanout) later moved to Rust, but orchestration stays in Python.

- **Netflix:** Uses async Python for their chaos engineering tools and internal APIs. Their Dispatch incident management platform (open-source) is FastAPI + asyncio.

- **Robinhood:** Trading platform built on async Python. Real-time price feeds use asyncio WebSockets. When they accidentally used a sync HTTP library inside an async endpoint, it caused a 3-hour outage during peak trading.

- **Cloudflare Workers analytics:** Uses Python asyncio to aggregate billions of events per day. Key lesson: they discovered that a single `requests.get()` (sync library) inside an async handler blocked 50K other connections.

**The "never block the event loop" incident pattern (common in production):**
```
Symptom: P99 latency spikes from 50ms to 30 seconds every few minutes.
Root cause: Some library deep in the call stack does synchronous DNS resolution.
Fix: Replace `socket.getaddrinfo()` with `asyncio.getaddrinfo()` or use `aiodns`.
Lesson: ONE blocking call anywhere in your async code ruins ALL connections.
```

### 3.1 asyncio Deep Dive

```python
import asyncio
from typing import AsyncIterator

async def fetch_data(url: str, delay: float) -> dict:
    """Simulate an I/O-bound operation (like a DB query or API call).
    
    When 'await asyncio.sleep(delay)' executes:
    1. This coroutine suspends itself
    2. Control returns to the event loop
    3. The event loop runs OTHER tasks that are ready
    4. After 'delay' seconds, the event loop resumes THIS coroutine
    """
    await asyncio.sleep(delay)  # Yields control — this is the "cooperative" part
    return {"url": url, "status": 200}

async def main():
    # create_task() SCHEDULES the coroutine to run (doesn't run it yet).
    # All three tasks are registered with the event loop.
    tasks = [
        asyncio.create_task(fetch_data("https://api.example.com/1", 1.0)),  # will take 1.0s
        asyncio.create_task(fetch_data("https://api.example.com/2", 0.5)),  # will take 0.5s
        asyncio.create_task(fetch_data("https://api.example.com/3", 1.5)),  # will take 1.5s
    ]
    
    # gather() runs all tasks concurrently and waits for ALL to complete.
    # Total time ≈ max(1.0, 0.5, 1.5) = 1.5s — NOT 1.0 + 0.5 + 1.5 = 3.0s
    # Because while task 3 is sleeping for 1.5s, tasks 1 and 2 also sleep simultaneously.
    results = await asyncio.gather(*tasks)
    return results

# asyncio.run() creates an event loop, runs main() until complete, then closes the loop.
asyncio.run(main())
```

**Visual timeline of what happens:**

```
Time:  0.0s    0.5s    1.0s    1.5s
       ─────┬──────┬──────┬──────┬
Task 1:  [sleeping...........] done (1.0s)
Task 2:  [sleeping...] done (0.5s)
Task 3:  [sleeping..................] done (1.5s)

All three sleep simultaneously because sleeping doesn't use CPU.
Event loop just registers "wake task X at time Y" and moves on.
Total wall-clock time: 1.5s (the longest single task).
```

### 3.2 Task Groups (Python 3.11+)

```python
import asyncio

async def process_batch(items: list[str]) -> list[dict]:
    """Structured concurrency with TaskGroup."""
    results = []
    
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(fetch_and_process(item))
            for item in items
        ]
    
    # All tasks completed (or one raised — cancels all others)
    return [t.result() for t in tasks]

async def fetch_and_process(item: str) -> dict:
    await asyncio.sleep(0.1)
    return {"item": item, "processed": True}

# Exception handling with TaskGroup
async def robust_batch():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(might_fail("a"))
            tg.create_task(might_fail("b"))
    except* ValueError as eg:
        # ExceptionGroup handling (Python 3.11+)
        for exc in eg.exceptions:
            print(f"Caught: {exc}")
    except* TypeError as eg:
        for exc in eg.exceptions:
            print(f"Type error: {exc}")
```

### 3.3 Semaphores and Rate Limiting

```python
import asyncio
from contextlib import asynccontextmanager

class RateLimiter:
    """Token bucket rate limiter for async operations."""
    
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self._tokens = burst
        self._semaphore = asyncio.Semaphore(burst)
        self._refill_task: asyncio.Task | None = None
    
    async def start(self):
        self._refill_task = asyncio.create_task(self._refill())
    
    async def _refill(self):
        while True:
            await asyncio.sleep(1.0 / self.rate)
            if self._tokens < self.burst:
                self._tokens += 1
                self._semaphore.release()
    
    @asynccontextmanager
    async def acquire(self):
        await self._semaphore.acquire()
        self._tokens -= 1
        try:
            yield
        finally:
            pass  # Token is consumed, not returned
    
    async def stop(self):
        if self._refill_task:
            self._refill_task.cancel()

# Usage
async def call_api_with_limit():
    limiter = RateLimiter(rate=10, burst=20)  # 10 req/sec, burst 20
    await limiter.start()
    
    async def make_request(i: int):
        async with limiter.acquire():
            await asyncio.sleep(0.1)  # Simulate API call
            return f"Response {i}"
    
    results = await asyncio.gather(*[make_request(i) for i in range(100)])
    await limiter.stop()
    return results
```

### 3.4 Async Generators and Streams

```python
import asyncio
from typing import AsyncIterator

async def paginated_fetch(url: str, page_size: int = 100) -> AsyncIterator[dict]:
    """Async generator for paginated API responses."""
    page = 1
    while True:
        response = await fetch_page(url, page, page_size)
        if not response["items"]:
            break
        for item in response["items"]:
            yield item
        page += 1

async def fetch_page(url: str, page: int, size: int) -> dict:
    await asyncio.sleep(0.05)
    if page > 5:
        return {"items": []}
    return {"items": [{"id": i + (page-1)*size} for i in range(size)]}

# Consuming async generators
async def process_all():
    async for item in paginated_fetch("https://api.example.com/items"):
        await process_item(item)

# Async comprehension
async def get_ids():
    return [
        item["id"]
        async for item in paginated_fetch("https://api.example.com/items")
        if item["id"] % 2 == 0
    ]
```

### 3.5 Channels Pattern (asyncio.Queue)

```python
import asyncio
from dataclasses import dataclass
from typing import Any

@dataclass
class Message:
    topic: str
    payload: Any

class AsyncChannel:
    """Multi-producer, multi-consumer async channel."""
    
    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.Queue[Message | None] = asyncio.Queue(maxsize=maxsize)
        self._closed = False
    
    async def send(self, message: Message):
        if self._closed:
            raise RuntimeError("Channel is closed")
        await self._queue.put(message)
    
    async def receive(self) -> Message | None:
        msg = await self._queue.get()
        self._queue.task_done()
        return msg
    
    async def close(self):
        self._closed = True
        await self._queue.put(None)  # Sentinel
    
    def __aiter__(self):
        return self
    
    async def __anext__(self) -> Message:
        msg = await self.receive()
        if msg is None:
            raise StopAsyncIteration
        return msg

# Fan-out pattern
async def producer(channel: AsyncChannel, n: int):
    for i in range(n):
        await channel.send(Message(topic="work", payload=i))
        await asyncio.sleep(0.01)
    await channel.close()

async def consumer(channel: AsyncChannel, name: str):
    async for msg in channel:
        print(f"[{name}] Processing: {msg.payload}")
        await asyncio.sleep(0.05)

async def fan_out():
    channel = AsyncChannel(maxsize=10)
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(channel, 50))
        tg.create_task(consumer(channel, "worker-1"))
        tg.create_task(consumer(channel, "worker-2"))
        tg.create_task(consumer(channel, "worker-3"))
```

### 3.6 Async Lock vs Local Lock (threading.Lock vs asyncio.Lock)

#### The Theory — When and Why You Need Locks in Async Code

**The fundamental question:** If asyncio is single-threaded, why do you need locks at all?

**Answer:** Because `await` creates a gap. Between two awaits, another task CAN run and modify shared state.

```
WITHOUT lock (race condition even in single-threaded asyncio):

balance = 100

Task A:                          Task B:
  bal = await get_balance()  →  (bal = 100)
  [await suspends here]         
                                  bal = await get_balance()  → (bal = 100)
                                  new_bal = 100 - 80 = 20
                                  await set_balance(20)      ← writes 20
  new_bal = 100 - 70 = 30
  await set_balance(30)          ← writes 30 (OVERWRITES the 20!)

Result: Both withdrew ($80 + $70 = $150) from $100 account. Bug!

The race happens because 'await get_balance()' suspends, letting Task B read
the SAME old value before Task A writes its update.

─────────────────────────────────────────────────────────────────────
WITH asyncio.Lock — HOW IT FIXES THE RACE:

lock = asyncio.Lock()
balance = 100

Task A:                              Task B:
  await lock.acquire()  ← GOT IT
  bal = await get_balance()  (100)
  [await suspends here]              
                                      await lock.acquire()  ← BLOCKED!
                                      (Lock is held by A, so B SUSPENDS here.
                                       B does NOT proceed. Event loop runs
                                       other tasks, but B is STUCK waiting.)
  new_bal = 100 - 70 = 30
  await set_balance(30)
  lock.release()         ← FREED
                                      ← B RESUMES NOW (lock is free)
                                      bal = await get_balance()  → (30, NOT 100!)
                                      new_bal = 30 - 80 = -50
                                      -50 < 0 → DENIED! ✓ Correct behavior!

Key insight: The lock ensures the ENTIRE sequence (read → compute → write)
runs WITHOUT any other coroutine touching the same data in between.

Task B cannot even READ the balance until Task A is completely done.
That's why there's no stale read — B always sees A's FINAL written value.
─────────────────────────────────────────────────────────────────────
```

**The 3 types of locks in Python:**

| Lock Type | `threading.Lock` | `asyncio.Lock` | Distributed Lock (Redis) |
|---|---|---|---|
| **Scope** | Single process, multiple threads | Single process, single thread (multiple coroutines) | Multiple processes, multiple machines |
| **Blocks** | The calling OS thread (truly sleeps) | Only the awaiting coroutine (event loop keeps running) | The calling coroutine/thread |
| **Use when** | Multithreaded code, GIL not enough | Async code with shared mutable state | Microservices, horizontal scaling |
| **Performance** | OS context switch overhead | Near-zero overhead (just queue manipulation) | Network round-trip (1-5ms) |
| **Deadlock risk** | High (OS threads can truly deadlock) | Lower (cooperative, easier to reason about) | Medium (TTL prevents permanent deadlock) |

**Critical difference — what "blocking" means:**

```python
import threading
import asyncio

# threading.Lock — BLOCKS THE ENTIRE THREAD
lock = threading.Lock()
lock.acquire()       # If another thread holds it, THIS thread freezes
                     # No other code on this thread can run.
                     # In asyncio: THIS FREEZES THE ENTIRE EVENT LOOP!
lock.release()

# asyncio.Lock — SUSPENDS ONLY THIS COROUTINE
lock = asyncio.Lock()
await lock.acquire() # If another coroutine holds it, only THIS coroutine waits.
                     # The event loop continues running OTHER coroutines normally.
                     # Other requests are still served!
lock.release()
```

**Visual comparison:**

```
threading.Lock (BAD in async code):
  Event Loop Thread: [Task A acquires lock] → [FROZEN — waiting for lock] → nothing else runs
  All 10,000 connections: STUCK. Server appears dead.

asyncio.Lock (CORRECT in async code):
  Event Loop Thread: [Task A acquires lock] → [Task B awaits lock, suspended] → 
                     [Task C runs normally] → [Task D runs normally] → [Task A releases] →
                     [Task B resumes with lock]
  Other connections: still being served normally ✓
```

#### Do You Need This in FastAPI? (Industry Reality)

**Short answer:** Rarely. Most FastAPI endpoints are stateless.

**When you DON'T need asyncio.Lock (99% of FastAPI code):**
```python
@app.post("/users/")
async def create_user(user: UserCreate):
    # Each request gets its own local variables.
    # No shared mutable state between requests.
    # Database handles concurrency with its own transactions.
    result = await db.execute(insert(User).values(**user.dict()))
    return {"id": result.inserted_primary_key[0]}
# No lock needed — the database is the source of truth.
```

**When you DO need asyncio.Lock (rare but real cases):**

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

# CASE 1: In-memory cache that's expensive to rebuild
# Problem: If 100 requests hit an expired cache simultaneously,
# all 100 will try to rebuild it (thundering herd).
class CacheWithLock:
    def __init__(self):
        self._cache: dict[str, str] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
    
    async def get_or_compute(self, key: str, compute_fn) -> str:
        if key in self._cache:
            return self._cache[key]
        
        # Get/create a per-key lock (prevents thundering herd)
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            lock = self._locks[key]
        
        async with lock:
            # Double-check after acquiring lock (another task might have computed it)
            if key in self._cache:
                return self._cache[key]
            
            # Only ONE coroutine computes; others wait for the lock then get cached result
            result = await compute_fn(key)
            self._cache[key] = result
            return result

cache = CacheWithLock()

@app.get("/expensive/{item_id}")
async def get_expensive_data(item_id: str):
    return await cache.get_or_compute(
        item_id,
        compute_fn=expensive_llm_call,  # Only called once even if 100 requests hit simultaneously
    )


# CASE 2: Rate limiter with in-memory token bucket
# Problem: Multiple coroutines checking/decrementing tokens is a race condition.
class InMemoryRateLimiter:
    def __init__(self, max_tokens: int, refill_rate: float):
        self._tokens = float(max_tokens)
        self._max = max_tokens
        self._rate = refill_rate
        self._lock = asyncio.Lock()
        self._last_refill = asyncio.get_event_loop().time()
    
    async def acquire(self) -> bool:
        async with self._lock:  # Protects _tokens from concurrent modification
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_refill
            self._tokens = min(self._max, self._tokens + elapsed * self._rate)
            self._last_refill = now
            
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False


# CASE 3: Singleton initialization (lazy loading)
# Problem: Two requests arrive, both see model is None, both load it (expensive!)
class ModelRegistry:
    def __init__(self):
        self._models: dict[str, object] = {}
        self._lock = asyncio.Lock()
    
    async def get_model(self, name: str):
        if name in self._models:
            return self._models[name]
        
        async with self._lock:
            if name in self._models:  # Double-check pattern
                return self._models[name]
            
            # Heavy async initialization — only one coroutine does this
            model = await load_model_from_s3(name)  # Takes 5-10 seconds
            self._models[name] = model
            return model
```

#### When Industry Uses What:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LOCK DECISION TREE FOR FastAPI                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Q: Is the shared state in a DATABASE (PostgreSQL, Redis)?           │
│  YES → Use database transactions / Redis atomic ops. NO Python lock. │
│        (This is 95% of cases in FastAPI)                             │
│                                                                      │
│  Q: Is it IN-MEMORY shared state (cache, counter, singleton)?        │
│  YES → Use asyncio.Lock                                              │
│        (Thundering herd prevention, lazy init, rate limiters)        │
│                                                                      │
│  Q: Are you running multiple PROCESSES (uvicorn --workers 4)?        │
│  YES → asyncio.Lock only protects within ONE process.               │
│        Use Redis/distributed lock for cross-process coordination.    │
│                                                                      │
│  Q: Are you running multiple SERVERS (Kubernetes, ECS)?              │
│  YES → Only distributed locks (Redis/etcd) work.                    │
│        asyncio.Lock is useless here — different machines.            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Industry reality:**
- **Stripe/Shopify:** Use database-level locking (SELECT FOR UPDATE) for financial ops. Distributed locks (Redis) for cross-service coordination.
- **FastAPI apps at scale:** 99% of the time, the database handles concurrency. You almost never need `asyncio.Lock`.
- **When you DO see asyncio.Lock:** Connection pool management, lazy singleton initialization, in-memory caches with thundering herd prevention, token bucket rate limiters.
- **Anti-pattern:** Don't use `threading.Lock` in async code. It freezes the event loop.

```python
# ❌ NEVER DO THIS IN FASTAPI
import threading
lock = threading.Lock()

@app.get("/data")
async def get_data():
    with lock:  # BLOCKS THE ENTIRE EVENT LOOP — all other requests freeze!
        data = await fetch_from_db()
    return data

# ✅ CORRECT — use asyncio.Lock
import asyncio
lock = asyncio.Lock()

@app.get("/data")
async def get_data():
    async with lock:  # Only THIS coroutine waits; others continue normally
        data = await fetch_from_db()
    return data
```

### 3.7 Threading vs Multiprocessing Decision Matrix

```python
import asyncio
import concurrent.futures
import multiprocessing
from functools import partial

# Decision matrix:
# I/O-bound → asyncio (best) or threading
# CPU-bound → multiprocessing
# CPU-bound + needs shared state → threading (with GIL overhead)
# Mixed → asyncio + ProcessPoolExecutor

async def mixed_workload():
    """Combine async I/O with CPU-bound work in processes."""
    loop = asyncio.get_event_loop()
    
    # CPU-bound work offloaded to process pool
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        # Run CPU work in separate process
        cpu_result = await loop.run_in_executor(
            pool, cpu_intensive_task, large_data
        )
    
    # I/O-bound work stays async
    io_results = await asyncio.gather(
        fetch_from_api("endpoint1"),
        fetch_from_api("endpoint2"),
    )
    
    return cpu_result, io_results

def cpu_intensive_task(data):
    """Runs in separate process — no GIL contention."""
    return sum(x * x for x in data)
```

---

## 4. Free-Threading (PEP 703)

#### The Theory — Why Python is Removing the GIL (and What Changes)

**The problem:** Python's GIL (Global Interpreter Lock) prevents true parallel execution of threads. Even on a 64-core server, Python threads run ONE AT A TIME. For CPU-bound work, threading gives ZERO speedup.

**The history:**
```
1991: Python created with GIL (simpler implementation, no multi-core CPUs existed)
2005: Multi-core CPUs become standard. GIL becomes a bottleneck.
2005-2023: Many attempts to remove GIL failed (broke C extensions, slowed single-threaded code)
2023: PEP 703 accepted — gradual GIL removal starting Python 3.13
2024: Python 3.13 ships with experimental --disable-gil flag
2025: Python 3.14 makes free-threading easier to enable (PYTHON_GIL=0)
Future: GIL becomes opt-in, then removed entirely
```

**What changes for developers:**

| Aspect | With GIL (current) | Without GIL (free-threaded) |
|---|---|---|
| Threading for CPU work | Useless (serialized) | Actually parallel! |
| Thread safety | GIL protects most operations | YOU must use locks |
| `counter += 1` | Accidentally safe (GIL) | RACE CONDITION without lock |
| `list.append()` | Safe (GIL) | Needs synchronization |
| C extensions | Assume GIL exists | Must be updated |
| Performance (single-thread) | Baseline | ~5-10% slower (extra bookkeeping) |
| Performance (multi-thread CPU) | 1 core used | All cores used |

**When to care:**
- If you do **I/O-bound** work (web servers, API calls) → asyncio is still the best choice. Free-threading doesn't change this.
- If you do **CPU-bound** work (ML inference, data crunching) → free-threading finally makes threads useful. No more multiprocessing workarounds.
- If you maintain **libraries** → you need to audit thread safety. Code that "worked" because of GIL may now break.

**The 3 parallelism options in modern Python:**

| Approach | When to Use | Shared Memory? | Overhead |
|---|---|---|---|
| `asyncio` | I/O-bound (network, disk) | Yes (same process) | Minimal |
| `threading` (free-threaded) | CPU-bound, needs shared state | Yes (same process) | Lock management |
| `multiprocessing` | CPU-bound, isolation needed | No (serialization) | High (process creation) |
| Subinterpreters | CPU-bound, partial isolation | Limited (channels) | Medium |

**Industry perspective on free-threading:**

- **Meta/Instagram:** Actively contributing to free-threading. Their use case: parallel request processing within a single Django process (shared caches, shared model state). Currently they use multiprocessing which wastes memory duplicating model data across processes.

- **Scientific Python (NumPy, SciPy):** Already release the GIL in C extensions. Free-threading will let pure Python code also run in parallel alongside these C extensions — useful for ML pipelines that mix Python orchestration with C computation.

- **Gradual adoption (2025-2027):** Most companies are waiting. Free-threading breaks some C extensions and requires code audits for thread safety. Early adopters: data science teams with CPU-bound workloads that are currently forced to use multiprocessing.

- **What will NOT change:** Web servers will still use asyncio for I/O-bound work. Free-threading doesn't replace asyncio — it complements it for CPU-bound work within the same process.

### 4.1 No-GIL Python (3.13+)

```python
# Python 3.13+ with --disable-gil build flag
# or Python 3.14+ with PYTHON_GIL=0

import sys
import threading

# Check if free-threading is active
print(sys._is_gil_enabled())  # False on free-threaded builds

# True parallelism for CPU-bound threads
def compute_chunk(data: list[int]) -> int:
    return sum(x * x for x in data)

def parallel_sum(data: list[int], num_threads: int = 4) -> int:
    chunk_size = len(data) // num_threads
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    results = [0] * len(chunks)
    threads = []
    
    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=lambda idx, c: results.__setitem__(idx, compute_chunk(c)), 
                           args=(i, chunk))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    return sum(results)

# On free-threaded Python: actual parallel execution
# On GIL Python: serialized execution
```

### 4.2 Thread Safety Without GIL

```python
import threading
from typing import Any

# Without GIL, you need explicit synchronization
class ThreadSafeCounter:
    """Lock-based counter for free-threaded Python."""
    
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value

# Per-object locks (biased locking in CPython 3.13+)
# CPython uses biased locking — lock favors the thread that last held it
# This makes uncontended locking nearly free

# Atomic operations that are safe without locks
# (even without GIL, some operations are atomic at C level):
# - Reading/writing a single reference (pointer-sized)
# - dict.get(), dict[key] (individual operations)
# NOT atomic: counter += 1, list.append() in all cases
```

### 4.3 Subinterpreters (PEP 554)

```python
# Python 3.12+ interpreters module
import interpreters  # or _interpreters in some builds

# Each interpreter has its own GIL (even on GIL builds)
# True parallelism without shared state complications

def run_in_subinterpreter():
    interp = interpreters.create()
    
    # Code runs in isolated interpreter — no shared objects
    interp.run("""
import json
result = sum(range(10_000_000))
# Can't directly share Python objects
# Use channels or serialization
    """)
    
    interp.close()

# Channels for inter-interpreter communication
def channel_example():
    send_end, recv_end = interpreters.create_channel()
    
    interp = interpreters.create()
    interp.run(f"""
import interpreters
channel = interpreters.RecvChannel({recv_end.id})
data = channel.recv()
result = int(data) ** 2
    """)
```

---

## 5. Performance Engineering

#### The Theory — The Performance Mindset

**Rule #1:** Don't optimize without measuring first. Premature optimization is the root of all evil (Knuth). Profile → identify bottleneck → fix THAT specific thing.

**Where time goes in a typical Python web service:**

```
Typical FastAPI endpoint (total: 120ms):
  ├── Network/serialization: 5ms (4%)    — rarely the bottleneck
  ├── Pydantic validation: 2ms (2%)      — fast in v2
  ├── Business logic (Python): 8ms (7%)  — optimize only if complex
  ├── Database query: 80ms (67%)         — USUALLY the bottleneck
  ├── External API call: 20ms (17%)      — 2nd most common bottleneck
  └── Response serialization: 5ms (4%)   — orjson makes this near-zero
```

**The optimization priority (most impactful first):**

1. **Algorithm complexity** — O(n²) → O(n log n) = 1000x speedup for large n
2. **I/O reduction** — Fewer DB queries (N+1 problem), batch API calls
3. **Caching** — Don't recompute what doesn't change
4. **Concurrency** — `asyncio.gather()` for parallel I/O
5. **Data structures** — Right structure for the access pattern
6. **Python-level tricks** — `__slots__`, generators, f-strings
7. **C extensions** — Only for truly CPU-bound hot paths

**Types of profilers and when to use each:**

| Profiler | Type | Overhead | Use When |
|---|---|---|---|
| `cProfile` | Deterministic (traces every call) | High (2-5x slowdown) | Development, finding which function is slow |
| `py-spy` | Sampling (snapshots every 1ms) | Very low (<5%) | Production-safe, live debugging |
| `scalene` | Sampling + memory + GPU | Low | Finding memory leaks + CPU bottlenecks |
| `line_profiler` | Line-by-line timing | High | Knowing exactly WHICH line is slow |
| `memory_profiler` | Line-by-line memory | Very high | Finding which line allocates most |

**Key concept — Amdahl's Law:**
If 80% of time is in database queries, making Python code 10x faster only speeds up the remaining 20% → total speedup is only 1.25x. Always optimize the BIGGEST chunk first.

**Industry performance war stories:**

- **Instagram:** Their biggest optimization wasn't code — it was removing N+1 database queries. A single endpoint was doing 500 DB queries (one per follower). Fix: `prefetch_related()` in Django ORM → 2 queries total. Response time: 3s → 50ms.

- **Uber:** Python-based pricing service was slow. Profiling revealed 40% of time in JSON serialization (`json.dumps()`). Switching to `orjson` (Rust-based JSON library) gave 10x speedup in serialization — total endpoint latency dropped 30%.

- **Pinterest:** Serving 500M+ users, they found that Python's `re.match()` was called 1M times/second on HTML parsing. Pre-compiling regexes at import time (not per-request) saved 15% CPU.

- **Spotify:** Data pipeline was slow. Profiling showed list comprehensions creating millions of temporary lists. Switching to generator expressions reduced memory from 8GB to 200MB and speed improved 3x (less GC pressure).

- **Netflix:** Their recommendation engine uses Python for orchestration but Cython for matrix operations. Key insight: optimize the HOT LOOP, leave the rest in readable Python.

### 5.1 Profiling Tools

```python
# cProfile — deterministic profiler (overhead but precise)
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = expensive_computation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

# From command line:
# python -m cProfile -o output.prof script.py
# python -m pstats output.prof

# py-spy — sampling profiler (low overhead, production-safe)
# pip install py-spy
# py-spy record -o profile.svg -- python script.py
# py-spy top -- python script.py  (live view)
# py-spy dump --pid 12345  (attach to running process)

# scalene — CPU + memory + GPU profiler
# pip install scalene
# scalene script.py
# Shows: CPU time, memory allocation, memory copy, GPU
```

### 5.2 Data Structure Performance

```python
import timeit
from collections import deque, defaultdict
from dataclasses import dataclass

# List vs Deque for queue operations
# list.pop(0) is O(n) — shifts all elements
# deque.popleft() is O(1) — doubly-linked list

def benchmark_queue():
    # Bad: list as queue
    lst = list(range(10000))
    timeit.timeit(lambda: lst.pop(0), number=1000)  # Slow: O(n)
    
    # Good: deque as queue
    dq = deque(range(10000))
    timeit.timeit(lambda: dq.popleft(), number=1000)  # Fast: O(1)

# Dict operations are O(1) average — hash table
# But: dict preserves insertion order (Python 3.7+)
# set operations: union O(n+m), intersection O(min(n,m))

# Named tuples vs dataclasses vs dicts
# Memory:  namedtuple < dataclass with slots < dataclass < dict
# Speed:   namedtuple access ≈ tuple access (C-level)

from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])  # Immutable, tuple-based

@dataclass(slots=True, frozen=True)
class PointDC:
    x: float
    y: float
```

### 5.3 String Interning and Optimization

```python
import sys

# String interning — Python automatically interns:
# - Identifiers (variable names, attribute names)
# - Strings that look like identifiers
# - String constants in source code

a = "hello"
b = "hello"
assert a is b  # True — interned

a = "hello world"
b = "hello world"
# May or may not be same object (implementation detail)

# Explicit interning
a = sys.intern("some_frequently_used_string")
b = sys.intern("some_frequently_used_string")
assert a is b  # Always True — forces interning

# String concatenation performance
# Bad: O(n²) due to repeated allocations
def bad_concat(items):
    result = ""
    for item in items:
        result += str(item)  # Creates new string each time
    return result

# Good: O(n) with join
def good_concat(items):
    return "".join(str(item) for item in items)

# Even better for formatted strings: f-strings (compiled to FORMAT_VALUE opcode)
def fstring_concat(name, age):
    return f"{name} is {age} years old"  # Fastest for simple cases
```

### 5.4 Generator Pipelines for Memory Efficiency

```python
from typing import Iterator, Iterable
import itertools

def read_large_file(path: str) -> Iterator[str]:
    """Memory-efficient line-by-line reading."""
    with open(path) as f:
        for line in f:
            yield line.strip()

def parse_records(lines: Iterable[str]) -> Iterator[dict]:
    """Transform step — processes one record at a time."""
    for line in lines:
        if line and not line.startswith('#'):
            parts = line.split(',')
            yield {"id": parts[0], "value": float(parts[1])}

def filter_valid(records: Iterable[dict]) -> Iterator[dict]:
    """Filter step — constant memory regardless of input size."""
    return (r for r in records if r["value"] > 0)

def batch(iterable: Iterable, size: int) -> Iterator[list]:
    """Batch items for bulk operations."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

# Pipeline processes millions of records in constant memory
def process_pipeline(file_path: str):
    lines = read_large_file(file_path)
    records = parse_records(lines)
    valid = filter_valid(records)
    
    for record_batch in batch(valid, size=1000):
        bulk_insert(record_batch)
```

### 5.5 C Extensions and Cython

```python
# When Python is too slow, drop to C

# Option 1: ctypes (no compilation needed)
import ctypes

lib = ctypes.CDLL('./libfast.so')
lib.compute.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
lib.compute.restype = ctypes.c_double

# Option 2: Cython (best of both worlds)
# fast_module.pyx
"""
# cython: language_level=3
import cython

@cython.boundscheck(False)
@cython.wraparound(False)
def fast_sum(double[:] arr):
    cdef:
        int i
        int n = arr.shape[0]
        double total = 0.0
    
    for i in range(n):
        total += arr[i]
    
    return total
"""

# Option 3: PyO3 (Rust extension)
# Cargo.toml: pyo3 = { version = "0.20", features = ["extension-module"] }
"""
use pyo3::prelude::*;

#[pyfunction]
fn fast_sum(data: Vec<f64>) -> f64 {
    data.iter().sum()
}

#[pymodule]
fn my_module(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_sum, m)?)?;
    Ok(())
}
"""
```

### 5.6 `__slots__`, `__match_args__`, and Struct-Like Objects

```python
from dataclasses import dataclass
import struct

# For millions of objects: use __slots__ or arrays
@dataclass(slots=True)
class TradeEvent:
    timestamp: float
    symbol: str
    price: float
    quantity: int

# For extreme performance: struct module for binary packing
class PackedTrade:
    _format = 'd8sdf'  # double, 8-char string, double, float
    _size = struct.calcsize(_format)
    
    def __init__(self, buffer: bytes, offset: int = 0):
        self._data = struct.unpack_from(self._format, buffer, offset)
    
    @property
    def timestamp(self) -> float:
        return self._data[0]
    
    @property
    def symbol(self) -> str:
        return self._data[1].decode().strip('\x00')

# For columnar data: numpy structured arrays
import numpy as np

trade_dtype = np.dtype([
    ('timestamp', 'f8'),
    ('symbol', 'U8'),
    ('price', 'f8'),
    ('quantity', 'i4'),
])

trades = np.zeros(1_000_000, dtype=trade_dtype)
# 1M trades in ~44MB (vs ~200MB+ with Python objects)
```

---

## 6. Advanced Type System

#### The Theory — Why Types Matter in Large Python Codebases

**Python is dynamically typed.** So why add types? Because at scale (50+ files, 5+ developers), types become your documentation AND your safety net.

**What static typing gives you:**

```
Without types (small project, 1 developer):
  def process(data):      # What's data? dict? list? str?
      return data["key"]  # Crashes at runtime if data is wrong type

With types (large project, team):
  def process(data: UserProfile) -> ProcessedResult:
      return ProcessedResult(name=data.name)  
      # IDE autocomplete works
      # Typos caught before running
      # Refactoring is safe (rename a field → type checker finds all usages)
```

**The type system features and when you need them:**

| Feature | What It Solves | Example |
|---|---|---|
| Basic types (`str`, `int`) | Documentation + IDE help | `def greet(name: str) -> str` |
| `Optional[X]` / `X \| None` | Explicit null handling | Forces you to check for None |
| `TypeVar` + `Generic` | Type-safe containers/repos | `Repository[User]` knows it returns `User` |
| `Protocol` | Interface without inheritance | Any class with `.read()` satisfies `Readable` |
| `ParamSpec` | Type-safe decorators | Decorated function keeps its type signature |
| `TypeGuard` / `TypeIs` | Type narrowing in branches | After `if is_admin(user):` → type is `AdminUser` |
| `Literal` | Restrict to specific values | `mode: Literal["read", "write"]` |
| `TypedDict` | Typed dictionaries | For API responses, config dicts |
| `overload` | Different return types per input | `get(id) -> User` vs `get(ids) -> list[User]` |

**Industry adoption:**
- **Stripe:** 100% typed Python (uses mypy in strict mode)
- **Instagram/Meta:** Gradually typed (pyre type checker)
- **Dropbox:** Typed critical paths (mypy originally created at Dropbox)
- **Google:** pytype for large internal codebases

**Practical rule:** Type your function signatures and class attributes. Don't type local variables (type inference handles those).

**Industry examples:**

- **Stripe:** 100% typed Python (mypy strict mode). They credit type safety for being able to refactor their payment processing code (handles billions of dollars) without introducing bugs. When you change a function signature, mypy catches EVERY caller that needs updating.

- **Instagram (Meta):** Uses `pyre` (their own type checker). Adding types to their Django codebase caught 100+ latent bugs that would have been production incidents. Their rule: all new code must be fully typed.

- **Dropbox:** Created mypy (the most popular Python type checker). Typed 4 million lines of Python. Found and fixed thousands of bugs that tests missed — especially None-related crashes.

- **Google:** Uses `pytype` (infers types even without annotations). Runs on 100M+ lines of internal Python code. The type checker IS the documentation — no stale docstrings.

- **Microsoft/Pylance:** Created `pyright` (fastest type checker). Used internally on VS Code's Python extension and Azure SDK. Their recommendation: pyright in strict mode for new projects.

### 6.1 Generics and TypeVar

```python
from typing import TypeVar, Generic, Protocol, overload
from collections.abc import Sequence

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Repository(Generic[T]):
    """Generic repository pattern."""
    
    def __init__(self):
        self._store: dict[str, T] = {}
    
    def get(self, id: str) -> T | None:
        return self._store.get(id)
    
    def save(self, id: str, entity: T) -> None:
        self._store[id] = entity
    
    def list_all(self) -> list[T]:
        return list(self._store.values())

# Bounded TypeVar
Comparable = TypeVar('Comparable', bound='SupportsLessThan')

class SupportsLessThan(Protocol):
    def __lt__(self, other: 'SupportsLessThan') -> bool: ...

def max_item(items: Sequence[Comparable]) -> Comparable:
    return max(items)
```

### 6.2 Protocols (Structural Typing)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Serializable': ...

@runtime_checkable
class Repository(Protocol[T]):
    async def get(self, id: str) -> T | None: ...
    async def save(self, entity: T) -> None: ...
    async def delete(self, id: str) -> bool: ...

# Any class implementing these methods satisfies the Protocol
# No inheritance needed — structural (duck) typing
class UserRepo:
    async def get(self, id: str) -> User | None:
        return await db.users.find_one({"_id": id})
    
    async def save(self, entity: User) -> None:
        await db.users.update_one(
            {"_id": entity.id}, {"$set": entity.to_dict()}, upsert=True
        )
    
    async def delete(self, id: str) -> bool:
        result = await db.users.delete_one({"_id": id})
        return result.deleted_count > 0

# UserRepo satisfies Repository[User] without explicit inheritance
def process(repo: Repository[User]):
    ...
```

### 6.3 ParamSpec and Concatenate

```python
from typing import ParamSpec, Concatenate, TypeVar, Callable
from functools import wraps
import time

P = ParamSpec('P')
R = TypeVar('R')

def timing(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that preserves type information perfectly."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timing
def process_data(items: list[int], multiplier: float) -> float:
    return sum(items) * multiplier

# Type checker knows: process_data(items: list[int], multiplier: float) -> float

# Concatenate — add parameters to the front
def with_session(
    func: Callable[Concatenate[Session, P], R]
) -> Callable[P, R]:
    """Inject database session as first argument."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with get_session() as session:
            return func(session, *args, **kwargs)
    return wrapper

@with_session
def get_user(session: Session, user_id: str) -> User:
    return session.query(User).get(user_id)

# Caller sees: get_user(user_id: str) -> User
```

### 6.4 TypeGuard and TypeNarrowing

```python
from typing import TypeGuard, TypeIs, assert_never

class Dog:
    def bark(self): ...

class Cat:
    def meow(self): ...

Animal = Dog | Cat

# TypeGuard — narrows type in if-branch
def is_dog(animal: Animal) -> TypeGuard[Dog]:
    return isinstance(animal, Dog)

# TypeIs (Python 3.13+) — narrows in both branches
def is_dog_v2(animal: Animal) -> TypeIs[Dog]:
    return isinstance(animal, Dog)

def handle_animal(animal: Animal):
    if is_dog_v2(animal):
        animal.bark()   # Type: Dog
    else:
        animal.meow()   # Type: Cat (narrowed in else branch too!)

# Exhaustiveness checking with assert_never
def process(animal: Animal) -> str:
    match animal:
        case Dog():
            return "woof"
        case Cat():
            return "meow"
        case _ as unreachable:
            assert_never(unreachable)  # Type error if Animal gets new variant
```

---

## 7. Metaclasses & Descriptors

#### The Theory — Python's Object Model Under the Hood

**Everything in Python is an object.** Classes are objects too. A metaclass is the "class of a class" — it controls how classes themselves are created.

**The creation chain:**
```
object → the base of all instances
type   → the base of all classes (type IS a metaclass)

When you write:
  class Dog:
      pass

Python actually does:
  Dog = type('Dog', (object,), {'__module__': '__main__'})
  #     ^^^^
  #     This is the metaclass calling! type.__call__() creates the class.

When you write:
  class Dog(metaclass=MyMeta):
      pass

Python does:
  Dog = MyMeta('Dog', (object,), {...})
  #     ^^^^^^
  #     YOUR metaclass controls how Dog (the class) is built.
```

**When to use each:**

| Mechanism | What It Does | Use When | Example |
|---|---|---|---|
| `__init__` | Controls instance creation | Normal object setup | `User(name="Bob")` |
| `__init_subclass__` | Runs when a subclass is defined | Plugin registry, validation | Auto-register handlers |
| `__class_getitem__` | `MyClass[T]` syntax | Generic containers | `Repository[User]` |
| Descriptor (`__get__/__set__`) | Controls attribute access | Validation, computed properties | `price = PositiveInt()` |
| Metaclass (`__new__`) | Controls CLASS creation | Framework internals, ORMs | Django models, SQLAlchemy |

**Industry reality:**
- You will **use** metaclass-based libraries daily (Django ORM, SQLAlchemy, Pydantic, dataclasses)
- You will **write** metaclasses almost never (prefer `__init_subclass__` for 95% of cases)
- You MUST **understand** them to debug framework issues and for senior interviews

**Where metaclasses/descriptors are used in real frameworks:**

- **Django ORM:** `class User(models.Model)` → Django's metaclass (`ModelBase`) scans all `Field` descriptors, creates the database schema, sets up manager methods. When you write `User.objects.filter(age=25)`, the entire query builder is powered by descriptors and metaclass magic.

- **SQLAlchemy:** `mapped_column()` is a descriptor. When you access `user.name`, SQLAlchemy's descriptor decides whether to load from cache, fire a SQL query (lazy loading), or return an instrumented attribute.

- **Pydantic:** Uses `__init_subclass__` and metaclass-like behavior to generate validators at class definition time. When you define `class User(BaseModel)`, Pydantic inspects type annotations and builds fast validation code ONCE (at import time, not per-request).

- **dataclasses:** The `@dataclass` decorator reads your annotations and generates `__init__`, `__repr__`, `__eq__` methods. This is descriptor + metaclass-adjacent behavior (code generation at class creation time).

- **pytest:** Uses metaclasses to discover test methods (any function starting with `test_`), collect fixtures (via introspection), and build the test graph.

**Descriptor protocol (the backbone of Python's attribute system):**
```
When you do obj.attr:
  1. Python checks type(obj).__mro__ for a DATA descriptor (has __set__ or __delete__)
  2. If found → call descriptor.__get__(obj, type(obj))
  3. If not → check obj.__dict__['attr']
  4. If not → check type(obj).__dict__['attr'] for a NON-DATA descriptor (only __get__)
  5. If not → raise AttributeError

This is why @property, @classmethod, @staticmethod, and __slots__ all work.
They are ALL descriptors.
```

### 7.1 Metaclass Fundamentals

```python
# Metaclass: a class whose instances are classes
# type is the default metaclass

# Class creation process:
# 1. Python finds metaclass (type by default)
# 2. Calls metaclass.__new__(mcs, name, bases, namespace)
# 3. Calls metaclass.__init__(cls, name, bases, namespace)

class SingletonMeta(type):
    """Metaclass that ensures only one instance of a class exists."""
    _instances: dict[type, object] = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self, url: str):
        self.url = url
        self.connected = False

# Always returns same instance
conn1 = DatabaseConnection("postgresql://localhost/db")
conn2 = DatabaseConnection("postgresql://localhost/db")
assert conn1 is conn2


class ValidatedMeta(type):
    """Metaclass that enforces class structure at definition time."""
    
    def __new__(mcs, name, bases, namespace):
        # Skip validation for base classes
        if bases:
            required_methods = getattr(bases[0], '_required_methods', [])
            for method in required_methods:
                if method not in namespace:
                    raise TypeError(
                        f"Class {name} must implement {method}()"
                    )
        
        return super().__new__(mcs, name, bases, namespace)

class BaseHandler(metaclass=ValidatedMeta):
    _required_methods = ['handle', 'validate']

# This will raise TypeError at class definition time (not runtime!)
# class BadHandler(BaseHandler):
#     def handle(self): ...
#     # Missing validate() → TypeError
```

### 7.2 Descriptors

```python
from typing import Any, TypeVar, Generic, get_type_hints

T = TypeVar('T')

class Validated(Generic[T]):
    """Descriptor that validates on assignment."""
    
    def __init__(self, validator=None, default=None):
        self.validator = validator
        self.default = default
        self.attr_name = None
    
    def __set_name__(self, owner, name):
        self.attr_name = name
        self.private_name = f"_validated_{name}"
    
    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self  # Class-level access
        return getattr(obj, self.private_name, self.default)
    
    def __set__(self, obj, value: T):
        if self.validator and not self.validator(value):
            raise ValueError(
                f"Invalid value for {self.attr_name}: {value!r}"
            )
        setattr(obj, self.private_name, value)

class PositiveInt(Validated[int]):
    def __init__(self, default=0):
        super().__init__(validator=lambda x: isinstance(x, int) and x > 0, default=default)

class NonEmptyStr(Validated[str]):
    def __init__(self, default=""):
        super().__init__(validator=lambda x: isinstance(x, str) and len(x) > 0, default=default)

class Product:
    name = NonEmptyStr()
    price = PositiveInt()
    quantity = PositiveInt(default=1)
    
    def __init__(self, name: str, price: int, quantity: int = 1):
        self.name = name
        self.price = price
        self.quantity = quantity

p = Product("Widget", 100, 5)
# p.price = -1  → ValueError
# p.name = ""   → ValueError
```

### 7.3 `__init_subclass__` (Modern Alternative to Metaclasses)

```python
class PluginBase:
    """Registry pattern using __init_subclass__."""
    _registry: dict[str, type] = {}
    
    def __init_subclass__(cls, plugin_name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__.lower()
        cls._registry[name] = cls
    
    @classmethod
    def create(cls, name: str, **kwargs):
        if name not in cls._registry:
            raise ValueError(f"Unknown plugin: {name}")
        return cls._registry[name](**kwargs)

class JSONParser(PluginBase, plugin_name="json"):
    def parse(self, data: str) -> dict:
        import json
        return json.loads(data)

class XMLParser(PluginBase, plugin_name="xml"):
    def parse(self, data: str) -> dict:
        ...

# Dynamic dispatch
parser = PluginBase.create("json")
result = parser.parse('{"key": "value"}')
```

---

## 8. Design Patterns at Scale

#### The Theory — Why Patterns Exist (and When NOT to Use Them)

Design patterns are **solutions to recurring problems** in large codebases. They exist because teams of 5-50 engineers need:
1. Shared vocabulary ("Use a Repository" is clearer than explaining the entire abstraction)
2. Testability (can mock dependencies, test in isolation)
3. Flexibility (swap implementations without changing business logic)

**The patterns in this section and when you NEED them:**

```
Simple app (1 developer, <10 endpoints):
  → You DON'T need these patterns. Direct DB calls are fine.
  → Adding Repository + UoW + CQRS is over-engineering.

Medium app (3-5 developers, 20-50 endpoints):
  → Repository pattern ← helpful (testability)
  → Unit of Work ← helpful (transaction management)
  → Retry/Circuit Breaker ← helpful (external service resilience)

Large app (10+ developers, microservices):
  → ALL of these patterns ← necessary for maintainability
  → CQRS ← when read/write have different scaling needs
  → Event Sourcing ← when you need audit trail + temporal queries
```

**How the patterns relate:**

```
HTTP Request
    ↓
[FastAPI Endpoint] ← thin, just delegates
    ↓
[Application Service / Command Handler] ← orchestration, no business logic
    ↓
[Domain Model] ← business rules live HERE
    ↓
[Repository] ← abstracts data storage
    ↓
[Database / External Service]

Wrapped by:
  - Unit of Work → groups multiple repo operations in one transaction
  - Circuit Breaker → protects against failed external calls
  - Retry → handles transient failures
  - Event Bus → decouples side effects (send email, update cache)
```

**Key principle — Dependency Inversion:**
- Domain layer defines INTERFACES (abstract Repository)
- Infrastructure layer provides IMPLEMENTATIONS (PostgresRepository)
- The domain NEVER imports from infrastructure
- This makes business logic testable with in-memory fakes

**Industry examples:**

- **Stripe:** Uses CQRS extensively. Their payment processing (write) path is separate from their dashboard (read) path. Write path uses PostgreSQL with strict consistency. Read path uses Elasticsearch with eventual consistency. This lets them scale reads independently.

- **Netflix:** Event Sourcing for their billing system. Every subscription change, pause, price change is an event. They can reconstruct any account's state at any point in time (required for disputes and audits).

- **Shopify:** Circuit breaker on every external payment gateway. When a payment provider is down, Shopify automatically routes to a backup provider. Without this, one provider's outage would mean ALL Shopify stores can't accept payments.

- **Uber:** Saga pattern for ride booking. Reserve driver → charge rider → start trip. If any step fails, compensating actions undo previous steps (release driver, refund rider). This replaced their earlier fragile distributed transaction approach.

- **Amazon (internal):** Retry with exponential backoff is MANDATORY for all inter-service calls. Their internal SDK enforces this. Without it, cascading retries during outages create "retry storms" that make problems worse.

### 8.1 Repository Pattern

#### The Theory

Repository = an abstraction over data storage. Your business logic says "save this user" without knowing if it goes to PostgreSQL, MongoDB, or an in-memory dict. This lets you:
1. Test business logic without a real database (use `InMemoryRepository`)
2. Swap databases without changing business code
3. Keep SQL/ORM details OUT of your domain layer

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Protocol
from dataclasses import dataclass, field
from uuid import UUID, uuid4

T = TypeVar('T')

@dataclass
class Entity:
    id: UUID = field(default_factory=uuid4)

@dataclass
class User(Entity):
    email: str = ""
    name: str = ""
    is_active: bool = True

class Repository(ABC, Generic[T]):
    """Abstract repository — domain layer knows only this interface."""
    
    @abstractmethod
    async def get(self, id: UUID) -> T | None: ...
    
    @abstractmethod
    async def save(self, entity: T) -> T: ...
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool: ...
    
    @abstractmethod
    async def find_by(self, **criteria) -> list[T]: ...

class UserRepository(Repository[User]):
    """Concrete implementation — infrastructure layer."""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    async def get(self, id: UUID) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == id)
            )
            row = result.scalar_one_or_none()
            return self._to_entity(row) if row else None
    
    async def save(self, entity: User) -> User:
        async with self._session_factory() as session:
            model = self._to_model(entity)
            session.add(model)
            await session.commit()
            return entity
    
    async def delete(self, id: UUID) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                delete(UserModel).where(UserModel.id == id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def find_by(self, **criteria) -> list[User]:
        async with self._session_factory() as session:
            query = select(UserModel)
            for key, value in criteria.items():
                query = query.where(getattr(UserModel, key) == value)
            result = await session.execute(query)
            return [self._to_entity(row) for row in result.scalars()]
    
    def _to_entity(self, model) -> User:
        return User(id=model.id, email=model.email, name=model.name)
    
    def _to_model(self, entity: User):
        return UserModel(id=entity.id, email=entity.email, name=entity.name)
```

### 8.2 Unit of Work Pattern

#### The Theory

Unit of Work = "do multiple things in ONE database transaction, or none at all."

Without UoW:
```
await user_repo.save(user)        ← commits immediately
await order_repo.save(order)      ← commits immediately
# If this line fails, user was saved but order wasn't → INCONSISTENT STATE
```

With UoW:
```
async with uow:
    await uow.users.save(user)     ← staged, not committed
    await uow.orders.save(order)   ← staged, not committed
    await uow.commit()             ← BOTH saved atomically
# If anything fails before commit() → NOTHING is saved (rollback)
```

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

class UnitOfWork:
    """Coordinates writes across multiple repositories in a single transaction."""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    async def __aenter__(self):
        self._session = self._session_factory()
        self.users = UserRepository(self._session)
        self.orders = OrderRepository(self._session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self._session.close()
    
    async def commit(self):
        await self._session.commit()
    
    async def rollback(self):
        await self._session.rollback()

# Usage
async def transfer_order(uow: UnitOfWork, user_id: UUID, order_data: dict):
    async with uow:
        user = await uow.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        order = Order(user_id=user_id, **order_data)
        await uow.orders.save(order)
        
        user.order_count += 1
        await uow.users.save(user)
        
        await uow.commit()  # Both writes in same transaction
```

### 8.3 CQRS (Command Query Responsibility Segregation)

#### The Theory

**CQRS** = use DIFFERENT models (even different databases) for reading vs writing.

**Why?** Because reads and writes have different requirements:
- **Writes (Commands):** Need validation, consistency, business rules. Go through domain model.
- **Reads (Queries):** Need speed, joins, projections. Can use denormalized views.

```
Traditional (same model for read + write):
  [User Table] ← writes here, reads here
  Problem: complex joins for dashboard queries slow down the whole system.

CQRS:
  Write side: [User Table] ← normalized, validated, consistent
  Read side:  [user_profiles_view] ← denormalized, pre-joined, FAST
  
  Write updates the source → event triggers → updates the read model
```

**When to use CQRS:**
- Read and write workloads are very different (90% reads, 10% writes)
- Dashboard/reporting queries are complex and slow
- You need different scaling (10 read replicas, 1 write primary)

**When NOT to use CQRS:** Simple CRUD apps where reads and writes are similar.

```python
from dataclasses import dataclass
from typing import Any
from abc import ABC, abstractmethod

# Commands — write side
@dataclass(frozen=True)
class Command:
    pass

@dataclass(frozen=True)
class CreateUserCommand(Command):
    email: str
    name: str

@dataclass(frozen=True)
class DeactivateUserCommand(Command):
    user_id: UUID

class CommandHandler(ABC):
    @abstractmethod
    async def handle(self, command: Command) -> Any: ...

class CreateUserHandler(CommandHandler):
    def __init__(self, repo: UserRepository, event_bus: EventBus):
        self._repo = repo
        self._event_bus = event_bus
    
    async def handle(self, command: CreateUserCommand) -> UUID:
        user = User(email=command.email, name=command.name)
        await self._repo.save(user)
        await self._event_bus.publish(UserCreatedEvent(user_id=user.id))
        return user.id

# Queries — read side (can use optimized read models)
@dataclass(frozen=True)
class Query:
    pass

@dataclass(frozen=True)
class GetUserProfileQuery(Query):
    user_id: UUID

class QueryHandler(ABC):
    @abstractmethod
    async def handle(self, query: Query) -> Any: ...

class GetUserProfileHandler(QueryHandler):
    def __init__(self, read_db):
        self._read_db = read_db  # Denormalized read model
    
    async def handle(self, query: GetUserProfileQuery) -> dict:
        return await self._read_db.find_one(
            "user_profiles", {"user_id": str(query.user_id)}
        )

# Mediator dispatches to correct handler
class Mediator:
    def __init__(self):
        self._handlers: dict[type, Any] = {}
    
    def register(self, message_type: type, handler):
        self._handlers[message_type] = handler
    
    async def send(self, message) -> Any:
        handler = self._handlers.get(type(message))
        if not handler:
            raise ValueError(f"No handler for {type(message).__name__}")
        return await handler.handle(message)
```

### 8.4 Event Sourcing

#### The Theory

**Event Sourcing** = instead of storing the CURRENT state, store every EVENT that happened. Rebuild state by replaying events.

```
Traditional (store current state):
  BankAccount: {id: 1, balance: 150}
  Problem: HOW did it become 150? Was it 200-50? 100+50? You can't tell.

Event Sourcing (store history):
  Event 1: AccountCreated(balance=0)
  Event 2: MoneyDeposited(amount=200)
  Event 3: MoneyWithdrawn(amount=50)
  Current state: replay events → 0 + 200 - 50 = 150 ✓
  You know EXACTLY what happened and WHEN.
```

**Benefits:**
- Complete audit trail (financial compliance, debugging)
- Time travel (what was the state at 3pm yesterday?)
- Rebuild read models (create new views from old events)
- Debugging (replay events to reproduce bugs exactly)

**Drawbacks:**
- Complexity (event versioning, schema evolution)
- Storage (events grow forever — need snapshotting)
- Querying (can't SELECT WHERE balance > 100 — need read projections)

**Used by:** Banking systems, trading platforms, inventory management, collaborative editing (Google Docs events).

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any
import json

@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default=None)

@dataclass(frozen=True)
class AccountCreated(DomainEvent):
    owner_name: str = ""
    initial_balance: float = 0.0

@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    amount: float = 0.0

@dataclass(frozen=True)
class MoneyWithdrawn(DomainEvent):
    amount: float = 0.0

class BankAccount:
    """Event-sourced aggregate — state derived from events."""
    
    def __init__(self):
        self.id: UUID | None = None
        self.owner_name: str = ""
        self.balance: float = 0.0
        self._pending_events: list[DomainEvent] = []
    
    @classmethod
    def create(cls, owner_name: str, initial_balance: float = 0.0) -> 'BankAccount':
        account = cls()
        account._apply(AccountCreated(
            aggregate_id=uuid4(),
            owner_name=owner_name,
            initial_balance=initial_balance,
        ))
        return account
    
    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._apply(MoneyDeposited(aggregate_id=self.id, amount=amount))
    
    def withdraw(self, amount: float):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self._apply(MoneyWithdrawn(aggregate_id=self.id, amount=amount))
    
    def _apply(self, event: DomainEvent):
        self._handle(event)
        self._pending_events.append(event)
    
    def _handle(self, event: DomainEvent):
        match event:
            case AccountCreated(aggregate_id=aid, owner_name=name, initial_balance=bal):
                self.id = aid
                self.owner_name = name
                self.balance = bal
            case MoneyDeposited(amount=amount):
                self.balance += amount
            case MoneyWithdrawn(amount=amount):
                self.balance -= amount
    
    @classmethod
    def from_events(cls, events: list[DomainEvent]) -> 'BankAccount':
        """Rebuild state from event history."""
        account = cls()
        for event in events:
            account._handle(event)
        return account
    
    def collect_events(self) -> list[DomainEvent]:
        events = self._pending_events[:]
        self._pending_events.clear()
        return events

class EventStore:
    """Append-only event store."""
    
    def __init__(self):
        self._events: dict[UUID, list[DomainEvent]] = {}
    
    async def save(self, aggregate_id: UUID, events: list[DomainEvent], expected_version: int):
        existing = self._events.get(aggregate_id, [])
        if len(existing) != expected_version:
            raise ConcurrencyError("Aggregate was modified by another process")
        
        self._events.setdefault(aggregate_id, []).extend(events)
    
    async def load(self, aggregate_id: UUID) -> list[DomainEvent]:
        return self._events.get(aggregate_id, [])
```

### 8.5 Circuit Breaker

```python
import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"         # Normal operation
    OPEN = "open"             # Failing — reject all calls
    HALF_OPEN = "half_open"   # Testing if service recovered

@dataclass
class CircuitBreaker:
    """Prevents cascading failures in distributed systems."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpen(
                f"Circuit is open. Retry after {self.recovery_timeout}s"
            )
        
        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpen("Half-open call limit reached")
            self._half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
        self._failure_count = 0
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

class CircuitBreakerOpen(Exception):
    pass

# Usage
payment_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

async def charge_payment(amount: float):
    return await payment_breaker.call(external_payment_api, amount)
```

### 8.6 Retry with Exponential Backoff

```python
import asyncio
import random
from functools import wraps
from typing import TypeVar, Callable, Type

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator for async retry with exponential backoff and jitter."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                    
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

@retry(max_attempts=5, retryable_exceptions=(ConnectionError, TimeoutError))
async def call_external_service(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post("https://api.example.com/process", json=payload)
        response.raise_for_status()
        return response.json()
```

---

## 9. FastAPI Production Patterns

#### The Theory — Why FastAPI and How It Works Internally

**FastAPI** is built on:
- **Starlette** (async web framework — handles routing, middleware, WebSocket)
- **Pydantic** (data validation — converts and validates request/response data)
- **Uvicorn** (ASGI server — handles HTTP connections, passes to FastAPI)

**Request lifecycle in FastAPI:**
```
1. Client sends HTTP request
2. Uvicorn receives TCP connection, parses HTTP
3. ASGI interface passes request to Starlette
4. Middleware stack executes (CORS, auth, logging)
5. Router matches URL to endpoint function
6. Dependency injection resolves dependencies (DB session, current user, etc.)
7. Pydantic validates request body/query params
8. Your endpoint function executes (async or sync)
9. Pydantic serializes response
10. Middleware stack executes (response side)
11. Uvicorn sends HTTP response back to client
```

**Why FastAPI over Django/Flask for new projects (2025+):**

| Feature | FastAPI | Django | Flask |
|---|---|---|---|
| Async native | Yes | Partial (Django 4.1+) | No (needs extensions) |
| Type validation | Built-in (Pydantic) | Django Forms/DRF Serializers | Manual |
| OpenAPI docs | Automatic (Swagger/ReDoc) | Needs DRF + drf-yasg | Manual |
| Performance | ~15K req/s | ~3K req/s | ~5K req/s |
| Learning curve | Low (if you know Python types) | High (ORM, admin, templates) | Low |
| Best for | APIs, microservices | Full-stack web apps | Small APIs, prototypes |

**Key production decisions:**

| Decision | Choice | Why |
|---|---|---|
| Workers | `uvicorn --workers 4` (= CPU cores) | One process per core, each handles thousands of connections |
| Sync vs async endpoints | Async for I/O, sync for CPU-bound | Sync endpoints run in threadpool automatically |
| Dependency injection | Use `Depends()` everywhere | Testable, reusable, auto-cleanup |
| Error handling | Global exception handlers | Consistent error format across all endpoints |
| Background tasks | `BackgroundTasks` for light work, Celery for heavy | Don't block the response |

**Companies using FastAPI in production:**

- **Microsoft:** Azure Cognitive Services, some internal APIs
- **Netflix:** Dispatch (incident management), internal tooling
- **Uber:** Internal ML model serving APIs
- **Explosion (spaCy):** NLP model serving
- **JPMorgan Chase:** Internal trading APIs
- **Robinhood:** Parts of their trading platform
- **Samsung:** SmartThings IoT platform APIs

**Why these companies chose FastAPI over Django REST Framework:**
1. Native async → 5-10x better throughput for I/O-heavy services
2. Auto-generated OpenAPI docs → frontend teams self-serve
3. Pydantic validation → catches bad data before it hits business logic
4. Lighter weight → faster startup, smaller containers, cheaper in K8s
5. Type safety → IDE support + fewer runtime errors

**Common production FastAPI architecture (industry standard):**
```
src/
├── main.py              ← app factory, middleware, lifespan
├── api/
│   ├── v1/
│   │   ├── users.py    ← endpoint functions (thin, just delegates)
│   │   └── orders.py
│   └── deps.py         ← shared dependencies (get_db, get_user)
├── services/            ← business logic (testable without HTTP)
├── repositories/        ← database access (abstracts SQLAlchemy)
├── models/              ← SQLAlchemy models (DB schema)
├── schemas/             ← Pydantic models (API contracts)
├── core/                ← config, security, events
└── workers/             ← background tasks (Celery/ARQ)
```

### 9.1 Application Structure

```
src/
├── main.py                  # App entry point
├── config.py                # Settings management
├── dependencies.py          # DI container
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py       # Main v1 router
│   │   ├── users.py        # User endpoints
│   │   └── orders.py       # Order endpoints
│   └── middleware.py
├── domain/
│   ├── __init__.py
│   ├── entities.py          # Domain models
│   ├── value_objects.py
│   ├── services.py          # Domain services
│   └── events.py
├── infrastructure/
│   ├── __init__.py
│   ├── database.py          # DB session management
│   ├── repositories.py      # Concrete repos
│   ├── cache.py
│   └── messaging.py
└── shared/
    ├── __init__.py
    ├── exceptions.py
    └── pagination.py
```

### 9.2 Dependency Injection

```python
from fastapi import FastAPI, Depends, Request
from functools import lru_cache
from typing import Annotated, AsyncIterator
from contextlib import asynccontextmanager

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/app"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me"
    debug: bool = False
    
    model_config = {"env_file": ".env"}

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Async database session dependency
async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)]
) -> AsyncIterator[AsyncSession]:
    async with async_session_factory(settings.database_url)() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Service dependency with repo injection
async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    repo = UserRepository(session)
    cache = RedisCache(settings.redis_url)
    return UserService(repo, cache)

# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pool = await create_db_pool()
    redis = await create_redis_pool()
    app.state.db_pool = pool
    app.state.redis = redis
    
    yield
    
    # Shutdown
    await pool.dispose()
    await redis.close()

app = FastAPI(lifespan=lifespan)
```

### 9.3 Middleware Stack

```python
import time
import uuid
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger()

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        structlog.contextvars.unbind_contextvars("request_id")
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis, rate: int = 100, window: int = 60):
        super().__init__(app)
        self.redis = redis
        self.rate = rate
        self.window = window
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"ratelimit:{client_ip}"
        
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window)
        
        if current > self.rate:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                headers={
                    "Retry-After": str(self.window),
                    "X-RateLimit-Limit": str(self.rate),
                    "X-RateLimit-Remaining": "0",
                },
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rate - current))
        return response

# Register middleware (order matters — last added = first executed)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, redis=redis_client, rate=100)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 9.4 Error Handling

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None

class AppException(Exception):
    def __init__(self, status_code: int, error: str, detail: str | None = None):
        self.status_code = status_code
        self.error = error
        self.detail = detail

class NotFoundError(AppException):
    def __init__(self, resource: str, id: Any):
        super().__init__(404, "not_found", f"{resource} with id={id} not found")

class ConflictError(AppException):
    def __init__(self, detail: str):
        super().__init__(409, "conflict", detail)

class ValidationError(AppException):
    def __init__(self, detail: str):
        super().__init__(422, "validation_error", detail)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            detail=exc.detail,
            request_id=getattr(request.state, 'request_id', None),
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            detail="An unexpected error occurred" if app.debug else None,
            request_id=getattr(request.state, 'request_id', None),
        ).model_dump(),
    )
```

### 9.5 Background Tasks and Workers

```python
from fastapi import BackgroundTasks
import asyncio
from typing import Callable, Any

# Simple background task
@app.post("/users/", status_code=201)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.create(user_data)
    
    # Fire-and-forget tasks
    background_tasks.add_task(send_welcome_email, user.email)
    background_tasks.add_task(notify_analytics, "user_created", user.id)
    
    return user

# For heavy processing: use a task queue (Celery, ARQ, or Dramatiq)
from arq import create_pool
from arq.connections import RedisSettings

async def get_task_queue():
    return await create_pool(RedisSettings(host='localhost'))

@app.post("/reports/generate")
async def generate_report(
    request: ReportRequest,
    queue = Depends(get_task_queue),
):
    job = await queue.enqueue_job(
        'generate_report_task',
        request.model_dump(),
        _queue_name='reports',
    )
    return {"job_id": job.job_id, "status": "queued"}

# ARQ worker function
async def generate_report_task(ctx: dict, report_config: dict):
    """Runs in separate worker process."""
    report = await build_report(report_config)
    await upload_to_s3(report)
    await notify_user(report_config["user_id"], report.url)
```

### 9.6 Pagination

```python
from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Sequence
from fastapi import Query

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

def paginate(
    items: Sequence[T],
    total: int,
    params: PaginationParams,
) -> PaginatedResponse[T]:
    total_pages = (total + params.page_size - 1) // params.page_size
    return PaginatedResponse(
        items=list(items),
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_previous=params.page > 1,
    )

# Cursor-based pagination (better for large datasets)
class CursorPaginationParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=100)

class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool

@app.get("/users/")
async def list_users(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: Annotated[UserService, Depends(get_user_service)] = None,
):
    users, next_cursor = await service.list_with_cursor(cursor, limit)
    return CursorPaginatedResponse(
        items=users,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
```

---

## 10. SQLAlchemy 2.0 & Database Patterns

#### The Theory — SQLAlchemy 2.0: The Python Database Standard

**SQLAlchemy** is not just an ORM — it has two distinct layers:
- **Core** (low-level): SQL expression language, connection management, connection pooling
- **ORM** (high-level): Object-Relational Mapping, session management, lazy loading

**SQLAlchemy 2.0 vs 1.x (breaking changes):**

| Feature | 1.x (legacy) | 2.0 (modern) |
|---|---|---|
| Query style | `session.query(User).filter()` | `select(User).where()` |
| Execute | `session.execute(query)` | Same but returns `Row` objects |
| Typing | Weak | Full type support with `Mapped[T]` |
| Async | Add-on | First-class (`AsyncSession`) |
| Model definition | `Column(Integer)` | `mapped_column(Integer)` or type annotation |

**The Session lifecycle (critical to understand):**
```
1. Create session (from sessionmaker/async_sessionmaker)
2. Load objects (SELECT) — objects are now "tracked" by session
3. Modify objects (Python attribute changes) — session detects changes
4. Flush — sends SQL to DB (INSERT/UPDATE/DELETE) but NOT committed
5. Commit — makes changes permanent (or Rollback to undo)
6. Close — detach all objects, return connection to pool

Key insight: Session is a UNIT OF WORK — it tracks all changes and 
writes them to the DB in one transaction at commit time.
```

**Common pitfalls:**
- **N+1 queries:** Loading 100 users, each with orders → 101 queries. Fix: `joinedload()` or `selectinload()`
- **Expired objects:** After commit, attributes are "expired." Accessing them triggers a new SELECT. Fix: `expire_on_commit=False` or eager loading.
- **Session scope:** Never share a session across requests. One session per request.
- **Connection pool exhaustion:** Forgetting to close sessions. Fix: use `async with` always.

**Industry examples:**

- **Reddit:** Hit connection pool exhaustion in production. 50 workers × 20 connections/worker = 1000 connections. PostgreSQL limit: 500. Solution: PgBouncer (connection pooler) between app and DB. Workers connect to PgBouncer (cheap), PgBouncer maintains 100 real connections to PostgreSQL.

- **Instagram:** The N+1 problem was their #1 performance issue. They built `django-batch-requests` to automatically batch multiple queries. A single API response that triggered 200 queries was reduced to 3.

- **Notion:** Used SQLAlchemy with async support for their workspace service. Key learning: they accidentally mixed sync and async sessions in the same request → deadlocks. Rule: NEVER mix sync and async SQLAlchemy in the same codebase.

- **Sentry:** Open-source error tracking. Their PostgreSQL database handles 100K+ inserts/second. Key optimization: bulk inserts with `session.execute(insert(Event), list_of_dicts)` instead of individual `session.add()` calls. 50x faster for batch operations.

### 10.1 Async Engine and Session

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, select, func
from datetime import datetime
from uuid import UUID, uuid4

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,     # Test connections before use
    pool_recycle=3600,       # Recycle connections after 1 hour
    echo=False,
)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

class UserModel(TimestampMixin, Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    
    orders: Mapped[list["OrderModel"]] = relationship(back_populates="user", lazy="selectin")

class OrderModel(TimestampMixin, Base):
    __tablename__ = "orders"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    total: Mapped[float]
    status: Mapped[str] = mapped_column(String(20), default="pending")
    
    user: Mapped["UserModel"] = relationship(back_populates="orders")
```

### 10.2 Query Patterns

```python
from sqlalchemy import select, func, and_, or_, case, text
from sqlalchemy.orm import selectinload, joinedload

async def complex_queries(session: AsyncSession):
    # Eager loading — avoid N+1
    stmt = (
        select(UserModel)
        .options(selectinload(UserModel.orders))
        .where(UserModel.is_active == True)
        .order_by(UserModel.created_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    # Aggregation
    stmt = (
        select(
            UserModel.id,
            UserModel.name,
            func.count(OrderModel.id).label("order_count"),
            func.sum(OrderModel.total).label("total_spent"),
        )
        .join(OrderModel, UserModel.id == OrderModel.user_id)
        .group_by(UserModel.id)
        .having(func.count(OrderModel.id) > 5)
        .order_by(func.sum(OrderModel.total).desc())
    )
    result = await session.execute(stmt)
    top_customers = result.all()
    
    # Subquery
    active_orders_subquery = (
        select(OrderModel.user_id)
        .where(OrderModel.status == "active")
        .group_by(OrderModel.user_id)
        .having(func.count() > 3)
        .subquery()
    )
    
    stmt = (
        select(UserModel)
        .where(UserModel.id.in_(select(active_orders_subquery.c.user_id)))
    )
    
    # Window function
    stmt = (
        select(
            OrderModel.id,
            OrderModel.total,
            func.row_number().over(
                partition_by=OrderModel.user_id,
                order_by=OrderModel.total.desc()
            ).label("rank")
        )
    )
```

### 10.3 Alembic Migrations

```python
# alembic.ini → sqlalchemy.url = postgresql+asyncpg://...

# env.py for async
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    engine = create_async_engine(config.get_main_option("sqlalchemy.url"))
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

# Migration best practices:
# 1. Always make migrations reversible (include downgrade)
# 2. Never modify a migration that's been applied to production
# 3. Add indexes concurrently for large tables
# 4. Use batch operations for data migrations

# Example migration with zero-downtime index creation
"""
def upgrade():
    # Add column as nullable first
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    
    # Create index concurrently (PostgreSQL-specific, no lock)
    op.execute(
        "CREATE INDEX CONCURRENTLY ix_users_phone ON users (phone)"
    )

def downgrade():
    op.drop_index('ix_users_phone')
    op.drop_column('users', 'phone')
"""
```

### 10.4 Connection Pool Management

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
import logging

# Production pool configuration
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    
    # Pool sizing
    pool_size=20,          # Maintained connections
    max_overflow=10,       # Extra connections under load (total max: 30)
    pool_timeout=30,       # Seconds to wait for available connection
    pool_recycle=1800,     # Recycle connections every 30 minutes
    pool_pre_ping=True,    # Validate connections before checkout
    
    # For serverless (Lambda): disable pooling
    # poolclass=NullPool,
    
    # Query logging
    echo=False,
    echo_pool="debug",     # Log pool checkout/checkin
)

# Monitor pool health
@app.get("/health/db")
async def db_health():
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
```

---

## 11. Event-Driven Architecture

#### The Theory — From Request-Response to Events

**Traditional (synchronous, coupled):**
```
User places order:
  order_service.create_order()      ← creates order
  payment_service.charge()          ← charges payment
  inventory_service.reserve()       ← reserves items
  email_service.send_confirmation() ← sends email
  analytics_service.track()         ← logs analytics

Problems:
  - If email service is down → entire order fails (fragile)
  - Adding new side effects → modify order_service code (coupled)
  - Order takes 2 seconds (sum of all calls) → slow UX
```

**Event-Driven (asynchronous, decoupled):**
```
User places order:
  order_service.create_order()                   ← creates order (50ms)
  event_bus.publish(OrderCreatedEvent(order_id)) ← fire and forget (1ms)
  → DONE. User sees "Order placed!" immediately.

Behind the scenes (async workers):
  payment_worker    → hears OrderCreated → charges payment
  inventory_worker  → hears OrderCreated → reserves items
  email_worker      → hears OrderCreated → sends confirmation
  analytics_worker  → hears OrderCreated → tracks event

Benefits:
  - Email service down? Order still succeeds. Email retries later.
  - New requirement (send SMS)? Just add new subscriber. Zero changes to order_service.
  - User response time: 51ms instead of 2000ms.
```

**Event types and their purposes:**

| Event Type | Produced By | Consumed By | Example |
|---|---|---|---|
| Domain Event | Business logic | Same service (side effects) | `UserRegistered` → send welcome email |
| Integration Event | Service boundary | Other microservices | `OrderPlaced` → notify warehouse |
| System Event | Infrastructure | Monitoring/alerting | `HighMemoryUsage` → page on-call |

**Message brokers for Python:**
- **Redis Pub/Sub:** Simple, in-memory, no persistence. Good for: real-time notifications.
- **Kafka:** Durable, ordered, replayable. Good for: critical business events, audit logs.
- **RabbitMQ:** Flexible routing, acknowledgments. Good for: task queues, complex routing.
- **SQS/SNS (AWS):** Managed, scalable. Good for: cloud-native, no infrastructure to manage.

**Industry examples:**

- **Uber:** 1 trillion+ Kafka messages per day. Every ride event (request, driver accept, pickup, dropoff, payment) is an event. 50+ services consume these events for different purposes (pricing, fraud detection, analytics, driver payments).

- **LinkedIn:** Kafka was literally invented at LinkedIn. Every user action (page view, click, message, job application) is an event processed by their Python recommendation engine.

- **Stripe:** Uses event sourcing for payment state machines. Events: `payment_intent.created`, `payment_intent.succeeded`, `charge.refunded`. Their webhook system sends these events to merchants — this IS the API (event-driven, not polling).

- **Shopify:** Event-driven inventory management. When an order is placed → event → inventory service decrements stock → if stock < threshold → event → supplier notification service orders more. All decoupled.

- **Netflix:** Their entire data pipeline is event-driven. User clicks play → event → recommendation service updates model → content delivery service pre-caches related content → analytics service tracks engagement. Each service only knows about events, not about other services.

### 11.1 Domain Events

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Callable, Any
from collections import defaultdict
import asyncio

@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    total: float = 0.0
    items: tuple = ()

@dataclass(frozen=True)
class PaymentProcessed(DomainEvent):
    order_id: UUID = field(default_factory=uuid4)
    amount: float = 0.0
    transaction_id: str = ""

class EventBus:
    """In-process event bus for domain events."""
    
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = defaultdict(list)
    
    def subscribe(self, event_type: type, handler: Callable):
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: DomainEvent):
        handlers = self._handlers.get(type(event), [])
        await asyncio.gather(
            *(handler(event) for handler in handlers),
            return_exceptions=True,
        )

# Event handlers
class NotificationHandler:
    async def on_order_placed(self, event: OrderPlaced):
        await send_email(event.user_id, f"Order {event.order_id} confirmed!")
    
    async def on_payment_processed(self, event: PaymentProcessed):
        await send_push(f"Payment of ${event.amount} received")

class InventoryHandler:
    async def on_order_placed(self, event: OrderPlaced):
        for item in event.items:
            await reserve_stock(item.product_id, item.quantity)

# Wiring
event_bus = EventBus()
notifications = NotificationHandler()
inventory = InventoryHandler()

event_bus.subscribe(OrderPlaced, notifications.on_order_placed)
event_bus.subscribe(OrderPlaced, inventory.on_order_placed)
event_bus.subscribe(PaymentProcessed, notifications.on_payment_processed)
```

### 11.2 Kafka Producer/Consumer

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from pydantic import BaseModel
import json
from typing import AsyncIterator

class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "my-service"
    auto_offset_reset: str = "earliest"

class EventPublisher:
    """Produces domain events to Kafka topics."""
    
    def __init__(self, config: KafkaConfig):
        self._producer: AIOKafkaProducer | None = None
        self._config = config
    
    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
            acks='all',                    # Wait for all replicas
            enable_idempotence=True,       # Exactly-once semantics
            max_batch_size=16384,
            linger_ms=10,                  # Batch for 10ms before sending
        )
        await self._producer.start()
    
    async def publish(self, topic: str, event: DomainEvent, key: str | None = None):
        payload = {
            "event_type": type(event).__name__,
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
            "data": {k: v for k, v in event.__dict__.items() 
                    if k not in ('event_id', 'occurred_at')},
        }
        await self._producer.send(topic, value=payload, key=key)
    
    async def stop(self):
        if self._producer:
            await self._producer.stop()

class EventConsumer:
    """Consumes events from Kafka with at-least-once delivery."""
    
    def __init__(self, config: KafkaConfig, topics: list[str]):
        self._config = config
        self._topics = topics
        self._consumer: AIOKafkaConsumer | None = None
    
    async def start(self):
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._config.bootstrap_servers,
            group_id=self._config.group_id,
            auto_offset_reset=self._config.auto_offset_reset,
            enable_auto_commit=False,      # Manual commit for at-least-once
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        await self._consumer.start()
    
    async def consume(self) -> AsyncIterator[dict]:
        async for msg in self._consumer:
            try:
                yield msg.value
                await self._consumer.commit()
            except Exception as e:
                # Don't commit — message will be redelivered
                logger.error("Failed to process message", error=str(e))
    
    async def stop(self):
        if self._consumer:
            await self._consumer.stop()
```

### 11.3 Outbox Pattern (Transactional Messaging)

```python
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import json

class OutboxMessage(Base):
    """Outbox table — events stored atomically with domain changes."""
    __tablename__ = "outbox_messages"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aggregate_type: Mapped[str] = mapped_column(String(100))
    aggregate_id: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    published: Mapped[bool] = mapped_column(default=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

class OutboxPublisher:
    """Polls outbox table and publishes to message broker."""
    
    def __init__(self, session_factory, kafka_producer: EventPublisher):
        self._session_factory = session_factory
        self._producer = kafka_producer
    
    async def publish_pending(self, batch_size: int = 100):
        async with self._session_factory() as session:
            # SELECT FOR UPDATE SKIP LOCKED — allows parallel publishers
            stmt = (
                select(OutboxMessage)
                .where(OutboxMessage.published == False)
                .order_by(OutboxMessage.created_at)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            for msg in messages:
                await self._producer.publish(
                    topic=f"events.{msg.aggregate_type}",
                    event=json.loads(msg.payload),
                    key=msg.aggregate_id,
                )
                msg.published = True
                msg.published_at = datetime.utcnow()
            
            await session.commit()
    
    async def run_forever(self, poll_interval: float = 1.0):
        while True:
            await self.publish_pending()
            await asyncio.sleep(poll_interval)

# Usage — atomic write: save entity + outbox message in same transaction
async def place_order(session: AsyncSession, order: Order):
    session.add(order_to_model(order))
    
    outbox_msg = OutboxMessage(
        aggregate_type="order",
        aggregate_id=str(order.id),
        event_type="OrderPlaced",
        payload=json.dumps({
            "order_id": str(order.id),
            "user_id": str(order.user_id),
            "total": order.total,
        }),
    )
    session.add(outbox_msg)
    
    await session.commit()
    # Event will be published by OutboxPublisher — guaranteed delivery
```

---

## 12. Distributed Systems Patterns

#### The Theory — Building High-Throughput Scalable Systems

This is the core knowledge that separates a senior engineer from a staff engineer. Every production system at scale must solve these fundamental challenges:

**The 5 pillars of high-throughput systems:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                   HIGH-THROUGHPUT SYSTEM DESIGN                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. HORIZONTAL SCALING                                              │
│     "Add more machines, not bigger machines"                        │
│     - Stateless services (any instance handles any request)         │
│     - Load balancer distributes traffic (round-robin, least-conn)  │
│     - Auto-scaling based on CPU/memory/queue depth                 │
│     - Session affinity only when absolutely necessary              │
│                                                                     │
│  2. ASYNCHRONOUS PROCESSING                                        │
│     "Don't make the user wait for non-critical work"               │
│     - Message queues (Kafka, RabbitMQ, SQS)                       │
│     - Background workers consume jobs at their own pace            │
│     - Request: accept fast, process later (202 Accepted)           │
│     - Decouples producers from consumers                          │
│                                                                     │
│  3. CACHING                                                        │
│     "The fastest request is one you don't process"                 │
│     - L1: In-process cache (dict, lru_cache) — ns latency         │
│     - L2: Redis/Memcached — 1ms latency                          │
│     - L3: CDN — serves from edge, 10ms globally                   │
│     - Cache invalidation is the hard problem                       │
│                                                                     │
│  4. DATA PARTITIONING                                              │
│     "No single database can hold everything"                       │
│     - Sharding: split data across multiple DBs                    │
│     - Partitioning: split table by range/hash                     │
│     - Read replicas: separate read/write paths                    │
│     - CQRS: different models for read vs write                    │
│                                                                     │
│  5. BACKPRESSURE & RESILIENCE                                      │
│     "Protect yourself from being overwhelmed"                      │
│     - Rate limiting: cap requests per user/IP/endpoint            │
│     - Circuit breaker: stop calling failed services               │
│     - Bulkhead: isolate failures (one bad service ≠ total crash)  │
│     - Timeout + retry with exponential backoff                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Scaling a Python service from 100 to 100,000 RPS:**

```
Stage 1: Single server (100 RPS)
┌───────────────────────────────┐
│  Uvicorn (1 worker, asyncio)  │ → PostgreSQL
└───────────────────────────────┘
Problem: CPU-bound requests block the event loop.

Stage 2: Multi-worker (500 RPS)  
┌───────────────────────────────┐
│  Uvicorn (4 workers = 4 processes) │ → PostgreSQL
└───────────────────────────────┘
Problem: Single DB is the bottleneck (connection limit ~100).

Stage 3: Connection pooling + read replicas (2,000 RPS)
┌───────────────────────────────┐
│  Uvicorn (4 workers)          │ → PgBouncer → Primary (writes)
│                               │            → Replica 1 (reads)
│                               │            → Replica 2 (reads)
└───────────────────────────────┘
Problem: Single server's CPU/memory is maxed.

Stage 4: Horizontal scaling + load balancer (10,000 RPS)
                  ┌─── Server 1 (4 workers) ──┐
Load Balancer ────┼─── Server 2 (4 workers) ──┼─→ DB cluster
(Nginx/ALB)       └─── Server 3 (4 workers) ──┘
                  + Redis (sessions, cache)
                  + Auto-scaling group
Problem: Some requests take 5s (ML inference, reports).

Stage 5: Async processing + queues (50,000 RPS)
                  ┌─── API Server (fast, <50ms) ──→ Redis cache
Load Balancer ────┤                               ──→ Kafka/SQS
                  └─── API Server                 
                                                       ↓
                                              Worker Pool (heavy tasks)
                                              ├── ML inference workers
                                              ├── Report generation workers
                                              └── Notification workers
Problem: Hot spots (viral content, flash sales).

Stage 6: Full production (100,000+ RPS)
CDN (static) → API Gateway (rate limit, auth)
                    ↓
              Service Mesh (Kubernetes)
              ├── User Service (sharded by user_id)
              ├── Order Service (partitioned by date)
              ├── Search Service (Elasticsearch cluster)
              └── ML Service (GPU instances, auto-scaled)
              
              All connected via:
              - Kafka (async events)
              - Redis Cluster (cache + sessions)
              - PostgreSQL + read replicas (source of truth)
```

**Key metrics for high-throughput systems:**

| Metric | What It Tells You | Target |
|---|---|---|
| **P50 latency** | Median response time | < 50ms for API |
| **P99 latency** | Worst 1% response time | < 500ms |
| **Throughput (RPS)** | Requests per second | Depends on SLA |
| **Error rate** | % of 5xx responses | < 0.1% |
| **Saturation** | CPU/memory/disk usage | < 80% (headroom for spikes) |
| **Queue depth** | Pending async work | Should not grow continuously |

**The CAP theorem (interview essential):**

In a distributed system, you can only guarantee 2 out of 3:
- **Consistency:** Every read returns the most recent write.
- **Availability:** Every request gets a response (even if stale).
- **Partition tolerance:** System works even if network splits between nodes.

In practice, network partitions ALWAYS happen. So your real choice is:
- **CP (Consistency + Partition tolerance):** Returns error if it can't confirm latest data. (PostgreSQL, MongoDB w/ majority reads)
- **AP (Availability + Partition tolerance):** Always responds, may return stale data. (Cassandra, DynamoDB, DNS)

Most web services choose **eventual consistency** (AP) for reads and **strong consistency** (CP) for writes.

**Industry patterns for Python backends:**

| Pattern | What It Solves | Python Implementation |
|---|---|---|
| Circuit Breaker | Stop calling a dead service | `circuitbreaker` lib or custom with Redis |
| Retry with backoff | Transient failures | `tenacity` lib (exponential + jitter) |
| Bulkhead | Isolate failure domains | Separate worker pools per dependency |
| Rate Limiting | Prevent abuse, protect resources | Token bucket in Redis (`aioredis`) |
| Saga | Distributed transactions | Orchestrator pattern (shown below) |
| Idempotency | Safe retries for mutations | Idempotency key + dedup store |
| CQRS | Separate read/write scaling | Different models/DBs for queries vs commands |
| Event Sourcing | Audit trail + temporal queries | Append-only event log (Kafka/EventStore) |
| Outbox | Reliable event publishing | Same-DB transaction (see DDD guide) |
| Sidecar | Cross-cutting concerns | Envoy proxy, Dapr |

### 12.1 Saga Pattern

#### The Theory

In a monolith, you wrap multiple operations in a database transaction — if one fails, all roll back. In microservices, there's no single database transaction spanning multiple services. The **Saga pattern** replaces distributed transactions with a sequence of local transactions + compensating actions.

```
Saga: Place Order
  Step 1: Reserve Inventory  (compensation: Release Inventory)
  Step 2: Charge Payment     (compensation: Refund Payment)
  Step 3: Create Order       (compensation: Cancel Order)
  Step 4: Send Notification  (compensation: none — best effort)

If Step 3 fails:
  → Compensate Step 2: Refund Payment
  → Compensate Step 1: Release Inventory
  → Order never created — system is consistent (eventually)
```

Two styles:
- **Choreography:** Each service publishes events, next service reacts. Simple but hard to track.
- **Orchestration:** A central coordinator tells each service what to do. More control, easier debugging.

```python
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
import asyncio

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    COMPENSATED = "compensated"
    FAILED = "failed"

@dataclass
class SagaStep:
    name: str
    action: Callable
    compensation: Callable
    status: SagaStepStatus = SagaStepStatus.PENDING

class Saga:
    """Orchestrator-based saga for distributed transactions."""
    
    def __init__(self, name: str):
        self.name = name
        self._steps: list[SagaStep] = []
        self._completed: list[SagaStep] = []
    
    def add_step(self, name: str, action: Callable, compensation: Callable):
        self._steps.append(SagaStep(name=name, action=action, compensation=compensation))
        return self
    
    async def execute(self, context: dict) -> dict:
        for step in self._steps:
            try:
                result = await step.action(context)
                context[f"{step.name}_result"] = result
                step.status = SagaStepStatus.COMPLETED
                self._completed.append(step)
            except Exception as e:
                step.status = SagaStepStatus.FAILED
                await self._compensate(context)
                raise SagaExecutionError(
                    f"Saga '{self.name}' failed at step '{step.name}': {e}"
                ) from e
        
        return context
    
    async def _compensate(self, context: dict):
        for step in reversed(self._completed):
            try:
                await step.compensation(context)
                step.status = SagaStepStatus.COMPENSATED
            except Exception as e:
                logger.error(
                    "Compensation failed",
                    saga=self.name,
                    step=step.name,
                    error=str(e),
                )

# Usage: Order placement saga
async def create_order_saga(order_data: dict):
    saga = Saga("place_order")
    
    saga.add_step(
        name="reserve_inventory",
        action=lambda ctx: inventory_service.reserve(ctx["items"]),
        compensation=lambda ctx: inventory_service.release(ctx["reserve_inventory_result"]),
    )
    saga.add_step(
        name="charge_payment",
        action=lambda ctx: payment_service.charge(ctx["user_id"], ctx["total"]),
        compensation=lambda ctx: payment_service.refund(ctx["charge_payment_result"]),
    )
    saga.add_step(
        name="create_order",
        action=lambda ctx: order_service.create(ctx),
        compensation=lambda ctx: order_service.cancel(ctx["create_order_result"]),
    )
    saga.add_step(
        name="send_confirmation",
        action=lambda ctx: notification_service.send(ctx["user_id"], ctx["create_order_result"]),
        compensation=lambda ctx: None,  # No-op: notification is best-effort
    )
    
    return await saga.execute(order_data)
```

### 12.2 Idempotency

#### The Theory

**Idempotency** = calling an operation multiple times produces the same result as calling it once.

Why this matters for high-throughput systems:
- Networks are unreliable. Clients retry. Load balancers retry. If "charge $50" is retried, you must NOT charge $100.
- At 10K RPS, even 0.1% duplicate rate = 10 accidental double-charges per second.

**How it works:**
```
Client sends: POST /payments  (Header: Idempotency-Key: "abc-123")

Server logic:
  1. Check Redis: Does key "abc-123" exist?
  2. YES → return cached result (no re-processing)
  3. NO  → process payment, store result under "abc-123", return result

If client retries (network timeout, 502, etc.):
  Same key "abc-123" → returns cached result → user charged exactly once ✓
```

**HTTP methods and idempotency:**
- GET, PUT, DELETE are naturally idempotent (by HTTP spec)
- POST is NOT idempotent → needs explicit idempotency keys
- PATCH may or may not be (depends on implementation)

**Industry practice:** Stripe, PayPal, and all payment APIs require `Idempotency-Key` header for mutations.

```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

class IdempotencyStore:
    """Redis-backed idempotency key store."""
    
    def __init__(self, redis, ttl: timedelta = timedelta(hours=24)):
        self._redis = redis
        self._ttl = ttl
    
    async def check_and_set(self, key: str) -> tuple[bool, Any]:
        """Returns (is_duplicate, cached_result)."""
        cached = await self._redis.get(f"idempotency:{key}")
        if cached:
            return True, json.loads(cached)
        return False, None
    
    async def store_result(self, key: str, result: Any):
        await self._redis.setex(
            f"idempotency:{key}",
            int(self._ttl.total_seconds()),
            json.dumps(result),
        )

def idempotent(key_func: Callable = None):
    """Decorator for idempotent endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0]
            idempotency_key = request.headers.get("Idempotency-Key")
            
            if not idempotency_key:
                return await func(*args, **kwargs)
            
            store = request.app.state.idempotency_store
            is_duplicate, cached_result = await store.check_and_set(idempotency_key)
            
            if is_duplicate:
                return cached_result
            
            result = await func(*args, **kwargs)
            await store.store_result(idempotency_key, result)
            return result
        
        return wrapper
    return decorator

@app.post("/payments/")
@idempotent()
async def process_payment(request: Request, payment: PaymentRequest):
    # Even if called multiple times with same Idempotency-Key,
    # payment is processed exactly once
    return await payment_service.charge(payment)
```

### 12.3 Distributed Locking

#### The Theory

In a single process, you use `threading.Lock()`. In a distributed system (multiple servers), you need a **distributed lock** — a lock that ALL servers respect.

**Why you need it:**
```
Without distributed lock:
  Server A reads balance = $100
  Server B reads balance = $100   (race condition!)
  Server A writes balance = $100 - $80 = $20
  Server B writes balance = $100 - $80 = $20  (should have been $20 - $80 = DENIED)
  Result: User withdrew $160 from $100 account. You lost $60.
```

**How Redis-based distributed lock works (Redlock simplified):**
1. Generate unique token (UUID)
2. `SET lock_key token NX EX 30` — atomically set only if not exists, expire in 30s
3. If SET succeeded → you hold the lock
4. Do your work
5. Release: delete key ONLY if token matches (Lua script for atomicity)

**The dangers:**
- Lock expires while you're still working (solution: auto-renewal)
- Redis crashes (solution: Redlock algorithm uses multiple Redis instances)
- Process dies holding lock (solution: TTL ensures lock auto-expires)

**When to use distributed locks vs alternatives:**
| Approach | Use When | Example |
|---|---|---|
| Distributed lock | Need mutual exclusion across services | Balance deduction |
| Optimistic locking | Conflicts are rare, reads >> writes | Updating a profile |
| Database SERIALIZABLE | Need strict consistency, low throughput | Financial ledger entries |
| Event sourcing | Need audit trail + conflict resolution | Collaborative editing |

```python
import asyncio
import time
import uuid
from contextlib import asynccontextmanager

class DistributedLock:
    """Redis-based distributed lock with auto-renewal."""
    
    def __init__(self, redis, name: str, ttl: float = 30.0):
        self._redis = redis
        self._name = f"lock:{name}"
        self._ttl = ttl
        self._token = str(uuid.uuid4())
        self._renewal_task: asyncio.Task | None = None
    
    async def acquire(self, timeout: float = 10.0) -> bool:
        deadline = time.monotonic() + timeout
        
        while time.monotonic() < deadline:
            acquired = await self._redis.set(
                self._name,
                self._token,
                nx=True,           # Only set if not exists
                ex=int(self._ttl), # Expire after TTL
            )
            if acquired:
                self._renewal_task = asyncio.create_task(self._renew())
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    async def release(self):
        if self._renewal_task:
            self._renewal_task.cancel()
        
        # Atomic check-and-delete (only delete if we own the lock)
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self._redis.eval(script, 1, self._name, self._token)
    
    async def _renew(self):
        """Renew lock periodically to prevent expiration during work."""
        while True:
            await asyncio.sleep(self._ttl / 3)
            await self._redis.expire(self._name, int(self._ttl))

@asynccontextmanager
async def distributed_lock(redis, name: str, ttl: float = 30.0):
    lock = DistributedLock(redis, name, ttl)
    if not await lock.acquire():
        raise LockAcquisitionError(f"Could not acquire lock: {name}")
    try:
        yield lock
    finally:
        await lock.release()

# Usage
async def process_withdrawal(user_id: str, amount: float):
    async with distributed_lock(redis, f"user:{user_id}:balance"):
        balance = await get_balance(user_id)
        if balance < amount:
            raise InsufficientFunds()
        await set_balance(user_id, balance - amount)
```

### 12.4 Back-Pressure

#### The Theory

**Backpressure** = when a system is overwhelmed, it signals upstream to SLOW DOWN instead of crashing.

Without backpressure:
```
Producer (10,000 req/s) → Consumer (5,000 req/s capacity)
  After 1 second: 5,000 items backed up in memory
  After 10 seconds: 50,000 items → OOM crash → total outage
```

With backpressure:
```
Producer (10,000 req/s) → Queue (max 1000) → Consumer (5,000 req/s)
  Queue reaches 800 (high watermark) → signal producer to PAUSE
  Queue drops to 300 (low watermark) → signal producer to RESUME
  Result: Producer slows down. No crash. Some requests get 503 "try later".
  Better: lose a few requests than crash and lose ALL requests.
```

**Backpressure strategies (from gentlest to harshest):**
1. **Slow down:** Producer blocks until space is available (internal systems)
2. **Shed load:** Return 503 immediately, client retries later (user-facing APIs)
3. **Degrade quality:** Skip non-critical work (skip analytics, use cached responses)
4. **Rate limit:** Hard cap on requests per second (global protection)
5. **Circuit break:** Stop calling failed dependency entirely (cascade prevention)

**Industry examples:**
- Kafka: Consumer lag causes partition rebalancing (automatic backpressure)
- TCP: Window-based flow control IS backpressure
- Kubernetes HPA: Pod scaling IS a form of backpressure relief
- Node.js streams: `pipe()` with `highWaterMark` implements backpressure

```python
import asyncio
from typing import AsyncIterator

class BackPressureQueue:
    """Queue with back-pressure — producers slow down when consumers can't keep up."""
    
    def __init__(self, maxsize: int, high_watermark: float = 0.8, low_watermark: float = 0.3):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._high = int(maxsize * high_watermark)
        self._low = int(maxsize * low_watermark)
        self._pressure_event = asyncio.Event()
        self._pressure_event.set()  # Initially no pressure
    
    @property
    def is_under_pressure(self) -> bool:
        return self._queue.qsize() >= self._high
    
    async def put(self, item):
        if self._queue.qsize() >= self._high:
            self._pressure_event.clear()
            # Block producer until consumer catches up
            await self._pressure_event.wait()
        await self._queue.put(item)
    
    async def get(self):
        item = await self._queue.get()
        if self._queue.qsize() <= self._low:
            self._pressure_event.set()  # Release producers
        return item

# HTTP back-pressure with semaphore
class ThrottledClient:
    """HTTP client with concurrency limit (back-pressure at network level)."""
    
    def __init__(self, max_concurrent: int = 50):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client = httpx.AsyncClient()
    
    async def get(self, url: str) -> httpx.Response:
        async with self._semaphore:
            return await self._client.get(url)
    
    async def close(self):
        await self._client.aclose()
```

### 12.5 Circuit Breaker

#### The Theory

**Circuit Breaker** = if a dependency is failing, STOP calling it (instead of wasting time waiting for timeouts).

Named after electrical circuit breakers: when current is too high, the breaker "trips" and cuts the circuit to prevent fire.

```
State Machine:
                    ┌─────────────────────────────────┐
                    │                                   │
                    ▼                                   │ (all attempts in half-open succeed)
            ┌──────────────┐    (failures > threshold)  │
            │    CLOSED    │ ──────────────────────┐   │
            │ (normal flow)│                       │   │
            └──────────────┘                       ▼   │
                    ▲                      ┌────────────────┐
                    │                      │     OPEN       │
                    │                      │ (reject all)   │
                    │                      └───────┬────────┘
                    │                              │
                    │         (timeout expires)    │
                    │                              ▼
                    │                      ┌────────────────┐
                    └──────────────────────│  HALF-OPEN     │
                      (attempt succeeds)   │ (try one req)  │
                                          └────────────────┘
                                                  │
                                          (attempt fails)
                                                  │
                                                  ▼
                                          Back to OPEN
```

**Without circuit breaker:**
- Downstream service is down
- Every request waits 30s for timeout → thread pool exhausted
- Your service goes down too → cascading failure → entire system down

**With circuit breaker:**
- After 5 failures in 60s → circuit OPENS
- All requests immediately get error (no waiting) → fast fail
- After 30s → try ONE request (half-open)
- If it works → circuit CLOSES (service is back)
- If it fails → circuit stays OPEN (wait another 30s)

**Key parameters:**
- `failure_threshold`: How many failures before opening (typically 5-10)
- `recovery_timeout`: How long to wait before trying again (typically 30-60s)
- `success_threshold`: How many successes in half-open before closing (typically 2-3)

```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Prevents cascading failures by failing fast when a dependency is down."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpen(
                f"Circuit is OPEN. Will retry after {self._recovery_timeout}s"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN

# Usage with multiple services
class ResilientServiceClient:
    """Client that protects each downstream service with its own circuit breaker."""
    
    def __init__(self):
        self._breakers = {
            "payment": CircuitBreaker(failure_threshold=3, recovery_timeout=60),
            "inventory": CircuitBreaker(failure_threshold=5, recovery_timeout=30),
            "notification": CircuitBreaker(failure_threshold=10, recovery_timeout=10),
        }
    
    async def charge_payment(self, amount: float):
        return await self._breakers["payment"].call(
            payment_api.charge, amount
        )
```

### 12.6 Rate Limiting (Token Bucket Algorithm)

#### The Theory

**Rate limiting** = control how many requests a user/IP/service can make in a time window.

**Why it's critical for high-throughput systems:**
1. Prevents abuse (one user can't DoS your service)
2. Protects downstream services (your DB can handle 10K QPS, not 100K)
3. Fair resource sharing (all users get reasonable access)
4. Cost control (expensive operations like LLM calls need hard limits)

**Common algorithms:**

| Algorithm | How It Works | Best For |
|---|---|---|
| **Token Bucket** | Tokens refill at fixed rate. Each request takes a token. | Smooth rate + burst allowed |
| **Sliding Window** | Count requests in last N seconds. | Simple per-user limits |
| **Leaky Bucket** | Fixed output rate regardless of input. | Constant-rate processing |
| **Fixed Window** | Count requests per minute/hour. | Simple but has boundary spike problem |

**Token Bucket — most popular (used by AWS, Stripe, OpenAI):**
```
Bucket capacity: 100 tokens
Refill rate: 10 tokens/second

Time 0: Bucket has 100 tokens
  → Burst of 100 requests arrives → all pass (100 tokens consumed)
  → Bucket now at 0 tokens

Time 1s: 10 tokens refilled
  → 10 more requests can pass

Time 10s: Bucket refilled to 100
  → Ready for another burst

This allows: steady 10 req/s AND occasional bursts up to 100.
```

```python
import time
import asyncio
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """Token bucket rate limiter — allows bursts while maintaining average rate."""
    
    capacity: int
    refill_rate: float  # tokens per second
    _tokens: float = 0
    _last_refill: float = 0
    
    def __post_init__(self):
        self._tokens = float(self.capacity)
        self._last_refill = time.monotonic()
    
    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.refill_rate,
        )
        self._last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rate limited."""
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

class DistributedRateLimiter:
    """Redis-based rate limiter for multi-server deployments.
    
    Uses sliding window counter for fairness across time boundaries.
    """
    
    def __init__(self, redis, requests_per_minute: int = 60):
        self._redis = redis
        self._limit = requests_per_minute
        self._window = 60  # seconds
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request from identifier is within rate limit.
        
        Uses Redis MULTI/EXEC for atomic sliding window:
        1. Remove entries older than window
        2. Count remaining entries
        3. If under limit, add current timestamp
        """
        key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - self._window
        
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zcard(key)                                # Count current entries
        pipe.zadd(key, {str(now): now})               # Add this request
        pipe.expire(key, self._window)                 # Auto-cleanup
        
        results = await pipe.execute()
        request_count = results[1]
        
        if request_count >= self._limit:
            await self._redis.zrem(key, str(now))  # Remove the one we just added
            return False
        
        return True

# Usage as FastAPI middleware
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        limiter = request.app.state.rate_limiter
        identifier = request.client.host  # or user_id from JWT
        
        if not await limiter.is_allowed(identifier):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )
        
        return await call_next(request)
```

### 12.7 Connection Pooling & Resource Management

#### The Theory

**Connection pooling** = reuse database/HTTP connections instead of creating new ones per request.

Why this matters at scale:
```
Without pooling (10,000 RPS):
  Each request: open TCP → TLS handshake → authenticate → query → close
  Time per connection: ~20ms (just for setup!)
  Connections open simultaneously: 10,000
  PostgreSQL max_connections (default): 100
  Result: "too many connections" error → service down

With pooling (10,000 RPS):
  Pool of 50 connections, reused across requests
  Request: borrow connection → query (2ms) → return connection
  Actual concurrent DB calls: 50 (well within limit)
  Result: Handles 10K RPS with 50 connections ✓
```

**The connection pool lifecycle:**
```
Application startup:
  → Create pool with min=10, max=50 connections
  → Pre-warm 10 connections (ready immediately)

Request arrives:
  → Borrow connection from pool (wait if all busy)
  → Execute query
  → Return connection to pool (NOT closed, just returned)

If pool is exhausted:
  → Wait up to `pool_timeout` seconds
  → If still no connection → raise error (backpressure!)

Application shutdown:
  → Close all connections gracefully
```

**Industry practice for PostgreSQL + Python:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=20,           # Steady-state connections
    max_overflow=30,        # Extra connections under load (total max: 50)
    pool_timeout=10,        # Wait 10s for connection, then error
    pool_recycle=3600,      # Recycle connections every hour (prevents stale)
    pool_pre_ping=True,     # Verify connection is alive before using
    echo=False,             # No SQL logging in production
)
```

**Rule of thumb:** `pool_size = (num_workers * 2) + 1` for CPU-bound, or `num_workers * 5` for I/O-bound.

---

## 13. Observability & Telemetry

#### The Theory — You Can't Scale What You Can't Measure

At scale, "why is it slow?" is the hardest question. Without proper observability, debugging a performance issue across 50 services with 100K RPS is impossible. You're flying blind.

**The Three Pillars of Observability:**

```
┌──────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY = 3 PILLARS                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. LOGS (What happened?)                                        │
│     - Structured JSON, not printf-style strings                  │
│     - Correlated by request_id (trace across services)           │
│     - Shipped to central store (ELK, Datadog, CloudWatch)        │
│     - NEVER log secrets, PII, or full request bodies             │
│                                                                  │
│  2. METRICS (How is the system performing?)                      │
│     - Counters: total requests, errors, cache hits               │
│     - Gauges: current connections, queue depth, memory usage     │
│     - Histograms: latency distribution (p50, p95, p99)           │
│     - RED method: Rate, Errors, Duration                         │
│     - USE method: Utilization, Saturation, Errors (for infra)    │
│                                                                  │
│  3. TRACES (Where did time go?)                                  │
│     - Distributed tracing follows a request across services      │
│     - Span = one unit of work (DB query, HTTP call, function)    │
│     - Trace = tree of spans showing the full request lifecycle   │
│     - Critical for: "why is this endpoint slow for 1% of users?" │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Why all three are needed:**
- Metrics tell you "P99 latency spiked to 5s at 3:42 PM"
- Traces tell you "the spike is in the payment service, specifically the fraud check"
- Logs tell you "fraud service was retrying because third-party API returned 503"

**Key metrics for high-throughput Python services (the RED method):**
| Metric | Formula | Alert Threshold |
|---|---|---|
| Request Rate | requests/second per endpoint | Sudden drop > 50% |
| Error Rate | 5xx responses / total responses | > 1% |
| Duration (P50) | Median response time | > 100ms |
| Duration (P99) | 99th percentile response time | > 1s |
| Saturation | Active connections / max pool size | > 80% |

**Industry tool choices:**
| Tool | What It Does | When to Use |
|---|---|---|
| Prometheus + Grafana | Metrics collection + visualization | Open-source, self-hosted |
| Datadog | All-in-one (logs, metrics, traces, APM) | Enterprise, managed |
| OpenTelemetry | Vendor-neutral instrumentation | Always (future-proof) |
| Sentry | Error tracking + performance | Application errors |
| PagerDuty/OpsGenie | Alert routing + on-call | Incident management |

**Industry observability examples:**

- **Uber:** Distributed tracing saved them during a 2-hour outage. A single trace showed: API gateway → user service → payment service → **bank API timeout (30s)**. Without tracing, they would have searched all 4000 services manually.

- **Netflix:** Their approach: "If it moves, measure it." Every Python service exports 100+ metrics automatically. They alert on the RATE OF CHANGE (sudden spike), not absolute values. A gradual increase from 50ms to 200ms is fine. A jump from 50ms to 500ms in 1 minute triggers an alert.

- **Stripe:** Structured logging is mandatory. Every log line includes: `request_id`, `user_id`, `merchant_id`, `amount`. When something goes wrong, they can reconstruct the ENTIRE lifecycle of a payment by filtering on `request_id`.

- **Datadog (their own service):** They process 100 billion+ events per day. Their Python agent uses OpenTelemetry for instrumentation. Key insight: sampling at 1% for normal requests, 100% for errors. This keeps cost manageable while catching every problem.

- **Cloudflare:** Discovered a memory leak via Prometheus metrics. Memory gauge showed a slow linear increase over 3 days. Root cause: a Python dict used as a cache that was never pruned. Without the metric, they would only notice at OOM crash.

### 13.1 Structured Logging with structlog

```python
import structlog
from structlog.contextvars import bind_contextvars, unbind_contextvars

# Configuration
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        # JSON in production, colored in dev
        structlog.dev.ConsoleRenderer() if DEBUG else structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

# Usage — structured context
async def process_order(order_id: str, user_id: str):
    # Bind context for all logs in this call chain
    bind_contextvars(order_id=order_id, user_id=user_id)
    
    logger.info("processing_order", total=order.total)
    
    try:
        result = await charge_payment(order)
        logger.info("payment_charged", transaction_id=result.tx_id)
    except PaymentError as e:
        logger.error("payment_failed", error=str(e), retry_count=0)
        raise
    finally:
        unbind_contextvars("order_id", "user_id")

# Output (JSON):
# {"event": "processing_order", "order_id": "abc-123", "user_id": "usr-456", 
#  "total": 99.99, "level": "info", "timestamp": "2025-01-15T10:30:00Z"}
```

### 13.2 OpenTelemetry Integration

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app: FastAPI, service_name: str):
    # Traces
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENV", "development"),
    }))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
    )
    trace.set_tracer_provider(provider)
    
    # Auto-instrument frameworks
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()
    
    # Custom metrics
    meter = metrics.get_meter(service_name)
    
    return meter

# Custom spans for business logic
tracer = trace.get_tracer(__name__)

async def process_complex_order(order: Order):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", str(order.id))
        span.set_attribute("order.total", order.total)
        span.set_attribute("order.item_count", len(order.items))
        
        with tracer.start_as_current_span("validate_inventory"):
            await validate_inventory(order.items)
        
        with tracer.start_as_current_span("charge_payment"):
            result = await charge_payment(order)
            span.set_attribute("payment.transaction_id", result.tx_id)
        
        with tracer.start_as_current_span("fulfill_order"):
            await fulfill(order)
        
        span.set_status(trace.StatusCode.OK)

# Custom metrics
meter = metrics.get_meter("order-service")

order_counter = meter.create_counter(
    "orders.created",
    description="Number of orders created",
)

order_duration = meter.create_histogram(
    "orders.processing_duration_ms",
    description="Time to process an order",
    unit="ms",
)

async def create_order(order_data: dict):
    start = time.perf_counter()
    
    order = await process_order(order_data)
    
    duration_ms = (time.perf_counter() - start) * 1000
    order_counter.add(1, {"status": "success", "region": "us-east"})
    order_duration.record(duration_ms, {"order_type": order.type})
    
    return order
```

### 13.3 Health Checks

```python
from fastapi import FastAPI, Response
from pydantic import BaseModel
from enum import Enum
import asyncio

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ComponentHealth(BaseModel):
    name: str
    status: HealthStatus
    latency_ms: float | None = None
    details: str | None = None

class HealthResponse(BaseModel):
    status: HealthStatus
    components: list[ComponentHealth]
    version: str

async def check_database() -> ComponentHealth:
    try:
        start = time.perf_counter()
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        return ComponentHealth(name="database", status=HealthStatus.HEALTHY, latency_ms=latency)
    except Exception as e:
        return ComponentHealth(name="database", status=HealthStatus.UNHEALTHY, details=str(e))

async def check_redis() -> ComponentHealth:
    try:
        start = time.perf_counter()
        await redis.ping()
        latency = (time.perf_counter() - start) * 1000
        return ComponentHealth(name="redis", status=HealthStatus.HEALTHY, latency_ms=latency)
    except Exception as e:
        return ComponentHealth(name="redis", status=HealthStatus.UNHEALTHY, details=str(e))

async def check_kafka() -> ComponentHealth:
    try:
        # Check if producer is connected
        if kafka_producer._producer and kafka_producer._producer._sender.is_alive():
            return ComponentHealth(name="kafka", status=HealthStatus.HEALTHY)
        return ComponentHealth(name="kafka", status=HealthStatus.DEGRADED, details="reconnecting")
    except Exception as e:
        return ComponentHealth(name="kafka", status=HealthStatus.UNHEALTHY, details=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_kafka(),
    )
    
    overall = HealthStatus.HEALTHY
    for check in checks:
        if check.status == HealthStatus.UNHEALTHY:
            overall = HealthStatus.UNHEALTHY
            break
        elif check.status == HealthStatus.DEGRADED:
            overall = HealthStatus.DEGRADED
    
    if overall != HealthStatus.HEALTHY:
        response.status_code = 503
    
    return HealthResponse(
        status=overall,
        components=checks,
        version=app.version,
    )

# Kubernetes probes
@app.get("/health/live")   # Liveness: is process alive?
async def liveness():
    return {"status": "ok"}

@app.get("/health/ready")  # Readiness: can it handle traffic?
async def readiness(response: Response):
    db_ok = await check_database()
    if db_ok.status == HealthStatus.UNHEALTHY:
        response.status_code = 503
        return {"status": "not ready", "reason": "database unavailable"}
    return {"status": "ready"}
```

---

## 14. Testing at Scale

#### The Theory — The Testing Pyramid and Why It Matters

**The testing pyramid (from bottom to top):**

```
         /\          E2E Tests (few, slow, expensive, high confidence)
        /  \         - Full system running, real browser/HTTP
       /    \        - Break often, hard to debug
      /──────\       
     / Integr-\      Integration Tests (moderate amount)
    /  ation   \     - Real DB, real Redis, Docker containers
   /────────────\    - Test that components work TOGETHER
  /              \   
 /   Unit Tests   \  Unit Tests (many, fast, cheap, specific)
/──────────────────\ - Pure functions, domain logic, no I/O
                     - Run in milliseconds, catch specific bugs
```

**How many tests at each level (industry rule of thumb):**
- Unit: 70% of tests (run in <5s total, catch logic bugs)
- Integration: 20% of tests (run in <2min, catch wiring bugs)
- E2E: 10% of tests (run in <10min, catch deployment bugs)

**What to test at each level:**

| Level | What to Test | What NOT to Test | Speed |
|---|---|---|---|
| Unit | Domain logic, validators, transforms | DB, HTTP, file I/O | 1000s per second |
| Integration | API endpoints, DB queries, caching | UI, external APIs | 10s per second |
| E2E | Critical user journeys (login, purchase) | Every edge case | 1 per 10 seconds |

**Key testing principles for large codebases:**
1. **Tests should be deterministic** — same input always gives same output. No random, no time.time().
2. **Tests should be independent** — order doesn't matter, no shared state between tests.
3. **Fast feedback loop** — unit tests run on every save, integration on every commit, E2E on every PR.
4. **Test behavior, not implementation** — test WHAT it does, not HOW it does it internally.
5. **If CI is slow, parallelize** — `pytest-xdist` runs tests across CPU cores.

**Industry testing practices:**

- **Stripe:** 90% code coverage enforced. Every PR must include tests. Their CI runs 50,000+ tests in parallel. Key philosophy: "If it's not tested, it's broken."

- **Netflix:** Uses "chaos engineering" as testing — intentionally killing production services to verify resilience. Their Chaos Monkey randomly terminates instances. Their Python services must handle this gracefully.

- **Spotify:** Contract testing between microservices. Each service publishes a "contract" (expected request/response format). If service A changes its API, service B's contract tests fail BEFORE deployment. Uses `pact-python`.

- **GitHub:** Mutation testing for critical paths. A tool mutates your code (changes `>` to `>=`, removes lines) and checks if tests catch it. If tests pass with mutated code → you have a coverage gap.

- **Airbnb:** Property-based testing (Hypothesis) for their pricing algorithm. Instead of testing specific prices, they test PROPERTIES: "price should always be positive," "discount can never exceed base price." This catches edge cases humans wouldn't think to test.

- **Instagram:** Integration tests use Docker Compose to spin up PostgreSQL, Redis, and Memcached. Tests run against real services, not mocks. This catches "works with mock, fails in production" bugs.

### 14.1 Test Architecture

```
tests/
├── unit/                    # Fast, isolated, no I/O
│   ├── domain/
│   │   ├── test_entities.py
│   │   └── test_services.py
│   └── conftest.py
├── integration/             # Real DB, real Redis, Docker
│   ├── test_repositories.py
│   ├── test_api.py
│   └── conftest.py
├── e2e/                     # Full system tests
│   └── test_workflows.py
├── conftest.py              # Shared fixtures
└── factories.py             # Test data factories
```

### 14.2 Fixtures and Factories

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from polyfactory.factories.pydantic_factory import ModelFactory

# Async test database
@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5433/test_db",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db_session] = lambda: db_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    app.dependency_overrides.clear()

# Polyfactory for test data generation
class UserFactory(ModelFactory):
    __model__ = UserCreate
    
    email = "test_{__sequence__}@example.com"
    name = "Test User"

class OrderFactory(ModelFactory):
    __model__ = OrderCreate

# Usage in tests
@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = UserFactory.build()
    
    response = await client.post("/api/v1/users/", json=user_data.model_dump())
    
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == user_data.email
    assert "id" in body
```

### 14.3 Mocking External Services

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from respx import MockRouter
import respx

# Mock HTTP calls with respx
@pytest.mark.asyncio
async def test_payment_integration():
    with respx.mock:
        respx.post("https://api.stripe.com/v1/charges").mock(
            return_value=httpx.Response(200, json={
                "id": "ch_test_123",
                "status": "succeeded",
                "amount": 5000,
            })
        )
        
        result = await payment_service.charge(user_id="usr_1", amount=50.00)
        
        assert result.transaction_id == "ch_test_123"
        assert result.status == "succeeded"

# Mock with dependency injection
@pytest.mark.asyncio
async def test_order_creation_with_mocked_deps():
    mock_repo = AsyncMock(spec=OrderRepository)
    mock_repo.save.return_value = Order(id=uuid4(), status="created")
    
    mock_event_bus = AsyncMock(spec=EventBus)
    
    service = OrderService(repo=mock_repo, event_bus=mock_event_bus)
    
    result = await service.create_order(OrderCreate(items=[...], user_id=uuid4()))
    
    mock_repo.save.assert_called_once()
    mock_event_bus.publish.assert_called_once()
    assert result.status == "created"

# Testcontainers for real infrastructure in tests
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()

@pytest.fixture(scope="session")
def redis():
    with RedisContainer("redis:7") as r:
        yield r.get_connection_url()
```

### 14.4 Property-Based Testing

```python
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

# Property: serialization round-trips
@given(st.builds(
    User,
    email=st.emails(),
    name=st.text(min_size=1, max_size=100),
    age=st.integers(min_value=0, max_value=150),
))
def test_user_serialization_roundtrip(user: User):
    serialized = user.to_dict()
    deserialized = User.from_dict(serialized)
    assert deserialized == user

# Property: sorting invariants
@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    sorted_lst = sorted(lst)
    assert len(sorted_lst) == len(lst)
    assert all(sorted_lst[i] <= sorted_lst[i+1] for i in range(len(sorted_lst)-1))

# Stateful testing — test state machines
class BankAccountMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.account = BankAccount.create("Test", 1000.0)
        self.expected_balance = 1000.0
    
    @rule(amount=st.floats(min_value=0.01, max_value=500.0))
    def deposit(self, amount):
        self.account.deposit(amount)
        self.expected_balance += amount
    
    @rule(amount=st.floats(min_value=0.01, max_value=500.0))
    def withdraw(self, amount):
        assume(amount <= self.expected_balance)
        self.account.withdraw(amount)
        self.expected_balance -= amount
    
    @invariant()
    def balance_matches(self):
        assert abs(self.account.balance - self.expected_balance) < 0.01
    
    @invariant()
    def balance_non_negative(self):
        assert self.account.balance >= 0

TestBankAccount = BankAccountMachine.TestCase
```

### 14.5 Performance Testing

```python
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

def test_serialization_performance(benchmark: BenchmarkFixture):
    user = User(email="test@example.com", name="Test", age=30)
    
    result = benchmark(user.to_dict)
    
    assert result["email"] == "test@example.com"
    # benchmark automatically reports: min, max, mean, stddev, ops/sec

# Load testing with locust
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.5, 2.0)
    
    @task(3)
    def list_users(self):
        self.client.get("/api/v1/users/")
    
    @task(1)
    def create_user(self):
        self.client.post("/api/v1/users/", json={
            "email": f"user_{time.time()}@test.com",
            "name": "Load Test User",
        })
    
    @task(2)
    def get_user(self):
        self.client.get("/api/v1/users/random-id")
```

---

## 15. Security Engineering

#### The Theory — Security is Not Optional (The OWASP Mindset)

**The reality:** Every public API is attacked within hours of deployment. Automated bots scan for common vulnerabilities. If you don't actively defend, you WILL be breached.

**The OWASP Top 10 for APIs (2023) — what attacks look like:**

| Rank | Vulnerability | Python Example | Fix |
|---|---|---|---|
| 1 | Broken Authentication | JWT never expires, no refresh rotation | Short-lived tokens + refresh |
| 2 | Broken Authorization | User A can access User B's data | Check ownership in every endpoint |
| 3 | Excessive Data Exposure | Returning full user object (incl. password_hash) | Response models with limited fields |
| 4 | Lack of Rate Limiting | Brute-force login, scraping | Token bucket per IP/user |
| 5 | Injection | Raw SQL queries, f-string in queries | Parameterized queries always |
| 6 | Mass Assignment | `user.update(**request.dict())` updates `is_admin` | Explicit allowed fields |
| 7 | Security Misconfiguration | Debug mode in prod, CORS `*` | Environment-specific configs |
| 8 | Improper Asset Mgmt | Old API v1 still running, undocumented endpoints | API versioning, deprecation |

**Authentication vs Authorization:**
- **Authentication (AuthN):** WHO are you? (Login, JWT validation)
- **Authorization (AuthZ):** WHAT can you do? (Roles, permissions, ownership)

**Password storage — NEVER store plaintext:**
```
Bad:  password = "secret123"            ← stored as-is, one breach = all accounts compromised
Good: hash = argon2.hash("secret123")   ← one-way, even if DB leaked, passwords are safe

Why Argon2 over bcrypt/SHA:
  - Memory-hard (can't parallelize on GPUs easily)
  - Configurable cost (time + memory)
  - Winner of the Password Hashing Competition (2015)
```

**JWT (JSON Web Tokens) — how they work:**
```
Login: user sends email+password → server validates → server returns JWT
JWT = base64(header).base64(payload).signature

Token has:
  - sub: user_id
  - exp: expiration time (e.g., 15 minutes)
  - iat: issued at
  
Server validates: check signature (not tampered), check exp (not expired).
Server NEVER stores the token — it's stateless. The token IS the proof.
```

**Industry security incidents (learn from others' mistakes):**

- **Uber (2016):** 57M user records stolen. Root cause: AWS credentials hardcoded in a GitHub repo. Lesson: NEVER commit secrets. Use environment variables + secret managers (AWS Secrets Manager, HashiCorp Vault).

- **Twitch (2021):** Entire source code leaked. Internal APIs had no authentication (trusted network fallacy). Lesson: Zero-trust architecture — authenticate EVERY service-to-service call, even internal ones.

- **CircleCI (2023):** Customer secrets compromised. Root cause: malware on an engineer's laptop stole session tokens. Lesson: Short-lived tokens (15min), forced re-auth for sensitive operations, hardware keys for production access.

- **Log4Shell (2021):** Not Python-specific, but relevant lesson. A single library vulnerability affected millions of apps. Python equivalent: always pin dependency versions, use `pip-audit` or `safety` to scan for known vulnerabilities.

- **Stripe's approach:** Every API request is authenticated (API key), rate-limited (per key), logged (audit trail), and validated (Pydantic-style schemas). Every internal service uses mTLS (mutual TLS) for service-to-service auth.

### 15.1 Authentication Patterns

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

class AuthConfig:
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, roles: list[str]) -> str:
    payload = {
        "sub": user_id,
        "roles": roles,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),  # Unique token ID for revocation
    }
    return jwt.encode(payload, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_store: TokenStore = Depends(get_token_store),
) -> TokenPayload:
    try:
        payload = jwt.decode(
            credentials.credentials,
            AuthConfig.SECRET_KEY,
            algorithms=[AuthConfig.ALGORITHM],
        )
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Check revocation
        if await token_store.is_revoked(payload["jti"]):
            raise HTTPException(status_code=401, detail="Token revoked")
        
        return TokenPayload(**payload)
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Role-based access control
def require_roles(*roles: str):
    async def check_roles(user: TokenPayload = Depends(get_current_user)):
        if not any(role in user.roles for role in roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check_roles

@app.get("/admin/users/")
async def admin_list_users(user: TokenPayload = Depends(require_roles("admin"))):
    ...
```

### 15.2 Input Validation and Sanitization

```python
from pydantic import BaseModel, Field, field_validator, model_validator
import re
import bleach

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    bio: str | None = Field(None, max_length=500)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        # Strip HTML/scripts
        return bleach.clean(v, tags=[], strip=True).strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @field_validator('bio')
    @classmethod
    def sanitize_bio(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Allow limited HTML
        return bleach.clean(v, tags=['b', 'i', 'em', 'strong'], strip=True)

# SQL injection prevention — always use parameterized queries
# SQLAlchemy handles this automatically with bound parameters
async def safe_search(session: AsyncSession, query: str) -> list:
    # SAFE: parameterized
    stmt = select(UserModel).where(UserModel.name.ilike(f"%{query}%"))
    
    # NEVER do this:
    # stmt = text(f"SELECT * FROM users WHERE name LIKE '%{query}%'")
    
    result = await session.execute(stmt)
    return result.scalars().all()
```

### 15.3 Secrets Management

```python
from pydantic_settings import BaseSettings
from pydantic import SecretStr
import os

class Settings(BaseSettings):
    # SecretStr prevents accidental logging of secrets
    database_url: SecretStr
    redis_password: SecretStr
    jwt_secret: SecretStr
    api_key: SecretStr
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()

# Accessing secret values
db_url = settings.database_url.get_secret_value()

# Never log secrets
print(settings.database_url)  # Outputs: SecretStr('**********')

# For cloud deployments: use secrets managers
# AWS: boto3 Secrets Manager
# GCP: google-cloud-secret-manager
# Vault: hvac library

import boto3
from functools import lru_cache

@lru_cache
def get_secret(secret_name: str) -> str:
    """Fetch secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

### 15.4 API Security Headers

```python
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Remove server identification
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

# Trusted hosts (prevent host header attacks)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.example.com"])
```

### 15.5 Supply Chain Security

```bash
# Pin all dependencies with hashes
# pip-compile --generate-hashes requirements.in > requirements.txt

# Vulnerability scanning
# pip install safety
# safety check --full-report

# pip-audit — scans installed packages for known vulnerabilities
# pip install pip-audit
# pip-audit

# SBOM generation
# pip install cyclonedx-bom
# cyclonedx-py environment -o sbom.json --format json

# Sigstore — sign and verify packages
# pip install sigstore
# python -m sigstore sign my_package-1.0.0.tar.gz
```

---

## 16. Modern Python Tooling (2025+)

#### The Theory — The Python Tooling Revolution

**The old world (2020-2023):**
```
pip install → slow (resolves dependencies sequentially)
virtualenv → manual management
black + isort + flake8 → 3 tools, 3 configs, conflicts
mypy → slow on large projects
requirements.txt → no lock file, no reproducible builds
```

**The new world (2024-2025+):**
```
uv → replaces pip + virtualenv + pip-tools (10-100x faster, written in Rust)
ruff → replaces black + isort + flake8 + pyupgrade + ALL linters (1 tool, 1 config)
pyright → faster than mypy, better VS Code integration
pyproject.toml → single config file for EVERYTHING
uv.lock → reproducible builds (like package-lock.json)
```

**Why the new tools are better:**

| Tool | Replaces | Speed Improvement | Why Faster |
|---|---|---|---|
| `uv` | pip, pip-tools, virtualenv | 10-100x | Written in Rust, parallel downloads |
| `ruff` | flake8, black, isort, pyupgrade | 50-100x | Written in Rust, single pass |
| `pyright` | mypy | 3-5x | Incremental, better caching |

**The standard modern Python project setup (2025):**
```
pyproject.toml      ← ALL configuration (deps, tools, metadata)
uv.lock             ← exact locked versions (committed to git)
src/                ← source code
tests/              ← test code
.python-version     ← pinned Python version (uv reads this)

No more: setup.py, setup.cfg, requirements.txt, MANIFEST.in, .flake8, .isort.cfg, .black.toml
```

**Industry adoption:**

- **Astral (creators of ruff & uv):** Founded by Charlie Marsh, raised $32M. Their tools are now used by FastAPI, Pydantic, Django, Flask, Jupyter — virtually every major Python project has adopted ruff.

- **Pydantic:** Switched from black+isort+flake8 to ruff. CI time for linting dropped from 45s to 2s.

- **FastAPI:** Uses ruff for linting/formatting, uv for dependency management. Their CI install time dropped from 60s (pip) to 3s (uv).

- **Companies adopting uv (2024-2025):** Stripe, Netflix internal tooling, Anthropic, OpenAI — all migrating from pip/poetry to uv for the speed improvement. A team with 30 developers saves ~1 hour/day of cumulative CI wait time.

### 16.1 uv — Fast Package Manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init my-project
cd my-project

# Add dependencies (10-100x faster than pip)
uv add fastapi uvicorn sqlalchemy[asyncio]
uv add --dev pytest pytest-asyncio ruff mypy

# Lock file (deterministic installs)
uv lock

# Run scripts
uv run python main.py
uv run pytest

# Virtual environment management
uv venv
uv sync  # Install from lock file

# Python version management (replaces pyenv)
uv python install 3.13
uv python pin 3.13
```

### 16.2 Ruff — Fast Linter & Formatter

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

```bash
# Usage (replaces flake8, isort, black, pyupgrade)
ruff check .           # Lint
ruff check --fix .     # Auto-fix
ruff format .          # Format (replaces black)
```

### 16.3 Pydantic v2 Patterns

```python
from pydantic import BaseModel, Field, computed_field, model_validator, ConfigDict
from typing import Self
from datetime import datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,       # ORM mode (was orm_mode)
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"email": "user@example.com"}]},
    )
    
    id: str
    email: str
    name: str
    created_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.email})"

class DateRange(BaseModel):
    start: datetime
    end: datetime
    
    @model_validator(mode='after')
    def validate_range(self) -> Self:
        if self.end <= self.start:
            raise ValueError('end must be after start')
        return self

# Discriminated unions
from typing import Literal, Annotated
from pydantic import Discriminator

class CreditCardPayment(BaseModel):
    type: Literal["credit_card"] = "credit_card"
    card_number: str
    expiry: str

class BankTransferPayment(BaseModel):
    type: Literal["bank_transfer"] = "bank_transfer"
    account_number: str
    routing_number: str

Payment = Annotated[
    CreditCardPayment | BankTransferPayment,
    Discriminator("type"),
]

class Order(BaseModel):
    amount: float
    payment: Payment  # Automatically dispatches based on "type" field
```

### 16.4 Type Checking with pyright/mypy

```toml
# pyproject.toml — pyright configuration
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingImports = true
reportMissingTypeStubs = false
venvPath = "."
venv = ".venv"

# mypy configuration
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### 16.5 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, fastapi]
```

---

## 17. Deployment & Infrastructure

#### The Theory — From Code to Production (The Deployment Pipeline)

**The journey of code to production:**
```
Developer machine → Git push → CI/CD Pipeline → Production
     (write code)    (trigger)   (test, build,     (serve users)
                                  deploy)

CI (Continuous Integration):
  1. Run linters (ruff check)
  2. Run type checker (pyright)
  3. Run unit tests (pytest -x)
  4. Run integration tests (Docker-based)
  5. Build Docker image
  6. Push to container registry

CD (Continuous Deployment):
  7. Deploy to staging (automatic)
  8. Run smoke tests against staging
  9. Deploy to production (manual approval or automatic)
  10. Monitor for errors (rollback if error rate > 1%)
```

**Docker — Why containerization matters:**
```
Without Docker:
  "Works on my machine" — different Python versions, missing system libs,
  different OS configurations. Deployment is fragile and manual.

With Docker:
  The SAME image runs on dev, CI, staging, and production.
  Reproducible everywhere. "Works in the container" = works everywhere.
```

**Docker best practices for Python:**
1. **Multi-stage builds** — separate build (install deps) from runtime (minimal image)
2. **Non-root user** — never run as root in production (security)
3. **Layer caching** — copy `pyproject.toml` before source code (deps change less often)
4. **Slim base image** — `python:3.13-slim` (~150MB) not `python:3.13` (~1GB)
5. **Health checks** — container orchestrator knows when your app is unhealthy

**Kubernetes — Why and when you need it:**
- < 5 services: Docker Compose or ECS is enough. K8s is overkill.
- 5-50 services: Kubernetes provides auto-scaling, self-healing, service discovery.
- Key K8s concepts: Pod (container), Deployment (manages pods), Service (load balancer), HPA (auto-scaling)

**Industry deployment practices:**

- **Spotify:** 1000+ microservices on Kubernetes. Each team owns their deployment. Key pattern: canary deployments — new version handles 5% of traffic first. If error rate increases, automatic rollback.

- **Netflix:** Blue/green deployments on AWS. Two identical environments (blue = current, green = new). Switch traffic atomically. If green fails → switch back to blue in seconds.

- **Instagram:** Gradual rollouts. New code goes to 1% of servers → 5% → 25% → 50% → 100%. Each step waits for metrics to stabilize. A 1% deployment caught a memory leak that would have been catastrophic at 100%.

- **Uber:** They deploy 4000+ times per day across their microservices. Each deploy is automatic (merge to main → deploy to production within 15 minutes). This is only possible with comprehensive testing + canary deployments + automatic rollback.

- **Airbnb:** Uses feature flags instead of code deploys for new features. Code ships in "dark mode" (flag off). Turn flag on for 1% of users → monitor → expand. If broken, flip flag off (instant, no redeploy).

### 17.1 Docker Best Practices

```dockerfile
# Multi-stage build for minimal production image
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ src/

# Production stage
FROM python:3.13-slim AS production

# Security: non-root user
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live')"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 17.2 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: api
          image: registry.example.com/api:v1.2.3
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          startupProbe:
            httpGet:
              path: /health/live
              port: 8000
            failureThreshold: 30
            periodSeconds: 2
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
```

### 17.3 Uvicorn Production Configuration

```python
# gunicorn.conf.py
import multiprocessing
import os

# Worker configuration
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000

# Server configuration
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
keepalive = 65
timeout = 120
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Process naming
proc_name = "api-service"

# Preloading (share memory across workers via copy-on-write)
preload_app = True

def on_starting(server):
    """Hook: called just before the master process is initialized."""
    pass

def pre_fork(server, worker):
    """Hook: called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Hook: called just after a worker has been forked."""
    # Re-seed random after fork
    import random
    random.seed()
```

### 17.4 Graceful Shutdown

```python
import asyncio
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI

class GracefulShutdown:
    """Handles graceful shutdown of async services."""
    
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
    
    def register_task(self, task: asyncio.Task):
        self._tasks.append(task)
    
    async def shutdown(self):
        self._shutdown_event.set()
        
        # Cancel all registered tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete cancellation
        await asyncio.gather(*self._tasks, return_exceptions=True)
    
    @property
    def is_shutting_down(self) -> bool:
        return self._shutdown_event.is_set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    shutdown = GracefulShutdown()
    app.state.shutdown = shutdown
    
    # Start background services
    kafka_task = asyncio.create_task(kafka_consumer.run())
    outbox_task = asyncio.create_task(outbox_publisher.run_forever())
    
    shutdown.register_task(kafka_task)
    shutdown.register_task(outbox_task)
    
    yield
    
    # Graceful shutdown
    await shutdown.shutdown()
    await kafka_producer.stop()
    await db_engine.dispose()
    await redis.close()
```

---

## 18. Interview Patterns

### 18.1 System Design Questions

**"Design a URL shortener"**

```python
import hashlib
import string
from datetime import datetime

class URLShortener:
    """
    Approach:
    - Generate short code: base62 encoding of hash
    - Storage: key-value store (Redis for hot data, PostgreSQL for persistence)
    - Read-heavy: 100:1 read/write ratio → optimize reads with cache
    - Scalability: consistent hashing for distribution
    """
    
    BASE62 = string.ascii_letters + string.digits
    
    def encode(self, url: str) -> str:
        # MD5 → take first 7 chars of base62 encoding
        hash_bytes = hashlib.md5(url.encode()).digest()
        num = int.from_bytes(hash_bytes[:6], 'big')
        
        chars = []
        while num > 0:
            chars.append(self.BASE62[num % 62])
            num //= 62
        
        return ''.join(reversed(chars))[:7]
    
    async def shorten(self, long_url: str, custom_alias: str = None) -> str:
        short_code = custom_alias or self.encode(long_url)
        
        # Check collision
        existing = await self.redis.get(f"url:{short_code}")
        if existing and existing != long_url:
            # Handle collision: append counter
            short_code = f"{short_code}{await self.redis.incr('collision_counter')}"
        
        # Store with TTL
        await self.redis.setex(f"url:{short_code}", 86400 * 365, long_url)
        
        # Persist to database asynchronously
        await self.db.execute(
            "INSERT INTO urls (short_code, long_url, created_at) VALUES ($1, $2, $3)",
            short_code, long_url, datetime.utcnow()
        )
        
        return f"https://short.url/{short_code}"
    
    async def resolve(self, short_code: str) -> str | None:
        # Check cache first
        url = await self.redis.get(f"url:{short_code}")
        if url:
            return url
        
        # Fallback to database
        url = await self.db.fetchval(
            "SELECT long_url FROM urls WHERE short_code = $1", short_code
        )
        
        if url:
            # Warm cache
            await self.redis.setex(f"url:{short_code}", 3600, url)
        
        return url
```

**"Design a rate limiter"**

```python
import time
from typing import Tuple

class SlidingWindowRateLimiter:
    """
    Sliding window counter — best balance of accuracy and memory.
    
    Approach:
    - Divide time into fixed windows
    - Use weighted count: prev_window_count * overlap% + current_count
    - O(1) time, O(1) space per client
    """
    
    def __init__(self, redis, limit: int, window_seconds: int):
        self.redis = redis
        self.limit = limit
        self.window = window_seconds
    
    async def is_allowed(self, client_id: str) -> Tuple[bool, dict]:
        now = time.time()
        current_window = int(now // self.window)
        previous_window = current_window - 1
        
        curr_key = f"rl:{client_id}:{current_window}"
        prev_key = f"rl:{client_id}:{previous_window}"
        
        # Get counts for current and previous windows
        pipe = self.redis.pipeline()
        pipe.get(curr_key)
        pipe.get(prev_key)
        curr_count, prev_count = await pipe.execute()
        
        curr_count = int(curr_count or 0)
        prev_count = int(prev_count or 0)
        
        # Calculate weighted count
        elapsed_in_window = now - (current_window * self.window)
        weight = 1 - (elapsed_in_window / self.window)
        
        estimated_count = prev_count * weight + curr_count
        
        if estimated_count >= self.limit:
            return False, {
                "limit": self.limit,
                "remaining": 0,
                "retry_after": self.window - elapsed_in_window,
            }
        
        # Increment current window
        pipe = self.redis.pipeline()
        pipe.incr(curr_key)
        pipe.expire(curr_key, self.window * 2)
        await pipe.execute()
        
        return True, {
            "limit": self.limit,
            "remaining": int(self.limit - estimated_count - 1),
            "retry_after": 0,
        }

class TokenBucketRateLimiter:
    """
    Token bucket — allows bursts while maintaining average rate.
    
    - Tokens added at fixed rate
    - Bucket has max capacity (burst size)
    - Each request consumes one token
    """
    
    def __init__(self, redis, rate: float, burst: int):
        self.redis = redis
        self.rate = rate    # Tokens per second
        self.burst = burst  # Max tokens
    
    async def is_allowed(self, client_id: str) -> bool:
        key = f"tb:{client_id}"
        now = time.time()
        
        # Atomic token bucket with Lua script
        script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local burst = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local data = redis.call('HMGET', key, 'tokens', 'last_time')
        local tokens = tonumber(data[1]) or burst
        local last_time = tonumber(data[2]) or now
        
        -- Add tokens based on elapsed time
        local elapsed = now - last_time
        tokens = math.min(burst, tokens + elapsed * rate)
        
        local allowed = tokens >= 1
        if allowed then
            tokens = tokens - 1
        end
        
        redis.call('HMSET', key, 'tokens', tokens, 'last_time', now)
        redis.call('EXPIRE', key, burst / rate * 2)
        
        return allowed and 1 or 0
        """
        
        result = await self.redis.eval(script, 1, key, self.rate, self.burst, now)
        return bool(result)
```

### 18.2 Coding Interview Patterns

```python
# LRU Cache implementation
from collections import OrderedDict
from threading import Lock

class LRUCache:
    """Thread-safe LRU cache — O(1) get and put."""
    
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> int | None:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def put(self, key: str, value: int) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                if len(self._cache) >= self._capacity:
                    self._cache.popitem(last=False)  # Remove oldest
                self._cache[key] = value


# Async worker pool with bounded concurrency
class WorkerPool:
    """Process N tasks with max M concurrent workers."""
    
    def __init__(self, max_workers: int = 10):
        self._semaphore = asyncio.Semaphore(max_workers)
        self._results: list = []
    
    async def submit(self, coro):
        async with self._semaphore:
            result = await coro
            self._results.append(result)
            return result
    
    async def map(self, func, items):
        tasks = [
            asyncio.create_task(self.submit(func(item)))
            for item in items
        ]
        return await asyncio.gather(*tasks)


# Producer-consumer with graceful shutdown
async def producer_consumer_example():
    queue = asyncio.Queue(maxsize=100)
    shutdown = asyncio.Event()
    
    async def producer():
        i = 0
        while not shutdown.is_set():
            await queue.put(i)
            i += 1
            await asyncio.sleep(0.01)
        
        # Signal consumers to stop
        for _ in range(3):  # Number of consumers
            await queue.put(None)
    
    async def consumer(name: str):
        while True:
            item = await queue.get()
            if item is None:
                break
            await process(item)
            queue.task_done()
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer())
        for i in range(3):
            tg.create_task(consumer(f"worker-{i}"))
        
        await asyncio.sleep(5)
        shutdown.set()
```

### 18.3 Common Interview Questions (Staff Level)

```python
# Q: "How would you handle a memory leak in production?"
"""
1. Detect: monitor RSS memory growth over time (Prometheus/Datadog)
2. Profile: 
   - tracemalloc for allocation tracking
   - objgraph for reference graph visualization
   - py-spy for sampling without restart
3. Common causes:
   - Unbounded caches (use maxsize or WeakValueDictionary)
   - Event listeners never removed
   - Circular references with __del__
   - Global lists/dicts that grow forever
   - C extension not releasing memory
4. Fix: bounded data structures, proper cleanup, gc.collect() as band-aid
"""

# Q: "Explain Python's import system"
"""
1. sys.modules check (cache) → if found, return it
2. Find the module:
   - sys.meta_path finders (PathFinder, BuiltinImporter, FrozenImporter)
   - sys.path entries
3. Load the module:
   - Create module object
   - Execute module code in module's namespace
   - Store in sys.modules
4. Circular imports: partially-loaded module returned from sys.modules
5. Lazy imports (Python 3.12+): PEP 690 for startup optimization
"""

# Q: "How do you ensure exactly-once processing in a distributed system?"
"""
Exactly-once is impossible in general (FLP impossibility), but achievable with:
1. Idempotency keys: client generates unique key, server deduplicates
2. Outbox pattern: atomic write to DB + outbox table, separate publisher
3. Kafka transactions: producer transaction + consumer offset commit
4. Deduplication window: store processed message IDs with TTL

Pattern:
- At-least-once delivery (retry on failure)
- + Idempotent processing (same input → same output, no side effects on replay)
- = Effectively exactly-once
"""

# Q: "When would you choose asyncio over multiprocessing?"
"""
asyncio:
- I/O-bound workloads (HTTP calls, DB queries, file I/O)
- High concurrency (thousands of connections)
- Single process, cooperative multitasking
- Lower memory (coroutines are ~100 bytes vs threads ~1MB)

multiprocessing:
- CPU-bound workloads (data processing, ML inference)
- True parallelism (bypasses GIL)
- Fault isolation (process crash doesn't kill others)
- Higher overhead (process creation, IPC serialization)

Hybrid (common in production):
- asyncio event loop for I/O coordination
- ProcessPoolExecutor for CPU-bound tasks
- run_in_executor() to bridge the two
"""
```

---

## Quick Reference: Performance Numbers

| Operation | Time |
|-----------|------|
| L1 cache reference | 0.5 ns |
| L2 cache reference | 7 ns |
| Main memory reference | 100 ns |
| SSD random read | 16 μs |
| Network round trip (same datacenter) | 0.5 ms |
| SSD sequential read (1 MB) | 1 ms |
| Network round trip (cross-region) | 50-100 ms |
| HDD seek | 10 ms |

| Python Operation | Relative Speed |
|------------------|---------------|
| dict lookup | 1x (baseline) |
| list append | 1x |
| set membership | 1x |
| list membership | O(n) — 100x slower for n=100 |
| string concatenation (loop) | O(n²) — avoid |
| f-string | 2-3x faster than .format() |
| dataclass(slots=True) | 3x less memory than regular |
| numpy vectorized | 100x faster than Python loop |

---

## 19. High-Throughput System Design Checklist (Interview + Production)

#### The Theory — How to Think About System Design

When asked "Design a system that handles X million requests per day," here's the mental framework:

**Step 1: Back-of-the-envelope calculations**
```
Given: 10 million requests per day

Requests per second:
  10,000,000 / 86,400 ≈ 115 RPS (average)
  Peak (assume 3x average): ~350 RPS
  
Storage per year (if each request creates 1KB record):
  10M × 1KB × 365 = 3.65 TB/year
  
Bandwidth:
  350 RPS × 5KB (avg response) = 1.75 MB/s outbound
```

**Step 2: Choose architecture based on scale**
```
< 100 RPS:          Single server, monolith, PostgreSQL ✓
100 - 1,000 RPS:    Multiple workers, read replicas, Redis cache
1,000 - 10,000 RPS: Load balancer, horizontal scaling, message queue
10,000 - 100,000:   Microservices, sharding, CDN, auto-scaling
> 100,000 RPS:      Event-driven, CQRS, specialized data stores, edge computing
```

**Step 3: Design for the hard problems**

| Problem | Solution Pattern | When to Apply |
|---|---|---|
| Hot spots (viral content) | Cache + CDN + sharding by hash | Social media, e-commerce |
| Consistency across services | Saga + event sourcing | Financial, inventory |
| Burst traffic (flash sales) | Queue + rate limit + auto-scale | E-commerce, ticketing |
| Global latency | Multi-region + eventual consistency | SaaS, streaming |
| Data growth | Partitioning + archival + data lakes | Analytics, IoT |
| Single point of failure | Redundancy + health checks + failover | Everything production |

**The complete high-throughput checklist:**

```
BEFORE PRODUCTION LAUNCH:
□ Load tested to 3x expected peak
□ Circuit breakers on all external dependencies
□ Rate limiting on all public endpoints
□ Health checks (liveness + readiness)
□ Graceful shutdown (drain connections before exit)
□ Connection pooling for DB + HTTP clients
□ Structured logging with correlation IDs
□ P50/P95/P99 latency dashboards
□ Error rate alerts (PagerDuty/OpsGenie)
□ Auto-scaling configured (CPU > 70% → scale up)

SCALING CHECKPOINTS:
□ 100 RPS: Add Redis caching for hot paths
□ 500 RPS: Move to async workers for heavy tasks
□ 1K RPS: Add read replicas, connection pooler (PgBouncer)
□ 5K RPS: Horizontal scaling, stateless services
□ 10K RPS: CDN for static, message queue for async
□ 50K RPS: Sharding, microservices, CQRS
□ 100K+ RPS: Edge computing, custom solutions

RESILIENCE CHECKLIST:
□ Retry with exponential backoff + jitter
□ Circuit breaker per dependency (5 failures → open)
□ Bulkhead (separate thread/process pools)
□ Timeout on every external call (never wait forever)
□ Graceful degradation (serve stale cache when DB is down)
□ Chaos testing (Netflix Chaos Monkey approach)
□ Disaster recovery plan tested quarterly
```

**Python-specific performance tips for high throughput:**

| Technique | Improvement | Implementation |
|---|---|---|
| `uvloop` | 2-3x faster event loop | `uvicorn --loop uvloop` |
| `orjson` | 10x faster JSON serialization | `response_class=ORJSONResponse` |
| Connection pooling | 50x fewer DB connections | SQLAlchemy `pool_size=20` |
| `__slots__` | 3x less memory per object | On hot data classes |
| asyncio gather | Parallel I/O (not sequential) | `await asyncio.gather(a(), b(), c())` |
| Pydantic v2 | 5-50x faster validation | Upgrade from v1 |
| `lru_cache` | Skip repeated computation | Pure functions with hashable args |
| Streaming responses | Constant memory usage | `StreamingResponse` for large payloads |
| Background tasks | Don't block the response | `BackgroundTasks.add_task()` |
| Compiled regex | 10x faster pattern matching | `re.compile()` at module level |

---

## Recommended Reading Order

1. **Week 1-2**: Sections 1-2 (Internals, Memory)
2. **Week 3-4**: Section 3-4 (Concurrency, Free-threading)
3. **Week 5-6**: Sections 5-6 (Performance, Types)
4. **Week 7-8**: Sections 8-9 (Patterns, FastAPI)
5. **Week 9-10**: Sections 10-11 (Database, Events)
6. **Week 11-12**: Sections 12-13 (Distributed Systems, Observability)
7. **Week 13-14**: Sections 14-15 (Testing, Security)
8. **Week 15-16**: Sections 16-19 (Tooling, Deployment, Interview, System Design)

---

*This guide assumes Python 3.12+ and covers patterns used at companies like Instagram (Django), Dropbox (asyncio), Stripe (type safety), and Netflix (resilience patterns).*
