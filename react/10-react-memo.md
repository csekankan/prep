# React.memo Deep Dive — Interview Bible

## What is React.memo?

`React.memo` is a Higher-Order Component (HOC) that memoizes a component's rendered output. It performs a **shallow comparison** of props and skips re-rendering if props haven't changed.

```javascript
const MemoizedComponent = React.memo(function MyComponent(props) {
  return <div>{props.value}</div>;
});
```

Without React.memo, a component re-renders whenever its parent re-renders — regardless of whether its props actually changed. React.memo adds a prop comparison gate.

---

## How Shallow Comparison Works

React.memo uses `Object.is` on each prop:

```javascript
// Simplified internal logic
function shallowEqual(prevProps, nextProps) {
  const prevKeys = Object.keys(prevProps);
  const nextKeys = Object.keys(nextProps);

  if (prevKeys.length !== nextKeys.length) return false;

  for (let key of prevKeys) {
    if (!Object.is(prevProps[key], nextProps[key])) {
      return false;
    }
  }
  return true;
}
```

What this means in practice:

```javascript
// Primitives — compared by value
<MemoComp name="Alice" age={25} />
// Re-render only if "Alice" or 25 changes

// Objects — compared by reference
<MemoComp style={{ color: 'red' }} />
// ALWAYS re-renders: new object every render

// Arrays — compared by reference
<MemoComp items={[1, 2, 3]} />
// ALWAYS re-renders: new array every render

// Functions — compared by reference
<MemoComp onClick={() => handleClick()} />
// ALWAYS re-renders: new function every render
```

---

## Custom areEqual Comparator

You can provide a custom comparison function as the second argument:

```javascript
const MemoComp = React.memo(function Component({ user, config }) {
  return <div>{user.name} - {config.theme}</div>;
}, (prevProps, nextProps) => {
  // Return true to SKIP re-render (props are "equal")
  // Return false to RE-RENDER (props are "different")
  return (
    prevProps.user.id === nextProps.user.id &&
    prevProps.config.theme === nextProps.config.theme
  );
});
```

Important: The comparator signature is the **opposite** of `shouldComponentUpdate`:
- `areEqual` returns `true` -> skip render (props are equal)
- `shouldComponentUpdate` returns `true` -> DO render

### When to Use Custom Comparator

```javascript
// Deep comparison for specific fields
const MemoChart = React.memo(Chart, (prev, next) => {
  return JSON.stringify(prev.data) === JSON.stringify(next.data) &&
         prev.width === next.width &&
         prev.height === next.height;
});
```

Use sparingly. Deep comparison can be more expensive than just re-rendering, especially for large objects.

---

## When React.memo Helps vs Hurts

### Helps

1. **Expensive render**: Component does heavy computation or renders many DOM nodes
2. **Frequent parent re-renders**: Parent re-renders often due to unrelated state changes
3. **Stable props**: Most props are primitives or properly memoized references

```javascript
// GOOD candidate: expensive render, parent re-renders often
const MemoDataGrid = React.memo(function DataGrid({ rows, columns }) {
  // Renders 1000+ table cells
  return (
    <table>
      {rows.map(row => (
        <tr key={row.id}>
          {columns.map(col => <td key={col}>{row[col]}</td>)}
        </tr>
      ))}
    </table>
  );
});
```

### Hurts

1. **Props always change**: Every prop is a new reference each render (memo check is wasted)
2. **Cheap render**: Component returns trivial JSX
3. **Rare re-renders**: Parent barely re-renders anyway
4. **All children are leaves**: No child tree to skip

```javascript
// BAD candidate: inline objects ensure props always differ
function Parent() {
  return (
    <MemoComp
      style={{ margin: 10 }}           // new object
      data={items.map(transform)}      // new array
      onClick={() => handleClick()}    // new function
    />
  );
  // React.memo does comparison work, finds difference, re-renders anyway
  // Net result: SLOWER than without memo
}
```

---

## React.memo with children Prop

The `children` prop is almost always a new reference:

```javascript
function Parent() {
  const [count, setCount] = useState(0);

  return (
    <MemoWrapper>
      <span>Count: {count}</span>
    </MemoWrapper>
  );
}

const MemoWrapper = React.memo(function Wrapper({ children }) {
  console.log("Wrapper rendered");
  return <div className="wrapper">{children}</div>;
});
```

`<span>Count: {count}</span>` creates a new React element (object) every render. Since `children` is a new reference, `React.memo` comparison always fails. The memo is useless here.

### Workaround: Lift Children Out

```javascript
function Parent() {
  const [count, setCount] = useState(0);
  return <Layout count={count} />;
}

function Layout({ count }) {
  return (
    <MemoExpensiveSidebar />
    <main>Count: {count}</main>
  );
}

const MemoExpensiveSidebar = React.memo(function Sidebar() {
  // Only re-renders if its own props change
  return <nav>...</nav>;
});
```

### Workaround: Memoize Children

```javascript
function Parent() {
  const [count, setCount] = useState(0);
  const [unrelated, setUnrelated] = useState(0);

  const children = useMemo(
    () => <span>Count: {count}</span>,
    [count]
  );

  return <MemoWrapper>{children}</MemoWrapper>;
}
```

Now `children` only changes when `count` changes, not on every render.

---

## Combining with useMemo/useCallback

The full optimization pattern requires all three:

```javascript
function Dashboard() {
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // useMemo: stable array reference
  const filteredItems = useMemo(
    () => items.filter(i => i.status === filter),
    [filter]
  );

  // useCallback: stable function reference
  const handleSelect = useCallback((id) => {
    setSelectedId(id);
  }, []);

  return (
    <div>
      <SearchInput value={searchTerm} onChange={setSearchTerm} />
      {/* MemoItemList won't re-render when searchTerm changes */}
      <MemoItemList items={filteredItems} onSelect={handleSelect} />
    </div>
  );
}

const MemoItemList = React.memo(function ItemList({ items, onSelect }) {
  console.log("ItemList rendered");
  return items.map(item => (
    <div key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </div>
  ));
});
```

If ANY one piece is missing:
- No `useMemo` on `filteredItems`: new array reference -> MemoItemList re-renders
- No `useCallback` on `handleSelect`: new function reference -> MemoItemList re-renders
- No `React.memo` on ItemList: re-renders regardless of prop stability

---

## PureComponent Equivalent

`React.memo` is the functional component equivalent of `PureComponent`:

```javascript
// Class component
class MyComponent extends React.PureComponent {
  render() {
    return <div>{this.props.value}</div>;
  }
}

// Functional equivalent
const MyComponent = React.memo(function MyComponent({ value }) {
  return <div>{value}</div>;
});
```

Both do shallow prop comparison. Differences:
- `PureComponent` also compares state (class state)
- `React.memo` only compares props (state is managed by hooks internally)
- `React.memo` accepts a custom comparator; `PureComponent` does not

---

## React.memo and Context Re-renders

React.memo does NOT prevent re-renders caused by context changes:

```javascript
const ThemeContext = React.createContext('light');

const MemoButton = React.memo(function Button({ label }) {
  const theme = useContext(ThemeContext);
  console.log("Button rendered");
  return <button className={theme}>{label}</button>;
});

function App() {
  const [theme, setTheme] = useState('light');
  const [count, setCount] = useState(0);

  return (
    <ThemeContext.Provider value={theme}>
      <MemoButton label="Click" />
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
        Toggle Theme
      </button>
    </ThemeContext.Provider>
  );
}
```

Behavior:
- Clicking "Count" button: MemoButton does NOT re-render (props unchanged, context unchanged)
- Clicking "Toggle Theme": MemoButton DOES re-render (context value changed)

React.memo's prop comparison is bypassed entirely when a consumed context value changes. This is by design — context changes are treated as internal state changes.

### Mitigating Context Re-renders

**Split contexts by update frequency:**
```javascript
const ThemeContext = React.createContext('light');      // changes rarely
const CounterContext = React.createContext(0);          // changes often

// Components consuming only ThemeContext don't re-render when count changes
```

**Memoize the context value:**
```javascript
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  const value = useMemo(() => ({ theme, setTheme }), [theme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}
```

Without `useMemo`, the context value object is new every render, forcing all consumers to re-render.

---

## Output-Based Interview Questions

### Question 1: Memo'd Component with Inline Object Prop

```javascript
const MemoCard = React.memo(function Card({ style, title }) {
  console.log("Card rendered:", title);
  return <div style={style}>{title}</div>;
});

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <MemoCard style={{ padding: 10 }} title="Hello" />
    </div>
  );
}
```

**Does "Card rendered: Hello" log on every count increment?**

**Answer:** Yes. `{ padding: 10 }` creates a new object reference on every render. Even though the object's content is identical, `Object.is(prevStyle, nextStyle)` returns `false`. React.memo's shallow comparison detects a "change" and re-renders.

Fix:
```javascript
const cardStyle = { padding: 10 }; // outside component, or useMemo
```

---

### Question 2: Memo'd Component with Children

```javascript
const MemoBox = React.memo(function Box({ children }) {
  console.log("Box rendered");
  return <div className="box">{children}</div>;
});

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <MemoBox>
        <p>Static content</p>
      </MemoBox>
    </div>
  );
}
```

**Does "Box rendered" log when count changes?**

**Answer:** Yes. `<p>Static content</p>` is a JSX expression that creates a new React element object every render. This object is passed as the `children` prop. Since it's a new reference, React.memo's comparison fails, and Box re-renders.

Even though the content is visually static, JSX creates a new object: `React.createElement('p', null, 'Static content')` returns a fresh object each call.

---

### Question 3: Memo with Custom Comparator

```javascript
const MemoUser = React.memo(
  function User({ user, onSelect }) {
    console.log("User rendered:", user.name);
    return <div onClick={() => onSelect(user.id)}>{user.name} ({user.age})</div>;
  },
  (prev, next) => prev.user.id === next.user.id
);

function App() {
  const [users, setUsers] = useState([
    { id: 1, name: "Alice", age: 25 },
    { id: 2, name: "Bob", age: 30 },
  ]);

  const handleBirthday = () => {
    setUsers(prev => prev.map(u =>
      u.id === 1 ? { ...u, age: u.age + 1 } : u
    ));
  };

  return (
    <div>
      <button onClick={handleBirthday}>Alice's Birthday</button>
      {users.map(u => (
        <MemoUser key={u.id} user={u} onSelect={console.log} />
      ))}
    </div>
  );
}
```

**What happens when "Alice's Birthday" is clicked?**

**Answer:** Neither User component re-renders. The custom comparator only checks `user.id`, and IDs don't change (1 and 2 remain the same). Even though Alice's age changed from 25 to 26, the comparator says "props are equal" and skips the render.

This is a correctness bug: the UI shows stale age. The custom comparator is too aggressive — it should also check `user.age` or use the full user object comparison.

---

### Question 4: Memo'd Component Receiving Stable vs Unstable Props

```javascript
const MemoHeader = React.memo(function Header({ title, actions }) {
  console.log("Header rendered");
  return (
    <header>
      <h1>{title}</h1>
      {actions}
    </header>
  );
});

function App() {
  const [count, setCount] = useState(0);
  const title = "My App"; // primitive, stable

  return (
    <div>
      <MemoHeader
        title={title}
        actions={<button>Settings</button>}
      />
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
    </div>
  );
}
```

**Does Header re-render when count changes?**

**Answer:** Yes. While `title` is a stable string, `actions` receives `<button>Settings</button>` which is a new React element (object) every render. One unstable prop is enough to fail the shallow comparison.

---

### Question 5: React.memo + Context Consumer

```javascript
const ColorContext = React.createContext("blue");

const MemoLabel = React.memo(function Label({ text }) {
  const color = useContext(ColorContext);
  console.log("Label rendered:", text);
  return <span style={{ color }}>{text}</span>;
});

function App() {
  const [color, setColor] = useState("blue");
  const [count, setCount] = useState(0);

  return (
    <ColorContext.Provider value={color}>
      <MemoLabel text="Hello" />
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <button onClick={() => setColor("red")}>Make Red</button>
    </ColorContext.Provider>
  );
}
```

**Which buttons cause MemoLabel to re-render?**

**Answer:**
- Clicking "Count": MemoLabel does NOT re-render. Props (`text="Hello"`) haven't changed, and context (`color="blue"`) hasn't changed.
- Clicking "Make Red": MemoLabel DOES re-render. Context value changed from "blue" to "red". React.memo cannot prevent context-triggered re-renders.
- Clicking "Make Red" again (already red): MemoLabel does NOT re-render. Context value is the same ("red" -> "red"), so React bails out.

---

## When to Apply React.memo — Decision Matrix

| Scenario | Use React.memo? | Reason |
|----------|----------------|--------|
| Component renders expensive tree | Yes | Skip subtree render |
| Parent re-renders frequently, child props stable | Yes | Avoid unnecessary work |
| Component always receives new props | No | Comparison overhead wasted |
| Component is a leaf with trivial render | Probably no | Savings negligible |
| Component uses context that changes often | Limited benefit | Context bypasses memo |
| Component renders a list of items | Yes (on each item) | Prevents full list re-render |

---

## Pitfalls

| Pitfall | Consequence |
|---------|-------------|
| Inline objects/arrays/functions as props | Memo comparison always fails |
| Passing children as JSX | New React element every render |
| Custom comparator too aggressive | Stale UI (correctness bug) |
| Custom comparator too expensive | Slower than just re-rendering |
| Forgetting that context bypasses memo | Unexpected re-renders |
| Applying memo without profiling | Overhead with no measured gain |

---

## Tradeoffs

### Memo Everything vs Selective Memo
- **Everything**: Consistent optimization, no decisions needed, but adds overhead everywhere
- **Selective**: Applied where profiling shows benefit, keeps code simpler

### Shallow vs Deep Comparison
- **Shallow (default)**: Fast O(n) where n = number of props, may miss deep changes
- **Deep (custom)**: Catches nested changes, but O(deep) comparison can be expensive
- Rule of thumb: if deep comparison is needed, restructure props to be flatter

### Correctness vs Performance
- Custom comparators that skip fields can cause stale UI
- Default shallow comparison is always correct but may re-render more than needed
- When in doubt, err on correctness (don't use custom comparator)

---

## Interview Tips

1. Always demonstrate that React.memo alone is not enough — pair with useMemo/useCallback
2. Explain why `children` prop breaks memo (JSX creates new objects)
3. Know the custom comparator return value semantics (true = skip, opposite of shouldComponentUpdate)
4. Discuss context as a way that re-renders bypass React.memo
5. Be prepared to argue against over-applying React.memo (not free, has overhead)
6. Mention that React Compiler will make manual React.memo obsolete
