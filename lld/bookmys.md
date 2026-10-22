# LLD Guide — Movie Ticket Booking

How to actually think through this in a real interview, the design that comes
out of it, the patterns you can reuse on other problems, my own mistakes, and
the full working code at the end.

Read Parts 1 and 2 first. They are the ones you use under pressure.

---

## Contents

1. [What actually happens in the room](#1-what-actually-happens-in-the-room)
2. [The five questions](#2-the-five-questions)
3. [How to find the classes and the methods](#3-how-to-find-the-classes-and-the-methods)
4. [The concurrency chapter](#4-the-concurrency-chapter)
5. [The booking flow and every way it can fail](#5-the-booking-flow-and-every-way-it-can-fail)
6. [Patterns you can reuse](#6-patterns-you-can-reuse)
7. [My mistakes: what, why, and the fix](#7-my-mistakes-what-why-and-the-fix)
8. [Transferring this to other problems](#8-transferring-this-to-other-problems)
9. [Rapid-fire answers](#9-rapid-fire-answers)
10. [Full code](#10-full-code)

---

## 1. What actually happens in the room

The interviewer says: *"Design a movie ticket booking system."*

Here is what goes through your head, in order, with what you actually say.

### Minute 0 — before you say anything

Don't start listing classes. Start by finding the hard part.

Ask yourself one question: **what would be a disaster here?**

> *Two people show up and sit in the same seat.*

That's it. That is the whole problem. Movies, cinemas, search, prices — those
are just data. The thing that is actually hard is making sure one seat goes to
one person.

Now you know what you are building, and you know what to spend your 45 minutes
on.

### Minutes 0–5 — ask four questions, not fifteen

You are not gathering requirements for real. You are steering the problem
toward the part you want to talk about. Ask the one that opens the door:

> **You:** "What happens if two users pick the same seat at the same moment?"
>
> **Them:** "Good question. The seats should be held for a short time while the
> user pays. If they don't pay in time, the seats go back."

They just handed you the entire design. Say thank you internally. Three more:

> "Does the user pick specific seats, or does the system assign them?"
> — *specific seats, so I need all-or-nothing for a group*
>
> "Can I assume an external payment gateway?"
> — *yes, so payment is slow and can fail, but I keep it in the flow*
>
> "Single server, or distributed?"
> — *I'll design in-memory and tell you what changes behind a database*

**Stop asking questions after four.** Longer lists make you look like you're
stalling.

### Minutes 5–10 — nouns on the board, fast

List the obvious things. Don't agonise.

```
Movie   Theater   Seat   Showtime   User   Booking   Payment
```

Now the one decision in this phase that actually matters. Ask yourself:

> *Where does "this seat is taken" live?*

The tempting answer is `Seat.status`. **It's wrong**, and here is the thirty
seconds of thinking that shows why:

> *Seat A01 exists in the room. The 6pm show and the 9pm show use the same
> room, so they use the same A01. If I book A01 at 6pm and set its status to
> BOOKED, the 9pm show now thinks A01 is gone. Same object, two meanings.*

So availability is not a property of the seat. It is a property of the
**pair** — this seat, that showtime. And since `Showtime` is the thing you book,
`Showtime` owns it.

Say this out loud, because it is the sentence that separates you from the
candidates who put `status` on `Seat`:

> "A seat doesn't have a status. The same physical seat is free at 6pm and
> taken at 9pm, so availability belongs to the Showtime, not the Seat."

**What you actually type.** Five minutes, no cleverness. Everything is frozen,
because if it can't change you never have to lock it:

```python
class SeatType(Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"

@dataclass(frozen=True)
class Seat:
    seat_id: str          # "A01"
    row: str
    number: int
    seat_type: SeatType
    # NO status field -- that's the whole point

@dataclass(frozen=True)
class Movie:
    movie_id: str
    title: str

@dataclass
class Theater:
    theater_id: str
    name: str
    seats: Dict[str, Seat]      # seat_id -> Seat

@dataclass
class Reservation:
    confirmation_id: str        # what the USER walks away with
    showtime_id: str
    user_id: str
    seat_ids: List[str]
    amount_cents: int           # cents, not float
    status: BookingStatus
```

Two things an interviewer notices here, and they cost you nothing:

- **`amount_cents: int`**, not `float`. `0.1 + 0.2 != 0.3` in binary floating
  point, so money totals drift. Every published solution for this problem uses
  `double`. Say "integer cents" and move on.
- **`frozen=True`** on everything immutable. It makes "what needs a lock" a
  question with an obvious answer: only the mutable things.

### Minutes 10–15 — find the one thing that needs a lock

Go down your noun list and ask of each: *does more than one request write to
this at the same time?*

```
Movie      no — written once at setup
Theater    no — written once at setup
Seat       no — it's just row/number/type now
Showtime   YES — every booking writes seat availability     <-- the whole game
Booking    written once per booking, each one separate
```

One line of shared mutable state. Say it:

> "The only contended state in the system is seat availability per showtime.
> That's where all the concurrency lives, so that's where the lock goes —
> one per showtime."

Now write the fields, and write the lock **first**, above them, so you
physically cannot forget what it covers:

```python
self._lock = RLock()                 # guards everything below
self._available: Set[str]
self._booked:    Set[str]
self._holds:     Dict[str, Hold]
self._hold_by_seat: Dict[str, str]
```

### Minutes 15–30 — the part they're grading

This is where most of your time should go. Three methods: `hold`, `confirm`,
`release`.

Before writing `hold`, one more piece of thinking. The interviewer said *"held
for a short time while the user pays."* That word "hold" is doing a lot of
work. Ask yourself:

> *What does a hold need to know?*
>
> Which seats. Who holds them. When it runs out.

A `threading.Lock` can store **none of those three**. So a hold is not a lock —
it's data:

```python
@dataclass(frozen=True)
class Hold:
    hold_id: str
    showtime_id: str
    user_id: str                  # WHO   -- a mutex can't store this
    seat_ids: Tuple[str, ...]     # WHAT
    expires_at: datetime          # WHEN  -- a mutex can't store this either
```

That realisation is the single highest-value thing in this interview, and it's
why I'll spend all of Part 4.1 on it. The lock guards the dictionary these live
in. It is not the hold itself.

**Now `hold()`.** One rule in your head: the check and the write go inside the
same `with self._lock:`. Not before it.

```python
def hold(self, seat_ids, user_id, ttl) -> Hold:
    requested = sorted(set(seat_ids))

    # Seat EXISTENCE comes from immutable theater data, so checking it
    # outside the lock is safe. AVAILABILITY is mutable -- that goes inside.
    unknown = sorted(set(requested) - self._all_seat_ids)
    if unknown:
        raise UnknownSeatError(f"no such seats: {unknown}")

    with self._lock:
        self._expire_holds()

        # ***** CHECK AND WRITE, SAME CRITICAL SECTION *****
        taken = [s for s in requested if s not in self._available]
        if taken:
            raise SeatUnavailableError(taken)   # nothing mutated yet

        hold = Hold(uuid.uuid4().hex, self.showtime_id, user_id,
                    tuple(requested), datetime.now() + ttl)
        self._holds[hold.hold_id] = hold
        for seat_id in requested:
            self._available.discard(seat_id)
            self._hold_by_seat[seat_id] = hold.hold_id
        return hold
```

Point at the free win while you write it:

> "Because I check everything before I mutate anything, all-or-nothing for a
> group of seats falls out for free. There's no rollback code."

**Then `confirm()`.** The trick is `pop`, which is lookup and removal in one
step:

```python
def confirm(self, hold) -> List[str]:
    with self._lock:
        self._expire_holds()
        live = self._holds.pop(hold.hold_id, None)
        if live is None:
            raise HoldExpiredError(hold.hold_id)   # expired, or already used
        for seat_id in live.seat_ids:
            self._hold_by_seat.pop(seat_id, None)
            self._booked.add(seat_id)
        return list(live.seat_ids)
```

Two sentences while you type it:

> "`pop` means a replayed confirm raises instead of double-booking. And because
> the hold is gone before I release the lock, the expiry sweep can never touch
> a seat that's already BOOKED."

**Then `release_hold()`**, which must be idempotent because the error path will
call it on holds that may already be gone:

```python
def release_hold(self, hold) -> None:
    with self._lock:
        live = self._holds.pop(hold.hold_id, None)
        if live is None:
            return                     # already expired or released
        for seat_id in live.seat_ids:
            # only clear if it still points at THIS hold
            if self._hold_by_seat.get(seat_id) == live.hold_id:
                self._hold_by_seat.pop(seat_id, None)
                self._available.add(seat_id)
```

**And expiry — lazy, no background thread:**

```python
def _expire_holds(self) -> None:
    """Caller must already hold self._lock."""
    now = datetime.now()
    for hold_id, hold in list(self._holds.items()):   # list() = snapshot
        if hold.expires_at <= now:
            del self._holds[hold_id]
            for seat_id in hold.seat_ids:
                if self._hold_by_seat.get(seat_id) == hold_id:
                    self._hold_by_seat.pop(seat_id, None)
                    self._available.add(seat_id)
```

Call it at the top of every method that reads or writes state. Say why:

> "No sweeper thread, so there's no thread that can race my own confirm. An
> expired hold nobody has looked at yet is unobservable, so cleaning it up at
> read time is enough."

### Minutes 30–38 — the flow, said as a sentence first

Before writing `book()`, say the order out loud:

> "Hold the seats, price them, charge the card, confirm, record. The charge
> sits in the middle with **no lock held**, because the gateway takes hundreds
> of milliseconds and I'm not serialising the whole cinema on a third party.
> That's the entire reason hold and confirm are separate operations."

Then write it:

```python
def book(self, showtime_id, seat_ids, user_id, payment=None) -> Reservation:
    gateway  = payment or self._default_payment
    showtime = self._catalog.get_showtime(showtime_id)

    # 1. claim. If this raises, nothing has happened -- nothing to undo.
    hold = showtime.hold_seats(seat_ids, user_id)
    try:
        # 2. price. cheap, pure, no lock.
        amount = showtime.price_for(hold.seat_ids)

        # 3. charge. SLOW. NO LOCK HELD.
        receipt = gateway.pay(user_id, amount)

        # 4. confirm. raises if the gateway outlived the TTL.
        try:
            confirmed = showtime.confirm_hold(hold)
        except HoldExpiredError:
            gateway.refund(receipt)      # we charged for seats we lost
            raise
    except Exception:
        showtime.release_hold(hold)      # compensate...
        raise                            # ...then let the caller see it

    # 5. record. only NOW does a booking exist.
    reservation = Reservation(
        confirmation_id=uuid.uuid4().hex, showtime_id=showtime_id,
        user_id=user_id, seat_ids=confirmed, amount_cents=amount,
        status=BookingStatus.CONFIRMED,
    )
    with self._lock:
        self._reservations[reservation.confirmation_id] = reservation
        self._ids_by_user[user_id].append(reservation.confirmation_id)
    return reservation
```

Now walk down it and ask at each line: *what if this fails?* Every answer is
"nothing to undo" or "the `except` handles it" — except two, and those are the
ones worth volunteering:

> "If the process dies mid-payment, nothing runs at all. That's what the TTL is
> for. Compensation handles errors I can catch; the TTL handles the ones I
> can't."

Three details to point at, because each one is a thing candidates get wrong:

- it catches `Exception`, not just payment errors, so *any* failure in the
  middle releases the hold
- it **re-raises**. Compensating and then swallowing leaves the caller thinking
  the booking worked
- it returns the `Reservation`, not `True`. The confirmation id is the only
  handle the user has to cancel

**And cancellation, which runs in the opposite order:**

```python
def cancel(self, confirmation_id, user_id) -> Reservation:
    with self._lock:
        r = self._reservations.get(confirmation_id)
        if r is None or r.user_id != user_id:
            raise BookingNotFoundError(confirmation_id)
        if r.status is BookingStatus.CANCELLED:
            return r                          # idempotent: no double refund
        r.status = BookingStatus.CANCELLED    # 1. RECORD INTENT FIRST

    # 2. reversible side effects LAST, outside the lock
    showtime.release_booked(r.seat_ids)
    gateway.refund(r.payment)
    return r
```

> "I flip the status before freeing the seats. If I did it the other way and
> the second step failed, the seats would be free while the booking still looks
> active — which is a double-booking."

### Minutes 38–43 — name the failures before they ask

Do not wait to be asked "what about race conditions?" Volunteer it. This is
free credit:

> "Let me walk through what can go wrong. There are three races here."

Then the three from Part 4.4:

| Race | What happens | Where it's closed |
|---|---|---|
| 1. Two users, same seat | both read "available", both write | check+write in one lock |
| 2. Expiry vs confirm | sweeper frees a seat being confirmed | no sweeper — lazy expiry |
| 3. Payment outlives hold | charged for a seat someone else took | `confirm` raises → refund |

Naming them and showing they're already closed is worth more than any extra
class you could have written instead.

If you have a spare minute, write the test. It is the most convincing thing you
can put on the screen:

```python
barrier = Barrier(40)
def race(i):
    barrier.wait()                       # all 40 threads released at once
    try:    winners.append(book("u%d" % i, "s1", ["C05", "C06"]))
    except SeatUnavailableError: losers.append(i)

assert len(winners) == 1                 # exactly one, every time
```

### Minutes 43–45 — extensibility

> "A new pricing rule is a new class implementing `PricingStrategy`, and
> nothing existing changes. If it needs to stack with weekend pricing, it's a
> decorator that wraps it."

```python
class PricingStrategy(Protocol):
    def total_cents(self, seats, price_by_type, start_time) -> int: ...

class WeekendPricing:
    def total_cents(self, seats, price_by_type, start_time):
        base = sum(price_by_type[s.seat_type] for s in seats)
        # start_time, NOT now() -- the price depends on when the SHOW is
        return base + base * 20 // 100 if start_time.weekday() >= 5 else base

class DemandPricing:                      # DECORATOR: wraps any other strategy
    def __init__(self, inner, occupancy_fn):
        self._inner, self._occupancy_fn = inner, occupancy_fn
    def total_cents(self, seats, price_by_type, start_time):
        base = self._inner.total_cents(seats, price_by_type, start_time)
        return base * 13 // 10 if self._occupancy_fn() >= 0.8 else base
```

> "Demand pricing is a decorator rather than a subclass, so a weekend show
> that's also filling up gets both surcharges. Subclassing would need a
> `WeekendAndDemandPricing` class, and then it's combinatorial."

Done.

### The shape of the whole thing

| Time | Where your head is |
|---|---|
| 0–5 | What's the disaster? Ask the question that surfaces holds |
| 5–10 | Nouns. Where does "taken" live? Not on Seat |
| 10–15 | Which single thing is contended? Lock goes there |
| 15–30 | **hold / confirm / release.** Check and write in one lock |
| 30–38 | hold → price → pay → confirm → record. What if each fails? |
| 38–43 | Name the three races, unprompted |
| 43–45 | New rule = new class |

**If you remember one thing about pacing:** be writing concurrency code by
minute 15. Entity lists are cheap and everybody produces one. Almost nobody
gets the lock right.

### The three sentences that carry it

If you say nothing else well, say these.

> "A seat doesn't have a status — the same seat is free at 6pm and taken at
> 9pm. Availability belongs to the Showtime. That also gives concurrency
> exactly one place to live."

> "A hold isn't a lock. A lock is held for microseconds by a thread. A hold is
> held for minutes by a *user*, and it needs an owner and an expiry — neither
> of which a mutex can store."

> "The check and the write happen inside the same lock. If I check availability
> before taking the lock, another thread can change it in the gap."

---

## 2. The five questions

Part 1 was this problem. Here is the same thinking stripped down so you can run
it on a problem you've never seen.

**1. What would be a disaster?**
One sentence. *Two people get the same seat.* Everything you build exists to
prevent that one thing. If you can't say it, you don't understand the problem
yet.

**2. What are people fighting over, and who owns it?**
Find the scarce thing (a seat for one showtime). Then find the one object that
owns it. The test: *if I change this, who else needs to know?* If the answer is
"nobody", you found the owner. **That object gets the lock** — one lock,
covering all of its state.

**3. What's slow, and is it inside the lock?**
List the slow things (the payment gateway). If anything slow is inside the
critical section, split the operation in two: a fast claim, then a fast commit,
with the slow part in between and no lock held.

That split is *why* `hold` and `confirm` exist as separate methods. It's not a
cinema thing — it's what you do whenever slow work sits inside a transaction.

**4. What expires, and who cleans it up?**
Any temporary claim needs an expiry. Two options:

- a background thread that sweeps — *creates a new race against your own commit*
- check expiry lazily, inside the lock you already take — *no new race*

Prefer lazy. A sweeper is a memory optimisation, never a correctness need.

**5. What does the user walk away with?**
The handle they'll use later — a confirmation id. So the main dictionary is
keyed by confirmation id, and `book()` returns the booking, not `True`. Return
a bool and you've thrown away the only thing that makes `cancel()` possible.

### Then two more, once the code exists

**6. What if each step fails halfway?** Walk the flow line by line and ask
"what if the process dies right here?" Each answer is "safe" or "compensate".

**7. What changes often?** Those become interfaces. Pricing rules and payment
methods change constantly → strategies. Seat layout doesn't → plain data.

---

## 3. How to find the classes and the methods

This is the part people find hardest: staring at a blank screen wondering what
classes to write. There is a mechanical way to do it. You will not need
inspiration.

### 3.1 Finding the classes — the noun recipe

**Step 1. Underline every noun in the problem statement.**

> "Users can search for *movies* by *title* and *city*, see *showtimes* at a
> *cinema*, pick *seats* from a *seat map*, and *book tickets*. Seats are
> *held* while the user *pays*."

```
user  movie  title  city  showtime  cinema  screen  seat  seat map
ticket  booking  hold  payment  price
```

That is your candidate list. You did not have to invent anything.

**Step 2. Delete the synonyms.** Pick one word and stick to it.

```
ticket / booking / reservation   -> keep ONE. I use Reservation.
cinema / theater / venue         -> keep ONE. I use Theater.
seat map                         -> that's just "the seats of a Theater"
```

**Step 3. Delete the ones that are fields, not classes.**

The test: *does it have its own identity, and would I look it up on its own?*

```
title   -> field on Movie.    You never ask "fetch me title #37".
city    -> field on Theater.  (Unless the problem says cities have their own
                               managers and currencies -- then promote it.)
price   -> field, a number on the Showtime.
```

Be ruthless here. Candidates lose ten minutes drawing a `City` class and a
`Screen` class that do nothing but hold a name and a list.

**Step 4. Split any noun that means two different things.**

This is the subtle one, and it is where the best design decision in this
problem comes from. Ask of each noun: *does this mean the same thing in every
context?*

```
"seat"  = the physical chair bolted to the floor      (same for every show)
"seat"  = the thing you are buying for the 6pm show   (different per show)
```

Same word, two concepts. So the chair is `Seat` and it is immutable, and
"is it taken" lives somewhere else. That single question is what stops you
writing `Seat.status`.

**Step 5. Add the nouns hiding inside the verbs.**

Re-read the requirements looking at the *verbs*. Some of them produce a thing
that must be remembered:

```
"seats are HELD while the user pays"  -> something must remember the hold
                                         -> class Hold
"the user PAYS"                       -> something must record the charge
                                         -> class Payment
"the user BOOKS"                      -> something must record the booking
                                         -> class Reservation
```

**The rule:** *if a verb produces something you'd have to show the user later,
or clean up later, it's a class.*

A hold must be cleaned up later, so it is a class. A search is not — nothing
survives it.

**Step 6. Sort what's left into four buckets.** Every class in every LLD
problem is one of these:

| Bucket | What it is | Here |
|---|---|---|
| **Things** | nouns with identity, mostly immutable | `Movie`, `Theater`, `Seat` |
| **Records** | "this happened", usually with a timestamp | `Hold`, `Payment`, `Reservation` |
| **Owners** | the thing that holds contended state | `Showtime` |
| **Doers** | verbs that belong to no single thing | `BookingService`, `MovieCatalog` |
| **Policies** | the "it depends" rules | `PricingStrategy`, `PaymentStrategy` |

If you can name one or two per bucket you have a complete design. If a bucket
is empty, that is a prompt: *no Policies? is nothing configurable here?*

### 3.2 The test that kills a bad class

Two questions. Either one failing means delete it.

**"What does it own?"** If a class owns no data that others can't own better,
it is not a class — it is a function. `SeatValidator`, `BookingHelper`,
`PriceCalculatorManager` all fail this.

**"Who changes it, and who needs to know?"** If the answer is "everyone changes
it", you have found your concurrency problem. If it is "nobody", the class is
immutable and needs no lock. This question is what sorts your classes into
"needs a lock" and "doesn't", which is the next thing you have to decide anyway.

### 3.3 Finding the methods — the verb recipe

Three sources. Work through them in order.

**Source 1: the verbs in the requirements.**

```
search  -> MovieCatalog.find_showtimes(title)
view    -> Showtime.available_seats()
hold    -> Showtime.hold_seats(seat_ids, user)
pay     -> PaymentStrategy.pay(amount)
book    -> BookingService.book(...)
cancel  -> BookingService.cancel(...)
```

**Source 2: the state machine. Every arrow is a method.**

Draw the lifecycle of the contended resource, then read the methods straight
off the diagram. This is the highest-yield trick in this whole guide:

```
            hold()                   confirm()
AVAILABLE ───────────▶ HELD ────────────────────▶ BOOKED
    ▲                   │                            │
    │   release_hold()  │                            │
    └───────────────────┘                            │
    │        or TTL expiry                           │
    │                                                │
    └────────────────────────────────────────────────┘
                     release_booked()   (cancellation)
```

Four arrows, four methods. You did not have to think of `release_hold` — the
diagram did. And if an arrow has no method, you have found a missing one. If a
method matches no arrow, you have found a method that shouldn't exist.

This also catches the thing I got wrong: I wrote `occupySeats` and
`unreserveSeat` but never drew the diagram, so I never noticed that the arrow
from BOOKED back to AVAILABLE and the arrow from HELD back to AVAILABLE are
*different transitions* that need different methods.

**Source 3: lifecycle pairs.** Whatever you create, something must undo. Scan
your methods and check each has its partner:

```
hold()       <->  release_hold()      and expiry, which is the automatic one
confirm()    <->  release_booked()
pay()        <->  refund()
add_movie()  <->  (remove? probably out of scope -- say so)
```

A missing partner is the most common gap an interviewer probes for.

### 3.4 Where does a method go?

One rule, and it answers every case:

> **A method lives where its data lives.**

If you are writing a method that reaches into another object's fields to do its
work, it is in the wrong class. Move it to the class that owns the fields.

Worked examples from this design:

| Method | Which data does it touch? | So it lives on |
|---|---|---|
| `hold_seats` | the available/held sets | the state store, owned by `Showtime` |
| `price_for` | the price table + seat types | `Showtime` (it holds the price data) |
| `find_showtimes` | the movie and showtime indexes | `MovieCatalog` |
| `book` | *several* objects — showtime, gateway, reservations | a **service**, because it owns none of them |

That last row is the whole justification for having a service layer at all. A
method that coordinates three objects belongs to none of them, so it gets its
own class. That is also why `BookingService` is thin: it sequences calls and
owns only the reservations dictionary.

**The anti-pattern to avoid:** a service that reaches into entities and mutates
their fields directly. If `BookingService` did
`showtime.available.remove(seat)`, then the lock that protects `available`
would have to be public, and now two classes share responsibility for one piece
of state. Keep the mutation inside the owner and give it a method name.

### 3.5 The entities this produces

```
Movie        what is playing              immutable
Theater      the room                     immutable
Seat         one physical seat            immutable   <-- note this
Showtime     movie + theater + time       OWNS mutable state
Hold         temporary claim              immutable, has expiry
Reservation  confirmed booking            mutable status only
Payment      record of one charge         immutable
```

The important decision is on `Seat`. **A seat does not have a status.** Its
availability is a property of the *(seat, showtime)* pair, so it lives in the
showtime, not on the seat.

This is the most common bug in published solutions for this problem. If you
put `status` on `Seat` and the `Theater` owns the seat objects, then booking
A01 for the 6pm show marks it booked for the 9pm show too.

**The general rule:** *if an attribute's value depends on the context you are
viewing the object in, it does not belong on the object.*

### 3.6 The invariant that defines "correct"

Every seat is in exactly one of the three states, and no seat is lost or
invented. Say this out loud and, if you have time, write it as an assert. It
shows you know what correctness *means* for your own data structure, which
almost nobody does:

```python
def check_invariants(self):
    with self._lock:
        held = set(self._hold_by_seat)
        assert not (self._available & held),           "available AND held"
        assert not (self._available & self._booked),   "available AND booked"
        assert not (held & self._booked),              "held AND booked"
        assert (self._available | held | self._booked) == self._all_seat_ids, \
            "seats were lost or invented"
```

This is also the best thing to assert at the end of a concurrency test. If
40 threads hammer the same seats and this still holds, your locking is right.

### 3.7 The data structures

```python
self._lock = RLock()                     # guards all four lines below
self._available: Set[str] = set(...)     # seat ids
self._booked:    Set[str] = set()        # seat ids
self._holds:     Dict[str, Hold] = {}    # hold_id -> Hold
self._hold_by_seat: Dict[str, str] = {}  # seat_id -> hold_id
```

Why two structures for holds? Because you need both directions:

- `hold_id → seats` when confirming or releasing (you have the hold id)
- `seat_id → hold` when checking if a seat is free (you have the seat id)

Keeping both in sync inside one lock is cheap. Scanning all holds to answer
"is A01 free" is not.

---

## 4. The concurrency chapter

This is the part that decides your rating. Everything above is setup.

### 4.1 A lock is not a hold

I got this wrong, and it caused five separate bugs in one class. Burn this in:

| | Mutex / Lock | Lease / Hold |
|---|---|---|
| Who owns it | a **thread** | a **user** |
| How long | microseconds | minutes |
| Is it visible to users | no | yes — "seats held, 9:58 left" |
| Where does it live | runtime primitive | a row in your data |
| How does it end | `release()` in `finally` | timestamp passes |
| Can it survive a restart | no | yes |
| Can another thread release it | no — crash | yes — that's normal |

**The tell:** *if your "lock" needs a timestamp, it is not a lock.*
**The second tell:** *if you want to display it to a user, it is not a lock.*

Here is the difference in code.

```python
# WRONG -- a mutex used as a hold. This is what I wrote.
self.locks[seat_id] = threading.Lock()     # no room for WHO, no room for WHEN
self.locks[seat_id].acquire()
# ... and now a background thread has to release a lock it never acquired,
#     which raises RuntimeError, and there is nowhere to store the user id.

# RIGHT -- a lease. Plain data.
Hold(hold_id=..., user_id="alice", seat_ids=("A01",), expires_at=now + 10min)
# The MUTEX guards the dict that holds these. The HOLD is the dict entry.
```

A lease lets you answer questions a mutex cannot:

```python
def who_holds(self, seat_id):          # impossible with a threading.Lock
    with self._lock:
        hold_id = self._hold_by_seat.get(seat_id)
        return self._holds[hold_id].user_id if hold_id else None
```

### 4.2 The check and the write must be in the same critical section

This is the one idea behind every concurrency bug in this problem.

```python
# WRONG -- there is a gap between the check and the write
if seat in self._available:        # thread A and thread B both see True here
    with self._lock:
        self._available.remove(seat)   # both remove, both think they won

# RIGHT -- check and write inside one lock
with self._lock:
    taken = [s for s in requested if s not in self._available]
    if taken:
        raise SeatUnavailableError(taken)   # nothing mutated, nothing to roll back
    for s in requested:
        self._available.discard(s)
```

This pattern has a name worth knowing: **TOCTOU**, time-of-check to
time-of-use. Any time you see `if <state is good>:` followed later by
`<mutate state>`, ask whether anything can run in between.

Notice the bonus: because the check happens before any mutation, "all or
nothing" for a group of seats falls out for free, with zero rollback code.

### 4.3 Why one lock per showtime, not one per seat

I reached for one lock per seat because 300 seats sounded like 300 parallel
bookings. That instinct is wrong here, and here is how to argue it:

1. **The critical section is tiny.** It is a set difference and a few set
   mutations — roughly a microsecond. The slow part (payment) is deliberately
   outside it.
2. **The lock is already sharded on the axis that matters.** One lock per
   showtime means the 6pm screening never waits on the 9pm screening. That is
   where the real parallelism is.
3. **Contention is inherent, not artificial.** A 300-seat room can only ever
   produce 300 successful bookings. Serialising a microsecond of work 300
   times is 300 microseconds total.
4. **Per-seat locking requires lock ordering.** Booking A01+A02 while someone
   books A02+A01 deadlocks unless you always acquire in sorted order and track
   what you managed to acquire. That is real code, and it is easy to get wrong
   under time pressure.

I benchmarked both. On disjoint seats — the *best* case for fine-grained
locking — the two came out dead even. On contended seats, per-seat was 1.6x
**slower**, because of the extra bookkeeping.

**What to say:** "One lock per showtime. The critical section is microseconds
and payment is outside it, so the contention is bounded. If one venue were
genuinely huge I'd shard by section, not by seat, so I never hold more than
one lock." That last clause shows you know the escape hatch exists and chose
not to use it.

### 4.4 The three races — name them and close them

Interviewers reward you for *naming* failure modes. These three cover it.

#### Race 1 — two users claim the same seat

Both threads read "A01 is available", both write "A01 is mine."

*Closed by:* check and set inside one lock (section 4.2). The second thread
sees the seat already gone and gets a clean `SeatUnavailableError`.

#### Race 2 — the expiry sweeper fires while the owner is confirming

A background thread decides Alice's hold expired at the same instant Alice's
payment succeeds and she confirms. The seat ends up either booked-and-then-
freed, or inconsistent between the two structures.

*Closed by:* **not having a sweeper thread.** Expiry is checked lazily inside
the lock that every operation already takes:

```python
def _expire_holds(self):          # caller must already hold self._lock
    now = datetime.now()
    for hold_id, hold in list(self._holds.items()):
        if hold.expires_at <= now:
            del self._holds[hold_id]
            for seat_id in hold.seat_ids:
                if self._hold_by_seat.get(seat_id) == hold_id:
                    self._hold_by_seat.pop(seat_id, None)
                    self._available.add(seat_id)
```

Called at the top of `available()`, `hold()`, `confirm()`, `validate_hold()`
and `stats()` — every entry point. An expired hold that nobody has observed
yet is unobservable, so leaving it in the dict for a moment changes nothing.

Two details worth knowing:

- `list(self._holds.items())` makes a snapshot. `.items()` on its own returns
  a live view, and deleting from the dict while iterating a view raises
  `RuntimeError: dictionary changed size during iteration`.
- The `if self._hold_by_seat.get(seat_id) == hold_id` guard matters. Without
  it, a late cleanup for an old hold could free a seat someone else has since
  legitimately re-held.

#### Race 3 — payment succeeds after the hold expired

The gateway is slower than the TTL. Alice's hold expires, Bob takes the seat,
*then* Alice's payment returns SUCCESS.

*Closed by:* re-validating at confirm time, and refunding if it fails.

```python
try:
    confirmed = showtime.confirm_hold(hold)
except HoldExpiredError:
    gateway.refund(receipt)     # we charged for seats we no longer hold
    raise
```

`confirm` uses `pop`, which is lookup and removal in one step:

```python
live = self._holds.pop(hold.hold_id, None)
if live is None:
    raise HoldExpiredError(...)
```

So a replayed confirm raises cleanly instead of double-booking, and a confirmed
hold is gone from `_holds` before the lock is released — which is why
`_expire_holds` can never touch a seat that is already BOOKED.

### 4.5 What this looks like behind a real database

Say this in one sentence and you have covered "how does it scale."

```sql
UPDATE seats SET status = 'HELD', hold_id = ?, expires_at = ?
 WHERE showtime_id = ? AND seat_id IN (?) AND status = 'AVAILABLE';
-- then check the affected row count equals the number of seats requested
```

The `AND status = 'AVAILABLE'` is the same check-and-set as the in-memory
version; the database does the serialising. In Redis it is `SET NX PX` per
seat, wrapped in a Lua script so the group stays atomic.

**The general principle:** a conditional write plus a row-count check is the
distributed version of "check and set under a lock."

---

## 5. The booking flow and every way it can fail

### 5.1 The order is the answer

```
hold  →  price  →  pay  →  confirm  →  record
```

- **hold first** — seats are safe before anything slow happens
- **pay in the middle with no lock held** — the gateway is the slowest thing
  in the stack; holding a lock across it would serialise the whole showtime on
  a third party
- **confirm after** — re-validates under the lock, so a payment that outlived
  the TTL is rejected and refunded rather than silently overwriting whoever
  now holds the seats

### 5.2 The code, with the failure paths

```python
hold = showtime.hold_seats(seat_ids, user_id)   # raises if taken; nothing to undo
try:
    amount = showtime.price_for(hold.seat_ids)
    receipt = gateway.pay(user_id, amount)      # SLOW. no lock held.
    try:
        confirmed = showtime.confirm_hold(hold)
    except HoldExpiredError:
        gateway.refund(receipt)                 # race 3
        raise
except Exception:
    showtime.release_hold(hold)                 # compensate...
    raise                                       # ...then re-raise
```

Three things to point at:

1. `except Exception` catches *every* way the middle can fail — declined card,
   network error, bug in pricing — and releases the hold in all of them.
2. It **re-raises**. Compensating and then swallowing the error leaves the
   caller thinking the booking succeeded.
3. `release_hold` is idempotent, so calling it on a hold that was already
   consumed or expired is harmless.

### 5.3 Every failure mode

| What fails | What happens | Who cleans up |
|---|---|---|
| Seat already taken | `SeatUnavailableError` before any mutation | nothing to clean |
| Card declined | `except` releases the hold, error propagates | the `except` block |
| Gateway times out | same path — any exception releases the hold | the `except` block |
| Payment succeeds, hold expired | `confirm` raises, we refund, then re-raise | the inner `except` |
| Process crashes mid-payment | hold sits in the dict until its TTL passes | **the TTL** |
| User closes the tab | nothing is called at all | **the TTL** |

The last two rows are why the TTL exists. Compensation handles the errors you
can catch; the TTL handles the ones you cannot.

### 5.4 Cancellation: reverse the order

Booking does side effects last. Cancellation does them last too — which means
the *record* update comes first.

```python
with self._lock:
    if reservation.status is BookingStatus.CANCELLED:
        return reservation              # idempotent: no double refund
    reservation.status = BookingStatus.CANCELLED   # 1. record intent
    seat_ids = list(reservation.seat_ids)

# outside the lock
showtime.release_booked(seat_ids)       # 2. reversible side effect
gateway.refund(receipt)                 # 3. reversible side effect
```

I originally wrote this backwards: free the seats, then delete the booking.
If the delete fails, the seats are free *and* the booking still looks active —
which is a double-booking.

> **The rule:** when two operations must stay in sync, do the one that
> **records intent** first and the **reversible side effect** last. A crash in
> between leaves a record whose intent is already correct, which a retry or a
> sweeper can finish.

This generalises to almost every "update two things" problem: write the
database row before sending the email, mark the order cancelled before issuing
the refund, flag the file deleted before unlinking it.

---

## 6. Patterns you can reuse

Each of these is worth recognising by its *trigger*, not its name.

### Strategy — "this rule changes often"

**Trigger:** a requirement contains "different kinds of" or "configurable".

```python
class PricingStrategy(Protocol):
    def total_cents(self, seats, price_by_type, start_time) -> int: ...
```

**The split that makes it work:** *prices are data, pricing is an algorithm.*
The price table lives on the `Showtime`; the formula lives in the strategy. If
you hardcode `price * 1.2 if weekend` inside `Showtime`, then every new rule —
holiday, matinee, loyalty, demand — edits `Showtime`. Split them and a new
rule is a new class that changes nothing existing.

**Elsewhere:** shipping cost calculators, tax rules, ranking functions, retry
policies, compression codecs, matchmaking rules.

### Decorator — "these rules need to combine"

**Trigger:** you have two strategies and someone asks "what if both apply?"

```python
class DemandPricing:
    def __init__(self, inner: PricingStrategy, occupancy_fn): ...
    def total_cents(self, seats, prices, start):
        return self._inner.total_cents(seats, prices, start) * multiplier
```

Subclassing gives you `WeekendPricing`, `DemandPricing`, then
`WeekendAndDemandPricing` — combinatorial explosion. Wrapping composes
linearly. This is the best 20-second extensibility answer you can give.

**Elsewhere:** middleware chains, stream wrappers, caching layers, auth
filters, discount stacking.

### Facade — "the caller shouldn't need to know the steps"

**Trigger:** your flow has four collaborators and the client should see one call.

`CinemaService.book_tickets()` hides the catalog lookup, the hold, the pricing
strategy, the gateway, and the confirm.

**Skip the Singleton.** Published designs make the facade a singleton with
double-checked locking. A singleton is global mutable state: it hides
dependencies and makes tests share state. Constructor injection costs one line
and gives you a fresh system per test. If asked for a singleton, give them one
*and say the trade-off out loud*.

### Lease / hold — "temporary exclusive claim"

**Trigger:** "reserve it while I finish something slow."

The whole of Part 4.1. This is the most transferable idea in this problem.

**Elsewhere:** parking spot reservation, hotel rooms, ride-hailing driver
assignment, flight seats, inventory reservation in checkout, distributed task
leases, DHCP, Kubernetes leader election.

### Primary store plus secondary index — "lookup by two different things"

**Trigger:** you need `cancel(confirmation_id)` *and* `history(user_id)`.

```python
self._reservations: Dict[str, Reservation] = {}             # primary, by id
self._ids_by_user: Dict[str, List[str]] = defaultdict(list) # secondary
```

**The rules:** the primary store is keyed by a *stable generated id*, never by
a human-readable string (titles collide, emails get reused). And every index
is updated in the *same method* that writes the primary, or the two drift
apart.

**Elsewhere:** any catalog, any user directory, any order system.

### Typed exception hierarchy — "the caller must react differently"

```python
class BookingError(Exception): ...
class UnknownSeatError(BookingError): ...      # bad input, don't retry
class SeatUnavailableError(BookingError): ...  # retry with other seats
class HoldExpiredError(BookingError): ...      # start over
```

One class per *distinct caller reaction*. A bare `return False` collapses all
three into "something went wrong", and the caller cannot build a sensible UI.
`SeatUnavailableError` carries `seat_ids` so the UI can grey out exactly those.

### Protocol / interface with a default — "swappable, but don't make me care"

```python
def __init__(self, ..., state_store: Optional[SeatStateStore] = None):
    self._state = state_store or InMemorySeatStateStore(...)
```

You get testability and a clean story for "how would you move to Redis", and
the caller still writes one line.

---

## 7. My mistakes: what, why, and the fix

Typos are excluded — those were text-editor artifacts, not design errors.
These are the real ones, ordered by how much they cost.

### M1 — The core method didn't do anything

```python
# what I wrote
def occupySeats(self, seats, userId):
    for seat in seats:
        if seat in self.seatLock:
            return False
    self.occupySeats(seats, userId)   # <-- calls itself. never removes anything.
```

**Why it happened:** I wrote the method top-down, got to the success path, and
typed the name of the operation I meant to perform instead of performing it.
Then I never re-read it.

**The fix:** after writing any method that is supposed to change state, read it
once and ask: *"which line actually changes the state?"* Point at it with your
finger. If you cannot, the method is a no-op.

This is the #1 lesson from the whole session: **verification, not knowledge.**
I knew what the method should do. I just never checked that it did.

### M2 — Checked availability outside the lock, with an inverted condition

```python
if seat in self.seatLock and seat in self.availableSeats:
    return False     # rejects seats that exist AND are free. Backwards.
```

**Why it happened:** I was writing the guard and the lock acquisition as two
separate thoughts, and I wrote the guard first because it was easier.

**The fix:** write `with self._lock:` **before** you write any condition that
reads shared state. Make the lock the first thing on the page, then fill in the
body. You cannot accidentally check outside the lock if the lock is already
there.

For the inverted condition specifically: when a boolean guard matters, write
the truth table in a comment. Four lines, five seconds, catches it every time.

### M3 — Used a mutex as the hold

I stored `Dict[seat_id, threading.Lock]` and then needed to attach a user and
an expiry to it, which a mutex cannot carry. That one decision produced five
bugs in the cleanup thread:

- released mutexes it never acquired → `RuntimeError`
- double-released, because the booking path's `finally` released too
- mutated the dict while iterating it → `RuntimeError`
- stored `{key: lock}` but unpacked `for lock, timestamp in ...items()`
- `if timestamp + delta >= now` — expires everything *except* the stale entries

**Why it happened:** the word "lock" appears in both the requirement ("lock the
seats for 10 minutes") and in the threading library, so I reached for the one
with the matching name.

**The fix:** the two tells in Part 4.1. If it needs a timestamp, it is not a
lock. If you'd show it to a user, it is not a lock. Write the data class first
(`Hold`), and only then ask what guards it.

`lock_vs_lease.py` in this folder runs every one of those five bugs so you can
see them fire.

### M4 — One lock per seat

**Why it happened:** "300 seats, 300 locks, more parallelism" felt obviously
right and I never questioned it.

**The fix:** the argument in Part 4.3 — critical section is microseconds, the
lock is already sharded per showtime, contention is bounded by inventory. And
say the escape hatch: "if a venue were genuinely huge, I'd shard by section."

### M5 — Keyed dictionaries by human-readable strings

```python
slots: Dict[movieTitle, Slot]            # two movies share a title -> silent overwrite
                                         # and only ONE showtime per movie can exist
reservations: Dict[user, List[Reservation]]   # O(n) scan to cancel by id
```

**Why it happened:** the title was the thing I had in my hand when I wrote the
search method.

**The fix:** primary stores are keyed by generated id. Always. If you need
lookup by title, that is a *secondary index* — and it maps to a **list**,
because titles are not unique. Deciding the return type is a list at
interface-design time is what stops the bug from ever being written.

### M6 — No defined behaviour for an unknown id

I returned `None` and left it to the caller.

**Why it happened:** I was focused on the happy path.

**The fix:** every lookup method, decide at the moment you write the signature:
raise or return `None`? For "the caller made a mistake", raise a typed error —
a `None` return can be forgotten, an exception cannot.

### M7 — `book()` returned `True`

**Why it happened:** the method felt like a success/failure operation.

**The fix:** ask "what does the user walk away with?" They walk away with a
confirmation id. Return the object. A `bool` return on a create operation is
almost always wrong.

### M8 — Payment declared out of scope, then left in the signature

I said payment was out of scope during clarification, then wrote
`reserveSeat(seats, slot, userId, payment: IPayment)` and kept it in the flow
diagram.

**Why it happened:** I changed my mind about scope and only updated half the
artifacts.

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

### The five methods that matter, line by line

Everything else in the file is plumbing. These five are what you are actually
being graded on, so here they are with a comment on every line that carries a
decision.

#### 1. `hold()` — the atomic claim

```python
def hold(self, seat_ids, user_id, ttl) -> Hold:

    requested = sorted(set(seat_ids))
    # set()    -> ["A01","A01"] would otherwise claim one seat twice
    # sorted() -> deterministic order; also what per-seat locking would need
    #             to avoid deadlock, so it costs nothing to do it here

    if not requested:
        raise UnknownSeatError("no seats requested")
        # define the empty case explicitly or it silently "succeeds"
        # with a hold on nothing

    unknown = sorted(set(requested) - self._all_seat_ids)
    if unknown:
        raise UnknownSeatError(f"no such seats: {unknown}")
    # WHY THIS IS OUTSIDE THE LOCK:
    #   seat EXISTENCE comes from immutable theater data -- it cannot change,
    #   so reading it unlocked is safe, and it keeps the critical section small.
    #   Seat AVAILABILITY is mutable, so that check must go inside. Knowing
    #   which checks can live outside the lock is a real signal of understanding.

    with self._lock:

        self._expire_holds()
        # FIRST thing inside the lock. If someone's 10 minutes ran out, their
        # seats must look free again BEFORE we decide this request fails.
        # Skip this and you reject users for seats that are actually available.

        taken = [s for s in requested if s not in self._available]
        if taken:
            raise SeatUnavailableError(taken)
        # ***** THE LINE THE WHOLE DESIGN EXISTS FOR *****
        # This check is inside the same `with` block as the writes below.
        # Move it one line above the `with` and you have the double-booking
        # bug: two threads both read "available" before either writes.
        #
        # SeatUnavailableError carries the seat ids so the UI can grey out
        # exactly those seats. A bare `return False` cannot do that.
        #
        # FREE BONUS: because we check ALL seats before mutating ANY, the
        # all-or-nothing guarantee needs zero rollback code.

        hold = Hold(
            hold_id=uuid.uuid4().hex,       # the handle we hand back
            showtime_id=self.showtime_id,
            user_id=user_id,                # WHO  -- a mutex cannot store this
            seat_ids=tuple(requested),      # tuple: frozen, so it can't drift
            expires_at=datetime.now() + ttl # WHEN -- a mutex cannot store this
        )
        # Two fields a threading.Lock has nowhere to put. That is the proof
        # that a hold is data, not a lock.

        self._holds[hold.hold_id] = hold
        for seat_id in requested:
            self._available.discard(seat_id)          # <-- ACTUALLY MUTATES.
            self._hold_by_seat[seat_id] = hold.hold_id
        # My interview bug (M1) was here: the success path called itself
        # recursively instead of removing anything, so the method was a no-op.
        # After writing any mutating method, point at the line that mutates.

        return hold
        # Return the Hold, not True. The caller needs the id to confirm later.
```

#### 2. `confirm()` — commit, and close race 3

```python
def confirm(self, hold) -> List[str]:
    with self._lock:

        self._expire_holds()
        # This single call is what closes RACE 3 (payment outlived the hold).
        # If the gateway took longer than the TTL, this removes the hold, and
        # the pop below then returns None and we reject instead of
        # overwriting whoever legitimately took the seats in the meantime.

        live = self._holds.pop(hold.hold_id, None)
        if live is None:
            raise HoldExpiredError(hold.hold_id)
        # pop() = look up AND remove in one step, under the lock.
        #   - a REPLAYED confirm (network retry, double click) finds nothing
        #     and raises, instead of booking the seats twice
        #   - the hold is gone before the lock is released, so nothing that
        #     runs later can ever "expire" a seat that is now BOOKED
        # Using get() then del would be two steps and reintroduce a gap.

        for seat_id in live.seat_ids:
            self._hold_by_seat.pop(seat_id, None)   # no longer held...
            self._booked.add(seat_id)               # ...now booked.
        # NOTE the seat never passes back through _available. HELD -> BOOKED
        # is one transition under one lock, so there is no instant where a
        # paid-for seat looks free.

        return list(live.seat_ids)
        # Return what was ACTUALLY confirmed, read from the stored hold --
        # not from the caller's argument, which could have been tampered with.
```

#### 3. `_expire_holds()` — lazy cleanup, no thread

```python
def _expire_holds(self) -> None:
    """MUST be called with self._lock already held."""
    # ^ This docstring is not decoration. A private method that assumes a lock
    #   is held is a trap for the next reader, so say it. The alternative --
    #   acquiring inside -- is why self._lock is an RLock, but relying on
    #   reentrancy to paper over unclear ownership is worse than a comment.

    now = datetime.now()
    # Read the clock ONCE. Calling now() inside the loop means different
    # holds are judged against different instants.

    for hold_id, hold in list(self._holds.items()):
        # list() IS LOAD-BEARING. .items() is a live view onto the dict, and
        # deleting during iteration over a view raises:
        #     RuntimeError: dictionary changed size during iteration
        # list() materialises a snapshot first, so `del` below is safe.
        # (That exact RuntimeError was one of my five Worker bugs.)

        if hold.expires_at <= now:
            del self._holds[hold_id]

            for seat_id in hold.seat_ids:
                if self._hold_by_seat.get(seat_id) == hold_id:
                    self._hold_by_seat.pop(seat_id, None)
                    self._available.add(seat_id)
                # THE GUARD MATTERS. Without `== hold_id`, a late cleanup for
                # an old hold could free a seat that somebody else has since
                # legitimately re-held. Always check you are deleting YOUR
                # entry, not whatever happens to be at that key now.

    # WHY NO BACKGROUND THREAD:
    #   A sweeper thread can fire at the same instant as a user's confirm.
    #   That is RACE 2, and published designs spend a page handling it.
    #   Doing expiry inside the lock every caller already takes means the
    #   race cannot exist. A sweeper is a MEMORY optimisation, never a
    #   correctness requirement.
```

#### 4. `book()` — the order that makes partial failure safe

```python
def book(self, showtime_id, seat_ids, user_id, payment=None) -> Reservation:

    gateway  = payment or self._default_payment
    # Per-CALL strategy, not a constructor field. Published designs inject one
    # gateway into the service, which means a user cannot pay by card today
    # and UPI tomorrow.

    showtime = self._catalog.get_showtime(showtime_id)
    # Raises ShowtimeNotFoundError rather than returning None, so a bad id
    # cannot slip through as an AttributeError twenty lines later.

    hold = showtime.hold_seats(seat_ids, user_id)
    # STEP 1, OUTSIDE the try. Deliberate: if this raises, nothing has
    # happened yet, so there is nothing to compensate. Putting it inside the
    # try would mean the except block runs release_hold(hold) with `hold`
    # unbound -> NameError masking the real error.

    try:
        amount = showtime.price_for(hold.seat_ids)
        # STEP 2. Note: price the seats the HOLD says we got, not the ones the
        # caller asked for. They are the same here, but reading from the
        # authoritative source is the habit that prevents whole bug classes.

        receipt = gateway.pay(user_id, amount)
        # STEP 3. THE SLOW ONE -- hundreds of milliseconds.
        # NO LOCK IS HELD AT THIS POINT. This is the entire reason hold and
        # confirm are separate methods. Hold a lock across this and every
        # booking for the showtime queues behind a third-party network call.

        try:
            confirmed = showtime.confirm_hold(hold)
        except HoldExpiredError:
            gateway.refund(receipt)
            raise
        # STEP 4 + the RACE 3 handler. We charged the card, then found the
        # hold had expired and someone else may hold the seats. Refund BEFORE
        # re-raising, or the user is out of pocket with no ticket.
        # This inner try exists only to distinguish "expired" (refund needed)
        # from every other failure (no charge happened, so nothing to refund).

    except Exception:
        showtime.release_hold(hold)
        raise
    # COMPENSATION. Catches Exception, not just PaymentFailedError, so ANY
    # failure in the middle -- declined card, timeout, a bug in pricing --
    # still frees the seats.
    #
    # The bare `raise` is essential. Compensating and then swallowing the
    # error returns None and the caller thinks the booking succeeded.
    #
    # release_hold is idempotent, so running it after a successful confirm
    # would be harmless. Cheap guarantees beat careful reasoning.

    reservation = Reservation(
        confirmation_id=uuid.uuid4().hex,
        ...
        status=BookingStatus.CONFIRMED,
    )
    # STEP 5. The Reservation is created ONLY here, after money and seats are
    # both secured. That is why BookingStatus has no CREATED state: the Hold
    # already played that role. One object per lifecycle stage beats one
    # object with a status meaning "maybe real".

    with self._lock:
        self._reservations[reservation.confirmation_id] = reservation
        self._ids_by_user[user_id].append(reservation.confirmation_id)
    # A DIFFERENT lock from the seat lock -- different state, different owner.
    # Primary store keyed by confirmation id gives O(1) cancel; the secondary
    # index gives per-user history. Keeping both means you don't have to
    # choose. My interview version kept only Dict[user, List[...]], which made
    # cancel-by-id an O(n) scan.

    return reservation
    # Return the object. Returning True throws away the confirmation id, which
    # is the only handle the user has to cancel. (My mistake M7.)
```

#### 5. `cancel()` — record intent first

```python
def cancel(self, confirmation_id, user_id, payment=None) -> Reservation:
    gateway = payment or self._default_payment

    with self._lock:

        reservation = self._reservations.get(confirmation_id)
        if reservation is None or reservation.user_id != user_id:
            raise BookingNotFoundError(confirmation_id)
        # "not yours" raises the SAME error as "does not exist". Distinguishing
        # them tells an attacker which confirmation ids are real.

        if reservation.status is BookingStatus.CANCELLED:
            return reservation
        # IDEMPOTENCY. A double click or a network retry must not refund twice
        # or free seats that someone else has since booked. Returning the
        # existing record is friendlier than raising -- the caller's desired
        # end state has been reached.

        reservation.status = BookingStatus.CANCELLED
        reservation.cancelled_at = datetime.now()
        seat_ids    = list(reservation.seat_ids)
        showtime_id = reservation.showtime_id
        receipt     = reservation.payment
        # RECORD INTENT FIRST, and copy out what the next part needs so we can
        # drop the lock. Cheap in-memory writes stay inside; slow calls do not.

    # ---- lock released ----

    self._catalog.get_showtime(showtime_id).release_booked(seat_ids)
    if receipt is not None:
        gateway.refund(receipt)
    # REVERSIBLE SIDE EFFECTS LAST, and outside the lock because refund() hits
    # the network.
    #
    # WHY THIS ORDER (my mistake M9): I originally freed the seats first and
    # updated the record second. If the second step fails, the seats are free
    # while the booking still looks ACTIVE -> double-booking. This way a crash
    # in between leaves a record whose INTENT is already correct, and a retry
    # or a sweeper can finish the job.
    #
    #   RULE: when two operations must stay in sync, do the one that RECORDS
    #         INTENT first and the REVERSIBLE SIDE EFFECT last.

    return reservation
```

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
        base = self._inner.total_cents(seats, price_by_type, start_time)
        occ = self._occupancy_fn()
        if occ >= 0.8:
            return base + (base * self._pct) // 100
        if occ <= 0.2:
            return base - (base * 10) // 100
        return base


# =============================================================================
# 5. PAYMENT -- Strategy. Slow and fallible: that is all the design needs.
# =============================================================================


class PaymentStrategy(Protocol):
    def pay(self, user_id: str, amount_cents: int) -> Payment: ...
    def refund(self, payment: Payment) -> None: ...


class CreditCardPayment:
    """latency_seconds exists so a test can make payment outlive the hold."""

    def __init__(self, success_rate: float = 1.0, latency_seconds: float = 0.0, seed: int = 7):
        self._success_rate = success_rate
        self._latency = latency_seconds
        self._random = random.Random(seed)
        self._lock = threading.Lock()
        self.charges = 0
        self.refunds = 0

    def pay(self, user_id: str, amount_cents: int) -> Payment:
        if self._latency:
            time.sleep(self._latency)
        with self._lock:
            if self._random.random() >= self._success_rate:
                raise PaymentFailedError(f"card declined for {user_id}")
            self.charges += 1
        return Payment(
            payment_id=uuid.uuid4().hex,
            amount_cents=amount_cents,
            status=PaymentStatus.SUCCESS,
            transaction_ref=f"txn_{uuid.uuid4().hex[:12]}",
        )

    def refund(self, payment: Payment) -> None:
        with self._lock:
            self.refunds += 1


# =============================================================================
# 6. SEAT STATE -- the only mutable shared state in the system
#
# ONE lock per showtime guards ALL THREE states. Lock granularity must equal
# state granularity: one owner, one lock.
# =============================================================================


class SeatStateStore:
    """One RLock guards every seat in one showtime.

    Why this granularity:
      - the critical section is a set difference, roughly a microsecond
      - payment, the slow part, happens OUTSIDE it
      - it is already sharded on the axis that matters: one lock per showtime
      - a thread never holds two locks, so deadlock is impossible
    """

    def __init__(self, showtime_id: str, all_seat_ids: Set[str]):
        self.showtime_id = showtime_id
        self._all_seat_ids = frozenset(all_seat_ids)

        # ---- everything below is guarded by self._lock ----
        self._lock = RLock()
        self._available: Set[str] = set(all_seat_ids)
        self._booked: Set[str] = set()
        self._holds: Dict[str, Hold] = {}          # hold_id -> Hold
        self._hold_by_seat: Dict[str, str] = {}    # seat_id -> hold_id

    # -- queries ------------------------------------------------------------

    def available(self) -> Set[str]:
        with self._lock:
            self._expire_holds()
            return set(self._available)  # a copy; never hand out internal state

    def stats(self) -> Dict[str, int]:
        with self._lock:
            self._expire_holds()
            return {
                "available": len(self._available),
                "held": len(self._hold_by_seat),
                "booked": len(self._booked),
                "total": len(self._all_seat_ids),
            }

    # -- the atomic claim ---------------------------------------------------

    def hold(self, seat_ids: Sequence[str], user_id: str, ttl: timedelta) -> Hold:
        requested = sorted(set(seat_ids))
        if not requested:
            raise UnknownSeatError("no seats requested")

        # Seat EXISTENCE is immutable data, so it is safe to check before the
        # lock. Seat AVAILABILITY is mutable, so it must not be.
        unknown = sorted(set(requested) - self._all_seat_ids)
        if unknown:
            raise UnknownSeatError(f"no such seats: {unknown}")

        with self._lock:
            self._expire_holds()

            # CHECK AND SET IN ONE CRITICAL SECTION. This is race 1 closed.
            taken = [s for s in requested if s not in self._available]
            if taken:
                # Nothing mutated yet, so all-or-nothing needs no rollback.
                raise SeatUnavailableError(taken)

            hold = Hold(
                hold_id=uuid.uuid4().hex,
                showtime_id=self.showtime_id,
                user_id=user_id,
                seat_ids=tuple(requested),
                expires_at=datetime.now() + ttl,
            )
            self._holds[hold.hold_id] = hold
            for seat_id in requested:
                self._available.discard(seat_id)
                self._hold_by_seat[seat_id] = hold.hold_id
            return hold

    def confirm(self, hold: Hold) -> List[str]:
        with self._lock:
            self._expire_holds()
            # pop() is lookup+removal in one step, so a replayed confirm raises
            # instead of double-booking. Race 3 is closed here: if payment
            # outlived the TTL, _expire_holds already removed this hold.
            live = self._holds.pop(hold.hold_id, None)
            if live is None:
                raise HoldExpiredError(f"hold expired or already used: {hold.hold_id}")
            for seat_id in live.seat_ids:
                self._hold_by_seat.pop(seat_id, None)
                self._booked.add(seat_id)
            return list(live.seat_ids)

    def validate_hold(self, hold: Hold, user_id: str) -> bool:
        with self._lock:
            self._expire_holds()
            live = self._holds.get(hold.hold_id)
            return live is not None and live.user_id == user_id

    # -- releases (both idempotent) -----------------------------------------

    def release_hold(self, hold: Hold) -> None:
        with self._lock:
            live = self._holds.pop(hold.hold_id, None)
            if live is None:
                return  # already expired or released
            for seat_id in live.seat_ids:
                # Only clear if the mapping still points at THIS hold, or a late
                # cleanup could free a seat someone else has since re-held.
                if self._hold_by_seat.get(seat_id) == live.hold_id:
                    self._hold_by_seat.pop(seat_id, None)
                    self._available.add(seat_id)

    def release_booked(self, seat_ids: Sequence[str]) -> None:
        with self._lock:
            for seat_id in seat_ids:
                if seat_id in self._booked:
                    self._booked.discard(seat_id)
                    self._available.add(seat_id)

    # -- internals ----------------------------------------------------------

    def _expire_holds(self) -> None:
        """LAZY expiry. Must be called with self._lock held.

        No background thread, so race 2 (sweeper vs confirm) cannot exist.
        list() takes a snapshot so `del` during iteration is safe.
        """
        now = datetime.now()
        for hold_id, hold in list(self._holds.items()):
            if hold.expires_at <= now:
                del self._holds[hold_id]
                for seat_id in hold.seat_ids:
                    if self._hold_by_seat.get(seat_id) == hold_id:
                        self._hold_by_seat.pop(seat_id, None)
                        self._available.add(seat_id)

    def check_invariants(self) -> None:
        """Every seat is in EXACTLY ONE of available / held / booked."""
        with self._lock:
            held = set(self._hold_by_seat)
            assert not (self._available & held)
            assert not (self._available & self._booked)
            assert not (held & self._booked)
            assert (self._available | held | self._booked) == self._all_seat_ids


# =============================================================================
# 7. SHOWTIME -- the bookable unit, and the owner of seat state
# =============================================================================

DEFAULT_HOLD_TTL = timedelta(minutes=10)


class Showtime:
    """Showtime owns availability because the same physical seat is free at 6pm
    and taken at 9pm. That also gives concurrency exactly one place to live."""

    def __init__(
        self,
        showtime_id: str,
        movie: Movie,
        theater: Theater,
        start_time: datetime,
        price_by_type: Dict[SeatType, int],
        pricing_strategy: Optional[PricingStrategy] = None,
        hold_ttl: timedelta = DEFAULT_HOLD_TTL,
    ):
        self.showtime_id = showtime_id
        self.movie = movie
        self.theater = theater
        self.start_time = start_time
        self.hold_ttl = hold_ttl
        self._price_by_type = dict(price_by_type)
        self._pricing = pricing_strategy or BasePricing()
        self._state = SeatStateStore(showtime_id, set(theater.seats))

    def available_seats(self, seat_type: Optional[SeatType] = None) -> List[Seat]:
        """Best-effort snapshot. A seat listed here may be gone a microsecond
        later -- true of any browse query, which is why hold() re-checks."""
        seats = [self.theater.seats[sid] for sid in self._state.available()]
        if seat_type is not None:
            seats = [s for s in seats if s.seat_type is seat_type]
        return sorted(seats, key=lambda s: (s.row, s.number))

    def occupancy(self) -> float:
        st = self._state.stats()
        return (st["held"] + st["booked"]) / st["total"] if st["total"] else 0.0

    def price_for(self, seat_ids: Sequence[str]) -> int:
        unknown = sorted(set(seat_ids) - set(self.theater.seats))
        if unknown:
            raise UnknownSeatError(f"no such seats: {unknown}")
        seats = [self.theater.seats[sid] for sid in seat_ids]
        return self._pricing.total_cents(seats, self._price_by_type, self.start_time)

    def hold_seats(self, seat_ids, user_id) -> Hold:
        return self._state.hold(seat_ids, user_id, self.hold_ttl)

    def confirm_hold(self, hold: Hold) -> List[str]:
        return self._state.confirm(hold)

    def release_hold(self, hold: Hold) -> None:
        self._state.release_hold(hold)

    def release_booked(self, seat_ids) -> None:
        self._state.release_booked(seat_ids)

    def stats(self) -> Dict[str, int]:
        return self._state.stats()

    def __repr__(self):
        return f"<Showtime {self.showtime_id} {self.movie.title!r} @ {self.start_time:%a %H:%M}>"


# =============================================================================
# 8. CATALOG -- primary store keyed by id, plus secondary indexes
# =============================================================================


def _normalize(title: str) -> str:
    return " ".join(title.split()).casefold()


class MovieCatalog:
    def __init__(self):
        # primary stores: keyed by stable generated id, never by a human string
        self._movies: Dict[str, Movie] = {}
        self._showtimes: Dict[str, Showtime] = {}
        # secondary indexes: updated in the same method that writes the primary
        self._movie_ids_by_title: Dict[str, List[str]] = defaultdict(list)
        self._showtime_ids_by_movie: Dict[str, List[str]] = defaultdict(list)

    def add_movie(self, movie: Movie) -> None:
        self._movies[movie.movie_id] = movie
        ids = self._movie_ids_by_title[_normalize(movie.title)]
        if movie.movie_id not in ids:
            ids.append(movie.movie_id)

    def add_showtime(self, showtime: Showtime) -> None:
        if showtime.movie.movie_id not in self._movies:
            self.add_movie(showtime.movie)
        self._showtimes[showtime.showtime_id] = showtime
        ids = self._showtime_ids_by_movie[showtime.movie.movie_id]
        if showtime.showtime_id not in ids:
            ids.append(showtime.showtime_id)

    def search_by_title(self, title: str) -> List[Movie]:
        """Returns a LIST: titles are not unique."""
        return [self._movies[m] for m in self._movie_ids_by_title.get(_normalize(title), [])]

    def get_showtime(self, showtime_id: str) -> Showtime:
        """RAISES on miss. A None return forces every caller to remember a null
        check; a typed exception cannot be forgotten."""
        showtime = self._showtimes.get(showtime_id)
        if showtime is None:
            raise ShowtimeNotFoundError(f"no such showtime: {showtime_id}")
        return showtime

    def find_showtimes(self, title: str, now: Optional[datetime] = None) -> List[Showtime]:
        now = now or datetime.now()
        out = []
        for movie in self.search_by_title(title):
            for sid in self._showtime_ids_by_movie.get(movie.movie_id, []):
                showtime = self._showtimes[sid]
                if showtime.start_time > now and showtime.available_seats():
                    out.append(showtime)
        return sorted(out, key=lambda s: s.start_time)


# =============================================================================
# 9. BOOKING SERVICE -- the step order that makes partial failure safe
# =============================================================================


class BookingService:
    def __init__(self, catalog: MovieCatalog, default_payment: PaymentStrategy):
        self._catalog = catalog
        self._default_payment = default_payment
        # ---- guarded by self._lock ----
        self._reservations: Dict[str, Reservation] = {}      # primary: O(1) cancel
        self._ids_by_user: Dict[str, List[str]] = defaultdict(list)  # secondary
        self._lock = RLock()

    def book(self, showtime_id, seat_ids, user_id, payment=None) -> Reservation:
        """hold -> price -> pay -> confirm -> record.

        Returns the Reservation, not a bool: the confirmation id is the only
        handle the user has to cancel.
        """
        gateway = payment or self._default_payment
        showtime = self._catalog.get_showtime(showtime_id)

        # 1. claim the seats. Nothing to undo if this fails.
        hold = showtime.hold_seats(seat_ids, user_id)
        try:
            # 2. price. Cheap, pure, no lock.
            amount = showtime.price_for(hold.seat_ids)

            # 3. charge. SLOW. NO LOCK HELD -- the whole reason hold and confirm
            #    are separate operations.
            receipt = gateway.pay(user_id, amount)

            # 4. confirm under the lock. Raises if the gateway outlived the TTL.
            try:
                confirmed = showtime.confirm_hold(hold)
            except HoldExpiredError:
                gateway.refund(receipt)  # we charged for seats we no longer hold
                raise
        except Exception:
            showtime.release_hold(hold)  # compensate...
            raise                        # ...then let the caller see the error

        # 5. record. Only now does a Reservation exist.
        reservation = Reservation(
            confirmation_id=uuid.uuid4().hex,
            showtime_id=showtime_id,
            user_id=user_id,
            seat_ids=confirmed,
            amount_cents=amount,
            status=BookingStatus.CONFIRMED,
            created_at=datetime.now(),
            payment=receipt,
        )
        with self._lock:
            self._reservations[reservation.confirmation_id] = reservation
            self._ids_by_user[user_id].append(reservation.confirmation_id)
        return reservation

    def cancel(self, confirmation_id, user_id, payment=None) -> Reservation:
        """Record intent FIRST, reversible side effects LAST."""
        gateway = payment or self._default_payment

        with self._lock:
            reservation = self._reservations.get(confirmation_id)
            # "not yours" is reported exactly like "does not exist"
            if reservation is None or reservation.user_id != user_id:
                raise BookingNotFoundError(f"no such booking: {confirmation_id}")
            if reservation.status is BookingStatus.CANCELLED:
                return reservation  # idempotent: no double refund
            reservation.status = BookingStatus.CANCELLED
            reservation.cancelled_at = datetime.now()
            seat_ids = list(reservation.seat_ids)
            showtime_id = reservation.showtime_id
            receipt = reservation.payment

        # Outside the lock. If either fails, the record already says CANCELLED,
        # so no seat is ever free while the booking still looks active.
        self._catalog.get_showtime(showtime_id).release_booked(seat_ids)
        if receipt is not None:
            gateway.refund(receipt)
        return reservation

    def history(self, user_id: str) -> List[Reservation]:
        with self._lock:
            return [self._reservations[c] for c in self._ids_by_user.get(user_id, [])]


# =============================================================================
# 10. FACADE -- one entry point. Not a Singleton: constructor injection instead.
# =============================================================================


class CinemaService:
    def __init__(self, payment: PaymentStrategy):
        self.catalog = MovieCatalog()
        self.bookings = BookingService(self.catalog, default_payment=payment)

    def add_showtime(self, showtime_id, movie, theater, start_time, price_by_type, **kw):
        showtime = Showtime(showtime_id, movie, theater, start_time, price_by_type, **kw)
        self.catalog.add_showtime(showtime)
        return showtime

    def find_showtimes(self, title):
        return self.catalog.find_showtimes(title)

    def available_seats(self, showtime_id, seat_type=None):
        return self.catalog.get_showtime(showtime_id).available_seats(seat_type)

    def book_tickets(self, user_id, showtime_id, seat_ids, payment=None):
        return self.bookings.book(showtime_id, seat_ids, user_id, payment)

    def cancel_booking(self, user_id, confirmation_id):
        return self.bookings.cancel(confirmation_id, user_id)

    def my_bookings(self, user_id):
        return self.bookings.history(user_id)


# =============================================================================
# DEMO -- including the race that decides the interview
# =============================================================================

if __name__ == "__main__":
    from threading import Barrier, Thread

    gateway = CreditCardPayment()
    cinema = CinemaService(payment=gateway)
    theater = Theater.with_grid("t1", "Grand IMAX", rows="ABCDE", seats_per_row=10,
                                premium_rows="AB")
    movie = Movie("m1", "Interstellar", 169)
    show = cinema.add_showtime(
        "s1", movie, theater,
        start_time=datetime.now() + timedelta(days=1),
        price_by_type={SeatType.REGULAR: 1200, SeatType.PREMIUM: 1800},
        pricing_strategy=WeekendPricing(),
    )

    print("1. browse       :", [s.seat_id for s in cinema.available_seats("s1")][:6], "...")
    print("2. price A01+A02:", show.price_for(["A01", "A02"]), "cents")

    r = cinema.book_tickets("alice", "s1", ["A01", "A02"])
    print("3. booked       :", r.confirmation_id[:8], r.seat_ids, r.amount_cents, "cents")

    try:
        cinema.book_tickets("bob", "s1", ["A02", "A03"])
    except SeatUnavailableError as e:
        print("4. bob rejected :", e.seat_ids, "(all-or-nothing: A03 stays free)")

    cinema.cancel_booking("alice", r.confirmation_id)
    print("5. cancelled    :", show.stats(), "refunds:", gateway.refunds)
    cinema.cancel_booking("alice", r.confirmation_id)
    print("6. cancel again :", "refunds still", gateway.refunds, "(idempotent)")

    # --- RACE 1: 40 threads, same two seats, exactly one may win -------------
    winners, losers = [], []
    barrier = Barrier(40)

    def race(i):
        barrier.wait()  # release all threads at the same instant
        try:
            winners.append(cinema.book_tickets(f"u{i}", "s1", ["C05", "C06"]))
        except SeatUnavailableError:
            losers.append(i)

    threads = [Thread(target=race, args=(i,)) for i in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"7. race         : {len(winners)} winner, {len(losers)} rejected")
    assert len(winners) == 1, "DOUBLE BOOKING"
    show._state.check_invariants()
    print("8. invariants   : every seat in exactly one state -- OK")
```

### Output

```
1. browse       : ['A01', 'A02', 'A03', 'A04', 'A05', 'A06'] ...
2. price A01+A02: 3600 cents
3. booked       : 601a16ca ['A01', 'A02'] 3600 cents
4. bob rejected : ['A02'] (all-or-nothing: A03 stays free)
5. cancelled    : {'available': 50, 'held': 0, 'booked': 0, 'total': 50} refunds: 1
6. cancel again : refunds still 1 (idempotent)
7. race         : 1 winner, 39 rejected
8. invariants   : every seat in exactly one state -- OK
```

---

## One-page summary

If you only remember five things:

1. **Showtime owns availability.** A seat has no status; a (seat, showtime)
   pair does.
2. **A hold is not a lock.** Owner + expiry + visible to users = data, not a
   mutex.
3. **Check and write in the same critical section.** One lock per showtime.
4. **hold → pay → confirm, with no lock held across the payment**, and re-check
   at confirm time.
5. **Record intent before the irreversible side effect.**

And the habit that fixes the most: after writing a method, re-read it and say
out loud what the lines actually do — not what you meant them to do.
