# Virtualization Deep Dive
## `@tanstack/react-virtual` — From Zero to Production

---

## Table of Contents

1. [Why Virtualization Exists](#1-why-virtualization-exists)
2. [How the Browser Renders Lists (The Problem)](#2-how-the-browser-renders-lists-the-problem)
3. [Fixed-Size Virtualization — The Foundation](#3-fixed-size-virtualization--the-foundation)
4. [Variable-Height Virtualization — The Real World](#4-variable-height-virtualization--the-real-world)
5. [Mini Project — HackerNews Feed with Real API](#5-mini-project--hackernews-feed-with-real-api)
6. [Infinite Scroll with Virtualization](#6-infinite-scroll-with-virtualization)
7. [Reverse Scroll (Chat Apps)](#7-reverse-scroll-chat-apps)
8. [Horizontal Virtualization](#8-horizontal-virtualization)
9. [2D Grid Virtualization](#9-2d-grid-virtualization)
10. [System Design Concepts](#10-system-design-concepts)
11. [Performance Profiling Checklist](#11-performance-profiling-checklist)
12. [Common Bugs and Fixes](#12-common-bugs-and-fixes)
13. [Browser Rendering Pipeline](#13-browser-rendering-pipeline--how-the-screen-actually-updates)
14. [Reflow and Repaint](#14-reflow-and-repaint--the-expensive-steps)
15. [GPU vs CPU — Why transform is Fast](#15-gpu-vs-cpu--why-transform-is-fast)
16. [Layout Thrashing](#16-layout-thrashing--reading-and-writing-in-a-loop)
17. [Cursor-Based Pagination with Virtualization](#17-cursor-based-pagination-with-virtualization)
18. [Memory Management for Large Datasets](#18-memory-management-for-large-datasets)
19. [Bidirectional Scroll — Jump to Any Position](#19-bidirectional-scroll--jump-to-any-position)
20. [Industry Patterns — How Slack, Twitter, Linear Do It](#20-industry-patterns--how-slack-twitter-linear-do-it)
21. [Callback Refs — How ref={fn} Actually Works](#21-callback-refs--how-reffn-actually-works)
22. [ResizeObserver — Complete Tutorial](#22-resizeobserver--complete-tutorial)
23. [IntersectionObserver — Complete Tutorial](#23-intersectionobserver--complete-tutorial)
24. [MutationObserver — Complete Tutorial](#24-mutationobserver--complete-tutorial)
25. [PerformanceObserver — Complete Tutorial](#25-performanceobserver--complete-tutorial)
26. [All Four Observers — When to Use Which](#26-all-four-observers--when-to-use-which)

---

## 1. Why Virtualization Exists

### The Mental Model

Imagine a printed book with 10,000 pages. You open it to page 50. You are **reading** pages 48–52. The other 9,995 pages exist physically in the book, but your eyes only engage with 5 of them.

The browser is dumb — without virtualization, it builds all 10,000 pages into memory and lays them all out, even though you can only see 5.

**Virtualization** tells the browser: _"Only build the 5 pages I can see right now. When I turn a page, swap the old one out and build the new one."_

### Numbers That Make It Real

| Items in DOM | Scroll FPS | Time to First Paint | Memory |
|---|---|---|---|
| 100 | 60fps | 50ms | ~5MB |
| 1,000 | 45fps | 200ms | ~30MB |
| 10,000 | 8fps | 2,000ms | ~200MB |
| 10,000 (virtualized) | 60fps | 50ms | ~8MB |

The virtualized list with 10,000 items is **identical in performance** to a plain list with 100 items.

---

## 2. How the Browser Renders Lists (The Problem)

### The Render Pipeline

Every DOM element goes through this pipeline:

```
JavaScript → Style → Layout → Paint → Composite
                      ↑
              This is the expensive one
              (called "reflow" or "layout thrashing")
```

**Layout** computes the exact pixel position and size of every element. If you have 10,000 `<div>` elements, the browser calculates geometry for all 10,000 — even the ones 50,000px below the viewport.

### What "Scroll" Actually Does

```
User moves scrollbar
        ↓
Browser updates scrollTop property on container
        ↓
Browser composites layers — moves the painted canvas up/down
        ↓
(No layout recalculation for static content)
```

Scrolling itself is fast — it's just moving pixels. The problem is the **initial layout cost** of building thousands of elements.

### The Virtualization Trick

```
Instead of:
  <div style="height: 500000px">   ← real height of all items
    <div>item 0</div>              ← all 10,000 in DOM
    <div>item 1</div>
    ...
    <div>item 9999</div>
  </div>

Virtualization does:
  <div style="height: 500000px">   ← same outer height (for scrollbar)
    <div style="position:absolute; top: 24800px">item 413</div>  ← only
    <div style="position:absolute; top: 24850px">item 414</div>  ← visible
    <div style="position:absolute; top: 24900px">item 415</div>  ← items
    ...12 more items...
  </div>
```

The scrollbar looks identical to the user. The DOM has 15 nodes instead of 10,000.

---

## 3. Fixed-Size Virtualization — The Foundation

> **When to use**: All items have the same height. Product grids, settings lists, option dropdowns, user lists.

### Install

```bash
npm install @tanstack/react-virtual
```

### Minimal Working Example

```tsx
// FixedList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

const ITEMS = Array.from({ length: 10_000 }, (_, i) => ({
  id: i,
  name: `User #${i}`,
  email: `user${i}@example.com`,
}));

const ROW_HEIGHT = 56; // Every row is exactly 56px

export function FixedList() {
  // The scrollable container — THIS element has overflow: auto
  const scrollRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: ITEMS.length,            // total number of items
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT, // fixed — always 56
    overscan: 5,                    // render 5 extra above and below viewport
  });

  return (
    // Scrollable viewport — fixed height
    <div
      ref={scrollRef}
      style={{ height: 600, overflowY: 'auto', border: '1px solid #e5e7eb' }}
    >
      {/*
        Inner container — its height equals the SUM of all item heights.
        This is what makes the scrollbar look correct.
        Without this, scrollbar would only represent visible items.
      */}
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>

        {virtualizer.getVirtualItems().map((virtualItem) => {
          const item = ITEMS[virtualItem.index];

          return (
            <div
              key={item.id}
              style={{
                position: 'absolute',
                top: virtualItem.start,   // pixel offset from top of inner container
                width: '100%',
                height: ROW_HEIGHT,       // must match estimateSize
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', padding: '0 16px', height: '100%', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', flexShrink: 0 }}>
                  {item.name[0]}
                </div>
                <div style={{ marginLeft: 12 }}>
                  <div style={{ fontWeight: 500 }}>{item.name}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{item.email}</div>
                </div>
              </div>
            </div>
          );
        })}

      </div>
    </div>
  );
}
```

### Anatomy of `getVirtualItems()`

Every object in `virtualizer.getVirtualItems()` gives you:

```typescript
{
  index: 413,          // which item in your data array
  start: 23128,        // top offset in pixels (= index × ROW_HEIGHT for fixed)
  end: 23184,          // bottom offset in pixels (= start + ROW_HEIGHT)
  size: 56,            // height of this item
  key: 413,            // React key (same as index by default)
  lane: 0,             // for masonry layouts (later)
}
```

### What `getTotalSize()` Returns

```
getTotalSize() = sum of ALL item heights
              = 10,000 × 56
              = 560,000px

This is set as the inner container height.
This is why the scrollbar thumb is tiny and proportionally correct.
```

### Scrolling to an Index Programmatically

```tsx
// Jump immediately
virtualizer.scrollToIndex(500);

// Smooth scroll
virtualizer.scrollToIndex(500, { behavior: 'smooth' });

// Align item to the top/center/bottom of viewport
virtualizer.scrollToIndex(500, { align: 'start' });   // item at top
virtualizer.scrollToIndex(500, { align: 'center' });  // item centered
virtualizer.scrollToIndex(500, { align: 'end' });     // item at bottom
```

---

## 4. Variable-Height Virtualization — The Real World

> **When to use**: Item heights depend on content. Chat messages, news feeds, comment threads, email inboxes, issue lists.

### The Problem Fixed-Size Cannot Solve

```
// Fixed size assumes:
item[0].top = 0 × 56    = 0
item[1].top = 1 × 56    = 56
item[2].top = 2 × 56    = 112

// But in reality:
item[0] renders to 42px  (short text)
item[1] renders to 180px (3-paragraph text)
item[2] renders to 300px (image)

// So item[2] should start at:
item[2].top = 42 + 180 = 222   (not 112!)

// Fixed-size virtualizer places it at 112 → OVERLAP with item[1]
```

### The Solution: Measure and Cache

The `@tanstack/react-virtual` library handles this with `measureElement`:

```tsx
// VariableList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

// Simulated data — items have different amounts of text
const POSTS = Array.from({ length: 5_000 }, (_, i) => ({
  id: i,
  title: `Post #${i}`,
  // Body length varies — creates variable heights
  body: 'Lorem ipsum '.repeat(Math.floor(Math.random() * 20) + 1),
  tags: Array.from({ length: Math.floor(Math.random() * 5) }, (_, t) => `tag-${t}`),
}));

export function VariableList() {
  const scrollRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: POSTS.length,
    getScrollElement: () => scrollRef.current,

    // INITIAL ESTIMATE — used before actual measurement
    // The library replaces this with real measurements after render
    estimateSize: () => 80,

    overscan: 5,
  });

  return (
    <div ref={scrollRef} style={{ height: 600, overflowY: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>

        {virtualizer.getVirtualItems().map((virtualItem) => {
          const post = POSTS[virtualItem.index];

          return (
            <div
              key={post.id}
              data-index={virtualItem.index}   // ← REQUIRED for measureElement
              ref={virtualizer.measureElement} // ← ResizeObserver attaches here
              style={{
                position: 'absolute',
                top: virtualItem.start,
                width: '100%',
                // DO NOT set height here — let content determine it
              }}
            >
              <PostCard post={post} />
            </div>
          );
        })}

      </div>
    </div>
  );
}

function PostCard({ post }: { post: typeof POSTS[0] }) {
  return (
    <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb' }}>
      <h3 style={{ margin: '0 0 8px', fontSize: 15, fontWeight: 600 }}>
        {post.title}
      </h3>
      <p style={{ margin: '0 0 8px', fontSize: 14, color: '#374151', lineHeight: 1.6 }}>
        {post.body}
      </p>
      <div style={{ display: 'flex', gap: 6 }}>
        {post.tags.map(tag => (
          <span key={tag} style={{ padding: '2px 8px', background: '#eff6ff', color: '#2563eb', borderRadius: 4, fontSize: 12 }}>
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
```

### The `data-index` + `measureElement` Contract

This is the most important part to understand:

```tsx
// When you write this:
<div
  data-index={virtualItem.index}   // "I am item #413"
  ref={virtualizer.measureElement} // "please measure me"
>

// The library does this internally:
const observer = new ResizeObserver(([entry]) => {
  const index = entry.target.dataset.index;  // reads data-index
  const height = entry.borderBoxSize[0].contentBlockSize;

  // Updates internal height cache: { 413: 142 }
  heightCache[index] = height;

  // Rebuilds prefix sum array from index 413 onward
  rebuildOffsetsFrom(413);
});
observer.observe(element);
```

### Prefix Sum — How Offsets Stay Correct

After measuring items `[0, 1, 2]` with heights `[42, 180, 300]`:

```
offsets = [0, 42, 222, 522]
           ↑   ↑    ↑    ↑
           |   |    |    total height
           |   |    item[2].start = 42 + 180 = 222
           |   item[1].start = 42
           item[0].start = 0

// Query: where does item[2] start?
// Answer: offsets[2] = 222 ✓
```

When item[1] changes height from 180 to 250 (e.g., user expands it):

```
Rebuild from index 1:
  offsets[1] = 42          (unchanged — item[0] didn't change)
  offsets[2] = 42 + 250    = 292  (updated)
  offsets[3] = 292 + 300   = 592  (updated)
  ...all subsequent items shift down by 70px
```

This is O(n) rebuild from the changed index, not the full list.

### Binary Search for startIndex

```
User scrolls to scrollTop = 8500px
"Which item starts at or before 8500px?"

offsets = [0, 42, 222, 522, 680, ..., 8430, 8612, ...]
                                         ↑      ↑
                                      item 97  item 98

Binary search finds: 8430 ≤ 8500 < 8612
→ startIndex = 97

Without binary search (linear scan): O(n) — 97 comparisons
With binary search: O(log n) — 7 comparisons
```

---

## 5. Mini Project — HackerNews Feed with Real API

> Full working project: virtualized list of HackerNews stories, loaded from the real API, with dynamic heights.

### Project Setup

```bash
npm create vite@latest hn-feed -- --template react-ts
cd hn-feed
npm install @tanstack/react-virtual @tanstack/react-query
npm run dev
```

### `src/api/hackernews.ts`

```typescript
const BASE = 'https://hacker-news.firebaseio.com/v0';

export interface HNStory {
  id: number;
  title: string;
  by: string;           // author
  score: number;
  url?: string;         // may be absent for text posts
  text?: string;        // HTML text for text-only posts
  descendants: number;  // comment count
  time: number;         // unix timestamp
  type: 'story' | 'job' | 'ask' | 'show';
}

// Fetch the top 500 story IDs
export async function fetchTopStoryIds(): Promise<number[]> {
  const res = await fetch(`${BASE}/topstories.json`);
  return res.json();
}

// Fetch one story by ID
export async function fetchStory(id: number): Promise<HNStory> {
  const res = await fetch(`${BASE}/item/${id}.json`);
  return res.json();
}

// Fetch a page of stories (ids already sliced)
export async function fetchStories(ids: number[]): Promise<HNStory[]> {
  // Parallel fetch — all stories in one "page"
  const stories = await Promise.all(ids.map(fetchStory));
  return stories.filter(Boolean); // remove nulls (deleted stories)
}
```

### `src/hooks/useHNFeed.ts`

```typescript
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { fetchTopStoryIds, fetchStories, HNStory } from '../api/hackernews';

const PAGE_SIZE = 30;

export function useHNFeed() {
  // Step 1: Get all 500 IDs (cheap — one small JSON file)
  const { data: allIds } = useQuery({
    queryKey: ['hn-top-ids'],
    queryFn: fetchTopStoryIds,
    staleTime: 5 * 60 * 1000, // cache for 5 minutes
  });

  // Step 2: Fetch pages of stories as user scrolls
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['hn-stories'],
    queryFn: ({ pageParam = 0 }) => {
      if (!allIds) return [];
      const pageIds = allIds.slice(pageParam * PAGE_SIZE, (pageParam + 1) * PAGE_SIZE);
      return fetchStories(pageIds);
    },
    getNextPageParam: (lastPage, allPages) => {
      const nextPage = allPages.length;
      const totalPages = Math.ceil((allIds?.length ?? 0) / PAGE_SIZE);
      return nextPage < totalPages ? nextPage : undefined;
    },
    enabled: !!allIds,
    initialPageParam: 0,
  });

  // Flatten pages into a single array
  const stories: HNStory[] = data?.pages.flat() ?? [];

  return { stories, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading };
}
```

### `src/components/StoryCard.tsx`

```tsx
import { HNStory } from '../api/hackernews';

interface Props {
  story: HNStory;
  rank: number;
}

function timeAgo(unix: number): string {
  const seconds = Math.floor(Date.now() / 1000) - unix;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function StoryCard({ story, rank }: Props) {
  const domain = story.url ? new URL(story.url).hostname.replace('www.', '') : null;

  return (
    <div style={{
      display: 'flex',
      gap: 12,
      padding: '12px 16px',
      borderBottom: '1px solid #e5e7eb',
      background: '#fff',
    }}>
      {/* Rank */}
      <div style={{ fontSize: 14, color: '#9ca3af', minWidth: 28, textAlign: 'right', paddingTop: 2 }}>
        {rank}.
      </div>

      {/* Content */}
      <div style={{ flex: 1 }}>
        {/* Title + domain */}
        <div style={{ marginBottom: 4 }}>
          <a
            href={story.url ?? `https://news.ycombinator.com/item?id=${story.id}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: 15, fontWeight: 500, color: '#111827', textDecoration: 'none' }}
          >
            {story.title}
          </a>
          {domain && (
            <span style={{ marginLeft: 6, fontSize: 12, color: '#9ca3af' }}>
              ({domain})
            </span>
          )}
        </div>

        {/* Text preview for Ask HN / text posts — THIS makes height variable */}
        {story.text && (
          <div
            style={{ fontSize: 13, color: '#4b5563', marginBottom: 6, lineHeight: 1.5 }}
            dangerouslySetInnerHTML={{
              __html: story.text.slice(0, 300) + (story.text.length > 300 ? '...' : ''),
            }}
          />
        )}

        {/* Metadata row */}
        <div style={{ fontSize: 12, color: '#6b7280', display: 'flex', gap: 12 }}>
          <span>▲ {story.score}</span>
          <span>by {story.by}</span>
          <span>{timeAgo(story.time)}</span>
          <a
            href={`https://news.ycombinator.com/item?id=${story.id}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#6b7280' }}
          >
            {story.descendants ?? 0} comments
          </a>
          {story.type !== 'story' && (
            <span style={{ padding: '0 6px', background: '#fef3c7', color: '#92400e', borderRadius: 4 }}>
              {story.type.toUpperCase()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
```

### `src/components/LoadingRow.tsx`

```tsx
// Skeleton placeholder while story is being fetched
export function LoadingRow() {
  return (
    <div style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb' }}>
      <div style={{ display: 'flex', gap: 12 }}>
        <div style={{ width: 24, height: 16, background: '#f3f4f6', borderRadius: 4 }} />
        <div style={{ flex: 1 }}>
          <div style={{ height: 16, background: '#f3f4f6', borderRadius: 4, marginBottom: 8, width: '70%' }} />
          <div style={{ height: 12, background: '#f3f4f6', borderRadius: 4, width: '40%' }} />
        </div>
      </div>
    </div>
  );
}
```

### `src/components/HNFeed.tsx` — The Virtualized Feed

```tsx
import { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useHNFeed } from '../hooks/useHNFeed';
import { StoryCard } from './StoryCard';
import { LoadingRow } from './LoadingRow';

const LOAD_MORE_THRESHOLD = 5; // Load more when within 5 items of end

export function HNFeed() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { stories, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useHNFeed();

  // Total rows = stories + 1 loading indicator row at bottom
  const rowCount = hasNextPage ? stories.length + 1 : stories.length;

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,

    // Smart estimate by story type
    // Stories with text are taller; regular link stories are shorter
    estimateSize: (index) => {
      const story = stories[index];
      if (!story) return 60;           // loading row
      if (story.text) return 120;      // Ask HN / text posts are taller
      return 70;                        // regular link story
    },

    overscan: 8,
  });

  // Detect when user is near the bottom → load next page
  useEffect(() => {
    const lastItem = virtualizer.getVirtualItems().at(-1);
    if (!lastItem) return;

    const nearEnd = lastItem.index >= stories.length - LOAD_MORE_THRESHOLD;
    if (nearEnd && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [virtualizer.getVirtualItems(), stories.length, hasNextPage, isFetchingNextPage]);

  if (isLoading) {
    return (
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        {Array.from({ length: 10 }).map((_, i) => <LoadingRow key={i} />)}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', fontFamily: 'system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ padding: '16px', background: '#ff6600', color: 'white', fontWeight: 700, fontSize: 18, display: 'flex', gap: 12 }}>
        <span>Y</span>
        <span>Hacker News — Top Stories</span>
      </div>

      {/* Virtualized scroll container */}
      <div
        ref={scrollRef}
        style={{ height: 'calc(100vh - 56px)', overflowY: 'auto' }}
      >
        {/* Inner container — full virtual height */}
        <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>

          {virtualizer.getVirtualItems().map((virtualItem) => {
            const isLoaderRow = virtualItem.index >= stories.length;
            const story = stories[virtualItem.index];

            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}        // Required for measureElement
                ref={virtualizer.measureElement}      // ResizeObserver target
                style={{
                  position: 'absolute',
                  top: virtualItem.start,
                  width: '100%',
                }}
              >
                {isLoaderRow ? (
                  <LoadingRow />
                ) : (
                  <StoryCard story={story} rank={virtualItem.index + 1} />
                )}
              </div>
            );
          })}

        </div>
      </div>
    </div>
  );
}
```

### `src/App.tsx`

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HNFeed } from './components/HNFeed';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HNFeed />
    </QueryClientProvider>
  );
}
```

### What Happens at Runtime

```
1. App loads → fetchTopStoryIds() returns [39521, 38902, ...] (500 IDs)

2. First page: fetchStories([39521, 38902, ..., 39550]) → 30 stories

3. Virtualizer renders:
   - Estimates all 31 rows at ~70px each
   - getTotalSize() = 31 × 70 = 2,170px
   - Viewport height = e.g. 800px → shows ~11 items

4. ResizeObserver fires for each rendered item:
   - story[0]: estimated 70px → actual 65px  (short title)
   - story[2]: estimated 70px → actual 118px (Ask HN with text)
   - story[7]: estimated 70px → actual 73px  (long title, 2 lines)
   → Offsets recalculate, container height adjusts

5. User scrolls to bottom of first page:
   → lastItem.index = 26 >= 30 - 5 → triggers fetchNextPage()
   → 30 more stories arrive, rowCount = 61
   → Virtualizer adds them automatically

6. Scroll continues — only 15 DOM nodes at any time
   → 500 stories loaded, still 60fps
```

---

## 6. Infinite Scroll with Virtualization

The pattern from the HN project, explained in isolation:

```tsx
// The key insight: virtualizer.getVirtualItems() tells you
// which items are currently visible. Check if we're near the end.

function useInfiniteScroll(virtualizer, totalLoaded, fetchMore, hasMore) {
  useEffect(() => {
    const visibleItems = virtualizer.getVirtualItems();
    if (visibleItems.length === 0) return;

    const lastVisibleIndex = visibleItems.at(-1).index;

    // "Within 10 items of the end" → start fetching
    if (lastVisibleIndex >= totalLoaded - 10 && hasMore) {
      fetchMore();
    }
  }, [virtualizer.getVirtualItems()]); // re-runs on every scroll
}
```

### Loading States Mid-List

```tsx
// If data is loading for a specific index, show skeleton
{virtualizer.getVirtualItems().map((virtualItem) => {
  const item = data[virtualItem.index];

  return (
    <div
      key={virtualItem.key}
      data-index={virtualItem.index}
      ref={virtualizer.measureElement}
      style={{ position: 'absolute', top: virtualItem.start, width: '100%' }}
    >
      {item ? <RealItem item={item} /> : <SkeletonItem />}
    </div>
  );
})}
```

---

## 7. Reverse Scroll (Chat Apps)

Chat apps scroll from **bottom to top** (newest message at bottom). This requires special handling.

```tsx
export function ChatFeed({ messages }: { messages: Message[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: (index) => {
      // Estimate based on message type
      const msg = messages[index];
      if (msg.type === 'image') return 250;
      if (msg.type === 'code') return 150;
      return 60;
    },
    overscan: 10,
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (isAtBottom) {
      virtualizer.scrollToIndex(messages.length - 1, { behavior: 'smooth' });
    }
  }, [messages.length]);

  // Track whether user has scrolled away from bottom
  function handleScroll(e: React.UIEvent<HTMLDivElement>) {
    const el = e.currentTarget;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setIsAtBottom(distanceFromBottom < 50);
  }

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      style={{ height: '100vh', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}
    >
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            data-index={virtualItem.index}
            ref={virtualizer.measureElement}
            style={{ position: 'absolute', top: virtualItem.start, width: '100%' }}
          >
            <ChatMessage message={messages[virtualItem.index]} />
          </div>
        ))}
      </div>

      {/* Scroll-to-bottom button */}
      {!isAtBottom && (
        <button
          onClick={() => virtualizer.scrollToIndex(messages.length - 1, { behavior: 'smooth' })}
          style={{
            position: 'fixed', bottom: 80, right: 24,
            background: '#6366f1', color: 'white',
            border: 'none', borderRadius: '50%',
            width: 44, height: 44, cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          ↓
        </button>
      )}
    </div>
  );
}
```

### Scroll Anchor Problem

When you load older messages at the **top** (load more history), the list jumps because inserting items at index 0 shifts everything down.

```tsx
// Solution: save scroll position before prepend, restore after
async function loadOlderMessages() {
  const el = scrollRef.current;
  if (!el) return;

  const scrollHeightBefore = el.scrollHeight;
  const scrollTopBefore = el.scrollTop;

  await prependMessages();

  // After React re-renders, restore relative position
  requestAnimationFrame(() => {
    const scrollHeightAfter = el.scrollHeight;
    el.scrollTop = scrollTopBefore + (scrollHeightAfter - scrollHeightBefore);
  });
}
```

---

## 8. Horizontal Virtualization

```tsx
// Horizontal scrolling — same API, different axis
const COLUMN_WIDTH = 200;

export function HorizontalList({ items }: { items: string[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => COLUMN_WIDTH,
    horizontal: true, // ← only difference from vertical
    overscan: 3,
  });

  return (
    <div
      ref={scrollRef}
      style={{
        width: '100%',
        overflowX: 'auto',   // horizontal scroll
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{ width: virtualizer.getTotalSize(), position: 'relative', height: 120 }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            data-index={virtualItem.index}
            ref={virtualizer.measureElement}
            style={{
              position: 'absolute',
              left: virtualItem.start,   // ← left, not top
              height: '100%',
              width: COLUMN_WIDTH,
            }}
          >
            <div style={{ padding: 16, background: '#f9fafb', border: '1px solid #e5e7eb', height: '100%', margin: '0 4px', borderRadius: 8 }}>
              {items[virtualItem.index]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 9. 2D Grid Virtualization

For image galleries, spreadsheets, kanban boards:

```tsx
const COLUMN_COUNT = 4;
const ROW_HEIGHT = 200;
const COLUMN_WIDTH = 250;

export function VirtualGrid({ items }: { items: ImageItem[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const rowCount = Math.ceil(items.length / COLUMN_COUNT);

  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 2,
  });

  const columnVirtualizer = useVirtualizer({
    horizontal: true,
    count: COLUMN_COUNT,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => COLUMN_WIDTH,
    overscan: 1,
  });

  return (
    <div
      ref={scrollRef}
      style={{ height: 600, width: '100%', overflow: 'auto' }}
    >
      <div
        style={{
          height: rowVirtualizer.getTotalSize(),
          width: columnVirtualizer.getTotalSize(),
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((row) =>
          columnVirtualizer.getVirtualItems().map((col) => {
            const itemIndex = row.index * COLUMN_COUNT + col.index;
            const item = items[itemIndex];
            if (!item) return null;

            return (
              <div
                key={`${row.index}-${col.index}`}
                style={{
                  position: 'absolute',
                  top: row.start,
                  left: col.start,
                  width: COLUMN_WIDTH,
                  height: ROW_HEIGHT,
                  padding: 4,
                }}
              >
                <img
                  src={item.url}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8 }}
                />
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
```

---

## 10. System Design Concepts

### 10.1 Windowing vs. Pagination vs. Virtualization

```
PAGINATION
─────────────────────────────────────
User sees:   Page 1 of 500  [< >]
DOM nodes:   20 (one page)
UX:          Discrete jumps — user loses context when turning pages
Best for:    Search results, admin tables, any context where position matters less

INFINITE SCROLL (without virtualization)
─────────────────────────────────────
User sees:   Continuous feed, scrolls down
DOM nodes:   Grows unboundedly — 20 → 40 → 60 → ... → 2000
UX:          Smooth, but degrades over time
Best for:    Short sessions where user won't scroll far

VIRTUALIZATION (windowing)
─────────────────────────────────────
User sees:   Continuous feed, scrolls down
DOM nodes:   Always ~15–30, regardless of total items
UX:          Smooth, stays smooth forever
Best for:    Long sessions, large datasets, high-frequency updates
```

### 10.2 Where to Put the Scroll Container

The `getScrollElement` must return the element with `overflow: auto/scroll`. Common mistakes:

```
WRONG: Attaching to document.body
  → The entire page scrolls, not your list component
  → Virtualizer cannot read scrollTop correctly

WRONG: Attaching to a parent without overflow: auto
  → scrollTop is always 0 → library renders nothing

CORRECT:
  <div ref={scrollRef} style={{ overflow: 'auto', height: 600 }}>
    <div style={{ height: getTotalSize(), position: 'relative' }}>
      {items}
    </div>
  </div>
```

### 10.3 Overscan — The Buffer Zone

```
Viewport: items 10–20 visible

With overscan=5:
  Rendered: items 5–25 (5 above, 5 below viewport)

  Items 5–9:  invisible (above viewport), but in DOM
  Items 10–20: visible
  Items 21–25: invisible (below viewport), but in DOM

Why it matters:
  User fast-scrolls down → items 21–25 are already rendered
  → No blank flash while new items mount
  → Tradeoff: more DOM nodes for smoother experience
```

Recommended overscan values:

| Use case | Overscan |
|---|---|
| Static list | 3–5 |
| Infinite scroll | 8–10 |
| Fast-scrolling list (social feed) | 10–15 |
| Chat (bidirectional scroll) | 10–15 |

### 10.4 The estimateSize Accuracy Trade-off

```
estimateSize too low (e.g., 40px when real is 200px):
  → Container height = 10,000 × 40 = 400,000px  (underestimate)
  → As items measure in, container grows
  → Scrollbar thumb shrinks suddenly (jarring)
  → Scroll position may jump

estimateSize too high (e.g., 300px when real is 80px):
  → Container height = 10,000 × 300 = 3,000,000px  (overestimate)
  → As items measure in, container shrinks
  → Scrollbar thumb grows (less jarring — preferred)
  → More whitespace initially

Rule of thumb: slightly overestimate
  → "scrollbar shrinks" is less disorienting than "scrollbar grows"
```

### 10.5 Scroll Restoration

When user navigates away and back, you want to restore their scroll position:

```typescript
// Save on unmount
useEffect(() => {
  return () => {
    const position = scrollRef.current?.scrollTop ?? 0;
    sessionStorage.setItem(`scroll-${listId}`, String(position));
  };
}, [listId]);

// Restore on mount
useEffect(() => {
  const saved = sessionStorage.getItem(`scroll-${listId}`);
  if (saved && scrollRef.current) {
    scrollRef.current.scrollTop = Number(saved);
  }
}, [listId]);
```

But with variable heights, this is imprecise — positions change as items measure in. For exact scroll restoration, store the **index + offset within item** instead of raw `scrollTop`.

### 10.6 Dynamic Item Updates (Real-time Data)

When a list item updates (e.g., a message gets a reaction), its height may change:

```
Message at index 47: 60px (no reactions)
User adds 3 reactions → message becomes 92px

ResizeObserver fires:
  → heightCache[47] = 92 (was 60)
  → Rebuild prefix sum from index 47
  → All items 48+ shift down by 32px
  → Container height increases by 32px
  → Current scroll position is preserved
```

The virtualizer handles this automatically via `measureElement`. You don't need to manually notify it.

### 10.7 Measuring Performance

Key metrics to measure in Chrome DevTools:

```
1. Long Tasks (> 50ms) on scroll
   → Open Performance panel, record scroll, look for red bars

2. Layout thrashing
   → Look for purple "Layout" blocks during scroll
   → Cause: reading offsetHeight inside a scroll handler

3. DOM node count
   → Open Elements panel, count items in your virtual container
   → Should stay constant while scrolling

4. Memory
   → Open Memory panel, take heap snapshot before/after scrolling
   → Should not grow proportionally with items scrolled
```

### 10.8 When NOT to Virtualize

```
Rule of thumb: virtualize when items > 500 AND content is dynamic

DON'T virtualize:
  • Dropdowns (< 200 items, user closes quickly)
  • Paginated tables (pagination already limits DOM)
  • Static pages (the list exists once, never scrolled repeatedly)
  • Lists that anchor to specific items (virtualization + anchoring is complex)

DO virtualize:
  • Chat history (thousands of messages, grows in real-time)
  • Social feeds (infinite content, variable heights)
  • File explorers (thousands of files in flat list)
  • Log viewers (millions of lines)
  • IDE autocomplete (filters large lists, must be instant)
```

---

## 11. Performance Profiling Checklist

Before shipping a virtualized list, verify:

```
□ DOM count stays constant during scroll
  → Inspect Elements panel while scrolling fast

□ No layout thrashing in scroll handler
  → Performance panel: no purple blocks synchronous with scroll events

□ estimateSize within 30% of real size
  → Add a console.warn if measured differs from estimate by > 100px

□ ResizeObserver does not fire on every frame
  → Should fire only when item height actually changes

□ Unmounted items have their ResizeObserver disconnected
  → Check in component cleanup / useEffect return

□ `data-index` attribute is present on all measured elements
  → Without it, measureElement silently fails

□ overscan is not too large
  → Overscan of 50+ defeats the purpose of virtualization

□ No key collisions
  → Each virtualItem.key must be unique and stable

□ Scroll container has a fixed height
  → Height: 'auto' on scroll container breaks the virtualizer
```

---

## 12. Common Bugs and Fixes

### Bug 1: Blank list / nothing renders

```tsx
// WRONG — container has no height, scrollTop is always 0
<div ref={scrollRef} style={{ overflowY: 'auto' }}>

// CORRECT — explicit height required
<div ref={scrollRef} style={{ overflowY: 'auto', height: 600 }}>
// or
<div ref={scrollRef} style={{ overflowY: 'auto', height: '100vh' }}>
```

### Bug 2: Items overlap each other

```tsx
// WRONG — setting height on the item div conflicts with measureElement
<div
  data-index={virtualItem.index}
  ref={virtualizer.measureElement}
  style={{ position: 'absolute', top: virtualItem.start, height: virtualItem.size }}
  // ↑ Don't set height! Let content determine it for variable lists.
>

// CORRECT — no height on the positioned div
<div
  data-index={virtualItem.index}
  ref={virtualizer.measureElement}
  style={{ position: 'absolute', top: virtualItem.start, width: '100%' }}
>
```

### Bug 3: `measureElement` not working (heights stay as estimate)

```tsx
// WRONG — missing data-index attribute
<div ref={virtualizer.measureElement}>

// CORRECT — data-index is how the library identifies which item was measured
<div data-index={virtualItem.index} ref={virtualizer.measureElement}>
```

### Bug 4: Scroll jumps when new items load at top

```tsx
// Cause: prepending items shifts all index-based positions
// Fix: use stable IDs as keys instead of index
{virtualizer.getVirtualItems().map((virtualItem) => (
  <div
    key={items[virtualItem.index].id}  // ← stable ID, not virtualItem.index
    data-index={virtualItem.index}
    ref={virtualizer.measureElement}
    ...
  >
```

### Bug 5: Memory leak — ResizeObserver not disconnected

```tsx
// @tanstack/react-virtual handles this for you via measureElement.
// If you attach your OWN ResizeObserver, disconnect in cleanup:

useEffect(() => {
  const observer = new ResizeObserver(callback);
  observer.observe(element);
  return () => observer.disconnect(); // ← required
}, [element]);
```

### Bug 6: List re-renders on every scroll event

```tsx
// WRONG — inline object recreated on every scroll, triggers full re-render
<VirtualItem style={{ position: 'absolute', top: virtualItem.start }} />

// CORRECT — pass primitives, or memoize the item component
const MemoizedItem = React.memo(VirtualItem);
<MemoizedItem top={virtualItem.start} index={virtualItem.index} />
```

---

## Quick Reference

```
useVirtualizer({
  count,           // number of items
  getScrollElement,// () => scrollRef.current
  estimateSize,    // (index) => estimated height in px
  overscan,        // extra items above/below (default 1)
  horizontal,      // true for horizontal scroll
  measureElement,  // custom measure function (optional)
})

virtualizer.getVirtualItems()  // items currently in DOM
virtualizer.getTotalSize()     // total height of all items (for inner container)
virtualizer.measureElement     // ref callback — attaches ResizeObserver
virtualizer.scrollToIndex(i, { behavior, align })

virtualItem.index  // data array index
virtualItem.start  // top (or left) pixel offset
virtualItem.size   // current measured height
virtualItem.key    // stable React key
```

---

## 13. Browser Rendering Pipeline — How the Screen Actually Updates

Understanding this is what separates developers who fix jank from those who guess at it.

### Two Separate Pipelines (Most People Confuse These)

#### Pipeline 1: Initial Page Load (runs once)

This is the one you learned first — HTML → CSS → JS:

```
Network bytes arrive
      ↓
HTML Parser → DOM tree         (all your divs, p, img nodes)
      ↓
CSS Parser  → CSSOM tree       (all style rules)
      ↓  ← parser PAUSES here if it hits <script> — why scripts go at bottom
JS executes → may modify DOM/CSSOM
      ↓
Browser: DOM + CSSOM → Render Tree   (only visible nodes with computed styles)
      ↓
Layout  → calculate exact pixel positions and sizes of everything  (first reflow)
      ↓
Paint   → fill pixels into bitmaps (layer by layer)
      ↓
Composite → send layers to GPU → screen
```

This runs exactly once on first load. HTML does come first here — you are correct about the order.

#### Pipeline 2: Per-Frame Update Loop (runs up to 60 times/second)

This is what runs every time anything changes — scroll, animation, user click, JS update.
This is what `JavaScript → Style → Layout → Paint → Composite` refers to:

```
User clicks button / scroll fires / animation frame ticks
      ↓
JavaScript → your code runs, modifies DOM or styles
      ↓
Style      → browser recalculates which CSS rules apply to changed elements
      ↓
Layout     → recalculates positions and sizes ("reflow")
      ↓
Paint      → redraws affected pixels ("repaint")
      ↓
Composite  → merges layers → GPU → screen
```

The browser has ~16ms to complete all of this for 60fps. If any step takes longer, a frame is dropped — the user sees jank.

JavaScript is listed first here because it is the **trigger** — your code runs, then the browser responds.

---

## 14. Reflow and Repaint — The Expensive Steps

### What is Reflow (Layout Recalculation)?

Reflow happens whenever the browser needs to recalculate the **geometry** of elements — their size, position, and relationship to each other.

```javascript
// ALL of these trigger reflow:
element.style.width = '200px'         // size changed
element.style.height = '100px'        // size changed
element.style.margin = '20px'         // spacing changed
element.style.padding = '10px'        // spacing changed
element.style.fontSize = '18px'       // text reflows → affects line wrapping
element.style.display = 'none'        // removes from layout entirely
element.style.position = 'absolute'   // changes layout context
document.body.appendChild(newDiv)     // DOM structure changed
window.resized                        // viewport changed → everything recalculates
```

**Reflow is contagious.** Change a parent's width → all its children must recalculate:

```
div.container { width: 800px → 600px }
      ↓
All children ask: "how wide am I now?"
      ↓
All grandchildren ask the same
      ↓
...cascades down the entire subtree
```

Change something at the root (`<body>`) → the entire page reflows.

### What is Repaint?

Repaint happens when you change a **visual property that doesn't affect geometry**.
The layout is already correct — only pixels need to be redrawn.

```javascript
// These trigger repaint but NOT reflow:
element.style.color = 'red'
element.style.backgroundColor = '#eee'
element.style.visibility = 'hidden'   // hides but keeps space (unlike display:none)
element.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)'
element.style.outline = '2px solid blue'
element.style.borderColor = 'red'     // color only, not border-width
```

Repaint is cheaper than reflow — no geometry recalculation. But still costs because the browser must re-execute the paint algorithm for the affected region and upload new pixels to the GPU.

### Composite Only — The Cheapest Change

Some properties skip both Layout and Paint entirely:

```javascript
// These go straight to Composite — no CPU layout or paint work:
element.style.transform = 'translateX(100px)'
element.style.transform = 'scale(1.5)'
element.style.opacity = '0.5'
```

The browser promotes these elements to their own **GPU layer**. Changes to transform/opacity are handled entirely by the GPU — the CPU rendering pipeline is never involved.

```
Property Changed              Steps Executed
────────────────────────────────────────────────────────────────
width, height, margin, top    Style → Layout → Paint → Composite  (all 4, most expensive)
color, background, shadow     Style → ~~Layout~~ → Paint → Composite
transform, opacity            Style → ~~Layout~~ → ~~Paint~~ → Composite  (cheapest)
```

---

## 15. GPU vs CPU — Why transform is Fast

### The Layer Model

When you use `transform` or `opacity`, the browser promotes that element to its own **GPU layer** — like a separate transparent sheet floating above the page.

```
Without transform (everything on one CPU-painted bitmap):

  ┌─────────────────────────────────┐
  │  Page bitmap (CPU-painted)      │
  │                                 │
  │  [item 1]                       │
  │  [item 2]  ← you change height  │  ← CPU must repaint this region
  │  [item 3]                       │
  └─────────────────────────────────┘

  Changing item 2 = CPU repaints item 2 AND surrounding pixels every frame
```

```
With transform (element gets its own GPU layer):

  ┌─────────────────────────────────┐  ← Layer 1: rest of page (CPU-painted once, never redraws)
  │  [item 1]                       │
  │  [item 2 original position]     │
  │  [item 3]                       │
  └─────────────────────────────────┘
             +
  ┌──────────────┐  ← Layer 2: item 2's own GPU layer (pre-painted once, just moved)
  │   [item 2]   │
  └──────────────┘  ← GPU slides this sheet. Zero CPU work per frame.
```

The page bitmap never changes. The GPU just repositions the sheet.

### CPU vs GPU at the Job Level

```
CPU (what it's good at):
  - Complex logic, branching, sequential work
  - Layout math (recursive geometry recalculation)
  - Parsing, decoding, compression
  - Few cores (4–16), each very powerful

GPU (what it's good at):
  - The same simple operation on thousands of pixels at once
  - Moving, scaling, blending pixel layers
  - Thousands of cores (1,000–10,000+), each simple
  - Designed specifically for: "take this bitmap, move it 70px right, draw it"
```

Asking the CPU to composite layers (move pixel sheets) is like asking a professor to sort 10,000 cards by hand. Asking the GPU is like giving each card to a different student — done in parallel, instantly.

### Side by Side: height vs transform in an animation

```javascript
// BAD: height animation — CPU does full pipeline 60x/second
function animate() {
  element.style.height = currentHeight + 'px'; // triggers Layout + Paint + Composite
  requestAnimationFrame(animate);
}

// Each frame:
//   CPU: Style recalc → Layout (recursive) → Paint (redraw pixels) → hand to GPU
//   GPU: Composite
//   Cost per frame: ~8–12ms on mid-range phone → drops below 60fps → jank visible
```

```javascript
// GOOD: transform animation — GPU does one step 60x/second
function animate() {
  element.style.transform = `scaleY(${scale})`; // skips Layout + Paint entirely
  requestAnimationFrame(animate);
}

// Each frame:
//   CPU: Style recalc (minimal)
//   GPU: Composite (scale the pre-painted layer)
//   Cost per frame: ~0.3ms → stable 60fps → perfectly smooth
```

### What if the Laptop Has No Dedicated GPU?

Every modern laptop — even the cheapest — has some form of GPU:

```
Dedicated GPU   → separate chip (NVIDIA RTX, AMD Radeon)
                  high performance, gaming/workstation laptops

Integrated GPU  → built into the CPU die (Intel Iris Xe, AMD Radeon Graphics,
                  Apple M-series GPU cores)
                  used by most laptops, low power

Software GPU    → CPU simulates GPU in software (Mesa llvmpipe, SwiftShader)
                  used only in: headless servers, VMs, ancient hardware,
                  GPU driver crash fallback
```

If a browser genuinely cannot access any GPU (software rendering mode):

```
transform/opacity change:
  → Still skips Layout and Paint ✓
  → Composite step runs on CPU in software (slower than GPU, but still runs)
  → Still much faster than triggering Layout + Paint per frame

Result: transform is still the correct choice
        It just gets a smaller advantage (2–3x faster instead of 10–20x)
```

You can check if your browser is in software rendering mode:

```
Chrome: chrome://gpu
  Look for: "Graphics Feature Status"
  "Canvas: Hardware accelerated" = GPU is working
  "Canvas: Software only"        = CPU fallback mode
```

### The Practical Rule

```
ONE reflow is fine
  → element.style.height = '200px' on a button click: totally OK
  → Happens once, costs one reflow, done

60 reflows per second is a disaster
  → element.style.height inside requestAnimationFrame: never do this
  → CPU doing recursive geometry math 60x/second = guaranteed jank

So:
  Static change (once)  → height/width/margin is fine
  Animation (60fps)     → transform/opacity always, no exceptions
```

---

## 16. Layout Thrashing — Reading and Writing in a Loop

Layout thrashing is what happens when you force the browser to run layout many times per frame by interleaving reads and writes.

### Why Reading Forces a Synchronous Reflow

The browser is lazy — it queues writes and applies them all at once just before the next paint. This is an optimization: batch 10 style changes into one layout pass instead of 10.

```
WRITE = "sticky note — do this later"  → queued, deferred, cheap
READ  = "I need the answer RIGHT NOW"  → forces the browser to process all queued notes first
```

The browser cannot return a stale `offsetHeight`. If layout is dirty (a write happened), it must run layout synchronously before it can answer your read — even mid-JavaScript-execution.

### The Bad Loop — Step by Step

```javascript
const items = document.querySelectorAll('.item'); // 3 items for clarity

// ── ITERATION 1 ──
const height = items[0].offsetHeight;
// Browser: "offsetHeight asked. Layout is dirty? No (nothing written yet).
//           Run layout to compute fresh values."
//           → REFLOW #1 executes
//           → Returns 50

items[0].style.height = '60px';
// Browser: "Noted. I'll apply this. Layout is now dirty." → queued, not run yet

// ── ITERATION 2 ──
const height = items[1].offsetHeight;
// Browser: "offsetHeight asked. Layout is dirty (from the write above).
//           I MUST run layout before I can answer."
//           → REFLOW #2 executes (includes the '60px' write from iteration 1)
//           → Returns 80

items[1].style.height = '90px';
// → Layout dirty again

// ── ITERATION 3 ──
const height = items[2].offsetHeight;
// → REFLOW #3 executes

items[2].style.height = '70px';
// → Layout dirty (no more reads, so browser defers to next frame)

// Total: 3 reflows for 3 items → 1000 reflows for 1000 items → page freezes
```

### The Fix — Batch Reads Before Writes

```javascript
const items = document.querySelectorAll('.item');

// ── PHASE 1: ALL READS ──
const h0 = items[0].offsetHeight;
// Browser: "Layout clean. Run layout once."  → REFLOW #1
// Returns 50

const h1 = items[1].offsetHeight;
// Browser: "Layout still clean — no writes since last reflow.
//           Answer is already computed."  → NO REFLOW, returns from cache
// Returns 80

const h2 = items[2].offsetHeight;
// Browser: "Still clean."  → NO REFLOW
// Returns 60

// ── PHASE 2: ALL WRITES ──
items[0].style.height = (h0 + 10) + 'px';  // layout dirty (deferred)
items[1].style.height = (h1 + 10) + 'px';  // still dirty (deferred)
items[2].style.height = (h2 + 10) + 'px';  // still dirty (deferred)

// No more reads → browser batches all 3 writes into one reflow at frame end
// → REFLOW #2 (the only write reflow)

// Total: 2 reflows for any number of items
```

### Properties That Force a Synchronous Reflow When Read

Avoid reading these inside loops or animation callbacks:

```javascript
// Reading any of these flushes pending layout immediately:
element.offsetWidth / offsetHeight / offsetTop / offsetLeft
element.clientWidth / clientHeight / clientTop / clientLeft
element.scrollWidth / scrollHeight / scrollTop / scrollLeft
element.getBoundingClientRect()
element.getComputedStyle()
window.innerWidth / innerHeight
document.documentElement.clientWidth
```

### Cache Geometry Reads Outside Animation Loops

```javascript
// BAD — forces reflow on every frame (60x/second)
function animate() {
  const w = container.offsetWidth;      // READ: layout flush every frame
  element.style.width = w * 0.5 + 'px'; // WRITE: layout dirty again
  requestAnimationFrame(animate);
}

// GOOD — read once, cache, use cached value inside loop
const containerWidth = container.offsetWidth; // READ once: one reflow here

function animate() {
  // No read inside the loop — no reflow per frame
  element.style.width = containerWidth * progress + 'px';
  requestAnimationFrame(animate);
}
```

```
BAD:  Frame 1 → READ → reflow → WRITE → paint
      Frame 2 → READ → reflow → WRITE → paint   (60 reflows/second)
      Frame 3 → READ → reflow → WRITE → paint

GOOD: Setup    → READ → reflow (once)
      Frame 1  → WRITE → paint
      Frame 2  → WRITE → paint                   (0 reflows/second)
      Frame 3  → WRITE → paint
```

### The Mental Model in One Sentence

> Never put a read after a write inside a loop. Reads after writes force the browser to stop deferring and compute immediately — once per iteration.

---

---

## 17. Cursor-Based Pagination with Virtualization

### Offset Pagination vs Cursor Pagination

Before building anything, understand why offset pagination breaks at scale.

#### Offset Pagination (the naive approach)

```
GET /api/posts?page=3&limit=20
GET /api/posts?offset=60&limit=20
```

```
Problem 1: Page drift
  User is on page 3. Meanwhile, 5 new posts are added at the top.
  Page 3 now contains items 65-85 instead of 60-80.
  User sees duplicates (items 60-65 appeared on page 2 AND page 3).

Problem 2: Database cost
  SELECT * FROM posts ORDER BY created_at DESC OFFSET 10000 LIMIT 20
                                               ↑
  Database scans and discards 10,000 rows before returning 20.
  Cost grows linearly with page number. Page 500 = scan 10,000 rows.

Problem 3: No stable position
  You cannot bookmark "I was at item 6,432" — the number shifts as items are added/deleted.
```

#### Cursor Pagination (industry standard)

```
GET /api/posts?limit=20                           → first page
GET /api/posts?after=eyJpZCI6MTIzfQ&limit=20      → next page (cursor is opaque)
GET /api/posts?before=eyJpZCI6MTIzfQ&limit=20     → previous page
```

The cursor encodes the **position in the dataset** — usually a base64-encoded ID or timestamp. It is stable regardless of inserts.

```
How it works on the server:

cursor = base64("2024-01-15T10:30:00Z:id:8472")   // encodes timestamp + id

SELECT * FROM posts
WHERE (created_at, id) < (cursor.timestamp, cursor.id)   // keyset pagination
ORDER BY created_at DESC, id DESC
LIMIT 20

This is O(log n) with a compound index — same cost at page 1 or page 500.
```

---

### Cursor Pagination + Virtualization Architecture

The challenge: `@tanstack/react-virtual` needs a **total count** for `getTotalSize()`. Cursor pagination does not give you a total count upfront.

#### Strategy 1: Unknown Total — Append Only

Best for: social feeds, activity logs, anything where you only scroll down.

```typescript
// types.ts
interface CursorPage<T> {
  items: T[];
  nextCursor: string | null;   // null = no more pages
  prevCursor: string | null;
}

interface Post {
  id: string;
  content: string;
  author: string;
  createdAt: string;
}
```

```typescript
// api.ts
export async function fetchPosts(cursor?: string): Promise<CursorPage<Post>> {
  const params = new URLSearchParams({ limit: '20' });
  if (cursor) params.set('after', cursor);

  const res = await fetch(`/api/posts?${params}`);
  return res.json();
}
```

```typescript
// useCursorFeed.ts
import { useInfiniteQuery } from '@tanstack/react-query';
import { fetchPosts } from './api';

export function useCursorFeed() {
  const query = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam }) => fetchPosts(pageParam as string | undefined),

    // React Query calls this to know what cursor to pass next
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    getPreviousPageParam: (firstPage) => firstPage.prevCursor ?? undefined,

    initialPageParam: undefined,
  });

  // Flatten all pages into one array for the virtualizer
  const allItems = query.data?.pages.flatMap(page => page.items) ?? [];

  // Sentinel at the end: one extra "row" that triggers load-more
  const rowCount = query.hasNextPage ? allItems.length + 1 : allItems.length;

  return {
    items: allItems,
    rowCount,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
    isLoading: query.isLoading,
  };
}
```

```tsx
// CursorFeed.tsx
import { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useCursorFeed } from './useCursorFeed';
import { PostCard } from './PostCard';

const LOAD_AHEAD = 8; // fetch next page when within 8 items of end

export function CursorFeed() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const {
    items,
    rowCount,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useCursorFeed();

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 80,
    overscan: 5,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Trigger next page fetch when near the end
  useEffect(() => {
    const lastItem = virtualItems.at(-1);
    if (!lastItem) return;

    const isNearEnd = lastItem.index >= items.length - LOAD_AHEAD;
    if (isNearEnd && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [virtualItems, items.length, hasNextPage, isFetchingNextPage]);

  return (
    <div ref={scrollRef} style={{ height: '100vh', overflowY: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualItems.map((virtualItem) => {
          const isLoadingRow = virtualItem.index >= items.length;

          return (
            <div
              key={virtualItem.key}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              style={{ position: 'absolute', top: virtualItem.start, width: '100%' }}
            >
              {isLoadingRow ? (
                <div style={{ padding: 20, textAlign: 'center', color: '#9ca3af' }}>
                  Loading more...
                </div>
              ) : (
                <PostCard post={items[virtualItem.index]} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

#### Why `rowCount = items.length + 1` is the Trigger Pattern

```
items.length = 40  (2 pages of 20 loaded)
rowCount     = 41  (40 items + 1 phantom loading row)

Virtualizer renders items 32–41 when user scrolls to bottom.
Item 41 is the loading row — it appears in the viewport.

useEffect fires:
  lastItem.index = 40 >= 40 - 8 = 32 → true
  fetchNextPage() called
  → items becomes 60, rowCount becomes 61
  → virtualizer extends, loading row moves to position 61
  → 20 new PostCards render
```

---

### Handling Real-Time Inserts at the Top (New Items Arriving)

```
Problem:
  User has scrolled deep into the feed — viewing item #150.
  10 new items arrive at the top (items -10 to -1, prepended).
  All existing items shift down by 10 positions.
  User's scroll position is now pointing at item #140 instead of #150.
  Visual content JUMPS — very disorienting.

Solution: Scroll Anchoring
  Before inserting, record: "I am at item #150, which is at scrollTop = 12,400px"
  After inserting, find item #150 again and scroll back to it.
```

```typescript
function usePrependAnchor(scrollRef: React.RefObject<HTMLDivElement>) {
  const anchorRef = useRef<{ scrollHeight: number; scrollTop: number } | null>(null);

  function captureAnchor() {
    const el = scrollRef.current;
    if (!el) return;
    anchorRef.current = {
      scrollHeight: el.scrollHeight,
      scrollTop: el.scrollTop,
    };
  }

  function restoreAnchor() {
    const el = scrollRef.current;
    if (!el || !anchorRef.current) return;

    // How much did scrollHeight grow? That's how much we need to compensate.
    const delta = el.scrollHeight - anchorRef.current.scrollHeight;
    el.scrollTop = anchorRef.current.scrollTop + delta;
    anchorRef.current = null;
  }

  return { captureAnchor, restoreAnchor };
}

// Usage:
async function loadNewerMessages() {
  captureAnchor();        // save position BEFORE new items arrive
  await prependItems();   // React re-renders with new items at top
  // requestAnimationFrame waits for the DOM to reflect the new render
  requestAnimationFrame(restoreAnchor);  // restore relative position
}
```

---

## 18. Memory Management for Large Datasets

### The Problem DOM Virtualization Alone Does NOT Solve

DOM virtualization keeps the DOM small. But your JavaScript **data array** still grows:

```
User scrolls through 10,000 items.
DOM nodes: always 15 (virtualization working correctly ✓)
Memory:    items array = 10,000 objects × ~500 bytes = ~5MB

User scrolls through 100,000 items.
DOM nodes: still 15 ✓
Memory:    items array = 100,000 × ~500 bytes = ~50MB ← growing problem

After 1M items:
Memory:    500MB → browser tab crashes on mobile
```

You need to virtualize **data in memory** too, not just DOM nodes.

### Strategy 1: Page Eviction — Sliding Window of Pages

Keep only N pages in memory. Evict the oldest when adding new ones.

```typescript
// useWindowedPages.ts

const MAX_PAGES_IN_MEMORY = 5; // keep 5 pages = 5 × 20 = 100 items max
const PAGE_SIZE = 20;

interface WindowState {
  pages: Map<number, Post[]>;   // pageNumber → items
  startPage: number;            // lowest page in memory
  endPage: number;              // highest page in memory
}

function useWindowedPages() {
  const [window, setWindow] = useState<WindowState>({
    pages: new Map(),
    startPage: 0,
    endPage: -1,
  });

  async function loadPage(pageNumber: number, cursor: string) {
    const data = await fetchPosts(cursor);

    setWindow(prev => {
      const next = new Map(prev.pages);
      next.set(pageNumber, data.items);

      let { startPage, endPage } = prev;
      endPage = Math.max(endPage, pageNumber);

      // Evict oldest pages if over the limit
      while (next.size > MAX_PAGES_IN_MEMORY) {
        // Evict the page furthest from current view
        next.delete(startPage);
        startPage++;
      }

      return { pages: next, startPage, endPage };
    });
  }

  // Flatten only loaded pages into a sparse-aware array
  function getItems(): (Post | null)[] {
    const totalSlots = (window.endPage + 1) * PAGE_SIZE;
    const items: (Post | null)[] = new Array(totalSlots).fill(null);

    window.pages.forEach((pageItems, pageNumber) => {
      const offset = pageNumber * PAGE_SIZE;
      pageItems.forEach((item, i) => {
        items[offset + i] = item;
      });
    });

    return items;
  }

  return { getItems, loadPage, window };
}
```

```tsx
// In the virtualizer — handle null slots (evicted pages)
{virtualItems.map((virtualItem) => {
  const item = items[virtualItem.index];

  return (
    <div
      key={virtualItem.key}
      data-index={virtualItem.index}
      ref={virtualizer.measureElement}
      style={{ position: 'absolute', top: virtualItem.start, width: '100%' }}
    >
      {item === null ? (
        // Item was evicted from memory — show skeleton, reload on demand
        <EvictedItemSkeleton index={virtualItem.index} onVisible={() => reloadPage(virtualItem.index)} />
      ) : (
        <PostCard post={item} />
      )}
    </div>
  );
})}
```

### Strategy 2: React Query's Built-In Page Garbage Collection

React Query can automatically garbage collect pages not in use:

```typescript
const query = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPage,
  getNextPageParam: ...,
  initialPageParam: undefined,

  // Pages not accessed in 5 minutes are garbage collected from memory
  gcTime: 5 * 60 * 1000,

  // Data older than 2 minutes is considered stale and will refetch in background
  staleTime: 2 * 60 * 1000,

  // Only keep 10 pages maximum in the query cache
  maxPages: 10,  // React Query v5 feature
});
```

With `maxPages: 10`:

```
User scrolls down → pages 1, 2, 3, ... 10 load
User reaches page 11 → page 1 is evicted from query cache
User reaches page 12 → page 2 is evicted
...

Memory stays bounded: always max 10 × PAGE_SIZE items
```

### Strategy 3: Normalization — Store Items Once, Reference by ID

Without normalization, the same item exists multiple times if it appears in multiple pages:

```
Page 1: [post:123, post:456, post:789, ...]
Page 2: [post:456, post:999, ...]   ← post:456 appears in both (e.g. pinned post)

Memory: post:456 object stored twice
Updates: if post:456 is edited, you must update it in both pages
```

Normalization stores each item once:

```typescript
// Normalized store (using Zustand or Redux Toolkit)
interface NormalizedStore {
  // The single source of truth for all item data
  entities: {
    posts: Record<string, Post>;  // id → Post object
    users: Record<string, User>;
  };

  // Pages only store IDs — not the actual objects
  pages: {
    [cursor: string]: string[];   // cursor → [postId, postId, ...]
  };
}

// When fetching a page:
function normalizePage(rawItems: Post[]): void {
  rawItems.forEach(post => {
    store.entities.posts[post.id] = post;     // store object once
  });
  store.pages[cursor] = rawItems.map(p => p.id); // page stores only IDs
}

// When rendering:
const postIds = store.pages[currentCursor];
const posts = postIds.map(id => store.entities.posts[id]); // O(1) lookup

// When an item is updated (e.g., via websocket):
store.entities.posts['456'] = updatedPost;   // update once → everywhere reflects it
// All pages that reference post:456 see the update automatically
```

### Memory Budget Guidelines

```
List type           Items per object   Max items in memory   Strategy
────────────────────────────────────────────────────────────────────────
Social feed         ~500B/item         2,000                 maxPages: 10
Chat messages       ~300B/item         5,000                 Sliding window
File browser        ~200B/item         10,000                Sparse array
Log viewer          ~100B/item         50,000                Stream, never store all
Spreadsheet cells   ~50B/cell          100,000               Canvas render, no DOM
```

For log viewers and spreadsheets: do not store all items in a JS array at all. Stream from server and keep only the visible window — think of it as a database with a cursor, not an in-memory array.

---

## 19. Bidirectional Scroll — Jump to Any Position

This is the hardest virtualization problem. It appears in: Slack (jump to mentioned message), Discord (jump to unread), email clients (jump to date), GitHub (jump to line in diff).

### The Challenge

```
User clicks a notification: "You were mentioned in #general, 3 days ago"
→ Must jump to message from 3 days ago
→ Messages before that must be loadable by scrolling UP
→ Messages after that must be loadable by scrolling DOWN
→ Starting position is NOT the beginning or end of history

This requires:
  1. Load a page "around" the target message
  2. Place the viewport at that message
  3. Support loading more in BOTH directions
  4. Maintain scroll position as content is prepended above
```

### Implementation

```typescript
// useBidirectionalFeed.ts

interface FeedState {
  items: Message[];
  hasPrevious: boolean;    // can load older messages
  hasNext: boolean;        // can load newer messages
  anchorId: string | null; // the message we jumped to
}

export function useBidirectionalFeed(initialMessageId?: string) {
  const [state, setState] = useState<FeedState>({
    items: [],
    hasPrevious: true,
    hasNext: initialMessageId !== undefined, // if we jumped in, there are newer messages
    anchorId: initialMessageId ?? null,
  });

  // Load the initial window around the anchor message
  useEffect(() => {
    async function init() {
      if (initialMessageId) {
        // Load 20 messages before + the anchor + 20 messages after
        const data = await fetchMessagesAround(initialMessageId, 20);
        setState({
          items: data.messages,
          hasPrevious: data.hasPrevious,
          hasNext: data.hasNext,
          anchorId: initialMessageId,
        });
      } else {
        // No anchor — load from the end (latest messages)
        const data = await fetchLatestMessages(40);
        setState({
          items: data.messages,
          hasPrevious: data.hasPrevious,
          hasNext: false,
          anchorId: null,
        });
      }
    }
    init();
  }, [initialMessageId]);

  async function loadPrevious() {
    const oldestItem = state.items[0];
    if (!oldestItem || !state.hasPrevious) return;

    const data = await fetchMessagesBefore(oldestItem.id, 20);

    setState(prev => ({
      ...prev,
      items: [...data.messages, ...prev.items], // prepend
      hasPrevious: data.hasPrevious,
    }));
  }

  async function loadNext() {
    const newestItem = state.items.at(-1);
    if (!newestItem || !state.hasNext) return;

    const data = await fetchMessagesAfter(newestItem.id, 20);

    setState(prev => ({
      ...prev,
      items: [...prev.items, ...data.messages], // append
      hasNext: data.hasNext,
    }));
  }

  return { ...state, loadPrevious, loadNext };
}
```

```tsx
// BidirectionalFeed.tsx
import { useRef, useEffect, useLayoutEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

export function BidirectionalFeed({ jumpToMessageId }: { jumpToMessageId?: string }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { items, hasPrevious, hasNext, anchorId, loadPrevious, loadNext } =
    useBidirectionalFeed(jumpToMessageId);

  // Row count: loading sentinels at top and/or bottom
  const topSentinel   = hasPrevious ? 1 : 0;
  const bottomSentinel = hasNext ? 1 : 0;
  const rowCount = topSentinel + items.length + bottomSentinel;

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 60,
    overscan: 8,
  });

  // Convert virtualItem.index → item (accounting for sentinel offset)
  function getItem(index: number): Message | null {
    if (topSentinel && index === 0) return null;            // top loading sentinel
    if (bottomSentinel && index === rowCount - 1) return null; // bottom loading sentinel
    return items[index - topSentinel];
  }

  // Jump to anchor message on first render
  useLayoutEffect(() => {
    if (!anchorId) return;
    const anchorIndex = items.findIndex(m => m.id === anchorId);
    if (anchorIndex === -1) return;

    const virtualIndex = anchorIndex + topSentinel;
    virtualizer.scrollToIndex(virtualIndex, { align: 'center' });
  }, [anchorId, items.length]);

  // Detect scroll near top → load previous
  const scrollTopRef = useRef(0);
  function handleScroll(e: React.UIEvent<HTMLDivElement>) {
    const el = e.currentTarget;
    scrollTopRef.current = el.scrollTop;

    if (el.scrollTop < 200 && hasPrevious) {
      // Capture anchor before prepend
      const heightBefore = el.scrollHeight;
      const scrollBefore = el.scrollTop;

      loadPrevious().then(() => {
        requestAnimationFrame(() => {
          const delta = el.scrollHeight - heightBefore;
          el.scrollTop = scrollBefore + delta; // compensate for prepended items
        });
      });
    }
  }

  // Detect scroll near bottom → load next
  useEffect(() => {
    const lastItem = virtualizer.getVirtualItems().at(-1);
    if (!lastItem) return;
    if (lastItem.index >= rowCount - 3 && hasNext) {
      loadNext();
    }
  }, [virtualizer.getVirtualItems()]);

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      style={{ height: '100vh', overflowY: 'auto' }}
    >
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const item = getItem(virtualItem.index);

          return (
            <div
              key={virtualItem.key}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: virtualItem.start,
                width: '100%',
                // Highlight anchor message
                background: item?.id === anchorId ? '#fef9c3' : undefined,
              }}
            >
              {item === null ? (
                <LoadingRow />
              ) : (
                <MessageCard message={item} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 20. Industry Patterns — How Slack, Twitter, Linear Do It

### Slack — Channel Message List

```
Problem Slack solved:
  - Channels can have years of history (millions of messages)
  - Users jump to mentions from any point in history
  - Multiple users in same channel see real-time updates
  - Messages can be edited, deleted, have reactions added

Architecture:
  1. Load "around" messages
     When jumping to a message, Slack fetches:
       - 50 messages before the target
       - The target message
       - 50 messages after the target
     This gives enough context to fill the viewport plus overscan.

  2. Anchor-preserving prepend
     When user scrolls up and older messages load, Slack uses the
     CSS `overflow-anchor` property + scroll compensation to prevent jumping.

  3. Fixed-size internal estimation with ResizeObserver correction
     All messages start with a fixed estimate. ResizeObserver fires and
     corrects. Slack does NOT wait for measurement before rendering.

  4. Memory budget: ~200 messages in memory per channel
     Oldest messages beyond 200 are evicted.
     If user scrolls back into evicted territory, they're fetched again.

  5. Real-time updates via WebSocket
     New message arrives → append to array → virtualizer extends automatically
     Message edited → update in-place → ResizeObserver fires if height changed
     Message deleted → remove from array → shift all indices (this is painful)
```

### Twitter / X — Home Timeline

```
Problem Twitter solved:
  - Infinite downward scroll
  - Tweets contain images (variable, unknown height)
  - Real-time new tweets arrive at top
  - "Show 47 new tweets" button (don't auto-prepend — would jump)

Architecture:
  1. Do NOT auto-prepend new tweets
     New tweets accumulate in a buffer. Show "47 new tweets" pill.
     User clicks → smooth scroll to top, new tweets prepend.
     This avoids the jump problem entirely.

  2. Cursor-based pagination
     Each request returns nextCursor.
     nextCursor is the tweet ID of the oldest tweet in the batch.
     Stable even as new tweets arrive.

  3. Image height reservation
     Twitter knows image aspect ratios from the API response.
     Height is pre-calculated: containerWidth / aspectRatio.
     No estimation needed for images — exact from the start.
     Only text tweets need ResizeObserver measurement.

  4. maxPages: 8
     Twitter keeps ~8 pages in memory (≈160 tweets).
     Scrolling back past 8 pages re-fetches from API.
```

### Linear — Issue List

```
Problem Linear solved:
  - Issues list is not just text — has status icons, assignee avatars, priority badges
  - List is filterable and sortable (changes items instantly)
  - Items can be drag-and-dropped (very complex with virtualization)
  - Keyboard navigation (j/k to move up/down)

Architecture:
  1. Windowed rendering with fixed row height
     Linear uses 36px fixed height rows.
     Even though rows visually look variable, they're fixed.
     Long titles are truncated with ellipsis — no wrapping.
     This makes virtualization trivial (no measurement needed).

  2. Instant filter/sort
     All issues for the current view are fetched upfront (max ~5,000).
     Filter/sort happens client-side in < 10ms on a sorted/indexed array.
     No network request on filter change.

  3. Drag and drop
     This is the hardest part. Linear uses a separate "drag layer":
       - The dragged item is removed from the virtual list
       - Rendered as a fixed-position clone following the cursor
       - On drop, re-inserted at the target position
       - Avoids fighting with absolute-positioned virtualized items.

  4. Keyboard navigation
     j/k moves a "focused index" counter.
     When focused index goes out of visible range:
       virtualizer.scrollToIndex(focusedIndex, { align: 'auto' })
     "auto" = scroll only if out of view, else don't move.
```

### Facebook Feed — The OG

```
Problem Facebook solved:
  - First to hit this problem at scale (2009–2011)
  - Feed mixes photos, videos, links, status updates, ads (massively variable heights)
  - Infinite scroll with no pagination
  - Feed is personalized — no stable cursor

Architecture (the original "virtualization from scratch" before libraries existed):
  1. Sentinel divs
     Each "page" of the feed was wrapped in a container div.
     When a container scrolled out of view, its children were REPLACED
     with an empty div of the same height. Content was destroyed.
     When it scrolled back into view, content was re-fetched and rendered.
     This was effectively manual DOM virtualization.

  2. Height caching via IntersectionObserver
     Facebook measured each container's height on first render.
     Stored in a Map. Used the cached height for the empty placeholder.

  3. Layout recalculation guard
     After replacing content with placeholder, Facebook forced a
     synchronous reflow ONCE to stabilize heights, then never again.

  4. Modern Facebook (2020+)
     Rewrote using React with a custom virtualized list built in-house.
     They open-sourced much of this thinking via the "Relay" data-fetching
     approach and "concurrent rendering" which became React's concurrent mode.
```

### The Pattern They All Share

```
Every production infinite list uses the same 5-layer architecture:

Layer 1: DATA FETCHING
  Cursor-based pagination
  React Query / SWR with maxPages
  Prefetch next page before user hits the end

Layer 2: MEMORY MANAGEMENT
  Normalized entity store (items stored once by ID)
  Page eviction when over memory budget
  Null placeholders for evicted content

Layer 3: VIRTUALIZATION
  @tanstack/react-virtual or custom
  estimateSize by content type
  measureElement with ResizeObserver
  Overscan tuned to scroll speed

Layer 4: SCROLL MANAGEMENT
  Scroll anchoring on prepend
  Bidirectional sentinel detection
  Scroll position restoration on navigation
  "New items" buffer (don't auto-prepend)

Layer 5: REAL-TIME SYNC
  WebSocket / SSE for live updates
  Append new items to end (cheap — no re-indexing)
  Update in-place via normalized store (cheap — O(1))
  Handle deletes carefully — they shift all indices
```

---

---

## 21. Callback Refs — How `ref={fn}` Actually Works

### The Two Types of Refs in React

Most people only know `useRef`. There is a second type — the **callback ref** — which is more powerful.

```tsx
// Type 1: Object ref (useRef)
const divRef = useRef<HTMLDivElement>(null);
<div ref={divRef}>

// React sets: divRef.current = divElement  on mount
// React sets: divRef.current = null        on unmount
// You read: divRef.current whenever you need it

// ─────────────────────────────────────────────────────

// Type 2: Callback ref (a plain function)
const handleRef = (element: HTMLDivElement | null) => {
  // React CALLS this function:
  //   with the DOM element  → on mount
  //   with null             → on unmount
};
<div ref={handleRef}>
```

The key difference: with `useRef` React sets a property silently. With a callback ref, **React calls your function** — you get control of the exact moment the element appears or disappears.

---

### Basic Callback Ref — Measure on Mount

```tsx
function MeasuredBox() {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const measuredRef = (element: HTMLDivElement | null) => {
    if (element === null) {
      // Element was removed from DOM — cleanup if needed
      return;
    }

    // Element just mounted — measure it RIGHT NOW
    const rect = element.getBoundingClientRect();
    setDimensions({ width: rect.width, height: rect.height });
  };

  return (
    <div ref={measuredRef} style={{ padding: 20, background: '#f3f4f6' }}>
      <p>My dimensions: {dimensions.width}px × {dimensions.height}px</p>
    </div>
  );
}
```

---

### Why `useRef` Cannot Do This

```tsx
// With useRef — you don't know WHEN the element is ready
const divRef = useRef(null);

useEffect(() => {
  // You use useEffect as a workaround, but:
  // 1. useEffect runs AFTER paint — one frame late
  // 2. You must list dependencies carefully
  // 3. No direct signal that the element mounted
  if (divRef.current) {
    const rect = divRef.current.getBoundingClientRect();
  }
}, []);

// With callback ref — you know EXACTLY when it mounted
const measuredRef = (element) => {
  if (element) {
    // Called synchronously during React's commit phase
    // BEFORE the browser paints — zero delay
    const rect = element.getBoundingClientRect();
  }
};
```

Callback refs run during React's **commit phase** — after the DOM is updated but before the browser paints. `useEffect` runs after the browser paints. For measurement, callback ref is faster by one frame.

---

### Stable Callback Ref with `useCallback`

The problem: if you define the callback ref inline, React recreates it on every render. React treats a new function reference as a new ref → it calls `fn(null)` then `fn(element)` every render — unnecessary unmount/remount cycle.

```tsx
// BAD — new function on every render → element unmounts and remounts every render
function Component({ id }) {
  return (
    <div ref={(el) => { /* inline arrow */ }}>
      {/* React calls null then el on EVERY render */}
    </div>
  );
}

// GOOD — stable function reference with useCallback
function Component({ id }) {
  const measuredRef = useCallback((element: HTMLDivElement | null) => {
    if (element === null) return;
    // Only called when the element truly mounts/unmounts
    console.log('mounted:', element);
  }, []); // empty deps = same function forever

  return <div ref={measuredRef}> ... </div>;
}
```

---

### Real Example: Auto-Focus Input on Condition

```tsx
function SearchBar({ isOpen }: { isOpen: boolean }) {
  // useCallback so the ref is stable
  const inputRef = useCallback((element: HTMLInputElement | null) => {
    if (element && isOpen) {
      // Focus exactly when element appears — no setTimeout needed
      element.focus();
    }
  }, [isOpen]);
  // Note: isOpen in deps — if isOpen changes, React re-evaluates the ref
  // This is fine here: when isOpen=true and component mounts, focus fires

  if (!isOpen) return null;

  return (
    <input
      ref={inputRef}
      type="text"
      placeholder="Search..."
      style={{ padding: 8, fontSize: 16, width: '100%' }}
    />
  );
}
```

---

### Real Example: Attach a Third-Party Library to a DOM Node

This is the most common real-world use of callback refs — attaching a library that needs a DOM element.

```tsx
import mapboxgl from 'mapbox-gl';

function MapView({ coordinates }: { coordinates: [number, number] }) {
  const mapInstance = useRef<mapboxgl.Map | null>(null);

  const mapContainerRef = useCallback((container: HTMLDivElement | null) => {
    if (container === null) {
      // Element removed — destroy the map to free memory
      mapInstance.current?.remove();
      mapInstance.current = null;
      return;
    }

    // Element ready — initialize Mapbox with the DOM node
    mapInstance.current = new mapboxgl.Map({
      container,                    // ← the actual DOM element
      style: 'mapbox://styles/mapbox/streets-v12',
      center: coordinates,
      zoom: 12,
    });
  }, []); // stable ref — map only initializes once

  return (
    <div
      ref={mapContainerRef}
      style={{ width: '100%', height: 400 }}
    />
  );
}
```

Without a callback ref, you would use `useRef + useEffect`, but then the map might initialize before the container has its final dimensions — causing wrong sizing.

---

### How `virtualizer.measureElement` Uses a Callback Ref

Now this makes complete sense:

```tsx
// The library defines (simplified):
const measureElement = useCallback((element: HTMLElement | null) => {
  if (element === null) {
    // Element unmounted — disconnect its ResizeObserver
    const index = element?.dataset.index;
    observers.get(index)?.disconnect();
    observers.delete(index);
    return;
  }

  // Element mounted — attach ResizeObserver
  const index = Number(element.dataset.index);
  const observer = new ResizeObserver(([entry]) => {
    const height = entry.borderBoxSize[0].contentBlockSize;
    heightCache.set(index, height);
    rebuildOffsetsFrom(index);
  });
  observer.observe(element, { box: 'border-box' });
  observers.set(index, observer);
}, []);

// You use it as:
<div ref={virtualizer.measureElement}>
// React calls measureElement(divElement) on mount
// React calls measureElement(null) on unmount
```

The library does NOT use `useEffect` to measure items. It uses a callback ref — so measurement happens in the commit phase, before paint, with no delay.

---

### Callback Ref vs useRef + useEffect — Decision Guide

```
Use callback ref when:
  → You need to run code the MOMENT an element appears
  → You need to attach/detach external libraries (maps, charts, players)
  → You need to measure the element right on mount (before paint)
  → The element conditionally renders (if/ternary) — useEffect misses this
  → You want clean teardown when element leaves the DOM

Use useRef when:
  → You need to imperatively call methods on an element later (input.focus())
  → You're storing a mutable value across renders (no DOM involved)
  → You need to access the element inside event handlers or callbacks
  → Timing does not matter — just need a reference
```

---

## 22. ResizeObserver — Complete Tutorial

### What It Does

Fires a callback whenever an element's **size changes**. It watches the element itself — not the window.

```
window.addEventListener('resize')   → fires when WINDOW resizes
ResizeObserver                      → fires when the ELEMENT resizes
                                      (even without window resize —
                                       e.g. sidebar opens, parent flex changes,
                                       content loads, font loads)
```

### Basic Usage

```javascript
// 1. Create the observer with a callback
const observer = new ResizeObserver((entries) => {
  for (const entry of entries) {
    // entry.target       → the DOM element being observed
    // entry.contentRect  → DOMRectReadOnly {width, height, top, left, ...}
    // entry.borderBoxSize    → [{ inlineSize, blockSize }] (includes padding+border)
    // entry.contentBoxSize   → [{ inlineSize, blockSize }] (excludes padding+border)
    // entry.devicePixelContentBoxSize → physical pixels (for canvas)

    console.log('Element resized:', entry.target);
    console.log('New width:', entry.contentRect.width);
    console.log('New height:', entry.contentRect.height);
  }
});

// 2. Start watching an element
const box = document.getElementById('my-box');
observer.observe(box);

// 3. Stop watching one element
observer.unobserve(box);

// 4. Stop watching all elements + free memory
observer.disconnect();
```

ResizeObserver fires **once immediately** when you call `observe()` — giving you the initial size. Then again on every subsequent resize.

### Choosing the Box Model

```javascript
observer.observe(element, { box: 'border-box' });
// Options:
//   'content-box'  → default. Width/height INSIDE padding
//   'border-box'   → width/height INCLUDING padding and border
//   'device-pixel-content-box' → physical pixels (Retina: 2× more than CSS pixels)
```

```
     ┌─────────────────────────────┐  ← border (4px)
     │  ┌───────────────────────┐  │  ← padding (16px)
     │  │                       │  │
     │  │   content area        │  │
     │  │   (content-box)       │  │
     │  └───────────────────────┘  │
     └─────────────────────────────┘
                ↑
           border-box
```

Use `border-box` when you care about total element size (virtualization, charts).
Use `content-box` when you care about the writable area (text editors, canvas).

### React Hook — `useResizeObserver`

```typescript
// useResizeObserver.ts
import { useEffect, useRef, useState, useCallback } from 'react';

interface Size {
  width: number;
  height: number;
}

export function useResizeObserver<T extends HTMLElement>() {
  const [size, setSize] = useState<Size>({ width: 0, height: 0 });
  const observerRef = useRef<ResizeObserver | null>(null);

  const ref = useCallback((element: T | null) => {
    // Disconnect previous observer
    observerRef.current?.disconnect();

    if (element === null) return;

    observerRef.current = new ResizeObserver(([entry]) => {
      setSize({
        width:  entry.borderBoxSize[0].inlineSize,    // width
        height: entry.borderBoxSize[0].contentBlockSize, // height
      });
    });

    observerRef.current.observe(element, { box: 'border-box' });
  }, []);

  return { ref, size };
}

// Usage:
function ResponsiveChart() {
  const { ref, size } = useResizeObserver<HTMLDivElement>();

  return (
    <div ref={ref} style={{ width: '100%' }}>
      {/* Chart redraws whenever container width changes */}
      <canvas width={size.width} height={300} />
      <p>Container is {size.width}px wide</p>
    </div>
  );
}
```

### Real Example: Responsive Text Truncation

```tsx
function TruncatedText({ text }: { text: string }) {
  const [isTruncated, setIsTruncated] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const ref = useCallback((element: HTMLParagraphElement | null) => {
    if (!element) return;

    const observer = new ResizeObserver(() => {
      // Check if text overflows its container
      setIsTruncated(element.scrollHeight > element.clientHeight);
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div>
      <p
        ref={ref}
        style={{
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: isExpanded ? 'unset' : 3,
          WebkitBoxOrient: 'vertical',
        }}
      >
        {text}
      </p>
      {isTruncated && !isExpanded && (
        <button onClick={() => setIsExpanded(true)}>Read more</button>
      )}
    </div>
  );
}
```

### ResizeObserver vs window resize

```javascript
// Old approach — only fires when WINDOW resizes
// Misses: sidebar open/close, dynamic content, font load, flex layout changes
window.addEventListener('resize', () => {
  const width = element.offsetWidth; // may be wrong if not caused by window resize
});

// Modern approach — fires whenever THIS ELEMENT changes size
// Catches everything: window resize, parent resize, content change
const observer = new ResizeObserver(([entry]) => {
  const width = entry.borderBoxSize[0].inlineSize; // always correct
});
observer.observe(element);
```

---

## 23. IntersectionObserver — Complete Tutorial

### What It Does

Fires a callback when an element **enters or exits the viewport** (or a specified container). The browser calculates this asynchronously — zero scroll handler overhead.

```
Before IntersectionObserver (the old way):
  window.addEventListener('scroll', () => {
    const rect = element.getBoundingClientRect(); // forces reflow!
    if (rect.top < window.innerHeight) { doSomething(); }
  });
  // Problem: getBoundingClientRect on every scroll = layout thrash at 60fps

With IntersectionObserver:
  const observer = new IntersectionObserver(callback);
  observer.observe(element);
  // Browser reports visibility changes asynchronously — zero reflow
```

### Basic Usage

```javascript
// 1. Create observer
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    // entry.target          → the observed element
    // entry.isIntersecting  → true = visible, false = not visible
    // entry.intersectionRatio → 0.0 (hidden) to 1.0 (fully visible)
    // entry.boundingClientRect → element's position
    // entry.intersectionRect   → the visible portion
    // entry.rootBounds         → the viewport (or root container)
    // entry.time               → timestamp when this fired

    if (entry.isIntersecting) {
      console.log('Element entered viewport');
    } else {
      console.log('Element left viewport');
    }
  }
});

// 2. Watch an element
observer.observe(document.getElementById('my-element'));

// 3. Stop watching
observer.unobserve(element);
observer.disconnect();
```

### Options — Controlling When It Fires

```javascript
const observer = new IntersectionObserver(callback, {
  // root: which element is the "viewport"
  // null = browser viewport (default)
  // any scrollable element = that container
  root: document.getElementById('scroll-container'),

  // rootMargin: expand/shrink the root for detection
  // Like CSS margin: "top right bottom left"
  // Positive = fires BEFORE element reaches the edge (preload)
  // Negative = fires AFTER element is partially hidden
  rootMargin: '100px 0px 100px 0px',
  // ↑ fires when element is within 100px of top/bottom of viewport

  // threshold: how much of the element must be visible to fire
  // 0   = fires as soon as 1 pixel is visible (default)
  // 0.5 = fires when 50% is visible
  // 1.0 = fires only when 100% is visible
  // [0, 0.25, 0.5, 0.75, 1.0] = fires at each milestone
  threshold: 0.1,
});
```

### Real Example 1: Lazy Loading Images

The most common use case.

```tsx
function LazyImage({ src, alt }: { src: string; alt: string }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = imgRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect(); // stop watching after first visibility — load once
        }
      },
      {
        rootMargin: '200px', // start loading 200px BEFORE entering viewport
        threshold: 0,
      }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} style={{ width: '100%', height: 300, background: '#f3f4f6' }}>
      {isVisible && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        />
      )}
    </div>
  );
}
```

### Real Example 2: Infinite Scroll Trigger

```tsx
function InfiniteList({ items, onLoadMore, hasMore }: Props) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore) {
          onLoadMore();
        }
      },
      {
        rootMargin: '300px', // load next page 300px before hitting the bottom
        threshold: 0,
      }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, onLoadMore]);

  return (
    <div>
      {items.map(item => <ItemCard key={item.id} item={item} />)}

      {/* This invisible div at the bottom triggers load */}
      <div ref={sentinelRef} style={{ height: 1 }} />

      {!hasMore && <p>All items loaded.</p>}
    </div>
  );
}
```

### Real Example 3: Animate Elements on Scroll (Scroll-Reveal)

```tsx
function AnimateOnScroll({ children }: { children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect(); // animate once, stop watching
        }
      },
      { threshold: 0.15 } // fire when 15% visible
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{
        opacity:    isVisible ? 1 : 0,
        transform:  isVisible ? 'translateY(0)' : 'translateY(32px)',
        transition: 'opacity 0.5s ease, transform 0.5s ease',
      }}
    >
      {children}
    </div>
  );
}
```

### Real Example 4: Active Section Highlighting (Table of Contents)

```tsx
function TableOfContents({ sections }: { sections: Section[] }) {
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        // Find the topmost visible section
        const visible = entries
          .filter(e => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      {
        rootMargin: '-20% 0px -70% 0px',
        // ↑ Only the middle 10% of the viewport counts as "active"
        // This prevents rapid switching as user scrolls
        threshold: 0,
      }
    );

    sections.forEach(section => {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav>
      {sections.map(section => (
        <a
          key={section.id}
          href={`#${section.id}`}
          style={{
            display: 'block',
            padding: '4px 8px',
            color:      activeId === section.id ? '#6366f1' : '#6b7280',
            fontWeight: activeId === section.id ? 600 : 400,
            borderLeft: activeId === section.id ? '2px solid #6366f1' : '2px solid transparent',
          }}
        >
          {section.title}
        </a>
      ))}
    </nav>
  );
}
```

---

## 24. MutationObserver — Complete Tutorial

### What It Does

Fires when the **DOM structure changes** — elements added/removed, attributes changed, text content changed.

```
ResizeObserver    → "this element's SIZE changed"
IntersectionObserver → "this element entered/exited the viewport"
MutationObserver  → "the DOM STRUCTURE changed (nodes added, attributes set, text changed)"
```

### Basic Usage

```javascript
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    // mutation.type            → 'childList' | 'attributes' | 'characterData'
    // mutation.target          → the element that changed
    // mutation.addedNodes      → NodeList of added children
    // mutation.removedNodes    → NodeList of removed children
    // mutation.attributeName   → which attribute changed (for 'attributes' type)
    // mutation.oldValue        → previous value (if configured)

    console.log('Mutation type:', mutation.type);
  }
});

// Start observing
observer.observe(element, {
  childList:     true,  // watch for child nodes added/removed
  attributes:    true,  // watch for attribute changes
  characterData: true,  // watch for text content changes
  subtree:       true,  // watch ALL descendants (not just direct children)
  attributeOldValue:    true,  // include previous attribute value in mutation
  characterDataOldValue: true, // include previous text in mutation
});

observer.disconnect(); // stop observing
```

### Real Example 1: Watch for Third-Party DOM Changes

Useful when a library injects elements you cannot control.

```typescript
function watchForInjectedBanner() {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node instanceof HTMLElement && node.classList.contains('ad-banner')) {
          // Third-party injected an ad — reposition our UI
          adjustLayoutForBanner(node.offsetHeight);
        }
      }
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
  return () => observer.disconnect();
}
```

### Real Example 2: React — Detect When a Modal Portal Mounts

React portals render outside the component tree. MutationObserver can detect when they appear.

```typescript
useEffect(() => {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node instanceof HTMLElement && node.getAttribute('data-modal')) {
          // A modal just opened — trap focus inside it
          trapFocus(node);
        }
      }
      for (const node of mutation.removedNodes) {
        if (node instanceof HTMLElement && node.getAttribute('data-modal')) {
          // Modal closed — restore focus to the trigger button
          restoreFocus();
        }
      }
    }
  });

  observer.observe(document.getElementById('portal-root')!, {
    childList: true,
  });

  return () => observer.disconnect();
}, []);
```

### Real Example 3: Live Character Counter

```tsx
function LiveCharCounter() {
  const [count, setCount] = useState(0);
  const editorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;

    const observer = new MutationObserver(() => {
      // contentEditable div — text can change without React knowing
      setCount(editor.textContent?.length ?? 0);
    });

    observer.observe(editor, {
      characterData: true,  // text node content changed
      childList: true,      // nodes added/removed (e.g. pasting)
      subtree: true,        // watch all descendants
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div>
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        style={{ border: '1px solid #ccc', padding: 12, minHeight: 100, borderRadius: 4 }}
      />
      <p style={{ color: count > 280 ? 'red' : '#6b7280', fontSize: 13 }}>
        {count} / 280 characters
      </p>
    </div>
  );
}
```

---

## 25. PerformanceObserver — Complete Tutorial

### What It Does

Fires when the browser records performance **timeline entries** — paint events, layout shifts, long tasks, resource loads, user interactions.

```
Other observers watch DOM changes.
PerformanceObserver watches BROWSER PERFORMANCE METRICS.
```

### Entry Types You Can Observe

```javascript
// See all available types in this browser:
PerformanceObserver.supportedEntryTypes
// → ['element', 'event', 'first-input', 'largest-contentful-paint',
//    'layout-shift', 'longtask', 'mark', 'measure', 'navigation',
//    'paint', 'resource', 'visibility-state']
```

### Basic Usage

```javascript
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(entry.entryType, entry.name, entry.startTime, entry.duration);
  }
});

observer.observe({ entryTypes: ['paint', 'longtask'] });
observer.disconnect();
```

### Real Example 1: Measure Core Web Vitals

```typescript
// core-web-vitals.ts — measure the 3 metrics Google uses for ranking

function measureWebVitals() {

  // 1. FCP — First Contentful Paint
  // When the first text/image appears on screen
  new PerformanceObserver((list) => {
    const fcp = list.getEntriesByName('first-contentful-paint')[0];
    console.log('FCP:', fcp.startTime.toFixed(0), 'ms');
    // Good: < 1800ms,  Needs improvement: < 3000ms,  Poor: > 3000ms
  }).observe({ entryTypes: ['paint'] });


  // 2. LCP — Largest Contentful Paint
  // When the largest image or text block finishes rendering
  new PerformanceObserver((list) => {
    const entries = list.getEntries();
    const lcp = entries.at(-1); // last entry = final LCP candidate
    console.log('LCP:', lcp.startTime.toFixed(0), 'ms');
    // Good: < 2500ms,  Needs improvement: < 4000ms,  Poor: > 4000ms
  }).observe({ entryTypes: ['largest-contentful-paint'] });


  // 3. CLS — Cumulative Layout Shift
  // How much content unexpectedly moves (images loading, ads injecting)
  let clsScore = 0;
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      // Only count shifts without recent user input (user-initiated shifts are ok)
      if (!(entry as any).hadRecentInput) {
        clsScore += (entry as any).value;
      }
    }
    console.log('CLS so far:', clsScore.toFixed(4));
    // Good: < 0.1,  Needs improvement: < 0.25,  Poor: > 0.25
  }).observe({ entryTypes: ['layout-shift'] });


  // 4. FID / INP — Interaction to Next Paint
  // Delay between user input and browser responding
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      const delay = (entry as any).processingStart - entry.startTime;
      console.log('Interaction delay:', delay.toFixed(0), 'ms', 'on', entry.name);
      // Good: < 200ms,  Needs improvement: < 500ms,  Poor: > 500ms
    }
  }).observe({ entryTypes: ['first-input', 'event'] });
}
```

### Real Example 2: Detect Long Tasks (Jank Detection)

```typescript
// A "long task" is any JS execution > 50ms
// It blocks the main thread and causes dropped frames

function detectJank() {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.duration > 50) {
        console.warn(
          `Long task detected: ${entry.duration.toFixed(0)}ms`,
          `Attribution:`, (entry as any).attribution
        );
        // In production: send to monitoring (Datadog, Sentry, etc.)
        sendMetric('long_task', {
          duration: entry.duration,
          startTime: entry.startTime,
        });
      }
    }
  });

  observer.observe({ entryTypes: ['longtask'] });
  return () => observer.disconnect();
}
```

### Real Example 3: Custom Performance Marks Around Your Own Code

```typescript
// Mark and measure your own code sections

// Place marks at key points in your code:
performance.mark('virtualization-render-start');

// ... your virtualized list renders ...
virtualizer.getVirtualItems().forEach(renderItem);

performance.mark('virtualization-render-end');

// Measure the gap between two marks:
performance.measure(
  'virtualization-render',       // name for this measurement
  'virtualization-render-start', // start mark
  'virtualization-render-end'    // end mark
);

// Observe your custom measurements:
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.name === 'virtualization-render') {
      console.log(`Rendered ${visibleItems} items in ${entry.duration.toFixed(2)}ms`);
    }
  }
});

observer.observe({ entryTypes: ['measure'] });
```

---

## 26. All Four Observers — When to Use Which

```
Observer              Watches                       Fires when
────────────────────────────────────────────────────────────────────────────────
ResizeObserver        A specific DOM element        Its WIDTH or HEIGHT changes
                                                    (window resize, parent resize,
                                                     content reflow, font load)

IntersectionObserver  A specific DOM element        It enters or exits the viewport
                      against a root/viewport       (or a custom scroll container)

MutationObserver      A DOM node (and optionally    Children added/removed
                      its entire subtree)           Attributes changed
                                                    Text content changed

PerformanceObserver   The browser's performance     Paint events, layout shifts,
                      timeline                      long tasks, resource loads,
                                                    user interactions
```

### Decision Tree

```
"I want to know when an element changes SIZE"
  → ResizeObserver

"I want to know when an element becomes VISIBLE or goes off-screen"
  → IntersectionObserver
  → Use cases: lazy load, infinite scroll trigger, animate on scroll, TOC highlight

"I want to know when the DOM STRUCTURE changes (nodes added/removed/text changed)"
  → MutationObserver
  → Use cases: third-party DOM injection, contentEditable, watching portals

"I want to measure BROWSER PERFORMANCE (FCP, LCP, CLS, long tasks)"
  → PerformanceObserver
  → Use cases: Core Web Vitals, jank detection, custom timing

"I want to run code when an element MOUNTS or UNMOUNTS"
  → Callback ref (not an observer — but the answer to this question)
  → Use cases: attach libraries, measure initial size, setup/teardown
```

### All Together in One Architecture

In a real virtualized list all of them work together:

```
Callback ref          → fires when item div mounts → hands element to ResizeObserver
ResizeObserver        → measures item height → updates prefix sum
IntersectionObserver  → detects list sentinel entering viewport → triggers fetchNextPage()
MutationObserver      → watches for content changes in items → invalidates height cache
PerformanceObserver   → measures render time per batch → alerts on long tasks
```

---

*This document covers `@tanstack/react-virtual` v3. Always check the [official docs](https://tanstack.com/virtual/latest) for the latest API.*
