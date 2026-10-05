# LLD Guide — Movie Ticket Booking
A complete walkthrough: how to approach the problem, the thinking that produces
the design, the patterns you can reuse elsewhere, my own mistakes and how to
avoid them, and the full working code at the end.
Written in plain language. Read it top to bottom once, then use Part 2 and
Part 9 for revision.
---
## Contents
1. [The 45-minute plan](#1-the-45-minute-plan)
2. [The method: nine questions that produce any LLD](#2-the-method-nine-questions-that-produce-any-lld)
3. [Walking the method on this problem](#3-walking-the-method-on-this-problem)
4. [The concurrency chapter](#4-the-concurrency-chapter)
5. [The booking flow and every way it can fail](#5-the-booking-flow-and-every-way-it-can-fail)
6. [Patterns you can reuse](#6-patterns-you-can-reuse)
7. [My mistakes: what, why, and the fix](#7-my-mistakes-what-why-and-the-fix)
8. [Transferring this to other problems](#8-transferring-this-to-other-problems)
9. [Rapid-fire answers](#9-rapid-fire-answers)
10. [Full code](#10-full-code)
---
## 1. The 45-minute plan
Most people fail LLD by spending 30 minutes on entities and 5 minutes on the
thing that actually gets graded. Here is the split that works.
| Time | What you do | What you must say out loud |
|---|---|---|
| 0–5 min | Clarify requirements | "What happens when two users pick the same seat?" |
| 5–10 min | Name the entities | "Showtime owns availability, because a seat is free at 6pm and taken at 9pm" |
| 10–15 min | Find the shared mutable state | "The only contended state is seat availability per showtime" |
| 15–30 min | Write the concurrency core | hold / confirm / release, and the check-and-set under one lock |
| 30–38 min | Write the orchestration | hold → price → pay → confirm → record, with compensation |
| 38–43 min | Name the races and show they are closed | the three races in Part 4 |
| 43–45 min | Extensibility | "New pricing rule is a new class, nothing existing changes" |
**The single most important reallocation:** get to code by minute 15. Entities
are cheap. The lock is what they are grading.
### The three sentences that carry the interview
Memorise these. If you say nothing else well, say these.
> "Showtime owns seat availability, because the same physical seat is free for
> the 6pm show and taken for the 9pm show. That also gives concurrency control
> exactly one place to live."
> "A hold is not a lock. A lock is held for microseconds to guard a mutation.
> A hold is business data with an owner and an expiry that lives for minutes.
> The lock protects the hold table; it is not the hold."
> "The check and the write happen in the same critical section. If I check
> availability before taking the lock, another thread can change it in the gap."
---
## 2. The method: nine questions that produce any LLD
This is the general procedure. It is not specific to cinemas. Ask these nine
questions in order and the design falls out.
**Q1. What must never happen?**
Write the one-line disaster. Here: *two people are sold the same seat.*
Everything else in the design is in service of preventing that one thing. If
you cannot state this, you do not yet know what you are building.
**Q2. What are users fighting over?**
Find the scarce resource. Here: a seat for one showtime. This is the thing
that needs concurrency control. Everything else — movie titles, user profiles,
prices — is read-mostly and does not.
**Q3. Who owns that resource?**
One object, never two. Here: `Showtime`. Not `Seat` (shared across showtimes),
not a global manager (no natural shard).
The test for ownership: *if I change this, who else needs to know?* If the
answer is "nobody", you found the owner.
**Q4. One owner, one lock.**
Lock granularity must equal state granularity. The owner from Q3 gets the
lock. Here: one lock per `Showtime`, guarding available + held + booked
together.
**Q5. What is slow, and is it inside the lock?**
List the slow operations. Here: the payment gateway, hundreds of milliseconds.
If anything slow is inside the critical section, split the operation in two:
a fast claim, then a fast commit, with the slow part in between and no lock
held. That split is exactly why `hold` and `confirm` are separate methods.
**Q6. What has a timeout, and who cleans it up?**
Any temporary claim needs an expiry. You have two choices:
- a background thread that sweeps (creates a race with the owner's own commit)
- expiry checked lazily inside the lock you already take (no new race)
Prefer lazy. A sweeper is a memory optimisation, never a correctness need.
**Q7. What does the user walk away with?**
The handle they will use later. Here: a confirmation id. That means the
primary store is keyed by confirmation id, not by user. Returning `True` from
`book()` throws away the only thing that makes `cancel()` possible.
**Q8. For each step, what breaks if it fails halfway?**
Walk the flow and ask "what if the process dies right here?" at each step.
Every answer is either "nothing, it's safe" or "add compensation here".
**Q9. What is likely to change?**
Those become interfaces. Here: pricing rules and payment methods change
constantly, so both are strategies. Seat layout does not, so it is plain data.
---
## 3. Walking the method on this problem
### 3.1 Clarifying questions worth asking (0–5 min)
Ask four, not fifteen. These four each change the design:
1. "What happens when two users select the same seat at the same time?"
   → the interviewer will describe a temporary hold. Now concurrency is in
   scope and *they* put it there.
2. "Does a user pick specific seats, or does the system assign them?"
   → specific seats means all-or-nothing group booking.
3. "Is payment in scope, or can I assume a gateway?"
   → assume a gateway, but **keep it in the flow**, because the hold timeout
   only makes sense if something slow sits between hold and confirm.
4. "Single process or distributed?"
   → say "I'll design in-memory and tell you what changes behind a database."
### 3.2 Entities (5–10 min)
Pull the nouns out of the requirements, then decide what is immutable.
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
### 3.3 The three states (10–15 min)
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
**The invariant:** every seat is in exactly one of the three states. Say this
out loud and, if you have time, write it as an assert. It shows you know what
"correct" means for your own data structure.
```python
assert (available | held | booked) == all_seats
assert not (available & held) and not (available & booked) and not (held & booked)
```
### 3.4 The data structures
```python
self._lock = RLock()                     # guards all four lines below
self._available: Set[str] = set(...)     # seat ids
self._booked:    Set[str] = set()        # seat ids
self._holds:     Dict[str, Hold] = {}    # hold_id -> Hold
self._hold_by_seat: Dict[str, str] = {}  # seat_id -> hold_id
```
