# useReducer -- Complex State, Dispatch Stability, and Patterns

## 1. The Reducer Pattern

The reducer pattern originates from functional programming and was popularized in the React ecosystem by Redux. A **reducer** is a pure function that takes the current state and an action, and returns a new state.

```
(state, action) => newState
```

Key properties of a reducer:
- **Pure:** no side effects, no API calls, no mutations.
- **Deterministic:** same inputs always produce the same output.
- **Synchronous:** returns the new state immediately.

---

## 2. useReducer Basics

```jsx
const initialState = { count: 0 };

function reducer(state, action) {
  switch (action.type) {
    case "increment":
      return { count: state.count + 1 };
    case "decrement":
      return { count: state.count - 1 };
    case "reset":
      return initialState;
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function Counter() {
  const [state, dispatch] = React.useReducer(reducer, initialState);

  return (
    <div>
      <span>{state.count}</span>
      <button onClick={() => dispatch({ type: "increment" })}>+</button>
      <button onClick={() => dispatch({ type: "decrement" })}>-</button>
      <button onClick={() => dispatch({ type: "reset" })}>Reset</button>
    </div>
  );
}
```

### API

```jsx
const [state, dispatch] = useReducer(reducer, initialArg, init?);
```

| Parameter | Description |
|-----------|-------------|
| `reducer` | `(state, action) => newState` function |
| `initialArg` | Initial state value (or argument to `init`) |
| `init` | Optional lazy initializer function |

---

## 3. Dispatch Function Stability

**Critical interview point:** `dispatch` has a **stable identity**. It never changes between renders. This is guaranteed by React.

```jsx
function Counter() {
  const [state, dispatch] = React.useReducer(reducer, { count: 0 });

  React.useEffect(() => {
    console.log("Effect runs only once");
    const id = setInterval(() => {
      dispatch({ type: "increment" }); // safe -- dispatch never changes
    }, 1000);
    return () => clearInterval(id);
  }, [dispatch]); // dispatch is stable, so this is equivalent to []

  return <div>{state.count}</div>;
}
```

Because `dispatch` is stable:
- You can safely include it in dependency arrays without causing re-runs.
- You can pass it to child components wrapped in `React.memo` without causing unnecessary re-renders.
- You can use it inside `setTimeout`, `setInterval`, or async callbacks without stale closure issues.

Compare this with `useState`'s setter, which is also stable. The advantage of `dispatch` is that you do not need the current state in the closure -- the reducer receives it.

---

## 4. Action Patterns

### 4.1 Type + Payload

The standard pattern:

```jsx
dispatch({ type: "SET_NAME", payload: "Alice" });

function reducer(state, action) {
  switch (action.type) {
    case "SET_NAME":
      return { ...state, name: action.payload };
    // ...
  }
}
```

### 4.2 Action Creators

Functions that return action objects, reducing typos and centralizing logic:

```jsx
const setName = (name) => ({ type: "SET_NAME", payload: name });
const setAge = (age) => ({ type: "SET_AGE", payload: age });

dispatch(setName("Alice"));
dispatch(setAge(30));
```

### 4.3 Multiple Fields in One Action

```jsx
dispatch({
  type: "UPDATE_FORM",
  payload: { field: "email", value: "a@b.com" },
});

function reducer(state, action) {
  switch (action.type) {
    case "UPDATE_FORM":
      return {
        ...state,
        [action.payload.field]: action.payload.value,
      };
    // ...
  }
}
```

---

## 5. Complex State with useReducer

`useReducer` shines when state has multiple related fields or complex transitions.

```jsx
const initialState = {
  status: "idle",    // "idle" | "loading" | "success" | "error"
  data: null,
  error: null,
};

function fetchReducer(state, action) {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, status: "loading", error: null };
    case "FETCH_SUCCESS":
      return { status: "success", data: action.payload, error: null };
    case "FETCH_ERROR":
      return { status: "error", data: null, error: action.payload };
    default:
      return state;
  }
}

function UserProfile({ userId }) {
  const [state, dispatch] = React.useReducer(fetchReducer, initialState);

  React.useEffect(() => {
    dispatch({ type: "FETCH_START" });
    fetch(`/api/users/${userId}`)
      .then((r) => r.json())
      .then((data) => dispatch({ type: "FETCH_SUCCESS", payload: data }))
      .catch((err) => dispatch({ type: "FETCH_ERROR", payload: err.message }));
  }, [userId]);

  if (state.status === "loading") return <div>Loading...</div>;
  if (state.status === "error") return <div>Error: {state.error}</div>;
  if (state.status === "success") return <div>{state.data.name}</div>;
  return null;
}
```

With `useState`, you would need three separate state variables and carefully coordinate their updates to avoid impossible states (e.g., `loading: true` and `error: "something"`). The reducer makes state transitions explicit and prevents invalid combinations.

---

## 6. useReducer vs useState -- Decision Matrix

| Criterion | useState | useReducer |
|-----------|----------|------------|
| Number of state fields | 1-2 | 3+ related fields |
| State transitions | Simple (direct set) | Complex (state machines, dependent fields) |
| Next state depends on prev | Functional updater works | Natural fit |
| Testing | Test the component | Test the reducer in isolation |
| Debugging | Inspect state | Log every action |
| Performance | Same | Same (dispatch is also stable) |
| Boilerplate | Less | More |

**Rule of thumb:** if you find yourself calling multiple `setState` calls together and they depend on each other, switch to `useReducer`.

---

## 7. Combining useReducer with Context (Mini-Redux)

This is a very common interview pattern.

```jsx
const TodoContext = React.createContext();

function todoReducer(state, action) {
  switch (action.type) {
    case "ADD":
      return [...state, { id: Date.now(), text: action.payload, done: false }];
    case "TOGGLE":
      return state.map((t) =>
        t.id === action.payload ? { ...t, done: !t.done } : t
      );
    case "DELETE":
      return state.filter((t) => t.id !== action.payload);
    default:
      return state;
  }
}

function TodoProvider({ children }) {
  const [todos, dispatch] = React.useReducer(todoReducer, []);
  const value = React.useMemo(() => ({ todos, dispatch }), [todos]);

  return <TodoContext.Provider value={value}>{children}</TodoContext.Provider>;
}

function useTodos() {
  const ctx = React.useContext(TodoContext);
  if (!ctx) throw new Error("useTodos must be inside TodoProvider");
  return ctx;
}

function TodoList() {
  const { todos, dispatch } = useTodos();
  return (
    <ul>
      {todos.map((t) => (
        <li key={t.id}>
          <span
            style={{ textDecoration: t.done ? "line-through" : "none" }}
            onClick={() => dispatch({ type: "TOGGLE", payload: t.id })}
          >
            {t.text}
          </span>
          <button onClick={() => dispatch({ type: "DELETE", payload: t.id })}>
            X
          </button>
        </li>
      ))}
    </ul>
  );
}

function AddTodo() {
  const { dispatch } = useTodos();
  const [text, setText] = React.useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        dispatch({ type: "ADD", payload: text });
        setText("");
      }}
    >
      <input value={text} onChange={(e) => setText(e.target.value)} />
      <button type="submit">Add</button>
    </form>
  );
}
```

### Optimization: separate state and dispatch contexts

```jsx
const TodoStateContext = React.createContext();
const TodoDispatchContext = React.createContext();

function TodoProvider({ children }) {
  const [todos, dispatch] = React.useReducer(todoReducer, []);

  return (
    <TodoDispatchContext.Provider value={dispatch}>
      <TodoStateContext.Provider value={todos}>
        {children}
      </TodoStateContext.Provider>
    </TodoDispatchContext.Provider>
  );
}
```

Now `AddTodo` can consume only `TodoDispatchContext` and will not re-render when the todo list changes (because `dispatch` is stable and the context value never changes).

---

## 8. Lazy Initialization

The third argument to `useReducer` is an `init` function. It receives `initialArg` and returns the actual initial state. This is useful for:

1. Expensive initial state computation.
2. Deriving initial state from props.
3. Providing a clean "reset" action.

```jsx
function init(initialCount) {
  return { count: initialCount };
}

function reducer(state, action) {
  switch (action.type) {
    case "increment":
      return { count: state.count + 1 };
    case "reset":
      return init(action.payload); // re-run init for clean reset
    default:
      return state;
  }
}

function Counter({ startAt }) {
  const [state, dispatch] = React.useReducer(reducer, startAt, init);

  return (
    <div>
      <span>{state.count}</span>
      <button onClick={() => dispatch({ type: "increment" })}>+</button>
      <button onClick={() => dispatch({ type: "reset", payload: startAt })}>
        Reset
      </button>
    </div>
  );
}
```

Without lazy initialization, the initial state object is created on every render (though only used on the first). With `init`, React calls the function only once during the initial render.

---

## 9. Immer with useReducer

Writing immutable state updates can be verbose. Immer lets you write "mutative" code that produces immutable updates under the hood.

```jsx
import { produce } from "immer";

const initialState = {
  users: [
    { id: 1, name: "Alice", scores: [90, 85] },
    { id: 2, name: "Bob", scores: [70, 80] },
  ],
};

function reducer(state, action) {
  return produce(state, (draft) => {
    switch (action.type) {
      case "ADD_SCORE": {
        const user = draft.users.find((u) => u.id === action.payload.userId);
        if (user) user.scores.push(action.payload.score);
        break;
      }
      case "RENAME": {
        const user = draft.users.find((u) => u.id === action.payload.userId);
        if (user) user.name = action.payload.name;
        break;
      }
    }
  });
}
```

Without Immer, the `ADD_SCORE` case would require:

```jsx
case "ADD_SCORE":
  return {
    ...state,
    users: state.users.map((u) =>
      u.id === action.payload.userId
        ? { ...u, scores: [...u.scores, action.payload.score] }
        : u
    ),
  };
```

Immer is especially valuable for deeply nested state.

---

## 10. Reducer Best Practices

1. **Always handle the default case.** Either return `state` (safe) or throw an error (strict, catches typos).
2. **Keep reducers pure.** No API calls, no `Date.now()`, no random values. Pass those as action payloads.
3. **Colocate related state.** If fields always change together, they belong in the same reducer.
4. **Use TypeScript discriminated unions** for actions to get exhaustive checking.
5. **Test reducers independently.** They are pure functions -- the easiest thing to unit test.

```js
// Pure unit test -- no React needed
test("increment", () => {
  const result = reducer({ count: 0 }, { type: "increment" });
  expect(result).toEqual({ count: 1 });
});
```

---

## 11. Output-Based Interview Questions

### Question 1: dispatch in setTimeout -- is dispatch stable?

```jsx
function Counter() {
  const [state, dispatch] = React.useReducer(
    (s, a) => (a === "inc" ? { count: s.count + 1 } : s),
    { count: 0 }
  );

  const handleClick = () => {
    setTimeout(() => {
      dispatch("inc");
      dispatch("inc");
      dispatch("inc");
    }, 1000);
  };

  console.log("render", state.count);
  return <button onClick={handleClick}>Go</button>;
}
```

**User clicks the button once. After 1 second, what logs?**

**Answer:**
```
render 3
```

All three dispatches execute. Each one calls the reducer with the **latest** state (not a stale closure value), so the count goes 0 -> 1 -> 2 -> 3. In React 18, the three dispatches inside `setTimeout` are batched into a single re-render, so you see one log: `render 3`. In React 17, you would see three separate renders: `render 1`, `render 2`, `render 3`.

`dispatch` is stable -- it works correctly inside `setTimeout` without needing to capture state in a closure. The reducer always receives the current state.

---

### Question 2: Reducer returns same state reference -- does component re-render?

```jsx
function reducer(state, action) {
  switch (action.type) {
    case "noop":
      return state; // same reference
    case "copy":
      return { ...state }; // new reference, same data
    default:
      return state;
  }
}

function App() {
  const [state, dispatch] = React.useReducer(reducer, { x: 1 });
  console.log("render");

  return (
    <div>
      <button onClick={() => dispatch({ type: "noop" })}>Noop</button>
      <button onClick={() => dispatch({ type: "copy" })}>Copy</button>
    </div>
  );
}
```

**User clicks "Noop" then "Copy". What logs (after initial render)?**

**Answer:**
- Clicking **Noop**: no additional log. React uses `Object.is` to compare the old and new state. Since the reducer returns the exact same reference, React **bails out** and does not re-render.
- Clicking **Copy**: logs `render`. Even though the data is identical, `{ ...state }` creates a **new object reference**, and `Object.is(oldState, newState)` returns `false`, so React re-renders.

**Takeaway:** Return the same state reference from a reducer when no change is needed to avoid unnecessary renders. Never spread state for a "no change" case.

---

### Question 3: Multiple dispatches in one handler -- batching behavior

```jsx
function reducer(state, action) {
  console.log("reducer", action.type, state.count);
  switch (action.type) {
    case "inc":
      return { count: state.count + 1 };
    default:
      return state;
  }
}

function App() {
  const [state, dispatch] = React.useReducer(reducer, { count: 0 });
  console.log("render", state.count);

  const handleClick = () => {
    dispatch({ type: "inc" });
    dispatch({ type: "inc" });
    dispatch({ type: "inc" });
  };

  return <button onClick={handleClick}>{state.count}</button>;
}
```

**User clicks the button once. What is the full console output (React 18)?**

**Answer:**
```
reducer inc 0
reducer inc 1
reducer inc 2
render 3
```

Each `dispatch` call **immediately** invokes the reducer to compute the next state. The reducer runs three times with progressively updated state (0 -> 1 -> 2 -> 3). However, React **batches** the re-render -- the component renders only once with the final state `{ count: 3 }`.

This demonstrates that:
1. Reducers are called synchronously on each dispatch.
2. Each subsequent reducer call receives the result of the previous one.
3. Only one re-render occurs (batching).

---

### Question 4: useReducer with lazy init -- when does init run?

```jsx
function init(initialValue) {
  console.log("init called");
  return { count: initialValue * 2 };
}

function reducer(state, action) {
  return action.type === "inc" ? { count: state.count + 1 } : state;
}

function Counter() {
  const [state, dispatch] = React.useReducer(reducer, 5, init);
  console.log("render", state.count);

  return (
    <button onClick={() => dispatch({ type: "inc" })}>
      {state.count}
    </button>
  );
}
```

**Component mounts, then user clicks the button once. What is the full output?**

**Answer:**
```
init called
render 10
render 11
```

The `init` function is called **once** during the initial render with `initialArg` = 5, returning `{ count: 10 }`. It is NOT called again on subsequent renders or dispatches. When the user clicks, the reducer increments from 10 to 11.

If you had written `useReducer(reducer, init(5))` (no third argument), `init(5)` would be evaluated on every render (though its result would only be used on the first). The lazy init pattern avoids that wasted computation.

---

### Question 5: dispatch after unmount

```jsx
function Timer() {
  const [state, dispatch] = React.useReducer(
    (s, a) => ({ ticks: s.ticks + 1 }),
    { ticks: 0 }
  );

  React.useEffect(() => {
    const id = setInterval(() => dispatch({ type: "tick" }), 1000);
    return () => clearInterval(id);
  }, []);

  return <div>{state.ticks}</div>;
}

function App() {
  const [show, setShow] = React.useState(true);
  return (
    <div>
      {show && <Timer />}
      <button onClick={() => setShow(false)}>Hide</button>
    </div>
  );
}
```

**User clicks "Hide" after 2 seconds. Is there a memory leak or error?**

**Answer:**
No error and no memory leak (assuming React 18). The cleanup function clears the interval when `Timer` unmounts, so `dispatch` is never called after unmount. If the cleanup were missing, `dispatch` would still not throw an error -- React silently ignores dispatches to unmounted components -- but the interval would keep running (a memory leak).

**Best practice:** Always clean up timers, subscriptions, and listeners in the `useEffect` cleanup function.

---

## 12. Pitfalls

1. **Mutating state in the reducer** -- Reducers must return new objects. `state.count++; return state;` does NOT trigger a re-render because the reference is the same.
2. **Side effects in reducers** -- Never fetch data or use `Date.now()` inside a reducer. Pass computed values as action payloads.
3. **Over-using useReducer** -- A single boolean toggle does not need a reducer. `useState` is fine.
4. **Forgetting the default case** -- Missing cases silently return `undefined`, which replaces your state with `undefined`.
5. **Inline reducer function** -- Defining the reducer inside the component works but creates a new function reference every render. This does not affect correctness but can confuse developers reading the code.

---

## 13. Summary

- `useReducer` separates state logic from the component, making complex state transitions explicit and testable.
- `dispatch` is referentially stable -- it never changes identity across renders.
- The reducer is called synchronously for each dispatch, but React batches the resulting re-renders.
- Returning the same state reference causes a render bail-out.
- Combine `useReducer` + Context for a lightweight "mini-Redux" pattern.
- Use lazy initialization (`init` function) when initial state is expensive or prop-derived.
- Immer eliminates the boilerplate of immutable updates in deeply nested state.
