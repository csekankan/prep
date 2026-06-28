# Props vs State -- Interview Deep Dive

---

## 1. Fundamental Distinction

| Aspect | Props | State |
|--------|-------|-------|
| Owner | Parent component | The component itself |
| Mutability | **Immutable** (read-only to receiver) | **Mutable** (via setState / useState setter) |
| Direction | Top-down (parent to child) | Local (internal to component) |
| Triggers re-render? | Yes (when parent passes new props) | Yes (when state is updated) |
| Serializable? | Should be | Not necessarily |

**One-sentence rule**: Props are a component's configuration; state is a component's memory.

---

## 2. Props Immutability

A component must **never** modify its own props. Props are owned by the parent.

```jsx
function Greeting({ name }) {
  // NEVER do this
  name = "Bob";  // This "works" locally but is an anti-pattern

  return <h1>Hello, {name}</h1>;
}
```

Why not? Because the parent is the source of truth. If a child mutates its props, it creates a disconnect between what the parent thinks the child received and what the child actually uses. This violates React's unidirectional data flow.

### Output-Based Question: Mutating Props

```jsx
function Parent() {
  const config = { theme: "dark" };
  return <Child config={config} />;
}

function Child({ config }) {
  config.theme = "light"; // Mutating the prop object
  return <div>{config.theme}</div>;
}
```

**Answer**: This renders "light" -- the mutation works because objects are passed by reference. But this is a **bug**: the `config` object in `Parent` is now also "light" because it is the same reference. This can cause subtle, hard-to-debug issues. Always treat props as immutable.

---

## 3. State Ownership

State should live in the **lowest common ancestor** of all components that need it.

```
         App
        /   \
    Sidebar  Main
              |
           Content
```

If both `Sidebar` and `Content` need `user` data, `user` state should live in `App`, which passes it down as props to both.

### Local State

If only one component needs a piece of data, keep it local:

```jsx
function SearchBar() {
  const [query, setQuery] = useState("");  // Only SearchBar needs this
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

### Shared State

If multiple components need the same data, lift it up:

```jsx
function Parent() {
  const [temperature, setTemperature] = useState("");

  return (
    <div>
      <CelsiusInput temp={temperature} onTempChange={setTemperature} />
      <FahrenheitInput temp={temperature} onTempChange={setTemperature} />
    </div>
  );
}
```

---

## 4. Lifting State Up

Lifting state up means moving state to a common parent so that multiple children can share it.

### Before Lifting (Broken)

```jsx
function Counter1() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>A: {count}</button>;
}

function Counter2() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>B: {count}</button>;
}

function App() {
  // No way to display total count
  return (
    <div>
      <Counter1 />
      <Counter2 />
    </div>
  );
}
```

### After Lifting (Fixed)

```jsx
function Counter({ label, count, onIncrement }) {
  return <button onClick={onIncrement}>{label}: {count}</button>;
}

function App() {
  const [countA, setCountA] = useState(0);
  const [countB, setCountB] = useState(0);

  return (
    <div>
      <Counter label="A" count={countA} onIncrement={() => setCountA(c => c + 1)} />
      <Counter label="B" count={countB} onIncrement={() => setCountB(c => c + 1)} />
      <p>Total: {countA + countB}</p>
    </div>
  );
}
```

---

## 5. Derived State

Derived state is data that can be computed from existing props or state. **Do not store it in state.**

### Anti-Pattern: Storing Derived Data

```jsx
function FilteredList({ items, query }) {
  const [filteredItems, setFilteredItems] = useState([]);

  useEffect(() => {
    setFilteredItems(items.filter(item => item.includes(query)));
  }, [items, query]);

  return <ul>{filteredItems.map(i => <li key={i}>{i}</li>)}</ul>;
}
```

This causes an unnecessary extra render: first render with stale `filteredItems`, then `useEffect` fires and triggers a second render.

### Correct: Compute During Render

```jsx
function FilteredList({ items, query }) {
  const filteredItems = items.filter(item => item.includes(query));

  return <ul>{filteredItems.map(i => <li key={i}>{i}</li>)}</ul>;
}
```

If the computation is expensive, use `useMemo`:

```jsx
function FilteredList({ items, query }) {
  const filteredItems = useMemo(
    () => items.filter(item => item.includes(query)),
    [items, query]
  );

  return <ul>{filteredItems.map(i => <li key={i}>{i}</li>)}</ul>;
}
```

**Interview rule of thumb**: "If you can compute it from existing props or state, don't put it in state."

---

## 6. Props Drilling Problem

Props drilling is passing props through many intermediate components that do not use them.

```
App (has user state)
  |-- Layout (passes user down)
       |-- Sidebar (passes user down)
            |-- UserAvatar (actually uses user)
```

`Layout` and `Sidebar` do not use `user` -- they just pass it through. This is props drilling.

### Why It Is a Problem

1. **Maintenance burden**: Adding a new prop requires updating every intermediate component.
2. **Coupling**: Intermediate components know about data they do not use.
3. **Re-renders**: All intermediate components re-render when the prop changes.

### Solutions

| Solution | When to use |
|----------|------------|
| Context API (`useContext`) | Global/semi-global data (theme, auth, locale) |
| Component composition | Restructure the tree so the consumer is closer to the provider |
| State management library (Zustand, Redux, Jotai) | Complex state shared across many unrelated components |

### Composition Approach (Often Overlooked)

```jsx
function App() {
  const user = useUser();

  return (
    <Layout>
      <Sidebar>
        <UserAvatar user={user} />
      </Sidebar>
    </Layout>
  );
}

function Layout({ children }) {
  return <div className="layout">{children}</div>;
}

function Sidebar({ children }) {
  return <aside>{children}</aside>;
}
```

`Layout` and `Sidebar` no longer need to know about `user` at all. The parent renders `UserAvatar` directly and passes it as `children`.

---

## 7. Default Props

### Functional Components (Modern)

```jsx
function Button({ variant = "primary", size = "medium", children }) {
  return <button className={`btn-${variant} btn-${size}`}>{children}</button>;
}
```

### Using `defaultProps` (Legacy, Still Valid)

```jsx
function Button({ variant, size, children }) {
  return <button className={`btn-${variant} btn-${size}`}>{children}</button>;
}

Button.defaultProps = {
  variant: "primary",
  size: "medium",
};
```

**Interview note**: `defaultProps` on function components is deprecated as of React 18.3 and will be removed in a future version. Use ES6 default parameters instead.

### Gotcha: `undefined` vs `null`

Default parameters only apply when the value is `undefined`, not `null`:

```jsx
function Greeting({ name = "World" }) {
  return <h1>Hello, {name}</h1>;
}

<Greeting />             // "Hello, World"
<Greeting name={undefined} />  // "Hello, World"
<Greeting name={null} />       // "Hello, " (null overrides the default)
<Greeting name="" />           // "Hello, " (empty string overrides the default)
```

---

## 8. The `children` Prop

`children` is a special prop that contains whatever is placed between a component's opening and closing tags.

```jsx
function Card({ children }) {
  return <div className="card">{children}</div>;
}

<Card>
  <h2>Title</h2>
  <p>Content</p>
</Card>
```

### `children` Can Be Anything

- A string: `<Card>Hello</Card>`
- JSX elements: `<Card><p>Text</p></Card>`
- An array: `<Card>{[<p key="1">A</p>, <p key="2">B</p>]}</Card>`
- A function (render prop pattern): `<Card>{(data) => <p>{data}</p>}</Card>`
- Nothing: `<Card></Card>` (children is `undefined`)

### `React.Children` Utilities

```jsx
React.Children.count(children);     // Number of children
React.Children.map(children, fn);   // Map over children safely
React.Children.forEach(children, fn);
React.Children.only(children);      // Assert exactly one child, return it
React.Children.toArray(children);   // Flatten to a flat array with keys
```

---

## 9. Render Props Pattern

A render prop is a prop whose value is a **function** that returns React elements. It allows a component to share behavior without dictating the UI.

```jsx
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    setPosition({ x: e.clientX, y: e.clientY });
  };

  return <div onMouseMove={handleMouseMove}>{render(position)}</div>;
}

function App() {
  return (
    <MouseTracker
      render={({ x, y }) => (
        <p>Mouse is at ({x}, {y})</p>
      )}
    />
  );
}
```

### Using `children` as a Render Prop

```jsx
function MouseTracker({ children }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  return (
    <div onMouseMove={(e) => setPosition({ x: e.clientX, y: e.clientY })}>
      {children(position)}
    </div>
  );
}

<MouseTracker>
  {({ x, y }) => <p>Mouse: ({x}, {y})</p>}
</MouseTracker>
```

**Interview note**: Render props were the dominant pattern for sharing behavior before hooks. Today, custom hooks have largely replaced them, but render props are still useful when you need to share behavior *and* control rendering.

---

## 10. State Initialization Pitfalls

### Pitfall 1: Copying Props to State

```jsx
function UserProfile({ user }) {
  const [name, setName] = useState(user.name);

  return <input value={name} onChange={e => setName(e.target.value)} />;
}
```

If the parent passes a new `user` prop, `name` state does NOT update. `useState` only uses the initial value on the first render.

**Fix options**:
1. Use a `key` to force remount: `<UserProfile key={user.id} user={user} />`
2. Synchronize with `useEffect` (less ideal, causes double render)
3. Make it a controlled component (no local state, use prop directly)

### Pitfall 2: Expensive Initialization

```jsx
// BAD: createExpensiveData() runs on EVERY render (result is ignored after first)
const [data, setData] = useState(createExpensiveData());

// GOOD: Lazy initializer -- function is called only on first render
const [data, setData] = useState(() => createExpensiveData());
```

### Pitfall 3: Object/Array State Mutations

```jsx
function App() {
  const [user, setUser] = useState({ name: "Alice", age: 30 });

  const handleBirthday = () => {
    // BAD: Mutating existing state object
    user.age += 1;
    setUser(user); // Same reference, React may skip the re-render!

    // GOOD: Create a new object
    setUser({ ...user, age: user.age + 1 });

    // ALSO GOOD: Functional update
    setUser(prev => ({ ...prev, age: prev.age + 1 }));
  };

  return <p>{user.name} is {user.age}</p>;
}
```

---

## 11. Output-Based Interview Questions

### Question 1: Stale State in Event Handler

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
  };

  return <button onClick={handleClick}>Count: {count}</button>;
}
```

**What is `count` after one click?**

**Answer**: `1`. All three `setCount` calls see the same `count` value from the current render (which is `0`). So all three calls are `setCount(0 + 1)` = `setCount(1)`. React batches these and the final state is `1`.

**Fix**: Use the functional updater form:

```jsx
const handleClick = () => {
  setCount(c => c + 1); // 0 -> 1
  setCount(c => c + 1); // 1 -> 2
  setCount(c => c + 1); // 2 -> 3
};
```

### Question 2: Props vs State Ownership

```jsx
function Parent() {
  const [color, setColor] = useState("red");
  return (
    <div>
      <Child color={color} />
      <button onClick={() => setColor("blue")}>Change</button>
    </div>
  );
}

function Child({ color }) {
  const [localColor, setLocalColor] = useState(color);
  return <div style={{ color: localColor }}>Hello</div>;
}
```

**What color is "Hello" after clicking "Change"?**

**Answer**: Still "red". `localColor` was initialized with `color` on the first render. When `Parent` re-renders with `color = "blue"`, `Child` re-renders but `useState` ignores the new initial value -- state is only initialized once.

### Question 3: Stale Closure in setTimeout

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setTimeout(() => {
      alert(count);
    }, 3000);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <button onClick={handleClick}>Alert</button>
    </div>
  );
}
```

**Steps**: Click + three times (count = 3), then click Alert.

**What does the alert show?**

**Answer**: `3`. The `handleClick` closure captures `count` from the render in which it was called. At the time of clicking Alert, `count` is `3`, so the closure captures `3`. The alert shows `3`.

**But**: If you click Alert first (count = 0), then click + three times, the alert shows `0` -- the closure captured the value at the time of the click, not the latest value.

### Question 4: When to Use Props vs State vs Context?

| Data type | Use |
|-----------|-----|
| Configuration passed from parent | **Props** |
| Internal component data (form input, toggle) | **State** |
| Derived/computed data | **Neither** (compute inline or useMemo) |
| Theme, locale, auth user (app-wide) | **Context** |
| Complex shared state with actions | **State manager** (Redux, Zustand) |

---

## 12. getDerivedStateFromProps Anti-Patterns

`getDerivedStateFromProps` (class component) was designed to sync state with props. It was widely misused.

### Anti-Pattern 1: Unconditionally Copying Props

```jsx
class EmailInput extends React.Component {
  state = { email: this.props.email };

  static getDerivedStateFromProps(props, state) {
    return { email: props.email }; // Always overwrite state with props
  }

  handleChange = (e) => {
    this.setState({ email: e.target.value }); // This is immediately overwritten!
  };

  render() {
    return <input value={this.state.email} onChange={this.handleChange} />;
  }
}
```

Typing in the input does nothing because `getDerivedStateFromProps` overwrites the state on every render.

### Anti-Pattern 2: Erasing State When Props Change

```jsx
static getDerivedStateFromProps(props, state) {
  if (props.email !== state.prevPropsEmail) {
    return {
      email: props.email,
      prevPropsEmail: props.email,
    };
  }
  return null;
}
```

This is better but still fragile. The correct solution is usually one of:

1. **Fully controlled**: No local state, parent owns everything.
2. **Fully uncontrolled with a key**: Use `key` to reset the component.
3. **Refs for imperative reset**: Expose a reset method via `useImperativeHandle`.

---

## 13. Props vs State Decision Flowchart

```
Is the data passed from a parent?
  YES -> It's a PROP
  NO  -> Can it be computed from existing props/state?
           YES -> Don't store it. Compute inline.
           NO  -> Does more than one component need it?
                    YES -> Lift state to nearest common ancestor (or use Context)
                    NO  -> It's LOCAL STATE in this component
```

---

## 14. Common Interview Questions

1. **What is the difference between props and state?** Props are external, immutable inputs. State is internal, mutable data.
2. **Can a child modify its parent's state?** Not directly. The parent must pass a callback as a prop.
3. **What happens if you mutate a prop?** The mutation works (JS objects are by reference) but it breaks React's contract and causes bugs.
4. **Why use functional updater `setState(prev => ...)`?** To avoid stale closure issues when setting state based on the previous value.
5. **What is props drilling and how do you fix it?** Passing props through many layers. Fix with Context, composition, or state managers.
6. **Should you store fetched data in state?** Yes, but consider if a data-fetching library (TanStack Query, SWR) manages it better.

---

## 15. Summary Cheat Sheet

```
Props = External, immutable, passed by parent
State = Internal, mutable, owned by component
Derived data = Don't store, compute from props/state
Props drilling = Solved by Context, composition, or state managers
State init = Only runs on first render (use lazy initializer for expensive ops)
Stale state = Caused by closures capturing old values; fix with functional updater
Default props = Use ES6 defaults (defaultProps is deprecated for function components)
children prop = Special prop for nested content; can be JSX, string, function, etc.
Render props = Functions as props to share behavior (largely replaced by hooks)
```

---
