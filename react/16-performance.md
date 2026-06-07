# 16. React Performance Optimization

## Table of Contents

1. [React Rendering Pipeline](#react-rendering-pipeline)
2. [Unnecessary Re-renders](#unnecessary-re-renders)
3. [React DevTools Profiler](#react-devtools-profiler)
4. [Memoization Strategy](#memoization-strategy)
5. [Virtualization for Long Lists](#virtualization-for-long-lists)
6. [Lazy Loading Images](#lazy-loading-images)
7. [Bundle Analysis and Tree Shaking](#bundle-analysis-and-tree-shaking)
8. [Debouncing and Throttling](#debouncing-and-throttling)
9. [Web Vitals](#web-vitals)
10. [React Compiler (React Forget)](#react-compiler-react-forget)
11. [Windowing vs Pagination](#windowing-vs-pagination)
12. [When NOT to Optimize](#when-not-to-optimize)
13. [Output-Based and Scenario Questions](#output-based-and-scenario-questions)

---

## React Rendering Pipeline

Every React update follows three phases:

**Trigger -> Render -> Commit**

### Phase 1: Trigger

A render is triggered when:
- `setState` / `useState` setter is called
- Parent component re-renders
- Context value changes
- `forceUpdate()` is called (class components)

### Phase 2: Render (Reconciliation)

React calls your component function (or `render()` method). It builds a new virtual DOM tree and diffs it against the previous one using the reconciliation algorithm. This phase is **pure** -- no side effects, no DOM mutations.

Key point: "Rendering" does NOT mean updating the DOM. It means React is *calculating* what changed.

### Phase 3: Commit

React applies the minimal set of DOM mutations. After the DOM is updated, React runs `useLayoutEffect` synchronously, then `useEffect` asynchronously.

```
setState() called
    |
    v
[Trigger] --> [Render Phase] --> [Commit Phase] --> [Browser Paint]
                  |                    |
            Build new VDOM        Apply DOM diffs
            Diff with old         Run useLayoutEffect
            (pure, no side fx)    Run useEffect (async)
```

### Important Nuance

React may call your component function but skip the commit phase entirely if the output is identical. This is why you should never put side effects directly in the render body.

---

## Unnecessary Re-renders

### What Causes Them

```jsx
function Parent() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Inc</button>
      <Child /> {/* Re-renders every time Parent re-renders */}
    </div>
  );
}

function Child() {
  console.log("Child rendered");
  return <div>I am a child</div>;
}
```

`Child` re-renders on every `count` change even though it receives no props and displays nothing related to `count`.

### How to Detect Unnecessary Re-renders

1. **React DevTools Profiler** -- highlights components that re-rendered and why
2. **React DevTools "Highlight updates"** -- flashes a border around re-rendering components
3. **`console.log` in component body** -- quick and dirty
4. **`why-did-you-render` library** -- patches React to log unnecessary re-renders

```jsx
// Using why-did-you-render
import React from 'react';

if (process.env.NODE_ENV === 'development') {
  const whyDidYouRender = require('@welldone-software/why-did-you-render');
  whyDidYouRender(React, { trackAllPureComponents: true });
}
```

---

## React DevTools Profiler

The Profiler tab records renders and shows:

- **Flamegraph**: visual hierarchy of component renders with render times
- **Ranked chart**: components sorted by render time (slowest first)
- **Why did this render?**: tells you "Props changed", "State changed", "Parent rendered", etc.

### Reading the Profiler

- Gray bars = component did NOT re-render
- Colored bars = component rendered (yellow = slow, green = fast)
- Click a component to see its props/state at that point

### Programmatic Profiling

```jsx
import { Profiler } from 'react';

function onRenderCallback(id, phase, actualDuration, baseDuration, startTime, commitTime) {
  console.log(`${id} [${phase}] took ${actualDuration}ms`);
}

<Profiler id="MyComponent" onRender={onRenderCallback}>
  <MyComponent />
</Profiler>
```

---

## Memoization Strategy

### React.memo

Wraps a component to skip re-renders when props are shallowly equal.

```jsx
// BEFORE: Child re-renders whenever Parent re-renders
function Child({ name }) {
  console.log("Child rendered");
  return <div>{name}</div>;
}

// AFTER: Child only re-renders when `name` actually changes
const Child = React.memo(function Child({ name }) {
  console.log("Child rendered");
  return <div>{name}</div>;
});
```

Custom comparison:

```jsx
const Child = React.memo(
  function Child({ user }) {
    return <div>{user.name}</div>;
  },
  (prevProps, nextProps) => prevProps.user.id === nextProps.user.id
);
```

### useMemo

Caches the result of an expensive computation between re-renders.

```jsx
// BEFORE: Filters recalculated on every render
function FilteredList({ items, query }) {
  const filtered = items.filter(item =>
    item.name.toLowerCase().includes(query.toLowerCase())
  );
  return <ul>{filtered.map(i => <li key={i.id}>{i.name}</li>)}</ul>;
}

// AFTER: Only recalculates when items or query change
function FilteredList({ items, query }) {
  const filtered = useMemo(
    () => items.filter(item =>
      item.name.toLowerCase().includes(query.toLowerCase())
    ),
    [items, query]
  );
  return <ul>{filtered.map(i => <li key={i.id}>{i.name}</li>)}</ul>;
}
```

### useCallback

Caches a function reference between re-renders. Critical when passing callbacks to memoized children.

```jsx
// BEFORE: handleClick is a new reference every render, breaking React.memo on Child
function Parent() {
  const [count, setCount] = useState(0);
  const handleClick = () => console.log("clicked");

  return <MemoizedChild onClick={handleClick} />;
}

// AFTER: handleClick maintains referential equality
function Parent() {
  const [count, setCount] = useState(0);
  const handleClick = useCallback(() => console.log("clicked"), []);

  return <MemoizedChild onClick={handleClick} />;
}
```

### The Golden Rule

`React.memo` alone is useless if you pass new object/array/function references as props. You must stabilize those references with `useMemo`/`useCallback`.

```jsx
// This breaks React.memo because style is a new object every render
<MemoizedChild style={{ color: "red" }} />

// Fix: stabilize the object
const style = useMemo(() => ({ color: "red" }), []);
<MemoizedChild style={style} />
```

---

## Virtualization for Long Lists

Rendering 10,000 DOM nodes kills performance. Virtualization renders only what is visible in the viewport.

### react-window (lightweight)

```jsx
import { FixedSizeList } from 'react-window';

function VirtualList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>{items[index].name}</div>
  );

  return (
    <FixedSizeList
      height={400}
      width={300}
      itemCount={items.length}
      itemSize={35}
    >
      {Row}
    </FixedSizeList>
  );
}
```

### react-virtuoso (feature-rich)

```jsx
import { Virtuoso } from 'react-virtuoso';

function VirtualList({ items }) {
  return (
    <Virtuoso
      style={{ height: 400 }}
      totalCount={items.length}
      itemContent={(index) => <div>{items[index].name}</div>}
    />
  );
}
```

### Tradeoffs

| Feature | react-window | react-virtuoso |
|---|---|---|
| Bundle size | ~6KB | ~15KB |
| Variable height | VariableSizeList (manual) | Automatic measurement |
| Grouped lists | Not built-in | Built-in |
| Infinite scroll | Requires addon | Built-in |
| SSR | Limited | Better support |

---

## Lazy Loading Images

### Native Lazy Loading

```jsx
<img src="photo.jpg" loading="lazy" alt="Photo" />
```

The browser defers loading until the image is near the viewport. Supported in all modern browsers.

### Intersection Observer Approach

```jsx
function LazyImage({ src, alt }) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.disconnect();
      }
    });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref}>
      {isVisible ? <img src={src} alt={alt} /> : <div className="placeholder" />}
    </div>
  );
}
```

---

## Bundle Analysis and Tree Shaking

### webpack-bundle-analyzer

```bash
npm install --save-dev webpack-bundle-analyzer
# For CRA:
npx source-map-explorer build/static/js/*.js
```

Generates an interactive treemap showing what is in your bundle and how large each module is.

### Tree Shaking

Dead code elimination. Only works with ES module syntax (`import`/`export`), not CommonJS (`require`).

```jsx
// Tree-shakeable: bundler can remove unused exports
import { debounce } from 'lodash-es';

// NOT tree-shakeable: imports the entire library
import _ from 'lodash';
```

Mark your package.json with `"sideEffects": false` to help bundlers tree-shake aggressively.

---

## Debouncing and Throttling

### Debounce

Delays execution until a pause in events. Use for search inputs.

```jsx
function SearchInput() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const debouncedSearch = useMemo(
    () => debounce(async (q) => {
      const res = await fetch(`/api/search?q=${q}`);
      setResults(await res.json());
    }, 300),
    []
  );

  useEffect(() => {
    return () => debouncedSearch.cancel();
  }, [debouncedSearch]);

  const handleChange = (e) => {
    setQuery(e.target.value);
    debouncedSearch(e.target.value);
  };

  return <input value={query} onChange={handleChange} />;
}
```

### Throttle

Limits execution to at most once per interval. Use for scroll/resize handlers.

```jsx
function ScrollTracker() {
  useEffect(() => {
    const handleScroll = throttle(() => {
      console.log("Scroll position:", window.scrollY);
    }, 200);

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      handleScroll.cancel();
    };
  }, []);

  return <div style={{ height: 5000 }}>Scroll me</div>;
}
```

### Pitfall: Stale Closures

If your debounced/throttled function closes over state, the state may be stale. Use refs to hold the latest value.

---

## Web Vitals

### LCP (Largest Contentful Paint)

Time until the largest visible element (image, heading, text block) is rendered. Target: < 2.5s.

Optimization: preload hero images, use `<link rel="preload">`, optimize server response time.

### FID (First Input Delay) / INP (Interaction to Next Paint)

Time from user interaction to browser response. FID measures first interaction; INP (its replacement) measures all interactions. Target: < 200ms (INP).

Optimization: reduce main thread work, break up long tasks, use `startTransition`.

### CLS (Cumulative Layout Shift)

Measures visual instability -- elements moving around. Target: < 0.1.

Optimization: set explicit `width`/`height` on images and ads, avoid injecting content above existing content, use `transform` for animations.

```jsx
// Measuring web vitals in React
import { onLCP, onINP, onCLS } from 'web-vitals';

onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

---

## React Compiler (React Forget)

The React Compiler (formerly React Forget) is an **automatic memoization compiler** that ships with React 19. It analyzes your component code at build time and inserts `useMemo`, `useCallback`, and `React.memo` equivalents automatically.

### What It Does

```jsx
// You write this:
function ProductList({ products, category }) {
  const filtered = products.filter(p => p.category === category);
  const handleClick = (id) => { /* ... */ };
  return filtered.map(p => <ProductCard key={p.id} product={p} onClick={handleClick} />);
}

// Compiler transforms it to something equivalent to:
function ProductList({ products, category }) {
  const filtered = useMemo(() => products.filter(p => p.category === category), [products, category]);
  const handleClick = useCallback((id) => { /* ... */ }, []);
  return filtered.map(p => <ProductCard key={p.id} product={p} onClick={handleClick} />);
}
```

### Key Points for Interviews

- Requires components to follow the Rules of React (pure renders, no side effects in render)
- Does NOT replace understanding of memoization -- you need to know what it does to debug it
- Works at build time via a Babel plugin
- Can be adopted incrementally (per file or per component)
- Violations are surfaced via an ESLint plugin (`eslint-plugin-react-compiler`)

---

## Windowing vs Pagination

| Aspect | Windowing (Virtualization) | Pagination |
|---|---|---|
| UX | Continuous scroll | Discrete pages |
| Memory | Low (only visible items in DOM) | Low per page |
| SEO | Harder (content not in DOM) | Easier (each page is a URL) |
| Implementation | Library needed | Simpler |
| Total data loaded | All at once or streamed | Page at a time |
| Back button | Loses scroll position | Each page is a URL |

### When to Use Which

- **Windowing**: dashboards, admin panels, chat apps, infinite feeds where UX matters
- **Pagination**: search results, e-commerce product listings, SEO-critical pages, server-heavy workloads

---

## When NOT to Optimize

Premature optimization wastes time and adds complexity. Do NOT optimize when:

1. **The component renders in < 16ms** -- users won't notice
2. **The list has fewer than ~100 items** -- virtualization is overkill
3. **The memoization cost exceeds the render cost** -- `useMemo` for a simple string concatenation is slower than just doing it
4. **You haven't measured first** -- profile with DevTools before adding `React.memo` everywhere

The React team's stance: write idiomatic code first, measure second, optimize only bottlenecks. The React Compiler is designed to eliminate the need for manual memoization in most cases.

---

## Output-Based and Scenario Questions

### Question 1: Will `ExpensiveChild` re-render?

```jsx
const ExpensiveChild = React.memo(({ data }) => {
  console.log("ExpensiveChild rendered");
  return <div>{data.value}</div>;
});

function Parent() {
  const [count, setCount] = useState(0);
  const data = { value: "hello" };

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Click</button>
      <ExpensiveChild data={data} />
    </div>
  );
}
```

**Answer**: Yes, `ExpensiveChild` re-renders on every click. Even though `data` looks the same, `{ value: "hello" }` creates a new object reference each render. `React.memo` does a shallow comparison and sees a different reference. Fix: `const data = useMemo(() => ({ value: "hello" }), []);`

---

### Question 2: What is logged?

```jsx
function App() {
  const [count, setCount] = useState(0);

  console.log("App render");

  const increment = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return (
    <div>
      <p>{count}</p>
      <MemoButton onClick={increment} />
    </div>
  );
}

const MemoButton = React.memo(({ onClick }) => {
  console.log("MemoButton render");
  return <button onClick={onClick}>+</button>;
});
```

After clicking the button twice, the console shows:

```
App render
MemoButton render
App render
App render
```

**Answer**: On initial mount, both render. On subsequent clicks, only `App` re-renders because `increment` has a stable reference (via `useCallback` with `[]`), so `React.memo` on `MemoButton` prevents re-renders. `MemoButton render` appears only once (on mount).

---

### Question 3: Spot the performance bug

```jsx
function UserList({ users }) {
  return (
    <ul>
      {users.map((user, index) => (
        <li key={index}>{user.name}</li>
      ))}
    </ul>
  );
}
```

**Answer**: Using `index` as key is a performance (and correctness) bug when the list can be reordered, filtered, or items can be inserted/removed. React uses keys to match elements between renders. With index keys, React may reuse DOM nodes incorrectly, causing state bugs in child components and unnecessary DOM mutations. Fix: use a stable unique identifier like `user.id`.

---

### Question 4: Is this useMemo necessary?

```jsx
function Greeting({ firstName, lastName }) {
  const fullName = useMemo(
    () => `${firstName} ${lastName}`,
    [firstName, lastName]
  );
  return <h1>Hello, {fullName}</h1>;
}
```

**Answer**: No. String concatenation is trivially cheap. The overhead of `useMemo` (storing the previous value, comparing deps) is greater than just doing the concatenation. This is a textbook example of unnecessary memoization.

---

### Question 5: Real-world scenario

You have a dashboard with a sidebar (navigation) and a main panel (data table with 500 rows). Clicking a sidebar link fetches new data. Users report that clicking sidebar links feels laggy. The Profiler shows:

- Sidebar re-renders on every data fetch (takes 2ms)
- DataTable re-renders on every data fetch (takes 180ms)

What do you do?

**Answer**:

1. **Virtualize the DataTable** -- 500 rows should not all be in the DOM. Use `react-window` or `react-virtuoso` to render only visible rows. This is the highest-impact fix.
2. **Wrap Sidebar in `React.memo`** -- it does not depend on the data, so it should not re-render when data changes. But at 2ms, this is low priority.
3. **Use `startTransition`** for the data fetch -- marks the table update as non-urgent, keeping the sidebar click responsive.
4. **Do NOT bother memoizing the Sidebar** unless the DataTable fix is insufficient. 2ms is not user-perceptible.

---

### Question 6: What happens with this throttled handler?

```jsx
function SearchBox() {
  const [query, setQuery] = useState('');

  const handleChange = useCallback(
    throttle((value) => {
      setQuery(value);
    }, 500),
    []
  );

  return <input onChange={(e) => handleChange(e.target.value)} />;
}
```

**Answer**: The input will feel broken. The user types but the displayed value only updates every 500ms because `setQuery` is throttled. The input is controlled (`value` would need to be set), but here it is uncontrolled (no `value` prop), so the typing appears in the input natively, but `query` state lags behind. If this were a controlled input with `value={query}`, the user would see characters appearing in bursts every 500ms -- a terrible UX.

The correct pattern: update the input value immediately (uncontrolled or with a separate display state), and debounce/throttle only the expensive operation (API call, filtering).

---

## Key Pitfalls Summary

| Pitfall | Why It Matters |
|---|---|
| `React.memo` with unstable props | Memo is useless if you pass new object/fn references |
| `useMemo` for cheap operations | Adds overhead without benefit |
| Missing `key` or index-based keys | Incorrect reconciliation, state bugs |
| Debouncing controlled inputs | Makes typing feel laggy |
| Not measuring before optimizing | Wastes time on non-bottlenecks |
| Forgetting to cancel debounce on unmount | Memory leaks and state updates on unmounted components |
| Over-memoizing everything | Code complexity for negligible gain |
