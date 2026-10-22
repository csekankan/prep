# My LLD Mistakes + Cheatsheet

Built from 3 of my designs: **BookMyShow**, **File System**, **Logging Library**.
Same 6 patterns repeat in all three. Fix the patterns, not the individual bugs.

---

## Quick index

| # | Pattern | Seen in |
|---|---|---|
| 1 | Not verifying code after writing it | All 3 |
| 2 | Locks without knowing what they protect | All 3 |
| 3 | Method / class in the wrong place | Logging, File System |
| 4 | Wrong keys, stored data goes stale | BookMyShow, File System |
| 5 | Wrong order of state changes | BookMyShow, File System |
| 6 | Vague API (bool + print, no return type) | All 3 |

---

## Pattern 1 — Not verifying code after writing it

**Biggest one. Not a knowledge gap, a habit gap.**

### Example A: computed but never used (BookMyShow)

❌ Wrong
```python
def getAvailableSlot(movieId):
    res = []
    for slot in slots.get(movieId, []):
        if slot.isSeatsAvaiable():
            res.append(slot)
    # forgot return -> caller gets None
```

**Why wrong:** work is done, result thrown away.

✅ Correct
```python
def get_available_showtimes(self, movie_id: str) -> list[Showtime]:
    return [s for s in self._showtimes_for(movie_id) if s.has_available_seats()]
```

### Example B: success path never changes state (BookMyShow)

❌ Wrong
```python
try:
    for seat in seatIds:
        if seat not in avaiableSeats:
            return False
    occupySeats(seatIds)      # calls ITSELF -> infinite recursion, nothing booked
    return True
```

**Why wrong:** the core operation of the system is a no-op.

✅ Correct
```python
with self._lock:
    taken = [s for s in seat_ids if s not in self._available]
    if taken:
        raise SeatUnavailableError(taken)
    for s in seat_ids:
        self._available.discard(s)      # <- the actual state change
```

### Example C: wrong field updated (File System)

❌ Wrong
```python
def setParent(self, parent):
    self.parent = parent
    self.name = parent.path + "/" + self.name    # changed NAME, not PATH
```

**Why wrong:** the name becomes `"/test/test"`, and the path stays old.

### Self-check after every method
1. Does this **actually change state**?
2. What does the caller **receive**, and which line produced it?
3. Is any variable **assigned but never read**? → that's the bug.
4. Is every method I call **actually implemented**? (`list()` was called but never written)

---

## Pattern 2 — Locks without knowing what they protect

### Example A: check before the lock (BookMyShow)

❌ Wrong
```python
for seat in seatIds:                 # check (no lock)
    if seat not in avaiableSeats:
        return False
for seat in seatIds:                 # lock (later)
    seatLock[seat].acquire()
```

**Why wrong:** between check and lock, another thread books the seat.

✅ Correct → see **Cheatsheet 1: check-and-set**

### Example B: lock granularity ≠ state granularity (BookMyShow)

❌ Wrong
```python
seatLock: dict[seatId, Lock]    # one lock per seat
avaiableSeats: set              # but ONE shared set
```

**Why wrong:** two threads holding different seat locks both mutate the same set. The locks protect nothing.

✅ Correct: one lock per showtime guarding that showtime's set. Simpler and usually faster.

### Example C: using a Lock as a 10-minute seat hold (BookMyShow)

❌ Wrong
```python
lock.acquire()
self.worker.addLock(seatid, slotid, lock)   # worker thread releases it later
```

**Why wrong:**
- A lock is held for **microseconds** by **one thread**.
- A hold lives for **minutes**, belongs to a **user**, must be **visible** to others.
- The worker thread releases a lock it never acquired → crash.

✅ Correct → see **Cheatsheet 2: hold with TTL**

### Example D: lock dict KeyError + keyed by path (File System)

❌ Wrong
```python
self._lock: Dict[str, RLock] = {}
with self._lock[parentPath]:        # KeyError: never created
```

**Why wrong:**
- Key never inserted → crash.
- The dict itself isn't protected → two threads can create two different locks.
- Path changes after `move` → same folder, different lock.

✅ Correct: one tree-wide lock (simple, correct). Optimize only if asked.
```python
self._lock = threading.RLock()

def create_file(self, path, name, content):
    with self._lock:
        parent = self._resolve_folder(path)
        ...
```

### Example E: slow I/O under the lock (Logging)

❌ Wrong
```python
with source_lock:
    for d in destinations:
        d.write(msg)       # disk/network I/O while holding the lock
```

**Why wrong:** every app thread waits on the slowest destination.

✅ Correct → see **Cheatsheet 3: producer-consumer queue**

### Before adding any lock, answer:
1. **What data** does this lock protect?
2. Are the **check and the write** both inside it?
3. Is anything **slow** (I/O, payment, network) inside it? → move it out.

---

## Pattern 3 — Method / class in the wrong place

### Example A: subclass for a value (Logging)

❌ Wrong
```
DebugMessage, InfoMessage, WarnMessage ... inherits ILogMessage
```

**Why wrong:** they all behave the same. Only the level value differs.

✅ Correct
```python
@dataclass(frozen=True)
class LogRecord:
    level: LogLevel
    message: str
```

> Rule: **different value → field. Different behavior → subclass.**

### Example B: wrong owner (Logging)

❌ Wrong
```
ILogMessage.formatMessage(message, IFormatter)
```

**Why wrong:** the file wants JSON and the console wants text. The same message can't choose both.

✅ Correct: the destination owns the formatter → see **Cheatsheet 4: template method**

> Rule: ask *"if this rule changes, which object do I edit?"* That object owns it.

### Example C: common method only on a subclass (File System)

❌ Wrong
```python
class Folder(FileSystem):
    def getType(self): ...       # only here

# move():
d.getType()                     # crashes when d is a File
```

**Why wrong:** callers treat everything as `FileSystem`, so the method must exist there.

✅ Correct
```python
class Node(ABC):
    @abstractmethod
    def is_dir(self) -> bool: ...

class File(Node):
    def is_dir(self): return False

class Folder(Node):
    def is_dir(self): return True
```

### Example D: root is the abstract type (File System)

❌ Wrong
```python
self.root = FileSystem("", "/", None, FileSystemType.DIRECTORY)   # has no getFolder()
```

✅ Correct
```python
self.root = Folder(name="", parent=None)
```

---

## Pattern 4 — Wrong keys, stored data goes stale

### Example A: human-readable key + single value (BookMyShow)

❌ Wrong
```python
slots: Dict[movieTitle, Slot]
```

**Why wrong:**
- Two movies titled "The Mummy" → one overwrites the other.
- One `Slot` per movie → the 6pm show overwrites the 3pm show.

✅ Correct → see **Cheatsheet 5: primary store + secondary index**

### Example B: keyed by user, looked up by booking id (BookMyShow)

❌ Wrong
```python
reservations: Dict[userId, List[Reservation]]
# cancel(reservation_id) -> scan the whole list
```

**Why wrong:** you gave the user a booking id, but you can't look up by it.

> Rule: **primary key = the id you hand to the caller.**

### Example C: storing derived data (File System)

❌ Wrong
```python
class FileSystem:
    self.path = path        # stored on every node
```

**Why wrong:** after `move("/a", "/b")`, folder `a` and **every file inside it** still have the old path.

✅ Correct → see **Cheatsheet 6: tree with derived path**

### Example D: separate dicts allow name clash (File System)

❌ Wrong
```python
self.files = {}
self.folders = {}       # a file "x" and a folder "x" can coexist
```

✅ Correct
```python
self.children: dict[str, Node] = {}
```

### Ask of every dict
1. What do I **look this up by**? → that's the key.
2. Can the key **collide**? → if yes, it's not a key.
3. Can there be **more than one** value? → value is a list.
4. Can I **compute** this instead of storing it? → don't store it.

---

## Pattern 5 — Wrong order of state changes

### Example A: read old value after overwriting it (File System)

❌ Wrong
```python
s.setParent(d)
d.addFile(s)
s.getParent().removeFile(s)      # getParent() is now d -> removes from NEW parent
```

**Why wrong:** you destroyed the old value before using it.

✅ Correct
```python
old_parent = s.parent            # read FIRST
old_parent.children.pop(s.name)
d.children[s.name] = s
s.parent = d
```

### Example B: using a return value that doesn't exist (File System)

❌ Wrong
```python
parent = s.setParent(d)          # setParent returns None
parent.removeFolder(s)           # AttributeError
```

### Example C: cleanup only on one failure path (BookMyShow)

❌ Wrong
```python
if payment.makePayment(amount):
    ...
else:
    slot.releaseSeats(seats)     # only when payment returns False
# if makePayment THROWS -> seats stuck forever
```

✅ Correct → see **Cheatsheet 7: compensate on every failure**

### Example D: side effect before the record (BookMyShow cancel)

❌ Wrong
```python
slot.releaseSeats(seats)         # seats free
del userReservations[i]          # if this fails, the booking still looks active
```

**Why wrong:** someone books a seat another person still thinks they own.

✅ Correct: **record intent first, side effect last.**
```python
booking.status = BookingStatus.CANCELLED
showtime.release(booking.seat_ids)
```

---

## Pattern 6 — Vague API

### Example A: bool + print (BookMyShow)

❌ Wrong
```python
if not slot.occupySeats(seats):
    print('Not possible to occupy all seats')
    return False
```

**Why wrong:** "seat taken", "seat doesn't exist", "payment failed" all return `False`. The caller can't react differently.

✅ Correct → see **Cheatsheet 8: exceptions + signatures**

### Example B: create returns bool (BookMyShow)

❌ Wrong
```python
def reserveSeat(...):
    ...
    return True          # user never gets a booking id to cancel later
```

✅ Correct
```python
def reserve(...) -> Booking:
    ...
    return booking
```

### Example C: awkward call (Logging)

❌ Wrong
```python
addLog(source, WarnMessage("disk full"))
```

✅ Correct
```python
log.warn("disk full")
```

### Example D: name mismatch (File System)
`create_file` in the class, `createFile` in `main`. Write signatures first, then code against them.

---

# Cheatsheet code

Copy-paste templates for the patterns above.

## 1. Check-and-set under one lock

```python
import threading


class Showtime:
    def __init__(self, seat_ids: set[str]):
        self._all = frozenset(seat_ids)
        self._available = set(seat_ids)
        self._lock = threading.Lock()

    def book(self, seat_ids: list[str]) -> None:
        unknown = set(seat_ids) - self._all      # immutable -> safe outside lock
        if unknown:
            raise UnknownSeatError(sorted(unknown))

        with self._lock:                          # check + write in ONE block
            taken = [s for s in seat_ids if s not in self._available]
            if taken:
                raise SeatUnavailableError(taken)
            self._available.difference_update(seat_ids)
```

## 2. Hold with TTL (lease, not a lock) + lazy expiry

```python
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Hold:
    hold_id: str
    user_id: str
    seat_ids: tuple[str, ...]
    expires_at: datetime


class Showtime:
    HOLD_TTL = timedelta(minutes=10)

    def __init__(self, seat_ids: set[str]):
        self._available = set(seat_ids)
        self._holds: dict[str, Hold] = {}
        self._booked: set[str] = set()
        self._lock = threading.Lock()

    def _expire_holds(self) -> None:              # caller must hold self._lock
        now = datetime.now()
        for hold_id, hold in list(self._holds.items()):
            if hold.expires_at <= now:            # "expiry is in the past"
                del self._holds[hold_id]
                self._available.update(hold.seat_ids)

    def hold(self, user_id: str, seat_ids: list[str]) -> Hold:
        with self._lock:
            self._expire_holds()
            taken = [s for s in seat_ids if s not in self._available]
            if taken:
                raise SeatUnavailableError(taken)
            self._available.difference_update(seat_ids)
            hold = Hold(str(uuid.uuid4()), user_id, tuple(seat_ids),
                        datetime.now() + self.HOLD_TTL)
            self._holds[hold.hold_id] = hold
            return hold

    def confirm(self, hold_id: str) -> None:
        with self._lock:
            self._expire_holds()
            hold = self._holds.pop(hold_id, None)
            if hold is None:
                raise HoldExpiredError(hold_id)
            self._booked.update(hold.seat_ids)

    def release(self, hold_id: str) -> None:
        with self._lock:
            hold = self._holds.pop(hold_id, None)
            if hold is not None:
                self._available.update(hold.seat_ids)
```

> No background thread needed. Expired holds are cleaned inside the lock you already hold.

## 3. Producer-consumer queue (keep slow I/O off caller threads)

```python
import queue
import threading

_STOP = object()


class AsyncWorker:
    def __init__(self, handle, capacity: int = 10_000):
        self._handle = handle
        self._queue: queue.Queue = queue.Queue(maxsize=capacity)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, item) -> None:
        self._queue.put(item)             # fast; blocks only if full (backpressure)

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is _STOP:
                return
            try:
                self._handle(item)
            except Exception as exc:      # one bad item must not kill the worker
                print(f"worker error: {exc}")

    def shutdown(self) -> None:
        self._queue.put(_STOP)
        self._thread.join()               # drains everything queued before STOP
```

> One queue + one consumer = order preserved.

## 4. Template method (common logic in base, varying part in subclass)

```python
from abc import ABC, abstractmethod


class Destination(ABC):
    def __init__(self, min_level: LogLevel, formatter: Formatter):
        self.min_level = min_level
        self.formatter = formatter

    def emit(self, record: LogRecord) -> None:     # same for every destination
        if record.level < self.min_level:
            return
        self._write(self.formatter.format(record))

    @abstractmethod
    def _write(self, line: str) -> None: ...       # only this varies


class ConsoleDestination(Destination):
    def _write(self, line: str) -> None:
        print(line)
```

## 5. Primary store + secondary index

```python
from collections import defaultdict


class BookingStore:
    def __init__(self):
        self._by_id: dict[str, Booking] = {}                          # primary
        self._ids_by_user: dict[str, list[str]] = defaultdict(list)   # secondary

    def add(self, booking: Booking) -> None:
        self._by_id[booking.booking_id] = booking
        self._ids_by_user[booking.user_id].append(booking.booking_id)

    def get(self, booking_id: str) -> Booking | None:
        return self._by_id.get(booking_id)                            # O(1)

    def for_user(self, user_id: str) -> list[Booking]:
        return [self._by_id[i] for i in self._ids_by_user.get(user_id, [])]
```

> `defaultdict(list)` avoids the `KeyError` on a user's first booking.

## 6. Tree with derived path (File System)

```python
import threading
from abc import ABC, abstractmethod


class Node(ABC):
    def __init__(self, name: str, parent: "Folder | None"):
        self.name = name
        self.parent = parent

    @property
    def path(self) -> str:                  # computed, never stale after move
        if self.parent is None:
            return "/"
        parent_path = self.parent.path
        return f"{parent_path.rstrip('/')}/{self.name}"

    @abstractmethod
    def is_dir(self) -> bool: ...


class File(Node):
    def __init__(self, name: str, parent: "Folder", content: str = ""):
        super().__init__(name, parent)
        self.content = content

    def is_dir(self) -> bool:
        return False


class Folder(Node):
    def __init__(self, name: str, parent: "Folder | None"):
        super().__init__(name, parent)
        self.children: dict[str, Node] = {}    # one dict -> no name clash

    def is_dir(self) -> bool:
        return True


class FileSystem:
    def __init__(self):
        self.root = Folder("", None)
        self._lock = threading.RLock()

    def _resolve(self, path: str) -> Node:
        node: Node = self.root
        for part in (p for p in path.split("/") if p):    # handles "/", "//"
            if not isinstance(node, Folder) or part not in node.children:
                raise PathNotFoundError(path)
            node = node.children[part]
        return node

    def _resolve_folder(self, path: str) -> Folder:
        node = self._resolve(path)
        if not isinstance(node, Folder):
            raise NotADirectoryError(path)
        return node

    def move(self, src: str, dest: str) -> None:
        with self._lock:
            node = self._resolve(src)
            target = self._resolve_folder(dest)
            if node is self.root:
                raise InvalidMoveError("cannot move root")

            cur: Folder | None = target                    # cycle check: walk UP
            while cur is not None:
                if cur is node:
                    raise InvalidMoveError("cannot move folder into itself")
                cur = cur.parent

            if node.name in target.children:
                raise AlreadyExistsError(node.name)

            old_parent = node.parent                       # read BEFORE mutating
            del old_parent.children[node.name]
            target.children[node.name] = node
            node.parent = target

    def list(self, path: str) -> list[str]:
        with self._lock:
            return sorted(self._resolve_folder(path).children)
```

## 7. Compensate on every failure

```python
def book(self, user_id: str, showtime: Showtime, seat_ids: list[str]) -> Booking:
    hold = showtime.hold(user_id, seat_ids)
    try:
        amount = self._pricing.total(showtime, hold.seat_ids)
        receipt = self._payments.charge(user_id, amount)
        showtime.confirm(hold.hold_id)
    except Exception:
        showtime.release(hold.hold_id)     # every failure path, not one else-branch
        raise
    booking = Booking(new_id(), user_id, hold.seat_ids, receipt.id)
    self._store.add(booking)
    return booking                          # return what you created
```

## 8. Specific exceptions + full signatures (write BEFORE bodies)

```python
class BookingError(Exception): ...
class UnknownSeatError(BookingError): ...          # 400: bad input
class SeatUnavailableError(BookingError): ...      # 409: retry other seats
class HoldExpiredError(BookingError): ...          # 410: start over
class PaymentFailedError(BookingError): ...        # 402: retry payment
class BookingNotFoundError(BookingError): ...      # 404


class BookingService:
    def book(self, user_id: str, showtime_id: str, seat_ids: list[str]) -> Booking:
        """Raises UnknownSeatError, SeatUnavailableError, PaymentFailedError."""

    def cancel(self, user_id: str, booking_id: str) -> Booking:
        """Idempotent. Raises BookingNotFoundError (also when not owned by user)."""
```

> One exception type per **different caller reaction**.

## 9. Idempotent + owner-checked cancel

```python
def cancel(self, user_id: str, booking_id: str) -> Booking:
    with self._lock:
        booking = self._store.get(booking_id)
        if booking is None or booking.user_id != user_id:
            raise BookingNotFoundError(booking_id)    # same error -> ids can't be probed
        if booking.status is BookingStatus.CANCELLED:
            return booking                            # double-click safe
        booking.status = BookingStatus.CANCELLED      # intent first
    self._showtimes[booking.showtime_id].release_booked(booking.seat_ids)   # effect last
    return booking
```

## 10. Safely acquiring multiple locks (only if you really need fine-grained)

```python
from contextlib import contextmanager


@contextmanager
def acquire_all(locks_by_key: dict[str, threading.Lock], keys: list[str]):
    acquired = []
    try:
        for key in sorted(set(keys)):        # fixed order -> no deadlock
            locks_by_key[key].acquire()
            acquired.append(key)             # track what you actually got
        yield
    finally:
        for key in reversed(acquired):       # release ONLY what you got
            locks_by_key[key].release()
```

---

# Process (use every time)

1. **Client code first** — `log.warn("x")`, `fs.move("/a", "/b")`, `svc.book(user, show, seats)`
2. **Trace one call** end to end
3. **Fields** of each class
4. **Full signatures** with return types + exceptions, no bodies
5. **Bodies** for the main 2–3 methods
6. **Concurrency** — which data each lock protects, what's slow
7. **Run the checklist** below

# Checklist before saying "done"

- [ ] Every method actually changes the state it should
- [ ] Every computed variable is used or returned
- [ ] Every method I call exists on that object's class
- [ ] Check and write are inside the **same** lock
- [ ] Nothing slow (I/O, payment) runs while holding a lock
- [ ] Old values are read **before** mutating
- [ ] Cleanup is in `except` / `finally`, not one `else`
- [ ] Every dict key is an id that can't collide
- [ ] No stored value that could be computed instead
- [ ] Every signature has a return type and listed exceptions
- [ ] Create methods return the created object, not `True`

# Concepts to study (in order)

1. **Dry-running my own code** — habit, catches ~40% of my bugs
2. **Concurrency** — critical section, check-then-act race, lock granularity, lock vs lease, producer-consumer
3. **Class responsibility** — field vs subclass, base-class methods, who owns the data
4. **Data modeling** — key by id, secondary indexes, derived vs stored data
5. **State-change ordering** — read old first, intent first, compensate in finally
6. **API contracts** — return types, specific exceptions, return created object
