# Threading & Concurrency — Python + Go Mastery Guide
> For software engineers cracking interviews and building industry-scale systems

---

## Table of Contents
1. [Mental Model: Concurrency vs Parallelism](#1-mental-model-concurrency-vs-parallelism)
2. [Python GIL — The Most Misunderstood Thing in Threading](#2-python-gil--the-most-misunderstood-thing-in-threading)
3. [Python Threading Primitives](#3-python-threading-primitives)
4. [Python Process vs Thread vs Async](#4-python-process-vs-thread-vs-async)
5. [Go Goroutines & the Runtime Scheduler](#5-go-goroutines--the-runtime-scheduler)
6. [Go Channels — Design Patterns](#6-go-channels--design-patterns)
7. [Synchronization Primitives (Both Languages)](#7-synchronization-primitives-both-languages)
8. [The Deadly Sins: Race, Deadlock, Livelock, Starvation](#8-the-deadly-sins-race-deadlock-livelock-starvation)
9. [Memory Model & Happens-Before](#9-memory-model--happens-before)
10. [Thread Pools & Worker Patterns](#10-thread-pools--worker-patterns)
11. [Producer-Consumer & Pipeline Patterns](#11-producer-consumer--pipeline-patterns)
12. [Fan-Out / Fan-In](#12-fan-out--fan-in)
13. [Context Cancellation & Timeouts](#13-context-cancellation--timeouts)
14. [Rate Limiting & Backpressure](#14-rate-limiting--backpressure)
15. [Atomic Operations & Lock-Free Structures](#15-atomic-operations--lock-free-structures)
16. [Condition Variables — The Hidden Interview Weapon](#16-condition-variables--the-hidden-interview-weapon)
17. [Classic Interview Problems](#17-classic-interview-problems)
18. [Industry-Scale Patterns](#18-industry-scale-patterns)
19. [Debugging Concurrency Bugs](#19-debugging-concurrency-bugs)
20. [Quick-Reference Cheat Sheet](#20-quick-reference-cheat-sheet)

---

## 1. Mental Model: Concurrency vs Parallelism

```
Concurrency  = dealing with many things at once  (structure)
Parallelism  = doing    many things at once  (execution)
```

```
Single Core — Concurrency only:
  Thread A: ████░░░░████░░░░████
  Thread B: ░░░░████░░░░████░░░░
             ← time slicing (OS scheduler) →

Multi Core — Parallelism:
  Core 1: Thread A: ████████████████████
  Core 2: Thread B: ████████████████████
```

**Key interview point:** Go's goroutines give you *concurrency by default*, with *parallelism automatically* when GOMAXPROCS > 1. Python's `threading` gives concurrency for I/O-bound but NOT parallelism for CPU-bound (GIL).

---

## 2. Python GIL — The Most Misunderstood Thing in Threading

### What it is

The **Global Interpreter Lock** is a mutex inside CPython that ensures only one thread executes Python bytecode at a time.

```
Thread 1: ▓▓▓▓░░░░▓▓▓▓░░░░   ← holds GIL, then releases
Thread 2: ░░░░▓▓▓▓░░░░▓▓▓▓   ← waits, then holds
```

### Why it exists

CPython's memory management (reference counting) is NOT thread-safe. The GIL is the coarse lock that makes it safe.

```python
import sys
x = []
# Under the hood: x.__refcount__ += 1  ← NOT atomic without GIL
sys.getrefcount(x)  # 2
```

### The Crucial Rules

| Workload | Python threads help? | Why |
|---|---|---|
| I/O-bound (network, disk) | YES | GIL released during I/O syscalls |
| CPU-bound (computation) | NO | GIL held during bytecode execution |
| C extension (NumPy, etc.) | YES | Extensions can release GIL explicitly |

```python
import threading
import time

# GIL is released during sleep (I/O simulation) — threads actually run in parallel!
def io_task(name):
    print(f"[{name}] start")
    time.sleep(1)   # GIL released here — other threads run
    print(f"[{name}] done")

t1 = threading.Thread(target=io_task, args=("A",))
t2 = threading.Thread(target=io_task, args=("B",))
t1.start(); t2.start()
t1.join();  t2.join()
# Total time: ~1s (concurrent), not 2s (sequential)

# CPU-bound — threads DON'T help
def cpu_task(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

# Two threads both computing: SLOWER than sequential (context switch overhead + GIL contention)
```

### GIL in Python 3.13+ (Free-Threaded Python)

```python
# Python 3.13 experimental: python3.13t --disable-gil
# PEP 703 — making the GIL optional
# Check at runtime:
import sys
print(sys._is_gil_enabled())  # False if disabled
```

### Workarounds for CPU-bound parallelism

```python
# Option 1: multiprocessing (separate processes, separate GIL)
from multiprocessing import Pool

with Pool(4) as p:
    results = p.map(cpu_task, [10**7] * 4)

# Option 2: concurrent.futures ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(cpu_task, 10**7) for _ in range(4)]
    results = [f.result() for f in futs]

# Option 3: Release GIL in C extension (NumPy, Cython, ctypes)
import numpy as np
arr = np.arange(10**7)  # GIL released inside NumPy C code
result = arr.sum()       # parallel with other threads
```

---

## 3. Python Threading Primitives

### 3.1 Thread Lifecycle

```python
import threading

def worker(n):
    print(f"Worker {n}, thread id: {threading.get_ident()}")

# Create
t = threading.Thread(target=worker, args=(42,), daemon=True)
# daemon=True: thread dies when main thread exits (don't use for critical work)

# Start
t.start()

# Join (wait for completion, optional timeout)
t.join(timeout=5.0)

# Check if alive
print(t.is_alive())

# Thread-local storage — each thread gets its own copy
local = threading.local()

def set_local():
    local.value = threading.get_ident()  # unique per thread
    print(local.value)

threading.Thread(target=set_local).start()
threading.Thread(target=set_local).start()
```

### 3.2 Lock (Mutex)

```python
import threading

lock = threading.Lock()
counter = 0

def increment():
    global counter
    for _ in range(100_000):
        with lock:          # acquire + release (exception-safe)
            counter += 1    # critical section

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)  # Always 500000

# Manual acquire/release (avoid — prefer 'with')
lock.acquire()
try:
    counter += 1
finally:
    lock.release()

# Non-blocking acquire
if lock.acquire(blocking=False):
    try:
        # got it
        pass
    finally:
        lock.release()
else:
    # couldn't get lock, do something else
    pass
```

### 3.3 RLock (Reentrant Lock)

```python
# Same thread can acquire multiple times without deadlocking
rlock = threading.RLock()

def recursive(n):
    with rlock:      # acquires (count=1)
        if n > 0:
            with rlock:   # re-acquires (count=2) — OK with RLock, deadlock with Lock!
                recursive(n - 1)
            # count decrements to 1
        # count decrements to 0, fully released
```

### 3.4 Semaphore

```python
# Semaphore: allow N concurrent accesses (count-based lock)
sem = threading.Semaphore(3)  # max 3 threads at once

def access_resource(name):
    with sem:
        print(f"{name} in critical section")
        time.sleep(1)

# BoundedSemaphore: raises ValueError if released more than acquired
bsem = threading.BoundedSemaphore(3)

# Classic use: connection pool
class ConnectionPool:
    def __init__(self, size):
        self._sem = threading.Semaphore(size)
        self._conns = [create_connection() for _ in range(size)]
        self._lock = threading.Lock()

    def acquire(self):
        self._sem.acquire()
        with self._lock:
            return self._conns.pop()

    def release(self, conn):
        with self._lock:
            self._conns.append(conn)
        self._sem.release()
```

### 3.5 Event

```python
# Event: one-shot or reusable signal between threads
event = threading.Event()

def waiter():
    print("Waiting for event...")
    event.wait()           # blocks until set()
    print("Event received!")

def setter():
    time.sleep(1)
    event.set()            # unblocks ALL waiting threads

threading.Thread(target=waiter).start()
threading.Thread(target=setter).start()

# With timeout
signaled = event.wait(timeout=2.0)  # returns True if set, False if timeout

event.clear()  # reset to unset state
event.is_set() # check without blocking
```

### 3.6 Condition Variable

```python
# Condition = Lock + wait/notify mechanism
condition = threading.Condition()
items = []

def consumer():
    with condition:
        while not items:        # ALWAYS use while-loop, not if (spurious wakeups!)
            condition.wait()    # atomically release lock and sleep
        item = items.pop()
        print(f"Consumed: {item}")

def producer():
    with condition:
        items.append(42)
        condition.notify()      # wake ONE waiter
        # condition.notify_all()  # wake ALL waiters

threading.Thread(target=consumer).start()
time.sleep(0.1)
threading.Thread(target=producer).start()
```

### 3.7 Barrier

```python
# Barrier: all threads must reach the barrier before any can proceed
barrier = threading.Barrier(3)  # 3 threads must call wait()

def phase_work(name):
    print(f"{name}: Phase 1 done")
    barrier.wait()  # blocks until all 3 arrive
    print(f"{name}: Phase 2 starting")

for name in ["A", "B", "C"]:
    threading.Thread(target=phase_work, args=(name,)).start()
```

### 3.8 Queue (Thread-Safe)

```python
from queue import Queue, LifoQueue, PriorityQueue, SimpleQueue
import queue

q = Queue(maxsize=10)  # maxsize=0 means unlimited

# Producer
q.put(item)            # blocks if full
q.put_nowait(item)     # raises queue.Full if full
q.put(item, timeout=1) # raises queue.Full after timeout

# Consumer
item = q.get()          # blocks if empty
item = q.get_nowait()   # raises queue.Empty
item = q.get(timeout=1) # raises queue.Empty after timeout

# Signaling completion
q.task_done()           # called by consumer after processing
q.join()                # blocks until all items have task_done() called

# PriorityQueue items: (priority, data) — lower number = higher priority
pq = PriorityQueue()
pq.put((1, "high"))
pq.put((3, "low"))
pq.put((2, "medium"))
print(pq.get())  # (1, 'high')
```

---

## 4. Python Process vs Thread vs Async

```
                Threading    Multiprocessing    asyncio
GIL affected?     YES              NO              NO (single thread)
Memory shared?    YES              NO (copy-on-write)  YES (single thread)
I/O-bound?       GREAT           GOOD             EXCELLENT
CPU-bound?        BAD             GREAT            BAD
Overhead?         Low             High (fork/spawn)  Minimal
Switch cost?      OS scheduler    OS scheduler     Cooperative (yield)
```

```python
# concurrent.futures — unified API for both
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests

urls = ["http://example.com"] * 10

# I/O bound — use threads
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(requests.get, url): url for url in urls}
    for fut in as_completed(futs):
        url = futs[fut]
        try:
            resp = fut.result()
            print(f"{url}: {resp.status_code}")
        except Exception as e:
            print(f"{url} failed: {e}")

# CPU bound — use processes
from concurrent.futures import ProcessPoolExecutor

def crunch(n):
    return sum(i*i for i in range(n))

with ProcessPoolExecutor() as ex:
    results = list(ex.map(crunch, [10**6] * 4))
```

### asyncio vs threading

```python
# asyncio — cooperative multitasking (one thread, explicit yield points)
import asyncio

async def fetch(url):
    await asyncio.sleep(1)   # yield point — other coroutines run here
    return f"result from {url}"

async def main():
    # Concurrent fetches in single thread
    tasks = [fetch(url) for url in ["a.com", "b.com", "c.com"]]
    results = await asyncio.gather(*tasks)
    print(results)

asyncio.run(main())

# Mix asyncio with threads for CPU work
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def hybrid():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        # Run CPU-bound in thread, await result
        result = await loop.run_in_executor(pool, cpu_task, 10**7)
    return result
```

---

## 5. Go Goroutines & the Runtime Scheduler

### 5.1 Goroutine Basics

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done()  // CRITICAL: always defer Done() first thing
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    var wg sync.WaitGroup

    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go worker(i, &wg)  // goroutine: ~2KB stack, grows dynamically
    }

    wg.Wait()  // blocks until all Done() calls
    fmt.Println("All workers finished")
}
```

### 5.2 The Go Scheduler (GMP Model)

```
G = Goroutine  (lightweight thread, ~2KB stack)
M = Machine    (OS thread)
P = Processor  (logical CPU, has run queue)

         P1                   P2
    ┌─────────┐          ┌─────────┐
    │ RunQueue│          │ RunQueue│
    │ G3 G4   │          │ G5 G6   │
    └────┬────┘          └────┬────┘
         │                   │
        M1                  M2
    (OS Thread)         (OS Thread)

Work stealing: P2 steals from P1's queue when idle
GOMAXPROCS: number of P's (defaults to num CPU cores)
```

```go
import "runtime"

// Set parallelism
runtime.GOMAXPROCS(4)  // use 4 OS threads

// Yield scheduler (cooperative hint)
runtime.Gosched()

// Number of goroutines
n := runtime.NumGoroutine()
```

### 5.3 Goroutine Gotchas

```go
// GOTCHA 1: Loop variable capture (classic bug — fixed in Go 1.22)
// Go < 1.22:
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i)  // BUG: all goroutines capture same 'i', likely prints 5,5,5,5,5
    }()
}

// Fix (pre-1.22):
for i := 0; i < 5; i++ {
    i := i  // shadow with new variable
    go func() {
        fmt.Println(i)  // CORRECT: each goroutine has its own 'i'
    }()
}

// Or pass as argument:
for i := 0; i < 5; i++ {
    go func(i int) {
        fmt.Println(i)
    }(i)  // copy of i passed at launch time
}

// Go 1.22+: loop variables are per-iteration, bug fixed by default

// GOTCHA 2: Goroutine leak — goroutine blocked forever
func leak() {
    ch := make(chan int)
    go func() {
        val := <-ch  // blocks forever if nothing sends — LEAKED GOROUTINE
        fmt.Println(val)
    }()
    // function returns, ch is garbage collected, goroutine leaks
}

// Fix: use done channel or context
func noLeak(ctx context.Context) {
    ch := make(chan int)
    go func() {
        select {
        case val := <-ch:
            fmt.Println(val)
        case <-ctx.Done():
            return  // properly cleaned up
        }
    }()
}

// GOTCHA 3: Starting goroutine on method with pointer receiver
type S struct{ val int }
func (s *S) Run() { fmt.Println(s.val) }

s := &S{val: 42}
go s.Run()   // CORRECT — s is evaluated now
// NOT: go (*s).Run  — might be different instance
```

---

## 6. Go Channels — Design Patterns

### 6.1 Channel Fundamentals

```go
// Unbuffered: sender blocks until receiver ready (synchronous)
ch := make(chan int)

// Buffered: sender blocks only when buffer full (async up to capacity)
ch := make(chan int, 10)

// Directional channel types (for function signatures)
func producer(out chan<- int) { out <- 42 }   // send-only
func consumer(in <-chan int)  { v := <-in }   // receive-only

// Close
close(ch)  // sender closes; receiver gets zero value after close

// Check if closed
val, ok := <-ch
if !ok {
    fmt.Println("channel closed")
}

// Range over channel (exits when channel closed)
for val := range ch {
    fmt.Println(val)
}

// Select: multiplexing channels
select {
case v := <-ch1:
    fmt.Println("from ch1:", v)
case ch2 <- 42:
    fmt.Println("sent to ch2")
case <-time.After(1 * time.Second):
    fmt.Println("timeout")
default:
    fmt.Println("non-blocking — no channel ready")
}
```

### 6.2 Patterns

**Done channel pattern:**
```go
func worker(done <-chan struct{}) {
    for {
        select {
        case <-done:
            fmt.Println("shutting down")
            return
        default:
            // do work
        }
    }
}

done := make(chan struct{})
go worker(done)
time.Sleep(time.Second)
close(done)  // broadcast to ALL goroutines waiting on done
```

**Pipeline:**
```go
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

// Compose pipeline
nums := generate(2, 3, 4)
squares := square(nums)
for n := range squares {
    fmt.Println(n)  // 4, 9, 16
}
```

**OR-Done pattern (read from channel respecting cancellation):**
```go
func orDone(done, c <-chan interface{}) <-chan interface{} {
    valStream := make(chan interface{})
    go func() {
        defer close(valStream)
        for {
            select {
            case <-done:
                return
            case v, ok := <-c:
                if !ok {
                    return
                }
                select {
                case valStream <- v:
                case <-done:
                }
            }
        }
    }()
    return valStream
}
```

---

## 7. Synchronization Primitives (Both Languages)

### 7.1 Mutex Comparison

```python
# Python
import threading
mu = threading.Lock()

with mu:
    # critical section
    shared_data += 1
```

```go
// Go
import "sync"
var mu sync.Mutex

mu.Lock()
defer mu.Unlock()  // ALWAYS defer to prevent forgetting unlock on error paths
sharedData++
```

### 7.2 RWMutex — Read-heavy workloads

```python
# Python
import threading
rw = threading.Lock()  # Python has no built-in RWLock; use this pattern:

from threading import Lock
class RWLock:
    def __init__(self):
        self._read_lock = Lock()
        self._write_lock = Lock()
        self._readers = 0

    def acquire_read(self):
        with self._read_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self):
        with self._read_lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self):
        self._write_lock.acquire()

    def release_write(self):
        self._write_lock.release()
```

```go
// Go — built-in sync.RWMutex
var rw sync.RWMutex
data := map[string]int{}

// Multiple readers simultaneously
func read(key string) int {
    rw.RLock()
    defer rw.RUnlock()
    return data[key]  // many goroutines can read concurrently
}

// Exclusive write
func write(key string, val int) {
    rw.Lock()
    defer rw.Unlock()
    data[key] = val  // blocks all readers and writers
}
```

### 7.3 sync.Once

```go
// Execute exactly once, even across goroutines — perfect for singleton init
var (
    instance *DB
    once     sync.Once
)

func GetDB() *DB {
    once.Do(func() {
        instance = &DB{conn: connect()}  // called exactly once
    })
    return instance
}

// Thread-safe lazy init, no lock needed after first call
```

```python
# Python equivalent
import threading

_instance = None
_once = threading.Lock()

def get_db():
    global _instance
    if _instance is None:         # double-checked locking
        with _once:
            if _instance is None:
                _instance = DB()
    return _instance
```

### 7.4 sync.Map (Go)

```go
// sync.Map: safe for concurrent use, no external locking needed
// Best for: mostly-read maps with infrequent writes, or disjoint key sets per goroutine
var m sync.Map

// Store
m.Store("key", "value")

// Load
val, ok := m.Load("key")

// LoadOrStore — atomic check-and-set
actual, loaded := m.LoadOrStore("key", "default")

// Delete
m.Delete("key")

// Range — iterate (snapshot-like, not fully consistent)
m.Range(func(k, v interface{}) bool {
    fmt.Println(k, v)
    return true  // return false to stop iteration
})
```

### 7.5 WaitGroup

```go
var wg sync.WaitGroup

for i := 0; i < 10; i++ {
    wg.Add(1)  // MUST call Add BEFORE starting goroutine
    go func(i int) {
        defer wg.Done()
        work(i)
    }(i)
}

wg.Wait()

// GOTCHA: Don't Add inside goroutine!
go func() {
    wg.Add(1)  // RACE: Wait() might finish before this Add()
    defer wg.Done()
    work()
}()
```

---

## 8. The Deadly Sins: Race, Deadlock, Livelock, Starvation

### 8.1 Race Condition

```python
# Python: even += 1 is NOT atomic (it's LOAD, ADD, STORE bytecode ops)
import threading

counter = 0
lock = threading.Lock()

def unsafe_increment():
    global counter
    counter += 1  # RACE CONDITION — use lock!

def safe_increment():
    global counter
    with lock:
        counter += 1
```

```go
// Go: detect races with -race flag
// go run -race main.go
// go test -race ./...

var counter int64

// UNSAFE:
counter++  // data race

// SAFE option 1: mutex
var mu sync.Mutex
mu.Lock()
counter++
mu.Unlock()

// SAFE option 2: atomic
import "sync/atomic"
atomic.AddInt64(&counter, 1)
```

### 8.2 Deadlock

```python
# Classic: two threads, two locks, opposite order
lock1 = threading.Lock()
lock2 = threading.Lock()

def thread_a():
    with lock1:
        time.sleep(0.1)
        with lock2:  # DEADLOCK: waiting for lock2 held by B
            pass

def thread_b():
    with lock2:
        time.sleep(0.1)
        with lock1:  # DEADLOCK: waiting for lock1 held by A
            pass

# Fix: always acquire locks in SAME ORDER
def thread_a_fixed():
    with lock1:
        with lock2:
            pass

def thread_b_fixed():
    with lock1:  # same order as A
        with lock2:
            pass

# Or: use trylock with timeout
if lock1.acquire(timeout=1.0):
    try:
        if lock2.acquire(timeout=1.0):
            try:
                pass  # do work
            finally:
                lock2.release()
        else:
            pass  # back off and retry
    finally:
        lock1.release()
```

```go
// Go deadlock example
func deadlock() {
    ch := make(chan int)
    ch <- 1  // blocks forever — no receiver — Go runtime detects this
    // fatal error: all goroutines are asleep - deadlock!
}

// Fix: buffer or separate goroutine
ch := make(chan int, 1)
ch <- 1  // doesn't block

// Or:
go func() { ch <- 1 }()  // sender in goroutine
val := <-ch
```

### 8.3 Livelock

```go
// Both threads keep responding to each other but make no progress
// Like two people in a hallway stepping aside for each other infinitely

// Pseudocode:
// A: "After you" → moves right
// B: "After you" → moves right (same direction)
// A: "After you" → moves left
// B: "After you" → moves left ... forever

// Fix: randomized backoff
import "math/rand"
import "time"

func tryAcquire(id int, ch chan struct{}) {
    for {
        select {
        case ch <- struct{}{}:
            return
        default:
            // backoff with jitter
            jitter := time.Duration(rand.Intn(100)) * time.Millisecond
            time.Sleep(jitter)
        }
    }
}
```

### 8.4 Starvation

```python
# Starvation: thread can never get lock because others keep taking it
# Common with unfair locks (Python's Lock is NOT fair)

# Fix 1: Use a Queue (inherently fair — FIFO)
from queue import Queue

work_queue = Queue()

def fair_worker():
    while True:
        task = work_queue.get()  # FIFO order
        process(task)
        work_queue.task_done()

# Fix 2: Priority queue with aging (increment priority the longer something waits)
```

---

## 9. Memory Model & Happens-Before

### Python Memory Model

```python
# Python provides sequential consistency WITHIN a thread.
# Between threads: happens-before is established by:
# - lock.acquire() happens-after lock.release()
# - thread.join() happens-after thread's last action
# - queue.get() happens-after queue.put()

x = 0
event = threading.Event()

def writer():
    x = 42        # (1)
    event.set()   # (2) — establishes happens-before with event.wait()

def reader():
    event.wait()  # (3) — happens-after (2)
    print(x)      # (4) — guaranteed to see x=42 due to (1)→(2)→(3)→(4)
```

### Go Memory Model

```go
// Go's memory model: documented at https://go.dev/ref/mem
// Happens-before established by:
// - Channel send happens-before corresponding receive
// - sync.Mutex.Unlock() happens-before next Lock()
// - sync.WaitGroup.Done() happens-before Wait() return
// - sync.Once.Do() completion happens-before any Once.Do() return

var a string

// Safe: channel establishes happens-before
func setup(ch chan<- struct{}) {
    a = "hello"  // (1)
    ch <- struct{}{}  // (2) send happens-before receive
}

func main() {
    ch := make(chan struct{}, 1)
    go setup(ch)
    <-ch          // (3) receive
    fmt.Println(a)  // (4) guaranteed to see "hello" — (1)→(2)→(3)→(4)
}

// UNSAFE: no synchronization
var x int
go func() { x = 1 }()
fmt.Println(x)  // data race — might see 0 or 1
```

---

## 10. Thread Pools & Worker Patterns

### Python ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Basic pool
with ThreadPoolExecutor(max_workers=8) as executor:
    future = executor.submit(fn, arg1, arg2)
    result = future.result()   # blocks

    # Map (like built-in map but concurrent)
    results = list(executor.map(fn, iterable))

    # As completed — process results as they finish (not submission order)
    futs = [executor.submit(fetch, url) for url in urls]
    for fut in as_completed(futs):
        print(fut.result())

# Custom worker pool with queue
class WorkerPool:
    def __init__(self, num_workers):
        self._queue = Queue()
        self._workers = []
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)

    def _worker(self):
        while True:
            fn, args, kwargs = self._queue.get()
            if fn is None:   # poison pill
                break
            try:
                fn(*args, **kwargs)
            except Exception as e:
                print(f"Worker error: {e}")
            finally:
                self._queue.task_done()

    def submit(self, fn, *args, **kwargs):
        self._queue.put((fn, args, kwargs))

    def shutdown(self):
        for _ in self._workers:
            self._queue.put((None, None, None))  # send poison pills
        for t in self._workers:
            t.join()
```

### Go Worker Pool

```go
func workerPool(numWorkers, numJobs int) {
    jobs := make(chan int, numJobs)
    results := make(chan int, numJobs)

    // Start workers
    for w := 0; w < numWorkers; w++ {
        go func() {
            for job := range jobs {   // exits when jobs closed
                results <- job * job
            }
        }()
    }

    // Send jobs
    for j := 0; j < numJobs; j++ {
        jobs <- j
    }
    close(jobs)  // signal workers to stop

    // Collect results
    for a := 0; a < numJobs; a++ {
        fmt.Println(<-results)
    }
}

// Errgroup — worker pool with error propagation
import "golang.org/x/sync/errgroup"

func fetchAll(urls []string) error {
    g, ctx := errgroup.WithContext(context.Background())

    for _, url := range urls {
        url := url  // capture loop var
        g.Go(func() error {
            req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
            if err != nil {
                return err
            }
            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                return err  // cancels all other goroutines via ctx
            }
            defer resp.Body.Close()
            return nil
        })
    }

    return g.Wait()  // waits for all, returns first non-nil error
}
```

---

## 11. Producer-Consumer & Pipeline Patterns

### Python Producer-Consumer

```python
from queue import Queue
import threading

def producer(queue, n_items):
    for i in range(n_items):
        queue.put(i)
        print(f"Produced: {i}")
    queue.put(None)  # poison pill — signals consumer to stop

def consumer(queue):
    while True:
        item = queue.get()
        if item is None:
            break
        print(f"Consumed: {item}")
        queue.task_done()

q = Queue(maxsize=5)  # bounded buffer — natural backpressure
prod = threading.Thread(target=producer, args=(q, 10))
cons = threading.Thread(target=consumer, args=(q,))
prod.start(); cons.start()
prod.join(); cons.join()

# Multiple consumers (parallel processing)
N_CONSUMERS = 4

def run_pool():
    q = Queue(maxsize=20)

    def producer():
        for i in range(100):
            q.put(i)
        for _ in range(N_CONSUMERS):
            q.put(None)   # one poison pill per consumer

    def consumer():
        while True:
            item = q.get()
            if item is None:
                break
            process(item)

    threads = [threading.Thread(target=producer)]
    threads += [threading.Thread(target=consumer) for _ in range(N_CONSUMERS)]
    for t in threads: t.start()
    for t in threads: t.join()
```

### Go Pipeline

```go
type Result struct {
    URL  string
    Body []byte
    Err  error
}

func crawl(ctx context.Context, urls []string) <-chan Result {
    out := make(chan Result, len(urls))

    var wg sync.WaitGroup
    for _, url := range urls {
        url := url
        wg.Add(1)
        go func() {
            defer wg.Done()
            select {
            case <-ctx.Done():
                out <- Result{URL: url, Err: ctx.Err()}
            default:
                body, err := fetch(ctx, url)
                out <- Result{URL: url, Body: body, Err: err}
            }
        }()
    }

    go func() {
        wg.Wait()
        close(out)  // close after all goroutines done
    }()

    return out
}

// Usage
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

for result := range crawl(ctx, urls) {
    if result.Err != nil {
        log.Printf("Error for %s: %v", result.URL, result.Err)
        continue
    }
    process(result.Body)
}
```

---

## 12. Fan-Out / Fan-In

### Go Fan-Out Fan-In

```go
// Fan-Out: distribute work across multiple goroutines
func fanOut(in <-chan int, numWorkers int) []<-chan int {
    channels := make([]<-chan int, numWorkers)
    for i := 0; i < numWorkers; i++ {
        channels[i] = process(in)  // each gets same input channel
    }
    return channels
}

// Fan-In: merge multiple channels into one
func fanIn(done <-chan struct{}, channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int)

    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c {
            select {
            case merged <- v:
            case <-done:
                return
            }
        }
    }

    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }

    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

// Full example
func main() {
    done := make(chan struct{})
    defer close(done)

    in := generate(done, 1, 2, 3, 4, 5)
    // Fan-out to 3 workers
    c1 := process(done, in)
    c2 := process(done, in)
    c3 := process(done, in)
    // Fan-in results
    for v := range fanIn(done, c1, c2, c3) {
        fmt.Println(v)
    }
}
```

### Python Fan-Out Fan-In

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

def fan_out_fan_in(tasks, num_workers=4):
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = {ex.submit(process_task, t): t for t in tasks}
        results = []
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                print(f"Task failed: {e}")
    return results
```

---

## 13. Context Cancellation & Timeouts

### Python with Threading

```python
import threading
import time

class CancellableTask:
    def __init__(self):
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    def run(self):
        for i in range(100):
            if self._cancel.is_set():
                print("Cancelled!")
                return
            time.sleep(0.1)
            print(f"Step {i}")

task = CancellableTask()
t = threading.Thread(target=task.run)
t.start()
time.sleep(0.5)
task.cancel()
t.join()
```

### Python asyncio Context

```python
import asyncio

async def long_task():
    try:
        await asyncio.sleep(100)
    except asyncio.CancelledError:
        print("Task was cancelled!")
        raise  # re-raise — important!

async def main():
    task = asyncio.create_task(long_task())
    await asyncio.sleep(1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Caught cancellation")

asyncio.run(main())
```

### Go context.Context

```go
import (
    "context"
    "fmt"
    "time"
)

func doWork(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()  // context.Canceled or context.DeadlineExceeded
        case <-time.After(100 * time.Millisecond):
            fmt.Println("working...")
        }
    }
}

func main() {
    // Timeout
    ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
    defer cancel()

    if err := doWork(ctx); err != nil {
        fmt.Println("stopped:", err)  // context deadline exceeded
    }
}

// Context with value (pass request-scoped data)
type keyType string
const userKey keyType = "user"

ctx = context.WithValue(ctx, userKey, "alice")
user := ctx.Value(userKey).(string)  // "alice"

// Propagate context through call chain — ALWAYS accept ctx as first param
func layer1(ctx context.Context) {
    layer2(ctx)
}
func layer2(ctx context.Context) {
    layer3(ctx)
}
func layer3(ctx context.Context) {
    select {
    case <-ctx.Done():
        return
    default:
        // work
    }
}
```

---

## 14. Rate Limiting & Backpressure

### Token Bucket in Go

```go
import "golang.org/x/time/rate"

limiter := rate.NewLimiter(rate.Every(time.Second), 10) // 10 req/sec, burst 10

func handleRequest(ctx context.Context) error {
    if err := limiter.Wait(ctx); err != nil {
        return err  // context cancelled while waiting for token
    }
    // process request
    return nil
}

// Or non-blocking:
if !limiter.Allow() {
    return errors.New("rate limit exceeded")
}
```

### Semaphore for Concurrency Limit in Go

```go
// Limit to N concurrent goroutines
sem := make(chan struct{}, N)

for _, url := range urls {
    url := url
    sem <- struct{}{}   // acquire slot (blocks if N already running)
    go func() {
        defer func() { <-sem }()  // release slot
        fetch(url)
    }()
}

// Drain remaining slots
for i := 0; i < N; i++ {
    sem <- struct{}{}
}
```

### Python Rate Limiter

```python
import threading
import time
from collections import deque

class TokenBucket:
    def __init__(self, rate, capacity):
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens=1):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._last = now
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_and_consume(self, tokens=1):
        while not self.consume(tokens):
            time.sleep(0.01)
```

---

## 15. Atomic Operations & Lock-Free Structures

### Python Atomics

```python
# Python integers (small ints) are interned and += is NOT atomic
# Use threading.Lock or atomic operations via ctypes/multiprocessing

# For simple counters: use threading.Lock
# For cross-process: multiprocessing.Value

from multiprocessing import Value
import ctypes

counter = Value(ctypes.c_int, 0)
with counter.get_lock():
    counter.value += 1

# Python 3.12+: atomics module (experimental)
# For production: just use Lock — it's fast enough
```

### Go Atomics

```go
import "sync/atomic"

var counter int64

// All atomic ops are goroutine-safe, no lock needed
atomic.AddInt64(&counter, 1)
atomic.AddInt64(&counter, -1)

current := atomic.LoadInt64(&counter)
atomic.StoreInt64(&counter, 42)

// Compare-and-Swap — foundation of lock-free algorithms
old, new := int64(5), int64(10)
swapped := atomic.CompareAndSwapInt64(&counter, old, new)
// If counter == old: set counter = new, return true
// Else: return false

// Generic atomics (Go 1.19+)
var val atomic.Int64
val.Add(1)
val.Load()
val.Store(42)
val.CompareAndSwap(5, 10)

var ptr atomic.Pointer[MyStruct]
ptr.Store(&MyStruct{})
s := ptr.Load()
```

### Lock-Free Stack (Go)

```go
type node struct {
    val  int
    next *node
}

type LockFreeStack struct {
    top atomic.Pointer[node]
}

func (s *LockFreeStack) Push(val int) {
    n := &node{val: val}
    for {
        top := s.top.Load()
        n.next = top
        if s.top.CompareAndSwap(top, n) {
            return
        }
        // CAS failed: another goroutine modified top — retry
    }
}

func (s *LockFreeStack) Pop() (int, bool) {
    for {
        top := s.top.Load()
        if top == nil {
            return 0, false
        }
        if s.top.CompareAndSwap(top, top.next) {
            return top.val, true
        }
    }
}
```

---

## 16. Condition Variables — The Hidden Interview Weapon

Condition variables are fundamental to implementing any "wait until condition is true" pattern. They appear in every classic interview problem.

### Python Condition

```python
import threading

# Pattern: wait until some condition, signal when condition changes
class BoundedBuffer:
    def __init__(self, capacity):
        self._buf = []
        self._capacity = capacity
        self._cond = threading.Condition()

    def put(self, item):
        with self._cond:
            while len(self._buf) >= self._capacity:  # WHILE, not IF
                self._cond.wait()  # releases lock, sleeps, reacquires on wake
            self._buf.append(item)
            self._cond.notify_all()  # wake consumers

    def get(self):
        with self._cond:
            while not self._buf:    # WHILE, not IF
                self._cond.wait()
            item = self._buf.pop(0)
            self._cond.notify_all()  # wake producers
            return item

# WHY WHILE NOT IF:
# Spurious wakeups: OS can wake thread without notify()
# Lost notify: producer notifies before consumer waits
# Multiple waiters: first consumer wakes and takes item; second consumer must re-check
```

### Go Condition Variable

```go
import "sync"

type BoundedBuffer struct {
    mu       sync.Mutex
    cond     *sync.Cond
    buf      []int
    capacity int
}

func NewBoundedBuffer(cap int) *BoundedBuffer {
    bb := &BoundedBuffer{capacity: cap}
    bb.cond = sync.NewCond(&bb.mu)
    return bb
}

func (bb *BoundedBuffer) Put(item int) {
    bb.mu.Lock()
    defer bb.mu.Unlock()
    for len(bb.buf) >= bb.capacity {  // WHILE not IF
        bb.cond.Wait()  // releases mu, sleeps, reacquires mu on wake
    }
    bb.buf = append(bb.buf, item)
    bb.cond.Broadcast()  // wake all waiters (or Signal() for one)
}

func (bb *BoundedBuffer) Get() int {
    bb.mu.Lock()
    defer bb.mu.Unlock()
    for len(bb.buf) == 0 {
        bb.cond.Wait()
    }
    item := bb.buf[0]
    bb.buf = bb.buf[1:]
    bb.cond.Broadcast()
    return item
}
```

---

## 17. Classic Interview Problems

### 17.1 Thread-Safe Singleton

```python
class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:          # first check (no lock, fast path)
            with cls._lock:
                if cls._instance is None:  # second check (with lock)
                    cls._instance = super().__new__(cls)
        return cls._instance
```

```go
var (
    instance *Singleton
    once     sync.Once
)

func GetInstance() *Singleton {
    once.Do(func() {
        instance = &Singleton{}
    })
    return instance
}
```

### 17.2 Dining Philosophers

```python
# 5 philosophers, 5 forks. Each needs 2 adjacent forks to eat.
# Naive solution: deadlock (each grabs left fork, waits for right)
# Fix 1: Global ordering — always pick up lower-numbered fork first
# Fix 2: Asymmetric — one philosopher picks right fork first
# Fix 3: Semaphore allowing only 4 philosophers to attempt eating

import threading

N = 5
forks = [threading.Lock() for _ in range(N)]
semaphore = threading.Semaphore(N - 1)  # allow at most N-1 philosophers

def philosopher(i):
    left = i
    right = (i + 1) % N
    while True:
        think()
        semaphore.acquire()          # at most N-1 trying to eat
        forks[left].acquire()
        forks[right].acquire()
        eat()
        forks[right].release()
        forks[left].release()
        semaphore.release()
```

### 17.3 Reader-Writer Problem

```python
# Multiple readers can read simultaneously
# Writers need exclusive access

class ReadWriteLock:
    def __init__(self):
        self._read_cond = threading.Condition(threading.Lock())
        self._readers = 0
        self._writing = False
        self._writers_waiting = 0

    def acquire_read(self):
        with self._read_cond:
            # Wait if writer is writing or waiting (writer preference)
            while self._writing or self._writers_waiting > 0:
                self._read_cond.wait()
            self._readers += 1

    def release_read(self):
        with self._read_cond:
            self._readers -= 1
            if self._readers == 0:
                self._read_cond.notify_all()

    def acquire_write(self):
        with self._read_cond:
            self._writers_waiting += 1
            while self._readers > 0 or self._writing:
                self._read_cond.wait()
            self._writers_waiting -= 1
            self._writing = True

    def release_write(self):
        with self._read_cond:
            self._writing = False
            self._read_cond.notify_all()
```

### 17.4 Barrier Synchronization (from scratch)

```python
class Barrier:
    def __init__(self, n):
        self._n = n
        self._count = 0
        self._cond = threading.Condition()
        self._generation = 0

    def wait(self):
        with self._cond:
            gen = self._generation
            self._count += 1
            if self._count == self._n:
                self._count = 0
                self._generation += 1    # new generation — reusable barrier
                self._cond.notify_all()
            else:
                while gen == self._generation:  # wait for generation to change
                    self._cond.wait()
```

### 17.5 Thread-Safe LRU Cache

```python
from collections import OrderedDict
import threading

class LRUCache:
    def __init__(self, capacity):
        self._cap = capacity
        self._cache = OrderedDict()
        self._lock = threading.RLock()  # RLock for reentrant access

    def get(self, key):
        with self._lock:
            if key not in self._cache:
                return -1
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key, value):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._cap:
                self._cache.popitem(last=False)
```

### 17.6 Print FooBar Alternately (LeetCode 1115)

```python
class FooBar:
    def __init__(self, n):
        self.n = n
        self._foo_sem = threading.Semaphore(1)  # foo goes first
        self._bar_sem = threading.Semaphore(0)

    def foo(self, printFoo):
        for _ in range(self.n):
            self._foo_sem.acquire()
            printFoo()
            self._bar_sem.release()

    def bar(self, printBar):
        for _ in range(self.n):
            self._bar_sem.acquire()
            printBar()
            self._foo_sem.release()
```

### 17.7 H2O (LeetCode 1117)

```python
class H2O:
    def __init__(self):
        self._h_sem = threading.Semaphore(2)  # 2 H atoms
        self._o_sem = threading.Semaphore(0)
        self._h_count = 0
        self._lock = threading.Lock()
        self._barrier = threading.Barrier(3)

    def hydrogen(self, releaseHydrogen):
        self._h_sem.acquire()
        releaseHydrogen()
        self._barrier.wait()
        with self._lock:
            self._h_count += 1
            if self._h_count == 2:
                self._h_count = 0
                self._h_sem = threading.Semaphore(2)
                self._o_sem.release()

    def oxygen(self, releaseOxygen):
        self._o_sem.acquire()
        releaseOxygen()
        self._barrier.wait()
```

### 17.8 Building Blocks: Thread-Safe Queue from Scratch

```python
class MyQueue:
    def __init__(self, maxsize=0):
        self._items = []
        self._maxsize = maxsize
        self._not_empty = threading.Condition()
        self._not_full = threading.Condition(self._not_empty._lock)  # share lock

    def put(self, item):
        with self._not_full:
            if self._maxsize:
                while len(self._items) >= self._maxsize:
                    self._not_full.wait()
            self._items.append(item)
            self._not_empty.notify()

    def get(self):
        with self._not_empty:
            while not self._items:
                self._not_empty.wait()
            item = self._items.pop(0)
            self._not_full.notify()
            return item
```

---

## 18. Industry-Scale Patterns

### 18.1 Circuit Breaker

```go
type State int

const (
    Closed   State = iota // normal operation
    Open                  // failing, reject requests
    HalfOpen              // testing if service recovered
)

type CircuitBreaker struct {
    mu           sync.Mutex
    state        State
    failures     int
    maxFailures  int
    timeout      time.Duration
    lastFailure  time.Time
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()

    if cb.state == Open {
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.state = HalfOpen
        } else {
            cb.mu.Unlock()
            return errors.New("circuit breaker open")
        }
    }
    cb.mu.Unlock()

    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = Open
        }
        return err
    }

    // Success
    cb.failures = 0
    cb.state = Closed
    return nil
}
```

### 18.2 Retry with Exponential Backoff

```go
func retryWithBackoff(ctx context.Context, maxRetries int, fn func() error) error {
    backoff := 100 * time.Millisecond
    for i := 0; i < maxRetries; i++ {
        err := fn()
        if err == nil {
            return nil
        }
        if i == maxRetries-1 {
            return fmt.Errorf("max retries exceeded: %w", err)
        }

        // Exponential backoff with jitter
        jitter := time.Duration(rand.Int63n(int64(backoff)))
        sleep := backoff + jitter

        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(sleep):
        }

        backoff *= 2
        if backoff > 30*time.Second {
            backoff = 30 * time.Second
        }
    }
    return nil
}
```

```python
import time
import random
from functools import wraps

def retry(max_attempts=3, base_delay=0.1, max_delay=30.0, exceptions=(Exception,)):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    jitter = random.uniform(0, delay)
                    time.sleep(min(delay + jitter, max_delay))
                    delay *= 2
        return wrapper
    return decorator

@retry(max_attempts=5, exceptions=(ConnectionError, TimeoutError))
def fetch_data(url):
    return requests.get(url, timeout=5)
```

### 18.3 Singleflight (Coalesce duplicate requests)

```go
// Multiple goroutines requesting same key — only one call executes
import "golang.org/x/sync/singleflight"

var group singleflight.Group

func GetUserFromDB(userID string) (*User, error) {
    result, err, _ := group.Do(userID, func() (interface{}, error) {
        return db.QueryUser(userID)  // only called once per key per flight
    })
    if err != nil {
        return nil, err
    }
    return result.(*User), nil
}
// If 100 goroutines call GetUserFromDB("user-42") simultaneously,
// only ONE db query executes; all 100 get the same result
```

### 18.4 Graceful Shutdown

```go
func main() {
    server := &http.Server{Addr: ":8080"}

    // Start server
    go func() {
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }
    log.Println("Server exited gracefully")
}
```

```python
import signal
import threading

class GracefulServer:
    def __init__(self):
        self._shutdown = threading.Event()
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print(f"Received signal {signum}, shutting down...")
        self._shutdown.set()

    def run(self):
        while not self._shutdown.is_set():
            self._process_request()
        self._cleanup()
```

### 18.5 Concurrent Map with Sharding (Reduce Lock Contention)

```go
const numShards = 32

type ShardedMap struct {
    shards [numShards]mapShard
}

type mapShard struct {
    sync.RWMutex
    data map[string]interface{}
}

func (m *ShardedMap) getShard(key string) *mapShard {
    hash := fnv.New32()
    hash.Write([]byte(key))
    return &m.shards[hash.Sum32()%numShards]
}

func (m *ShardedMap) Get(key string) (interface{}, bool) {
    shard := m.getShard(key)
    shard.RLock()
    defer shard.RUnlock()
    val, ok := shard.data[key]
    return val, ok
}

func (m *ShardedMap) Set(key string, val interface{}) {
    shard := m.getShard(key)
    shard.Lock()
    defer shard.Unlock()
    shard.data[key] = val
}
// 32 independent locks → ~32x less contention than a single lock
```

### 18.6 Work Stealing Queue

```go
// Each worker has its own deque; steals from others when empty
// Used in: Go runtime, Java ForkJoinPool, Tokio (Rust)

// Simplified concept:
type WorkStealingPool struct {
    workers []*worker
    mu      sync.Mutex
}

type worker struct {
    id    int
    queue chan func()
    pool  *WorkStealingPool
}

func (w *worker) run() {
    for {
        // Try own queue first
        select {
        case task := <-w.queue:
            task()
        default:
            // Steal from random worker
            victim := w.pool.workers[rand.Intn(len(w.pool.workers))]
            select {
            case task := <-victim.queue:
                task()
            default:
                runtime.Gosched()
            }
        }
    }
}
```

---

## 19. Debugging Concurrency Bugs

### Go Race Detector

```bash
# Compile and run with race detector
go run -race main.go
go test -race ./...
go build -race -o myapp .

# Output:
# WARNING: DATA RACE
# Write at 0x... by goroutine 7:
#   main.increment()  main.go:14
# Previous read at 0x... by goroutine 6:
#   main.increment()  main.go:14
```

### Python: `threading` debugging

```python
import threading
import traceback

# Print all thread stacks (useful for deadlock diagnosis)
def dump_threads():
    for thread_id, frame in sys._current_frames().items():
        name = {t.ident: t.name for t in threading.enumerate()}.get(thread_id, "?")
        print(f"\n--- Thread {name} ({thread_id}) ---")
        traceback.print_stack(frame)

# Timeout-based deadlock detection
def detect_deadlock(lock, timeout=5.0):
    acquired = lock.acquire(timeout=timeout)
    if not acquired:
        print("POSSIBLE DEADLOCK DETECTED")
        dump_threads()
        raise RuntimeError("Deadlock detected")
    return acquired

# Use faulthandler for crash debugging
import faulthandler
faulthandler.enable()  # prints tracebacks on SIGSEGV
# Send SIGUSR1 to dump all threads: kill -USR1 <pid>
faulthandler.register(signal.SIGUSR1)
```

### Goroutine Leak Detection

```go
// Use goleak in tests
import "go.uber.org/goleak"

func TestMyFunc(t *testing.T) {
    defer goleak.VerifyNone(t)
    // ... test code
    // goleak fails test if any goroutines leaked
}

// Manual: check goroutine count
import "runtime/pprof"

func dumpGoroutines() {
    pprof.Lookup("goroutine").WriteTo(os.Stdout, 1)
}
```

### Common Patterns That Hide Bugs

```python
# WRONG: lock doesn't protect what you think
lock = threading.Lock()
data = {}

def bad():
    with lock:
        keys = list(data.keys())  # protected
    for key in keys:
        process(data[key])  # NOT protected! data could change between iterations

# RIGHT: hold lock for entire operation
def good():
    with lock:
        for key, val in data.items():
            process(val)  # lock held throughout
```

```go
// WRONG: check-then-act without lock
if _, exists := m[key]; !exists {  // check
    m[key] = compute(key)           // act — RACE!
}

// RIGHT: use LoadOrStore or lock
val, loaded := m.LoadOrStore(key, compute(key))  // atomic
// OR:
mu.Lock()
if _, exists := m[key]; !exists {
    m[key] = compute(key)
}
mu.Unlock()
```

---

## 20. Quick-Reference Cheat Sheet

### When to use what

```
PYTHON:
┌─────────────────────────────────────────────────────────┐
│ I/O-bound + simple     → threading.Thread               │
│ I/O-bound + many tasks → ThreadPoolExecutor             │
│ I/O-bound + async      → asyncio                        │
│ CPU-bound              → ProcessPoolExecutor            │
│ Shared state + threads → threading.Lock / RLock         │
│ Signaling              → threading.Event                │
│ Rate limiting access   → threading.Semaphore            │
│ Wait-until-condition   → threading.Condition            │
│ Thread-safe comms      → queue.Queue                    │
└─────────────────────────────────────────────────────────┘

GO:
┌─────────────────────────────────────────────────────────┐
│ Any concurrent task    → goroutine                      │
│ Communicate            → channel (buffered or not)      │
│ Shared state           → sync.Mutex / sync.RWMutex      │
│ One-time init          → sync.Once                      │
│ Wait for goroutines    → sync.WaitGroup                 │
│ Wait-until-condition   → sync.Cond                      │
│ Safe concurrent map    → sync.Map                       │
│ Cancellation           → context.Context               │
│ Concurrent counter     → sync/atomic                    │
│ Limit concurrency      → buffered channel semaphore     │
└─────────────────────────────────────────────────────────┘
```

### Complexity & Trade-offs

```
Primitive          | Python              | Go
-------------------+---------------------+--------------------
Mutex              | threading.Lock      | sync.Mutex
RW Mutex           | (custom)            | sync.RWMutex
Condition Var      | threading.Condition | sync.Cond
Semaphore          | threading.Semaphore | chan struct{}
Barrier            | threading.Barrier   | sync.WaitGroup
Once               | (double-checked)    | sync.Once
Atomic int         | (via lock)          | sync/atomic
Thread-safe queue  | queue.Queue         | chan T
Thread-local       | threading.local()   | goroutine-local (no built-in)
```

### Interview Answer Framework

When asked about a concurrency problem:

1. **Identify** the shared resource and who accesses it
2. **Classify** as read-heavy or write-heavy
3. **Choose** the right primitive (Mutex → RWMutex → channel → atomic)
4. **Consider** deadlock: always acquire locks in consistent order
5. **Consider** starvation: ensure all threads eventually make progress
6. **Consider** performance: minimize critical section size
7. **Test** with race detector / stress test

### Key Rules to Never Forget

```
Python:
  ✓ Always use 'with lock:' (exception-safe release)
  ✓ Condition.wait() MUST be in a while loop
  ✓ GIL helps I/O, hurts CPU
  ✓ daemon=True threads die with main — don't use for critical work
  ✓ Never share Queue between processes (use multiprocessing.Queue)

Go:
  ✓ Don't communicate by sharing memory; share memory by communicating
  ✓ Always close channels from sender side, never receiver
  ✓ Don't close a channel twice (panic)
  ✓ Use defer wg.Done() as first statement in goroutine
  ✓ Call wg.Add() BEFORE starting goroutine
  ✓ Always propagate context; never store it in struct
  ✓ Run with -race flag in CI always
  ✓ A nil channel blocks forever (useful in select to disable a case)
  ✓ Sending to closed channel panics; receiving from closed gives zero value
```

---

*Related: `DSA_PATTERNS.md` | `CONCEPTS.md` | `FASTAPI_PATTERNS.md` | `LLD_OOD.md`*
