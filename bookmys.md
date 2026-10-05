**The fix:** when you cut scope, cut it from the flow *and* the signatures in
the same breath. Or keep it and model it honestly behind an interface — which
is what this repo does, because the hold timeout only makes sense if something
slow sits between hold and confirm. Pick one; do not half-do both.
### M9 — Cancellation did the side effect before the record update
Covered in Part 5.4. **The fix:** record intent first, reversible side effect
last.
### The meta-lesson
Look at M1, M2, and M3 together. I knew holds needed owners. I knew checks
belong inside locks. I knew a method should mutate state. Every one of these
was a **verification failure**, not a knowledge gap.
So the practice that fixes the most: **after each method, re-read it once and
say out loud what it does.** Not what you meant it to do. What the lines say.
Thirty seconds per method, and it would have caught M1, M2, and three of the
five bugs in M3.
---
## 8. Transferring this to other problems
The same skeleton solves a surprising number of LLD questions. Fill in the
table and the design writes itself.
| Problem | Scarce resource | Owner (one lock) | The lease | TTL reason |
|---|---|---|---|---|
| Movie booking | seat per showtime | `Showtime` | seat hold | checkout time |
| Parking lot | spot per lot | `ParkingLot` or floor | spot reservation | arrival window |
| Hotel booking | room per date range | `RoomType` per night | tentative booking | checkout time |
| Ride hailing | driver | geo cell | driver assignment | accept window |
| Flight booking | seat per flight leg | `FlightLeg` | seat hold | payment time |
| Food delivery | courier | zone | order assignment | accept window |
| Inventory / cart | SKU stock | warehouse SKU | cart reservation | checkout time |
| Elevator | car | bank of elevators | trip assignment | — |
| Ticketmaster queue | ticket | event | queue token | session time |
| Library | copy of a book | branch | hold shelf | pickup window |
For every row the answers to the nine questions are structurally identical:
- **Q1 what must never happen** — two people get the same unit
- **Q3 owner** — the thing that scopes the resource in *time* or *place*
- **Q5 what's slow** — payment, user confirmation, or a third-party call
- **Q6 timeout** — lazy expiry inside the existing lock
- **Q9 what changes** — pricing and the external integration
### The three structural moves, stated generally
1. **State granularity = lock granularity.** Find the one object that owns the
   contended state. Give it the lock.
2. **Fast claim → slow work → fast commit, with a re-check at commit time.**
   Any time a slow operation sits in the middle of a transaction.
3. **Record intent before you do the irreversible thing.** Any time two things
   must stay in sync.
---
## 9. Rapid-fire answers
Practise saying these in under 30 seconds each.
**"How do you prevent double booking?"**
The check and the write happen in the same critical section, under one lock per
showtime. The second thread sees the seat is gone and gets a typed error.
Behind a database it's a conditional update with a row-count check.
**"Why one lock per showtime and not per seat?"**
The critical section is a set difference, microseconds, and payment is outside
it. The lock is already sharded on the axis that matters — different showtimes
never contend. Per-seat locking needs lock ordering to avoid deadlock and
benchmarks no faster. For a very large venue I'd shard by section.
**"What if payment takes longer than the hold?"**
`confirm` re-validates under the lock and raises, we refund the charge and tell
the user to start over. In production I'd set the TTL well above worst-case
gateway latency so it's rare, and keep the confirm-or-refund as the backstop.
**"How do holds expire?"**
Lazily, inside the lock every operation already takes. No sweeper thread, so
there's no thread that can race a confirm. A sweeper is a memory optimisation,
not a correctness need.
**"What if the process crashes mid-booking?"**
The hold has a timestamp, so it expires on its own. That's the advantage of a
lease over a mutex — the claim is data and survives restart, or dies cleanly on
its own schedule.
**"Add holiday pricing."**
New class implementing `PricingStrategy`. Nothing existing changes. If it needs
to combine with weekend pricing, it's a decorator that wraps the other one.
**"Add a waitlist."**
A `WaitlistManager` keyed by showtime holding a queue per show. The
cancellation path already has a single place where seats return to AVAILABLE —
that's the hook. It notifies the next user; it doesn't auto-book, so the freed
seat still goes through the normal hold-and-pay flow.
**"Book four adjacent seats."**
A seat-allocation strategy that scans each row for a run of consecutive
available seats and returns the list. The booking path is unchanged because it
only ever receives a final list of seat ids.
**"How would this work across multiple servers?"**
The seat state moves to Redis or the database. The hold becomes a row with an
`expires_at`, claimed with a conditional write — `SET NX PX` per seat wrapped
in a Lua script so the group stays atomic, or an `UPDATE ... WHERE
status='AVAILABLE'` with a row-count check. The logic is identical; the lock
just moves out of process.
**"What's your test for correctness?"**
The three-state invariant: every seat is in exactly one of available, held,
booked, and no seat is lost or invented. Plus a thread test that releases 40
threads from a barrier onto the same two seats and asserts exactly one winner.
---
## 10. Full code
Single-file version, verified to run. `python3 interview_single_file.py`.
The multi-file version in this folder is the same design with two
interchangeable state stores, 39 tests, a benchmark, and heavier comments.
### File map
| File | What it is for |
|---|---|
| `interview_single_file.py` | this code, runnable, what you'd write in 45 min |
| `domain.py` | entities, enums, exceptions |
| `seat_state.py` | all the concurrency; two store implementations |
| `showtime.py` | the bookable unit |
| `booking_service.py` | the hold → pay → confirm orchestration |
| `catalog.py` | primary stores and secondary indexes |
| `pricing.py` / `payment.py` | the two strategies |
| `cinema.py` | the facade |
| `test_booking.py` | 39 tests including the three races |
| `benchmark.py` | per-showtime vs per-seat locking, measured |
| `lock_vs_lease.py` | runs all five of my Worker bugs so you can see them |
| `my_original_code_annotated.py` | my interview code, annotated line by line |
### The code
```python
"""Movie ticket booking -- the whole design in one file."""
from __future__ import annotations
import random
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Protocol, Sequence, Set, Tuple
# =============================================================================
# 1. ENUMS
# =============================================================================
class SeatType(Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    RECLINER = "RECLINER"
class BookingStatus(Enum):
    # No CREATED state: the Hold plays that role before payment succeeds.
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
class PaymentStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
# =============================================================================
# 2. ERRORS -- one per distinct caller reaction
# =============================================================================
class BookingError(Exception):
    """Base for every failure this system produces."""
class UnknownSeatError(BookingError):
    """Seat id does not exist. Bad input, not retryable."""
class SeatUnavailableError(BookingError):
    """Seat is held or booked. Retryable with different seats."""
    def __init__(self, seat_ids):
        self.seat_ids = sorted(seat_ids)
        super().__init__(f"seats unavailable: {self.seat_ids}")
class HoldExpiredError(BookingError):
    """Checkout outlived the TTL. Caller must start over."""
class ShowtimeNotFoundError(BookingError):
    pass
class BookingNotFoundError(BookingError):
    pass
class PaymentFailedError(BookingError):
    pass
# =============================================================================
# 3. ENTITIES -- all immutable except Reservation.status
# =============================================================================
@dataclass(frozen=True)
class Seat:
    """A seat's AVAILABILITY is not a property of the seat. It is a property of
    a (seat, showtime) pair, so it is not stored here."""
    seat_id: str
    row: str
    number: int
    seat_type: SeatType
@dataclass(frozen=True)
class Movie:
    movie_id: str
    title: str
    duration_mins: int = 120
@dataclass
class Theater:
    theater_id: str
    name: str
    seats: Dict[str, Seat] = field(default_factory=dict)
    @classmethod
    def with_grid(cls, theater_id, name, rows, seats_per_row, premium_rows=()):
        premium = set(premium_rows)
        theater = cls(theater_id=theater_id, name=name)
        for row in rows:
            for number in range(1, seats_per_row + 1):
                seat_id = f"{row}{number:02d}"  # zero-padded: "A01" sorts right
                theater.seats[seat_id] = Seat(
                    seat_id=seat_id,
                    row=row,
                    number=number,
                    seat_type=SeatType.PREMIUM if row in premium else SeatType.REGULAR,
                )
        return theater
@dataclass(frozen=True)
class Hold:
    """A temporary claim. NOT a mutex: it has an owner and an expiry, lives for
    minutes, and is handed back to the caller."""
    hold_id: str
    showtime_id: str
    user_id: str
    seat_ids: Tuple[str, ...]
    expires_at: datetime
@dataclass(frozen=True)
class Payment:
    payment_id: str
    amount_cents: int  # CENTS. Never float.
    status: PaymentStatus
    transaction_ref: str
@dataclass
class Reservation:
    confirmation_id: str
    showtime_id: str
    user_id: str
    seat_ids: List[str]
    amount_cents: int
    status: BookingStatus
    created_at: datetime
    payment: Optional[Payment] = None
    cancelled_at: Optional[datetime] = None
# =============================================================================
# 4. PRICING -- Strategy. Prices are DATA, pricing is an ALGORITHM.
# =============================================================================
class PricingStrategy(Protocol):
    def total_cents(
        self, seats: Sequence[Seat], price_by_type: Dict[SeatType, int], start_time: datetime
    ) -> int: ...
class BasePricing:
    def total_cents(self, seats, price_by_type, start_time) -> int:
        return sum(price_by_type[s.seat_type] for s in seats)
class WeekendPricing:
    """Reads start_time, not now(): the price depends on when the SHOW is."""
    def __init__(self, surcharge_pct: int = 20):
        self._pct = surcharge_pct
    def total_cents(self, seats, price_by_type, start_time) -> int:
        base = sum(price_by_type[s.seat_type] for s in seats)
        if start_time.weekday() >= 5:
            return base + (base * self._pct) // 100
        return base
class DemandPricing:
    """DECORATOR: wraps any other strategy so surcharges compose."""
    def __init__(self, inner: PricingStrategy, occupancy_fn, surcharge_pct: int = 30):
        self._inner = inner
        self._occupancy_fn = occupancy_fn
        self._pct = surcharge_pct
    def total_cents(self, seats, price_by_type, start_time) -> int:
