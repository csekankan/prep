# 17. Code Splitting in React

## Table of Contents

1. [Why Code Splitting Matters](#why-code-splitting-matters)
2. [Dynamic import() Syntax](#dynamic-import-syntax)
3. [React.lazy for Component-Level Splitting](#reactlazy-for-component-level-splitting)
4. [Route-Based Splitting with React Router](#route-based-splitting-with-react-router)
5. [Suspense as Loading Boundary](#suspense-as-loading-boundary)
6. [Named Exports with Lazy](#named-exports-with-lazy)
7. [Preloading Strategies](#preloading-strategies)
8. [Webpack Magic Comments](#webpack-magic-comments)
9. [Vendor Splitting and Common Chunk Optimization](#vendor-splitting-and-common-chunk-optimization)
10. [Pitfalls and Tradeoffs](#pitfalls-and-tradeoffs)
11. [Output-Based Questions](#output-based-questions)

---

## Why Code Splitting Matters

A typical React SPA bundles all JavaScript into a single file. As the app grows, this bundle grows:

```
small app:    main.js  ~100KB
medium app:   main.js  ~500KB
large app:    main.js  ~2MB+
```

### The Problem

- **Longer download time**: users download code for pages they may never visit
- **Longer parse/compile time**: the browser must parse all JS before the app becomes interactive
- **Higher TTI (Time to Interactive)**: the app appears frozen while the browser processes the bundle
- **Wasted bandwidth**: mobile users on slow networks pay the cost for the entire app

### The Solution

Code splitting breaks the monolithic bundle into smaller chunks loaded on demand. The user downloads only the code needed for the current view.

```
Before:  main.js (2MB) -- everything
After:   main.js (200KB) -- core shell
         home.chunk.js (80KB) -- loaded when visiting /home
         dashboard.chunk.js (300KB) -- loaded when visiting /dashboard
         settings.chunk.js (50KB) -- loaded when visiting /settings
```

### Impact on Metrics

| Metric | Before Split | After Split |
|---|---|---|
| Initial bundle | 2MB | 200KB |
| TTI | 4.5s | 1.2s |
| FCP | 3.0s | 0.8s |

---

## Dynamic import() Syntax

The foundation of code splitting is the dynamic `import()` expression. Unlike static `import` at the top of a file, dynamic `import()` returns a Promise and loads the module at runtime.

```js
// Static import -- included in the main bundle
import { heavyFunction } from './heavyModule';

// Dynamic import -- creates a separate chunk, loaded on demand
const loadHeavy = async () => {
  const module = await import('./heavyModule');
  module.heavyFunction();
};
```

### How It Works Under the Hood

1. The bundler (webpack/Vite) sees `import('./heavyModule')`
2. It extracts `heavyModule` and its dependencies into a separate chunk file
3. At runtime, `import()` fetches this chunk via a network request
4. The Promise resolves with the module's exports

### Important: import() Returns a Module Object

```js
// heavyModule.js
export const greet = (name) => `Hello, ${name}`;
export default function calculate() { /* ... */ }

// consumer.js
import('./heavyModule').then(module => {
  console.log(module.greet("World"));   // named export
  console.log(module.default());         // default export
});
```

---

## React.lazy for Component-Level Splitting

`React.lazy` wraps a dynamic import and makes it usable as a React component.

### Basic Usage

```jsx
import React, { Suspense, lazy } from 'react';

// This creates a separate chunk for HeavyChart
const HeavyChart = lazy(() => import('./HeavyChart'));

function Dashboard() {
  return (
    <Suspense fallback={<div>Loading chart...</div>}>
      <HeavyChart />
    </Suspense>
  );
}
```

### Rules of React.lazy

1. The function passed to `lazy()` must return a Promise that resolves to a module with a `default` export
2. `React.lazy` components **must** be rendered inside a `<Suspense>` boundary
3. Call `lazy()` **outside** the component -- never inside a render function
4. `React.lazy` only works on the client side (not during SSR without additional setup)

### Why Outside the Component?

```jsx
// WRONG: Creates a new lazy component on every render
function App() {
  const LazyComp = lazy(() => import('./MyComp')); // re-created each render!
  return <Suspense fallback="..."><LazyComp /></Suspense>;
}

// CORRECT: Created once at module level
const LazyComp = lazy(() => import('./MyComp'));
function App() {
  return <Suspense fallback="..."><LazyComp /></Suspense>;
}
```

---

## Route-Based Splitting with React Router

The most impactful place to split code is at the route level. Each route becomes its own chunk.

### React Router v6+ Example

```jsx
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const UserProfile = lazy(() => import('./pages/UserProfile'));

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/settings">Settings</Link>
      </nav>

      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/user/:id" element={<UserProfile />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

function PageLoader() {
  return (
    <div className="page-loader">
      <div className="spinner" />
      <p>Loading page...</p>
    </div>
  );
}
```

### Granularity Decision

| Split Level | When to Use |
|---|---|
| Route-level | Always. This is the baseline. |
| Component-level | Heavy components: rich text editors, charts, maps |
| Library-level | Large libraries used in only one feature |

Route-level splitting gives you the best ROI with minimal effort. Component-level splitting is for targeted optimization after measuring.

---

## Suspense as Loading Boundary

`Suspense` catches the Promise thrown by `React.lazy` and shows a fallback while the chunk loads.

### Placement Strategy

You can place `Suspense` at different levels to control the loading experience:

```jsx
// Option 1: One Suspense wrapping all routes (entire page shows loader)
<Suspense fallback={<FullPageSpinner />}>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/dashboard" element={<Dashboard />} />
  </Routes>
</Suspense>

// Option 2: Suspense per route (only the content area shows loader, nav stays)
<Routes>
  <Route path="/" element={
    <Suspense fallback={<ContentSpinner />}>
      <Home />
    </Suspense>
  } />
  <Route path="/dashboard" element={
    <Suspense fallback={<ContentSpinner />}>
      <Dashboard />
    </Suspense>
  } />
</Routes>

// Option 3: Nested Suspense (granular fallbacks)
function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<ChartSkeleton />}>
        <HeavyChart />
      </Suspense>
      <Suspense fallback={<TableSkeleton />}>
        <DataTable />
      </Suspense>
    </div>
  );
}
```

**Best practice**: Place Suspense boundaries where you want the user to see a loading indicator. Use skeleton UIs instead of spinners for a smoother experience.

---

## Named Exports with Lazy

`React.lazy` only supports default exports. If your component uses a named export, you need a wrapper.

### The Problem

```jsx
// MyComponents.js
export function Chart() { /* ... */ }
export function Table() { /* ... */ }

// This FAILS
const Chart = lazy(() => import('./MyComponents')); // no default export!
```

### The Solution

Re-export the named export as default in the import:

```jsx
// Works: map the named export to default
const Chart = lazy(() =>
  import('./MyComponents').then(module => ({
    default: module.Chart
  }))
);

const Table = lazy(() =>
  import('./MyComponents').then(module => ({
    default: module.Table
  }))
);
```

### Alternative: Barrel File

```jsx
// ChartLazy.js
export { Chart as default } from './MyComponents';

// Now you can use it directly
const Chart = lazy(() => import('./ChartLazy'));
```

---

## Preloading Strategies

The main UX cost of code splitting is the loading delay when the user navigates. Preloading mitigates this.

### Preload on Hover

Load the chunk when the user hovers over a link, before they click:

```jsx
const Dashboard = lazy(() => import('./pages/Dashboard'));

function preloadDashboard() {
  import('./pages/Dashboard');
}

function NavLink() {
  return (
    <Link
      to="/dashboard"
      onMouseEnter={preloadDashboard}
      onFocus={preloadDashboard}
    >
      Dashboard
    </Link>
  );
}
```

Once `import()` is called, the module is cached. When `React.lazy` later needs it, it resolves instantly.

### Preload After Initial Render

Load non-critical chunks after the main page is interactive:

```jsx
useEffect(() => {
  const timer = setTimeout(() => {
    import('./pages/Dashboard');
    import('./pages/Settings');
  }, 3000);
  return () => clearTimeout(timer);
}, []);
```

### Preload with Link Tags

```html
<!-- In your HTML head -->
<link rel="prefetch" href="/static/js/dashboard.chunk.js" />
```

`prefetch` tells the browser to download the resource during idle time. `preload` tells the browser to download it immediately (use for critical resources).

### Tradeoffs

| Strategy | When Chunk Loads | UX Impact |
|---|---|---|
| No preloading | On navigation | Visible spinner on every route change |
| Preload on hover | ~200ms before click | Usually instant transition |
| Preload after idle | After main page loads | Uses bandwidth but eliminates future delays |
| Prefetch link | Browser decides | No control over timing |

---

## Webpack Magic Comments

Webpack supports special comments inside `import()` to control chunk behavior.

### Chunk Naming

```jsx
const Dashboard = lazy(() =>
  import(/* webpackChunkName: "dashboard" */ './pages/Dashboard')
);
// Produces: dashboard.chunk.js instead of 3.chunk.js
```

### Preloading Hints

```jsx
// Prefetch: low-priority, loads during idle time
const Settings = lazy(() =>
  import(/* webpackPrefetch: true */ './pages/Settings')
);
// Adds: <link rel="prefetch" href="settings.chunk.js"> to the document

// Preload: high-priority, loads immediately in parallel
const Dashboard = lazy(() =>
  import(/* webpackPreload: true */ './pages/Dashboard')
);
// Adds: <link rel="preload" href="dashboard.chunk.js"> to the document
```

### Combining Comments

```jsx
const Analytics = lazy(() =>
  import(
    /* webpackChunkName: "analytics" */
    /* webpackPrefetch: true */
    './pages/Analytics'
  )
);
```

### Vite Equivalent

Vite does not use webpack magic comments. Chunk naming is configured in `vite.config.js`:

```js
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
        }
      }
    }
  }
};
```

---

## Vendor Splitting and Common Chunk Optimization

### The Problem with One Vendor Bundle

If all dependencies go into one `vendor.js`, updating your app code invalidates the vendor cache too (if they share a chunk). Splitting vendors lets the browser cache stable libraries separately.

### Webpack SplitChunksPlugin

```js
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        // Separate large libraries into their own chunks
        charts: {
          test: /[\\/]node_modules[\\/](recharts|d3)[\\/]/,
          name: 'charts-vendor',
          chunks: 'all',
          priority: 10,
        },
      },
    },
  },
};
```

### Common Chunk Strategy

When multiple routes import the same utility module, webpack can extract it into a shared chunk:

```
Route A imports: utils.js, chartHelpers.js
Route B imports: utils.js, tableHelpers.js

Without common chunk:
  routeA.chunk.js includes utils.js + chartHelpers.js
  routeB.chunk.js includes utils.js + tableHelpers.js
  utils.js is DUPLICATED

With common chunk:
  common.chunk.js includes utils.js
  routeA.chunk.js includes chartHelpers.js
  routeB.chunk.js includes tableHelpers.js
  utils.js loaded ONCE
```

### Content Hashing for Caching

```js
output: {
  filename: '[name].[contenthash].js',
  chunkFilename: '[name].[contenthash].chunk.js',
}
```

Content hashes change only when file contents change, enabling long-term browser caching.

---

## Pitfalls and Tradeoffs

### Pitfall 1: Flash of Loading State

If chunks load fast (< 300ms), the spinner flashes briefly and feels janky. Solutions:
- Use skeleton UIs instead of spinners
- Add a minimum display time for the fallback
- Preload aggressively so the fallback is never shown

### Pitfall 2: Network Errors on Chunk Load

If the network fails while loading a chunk, the app crashes with an unhandled rejection.

```jsx
// Wrap lazy with error handling and retry
function lazyWithRetry(importFn, retries = 3) {
  return lazy(() => {
    return new Promise((resolve, reject) => {
      const attempt = (retriesLeft) => {
        importFn()
          .then(resolve)
          .catch((err) => {
            if (retriesLeft <= 0) {
              reject(err);
              return;
            }
            setTimeout(() => attempt(retriesLeft - 1), 1000);
          });
      };
      attempt(retries);
    });
  });
}

const Dashboard = lazyWithRetry(() => import('./pages/Dashboard'));
```

### Pitfall 3: Over-Splitting

Splitting every tiny component creates too many network requests. Each HTTP request has overhead (DNS, TLS, headers). Balance chunk count against chunk size.

**Rule of thumb**: split at route boundaries and for components > 30KB minified.

### Pitfall 4: SSR Compatibility

`React.lazy` does not work with server-side rendering out of the box. For SSR, use:
- `@loadable/component` (supports SSR)
- Next.js `dynamic()` (handles SSR automatically)
- React 18 `renderToPipeableStream` with Suspense

---

## Output-Based Questions

### Question 1: What happens when this code runs?

```jsx
const LazyComponent = lazy(() => import('./MyComponent'));

function App() {
  return (
    <div>
      <h1>Welcome</h1>
      <LazyComponent />
    </div>
  );
}
```

**Answer**: The app crashes with an error:

```
Error: A component suspended while responding to synchronous input.
This will cause the UI to be replaced with a loading indicator.
```

Or more specifically: `LazyComponent` throws a Promise (that is how Suspense works internally), but there is no `<Suspense>` boundary to catch it. React treats an uncaught suspended component as an error. Fix: wrap `<LazyComponent />` in `<Suspense fallback={...}>`.

---

### Question 2: How many chunks are created?

```jsx
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Contact = lazy(() => import('./pages/Contact'));

// All three pages import:
// import { formatDate } from '../utils/dateUtils';
```

Assuming default webpack config with `splitChunks: { chunks: 'all' }`.

**Answer**: 4 chunks total:
1. `home.chunk.js` -- Home component code
2. `about.chunk.js` -- About component code
3. `contact.chunk.js` -- Contact component code
4. `common.chunk.js` -- `dateUtils.js` (extracted because it is shared by 3+ chunks, meeting webpack's default `minChunks: 2` threshold)

Plus the main `main.js` bundle for the App shell. The exact behavior depends on `splitChunks` config (minSize, minChunks thresholds).

---

### Question 3: What is the order of console.log output?

```jsx
console.log("1: Module level");

const LazyPage = lazy(() => {
  console.log("2: Lazy factory called");
  return import('./Page').then(module => {
    console.log("3: Module loaded");
    return module;
  });
});

function App() {
  console.log("4: App render");
  const [show, setShow] = useState(false);

  return (
    <div>
      <button onClick={() => setShow(true)}>Show</button>
      {show && (
        <Suspense fallback={<div>Loading...</div>}>
          <LazyPage />
        </Suspense>
      )}
    </div>
  );
}
```

**Answer**:

On initial load:
```
1: Module level
4: App render
```

After clicking the button:
```
4: App render        (re-render due to setState)
2: Lazy factory called  (lazy triggers the import)
4: App render        (Suspense re-renders App when chunk arrives)
3: Module loaded     (chunk has been fetched and parsed)
4: App render        (final render with the resolved component)
```

Note: the exact number of `4: App render` logs depends on React's batching behavior and Strict Mode, but the key insight is that `2` logs when the component first tries to render (triggering the dynamic import), and `3` logs when the network request completes.

---

### Question 4: Will this preload work?

```jsx
const Dashboard = lazy(() => import('./Dashboard'));

function App() {
  const [page, setPage] = useState('home');

  useEffect(() => {
    import('./Dashboard');
  }, []);

  return (
    <Suspense fallback={<Spinner />}>
      {page === 'home' && <Home />}
      {page === 'dashboard' && <Dashboard />}
    </Suspense>
  );
}
```

**Answer**: Yes, this preload works. The `useEffect` calls `import('./Dashboard')` immediately after mount, which starts downloading the chunk. The result is cached by the bundler's module system. When the user later switches to `page === 'dashboard'`, `React.lazy` calls `import('./Dashboard')` again, but it resolves instantly from cache. The user sees no loading spinner (assuming the chunk downloaded before they navigated).

However, a subtle issue: if the user clicks "dashboard" before the preload finishes, they will still see the spinner. The preload is not guaranteed to complete before navigation.

---

## Interview Tips

1. **Always mention measuring first**: interviewers want to hear that you profile before optimizing
2. **Route-based splitting is the answer to "how do you reduce bundle size"**: it is the highest-impact, lowest-effort optimization
3. **Know the SSR limitation**: `React.lazy` does not work with SSR; mention `@loadable/component` or Next.js `dynamic()`
4. **Preloading on hover is a crowd-pleaser**: it shows you think about UX, not just performance numbers
5. **Understand the Promise mechanism**: `React.lazy` works because the component throws a Promise that Suspense catches -- this is the foundation for all Suspense-based features
