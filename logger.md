# Logger / Logging Library — Deep LLD

A single document that teaches you how to design this problem from scratch, the way a beginner should think about it, with the sync and async implementations, every concept behind each decision, and the mistakes **I** made the first time around with the fix next to each one.

**Read it top to bottom once. Keep it open the next time you design any "producer calls, something fans out" system (notification service, metric emitter, event bus, audit log).**

---

## Table of contents

1. [The problem](#1-the-problem)
2. [How to approach it (beginner-friendly, 5 steps)](#2-how-to-approach-it-beginner-friendly-5-steps)
3. [Requirements, read carefully](#3-requirements-read-carefully)
4. [Finding the classes](#4-finding-the-classes-entity-discovery)
5. [Class design, with the reasoning for every choice](#5-class-design-with-the-reasoning-for-every-choice)
6. [Sync implementation (complete, runnable)](#6-sync-implementation-complete-runnable)
7. [Async / queue-based implementation (complete, runnable)](#7-async--queue-based-implementation-complete-runnable)
8. [Deep concepts](#8-deep-concepts)
9. [My mistakes, with the fix next to each](#9-my-mistakes-with-the-fix-next-to-each)
10. [Trade-offs to talk about in an interview](#10-trade-offs-to-talk-about-in-an-interview)
11. [Extensions interviewers love to ask](#11-extensions-interviewers-love-to-ask)
12. [One-page cheatsheet](#12-one-page-cheatsheet)

---

## 1. The problem

> Design an in-process logging library that an application can call to record events. Each call fans out to one or more configured destinations.

**Must have:**
- 5 levels — `DEBUG < INFO < WARN < ERROR < FATAL`
- Used as a package by other apps (not a server)
- The app configures destinations (console, file, HTTP, ...)
- A log call fans out to every configured destination
- **Each destination has its own minimum level.** If a record's level is below the destination's threshold, the destination silently drops it.
- Thread-safe, and the order of calls inside one app is preserved

**Out of scope:**
- No dashboard, no search

**That's it.** Don't invent a central service, don't invent user management, don't invent cross-app features. Everything below exists because one of those bullets demanded it.

---

## 2. How to approach it (beginner-friendly, 5 steps)

> The single biggest reason my first attempt failed was skipping these steps. Do them in order.

### Step 1 — Write the client code first (2 min)

Pretend you're the app using this library. What's the nicest thing you'd want to type?

```python
log = get_logger("payments")
log.info("charge started", order_id=42)
log.error("card declined", order_id=42)
```

Why this matters: if the API feels awkward now, the design is wrong. My first attempt had `addLog(source, WarnMessage("x"))` — ugly because the client would never want to build a `WarnMessage` object by hand.

### Step 2 — Trace one call end to end (3 min)

```
log.error("card declined", order_id=42)
  │
  ▼
Logger
  ├─ check logger's own min level  ──► below threshold? return
  ├─ build LogRecord(level, msg, time, seq, context)
  │
  ├─[sync]── for each Destination:
  │           ├─ check dest min level ──► below? skip this dest
  │           ├─ format record using dest's Formatter
  │           └─ write to backend (stdout / file / HTTP)
  │
  └─[async]─ put record on a queue  (caller returns here, FAST)
              │
              ▼
            Worker thread
              └─ for each Destination: level check → format → write
```

Why this matters: every class you'll need shows up in this trace. Any class you can't place on an arrow doesn't belong.

### Step 3 — Write every class's fields first, no methods yet (5 min)

Fields are data. Methods are behavior. Data is the easier of the two to get right, and if a method has no data to work on, the design is wrong.

Example — I originally wrote:
```
IDestination:
    - validateMessage()
```
Hopeless, because `validateMessage` has nothing to compare against. If I'd written the fields first I'd have been forced to type `min_level`, and the method would have been obvious.

### Step 4 — Write full signatures with return types and exceptions, still no bodies (5 min)

```python
class Destination(ABC):
    min_level: LogLevel
    formatter: Formatter

    def emit(self, record: LogRecord) -> None: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...
```

Why this matters: ambiguity caught in a signature is free. Caught in a body it's a bug.

### Step 5 — Fill in the main methods (10 min)

Only now do you write bodies. Start with the one method a reviewer will look at first: `Logger.log()`.

---

## 3. Requirements, read carefully

The problem statement is 5 bullet points. Each has a design implication I missed on my first read:

| Requirement | What it actually means |
|---|---|
| "5 levels DEBUG < INFO < WARN < ERROR < FATAL" | They are **ordered**. Use `IntEnum`, not plain `Enum`, so `WARN >= INFO` works. |
| "Used as a package by other applications" | **One process, one copy.** No multi-tenant lookup by application id. |
| "Each application configures its destinations" | A `LogManager` or similar config entry point exists, but it's module-level. |
| "Fans out to configured destinations" | A logger holds a **list** of destinations. The fan-out is just a `for` loop. |
| "Each destination has its own min level" | `min_level` is a **field on the destination**, not a global, not a method parameter. |
| "Order preserved within one app" | A **single consumer** of the queue, or synchronous emit. Multiple workers would reorder. |
| "Thread-safe" | Two threads calling `log.info()` at the same moment must both succeed, nothing corrupts, and the sequence number is unique. |

**Out of scope matters too.** No dashboard means no in-memory ring buffer, no HTTP endpoint, no search index. Don't design what wasn't asked.

---

## 4. Finding the classes (entity discovery)

The naive way is to list every noun in the problem: `Log`, `Logger`, `Level`, `Message`, `Source`, `Destination`, `Formatter`, `Config`, ... That's how I ended up with 10 classes, half of them useless.

The better way is to **look at your call trace** and ask: *for every arrow, which object is doing the work?*

| Arrow in the trace | Object |
|---|---|
| App calls `log.error(...)` | `Logger` |
| Build the record | `LogRecord` (plain data) |
| Decide if a destination accepts | `Destination` (field: `min_level`) |
| Turn a record into text/JSON | `Formatter` |
| Write to stdout, file, HTTP | subclasses of `Destination` |
| Hand off to a worker thread | the queue inside `Logger` |
| Give out named loggers, hold global config | `LogManager` |

That's **6 classes**. Compare with my first draft, which also had `Source`, `Config`, `LogService`, `DebugMessage`, `InfoMessage`, `WarnMessage`, `ErrorMessage`, `FatalMessage`, `ILogMessage` — nine extra classes, every one of them wrong or redundant.

**Rule:** before adding a class, ask *"what does this class do that an existing class can't?"* If the answer is "it just holds a different value," make it a field.

---

## 5. Class design, with the reasoning for every choice

### 5.1 `LogLevel` — why `IntEnum`

```python
class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50
```

**Why `IntEnum`:** level comparisons (`record.level >= dest.min_level`) must work. Plain `Enum` doesn't support `>=`.

**Why gaps of 10:** so you can insert `NOTICE = 25` later without renumbering.

**My mistake:** wrote `enum LOG_LEVEL : DEBUG < INFO < WARN < ERROR < FATAL`. The order was in the comment, not in the code. The code couldn't actually compare them.

### 5.2 `LogRecord` — one class, not five

```python
@dataclass(frozen=True)
class LogRecord:
    level: LogLevel
    message: str
    logger_name: str
    timestamp: float
    seq: int
    thread_name: str
    context: dict
```

**Why one class:** `DebugMessage`, `InfoMessage`, `WarnMessage` would have identical behavior and differ only by one field value. That's a field, not a subclass.

**Why `frozen=True`:** the record is passed to multiple destinations in sequence (and in async mode, across threads). If one destination mutates it, the next sees the mutation. Immutable records remove that whole class of bug.

**Why `seq`:** total ordering across threads. Two threads logging at the exact same microsecond would otherwise be indistinguishable; `seq` gives you one definitive order.

**Why `thread_name` and `context`:** operators always want them when debugging. Cheap to collect at the call site, impossible to recover later.

### 5.3 `Formatter` — owned by the destination, not the record

```python
class Formatter(ABC):
    @abstractmethod
    def format(self, record: LogRecord) -> str: ...

class TextFormatter(Formatter):
    def format(self, r):
        return f"{r.timestamp:.3f} [{r.level.name}] {r.logger_name}: {r.message}"

class JsonFormatter(Formatter):
    def format(self, r):
        return json.dumps({"ts": r.timestamp, "level": r.level.name, ...})
```

**Why the destination owns the formatter, not the record:** the same record goes to the file (as JSON for the log shipper) and to the console (as plain text for the human watching). The record can't pick one. Each destination picks its own.

**The ownership test** (use this everywhere):
> *"If I wanted the file in a different format tomorrow, which object would I change?"*
> The file destination. So the file destination owns the formatter.

**My mistake:** I had `ILogMessage.formatMessage(message, IFormatter)` — the message formatting itself. The method lived on the wrong class.

### 5.4 `Destination` — abstract base with a template method

```python
class Destination(ABC):
    def __init__(self, min_level: LogLevel, formatter: Formatter):
        self.min_level = min_level
        self.formatter = formatter

    def emit(self, record: LogRecord) -> None:   # same for ALL destinations
        if record.level < self.min_level:        # requirement 5, in one place
            return
        line = self.formatter.format(record)
        self._write(line)

    @abstractmethod
    def _write(self, line: str) -> None: ...     # only this varies

    def flush(self) -> None: pass                # overridden by file/HTTP
    def close(self) -> None: pass
```

**Why `min_level` is a field, not a method parameter:** requirement 5 says *"each destination has its own minimum."* Each → field.

**Why the level check lives in the base `emit`, not in each subclass:** otherwise every new destination has to remember to check. Base-class template method = write it once, impossible to forget.

**Why `flush` and `close`:** reliability. If the app exits with buffered lines still in a file handle, those lines are lost. Every destination needs a chance to drain and release OS resources.

**Why `_write` is a separate abstract method:** this is the **Template Method** pattern. `emit` is the fixed algorithm (check → format → write); subclasses supply only the one varying step.

### 5.5 Concrete destinations

```python
class ConsoleDestination(Destination):
    def _write(self, line): print(line, file=sys.stderr)

class FileDestination(Destination):
    def __init__(self, path, min_level, formatter):
        super().__init__(min_level, formatter)
        self._file = open(path, "a", encoding="utf-8")
        self._lock = threading.Lock()      # see 5.6

    def _write(self, line):
        with self._lock:                   # protect the file handle
            self._file.write(line + "\n")

    def flush(self): self._file.flush()
    def close(self):  self._file.close()
```

**Why `ConsoleDestination` prints to `stderr`:** `stdout` is for the program's output; `stderr` is for diagnostics. Logs are diagnostics.

**Why `FileDestination` locks around `write`:** two threads writing to the same file simultaneously can interleave bytes mid-line. In async mode you have one worker thread so the lock is redundant; keep it anyway, because someone will later use `FileDestination` from the sync logger.

### 5.6 `Logger` — the thing the app actually holds

Two versions below, sync and async. The interface is identical; the body differs.

### 5.7 `LogManager` — module-level config

```python
class LogManager:
    _loggers: dict[str, Logger] = {}
    _destinations: tuple[Destination, ...] = (ConsoleDestination(LogLevel.INFO, TextFormatter()),)
    _min_level: LogLevel = LogLevel.DEBUG
    _lock = threading.Lock()

    @classmethod
    def configure(cls, destinations, min_level=LogLevel.DEBUG):
        with cls._lock:
            cls._destinations = tuple(destinations)
            cls._min_level = min_level

    @classmethod
    def get_logger(cls, name: str) -> "Logger":
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = Logger(name, cls._destinations, cls._min_level)
            return cls._loggers[name]
```

**Why class-methods on a module-level singleton:** this is a package. One process, one copy. A `LogManager()` instance you'd have to pass around would add zero value and lots of ceremony.

**Why `_lock`:** two app threads doing `get_logger("x")` on the first call would otherwise create two loggers.

**Why `destinations` is a `tuple`:** immutable snapshot. If someone reconfigures mid-flight, loggers already built keep the old destinations, and nothing can mutate a shared list while a worker iterates it.

---

## 6. Sync implementation (complete, runnable)

Use this when:
- You're writing to local files or `stderr` only (no network),
- Loss on crash is acceptable,
- Simplicity > throughput.

```python
import json
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum


# --- level ------------------------------------------------------------------
class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50


# --- record -----------------------------------------------------------------
@dataclass(frozen=True)
class LogRecord:
    level: LogLevel
    message: str
    logger_name: str
    timestamp: float
    seq: int
    thread_name: str
    context: dict = field(default_factory=dict)


# --- formatter --------------------------------------------------------------
class Formatter(ABC):
    @abstractmethod
    def format(self, record: LogRecord) -> str: ...


class TextFormatter(Formatter):
    def format(self, r: LogRecord) -> str:
        ctx = " ".join(f"{k}={v}" for k, v in r.context.items())
        return f"{r.timestamp:.3f} #{r.seq} [{r.level.name}] {r.logger_name}: {r.message} {ctx}".rstrip()


class JsonFormatter(Formatter):
    def format(self, r: LogRecord) -> str:
        return json.dumps({
            "ts": r.timestamp, "seq": r.seq, "level": r.level.name,
            "logger": r.logger_name, "thread": r.thread_name,
            "msg": r.message, **r.context,
        })


# --- destinations -----------------------------------------------------------
class Destination(ABC):
    def __init__(self, min_level: LogLevel, formatter: Formatter):
        self.min_level = min_level
        self.formatter = formatter

    def emit(self, record: LogRecord) -> None:
        if record.level < self.min_level:
            return
        self._write(self.formatter.format(record))

    @abstractmethod
    def _write(self, line: str) -> None: ...

    def flush(self) -> None: pass
    def close(self) -> None: pass


class ConsoleDestination(Destination):
    _stdio_lock = threading.Lock()                       # one lock shared across console destinations

    def _write(self, line: str) -> None:
        with ConsoleDestination._stdio_lock:
            print(line, file=sys.stderr)


class FileDestination(Destination):
    def __init__(self, path: str, min_level: LogLevel, formatter: Formatter):
        super().__init__(min_level, formatter)
        self._file = open(path, "a", encoding="utf-8")
        self._lock = threading.Lock()

    def _write(self, line: str) -> None:
        with self._lock:
            self._file.write(line + "\n")

    def flush(self) -> None:
        with self._lock:
            self._file.flush()

    def close(self) -> None:
        with self._lock:
            self._file.close()


# --- logger (sync) ----------------------------------------------------------
class Logger:
    def __init__(self, name: str, destinations, min_level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self.min_level = min_level
        self._destinations = tuple(destinations)
        self._seq = 0
        self._lock = threading.Lock()                    # protects _seq

    def log(self, level: LogLevel, message: str, **context) -> None:
        if level < self.min_level:
            return                                       # fast path: no lock, no record built
        with self._lock:
            self._seq += 1
            seq = self._seq
        record = LogRecord(
            level=level, message=message, logger_name=self.name,
            timestamp=time.time(), seq=seq,
            thread_name=threading.current_thread().name,
            context=context,
        )
        for dest in self._destinations:                  # fan-out
            try:
                dest.emit(record)
            except Exception as exc:
                print(f"logging: {type(dest).__name__} failed: {exc}", file=sys.stderr)

    def debug(self, msg, **ctx): self.log(LogLevel.DEBUG, msg, **ctx)
    def info(self, msg, **ctx):  self.log(LogLevel.INFO, msg, **ctx)
    def warn(self, msg, **ctx):  self.log(LogLevel.WARN, msg, **ctx)
    def error(self, msg, **ctx): self.log(LogLevel.ERROR, msg, **ctx)
    def fatal(self, msg, **ctx): self.log(LogLevel.FATAL, msg, **ctx)

    def shutdown(self) -> None:
        for dest in self._destinations:
            try:
                dest.flush(); dest.close()
            except Exception:
                pass


# --- manager ----------------------------------------------------------------
class LogManager:
    _loggers: dict[str, Logger] = {}
    _destinations: tuple[Destination, ...] = (ConsoleDestination(LogLevel.INFO, TextFormatter()),)
    _min_level: LogLevel = LogLevel.DEBUG
    _lock = threading.Lock()

    @classmethod
    def configure(cls, destinations, min_level=LogLevel.DEBUG):
        with cls._lock:
            cls._destinations = tuple(destinations)
            cls._min_level = min_level

    @classmethod
    def get_logger(cls, name: str) -> Logger:
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = Logger(name, cls._destinations, cls._min_level)
            return cls._loggers[name]

    @classmethod
    def shutdown(cls):
        with cls._lock:
            for lg in cls._loggers.values():
                lg.shutdown()
```

Usage:

```python
LogManager.configure([
    ConsoleDestination(LogLevel.WARN, TextFormatter()),
    FileDestination("app.log", LogLevel.DEBUG, JsonFormatter()),
])
log = LogManager.get_logger("payments")
log.info("charge started", order_id=42)      # file only (console min is WARN)
log.error("card declined", order_id=42)      # console + file
LogManager.shutdown()
```

---

## 7. Async / queue-based implementation (complete, runnable)

Use this when:
- Destinations include anything slow (file, HTTP, syslog, Elasticsearch),
- You care about caller latency (web requests, hot paths),
- You accept that a hard crash can lose the records still in the queue.

Only `Logger` changes. Everything else — `LogLevel`, `LogRecord`, `Formatter`, `Destination`, `LogManager` — is identical.

```python
import queue
import threading
import time

_STOP = object()                                         # sentinel for shutdown


class AsyncLogger:
    def __init__(
        self,
        name: str,
        destinations,
        min_level: LogLevel = LogLevel.DEBUG,
        capacity: int = 10_000,
        drop_when_full: bool = False,
    ):
        self.name = name
        self.min_level = min_level
        self._destinations = tuple(destinations)
        self._queue: queue.Queue = queue.Queue(maxsize=capacity)
        self._seq = 0
        self._seq_lock = threading.Lock()
        self._drop_when_full = drop_when_full
        self._dropped = 0                                # observability
        self._closed = False
        self._worker = threading.Thread(
            target=self._drain, name=f"log-{name}", daemon=True,
        )
        self._worker.start()

    # ----- public API --------------------------------------------------------
    def log(self, level: LogLevel, message: str, **context) -> None:
        if level < self.min_level or self._closed:
            return

        # Sequence assignment and enqueue MUST be in the same critical section.
        # Otherwise two threads can grab seq 5 and 6, then race to put(), and
        # record #6 ends up on the queue before record #5. Order would break.
        with self._seq_lock:
            self._seq += 1
            record = LogRecord(
                level=level, message=message, logger_name=self.name,
                timestamp=time.time(), seq=self._seq,
                thread_name=threading.current_thread().name,
                context=context,
            )
            try:
                if self._drop_when_full:
                    self._queue.put_nowait(record)       # non-blocking
                else:
                    self._queue.put(record)              # backpressure
            except queue.Full:
                self._dropped += 1                       # drop oldest-style policy possible here too

    def debug(self, msg, **ctx): self.log(LogLevel.DEBUG, msg, **ctx)
    def info(self, msg, **ctx):  self.log(LogLevel.INFO, msg, **ctx)
    def warn(self, msg, **ctx):  self.log(LogLevel.WARN, msg, **ctx)
    def error(self, msg, **ctx): self.log(LogLevel.ERROR, msg, **ctx)
    def fatal(self, msg, **ctx): self.log(LogLevel.FATAL, msg, **ctx)

    # ----- worker ------------------------------------------------------------
    def _drain(self) -> None:
        while True:
            record = self._queue.get()
            if record is _STOP:
                break
            for dest in self._destinations:
                try:
                    dest.emit(record)
                except Exception as exc:
                    # One broken destination must not stop the others.
                    print(f"logging: {type(dest).__name__} failed: {exc}", file=sys.stderr)
            # Durability: force a flush for anything at ERROR or above.
            if record.level >= LogLevel.ERROR:
                for dest in self._destinations:
                    try: dest.flush()
                    except Exception: pass

    # ----- lifecycle ---------------------------------------------------------
    def shutdown(self, timeout: float | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_STOP)                           # drains everything already queued
        self._worker.join(timeout)
        for dest in self._destinations:
            try: dest.flush(); dest.close()
            except Exception: pass

    # ----- observability -----------------------------------------------------
    @property
    def queue_depth(self) -> int: return self._queue.qsize()
    @property
    def dropped(self) -> int: return self._dropped
```

**Why `daemon=True`:** if the main thread crashes without calling `shutdown`, Python shouldn't hang waiting for the worker. Users should always call `shutdown()`; `daemon=True` is the safety net.

**Why `_STOP` is a sentinel put on the queue, not a flag the worker polls:** polling a flag would race with records enqueued just before the flag was set. Putting `_STOP` on the queue guarantees every record ahead of it is drained first.

**Why `qsize()` and `dropped` are exposed:** you need a way to tell when the queue is backing up in production. Without observability, async logging becomes "silently losing events."

---

## 8. Deep concepts

### 8.1 Why async matters: amortizing I/O cost

A `log.info()` call shouldn't block an HTTP request handler for 5ms writing to disk, and must never block it for 500ms writing over the network. The async design decouples:

- **Caller cost:** build a record, grab a lock briefly, `queue.put`. Microseconds.
- **I/O cost:** paid once per record by one background thread, off the hot path.

### 8.2 Order preservation — why one worker, and why the lock

The requirement says "order of calls preserved within a single application." Two things could break order:

1. **Multiple consumer threads.** Thread A dequeues record 5, thread B dequeues record 6, B is faster → record 6 lands first. **Fix:** one consumer thread.
2. **Enqueue reordering.** Thread A takes `seq=5`, is preempted. Thread B takes `seq=6`, calls `queue.put(record6)`. Now A resumes and calls `queue.put(record5)`. **Fix:** both operations inside the same lock.

```python
with self._seq_lock:
    self._seq += 1
    record = LogRecord(..., seq=self._seq, ...)
    self._queue.put(record)             # inside the lock
```

If you only hold the lock around `self._seq += 1`, order is not guaranteed. This is subtle, and interviewers love it.

> **Caveat to say out loud:** calls from the same thread are always preserved in call-order. For two threads logging *at the exact same moment*, there's no true physical order — the design makes an explicit choice: "whichever acquires the lock first wins, and `seq` records that choice."

### 8.3 Backpressure vs. drop

Queues can fill. Two policies:

| Policy | Call | Behavior | When to use |
|---|---|---|---|
| **Backpressure** | `queue.put(record)` | Blocks the caller until space frees | Correctness > latency. Your app is slow when disk is slow — fine. |
| **Drop** | `queue.put_nowait(record)` + count drops | Caller returns instantly; dropped records are counted | Latency > completeness. Web request serving under load. |

Either is defensible. Say which you picked and why.

> **Hybrid policy, better:** backpressure for `ERROR` and above, drop for `DEBUG`/`INFO`. The important ones never get lost; the chatty ones do. Mention this in an interview — it's a sign you've thought about it.

### 8.4 Reliability: what "reliable" means, concretely

The problem says "reliable." That's vague. Pin it down:

1. **No corruption under concurrency.** Two threads writing to the same file never produce an interleaved line → each destination owns the lock around its backend.
2. **One broken destination doesn't take down the others.** Wrap each `dest.emit()` in `try/except`.
3. **No records lost on clean exit.** `shutdown()` drains the queue and `flush()`es each destination.
4. **Important records never lost on crash.** `flush()` after every record at `ERROR` and above (and maybe `fsync` on the file destination if you really need it).

What async logging **cannot** guarantee: records lost on a hard crash (`kill -9`, power loss) while they're still in the queue. That's an inherent trade-off — call it out and offer sync mode for records that must survive.

### 8.5 Lock placement — where to lock, where not to

| Operation | Lock? | Why |
|---|---|---|
| `self._seq += 1` and `queue.put` | Yes, together | ordering |
| `queue.get` | No, `Queue` is thread-safe internally | library handles it |
| `file.write` | Yes, per-file | avoid interleaved bytes |
| `print` | Yes (shared) | stdout/stderr buffer can interleave under heavy load |
| `dest.emit` in the sync logger | No | each destination handles its own backend lock |
| Reading `self.min_level` | No | int reads are atomic in Python; worst case you see the old value for a nanosecond |

**The rule I keep repeating because I keep violating it:** *don't do I/O while holding a lock that other callers need to progress.* In the sync logger, destinations lock their own file handle, not a global. In the async logger, the worker thread is the only one touching destinations, so caller threads are never blocked on I/O.

### 8.6 Immutable records

```python
@dataclass(frozen=True)
class LogRecord: ...
```

Three reasons:

1. **Safe to share across threads** — the caller builds it, the worker reads it, no synchronization needed.
2. **Safe to fan out** — three destinations each read the same object; none can corrupt it for the next.
3. **Debugging is easier** — if a record looks wrong at destination B, you know it was wrong at destination A too. No "spooky action at a distance."

### 8.7 Template Method — why `emit` is in the base class

```python
class Destination:
    def emit(self, record):          # the ALGORITHM
        if record.level < self.min_level: return
        self._write(self.formatter.format(record))

    @abstractmethod
    def _write(self, line): ...      # the ONE varying step
```

If you put the level check in each subclass, a new destination author will forget it. If you put the format call in each subclass, same. Template Method says: *fix the algorithm in the base class, let subclasses override only the specific step.*

### 8.8 Who owns the formatter: a reusable test

Interviewers push on this. Here's how to answer:

> "The destination owns the formatter because the format is a property of the destination, not the record. The console wants text for humans; the file wants JSON for log shippers; an HTTP destination might want protobuf. If I owned the formatter on the record, the record would have to know about every destination that might consume it — the dependency is upside down."

Apply this test to anything in design: *"if I wanted to change X, which object would I touch?"* That object owns X.

### 8.9 Why not inherit from `Logger`?

Someone will suggest `AuditLogger(Logger)`, `AccessLogger(Logger)`, ... Don't. The behavior is identical; only the name and perhaps the destinations differ. Different value → field. `get_logger("audit")` and `get_logger("access")` give you different loggers with the same class.

### 8.10 Named loggers and hierarchy (optional, but asked often)

Python's stdlib `logging` has a dotted hierarchy: `payments.stripe.webhook` inherits from `payments.stripe` which inherits from `payments`. That lets you set `payments` to `DEBUG` and have the whole subtree inherit it.

How to add it: in `LogManager.get_logger`, walk from the full name up through dot-separated prefixes, inheriting `min_level` and `destinations` from the nearest ancestor that was explicitly configured. Not needed for the base problem, but good to mention.

### 8.11 Comparison to Python's `logging` module

| Concept | Mine | `logging` module |
|---|---|---|
| Logger | `Logger` | `Logger` |
| Record | `LogRecord` | `LogRecord` |
| Destination | `Destination` | `Handler` |
| Formatter | `Formatter` | `Formatter` |
| Async worker | custom queue + thread | `QueueHandler` + `QueueListener` |
| Hierarchy | not implemented | yes, dot-separated |

The vocabulary matches a real design. Interviewers will nod.

---

## 9. My mistakes, with the fix next to each

### M1 — Subclass for each level

❌ What I wrote
```
DebugMessage, InfoMessage, WarnMessage, ErrorMessage, FatalMessage : ILogMessage
```

**Why wrong:** zero behavioral difference between them. Only the level value changes.

✅ Fix
```python
record = LogRecord(level=LogLevel.WARN, message="disk full")
```

**Lesson:** *different value → field; different behavior → subclass*.

---

### M2 — Formatter on the message

❌ What I wrote
```
ILogMessage.formatMessage(message, IFormatter)
```

**Why wrong:** the same record goes to a text console and a JSON file. The record can't choose both. Formatting is per-destination.

✅ Fix
```python
class Destination:
    formatter: Formatter

    def emit(self, record):
        self._write(self.formatter.format(record))
```

**Lesson:** *"If this rule changed, which object would I edit?"* That object owns it.

---

### M3 — Destination missing `min_level`

❌ What I wrote
```
IDestination:
    validateMessage()
```

**Why wrong:** `validateMessage` has nothing to compare against — no `min_level` field.

✅ Fix
```python
class Destination:
    min_level: LogLevel
    def emit(self, record):
        if record.level >= self.min_level:
            self._write(self.formatter.format(record))
```

**Lesson:** *fields first, methods second. If a method has no data to work on, you forgot the data.*

---

### M4 — `LogLevel` not actually ordered

❌ What I wrote
```
enum LOG_LEVEL : DEBUG < INFO < WARN < ERROR < FATAL
```

**Why wrong:** the order was in my comment. The code couldn't compare them.

✅ Fix
```python
class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50
```

**Lesson:** *if a requirement says "ordered," use a type that supports `<`/`>=`.*

---

### M5 — Useless `Config` class

❌ What I wrote
```
Config:
    configId: string
    destinations: List<IDestination>
```

**Why wrong:** wraps a list and nothing else. `configId` is never used. Delete it and nothing breaks.

✅ Fix
```python
logger = Logger(name="payments", destinations=[console, file])
```

**Lesson:** *if deleting a class breaks nothing, delete the class.*

---

### M6 — Designed like a multi-tenant server

❌ What I wrote
```
LogService:
    config: dict<sourceId, Config>
    locks:  dict<sourceId, RLock>
Source: sourceId, applicationName, tag
```

**Why wrong:** this is a package, not a server. Each app imports one copy. There's nothing to look up by `sourceId`.

✅ Fix
```python
log = LogManager.get_logger("payments")
```

**Lesson:** *re-read "it's a package." A package runs inside one process.*

---

### M7 — Lock per source, held during I/O

❌ What I wrote
```
for seat in seatIds: lock.acquire()   # ... then write to file ...
```
(the equivalent in logging: holding the source lock while fanning out to destinations)

**Why wrong:** every app thread waits on disk and network. One slow destination freezes the whole app.

✅ Fix: producer / consumer queue
```python
def log(self, level, msg, **ctx):
    with self._seq_lock:
        self._seq += 1
        self._queue.put(LogRecord(..., seq=self._seq, ...))   # instant

# background worker thread drains the queue; app threads never touch I/O
```

**Lesson:** *slow I/O never runs on the caller's thread; a lock protects data, not an entire pipeline.*

---

### M8 — Awkward API

❌ What I wrote
```python
addLog(source, WarnMessage("disk full"))
```

**Why wrong:** the client has to build a message object every call. Nobody wants that.

✅ Fix
```python
log.warn("disk full", order_id=42)
```

**Lesson:** *write the client code first, in step 1.*

---

### M9 — Implementation section empty

❌ What I wrote
```
addLog(source, ILogMessage)
```
(no body)

**Why wrong:** writing the body is how you catch the design bugs. If I'd tried to write `addLog`'s body, mistakes M2, M3, M7 would have smacked me in the face.

✅ Fix: always write at least one method body during class design, even in pseudocode.

**Lesson:** *the body is the proof.*

---

### Summary of the 9 mistakes, by root cause

| Root cause | Mistakes | Fix habit |
|---|---|---|
| Verified nothing | M9 | Write the main method body, even rough |
| Confused value with class | M1, M4 | "Different value → field" |
| Wrong owner | M2 | "If this changed, which class do I edit?" |
| Methods before fields | M3 | Write fields first |
| Added classes you don't need | M5 | "If I delete it, does anything break?" |
| Misread problem scope | M6, M8 | Write client code first |
| Added locks without thinking | M7 | "What does this lock protect? Is I/O inside?" |

Nothing in that list requires new knowledge. All of it is **sequence of thought**.

---

## 10. Trade-offs to talk about in an interview

### Sync vs async

| | Sync | Async |
|---|---|---|
| Caller latency | high (I/O cost) | low (queue put) |
| Lost on crash | 0 | records still in queue |
| Lost on OOM | 0 | depends on queue policy |
| Order preserved | trivially | needs single consumer + locked enqueue |
| Setup complexity | low | medium |
| Operational complexity | low | need observability on queue depth |

**Default:** async with sync-mode escape hatch for FATAL.

### Backpressure vs drop

- Backpressure: your app slows down with your logging. Honest.
- Drop: your app stays fast but silently loses records. Dangerous if you lose errors.
- **Hybrid:** backpressure for `>= WARN`, drop for `< WARN`.

### One lock vs per-destination lock

Each destination owns its own backend lock. One global lock would serialize unrelated destinations (console and file would wait on each other for no reason).

### Daemon worker vs non-daemon

Daemon worker exits with the process → simpler, risks losing in-flight records on sudden exit. Non-daemon → you *must* call `shutdown` or the process never exits. Daemon with `shutdown` is the right compromise.

---

## 11. Extensions interviewers love to ask

1. **"What if a destination goes down?"** → Retry with exponential backoff inside the destination; after N failures, open a circuit breaker and drop records with a counter; emit an internal metric so operators notice.
2. **"What about rotation?"** → `RotatingFileDestination` wrapping `FileDestination`; the base class doesn't change.
3. **"Multiprocess?"** → Use `multiprocessing.Queue` or `QueueHandler` + a dedicated listener process. Processes don't share memory, so the queue has to be IPC.
4. **"Structured logging?"** → You already have it: `context: dict` on `LogRecord`, `JsonFormatter` to serialize.
5. **"Sampling?"** → A `SamplingDestination(wrapped, rate=0.01)` decorator around another destination.
6. **"Dynamic reconfiguration?"** → `LogManager.configure` already supports it; add `Logger.rebind_destinations(new_tuple)` with a lock.
7. **"Correlation IDs across async calls?"** → `contextvars.ContextVar` for `trace_id`, read inside `Logger.log` and merged into `context`.
8. **"Hierarchy by logger name?"** → See 8.10.

---

## 12. One-page cheatsheet

### Class map (6 classes)

```
LogLevel(IntEnum)
LogRecord(frozen dataclass)       level, message, logger_name, timestamp, seq, thread_name, context
Formatter(ABC)                    .format(record) -> str
    TextFormatter, JsonFormatter
Destination(ABC)                  min_level, formatter
    .emit(record)                 base-class template method
    ._write(line)                 abstract
    ConsoleDestination, FileDestination
Logger / AsyncLogger              name, min_level, destinations, (queue, worker)
    .debug/info/warn/error/fatal(msg, **ctx)
    .shutdown()
LogManager                        configure(), get_logger(name)
```

### Flow

```
log.warn("x", k=v)
  -> level check (fast)
  -> seq++ + build LogRecord      (locked, ordering)
  -> SYNC: for dest: emit         (level check -> format -> write, each in try)
     ASYNC: queue.put(record)     (locked with seq++)
             worker: get -> for dest: emit
  -> flush on >= ERROR
  -> shutdown drains + closes
```

### The 5 steps

1. Write client code
2. Trace one call
3. Fields of each class
4. Signatures + return types + exceptions
5. Main method bodies

### Pre-flight checklist

- [ ] Every method actually mutates state it claims to
- [ ] Every computed value is used or returned
- [ ] Every method called exists on that object's class
- [ ] Enqueue + seq assignment inside the same lock
- [ ] No I/O inside caller-held locks
- [ ] Each destination has `min_level`, `flush`, `close`
- [ ] Immutable record
- [ ] One worker thread (not many) if order matters
- [ ] `shutdown` drains the queue before closing

### My 9 mistakes, in one line each

1. 5 subclasses when a field would do
2. Formatter on the message instead of the destination
3. Destination with no `min_level` field
4. Enum without ordered values
5. `Config` class that did nothing
6. Multi-tenant lookup for a single-process package
7. Lock around the whole pipeline including I/O
8. `addLog(source, WarnMessage(...))` instead of `log.warn(...)`
9. Empty implementation section — didn't write the main method body

**All 9 come from skipping the 5 steps.** Follow them next time.
