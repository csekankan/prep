# 21. React 18 — Concurrent Features and New APIs

## Table of Contents

1. [Concurrent Rendering](#concurrent-rendering)
2. [Automatic Batching](#automatic-batching)
3. [startTransition and useTransition](#starttransition-and-usetransition)
4. [useDeferredValue](#usedeferredvalue)
5. [Suspense Improvements](#suspense-improvements)
6. [Streaming SSR with Suspense](#streaming-ssr-with-suspense)
7. [New Rendering APIs](#new-rendering-apis)
8. [Strict Mode Changes](#strict-mode-changes)
9. [useSyncExternalStore](#usesyncexternalstore)
10. [useId](#useid)
11. [React Server Components](#react-server-components)
12. [Output-Based Interview Questions](#output-based-interview-questions)

---

## Concurrent Rendering

### What It Means

Before React 18, rendering was **synchronous** -- once React started rendering a component tree, it could not be interrupted until the entire tree was rendered. This meant a large update could block the main thread for hundreds of milliseconds, making the UI unresponsive.

Concurrent rendering makes rendering **interruptible**. React can:
- Start rendering an update.
- Pause in the middle to handle a more urgent update (e.g., user input).
- Resume or discard the interrupted render.

**Critical distinction:** Concurrent rendering is not multi-threaded. React still runs on the main thread. It splits work into small chunks and yields control back to the browser between chunks, allowing the browser to process events and paint.

```
Synchronous (React 17):
[==========RENDER==========][PAINT]
User input during render is blocked

Concurrent (React 18):
[==RENDER==][YIELD][==RENDER==][YIELD][==RENDER==][PAINT]
User input can be processed during yields
```

### Opting In

Concurrent features are opt-in. Simply using `createRoot` enables the concurrent renderer, but your app will not behave differently unless you use concurrent APIs like `useTransition` or `useDeferredValue`.

```jsx
// React 17 (legacy)
import { render } from 'react-dom';
render(<App />, document.getElementById('root'));

// React 18 (concurrent-capable)
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

---

## Automatic Batching

### The Problem Before React 18

In React 17, state updates were batched **only** inside React event handlers. Updates inside promises, `setTimeout`, native event handlers, or any other async context were NOT batched.

### React 17 Behavior (No Batching Outside Event Handlers)

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);

  console.log('Render');

  function handleClick() {
    // Inside React event handler: batched (1 re-render)
    setCount(c => c + 1);
    setFlag(f => !f);
    // "Render" logged once
  }

  function handleAsync() {
    setTimeout(() => {
      // React 17: NOT batched (2 re-renders!)
      setCount(c => c + 1);   // re-render 1
      setFlag(f => !f);        // re-render 2
      // "Render" logged twice
    }, 0);
  }

  function handleFetch() {
    fetch('/api/data').then(() => {
      // React 17: NOT batched (2 re-renders!)
      setCount(c => c + 1);
      setFlag(f => !f);
    });
  }

  return (
    <div>
      <button onClick={handleClick}>Sync</button>
      <button onClick={handleAsync}>Async</button>
    </div>
  );
}
```

### React 18 Behavior (Automatic Batching Everywhere)

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);

  console.log('Render');

  function handleAsync() {
    setTimeout(() => {
      // React 18: BATCHED (1 re-render)
      setCount(c => c + 1);
      setFlag(f => !f);
      // "Render" logged once
    }, 0);
  }

  function handleFetch() {
    fetch('/api/data').then(() => {
      // React 18: BATCHED (1 re-render)
      setCount(c => c + 1);
      setFlag(f => !f);
      // "Render" logged once
    });
  }

  return <button onClick={handleAsync}>Click</button>;
}
```

### Opting Out of Batching

If you need synchronous re-renders (rare), use `flushSync`:

```jsx
import { flushSync } from 'react-dom';

function handleClick() {
  flushSync(() => {
    setCount(c => c + 1);
  });
  // DOM is updated here

  flushSync(() => {
    setFlag(f => !f);
  });
  // DOM is updated here
}
```

---

## startTransition and useTransition

### Urgent vs Non-Urgent Updates

Not all state updates are equal. Typing in a search box (urgent) and filtering a list of 10,000 results (non-urgent) should be treated differently.

`startTransition` marks a state update as **non-urgent**. React can interrupt it if a more urgent update arrives.

### Basic startTransition

```jsx
import { startTransition, useState } from 'react';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  function handleChange(e) {
    const value = e.target.value;

    // Urgent: update input immediately
    setQuery(value);

    // Non-urgent: can be interrupted
    startTransition(() => {
      setResults(filterLargeDataset(value));
    });
  }

  return (
    <div>
      <input value={query} onChange={handleChange} />
      <ResultsList results={results} />
    </div>
  );
}
```

### useTransition (with pending state)

`useTransition` returns a `isPending` boolean so you can show loading indicators during transitions.

```jsx
import { useState, useTransition } from 'react';

function TabContainer() {
  const [tab, setTab] = useState('home');
  const [isPending, startTransition] = useTransition();

  function selectTab(nextTab) {
    startTransition(() => {
      setTab(nextTab);
    });
  }

  return (
    <div>
      <nav>
        <button onClick={() => selectTab('home')}>Home</button>
        <button onClick={() => selectTab('posts')}>Posts</button>
        <button onClick={() => selectTab('settings')}>Settings</button>
      </nav>
      {isPending && <div className="spinner" />}
      <TabContent tab={tab} />
    </div>
  );
}

function TabContent({ tab }) {
  switch (tab) {
    case 'home': return <Home />;
    case 'posts': return <Posts />; // expensive render
    case 'settings': return <Settings />;
  }
}
```

**Key behavior:** While `Posts` is rendering (expensive), if the user clicks "Settings", React will **abandon** the Posts render and start rendering Settings instead.

### Rules and Pitfalls

- `startTransition` callback must be **synchronous**. You cannot use `await` inside it.
- Only state updates inside `startTransition` are marked as transitions. Other updates in the same handler remain urgent.
- Transitions are lower priority, not deferred indefinitely. If no urgent updates interrupt, the transition completes normally.

---

## useDeferredValue

### Deferring Expensive Re-Renders

`useDeferredValue` accepts a value and returns a deferred copy that "lags behind" the original. When the original value changes, React first re-renders with the old deferred value (cheap), then schedules a background re-render with the new value.

```jsx
import { useState, useDeferredValue, memo } from 'react';

function SearchResults() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  return (
    <div>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search..."
      />
      {/* Shows stale results briefly while new ones render in background */}
      <div style={{ opacity: query !== deferredQuery ? 0.7 : 1 }}>
        <HeavyList query={deferredQuery} />
      </div>
    </div>
  );
}

const HeavyList = memo(function HeavyList({ query }) {
  const items = filterLargeDataset(query); // expensive
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  );
});
```

### useDeferredValue vs useTransition

| Feature | useTransition | useDeferredValue |
|---------|--------------|------------------|
| Wraps | A state update | A value |
| Control | You control which `setState` is deferred | React defers the value for you |
| Pending state | `isPending` available | No built-in pending state |
| Use case | When you own the state update | When you receive a value as a prop |

---

## Suspense Improvements

### Beyond Lazy Loading

In React 17, `<Suspense>` only worked with `React.lazy()` for code splitting. React 18 expands Suspense to work with:
- Data fetching (via compatible libraries like Relay, TanStack Query v5+, Next.js)
- Server-side rendering (streaming SSR)
- Selective hydration

```jsx
import { Suspense } from 'react';

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<Skeleton type="stats" />}>
        <Stats />
      </Suspense>
      <Suspense fallback={<Skeleton type="chart" />}>
        <RevenueChart />
      </Suspense>
      <Suspense fallback={<Skeleton type="table" />}>
        <RecentOrders />
      </Suspense>
    </div>
  );
}
```

Each section loads independently. If `RevenueChart` takes 3 seconds but `Stats` takes 200ms, the stats appear immediately.

### Nested Suspense

```jsx
<Suspense fallback={<PageSkeleton />}>
  <Layout>
    <Suspense fallback={<SidebarSkeleton />}>
      <Sidebar />
    </Suspense>
    <Suspense fallback={<ContentSkeleton />}>
      <MainContent />
    </Suspense>
  </Layout>
</Suspense>
```

If `Layout` suspends, the outer fallback shows. If only `Sidebar` suspends, the sidebar skeleton shows while `MainContent` renders normally.

---

## Streaming SSR with Suspense

React 18 combines Suspense with streaming SSR. Components wrapped in `<Suspense>` can be streamed to the client as they resolve.

```jsx
// Server component tree
function App() {
  return (
    <html>
      <body>
        <Header />
        <Suspense fallback={<Spinner />}>
          <SlowDataComponent /> {/* data fetching */}
        </Suspense>
        <Footer />
      </body>
    </html>
  );
}
```

**What the server streams:**

1. First chunk: `<html><body><Header/><Spinner/><Footer/></body></html>`
2. When `SlowDataComponent` resolves: an inline `<script>` that replaces `<Spinner/>` with the real content.

The browser progressively replaces fallbacks with real content without a full page reload.

---

## New Rendering APIs

### createRoot (replacing ReactDOM.render)

```jsx
// Before (React 17)
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));

// Unmount
ReactDOM.unmountComponentAtNode(document.getElementById('root'));

// After (React 18)
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(<App />);

// Unmount
root.unmount();
```

### hydrateRoot (replacing ReactDOM.hydrate)

```jsx
// Before (React 17)
import ReactDOM from 'react-dom';
ReactDOM.hydrate(<App />, document.getElementById('root'));

// After (React 18)
import { hydrateRoot } from 'react-dom/client';
const root = hydrateRoot(document.getElementById('root'), <App />);

// Subsequent updates
root.render(<UpdatedApp />);
```

**Key difference:** `hydrateRoot` accepts the JSX as the second argument (not a callback). React 18 also added the `onRecoverableError` option for handling hydration mismatches gracefully.

---

## Strict Mode Changes

### Double Effect Invocation

In React 18 Strict Mode (development only), React **mounts, unmounts, and re-mounts** every component. Effects fire twice:

```
Mount --> effect runs
Unmount --> cleanup runs
Re-mount --> effect runs again
```

This catches bugs where effects do not properly clean up.

```jsx
function ChatRoom({ roomId }) {
  useEffect(() => {
    const connection = createConnection(roomId);
    connection.connect();
    console.log('Connected to', roomId);

    return () => {
      connection.disconnect();
      console.log('Disconnected from', roomId);
    };
  }, [roomId]);

  return <div>Chat Room: {roomId}</div>;
}

// In Strict Mode (dev), console output:
// "Connected to general"
// "Disconnected from general"
// "Connected to general"
```

**Why this matters:** If your effect does not clean up properly (e.g., you forget to disconnect), the double invocation exposes the leak.

**Common pitfall:**

```jsx
// BUG: Double subscription without cleanup
useEffect(() => {
  window.addEventListener('resize', handleResize);
  // Missing cleanup! In Strict Mode, you get 2 listeners.
}, []);

// FIX: Always clean up
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

---

## useSyncExternalStore

### Subscribing to External Stores Safely

`useSyncExternalStore` is a hook for reading and subscribing to external mutable stores (Redux, Zustand internals, browser APIs) in a way that is compatible with concurrent rendering.

```jsx
import { useSyncExternalStore } from 'react';

// External store: browser online/offline status
function useOnlineStatus() {
  return useSyncExternalStore(
    subscribe,       // how to subscribe
    getSnapshot,     // how to get current value (client)
    getServerSnapshot // how to get value on server (SSR)
  );
}

function subscribe(callback) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function getSnapshot() {
  return navigator.onLine;
}

function getServerSnapshot() {
  return true; // assume online during SSR
}

// Usage
function StatusBar() {
  const isOnline = useOnlineStatus();
  return <div>{isOnline ? 'Online' : 'Offline'}</div>;
}
```

**Why not just use `useState` + `useEffect`?** In concurrent mode, `useState` + `useEffect` can read different values during a single render (tearing). `useSyncExternalStore` guarantees consistency by forcing a synchronous re-render when the store changes.

---

## useId

### Generating Unique IDs for Accessibility

`useId` generates unique IDs that are stable across server and client (no hydration mismatch).

```jsx
import { useId } from 'react';

function EmailField() {
  const id = useId();
  return (
    <div>
      <label htmlFor={id}>Email</label>
      <input id={id} type="email" />
    </div>
  );
}

function Form() {
  return (
    <form>
      <EmailField /> {/* id=":r0:" */}
      <EmailField /> {/* id=":r1:" */}
    </form>
  );
}
```

**Why not use a counter or `Math.random()`?**
- A counter gives different values on server vs client (hydration mismatch).
- `Math.random()` also mismatches.
- `useId` uses the component's position in the tree to generate deterministic IDs.

**Pitfall:** Do NOT use `useId` for list keys. It generates one ID per component instance, not per list item.

---

## React Server Components

### Concept (RSC)

React Server Components are components that run **only on the server**. They never ship to the client bundle, can directly access databases and file systems, and send rendered output (not JS code) to the client.

```jsx
// app/page.jsx (Server Component -- no "use client")
import db from './db';

async function ProductPage({ params }) {
  // Direct database access -- no API layer needed
  const product = await db.product.findUnique({
    where: { id: params.id },
  });

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <AddToCartButton productId={product.id} />
    </div>
  );
}
```

```jsx
// app/AddToCartButton.jsx (Client Component)
'use client';

import { useState } from 'react';

export function AddToCartButton({ productId }) {
  const [added, setAdded] = useState(false);

  return (
    <button onClick={() => {
      addToCart(productId);
      setAdded(true);
    }}>
      {added ? 'Added!' : 'Add to Cart'}
    </button>
  );
}
```

### Server vs Client Component Rules

| Capability | Server Component | Client Component |
|-----------|-----------------|-----------------|
| `useState`, `useEffect` | No | Yes |
| Event handlers (`onClick`) | No | Yes |
| Browser APIs | No | Yes |
| Direct DB/filesystem access | Yes | No |
| Ships JS to client | No | Yes |
| Can import Client Components | Yes | No (cannot import Server Components) |
| `async`/`await` at top level | Yes | No |

---

## Output-Based Interview Questions

### Q1: What does this log? (Automatic Batching)

```jsx
import { useState } from 'react';

function App() {
  const [a, setA] = useState(0);
  const [b, setB] = useState(0);

  console.log('Render:', a, b);

  function handleClick() {
    setTimeout(() => {
      setA(1);
      setB(1);
      console.log('After setState:', a, b);
    }, 0);
  }

  return <button onClick={handleClick}>Click</button>;
}
```

**Answer:**

```
// Initial render:
Render: 0 0

// After clicking (React 18):
After setState: 0 0       // closure captures initial values
Render: 1 1               // ONE re-render (batched)

// If this were React 17:
After setState: 0 0
Render: 1 0               // first re-render (only a updated)
Render: 1 1               // second re-render (b updated)
```

In React 18, both updates inside `setTimeout` are batched into a single re-render. The `console.log` after `setState` shows stale values because `a` and `b` are closures over the render in which the handler was created.

---

### Q2: What renders and when? (useTransition)

```jsx
import { useState, useTransition } from 'react';

function App() {
  const [text, setText] = useState('');
  const [list, setList] = useState([]);
  const [isPending, startTransition] = useTransition();

  function handleChange(e) {
    setText(e.target.value);
    startTransition(() => {
      const items = Array.from({ length: 20000 }, (_, i) =>
        `${e.target.value}-${i}`
      );
      setList(items);
    });
  }

  console.log('Render. isPending:', isPending, 'list length:', list.length);

  return (
    <div>
      <input value={text} onChange={handleChange} />
      {isPending ? <p>Loading...</p> : <p>Items: {list.length}</p>}
    </div>
  );
}
```

**Answer:**

When the user types "a":

```
Render. isPending: true list length: 0     // urgent update (setText) renders immediately
                                            // isPending is true because transition is pending
Render. isPending: false list length: 20000 // transition completes in background
```

The input updates immediately. The expensive list update happens in a non-urgent transition. If the user types another character before the transition completes, React discards the in-progress transition and starts a new one.

---

### Q3: How many times does the effect run? (Strict Mode)

```jsx
import { useState, useEffect } from 'react';

function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log('Effect:', count);
    return () => console.log('Cleanup:', count);
  }, [count]);

  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}
```

**Answer (Strict Mode, development):**

```
// Initial mount:
Effect: 0
Cleanup: 0        // Strict Mode unmounts
Effect: 0         // Strict Mode re-mounts

// Click button (count becomes 1):
Cleanup: 0
Effect: 1
Cleanup: 1        // Strict Mode unmounts
Effect: 1         // Strict Mode re-mounts
```

**In production (no Strict Mode):**

```
// Initial mount:
Effect: 0

// Click button:
Cleanup: 0
Effect: 1
```

---

### Q4: What is the value of `id` on server and client?

```jsx
import { useId } from 'react';

function Field({ label }) {
  const id = useId();
  console.log('ID:', id);
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </div>
  );
}

function App() {
  return (
    <>
      <Field label="Name" />
      <Field label="Email" />
    </>
  );
}
```

**Answer:**

```
// Both server and client will produce the same IDs:
ID: :r0:
ID: :r1:
```

The IDs are deterministic based on the component's position in the React tree. The first `Field` always gets `:r0:` and the second always gets `:r1:`, regardless of whether rendering happens on server or client. This prevents hydration mismatches that would occur with counters or random IDs.

---

### Q5: Predict the behavior of this flushSync usage:

```jsx
import { useState } from 'react';
import { flushSync } from 'react-dom';

function App() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);

  console.log('Render:', count, flag);

  function handleClick() {
    flushSync(() => {
      setCount(c => c + 1);
    });
    console.log('After first flushSync');

    flushSync(() => {
      setFlag(f => !f);
    });
    console.log('After second flushSync');
  }

  return <button onClick={handleClick}>Click</button>;
}
```

**Answer:**

```
// Initial:
Render: 0 false

// After clicking:
Render: 1 false             // flushSync forces synchronous render
After first flushSync        // DOM is already updated with count=1
Render: 1 true              // second flushSync forces another render
After second flushSync       // DOM is updated with flag=true
```

`flushSync` opts out of batching. Each `flushSync` call forces React to synchronously flush the update and update the DOM before the next line executes. This results in 2 re-renders instead of the 1 that automatic batching would produce.

---

### Q6: What problem does this code have in concurrent mode?

```jsx
import { useState, useEffect } from 'react';

let externalCount = 0;
const listeners = new Set();

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function useExternalCount() {
  const [, forceRender] = useState(0);

  useEffect(() => {
    return subscribe(() => forceRender(c => c + 1));
  }, []);

  return externalCount;
}
```

**Answer:**

This code is susceptible to **tearing** in concurrent mode. Between the time React starts rendering a component tree and finishes, `externalCount` could change. Different components reading this store during the same render could see different values.

**Fix: Use `useSyncExternalStore`:**

```jsx
import { useSyncExternalStore } from 'react';

function useExternalCount() {
  return useSyncExternalStore(
    subscribe,
    () => externalCount,      // getSnapshot
    () => externalCount        // getServerSnapshot
  );
}
```

`useSyncExternalStore` prevents tearing by forcing a synchronous re-render if the store value changes during a concurrent render.
