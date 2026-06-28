# React Context API -- Provider, Consumer, Pitfalls, and Optimization

## 1. What Is Context?

Context provides a way to pass data through the component tree without manually threading props at every level. It solves the "prop drilling" problem where intermediate components receive and forward props they do not use.

```
App --> Layout --> Sidebar --> UserAvatar
```

Without context, `Layout` and `Sidebar` must accept and forward a `user` prop even though only `UserAvatar` needs it. With context, `UserAvatar` reads the user directly.

---

## 2. createContext and Provider

```jsx
const ThemeContext = React.createContext("light"); // default value

function App() {
  const [theme, setTheme] = React.useState("dark");

  return (
    <ThemeContext.Provider value={theme}>
      <Toolbar />
      <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
        Toggle
      </button>
    </ThemeContext.Provider>
  );
}
```

### Key points

- `createContext(defaultValue)` creates a context object.
- The `defaultValue` is used **only** when a component calls `useContext` and there is **no** matching `Provider` above it in the tree.
- `Provider` accepts a single `value` prop. This is what consumers receive.

---

## 3. Consuming Context

### 3.1 useContext (preferred)

```jsx
function Toolbar() {
  const theme = React.useContext(ThemeContext);
  return <div className={`toolbar-${theme}`}>Toolbar</div>;
}
```

### 3.2 Context.Consumer (legacy, class components)

```jsx
function Toolbar() {
  return (
    <ThemeContext.Consumer>
      {(theme) => <div className={`toolbar-${theme}`}>{theme}</div>}
    </ThemeContext.Consumer>
  );
}
```

`useContext` is cleaner and works in function components. `Consumer` is still useful in class components or when you need to consume multiple contexts without nesting hooks.

---

## 4. Common Use Cases

| Use Case | What goes in Context |
|----------|---------------------|
| Theme | `"light"` / `"dark"` string or full theme object |
| Authentication | `{ user, login, logout }` |
| Locale / i18n | `"en"`, `"fr"`, translation function |
| Feature flags | `{ darkMode: true, betaUI: false }` |
| Toast / notification system | `{ show, hide }` functions |

---

## 5. The Re-Render Problem

This is the most important interview topic around Context.

**Rule: When a Provider's `value` changes (by reference), every component that calls `useContext` for that context re-renders -- regardless of whether the specific piece of data they use actually changed.**

```jsx
const AppContext = React.createContext();

function App() {
  const [user, setUser] = React.useState("Alice");
  const [theme, setTheme] = React.useState("dark");

  return (
    <AppContext.Provider value={{ user, theme }}>
      <UserDisplay />
      <ThemeDisplay />
      <button onClick={() => setTheme("light")}>Change theme</button>
    </AppContext.Provider>
  );
}

function UserDisplay() {
  const { user } = React.useContext(AppContext);
  console.log("UserDisplay render");
  return <div>{user}</div>;
}

function ThemeDisplay() {
  const { theme } = React.useContext(AppContext);
  console.log("ThemeDisplay render");
  return <div>{theme}</div>;
}
```

When the user clicks "Change theme":
- Both `UserDisplay` and `ThemeDisplay` re-render.
- Even though `user` did not change, `UserDisplay` re-renders because the provider `value` is a **new object** on every render.
- `React.memo` on the consumer **does not help** -- `useContext` bypasses memo.

---

## 6. Optimization Strategies

### 6.1 Split Contexts

Separate unrelated data into different contexts.

```jsx
const UserContext = React.createContext();
const ThemeContext = React.createContext();

function App() {
  const [user, setUser] = React.useState("Alice");
  const [theme, setTheme] = React.useState("dark");

  return (
    <UserContext.Provider value={user}>
      <ThemeContext.Provider value={theme}>
        <UserDisplay />
        <ThemeDisplay />
      </ThemeContext.Provider>
    </UserContext.Provider>
  );
}
```

Now changing theme does not re-render `UserDisplay`.

### 6.2 Memoize the Provider Value

```jsx
function App() {
  const [user, setUser] = React.useState("Alice");
  const [theme, setTheme] = React.useState("dark");

  const value = React.useMemo(() => ({ user, theme }), [user, theme]);

  return (
    <AppContext.Provider value={value}>
      <Children />
    </AppContext.Provider>
  );
}
```

This prevents unnecessary reference changes when the parent re-renders for reasons unrelated to `user` or `theme`. However, it does **not** solve the problem of `UserDisplay` re-rendering when only `theme` changes -- for that, you need split contexts or selectors.

### 6.3 Selector Libraries

`use-context-selector` allows consuming only a slice of context.

```jsx
import { createContext, useContextSelector } from "use-context-selector";

const AppContext = createContext();

function UserDisplay() {
  const user = useContextSelector(AppContext, (v) => v.user);
  console.log("UserDisplay render"); // only when user changes
  return <div>{user}</div>;
}
```

### 6.4 Separate State and Dispatch Contexts

A common pattern with `useReducer`:

```jsx
const StateContext = React.createContext();
const DispatchContext = React.createContext();

function AppProvider({ children }) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  return (
    <DispatchContext.Provider value={dispatch}>
      <StateContext.Provider value={state}>
        {children}
      </StateContext.Provider>
    </DispatchContext.Provider>
  );
}
```

Components that only dispatch actions (e.g., buttons) consume `DispatchContext` and never re-render when state changes because `dispatch` identity is stable.

---

## 7. Nested Providers

A context can have multiple providers at different levels. The consumer reads from the **nearest** provider above it.

```jsx
const ThemeContext = React.createContext("light");

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Outer />
      <ThemeContext.Provider value="blue">
        <Inner />
      </ThemeContext.Provider>
    </ThemeContext.Provider>
  );
}

function Outer() {
  const theme = React.useContext(ThemeContext);
  return <div>Outer: {theme}</div>; // "dark"
}

function Inner() {
  const theme = React.useContext(ThemeContext);
  return <div>Inner: {theme}</div>; // "blue"
}
```

This pattern is useful for overriding themes or configurations in sub-trees.

---

## 8. Default Value Behavior

```jsx
const LangContext = React.createContext("en");

function Greeting() {
  const lang = React.useContext(LangContext);
  return <div>Language: {lang}</div>;
}

function App() {
  return <Greeting />; // No Provider wrapping Greeting
}
```

Output: `Language: en`. The default value `"en"` is used because there is no `LangContext.Provider` in the ancestor tree.

**Common mistake:** passing `undefined` as the default and expecting it to be `null`. `createContext()` with no argument gives `undefined`.

---

## 9. Context vs Prop Drilling vs State Management

| | Prop Drilling | Context | External State (Redux, Zustand) |
|---|---|---|---|
| Complexity | Low | Medium | Higher |
| Refactoring | Painful across many layers | Easy to add/remove consumers | Easy |
| Performance | Optimal (no extra wrappers) | Re-render all consumers on change | Fine-grained subscriptions |
| DevTools | Props visible naturally | React DevTools shows context | Dedicated devtools |
| When to use | Shallow trees (2-3 levels) | Medium apps, theme/auth/locale | Large apps, frequent updates, derived state |

**Interview guidance:** Context is NOT a state management replacement. It is a dependency injection mechanism. It is great for low-frequency, broadly-needed data. For high-frequency updates (e.g., cursor position, animation frames), prefer external state or refs.

---

## 10. Full Provider Pattern with Auth

```jsx
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("/api/me")
      .then((r) => r.json())
      .then((data) => {
        setUser(data.user);
        setLoading(false);
      });
  }, []);

  const login = async (credentials) => {
    const res = await fetch("/api/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    const data = await res.json();
    setUser(data.user);
  };

  const logout = () => {
    fetch("/api/logout", { method: "POST" });
    setUser(null);
  };

  const value = React.useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
```

The `useAuth` custom hook enforces correct usage and provides a clean API.

---

## 11. Output-Based Interview Questions

### Question 1: Provider value is an inline object -- how many re-renders?

```jsx
const Ctx = React.createContext();

function Parent() {
  const [count, setCount] = React.useState(0);

  return (
    <Ctx.Provider value={{ name: "Alice" }}>
      <Child />
      <button onClick={() => setCount(count + 1)}>Inc</button>
    </Ctx.Provider>
  );
}

const Child = React.memo(function Child() {
  const val = React.useContext(Ctx);
  console.log("Child render");
  return <div>{val.name}</div>;
});
```

**User clicks the button 3 times. How many times does "Child render" print (after initial)?**

**Answer:**
**3 times.** Every time `Parent` re-renders (due to `count` changing), a new `{ name: "Alice" }` object is created as the provider value. Even though the content is identical, the reference is different, so React considers the context value changed. `React.memo` on `Child` does NOT prevent re-renders triggered by context changes -- `useContext` is a direct subscription that bypasses memo.

**Fix:** Memoize the value:
```jsx
const value = React.useMemo(() => ({ name: "Alice" }), []);
```

---

### Question 2: useContext without Provider -- what happens?

```jsx
const ColorContext = React.createContext("red");

function Box() {
  const color = React.useContext(ColorContext);
  console.log(color);
  return <div style={{ color }}>{color}</div>;
}

function App() {
  return <Box />;
}
```

**What is logged?**

**Answer:**
`"red"`. When no `Provider` exists in the tree, `useContext` returns the **default value** passed to `createContext`. There is no error, no warning. This is by design -- the default value acts as a fallback.

---

### Question 3: Nested providers -- which value wins?

```jsx
const NumContext = React.createContext(0);

function App() {
  return (
    <NumContext.Provider value={1}>
      <NumContext.Provider value={2}>
        <NumContext.Provider value={3}>
          <Display />
        </NumContext.Provider>
      </NumContext.Provider>
    </NumContext.Provider>
  );
}

function Display() {
  const num = React.useContext(NumContext);
  console.log(num);
  return <span>{num}</span>;
}
```

**What is logged?**

**Answer:**
`3`. `useContext` reads from the **nearest** (closest ancestor) Provider. The innermost Provider has `value={3}`, so that is what `Display` receives.

---

### Question 4: Context with undefined vs missing Provider

```jsx
const Ctx = React.createContext("fallback");

function App() {
  return (
    <Ctx.Provider value={undefined}>
      <Child />
    </Ctx.Provider>
  );
}

function Child() {
  const val = React.useContext(Ctx);
  console.log(val);
  return <div>{String(val)}</div>;
}
```

**What is logged?**

**Answer:**
`undefined`. A `Provider` **is** present, so the default value (`"fallback"`) is **not** used. The Provider's `value` is explicitly `undefined`, and that is what the consumer receives. This is a common gotcha -- the default value only applies when there is **no Provider at all**, not when the Provider's value happens to be `undefined`.

---

### Question 5: Does context change trigger re-render in children that do NOT consume it?

```jsx
const Ctx = React.createContext("a");

function App() {
  const [val, setVal] = React.useState("a");

  return (
    <Ctx.Provider value={val}>
      <Parent />
      <button onClick={() => setVal("b")}>Change</button>
    </Ctx.Provider>
  );
}

const Parent = React.memo(function Parent() {
  console.log("Parent render");
  return <GrandChild />;
});

function GrandChild() {
  const v = React.useContext(Ctx);
  console.log("GrandChild render", v);
  return <div>{v}</div>;
}
```

**User clicks the button. What logs?**

**Answer:**
```
GrandChild render b
```

`Parent` does NOT log because it is wrapped in `React.memo` and receives no props that changed. However, `GrandChild` DOES re-render because it calls `useContext(Ctx)`. Context changes propagate directly to the consumer, skipping memoized intermediate components. React "punches through" memo boundaries for context updates.

---

### Question 6: Multiple contexts consumed in one component

```jsx
const A = React.createContext("a");
const B = React.createContext("b");

function App() {
  const [valA, setValA] = React.useState("a");
  const [valB, setValB] = React.useState("b");

  return (
    <A.Provider value={valA}>
      <B.Provider value={valB}>
        <Display />
        <button onClick={() => setValA("a2")}>Change A</button>
      </B.Provider>
    </A.Provider>
  );
}

function Display() {
  const a = React.useContext(A);
  const b = React.useContext(B);
  console.log("render", a, b);
  return <div>{a} {b}</div>;
}
```

**User clicks "Change A". How many times does Display render?**

**Answer:**
**Once**, logging `render a2 b`. The component re-renders because one of its consumed contexts changed. Both `useContext` calls execute during that single render, reading the latest values. There is no "double render" for consuming two contexts -- the re-render is triggered once and reads all contexts in that pass.

---

## 12. Pitfalls Summary

1. **Inline object as Provider value** causes re-renders on every parent render. Always memoize.
2. **Putting everything in one context** means every consumer re-renders on any change. Split contexts by update frequency.
3. **Expecting `React.memo` to block context re-renders** -- it does not. `useContext` bypasses memo.
4. **Confusing default value with Provider value** -- default is only used when no Provider exists.
5. **Using context for high-frequency updates** (mouse position, scroll offset) -- causes widespread re-renders. Use refs or external stores instead.
6. **Forgetting to wrap the app in a Provider** -- consumers silently get the default value, leading to subtle bugs.

---

## 13. Summary

- Context is a dependency injection tool, not a state manager.
- The default value is only used when no Provider wraps the consumer.
- Nested Providers override outer ones -- nearest wins.
- The biggest performance pitfall is re-rendering all consumers on any value change.
- Fix it by splitting contexts, memoizing values, or using selector libraries.
- Separate state context from dispatch context when using with `useReducer`.
