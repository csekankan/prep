# React — Complete Core Concepts & FAANG Interview Reference

Everything you need to master React internals, patterns, and advanced concepts for FAANG-level frontend interviews — with real code examples and deep explanations.

---

## Table of Contents

1. [React Fundamentals](#1-react-fundamentals)
2. [JSX Deep Dive](#2-jsx-deep-dive)
3. [Virtual DOM & Reconciliation](#3-virtual-dom--reconciliation)
4. [React Fiber Architecture](#4-react-fiber-architecture)
5. [Components](#5-components)
6. [Props — Deep Dive](#6-props--deep-dive)
7. [State — Deep Dive](#7-state--deep-dive)
8. [Component Lifecycle](#8-component-lifecycle)
9. [Hooks — Complete Reference](#9-hooks--complete-reference)
10. [Custom Hooks](#10-custom-hooks)
11. [Rendering Behavior & Batching](#11-rendering-behavior--batching)
12. [Refs & the DOM](#12-refs--the-dom)
13. [Context API](#13-context-api)
14. [Error Boundaries](#14-error-boundaries)
15. [Portals](#15-portals)
16. [Higher-Order Components (HOC)](#16-higher-order-components-hoc)
17. [Render Props](#17-render-props)
18. [Compound Components](#18-compound-components)
19. [Performance Optimization](#19-performance-optimization)
20. [Code Splitting & Lazy Loading](#20-code-splitting--lazy-loading)
21. [Concurrent React & Suspense](#21-concurrent-react--suspense)
22. [Server Components & SSR](#22-server-components--ssr)
23. [State Management Patterns](#23-state-management-patterns)
24. [React & TypeScript](#24-react--typescript)
25. [Testing React Applications](#25-testing-react-applications)
26. [React Security](#26-react-security)
27. [React Design Patterns — Catalog](#27-react-design-patterns--catalog)
28. [React Internals — Interview Deep Dives](#28-react-internals--interview-deep-dives)
29. [Common FAANG Interview Questions](#29-common-faang-interview-questions)
30. [Cheatsheet](#30-cheatsheet)

---

## 1. React Fundamentals

### 1.1 What Is React?

React is a **declarative, component-based** JavaScript library for building user interfaces. It was created by Jordan Walke at Facebook (2013).

```
Core Philosophy:
  1. Declarative — describe WHAT the UI should look like, not HOW to update it
  2. Component-Based — build encapsulated pieces that compose into complex UIs
  3. Learn Once, Write Anywhere — React DOM, React Native, React Three Fiber
```

### 1.2 React vs. the DOM

```
Imperative (vanilla JS):
  const el = document.createElement('div');
  el.textContent = 'Hello';
  el.className = 'greeting';
  document.body.appendChild(el);

Declarative (React):
  <div className="greeting">Hello</div>

React handles the imperative DOM operations for you via the reconciler.
```

### 1.3 React Element vs. Component

```
React Element — a plain JavaScript object describing what to render.
  const element = { type: 'div', props: { children: 'Hello' } };
  // Created by React.createElement() or JSX

React Component — a function (or class) that RETURNS React elements.
  function Greeting() { return <div>Hello</div>; }

Key distinction:
  Element → lightweight description (blueprint)
  Component → factory that produces elements
```

```jsx
// React.createElement returns a plain object:
const element = React.createElement('h1', { className: 'title' }, 'Hello');

// Equivalent object:
{
  type: 'h1',
  props: {
    className: 'title',
    children: 'Hello'
  },
  key: null,
  ref: null,
  $$typeof: Symbol.for('react.element') // security — prevents JSON injection
}
```

### 1.4 Rendering Pipeline

```
JSX
  ↓  (Babel / SWC / esbuild)
React.createElement() calls
  ↓
React Element tree (virtual DOM)
  ↓  (Reconciler — diffing old vs new tree)
Minimal DOM mutations
  ↓
Browser paints pixels
```

---

## 2. JSX Deep Dive

### 2.1 What Is JSX?

JSX is a syntax extension that looks like HTML but compiles to `React.createElement()` calls (or the new JSX transform `jsx()` / `jsxs()`).

```jsx
// JSX
<Button variant="primary" onClick={handleClick}>
  Save
</Button>

// Compiles to (classic transform):
React.createElement(Button, { variant: "primary", onClick: handleClick }, "Save");

// Compiles to (new transform — React 17+):
import { jsx as _jsx } from 'react/jsx-runtime';
_jsx(Button, { variant: "primary", onClick: handleClick, children: "Save" });
```

### 2.2 JSX Rules & Gotchas

```
1. Must return a SINGLE root element (or Fragment)
2. All tags must be closed: <img /> not <img>
3. className instead of class
4. htmlFor instead of for
5. camelCase for event handlers: onClick, onChange, onSubmit
6. style takes an OBJECT, not a string: style={{ color: 'red' }}
7. Boolean attributes: disabled={true} or just disabled
8. Expressions in {}, not statements (no if/for inside JSX — use ternary or map)
```

### 2.3 Conditional Rendering Patterns

```jsx
// 1. Ternary
{isLoggedIn ? <Dashboard /> : <Login />}

// 2. Logical AND (short-circuit) — CAUTION with falsy values
{items.length > 0 && <ItemList items={items} />}
// BUG: {count && <Display />} renders "0" when count === 0
// FIX: {count > 0 && <Display />}

// 3. Early return
function Profile({ user }) {
  if (!user) return null;
  return <div>{user.name}</div>;
}

// 4. IIFE (rarely needed)
{(() => {
  switch (status) {
    case 'loading': return <Spinner />;
    case 'error': return <Error />;
    case 'success': return <Data />;
  }
})()}

// 5. Lookup object (preferred for switch-like logic)
const statusComponents = {
  loading: Spinner,
  error: ErrorView,
  success: DataView,
};
const Component = statusComponents[status];
return <Component />;
```

### 2.4 List Rendering & Keys

```jsx
// Keys help React identify which items changed, were added, or removed
{items.map(item => (
  <ListItem key={item.id} data={item} />
))}
```

```
Key Rules:
  ✓ Must be UNIQUE among siblings
  ✓ Must be STABLE (same item → same key across re-renders)
  ✓ Use domain identifiers (item.id, item.slug)

  ✗ NEVER use array index as key for dynamic lists
    — causes bugs with reordering, insertion, deletion
    — breaks component state (input values, animations)
  ✗ NEVER use Math.random() — remounts on every render

When index as key is acceptable:
  — static list that never reorders
  — no component state inside list items
  — items have no stable IDs
```

**Interview question: What happens without keys?**
```
React uses index by default. When items reorder:
  1. React compares element at index 0 (old) with element at index 0 (new)
  2. If types match, it REUSES the component instance (including state)
  3. This leads to stale state — e.g., checked checkbox stays at index 0
     even though the item that was at index 0 moved to index 2
```

---

## 3. Virtual DOM & Reconciliation

### 3.1 What Is the Virtual DOM?

```
Virtual DOM = in-memory representation of the real DOM as a tree of
              plain JavaScript objects (React elements).

Purpose:
  1. Batch DOM operations (DOM access is expensive)
  2. Diff old tree vs new tree → compute minimal set of mutations
  3. Enable declarative programming while maintaining performance
```

### 3.2 Reconciliation Algorithm (Diffing)

React's diffing algorithm runs in O(n) time using two key heuristics:

```
Heuristic 1: Elements of DIFFERENT types produce DIFFERENT trees.
  — If root element type changes (div → span), destroy entire subtree
    and rebuild from scratch.
  — If component type changes (ComponentA → ComponentB), unmount A,
    mount B (state is lost).

Heuristic 2: Developer provides KEYS to hint which children are stable.
  — Keys let React match children across renders without relying on order.
```

### 3.3 Diffing in Detail

```
Case 1: Same DOM element type
  <div className="old" /> → <div className="new" />
  → React keeps the DOM node, only updates changed attributes

Case 2: Same component type
  <Counter count={1} /> → <Counter count={2} />
  → React keeps the instance, calls render with new props
  → Triggers componentDidUpdate / useEffect cleanup + re-run

Case 3: Different types
  <div><Counter /></div> → <span><Counter /></span>
  → div is destroyed (Counter is unmounted)
  → span is created (Counter is mounted fresh — state reset)

Case 4: Lists
  Without keys: compares by index (buggy for dynamic lists)
  With keys: matches by key, then diffs matched pairs
```

### 3.4 Why Not Full Tree Diff?

```
Full tree diff (optimal): O(n³) — impractical for large UIs
React's heuristic diff:  O(n)  — trades perfect accuracy for speed

The tradeoff: React may do slightly more DOM work than strictly necessary,
but the diffing itself is fast enough to run on every state change.
```

---

## 4. React Fiber Architecture

### 4.1 What Is Fiber?

Fiber is React's internal reconciliation engine (introduced in React 16). It replaced the old "stack reconciler" with an architecture that supports:

```
1. Incremental rendering — split work into chunks
2. Pause, abort, or reuse work
3. Assign priority to different types of updates
4. Concurrency — multiple tasks can be in-flight
```

### 4.2 Fiber Node Structure

```
Each React element maps to a Fiber node:

FiberNode {
  tag           // FunctionComponent, ClassComponent, HostComponent, etc.
  type          // function/class reference or string ('div', 'span')
  key           // reconciliation key
  stateNode     // DOM node (for host components) or class instance
  
  // Fiber Tree Links (linked list, not recursive tree)
  return        // parent fiber
  child         // first child fiber
  sibling       // next sibling fiber
  
  // Work
  pendingProps  // new props (input)
  memoizedProps // props from last render (compared to detect changes)
  memoizedState // state from last render
  updateQueue   // linked list of state updates
  
  // Effects
  flags         // side-effect flags (Placement, Update, Deletion, etc.)
  subtreeFlags  // aggregated flags from children
  
  // Scheduling
  lanes         // priority lanes (bit field)
  childLanes    // lanes needed by subtree
  
  alternate     // points to the other version (current ↔ workInProgress)
}
```

### 4.3 Double Buffering

```
React maintains TWO fiber trees:

  current tree      — represents what's currently on screen
  workInProgress    — being built during rendering

After rendering completes:
  workInProgress becomes current (pointer swap)
  old current becomes the base for next workInProgress

This is "double buffering" — borrowed from graphics rendering.
No visible intermediate states appear on screen.
```

### 4.4 Render Phases

```
Phase 1: RENDER (reconciliation) — "pure", can be interrupted
  ┌─ beginWork()   — process fiber top-down (call component, diff children)
  └─ completeWork() — bottom-up (create DOM nodes, collect effects)
  
  This phase is INTERRUPTIBLE in concurrent mode.
  React can pause here, do higher-priority work, then resume.
  
  MUST be pure: no side effects, no DOM mutations.

Phase 2: COMMIT — synchronous, cannot be interrupted
  ┌─ Before mutation  — read DOM (getSnapshotBeforeUpdate)
  ├─ Mutation          — apply DOM changes (insertions, updates, deletions)
  └─ Layout            — run useLayoutEffect, componentDidMount/Update
  
  After commit: useEffect callbacks are scheduled (asynchronous).
```

### 4.5 Priority Lanes

```
React 18 uses a lanes model for scheduling:

  SyncLane              — click handlers, input (highest priority)
  InputContinuousLane   — drag, scroll
  DefaultLane           — data fetching, network responses
  TransitionLane        — startTransition updates (lower priority)
  IdleLane              — deferred / offscreen work (lowest priority)

Higher-priority updates can interrupt lower-priority rendering.
This is the foundation of concurrent features (useTransition, useDeferredValue).
```

---

## 5. Components

### 5.1 Function Components

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}

// Arrow function variant
const Greeting = ({ name }) => <h1>Hello, {name}!</h1>;
```

```
Function components:
  — Are plain JavaScript functions
  — Receive props as first argument
  — Return React elements (JSX)
  — Use hooks for state and side effects
  — Are the STANDARD in modern React (preferred over classes)
```

### 5.2 Class Components

```jsx
class Greeting extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }

  componentDidMount() {
    document.title = `Count: ${this.state.count}`;
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevState.count !== this.state.count) {
      document.title = `Count: ${this.state.count}`;
    }
  }

  componentWillUnmount() {
    document.title = 'React App';
  }

  handleClick = () => {
    this.setState(prev => ({ count: prev.count + 1 }));
  };

  render() {
    return (
      <div>
        <p>Count: {this.state.count}</p>
        <button onClick={this.handleClick}>Increment</button>
      </div>
    );
  }
}
```

### 5.3 Function vs. Class — Key Differences

```
Feature               Function Component        Class Component
─────────────────────────────────────────────────────────────────
State                 useState hook              this.state
Side effects          useEffect                  lifecycle methods
Ref                   useRef                     createRef
Context               useContext                 contextType / Consumer
Error boundary        ✗ (not supported)          componentDidCatch ✓
this binding          N/A                        manual binding needed
Closure behavior      captures props/state       reads latest this.props
Performance           slight edge (no instance)  instance overhead
Future React          concurrent features ✓      limited support
```

### 5.4 Closures vs. `this` — The Capture Problem

```jsx
// Function component — captures the value at render time
function ProfilePage({ user }) {
  const showMessage = () => {
    alert('Followed ' + user); // always shows the user from THIS render
  };
  
  setTimeout(showMessage, 3000);
}

// Class component — reads the LATEST value from this.props
class ProfilePage extends React.Component {
  showMessage = () => {
    alert('Followed ' + this.props.user); // shows the CURRENT user
  };
  
  // If user changes during the 3-second timeout, 
  // the alert shows the NEW user, not the one when button was clicked
  componentDidMount() {
    setTimeout(this.showMessage, 3000);
  }
}
```

```
This is a FUNDAMENTAL difference:
  Function components capture values (closure over render scope)
  Class components read latest values (via mutable this)

Dan Abramov's famous article: "How Are Function Components Different from Classes?"
```

---

## 6. Props — Deep Dive

### 6.1 Props Flow

```
Props flow ONE WAY: parent → child (unidirectional data flow)

Parent                     Child
  │                          │
  ├── passes props ──────►   │ receives as argument
  │                          │ CANNOT modify props
  │                          │ (props are read-only)
  │   ◄── calls callback ── │ communicates up via callback props
```

### 6.2 Props Patterns

```jsx
// Destructuring with defaults
function Button({ variant = 'primary', size = 'md', children, ...rest }) {
  return (
    <button className={`btn btn-${variant} btn-${size}`} {...rest}>
      {children}
    </button>
  );
}

// Render callback (function as child)
function DataFetcher({ url, children }) {
  const [data, setData] = useState(null);
  useEffect(() => { fetch(url).then(r => r.json()).then(setData); }, [url]);
  return children(data);
}

// Usage
<DataFetcher url="/api/user">
  {data => data ? <Profile data={data} /> : <Spinner />}
</DataFetcher>
```

### 6.3 children Prop

```jsx
// children is a special prop — content between opening and closing tags

// String
<Title>Hello</Title>        // children = "Hello"

// Element
<Card><Avatar /></Card>     // children = <Avatar /> element

// Multiple children
<Layout>                    // children = [<Header />, <Main />, <Footer />]
  <Header />
  <Main />
  <Footer />
</Layout>

// Function (render prop pattern)
<Mouse>{pos => <Cat position={pos} />}</Mouse>

// React.Children utilities for manipulating children
React.Children.map(children, child => ...)
React.Children.count(children)
React.Children.only(children)  // throws if not exactly one child
React.Children.toArray(children)
```

### 6.4 Prop Drilling & Solutions

```
Prop drilling = passing props through intermediate components that don't need them

App → Layout → Sidebar → UserInfo → Avatar
                                      ↑
                                    needs "user" prop
                                    but Layout and Sidebar don't care

Solutions:
  1. Context API — for truly global data (theme, auth, locale)
  2. Component composition — restructure to avoid passing through
  3. Render props / children — invert control
  4. State management library — Redux, Zustand, Jotai
```

```jsx
// Component composition fixes drilling without Context:

// BEFORE (drilling):
function App() {
  return <Layout user={user} />;
}
function Layout({ user }) {
  return <Sidebar user={user} />;      // doesn't use user, just passes it
}
function Sidebar({ user }) {
  return <Avatar user={user} />;
}

// AFTER (composition):
function App() {
  return (
    <Layout sidebar={<Sidebar avatar={<Avatar user={user} />} />} />
  );
}
function Layout({ sidebar }) {
  return <div>{sidebar}</div>;          // no knowledge of "user"
}
```

---

## 7. State — Deep Dive

### 7.1 What Is State?

```
State = data that changes over time and affects what the component renders.

When state changes → React re-renders the component (and its subtree).

State is:
  — Local to the component (unless lifted or shared)
  — Preserved between re-renders (React "remembers" it)
  — Updated ASYNCHRONOUSLY (batched)
  — Immutable (never mutate directly — always create new references)
```

### 7.2 useState

```jsx
const [count, setCount] = useState(0);

// Direct value
setCount(5);

// Updater function (when new state depends on old state)
setCount(prev => prev + 1);

// Lazy initialization (expensive initial computation)
const [data, setData] = useState(() => computeExpensiveValue());
```

### 7.3 State Immutability — Why It Matters

```jsx
// ✗ WRONG — mutating state directly
const [user, setUser] = useState({ name: 'Alice', age: 25 });
user.name = 'Bob';      // mutation — React doesn't see this change
setUser(user);           // same reference — React skips re-render (Object.is)

// ✓ CORRECT — creating new reference
setUser({ ...user, name: 'Bob' });
setUser(prev => ({ ...prev, name: 'Bob' }));

// Nested objects
const [state, setState] = useState({
  user: { address: { city: 'NYC' } }
});

// ✗ WRONG
state.user.address.city = 'LA';

// ✓ CORRECT
setState(prev => ({
  ...prev,
  user: {
    ...prev.user,
    address: {
      ...prev.user.address,
      city: 'LA'
    }
  }
}));

// Arrays
const [items, setItems] = useState([1, 2, 3]);
setItems([...items, 4]);                       // add
setItems(items.filter(i => i !== 2));           // remove
setItems(items.map(i => i === 2 ? 20 : i));    // update
```

```
Why immutability?
  1. React uses Object.is() to compare old state vs new state
  2. Same reference → skip re-render (optimization)
  3. New reference → re-render
  4. If you mutate, the reference stays the same → React misses the update
  5. Also enables features like time-travel debugging, undo/redo
```

### 7.4 State Batching

```jsx
// React 18+ batches ALL state updates (even in promises, timeouts, event handlers)

function handleClick() {
  setCount(c => c + 1);    // does NOT re-render yet
  setFlag(f => !f);        // does NOT re-render yet
  setName('Bob');           // does NOT re-render yet
  // React batches all three → ONE re-render
}

// Even in async code (NEW in React 18):
async function handleSubmit() {
  const data = await fetchData();
  setLoading(false);       // batched
  setData(data);           // batched → one re-render
}

// To force synchronous update (rare):
import { flushSync } from 'react-dom';
flushSync(() => setCount(c => c + 1)); // re-renders immediately
flushSync(() => setFlag(f => !f));      // re-renders again
```

### 7.5 Lifting State Up

```
When two sibling components need to share state:
  1. Move state to their CLOSEST common ancestor
  2. Pass state down as props
  3. Pass setter/callback down for children to update

                    Parent (owns state)
                   /                    \
          ChildA (reads)          ChildB (updates via callback)
```

```jsx
function Parent() {
  const [temp, setTemp] = useState(0);
  return (
    <>
      <TemperatureDisplay celsius={temp} />
      <TemperatureInput onTempChange={setTemp} />
    </>
  );
}
```

### 7.6 Derived State

```
Derived state = values computed from existing state or props.
Do NOT store derived values in state — compute them during render.
```

```jsx
// ✗ WRONG — storing derived state
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]);
const [query, setQuery] = useState('');

useEffect(() => {
  setFilteredItems(items.filter(i => i.includes(query)));
}, [items, query]);

// ✓ CORRECT — compute during render
const [items, setItems] = useState([]);
const [query, setQuery] = useState('');
const filteredItems = items.filter(i => i.includes(query));

// If the computation is expensive, memoize:
const filteredItems = useMemo(
  () => items.filter(i => i.includes(query)),
  [items, query]
);
```

---

## 8. Component Lifecycle

### 8.1 Class Component Lifecycle

```
MOUNTING (component created and inserted into DOM)
  ├── constructor()
  ├── static getDerivedStateFromProps(props, state)
  ├── render()
  ├── DOM updated
  └── componentDidMount()

UPDATING (re-render due to props/state change)
  ├── static getDerivedStateFromProps(props, state)
  ├── shouldComponentUpdate(nextProps, nextState)
  ├── render()
  ├── getSnapshotBeforeUpdate(prevProps, prevState)
  ├── DOM updated
  └── componentDidUpdate(prevProps, prevState, snapshot)

UNMOUNTING
  └── componentWillUnmount()

ERROR HANDLING
  ├── static getDerivedStateFromError(error)
  └── componentDidCatch(error, info)
```

### 8.2 Hooks Equivalents

```
Lifecycle Method             Hook Equivalent
──────────────────────────────────────────────────────────
constructor                  useState (initialization)
                             useRef (instance variables)
componentDidMount            useEffect(() => { ... }, [])
componentDidUpdate           useEffect(() => { ... }, [deps])
componentWillUnmount         useEffect(() => { return () => cleanup; }, [])
shouldComponentUpdate        React.memo (for function components)
getDerivedStateFromProps      Compute during render or use useEffect
getSnapshotBeforeUpdate       useLayoutEffect (close but not exact)
componentDidCatch            ✗ No hook equivalent (use class ErrorBoundary)
getDerivedStateFromError     ✗ No hook equivalent
```

---

## 9. Hooks — Complete Reference

### 9.1 Rules of Hooks

```
Rule 1: Only call hooks at the TOP LEVEL
  — NOT inside loops, conditions, or nested functions
  — React relies on call ORDER to match hooks to their state

Rule 2: Only call hooks from React FUNCTIONS
  — Function components
  — Custom hooks (functions starting with "use")
  — NOT from regular functions or class components

Why call order matters:
  React stores hooks in a linked list per component.
  On each render, it walks the list in order.
  If you skip a hook call (via condition), the list gets misaligned.
```

```jsx
// ✗ WRONG — conditional hook
function Component({ showName }) {
  if (showName) {
    const [name, setName] = useState('');  // BREAKS if showName changes
  }
  const [age, setAge] = useState(0);
}

// ✓ CORRECT — always call, conditionally use
function Component({ showName }) {
  const [name, setName] = useState('');
  const [age, setAge] = useState(0);
  // Use name conditionally in JSX, not in hook call
}
```

### 9.2 useState

```jsx
// Signature
const [state, setState] = useState(initialValue);
const [state, setState] = useState(() => computeInitialValue()); // lazy init

// setState behavior:
// 1. Triggers re-render
// 2. Batched with other updates
// 3. Object.is comparison — same value → no re-render
// 4. Updater function receives previous state

setState(newValue);           // direct
setState(prev => prev + 1);   // updater (recommended when depending on prev)
```

### 9.3 useEffect

```jsx
// Signature
useEffect(setup, dependencies?);

// 1. Run on EVERY render (rarely desired)
useEffect(() => {
  console.log('renders');
});

// 2. Run ONCE on mount (componentDidMount)
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe(); // cleanup on unmount
}, []);

// 3. Run when DEPENDENCIES change
useEffect(() => {
  fetchUser(userId);
}, [userId]); // re-runs when userId changes

// 4. Cleanup runs BEFORE the effect re-runs AND on unmount
useEffect(() => {
  const handler = () => console.log(query);
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler);
}, [query]);
```

```
Effect timing:
  1. React renders (calls your component)
  2. React commits to DOM (screen updates)
  3. Browser paints
  4. React runs useEffect (AFTER paint — asynchronous)

This means useEffect does NOT block the browser from painting.
For synchronous DOM measurements, use useLayoutEffect.
```

**Common useEffect Mistakes:**

```jsx
// ✗ Missing dependency
useEffect(() => {
  fetchData(userId);
}, []); // userId missing → stale closure

// ✗ Object/array in dependency (new reference every render)
useEffect(() => {
  doSomething(options);
}, [options]); // if options = { ... } created in render, runs every time

// Fix: memoize the object or extract primitive dependencies
useEffect(() => {
  doSomething({ sortBy, filterBy });
}, [sortBy, filterBy]); // primitive deps are stable

// ✗ Infinite loop
useEffect(() => {
  setCount(count + 1); // state change → re-render → effect → state change → ...
}, [count]);

// ✗ Fetching without cleanup (race condition)
useEffect(() => {
  fetchData(id).then(setData); // if id changes fast, old response may arrive last
}, [id]);

// ✓ Fix with abort controller
useEffect(() => {
  const controller = new AbortController();
  fetchData(id, { signal: controller.signal }).then(setData).catch(() => {});
  return () => controller.abort();
}, [id]);

// ✓ Fix with boolean flag
useEffect(() => {
  let cancelled = false;
  fetchData(id).then(data => {
    if (!cancelled) setData(data);
  });
  return () => { cancelled = true; };
}, [id]);
```

### 9.4 useLayoutEffect

```jsx
useLayoutEffect(() => {
  // Runs SYNCHRONOUSLY after DOM mutations, BEFORE browser paint
  // Use for: DOM measurements, scroll position, preventing visual flicker
  const { height } = ref.current.getBoundingClientRect();
  setHeight(height);
}, []);
```

```
Timeline comparison:
  useEffect:       render → commit → paint → effect
  useLayoutEffect: render → commit → effect → paint

useLayoutEffect blocks painting — use sparingly.
Common use cases:
  — Measuring DOM elements (tooltips, popovers)
  — Synchronously adjusting layout before user sees it
  — Integrating with third-party DOM libraries
```

### 9.5 useReducer

```jsx
const [state, dispatch] = useReducer(reducer, initialState, init?);

// Reducer function (must be pure)
function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + 1 };
    case 'decrement':
      return { ...state, count: state.count - 1 };
    case 'set':
      return { ...state, count: action.payload };
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

// Usage
const [state, dispatch] = useReducer(reducer, { count: 0 });
dispatch({ type: 'increment' });
dispatch({ type: 'set', payload: 42 });
```

```
When to use useReducer vs useState:
  useState   — simple, independent state values
  useReducer — complex state logic, multiple related values, 
               state transitions that depend on previous state,
               when next state depends on the action AND current state
```

### 9.6 useRef

```jsx
const ref = useRef(initialValue);
// ref.current persists across renders (mutable container)
// Changing ref.current does NOT trigger re-render

// 1. DOM reference
function TextInput() {
  const inputRef = useRef(null);
  const focusInput = () => inputRef.current.focus();
  return <input ref={inputRef} />;
}

// 2. Instance variable (previous value)
function Counter() {
  const [count, setCount] = useState(0);
  const prevCount = useRef(count);
  
  useEffect(() => {
    prevCount.current = count;
  });
  
  return <p>Now: {count}, Before: {prevCount.current}</p>;
}

// 3. Storing interval/timeout IDs
function Timer() {
  const intervalRef = useRef(null);
  
  const start = () => {
    intervalRef.current = setInterval(() => tick(), 1000);
  };
  
  const stop = () => {
    clearInterval(intervalRef.current);
  };
  
  useEffect(() => () => clearInterval(intervalRef.current), []);
}
```

### 9.7 useMemo

```jsx
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);

// Only recomputes when a or b changes
// Returns the CACHED value on other re-renders
```

```
When to use useMemo:
  ✓ Expensive computations (sorting/filtering large lists)
  ✓ Referential equality for objects/arrays passed to memoized children
  ✓ Preventing expensive re-computations in render

  ✗ Don't memoize everything — the memoization itself has cost
  ✗ Don't use for simple computations (a + b)
  ✗ React may drop cached values (it's an optimization hint, not guarantee)
```

### 9.8 useCallback

```jsx
const memoizedCallback = useCallback(
  (arg) => doSomething(arg, dep1, dep2),
  [dep1, dep2]
);

// Equivalent to:
const memoizedCallback = useMemo(
  () => (arg) => doSomething(arg, dep1, dep2),
  [dep1, dep2]
);
```

```
useCallback memoizes the FUNCTION REFERENCE (identity).
useMemo memoizes the RETURN VALUE.

Primary use case: preventing re-renders of memoized children.

function Parent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <MemoizedChild onClick={handleClick} />;
}

const MemoizedChild = React.memo(({ onClick }) => {
  return <button onClick={onClick}>Click</button>;
});

Without useCallback:
  — Parent re-renders → new handleClick function created
  — React.memo sees new prop reference → re-renders child

With useCallback:
  — Parent re-renders → same handleClick function returned
  — React.memo sees same prop reference → skips child re-render
```

### 9.9 useContext

```jsx
const value = useContext(MyContext);

// Subscribes the component to context changes.
// Re-renders when the nearest <MyContext.Provider> value changes.
// See Section 13 for full Context API coverage.
```

### 9.10 useImperativeHandle

```jsx
// Customize the ref value exposed to parent components
// Used with forwardRef

const FancyInput = forwardRef((props, ref) => {
  const inputRef = useRef();
  
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current.focus(),
    getValue: () => inputRef.current.value,
    // Only expose specific methods, not the entire DOM node
  }), []);
  
  return <input ref={inputRef} />;
});

// Parent
function Parent() {
  const ref = useRef();
  return (
    <>
      <FancyInput ref={ref} />
      <button onClick={() => ref.current.focus()}>Focus</button>
    </>
  );
}
```

### 9.11 useId

```jsx
// Generates unique IDs stable across server & client (hydration-safe)
function PasswordField() {
  const id = useId();
  return (
    <>
      <label htmlFor={id}>Password</label>
      <input id={id} type="password" />
    </>
  );
}
// DO NOT use for keys in lists
```

### 9.12 useTransition

```jsx
// Mark state updates as non-urgent (can be interrupted by urgent updates)
function SearchResults() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  function handleChange(e) {
    setQuery(e.target.value);               // urgent — update input immediately
    startTransition(() => {
      setResults(filterLargeList(e.target.value)); // non-urgent — can be interrupted
    });
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <ResultList results={results} />}
    </>
  );
}
```

### 9.13 useDeferredValue

```jsx
// Defer re-rendering a value until higher-priority updates complete
function SearchResults({ query }) {
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;
  
  const results = useMemo(() => filterItems(deferredQuery), [deferredQuery]);
  
  return (
    <div style={{ opacity: isStale ? 0.5 : 1 }}>
      <ResultList results={results} />
    </div>
  );
}
```

```
useTransition vs useDeferredValue:
  useTransition — you control the state update (wrap setState)
  useDeferredValue — you receive a prop/value, defer its effect on rendering

Both allow React to keep the UI responsive during expensive renders.
```

### 9.14 useSyncExternalStore

```jsx
// Subscribe to external stores (Redux, Zustand, browser APIs)
const width = useSyncExternalStore(
  subscribe,   // function that subscribes to the store
  getSnapshot, // function that returns current value
  getServerSnapshot? // optional, for SSR
);

// Example: window width
function useWindowWidth() {
  return useSyncExternalStore(
    (callback) => {
      window.addEventListener('resize', callback);
      return () => window.removeEventListener('resize', callback);
    },
    () => window.innerWidth,
    () => 1024 // server fallback
  );
}
```

### 9.15 useInsertionEffect (CSS-in-JS libraries only)

```jsx
// Fires BEFORE any DOM mutations — for injecting styles
// Only for CSS-in-JS library authors
useInsertionEffect(() => {
  const style = document.createElement('style');
  style.textContent = rule;
  document.head.appendChild(style);
  return () => style.remove();
}, [rule]);
```

```
Execution order:
  useInsertionEffect → DOM mutations → useLayoutEffect → paint → useEffect
```

---

## 10. Custom Hooks

### 10.1 Principles

```
Custom hooks:
  — Extract reusable stateful logic
  — Start with "use" prefix (enforced by linter)
  — Can call other hooks
  — Each call gets its own isolated state
  — Are just regular functions that follow the Rules of Hooks
```

### 10.2 Essential Custom Hooks

```jsx
// useToggle
function useToggle(initial = false) {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue(v => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);
  return { value, toggle, setTrue, setFalse };
}

// useDebounce
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}

// usePrevious
function usePrevious(value) {
  const ref = useRef();
  useEffect(() => { ref.current = value; });
  return ref.current;
}

// useLocalStorage
function useLocalStorage(key, initialValue) {
  const [stored, setStored] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    setStored(prev => {
      const next = value instanceof Function ? value(prev) : value;
      localStorage.setItem(key, JSON.stringify(next));
      return next;
    });
  }, [key]);

  return [stored, setValue];
}

// useFetch
function useFetch(url) {
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState(s => ({ ...s, loading: true, error: null }));

    fetch(url, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => setState({ data, loading: false, error: null }))
      .catch(err => {
        if (err.name !== 'AbortError') {
          setState({ data: null, loading: false, error: err });
        }
      });

    return () => controller.abort();
  }, [url]);

  return state;
}

// useIntersectionObserver
function useIntersectionObserver(ref, options = {}) {
  const [isIntersecting, setIsIntersecting] = useState(false);
  
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);
    
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, options.threshold, options.root, options.rootMargin]);
  
  return isIntersecting;
}

// useMediaQuery
function useMediaQuery(query) {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches
  );
  
  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);
  
  return matches;
}

// useOnClickOutside
function useOnClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      handler(event);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
```

---

## 11. Rendering Behavior & Batching

### 11.1 What Triggers a Re-render?

```
A component re-renders when:
  1. Its state changes (setState/dispatch)
  2. Its parent re-renders (even if props haven't changed!)
  3. A context it consumes changes
  4. forceUpdate() is called (class components)

A component does NOT re-render when:
  ✗ Props change alone (only if parent re-renders and passes new props)
  ✗ Ref changes (ref.current mutation is silent)
  ✗ A variable outside state changes
```

### 11.2 Render ≠ DOM Update

```
"Rendering" in React means calling your component function.
It does NOT necessarily mean the DOM changes.

Render → Reconciliation (diff) → only changed parts → DOM update

If render produces identical output, React skips DOM mutations.
The component function still ran (wasted work), but the DOM is untouched.
This is why memoization (React.memo) helps — it skips the RENDER itself.
```

### 11.3 Re-render Cascade

```
When Parent re-renders, ALL children re-render by default:

Parent (re-renders)
  ├── ChildA (re-renders — even if props unchanged)
  │     └── GrandchildA (re-renders)
  ├── ChildB (re-renders)
  └── ChildC (re-renders)

To prevent unnecessary child re-renders:
  1. React.memo(Child) — skip if props haven't changed
  2. Move state down — only the component that needs it re-renders
  3. Lift content up — pass children as props (they're already created)
```

### 11.4 The Children-as-Props Optimization

```jsx
// ✗ SlowChild re-renders when count changes (because Parent re-renders)
function Parent() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>{count}</button>
      <SlowChild />  {/* re-renders even though it doesn't use count */}
    </div>
  );
}

// ✓ Fix: move state into a wrapper, pass SlowChild as children
function CounterWrapper({ children }) {
  const [count, setCount] = useState(0);
  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>{count}</button>
      {children}  {/* children prop doesn't change — SlowChild skips render */}
    </div>
  );
}

function Parent() {
  return (
    <CounterWrapper>
      <SlowChild />
    </CounterWrapper>
  );
}
```

---

## 12. Refs & the DOM

### 12.1 Ref Callback Pattern

```jsx
// Instead of useRef, pass a function to the ref attribute
function MeasureExample() {
  const [height, setHeight] = useState(0);

  const measuredRef = useCallback((node) => {
    if (node !== null) {
      setHeight(node.getBoundingClientRect().height);
    }
  }, []);

  return <div ref={measuredRef}>Hello</div>;
}
// Useful when you need to act on the DOM node at mount time
// or when the ref is conditionally applied
```

### 12.2 forwardRef

```jsx
// Forward a ref from parent to a child's DOM element
const FancyButton = forwardRef((props, ref) => (
  <button ref={ref} className="fancy">
    {props.children}
  </button>
));

// Parent can now access the <button> DOM node
function Parent() {
  const buttonRef = useRef();
  return <FancyButton ref={buttonRef}>Click me</FancyButton>;
}

// React 19: ref is a regular prop (no forwardRef needed)
function FancyButton({ ref, children }) {
  return <button ref={ref} className="fancy">{children}</button>;
}
```

### 12.3 When to Use Refs vs. State

```
Use Ref when:
  — Value doesn't affect visual output
  — Need to access DOM nodes directly
  — Need mutable value that persists without re-rendering
  — Storing timer/interval IDs

Use State when:
  — Value changes should trigger re-render
  — Value is displayed in UI
  — Value determines component behavior
```

---

## 13. Context API

### 13.1 Creating and Using Context

```jsx
// 1. Create
const ThemeContext = createContext('light'); // default value

// 2. Provide
function App() {
  const [theme, setTheme] = useState('dark');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <Main />
    </ThemeContext.Provider>
  );
}

// 3. Consume
function ThemedButton() {
  const { theme, setTheme } = useContext(ThemeContext);
  return <button className={theme}>Toggle</button>;
}
```

### 13.2 Context Performance Problem

```
Problem: When context value changes, ALL consumers re-render,
even if they only use a part of the value that didn't change.

const value = { user, theme, locale };
// If user changes, components that only use theme still re-render.
```

### 13.3 Context Optimization Strategies

```jsx
// Strategy 1: Split contexts
const UserContext = createContext(null);
const ThemeContext = createContext('light');
// Now theme consumers don't re-render when user changes

// Strategy 2: Memoize the value object
function App() {
  const [theme, setTheme] = useState('light');
  const value = useMemo(() => ({ theme, setTheme }), [theme]);
  return <ThemeContext.Provider value={value}><Main /></ThemeContext.Provider>;
}

// Strategy 3: Separate state and dispatch contexts
const StateContext = createContext(null);
const DispatchContext = createContext(null);

function Provider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <DispatchContext.Provider value={dispatch}>
      <StateContext.Provider value={state}>
        {children}
      </StateContext.Provider>
    </DispatchContext.Provider>
  );
}
// Components that only dispatch don't re-render when state changes

// Strategy 4: Use selector pattern (external libraries or useSyncExternalStore)
```

### 13.4 Context vs. State Management Libraries

```
Context is good for:
  — Infrequently changing data (theme, locale, auth)
  — Avoiding prop drilling for a few values

Context is NOT ideal for:
  — High-frequency updates (causes cascading re-renders)
  — Complex state logic (use useReducer + context or external store)
  — Global app state with many consumers reading different slices

For complex state:
  — Zustand — minimal, hooks-based, no provider needed
  — Jotai — atomic state, fine-grained updates
  — Redux Toolkit — predictable, middleware, devtools
  — Recoil — atom-based, async selectors (Meta)
```

---

## 14. Error Boundaries

### 14.1 Class-based Error Boundary

```jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}

// Usage
<ErrorBoundary fallback={<ErrorPage />}>
  <UserProfile />
</ErrorBoundary>
```

### 14.2 What Error Boundaries Catch & Don't Catch

```
✓ Catches:
  — Errors during rendering
  — Errors in lifecycle methods
  — Errors in constructors of the whole subtree

✗ Does NOT catch:
  — Event handler errors (use try/catch)
  — Async code (promises, setTimeout)
  — Server-side rendering errors
  — Errors in the error boundary itself
```

### 14.3 Recovery Pattern

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  handleRetry = () => {
    this.setState({ hasError: false }); // reset → re-mount children
  };

  render() {
    if (this.state.hasError) {
      return <button onClick={this.handleRetry}>Retry</button>;
    }
    return this.props.children;
  }
}

// Granular boundaries — wrap individual features, not the entire app
<Layout>
  <ErrorBoundary fallback={<SidebarError />}>
    <Sidebar />
  </ErrorBoundary>
  <ErrorBoundary fallback={<ContentError />}>
    <MainContent />
  </ErrorBoundary>
</Layout>
```

---

## 15. Portals

```jsx
import { createPortal } from 'react-dom';

function Modal({ children, isOpen }) {
  if (!isOpen) return null;
  
  return createPortal(
    <div className="modal-overlay">
      <div className="modal-content">{children}</div>
    </div>,
    document.getElementById('modal-root') // renders outside parent DOM hierarchy
  );
}
```

```
Portals:
  — Render children into a DOM node outside the parent hierarchy
  — Event bubbling still follows the REACT tree (not DOM tree)
  — CSS stacking context issues are avoided (z-index, overflow: hidden)

Use cases:
  — Modals / Dialogs
  — Tooltips / Popovers
  — Dropdown menus
  — Notifications / Toasts
```

---

## 16. Higher-Order Components (HOC)

### 16.1 Pattern

```jsx
// HOC = function that takes a component and returns a new component
function withAuth(WrappedComponent) {
  return function AuthenticatedComponent(props) {
    const { user, loading } = useAuth();
    
    if (loading) return <Spinner />;
    if (!user) return <Redirect to="/login" />;
    
    return <WrappedComponent {...props} user={user} />;
  };
}

const ProtectedDashboard = withAuth(Dashboard);
```

### 16.2 HOC Best Practices

```
✓ Pass through unrelated props: {...props}
✓ Maximize composability: compose(withAuth, withTheme)(Component)
✓ Wrap display name for debugging:
    AuthComponent.displayName = `withAuth(${getDisplayName(WrappedComponent)})`;
✓ Hoist non-React statics: hoist-non-react-statics library

✗ Don't mutate the original component
✗ Don't apply HOC inside render (creates new component type each render)
✗ Don't copy refs (use forwardRef)
```

### 16.3 HOC vs. Hooks

```
HOCs were the primary reuse pattern before hooks.
Modern React favors custom hooks for most use cases.

HOC advantages:
  — Can wrap component with additional JSX (layout, providers)
  — Can control whether the wrapped component renders
  — Work with class and function components

Hook advantages:
  — No wrapper component (no extra nesting in React DevTools)
  — Simpler mental model
  — Can share stateful logic without changing component hierarchy
  — Composable without compose() utilities
```

---

## 17. Render Props

```jsx
// Pattern: component takes a function prop that returns React elements
function Mouse({ render }) {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  
  const handleMouseMove = (e) => {
    setPos({ x: e.clientX, y: e.clientY });
  };
  
  return (
    <div onMouseMove={handleMouseMove} style={{ height: '100vh' }}>
      {render(pos)}
    </div>
  );
}

// Usage
<Mouse render={({ x, y }) => (
  <p>Mouse is at ({x}, {y})</p>
)} />

// Function-as-children variant
<Mouse>
  {({ x, y }) => <p>Mouse is at ({x}, {y})</p>}
</Mouse>
```

```
Render props vs. custom hooks:
  — Same problem solved: sharing stateful logic
  — Hooks are simpler and more common today
  — Render props still useful when you need to control the render output
    from WITHIN the shared logic component
```

---

## 18. Compound Components

```jsx
// Pattern: components that work together sharing implicit state

// API usage
<Select value={selected} onChange={setSelected}>
  <Select.Option value="a">Option A</Select.Option>
  <Select.Option value="b">Option B</Select.Option>
  <Select.Option value="c">Option C</Select.Option>
</Select>

// Implementation using Context
const SelectContext = createContext(null);

function Select({ value, onChange, children }) {
  return (
    <SelectContext.Provider value={{ value, onChange }}>
      <div className="select">{children}</div>
    </SelectContext.Provider>
  );
}

function Option({ value, children }) {
  const { value: selected, onChange } = useContext(SelectContext);
  const isSelected = value === selected;
  
  return (
    <div
      className={`option ${isSelected ? 'selected' : ''}`}
      onClick={() => onChange(value)}
    >
      {children}
    </div>
  );
}

Select.Option = Option;
```

```
Compound component benefits:
  — Flexible API (user controls order and composition of children)
  — Implicit state sharing (no prop drilling between related components)
  — Inversion of control (parent decides what to render, child handles logic)

Real-world examples:
  <Tabs> / <Tab> / <TabPanel>
  <Accordion> / <AccordionItem>
  <Menu> / <MenuItem>
  <Form> / <Field> / <Submit>
```

---

## 19. Performance Optimization

### 19.1 React.memo

```jsx
// Memoize a component — skip re-render if props haven't changed
const ExpensiveList = React.memo(function ExpensiveList({ items, onSelect }) {
  return items.map(item => (
    <div key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </div>
  ));
});

// Custom comparison function
const Chart = React.memo(
  function Chart({ data, config }) { /* ... */ },
  (prevProps, nextProps) => {
    return prevProps.data === nextProps.data; // skip config comparison
  }
);
```

```
React.memo uses SHALLOW comparison (Object.is for each prop).
  — Primitive props: compares by value (fast)
  — Object/array/function props: compares by REFERENCE

Common mistake:
  function Parent() {
    const options = { sort: 'asc' };              // new object every render
    const handleClick = () => console.log('hi');   // new function every render
    return <MemoizedChild options={options} onClick={handleClick} />;
    // memo is useless — new references break shallow comparison
  }

Fix:
  function Parent() {
    const options = useMemo(() => ({ sort: 'asc' }), []);
    const handleClick = useCallback(() => console.log('hi'), []);
    return <MemoizedChild options={options} onClick={handleClick} />;
  }
```

### 19.2 Virtualization

```
Problem: rendering 10,000+ items in a list is slow.
Solution: only render items visible in the viewport.

Libraries:
  — react-window (lightweight, by Brian Vaughn)
  — react-virtuoso (auto-sizing, grouping)
  — @tanstack/react-virtual (headless, framework-agnostic)
```

```jsx
import { FixedSizeList } from 'react-window';

function VirtualList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>{items[index].name}</div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={35}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

### 19.3 Debouncing & Throttling

```jsx
function SearchInput() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  
  useEffect(() => {
    if (debouncedQuery) {
      searchAPI(debouncedQuery);
    }
  }, [debouncedQuery]);
  
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

### 19.4 Performance Checklist

```
1. Profile first — don't optimize prematurely
   — React DevTools Profiler (flamegraph, ranked)
   — Chrome DevTools Performance tab
   — React.Profiler component

2. Reduce unnecessary re-renders
   — React.memo for expensive components
   — useMemo / useCallback for stable references
   — Split context to reduce consumer scope
   — Move state down (colocate with where it's used)
   — Children-as-props pattern

3. Reduce render cost
   — Virtualize long lists
   — Lazy load heavy components (React.lazy + Suspense)
   — Debounce/throttle frequent updates
   — Avoid inline object/array/function creation in JSX

4. Reduce bundle size
   — Code splitting (dynamic import)
   — Tree shaking (named imports)
   — Analyze with webpack-bundle-analyzer / source-map-explorer

5. Optimize images & assets
   — Lazy load images (loading="lazy")
   — Use modern formats (WebP, AVIF)
   — Responsive images (srcSet)
```

---

## 20. Code Splitting & Lazy Loading

### 20.1 React.lazy & Suspense

```jsx
// Lazy load a component
const Dashboard = React.lazy(() => import('./Dashboard'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Dashboard />
    </Suspense>
  );
}
```

### 20.2 Route-based Splitting

```jsx
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### 20.3 Named Exports with lazy

```jsx
// React.lazy only supports default exports
// Workaround for named exports:
const MyComponent = lazy(() =>
  import('./MyModule').then(module => ({ default: module.MyComponent }))
);
```

### 20.4 Preloading

```jsx
// Preload a component before the user navigates
const Dashboard = lazy(() => import('./Dashboard'));

function NavLink() {
  const preload = () => import('./Dashboard'); // triggers chunk download
  
  return (
    <Link to="/dashboard" onMouseEnter={preload} onFocus={preload}>
      Dashboard
    </Link>
  );
}
```

---

## 21. Concurrent React & Suspense

### 21.1 What Is Concurrent React?

```
Concurrent React allows React to:
  — Prepare multiple versions of the UI simultaneously
  — Interrupt low-priority rendering for high-priority updates
  — Keep the old UI visible while rendering the new one

It is NOT "multi-threading" — React still uses one main thread.
Instead, it splits rendering into small units of work (fibers)
and yields control back to the browser between chunks.
```

### 21.2 Key Concurrent Features

```
Feature              API                     Purpose
────────────────────────────────────────────────────────────
Transitions          useTransition           Mark updates as non-urgent
                     startTransition
Deferred values      useDeferredValue        Defer re-rendering of a value
Suspense             <Suspense>              Show fallback while waiting
Streaming SSR        renderToPipeableStream   Stream HTML from server
Selective hydration  <Suspense> on server     Hydrate parts independently
```

### 21.3 Suspense for Data Fetching

```jsx
// Suspense works with frameworks that support it (Relay, Next.js, SWR)
// The data-fetching library "throws a promise" to signal loading

function ProfilePage({ userId }) {
  return (
    <Suspense fallback={<Skeleton />}>
      <ProfileDetails userId={userId} />
      <Suspense fallback={<PostsSkeleton />}>
        <ProfilePosts userId={userId} />
      </Suspense>
    </Suspense>
  );
}

// Nested Suspense boundaries allow progressive loading:
// 1. Show Skeleton immediately
// 2. When ProfileDetails loads, show it + PostsSkeleton
// 3. When ProfilePosts loads, show everything
```

### 21.4 use() Hook (React 19)

```jsx
// Read a promise or context during render
import { use } from 'react';

function Comments({ commentsPromise }) {
  const comments = use(commentsPromise); // suspends until resolved
  return comments.map(c => <Comment key={c.id} data={c} />);
}

// Can be called conditionally (unlike other hooks!)
function UserName({ userPromise, shouldLoad }) {
  if (!shouldLoad) return null;
  const user = use(userPromise);
  return <span>{user.name}</span>;
}
```

---

## 22. Server Components & SSR

### 22.1 Traditional SSR

```
Request → Server renders HTML → Send to client → Download JS → Hydrate

Problems:
  1. Must fetch ALL data before rendering anything
  2. Must load ALL JS before hydrating anything
  3. Must hydrate everything before anything is interactive
  → "All or nothing" waterfall
```

### 22.2 React Server Components (RSC)

```
Server Components:
  — Run ONLY on the server
  — Can directly access databases, file system, etc.
  — Never sent to the client as JavaScript (zero bundle impact)
  — Cannot have state, effects, or event handlers

Client Components:
  — Run on both server (SSR) and client
  — Can have interactivity (state, effects, handlers)
  — Marked with 'use client' directive
```

```jsx
// Server Component (default in Next.js App Router)
async function ProductList() {
  const products = await db.query('SELECT * FROM products');
  return (
    <div>
      {products.map(p => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}

// Client Component
'use client';
import { useState } from 'react';

function AddToCartButton({ productId }) {
  const [added, setAdded] = useState(false);
  
  return (
    <button onClick={() => {
      addToCart(productId);
      setAdded(true);
    }}>
      {added ? 'Added ✓' : 'Add to Cart'}
    </button>
  );
}
```

### 22.3 RSC Rules

```
Server Component can:
  ✓ Import and render Server Components
  ✓ Import and render Client Components
  ✓ Pass serializable props to Client Components
  ✓ Async/await for data fetching

Server Component CANNOT:
  ✗ Use useState, useEffect, or other client hooks
  ✗ Use browser-only APIs (DOM, window, localStorage)
  ✗ Pass functions as props to Client Components (not serializable)
  ✗ Use Context

Client Component can:
  ✓ Use hooks, state, effects, browser APIs
  ✓ Render other Client Components
  ✓ Receive Server Components as children (pre-rendered)

Client Component CANNOT:
  ✗ Import Server Components directly
  ✗ Use server-only APIs (db, fs)
```

### 22.4 Streaming SSR with Suspense

```jsx
// Server sends HTML progressively as components resolve
import { renderToPipeableStream } from 'react-dom/server';

app.get('/', (req, res) => {
  const { pipe } = renderToPipeableStream(
    <App />,
    {
      bootstrapScripts: ['/client.js'],
      onShellReady() {
        res.setHeader('Content-Type', 'text/html');
        pipe(res);
      },
    }
  );
});

// Client-side: selective hydration
// React hydrates <Suspense> boundaries independently
// User can interact with already-hydrated parts
// while other parts are still streaming / hydrating
```

---

## 23. State Management Patterns

### 23.1 Decision Framework

```
Local state (useState)
  └── Single component, simple values

Local + lifted state
  └── 2-3 components sharing state, close in tree

useReducer
  └── Complex state logic, many actions, state machine-like

Context + useReducer
  └── Medium apps, infrequent updates, theme/auth/locale

External store (Zustand / Redux / Jotai)
  └── Large apps, frequent updates, complex relationships,
      need middleware (logging, persistence, async)
```

### 23.2 useReducer + Context Pattern

```jsx
const initialState = {
  items: [],
  loading: false,
  error: null,
  filter: 'all',
};

function appReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return { ...state, loading: false, items: action.payload };
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    case 'SET_FILTER':
      return { ...state, filter: action.payload };
    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };
    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter(i => i.id !== action.payload) };
    default:
      throw new Error(`Unhandled action: ${action.type}`);
  }
}

const AppStateContext = createContext(null);
const AppDispatchContext = createContext(null);

function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return (
    <AppDispatchContext.Provider value={dispatch}>
      <AppStateContext.Provider value={state}>
        {children}
      </AppStateContext.Provider>
    </AppDispatchContext.Provider>
  );
}

function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error('useAppState must be used within AppProvider');
  return ctx;
}

function useAppDispatch() {
  const ctx = useContext(AppDispatchContext);
  if (!ctx) throw new Error('useAppDispatch must be used within AppProvider');
  return ctx;
}
```

### 23.3 Zustand (Minimal External Store)

```jsx
import { create } from 'zustand';

const useStore = create((set, get) => ({
  count: 0,
  items: [],
  
  increment: () => set(state => ({ count: state.count + 1 })),
  
  addItem: (item) => set(state => ({ items: [...state.items, item] })),
  
  removeItem: (id) => set(state => ({
    items: state.items.filter(i => i.id !== id)
  })),
  
  fetchItems: async () => {
    const response = await fetch('/api/items');
    const items = await response.json();
    set({ items });
  },
  
  getTotal: () => get().items.reduce((sum, i) => sum + i.price, 0),
}));

// Usage — components only re-render when their selected slice changes
function Counter() {
  const count = useStore(state => state.count);       // selector
  const increment = useStore(state => state.increment);
  return <button onClick={increment}>{count}</button>;
}

function ItemList() {
  const items = useStore(state => state.items);
  return items.map(i => <div key={i.id}>{i.name}</div>);
}
```

### 23.4 Redux Toolkit Pattern

```jsx
import { configureStore, createSlice } from '@reduxjs/toolkit';

const todosSlice = createSlice({
  name: 'todos',
  initialState: { items: [], filter: 'all' },
  reducers: {
    addTodo: (state, action) => {
      state.items.push(action.payload); // Immer allows "mutation" syntax
    },
    toggleTodo: (state, action) => {
      const todo = state.items.find(t => t.id === action.payload);
      if (todo) todo.completed = !todo.completed;
    },
    setFilter: (state, action) => {
      state.filter = action.payload;
    },
  },
});

export const { addTodo, toggleTodo, setFilter } = todosSlice.actions;

const store = configureStore({
  reducer: { todos: todosSlice.reducer },
});
```

---

## 24. React & TypeScript

### 24.1 Component Props

```tsx
// Basic props
interface ButtonProps {
  label: string;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

function Button({ label, variant = 'primary', disabled, onClick }: ButtonProps) {
  return (
    <button className={variant} disabled={disabled} onClick={onClick}>
      {label}
    </button>
  );
}

// Children
interface CardProps {
  title: string;
  children: React.ReactNode;   // anything renderable
}

// Extending HTML attributes
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

function Input({ label, error, ...rest }: InputProps) {
  return (
    <div>
      <label>{label}</label>
      <input {...rest} />
      {error && <span className="error">{error}</span>}
    </div>
  );
}
```

### 24.2 Hooks with TypeScript

```tsx
// useState — type inference or explicit
const [count, setCount] = useState(0);           // inferred as number
const [user, setUser] = useState<User | null>(null); // explicit

// useRef
const inputRef = useRef<HTMLInputElement>(null);  // DOM ref
const timerRef = useRef<number | null>(null);     // mutable ref

// useReducer
type Action =
  | { type: 'increment' }
  | { type: 'decrement' }
  | { type: 'set'; payload: number };

interface State {
  count: number;
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'increment': return { count: state.count + 1 };
    case 'decrement': return { count: state.count - 1 };
    case 'set': return { count: action.payload };
  }
}

// useContext
interface AuthContextValue {
  user: User | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
```

### 24.3 Generic Components

```tsx
// Generic list component
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map((item, index) => (
        <li key={keyExtractor(item)}>{renderItem(item, index)}</li>
      ))}
    </ul>
  );
}

// Usage
<List
  items={users}
  renderItem={(user) => <span>{user.name}</span>}
  keyExtractor={(user) => user.id}
/>
```

### 24.4 Discriminated Unions for Props

```tsx
// Different props based on a variant
type AlertProps =
  | { variant: 'success'; message: string }
  | { variant: 'error'; message: string; retry: () => void }
  | { variant: 'loading' };

function Alert(props: AlertProps) {
  switch (props.variant) {
    case 'success':
      return <div className="success">{props.message}</div>;
    case 'error':
      return (
        <div className="error">
          {props.message}
          <button onClick={props.retry}>Retry</button>
        </div>
      );
    case 'loading':
      return <Spinner />;
  }
}
```

### 24.5 Common React Types Reference

```tsx
// Event types
React.MouseEvent<HTMLButtonElement>
React.ChangeEvent<HTMLInputElement>
React.FormEvent<HTMLFormElement>
React.KeyboardEvent<HTMLInputElement>
React.FocusEvent<HTMLInputElement>
React.DragEvent<HTMLDivElement>

// Children types
React.ReactNode      // anything renderable (string, number, element, null, etc.)
React.ReactElement   // specifically a React element (<Component /> or JSX)
React.JSX.Element    // return type of JSX expressions

// Ref types
React.RefObject<HTMLDivElement>  // from useRef (readonly .current)
React.MutableRefObject<number>   // from useRef with non-null init
React.ForwardedRef<HTMLInputElement> // for forwardRef

// Style
React.CSSProperties  // inline style object

// Component types
React.FC<Props>      // function component type (includes children — controversial)
React.ComponentType<Props>  // class or function component
React.ElementType    // string ('div') or component type
```

---

## 25. Testing React Applications

### 25.1 Testing Philosophy

```
Testing Trophy (Kent C. Dodds):

          ┌─── E2E (few) ───┐           Cypress, Playwright
         ┌┤  Integration    ├┐          React Testing Library
        ┌┤│   (most tests)  │├┐
       ┌┤││   Unit tests    │││┐        Jest, Vitest
  ─────┤│││ Static Analysis ││││────    TypeScript, ESLint
       └┤││                 │││┘
        └┤│                 │├┘
         └┤                 ├┘
          └─────────────────┘

Priority: Integration > Unit > E2E > Static
Write tests that resemble how users use your software.
```

### 25.2 React Testing Library

```jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Rendering
test('renders greeting', () => {
  render(<Greeting name="Alice" />);
  expect(screen.getByText('Hello, Alice!')).toBeInTheDocument();
});

// Queries (priority order):
// 1. getByRole       — accessible role (button, heading, textbox)
// 2. getByLabelText  — form fields by label
// 3. getByPlaceholderText
// 4. getByText       — visible text content
// 5. getByDisplayValue
// 6. getByAltText    — images
// 7. getByTitle
// 8. getByTestId     — LAST RESORT

// User interactions
test('increments counter', async () => {
  const user = userEvent.setup();
  render(<Counter />);
  
  const button = screen.getByRole('button', { name: /increment/i });
  await user.click(button);
  
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});

// Async operations
test('loads user data', async () => {
  render(<UserProfile userId="123" />);
  
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
  
  await waitFor(() => {
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });
});

// Testing forms
test('submits form with values', async () => {
  const handleSubmit = jest.fn();
  const user = userEvent.setup();
  render(<LoginForm onSubmit={handleSubmit} />);
  
  await user.type(screen.getByLabelText(/email/i), 'test@example.com');
  await user.type(screen.getByLabelText(/password/i), 'password123');
  await user.click(screen.getByRole('button', { name: /sign in/i }));
  
  expect(handleSubmit).toHaveBeenCalledWith({
    email: 'test@example.com',
    password: 'password123',
  });
});
```

### 25.3 Testing Hooks

```jsx
import { renderHook, act } from '@testing-library/react';

test('useCounter', () => {
  const { result } = renderHook(() => useCounter(0));
  
  expect(result.current.count).toBe(0);
  
  act(() => {
    result.current.increment();
  });
  
  expect(result.current.count).toBe(1);
});

// With wrapper (for context providers)
test('useAuth', () => {
  const wrapper = ({ children }) => (
    <AuthProvider>{children}</AuthProvider>
  );
  
  const { result } = renderHook(() => useAuth(), { wrapper });
  expect(result.current.user).toBeNull();
});
```

### 25.4 Mocking

```jsx
// Mock a module
jest.mock('./api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ name: 'Alice' }),
}));

// Mock a component
jest.mock('./HeavyChart', () => {
  return function MockChart(props) {
    return <div data-testid="chart">{props.title}</div>;
  };
});

// Mock context
function renderWithAuth(ui, { user = null } = {}) {
  return render(
    <AuthContext.Provider value={{ user, login: jest.fn(), logout: jest.fn() }}>
      {ui}
    </AuthContext.Provider>
  );
}
```

---

## 26. React Security

### 26.1 XSS Protection

```
React auto-escapes string values rendered in JSX:
  <div>{userInput}</div>  → safe (strings are escaped)

Dangerous:
  <div dangerouslySetInnerHTML={{ __html: userInput }} />
  → XSS vulnerability if userInput is not sanitized

  <a href={userProvidedUrl}>Link</a>
  → XSS if url is "javascript:alert('xss')"
  → Validate: url.startsWith('https://') || url.startsWith('/')
```

### 26.2 Common Vulnerabilities

```
1. dangerouslySetInnerHTML — sanitize with DOMPurify
2. href/src with user input — validate protocol
3. Server-side rendering — escape data injected into HTML
4. JSON in <script> — use serialize-javascript, not JSON.stringify
5. Dependency vulnerabilities — npm audit, Dependabot
6. Sensitive data in client code — never store secrets in React
```

```jsx
// Safe HTML rendering
import DOMPurify from 'dompurify';

function SafeHTML({ html }) {
  return (
    <div dangerouslySetInnerHTML={{
      __html: DOMPurify.sanitize(html)
    }} />
  );
}

// Safe URL
function SafeLink({ url, children }) {
  const isSafe = url.startsWith('https://') || url.startsWith('/');
  return isSafe ? <a href={url}>{children}</a> : <span>{children}</span>;
}
```

### 26.3 $$typeof — React's Built-in Protection

```
Every React element has a $$typeof property:
  $$typeof: Symbol.for('react.element')

Why? Prevents JSON injection attacks:
  — Attacker stores malicious React element as JSON in database
  — JSON cannot contain Symbols
  — React checks $$typeof before rendering — rejects non-Symbol values
```

---

## 27. React Design Patterns — Catalog

### 27.1 Container / Presentational

```
Container: handles data fetching, state, logic
Presentational: receives props, renders UI

Modern alternative: custom hooks replace containers
```

```jsx
// Custom hook replaces container
function useUserData(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetchUser(userId).then(setUser).finally(() => setLoading(false));
  }, [userId]);
  return { user, loading };
}

function UserProfile({ userId }) {
  const { user, loading } = useUserData(userId);
  if (loading) return <Spinner />;
  return <ProfileCard user={user} />;
}
```

### 27.2 Controlled vs. Uncontrolled Components

```jsx
// Controlled — React state is the single source of truth
function ControlledInput() {
  const [value, setValue] = useState('');
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}

// Uncontrolled — DOM is the source of truth
function UncontrolledInput() {
  const inputRef = useRef();
  const handleSubmit = () => console.log(inputRef.current.value);
  return <input ref={inputRef} defaultValue="" />;
}
```

```
Controlled:
  ✓ Validation on every keystroke
  ✓ Conditional rendering based on input
  ✓ Enforcing input format
  ✓ Dynamic inputs

Uncontrolled:
  ✓ Simple forms with no complex validation
  ✓ File inputs (<input type="file" /> must be uncontrolled)
  ✓ Integrating non-React code
```

### 27.3 State Machine Pattern

```jsx
// Explicit states prevent impossible states
const STATES = {
  idle: 'idle',
  loading: 'loading',
  success: 'success',
  error: 'error',
};

function fetchReducer(state, action) {
  switch (state.status) {
    case STATES.idle:
      if (action.type === 'FETCH') return { status: STATES.loading };
      break;
    case STATES.loading:
      if (action.type === 'SUCCESS') return { status: STATES.success, data: action.data };
      if (action.type === 'ERROR') return { status: STATES.error, error: action.error };
      break;
    case STATES.success:
    case STATES.error:
      if (action.type === 'FETCH') return { status: STATES.loading };
      if (action.type === 'RESET') return { status: STATES.idle };
      break;
  }
  return state;
}
```

### 27.4 Provider Pattern

```jsx
// Combine multiple providers cleanly
function AppProviders({ children }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

// Or use a compose utility
function composeProviders(...providers) {
  return ({ children }) =>
    providers.reduceRight(
      (acc, Provider) => <Provider>{acc}</Provider>,
      children
    );
}

const AppProviders = composeProviders(
  ThemeProvider,
  AuthProvider,
  NotificationProvider
);
```

### 27.5 Slots Pattern

```jsx
// Named slots via props (like Vue slots)
function Layout({ header, sidebar, content, footer }) {
  return (
    <div className="layout">
      <header>{header}</header>
      <div className="body">
        <aside>{sidebar}</aside>
        <main>{content}</main>
      </div>
      <footer>{footer}</footer>
    </div>
  );
}

<Layout
  header={<NavBar />}
  sidebar={<SideMenu />}
  content={<Dashboard />}
  footer={<FooterLinks />}
/>
```

### 27.6 Headless Component Pattern

```jsx
// Logic-only hook / component — no UI, consumer provides rendering
function useDropdown(items) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const getToggleProps = () => ({
    onClick: () => setIsOpen(!isOpen),
    'aria-expanded': isOpen,
    'aria-haspopup': 'listbox',
  });

  const getMenuProps = () => ({
    role: 'listbox',
    hidden: !isOpen,
  });

  const getItemProps = (index) => ({
    role: 'option',
    'aria-selected': index === selectedIndex,
    onClick: () => {
      setSelectedIndex(index);
      setIsOpen(false);
    },
  });

  return {
    isOpen,
    selectedItem: items[selectedIndex],
    getToggleProps,
    getMenuProps,
    getItemProps,
  };
}

// Consumer provides all the UI
function CityPicker({ cities }) {
  const { isOpen, selectedItem, getToggleProps, getMenuProps, getItemProps } =
    useDropdown(cities);

  return (
    <div>
      <button {...getToggleProps()}>{selectedItem?.name ?? 'Select city'}</button>
      <ul {...getMenuProps()}>
        {isOpen && cities.map((city, i) => (
          <li key={city.id} {...getItemProps(i)}>{city.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 28. React Internals — Interview Deep Dives

### 28.1 How Does setState Work?

```
1. Component calls setState(newValue)
2. React creates an update object { action: newValue, next: null }
3. Update is enqueued onto the fiber's updateQueue (linked list)
4. React schedules a re-render (via the scheduler)
5. During render phase:
   a. React walks the fiber tree (beginWork)
   b. Processes the update queue for the fiber
   c. Computes new state by applying updates in order
   d. Calls the component function with new state
   e. Diffs old vs new children (reconciliation)
6. During commit phase:
   a. Apply DOM mutations
   b. Run layout effects
   c. Schedule passive effects
```

### 28.2 How Does useEffect Work Internally?

```
1. During render: React sees useEffect call, stores the effect on the fiber
   — effect = { tag, create, destroy, deps, next }
   — effect is added to fiber's updateQueue (effect list)

2. During commit (layout phase): effects are scheduled (not run)

3. After paint: React runs pending effects asynchronously
   — If deps changed (or first mount):
     a. Run the DESTROY function from previous render (cleanup)
     b. Run the CREATE function (new effect)
     c. Store new destroy function for next cleanup

4. On unmount: run destroy for all effects
```

### 28.3 How Does React.memo Work?

```
1. React.memo wraps a component with a comparison check
2. Before rendering, React compares prev props vs next props
3. Default: shallow comparison (Object.is for each prop key)
4. Custom: uses the provided areEqual(prevProps, nextProps) function
5. If props are "equal" → return true → SKIP render (reuse previous fiber)
6. If props differ → return false → render as normal

IMPORTANT:
  — React.memo only checks PROPS, not state or context
  — If the component uses useContext, it re-renders on context change
    regardless of React.memo
  — React.memo is a performance hint, not a guarantee
    (React may still re-render in some cases)
```

### 28.4 How Does Key-based Reconciliation Work?

```
Old list: [A, B, C, D]    keys: [1, 2, 3, 4]
New list: [D, A, B, C]    keys: [4, 1, 2, 3]

Step 1: Build map from old keys → old fibers
  { 1: fiberA, 2: fiberB, 3: fiberC, 4: fiberD }

Step 2: Walk new children, look up by key
  D → found fiber4 → reuse (move)
  A → found fiber1 → reuse (move)
  B → found fiber2 → reuse (move)
  C → found fiber3 → reuse (no move needed — already last)

Step 3: Delete any old fibers not found in new list

Result: 3 DOM moves, 0 creates, 0 deletes
Without keys: React compares by index → 4 updates (more DOM work)
```

### 28.5 Hydration

```
Hydration = attaching React event handlers to server-rendered HTML
  1. Server renders HTML string (or stream)
  2. Browser displays HTML immediately (fast First Paint)
  3. Client downloads React JS bundle
  4. React calls hydrateRoot() instead of createRoot()
  5. React walks the existing DOM and the virtual tree simultaneously
  6. Instead of creating new DOM nodes, React ADOPTS existing ones
  7. Attaches event handlers and refs
  8. If mismatch found → warning in dev, client wins in prod

Hydration errors (common interview topic):
  — Server and client render different content
  — Causes: Date.now(), Math.random(), browser-only APIs
  — Fix: useEffect for client-only values, suppressHydrationWarning
```

### 28.6 Event System

```
React 17+ attaches event listeners to the ROOT element (not document).

Event Flow:
  1. Native event fires on DOM element
  2. Event bubbles to React root
  3. React creates a SyntheticEvent (cross-browser wrapper)
  4. React dispatches to the correct fiber's handler
  5. SyntheticEvent pools are NOT used anymore (React 17+)

SyntheticEvent:
  — Wraps the native event
  — Same interface across browsers
  — event.nativeEvent to access the real DOM event
  — event.stopPropagation() stops React propagation
  — event.preventDefault() works as expected

Capture phase:
  onClickCapture instead of onClick
```

---

## 29. Common FAANG Interview Questions

### 29.1 Conceptual Questions

```
Q: What is the virtual DOM and why does React use it?
A: An in-memory representation of the real DOM. React diffs old vs new
   virtual trees to compute minimal DOM mutations. This enables declarative
   programming while maintaining performance.

Q: Explain React's reconciliation algorithm.
A: O(n) heuristic diffing:
   1. Different element types → unmount old, mount new
   2. Same DOM type → update changed attributes
   3. Same component type → re-render with new props
   4. Lists use keys to match children across renders

Q: What is the difference between useEffect and useLayoutEffect?
A: useEffect runs AFTER browser paint (async, non-blocking).
   useLayoutEffect runs BEFORE paint (sync, blocking).
   Use useLayoutEffect for DOM measurements to prevent visual flicker.

Q: How does React batch state updates?
A: React 18+ batches ALL setState calls (event handlers, promises,
   timeouts) into a single re-render. Use flushSync to opt out.

Q: What is a closure bug with hooks?
A: When a hook callback captures a stale value from a previous render
   because the dependency array is missing that value.

Q: Why can't hooks be called conditionally?
A: React tracks hooks by their call order (linked list). Conditional
   calls change the order, causing hooks to map to wrong state.

Q: What is React Fiber?
A: React's internal reconciliation engine that splits rendering into
   interruptible units of work. Enables concurrent features like
   useTransition and Suspense.

Q: What causes unnecessary re-renders?
A: Parent re-rendering (cascading), new object/function references as
   props, context changes, and missing memoization.

Q: When would you NOT use React.memo?
A: When the component is cheap to render, props change almost every
   render, or the component receives children (always new reference).
```

### 29.2 Coding Challenges

```
Challenge 1: Implement useDebounce hook
Challenge 2: Build an autocomplete/typeahead component
Challenge 3: Implement infinite scroll with IntersectionObserver
Challenge 4: Build a modal with focus trap and portal
Challenge 5: Create a form with validation (controlled components)
Challenge 6: Implement a data table with sorting, filtering, pagination
Challenge 7: Build a drag-and-drop interface
Challenge 8: Implement undo/redo with useReducer
Challenge 9: Build a virtualized list from scratch
Challenge 10: Create a theme system with context and CSS variables
```

### 29.3 Implement Undo/Redo

```jsx
function undoReducer(state, action) {
  const { past, present, future } = state;
  
  switch (action.type) {
    case 'SET': {
      return {
        past: [...past, present],
        present: action.value,
        future: [],
      };
    }
    case 'UNDO': {
      if (past.length === 0) return state;
      const previous = past[past.length - 1];
      return {
        past: past.slice(0, -1),
        present: previous,
        future: [present, ...future],
      };
    }
    case 'REDO': {
      if (future.length === 0) return state;
      const next = future[0];
      return {
        past: [...past, present],
        present: next,
        future: future.slice(1),
      };
    }
    default:
      return state;
  }
}

function useUndoRedo(initialValue) {
  const [state, dispatch] = useReducer(undoReducer, {
    past: [],
    present: initialValue,
    future: [],
  });
  
  return {
    value: state.present,
    canUndo: state.past.length > 0,
    canRedo: state.future.length > 0,
    set: (value) => dispatch({ type: 'SET', value }),
    undo: () => dispatch({ type: 'UNDO' }),
    redo: () => dispatch({ type: 'REDO' }),
  };
}
```

### 29.4 Implement Throttled Resize Observer

```jsx
function useResizeObserver(ref, delay = 100) {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    let rafId = null;
    let lastTime = 0;
    
    const observer = new ResizeObserver((entries) => {
      const now = Date.now();
      if (now - lastTime < delay) {
        cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
          lastTime = Date.now();
          const { width, height } = entries[0].contentRect;
          setDimensions({ width, height });
        });
      } else {
        lastTime = now;
        const { width, height } = entries[0].contentRect;
        setDimensions({ width, height });
      }
    });
    
    observer.observe(element);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(rafId);
    };
  }, [ref, delay]);
  
  return dimensions;
}
```

### 29.5 Implement a Focus Trap (Accessibility)

```jsx
function useFocusTrap(ref) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    const focusableSelector = [
      'a[href]', 'button:not([disabled])', 'textarea:not([disabled])',
      'input:not([disabled])', 'select:not([disabled])', '[tabindex]:not([tabindex="-1"])',
    ].join(', ');
    
    const previouslyFocused = document.activeElement;
    
    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;
      
      const focusable = element.querySelectorAll(focusableSelector);
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    
    element.addEventListener('keydown', handleKeyDown);
    const focusable = element.querySelectorAll(focusableSelector);
    if (focusable.length) focusable[0].focus();
    
    return () => {
      element.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [ref]);
}
```

---

## 30. Cheatsheet

### Quick Reference — Hooks

```
Hook                  Purpose                              Common Pitfall
──────────────────────────────────────────────────────────────────────────────
useState              Local state                          Mutating state directly
useEffect             Side effects after render            Missing deps / race conditions
useLayoutEffect       Side effects before paint            Blocking the paint
useReducer            Complex state logic                  Forgetting to return new object
useRef                Mutable value / DOM ref              Expecting re-render on change
useMemo               Cache expensive computation          Over-memoizing cheap values
useCallback           Cache function reference             Missing it where React.memo expects it
useContext            Read context value                   Not splitting contexts
useId                 Stable unique IDs                    Using for list keys
useTransition         Mark updates as non-urgent           Using for urgent UI updates
useDeferredValue      Defer a value's update               Not combining with useMemo
useSyncExternalStore  Subscribe to external store          Inconsistent snapshot
useImperativeHandle   Customize ref value                  Exposing too much
useInsertionEffect    Inject styles before DOM mutations   Using outside CSS-in-JS lib
```

### Quick Reference — Optimization

```
Technique                When to Use
──────────────────────────────────────────────────────────────────────────
React.memo              Expensive component with stable props
useMemo                 Expensive derived computation
useCallback             Function prop to memoized child
Children-as-props       Avoid re-rendering static subtrees
Move state down         Colocate state with consumer
Lazy loading            Large components / route-based splitting
Virtualization          10,000+ item lists
Debounce/throttle       High-frequency input events
Web Workers             CPU-heavy calculations off main thread
```

### Quick Reference — When to Use What

```
Need                             Tool
──────────────────────────────────────────────────────────────────────────
Simple local state               useState
Complex/related state            useReducer
Share across few components      Lift state up + props
Share across many components     Context (if infrequent updates)
Global state, frequent updates   Zustand / Redux / Jotai
Server data                      TanStack Query / SWR
Forms                            React Hook Form / Formik
Routing                          React Router / TanStack Router
SSR + RSC                        Next.js / Remix
Styling                          Tailwind / CSS Modules / styled-components
Animation                        Framer Motion / React Spring
Testing                          Vitest + React Testing Library
```

### Key Interview Mental Models

```
1. React rendering is a PURE FUNCTION: state + props → UI
2. State is immutable — always create new references
3. Effects are for SYNCHRONIZATION, not lifecycle events
4. Hooks are ordered calls — position matters, not name
5. Keys preserve identity across renders
6. Memoization is an optimization, not a correctness tool
7. Context is for dependency injection, not state management
8. Server Components separate data fetching from interactivity
9. Concurrent React = interruptible rendering + priority scheduling
10. The commit phase is synchronous — the render phase can be interrupted
```

---

*Last updated: April 2026*
