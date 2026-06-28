# useRef Deep Dive — Interview Bible

## useRef as a Mutable Container

`useRef` returns a mutable object with a `.current` property that persists for the entire lifetime of the component:

```javascript
const ref = useRef(initialValue);
// ref = { current: initialValue }
```

Key characteristics:
1. **Persists across renders**: Unlike local variables, the ref object survives re-renders
2. **Does NOT trigger re-render**: Changing `ref.current` does not cause the component to re-render
3. **Synchronous access**: Always holds the latest value immediately after assignment
4. **Mutable**: You can assign any value to `ref.current`

```javascript
function Timer() {
  const countRef = useRef(0);

  const tick = () => {
    countRef.current += 1;
    console.log(countRef.current); // always latest value
    // BUT: UI does NOT update because no re-render triggered
  };

  return <button onClick={tick}>Ticks: {countRef.current}</button>;
}
```

---

## How useRef Differs from useState

| Feature | useState | useRef |
|---------|----------|--------|
| Triggers re-render | Yes | No |
| Returns | [value, setter] | { current: value } |
| Update mechanism | setState function | Direct assignment |
| Value timing | Stale until next render | Immediately available |
| Use for UI | Yes | No (not reactive) |
| Use for side-effect data | Overhead (unnecessary re-renders) | Ideal |

---

## DOM Ref Access

The primary use case for refs in React's original design — accessing DOM nodes:

```javascript
function TextInput() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current.focus(); // direct DOM API access
  };

  return (
    <div>
      <input ref={inputRef} type="text" />
      <button onClick={focusInput}>Focus</button>
    </div>
  );
}
```

React sets `ref.current` to the DOM node after mounting and sets it back to `null` before unmounting.

### Accessing Child DOM Nodes

```javascript
function Parent() {
  const childRef = useRef(null);

  return <Child ref={childRef} />;
}

// This FAILS — function components don't have instances
function Child(props) {
  return <input />;
}
```

Function components cannot receive refs directly. You need `forwardRef`.

---

## Forwarding Refs (forwardRef)

`forwardRef` allows a parent to get a ref to a DOM element inside a child component:

```javascript
const FancyInput = React.forwardRef(function FancyInput(props, ref) {
  return (
    <div className="fancy-wrapper">
      <input ref={ref} className="fancy-input" {...props} />
    </div>
  );
});

function Parent() {
  const inputRef = useRef(null);

  const handleClick = () => {
    inputRef.current.focus(); // accesses the <input> inside FancyInput
  };

  return (
    <div>
      <FancyInput ref={inputRef} placeholder="Type here..." />
      <button onClick={handleClick}>Focus</button>
    </div>
  );
}
```

The `ref` parameter only exists when you wrap with `forwardRef`. Without it, the `ref` prop is consumed by React and not passed to the component.

### React 19+ ref as prop

In React 19, `ref` can be passed as a regular prop without `forwardRef`:

```javascript
function FancyInput({ ref, ...props }) {
  return <input ref={ref} {...props} />;
}
```

---

## useImperativeHandle

Restricts what the parent can access through the ref. Instead of exposing the full DOM node, expose a custom API:

```javascript
const VideoPlayer = React.forwardRef(function VideoPlayer(props, ref) {
  const videoRef = useRef(null);

  useImperativeHandle(ref, () => ({
    play() {
      videoRef.current.play();
    },
    pause() {
      videoRef.current.pause();
    },
    get currentTime() {
      return videoRef.current.currentTime;
    }
  }), []); // dependencies for when to recreate the handle

  return <video ref={videoRef} src={props.src} />;
});

function App() {
  const playerRef = useRef(null);

  const handlePlay = () => {
    playerRef.current.play();      // works
    playerRef.current.currentTime; // works
    playerRef.current.remove();    // undefined! not exposed
  };

  return <VideoPlayer ref={playerRef} src="video.mp4" />;
}
```

Benefits:
- Encapsulation: parent cannot do unexpected DOM mutations
- Clear API contract between parent and child
- Child can change internal implementation without breaking parent

---

## Ref Callbacks

Instead of a ref object, you can pass a function:

```javascript
function MeasuredBox() {
  const [height, setHeight] = useState(0);

  const measuredRef = (node) => {
    if (node !== null) {
      setHeight(node.getBoundingClientRect().height);
    }
  };

  return (
    <div ref={measuredRef}>
      <p>This box is {height}px tall</p>
    </div>
  );
}
```

Ref callbacks are called:
- With the DOM node when the element mounts
- With `null` when the element unmounts
- On every render if the callback is a new function (use useCallback to prevent)

```javascript
// Stable ref callback (doesn't re-run on every render)
const measuredRef = useCallback((node) => {
  if (node !== null) {
    setHeight(node.getBoundingClientRect().height);
  }
}, []);
```

### React 19 Cleanup in Ref Callbacks

React 19 allows returning a cleanup function from ref callbacks:

```javascript
const ref = (node) => {
  const observer = new ResizeObserver(() => { /* ... */ });
  observer.observe(node);
  return () => observer.disconnect(); // cleanup on unmount
};
```

---

## Storing Previous Values

A common pattern using useRef to capture the previous render's value:

```javascript
function usePrevious(value) {
  const ref = useRef();

  useEffect(() => {
    ref.current = value; // updates AFTER render
  });

  return ref.current; // returns value from previous render
}

function Counter() {
  const [count, setCount] = useState(0);
  const prevCount = usePrevious(count);

  return (
    <div>
      <p>Current: {count}, Previous: {prevCount}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </div>
  );
}
```

How it works:
1. Render happens — `ref.current` still has old value (returned as "previous")
2. After render, useEffect runs and updates `ref.current` to new value
3. Next render, the cycle repeats

---

## Storing Interval/Timeout IDs

Refs are ideal for holding timer IDs because:
- Timer IDs don't affect UI (no need for re-render)
- You need the latest ID to clear it (no stale closure issue)

```javascript
function Stopwatch() {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef(null);

  const start = () => {
    if (intervalRef.current !== null) return; // prevent double-start
    intervalRef.current = setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);
  };

  const stop = () => {
    clearInterval(intervalRef.current);
    intervalRef.current = null;
  };

  const reset = () => {
    stop();
    setSeconds(0);
  };

  useEffect(() => {
    return () => clearInterval(intervalRef.current); // cleanup on unmount
  }, []);

  return (
    <div>
      <p>{seconds}s</p>
      <button onClick={start}>Start</button>
      <button onClick={stop}>Stop</button>
      <button onClick={reset}>Reset</button>
    </div>
  );
}
```

Why not `useState` for the interval ID?
- `setIntervalId(id)` would trigger an unnecessary re-render
- The interval ID is never displayed in the UI
- It's purely bookkeeping data for cleanup

---

## Ref vs State Decision Matrix

| Criterion | Use useState | Use useRef |
|-----------|-------------|------------|
| Displayed in UI | Yes | No |
| Triggers re-render needed | Yes | No |
| Compared across renders | Sometimes | Often (latest value) |
| Timer/subscription IDs | No (wasteful re-render) | Yes |
| DOM element access | No | Yes |
| Mutable counter not in UI | No | Yes |
| Previous value tracking | No | Yes |
| Form validation (live) | Yes | No |
| Animation frame ID | No | Yes |

### The Rule

If changing the value should update what the user sees -> `useState`
If changing the value should NOT update what the user sees -> `useRef`

---

## Advanced Pattern: Ref for Latest Callback

Avoid stale closures in intervals/subscriptions without re-creating them:

```javascript
function useInterval(callback, delay) {
  const savedCallback = useRef(callback);

  // Always update to latest callback
  useEffect(() => {
    savedCallback.current = callback;
  });

  useEffect(() => {
    if (delay === null) return;

    const tick = () => savedCallback.current();
    const id = setInterval(tick, delay);
    return () => clearInterval(id);
  }, [delay]); // interval only resets when delay changes
}
```

This pattern:
- Interval is set up once (or when delay changes)
- The callback it executes is always the latest version
- No stale closure: `savedCallback.current` always points to current function

---

## Output-Based Interview Questions

### Question 1: ref.current Updated in Handler — What Does Next Render Show?

```javascript
function App() {
  const [, forceRender] = useState(0);
  const countRef = useRef(0);

  const handleClick = () => {
    countRef.current += 1;
    console.log("ref:", countRef.current);
  };

  const handleRender = () => {
    forceRender(n => n + 1);
  };

  return (
    <div>
      <p>Display: {countRef.current}</p>
      <button onClick={handleClick}>Increment Ref</button>
      <button onClick={handleRender}>Force Render</button>
    </div>
  );
}
```

**User clicks "Increment Ref" 3 times, then "Force Render". What does the UI show?**

**Answer:**
- After clicking "Increment Ref" 3 times: UI still shows `Display: 0`. Changing `ref.current` does not trigger re-render. Console logs `ref: 1`, `ref: 2`, `ref: 3`.
- After clicking "Force Render": UI shows `Display: 3`. The forced re-render reads `countRef.current` which is now 3.

The ref holds the latest value immediately, but the UI only reflects it when something else causes a re-render.

---

### Question 2: forwardRef with useImperativeHandle

```javascript
const CustomInput = React.forwardRef(function CustomInput(props, ref) {
  const inputRef = useRef(null);
  const [value, setValue] = useState("");

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current.focus(),
    clear: () => setValue(""),
    getValue: () => value,
  }), [value]);

  return (
    <input
      ref={inputRef}
      value={value}
      onChange={e => setValue(e.target.value)}
    />
  );
});

function Parent() {
  const ref = useRef(null);

  const handleAction = () => {
    console.log("value:", ref.current.getValue());
    console.log("focus:", typeof ref.current.focus);
    console.log("blur:", typeof ref.current.blur);
    console.log("style:", typeof ref.current.style);
  };

  return (
    <div>
      <CustomInput ref={ref} />
      <button onClick={handleAction}>Action</button>
    </div>
  );
}
```

**What does handleAction log after typing "hello" and clicking Action?**

**Answer:**
```
value: hello
focus: function
blur: undefined
style: undefined
```

`useImperativeHandle` restricts the ref to only expose `focus`, `clear`, and `getValue`. The parent cannot access `blur`, `style`, or any other DOM properties. Only the methods explicitly returned in the imperative handle are available. `getValue()` returns "hello" because `value` is in the dependency array and the handle is recreated when value changes.

---

### Question 3: Ref vs State Timing

```javascript
function Timer() {
  const [stateCount, setStateCount] = useState(0);
  const refCount = useRef(0);

  const handleClick = () => {
    setStateCount(stateCount + 1);
    refCount.current += 1;

    console.log("state:", stateCount);       // what?
    console.log("ref:", refCount.current);   // what?
  };

  return (
    <div>
      <p>State: {stateCount}, Ref: {refCount.current}</p>
      <button onClick={handleClick}>Click</button>
    </div>
  );
}
```

**Starting from 0, what logs on first click?**

**Answer:**
```
state: 0
ref: 1
```

- `stateCount` logs `0` because setState is asynchronous — the current render's closure still has the old value
- `refCount.current` logs `1` because ref mutation is synchronous and immediately visible

After re-render, the UI shows `State: 1, Ref: 1`. But within the event handler, state is stale while ref is immediate.

---

### Question 4: useRef in useEffect Cleanup

```javascript
function WebSocket({ url }) {
  const wsRef = useRef(null);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    wsRef.current = new WebSocket(url);

    wsRef.current.onmessage = (event) => {
      setMessages(prev => [...prev, event.data]);
    };

    return () => {
      console.log("closing:", wsRef.current.url);
      wsRef.current.close();
    };
  }, [url]);

  return <div>{messages.length} messages</div>;
}
```

**If url changes from "ws://a" to "ws://b", what does cleanup log?**

**Answer:** `closing: ws://b`

This is a subtle bug. The cleanup function runs after the new effect has already executed (in React's batched execution model). Wait — actually, let's trace carefully:

1. url changes to "ws://b"
2. React re-renders the component
3. Previous effect's cleanup runs (closure has old `wsRef` reference, but `wsRef.current` has been overwritten by... no, cleanup runs BEFORE new effect)

Actually, the correct order is:
1. Render with url="ws://b"
2. Paint
3. Cleanup of old effect runs -> `wsRef.current` still points to old WebSocket("ws://a") -> logs `closing: ws://a`
4. New effect runs -> `wsRef.current` = new WebSocket("ws://b")

**Corrected Answer:** `closing: ws://a`

The cleanup closure captures `wsRef` (the ref object itself, not its current value). At cleanup time, `wsRef.current` still holds the old WebSocket because the new effect hasn't run yet. Cleanup always runs before the next effect setup.

---

### Question 5: Ref to Track Render Count

```javascript
function RenderCounter() {
  const renderCount = useRef(0);
  renderCount.current += 1;

  const [name, setName] = useState("");

  return (
    <div>
      <p>Renders: {renderCount.current}</p>
      <input value={name} onChange={e => setName(e.target.value)} />
    </div>
  );
}
```

**After typing 3 characters, what does "Renders:" show?**

**Answer:** `Renders: 4` (1 initial render + 3 re-renders from typing).

Each render increments `renderCount.current` synchronously at the top of the function. Since it's a ref, the increment persists and is immediately readable in the same render's JSX. No infinite loop because changing a ref doesn't trigger another render.

Note: In StrictMode development, you'd see double-counting (each render function called twice), showing 8 instead of 4.

---

## Common Patterns Summary

### 1. DOM Manipulation
```javascript
const ref = useRef(null);
// <input ref={ref} />
// ref.current.focus(), .scrollIntoView(), .getBoundingClientRect()
```

### 2. Store Mutable Instance Data
```javascript
const timerRef = useRef(null);
const wsRef = useRef(null);
const observerRef = useRef(null);
```

### 3. Track Previous Props/State
```javascript
const prevProps = useRef(props);
useEffect(() => { prevProps.current = props; });
```

### 4. Avoid Stale Closures
```javascript
const latestCallback = useRef(callback);
latestCallback.current = callback;
// Use latestCallback.current inside long-lived subscriptions
```

### 5. Flag for Mounted Status
```javascript
const isMounted = useRef(true);
useEffect(() => () => { isMounted.current = false; }, []);
// Check isMounted.current before async setState
```

---

## Pitfalls

| Pitfall | Consequence |
|---------|-------------|
| Rendering ref.current in JSX without re-render trigger | Stale display until something else triggers render |
| Mutating ref during render (before return) in StrictMode | Double-invocation causes double mutation |
| Assuming ref callbacks run once | Without useCallback, ref callback runs on every render |
| Reading ref.current during render for conditional logic | May not have DOM node yet (null on first render) |
| Using ref instead of state for user-visible data | UI doesn't update when value changes |

---

## Tradeoffs

### Ref vs State for Derived Data
- **State**: Reactive, UI always in sync, but causes re-renders
- **Ref**: No re-renders, but UI can become stale

### Imperative vs Declarative
- **Refs enable imperative code**: Direct DOM manipulation, focus, scroll
- **React prefers declarative**: Props/state drive UI
- Use imperative (refs) only when declarative approach is insufficient

### forwardRef + useImperativeHandle vs Lifting State
- **Imperative handle**: Clean API, encapsulated, but breaks data-flow model
- **Lifting state**: Pure React pattern, easier to reason about, but more re-renders
- Prefer lifting state; use imperative handles for DOM-focused operations (focus, scroll, animate)

---

## Interview Tips

1. Clearly distinguish ref from state: ref is a mutable escape hatch that doesn't participate in React's render cycle
2. Know the DOM ref lifecycle: set on mount, null on unmount
3. Explain forwardRef as necessary because function components have no instance
4. useImperativeHandle demonstrates understanding of encapsulation
5. The "latest callback in ref" pattern shows advanced understanding of closure problems
6. Mention React 19's simplified ref-as-prop when discussing forwardRef
7. Never suggest using ref for data that should trigger UI updates
