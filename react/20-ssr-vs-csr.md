# 20. SSR vs CSR vs SSG — Rendering Strategies in React

## Table of Contents

1. [Client-Side Rendering (CSR)](#client-side-rendering-csr)
2. [Server-Side Rendering (SSR)](#server-side-rendering-ssr)
3. [Static Site Generation (SSG)](#static-site-generation-ssg)
4. [Hydration](#hydration)
5. [Streaming SSR](#streaming-ssr)
6. [Framework Comparison](#framework-comparison)
7. [Decision Matrix](#decision-matrix)
8. [Performance Comparison](#performance-comparison)
9. [SEO Implications](#seo-implications)
10. [Interview Questions](#interview-questions)

---

## Client-Side Rendering (CSR)

### How a Single-Page Application Works

In CSR, the server sends a minimal HTML shell with an empty `<div id="root">` and a `<script>` tag pointing to a JavaScript bundle. The browser downloads, parses, and executes the JS, which then builds the entire DOM.

**The HTML shell served by the server:**

```html
<!DOCTYPE html>
<html>
<head>
  <title>My App</title>
  <link rel="stylesheet" href="/static/css/main.abc123.css" />
</head>
<body>
  <div id="root"></div>
  <script src="/static/js/bundle.def456.js"></script>
</body>
</html>
```

### CSR Rendering Timeline

```
Browser Request
    |
    v
Server sends empty HTML shell (~1 KB)
    |
    v
Browser downloads JS bundle (200 KB - 2 MB)
    |
    v
Browser parses and executes JS
    |
    v
React creates virtual DOM, mounts components
    |
    v
API calls fire (useEffect)
    |
    v
Data arrives, re-render with content
    |
    v
Page is finally interactive and visible
```

**Key metrics affected:**
- **FCP (First Contentful Paint):** Slow -- user sees blank screen until JS executes.
- **TTI (Time to Interactive):** Equal to FCP since JS is already loaded.
- **LCP (Largest Contentful Paint):** Delayed until data fetching completes.

### CSR Code Example (Vite + React)

```jsx
// main.jsx
import { createRoot } from 'react-dom/client';
import App from './App';

const root = createRoot(document.getElementById('root'));
root.render(<App />);

// App.jsx
import { useState, useEffect } from 'react';

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/posts')
      .then(res => res.json())
      .then(data => {
        setPosts(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### CSR Pitfalls

- **SEO:** Search engine crawlers may not execute JS. Google's crawler does run JS but with a delay (days). Other crawlers (Bing, social media link previews) often do not.
- **Initial load performance:** Large bundles cause blank screens on slow networks.
- **Waterfall requests:** Component tree must render before child components can trigger their own data fetches.

---

## Server-Side Rendering (SSR)

### How SSR Works

The server executes React components, generates the full HTML string, and sends it to the browser. The user sees content immediately, then React "hydrates" the page to make it interactive.

### SSR Rendering Timeline

```
Browser Request
    |
    v
Server fetches data from DB/API
    |
    v
Server renders React components to HTML string
    |
    v
Server sends full HTML to browser
    |
    v
Browser paints content (FCP -- fast!)
    |
    v
Browser downloads JS bundle
    |
    v
React hydrates the DOM (attaches event handlers)
    |
    v
Page is interactive (TTI)
```

### SSR with Next.js (Pages Router)

```jsx
// pages/posts.jsx
export async function getServerSideProps() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();

  return {
    props: { posts },
  };
}

export default function PostsPage({ posts }) {
  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### SSR with Next.js (App Router)

```jsx
// app/posts/page.jsx
// Server Component by default -- no "use client" directive
async function PostsPage() {
  const res = await fetch('https://api.example.com/posts', {
    cache: 'no-store', // opt out of caching = SSR behavior
  });
  const posts = await res.json();

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}

export default PostsPage;
```

### SSR Tradeoffs

| Advantage | Disadvantage |
|-----------|--------------|
| Fast FCP -- user sees content quickly | Higher server load (renders per request) |
| SEO-friendly (full HTML in response) | Slower TTFB than CSR (server must render) |
| Works without JS on the client | TTI is delayed (hydration must complete) |
| Better social media link previews | Server infrastructure complexity |

---

## Static Site Generation (SSG)

### Build-Time Rendering

SSG renders pages at **build time**. The HTML is generated once and served from a CDN. No server computation per request.

```jsx
// pages/blog/[slug].jsx (Next.js Pages Router)
export async function getStaticPaths() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();

  const paths = posts.map(post => ({
    params: { slug: post.slug },
  }));

  return { paths, fallback: 'blocking' };
}

export async function getStaticProps({ params }) {
  const res = await fetch(`https://api.example.com/posts/${params.slug}`);
  const post = await res.json();

  return {
    props: { post },
    revalidate: 60, // ISR: regenerate at most every 60 seconds
  };
}

export default function BlogPost({ post }) {
  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  );
}
```

### Incremental Static Regeneration (ISR)

ISR lets you update static pages **after** the site is built, without rebuilding the entire site.

**How ISR works:**

```
1. First request after build  -->  serves cached static HTML
2. After `revalidate` seconds -->  next request triggers background regeneration
3. Stale page is served while new one is built
4. New page replaces old one in cache
```

**ISR in the App Router:**

```jsx
// app/blog/[slug]/page.jsx
export const revalidate = 60; // seconds

async function BlogPost({ params }) {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`, {
    next: { revalidate: 60 },
  }).then(r => r.json());

  return <article><h1>{post.title}</h1></article>;
}
```

### SSG Pitfalls

- **Build time scales with page count.** 10,000 product pages = long builds.
- **Stale data.** Content is only as fresh as the last build (or ISR interval).
- **Not suitable for personalized content** (user dashboards, auth-gated pages).

---

## Hydration

### What Is Hydration?

Hydration is the process where React attaches event handlers and internal state to server-rendered HTML. The server sends static HTML; the client "brings it to life."

```
Server HTML (static, non-interactive)
         |
         |  hydration
         v
Interactive React app (event handlers attached, state initialized)
```

### Hydration Mismatch Errors

A hydration mismatch occurs when the HTML generated on the server does not match what React tries to render on the client. React will warn and potentially discard the server-rendered HTML.

**Common causes and examples:**

```jsx
// MISMATCH: Date/time differs between server and client
function Header() {
  return <p>Current time: {new Date().toLocaleTimeString()}</p>;
  // Server renders "10:30:00 AM"
  // Client hydrates at "10:30:02 AM"
  // React warning: Text content mismatch
}

// FIX: Use useEffect for client-only values
function Header() {
  const [time, setTime] = useState('');

  useEffect(() => {
    setTime(new Date().toLocaleTimeString());
  }, []);

  return <p>Current time: {time || 'Loading...'}</p>;
}
```

```jsx
// MISMATCH: Conditional rendering based on window/localStorage
function Greeting() {
  const theme = localStorage.getItem('theme'); // not available on server!
  return <div className={theme}>Hello</div>;
}

// FIX: Defer to client
function Greeting() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    setTheme(localStorage.getItem('theme') || 'light');
  }, []);

  return <div className={theme}>Hello</div>;
}
```

```jsx
// MISMATCH: Invalid HTML nesting
function App() {
  return (
    <p>
      <div>Nested div inside p</div> {/* Invalid HTML */}
    </p>
  );
  // Browser auto-corrects HTML, creating a mismatch with React's expected tree
}
```

### Selective Hydration (React 18)

React 18 introduced selective hydration with `<Suspense>`. Instead of hydrating the entire page at once, React can hydrate parts independently and prioritize sections the user interacts with.

```jsx
import { Suspense } from 'react';

function App() {
  return (
    <div>
      <Header /> {/* Hydrates first */}
      <Suspense fallback={<Spinner />}>
        <HeavySidebar /> {/* Can hydrate later */}
      </Suspense>
      <MainContent /> {/* Hydrates independently */}
      <Suspense fallback={<Spinner />}>
        <Comments /> {/* Hydrates last, or on interaction */}
      </Suspense>
    </div>
  );
}
```

**Key behavior:** If a user clicks on a `<Suspense>` boundary that has not yet hydrated, React will **prioritize** hydrating that section first.

---

## Streaming SSR

### renderToPipeableStream (React 18)

Instead of waiting for the entire HTML to be ready, streaming SSR sends HTML in chunks as components resolve.

```jsx
// server.js (Node.js)
import { renderToPipeableStream } from 'react-dom/server';
import App from './App';

app.get('/', (req, res) => {
  res.setHeader('Content-Type', 'text/html');

  const { pipe, abort } = renderToPipeableStream(<App />, {
    bootstrapScripts: ['/static/js/bundle.js'],
    onShellReady() {
      // The shell (everything outside Suspense boundaries) is ready
      res.statusCode = 200;
      pipe(res);
    },
    onShellError(error) {
      res.statusCode = 500;
      res.send('<h1>Server Error</h1>');
    },
    onAllReady() {
      // Everything including Suspense content is ready
      // Useful for crawlers/bots that need complete HTML
    },
    onError(error) {
      console.error(error);
    },
  });

  setTimeout(() => abort(), 10000); // 10s timeout
});
```

### Streaming Timeline

```
Server starts rendering
    |
    v
Shell HTML sent immediately (header, layout, nav)
    |
    v
Browser starts painting shell
    |
    v
Suspense boundary 1 resolves --> HTML chunk streamed
    |
    v
Suspense boundary 2 resolves --> HTML chunk streamed
    |
    v
JS bundle loaded --> selective hydration begins
```

---

## Framework Comparison

### Next.js App Router vs Pages Router

| Feature | Pages Router | App Router |
|---------|-------------|------------|
| Data fetching | `getServerSideProps`, `getStaticProps` | `fetch()` in Server Components |
| Default component type | Client Component | Server Component |
| Layouts | `_app.jsx`, `_document.jsx` | Nested `layout.jsx` files |
| Streaming | Limited | Built-in with Suspense |
| Server Components | Not supported | First-class support |
| Caching | ISR via `revalidate` | Granular fetch-level caching |
| Routing | File-based (`pages/`) | File-based (`app/`) with groups |

### Remix

- Nested routing with parallel data loading (no waterfalls).
- `loader` functions run on the server before rendering.
- Progressive enhancement: forms work without JS.
- Uses Web Fetch API and Web Streams.

```jsx
// app/routes/posts.jsx (Remix)
import { useLoaderData } from '@remix-run/react';

export async function loader() {
  const posts = await db.post.findMany();
  return Response.json(posts);
}

export default function Posts() {
  const posts = useLoaderData();
  return (
    <ul>
      {posts.map(post => <li key={post.id}>{post.title}</li>)}
    </ul>
  );
}
```

### Gatsby

- Primarily SSG-focused with GraphQL data layer.
- Rich plugin ecosystem.
- Less focus on SSR (added later as Deferred Static Generation).
- Ideal for content-heavy marketing sites and blogs.

---

## Decision Matrix

```
+---------------------+-------+-------+-------+
| Requirement         | CSR   | SSR   | SSG   |
+---------------------+-------+-------+-------+
| SEO critical        |  No   |  Yes  |  Yes  |
| Highly dynamic data |  Yes  |  Yes  |  No*  |
| Fast FCP            |  No   |  Yes  |  Yes  |
| Low server cost     |  Yes  |  No   |  Yes  |
| Personalized pages  |  Yes  |  Yes  |  No   |
| Real-time updates   |  Yes  |  Yes* |  No   |
| Offline capable     |  Yes  |  No   |  Yes  |
| Build time matters  |  N/A  |  N/A  |  Yes  |
+---------------------+-------+-------+-------+

* SSG + ISR can handle moderately dynamic data
* SSR + WebSockets can handle real-time
```

**When to use what:**

- **CSR:** Internal dashboards, admin panels, apps behind login where SEO does not matter.
- **SSR:** E-commerce product pages, news sites, content that changes frequently and needs SEO.
- **SSG:** Blogs, documentation, marketing sites, content that changes infrequently.
- **SSG + ISR:** Product catalogs, large content sites where you need SSG benefits but cannot rebuild on every change.
- **Streaming SSR:** Large pages with multiple data sources of varying latency.

---

## Performance Comparison

```
Metric Timeline (lower is better)

CSR:
  TTFB   [==]
  FCP    [============]
  TTI    [============]
  LCP    [=================]

SSR:
  TTFB   [=====]
  FCP    [======]
  TTI    [===============]
  LCP    [======]

SSG:
  TTFB   [=]
  FCP    [===]
  TTI    [============]
  LCP    [===]

SSR + Streaming:
  TTFB   [=====]
  FCP    [=====]
  TTI    [=============]
  LCP    [=========]
```

**Key observations:**
- CSR has the fastest TTFB (tiny HTML) but slowest FCP.
- SSG has the fastest everything except TTI (still needs hydration).
- Streaming SSR improves FCP over traditional SSR by sending the shell early.

---

## SEO Implications

| Strategy | Crawlable without JS | Social previews | Core Web Vitals |
|----------|---------------------|-----------------|-----------------|
| CSR | No (or delayed) | No (empty HTML) | Poor FCP/LCP |
| SSR | Yes | Yes | Good FCP, variable TTI |
| SSG | Yes | Yes | Excellent (CDN-served) |
| Streaming SSR | Yes | Partial (depends on bot) | Good FCP |

**Practical tips:**
- Use SSR or SSG for any page you want indexed.
- For CSR apps needing SEO, consider pre-rendering or adding SSR for specific routes.
- Google indexes JS-rendered content but with a delay; other engines may not at all.
- Open Graph and Twitter Card meta tags must be in the initial HTML (not injected by JS).

---

## Interview Questions

### Q1: What happens when a user visits a CSR React app? Walk through the full lifecycle.

**Answer:**

1. Browser sends a GET request to the server.
2. Server responds with a minimal HTML file containing an empty `<div id="root">` and `<script>` tags.
3. Browser parses the HTML and begins downloading the JS bundle(s).
4. Browser parses and executes the JavaScript. React's `createRoot` mounts the app.
5. Components render, `useEffect` hooks fire, triggering API calls.
6. Data arrives, state updates trigger re-renders, and the user finally sees content.

The critical downside is that steps 3-6 all happen before the user sees any meaningful content, leading to poor FCP.

---

### Q2: Explain hydration mismatch. Give a real-world scenario and how to fix it.

**Answer:**

Hydration mismatch occurs when server-rendered HTML differs from what React expects on the client. React compares its virtual DOM output against the existing DOM. If they differ, React logs a warning and may fall back to client-side rendering (discarding SSR benefits).

**Real-world scenario:** A component renders `window.innerWidth` to decide layout.

```jsx
// Broken: window does not exist on the server
function Layout() {
  const isMobile = window.innerWidth < 768;
  return isMobile ? <MobileNav /> : <DesktopNav />;
}

// Fixed: Default to a value and update on client
function Layout() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setIsMobile(window.innerWidth < 768);
    const handler = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  return isMobile ? <MobileNav /> : <DesktopNav />;
}
```

---

### Q3: Compare getServerSideProps, getStaticProps, and the App Router's fetch-based approach.

**Answer:**

| Feature | getServerSideProps | getStaticProps | App Router fetch |
|---------|-------------------|----------------|------------------|
| Runs on | Every request | Build time | Build or request time |
| Location | Pages Router only | Pages Router only | App Router |
| Caching | None by default | Full static + ISR | Granular per-fetch |
| Streaming | No | No | Yes (with Suspense) |
| Component type | Client Component receives props | Client Component receives props | Server Component fetches directly |

The App Router approach is more flexible: each `fetch` call can independently opt into caching (`force-cache`), revalidation (`next: { revalidate: 60 }`), or no caching (`no-store`).

---

### Q4: When would you choose Streaming SSR over traditional SSR?

**Answer:**

Streaming SSR is beneficial when:

1. **Multiple data sources with varying latency.** A page fetching user data (50ms), recommendations (500ms), and comments (2s). With traditional SSR, TTFB is gated by the slowest query (2s). With streaming, the shell and fast sections arrive immediately.

2. **Large pages.** Instead of buffering the entire HTML, the browser can start parsing and rendering incrementally.

3. **Selective hydration.** Combined with React 18's Suspense, streaming allows hydrating interactive sections first while less critical sections load in the background.

You would NOT choose streaming when you need the complete HTML for bots/crawlers that do not support streaming, or when the page is simple enough that traditional SSR is already fast.

---

### Q5: A product manager asks: "Should we use CSR or SSR for our new e-commerce site?" How do you reason about this?

**Answer:**

Key factors to evaluate:

1. **SEO is critical for e-commerce.** Product pages must be indexed. This rules out pure CSR.
2. **Product data changes frequently** (price, availability). Pure SSG would serve stale data.
3. **Performance matters for conversion.** Every 100ms of load time impacts conversion rates.

**Recommended approach:**
- **SSG + ISR** for product listing pages (revalidate every few minutes).
- **SSR** for cart, checkout, and pages with user-specific pricing.
- **CSR** for post-login account dashboards.
- **Streaming SSR** for product detail pages with reviews (fast shell + streamed reviews).

This hybrid approach, natural in Next.js App Router, gives the best of all worlds: fast CDN-served pages where possible, fresh server-rendered content where needed, and interactive client-side behavior for authenticated flows.

---

### Q6: What is the difference between `onShellReady` and `onAllReady` in `renderToPipeableStream`?

**Answer:**

- `onShellReady`: Fires when all content **outside** Suspense boundaries is rendered. This is when you should start piping the response for regular users, giving them the fastest possible FCP.
- `onAllReady`: Fires when **everything** including Suspense content is resolved. Use this for crawlers/bots that need the complete HTML in one response.

```jsx
const { pipe } = renderToPipeableStream(<App />, {
  onShellReady() {
    if (isCrawler(req)) return; // wait for onAllReady
    res.statusCode = 200;
    pipe(res);
  },
  onAllReady() {
    if (isCrawler(req)) {
      res.statusCode = 200;
      pipe(res);
    }
  },
});
```
