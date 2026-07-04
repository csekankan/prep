# TanStack Query, SWR, Zustand & React Libraries — Interview-Ready Deep Dive

> Real examples, advanced concepts, and the libraries every React developer is expected to know.

---

## Table of Contents

1. [TanStack Query (React Query)](#1-tanstack-query-react-query)
   - [Without ETag — Basic Setup](#11-without-etag--basic-setup)
   - [With ETag — Conditional Requests](#12-with-etag--conditional-requests)
   - [Mutations — POST, PUT, DELETE](#13-mutations)
   - [Optimistic Updates](#14-optimistic-updates)
   - [Infinite Scroll / Pagination](#15-infinite-scroll--pagination)
   - [Prefetching](#16-prefetching)
   - [Dependent Queries](#17-dependent-queries)
   - [Query Invalidation](#18-query-invalidation)
   - [Cache Synchronization across tabs](#19-cache-synchronization-across-tabs)
   - [Advanced: Custom Query Client](#110-advanced-custom-query-client)
2. [SWR — by Vercel](#2-swr--by-vercel)
3. [Zustand — Lightweight Global State](#3-zustand--lightweight-global-state)
4. [Redux Toolkit (RTK) + RTK Query](#4-redux-toolkit-rtk--rtk-query)
5. [React Hook Form](#5-react-hook-form)
6. [Jotai — Atomic State](#6-jotai--atomic-state)
7. [Library Comparison — When to Use What](#7-library-comparison--when-to-use-what)
8. [Interview Questions & Answers](#8-interview-questions--answers)

---

## 1. TanStack Query (React Query)

### What it solves

Without TanStack Query, you write this manually for every API call:

```tsx
// The pain — without TanStack Query
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/users/${userId}`)
      .then((r) => r.json())
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [userId]);

  // Problems:
  // - No caching (re-fetches every mount)
  // - No deduplication (10 components = 10 requests)
  // - No background refresh
  // - No stale detection
  // - No retry on failure
  // - Race conditions if userId changes fast
  // - You write this 50 times across the app
}
```

TanStack Query solves all of this in one hook.

---

### 1.1 Without ETag — Basic Setup

**Install:**

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

**Setup at app root:**

```tsx
// main.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,        // data is fresh for 60s — no refetch
      gcTime: 5 * 60 * 1000,   // remove from memory after 5min unused
      retry: 2,                 // retry failed requests twice
      refetchOnWindowFocus: true, // refetch when tab gets focus
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

**Basic useQuery:**

```tsx
// hooks/useUser.ts
import { useQuery } from "@tanstack/react-query";

async function fetchUser(userId: number) {
  const res = await fetch(`/api/users/${userId}`);
  if (!res.ok) throw new Error(`Failed: ${res.status}`);
  return res.json();
}

export function useUser(userId: number) {
  return useQuery({
    queryKey: ["user", userId],   // cache key — array, not string
    queryFn: () => fetchUser(userId),
    enabled: !!userId,            // don't fetch if userId is undefined/null
  });
}

// components/UserProfile.tsx
import { useUser } from "../hooks/useUser";

export function UserProfile({ userId }: { userId: number }) {
  const { data: user, isLoading, isError, error, isFetching } = useUser(userId);

  if (isLoading) return <Skeleton />;           // first load, no cache
  if (isError) return <p>Error: {error.message}</p>;

  return (
    <div>
      {isFetching && <RefreshIndicator />}       // background refresh happening
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}
```

**Understanding query states:**

```
isLoading   = true  → no data in cache at all, waiting for first fetch
isPending   = true  → query hasn't run yet (enabled: false, or first run)
isFetching  = true  → any fetch in progress (initial OR background)
isStale     = true  → data older than staleTime, will refetch on next trigger
isSuccess   = true  → data available
isError     = true  → last fetch failed
```

```
Timeline:

Mount (no cache)
  isLoading: true, isFetching: true
        ↓ fetch completes
  isLoading: false, isSuccess: true, isFetching: false

Navigate away, come back (data is stale)
  isLoading: false  ← data exists, shown immediately
  isFetching: true  ← background refresh started
        ↓ fetch completes
  isFetching: false ← UI updates silently if data changed
```

---

### 1.2 With ETag — Conditional Requests

Without ETag: every background refetch downloads full response body.
With ETag: server checks fingerprint — if unchanged, sends `304 Not Modified` (no body).

```tsx
// lib/fetchWithETag.ts
const etagStore = new Map<string, string>(); // url → etag value

export async function fetchWithETag<T>(url: string): Promise<T | undefined> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Attach ETag if we have one from a previous response
  const storedEtag = etagStore.get(url);
  if (storedEtag) {
    headers["If-None-Match"] = storedEtag;
  }

  const res = await fetch(url, { headers });

  // 304 = nothing changed → return undefined, TanStack keeps old data
  if (res.status === 304) {
    return undefined;
  }

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  // Store new ETag for next request
  const newEtag = res.headers.get("ETag");
  if (newEtag) {
    etagStore.set(url, newEtag);
  }

  return res.json() as T;
}
```

```tsx
// hooks/useUser.ts — now with ETag
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchWithETag } from "../lib/fetchWithETag";

export function useUser(userId: number) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ["user", userId],
    queryFn: async () => {
      const data = await fetchWithETag<User>(`/api/users/${userId}`);

      // If 304 — fetchWithETag returned undefined
      // Return existing cache so TanStack doesn't overwrite with undefined
      if (data === undefined) {
        return queryClient.getQueryData<User>(["user", userId]);
      }

      return data;
    },
    staleTime: 30_000,
  });
}
```

**Network tab comparison:**

```
Without ETag (every refetch):
  GET /api/users/1 → 200 → 1.2 KB downloaded

With ETag (data unchanged):
  GET /api/users/1
  If-None-Match: "abc123"
  → 304 Not Modified → 0 bytes downloaded
```

On a list page with 50 items, this means:
- Without ETag: 50 × 1.2KB = 60KB downloaded on every background refetch
- With ETag (unchanged): 50 × ~200 bytes (headers only) = 10KB

---

### 1.3 Mutations

`useMutation` handles POST / PUT / DELETE. Unlike `useQuery`, it does NOT run automatically — you call it manually.

```tsx
// hooks/useUpdateUser.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";

async function updateUser(userId: number, data: Partial<User>) {
  const res = await fetch(`/api/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Update failed");
  return res.json();
}

export function useUpdateUser(userId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<User>) => updateUser(userId, data),

    // After success — tell TanStack the cached user is now stale
    onSuccess: (updatedUser) => {
      // Option A: Invalidate — forces a fresh fetch on next access
      queryClient.invalidateQueries({ queryKey: ["user", userId] });

      // Option B: Directly update cache — no extra network request
      queryClient.setQueryData(["user", userId], updatedUser);
    },

    onError: (error) => {
      console.error("Mutation failed:", error);
    },
  });
}

// components/EditProfile.tsx
export function EditProfile({ userId }: { userId: number }) {
  const { data: user } = useUser(userId);
  const { mutate: updateUser, isPending, isError } = useUpdateUser(userId);
  const [name, setName] = useState(user?.name ?? "");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    updateUser({ name }); // triggers the mutation
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button type="submit" disabled={isPending}>
        {isPending ? "Saving..." : "Save"}
      </button>
      {isError && <p>Failed to save. Try again.</p>}
    </form>
  );
}
```

---

### 1.4 Optimistic Updates

Show the result immediately, before the server responds. Roll back if server rejects it.

```
Without optimistic update:
  User clicks Save → spinner → 500ms wait → UI updates
  Feels slow.

With optimistic update:
  User clicks Save → UI updates instantly → server confirms in background
  Feels instant. Roll back only if server rejects.
```

```tsx
// hooks/useToggleTodo.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface Todo {
  id: number;
  text: string;
  completed: boolean;
}

export function useToggleTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (todo: Todo) =>
      fetch(`/api/todos/${todo.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: !todo.completed }),
      }).then((r) => r.json()),

    // Fires BEFORE the network request
    onMutate: async (todo) => {
      // 1. Cancel any in-flight queries for this key (avoid race condition)
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // 2. Snapshot the current cache (for rollback)
      const previousTodos = queryClient.getQueryData<Todo[]>(["todos"]);

      // 3. Optimistically update the cache
      queryClient.setQueryData<Todo[]>(["todos"], (old) =>
        old?.map((t) =>
          t.id === todo.id ? { ...t, completed: !t.completed } : t
        )
      );

      // 4. Return snapshot in context — used in onError for rollback
      return { previousTodos };
    },

    // Server rejected → roll back to snapshot
    onError: (_error, _todo, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(["todos"], context.previousTodos);
      }
    },

    // After success or error → sync with server truth
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

// components/TodoItem.tsx
export function TodoItem({ todo }: { todo: Todo }) {
  const { mutate: toggle } = useToggleTodo();

  return (
    <li
      onClick={() => toggle(todo)}
      style={{ textDecoration: todo.completed ? "line-through" : "none" }}
    >
      {todo.text}
    </li>
    // Clicking toggles instantly — no spinner, no wait
    // If server fails, it snaps back automatically
  );
}
```

---

### 1.5 Infinite Scroll / Pagination

```tsx
// hooks/usePosts.ts
import { useInfiniteQuery } from "@tanstack/react-query";

interface PostsPage {
  posts: Post[];
  nextCursor: string | null;
  totalCount: number;
}

async function fetchPosts({ pageParam }: { pageParam: string | null }) {
  const url = pageParam
    ? `/api/posts?cursor=${pageParam}&limit=20`
    : `/api/posts?limit=20`;
  const res = await fetch(url);
  return res.json() as Promise<PostsPage>;
}

export function useInfinitePosts() {
  return useInfiniteQuery({
    queryKey: ["posts"],
    queryFn: fetchPosts,
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor, // null = no more pages
  });
}

// components/PostFeed.tsx
import { useIntersectionObserver } from "../hooks/useIntersectionObserver";

export function PostFeed() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfinitePosts();

  // Intersection observer fires fetchNextPage when sentinel div enters view
  const { ref: sentinelRef } = useIntersectionObserver({
    onIntersect: () => {
      if (hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
  });

  if (isLoading) return <Skeleton />;

  // data.pages is an array of pages — flatten into one list
  const allPosts = data.pages.flatMap((page) => page.posts);

  return (
    <div>
      {allPosts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      {/* Invisible div at bottom — triggers load when visible */}
      <div ref={sentinelRef} style={{ height: 1 }} />

      {isFetchingNextPage && <LoadingSpinner />}
      {!hasNextPage && <p>No more posts</p>}
    </div>
  );
}
```

---

### 1.6 Prefetching

Load data before the user navigates to a page — so it appears instant.

```tsx
// Prefetch on hover — data is ready before click
function PostLink({ postId, children }: { postId: number; children: React.ReactNode }) {
  const queryClient = useQueryClient();

  function handleMouseEnter() {
    queryClient.prefetchQuery({
      queryKey: ["post", postId],
      queryFn: () => fetchPost(postId),
      staleTime: 30_000, // only prefetch if cache is older than 30s
    });
  }

  return (
    <Link to={`/posts/${postId}`} onMouseEnter={handleMouseEnter}>
      {children}
    </Link>
  );
}

// Prefetch on server side (Next.js / TanStack Router)
// app/posts/page.tsx (Next.js)
export async function generateStaticProps() {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: ["posts"],
    queryFn: fetchPosts,
  });

  return {
    props: {
      dehydratedState: dehydrate(queryClient), // serialize for client
    },
  };
}
```

---

### 1.7 Dependent Queries

Query B depends on the result of Query A.

```tsx
// First get the user, then get their company using user.companyId
function useUserWithCompany(userId: number) {
  // Query A — always runs
  const userQuery = useQuery({
    queryKey: ["user", userId],
    queryFn: () => fetchUser(userId),
  });

  // Query B — only runs AFTER Query A has data
  const companyQuery = useQuery({
    queryKey: ["company", userQuery.data?.companyId],
    queryFn: () => fetchCompany(userQuery.data!.companyId),
    enabled: !!userQuery.data?.companyId, // ← key: disabled until we have companyId
  });

  return { user: userQuery.data, company: companyQuery.data };
}
```

---

### 1.8 Query Invalidation

After a mutation, tell TanStack which cached data is now stale.

```tsx
const queryClient = useQueryClient();

// Invalidate a specific query
queryClient.invalidateQueries({ queryKey: ["user", 1] });

// Invalidate all queries starting with "user"
queryClient.invalidateQueries({ queryKey: ["user"] });

// Invalidate everything
queryClient.invalidateQueries();

// Remove from cache entirely (no background refetch)
queryClient.removeQueries({ queryKey: ["user", 1] });

// Force refetch immediately (even if fresh)
queryClient.refetchQueries({ queryKey: ["user"] });

// Manually set data (skip network entirely)
queryClient.setQueryData(["user", 1], (old: User) => ({
  ...old,
  name: "Updated Name",
}));
```

---

### 1.9 Cache Synchronization Across Tabs

When the user updates data in Tab A, Tab B should show the update automatically.

```tsx
// lib/broadcastInvalidation.ts
const channel = new BroadcastChannel("query-invalidation");

// Send invalidation event to other tabs
export function broadcastInvalidation(queryKey: unknown[]) {
  channel.postMessage({ type: "invalidate", queryKey });
}

// Listen and apply in your app root
export function useCrossTabInvalidation() {
  const queryClient = useQueryClient();

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data.type === "invalidate") {
        queryClient.invalidateQueries({ queryKey: event.data.queryKey });
      }
    }
    channel.addEventListener("message", handleMessage);
    return () => channel.removeEventListener("message", handleMessage);
  }, [queryClient]);
}

// In your mutation — broadcast after success
useMutation({
  mutationFn: updateUser,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["user"] });
    broadcastInvalidation(["user"]); // tells other tabs to refresh
  },
});
```

---

### 1.10 Advanced: Custom Query Client

Configure different defaults per query type:

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 10 * 60 * 1000,
      retry: (failureCount, error) => {
        // Don't retry on 401/403/404 — they won't change
        if (error instanceof HttpError && [401, 403, 404].includes(error.status)) {
          return false;
        }
        return failureCount < 3; // retry up to 3 times for other errors
      },
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000), // exponential backoff
    },
    mutations: {
      retry: 0, // never retry mutations automatically
      onError: (error) => {
        toast.error(`Something went wrong: ${error.message}`);
      },
    },
  },
});
```

---

## 2. SWR — by Vercel

SWR (Stale-While-Revalidate) is Vercel's lightweight alternative to TanStack Query. Simpler API, smaller bundle, used heavily in Next.js apps.

**Install:**

```bash
npm install swr
```

**Basic usage:**

```tsx
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function UserProfile({ userId }: { userId: number }) {
  const { data: user, error, isLoading, isValidating } = useSWR(
    `/api/users/${userId}`,
    fetcher,
    {
      revalidateOnFocus: true,       // refetch when tab gets focus
      revalidateOnReconnect: true,   // refetch when network returns
      refreshInterval: 30_000,       // poll every 30s
      dedupingInterval: 2_000,       // deduplicate requests within 2s
    }
  );

  if (isLoading) return <Skeleton />;
  if (error) return <p>Error</p>;

  return (
    <div>
      {isValidating && <RefreshIndicator />}
      <h1>{user.name}</h1>
    </div>
  );
}
```

**SWR mutation:**

```tsx
import useSWRMutation from "swr/mutation";

async function updateUser(url: string, { arg }: { arg: Partial<User> }) {
  return fetch(url, {
    method: "PUT",
    body: JSON.stringify(arg),
  }).then((r) => r.json());
}

function EditProfile({ userId }: { userId: number }) {
  const { trigger, isMutating } = useSWRMutation(
    `/api/users/${userId}`,
    updateUser
  );

  return (
    <button
      disabled={isMutating}
      onClick={() => trigger({ name: "Alice Smith" })}
    >
      {isMutating ? "Saving..." : "Save"}
    </button>
  );
}
```

**SWR vs TanStack Query — honest comparison:**

| Feature | SWR | TanStack Query |
|---|---|---|
| Bundle size | ~4KB | ~13KB |
| API simplicity | Simpler | More verbose |
| Mutations | Basic (`useSWRMutation`) | Powerful (`useMutation` + `onMutate`) |
| Optimistic updates | Manual | Built-in pattern |
| Infinite scroll | `useSWRInfinite` | `useInfiniteQuery` |
| Devtools | No official devtools | Full devtools panel |
| Dependent queries | Conditional key | `enabled` option |
| Best for | Next.js, simple apps | Complex apps, lots of mutations |

---

## 3. Zustand — Lightweight Global State

Zustand is the most popular simple global state library. Replaces Redux for most use cases. Tiny API, no boilerplate.

**Install:**

```bash
npm install zustand
```

**Basic store:**

```tsx
// stores/useAuthStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware"; // persist to localStorage

interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "user";
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (user: User, token: string) => void;
  logout: () => void;
  updateProfile: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (user, token) => set({ user, token, isAuthenticated: true }),

      logout: () => set({ user: null, token: null, isAuthenticated: false }),

      updateProfile: (updates) => {
        const current = get().user;
        if (!current) return;
        set({ user: { ...current, ...updates } });
      },
    }),
    {
      name: "auth-storage", // localStorage key
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
);

// Usage in component — subscribe to only what you need
function NavBar() {
  // Only re-renders when user.name changes — not on unrelated state changes
  const userName = useAuthStore((state) => state.user?.name);
  const logout = useAuthStore((state) => state.logout);

  return (
    <nav>
      <span>Hello, {userName}</span>
      <button onClick={logout}>Logout</button>
    </nav>
  );
}
```

**Zustand with immer (for nested state):**

```tsx
// stores/useCartStore.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

interface CartItem {
  id: number;
  name: string;
  price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  addItem: (item: Omit<CartItem, "quantity">) => void;
  removeItem: (id: number) => void;
  incrementQuantity: (id: number) => void;
  totalPrice: () => number;
}

export const useCartStore = create<CartState>()(
  immer((set, get) => ({
    items: [],

    addItem: (item) =>
      set((state) => {
        const existing = state.items.find((i) => i.id === item.id);
        if (existing) {
          existing.quantity += 1; // immer lets you mutate directly
        } else {
          state.items.push({ ...item, quantity: 1 });
        }
      }),

    removeItem: (id) =>
      set((state) => {
        state.items = state.items.filter((i) => i.id !== id);
      }),

    incrementQuantity: (id) =>
      set((state) => {
        const item = state.items.find((i) => i.id === id);
        if (item) item.quantity += 1;
      }),

    totalPrice: () =>
      get().items.reduce((sum, item) => sum + item.price * item.quantity, 0),
  }))
);
```

**Zustand slice pattern (large stores):**

```tsx
// Split large stores into slices
interface BearSlice {
  bears: number;
  addBear: () => void;
}

interface FishSlice {
  fish: number;
  addFish: () => void;
}

const createBearSlice = (set: SetState<BearSlice & FishSlice>): BearSlice => ({
  bears: 0,
  addBear: () => set((state) => ({ bears: state.bears + 1 })),
});

const createFishSlice = (set: SetState<BearSlice & FishSlice>): FishSlice => ({
  fish: 0,
  addFish: () => set((state) => ({ fish: state.fish + 1 })),
});

export const useStore = create<BearSlice & FishSlice>()((...args) => ({
  ...createBearSlice(...args),
  ...createFishSlice(...args),
}));
```

---

## 4. Redux Toolkit (RTK) + RTK Query

Redux Toolkit is the modern, official way to use Redux. RTK Query is its built-in data fetching layer — similar to TanStack Query but tightly integrated with Redux.

**Install:**

```bash
npm install @reduxjs/toolkit react-redux
```

**RTK — createSlice (replaces old Redux):**

```tsx
// features/counterSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface CounterState {
  value: number;
  status: "idle" | "loading";
}

const counterSlice = createSlice({
  name: "counter",
  initialState: { value: 0, status: "idle" } as CounterState,
  reducers: {
    increment: (state) => {
      state.value += 1; // RTK uses immer — direct mutation is safe
    },
    decrement: (state) => {
      state.value -= 1;
    },
    incrementByAmount: (state, action: PayloadAction<number>) => {
      state.value += action.payload;
    },
  },
});

export const { increment, decrement, incrementByAmount } = counterSlice.actions;
export default counterSlice.reducer;
```

**RTK Query — API slice:**

```tsx
// services/userApi.ts
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const userApi = createApi({
  reducerPath: "userApi",
  baseQuery: fetchBaseQuery({ baseUrl: "/api" }),
  tagTypes: ["User"],  // for cache invalidation

  endpoints: (builder) => ({
    getUser: builder.query<User, number>({
      query: (id) => `/users/${id}`,
      providesTags: (result, error, id) => [{ type: "User", id }],
    }),

    updateUser: builder.mutation<User, { id: number; data: Partial<User> }>({
      query: ({ id, data }) => ({
        url: `/users/${id}`,
        method: "PUT",
        body: data,
      }),
      // Invalidate the User cache after update
      invalidatesTags: (result, error, { id }) => [{ type: "User", id }],
    }),

    getUsers: builder.query<User[], void>({
      query: () => "/users",
      providesTags: ["User"],
    }),
  }),
});

// Auto-generated hooks
export const { useGetUserQuery, useUpdateUserMutation, useGetUsersQuery } = userApi;

// Usage in component — identical mental model to TanStack Query
function UserProfile({ userId }: { userId: number }) {
  const { data: user, isLoading, isFetching } = useGetUserQuery(userId);
  const [updateUser, { isLoading: isUpdating }] = useUpdateUserMutation();

  return (
    <div>
      {isFetching && <RefreshIndicator />}
      <h1>{user?.name}</h1>
      <button onClick={() => updateUser({ id: userId, data: { name: "New Name" } })}>
        Update
      </button>
    </div>
  );
}
```

---

## 5. React Hook Form

The most popular form library in React. Uncontrolled inputs by default — no re-render on every keystroke.

**Install:**

```bash
npm install react-hook-form zod @hookform/resolvers
```

**Basic form:**

```tsx
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

// 1. Define schema with Zod
const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterForm = z.infer<typeof registerSchema>;

// 2. Use the form
export function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty, isValid },
    watch,
    reset,
    setError,
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" },
    mode: "onBlur", // validate on blur (options: onChange, onSubmit, onTouched)
  });

  async function onSubmit(data: RegisterForm) {
    try {
      await registerUser(data);
      reset(); // clear form after success
    } catch (error) {
      // Set server-side error on specific field
      setError("email", { message: "Email already taken" });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input
          {...register("name")}
          placeholder="Name"
          aria-invalid={!!errors.name}
        />
        {errors.name && <span>{errors.name.message}</span>}
      </div>

      <div>
        <input
          {...register("email")}
          type="email"
          placeholder="Email"
        />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <input
          {...register("password")}
          type="password"
          placeholder="Password"
        />
        {errors.password && <span>{errors.password.message}</span>}
      </div>

      <button
        type="submit"
        disabled={isSubmitting || !isDirty || !isValid}
      >
        {isSubmitting ? "Registering..." : "Register"}
      </button>
    </form>
  );
}
```

**Advanced: dynamic fields with useFieldArray:**

```tsx
import { useFieldArray, useForm } from "react-hook-form";

interface InvoiceForm {
  clientName: string;
  lineItems: { description: string; amount: number }[];
}

export function InvoiceBuilder() {
  const { register, control, handleSubmit, watch } = useForm<InvoiceForm>({
    defaultValues: {
      clientName: "",
      lineItems: [{ description: "", amount: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "lineItems",
  });

  const lineItems = watch("lineItems");
  const total = lineItems.reduce((sum, item) => sum + (item.amount || 0), 0);

  return (
    <form onSubmit={handleSubmit(console.log)}>
      <input {...register("clientName")} placeholder="Client name" />

      {fields.map((field, index) => (
        <div key={field.id}>
          <input
            {...register(`lineItems.${index}.description`)}
            placeholder="Description"
          />
          <input
            {...register(`lineItems.${index}.amount`, { valueAsNumber: true })}
            type="number"
            placeholder="Amount"
          />
          <button type="button" onClick={() => remove(index)}>
            Remove
          </button>
        </div>
      ))}

      <button type="button" onClick={() => append({ description: "", amount: 0 })}>
        + Add Line Item
      </button>

      <p>Total: ${total}</p>
      <button type="submit">Send Invoice</button>
    </form>
  );
}
```

---

## 6. Jotai — Atomic State

Jotai is the atomic state model — instead of one big store, you create small independent atoms. React only re-renders components that subscribe to a changed atom.

**Install:**

```bash
npm install jotai
```

```tsx
import { atom, useAtom, useAtomValue, useSetAtom } from "jotai";
import { atomWithStorage } from "jotai/utils";

// Primitive atoms
const countAtom = atom(0);
const nameAtom = atom("Alice");

// Derived atom — recomputes when countAtom changes
const doubleCountAtom = atom((get) => get(countAtom) * 2);

// Async atom — like a query
const userAtom = atom(async () => {
  const res = await fetch("/api/user");
  return res.json();
});

// Persistent atom (writes to localStorage)
const themeAtom = atomWithStorage<"light" | "dark">("theme", "light");

// Component that only re-renders when countAtom changes
function Counter() {
  const [count, setCount] = useAtom(countAtom);
  const double = useAtomValue(doubleCountAtom); // read-only

  return (
    <div>
      <p>Count: {count}</p>
      <p>Double: {double}</p>
      <button onClick={() => setCount((c) => c + 1)}>+1</button>
    </div>
  );
}

// Component that only sets — never re-renders from countAtom changes
function IncrementButton() {
  const increment = useSetAtom(countAtom); // no re-renders from reads

  return <button onClick={() => increment((c) => c + 1)}>Increment</button>;
}
```

---

## 7. Library Comparison — When to Use What

```
What do you need?

Server data (API calls, loading states, caching)
  → TanStack Query      (complex apps, many mutations)
  → SWR                 (simple apps, Next.js, smaller bundle)
  → RTK Query           (already using Redux)

Client global state (auth, cart, UI state, theme)
  → Zustand             (most cases — simple API, great performance)
  → Jotai               (fine-grained, atoms-based, minimal re-renders)
  → Redux Toolkit       (large teams, time-travel debugging, existing Redux)
  → Context API         (small apps, prop drilling fix, no frequent updates)

Forms
  → React Hook Form     (90% of cases — uncontrolled, performant)
  → Formik              (legacy codebases)
  → TanStack Form       (complex forms with server integration)
```

**Bundle size comparison:**

| Library | Min+gzip |
|---|---|
| Zustand | ~1KB |
| Jotai | ~3KB |
| SWR | ~4KB |
| React Hook Form | ~9KB |
| TanStack Query | ~13KB |
| Redux Toolkit | ~18KB |

---

## 8. Interview Questions & Answers

### TanStack Query

**Q: What is the difference between `isLoading` and `isFetching`?**

> `isLoading` is true only on the very first fetch when there is no cached data at all. `isFetching` is true during any fetch — initial or background. A common pattern is to show a full-page spinner for `isLoading` and a subtle indicator (spinner in the corner) for `isFetching`.

**Q: What does `staleTime` do? What happens when data becomes stale?**

> `staleTime` is how long data is considered fresh. During this window, no refetch happens even if you mount the component again. Once data is stale, the next trigger (component mount, window focus, network reconnect) will fire a background refetch. The user still sees the stale data immediately — the update is silent.

**Q: What is `gcTime` (formerly `cacheTime`)?**

> `gcTime` is how long unused data stays in memory. If no component is subscribed to `["user", 1]` for 5 minutes (default), the cache entry is garbage collected. If a component subscribes again, it fetches fresh. Separate from `staleTime` — data can be stale but still in memory.

**Q: How do you handle optimistic updates safely?**

> Three steps: 1) `onMutate` — cancel in-flight queries, snapshot current cache, apply optimistic change. 2) `onError` — restore the snapshot from context. 3) `onSettled` — invalidate to sync with server truth regardless of success or failure.

**Q: What is query key structure and why use arrays?**

> Query keys uniquely identify cached data. Arrays let you namespace: `["user"]` matches all user queries, `["user", 1]` is specific to user 1. `invalidateQueries({ queryKey: ["user"] })` invalidates all user-related caches with one call.

---

### Zustand

**Q: Why is Zustand better than Context API for global state?**

> Context API re-renders every consumer when any part of context changes. Zustand uses selector subscriptions — a component only re-renders when the specific slice it subscribes to changes. `useAuthStore((state) => state.user.name)` only re-renders when `name` changes, not when `token` changes.

**Q: How do you persist Zustand state?**

> Use the `persist` middleware. It wraps the store and syncs the state to `localStorage` (or any storage). The `partialize` option lets you choose which state slices to persist.

---

### SWR vs TanStack Query

**Q: When would you choose SWR over TanStack Query?**

> SWR when: building a Next.js app (same vendor, tight integration), bundle size matters, the app is mostly read-heavy with simple mutations. TanStack Query when: complex mutation patterns (optimistic updates, rollbacks), you need the devtools, or the app has many interdependent queries.

---

### React Hook Form

**Q: Why is React Hook Form more performant than Formik?**

> React Hook Form uses uncontrolled inputs — it reads values from DOM refs rather than React state. Formik uses controlled inputs, which trigger a re-render on every keystroke. In a form with 20 fields, React Hook Form causes zero re-renders while typing; Formik re-renders the entire form on every character.

**Q: How do you integrate server-side validation errors?**

> Use the `setError` function returned by `useForm`. After a failed API call, call `setError("email", { message: "Email already taken" })` to attach the server error to the specific field. The form displays it alongside client-side errors automatically.

---

*References:*
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [SWR Docs](https://swr.vercel.app)
- [Zustand Docs](https://zustand-demo.pmnd.rs)
- [RTK Query Docs](https://redux-toolkit.js.org/rtk-query/overview)
- [React Hook Form Docs](https://react-hook-form.com)
- [Jotai Docs](https://jotai.org)
