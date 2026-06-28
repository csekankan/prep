# useCallback Deep Dive — Interview Bible

## Why Functions Break Memoization

In JavaScript, functions are objects. Every render creates a new function instance:

```javascript
function Parent() {
  // New function object created every render
  const handleClick = () => { console.log("clicked"); };

  // Even though the function body is identical, it's a new reference
  return <Child onClick={handleClick} />;
}
```

This matters because:
1. If `Child` is wrapped in `React.memo`, the new `handleClick` reference fails the shallow prop comparison
2. If `handleClick` is in a dependency array, hooks re-run every render
3. Object.is(prevHandleClick, nextHandleClick) is always `false`

---

## useCallback Fundamentals

```javascript
const memoizedFn = useCallback(fn, dependencies);
```

`useCallback` returns the **same function reference** across renders as long as dependencies haven't changed:

```javascript
function Parent() {
  const [count, setCount] = useState(0);

  // Same reference returned unless `count` changes
  const handleClick = useCallback(() => {
    console.log(count);
  }, [count]);

  return <MemoChild onClick={handleClick} />;
}
```

What useCallback does internally:
```javascript
// Simplified implementation
function useCallback(fn, deps) {
  return useMemo(() => fn, deps);
}
```

It literally IS `useMemo` returning the function itself rather than calling it.

---

## useCallback + React.memo Combo

This is the canonical pattern. Neither is useful alone:

```javascript
const MemoChild = React.memo(function Child({ onClick, label }) {
  console.log("Child rendered");
  return <button onClick={onClick}>{label}</button>;
});

function Parent() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []); // stable: no deps needed with functional update

  return (
    <div>
      <input value={text} onChange={e => setText(e.target.value)} />
      <MemoChild onClick={handleClick} label="Increment" />
    </div>
  );
}
```

When user types in the input:
- Parent re-renders (text state changed)
- `handleClick` returns same reference (deps unchanged)
- `MemoChild` receives same props -> skips re-render

Without useCallback, MemoChild would re-render on every keystroke because `onClick` would be a new function.

---

## Dependency Array Behavior

### Empty Dependencies

```javascript
const handleSubmit = useCallback(() => {
  submitForm(formData); // BUG: stale formData!
}, []);
```

Empty deps means the function is created once on mount and never updated. Any values referenced inside become stale closures.

### Correct Dependencies

```javascript
const handleSubmit = useCallback(() => {
  submitForm(formData);
}, [formData]); // new function when formData changes
```

### Functional Updates to Avoid Dependencies

```javascript
// Instead of depending on count:
const increment = useCallback(() => {
  setCount(count + 1); // requires [count] dependency
}, [count]);

// Use functional update — no dependency needed:
const increment = useCallback(() => {
  setCount(prev => prev + 1); // always reads latest
}, []);
```

This pattern gives maximum stability: the function reference NEVER changes.

---

## useCallback vs useMemo(() => fn)

They are functionally identical:

```javascript
// These are equivalent:
const fn1 = useCallback(() => doSomething(a, b), [a, b]);
const fn2 = useMemo(() => () => doSomething(a, b), [a, b]);
```

`useCallback(fn, deps)` is syntactic sugar for `useMemo(() => fn, deps)`.

When to prefer each:
- `useCallback`: When you want to memoize a function (99% of cases)
- `useMemo(() => fn)`: Almost never — only useful if you need to emphasize that the function itself is the expensive thing to create (extremely rare)

---

## When useCallback Is Useless

### Without React.memo on Child

```javascript
function Parent() {
  const [count, setCount] = useState(0);

  // useCallback is POINTLESS here
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  // Child is NOT memoized — it re-renders regardless of prop stability
  return <Child onClick={handleClick} />;
}

function Child({ onClick }) {
  console.log("Child rendered"); // logs on every Parent render
  return <button onClick={onClick}>Click</button>;
}
```

Without `React.memo` on Child, the child always re-renders when Parent re-renders — regardless of whether props changed. The useCallback adds overhead for zero benefit.

### For DOM Elements

```javascript
function App() {
  const [count, setCount] = useState(0);

  // UNNECESSARY: native elements don't use React.memo
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return <button onClick={handleClick}>Click</button>;
}
```

Native HTML elements cannot be memoized. Passing a new function to a `<button>` costs almost nothing.

### When Re-renders Are Cheap

```javascript
// If Child renders in <1ms, memoization overhead isn't worth it
const SimpleChild = React.memo(({ onClick }) => {
  return <span onClick={onClick}>simple text</span>;
});
```

Profile first. If the child's render is cheap, the bookkeeping cost of useCallback + memo may exceed the saved render time.

---

## Event Handler Stability

### In Lists

```javascript
function TodoList({ todos, onToggle }) {
  return (
    <ul>
      {todos.map(todo => (
        // New arrow function per item per render — bad if MemoTodoItem
        <MemoTodoItem
          key={todo.id}
          todo={todo}
          onToggle={() => onToggle(todo.id)} // new reference!
        />
      ))}
    </ul>
  );
}
```

Fixes:

**Option 1: Pass ID down, handle in child**
```javascript
const MemoTodoItem = React.memo(function TodoItem({ todo, onToggle }) {
  return (
    <li onClick={() => onToggle(todo.id)}>
      {todo.text}
    </li>
  );
});

function TodoList({ todos, onToggle }) {
  // onToggle is stable (useCallback in parent)
  return todos.map(todo => (
    <MemoTodoItem key={todo.id} todo={todo} onToggle={onToggle} />
  ));
}
```

**Option 2: useCallback with event parameter**
```javascript
const handleToggle = useCallback((id) => {
  setTodos(prev => prev.map(t =>
    t.id === id ? { ...t, done: !t.done } : t
  ));
}, []);
```

---

## useCallback in Custom Hooks

Custom hooks that return functions should almost always memoize them:

```javascript
function useDebounce(callback, delay) {
  const timeoutRef = useRef(null);

  // Consumers expect this to be stable
  const debouncedFn = useCallback((...args) => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  return debouncedFn;
}
```

Why this matters:
- Consumers may pass the returned function as a prop to memo'd children
- Consumers may use it in dependency arrays of their own hooks
- Unstable return functions propagate instability through the component tree

---

## Output-Based Interview Questions

### Question 1: Child with React.memo but Parent Creates New Handler

```javascript
const MemoButton = React.memo(({ onClick, label }) => {
  console.log("MemoButton rendered:", label);
  return <button onClick={onClick}>{label}</button>;
});

function App() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  const increment = () => setCount(c => c + 1);

  return (
    <div>
      <input value={text} onChange={e => setText(e.target.value)} />
      <MemoButton onClick={increment} label="Add" />
      <p>{count}</p>
    </div>
  );
}
```

**What happens when user types in the input?**

**Answer:** `MemoButton rendered: Add` logs on every keystroke. Even though `MemoButton` is wrapped in `React.memo`, the `increment` function is recreated every render (no `useCallback`). The new function reference fails `React.memo`'s shallow comparison. The memo wrapper provides zero benefit here.

Fix: `const increment = useCallback(() => setCount(c => c + 1), []);`

---

### Question 2: useCallback with Stale Closure

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  const logCount = useCallback(() => {
    console.log("count:", count);
  }, []); // empty deps!

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
      <button onClick={logCount}>Log</button>
    </div>
  );
}
```

**User clicks Increment 5 times, then clicks Log. What is logged?**

**Answer:** `count: 0`

The `useCallback` has empty dependencies, so it never recreates the function. The closure permanently captures `count = 0` from the initial render. Clicking Increment updates `count` to 5 in state, but the memoized `logCount` function still references the stale initial value.

Fix: Add `count` to deps: `useCallback(() => { console.log(count); }, [count])` or use a ref.

---

### Question 3: useCallback Dependency Change

```javascript
const MemoDisplay = React.memo(({ getValue }) => {
  console.log("Display rendered");
  return <span>{getValue()}</span>;
});

function App() {
  const [count, setCount] = useState(0);
  const [multiplier, setMultiplier] = useState(2);

  const getValue = useCallback(() => {
    return count * multiplier;
  }, [count, multiplier]);

  return (
    <div>
      <MemoDisplay getValue={getValue} />
      <button onClick={() => setCount(c => c + 1)}>Count+</button>
      <button onClick={() => setMultiplier(m => m + 1)}>Mult+</button>
    </div>
  );
}
```

**How many times does "Display rendered" log if user clicks Count+ then Mult+?**

**Answer:** 3 times total.

1. Initial mount: `Display rendered` (count=0, multiplier=2, getValue returns 0)
2. Click Count+: `count` changes -> `getValue` gets new reference -> MemoDisplay re-renders: `Display rendered`
3. Click Mult+: `multiplier` changes -> `getValue` gets new reference -> MemoDisplay re-renders: `Display rendered`

Every dependency change creates a new function reference, which breaks memo's shallow comparison.

---

### Question 4: useCallback Without Dependencies vs With Dependencies

```javascript
function SearchForm({ onSearch }) {
  const [query, setQuery] = useState("");

  const handleSubmit = useCallback(() => {
    onSearch(query);
  }, [query, onSearch]);

  console.log("SearchForm rendered");

  return (
    <form onSubmit={e => { e.preventDefault(); handleSubmit(); }}>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <MemoSubmitButton onSubmit={handleSubmit} />
    </form>
  );
}

const MemoSubmitButton = React.memo(({ onSubmit }) => {
  console.log("SubmitButton rendered");
  return <button type="button" onClick={onSubmit}>Search</button>;
});
```

**User types "abc" (3 keystrokes). How many times does SubmitButton render?**

**Answer:** 4 times (1 initial + 3 keystrokes).

Each keystroke changes `query` state, which changes the `[query, onSearch]` dependency, which creates a new `handleSubmit` reference. MemoSubmitButton sees a new `onSubmit` prop and re-renders.

The useCallback is doing the right thing here (the function's behavior actually changes with each keystroke), but it means MemoSubmitButton can't avoid re-renders. This is expected behavior, not a bug.

---

### Question 5: Comparing Two Patterns

```javascript
// Pattern A
function Parent() {
  const [items, setItems] = useState([1, 2, 3]);

  const removeItem = (id) => {
    setItems(prev => prev.filter(i => i !== id));
  };

  return <MemoList items={items} onRemove={removeItem} />;
}

// Pattern B
function Parent() {
  const [items, setItems] = useState([1, 2, 3]);

  const removeItem = useCallback((id) => {
    setItems(prev => prev.filter(i => i !== id));
  }, []);

  return <MemoList items={items} onRemove={removeItem} />;
}

const MemoList = React.memo(({ items, onRemove }) => {
  console.log("List rendered");
  return items.map(i => <span key={i} onClick={() => onRemove(i)}>{i}</span>);
});
```

**If a sibling component's state change causes Parent to re-render (items unchanged), does MemoList re-render in each pattern?**

**Answer:**
- **Pattern A:** Yes. `removeItem` is a new function -> `React.memo` shallow comparison fails -> MemoList re-renders.
- **Pattern B:** No. `removeItem` has empty deps (uses functional update) -> same reference -> `items` same reference -> MemoList skips render.

---

## Pitfalls

| Pitfall | Consequence |
|---------|-------------|
| useCallback without React.memo on child | Pure overhead, no benefit |
| Empty deps with referenced state | Stale closure bug |
| Too many dependencies | Function recreated often, defeating the purpose |
| Using on native DOM elements | No component memoization exists to benefit from |
| Not using functional setState updates | Forces state into dependency array |

---

## Tradeoffs

### Stability vs Correctness
- More stable function (fewer deps) = stale closure risk
- More correct function (all deps) = less stability
- Functional updates (`prev => ...`) resolve this tension for setState

### useCallback Everywhere vs Selective
- **Everywhere**: Consistent, no thinking required, but adds overhead
- **Selective**: Only where needed (memo'd children, hook deps), cleaner code
- React Compiler will make this moot in the future

### Readability Impact
- Heavy useCallback usage adds visual noise
- Extracting callbacks to custom hooks can improve readability
- Consider whether the optimization is worth the complexity

---

## Decision Framework

Use useCallback when ALL of these are true:
1. The function is passed as a prop to a `React.memo` wrapped child, OR used in a dependency array
2. The parent component re-renders frequently for reasons unrelated to this function
3. The child component's render is expensive enough to justify the optimization

Skip useCallback when ANY of these are true:
- Child is not memoized
- Function is used on native DOM elements only
- Component rarely re-renders
- Child render is trivially cheap

---

## Interview Tips

1. Always pair useCallback with React.memo in your explanation — one without the other is usually pointless
2. Demonstrate understanding of closure staleness and how functional updates solve it
3. Know that `useCallback(fn, deps)` === `useMemo(() => fn, deps)`
4. Explain the list rendering pattern (pass stable handler + ID, handle in child)
5. Be ready to argue AGAINST useCallback in simple cases
6. Mention React Compiler as the future automatic optimization
