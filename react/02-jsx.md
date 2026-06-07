# JSX -- Interview Deep Dive

---

## 1. What Is JSX?

JSX stands for **JavaScript XML**. It is a syntax extension for JavaScript that looks like HTML but lives inside JS files. JSX is **not valid JavaScript** -- it must be transformed by a compiler (Babel, TypeScript, SWC, esbuild) before the browser can execute it.

```jsx
const element = <h1 className="title">Hello, world</h1>;
```

This is syntactic sugar. It compiles to a function call.

---

## 2. What JSX Compiles To

### Classic Transform (React 16 and earlier)

```jsx
// JSX
const element = <h1 className="title">Hello</h1>;

// Compiles to
const element = React.createElement("h1", { className: "title" }, "Hello");
```

`React.createElement(type, props, ...children)` returns a plain JavaScript object (a "React element"):

```js
{
  type: "h1",
  props: {
    className: "title",
    children: "Hello"
  },
  key: null,
  ref: null,
  $$typeof: Symbol.for("react.element")
}
```

The `$$typeof` symbol is a security measure -- it prevents JSON injection attacks because `Symbol` values cannot be serialized in JSON.

### New JSX Transform (React 17+)

React 17 introduced an automatic JSX runtime. You no longer need `import React from 'react'` in every file.

```jsx
// JSX
const element = <h1 className="title">Hello</h1>;

// Compiles to (automatic runtime)
import { jsx as _jsx } from "react/jsx-runtime";
const element = _jsx("h1", { className: "title", children: "Hello" });
```

**Interview question**: "Why did React 17 introduce the new JSX transform?"
**Answer**: (1) Eliminates the need to import React in every file. (2) Slight bundle size reduction. (3) Future optimizations that are hard with `createElement`.

---

## 3. Babel Transformation Details

Babel uses the `@babel/plugin-transform-react-jsx` plugin. You can configure it to use the classic or automatic runtime:

```json
{
  "presets": [
    ["@babel/preset-react", {
      "runtime": "automatic"
    }]
  ]
}
```

### Nested Elements

```jsx
const element = (
  <div>
    <h1>Title</h1>
    <p>Body</p>
  </div>
);

// Compiles to (classic)
const element = React.createElement(
  "div",
  null,
  React.createElement("h1", null, "Title"),
  React.createElement("p", null, "Body")
);
```

### Component Elements

```jsx
const element = <MyComponent name="Alice" />;

// Compiles to
const element = React.createElement(MyComponent, { name: "Alice" });
```

Notice: HTML tags compile with a **string** type (`"div"`), while components compile with a **function/class reference** (`MyComponent`). This is why component names must start with an uppercase letter -- lowercase names are treated as HTML tags.

---

## 4. JSX Expressions

You can embed any JavaScript expression inside JSX using curly braces `{}`.

```jsx
const name = "Alice";
const element = <h1>Hello, {name}</h1>;
```

### What Counts as an Expression?

```jsx
// Valid -- these are expressions
{2 + 2}
{user.name}
{formatDate(new Date())}
{isLoggedIn ? "Welcome" : "Please log in"}
{items.map(item => <li key={item.id}>{item.text}</li>)}

// Invalid -- these are statements, not expressions
{if (condition) { return "yes"; }}   // Use ternary instead
{for (let i = 0; i < 5; i++) {}}    // Use .map() instead
```

---

## 5. Conditional Rendering Patterns

### Pattern 1: Ternary Operator

```jsx
function Greeting({ isLoggedIn }) {
  return (
    <div>
      {isLoggedIn ? <UserGreeting /> : <GuestGreeting />}
    </div>
  );
}
```

### Pattern 2: Logical AND (&&)

```jsx
function Mailbox({ unreadMessages }) {
  return (
    <div>
      <h1>Messages</h1>
      {unreadMessages.length > 0 && (
        <p>You have {unreadMessages.length} unread messages.</p>
      )}
    </div>
  );
}
```

**DANGER**: The `&&` pattern has a well-known gotcha with falsy values (see Section 9).

### Pattern 3: Early Return

```jsx
function AdminPanel({ user }) {
  if (!user.isAdmin) {
    return null;
  }

  return <div>Admin controls here</div>;
}
```

### Pattern 4: Variable Assignment

```jsx
function StatusIcon({ status }) {
  let icon;
  if (status === "success") icon = <CheckIcon />;
  else if (status === "error") icon = <ErrorIcon />;
  else icon = <SpinnerIcon />;

  return <div>{icon}</div>;
}
```

### Pattern 5: IIFE (avoid in production code)

```jsx
function Example() {
  return (
    <div>
      {(() => {
        if (condition) return <A />;
        return <B />;
      })()}
    </div>
  );
}
```

---

## 6. JSX vs Template Literals

| Aspect | JSX | Template literals / Template engines |
|--------|-----|--------------------------------------|
| Language | JavaScript (expressions) | String-based with special syntax |
| Type safety | Full (with TypeScript) | Limited or none |
| Tooling | Linting, autocomplete, refactoring | Varies |
| Logic | Any JS expression | Framework-specific directives (`v-if`, `*ngIf`) |
| Output | React element objects | Strings (must be parsed to DOM) |

JSX is **not** a template language. It is JavaScript with syntactic sugar. This means you get the full power of JavaScript (map, filter, ternary, variables) without learning a separate directive syntax.

---

## 7. Fragments

Fragments let you group children without adding an extra DOM node.

### Long Syntax

```jsx
import { Fragment } from "react";

function Columns() {
  return (
    <Fragment>
      <td>Column 1</td>
      <td>Column 2</td>
    </Fragment>
  );
}
```

### Short Syntax

```jsx
function Columns() {
  return (
    <>
      <td>Column 1</td>
      <td>Column 2</td>
    </>
  );
}
```

### When You Need the Long Syntax

The short syntax `<>` does not support attributes. If you need a `key`, use the full form:

```jsx
function Glossary({ items }) {
  return (
    <dl>
      {items.map(item => (
        <Fragment key={item.id}>
          <dt>{item.term}</dt>
          <dd>{item.description}</dd>
        </Fragment>
      ))}
    </dl>
  );
}
```

**Interview tip**: "Can you put a key on a Fragment?" Yes, but only with the `<Fragment>` syntax, not `<>`.

---

## 8. JSX Spread Attributes

You can spread an object as props:

```jsx
function App() {
  const props = { firstName: "Alice", lastName: "Smith", age: 30 };
  return <UserCard {...props} />;
}

// Equivalent to
<UserCard firstName="Alice" lastName="Smith" age={30} />
```

### Overriding Spread Props

Order matters -- later props override earlier ones:

```jsx
const defaults = { variant: "primary", size: "medium" };

<Button {...defaults} size="large" />
// variant = "primary", size = "large" (overridden)

<Button size="large" {...defaults} />
// variant = "primary", size = "medium" (spread overrides explicit)
```

### Forwarding All Props

```jsx
function WrappedInput(props) {
  return <input className="styled-input" {...props} />;
}
```

**Pitfall**: Spreading all props can pass unintended HTML attributes to DOM elements, causing React warnings. Use destructuring to extract known props:

```jsx
function WrappedInput({ label, ...rest }) {
  return (
    <div>
      <label>{label}</label>
      <input {...rest} />
    </div>
  );
}
```

---

## 9. Boolean, Null, and Undefined Rendering Rules

React **does not render** the following values -- they produce no visible output:

- `true`
- `false`
- `null`
- `undefined`

```jsx
<div>{true}</div>    // Renders: <div></div>
<div>{false}</div>   // Renders: <div></div>
<div>{null}</div>    // Renders: <div></div>
<div>{undefined}</div> // Renders: <div></div>
```

### The Falsy Value Trap

The `&&` operator does NOT convert its left operand to boolean. It returns the left operand if it is falsy.

```jsx
function MessageCount({ count }) {
  return (
    <div>
      {count && <p>You have {count} messages</p>}
    </div>
  );
}
```

**What happens when `count` is `0`?**

`0 && <p>...</p>` evaluates to `0`. React **renders `0`** as text. The user sees a lone "0" on the screen.

**Fix**: Use an explicit boolean comparison:

```jsx
{count > 0 && <p>You have {count} messages</p>}
// or
{count ? <p>You have {count} messages</p> : null}
// or
{!!count && <p>You have {count} messages</p>}
```

### Other Falsy Values

| Value | Rendered? | What appears? |
|-------|----------|--------------|
| `false` | No | Nothing |
| `null` | No | Nothing |
| `undefined` | No | Nothing |
| `0` | **Yes** | "0" |
| `""` (empty string) | **Yes** | "" (nothing visible, but an empty text node) |
| `NaN` | **Yes** | "NaN" |

---

## 10. Output-Based Interview Questions

### Question 1: What does this render?

```jsx
function App() {
  const items = [];
  return (
    <div>
      {items.length && <ul>{items.map(i => <li key={i}>{i}</li>)}</ul>}
    </div>
  );
}
```

**Answer**: Renders `<div>0</div>`. `items.length` is `0`, which is falsy. The `&&` operator returns `0`, and React renders `0` as text. This is the classic `&&` gotcha.

### Question 2: What does this render?

```jsx
function App() {
  return (
    <div>
      <p>A</p>
      {false}
      {null}
      {undefined}
      {true}
      <p>B</p>
    </div>
  );
}
```

**Answer**: Renders `<div><p>A</p><p>B</p></div>`. All four values (`false`, `null`, `undefined`, `true`) are ignored by React. Only the two `<p>` tags appear.

### Question 3: Spot the bug

```jsx
function UserList({ users }) {
  return (
    <ul>
      {users.map(user => (
        <li>
          {user.name} - {user.isActive && "Active"}
        </li>
      ))}
    </ul>
  );
}
```

**Answer**: Two issues: (1) Missing `key` prop on `<li>` -- React will warn. (2) If `user.isActive` is `false`, `false && "Active"` returns `false`, which React does not render -- this is actually fine. But if `isActive` were `0` instead of `false`, it would render "0".

### Question 4: What does this JSX compile to?

```jsx
<div>
  <MyComponent />
  <my-component />
</div>
```

**Answer**:

```js
React.createElement("div", null,
  React.createElement(MyComponent, null),   // component reference
  React.createElement("my-component", null) // string (custom HTML element)
);
```

`MyComponent` (uppercase) is treated as a component. `my-component` (lowercase) is treated as an HTML custom element and compiled with a string type.

### Question 5: What renders?

```jsx
function App() {
  const name = undefined;
  return <h1>Hello, {name}!</h1>;
}
```

**Answer**: Renders `<h1>Hello, !</h1>`. `undefined` is not rendered, but the surrounding text ("Hello, " and "!") still appears. There is no error.

### Question 6: What is the output?

```jsx
function App() {
  return (
    <div>
      {"" && <span>Shown</span>}
    </div>
  );
}
```

**Answer**: Renders `<div></div>` (empty div). `""` is falsy, so `&&` returns `""`. React renders an empty string as an empty text node -- nothing visible appears. This is different from `0`, which *is* visible.

---

## 11. JSX Key Gotchas

### Self-Closing Tags Are Required

In HTML, `<img>` and `<input>` do not need to be closed. In JSX, **all tags must be closed**:

```jsx
// Valid JSX
<img src="photo.jpg" />
<input type="text" />
<br />

// Invalid JSX (will not compile)
<img src="photo.jpg">
<input type="text">
```

### `className` Instead of `class`

```jsx
// JSX
<div className="container">...</div>

// NOT
<div class="container">...</div>  // Works but triggers a warning
```

### `htmlFor` Instead of `for`

```jsx
<label htmlFor="email">Email</label>
<input id="email" type="email" />
```

### Style Is an Object

```jsx
// JSX
<div style={{ backgroundColor: "red", fontSize: "16px" }}>...</div>

// NOT a string like HTML
<div style="background-color: red">...</div>  // Error!
```

### Event Handlers Are camelCase

```jsx
<button onClick={handleClick}>Click</button>   // camelCase
// NOT
<button onclick={handleClick}>Click</button>    // wrong
```

### Inline Expressions Must Be Expressions

```jsx
// This does NOT work -- if is a statement
<div>{if (x) { "hello" }}</div>

// Use a ternary (expression)
<div>{x ? "hello" : null}</div>
```

---

## 12. Advanced: JSX Namespaced Components

You can use dot notation for component namespacing:

```jsx
const Form = {
  Input: function Input(props) {
    return <input {...props} />;
  },
  Label: function Label({ children }) {
    return <label>{children}</label>;
  },
};

function App() {
  return (
    <div>
      <Form.Label>Name</Form.Label>
      <Form.Input type="text" name="username" />
    </div>
  );
}
```

This pattern is useful for component libraries where related components share a namespace.

---

## 13. Pitfalls Summary

| Pitfall | Explanation |
|---------|-------------|
| `0 && <Component />` renders "0" | Use `> 0 &&` or ternary |
| Forgetting `key` in `.map()` | React warns and reconciliation suffers |
| Lowercase component names | Treated as HTML elements, not components |
| `style` as a string | Must be an object with camelCase properties |
| `class` instead of `className` | Works but triggers a console warning |
| Forgetting to close self-closing tags | JSX requires `/>` on void elements |
| Nesting `<p>` inside `<p>` | Invalid HTML; React + browser will break the DOM |
| Returning multiple root elements | Use a Fragment (`<>...</>`) |

---

## 14. Summary Cheat Sheet

```
JSX = Syntactic sugar for React.createElement()
Babel / SWC / esbuild = Compilers that transform JSX
New transform (React 17+) = Auto-imports jsx runtime, no manual React import needed
Expressions in {} = Any valid JS expression (not statements)
Conditional rendering = Ternary, &&, early return, variable assignment
Fragments = <> or <Fragment> to avoid extra DOM nodes
Spread = {...props} forwards all properties, order matters
Rendered: 0, NaN, strings
Not rendered: false, null, undefined, true
Key gotcha: && with 0 renders "0"
```

---
