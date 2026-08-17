# Web Workers — Multithreading on the Web

> Covers the Web Worker execution model, message-passing internals, practical use cases,
> common misconceptions, and production-grade patterns for offloading work off the main thread.

---

## Table of Contents

1. [The Core Problem — JavaScript Is Single-Threaded](#1-the-core-problem--javascript-is-single-threaded)
2. [What a Web Worker Actually Is](#2-what-a-web-worker-actually-is)
3. [Basic Usage](#3-basic-usage)
4. [What Workers Can and Cannot Do](#4-what-workers-can-and-cannot-do)
5. [Practical Use Cases](#5-practical-use-cases)
6. [Dedicated Worker vs Shared Worker vs Service Worker](#6-dedicated-worker-vs-shared-worker-vs-service-worker)
7. [Communication Overhead & How to Reduce It](#7-communication-overhead--how-to-reduce-it)
8. [Transferable Objects & SharedArrayBuffer](#8-transferable-objects--sharedarraybuffer)
9. [Common Misconceptions (Corrections)](#9-common-misconceptions-corrections)
10. [Debugging Workers](#10-debugging-workers)
11. [Libraries That Simplify Workers](#11-libraries-that-simplify-workers)
12. [Decision Checklist — Should You Use a Worker?](#12-decision-checklist--should-you-use-a-worker)
13. [Web Worker vs `async`/`await` vs `useEffect`](#13-web-worker-vs-asyncawait-vs-useeffect)

---

## 1. The Core Problem — JavaScript Is Single-Threaded

Every tab in a browser has one "main thread" responsible for:

- Executing your JavaScript
- Rendering the DOM
- Handling user input (clicks, scrolls, key presses)
- Running layout/paint/composite

```
Main thread timeline (single-threaded):

|--JS runs--|--JS runs--|----HEAVY COMPUTATION (500ms)----|--JS runs--|
                                    ▲
                          Page is FROZEN here.
                          No clicks register. No scrolling. No animation.
                          The browser looks "hung" even though it isn't.
```

Anything synchronous and slow — a big loop, expensive JSON parsing, image
manipulation, complex calculations — blocks this ONE thread completely
until it finishes. There is no way around this without moving the work
somewhere else.

---

## 2. What a Web Worker Actually Is

A Web Worker runs a separate JavaScript file on a genuinely different OS-level
thread. It does **not** share memory with the main thread — the two
communicate exclusively by **passing messages**, where the data is
**copied** (technically: structured-cloned) across the thread boundary.

```
┌─────────────────────────┐        postMessage()        ┌─────────────────────────┐
│      Main Thread          │ ───────────────────────────→ │      Worker Thread        │
│  - Renders UI              │                              │  - No DOM access           │
│  - Handles user input       │ ←─────────────────────────── │  - No window/document      │
│  - Runs your app code       │        postMessage()          │  - Runs worker.js in a     │
│                            │                              │    sandboxed environment   │
└─────────────────────────┘                              └─────────────────────────┘
       (this thread must                                        (this thread can block
        never be blocked)                                        for as long as it wants)
```

Because there's no shared memory by default, a worker can never directly
corrupt or race against the main thread's data — the message-passing
boundary enforces isolation, which is also why a crash or infinite loop
inside a worker doesn't take down the rest of the page.

---

## 3. Basic Usage

```javascript
// main.js
const worker = new Worker('worker.js');

worker.postMessage('Hello, worker!');

worker.onmessage = (event) => {
  console.log('Worker said:', event.data);
};

worker.onerror = (event) => {
  console.error('Worker error:', event.message, event.filename, event.lineno);
};
```

```javascript
// worker.js
self.onmessage = (event) => {
  console.log('Main thread said:', event.data);
  self.postMessage('Hello, main thread!');
};
```

Always attach `onerror` in production — an uncaught exception inside a
worker does NOT throw in the main thread; it silently fails unless you're
listening for it.

Cleaning up a worker you no longer need:

```javascript
worker.terminate();   // from the main thread — immediately stops the worker
// or, from inside the worker itself:
self.close();
```

Forgetting to terminate workers that are no longer needed is a real memory
leak source in long-lived single-page apps (e.g. a worker created per
opened document/tab that's never cleaned up when the tab closes).

---

## 4. What Workers Can and Cannot Do

| Capability | Available in a Worker? |
|---|---|
| `fetch`, `XMLHttpRequest`, WebSocket | ✅ Yes |
| `setTimeout` / `setInterval` | ✅ Yes |
| `IndexedDB` | ✅ Yes |
| `console.log` | ✅ Yes |
| Importing other scripts (`importScripts`) or ES modules | ✅ Yes |
| DOM (`document`, elements, `window`) | ❌ No |
| `localStorage` / `sessionStorage` (synchronous storage) | ❌ No |
| Direct access to variables/objects on the main thread | ❌ No (must message-pass) |
| Spawning another nested Worker | ✅ Yes (workers can spawn workers) |

The DOM restriction is fundamental, not incidental: the DOM is not
thread-safe, so allowing worker threads to touch it would reintroduce all
the race conditions multithreading is supposed to avoid. If you need a
worker's result reflected in the UI, it sends the RESULT back via
`postMessage`, and the main thread does the actual DOM update.

---

## 5. Practical Use Cases

### 5.1 Offloading CPU-intensive computation

```javascript
// main.js
const worker = new Worker('worker.js');
worker.onmessage = (event) => console.log('Result:', event.data);
worker.postMessage({ num: 1_000_000 });
```

```javascript
// worker.js
function compute(num) {
  let sum = 0;
  for (let i = 0; i < num; i++) sum += i;
  return sum;
}

self.onmessage = (event) => {
  const result = compute(event.data.num);
  self.postMessage(result);
};
```

The main thread stays responsive (scrolling, clicks, animations keep
working) while the worker grinds through the loop on its own thread.

### 5.2 Parallel independent computations

```javascript
// main.js
worker.postMessage({ nums: [1_000_000, 2_000_000, 3_000_000] });
```

```javascript
// worker.js
self.onmessage = (event) => {
  const results = event.data.nums.map(compute);
  self.postMessage(results);
};
```

Note: a single worker still runs its own code on ONE thread — `.map()`
here runs sequentially inside that one worker. True parallelism across
multiple CPU cores requires spinning up MULTIPLE worker instances (a
"worker pool") and splitting the input across them, not just running an
array method inside a single worker.

```javascript
// Real parallelism: a small worker pool
const NUM_WORKERS = navigator.hardwareConcurrency || 4;
const pool = Array.from({ length: NUM_WORKERS }, () => new Worker('worker.js'));

function runOnPool(tasks) {
  return Promise.all(
    tasks.map((task, i) => {
      const worker = pool[i % pool.length];
      return new Promise((resolve) => {
        worker.onmessage = (e) => resolve(e.data);
        worker.postMessage(task);
      });
    })
  );
}
```

### 5.3 Background network requests + response processing

```javascript
// worker.js
async function request(url) {
  const response = await fetch(url);
  return response.json();
}

self.onmessage = async (event) => {
  const results = await Promise.all(event.data.urls.map(request));
  self.postMessage(results);
};
```

Note the nuance here: `fetch` itself is already non-blocking on the main
thread (it's async by nature via the browser's network stack). The real
win from doing this in a worker is when you're also doing **heavy
processing of the responses** (e.g. parsing a huge JSON payload, decoding
large binary data) — THAT part would otherwise block the main thread even
though the network request wouldn't.

---

## 6. Dedicated Worker vs Shared Worker vs Service Worker

These three are often confused — they solve different problems.

```
┌───────────────────────────────────────────────────────────────────────┐
│ Dedicated Worker (new Worker(...))                                    │
├───────────────────────────────────────────────────────────────────────┤
│ • Belongs to ONE tab/page only                                        │
│ • Dies when that tab closes                                           │
│ • Use for: per-page CPU offloading (the examples above)              │
├───────────────────────────────────────────────────────────────────────┤
│ SharedWorker (new SharedWorker(...))                                  │
├───────────────────────────────────────────────────────────────────────┤
│ • Shared across MULTIPLE tabs/windows from the SAME origin            │
│ • Survives as long as at least one connected tab is open              │
│ • Communication uses a `port` object per connected tab, not a plain   │
│   `postMessage` directly on the worker                                │
│ • Use for: a single shared WebSocket/SSE connection across tabs, a    │
│   shared in-memory cache, deduplicating identical work across tabs    │
├───────────────────────────────────────────────────────────────────────┤
│ Service Worker (navigator.serviceWorker.register(...))                │
├───────────────────────────────────────────────────────────────────────┤
│ • NOT for computation — it's a programmable network proxy             │
│ • Sits between your page and the network; intercepts fetch requests   │
│ • Survives even when NO tab is open (can wake up for push events)     │
│ • Use for: offline caching, PWA install, background sync, push        │
│   notifications — an entirely different problem domain from the       │
│   "CPU offloading" workers described in this document                 │
└───────────────────────────────────────────────────────────────────────┘
```

```javascript
// SharedWorker example — multiple tabs, one underlying worker
const worker = new SharedWorker('shared-worker.js');
worker.port.start();
worker.port.postMessage('hello from a tab');
worker.port.onmessage = (event) => console.log(event.data);
```

```javascript
// shared-worker.js
const ports = [];

self.onconnect = (event) => {
  const port = event.ports[0];
  ports.push(port);

  port.onmessage = (e) => {
    // Broadcast to all connected tabs
    for (const p of ports) p.postMessage(`echo: ${e.data}`);
  };
};
```

---

## 7. Communication Overhead & How to Reduce It

Every `postMessage` call has real, non-zero cost: a thread hop plus
structured-clone serialization of whatever you send. Sending thousands of
tiny messages per second adds up.

### Message batching

```javascript
// Inside a worker producing many small results rapidly
const queue = [];
const FLUSH_SIZE = 50;
let flushTimer = null;

function enqueue(item) {
  queue.push(item);
  if (queue.length >= FLUSH_SIZE) {
    flush();
  } else if (!flushTimer) {
    flushTimer = setTimeout(flush, 16); // ~1 frame, avoids unbounded delay
  }
}

function flush() {
  if (queue.length === 0) return;
  self.postMessage(queue.splice(0, queue.length));
  clearTimeout(flushTimer);
  flushTimer = null;
}
```

Batching trades a small amount of latency (up to one batch window) for a
large reduction in the NUMBER of cross-thread hops, which is usually a
clear win when producing many small updates.

---

## 8. Transferable Objects & SharedArrayBuffer

By default, `postMessage` **clones** data — for large binary buffers
(images, audio, big typed arrays), cloning megabytes of data on every
message is wasteful.

### Transferable objects — move instead of copy

```javascript
// main.js
const buffer = new ArrayBuffer(1024 * 1024 * 10); // 10 MB
worker.postMessage({ buffer }, [buffer]);
// After this call, `buffer` is NEUTERED (byteLength becomes 0) on the
// main thread — ownership was transferred, not copied. Zero-copy, instant.
```

This works for `ArrayBuffer`, `MessagePort`, `ImageBitmap`, and a few
other transferable types — check per-object support, not all objects
qualify.

### SharedArrayBuffer — actual shared memory (not a Worker alternative!)

`SharedArrayBuffer` lets multiple workers (and the main thread) read/write
the SAME underlying memory directly, with no copying and no message-passing
needed for the data itself — messages are then only used for
signaling/coordination, not data transfer.

```javascript
// main.js
const sab = new SharedArrayBuffer(1024);
const view = new Int32Array(sab);
worker.postMessage(sab); // the SharedArrayBuffer itself IS shareable, no transfer needed

// Both the main thread's `view` and the worker's view of the same buffer
// now point at the SAME memory. Writes from either side are visible to
// the other — but this reintroduces the race-condition risk that
// message-passing normally protects you from, so coordinate access with
// Atomics (Atomics.wait, Atomics.notify, Atomics.compareExchange, etc.).
```

```javascript
// worker.js
self.onmessage = (event) => {
  const view = new Int32Array(event.data);
  Atomics.add(view, 0, 1); // atomic increment — safe even with concurrent writers
};
```

Important: `SharedArrayBuffer` is a companion feature used ALONGSIDE
workers to avoid the copy cost of `postMessage` for large shared data —
it is not, as sometimes miscategorized, an "alternative to Web Workers."
It also requires specific cross-origin isolation HTTP headers
(`Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: require-corp`) to be enabled in modern
browsers, due to Spectre-class security concerns.

---

## 9. Common Misconceptions (Corrections)

```
❌ "WebSockets are an alternative multithreading technique to Web Workers."
✅ WebSockets are a network protocol for client-server communication —
   entirely unrelated to running code across multiple threads. Don't
   conflate networking concurrency with CPU concurrency.

❌ "Using forEach/reduce instead of a for-loop avoids loading the whole
   array into memory at once."
✅ forEach, reduce, and a plain for-loop all iterate over the SAME array
   that is already fully in memory — none of them changes when/how the
   array itself got loaded. Iteration style has no effect on memory
   footprint here. To actually avoid holding a huge dataset in memory,
   you need to stream/chunk the SOURCE data itself (e.g. process a
   ReadableStream incrementally, or paginate).

❌ "Wrapping a long computation in setTimeout(fn, 0) makes it run
   asynchronously / non-blocking."
✅ setTimeout only defers WHEN a function starts running (to the next
   event-loop tick) — once it starts, it still runs to completion
   synchronously and blocks whichever thread it's on for that entire
   duration. It does not chop the work into interruptible pieces. Inside
   a worker, that's fine for the main thread (which isn't affected
   either way), but it can still stall OTHER pending work in that same
   worker. To make heavy work genuinely interruptible, break it into
   chunks and yield periodically (e.g. process N items, then
   setTimeout/postMessage before continuing), or use multiple workers.

❌ "A Web Worker gives you access to more memory/resources than the main
   thread."
✅ Workers run in the same overall browser process/tab resource budget
   in most implementations — they help with THREAD contention (keeping
   the UI thread free), not with any expanded memory ceiling.

❌ "SharedWorker and Service Worker are just fancier Web Workers."
✅ They solve different problems entirely (see Section 6) — SharedWorker
   is about cross-tab computation sharing, Service Worker is a network
   proxy for offline/caching/push, and neither is primarily about raw
   CPU offloading the way a dedicated Worker is.
```

---

## 10. Debugging Workers

- Chrome DevTools: open the **Sources** panel → look for a separate
  thread/context selector (top-left dropdown, usually says "top" by
  default) → switch to the worker's context to set breakpoints inside it.
- `console.log` inside a worker still shows up in the same DevTools
  console, usually tagged with the worker's script name.
- Uncaught exceptions inside a worker do NOT propagate to
  `window.onerror` on the main thread — you must attach `worker.onerror`
  explicitly, or they fail silently.
- For message-flow debugging, log both sides of every `postMessage` call
  during development (strip or gate behind a debug flag in production —
  logging large payloads on every message adds real overhead).

---

## 11. Libraries That Simplify Workers

| Library | What it does |
|---|---|
| **Comlink** | Lets you call worker functions as if they were normal async functions/promises — hides all the manual `postMessage`/`onmessage` plumbing behind a proxy object |
| **Workerize** | Turns an existing module into a worker automatically, exposing its exports as async functions |
| **WorkerDOM** | Experimental — runs a subset of DOM operations inside a worker via a virtual DOM-like bridge, for cases where you want most of your app logic off the main thread |

```javascript
// Comlink example — feels like calling a normal function
import { wrap } from 'comlink';

const worker = new Worker('worker.js');
const api = wrap(worker);

const result = await api.compute(1_000_000); // looks synchronous, actually cross-thread
```

---

## 12. Decision Checklist — Should You Use a Worker?

```
Use a Web Worker when:
  ✅ You have a genuinely CPU-bound task (not I/O-bound — fetch/network
     calls are already non-blocking without a worker)
  ✅ The task takes long enough to visibly affect UI responsiveness
     (roughly: anything that could take more than ~50ms on the main
     thread is a candidate — that's the widely-cited threshold before
     users perceive jank)
  ✅ The task doesn't need to touch the DOM mid-computation
  ✅ You're willing to accept the added complexity of message-passing
     and (if needed) a small serialization/copy cost

Skip a Web Worker when:
  ❌ The task is I/O-bound (network requests, timers) — async/await on
     the main thread already handles this without blocking
  ❌ The task is trivially fast (<10-20ms) — the thread-hop + clone
     overhead of postMessage can exceed the cost of just doing it inline
  ❌ The task needs frequent, low-latency DOM interaction throughout its
     execution (better to keep it on the main thread and yield
     periodically instead)
```

---

## 13. Web Worker vs `async`/`await` vs `useEffect`

These three get lumped together as "ways to do something off to the side,"
but they solve three completely different problems and operate at three
different layers. Confusing them is one of the most common mistakes in
React apps that try to "optimize" with a worker when the real issue was
just a missing `await`, or a missed dependency.

### 13.1 What each one actually is

```
┌──────────────────────────────────────────────────────────────────────┐
│ async/await                                                          │
├──────────────────────────────────────────────────────────────────────┤
│ • Syntax sugar over Promises                                         │
│ • STILL runs on the main thread, on ONE thread                       │
│ • Solves: "don't block on I/O" (network, timers, file reads)         │
│ • Does NOT solve: CPU-bound work — a tight synchronous loop inside   │
│   an async function still blocks the main thread once it starts,    │
│   `await` only yields at points where you're actually waiting on     │
│   something external                                                 │
├──────────────────────────────────────────────────────────────────────┤
│ useEffect (React)                                                    │
├──────────────────────────────────────────────────────────────────────┤
│ • A lifecycle hook — runs code after render, tied to the component   │
│   tree and its dependency array                                      │
│ • STILL runs on the main thread                                      │
│ • Solves: "run this side effect when the component mounts/updates/   │
│   unmounts" (subscriptions, fetches, DOM measurements, syncing with  │
│   external systems)                                                   │
│ • Does NOT solve: blocking work, threading, or concurrency at all —  │
│   it's purely about WHEN code runs relative to render, not WHERE     │
│   (which thread) it runs                                             │
├──────────────────────────────────────────────────────────────────────┤
│ Web Worker                                                            │
├──────────────────────────────────────────────────────────────────────┤
│ • An actual separate OS-level thread                                 │
│ • Solves: "don't block the main thread with CPU-bound work" — the    │
│   only one of the three that changes WHICH thread code runs on      │
│ • Does NOT solve: React lifecycle timing or Promise ergonomics —     │
│   you still need async/await (for messaging) and useEffect (for     │
│   wiring it into a component) around it                              │
└──────────────────────────────────────────────────────────────────────┘
```

The key distinction: `async`/`await` and `useEffect` are both about
**scheduling/timing on the same single thread**. A Web Worker is about
**physically executing code on a different thread**. They aren't
competing solutions to the same problem — a real app typically uses all
three together, each for what it's actually good at.

### 13.2 Why `async`/`await` doesn't help with CPU-bound work

```javascript
// Looks async, but this STILL freezes the UI
async function computeSum(n) {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += i; // synchronous, blocking, no await inside
  return sum;
}

async function handleClick() {
  console.log('start');
  const result = await computeSum(5_000_000_000); // blocks main thread the whole time
  console.log(result);
}
```

`await` only yields control back to the event loop at the point where
there's actually something asynchronous to wait for (a pending Promise
resolving from I/O, a timer, etc.). A synchronous loop has nothing to
await, so the function runs start-to-finish on the main thread exactly as
if `async` weren't there at all — clicks, scrolling, and animations all
freeze for the loop's entire duration. Moving `computeSum` into a worker
(and awaiting `worker.postMessage`/`onmessage` from the main thread
instead) is what actually keeps the UI responsive:

```javascript
// main.js — this one genuinely doesn't block the UI
async function handleClick() {
  console.log('start');
  const result = await runOnWorker(5_000_000_000); // main thread is free while this runs
  console.log(result);
}

function runOnWorker(n) {
  return new Promise((resolve) => {
    const worker = new Worker('worker.js');
    worker.onmessage = (e) => {
      resolve(e.data);
      worker.terminate();
    };
    worker.postMessage(n);
  });
}
```

### 13.3 Why `useEffect` doesn't help with CPU-bound work either

```jsx
// This still freezes the whole page on mount — useEffect changes WHEN
// it runs (after render), not WHICH thread it runs on
function ReportPanel({ rows }) {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    const result = heavyAggregate(rows); // synchronous, CPU-bound, main thread
    setSummary(result);
  }, [rows]);

  return summary ? <Summary data={summary} /> : <Spinner />;
}
```

`useEffect` correctly defers `heavyAggregate` until after the component
has painted once, so the user briefly sees the `<Spinner />` — but the
moment the effect fires, `heavyAggregate` still runs synchronously on the
main thread and can freeze scrolling/input for however long it takes.
Combining a worker with `useEffect` gets you both benefits: the effect
decides WHEN to kick off the work (on mount/when `rows` changes), and the
worker decides WHERE it runs (off the main thread):

```jsx
function ReportPanel({ rows }) {
  const [summary, setSummary] = useState(null);
  const workerRef = useRef(null);

  useEffect(() => {
    const worker = new Worker('aggregate-worker.js');
    workerRef.current = worker;

    worker.onmessage = (event) => setSummary(event.data);
    worker.postMessage(rows);

    return () => worker.terminate(); // cleanup on unmount or before the next run
  }, [rows]);

  return summary ? <Summary data={summary} /> : <Spinner />;
}
```

### 13.4 Side-by-side comparison

| | `async`/`await` | `useEffect` | Web Worker |
|---|---|---|---|
| Changes which thread runs the code | ❌ No | ❌ No | ✅ Yes |
| Prevents blocking on I/O (network, timers) | ✅ Yes | ➖ Only via what's inside it | ➖ Not its purpose (I/O is already non-blocking) |
| Prevents blocking on CPU-bound loops | ❌ No | ❌ No | ✅ Yes |
| Tied to React component lifecycle | ❌ No | ✅ Yes | ❌ No (framework-agnostic) |
| Adds real overhead (serialization, thread hop) | ❌ No | ❌ No | ✅ Yes (via `postMessage`) |
| Typical use | Awaiting a fetch, a timer, a DB call | Running a fetch/subscription on mount or when deps change | Offloading a genuinely CPU-heavy computation |

### 13.5 How they compose in practice

```
User clicks "Generate Report"
        │
        ▼
useEffect (or event handler) decides WHEN to start the work
        │
        ▼
async/await manages the Promise-based messaging with the worker
(worker.postMessage → await a Promise that resolves in worker.onmessage)
        │
        ▼
Web Worker actually executes the CPU-bound computation on another thread
        │
        ▼
Result flows back → setState → React re-renders with the result
```

None of the three is a substitute for another: `async`/`await` without a
worker still blocks on CPU-bound work; a worker without `async`/`await`
forces you to hand-roll callback-based message handling instead of a
clean `await`; and a worker without `useEffect` (in React) has no
well-defined place to be created, wired up, and torn down alongside the
component that owns it.

---
