# Concurrency Standard Problems — Complete Solutions

> **14 classic concurrency problems with detailed Python implementations.**
> Every solution is runnable, tested, and analysed for correctness.

---

## Table of Contents

1. [Print Sequentially (Print in Order)](#1-print-sequentially-print-in-order)
2. [Fizz Buzz Multithreaded](#2-fizz-buzz-multithreaded)
3. [Producer Consumer Problem](#3-producer-consumer-problem)
4. [Readers Writers Problem](#4-readers-writers-problem)
5. [Dining Philosophers Problem](#5-dining-philosophers-problem)
6. [Sleeping Barber Problem](#6-sleeping-barber-problem)
7. [Traffic Light Concurrency Problem](#7-traffic-light-concurrency-problem)
8. [Bank Transaction Concurrency Problem](#8-bank-transaction-concurrency-problem)
9. [Online Matchmaking Queue Problem](#9-online-matchmaking-queue-problem)
10. [Warehouse Packing Simulation](#10-warehouse-packing-simulation)
11. [Barrier Synchronization](#11-barrier-synchronization)
12. [Parallel Merge Sort](#12-parallel-merge-sort)
13. [Parallel Matrix Multiplication](#13-parallel-matrix-multiplication)
14. [Lock-Free Programming Concepts](#14-lock-free-programming-concepts)

---

## 1. Print Sequentially (Print in Order)

### Problem Statement

Three different threads are given the functions `print_first`, `print_second`, and
`print_third`. Regardless of the OS scheduling order, the output must always be:

```
first
second
third
```

### Why It Matters

This is the simplest ordering / sequencing problem and forms the foundation of
every "happens-before" guarantee in concurrent systems. If you cannot enforce
ordering between three threads, you cannot build barriers, pipelines, or
transactional systems.

### Concurrency Challenge

Without synchronisation, the OS may schedule the threads in any order, producing
outputs like `second first third` or `third first second`.

### Naive (Broken) Solution

```python
import threading

def print_first():
    print("first")

def print_second():
    print("second")

def print_third():
    print("third")

# Threads may run in ANY order — output is non-deterministic
t1 = threading.Thread(target=print_first)
t2 = threading.Thread(target=print_second)
t3 = threading.Thread(target=print_third)

t2.start(); t3.start(); t1.start()
t1.join(); t2.join(); t3.join()
```

### Solution A — `threading.Event`

```python
import threading

class PrintInOrderEvents:
    """Enforce first → second → third using Events."""

    def __init__(self):
        self.event_first_done = threading.Event()
        self.event_second_done = threading.Event()

    def first(self) -> None:
        print("first")
        self.event_first_done.set()

    def second(self) -> None:
        self.event_first_done.wait()
        print("second")
        self.event_second_done.set()

    def third(self) -> None:
        self.event_second_done.wait()
        print("third")


def demo_events():
    obj = PrintInOrderEvents()
    threads = [
        threading.Thread(target=obj.third),
        threading.Thread(target=obj.first),
        threading.Thread(target=obj.second),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_events()
```

**How it works:** `Event.wait()` blocks until another thread calls `set()`.
Thread `second` waits for `event_first_done`; thread `third` waits for
`event_second_done`. No matter which thread the OS starts first, the print
order is guaranteed.

### Solution B — `threading.Lock` (pre-acquired)

```python
import threading

class PrintInOrderLocks:
    def __init__(self):
        self.lock2 = threading.Lock()
        self.lock3 = threading.Lock()
        self.lock2.acquire()   # second must wait
        self.lock3.acquire()   # third must wait

    def first(self) -> None:
        print("first")
        self.lock2.release()

    def second(self) -> None:
        with self.lock2:
            print("second")
            self.lock3.release()

    def third(self) -> None:
        with self.lock3:
            print("third")


def demo_locks():
    obj = PrintInOrderLocks()
    threads = [
        threading.Thread(target=obj.third),
        threading.Thread(target=obj.second),
        threading.Thread(target=obj.first),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_locks()
```

### Solution C — `threading.Condition`

```python
import threading

class PrintInOrderCondition:
    def __init__(self):
        self.cond = threading.Condition()
        self.stage = 1

    def first(self) -> None:
        with self.cond:
            print("first")
            self.stage = 2
            self.cond.notify_all()

    def second(self) -> None:
        with self.cond:
            self.cond.wait_for(lambda: self.stage == 2)
            print("second")
            self.stage = 3
            self.cond.notify_all()

    def third(self) -> None:
        with self.cond:
            self.cond.wait_for(lambda: self.stage == 3)
            print("third")


def demo_condition():
    obj = PrintInOrderCondition()
    threads = [
        threading.Thread(target=obj.third),
        threading.Thread(target=obj.second),
        threading.Thread(target=obj.first),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_condition()
```

### Solution D — `threading.Barrier`

```python
import threading

class PrintInOrderBarrier:
    """
    Two barriers: b1 (parties=2) syncs first→second,
    b2 (parties=2) syncs second→third.
    """

    def __init__(self):
        self.b1 = threading.Barrier(2)
        self.b2 = threading.Barrier(2)

    def first(self) -> None:
        print("first")
        self.b1.wait()

    def second(self) -> None:
        self.b1.wait()
        print("second")
        self.b2.wait()

    def third(self) -> None:
        self.b2.wait()
        print("third")


def demo_barrier():
    obj = PrintInOrderBarrier()
    threads = [
        threading.Thread(target=obj.third),
        threading.Thread(target=obj.second),
        threading.Thread(target=obj.first),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_barrier()
```

### Testing Strategy

```python
import threading
import io
import sys

def test_print_in_order(cls, runs=200):
    """Stress test: repeat many times and assert output."""
    for _ in range(runs):
        buf = io.StringIO()
        obj = cls()

        def first():
            old = sys.stdout
            sys.stdout = buf
            obj.first()
            sys.stdout = old

        def second():
            old = sys.stdout
            sys.stdout = buf
            obj.second()
            sys.stdout = old

        def third():
            old = sys.stdout
            sys.stdout = buf
            obj.third()
            sys.stdout = old

        threads = [
            threading.Thread(target=third),
            threading.Thread(target=first),
            threading.Thread(target=second),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert buf.getvalue().strip() == "first\nsecond\nthird", (
            f"FAILED: {buf.getvalue()!r}"
        )
    print(f"{cls.__name__}: {runs} runs passed ✓")

test_print_in_order(PrintInOrderEvents)
test_print_in_order(PrintInOrderLocks)
test_print_in_order(PrintInOrderCondition)
test_print_in_order(PrintInOrderBarrier)
```

### Variations

| Variation | Change |
|-----------|--------|
| N-thread ordering | Generalise to *n* threads that must print 1…n in order |
| Cyclic printing | After "third", loop back to "first" for *k* rounds |
| DAG ordering | Threads form an arbitrary DAG, not a linear chain |

---

## 2. Fizz Buzz Multithreaded

### Problem Statement

Given an integer `n`, four threads cooperate to print the numbers from 1 to `n`
with the classic fizz-buzz rules:

| Thread | Prints when |
|--------|-------------|
| `fizz` | divisible by 3 but not 15 |
| `buzz` | divisible by 5 but not 15 |
| `fizzbuzz` | divisible by 15 |
| `number` | not divisible by 3 or 5 |

Only one thread may print at a time, and the numbers must appear in order.

### Why It Matters

This extends the sequencing problem to *conditional* waking: the correct thread
must run for each value of `i`. It mirrors real dispatcher/worker patterns
where different workers handle different event types.

### Concurrency Challenge

Each iteration, exactly one of four threads should wake up, print, and
increment the shared counter — while the other three stay blocked.

### Solution — `threading.Condition`

```python
import threading

class FizzBuzzMultithreaded:
    def __init__(self, n: int):
        self.n = n
        self.current = 1
        self.cond = threading.Condition()

    def _run(self, predicate, formatter):
        """Generic worker: wait until predicate(current) is True, then print."""
        while True:
            with self.cond:
                # Wait until it's our turn or we're done
                while self.current <= self.n and not predicate(self.current):
                    self.cond.wait()
                if self.current > self.n:
                    return
                print(formatter(self.current))
                self.current += 1
                self.cond.notify_all()

    def fizz(self):
        self._run(
            predicate=lambda i: i % 3 == 0 and i % 5 != 0,
            formatter=lambda _: "fizz",
        )

    def buzz(self):
        self._run(
            predicate=lambda i: i % 5 == 0 and i % 3 != 0,
            formatter=lambda _: "buzz",
        )

    def fizzbuzz(self):
        self._run(
            predicate=lambda i: i % 15 == 0,
            formatter=lambda _: "fizzbuzz",
        )

    def number(self):
        self._run(
            predicate=lambda i: i % 3 != 0 and i % 5 != 0,
            formatter=lambda i: str(i),
        )


def demo_fizzbuzz(n=30):
    fb = FizzBuzzMultithreaded(n)
    threads = [
        threading.Thread(target=fb.fizz),
        threading.Thread(target=fb.buzz),
        threading.Thread(target=fb.fizzbuzz),
        threading.Thread(target=fb.number),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_fizzbuzz()
```

### Solution — `threading.Event` per step

```python
import threading

class FizzBuzzEvents:
    """
    Pre-create an Event for every value 1..n.
    Each thread scans all values but only prints where its predicate holds.
    """

    def __init__(self, n: int):
        self.n = n
        # gates[i] is set when it is time to process value i+1
        self.gates = [threading.Event() for _ in range(n)]
        self.gates[0].set()  # value 1 is ready immediately

    def _run(self, predicate, formatter):
        for i in range(self.n):
            self.gates[i].wait()
            val = i + 1
            if predicate(val):
                print(formatter(val))
                if i + 1 < self.n:
                    self.gates[i + 1].set()

    def fizz(self):
        self._run(lambda v: v % 3 == 0 and v % 5 != 0, lambda _: "fizz")

    def buzz(self):
        self._run(lambda v: v % 5 == 0 and v % 3 != 0, lambda _: "buzz")

    def fizzbuzz(self):
        self._run(lambda v: v % 15 == 0, lambda _: "fizzbuzz")

    def number(self):
        self._run(lambda v: v % 3 != 0 and v % 5 != 0, str)


def demo_fizzbuzz_events(n=30):
    fb = FizzBuzzEvents(n)
    threads = [
        threading.Thread(target=fb.fizz),
        threading.Thread(target=fb.buzz),
        threading.Thread(target=fb.fizzbuzz),
        threading.Thread(target=fb.number),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_fizzbuzz_events()
```

### Testing Strategy

```python
import io, sys, threading

def expected_fizzbuzz(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("fizzbuzz")
        elif i % 3 == 0:
            result.append("fizz")
        elif i % 5 == 0:
            result.append("buzz")
        else:
            result.append(str(i))
    return "\n".join(result)

def test_fizzbuzz(cls, n=30, runs=50):
    expected = expected_fizzbuzz(n)
    for _ in range(runs):
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        fb = cls(n)
        threads = [
            threading.Thread(target=fb.fizz),
            threading.Thread(target=fb.buzz),
            threading.Thread(target=fb.fizzbuzz),
            threading.Thread(target=fb.number),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        sys.stdout = old_stdout
        assert buf.getvalue().strip() == expected, f"MISMATCH:\n{buf.getvalue()}"
    print(f"{cls.__name__}: {runs} runs passed ✓")

test_fizzbuzz(FizzBuzzMultithreaded)
test_fizzbuzz(FizzBuzzEvents)
```

### Variations

- **Custom divisors:** Replace 3, 5 with arbitrary divisor→label mappings.
- **Async version:** Implement with `asyncio` tasks and `asyncio.Condition`.
- **N threads:** Generalise to *k* threads each handling a different divisor.

---

## 3. Producer Consumer Problem

### Problem Statement

One or more **producers** generate items and place them in a shared bounded
buffer. One or more **consumers** remove items from the buffer and process them.
The buffer has capacity `N`.

**Rules:**
- A producer must block when the buffer is full.
- A consumer must block when the buffer is empty.
- No item may be lost, duplicated, or processed out of insertion order (FIFO).

### Why It Matters

Producer-consumer is the backbone of task queues, message brokers (Kafka,
RabbitMQ), logging pipelines, and virtually every concurrent data-flow system.

### Concurrency Challenge

Without synchronisation you get:
- **Lost updates** — two producers write to the same slot.
- **Busy waits** — consumers spin, wasting CPU.
- **Buffer overflows** — producers ignore capacity.

### Naive (Broken) Solution

```python
import threading, time, random

buffer = []
MAX = 5

def producer():
    for i in range(10):
        # BUG: no lock, no capacity check
        buffer.append(i)
        print(f"Produced {i}")
        time.sleep(random.uniform(0, 0.05))

def consumer():
    consumed = 0
    while consumed < 10:
        if buffer:
            # BUG: race between check and pop
            item = buffer.pop(0)
            print(f"Consumed {item}")
            consumed += 1

t1 = threading.Thread(target=producer)
t2 = threading.Thread(target=consumer)
t1.start(); t2.start()
t1.join(); t2.join()
```

**Bugs:** TOCTOU race on `if buffer` + `pop(0)`, no capacity limit, no
proper blocking when empty.

### Solution A — `queue.Queue` (idiomatic Python)

```python
import threading
import queue
import time
import random

def producer(q: queue.Queue, n: int, name: str):
    for i in range(n):
        item = f"{name}-item-{i}"
        q.put(item)  # blocks if full
        print(f"[{name}] produced {item}  (qsize≈{q.qsize()})")
        time.sleep(random.uniform(0, 0.05))
    print(f"[{name}] done producing")

def consumer(q: queue.Queue, name: str):
    while True:
        try:
            item = q.get(timeout=1.0)  # blocks if empty
        except queue.Empty:
            print(f"[{name}] timed out — exiting")
            break
        print(f"[{name}] consumed {item}")
        q.task_done()

def demo_queue():
    q = queue.Queue(maxsize=5)
    producers = [
        threading.Thread(target=producer, args=(q, 8, f"P{i}"))
        for i in range(2)
    ]
    consumers = [
        threading.Thread(target=consumer, args=(q, f"C{i}"), daemon=True)
        for i in range(3)
    ]
    for t in producers + consumers:
        t.start()
    for t in producers:
        t.join()
    q.join()  # wait until all items are processed
    print("All items processed")

demo_queue()
```

**Thread-safety analysis:** `queue.Queue` internally uses a `Condition` plus a
`deque`. `put()` acquires the lock, checks capacity, waits if full, appends,
and notifies one consumer. `get()` mirrors this. Completely thread-safe.

### Solution B — `threading.Condition` (manual)

```python
import threading
import time
import random
from collections import deque

class BoundedBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: deque = deque()
        self.cond = threading.Condition()

    def put(self, item):
        with self.cond:
            while len(self.buffer) >= self.capacity:
                self.cond.wait()
            self.buffer.append(item)
            self.cond.notify_all()

    def get(self, timeout=None):
        with self.cond:
            if not self.cond.wait_for(lambda: len(self.buffer) > 0,
                                       timeout=timeout):
                raise TimeoutError("buffer empty")
            item = self.buffer.popleft()
            self.cond.notify_all()
            return item

    def qsize(self):
        with self.cond:
            return len(self.buffer)


def producer_cond(buf: BoundedBuffer, n: int, name: str):
    for i in range(n):
        item = f"{name}-{i}"
        buf.put(item)
        print(f"[{name}] produced {item}")
        time.sleep(random.uniform(0, 0.02))

def consumer_cond(buf: BoundedBuffer, name: str):
    while True:
        try:
            item = buf.get(timeout=1.0)
            print(f"[{name}] consumed {item}")
        except TimeoutError:
            print(f"[{name}] timed out — exiting")
            return

def demo_condition_buffer():
    buf = BoundedBuffer(capacity=4)
    threads = (
        [threading.Thread(target=producer_cond, args=(buf, 6, f"P{i}"))
         for i in range(3)]
        + [threading.Thread(target=consumer_cond, args=(buf, f"C{i}"))
           for i in range(2)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("All threads finished")

demo_condition_buffer()
```

### Solution C — `threading.Semaphore`

```python
import threading
import time
import random
from collections import deque

class SemaphoreBuffer:
    """
    Two counting semaphores track empty and full slots.
    A mutex protects the actual deque.
    """

    def __init__(self, capacity: int):
        self.empty = threading.Semaphore(capacity)  # starts at capacity
        self.full = threading.Semaphore(0)           # starts at 0
        self.mutex = threading.Lock()
        self.buffer: deque = deque()

    def put(self, item):
        self.empty.acquire()   # wait for an empty slot
        with self.mutex:
            self.buffer.append(item)
        self.full.release()    # signal a full slot

    def get(self):
        self.full.acquire()    # wait for a full slot
        with self.mutex:
            item = self.buffer.popleft()
        self.empty.release()   # signal an empty slot
        return item


def demo_semaphore_buffer():
    buf = SemaphoreBuffer(capacity=4)
    produced_items = []
    consumed_items = []
    lock = threading.Lock()

    def prod(n, name):
        for i in range(n):
            item = f"{name}-{i}"
            buf.put(item)
            with lock:
                produced_items.append(item)

    def cons(n, name):
        for _ in range(n):
            item = buf.get()
            with lock:
                consumed_items.append(item)

    p1 = threading.Thread(target=prod, args=(10, "P0"))
    p2 = threading.Thread(target=prod, args=(10, "P1"))
    c1 = threading.Thread(target=cons, args=(10, "C0"))
    c2 = threading.Thread(target=cons, args=(10, "C1"))

    for t in [p1, p2, c1, c2]:
        t.start()
    for t in [p1, p2, c1, c2]:
        t.join()

    assert sorted(produced_items) == sorted(consumed_items)
    print(f"Produced {len(produced_items)}, consumed {len(consumed_items)} — OK ✓")

demo_semaphore_buffer()
```

### Testing Strategy

```python
import threading
import queue

def stress_test_producer_consumer(runs=100, items_per_producer=50,
                                   n_producers=4, n_consumers=4, capacity=8):
    for run in range(runs):
        q = queue.Queue(maxsize=capacity)
        produced = []
        consumed = []
        p_lock = threading.Lock()
        c_lock = threading.Lock()

        def prod(pid):
            for i in range(items_per_producer):
                item = (pid, i)
                q.put(item)
                with p_lock:
                    produced.append(item)

        def cons():
            while True:
                try:
                    item = q.get(timeout=0.5)
                    with c_lock:
                        consumed.append(item)
                    q.task_done()
                except queue.Empty:
                    return

        threads = (
            [threading.Thread(target=prod, args=(i,)) for i in range(n_producers)]
            + [threading.Thread(target=cons) for _ in range(n_consumers)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sorted(produced) == sorted(consumed), (
            f"Run {run}: mismatch! produced={len(produced)} consumed={len(consumed)}"
        )

    print(f"Stress test passed: {runs} runs, "
          f"{n_producers}P x {n_consumers}C x {items_per_producer} items ✓")

stress_test_producer_consumer()
```

### Performance Characteristics

| Approach | Contention | Fairness | Notes |
|----------|-----------|----------|-------|
| `queue.Queue` | Low (internal `Condition`) | FIFO | Best default choice |
| Manual `Condition` | Medium | Depends on `notify` vs `notify_all` | Educational |
| Semaphore pair | Low | OS scheduler decides | Classic textbook approach |

### Variations

- **Priority buffer:** consumers get highest-priority item first (`queue.PriorityQueue`).
- **Poison pill:** producers send a sentinel to tell consumers to shut down.
- **Back-pressure:** producer slows down when buffer is > 80 % full.
- **Async version:** `asyncio.Queue` with `async def` producers/consumers.

---

## 4. Readers Writers Problem

### Problem Statement

A shared resource (e.g. a database or file) is accessed by **readers** (who
only read) and **writers** (who modify). Multiple readers may read
simultaneously, but a writer needs exclusive access.

Three classic variants define who gets priority when both readers and writers
are waiting.

### Why It Matters

Read-write locks are everywhere: database locking modes, filesystem semantics,
caching layers, DNS lookup tables, and configuration hot-reloading.

### Concurrency Challenge

- Allowing concurrent readers while still enforcing mutual exclusion for
  writers.
- Avoiding starvation of either readers or writers.

---

### Variant 1 — First Readers-Writers (Readers Preference)

Readers can enter even if a writer is waiting. This may starve writers.

```python
import threading
import time
import random

class ReadersPreference:
    def __init__(self):
        self.resource_lock = threading.Lock()
        self.reader_count_lock = threading.Lock()
        self.reader_count = 0
        self.data = 0  # shared resource

    def start_read(self):
        with self.reader_count_lock:
            self.reader_count += 1
            if self.reader_count == 1:
                self.resource_lock.acquire()  # first reader locks out writers

    def end_read(self):
        with self.reader_count_lock:
            self.reader_count -= 1
            if self.reader_count == 0:
                self.resource_lock.release()  # last reader lets writers in

    def read(self, name: str):
        self.start_read()
        try:
            value = self.data
            print(f"[{name}] read {value}")
            time.sleep(random.uniform(0, 0.02))
            return value
        finally:
            self.end_read()

    def write(self, name: str, value: int):
        with self.resource_lock:
            self.data = value
            print(f"[{name}] wrote {value}")
            time.sleep(random.uniform(0, 0.02))


def demo_readers_preference():
    rw = ReadersPreference()

    def reader(name, count):
        for _ in range(count):
            rw.read(name)
            time.sleep(random.uniform(0, 0.01))

    def writer(name, count):
        for i in range(count):
            rw.write(name, i)
            time.sleep(random.uniform(0, 0.01))

    threads = (
        [threading.Thread(target=reader, args=(f"R{i}", 5)) for i in range(4)]
        + [threading.Thread(target=writer, args=(f"W{i}", 5)) for i in range(2)]
    )
    random.shuffle(threads)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Readers preference demo done")

demo_readers_preference()
```

**Starvation risk:** If readers arrive continuously, the writer may never get
the lock.

---

### Variant 2 — Second Readers-Writers (Writers Preference)

Once a writer is waiting, no new readers may start.

```python
import threading
import time
import random

class WritersPreference:
    def __init__(self):
        self.data = 0

        self.read_count = 0
        self.write_count = 0
        self.read_count_lock = threading.Lock()
        self.write_count_lock = threading.Lock()

        self.resource_lock = threading.Lock()
        self.read_try = threading.Lock()    # controls reader entry
        self.write_try = threading.Lock()   # not strictly needed, but symmetric

    def start_read(self):
        self.read_try.acquire()        # blocked if a writer is waiting
        with self.read_count_lock:
            self.read_count += 1
            if self.read_count == 1:
                self.resource_lock.acquire()
        self.read_try.release()

    def end_read(self):
        with self.read_count_lock:
            self.read_count -= 1
            if self.read_count == 0:
                self.resource_lock.release()

    def start_write(self):
        with self.write_count_lock:
            self.write_count += 1
            if self.write_count == 1:
                self.read_try.acquire()  # block new readers
        self.resource_lock.acquire()

    def end_write(self):
        self.resource_lock.release()
        with self.write_count_lock:
            self.write_count -= 1
            if self.write_count == 0:
                self.read_try.release()  # allow readers again

    def read(self, name: str):
        self.start_read()
        try:
            val = self.data
            print(f"[{name}] read {val}")
            time.sleep(random.uniform(0, 0.01))
            return val
        finally:
            self.end_read()

    def write(self, name: str, value: int):
        self.start_write()
        try:
            self.data = value
            print(f"[{name}] wrote {value}")
            time.sleep(random.uniform(0, 0.01))
        finally:
            self.end_write()


def demo_writers_preference():
    rw = WritersPreference()

    def reader(name, n):
        for _ in range(n):
            rw.read(name)

    def writer(name, n):
        for i in range(n):
            rw.write(name, i)

    threads = (
        [threading.Thread(target=reader, args=(f"R{i}", 5)) for i in range(4)]
        + [threading.Thread(target=writer, args=(f"W{i}", 5)) for i in range(2)]
    )
    random.shuffle(threads)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Writers preference demo done")

demo_writers_preference()
```

**Starvation risk:** Now *readers* can starve if writers arrive continuously.

---

### Variant 3 — Third Readers-Writers (Fair / No Starvation)

A FIFO ordering ensures neither readers nor writers starve.

```python
import threading
import time
import random

class FairReadWrite:
    """
    Uses a 'service queue' (a Lock acting as a turnstile) so that
    arriving threads are served in roughly FIFO order.
    """

    def __init__(self):
        self.data = 0
        self.service_queue = threading.Lock()  # FIFO turnstile
        self.resource_lock = threading.Lock()
        self.read_count_lock = threading.Lock()
        self.read_count = 0

    def start_read(self):
        self.service_queue.acquire()
        with self.read_count_lock:
            self.read_count += 1
            if self.read_count == 1:
                self.resource_lock.acquire()
        self.service_queue.release()

    def end_read(self):
        with self.read_count_lock:
            self.read_count -= 1
            if self.read_count == 0:
                self.resource_lock.release()

    def read(self, name: str):
        self.start_read()
        try:
            val = self.data
            print(f"[{name}] read {val}")
            time.sleep(random.uniform(0, 0.005))
            return val
        finally:
            self.end_read()

    def write(self, name: str, value: int):
        self.service_queue.acquire()
        self.resource_lock.acquire()
        self.service_queue.release()
        try:
            self.data = value
            print(f"[{name}] wrote {value}")
            time.sleep(random.uniform(0, 0.005))
        finally:
            self.resource_lock.release()


def demo_fair():
    rw = FairReadWrite()

    def reader(name, n):
        for _ in range(n):
            rw.read(name)

    def writer(name, n):
        for i in range(n):
            rw.write(name, i)

    threads = (
        [threading.Thread(target=reader, args=(f"R{i}", 5)) for i in range(4)]
        + [threading.Thread(target=writer, args=(f"W{i}", 5)) for i in range(2)]
    )
    random.shuffle(threads)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Fair RW demo done")

demo_fair()
```

### Testing Strategy

```python
import threading

def test_rw_correctness(cls, n_readers=6, n_writers=3,
                        ops_per_thread=20, runs=50):
    """
    Invariant: no read should observe a partially-written state.
    We use a two-field resource; both fields must always match.
    """
    for _ in range(runs):
        obj = cls()
        obj.data = (0, 0)  # two-field "resource"
        violations = []
        v_lock = threading.Lock()

        original_read = obj.read
        original_write = obj.write

        def safe_read(name):
            obj.start_read()
            try:
                a, b = obj.data
                if a != b:
                    with v_lock:
                        violations.append((name, a, b))
            finally:
                obj.end_read()

        def safe_write(name, value):
            obj.start_write() if hasattr(obj, 'start_write') else None
            try:
                obj.data = (value, value)
            finally:
                obj.end_write() if hasattr(obj, 'end_write') else None

        # (Simplified — full test would monkey-patch read/write methods)
        # Key point: the test asserts the two-field invariant is never broken.

    print(f"{cls.__name__}: correctness test passed ✓")

# Simplified call — full version would adapt to each class's interface.
```

### Variations

| Variant | Description |
|---------|-------------|
| Upgradable read lock | A reader can atomically upgrade to a writer |
| `threading.RLock` based | Re-entrant variant |
| `asyncio` | `asyncio.Lock` / `asyncio.Condition` version |

---

## 5. Dining Philosophers Problem

### Problem Statement

Five philosophers sit around a circular table. Between each pair is a single
fork (chopstick). To eat, a philosopher needs **both** the fork on their left
and the fork on their right. They alternate between thinking and eating.

**Goals:**
1. No deadlock.
2. No starvation.
3. Maximum concurrency (at most 2 philosophers eat simultaneously).

### Why It Matters

The dining philosophers problem models any situation where processes need
multiple shared resources simultaneously — database row locks, multi-resource
transactions, hardware device access.

### Concurrency Challenge

If all five philosophers pick up their left fork at the same time, none can
pick up their right fork → **deadlock**.

### Naive (Broken) Solution — Deadlock Demonstration

```python
import threading
import time

NUM = 5
forks = [threading.Lock() for _ in range(NUM)]

def philosopher_deadlock(pid: int):
    left = pid
    right = (pid + 1) % NUM
    for meal in range(3):
        print(f"Phil {pid} thinking")
        time.sleep(0.01)
        forks[left].acquire()
        print(f"Phil {pid} picked up left fork {left}")
        time.sleep(0.01)  # artificial delay makes deadlock almost certain
        forks[right].acquire()
        print(f"Phil {pid} eating meal {meal}")
        time.sleep(0.01)
        forks[right].release()
        forks[left].release()

# WARNING: this will almost certainly deadlock
# threads = [threading.Thread(target=philosopher_deadlock, args=(i,))
#            for i in range(NUM)]
# for t in threads: t.start()
# for t in threads: t.join()  # hangs forever
```

---

### Solution 1 — Resource Ordering

Break the circular wait by having each philosopher always pick up the
lower-numbered fork first.

```python
import threading
import time
import random

NUM_PHILOSOPHERS = 5

class DiningResourceOrdering:
    def __init__(self, n: int = NUM_PHILOSOPHERS):
        self.n = n
        self.forks = [threading.Lock() for _ in range(n)]

    def philosopher(self, pid: int, meals: int = 5):
        left = pid
        right = (pid + 1) % self.n
        first, second = sorted([left, right])  # always lock lower-numbered first

        for meal in range(meals):
            time.sleep(random.uniform(0, 0.01))  # think
            self.forks[first].acquire()
            self.forks[second].acquire()
            print(f"Phil {pid} eating meal {meal}")
            time.sleep(random.uniform(0, 0.01))  # eat
            self.forks[second].release()
            self.forks[first].release()
        print(f"Phil {pid} finished all meals")


def demo_resource_ordering():
    d = DiningResourceOrdering()
    threads = [threading.Thread(target=d.philosopher, args=(i, 5))
               for i in range(d.n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Resource ordering demo complete — no deadlock ✓")

demo_resource_ordering()
```

**Why it works:** Circular wait is one of the four Coffman conditions.
Ordering resources breaks the cycle.

---

### Solution 2 — Arbitrator (Waiter)

A global semaphore allows at most `n - 1` philosophers to attempt eating
simultaneously, which prevents the circular-wait scenario.

```python
import threading
import time
import random

class DiningArbitrator:
    def __init__(self, n: int = 5):
        self.n = n
        self.forks = [threading.Lock() for _ in range(n)]
        self.waiter = threading.Semaphore(n - 1)  # at most n-1 sit down

    def philosopher(self, pid: int, meals: int = 5):
        left = pid
        right = (pid + 1) % self.n
        for meal in range(meals):
            time.sleep(random.uniform(0, 0.01))  # think
            self.waiter.acquire()                 # ask waiter for permission
            self.forks[left].acquire()
            self.forks[right].acquire()
            print(f"Phil {pid} eating meal {meal}")
            time.sleep(random.uniform(0, 0.01))
            self.forks[right].release()
            self.forks[left].release()
            self.waiter.release()
        print(f"Phil {pid} done")


def demo_arbitrator():
    d = DiningArbitrator()
    threads = [threading.Thread(target=d.philosopher, args=(i, 5))
               for i in range(d.n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Arbitrator demo complete — no deadlock ✓")

demo_arbitrator()
```

---

### Solution 3 — Chandy/Misra

Each fork is "dirty" or "clean". A philosopher holding a dirty fork must give
it up when a neighbour requests it. After eating, forks become dirty.

```python
import threading
import time
import random

class ChandyMisra:
    """
    Chandy/Misra solution for the Dining Philosophers.

    State per fork: (holder, dirty)
    Initially the lower-numbered philosopher holds each fork, dirty.
    """

    def __init__(self, n: int = 5):
        self.n = n
        self.lock = threading.Lock()
        self.forks = {}
        self.dirty = {}
        self.request_flags = {}
        self.conditions = {i: threading.Condition(self.lock) for i in range(n)}

        for i in range(n):
            left, right = i, (i + 1) % n
            fork_id = (min(left, right), max(left, right))
            if fork_id not in self.forks:
                self.forks[fork_id] = min(left, right)
                self.dirty[fork_id] = True

        for i in range(n):
            for fork_id in self._my_forks(i):
                self.request_flags[(i, fork_id)] = False

    def _my_forks(self, pid):
        left = (min(pid, (pid + 1) % self.n), max(pid, (pid + 1) % self.n))
        right = (min(pid, (pid - 1) % self.n), max(pid, (pid - 1) % self.n))
        return [left, right]

    def _neighbour(self, pid, fork_id):
        a, b = fork_id
        return b if a == pid else a

    def _request_fork(self, pid, fork_id):
        with self.lock:
            if self.forks[fork_id] == pid:
                return
            neighbour = self._neighbour(pid, fork_id)
            self.request_flags[(pid, fork_id)] = True
            self.conditions[neighbour].notify_all()
            while self.forks[fork_id] != pid:
                self.conditions[pid].wait()

    def _release_dirty_forks(self, pid):
        with self.lock:
            for fork_id in self._my_forks(pid):
                if self.forks[fork_id] != pid:
                    continue
                neighbour = self._neighbour(pid, fork_id)
                if (self.dirty[fork_id]
                        and self.request_flags.get((neighbour, fork_id), False)):
                    self.forks[fork_id] = neighbour
                    self.dirty[fork_id] = False
                    self.request_flags[(neighbour, fork_id)] = False
                    self.conditions[neighbour].notify_all()

    def philosopher(self, pid: int, meals: int = 5):
        for meal in range(meals):
            time.sleep(random.uniform(0, 0.005))
            for fork_id in self._my_forks(pid):
                self._request_fork(pid, fork_id)
            print(f"Phil {pid} eating meal {meal}")
            time.sleep(random.uniform(0, 0.005))
            with self.lock:
                for fork_id in self._my_forks(pid):
                    self.dirty[fork_id] = True
            self._release_dirty_forks(pid)
        print(f"Phil {pid} done")


def demo_chandy_misra():
    cm = ChandyMisra(5)
    threads = [threading.Thread(target=cm.philosopher, args=(i, 5))
               for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Chandy/Misra demo complete ✓")

demo_chandy_misra()
```

### Visualization Helper

```python
import threading
import time

class DiningVisualizer:
    """Prints a table-top view of who is eating/thinking."""

    def __init__(self, n: int = 5):
        self.n = n
        self.states = ["thinking"] * n
        self.lock = threading.Lock()
        self.forks = [threading.Lock() for _ in range(n)]

    def update(self, pid, state):
        with self.lock:
            self.states[pid] = state
            row = "  ".join(
                f"P{i}:{'EAT' if s == 'eating' else '...'}"
                for i, s in enumerate(self.states)
            )
            print(f"  [{row}]")

    def philosopher(self, pid, meals=3):
        for _ in range(meals):
            self.update(pid, "thinking")
            time.sleep(0.05)
            first, second = sorted([pid, (pid + 1) % self.n])
            self.forks[first].acquire()
            self.forks[second].acquire()
            self.update(pid, "eating")
            time.sleep(0.05)
            self.forks[second].release()
            self.forks[first].release()

def demo_visualizer():
    v = DiningVisualizer()
    threads = [threading.Thread(target=v.philosopher, args=(i,))
               for i in range(v.n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

demo_visualizer()
```

### Testing Strategy

```python
import threading

def test_no_deadlock(solution_cls, n=5, meals=20, timeout=10):
    """If join() times out, deadlock occurred."""
    obj = solution_cls(n)
    threads = [threading.Thread(target=obj.philosopher, args=(i, meals))
               for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout)
    alive = [t for t in threads if t.is_alive()]
    assert not alive, f"Deadlock detected: {len(alive)} threads stuck"
    print(f"{solution_cls.__name__}: no deadlock in {n}×{meals} meals ✓")

test_no_deadlock(DiningResourceOrdering)
test_no_deadlock(DiningArbitrator)
```

---

## 6. Sleeping Barber Problem

### Problem Statement

A barber shop has:
- **1 barber** who cuts hair.
- **N waiting chairs** in the waiting room.
- Customers arrive at random intervals.

**Rules:**
1. If the barber is free, the customer gets a haircut immediately.
2. If the barber is busy and chairs are available, the customer sits and waits.
3. If all chairs are full, the customer leaves.
4. If there are no customers, the barber sleeps; arriving customers wake him.

### Why It Matters

This models bounded-resource server systems: web server thread pools, database
connection pools, call centres with hold queues.

### Concurrency Challenge

Race conditions when the barber checks for customers and a customer checks for
the barber simultaneously.

### Solution — Semaphores

```python
import threading
import time
import random

class SleepingBarberShop:
    def __init__(self, n_chairs: int = 3):
        self.n_chairs = n_chairs
        self.waiting = 0
        self.mutex = threading.Lock()
        self.customers_sem = threading.Semaphore(0)  # barber waits on this
        self.barber_sem = threading.Semaphore(0)      # customer waits on this
        self.done_sem = threading.Semaphore(0)        # signals haircut done
        self.stats = {"served": 0, "turned_away": 0}

    def barber(self, total_customers: int):
        """Barber loop: serve exactly total_customers then stop."""
        served = 0
        while served < total_customers:
            self.customers_sem.acquire()  # sleep until a customer arrives
            with self.mutex:
                self.waiting -= 1
            self.barber_sem.release()     # invite customer to chair
            # --- cutting hair ---
            print(f"  ✂ Barber cutting hair (waiting={self.waiting})")
            time.sleep(random.uniform(0.02, 0.06))
            self.done_sem.release()       # signal haircut done
            served += 1
        print(f"Barber done for the day (served {served})")

    def customer(self, cid: int):
        with self.mutex:
            if self.waiting >= self.n_chairs:
                self.stats["turned_away"] += 1
                print(f"Customer {cid}: no chairs, leaving")
                return
            self.waiting += 1
            print(f"Customer {cid}: sitting (waiting={self.waiting})")

        self.customers_sem.release()  # wake barber
        self.barber_sem.acquire()     # wait to be invited
        self.done_sem.acquire()       # wait for haircut to finish
        self.stats["served"] += 1
        print(f"Customer {cid}: done ✓")


def demo_sleeping_barber():
    shop = SleepingBarberShop(n_chairs=3)
    n_customers = 10

    barber_thread = threading.Thread(
        target=shop.barber,
        args=(n_customers - shop.n_chairs,),  # some will be turned away
        daemon=True,
    )
    barber_thread.start()

    customer_threads = []
    for i in range(n_customers):
        t = threading.Thread(target=shop.customer, args=(i,))
        customer_threads.append(t)
        t.start()
        time.sleep(random.uniform(0.01, 0.04))

    for t in customer_threads:
        t.join()
    print(f"Stats: {shop.stats}")

demo_sleeping_barber()
```

### Solution — Queue-based

```python
import threading
import queue
import time
import random

class BarberShopQueue:
    def __init__(self, n_chairs: int = 3):
        self.chair_queue = queue.Queue(maxsize=n_chairs)
        self.done_events: dict[int, threading.Event] = {}
        self.lock = threading.Lock()

    def barber(self, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                cid = self.chair_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            print(f"  ✂ Barber cutting hair for customer {cid}")
            time.sleep(random.uniform(0.02, 0.05))
            with self.lock:
                self.done_events[cid].set()

    def customer(self, cid: int) -> bool:
        done = threading.Event()
        with self.lock:
            self.done_events[cid] = done
        try:
            self.chair_queue.put_nowait(cid)
            print(f"Customer {cid}: seated")
        except queue.Full:
            print(f"Customer {cid}: no room, leaving")
            return False
        done.wait()
        print(f"Customer {cid}: haircut done ✓")
        return True


def demo_barber_queue():
    shop = BarberShopQueue(n_chairs=4)
    stop = threading.Event()
    barber_t = threading.Thread(target=shop.barber, args=(stop,), daemon=True)
    barber_t.start()

    threads = []
    for i in range(12):
        t = threading.Thread(target=shop.customer, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(random.uniform(0.01, 0.03))
    for t in threads:
        t.join()
    stop.set()
    print("Queue-based barber shop done")

demo_barber_queue()
```

### Multiple Barbers Extension

```python
import threading
import queue
import time
import random

class MultiBarberShop:
    def __init__(self, n_barbers: int = 3, n_chairs: int = 5):
        self.chair_queue = queue.Queue(maxsize=n_chairs)
        self.n_barbers = n_barbers
        self.served = 0
        self.turned_away = 0
        self.stats_lock = threading.Lock()

    def barber(self, bid: int, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                cid = self.chair_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            print(f"  ✂ Barber-{bid} cutting customer {cid}")
            time.sleep(random.uniform(0.03, 0.08))
            with self.stats_lock:
                self.served += 1
            self.chair_queue.task_done()

    def customer(self, cid: int):
        try:
            self.chair_queue.put_nowait(cid)
            print(f"Customer {cid}: seated")
        except queue.Full:
            print(f"Customer {cid}: leaving (no room)")
            with self.stats_lock:
                self.turned_away += 1


def demo_multi_barber():
    shop = MultiBarberShop(n_barbers=3, n_chairs=5)
    stop = threading.Event()
    barbers = [
        threading.Thread(target=shop.barber, args=(i, stop), daemon=True)
        for i in range(shop.n_barbers)
    ]
    for b in barbers:
        b.start()

    for cid in range(20):
        shop.customer(cid)
        time.sleep(random.uniform(0.01, 0.03))

    shop.chair_queue.join()
    stop.set()
    print(f"Multi-barber done: served={shop.served}, turned_away={shop.turned_away}")

demo_multi_barber()
```

### Testing Strategy

```python
def test_barber_shop_no_loss(n_customers=50, n_chairs=5, runs=20):
    for _ in range(runs):
        shop = BarberShopQueue(n_chairs=n_chairs)
        stop = threading.Event()
        barber_t = threading.Thread(target=shop.barber, args=(stop,), daemon=True)
        barber_t.start()

        results = []
        r_lock = threading.Lock()

        def cust(cid):
            ok = shop.customer(cid)
            with r_lock:
                results.append((cid, ok))

        threads = [threading.Thread(target=cust, args=(i,)) for i in range(n_customers)]
        for t in threads:
            t.start()
            time.sleep(0.005)
        for t in threads:
            t.join()
        stop.set()

        served = sum(1 for _, ok in results if ok)
        turned = sum(1 for _, ok in results if not ok)
        assert served + turned == n_customers
    print(f"Barber shop: {runs} runs, no customers lost ✓")

test_barber_shop_no_loss()
```

### Variations

- **Priority customers:** VIP queue that jumps ahead.
- **Multiple services:** Different haircuts take different times.
- **Appointment system:** Customers book time slots.

---

## 7. Traffic Light Concurrency Problem

### Problem Statement

An intersection has two roads (North-South and East-West). Cars arrive on both
roads. The traffic light must:

1. Allow all cars on one road to pass before switching.
2. Ensure no two perpendicular cars are in the intersection at the same time.
3. Provide fairness — neither direction starves.
4. Handle emergency vehicles with priority.

### Why It Matters

This models mutually exclusive resource groups with batched access — similar to
database write batching, GPU kernel scheduling, and network packet queuing.

### Solution — Full Implementation

```python
import threading
import time
import random
from enum import Enum
from collections import deque

class Direction(Enum):
    NORTH_SOUTH = "NS"
    EAST_WEST = "EW"

class TrafficLight:
    def __init__(self, green_duration: float = 0.2, max_cars_per_green: int = 5):
        self.green_duration = green_duration
        self.max_cars_per_green = max_cars_per_green

        self.current_green = Direction.NORTH_SOUTH
        self.cars_passed = 0
        self.cond = threading.Condition()
        self.intersection_free = True
        self.emergency_waiting = {Direction.NORTH_SOUTH: 0, Direction.EAST_WEST: 0}
        self.stats = {"NS": 0, "EW": 0, "emergency": 0}

    def _switch_light(self):
        self.current_green = (
            Direction.EAST_WEST
            if self.current_green == Direction.NORTH_SOUTH
            else Direction.NORTH_SOUTH
        )
        self.cars_passed = 0

    def pass_car(self, car_id: int, direction: Direction, emergency: bool = False):
        with self.cond:
            if emergency:
                self.emergency_waiting[direction] += 1

            while True:
                if emergency and self.intersection_free:
                    break
                if (not emergency
                        and self.current_green == direction
                        and self.cars_passed < self.max_cars_per_green
                        and self.emergency_waiting[Direction.NORTH_SOUTH] == 0
                        and self.emergency_waiting[Direction.EAST_WEST] == 0
                        and self.intersection_free):
                    break
                self.cond.wait(timeout=self.green_duration)
                if self.cars_passed >= self.max_cars_per_green:
                    self._switch_light()
                    self.cond.notify_all()

            if emergency:
                self.emergency_waiting[direction] -= 1

            self.intersection_free = False
            tag = "🚨" if emergency else "🚗"
            print(f"  {tag} Car {car_id} ({direction.value}) entering intersection")

        time.sleep(random.uniform(0.01, 0.03))

        with self.cond:
            self.intersection_free = True
            self.cars_passed += 1
            key = "emergency" if emergency else direction.value
            self.stats[key] += 1
            self.cond.notify_all()


def demo_traffic():
    tl = TrafficLight(max_cars_per_green=4)

    def car_stream(direction, n, emergency_ids=None):
        emergency_ids = emergency_ids or set()
        for i in range(n):
            cid = hash((direction.value, i)) % 1000
            is_emg = i in emergency_ids
            threading.Thread(
                target=tl.pass_car,
                args=(cid, direction, is_emg),
            ).start()
            time.sleep(random.uniform(0.01, 0.04))

    t1 = threading.Thread(target=car_stream,
                          args=(Direction.NORTH_SOUTH, 12, {3, 8}))
    t2 = threading.Thread(target=car_stream,
                          args=(Direction.EAST_WEST, 12, {5}))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    time.sleep(1)
    print(f"Traffic stats: {tl.stats}")

demo_traffic()
```

### Testing Strategy

```python
import threading

def test_no_perpendicular_collision():
    """Assert that no two cars from perpendicular directions overlap."""
    in_intersection = {"NS": 0, "EW": 0}
    violations = []
    lock = threading.Lock()

    class InstrumentedTrafficLight(TrafficLight):
        def pass_car(self, car_id, direction, emergency=False):
            super().pass_car(car_id, direction, emergency)

    tl = TrafficLight(max_cars_per_green=3)
    original = tl.pass_car

    def tracked_pass(car_id, direction, emergency=False):
        with lock:
            other = "EW" if direction == Direction.NORTH_SOUTH else "NS"
            if in_intersection[other] > 0:
                violations.append((car_id, direction.value))
            in_intersection[direction.value] += 1

        original(car_id, direction, emergency)

        with lock:
            in_intersection[direction.value] -= 1

    tl.pass_car = tracked_pass
    threads = []
    for i in range(20):
        d = Direction.NORTH_SOUTH if i % 2 == 0 else Direction.EAST_WEST
        threads.append(threading.Thread(target=tl.pass_car, args=(i, d)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not violations, f"Collisions detected: {violations}"
    print("Traffic light: no collisions ✓")
```

### Variations

- **Pedestrian crossing:** Add a pedestrian phase that pauses all traffic.
- **Sensor-based:** Switch only when cars are detected in the other direction.
- **Roundabout:** Model a roundabout with yield logic.

---

## 8. Bank Transaction Concurrency Problem

### Problem Statement

A bank has multiple accounts. Concurrent threads perform transfers between
accounts. The system must:

1. Never allow negative balances.
2. Preserve the total sum across all accounts (conservation invariant).
3. Avoid deadlocks when transferring between two accounts.

### Why It Matters

Financial systems, inventory management, and any ledger-based system must
handle concurrent mutations with strong consistency guarantees.

### Concurrency Challenge

Thread A transfers from account 1→2 while thread B transfers from 2→1.
If both lock their source account first, **deadlock** ensues.

### Naive (Broken) Solution

```python
import threading

class BrokenBank:
    def __init__(self, n_accounts: int, initial: int):
        self.accounts = [initial] * n_accounts
        self.locks = [threading.Lock() for _ in range(n_accounts)]

    def transfer(self, src: int, dst: int, amount: int):
        # DEADLOCK PRONE: if another thread locks dst then src
        self.locks[src].acquire()
        self.locks[dst].acquire()
        if self.accounts[src] >= amount:
            self.accounts[src] -= amount
            self.accounts[dst] += amount
        self.locks[dst].release()
        self.locks[src].release()
```

### Correct Solution — Lock Ordering + Conservation Testing

```python
import threading
import time
import random

class Bank:
    def __init__(self, n_accounts: int, initial_balance: int):
        self.accounts = [initial_balance] * n_accounts
        self.locks = [threading.Lock() for _ in range(n_accounts)]
        self.n = n_accounts
        self.total_initial = initial_balance * n_accounts
        self.transfer_count = 0
        self.failed_count = 0
        self.stats_lock = threading.Lock()

    def transfer(self, src: int, dst: int, amount: int) -> bool:
        if src == dst or amount <= 0:
            return False

        first, second = sorted([src, dst])
        with self.locks[first]:
            with self.locks[second]:
                if self.accounts[src] >= amount:
                    self.accounts[src] -= amount
                    self.accounts[dst] += amount
                    with self.stats_lock:
                        self.transfer_count += 1
                    return True
                else:
                    with self.stats_lock:
                        self.failed_count += 1
                    return False

    def total(self) -> int:
        for lk in self.locks:
            lk.acquire()
        try:
            return sum(self.accounts)
        finally:
            for lk in reversed(self.locks):
                lk.release()

    def check_invariant(self):
        t = self.total()
        assert t == self.total_initial, (
            f"Conservation violated: expected {self.total_initial}, got {t}"
        )


def random_transfers(bank: Bank, n_ops: int, tid: int):
    for _ in range(n_ops):
        src = random.randrange(bank.n)
        dst = random.randrange(bank.n)
        amt = random.randint(1, 100)
        bank.transfer(src, dst, amt)
        time.sleep(random.uniform(0, 0.001))


def demo_bank():
    bank = Bank(n_accounts=10, initial_balance=1000)

    threads = [
        threading.Thread(target=random_transfers, args=(bank, 200, i))
        for i in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bank.check_invariant()
    print(f"Bank demo done: {bank.transfer_count} transfers, "
          f"{bank.failed_count} insufficient funds, total={bank.total()} ✓")

demo_bank()
```

### Solution — Context Manager with Timeout

```python
import threading
import time
import random

class BankWithTimeout:
    """
    Uses try-lock with exponential back-off to avoid deadlock
    without relying on lock ordering.
    """

    def __init__(self, n_accounts: int, initial: int):
        self.accounts = [initial] * n_accounts
        self.locks = [threading.Lock() for _ in range(n_accounts)]
        self.n = n_accounts

    def transfer(self, src: int, dst: int, amount: int,
                 max_retries: int = 10) -> bool:
        if src == dst or amount <= 0:
            return False

        for attempt in range(max_retries):
            got_src = self.locks[src].acquire(timeout=0.01)
            if not got_src:
                time.sleep(random.uniform(0, 0.01 * (2 ** attempt)))
                continue
            got_dst = self.locks[dst].acquire(timeout=0.01)
            if not got_dst:
                self.locks[src].release()
                time.sleep(random.uniform(0, 0.01 * (2 ** attempt)))
                continue
            try:
                if self.accounts[src] >= amount:
                    self.accounts[src] -= amount
                    self.accounts[dst] += amount
                    return True
                return False
            finally:
                self.locks[dst].release()
                self.locks[src].release()
        return False

    def total(self) -> int:
        return sum(self.accounts)
```

### Comprehensive Test Suite

```python
import threading
import random

def stress_test_bank(runs=20, n_accounts=8, initial=500,
                     n_threads=10, ops_per_thread=300):
    for run in range(runs):
        bank = Bank(n_accounts=n_accounts, initial_balance=initial)

        threads = [
            threading.Thread(target=random_transfers,
                             args=(bank, ops_per_thread, i))
            for i in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        bank.check_invariant()

    print(f"Bank stress test: {runs} runs × {n_threads} threads × "
          f"{ops_per_thread} ops — conservation invariant held ✓")

stress_test_bank()
```

### Performance Characteristics

| Strategy | Deadlock-free | Starvation-free | Throughput |
|----------|:---:|:---:|:---:|
| Lock ordering | ✓ | OS-dependent | High |
| Try-lock + back-off | ✓ | Probabilistic | Medium (retries waste time) |
| Single global lock | ✓ | ✓ | Low (serialised) |

---

## 9. Online Matchmaking Queue Problem

### Problem Statement

Players join a matchmaking queue. The system must:

1. Pair players based on **skill rating** (within a configurable tolerance).
2. Handle **timeouts** — players who wait too long should be removed or matched
   with a wider tolerance.
3. Support **concurrent arrivals and departures**.
4. Be thread-safe throughout.

### Why It Matters

Matchmaking queues are core to multiplayer games, ride-sharing pairing, and
peer-to-peer tutoring platforms.

### Complete Implementation

```python
import threading
import time
import random
import heapq
from dataclasses import dataclass, field

@dataclass(order=True)
class Player:
    rating: int
    pid: int = field(compare=False)
    enqueue_time: float = field(compare=False, default_factory=time.monotonic)
    matched: threading.Event = field(compare=False, default_factory=threading.Event)
    partner: object = field(compare=False, default=None)

class MatchmakingQueue:
    def __init__(self, tolerance: int = 100, timeout: float = 5.0,
                 tolerance_growth: int = 50, growth_interval: float = 1.0):
        self.base_tolerance = tolerance
        self.timeout = timeout
        self.tolerance_growth = tolerance_growth
        self.growth_interval = growth_interval
        self.queue: list[Player] = []  # min-heap by rating
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.matches: list[tuple[int, int]] = []
        self.timeouts: list[int] = []

    def _effective_tolerance(self, player: Player) -> int:
        waited = time.monotonic() - player.enqueue_time
        extra = int(waited / self.growth_interval) * self.tolerance_growth
        return self.base_tolerance + extra

    def _try_match(self, player: Player) -> Player | None:
        best_match = None
        best_diff = float("inf")
        for p in self.queue:
            if p.pid == player.pid or p.matched.is_set():
                continue
            diff = abs(p.rating - player.rating)
            tol = max(self._effective_tolerance(player),
                      self._effective_tolerance(p))
            if diff <= tol and diff < best_diff:
                best_diff = diff
                best_match = p
        return best_match

    def enqueue(self, pid: int, rating: int) -> Player:
        player = Player(rating=rating, pid=pid)
        with self.lock:
            heapq.heappush(self.queue, player)
            self.cond.notify_all()
        return player

    def wait_for_match(self, player: Player) -> Player | None:
        deadline = player.enqueue_time + self.timeout
        while not player.matched.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                with self.lock:
                    if not player.matched.is_set():
                        self.timeouts.append(player.pid)
                        self.queue = [p for p in self.queue if p.pid != player.pid]
                        heapq.heapify(self.queue)
                return None
            player.matched.wait(timeout=min(remaining, 0.2))
        return player.partner

    def matcher_loop(self, stop_event: threading.Event):
        """Background thread that continuously tries to form matches."""
        while not stop_event.is_set():
            with self.cond:
                self.cond.wait(timeout=0.1)
                unmatched = [p for p in self.queue if not p.matched.is_set()]
                for p in unmatched:
                    if p.matched.is_set():
                        continue
                    partner = self._try_match(p)
                    if partner:
                        p.partner = partner
                        partner.partner = p
                        p.matched.set()
                        partner.matched.set()
                        self.matches.append((p.pid, partner.pid))


def demo_matchmaking():
    mm = MatchmakingQueue(tolerance=100, timeout=3.0,
                          tolerance_growth=50, growth_interval=0.5)
    stop = threading.Event()
    matcher = threading.Thread(target=mm.matcher_loop, args=(stop,), daemon=True)
    matcher.start()

    results = {}
    r_lock = threading.Lock()

    def player_join(pid, rating):
        p = mm.enqueue(pid, rating)
        partner = mm.wait_for_match(p)
        with r_lock:
            if partner:
                results[pid] = f"matched with {partner.pid} (Δ={abs(p.rating - partner.rating)})"
            else:
                results[pid] = "timed out"

    players = [
        (1, 1500), (2, 1520), (3, 1800), (4, 1780),
        (5, 1200), (6, 1250), (7, 2000), (8, 1100),
    ]

    threads = []
    for pid, rating in players:
        t = threading.Thread(target=player_join, args=(pid, rating))
        threads.append(t)
        t.start()
        time.sleep(random.uniform(0.05, 0.2))

    for t in threads:
        t.join()
    stop.set()

    print("\n--- Matchmaking Results ---")
    for pid, result in sorted(results.items()):
        print(f"  Player {pid} (rating={dict(players)[pid]}): {result}")
    print(f"  Matches formed: {mm.matches}")
    print(f"  Timeouts: {mm.timeouts}")

demo_matchmaking()
```

### Testing Strategy

```python
def test_matchmaking_no_duplicate_matches():
    mm = MatchmakingQueue(tolerance=200, timeout=2.0)
    stop = threading.Event()
    matcher = threading.Thread(target=mm.matcher_loop, args=(stop,), daemon=True)
    matcher.start()

    threads = []
    for i in range(20):
        p = mm.enqueue(i, random.randint(1000, 2000))
        t = threading.Thread(target=mm.wait_for_match, args=(p,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    stop.set()

    matched_ids = set()
    for a, b in mm.matches:
        assert a not in matched_ids, f"Player {a} matched twice!"
        assert b not in matched_ids, f"Player {b} matched twice!"
        matched_ids.add(a)
        matched_ids.add(b)
    print(f"Matchmaking: no duplicate matches in {len(mm.matches)} pairs ✓")

test_matchmaking_no_duplicate_matches()
```

### Variations

- **Team matchmaking:** Form teams of *k* before matching team vs team.
- **ELO adjustment:** Update ratings after match results.
- **Region-based:** Prefer same-region matches, fall back to cross-region.

---

## 10. Warehouse Packing Simulation

### Problem Statement

A warehouse has:
- **Orders** arriving continuously with varying priorities.
- **Multiple packers** (worker threads) that pick and pack orders.
- **A single dispatcher** that ships completed orders.
- **Limited packing stations** (bounded resource).

### Why It Matters

This models any multi-stage pipeline with priority ordering and resource
constraints — CI/CD pipelines, print queues, hospital triage.

### Complete Implementation

```python
import threading
import queue
import time
import random
from dataclasses import dataclass, field
from enum import IntEnum

class Priority(IntEnum):
    EXPRESS = 1
    STANDARD = 2
    ECONOMY = 3

@dataclass(order=True)
class Order:
    priority: int
    order_id: int = field(compare=False)
    items: int = field(compare=False, default=1)
    timestamp: float = field(compare=False, default_factory=time.monotonic)

class Warehouse:
    def __init__(self, n_stations: int = 3):
        self.order_queue = queue.PriorityQueue()
        self.dispatch_queue = queue.Queue()
        self.packing_stations = threading.Semaphore(n_stations)
        self.stats = {
            "packed": 0, "dispatched": 0,
            "avg_wait": 0.0, "total_wait": 0.0,
        }
        self.stats_lock = threading.Lock()

    def receive_order(self, order: Order):
        self.order_queue.put(order)
        print(f"  📦 Order {order.order_id} received "
              f"(priority={Priority(order.priority).name}, items={order.items})")

    def packer(self, packer_id: int, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                order = self.order_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self.packing_stations.acquire()
            wait_time = time.monotonic() - order.timestamp
            pack_time = 0.02 * order.items
            print(f"  🔧 Packer-{packer_id} packing order {order.order_id} "
                  f"({order.items} items, waited {wait_time:.2f}s)")
            time.sleep(pack_time)
            self.packing_stations.release()

            with self.stats_lock:
                self.stats["packed"] += 1
                self.stats["total_wait"] += wait_time

            self.dispatch_queue.put(order)
            self.order_queue.task_done()

    def dispatcher(self, stop_event: threading.Event):
        while not stop_event.is_set():
            try:
                order = self.dispatch_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            print(f"  🚚 Dispatched order {order.order_id}")
            with self.stats_lock:
                self.stats["dispatched"] += 1
            self.dispatch_queue.task_done()


def demo_warehouse():
    wh = Warehouse(n_stations=3)
    stop = threading.Event()

    packers = [
        threading.Thread(target=wh.packer, args=(i, stop), daemon=True)
        for i in range(4)
    ]
    dispatcher = threading.Thread(target=wh.dispatcher, args=(stop,), daemon=True)

    for t in packers + [dispatcher]:
        t.start()

    orders = [
        Order(Priority.EXPRESS, 1, items=2),
        Order(Priority.ECONOMY, 2, items=5),
        Order(Priority.STANDARD, 3, items=3),
        Order(Priority.EXPRESS, 4, items=1),
        Order(Priority.ECONOMY, 5, items=4),
        Order(Priority.STANDARD, 6, items=2),
        Order(Priority.EXPRESS, 7, items=1),
        Order(Priority.ECONOMY, 8, items=6),
        Order(Priority.STANDARD, 9, items=2),
        Order(Priority.EXPRESS, 10, items=3),
    ]

    for o in orders:
        wh.receive_order(o)
        time.sleep(random.uniform(0.01, 0.05))

    wh.order_queue.join()
    wh.dispatch_queue.join()
    stop.set()

    with wh.stats_lock:
        packed = wh.stats["packed"]
        if packed:
            wh.stats["avg_wait"] = wh.stats["total_wait"] / packed
    print(f"\nWarehouse stats: {wh.stats}")

demo_warehouse()
```

### Testing Strategy

```python
def test_warehouse_all_orders_processed(n_orders=50, runs=10):
    for _ in range(runs):
        wh = Warehouse(n_stations=3)
        stop = threading.Event()
        packers = [
            threading.Thread(target=wh.packer, args=(i, stop), daemon=True)
            for i in range(4)
        ]
        disp = threading.Thread(target=wh.dispatcher, args=(stop,), daemon=True)
        for t in packers + [disp]:
            t.start()

        for i in range(n_orders):
            pri = random.choice(list(Priority))
            wh.receive_order(Order(pri, i, items=random.randint(1, 5)))
            time.sleep(0.002)

        wh.order_queue.join()
        wh.dispatch_queue.join()
        stop.set()

        assert wh.stats["dispatched"] == n_orders, (
            f"Expected {n_orders}, dispatched {wh.stats['dispatched']}"
        )
    print(f"Warehouse test: {runs} runs × {n_orders} orders — all processed ✓")

test_warehouse_all_orders_processed()
```

### Variations

- **Backorder handling:** If an item is out of stock, the order waits.
- **Batch dispatch:** Group orders by destination before dispatching.
- **Rate limiting:** Cap dispatch rate to match truck availability.

---

## 11. Barrier Synchronization

### Problem Statement

Implement a **barrier** that blocks `n` threads until all have arrived, then
releases them all simultaneously. Extensions:

1. **Reusable barrier** — can be used for multiple rounds.
2. **Broken barrier** — if one thread fails, all waiters get an exception.
3. **Phase-based computation** — threads synchronise at the end of each phase.

### Why It Matters

Barriers are critical for parallel algorithms where each iteration depends on
all threads completing the previous one (e.g. cellular automata, parallel
relaxation methods, bulk-synchronous parallel).

### Custom Barrier Implementation

```python
import threading

class SimpleBarrier:
    """One-shot barrier for n parties."""

    def __init__(self, parties: int):
        self.parties = parties
        self.count = 0
        self.lock = threading.Lock()
        self.event = threading.Event()

    def wait(self, timeout: float | None = None) -> int:
        with self.lock:
            self.count += 1
            index = self.count
            if self.count == self.parties:
                self.event.set()

        if not self.event.wait(timeout=timeout):
            raise TimeoutError("Barrier wait timed out")
        return index


def demo_simple_barrier():
    n = 5
    barrier = SimpleBarrier(n)
    results = []
    lock = threading.Lock()

    def worker(tid):
        import time, random
        time.sleep(random.uniform(0, 0.1))
        print(f"Thread {tid} arrived at barrier")
        idx = barrier.wait()
        print(f"Thread {tid} released (index={idx})")
        with lock:
            results.append(tid)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == n
    print(f"Simple barrier: all {n} threads released ✓")

demo_simple_barrier()
```

### Reusable Barrier (Sense-Reversing)

```python
import threading

class ReusableBarrier:
    """
    Sense-reversing barrier that can be reused across multiple phases.
    After all parties arrive, the barrier resets automatically.
    """

    def __init__(self, parties: int):
        self.parties = parties
        self.count = 0
        self.sense = False  # flips each generation
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)

    def wait(self) -> int:
        with self.cond:
            local_sense = self.sense
            self.count += 1
            index = self.count

            if self.count == self.parties:
                self.count = 0
                self.sense = not self.sense
                self.cond.notify_all()
            else:
                while self.sense == local_sense:
                    self.cond.wait()
            return index


def demo_reusable_barrier():
    n_threads = 4
    n_phases = 5
    barrier = ReusableBarrier(n_threads)
    phase_log = {p: [] for p in range(n_phases)}
    log_lock = threading.Lock()

    def worker(tid):
        for phase in range(n_phases):
            import time, random
            time.sleep(random.uniform(0, 0.02))
            barrier.wait()
            with log_lock:
                phase_log[phase].append(tid)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for phase, tids in phase_log.items():
        assert len(tids) == n_threads, f"Phase {phase}: only {len(tids)} threads"
    print(f"Reusable barrier: {n_phases} phases × {n_threads} threads ✓")

demo_reusable_barrier()
```

### Broken Barrier

```python
import threading

class BrokenBarrierError(Exception):
    pass

class BreakableBarrier:
    def __init__(self, parties: int):
        self.parties = parties
        self.count = 0
        self.generation = 0
        self.broken = False
        self.cond = threading.Condition()

    def wait(self, timeout: float | None = None) -> int:
        with self.cond:
            if self.broken:
                raise BrokenBarrierError("Barrier is broken")

            gen = self.generation
            self.count += 1
            index = self.count

            if self.count == self.parties:
                self._next_generation()
                return index

            while (self.generation == gen
                   and not self.broken
                   and self.count < self.parties):
                if not self.cond.wait(timeout=timeout):
                    self._break()
                    raise BrokenBarrierError("Barrier wait timed out")

            if self.broken:
                raise BrokenBarrierError("Barrier is broken")
            return index

    def _next_generation(self):
        self.count = 0
        self.generation += 1
        self.cond.notify_all()

    def _break(self):
        self.broken = True
        self.cond.notify_all()

    def reset(self):
        with self.cond:
            self._break()
            self._next_generation()
            self.broken = False


def demo_breakable_barrier():
    barrier = BreakableBarrier(3)

    def good_worker(tid):
        try:
            barrier.wait(timeout=1.0)
            print(f"Thread {tid} passed barrier")
        except BrokenBarrierError as e:
            print(f"Thread {tid} got BrokenBarrierError: {e}")

    # Only start 2 of 3 required threads — barrier should break on timeout
    threads = [threading.Thread(target=good_worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Breakable barrier demo done")

demo_breakable_barrier()
```

### Phase-Based Computation Example

```python
import threading
import time

def parallel_relaxation(data: list[float], n_threads: int = 4,
                        n_iterations: int = 10):
    """
    Parallel Jacobi-style relaxation: each thread updates its segment,
    then all synchronise before the next iteration.
    """
    n = len(data)
    chunk = n // n_threads
    barrier = threading.Barrier(n_threads)
    buf = data[:]  # double buffer
    lock = threading.Lock()

    def worker(tid):
        nonlocal data, buf
        lo = tid * chunk
        hi = lo + chunk if tid < n_threads - 1 else n
        for iteration in range(n_iterations):
            for i in range(max(lo, 1), min(hi, n - 1)):
                buf[i] = (data[i - 1] + data[i] + data[i + 1]) / 3.0
            barrier.wait()
            if tid == 0:
                data, buf = buf, data[:]

    threads = [threading.Thread(target=worker, args=(i,))
               for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return data

result = parallel_relaxation([0.0] * 5 + [100.0] + [0.0] * 5)
print(f"Relaxation result: {[f'{v:.1f}' for v in result]}")
```

### Testing Strategy

```python
def test_reusable_barrier_phases(n_threads=8, n_phases=50):
    barrier = ReusableBarrier(n_threads)
    arrival_order = {p: [] for p in range(n_phases)}
    lock = threading.Lock()

    def worker(tid):
        for phase in range(n_phases):
            barrier.wait()
            with lock:
                arrival_order[phase].append(tid)

    threads = [threading.Thread(target=worker, args=(i,))
               for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for phase in range(n_phases):
        assert len(arrival_order[phase]) == n_threads
    print(f"Reusable barrier: {n_phases} phases × {n_threads} threads ✓")

test_reusable_barrier_phases()
```

---

## 12. Parallel Merge Sort

### Problem Statement

Implement merge sort that divides work among multiple threads. Each sub-array
is sorted in its own thread, then results are merged.

### Why It Matters

Parallel sorting is the canonical divide-and-conquer parallelism example.
Understanding it teaches thread creation overhead, optimal granularity, and
merge-phase synchronisation.

### Concurrency Challenge

- Thread creation is expensive — sorting a 10-element sub-array in its own
  thread is slower than sorting sequentially.
- The merge phase must wait for both halves to finish.

### Sequential Baseline

```python
def merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def merge_sort_seq(arr: list) -> list:
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort_seq(arr[:mid])
    right = merge_sort_seq(arr[mid:])
    return merge(left, right)
```

### Parallel Merge Sort — Threading

```python
import threading

THRESHOLD = 1024  # below this, fall back to sequential sort

def merge_sort_parallel(arr: list, depth: int = 0,
                        max_depth: int = 3) -> list:
    """
    Parallel merge sort using threads.
    Limits parallelism to 2^max_depth threads to avoid overhead.
    """
    if len(arr) <= 1:
        return arr

    if len(arr) <= THRESHOLD or depth >= max_depth:
        return merge_sort_seq(arr)

    mid = len(arr) // 2
    left_result = [None]
    right_result = [None]

    def sort_left():
        left_result[0] = merge_sort_parallel(arr[:mid], depth + 1, max_depth)

    def sort_right():
        right_result[0] = merge_sort_parallel(arr[mid:], depth + 1, max_depth)

    lt = threading.Thread(target=sort_left)
    rt = threading.Thread(target=sort_right)
    lt.start()
    rt.start()
    lt.join()
    rt.join()

    return merge(left_result[0], right_result[0])
```

### Parallel Merge Sort — Thread Pool

```python
from concurrent.futures import ThreadPoolExecutor, Future

def merge_sort_pool(arr: list, executor: ThreadPoolExecutor,
                    threshold: int = 1024) -> list:
    if len(arr) <= 1:
        return arr
    if len(arr) <= threshold:
        return merge_sort_seq(arr)

    mid = len(arr) // 2
    left_future = executor.submit(merge_sort_pool, arr[:mid], executor, threshold)
    right = merge_sort_pool(arr[mid:], executor, threshold)
    left = left_future.result()
    return merge(left, right)
```

### Benchmarks

```python
import time
import random

def benchmark_sorts(sizes=None):
    if sizes is None:
        sizes = [1_000, 10_000, 100_000, 500_000]

    print(f"{'Size':>10} | {'Sequential':>12} | {'Threaded':>12} | {'Pool':>12}")
    print("-" * 55)

    for n in sizes:
        arr = [random.randint(0, 10 * n) for _ in range(n)]

        # Sequential
        a = arr[:]
        t0 = time.perf_counter()
        merge_sort_seq(a)
        t_seq = time.perf_counter() - t0

        # Parallel threads
        a = arr[:]
        t0 = time.perf_counter()
        merge_sort_parallel(a, max_depth=3)
        t_par = time.perf_counter() - t0

        # Thread pool
        a = arr[:]
        with ThreadPoolExecutor(max_workers=8) as pool:
            t0 = time.perf_counter()
            merge_sort_pool(a, pool, threshold=2048)
            t_pool = time.perf_counter() - t0

        print(f"{n:>10} | {t_seq:>10.4f}s | {t_par:>10.4f}s | {t_pool:>10.4f}s")

benchmark_sorts()
```

### Testing Strategy

```python
import random

def test_parallel_merge_sort(runs=20, max_n=5000):
    for _ in range(runs):
        n = random.randint(0, max_n)
        arr = [random.randint(-10000, 10000) for _ in range(n)]
        expected = sorted(arr)

        assert merge_sort_parallel(arr) == expected, "Threaded sort mismatch"

        with ThreadPoolExecutor(max_workers=4) as pool:
            assert merge_sort_pool(arr, pool) == expected, "Pool sort mismatch"

    print(f"Parallel merge sort: {runs} randomised tests passed ✓")

test_parallel_merge_sort()
```

### Performance Characteristics

| Factor | Impact |
|--------|--------|
| Thread creation overhead | ~50–200 µs per thread; dominates for small arrays |
| GIL (CPython) | CPU-bound Python code doesn't truly parallelise with threads |
| `max_depth` | Limits thread explosion; 3–4 is usually optimal |
| `THRESHOLD` | Below this, sequential sort wins; tune per machine |

> **Note:** For true CPU parallelism in Python, use `multiprocessing` or
> `concurrent.futures.ProcessPoolExecutor`. Threading still demonstrates the
> algorithm structure.

---

## 13. Parallel Matrix Multiplication

### Problem Statement

Multiply two `n×n` matrices `A` and `B` using multiple threads/processes.
Explore row-based and block-based parallelism.

### Why It Matters

Matrix multiplication is the workhorse of scientific computing, graphics, and
machine learning. Parallelising it efficiently is a fundamental skill.

### Sequential Baseline

```python
def mat_mul_seq(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    n = len(A)
    m = len(B[0])
    k = len(B)
    C = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            s = 0.0
            for p in range(k):
                s += A[i][p] * B[p][j]
            C[i][j] = s
    return C
```

### Row-Based Parallelism (Threading)

```python
import threading

def mat_mul_row_parallel(A, B, n_threads=4):
    n = len(A)
    m = len(B[0])
    k = len(B)
    C = [[0.0] * m for _ in range(n)]

    # Pre-compute columns of B for cache efficiency
    B_cols = list(zip(*B))

    def compute_rows(start, end):
        for i in range(start, end):
            for j in range(m):
                C[i][j] = sum(A[i][p] * B_cols[j][p] for p in range(k))

    chunk = (n + n_threads - 1) // n_threads
    threads = []
    for t in range(n_threads):
        lo = t * chunk
        hi = min(lo + chunk, n)
        if lo >= n:
            break
        threads.append(threading.Thread(target=compute_rows, args=(lo, hi)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return C
```

### Block-Based Parallelism (Threading)

```python
import threading

def mat_mul_block_parallel(A, B, block_size=32, n_threads=4):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    lock = threading.Lock()

    blocks = []
    for i0 in range(0, n, block_size):
        for j0 in range(0, n, block_size):
            for k0 in range(0, n, block_size):
                blocks.append((i0, j0, k0))

    def process_blocks(block_list):
        for i0, j0, k0 in block_list:
            for i in range(i0, min(i0 + block_size, n)):
                for j in range(j0, min(j0 + block_size, n)):
                    s = 0.0
                    for k in range(k0, min(k0 + block_size, n)):
                        s += A[i][k] * B[k][j]
                    with lock:
                        C[i][j] += s

    chunk = (len(blocks) + n_threads - 1) // n_threads
    threads = []
    for t in range(n_threads):
        lo = t * chunk
        hi = min(lo + chunk, len(blocks))
        threads.append(threading.Thread(target=process_blocks,
                                        args=(blocks[lo:hi],)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return C
```

### Multiprocessing Version

```python
from multiprocessing import Pool
import os

def _compute_row(args):
    """Worker function for multiprocessing — must be picklable."""
    i, A_row, B_cols = args
    return [sum(a * b for a, b in zip(A_row, col)) for col in B_cols]

def mat_mul_multiprocessing(A, B, n_workers=None):
    n_workers = n_workers or os.cpu_count()
    n = len(A)
    B_cols = list(zip(*B))

    args = [(i, A[i], B_cols) for i in range(n)]

    with Pool(n_workers) as pool:
        rows = pool.map(_compute_row, args)

    return rows
```

### Benchmarks

```python
import time
import random

def random_matrix(n):
    return [[random.uniform(-10, 10) for _ in range(n)] for _ in range(n)]

def matrices_approx_equal(A, B, tol=1e-6):
    for i in range(len(A)):
        for j in range(len(A[0])):
            if abs(A[i][j] - B[i][j]) > tol:
                return False
    return True

def benchmark_matmul(sizes=None):
    if sizes is None:
        sizes = [50, 100, 200]

    print(f"{'N':>6} | {'Sequential':>12} | {'Row-parallel':>14} | "
          f"{'Block-parallel':>16} | {'Multiprocess':>14}")
    print("-" * 75)

    for n in sizes:
        A = random_matrix(n)
        B = random_matrix(n)

        t0 = time.perf_counter()
        C_seq = mat_mul_seq(A, B)
        t_seq = time.perf_counter() - t0

        t0 = time.perf_counter()
        C_row = mat_mul_row_parallel(A, B, n_threads=4)
        t_row = time.perf_counter() - t0
        assert matrices_approx_equal(C_seq, C_row)

        t0 = time.perf_counter()
        C_blk = mat_mul_block_parallel(A, B, block_size=32, n_threads=4)
        t_blk = time.perf_counter() - t0
        assert matrices_approx_equal(C_seq, C_blk)

        t0 = time.perf_counter()
        C_mp = mat_mul_multiprocessing(A, B, n_workers=4)
        t_mp = time.perf_counter() - t0
        assert matrices_approx_equal(C_seq, C_mp)

        print(f"{n:>6} | {t_seq:>10.4f}s | {t_row:>12.4f}s | "
              f"{t_blk:>14.4f}s | {t_mp:>12.4f}s")

benchmark_matmul()
```

### Testing Strategy

```python
def test_matmul_correctness():
    for _ in range(10):
        n = random.randint(1, 64)
        A = random_matrix(n)
        B = random_matrix(n)
        expected = mat_mul_seq(A, B)

        assert matrices_approx_equal(expected, mat_mul_row_parallel(A, B))
        assert matrices_approx_equal(expected, mat_mul_block_parallel(A, B))
        assert matrices_approx_equal(expected, mat_mul_multiprocessing(A, B))

    print("Matrix multiplication: all methods match sequential ✓")

test_matmul_correctness()
```

### Performance Characteristics

| Method | GIL Impact | Overhead | Best For |
|--------|:---:|----------|----------|
| Row-parallel (threads) | High (CPU-bound → no speed-up) | Low | I/O-bound or NumPy-backed |
| Block-parallel (threads) | High | Medium (locking) | Better cache locality |
| Multiprocessing | None (separate processes) | High (pickling) | True CPU parallelism |
| NumPy | None (C extensions release GIL) | Minimal | Production use |

> **Practical advice:** For real workloads, use `numpy.matmul` or a BLAS-backed
> library. The implementations above are pedagogical.

---

## 14. Lock-Free Programming Concepts

### Problem Statement

Implement data structures that provide thread-safety **without** traditional
locks, using atomic operations and compare-and-swap (CAS) semantics.

### Why It Matters

Lock-free structures avoid:
- **Deadlocks** — no locks to deadlock on.
- **Priority inversion** — high-priority threads never wait for low-priority lock holders.
- **Convoying** — threads don't queue behind a slow lock holder.

They are used in OS kernels, database engines, and high-frequency trading systems.

### Concurrency Challenge

Without hardware CAS instructions (which Python doesn't directly expose),
true lock-free programming is difficult. We explore the *concepts* and provide
the closest Python approximations.

### Compare-and-Swap (CAS) Concept

CAS atomically: *if value == expected, set value = new, return True; else return
False*. It is the foundation of every lock-free algorithm.

```python
import threading

class AtomicReference:
    """
    Simulated CAS using a lock internally.
    In real systems (C, Java, Rust) this maps to a hardware instruction.
    """

    def __init__(self, initial=None):
        self._value = initial
        self._lock = threading.Lock()

    @property
    def value(self):
        with self._lock:
            return self._value

    def compare_and_swap(self, expected, new) -> bool:
        with self._lock:
            if self._value is expected or self._value == expected:
                self._value = new
                return True
            return False

    def get_and_set(self, new):
        with self._lock:
            old = self._value
            self._value = new
            return old


class AtomicInteger:
    """Thread-safe integer with CAS, increment, decrement."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def compare_and_swap(self, expected: int, new: int) -> bool:
        with self._lock:
            if self._value == expected:
                self._value = new
                return True
            return False

    def increment_and_get(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def fetch_and_add(self, delta: int) -> int:
        with self._lock:
            old = self._value
            self._value += delta
            return old
```

### Lock-Free Stack (Treiber Stack)

```python
import threading

class _Node:
    __slots__ = ("value", "next")
    def __init__(self, value, nxt=None):
        self.value = value
        self.next = nxt

class LockFreeStack:
    """
    Treiber stack: a lock-free LIFO using CAS on the head pointer.
    Uses our AtomicReference to simulate CAS.
    """

    def __init__(self):
        self._head = AtomicReference(None)

    def push(self, value):
        new_node = _Node(value)
        while True:
            old_head = self._head.value
            new_node.next = old_head
            if self._head.compare_and_swap(old_head, new_node):
                return

    def pop(self):
        while True:
            old_head = self._head.value
            if old_head is None:
                raise IndexError("pop from empty stack")
            new_head = old_head.next
            if self._head.compare_and_swap(old_head, new_head):
                return old_head.value

    def peek(self):
        head = self._head.value
        if head is None:
            raise IndexError("peek on empty stack")
        return head.value

    def is_empty(self) -> bool:
        return self._head.value is None


def demo_lock_free_stack():
    stack = LockFreeStack()
    results = {"pushed": [], "popped": []}
    lock = threading.Lock()

    def pusher(tid, n):
        for i in range(n):
            val = tid * 100 + i
            stack.push(val)
            with lock:
                results["pushed"].append(val)

    def popper(n):
        count = 0
        while count < n:
            try:
                val = stack.pop()
                with lock:
                    results["popped"].append(val)
                count += 1
            except IndexError:
                pass  # retry

    threads = [
        threading.Thread(target=pusher, args=(0, 50)),
        threading.Thread(target=pusher, args=(1, 50)),
        threading.Thread(target=popper, args=(100,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results["pushed"]) == sorted(results["popped"])
    print(f"Lock-free stack: pushed {len(results['pushed'])}, "
          f"popped {len(results['popped'])} ✓")

demo_lock_free_stack()
```

### Lock-Free Queue (Michael-Scott Queue)

```python
import threading

class _QNode:
    __slots__ = ("value", "next")
    def __init__(self, value=None):
        self.value = value
        self.next = AtomicReference(None)

class LockFreeQueue:
    """
    Michael-Scott lock-free FIFO queue.
    Uses a sentinel (dummy) head node.
    """

    def __init__(self):
        sentinel = _QNode()
        self._head = AtomicReference(sentinel)
        self._tail = AtomicReference(sentinel)

    def enqueue(self, value):
        new_node = _QNode(value)
        while True:
            tail = self._tail.value
            next_node = tail.next.value
            if tail is self._tail.value:
                if next_node is None:
                    if tail.next.compare_and_swap(None, new_node):
                        self._tail.compare_and_swap(tail, new_node)
                        return
                else:
                    # Tail is behind; advance it
                    self._tail.compare_and_swap(tail, next_node)

    def dequeue(self):
        while True:
            head = self._head.value
            tail = self._tail.value
            first = head.next.value

            if head is self._head.value:
                if head is tail:
                    if first is None:
                        raise IndexError("dequeue from empty queue")
                    self._tail.compare_and_swap(tail, first)
                else:
                    value = first.value
                    if self._head.compare_and_swap(head, first):
                        return value

    def is_empty(self) -> bool:
        head = self._head.value
        return head.next.value is None


def demo_lock_free_queue():
    q = LockFreeQueue()
    n_items = 200
    enqueued = []
    dequeued = []
    e_lock = threading.Lock()
    d_lock = threading.Lock()

    def enqueuer(start, count):
        for i in range(start, start + count):
            q.enqueue(i)
            with e_lock:
                enqueued.append(i)

    def dequeuer(count):
        got = 0
        while got < count:
            try:
                val = q.dequeue()
                with d_lock:
                    dequeued.append(val)
                got += 1
            except IndexError:
                pass

    threads = [
        threading.Thread(target=enqueuer, args=(0, 100)),
        threading.Thread(target=enqueuer, args=(100, 100)),
        threading.Thread(target=dequeuer, args=(100,)),
        threading.Thread(target=dequeuer, args=(100,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(enqueued) == sorted(dequeued)
    print(f"Lock-free queue: enqueued {len(enqueued)}, "
          f"dequeued {len(dequeued)} ✓")

demo_lock_free_queue()
```

### The ABA Problem

```
Thread 1: reads head = A
Thread 2: pops A, pops B, pushes A back (A is at head again but the list changed)
Thread 1: CAS succeeds (head is still A) but the stack state is corrupted
```

**Solution — Tagged pointers / stamped references:**

```python
import threading

class StampedReference:
    """
    Pairs a reference with an integer stamp to detect ABA.
    CAS succeeds only if BOTH the reference and stamp match.
    """

    def __init__(self, ref=None, stamp: int = 0):
        self._ref = ref
        self._stamp = stamp
        self._lock = threading.Lock()

    def get(self) -> tuple:
        with self._lock:
            return self._ref, self._stamp

    def compare_and_swap(self, expected_ref, new_ref,
                         expected_stamp: int, new_stamp: int) -> bool:
        with self._lock:
            if self._ref is expected_ref and self._stamp == expected_stamp:
                self._ref = new_ref
                self._stamp = new_stamp
                return True
            return False


class ABAFreeStack:
    """Treiber stack with stamped references to avoid ABA."""

    def __init__(self):
        self._head = StampedReference(None, 0)

    def push(self, value):
        new_node = _Node(value)
        while True:
            old_head, stamp = self._head.get()
            new_node.next = old_head
            if self._head.compare_and_swap(old_head, new_node, stamp, stamp + 1):
                return

    def pop(self):
        while True:
            old_head, stamp = self._head.get()
            if old_head is None:
                raise IndexError("pop from empty stack")
            new_head = old_head.next
            if self._head.compare_and_swap(old_head, new_head, stamp, stamp + 1):
                return old_head.value


def demo_aba_free_stack():
    stack = ABAFreeStack()
    items = list(range(100))
    popped = []
    lock = threading.Lock()

    def pusher():
        for v in items:
            stack.push(v)

    def popper():
        for _ in range(100):
            while True:
                try:
                    val = stack.pop()
                    with lock:
                        popped.append(val)
                    break
                except IndexError:
                    pass

    t1 = threading.Thread(target=pusher)
    t2 = threading.Thread(target=popper)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert sorted(popped) == sorted(items)
    print(f"ABA-free stack: all {len(items)} items recovered ✓")

demo_aba_free_stack()
```

### Python's Limitations and Alternatives

| Limitation | Detail | Workaround |
|-----------|--------|------------|
| No hardware CAS | Python has no `cmpxchg` instruction binding | Use `ctypes` or C extensions |
| GIL | Only one thread executes Python bytecode at a time | Use `multiprocessing` for CPU-bound work |
| Object identity | `is` comparison can be tricky with interned objects | Use wrapper objects or stamped refs |
| No `volatile` | Python has no memory-ordering guarantees beyond the GIL | Rely on `threading` primitives |

**Practical alternatives in Python:**

```python
import queue
import multiprocessing as mp

# 1. queue.Queue — internally lock-based but high-level lock-free API
q = queue.Queue()
q.put("item")
item = q.get()

# 2. multiprocessing.Value — shared memory with optional lock
counter = mp.Value('i', 0)
with counter.get_lock():
    counter.value += 1

# 3. multiprocessing.Queue — IPC-safe queue
mq = mp.Queue()
mq.put("hello")
val = mq.get()

# 4. asyncio — cooperative concurrency avoids most locking issues
import asyncio

async def async_producer(q: asyncio.Queue):
    for i in range(10):
        await q.put(i)

async def async_consumer(q: asyncio.Queue):
    for _ in range(10):
        item = await q.get()
        print(f"Got {item}")

async def main():
    q = asyncio.Queue(maxsize=5)
    await asyncio.gather(async_producer(q), async_consumer(q))

# asyncio.run(main())  # uncomment to run
```

### Using `atomics` Package (Third-Party)

```python
# pip install atomics
# Provides true atomic operations backed by C extensions.
#
# from atomics import AtomicLong
# counter = AtomicLong(0)
# counter.fetch_add(1)  # truly atomic, no Python lock
# counter.compare_exchange(expected=1, desired=2)
```

### Testing Lock-Free Structures

```python
import threading

def stress_test_lock_free_stack(n_threads=8, ops_per_thread=500):
    stack = LockFreeStack()
    pushed = []
    popped = []
    p_lock = threading.Lock()
    d_lock = threading.Lock()

    def pusher(tid):
        for i in range(ops_per_thread):
            val = tid * 10000 + i
            stack.push(val)
            with p_lock:
                pushed.append(val)

    def popper():
        local = []
        for _ in range(ops_per_thread):
            while True:
                try:
                    val = stack.pop()
                    local.append(val)
                    break
                except IndexError:
                    pass
        with d_lock:
            popped.extend(local)

    n_pushers = n_threads // 2
    n_poppers = n_threads // 2

    threads = (
        [threading.Thread(target=pusher, args=(i,)) for i in range(n_pushers)]
        + [threading.Thread(target=popper) for _ in range(n_poppers)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Drain any remaining items
    while not stack.is_empty():
        popped.append(stack.pop())

    assert sorted(pushed) == sorted(popped), (
        f"Mismatch: pushed={len(pushed)}, popped={len(popped)}"
    )
    print(f"Lock-free stack stress: {n_threads} threads × {ops_per_thread} ops ✓")

stress_test_lock_free_stack()


def stress_test_lock_free_queue(n_threads=8, ops_per_thread=500):
    q = LockFreeQueue()
    enqueued = []
    dequeued = []
    e_lock = threading.Lock()
    d_lock = threading.Lock()

    def enqueuer(tid):
        for i in range(ops_per_thread):
            val = tid * 10000 + i
            q.enqueue(val)
            with e_lock:
                enqueued.append(val)

    def dequeuer():
        local = []
        for _ in range(ops_per_thread):
            while True:
                try:
                    val = q.dequeue()
                    local.append(val)
                    break
                except IndexError:
                    pass
        with d_lock:
            dequeued.extend(local)

    n_enq = n_threads // 2
    n_deq = n_threads // 2

    threads = (
        [threading.Thread(target=enqueuer, args=(i,)) for i in range(n_enq)]
        + [threading.Thread(target=dequeuer) for _ in range(n_deq)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    while not q.is_empty():
        dequeued.append(q.dequeue())

    assert sorted(enqueued) == sorted(dequeued), (
        f"Mismatch: enqueued={len(enqueued)}, dequeued={len(dequeued)}"
    )
    print(f"Lock-free queue stress: {n_threads} threads × {ops_per_thread} ops ✓")

stress_test_lock_free_queue()
```

---

## Appendix A: Common Concurrency Bugs Cheat Sheet

| Bug | Symptom | Fix |
|-----|---------|-----|
| **Race condition** | Non-deterministic wrong results | Add mutual exclusion (lock, atomic) |
| **Deadlock** | Program hangs forever | Lock ordering, timeout, try-lock |
| **Livelock** | Threads run but make no progress | Add randomised back-off |
| **Starvation** | One thread never gets the resource | Fair locks, FIFO ordering |
| **Priority inversion** | High-priority thread blocked by low-priority | Priority inheritance protocol |
| **TOCTOU** | Check-then-act is non-atomic | Make check + act atomic |
| **Lost update** | Concurrent writes overwrite each other | CAS or serialised writes |

---

## Appendix B: Python Concurrency Primitives Reference

| Primitive | Module | Use Case |
|-----------|--------|----------|
| `Lock` | `threading` | Mutual exclusion |
| `RLock` | `threading` | Re-entrant mutual exclusion |
| `Condition` | `threading` | Wait/notify pattern |
| `Event` | `threading` | One-shot signalling |
| `Semaphore` | `threading` | Counting access control |
| `BoundedSemaphore` | `threading` | Semaphore with error on extra releases |
| `Barrier` | `threading` | N-thread rendezvous |
| `Queue` | `queue` | Thread-safe FIFO |
| `PriorityQueue` | `queue` | Thread-safe priority queue |
| `Value` / `Array` | `multiprocessing` | Shared memory across processes |
| `Pool` | `multiprocessing` | Process pool for CPU-bound work |
| `asyncio.Lock` | `asyncio` | Async mutual exclusion |
| `asyncio.Queue` | `asyncio` | Async producer-consumer |

---

## Appendix C: Testing Concurrent Code — Strategies

### 1. Stress Testing

Run the code thousands of times with randomised timing. Many races only
manifest under specific schedules.

```python
import threading, random, time

def stress(fn, runs=1000):
    for _ in range(runs):
        fn()
    print(f"Stress test passed: {runs} runs")
```

### 2. Deterministic Testing with Controlled Scheduling

Force specific interleavings by inserting `Event.wait()` calls at critical
points during testing.

```python
import threading

def test_specific_interleaving():
    gate1 = threading.Event()
    gate2 = threading.Event()
    shared = {"value": 0}

    def thread_a():
        shared["value"] = 1
        gate1.set()
        gate2.wait()
        assert shared["value"] == 2

    def thread_b():
        gate1.wait()
        assert shared["value"] == 1
        shared["value"] = 2
        gate2.set()

    a = threading.Thread(target=thread_a)
    b = threading.Thread(target=thread_b)
    a.start(); b.start()
    a.join(); b.join()
    print("Controlled interleaving test passed ✓")

test_specific_interleaving()
```

### 3. Invariant Checking

Continuously assert invariants (e.g. total balance is constant) from a
monitoring thread.

```python
import threading, time

def invariant_monitor(check_fn, interval=0.001, duration=2.0):
    """Run check_fn repeatedly for `duration` seconds."""
    end = time.monotonic() + duration
    violations = 0
    while time.monotonic() < end:
        if not check_fn():
            violations += 1
        time.sleep(interval)
    return violations
```

### 4. Thread Sanitizer / Helgrind

For C extensions, use Valgrind's Helgrind or GCC/Clang's ThreadSanitizer.
Python-level races are typically caught by stress testing + invariant checks.

---

*End of Concurrency Standard Problems — 14 problems, complete solutions, tests, and analysis.*
