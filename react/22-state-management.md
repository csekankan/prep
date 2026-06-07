# 22. State Management in React — From Local State to Global Solutions

## Table of Contents

1. [Local State (useState / useReducer)](#local-state)
2. [Lifting State Up](#lifting-state-up)
3. [Context API](#context-api)
4. [Redux Evolution](#redux-evolution)
5. [Zustand](#zustand)
6. [Jotai](#jotai)
7. [Recoil](#recoil)
8. [MobX](#mobx)
9. [React Query / TanStack Query](#react-query--tanstack-query)
10. [State Categories](#state-categories)
11. [Counter App Comparison (Context vs Redux Toolkit vs Zustand)](#counter-app-comparison)
12. [Decision Framework](#decision-framework)
13. [Interview Questions](#interview-questions)

---

## Local State

### useState

For simple, component-scoped state:

```jsx
function Toggle() {
  const [isOn, setIsOn] = useState(false);

  return (
    <button onClick={() => setIsOn(prev => !prev)}>
      {isOn ? 'ON' : 'OFF'}
    </button>
  );
}
```

### useReducer

For complex state logic with multiple sub-values or when the next state depends on the previous one:

```jsx
const initialState = { count: 0, step: 1 };

function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step };
    case 'decrement':
      return { ...state, count: state.count - state.step };
    case 'setStep':
      return { ...state, step: action.payload };
    case 'reset':
      return initialState;
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <div>
      <p>Count: {state.count} (step: {state.step})</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
      <input
        type="number"
        value={state.step}
        onChange={e => dispatch({ type: 'setStep', payload: Number(e.target.value) })}
      />
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
    </div>
  );
}
```

### When to Use useReducer Over useState

| Scenario | Prefer |
|----------|--------|
| Single boolean or primitive | `useState` |
| Related state values that change together | `useReducer` |
| Complex state transitions with validation | `useReducer` |
| State machine (finite states + transitions) | `useReducer` |
| Passing update logic to child components | `useReducer` (pass `dispatch` instead of multiple callbacks) |

---

## Lifting State Up

When siblings need to share state, move it to their closest common ancestor:

```jsx
function Parent() {
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div>
      <Sidebar items={items} selectedId={selectedId} onSelect={setSelectedId} />
      <Detail itemId={selectedId} />
    </div>
  );
}
```

**The problem:** As the app grows, state gets lifted higher and higher, eventually sitting in the root component. This leads to "prop drilling" -- passing props through many intermediate components that do not use them.

---

## Context API

### Basic Usage

```jsx
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext('light');

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

function Header() {
  const { theme, setTheme } = useTheme();
  return (
    <header className={theme}>
      <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
        Toggle Theme
      </button>
    </header>
  );
}
```

### Limitations of Context as State Management

**Problem 1: Any value change re-renders ALL consumers.**

```jsx
const AppContext = createContext();

function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  const [notifications, setNotifications] = useState([]);

  return (
    <AppContext.Provider value={{ user, setUser, theme, setTheme, notifications, setNotifications }}>
      {children}
    </AppContext.Provider>
  );
}

// PROBLEM: When `notifications` changes, EVERY component consuming
// AppContext re-renders, even those only using `theme`.
function ThemeButton() {
  const { theme } = useContext(AppContext);
  console.log('ThemeButton rendered'); // fires on notification changes too!
  return <button className={theme}>Click</button>;
}
```

**Mitigation:** Split into multiple contexts:

```jsx
const UserContext = createContext();
const ThemeContext = createContext();
const NotificationContext = createContext();

function AppProvider({ children }) {
  return (
    <UserProvider>
      <ThemeProvider>
        <NotificationProvider>
          {children}
        </NotificationProvider>
      </ThemeProvider>
    </UserProvider>
  );
}
```

**Problem 2: No built-in middleware, devtools, or time-travel debugging.**

**Problem 3: Context value identity changes on every render unless memoized.**

```jsx
// BAD: new object every render -> all consumers re-render
function Provider({ children }) {
  const [count, setCount] = useState(0);
  return (
    <CountContext.Provider value={{ count, setCount }}>
      {children}
    </CountContext.Provider>
  );
}

// GOOD: memoize the value
function Provider({ children }) {
  const [count, setCount] = useState(0);
  const value = useMemo(() => ({ count, setCount }), [count]);
  return (
    <CountContext.Provider value={value}>
      {children}
    </CountContext.Provider>
  );
}
```

---

## Redux Evolution

### Classic Redux (Pre-2019)

Verbose boilerplate: action types, action creators, reducers, manual immutability, `connect()` HOC.

```jsx
// Action types
const INCREMENT = 'INCREMENT';
const DECREMENT = 'DECREMENT';

// Action creators
const increment = () => ({ type: INCREMENT });
const decrement = () => ({ type: DECREMENT });

// Reducer
function counterReducer(state = { count: 0 }, action) {
  switch (action.type) {
    case INCREMENT:
      return { ...state, count: state.count + 1 };
    case DECREMENT:
      return { ...state, count: state.count - 1 };
    default:
      return state;
  }
}

// Store
const store = createStore(counterReducer, applyMiddleware(thunk));
```

### Redux Toolkit (RTK)

RTK is now the official recommended way to write Redux. It reduces boilerplate dramatically.

```jsx
import { createSlice, configureStore } from '@reduxjs/toolkit';

const counterSlice = createSlice({
  name: 'counter',
  initialState: { count: 0 },
  reducers: {
    increment(state) {
      state.count += 1; // Immer allows "mutations"
    },
    decrement(state) {
      state.count -= 1;
    },
    incrementByAmount(state, action) {
      state.count += action.payload;
    },
  },
});

export const { increment, decrement, incrementByAmount } = counterSlice.actions;

const store = configureStore({
  reducer: {
    counter: counterSlice.reducer,
  },
});

// Component
import { useSelector, useDispatch } from 'react-redux';

function Counter() {
  const count = useSelector(state => state.counter.count);
  const dispatch = useDispatch();

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => dispatch(increment())}>+</button>
      <button onClick={() => dispatch(decrement())}>-</button>
    </div>
  );
}
```

### RTK Query

Built-in data fetching and caching layer (replaces the need for thunks/sagas for API calls):

```jsx
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const api = createApi({
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  tagTypes: ['Post'],
  endpoints: (builder) => ({
    getPosts: builder.query({
      query: () => '/posts',
      providesTags: ['Post'],
    }),
    addPost: builder.mutation({
      query: (newPost) => ({
        url: '/posts',
        method: 'POST',
        body: newPost,
      }),
      invalidatesTags: ['Post'],
    }),
  }),
});

export const { useGetPostsQuery, useAddPostMutation } = api;

function PostList() {
  const { data: posts, isLoading, error } = useGetPostsQuery();
  const [addPost] = useAddPostMutation();

  if (isLoading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <div>
      <button onClick={() => addPost({ title: 'New Post' })}>Add</button>
      {posts.map(post => <PostCard key={post.id} post={post} />)}
    </div>
  );
}
```

---

## Zustand

### Minimal API, No Providers

Zustand is a small, fast state management library. No Provider wrapper needed.

```jsx
import { create } from 'zustand';

const useCounterStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}));

function Counter() {
  const count = useCounterStore((state) => state.count);
  const increment = useCounterStore((state) => state.increment);

  return (
    <div>
      <p>{count}</p>
      <button onClick={increment}>+</button>
    </div>
  );
}
```

### Zustand Features

```jsx
import { create } from 'zustand';
import { devtools, persist, immer } from 'zustand/middleware';

const useStore = create(
  devtools(
    persist(
      immer((set) => ({
        todos: [],
        addTodo: (text) =>
          set((state) => {
            state.todos.push({ id: Date.now(), text, done: false });
          }),
        toggleTodo: (id) =>
          set((state) => {
            const todo = state.todos.find(t => t.id === id);
            if (todo) todo.done = !todo.done;
          }),
      })),
      { name: 'todo-storage' }
    )
  )
);
```

**Key advantages:**
- No boilerplate, no providers, no action types.
- Selectors prevent unnecessary re-renders (only re-renders when selected slice changes).
- Middleware for devtools, persistence, immer.
- Works outside React (vanilla JS).

---

## Jotai

### Atomic State

Jotai uses atoms as the unit of state. Each atom is independently subscribable.

```jsx
import { atom, useAtom } from 'jotai';

const countAtom = atom(0);
const doubledCountAtom = atom((get) => get(countAtom) * 2); // derived atom

function Counter() {
  const [count, setCount] = useAtom(countAtom);
  const [doubled] = useAtom(doubledCountAtom);

  return (
    <div>
      <p>Count: {count}</p>
      <p>Doubled: {doubled}</p>
      <button onClick={() => setCount(c => c + 1)}>+</button>
    </div>
  );
}
```

### Async Atoms

```jsx
const userAtom = atom(async () => {
  const res = await fetch('/api/user');
  return res.json();
});

function UserProfile() {
  const [user] = useAtom(userAtom); // Suspense-compatible
  return <p>{user.name}</p>;
}
```

**Jotai vs Zustand:**
- Jotai: bottom-up (atoms compose), React-centric, Suspense integration.
- Zustand: top-down (single store), works outside React, simpler mental model.

---

## Recoil

### Atoms and Selectors

```jsx
import { atom, selector, useRecoilState, useRecoilValue, RecoilRoot } from 'recoil';

const todoListAtom = atom({
  key: 'todoList',
  default: [],
});

const todoCountSelector = selector({
  key: 'todoCount',
  get: ({ get }) => {
    const todos = get(todoListAtom);
    return {
      total: todos.length,
      completed: todos.filter(t => t.done).length,
      pending: todos.filter(t => !t.done).length,
    };
  },
});

function TodoStats() {
  const { total, completed, pending } = useRecoilValue(todoCountSelector);
  return (
    <div>
      <p>Total: {total}</p>
      <p>Completed: {completed}</p>
      <p>Pending: {pending}</p>
    </div>
  );
}

function App() {
  return (
    <RecoilRoot>
      <TodoApp />
    </RecoilRoot>
  );
}
```

**Note:** Recoil is largely in maintenance mode. Meta has shifted focus, and the community has largely moved to Jotai or Zustand.

---

## MobX

### Observable State

MobX uses observables, computed values, and reactions. It automatically tracks which observables a component uses and re-renders only when those change.

```jsx
import { makeAutoObservable } from 'mobx';
import { observer } from 'mobx-react-lite';

class CounterStore {
  count = 0;

  constructor() {
    makeAutoObservable(this);
  }

  increment() {
    this.count++;
  }

  decrement() {
    this.count--;
  }

  get doubled() {
    return this.count * 2;
  }
}

const counterStore = new CounterStore();

const Counter = observer(function Counter() {
  return (
    <div>
      <p>{counterStore.count} (doubled: {counterStore.doubled})</p>
      <button onClick={() => counterStore.increment()}>+</button>
    </div>
  );
});
```

**Tradeoffs:**
- Automatic tracking is powerful but can be "magical" and harder to debug.
- Class-based stores feel different from the hooks ecosystem.
- Great for complex, heavily interconnected state.

---

## React Query / TanStack Query

### Server State vs Client State

TanStack Query makes a critical distinction:
- **Client state:** UI state owned by the app (modals, form inputs, theme).
- **Server state:** Data that lives on the server and is cached/synchronized (API responses).

Most state management complexity comes from treating server state like client state.

```jsx
import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PostList />
    </QueryClientProvider>
  );
}

function PostList() {
  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ['posts'],
    queryFn: () => fetch('/api/posts').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,   // garbage collect after 30 min
    refetchOnWindowFocus: true,
  });

  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (newPost) =>
      fetch('/api/posts', {
        method: 'POST',
        body: JSON.stringify(newPost),
        headers: { 'Content-Type': 'application/json' },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });

  if (isLoading) return <Spinner />;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      {isFetching && <p>Refreshing...</p>}
      <button onClick={() => mutation.mutate({ title: 'New Post' })}>
        Add Post
      </button>
      {data.map(post => <PostCard key={post.id} post={post} />)}
    </div>
  );
}
```

### Key Features

- **Automatic caching and deduplication:** Multiple components requesting the same data trigger one fetch.
- **Background refetching:** Stale data is served immediately, then refetched.
- **Optimistic updates:** Update UI before the server responds.
- **Pagination and infinite scroll:** Built-in `useInfiniteQuery`.
- **Devtools:** Visual cache inspector.

---

## State Categories

```
+------------------+-------------------------+---------------------------+
| Category         | Examples                | Recommended Tool          |
+------------------+-------------------------+---------------------------+
| UI State         | Modals, tabs, toggles   | useState / useReducer     |
| Form State       | Input values, errors    | react-hook-form / useState|
| Server Cache     | API data, user profile  | TanStack Query / RTK Query|
| URL State        | Filters, pagination     | URL params (useSearchParams) |
| Global UI State  | Theme, auth, sidebar    | Context or Zustand        |
| Complex App State| Multi-step workflows    | Redux Toolkit or Zustand  |
+------------------+-------------------------+---------------------------+
```

---

## Counter App Comparison

### Implementation 1: Context API

```jsx
// counterContext.jsx
import { createContext, useContext, useReducer, useMemo } from 'react';

const CounterContext = createContext();

function counterReducer(state, action) {
  switch (action.type) {
    case 'increment': return { count: state.count + 1 };
    case 'decrement': return { count: state.count - 1 };
    case 'reset': return { count: 0 };
    default: throw new Error(`Unknown action: ${action.type}`);
  }
}

export function CounterProvider({ children }) {
  const [state, dispatch] = useReducer(counterReducer, { count: 0 });
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return (
    <CounterContext.Provider value={value}>
      {children}
    </CounterContext.Provider>
  );
}

export function useCounter() {
  const context = useContext(CounterContext);
  if (!context) throw new Error('useCounter must be used within CounterProvider');
  return context;
}

// App.jsx
function App() {
  return (
    <CounterProvider>
      <CounterDisplay />
      <CounterControls />
    </CounterProvider>
  );
}

function CounterDisplay() {
  const { state } = useCounter();
  return <p>Count: {state.count}</p>;
}

function CounterControls() {
  const { dispatch } = useCounter();
  return (
    <div>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
    </div>
  );
}
```

### Implementation 2: Redux Toolkit

```jsx
// store.js
import { configureStore, createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
  name: 'counter',
  initialState: { count: 0 },
  reducers: {
    increment: (state) => { state.count += 1; },
    decrement: (state) => { state.count -= 1; },
    reset: () => ({ count: 0 }),
  },
});

export const { increment, decrement, reset } = counterSlice.actions;
export const store = configureStore({ reducer: { counter: counterSlice.reducer } });

// App.jsx
import { Provider, useSelector, useDispatch } from 'react-redux';
import { store, increment, decrement, reset } from './store';

function App() {
  return (
    <Provider store={store}>
      <CounterDisplay />
      <CounterControls />
    </Provider>
  );
}

function CounterDisplay() {
  const count = useSelector((state) => state.counter.count);
  return <p>Count: {count}</p>;
}

function CounterControls() {
  const dispatch = useDispatch();
  return (
    <div>
      <button onClick={() => dispatch(increment())}>+</button>
      <button onClick={() => dispatch(decrement())}>-</button>
      <button onClick={() => dispatch(reset())}>Reset</button>
    </div>
  );
}
```

### Implementation 3: Zustand

```jsx
// store.js
import { create } from 'zustand';

export const useCounterStore = create((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
  decrement: () => set((s) => ({ count: s.count - 1 })),
  reset: () => set({ count: 0 }),
}));

// App.jsx
import { useCounterStore } from './store';

function App() {
  return (
    <div>
      <CounterDisplay />
      <CounterControls />
    </div>
  );
}

function CounterDisplay() {
  const count = useCounterStore((s) => s.count);
  return <p>Count: {count}</p>;
}

function CounterControls() {
  const increment = useCounterStore((s) => s.increment);
  const decrement = useCounterStore((s) => s.decrement);
  const reset = useCounterStore((s) => s.reset);
  return (
    <div>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
      <button onClick={reset}>Reset</button>
    </div>
  );
}
```

### Comparison Summary

| Aspect | Context | Redux Toolkit | Zustand |
|--------|---------|---------------|---------|
| Boilerplate | Medium | Medium | Low |
| Provider required | Yes | Yes | No |
| Devtools | No | Yes (excellent) | Yes (middleware) |
| Re-render control | Poor (all consumers) | Good (selectors) | Good (selectors) |
| Bundle size | 0 KB (built-in) | ~11 KB | ~1.5 KB |
| Learning curve | Low | Medium | Low |
| Middleware | None | Yes (thunk, saga) | Yes (devtools, persist, immer) |
| Use outside React | No | Yes (store.getState) | Yes |

---

## Decision Framework

```
START
  |
  v
Is it server data (API responses)?
  |--YES--> Use TanStack Query or RTK Query
  |
  v
Is it URL state (filters, pagination, search)?
  |--YES--> Use URL search params (useSearchParams)
  |
  v
Is it form state?
  |--YES--> Use react-hook-form or local state
  |
  v
Is it used by only one component?
  |--YES--> Use useState or useReducer
  |
  v
Is it shared by 2-3 nearby components?
  |--YES--> Lift state up
  |
  v
Is it simple global state (theme, auth)?
  |--YES--> Context API (split contexts)
  |
  v
Is it complex global state with many consumers?
  |--YES--> Do you need time-travel debugging and middleware?
       |--YES--> Redux Toolkit
       |--NO---> Zustand or Jotai
```

---

## Interview Questions

### Q1: Why is Context API not a full replacement for Redux?

**Answer:**

Context is a **dependency injection mechanism**, not a state management library. Key differences:

1. **Re-render behavior:** Context re-renders ALL consumers when the value changes, regardless of which part of the value they use. Redux and Zustand use selectors for granular subscriptions.

2. **No middleware:** Context has no built-in support for logging, async operations, or intercepting state changes. Redux has middleware (thunk, saga, RTK listener).

3. **No devtools:** Redux DevTools offer time-travel debugging, action history, state diff inspection. Context has none of this.

4. **Performance at scale:** Context works well for low-frequency updates (theme, locale, auth). For high-frequency updates (typing in a form, real-time data), it causes cascading re-renders.

Context is great for: theme, locale, authenticated user, feature flags. Use a state management library for anything more complex.

---

### Q2: Explain the difference between server state and client state. Why does this distinction matter?

**Answer:**

**Client state** is owned and controlled entirely by the frontend. Examples: whether a modal is open, which tab is selected, form input values. It is synchronous, always up-to-date, and exists only in the browser.

**Server state** is owned by the backend. Examples: user profile data, list of products, order history. It is asynchronous, potentially stale, shared across users, and requires synchronization.

**Why it matters:** Treating server state like client state leads to manually managing loading/error states, stale data, cache invalidation, deduplication, and background refetching. Libraries like TanStack Query handle all of this declaratively. An app that separates these concerns will use something like Zustand for client state and TanStack Query for server state, reducing code complexity dramatically.

---

### Q3: When would you choose Zustand over Redux Toolkit?

**Answer:**

Choose **Zustand** when:
- You want minimal boilerplate and fast setup.
- The app is small to medium-sized.
- You do not need the Redux ecosystem (sagas, complex middleware chains).
- You want to use state outside React components (e.g., in utility functions).
- Bundle size matters (Zustand is ~1.5 KB vs Redux Toolkit's ~11 KB).

Choose **Redux Toolkit** when:
- The team already knows Redux.
- You need time-travel debugging and action history.
- The app has complex async workflows (RTK listener middleware).
- You want RTK Query for data fetching with cache invalidation.
- You need strict architectural patterns (actions, reducers) for a large team.

---

### Q4: A component using useContext re-renders too often. How do you diagnose and fix it?

**Answer:**

**Diagnosis:**

1. Add `console.log('render')` or use React DevTools Profiler to confirm unnecessary renders.
2. Check what value the Context.Provider passes. If it creates a new object on every render, all consumers re-render.

**Fixes (in order of preference):**

1. **Memoize the context value:**

```jsx
const value = useMemo(() => ({ count, increment }), [count]);
```

2. **Split read and write contexts:**

```jsx
const CountContext = createContext(0);
const DispatchContext = createContext(() => {});

function Provider({ children }) {
  const [count, dispatch] = useReducer(reducer, 0);
  return (
    <CountContext.Provider value={count}>
      <DispatchContext.Provider value={dispatch}>
        {children}
      </DispatchContext.Provider>
    </CountContext.Provider>
  );
}
```

Components that only dispatch never re-render when count changes.

3. **Use `React.memo` on consumer components** to prevent re-renders from parent, combined with the above.

4. **Switch to Zustand or Jotai** if the re-render problem persists. Their selector-based subscription model only re-renders when the selected slice changes.

---

### Q5: Describe optimistic updates. Implement one with TanStack Query.

**Answer:**

An optimistic update immediately reflects the change in the UI before the server confirms it. If the server request fails, the UI rolls back to the previous state.

```jsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useLikePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (postId) =>
      fetch(`/api/posts/${postId}/like`, { method: 'POST' }),

    onMutate: async (postId) => {
      // Cancel outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: ['posts'] });

      // Snapshot the previous value
      const previousPosts = queryClient.getQueryData(['posts']);

      // Optimistically update
      queryClient.setQueryData(['posts'], (old) =>
        old.map(post =>
          post.id === postId
            ? { ...post, likes: post.likes + 1 }
            : post
        )
      );

      // Return snapshot for rollback
      return { previousPosts };
    },

    onError: (err, postId, context) => {
      // Rollback on error
      queryClient.setQueryData(['posts'], context.previousPosts);
    },

    onSettled: () => {
      // Refetch to ensure server state is in sync
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
}
```

**Key steps:**
1. Cancel in-flight queries to avoid race conditions.
2. Snapshot current data for rollback.
3. Apply the optimistic change immediately.
4. On error, restore the snapshot.
5. On success or error, refetch to ensure consistency.
