# Next.js — Complete Industry Guide

> Everything you need to know: routing, rendering, data fetching, state management, authentication, deployment, and interview-critical concepts.

---

## Table of Contents

1. [What Is Next.js and Why It Exists](#1-what-is-nextjs-and-why-it-exists)
2. [App Router vs Pages Router](#2-app-router-vs-pages-router)
3. [Routing — Every Pattern](#3-routing--every-pattern)
4. [Server Components vs Client Components](#4-server-components-vs-client-components)
5. [Rendering Strategies: SSR, SSG, ISR, CSR](#5-rendering-strategies-ssr-ssg-isr-csr)
6. [Data Fetching — Complete Guide](#6-data-fetching--complete-guide)
7. [Server Actions (Mutations)](#7-server-actions-mutations)
8. [Layouts, Templates, Loading, Error Handling](#8-layouts-templates-loading-error-handling)
9. [Middleware](#9-middleware)
10. [API Routes (Route Handlers)](#10-api-routes-route-handlers)
11. [State Management — Redux, Zustand, Context](#11-state-management--redux-zustand-context)
12. [Authentication — NextAuth.js / Auth.js](#12-authentication--nextauthjs--authjs)
13. [Database Integration — Prisma, Drizzle](#13-database-integration--prisma-drizzle)
14. [Styling — Tailwind, CSS Modules, Styled Components](#14-styling--tailwind-css-modules-styled-components)
15. [Image, Font, and Script Optimization](#15-image-font-and-script-optimization)
16. [Caching and Revalidation](#16-caching-and-revalidation)
17. [Streaming and Suspense](#17-streaming-and-suspense)
18. [Parallel and Intercepting Routes](#18-parallel-and-intercepting-routes)
19. [Internationalization (i18n)](#19-internationalization-i18n)
20. [Testing — Jest, React Testing Library, Playwright](#20-testing--jest-react-testing-library-playwright)
21. [Deployment — Vercel, Docker, Self-Hosted](#21-deployment--vercel-docker-self-hosted)
22. [Performance Optimization](#22-performance-optimization)
23. [Important Libraries Ecosystem](#23-important-libraries-ecosystem)
24. [Interview Critical Concepts](#24-interview-critical-concepts)
25. [Common Mistakes and Gotchas](#25-common-mistakes-and-gotchas)

---

## 1. What Is Next.js and Why It Exists

### The Problem with Plain React (Vite / CRA)

```
Plain React (Client-Side Only):
- User opens page → sees BLANK white screen
- Downloads 500KB JS bundle
- JS executes → fetches data from API
- Finally renders content (3-5 seconds later)
- Search engines see empty <div id="root"></div> → bad SEO
```

### What Next.js Adds on Top of React

| Feature | Plain React | Next.js |
|---|---|---|
| Server-side rendering | Manual setup | Built-in |
| File-based routing | Need react-router | Automatic |
| Code splitting | Manual | Automatic per route |
| API routes | Need Express | Built-in |
| Image optimization | Manual | `<Image>` component |
| SEO | Terrible | Excellent |
| Static generation | Not possible | Built-in |
| Streaming | Complex | Built-in |

### Next.js = React + Server + Routing + Optimization

```bash
# Create a Next.js project
npx create-next-app@latest my-app
cd my-app
npm run dev    # → http://localhost:3000
```

Project structure after creation:

```
my-app/
├── app/                    ← Your pages and components
│   ├── layout.jsx         ← Root layout (wraps all pages)
│   ├── page.jsx           ← Homepage (/)
│   └── globals.css
├── public/                 ← Static files (images, favicon)
├── next.config.js          ← Next.js configuration
├── package.json
├── tailwind.config.js      ← Tailwind CSS config
└── tsconfig.json           ← TypeScript config
```

---

## 2. App Router vs Pages Router

### File Location Determines Which Router

```
my-app/
├── app/       ← APP ROUTER (Next.js 13+, recommended)
└── pages/     ← PAGES ROUTER (legacy, still supported)
```

### Key Differences

| Feature | Pages Router | App Router |
|---|---|---|
| Directory | `pages/` | `app/` |
| File convention | `pages/about.jsx` | `app/about/page.jsx` |
| Default rendering | Client Component | Server Component |
| Data fetching | `getServerSideProps`, `getStaticProps` | `async` components, `fetch()` |
| Layouts | `_app.jsx` (global only) | `layout.jsx` (nested per route) |
| Loading UI | Manual | `loading.jsx` (automatic) |
| Error UI | `_error.jsx` (global) | `error.jsx` (per route) |
| Streaming | Not supported | Built-in |
| Server Actions | Not supported | Built-in |
| Released | 2016 | 2022 |

### This guide focuses on App Router (the future).

---

## 3. Routing — Every Pattern

### Basic Routes

```
app/
├── page.jsx                    → /
├── about/
│   └── page.jsx                → /about
├── blog/
│   └── page.jsx                → /blog
└── contact/
    └── page.jsx                → /contact
```

### Dynamic Routes — `[param]`

```
app/
└── posts/
    └── [id]/
        └── page.jsx            → /posts/1, /posts/abc, /posts/anything
```

```jsx
// app/posts/[id]/page.jsx
export default async function PostPage({ params }) {
  const { id } = await params;  // "1" from /posts/1
  const post = await fetch(`https://api.example.com/posts/${id}`).then(r => r.json());
  return <h1>{post.title}</h1>;
}
```

### Multiple Dynamic Segments

```
app/
└── shop/
    └── [category]/
        └── [productId]/
            └── page.jsx        → /shop/shoes/nike-air-max
```

```jsx
// app/shop/[category]/[productId]/page.jsx
export default async function ProductPage({ params }) {
  const { category, productId } = await params;
  // category = "shoes", productId = "nike-air-max"
}
```

### Catch-All Routes — `[...slug]`

Matches any number of segments:

```
app/
└── docs/
    └── [...slug]/
        └── page.jsx
```

```jsx
// URL: /docs/react/hooks/useEffect
// params.slug = ["react", "hooks", "useEffect"]

// URL: /docs/next
// params.slug = ["next"]
```

### Optional Catch-All — `[[...slug]]`

Same as catch-all but ALSO matches the base path:

```
app/
└── docs/
    └── [[...slug]]/
        └── page.jsx
```

```jsx
// URL: /docs           → params.slug = undefined (matches!)
// URL: /docs/react     → params.slug = ["react"]
// URL: /docs/a/b/c     → params.slug = ["a", "b", "c"]
```

### Route Groups — `(groupName)`

Organize files without affecting the URL:

```
app/
├── (marketing)/            ← NOT in URL
│   ├── about/
│   │   └── page.jsx       → /about (not /marketing/about)
│   └── pricing/
│       └── page.jsx       → /pricing
│
├── (shop)/                 ← NOT in URL
│   ├── products/
│   │   └── page.jsx       → /products
│   └── cart/
│       └── page.jsx       → /cart
│
└── (auth)/                 ← NOT in URL, can have its own layout
    ├── layout.jsx          ← Auth-specific layout (no navbar)
    ├── login/
    │   └── page.jsx        → /login
    └── register/
        └── page.jsx        → /register
```

### Private Folders — `_folderName`

Excluded from routing entirely:

```
app/
├── _components/            ← NOT a route, just organization
│   ├── Button.jsx
│   └── Card.jsx
├── _lib/                   ← NOT a route
│   └── utils.js
└── page.jsx
```

### Programmatic Navigation

```jsx
"use client";
import { useRouter, usePathname, useSearchParams } from 'next/navigation';

export function NavigationExample() {
  const router = useRouter();
  const pathname = usePathname();       // "/posts/42"
  const searchParams = useSearchParams(); // ?sort=date → searchParams.get('sort')

  return (
    <div>
      <button onClick={() => router.push('/posts')}>Go to Posts</button>
      <button onClick={() => router.replace('/login')}>Replace with Login</button>
      <button onClick={() => router.back()}>Go Back</button>
      <button onClick={() => router.refresh()}>Refresh Server Data</button>
    </div>
  );
}
```

### Link Component (Preferred for navigation)

```jsx
import Link from 'next/link';

export function Nav() {
  return (
    <nav>
      <Link href="/">Home</Link>
      <Link href="/about">About</Link>
      <Link href={`/posts/${post.id}`}>Read More</Link>
      <Link href="/dashboard" prefetch={false}>Dashboard</Link>
    </nav>
  );
}
```

---

## 4. Server Components vs Client Components

### The Core Mental Model

```
SERVER COMPONENT (default):
  - Runs on the server (Node.js)
  - Has access to: database, file system, env secrets
  - Cannot use: useState, useEffect, onClick, browser APIs
  - Sends: ZERO JavaScript to the browser
  - Think of it as: a template engine that happens to use JSX

CLIENT COMPONENT ("use client"):
  - Runs in the browser (like normal React)
  - Has access to: window, localStorage, DOM, events
  - Can use: ALL hooks, ALL event handlers
  - Sends: JavaScript bundle to the browser
  - Think of it as: traditional React component
```

### Decision Table

| I need to... | Component Type |
|---|---|
| Fetch data from DB/API | Server |
| Use `useState` or `useEffect` | Client |
| Access backend resources (DB, fs, secrets) | Server |
| Add interactivity (onClick, onChange) | Client |
| Use browser APIs (localStorage, window) | Client |
| Reduce JS sent to browser | Server |
| Use third-party client libraries (Redux, Framer Motion) | Client |
| Display static content | Server |

### How They Work Together

```jsx
// app/dashboard/page.jsx — SERVER COMPONENT
import { DashboardChart } from './chart';  // client
import { StatsCard } from './stats-card';  // server

export default async function DashboardPage() {
  // This runs on server — direct DB access
  const stats = await db.query("SELECT count(*) FROM orders");
  const revenue = await db.query("SELECT sum(total) FROM orders");

  return (
    <div>
      {/* Server component — no JS shipped */}
      <StatsCard orders={stats.count} revenue={revenue.sum} />

      {/* Client component — JS shipped for interactivity */}
      <DashboardChart data={stats.monthly} />
    </div>
  );
}
```

```jsx
// app/dashboard/stats-card.jsx — SERVER COMPONENT (no directive)
export function StatsCard({ orders, revenue }) {
  return (
    <div>
      <p>Total Orders: {orders}</p>
      <p>Revenue: ${revenue}</p>
    </div>
  );
}
```

```jsx
// app/dashboard/chart.jsx — CLIENT COMPONENT
"use client";
import { useState } from 'react';
import { BarChart } from 'recharts';

export function DashboardChart({ data }) {
  const [timeRange, setTimeRange] = useState('7d');

  return (
    <div>
      <select onChange={e => setTimeRange(e.target.value)}>
        <option value="7d">7 Days</option>
        <option value="30d">30 Days</option>
      </select>
      <BarChart data={data[timeRange]} />
    </div>
  );
}
```

### The Boundary Rule

```
Server Component can import:
  ✅ Other Server Components
  ✅ Client Components (renders them, passes props)

Client Component can import:
  ✅ Other Client Components
  ❌ Server Components (CANNOT import directly)

Workaround: pass Server Component as {children} prop
```

```jsx
// WRONG — Client importing Server
"use client";
import { ServerThing } from './server-thing';  // ❌ Error!

// RIGHT — Pass as children
// app/page.jsx (server)
import { ClientWrapper } from './client-wrapper';
import { ServerContent } from './server-content';

export default function Page() {
  return (
    <ClientWrapper>
      <ServerContent />  {/* ← passed as children prop */}
    </ClientWrapper>
  );
}

// client-wrapper.jsx
"use client";
export function ClientWrapper({ children }) {
  const [open, setOpen] = useState(true);
  return open ? <div>{children}</div> : null;
}
```

---

## 5. Rendering Strategies: SSR, SSG, ISR, CSR

### The Four Strategies

```
SSR — Server-Side Rendering
  When: every request
  HTML: generated fresh on each request
  Use: personalized data, real-time content

SSG — Static Site Generation
  When: build time (once)
  HTML: pre-generated, served from CDN
  Use: blog posts, docs, marketing pages

ISR — Incremental Static Regeneration
  When: build time + revalidate periodically
  HTML: static but refreshes every N seconds
  Use: product pages, news (stale-while-revalidate)

CSR — Client-Side Rendering
  When: browser loads
  HTML: empty shell, JS builds the page
  Use: dashboards behind auth, highly interactive UIs
```

### How to Choose Each in App Router

```jsx
// SSR — fetch on every request (no cache)
async function SSRPage() {
  const data = await fetch('https://api.example.com/data', {
    cache: 'no-store',  // ← forces SSR
  });
  return <div>{data}</div>;
}

// SSG — fetch once at build time (cached forever)
async function SSGPage() {
  const data = await fetch('https://api.example.com/data');
  // Default behavior: cached at build time
  return <div>{data}</div>;
}

// ISR — fetch at build time, revalidate every 60 seconds
async function ISRPage() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 60 },  // ← refresh every 60s
  });
  return <div>{data}</div>;
}

// CSR — no server rendering, all in browser
"use client";
function CSRPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData);
  }, []);
  return <div>{data}</div>;
}
```

### Route Segment Config (Force behavior for entire page)

```jsx
// app/dashboard/page.jsx
export const dynamic = 'force-dynamic';       // = SSR (always fresh)
// OR
export const dynamic = 'force-static';        // = SSG (always cached)
// OR
export const revalidate = 3600;               // = ISR (refresh every hour)
```

### When to Use What

| Content Type | Strategy | Why |
|---|---|---|
| Blog post | SSG | Content rarely changes |
| Product page | ISR (60s) | Updates occasionally, CDN speed |
| User dashboard | SSR | Personalized, must be fresh |
| Search results | SSR | Depends on query |
| Admin panel | CSR | Behind auth, highly interactive |
| Landing page | SSG | Static, maximum speed |
| E-commerce prices | ISR (30s) | Change sometimes, speed matters |
| Real-time chat | CSR + WebSocket | Constantly changing |

---

## 5.5 ISR Deep Dive — Incremental Static Regeneration

### The Problem ISR Solves

```
SSG problem:  Data is stale until next deploy. You have 10,000 product pages.
              A price changes → you must rebuild ALL 10,000 pages. Takes 20 minutes.

SSR problem:  Every visitor hits your server + database.
              1 million visitors = 1 million DB queries. Slow, expensive.

ISR solution: Serve cached static HTML (fast like SSG).
              In background, regenerate the page every N seconds (fresh like SSR).
              Only regenerate pages that are actually visited.
```

### How ISR Works — Step by Step

```
Timeline for a product page with revalidate: 60

0:00  — Build time: page is generated and cached.
0:01  — User A visits → gets cached HTML (instant, from CDN)
0:30  — User B visits → gets same cached HTML (instant)
1:01  — User C visits → gets STALE cached HTML (still instant!)
         BUT: Next.js triggers background regeneration
1:02  — Server re-renders the page with fresh data (in background)
         New HTML replaces old in cache
1:03  — User D visits → gets NEW fresh HTML (instant, from CDN)
2:01  — Cycle repeats...

KEY INSIGHT: User C still got a fast response (stale cache).
             User D gets the fresh version.
             No one ever waits for the server.
```

### ISR in App Router — Time-Based

```jsx
// app/products/[id]/page.jsx

// Option 1: Per-fetch revalidation
export default async function ProductPage({ params }) {
  const { id } = await params;

  const product = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 60 },  // ← revalidate this data every 60 seconds
  });

  return <div>{product.name} — ${product.price}</div>;
}

// Option 2: Page-level revalidation (applies to ALL fetches in this page)
export const revalidate = 60;  // ← entire page revalidates every 60s

export default async function ProductPage({ params }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`);
  return <div>{product.name}</div>;
}
```

### ISR in Pages Router (Legacy — for reference)

```jsx
// pages/products/[id].jsx

export async function getStaticPaths() {
  // Pre-render top 100 products at build time
  const products = await fetch('https://api.example.com/products?top=100').then(r => r.json());
  return {
    paths: products.map(p => ({ params: { id: p.id.toString() } })),
    fallback: 'blocking',  // other pages: generate on first visit, then cache
  };
}

export async function getStaticProps({ params }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`).then(r => r.json());
  return {
    props: { product },
    revalidate: 60,  // ← ISR: regenerate every 60 seconds
  };
}

export default function ProductPage({ product }) {
  return <div>{product.name} — ${product.price}</div>;
}
```

### On-Demand ISR (Revalidate When Data Changes — Not on Timer)

Instead of waiting N seconds, revalidate **immediately** when data changes:

```jsx
// app/api/revalidate/route.js — Webhook from CMS or admin panel
import { revalidatePath, revalidateTag } from 'next/cache';
import { NextResponse } from 'next/server';

export async function POST(request) {
  const { secret, path, tag } = await request.json();

  // Verify webhook is legitimate
  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }

  // Option 1: Revalidate a specific page
  if (path) {
    revalidatePath(path);  // e.g., '/products/42'
  }

  // Option 2: Revalidate all fetches with a tag
  if (tag) {
    revalidateTag(tag);  // e.g., 'products'
  }

  return NextResponse.json({ revalidated: true, now: Date.now() });
}
```

```jsx
// app/products/[id]/page.jsx — tag your fetches
export default async function ProductPage({ params }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`, {
    next: {
      tags: ['products', `product-${params.id}`],  // ← tagged for on-demand revalidation
    },
  });
  return <div>{product.name}</div>;
}

// Now when admin updates a product, CMS sends webhook:
// POST /api/revalidate { secret: "...", tag: "product-42" }
// → Only that specific product page is regenerated. Instant.
```

### ISR with `generateStaticParams` (Pre-render at Build + ISR After)

```jsx
// app/products/[id]/page.jsx

// Pre-render these pages at build time (like SSG)
export async function generateStaticParams() {
  const topProducts = await fetch('https://api.example.com/products?top=100').then(r => r.json());
  return topProducts.map(p => ({ id: p.id.toString() }));
}

// ISR for this page
export const revalidate = 120;  // regenerate every 2 minutes

// For pages NOT in generateStaticParams:
export const dynamicParams = true;  // allow dynamic generation on first visit
// false = return 404 for unknown IDs

export default async function ProductPage({ params }) {
  const { id } = await params;
  const product = await fetch(`https://api.example.com/products/${id}`).then(r => r.json());
  if (!product) notFound();
  return <h1>{product.name}</h1>;
}
```

### ISR vs SSR — Direct Comparison

```
Scenario: E-commerce site with 50,000 products. 100,000 visitors/day.

═══════════════════════════════════════════════════════════
SSR Approach:
═══════════════════════════════════════════════════════════
  Every visit → server runs → queries DB → renders HTML → sends response
  
  100,000 visitors × DB query each = 100,000 DB queries per day
  Response time: 200-500ms (server must work every time)
  Server cost: HIGH (needs powerful server for load)
  Data freshness: ALWAYS fresh (real-time)
  CDN: Cannot cache (personalized or no-store)

═══════════════════════════════════════════════════════════
ISR Approach (revalidate: 60):
═══════════════════════════════════════════════════════════
  First visit after 60s → triggers background regeneration
  All other visits → served from CDN cache (no server hit)
  
  100,000 visitors → only ~1,440 regenerations/day (one per page per minute)
  Response time: 10-50ms (CDN cache hit — no server involved)
  Server cost: LOW (server barely works)
  Data freshness: Up to 60 seconds stale (acceptable for prices)
  CDN: Fully cacheable
```

### Head-to-Head Feature Comparison

| Feature | SSR | ISR | SSG |
|---|---|---|---|
| When HTML is generated | Every request | Build + background refresh | Build only |
| Response time | 200-500ms | 10-50ms (CDN) | 10-50ms (CDN) |
| Server load | High | Very low | Zero |
| Data freshness | Real-time | Up to N seconds stale | Stale until redeploy |
| Personalized content | Yes | No (same page for all users) | No |
| Scales to millions of users | Expensive | Easily (CDN handles it) | Easily |
| Dynamic paths (new products) | Automatic | `dynamicParams: true` | Need rebuild |
| Auth-dependent content | Yes | No — use CSR for that part | No |
| Cost | $$$$ (server always running) | $ (CDN + occasional regen) | $ (CDN only) |

### When to Use ISR vs SSR

```
USE ISR WHEN:
  ✅ Same content for all users (not personalized)
  ✅ Data changes occasionally (every few seconds to hours)
  ✅ Speed matters more than real-time accuracy
  ✅ High traffic pages (CDN absorbs load)
  ✅ E-commerce products, blog posts, news articles, documentation

USE SSR WHEN:
  ✅ Content is personalized (user-specific dashboard)
  ✅ Data MUST be real-time (stock prices, live scores)
  ✅ Content depends on request (cookies, headers, search query)
  ✅ Auth-gated pages where content varies per user
  ✅ Search results, user profiles, real-time analytics
```

### Mixing ISR and SSR on the Same Page (Common Pattern)

```jsx
// app/products/[id]/page.jsx
import { Suspense } from 'react';

// ISR for product data (same for everyone, changes rarely)
export const revalidate = 120;

export default async function ProductPage({ params }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`, {
    next: { revalidate: 120 },  // ← ISR: refresh every 2 min
  });

  return (
    <div>
      {/* Static product info — served from cache */}
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p>Price: ${product.price}</p>

      {/* Dynamic stock — client-side (real-time, per-user) */}
      <Suspense fallback={<p>Checking stock...</p>}>
        <StockChecker productId={params.id} />
      </Suspense>
    </div>
  );
}
```

```jsx
// app/products/[id]/stock-checker.jsx
"use client";
import useSWR from 'swr';

export function StockChecker({ productId }) {
  // This fetches in the BROWSER — always real-time
  const { data } = useSWR(`/api/products/${productId}/stock`, fetcher, {
    refreshInterval: 5000,  // poll every 5 seconds
  });

  if (!data) return <p>Loading...</p>;
  return <p>{data.inStock ? '✅ In Stock' : '❌ Out of Stock'}</p>;
}
```

### ISR Gotchas

```
1. ISR serves STALE content to the user who triggers revalidation.
   The NEXT user gets fresh content. This is by design (stale-while-revalidate).

2. On Vercel, ISR works automatically (CDN handles caching).
   Self-hosted: you need a CDN or reverse proxy (Nginx, CloudFront) in front.

3. ISR does NOT work with cookies/headers-dependent content.
   If your page reads cookies → Next.js auto-opts into SSR.

4. revalidate: 0 is NOT the same as cache: 'no-store'.
   revalidate: 0 = revalidate on every request (still uses cache mechanism).
   cache: 'no-store' = bypass cache entirely (true SSR).

5. ISR pages must be the same for ALL users.
   If user A and user B should see different content → use SSR, not ISR.
```

---

## 6. Data Fetching — Complete Guide

### In Server Components (recommended)

```jsx
// app/posts/page.jsx — Server Component
export default async function PostsPage() {
  // Option 1: fetch API
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());

  // Option 2: direct database query (no API needed!)
  const posts = await prisma.post.findMany();

  // Option 3: direct file system
  const content = await fs.readFile('./data/posts.json', 'utf8');

  return <PostList posts={posts} />;
}
```

### Request Deduplication

Next.js automatically deduplicates identical fetches in the same render:

```jsx
// These two components make the SAME request
// Next.js only calls the API ONCE and shares the result

// app/layout.jsx
async function Layout({ children }) {
  const user = await fetch('/api/user').then(r => r.json());  // ← call #1
  return <div><Navbar user={user} />{children}</div>;
}

// app/page.jsx
async function Page() {
  const user = await fetch('/api/user').then(r => r.json());  // ← same URL = deduplicated
  return <h1>Hello {user.name}</h1>;
}
// Only ONE actual HTTP request is made!
```

### In Client Components

```jsx
"use client";
import { useState, useEffect } from 'react';

// Option 1: useEffect (basic)
function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/search?q=${query}`)
      .then(r => r.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      });
  }, [query]);

  if (loading) return <p>Loading...</p>;
  return <ul>{results.map(r => <li key={r.id}>{r.title}</li>)}</ul>;
}
```

```jsx
// Option 2: SWR (recommended for client fetching)
"use client";
import useSWR from 'swr';

const fetcher = (url) => fetch(url).then(r => r.json());

function SearchResults({ query }) {
  const { data, error, isLoading } = useSWR(`/api/search?q=${query}`, fetcher);

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error!</p>;
  return <ul>{data.map(r => <li key={r.id}>{r.title}</li>)}</ul>;
}
```

```jsx
// Option 3: TanStack Query (most powerful)
"use client";
import { useQuery } from '@tanstack/react-query';

function SearchResults({ query }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query],
    queryFn: () => fetch(`/api/search?q=${query}`).then(r => r.json()),
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error!</p>;
  return <ul>{data.map(r => <li key={r.id}>{r.title}</li>)}</ul>;
}
```

---

## 7. Server Actions (Mutations)

Server Actions let you mutate data **without creating API routes**. The function runs on the server, called from a form or client component.

### Basic Form with Server Action

```jsx
// app/posts/new/page.jsx
import { redirect } from 'next/navigation';
import { prisma } from '@/lib/db';

export default function NewPostPage() {
  async function createPost(formData) {
    "use server";  // ← this function runs on the SERVER

    const title = formData.get('title');
    const body = formData.get('body');

    await prisma.post.create({
      data: { title, body },
    });

    redirect('/posts');  // redirect after mutation
  }

  return (
    <form action={createPost}>
      <input name="title" placeholder="Title" required />
      <textarea name="body" placeholder="Body" required />
      <button type="submit">Create Post</button>
    </form>
  );
}
```

### Server Action in Separate File (Reusable)

```jsx
// app/actions/posts.js
"use server";
import { prisma } from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function createPost(formData) {
  const title = formData.get('title');
  const body = formData.get('body');

  await prisma.post.create({ data: { title, body } });
  revalidatePath('/posts');  // refresh the posts list page
}

export async function deletePost(postId) {
  await prisma.post.delete({ where: { id: postId } });
  revalidatePath('/posts');
}

export async function likePost(postId) {
  await prisma.post.update({
    where: { id: postId },
    data: { likes: { increment: 1 } },
  });
  revalidatePath(`/posts/${postId}`);
}
```

### Calling Server Actions from Client Components

```jsx
// app/posts/[id]/like-button.jsx
"use client";
import { useTransition } from 'react';
import { likePost } from '@/app/actions/posts';

export function LikeButton({ postId }) {
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    startTransition(async () => {
      await likePost(postId);  // calls server function from client!
    });
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {isPending ? 'Liking...' : '❤️ Like'}
    </button>
  );
}
```

### Server Action with Validation (using Zod)

```jsx
// app/actions/posts.js
"use server";
import { z } from 'zod';

const PostSchema = z.object({
  title: z.string().min(3).max(100),
  body: z.string().min(10).max(5000),
});

export async function createPost(prevState, formData) {
  const raw = {
    title: formData.get('title'),
    body: formData.get('body'),
  };

  const result = PostSchema.safeParse(raw);
  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors };
  }

  await prisma.post.create({ data: result.data });
  redirect('/posts');
}
```

```jsx
// app/posts/new/page.jsx — form with validation errors
"use client";
import { useActionState } from 'react';
import { createPost } from '@/app/actions/posts';

export default function NewPostForm() {
  const [state, formAction, isPending] = useActionState(createPost, { errors: {} });

  return (
    <form action={formAction}>
      <input name="title" />
      {state.errors?.title && <p className="text-red-500">{state.errors.title}</p>}

      <textarea name="body" />
      {state.errors?.body && <p className="text-red-500">{state.errors.body}</p>}

      <button disabled={isPending}>
        {isPending ? 'Creating...' : 'Create'}
      </button>
    </form>
  );
}
```

---

## 8. Layouts, Templates, Loading, Error Handling

### File Convention

```
app/
├── layout.jsx       ← Persistent layout (doesn't re-render on navigation)
├── template.jsx     ← Re-renders on every navigation
├── loading.jsx      ← Shown while page.jsx is loading (Suspense boundary)
├── error.jsx        ← Shown when page.jsx throws an error
├── not-found.jsx    ← Shown for 404
└── page.jsx         ← The actual page content
```

### Layout — Persistent Shell

```jsx
// app/layout.jsx — Root layout (REQUIRED)
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'My App',
  description: 'Built with Next.js',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header>
          <nav>My App</nav>
        </header>
        <main>{children}</main>
        <footer>© 2024</footer>
      </body>
    </html>
  );
}
```

```jsx
// app/dashboard/layout.jsx — Nested layout (only for /dashboard/*)
export default function DashboardLayout({ children }) {
  return (
    <div className="flex">
      <aside>
        <nav>
          <a href="/dashboard">Overview</a>
          <a href="/dashboard/settings">Settings</a>
        </nav>
      </aside>
      <section className="flex-1">{children}</section>
    </div>
  );
}
```

### Template — Re-renders Every Navigation

```jsx
// app/dashboard/template.jsx
// Unlike layout, this component RE-MOUNTS on every navigation
// Use for: entrance animations, logging page views, resetting state

export default function DashboardTemplate({ children }) {
  // This useEffect would fire on EVERY page change within /dashboard
  return <div className="animate-fadeIn">{children}</div>;
}
```

### Loading UI

```jsx
// app/posts/loading.jsx
// Automatically shown while page.jsx is awaiting data
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-3/4 mb-4" />
      <div className="h-4 bg-gray-200 rounded w-full mb-2" />
      <div className="h-4 bg-gray-200 rounded w-5/6" />
    </div>
  );
}
```

### Error Handling

```jsx
// app/posts/error.jsx — MUST be "use client"
"use client";

export default function Error({ error, reset }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <p>{error.message}</p>
      <button onClick={() => reset()}>Try Again</button>
    </div>
  );
}
```

### Not Found

```jsx
// app/not-found.jsx — Custom 404 page
import Link from 'next/link';

export default function NotFound() {
  return (
    <div>
      <h1>404 — Page Not Found</h1>
      <Link href="/">Go Home</Link>
    </div>
  );
}
```

```jsx
// Programmatically trigger 404
import { notFound } from 'next/navigation';

export default async function PostPage({ params }) {
  const post = await getPost(params.id);
  if (!post) notFound();  // ← shows not-found.jsx
  return <h1>{post.title}</h1>;
}
```

### Rendering Order

```
Request for /dashboard/settings:

RootLayout (app/layout.jsx)
  └── DashboardLayout (app/dashboard/layout.jsx)
       └── DashboardTemplate (app/dashboard/template.jsx)
            └── Loading (app/dashboard/settings/loading.jsx)  ← while awaiting
            └── SettingsPage (app/dashboard/settings/page.jsx) ← when ready
            └── Error (app/dashboard/settings/error.jsx)       ← if crashed
```

---

## 9. Middleware

Middleware runs **before every request** — for auth checks, redirects, rewrites, headers.

```javascript
// middleware.js (MUST be in project root, NOT in app/)
import { NextResponse } from 'next/server';

export function middleware(request) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('auth-token');

  // Redirect unauthenticated users away from protected routes
  if (pathname.startsWith('/dashboard') && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Add custom headers
  const response = NextResponse.next();
  response.headers.set('x-request-id', crypto.randomUUID());
  return response;
}

// Only run middleware on these paths
export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};
```

### Common Middleware Patterns

```javascript
// middleware.js — multiple concerns
import { NextResponse } from 'next/server';

export function middleware(request) {
  const { pathname } = request.nextUrl;

  // 1. Auth check
  if (isProtectedRoute(pathname) && !isAuthenticated(request)) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // 2. Geo-based redirect
  const country = request.geo?.country || 'US';
  if (pathname === '/' && country === 'IN') {
    return NextResponse.rewrite(new URL('/in', request.url));
  }

  // 3. Rate limiting header
  const response = NextResponse.next();
  response.headers.set('X-RateLimit-Remaining', '99');

  // 4. CORS
  if (pathname.startsWith('/api/')) {
    response.headers.set('Access-Control-Allow-Origin', '*');
  }

  return response;
}

function isProtectedRoute(pathname) {
  return pathname.startsWith('/dashboard') || pathname.startsWith('/settings');
}

function isAuthenticated(request) {
  return request.cookies.has('session');
}
```

---

## 10. API Routes (Route Handlers)

### App Router — `route.js` files

```
app/
└── api/
    ├── posts/
    │   ├── route.js              → GET/POST /api/posts
    │   └── [id]/
    │       └── route.js          → GET/PUT/DELETE /api/posts/123
    └── auth/
        └── route.js              → /api/auth
```

### Basic CRUD API

```javascript
// app/api/posts/route.js
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// GET /api/posts
export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '10');

  const posts = await prisma.post.findMany({
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: 'desc' },
  });

  return NextResponse.json(posts);
}

// POST /api/posts
export async function POST(request) {
  const body = await request.json();

  if (!body.title || !body.content) {
    return NextResponse.json(
      { error: 'Title and content are required' },
      { status: 400 }
    );
  }

  const post = await prisma.post.create({
    data: { title: body.title, content: body.content },
  });

  return NextResponse.json(post, { status: 201 });
}
```

```javascript
// app/api/posts/[id]/route.js
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

// GET /api/posts/123
export async function GET(request, { params }) {
  const { id } = await params;
  const post = await prisma.post.findUnique({ where: { id } });

  if (!post) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }
  return NextResponse.json(post);
}

// PUT /api/posts/123
export async function PUT(request, { params }) {
  const { id } = await params;
  const body = await request.json();

  const post = await prisma.post.update({
    where: { id },
    data: body,
  });
  return NextResponse.json(post);
}

// DELETE /api/posts/123
export async function DELETE(request, { params }) {
  const { id } = await params;
  await prisma.post.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
```

### When to Use API Routes vs Server Actions

| Use API Route (`route.js`) | Use Server Action |
|---|---|
| External clients consume it (mobile app, third-party) | Only your own Next.js app uses it |
| Webhook endpoints | Form submissions |
| Need custom HTTP methods/headers | Simple mutations (create, update, delete) |
| Public API | Internal data changes |

---

## 11. State Management — Redux, Zustand, Context

### When Do You Need State Management in App Router?

```
Server data (posts, products, user profile):
  → Fetch in Server Components. No state library needed.

Client-only state (cart, theme, modals, notifications):
  → You need a state library. Choose one:
     - Small/medium app: Zustand or React Context
     - Large app with complex state: Redux Toolkit
     - Simple shared state: React Context
```

### Option 1: Redux Toolkit (Full Setup)

#### Install

```bash
npm install @reduxjs/toolkit react-redux
```

#### Store Setup

```javascript
// lib/store/store.js
import { configureStore } from '@reduxjs/toolkit';
import cartReducer from './slices/cartSlice';
import uiReducer from './slices/uiSlice';

export const makeStore = () => {
  return configureStore({
    reducer: {
      cart: cartReducer,
      ui: uiReducer,
    },
  });
};
```

#### Cart Slice

```javascript
// lib/store/slices/cartSlice.js
import { createSlice } from '@reduxjs/toolkit';

const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    items: [],
    total: 0,
  },
  reducers: {
    addItem(state, action) {
      const existing = state.items.find(i => i.id === action.payload.id);
      if (existing) {
        existing.quantity += 1;
      } else {
        state.items.push({ ...action.payload, quantity: 1 });
      }
      state.total = state.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    },
    removeItem(state, action) {
      state.items = state.items.filter(i => i.id !== action.payload);
      state.total = state.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    },
    clearCart(state) {
      state.items = [];
      state.total = 0;
    },
  },
});

export const { addItem, removeItem, clearCart } = cartSlice.actions;
export default cartSlice.reducer;
```

#### Provider (Must Be Client Component)

```jsx
// lib/store/provider.jsx
"use client";
import { useRef } from 'react';
import { Provider } from 'react-redux';
import { makeStore } from './store';

export function StoreProvider({ children }) {
  const storeRef = useRef(null);
  if (!storeRef.current) {
    storeRef.current = makeStore();
  }
  return <Provider store={storeRef.current}>{children}</Provider>;
}
```

#### Wire into Layout

```jsx
// app/layout.jsx
import { StoreProvider } from '@/lib/store/provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <StoreProvider>
          {children}
        </StoreProvider>
      </body>
    </html>
  );
}
```

#### Use in Components

```jsx
// app/products/[id]/add-to-cart.jsx
"use client";
import { useDispatch, useSelector } from 'react-redux';
import { addItem } from '@/lib/store/slices/cartSlice';

export function AddToCart({ product }) {
  const dispatch = useDispatch();
  const cartCount = useSelector(state => state.cart.items.length);

  return (
    <button onClick={() => dispatch(addItem(product))}>
      Add to Cart ({cartCount} items)
    </button>
  );
}
```

#### Async Actions (Thunks)

```javascript
// lib/store/slices/cartSlice.js (continued)
import { createAsyncThunk } from '@reduxjs/toolkit';

export const checkout = createAsyncThunk(
  'cart/checkout',
  async (_, { getState }) => {
    const { cart } = getState();
    const response = await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify({ items: cart.items }),
    });
    return response.json();
  }
);

// In the slice:
extraReducers: (builder) => {
  builder
    .addCase(checkout.pending, (state) => { state.status = 'loading'; })
    .addCase(checkout.fulfilled, (state) => {
      state.items = [];
      state.total = 0;
      state.status = 'succeeded';
    })
    .addCase(checkout.rejected, (state, action) => {
      state.status = 'failed';
      state.error = action.error.message;
    });
}
```

### Option 2: Zustand (Simpler Alternative)

```bash
npm install zustand
```

```javascript
// lib/store/cart-store.js
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      total: 0,

      addItem: (product) => set((state) => {
        const existing = state.items.find(i => i.id === product.id);
        if (existing) {
          const items = state.items.map(i =>
            i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
          );
          return { items, total: items.reduce((s, i) => s + i.price * i.quantity, 0) };
        }
        const items = [...state.items, { ...product, quantity: 1 }];
        return { items, total: items.reduce((s, i) => s + i.price * i.quantity, 0) };
      }),

      removeItem: (id) => set((state) => {
        const items = state.items.filter(i => i.id !== id);
        return { items, total: items.reduce((s, i) => s + i.price * i.quantity, 0) };
      }),

      clearCart: () => set({ items: [], total: 0 }),
    }),
    { name: 'cart-storage' }  // persists to localStorage
  )
);
```

```jsx
// Usage — no Provider needed!
"use client";
import { useCartStore } from '@/lib/store/cart-store';

export function AddToCart({ product }) {
  const addItem = useCartStore(state => state.addItem);
  const count = useCartStore(state => state.items.length);

  return (
    <button onClick={() => addItem(product)}>
      Add to Cart ({count})
    </button>
  );
}
```

### Option 3: React Context (Built-in, No Library)

```jsx
// lib/context/theme-context.jsx
"use client";
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  const toggle = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
```

### Comparison

| Feature | Redux Toolkit | Zustand | React Context |
|---|---|---|---|
| Bundle size | ~11KB | ~1KB | 0KB |
| Boilerplate | High | Low | Medium |
| DevTools | Excellent | Good | Basic |
| Middleware | Yes (thunks, saga) | Yes | Manual |
| Persist state | Extra setup | Built-in | Manual |
| Performance (many consumers) | Good (selectors) | Good | Poor (re-renders all) |
| Provider needed | Yes | No | Yes |
| Best for | Large apps, complex state | Medium apps | Simple shared state |

---

## 12. Authentication — NextAuth.js / Auth.js

### Install

```bash
npm install next-auth
```

### Setup

```javascript
// app/api/auth/[...nextauth]/route.js
import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import CredentialsProvider from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/db';
import bcrypt from 'bcrypt';

const handler = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
        });
        if (!user) return null;
        const valid = await bcrypt.compare(credentials.password, user.password);
        if (!valid) return null;
        return user;
      },
    }),
  ],
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
    error: '/auth/error',
  },
});

export { handler as GET, handler as POST };
```

### Session Provider

```jsx
// app/layout.jsx
import { SessionProvider } from './session-provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
```

```jsx
// app/session-provider.jsx
"use client";
import { SessionProvider as Provider } from 'next-auth/react';

export function SessionProvider({ children }) {
  return <Provider>{children}</Provider>;
}
```

### Use in Server Components

```jsx
// app/dashboard/page.jsx — Server Component
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await getServerSession();

  if (!session) {
    redirect('/login');
  }

  return <h1>Welcome {session.user.name}</h1>;
}
```

### Use in Client Components

```jsx
// app/components/auth-button.jsx
"use client";
import { useSession, signIn, signOut } from 'next-auth/react';

export function AuthButton() {
  const { data: session, status } = useSession();

  if (status === 'loading') return <p>Loading...</p>;

  if (session) {
    return (
      <div>
        <span>{session.user.email}</span>
        <button onClick={() => signOut()}>Sign Out</button>
      </div>
    );
  }

  return <button onClick={() => signIn('google')}>Sign In with Google</button>;
}
```

### Protecting Routes with Middleware

```javascript
// middleware.js
import { withAuth } from 'next-auth/middleware';

export default withAuth({
  pages: { signIn: '/login' },
});

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*'],
};
```

---

## 13. Database Integration — Prisma, Drizzle

### Prisma Setup

```bash
npm install prisma @prisma/client
npx prisma init
```

```prisma
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
}

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

```bash
npx prisma migrate dev --name init   # create tables
npx prisma generate                  # generate client
```

### Prisma Client Singleton

```javascript
// lib/db.js
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis;

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
```

### Using Prisma in Server Components

```jsx
// app/posts/page.jsx
import { prisma } from '@/lib/db';

export default async function PostsPage() {
  const posts = await prisma.post.findMany({
    where: { published: true },
    include: { author: true },
    orderBy: { createdAt: 'desc' },
  });

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>
          <h2>{post.title}</h2>
          <p>By {post.author.name}</p>
        </li>
      ))}
    </ul>
  );
}
```

---

## 14. Styling — Tailwind, CSS Modules, Styled Components

### Tailwind CSS (Default in Next.js)

```jsx
// Already configured with create-next-app
export function Card({ title, description }) {
  return (
    <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-gray-600">{description}</p>
    </div>
  );
}
```

### CSS Modules

```css
/* app/components/button.module.css */
.button {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
}
.primary {
  background-color: #3b82f6;
  color: white;
}
.secondary {
  background-color: #e5e7eb;
  color: #1f2937;
}
```

```jsx
// app/components/button.jsx
import styles from './button.module.css';

export function Button({ variant = 'primary', children }) {
  return (
    <button className={`${styles.button} ${styles[variant]}`}>
      {children}
    </button>
  );
}
```

### Global CSS

```css
/* app/globals.css — imported in root layout */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground: #171717;
  --background: #ffffff;
}

body {
  color: var(--foreground);
  background: var(--background);
}
```

---

## 15. Image, Font, and Script Optimization

### Image Component

```jsx
import Image from 'next/image';

// Local image
import heroImage from '@/public/hero.jpg';

export function Hero() {
  return (
    <Image
      src={heroImage}
      alt="Hero banner"
      width={1200}
      height={600}
      priority           // load immediately (above-the-fold)
      placeholder="blur" // show blur while loading
    />
  );
}

// Remote image
export function Avatar({ user }) {
  return (
    <Image
      src={user.avatarUrl}
      alt={user.name}
      width={48}
      height={48}
      className="rounded-full"
    />
  );
}
```

```javascript
// next.config.js — allow remote images
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'avatars.githubusercontent.com' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
    ],
  },
};
export default nextConfig;
```

### Font Optimization

```jsx
// app/layout.jsx
import { Inter, Roboto_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  variable: '--font-roboto-mono',
});

export default function RootLayout({ children }) {
  return (
    <html className={`${inter.variable} ${robotoMono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
```

### Script Optimization

```jsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        {/* Load after page is interactive */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=GA_ID"
          strategy="afterInteractive"
        />
        {/* Load when browser is idle */}
        <Script src="/analytics.js" strategy="lazyOnload" />
      </body>
    </html>
  );
}
```

---

## 16. Caching and Revalidation

### Next.js Caching Layers

```
Request → [Router Cache] → [Full Route Cache] → [Data Cache] → Origin
              (client)         (server CDN)       (server)       (DB/API)
```

### Controlling Cache Behavior

```jsx
// Cache forever (default for fetch in Server Components)
const data = await fetch('https://api.example.com/posts');

// Never cache (SSR — always fresh)
const data = await fetch('https://api.example.com/posts', {
  cache: 'no-store',
});

// Cache for 60 seconds then revalidate (ISR)
const data = await fetch('https://api.example.com/posts', {
  next: { revalidate: 60 },
});

// Cache with a tag (for on-demand revalidation)
const data = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] },
});
```

### On-Demand Revalidation

```javascript
// app/api/revalidate/route.js — webhook endpoint
import { revalidateTag, revalidatePath } from 'next/cache';

export async function POST(request) {
  const { tag, path } = await request.json();

  if (tag) revalidateTag(tag);    // invalidate all fetches with this tag
  if (path) revalidatePath(path); // invalidate a specific page

  return Response.json({ revalidated: true });
}
```

```jsx
// In a Server Action — revalidate after mutation
"use server";
import { revalidatePath, revalidateTag } from 'next/cache';

export async function createPost(formData) {
  await prisma.post.create({ data: { ... } });

  revalidatePath('/posts');         // re-render the posts page
  revalidateTag('posts');           // invalidate all 'posts' tagged fetches
}
```

---

## 17. Streaming and Suspense

### What Is Streaming?

Instead of waiting for ALL data before sending HTML, stream parts of the page as they're ready:

```
Traditional SSR:
  [wait for ALL data......] → [send complete HTML]

Streaming:
  [send shell immediately] → [stream post content when ready] → [stream comments when ready]
```

### Using Suspense for Streaming

```jsx
// app/posts/[id]/page.jsx
import { Suspense } from 'react';

export default function PostPage({ params }) {
  return (
    <div>
      {/* This loads instantly */}
      <h1>Post Page</h1>

      {/* This streams in when data is ready */}
      <Suspense fallback={<p>Loading post...</p>}>
        <PostContent id={params.id} />
      </Suspense>

      {/* This streams independently */}
      <Suspense fallback={<p>Loading comments...</p>}>
        <Comments postId={params.id} />
      </Suspense>
    </div>
  );
}

// These are async Server Components
async function PostContent({ id }) {
  const post = await fetch(`/api/posts/${id}`).then(r => r.json()); // 200ms
  return <article>{post.content}</article>;
}

async function Comments({ postId }) {
  const comments = await fetch(`/api/posts/${postId}/comments`).then(r => r.json()); // 2000ms
  return (
    <ul>
      {comments.map(c => <li key={c.id}>{c.text}</li>)}
    </ul>
  );
}
```

The user sees:
1. Instant: shell + "Loading post..." + "Loading comments..."
2. After 200ms: post content appears, comments still loading
3. After 2000ms: comments appear

---

### Streaming SSR vs Traditional SSR — The Full Picture

#### Traditional SSR — The Waterfall Problem

```
Traditional SSR (Next.js Pages Router / getServerSideProps):

User request arrives
       │
       ▼
┌────────────────────────────────────────────────────────────┐
│  Server must complete ALL of this before sending ANYTHING: │
│                                                            │
│  1. Fetch user data from DB ─────── 100ms                 │
│  2. Fetch post from DB ──────────── 200ms                 │
│  3. Fetch comments from API ─────── 800ms                 │
│  4. Fetch recommendations ───────── 1500ms                │
│  5. Render ALL components to HTML ─ 50ms                  │
│                                                            │
│  TOTAL: 2650ms before user sees ANYTHING                  │
└────────────────────────────────────────────────────────────┘
       │
       ▼ (after 2650ms)
Server sends complete HTML (all at once)
       │
       ▼
Browser paints entire page
       │
       ▼
Download JS bundle
       │
       ▼
Hydrate ENTIRE page (all-or-nothing)
       │
       ▼
Page is interactive

PROBLEMS:
1. Slowest data fetch blocks EVERYTHING (recommendations = 1500ms delay)
2. User sees white screen for 2.65 seconds
3. Hydration is all-or-nothing (entire page must hydrate before ANY interaction)
4. If one section's data fails, the whole page can fail
```

#### Streaming SSR — Progressive Rendering

```
Streaming SSR (Next.js App Router with Suspense):

User request arrives
       │
       ▼
Server immediately sends HTML shell + CSS (0ms wait)
       │
       ├─► Browser paints: navbar, layout, loading skeletons (50ms)
       │   USER CAN ALREADY SEE THE PAGE!
       │
       │   Meanwhile, server fetches data in PARALLEL:
       │
       ├─► User data ready (100ms) → stream <UserProfile/> chunk
       │   Browser: replaces skeleton with real content
       │
       ├─► Post data ready (200ms) → stream <PostContent/> chunk  
       │   Browser: replaces "Loading post..." with actual post
       │
       ├─► Comments ready (800ms) → stream <Comments/> chunk
       │   Browser: replaces "Loading comments..." with real comments
       │   HYDRATES just this chunk (selective hydration)
       │
       └─► Recommendations ready (1500ms) → stream <Recommendations/> chunk
           Browser: replaces skeleton with recommendations
           HYDRATES just this chunk

RESULT:
  - First paint: 50ms (not 2650ms!)
  - Post visible: 200ms
  - Comments visible: 800ms
  - Fully loaded: 1500ms
  - NO section blocks another
```

#### Side-by-Side Comparison

| Aspect | Traditional SSR | Streaming SSR |
|---|---|---|
| First Byte (TTFB) | After ALL data fetched | Immediate (shell) |
| First Contentful Paint | 2-5 seconds | 50-100ms |
| Blocking | Slowest fetch blocks everything | Nothing blocks |
| Failure handling | Whole page fails | Only failed section shows error |
| Hydration | All-or-nothing | Selective (per Suspense boundary) |
| User experience | Blank screen → full page | Progressive: skeleton → content |
| HTTP response | One big chunk | Multiple chunks over time |
| Server memory | Must hold entire HTML in memory | Streams out as generated |
| Browser rendering | Wait for full HTML → render once | Render chunks as they arrive |

#### How Streaming Works Under the Hood (HTTP Chunked Transfer)

```
Traditional SSR HTTP Response:
  HTTP/1.1 200 OK
  Content-Length: 45000
  
  <html><body>...entire page 45KB...</body></html>
  [CONNECTION CLOSED]


Streaming SSR HTTP Response:
  HTTP/1.1 200 OK
  Transfer-Encoding: chunked     ← key difference!
  
  CHUNK 1 (immediate):
  <html><body>
    <nav>My App</nav>
    <main>
      <div id="post">Loading...</div>
      <div id="comments">Loading...</div>
    </main>

  CHUNK 2 (after 200ms):
  <script>
    // Replace loading placeholder with real content
    document.getElementById('post').innerHTML = '<article>...</article>';
  </script>

  CHUNK 3 (after 800ms):
  <script>
    document.getElementById('comments').innerHTML = '<ul>...</ul>';
  </script>

  [CONNECTION CLOSED after all chunks sent]
```

#### Code: Traditional SSR (Pages Router)

```jsx
// pages/posts/[id].jsx — TRADITIONAL SSR
// ALL data must be fetched before ANY HTML is sent

export async function getServerSideProps({ params }) {
  // These run SEQUENTIALLY or in parallel, but ALL must complete
  const [post, comments, recommendations, user] = await Promise.all([
    fetch(`/api/posts/${params.id}`).then(r => r.json()),        // 200ms
    fetch(`/api/posts/${params.id}/comments`).then(r => r.json()), // 800ms
    fetch(`/api/recommendations`).then(r => r.json()),            // 1500ms ← BLOCKS!
    fetch(`/api/user`).then(r => r.json()),                       // 100ms
  ]);
  // Even with Promise.all, must wait for slowest (1500ms)

  return { props: { post, comments, recommendations, user } };
}

export default function PostPage({ post, comments, recommendations, user }) {
  return (
    <div>
      <UserBanner user={user} />
      <article>{post.content}</article>
      <CommentsList comments={comments} />
      <Recommendations items={recommendations} />
    </div>
  );
}
// User waits 1500ms seeing NOTHING, then entire page appears at once
```

#### Code: Streaming SSR (App Router)

```jsx
// app/posts/[id]/page.jsx — STREAMING SSR
// Each section loads independently, streams to browser when ready

import { Suspense } from 'react';
import { PostSkeleton, CommentsSkeleton, RecommendationsSkeleton } from './skeletons';

export default function PostPage({ params }) {
  return (
    <div>
      {/* Streams immediately — no await */}
      <nav>My App</nav>

      {/* Each Suspense boundary = independent stream */}
      <Suspense fallback={<PostSkeleton />}>
        <PostContent id={params.id} />
      </Suspense>

      <Suspense fallback={<CommentsSkeleton />}>
        <Comments postId={params.id} />
      </Suspense>

      <Suspense fallback={<RecommendationsSkeleton />}>
        <Recommendations />
      </Suspense>
    </div>
  );
}

// Each component fetches its OWN data — no single bottleneck
async function PostContent({ id }) {
  const post = await fetch(`https://api.example.com/posts/${id}`, {
    cache: 'no-store',
  }).then(r => r.json());
  return <article>{post.content}</article>;  // streams at 200ms
}

async function Comments({ postId }) {
  const comments = await fetch(`https://api.example.com/posts/${postId}/comments`, {
    cache: 'no-store',
  }).then(r => r.json());
  return (  // streams at 800ms
    <ul>{comments.map(c => <li key={c.id}>{c.text}</li>)}</ul>
  );
}

async function Recommendations() {
  const items = await fetch('https://api.example.com/recommendations', {
    cache: 'no-store',
  }).then(r => r.json());
  return (  // streams at 1500ms — doesn't block anything else!
    <aside>{items.map(i => <Card key={i.id} item={i} />)}</aside>
  );
}
```

#### Selective Hydration — The Hidden Superpower

Traditional SSR hydrates the **entire page at once**. If hydration takes 500ms, nothing is interactive for 500ms.

Streaming SSR hydrates **each Suspense boundary independently**:

```
Traditional Hydration:
  [download ALL JS] → [hydrate ENTIRE page] → interactive
  Total blocking time: 500ms (nothing clickable)

Selective Hydration (Streaming):
  [download JS] → [hydrate navbar] → navbar clickable! (50ms)
                → [hydrate post] → post links clickable! (100ms)
                → [hydrate comments] → comment buttons work! (200ms)
                → [hydrate recommendations] → cards clickable! (300ms)

  Navbar is interactive 450ms BEFORE the recommendations are hydrated.
```

Even better — React **prioritizes hydration** based on user interaction:

```
User clicks on a comment button while recommendations are still hydrating.
React: "Let me hydrate comments FIRST since the user is trying to interact there."
       → Comments become interactive immediately.
       → Recommendations hydrate later.
```

#### Streaming SSR with Error Boundaries

If one section fails, only THAT section shows an error — not the whole page:

```jsx
// app/posts/[id]/page.jsx
import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

export default function PostPage({ params }) {
  return (
    <div>
      {/* Post is critical — if it fails, show error for this section */}
      <ErrorBoundary fallback={<p>Failed to load post</p>}>
        <Suspense fallback={<PostSkeleton />}>
          <PostContent id={params.id} />
        </Suspense>
      </ErrorBoundary>

      {/* Comments are optional — if they fail, page still works */}
      <ErrorBoundary fallback={<p>Comments unavailable</p>}>
        <Suspense fallback={<CommentsSkeleton />}>
          <Comments postId={params.id} />
        </Suspense>
      </ErrorBoundary>

      {/* Recommendations are nice-to-have */}
      <ErrorBoundary fallback={null}>
        <Suspense fallback={<RecommendationsSkeleton />}>
          <Recommendations />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
```

With traditional SSR: if recommendations API is down → entire page returns 500 error.  
With streaming SSR: if recommendations API is down → only that section is empty, rest works fine.

#### When to Use Streaming SSR vs Traditional SSR

| Scenario | Use Traditional SSR | Use Streaming SSR |
|---|---|---|
| Simple page with one data source | ✅ Simpler code | Overkill |
| Page with multiple independent data sources | Slow (bottlenecked) | ✅ Each loads independently |
| Critical above-the-fold content | Works fine | ✅ Shows faster |
| Page where sections have very different load times | Bad UX (all-or-nothing) | ✅ Progressive loading |
| SEO-critical pages | Both work for SEO | ✅ Better Core Web Vitals |
| Pages with optional non-critical sections | If one fails, all fails | ✅ Graceful degradation |

#### Summary: Why Streaming SSR Is the Default in App Router

```
Next.js App Router made Streaming SSR the DEFAULT because:

1. FASTER first paint (user sees content in <100ms, not 2+ seconds)
2. NO single bottleneck (slowest API doesn't block the page)
3. SELECTIVE hydration (interactive faster, priority-based)
4. GRACEFUL errors (one failure doesn't kill the page)
5. LOWER server memory (stream out, don't buffer entire HTML)
6. BETTER Core Web Vitals (LCP, FID, CLS all improve)

You get it for FREE just by using Suspense boundaries.
No configuration, no special setup.
```

---

## 18. Parallel and Intercepting Routes

### Parallel Routes — Render Multiple Pages Simultaneously

Show multiple independent sections that load independently:

```
app/
└── dashboard/
    ├── layout.jsx
    ├── page.jsx
    ├── @analytics/           ← slot name starts with @
    │   └── page.jsx
    ├── @notifications/
    │   └── page.jsx
    └── @activity/
        └── page.jsx
```

```jsx
// app/dashboard/layout.jsx
export default function DashboardLayout({ children, analytics, notifications, activity }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2">{children}</div>
      <div>{analytics}</div>
      <div>{notifications}</div>
      <div>{activity}</div>
    </div>
  );
}
```

Each slot loads independently — if analytics is slow, notifications still appear.

### Intercepting Routes — Modal Pattern

Show a route as a modal without full navigation:

```
app/
├── posts/
│   └── [id]/
│       └── page.jsx              ← Full page (direct URL access)
├── @modal/
│   └── (.)posts/
│       └── [id]/
│           └── page.jsx          ← Modal version (when navigating from feed)
└── feed/
    └── page.jsx                  ← Contains links to posts
```

Convention: `(.)` = same level, `(..)` = one level up, `(...)` = root level.

When user clicks a post link from the feed → shows modal.  
When user directly visits `/posts/123` → shows full page.

---

## 19. Internationalization (i18n)

### Using next-intl

```bash
npm install next-intl
```

```
app/
└── [locale]/              ← dynamic segment for language
    ├── layout.jsx
    ├── page.jsx
    └── posts/
        └── page.jsx
messages/
├── en.json
└── es.json
```

```json
// messages/en.json
{
  "home": {
    "title": "Welcome",
    "description": "The best blog on the internet"
  },
  "posts": {
    "title": "All Posts",
    "readMore": "Read more"
  }
}
```

```json
// messages/es.json
{
  "home": {
    "title": "Bienvenido",
    "description": "El mejor blog en internet"
  }
}
```

```jsx
// app/[locale]/page.jsx
import { useTranslations } from 'next-intl';

export default function HomePage() {
  const t = useTranslations('home');

  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
    </div>
  );
}
```

---

## 20. Testing — Complete Strategy and Best Practices

### The Next.js Testing Pyramid

```
           ╱╲
          ╱  ╲         E2E Tests (Playwright/Cypress)
         ╱ E2E╲        — Full browser, real server, real DB
        ╱──────╲       — Slow (seconds), few tests
       ╱        ╲
      ╱Integration╲   Integration Tests
     ╱──────────────╲  — Server Components, API routes, Server Actions
    ╱                ╲ — Moderate speed, moderate count
   ╱   Component      ╲ Component Tests (React Testing Library)
  ╱────────────────────╲ — Client Components in isolation
 ╱                      ╲
╱       Unit Tests       ╲ Unit Tests (Jest/Vitest)
╱────────────────────────╲ — Pure functions, utilities, hooks
                            — Fast (ms), many tests
```

### Setup — Install Everything

```bash
# Core testing
npm install -D jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom

# For TypeScript
npm install -D ts-jest @types/jest

# For React hooks testing
npm install -D @testing-library/react-hooks

# E2E
npm install -D @playwright/test

# Optional: Vitest (faster alternative to Jest, Vite-based)
npm install -D vitest @vitejs/plugin-react happy-dom
```

### Folder Structure

```
my-app/
├── app/                        ← your app code
├── __tests__/                  ← test files mirror app structure
│   ├── unit/
│   │   ├── utils.test.ts
│   │   └── hooks/
│   │       └── useCart.test.ts
│   ├── components/
│   │   ├── button.test.tsx
│   │   ├── cart.test.tsx
│   │   └── login-form.test.tsx
│   ├── integration/
│   │   ├── api/
│   │   │   └── posts.test.ts
│   │   └── actions/
│   │       └── create-post.test.ts
│   └── e2e/
│       ├── auth.spec.ts
│       ├── checkout.spec.ts
│       └── posts.spec.ts
├── jest.config.js
├── jest.setup.js
└── playwright.config.ts
```

### Jest Configuration

```javascript
// jest.config.js
const nextJest = require('next/jest');

const createJestConfig = nextJest({ dir: './' });

const customConfig = {
  setupFilesAfterFramework: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',  // support @/ imports
  },
  testPathIgnorePatterns: ['<rootDir>/__tests__/e2e/'],  // exclude E2E
};

module.exports = createJestConfig(customConfig);
```

```javascript
// jest.setup.js
import '@testing-library/jest-dom';
```

---

### Layer 1: Unit Tests — Pure Functions, No React

```typescript
// lib/utils/format-price.ts
export function formatPrice(cents: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(cents / 100);
}

export function calculateDiscount(price: number, discountPercent: number): number {
  if (discountPercent < 0 || discountPercent > 100) {
    throw new Error('Discount must be between 0 and 100');
  }
  return Math.round(price * (1 - discountPercent / 100));
}
```

```typescript
// __tests__/unit/utils.test.ts
import { formatPrice, calculateDiscount } from '@/lib/utils/format-price';

describe('formatPrice', () => {
  it('formats cents to dollars', () => {
    expect(formatPrice(1999)).toBe('$19.99');
    expect(formatPrice(500)).toBe('$5.00');
    expect(formatPrice(0)).toBe('$0.00');
  });

  it('handles different currencies', () => {
    expect(formatPrice(1000, 'EUR')).toContain('€');
  });
});

describe('calculateDiscount', () => {
  it('calculates percentage discount', () => {
    expect(calculateDiscount(10000, 20)).toBe(8000);  // $100 - 20% = $80
    expect(calculateDiscount(5000, 50)).toBe(2500);
  });

  it('handles edge cases', () => {
    expect(calculateDiscount(1000, 0)).toBe(1000);    // no discount
    expect(calculateDiscount(1000, 100)).toBe(0);     // free
  });

  it('throws on invalid discount', () => {
    expect(() => calculateDiscount(1000, -10)).toThrow('between 0 and 100');
    expect(() => calculateDiscount(1000, 150)).toThrow('between 0 and 100');
  });
});
```

### Testing Custom Hooks

```typescript
// lib/hooks/useCart.ts
"use client";
import { useState, useCallback } from 'react';

export function useCart() {
  const [items, setItems] = useState([]);

  const addItem = useCallback((product) => {
    setItems(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) {
        return prev.map(i => i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  }, []);

  const removeItem = useCallback((id) => {
    setItems(prev => prev.filter(i => i.id !== id));
  }, []);

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  return { items, addItem, removeItem, total };
}
```

```typescript
// __tests__/unit/hooks/useCart.test.ts
import { renderHook, act } from '@testing-library/react';
import { useCart } from '@/lib/hooks/useCart';

describe('useCart', () => {
  const mockProduct = { id: '1', name: 'Shirt', price: 2999 };

  it('starts with empty cart', () => {
    const { result } = renderHook(() => useCart());
    expect(result.current.items).toHaveLength(0);
    expect(result.current.total).toBe(0);
  });

  it('adds an item', () => {
    const { result } = renderHook(() => useCart());
    act(() => { result.current.addItem(mockProduct); });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].quantity).toBe(1);
    expect(result.current.total).toBe(2999);
  });

  it('increments quantity for duplicate item', () => {
    const { result } = renderHook(() => useCart());
    act(() => { result.current.addItem(mockProduct); });
    act(() => { result.current.addItem(mockProduct); });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].quantity).toBe(2);
    expect(result.current.total).toBe(5998);
  });

  it('removes an item', () => {
    const { result } = renderHook(() => useCart());
    act(() => { result.current.addItem(mockProduct); });
    act(() => { result.current.removeItem('1'); });

    expect(result.current.items).toHaveLength(0);
    expect(result.current.total).toBe(0);
  });
});
```

---

### Layer 2: Component Tests — Client Components in Isolation

```tsx
// app/components/login-form.tsx
"use client";
import { useState } from 'react';

export function LoginForm({ onSubmit }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('All fields are required');
      return;
    }
    await onSubmit({ email, password });
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Login form">
      {error && <p role="alert">{error}</p>}
      <label htmlFor="email">Email</label>
      <input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} />
      <label htmlFor="password">Password</label>
      <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button type="submit">Sign In</button>
    </form>
  );
}
```

```tsx
// __tests__/components/login-form.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from '@/app/components/login-form';

describe('LoginForm', () => {
  const mockSubmit = jest.fn();

  beforeEach(() => {
    mockSubmit.mockClear();
  });

  it('renders all fields', () => {
    render(<LoginForm onSubmit={mockSubmit} />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
  });

  it('shows error when submitting empty form', async () => {
    render(<LoginForm onSubmit={mockSubmit} />);
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(screen.getByRole('alert')).toHaveTextContent('All fields are required');
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('calls onSubmit with email and password', async () => {
    render(<LoginForm onSubmit={mockSubmit} />);

    await userEvent.type(screen.getByLabelText('Email'), 'test@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  it('clears error when user starts typing', async () => {
    render(<LoginForm onSubmit={mockSubmit} />);

    // Trigger error
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));
    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Start typing — submit again with data
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.com');
    await userEvent.type(screen.getByLabelText('Password'), 'pass');
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
```

### Testing Components with Redux

```tsx
// __tests__/components/cart.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import cartReducer from '@/lib/store/slices/cartSlice';
import { CartSummary } from '@/app/components/cart-summary';

function renderWithRedux(component, { initialState } = {}) {
  const store = configureStore({
    reducer: { cart: cartReducer },
    preloadedState: initialState,
  });
  return {
    ...render(<Provider store={store}>{component}</Provider>),
    store,
  };
}

describe('CartSummary', () => {
  it('shows empty cart message', () => {
    renderWithRedux(<CartSummary />);
    expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
  });

  it('shows items and total', () => {
    renderWithRedux(<CartSummary />, {
      initialState: {
        cart: {
          items: [
            { id: '1', name: 'Shirt', price: 2999, quantity: 2 },
            { id: '2', name: 'Pants', price: 4999, quantity: 1 },
          ],
          total: 10997,
        },
      },
    });

    expect(screen.getByText('Shirt')).toBeInTheDocument();
    expect(screen.getByText('Pants')).toBeInTheDocument();
    expect(screen.getByText('$109.97')).toBeInTheDocument();
  });
});
```

---

### Layer 3: Integration Tests — Server Actions and API Routes

```typescript
// __tests__/integration/actions/create-post.test.ts
// Testing Server Actions requires mocking the database

import { createPost } from '@/app/actions/posts';
import { prisma } from '@/lib/db';
import { revalidatePath } from 'next/cache';

// Mock Prisma
jest.mock('@/lib/db', () => ({
  prisma: {
    post: {
      create: jest.fn(),
    },
  },
}));

// Mock Next.js cache functions
jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

describe('createPost Server Action', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('creates a post with valid data', async () => {
    const formData = new FormData();
    formData.set('title', 'Test Post');
    formData.set('body', 'This is the body content of the post');

    (prisma.post.create as jest.Mock).mockResolvedValue({ id: '1', title: 'Test Post' });

    await createPost(formData);

    expect(prisma.post.create).toHaveBeenCalledWith({
      data: { title: 'Test Post', body: 'This is the body content of the post' },
    });
    expect(revalidatePath).toHaveBeenCalledWith('/posts');
  });

  it('returns errors for invalid data', async () => {
    const formData = new FormData();
    formData.set('title', 'ab');  // too short (min 3)
    formData.set('body', 'short');  // too short (min 10)

    const result = await createPost({}, formData);

    expect(result.errors).toBeDefined();
    expect(prisma.post.create).not.toHaveBeenCalled();
  });
});
```

### Testing API Routes

```typescript
// __tests__/integration/api/posts.test.ts
import { GET, POST } from '@/app/api/posts/route';
import { prisma } from '@/lib/db';

jest.mock('@/lib/db');

describe('POST /api/posts', () => {
  it('returns 201 with valid data', async () => {
    const mockPost = { id: '1', title: 'Test', content: 'Hello world' };
    (prisma.post.create as jest.Mock).mockResolvedValue(mockPost);

    const request = new Request('http://localhost/api/posts', {
      method: 'POST',
      body: JSON.stringify({ title: 'Test', content: 'Hello world' }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(201);
    expect(data.title).toBe('Test');
  });

  it('returns 400 with missing title', async () => {
    const request = new Request('http://localhost/api/posts', {
      method: 'POST',
      body: JSON.stringify({ content: 'No title here' }),
    });

    const response = await POST(request);
    expect(response.status).toBe(400);
  });
});

describe('GET /api/posts', () => {
  it('returns paginated posts', async () => {
    const mockPosts = [{ id: '1', title: 'Post 1' }, { id: '2', title: 'Post 2' }];
    (prisma.post.findMany as jest.Mock).mockResolvedValue(mockPosts);

    const request = new Request('http://localhost/api/posts?page=1&limit=10');
    const response = await GET(request);
    const data = await response.json();

    expect(data).toHaveLength(2);
    expect(prisma.post.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 0, take: 10 })
    );
  });
});
```

---

### Layer 4: E2E Tests — Full Browser with Playwright

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './__tests__/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

```typescript
// __tests__/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });

  test('logs in with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('shows error with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByText('Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('logs out successfully', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/dashboard');

    // Logout
    await page.getByRole('button', { name: 'Sign Out' }).click();
    await expect(page).toHaveURL('/');
  });
});
```

```typescript
// __tests__/e2e/checkout.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();
  });

  test('full checkout flow', async ({ page }) => {
    // Browse products
    await page.goto('/products');
    await page.getByText('Add to Cart').first().click();

    // Check cart badge updated
    await expect(page.getByTestId('cart-count')).toHaveText('1');

    // Go to cart
    await page.goto('/cart');
    await expect(page.getByRole('heading', { name: 'Your Cart' })).toBeVisible();
    await expect(page.getByText('1 item')).toBeVisible();

    // Proceed to checkout
    await page.getByRole('button', { name: 'Checkout' }).click();
    await expect(page).toHaveURL('/checkout');

    // Fill shipping info
    await page.getByLabel('Address').fill('123 Main St');
    await page.getByLabel('City').fill('New York');
    await page.getByLabel('Zip').fill('10001');

    // Submit order
    await page.getByRole('button', { name: 'Place Order' }).click();

    // Verify success
    await expect(page.getByText('Order Confirmed')).toBeVisible();
    await expect(page.getByText('Order #')).toBeVisible();
  });

  test('shows error when cart is empty', async ({ page }) => {
    await page.goto('/checkout');
    await expect(page.getByText('Your cart is empty')).toBeVisible();
  });
});
```

### Testing with Network Mocking (Playwright)

```typescript
// __tests__/e2e/posts.spec.ts
import { test, expect } from '@playwright/test';

test('displays posts from API', async ({ page }) => {
  // Mock the API response
  await page.route('**/api/posts', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: '1', title: 'Mocked Post 1' },
        { id: '2', title: 'Mocked Post 2' },
      ]),
    });
  });

  await page.goto('/posts');
  await expect(page.getByText('Mocked Post 1')).toBeVisible();
  await expect(page.getByText('Mocked Post 2')).toBeVisible();
});

test('handles API errors gracefully', async ({ page }) => {
  await page.route('**/api/posts', async (route) => {
    await route.fulfill({ status: 500 });
  });

  await page.goto('/posts');
  await expect(page.getByText('Something went wrong')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Try Again' })).toBeVisible();
});
```

---

### Testing Best Practices

#### Best Practice 1: Test Behavior, Not Implementation

```tsx
// WRONG — testing implementation details
it('sets isLoading state to true', () => {
  const { result } = renderHook(() => useData());
  expect(result.current.isLoading).toBe(true);  // tests internal state
});

// RIGHT — testing what the user sees
it('shows loading spinner while fetching', () => {
  render(<PostsList />);
  expect(screen.getByRole('progressbar')).toBeVisible();
});
```

#### Best Practice 2: Use Accessible Queries

```tsx
// WRONG — fragile selectors
screen.getByTestId('submit-btn');          // meaningless to user
screen.getByClassName('btn-primary');       // styling concern

// RIGHT — query like a user would find elements
screen.getByRole('button', { name: 'Submit' });   // accessible
screen.getByLabelText('Email');                    // form fields
screen.getByText('Welcome back');                  // visible text
screen.getByPlaceholderText('Search...');          // input placeholder
```

#### Best Practice 3: Query Priority (from best to worst)

```
1. getByRole         ← best (accessible, how users/screen readers find things)
2. getByLabelText    ← great for form inputs
3. getByPlaceholderText ← good fallback for inputs
4. getByText         ← good for non-interactive elements
5. getByDisplayValue ← form elements with current value
6. getByAltText      ← images
7. getByTitle        ← tooltips
8. getByTestId       ← LAST RESORT (not user-facing)
```

#### Best Practice 4: Use userEvent over fireEvent

```tsx
// WRONG — fireEvent is low-level
fireEvent.change(input, { target: { value: 'hello' } });

// RIGHT — userEvent simulates real user behavior
await userEvent.type(input, 'hello');
// This fires: focus, keydown, keypress, input, keyup for EACH character
// Catches bugs that fireEvent.change would miss
```

#### Best Practice 5: Wait for Async Operations

```tsx
// WRONG — test runs before async operation completes
it('creates a post', () => {
  render(<CreatePostForm />);
  userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('Post created')).toBeVisible();  // ❌ fails — not rendered yet
});

// RIGHT — waitFor or findBy queries
it('creates a post', async () => {
  render(<CreatePostForm />);
  await userEvent.click(screen.getByRole('button'));
  await waitFor(() => {
    expect(screen.getByText('Post created')).toBeVisible();  // ✅ waits for it
  });
  // OR use findBy (combines getBy + waitFor):
  expect(await screen.findByText('Post created')).toBeVisible();
});
```

#### Best Practice 6: One Assertion Per Test (Mostly)

```tsx
// WRONG — testing everything in one test
it('does everything', async () => {
  render(<LoginForm />);
  expect(screen.getByLabelText('Email')).toBeVisible();
  expect(screen.getByLabelText('Password')).toBeVisible();
  await userEvent.type(...);
  await userEvent.click(...);
  expect(screen.getByText('Welcome')).toBeVisible();
});

// RIGHT — focused tests with clear failure messages
it('renders email and password fields', () => { ... });
it('shows validation error when email is empty', () => { ... });
it('calls onSubmit with credentials', async () => { ... });
it('shows loading state during submission', async () => { ... });
```

#### Best Practice 7: Test Error States and Edge Cases

```tsx
describe('ProductPage', () => {
  it('shows product details on success', async () => { ... });
  it('shows 404 when product does not exist', async () => { ... });
  it('shows error message on network failure', async () => { ... });
  it('shows loading skeleton while fetching', () => { ... });
  it('handles product with no images gracefully', async () => { ... });
  it('shows "Out of Stock" when quantity is 0', async () => { ... });
});
```

#### Best Practice 8: Isolate Tests — No Shared State

```tsx
// WRONG — tests depend on each other
let cart;
beforeAll(() => { cart = createCart(); });

it('adds item', () => { cart.add(item); expect(cart.items).toHaveLength(1); });
it('shows total', () => { expect(cart.total).toBe(2999); });  // depends on previous!

// RIGHT — each test starts fresh
describe('Cart', () => {
  let cart;
  beforeEach(() => { cart = createCart(); });  // fresh cart every time

  it('adds item', () => {
    cart.add(item);
    expect(cart.items).toHaveLength(1);
  });

  it('starts with zero total', () => {
    expect(cart.total).toBe(0);  // independent
  });
});
```

#### Best Practice 9: Mock at the Right Level

```
For unit tests: mock everything external (DB, APIs, other modules)
For component tests: mock API calls (MSW or jest.mock), render real components
For integration tests: mock only the database layer
For E2E tests: mock NOTHING (or only third-party services like Stripe)
```

```tsx
// Mock API calls with MSW (Mock Service Worker) — recommended
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.get('/api/posts', () => {
    return HttpResponse.json([
      { id: '1', title: 'Test Post' },
    ]);
  }),
  http.post('/api/posts', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '2', ...body }, { status: 201 });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

#### Best Practice 10: Test Accessibility

```tsx
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

### What to Test at Each Level — Summary

| Layer | What to Test | What NOT to Test |
|---|---|---|
| **Unit** | Pure functions, utilities, custom hooks, calculations | React rendering, DOM |
| **Component** | User interactions, form validation, conditional rendering, error states | Implementation details, internal state |
| **Integration** | Server Actions + DB, API routes, auth flows | UI rendering |
| **E2E** | Critical user journeys (login, checkout, create/edit/delete) | Every possible path |

### npm Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "jest && playwright test"
  }
}
```

### Coverage Targets (Industry Standard)

```
Overall:      > 80% line coverage
Unit/Hooks:   > 90% (they're fast and easy)
Components:   > 70% (focus on behavior)
Integration:  > 60% (critical paths)
E2E:          Cover top 5-10 user journeys
```

---

## 21. Deployment — Vercel, Docker, Self-Hosted

### Vercel (Easiest — Built for Next.js)

```bash
npm install -g vercel
vercel          # deploy in one command
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

```javascript
// next.config.js — enable standalone output for Docker
const nextConfig = {
  output: 'standalone',
};
export default nextConfig;
```

### Self-Hosted (PM2)

```bash
npm run build
pm2 start npm --name "next-app" -- start
```

---

## 22. Performance Optimization

### Bundle Analysis

```bash
npm install -D @next/bundle-analyzer
```

```javascript
// next.config.js
import withBundleAnalyzer from '@next/bundle-analyzer';

const config = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})({});

export default config;
```

```bash
ANALYZE=true npm run build   # generates visual bundle report
```

### Key Optimizations

```jsx
// 1. Dynamic imports — load heavy components only when needed
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('./chart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false,  // don't render on server (client-only library)
});

// 2. Lazy load below-the-fold content
import dynamic from 'next/dynamic';
const Comments = dynamic(() => import('./comments'));

// 3. Optimize images (automatic with next/image)
import Image from 'next/image';
<Image src="/hero.jpg" width={800} height={400} alt="Hero" priority />

// 4. Prefetch links (automatic with next/link)
import Link from 'next/link';
<Link href="/posts">Posts</Link>  // prefetches on hover/viewport

// 5. Route segment config
export const dynamic = 'force-static';  // cache the whole page
export const revalidate = 3600;         // refresh every hour
```

### Core Web Vitals Targets

| Metric | What It Measures | Target |
|---|---|---|
| LCP (Largest Contentful Paint) | When main content is visible | < 2.5s |
| FID (First Input Delay) | Response time to first interaction | < 100ms |
| CLS (Cumulative Layout Shift) | Visual stability | < 0.1 |
| INP (Interaction to Next Paint) | Responsiveness | < 200ms |

---

## 23. Important Libraries Ecosystem

### Must-Know Libraries for Next.js

| Category | Library | Purpose |
|---|---|---|
| **State** | Redux Toolkit | Complex global state |
| **State** | Zustand | Simple global state |
| **State** | Jotai | Atomic state |
| **Data Fetching** | TanStack Query | Client-side caching + mutations |
| **Data Fetching** | SWR | Lightweight data fetching (by Vercel) |
| **Forms** | React Hook Form | Performant forms |
| **Forms** | Zod | Schema validation |
| **Auth** | NextAuth.js / Auth.js | Authentication |
| **Auth** | Clerk | Managed auth (easier) |
| **Database** | Prisma | Type-safe ORM |
| **Database** | Drizzle | Lightweight ORM |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Styling** | shadcn/ui | Pre-built Tailwind components |
| **Styling** | Framer Motion | Animations |
| **UI** | Radix UI | Headless accessible components |
| **UI** | Headless UI | Headless components (by Tailwind) |
| **Testing** | Jest | Unit tests |
| **Testing** | Playwright | E2E tests |
| **Testing** | React Testing Library | Component tests |
| **File Upload** | UploadThing | File uploads for Next.js |
| **Email** | React Email + Resend | Transactional emails |
| **Payments** | Stripe | Payment processing |
| **Real-time** | Pusher / Socket.io | WebSockets |
| **CMS** | Contentful / Sanity | Headless CMS |
| **Analytics** | Vercel Analytics | Web analytics |
| **Monitoring** | Sentry | Error tracking |

### Common Stack Combinations

```
"The Vercel Stack" (most popular):
  Next.js + Tailwind + shadcn/ui + Prisma + NextAuth + Vercel

"The T3 Stack":
  Next.js + TypeScript + tRPC + Tailwind + Prisma + NextAuth

"Enterprise Stack":
  Next.js + Redux + TanStack Query + Prisma + Clerk + Docker + AWS
```

---

## 24. Interview Critical Concepts

### Q1: What is the difference between SSR, SSG, and ISR?

```
SSR: HTML generated on EVERY request. Fresh data, slower TTFB.
     → fetch('...', { cache: 'no-store' })

SSG: HTML generated at BUILD TIME. Fastest, but stale until rebuild.
     → fetch('...') [default, cached forever]

ISR: HTML generated at build time + REVALIDATED every N seconds.
     Best of both worlds: fast + eventually fresh.
     → fetch('...', { next: { revalidate: 60 } })
```

### Q2: What is hydration? Why can it cause bugs?

```
Hydration: React attaches event handlers to server-rendered HTML.
Server HTML and client render MUST match.

Bug: "Hydration mismatch" — when server renders one thing and client renders another.

Common cause:
  - Using Date.now() or Math.random() (different on server vs client)
  - Checking window/localStorage (doesn't exist on server)
  - Browser extensions modifying DOM

Fix:
  - Use useEffect for browser-only logic
  - Use suppressHydrationWarning for intentional mismatches
  - Wrap in "use client" + dynamic import with ssr: false
```

### Q3: What is the difference between `redirect()` and `router.push()`?

```
redirect():
  - Server-side (Server Components, Server Actions, Middleware)
  - Throws internally, stops execution
  - Returns HTTP 307/308 redirect

router.push():
  - Client-side only ("use client" components)
  - Programmatic navigation
  - Client-side transition (no full page reload)
```

### Q4: How does Next.js handle code splitting?

```
Automatic per route:
  /posts    → downloads only posts page JS
  /about    → downloads only about page JS

Each "use client" component boundary creates a separate chunk.
Server Components ship ZERO JS to the browser.

Dynamic imports for heavy libraries:
  const Chart = dynamic(() => import('./chart'), { ssr: false })
```

### Q5: What is the purpose of `generateStaticParams`?

```jsx
// Tells Next.js which dynamic routes to pre-render at build time (SSG)
// app/posts/[id]/page.jsx

export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return posts.map(post => ({ id: post.id.toString() }));
}
// Now /posts/1, /posts/2, /posts/3 are all pre-rendered as static HTML
```

### Q6: How do you handle SEO in Next.js?

```jsx
// app/posts/[id]/page.jsx

// Static metadata
export const metadata = {
  title: 'My Blog',
  description: 'Welcome to my blog',
};

// Dynamic metadata (based on data)
export async function generateMetadata({ params }) {
  const post = await getPost(params.id);
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      images: [post.coverImage],
    },
  };
}
```

### Q7: What is the difference between `fetch` in Server vs Client Components?

```
Server Component fetch:
  - Runs on Node.js server
  - Automatically deduped (same URL = one request)
  - Cached by default (can configure)
  - Can access internal APIs without full URL
  - Results never sent to browser

Client Component fetch:
  - Runs in user's browser
  - Not deduped
  - No cache by default
  - Must use full URLs
  - Subject to CORS
```

### Q8: Explain the rendering flow when a user visits a page

```
1. Request hits server (or CDN if cached)
2. Middleware runs (auth check, redirects)
3. Layout components render (top-down)
4. Page component renders (fetches data if async)
5. HTML stream sent to browser
6. Browser paints HTML (user sees content)
7. JS bundles download (only for Client Components)
8. Hydration (event handlers attached)
9. Page is interactive
```

### Q9: What are Server Actions and why do they replace API routes?

```
Before (API route approach):
  1. Create /api/posts/route.js with POST handler
  2. Client calls fetch('/api/posts', { method: 'POST', body: ... })
  3. API route validates + saves to DB
  4. Return response

After (Server Action approach):
  1. Create function with "use server"
  2. Call it from a form action or client component
  3. Function validates + saves to DB
  4. Revalidate cache automatically

Advantages:
  - No manual fetch boilerplate
  - Type-safe (TypeScript knows the function signature)
  - Progressive enhancement (works without JS)
  - Automatic form state management
```

### Q10: What is the "use client" boundary and how does it affect the component tree?

```
"use client" marks the BOUNDARY between server and client.
Everything below that boundary becomes a Client Component.

// app/page.jsx (Server)
import { Header } from './header';  // also Server (no directive)
import { Form } from './form';      // Client (has "use client")

// The tree:
ServerPage
  ├── Header (Server — no JS shipped)
  └── Form (Client — JS shipped)
       ├── Input (Client — inherits from parent)
       └── Button (Client — inherits from parent)

IMPORTANT: Once you mark a component "use client",
ALL its children become client components too,
UNLESS passed as {children} from a Server Component.
```

### Q11: How do you handle environment variables?

```
.env.local:
  DATABASE_URL=postgres://...          ← server only
  API_SECRET=abc123                    ← server only
  NEXT_PUBLIC_SITE_URL=https://...     ← exposed to browser

Rules:
  - NEXT_PUBLIC_ prefix → available everywhere (server + client)
  - No prefix → server only (Server Components, API routes, middleware)
  - NEVER put secrets in NEXT_PUBLIC_ variables
```

### Q12: What is Partial Pre-Rendering (PPR)?

```
Next.js 14+ experimental feature.
Combines static shell + dynamic content in ONE request:

┌─────────────────────────────────┐
│ Static Shell (cached on CDN)    │  ← instant from edge
│  ┌──────────────────────────┐  │
│  │ Dynamic Hole (streamed)  │  │  ← server-rendered in real-time
│  └──────────────────────────┘  │
└─────────────────────────────────┘

The static parts serve instantly from CDN.
The dynamic parts stream in from the server.
No configuration needed — just use Suspense boundaries.
```

---

## 25. Common Mistakes and Gotchas

### Mistake 1: Using hooks in Server Components

```jsx
// WRONG
export default function Page() {
  const [count, setCount] = useState(0);  // ❌ Error!
  return <p>{count}</p>;
}

// RIGHT — add "use client" or move state to a child component
"use client";
export default function Page() {
  const [count, setCount] = useState(0);  // ✅
  return <p>{count}</p>;
}
```

### Mistake 2: Fetching in Client Component when Server can do it

```jsx
// WRONG — unnecessary client-side fetch
"use client";
export default function Posts() {
  const [posts, setPosts] = useState([]);
  useEffect(() => {
    fetch('/api/posts').then(r => r.json()).then(setPosts);
  }, []);
  return <ul>{posts.map(...)}</ul>;
}

// RIGHT — fetch on server, zero JS shipped
export default async function Posts() {
  const posts = await prisma.post.findMany();
  return <ul>{posts.map(...)}</ul>;
}
```

### Mistake 3: Marking entire page as "use client"

```jsx
// WRONG — everything ships as JS to browser
"use client";
export default function ProductPage() {
  const [quantity, setQuantity] = useState(1);
  // Now the product data fetch ALSO runs in browser...
}

// RIGHT — only the interactive part is client
// page.jsx (server — fetches product)
import { QuantitySelector } from './quantity-selector';
export default async function ProductPage({ params }) {
  const product = await getProduct(params.id);
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <QuantitySelector price={product.price} />
    </div>
  );
}

// quantity-selector.jsx (client — handles interaction)
"use client";
export function QuantitySelector({ price }) {
  const [qty, setQty] = useState(1);
  return <div>...</div>;
}
```

### Mistake 4: Not handling loading/error states

```jsx
// WRONG — page hangs if fetch is slow
export default async function Page() {
  const data = await slowFetch();  // user waits, sees nothing
  return <div>{data}</div>;
}

// RIGHT — add loading.jsx or Suspense
// loading.jsx handles the loading state automatically!
```

### Mistake 5: Exposing secrets via NEXT_PUBLIC_

```
# .env.local
NEXT_PUBLIC_DB_URL=postgres://user:pass@db    ← ❌ EXPOSED to browser!
DATABASE_URL=postgres://user:pass@db          ← ✅ server only
```

### Mistake 6: Not understanding caching

```jsx
// This is cached FOREVER by default — might show stale data
const data = await fetch('https://api.example.com/prices');

// Add no-store for always-fresh data
const data = await fetch('https://api.example.com/prices', { cache: 'no-store' });

// Or revalidate periodically
const data = await fetch('https://api.example.com/prices', { next: { revalidate: 30 } });
```

### Mistake 7: Hydration mismatches

```jsx
// WRONG — different output on server vs client
export default function Page() {
  return <p>Current time: {new Date().toLocaleString()}</p>;
  // Server renders "3:00 PM", client renders "3:00:01 PM" → mismatch!
}

// RIGHT — use useEffect for time-dependent content
"use client";
export default function Page() {
  const [time, setTime] = useState('');
  useEffect(() => { setTime(new Date().toLocaleString()); }, []);
  return <p>Current time: {time}</p>;
}
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│ NEXT.JS APP ROUTER CHEAT SHEET                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ROUTING:                                                        │
│   page.jsx        = route content                               │
│   layout.jsx      = persistent wrapper                          │
│   loading.jsx     = suspense fallback                           │
│   error.jsx       = error boundary                              │
│   not-found.jsx   = 404 page                                    │
│   route.js        = API endpoint                                │
│   [param]         = dynamic segment                             │
│   [...slug]       = catch-all                                   │
│   (group)         = folder group (not in URL)                   │
│                                                                 │
│ RENDERING:                                                      │
│   Default         = Server Component (no JS shipped)            │
│   "use client"    = Client Component (JS shipped)               │
│   cache:'no-store'= SSR (fresh every request)                   │
│   revalidate: N   = ISR (refresh every N seconds)               │
│   default fetch   = SSG (cached forever)                        │
│                                                                 │
│ DATA:                                                           │
│   Server: await fetch() or await db.query()                     │
│   Client: useEffect, SWR, or TanStack Query                    │
│   Mutate: Server Actions ("use server")                         │
│                                                                 │
│ STATE:                                                          │
│   Server data    → fetch in Server Component (no state lib)     │
│   Client state   → Redux / Zustand / Context                   │
│                                                                 │
│ CACHE CONTROL:                                                  │
│   revalidatePath('/posts')     ← refresh specific page          │
│   revalidateTag('posts')       ← refresh tagged fetches         │
│   router.refresh()             ← client-side refetch            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
