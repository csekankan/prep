# 18. React Suspense

## Table of Contents

1. [What Is Suspense?](#what-is-suspense)
2. [Suspense for Lazy Loading (React 16+)](#suspense-for-lazy-loading)
3. [Suspense for Data Fetching (React 18+)](#suspense-for-data-fetching)
4. [The Fallback Prop](#the-fallback-prop)
5. [Nested Suspense Boundaries](#nested-suspense-boundaries)
6. [SuspenseList (Experimental)](#suspenselist-experimental)
7. [Error Boundaries with Suspense](#error-boundaries-with-suspense)
8. [Suspense and Streaming SSR](#suspense-and-streaming-ssr)
9. [How Suspense Works Internally](#how-suspense-works-internally)
10. [The use() Hook (React 19)](#the-use-hook-react-19)
11. [Suspense vs Loading State Management](#suspense-vs-loading-state-management)
12. [Pitfalls and Tradeoffs](#pitfalls-and-tradeoffs)
13. [Output-Based Questions](#output-based-questions)

---

## What Is Suspense?

Suspense is a React mechanism that lets components "wait" for something before rendering. While waiting, React shows a fallback UI. When the data/code is ready, React replaces the fallback with the actual content.

```jsx
<Suspense fallback={<Spinner />}>
  <SomeComponentThatMightSuspend />
</Suspense>
```

Suspense has evolved across React versions:

| React Version | Suspense Capability |
|---|---|
| 16.6 | Lazy loading components (`React.lazy`) |
| 18 | Data fetching (with compatible libraries), streaming SSR |
| 19 | `use()` hook, first-class Promise handling |

---

## Suspense for Lazy Loading

The original and most common use of Suspense: loading code-split components.

```jsx
import React, { Suspense, lazy } from 'react';

const HeavyEditor = lazy(() => import('./HeavyEditor'));

function EditorPage() {
  return (
    <div>
      <h1>Editor</h1>
      <Suspense fallback={<p>Loading editor...</p>}>
        <HeavyEditor />
      </Suspense>
    </div>
  );
}
```

### What Happens Step by Step

1. React renders `EditorPage`
2. It encounters `<HeavyEditor />` which is a lazy component
3. The lazy component is not yet loaded, so it **throws a Promise**
4. React catches the Promise at the nearest `<Suspense>` boundary
5. React renders the `fallback` instead of the suspended subtree
6. When the Promise resolves (chunk downloaded), React re-renders the subtree
7. The actual `HeavyEditor` component renders

### Multiple Lazy Components Under One Boundary

```jsx
const Editor = lazy(() => import('./Editor'));
const Preview = lazy(() => import('./Preview'));

function App() {
  return (
    <Suspense fallback={<FullPageLoader />}>
      <Editor />
      <Preview />
    </Suspense>
  );
}
```

Both chunks load in parallel. The fallback shows until **both** are ready. If you want independent loading, use separate Suspense boundaries (see Nested Suspense below).

---

## Suspense for Data Fetching

React 18 introduced Suspense-compatible data fetching. The component does not manage loading state itself -- it just reads data, and if it is not ready, it suspends.

### With a Suspense-Compatible Library (e.g., Relay, TanStack Query, SWR)

```jsx
// With a Suspense-enabled data library
function UserProfile({ userId }) {
  const user = useSuspenseQuery(['user', userId], () => fetchUser(userId));

  // No loading check needed! If data isn't ready, this component suspends.
  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}

function ProfilePage({ userId }) {
  return (
    <Suspense fallback={<ProfileSkeleton />}>
      <UserProfile userId={userId} />
    </Suspense>
  );
}
```

### Why This Is Better

Traditional approach:

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchUser(userId)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} />;
  return <div>{user.name}</div>;
}
```

Problems with the traditional approach:
- Every data-fetching component has its own loading/error state boilerplate
- Loading states are **colocated** with data, not with UI layout
- Waterfalls: child components cannot start fetching until parent finishes rendering
- Difficult to coordinate loading states across sibling components

With Suspense:
- Components just read data -- zero loading state boilerplate
- Loading boundaries are declared in the **parent**, which controls the UX
- Parallel fetching: sibling components can fetch simultaneously
- Composable: nest Suspense boundaries for granular loading UX

### Important: You Cannot Just Throw a Promise

Suspense for data fetching requires a compatible library or a specific integration pattern. You cannot simply throw a Promise from a component:

```jsx
// THIS IS NOT HOW YOU USE SUSPENSE (anti-pattern)
function BadComponent() {
  const promise = fetch('/api/data');
  throw promise; // Don't do this!
}
```

Libraries like Relay, TanStack Query (with `suspense: true`), or SWR handle the integration correctly by maintaining a cache and throwing tracked Promises.

---

## The Fallback Prop

The `fallback` prop accepts any React node to display while children are suspended.

```jsx
// String
<Suspense fallback="Loading...">

// Element
<Suspense fallback={<Spinner />}>

// Complex skeleton UI
<Suspense fallback={
  <div className="skeleton">
    <div className="skeleton-avatar" />
    <div className="skeleton-text" />
    <div className="skeleton-text short" />
  </div>
}>
```

### Fallback Behavior Rules

1. The fallback renders when **any** child in the subtree suspends
2. The fallback is shown until **all** suspended children resolve
3. If a child suspends again after resolving (e.g., re-fetch on prop change), the fallback shows again
4. `fallback={null}` shows nothing while loading (not recommended -- bad UX)
5. If no Suspense boundary exists, React throws an error

### Avoiding Flash of Loading State

If the chunk/data loads very fast (< 200ms), the fallback flashes briefly. React 18's `startTransition` helps:

```jsx
function App() {
  const [tab, setTab] = useState('home');

  function selectTab(nextTab) {
    startTransition(() => {
      setTab(nextTab);
    });
  }

  return (
    <div>
      <TabBar onSelect={selectTab} />
      <Suspense fallback={<Spinner />}>
        {tab === 'home' && <Home />}
        {tab === 'posts' && <Posts />}
      </Suspense>
    </div>
  );
}
```

With `startTransition`, React keeps showing the old content (the previous tab) while the new content loads. The Suspense fallback only appears if loading takes too long.

---

## Nested Suspense Boundaries

Nesting Suspense boundaries gives you granular control over loading states.

### Pattern: Independent Loading Regions

```jsx
function Dashboard() {
  return (
    <div className="dashboard">
      <Suspense fallback={<HeaderSkeleton />}>
        <Header />
      </Suspense>

      <div className="main-content">
        <Suspense fallback={<ChartSkeleton />}>
          <AnalyticsChart />
        </Suspense>

        <Suspense fallback={<TableSkeleton />}>
          <DataTable />
        </Suspense>
      </div>

      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
    </div>
  );
}
```

Each section loads independently. The chart can appear before the table, and vice versa. This creates a progressive loading experience.

### Pattern: Outer + Inner Boundaries

```jsx
function App() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <Layout>
        <Suspense fallback={<ContentSkeleton />}>
          <MainContent />
        </Suspense>
      </Layout>
    </Suspense>
  );
}
```

- If `Layout` suspends, the outer boundary shows `FullPageSpinner`
- If only `MainContent` suspends, the inner boundary shows `ContentSkeleton`
- The outer boundary is a "catch-all" for anything that slips past inner boundaries

### How React Resolves Nested Boundaries

When a component suspends, React walks **up** the tree until it finds the nearest `<Suspense>`. That boundary shows its fallback. Parents above the boundary continue to render normally.

```
<App>                        -- renders normally
  <Suspense fallback={A}>   -- catches suspension from below
    <Parent>                 -- hidden (part of suspended subtree)
      <Suspense fallback={B}>  -- THIS catches it (nearest boundary)
        <SuspendingChild />    -- suspends (throws Promise)
      </Suspense>
    </Parent>
  </Suspense>
</App>
```

`SuspendingChild` suspends. The nearest boundary shows fallback `B`. If we removed the inner Suspense, fallback `A` would show instead, hiding the entire `Parent`.

---

## SuspenseList (Experimental)

`SuspenseList` controls the **order** in which nested Suspense boundaries reveal their content.

```jsx
import { SuspenseList, Suspense } from 'react';

function Feed() {
  return (
    <SuspenseList revealOrder="forwards" tail="collapsed">
      <Suspense fallback={<PostSkeleton />}>
        <Post id={1} />
      </Suspense>
      <Suspense fallback={<PostSkeleton />}>
        <Post id={2} />
      </Suspense>
      <Suspense fallback={<PostSkeleton />}>
        <Post id={3} />
      </Suspense>
    </SuspenseList>
  );
}
```

### Props

| Prop | Values | Behavior |
|---|---|---|
| `revealOrder` | `"forwards"` | Reveal top to bottom, even if bottom loads first |
| | `"backwards"` | Reveal bottom to top |
| | `"together"` | Reveal all at once when all are ready |
| `tail` | `"collapsed"` | Only show one fallback at a time |
| | `"hidden"` | Don't show fallbacks for unrevealed items |

### Status

As of React 19, `SuspenseList` is still experimental and not recommended for production. However, it demonstrates React's vision for orchestrated loading states.

---

## Error Boundaries with Suspense

Suspense handles the "loading" state. Error boundaries handle the "error" state. Together, they cover all async states.

### The Pattern

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <DefaultErrorUI error={this.state.error} />;
    }
    return this.props.children;
  }
}

function DefaultErrorUI({ error }) {
  return (
    <div className="error-panel">
      <h2>Something went wrong</h2>
      <p>{error?.message}</p>
      <button onClick={() => window.location.reload()}>Reload</button>
    </div>
  );
}
```

### Composing Error Boundary + Suspense

```jsx
function DataSection({ userId }) {
  return (
    <ErrorBoundary fallback={<ErrorPanel />}>
      <Suspense fallback={<LoadingSkeleton />}>
        <UserData userId={userId} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

**Order matters**: ErrorBoundary must be **outside** Suspense. If the chunk fails to load or the data fetch throws, the error propagates up from Suspense to the ErrorBoundary.

### With Retry

```jsx
function RetryableSection({ children, fallback }) {
  const [key, setKey] = useState(0);

  return (
    <ErrorBoundary
      key={key}
      fallback={
        <div>
          <p>Failed to load.</p>
          <button onClick={() => setKey(k => k + 1)}>Retry</button>
        </div>
      }
    >
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
```

Changing the `key` on ErrorBoundary forces React to unmount and remount it, clearing the error state and re-attempting the suspended operation.

---

## Suspense and Streaming SSR

React 18 introduced streaming SSR with `renderToPipeableStream`, which integrates with Suspense.

### Traditional SSR Problem

Without streaming, the server must wait for ALL data before sending ANY HTML:

```
Client request --> Server fetches ALL data --> Server renders ALL HTML --> Client receives page
                   (blocked for 3 seconds)
```

### Streaming SSR with Suspense

With streaming, the server sends the HTML shell immediately and streams in Suspense boundaries as they resolve:

```jsx
// server.js
import { renderToPipeableStream } from 'react-dom/server';

app.get('/', (req, res) => {
  const { pipe } = renderToPipeableStream(
    <App />,
    {
      bootstrapScripts: ['/main.js'],
      onShellReady() {
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/html');
        pipe(res);
      },
    }
  );
});
```

```jsx
// App.jsx
function App() {
  return (
    <html>
      <body>
        <Header /> {/* Sent immediately */}
        <Suspense fallback={<Spinner />}>
          <MainContent /> {/* Streamed in when data is ready */}
        </Suspense>
        <Footer /> {/* Sent immediately */}
      </body>
    </html>
  );
}
```

### The Streaming Timeline

```
1. Server sends:  <Header /> + <Spinner /> (fallback) + <Footer />
2. Client hydrates the shell, spinner is interactive
3. Server finishes fetching MainContent data
4. Server streams:  <MainContent /> HTML + inline <script> to swap the spinner
5. Client hydrates MainContent in place
```

The user sees a complete page layout immediately with spinners/skeletons for pending sections. Each section pops in as its data arrives.

### Selective Hydration

React 18 also hydrates Suspense boundaries independently. If the user clicks on a section that is not yet hydrated, React **prioritizes** hydrating that section first.

---

## How Suspense Works Internally

### The Throw Promise Mechanism

This is the core trick. When a component is not ready:

1. The component **throws a Promise** (literally, like throwing an error)
2. React catches it at the nearest Suspense boundary
3. React renders the fallback instead
4. React subscribes to the Promise
5. When the Promise resolves, React re-renders the subtree

```jsx
// Simplified view of what React.lazy does internally
function lazy(importFn) {
  let status = 'pending';
  let result;

  const thenable = importFn().then(
    module => { status = 'resolved'; result = module; },
    error => { status = 'rejected'; result = error; }
  );

  return function LazyComponent(props) {
    if (status === 'pending') throw thenable;   // Suspense catches this
    if (status === 'rejected') throw result;     // Error boundary catches this
    const Component = result.default;
    return <Component {...props} />;
  };
}
```

### Why Throwing Works

React's reconciler wraps component rendering in a try-catch. When it catches a thenable (object with a `.then` method), it knows the component suspended:

```
try {
  result = Component(props);
} catch (thrownValue) {
  if (isThenable(thrownValue)) {
    // Component suspended! Show Suspense fallback.
    // Subscribe to the thenable for re-render.
  } else {
    // Regular error. Propagate to Error Boundary.
  }
}
```

### Key Insight for Interviews

Suspense uses the **same mechanism as error boundaries** (throwing during render) but distinguishes between Promises (suspend) and Errors (error boundary). This is why:
- Suspense catches Promises
- Error boundaries catch Errors
- They compose naturally when nested

---

## The use() Hook (React 19)

React 19 introduced the `use()` hook, which can read Promises and Context directly.

### Reading a Promise

```jsx
import { use, Suspense } from 'react';

function UserProfile({ userPromise }) {
  const user = use(userPromise); // Suspends until promise resolves

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}

function App() {
  const userPromise = fetchUser(1); // Start fetch in parent

  return (
    <Suspense fallback={<Spinner />}>
      <UserProfile userPromise={userPromise} />
    </Suspense>
  );
}
```

### How use() Differs from Other Hooks

| Feature | use() | useState/useEffect |
|---|---|---|
| Can be called conditionally | Yes | No |
| Can be called in loops | Yes | No |
| Integrates with Suspense | Yes | No |
| Handles Promises natively | Yes | Manual async logic |

```jsx
function MessageThread({ showReplies, repliesPromise }) {
  // This is valid! use() can be called conditionally.
  if (showReplies) {
    const replies = use(repliesPromise);
    return <RepliesList replies={replies} />;
  }
  return <p>Click to show replies</p>;
}
```

### use() with Context

`use()` can also read context, replacing `useContext`:

```jsx
// These are equivalent:
const theme = useContext(ThemeContext);
const theme = use(ThemeContext);

// But use() can be called conditionally:
function Component({ useCustomTheme }) {
  const theme = useCustomTheme ? use(ThemeContext) : defaultTheme;
  // useContext cannot do this!
}
```

### Important: Promise Stability

The Promise passed to `use()` must be the **same reference** across re-renders (until it resolves), or React will re-suspend. Create the Promise in the parent and pass it down, or use a caching layer.

```jsx
// WRONG: Creates a new Promise every render, causing infinite suspension
function Bad() {
  const data = use(fetch('/api/data').then(r => r.json())); // New promise each render!
}

// CORRECT: Promise created once, passed as prop or cached
function Good({ dataPromise }) {
  const data = use(dataPromise); // Stable reference
}
```

---

## Suspense vs Loading State Management

### Comparison

```jsx
// Traditional: Component manages its own loading state
function TraditionalComponent() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData().then(d => {
      setData(d);
      setIsLoading(false);
    });
  }, []);

  if (isLoading) return <Spinner />;
  return <DataView data={data} />;
}

// Suspense: Parent controls loading UI, component just reads data
function SuspenseComponent() {
  const data = useSuspenseQuery(fetchData);
  return <DataView data={data} />;
}

function Parent() {
  return (
    <Suspense fallback={<Spinner />}>
      <SuspenseComponent />
    </Suspense>
  );
}
```

### Tradeoffs

| Aspect | Traditional (useState/useEffect) | Suspense |
|---|---|---|
| Loading state location | Inside the component | In a parent boundary |
| Boilerplate | High (state + effect + conditionals) | Low (just read data) |
| Composability | Poor (each component is independent) | High (boundaries can be nested/rearranged) |
| Data fetching waterfalls | Easy to create accidentally | Naturally avoids them |
| Library support | Works everywhere | Requires Suspense-compatible library |
| Error handling | Try-catch in effect + error state | Error boundary (separate concern) |
| SSR | Manual | Streaming SSR integration |
| Learning curve | Familiar | New mental model |

---

## Pitfalls and Tradeoffs

### Pitfall 1: Suspense Waterfall

Even with Suspense, you can create waterfalls if data fetching starts inside components:

```jsx
// WATERFALL: Child doesn't start fetching until Parent's data arrives
function Parent() {
  const parent = use(parentPromise);
  return (
    <Suspense fallback={<Spinner />}>
      <Child parentId={parent.id} /> {/* Fetch starts here, after parent resolves */}
    </Suspense>
  );
}

// PARALLEL: Both fetches start at the same time
function Page({ parentPromise, childPromise }) {
  return (
    <>
      <Suspense fallback={<ParentSkeleton />}>
        <Parent promise={parentPromise} />
      </Suspense>
      <Suspense fallback={<ChildSkeleton />}>
        <Child promise={childPromise} />
      </Suspense>
    </>
  );
}
```

### Pitfall 2: Over-Granular Boundaries

Too many Suspense boundaries can create a "popcorn" effect where items pop in one by one. Group related content under a single boundary for a more cohesive loading experience.

### Pitfall 3: Losing State on Re-suspension

When a component re-suspends (e.g., data refetch on prop change), the entire subtree under the Suspense boundary unmounts. Any local state in that subtree is lost.

```jsx
<Suspense fallback={<Spinner />}>
  <FormWithLocalState />  {/* If this re-suspends, form state is lost! */}
</Suspense>
```

Mitigation: lift important state above the Suspense boundary or use `startTransition` to keep showing stale content while the new content loads.

---

## Output-Based Questions

### Question 1: What renders on screen?

```jsx
const SlowComponent = lazy(() =>
  new Promise(resolve =>
    setTimeout(() => resolve({ default: () => <div>Loaded!</div> }), 2000)
  )
);

function App() {
  return (
    <div>
      <h1>App</h1>
      <Suspense fallback={<p>Outer loading...</p>}>
        <div>
          <Suspense fallback={<p>Inner loading...</p>}>
            <SlowComponent />
          </Suspense>
        </div>
      </Suspense>
    </div>
  );
}
```

**Answer**: 

Initially (for 2 seconds):
```
App
Inner loading...
```

After 2 seconds:
```
App
Loaded!
```

The inner Suspense catches the suspension because it is the nearest boundary. The outer Suspense never shows its fallback. The `<h1>App</h1>` and the wrapping `<div>` render immediately because they are not suspended.

---

### Question 2: What happens when the fetch fails?

```jsx
function UserData({ userPromise }) {
  const user = use(userPromise);
  return <div>{user.name}</div>;
}

function App() {
  const userPromise = fetch('/api/user/999').then(r => {
    if (!r.ok) throw new Error('User not found');
    return r.json();
  });

  return (
    <Suspense fallback={<p>Loading...</p>}>
      <UserData userPromise={userPromise} />
    </Suspense>
  );
}
```

**Answer**: The app crashes with an unhandled error. When the Promise rejects, `use()` throws the error during render. Suspense does NOT catch errors -- it only catches Promises. Without an Error Boundary above the Suspense, the error propagates to the root and React unmounts the entire tree.

Fix: wrap with an Error Boundary:

```jsx
<ErrorBoundary fallback={<p>Failed to load user</p>}>
  <Suspense fallback={<p>Loading...</p>}>
    <UserData userPromise={userPromise} />
  </Suspense>
</ErrorBoundary>
```

---

### Question 3: In what order do the sections appear?

```jsx
const Header = lazy(() => delay(import('./Header'), 100));
const Sidebar = lazy(() => delay(import('./Sidebar'), 500));
const Content = lazy(() => delay(import('./Content'), 300));

function delay(promise, ms) {
  return new Promise(resolve => setTimeout(() => promise.then(resolve), ms));
}

function App() {
  return (
    <div>
      <Suspense fallback={<p>Loading header...</p>}>
        <Header />
      </Suspense>
      <Suspense fallback={<p>Loading sidebar...</p>}>
        <Sidebar />
      </Suspense>
      <Suspense fallback={<p>Loading content...</p>}>
        <Content />
      </Suspense>
    </div>
  );
}
```

**Answer**: Each section resolves independently:

- t=0ms: All three show their fallbacks
- t=100ms: Header appears. Sidebar and Content still loading.
- t=300ms: Content appears. Sidebar still loading.
- t=500ms: Sidebar appears.

Since each component has its own Suspense boundary, they resolve independently in the order their Promises complete (Header first, Content second, Sidebar last). This is the "popcorn" effect -- each section pops in as it becomes ready.

---

### Question 4: Does the fallback re-appear?

```jsx
function UserPage() {
  const [userId, setUserId] = useState(1);

  return (
    <div>
      <button onClick={() => setUserId(u => u + 1)}>Next User</button>
      <Suspense fallback={<p>Loading user...</p>}>
        <UserProfile userId={userId} />
      </Suspense>
    </div>
  );
}

function UserProfile({ userId }) {
  const user = useSuspenseQuery(['user', userId], () => fetchUser(userId));
  return <div>{user.name}</div>;
}
```

Clicking "Next User" changes `userId` from 1 to 2.

**Answer**: Yes, the fallback re-appears. When `userId` changes, `useSuspenseQuery` starts a new fetch and the component suspends again. React unmounts the subtree and shows the fallback.

To prevent this and keep showing the old user while the new one loads, wrap the state update in `startTransition`:

```jsx
<button onClick={() => startTransition(() => setUserId(u => u + 1))}>
  Next User
</button>
```

With `startTransition`, React keeps the current UI visible and only swaps in the new content when it is ready. The fallback only appears if the transition takes too long.

---

## Summary: The Suspense Mental Model

1. **Suspense = declarative loading states**. You declare where loading indicators go, not how to manage loading booleans.
2. **The throw-Promise mechanism** is the engine. Components throw Promises to signal "not ready."
3. **Error boundaries + Suspense** together cover loading + error states for any async operation.
4. **Streaming SSR** sends the page shell immediately and fills in Suspense boundaries as data arrives.
5. **`use()` in React 19** makes Suspense a first-class citizen for any Promise, not just lazy components.
6. **`startTransition`** is the companion to Suspense for avoiding jarring fallback re-appearances during updates.
