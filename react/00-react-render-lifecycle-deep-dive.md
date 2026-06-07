# React Render Lifecycle — Deep Dive & Tricky Questions

Understanding the **exact order** in which React executes code is the single most important concept for interviews. Every "tricky" React question is really a question about **execution order**.

---

## The Complete Render Cycle

Every React render goes through **exactly these phases**, in this order:

```
TRIGGER (setState, prop change, parent re-render, context change)
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  PHASE 1: RENDER (Pure Computation)                   │
│                                                       │
│  React calls your component function top to bottom:   │
│    1. useState / useReducer → return current state     │
│    2. useRef → return ref object (stable, no re-render)│
│    3. useMemo → recompute if deps changed              │
│    4. useCallback → return memoized function            │
│    5. useEffect → REGISTER callback (NOT run it)       │
│    6. useLayoutEffect → REGISTER callback (NOT run it) │
│    7. return JSX → build virtual DOM tree               │
│                                                       │
│  RULES:                                                │
│    - No side effects                                   │
│    - No DOM access                                     │
│    - May be called multiple times (Strict Mode)        │
│    - May be interrupted (concurrent mode)              │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  PHASE 2: RECONCILIATION (Diffing)                    │
│                                                       │
│  React compares OLD virtual DOM vs NEW virtual DOM:    │
│    - Same type, same key → update props/state          │
│    - Different type → unmount old, mount new           │
│    - Key changed → unmount old, mount new              │
│    - Builds a list of DOM mutations needed             │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  PHASE 3: COMMIT (DOM Mutation — synchronous)         │
│                                                       │
│  React applies DOM changes (insertions, updates,      │
│  deletions) in one synchronous batch.                 │
│                                                       │
│  During this phase:                                    │
│    - Refs are updated (.current = DOM node)            │
│    - Cleanup of useLayoutEffect from previous render   │
│    - useLayoutEffect callbacks run (synchronous!)      │
│                                                       │
│  DOM is now updated but browser hasn't painted yet.    │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  PHASE 4: BROWSER PAINT                               │
│                                                       │
│  Browser updates the screen. User sees the new UI.    │
└──────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│  PHASE 5: EFFECTS (Asynchronous, after paint)         │
│                                                       │
│  1. Cleanup functions from PREVIOUS useEffect run     │
│  2. New useEffect callbacks run                       │
│                                                       │
│  This is async — browser can paint before effects run  │
└──────────────────────────────────────────────────────┘
```

---

## The Golden Rule: Execution Order

For a single component on **mount**:

```
1. Component function body        (render phase)
2. useMemo computations           (render phase)
3. JSX returned                   (render phase)
4. DOM mutations committed        (commit phase)
5. Refs attached                  (commit phase)
6. useLayoutEffect callback       (commit phase, BEFORE paint)
7. Browser paints                 (browser)
8. useEffect callback             (after paint)
```

For a single component on **update**:

```
1. Component function body        (render phase)
2. useMemo recomputes if deps changed  (render phase)
3. JSX returned                   (render phase)
4. DOM mutations committed        (commit phase)
5. Refs updated                   (commit phase)
6. useLayoutEffect CLEANUP (prev) (commit phase, BEFORE paint)
7. useLayoutEffect callback (new) (commit phase, BEFORE paint)
8. Browser paints                 (browser)
9. useEffect CLEANUP (prev)       (after paint)
10. useEffect callback (new)      (after paint)
```

For a component on **unmount**:

```
1. useLayoutEffect cleanup        (commit phase)
2. useEffect cleanup              (after paint)
3. Refs detached (.current = null)
```

---

## Parent-Child Execution Order

This trips everyone up. For a tree like:

```
<Parent>
  <Child />
</Parent>
```

### Mount order:

```
1. Parent function body           ← parent renders first
2.   Child function body          ← child renders during parent's JSX
3.   Child useLayoutEffect        ← child effects first (bottom-up)
4. Parent useLayoutEffect         ← parent effects after children
5.   Child useEffect              ← child effects first (bottom-up)
6. Parent useEffect               ← parent effects after children
```

Effects fire **bottom-up** (children before parents), but render is **top-down** (parent calls child).

### Update order (parent state changes):

```
1. Parent function body           ← parent re-renders
2.   Child function body          ← child re-renders (new props or same)
3.   Child useLayoutEffect cleanup (prev)
4.   Child useLayoutEffect callback (new)
5. Parent useLayoutEffect cleanup (prev)
6. Parent useLayoutEffect callback (new)
7. PAINT
8.   Child useEffect cleanup (prev)
9.   Child useEffect callback (new)
10. Parent useEffect cleanup (prev)
11. Parent useEffect callback (new)
```

---

## useState: What Actually Happens During setState

```javascript
const [count, setCount] = useState(0);

function handleClick() {
  setCount(1);        // does NOT change count immediately
  console.log(count); // still 0!
}
```

`setCount` does NOT mutate `count`. It:

1. Enqueues an update on the fiber node
2. Marks the component as "needs re-render"
3. Schedules a re-render
4. On the NEXT render, `useState(0)` returns the new value `1`

```
Timeline:
  handleClick() called
    setCount(1)       → queues update, count is STILL 0
    console.log(count) → logs 0
  handleClick() returns
  React processes queue
  React calls component function again
    useState(0) → returns 1 (from queue)
    count is now 1 in THIS render
```

### Batching

React 18+ batches ALL setState calls, even in setTimeout/promises:

```javascript
function handleClick() {
  setCount(c => c + 1);  // queued
  setFlag(f => !f);      // queued
  setName("hello");      // queued
  // ONE re-render with all three updates
}
```

Before React 18, only event handlers were batched. Async callbacks like setTimeout caused multiple re-renders.

---

## useEffect vs useLayoutEffect — The Critical Difference

```
                    useLayoutEffect          useEffect
                         │                       │
Render ──► Commit ──► runs HERE ──► Paint ──► runs HERE
                    (blocks paint)          (after paint)
```

### When it matters:

```javascript
function Tooltip({ text, targetRect }) {
  const ref = useRef();
  const [position, setPosition] = useState({ top: 0, left: 0 });

  // BAD: useEffect — user sees a flash (tooltip renders at 0,0 then jumps)
  useEffect(() => {
    const { height } = ref.current.getBoundingClientRect();
    setPosition({ top: targetRect.top - height, left: targetRect.left });
  }, [targetRect]);

  // GOOD: useLayoutEffect — runs before paint, no flash
  useLayoutEffect(() => {
    const { height } = ref.current.getBoundingClientRect();
    setPosition({ top: targetRect.top - height, left: targetRect.left });
  }, [targetRect]);

  return <div ref={ref} style={position}>{text}</div>;
}
```

`useLayoutEffect` = "I need to read/write the DOM before the user sees anything."
`useEffect` = "I have a side effect that doesn't need to block the screen."

---

## Closures and Stale Values — The Root of All Confusion

Every render creates a **snapshot** — a frozen copy of all values at that moment:

```javascript
function Counter() {
  const [count, setCount] = useState(0);

  function handleClick() {
    // This function "closes over" count = 0 on first render
    setTimeout(() => {
      console.log(count); // will ALWAYS log the value from when setTimeout was created
    }, 3000);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

```
Render 1: count=0, handleClick closes over count=0
  User clicks → setTimeout(() => log(0), 3000) scheduled
Render 2: count=1, NEW handleClick closes over count=1
Render 3: count=2, NEW handleClick closes over count=2
  3 seconds pass...
  setTimeout fires → logs 0  (the closure from Render 1)
```

Each render is a **photograph**. The function remembers the photograph it was born in.

### Fix with ref:

```javascript
function Counter() {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);
  countRef.current = count; // always up to date (runs during render)

  function handleClick() {
    setTimeout(() => {
      console.log(countRef.current); // always latest value
    }, 3000);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

`ref.current` is a **mutable box** that always holds the latest value. The closure captures the **box** (same reference every render), not the value inside it.

### Fix with functional update:

```javascript
function handleClick() {
  setTimeout(() => {
    setCount(prev => prev + 1); // prev is always current, no stale closure
  }, 3000);
}
```

---

## Strict Mode Double-Invocation

In development, React Strict Mode intentionally calls certain things twice:

```
What runs twice (dev only):
  - Component function body
  - useState initializer function
  - useMemo computation
  - useReducer reducer

What runs setup+cleanup+setup (dev only):
  - useEffect
  - useLayoutEffect

What does NOT run twice:
  - Event handlers
  - setState/dispatch calls
```

This is to catch impure renders and missing cleanup. If your component breaks under double-invocation, it has a bug.

---

## Reconciliation Key Behaviors

### Same type = update in place

```javascript
// Render 1:
<div className="old">Hello</div>

// Render 2:
<div className="new">World</div>

// React: Same type (div) → keep DOM node, update className and textContent
```

### Different type = destroy and rebuild

```javascript
// Render 1:
<div><Counter /></div>

// Render 2:
<span><Counter /></span>

// React: div → span = different type → unmount Counter, destroy div, 
// create span, mount NEW Counter (state is lost!)
```

### Key = identity

```javascript
// Render 1:
<input key="email" />

// Render 2:
<input key="password" />

// React: different key → unmount old input, mount new input
// (even though same type! state is lost, DOM is recreated)
```

---

# Tricky Output-Based Questions

---

## Question 1: setState is not synchronous

```javascript
function App() {
  const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
    console.log(count);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

**After one click, what is logged? What does the button show?**

<details>
<summary>Answer</summary>

**Console: `0`**
**Button shows: `1`**

- `count` is `0` when handleClick runs (closure snapshot).
- All three `setCount(count + 1)` calls are `setCount(0 + 1)` = `setCount(1)`.
- React batches them. Last one wins: state = 1.
- `console.log(count)` reads the closure value: still `0`.
- On next render, `count` = 1 and button shows `1`.

**Fix: use functional updates**
```javascript
setCount(c => c + 1); // c = 0 → 1
setCount(c => c + 1); // c = 1 → 2
setCount(c => c + 1); // c = 2 → 3
// Button would show 3
```

</details>

---

## Question 2: Effect cleanup ordering

```javascript
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log("effect", count);
    return () => console.log("cleanup", count);
  });

  console.log("render", count);

  return <button onClick={() => setCount(1)}>Click</button>;
}
```

**What logs on mount, then after one click?**

<details>
<summary>Answer</summary>

**Mount:**
```
render 0
effect 0
```

**After click (count: 0 → 1):**
```
render 1
cleanup 0
effect 1
```

Order explained:
1. Component function runs → `render 1`
2. React commits DOM, browser paints
3. Previous effect's cleanup runs → `cleanup 0` (closure from previous render)
4. New effect runs → `effect 1`

The cleanup logs `0` (not `1`) because it was created during the previous render when `count` was `0`.

</details>

---

## Question 3: Stale closure in setTimeout

```javascript
function App() {
  const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
    setTimeout(() => {
      console.log("timeout:", count);
    }, 0);
    console.log("sync:", count);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

**Click the button once. What logs?**

<details>
<summary>Answer</summary>

```
sync: 0
timeout: 0
```

Both log `0`. Here's why:

1. `handleClick` closes over `count = 0`.
2. `setCount(count + 1)` queues an update. `count` is still `0`.
3. `console.log("sync:", count)` runs immediately → `0`.
4. `setTimeout` callback also closes over `count = 0`.
5. Even though setTimeout fires after the re-render, it uses the closure from when it was created.
6. Button will show `1` on next render, but the setTimeout captured `0`.

</details>

---

## Question 4: useEffect dependency array

```javascript
function App() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState("Alice");

  useEffect(() => {
    console.log("effect ran");
  }, [count]);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
      <button onClick={() => setName("Bob")}>Name: {name}</button>
    </div>
  );
}
```

**Click "Name" button. Does the effect run?**

<details>
<summary>Answer</summary>

**No, the effect does NOT run.**

The dependency array is `[count]`. Clicking the Name button changes `name`, which triggers a re-render, but `count` hasn't changed. React compares deps: `Object.is(0, 0)` is `true`, so the effect is skipped.

The component function body still runs (re-render happens), but the effect is skipped.

</details>

---

## Question 5: Parent-child effect order

```javascript
function Child() {
  console.log("Child render");
  useEffect(() => {
    console.log("Child effect");
    return () => console.log("Child cleanup");
  });
  return <div>Child</div>;
}

function Parent() {
  console.log("Parent render");
  useEffect(() => {
    console.log("Parent effect");
    return () => console.log("Parent cleanup");
  });
  return <div><Child /></div>;
}
```

**What logs on mount? Then Parent re-renders (state change)?**

<details>
<summary>Answer</summary>

**Mount:**
```
Parent render
Child render
Child effect
Parent effect
```

**Re-render:**
```
Parent render
Child render
Child cleanup
Child effect
Parent cleanup
Parent effect
```

Render is **top-down** (Parent → Child).
Effects are **bottom-up** (Child → Parent).
Cleanups run before their corresponding new effects, but the entire cleanup+effect sequence is bottom-up.

</details>

---

## Question 6: Ref vs State timing

```javascript
function App() {
  const [stateVal, setStateVal] = useState(0);
  const refVal = useRef(0);

  function handleClick() {
    setStateVal(stateVal + 1);
    refVal.current = refVal.current + 1;
    console.log("state:", stateVal);
    console.log("ref:", refVal.current);
  }

  return (
    <div>
      <p>State: {stateVal}, Ref: {refVal.current}</p>
      <button onClick={handleClick}>Click</button>
    </div>
  );
}
```

**Click once. What logs? What does the UI show?**

<details>
<summary>Answer</summary>

**Console:**
```
state: 0
ref: 1
```

**UI shows: "State: 1, Ref: 1"**

- `stateVal` is `0` in this closure. `setStateVal(1)` queues update. Logging `stateVal` → `0`.
- `refVal.current` mutates immediately (no queue, no async). Goes from 0 to 1. Logging it → `1`.
- On re-render: `useState` returns `1`, `refVal.current` is still `1`. UI shows both as 1.

Key difference: `ref` updates **immediately and synchronously**. `state` updates **on next render**.

</details>

---

## Question 7: useEffect with empty deps and state

```javascript
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      console.log("count:", count);
      setCount(count + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);  // empty deps!

  return <p>{count}</p>;
}
```

**What happens? What does the UI show over time?**

<details>
<summary>Answer</summary>

**Console:** `count: 0` every second, forever.

**UI:** Shows `1` and never changes.

The effect runs once (empty deps). The `setInterval` callback closes over `count = 0`.
- Every second: `console.log("count:", 0)` and `setCount(0 + 1)` = `setCount(1)`.
- First time: state goes 0 → 1, UI shows 1.
- Every subsequent time: `setCount(1)` but state is already `1`. `Object.is(1, 1)` → React bails out, no re-render.

The interval keeps running and logging `0` forever (stale closure), but the UI is stuck at `1`.

**Fix with functional update:**
```javascript
setCount(c => c + 1); // no closure dependency, always uses latest
```
Now it increments correctly: 0, 1, 2, 3...

</details>

---

## Question 8: Multiple effects — execution order

```javascript
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log("A");
    return () => console.log("cleanup A");
  });

  useEffect(() => {
    console.log("B");
    return () => console.log("cleanup B");
  });

  useEffect(() => {
    console.log("C");
    return () => console.log("cleanup C");
  });

  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**What logs on mount? After one click?**

<details>
<summary>Answer</summary>

**Mount:**
```
A
B
C
```

**After click:**
```
cleanup A
cleanup B
cleanup C
A
B
C
```

Multiple effects in the same component run in **declaration order** (top to bottom).
On update: ALL cleanups run first (in order), THEN all new effects run (in order).
NOT cleanup-A → effect-A → cleanup-B → effect-B. It's all cleanups, then all effects.

</details>

---

## Question 9: Key prop resets state

```javascript
function Input({ label }) {
  const [text, setText] = useState("");
  console.log(`${label} render, text="${text}"`);

  return <input value={text} onChange={e => setText(e.target.value)} />;
}

function App() {
  const [isEmail, setIsEmail] = useState(true);

  return (
    <div>
      <button onClick={() => setIsEmail(e => !e)}>Toggle</button>
      {isEmail
        ? <Input label="Email" />
        : <Input label="Password" />
      }
    </div>
  );
}
```

**Type "hello" in the Email input, then click Toggle. What happens to the text?**

<details>
<summary>Answer</summary>

**The text "hello" SURVIVES the toggle.** It shows "hello" in the Password input.

```
Email render, text=""
// type "hello"
Email render, text="h"
Email render, text="he"
Email render, text="hel"
Email render, text="hell"
Email render, text="hello"
// click toggle
Password render, text="hello"  ← state preserved!
```

Why? Both branches render `<Input>` at the same position in the tree. React sees:
- Same type (`Input`)? Yes.
- Same position? Yes.
- → Update props, KEEP state.

React does not care about `label` being different. It only checks **type + position**.

**Fix: add key to force remount**
```javascript
{isEmail
  ? <Input key="email" label="Email" />
  : <Input key="password" label="Password" />
}
```
Now React treats them as different components. State resets on toggle.

</details>

---

## Question 10: useLayoutEffect vs useEffect timing

```javascript
function App() {
  const [show, setShow] = useState(false);
  const ref = useRef(null);

  useLayoutEffect(() => {
    if (ref.current) {
      console.log("layout:", ref.current.getBoundingClientRect().height);
    }
  });

  useEffect(() => {
    if (ref.current) {
      console.log("effect:", ref.current.getBoundingClientRect().height);
    }
  });

  console.log("render");

  return (
    <div>
      <button onClick={() => setShow(true)}>Show</button>
      {show && <div ref={ref} style={{ height: 200 }}>Content</div>}
    </div>
  );
}
```

**Click Show. What order do the logs appear?**

<details>
<summary>Answer</summary>

```
render
layout: 200
effect: 200
```

1. `render` — component function body runs first
2. `layout: 200` — useLayoutEffect runs after DOM commit but BEFORE paint
3. `effect: 200` — useEffect runs AFTER paint

Both can read the DOM (the div exists in both cases), but `useLayoutEffect` runs synchronously before the browser paints, while `useEffect` runs asynchronously after.

If you did DOM mutations in `useLayoutEffect`, the user would never see the intermediate state. In `useEffect`, they might see a flash.

</details>

---

## Question 11: setState inside useEffect

```javascript
function App() {
  const [count, setCount] = useState(0);
  const [doubled, setDoubled] = useState(0);

  useEffect(() => {
    setDoubled(count * 2);
  }, [count]);

  console.log("render", count, doubled);

  return (
    <div>
      <p>{count} x 2 = {doubled}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </div>
  );
}
```

**Click the button. How many renders happen? What logs?**

<details>
<summary>Answer</summary>

**On click (count 0 → 1):**
```
render 1 0
render 1 2
```

**Two renders happen:**

1. First render: `count` is 1, but `doubled` is still 0 (effect hasn't run yet). Logs `render 1 0`.
2. React commits, paints, runs effect → `setDoubled(1 * 2)` = `setDoubled(2)` → triggers re-render.
3. Second render: `count` is 1, `doubled` is 2. Logs `render 1 2`.

User might briefly see "1 x 2 = 0" before it becomes "1 x 2 = 2".

**This is an anti-pattern.** `doubled` is derived state. Use `useMemo` instead:
```javascript
const doubled = useMemo(() => count * 2, [count]);
// One render, no flash, no extra state
```

</details>

---

## Question 12: Context re-render behavior

```javascript
const ThemeContext = React.createContext("light");

const MemoChild = React.memo(function MemoChild() {
  console.log("MemoChild render");
  return <div>Memo Child</div>;
});

function ContextChild() {
  const theme = useContext(ThemeContext);
  console.log("ContextChild render", theme);
  return <div>Theme: {theme}</div>;
}

function Parent() {
  const [count, setCount] = useState(0);
  console.log("Parent render");

  return (
    <ThemeContext.Provider value={count % 2 === 0 ? "light" : "dark"}>
      <MemoChild />
      <ContextChild />
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </ThemeContext.Provider>
  );
}
```

**Click the button. What re-renders?**

<details>
<summary>Answer</summary>

```
Parent render
ContextChild render dark
```

`MemoChild` does NOT re-render (no props changed, React.memo skips it).
`ContextChild` DOES re-render even though it's not wrapped in memo.

Key insight: **Context bypasses React.memo.** Even if you wrapped `ContextChild` in `React.memo`, it would STILL re-render because `useContext` subscribes the component to context changes directly.

```javascript
const ContextChild = React.memo(function ContextChild() {
  const theme = useContext(ThemeContext); // context changed → re-render regardless of memo
  return <div>{theme}</div>;
});
// Still re-renders when theme changes!
```

</details>

---

## Question 13: Batching in setTimeout (React 18 vs 17)

```javascript
function App() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);

  console.log("render", count, flag);

  function handleClick() {
    setTimeout(() => {
      setCount(c => c + 1);
      setFlag(f => !f);
    }, 0);
  }

  return <button onClick={handleClick}>Click</button>;
}
```

**Click once. How many renders happen?**

<details>
<summary>Answer</summary>

**React 18:** ONE render.
```
render 1 true
```

**React 17:** TWO renders.
```
render 1 false
render 1 true
```

React 18 introduced **automatic batching** everywhere — even inside setTimeout, promises, and native event handlers. React 17 only batched inside React event handlers.

</details>

---

## Question 14: Cleanup captures old values

```javascript
function Chat({ roomId }) {
  useEffect(() => {
    console.log("connect to", roomId);

    return () => {
      console.log("disconnect from", roomId);
    };
  }, [roomId]);

  return <div>Room: {roomId}</div>;
}

function App() {
  const [room, setRoom] = useState("general");
  return (
    <div>
      <Chat roomId={room} />
      <button onClick={() => setRoom("random")}>Switch</button>
    </div>
  );
}
```

**Mount, then click Switch. What logs?**

<details>
<summary>Answer</summary>

```
connect to general
disconnect from general
connect to random
```

The cleanup function logs `"disconnect from general"` — NOT `"disconnect from random"`.

The cleanup was created during the render when `roomId` was `"general"`. It closes over that value. When React runs the cleanup before the new effect, it uses the closure from the previous render.

This is exactly right for resource management: disconnect from the room you WERE in, then connect to the new one.

</details>

---

## Question 15: Conditional rendering and state preservation

```javascript
function App() {
  const [showA, setShowA] = useState(true);

  return (
    <div>
      {showA && <Counter label="A" />}
      <Counter label="B" />
      <button onClick={() => setShowA(s => !s)}>Toggle A</button>
    </div>
  );
}

function Counter({ label }) {
  const [count, setCount] = useState(0);
  return (
    <div>
      {label}: {count}
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </div>
  );
}
```

**Increment both counters to 5. Click Toggle A (hides A). What is B's count?**

<details>
<summary>Answer</summary>

**B's count resets to 0!**

Before toggle:
```
Position 0: <Counter label="A" />   ← count=5
Position 1: <Counter label="B" />   ← count=5
```

After toggle (showA = false):
```
Position 0: <Counter label="B" />   ← React thinks this is A updated with new props!
```

React matches by **position**, not by `label`. When A disappears, B moves from position 1 to position 0. React sees "Counter at position 0" — same type, same position — and **updates** the existing instance with new props (`label="B"`). But since React reuses the fiber... actually no.

Wait — when `showA` is false, `{false && <Counter>}` produces `false`, and `<Counter label="B">` is now the first real element. React sees that position 0 changed from `Counter` to `false` (different type), so it **unmounts** the old Counter. Position 1 had Counter B, but now Counter B is at position 0 — different position means React treats it as a new mount.

**B resets to 0** because its position in the tree changed.

**Fix: use keys**
```javascript
{showA && <Counter key="a" label="A" />}
<Counter key="b" label="B" />
```
Now React tracks by key, not position. B keeps its state.

</details>

---

## Master Cheat Sheet

```
RENDER ORDER:
  function body → useMemo → JSX → commit → refs → useLayoutEffect → paint → useEffect

PARENT-CHILD:
  Render: top-down (parent → child)
  Effects: bottom-up (child → parent)

STATE:
  setState is async (queued), not synchronous
  Functional updates (c => c+1) avoid stale closures
  React 18 batches everywhere

EFFECTS:
  useEffect = after paint (async)
  useLayoutEffect = before paint (sync, blocks)
  Cleanup runs before new effect, uses OLD closure values
  Empty deps [] = mount only
  No deps = every render

RECONCILIATION:
  Same type + same position = update (keep state)
  Different type OR different key = unmount + remount (lose state)
  key prop forces identity

CLOSURES:
  Each render = frozen snapshot
  Functions close over the snapshot they were created in
  Refs bypass closures (mutable box, same reference every render)
```
