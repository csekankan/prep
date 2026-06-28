# Top React Interview Questions

## Core React (10 Questions)

### Q1: What is the Virtual DOM and how does React use it?

**Answer:** The Virtual DOM is a lightweight JavaScript representation of the actual DOM. When state changes, React creates a new Virtual DOM tree, diffs it against the previous one (reconciliation), and computes the minimal set of actual DOM operations needed. This batching of DOM updates is more efficient than directly manipulating the DOM for every state change, because real DOM operations are expensive (they trigger layout, paint, and compositing).

**Follow-up:** How does React's reconciliation algorithm work?

React uses a heuristic O(n) algorithm with two key assumptions: (1) elements of different types produce different trees (a `<div>` changing to `<span>` causes a full subtree remount), and (2) the `key` prop hints at which children are stable across renders.

---

### Q2: What is JSX and why does React use it?

**Answer:** JSX is a syntax extension that looks like HTML but compiles to JavaScript function calls. `<div className="box">Hello</div>` compiles to `React.createElement('div', { className: 'box' }, 'Hello')` (or the new JSX transform: `_jsx('div', { className: 'box', children: 'Hello' })`). React uses JSX because it colocates markup with logic, making components self-contained. Since JSX is just JavaScript, you get full programmatic control (map, conditionals, variables) within your templates.

**Follow-up:** Can you use React without JSX?

Yes. You can call `React.createElement` directly. This is sometimes done in testing utilities or when embedding React in environments where a build step is not available.

---

### Q3: What is the difference between controlled and uncontrolled components?

**Answer:** A controlled component has its form value driven by React state. Every change goes through a handler that updates state, and the input reads from state. An uncontrolled component stores its value internally in the DOM; you read it via a ref when needed.

```tsx
// Controlled
function ControlledInput() {
  const [value, setValue] = useState("");
  return <input value={value} onChange={(e) => setValue(e.target.value)} />;
}

// Uncontrolled
function UncontrolledInput() {
  const inputRef = useRef<HTMLInputElement>(null);
  const handleSubmit = () => console.log(inputRef.current?.value);
  return <input ref={inputRef} defaultValue="" />;
}
```

**Follow-up:** When would you choose uncontrolled?

When integrating with non-React code (e.g., a third-party DOM library), when building simple forms where you only need the value on submit, or for file inputs (which are always uncontrolled in React).

---

### Q4: What are keys in React and why are they important?

**Answer:** Keys help React identify which items in a list have changed, been added, or removed. Without keys (or with index-based keys), React may reuse DOM nodes incorrectly, causing bugs with component state, focus, and animations. Keys must be stable, unique among siblings, and not derived from array index when the list can be reordered or filtered.

```tsx
// Bad: using index as key when list can reorder
{items.map((item, index) => <ListItem key={index} item={item} />)}

// Good: using stable unique identifier
{items.map((item) => <ListItem key={item.id} item={item} />)}
```

**Follow-up:** What happens if two siblings have the same key?

React logs a warning and may exhibit undefined behavior -- it might skip updates or apply updates to the wrong element.

---

### Q5: Explain the component lifecycle in React (class and functional).

**Answer:**

**Class components:** `constructor` -> `render` -> `componentDidMount` (mount). On update: `shouldComponentUpdate` -> `render` -> `componentDidUpdate`. On unmount: `componentWillUnmount`.

**Functional components with hooks:**
- `useState` / `useReducer` for initialization (replaces constructor)
- Return JSX (replaces render)
- `useEffect(() => { ... }, [])` with empty deps (replaces componentDidMount)
- `useEffect(() => { ... }, [dep])` with deps (replaces componentDidUpdate for those deps)
- `useEffect(() => { return cleanup }, [])` cleanup function (replaces componentWillUnmount)

**Follow-up:** Is there a hook equivalent for `shouldComponentUpdate`?

`React.memo` for the component level, and `useMemo`/`useCallback` for avoiding expensive recomputations that could trigger child re-renders.

---

### Q6: What is the difference between `state` and `props`?

**Answer:** Props are passed to a component by its parent and are read-only within the component. State is managed within the component and can be updated. When state changes, the component re-renders. Props flow down (parent to child); state is local unless explicitly lifted or shared via context/stores.

**Follow-up:** Can a child modify its parent's state?

Not directly. The parent passes a callback function as a prop, and the child calls that callback to request the state change.

---

### Q7: What is React.Fragment and when do you use it?

**Answer:** `React.Fragment` lets you group children without adding an extra DOM node. This is necessary when a component needs to return multiple elements but you do not want a wrapper `<div>` in the output.

```tsx
// Without Fragment: adds unnecessary div
function Columns() {
  return (
    <div>
      <td>Column 1</td>
      <td>Column 2</td>
    </div>
  );
}

// With Fragment: no extra DOM node
function Columns() {
  return (
    <>
      <td>Column 1</td>
      <td>Column 2</td>
    </>
  );
}
```

**Follow-up:** When do you need the explicit `<React.Fragment>` form instead of `<>`?

When you need to pass a `key` prop, which the shorthand syntax does not support: `<React.Fragment key={item.id}>...</React.Fragment>`.

---

### Q8: What are portals in React?

**Answer:** Portals render a component's children into a DOM node that exists outside the parent component's DOM hierarchy. The component still behaves normally in the React tree (events bubble, context is available), but the rendered output appears elsewhere in the DOM.

```tsx
function Modal({ children }) {
  return createPortal(
    <div className="modal-overlay">{children}</div>,
    document.getElementById("modal-root")
  );
}
```

**Use cases:** Modals, tooltips, dropdown menus, toast notifications -- anything that needs to break out of `overflow: hidden` or `z-index` stacking context constraints.

**Follow-up:** Do events from a portal bubble through the React tree or the DOM tree?

The React tree. A click inside a portal child bubbles to the React parent, not the DOM parent.

---

### Q9: What is the difference between `createElement` and `cloneElement`?

**Answer:** `createElement` creates a new React element from scratch (type, props, children). `cloneElement` takes an existing element and returns a copy with merged props. `cloneElement` is used in advanced patterns where a parent needs to inject additional props into children it does not control.

```tsx
// Injecting an onClick handler to all children
function ButtonGroup({ children }) {
  return (
    <div>
      {React.Children.map(children, (child) =>
        React.cloneElement(child, {
          className: `${child.props.className} group-button`,
        })
      )}
    </div>
  );
}
```

**Follow-up:** Why is `cloneElement` considered a legacy pattern?

It couples the parent to the child's prop interface and breaks when children are wrapped in fragments or other elements. Context or render props are more robust alternatives.

---

### Q10: What is StrictMode and what does it do?

**Answer:** `<React.StrictMode>` is a development-only wrapper that activates extra checks: it double-invokes render functions, effects, and reducers to detect impure rendering; it warns about deprecated lifecycle methods; and it flags legacy string ref usage. It does not affect the production build.

**Follow-up:** Why does React call effects twice in StrictMode?

To help you find bugs caused by missing cleanup functions. If your effect works correctly when run twice, it will work correctly when React unmounts and remounts components (which happens in features like Offscreen/Activity).

---

## Hooks (10 Questions)

### Q11: What are the rules of hooks?

**Answer:** Two rules: (1) Only call hooks at the top level of a component or custom hook -- never inside conditions, loops, or nested functions. (2) Only call hooks from React function components or custom hooks, not from regular JavaScript functions. These rules exist because React relies on the order of hook calls being the same on every render to correctly associate state with the right hook.

**Follow-up:** What happens if you break these rules?

React's internal linked list of hooks becomes misaligned. Hook N might read state from hook N+1's slot, causing corrupted state and crashes.

---

### Q12: Explain the difference between `useMemo` and `useCallback`.

**Answer:** Both memoize values between renders. `useMemo` memoizes the result of a computation: `useMemo(() => expensiveCalc(a, b), [a, b])`. `useCallback` memoizes a function reference: `useCallback((x) => doSomething(x, dep), [dep])`. In fact, `useCallback(fn, deps)` is equivalent to `useMemo(() => fn, deps)`.

```tsx
// useMemo: avoid re-sorting on every render
const sortedItems = useMemo(() => items.sort(compareFn), [items]);

// useCallback: stable reference for child props
const handleClick = useCallback((id: string) => {
  setSelected(id);
}, []);

// Child only re-renders when handleClick reference changes
<List items={items} onSelect={handleClick} />
```

**Follow-up:** Should you wrap every function in `useCallback`?

No. Memoization has a cost (storing the previous value, comparing deps). Only use it when the function is passed to a memoized child (`React.memo`), used as a dependency in another hook, or when profiling shows unnecessary re-renders.

---

### Q13: How does `useEffect` differ from `useLayoutEffect`?

**Answer:** `useEffect` runs asynchronously after the browser has painted. `useLayoutEffect` runs synchronously after DOM mutations but before the browser paints. Use `useLayoutEffect` when you need to read layout information (element dimensions) and synchronously update the DOM to avoid visual flicker.

```tsx
// useEffect: runs after paint (non-blocking)
useEffect(() => {
  analytics.trackPageView();
}, []);

// useLayoutEffect: runs before paint (blocking)
useLayoutEffect(() => {
  const { height } = ref.current.getBoundingClientRect();
  setTooltipPosition(calculatePosition(height));
}, [content]);
```

**Follow-up:** What is the SSR implication?

`useLayoutEffect` fires a warning during SSR because there is no DOM to measure. Use `useEffect` for SSR-safe code, or conditionally use `useLayoutEffect` only on the client.

---

### Q14: What is `useRef` and what are its use cases?

**Answer:** `useRef` returns a mutable ref object whose `.current` property persists across renders without causing re-renders when changed. Use cases: (1) accessing DOM elements, (2) storing mutable values that do not need to trigger re-renders (timers, previous values, WebSocket instances), (3) storing the latest value of a prop or state for use inside stale closures.

```tsx
// DOM access
const inputRef = useRef<HTMLInputElement>(null);
const focusInput = () => inputRef.current?.focus();

// Mutable value that persists without re-renders
const renderCount = useRef(0);
useEffect(() => { renderCount.current += 1; });

// Capturing latest value for async callbacks
const latestCallback = useRef(callback);
useEffect(() => { latestCallback.current = callback; });
```

**Follow-up:** Can you use `useRef` to store a previous value?

Yes, but you must update it manually in a `useEffect`: `useEffect(() => { prevRef.current = value; }, [value])`.

---

### Q15: Explain `useReducer` and when you would use it over `useState`.

**Answer:** `useReducer` accepts a reducer function and initial state, returning the current state and a dispatch function. It is preferred when: (1) state has multiple sub-values that change together, (2) the next state depends on the previous state in complex ways, (3) you want to decouple state transitions from the component that triggers them.

```tsx
type State = { count: number; step: number };
type Action =
  | { type: "increment" }
  | { type: "decrement" }
  | { type: "setStep"; payload: number }
  | { type: "reset" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "increment":
      return { ...state, count: state.count + state.step };
    case "decrement":
      return { ...state, count: state.count - state.step };
    case "setStep":
      return { ...state, step: action.payload };
    case "reset":
      return { count: 0, step: 1 };
    default:
      return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, { count: 0, step: 1 });
  return (
    <>
      <span>{state.count}</span>
      <button onClick={() => dispatch({ type: "increment" })}>+</button>
    </>
  );
}
```

**Follow-up:** Can you use `useReducer` with context for global state management?

Yes. Combine `useReducer` with `React.createContext` to create a lightweight Redux-like store. However, be aware that every dispatch causes all consumers of the context to re-render unless you split state and dispatch into separate contexts or memoize the value.

---

### Q16: What is `useContext` and what is the re-render problem?

**Answer:** `useContext` subscribes a component to a React context. When the context value changes, all components consuming that context re-render, even if they only use a subset of the value.

```tsx
const ThemeContext = createContext({ theme: "light", language: "en" });

// This component re-renders when language changes, even though it only uses theme
function ThemedButton() {
  const { theme } = useContext(ThemeContext);
  return <button className={theme}>Click</button>;
}
```

**Solutions:**
1. Split contexts: separate `ThemeContext` and `LanguageContext`
2. Memoize the context value: `useMemo(() => ({ theme }), [theme])`
3. Use a selector-based library (Zustand, Jotai) for granular subscriptions
4. Use `React.memo` on consumers (prevents re-render if props have not changed, but context changes still trigger it)

---

### Q17: How do you create a custom hook? What are the conventions?

**Answer:** A custom hook is a JavaScript function whose name starts with `use` and that calls other hooks. The `use` prefix is mandatory -- it enables the linter to enforce the rules of hooks.

```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    setStoredValue((prev) => {
      const nextValue = value instanceof Function ? value(prev) : value;
      window.localStorage.setItem(key, JSON.stringify(nextValue));
      return nextValue;
    });
  }, [key]);

  return [storedValue, setValue] as const;
}
```

**Follow-up:** Do two components using the same custom hook share state?

No. Each call to a custom hook creates independent state. The hook shares logic, not state.

---

### Q18: What is `useImperativeHandle` and when is it used?

**Answer:** `useImperativeHandle` customizes the instance value exposed when a parent uses a `ref` on a child component. Used with `forwardRef` to expose a limited API rather than the full DOM element.

```tsx
const FancyInput = forwardRef((props, ref) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    clear: () => {
      if (inputRef.current) inputRef.current.value = "";
    },
  }));

  return <input ref={inputRef} {...props} />;
});

// Parent
function Form() {
  const inputRef = useRef<{ focus: () => void; clear: () => void }>(null);
  return (
    <>
      <FancyInput ref={inputRef} />
      <button onClick={() => inputRef.current?.focus()}>Focus</button>
      <button onClick={() => inputRef.current?.clear()}>Clear</button>
    </>
  );
}
```

**Follow-up:** Why not just expose the raw DOM ref?

Exposing the full DOM element breaks encapsulation. The parent could call any DOM method, making the child's implementation details a public API. `useImperativeHandle` creates a controlled contract.

---

### Q19: What is the `use` hook introduced in React 19?

**Answer:** The `use` hook can read the value of a resource like a Promise or a context. Unlike other hooks, `use` can be called inside conditionals and loops.

```tsx
function Comments({ commentsPromise }) {
  const comments = use(commentsPromise);
  return (
    <ul>
      {comments.map((c) => (
        <li key={c.id}>{c.body}</li>
      ))}
    </ul>
  );
}

// Wrapped in Suspense
<Suspense fallback={<Spinner />}>
  <Comments commentsPromise={fetchComments(postId)} />
</Suspense>
```

When `use` reads a pending Promise, the component suspends (integrates with Suspense boundaries). When it reads a context, it behaves like `useContext` but can be called conditionally.

**Follow-up:** How does `use` differ from `await` in a Server Component?

Server Components can use `await` directly because they run on the server and do not re-render. Client Components cannot be async, so `use` provides a way to read promises while integrating with React's Suspense mechanism.

---

### Q20: How do you handle stale closures in hooks?

**Answer:** Stale closures occur when a callback created during a previous render captures old variable values.

```tsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // BUG: count is always 0 (stale closure)
      setCount(count + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []); // empty deps = closure captures initial count

  // FIX: use functional updater
  useEffect(() => {
    const id = setInterval(() => {
      setCount((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <span>{count}</span>;
}
```

Other solutions: add the value to the dependency array (causes the effect to re-run), or store the latest value in a ref.

---

## Performance & Optimization (8 Questions)

### Q21: What causes unnecessary re-renders in React and how do you prevent them?

**Answer:** A component re-renders when: (1) its state changes, (2) its parent re-renders (even if props have not changed), (3) a context it consumes changes.

**Prevention strategies:**
- `React.memo`: Wraps a component to skip re-render if props are shallowly equal
- `useMemo`: Avoid recomputing expensive derived data
- `useCallback`: Stabilize function references passed as props
- State colocation: Move state closer to where it is used so fewer components are in the re-render tree
- Context splitting: Separate frequently-changing context from stable context

```tsx
const ExpensiveChild = React.memo(({ data, onAction }) => {
  // Only re-renders when data or onAction reference changes
  return <div>{/* ... */}</div>;
});

function Parent() {
  const [count, setCount] = useState(0);
  const data = useMemo(() => processData(rawData), [rawData]);
  const onAction = useCallback(() => { /* ... */ }, []);

  return (
    <>
      <button onClick={() => setCount(c => c + 1)}>{count}</button>
      <ExpensiveChild data={data} onAction={onAction} />
    </>
  );
}
```

---

### Q22: What is React.lazy and how does code splitting work?

**Answer:** `React.lazy` lets you define a component that is loaded dynamically via dynamic `import()`. The component's code is split into a separate bundle chunk and only downloaded when the component is rendered.

```tsx
const AdminPanel = React.lazy(() => import("./AdminPanel"));

function App() {
  return (
    <Routes>
      <Route path="/admin" element={
        <Suspense fallback={<Spinner />}>
          <AdminPanel />
        </Suspense>
      } />
    </Routes>
  );
}
```

**Follow-up:** How do you preload a lazy component?

Call the import function ahead of time: `const adminPromise = import("./AdminPanel")`. Or use `<link rel="prefetch">` in the HTML head. Some routers (React Router, Next.js) support automatic prefetching on link hover.

---

### Q23: How does virtualization improve performance for long lists?

**Answer:** Virtualization renders only the items currently visible in the viewport (plus a small buffer), instead of all items. For a list of 10,000 items where only 20 are visible, virtualization reduces the DOM node count from 10,000 to ~25, dramatically improving rendering time, memory usage, and scroll performance.

```tsx
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }) {
  const parentRef = useRef(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
    overscan: 5,
  });

  return (
    <div ref={parentRef} style={{ height: 400, overflow: "auto" }}>
      <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: "absolute",
              top: virtualRow.start,
              height: virtualRow.size,
              width: "100%",
            }}
          >
            {items[virtualRow.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Follow-up:** What are the downsides of virtualization?

Accessibility (screen readers may not see off-screen items), CMD+F (browser search does not find non-rendered text), SEO (not relevant for SPAs but matters for SSR), and complexity of handling variable-height items.

---

### Q24: What is reconciliation and how does the diffing algorithm work?

**Answer:** Reconciliation is the process by which React updates the DOM to match the latest render output. The diffing algorithm compares two trees and produces the minimum number of operations to transform one into the other.

**Key heuristics:**
1. Different element types (`<div>` vs `<span>`) produce entirely different trees. React tears down the old subtree and builds a new one.
2. Same element type: React keeps the same DOM node and updates only the changed attributes.
3. Lists use `key` to match children between old and new renders. Without keys, React compares by position (index), which causes problems when items are reordered.

**Follow-up:** What is the time complexity?

O(n) where n is the number of elements. A generic tree diff is O(n^3), but React's heuristics make it linear.

---

### Q25: How do you profile and debug React performance issues?

**Answer:**

1. **React DevTools Profiler:** Record a session, identify which components render and how long each render takes. Look for components that re-render frequently with no visual change.
2. **React DevTools "Highlight Updates":** Visually shows which components re-render on the page.
3. **`console.count` or `useRenderCount` hook:** Quick way to see how many times a component renders.
4. **Chrome Performance tab:** Record a trace to see JavaScript execution, layout, paint. Look for long tasks (>50ms) that block the main thread.
5. **`React.Profiler` component:** Programmatically measure render times in production.

```tsx
<Profiler id="Feed" onRender={(id, phase, actualDuration) => {
  if (actualDuration > 16) {
    console.warn(`${id} took ${actualDuration.toFixed(1)}ms (${phase})`);
  }
}}>
  <Feed />
</Profiler>
```

---

### Q26: What is `startTransition` and how does it improve UX?

**Answer:** `startTransition` marks a state update as non-urgent (a "transition"). React keeps the current UI responsive while computing the next state in the background. If a more urgent update comes in (e.g., typing in an input), React pauses the transition to handle it first.

```tsx
function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);  // urgent: update input immediately

    startTransition(() => {
      setResults(filterLargeDataset(value));  // non-urgent: can be deferred
    });
  };

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending && <Spinner />}
      <ResultsList results={results} />
    </>
  );
}
```

**Follow-up:** How does `useTransition` differ from `useDeferredValue`?

`useTransition` wraps the state *setter* -- you control which update is deferred. `useDeferredValue` wraps the state *value* -- React gives you a "lagging" copy that updates with lower priority. Use `useDeferredValue` when you do not control the state update (e.g., it comes from a parent prop).

---

### Q27: What are the best practices for optimizing React Context performance?

**Answer:**

1. **Split contexts by update frequency.** Do not put fast-changing values (mouse position) and slow-changing values (theme) in the same context.
2. **Memoize the context value.** If the value is an object, wrap it in `useMemo` to prevent new object references on every render.
3. **Separate state and dispatch.** Create two contexts: one for the state, one for the dispatch function. Components that only dispatch (e.g., a button) do not need to re-render when state changes.

```tsx
const StateContext = createContext<State | null>(null);
const DispatchContext = createContext<Dispatch | null>(null);

function Provider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const memoState = useMemo(() => state, [state]);

  return (
    <DispatchContext.Provider value={dispatch}>
      <StateContext.Provider value={memoState}>
        {children}
      </StateContext.Provider>
    </DispatchContext.Provider>
  );
}
```

4. **Use selector pattern.** Libraries like `use-context-selector` allow subscribing to a slice of context rather than the whole value.

---

### Q28: How does React's batching work and what changed in React 18?

**Answer:** Batching groups multiple state updates into a single re-render. Before React 18, batching only worked inside React event handlers. Updates inside `setTimeout`, `fetch.then`, or native event listeners caused separate re-renders for each `setState`.

React 18 introduced **automatic batching**: all state updates are batched regardless of where they originate.

```tsx
// React 17: TWO re-renders
setTimeout(() => {
  setCount(1);    // render
  setFlag(true);  // render
}, 1000);

// React 18: ONE re-render (automatic batching)
setTimeout(() => {
  setCount(1);    // queued
  setFlag(true);  // queued, then single render
}, 1000);
```

**Follow-up:** How do you opt out of batching?

Use `flushSync` to force a synchronous render: `flushSync(() => setCount(1))`. This is rarely needed -- usually only for DOM measurements that must happen between state updates.

---

## State Management (6 Questions)

### Q29: When should you use local state vs global state?

**Answer:** Apply the principle of least privilege: state should live as close to where it is used as possible.

| Scenario | Recommendation |
|----------|---------------|
| Form input value | Local state (`useState`) |
| Open/closed state of a modal | Local state in the component that owns it |
| Currently authenticated user | Global state (context or store) |
| Server data (API responses) | Server state library (React Query, SWR) |
| URL-derived state | Router (`useSearchParams`, `useParams`) |
| Theme or locale | Context (changes infrequently, needed everywhere) |
| Complex cross-feature state | External store (Zustand, Redux Toolkit) |

**Follow-up:** What is "server state" and why is it different?

Server state is data that lives on the server and is cached on the client. It has unique concerns: staleness, background refetching, cache invalidation, optimistic updates, and pagination. These are orthogonal to client state management, which is why dedicated libraries (React Query) handle it better than general-purpose stores.

---

### Q30: Compare Redux Toolkit, Zustand, and Jotai.

**Answer:**

| Feature | Redux Toolkit | Zustand | Jotai |
|---------|--------------|---------|-------|
| Mental model | Single store, actions, reducers | Single store, set functions | Atoms (bottom-up) |
| Boilerplate | Low (with RTK) | Very low | Very low |
| DevTools | Excellent (time travel) | Good (via middleware) | Good (Jotai DevTools) |
| Bundle size | ~11KB | ~1KB | ~3KB |
| Middleware | Rich ecosystem | Simple API | Derived atoms |
| Learning curve | Medium | Low | Low |
| Re-render granularity | Selectors | Selectors | Atom-level |
| SSR support | Good | Good | Good |

**When to choose each:**
- **Redux Toolkit:** Large team, complex state transitions, need for time-travel debugging, existing Redux codebase
- **Zustand:** Small-to-medium app, want simplicity, no boilerplate tolerance
- **Jotai:** Fine-grained reactivity needed, state is naturally composed of independent atoms, want React-centric API

---

### Q31: How does React Query (TanStack Query) change state management architecture?

**Answer:** React Query separates server state from client state entirely. Before React Query, developers put everything in Redux: API responses, loading flags, error states, pagination cursors. This bloats the store and forces manual cache management.

With React Query:
- **Server state** (API data) is managed by React Query with automatic caching, deduplication, background refetch, and retry
- **Client state** (UI state, user preferences) stays in local state, context, or a lightweight store like Zustand

```tsx
// Before: Redux for everything
dispatch(fetchUsersRequest());
const response = await api.getUsers();
dispatch(fetchUsersSuccess(response.data));
// Manual: cache invalidation, loading states, error handling, stale data...

// After: React Query
const { data, isLoading, error } = useQuery({
  queryKey: ["users"],
  queryFn: api.getUsers,
  staleTime: 5 * 60 * 1000,
});
// Automatic: caching, dedup, background refetch, retry, loading/error states
```

---

### Q32: How do you manage form state in React? Compare approaches.

**Answer:**

**1. Controlled with `useState`:** Simple forms. Full control, but verbose for many fields.

**2. `useReducer`:** Complex forms with interdependent fields or validation logic.

**3. React Hook Form:** Uncontrolled by default (stores values in refs), minimal re-renders. Best for performance with large forms.

```tsx
import { useForm } from "react-hook-form";

function SignupForm() {
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = (data) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email", {
        required: "Email is required",
        pattern: { value: /^\S+@\S+$/i, message: "Invalid email" }
      })} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register("password", {
        required: "Password is required",
        minLength: { value: 8, message: "Min 8 characters" }
      })} />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit">Sign Up</button>
    </form>
  );
}
```

**4. Formik:** Controlled, more opinionated. Heavier than React Hook Form but integrates well with Yup validation schemas.

**Tradeoff:** React Hook Form is faster (fewer re-renders) but debugging is harder because values are not in React state. Formik is simpler to reason about but can cause performance issues with large forms.

---

### Q33: What is the Context + useReducer pattern and what are its limitations?

**Answer:** Combining Context and useReducer creates a lightweight Redux-like architecture without external dependencies.

```tsx
const TodoContext = createContext(null);
const TodoDispatchContext = createContext(null);

function TodoProvider({ children }) {
  const [todos, dispatch] = useReducer(todoReducer, []);
  return (
    <TodoDispatchContext.Provider value={dispatch}>
      <TodoContext.Provider value={todos}>
        {children}
      </TodoContext.Provider>
    </TodoDispatchContext.Provider>
  );
}
```

**Limitations:**
1. No selector support: all consumers re-render on any state change (unless you split contexts aggressively)
2. No middleware: no built-in way to add logging, async handling, or persistence
3. No devtools: no time-travel debugging
4. Scaling: as state grows, you either have one massive reducer or many contexts, both of which are awkward

**When it is enough:** Theme/locale, auth state, small apps with < 5 pieces of shared state.

---

### Q34: How do you handle derived/computed state in React?

**Answer:** Derived state is data computed from existing state. Never store it as separate state -- compute it on render or memoize it.

```tsx
// BAD: storing derived state separately
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]);  // derived! Don't do this.
const [totalPrice, setTotalPrice] = useState(0);          // derived! Don't do this.

useEffect(() => {
  setFilteredItems(items.filter((i) => i.active));
  setTotalPrice(items.reduce((sum, i) => sum + i.price, 0));
}, [items]);

// GOOD: compute during render, memoize if expensive
const [items, setItems] = useState([]);
const filteredItems = useMemo(() => items.filter((i) => i.active), [items]);
const totalPrice = useMemo(() => items.reduce((sum, i) => sum + i.price, 0), [items]);
```

**Follow-up:** Why is storing derived state in `useState` + `useEffect` problematic?

It causes an extra render cycle: first render with stale derived state, then the effect runs and triggers a second render with updated derived state. Computing during render avoids this.

---

## Advanced Patterns (6 Questions)

### Q35: What are render props and when would you still use them today?

**Answer:** A render prop is a function prop that a component calls to determine what to render. The component providing the render prop handles behavior/state; the consumer handles presentation.

```tsx
function Toggleable({ children }) {
  const [isOn, setIsOn] = useState(false);
  return children({ isOn, toggle: () => setIsOn((prev) => !prev) });
}

// Usage
<Toggleable>
  {({ isOn, toggle }) => (
    <button onClick={toggle}>{isOn ? "ON" : "OFF"}</button>
  )}
</Toggleable>
```

**When still useful today:** (1) Libraries that need framework-agnostic logic sharing (Formik's `<Field>` uses render props). (2) When you need the behavior to be tightly coupled with a specific DOM subtree that the hook pattern cannot express. (3) Headless UI component libraries (Downshift, Radix primitives).

---

### Q36: What is the Provider pattern and how do you avoid prop drilling?

**Answer:** The Provider pattern uses React Context to make data available to any descendant component without passing it through every intermediate component.

```tsx
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <Layout />
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );
}

// Deep child component accesses auth without prop drilling
function UserAvatar() {
  const { user } = useAuth();
  return <img src={user.avatarUrl} alt={user.name} />;
}
```

**Pitfall:** Over-using providers creates "provider hell" at the root of the app. Only use context for truly cross-cutting concerns (auth, theme, locale). For data needed by a subtree, lift state to the common ancestor and pass it as props.

---

### Q37: Explain the State Reducer Pattern.

**Answer:** The state reducer pattern gives the consumer of a component full control over state transitions by allowing them to provide a custom reducer that wraps or replaces the default one.

```tsx
function useToggle({ reducer = toggleReducer } = {}) {
  const [state, dispatch] = useReducer(reducer, { on: false });
  const toggle = () => dispatch({ type: "TOGGLE" });
  const reset = () => dispatch({ type: "RESET" });
  return { ...state, toggle, reset, dispatch };
}

function toggleReducer(state, action) {
  switch (action.type) {
    case "TOGGLE": return { on: !state.on };
    case "RESET": return { on: false };
    default: return state;
  }
}

// Consumer overrides: prevent toggling more than 4 times
function App() {
  const [clickCount, setClickCount] = useState(0);

  const { on, toggle } = useToggle({
    reducer: (state, action) => {
      if (action.type === "TOGGLE" && clickCount >= 4) {
        return state;  // block the transition
      }
      setClickCount((c) => c + 1);
      return toggleReducer(state, action);
    },
  });

  return <button onClick={toggle}>{on ? "ON" : "OFF"}</button>;
}
```

This pattern is used in libraries like Downshift to give consumers full control without forking the library.

---

### Q38: What are higher-order components (HOC) and what problems do they have?

**Answer:** See the HOC section in the design patterns above for the definition and example. Key problems:

1. **Wrapper Hell:** Multiple HOCs create deeply nested component trees (`withAuth(withTheme(withRouter(Component)))`) that are hard to debug.
2. **Name collisions:** If two HOCs inject a prop with the same name, one silently overwrites the other.
3. **Static typing:** TypeScript inference breaks down with multiple HOCs. Generics become complex and error-prone.
4. **Ref forwarding:** HOCs swallow refs unless explicitly forwarded with `React.forwardRef`.
5. **Indirection:** It is hard to tell which HOC is providing which prop when reading the component.

**Why hooks replaced HOCs:** Hooks provide the same logic-sharing capability without wrapper components, without prop collision, with clear data flow, and with excellent TypeScript support.

---

### Q39: How do Suspense and Error Boundaries work together?

**Answer:** Suspense handles loading states; Error Boundaries handle error states. Together, they provide a declarative way to manage async UI.

```tsx
function PostPage({ postId }) {
  return (
    <ErrorBoundary fallback={<p>Something went wrong loading this post.</p>}>
      <Suspense fallback={<PostSkeleton />}>
        <PostContent postId={postId} />
      </Suspense>
      <Suspense fallback={<CommentsSkeleton />}>
        <Comments postId={postId} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

If `PostContent` throws a promise (suspends), the nearest `Suspense` boundary shows `<PostSkeleton />`. If it throws an error, the nearest `ErrorBoundary` catches it. Placing separate `Suspense` boundaries around `PostContent` and `Comments` allows them to load independently.

**Follow-up:** Can you nest Suspense boundaries?

Yes. An outer Suspense shows a full-page skeleton, and inner Suspense boundaries show granular skeletons for subsections. When all inner boundaries resolve, the outer one is no longer needed.

---

### Q40: What is the Module Pattern for organizing React code?

**Answer:** The module pattern groups related components, hooks, types, and utilities into a self-contained directory with a clear public API.

```
features/
  cart/
    index.ts              // public API: exports only what other features need
    CartPage.tsx           // page-level component
    CartItem.tsx           // internal component
    useCart.ts             // custom hook
    cartApi.ts             // API calls
    cartTypes.ts           // TypeScript types
    cart.test.tsx           // tests
```

`index.ts` controls what is exposed:

```tsx
export { CartPage } from "./CartPage";
export { useCart } from "./useCart";
export type { CartItem } from "./cartTypes";
// CartItem component is internal, not exported
```

This pattern, combined with ESLint rules or Nx module boundary enforcement, prevents spaghetti imports across feature boundaries.

---

## React 18+ / Modern React (5 Questions)

### Q41: What is Concurrent Rendering and how does it differ from synchronous rendering?

**Answer:** In synchronous rendering (React 17 and earlier), once React starts rendering a tree, it cannot be interrupted until complete. If the tree is large, this blocks the main thread and makes the UI unresponsive.

Concurrent rendering (React 18+) allows React to pause, resume, or abandon renders. It can start rendering an update, pause to handle a more urgent update (like user input), and then resume the original render. This is not multithreading -- it is cooperative scheduling on the main thread using time-slicing.

**Key APIs enabled by concurrent rendering:**
- `startTransition` / `useTransition`: Mark updates as non-urgent
- `useDeferredValue`: Defer expensive value computations
- Suspense for data fetching: React can render other siblings while one component suspends

---

### Q42: What are Server Components and how do they differ from Client Components?

**Answer:** Server Components render on the server and send serialized UI (not HTML, but a React-specific format) to the client. They never re-render on the client and cannot use state, effects, or browser APIs.

| Feature | Server Component | Client Component |
|---------|-----------------|------------------|
| Runs on | Server only | Client (and server for SSR) |
| State/Effects | No | Yes |
| Browser APIs | No | Yes |
| Direct DB/FS access | Yes | No |
| Bundle size impact | Zero (not sent to client) | Included in JS bundle |
| Interactivity | None | Full |

```tsx
// Server Component (default in Next.js App Router)
async function PostPage({ params }) {
  const post = await db.posts.findUnique({ where: { id: params.id } });
  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
      <LikeButton postId={post.id} />  {/* Client Component boundary */}
    </article>
  );
}

// Client Component
"use client";
function LikeButton({ postId }) {
  const [liked, setLiked] = useState(false);
  return <button onClick={() => setLiked(!liked)}>{liked ? "Unlike" : "Like"}</button>;
}
```

**Follow-up:** Can a Client Component render a Server Component?

Not directly. But a Client Component can accept Server Components as children (passed via the `children` prop), because the parent renders the children slot without knowing its contents.

---

### Q43: What are React Server Actions?

**Answer:** Server Actions are async functions that run on the server, callable directly from Client Components. They replace the need for manual API routes for mutations.

```tsx
// actions.ts
"use server";

export async function createPost(formData: FormData) {
  const title = formData.get("title") as string;
  const content = formData.get("content") as string;

  await db.posts.create({ data: { title, content } });
  revalidatePath("/posts");
}

// Client Component
"use client";
function NewPostForm() {
  return (
    <form action={createPost}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit">Create Post</button>
    </form>
  );
}
```

**Follow-up:** How do Server Actions handle progressive enhancement?

When JavaScript is disabled, the form still submits as a standard HTML form POST. The Server Action processes the FormData on the server. When JavaScript is enabled, React intercepts the submission and handles it as a client-side transition with loading states.

---

### Q44: What is Suspense for data fetching and how does it work?

**Answer:** Suspense for data fetching allows components to "suspend" while waiting for async data. Instead of each component managing its own loading state, the nearest Suspense boundary shows a fallback.

```tsx
// The data fetching library integrates with Suspense
function ProfilePage({ userId }) {
  return (
    <Suspense fallback={<ProfileSkeleton />}>
      <ProfileDetails userId={userId} />
      <Suspense fallback={<PostsSkeleton />}>
        <ProfilePosts userId={userId} />
      </Suspense>
    </Suspense>
  );
}

function ProfileDetails({ userId }) {
  const user = use(fetchUser(userId));  // suspends until resolved
  return <h1>{user.name}</h1>;
}
```

**How it works internally:** When a component throws a Promise (e.g., via the `use` hook or a Suspense-compatible library), React catches it, shows the Suspense fallback, and re-renders the component when the Promise resolves.

---

### Q45: What is the `useOptimistic` hook?

**Answer:** `useOptimistic` (React 19) provides a pattern for optimistic UI updates that automatically revert when the async action completes.

```tsx
function MessageThread({ messages, sendMessage }) {
  const [optimisticMessages, addOptimistic] = useOptimistic(
    messages,
    (currentMessages, newMessage) => [
      ...currentMessages,
      { ...newMessage, sending: true },
    ]
  );

  async function handleSend(formData) {
    const text = formData.get("text");
    addOptimistic({ text, id: crypto.randomUUID() });
    await sendMessage(text);
  }

  return (
    <>
      {optimisticMessages.map((msg) => (
        <div key={msg.id} style={{ opacity: msg.sending ? 0.6 : 1 }}>
          {msg.text}
        </div>
      ))}
      <form action={handleSend}>
        <input name="text" />
        <button>Send</button>
      </form>
    </>
  );
}
```

When `sendMessage` completes (or the parent re-renders with new `messages`), the optimistic state is replaced with the real server state. If the action fails, the optimistic addition disappears automatically.

---

## Scenario / Output-Based Questions (10 Questions)

### Q46: What does this output?

```tsx
function App() {
  const [count, setCount] = useState(0);

  console.log("render", count);

  useEffect(() => {
    console.log("effect", count);
  });

  return <button onClick={() => setCount(count + 1)}>Click</button>;
}
```

**Answer:** On mount: `render 0`, then `effect 0`. After each click: `render N`, then `effect N`. The `useEffect` without a dependency array runs after every render. Logs always appear in pairs: render first, then effect.

---

### Q47: What does this output?

```tsx
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log("effect");
    return () => console.log("cleanup");
  });

  return <button onClick={() => setCount((c) => c + 1)}>Click ({count})</button>;
}
```

**Answer:** On mount: `effect`. On first click: `cleanup`, `effect`. On second click: `cleanup`, `effect`. And so on. The cleanup function from the previous render runs before the new effect. On unmount, the final `cleanup` runs.

---

### Q48: What is wrong with this code?

```tsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then((data) => setUser(data));
  }, [userId]);

  return <div>{user?.name}</div>;
}
```

**Answer:** There is a race condition. If `userId` changes rapidly (e.g., from 1 to 2 to 3), three requests fire. They may resolve out of order: the response for userId=2 might arrive after userId=3. The component would display user 2's data even though userId is 3.

**Fix:** Use an AbortController or a cancelled flag:

```tsx
useEffect(() => {
  const controller = new AbortController();

  fetch(`/api/users/${userId}`, { signal: controller.signal })
    .then((res) => res.json())
    .then((data) => setUser(data))
    .catch((err) => {
      if (err.name !== "AbortError") console.error(err);
    });

  return () => controller.abort();
}, [userId]);
```

---

### Q49: What does this output?

```tsx
function App() {
  const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
  }

  return <button onClick={handleClick}>Count: {count}</button>;
}
```

**Answer:** After one click, count is `1`, not `3`. All three `setCount` calls use the same `count` value from the current closure (which is `0`). So all three set count to `0 + 1 = 1`. To increment three times, use the functional updater: `setCount(c => c + 1)`.

---

### Q50: What does this output?

```tsx
function App() {
  const [items, setItems] = useState([1, 2, 3]);

  const handleClick = () => {
    items.push(4);
    setItems(items);
  };

  return (
    <div>
      <button onClick={handleClick}>Add</button>
      <p>{items.join(", ")}</p>
    </div>
  );
}
```

**Answer:** Nothing visually changes on click. `items.push(4)` mutates the existing array, and `setItems(items)` passes the same reference. React uses `Object.is` to compare old and new state. Since the reference is the same, React skips the re-render.

**Fix:** Create a new array: `setItems([...items, 4])` or `setItems(prev => [...prev, 4])`.

---

### Q51: What is the problem here?

```tsx
function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData().then((result) => {
      setData(result);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spinner />;
  return <DataView data={data} />;
}
```

**Answer:** In React 18 with automatic batching, this works fine -- both state updates are batched into a single re-render. However, there is a subtler issue: the component does not handle the case where `fetchData` rejects. If the promise rejects, `loading` stays `true` forever and the user sees an infinite spinner.

**Fix:** Add error handling:

```tsx
const [error, setError] = useState(null);

useEffect(() => {
  fetchData()
    .then((result) => {
      setData(result);
      setLoading(false);
    })
    .catch((err) => {
      setError(err);
      setLoading(false);
    });
}, []);

if (loading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
return <DataView data={data} />;
```

---

### Q52: What does this output?

```tsx
function App() {
  const ref = useRef(0);
  const [, forceRender] = useState({});

  function handleClick() {
    ref.current += 1;
    console.log("ref:", ref.current);
    forceRender({});
  }

  console.log("render, ref:", ref.current);

  return <button onClick={handleClick}>Click</button>;
}
```

**Answer:** On mount: `render, ref: 0`. On first click: `ref: 1`, then `render, ref: 1`. On second click: `ref: 2`, then `render, ref: 2`. The ref mutation is synchronous, so `console.log` inside `handleClick` sees the updated value immediately. The subsequent re-render (triggered by `forceRender`) also sees the updated ref value because refs are mutable objects, not captured values.

---

### Q53: What does this output?

```tsx
function Parent() {
  console.log("Parent render");
  const [count, setCount] = useState(0);
  return (
    <div>
      <button onClick={() => setCount((c) => c + 1)}>Inc</button>
      <Child />
    </div>
  );
}

const Child = React.memo(function Child() {
  console.log("Child render");
  return <p>I am child</p>;
});
```

**Answer:** On mount: `Parent render`, `Child render`. On each button click: `Parent render` only. `React.memo` prevents `Child` from re-rendering because it receives no props (or more precisely, its props are `{}` which is shallowly equal to the previous `{}`).

**Follow-up:** What if `Child` received a prop like `style={{ color: 'red' }}`?

Then `Child` would re-render on every parent render because `{}` creates a new object reference each time. Fix with `useMemo`: `const style = useMemo(() => ({ color: 'red' }), [])`.

---

### Q54: What is wrong with this custom hook?

```tsx
function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    function handleResize() {
      setSize({ width: window.innerWidth, height: window.innerHeight });
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return size;
}
```

**Answer:** Two issues:

1. **SSR crash:** `window.innerWidth` is accessed during `useState` initialization, which runs on the server where `window` is undefined. Fix: use lazy initialization with a fallback: `useState(() => typeof window !== 'undefined' ? { width: window.innerWidth, height: window.innerHeight } : { width: 0, height: 0 })`.

2. **Performance:** Every resize event creates a new state object and triggers a re-render. This can fire 60+ times per second during a drag resize. Fix: throttle or debounce the handler.

---

### Q55: What does this output and why?

```tsx
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <h1>{count}</h1>;
}
```

**Answer:** The display shows `0`, then flips to `1` after one second, and stays at `1` forever. The effect closure captures `count = 0` from the initial render. Every interval tick calls `setCount(0 + 1)`, which sets count to `1`. After the first tick, React sees state is already `1` and does not re-render for subsequent `setCount(1)` calls.

**Fix:** Use the functional updater: `setCount(c => c + 1)`, or add `count` to the dependency array (but then you must re-create the interval on every count change, which is less clean).
