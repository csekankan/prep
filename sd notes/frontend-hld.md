# Frontend System Design — Advanced FAANG Reference Guide

Everything you need to ace frontend system design interviews at FAANG — from rendering pipelines and state management to performance optimization and real-world architecture.

---

## Table of Contents

1. [How Frontend System Design Interviews Work](#1-how-frontend-system-design-interviews-work)
2. [The Framework: How To Answer Any Question](#2-the-framework-how-to-answer-any-question)
3. [Rendering Pipeline & Browser Internals](#3-rendering-pipeline--browser-internals)
4. [Component Architecture & Design Patterns](#4-component-architecture--design-patterns)
5. [State Management at Scale](#5-state-management-at-scale)
6. [Data Fetching & API Layer](#6-data-fetching--api-layer)
7. [Real-Time Systems](#7-real-time-systems)
8. [Performance Optimization](#8-performance-optimization)
9. [Virtualization & Large Data Rendering](#9-virtualization--large-data-rendering)
10. [Caching Strategies](#10-caching-strategies)
11. [Offline-First & PWA Architecture](#11-offline-first--pwa-architecture)
12. [Security](#12-security)
13. [Accessibility (a11y)](#13-accessibility-a11y)
14. [Internationalization (i18n)](#14-internationalization-i18n)
15. [Testing Architecture](#15-testing-architecture)
16. [Build Systems & Module Federation](#16-build-systems--module-federation)
17. [Micro-Frontends](#17-micro-frontends)
18. [Observability & Monitoring](#18-observability--monitoring)
19. [Design System Architecture](#19-design-system-architecture)
20. [SEO & Core Web Vitals](#20-seo--core-web-vitals)
21. [Image & Media Architecture](#21-image--media-architecture)
22. [Authentication & Authorization Flows](#22-authentication--authorization-flows)
23. [Client-Side Storage Deep Dive](#23-client-side-storage-deep-dive)
24. [Networking & Protocol Optimization](#24-networking--protocol-optimization)
25. [Deployment, CI/CD & Feature Flags](#25-deployment-cicd--feature-flags)
26. [Design: Facebook News Feed](#26-design-facebook-news-feed)
27. [Design: Google Search Autocomplete](#27-design-google-search-autocomplete)
28. [Design: Google Docs (Collaborative Editor)](#28-design-google-docs-collaborative-editor)
29. [Design: Instagram Stories / TikTok Feed](#29-design-instagram-stories--tiktok-feed)
30. [Design: Slack / Chat Application](#30-design-slack--chat-application)
31. [Design: E-Commerce Product Page (Amazon)](#31-design-e-commerce-product-page-amazon)
32. [Design: Google Maps](#32-design-google-maps)
33. [Design: Spreadsheet (Google Sheets)](#33-design-spreadsheet-google-sheets)
34. [Design: Video Player (YouTube)](#34-design-video-player-youtube)
35. [Design: Notification System](#35-design-notification-system)
36. [Cheatsheet & Interview Quick Reference](#36-cheatsheet--interview-quick-reference)

---

## 1. How Frontend System Design Interviews Work

### What Interviewers Evaluate

```
1. Requirements Gathering    — Can you ask the RIGHT questions?
2. High-Level Architecture   — Can you break a complex UI into subsystems?
3. Component Design          — Can you design composable, reusable components?
4. Data Model & API          — Can you define clean data contracts?
5. Performance               — Do you think about scale from the start?
6. Trade-Off Analysis        — Can you justify decisions with reasoning?
7. Edge Cases & Reliability  — Do you think about failure states?
```

### Common Mistakes

```
❌ Jumping into code immediately
❌ Designing only the "happy path"
❌ Ignoring accessibility and i18n
❌ Not discussing trade-offs (just picking one solution)
❌ Treating it like a backend system design (focus stays on the CLIENT)
❌ Over-engineering: picking micro-frontends for a todo app
❌ Ignoring offline / poor network scenarios
```

### Signal Levels

```
L3-L4 (Junior/Mid):
  - Basic component breakdown
  - Simple state management
  - Knows REST APIs

L5 (Senior):
  - Deep performance analysis (CWV, bundle splitting)
  - State management trade-offs at scale
  - Caching strategies, optimistic updates
  - Accessibility baked in

L6+ (Staff/Principal):
  - Cross-team architectural decisions
  - Build system & deployment strategy
  - Observability, monitoring, alerting
  - Micro-frontends, design systems
  - Organizational scaling (how 50 teams ship to one app)
```

---

## 2. The Framework: How To Answer Any Question

### Step-by-Step Framework (Use This for EVERY Question)

```
┌─────────────────────────────────────────────────────┐
│  1. REQUIREMENTS (3-5 min)                          │
│     ├── Functional: What does the user DO?          │
│     ├── Non-Functional: Scale, perf, a11y, i18n     │
│     └── Out of scope: What are we NOT building?     │
│                                                     │
│  2. HIGH-LEVEL ARCHITECTURE (5-7 min)               │
│     ├── Component tree / page layout                │
│     ├── Client-server boundary                      │
│     ├── Rendering strategy (CSR/SSR/SSG/ISR)        │
│     └── Third-party dependencies                    │
│                                                     │
│  3. DATA MODEL & API (5-7 min)                      │
│     ├── API endpoints / GraphQL schema              │
│     ├── Client-side data models                     │
│     ├── Normalization strategy                      │
│     └── Caching & invalidation                      │
│                                                     │
│  4. COMPONENT DEEP DIVE (10-15 min)                 │
│     ├── Component API (props/state/events)          │
│     ├── State management approach                   │
│     ├── Rendering behavior & optimization           │
│     └── Error states, loading states, empty states  │
│                                                     │
│  5. PERFORMANCE & OPTIMIZATION (5-7 min)            │
│     ├── Bundle size & code splitting                │
│     ├── Rendering performance                       │
│     ├── Network optimization                        │
│     └── Perceived performance                       │
│                                                     │
│  6. ACCESSIBILITY & EDGE CASES (3-5 min)            │
│     ├── Keyboard navigation                         │
│     ├── Screen reader support                       │
│     ├── Offline behavior                            │
│     └── Error handling & recovery                   │
└─────────────────────────────────────────────────────┘
```

---

## 3. Rendering Pipeline & Browser Internals

Understanding how browsers work is the foundation of all frontend optimization.

### The Critical Rendering Path

```
                    Network
                      │
                      ▼
            ┌──────────────────┐
            │   HTML Parsing   │ ──► DOM Tree
            └──────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   CSS Parsing    │ ──► CSSOM Tree
            └──────────────────┘
                      │
          DOM + CSSOM combine
                      │
                      ▼
            ┌──────────────────┐
            │   Render Tree    │  (only visible nodes)
            └──────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │     Layout       │  (geometry: position, size)
            └──────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │     Paint        │  (pixels: color, shadows, text)
            └──────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   Composite      │  (GPU layers merged)
            └──────────────────┘
```

### What Triggers What

```
┌─────────────────────────────────────────────────────────────┐
│ LAYOUT (Reflow) — Most expensive                            │
│ Triggers: width, height, top, left, margin, padding,        │
│           font-size, display, position, float               │
│ Causes: Layout → Paint → Composite                          │
├─────────────────────────────────────────────────────────────┤
│ PAINT — Moderately expensive                                │
│ Triggers: color, background, border-radius, box-shadow,     │
│           visibility, outline                               │
│ Causes: Paint → Composite                                   │
├─────────────────────────────────────────────────────────────┤
│ COMPOSITE ONLY — Cheapest (GPU-accelerated)                 │
│ Triggers: transform, opacity, will-change                   │
│ Causes: Composite only                                      │
└─────────────────────────────────────────────────────────────┘
```

### Browser Process Architecture (Chrome)

```
┌─────────────────────────────────────────────┐
│ Browser Process                              │
│   ├── UI Thread (address bar, tabs)          │
│   ├── Network Thread (HTTP, DNS)             │
│   └── Storage Thread (IndexedDB, cookies)    │
├─────────────────────────────────────────────┤
│ Renderer Process (one per tab/site)          │
│   ├── Main Thread                            │
│   │     ├── JS execution                     │
│   │     ├── DOM manipulation                 │
│   │     ├── Style calculation                │
│   │     ├── Layout                           │
│   │     └── Paint (recording)                │
│   ├── Compositor Thread                      │
│   │     └── Compositing layers               │
│   ├── Raster Threads                         │
│   │     └── Rasterizing paint records        │
│   └── Worker Threads                         │
│         └── Web Workers, Service Workers     │
├─────────────────────────────────────────────┤
│ GPU Process                                  │
│   └── Draws tiles, composites layers         │
└─────────────────────────────────────────────┘
```

### Event Loop Deep Dive

```
┌──────────────────────────────────────────────────────────────┐
│                     EVENT LOOP                                │
│                                                              │
│  ┌─────────────┐     ┌──────────────┐    ┌────────────────┐  │
│  │  Call Stack  │     │  Task Queue  │    │ Microtask Queue│  │
│  │  (LIFO)     │     │  (FIFO)      │    │ (FIFO)         │  │
│  └─────────────┘     └──────────────┘    └────────────────┘  │
│                                                              │
│  Execution Order:                                            │
│  1. Execute all synchronous code (call stack)                │
│  2. Drain ALL microtasks (Promise.then, queueMicrotask,      │
│     MutationObserver)                                        │
│  3. Render if needed (requestAnimationFrame → Style →        │
│     Layout → Paint)                                          │
│  4. Pick ONE macrotask (setTimeout, setInterval,             │
│     MessageChannel, I/O)                                     │
│  5. Go to step 2                                             │
│                                                              │
│  Priority: Microtasks > rAF > Macrotasks                     │
└──────────────────────────────────────────────────────────────┘
```

```javascript
// Classic interview question — predict the output
console.log('1');                          // sync
setTimeout(() => console.log('2'), 0);     // macrotask
Promise.resolve().then(() => console.log('3')); // microtask
requestAnimationFrame(() => console.log('4'));   // before next paint
console.log('5');                          // sync

// Output: 1, 5, 3, 4, 2
// (rAF timing can vary, but microtasks always before macrotasks)
```

### requestAnimationFrame vs requestIdleCallback

```
requestAnimationFrame (rAF):
  - Runs BEFORE the browser paints (~16ms for 60fps)
  - Use for: animations, layout reads, DOM mutations
  - Guaranteed to run once per frame

requestIdleCallback (rIC):
  - Runs when the browser is IDLE (no pending work)
  - Use for: analytics, prefetching, non-urgent work
  - NOT guaranteed to run — may be starved
  - Pass { timeout: ms } for deadline guarantee
  - NOT available in Safari (use setTimeout fallback)
```

---

## 4. Component Architecture & Design Patterns

### Component Taxonomy

```
┌───────────────────────────────────────────────────┐
│               Component Types                      │
├───────────────────────────────────────────────────┤
│                                                   │
│  Presentational (Dumb)                            │
│  ├── Pure rendering, no side effects              │
│  ├── Receives data via props                      │
│  ├── Highly reusable, easy to test                │
│  └── Example: Button, Card, Avatar                │
│                                                   │
│  Container (Smart)                                │
│  ├── Manages state, data fetching                 │
│  ├── Connects to stores / context                 │
│  ├── Passes data down to presentational           │
│  └── Example: UserProfilePage, DashboardContainer │
│                                                   │
│  Layout                                           │
│  ├── Structural positioning only                  │
│  ├── No business logic                            │
│  └── Example: Grid, Stack, Sidebar, PageShell     │
│                                                   │
│  Higher-Order Component (HOC)                     │
│  ├── Wraps component, adds behavior               │
│  ├── Cross-cutting concerns (auth, logging)       │
│  └── Example: withAuth, withTheme                 │
│                                                   │
│  Headless (Renderless)                            │
│  ├── Logic only, no UI                            │
│  ├── Consumer provides rendering                  │
│  ├── Maximum flexibility                          │
│  └── Example: useCombobox, Downshift, React Table │
│                                                   │
│  Compound Components                              │
│  ├── Group of components sharing implicit state   │
│  ├── Parent manages state, children consume       │
│  └── Example: <Tabs>, <Tab>, <TabPanel>           │
│                                                   │
└───────────────────────────────────────────────────┘
```

### Compound Component Pattern

```jsx
// Parent manages state, children read it via context
const TabsContext = React.createContext();

function Tabs({ children, defaultIndex = 0 }) {
  const [activeIndex, setActiveIndex] = useState(defaultIndex);
  return (
    <TabsContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div role="tablist">{children}</div>
    </TabsContext.Provider>
  );
}

function Tab({ index, children }) {
  const { activeIndex, setActiveIndex } = useContext(TabsContext);
  return (
    <button
      role="tab"
      aria-selected={activeIndex === index}
      onClick={() => setActiveIndex(index)}
    >
      {children}
    </button>
  );
}

function TabPanel({ index, children }) {
  const { activeIndex } = useContext(TabsContext);
  if (activeIndex !== index) return null;
  return <div role="tabpanel">{children}</div>;
}

// Usage — clean, declarative API
<Tabs defaultIndex={0}>
  <Tab index={0}>Profile</Tab>
  <Tab index={1}>Settings</Tab>
  <TabPanel index={0}><Profile /></TabPanel>
  <TabPanel index={1}><Settings /></TabPanel>
</Tabs>
```

### Render Props Pattern

```jsx
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => setPosition({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return render(position);
}

// Usage
<MouseTracker render={({ x, y }) => <Cursor x={x} y={y} />} />
```

### Headless Component (Hook-based)

```jsx
function useToggle(initialState = false) {
  const [isOn, setIsOn] = useState(initialState);
  const toggle = useCallback(() => setIsOn(prev => !prev), []);
  const setOn = useCallback(() => setIsOn(true), []);
  const setOff = useCallback(() => setIsOn(false), []);
  return { isOn, toggle, setOn, setOff };
}

function useClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      handler(event);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
```

### Inversion of Control — Slot Pattern

```jsx
function Card({ header, body, footer, actions }) {
  return (
    <div className="card">
      {header && <div className="card-header">{header}</div>}
      <div className="card-body">{body}</div>
      {actions && <div className="card-actions">{actions}</div>}
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
}

// Consumer has full control over each slot
<Card
  header={<h2>Order Summary</h2>}
  body={<OrderDetails order={order} />}
  actions={<Button onClick={checkout}>Checkout</Button>}
/>
```

---

## 5. State Management at Scale

### State Categories

```
┌──────────────────────────────────────────────────────────┐
│                    State Taxonomy                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. UI State (local)                                     │
│     - Modal open/closed, accordion expanded              │
│     - Form input values mid-edit                         │
│     - Tooltip visibility                                 │
│     → useState, useReducer                               │
│                                                          │
│  2. Server State (remote/cached)                         │
│     - User profile, product list, search results         │
│     - Has authoritative source on server                 │
│     - Needs cache invalidation, background refetch       │
│     → React Query / TanStack Query, SWR, Apollo Cache    │
│                                                          │
│  3. URL State                                            │
│     - Current page, filters, sort order, search query    │
│     - Must survive refresh, be shareable                 │
│     → Router params, searchParams, history API           │
│                                                          │
│  4. Global Client State                                  │
│     - Auth status, theme, locale, feature flags          │
│     - Shared across many components                      │
│     → Context, Zustand, Redux, Jotai                     │
│                                                          │
│  5. Derived State                                        │
│     - Computed from other state (totalPrice, isValid)    │
│     - NEVER store — always compute                       │
│     → useMemo, selectors, computed properties            │
│                                                          │
│  6. Form State                                           │
│     - Validation, dirty tracking, submission status      │
│     - Complex nested structures, arrays of fields        │
│     → React Hook Form, Formik, final-form                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### State Management Decision Matrix

```
Question: "Where should this state live?"

Is it derived from other state?
  └── YES → Don't store it. Compute it. (useMemo / selector)

Is it only used by one component?
  └── YES → useState / useReducer

Is it needed by a parent and child?
  └── YES → Lift state to nearest common ancestor

Does it come from the server?
  └── YES → Server state library (TanStack Query / SWR)

Should it survive page refresh?
  └── YES → URL state (searchParams) or localStorage

Is it truly global (auth, theme)?
  └── YES → Context + useReducer, or Zustand / Redux

Is it shared by 2-3 siblings?
  └── YES → Lift to parent, pass down as props
```

### Normalized State Shape

```
❌ BAD: Nested / Denormalized
{
  posts: [
    {
      id: 1,
      title: "Hello",
      author: { id: 10, name: "Alice" },
      comments: [
        { id: 100, text: "Great!", author: { id: 11, name: "Bob" } }
      ]
    }
  ]
}

Problems:
- Updating Alice's name requires finding her in every post
- Duplicate data everywhere
- Deep updates are error-prone

✅ GOOD: Normalized (like a database)
{
  entities: {
    users: {
      10: { id: 10, name: "Alice" },
      11: { id: 11, name: "Bob" }
    },
    posts: {
      1: { id: 1, title: "Hello", authorId: 10, commentIds: [100] }
    },
    comments: {
      100: { id: 100, text: "Great!", authorId: 11, postId: 1 }
    }
  },
  ui: {
    postsList: { ids: [1], loading: false, error: null }
  }
}

Benefits:
- Single source of truth per entity
- O(1) lookups by ID
- Easy partial updates
- No stale duplicates
```

### React Query / TanStack Query Architecture

```
┌───────────────────────────────────────────────────┐
│              TanStack Query Flow                   │
│                                                   │
│  Component                                        │
│    │                                              │
│    ├── useQuery({ queryKey, queryFn })             │
│    │     │                                        │
│    │     ▼                                        │
│    │  Query Cache ── hit? ──► return cached data   │
│    │     │                                        │
│    │     miss / stale                              │
│    │     │                                        │
│    │     ▼                                        │
│    │  queryFn() ── fetch from server              │
│    │     │                                        │
│    │     ▼                                        │
│    │  Cache updated                               │
│    │     │                                        │
│    │     ▼                                        │
│    │  All subscribers re-render                   │
│    │                                              │
│    └── useMutation({ mutationFn, onSuccess })     │
│          │                                        │
│          ▼                                        │
│       Optimistic update → Server call             │
│          │                                        │
│          ├── Success → invalidate queries          │
│          └── Failure → rollback optimistic update  │
└───────────────────────────────────────────────────┘
```

```javascript
// Optimistic update pattern
const queryClient = useQueryClient();

const likeMutation = useMutation({
  mutationFn: (postId) => api.likePost(postId),

  onMutate: async (postId) => {
    await queryClient.cancelQueries({ queryKey: ['posts', postId] });
    const previous = queryClient.getQueryData(['posts', postId]);

    queryClient.setQueryData(['posts', postId], (old) => ({
      ...old,
      likes: old.likes + 1,
      isLiked: true,
    }));

    return { previous };
  },

  onError: (err, postId, context) => {
    queryClient.setQueryData(['posts', postId], context.previous);
  },

  onSettled: (data, error, postId) => {
    queryClient.invalidateQueries({ queryKey: ['posts', postId] });
  },
});
```

---

## 6. Data Fetching & API Layer

### REST vs GraphQL vs tRPC

```
┌─────────────┬──────────────────┬──────────────────┬──────────────────┐
│             │ REST             │ GraphQL          │ tRPC             │
├─────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Over-fetch  │ Common           │ Solved           │ Solved           │
│ Under-fetch │ N+1 round trips  │ Single query     │ Batched calls    │
│ Type safety │ Manual (OpenAPI) │ Schema + codegen │ End-to-end auto  │
│ Caching     │ HTTP cache       │ Normalized cache │ TanStack Query   │
│ File upload │ Native           │ Needs multipart  │ Needs adapter    │
│ Learning    │ Low              │ Medium           │ Low (TS only)    │
│ Tooling     │ Mature           │ Good             │ Growing          │
│ Best for    │ Public APIs      │ Complex UIs,     │ Full-stack TS    │
│             │                  │ mobile + web     │ monorepos        │
└─────────────┴──────────────────┴──────────────────┴──────────────────┘
```

### API Client Architecture

```
┌─────────────────────────────────────────────────────┐
│                 API Layer Design                     │
│                                                     │
│  Component Layer                                    │
│       │                                             │
│       ▼                                             │
│  React Query Hooks (useGetUser, useCreatePost)      │
│       │                                             │
│       ▼                                             │
│  API Client (axios / fetch wrapper)                 │
│       │                                             │
│       ├── Request interceptors                      │
│       │     ├── Attach auth token                   │
│       │     ├── Add correlation ID                  │
│       │     └── Request deduplication               │
│       │                                             │
│       ├── Response interceptors                     │
│       │     ├── Transform response shape            │
│       │     ├── Handle 401 → refresh token          │
│       │     ├── Retry logic (exponential backoff)   │
│       │     └── Error normalization                 │
│       │                                             │
│       └── Base config                               │
│             ├── baseURL per environment             │
│             ├── timeout                             │
│             └── headers                             │
└─────────────────────────────────────────────────────┘
```

```javascript
class ApiClient {
  constructor(config) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: 10000,
    });

    this.client.interceptors.request.use((req) => {
      const token = authStore.getToken();
      if (token) req.headers.Authorization = `Bearer ${token}`;
      req.headers['X-Request-ID'] = crypto.randomUUID();
      return req;
    });

    this.client.interceptors.response.use(
      (res) => res.data,
      async (error) => {
        if (error.response?.status === 401) {
          const newToken = await this.refreshToken();
          error.config.headers.Authorization = `Bearer ${newToken}`;
          return this.client(error.config);
        }
        throw this.normalizeError(error);
      }
    );
  }

  normalizeError(error) {
    return {
      message: error.response?.data?.message || 'Something went wrong',
      status: error.response?.status || 500,
      code: error.response?.data?.code || 'UNKNOWN',
      requestId: error.config?.headers['X-Request-ID'],
    };
  }
}
```

### Pagination Strategies

```
┌─────────────────────────────────────────────────────────────┐
│                   Pagination Patterns                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Offset-Based                                            │
│     GET /posts?offset=20&limit=10                           │
│     ✅ Simple, supports "jump to page 5"                    │
│     ❌ Inconsistent with real-time inserts/deletes          │
│     ❌ Slow for large offsets (DB scans)                    │
│                                                             │
│  2. Cursor-Based (Keyset)                                   │
│     GET /posts?cursor=abc123&limit=10                       │
│     ✅ Consistent pagination (no skips/duplicates)          │
│     ✅ Performant at any depth                              │
│     ❌ No "jump to page N" (forward/backward only)          │
│     Best for: Feeds, infinite scroll                        │
│                                                             │
│  3. Page-Based                                              │
│     GET /posts?page=3&per_page=10                           │
│     ✅ Simple mental model                                  │
│     ❌ Same consistency issues as offset                    │
│     Best for: Admin panels, search results                  │
│                                                             │
│  4. Relay-style (GraphQL)                                   │
│     { edges { node, cursor }, pageInfo { hasNextPage } }    │
│     ✅ Standardized, cursor-based                           │
│     ✅ Rich metadata                                        │
│     Best for: GraphQL APIs                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```javascript
// Infinite scroll with TanStack Query
function useFeed() {
  return useInfiniteQuery({
    queryKey: ['feed'],
    queryFn: ({ pageParam }) => api.getFeed({ cursor: pageParam }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) =>
      lastPage.hasMore ? lastPage.nextCursor : undefined,
  });
}

function Feed() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useFeed();
  const observerRef = useRef();
  const lastPostRef = useCallback(
    (node) => {
      if (isFetchingNextPage) return;
      if (observerRef.current) observerRef.current.disconnect();
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage) fetchNextPage();
      });
      if (node) observerRef.current.observe(node);
    },
    [isFetchingNextPage, hasNextPage, fetchNextPage]
  );

  const posts = data?.pages.flatMap((page) => page.posts) ?? [];

  return (
    <div>
      {posts.map((post, i) => (
        <PostCard
          key={post.id}
          post={post}
          ref={i === posts.length - 1 ? lastPostRef : null}
        />
      ))}
      {isFetchingNextPage && <Spinner />}
    </div>
  );
}
```

---

## 7. Real-Time Systems

### Transport Comparison

```
┌──────────────┬──────────────────┬───────────────┬──────────────────┐
│              │ Polling          │ SSE           │ WebSocket        │
├──────────────┼──────────────────┼───────────────┼──────────────────┤
│ Direction    │ Client → Server  │ Server → Cl.  │ Bidirectional    │
│ Connection   │ New per request  │ Persistent    │ Persistent       │
│ Protocol     │ HTTP             │ HTTP          │ WS (TCP)         │
│ Overhead     │ High             │ Low           │ Lowest           │
│ Multiplexing │ Yes (HTTP/2)     │ Limited       │ Manual           │
│ Reconnection │ Automatic        │ Built-in      │ Manual           │
│ Binary data  │ Yes              │ No (text)     │ Yes              │
│ Proxy/LB     │ Easy             │ Easy          │ Needs config     │
│ Best for     │ Dashboards,      │ Notifications │ Chat, gaming,    │
│              │ simple refresh   │ live feeds    │ collaboration    │
└──────────────┴──────────────────┴───────────────┴──────────────────┘
```

### WebSocket Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              WebSocket Connection Manager                      │
│                                                                │
│  ┌─────────────────────────────────────────────────┐           │
│  │  Connection State Machine                        │           │
│  │                                                 │           │
│  │  DISCONNECTED ──► CONNECTING ──► CONNECTED       │           │
│  │       ▲                             │            │           │
│  │       │                             ▼            │           │
│  │       ◄──────── RECONNECTING ◄── DISCONNECTED    │           │
│  │                                                 │           │
│  │  Reconnection: Exponential backoff              │           │
│  │    1s → 2s → 4s → 8s → 16s → 30s (max)         │           │
│  │    + random jitter (0-1s)                       │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                │
│  Features:                                                     │
│  ├── Heartbeat / ping-pong (detect dead connections)           │
│  ├── Message queue (buffer while disconnected)                 │
│  ├── Subscription management (rooms/channels)                  │
│  ├── Message acknowledgment (at-least-once delivery)           │
│  └── Connection sharing across tabs (SharedWorker / BC API)    │
└────────────────────────────────────────────────────────────────┘
```

```javascript
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    this.messageQueue = [];
    this.reconnectAttempt = 0;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.flushQueue();
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const { type, payload } = JSON.parse(event.data);
      this.listeners.get(type)?.forEach((cb) => cb(payload));
    };

    this.ws.onclose = (event) => {
      this.stopHeartbeat();
      if (!event.wasClean) this.reconnect();
    };
  }

  reconnect() {
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempt) + Math.random() * 1000,
      this.maxReconnectDelay
    );
    this.reconnectAttempt++;
    setTimeout(() => this.connect(), delay);
  }

  send(type, payload) {
    const message = JSON.stringify({ type, payload });
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      this.messageQueue.push(message);
    }
  }

  flushQueue() {
    while (this.messageQueue.length > 0) {
      this.ws.send(this.messageQueue.shift());
    }
  }

  subscribe(type, callback) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(callback);
    return () => this.listeners.get(type).delete(callback);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  stopHeartbeat() {
    clearInterval(this.heartbeatInterval);
  }
}
```

### Server-Sent Events (SSE)

```javascript
function useSSE(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('connecting');

  useEffect(() => {
    const eventSource = new EventSource(url);

    eventSource.onopen = () => setStatus('connected');

    eventSource.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    eventSource.addEventListener('notification', (event) => {
      const notification = JSON.parse(event.data);
      showToast(notification);
    });

    eventSource.onerror = () => {
      setStatus('reconnecting'); // browser auto-reconnects
      setError('Connection lost');
    };

    return () => eventSource.close();
  }, [url]);

  return { data, error, status };
}
```

---

## 8. Performance Optimization

### Performance Budget

```
┌──────────────────────────────────────────────────────────────┐
│                    Performance Budget                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Bundle Size Budgets:                                        │
│  ├── Initial JS: < 170 KB (compressed)                       │
│  ├── Initial CSS: < 50 KB (compressed)                       │
│  ├── Total page weight: < 500 KB                             │
│  └── Third-party JS: < 100 KB                               │
│                                                              │
│  Timing Budgets:                                             │
│  ├── Time to First Byte (TTFB): < 600ms                     │
│  ├── First Contentful Paint (FCP): < 1.8s                    │
│  ├── Largest Contentful Paint (LCP): < 2.5s                  │
│  ├── First Input Delay (FID): < 100ms                        │
│  ├── Interaction to Next Paint (INP): < 200ms                │
│  ├── Cumulative Layout Shift (CLS): < 0.1                    │
│  └── Time to Interactive (TTI): < 3.8s                       │
│                                                              │
│  Request Budgets:                                            │
│  ├── HTTP requests (initial): < 30                           │
│  ├── Image requests: < 15                                    │
│  └── Third-party requests: < 10                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Code Splitting Strategies

```
┌──────────────────────────────────────────────────────────────┐
│                  Code Splitting Levels                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Route-based splitting (most impactful)                   │
│     const Dashboard = lazy(() => import('./pages/Dashboard'))│
│     - Each route is its own chunk                            │
│     - User only downloads code for current page              │
│                                                              │
│  2. Component-based splitting                                │
│     const HeavyChart = lazy(() => import('./HeavyChart'))    │
│     - Split out large, below-fold components                 │
│     - Modals, dialogs, date pickers                          │
│                                                              │
│  3. Library splitting                                        │
│     const { format } = await import('date-fns/format')       │
│     - Load heavy libs only when needed                       │
│     - Moment.js, D3, Highlight.js                            │
│                                                              │
│  4. Conditional feature splitting                            │
│     if (user.isAdmin) {                                      │
│       const Admin = await import('./AdminPanel');             │
│     }                                                        │
│                                                              │
│  5. Interaction-based splitting                              │
│     onMouseEnter → prefetch component chunk                  │
│     onClick → load and render                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Rendering Optimization (React-specific)

```
┌──────────────────────────────────────────────────────────────┐
│               Why Components Re-render                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. State changes (setState / useState setter)               │
│  2. Parent re-renders (props reference changes)              │
│  3. Context value changes                                    │
│  4. Custom hook state changes                                │
│                                                              │
│  Re-render does NOT mean DOM update.                         │
│  React reconciles (diffs) virtual DOM first.                 │
│  Unnecessary re-renders waste CPU on diffing.                │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Optimization Techniques:

1. React.memo — skip re-render if props unchanged
   const Item = React.memo(({ title, onClick }) => { ... })

2. useMemo — memoize expensive computations
   const sorted = useMemo(() => items.sort(compareFn), [items])

3. useCallback — stable function references
   const handleClick = useCallback(() => { ... }, [dependency])

4. Key prop — help React identify items in lists
   {items.map(item => <Item key={item.id} />)}
   ❌ key={index} — causes full re-mount on reorder

5. State colocation — move state DOWN to where it's used
   ❌ Global state for a single form field
   ✅ Local state in the component that uses it

6. Children as props — parent re-render doesn't affect children
   function Layout({ children }) { ... }  // children are already created

7. Lazy initial state
   ❌ useState(expensiveComputation())      // runs every render
   ✅ useState(() => expensiveComputation()) // runs once

8. Context splitting — separate read and write contexts
   <ReadContext.Provider value={state}>
     <WriteContext.Provider value={dispatch}>
```

### Debounce, Throttle, and requestAnimationFrame

```
Debounce: Wait until user STOPS doing something
  Use for: search input, window resize, form validation
  "Wait 300ms after the user stops typing, then search"

Throttle: Execute at most once per interval
  Use for: scroll handler, mousemove, window resize
  "Execute at most once every 100ms"

requestAnimationFrame: Sync with browser paint
  Use for: animations, scroll-linked effects, visual updates
  "Run this right before the next frame is painted"
```

```javascript
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function throttle(fn, limit) {
  let lastCall = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      fn(...args);
    }
  };
}

// AbortController for cancellable search
function useSearch() {
  const [results, setResults] = useState([]);
  const controllerRef = useRef(null);

  const search = useMemo(
    () =>
      debounce(async (query) => {
        controllerRef.current?.abort();
        controllerRef.current = new AbortController();

        try {
          const data = await api.search(query, {
            signal: controllerRef.current.signal,
          });
          setResults(data);
        } catch (e) {
          if (e.name !== 'AbortError') throw e;
        }
      }, 300),
    []
  );

  return { results, search };
}
```

### Web Workers for CPU-Intensive Tasks

```javascript
// worker.js
self.onmessage = function (e) {
  const { type, payload } = e.data;

  switch (type) {
    case 'SORT_LARGE_DATASET': {
      const sorted = payload.sort((a, b) => a.value - b.value);
      self.postMessage({ type: 'SORT_COMPLETE', payload: sorted });
      break;
    }
    case 'PARSE_CSV': {
      const rows = parseCSV(payload);
      self.postMessage({ type: 'PARSE_COMPLETE', payload: rows });
      break;
    }
  }
};

// main thread hook
function useWorker(workerScript) {
  const workerRef = useRef(null);

  useEffect(() => {
    workerRef.current = new Worker(workerScript);
    return () => workerRef.current.terminate();
  }, [workerScript]);

  const postMessage = useCallback((message) => {
    return new Promise((resolve) => {
      workerRef.current.onmessage = (e) => resolve(e.data);
      workerRef.current.postMessage(message);
    });
  }, []);

  return { postMessage };
}
```

---

## 9. Virtualization & Large Data Rendering

### When You Need Virtualization

```
Rule of thumb:
  > 100 items in a scrollable list → consider virtualization
  > 1000 items → definitely virtualize
  > 10000 items → virtualize + paginate server-side
```

### How Virtualization Works

```
┌─────────────────────────────────────────────────┐
│         Viewport (visible area)                  │
│                                                 │
│  ┌──── overscan (buffer above) ────┐            │
│  │  Item 45                        │            │
│  │  Item 46                        │            │
│  ├──── visible window ─────────────┤            │
│  │  Item 47  ◄ first visible       │  rendered  │
│  │  Item 48                        │  in DOM    │
│  │  Item 49                        │            │
│  │  Item 50                        │            │
│  │  Item 51                        │            │
│  │  Item 52  ◄ last visible        │            │
│  ├──────────────────────────────────┤            │
│  │  Item 53                        │            │
│  │  Item 54                        │            │
│  └──── overscan (buffer below) ────┘            │
│                                                 │
│  Items 1-44: NOT rendered (spacer div)          │
│  Items 55-10000: NOT rendered (spacer div)      │
│                                                 │
│  Total DOM nodes: ~12 (instead of 10000)        │
└─────────────────────────────────────────────────┘
```

```javascript
// Simplified virtual list logic
function VirtualList({ items, itemHeight, containerHeight, overscan = 5 }) {
  const [scrollTop, setScrollTop] = useState(0);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, i) => (
            <div key={startIndex + i} style={{ height: itemHeight }}>
              {item.content}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Variable-Height Virtualization

```
Challenge: Items have different heights, unknown until rendered.

Approach:
1. Estimate heights initially (e.g., average or min height)
2. Measure actual height after rendering (ResizeObserver)
3. Cache measured heights in a map: { [index]: measuredHeight }
4. Recalculate offsets using prefix sum of heights
5. Use binary search to find startIndex from scrollTop

Libraries: @tanstack/react-virtual, react-window, react-virtuoso
```

---

## 10. Caching Strategies

### Multi-Layer Caching Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Caching Layers                             │
│                                                              │
│  ┌─────────────────────────────────────────────┐             │
│  │ L1: In-Memory (JS heap)                     │ ~0ms        │
│  │   React state, TanStack Query cache,        │             │
│  │   module-level variables                    │             │
│  └──────────────────┬──────────────────────────┘             │
│                     │ miss                                    │
│  ┌──────────────────▼──────────────────────────┐             │
│  │ L2: Browser Storage                         │ ~1-5ms      │
│  │   localStorage, sessionStorage, IndexedDB   │             │
│  └──────────────────┬──────────────────────────┘             │
│                     │ miss                                    │
│  ┌──────────────────▼──────────────────────────┐             │
│  │ L3: HTTP Cache                              │ ~0ms*       │
│  │   Cache-Control, ETag, Service Worker cache │             │
│  └──────────────────┬──────────────────────────┘             │
│                     │ miss                                    │
│  ┌──────────────────▼──────────────────────────┐             │
│  │ L4: CDN Edge Cache                          │ ~10-50ms    │
│  │   CloudFront, Fastly, Cloudflare            │             │
│  └──────────────────┬──────────────────────────┘             │
│                     │ miss                                    │
│  ┌──────────────────▼──────────────────────────┐             │
│  │ L5: Origin Server                           │ ~50-500ms   │
│  │   Application server + database             │             │
│  └─────────────────────────────────────────────┘             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### HTTP Caching Headers

```
┌─────────────────────────────────────────────────────────────────┐
│ Cache-Control Directives                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Static assets (JS, CSS, images with hash in filename):          │
│   Cache-Control: public, max-age=31536000, immutable            │
│   (cache forever — filename changes on content change)          │
│                                                                 │
│ HTML pages:                                                     │
│   Cache-Control: no-cache                                       │
│   (always revalidate with server, but can use cached if 304)    │
│                                                                 │
│ API responses:                                                  │
│   Cache-Control: private, max-age=60                            │
│   (cache for 60s, only in browser not CDN)                      │
│                                                                 │
│ Sensitive data:                                                 │
│   Cache-Control: no-store                                       │
│   (never cache anywhere)                                        │
│                                                                 │
│ Stale-while-revalidate:                                         │
│   Cache-Control: max-age=60, stale-while-revalidate=300         │
│   (serve stale for 5min while revalidating in background)       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ETag Flow:                                                      │
│                                                                 │
│   1. Server: ETag: "abc123"                                     │
│   2. Client: If-None-Match: "abc123"                            │
│   3. Server: 304 Not Modified (no body, save bandwidth)         │
│      OR: 200 + new body + new ETag                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Stale-While-Revalidate Pattern (Client-Side)

```javascript
// This is exactly what TanStack Query / SWR do
async function staleWhileRevalidate(key, fetchFn, { staleTime, cacheTime }) {
  const cached = cache.get(key);

  if (cached && Date.now() - cached.timestamp < staleTime) {
    return cached.data; // fresh — return immediately
  }

  if (cached) {
    // stale — return cached, refetch in background
    fetchFn().then((data) => {
      cache.set(key, { data, timestamp: Date.now() });
      notifySubscribers(key, data);
    });
    return cached.data;
  }

  // no cache — fetch and wait
  const data = await fetchFn();
  cache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

---

## 11. Offline-First & PWA Architecture

### Service Worker Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│            Service Worker Lifecycle                       │
│                                                         │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────┐  │
│  │Installing │───►│ Installed │───►│   Activating     │  │
│  │           │    │ (Waiting) │    │                  │  │
│  └──────────┘    └───────────┘    └──────────────────┘  │
│                                          │               │
│                                          ▼               │
│                                   ┌──────────────┐      │
│                                   │   Activated  │      │
│                                   │  (Controls   │      │
│                                   │   pages)     │      │
│                                   └──────────────┘      │
│                                          │               │
│                                          ▼               │
│                                   ┌──────────────┐      │
│                                   │  Redundant   │      │
│                                   │  (Replaced)  │      │
│                                   └──────────────┘      │
│                                                         │
│  Key Events:                                            │
│  install  → pre-cache critical assets                   │
│  activate → clean up old caches                         │
│  fetch    → intercept network requests                  │
│  push     → receive push notifications                  │
│  sync     → background sync when online                 │
└─────────────────────────────────────────────────────────┘
```

### Caching Strategies for Service Workers

```
┌────────────────────┬─────────────────────────────────────────┐
│ Strategy           │ Description                              │
├────────────────────┼─────────────────────────────────────────┤
│ Cache First        │ Check cache → if miss, fetch network     │
│                    │ Best for: static assets, fonts, images   │
│                    │                                         │
│ Network First      │ Try network → if fail, fallback to cache │
│                    │ Best for: API data, frequently updated   │
│                    │                                         │
│ Stale While        │ Serve cache immediately + fetch update   │
│ Revalidate         │ Best for: content that can be slightly   │
│                    │ stale (avatars, articles)                │
│                    │                                         │
│ Network Only       │ Always fetch from network                │
│                    │ Best for: analytics, non-GET requests    │
│                    │                                         │
│ Cache Only         │ Only serve from cache                    │
│                    │ Best for: pre-cached critical assets     │
└────────────────────┴─────────────────────────────────────────┘
```

### Offline Data Sync Pattern

```
┌──────────────────────────────────────────────────────────────┐
│                  Offline Queue Architecture                   │
│                                                              │
│  User Action → Is Online?                                    │
│                 │                                            │
│          ┌──── YES ────┐                                     │
│          │             │                                     │
│          ▼             ▼                                     │
│     Send to API   Queue in IndexedDB                         │
│          │         (with timestamp, retryCount)               │
│          │             │                                     │
│          ▼             ▼                                     │
│     Update UI     Update UI optimistically                   │
│                        │                                     │
│                   Online event fires                         │
│                        │                                     │
│                        ▼                                     │
│                   Process queue (FIFO)                        │
│                        │                                     │
│                   ┌────┴────┐                                │
│                   │         │                                │
│                 Success   Failure                            │
│                   │         │                                │
│                   ▼         ▼                                │
│              Remove from  Retry with backoff                 │
│              queue        (max 3 attempts)                   │
│                              │                               │
│                           Still failing?                     │
│                              │                               │
│                              ▼                               │
│                         Notify user                          │
│                         + keep in queue                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. Security

### Frontend Security Threat Model

```
┌──────────────────────────────────────────────────────────────┐
│                Frontend Security Threats                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  XSS (Cross-Site Scripting)                                  │
│  ├── Stored: malicious script saved in DB, served to users   │
│  ├── Reflected: script in URL, reflected in response         │
│  ├── DOM-based: script manipulates DOM directly              │
│  ├── Prevention:                                             │
│  │   ├── Escape all user input before rendering              │
│  │   ├── Use textContent, not innerHTML                      │
│  │   ├── CSP headers (Content-Security-Policy)               │
│  │   ├── React auto-escapes JSX (but not dangerouslySet...)  │
│  │   └── Sanitize HTML with DOMPurify if needed              │
│  │                                                           │
│  CSRF (Cross-Site Request Forgery)                           │
│  ├── Attacker tricks user into making unwanted request        │
│  ├── Prevention:                                             │
│  │   ├── CSRF tokens in forms/headers                        │
│  │   ├── SameSite cookie attribute                           │
│  │   ├── Check Origin/Referer headers                        │
│  │   └── Use non-cookie auth (Bearer token in header)        │
│  │                                                           │
│  Clickjacking                                                │
│  ├── Page loaded in invisible iframe, user clicks attacker   │
│  ├── Prevention:                                             │
│  │   ├── X-Frame-Options: DENY                               │
│  │   └── CSP frame-ancestors 'none'                          │
│  │                                                           │
│  Supply Chain Attacks                                        │
│  ├── Compromised npm package                                 │
│  ├── Prevention:                                             │
│  │   ├── Lock file (package-lock.json)                       │
│  │   ├── npm audit, Snyk, Socket                             │
│  │   ├── Subresource Integrity (SRI) for CDN scripts         │
│  │   └── Minimize dependencies                               │
│  │                                                           │
│  Sensitive Data Exposure                                     │
│  ├── API keys in client bundle                               │
│  ├── PII in localStorage                                     │
│  ├── Prevention:                                             │
│  │   ├── Environment variables (server-side only)            │
│  │   ├── Never store tokens in localStorage (use httpOnly)   │
│  │   └── Encrypt sensitive client-side data                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Content Security Policy (CSP)

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-abc123';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https://cdn.example.com;
  connect-src 'self' https://api.example.com;
  font-src 'self' https://fonts.googleapis.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  upgrade-insecure-requests;

Directives cheat sheet:
  default-src  → fallback for all resource types
  script-src   → JavaScript sources
  style-src    → CSS sources
  img-src      → image sources
  connect-src  → fetch, XHR, WebSocket targets
  frame-src    → iframe sources
  'nonce-xxx'  → allow specific inline scripts with matching nonce
  'strict-dynamic' → trust scripts loaded by already trusted scripts
```

---

## 13. Accessibility (a11y)

### WCAG Principles (POUR)

```
P — Perceivable
  Users must be able to perceive the information
  ├── Text alternatives for images (alt text)
  ├── Captions for video/audio
  ├── Sufficient color contrast (4.5:1 for text)
  └── Content adaptable to different presentations

O — Operable
  Users must be able to operate the interface
  ├── All functionality via keyboard
  ├── Enough time to read/interact
  ├── No content that causes seizures
  └── Clear navigation and wayfinding

U — Understandable
  Users must be able to understand the information
  ├── Readable text
  ├── Predictable behavior
  └── Input assistance (error messages, labels)

R — Robust
  Content must be robust enough for diverse user agents
  ├── Valid HTML
  ├── Compatible with assistive technology
  └── Proper ARIA usage
```

### ARIA Roles & Patterns

```
┌────────────────────┬─────────────────────────────────────────┐
│ Widget             │ Key ARIA Attributes                      │
├────────────────────┼─────────────────────────────────────────┤
│ Modal Dialog       │ role="dialog"                            │
│                    │ aria-modal="true"                        │
│                    │ aria-labelledby="title-id"               │
│                    │ Focus trap (Tab cycles inside)           │
│                    │ Escape closes                            │
│                    │ Return focus on close                    │
├────────────────────┼─────────────────────────────────────────┤
│ Dropdown Menu      │ role="menu" on container                 │
│                    │ role="menuitem" on items                 │
│                    │ aria-expanded on trigger                 │
│                    │ Arrow keys navigate                     │
│                    │ Enter/Space selects                     │
├────────────────────┼─────────────────────────────────────────┤
│ Tabs               │ role="tablist" on container              │
│                    │ role="tab" on tabs                       │
│                    │ role="tabpanel" on panels                │
│                    │ aria-selected on active tab              │
│                    │ Arrow keys switch tabs                   │
├────────────────────┼─────────────────────────────────────────┤
│ Combobox           │ role="combobox" on input                 │
│ (Autocomplete)     │ role="listbox" on dropdown               │
│                    │ role="option" on items                   │
│                    │ aria-activedescendant for highlight      │
│                    │ aria-expanded, aria-autocomplete         │
├────────────────────┼─────────────────────────────────────────┤
│ Toast/Alert        │ role="alert" or role="status"            │
│                    │ aria-live="polite" or "assertive"        │
│                    │ aria-atomic="true"                       │
├────────────────────┼─────────────────────────────────────────┤
│ Toggle             │ role="switch"                            │
│                    │ aria-checked="true/false"                │
└────────────────────┴─────────────────────────────────────────┘
```

### Focus Management

```javascript
// Focus trap for modals
function useFocusTrap(ref) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const focusable = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const previouslyFocused = document.activeElement;
    first?.focus();

    function handleKeyDown(e) {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    element.addEventListener('keydown', handleKeyDown);

    return () => {
      element.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus(); // restore focus on unmount
    };
  }, [ref]);
}
```

---

## 14. Internationalization (i18n)

### i18n Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     i18n Architecture                         │
│                                                              │
│  Translation Files (JSON per locale)                         │
│  ├── en.json: { "greeting": "Hello, {name}!" }              │
│  ├── es.json: { "greeting": "¡Hola, {name}!" }              │
│  └── ar.json: { "greeting": "!{name} ،مرحبا" }              │
│                                                              │
│  Loading Strategy:                                           │
│  ├── Bundle all locales → simple but large                   │
│  ├── Lazy load per locale → code-split, smaller bundles      │
│  └── Namespace splitting → load translations per page/feature│
│                                                              │
│  Beyond Text:                                                │
│  ├── Date/time formatting (Intl.DateTimeFormat)              │
│  ├── Number formatting (Intl.NumberFormat)                    │
│  ├── Currency formatting                                     │
│  ├── Pluralization rules (1 item vs 2 items)                 │
│  ├── RTL layout support (dir="rtl", CSS logical properties)  │
│  ├── Cultural differences (color, icons, imagery)            │
│  └── Input methods (CJK, Arabic, Hebrew)                     │
│                                                              │
│  CSS Logical Properties (for RTL):                           │
│  ├── margin-inline-start (not margin-left)                   │
│  ├── padding-inline-end (not padding-right)                  │
│  ├── inset-inline-start (not left)                           │
│  └── border-block-end (not border-bottom)                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 15. Testing Architecture

### Testing Trophy (Kent C. Dodds Model)

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E ╲         Few, expensive, high confidence
                 ╱────────╲
                ╱          ╲
               ╱ Integration ╲    Most tests here, best ROI
              ╱────────────────╲
             ╱                  ╲
            ╱       Unit         ╲  Many, fast, focused
           ╱──────────────────────╲
          ╱                        ╲
         ╱     Static Analysis      ╲  TypeScript, ESLint
        ╱────────────────────────────╲
```

### What To Test at Each Level

```
Static Analysis (TypeScript + ESLint):
  - Type errors, unused variables, import issues
  - Enforced code patterns
  - Zero runtime cost

Unit Tests (Vitest / Jest):
  - Pure functions, utilities, helpers
  - Custom hooks (renderHook)
  - Reducers, selectors
  - Data transformations
  - NOT: components in isolation (low value)

Integration Tests (Testing Library):
  - User flows within a page/feature
  - Component interactions
  - Form submission, validation
  - API mocking (MSW)
  - "Does clicking 'Add to Cart' update the cart count?"

E2E Tests (Playwright / Cypress):
  - Critical user journeys (signup → checkout)
  - Cross-browser testing
  - Visual regression
  - Performance testing
```

### Testing Patterns

```javascript
// MSW (Mock Service Worker) for API mocking
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const handlers = [
  http.get('/api/user/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Test User',
      email: 'test@example.com',
    });
  }),

  http.post('/api/posts', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 1, ...body }, { status: 201 });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Integration test with Testing Library
test('user can search and see results', async () => {
  render(<SearchPage />);

  const input = screen.getByRole('searchbox');
  await userEvent.type(input, 'react');

  await waitFor(() => {
    expect(screen.getByText('React Documentation')).toBeInTheDocument();
  });

  await userEvent.click(screen.getByText('React Documentation'));
  expect(screen.getByRole('heading', { name: /react/i })).toBeInTheDocument();
});
```

---

## 16. Build Systems & Module Federation

### Module Systems

```
CommonJS (CJS):
  const x = require('module')    // synchronous
  module.exports = { x }
  - Node.js default
  - Cannot tree-shake (dynamic require possible)

ES Modules (ESM):
  import { x } from 'module'     // static, async
  export const x = ...
  - Browser native (type="module")
  - Tree-shakeable (static analysis)
  - Top-level await

UMD (Universal Module Definition):
  - Works in CJS, AMD, and browser globals
  - Used for libraries distributed via CDN
```

### Tree Shaking Deep Dive

```
Tree shaking = dead code elimination for ES modules

Requirements:
  1. ES module syntax (import/export)
  2. Side-effect-free modules
  3. Production mode bundling

What breaks tree shaking:
  ❌ import * as utils from './utils'  (imports everything)
  ❌ Side effects at module level (global mutations)
  ❌ CommonJS require() (dynamic, not analyzable)
  ❌ Re-exports without explicit names

package.json "sideEffects" field:
  "sideEffects": false              // all modules are pure
  "sideEffects": ["*.css", "*.scss"] // only CSS has side effects

Barrel file anti-pattern:
  ❌ index.ts that re-exports 50 components
     import { Button } from './components'
     → May pull in ALL 50 components

  ✅ Direct imports
     import { Button } from './components/Button'
```

### Module Federation (Micro-Frontend Sharing)

```
┌──────────────────────────────────────────────────────────────┐
│              Module Federation Architecture                   │
│                                                              │
│  Host App (Shell)                                            │
│  ├── Loads shared dependencies (React, router)               │
│  ├── Defines layout and navigation                           │
│  └── Dynamically imports remote modules                      │
│                                                              │
│  Remote App A (Team Checkout)                                │
│  ├── Exposes: CheckoutWidget, CartSummary                    │
│  ├── Shares: react, react-dom (singleton)                    │
│  └── Deployed independently                                  │
│                                                              │
│  Remote App B (Team Product)                                 │
│  ├── Exposes: ProductCard, ProductSearch                     │
│  ├── Shares: react, react-dom (singleton)                    │
│  └── Deployed independently                                  │
│                                                              │
│  Runtime Flow:                                               │
│  1. Host loads → fetches remoteEntry.js from each remote     │
│  2. remoteEntry.js has module map                            │
│  3. Host requests specific module → remote serves it         │
│  4. Shared deps resolved at runtime (version negotiation)    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 17. Micro-Frontends

### Integration Approaches

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Approach          │ Description                                  │
├──────────────────┼──────────────────────────────────────────────┤
│ Build-time       │ npm packages, compiled together               │
│                  │ ✅ Simple, type-safe                          │
│                  │ ❌ Coupled releases, all-or-nothing deploy    │
├──────────────────┼──────────────────────────────────────────────┤
│ Server-side      │ Server composes HTML from multiple services   │
│ (SSI, ESI)       │ ✅ Works without JS, SEO-friendly            │
│                  │ ❌ Limited interactivity                      │
├──────────────────┼──────────────────────────────────────────────┤
│ Runtime (iframe) │ Each MFE in an iframe                        │
│                  │ ✅ Complete isolation                         │
│                  │ ❌ Poor UX, no shared state, perf overhead    │
├──────────────────┼──────────────────────────────────────────────┤
│ Runtime (JS)     │ Module Federation, Single-SPA, importmaps    │
│                  │ ✅ Independent deploy, shared deps            │
│                  │ ❌ Complex setup, version conflicts           │
├──────────────────┼──────────────────────────────────────────────┤
│ Web Components   │ Custom elements with Shadow DOM               │
│                  │ ✅ Framework-agnostic, native isolation       │
│                  │ ❌ SSR challenges, limited React integration  │
└──────────────────┴──────────────────────────────────────────────┘
```

### Communication Between Micro-Frontends

```
1. Custom Events (loosely coupled)
   window.dispatchEvent(new CustomEvent('cart:updated', { detail: { count: 5 } }))
   window.addEventListener('cart:updated', handler)

2. Shared State (e.g., shared Redux store, pub/sub)
   ├── Event bus / pub-sub
   ├── Shared observable store
   └── URL as shared state (query params)

3. Props / Callbacks (parent-child)
   <RemoteWidget onCheckout={handleCheckout} user={currentUser} />

4. BroadcastChannel API (cross-tab)
   const channel = new BroadcastChannel('app_events')
   channel.postMessage({ type: 'LOGOUT' })
```

---

## 18. Observability & Monitoring

### Frontend Observability Stack

```
┌──────────────────────────────────────────────────────────────┐
│               Frontend Observability Pillars                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Error Tracking                                           │
│     ├── window.onerror (global JS errors)                    │
│     ├── window.onunhandledrejection (Promise rejections)     │
│     ├── React Error Boundaries (component errors)            │
│     ├── Source maps for readable stack traces                 │
│     └── Tools: Sentry, Bugsnag, Datadog RUM                 │
│                                                              │
│  2. Performance Monitoring (RUM)                             │
│     ├── Core Web Vitals (LCP, FID/INP, CLS)                 │
│     ├── Navigation Timing API                                │
│     ├── Resource Timing API                                  │
│     ├── Long Tasks API (tasks > 50ms)                        │
│     ├── Layout Instability API (CLS)                         │
│     └── Tools: web-vitals library, Lighthouse CI             │
│                                                              │
│  3. User Session Tracking                                    │
│     ├── Session replay (heatmaps, recordings)                │
│     ├── Funnel analysis                                      │
│     ├── Feature usage tracking                               │
│     └── Tools: FullStory, LogRocket, Hotjar                  │
│                                                              │
│  4. Logging                                                  │
│     ├── Structured client-side logging                       │
│     ├── Log levels (debug, info, warn, error)                │
│     ├── Batched transport to backend                         │
│     ├── Correlation IDs (trace through frontend → backend)   │
│     └── Sampling (don't log everything in prod)              │
│                                                              │
│  5. Alerting                                                 │
│     ├── Error rate spike (> 1% of sessions)                  │
│     ├── Performance degradation (P75 LCP > 4s)              │
│     ├── API error rate increase                              │
│     └── Bundle size increase (CI check)                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Error Boundary Pattern

```jsx
class ErrorBoundary extends React.Component {
  state = { error: null, errorInfo: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    errorReporter.captureException(error, {
      componentStack: errorInfo.componentStack,
      tags: { boundary: this.props.name },
    });
  }

  render() {
    if (this.state.error) {
      return this.props.fallback?.(this.state.error, () =>
        this.setState({ error: null, errorInfo: null })
      ) ?? <DefaultErrorUI />;
    }
    return this.props.children;
  }
}

// Granular error boundaries per feature
<ErrorBoundary name="header" fallback={(err, retry) => <HeaderFallback />}>
  <Header />
</ErrorBoundary>
<ErrorBoundary name="feed" fallback={(err, retry) => <FeedError onRetry={retry} />}>
  <NewsFeed />
</ErrorBoundary>
<ErrorBoundary name="sidebar" fallback={(err, retry) => <SidebarFallback />}>
  <Sidebar />
</ErrorBoundary>
```

### Performance Measurement

```javascript
// Core Web Vitals collection
import { onLCP, onFID, onCLS, onINP, onTTFB } from 'web-vitals';

function sendMetric(metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating, // "good" | "needs-improvement" | "poor"
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    url: location.href,
    userAgent: navigator.userAgent,
    connection: navigator.connection?.effectiveType,
    timestamp: Date.now(),
  });

  // Use sendBeacon for reliability (survives page unload)
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/metrics', body);
  } else {
    fetch('/api/metrics', { body, method: 'POST', keepalive: true });
  }
}

onLCP(sendMetric);
onFID(sendMetric);
onCLS(sendMetric);
onINP(sendMetric);
onTTFB(sendMetric);

// Custom performance marks
performance.mark('feed-render-start');
// ... render feed
performance.mark('feed-render-end');
performance.measure('feed-render', 'feed-render-start', 'feed-render-end');
```

---

## 19. Design System Architecture

### Design Token Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│                Design Token Layers                            │
│                                                              │
│  Global Tokens (raw values)                                  │
│  ├── color-blue-500: #3B82F6                                 │
│  ├── spacing-4: 16px                                         │
│  ├── font-size-lg: 18px                                      │
│  └── radius-md: 8px                                          │
│                                                              │
│           ▼  (alias/semantic mapping)                        │
│                                                              │
│  Semantic Tokens (purpose-based)                             │
│  ├── color-primary: {color-blue-500}                         │
│  ├── color-error: {color-red-500}                            │
│  ├── spacing-component-gap: {spacing-4}                      │
│  └── radius-button: {radius-md}                              │
│                                                              │
│           ▼  (component-specific)                            │
│                                                              │
│  Component Tokens                                            │
│  ├── button-bg: {color-primary}                              │
│  ├── button-radius: {radius-button}                          │
│  ├── button-padding-x: {spacing-4}                           │
│  └── input-border-color: {color-border}                      │
│                                                              │
│  Theming = swapping semantic token values                    │
│  Dark mode: color-primary: {color-blue-400}                  │
│  High contrast: color-primary: {color-blue-700}              │
└──────────────────────────────────────────────────────────────┘
```

### Component API Design Principles

```
1. Composition over configuration
   ❌ <Button icon="search" iconPosition="left" label="Search" />
   ✅ <Button><SearchIcon /> Search</Button>

2. Consistent prop naming
   ├── size: "sm" | "md" | "lg" (not "small" | "medium")
   ├── variant: "primary" | "secondary" | "ghost"
   ├── isDisabled, isLoading, isSelected (boolean prefix)
   └── onAction pattern: onClick, onChange, onClose

3. Polymorphic "as" prop
   <Button as="a" href="/home">Go Home</Button>
   <Text as="h1">Title</Text>

4. Forward refs and spread props
   const Button = forwardRef(({ children, ...props }, ref) => (
     <button ref={ref} {...props}>{children}</button>
   ))

5. Accessible by default
   Built-in ARIA attributes, keyboard handling, focus management
```

---

## 20. SEO & Core Web Vitals

### Rendering Strategies & SEO Impact

```
┌─────────────────┬────────────────────────────────────────────────┐
│ Strategy         │ Description & Trade-offs                       │
├─────────────────┼────────────────────────────────────────────────┤
│ CSR              │ Client-Side Rendering                          │
│ (Create React    │ ❌ Empty HTML → poor SEO, slow FCP             │
│  App)            │ ✅ Simple deploy (static files)                │
│                  │ Use: Internal tools, dashboards                │
├─────────────────┼────────────────────────────────────────────────┤
│ SSR              │ Server-Side Rendering                          │
│ (Next.js         │ ✅ Full HTML on first load → great SEO         │
│  getServerSide   │ ✅ Fast FCP                                    │
│  Props)          │ ❌ Server cost, TTFB depends on server speed   │
│                  │ Use: Dynamic content, personalized pages       │
├─────────────────┼────────────────────────────────────────────────┤
│ SSG              │ Static Site Generation                         │
│ (Next.js         │ ✅ Pre-built HTML → fastest TTFB               │
│  getStaticProps) │ ✅ Served from CDN                             │
│                  │ ❌ Stale until rebuild                         │
│                  │ Use: Blog, docs, marketing pages               │
├─────────────────┼────────────────────────────────────────────────┤
│ ISR              │ Incremental Static Regeneration                │
│ (Next.js         │ ✅ SSG + background revalidation               │
│  revalidate)     │ ✅ Fresh content without full rebuild           │
│                  │ Use: Product pages, news articles              │
├─────────────────┼────────────────────────────────────────────────┤
│ Streaming SSR    │ React 18 Suspense + streaming                  │
│ (React Server    │ ✅ Progressive HTML delivery                   │
│  Components)     │ ✅ Selective hydration                         │
│                  │ Use: Complex pages with mixed priorities       │
├─────────────────┼────────────────────────────────────────────────┤
│ RSC              │ React Server Components                        │
│ (Next.js App     │ ✅ Zero client-side JS for server components   │
│  Router)         │ ✅ Direct DB/API access in components          │
│                  │ ✅ Streaming + selective hydration              │
│                  │ Use: Modern Next.js apps                       │
└─────────────────┴────────────────────────────────────────────────┘
```

### Core Web Vitals Optimization

```
LCP (Largest Contentful Paint) < 2.5s
  ├── Preload hero image: <link rel="preload" as="image" href="...">
  ├── Use srcset + sizes for responsive images
  ├── Inline critical CSS, defer non-critical
  ├── Preconnect to CDN: <link rel="preconnect" href="...">
  ├── Server-side render above-the-fold content
  ├── Avoid client-side redirects
  └── Use priority hints: <img fetchpriority="high">

INP (Interaction to Next Paint) < 200ms
  ├── Break up long tasks (yield to main thread)
  ├── Use startTransition for non-urgent updates
  ├── Debounce/throttle input handlers
  ├── Move computation to Web Workers
  ├── Minimize DOM size (< 1500 nodes)
  └── Avoid layout thrashing (batch reads/writes)

CLS (Cumulative Layout Shift) < 0.1
  ├── Set explicit width/height on images and videos
  ├── Use aspect-ratio CSS property
  ├── Reserve space for ads/embeds
  ├── Avoid inserting content above existing content
  ├── Use transform for animations (not top/left/width)
  └── Preload fonts with font-display: optional
```

---

## 21. Image & Media Architecture

### Image Optimization Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│               Image Optimization Strategy                     │
│                                                              │
│  Format Selection:                                           │
│  ├── AVIF: best compression, growing support                 │
│  ├── WebP: good compression, wide support                    │
│  ├── JPEG: photos, universal support (fallback)              │
│  ├── PNG: transparency needed, lossless                      │
│  └── SVG: icons, logos, illustrations (vector)               │
│                                                              │
│  <picture> for format negotiation:                           │
│  <picture>                                                   │
│    <source srcset="img.avif" type="image/avif">              │
│    <source srcset="img.webp" type="image/webp">              │
│    <img src="img.jpg" alt="..." loading="lazy"               │
│         width="800" height="600">                            │
│  </picture>                                                  │
│                                                              │
│  Responsive images:                                          │
│  <img                                                        │
│    srcset="img-400.jpg 400w, img-800.jpg 800w, img-1200.jpg" │
│    sizes="(max-width: 600px) 100vw, 50vw"                    │
│    src="img-800.jpg"                                         │
│    alt="..."                                                 │
│    loading="lazy"                                            │
│    decoding="async"                                          │
│  >                                                           │
│                                                              │
│  Loading Strategy:                                           │
│  ├── Above fold: loading="eager", fetchpriority="high"       │
│  ├── Below fold: loading="lazy" (native)                     │
│  ├── Thumbnails: low-quality placeholder (LQIP / blur-up)    │
│  └── Critical hero: preload in <head>                        │
│                                                              │
│  CDN + Image Service:                                        │
│  https://cdn.example.com/image.jpg?w=400&h=300&format=webp   │
│  └── Resize, format convert, compress on-the-fly             │
└──────────────────────────────────────────────────────────────┘
```

### Video Streaming Architecture

```
Adaptive Bitrate Streaming (ABR):
  ├── HLS (HTTP Live Streaming) — Apple, most common
  ├── DASH (Dynamic Adaptive Streaming over HTTP) — Open standard
  │
  │  How it works:
  │  1. Video encoded at multiple qualities (360p, 720p, 1080p, 4K)
  │  2. Each quality split into small segments (2-10 seconds)
  │  3. Manifest file lists all available segments/qualities
  │  4. Player monitors bandwidth and buffer
  │  5. Player switches quality dynamically per segment
  │
  │  Buffer Strategy:
  │  ├── Forward buffer: 30-60s of video pre-loaded
  │  ├── Quality switch: wait for segment boundary
  │  └── Stall recovery: drop to lowest quality immediately

Custom Video Player Considerations:
  ├── Preload strategies: none | metadata | auto
  ├── Poster image while loading
  ├── Keyboard controls (Space, arrows, M, F)
  ├── Subtitles/captions (WebVTT format)
  ├── Fullscreen API
  ├── Picture-in-Picture API
  ├── MediaSession API (OS media controls)
  └── DRM (Encrypted Media Extensions — EME)
```

---

## 22. Authentication & Authorization Flows

### Token Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Auth Token Architecture                          │
│                                                              │
│  JWT (JSON Web Token):                                       │
│  ┌────────────┬──────────────┬──────────────────┐            │
│  │  Header    │   Payload    │   Signature      │            │
│  │  (algo)    │   (claims)   │   (verification) │            │
│  └────────────┴──────────────┴──────────────────┘            │
│                                                              │
│  Token Pair Strategy:                                        │
│  ├── Access Token                                            │
│  │   ├── Short-lived (15 min)                                │
│  │   ├── Contains user claims (id, roles)                    │
│  │   ├── Sent in Authorization header                        │
│  │   └── Stored in memory (NOT localStorage)                 │
│  │                                                           │
│  └── Refresh Token                                           │
│      ├── Long-lived (7-30 days)                              │
│      ├── Used only to get new access tokens                  │
│      ├── Stored in httpOnly, secure, SameSite cookie         │
│      ├── Rotated on each use (one-time use)                  │
│      └── Server-side revocation list                         │
│                                                              │
│  Silent Refresh Flow:                                        │
│  1. Access token expires                                     │
│  2. API returns 401                                          │
│  3. Interceptor catches 401                                  │
│  4. POST /auth/refresh (cookie sent automatically)           │
│  5. New access token received                                │
│  6. Retry original request with new token                    │
│  7. If refresh fails → redirect to login                     │
│                                                              │
│  Race Condition:                                             │
│  Multiple parallel requests all get 401.                     │
│  Solution: Queue requests, only ONE refresh call,            │
│  then replay all queued requests with new token.             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```javascript
// Token refresh with request queuing
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token) {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve(token);
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { accessToken } = await authApi.refresh();
        tokenStore.setAccessToken(accessToken);
        processQueue(null, accessToken);
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        tokenStore.clear();
        window.location.href = '/login';
        throw err;
      } finally {
        isRefreshing = false;
      }
    }
    throw error;
  }
);
```

### OAuth 2.0 + PKCE Flow

```
┌──────────────────────────────────────────────────────────────┐
│           OAuth 2.0 Authorization Code + PKCE                │
│                                                              │
│  1. Generate code_verifier (random string)                   │
│  2. Generate code_challenge = SHA256(code_verifier)          │
│  3. Redirect to authorization server:                        │
│     /authorize?                                              │
│       response_type=code&                                    │
│       client_id=XXX&                                         │
│       redirect_uri=https://app.com/callback&                 │
│       code_challenge=ABC&                                    │
│       code_challenge_method=S256&                            │
│       scope=openid profile email&                            │
│       state=random_csrf_token                                │
│                                                              │
│  4. User authenticates and consents                          │
│  5. Redirect back: /callback?code=AUTH_CODE&state=...        │
│  6. Verify state matches                                     │
│  7. Exchange code for tokens:                                │
│     POST /token                                              │
│       grant_type=authorization_code&                         │
│       code=AUTH_CODE&                                         │
│       code_verifier=ORIGINAL_VERIFIER&                       │
│       redirect_uri=https://app.com/callback                  │
│                                                              │
│  8. Receive access_token + refresh_token + id_token          │
│                                                              │
│  Why PKCE?                                                   │
│  Without PKCE, anyone who intercepts the auth code           │
│  can exchange it. PKCE proves the requestor is the           │
│  same entity that initiated the flow.                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 23. Client-Side Storage Deep Dive

### Storage Comparison

```
┌──────────────┬────────┬──────────┬────────────┬──────────────┐
│              │ Cookie │ local    │ session    │ IndexedDB    │
│              │        │ Storage  │ Storage    │              │
├──────────────┼────────┼──────────┼────────────┼──────────────┤
│ Capacity     │ ~4KB   │ ~5-10MB  │ ~5-10MB    │ 100s of MB   │
│ Persistence  │ Expiry │ Forever  │ Tab close  │ Forever      │
│ Sent to      │ Yes    │ No       │ No         │ No           │
│ server       │        │          │            │              │
│ API          │ String │ Sync     │ Sync       │ Async (IDB)  │
│ Data type    │ String │ String   │ String     │ Structured   │
│ Indexable    │ No     │ No       │ No         │ Yes          │
│ Web Workers  │ No     │ No       │ No         │ Yes          │
│ Transactions │ No     │ No       │ No         │ Yes          │
├──────────────┼────────┼──────────┼────────────┼──────────────┤
│ Use for      │ Auth   │ Prefs,   │ Temp form  │ Offline data │
│              │ tokens │ theme,   │ data, tab- │ large blobs, │
│              │ (http  │ non-     │ specific   │ file cache   │
│              │ Only)  │ sensitive│ state      │              │
└──────────────┴────────┴──────────┴────────────┴──────────────┘
```

### IndexedDB Pattern

```javascript
class ClientDB {
  constructor(dbName, version = 1) {
    this.dbName = dbName;
    this.version = version;
    this.db = null;
  }

  async open(upgradeCallback) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      request.onupgradeneeded = (event) => {
        upgradeCallback(event.target.result);
      };
      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async put(storeName, data) {
    const tx = this.db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async get(storeName, key) {
    const tx = this.db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getAll(storeName, query, count) {
    const tx = this.db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.getAll(query, count);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

// Usage
const db = new ClientDB('myApp', 1);
await db.open((database) => {
  const store = database.createObjectStore('posts', { keyPath: 'id' });
  store.createIndex('by_date', 'createdAt');
  store.createIndex('by_author', 'authorId');
});
```

---

## 24. Networking & Protocol Optimization

### HTTP/2 and HTTP/3

```
HTTP/1.1 Problems:
  ├── Head-of-line blocking (one request blocks the connection)
  ├── 6 connections per origin limit
  ├── No header compression
  └── No server push

HTTP/2 Solutions:
  ├── Multiplexing (parallel requests on single connection)
  ├── Header compression (HPACK)
  ├── Server push (proactively send resources)
  ├── Stream prioritization
  └── Binary protocol (more efficient than text)

  Frontend implications:
  ├── ❌ Stop concatenating files (bundles can be smaller)
  ├── ❌ Stop spriting images
  ├── ❌ Stop domain sharding
  ├── ✅ Use more granular chunks
  └── ✅ Still useful to minimize total request count

HTTP/3 (QUIC):
  ├── UDP-based (not TCP)
  ├── No TCP head-of-line blocking
  ├── Faster connection establishment (0-RTT)
  ├── Better on lossy networks (mobile)
  └── Connection migration (switch networks seamlessly)
```

### Resource Hints

```html
<!-- DNS lookup (cheapest) -->
<link rel="dns-prefetch" href="https://api.example.com">

<!-- DNS + TCP + TLS handshake -->
<link rel="preconnect" href="https://cdn.example.com">

<!-- Full download, high priority -->
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/hero.avif" as="image">
<link rel="preload" href="/critical.css" as="style">

<!-- Download at low priority, likely needed for next navigation -->
<link rel="prefetch" href="/dashboard.js">

<!-- Full page prerender (speculative) -->
<link rel="prerender" href="/likely-next-page">

<!-- Modern speculation rules (Chrome) -->
<script type="speculationrules">
{
  "prerender": [{
    "where": { "href_matches": "/product/*" },
    "eagerness": "moderate"
  }]
}
</script>
```

### Request Optimization Patterns

```
1. Request Deduplication
   Multiple components request the same data simultaneously.
   Solution: Cache in-flight promises, return same promise.

2. Request Batching
   Multiple small requests combined into one.
   DataLoader pattern: collect IDs for 10ms, then batch fetch.

3. Request Cancellation
   Cancel outdated requests (user types fast in search).
   AbortController → signal passed to fetch.

4. Waterfall Prevention
   ❌ Load parent → load child data → load grandchild
   ✅ Parallel fetches or server-side aggregation
   ✅ Suspense + parallel data loading

5. Prefetching
   User hovers a link → prefetch that page's data.
   IntersectionObserver → prefetch when card enters viewport.
```

```javascript
// Request deduplication
const inFlightRequests = new Map();

async function deduplicatedFetch(url, options) {
  const key = `${options?.method || 'GET'}:${url}`;

  if (inFlightRequests.has(key)) {
    return inFlightRequests.get(key);
  }

  const promise = fetch(url, options)
    .then((res) => res.json())
    .finally(() => inFlightRequests.delete(key));

  inFlightRequests.set(key, promise);
  return promise;
}

// DataLoader-style batching
class BatchLoader {
  constructor(batchFn, { maxBatchSize = 25, batchDelay = 10 } = {}) {
    this.batchFn = batchFn;
    this.maxBatchSize = maxBatchSize;
    this.batchDelay = batchDelay;
    this.queue = [];
    this.timer = null;
  }

  load(key) {
    return new Promise((resolve, reject) => {
      this.queue.push({ key, resolve, reject });

      if (this.queue.length >= this.maxBatchSize) {
        this.dispatch();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this.dispatch(), this.batchDelay);
      }
    });
  }

  async dispatch() {
    clearTimeout(this.timer);
    this.timer = null;
    const batch = this.queue.splice(0, this.maxBatchSize);
    const keys = batch.map((item) => item.key);

    try {
      const results = await this.batchFn(keys);
      batch.forEach((item, i) => item.resolve(results[i]));
    } catch (error) {
      batch.forEach((item) => item.reject(error));
    }
  }
}

// Usage
const userLoader = new BatchLoader((ids) =>
  api.getUsers({ ids }) // GET /api/users?ids=1,2,3,4,5
);

// These 3 calls made within 10ms become ONE request
const [alice, bob, charlie] = await Promise.all([
  userLoader.load(1),
  userLoader.load(2),
  userLoader.load(3),
]);
```

---

## 25. Deployment, CI/CD & Feature Flags

### Deployment Strategies

```
┌──────────────────────────────────────────────────────────────┐
│                 Deployment Strategies                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Blue-Green Deployment                                       │
│  ├── Two identical environments: Blue (live), Green (new)    │
│  ├── Deploy to Green, smoke test, switch traffic             │
│  ├── Instant rollback: switch back to Blue                   │
│  └── Cost: 2x infrastructure during deployment               │
│                                                              │
│  Canary Deployment                                           │
│  ├── Roll out to 1% → 5% → 25% → 100% of users             │
│  ├── Monitor error rates and performance at each stage       │
│  ├── Auto-rollback if metrics degrade                        │
│  └── Best for high-traffic, risk-averse deployments          │
│                                                              │
│  Feature Flags (Decoupled from Deploy)                       │
│  ├── Deploy code → flag OFF → enable for internal → beta     │
│  │   → GA → remove flag                                      │
│  ├── Target by user, region, %, device, org                  │
│  ├── Kill switch for problematic features                    │
│  └── A/B testing built on flags                              │
│                                                              │
│  Atomic Deploys (Vercel, Netlify model)                      │
│  ├── Each deploy is an immutable snapshot                    │
│  ├── Instant rollback to any previous deploy                 │
│  ├── Preview deployments per PR                              │
│  └── No "partially deployed" state                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Feature Flag Architecture

```javascript
// Feature flag service
class FeatureFlagService {
  constructor() {
    this.flags = new Map();
    this.overrides = new Map(); // developer overrides
  }

  async initialize(userId) {
    const response = await fetch(`/api/flags?userId=${userId}`);
    const flags = await response.json();
    flags.forEach((flag) => this.flags.set(flag.name, flag));

    // SSE for real-time flag updates
    const sse = new EventSource(`/api/flags/stream?userId=${userId}`);
    sse.addEventListener('flag-update', (event) => {
      const flag = JSON.parse(event.data);
      this.flags.set(flag.name, flag);
      this.notifySubscribers(flag.name);
    });
  }

  isEnabled(flagName) {
    if (this.overrides.has(flagName)) return this.overrides.get(flagName);
    const flag = this.flags.get(flagName);
    return flag?.enabled ?? false;
  }

  getVariant(flagName) {
    const flag = this.flags.get(flagName);
    return flag?.variant ?? 'control';
  }
}

// React hook
function useFeatureFlag(flagName) {
  const flagService = useContext(FeatureFlagContext);
  const [enabled, setEnabled] = useState(flagService.isEnabled(flagName));

  useEffect(() => {
    return flagService.subscribe(flagName, (flag) => {
      setEnabled(flag.enabled);
    });
  }, [flagName, flagService]);

  return enabled;
}

// Usage
function Header() {
  const showNewNav = useFeatureFlag('new-navigation-2024');
  return showNewNav ? <NewNavigation /> : <LegacyNavigation />;
}
```

---

## 26. Design: Facebook News Feed

### Requirements

```
Functional:
  - Infinite scrolling feed of posts (text, images, videos, links)
  - Like, comment, share interactions
  - Create new post
  - Real-time updates (new posts, live reactions)
  - Post visibility (public, friends, specific groups)

Non-Functional:
  - Billions of posts, millions concurrent users
  - < 2s initial load, smooth 60fps scroll
  - Works on slow 3G connections
  - Accessible (screen readers)
  - Support for RTL languages
```

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Facebook News Feed                         │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  App Shell                                              │   │
│  │  ├── Header (logo, search, notifications, profile)      │   │
│  │  ├── Left Sidebar (navigation)                          │   │
│  │  ├── Feed (main content — scrollable)                   │   │
│  │  │   ├── CreatePostWidget                               │   │
│  │  │   ├── Stories Carousel                               │   │
│  │  │   └── PostList (virtualized)                         │   │
│  │  │       ├── PostCard                                   │   │
│  │  │       │   ├── PostHeader (avatar, name, time, menu)  │   │
│  │  │       │   ├── PostContent (text, media, link preview)│   │
│  │  │       │   ├── ReactionBar (like counts, share count) │   │
│  │  │       │   ├── ActionBar (like, comment, share)       │   │
│  │  │       │   └── CommentSection (lazy loaded)           │   │
│  │  │       │       ├── CommentList                        │   │
│  │  │       │       └── CommentInput                       │   │
│  │  │       └── ...more posts (infinite scroll)            │   │
│  │  └── Right Sidebar (contacts, sponsored)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  Data Flow:                                                    │
│  ├── Initial load: SSR first 5 posts + hydrate                 │
│  ├── Scroll: cursor-based pagination via IntersectionObserver  │
│  ├── Real-time: WebSocket for new posts, reactions             │
│  └── Mutations: optimistic updates for likes/comments          │
│                                                                │
│  State:                                                        │
│  ├── Server state: TanStack Query (posts, comments, reactions) │
│  ├── UI state: scroll position, expanded comments, modal state │
│  └── URL state: post permalinks, filter params                 │
│                                                                │
│  Performance:                                                  │
│  ├── Virtualized list (only render visible posts)              │
│  ├── Image lazy loading + progressive JPEG / AVIF             │
│  ├── Video: load poster only, play on viewport enter           │
│  ├── Comment section: lazy loaded on click/expand              │
│  ├── Code split: CreatePost modal, share dialog, reactions     │
│  ├── Skeleton screens during loading                           │
│  └── Prefetch next page when 3 posts from bottom               │
│                                                                │
│  API Design:                                                   │
│  GET /api/feed?cursor=xxx&limit=10                             │
│  POST /api/posts (create)                                      │
│  POST /api/posts/:id/reactions (like)                          │
│  GET /api/posts/:id/comments?cursor=xxx                        │
│  WebSocket: /ws/feed (new posts, reaction updates)             │
│                                                                │
│  Data Model:                                                   │
│  Post {                                                        │
│    id, authorId, content, mediaUrls[], type,                   │
│    createdAt, visibility, reactionCounts: { like, love, ... }, │
│    commentCount, shareCount, isLikedByMe                       │
│  }                                                             │
│                                                                │
│  Edge Cases:                                                   │
│  ├── Rapid-fire likes: debounce API call, optimistic UI        │
│  ├── Stale feed: "New posts available" banner (don't auto-jump)│
│  ├── Failed post creation: save draft to localStorage          │
│  ├── Long text: truncate with "See more" (CSS line-clamp)      │
│  └── Broken images: fallback placeholder                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 27. Design: Google Search Autocomplete

### Requirements

```
Functional:
  - Type → see suggestions in real-time (< 100ms perceived)
  - Suggestions: recent searches, trending, autocomplete
  - Keyboard navigation (up/down arrows, enter to select)
  - Clear recent searches, remove individual items
  - Search on Enter or suggestion click

Non-Functional:
  - < 50ms rendering per keystroke
  - Works offline (recent searches)
  - Accessible (ARIA combobox pattern)
  - Mobile-friendly
  - Handle 100K+ QPS
```

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                 Search Autocomplete                            │
│                                                                │
│  Component Tree:                                               │
│  SearchBar                                                     │
│  ├── SearchInput                                               │
│  │   ├── <input role="combobox" aria-expanded aria-controls>   │
│  │   └── Ghost text (inline suggestion)                        │
│  └── SuggestionDropdown                                        │
│      ├── RecentSearches (from localStorage)                    │
│      ├── TrendingSearches (prefetched)                         │
│      └── AutocompleteSuggestions (from API)                    │
│          └── SuggestionItem (highlighted matching text)        │
│                                                                │
│  Data Fetching Strategy:                                       │
│  ├── Debounce input: 150-300ms                                 │
│  ├── Minimum query length: 1 character                         │
│  ├── Cancel previous request (AbortController)                 │
│  ├── Cache results: "rea" cached, "reac" is "rea" + filter     │
│  ├── Trie-based client-side cache for prefix matching          │
│  └── Priority: cache hit → show instantly, API → merge results │
│                                                                │
│  Keyboard Interaction:                                         │
│  ├── ↓ Arrow: highlight next suggestion                        │
│  ├── ↑ Arrow: highlight previous                               │
│  ├── Enter: search with highlighted or input text              │
│  ├── Escape: close dropdown, clear highlight                   │
│  ├── Tab: accept inline suggestion                             │
│  └── aria-activedescendant for screen readers                  │
│                                                                │
│  Performance:                                                  │
│  ├── Show recent/trending immediately (no API call)            │
│  ├── Preconnect to suggestion API on page load                 │
│  ├── HTTP cache: Cache-Control: private, max-age=300           │
│  ├── Compress suggestion payload (short JSON)                  │
│  ├── Limit to 8-10 suggestions max                             │
│  └── Use Highlight component with dangerouslySetInnerHTML      │
│      (sanitized) or mark + text nodes for matching text        │
│                                                                │
│  Highlight Pattern:                                            │
│  Query: "reac"                                                 │
│  Suggestion: "<strong>reac</strong>t hooks tutorial"            │
│                                                                │
│  API:                                                          │
│  GET /api/autocomplete?q=reac&limit=8&lang=en                  │
│  Response: { suggestions: ["react hooks", "react router", ...] │
│              trending: [...] }                                  │
│                                                                │
│  Edge Cases:                                                   │
│  ├── Empty query: show recent + trending                       │
│  ├── No results: "No suggestions" (don't show empty dropdown)  │
│  ├── Very fast typing: only latest request matters             │
│  ├── Paste: treat as type event, debounce normally             │
│  ├── XSS: never render raw suggestion HTML                     │
│  └── IME input (CJK): handle compositionstart/end events      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 28. Design: Google Docs (Collaborative Editor)

### Requirements

```
Functional:
  - Rich text editing (bold, italic, headings, lists, tables)
  - Real-time collaboration (multiple cursors, presence)
  - Version history and undo/redo
  - Comments and suggestions
  - Offline editing with sync on reconnect

Non-Functional:
  - Real-time sync < 100ms latency
  - Handle 100+ concurrent editors
  - No data loss, eventual consistency
  - Works offline for single user
```

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              Collaborative Editor Architecture                  │
│                                                                │
│  Conflict Resolution Strategy:                                 │
│                                                                │
│  Option A: OT (Operational Transformation)                     │
│  ├── Used by Google Docs                                       │
│  ├── Server is central authority                               │
│  ├── Transforms operations against concurrent edits            │
│  ├── Complex to implement (O(n²) transform functions)          │
│  └── Proven at massive scale                                   │
│                                                                │
│  Option B: CRDT (Conflict-free Replicated Data Type)           │
│  ├── Used by Figma, newer editors                              │
│  ├── No central server needed (P2P possible)                   │
│  ├── Operations are commutative (order doesn't matter)         │
│  ├── Larger document size (metadata overhead)                  │
│  └── Libraries: Yjs, Automerge                                 │
│                                                                │
│  ┌─────────────── Client Architecture ─────────────────┐       │
│  │                                                     │       │
│  │  Editor Component (ProseMirror / TipTap / Slate)    │       │
│  │       │                                             │       │
│  │       ├── Document Model (tree of nodes)            │       │
│  │       ├── Selection / Cursor State                  │       │
│  │       ├── History (undo stack, redo stack)           │       │
│  │       └── Plugin System (formatting, mentions, etc.)│       │
│  │       │                                             │       │
│  │       ▼                                             │       │
│  │  Collaboration Layer (Yjs / OT)                     │       │
│  │       │                                             │       │
│  │       ├── Local changes → operations                │       │
│  │       ├── Send ops via WebSocket                    │       │
│  │       ├── Receive remote ops                        │       │
│  │       ├── Transform / merge                         │       │
│  │       └── Apply to local document                   │       │
│  │       │                                             │       │
│  │       ▼                                             │       │
│  │  Presence Layer                                     │       │
│  │       ├── Cursor positions of other users           │       │
│  │       ├── Selection highlights (colored per user)   │       │
│  │       └── User avatars on sidebar                   │       │
│  │       │                                             │       │
│  │       ▼                                             │       │
│  │  Offline Layer                                      │       │
│  │       ├── Queue operations in IndexedDB             │       │
│  │       ├── Mark document as "offline-modified"       │       │
│  │       └── Sync on reconnect (replay queued ops)     │       │
│  │                                                     │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                │
│  CRDT Simplified (Yjs model):                                  │
│  - Each character has a unique ID (clientId, clock)            │
│  - Insert: place character between two IDs                     │
│  - Delete: mark character as tombstone (soft delete)           │
│  - Operations are idempotent and commutative                   │
│  - All clients converge to same state regardless of order      │
│                                                                │
│  Key Performance Decisions:                                    │
│  ├── Virtualize long documents (only render visible pages)     │
│  ├── Batch DOM updates with requestAnimationFrame              │
│  ├── Throttle cursor broadcasts (max 10/sec)                   │
│  ├── Compress operations for network transfer                  │
│  ├── Lazy load images/embeds in document                       │
│  └── Use contenteditable (not textarea) for rich text          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 29. Design: Instagram Stories / TikTok Feed

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│            Instagram Stories / TikTok Feed                      │
│                                                                │
│  Stories Architecture:                                          │
│  ├── StoriesTray (horizontal scroll, top of feed)              │
│  │   └── StoryAvatar[] (preload first story image)             │
│  └── StoryViewer (fullscreen overlay)                          │
│      ├── StoryProgress (animated bars per segment)             │
│      ├── StoryContent (image/video/text)                       │
│      ├── StoryInteractions (reply, reactions, share)           │
│      └── Navigation (tap left/right, swipe, long-press pause) │
│                                                                │
│  Video Feed (TikTok model):                                    │
│  ├── Full-screen vertical swipe                                │
│  ├── One video visible at a time                               │
│  ├── Auto-play on enter viewport                               │
│  └── Snap scroll (scroll-snap-type: y mandatory)               │
│                                                                │
│  Video Preloading Strategy:                                    │
│  ┌───────────────────────────────────────┐                     │
│  │  Previous video: keep in memory       │                     │
│  │  Current video:  playing              │ ◄── viewport        │
│  │  Next video:     preload first 3 sec  │                     │
│  │  Next+1 video:   preload poster/thumb │                     │
│  │  Everything else: nothing loaded      │                     │
│  └───────────────────────────────────────┘                     │
│                                                                │
│  Autoplay Rules:                                               │
│  ├── Muted by default (browser autoplay policy)                │
│  ├── Play when > 50% in viewport (IntersectionObserver)        │
│  ├── Pause when out of viewport                                │
│  ├── Resume on return (visibility change API)                  │
│  └── Respect data-saver / reduced-motion preferences           │
│                                                                │
│  Performance:                                                  │
│  ├── Preload next video while current plays                    │
│  ├── Use video poster for instant visual feedback              │
│  ├── HLS/DASH adaptive streaming                               │
│  ├── Low-quality start, upgrade quality as bandwidth allows    │
│  ├── Recycle video elements (pool of 3-5 <video> elements)     │
│  ├── Pause/destroy off-screen videos (memory management)       │
│  └── Use IntersectionObserver threshold: [0, 0.5, 1.0]        │
│                                                                │
│  Gesture Handling:                                              │
│  ├── Swipe up/down: next/previous video                        │
│  ├── Double-tap: like animation                                │
│  ├── Long-press: pause video                                   │
│  ├── Swipe left: profile/info panel                            │
│  └── Handle touch vs mouse vs keyboard                         │
│                                                                │
│  CSS Scroll Snapping:                                          │
│  .feed-container {                                             │
│    scroll-snap-type: y mandatory;                              │
│    overflow-y: scroll;                                         │
│    height: 100vh;                                              │
│  }                                                             │
│  .video-item {                                                 │
│    scroll-snap-align: start;                                   │
│    height: 100vh;                                              │
│  }                                                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 30. Design: Slack / Chat Application

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Chat Application                              │
│                                                                │
│  Component Layout:                                             │
│  ┌──────┬───────────────┬──────────────────────┬────────────┐  │
│  │      │               │                      │            │  │
│  │ Work │   Channel     │   Message Pane       │  Thread /  │  │
│  │ space│   Sidebar     │                      │  Details   │  │
│  │ Rail │               │  ┌────────────────┐  │  Panel     │  │
│  │      │  #general     │  │ Message List   │  │            │  │
│  │      │  #engineering │  │ (virtualized)  │  │            │  │
│  │      │  #random      │  │                │  │            │  │
│  │      │               │  │ ──────────────  │  │            │  │
│  │      │  DMs          │  │ "New messages"  │  │            │  │
│  │      │  @alice       │  │ ──────────────  │  │            │  │
│  │      │  @bob         │  │                │  │            │  │
│  │      │               │  └────────────────┘  │            │  │
│  │      │               │  ┌────────────────┐  │            │  │
│  │      │               │  │ Composer       │  │            │  │
│  │      │               │  │ (rich text)    │  │            │  │
│  │      │               │  └────────────────┘  │            │  │
│  └──────┴───────────────┴──────────────────────┴────────────┘  │
│                                                                │
│  Real-Time Architecture:                                       │
│  ├── WebSocket per workspace (not per channel)                 │
│  ├── Subscribe to channels server-side                         │
│  ├── Server pushes: message, typing, presence, reaction        │
│  ├── Client multiplexes events to correct channel UI           │
│  └── Reconnection with "catch-up" (fetch missed messages)      │
│                                                                │
│  Message Rendering:                                            │
│  ├── Markdown parsing (bold, italic, code, links)              │
│  ├── @mentions → highlighted, linked to profile                │
│  ├── Emoji: shortcodes (:smile:) → Unicode or custom images    │
│  ├── Code blocks with syntax highlighting (lazy-loaded)        │
│  ├── File attachments (image preview, file icon)               │
│  ├── Link previews (unfurling — fetched server-side)           │
│  ├── Thread indicator ("3 replies" clickable)                  │
│  └── Reactions row (emoji + count)                             │
│                                                                │
│  Virtualization for Messages:                                  │
│  ├── Variable height (each message has different content)      │
│  ├── Scroll anchoring (new messages don't jump scroll)         │
│  ├── Bi-directional loading (scroll up for history)            │
│  ├── Jump to latest button when scrolled up                    │
│  └── Maintain scroll position on channel switch (save/restore) │
│                                                                │
│  Typing Indicator:                                             │
│  ├── Send "typing" event on keystroke (throttled: 3s)          │
│  ├── Auto-expire after 5s of no typing                         │
│  ├── Show "Alice is typing..." with animated dots              │
│  └── Multiple users: "Alice and Bob are typing..."             │
│                                                                │
│  Unread Management:                                            │
│  ├── Track last-read message per channel                       │
│  ├── Unread count badge on channel list                        │
│  ├── "New messages" separator in message list                  │
│  ├── Mark as read when channel is visible + focused            │
│  └── Tab title: "(3) Slack" for unread count                   │
│                                                                │
│  Offline Behavior:                                             │
│  ├── Cache recent channels + messages in IndexedDB             │
│  ├── Queue outgoing messages                                   │
│  ├── Show "reconnecting..." banner                             │
│  ├── Sync on reconnect (fetch messages since last seen)        │
│  └── Show cached messages immediately on channel switch        │
│                                                                │
│  Search:                                                       │
│  ├── Full-text search across channels                          │
│  ├── Filters: from:alice, in:#general, has:link, before:today  │
│  ├── Search results with context (messages around match)       │
│  ├── Click result → scroll to message in channel               │
│  └── Debounced, server-side search with pagination             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 31. Design: E-Commerce Product Page (Amazon)

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              E-Commerce Product Page                            │
│                                                                │
│  Rendering: ISR (Incremental Static Regeneration)              │
│  ├── Product info rarely changes → SSG with revalidation       │
│  ├── Price, availability → client-side fetch (always fresh)    │
│  └── Reviews → lazy loaded on scroll                           │
│                                                                │
│  Component Breakdown:                                          │
│  ProductPage                                                   │
│  ├── Breadcrumbs                                               │
│  ├── ProductGallery                                            │
│  │   ├── MainImage (zoom on hover, lightbox on click)          │
│  │   ├── ThumbnailStrip                                        │
│  │   └── 360° view / Video tab                                 │
│  ├── ProductInfo                                               │
│  │   ├── Title, Brand, Rating (stars + count)                  │
│  │   ├── Price (sale price, original, discount %)              │
│  │   ├── VariantSelector (size, color — reloads image)         │
│  │   ├── QuantitySelector                                      │
│  │   ├── AddToCartButton (sticky on mobile)                    │
│  │   ├── DeliveryEstimate (personalized by zipcode)            │
│  │   └── ProductBadges (Prime, Best Seller, etc.)              │
│  ├── ProductDetails (tabs or accordion)                        │
│  │   ├── Description (HTML content)                            │
│  │   ├── Specifications (key-value table)                      │
│  │   └── Size Guide                                            │
│  ├── ReviewsSection (lazy loaded)                              │
│  │   ├── RatingSummary (histogram)                             │
│  │   ├── ReviewFilters (star, verified, with images)           │
│  │   └── ReviewList (paginated)                                │
│  ├── RecommendedProducts (carousel)                            │
│  │   └── ProductCard[] (lazy loaded images)                    │
│  └── RecentlyViewed (from localStorage)                        │
│                                                                │
│  Cart Architecture:                                            │
│  ├── Cart state: Context + useReducer (or Zustand)             │
│  ├── Persist to localStorage + sync with server                │
│  ├── Optimistic "Add to Cart" (instant UI feedback)            │
│  ├── Cart count in header (updates globally)                   │
│  ├── Cart drawer vs full cart page                              │
│  └── Inventory check before checkout                           │
│                                                                │
│  Performance:                                                  │
│  ├── Hero image preloaded in <head>                            │
│  ├── Product JSON-LD for SEO (structured data)                 │
│  ├── Above-fold content SSR'd (image, title, price, CTA)      │
│  ├── Reviews, recommendations below fold → lazy                │
│  ├── Image gallery: preload next image on hover                │
│  ├── Price/availability: client-side fetch (< 200ms)           │
│  └── Variant images prefetched on variant hover                │
│                                                                │
│  SEO:                                                          │
│  ├── Structured data (Product schema, AggregateRating)         │
│  ├── Canonical URL per product                                 │
│  ├── Open Graph tags for social sharing                        │
│  ├── Dynamic meta tags (title = product name)                  │
│  └── Breadcrumb structured data                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 32. Design: Google Maps

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Google Maps                                │
│                                                                │
│  Tile-Based Rendering:                                         │
│  ├── World divided into tiles (256×256 px or 512×512)          │
│  ├── Tile coordinates: (x, y, zoom level)                      │
│  ├── Only load tiles visible in viewport + buffer              │
│  ├── Pre-fetch adjacent tiles for smooth panning               │
│  └── Cache tiles aggressively (they rarely change)             │
│                                                                │
│  ┌──────────────────────────────────────────┐                  │
│  │  Zoom 0: 1 tile (whole world)           │                  │
│  │  Zoom 1: 4 tiles                        │                  │
│  │  Zoom 2: 16 tiles                       │                  │
│  │  ...                                    │                  │
│  │  Zoom 20: ~1 trillion tiles             │                  │
│  │                                         │                  │
│  │  Only ~20-30 tiles visible at any time   │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                │
│  Rendering Approaches:                                         │
│  ├── Canvas 2D: simpler, lower GPU usage                       │
│  ├── WebGL: better for 3D, smooth rotation, millions of points │
│  └── SVG: for overlays (not tiles), scalable, accessible       │
│                                                                │
│  Marker Clustering:                                             │
│  ├── 10K+ markers → cluster into groups                        │
│  ├── Cluster by grid or distance                               │
│  ├── Show count on cluster marker                              │
│  ├── Expand on zoom in                                         │
│  └── Use Web Worker for clustering calculation                 │
│                                                                │
│  Interaction Handling:                                          │
│  ├── Pan: track mouse drag → update tile offset                │
│  ├── Zoom: wheel event → zoom level + recompute tiles          │
│  ├── Pinch zoom: touch events + gesture recognition            │
│  ├── Smooth animation: interpolate zoom level with rAF         │
│  └── Inertial scrolling: velocity-based deceleration           │
│                                                                │
│  Search + Geocoding:                                           │
│  ├── Autocomplete for places (debounced, same as search Q27)   │
│  ├── Geocode address → lat/lng                                 │
│  ├── Reverse geocode: click on map → address                   │
│  └── Search results as markers + list panel                    │
│                                                                │
│  Directions / Routing:                                         │
│  ├── Polyline overlay (GeoJSON → Canvas/SVG path)              │
│  ├── Turn-by-turn instructions (step list)                     │
│  ├── ETA with real-time traffic (WebSocket updates)            │
│  ├── Multiple route alternatives                               │
│  └── Drag route to modify                                      │
│                                                                │
│  Performance:                                                  │
│  ├── Tile prefetching (adjacent tiles at same zoom)            │
│  ├── Level-of-detail: fewer labels at low zoom                 │
│  ├── Debounce tile requests during fast pan/zoom               │
│  ├── RequestAnimationFrame for smooth animation                │
│  ├── OffscreenCanvas for worker-based rendering                │
│  └── Tile cache: IndexedDB for offline tiles                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 33. Design: Spreadsheet (Google Sheets)

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Spreadsheet                                │
│                                                                │
│  Data Model:                                                   │
│  ├── NOT a 2D array (too sparse, most cells empty)             │
│  ├── Use sparse representation: Map<"A1", CellData>            │
│  ├── CellData: { rawValue, formula, computedValue, format }    │
│  └── Dependency graph for formula recalculation                │
│                                                                │
│  Cell = {                                                      │
│    raw: "=SUM(A1:A10)",    // what user typed                  │
│    computed: 42,            // evaluated result                 │
│    format: { bold: true, color: "#333", type: "number" },      │
│    dependsOn: ["A1","A2",...,"A10"],  // formula dependencies   │
│    dependedBy: ["B15"]     // cells that reference this cell   │
│  }                                                             │
│                                                                │
│  Rendering (Canvas-based):                                     │
│  ├── DOM-based: ❌ 1M cells = 1M <div>s (impossible)           │
│  ├── Canvas 2D: ✅ draw only visible cells (~50-100)           │
│  ├── Overlay DOM for active cell (input, selection, menus)     │
│  └── Virtual scrolling with canvas repaint on scroll           │
│                                                                │
│  Formula Engine:                                               │
│  ├── Parse formula string → AST (Abstract Syntax Tree)         │
│  ├── Evaluate AST against cell data                            │
│  ├── Dependency tracking (directed acyclic graph)              │
│  ├── Topological sort for evaluation order                     │
│  ├── Circular reference detection                              │
│  ├── Run in Web Worker (don't block main thread)               │
│  └── Incremental recalculation (only dirty cells + dependents) │
│                                                                │
│  ┌────── Dependency Graph ──────┐                              │
│  │  A1 ──► B1 (=A1*2)          │                              │
│  │  A2 ──► B1                  │                              │
│  │  B1 ──► C1 (=B1+10)         │                              │
│  │                             │                              │
│  │  Change A1 → recalc B1 → recalc C1                         │
│  │  (topological order: A1, B1, C1)                            │
│  └──────────────────────────────┘                              │
│                                                                │
│  Selection & Interaction:                                      │
│  ├── Click cell → show input overlay at cell position          │
│  ├── Range selection: mousedown → mousemove → mouseup          │
│  ├── Multi-select: Cmd/Ctrl + click                            │
│  ├── Column/row resize: drag border                            │
│  ├── Copy/paste: Clipboard API (preserve formatting)           │
│  ├── Fill handle: drag corner to auto-fill                     │
│  └── Keyboard: arrow keys, Tab, Enter, F2 (edit mode)         │
│                                                                │
│  Collaboration:                                                │
│  ├── CRDT or OT for concurrent cell edits                      │
│  ├── Cell-level locking during active edit                     │
│  ├── Colored cursors per user                                  │
│  └── Conflict: last-write-wins for same cell                   │
│                                                                │
│  Performance:                                                  │
│  ├── Canvas rendering: only visible cells (~2000 max)          │
│  ├── Formula evaluation: Web Worker + memoization              │
│  ├── Batch updates: collect changes, recalc once               │
│  ├── Lazy formatting: compute cell format on paint             │
│  └── Undo/redo: command pattern (store inverse operations)     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 34. Design: Video Player (YouTube)

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Video Player                                │
│                                                                │
│  Component Hierarchy:                                          │
│  VideoPlayer                                                   │
│  ├── VideoElement (<video> with HLS.js / dash.js)              │
│  ├── PosterOverlay (thumbnail before play)                     │
│  ├── BufferingSpinner                                          │
│  ├── ControlsOverlay (show/hide on hover/tap)                  │
│  │   ├── ProgressBar                                           │
│  │   │   ├── LoadedBuffer (gray bar)                           │
│  │   │   ├── PlayedProgress (red bar)                          │
│  │   │   ├── SeekPreview (thumbnail on hover)                  │
│  │   │   └── ChapterMarkers                                   │
│  │   ├── PlayPauseButton                                       │
│  │   ├── VolumeControl (slider + mute)                         │
│  │   ├── TimeDisplay (current / total)                         │
│  │   ├── SpeedSelector (0.5x - 2x)                            │
│  │   ├── QualitySelector (auto, 360p-4K)                       │
│  │   ├── SubtitleSelector                                      │
│  │   ├── PictureInPictureButton                                │
│  │   └── FullscreenButton                                      │
│  ├── SubtitleOverlay (WebVTT renderer)                         │
│  ├── AnnotationOverlay (cards, end screens)                    │
│  └── KeyboardShortcuts (Space, M, F, J, K, L, arrows)         │
│                                                                │
│  Adaptive Streaming:                                           │
│  ├── HLS.js / dash.js for adaptive bitrate                     │
│  ├── Monitor bandwidth → switch quality automatically          │
│  ├── Buffer 30-60s ahead                                       │
│  ├── Quality switch at segment boundaries (seamless)           │
│  └── User manual override persisted in preferences             │
│                                                                │
│  Seek Preview (Thumbnail Scrubbing):                           │
│  ├── Pre-generated sprite sheet (grid of thumbnails)           │
│  ├── One sprite per N seconds (e.g., every 5s)                 │
│  ├── On hover over progress bar → show correct sprite          │
│  └── Calculate sprite position: time → column/row in grid      │
│                                                                │
│  Keyboard Shortcuts:                                           │
│  ├── Space/K: play/pause                                       │
│  ├── J/L: seek -10s/+10s                                       │
│  ├── Arrow left/right: seek -5s/+5s                            │
│  ├── Arrow up/down: volume +5%/-5%                             │
│  ├── M: mute/unmute                                            │
│  ├── F: fullscreen toggle                                      │
│  ├── C: captions toggle                                        │
│  ├── < / >: playback speed down/up                             │
│  └── 0-9: seek to 0%-90% of video                              │
│                                                                │
│  Accessibility:                                                │
│  ├── Keyboard-only operation (all shortcuts above)             │
│  ├── Screen reader: aria-label on all controls                 │
│  ├── Captions: WebVTT format, style customizable               │
│  ├── Audio description track                                  │
│  └── Focus management (controls appear on focus)               │
│                                                                │
│  Analytics Events:                                             │
│  ├── play, pause, seek, complete                               │
│  ├── Buffer events (stall count, duration)                     │
│  ├── Quality changes (auto and manual)                         │
│  ├── Watch time (heartbeat every 30s)                          │
│  ├── Drop-off points (where users leave)                       │
│  └── Engagement (likes, shares, comments while watching)       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 35. Design: Notification System

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   Notification System                           │
│                                                                │
│  Notification Types:                                           │
│  ├── In-app (bell icon → dropdown / notification center)       │
│  ├── Push (browser Push API / FCM)                             │
│  ├── Email (server-side, not frontend concern)                 │
│  ├── Toast (ephemeral, auto-dismiss)                           │
│  └── Badge (unread count on tab, favicon, app icon)            │
│                                                                │
│  In-App Architecture:                                          │
│  ┌──────────────────────────────────────────┐                  │
│  │  NotificationBell                        │                  │
│  │  ├── Badge (unread count)                │                  │
│  │  └── NotificationPanel (dropdown)        │                  │
│  │      ├── NotificationTabs                │                  │
│  │      │   ├── All                         │                  │
│  │      │   ├── Mentions                    │                  │
│  │      │   └── Unread                      │                  │
│  │      ├── NotificationList (virtualized)  │                  │
│  │      │   └── NotificationItem            │                  │
│  │      │       ├── Avatar                  │                  │
│  │      │       ├── Content (rich text)     │                  │
│  │      │       ├── Timestamp (relative)    │                  │
│  │      │       ├── Actions (accept/reject) │                  │
│  │      │       └── Unread indicator        │                  │
│  │      ├── MarkAllRead button              │                  │
│  │      └── EmptyState                      │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                │
│  Real-Time Delivery:                                           │
│  ├── SSE for notification stream (Server-Sent Events)          │
│  │   → Simpler than WebSocket for unidirectional flow          │
│  ├── Reconnection with last-event-id                           │
│  ├── Missed notifications: fetch on reconnect                  │
│  │   GET /api/notifications?since={lastEventId}                │
│  └── Cross-tab coordination: BroadcastChannel API              │
│      → One tab maintains SSE, broadcasts to others             │
│                                                                │
│  Push Notifications:                                           │
│  1. Register Service Worker                                    │
│  2. Request permission: Notification.requestPermission()       │
│  3. Subscribe: registration.pushManager.subscribe(options)     │
│  4. Send subscription to server                                │
│  5. Server sends push via Push API (web-push library)          │
│  6. SW receives push event → show notification                 │
│  7. User clicks → notificationclick event → open/focus app     │
│                                                                │
│  Toast System:                                                 │
│  ├── Queue-based: max 3 visible at a time                      │
│  ├── Position: top-right (desktop), bottom (mobile)            │
│  ├── Auto-dismiss: 5s default (configurable)                   │
│  ├── Pause timer on hover                                      │
│  ├── Swipe to dismiss (mobile)                                 │
│  ├── Types: success, error, warning, info                      │
│  ├── Stacking animation (push down, slide in)                  │
│  └── aria-live="polite" for screen readers                     │
│                                                                │
│  Unread Count:                                                 │
│  ├── Badge on bell icon                                        │
│  ├── Tab title: "(5) App Name"                                 │
│  ├── Favicon badge (draw on canvas, set as favicon)            │
│  └── navigator.setAppBadge(5) (PWA)                            │
│                                                                │
│  Notification Preferences:                                     │
│  ├── Per-category: comments (on), marketing (off)              │
│  ├── Per-channel: email (on), push (off), in-app (on)          │
│  ├── Quiet hours: no push between 10pm-8am                     │
│  ├── Digest mode: batch into hourly/daily summary              │
│  └── Store preferences: server-side (synced across devices)    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 36. Cheatsheet & Interview Quick Reference

### The 60-Second Component Design Checklist

```
□ Props API — What data does it receive? What callbacks?
□ State — What's local? What's lifted? What's server state?
□ Rendering — SSR, CSR, or hybrid? Code split?
□ Data fetching — When? How? Caching? Error handling?
□ Loading — Skeleton? Spinner? Progressive?
□ Error — Boundary? Retry? Fallback UI?
□ Empty — Zero state? First-time user experience?
□ Accessibility — Keyboard? ARIA? Focus management?
□ Performance — Memoization? Virtualization? Lazy loading?
□ Responsiveness — Mobile-first? Breakpoints? Touch?
□ Testing — What integration tests? What E2E?
□ Monitoring — Error tracking? Performance metrics?
```

### Key Numbers to Know

```
Network:
  DNS lookup:          ~20-120ms
  TCP handshake:       ~30-100ms (one RTT)
  TLS handshake:       ~30-100ms (one RTT with TLS 1.3)
  HTTP request:        ~50-300ms (origin)
  CDN response:        ~5-50ms (edge)
  WebSocket frame:     ~1-5ms (after connection)

Browser:
  Frame budget (60fps):      16.67ms
  Long task threshold:       50ms
  localStorage read:         ~0.5ms (synchronous)
  IndexedDB read:           ~1-5ms (async)
  DOM node cost:            ~0.5-1KB each
  Max DOM nodes (practical): ~1500-3000

Bundle Sizes (gzipped):
  React + ReactDOM:          ~45KB
  Vue 3:                     ~33KB
  Svelte (runtime):          ~2KB
  TanStack Query:            ~12KB
  Zustand:                   ~1KB
  date-fns (one function):   ~1KB
  lodash (full):             ~70KB ❌
  lodash-es (tree-shaken):   depends on usage

User Perception:
  0-100ms:    Instant
  100-300ms:  Slight delay (still feels responsive)
  300-1000ms: Noticeable (show loading indicator)
  1000ms+:    User loses focus (show progress)
  10000ms+:   User leaves
```

### Rendering Strategy Decision Tree

```
Is the content public and SEO-critical?
├── YES → Is it mostly static?
│         ├── YES → SSG or ISR
│         └── NO  → SSR (or streaming SSR)
└── NO  → Is it behind authentication?
          ├── YES → CSR (SPA) or SSR with auth
          └── NO  → Does it need instant updates?
                    ├── YES → CSR with WebSocket/SSE
                    └── NO  → SSR or CSR (either works)
```

### Communication Protocol Decision Tree

```
Do you need bidirectional real-time?
├── YES → WebSocket
│         (chat, gaming, collaboration)
└── NO  → Do you need server-push only?
          ├── YES → SSE (Server-Sent Events)
          │         (notifications, live scores, feeds)
          └── NO  → How fresh does data need to be?
                    ├── Real-time → Short polling (1-5s)
                    ├── Near-real → Long polling (30s)
                    └── Eventually → Normal REST + cache
```

### State Management Decision Tree

```
Where should state live?

Is it computed from other state?
  → useMemo / selector (NEVER store derived state)

Used by only ONE component?
  → useState / useReducer

Needed by parent + child?
  → Props (lift to parent)

Shared by siblings?
  → Lift to nearest common ancestor

Comes from server?
  → TanStack Query / SWR

Should survive refresh?
  → URL params (searchParams)

Truly global (auth, theme)?
  → Context / Zustand / Redux
```

### Performance Optimization Priority

```
Impact vs Effort (do these in order):

1. [HIGH impact, LOW effort]
   ├── Code splitting (route-based)
   ├── Image optimization (format, lazy loading)
   ├── Preconnect / preload critical resources
   └── Cache-Control headers on static assets

2. [HIGH impact, MEDIUM effort]
   ├── Server-side rendering (critical path)
   ├── Bundle analysis + tree shaking
   ├── Component lazy loading (below fold)
   └── API response caching (TanStack Query)

3. [MEDIUM impact, MEDIUM effort]
   ├── Virtualization (long lists)
   ├── Web Workers (CPU-heavy tasks)
   ├── Service Worker caching
   └── Font optimization (subset, display)

4. [MEDIUM impact, HIGH effort]
   ├── Micro-frontends
   ├── Edge rendering (edge SSR)
   ├── Custom image CDN pipeline
   └── HTTP/3 + Early Hints
```

### Common Interview Answers Template

```
When asked "How would you design X?":

"First, let me clarify the requirements...
  - Who are the users?
  - What's the expected scale?
  - What platforms (web only? mobile web?)
  - Any specific performance targets?

For the high-level architecture, I'd use...
  - [Rendering strategy] because [reason]
  - [State management] because [reason]
  - [Data fetching approach] because [reason]

The key components would be...
  - [Component A] responsible for [X]
  - [Component B] responsible for [Y]
  - [Component C] responsible for [Z]

For data, I'd structure the API as...
  - [Endpoint/query] returning [shape]
  - Caching strategy: [approach]
  - Real-time updates via [transport]

The main performance considerations are...
  - [Technique 1] to address [bottleneck]
  - [Technique 2] to address [bottleneck]

For accessibility...
  - [ARIA pattern] for [widget]
  - Keyboard navigation via [approach]

The trade-off I'm making is...
  - [Option A] vs [Option B]
  - I chose [A] because [reason], accepting [downside]"
```

---

**Last updated:** April 2026

> "The best frontend system design answers show you've shipped real products —
> you know where the dragons live because you've fought them before."
