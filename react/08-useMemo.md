# useMemo Deep Dive — Interview Bible

## What is Memoization?

Memoization is an optimization technique that caches the result of an expensive computation and returns the cached result when the same inputs occur again. `useMemo` applies this concept within React components.

```javascript
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
```

- First argument: a "create" function that returns the computed value
- Second argument: dependency array
- Returns: the memoized value (not a function)

---

## When useMemo Runs

```javascript
function Component({ items, filter }) {
  const filtered = useMemo(() => {
    console.log("computing...");
    return items.filter(item => item.category === filter);
  }, [items, filter]);
}
```

Execution rules:
1. **Mount**: Always runs the factory function
2. **Re-render with same deps**: Returns cached value (skips computation)
3. **Re-render with changed deps**: Runs factory again, caches new result

React compares each dependency with its previous value using `Object.is`. If ALL dependencies are the same, the cached value is returned.

---

## Dependency Comparison with Object.is

```javascript
// Primitive deps — stable comparison
useMemo(() => compute(count), [count]);
// count: 5 -> 5 = same, skip
// count: 5 -> 6 = different, recompute

// Object deps — reference comparison
useMemo(() => compute(config), [config]);
// config: {a:1} -> {a:1} = DIFFERENT references, recompute every time!
```

This is the most common mistake with useMemo. If a dependency is an object or array that gets recreated every render, useMemo provides zero benefit:

```javascript
function Parent() {
  const options = { sort: 'asc' }; // new object every render

  return <Child options={options} />;
}

function Child({ options }) {
  // This recomputes every render because options is a new reference!
  const sorted = useMemo(() => sortData(data, options), [options]);
}
```

---

## Referential Equality for Objects/Arrays

### The Problem

```javascript
function SearchResults({ query }) {
  // New array reference every render, even if contents are identical
  const results = data.filter(item => item.name.includes(query));

  return <ResultList items={results} />;
}
```

If `ResultList` is wrapped in `React.memo`, it still re-renders because `results` is a new array reference every time (even when `query` hasn't changed and other state triggered re-render).

### The Solution

```javascript
function SearchResults({ query }) {
  const results = useMemo(
    () => data.filter(item => item.name.includes(query)),
    [query]
  );

  return <ResultList items={results} />;
}
```

Now `results` maintains the same reference across renders unless `query` actually changes. Combined with `React.memo` on `ResultList`, the child skips re-rendering.

---

## Expensive Computation Caching

The primary use case for useMemo — avoid redundant heavy calculations:

```javascript
function DataGrid({ rows, sortConfig }) {
  const sortedRows = useMemo(() => {
    // O(n log n) operation — don't want this on every keystroke
    return [...rows].sort((a, b) => {
      const val = a[sortConfig.key] > b[sortConfig.key] ? 1 : -1;
      return sortConfig.direction === 'desc' ? -val : val;
    });
  }, [rows, sortConfig]);

  return <Table data={sortedRows} />;
}
```

Good candidates for useMemo:
- Sorting large arrays (1000+ items)
- Complex filtering/mapping
- Mathematical computations (Fibonacci, matrix operations)
- Creating derived data structures (trees from flat lists)
- Regular expression compilation

---

## When NOT to Use useMemo (Premature Optimization)

### useMemo Has a Cost

```javascript
// UNNECESSARY: simple operations
const fullName = useMemo(
  () => `${firstName} ${lastName}`,
  [firstName, lastName]
);

// Just compute directly — string concatenation is negligible
const fullName = `${firstName} ${lastName}`;
```

The overhead of useMemo includes:
- Storing the previous dependency array
- Comparing each dependency on every render
- Storing the cached value in memory
- The hook call overhead itself

### Rules of Thumb

Do NOT use useMemo when:
- The computation is trivial (simple math, string ops, property access)
- The component rarely re-renders
- The value is a primitive that would be the same anyway
- You haven't measured a performance problem

DO use useMemo when:
- Computation is provably expensive (> 1ms, ideally profiled)
- The result is passed as a prop to a memoized child component
- The result is used as a dependency in another hook
- You have measured and confirmed re-renders are the bottleneck

```javascript
// GOOD: expensive + passed to memo'd child
const chartData = useMemo(() => processLargeDataset(rawData), [rawData]);
return <MemoizedChart data={chartData} />;

// BAD: trivial computation, no downstream memo
const isEven = useMemo(() => count % 2 === 0, [count]);
return <div>{isEven ? 'even' : 'odd'}</div>;
```

---

## useMemo vs useEffect

A common anti-pattern is using useEffect + setState when useMemo would suffice:

```javascript
// BAD: causes an extra render
function Component({ items }) {
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    setFiltered(items.filter(i => i.active));
  }, [items]);

  return <List items={filtered} />;
}

// GOOD: computed synchronously during render, no extra render
function Component({ items }) {
  const filtered = useMemo(
    () => items.filter(i => i.active),
    [items]
  );

  return <List items={filtered} />;
}
```

Key differences:
| Aspect | useMemo | useEffect + setState |
|--------|---------|---------------------|
| When runs | During render (synchronous) | After render + paint |
| Extra renders | No | Yes (setState triggers another render) |
| Flash of stale data | No | Possible (first render has old state) |
| Use case | Derived data | Side effects with external systems |

---

## useMemo for Referential Stability in Hooks

When a memoized value is used as a dependency in another hook:

```javascript
function useQuery(query, options) {
  useEffect(() => {
    fetchData(query, options);
  }, [query, options]); // options must be referentially stable!
}

function App() {
  // Without useMemo, options is new reference every render
  // causing the effect to re-run endlessly
  const options = useMemo(
    () => ({ limit: 10, offset: page * 10 }),
    [page]
  );

  useQuery(searchTerm, options);
}
```

---

## React Compiler and Auto-Memoization Future

React Compiler (formerly React Forget) aims to automatically memoize:
- Component return values (like React.memo)
- Expensive computations (like useMemo)
- Callback functions (like useCallback)

```javascript
// Future: compiler detects and auto-memoizes
function TodoList({ todos, filter }) {
  const filtered = todos.filter(t => t.status === filter);
  // Compiler inserts memoization automatically
  return <List items={filtered} />;
}
```

Implications for interviews:
- useMemo will eventually become unnecessary in most cases
- Understanding WHY memoization helps is still critical
- The mental model of referential equality remains important
- Manual useMemo won't break — it just becomes redundant

Current status: React Compiler is in production at Meta and available as an experimental feature.

---

## Output-Based Interview Questions

### Question 1: useMemo with Object Dependency

```javascript
function App() {
  const [count, setCount] = useState(0);
  const config = { threshold: 10 };

  const result = useMemo(() => {
    console.log("computing");
    return count > config.threshold ? "high" : "low";
  }, [count, config]);

  return (
    <div>
      <span>{result}</span>
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </div>
  );
}
```

**Does "computing" log on every click?**

**Answer:** Yes. Even though `config` has the same shape `{ threshold: 10 }` every render, it's a **new object reference** each time. `Object.is(prevConfig, nextConfig)` returns `false`, so useMemo recomputes on every render. The memoization is completely ineffective here.

Fix: move `config` outside the component, or memoize it, or use `config.threshold` as the dependency instead.

---

### Question 2: useMemo Without Deps

```javascript
function Component({ items }) {
  const sorted = useMemo(() => {
    console.log("sorting");
    return [...items].sort();
  });

  return <div>{sorted.join(", ")}</div>;
}
```

**When does "sorting" log?**

**Answer:** On every render. When the dependency array is **omitted entirely** (not empty `[]`, but completely absent), useMemo provides no memoization — it recalculates every time. This is different from `[]` which would compute only on mount.

- `useMemo(fn)` — no deps, computes every render (useless)
- `useMemo(fn, [])` — empty deps, computes only on mount
- `useMemo(fn, [a, b])` — computes when a or b changes

---

### Question 3: useMemo Return Value Identity

```javascript
function App() {
  const [name, setName] = useState("Alice");
  const [age, setAge] = useState(25);

  const user = useMemo(() => ({ name, age }), [name]);

  useEffect(() => {
    console.log("user changed");
  }, [user]);

  return (
    <div>
      <button onClick={() => setAge(a => a + 1)}>Birthday</button>
    </div>
  );
}
```

**Does "user changed" log when the Birthday button is clicked?**

**Answer:** No. The `useMemo` depends only on `[name]`. Clicking Birthday changes `age` but not `name`. Since `name` hasn't changed, useMemo returns the **same cached object reference**. The useEffect sees the same reference and doesn't re-run.

However, this introduces a bug: `user.age` inside the cached object is stale! It captured `age = 25` when useMemo last ran. This is a correctness issue — `age` should be in the dependency array.

---

### Question 4: useMemo with Expensive Computation Order

```javascript
function App() {
  const [x, setX] = useState(1);
  const [y, setY] = useState(1);

  console.log("render start");

  const a = useMemo(() => {
    console.log("memo a");
    return x * 2;
  }, [x]);

  const b = useMemo(() => {
    console.log("memo b");
    return y * 3;
  }, [y]);

  console.log("render end");
  return <div>{a + b}</div>;
}
```

**What logs when only `y` changes (e.g., setY(2) is called)?**

**Answer:**
```
render start
memo b
render end
```

Explanation:
- `render start` — component re-renders
- `memo a` is NOT logged — `x` hasn't changed, cached value returned
- `memo b` IS logged — `y` changed, recomputes
- `render end` — render continues

useMemo computations happen synchronously during render, in the order they appear. Only memos whose dependencies changed execute their factory.

---

### Question 5: useMemo vs Direct Computation (Behavior Difference)

```javascript
function Parent() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  // Version A: direct computation
  const doubled = count * 2;

  // Version B: memoized
  const doubledMemo = useMemo(() => count * 2, [count]);

  return (
    <div>
      <input value={text} onChange={e => setText(e.target.value)} />
      <MemoChild value={doubled} />
      <MemoChild value={doubledMemo} />
    </div>
  );
}

const MemoChild = React.memo(({ value }) => {
  console.log("child render:", value);
  return <span>{value}</span>;
});
```

**When the user types in the input (text changes), which child re-renders?**

**Answer:** Neither re-renders. Both `doubled` and `doubledMemo` produce the same primitive value (e.g., `0`). Since `React.memo` does shallow comparison and `0 === 0`, both children skip re-render.

However, if the value were an object (`{ doubled: count * 2 }`), Version A would create a new reference every render (child re-renders), while Version B would return the cached reference (child skips). This is where useMemo provides real value with memo'd children.

---

## Pitfalls

| Pitfall | Consequence |
|---------|-------------|
| Object/array dependency without memoization | useMemo recomputes every render (pointless) |
| Omitting dependency array entirely | Computes every render (defeats purpose) |
| Missing dependency in array | Stale cached value (correctness bug) |
| Memoizing trivial computations | Overhead exceeds savings |
| Using useMemo for side effects | Violates React's model (use useEffect instead) |

---

## Tradeoffs

### Memory vs CPU
- useMemo trades memory (storing cached values) for CPU time (avoiding recomputation)
- For very large cached objects, memory pressure may outweigh computation savings

### Correctness vs Performance
- Adding useMemo with incomplete deps can cause stale data bugs
- The "always recompute" approach is always correct, just potentially slow

### Readability vs Optimization
- Excessive memoization clutters code and adds indirection
- Profile first, optimize second
- React DevTools Profiler can show which renders are expensive

---

## Interview Tips

1. Know the difference between omitted deps (no memoization) and empty deps (mount only)
2. Explain Object.is and why object deps break memoization
3. Contrast useMemo vs useEffect for derived state — useMemo avoids extra renders
4. Mention React Compiler as the future of automatic memoization
5. Be ready to argue AGAINST useMemo when computation is trivial
6. Understand that useMemo is a performance optimization, not a semantic guarantee — React may discard cached values in future (e.g., offscreen components)
