# useEffect Deep Dive — Interview Bible

## Effect Lifecycle

A `useEffect` hook goes through three phases:

1. **Mount (Setup)**: The effect callback runs after the component mounts and the DOM is painted
2. **Update (Cleanup + Re-run)**: When dependencies change, the previous cleanup runs, then the new effect runs
3. **Unmount (Final Cleanup)**: When the component unmounts, the cleanup function runs one final time

```javascript
useEffect(() => {
  // SETUP: runs after render is committed to DOM
  const subscription = dataSource.subscribe(handleChange);

  return () => {
    // CLEANUP: runs before next effect or on unmount
    subscription.unsubscribe();
  };
}, [dataSource]); // dependency array
```

Timeline of execution:
```
Mount:     render -> DOM paint -> effect runs
Update:    render -> DOM paint -> previous cleanup -> new effect runs
Unmount:   previous cleanup runs
```

---

## Dependency Array Deep Dive

### Empty Array `[]`

```javascript
useEffect(() => {
  console.log("Runs only once on mount");
  return () => console.log("Runs only on unmount");
}, []);
```

Equivalent to `componentDidMount` + `componentWillUnmount`. The effect captures the initial values of any referenced state/props via closure.

### No Array (omitted)

```javascript
useEffect(() => {
  console.log("Runs after EVERY render");
});
```

This runs after every single render, including the initial mount. Rarely what you want — usually indicates a missing dependency array.

### Specific Dependencies

```javascript
useEffect(() => {
  fetchUser(userId);
}, [userId]);
```

Runs on mount and whenever `userId` changes. React compares each dependency using `Object.is` against the previous render's value.

### Dependency Comparison Details

```javascript
useEffect(() => {
  // ...
}, [obj]); // new object every render = runs every render!
```

Objects, arrays, and functions create new references each render. If passed as dependencies, the effect re-runs every time. Solutions:
- Move the object creation inside the effect
- Depend on primitive properties: `[obj.id, obj.name]`
- Memoize with `useMemo`

---

## Stale Closures in Effects

### The Problem

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      console.log(count); // always logs 0!
    }, 1000);
    return () => clearInterval(id);
  }, []); // empty deps = closure captures initial count

  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

The effect's closure captures `count = 0` from the initial render and never updates because the dependency array is empty.

### Solutions

**1. Add the dependency:**
```javascript
useEffect(() => {
  const id = setInterval(() => {
    console.log(count);
  }, 1000);
  return () => clearInterval(id);
}, [count]); // restarts interval on every count change
```

**2. Use functional update (when you only need to update):**
```javascript
useEffect(() => {
  const id = setInterval(() => {
    setCount(prev => prev + 1); // doesn't read count, no stale closure
  }, 1000);
  return () => clearInterval(id);
}, []);
```

**3. Use a ref to hold current value:**
```javascript
const countRef = useRef(count);
countRef.current = count;

useEffect(() => {
  const id = setInterval(() => {
    console.log(countRef.current); // always fresh
  }, 1000);
  return () => clearInterval(id);
}, []);
```

---

## Cleanup Timing

Cleanup runs:
1. **Before the next effect execution** (when deps change)
2. **When the component unmounts**

Critical: cleanup runs AFTER the new render is painted to the DOM but BEFORE the new effect executes.

```javascript
useEffect(() => {
  console.log("effect", id);
  return () => console.log("cleanup", id);
}, [id]);
```

When `id` changes from 1 to 2:
```
render with id=2
DOM paint
cleanup 1       <-- runs with OLD id value (closure)
effect 2        <-- runs with NEW id value
```

---

## Race Conditions in Data Fetching

### The Problem

```javascript
function Profile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => setUser(data)); // race condition!
  }, [userId]);
}
```

If `userId` changes rapidly (1 -> 2 -> 3), three fetch requests fire. If request for userId=2 resolves after userId=3, stale data overwrites fresh data.

### Solution: Boolean Flag

```javascript
useEffect(() => {
  let cancelled = false;

  fetch(`/api/users/${userId}`)
    .then(res => res.json())
    .then(data => {
      if (!cancelled) setUser(data);
    });

  return () => { cancelled = true; };
}, [userId]);
```

### Solution: AbortController (Preferred)

```javascript
useEffect(() => {
  const controller = new AbortController();

  async function fetchData() {
    try {
      const res = await fetch(`/api/users/${userId}`, {
        signal: controller.signal,
      });
      const data = await res.json();
      setUser(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err);
      }
    }
  }

  fetchData();

  return () => controller.abort();
}, [userId]);
```

AbortController actually cancels the network request, saving bandwidth.

---

## useEffect vs useLayoutEffect

| Feature | useEffect | useLayoutEffect |
|---------|-----------|-----------------|
| Timing | After paint (async) | Before paint (sync) |
| Blocks paint | No | Yes |
| Use case | Data fetching, subscriptions | DOM measurements, scroll position |
| SSR | Works | Warns (no DOM on server) |

```javascript
// useLayoutEffect — synchronous, blocks visual update
useLayoutEffect(() => {
  // Measure DOM, set position — user never sees intermediate state
  const rect = ref.current.getBoundingClientRect();
  setPosition({ top: rect.top, left: rect.left });
}, []);

// useEffect — asynchronous, may cause flicker
useEffect(() => {
  // If you set position here, user might see element jump
  const rect = ref.current.getBoundingClientRect();
  setPosition({ top: rect.top, left: rect.left });
}, []);
```

Use `useLayoutEffect` when:
- You need to read layout (getBoundingClientRect) and synchronously re-render
- You need to prevent visual flicker of intermediate states
- You're implementing tooltips, popovers, or animations that depend on DOM position

---

## Strict Mode Double Invocation

In development with React.StrictMode, React intentionally:
1. Calls the component function twice
2. Runs effects, then immediately runs cleanup, then runs effects again

```javascript
// In development with StrictMode:
useEffect(() => {
  console.log("setup");        // logs twice
  return () => console.log("cleanup"); // first cleanup also runs
}, []);

// Console output in dev:
// setup
// cleanup
// setup
```

Purpose: Expose impure effects and missing cleanups. If your effect breaks on double-invocation, it has a bug that would manifest in production during updates.

How to write resilient effects:
```javascript
useEffect(() => {
  const connection = createConnection();
  connection.connect();
  return () => connection.disconnect();
}, []);
// Safe: second invocation creates new connection after first is cleaned up
```

---

## Async in useEffect

### Why You Cannot Return a Promise

```javascript
// WRONG: returns a Promise, not a cleanup function
useEffect(async () => {
  const data = await fetch('/api');
  setData(await data.json());
}, []);
```

The return value of the effect callback must be either `undefined` or a cleanup function. An async function implicitly returns a Promise, which React cannot use as a cleanup.

### Correct Pattern

```javascript
useEffect(() => {
  async function fetchData() {
    const response = await fetch('/api');
    const data = await response.json();
    setData(data);
  }
  fetchData();
}, []);
```

Or with IIFE:
```javascript
useEffect(() => {
  (async () => {
    const data = await fetch('/api').then(r => r.json());
    setData(data);
  })();
}, []);
```

---

## Output-Based Interview Questions

### Question 1: Effect with Empty Deps + State Reference

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      console.log("count:", count);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <button onClick={() => setCount(c => c + 1)}>
      {count}
    </button>
  );
}
```

**User clicks 5 times, then waits. What does the interval log?**

**Answer:** It always logs `count: 0`. The effect closure captured `count` at the time it ran (mount), and the empty dependency array means it never re-runs. The `count` inside the closure is permanently `0` regardless of how many times the button is clicked. This is the classic stale closure problem.

---

### Question 2: Missing Dependency

```javascript
function SearchResults({ query }) {
  const [results, setResults] = useState([]);

  useEffect(() => {
    fetch(`/api/search?q=${query}`)
      .then(r => r.json())
      .then(data => setResults(data));
  }, []); // query is NOT in deps

  return <div>{results.length} results for "{query}"</div>;
}
```

**What happens when `query` prop changes?**

**Answer:** The fetch only runs once on mount with the initial `query` value. When `query` changes, the component re-renders (showing the new query text) but the effect does NOT re-run. So you see "0 results for 'new query'" or stale results from the initial query. The `query` text updates but `results` stays stale. The ESLint exhaustive-deps rule would warn about this.

---

### Question 3: Cleanup Order When Deps Change

```javascript
function Logger({ value }) {
  useEffect(() => {
    console.log("effect:", value);
    return () => console.log("cleanup:", value);
  }, [value]);

  console.log("render:", value);
  return <div>{value}</div>;
}
```

**If value changes from "A" to "B", what is the full console output?**

**Answer:**
```
render: B
cleanup: A
effect: B
```

Explanation:
1. React renders the component with value="B" -> `render: B`
2. React commits to DOM and paints
3. Previous effect's cleanup runs with OLD closure value -> `cleanup: A`
4. New effect runs with NEW closure value -> `effect: B`

Note: The render phase happens first, then after paint, the old cleanup runs, then the new effect.

---

### Question 4: Multiple Effects Execution Order

```javascript
function App() {
  useEffect(() => {
    console.log("effect 1");
    return () => console.log("cleanup 1");
  });

  useEffect(() => {
    console.log("effect 2");
    return () => console.log("cleanup 2");
  });

  console.log("render");
  return <div>App</div>;
}
```

**What logs on mount and then on a re-render?**

**Answer:**

On mount:
```
render
effect 1
effect 2
```

On re-render:
```
render
cleanup 1
cleanup 2
effect 1
effect 2
```

Effects run in declaration order. On re-render, ALL previous cleanups run first (in order), THEN all new effects run (in order). Cleanups are batched together before effects.

---

### Question 5: setState Inside useEffect (Infinite Loop)

```javascript
function Infinite() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    setCount(count + 1);
  }); // no dependency array!

  return <div>{count}</div>;
}
```

**What happens?**

**Answer:** Infinite loop. Without a dependency array, the effect runs after every render. Each invocation calls `setCount`, which triggers a re-render, which triggers the effect again. React will eventually throw a "Maximum update depth exceeded" error. Fix: add `[]` to run only once, or add `[count]` with a conditional guard.

---

### Question 6: Effect Timing Relative to setState

```javascript
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log("effect:", count);
  }, [count]);

  const handleClick = () => {
    setCount(1);
    console.log("after setState:", count);
  };

  console.log("render:", count);
  return <button onClick={handleClick}>{count}</button>;
}
```

**What logs when the button is clicked (starting from count=0)?**

**Answer:**
```
after setState: 0
render: 1
effect: 1
```

Explanation:
1. `setCount(1)` does NOT immediately change `count` — the closure still has `0` -> logs `after setState: 0`
2. React re-renders the component -> logs `render: 1`
3. After DOM paint, the effect runs -> logs `effect: 1`

setState is asynchronous in terms of reading the new value. The current render's closure always has the value from when that render began.

---

## Pitfalls

### 1. Object/Array as Dependency

```javascript
const options = { method: 'GET' }; // new reference every render!

useEffect(() => {
  fetch(url, options);
}, [options]); // runs EVERY render
```

Fix: move inside effect, memoize, or depend on primitives.

### 2. Functions as Dependencies

```javascript
function App({ id }) {
  function fetchData() {
    return fetch(`/api/${id}`);
  }

  useEffect(() => {
    fetchData();
  }, [fetchData]); // new function every render!
}
```

Fix: move `fetchData` inside the effect or wrap with `useCallback`.

### 3. Forgetting Cleanup

```javascript
// Memory leak: listener never removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);
```

### 4. Reading State After Async Gap

```javascript
useEffect(() => {
  async function run() {
    await delay(2000);
    setData(count); // count might be stale!
  }
  run();
}, []);
```

---

## Tradeoffs

### useEffect vs Event Handlers
- **useEffect**: For side effects that synchronize with external systems (subscriptions, DOM manipulation, data fetching on prop change)
- **Event Handlers**: For side effects triggered by user actions (form submission, button clicks)

### AbortController vs Boolean Flag
- **AbortController**: Actually cancels the network request, better for performance, built-in browser API
- **Boolean flag**: Simpler, works for non-fetch async operations, more portable

### Empty Deps vs Specific Deps
- **Empty `[]`**: Runs once, risk of stale closures, good for one-time setup
- **Specific deps**: Runs on changes, no stale closure risk, may run too often if deps are unstable references

---

## Interview Tips

1. Always explain the cleanup -> setup ordering when deps change
2. Mention that effects run AFTER paint (unlike useLayoutEffect)
3. Know the difference between "the effect doesn't re-run" vs "the effect has a stale closure"
4. Be ready to explain why async functions can't be effect callbacks
5. AbortController pattern is a strong signal of production experience
6. Mention React.StrictMode double-invocation when discussing effect lifecycle in development
