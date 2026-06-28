# Advanced Machine Coding Problems

A collection of 12 advanced machine coding problems that test deep system design and implementation skills. These problems go beyond standard LLD — they require understanding of concurrency primitives, distributed systems concepts, compiler internals, and production-grade engineering.

> **Target audience:** Senior engineers preparing for Staff/Principal-level interviews, or anyone who wants to deeply understand the systems they use daily. Each problem includes production-level implementation with 200+ lines of core logic.

---

## Table of Contents

1. [Thread Pool Design](#1-thread-pool-design)
2. [Rate Limiter Design](#2-rate-limiter-design)
3. [Distributed Cache System](#3-distributed-cache-system)
4. [Message Queue](#4-message-queue)
5. [Workflow Engine](#5-workflow-engine)
6. [Distributed Key-Value Store](#6-distributed-key-value-store)
7. [Incremental Compiler](#7-incremental-compiler)
8. [LeetCode Judge Service](#8-leetcode-judge-service)
9. [Code Runner Service](#9-code-runner-service)
10. [Trading Platform](#10-trading-platform)
11. [Order Matching Engine](#11-order-matching-engine)
12. [Cloud Storage Service](#12-cloud-storage-service)

---

## 1. Thread Pool Design

### Detailed Requirements

- Create a pool of worker threads with configurable initial and maximum size
- Support task submission returning `Future` objects for result retrieval
- Implement multiple rejection policies: Abort, CallerRuns, Discard, DiscardOldest
- Support graceful and immediate shutdown modes
- Dynamic pool sizing: grow under load, shrink when idle
- Monitor thread health: detect and replace hung threads
- Task prioritization with priority queues
- Support scheduled/delayed task execution
- Track pool statistics: active threads, completed tasks, queue depth

### Architecture Overview

```
Client ──submits──▶ ThreadPool ──dispatches──▶ Worker*
ThreadPool ──uses──▶ TaskQueue (bounded, priority)
Worker ──pulls from──▶ TaskQueue
Worker ──writes to──▶ Future (result/exception)
PoolManager ──monitors──▶ Worker health, pool sizing
RejectionHandler ──invoked when──▶ queue is full
```

### Key Design Decisions and Tradeoffs

| Decision | Tradeoff |
|----------|----------|
| Bounded vs unbounded queue | Bounded prevents OOM but requires rejection policy; unbounded is simpler but risky |
| Core vs max threads | Core threads stay alive; max threads allow burst capacity but consume resources |
| Thread creation eagerness | Lazy (create on demand) saves resources; eager (pre-create) reduces latency |
| Keep-alive for idle threads | Short timeout reclaims resources quickly; long timeout reduces thread churn |
| Lock granularity | Single pool lock is simple; per-worker state reduces contention |

### Core Implementation

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from concurrent.futures import Future
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any, Optional
import threading
import time
import heapq
import uuid
import traceback


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class ShutdownMode(Enum):
    GRACEFUL = auto()    # finish queued tasks, then stop
    IMMEDIATE = auto()   # stop after current tasks, discard queued


class RejectionPolicy(ABC):
    @abstractmethod
    def reject(self, task: "PoolTask", pool: "ThreadPool") -> None:
        pass


class AbortPolicy(RejectionPolicy):
    def reject(self, task: "PoolTask", pool: "ThreadPool") -> None:
        raise RuntimeError(f"Task {task.task_id} rejected: queue full "
                           f"(size={pool.queue_size})")


class CallerRunsPolicy(RejectionPolicy):
    def reject(self, task: "PoolTask", pool: "ThreadPool") -> None:
        if not pool.is_shutdown:
            task.callable()


class DiscardPolicy(RejectionPolicy):
    def reject(self, task: "PoolTask", pool: "ThreadPool") -> None:
        pass  # silently discard


class DiscardOldestPolicy(RejectionPolicy):
    def reject(self, task: "PoolTask", pool: "ThreadPool") -> None:
        pool._task_queue.discard_oldest()
        pool._task_queue.put(task)


@dataclass(order=True)
class PoolTask:
    priority: int = field(compare=True)
    sequence: int = field(compare=True)
    task_id: str = field(compare=False,
                         default_factory=lambda: str(uuid.uuid4())[:8])
    callable: Callable = field(compare=False, default=None)
    future: Future = field(compare=False, default_factory=Future)
    submitted_at: float = field(compare=False, default_factory=time.monotonic)
    scheduled_time: float = field(compare=False, default=0.0)

    def __post_init__(self):
        self.priority = -self.priority  # negate for max-heap behavior


class BoundedPriorityQueue:
    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._heap: list[PoolTask] = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    def put(self, task: PoolTask, timeout: float = None) -> bool:
        with self._not_full:
            if len(self._heap) >= self._max_size:
                if timeout is None:
                    return False
                if not self._not_full.wait(timeout=timeout):
                    return False
            heapq.heappush(self._heap, task)
            self._not_empty.notify()
            return True

    def get(self, timeout: float = None) -> Optional[PoolTask]:
        with self._not_empty:
            while not self._heap:
                if not self._not_empty.wait(timeout=timeout):
                    return None

            now = time.monotonic()
            if self._heap[0].scheduled_time > now:
                wait = self._heap[0].scheduled_time - now
                self._not_empty.wait(timeout=min(wait, timeout or wait))
                if not self._heap or self._heap[0].scheduled_time > now:
                    return None

            task = heapq.heappop(self._heap)
            self._not_full.notify()
            return task

    def discard_oldest(self) -> Optional[PoolTask]:
        with self._lock:
            if self._heap:
                task = heapq.heappop(self._heap)
                self._not_full.notify()
                return task
            return None

    @property
    def size(self) -> int:
        return len(self._heap)

    def drain(self) -> list[PoolTask]:
        with self._lock:
            tasks = list(self._heap)
            self._heap.clear()
            return tasks


@dataclass
class PoolStats:
    core_pool_size: int = 0
    max_pool_size: int = 0
    active_threads: int = 0
    idle_threads: int = 0
    total_threads: int = 0
    queue_depth: int = 0
    completed_tasks: int = 0
    rejected_tasks: int = 0
    failed_tasks: int = 0
    total_submitted: int = 0


class Worker:
    def __init__(self, worker_id: int, pool: "ThreadPool"):
        self.worker_id = worker_id
        self._pool = pool
        self._thread = threading.Thread(
            target=self._run, daemon=True,
            name=f"pool-worker-{worker_id}"
        )
        self._current_task: Optional[PoolTask] = None
        self._idle_since: float = time.monotonic()
        self._tasks_completed = 0
        self._alive = True

    def start(self) -> None:
        self._thread.start()

    @property
    def is_idle(self) -> bool:
        return self._current_task is None

    @property
    def idle_time(self) -> float:
        if not self.is_idle:
            return 0.0
        return time.monotonic() - self._idle_since

    def _run(self) -> None:
        while self._alive and not self._pool.is_shutdown:
            task = self._pool._task_queue.get(timeout=1.0)
            if task is None:
                if self._should_terminate():
                    break
                continue

            self._current_task = task
            self._execute(task)
            self._current_task = None
            self._idle_since = time.monotonic()

        self._pool._on_worker_exit(self)

    def _execute(self, task: PoolTask) -> None:
        if task.future.cancelled():
            return

        try:
            result = task.callable()
            task.future.set_result(result)
            self._tasks_completed += 1
            self._pool._stats_completed += 1
        except Exception as e:
            task.future.set_exception(e)
            self._pool._stats_failed += 1

    def _should_terminate(self) -> bool:
        if self._pool._shutdown_mode == ShutdownMode.IMMEDIATE:
            return True
        with self._pool._lock:
            if (len(self._pool._workers) > self._pool._core_size
                    and self.idle_time > self._pool._keep_alive):
                return True
        return False

    def stop(self) -> None:
        self._alive = False


class ThreadPool:
    def __init__(self, core_size: int = 4, max_size: int = 16,
                 queue_capacity: int = 1000,
                 keep_alive_seconds: float = 60.0,
                 rejection_policy: RejectionPolicy = None):
        self._core_size = core_size
        self._max_size = max_size
        self._keep_alive = keep_alive_seconds
        self._task_queue = BoundedPriorityQueue(queue_capacity)
        self._rejection_policy = rejection_policy or AbortPolicy()

        self._workers: list[Worker] = []
        self._lock = threading.Lock()
        self._shutdown_mode: Optional[ShutdownMode] = None
        self._sequence_counter = 0

        self._stats_completed = 0
        self._stats_failed = 0
        self._stats_rejected = 0
        self._stats_submitted = 0

        for i in range(core_size):
            self._add_worker()

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown_mode is not None

    @property
    def queue_size(self) -> int:
        return self._task_queue.size

    def submit(self, fn: Callable[..., Any], *args,
               priority: TaskPriority = TaskPriority.NORMAL,
               delay_seconds: float = 0,
               **kwargs) -> Future:
        if self.is_shutdown:
            raise RuntimeError("Pool is shut down")

        self._stats_submitted += 1
        self._sequence_counter += 1

        wrapped = lambda: fn(*args, **kwargs)  # noqa: E731
        task = PoolTask(
            priority=priority.value,
            sequence=self._sequence_counter,
            callable=wrapped,
            scheduled_time=time.monotonic() + delay_seconds,
        )

        if not self._try_grow_and_submit(task):
            if not self._task_queue.put(task):
                self._stats_rejected += 1
                self._rejection_policy.reject(task, self)

        return task.future

    def _try_grow_and_submit(self, task: PoolTask) -> bool:
        with self._lock:
            idle_count = sum(1 for w in self._workers if w.is_idle)
            if idle_count == 0 and len(self._workers) < self._max_size:
                self._add_worker()

        return self._task_queue.put(task)

    def _add_worker(self) -> Worker:
        worker = Worker(len(self._workers), self)
        self._workers.append(worker)
        worker.start()
        return worker

    def _on_worker_exit(self, worker: Worker) -> None:
        with self._lock:
            if worker in self._workers:
                self._workers.remove(worker)
            if (not self.is_shutdown
                    and len(self._workers) < self._core_size):
                self._add_worker()

    def shutdown(self, mode: ShutdownMode = ShutdownMode.GRACEFUL,
                 timeout: float = 30.0) -> bool:
        self._shutdown_mode = mode

        if mode == ShutdownMode.IMMEDIATE:
            remaining = self._task_queue.drain()
            for task in remaining:
                task.future.cancel()
            for worker in self._workers:
                worker.stop()

        deadline = time.monotonic() + timeout
        for worker in list(self._workers):
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                return False
            worker._thread.join(timeout=remaining_time)

        return len(self._workers) == 0

    def get_stats(self) -> PoolStats:
        with self._lock:
            active = sum(1 for w in self._workers if not w.is_idle)
            idle = sum(1 for w in self._workers if w.is_idle)
            return PoolStats(
                core_pool_size=self._core_size,
                max_pool_size=self._max_size,
                active_threads=active,
                idle_threads=idle,
                total_threads=len(self._workers),
                queue_depth=self._task_queue.size,
                completed_tasks=self._stats_completed,
                rejected_tasks=self._stats_rejected,
                failed_tasks=self._stats_failed,
                total_submitted=self._stats_submitted,
            )

    def __enter__(self) -> "ThreadPool":
        return self

    def __exit__(self, *args) -> None:
        self.shutdown(ShutdownMode.GRACEFUL)
```

### Concurrency Handling

- **`BoundedPriorityQueue`** uses `Condition` variables for efficient blocking — `_not_empty` wakes workers when tasks arrive, `_not_full` wakes submitters when space opens up
- **Worker lifecycle** is self-managed — workers check `_should_terminate` to decide whether to exit when idle, enabling dynamic pool shrinking
- **Pool-level lock** protects the worker list and pool sizing decisions, but task execution is lock-free (each worker runs independently)
- **Future** provides thread-safe result delivery from worker to caller without explicit synchronization
- **Graceful shutdown** waits for queued tasks; immediate shutdown cancels pending futures and stops workers

### Scalability Considerations

- Core threads handle steady-state load; max threads absorb bursts
- The priority queue ensures critical tasks skip ahead of normal ones
- Keep-alive timer reclaims excess threads during low-load periods, returning to core size
- For CPU-bound workloads, use `ProcessPoolExecutor` instead (to bypass the GIL)
- Consider per-priority sub-queues for O(1) fairness guarantees

### Testing Approach

- **Functional**: Submit tasks and verify futures resolve with correct results
- **Concurrency**: Submit 1000 tasks from 10 threads and verify all complete without duplicates or losses
- **Rejection**: Fill the queue, submit more, and verify the rejection policy fires
- **Shutdown**: Submit long-running tasks, call `shutdown(GRACEFUL)`, verify they complete
- **Dynamic sizing**: Submit burst traffic, verify pool grows to max_size, then shrinks after idle timeout
- **Priority**: Submit LOW, then CRITICAL tasks — verify CRITICAL executes first

---

## 2. Rate Limiter Design

### Detailed Requirements

- Support multiple rate limiting algorithms: Token Bucket, Leaky Bucket, Fixed Window, Sliding Window Log, Sliding Window Counter
- Distributed rate limiting across multiple service instances
- Per-user and per-API-endpoint granularity
- Configurable rate limits with hot-reload capability
- Return accurate rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)
- Support rate limit exemptions (whitelist) and custom rules
- Handle clock skew in distributed environments
- Provide monitoring and alerting for rate limit violations

### Architecture Overview

```
Client ──request──▶ RateLimitMiddleware ──check──▶ RateLimiter
RateLimiter ──uses──▶ Algorithm (TokenBucket | SlidingWindow | ...)
RateLimiter ──stores state──▶ StateStore (InMemory | Redis interface)
RateLimitConfig ──defines──▶ limits per (user, endpoint)
RateLimitResult ──returns──▶ allowed/denied + headers
```

### Key Design Decisions and Tradeoffs

| Decision | Tradeoff |
|----------|----------|
| Token Bucket vs Sliding Window | Token bucket handles bursts naturally; sliding window gives precise rate guarantees |
| In-memory vs distributed state | In-memory is fast but per-instance; distributed is consistent but adds latency |
| Synchronous vs async checking | Sync blocks the request; async may allow brief overages |
| Fixed vs dynamic configuration | Fixed is predictable; dynamic allows real-time tuning |

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import threading
import time
import math
from collections import defaultdict, deque


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: float  # Unix timestamp
    retry_after: float = 0.0  # seconds until next allowed request

    def headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at)),
            **({"Retry-After": str(int(self.retry_after))}
               if not self.allowed else {}),
        }


@dataclass
class RateLimitRule:
    key_prefix: str
    max_requests: int
    window_seconds: float
    algorithm: str = "sliding_window"
    burst_allowance: int = 0


class RateLimitAlgorithm(ABC):
    @abstractmethod
    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        pass


class TokenBucketAlgorithm(RateLimitAlgorithm):
    def __init__(self):
        self._buckets: dict[str, dict] = {}
        self._lock = threading.Lock()

    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        with self._lock:
            now = time.time()
            capacity = rule.max_requests + rule.burst_allowance
            refill_rate = rule.max_requests / rule.window_seconds

            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": capacity,
                    "last_refill": now,
                }

            bucket = self._buckets[key]
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(
                capacity,
                bucket["tokens"] + elapsed * refill_rate
            )
            bucket["last_refill"] = now

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return RateLimitResult(
                    allowed=True,
                    limit=rule.max_requests,
                    remaining=int(bucket["tokens"]),
                    reset_at=now + rule.window_seconds,
                )

            retry_after = (1.0 - bucket["tokens"]) / refill_rate
            return RateLimitResult(
                allowed=False,
                limit=rule.max_requests,
                remaining=0,
                reset_at=now + retry_after,
                retry_after=retry_after,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)


class SlidingWindowLogAlgorithm(RateLimitAlgorithm):
    """Precise but memory-intensive: stores timestamp of every request."""

    def __init__(self):
        self._logs: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        with self._lock:
            now = time.time()
            window_start = now - rule.window_seconds
            log = self._logs[key]

            while log and log[0] < window_start:
                log.popleft()

            current_count = len(log)

            if current_count < rule.max_requests:
                log.append(now)
                return RateLimitResult(
                    allowed=True,
                    limit=rule.max_requests,
                    remaining=rule.max_requests - current_count - 1,
                    reset_at=log[0] + rule.window_seconds if log else now + rule.window_seconds,
                )

            reset_at = log[0] + rule.window_seconds
            return RateLimitResult(
                allowed=False,
                limit=rule.max_requests,
                remaining=0,
                reset_at=reset_at,
                retry_after=reset_at - now,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._logs.pop(key, None)


class SlidingWindowCounterAlgorithm(RateLimitAlgorithm):
    """Memory-efficient approximation using weighted window counts."""

    def __init__(self):
        self._windows: dict[str, dict] = {}
        self._lock = threading.Lock()

    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        with self._lock:
            now = time.time()
            window_size = rule.window_seconds
            current_window = int(now / window_size) * window_size
            previous_window = current_window - window_size

            if key not in self._windows:
                self._windows[key] = {
                    "current_count": 0,
                    "previous_count": 0,
                    "current_window": current_window,
                }

            state = self._windows[key]

            if state["current_window"] < current_window:
                if state["current_window"] == previous_window:
                    state["previous_count"] = state["current_count"]
                else:
                    state["previous_count"] = 0
                state["current_count"] = 0
                state["current_window"] = current_window

            elapsed_ratio = (now - current_window) / window_size
            previous_weight = 1.0 - elapsed_ratio
            estimated = (state["previous_count"] * previous_weight
                         + state["current_count"])

            if estimated < rule.max_requests:
                state["current_count"] += 1
                return RateLimitResult(
                    allowed=True,
                    limit=rule.max_requests,
                    remaining=int(rule.max_requests - estimated - 1),
                    reset_at=current_window + window_size,
                )

            return RateLimitResult(
                allowed=False,
                limit=rule.max_requests,
                remaining=0,
                reset_at=current_window + window_size,
                retry_after=current_window + window_size - now,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


class FixedWindowAlgorithm(RateLimitAlgorithm):
    def __init__(self):
        self._counters: dict[str, dict] = {}
        self._lock = threading.Lock()

    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        with self._lock:
            now = time.time()
            window_start = int(now / rule.window_seconds) * rule.window_seconds
            window_end = window_start + rule.window_seconds

            if key not in self._counters or self._counters[key]["window"] != window_start:
                self._counters[key] = {"count": 0, "window": window_start}

            state = self._counters[key]

            if state["count"] < rule.max_requests:
                state["count"] += 1
                return RateLimitResult(
                    allowed=True,
                    limit=rule.max_requests,
                    remaining=rule.max_requests - state["count"],
                    reset_at=window_end,
                )

            return RateLimitResult(
                allowed=False,
                limit=rule.max_requests,
                remaining=0,
                reset_at=window_end,
                retry_after=window_end - now,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._counters.pop(key, None)


class LeakyBucketAlgorithm(RateLimitAlgorithm):
    """Smooths traffic to a constant rate by leaking at a fixed rate."""

    def __init__(self):
        self._buckets: dict[str, dict] = {}
        self._lock = threading.Lock()

    def try_acquire(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        with self._lock:
            now = time.time()
            leak_rate = rule.max_requests / rule.window_seconds

            if key not in self._buckets:
                self._buckets[key] = {"water": 0.0, "last_leak": now}

            bucket = self._buckets[key]
            elapsed = now - bucket["last_leak"]
            bucket["water"] = max(0, bucket["water"] - elapsed * leak_rate)
            bucket["last_leak"] = now

            capacity = rule.max_requests
            if bucket["water"] < capacity:
                bucket["water"] += 1
                return RateLimitResult(
                    allowed=True,
                    limit=rule.max_requests,
                    remaining=int(capacity - bucket["water"]),
                    reset_at=now + bucket["water"] / leak_rate,
                )

            retry_after = 1.0 / leak_rate
            return RateLimitResult(
                allowed=False,
                limit=rule.max_requests,
                remaining=0,
                reset_at=now + retry_after,
                retry_after=retry_after,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)


class RateLimiterService:
    ALGORITHMS = {
        "token_bucket": TokenBucketAlgorithm,
        "sliding_window_log": SlidingWindowLogAlgorithm,
        "sliding_window_counter": SlidingWindowCounterAlgorithm,
        "fixed_window": FixedWindowAlgorithm,
        "leaky_bucket": LeakyBucketAlgorithm,
    }

    def __init__(self):
        self._rules: dict[str, RateLimitRule] = {}
        self._algorithms: dict[str, RateLimitAlgorithm] = {}
        self._whitelist: set[str] = set()
        self._violation_count: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def add_rule(self, endpoint: str, rule: RateLimitRule) -> None:
        self._rules[endpoint] = rule
        algo_class = self.ALGORITHMS.get(rule.algorithm, SlidingWindowCounterAlgorithm)
        self._algorithms[endpoint] = algo_class()

    def whitelist_key(self, key: str) -> None:
        self._whitelist.add(key)

    def check(self, user_id: str, endpoint: str) -> RateLimitResult:
        if user_id in self._whitelist:
            return RateLimitResult(allowed=True, limit=999999,
                                   remaining=999999,
                                   reset_at=time.time() + 3600)

        rule = self._rules.get(endpoint)
        if not rule:
            return RateLimitResult(allowed=True, limit=0, remaining=0,
                                   reset_at=0)

        key = f"{rule.key_prefix}:{user_id}:{endpoint}"
        algorithm = self._algorithms[endpoint]
        result = algorithm.try_acquire(key, rule)

        if not result.allowed:
            self._violation_count[key] += 1

        return result

    def get_violations(self) -> dict[str, int]:
        return dict(self._violation_count)

    def reset_user(self, user_id: str, endpoint: str = None) -> None:
        if endpoint:
            rule = self._rules.get(endpoint)
            if rule:
                key = f"{rule.key_prefix}:{user_id}:{endpoint}"
                self._algorithms[endpoint].reset(key)
        else:
            for ep, algo in self._algorithms.items():
                rule = self._rules[ep]
                key = f"{rule.key_prefix}:{user_id}:{ep}"
                algo.reset(key)
```

### Concurrency Handling

- Each algorithm implementation uses its own lock — different endpoints can be rate-limited concurrently
- Token bucket refill calculation is atomic within the lock, ensuring no lost tokens
- Sliding window log uses `deque` for O(1) amortized cleanup of expired entries
- For distributed deployments, replace in-memory state with Redis using Lua scripts for atomic check-and-increment

### Scalability Considerations

- **Sliding Window Counter** is the best balance of accuracy and memory — only 2 counters per key vs. N timestamps for Sliding Window Log
- **Token Bucket** is ideal for APIs that should allow bursts (e.g., batch uploads)
- **Leaky Bucket** enforces constant rate and is ideal for rate-limiting outgoing requests (e.g., to third-party APIs)
- **Distributed state**: Use Redis `INCR` + `EXPIRE` for fixed window, or Lua scripts for sliding window atomicity
- **Sharding**: Partition rate limit state by user-id hash to scale horizontally

### Testing Approach

- **Basic rate limiting**: Send `max_requests + 1` requests and verify the last one is denied
- **Window reset**: Wait for window to expire and verify new requests are allowed
- **Burst handling**: Verify token bucket allows bursts up to capacity
- **Concurrent stress test**: 100 threads sending requests for same user — verify total allowed ≤ limit
- **Clock skew simulation**: Inject time offsets and verify algorithms handle them gracefully
- **Whitelist bypass**: Verify whitelisted users are never rate-limited

---

## 3. Distributed Cache System

### Detailed Requirements

- Implement consistent hashing for key distribution across cache nodes
- Support virtual nodes for better load distribution
- Configurable replication factor (store copies on N nodes)
- Multiple eviction policies per node: LRU, LFU, TTL-based
- Cache coherence protocol for multi-node consistency
- Support for cache-aside, read-through, and write-through patterns
- Node health monitoring with automatic failover
- Cache warmup and preloading strategies

### Architecture Overview

```
Client ──request──▶ CacheRouter ──consistent hash──▶ CacheNode
CacheRouter ──uses──▶ ConsistentHashRing
CacheNode ──stores──▶ entries with EvictionPolicy
Replicator ──copies──▶ data to replica nodes
HealthChecker ──monitors──▶ CacheNode availability
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from collections import OrderedDict
import hashlib
import bisect
import threading
import time


class ConsistentHashRing:
    def __init__(self, virtual_nodes: int = 150):
        self._virtual_nodes = virtual_nodes
        self._ring: list[int] = []  # sorted hash positions
        self._node_map: dict[int, str] = {}  # hash → node_id
        self._nodes: set[str] = set()
        self._lock = threading.Lock()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.add(node_id)
            for i in range(self._virtual_nodes):
                vnode_key = f"{node_id}:vnode:{i}"
                hash_val = self._hash(vnode_key)
                self._node_map[hash_val] = node_id
                bisect.insort(self._ring, hash_val)

    def remove_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.discard(node_id)
            for i in range(self._virtual_nodes):
                vnode_key = f"{node_id}:vnode:{i}"
                hash_val = self._hash(vnode_key)
                self._node_map.pop(hash_val, None)
                idx = bisect.bisect_left(self._ring, hash_val)
                if idx < len(self._ring) and self._ring[idx] == hash_val:
                    self._ring.pop(idx)

    def get_node(self, key: str) -> Optional[str]:
        if not self._ring:
            return None
        hash_val = self._hash(key)
        idx = bisect.bisect_right(self._ring, hash_val) % len(self._ring)
        return self._node_map[self._ring[idx]]

    def get_nodes(self, key: str, count: int) -> list[str]:
        """Get `count` distinct nodes for replication."""
        if not self._ring or count <= 0:
            return []

        hash_val = self._hash(key)
        idx = bisect.bisect_right(self._ring, hash_val) % len(self._ring)

        nodes = []
        seen = set()
        checked = 0
        while len(nodes) < count and checked < len(self._ring):
            node_id = self._node_map[self._ring[(idx + checked) % len(self._ring)]]
            if node_id not in seen:
                nodes.append(node_id)
                seen.add(node_id)
            checked += 1

        return nodes

    @property
    def node_count(self) -> int:
        return len(self._nodes)


@dataclass
class CacheEntry:
    key: str
    value: Any
    version: int = 1
    created_at: float = field(default_factory=time.monotonic)
    last_accessed: float = field(default_factory=time.monotonic)
    ttl: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.monotonic() - self.created_at) > self.ttl


class CacheNode:
    def __init__(self, node_id: str, max_size: int = 10000,
                 default_ttl: float = None):
        self.node_id = node_id
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
        self.is_healthy = True

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired:
                del self._store[key]
                self._stats["misses"] += 1
                return None

            self._store.move_to_end(key)
            entry.last_accessed = time.monotonic()
            self._stats["hits"] += 1
            return entry.value

    def put(self, key: str, value: Any, ttl: float = None,
            version: int = 1) -> None:
        with self._lock:
            if key in self._store:
                existing = self._store[key]
                if version <= existing.version:
                    return  # stale write
                del self._store[key]

            while len(self._store) >= self._max_size:
                evicted_key, _ = self._store.popitem(last=False)
                self._stats["evictions"] += 1

            entry = CacheEntry(
                key=key, value=value, version=version,
                ttl=ttl or self._default_ttl,
            )
            self._store[key] = entry

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            return self._store.get(key)

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {**self._stats, "hit_rate": hit_rate, "size": self.size}

    def cleanup_expired(self) -> int:
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired]
            for key in expired:
                del self._store[key]
            return len(expired)


class DistributedCache:
    def __init__(self, replication_factor: int = 2,
                 virtual_nodes: int = 150,
                 read_quorum: int = 1,
                 write_quorum: int = 1):
        self._ring = ConsistentHashRing(virtual_nodes)
        self._nodes: dict[str, CacheNode] = {}
        self._replication_factor = replication_factor
        self._read_quorum = read_quorum
        self._write_quorum = write_quorum
        self._version_counter = 0
        self._lock = threading.Lock()
        self._data_source: Optional[Callable[[str], Any]] = None

    def add_node(self, node: CacheNode) -> None:
        with self._lock:
            self._nodes[node.node_id] = node
            self._ring.add_node(node.node_id)

    def remove_node(self, node_id: str) -> dict[str, Any]:
        with self._lock:
            node = self._nodes.pop(node_id, None)
            self._ring.remove_node(node_id)
            if node:
                orphaned = {}
                for key in list(node._store.keys()):
                    entry = node.get_entry(key)
                    if entry:
                        orphaned[key] = entry.value
                return orphaned
            return {}

    def get(self, key: str) -> Optional[Any]:
        target_nodes = self._ring.get_nodes(key, self._replication_factor)
        if not target_nodes:
            return None

        results = []
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_healthy:
                entry = node.get_entry(key)
                if entry and not entry.is_expired:
                    results.append(entry)

        if not results:
            if self._data_source:
                value = self._data_source(key)
                if value is not None:
                    self.put(key, value)
                return value
            return None

        best = max(results, key=lambda e: e.version)

        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_healthy:
                existing = node.get_entry(key)
                if not existing or existing.version < best.version:
                    node.put(key, best.value, best.ttl, best.version)

        return best.value

    def put(self, key: str, value: Any, ttl: float = None) -> bool:
        with self._lock:
            self._version_counter += 1
            version = self._version_counter

        target_nodes = self._ring.get_nodes(key, self._replication_factor)
        successes = 0

        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_healthy:
                node.put(key, value, ttl, version)
                successes += 1

        return successes >= self._write_quorum

    def delete(self, key: str) -> bool:
        target_nodes = self._ring.get_nodes(key, self._replication_factor)
        deleted = False
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_healthy:
                if node.delete(key):
                    deleted = True
        return deleted

    def set_data_source(self, loader: Callable[[str], Any]) -> None:
        self._data_source = loader

    def rebalance(self) -> int:
        """Redistribute keys after node topology changes."""
        moved = 0
        all_keys: set[str] = set()

        for node in self._nodes.values():
            for key in list(node._store.keys()):
                all_keys.add(key)

        for key in all_keys:
            target_nodes = set(self._ring.get_nodes(key, self._replication_factor))
            for node_id, node in self._nodes.items():
                entry = node.get_entry(key)
                if entry:
                    if node_id not in target_nodes:
                        for target_id in target_nodes:
                            target = self._nodes.get(target_id)
                            if target:
                                target.put(key, entry.value, entry.ttl, entry.version)
                        node.delete(key)
                        moved += 1
                    break
        return moved

    def get_cluster_stats(self) -> dict:
        stats = {}
        for node_id, node in self._nodes.items():
            stats[node_id] = node.stats
        return stats
```

### Concurrency Handling

- **Per-node RLock** allows independent access to different cache nodes
- **Version-based conflict resolution** — writes with stale versions are rejected, preventing lost updates
- **Read repair** — on read, if replicas have different versions, the stale ones are updated with the latest version
- **Quorum reads/writes** — configurable consistency levels (e.g., write to 2 of 3 nodes for durability)

### Scalability Considerations

- **Virtual nodes** (150 per physical node) ensure even key distribution even with few nodes
- **Replication factor** trades storage for availability — with 3 replicas, 2 nodes can fail without data loss
- **Rebalancing** after node addition/removal moves only K/N keys on average (where K = total keys, N = nodes)
- **Read-through** pattern avoids cache stampedes — only one request loads from the data source
- Horizontal scaling: add nodes and call `rebalance()` to redistribute

### Testing Approach

- **Hash distribution**: Add 100K keys, verify each node gets roughly K/N keys (within 20% variance)
- **Node failure**: Remove a node, verify all its keys are still accessible from replicas
- **Version conflicts**: Write the same key from two threads with different values, verify the higher-version wins
- **Rebalance**: Add a node, call rebalance, verify keys moved correctly
- **TTL expiration**: Set short TTL, wait, verify entries are gone
- **Read-through**: Configure a data source, verify cache miss triggers a load

---

## 4. Message Queue

### Detailed Requirements

- Support multiple topics with configurable partition count
- Consumer groups with partition assignment and rebalancing
- Offset management for reliable message consumption
- At-least-once, at-most-once, and exactly-once delivery guarantee options
- Message retention with configurable time-based or size-based policies
- Support both push (subscription callback) and pull (poll) consumption models
- Dead letter queue for messages that repeatedly fail processing
- Message ordering guarantees within a partition

### Architecture Overview

```
Producer ──publishes──▶ Topic ──partitioned into──▶ Partition*
Partition ──stores──▶ Message* (append-only log)
ConsumerGroup ──assigns──▶ Partition → Consumer
Consumer ──tracks──▶ committed offset per partition
DeadLetterQueue ──receives──▶ repeatedly failed messages
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Any
import threading
import time
import uuid
import hashlib
from collections import defaultdict


class DeliveryGuarantee(Enum):
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class Message:
    key: Optional[str]
    value: Any
    topic: str = ""
    partition: int = -1
    offset: int = -1
    timestamp: float = field(default_factory=time.time)
    headers: dict[str, str] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])

    def __repr__(self):
        return f"Message(key={self.key}, partition={self.partition}, offset={self.offset})"


class Partition:
    def __init__(self, partition_id: int, topic_name: str,
                 retention_seconds: float = 3600,
                 max_size_bytes: int = 100 * 1024 * 1024):
        self.partition_id = partition_id
        self.topic_name = topic_name
        self._messages: list[Message] = []
        self._retention = retention_seconds
        self._max_size = max_size_bytes
        self._current_size = 0
        self._lock = threading.Lock()
        self._high_watermark = 0

    def append(self, message: Message) -> int:
        with self._lock:
            message.partition = self.partition_id
            message.offset = self._high_watermark
            self._messages.append(message)
            self._high_watermark += 1
            self._enforce_retention()
            return message.offset

    def read(self, offset: int, max_messages: int = 10) -> list[Message]:
        with self._lock:
            if not self._messages:
                return []

            start_offset = self._messages[0].offset
            relative_idx = offset - start_offset
            if relative_idx < 0:
                relative_idx = 0

            end_idx = min(relative_idx + max_messages, len(self._messages))
            return list(self._messages[relative_idx:end_idx])

    @property
    def earliest_offset(self) -> int:
        if not self._messages:
            return 0
        return self._messages[0].offset

    @property
    def latest_offset(self) -> int:
        return self._high_watermark

    def _enforce_retention(self) -> None:
        cutoff = time.time() - self._retention
        while self._messages and self._messages[0].timestamp < cutoff:
            self._messages.pop(0)

    @property
    def message_count(self) -> int:
        return len(self._messages)


class PartitionAssignor(ABC):
    @abstractmethod
    def assign(self, partitions: list[int],
               consumers: list[str]) -> dict[str, list[int]]:
        pass


class RangeAssignor(PartitionAssignor):
    def assign(self, partitions: list[int],
               consumers: list[str]) -> dict[str, list[int]]:
        if not consumers:
            return {}
        assignment: dict[str, list[int]] = {c: [] for c in consumers}
        partitions_sorted = sorted(partitions)
        consumers_sorted = sorted(consumers)
        chunk_size = len(partitions_sorted) // len(consumers_sorted)
        remainder = len(partitions_sorted) % len(consumers_sorted)

        idx = 0
        for i, consumer in enumerate(consumers_sorted):
            count = chunk_size + (1 if i < remainder else 0)
            assignment[consumer] = partitions_sorted[idx:idx + count]
            idx += count

        return assignment


class RoundRobinAssignor(PartitionAssignor):
    def assign(self, partitions: list[int],
               consumers: list[str]) -> dict[str, list[int]]:
        if not consumers:
            return {}
        assignment: dict[str, list[int]] = {c: [] for c in consumers}
        consumers_sorted = sorted(consumers)
        for i, p in enumerate(sorted(partitions)):
            consumer = consumers_sorted[i % len(consumers_sorted)]
            assignment[consumer].append(p)
        return assignment


class ConsumerGroup:
    def __init__(self, group_id: str,
                 assignor: PartitionAssignor = None):
        self.group_id = group_id
        self._assignor = assignor or RangeAssignor()
        self._members: set[str] = set()
        self._assignment: dict[str, list[int]] = {}
        self._committed_offsets: dict[int, int] = {}  # partition → offset
        self._lock = threading.Lock()

    def join(self, consumer_id: str, partitions: list[int]) -> dict[str, list[int]]:
        with self._lock:
            self._members.add(consumer_id)
            self._assignment = self._assignor.assign(
                partitions, list(self._members)
            )
            return self._assignment

    def leave(self, consumer_id: str, partitions: list[int]) -> None:
        with self._lock:
            self._members.discard(consumer_id)
            if self._members:
                self._assignment = self._assignor.assign(
                    partitions, list(self._members)
                )

    def commit_offset(self, partition: int, offset: int) -> None:
        with self._lock:
            current = self._committed_offsets.get(partition, -1)
            if offset > current:
                self._committed_offsets[partition] = offset

    def get_committed_offset(self, partition: int) -> int:
        return self._committed_offsets.get(partition, 0)

    def get_assignment(self, consumer_id: str) -> list[int]:
        return self._assignment.get(consumer_id, [])


class Topic:
    def __init__(self, name: str, num_partitions: int = 3,
                 retention_seconds: float = 3600):
        self.name = name
        self.partitions = [
            Partition(i, name, retention_seconds)
            for i in range(num_partitions)
        ]
        self._groups: dict[str, ConsumerGroup] = {}
        self._lock = threading.Lock()

    def get_partition(self, key: Optional[str]) -> Partition:
        if key is None:
            idx = hash(time.time()) % len(self.partitions)
        else:
            idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(self.partitions)
        return self.partitions[idx]

    def get_or_create_group(self, group_id: str,
                             assignor: PartitionAssignor = None) -> ConsumerGroup:
        with self._lock:
            if group_id not in self._groups:
                self._groups[group_id] = ConsumerGroup(group_id, assignor)
            return self._groups[group_id]


class DeadLetterQueue:
    def __init__(self, max_size: int = 10000):
        self._messages: list[tuple[Message, str, int]] = []
        self._max_size = max_size
        self._lock = threading.Lock()

    def add(self, message: Message, reason: str, attempts: int) -> None:
        with self._lock:
            if len(self._messages) >= self._max_size:
                self._messages.pop(0)
            self._messages.append((message, reason, attempts))

    def get_all(self) -> list[tuple[Message, str, int]]:
        with self._lock:
            return list(self._messages)

    @property
    def size(self) -> int:
        return len(self._messages)


class Consumer:
    def __init__(self, consumer_id: str = None, group_id: str = "",
                 delivery: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
                 max_retries: int = 3):
        self.consumer_id = consumer_id or str(uuid.uuid4())[:8]
        self.group_id = group_id
        self._delivery = delivery
        self._max_retries = max_retries
        self._handlers: dict[str, Callable[[Message], None]] = {}
        self._running = False
        self._local_offsets: dict[str, dict[int, int]] = {}  # topic → {partition → offset}

    def subscribe(self, topic_name: str,
                  handler: Callable[[Message], None]) -> None:
        self._handlers[topic_name] = handler

    def poll(self, topic: Topic, timeout: float = 1.0) -> list[Message]:
        group = topic.get_or_create_group(self.group_id)
        assigned = group.get_assignment(self.consumer_id)
        all_messages = []

        for partition_id in assigned:
            partition = topic.partitions[partition_id]
            offset = self._get_offset(topic.name, partition_id, group)

            messages = partition.read(offset, max_messages=100)
            all_messages.extend(messages)

            if messages:
                if self._delivery == DeliveryGuarantee.AT_MOST_ONCE:
                    new_offset = messages[-1].offset + 1
                    group.commit_offset(partition_id, new_offset)
                    self._set_local_offset(topic.name, partition_id, new_offset)

        return all_messages

    def commit(self, topic: Topic, messages: list[Message]) -> None:
        group = topic.get_or_create_group(self.group_id)
        partition_offsets: dict[int, int] = {}
        for msg in messages:
            current = partition_offsets.get(msg.partition, -1)
            if msg.offset + 1 > current:
                partition_offsets[msg.partition] = msg.offset + 1

        for partition_id, offset in partition_offsets.items():
            group.commit_offset(partition_id, offset)
            self._set_local_offset(topic.name, partition_id, offset)

    def _get_offset(self, topic: str, partition: int,
                    group: ConsumerGroup) -> int:
        local = self._local_offsets.get(topic, {}).get(partition)
        if local is not None:
            return local
        return group.get_committed_offset(partition)

    def _set_local_offset(self, topic: str, partition: int,
                           offset: int) -> None:
        if topic not in self._local_offsets:
            self._local_offsets[topic] = {}
        self._local_offsets[topic][partition] = offset


class Producer:
    def __init__(self, producer_id: str = None):
        self.producer_id = producer_id or str(uuid.uuid4())[:8]
        self._sent_count = 0

    def send(self, topic: Topic, key: Optional[str],
             value: Any, headers: dict[str, str] = None) -> Message:
        message = Message(
            key=key, value=value, topic=topic.name,
            headers=headers or {},
        )
        partition = topic.get_partition(key)
        partition.append(message)
        self._sent_count += 1
        return message

    def send_batch(self, topic: Topic,
                   messages: list[tuple[Optional[str], Any]]) -> list[Message]:
        results = []
        for key, value in messages:
            results.append(self.send(topic, key, value))
        return results


class MessageBroker:
    def __init__(self):
        self._topics: dict[str, Topic] = {}
        self._dlq = DeadLetterQueue()
        self._lock = threading.Lock()

    def create_topic(self, name: str, partitions: int = 3,
                     retention_seconds: float = 3600) -> Topic:
        with self._lock:
            if name not in self._topics:
                self._topics[name] = Topic(name, partitions, retention_seconds)
            return self._topics[name]

    def get_topic(self, name: str) -> Optional[Topic]:
        return self._topics.get(name)

    def delete_topic(self, name: str) -> bool:
        with self._lock:
            return self._topics.pop(name, None) is not None

    def register_consumer(self, consumer: Consumer,
                           topic_name: str) -> None:
        topic = self._topics.get(topic_name)
        if not topic:
            raise ValueError(f"Topic {topic_name} not found")

        group = topic.get_or_create_group(consumer.group_id)
        partition_ids = list(range(len(topic.partitions)))
        group.join(consumer.consumer_id, partition_ids)

    def get_broker_stats(self) -> dict:
        stats = {}
        for name, topic in self._topics.items():
            stats[name] = {
                "partitions": len(topic.partitions),
                "messages": sum(p.message_count for p in topic.partitions),
            }
        stats["dlq_size"] = self._dlq.size
        return stats
```

### Concurrency Handling

- **Per-partition locks** for append and read operations — producers writing to different partitions don't contend
- **Per-group locks** for offset management and partition assignment — different consumer groups are independent
- **Key-based partitioning** ensures messages with the same key always go to the same partition, preserving order
- **Consumer rebalancing** is triggered on join/leave and is protected by the group lock

### Scalability Considerations

- Partitions are the unit of parallelism — more partitions allow more concurrent consumers
- Within a consumer group, each partition is assigned to exactly one consumer (no double-processing)
- Retention policy prevents unbounded growth — old messages are pruned based on time or size
- Dead letter queue prevents poison messages from blocking consumers indefinitely
- For production scale, partitions would be distributed across broker nodes with replication

### Testing Approach

- **Ordering**: Send 1000 messages with the same key, verify they're consumed in order
- **Consumer groups**: Two consumers in the same group, verify each partition is processed by exactly one consumer
- **Rebalancing**: Consumer joins/leaves group, verify partitions are reassigned correctly
- **Delivery guarantees**: Simulate consumer crash after processing but before commit — verify AT_LEAST_ONCE redelivers
- **Retention**: Set 1-second retention, send messages, wait, verify old messages are gone
- **Dead letter queue**: Send a message that always fails processing, verify it lands in DLQ after max retries

---

## 5. Workflow Engine

### Detailed Requirements

- Define workflows as DAGs with typed steps (Action, Decision, Fork, Join)
- Execute workflows with state persistence between steps
- Support parallel execution paths (fork) with synchronization (join)
- Implement compensation (rollback) when steps fail (Saga pattern)
- Retry failed steps with configurable policies
- Support long-running workflows with checkpoint/resume
- Workflow versioning and migration
- Provide execution history and audit trail

### Architecture Overview

```
WorkflowDefinition ──has──▶ Step* (DAG)
WorkflowEngine ──creates──▶ WorkflowInstance from Definition
WorkflowInstance ──tracks──▶ StepExecution* (state, result)
Step types: ActionStep, DecisionStep, ForkStep, JoinStep
CompensationManager ──runs──▶ compensations on failure (reverse order)
```

### Core Implementation

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import threading
import uuid
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, Future, wait


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    PAUSED = "paused"


@dataclass
class StepResult:
    success: bool
    output: Any = None
    error: str = ""
    duration_ms: float = 0


@dataclass
class ExecutionContext:
    """Shared context passed through workflow steps."""
    workflow_id: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    step_outputs: dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set_step_output(self, step_id: str, output: Any) -> None:
        with self._lock:
            self.step_outputs[step_id] = output

    def get_step_output(self, step_id: str) -> Any:
        return self.step_outputs.get(step_id)


class WorkflowStep(ABC):
    def __init__(self, step_id: str, name: str,
                 retry_count: int = 0, retry_delay: float = 1.0):
        self.step_id = step_id
        self.name = name
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.next_steps: list[str] = []
        self.compensation: Optional[Callable[[ExecutionContext], None]] = None

    @abstractmethod
    def execute(self, context: ExecutionContext) -> StepResult:
        pass

    def set_compensation(self,
                          comp: Callable[[ExecutionContext], None]) -> "WorkflowStep":
        self.compensation = comp
        return self

    def then(self, *step_ids: str) -> "WorkflowStep":
        self.next_steps.extend(step_ids)
        return self


class ActionStep(WorkflowStep):
    def __init__(self, step_id: str, name: str,
                 action: Callable[[ExecutionContext], Any],
                 retry_count: int = 0, retry_delay: float = 1.0):
        super().__init__(step_id, name, retry_count, retry_delay)
        self._action = action

    def execute(self, context: ExecutionContext) -> StepResult:
        start = time.monotonic()
        try:
            output = self._action(context)
            duration = (time.monotonic() - start) * 1000
            context.set_step_output(self.step_id, output)
            return StepResult(success=True, output=output,
                              duration_ms=duration)
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return StepResult(success=False, error=str(e),
                              duration_ms=duration)


class DecisionStep(WorkflowStep):
    """Conditional branching based on context evaluation."""

    def __init__(self, step_id: str, name: str,
                 condition: Callable[[ExecutionContext], str]):
        super().__init__(step_id, name)
        self._condition = condition
        self._branches: dict[str, list[str]] = {}

    def branch(self, outcome: str, *step_ids: str) -> "DecisionStep":
        self._branches[outcome] = list(step_ids)
        return self

    def execute(self, context: ExecutionContext) -> StepResult:
        try:
            outcome = self._condition(context)
            self.next_steps = self._branches.get(outcome, [])
            return StepResult(success=True, output=outcome)
        except Exception as e:
            return StepResult(success=False, error=str(e))


class ForkStep(WorkflowStep):
    """Splits execution into parallel branches."""

    def __init__(self, step_id: str, name: str,
                 parallel_branches: list[list[str]]):
        super().__init__(step_id, name)
        self.parallel_branches = parallel_branches

    def execute(self, context: ExecutionContext) -> StepResult:
        self.next_steps = [branch[0] for branch in self.parallel_branches if branch]
        return StepResult(success=True, output=f"{len(self.parallel_branches)} branches forked")


class JoinStep(WorkflowStep):
    """Synchronization point for parallel branches."""

    def __init__(self, step_id: str, name: str,
                 required_branches: list[str]):
        super().__init__(step_id, name)
        self.required_branches = required_branches
        self._completed: set[str] = set()
        self._lock = threading.Lock()

    def mark_branch_complete(self, branch_id: str) -> bool:
        with self._lock:
            self._completed.add(branch_id)
            return len(self._completed) >= len(self.required_branches)

    def execute(self, context: ExecutionContext) -> StepResult:
        return StepResult(success=True, output="All branches joined")

    def is_ready(self) -> bool:
        with self._lock:
            return len(self._completed) >= len(self.required_branches)


@dataclass
class StepExecution:
    step_id: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[StepResult] = None
    attempts: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class AuditEntry:
    timestamp: datetime = field(default_factory=datetime.now)
    step_id: str = ""
    event: str = ""
    details: str = ""


class WorkflowDefinition:
    def __init__(self, name: str, version: int = 1):
        self.name = name
        self.version = version
        self.steps: dict[str, WorkflowStep] = {}
        self.start_step: Optional[str] = None

    def add_step(self, step: WorkflowStep) -> "WorkflowDefinition":
        self.steps[step.step_id] = step
        if self.start_step is None:
            self.start_step = step.step_id
        return self

    def set_start(self, step_id: str) -> "WorkflowDefinition":
        self.start_step = step_id
        return self


class WorkflowInstance:
    def __init__(self, definition: WorkflowDefinition,
                 context: ExecutionContext = None):
        self.instance_id = str(uuid.uuid4())[:8]
        self.definition = definition
        self.context = context or ExecutionContext()
        self.context.workflow_id = self.instance_id
        self.status = WorkflowStatus.CREATED
        self.step_executions: dict[str, StepExecution] = {
            sid: StepExecution(step_id=sid)
            for sid in definition.steps
        }
        self.audit_log: list[AuditEntry] = []
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self._completed_steps: list[str] = []  # for compensation ordering

    def _audit(self, step_id: str, event: str, details: str = "") -> None:
        self.audit_log.append(AuditEntry(
            step_id=step_id, event=event, details=details,
        ))


class CompensationManager:
    def compensate(self, instance: WorkflowInstance) -> bool:
        instance.status = WorkflowStatus.COMPENSATING
        success = True

        for step_id in reversed(instance._completed_steps):
            step = instance.definition.steps.get(step_id)
            if step and step.compensation:
                try:
                    step.compensation(instance.context)
                    exec_state = instance.step_executions[step_id]
                    exec_state.status = StepStatus.COMPENSATED
                    instance._audit(step_id, "compensated")
                except Exception as e:
                    instance._audit(step_id, "compensation_failed", str(e))
                    success = False

        instance.status = (WorkflowStatus.COMPENSATED if success
                           else WorkflowStatus.FAILED)
        return success


class WorkflowEngine:
    def __init__(self, max_workers: int = 4):
        self._instances: dict[str, WorkflowInstance] = {}
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._compensation = CompensationManager()
        self._lock = threading.Lock()

    def create_instance(self, definition: WorkflowDefinition,
                         initial_vars: dict[str, Any] = None) -> WorkflowInstance:
        context = ExecutionContext()
        if initial_vars:
            context.variables.update(initial_vars)

        instance = WorkflowInstance(definition, context)
        self._instances[instance.instance_id] = instance
        return instance

    def run(self, instance: WorkflowInstance) -> WorkflowStatus:
        instance.status = WorkflowStatus.RUNNING
        instance._audit("", "workflow_started")

        start_step_id = instance.definition.start_step
        if not start_step_id:
            instance.status = WorkflowStatus.FAILED
            return instance.status

        success = self._execute_from(instance, start_step_id)

        if success:
            instance.status = WorkflowStatus.COMPLETED
            instance._audit("", "workflow_completed")
        else:
            instance._audit("", "workflow_failed, starting compensation")
            self._compensation.compensate(instance)

        instance.completed_at = datetime.now()
        return instance.status

    def _execute_from(self, instance: WorkflowInstance,
                       step_id: str) -> bool:
        step = instance.definition.steps.get(step_id)
        if not step:
            return True

        if isinstance(step, ForkStep):
            return self._execute_fork(instance, step)

        result = self._execute_step(instance, step)
        if not result:
            return False

        for next_id in step.next_steps:
            next_step = instance.definition.steps.get(next_id)
            if isinstance(next_step, JoinStep):
                if next_step.mark_branch_complete(step_id):
                    if not self._execute_from(instance, next_id):
                        return False
            else:
                if not self._execute_from(instance, next_id):
                    return False

        return True

    def _execute_step(self, instance: WorkflowInstance,
                       step: WorkflowStep) -> bool:
        exec_state = instance.step_executions[step.step_id]
        exec_state.status = StepStatus.RUNNING
        exec_state.started_at = datetime.now()
        instance._audit(step.step_id, "step_started")

        for attempt in range(step.retry_count + 1):
            exec_state.attempts = attempt + 1
            result = step.execute(instance.context)

            if result.success:
                exec_state.status = StepStatus.COMPLETED
                exec_state.result = result
                exec_state.completed_at = datetime.now()
                instance._completed_steps.append(step.step_id)
                instance._audit(step.step_id, "step_completed",
                                f"output={result.output}")
                return True

            if attempt < step.retry_count:
                delay = step.retry_delay * (2 ** attempt)
                instance._audit(step.step_id, "step_retry",
                                f"attempt={attempt+1}, delay={delay}s")
                time.sleep(delay)

        exec_state.status = StepStatus.FAILED
        exec_state.result = result
        exec_state.completed_at = datetime.now()
        instance._audit(step.step_id, "step_failed", result.error)
        return False

    def _execute_fork(self, instance: WorkflowInstance,
                       fork: ForkStep) -> bool:
        exec_state = instance.step_executions[fork.step_id]
        exec_state.status = StepStatus.RUNNING

        fork.execute(instance.context)
        exec_state.status = StepStatus.COMPLETED
        instance._completed_steps.append(fork.step_id)

        futures: dict[Future, list[str]] = {}
        for branch in fork.parallel_branches:
            if branch:
                future = self._pool.submit(
                    self._execute_branch, instance, branch
                )
                futures[future] = branch

        all_success = True
        for future in futures:
            try:
                if not future.result():
                    all_success = False
            except Exception:
                all_success = False

        return all_success

    def _execute_branch(self, instance: WorkflowInstance,
                         branch: list[str]) -> bool:
        for step_id in branch:
            step = instance.definition.steps.get(step_id)
            if not step:
                continue
            if isinstance(step, JoinStep):
                return True
            if not self._execute_step(instance, step):
                return False
            for next_id in step.next_steps:
                next_step = instance.definition.steps.get(next_id)
                if isinstance(next_step, JoinStep):
                    next_step.mark_branch_complete(step_id)
        return True

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        return self._instances.get(instance_id)
```

### Concurrency Handling

- **Fork/Join** uses `ThreadPoolExecutor` to run parallel branches concurrently, with `Future.result()` for synchronization
- **JoinStep** uses an internal lock + counter to track completed branches atomically
- **ExecutionContext** uses a lock for variable mutations, ensuring safe concurrent access from parallel branches
- **Compensation** runs in reverse order of completion (not definition order), ensuring correct undo semantics

### Scalability Considerations

- Persist workflow state to a database for crash recovery — the current in-memory model loses state on restart
- For long-running workflows (hours/days), support checkpointing and resumption
- Scale by partitioning workflow instances across workers (each worker handles a subset)
- Consider event sourcing for workflow state — replay events to reconstruct state after failure

### Testing Approach

- **Linear workflow**: A → B → C, verify execution order and context propagation
- **Branching**: Decision step routes to different paths based on context
- **Parallel execution**: Fork into 3 branches, verify all run concurrently (check timing)
- **Compensation**: Step C fails, verify B and A compensations run in reverse order
- **Retry**: Step fails twice, succeeds on third attempt — verify retry policy works
- **Context sharing**: Parallel branches write to shared context, verify all writes visible after Join

---

## 6. Distributed Key-Value Store

### Detailed Requirements

- Support basic CRUD operations: GET, PUT, DELETE
- Hash-based partitioning across multiple storage nodes
- Configurable replication with consistency levels (ONE, QUORUM, ALL)
- Conflict resolution using vector clocks or last-write-wins
- Anti-entropy protocol for detecting and repairing inconsistencies
- Support range queries with sorted storage (optional)
- Node failure detection with gossip protocol interface
- Compaction for cleaning up tombstones (deleted keys)

### Architecture Overview

```
Client ──request──▶ Coordinator ──routes──▶ StorageNode*
Coordinator ──uses──▶ Partitioner (hash ring)
StorageNode ──stores──▶ Entry* with VectorClock
ReplicationManager ──copies──▶ writes to replica nodes
ConflictResolver ──merges──▶ conflicting versions
AntiEntropy ──repairs──▶ inconsistencies via Merkle trees (interface)
```

### Core Implementation

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import hashlib
import bisect
import threading
import time
import uuid
from collections import defaultdict


class ConsistencyLevel(Enum):
    ONE = 1
    QUORUM = "quorum"
    ALL = "all"


@dataclass
class VectorClock:
    clocks: dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> "VectorClock":
        new_clocks = dict(self.clocks)
        new_clocks[node_id] = new_clocks.get(node_id, 0) + 1
        return VectorClock(clocks=new_clocks)

    def merge(self, other: "VectorClock") -> "VectorClock":
        merged = dict(self.clocks)
        for node, ts in other.clocks.items():
            merged[node] = max(merged.get(node, 0), ts)
        return VectorClock(clocks=merged)

    def is_concurrent_with(self, other: "VectorClock") -> bool:
        return not self.dominates(other) and not other.dominates(self)

    def dominates(self, other: "VectorClock") -> bool:
        if not other.clocks:
            return bool(self.clocks)
        all_keys = set(self.clocks) | set(other.clocks)
        at_least_one_greater = False
        for key in all_keys:
            self_val = self.clocks.get(key, 0)
            other_val = other.clocks.get(key, 0)
            if self_val < other_val:
                return False
            if self_val > other_val:
                at_least_one_greater = True
        return at_least_one_greater

    def __repr__(self):
        return f"VC({self.clocks})"


@dataclass
class VersionedValue:
    value: Any
    clock: VectorClock
    timestamp: float = field(default_factory=time.time)
    is_tombstone: bool = False


@dataclass
class StoreEntry:
    key: str
    versions: list[VersionedValue] = field(default_factory=list)

    def add_version(self, versioned: VersionedValue) -> None:
        non_dominated = []
        for existing in self.versions:
            if not versioned.clock.dominates(existing.clock):
                non_dominated.append(existing)
        non_dominated.append(versioned)
        self.versions = non_dominated

    @property
    def latest(self) -> Optional[VersionedValue]:
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.timestamp)

    @property
    def has_conflicts(self) -> bool:
        return len(self.versions) > 1


class StorageNode:
    def __init__(self, node_id: str, capacity: int = 100000):
        self.node_id = node_id
        self._store: dict[str, StoreEntry] = {}
        self._capacity = capacity
        self._lock = threading.RLock()
        self.is_alive = True
        self._stats = {"reads": 0, "writes": 0, "deletes": 0}

    def local_get(self, key: str) -> Optional[StoreEntry]:
        with self._lock:
            self._stats["reads"] += 1
            entry = self._store.get(key)
            if entry and entry.latest and entry.latest.is_tombstone:
                return None
            return entry

    def local_put(self, key: str, value: Any,
                  clock: VectorClock) -> VectorClock:
        with self._lock:
            self._stats["writes"] += 1
            new_clock = clock.increment(self.node_id)

            if key not in self._store:
                self._store[key] = StoreEntry(key=key)

            versioned = VersionedValue(value=value, clock=new_clock)
            self._store[key].add_version(versioned)
            return new_clock

    def local_delete(self, key: str, clock: VectorClock) -> VectorClock:
        with self._lock:
            self._stats["deletes"] += 1
            new_clock = clock.increment(self.node_id)

            if key not in self._store:
                self._store[key] = StoreEntry(key=key)

            tombstone = VersionedValue(
                value=None, clock=new_clock, is_tombstone=True
            )
            self._store[key].add_version(tombstone)
            return new_clock

    def replicate(self, key: str, versioned: VersionedValue) -> None:
        with self._lock:
            if key not in self._store:
                self._store[key] = StoreEntry(key=key)
            self._store[key].add_version(versioned)

    def get_keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def compact(self, tombstone_age_seconds: float = 3600) -> int:
        """Remove old tombstones."""
        with self._lock:
            compacted = 0
            cutoff = time.time() - tombstone_age_seconds
            to_delete = []
            for key, entry in self._store.items():
                if (entry.latest and entry.latest.is_tombstone
                        and entry.latest.timestamp < cutoff):
                    to_delete.append(key)
            for key in to_delete:
                del self._store[key]
                compacted += 1
            return compacted

    @property
    def stats(self) -> dict:
        return {**self._stats, "keys": len(self._store)}


class Partitioner:
    def __init__(self, virtual_nodes: int = 100):
        self._virtual_nodes = virtual_nodes
        self._ring: list[int] = []
        self._node_map: dict[int, str] = {}
        self._nodes: list[str] = []
        self._lock = threading.Lock()

    def _hash(self, key: str) -> int:
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)

    def add_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.append(node_id)
            for i in range(self._virtual_nodes):
                h = self._hash(f"{node_id}:{i}")
                self._node_map[h] = node_id
                bisect.insort(self._ring, h)

    def remove_node(self, node_id: str) -> None:
        with self._lock:
            self._nodes.remove(node_id)
            for i in range(self._virtual_nodes):
                h = self._hash(f"{node_id}:{i}")
                del self._node_map[h]
                idx = bisect.bisect_left(self._ring, h)
                if idx < len(self._ring) and self._ring[idx] == h:
                    self._ring.pop(idx)

    def get_nodes(self, key: str, count: int) -> list[str]:
        if not self._ring:
            return []
        h = self._hash(key)
        idx = bisect.bisect_right(self._ring, h) % len(self._ring)

        result = []
        seen = set()
        checked = 0
        while len(result) < count and checked < len(self._ring):
            node_id = self._node_map[self._ring[(idx + checked) % len(self._ring)]]
            if node_id not in seen:
                result.append(node_id)
                seen.add(node_id)
            checked += 1
        return result


class ConflictResolver:
    @staticmethod
    def resolve_lww(entry: StoreEntry) -> VersionedValue:
        """Last-Write-Wins based on timestamp."""
        return max(entry.versions, key=lambda v: v.timestamp)

    @staticmethod
    def resolve_vector_clock(entry: StoreEntry) -> list[VersionedValue]:
        """Returns all concurrent versions for client-side resolution."""
        return entry.versions


class KVStore:
    def __init__(self, replication_factor: int = 3,
                 default_consistency: ConsistencyLevel = ConsistencyLevel.QUORUM):
        self._nodes: dict[str, StorageNode] = {}
        self._partitioner = Partitioner()
        self._replication_factor = replication_factor
        self._default_consistency = default_consistency
        self._conflict_resolver = ConflictResolver()

    def add_node(self, node: StorageNode) -> None:
        self._nodes[node.node_id] = node
        self._partitioner.add_node(node.node_id)

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._partitioner.remove_node(node_id)

    def _required_acks(self, consistency: ConsistencyLevel) -> int:
        alive = sum(1 for n in self._nodes.values() if n.is_alive)
        rf = min(self._replication_factor, alive)
        if consistency == ConsistencyLevel.ONE:
            return 1
        elif consistency == ConsistencyLevel.QUORUM:
            return (rf // 2) + 1
        else:
            return rf

    def get(self, key: str,
            consistency: ConsistencyLevel = None) -> Optional[Any]:
        consistency = consistency or self._default_consistency
        target_nodes = self._partitioner.get_nodes(key, self._replication_factor)
        required = self._required_acks(consistency)

        entries = []
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                entry = node.local_get(key)
                if entry:
                    entries.append(entry)

        if len(entries) < required:
            return None

        all_versions = []
        for entry in entries:
            all_versions.extend(entry.versions)

        if not all_versions:
            return None

        merged = StoreEntry(key=key, versions=all_versions)
        if merged.has_conflicts:
            resolved = self._conflict_resolver.resolve_lww(merged)
        else:
            resolved = merged.latest

        if resolved.is_tombstone:
            return None

        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                node.replicate(key, resolved)

        return resolved.value

    def put(self, key: str, value: Any,
            consistency: ConsistencyLevel = None) -> bool:
        consistency = consistency or self._default_consistency
        target_nodes = self._partitioner.get_nodes(key, self._replication_factor)
        required = self._required_acks(consistency)

        existing_clock = VectorClock()
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                entry = node.local_get(key)
                if entry and entry.latest:
                    existing_clock = existing_clock.merge(entry.latest.clock)

        acks = 0
        new_clock = None
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                new_clock = node.local_put(key, value, existing_clock)
                acks += 1

        if acks < required:
            return False

        if new_clock:
            versioned = VersionedValue(value=value, clock=new_clock)
            for node_id in target_nodes:
                node = self._nodes.get(node_id)
                if node and node.is_alive:
                    node.replicate(key, versioned)

        return True

    def delete(self, key: str,
               consistency: ConsistencyLevel = None) -> bool:
        consistency = consistency or self._default_consistency
        target_nodes = self._partitioner.get_nodes(key, self._replication_factor)
        required = self._required_acks(consistency)

        existing_clock = VectorClock()
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                entry = node.local_get(key)
                if entry and entry.latest:
                    existing_clock = existing_clock.merge(entry.latest.clock)

        acks = 0
        for node_id in target_nodes:
            node = self._nodes.get(node_id)
            if node and node.is_alive:
                node.local_delete(key, existing_clock)
                acks += 1

        return acks >= required

    def get_cluster_stats(self) -> dict:
        return {
            node_id: node.stats
            for node_id, node in self._nodes.items()
        }
```

### Concurrency Handling

- **Per-node RLock** serializes access to each node's local store — different keys on different nodes are fully concurrent
- **Vector clocks** provide causality tracking without global coordination — no distributed locks needed
- **Quorum reads/writes** ensure consistency without requiring all nodes to respond, tolerating minority failures
- **Read repair** during `get()` pushes the latest version to stale replicas, healing inconsistencies lazily

### Scalability Considerations

- **Consistent hashing** means adding a node only moves ~1/N of keys, not a full reshuffle
- **Tunable consistency**: ONE for fast reads (eventual), QUORUM for strong reads, ALL for strict consistency
- **Tombstone compaction** prevents unbounded growth from deletes — run periodically as background maintenance
- **Hinted handoff** (not shown): when a target node is down, a neighbor temporarily stores the write and forwards it when the target recovers
- **Anti-entropy**: Merkle tree comparison between replicas detects and repairs divergence

### Testing Approach

- **Basic CRUD**: PUT, GET, DELETE — verify correctness
- **Replication**: Write to key, verify it appears on all replica nodes
- **Node failure**: Take down a node, verify reads/writes still work with quorum
- **Conflict resolution**: Write different values to the same key from two nodes simultaneously, verify LWW resolves correctly
- **Vector clock ordering**: Verify causally related writes are ordered correctly
- **Compaction**: Delete keys, run compaction, verify tombstones are removed after the grace period

---

## 7. Incremental Compiler

### Detailed Requirements

- Implement a lexer that tokenizes source code into a stream of tokens
- Build a recursive descent parser that produces an Abstract Syntax Tree (AST)
- Support basic expressions: arithmetic, variables, functions, conditionals
- Track dependencies between source files/modules
- Implement incremental compilation: only recompile changed files and their dependents
- AST-based type checking with basic type inference
- Produce intermediate representation (IR) or bytecode output
- Provide meaningful error messages with source locations

### Architecture Overview

```
SourceFile ──tokenized by──▶ Lexer ──produces──▶ Token*
Token* ──parsed by──▶ Parser ──produces──▶ AST
AST ──checked by──▶ TypeChecker
AST ──compiled by──▶ CodeGenerator ──produces──▶ Bytecode
DependencyTracker ──determines──▶ which files need recompilation
IncrementalCache ──stores──▶ AST + types per file (keyed by content hash)
```

### Core Implementation

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional, Union
import hashlib
import re


class TokenType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS = auto()
    GREATER = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    ARROW = auto()
    SEMICOLON = auto()
    KW_LET = auto()
    KW_FN = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_RETURN = auto()
    KW_WHILE = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_IMPORT = auto()
    EOF = auto()
    NEWLINE = auto()


@dataclass
class SourceLocation:
    file: str
    line: int
    column: int

    def __str__(self):
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class Token:
    type: TokenType
    value: str
    location: SourceLocation


class LexerError(Exception):
    def __init__(self, message: str, location: SourceLocation):
        super().__init__(f"{location}: {message}")
        self.location = location


class Lexer:
    KEYWORDS = {
        "let": TokenType.KW_LET,
        "fn": TokenType.KW_FN,
        "if": TokenType.KW_IF,
        "else": TokenType.KW_ELSE,
        "return": TokenType.KW_RETURN,
        "while": TokenType.KW_WHILE,
        "true": TokenType.KW_TRUE,
        "false": TokenType.KW_FALSE,
        "import": TokenType.KW_IMPORT,
    }

    SYMBOLS = {
        '+': TokenType.PLUS, '-': TokenType.MINUS,
        '*': TokenType.STAR, '/': TokenType.SLASH,
        '(': TokenType.LPAREN, ')': TokenType.RPAREN,
        '{': TokenType.LBRACE, '}': TokenType.RBRACE,
        ',': TokenType.COMMA, ':': TokenType.COLON,
        ';': TokenType.SEMICOLON,
    }

    def __init__(self, source: str, filename: str = "<stdin>"):
        self._source = source
        self._filename = filename
        self._pos = 0
        self._line = 1
        self._column = 1

    def tokenize(self) -> list[Token]:
        tokens = []
        while self._pos < len(self._source):
            self._skip_whitespace()
            if self._pos >= len(self._source):
                break

            if self._source[self._pos] == '#':
                self._skip_comment()
                continue

            char = self._source[self._pos]
            loc = SourceLocation(self._filename, self._line, self._column)

            if char == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', loc))
                self._advance()
                continue

            if char == '=' and self._peek(1) == '=':
                tokens.append(Token(TokenType.EQUALS, '==', loc))
                self._advance(2)
            elif char == '!' and self._peek(1) == '=':
                tokens.append(Token(TokenType.NOT_EQUALS, '!=', loc))
                self._advance(2)
            elif char == '-' and self._peek(1) == '>':
                tokens.append(Token(TokenType.ARROW, '->', loc))
                self._advance(2)
            elif char == '=':
                tokens.append(Token(TokenType.ASSIGN, '=', loc))
                self._advance()
            elif char == '<':
                tokens.append(Token(TokenType.LESS, '<', loc))
                self._advance()
            elif char == '>':
                tokens.append(Token(TokenType.GREATER, '>', loc))
                self._advance()
            elif char in self.SYMBOLS:
                tokens.append(Token(self.SYMBOLS[char], char, loc))
                self._advance()
            elif char == '"':
                tokens.append(self._read_string(loc))
            elif char.isdigit():
                tokens.append(self._read_number(loc))
            elif char.isalpha() or char == '_':
                tokens.append(self._read_identifier(loc))
            else:
                raise LexerError(f"Unexpected character: '{char}'", loc)

        tokens.append(Token(TokenType.EOF, "",
                           SourceLocation(self._filename, self._line, self._column)))
        return tokens

    def _advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self._pos < len(self._source):
                if self._source[self._pos] == '\n':
                    self._line += 1
                    self._column = 1
                else:
                    self._column += 1
                self._pos += 1

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._source[idx] if idx < len(self._source) else ''

    def _skip_whitespace(self) -> None:
        while self._pos < len(self._source) and self._source[self._pos] in (' ', '\t', '\r'):
            self._advance()

    def _skip_comment(self) -> None:
        while self._pos < len(self._source) and self._source[self._pos] != '\n':
            self._advance()

    def _read_string(self, loc: SourceLocation) -> Token:
        self._advance()  # skip opening quote
        chars = []
        while self._pos < len(self._source) and self._source[self._pos] != '"':
            if self._source[self._pos] == '\\':
                self._advance()
                escape_map = {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}
                chars.append(escape_map.get(self._source[self._pos], self._source[self._pos]))
            else:
                chars.append(self._source[self._pos])
            self._advance()
        self._advance()  # skip closing quote
        return Token(TokenType.STRING, ''.join(chars), loc)

    def _read_number(self, loc: SourceLocation) -> Token:
        start = self._pos
        is_float = False
        while self._pos < len(self._source) and (self._source[self._pos].isdigit() or self._source[self._pos] == '.'):
            if self._source[self._pos] == '.':
                is_float = True
            self._advance()
        value = self._source[start:self._pos]
        return Token(TokenType.FLOAT if is_float else TokenType.INTEGER, value, loc)

    def _read_identifier(self, loc: SourceLocation) -> Token:
        start = self._pos
        while self._pos < len(self._source) and (self._source[self._pos].isalnum() or self._source[self._pos] == '_'):
            self._advance()
        word = self._source[start:self._pos]
        token_type = self.KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word, loc)


# === AST Nodes ===

class ASTNode(ABC):
    location: SourceLocation = None


@dataclass
class NumberLiteral(ASTNode):
    value: float
    location: SourceLocation = None


@dataclass
class StringLiteral(ASTNode):
    value: str
    location: SourceLocation = None


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    location: SourceLocation = None


@dataclass
class Identifier(ASTNode):
    name: str
    location: SourceLocation = None


@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode = None
    right: ASTNode = None
    location: SourceLocation = None


@dataclass
class LetStatement(ASTNode):
    name: str = ""
    type_annotation: Optional[str] = None
    value: ASTNode = None
    location: SourceLocation = None


@dataclass
class FunctionDef(ASTNode):
    name: str = ""
    params: list[tuple[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    body: list[ASTNode] = field(default_factory=list)
    location: SourceLocation = None


@dataclass
class FunctionCall(ASTNode):
    name: str = ""
    arguments: list[ASTNode] = field(default_factory=list)
    location: SourceLocation = None


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode = None
    then_body: list[ASTNode] = field(default_factory=list)
    else_body: list[ASTNode] = field(default_factory=list)
    location: SourceLocation = None


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode] = None
    location: SourceLocation = None


@dataclass
class ImportStatement(ASTNode):
    module_name: str = ""
    location: SourceLocation = None


@dataclass
class Program(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    location: SourceLocation = None


class ParseError(Exception):
    def __init__(self, message: str, location: SourceLocation):
        super().__init__(f"{location}: {message}")
        self.location = location


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self._pos = 0

    def parse(self) -> Program:
        statements = []
        imports = []
        while not self._at_end():
            if self._check(TokenType.KW_IMPORT):
                imp = self._parse_import()
                imports.append(imp.module_name)
                statements.append(imp)
            elif self._check(TokenType.KW_FN):
                statements.append(self._parse_function())
            elif self._check(TokenType.KW_LET):
                statements.append(self._parse_let())
            else:
                statements.append(self._parse_expression_statement())
        return Program(statements=statements, imports=imports)

    def _parse_import(self) -> ImportStatement:
        loc = self._consume(TokenType.KW_IMPORT).location
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume_optional(TokenType.SEMICOLON)
        return ImportStatement(module_name=name, location=loc)

    def _parse_function(self) -> FunctionDef:
        loc = self._consume(TokenType.KW_FN).location
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LPAREN)

        params = []
        while not self._check(TokenType.RPAREN):
            pname = self._consume(TokenType.IDENTIFIER).value
            self._consume(TokenType.COLON)
            ptype = self._consume(TokenType.IDENTIFIER).value
            params.append((pname, ptype))
            if not self._check(TokenType.RPAREN):
                self._consume(TokenType.COMMA)
        self._consume(TokenType.RPAREN)

        return_type = None
        if self._check(TokenType.ARROW):
            self._advance()
            return_type = self._consume(TokenType.IDENTIFIER).value

        body = self._parse_block()
        return FunctionDef(name=name, params=params,
                           return_type=return_type, body=body,
                           location=loc)

    def _parse_let(self) -> LetStatement:
        loc = self._consume(TokenType.KW_LET).location
        name = self._consume(TokenType.IDENTIFIER).value

        type_ann = None
        if self._check(TokenType.COLON):
            self._advance()
            type_ann = self._consume(TokenType.IDENTIFIER).value

        self._consume(TokenType.ASSIGN)
        value = self._parse_expression()
        self._consume_optional(TokenType.SEMICOLON)
        return LetStatement(name=name, type_annotation=type_ann,
                            value=value, location=loc)

    def _parse_block(self) -> list[ASTNode]:
        self._consume(TokenType.LBRACE)
        statements = []
        while not self._check(TokenType.RBRACE):
            if self._check(TokenType.KW_LET):
                statements.append(self._parse_let())
            elif self._check(TokenType.KW_IF):
                statements.append(self._parse_if())
            elif self._check(TokenType.KW_RETURN):
                statements.append(self._parse_return())
            else:
                statements.append(self._parse_expression_statement())
        self._consume(TokenType.RBRACE)
        return statements

    def _parse_if(self) -> IfStatement:
        loc = self._consume(TokenType.KW_IF).location
        condition = self._parse_expression()
        then_body = self._parse_block()
        else_body = []
        if self._check(TokenType.KW_ELSE):
            self._advance()
            else_body = self._parse_block()
        return IfStatement(condition=condition, then_body=then_body,
                           else_body=else_body, location=loc)

    def _parse_return(self) -> ReturnStatement:
        loc = self._consume(TokenType.KW_RETURN).location
        value = None
        if not self._check(TokenType.SEMICOLON) and not self._check(TokenType.RBRACE):
            value = self._parse_expression()
        self._consume_optional(TokenType.SEMICOLON)
        return ReturnStatement(value=value, location=loc)

    def _parse_expression_statement(self) -> ASTNode:
        expr = self._parse_expression()
        self._consume_optional(TokenType.SEMICOLON)
        return expr

    def _parse_expression(self) -> ASTNode:
        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_additive()
        while self._check_any(TokenType.EQUALS, TokenType.NOT_EQUALS,
                              TokenType.LESS, TokenType.GREATER):
            op = self._advance()
            right = self._parse_additive()
            left = BinaryOp(op=op.value, left=left, right=right,
                            location=op.location)
        return left

    def _parse_additive(self) -> ASTNode:
        left = self._parse_multiplicative()
        while self._check_any(TokenType.PLUS, TokenType.MINUS):
            op = self._advance()
            right = self._parse_multiplicative()
            left = BinaryOp(op=op.value, left=left, right=right,
                            location=op.location)
        return left

    def _parse_multiplicative(self) -> ASTNode:
        left = self._parse_primary()
        while self._check_any(TokenType.STAR, TokenType.SLASH):
            op = self._advance()
            right = self._parse_primary()
            left = BinaryOp(op=op.value, left=left, right=right,
                            location=op.location)
        return left

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        if tok.type in (TokenType.INTEGER, TokenType.FLOAT):
            self._advance()
            return NumberLiteral(value=float(tok.value), location=tok.location)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(value=tok.value, location=tok.location)

        if tok.type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
            self._advance()
            return BoolLiteral(value=tok.type == TokenType.KW_TRUE,
                               location=tok.location)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            if self._check(TokenType.LPAREN):
                return self._parse_call(tok)
            return Identifier(name=tok.value, location=tok.location)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN)
            return expr

        raise ParseError(f"Unexpected token: {tok.value}", tok.location)

    def _parse_call(self, name_tok: Token) -> FunctionCall:
        self._consume(TokenType.LPAREN)
        args = []
        while not self._check(TokenType.RPAREN):
            args.append(self._parse_expression())
            if not self._check(TokenType.RPAREN):
                self._consume(TokenType.COMMA)
        self._consume(TokenType.RPAREN)
        return FunctionCall(name=name_tok.value, arguments=args,
                            location=name_tok.location)

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _check(self, tt: TokenType) -> bool:
        return not self._at_end() and self._tokens[self._pos].type == tt

    def _check_any(self, *types: TokenType) -> bool:
        return not self._at_end() and self._tokens[self._pos].type in types

    def _consume(self, tt: TokenType) -> Token:
        if self._check(tt):
            return self._advance()
        loc = self._tokens[self._pos].location if not self._at_end() else SourceLocation("<eof>", 0, 0)
        raise ParseError(f"Expected {tt.name}, got {self._tokens[self._pos].type.name}", loc)

    def _consume_optional(self, tt: TokenType) -> Optional[Token]:
        if self._check(tt):
            return self._advance()
        return None

    def _at_end(self) -> bool:
        return self._pos >= len(self._tokens) or self._tokens[self._pos].type == TokenType.EOF


# === Incremental Compilation ===

@dataclass
class CompilationUnit:
    filename: str
    source_hash: str
    ast: Optional[Program] = None
    dependencies: list[str] = field(default_factory=list)
    compiled_at: float = 0


class IncrementalCompiler:
    def __init__(self):
        self._cache: dict[str, CompilationUnit] = {}
        self._dependency_graph: dict[str, set[str]] = {}

    def compile(self, filename: str, source: str) -> Program:
        source_hash = hashlib.sha256(source.encode()).hexdigest()

        cached = self._cache.get(filename)
        if cached and cached.source_hash == source_hash:
            return cached.ast

        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        unit = CompilationUnit(
            filename=filename,
            source_hash=source_hash,
            ast=ast,
            dependencies=ast.imports,
        )
        self._cache[filename] = unit

        self._dependency_graph[filename] = set(ast.imports)

        return ast

    def get_files_to_recompile(self, changed_file: str) -> list[str]:
        """Returns all files that need recompilation when changed_file is modified."""
        affected = set()
        queue = [changed_file]
        while queue:
            current = queue.pop(0)
            if current in affected:
                continue
            affected.add(current)

            for file, deps in self._dependency_graph.items():
                if current in deps and file not in affected:
                    queue.append(file)

        return sorted(affected)

    def invalidate(self, filename: str) -> list[str]:
        """Invalidate cache for a file and its dependents."""
        to_recompile = self.get_files_to_recompile(filename)
        for f in to_recompile:
            self._cache.pop(f, None)
        return to_recompile
```

### Concurrency Handling

- The lexer and parser are inherently single-threaded per file — no shared state
- **Incremental compilation** allows parallel compilation of independent files (no mutual dependencies)
- The **dependency graph** must be locked if multiple files are being compiled concurrently and share dependencies
- **Cache invalidation** can trigger cascading recompilation — topological ordering ensures correct rebuild order

### Scalability Considerations

- Content-addressed caching (by source hash) avoids recompilation of unchanged files
- Dependency graph enables minimal rebuilds — only recompile files transitively affected by a change
- For large codebases, persist the cache to disk for cross-session incremental builds
- Parallel compilation of independent modules provides linear speedup

### Testing Approach

- **Lexer**: Tokenize various inputs (numbers, strings, operators, keywords) and verify token sequences
- **Parser**: Parse expressions like `1 + 2 * 3` and verify AST structure respects precedence
- **Error recovery**: Invalid syntax produces meaningful error messages with correct source locations
- **Incremental**: Compile file A, modify file B (that A imports), verify A is marked for recompilation
- **Cache hit**: Compile same source twice, verify second call returns cached AST
- **Edge cases**: Empty files, deeply nested expressions, unicode identifiers

---

## 8. LeetCode Judge Service

### Detailed Requirements

- Accept user-submitted code in multiple languages (Python, Java, C++)
- Execute code against predefined test cases with expected outputs
- Enforce time limits (per test case) and memory limits
- Sandbox execution to prevent malicious code (file access, network, system calls)
- Support custom test cases submitted by the user
- Return detailed results: pass/fail per test case, runtime, memory usage
- Support different problem types: return value, stdout comparison, special judge
- Queue submissions and process them fairly

### Architecture Overview

```
Submission ──queued in──▶ SubmissionQueue
JudgeWorker ──dequeues──▶ Submission
JudgeWorker ──creates──▶ Sandbox ──executes──▶ UserCode
Sandbox ──monitors──▶ Time, Memory limits
TestRunner ──compares──▶ actual vs expected output
Problem ──defines──▶ TestCase*, limits, judge type
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Callable
import threading
import subprocess
import tempfile
import os
import time
import uuid
import queue
import shutil
import signal
import resource


class Language(Enum):
    PYTHON = "python"
    JAVA = "java"
    CPP = "cpp"


class Verdict(Enum):
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILATION_ERROR = "Compilation Error"
    PENDING = "Pending"
    JUDGING = "Judging"


@dataclass
class TestCase:
    test_id: int
    input_data: str
    expected_output: str
    is_sample: bool = False


@dataclass
class TestResult:
    test_id: int
    verdict: Verdict
    actual_output: str = ""
    expected_output: str = ""
    runtime_ms: float = 0
    memory_kb: int = 0
    error_message: str = ""


@dataclass
class Problem:
    problem_id: str
    title: str
    test_cases: list[TestCase] = field(default_factory=list)
    time_limit_ms: int = 2000
    memory_limit_kb: int = 256 * 1024
    judge_type: str = "exact"  # exact, special, float_tolerance

    def add_test_case(self, input_data: str, expected: str,
                       is_sample: bool = False) -> None:
        tc = TestCase(
            test_id=len(self.test_cases) + 1,
            input_data=input_data,
            expected_output=expected,
            is_sample=is_sample,
        )
        self.test_cases.append(tc)


@dataclass
class Submission:
    submission_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    problem_id: str = ""
    language: Language = Language.PYTHON
    source_code: str = ""
    verdict: Verdict = Verdict.PENDING
    test_results: list[TestResult] = field(default_factory=list)
    total_runtime_ms: float = 0
    max_memory_kb: int = 0
    submitted_at: datetime = field(default_factory=datetime.now)
    judged_at: Optional[datetime] = None


class JudgeStrategy(ABC):
    @abstractmethod
    def compare(self, actual: str, expected: str) -> bool:
        pass


class ExactJudge(JudgeStrategy):
    def compare(self, actual: str, expected: str) -> bool:
        return actual.strip() == expected.strip()


class TokenJudge(JudgeStrategy):
    """Compares output token by token, ignoring whitespace differences."""

    def compare(self, actual: str, expected: str) -> bool:
        return actual.split() == expected.split()


class FloatToleranceJudge(JudgeStrategy):
    def __init__(self, tolerance: float = 1e-6):
        self._tolerance = tolerance

    def compare(self, actual: str, expected: str) -> bool:
        try:
            actual_vals = [float(x) for x in actual.split()]
            expected_vals = [float(x) for x in expected.split()]
            if len(actual_vals) != len(expected_vals):
                return False
            return all(
                abs(a - e) <= self._tolerance
                for a, e in zip(actual_vals, expected_vals)
            )
        except ValueError:
            return False


class LanguageRunner(ABC):
    @abstractmethod
    def get_compile_command(self, source_file: str,
                             output_file: str) -> Optional[list[str]]:
        pass

    @abstractmethod
    def get_run_command(self, executable: str) -> list[str]:
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        pass


class PythonRunner(LanguageRunner):
    def get_compile_command(self, source_file: str,
                             output_file: str) -> Optional[list[str]]:
        return None  # interpreted

    def get_run_command(self, executable: str) -> list[str]:
        return ["python3", executable]

    def get_file_extension(self) -> str:
        return ".py"


class CppRunner(LanguageRunner):
    def get_compile_command(self, source_file: str,
                             output_file: str) -> Optional[list[str]]:
        return ["g++", "-O2", "-std=c++17", "-o", output_file, source_file]

    def get_run_command(self, executable: str) -> list[str]:
        return [executable]

    def get_file_extension(self) -> str:
        return ".cpp"


class JavaRunner(LanguageRunner):
    def get_compile_command(self, source_file: str,
                             output_file: str) -> Optional[list[str]]:
        return ["javac", source_file]

    def get_run_command(self, executable: str) -> list[str]:
        dir_name = os.path.dirname(executable)
        class_name = os.path.basename(executable).replace(".java", "")
        return ["java", "-cp", dir_name, class_name]

    def get_file_extension(self) -> str:
        return ".java"


class Sandbox:
    RUNNERS: dict[Language, LanguageRunner] = {
        Language.PYTHON: PythonRunner(),
        Language.CPP: CppRunner(),
        Language.JAVA: JavaRunner(),
    }

    def __init__(self, time_limit_ms: int, memory_limit_kb: int):
        self._time_limit = time_limit_ms / 1000.0
        self._memory_limit = memory_limit_kb * 1024

    def execute(self, language: Language, source_code: str,
                input_data: str) -> tuple[str, float, int, str]:
        """Returns (stdout, runtime_ms, memory_kb, error)."""
        runner = self.RUNNERS[language]
        work_dir = tempfile.mkdtemp(prefix="judge_")

        try:
            ext = runner.get_file_extension()
            source_file = os.path.join(work_dir, f"solution{ext}")
            with open(source_file, 'w') as f:
                f.write(source_code)

            compile_cmd = runner.get_compile_command(
                source_file, os.path.join(work_dir, "solution")
            )
            if compile_cmd:
                result = subprocess.run(
                    compile_cmd, capture_output=True, text=True,
                    timeout=30, cwd=work_dir
                )
                if result.returncode != 0:
                    return "", 0, 0, f"Compilation Error:\n{result.stderr}"

            executable = (os.path.join(work_dir, "solution")
                          if compile_cmd else source_file)
            run_cmd = runner.get_run_command(executable)

            start_time = time.monotonic()
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self._time_limit,
                    cwd=work_dir,
                )
                elapsed_ms = (time.monotonic() - start_time) * 1000

                if proc.returncode != 0:
                    return "", elapsed_ms, 0, f"Runtime Error:\n{proc.stderr}"

                return proc.stdout, elapsed_ms, 0, ""

            except subprocess.TimeoutExpired:
                elapsed_ms = (time.monotonic() - start_time) * 1000
                return "", elapsed_ms, 0, "Time Limit Exceeded"

        finally:
            shutil.rmtree(work_dir, ignore_errors=True)


class JudgeWorker:
    def __init__(self, worker_id: int, submission_queue: queue.Queue,
                 problems: dict[str, Problem],
                 on_complete: Callable[[Submission], None]):
        self._worker_id = worker_id
        self._queue = submission_queue
        self._problems = problems
        self._on_complete = on_complete
        self._running = True
        self._judges: dict[str, JudgeStrategy] = {
            "exact": ExactJudge(),
            "token": TokenJudge(),
            "float_tolerance": FloatToleranceJudge(),
        }
        self._thread = threading.Thread(
            target=self._run, daemon=True,
            name=f"JudgeWorker-{worker_id}"
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        while self._running:
            try:
                submission = self._queue.get(timeout=1.0)
                self._judge(submission)
                self._on_complete(submission)
            except queue.Empty:
                continue

    def _judge(self, submission: Submission) -> None:
        submission.verdict = Verdict.JUDGING
        problem = self._problems.get(submission.problem_id)
        if not problem:
            submission.verdict = Verdict.RUNTIME_ERROR
            return

        sandbox = Sandbox(problem.time_limit_ms, problem.memory_limit_kb)
        judge = self._judges.get(problem.judge_type, ExactJudge())

        all_passed = True
        for tc in problem.test_cases:
            stdout, runtime, memory, error = sandbox.execute(
                submission.language, submission.source_code, tc.input_data
            )

            result = TestResult(
                test_id=tc.test_id,
                expected_output=tc.expected_output,
                actual_output=stdout,
                runtime_ms=runtime,
                memory_kb=memory,
            )

            if error:
                if "Time Limit" in error:
                    result.verdict = Verdict.TIME_LIMIT_EXCEEDED
                elif "Compilation" in error:
                    result.verdict = Verdict.COMPILATION_ERROR
                else:
                    result.verdict = Verdict.RUNTIME_ERROR
                result.error_message = error
                all_passed = False
            elif judge.compare(stdout, tc.expected_output):
                result.verdict = Verdict.ACCEPTED
            else:
                result.verdict = Verdict.WRONG_ANSWER
                all_passed = False

            submission.test_results.append(result)
            submission.total_runtime_ms += runtime
            submission.max_memory_kb = max(submission.max_memory_kb, memory)

            if not all_passed and not tc.is_sample:
                break

        submission.verdict = Verdict.ACCEPTED if all_passed else submission.test_results[-1].verdict
        submission.judged_at = datetime.now()


class JudgeService:
    def __init__(self, num_workers: int = 4):
        self._problems: dict[str, Problem] = {}
        self._submissions: dict[str, Submission] = {}
        self._queue: queue.Queue = queue.Queue(maxsize=1000)
        self._workers: list[JudgeWorker] = []
        self._lock = threading.Lock()

        for i in range(num_workers):
            worker = JudgeWorker(i, self._queue, self._problems,
                                 self._on_submission_complete)
            self._workers.append(worker)
            worker.start()

    def add_problem(self, problem: Problem) -> None:
        self._problems[problem.problem_id] = problem

    def submit(self, user_id: str, problem_id: str,
               language: Language, source_code: str) -> Submission:
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            language=language,
            source_code=source_code,
        )
        with self._lock:
            self._submissions[submission.submission_id] = submission
        self._queue.put(submission)
        return submission

    def get_submission(self, submission_id: str) -> Optional[Submission]:
        return self._submissions.get(submission_id)

    def _on_submission_complete(self, submission: Submission) -> None:
        pass

    def shutdown(self) -> None:
        for worker in self._workers:
            worker.stop()
```

### Concurrency Handling

- **Thread-safe submission queue** decouples submission from judging — multiple users can submit simultaneously
- **Worker pool** judges submissions concurrently — each worker handles one submission at a time
- **Sandbox isolation** via subprocess — user code runs in a separate process with resource limits, preventing interference
- **Timeout enforcement** via `subprocess.timeout` — prevents infinite loops from blocking workers indefinitely

### Scalability Considerations

- Scale horizontally by adding more judge workers (each is independent)
- Use containers (Docker) for stronger sandbox isolation in production
- Rate limit submissions per user to prevent abuse
- Cache compilation results for the same source code to avoid redundant work
- Implement a priority queue: contest submissions get higher priority than practice

### Testing Approach

- **Correct solution**: Submit a valid solution, verify all test cases pass
- **Wrong answer**: Submit incorrect solution, verify WA verdict
- **TLE**: Submit infinite loop, verify TLE verdict within reasonable time
- **Compilation error**: Submit invalid syntax, verify CE verdict
- **Multiple languages**: Test same problem with Python, C++, Java
- **Concurrent submissions**: Submit 50 solutions simultaneously, verify all are judged correctly

---

## 9. Code Runner Service

### Detailed Requirements

- Execute code snippets in multiple programming languages
- Use containerized execution for isolation and reproducibility
- Queue-based processing with configurable worker count
- Capture stdout, stderr, and exit code
- Enforce time and memory limits per execution
- Support stdin input for interactive programs
- Return structured results with execution metadata
- Handle concurrent execution requests from multiple users

### Architecture Overview

```
Client ──submits──▶ CodeRunnerService ──queues──▶ ExecutionQueue
ExecutionWorker ──dequeues──▶ ExecutionRequest
ExecutionWorker ──creates──▶ ContainerSandbox ──runs──▶ Code
ContainerSandbox ──returns──▶ ExecutionResult
LanguageConfig defines per-language settings (image, command, limits)
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import threading
import queue
import subprocess
import tempfile
import shutil
import os
import time
import uuid


class ExecutionStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class LanguageConfig:
    name: str
    extension: str
    compile_command: Optional[str] = None  # None for interpreted
    run_command: str = ""
    default_timeout_seconds: float = 10.0
    default_memory_mb: int = 128


@dataclass
class ExecutionRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    language: str = "python"
    source_code: str = ""
    stdin_input: str = ""
    timeout_seconds: float = 10.0
    memory_limit_mb: int = 128
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    request_id: str = ""
    status: ExecutionStatus = ExecutionStatus.QUEUED
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    runtime_ms: float = 0
    memory_used_kb: int = 0
    error_message: str = ""
    completed_at: Optional[datetime] = None


class ExecutionSandbox:
    """Process-based sandbox for code execution."""

    def __init__(self, language_config: LanguageConfig):
        self._config = language_config

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        result = ExecutionResult(request_id=request.request_id)
        work_dir = tempfile.mkdtemp(prefix="runner_")

        try:
            source_file = os.path.join(
                work_dir, f"code{self._config.extension}"
            )
            with open(source_file, 'w') as f:
                f.write(request.source_code)

            if self._config.compile_command:
                compile_cmd = self._config.compile_command.format(
                    source=source_file,
                    output=os.path.join(work_dir, "code_out")
                )
                comp = subprocess.run(
                    compile_cmd.split(), capture_output=True,
                    text=True, timeout=30, cwd=work_dir
                )
                if comp.returncode != 0:
                    result.status = ExecutionStatus.FAILED
                    result.stderr = comp.stderr
                    result.error_message = "Compilation failed"
                    return result
                executable = os.path.join(work_dir, "code_out")
            else:
                executable = source_file

            run_cmd = self._config.run_command.format(
                executable=executable
            )

            start = time.monotonic()
            try:
                proc = subprocess.run(
                    run_cmd.split(),
                    input=request.stdin_input,
                    capture_output=True,
                    text=True,
                    timeout=request.timeout_seconds,
                    cwd=work_dir,
                )
                elapsed = (time.monotonic() - start) * 1000

                result.stdout = proc.stdout
                result.stderr = proc.stderr
                result.exit_code = proc.returncode
                result.runtime_ms = elapsed
                result.status = (ExecutionStatus.COMPLETED
                                 if proc.returncode == 0
                                 else ExecutionStatus.FAILED)

            except subprocess.TimeoutExpired:
                elapsed = (time.monotonic() - start) * 1000
                result.status = ExecutionStatus.TIMEOUT
                result.runtime_ms = elapsed
                result.error_message = (
                    f"Execution exceeded {request.timeout_seconds}s limit"
                )

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)

        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            result.completed_at = datetime.now()

        return result


class ExecutionWorker:
    def __init__(self, worker_id: int,
                 task_queue: queue.Queue,
                 language_configs: dict[str, LanguageConfig],
                 result_store: dict[str, ExecutionResult]):
        self._worker_id = worker_id
        self._queue = task_queue
        self._configs = language_configs
        self._results = result_store
        self._running = True
        self._thread = threading.Thread(
            target=self._run, daemon=True,
            name=f"RunnerWorker-{worker_id}"
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        while self._running:
            try:
                request = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            config = self._configs.get(request.language)
            if not config:
                result = ExecutionResult(
                    request_id=request.request_id,
                    status=ExecutionStatus.FAILED,
                    error_message=f"Unsupported language: {request.language}",
                )
            else:
                sandbox = ExecutionSandbox(config)
                result = sandbox.execute(request)

            self._results[request.request_id] = result


class CodeRunnerService:
    DEFAULT_CONFIGS = {
        "python": LanguageConfig(
            name="Python 3",
            extension=".py",
            run_command="python3 {executable}",
            default_timeout_seconds=10.0,
        ),
        "javascript": LanguageConfig(
            name="Node.js",
            extension=".js",
            run_command="node {executable}",
            default_timeout_seconds=10.0,
        ),
        "cpp": LanguageConfig(
            name="C++ 17",
            extension=".cpp",
            compile_command="g++ -O2 -std=c++17 -o {output} {source}",
            run_command="{executable}",
            default_timeout_seconds=5.0,
        ),
        "java": LanguageConfig(
            name="Java 17",
            extension=".java",
            compile_command="javac {source}",
            run_command="java -cp {executable} Main",
            default_timeout_seconds=10.0,
        ),
        "go": LanguageConfig(
            name="Go",
            extension=".go",
            run_command="go run {executable}",
            default_timeout_seconds=10.0,
        ),
    }

    def __init__(self, num_workers: int = 4,
                 max_queue_size: int = 500):
        self._configs = dict(self.DEFAULT_CONFIGS)
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._results: dict[str, ExecutionResult] = {}
        self._workers: list[ExecutionWorker] = []
        self._lock = threading.Lock()

        for i in range(num_workers):
            worker = ExecutionWorker(
                i, self._queue, self._configs, self._results
            )
            self._workers.append(worker)
            worker.start()

    def submit(self, request: ExecutionRequest) -> str:
        if request.language not in self._configs:
            raise ValueError(f"Unsupported language: {request.language}")

        try:
            self._queue.put(request, timeout=5.0)
        except queue.Full:
            raise RuntimeError("Execution queue is full, try again later")

        return request.request_id

    def get_result(self, request_id: str) -> Optional[ExecutionResult]:
        return self._results.get(request_id)

    def wait_for_result(self, request_id: str,
                         timeout: float = 30.0) -> Optional[ExecutionResult]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self._results.get(request_id)
            if result and result.status != ExecutionStatus.QUEUED:
                return result
            time.sleep(0.1)
        return None

    def get_queue_stats(self) -> dict:
        return {
            "queue_size": self._queue.qsize(),
            "completed": len(self._results),
            "workers": len(self._workers),
        }

    def add_language(self, lang_id: str, config: LanguageConfig) -> None:
        self._configs[lang_id] = config

    def shutdown(self) -> None:
        for worker in self._workers:
            worker.stop()
```

### Concurrency Handling

- **Bounded queue** with timeout prevents OOM from unbounded submission — callers get immediate feedback when the queue is full
- **Worker threads** are independent — each creates its own sandbox and temp directory
- **Result store** (dict) is thread-safe for simple reads in CPython (GIL), but would need explicit locking for non-CPython implementations
- **Subprocess isolation** — user code runs in a separate process, so a crash doesn't affect the worker

### Scalability Considerations

- Replace subprocess with Docker containers for stronger isolation and reproducible environments
- Use a persistent message queue (Redis, RabbitMQ) for cross-machine job distribution
- Implement resource quotas per user (max concurrent executions, daily execution limit)
- Pre-warm containers for popular languages to reduce cold-start latency
- Consider serverless execution (AWS Lambda, GCP Cloud Run) for elastic scaling

### Testing Approach

- **Hello World**: Run a simple print statement in each supported language
- **Stdin handling**: Pass input, verify code reads and processes it correctly
- **Timeout**: Submit an infinite loop, verify it's killed within the time limit
- **Compilation error**: Submit invalid C++ code, verify error message is returned
- **Concurrent execution**: Submit 20 requests simultaneously, verify all complete
- **Queue overflow**: Fill the queue, submit more, verify proper error handling

---

## 10. Trading Platform

### Detailed Requirements

- Support multiple asset types (stocks, options, crypto)
- Real-time order book with bid/ask price levels
- Price-time priority matching with partial fills
- Market, Limit, Stop, and Stop-Limit order types
- Portfolio management with real-time P&L calculation
- Risk checks before order placement (position limits, buying power)
- Trade history and execution reports
- Real-time market data feed to subscribers

### Architecture Overview

```
Trader ──places──▶ Order ──validated by──▶ RiskEngine
Order ──routed to──▶ OrderBook (per symbol)
OrderBook ──matches──▶ Buy/Sell orders ──produces──▶ Trade
MarketDataFeed ──publishes──▶ price updates to Subscriber*
Portfolio ──tracks──▶ positions, P&L, buying power
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable
import threading
import heapq
import uuid
from collections import defaultdict


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TimeInForce(Enum):
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    DAY = "DAY"


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    trader_id: str = ""
    symbol: str = ""
    side: Side = Side.BUY
    order_type: OrderType = OrderType.LIMIT
    price: float = 0.0
    stop_price: float = 0.0
    quantity: int = 0
    filled_quantity: int = 0
    time_in_force: TimeInForce = TimeInForce.GTC
    status: OrderStatus = OrderStatus.NEW
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def remaining(self) -> int:
        return self.quantity - self.filled_quantity

    def fill(self, qty: int) -> None:
        self.filled_quantity += qty
        self.status = (OrderStatus.FILLED
                       if self.filled_quantity >= self.quantity
                       else OrderStatus.PARTIALLY_FILLED)


@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    buy_order_id: str = ""
    sell_order_id: str = ""
    price: float = 0.0
    quantity: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PriceLevel:
    price: float
    orders: list[Order] = field(default_factory=list)

    @property
    def total_quantity(self) -> int:
        return sum(o.remaining for o in self.orders if o.status not in
                   (OrderStatus.FILLED, OrderStatus.CANCELLED))


class MarketDataSubscriber(ABC):
    @abstractmethod
    def on_trade(self, trade: Trade) -> None:
        pass

    @abstractmethod
    def on_book_update(self, symbol: str, bids: list[PriceLevel],
                        asks: list[PriceLevel]) -> None:
        pass


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self._bids: list[tuple[float, int, Order]] = []  # max-heap (neg price)
        self._asks: list[tuple[float, int, Order]] = []  # min-heap
        self._order_counter = 0
        self._lock = threading.Lock()
        self._subscribers: list[MarketDataSubscriber] = []
        self._stop_orders: list[Order] = []
        self.last_trade_price: float = 0.0

    def add_subscriber(self, sub: MarketDataSubscriber) -> None:
        self._subscribers.append(sub)

    def submit_order(self, order: Order) -> list[Trade]:
        with self._lock:
            if order.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
                self._stop_orders.append(order)
                return []

            trades = self._match(order)

            if order.time_in_force == TimeInForce.IOC:
                if order.remaining > 0:
                    order.status = OrderStatus.CANCELLED
            elif order.time_in_force == TimeInForce.FOK:
                if order.filled_quantity == 0:
                    order.status = OrderStatus.CANCELLED
                    return []
            elif order.remaining > 0 and order.order_type == OrderType.LIMIT:
                self._insert(order)

            if trades:
                self._check_stop_orders(trades[-1].price)

            self._notify_book_update()
            return trades

    def cancel_order(self, order_id: str) -> bool:
        with self._lock:
            for heap in (self._bids, self._asks):
                for _, _, order in heap:
                    if order.order_id == order_id:
                        if order.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                            order.status = OrderStatus.CANCELLED
                            return True
            return False

    def _match(self, incoming: Order) -> list[Trade]:
        trades = []
        if incoming.side == Side.BUY:
            while incoming.remaining > 0 and self._asks:
                best_price, _, best_order = self._asks[0]
                if best_order.status == OrderStatus.CANCELLED:
                    heapq.heappop(self._asks)
                    continue
                if (incoming.order_type == OrderType.LIMIT
                        and best_price > incoming.price):
                    break
                trade = self._execute_trade(incoming, best_order, best_price)
                trades.append(trade)
                if best_order.remaining == 0:
                    heapq.heappop(self._asks)
        else:
            while incoming.remaining > 0 and self._bids:
                neg_price, _, best_order = self._bids[0]
                best_price = -neg_price
                if best_order.status == OrderStatus.CANCELLED:
                    heapq.heappop(self._bids)
                    continue
                if (incoming.order_type == OrderType.LIMIT
                        and best_price < incoming.price):
                    break
                trade = self._execute_trade(best_order, incoming, best_price)
                trades.append(trade)
                if best_order.remaining == 0:
                    heapq.heappop(self._bids)

        return trades

    def _execute_trade(self, buy: Order, sell: Order,
                        price: float) -> Trade:
        qty = min(buy.remaining, sell.remaining)
        buy.fill(qty)
        sell.fill(qty)
        self.last_trade_price = price

        trade = Trade(
            symbol=self.symbol,
            buy_order_id=buy.order_id,
            sell_order_id=sell.order_id,
            price=price,
            quantity=qty,
        )

        for sub in self._subscribers:
            sub.on_trade(trade)

        return trade

    def _insert(self, order: Order) -> None:
        self._order_counter += 1
        if order.side == Side.BUY:
            heapq.heappush(self._bids,
                           (-order.price, self._order_counter, order))
        else:
            heapq.heappush(self._asks,
                           (order.price, self._order_counter, order))

    def _check_stop_orders(self, last_price: float) -> None:
        triggered = []
        remaining = []
        for stop_order in self._stop_orders:
            if (stop_order.side == Side.BUY and last_price >= stop_order.stop_price) or \
               (stop_order.side == Side.SELL and last_price <= stop_order.stop_price):
                if stop_order.order_type == OrderType.STOP:
                    stop_order.order_type = OrderType.MARKET
                else:
                    stop_order.order_type = OrderType.LIMIT
                triggered.append(stop_order)
            else:
                remaining.append(stop_order)

        self._stop_orders = remaining
        for order in triggered:
            self._match(order)
            if order.remaining > 0 and order.order_type == OrderType.LIMIT:
                self._insert(order)

    def _notify_book_update(self) -> None:
        bids = self._get_price_levels(self._bids, is_bid=True)
        asks = self._get_price_levels(self._asks, is_bid=False)
        for sub in self._subscribers:
            sub.on_book_update(self.symbol, bids, asks)

    def _get_price_levels(self, heap: list, is_bid: bool,
                           depth: int = 5) -> list[PriceLevel]:
        levels: dict[float, PriceLevel] = {}
        for entry in heap:
            price = -entry[0] if is_bid else entry[0]
            order = entry[2]
            if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                continue
            if price not in levels:
                levels[price] = PriceLevel(price=price)
            levels[price].orders.append(order)

        sorted_prices = sorted(levels.keys(), reverse=is_bid)
        return [levels[p] for p in sorted_prices[:depth]]

    def get_best_bid(self) -> Optional[float]:
        for neg_price, _, order in sorted(self._bids):
            if order.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                return -neg_price
        return None

    def get_best_ask(self) -> Optional[float]:
        for price, _, order in sorted(self._asks):
            if order.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                return price
        return None


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0

    def update_on_buy(self, qty: int, price: float) -> None:
        total_cost = self.avg_cost * self.quantity + price * qty
        self.quantity += qty
        self.avg_cost = total_cost / self.quantity if self.quantity > 0 else 0

    def update_on_sell(self, qty: int, price: float) -> None:
        self.realized_pnl += (price - self.avg_cost) * qty
        self.quantity -= qty
        if self.quantity <= 0:
            self.avg_cost = 0
            self.quantity = 0

    def unrealized_pnl(self, market_price: float) -> float:
        return (market_price - self.avg_cost) * self.quantity


class RiskEngine:
    def __init__(self, max_position_size: int = 10000,
                 max_order_value: float = 1_000_000):
        self._max_position = max_position_size
        self._max_order_value = max_order_value

    def validate_order(self, order: Order,
                       portfolio: "Portfolio") -> tuple[bool, str]:
        if order.quantity <= 0:
            return False, "Invalid quantity"

        if order.order_type == OrderType.LIMIT and order.price <= 0:
            return False, "Invalid price for limit order"

        estimated_value = order.price * order.quantity if order.price else 0
        if estimated_value > self._max_order_value:
            return False, f"Order value {estimated_value} exceeds limit"

        position = portfolio.positions.get(order.symbol)
        current_qty = position.quantity if position else 0
        if order.side == Side.BUY:
            new_qty = current_qty + order.quantity
        else:
            new_qty = current_qty - order.quantity
        if abs(new_qty) > self._max_position:
            return False, f"Position would exceed limit: {new_qty}"

        if order.side == Side.BUY and estimated_value > portfolio.cash:
            return False, "Insufficient buying power"

        return True, ""


class Portfolio:
    def __init__(self, trader_id: str, initial_cash: float = 0):
        self.trader_id = trader_id
        self.cash: float = initial_cash
        self.positions: dict[str, Position] = {}
        self._lock = threading.Lock()

    def update_on_trade(self, trade: Trade, side: Side) -> None:
        with self._lock:
            if trade.symbol not in self.positions:
                self.positions[trade.symbol] = Position(symbol=trade.symbol)

            pos = self.positions[trade.symbol]
            if side == Side.BUY:
                pos.update_on_buy(trade.quantity, trade.price)
                self.cash -= trade.price * trade.quantity
            else:
                pos.update_on_sell(trade.quantity, trade.price)
                self.cash += trade.price * trade.quantity

    def total_value(self, market_prices: dict[str, float]) -> float:
        total = self.cash
        for symbol, pos in self.positions.items():
            price = market_prices.get(symbol, pos.avg_cost)
            total += pos.quantity * price
        return total


class TradingPlatform:
    def __init__(self):
        self._order_books: dict[str, OrderBook] = {}
        self._portfolios: dict[str, Portfolio] = {}
        self._risk_engine = RiskEngine()
        self._trade_history: list[Trade] = []
        self._lock = threading.Lock()

    def register_trader(self, trader_id: str,
                         initial_cash: float) -> Portfolio:
        portfolio = Portfolio(trader_id, initial_cash)
        self._portfolios[trader_id] = portfolio
        return portfolio

    def place_order(self, order: Order) -> tuple[list[Trade], str]:
        portfolio = self._portfolios.get(order.trader_id)
        if not portfolio:
            return [], "Trader not registered"

        valid, reason = self._risk_engine.validate_order(order, portfolio)
        if not valid:
            order.status = OrderStatus.REJECTED
            return [], reason

        with self._lock:
            if order.symbol not in self._order_books:
                self._order_books[order.symbol] = OrderBook(order.symbol)

        book = self._order_books[order.symbol]
        trades = book.submit_order(order)

        for trade in trades:
            buy_portfolio = self._portfolios.get(
                self._find_trader(trade.buy_order_id))
            sell_portfolio = self._portfolios.get(
                self._find_trader(trade.sell_order_id))
            if buy_portfolio:
                buy_portfolio.update_on_trade(trade, Side.BUY)
            if sell_portfolio:
                sell_portfolio.update_on_trade(trade, Side.SELL)

        self._trade_history.extend(trades)
        return trades, ""

    def _find_trader(self, order_id: str) -> str:
        for book in self._order_books.values():
            for heap in (book._bids, book._asks):
                for _, _, order in heap:
                    if order.order_id == order_id:
                        return order.trader_id
        return ""
```

### Concurrency Handling

- **Per-order-book locks** — different symbols can be traded simultaneously without contention
- **Portfolio locks** — P&L updates from trades on different symbols are serialized per trader
- **Price-time priority** guaranteed by the heap structure — insertion order (counter) breaks ties at the same price
- **Stop order triggering** is checked within the book lock after each trade, ensuring consistent price reference

### Scalability Considerations

- Shard order books by symbol across different servers for horizontal scaling
- Use lock-free data structures (disruptor pattern) for ultra-low-latency matching
- Separate market data dissemination from matching — fan-out trade notifications asynchronously
- Event sourcing for the order book enables replay and audit

### Testing Approach

- **Basic matching**: Buy limit at $10, sell limit at $10 — verify trade at $10
- **Price-time priority**: Two sells at $10 — verify the earlier one matches first
- **Partial fills**: Buy 100 at $10, sell 30 at $10 — verify 30-share trade, 70 remaining
- **Stop orders**: Place stop-buy at $15, market trades at $15 — verify stop converts to market order
- **Risk checks**: Try to buy more than buying power allows — verify rejection
- **IOC/FOK**: Submit IOC that can't fully fill — verify remainder is cancelled

---

## 11. Order Matching Engine

### Detailed Requirements

- Maintain separate bid and ask queues per instrument
- Price-time priority: best price first, then earliest order at same price
- Support matching algorithms: Pro-rata, FIFO, and hybrid
- Handle partial fills and order amendments
- Generate execution reports for each fill
- Support market hours and pre/post-market sessions
- Provide Level 2 market data (full order book depth)
- High-throughput design targeting microsecond latency goals

### Architecture Overview

```
OrderGateway ──validates──▶ Order ──routes to──▶ MatchingEngine
MatchingEngine ──manages──▶ OrderBook per instrument
OrderBook ──bid/ask──▶ PriceLevelMap ──contains──▶ OrderQueue
Match ──produces──▶ ExecutionReport*
MarketDataPublisher ──broadcasts──▶ Level2Data
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from enum import Enum
from typing import Optional
from collections import OrderedDict, deque
import threading
import uuid


class InstrumentType(Enum):
    EQUITY = "equity"
    OPTION = "option"
    FUTURE = "future"


class MatchAlgorithm(Enum):
    FIFO = "fifo"
    PRO_RATA = "pro_rata"


@dataclass
class Instrument:
    symbol: str
    instrument_type: InstrumentType = InstrumentType.EQUITY
    tick_size: float = 0.01
    lot_size: int = 1
    match_algorithm: MatchAlgorithm = MatchAlgorithm.FIFO


@dataclass
class EngineOrder:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    participant_id: str = ""
    instrument: str = ""
    side: str = "BUY"
    price: float = 0.0
    quantity: int = 0
    filled: int = 0
    is_market: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    sequence: int = 0

    @property
    def remaining(self) -> int:
        return self.quantity - self.filled


@dataclass
class ExecutionReport:
    exec_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    order_id: str = ""
    counter_order_id: str = ""
    instrument: str = ""
    side: str = ""
    price: float = 0.0
    quantity: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class OrderQueue:
    """Queue of orders at a single price level."""

    def __init__(self, price: float):
        self.price = price
        self._orders: deque[EngineOrder] = deque()
        self._total_quantity = 0

    def add(self, order: EngineOrder) -> None:
        self._orders.append(order)
        self._total_quantity += order.remaining

    def remove(self, order_id: str) -> Optional[EngineOrder]:
        for i, order in enumerate(self._orders):
            if order.order_id == order_id:
                self._total_quantity -= order.remaining
                del self._orders[i]
                return order
        return None

    @property
    def total_quantity(self) -> int:
        return self._total_quantity

    @property
    def order_count(self) -> int:
        return len(self._orders)

    @property
    def is_empty(self) -> bool:
        return len(self._orders) == 0

    def peek(self) -> Optional[EngineOrder]:
        return self._orders[0] if self._orders else None

    def pop_front(self) -> Optional[EngineOrder]:
        if self._orders:
            order = self._orders.popleft()
            self._total_quantity -= order.remaining
            return order
        return None

    def orders(self) -> list[EngineOrder]:
        return list(self._orders)


class MatchingStrategy(ABC):
    @abstractmethod
    def match(self, aggressor: EngineOrder,
              price_level: OrderQueue) -> list[ExecutionReport]:
        pass


class FIFOMatching(MatchingStrategy):
    def match(self, aggressor: EngineOrder,
              price_level: OrderQueue) -> list[ExecutionReport]:
        reports = []
        while aggressor.remaining > 0 and not price_level.is_empty:
            passive = price_level.peek()
            trade_qty = min(aggressor.remaining, passive.remaining)

            aggressor.filled += trade_qty
            passive.filled += trade_qty
            price_level._total_quantity -= trade_qty

            reports.append(ExecutionReport(
                order_id=aggressor.order_id,
                counter_order_id=passive.order_id,
                instrument=aggressor.instrument,
                side=aggressor.side,
                price=price_level.price,
                quantity=trade_qty,
            ))

            if passive.remaining == 0:
                price_level.pop_front()

        return reports


class ProRataMatching(MatchingStrategy):
    def match(self, aggressor: EngineOrder,
              price_level: OrderQueue) -> list[ExecutionReport]:
        reports = []
        total_passive = price_level.total_quantity
        if total_passive == 0:
            return reports

        available = aggressor.remaining
        allocations: list[tuple[EngineOrder, int]] = []

        for passive in price_level.orders():
            share = int((passive.remaining / total_passive) * available)
            share = max(1, share) if share > 0 else 0
            allocations.append((passive, min(share, passive.remaining)))

        allocated = sum(a for _, a in allocations)
        remainder = available - allocated
        if remainder > 0:
            for i, (order, alloc) in enumerate(allocations):
                extra = min(remainder, order.remaining - alloc)
                allocations[i] = (order, alloc + extra)
                remainder -= extra
                if remainder <= 0:
                    break

        to_remove = []
        for passive, qty in allocations:
            if qty <= 0:
                continue
            aggressor.filled += qty
            passive.filled += qty
            price_level._total_quantity -= qty

            reports.append(ExecutionReport(
                order_id=aggressor.order_id,
                counter_order_id=passive.order_id,
                instrument=aggressor.instrument,
                side=aggressor.side,
                price=price_level.price,
                quantity=qty,
            ))

            if passive.remaining == 0:
                to_remove.append(passive.order_id)

        for oid in to_remove:
            price_level.remove(oid)

        return reports


class BookSide:
    """One side (bid or ask) of the order book."""

    def __init__(self, is_bid: bool):
        self._is_bid = is_bid
        self._levels: OrderedDict[float, OrderQueue] = OrderedDict()

    def add_order(self, order: EngineOrder) -> None:
        price = order.price
        if price not in self._levels:
            self._levels[price] = OrderQueue(price)
            self._levels = OrderedDict(
                sorted(self._levels.items(),
                       reverse=self._is_bid)
            )
        self._levels[price].add(order)

    def remove_order(self, price: float,
                      order_id: str) -> Optional[EngineOrder]:
        level = self._levels.get(price)
        if not level:
            return None
        order = level.remove(order_id)
        if level.is_empty:
            del self._levels[price]
        return order

    def best_price(self) -> Optional[float]:
        if not self._levels:
            return None
        return next(iter(self._levels))

    def best_level(self) -> Optional[OrderQueue]:
        if not self._levels:
            return None
        return next(iter(self._levels.values()))

    def depth(self, levels: int = 10) -> list[tuple[float, int, int]]:
        """Returns (price, total_qty, order_count) for top N levels."""
        result = []
        for price, queue in self._levels.items():
            if len(result) >= levels:
                break
            result.append((price, queue.total_quantity, queue.order_count))
        return result

    @property
    def is_empty(self) -> bool:
        return len(self._levels) == 0


class InstrumentOrderBook:
    def __init__(self, instrument: Instrument):
        self.instrument = instrument
        self.bids = BookSide(is_bid=True)
        self.asks = BookSide(is_bid=False)
        self._sequence = 0
        self._lock = threading.Lock()

        strategy_class = (ProRataMatching if instrument.match_algorithm == MatchAlgorithm.PRO_RATA
                          else FIFOMatching)
        self._strategy: MatchingStrategy = strategy_class()
        self.last_trade_price: float = 0.0
        self.trades_today: int = 0
        self.volume_today: int = 0

    def submit(self, order: EngineOrder) -> list[ExecutionReport]:
        with self._lock:
            self._sequence += 1
            order.sequence = self._sequence
            order.instrument = self.instrument.symbol

            reports = self._try_match(order)

            if order.remaining > 0 and not order.is_market:
                if order.side == "BUY":
                    self.bids.add_order(order)
                else:
                    self.asks.add_order(order)

            for report in reports:
                self.last_trade_price = report.price
                self.trades_today += 1
                self.volume_today += report.quantity

            return reports

    def cancel(self, order: EngineOrder) -> bool:
        with self._lock:
            side = self.bids if order.side == "BUY" else self.asks
            removed = side.remove_order(order.price, order.order_id)
            return removed is not None

    def amend(self, order_id: str, side: str, old_price: float,
              new_qty: int) -> bool:
        with self._lock:
            book_side = self.bids if side == "BUY" else self.asks
            existing = book_side.remove_order(old_price, order_id)
            if not existing:
                return False
            existing.quantity = new_qty
            existing.filled = 0
            existing.timestamp = datetime.now()
            book_side.add_order(existing)
            return True

    def _try_match(self, order: EngineOrder) -> list[ExecutionReport]:
        reports = []
        opposite = self.asks if order.side == "BUY" else self.bids

        while order.remaining > 0 and not opposite.is_empty:
            best_level = opposite.best_level()
            best_price = best_level.price

            if not order.is_market:
                if order.side == "BUY" and best_price > order.price:
                    break
                if order.side == "SELL" and best_price < order.price:
                    break

            level_reports = self._strategy.match(order, best_level)
            reports.extend(level_reports)

            if best_level.is_empty:
                opposite._levels.pop(best_price, None)

        return reports

    def get_level2(self, depth: int = 10) -> dict:
        with self._lock:
            return {
                "symbol": self.instrument.symbol,
                "bids": self.bids.depth(depth),
                "asks": self.asks.depth(depth),
                "last_price": self.last_trade_price,
                "volume": self.volume_today,
            }


class OrderMatchingEngine:
    def __init__(self):
        self._books: dict[str, InstrumentOrderBook] = {}
        self._instruments: dict[str, Instrument] = {}
        self._execution_reports: list[ExecutionReport] = []
        self._lock = threading.Lock()

    def register_instrument(self, instrument: Instrument) -> None:
        self._instruments[instrument.symbol] = instrument
        self._books[instrument.symbol] = InstrumentOrderBook(instrument)

    def submit_order(self, order: EngineOrder) -> list[ExecutionReport]:
        book = self._books.get(order.instrument)
        if not book:
            return []

        reports = book.submit(order)
        self._execution_reports.extend(reports)
        return reports

    def cancel_order(self, order: EngineOrder) -> bool:
        book = self._books.get(order.instrument)
        if not book:
            return False
        return book.cancel(order)

    def get_market_data(self, symbol: str,
                         depth: int = 10) -> Optional[dict]:
        book = self._books.get(symbol)
        return book.get_level2(depth) if book else None

    def get_stats(self) -> dict:
        return {
            symbol: {
                "last_price": book.last_trade_price,
                "trades": book.trades_today,
                "volume": book.volume_today,
            }
            for symbol, book in self._books.items()
        }
```

### Concurrency Handling

- **Per-instrument locks** — orders for different instruments are matched concurrently
- **Sequence numbers** provide deterministic ordering within each instrument's book
- **BookSide** maintains sorted price levels — the `OrderedDict` is re-sorted on insertion, which is O(N log N) but happens infrequently
- For production latency requirements, use lock-free single-writer (disruptor) patterns

### Scalability Considerations

- Each instrument's order book is independent — shard by symbol for horizontal scaling
- Pro-rata matching is more complex (O(N) per match at a price level) vs FIFO (O(1) amortized)
- Batch matching: accumulate orders during an auction period, then match all at once
- Event sourcing: log every order and trade for replay, audit, and recovery

### Testing Approach

- **FIFO matching**: Two sells at same price — verify first is filled first
- **Pro-rata**: Three sellers with different quantities at same price — verify proportional allocation
- **Price improvement**: Buy at $10, sell at $9.50 — verify trade at $9.50 (seller's price)
- **Amendment**: Change order quantity, verify it loses time priority
- **Level 2 data**: Place multiple orders, verify book depth is accurate
- **Throughput**: Submit 100K orders per second, verify no lost orders

---

## 12. Cloud Storage Service

### Detailed Requirements

- Upload files with automatic chunking for large files
- Content-addressable storage with SHA-256 deduplication
- File versioning with full version history
- Sync client that detects and uploads local changes
- Share files and folders with other users via permission links
- Support multiple storage backends (local filesystem, S3 interface)
- File metadata indexing for search
- Handle concurrent uploads to the same file

### Architecture Overview

```
Client ──uploads──▶ ChunkManager ──deduplicates──▶ ChunkStore
FileMetadata ──tracks──▶ FileVersion* ──references──▶ Chunk*
SyncEngine ──detects──▶ local changes ──uploads──▶ delta chunks
ShareManager ──controls──▶ access permissions
StorageBackend (interface) ──stores──▶ chunk data
```

### Core Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, BinaryIO
import hashlib
import os
import threading
import uuid
import io


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class Chunk:
    chunk_hash: str
    size: int
    data: bytes = field(repr=False, default=b"")
    reference_count: int = 0

    @staticmethod
    def compute_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


@dataclass
class FileVersion:
    version_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    version_number: int = 0
    chunk_hashes: list[str] = field(default_factory=list)
    total_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    comment: str = ""

    @property
    def chunk_count(self) -> int:
        return len(self.chunk_hashes)


@dataclass
class FileMeta:
    file_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    path: str = ""
    owner_id: str = ""
    mime_type: str = "application/octet-stream"
    versions: list[FileVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_deleted: bool = False

    @property
    def current_version(self) -> Optional[FileVersion]:
        return self.versions[-1] if self.versions else None

    @property
    def current_size(self) -> int:
        return self.current_version.total_size if self.current_version else 0


@dataclass
class ShareLink:
    link_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    file_id: str = ""
    owner_id: str = ""
    permission: Permission = Permission.READ
    shared_with: set[str] = field(default_factory=set)
    is_public: bool = False
    expires_at: Optional[datetime] = None

    def can_access(self, user_id: str) -> bool:
        if self.is_public:
            return True
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return user_id == self.owner_id or user_id in self.shared_with


class StorageBackend(ABC):
    @abstractmethod
    def store_chunk(self, chunk_hash: str, data: bytes) -> bool:
        pass

    @abstractmethod
    def retrieve_chunk(self, chunk_hash: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def delete_chunk(self, chunk_hash: str) -> bool:
        pass

    @abstractmethod
    def has_chunk(self, chunk_hash: str) -> bool:
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str = "/tmp/cloud_storage"):
        self._base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _chunk_path(self, chunk_hash: str) -> str:
        prefix = chunk_hash[:2]
        dir_path = os.path.join(self._base_path, prefix)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, chunk_hash)

    def store_chunk(self, chunk_hash: str, data: bytes) -> bool:
        path = self._chunk_path(chunk_hash)
        if os.path.exists(path):
            return True  # already stored (dedup)
        with open(path, 'wb') as f:
            f.write(data)
        return True

    def retrieve_chunk(self, chunk_hash: str) -> Optional[bytes]:
        path = self._chunk_path(chunk_hash)
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return f.read()

    def delete_chunk(self, chunk_hash: str) -> bool:
        path = self._chunk_path(chunk_hash)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def has_chunk(self, chunk_hash: str) -> bool:
        return os.path.exists(self._chunk_path(chunk_hash))


class InMemoryStorageBackend(StorageBackend):
    def __init__(self):
        self._store: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def store_chunk(self, chunk_hash: str, data: bytes) -> bool:
        with self._lock:
            self._store[chunk_hash] = data
            return True

    def retrieve_chunk(self, chunk_hash: str) -> Optional[bytes]:
        return self._store.get(chunk_hash)

    def delete_chunk(self, chunk_hash: str) -> bool:
        with self._lock:
            return self._store.pop(chunk_hash, None) is not None

    def has_chunk(self, chunk_hash: str) -> bool:
        return chunk_hash in self._store


class ChunkManager:
    DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

    def __init__(self, backend: StorageBackend,
                 chunk_size: int = None):
        self._backend = backend
        self._chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self._chunk_refs: dict[str, int] = {}
        self._lock = threading.Lock()

    def split_and_store(self, data: bytes) -> list[str]:
        chunk_hashes = []
        for offset in range(0, len(data), self._chunk_size):
            chunk_data = data[offset:offset + self._chunk_size]
            chunk_hash = Chunk.compute_hash(chunk_data)

            with self._lock:
                if self._backend.has_chunk(chunk_hash):
                    self._chunk_refs[chunk_hash] = self._chunk_refs.get(chunk_hash, 0) + 1
                else:
                    self._backend.store_chunk(chunk_hash, chunk_data)
                    self._chunk_refs[chunk_hash] = 1

            chunk_hashes.append(chunk_hash)

        return chunk_hashes

    def reassemble(self, chunk_hashes: list[str]) -> bytes:
        parts = []
        for h in chunk_hashes:
            data = self._backend.retrieve_chunk(h)
            if data is None:
                raise FileNotFoundError(f"Missing chunk: {h}")
            parts.append(data)
        return b"".join(parts)

    def release_chunks(self, chunk_hashes: list[str]) -> None:
        with self._lock:
            for h in chunk_hashes:
                ref = self._chunk_refs.get(h, 0) - 1
                if ref <= 0:
                    self._backend.delete_chunk(h)
                    self._chunk_refs.pop(h, None)
                else:
                    self._chunk_refs[h] = ref

    def get_dedup_savings(self) -> dict:
        total_refs = sum(self._chunk_refs.values())
        unique_chunks = len(self._chunk_refs)
        return {
            "total_references": total_refs,
            "unique_chunks": unique_chunks,
            "dedup_ratio": total_refs / unique_chunks if unique_chunks > 0 else 1.0,
        }


class SyncState:
    """Tracks file states for sync detection."""

    def __init__(self):
        self._file_hashes: dict[str, str] = {}
        self._lock = threading.Lock()

    def update(self, path: str, content_hash: str) -> None:
        with self._lock:
            self._file_hashes[path] = content_hash

    def has_changed(self, path: str, content_hash: str) -> bool:
        return self._file_hashes.get(path) != content_hash

    def get_hash(self, path: str) -> Optional[str]:
        return self._file_hashes.get(path)


class CloudStorageService:
    def __init__(self, backend: StorageBackend = None):
        self._backend = backend or InMemoryStorageBackend()
        self._chunk_manager = ChunkManager(self._backend)
        self._files: dict[str, FileMeta] = {}
        self._shares: dict[str, ShareLink] = {}
        self._user_files: dict[str, list[str]] = {}
        self._sync_states: dict[str, SyncState] = {}
        self._lock = threading.Lock()

    def upload(self, user_id: str, path: str, name: str,
               data: bytes, comment: str = "") -> FileMeta:
        content_hash = hashlib.sha256(data).hexdigest()
        full_path = f"{path}/{name}"

        with self._lock:
            existing = self._find_file(user_id, full_path)

        chunk_hashes = self._chunk_manager.split_and_store(data)

        with self._lock:
            if existing:
                file_meta = existing
                version_num = len(file_meta.versions) + 1
            else:
                file_meta = FileMeta(
                    name=name, path=path, owner_id=user_id,
                )
                self._files[file_meta.file_id] = file_meta
                if user_id not in self._user_files:
                    self._user_files[user_id] = []
                self._user_files[user_id].append(file_meta.file_id)
                version_num = 1

            version = FileVersion(
                version_number=version_num,
                chunk_hashes=chunk_hashes,
                total_size=len(data),
                created_by=user_id,
                comment=comment,
            )
            file_meta.versions.append(version)
            file_meta.modified_at = datetime.now()

            sync_state = self._sync_states.setdefault(user_id, SyncState())
            sync_state.update(full_path, content_hash)

        return file_meta

    def download(self, user_id: str, file_id: str,
                 version: int = None) -> Optional[bytes]:
        file_meta = self._files.get(file_id)
        if not file_meta:
            return None

        if not self._can_access(user_id, file_id, Permission.READ):
            return None

        if version:
            target = next(
                (v for v in file_meta.versions if v.version_number == version),
                None
            )
        else:
            target = file_meta.current_version

        if not target:
            return None

        return self._chunk_manager.reassemble(target.chunk_hashes)

    def delete(self, user_id: str, file_id: str) -> bool:
        file_meta = self._files.get(file_id)
        if not file_meta or file_meta.owner_id != user_id:
            return False

        file_meta.is_deleted = True
        file_meta.modified_at = datetime.now()
        return True

    def get_versions(self, file_id: str) -> list[FileVersion]:
        file_meta = self._files.get(file_id)
        if not file_meta:
            return []
        return file_meta.versions

    def restore_version(self, user_id: str, file_id: str,
                         version: int) -> bool:
        file_meta = self._files.get(file_id)
        if not file_meta or file_meta.owner_id != user_id:
            return False

        target = next(
            (v for v in file_meta.versions if v.version_number == version),
            None
        )
        if not target:
            return False

        new_version = FileVersion(
            version_number=len(file_meta.versions) + 1,
            chunk_hashes=list(target.chunk_hashes),
            total_size=target.total_size,
            created_by=user_id,
            comment=f"Restored from version {version}",
        )
        file_meta.versions.append(new_version)
        file_meta.modified_at = datetime.now()
        return True

    def share(self, owner_id: str, file_id: str,
              target_users: set[str] = None,
              permission: Permission = Permission.READ,
              is_public: bool = False) -> ShareLink:
        link = ShareLink(
            file_id=file_id,
            owner_id=owner_id,
            permission=permission,
            shared_with=target_users or set(),
            is_public=is_public,
        )
        self._shares[link.link_id] = link
        return link

    def search(self, user_id: str, query: str) -> list[FileMeta]:
        results = []
        for file_id in self._user_files.get(user_id, []):
            file_meta = self._files.get(file_id)
            if file_meta and not file_meta.is_deleted:
                if query.lower() in file_meta.name.lower():
                    results.append(file_meta)
        return results

    def get_storage_stats(self, user_id: str) -> dict:
        total_size = 0
        file_count = 0
        version_count = 0
        for file_id in self._user_files.get(user_id, []):
            file_meta = self._files.get(file_id)
            if file_meta and not file_meta.is_deleted:
                file_count += 1
                version_count += len(file_meta.versions)
                total_size += file_meta.current_size

        dedup = self._chunk_manager.get_dedup_savings()
        return {
            "total_size_bytes": total_size,
            "file_count": file_count,
            "version_count": version_count,
            "dedup_ratio": dedup["dedup_ratio"],
        }

    def _find_file(self, user_id: str, full_path: str) -> Optional[FileMeta]:
        for file_id in self._user_files.get(user_id, []):
            meta = self._files.get(file_id)
            if meta and not meta.is_deleted:
                if f"{meta.path}/{meta.name}" == full_path:
                    return meta
        return None

    def _can_access(self, user_id: str, file_id: str,
                     required: Permission) -> bool:
        file_meta = self._files.get(file_id)
        if not file_meta:
            return False
        if file_meta.owner_id == user_id:
            return True
        for link in self._shares.values():
            if link.file_id == file_id and link.can_access(user_id):
                if required == Permission.READ:
                    return True
                if link.permission in (Permission.WRITE, Permission.ADMIN):
                    return True
        return False

    def detect_changes(self, user_id: str,
                        local_files: dict[str, bytes]) -> dict[str, str]:
        """Compare local files with cloud state, return actions needed."""
        sync_state = self._sync_states.get(user_id, SyncState())
        actions = {}
        for path, data in local_files.items():
            content_hash = hashlib.sha256(data).hexdigest()
            if sync_state.has_changed(path, content_hash):
                actions[path] = "upload"
        return actions
```

### Concurrency Handling

- **Service-level lock** for metadata operations (file creation, version updates) — prevents concurrent uploads from creating duplicate file entries
- **ChunkManager lock** for reference counting — ensures chunk deduplication counts are accurate
- **Backend locks** in `InMemoryStorageBackend` — the `LocalStorageBackend` relies on filesystem atomicity
- **Per-file versioning** — concurrent uploads to the same file create separate versions rather than conflicting

### Scalability Considerations

- **Content-addressable storage** with SHA-256 hashing provides automatic deduplication — identical chunks are stored once regardless of how many files reference them
- **Chunking** enables parallel uploads (each chunk uploaded independently) and efficient sync (only changed chunks are re-uploaded)
- **Swap the storage backend** to S3 or GCS for virtually unlimited capacity
- **Reference counting** for chunks enables safe garbage collection when files are deleted
- **Version history** grows linearly — implement retention policies (keep last N versions, or versions within M days)

### Testing Approach

- **Upload and download**: Upload a file, download it, verify byte-for-byte match
- **Deduplication**: Upload the same file twice, verify only one copy of chunks exists
- **Versioning**: Upload a file, modify it, upload again — verify both versions are accessible
- **Restore**: Restore an old version, verify current version now matches the restored content
- **Sharing**: Share a file with another user, verify they can read but not delete
- **Large file chunking**: Upload a 50 MB file, verify it's split into correct number of chunks
- **Concurrent upload**: Two users upload different files simultaneously, verify both succeed
- **Sync detection**: Modify a local file, call `detect_changes`, verify it's flagged for upload

---

## Summary: Complexity and Pattern Matrix

| Problem | Primary Patterns | Concurrency Model | Complexity |
|---------|-----------------|-------------------|------------|
| Thread Pool | Producer-Consumer, Strategy, Command | Locks, Conditions, Futures | ●●●●● |
| Rate Limiter | Strategy, Decorator | Per-key locks, Atomic counters | ●●●● |
| Distributed Cache | Strategy, Chain of Responsibility | Per-node locks, Version vectors | ●●●●● |
| Message Queue | Observer, Strategy, Iterator | Per-partition locks, Offset tracking | ●●●●● |
| Workflow Engine | Command, State, Composite | Fork/Join threads, Shared context | ●●●●● |
| KV Store | Strategy, Mediator | Vector clocks, Quorum | ●●●●● |
| Incremental Compiler | Interpreter, Composite, Iterator | Per-file parallel compilation | ●●●● |
| LeetCode Judge | Strategy, Command, Factory | Worker pool, Sandboxed subprocess | ●●●● |
| Code Runner | Strategy, Factory | Worker pool, Process isolation | ●●● |
| Trading Platform | Observer, Strategy, Mediator | Per-book locks, Event-driven | ●●●●● |
| Order Matching Engine | Strategy, Iterator | Per-instrument locks, Sequence ordering | ●●●●● |
| Cloud Storage | Strategy, Proxy, Template Method | Chunk-level dedup, Version control | ●●●● |

### How to Practice

1. **Pick one problem per day** — spend 60–90 minutes on the design and core implementation
2. **Start with the data model** — draw entities and relationships before writing code
3. **Identify the hardest concurrency challenge** in each problem — that's where interviewers will dig in
4. **Write tests** — if you can test it, you understand it
5. **Extend the design** — interviewers love follow-up questions like "How would you add feature X?"

### Cross-Cutting Concerns Checklist

For every problem, be prepared to discuss:

- [ ] **Thread safety**: Where are the critical sections? What's the lock granularity?
- [ ] **Failure handling**: What happens when a component crashes mid-operation?
- [ ] **Scalability**: How does this work with 100x more load?
- [ ] **Observability**: How would you monitor this system in production?
- [ ] **Testing**: How do you test concurrent behavior? Race conditions?
- [ ] **Extensibility**: How easy is it to add a new algorithm/strategy/backend?
