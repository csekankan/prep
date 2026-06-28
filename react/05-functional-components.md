# Functional Components -- Interview Deep Dive

---

## 1. Function vs Class Components

### Class Component

```jsx
class Greeting extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }

  handleClick = () => {
    this.setState(prev => ({ count: prev.count + 1 }));
  };

  render() {
    return (
      <div>
        <h1>Hello, {this.props.name}</h1>
        <button onClick={this.handleClick}>Count: {this.state.count}</button>
      </div>
    );
  }
}
```

### Functional Component (Equivalent)

```jsx
function Greeting({ name }) {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>Hello, {name}</h1>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
    </div>
  );
}
```

### Comparison Table

| Aspect | Class | Functional |
|--------|-------|------------|
| Syntax | ES6 class, extends React.Component | Plain function |
| State | `this.state` + `this.setState` | `useState` hook |
| Side effects | Lifecycle methods | `useEffect` hook |
| `this` binding | Must bind methods or use arrow fields | No `this` issues |
| Performance | Slightly heavier (instance creation) | Slightly lighter |
| Readability | More boilerplate | More concise |
| Hooks support | No | Yes |
| Error boundaries | Yes (`componentDidCatch`) | Not yet (as of React 18) |
| Ref access | `createRef` or callback ref | `useRef` |
| `shouldComponentUpdate` | Yes (or extend PureComponent) | `React.memo` |

**Interview note**: As of React 18, there is one thing class components can do that functional components cannot: **error boundaries** (via `componentDidCatch` and `getDerivedStateFromError`). However, libraries like `react-error-boundary` provide a wrapper.

---

## 2. Closure Behavior in Functional Components

This is perhaps the most important concept for interviews involving functional components. Every render creates a new closure.

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    console.log(count); // Captures `count` from THIS render
  };

  return <button onClick={handleClick}>Count: {count}</button>;
}
```

Each time `Counter` renders, a new `handleClick` function is created that closes over the `count` value from that specific render. This is fundamentally different from class components, where `this.state.count` always points to the latest value.

### Render 1: count = 0

```
handleClick closes over count = 0
```

### Render 2: count = 1

```
handleClick closes over count = 1
(the old handleClick from render 1 still sees count = 0)
```

---

## 3. The Stale Closure Problem

A stale closure occurs when a function captures an old value from a previous render and continues to use it.

### Classic Example: setTimeout

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setTimeout(() => {
      console.log("Count:", count);
    }, 3000);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <button onClick={handleClick}>Log after 3s</button>
    </div>
  );
}
```

**Steps**:
1. Click "+" three times (count = 3)
2. Click "Log after 3s"
3. Click "+" two more times (count = 5)
4. After 3 seconds, the console logs...

**Answer**: `Count: 3`. The `handleClick` function was created during the render where `count` was 3. The `setTimeout` callback captured that closure. Even though `count` is now 5, the old closure still sees 3.

### How to Get the Latest Value in a Closure

**Method 1: useRef**

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);
  countRef.current = count; // Always sync the ref

  const handleClick = () => {
    setTimeout(() => {
      console.log("Count:", countRef.current); // Always latest
    }, 3000);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <button onClick={handleClick}>Log after 3s</button>
    </div>
  );
}
```

**Method 2: Functional updater (for setState only)**

```jsx
const handleClick = () => {
  setCount(currentCount => {
    console.log("Count:", currentCount); // Latest value
    return currentCount; // Return same value (no state change)
  });
};
```

### Stale Closure in useEffect

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1); // BUG: count is always 0 (stale closure)
    }, 1000);
    return () => clearInterval(id);
  }, []); // Empty deps = runs once, captures count=0

  return <p>Count: {count}</p>;
}
```

**What happens**: The counter increments to 1 and stops. `count` is captured as `0` in the closure. Every tick calls `setCount(0 + 1)`, which always sets count to 1.

**Fix**: Use functional updater:

```jsx
useEffect(() => {
  const id = setInterval(() => {
    setCount(c => c + 1); // Uses latest count
  }, 1000);
  return () => clearInterval(id);
}, []);
```

---

## 4. Rules of Hooks

### Rule 1: Only Call Hooks at the Top Level

Do NOT call hooks inside loops, conditions, or nested functions.

```jsx
// BAD
function Form({ showName }) {
  if (showName) {
    const [name, setName] = useState(""); // Conditional hook!
  }
  const [email, setEmail] = useState("");
}

// GOOD
function Form({ showName }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  return (
    <div>
      {showName && <input value={name} onChange={e => setName(e.target.value)} />}
      <input value={email} onChange={e => setEmail(e.target.value)} />
    </div>
  );
}
```

### Why Order Matters

React identifies hooks by their **call order** (position in the call sequence), not by name. React stores hook state in an array-like structure internally:

```
Render 1:
  Hook 0: useState("") -> name
  Hook 1: useState("") -> email

Render 2 (showName = false, conditional hook skipped):
  Hook 0: useState("") -> ???
  // React expects this to be `name`, but now it might be `email`
  // Hook state is mismatched!
```

If a hook is conditionally skipped, all subsequent hooks shift position, causing state to be matched to the wrong hook.

### Rule 2: Only Call Hooks from React Functions

Hooks can only be called from:
- React function components
- Custom hooks (functions whose names start with `use`)

They cannot be called from:
- Regular JavaScript functions
- Class components
- Event handlers (unless inside a component or custom hook's scope)

### ESLint Plugin

The `eslint-plugin-react-hooks` package enforces these rules:

```json
{
  "plugins": ["react-hooks"],
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

---

## 5. Component Lifecycle Mapping: Class to Hooks

### Mounting

| Class | Hooks equivalent |
|-------|-----------------|
| `constructor` | Function body + `useState` initializer |
| `componentDidMount` | `useEffect(() => { ... }, [])` |
| `getDerivedStateFromProps` | Update state during render (rare) |

### Updating

| Class | Hooks equivalent |
|-------|-----------------|
| `componentDidUpdate` | `useEffect(() => { ... }, [deps])` |
| `shouldComponentUpdate` | `React.memo` |
| `getSnapshotBeforeUpdate` | No direct equivalent (use `useLayoutEffect` for some cases) |

### Unmounting

| Class | Hooks equivalent |
|-------|-----------------|
| `componentWillUnmount` | `useEffect(() => { return () => { cleanup }; }, [])` |

### Important Mental Model Shift

**Class components think in lifecycle**: "What should happen when the component mounts, updates, or unmounts?"

**Hooks think in synchronization**: "What external systems does this component synchronize with, and what values does that synchronization depend on?"

```jsx
// Class: "When the component mounts, start a subscription. When it unmounts, stop it."
componentDidMount() {
  this.subscription = dataSource.subscribe(this.handleChange);
}
componentWillUnmount() {
  this.subscription.unsubscribe();
}

// Hooks: "Synchronize with dataSource. Re-sync when dataSource changes."
useEffect(() => {
  const subscription = dataSource.subscribe(handleChange);
  return () => subscription.unsubscribe();
}, [dataSource]);
```

The hooks version automatically handles the case where `dataSource` changes (unsubscribe from old, subscribe to new). The class version requires `componentDidUpdate` to handle that.

---

## 6. Pure Components and React.memo

### Class: PureComponent

```jsx
class MyComponent extends React.PureComponent {
  render() {
    return <div>{this.props.name}</div>;
  }
}
```

`PureComponent` implements `shouldComponentUpdate` with a **shallow comparison** of props and state.

### Functional: React.memo

```jsx
const MyComponent = React.memo(function MyComponent({ name }) {
  return <div>{name}</div>;
});
```

`React.memo` wraps a functional component and skips re-rendering if props have not changed (shallow comparison).

### Custom Comparison

```jsx
const MyComponent = React.memo(
  function MyComponent({ user }) {
    return <div>{user.name}</div>;
  },
  (prevProps, nextProps) => {
    return prevProps.user.id === nextProps.user.id;
  }
);
```

The second argument is a comparison function. Return `true` to **skip** the re-render (opposite of `shouldComponentUpdate`).

### When React.memo Fails

```jsx
const Parent = () => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <MemoizedChild onClick={() => console.log("click")} items={[1, 2, 3]} />
    </div>
  );
};

const MemoizedChild = React.memo(function Child({ onClick, items }) {
  console.log("Child rendered");
  return <button onClick={onClick}>Click ({items.length})</button>;
});
```

**Answer**: `MemoizedChild` re-renders on every parent re-render despite `React.memo`. Both `onClick` (inline arrow function) and `items` (inline array literal) create **new references** on every render. Shallow comparison detects them as changed.

**Fix**:

```jsx
const Parent = () => {
  const [count, setCount] = useState(0);
  const handleClick = useCallback(() => console.log("click"), []);
  const items = useMemo(() => [1, 2, 3], []);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <MemoizedChild onClick={handleClick} items={items} />
    </div>
  );
};
```

---

## 7. Higher-Order Components (HOCs)

A HOC is a function that takes a component and returns a new enhanced component.

```jsx
function withLogger(WrappedComponent) {
  return function EnhancedComponent(props) {
    useEffect(() => {
      console.log(`${WrappedComponent.name} mounted`);
      return () => console.log(`${WrappedComponent.name} unmounted`);
    }, []);

    return <WrappedComponent {...props} />;
  };
}

const LoggedButton = withLogger(Button);
```

### HOC Pitfalls

1. **Wrapper hell**: Multiple HOCs create deeply nested component trees.

```jsx
export default withRouter(withAuth(withTheme(withLogger(MyComponent))));
```

2. **Props collision**: If two HOCs inject a prop with the same name, one overwrites the other.

3. **Ref forwarding**: HOCs do not forward refs by default. You must use `React.forwardRef`.

4. **Static methods lost**: Static methods on the wrapped component are not copied to the HOC. Use `hoist-non-react-statics`.

5. **Display name**: Wrap the component's display name for better DevTools experience:

```jsx
function withLogger(WrappedComponent) {
  function Enhanced(props) { /* ... */ }
  Enhanced.displayName = `withLogger(${WrappedComponent.displayName || WrappedComponent.name})`;
  return Enhanced;
}
```

---

## 8. Render Props to Hooks Migration

### Before: Render Prop

```jsx
function MousePosition({ children }) {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  return (
    <div onMouseMove={(e) => setPos({ x: e.clientX, y: e.clientY })}>
      {children(pos)}
    </div>
  );
}

function App() {
  return (
    <MousePosition>
      {({ x, y }) => <p>Mouse: ({x}, {y})</p>}
    </MousePosition>
  );
}
```

### After: Custom Hook

```jsx
function useMousePosition() {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => setPos({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", handler);
    return () => window.removeEventListener("mousemove", handler);
  }, []);

  return pos;
}

function App() {
  const { x, y } = useMousePosition();
  return <p>Mouse: ({x}, {y})</p>;
}
```

### Why Hooks Are Better Here

1. **No wrapper nesting**: No extra `<MousePosition>` component in the tree.
2. **No render function indirection**: Cleaner, more readable code.
3. **Composable**: Multiple hooks can be used together without nesting render props inside each other.
4. **Testable**: Hooks can be tested with `renderHook` from React Testing Library.

### When Render Props Are Still Useful

- When the behavior provider also needs to **render something** (e.g., a wrapper `<div>` with event handlers).
- When you need **different UI** for the same behavior in different places within the same component.

---

## 9. When Do Functional Components Re-Render?

A functional component re-renders when:

1. **Its parent re-renders** (regardless of whether props changed)
2. **Its state changes** (via `useState` or `useReducer` setter)
3. **A context it consumes changes** (via `useContext`)

A functional component does NOT re-render when:
- Its props change but the parent does not re-render (this scenario is impossible -- props can only change when the parent re-renders)
- A ref changes (`useRef` does not trigger re-renders)
- It is wrapped in `React.memo` and props are shallowly equal

### Output-Based Question: Re-Render Cascade

```jsx
function App() {
  const [count, setCount] = useState(0);
  console.log("App renders");

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <Parent />
    </div>
  );
}

function Parent() {
  console.log("Parent renders");
  return <Child />;
}

function Child() {
  console.log("Child renders");
  return <p>Hello</p>;
}
```

**What logs when the button is clicked?**

**Answer**:
```
App renders
Parent renders
Child renders
```

All three log on every click, even though `Parent` and `Child` receive no props and have no state. **Re-renders cascade from parent to all descendants by default.** This is React's default behavior. To prevent it, wrap `Parent` in `React.memo`.

---

## 10. Output-Based Interview Questions

### Question 1: Closure Captures Render Value

```jsx
function ProfilePage({ userId }) {
  const showMessage = () => {
    alert("Followed user " + userId);
  };

  const handleClick = () => {
    setTimeout(showMessage, 3000);
  };

  return <button onClick={handleClick}>Follow</button>;
}
```

**Scenario**: userId is "Alice". User clicks Follow. Before 3 seconds pass, the parent changes userId to "Bob".

**What does the alert show?**

**Answer**: "Followed user Alice". The `showMessage` function was created during the render where `userId` was "Alice". The `setTimeout` callback captured that closure. The fact that the component later re-rendered with "Bob" does not affect the already-captured closure.

**Contrast with class component**: In a class component using `this.props.userId`, the alert would show "Bob" because `this.props` always points to the latest props.

### Question 2: Multiple useState Hooks

```jsx
function App() {
  const [a, setA] = useState(1);
  const [b, setB] = useState(2);

  const handleClick = () => {
    setA(10);
    setB(20);
  };

  console.log("Render: a =", a, "b =", b);
  return <button onClick={handleClick}>Update</button>;
}
```

**What logs when the button is clicked?**

**Answer**:
```
Render: a = 10 b = 20
```

React 18 batches all state updates within event handlers (and also inside `setTimeout`, promises, etc.). Both `setA` and `setB` are batched into a single re-render. The component renders once with both new values.

### Question 3: useState with Same Value

```jsx
function App() {
  const [count, setCount] = useState(0);
  console.log("Render");

  return <button onClick={() => setCount(0)}>Click</button>;
}
```

**How many times does "Render" log after clicking the button?**

**Answer**: After initial render, clicking the button **may** cause one additional render, but React will bail out early on subsequent clicks. React uses Object.is to compare the new state with the current state. Since `0 === 0`, React skips the re-render. However, the first click after the initial render may still trigger a render as part of React's eager bailout optimization. After that, no more renders occur.

### Question 4: useRef Does Not Cause Re-Render

```jsx
function App() {
  const countRef = useRef(0);
  console.log("Render, ref:", countRef.current);

  const handleClick = () => {
    countRef.current += 1;
    console.log("Clicked, ref:", countRef.current);
  };

  return <button onClick={handleClick}>Click ({countRef.current})</button>;
}
```

**What happens after 3 clicks?**

**Answer**: The console logs:
```
Render, ref: 0         // Initial render
Clicked, ref: 1        // Click 1
Clicked, ref: 2        // Click 2
Clicked, ref: 3        // Click 3
```

The button always shows "Click (0)" because `countRef.current` is updated, but **no re-render** is triggered. The screen never reflects the updated ref value. The ref is a mutable container that persists across renders but does not participate in React's rendering cycle.

### Question 5: Hooks Order Violation

```jsx
function App({ showExtra }) {
  const [name, setName] = useState("Alice");

  if (showExtra) {
    const [extra, setExtra] = useState(""); // Conditional hook!
  }

  const [age, setAge] = useState(25);

  return <p>{name}, {age}</p>;
}
```

**What happens when `showExtra` changes from `true` to `false`?**

**Answer**: React throws an error: "Rendered fewer hooks than expected." On the first render (showExtra = true), React sees 3 hooks. On the second render (showExtra = false), React sees 2 hooks. The hook count mismatch violates the Rules of Hooks and causes a runtime error.

---

## 11. Advanced: Closures and Event Handlers

### Why Does This Work Differently from Class Components?

```jsx
// Functional: each render captures its own props/state
function Greeting({ name }) {
  const handleClick = () => alert(name);
  return <button onClick={handleClick}>Greet</button>;
}

// Class: this.props always points to the latest
class Greeting extends React.Component {
  handleClick = () => alert(this.props.name);
  render() {
    return <button onClick={this.handleClick}>Greet</button>;
  }
}
```

If `name` changes from "Alice" to "Bob" between the click and the alert:
- **Functional**: alerts "Alice" (closure captured "Alice")
- **Class**: alerts "Bob" (`this.props` is mutable, points to latest)

This is a **feature** of functional components, not a bug. Each render is a snapshot.

---

## 12. Component Design Patterns

### Container / Presentational (Historical)

```jsx
// Container (logic)
function UserListContainer() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    fetch("/api/users").then(r => r.json()).then(setUsers);
  }, []);
  return <UserList users={users} />;
}

// Presentational (UI only)
function UserList({ users }) {
  return (
    <ul>
      {users.map(u => <li key={u.id}>{u.name}</li>)}
    </ul>
  );
}
```

This pattern is less necessary with hooks (you can use a custom hook instead of a container), but the separation of logic and UI is still a good principle.

### Compound Components

```jsx
function Tabs({ children }) {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <TabsContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

function Tab({ index, children }) {
  const { activeIndex, setActiveIndex } = useContext(TabsContext);
  return (
    <button
      className={activeIndex === index ? "active" : ""}
      onClick={() => setActiveIndex(index)}
    >
      {children}
    </button>
  );
}

function TabPanel({ index, children }) {
  const { activeIndex } = useContext(TabsContext);
  return activeIndex === index ? <div>{children}</div> : null;
}

// Usage
<Tabs>
  <Tab index={0}>Tab 1</Tab>
  <Tab index={1}>Tab 2</Tab>
  <TabPanel index={0}>Content 1</TabPanel>
  <TabPanel index={1}>Content 2</TabPanel>
</Tabs>
```

### Controlled vs Uncontrolled Components

```jsx
// Controlled: React state is the source of truth
function ControlledInput() {
  const [value, setValue] = useState("");
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}

// Uncontrolled: DOM is the source of truth
function UncontrolledInput() {
  const inputRef = useRef(null);
  const handleSubmit = () => console.log(inputRef.current.value);
  return <input ref={inputRef} defaultValue="" />;
}
```

| Aspect | Controlled | Uncontrolled |
|--------|-----------|-------------|
| Source of truth | React state | DOM |
| Validation timing | On every change | On submit |
| Re-renders | On every keystroke | None (until form submit) |
| Complexity | Higher | Lower |
| Use case | Complex forms, real-time validation | Simple forms, third-party integrations |

---

## 13. Common Interview Questions

1. **Can functional components do everything class components can?** Almost. Error boundaries still require class components (or a wrapper library).
2. **Why do hooks have rules?** React identifies hooks by call order. Conditional or loop-based hooks break the mapping between call position and state.
3. **What is the stale closure problem?** A function captures an old value from a previous render. Common with `setTimeout`, `setInterval`, and event listeners in `useEffect`.
4. **How is `React.memo` different from `useMemo`?** `React.memo` memoizes a component (skips re-render). `useMemo` memoizes a computed value inside a component.
5. **When should you NOT use React.memo?** When the component is cheap to render, or when props change on nearly every render (the comparison cost outweighs the savings).
6. **Why did hooks replace HOCs and render props?** Hooks avoid wrapper nesting, are more composable, eliminate prop collision, and are easier to type with TypeScript.

---

## 14. Pitfalls Summary

| Pitfall | Explanation |
|---------|-------------|
| Stale closure | Functions capture values from the render they were created in |
| Conditional hooks | Breaks hook ordering; causes runtime errors |
| Missing deps in useEffect | Leads to stale closures or infinite loops |
| Inline functions defeating React.memo | New function reference on every render; use useCallback |
| Inline objects/arrays defeating React.memo | New reference on every render; use useMemo |
| useRef mutation not triggering render | Refs are mutable containers; updating them does not cause re-renders |
| Forgetting cleanup in useEffect | Memory leaks from subscriptions, timers, event listeners |
| Initializing state from props | useState initial value only used on first render; use key to reset |

---

## 15. Summary Cheat Sheet

```
Functional components = Functions that return JSX
Closures = Each render captures its own props/state
Stale closure = Captured value is outdated; fix with refs or functional updater
Hooks rules = Top-level only, React functions only, order must be stable
Lifecycle mapping = constructor -> function body, didMount -> useEffect(,[]),
                    didUpdate -> useEffect(,[deps]), willUnmount -> useEffect cleanup
React.memo = Skip re-render if props unchanged (shallow comparison)
HOCs = Functions wrapping components (being replaced by hooks)
Render props = Functions as children/props for behavior sharing (replaced by hooks)
Re-render triggers = Parent re-render, state change, context change
useRef = Mutable container, no re-render on change
```

---
