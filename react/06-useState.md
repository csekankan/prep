# useState Deep Dive — Interview Bible

## How React Stores State Internally

React does not store state in the component function itself. Each component instance corresponds to a **fiber node** in React's internal fiber tree. State is stored as a linked list of hooks on that fiber.

```javascript
// Simplified internal representation
fiber = {
  memoizedState: {
    queue: updateQueue,
    memoizedState: currentValue, // the actual state value
    next: nextHook              // linked list to next hook
  }
}
```

Key implications:
- Hooks must be called in the same order every render (linked list traversal)
- Calling hooks conditionally breaks the linked list alignment
- Each `useState` call corresponds to a specific position in the list

---

## Primitive vs Object State

### Primitive State

```javascript
const [count, setCount] = useState(0);
setCount(1); // triggers re-render only if 1 !== 0
setCount(0); // no re-render (same value)
```

### Object State

```javascript
const [user, setUser] = useState({ name: "Alice", age: 25 });

// WRONG: mutating existing object
user.name = "Bob";
setUser(user); // NO re-render! Same reference

// CORRECT: new object reference
setUser({ ...user, name: "Bob" }); // re-renders
```

React uses `Object.is` to compare previous and next state. For objects, this is a **reference comparison**, not a deep equality check.

---

## Functional Updates

### Why `prev => prev + 1` Is Necessary

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(count + 1); // uses stale closure value
    setCount(count + 1); // same stale value — still 0 + 1
    setCount(count + 1); // same stale value — still 0 + 1
  };
  // Final count: 1 (not 3)
}
```

With functional updates:

```javascript
const handleClick = () => {
  setCount(prev => prev + 1); // 0 -> 1
  setCount(prev => prev + 1); // 1 -> 2
  setCount(prev => prev + 1); // 2 -> 3
};
// Final count: 3
```

Functional updates read from the **pending state queue**, not the stale closure. This is critical in:
- Event handlers calling setState multiple times
- setTimeout / setInterval callbacks
- Any scenario where the closure captures an outdated value

---

## Batching: React 17 vs React 18

### React 17 Batching

Batching only occurs inside React event handlers:

```javascript
// React 17
function App() {
  const [a, setA] = useState(0);
  const [b, setB] = useState(0);

  const handleClick = () => {
    setA(1);
    setB(1);
    // ONE re-render (batched)
  };

  setTimeout(() => {
    setA(1);
    setB(1);
    // TWO re-renders (not batched in React 17!)
  }, 0);
}
```

### React 18 Automatic Batching

All state updates are batched regardless of context:

```javascript
// React 18
setTimeout(() => {
  setA(1);
  setB(1);
  // ONE re-render (automatic batching)
}, 0);

fetch('/api').then(() => {
  setA(1);
  setB(1);
  // ONE re-render (automatic batching)
});
```

To opt out of batching in React 18:

```javascript
import { flushSync } from 'react-dom';

flushSync(() => setA(1)); // re-render immediately
flushSync(() => setB(1)); // re-render again
```

---

## Lazy Initialization

When initial state requires expensive computation:

```javascript
// BAD: runs on every render
const [data, setData] = useState(expensiveComputation());

// GOOD: runs only on first render
const [data, setData] = useState(() => expensiveComputation());
```

The initializer function is called only on mount. React discards it on subsequent renders. Use this for:
- Reading from localStorage
- Parsing large JSON
- Complex calculations

```javascript
const [items, setItems] = useState(() => {
  const saved = localStorage.getItem('items');
  return saved ? JSON.parse(saved) : [];
});
```

---

## State Identity and Object.is Comparison

React bails out of re-renders when the new state is identical to the current state per `Object.is`:

```javascript
Object.is(0, 0)           // true — no re-render
Object.is('a', 'a')       // true — no re-render
Object.is(NaN, NaN)       // true — no re-render
Object.is(0, -0)          // false — re-render!
Object.is({}, {})         // false — re-render (different references)
```

Important edge case:

```javascript
const [val, setVal] = useState(0);
setVal(0); // React bails out — component does NOT re-render
```

However, React may still render the component once before bailing out (without committing to DOM). This is an internal optimization detail.

---

## Resetting State with Key Prop

When you need to fully reset a component's internal state:

```javascript
function App() {
  const [userId, setUserId] = useState(1);
  return <Profile key={userId} userId={userId} />;
}

function Profile({ userId }) {
  const [name, setName] = useState('');
  // When key changes, React unmounts old Profile and mounts new one
  // All internal state resets to initial values
}
```

This is cleaner than:
```javascript
useEffect(() => {
  setName('');
  setAge(0);
  setEmail('');
}, [userId]);
```

The `key` prop approach guarantees a fresh instance.

---

## Common Anti-Patterns

### 1. Derived State That Should Be Computed

```javascript
// BAD
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]);

useEffect(() => {
  setFilteredItems(items.filter(i => i.active));
}, [items]);

// GOOD — derive during render
const [items, setItems] = useState([]);
const filteredItems = items.filter(i => i.active);
```

### 2. Copying Props into State

```javascript
// BAD — state diverges from props
function Child({ initialValue }) {
  const [value, setValue] = useState(initialValue);
  // If parent re-renders with new initialValue, state doesn't update!
}
```

### 3. Using State for Non-Render Data

```javascript
// BAD — triggers re-render unnecessarily
const [intervalId, setIntervalId] = useState(null);

// GOOD — use useRef for values that don't affect UI
const intervalRef = useRef(null);
```

---

## Output-Based Interview Questions

### Question 1: Triple setState in Click Handler

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
  };

  return <button onClick={handleClick}>{count}</button>;
}
```

**What is displayed after one click?**

**Answer:** `1`

All three calls use the same closure value of `count` (which is `0`). So each call computes `0 + 1 = 1`. React batches them and the final value is `1`. The three calls are equivalent to calling `setCount(1)` three times.

---

### Question 2: setTimeout + setState

```javascript
function Timer() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setTimeout(() => {
      setCount(count + 1);
    }, 3000);
    setCount(count + 1);
  };

  console.log("render:", count);
  return <button onClick={handleClick}>{count}</button>;
}
```

**What logs after clicking once (initial count is 0)?**

**Answer:**
- Immediately: `render: 1` (synchronous setState causes re-render)
- After 3 seconds: `render: 1` (setTimeout closure captured `count = 0`, so `0 + 1 = 1`, same as current state)

Wait — actually in React 18, `setCount(0 + 1)` inside setTimeout computes `1`. Since current state is already `1`, React bails out. If using functional update `setCount(prev => prev + 1)`, it would go from 1 to 2.

---

### Question 3: Object State Mutation Without Spread

```javascript
function UserProfile() {
  const [user, setUser] = useState({ name: "Alice", age: 25 });

  const handleClick = () => {
    user.age = 30;
    setUser(user);
  };

  return <div>{user.name} - {user.age}</div>;
}
```

**What renders after clicking?**

**Answer:** The component does NOT re-render. `user` is the same reference before and after the mutation. `Object.is(prevState, nextState)` returns `true`, so React bails out. The UI still shows "Alice - 25" even though the underlying object's `age` property was mutated to 30. This is a very common bug.

---

### Question 4: Functional Update Order

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(prev => prev + 1);
    setCount(prev => prev * 10);
    setCount(prev => prev + 2);
  };

  return <span>{count}</span>;
}
```

**What is displayed after one click?**

**Answer:** `12`

The functional updates are queued and processed sequentially:
1. `prev = 0` -> `0 + 1 = 1`
2. `prev = 1` -> `1 * 10 = 10`
3. `prev = 10` -> `10 + 2 = 12`

---

### Question 5: setState in Render

```javascript
function Broken() {
  const [count, setCount] = useState(0);

  if (count < 5) {
    setCount(count + 1); // setState during render
  }

  return <div>{count}</div>;
}
```

**What happens?**

**Answer:** React allows setState during render as a pattern for derived state (similar to getDerivedStateFromProps). React will re-render the component immediately without committing intermediate states to the DOM. The component renders repeatedly: 0, 1, 2, 3, 4, 5 — but only `5` is committed to the DOM. However, if the condition were always true (infinite loop), React would throw a "Too many re-renders" error.

---

### Question 6: Batching Across Async Boundaries (React 18)

```javascript
function App() {
  const [a, setA] = useState(0);
  const [b, setB] = useState(0);

  console.log("render", a, b);

  const handleClick = async () => {
    const data = await fetch('/api/data');
    setA(1);
    setB(2);
  };

  return <button onClick={handleClick}>Click</button>;
}
```

**How many renders after clicking? (React 18)**

**Answer:** One render logging `render 1 2`. In React 18, automatic batching applies even in async callbacks (after `await`). Both `setA(1)` and `setB(2)` are batched into a single re-render. In React 17, this would cause two separate renders.

---

## Key Pitfalls Summary

| Pitfall | Consequence |
|---------|-------------|
| Mutating object state directly | No re-render (same reference) |
| Using `count + 1` in async | Stale closure captures old value |
| Expensive initial state without lazy init | Recalculated every render |
| Storing derived data as state | State synchronization bugs |
| Conditional hook calls | Linked list corruption, crashes |
| setState with same value | No re-render (Object.is bailout) |

---

## Tradeoffs

### Primitive vs Object State
- **Primitive**: Simple, no spread needed, clear equality semantics
- **Object**: Groups related data, but requires immutable updates

### Single Object vs Multiple useState
- **Single object**: Fewer hook calls, atomic updates for related fields
- **Multiple useState**: Independent updates, simpler individual setters, better for unrelated values

### useState vs useReducer
- **useState**: Simple values, 1-2 transitions
- **useReducer**: Complex state logic, many transitions, testable reducer functions

---

## Interview Tips

1. Always mention fiber node and linked list when explaining internals
2. Demonstrate understanding of batching differences between React 17 and 18
3. Use functional updates whenever current state depends on previous state
4. Know when to use `key` prop for resetting state vs useEffect
5. Understand that `Object.is` is the comparison algorithm, not `===` (they differ on NaN and +0/-0)
