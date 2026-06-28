# React Fundamentals -- Interview Deep Dive

---

## 1. What Is React?

React is a **JavaScript library** for building user interfaces. It was created by Jordan Walke at Facebook (now Meta) and open-sourced in 2013. React focuses exclusively on the **view layer** -- it does not prescribe routing, state management, or HTTP libraries.

Core philosophy:

- **Declarative**: You describe *what* the UI should look like, not *how* to update the DOM.
- **Component-based**: UIs are built from small, isolated, reusable pieces.
- **Learn once, write anywhere**: The same mental model applies to web (ReactDOM), mobile (React Native), VR (React 360), etc.

---

## 2. Library vs Framework

| Aspect | Library (React) | Framework (Angular) |
|--------|----------------|---------------------|
| Control flow | You call the library | The framework calls your code (IoC) |
| Scope | View layer only | Full-stack (routing, forms, HTTP, DI) |
| Flexibility | Pick your own router, state manager | Opinionated defaults |
| Bundle size (base) | ~6 KB gzipped (react + react-dom) | ~60-90 KB gzipped |
| Learning curve | Lower initial, grows with ecosystem | Higher initial, flattens out |

**Interview pitfall**: Candidates often say "React is a framework." Interviewers specifically listen for the distinction. React is a *library* -- it manages rendering and component lifecycle, but delegates everything else to the ecosystem.

### Tradeoffs: React vs Angular vs Vue

| Concern | React | Angular | Vue |
|---------|-------|---------|-----|
| Template syntax | JSX (JS-first) | HTML templates with directives | HTML templates with directives |
| State management | External (Redux, Zustand, Jotai) | Built-in services + RxJS | Vuex / Pinia |
| TypeScript | Opt-in | First-class, mandatory in practice | Opt-in |
| Change detection | Virtual DOM diffing | Zone.js + dirty checking (or Signals) | Proxy-based reactivity |
| Opinionatedness | Low | High | Medium |
| Ecosystem fragmentation | Higher (many choices) | Lower (official packages) | Medium |

**When to choose React**: You want maximum ecosystem flexibility, a large talent pool, and you are comfortable assembling your own stack.

**When to choose Angular**: You want a batteries-included framework with strong conventions for large enterprise teams.

**When to choose Vue**: You want a gentle learning curve with built-in reactivity that sits between React's flexibility and Angular's structure.

---

## 3. The Component Model

Everything in React is a component. A component is a **function** (or class) that accepts inputs (`props`) and returns React elements describing what should appear on screen.

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}</h1>;
}
```

Components can be composed:

```jsx
function App() {
  return (
    <div>
      <Greeting name="Alice" />
      <Greeting name="Bob" />
    </div>
  );
}
```

### Component Rules

1. Component names must start with an **uppercase letter** -- lowercase tags are treated as HTML elements.
2. A component must return a single root element (or use a Fragment).
3. Components should be **pure with respect to their props** -- same props should produce the same output.

---

## 4. One-Way Data Flow (Unidirectional)

Data in React flows **downward** from parent to child through props.

```
App (state: user)
  |
  v  props: user
UserProfile
  |
  v  props: user.name
UserName
```

If a child needs to modify parent state, the parent passes a **callback** as a prop:

```jsx
function Parent() {
  const [count, setCount] = useState(0);
  return <Child count={count} onIncrement={() => setCount(c => c + 1)} />;
}

function Child({ count, onIncrement }) {
  return <button onClick={onIncrement}>Count: {count}</button>;
}
```

**Why one-way?** It makes data flow predictable and debugging easier. In two-way binding (Angular's `ngModel`), a child can silently modify parent state, making it harder to trace the source of a change.

---

## 5. Declarative vs Imperative

### Imperative (vanilla JS)

```js
const list = document.getElementById("list");
const item = document.createElement("li");
item.textContent = "New item";
list.appendChild(item);
```

You describe **every step** to manipulate the DOM.

### Declarative (React)

```jsx
function TodoList({ items }) {
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.text}</li>)}
    </ul>
  );
}
```

You describe **what** the UI should look like for a given state. React figures out *how* to update the DOM to match.

**Analogy**: Imperative is giving turn-by-turn driving directions. Declarative is giving the destination and letting the GPS figure out the route.

---

## 6. Virtual DOM Overview

The Virtual DOM (VDOM) is a **lightweight in-memory representation** of the real DOM. It is a plain JavaScript object tree.

```
Real DOM node:          Virtual DOM node (simplified):
<div id="root">        { type: 'div', props: { id: 'root' },
  <h1>Hello</h1>          children: [
</div>                       { type: 'h1', props: {}, children: ['Hello'] }
                           ]
                        }
```

### How It Works

1. **State changes** trigger a re-render of the component tree.
2. React builds a **new** VDOM tree.
3. React **diffs** the new VDOM tree against the previous one.
4. React computes the **minimal set of DOM mutations** needed.
5. React **batches** and applies those mutations to the real DOM.

### Why Not Directly Mutate the DOM?

- DOM operations are expensive (layout recalculation, paint, composite).
- Batching multiple state changes into a single DOM update is more efficient.
- The VDOM allows React to work in non-DOM environments (React Native, server rendering).

**Common misconception**: "The Virtual DOM is faster than the real DOM." This is misleading. The VDOM adds overhead (diffing, object creation). What is faster is React's **batched, minimal updates** compared to naive imperative DOM manipulation. Frameworks like Svelte and SolidJS skip the VDOM entirely and can be faster for certain workloads.

---

## 7. Reconciliation Overview

Reconciliation is the algorithm React uses to diff two VDOM trees.

### The O(n) Heuristic

A general tree diff algorithm is O(n^3). React makes two assumptions to achieve O(n):

1. **Two elements of different types produce different trees.** If a `<div>` becomes a `<span>`, React tears down the entire subtree and rebuilds it.
2. **Keys hint at stable identity across renders.** Elements with the same key are assumed to represent the same entity.

### Rules

| Scenario | React's action |
|----------|---------------|
| Same element type, same key | Update props/attributes in-place |
| Different element type | Unmount old tree, mount new tree |
| Key changed | Unmount old, mount new (even if type is the same) |
| Key stable, position changed | Reorder DOM node (no remount) |

---

## 8. React Fiber -- Introduction

React Fiber is the **reimplementation of React's core reconciliation algorithm**, shipped in React 16 (2017). The old reconciler ("Stack Reconciler") was synchronous -- once it started rendering a tree, it could not be interrupted.

### Key Concepts

- **Work unit (Fiber node)**: Each component/element is a fiber. The reconciler processes one fiber at a time.
- **Incremental rendering**: Work can be paused, resumed, or aborted.
- **Priority lanes**: Different updates have different priorities (user input > data fetching > offscreen rendering).
- **Double buffering**: React maintains two fiber trees -- `current` (what is on screen) and `workInProgress` (being built). On commit, they swap.

### Two Phases

| Phase | Can be interrupted? | Side effects? |
|-------|---------------------|--------------|
| Render phase | Yes | No (pure computation) |
| Commit phase | No | Yes (DOM mutations, refs, effects) |

**Interview insight**: Fiber is what enables Concurrent Mode features like `useTransition`, `useDeferredValue`, and Suspense boundaries. Without Fiber, these would be impossible.

---

## 9. Composition vs Inheritance

React strongly favors **composition** over inheritance.

### Composition: Containment

```jsx
function Card({ children }) {
  return <div className="card">{children}</div>;
}

function UserCard({ user }) {
  return (
    <Card>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </Card>
  );
}
```

### Composition: Specialization

```jsx
function Dialog({ title, message }) {
  return (
    <div className="dialog">
      <h2>{title}</h2>
      <p>{message}</p>
    </div>
  );
}

function WelcomeDialog() {
  return <Dialog title="Welcome" message="Thanks for visiting!" />;
}
```

### Why Not Inheritance?

- React components do not have deep class hierarchies.
- Props and composition give you all the flexibility you need.
- Inheritance creates tight coupling and makes components harder to reuse.
- The React team has stated: "We have not found any use cases where we would recommend creating component inheritance hierarchies."

---

## 10. Output-Based Interview Questions

### Question 1: What renders when a parent re-renders?

```jsx
function Parent() {
  const [count, setCount] = useState(0);
  console.log("Parent renders");

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <Child />
    </div>
  );
}

function Child() {
  console.log("Child renders");
  return <p>I am a child</p>;
}
```

**Answer**: Every time the button is clicked, **both** "Parent renders" and "Child renders" are logged. When a parent re-renders, **all** its children re-render by default, even if their props have not changed. This is a fundamental React behavior. To prevent unnecessary child re-renders, wrap `Child` in `React.memo`.

### Question 2: Does `React.memo` prevent this re-render?

```jsx
const Child = React.memo(function Child({ onClick }) {
  console.log("Child renders");
  return <button onClick={onClick}>Click</button>;
});

function Parent() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(c => c + 1)}>+</button>
      <Child onClick={() => console.log("clicked")} />
    </div>
  );
}
```

**Answer**: `Child` re-renders on every parent re-render **despite** `React.memo`. The `onClick` prop is an inline arrow function -- a **new reference** is created on every render. `React.memo` does a shallow comparison and sees a different function reference each time. Fix: wrap the callback in `useCallback`.

### Question 3: What is the output?

```jsx
function App() {
  const [show, setShow] = useState(true);

  return (
    <div>
      <button onClick={() => setShow(s => !s)}>Toggle</button>
      {show ? <Counter /> : <Counter />}
    </div>
  );
}

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}
```

**Answer**: Clicking toggle does **not** reset the counter. Both branches render `<Counter />` at the same position in the tree with the same type. React sees the same component type at the same position and **preserves the state**. To force a reset, add different `key` props: `<Counter key="a" />` vs `<Counter key="b" />`.

---

## 11. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "React is a framework" | React is a UI library. You need additional libraries for routing, state management, etc. |
| "Virtual DOM is always faster" | VDOM adds diffing overhead. Svelte/SolidJS skip it and can outperform React in benchmarks. |
| "Components only re-render when props change" | Components re-render whenever their parent re-renders, regardless of props. |
| "React re-renders the whole page" | React only updates the DOM nodes that actually changed after diffing. |
| "useState is like this.state" | `useState` captures state per render (closure). Class `this.state` is mutable and always current. |
| "Hooks replaced lifecycle methods" | Hooks provide a different mental model (synchronization, not lifecycle). `useEffect` is not `componentDidMount`. |

---

## 12. Frequently Asked Interview Questions

1. **Why is React declarative?** You describe the desired UI for a given state. React handles the DOM mutations.
2. **What problem does the component model solve?** Encapsulation, reusability, and separation of concerns.
3. **Why one-way data flow?** Predictability and easier debugging.
4. **What is the role of the key prop?** It gives elements a stable identity for the reconciliation algorithm.
5. **Can you use React without JSX?** Yes. JSX compiles to `React.createElement` calls. You can write those directly.
6. **What is the difference between React and ReactDOM?** `React` provides the component model and VDOM logic. `ReactDOM` handles rendering to the browser DOM. This separation allows React to target other platforms (React Native).

---

## 13. Summary Cheat Sheet

```
React = Library (not framework)
Data flow = One-way (parent -> child via props)
Rendering = Declarative (describe what, not how)
VDOM = JS object tree diffed against previous version
Reconciliation = O(n) diff using type + key heuristics
Fiber = Incremental, interruptible reconciler (React 16+)
Composition > Inheritance (always)
Re-render = Parent re-renders => children re-render (unless memoized)
```

---
