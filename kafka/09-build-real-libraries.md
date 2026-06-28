# Build Real Libraries - From Design to Implementation

Building production-quality libraries teaches you software architecture, design patterns, API design, and systems thinking. This guide walks through building 8 complete libraries from scratch in Python—each one used in real production systems.

---

## Table of Contents

1. [Logging Library](#1-logging-library-like-log4j)
2. [Rate Limiter Library](#2-rate-limiter-library)
3. [Retry Framework](#3-retry-framework)
4. [Circuit Breaker Library](#4-circuit-breaker-library)
5. [Task Scheduler Library](#5-task-scheduler-library)
6. [Configuration Framework](#6-configuration-framework)
7. [Caching Library](#7-caching-library)
8. [Event Bus Framework](#8-event-bus-framework)

---

## 1. Logging Library (Like Log4j)

### Requirements Analysis

**Functional Requirements:**
- Log messages at different severity levels
- Route log messages to multiple destinations (console, file, network)
- Format log messages with customizable patterns
- Filter log messages based on criteria
- Support hierarchical logger namespaces (e.g., `app.db.queries`)
- Lazy evaluation of expensive log message construction

**Non-Functional Requirements:**
- Thread-safe for concurrent logging
- Minimal performance impact when log level is disabled
- Extensible (custom handlers, formatters, filters)
- Zero external dependencies

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LoggerFactory                         │
│              (Singleton Registry)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Logger A │    │ Logger B │    │ Logger C │         │
│  │ "app"    │    │ "app.db" │    │ "app.web"│         │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│       │               │               │                │
│       ▼               ▼               ▼                │
│  ┌──────────────────────────────────────────┐          │
│  │           Handler Chain                   │          │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │          │
│  │  │Console  │→ │  File   │→ │Rotating │ │          │
│  │  │Handler  │  │ Handler │  │  File   │ │          │
│  │  └────┬────┘  └────┬────┘  └────┬────┘ │          │
│  └───────┼─────────────┼───────────┼───────┘          │
│          ▼             ▼           ▼                   │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│     │Formatter │  │Formatter │  │Formatter │         │
│     └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Singleton | Logger registry ensures one logger per name |
| Chain of Responsibility | Handlers process log records in sequence |
| Strategy | Formatters are interchangeable formatting strategies |
| Template Method | Base handler defines emit flow, subclasses fill in details |
| Observer | Loggers propagate records to parent loggers |

### Complete Implementation

```python
import sys
import os
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional, TextIO
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# Log Levels
# ═══════════════════════════════════════════════════════════

class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, name: str) -> "Level":
        return cls[name.upper()]


# ═══════════════════════════════════════════════════════════
# Log Record
# ═══════════════════════════════════════════════════════════

@dataclass
class LogRecord:
    """Immutable record of a single log event."""
    logger_name: str
    level: Level
    message: str
    timestamp: float = field(default_factory=time.time)
    thread_name: str = field(default_factory=lambda: threading.current_thread().name)
    thread_id: int = field(default_factory=threading.get_ident)
    exc_info: Optional[tuple] = None
    extra: dict = field(default_factory=dict)

    @property
    def level_name(self) -> str:
        return self.level.name

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)


# ═══════════════════════════════════════════════════════════
# Filters
# ═══════════════════════════════════════════════════════════

class Filter(ABC):
    @abstractmethod
    def should_log(self, record: LogRecord) -> bool:
        pass


class LevelFilter(Filter):
    """Only allow records at or above a certain level."""
    def __init__(self, min_level: Level):
        self.min_level = min_level

    def should_log(self, record: LogRecord) -> bool:
        return record.level >= self.min_level


class NameFilter(Filter):
    """Only allow records from loggers matching a prefix."""
    def __init__(self, name_prefix: str):
        self.name_prefix = name_prefix

    def should_log(self, record: LogRecord) -> bool:
        return record.logger_name.startswith(self.name_prefix)


class CallableFilter(Filter):
    """Filter using an arbitrary callable."""
    def __init__(self, func: Callable[[LogRecord], bool]):
        self._func = func

    def should_log(self, record: LogRecord) -> bool:
        return self._func(record)


# ═══════════════════════════════════════════════════════════
# Formatters (Strategy Pattern)
# ═══════════════════════════════════════════════════════════

class Formatter(ABC):
    @abstractmethod
    def format(self, record: LogRecord) -> str:
        pass


class SimpleFormatter(Formatter):
    """Basic format: LEVEL - message"""
    def format(self, record: LogRecord) -> str:
        return f"{record.level_name} - {record.message}"


class DetailedFormatter(Formatter):
    """Full format with timestamp, thread, logger name."""
    def __init__(self, date_format: str = "%Y-%m-%d %H:%M:%S"):
        self.date_format = date_format

    def format(self, record: LogRecord) -> str:
        ts = record.datetime.strftime(self.date_format)
        parts = [
            f"[{ts}]",
            f"[{record.level_name:8s}]",
            f"[{record.thread_name}]",
            f"[{record.logger_name}]",
            f"- {record.message}",
        ]
        result = " ".join(parts)
        if record.exc_info:
            import traceback
            result += "\n" + "".join(
                traceback.format_exception(*record.exc_info)
            )
        return result


class PatternFormatter(Formatter):
    """
    Format using a pattern string.
    Supported placeholders:
      %(timestamp)s, %(level)s, %(logger)s, %(thread)s,
      %(message)s, %(thread_id)d
    """
    def __init__(self, pattern: str):
        self.pattern = pattern

    def format(self, record: LogRecord) -> str:
        return self.pattern % {
            "timestamp": record.datetime.isoformat(),
            "level": record.level_name,
            "logger": record.logger_name,
            "thread": record.thread_name,
            "thread_id": record.thread_id,
            "message": record.message,
        }


class JSONFormatter(Formatter):
    """Format log records as JSON lines."""
    def format(self, record: LogRecord) -> str:
        import json
        data = {
            "timestamp": record.datetime.isoformat(),
            "level": record.level_name,
            "logger": record.logger_name,
            "thread": record.thread_name,
            "message": record.message,
        }
        if record.extra:
            data["extra"] = record.extra
        return json.dumps(data)


# ═══════════════════════════════════════════════════════════
# Handlers (Chain of Responsibility)
# ═══════════════════════════════════════════════════════════

class Handler(ABC):
    def __init__(self, level: Level = Level.DEBUG,
                 formatter: Optional[Formatter] = None):
        self.level = level
        self.formatter = formatter or SimpleFormatter()
        self._filters: list[Filter] = []
        self._lock = threading.Lock()

    def add_filter(self, f: Filter) -> "Handler":
        self._filters.append(f)
        return self

    def handle(self, record: LogRecord) -> None:
        if record.level < self.level:
            return
        for f in self._filters:
            if not f.should_log(record):
                return
        formatted = self.formatter.format(record)
        with self._lock:
            self.emit(formatted, record)

    @abstractmethod
    def emit(self, formatted_message: str, record: LogRecord) -> None:
        pass

    def close(self) -> None:
        pass


class ConsoleHandler(Handler):
    """Writes log output to stdout or stderr."""
    def __init__(self, stream: TextIO = sys.stderr, **kwargs):
        super().__init__(**kwargs)
        self.stream = stream

    def emit(self, formatted_message: str, record: LogRecord) -> None:
        self.stream.write(formatted_message + "\n")
        self.stream.flush()


class FileHandler(Handler):
    """Writes log output to a file."""
    def __init__(self, filename: str, mode: str = "a", **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.mode = mode
        self._file: Optional[TextIO] = None

    def _ensure_open(self) -> TextIO:
        if self._file is None or self._file.closed:
            os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)
            self._file = open(self.filename, self.mode, encoding="utf-8")
        return self._file

    def emit(self, formatted_message: str, record: LogRecord) -> None:
        f = self._ensure_open()
        f.write(formatted_message + "\n")
        f.flush()

    def close(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()


class RotatingFileHandler(Handler):
    """
    File handler that rotates when file exceeds max_bytes.
    Keeps up to backup_count old files.
    """
    def __init__(self, filename: str, max_bytes: int = 10 * 1024 * 1024,
                 backup_count: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._file: Optional[TextIO] = None
        self._current_size = 0

    def _open(self) -> TextIO:
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)
        f = open(self.filename, "a", encoding="utf-8")
        f.seek(0, 2)  # seek to end
        self._current_size = f.tell()
        return f

    def _rotate(self) -> None:
        if self._file:
            self._file.close()
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.filename}.{i}"
            dst = f"{self.filename}.{i + 1}"
            if os.path.exists(src):
                os.replace(src, dst)
        if os.path.exists(self.filename):
            os.replace(self.filename, f"{self.filename}.1")
        self._file = self._open()

    def emit(self, formatted_message: str, record: LogRecord) -> None:
        if self._file is None:
            self._file = self._open()
        msg_bytes = len(formatted_message.encode("utf-8")) + 1
        if self._current_size + msg_bytes > self.max_bytes:
            self._rotate()
        self._file.write(formatted_message + "\n")
        self._file.flush()
        self._current_size += msg_bytes

    def close(self) -> None:
        if self._file and not self._file.closed:
            self._file.close()


# ═══════════════════════════════════════════════════════════
# Logger
# ═══════════════════════════════════════════════════════════

class Logger:
    """
    A named logger that dispatches log records to handlers.
    Supports hierarchical propagation (app.db propagates to app).
    """
    def __init__(self, name: str, level: Level = Level.DEBUG):
        self.name = name
        self.level = level
        self._handlers: list[Handler] = []
        self._parent: Optional["Logger"] = None
        self.propagate = True

    def add_handler(self, handler: Handler) -> "Logger":
        self._handlers.append(handler)
        return self

    def remove_handler(self, handler: Handler) -> None:
        self._handlers.remove(handler)

    def set_level(self, level: Level) -> None:
        self.level = level

    def is_enabled_for(self, level: Level) -> bool:
        return level >= self.level

    def _log(self, level: Level, message, *args,
             exc_info=None, **kwargs) -> None:
        if not self.is_enabled_for(level):
            return
        # Lazy evaluation: only format if we're going to log
        if callable(message):
            message = message()
        elif args:
            message = message % args

        record = LogRecord(
            logger_name=self.name,
            level=level,
            message=str(message),
            exc_info=exc_info,
            extra=kwargs,
        )
        self._dispatch(record)

    def _dispatch(self, record: LogRecord) -> None:
        for handler in self._handlers:
            handler.handle(record)
        if self.propagate and self._parent:
            self._parent._dispatch(record)

    def debug(self, message, *args, **kwargs) -> None:
        self._log(Level.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs) -> None:
        self._log(Level.INFO, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs) -> None:
        self._log(Level.WARNING, message, *args, **kwargs)

    def error(self, message, *args, **kwargs) -> None:
        self._log(Level.ERROR, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs) -> None:
        self._log(Level.CRITICAL, message, *args, **kwargs)

    def exception(self, message, *args, **kwargs) -> None:
        kwargs["exc_info"] = sys.exc_info()
        self._log(Level.ERROR, message, *args, **kwargs)


# ═══════════════════════════════════════════════════════════
# Logger Factory (Singleton Registry)
# ═══════════════════════════════════════════════════════════

class LoggerFactory:
    """
    Thread-safe singleton registry for loggers.
    Creates hierarchical logger relationships automatically.
    """
    _instance: Optional["LoggerFactory"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggerFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._loggers = {}
                    cls._instance._root = Logger("root", Level.WARNING)
        return cls._instance

    def get_logger(self, name: str) -> Logger:
        if name in self._loggers:
            return self._loggers[name]
        with self._lock:
            if name in self._loggers:
                return self._loggers[name]
            logger = Logger(name)
            # Set up hierarchy
            parent_name = name.rsplit(".", 1)[0] if "." in name else "root"
            if parent_name == name:
                logger._parent = self._root
            else:
                logger._parent = self.get_logger(parent_name)
            self._loggers[name] = logger
            return logger

    @property
    def root(self) -> Logger:
        return self._root

    def reset(self) -> None:
        """Reset all loggers (useful for testing)."""
        with self._lock:
            for logger in self._loggers.values():
                for handler in logger._handlers:
                    handler.close()
            self._loggers.clear()


def get_logger(name: str) -> Logger:
    """Module-level convenience function."""
    return LoggerFactory().get_logger(name)
```

### Usage Examples

```python
# Basic usage
logger = get_logger("myapp")
logger.set_level(Level.DEBUG)
logger.add_handler(
    ConsoleHandler(
        stream=sys.stdout,
        formatter=DetailedFormatter()
    )
)

logger.info("Application started")
logger.debug("Processing item %s", item_id)
logger.error("Failed to connect to database")

# Lazy evaluation for expensive messages
logger.debug(lambda: f"Object state: {expensive_serialization()}")

# Hierarchical loggers
db_logger = get_logger("myapp.db")
# db_logger propagates to "myapp" logger automatically

# Rotating file handler
file_handler = RotatingFileHandler(
    filename="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    formatter=JSONFormatter(),
    level=Level.INFO,
)
logger.add_handler(file_handler)

# Custom filter
logger.add_handler(
    ConsoleHandler(level=Level.ERROR)
    .add_filter(CallableFilter(
        lambda r: "sensitive" not in r.message
    ))
)

# Exception logging
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

### Unit Test Example

```python
import unittest
from io import StringIO


class TestLogger(unittest.TestCase):
    def setUp(self):
        LoggerFactory().reset()
        self.output = StringIO()
        self.handler = ConsoleHandler(
            stream=self.output,
            formatter=SimpleFormatter()
        )

    def test_basic_logging(self):
        logger = get_logger("test")
        logger.add_handler(self.handler)
        logger.info("hello")
        self.assertIn("INFO - hello", self.output.getvalue())

    def test_level_filtering(self):
        logger = get_logger("test")
        logger.set_level(Level.WARNING)
        logger.add_handler(self.handler)
        logger.debug("should not appear")
        logger.warning("should appear")
        output = self.output.getvalue()
        self.assertNotIn("should not appear", output)
        self.assertIn("should appear", output)

    def test_hierarchy_propagation(self):
        parent = get_logger("app")
        parent.add_handler(self.handler)
        child = get_logger("app.module")
        child.info("from child")
        self.assertIn("from child", self.output.getvalue())

    def test_lazy_evaluation(self):
        logger = get_logger("test")
        logger.set_level(Level.ERROR)
        logger.add_handler(self.handler)
        called = []
        logger.debug(lambda: called.append(1) or "expensive")
        self.assertEqual(called, [])  # Never evaluated
```

---

## 2. Rate Limiter Library

### Requirements Analysis

**Functional Requirements:**
- Support multiple rate limiting algorithms
- Configurable limits (requests per time window)
- Thread-safe for concurrent access
- Clean decorator interface for easy integration
- Support per-key limiting (e.g., per user, per IP)

**Non-Functional Requirements:**
- O(1) time complexity for check operations where possible
- Memory-efficient for large numbers of keys
- Accurate limiting under high concurrency
- Extensible for custom algorithms

### Architecture

```
┌────────────────────────────────────────────────────────┐
│                  RateLimiter API                        │
│           (Decorator / Context Manager)                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐      │
│  │   Token    │  │   Fixed    │  │  Sliding   │      │
│  │   Bucket   │  │  Window    │  │  Window    │      │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘      │
│        │               │               │              │
│        ▼               ▼               ▼              │
│  ┌────────────────────────────────────────────────┐   │
│  │              Storage Backend                    │   │
│  │      (In-Memory / Thread-Safe Dict)            │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Strategy | Each algorithm is an interchangeable strategy |
| Decorator | Clean `@rate_limit` interface |
| Factory | Create appropriate limiter from config |
| Template Method | Base class defines `allow()` flow |

### Complete Implementation

```python
import time
import threading
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional


# ═══════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════

class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded."""
    def __init__(self, retry_after: float = 0.0):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after:.2f}s"
        )


# ═══════════════════════════════════════════════════════════
# Result Type
# ═══════════════════════════════════════════════════════════

@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    limit: int
    retry_after: float = 0.0
    reset_at: float = 0.0


# ═══════════════════════════════════════════════════════════
# Base Rate Limiter
# ═══════════════════════════════════════════════════════════

class RateLimiter(ABC):
    @abstractmethod
    def allow(self, key: str = "default") -> RateLimitResult:
        """Check if request is allowed. Returns result with metadata."""
        pass

    @abstractmethod
    def reset(self, key: str = "default") -> None:
        """Reset the rate limit state for a key."""
        pass


# ═══════════════════════════════════════════════════════════
# Token Bucket Algorithm
# ═══════════════════════════════════════════════════════════

class TokenBucket(RateLimiter):
    """
    Token Bucket: Tokens are added at a fixed rate. Each request
    consumes one token. Allows bursts up to bucket capacity.

    Good for: APIs that allow bursting but enforce average rate.
    """
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in the bucket (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def _get_tokens(self, key: str) -> tuple[float, float]:
        """Returns (current_tokens, last_refill_time)."""
        now = time.monotonic()
        if key not in self._buckets:
            return (float(self.capacity), now)
        tokens, last_time = self._buckets[key]
        elapsed = now - last_time
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)
        return (tokens, now)

    def allow(self, key: str = "default") -> RateLimitResult:
        with self._lock:
            tokens, now = self._get_tokens(key)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return RateLimitResult(
                    allowed=True,
                    remaining=int(tokens - 1),
                    limit=self.capacity,
                )
            else:
                self._buckets[key] = (tokens, now)
                wait_time = (1.0 - tokens) / self.refill_rate
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self.capacity,
                    retry_after=wait_time,
                )

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._buckets.pop(key, None)


# ═══════════════════════════════════════════════════════════
# Fixed Window Counter
# ═══════════════════════════════════════════════════════════

class FixedWindowCounter(RateLimiter):
    """
    Fixed Window: Counts requests in fixed time windows.
    Simple but has boundary burst problem.

    Good for: Simple rate limiting where boundary precision isn't critical.
    """
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, tuple[int, int]] = {}  # key -> (window_id, count)
        self._lock = threading.Lock()

    def _get_window_id(self) -> int:
        return int(time.time() / self.window_seconds)

    def allow(self, key: str = "default") -> RateLimitResult:
        with self._lock:
            current_window = self._get_window_id()
            if key not in self._windows:
                self._windows[key] = (current_window, 0)

            window_id, count = self._windows[key]
            if window_id != current_window:
                window_id = current_window
                count = 0

            if count < self.max_requests:
                count += 1
                self._windows[key] = (window_id, count)
                reset_at = (window_id + 1) * self.window_seconds
                return RateLimitResult(
                    allowed=True,
                    remaining=self.max_requests - count,
                    limit=self.max_requests,
                    reset_at=reset_at,
                )
            else:
                reset_at = (window_id + 1) * self.window_seconds
                retry_after = reset_at - time.time()
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self.max_requests,
                    retry_after=max(0.0, retry_after),
                    reset_at=reset_at,
                )

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._windows.pop(key, None)


# ═══════════════════════════════════════════════════════════
# Sliding Window Log
# ═══════════════════════════════════════════════════════════

class SlidingWindowLog(RateLimiter):
    """
    Sliding Window Log: Keeps timestamps of all requests within the window.
    Most accurate but uses more memory.

    Good for: When precision matters more than memory usage.
    """
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._logs: dict[str, deque] = {}
        self._lock = threading.Lock()

    def _cleanup(self, key: str, now: float) -> None:
        if key in self._logs:
            cutoff = now - self.window_seconds
            log = self._logs[key]
            while log and log[0] <= cutoff:
                log.popleft()

    def allow(self, key: str = "default") -> RateLimitResult:
        with self._lock:
            now = time.time()
            if key not in self._logs:
                self._logs[key] = deque()
            self._cleanup(key, now)
            log = self._logs[key]

            if len(log) < self.max_requests:
                log.append(now)
                return RateLimitResult(
                    allowed=True,
                    remaining=self.max_requests - len(log),
                    limit=self.max_requests,
                )
            else:
                oldest = log[0]
                retry_after = oldest + self.window_seconds - now
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self.max_requests,
                    retry_after=max(0.0, retry_after),
                )

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._logs.pop(key, None)


# ═══════════════════════════════════════════════════════════
# Sliding Window Counter
# ═══════════════════════════════════════════════════════════

class SlidingWindowCounter(RateLimiter):
    """
    Sliding Window Counter: Approximates sliding window using weighted
    counts from current and previous windows.

    Good for: Balance between accuracy and memory efficiency.
    """
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> (prev_window_id, prev_count, curr_window_id, curr_count)
        self._state: dict[str, tuple[int, int, int, int]] = {}
        self._lock = threading.Lock()

    def _get_window_id(self) -> int:
        return int(time.time() / self.window_seconds)

    def _get_weighted_count(self, key: str) -> float:
        now = time.time()
        current_window = self._get_window_id()
        elapsed_in_window = now - (current_window * self.window_seconds)
        weight = elapsed_in_window / self.window_seconds

        if key not in self._state:
            return 0.0

        prev_wid, prev_count, curr_wid, curr_count = self._state[key]

        if curr_wid != current_window:
            if curr_wid == current_window - 1:
                prev_count = curr_count
            else:
                prev_count = 0
            curr_count = 0

        return curr_count + prev_count * (1 - weight)

    def allow(self, key: str = "default") -> RateLimitResult:
        with self._lock:
            current_window = self._get_window_id()
            weighted = self._get_weighted_count(key)

            if weighted < self.max_requests:
                if key not in self._state:
                    self._state[key] = (0, 0, current_window, 1)
                else:
                    prev_wid, prev_count, curr_wid, curr_count = self._state[key]
                    if curr_wid != current_window:
                        prev_count = curr_count if curr_wid == current_window - 1 else 0
                        curr_count = 0
                    curr_count += 1
                    self._state[key] = (current_window - 1, prev_count,
                                        current_window, curr_count)
                return RateLimitResult(
                    allowed=True,
                    remaining=max(0, int(self.max_requests - weighted - 1)),
                    limit=self.max_requests,
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self.max_requests,
                    retry_after=self.window_seconds * 0.1,
                )

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._state.pop(key, None)


# ═══════════════════════════════════════════════════════════
# Leaky Bucket
# ═══════════════════════════════════════════════════════════

class LeakyBucket(RateLimiter):
    """
    Leaky Bucket: Requests enter a queue that drains at a fixed rate.
    Smooths out bursts into a steady stream.

    Good for: Smoothing traffic, ensuring constant output rate.
    """
    def __init__(self, capacity: int, leak_rate: float):
        """
        Args:
            capacity: Maximum queue size
            leak_rate: Requests processed per second
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self._queues: dict[str, tuple[float, float]] = {}  # key -> (water_level, last_check)
        self._lock = threading.Lock()

    def allow(self, key: str = "default") -> RateLimitResult:
        with self._lock:
            now = time.monotonic()
            if key not in self._queues:
                self._queues[key] = (1.0, now)
                return RateLimitResult(
                    allowed=True,
                    remaining=self.capacity - 1,
                    limit=self.capacity,
                )

            water_level, last_check = self._queues[key]
            elapsed = now - last_check
            leaked = elapsed * self.leak_rate
            water_level = max(0.0, water_level - leaked)

            if water_level < self.capacity:
                water_level += 1.0
                self._queues[key] = (water_level, now)
                return RateLimitResult(
                    allowed=True,
                    remaining=int(self.capacity - water_level),
                    limit=self.capacity,
                )
            else:
                self._queues[key] = (water_level, now)
                retry_after = 1.0 / self.leak_rate
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self.capacity,
                    retry_after=retry_after,
                )

    def reset(self, key: str = "default") -> None:
        with self._lock:
            self._queues.pop(key, None)


# ═══════════════════════════════════════════════════════════
# Decorator Interface
# ═══════════════════════════════════════════════════════════

def rate_limit(limiter: RateLimiter,
               key_func: Optional[Callable] = None,
               on_limited: Optional[Callable] = None):
    """
    Decorator that applies rate limiting to a function.

    Args:
        limiter: The rate limiter instance to use
        key_func: Optional function to extract key from args
        on_limited: Optional callback when rate limited
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else "default"
            result = limiter.allow(key)
            if result.allowed:
                return func(*args, **kwargs)
            else:
                if on_limited:
                    return on_limited(result)
                raise RateLimitExceeded(result.retry_after)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════

class RateLimiterFactory:
    """Create rate limiters from configuration."""

    @staticmethod
    def create(algorithm: str, **kwargs) -> RateLimiter:
        algorithms = {
            "token_bucket": TokenBucket,
            "fixed_window": FixedWindowCounter,
            "sliding_window_log": SlidingWindowLog,
            "sliding_window_counter": SlidingWindowCounter,
            "leaky_bucket": LeakyBucket,
        }
        if algorithm not in algorithms:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. "
                f"Available: {list(algorithms.keys())}"
            )
        return algorithms[algorithm](**kwargs)
```

### Usage Examples

```python
# Token Bucket: 100 requests, refills at 10/sec
limiter = TokenBucket(capacity=100, refill_rate=10)
result = limiter.allow("user_123")
if result.allowed:
    process_request()
else:
    time.sleep(result.retry_after)

# Decorator usage
api_limiter = FixedWindowCounter(max_requests=60, window_seconds=60)

@rate_limit(
    api_limiter,
    key_func=lambda request: request.client_ip,
    on_limited=lambda r: {"error": "too many requests", "retry_after": r.retry_after}
)
def handle_api_request(request):
    return {"data": "response"}

# Factory usage
limiter = RateLimiterFactory.create(
    "sliding_window_log",
    max_requests=1000,
    window_seconds=3600,
)
```

---

## 3. Retry Framework

### Requirements Analysis

**Functional Requirements:**
- Retry failed operations with configurable strategies
- Support multiple backoff algorithms (fixed, exponential, jitter)
- Allow filtering which exceptions trigger retries
- Provide hooks for monitoring retry behavior
- Support retry budgets to prevent retry storms
- Offer both decorator and context manager interfaces

**Non-Functional Requirements:**
- Minimal overhead for successful operations
- Thread-safe retry state
- Clear error reporting with full attempt history
- Cancellable retry loops

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  User Interface Layer                     │
│       @retry decorator  |  RetryContext manager          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌──────────────┐                   │
│  │ RetryPolicy │───▶│RetryExecutor │                   │
│  │             │    │              │                   │
│  │ - max_tries │    │ - execute()  │                   │
│  │ - backoff   │    │ - attempt()  │                   │
│  │ - filters   │    │              │                   │
│  └─────────────┘    └──────┬───────┘                   │
│                            │                            │
│            ┌───────────────┼───────────────┐           │
│            ▼               ▼               ▼           │
│     ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│     │  Fixed   │    │  Expo    │    │  Jitter  │     │
│     │ Backoff  │    │ Backoff  │    │ Backoff  │     │
│     └──────────┘    └──────────┘    └──────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              RetryListeners                       │  │
│  │   on_retry() | on_success() | on_failure()       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Strategy | Backoff algorithms are interchangeable strategies |
| Observer | Listeners observe retry events |
| Builder | Fluent API for constructing retry policies |
| Decorator | `@retry` wraps functions transparently |
| Command | Each retry attempt encapsulated as an operation |

### Complete Implementation

```python
import time
import random
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Optional, Type
from contextlib import contextmanager


# ═══════════════════════════════════════════════════════════
# Backoff Strategies
# ═══════════════════════════════════════════════════════════

class BackoffStrategy(ABC):
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Return delay in seconds before the next retry."""
        pass


class FixedBackoff(BackoffStrategy):
    """Wait a fixed amount of time between retries."""
    def __init__(self, delay: float = 1.0):
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        return self.delay


class ExponentialBackoff(BackoffStrategy):
    """
    Exponential backoff: delay doubles with each attempt.
    delay = base * (multiplier ^ attempt), capped at max_delay.
    """
    def __init__(self, base: float = 1.0, multiplier: float = 2.0,
                 max_delay: float = 60.0):
        self.base = base
        self.multiplier = multiplier
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        delay = self.base * (self.multiplier ** attempt)
        return min(delay, self.max_delay)


class ExponentialBackoffWithJitter(BackoffStrategy):
    """
    Exponential backoff with random jitter to prevent thundering herd.
    Uses "full jitter": uniform random between 0 and exponential delay.
    """
    def __init__(self, base: float = 1.0, multiplier: float = 2.0,
                 max_delay: float = 60.0):
        self.base = base
        self.multiplier = multiplier
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        exp_delay = self.base * (self.multiplier ** attempt)
        capped = min(exp_delay, self.max_delay)
        return random.uniform(0, capped)


class DecorrelatedJitter(BackoffStrategy):
    """
    AWS-style decorrelated jitter.
    delay = random(base, previous_delay * 3), capped at max_delay.
    """
    def __init__(self, base: float = 1.0, max_delay: float = 60.0):
        self.base = base
        self.max_delay = max_delay
        self._last_delay = base

    def get_delay(self, attempt: int) -> float:
        delay = random.uniform(self.base, self._last_delay * 3)
        delay = min(delay, self.max_delay)
        self._last_delay = delay
        return delay


# ═══════════════════════════════════════════════════════════
# Attempt Record
# ═══════════════════════════════════════════════════════════

@dataclass
class AttemptRecord:
    """Record of a single retry attempt."""
    attempt_number: int
    timestamp: float
    exception: Optional[Exception] = None
    result: object = None
    delay_before: float = 0.0


@dataclass
class RetryResult:
    """Final result of a retry operation."""
    success: bool
    result: object = None
    final_exception: Optional[Exception] = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    total_time: float = 0.0

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)


# ═══════════════════════════════════════════════════════════
# Retry Listeners
# ═══════════════════════════════════════════════════════════

class RetryListener(ABC):
    """Observer interface for retry events."""
    def on_retry(self, attempt: AttemptRecord, next_delay: float) -> None:
        pass

    def on_success(self, result: RetryResult) -> None:
        pass

    def on_failure(self, result: RetryResult) -> None:
        pass


class LoggingListener(RetryListener):
    """Logs retry events (integrates with our logging library)."""
    def __init__(self, logger=None):
        self.logger = logger

    def on_retry(self, attempt: AttemptRecord, next_delay: float) -> None:
        msg = (
            f"Retry attempt {attempt.attempt_number} failed: "
            f"{attempt.exception}. Retrying in {next_delay:.2f}s"
        )
        if self.logger:
            self.logger.warning(msg)
        else:
            print(msg)

    def on_failure(self, result: RetryResult) -> None:
        msg = (
            f"All {result.attempt_count} attempts failed. "
            f"Total time: {result.total_time:.2f}s"
        )
        if self.logger:
            self.logger.error(msg)
        else:
            print(msg)


# ═══════════════════════════════════════════════════════════
# Retry Budget
# ═══════════════════════════════════════════════════════════

class RetryBudget:
    """
    Limits total retries within a time window to prevent retry storms.
    Shared across all operations using this budget.
    """
    def __init__(self, max_retries: int, window_seconds: float):
        self.max_retries = max_retries
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Try to acquire a retry token. Returns False if budget exhausted."""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) < self.max_retries:
                self._timestamps.append(now)
                return True
            return False

    @property
    def remaining(self) -> int:
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            active = sum(1 for t in self._timestamps if t > cutoff)
            return max(0, self.max_retries - active)


# ═══════════════════════════════════════════════════════════
# Retry Policy (Builder Pattern)
# ═══════════════════════════════════════════════════════════

class RetryPolicy:
    """
    Configures retry behavior. Use fluent builder methods.
    """
    def __init__(self):
        self.max_attempts: int = 3
        self.backoff: BackoffStrategy = ExponentialBackoff()
        self.retry_on: tuple[Type[Exception], ...] = (Exception,)
        self.retry_if: Optional[Callable[[Exception], bool]] = None
        self.budget: Optional[RetryBudget] = None
        self.listeners: list[RetryListener] = []
        self.timeout: Optional[float] = None

    def with_max_attempts(self, n: int) -> "RetryPolicy":
        self.max_attempts = n
        return self

    def with_backoff(self, strategy: BackoffStrategy) -> "RetryPolicy":
        self.backoff = strategy
        return self

    def with_retry_on(self, *exceptions: Type[Exception]) -> "RetryPolicy":
        self.retry_on = exceptions
        return self

    def with_retry_if(self, predicate: Callable[[Exception], bool]) -> "RetryPolicy":
        self.retry_if = predicate
        return self

    def with_budget(self, budget: RetryBudget) -> "RetryPolicy":
        self.budget = budget
        return self

    def with_listener(self, listener: RetryListener) -> "RetryPolicy":
        self.listeners.append(listener)
        return self

    def with_timeout(self, seconds: float) -> "RetryPolicy":
        self.timeout = seconds
        return self

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        if not isinstance(exception, self.retry_on):
            return False
        if self.retry_if and not self.retry_if(exception):
            return False
        return True


# ═══════════════════════════════════════════════════════════
# Retry Executor
# ═══════════════════════════════════════════════════════════

class RetryExecutor:
    """Executes a callable with retry logic."""

    def __init__(self, policy: RetryPolicy):
        self.policy = policy

    def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        attempts: list[AttemptRecord] = []
        start_time = time.time()

        for attempt_num in range(1, self.policy.max_attempts + 1):
            if self.policy.timeout:
                elapsed = time.time() - start_time
                if elapsed >= self.policy.timeout:
                    break

            record = AttemptRecord(
                attempt_number=attempt_num,
                timestamp=time.time(),
            )

            try:
                result = func(*args, **kwargs)
                record.result = result
                attempts.append(record)
                retry_result = RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                )
                for listener in self.policy.listeners:
                    listener.on_success(retry_result)
                return retry_result

            except Exception as e:
                record.exception = e
                attempts.append(record)

                is_last_attempt = attempt_num == self.policy.max_attempts
                if is_last_attempt or not self.policy.should_retry(e):
                    break

                if self.policy.budget and not self.policy.budget.acquire():
                    break

                delay = self.policy.backoff.get_delay(attempt_num - 1)
                record.delay_before = delay

                for listener in self.policy.listeners:
                    listener.on_retry(record, delay)

                time.sleep(delay)

        final_result = RetryResult(
            success=False,
            final_exception=attempts[-1].exception if attempts else None,
            attempts=attempts,
            total_time=time.time() - start_time,
        )
        for listener in self.policy.listeners:
            listener.on_failure(final_result)
        return final_result


# ═══════════════════════════════════════════════════════════
# Decorator Interface
# ═══════════════════════════════════════════════════════════

def retry(policy: Optional[RetryPolicy] = None, **kwargs):
    """
    Decorator that retries a function on failure.

    Can be used as:
        @retry()
        @retry(policy=my_policy)
        @retry(max_attempts=5, backoff=ExponentialBackoff())
    """
    if policy is None:
        policy = RetryPolicy()
        if "max_attempts" in kwargs:
            policy.with_max_attempts(kwargs["max_attempts"])
        if "backoff" in kwargs:
            policy.with_backoff(kwargs["backoff"])
        if "retry_on" in kwargs:
            policy.with_retry_on(*kwargs["retry_on"])

    executor = RetryExecutor(policy)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kw):
            result = executor.execute(func, *args, **kw)
            if result.success:
                return result.result
            raise result.final_exception
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
# Context Manager Interface
# ═══════════════════════════════════════════════════════════

class RetryContext:
    """
    Context manager for retry logic around code blocks.

    Usage:
        with RetryContext(policy) as ctx:
            for attempt in ctx:
                with attempt:
                    do_something()
    """
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        self._attempts: list[AttemptRecord] = []
        self._success = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __iter__(self):
        for attempt_num in range(1, self.policy.max_attempts + 1):
            yield RetryAttempt(self, attempt_num)
            if self._success:
                break

    def _record_success(self):
        self._success = True

    def _record_failure(self, attempt_num: int, exception: Exception):
        record = AttemptRecord(
            attempt_number=attempt_num,
            timestamp=time.time(),
            exception=exception,
        )
        self._attempts.append(record)

        if attempt_num < self.policy.max_attempts:
            if self.policy.should_retry(exception):
                delay = self.policy.backoff.get_delay(attempt_num - 1)
                time.sleep(delay)
            else:
                raise exception
        else:
            raise exception


class RetryAttempt:
    """Represents a single attempt within a RetryContext."""
    def __init__(self, ctx: RetryContext, attempt_num: int):
        self._ctx = ctx
        self._attempt_num = attempt_num

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._ctx._record_success()
            return False
        self._ctx._record_failure(self._attempt_num, exc_val)
        return True  # Suppress exception for retry
```

### Usage Examples

```python
# Simple decorator usage
@retry(max_attempts=3, backoff=ExponentialBackoff(base=0.5))
def fetch_data(url: str):
    response = http_get(url)
    if response.status >= 500:
        raise ServerError(f"Status {response.status}")
    return response.json()

# Advanced policy with builder pattern
policy = (
    RetryPolicy()
    .with_max_attempts(5)
    .with_backoff(ExponentialBackoffWithJitter(base=1.0, max_delay=30.0))
    .with_retry_on(ConnectionError, TimeoutError)
    .with_retry_if(lambda e: "temporary" in str(e).lower())
    .with_listener(LoggingListener())
    .with_timeout(120.0)
)

@retry(policy=policy)
def call_external_service():
    return service_client.make_request()

# Context manager usage
policy = RetryPolicy().with_max_attempts(3)
with RetryContext(policy) as ctx:
    for attempt in ctx:
        with attempt:
            connection = database.connect()
            result = connection.execute(query)

# Shared retry budget across services
budget = RetryBudget(max_retries=100, window_seconds=60)
policy_a = RetryPolicy().with_budget(budget)
policy_b = RetryPolicy().with_budget(budget)
```

---

## 4. Circuit Breaker Library

### Requirements Analysis

**Functional Requirements:**
- Track failure rates for protected operations
- Automatically stop calling failing services (open state)
- Periodically test if service has recovered (half-open state)
- Resume normal operation when service recovers (closed state)
- Provide metrics and events for monitoring

**Non-Functional Requirements:**
- Thread-safe state transitions
- Minimal overhead in closed state
- Configurable thresholds and timeouts
- Integration with retry framework

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Circuit Breaker                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────── State Machine ─────────────────┐        │
│  │                                                 │        │
│  │   ┌────────┐  failures    ┌────────┐           │        │
│  │   │ CLOSED │──────────▶│  OPEN  │           │        │
│  │   │        │  >= thresh   │        │           │        │
│  │   └────┬───┘             └───┬────┘           │        │
│  │        ▲                     │                 │        │
│  │        │ success             │ timeout         │        │
│  │        │                     ▼                 │        │
│  │        │              ┌───────────┐            │        │
│  │        └──────────────│ HALF-OPEN │            │        │
│  │            (trial     │           │            │        │
│  │             succeeds) └─────┬─────┘            │        │
│  │                             │                  │        │
│  │                             │ trial fails      │        │
│  │                             ▼                  │        │
│  │                        back to OPEN            │        │
│  └─────────────────────────────────────────────────┘        │
│                                                             │
│  ┌──────────────── Metrics ──────────────────────┐         │
│  │  total_calls | failures | successes | state   │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| State | Circuit breaker states with distinct behaviors |
| Observer | Event callbacks on state transitions |
| Decorator | `@circuit_breaker` function wrapper |
| Proxy | Breaker acts as proxy to the real operation |

### Complete Implementation

```python
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Callable, Optional, Type


# ═══════════════════════════════════════════════════════════
# States and Events
# ═══════════════════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject all calls
    HALF_OPEN = auto()   # Testing if service recovered


class CircuitEvent(Enum):
    STATE_CHANGE = auto()
    CALL_SUCCESS = auto()
    CALL_FAILURE = auto()
    CALL_REJECTED = auto()


# ═══════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════

class CircuitBreakerOpen(Exception):
    """Raised when circuit is open and call is rejected."""
    def __init__(self, breaker_name: str, retry_after: float):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. "
            f"Retry after {retry_after:.1f}s"
        )


# ═══════════════════════════════════════════════════════════
# Metrics
# ═══════════════════════════════════════════════════════════

@dataclass
class CircuitMetrics:
    """Tracks circuit breaker performance metrics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: list[tuple[float, CircuitState]] = field(
        default_factory=list
    )

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    def record_success(self) -> None:
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_time = time.time()

    def record_failure(self) -> None:
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = time.time()

    def record_rejected(self) -> None:
        self.rejected_calls += 1

    def record_state_change(self, new_state: CircuitState) -> None:
        self.state_changes.append((time.time(), new_state))

    def reset(self) -> None:
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0


# ═══════════════════════════════════════════════════════════
# Sliding Window for Failure Tracking
# ═══════════════════════════════════════════════════════════

class SlidingWindowMetrics:
    """Tracks successes/failures in a rolling time window."""
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._outcomes: list[bool] = []  # True=success, False=failure

    def record(self, success: bool) -> None:
        self._outcomes.append(success)
        if len(self._outcomes) > self.window_size:
            self._outcomes.pop(0)

    @property
    def failure_count(self) -> int:
        return sum(1 for o in self._outcomes if not o)

    @property
    def success_count(self) -> int:
        return sum(1 for o in self._outcomes if o)

    @property
    def total_count(self) -> int:
        return len(self._outcomes)

    @property
    def failure_rate(self) -> float:
        if not self._outcomes:
            return 0.0
        return self.failure_count / len(self._outcomes)

    def reset(self) -> None:
        self._outcomes.clear()


# ═══════════════════════════════════════════════════════════
# Circuit Breaker Configuration
# ═══════════════════════════════════════════════════════════

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: float = 30.0       # Seconds before trying half-open
    window_size: int = 10       # Sliding window for failure counting
    failure_rate_threshold: float = 0.5
    excluded_exceptions: tuple[Type[Exception], ...] = ()
    included_exceptions: tuple[Type[Exception], ...] = (Exception,)


# ═══════════════════════════════════════════════════════════
# Circuit Breaker States (State Pattern)
# ═══════════════════════════════════════════════════════════

class State(ABC):
    def __init__(self, breaker: "CircuitBreaker"):
        self.breaker = breaker

    @abstractmethod
    def on_success(self) -> None:
        pass

    @abstractmethod
    def on_failure(self) -> None:
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        pass

    @property
    @abstractmethod
    def state_type(self) -> CircuitState:
        pass


class ClosedState(State):
    """Normal operation. Tracking failures."""
    @property
    def state_type(self) -> CircuitState:
        return CircuitState.CLOSED

    def can_execute(self) -> bool:
        return True

    def on_success(self) -> None:
        self.breaker._window.record(True)

    def on_failure(self) -> None:
        self.breaker._window.record(False)
        config = self.breaker._config
        if (self.breaker._window.failure_count >= config.failure_threshold or
                self.breaker._window.failure_rate >= config.failure_rate_threshold):
            self.breaker._transition_to(OpenState(self.breaker))


class OpenState(State):
    """Circuit is open. All calls are rejected."""
    def __init__(self, breaker: "CircuitBreaker"):
        super().__init__(breaker)
        self._opened_at = time.monotonic()

    @property
    def state_type(self) -> CircuitState:
        return CircuitState.OPEN

    def can_execute(self) -> bool:
        if time.monotonic() - self._opened_at >= self.breaker._config.timeout:
            self.breaker._transition_to(HalfOpenState(self.breaker))
            return True
        return False

    def on_success(self) -> None:
        pass

    def on_failure(self) -> None:
        pass


class HalfOpenState(State):
    """Testing if service recovered. Limited calls allowed."""
    def __init__(self, breaker: "CircuitBreaker"):
        super().__init__(breaker)
        self._success_count = 0

    @property
    def state_type(self) -> CircuitState:
        return CircuitState.HALF_OPEN

    def can_execute(self) -> bool:
        return True

    def on_success(self) -> None:
        self._success_count += 1
        if self._success_count >= self.breaker._config.success_threshold:
            self.breaker._window.reset()
            self.breaker._transition_to(ClosedState(self.breaker))

    def on_failure(self) -> None:
        self.breaker._transition_to(OpenState(self.breaker))


# ═══════════════════════════════════════════════════════════
# Circuit Breaker
# ═══════════════════════════════════════════════════════════

class CircuitBreaker:
    """
    Production-quality circuit breaker implementation.
    Thread-safe with metrics and event callbacks.
    """
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self._config = config or CircuitBreakerConfig()
        self._window = SlidingWindowMetrics(self._config.window_size)
        self._state: State = ClosedState(self)
        self._metrics = CircuitMetrics()
        self._lock = threading.RLock()
        self._listeners: list[Callable[[CircuitEvent, dict], None]] = []

    @property
    def state(self) -> CircuitState:
        return self._state.state_type

    @property
    def metrics(self) -> CircuitMetrics:
        return self._metrics

    def add_listener(
        self, listener: Callable[[CircuitEvent, dict], None]
    ) -> None:
        self._listeners.append(listener)

    def _notify(self, event: CircuitEvent, data: dict) -> None:
        for listener in self._listeners:
            try:
                listener(event, data)
            except Exception:
                pass

    def _transition_to(self, new_state: State) -> None:
        old_state = self._state.state_type
        self._state = new_state
        self._metrics.record_state_change(new_state.state_type)
        self._notify(CircuitEvent.STATE_CHANGE, {
            "from": old_state,
            "to": new_state.state_type,
            "breaker": self.name,
        })

    def _is_counted_exception(self, exception: Exception) -> bool:
        if isinstance(exception, self._config.excluded_exceptions):
            return False
        return isinstance(exception, self._config.included_exceptions)

    def call(self, func: Callable, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        with self._lock:
            if not self._state.can_execute():
                self._metrics.record_rejected()
                self._notify(CircuitEvent.CALL_REJECTED, {
                    "breaker": self.name
                })
                opened_state = self._state
                if isinstance(opened_state, OpenState):
                    elapsed = time.monotonic() - opened_state._opened_at
                    retry_after = max(0, self._config.timeout - elapsed)
                else:
                    retry_after = self._config.timeout
                raise CircuitBreakerOpen(self.name, retry_after)

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            with self._lock:
                if self._is_counted_exception(e):
                    self._metrics.record_failure()
                    self._state.on_failure()
                    self._notify(CircuitEvent.CALL_FAILURE, {
                        "breaker": self.name,
                        "exception": e,
                    })
            raise
        else:
            with self._lock:
                self._metrics.record_success()
                self._state.on_success()
                self._notify(CircuitEvent.CALL_SUCCESS, {
                    "breaker": self.name,
                })
            return result

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._window.reset()
            self._metrics.reset()
            self._transition_to(ClosedState(self))


# ═══════════════════════════════════════════════════════════
# Decorator Interface
# ═══════════════════════════════════════════════════════════

def circuit_breaker(name: str,
                    config: Optional[CircuitBreakerConfig] = None,
                    fallback: Optional[Callable] = None):
    """
    Decorator that protects a function with a circuit breaker.

    Args:
        name: Unique name for this circuit breaker
        config: Configuration options
        fallback: Function to call when circuit is open
    """
    breaker = CircuitBreaker(name, config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerOpen:
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        wrapper._breaker = breaker  # Expose for testing/monitoring
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
# Integration with Retry Framework
# ═══════════════════════════════════════════════════════════

class CircuitBreakerRetryPolicy:
    """Combines circuit breaker with retry logic."""
    def __init__(self, breaker: CircuitBreaker, retry_policy: "RetryPolicy"):
        self.breaker = breaker
        self.retry_policy = retry_policy

    def execute(self, func: Callable, *args, **kwargs):
        executor = RetryExecutor(self.retry_policy)

        def protected_call():
            return self.breaker.call(func, *args, **kwargs)

        result = executor.execute(protected_call)
        if result.success:
            return result.result
        raise result.final_exception
```

### Usage Examples

```python
# Basic usage
config = CircuitBreakerConfig(
    failure_threshold=5,
    timeout=30.0,
    success_threshold=3,
)

@circuit_breaker("payment_service", config=config)
def process_payment(order_id: str, amount: float):
    return payment_api.charge(order_id, amount)

# With fallback
@circuit_breaker(
    "recommendation_service",
    fallback=lambda user_id: get_default_recommendations()
)
def get_recommendations(user_id: str):
    return recommendation_api.get(user_id)

# Manual usage with metrics
breaker = CircuitBreaker("database", CircuitBreakerConfig(
    failure_threshold=3,
    timeout=60.0,
))

breaker.add_listener(lambda event, data: print(f"CB Event: {event} {data}"))

try:
    result = breaker.call(database.query, "SELECT * FROM users")
except CircuitBreakerOpen as e:
    print(f"Service unavailable, retry after {e.retry_after}s")

# Check metrics
print(f"State: {breaker.state}")
print(f"Failure rate: {breaker.metrics.failure_rate:.2%}")
print(f"Total calls: {breaker.metrics.total_calls}")

# Combined with retry
combined = CircuitBreakerRetryPolicy(
    breaker=CircuitBreaker("api", CircuitBreakerConfig(failure_threshold=5)),
    retry_policy=RetryPolicy()
        .with_max_attempts(3)
        .with_backoff(ExponentialBackoffWithJitter())
        .with_retry_on(ConnectionError, TimeoutError)
)
result = combined.execute(api_client.get, "/users")
```

---

## 5. Task Scheduler Library

### Requirements Analysis

**Functional Requirements:**
- Schedule one-time delayed tasks
- Schedule periodic tasks (fixed rate and fixed delay)
- Support cron-like scheduling expressions
- Priority-based execution ordering
- Task cancellation and modification
- Thread pool for concurrent execution

**Non-Functional Requirements:**
- Efficient scheduling (min-heap for next execution time)
- Thread-safe task management
- Graceful shutdown with timeout
- Error isolation between tasks

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Scheduler                            │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │  Task Queue │   │   Triggers   │   │  Executor  │  │
│  │  (Min-Heap) │   │              │   │ (ThreadPool│  │
│  │             │   │ - Once       │   │  Workers)  │  │
│  │  sorted by  │   │ - Interval   │   │            │  │
│  │  next_run   │   │ - Cron       │   │            │  │
│  └──────┬──────┘   └──────┬───────┘   └──────┬─────┘  │
│         │                  │                  │         │
│         ▼                  ▼                  ▼         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Scheduler Loop Thread                │  │
│  │   while running:                                  │  │
│  │     1. Get next task from queue                   │  │
│  │     2. Wait until execution time                  │  │
│  │     3. Submit to thread pool                      │  │
│  │     4. Reschedule if periodic                     │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Strategy | Triggers determine when tasks run next |
| Command | Tasks encapsulate work to be done |
| Observer | Task lifecycle callbacks |
| Thread Pool | Concurrent task execution |
| Priority Queue | Efficient next-task selection |

### Complete Implementation

```python
import time
import heapq
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, Any
import uuid


# ═══════════════════════════════════════════════════════════
# Task States
# ═══════════════════════════════════════════════════════════

class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


# ═══════════════════════════════════════════════════════════
# Triggers (Strategy Pattern)
# ═══════════════════════════════════════════════════════════

class Trigger(ABC):
    @abstractmethod
    def next_fire_time(self, after: float) -> Optional[float]:
        """Return the next fire time after the given timestamp, or None if done."""
        pass


class OnceTrigger(Trigger):
    """Fires exactly once at a specific time."""
    def __init__(self, run_at: float):
        self.run_at = run_at
        self._fired = False

    def next_fire_time(self, after: float) -> Optional[float]:
        if self._fired:
            return None
        self._fired = True
        return self.run_at


class IntervalTrigger(Trigger):
    """Fires at fixed intervals (fixed rate scheduling)."""
    def __init__(self, interval: float, start_at: Optional[float] = None):
        self.interval = interval
        self.start_at = start_at or time.time()
        self._last_fire: Optional[float] = None

    def next_fire_time(self, after: float) -> Optional[float]:
        if self._last_fire is None:
            self._last_fire = self.start_at
            return self.start_at
        next_time = self._last_fire + self.interval
        self._last_fire = next_time
        return next_time


class FixedDelayTrigger(Trigger):
    """Fires with a fixed delay after previous execution completes."""
    def __init__(self, delay: float):
        self.delay = delay

    def next_fire_time(self, after: float) -> Optional[float]:
        return after + self.delay


class CronTrigger(Trigger):
    """
    Simplified cron-like trigger.
    Supports: minute, hour, day_of_month, month, day_of_week
    Uses '*' for any, specific numbers, or comma-separated lists.
    """
    def __init__(self, minute: str = "*", hour: str = "*",
                 day_of_month: str = "*", month: str = "*",
                 day_of_week: str = "*"):
        self.minute = self._parse_field(minute, 0, 59)
        self.hour = self._parse_field(hour, 0, 23)
        self.day_of_month = self._parse_field(day_of_month, 1, 31)
        self.month = self._parse_field(month, 1, 12)
        self.day_of_week = self._parse_field(day_of_week, 0, 6)

    def _parse_field(self, value: str, min_val: int, max_val: int) -> set[int]:
        if value == "*":
            return set(range(min_val, max_val + 1))
        if "/" in value:
            step = int(value.split("/")[1])
            return set(range(min_val, max_val + 1, step))
        return {int(v) for v in value.split(",")}

    def next_fire_time(self, after: float) -> Optional[float]:
        from datetime import datetime, timedelta
        dt = datetime.fromtimestamp(after) + timedelta(minutes=1)
        dt = dt.replace(second=0, microsecond=0)

        for _ in range(525600):  # Max one year of minutes
            if (dt.minute in self.minute and
                dt.hour in self.hour and
                dt.day in self.day_of_month and
                dt.month in self.month and
                dt.weekday() in self.day_of_week):
                return dt.timestamp()
            dt += timedelta(minutes=1)
        return None


# ═══════════════════════════════════════════════════════════
# Task
# ═══════════════════════════════════════════════════════════

@dataclass(order=True)
class ScheduledTask:
    """A task scheduled for execution."""
    next_run_time: float
    priority: int = field(compare=True)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()),
                         compare=False)
    name: str = field(default="", compare=False)
    func: Callable = field(default=None, compare=False)
    args: tuple = field(default=(), compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    trigger: Trigger = field(default=None, compare=False)
    state: TaskState = field(default=TaskState.PENDING, compare=False)
    max_retries: int = field(default=0, compare=False)
    retry_count: int = field(default=0, compare=False)
    error: Optional[Exception] = field(default=None, compare=False)
    result: Any = field(default=None, compare=False)


# ═══════════════════════════════════════════════════════════
# Task Scheduler
# ═══════════════════════════════════════════════════════════

class TaskScheduler:
    """
    Production-quality task scheduler with thread pool execution.
    """
    def __init__(self, max_workers: int = 4):
        self._queue: list[ScheduledTask] = []
        self._tasks: dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._listeners: list[Callable[[str, ScheduledTask], None]] = []

    def add_listener(self, listener: Callable[[str, ScheduledTask], None]):
        self._listeners.append(listener)

    def _notify_listeners(self, event: str, task: ScheduledTask):
        for listener in self._listeners:
            try:
                listener(event, task)
            except Exception:
                pass

    def schedule(self, func: Callable, trigger: Trigger,
                 name: str = "", priority: int = 0,
                 max_retries: int = 0,
                 args: tuple = (), kwargs: dict = None) -> str:
        """Schedule a task. Returns task_id."""
        kwargs = kwargs or {}
        next_time = trigger.next_fire_time(time.time())
        if next_time is None:
            raise ValueError("Trigger has no future fire time")

        task = ScheduledTask(
            next_run_time=next_time,
            priority=priority,
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            trigger=trigger,
            max_retries=max_retries,
        )

        with self._condition:
            heapq.heappush(self._queue, task)
            self._tasks[task.task_id] = task
            self._condition.notify()

        self._notify_listeners("scheduled", task)
        return task.task_id

    def schedule_once(self, func: Callable, delay: float,
                      priority: int = 0, **kwargs) -> str:
        """Schedule a one-time task after a delay."""
        trigger = OnceTrigger(time.time() + delay)
        return self.schedule(func, trigger, priority=priority, **kwargs)

    def schedule_interval(self, func: Callable, interval: float,
                          priority: int = 0, **kwargs) -> str:
        """Schedule a task at fixed intervals."""
        trigger = IntervalTrigger(interval)
        return self.schedule(func, trigger, priority=priority, **kwargs)

    def schedule_cron(self, func: Callable, minute: str = "*",
                      hour: str = "*", day_of_month: str = "*",
                      month: str = "*", day_of_week: str = "*",
                      **kwargs) -> str:
        """Schedule a task using cron-like expression."""
        trigger = CronTrigger(minute, hour, day_of_month, month, day_of_week)
        return self.schedule(func, trigger, **kwargs)

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].state = TaskState.CANCELLED
                self._notify_listeners("cancelled", self._tasks[task_id])
                return True
            return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self._tasks.get(task_id)

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="TaskScheduler"
        )
        self._scheduler_thread.start()

    def stop(self, wait: bool = True, timeout: float = 30.0) -> None:
        """Stop the scheduler."""
        self._running = False
        with self._condition:
            self._condition.notify_all()
        if wait and self._scheduler_thread:
            self._scheduler_thread.join(timeout=timeout)
        self._executor.shutdown(wait=wait)

    def _run_loop(self) -> None:
        while self._running:
            with self._condition:
                while self._running and not self._queue:
                    self._condition.wait(timeout=1.0)

                if not self._running:
                    break

                task = self._queue[0]
                now = time.time()

                if task.next_run_time > now:
                    wait_time = min(task.next_run_time - now, 1.0)
                    self._condition.wait(timeout=wait_time)
                    continue

                heapq.heappop(self._queue)

                if task.state == TaskState.CANCELLED:
                    continue

                task.state = TaskState.RUNNING
                self._executor.submit(self._execute_task, task)

    def _execute_task(self, task: ScheduledTask) -> None:
        self._notify_listeners("started", task)
        try:
            result = task.func(*task.args, **task.kwargs)
            task.result = result
            task.state = TaskState.COMPLETED
            self._notify_listeners("completed", task)
        except Exception as e:
            task.error = e
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.PENDING
                task.next_run_time = time.time() + (2 ** task.retry_count)
                with self._condition:
                    heapq.heappush(self._queue, task)
                    self._condition.notify()
                self._notify_listeners("retry", task)
                return
            task.state = TaskState.FAILED
            self._notify_listeners("failed", task)

        # Reschedule periodic tasks
        if task.state == TaskState.COMPLETED and task.trigger:
            next_time = task.trigger.next_fire_time(time.time())
            if next_time is not None:
                task.next_run_time = next_time
                task.state = TaskState.PENDING
                with self._condition:
                    heapq.heappush(self._queue, task)
                    self._condition.notify()
```

### Usage Examples

```python
scheduler = TaskScheduler(max_workers=8)
scheduler.start()

# One-time delayed task
task_id = scheduler.schedule_once(
    send_welcome_email,
    delay=300,  # 5 minutes
    args=(user_id,),
    name="welcome_email"
)

# Periodic task every 60 seconds
scheduler.schedule_interval(
    collect_metrics,
    interval=60.0,
    name="metrics_collector"
)

# Cron-like scheduling: every day at 2:30 AM
scheduler.schedule_cron(
    run_daily_report,
    minute="30",
    hour="2",
    name="daily_report"
)

# Priority task (lower number = higher priority)
scheduler.schedule_once(
    critical_cleanup,
    delay=0,
    priority=-10,
    name="critical_cleanup"
)

# Task with retry
scheduler.schedule_once(
    sync_data_to_warehouse,
    delay=0,
    max_retries=3,
    name="data_sync"
)

# Cancel a task
scheduler.cancel(task_id)

# Monitor tasks
scheduler.add_listener(
    lambda event, task: print(f"[{event}] {task.name} - {task.state}")
)

# Graceful shutdown
scheduler.stop(wait=True, timeout=60.0)
```

---

## 6. Configuration Framework

### Requirements Analysis

**Functional Requirements:**
- Load configuration from multiple sources (files, env vars, defaults)
- Type-safe access with automatic coercion
- Validation rules for configuration values
- Hierarchical configuration with overrides
- Hot reload when configuration files change
- Support JSON and `.env` file formats

**Non-Functional Requirements:**
- Thread-safe reads and updates
- Immutable config snapshots
- Clear error messages for invalid config
- Minimal external dependencies

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   ConfigStore                             │
│              (Thread-Safe Access)                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────── Sources (Priority Order) ────────┐ │
│  │                                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │ Defaults │  │  File    │  │   Env    │        │ │
│  │  │ (lowest) │  │ Source   │  │  Vars    │        │ │
│  │  │          │  │          │  │ (highest)│        │ │
│  │  └──────────┘  └──────────┘  └──────────┘        │ │
│  └─────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Validator / Type Coercion              │ │
│  └─────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                Merged Config View                   │ │
│  │          (Immutable, Typed Access)                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              File Watcher (Hot Reload)              │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Strategy | Config sources are interchangeable strategies |
| Chain of Responsibility | Sources checked in priority order |
| Observer | Listeners notified on config changes |
| Composite | Hierarchical config merging |
| Immutable Object | Config snapshots are read-only |

### Complete Implementation

```python
import os
import json
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Type, Union
from copy import deepcopy


# ═══════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════

class ConfigError(Exception):
    pass


class ConfigValidationError(ConfigError):
    def __init__(self, key: str, value: Any, message: str):
        self.key = key
        self.value = value
        super().__init__(f"Config validation failed for '{key}': {message}")


class ConfigKeyNotFound(ConfigError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Config key not found: '{key}'")


# ═══════════════════════════════════════════════════════════
# Type Coercion
# ═══════════════════════════════════════════════════════════

class TypeCoercer:
    """Converts string config values to typed Python objects."""

    _BOOL_TRUE = {"true", "1", "yes", "on", "enabled"}
    _BOOL_FALSE = {"false", "0", "no", "off", "disabled"}

    @classmethod
    def coerce(cls, value: Any, target_type: Type) -> Any:
        if value is None:
            return None
        if isinstance(value, target_type):
            return value
        if target_type == bool:
            return cls._to_bool(value)
        if target_type == int:
            return int(value)
        if target_type == float:
            return float(value)
        if target_type == str:
            return str(value)
        if target_type == list:
            if isinstance(value, str):
                return [v.strip() for v in value.split(",")]
            return list(value)
        return value

    @classmethod
    def _to_bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        s = str(value).lower().strip()
        if s in cls._BOOL_TRUE:
            return True
        if s in cls._BOOL_FALSE:
            return False
        raise ValueError(f"Cannot convert '{value}' to bool")


# ═══════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════

@dataclass
class ValidationRule:
    required: bool = False
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[list] = None
    pattern: Optional[str] = None
    custom: Optional[Callable[[Any], bool]] = None
    message: str = ""


class ConfigValidator:
    """Validates configuration values against rules."""

    def __init__(self):
        self._rules: dict[str, ValidationRule] = {}

    def add_rule(self, key: str, rule: ValidationRule) -> "ConfigValidator":
        self._rules[key] = rule
        return self

    def validate(self, config: dict[str, Any]) -> list[ConfigValidationError]:
        errors = []
        for key, rule in self._rules.items():
            value = self._get_nested(config, key)

            if value is None:
                if rule.required:
                    errors.append(ConfigValidationError(
                        key, None, "Required value is missing"
                    ))
                continue

            if rule.min_value is not None and value < rule.min_value:
                errors.append(ConfigValidationError(
                    key, value,
                    f"Value {value} is below minimum {rule.min_value}"
                ))

            if rule.max_value is not None and value > rule.max_value:
                errors.append(ConfigValidationError(
                    key, value,
                    f"Value {value} exceeds maximum {rule.max_value}"
                ))

            if rule.choices is not None and value not in rule.choices:
                errors.append(ConfigValidationError(
                    key, value,
                    f"Value must be one of {rule.choices}"
                ))

            if rule.pattern is not None:
                import re
                if not re.match(rule.pattern, str(value)):
                    errors.append(ConfigValidationError(
                        key, value,
                        f"Value does not match pattern '{rule.pattern}'"
                    ))

            if rule.custom is not None and not rule.custom(value):
                errors.append(ConfigValidationError(
                    key, value, rule.message or "Custom validation failed"
                ))

        return errors

    @staticmethod
    def _get_nested(config: dict, key: str) -> Any:
        parts = key.split(".")
        current = config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


# ═══════════════════════════════════════════════════════════
# Config Sources (Strategy Pattern)
# ═══════════════════════════════════════════════════════════

class ConfigSource(ABC):
    """Base class for configuration sources."""
    def __init__(self, priority: int = 0):
        self.priority = priority

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """Load and return configuration data."""
        pass

    @abstractmethod
    def has_changed(self) -> bool:
        """Check if source data has changed since last load."""
        pass


class DictSource(ConfigSource):
    """Configuration from a dictionary (defaults)."""
    def __init__(self, data: dict[str, Any], priority: int = 0):
        super().__init__(priority)
        self._data = deepcopy(data)

    def load(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def has_changed(self) -> bool:
        return False


class EnvironmentSource(ConfigSource):
    """Configuration from environment variables."""
    def __init__(self, prefix: str = "", priority: int = 100):
        super().__init__(priority)
        self.prefix = prefix.upper()
        self._last_snapshot: dict[str, str] = {}

    def load(self) -> dict[str, Any]:
        result = {}
        for key, value in os.environ.items():
            if self.prefix and not key.startswith(self.prefix):
                continue
            config_key = key[len(self.prefix):].lower().replace("__", ".")
            result[config_key] = value
        self._last_snapshot = dict(result)
        return result

    def has_changed(self) -> bool:
        current = {}
        for key, value in os.environ.items():
            if self.prefix and not key.startswith(self.prefix):
                continue
            config_key = key[len(self.prefix):].lower().replace("__", ".")
            current[config_key] = value
        return current != self._last_snapshot


class JSONFileSource(ConfigSource):
    """Configuration from a JSON file."""
    def __init__(self, path: str, priority: int = 50):
        super().__init__(priority)
        self.path = Path(path)
        self._last_mtime: float = 0

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        self._last_mtime = self.path.stat().st_mtime
        with open(self.path, "r") as f:
            return json.load(f)

    def has_changed(self) -> bool:
        if not self.path.exists():
            return self._last_mtime != 0
        return self.path.stat().st_mtime != self._last_mtime


class DotEnvSource(ConfigSource):
    """Configuration from a .env file."""
    def __init__(self, path: str = ".env", priority: int = 30):
        super().__init__(priority)
        self.path = Path(path)
        self._last_mtime: float = 0

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        self._last_mtime = self.path.stat().st_mtime
        result = {}
        with open(self.path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip().lower()
                    value = value.strip().strip("\"'")
                    result[key] = value
        return result

    def has_changed(self) -> bool:
        if not self.path.exists():
            return self._last_mtime != 0
        return self.path.stat().st_mtime != self._last_mtime


# ═══════════════════════════════════════════════════════════
# Config Store
# ═══════════════════════════════════════════════════════════

class ConfigStore:
    """
    Thread-safe configuration store with hot reload support.
    Merges multiple sources by priority (higher priority wins).
    """
    def __init__(self):
        self._sources: list[ConfigSource] = []
        self._config: dict[str, Any] = {}
        self._validator: Optional[ConfigValidator] = None
        self._lock = threading.RLock()
        self._watchers: list[Callable[[dict, dict], None]] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._watching = False

    def add_source(self, source: ConfigSource) -> "ConfigStore":
        self._sources.append(source)
        self._sources.sort(key=lambda s: s.priority)
        return self

    def set_validator(self, validator: ConfigValidator) -> "ConfigStore":
        self._validator = validator
        return self

    def on_change(self, callback: Callable[[dict, dict], None]) -> "ConfigStore":
        self._watchers.append(callback)
        return self

    def load(self) -> "ConfigStore":
        """Load/reload all configuration sources."""
        with self._lock:
            old_config = deepcopy(self._config)
            merged = {}
            for source in self._sources:
                data = source.load()
                self._deep_merge(merged, data)
            if self._validator:
                errors = self._validator.validate(merged)
                if errors:
                    raise ConfigError(
                        f"Validation errors: {[str(e) for e in errors]}"
                    )
            self._config = merged

            if old_config and old_config != merged:
                for watcher in self._watchers:
                    try:
                        watcher(old_config, merged)
                    except Exception:
                        pass
        return self

    def get(self, key: str, default: Any = None,
            type_: Optional[Type] = None) -> Any:
        """
        Get a config value by dot-notation key.
        Supports type coercion.
        """
        with self._lock:
            value = self._get_nested(self._config, key)
            if value is None:
                return default
            if type_ is not None:
                return TypeCoercer.coerce(value, type_)
            return value

    def get_required(self, key: str, type_: Optional[Type] = None) -> Any:
        """Get a required config value. Raises if not found."""
        value = self.get(key, type_=type_)
        if value is None:
            raise ConfigKeyNotFound(key)
        return value

    def get_section(self, prefix: str) -> dict[str, Any]:
        """Get all config values under a prefix as a dict."""
        with self._lock:
            section = self._get_nested(self._config, prefix)
            if isinstance(section, dict):
                return deepcopy(section)
            return {}

    def as_dict(self) -> dict[str, Any]:
        """Return a complete copy of the config."""
        with self._lock:
            return deepcopy(self._config)

    def start_watching(self, interval: float = 5.0) -> None:
        """Start watching for config changes (hot reload)."""
        if self._watching:
            return
        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval,),
            daemon=True,
            name="ConfigWatcher",
        )
        self._watch_thread.start()

    def stop_watching(self) -> None:
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=10)

    def _watch_loop(self, interval: float) -> None:
        while self._watching:
            time.sleep(interval)
            if any(source.has_changed() for source in self._sources):
                try:
                    self.load()
                except ConfigError:
                    pass

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        for key, value in override.items():
            if (key in base and isinstance(base[key], dict)
                    and isinstance(value, dict)):
                ConfigStore._deep_merge(base[key], value)
            else:
                base[key] = deepcopy(value)
        return base

    @staticmethod
    def _get_nested(config: dict, key: str) -> Any:
        parts = key.split(".")
        current = config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
```

### Usage Examples

```python
# Define defaults
defaults = DictSource({
    "app": {
        "name": "MyService",
        "debug": False,
        "port": 8080,
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "pool_size": 10,
    },
    "cache": {
        "ttl": 300,
        "max_size": 1000,
    },
}, priority=0)

# Create and configure store
config = (
    ConfigStore()
    .add_source(defaults)
    .add_source(JSONFileSource("config.json", priority=50))
    .add_source(DotEnvSource(".env", priority=30))
    .add_source(EnvironmentSource(prefix="MYAPP_", priority=100))
    .set_validator(
        ConfigValidator()
        .add_rule("app.port", ValidationRule(
            required=True, min_value=1, max_value=65535
        ))
        .add_rule("database.pool_size", ValidationRule(
            min_value=1, max_value=100
        ))
    )
    .load()
)

# Type-safe access
port = config.get("app.port", type_=int)
debug = config.get("app.debug", type_=bool)
db_host = config.get("database.host", type_=str)

# Section access
db_config = config.get_section("database")
# {'host': 'localhost', 'port': 5432, 'pool_size': 10}

# Hot reload with change notification
config.on_change(lambda old, new: print("Config updated!"))
config.start_watching(interval=5.0)

# Environment variable override:
# MYAPP_DATABASE__HOST=prod-db.example.com overrides database.host
```

---

## 7. Caching Library

### Requirements Analysis

**Functional Requirements:**
- Store and retrieve key-value pairs with configurable eviction
- Support multiple eviction policies (LRU, LFU, FIFO, TTL)
- Provide cache statistics (hits, misses, evictions)
- Thread-safe for concurrent access
- Decorator interface for transparent memoization
- Write-through and write-behind strategies

**Non-Functional Requirements:**
- O(1) operations for LRU/FIFO
- Minimal memory overhead per entry
- No external dependencies
- Extensible for custom eviction policies

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Cache API                             │
│        get() | put() | delete() | @cached decorator          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────── Eviction Policies ──────────────────┐      │
│  │                                                   │      │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐           │      │
│  │  │ LRU │  │ LFU │  │FIFO │  │ TTL │           │      │
│  │  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘           │      │
│  │     │        │        │        │                │      │
│  │     └────────┴────────┴────────┘                │      │
│  │                    │                             │      │
│  └────────────────────┼─────────────────────────────┘      │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────┐      │
│  │              Storage (dict + metadata)            │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Write Strategies                        │      │
│  │    Write-Through  |  Write-Behind (Async)        │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │              Statistics Collector                  │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Strategy | Eviction policies are interchangeable strategies |
| Decorator | `@cached` transparently memoizes functions |
| Proxy | Write-through/behind proxies to backing store |
| Observer | Stats collection observes cache operations |
| Template Method | Base cache defines flow, policies fill in details |

### Complete Implementation

```python
import time
import threading
import heapq
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, Hashable


# ═══════════════════════════════════════════════════════════
# Cache Entry
# ═══════════════════════════════════════════════════════════

@dataclass
class CacheEntry:
    key: Hashable
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1


# ═══════════════════════════════════════════════════════════
# Cache Statistics
# ═══════════════════════════════════════════════════════════

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate

    def __repr__(self) -> str:
        return (
            f"CacheStats(hits={self.hits}, misses={self.misses}, "
            f"hit_rate={self.hit_rate:.2%}, evictions={self.evictions}, "
            f"size={self.size}/{self.max_size})"
        )


# ═══════════════════════════════════════════════════════════
# Eviction Policies (Strategy Pattern)
# ═══════════════════════════════════════════════════════════

class EvictionPolicy(ABC):
    @abstractmethod
    def on_access(self, key: Hashable) -> None:
        pass

    @abstractmethod
    def on_insert(self, key: Hashable) -> None:
        pass

    @abstractmethod
    def on_remove(self, key: Hashable) -> None:
        pass

    @abstractmethod
    def evict(self) -> Optional[Hashable]:
        """Return the key to evict, or None if empty."""
        pass


class LRUPolicy(EvictionPolicy):
    """Least Recently Used: evicts the entry not accessed for the longest."""
    def __init__(self):
        self._order = OrderedDict()

    def on_access(self, key: Hashable) -> None:
        if key in self._order:
            self._order.move_to_end(key)

    def on_insert(self, key: Hashable) -> None:
        self._order[key] = True

    def on_remove(self, key: Hashable) -> None:
        self._order.pop(key, None)

    def evict(self) -> Optional[Hashable]:
        if self._order:
            key, _ = self._order.popitem(last=False)
            return key
        return None


class LFUPolicy(EvictionPolicy):
    """Least Frequently Used: evicts the entry with fewest accesses."""
    def __init__(self):
        self._freq: dict[Hashable, int] = {}
        self._min_freq = 0
        self._freq_to_keys: dict[int, OrderedDict] = defaultdict(OrderedDict)

    def on_access(self, key: Hashable) -> None:
        if key not in self._freq:
            return
        freq = self._freq[key]
        self._freq_to_keys[freq].pop(key, None)
        if not self._freq_to_keys[freq] and freq == self._min_freq:
            self._min_freq += 1
        self._freq[key] = freq + 1
        self._freq_to_keys[freq + 1][key] = True

    def on_insert(self, key: Hashable) -> None:
        self._freq[key] = 1
        self._freq_to_keys[1][key] = True
        self._min_freq = 1

    def on_remove(self, key: Hashable) -> None:
        if key in self._freq:
            freq = self._freq.pop(key)
            self._freq_to_keys[freq].pop(key, None)

    def evict(self) -> Optional[Hashable]:
        if not self._freq_to_keys[self._min_freq]:
            return None
        key, _ = self._freq_to_keys[self._min_freq].popitem(last=False)
        del self._freq[key]
        return key


class FIFOPolicy(EvictionPolicy):
    """First In First Out: evicts the oldest entry."""
    def __init__(self):
        self._order = OrderedDict()

    def on_access(self, key: Hashable) -> None:
        pass  # Access order doesn't matter for FIFO

    def on_insert(self, key: Hashable) -> None:
        self._order[key] = True

    def on_remove(self, key: Hashable) -> None:
        self._order.pop(key, None)

    def evict(self) -> Optional[Hashable]:
        if self._order:
            key, _ = self._order.popitem(last=False)
            return key
        return None


class TTLPolicy(EvictionPolicy):
    """
    TTL-based eviction: removes expired entries.
    Uses a min-heap sorted by expiry time.
    """
    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._expiry_heap: list[tuple[float, Hashable]] = []
        self._entries: dict[Hashable, float] = {}

    def on_access(self, key: Hashable) -> None:
        pass

    def on_insert(self, key: Hashable) -> None:
        expiry = time.time() + self.default_ttl
        self._entries[key] = expiry
        heapq.heappush(self._expiry_heap, (expiry, key))

    def on_remove(self, key: Hashable) -> None:
        self._entries.pop(key, None)

    def evict(self) -> Optional[Hashable]:
        now = time.time()
        while self._expiry_heap:
            expiry, key = self._expiry_heap[0]
            if key not in self._entries:
                heapq.heappop(self._expiry_heap)
                continue
            if self._entries[key] != expiry:
                heapq.heappop(self._expiry_heap)
                continue
            if expiry <= now:
                heapq.heappop(self._expiry_heap)
                del self._entries[key]
                return key
            break
        # If nothing expired, evict oldest
        if self._expiry_heap:
            _, key = heapq.heappop(self._expiry_heap)
            self._entries.pop(key, None)
            return key
        return None


# ═══════════════════════════════════════════════════════════
# Write Strategies
# ═══════════════════════════════════════════════════════════

class WriteStrategy(ABC):
    @abstractmethod
    def write(self, key: Hashable, value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: Hashable) -> None:
        pass


class NoOpWriteStrategy(WriteStrategy):
    """Cache-only, no persistence."""
    def write(self, key: Hashable, value: Any) -> None:
        pass

    def delete(self, key: Hashable) -> None:
        pass


class WriteThroughStrategy(WriteStrategy):
    """Writes to backing store synchronously on every cache write."""
    def __init__(self, store_write: Callable, store_delete: Callable):
        self._write = store_write
        self._delete = store_delete

    def write(self, key: Hashable, value: Any) -> None:
        self._write(key, value)

    def delete(self, key: Hashable) -> None:
        self._delete(key)


class WriteBehindStrategy(WriteStrategy):
    """Buffers writes and flushes to backing store asynchronously."""
    def __init__(self, store_write: Callable, store_delete: Callable,
                 flush_interval: float = 5.0):
        self._write_fn = store_write
        self._delete_fn = store_delete
        self._buffer: dict[Hashable, tuple[str, Any]] = {}
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(
            target=self._flush_loop,
            args=(flush_interval,),
            daemon=True,
        )
        self._thread.start()

    def write(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._buffer[key] = ("write", value)

    def delete(self, key: Hashable) -> None:
        with self._lock:
            self._buffer[key] = ("delete", None)

    def _flush_loop(self, interval: float) -> None:
        while self._running:
            time.sleep(interval)
            self._flush()

    def _flush(self) -> None:
        with self._lock:
            buffer = dict(self._buffer)
            self._buffer.clear()
        for key, (op, value) in buffer.items():
            try:
                if op == "write":
                    self._write_fn(key, value)
                elif op == "delete":
                    self._delete_fn(key)
            except Exception:
                pass

    def stop(self) -> None:
        self._running = False
        self._flush()


# ═══════════════════════════════════════════════════════════
# Cache Implementation
# ═══════════════════════════════════════════════════════════

class Cache:
    """
    Thread-safe cache with configurable eviction policy.
    """
    def __init__(self, max_size: int = 1000,
                 eviction_policy: Optional[EvictionPolicy] = None,
                 write_strategy: Optional[WriteStrategy] = None,
                 default_ttl: Optional[float] = None):
        self.max_size = max_size
        self._policy = eviction_policy or LRUPolicy()
        self._write_strategy = write_strategy or NoOpWriteStrategy()
        self._default_ttl = default_ttl
        self._store: dict[Hashable, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)

    @property
    def stats(self) -> CacheStats:
        return self._stats

    def get(self, key: Hashable) -> Optional[Any]:
        """Get a value from the cache. Returns None on miss."""
        with self._lock:
            if key not in self._store:
                self._stats.misses += 1
                return None
            entry = self._store[key]
            if entry.is_expired:
                self._remove(key)
                self._stats.misses += 1
                return None
            entry.touch()
            self._policy.on_access(key)
            self._stats.hits += 1
            return entry.value

    def put(self, key: Hashable, value: Any,
            ttl: Optional[float] = None) -> None:
        """Put a value into the cache."""
        with self._lock:
            if key in self._store:
                self._store[key].value = value
                self._store[key].last_accessed = time.time()
                self._policy.on_access(key)
            else:
                if len(self._store) >= self.max_size:
                    self._evict()
                entry = CacheEntry(
                    key=key,
                    value=value,
                    ttl=ttl or self._default_ttl,
                )
                self._store[key] = entry
                self._policy.on_insert(key)
                self._stats.size = len(self._store)
            self._write_strategy.write(key, value)

    def delete(self, key: Hashable) -> bool:
        """Remove a key from the cache."""
        with self._lock:
            if key in self._store:
                self._remove(key)
                self._write_strategy.delete(key)
                return True
            return False

    def contains(self, key: Hashable) -> bool:
        with self._lock:
            if key not in self._store:
                return False
            if self._store[key].is_expired:
                self._remove(key)
                return False
            return True

    def clear(self) -> None:
        with self._lock:
            for key in list(self._store.keys()):
                self._policy.on_remove(key)
            self._store.clear()
            self._stats.size = 0

    def size(self) -> int:
        return len(self._store)

    def _evict(self) -> None:
        key = self._policy.evict()
        if key is not None and key in self._store:
            del self._store[key]
            self._stats.evictions += 1
            self._stats.size = len(self._store)

    def _remove(self, key: Hashable) -> None:
        if key in self._store:
            del self._store[key]
            self._policy.on_remove(key)
            self._stats.size = len(self._store)


# ═══════════════════════════════════════════════════════════
# Decorator Interface
# ═══════════════════════════════════════════════════════════

def cached(cache: Cache,
           key_func: Optional[Callable] = None,
           ttl: Optional[float] = None):
    """
    Decorator that caches function results.

    Args:
        cache: Cache instance to use
        key_func: Custom function to generate cache keys
        ttl: Optional TTL override for cached entries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = (func.__name__, args, tuple(sorted(kwargs.items())))

            result = cache.get(key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.put(key, result, ttl=ttl)
            return result

        wrapper.cache = cache
        wrapper.invalidate = lambda *a, **kw: cache.delete(
            key_func(*a, **kw) if key_func
            else (func.__name__, a, tuple(sorted(kw.items())))
        )
        return wrapper
    return decorator
```

### Usage Examples

```python
# LRU Cache
lru_cache = Cache(max_size=1000, eviction_policy=LRUPolicy())
lru_cache.put("user:123", {"name": "Alice", "email": "alice@example.com"})
user = lru_cache.get("user:123")

# LFU Cache with TTL
lfu_cache = Cache(
    max_size=500,
    eviction_policy=LFUPolicy(),
    default_ttl=300.0,  # 5 minutes
)

# Decorator for memoization
app_cache = Cache(max_size=10000, eviction_policy=LRUPolicy())

@cached(app_cache, ttl=60.0)
def get_user_profile(user_id: str) -> dict:
    return database.query(f"SELECT * FROM users WHERE id = %s", user_id)

profile = get_user_profile("user_123")  # DB call
profile = get_user_profile("user_123")  # Cache hit

# Invalidate specific entry
get_user_profile.invalidate("user_123")

# Write-through cache
def db_write(key, value):
    database.upsert("cache_table", key=key, value=json.dumps(value))

def db_delete(key):
    database.delete("cache_table", key=key)

persistent_cache = Cache(
    max_size=5000,
    eviction_policy=LRUPolicy(),
    write_strategy=WriteThroughStrategy(db_write, db_delete),
)

# Cache statistics
print(app_cache.stats)
# CacheStats(hits=1, misses=1, hit_rate=50.00%, evictions=0, size=1/10000)
```

### Unit Test Example

```python
import unittest


class TestLRUCache(unittest.TestCase):
    def test_basic_put_get(self):
        cache = Cache(max_size=3, eviction_policy=LRUPolicy())
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("b"), 2)

    def test_eviction(self):
        cache = Cache(max_size=2, eviction_policy=LRUPolicy())
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # Should evict "a"
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)

    def test_access_updates_lru(self):
        cache = Cache(max_size=2, eviction_policy=LRUPolicy())
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")  # Access "a", making "b" the LRU
        cache.put("c", 3)  # Should evict "b"
        self.assertEqual(cache.get("a"), 1)
        self.assertIsNone(cache.get("b"))

    def test_ttl_expiration(self):
        cache = Cache(max_size=10, eviction_policy=LRUPolicy())
        cache.put("key", "value", ttl=0.01)
        time.sleep(0.02)
        self.assertIsNone(cache.get("key"))

    def test_stats(self):
        cache = Cache(max_size=10, eviction_policy=LRUPolicy())
        cache.put("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss
        self.assertEqual(cache.stats.hits, 1)
        self.assertEqual(cache.stats.misses, 1)
        self.assertAlmostEqual(cache.stats.hit_rate, 0.5)
```

---

## 8. Event Bus Framework

### Requirements Analysis

**Functional Requirements:**
- Publish events to topics
- Subscribe handlers to specific topics
- Support wildcard/pattern subscriptions
- Priority-based subscriber ordering
- Async event handling
- Dead letter queue for failed events
- Weak references to prevent memory leaks

**Non-Functional Requirements:**
- Thread-safe event dispatching
- Decoupled publishers and subscribers
- Minimal latency for synchronous dispatch
- Graceful handling of subscriber failures

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Event Bus                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Publishers ──▶ ┌──────────────────────────────┐            │
│                 │      Topic Router            │            │
│                 │                              │            │
│                 │  "user.created" ──┐          │            │
│                 │  "user.*"     ────┤          │            │
│                 │  "order.paid" ────┤          │            │
│                 │  "*"          ────┘          │            │
│                 └──────────┬───────────────────┘            │
│                            │                                 │
│                            ▼                                 │
│                 ┌──────────────────────────────┐            │
│                 │  Subscriber Priority Queue   │            │
│                 │  [p=0] Handler A             │            │
│                 │  [p=1] Handler B             │            │
│                 │  [p=2] Handler C             │            │
│                 └──────────┬───────────────────┘            │
│                            │                                 │
│              ┌─────────────┼──────────────┐                 │
│              ▼             ▼              ▼                  │
│        ┌──────────┐ ┌──────────┐  ┌──────────────┐        │
│        │   Sync   │ │  Async   │  │  Dead Letter │        │
│        │ Dispatch │ │ Dispatch │  │    Queue     │        │
│        └──────────┘ └──────────┘  └──────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Application |
|---------|-------------|
| Observer/Pub-Sub | Core event dispatching mechanism |
| Mediator | Event bus mediates between publishers and subscribers |
| Strategy | Dispatch strategies (sync/async) |
| Chain of Responsibility | Middleware/filter chain |
| Command | Events encapsulate data to be processed |

### Complete Implementation

```python
import time
import weakref
import threading
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from queue import Queue
import uuid


# ═══════════════════════════════════════════════════════════
# Events
# ═══════════════════════════════════════════════════════════

@dataclass
class Event:
    """Base event class."""
    topic: str
    data: Any = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    _propagation_stopped: bool = field(default=False, init=False)

    def stop_propagation(self) -> None:
        """Stop this event from being delivered to remaining subscribers."""
        self._propagation_stopped = True

    @property
    def is_propagation_stopped(self) -> bool:
        return self._propagation_stopped


# ═══════════════════════════════════════════════════════════
# Subscriber
# ═══════════════════════════════════════════════════════════

@dataclass
class Subscription:
    """Represents a subscription to an event topic."""
    subscriber_id: str
    topic_pattern: str
    handler: Callable[[Event], None]
    priority: int = 0
    is_async: bool = False
    use_weak_ref: bool = False
    _regex: Optional[re.Pattern] = field(default=None, init=False)

    def __post_init__(self):
        pattern = self.topic_pattern.replace(".", r"\.")
        pattern = pattern.replace("*", r"[^.]*")
        pattern = pattern.replace("#", r".*")
        self._regex = re.compile(f"^{pattern}$")

    def matches(self, topic: str) -> bool:
        return self._regex.match(topic) is not None


# ═══════════════════════════════════════════════════════════
# Dead Letter Queue
# ═══════════════════════════════════════════════════════════

@dataclass
class DeadLetter:
    """A failed event delivery."""
    event: Event
    subscriber_id: str
    exception: Exception
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0


class DeadLetterQueue:
    """Stores events that failed delivery for later processing."""
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: Queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
        self._total_count = 0

    def put(self, dead_letter: DeadLetter) -> None:
        with self._lock:
            if self._queue.full():
                self._queue.get()  # Drop oldest
            self._queue.put(dead_letter)
            self._total_count += 1

    def get(self) -> Optional[DeadLetter]:
        try:
            return self._queue.get_nowait()
        except Exception:
            return None

    def drain(self, max_items: int = 100) -> list[DeadLetter]:
        items = []
        for _ in range(max_items):
            item = self.get()
            if item is None:
                break
            items.append(item)
        return items

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def total_failed(self) -> int:
        return self._total_count


# ═══════════════════════════════════════════════════════════
# Event Bus Middleware
# ═══════════════════════════════════════════════════════════

class Middleware(ABC):
    """Middleware that can intercept event publishing."""
    @abstractmethod
    def process(self, event: Event, next_fn: Callable) -> None:
        pass


class LoggingMiddleware(Middleware):
    """Logs all published events."""
    def __init__(self, logger=None):
        self.logger = logger

    def process(self, event: Event, next_fn: Callable) -> None:
        msg = f"Event published: {event.topic} (id={event.event_id})"
        if self.logger:
            self.logger.debug(msg)
        next_fn(event)


class FilterMiddleware(Middleware):
    """Filters events based on a predicate."""
    def __init__(self, predicate: Callable[[Event], bool]):
        self._predicate = predicate

    def process(self, event: Event, next_fn: Callable) -> None:
        if self._predicate(event):
            next_fn(event)


# ═══════════════════════════════════════════════════════════
# Event Bus
# ═══════════════════════════════════════════════════════════

class EventBus:
    """
    Production-quality event bus with pub/sub, topic routing,
    priority subscribers, async dispatch, and dead letter queue.
    """
    def __init__(self, max_workers: int = 4):
        self._subscriptions: list[Subscription] = []
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._dead_letter_queue = DeadLetterQueue()
        self._middlewares: list[Middleware] = []
        self._event_history: list[Event] = []
        self._history_size = 1000
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    @property
    def dead_letters(self) -> DeadLetterQueue:
        return self._dead_letter_queue

    def use(self, middleware: Middleware) -> "EventBus":
        """Add middleware to the event processing pipeline."""
        self._middlewares.append(middleware)
        return self

    def subscribe(self, topic_pattern: str,
                  handler: Callable[[Event], None],
                  priority: int = 0,
                  is_async: bool = False,
                  use_weak_ref: bool = False) -> str:
        """
        Subscribe to events matching a topic pattern.

        Patterns:
            "user.created" - exact match
            "user.*"       - matches user.created, user.deleted, etc.
            "user.#"       - matches user.created, user.profile.updated, etc.
            "*"            - matches all single-level topics

        Args:
            topic_pattern: Topic pattern to match
            handler: Function to call with the event
            priority: Lower number = higher priority (called first)
            is_async: If True, handler is called in thread pool
            use_weak_ref: If True, uses weak reference to handler

        Returns:
            Subscription ID for unsubscribing
        """
        sub_id = str(uuid.uuid4())

        if use_weak_ref and hasattr(handler, "__self__"):
            weak_handler = weakref.WeakMethod(handler)
        elif use_weak_ref:
            weak_handler = weakref.ref(handler)
        else:
            weak_handler = None

        subscription = Subscription(
            subscriber_id=sub_id,
            topic_pattern=topic_pattern,
            handler=weak_handler or handler,
            priority=priority,
            is_async=is_async,
            use_weak_ref=use_weak_ref,
        )

        with self._lock:
            self._subscriptions.append(subscription)
            self._subscriptions.sort(key=lambda s: s.priority)

        return sub_id

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Remove a subscription by ID."""
        with self._lock:
            before = len(self._subscriptions)
            self._subscriptions = [
                s for s in self._subscriptions
                if s.subscriber_id != subscriber_id
            ]
            return len(self._subscriptions) < before

    def publish(self, topic: str, data: Any = None,
                metadata: Optional[dict] = None) -> Event:
        """
        Publish an event to all matching subscribers.

        Args:
            topic: The event topic
            data: Event payload
            metadata: Optional metadata dict

        Returns:
            The published Event object
        """
        event = Event(
            topic=topic,
            data=data,
            metadata=metadata or {},
        )

        if self._middlewares:
            self._apply_middleware(event, 0)
        else:
            self._dispatch(event)

        self._record_event(event)
        return event

    def publish_event(self, event: Event) -> Event:
        """Publish a pre-constructed event."""
        if self._middlewares:
            self._apply_middleware(event, 0)
        else:
            self._dispatch(event)
        self._record_event(event)
        return event

    def _apply_middleware(self, event: Event, index: int) -> None:
        if index >= len(self._middlewares):
            self._dispatch(event)
            return
        middleware = self._middlewares[index]
        middleware.process(
            event,
            lambda e: self._apply_middleware(e, index + 1)
        )

    def _dispatch(self, event: Event) -> None:
        with self._lock:
            matching = [
                s for s in self._subscriptions
                if s.matches(event.topic)
            ]

        for subscription in matching:
            if event.is_propagation_stopped:
                break

            handler = self._resolve_handler(subscription)
            if handler is None:
                self._cleanup_dead_subscription(subscription)
                continue

            if subscription.is_async:
                self._executor.submit(
                    self._safe_invoke, handler, event, subscription
                )
            else:
                self._safe_invoke(handler, event, subscription)

    def _resolve_handler(self, subscription: Subscription) -> Optional[Callable]:
        if not subscription.use_weak_ref:
            return subscription.handler
        ref = subscription.handler
        handler = ref()
        return handler

    def _cleanup_dead_subscription(self, subscription: Subscription) -> None:
        with self._lock:
            self._subscriptions = [
                s for s in self._subscriptions
                if s.subscriber_id != subscription.subscriber_id
            ]

    def _safe_invoke(self, handler: Callable, event: Event,
                     subscription: Subscription) -> None:
        try:
            handler(event)
        except Exception as e:
            dead_letter = DeadLetter(
                event=event,
                subscriber_id=subscription.subscriber_id,
                exception=e,
            )
            self._dead_letter_queue.put(dead_letter)

    def _record_event(self, event: Event) -> None:
        self._event_history.append(event)
        if len(self._event_history) > self._history_size:
            self._event_history = self._event_history[-self._history_size:]

    def get_history(self, topic_filter: Optional[str] = None,
                    limit: int = 100) -> list[Event]:
        """Get recent event history, optionally filtered by topic."""
        events = self._event_history
        if topic_filter:
            pattern = topic_filter.replace(".", r"\.").replace("*", r"[^.]*")
            regex = re.compile(f"^{pattern}$")
            events = [e for e in events if regex.match(e.topic)]
        return events[-limit:]

    def subscriber_count(self, topic: Optional[str] = None) -> int:
        """Get the number of active subscribers."""
        if topic is None:
            return len(self._subscriptions)
        return sum(
            1 for s in self._subscriptions if s.matches(topic)
        )

    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._subscriptions.clear()

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the event bus executor."""
        self._executor.shutdown(wait=wait)


# ═══════════════════════════════════════════════════════════
# Typed Event Helpers
# ═══════════════════════════════════════════════════════════

class TypedEvent(Event):
    """Base class for strongly-typed events."""
    @classmethod
    def topic_name(cls) -> str:
        name = cls.__name__
        parts = []
        for char in name:
            if char.isupper() and parts:
                parts.append(".")
            parts.append(char.lower())
        return "".join(parts)


class TypedEventBus:
    """Wrapper that adds type-safe publish/subscribe."""
    def __init__(self, bus: Optional[EventBus] = None):
        self._bus = bus or EventBus()
        self._type_map: dict[type, str] = {}

    def subscribe_type(self, event_type: type,
                       handler: Callable[[Event], None],
                       **kwargs) -> str:
        topic = self._get_topic(event_type)
        return self._bus.subscribe(topic, handler, **kwargs)

    def publish_typed(self, event: TypedEvent) -> Event:
        if not event.topic:
            event.topic = self._get_topic(type(event))
        return self._bus.publish_event(event)

    def _get_topic(self, event_type: type) -> str:
        if event_type not in self._type_map:
            if hasattr(event_type, "topic_name"):
                self._type_map[event_type] = event_type.topic_name()
            else:
                self._type_map[event_type] = event_type.__name__.lower()
        return self._type_map[event_type]
```

### Usage Examples

```python
# Create event bus
bus = EventBus(max_workers=8)

# Simple subscribe/publish
def on_user_created(event: Event):
    user = event.data
    print(f"Welcome {user['name']}!")
    send_welcome_email(user["email"])

bus.subscribe("user.created", on_user_created)
bus.publish("user.created", {"name": "Alice", "email": "alice@example.com"})

# Wildcard subscriptions
def audit_log(event: Event):
    log_to_audit_db(event.topic, event.data, event.timestamp)

bus.subscribe("user.*", audit_log)  # All user events
bus.subscribe("#", audit_log)       # ALL events

# Priority subscribers (lower number = higher priority)
bus.subscribe("order.placed", validate_order, priority=0)
bus.subscribe("order.placed", charge_payment, priority=1)
bus.subscribe("order.placed", send_confirmation, priority=2)

# Async subscribers for non-blocking operations
bus.subscribe(
    "user.created",
    lambda e: sync_to_analytics(e.data),
    is_async=True,
)

# Weak references (auto-cleanup when subscriber is garbage collected)
class OrderService:
    def __init__(self, bus: EventBus):
        bus.subscribe("order.*", self.handle_order, use_weak_ref=True)

    def handle_order(self, event: Event):
        print(f"Processing order event: {event.topic}")

# Stop propagation
def security_check(event: Event):
    if not is_authorized(event.metadata.get("user_id")):
        event.stop_propagation()
        raise PermissionError("Unauthorized")

bus.subscribe("admin.*", security_check, priority=-100)

# Dead letter queue processing
def process_dead_letters():
    letters = bus.dead_letters.drain(max_items=50)
    for letter in letters:
        print(f"Failed: {letter.event.topic} -> {letter.exception}")
        if letter.retry_count < 3:
            letter.retry_count += 1
            bus.publish_event(letter.event)

# Middleware
bus.use(LoggingMiddleware())
bus.use(FilterMiddleware(lambda e: not e.topic.startswith("internal.")))

# Typed events
class UserCreatedEvent(TypedEvent):
    pass

class OrderPlacedEvent(TypedEvent):
    pass

typed_bus = TypedEventBus(bus)
typed_bus.subscribe_type(UserCreatedEvent, on_user_created)
typed_bus.publish_typed(UserCreatedEvent(
    topic="user.created.event",
    data={"user_id": "123"}
))

# Graceful shutdown
bus.shutdown(wait=True)
```

### Unit Test Example

```python
import unittest


class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.received = []

    def test_basic_pub_sub(self):
        self.bus.subscribe("test", lambda e: self.received.append(e.data))
        self.bus.publish("test", "hello")
        self.assertEqual(self.received, ["hello"])

    def test_wildcard_subscription(self):
        self.bus.subscribe("user.*", lambda e: self.received.append(e.topic))
        self.bus.publish("user.created", None)
        self.bus.publish("user.deleted", None)
        self.bus.publish("order.placed", None)
        self.assertEqual(self.received, ["user.created", "user.deleted"])

    def test_priority_ordering(self):
        self.bus.subscribe("test", lambda e: self.received.append("B"), priority=1)
        self.bus.subscribe("test", lambda e: self.received.append("A"), priority=0)
        self.bus.subscribe("test", lambda e: self.received.append("C"), priority=2)
        self.bus.publish("test", None)
        self.assertEqual(self.received, ["A", "B", "C"])

    def test_stop_propagation(self):
        def stopper(event: Event):
            self.received.append("stopper")
            event.stop_propagation()

        self.bus.subscribe("test", stopper, priority=0)
        self.bus.subscribe("test", lambda e: self.received.append("after"), priority=1)
        self.bus.publish("test", None)
        self.assertEqual(self.received, ["stopper"])

    def test_dead_letter_queue(self):
        def failing_handler(event: Event):
            raise ValueError("Handler failed")

        self.bus.subscribe("test", failing_handler)
        self.bus.publish("test", "data")
        self.assertEqual(self.bus.dead_letters.size, 1)

    def test_unsubscribe(self):
        sub_id = self.bus.subscribe("test", lambda e: self.received.append(1))
        self.bus.publish("test", None)
        self.bus.unsubscribe(sub_id)
        self.bus.publish("test", None)
        self.assertEqual(self.received, [1])
```

---

## Cross-Cutting Concerns

### Thread Safety Patterns Used Across All Libraries

```python
# Pattern 1: Simple Lock
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

# Pattern 2: Read-Write Lock (for read-heavy workloads)
class ReadWriteLock:
    def __init__(self):
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
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

# Pattern 3: Condition Variable (for coordination)
class BoundedBuffer:
    def __init__(self, capacity: int):
        self._buffer = []
        self._capacity = capacity
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def put(self, item):
        with self._not_full:
            while len(self._buffer) >= self._capacity:
                self._not_full.wait()
            self._buffer.append(item)
            self._not_empty.notify()

    def get(self):
        with self._not_empty:
            while not self._buffer:
                self._not_empty.wait()
            item = self._buffer.pop(0)
            self._not_full.notify()
            return item
```

### Extension Points

Each library is designed with clear extension points:

| Library | Extension Point | How to Extend |
|---------|----------------|---------------|
| Logging | Custom Handler | Subclass `Handler`, implement `emit()` |
| Rate Limiter | New Algorithm | Subclass `RateLimiter`, implement `allow()` |
| Retry | Backoff Strategy | Subclass `BackoffStrategy`, implement `get_delay()` |
| Circuit Breaker | Metrics Backend | Replace `SlidingWindowMetrics` |
| Scheduler | Custom Trigger | Subclass `Trigger`, implement `next_fire_time()` |
| Config | New Source | Subclass `ConfigSource`, implement `load()` |
| Cache | Eviction Policy | Subclass `EvictionPolicy`, implement all methods |
| Event Bus | Middleware | Subclass `Middleware`, implement `process()` |

---

## Integration Example: Resilient Service Client

Here's how all these libraries work together in a production service:

```python
class ResilientServiceClient:
    """
    Example showing all libraries integrated together:
    - Logging for observability
    - Rate limiting for outbound calls
    - Retry for transient failures
    - Circuit breaker for cascading failure prevention
    - Caching for response caching
    - Config for settings
    - Event bus for monitoring
    - Scheduler for periodic health checks
    """
    def __init__(self, config: ConfigStore, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = get_logger("service_client")

        # Rate limiter: 100 requests per second
        self.rate_limiter = TokenBucket(
            capacity=config.get("client.rate_limit.capacity", type_=int),
            refill_rate=config.get("client.rate_limit.refill_rate", type_=float),
        )

        # Circuit breaker
        self.breaker = CircuitBreaker(
            "external_service",
            CircuitBreakerConfig(
                failure_threshold=config.get("client.breaker.threshold", type_=int),
                timeout=config.get("client.breaker.timeout", type_=float),
            ),
        )
        self.breaker.add_listener(self._on_breaker_event)

        # Response cache
        self.cache = Cache(
            max_size=config.get("client.cache.max_size", type_=int),
            eviction_policy=LRUPolicy(),
            default_ttl=config.get("client.cache.ttl", type_=float),
        )

        # Retry policy
        self.retry_policy = (
            RetryPolicy()
            .with_max_attempts(3)
            .with_backoff(ExponentialBackoffWithJitter(base=0.5, max_delay=10.0))
            .with_retry_on(ConnectionError, TimeoutError)
            .with_listener(LoggingListener(self.logger))
        )

        self.logger.add_handler(
            ConsoleHandler(formatter=DetailedFormatter())
        )

    def get(self, path: str) -> dict:
        """Make a GET request with full resilience stack."""
        # Check cache first
        cached = self.cache.get(f"GET:{path}")
        if cached is not None:
            self.logger.debug("Cache hit for %s", path)
            return cached

        # Rate limit
        result = self.rate_limiter.allow("outbound")
        if not result.allowed:
            self.logger.warning("Rate limited, retry after %s", result.retry_after)
            raise RateLimitExceeded(result.retry_after)

        # Circuit breaker + retry
        combined = CircuitBreakerRetryPolicy(self.breaker, self.retry_policy)
        response = combined.execute(self._do_request, "GET", path)

        # Cache response
        self.cache.put(f"GET:{path}", response)
        self.event_bus.publish("client.request.success", {
            "path": path, "cached": False
        })
        return response

    def _do_request(self, method: str, path: str) -> dict:
        """Actual HTTP request (simulated)."""
        import urllib.request
        url = self.config.get("client.base_url") + path
        self.logger.debug("Request: %s %s", method, url)
        # Real implementation would use httpx/requests
        return {"status": "ok"}

    def _on_breaker_event(self, event: CircuitEvent, data: dict):
        if event == CircuitEvent.STATE_CHANGE:
            self.event_bus.publish("client.circuit_breaker.state_change", data)
            self.logger.warning("Circuit breaker state: %s -> %s",
                              data["from"], data["to"])
```

---

## Summary

These 8 libraries cover fundamental patterns used in every production system:

| Library | Key Concepts |
|---------|-------------|
| **Logging** | Hierarchical design, separation of concerns, thread safety |
| **Rate Limiter** | Algorithm trade-offs, distributed systems thinking |
| **Retry** | Resilience, backoff strategies, failure handling |
| **Circuit Breaker** | State machines, failure isolation, graceful degradation |
| **Task Scheduler** | Concurrency, priority queues, time-based scheduling |
| **Configuration** | Multiple sources, type safety, hot reload |
| **Caching** | Eviction strategies, memory management, consistency |
| **Event Bus** | Decoupling, async processing, pub/sub patterns |

Each library demonstrates:
- Clean API design with both simple and advanced usage
- Proper use of design patterns (not forced, but natural fits)
- Thread safety as a first-class concern
- Extension through abstraction (open/closed principle)
- Separation of policy from mechanism
- Comprehensive error handling

Building these from scratch gives you deep understanding of the systems you use daily in production—logging frameworks, rate limiters, circuit breakers, and caching layers are present in every large-scale service.
