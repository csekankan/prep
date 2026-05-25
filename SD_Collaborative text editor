# Collaborative Text Editor — Complete System Design
### OT · CRDT · WebSockets · Offline Sync · Frontend + Backend

Everything you need to design a Google Docs-style collaborative editor — from
first principles to production trade-offs.

---

## Table of Contents

1. [The Core Problem](#1-the-core-problem)
2. [Text Editor Fundamentals](#2-text-editor-fundamentals)
3. [Why Collaboration Is Hard](#3-why-collaboration-is-hard)
4. [Operational Transformation (OT)](#4-operational-transformation-ot)
5. [Conflict-Free Replicated Data Types (CRDT)](#5-conflict-free-replicated-data-types-crdt)
6. [OT vs CRDT — Full Comparison](#6-ot-vs-crdt--full-comparison)
7. [Offline / Online Sync & WebSockets](#7-offline--online-sync--websockets)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Backend Architecture](#9-backend-architecture)
10. [Data Models & API Design](#10-data-models--api-design)
11. [Performance Optimizations](#11-performance-optimizations)
12. [Edge Cases & Failure Modes](#12-edge-cases--failure-modes)
13. [Interview Cheatsheet](#13-interview-cheatsheet)

---

## 1. The Core Problem

Two users edit the same document simultaneously. Their edits travel over a
network with non-zero latency. Both users must see an **identical final
document** regardless of the order edits arrive.

```
Initial state: "Hello"

Alice types " World"  → locally sees "Hello World"
Bob deletes "Hello"   → locally sees ""

Naively applied on Alice's machine:
  Bob's delete arrives → "" + " World" = " World"   ✗

Naively applied on Bob's machine:
  Alice's insert arrives → "" + " World" = " World"  ✗

Expected convergence:
  Both should see " World" or "Hello World" — consistently the same thing.
```

The documents **did not converge**. This happens because edits do not commute:
`A - B ≠ B - A` for deletion, and idempotency breaks when two users delete the
same character expecting only one deletion.

**Three challenges to solve:**

| Challenge | Description |
|---|---|
| **Conflict resolution** | Whose change wins when two users edit the same position |
| **Real-time coordination** | Changes must feel instant, like a single-user editor |
| **Synchronization** | New users joining must receive the current full state |

---

## 2. Text Editor Fundamentals

A text editor's core job is **insertion and deletion of characters**. Its
central component is a data structure holding the text content.

```
Simple model — text as an array of characters:

  Index:  0    1    2    3    4
  Char:  'H'  'e'  'l'  'l'  'o'

Insert 'X' at index 2:
  Shift everything from index 2 right by 1
  Result: H e X l l o   → O(N) operation

Delete at index 1:
  Shift everything from index 2 left by 1
  Result: H l l o       → O(N) operation
```

For collaborative editors, **position-based indexing breaks** because a
position "2" on Alice's screen means something different after Bob inserted a
character before it. This is the fundamental mismatch both OT and CRDT solve.

```
Advanced data structures used in real editors:

Rope:          Tree of strings. O(log N) insert/delete. Used in large docs.
Piece Table:   Two buffers (original + additions). Undo-friendly. Used in VSCode.
Gap Buffer:    Array with a gap at cursor. O(1) near-cursor edits. Used in Emacs.
CRDT sequence: Linked list of objects with stable IDs. Collaboration-friendly.
```

---

## 3. Why Collaboration Is Hard

### The Commutativity Problem

```
State: "ab"

Alice: insert 'c' at position 2  →  "abc"
Bob:   insert 'd' at position 0  →  "dab"

Apply Alice then Bob:  "abc" → insert 'd' at 0 → "dabc"  ✓
Apply Bob then Alice:  "dab" → insert 'c' at 2 → "dacb"  ✗

Same operations, different order → different results.
Operations are NOT commutative. a + b ≠ b + a.
```

### The Idempotency Problem

```
State: "ab"

Alice: delete 'a' at position 0
Bob:   delete 'a' at position 0  (same operation, different client)

Expected: one 'a' deleted → "b"
Actual (naively):  two deletions applied → "" or crash ✗

The operation is not idempotent: applying it twice gives wrong result.
```

### Mathematical Properties Required

For convergence, operations must satisfy:

```
Commutative:  A ∘ B  =  B ∘ A        (order doesn't matter)
Associative: (A ∘ B) ∘ C = A ∘ (B ∘ C)  (grouping doesn't matter)
Idempotent:   A ∘ A  =  A            (applying twice = applying once)
```

- OT achieves these via **transform functions** applied at runtime
- CRDT achieves these via **data structure design** — baked in by construction

---

## 4. Operational Transformation (OT)

### Core Idea

> Don't send the final state — send the **intent (operation)**. Then
> **transform** that intent based on what happened concurrently.

OT keeps documents as a linear structure (positions) but adjusts every
incoming operation's position before applying it, based on what other
operations already happened.

### Key Components

```
Operation:   A description of a change
             insert(pos, char) or delete(pos)

Transform:   T(op1, op2) → op1'
             Adjust op1 assuming op2 already happened

Revision:    A monotonically increasing sequence number.
             Every op carries the revision it was based on.

Server:      Single source of truth for operation ordering.
             Assigns sequence numbers. Never optional in OT.
```

### Step-by-Step Example

```
Initial state: "ab"   (revision 0)

Alice: insert('c', pos=2)   baseRevision=0
Bob:   insert('d', pos=0)   baseRevision=0

Both ops travel to server simultaneously.
Server receives Alice's op first (arbitrary tie-break).

Server applies Alice:  "ab" → "abc"   revision=1
Server now must apply Bob's op, but must transform it first:

  Transform(Bob_op, Alice_op):
    Bob wants: insert('d', pos=0)
    Alice inserted at pos=2. Bob's pos=0 is BEFORE pos=2.
    → Bob's position unaffected.
    → Bob_op' = insert('d', pos=0)

Server applies Bob':  "abc" → "dabc"   revision=2

Server sends Alice: Bob_op (she needs to update her local view)
  Alice already applied her own op locally.
  She must transform Bob_op against her own pending op:

  Transform(Bob_op, Alice_op):
    Same calculation → Bob_op' = insert('d', pos=0)

  Alice applies Bob_op' to her local "abc" → "dabc"  ✓

Both clients: "dabc"  ✓  Converged.
```

### The Transform Function

```python
def transform_insert_insert(op1, op2):
    """Adjust op1 (insert) given op2 (insert) already happened."""
    if op2.pos < op1.pos:
        return Insert(op1.pos + 1, op1.char)      # shift right
    elif op2.pos == op1.pos:
        # Tie-break: lower client_id goes first
        if op2.client_id < op1.client_id:
            return Insert(op1.pos + 1, op1.char)
        else:
            return op1
    else:
        return op1                                  # no shift needed

def transform_insert_delete(op1, op2):
    """Adjust insert op1 given delete op2 already happened."""
    if op2.pos < op1.pos:
        return Insert(op1.pos - 1, op1.char)       # shift left
    else:
        return op1

def transform_delete_insert(op1, op2):
    """Adjust delete op1 given insert op2 already happened."""
    if op2.pos <= op1.pos:
        return Delete(op1.pos + 1)                 # shift right
    else:
        return op1

def transform_delete_delete(op1, op2):
    """Adjust delete op1 given delete op2 already happened."""
    if op2.pos < op1.pos:
        return Delete(op1.pos - 1)                 # shift left
    elif op2.pos == op1.pos:
        return NoOp()                              # both deleted same char
    else:
        return op1
```

### The OT Diamond Problem (TP2)

OT must satisfy the **TP2 property** for correctness with 3+ concurrent ops:

```
                   State S
                  /        \
            op_A            op_B
            /                  \
        S+A                    S+B
            \                  /
      T(B,A)  \              /  T(A,B)
               \            /
                S+A+T(B,A) must equal S+B+T(A,B)

TP2: T(T(A,B), T(C,B)) = T(T(A,C), T(B,C))

This is notoriously hard to satisfy. Google Wave took 2 years.
Joseph Gentle (Google Wave engineer):
  "Unfortunately, implementing OT sucks. The algorithms are really
   hard and time consuming to implement correctly."
```

### OT Client State Machine

```
client = {
  doc:          "Hello World",   // current visible document
  revision:     7,               // last server revision seen
  pendingOps:   [...],           // sent to server, awaiting ACK
  buffer:       [...],           // not yet sent (waiting for ACK of pendingOps)
}

ONLINE flow:
  User types → create op with baseRevision=7
             → apply to local doc immediately (optimistic)
             → push to pendingOps
             → send over WebSocket

  Server ACKs with seq=8:
             → pendingOps cleared
             → revision = 8
             → send next op from buffer

OFFLINE flow:
  User types → create op with baseRevision=7
             → apply to local doc
             → push to pendingOps (saved to IndexedDB)
             → WebSocket is down, ops sit in queue

RECONNECT flow:
  Send: { type: "SYNC_REQUEST", lastSeenRevision: 7 }
  Receive: { type: "CATCH_UP", ops: [op8, op9, op10...] }
  
  For each missed server op:
    Transform all pendingOps against it
    Apply missed op to local doc

  Flush pendingOps to server (now with correct baseRevision)
```

### OT Memory Management

```
Server keeps a sliding operation log:

  op_log = { 1: op, 2: op, 3: op, ... 50: op }

  Every client sends periodic ACKs:
    { type: "ACK", revision: 50 }

  Server tracks min revision across all clients:
    alice → rev 50
    bob   → rev 50
    carol → rev 47   ← slowest client

  Safe to prune: everything before rev 47
  → ops 1..46 deleted from memory

Long offline clients:
  If Carol is offline too long → session expires
  Carol must reload full document on return
  (Google Docs behavior: "Reconnecting..." then full reload)

Memory usage:
  Active session: O(ops since slowest client's revision)
  After session: O(1) — just final document
```

---

## 5. Conflict-Free Replicated Data Types (CRDT)

### Core Idea

> Design your data structure so that all concurrent operations are
> **mathematically guaranteed to converge**, regardless of the order applied.
> No server authority needed. No transformation. Just merge.

### The Three Magic Properties (Built Into the Data Structure)

```
Commutative:   Merge(A, B)       = Merge(B, A)
Associative:   Merge(Merge(A,B),C) = Merge(A,Merge(B,C))
Idempotent:    Merge(A, A)       = A

If your structure has these → conflicts are IMPOSSIBLE by construction.
```

### Type 1: G-Counter (Grow-Only Counter)

```python
class GCounter:
    def __init__(self, node_id, num_nodes):
        self.node_id = node_id
        self.counts = [0] * num_nodes  # each node tracks only its own slot

    def increment(self):
        self.counts[self.node_id] += 1

    def value(self):
        return sum(self.counts)

    def merge(self, other):
        # Take MAX of each slot — commutative, associative, idempotent
        return [max(a, b) for a, b in zip(self.counts, other.counts)]

# Node A: [3, 0, 0]  Node B: [0, 5, 0]  Node C: [0, 0, 2]
# Merge all: [3, 5, 2] → value = 10  (same regardless of merge order)
```

### Type 2: LWW-Register (Last Write Wins)

```python
class LWWRegister:
    def __init__(self):
        self.value = None
        self.timestamp = 0

    def write(self, value, timestamp):
        if timestamp > self.timestamp:
            self.value = value
            self.timestamp = timestamp

    def merge(self, other):
        if other.timestamp > self.timestamp:
            self.value = other.value
            self.timestamp = other.timestamp

# Used for: document title, user status, cell values in spreadsheets
# Trade-off: one concurrent write is silently lost (acceptable for scalars)
```

### Type 3: OR-Set (Observed-Remove Set)

```python
import uuid

class ORSet:
    def __init__(self):
        self.additions = {}   # { element: {tag1, tag2} }
        self.removals  = set()

    def add(self, element):
        tag = uuid.uuid4()
        self.additions.setdefault(element, set()).add(tag)

    def remove(self, element):
        # Remove only tags currently known — concurrent adds survive
        for tag in self.additions.get(element, set()):
            self.removals.add(tag)

    def contains(self, element):
        live_tags = self.additions.get(element, set()) - self.removals
        return bool(live_tags)

    def merge(self, other):
        result = ORSet()
        for elem, tags in {**self.additions, **other.additions}.items():
            result.additions[elem] = (
                self.additions.get(elem, set()) | other.additions.get(elem, set())
            )
        result.removals = self.removals | other.removals
        return result

# Concurrent add + remove → ADD WINS (by design)
# Used for: shared lists, presence sets, feature flags
```

### Type 4: CRDT Text (RGA — Replicated Growable Array)

This is the CRDT used in text editors (Yjs Y.Text, Automerge).

**Key insight:** each character gets a **stable unique ID** and knows what
character it comes **after** — not its numeric position.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Char:
    id: tuple          # (client_id, clock) — globally unique
    value: str
    after: Optional[tuple]  # ID of the preceding char (None = document start)
    deleted: bool = False   # tombstone — never truly removed

class RGAText:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.clock = 0
        self.chars: list[Char] = []

    def _new_id(self):
        self.clock += 1
        return (self.client_id, self.clock)

    def insert_after(self, after_id, value) -> Char:
        char = Char(id=self._new_id(), value=value, after=after_id)
        self.chars.append(char)
        self._sort()
        return char  # broadcast this to all peers

    def delete(self, char_id) -> Char:
        for char in self.chars:
            if char.id == char_id:
                char.deleted = True
                return char  # broadcast tombstone to all peers

    def apply_remote(self, remote_char: Char):
        self.chars.append(remote_char)
        self._sort()

    def _sort(self):
        # Topological sort: chars ordered by their 'after' chain.
        # Tie-break concurrent inserts at same position by client_id.
        pass  # full implementation: topological sort on after-pointers

    def to_string(self) -> str:
        return ''.join(c.value for c in self.chars if not c.deleted)
```

**Concurrent insert — no transformation needed:**

```
Document: "ct"
  char(id=("A",1), value='c', after=None)
  char(id=("A",2), value='t', after=("A",1))

You:    insert 'a' after ("A",1) → char(id=("Y",1), value='a', after=("A",1))
Friend: insert 'h' after ("A",1) → char(id=("F",1), value='h', after=("A",1))

Both say "insert after (A,1)". Tie-break by client_id: "F" < "Y"
→ F's char goes first.

Final on ALL nodes: c → h → a → t = "chat"  ✓  No server. No transform.
```

**Why deletions are tombstones (never hard-deleted):**

```
Alice deletes char(id=("A",3)) → marks deleted=True
Bob (offline) inserts 'X' after ("A",3)

If you removed the tombstone before Bob reconnects:
  Bob's op arrives: "insert after (A,3)" → (A,3) not found → BROKEN ✗

With tombstone:
  Bob merges: (A,3) exists (deleted=True) but still an anchor
  'X' inserts correctly, renders after the invisible deleted char ✓
```

### CRDT Implementation in JavaScript (LSEQ / Fractional Index style)

```javascript
const uuidv1 = () => {
    const s4 = () => Math.floor((1 + Math.random()) * 0x10000)
        .toString(16).substring(1);
    return `${s4()}${s4()}-${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`;
};

function Char(index, char, siteID, id = uuidv1()) {
    this.id = id;
    this.index = index;   // fractional index for ordering
    this.char = char;
    this.siteID = siteID;
    this.deleted = false;
}

function CRDT() {
    this.siteID = uuidv1();
    // sentinel chars: beginning-of-file and end-of-file
    this.chars = [
        new Char(0,     'bof', this.siteID),
        new Char(10000, 'eof', this.siteID),
    ];

    // Generate a fractional index between two positions
    this.generateIndex = function(indexStart, indexEnd) {
        const diff = indexEnd - indexStart;
        if (diff <= 10)   return indexStart + diff / 100;
        if (diff <= 1000) return Math.round(indexStart + diff / 10);
        if (diff <= 5000) return Math.round(indexStart + diff / 100);
        return Math.round(indexStart + diff / 1000);
    };

    // Local insert: new character between indexStart and indexEnd
    this.insert = function(indexStart, indexEnd, char, id) {
        const index = this.generateIndex(indexStart, indexEnd);
        const charObj = id
            ? new Char(index, char, this.siteID, id)
            : new Char(index, char, this.siteID);
        this.chars.push(charObj);
        this.chars.sort((a, b) => a.index - b.index);
        return charObj;  // send to server/peers
    };

    // Remote insert: received from another user
    this.remoteInsert = function(char) {
        const copy = new Char(char.index, char.char, char.siteID, char.id);
        this.chars.push(copy);
        this.chars.sort((a, b) =>
            a.index === b.index
                ? a.siteID < b.siteID ? -1 : 1  // tie-break by siteID
                : a.index - b.index
        );
    };

    // Delete: mark as tombstone (local or remote — same operation)
    this.delete = function(id) {
        const char = this.chars.find(c => c.id === id);
        if (char) char.deleted = true;
    };

    // Render: skip tombstones and sentinels
    this.render = function() {
        return this.chars
            .filter(c => !c.deleted && c.char !== 'bof' && c.char !== 'eof')
            .map(c => c.char)
            .join('');
    };
}

// Usage:
const crdt = new CRDT();
const h = crdt.insert(0, 10000, 'h');   // between bof(0) and eof(10000)
const e = crdt.insert(h.index, 10000, 'e');
const l = crdt.insert(e.index, 10000, 'l');
crdt.insert(l.index, 10000, 'l');
crdt.insert(l.index, 10000, 'o');
console.log(crdt.render()); // "hello"

crdt.delete(e.id);
console.log(crdt.render()); // "hllo"
```

### CRDT State-Based vs Op-Based

| | State-Based (CvRDT) | Op-Based (CmRDT) |
|---|---|---|
| What you sync | Full state | Individual operations |
| Network requirement | At-least-once delivery | Exactly-once delivery |
| Bandwidth | High (full state) | Low (just ops) |
| Merge | `merge(stateA, stateB)` | `apply(op)` |
| Example | G-Counter, LWW-Register | RGA Text, OR-Set |

Real systems (Yjs, Automerge) use op-based for bandwidth, fall back to
full-state sync for peers that were offline a long time.

### CRDT Memory — The Tombstone Problem

```
User types and deletes 10,000 characters in a session.
Visible text:       200 characters
CRDT in memory:     200 live + 10,000 tombstones = 10,200 entries

Cannot garbage-collect tombstones because:
  An offline peer might reference a deleted char as an anchor.
  Deleting it before that peer reconnects → their insert has no anchor → BROKEN.

Garbage collection requires:
  Server coordinates: "Everyone has seen op N, safe to GC tombstones before N"
  This is expensive and partially defeats the "no server" advantage.

Yjs approach: GC pass only after all known peers ACK a checkpoint.
```

---

## 6. OT vs CRDT — Full Comparison

### Memory

```
                    OT                          CRDT
                    ──                          ────

Live storage        O(n) current doc            O(n + d) doc + tombstones
History storage     Sliding window — PRUNABLE   Tombstones — NOT prunable
                    once all clients ACK        without coordination
After session       Just final doc              Final doc + all tombstones
Long-term growth    Stable                      Grows with every deletion
Winner              OT                          ✗
```

### Architecture

```
                    OT                          CRDT
                    ──                          ────

Server required?    YES — assigns revision seq  NO — optional relay
P2P possible?       No                          Yes
Offline handling    Session expires if too long Works forever, just merge
On reconnect        Transform ops against       Merge (union) — no transform
                    all missed server ops
Central bottleneck  Yes (server orders ops)     No
Winner              CRDT                        ✗
```

### Implementation

```
                    OT                          CRDT
                    ──                          ────

Complexity          High — O(n²) transform      Moderate — merge is simpler
                    pairs, TP2 hard to prove    but data structure is richer
Rich text support   Natural — ops carry attrs   Harder — must CRDT-ify attrs
Proven at scale     Google Docs (decades)       Figma, Linear, Notion (newer)
Library support     ShareDB, Quill OT           Yjs, Automerge
Winner              Tie                         —
```

### Decision Guide

```
Choose OT when:
  ✓ You have a central server and want to keep it
  ✓ Memory efficiency matters (large docs, many users)
  ✓ You need rich text formatting (complex op types)
  ✓ Building on proven infra (Google Docs model)
  ✓ You can accept: offline sessions expire

Choose CRDT when:
  ✓ You want offline-first / local-first architecture
  ✓ P2P or edge collaboration is a goal
  ✓ Simpler convergence guarantees are preferred
  ✓ You can accept: tombstone memory overhead
  ✓ Using Yjs/Automerge libraries (don't write from scratch)
```

---

## 7. Offline / Online Sync & WebSockets

### WebSocket — Why Not HTTP

```
HTTP (request/response):
  Client ──── "give me data" ────► Server
  Client ◄─── "here's data" ────  Server
  (connection closed after each exchange)
  Latency: 2× RTT per update — too slow for real-time

WebSocket (persistent, bidirectional):
  Client ◄═══════════════════════► Server
         (stays open, both sides push anytime)
  Latency: 1× RTT per update — fast enough for collab
```

### Online Edit Flow

```
User types 'X'
  │
  ▼
Local document updated IMMEDIATELY (optimistic update — user sees it now)
  │
  ▼
Op created: { type:"insert", char:'X', after:"id42", clientId:"alice", clock:5 }
  │
  ▼
WebSocket.send(op) ───────────────────────────────► Server
                                                      │
                                                   Apply op
                                                   Assign seq: 42
                                                      │
                                        ┌─────────────┴──────────────┐
                                     ACK to Alice              Broadcast to Bob
                                     { seq: 42 }               (op + seq)
  │
  ▼
Alice receives ACK → mark op as confirmed → remove from pending queue
```

### Client State Machine

```
┌──────────────────────────────────────────────────────┐
│                   CLIENT STATES                       │
│                                                       │
│   ONLINE ─────── disconnect ──────► OFFLINE           │
│     ▲                                  │              │
│     └──────────── reconnect ───────────┘              │
│                        │                              │
│                    SYNCING                            │
│             (fetching missed ops,                     │
│              flushing pending queue)                  │
└──────────────────────────────────────────────────────┘

ONLINE:
  WebSocket connected
  Ops sent immediately
  ACKs tracked, pending queue pruned on ACK

OFFLINE:
  Ops saved to IndexedDB (survive page refresh)
  User keeps editing normally
  Pending queue grows

SYNCING:
  WebSocket just reconnected
  1. Send SYNC_REQUEST with lastSeenSeq
  2. Receive CATCH_UP with missed ops
  3. Apply missed ops (CRDT: merge / OT: transform)
  4. Flush pending queue to server
```

### Reconnect Flow (Code)

```javascript
class CollabClient {
    constructor() {
        this.pendingOps  = [];       // ops not yet ACKed by server
        this.lastSeenSeq = 0;        // last server sequence number seen
        this.isOnline    = false;
        this.doc         = new CRDTDocument(); // or OTDocument
    }

    // ── USER EDITS ────────────────────────────────────────
    applyLocalOp(op) {
        this.doc.applyLocal(op);         // instant local update
        this.pendingOps.push(op);
        this.persist();                  // save to IndexedDB
        if (this.isOnline) this.flush();
    }

    // ── SEND QUEUE TO SERVER ──────────────────────────────
    flush() {
        for (const op of this.pendingOps) {
            this.ws.send(JSON.stringify(op));
        }
    }

    // ── SERVER ACK ────────────────────────────────────────
    onServerAck({ seq }) {
        this.pendingOps  = this.pendingOps.filter(op => op.clock > seq);
        this.lastSeenSeq = seq;
        this.persist();
    }

    // ── REMOTE OP FROM ANOTHER USER ──────────────────────
    onServerBroadcast({ op, seq }) {
        this.doc.applyRemote(op);   // CRDT merge OR OT transform
        this.lastSeenSeq = seq;
    }

    // ── RECONNECT ─────────────────────────────────────────
    onReconnect() {
        this.isOnline = true;
        this.ws.send(JSON.stringify({
            type: 'SYNC_REQUEST',
            lastSeenSeq: this.lastSeenSeq,
        }));
        // Wait for CATCH_UP response before flushing
    }

    onCatchUp({ missedOps }) {
        for (const op of missedOps) {
            this.doc.applyRemote(op);
        }
        this.flush(); // now safe to send our pending ops
    }

    // ── DISCONNECT ────────────────────────────────────────
    onDisconnect() {
        this.isOnline = false;
        // pendingOps already in IndexedDB — nothing else needed
    }
}
```

### OT vs CRDT on Reconnect

```
OT reconnect:
  pendingOps have baseRevision=42, server is at revision=100.
  Server must transform each pending op against ops 43..100.
  Complex but server does the heavy lifting.
  O(pending × missed) transforms.

CRDT reconnect:
  pendingOps have stable char IDs.
  Server just merges: apply each op to current state.
  O(pending + missed) — simpler, no transformation.
  Works even if offline for weeks/months.
```

### Optimizations for Offline

```
Version Vectors:
  Each client keeps a vector { alice: 5, bob: 3, carol: 7 }
  meaning "I've seen 5 ops from alice, 3 from bob, 7 from carol"
  On reconnect: compare vectors to find exactly what's missing.
  Avoids re-sending ops already known.

Deletion Buffer:
  Problem: delete op for char X arrives before insert op for char X
  Solution: buffer delete ops, retry after each insert
  { delete: charId } → if charId not found, push to deletionBuffer
  After every insert: scan deletionBuffer, retry deletes

IndexedDB Persistence:
  pendingOps stored as JSON array in IndexedDB
  doc snapshot stored periodically
  On page load: restore from IndexedDB before WebSocket connects
  User sees their offline work instantly, then syncs
```

### User-Facing Status Indicators

```
🟢  Live — WebSocket connected, all changes saved
🟡  Syncing — reconnected, flushing N pending changes
🔴  Offline — changes saved locally, will sync when connected
⚠️  Conflict — rare, prompts user (only in non-CRDT/non-OT fallback)

Banner text examples:
  "Offline — 8 unsaved changes (will sync when connected)"
  "Syncing 8 changes..."
  "All changes saved"
```

---

## 8. Frontend Architecture

### Component Hierarchy

```
<App>
  └── <DocumentPage>
        ├── <Toolbar>              (formatting buttons, share, version history)
        ├── <CollaboratorPresence> (avatars, online count)
        └── <EditorContainer>
              ├── <Editor>         (ProseMirror / TipTap / Slate.js)
              │     ├── Document model (tree of nodes)
              │     ├── Selection/cursor state
              │     ├── History (undo/redo stack)
              │     └── Plugin system (formatting, mentions, comments)
              │
              ├── <CollabLayer>    (CRDT/OT integration)
              │     ├── Local op dispatch
              │     ├── Remote op application
              │     ├── Cursor broadcast (presence)
              │     └── WebSocket management
              │
              ├── <RemoteCursors>  (colored cursors for other users)
              └── <OfflineBanner>  (sync status indicator)
```

### State Architecture

```javascript
// Global document state (in Zustand / Redux)
{
  docId:        "doc_abc123",
  content:      CRDTDocument,          // the live CRDT/OT document
  revision:     42,                    // last server revision seen
  pendingOps:   [...],                 // unsent/unACKed operations
  isOnline:     true,
  syncStatus:   "live" | "syncing" | "offline",

  // Presence
  collaborators: {
    "user_bob":   { name: "Bob", color: "#3b82f6", cursor: { line:5, col:12 } },
    "user_carol": { name: "Carol", color: "#10b981", cursor: { line:2, col:7 } },
  },

  // UI
  selection:    { anchor: 42, head: 55 },
  comments:     [...],
  versions:     [...],
}
```

### Editor Library Integration

```javascript
// Using Yjs + TipTap (recommended for CRDT approach)

import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { Editor } from '@tiptap/react'
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'

const ydoc     = new Y.Doc()
const provider = new WebsocketProvider('wss://your-server', 'doc-id', ydoc)

const editor = new Editor({
  extensions: [
    Collaboration.configure({ document: ydoc }),
    CollaborationCursor.configure({
      provider,
      user: { name: 'Alice', color: '#f59e0b' },
    }),
  ],
})

// Offline: provider buffers ops automatically in IndexedDB via y-indexeddb
// Reconnect: provider replays from stored state — zero custom code needed
```

### Presence — Remote Cursors

```javascript
// Throttle cursor position broadcasts (max 10 per second)
const broadcastCursor = throttle((position) => {
    provider.awareness.setLocalStateField('cursor', {
        anchor: position.anchor,
        head:   position.head,
    });
}, 100);

editor.on('selectionUpdate', ({ editor }) => {
    broadcastCursor(editor.state.selection);
});

// Render remote cursors as colored overlays in the editor DOM
provider.awareness.on('change', () => {
    const states = provider.awareness.getStates();
    renderRemoteCursors(states); // custom rendering layer
});
```

### Undo / Redo in Collaborative Context

```
Problem: Standard undo undoes the last operation in history.
         But "last op" might be someone else's edit.

Solution: Per-user undo stacks.
  Each client only undoes its OWN operations.
  OT: undo op is transformed against all subsequent remote ops before applying.
  CRDT: undo is a new inverse operation, not a history reversal.

Yjs UndoManager:
  const undoManager = new Y.UndoManager(ydoc.getText('content'))
  undoManager.undo()  // only undoes local user's changes
  undoManager.redo()
```

### Performance — Large Documents

```
Problem: CRDT array of 100,000 chars → O(N) sort on every insert

Solutions:

1. 2D Array (M rows × N chars per row):
   Searching: O(log M + log N) with binary search
   Insert:    O(N) only within the affected row
   Trade-off: must handle line-wrap shifts between rows

2. Rope data structure:
   Tree of string segments
   O(log N) insert and delete
   Used in: CodeMirror, Monaco Editor

3. Virtual rendering:
   Only render characters visible in viewport
   requestAnimationFrame batching for DOM updates
   Cursor/selection updates decoupled from content renders

4. Throttle presence broadcasts:
   Cursor position: max 10/sec (100ms throttle)
   Awareness (online status): debounced 500ms
   
5. Compress ops before sending:
   Batch multiple single-char inserts into one string insert op
   Use binary encoding (msgpack) instead of JSON
   ~3-5× bandwidth reduction
```

---

## 9. Backend Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND SYSTEM                            │
│                                                                  │
│   Client A ──WebSocket──┐                                        │
│   Client B ──WebSocket──┤                                        │
│   Client C ──WebSocket──┼──► WebSocket Gateway (stateful)        │
│                         │         │                              │
│                         │    Session Router                      │
│                         │    (route by docId)                    │
│                         │         │                              │
│                         │    ┌────▼─────────────────────┐        │
│                         │    │   Collab Service          │        │
│                         │    │  (one instance per doc)   │        │
│                         │    │                           │        │
│                         │    │  OT:  order ops,          │        │
│                         │    │       transform, broadcast│        │
│                         │    │  CRDT: merge, broadcast   │        │
│                         │    └────┬──────────┬───────────┘        │
│                         │         │          │                    │
│                         │    Op Log DB   Document Store           │
│                         │    (Postgres/  (Postgres/S3)            │
│                         │     Redis)                              │
│                         │         │                              │
│                         │    Message Queue (Kafka/Redis Pub/Sub)  │
│                         │    (fan-out to multiple WS servers)     │
└─────────────────────────────────────────────────────────────────┘
```

### WebSocket Gateway (Stateful Layer)

```javascript
// Each WebSocket connection is stateful — must route to correct collab instance

class WebSocketGateway {
    constructor() {
        this.connections = new Map(); // connId → { ws, userId, docId }
        this.docRooms    = new Map(); // docId  → Set<connId>
    }

    onConnect(ws, { userId, docId }) {
        const connId = generateId();
        this.connections.set(connId, { ws, userId, docId });
        this.docRooms.get(docId)?.add(connId)
            ?? this.docRooms.set(docId, new Set([connId]));

        // Send current document state to new client
        this.sendCurrentState(ws, docId);
        // Notify others of new presence
        this.broadcast(docId, { type: 'USER_JOINED', userId }, connId);
    }

    onMessage(connId, message) {
        const { docId } = this.connections.get(connId);
        // Forward to Collab Service for this docId
        collabService.handleOp(docId, message, connId);
    }

    broadcast(docId, message, excludeConnId = null) {
        for (const connId of this.docRooms.get(docId) ?? []) {
            if (connId !== excludeConnId) {
                this.connections.get(connId)?.ws.send(JSON.stringify(message));
            }
        }
    }

    onDisconnect(connId) {
        const { userId, docId } = this.connections.get(connId);
        this.connections.delete(connId);
        this.docRooms.get(docId)?.delete(connId);
        this.broadcast(docId, { type: 'USER_LEFT', userId });
    }
}
```

### Collab Service — OT Path

```javascript
class OTCollabService {
    constructor(docId) {
        this.docId     = docId;
        this.revision  = 0;
        this.doc       = '';          // current document state
        this.opLog     = [];          // [{ revision, op, clientId }]
        this.clientRevisions = {};    // { clientId: lastSeenRevision }
    }

    handleOp(op, clientId) {
        const baseRev = op.baseRevision;
        const currentRev = this.revision;

        // Transform op against all ops that happened since baseRev
        let transformedOp = op;
        for (let r = baseRev + 1; r <= currentRev; r++) {
            const serverOp = this.opLog[r - 1];
            transformedOp = transform(transformedOp, serverOp.op);
        }

        // Apply transformed op
        this.doc = apply(this.doc, transformedOp);
        this.revision++;

        // Log it
        this.opLog.push({ revision: this.revision, op: transformedOp, clientId });

        // ACK to sender, broadcast to others
        return { transformedOp, revision: this.revision };
    }

    pruneOpLog() {
        const minClientRev = Math.min(...Object.values(this.clientRevisions));
        this.opLog = this.opLog.filter(entry => entry.revision > minClientRev);
    }

    handleSyncRequest(clientId, lastSeenRevision) {
        this.clientRevisions[clientId] = lastSeenRevision;
        const missedOps = this.opLog.filter(e => e.revision > lastSeenRevision);
        return { currentDoc: this.doc, missedOps };
    }
}
```

### Collab Service — CRDT Path

```javascript
class CRDTCollabService {
    constructor(docId) {
        this.docId = docId;
        this.doc   = new CRDTDocument(); // server-side CRDT
        this.opLog = [];                 // for catch-up on reconnect
        this.seq   = 0;
    }

    handleOp(op, clientId) {
        // No transformation needed — just merge
        this.doc.apply(op);
        this.seq++;
        this.opLog.push({ seq: this.seq, op, clientId });

        // Prune old ops (safe once all clients ACK past a seq)
        this.maybePrune();

        return { seq: this.seq };
    }

    handleSyncRequest(clientId, lastSeenSeq) {
        const missedOps = this.opLog.filter(e => e.seq > lastSeenSeq);
        // For very long offline: send full doc state + ops
        if (missedOps.length > FULL_SYNC_THRESHOLD) {
            return { type: 'FULL_STATE', state: this.doc.serialize() };
        }
        return { type: 'CATCH_UP', missedOps };
    }
}
```

### Database Schema

```sql
-- Documents table
CREATE TABLE documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL DEFAULT 'Untitled',
    owner_id     UUID NOT NULL REFERENCES users(id),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Document content (snapshots)
CREATE TABLE document_snapshots (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id),
    revision     INTEGER NOT NULL,          -- OT revision number
    content      JSONB NOT NULL,            -- serialized doc state
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, revision)
);

-- Operation log (OT: sliding window / CRDT: for catch-up)
CREATE TABLE document_ops (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id),
    seq          INTEGER NOT NULL,          -- global sequence number
    client_id    UUID NOT NULL,
    op_type      TEXT NOT NULL,             -- 'insert' | 'delete' | 'format'
    op_data      JSONB NOT NULL,            -- the operation payload
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, seq)
);
CREATE INDEX idx_ops_document_seq ON document_ops(document_id, seq);

-- Collaborators / permissions
CREATE TABLE document_collaborators (
    document_id  UUID REFERENCES documents(id),
    user_id      UUID REFERENCES users(id),
    role         TEXT NOT NULL DEFAULT 'editor', -- 'viewer' | 'editor' | 'owner'
    joined_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (document_id, user_id)
);

-- Comments
CREATE TABLE comments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id),
    user_id      UUID NOT NULL REFERENCES users(id),
    anchor_start INTEGER NOT NULL,          -- character position (snapshot-anchored)
    anchor_end   INTEGER NOT NULL,
    content      TEXT NOT NULL,
    resolved     BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Version history
CREATE TABLE document_versions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id),
    label        TEXT,                      -- "Version before meeting"
    snapshot_id  UUID REFERENCES document_snapshots(id),
    created_by   UUID REFERENCES users(id),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### WebSocket Message Protocol

```javascript
// Client → Server
{ type: "OP",           op: {...}, baseRevision: 42                     }
{ type: "SYNC_REQUEST", lastSeenSeq: 41                                 }
{ type: "ACK",          revision: 50                                    }  // for pruning
{ type: "CURSOR",       position: { anchor: 42, head: 55 }              }
{ type: "PING"                                                          }

// Server → Client (sender)
{ type: "ACK",          seq: 42                                         }

// Server → Client (others)
{ type: "REMOTE_OP",    op: {...}, seq: 42, clientId: "alice"           }
{ type: "CATCH_UP",     missedOps: [...], currentRevision: 50           }
{ type: "FULL_STATE",   state: {...}, revision: 50                      }
{ type: "USER_JOINED",  user: { id, name, color }                       }
{ type: "USER_LEFT",    userId: "abc"                                   }
{ type: "CURSOR",       userId: "alice", position: { anchor:5, head:5 } }
{ type: "PONG"                                                          }
```

### Scaling WebSocket Servers

```
Problem: WebSocket connections are stateful.
         All clients editing the same doc must be on the same server,
         OR messages must be routed between servers.

Solution 1 — Sticky Sessions:
  Load balancer routes all connections for docId X to server A.
  Simple but creates hot spots.

Solution 2 — Redis Pub/Sub (fan-out):
  Any server can receive an op.
  Publish op to Redis channel: "doc:{docId}"
  All servers subscribed to that channel forward to their local connections.

  Client A (Server 1) ──op──► Server 1
                               │
                           Publish to Redis "doc:123"
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
          Server 1         Server 2         Server 3
          (forward         (forward         (forward
           to A's           to B's           to C's
           socket)          socket)          socket)

Solution 3 — Collab Service per Document (Actor model):
  One process/actor owns each document.
  Routes ops through a message queue (Kafka/Redis).
  Elixir/Erlang process model is ideal for this.
```

### Snapshot & Version History

```
Problem: Op log grows over time. Full replay from op 1 is slow.

Solution: Periodic snapshots + op log from snapshot point.

Every N ops OR every M minutes:
  1. Serialize current doc to JSON/binary
  2. Store as snapshot at revision R
  3. Op log before R can be safely archived/deleted

On client load:
  Fetch latest snapshot → restore doc state
  Fetch ops after snapshot revision → replay
  Ready in O(ops since snapshot) instead of O(all ops ever)

Version history:
  User clicks "See version history"
  → Fetch snapshots list
  → User picks a point in time
  → Restore snapshot + replay ops up to that timestamp
  → Read-only preview of that version
```

### REST API Endpoints

```
Document Management:
  POST   /api/documents                     Create new document
  GET    /api/documents/:id                 Fetch document metadata
  PATCH  /api/documents/:id                 Update title, settings
  DELETE /api/documents/:id                 Delete document

Collaboration:
  GET    /api/documents/:id/snapshot        Latest snapshot + revision
  GET    /api/documents/:id/ops?from=42     Ops since revision 42
  GET    /api/documents/:id/collaborators   List collaborators
  POST   /api/documents/:id/collaborators   Invite collaborator
  DELETE /api/documents/:id/collaborators/:userId  Remove

Comments:
  GET    /api/documents/:id/comments        All comments
  POST   /api/documents/:id/comments        Add comment
  PATCH  /api/comments/:id                  Resolve / edit comment
  DELETE /api/comments/:id                  Delete comment

Versions:
  GET    /api/documents/:id/versions        List named versions
  POST   /api/documents/:id/versions        Save named version
  GET    /api/documents/:id/versions/:vid   Fetch specific version

Auth:
  WebSocket upgrade authenticated via:
    JWT in Authorization header, OR
    Short-lived token from GET /api/documents/:id/ws-token
```

---

## 10. Data Models & API Design

### Operation Schema

```typescript
// Base operation
interface BaseOp {
    clientId:     string;          // UUID of the client/user
    clock:        number;          // Lamport clock — monotonically increasing per client
    docId:        string;          // document this op belongs to
    timestamp:    number;          // wall clock (for display only, NOT ordering)
}

// OT operations (position-based)
interface OTInsertOp extends BaseOp {
    type:         'insert';
    pos:          number;          // absolute position in document
    chars:        string;          // one or more characters (batched)
    baseRevision: number;          // server revision this was based on
    attrs?:       TextAttributes;  // formatting: bold, italic, color, etc.
}

interface OTDeleteOp extends BaseOp {
    type:         'delete';
    pos:          number;
    length:       number;          // number of characters to delete
    baseRevision: number;
}

// CRDT operations (ID-based)
interface CRDTInsertOp extends BaseOp {
    type:   'insert';
    id:     [string, number];      // [clientId, clock] — unique char ID
    after:  [string, number] | null; // insert after this char ID
    char:   string;
    attrs?: TextAttributes;
}

interface CRDTDeleteOp extends BaseOp {
    type:   'delete';
    id:     [string, number];      // char ID to tombstone
}

interface TextAttributes {
    bold?:          boolean;
    italic?:        boolean;
    underline?:     boolean;
    strikethrough?: boolean;
    color?:         string;        // hex
    fontSize?:      number;        // px
    link?:          string;        // URL
    heading?:       1 | 2 | 3;
}
```

### Document Snapshot Schema

```typescript
interface DocumentSnapshot {
    docId:    string;
    revision: number;           // OT revision OR CRDT vector clock
    content:  DocNode;          // rich text tree
    metadata: {
        createdAt:   string;
        updatedAt:   string;
        charCount:   number;
        wordCount:   number;
    };
}

// Rich text node (ProseMirror-style)
interface DocNode {
    type:    'doc' | 'paragraph' | 'heading' | 'text' | 'image' | 'table';
    attrs?:  Record<string, unknown>;
    content?: DocNode[];
    text?:   string;
    marks?:  Array<{ type: string; attrs?: Record<string, unknown> }>;
}
```

---

## 11. Performance Optimizations

### Frontend

```
1. Virtual rendering (long documents):
   Only render paragraphs/lines visible in viewport.
   Use IntersectionObserver to track visible range.
   Off-screen content: render as placeholder div with correct height.

2. Batch DOM updates:
   Collect all incoming remote ops in a 16ms frame.
   Apply in one batch inside requestAnimationFrame.
   Prevents layout thrashing from rapid consecutive updates.

3. Throttle presence broadcasts:
   Cursor position:  100ms throttle (10 updates/sec max)
   Online status:    500ms debounce
   Selection range:  200ms debounce

4. Compress op payloads:
   Batch single-char inserts into multi-char ops before sending.
   Use MessagePack (binary) instead of JSON: ~40% smaller.
   Compress with zlib for large snapshots.

5. Lazy load heavy content:
   Images, embeds, tables: load on scroll into view.
   Code blocks: lazy-load syntax highlighter.

6. Web Worker for CRDT merge:
   Move CRDT sort/merge off the main thread.
   Post merged state back to main thread for rendering.
   Keeps UI responsive during heavy sync.
```

### Backend

```
1. Connection pooling:
   WebSocket connections: use event loop (Node.js / Erlang) — no thread per conn.
   DB connections: pool of 20-50, use pgBouncer for Postgres.

2. Op batching at ingestion:
   Accept ops in bursts, batch-write to DB every 100ms.
   Reduces DB write amplification significantly.

3. Redis for hot data:
   Active document state in Redis (fast read/write).
   Flush to Postgres every 30 seconds or on idle.
   Redis pub/sub for cross-server fan-out.

4. Horizontal scaling:
   Stateless HTTP servers: scale freely.
   WebSocket servers: scale with Redis pub/sub fan-out.
   Collab service: shard by docId (consistent hashing).

5. Op log compaction:
   Prune ops confirmed by all clients (OT).
   Archive old ops to cold storage (S3) for audit trail.
   Snapshots every 1000 ops to speed up load time.

6. CDN for snapshots:
   Document load fetches snapshot from CDN edge.
   Only the incremental ops come from origin.
   Reduces latency for initial document open.
```

---

## 12. Edge Cases & Failure Modes

```
1. Network partition (user offline):
   CRDT: works perfectly, merge on reconnect
   OT:   works up to session timeout, then forces full reload

2. Two users delete same character:
   OT:   transform_delete_delete → NoOp for second delete ✓
   CRDT: tombstone is idempotent — setting deleted=true twice = deleted=true ✓

3. User reconnects with very stale state:
   Send full document snapshot instead of ops list
   Client discards local state, loads snapshot, replays recent ops

4. Server crashes mid-operation:
   Client didn't receive ACK → op stays in pendingOps
   Client retries on reconnect → server applies op (idempotent via op ID)
   Server must deduplicate by (clientId, clock)

5. Concurrent insert at same position:
   OT:   tie-break by client_id in transform function
   CRDT: tie-break by client_id in sort order
   Both deterministic → all clients converge to same order ✓

6. Clock skew / reordering:
   Don't use wall clock for ordering — use Lamport logical clocks
   Lamport clock: max(local, received) + 1 on every message

7. Very large documents (> 1MB):
   Chunk the document into pages/sections
   Each section is a separate CRDT/OT scope
   Load only visible sections; lazy-load others

8. Presence ghost (user closed tab without clean disconnect):
   Server detects WebSocket close → broadcast USER_LEFT immediately
   Heartbeat (PING/PONG every 30s): if missed 3 → evict from presence

9. Op arrives referencing deleted anchor (CRDT):
   Deletion buffer: hold the op, retry after next insert
   After N retries: apply at nearest valid ancestor position

10. Undo in collaborative context:
    Standard undo would undo other users' changes too
    Solution: per-user undo stack, only undo own ops
    Undo op = inverse op (re-insert deleted char, re-delete inserted char)
    Must be transformed against all remote ops applied since original op
```

---

## 13. Interview Cheatsheet

### Requirements to Clarify

```
✓ How many concurrent editors per document? (10? 100? 1000?)
✓ Rich text (bold, tables) or plain text only?
✓ Offline support required?
✓ P2P / local-first, or centralized server?
✓ Version history / undo needed?
✓ Comments and suggestions?
✓ Mobile support (lower bandwidth, unreliable network)?
```

### The Decision Framework

```
Question: OT or CRDT?

Has a central server + memory efficiency matters?  → OT
Offline-first / P2P / simpler convergence needed?  → CRDT
Building from scratch (no library)?               → OT (more literature)
Using a library?                                  → Yjs (CRDT) — much easier
```

### Key Numbers to Know

```
WebSocket latency target:  < 100ms for edits to appear on remote clients
Presence throttle:         100ms (cursor), 500ms (status)
Heartbeat interval:        30 seconds PING/PONG
Session timeout (OT):      Hours to days (site-specific policy)
Snapshot frequency:        Every 1000 ops OR 30 minutes idle
Op log pruning:            Safe after min(all client revisions) ACKed
CRDT GC:                   Only after all peers ACK a checkpoint
```

### Trade-Off Talking Points

```
OT:
  + Proven at scale (Google Docs)
  + Memory efficient (prunable op log)
  + Natural for rich text formatting
  - Requires central server
  - Complex transform functions (TP2 property)
  - Session expires if offline too long

CRDT:
  + No server needed (P2P possible)
  + Offline forever — merge on return
  + Simpler convergence (math guarantees)
  - Tombstone memory overhead
  - GC requires coordination
  - Less mature for complex rich text

WebSocket vs HTTP polling:
  WebSocket: persistent, low latency, bidirectional — right choice for collab
  HTTP SSE:  server push only, no client push — wrong for editing
  HTTP poll: too slow (100-1000ms latency) — unacceptable

Optimistic updates:
  Always apply locally first, reconcile on server ACK
  User never waits for round-trip to see their own edit
```

### One-Liners for Each Concept

```
OT:      "Send the intent, transform the position."
CRDT:    "Design the data structure so conflicts are impossible by math."
Tombstone: "Mark as deleted but keep as anchor for future inserts."
Revision:  "OT's global clock — lets server know what to transform against."
Merge:     "CRDT's reconnect strategy — union the sets, math handles the rest."
Presence:  "Broadcast cursor positions via WebSocket, throttled to 10/sec."
IndexedDB: "The offline buffer — ops survive page refresh, sync on reconnect."
Snapshot:  "Checkpoint of full doc state — avoids replaying all ops from op 1."
```

---

*Based on: OT (Jupiter algorithm, Google Docs), CRDT (LSEQ, RGA, Yjs, Automerge),
WebSocket sync patterns, and production architectures at Google, Figma, Notion, Linear.*
