# LLD Interview Guide: Circuit Breaker Pattern

## How to Think Through Any LLD Problem in FAANG Interviews

---

# PART A: BEGINNER'S FIRST PRINCIPLES (Start Here If You're New)

If you don't know design patterns yet — that's fine. Here's how to THINK your way to a
good design from scratch, using pure logic.

---

## The Beginner Mindset: Forget Patterns, Think in Problems

Patterns are just names for solutions that smart people kept repeating. You can
REDISCOVER them by asking the right questions.

---

## Level 1: Start With "What Does This Thing DO?"

Write ONE sentence about the system:

> "A circuit breaker wraps an API call and stops calling when the service is unhealthy."

Now expand with THREE questions:

| Question | Your Answer | What this becomes |
|----------|-------------|-------------------|
| What changes? | The behavior (allow calls vs block calls) | You need STATES |
| What decides the change? | Some condition (too many errors) | You need a DECISION MAKER |
| What tracks history? | Success/failure counts | You need MEMORY |

**Congrats — you just discovered your first 3 classes:**
- `State` (behavior that changes)
- `DecisionMaker` (logic that triggers change)
- `Memory` (data that the decision is based on)

You don't need to know "State Pattern" — you naturally arrived at it by asking "what changes?"

---

## Level 2: "What If I Put Everything in One Class?"

Beginners often start here:

```python
class CircuitBreaker:
    def __init__(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.threshold = 5

    def call(self, func):
        if self.state == "OPEN":
            raise Exception("Circuit open!")

        try:
            result = func()
            self.failure_count = 0
            return result
        except:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.state = "OPEN"
            raise
```

**This works!** But now ask: "What's WRONG with this?"

| Problem | Why it's bad | Fix |
|---------|-------------|-----|
| Adding HALF_OPEN means adding more if-else to `call()` | Every new state makes the method longer | Extract each state's logic into its own class |
| Changing from count-based to percentage-based means editing `call()` | Core logic changes for a config decision | Extract the "should I trip?" logic out |
| `failure_count` and threshold logic are mixed with call execution | Can't test counting independently | Separate metrics tracking |

**This is how you "discover" patterns:**
- "Each state has different behavior" → extract into state classes → you just invented State Pattern
- "The trip decision might change" → extract into a separate class → you just invented Strategy Pattern
- "Tracking data is separate from using it" → extract into Metrics → you just invented Single Responsibility

---

## Level 3: The "What If" Game — How to Break Your Design

After your first draft, attack it with questions:

| Ask yourself | What it reveals |
|---|---|
| "What if two threads call this at the same time?" | You need thread safety |
| "What if I have 10 different APIs?" | You need one breaker per service |
| "What if the service is slow but not failing?" | You need latency tracking too |
| "What if I want to change threshold without restarting?" | You need config separated from logic |
| "What if OPEN state never recovers?" | You need a timeout + HALF_OPEN state |
| "What if 100 threads all try HALF_OPEN at once?" | You need to limit trial requests |

**Every "what if" that breaks your design = a follow-up the interviewer will ask.**
Find them FIRST, and you look like a senior engineer.

---

## Level 4: How to Learn Patterns (The Right Way)

Don't memorize patterns from a book. Instead:

**Step 1:** Build a naive version (everything in one class)
**Step 2:** Ask "what changes independently?" — extract it
**Step 3:** Ask "what might have multiple implementations?" — make it an interface
**Step 4:** Give it a name later (oh, that's Strategy Pattern!)

Here's the progression:

```
BEGINNER:     One big class with if-else
                        ↓
INTERMEDIATE: "I'll separate states into classes" (discovers State Pattern)
              "I'll make the threshold logic swappable" (discovers Strategy)
                        ↓
ADVANCED:     Names the patterns, justifies trade-offs, identifies concurrency
              issues, walks through scenarios — all PROACTIVELY
```

---

## Level 5: The Concurrency Crash Course (for Beginners)

If you've never dealt with threading, here are the 3 things to know:

### Problem 1: Two threads read-then-write the same variable

```
Thread A reads count = 4
Thread B reads count = 4
Thread A writes count = 5
Thread B writes count = 5   ← WRONG! Should be 6
```

**Fix:** Lock (mutex) — only one thread can read+write at a time.

### Problem 2: One thread updates state, others see old value

```
Thread A sets state = OPEN
Thread B still sees state = CLOSED (CPU cache)
```

**Fix:** Lock ensures visibility, or use atomic variables.

### Problem 3: You want exactly N threads to do something

```
HALF_OPEN: only 3 threads should make trial calls, rest should fail fast
```

**Fix:** Semaphore — like a counter of "permits". Acquire one to proceed, others wait/fail.

### Quick reference:

| I need... | Use... | Python |
|-----------|--------|--------|
| Only one thread in a section | Lock/Mutex | `threading.Lock()` |
| N threads allowed concurrently | Semaphore | `threading.Semaphore(n)` |
| Wait for a condition | Condition Variable | `threading.Condition()` |
| Thread-safe queue | BlockingQueue | `queue.Queue()` |

---

## Level 6: "But I Don't Know Which Pattern to Use"

Here's the cheat sheet. If your problem has THIS characteristic, use THIS:

| Your problem looks like... | Pattern | English translation |
|---|---|---|
| Object behaves differently based on its current mode | State | "It acts different when it's angry vs calm" |
| You need to swap an algorithm without changing the caller | Strategy | "Same car, different engines" |
| Only one instance should exist | Singleton | "There can only be one" |
| You want to be notified when something changes | Observer | "Subscribe to updates" |
| You want to add features without changing original class | Decorator | "Wrap it with extra powers" |
| You want to create objects without hardcoding the type | Factory | "Order from menu, kitchen decides how" |

---

## How to Bridge Beginner → Interview Ready

| Week | Focus | Practice |
|------|-------|----------|
| 1-2 | Build naive versions | Code a CB, Rate Limiter, LRU Cache with ONE class |
| 3-4 | Learn to extract | Refactor your naive code — separate concerns |
| 5-6 | Name the patterns | Map your extractions to pattern names |
| 7-8 | Add concurrency | Make your designs thread-safe |
| 9-10 | Practice communication | Explain your design OUT LOUD in 12 minutes |

---

# PART B: INTERMEDIATE TO ADVANCED (The Structured Approach)

Everything below assumes you're comfortable with basic OOP and want to
nail the structured delivery in a FAANG interview.

---

## Step 0: The First 2 Minutes — Clarify & Scope

Before you touch a whiteboard, ask questions. This separates senior from junior candidates.

**Questions to ask the interviewer:**

1. "Is this for a single service or multiple downstream services?"
2. "Do we need thread-safety? Is this a multi-threaded environment?"
3. "Should the failure criteria be configurable? (count vs percentage vs latency)"
4. "Do we need observability — like callbacks on state change?"

**Why this matters:** Interviewers want to see you DON'T jump to code. You think about requirements first.

**For Circuit Breaker, you'd arrive at:**
- Wrap any remote call
- Three states: CLOSED → OPEN → HALF_OPEN → CLOSED
- Configurable trip conditions
- Thread-safe
- Per-service isolation

---

## Step 1: Identify Core Entities (3 minutes)

**The mental model:** Think of the system as NOUNS (entities) and VERBS (behaviors).

| Ask yourself | Answer | Entity |
|---|---|---|
| What's the main thing? | The breaker itself | `CircuitBreaker` |
| What does it track? | Success/failure history | `Metrics` |
| What does it decide? | Should we trip? | `EvaluationStrategy` |
| What behavior changes? | Open vs Closed vs Half-Open | `State` (abstract) |
| What holds configuration? | Thresholds, timeouts | `Config` |
| What manages multiple breakers? | One per service | `Registry` |

**Tip:** Start with 4-6 classes max. Don't over-engineer upfront. You can add more when the interviewer probes.

---

## Step 2: Choose Design Patterns (2 minutes)

Once you have entities, map them to patterns. This is where you show depth.

| Problem | Pattern | Why |
|---|---|---|
| Behavior changes based on state | **State Pattern** | Each state encapsulates its own logic. Adding a new state doesn't touch existing code. |
| Multiple ways to decide "should trip?" | **Strategy Pattern** | Swap error-rate, count-based, slow-call strategies without modifying core. |
| One breaker per downstream service | **Registry / Factory** | Centralized creation, prevents duplicates. |
| Singleton registry | **Double-Checked Locking** | Thread-safe lazy initialization. |

**How to articulate this in interview:**

> "I'll use the State Pattern because behavior differs per state — CLOSED executes calls,
> OPEN rejects them, HALF_OPEN does limited trials. Each state class owns its own logic,
> so adding a new state is just a new class."

> "For the trip condition, I'll use Strategy Pattern. Today it's error-rate, tomorrow
> the team might want slow-call percentage. The core breaker shouldn't know or care."

---

## Step 3: Define Relationships & Responsibilities (3 minutes)

Draw the class diagram. Each class should have ONE clear job.

```
┌─────────────────────────────────────────────────────────────┐
│                    CircuitBreakerRegistry                     │
│  (Singleton, thread-safe, one CB per service name)           │
│  + get(name) → CircuitBreaker                                │
└───────────────────────────┬─────────────────────────────────┘
                            │ creates/returns
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      CircuitBreaker                           │
│  - name: str                                                 │
│  - state_context: StateContext                               │
│  + call(func, *args) → result or raise OpenError             │
└───────────────────────────┬─────────────────────────────────┘
                            │ delegates to
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      StateContext                             │
│  - current_state: State                                      │
│  - strategy: EvaluationStrategy                              │
│  - metrics: Metrics                                          │
│  - config: Config                                            │
│  + transition_to(target_state)   ← atomic, locked            │
└────────┬──────────────────────────────────┬─────────────────┘
         │ holds                            │ uses
         ▼                                  ▼
┌──────────────────┐             ┌──────────────────────────┐
│   State (ABC)    │             │  EvaluationStrategy (ABC) │
│  + handle(func)  │             │  + should_transition()    │
└────────┬─────────┘             └────────────┬─────────────┘
         │ extends                            │ implements
    ┌────┼────────┐                ┌──────────┼──────────┐
    ▼    ▼        ▼                ▼          ▼          ▼
Closed  Open  HalfOpen      ErrorRate   CountBased  SlowCall
```

**Key ownership rules:**
- `CircuitBreaker` → thin API layer, delegates everything
- `StateContext` → owns state transitions (locked), holds shared resources
- `State` subclasses → own per-state behavior logic
- `Strategy` → owns the "should I trip?" decision
- `Metrics` → owns the sliding window data

---

## Step 4: Nail the State Transitions (5 minutes)

This is the CORE of the problem. Draw it clearly.

```
                    failure threshold exceeded
         ┌──────────────────────────────────────────┐
         │                                          ▼
    ┌─────────┐                              ┌──────────┐
    │ CLOSED  │                              │   OPEN   │
    │         │                              │          │
    │ execute │                              │ fail-fast│
    │  calls  │                              │ all calls│
    └─────────┘                              └──────────┘
         ▲                                        │
         │ all trials succeed              timeout elapsed
         │                                  (lazy check)
         │         ┌───────────┐                  │
         └─────────│ HALF_OPEN │◄─────────────────┘
                   │           │
                   │  limited  │──── any trial fails ──→ back to OPEN
                   │  trials   │
                   └───────────┘
```

**For each state, define:**

| State | On call arrives | Transition trigger | Who triggers |
|-------|----------------|-------------------|--------------|
| CLOSED | Execute the call, record result | Error rate ≥ threshold | Strategy after recording metric |
| OPEN | Reject immediately (fail-fast) | Timeout elapsed | Caller thread (lazy check on next call) |
| HALF_OPEN | Allow if semaphore permits, else reject | All trials pass OR any fails | HalfOpenStrategy after trial |

---

## Step 5: Concurrency — Where It Gets Real (5 minutes)

**The interviewer WILL ask about thread safety.** Here's how to think about it systematically.

### Identify shared mutable state:
1. `current_state` — read by all callers, written during transitions
2. `metrics` data — written on every call result
3. `semaphore` in HALF_OPEN — shared across trial threads

### For each, choose the right primitive:

| Shared State | Concurrency Approach | Rationale |
|---|---|---|
| State transitions | `threading.Lock` (mutex) | Only one thread should transition at a time. CAS semantics. |
| Metrics writes | Lock inside Metrics class | Single lock, fine-grained. Or use producer-consumer queue. |
| HALF_OPEN trial limit | `threading.Semaphore(N)` | Natural fit — N permits for N trials. Non-blocking tryAcquire. |
| State read visibility | Transition under lock ensures visibility | Python's GIL + lock release acts as memory barrier |

### The key race condition to call out:

> "When timeout elapses in OPEN state, multiple threads might simultaneously try to
> transition to HALF_OPEN. I handle this with a lock in `transition_to()` — only the
> first thread wins. The rest see the state already changed and proceed under HALF_OPEN rules."

**Say this proactively.** Don't wait for the interviewer to find it.

---

## Step 6: Walk Through a Scenario (2 minutes)

Always validate your design with a concrete trace. This catches bugs and impresses interviewers.

```
Timeline:
─────────────────────────────────────────────────────────────────
t=0   Call 1 → CLOSED → execute → SUCCESS → metrics: 0% error
t=1   Call 2 → CLOSED → execute → FAIL    → metrics: 50% (1/2)
t=2   Call 3 → CLOSED → execute → FAIL    → metrics: 66% (2/3)
                                            → threshold 50% exceeded!
                                            → Strategy says: OPEN
                                            → transition_to(OPEN)
t=3   Call 4 → OPEN → fail fast (no downstream call)
t=4   Call 5 → OPEN → fail fast
...
t=32  Call N → OPEN → check: 30s elapsed? YES
                    → transition_to(HALF_OPEN)
                    → semaphore(3 permits)
t=32  Call N → HALF_OPEN → acquire permit (2 left)
                         → execute → SUCCESS → trial 1 pass
t=33  Call N+1 → HALF_OPEN → acquire permit (1 left)
                           → execute → SUCCESS → trial 2 pass
t=34  Call N+2 → HALF_OPEN → acquire permit (0 left)
                           → execute → SUCCESS → trial 3 pass
                           → all 3 passed! → transition_to(CLOSED)
t=35  Call N+3 → CLOSED → normal flow resumes
```

---

## Step 7: Extensibility — Show Senior Thinking

After the core design, mention what can be added WITHOUT changing existing code:

| Extension | How to add | SOLID principle |
|---|---|---|
| New trip strategy (e.g., composite) | Implement `EvaluationStrategy` | Open/Closed |
| Event listeners (on state change) | Observer pattern on `transition_to()` | Single Responsibility |
| Decorator/annotation support | `@circuit_breaker("service")` | Don't Repeat Yourself |
| Health dashboard | Read from `Registry.get_all()` | Interface Segregation |
| Fallback function | Optional param in `call()` | Liskov (fallback returns same type) |

---

## The Interview Communication Template

Use this structure when presenting:

```
1. "Let me clarify the requirements..." (30 sec)
2. "The core entities I see are..." (1 min)
3. "I'll use [Pattern] because [reason]..." (1 min)
4. "Here's how state transitions work..." (3 min, draw diagram)
5. "For concurrency, the critical sections are..." (2 min)
6. "Let me trace through a scenario..." (2 min)
7. "For extensibility, I'd add..." (1 min, if time permits)
```

Total: ~12 minutes for the design + remaining time for coding key classes.

---

## Common Follow-Up Questions & Strong Answers

**Q: "Why not use if-else for states instead of State Pattern?"**
> "With 3 states, if-else works. But when we add FORCED_OPEN (for maintenance),
> DISABLED (for testing), each if-else grows. State pattern makes each state
> independently testable and follows Open/Closed principle."

**Q: "What if the strategy needs to change at runtime?"**
> "Strategy is injected via constructor. I can add `setStrategy()` on the context.
> The next evaluation will use the new strategy. Since the consumer thread is the
> only one calling it, no race condition."

**Q: "How would you test this?"**
> "I'd mock the downstream call. For state transitions: inject a clock (instead of
> `time.time()`) so I can fast-forward the OPEN timeout in tests without sleeping."

**Q: "What about monitoring?"**
> "I'd add an Observer/callback list on `transition_to()`. On state change, notify
> all listeners — they can emit metrics to Prometheus, log, alert. Decoupled from core logic."

---

## Anti-Patterns to Avoid in LLD Interviews

| Don't do this | Do this instead |
|---|---|
| Start coding immediately | Clarify requirements, draw diagram first |
| Use God class with all logic | Separate concerns into focused classes |
| Ignore concurrency until asked | Proactively identify shared state |
| Over-engineer from start | Start simple, mention extensions verbally |
| Say "I think" / "maybe" | Be decisive: "I'll use X because Y" |
| Forget error handling | Show CircuitBreakerOpenError, fallback path |
| Design in vacuum | Trace a concrete scenario through your design |

---

## Quick Reference: When to Use Which Pattern

| If you see... | Think... |
|---|---|
| Object behavior changes based on internal state | State Pattern |
| Multiple algorithms for the same task | Strategy Pattern |
| One instance shared across the system | Singleton / Registry |
| Limiting concurrent access to a resource | Semaphore |
| Decoupling event producers from consumers | Observer / Pub-Sub |
| Wrapping an object with additional behavior | Decorator |
| Creating objects without specifying exact class | Factory |
| Undoing operations | Command + Memento |

---

---

# PART C: KEY CODE SNIPPETS — The Logic That Matters

These are the critical pieces an interviewer expects you to write on a whiteboard.
Not the full implementation — just the CORE logic that proves you can code the design.

---

## 1. The State Enum + Config (Simple, Write First)

```python
from enum import Enum
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class Config:
    failure_threshold: float = 0.5      # 50% error rate to trip
    window_seconds: int = 60            # sliding window
    open_timeout_seconds: int = 30      # how long to stay open
    max_trial_requests: int = 3         # permits in HALF_OPEN
    min_calls_in_window: int = 5        # minimum sample size
```

---

## 2. Sliding Window Metrics (The Data Layer)

This is what interviewers look for — efficient eviction, not storing data forever.

```python
import time
import threading
from collections import deque

class Metrics:
    def __init__(self, window_seconds: int):
        self._window = window_seconds
        self._records: deque = deque()  # (timestamp, success: bool)
        self._lock = threading.Lock()

    def record(self, success: bool):
        with self._lock:
            self._records.append((time.time(), success))
            self._evict()

    def get_failure_rate(self) -> float:
        with self._lock:
            self._evict()
            if not self._records:
                return 0.0
            failures = sum(1 for _, ok in self._records if not ok)
            return failures / len(self._records)

    def total_calls(self) -> int:
        with self._lock:
            self._evict()
            return len(self._records)

    def _evict(self):
        """Remove entries outside the time window — O(1) amortized with deque."""
        cutoff = time.time() - self._window
        while self._records and self._records[0][0] < cutoff:
            self._records.popleft()

    def reset(self):
        with self._lock:
            self._records.clear()
```

**Why deque?** — `popleft()` is O(1). Entries arrive in time order, so oldest is always at front.
No need to sort or scan.

---

## 3. Strategy Interface + Error Rate Strategy (Pluggable Decision)

```python
from abc import ABC, abstractmethod

class TripStrategy(ABC):
    @abstractmethod
    def should_trip(self, metrics: Metrics) -> bool:
        """Return True if circuit should OPEN."""
        ...

class ErrorRateStrategy(TripStrategy):
    def __init__(self, threshold: float = 0.5, min_calls: int = 5):
        self._threshold = threshold
        self._min_calls = min_calls

    def should_trip(self, metrics: Metrics) -> bool:
        if metrics.total_calls() < self._min_calls:
            return False  # not enough data to decide
        return metrics.get_failure_rate() >= self._threshold
```

**Interview point:** Always check `min_calls`. Without it, 1 failure out of 1 call = 100%
error rate → circuit trips on the FIRST failure. That's a bug.

---

## 4. The State Transition Logic (THE HEART — Write This on Whiteboard)

```python
import time
import threading

class StateContext:
    def __init__(self, config: Config, strategy: TripStrategy):
        self.config = config
        self.strategy = strategy
        self.metrics = Metrics(config.window_seconds)
        self._state = CircuitState.CLOSED
        self._lock = threading.Lock()
        self._opened_at: float = 0
        self._semaphore: threading.Semaphore | None = None

    @property
    def state(self) -> CircuitState:
        return self._state

    def transition_to(self, target: CircuitState):
        """Atomic state transition — only one thread can transition at a time."""
        with self._lock:
            if self._state == target:
                return  # already there, no-op
            self._state = target
            if target == CircuitState.OPEN:
                self._opened_at = time.time()
            elif target == CircuitState.HALF_OPEN:
                self._semaphore = threading.Semaphore(self.config.max_trial_requests)

    def execute(self, func, *args, **kwargs):
        """The main entry point — routes to correct state logic."""
        if self._state == CircuitState.CLOSED:
            return self._handle_closed(func, *args, **kwargs)
        elif self._state == CircuitState.OPEN:
            return self._handle_open(func, *args, **kwargs)
        elif self._state == CircuitState.HALF_OPEN:
            return self._handle_half_open(func, *args, **kwargs)

    def _handle_closed(self, func, *args, **kwargs):
        """Execute call. If strategy says trip → go OPEN."""
        try:
            result = func(*args, **kwargs)
            self.metrics.record(success=True)
            return result
        except Exception as exc:
            self.metrics.record(success=False)
            if self.strategy.should_trip(self.metrics):
                self.transition_to(CircuitState.OPEN)
            raise exc

    def _handle_open(self, func, *args, **kwargs):
        """Fail fast. Lazy check: if timeout elapsed → go HALF_OPEN."""
        elapsed = time.time() - self._opened_at
        if elapsed >= self.config.open_timeout_seconds:
            self.transition_to(CircuitState.HALF_OPEN)
            return self._handle_half_open(func, *args, **kwargs)
        raise CircuitBreakerOpenError(
            f"Circuit OPEN. Retry in {self.config.open_timeout_seconds - elapsed:.1f}s"
        )

    def _handle_half_open(self, func, *args, **kwargs):
        """Limited trials via semaphore. Success → CLOSED. Failure → OPEN."""
        acquired = self._semaphore.acquire(blocking=False)
        if not acquired:
            raise CircuitBreakerOpenError("HALF_OPEN: trial slots full")

        try:
            result = func(*args, **kwargs)
            self.metrics.record(success=True)
            # Check if all trials succeeded
            if self._all_trials_passed():
                self.metrics.reset()
                self.transition_to(CircuitState.CLOSED)
            return result
        except Exception as exc:
            self.metrics.record(success=False)
            self.transition_to(CircuitState.OPEN)  # any failure → back to OPEN
            raise exc

    def _all_trials_passed(self) -> bool:
        """If semaphore is fully consumed AND no failures, all trials passed."""
        # Attempt to acquire — if it fails, all permits used
        if self._semaphore.acquire(blocking=False):
            self._semaphore.release()  # put it back, not all used yet
            return False
        return True  # all permits consumed = all trials done


class CircuitBreakerOpenError(Exception):
    pass
```

---

## 5. The Public API (What Callers See)

```python
class CircuitBreaker:
    def __init__(self, name: str, config: Config = None, strategy: TripStrategy = None):
        self._name = name
        self._config = config or Config()
        self._strategy = strategy or ErrorRateStrategy(
            threshold=self._config.failure_threshold,
            min_calls=self._config.min_calls_in_window,
        )
        self._context = StateContext(self._config, self._strategy)

    @property
    def state(self) -> CircuitState:
        return self._context.state

    def call(self, func, *args, **kwargs):
        """Execute func through the circuit breaker."""
        return self._context.execute(func, *args, **kwargs)


# Usage:
cb = CircuitBreaker("payment-service", Config(failure_threshold=0.6))
try:
    result = cb.call(requests.get, "http://payments/api/charge")
except CircuitBreakerOpenError:
    return fallback_response()
```

---

## 6. Registry — One Breaker Per Service (Thread-Safe)

```python
class CircuitBreakerRegistry:
    _breakers: dict[str, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, name: str, config: Config = None) -> CircuitBreaker:
        """Get or create. Double-checked locking for thread safety."""
        if name not in cls._breakers:
            with cls._lock:
                if name not in cls._breakers:  # double-check after lock
                    cls._breakers[name] = CircuitBreaker(name, config)
        return cls._breakers[name]
```

**Interview point:** Double-checked locking — check without lock (fast path), then
check again WITH lock (safe path). Avoids locking on every access.

---

## 7. Decorator Syntax (Bonus — Shows Polish)

```python
import functools

def circuit_breaker(service_name: str, config: Config = None):
    """Use as @circuit_breaker('payment-service') on any function."""
    def decorator(func):
        cb = CircuitBreakerRegistry.get(service_name, config)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Usage:
@circuit_breaker("inventory-service", Config(failure_threshold=0.7))
def get_stock(item_id: str):
    return requests.get(f"http://inventory/stock/{item_id}").json()
```

---

## 8. Concurrency Race Condition — The Critical Code

This is the EXACT scenario interviewers ask about:

```python
# PROBLEM: Multiple threads hit OPEN→HALF_OPEN simultaneously
#
# Thread A: sees OPEN, checks timeout → elapsed! tries to transition
# Thread B: sees OPEN, checks timeout → elapsed! tries to transition
# Thread C: sees OPEN, checks timeout → elapsed! tries to transition
#
# Without protection: 3 semaphores created, 9 trial requests sent!

# SOLUTION: Lock inside transition_to() ensures only FIRST thread wins:
def transition_to(self, target: CircuitState):
    with self._lock:
        if self._state == target:
            return  # Thread B and C land here — state already changed
        self._state = target
        if target == CircuitState.HALF_OPEN:
            self._semaphore = threading.Semaphore(self.config.max_trial_requests)
```

```python
# PROBLEM: Metrics read-write race
#
# Consumer writes: records.append(new_failure)
# Caller reads: get_failure_rate() iterates records
#
# SOLUTION: Lock inside Metrics class (fine-grained, not global)
def get_failure_rate(self) -> float:
    with self._lock:       # ← same lock as record()
        self._evict()
        if not self._records:
            return 0.0
        failures = sum(1 for _, ok in self._records if not ok)
        return failures / len(self._records)
```

---

## 9. The Sliding Window — Alternative: Bucket-Based (Advanced)

If interviewer asks "what if you have 10,000 calls/sec? Deque won't scale."

```python
class BucketMetrics:
    """
    Divide the window into fixed buckets (e.g., 1-second granularity).
    Each bucket stores aggregated counts — O(1) record, O(buckets) query.
    """
    def __init__(self, window_seconds: int = 60, bucket_size_seconds: int = 1):
        self._window = window_seconds
        self._bucket_size = bucket_size_seconds
        self._num_buckets = window_seconds // bucket_size_seconds
        self._buckets: list[dict] = [
            {"success": 0, "failure": 0, "timestamp": 0}
            for _ in range(self._num_buckets)
        ]
        self._lock = threading.Lock()

    def record(self, success: bool):
        with self._lock:
            now = time.time()
            bucket_idx = int(now / self._bucket_size) % self._num_buckets
            bucket = self._buckets[bucket_idx]

            # Reset bucket if it's from a previous window rotation
            if now - bucket["timestamp"] >= self._window:
                bucket["success"] = 0
                bucket["failure"] = 0

            bucket["timestamp"] = now
            if success:
                bucket["success"] += 1
            else:
                bucket["failure"] += 1

    def get_failure_rate(self) -> float:
        with self._lock:
            now = time.time()
            total_success = 0
            total_failure = 0
            for bucket in self._buckets:
                if now - bucket["timestamp"] < self._window:
                    total_success += bucket["success"]
                    total_failure += bucket["failure"]
            total = total_success + total_failure
            if total == 0:
                return 0.0
            return total_failure / total
```

**When to mention this:** Only if interviewer asks about scale. Don't volunteer it
unless you have time — it adds complexity without core design value.

---

## 10. Putting It All Together — A Complete 30-Line Interview Sketch

If you're running low on time, this is the MINIMUM code that shows you can implement:

```python
class CircuitBreaker:
    def __init__(self, threshold=0.5, timeout=30, trials=3):
        self.state = "CLOSED"
        self.metrics = Metrics(window=60)
        self.threshold = threshold
        self.timeout = timeout
        self.max_trials = trials
        self._opened_at = 0
        self._trial_sem = None
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self._opened_at >= self.timeout:
                self._to("HALF_OPEN")
            else:
                raise Exception("OPEN")

        if self.state == "HALF_OPEN":
            if not self._trial_sem.acquire(blocking=False):
                raise Exception("HALF_OPEN full")

        try:
            result = func(*args, **kwargs)
            self.metrics.record(True)
            if self.state == "HALF_OPEN" and self._trials_done():
                self._to("CLOSED")
            return result
        except Exception as e:
            self.metrics.record(False)
            if self.state == "CLOSED" and self.metrics.get_failure_rate() >= self.threshold:
                self._to("OPEN")
            elif self.state == "HALF_OPEN":
                self._to("OPEN")
            raise

    def _to(self, target):
        with self._lock:
            if self.state == target:
                return
            self.state = target
            if target == "OPEN":
                self._opened_at = time.time()
            elif target == "HALF_OPEN":
                self._trial_sem = threading.Semaphore(self.max_trials)
            elif target == "CLOSED":
                self.metrics.reset()
```

**This is your safety net.** If you're running out of time and haven't coded yet,
write this compact version. It shows all the logic in one place — state checks,
transitions, semaphore, metrics, locking.

---

## What to Write vs What to Explain Verbally

| Code it | Explain verbally |
|---------|-----------------|
| State transition logic | "I'd use State Pattern — each state is a class" |
| Metrics sliding window | "For scale, I'd use bucket-based instead of deque" |
| Semaphore in HALF_OPEN | "This limits concurrent trials" |
| The lock placement | "Without this, Thread B could create a second semaphore" |
| Strategy interface (2 lines) | "Concrete impls would be ErrorRate, CountBased, SlowCall" |
| Registry double-checked locking | "Standard thread-safe singleton creation" |

In a 45-minute round, you have ~20 min for code. Prioritize: **state transitions > metrics >
concurrency > strategy interface > registry.**

---

## File Structure of This Implementation

```
circuit_breaker/
├── __init__.py              # Public API exports
├── enums.py                 # CircuitState enum (CLOSED, OPEN, HALF_OPEN)
├── config.py                # CircuitBreakerConfig dataclass
├── metrics.py               # Sliding window metrics (thread-safe)
├── strategy.py              # EvaluationStrategy + concrete strategies
├── states.py                # State classes + StateContext (transition logic)
├── circuit_breaker.py       # CircuitBreaker + Registry (entry point)
├── demo.py                  # Working demo with concurrent access
└── LLD_INTERVIEW_GUIDE.md   # This file
```

Each file = one responsibility. Each class = one reason to change.

---

## Final Thought

The difference between a 6/10 and a 9/10 in LLD interviews is NOT knowing more patterns.
It's **structured communication**, **proactive identification of edge cases**, and
**showing trade-off awareness** before the interviewer has to pull it out of you.

Practice narrating your thought process out loud. The design is in your head — the interview
tests whether you can EXPLAIN it clearly under pressure.
