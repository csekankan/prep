# Custom Hooks -- Reusable Logic, Patterns, and Testing

## 1. What Are Custom Hooks?

A custom hook is a JavaScript function whose name starts with `use` and that calls other hooks. It lets you extract and share stateful logic between components without changing the component hierarchy.

```jsx
function useWindowWidth() {
  const [width, setWidth] = React.useState(window.innerWidth);

  React.useEffect(() => {
    const handler = () => setWidth(window.innerWidth);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return width;
}

function Header() {
  const width = useWindowWidth();
  return <h1>{width > 768 ? "Desktop" : "Mobile"}</h1>;
}
```

### Rules for Custom Hooks

1. **Must start with `use`** -- This is how React's linter identifies hooks. Without the prefix, the linter cannot enforce the Rules of Hooks (no conditional calls, etc.).
2. **Can call other hooks** -- `useState`, `useEffect`, `useRef`, other custom hooks.
3. **Each call gets its own state** -- Two components calling the same custom hook do NOT share state. Each gets an independent copy.

---

## 2. Custom Hooks vs Utility Functions

| Custom Hook | Utility Function |
|-------------|-----------------|
| Calls React hooks internally | Pure computation, no hooks |
| Starts with `use` | Any name |
| Tied to component lifecycle | Stateless, can be called anywhere |
| Returns reactive values | Returns static values |

```jsx
// Utility function -- no hooks, pure logic
function formatCurrency(amount, currency = "USD") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

// Custom hook -- uses React state/effects
function useCurrencyFormatter(currency) {
  const formatter = React.useMemo(
    () => new Intl.NumberFormat("en-US", { style: "currency", currency }),
    [currency]
  );
  return (amount) => formatter.format(amount);
}
```

**Rule of thumb:** if the function does not call any hook, do NOT prefix it with `use`.

---

## 3. Hook Composition

Custom hooks can call other custom hooks, enabling layered abstractions.

```jsx
function useDebounce(value, delay) {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function useSearchResults(query) {
  const debouncedQuery = useDebounce(query, 300);
  const [results, setResults] = React.useState([]);

  React.useEffect(() => {
    if (!debouncedQuery) {
      setResults([]);
      return;
    }
    fetch(`/api/search?q=${debouncedQuery}`)
      .then((r) => r.json())
      .then(setResults);
  }, [debouncedQuery]);

  return results;
}
```

`useSearchResults` composes `useDebounce` internally. The consumer never needs to know about debouncing.

---

## 4. Closure Behavior in Custom Hooks

Custom hooks capture values from the render in which they execute, just like any function component code. This creates closures that can be stale if not managed.

```jsx
function useInterval(callback, delay) {
  const savedCallback = React.useRef(callback);

  React.useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  React.useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
```

Why the ref? If we passed `callback` directly to `setInterval`, the interval would capture the callback from the first render and never see updated state. The ref always points to the latest callback.

---

## 5. Full Implementations of Useful Custom Hooks

### 5.1 useLocalStorage

Persists state to `localStorage` and syncs across tabs.

```jsx
function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = React.useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item !== null ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = React.useCallback(
    (value) => {
      setStoredValue((prev) => {
        const nextValue = typeof value === "function" ? value(prev) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(nextValue));
        } catch {
          // quota exceeded or private browsing
        }
        return nextValue;
      });
    },
    [key]
  );

  React.useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === key && e.newValue !== null) {
        setStoredValue(JSON.parse(e.newValue));
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [key]);

  return [storedValue, setValue];
}

// Usage
function Settings() {
  const [theme, setTheme] = useLocalStorage("theme", "light");
  return (
    <button onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
      Current: {theme}
    </button>
  );
}
```

**Key design decisions:**
- Lazy initializer avoids reading `localStorage` on every render.
- `useCallback` on the setter prevents unnecessary child re-renders.
- Listens to `storage` events for cross-tab sync.
- Try/catch handles private browsing and quota limits.

---

### 5.2 useFetch

A generic data fetching hook with loading, error, and abort support.

```jsx
function useFetch(url) {
  const [state, setState] = React.useState({
    data: null,
    loading: true,
    error: null,
  });

  React.useEffect(() => {
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((err) => {
        if (err.name !== "AbortError") {
          setState({ data: null, loading: false, error: err.message });
        }
      });

    return () => controller.abort();
  }, [url]);

  return state;
}

// Usage
function UserProfile({ userId }) {
  const { data, loading, error } = useFetch(`/api/users/${userId}`);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  return <div>{data.name}</div>;
}
```

**Key design decisions:**
- `AbortController` cancels in-flight requests on URL change or unmount.
- Distinguishes abort errors from real errors.
- Resets to loading state when URL changes.

---

### 5.3 usePrevious

Captures the value from the previous render.

```jsx
function usePrevious(value) {
  const ref = React.useRef();

  React.useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

// Usage
function Counter() {
  const [count, setCount] = React.useState(0);
  const prevCount = usePrevious(count);

  return (
    <div>
      <p>Now: {count}, Before: {prevCount}</p>
      <button onClick={() => setCount(count + 1)}>+</button>
    </div>
  );
}
```

**How it works:** During render, `ref.current` still holds the old value (the effect has not run yet). After render, the effect updates `ref.current` to the new value. On the next render, `ref.current` is the "previous" value.

---

### 5.4 useOnClickOutside

Detects clicks outside a referenced element. Commonly used for dropdowns, modals, and popovers.

```jsx
function useOnClickOutside(ref, handler) {
  React.useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [ref, handler]);
}

// Usage
function Dropdown() {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef();

  useOnClickOutside(ref, () => setOpen(false));

  return (
    <div ref={ref}>
      <button onClick={() => setOpen(!open)}>Toggle</button>
      {open && <ul><li>Option 1</li><li>Option 2</li></ul>}
    </div>
  );
}
```

**Pitfall:** The `handler` should be stable (wrapped in `useCallback`) to avoid re-attaching listeners on every render.

---

### 5.5 useMediaQuery

Responds to CSS media query changes.

```jsx
function useMediaQuery(query) {
  const [matches, setMatches] = React.useState(() => {
    return window.matchMedia(query).matches;
  });

  React.useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    setMatches(mql.matches);
    return () => mql.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

// Usage
function Layout() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");

  return (
    <div className={prefersDark ? "dark" : "light"}>
      {isMobile ? <MobileNav /> : <DesktopNav />}
    </div>
  );
}
```

---

### 5.6 useDebounce

Delays updating a value until a specified time has passed since the last change.

```jsx
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = React.useState(value);

  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage
function SearchBar() {
  const [query, setQuery] = React.useState("");
  const debouncedQuery = useDebounce(query, 300);

  React.useEffect(() => {
    if (debouncedQuery) {
      console.log("Searching for:", debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

---

### 5.7 useToggle

Simple boolean state toggle.

```jsx
function useToggle(initialValue = false) {
  const [value, setValue] = React.useState(initialValue);

  const toggle = React.useCallback(() => setValue((v) => !v), []);
  const setTrue = React.useCallback(() => setValue(true), []);
  const setFalse = React.useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse };
}

// Usage
function Modal() {
  const { value: isOpen, toggle, setFalse: close } = useToggle();

  return (
    <div>
      <button onClick={toggle}>Toggle Modal</button>
      {isOpen && (
        <div className="modal">
          <p>Content</p>
          <button onClick={close}>Close</button>
        </div>
      )}
    </div>
  );
}
```

---

## 6. Testing Custom Hooks

### 6.1 Using renderHook from React Testing Library

```jsx
import { renderHook, act } from "@testing-library/react";

test("useToggle toggles value", () => {
  const { result } = renderHook(() => useToggle(false));

  expect(result.current.value).toBe(false);

  act(() => {
    result.current.toggle();
  });

  expect(result.current.value).toBe(true);

  act(() => {
    result.current.setFalse();
  });

  expect(result.current.value).toBe(false);
});
```

### 6.2 Testing hooks with dependencies

```jsx
test("useDebounce delays value update", async () => {
  jest.useFakeTimers();

  const { result, rerender } = renderHook(
    ({ value, delay }) => useDebounce(value, delay),
    { initialProps: { value: "hello", delay: 500 } }
  );

  expect(result.current).toBe("hello");

  rerender({ value: "world", delay: 500 });
  expect(result.current).toBe("hello"); // not yet updated

  act(() => {
    jest.advanceTimersByTime(500);
  });

  expect(result.current).toBe("world"); // now updated

  jest.useRealTimers();
});
```

### 6.3 Testing hooks with context

```jsx
test("useTodos adds a todo", () => {
  const wrapper = ({ children }) => <TodoProvider>{children}</TodoProvider>;
  const { result } = renderHook(() => useTodos(), { wrapper });

  act(() => {
    result.current.dispatch({ type: "ADD", payload: "Buy milk" });
  });

  expect(result.current.todos).toHaveLength(1);
  expect(result.current.todos[0].text).toBe("Buy milk");
});
```

**Key testing principles:**
- Wrap state updates in `act()`.
- Use `rerender` to test how hooks respond to prop changes.
- Use `wrapper` to provide context.
- Use fake timers for time-dependent hooks.

---

## 7. Shared State Misconception

This is the most common misunderstanding about custom hooks.

```jsx
function useCounter() {
  const [count, setCount] = React.useState(0);
  return { count, increment: () => setCount((c) => c + 1) };
}

function ComponentA() {
  const { count, increment } = useCounter();
  return <button onClick={increment}>A: {count}</button>;
}

function ComponentB() {
  const { count } = useCounter();
  return <div>B: {count}</div>;
}
```

**Clicking the button in ComponentA does NOT update ComponentB.** Each component calling `useCounter` gets its **own** independent `useState`. Custom hooks share **logic**, not **state**.

To share state, you need to lift it up (props, context, or external store).

---

## 8. Hook Execution Order

Hooks must be called in the same order on every render. React identifies hooks by their position in the call sequence.

```jsx
function useBoth(flag) {
  // BUG: conditional hook call
  if (flag) {
    React.useState(0); // hook 1 (sometimes)
  }
  React.useState(""); // hook 2 (or hook 1 if flag is false)
}
```

This violates the Rules of Hooks and causes React to map state to the wrong hook. The ESLint plugin `react-hooks/rules-of-hooks` catches this.

---

## 9. Output-Based Interview Questions

### Question 1: Do two components share state from the same custom hook?

```jsx
function useCount() {
  const [count, setCount] = React.useState(0);
  return [count, () => setCount((c) => c + 1)];
}

function A() {
  const [count, inc] = useCount();
  return <button onClick={inc}>A: {count}</button>;
}

function B() {
  const [count] = useCount();
  return <div>B: {count}</div>;
}

function App() {
  return (
    <>
      <A />
      <B />
    </>
  );
}
```

**User clicks A's button 3 times. What does each component display?**

**Answer:**
- A displays: `A: 3`
- B displays: `B: 0`

Each component gets its own independent `useState` instance. Custom hooks share **logic** (the code), not **state** (the data). B's count remains 0 because it has its own state that was never incremented.

---

### Question 2: Hook execution order across renders

```jsx
function useLogger(label) {
  React.useEffect(() => {
    console.log("mount", label);
    return () => console.log("unmount", label);
  }, [label]);
}

function App() {
  const [show, setShow] = React.useState(true);

  useLogger("App");

  return (
    <div>
      {show && <Child />}
      <button onClick={() => setShow(false)}>Hide</button>
    </div>
  );
}

function Child() {
  useLogger("Child");
  return <div>Child</div>;
}
```

**On initial mount, what logs? Then user clicks "Hide" -- what logs?**

**Answer:**
Initial mount:
```
mount App
mount Child
```

After clicking "Hide":
```
unmount Child
```

Effects fire bottom-up (children before parents) during mount, but the logs appear in the order React commits them. When `Child` unmounts, its cleanup runs. `App` does NOT re-run its effect because `label` ("App") did not change, and `App` did not unmount.

---

### Question 3: Custom hook returning a new object every render

```jsx
function useUser() {
  const [name, setName] = React.useState("Alice");
  return { name, setName }; // new object every render
}

const Profile = React.memo(function Profile({ user }) {
  console.log("Profile render");
  return <div>{user.name}</div>;
});

function App() {
  const user = useUser();
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <Profile user={user} />
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
    </div>
  );
}
```

**User clicks the count button. Does Profile re-render?**

**Answer:**
**Yes, Profile re-renders.** Even though `React.memo` wraps `Profile`, the `user` prop is a new object on every render (because `useUser` returns `{ name, setName }` -- a fresh object). `React.memo` does a shallow comparison and sees a different reference, so it re-renders.

**Fix:** Memoize the return value inside the hook:

```jsx
function useUser() {
  const [name, setName] = React.useState("Alice");
  return React.useMemo(() => ({ name, setName }), [name]);
}
```

---

### Question 4: useEffect cleanup in a custom hook

```jsx
function useDocumentTitle(title) {
  React.useEffect(() => {
    const prevTitle = document.title;
    document.title = title;
    return () => {
      document.title = prevTitle;
    };
  }, [title]);
}

function Page() {
  const [count, setCount] = React.useState(0);
  useDocumentTitle(`Count: ${count}`);

  return <button onClick={() => setCount(count + 1)}>Click</button>;
}
```

**User clicks the button twice (count goes 0 -> 1 -> 2). What does document.title end up as? What would document.title be if the component unmounts after that?**

**Answer:**
After two clicks, `document.title` is `"Count: 2"`.

If the component unmounts, the cleanup function runs and restores `document.title` to the `prevTitle` captured in the **last** effect call. The last effect captured `prevTitle = "Count: 1"` (the title before setting it to "Count: 2"). So after unmount, `document.title` becomes `"Count: 1"`.

Wait -- this is subtle. Let us trace carefully:

1. Mount: effect runs. `prevTitle` = original page title (say `"React App"`). Sets title to `"Count: 0"`.
2. Click (count=1): cleanup runs, restores to `"React App"`. Then new effect runs. `prevTitle` = `"React App"`. Sets title to `"Count: 1"`.
3. Click (count=2): cleanup runs, restores to `"React App"`. Then new effect runs. `prevTitle` = `"React App"`. Sets title to `"Count: 2"`.
4. Unmount: cleanup runs, restores to `"React App"`.

**Corrected answer:** After unmount, `document.title` is `"React App"` (the original title). Each cleanup captures `prevTitle` as whatever `document.title` was **before** the effect set it. Since cleanup runs first (restoring the title) and then the new effect sets it, `prevTitle` in each effect is always the restored original title.

This is a common interview trick question to test understanding of effect cleanup ordering.

---

### Question 5: Conditional hook call

```jsx
function useConditional(flag) {
  if (flag) {
    const [val, setVal] = React.useState("yes");
    return val;
  }
  return "no";
}

function App() {
  const [flag, setFlag] = React.useState(true);
  const result = useConditional(flag);

  return (
    <div>
      <span>{result}</span>
      <button onClick={() => setFlag(false)}>Switch</button>
    </div>
  );
}
```

**What happens when the user clicks "Switch"?**

**Answer:**
**React throws an error.** On the first render, `useConditional(true)` calls `useState` (1 hook call). When `flag` becomes `false`, `useConditional(false)` calls 0 hooks. React detects that fewer hooks were called than on the previous render and throws: _"Rendered fewer hooks than expected."_

This violates the Rules of Hooks. Hooks must be called unconditionally and in the same order on every render.

**Fix:** Always call the hook, use the flag to decide what to return:
```jsx
function useConditional(flag) {
  const [val] = React.useState("yes");
  return flag ? val : "no";
}
```

---

## 10. Advanced Patterns

### 10.1 Returning Refs from Hooks (Callback Ref Pattern)

```jsx
function useMeasure() {
  const [rect, setRect] = React.useState(null);

  const ref = React.useCallback((node) => {
    if (node !== null) {
      setRect(node.getBoundingClientRect());
    }
  }, []);

  return [ref, rect];
}

function MeasuredBox() {
  const [ref, rect] = useMeasure();
  return (
    <div ref={ref}>
      {rect && <span>Width: {rect.width}px</span>}
    </div>
  );
}
```

### 10.2 Hook Factories

Functions that return custom hooks, parameterized at creation time.

```jsx
function createResourceHook(fetchFn) {
  return function useResource(id) {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
      setLoading(true);
      fetchFn(id).then((result) => {
        setData(result);
        setLoading(false);
      });
    }, [id]);

    return { data, loading };
  };
}

const useUser = createResourceHook((id) =>
  fetch(`/api/users/${id}`).then((r) => r.json())
);

const usePost = createResourceHook((id) =>
  fetch(`/api/posts/${id}`).then((r) => r.json())
);
```

---

## 11. Pitfalls

1. **Not starting with `use`** -- The linter cannot enforce Rules of Hooks. React will not treat it as a hook internally.
2. **Assuming shared state** -- Two components calling the same hook get independent state.
3. **Returning unstable references** -- New objects/arrays on every call defeat `React.memo` on consumers. Memoize return values.
4. **Missing dependencies in internal effects** -- The custom hook's `useEffect` has the same dependency rules. The `exhaustive-deps` lint rule catches this.
5. **Overabstracting** -- Not everything needs to be a hook. If logic is stateless and does not interact with the React lifecycle, a plain function is simpler and testable without `renderHook`.
6. **Conditional hook calls** -- Even inside custom hooks, calling hooks conditionally breaks React's internal bookkeeping.

---

## 12. Summary

- Custom hooks extract and reuse stateful logic. They share code, not state.
- Follow the `use` prefix convention and the Rules of Hooks (no conditional calls).
- Compose hooks by calling custom hooks inside other custom hooks.
- Manage closures carefully with refs (e.g., `useInterval`, `useOnClickOutside`).
- Memoize return values to avoid defeating `React.memo` in consumers.
- Test with `renderHook` from React Testing Library, wrapping updates in `act()`.
- Common patterns: `useLocalStorage`, `useFetch`, `useDebounce`, `usePrevious`, `useOnClickOutside`, `useMediaQuery`, `useToggle`.
- A utility function that does not call hooks should NOT be named with the `use` prefix.
