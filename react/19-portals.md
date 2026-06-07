# 19. React Portals

## Table of Contents

1. [What Are Portals?](#what-are-portals)
2. [createPortal API](#createportal-api)
3. [When to Use Portals](#when-to-use-portals)
4. [Event Bubbling Through Portals](#event-bubbling-through-portals)
5. [Portals and Context](#portals-and-context)
6. [Full Modal Implementation](#full-modal-implementation)
7. [Tooltip Implementation](#tooltip-implementation)
8. [Accessibility Considerations](#accessibility-considerations)
9. [Portals with SSR](#portals-with-ssr)
10. [z-index and Stacking Context](#z-index-and-stacking-context)
11. [Portal Cleanup](#portal-cleanup)
12. [Pitfalls and Tradeoffs](#pitfalls-and-tradeoffs)
13. [Output-Based Questions](#output-based-questions)

---

## What Are Portals?

A portal lets you render a child component into a **different DOM node** than its parent, while keeping it in the **same React tree**.

Normally, everything you render in a component goes into its parent's DOM node:

```
React Tree:              DOM Tree:
<App>                    <div id="root">
  <Parent>                 <div class="parent">
    <Child />                <div class="child" />   <-- same place
  </Parent>                </div>
</App>                   </div>
```

With a portal, the DOM placement differs from the React tree:

```
React Tree:              DOM Tree:
<App>                    <div id="root">
  <Parent>                 <div class="parent">
    <Child /> (portal)       <!-- Child is NOT here -->
  </Parent>                </div>
</App>                   </div>
                         <div id="modal-root">
                           <div class="child" />   <-- rendered HERE
                         </div>
```

---

## createPortal API

```jsx
import { createPortal } from 'react-dom';

function MyComponent() {
  return createPortal(
    <div>I render somewhere else in the DOM</div>,
    document.getElementById('modal-root')
  );
}
```

### Signature

```
createPortal(child, container, key?)
```

| Parameter | Type | Description |
|---|---|---|
| `child` | ReactNode | Any renderable React content (elements, strings, fragments) |
| `container` | DOM Element | The actual DOM node to render into |
| `key` | string (optional) | Used when rendering multiple portals to the same container |

### Basic Example

```html
<!-- index.html -->
<body>
  <div id="root"></div>
  <div id="portal-root"></div>
</body>
```

```jsx
import { createPortal } from 'react-dom';

function Overlay({ children }) {
  return createPortal(
    <div className="overlay">{children}</div>,
    document.getElementById('portal-root')
  );
}

function App() {
  const [show, setShow] = useState(false);
  return (
    <div>
      <button onClick={() => setShow(true)}>Open</button>
      {show && (
        <Overlay>
          <p>This renders in #portal-root, not #root</p>
          <button onClick={() => setShow(false)}>Close</button>
        </Overlay>
      )}
    </div>
  );
}
```

---

## When to Use Portals

### Modals / Dialogs

The most common use case. Modals need to visually overlay the entire page, but they are logically "owned" by a deeply nested component.

Without a portal, the modal is trapped inside its parent's `overflow: hidden`, `z-index`, or `transform` stacking context. The portal frees it from these CSS constraints by rendering at the top level of the DOM.

### Tooltips

Tooltips must appear above all other content. If a tooltip is rendered inside a container with `overflow: hidden`, it gets clipped. A portal avoids this.

### Dropdown Menus

Same problem as tooltips. A dropdown inside an `overflow: auto` container will be cut off. Portals let the dropdown escape.

### Toast Notifications

Toasts appear in a fixed position (e.g., bottom-right corner) regardless of where the triggering component lives. A portal renders them into a dedicated container.

### When NOT to Use Portals

- Simple child components that don't need to escape CSS constraints
- Components that don't need to overlay other content
- When you can solve the problem with CSS alone (`z-index`, `position: fixed`)

---

## Event Bubbling Through Portals

This is the most interview-critical topic about portals.

### The Rule

Events from a portal bubble through the **React tree** (logical parent), NOT the **DOM tree** (physical parent).

Even though the portal's DOM node is outside its React parent's DOM node, React events still bubble to the React parent. This is because React implements its own synthetic event system on top of the real DOM events.

### Demonstration

```jsx
function Parent() {
  const handleClick = () => {
    console.log("Parent caught click!");
  };

  return (
    <div onClick={handleClick}>
      <p>I am the parent</p>
      <PortalChild />
    </div>
  );
}

function PortalChild() {
  return createPortal(
    <button>Click me (I'm in a portal)</button>,
    document.getElementById('portal-root')
  );
}
```

**When you click the portal button:**

- **DOM perspective**: The `<button>` is inside `#portal-root`, which is a sibling of `#root`. The click event bubbles from `button -> #portal-root -> body`. It does NOT pass through the `<div onClick={handleClick}>` in the DOM.
- **React perspective**: `PortalChild` is a child of `Parent` in the React tree. React's synthetic event system bubbles the click through the React tree: `button -> PortalChild -> Parent's div`. So `handleClick` FIRES.

```
DOM Tree:                        React Tree:
<body>                           <Parent>
  <div id="root">                  <div onClick={handleClick}>
    <div onClick={handleClick}>      <p>I am the parent</p>
      <p>I am the parent</p>        <PortalChild>          <-- React parent
    </div>                             <button>Click me</button>  <-- event bubbles UP React tree
  </div>                           </PortalChild>
  <div id="portal-root">          </div>
    <button>Click me</button>    </Parent>
  </div>
</body>

Button click:
  DOM bubbling:   button -> #portal-root -> body  (misses the div with onClick)
  React bubbling: button -> PortalChild -> div (handleClick FIRES!)
```

### Why This Matters

This behavior enables:
- A parent form can catch `onSubmit` from a portal modal's form
- A parent `onClick` handler on a container catches clicks inside portals
- `stopPropagation()` in a portal stops propagation in the React tree, not the DOM tree

This trips people up because they expect DOM bubbling, but React uses its own event system.

---

## Portals and Context

Context providers work through the React tree, not the DOM tree. Since portals remain in the React tree, they have access to all ancestor contexts.

```jsx
const ThemeContext = createContext('light');

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Dashboard />
    </ThemeContext.Provider>
  );
}

function Dashboard() {
  const [showModal, setShowModal] = useState(false);
  return (
    <div>
      <button onClick={() => setShowModal(true)}>Open Modal</button>
      {showModal && <ModalPortal onClose={() => setShowModal(false)} />}
    </div>
  );
}

function ModalPortal({ onClose }) {
  const theme = useContext(ThemeContext); // "dark" -- works through portal!

  return createPortal(
    <div className={`modal ${theme}`}>
      <p>Theme is: {theme}</p>
      <button onClick={onClose}>Close</button>
    </div>,
    document.getElementById('modal-root')
  );
}
```

Even though the modal's DOM is in `#modal-root` (completely outside `#root`), it still reads `ThemeContext` from its React ancestor. This is one of the most powerful aspects of portals.

### This Also Works With

- Redux `<Provider>` -- portals can `useSelector`/`useDispatch`
- React Router -- portals can use `useNavigate`, `useParams`
- Any custom context provider higher in the React tree

---

## Full Modal Implementation

A production-quality modal with portal, accessibility, and cleanup:

```jsx
import { createPortal } from 'react-dom';
import { useEffect, useRef, useCallback } from 'react';

function Modal({ isOpen, onClose, title, children }) {
  const modalRef = useRef(null);
  const previousActiveElement = useRef(null);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }
    if (e.key === 'Tab') {
      trapFocus(e, modalRef.current);
    }
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return;

    previousActiveElement.current = document.activeElement;
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeyDown);
    modalRef.current?.focus();

    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
      previousActiveElement.current?.focus();
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className="modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabIndex={-1}
      >
        <header className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="modal-close"
          >
            X
          </button>
        </header>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>,
    document.getElementById('modal-root')
  );
}

function trapFocus(event, container) {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (event.shiftKey && document.activeElement === firstElement) {
    lastElement.focus();
    event.preventDefault();
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    firstElement.focus();
    event.preventDefault();
  }
}
```

### Usage

```jsx
function App() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Open Modal</button>
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Action"
      >
        <p>Are you sure you want to proceed?</p>
        <button onClick={() => setIsOpen(false)}>Cancel</button>
        <button onClick={() => { doAction(); setIsOpen(false); }}>Confirm</button>
      </Modal>
    </div>
  );
}
```

### What This Implementation Handles

- **Backdrop click to close**: clicking outside the modal closes it
- **Escape key to close**: keyboard shortcut
- **Focus trap**: Tab cycles only through focusable elements inside the modal
- **Focus restoration**: when modal closes, focus returns to the trigger button
- **Scroll lock**: body scroll is disabled while modal is open
- **ARIA attributes**: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- **Portal rendering**: modal escapes CSS constraints of parent components

---

## Tooltip Implementation

```jsx
import { createPortal } from 'react-dom';
import { useState, useRef, useLayoutEffect } from 'react';

function Tooltip({ children, text }) {
  const [show, setShow] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef(null);

  useLayoutEffect(() => {
    if (!show || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPosition({
      top: rect.top - 8 + window.scrollY,
      left: rect.left + rect.width / 2 + window.scrollX,
    });
  }, [show]);

  return (
    <>
      <span
        ref={triggerRef}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onFocus={() => setShow(true)}
        onBlur={() => setShow(false)}
        tabIndex={0}
        aria-describedby={show ? 'tooltip' : undefined}
      >
        {children}
      </span>
      {show && createPortal(
        <div
          id="tooltip"
          role="tooltip"
          className="tooltip"
          style={{
            position: 'absolute',
            top: position.top,
            left: position.left,
            transform: 'translate(-50%, -100%)',
          }}
        >
          {text}
        </div>,
        document.body
      )}
    </>
  );
}
```

### Usage

```jsx
function App() {
  return (
    <div style={{ overflow: 'hidden', height: 200 }}>
      <Tooltip text="This tooltip escapes overflow: hidden!">
        <button>Hover me</button>
      </Tooltip>
    </div>
  );
}
```

Without the portal, the tooltip would be clipped by the parent's `overflow: hidden`. With the portal, it renders on `document.body` and appears above everything.

### Why useLayoutEffect for Positioning

`useLayoutEffect` runs synchronously after DOM mutations but before the browser paints. This prevents a visual "jump" where the tooltip briefly appears at (0, 0) before moving to the correct position. `useEffect` would cause that flicker.

---

## Accessibility Considerations

### Modals

| Requirement | How to Implement |
|---|---|
| Focus trap | Tab should cycle within the modal |
| Focus management | Focus modal on open, restore on close |
| Escape to close | `keydown` listener for Escape key |
| `aria-modal="true"` | Tells assistive technology this is modal |
| `role="dialog"` | Identifies the element as a dialog |
| `aria-labelledby` | Points to the modal's title |
| Background inert | Use `inert` attribute on the rest of the page |

### The `inert` Attribute

```jsx
useEffect(() => {
  if (!isOpen) return;
  const root = document.getElementById('root');
  root.setAttribute('inert', '');
  return () => root.removeAttribute('inert');
}, [isOpen]);
```

`inert` makes the entire `#root` div non-interactive and invisible to screen readers while the modal is open. This is the modern replacement for `aria-hidden="true"` on the background.

### Tooltips

- Use `role="tooltip"` on the tooltip element
- Use `aria-describedby` on the trigger, pointing to the tooltip's id
- Ensure the tooltip is keyboard-accessible (show on focus, not just hover)

---

## Portals with SSR

Portals require a DOM element as the `container` argument. During server-side rendering, `document` does not exist.

### Problem

```jsx
function Modal({ children }) {
  // CRASHES during SSR: document is not defined
  return createPortal(children, document.getElementById('modal-root'));
}
```

### Solutions

**Option 1: Guard with typeof check**

```jsx
function Modal({ children }) {
  if (typeof document === 'undefined') return null;
  return createPortal(children, document.getElementById('modal-root'));
}
```

**Option 2: Create container lazily with useEffect**

```jsx
function Modal({ children }) {
  const [container, setContainer] = useState(null);

  useEffect(() => {
    let el = document.getElementById('modal-root');
    if (!el) {
      el = document.createElement('div');
      el.id = 'modal-root';
      document.body.appendChild(el);
    }
    setContainer(el);
  }, []);

  if (!container) return null;
  return createPortal(children, container);
}
```

**Option 3: Use a ref to track if mounted**

```jsx
function useIsMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}

function Modal({ children }) {
  const isMounted = useIsMounted();
  if (!isMounted) return null;
  return createPortal(children, document.getElementById('modal-root'));
}
```

---

## z-index and Stacking Context

### The Problem Portals Solve

CSS stacking contexts are created by elements with `position` + `z-index`, `transform`, `opacity < 1`, `filter`, and several other properties. A child's z-index only competes within its parent's stacking context.

```css
.sidebar { position: relative; z-index: 1; }
.content { position: relative; z-index: 2; }

/* A modal inside .sidebar can NEVER appear above .content,
   no matter how high its z-index is */
.sidebar .modal { z-index: 999999; } /* Still behind .content! */
```

By portaling the modal to `document.body`, it escapes the sidebar's stacking context and participates in the root stacking context. Now `z-index: 999999` works as expected.

### Best Practice: Dedicated Portal Layers

```html
<body>
  <div id="root"></div>          <!-- z-index: 0 (app) -->
  <div id="dropdown-root"></div> <!-- z-index: 100 (dropdowns) -->
  <div id="modal-root"></div>    <!-- z-index: 200 (modals) -->
  <div id="toast-root"></div>    <!-- z-index: 300 (toasts) -->
</body>
```

This creates a clear layering hierarchy: toasts always above modals, modals always above dropdowns.

### Transform Gotcha

Even without a z-index, `transform` on a parent creates a new stacking context AND a new containing block for `position: fixed` children.

```jsx
// The modal uses position: fixed, but a parent has transform.
// Result: position: fixed is relative to the transformed parent, not the viewport!
<div style={{ transform: 'translateZ(0)' }}>
  <Modal /> {/* If not portaled, position: fixed is BROKEN */}
</div>
```

This is a common bug. Portals fix it by rendering outside the transformed parent.

---

## Portal Cleanup

### Automatic Cleanup

When a portal's parent component unmounts, React automatically removes the portal's children from the container. You do not need to manually clean up.

```jsx
function App() {
  const [show, setShow] = useState(true);

  return (
    <div>
      {show && <PortalChild />}
      <button onClick={() => setShow(false)}>Remove</button>
    </div>
  );
}

function PortalChild() {
  return createPortal(
    <div>I will be cleaned up automatically</div>,
    document.getElementById('portal-root')
  );
}
```

When `show` becomes `false`, React unmounts `PortalChild` and removes its portal content from `#portal-root`.

### Dynamically Created Containers

If you create the container element dynamically, you must clean it up yourself:

```jsx
function DynamicPortal({ children }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = document.createElement('div');
    container.classList.add('dynamic-portal');
    document.body.appendChild(container);
    containerRef.current = container;

    return () => {
      document.body.removeChild(container);
    };
  }, []);

  if (!containerRef.current) return null;
  return createPortal(children, containerRef.current);
}
```

The cleanup function in `useEffect` removes the container from the DOM when the component unmounts.

### Memory Leak Risk

If you add event listeners or modify global state (e.g., `document.body.style.overflow = 'hidden'`) inside a portal component, always clean up in the effect's return function. Portals do not have any special cleanup magic beyond removing the rendered content.

---

## Pitfalls and Tradeoffs

### Pitfall 1: Assuming DOM Event Bubbling

Developers expect clicks inside a portal to NOT reach React parents (because the DOM nodes are separate). But React's synthetic events follow the React tree.

### Pitfall 2: Multiple Portals to the Same Container

If two portals render into the same container, they append their content. This is fine, but ordering depends on render order, which can be fragile.

### Pitfall 3: Refs to Portal Children

`ref` works normally on portal children. The ref points to the actual DOM node (which lives in the portal container, not in the parent's DOM subtree).

```jsx
function App() {
  const portalChildRef = useRef();

  useEffect(() => {
    console.log(portalChildRef.current); // <div> inside #portal-root
    console.log(portalChildRef.current.parentElement); // #portal-root, NOT App's div
  }, []);

  return (
    <div>
      {createPortal(
        <div ref={portalChildRef}>Hello</div>,
        document.getElementById('portal-root')
      )}
    </div>
  );
}
```

### Pitfall 4: CSS-in-JS and Portals

Libraries like styled-components inject styles into `<head>`. Since portal content lives in a different DOM subtree, styles work fine because they are global. However, CSS Modules or scoped styles could miss portal content if the CSS scoping is based on DOM hierarchy.

### Tradeoffs Table

| Aspect | Without Portal | With Portal |
|---|---|---|
| CSS stacking context | Trapped in parent | Escapes to root |
| Event bubbling | DOM = React tree | React tree only |
| Context access | Works | Still works |
| SSR compatibility | No issues | Requires guards |
| Debugging (DOM inspector) | Component is where you expect | Component is in a different DOM location |
| Testing | Straightforward | May need to query the portal container |

---

## Output-Based Questions

### Question 1: Does the parent's onClick fire?

```jsx
function App() {
  return (
    <div onClick={() => console.log("App clicked!")}>
      <h1>App</h1>
      <PortalButton />
    </div>
  );
}

function PortalButton() {
  return createPortal(
    <button onClick={() => console.log("Button clicked!")}>
      Click me
    </button>,
    document.getElementById('portal-root')
  );
}
```

When the user clicks the portal button, what is logged?

**Answer**:

```
Button clicked!
App clicked!
```

Both fire. The button's own `onClick` fires first, then the event bubbles through the **React tree** (not the DOM tree) to `App`'s `div`. Even though the `<button>` is physically in `#portal-root` (a sibling of `#root` in the DOM), React treats `PortalButton` as a child of `App`'s `div` in the React tree.

If you add `e.stopPropagation()` to the button's onClick, "App clicked!" will NOT log -- because `stopPropagation` stops bubbling through the React tree.

---

### Question 2: Does the context value reach the portal?

```jsx
const UserContext = createContext(null);

function App() {
  return (
    <UserContext.Provider value={{ name: "Alice" }}>
      <div id="app">
        <ProfileModal />
      </div>
    </UserContext.Provider>
  );
}

function ProfileModal() {
  const user = useContext(UserContext);
  return createPortal(
    <div className="modal">
      <p>User: {user?.name}</p>
    </div>,
    document.getElementById('modal-root')
  );
}
```

**Answer**: Yes. The portal renders `<p>User: Alice</p>`. Context follows the React tree, not the DOM tree. `ProfileModal` is a descendant of `UserContext.Provider` in the React tree, so `useContext(UserContext)` returns `{ name: "Alice" }` even though the modal's DOM is outside `#root`.

---

### Question 3: What happens with this event handler?

```jsx
function Form() {
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form submitted!");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="username" />
      <SubmitPortal />
    </form>
  );
}

function SubmitPortal() {
  return createPortal(
    <button type="submit">Submit</button>,
    document.getElementById('portal-root')
  );
}
```

When the user clicks the submit button, does "Form submitted!" log?

**Answer**: No. This is a subtle case where the DOM and React behaviors diverge.

The `<button type="submit">` is in `#portal-root` in the DOM, not inside the `<form>`. Native HTML form submission requires the submit button to be a descendant of the `<form>` element **in the DOM**. Since the button is not inside the form in the DOM, clicking it does not trigger the native `submit` event on the form.

React's synthetic event bubbling only applies to React's own event system. The native `submit` event is never triggered on the `<form>` because the browser does not see the button as part of the form. Therefore, `handleSubmit` does not fire.

**Fix**: Use the `form` attribute on the button to associate it with the form:

```jsx
<form id="my-form" onSubmit={handleSubmit}>
  <input type="text" name="username" />
</form>

// In portal:
<button type="submit" form="my-form">Submit</button>
```

Or handle it with an explicit `onClick`:

```jsx
function SubmitPortal({ onSubmit }) {
  return createPortal(
    <button onClick={onSubmit}>Submit</button>,
    document.getElementById('portal-root')
  );
}
```

---

### Question 4: What renders, and where in the DOM?

```jsx
function App() {
  return (
    <div className="app">
      <h1>Main App</h1>
      <Panel />
    </div>
  );
}

function Panel() {
  return (
    <div className="panel">
      <p>Panel content</p>
      {createPortal(
        <div className="overlay">
          <p>Overlay content</p>
          {createPortal(
            <div className="tooltip">Nested portal</div>,
            document.getElementById('tooltip-root')
          )}
        </div>,
        document.getElementById('overlay-root')
      )}
    </div>
  );
}
```

Given this HTML:

```html
<div id="root"></div>
<div id="overlay-root"></div>
<div id="tooltip-root"></div>
```

**Answer**:

DOM structure after render:

```html
<div id="root">
  <div class="app">
    <h1>Main App</h1>
    <div class="panel">
      <p>Panel content</p>
      <!-- First portal's content is NOT here -->
    </div>
  </div>
</div>

<div id="overlay-root">
  <div class="overlay">
    <p>Overlay content</p>
    <!-- Nested portal's content is NOT here either -->
  </div>
</div>

<div id="tooltip-root">
  <div class="tooltip">Nested portal</div>
</div>
```

But the **React tree** is:

```
<App>
  <div className="app">
    <h1>Main App</h1>
    <Panel>
      <div className="panel">
        <p>Panel content</p>
        <div className="overlay">        (portaled to #overlay-root)
          <p>Overlay content</p>
          <div className="tooltip">      (portaled to #tooltip-root)
            Nested portal
          </div>
        </div>
      </div>
    </Panel>
  </div>
</App>
```

A click on "Nested portal" would bubble through: tooltip -> overlay -> Panel -> App in the React tree.

---

### Question 5: Will the portal content be cleaned up?

```jsx
function App() {
  const [show, setShow] = useState(true);

  return (
    <div>
      {show && <FloatingWidget />}
      <button onClick={() => setShow(false)}>Remove</button>
    </div>
  );
}

function FloatingWidget() {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return createPortal(
    <div className="floating-widget">Widget</div>,
    document.getElementById('widget-root')
  );
}
```

When the user clicks "Remove," what happens?

**Answer**: Two things happen:

1. **React automatically removes** the `<div className="floating-widget">` from `#widget-root`. Portal content is cleaned up when the component unmounts -- you do not need to handle this.

2. **The `useEffect` cleanup runs**, restoring `document.body.style.overflow` to `''`. This is explicit cleanup you wrote.

Both happen correctly. The portal content removal is automatic; the body style restoration is your cleanup function. If you forgot the cleanup function, the body would remain locked with `overflow: hidden` -- a memory/behavior leak.

---

## Summary: Portal Mental Model

1. **Portals change WHERE in the DOM**, not where in the React tree
2. **Events bubble through React tree** -- this is the #1 interview gotcha
3. **Context works through portals** -- because context follows the React tree
4. **Portals solve CSS problems**: stacking contexts, overflow, transform-containing blocks
5. **Always handle cleanup**: scroll locks, event listeners, dynamically created containers
6. **SSR requires guards**: `typeof document !== 'undefined'` or lazy mounting with useEffect
7. **Accessibility is non-negotiable for modals**: focus trap, focus restoration, ARIA attributes, inert background
