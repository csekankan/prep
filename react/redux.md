# Redux Deep Dive — From Zero to Production

> Everything: core concepts, modern RTK, async patterns, middleware, RTK Query, testing, and interview prep.

---

## Table of Contents

1. [Why Redux Exists — The Problem](#1-why-redux-exists--the-problem)
2. [Core Mental Model](#2-core-mental-model)
3. [Redux Fundamentals (Vanilla)](#3-redux-fundamentals-vanilla)
   - [Store](#31-store)
   - [Actions](#32-actions)
   - [Reducers](#33-reducers)
   - [Dispatch](#34-dispatch)
   - [Selectors](#35-selectors)
4. [The Redux Data Flow](#4-the-redux-data-flow)
5. [Redux Toolkit — Modern Redux](#5-redux-toolkit--modern-redux)
   - [createSlice](#51-createslice)
   - [configureStore](#52-configurestore)
   - [createAsyncThunk](#53-createasyncthunk)
   - [createEntityAdapter](#54-createentityadapter)
   - [createSelector (Reselect)](#55-createselector-reselect)
6. [Middleware](#6-middleware)
   - [What middleware is](#61-what-middleware-is)
   - [redux-thunk (built-in)](#62-redux-thunk-built-in)
   - [redux-saga](#63-redux-saga)
   - [Writing custom middleware](#64-writing-custom-middleware)
7. [RTK Query](#7-rtk-query)
   - [createApi](#71-createapi)
   - [Mutations + Cache Invalidation](#72-mutations--cache-invalidation)
   - [Optimistic Updates](#73-optimistic-updates)
   - [Streaming / Polling](#74-streaming--polling)
8. [React-Redux Hooks](#8-react-redux-hooks)
9. [Redux DevTools](#9-redux-devtools)
10. [Patterns & Best Practices](#10-patterns--best-practices)
11. [Testing Redux](#11-testing-redux)
12. [Redux vs Zustand vs Context — When to Use What](#12-redux-vs-zustand-vs-context--when-to-use-what)
13. [Interview Questions & Answers](#13-interview-questions--answers)

---

## 1. Why Redux Exists — The Problem

### Props drilling

```
App
 └── Dashboard
      └── Sidebar
           └── UserAvatar  ← needs user data
```

To pass `user` to `UserAvatar`, you thread it through every layer:

```tsx
<App user={user}>
  <Dashboard user={user}>
    <Sidebar user={user}>
      <UserAvatar user={user} />   // finally here
```

Change the shape of `user`? Update every layer. Add another deep component? Thread again.

### Shared state between siblings

```
CartIcon (header)         CartPage (body)
    │                          │
    └──── both need cart ──────┘
          but they're siblings — no parent owns both
```

Neither component is an ancestor of the other. Lifting state to `App` and threading down creates the same props drilling problem.

### Redux solution

One **global store** holds all shared state. Any component reads directly from it. No threading.

```
            Redux Store
           (single source of truth)
          /        |         \
    CartIcon   CartPage   OrderHistory
    (reads)    (reads +    (reads)
               writes)
```

---

## 2. Core Mental Model

Redux has exactly **3 rules:**

### Rule 1: Single source of truth

All application state lives in one JavaScript object (the store).

```js
// The entire app state is one object
{
  auth: { user: { id: 1, name: "Alice" }, token: "abc" },
  cart: { items: [...], total: 120 },
  ui: { sidebarOpen: false, theme: "dark" }
}
```

### Rule 2: State is read-only

You never mutate state directly. You describe what happened (an action), and Redux creates a new state object.

```js
// WRONG — direct mutation
state.cart.items.push(newItem);

// CORRECT — dispatch an action describing what happened
dispatch({ type: "cart/addItem", payload: newItem });
```

### Rule 3: Changes are made with pure functions (reducers)

A reducer takes the current state and an action, and returns a new state. No side effects. Same input always produces same output.

```js
function cartReducer(state, action) {
  switch (action.type) {
    case "cart/addItem":
      return { ...state, items: [...state.items, action.payload] };
    default:
      return state;
  }
}
```

---

## 3. Redux Fundamentals (Vanilla)

Understanding the raw API before RTK makes the abstractions obvious.

### 3.1 Store

The store holds state and exposes 3 methods:

```js
import { createStore } from "redux"; // legacy API — use configureStore in RTK

const store = createStore(rootReducer);

store.getState();         // read current state
store.dispatch(action);   // send an action
store.subscribe(fn);      // listen for state changes
```

### 3.2 Actions

An action is a plain object with a `type` field. Think of it as an event that something happened.

```js
// Action objects
{ type: "cart/addItem",    payload: { id: 1, name: "Shirt", price: 29 } }
{ type: "cart/removeItem", payload: 1 }          // payload is the id
{ type: "auth/login",      payload: { user, token } }
{ type: "ui/toggleSidebar" }                     // no payload needed

// Action creators — functions that return action objects
function addItem(item) {
  return { type: "cart/addItem", payload: item };
}

// Usage
store.dispatch(addItem({ id: 1, name: "Shirt", price: 29 }));
```

The `type` string convention is `"domain/eventName"`. This is just a convention — Redux doesn't enforce it — but RTK's `createSlice` generates types in this format automatically.

### 3.3 Reducers

A reducer is a pure function: `(currentState, action) → newState`

```js
const initialCartState = {
  items: [],
  total: 0,
};

function cartReducer(state = initialCartState, action) {
  switch (action.type) {
    case "cart/addItem": {
      const newItems = [...state.items, action.payload];
      return {
        ...state,
        items: newItems,
        total: newItems.reduce((sum, item) => sum + item.price, 0),
      };
    }

    case "cart/removeItem": {
      const newItems = state.items.filter((item) => item.id !== action.payload);
      return {
        ...state,
        items: newItems,
        total: newItems.reduce((sum, item) => sum + item.price, 0),
      };
    }

    default:
      return state; // IMPORTANT: always return state for unknown actions
  }
}
```

**Combining reducers** — each reducer owns its own slice of state:

```js
import { combineReducers } from "redux";

const rootReducer = combineReducers({
  cart: cartReducer,      // state.cart → cartReducer manages this
  auth: authReducer,      // state.auth → authReducer manages this
  ui: uiReducer,          // state.ui → uiReducer manages this
});

// Store shape:
// {
//   cart: { items: [], total: 0 },
//   auth: { user: null, token: null },
//   ui: { sidebarOpen: false }
// }
```

### 3.4 Dispatch

`dispatch` is how you send an action to the store.

```js
// Synchronous dispatch
store.dispatch({ type: "cart/addItem", payload: item });

// After dispatch:
// 1. Redux calls cartReducer(currentState, action)
// 2. Reducer returns new state
// 3. Store saves new state
// 4. All subscribers (React components) are notified
```

### 3.5 Selectors

A selector is a function that extracts a specific piece of state.

```js
// Simple selectors
const selectCart = (state) => state.cart;
const selectCartItems = (state) => state.cart.items;
const selectCartTotal = (state) => state.cart.total;
const selectItemCount = (state) => state.cart.items.length;
const selectIsLoggedIn = (state) => !!state.auth.token;

// Usage with useSelector
const total = useSelector(selectCartTotal);
const isLoggedIn = useSelector(selectIsLoggedIn);
```

Selectors keep component code clean — no inline `state.cart.items.length` all over the place.

---

## 4. The Redux Data Flow

This is the most important thing to understand about Redux:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   User clicks "Add to Cart"                                 │
│          │                                                  │
│          ▼                                                  │
│   Component calls dispatch(addItem(product))                │
│          │                                                  │
│          ▼                                                  │
│   Middleware (thunk, logger, etc.)                          │
│   processes the action                                      │
│          │                                                  │
│          ▼                                                  │
│   Reducer receives (currentState, action)                   │
│   returns NEW state object                                  │
│          │                                                  │
│          ▼                                                  │
│   Store saves new state                                     │
│          │                                                  │
│          ▼                                                  │
│   React re-renders components                               │
│   whose selected state changed                              │
│          │                                                  │
│          ▼                                                  │
│   CartIcon shows new item count                             │
│   CartPage shows new item in list                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** State flows in one direction — down. Components never directly talk to each other. They talk to the store.

```
Component A ─── dispatch ──► Store ◄─── dispatch ─── Component B
                                │
                            new state
                           /         \
              Component A              Component B
              re-renders               re-renders
```

---

## 5. Redux Toolkit — Modern Redux

RTK is the official, recommended way to write Redux. It eliminates boilerplate.

**Install:**

```bash
npm install @reduxjs/toolkit react-redux
```

### 5.1 createSlice

`createSlice` replaces: action types, action creators, and reducer — all in one.

```tsx
// features/cart/cartSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface CartItem {
  id: number;
  name: string;
  price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  coupon: string | null;
}

const initialState: CartState = {
  items: [],
  coupon: null,
};

const cartSlice = createSlice({
  name: "cart",                    // prefix for action types
  initialState,
  reducers: {
    // RTK uses immer under the hood — you CAN mutate state directly here
    addItem(state, action: PayloadAction<Omit<CartItem, "quantity">>) {
      const existing = state.items.find((item) => item.id === action.payload.id);
      if (existing) {
        existing.quantity += 1;    // direct mutation — immer handles this
      } else {
        state.items.push({ ...action.payload, quantity: 1 });
      }
    },

    removeItem(state, action: PayloadAction<number>) {
      state.items = state.items.filter((item) => item.id !== action.payload);
    },

    updateQuantity(
      state,
      action: PayloadAction<{ id: number; quantity: number }>
    ) {
      const item = state.items.find((i) => i.id === action.payload.id);
      if (item) {
        item.quantity = action.payload.quantity;
        if (item.quantity <= 0) {
          state.items = state.items.filter((i) => i.id !== action.payload.id);
        }
      }
    },

    clearCart(state) {
      state.items = [];
      state.coupon = null;
    },

    applyCoupon(state, action: PayloadAction<string>) {
      state.coupon = action.payload;
    },
  },
});

// RTK auto-generates action creators with the same names
export const { addItem, removeItem, updateQuantity, clearCart, applyCoupon } =
  cartSlice.actions;

// Selectors — co-locate with the slice
export const selectCartItems = (state: RootState) => state.cart.items;
export const selectCartTotal = (state: RootState) =>
  state.cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
export const selectCartItemCount = (state: RootState) =>
  state.cart.items.reduce((sum, item) => sum + item.quantity, 0);

export default cartSlice.reducer;
```

**What RTK generated automatically:**

```js
// These are created for you by createSlice:
cartSlice.actions.addItem({ id: 1, name: "Shirt", price: 29 })
// → { type: "cart/addItem", payload: { id: 1, name: "Shirt", price: 29 } }

cartSlice.actions.clearCart()
// → { type: "cart/clearCart" }
```

### 5.2 configureStore

```tsx
// app/store.ts
import { configureStore } from "@reduxjs/toolkit";
import cartReducer from "../features/cart/cartSlice";
import authReducer from "../features/auth/authSlice";
import { userApi } from "../services/userApi";

export const store = configureStore({
  reducer: {
    cart: cartReducer,
    auth: authReducer,
    [userApi.reducerPath]: userApi.reducer, // RTK Query
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      userApi.middleware,  // RTK Query middleware
      loggerMiddleware,    // custom middleware
    ),
  devTools: process.env.NODE_ENV !== "production",
});

// TypeScript: infer types from store
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Type-safe hooks — use these instead of raw useSelector/useDispatch
// hooks/redux.ts
import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Wrap the app
// main.tsx
import { Provider } from "react-redux";
import { store } from "./app/store";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <Provider store={store}>
    <App />
  </Provider>
);
```

**Using the slice in a component:**

```tsx
// components/CartIcon.tsx
import { useAppSelector, useAppDispatch } from "../hooks/redux";
import { selectCartItemCount } from "../features/cart/cartSlice";
import { addItem } from "../features/cart/cartSlice";

export function CartIcon() {
  const count = useAppSelector(selectCartItemCount);
  // Only re-renders when count changes — not on every state change

  return <div>Cart ({count})</div>;
}

export function AddToCartButton({ product }) {
  const dispatch = useAppDispatch();

  return (
    <button onClick={() => dispatch(addItem(product))}>
      Add to Cart
    </button>
  );
}
```

---

### 5.3 createAsyncThunk

For async operations (API calls). The most common pattern in real apps.

```tsx
// features/auth/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";

interface AuthState {
  user: User | null;
  token: string | null;
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
}

// createAsyncThunk generates 3 action types automatically:
// auth/login/pending   → when fetch starts
// auth/login/fulfilled → when fetch succeeds
// auth/login/rejected  → when fetch fails

export const login = createAsyncThunk(
  "auth/login",  // action type prefix
  async (credentials: { email: string; password: string }, thunkAPI) => {
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        // rejectWithValue lets you control the rejected payload
        return thunkAPI.rejectWithValue(await res.json());
      }

      return await res.json(); // { user, token }
    } catch (error) {
      return thunkAPI.rejectWithValue({ message: "Network error" });
    }
  }
);

export const logout = createAsyncThunk("auth/logout", async (_, thunkAPI) => {
  await fetch("/api/auth/logout", { method: "POST" });

  // Access other state slices from within a thunk
  const userId = (thunkAPI.getState() as RootState).auth.user?.id;
  console.log(`User ${userId} logged out`);
});

const authSlice = createSlice({
  name: "auth",
  initialState: {
    user: null,
    token: null,
    status: "idle",
    error: null,
  } as AuthState,
  reducers: {
    // Synchronous reducers
    clearError(state) {
      state.error = null;
    },
  },
  // Handle async thunk lifecycle actions
  extraReducers: (builder) => {
    builder
      // login
      .addCase(login.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.token = action.payload.token;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = "failed";
        state.error = (action.payload as any)?.message ?? "Login failed";
      })
      // logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.status = "idle";
      });
  },
});

export const { clearError } = authSlice.actions;
export const selectUser = (state: RootState) => state.auth.user;
export const selectAuthStatus = (state: RootState) => state.auth.status;
export const selectAuthError = (state: RootState) => state.auth.error;
export const selectIsLoggedIn = (state: RootState) => !!state.auth.token;

export default authSlice.reducer;

// components/LoginForm.tsx
export function LoginForm() {
  const dispatch = useAppDispatch();
  const status = useAppSelector(selectAuthStatus);
  const error = useAppSelector(selectAuthError);

  async function handleSubmit(credentials) {
    // dispatch returns a promise — you can await it
    const result = await dispatch(login(credentials));

    // Check if it succeeded
    if (login.fulfilled.match(result)) {
      navigate("/dashboard");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={status === "loading"}>
        {status === "loading" ? "Signing in..." : "Sign In"}
      </button>
    </form>
  );
}
```

---

### 5.4 createEntityAdapter

For managing collections of items (lists). Gives you a normalized state + CRUD operations for free.

```tsx
// features/posts/postsSlice.ts
import { createEntityAdapter, createSlice, createAsyncThunk } from "@reduxjs/toolkit";

interface Post {
  id: number;
  title: string;
  body: string;
  authorId: number;
}

// Normalized state — looks like:
// {
//   ids: [1, 2, 3],
//   entities: { 1: { id: 1, title: "..." }, 2: {...}, ... }
// }
// O(1) lookups by id instead of O(n) array.find()

const postsAdapter = createEntityAdapter<Post>({
  sortComparer: (a, b) => b.id - a.id, // newest first
});

export const fetchPosts = createAsyncThunk("posts/fetchAll", async () => {
  const res = await fetch("/api/posts");
  return res.json() as Promise<Post[]>;
});

const postsSlice = createSlice({
  name: "posts",
  initialState: postsAdapter.getInitialState({ status: "idle" as const }),
  reducers: {
    postAdded: postsAdapter.addOne,
    postUpdated: postsAdapter.updateOne,
    postRemoved: postsAdapter.removeOne,
    postsReceived: postsAdapter.setAll,
  },
  extraReducers: (builder) => {
    builder.addCase(fetchPosts.fulfilled, (state, action) => {
      postsAdapter.setAll(state, action.payload);
      state.status = "idle";
    });
  },
});

// Auto-generated selectors from the adapter
export const {
  selectAll: selectAllPosts,
  selectById: selectPostById,
  selectIds: selectPostIds,
} = postsAdapter.getSelectors((state: RootState) => state.posts);

export default postsSlice.reducer;

// Usage
function PostDetail({ postId }) {
  const post = useAppSelector((state) => selectPostById(state, postId));
  // O(1) lookup — entities[postId] directly
}
```

---

### 5.5 createSelector (Reselect)

Memoized selectors — only recompute when their inputs change.

```tsx
import { createSelector } from "@reduxjs/toolkit"; // reselect is bundled

// Without memoization — runs on EVERY state change, even unrelated ones
const selectExpensiveComputation = (state) =>
  state.orders.items
    .filter((order) => order.status === "completed")
    .map((order) => ({ ...order, total: order.items.reduce(...) }));
    // This runs 50 times if unrelated state changes 50 times

// With createSelector — only runs when state.orders.items actually changes
const selectCompletedOrders = createSelector(
  [(state: RootState) => state.orders.items],  // input selectors
  (items) =>                                    // result function (memoized)
    items
      .filter((order) => order.status === "completed")
      .map((order) => ({ ...order, total: order.items.reduce((s, i) => s + i.price, 0) }))
);

// Parameterized selector
const selectOrdersByUser = createSelector(
  [(state: RootState) => state.orders.items, (_state, userId: number) => userId],
  (items, userId) => items.filter((order) => order.userId === userId)
);

// Usage
const orders = useAppSelector(selectCompletedOrders);
const userOrders = useAppSelector((state) => selectOrdersByUser(state, userId));
```

---

## 6. Middleware

### 6.1 What middleware is

Middleware sits between `dispatch` and the reducer. It can:
- Inspect actions
- Modify actions
- Dispatch additional actions
- Cancel actions
- Handle async work

```
dispatch(action)
     │
     ▼
┌──────────────┐
│  Middleware 1 │  (e.g., logger — logs the action)
└──────────────┘
     │
     ▼
┌──────────────┐
│  Middleware 2 │  (e.g., thunk — handles async functions)
└──────────────┘
     │
     ▼
┌──────────────┐
│   Reducer    │  (receives the final action)
└──────────────┘
     │
     ▼
   New State
```

### 6.2 redux-thunk (built-in)

Thunk is already included in RTK. It lets you dispatch **functions** instead of objects — enabling async logic.

```tsx
// Without thunk — can only dispatch plain objects
dispatch({ type: "cart/addItem", payload: item });

// With thunk — can dispatch functions (thunks)
dispatch(async (dispatch, getState) => {
  const state = getState();
  const isLoggedIn = selectIsLoggedIn(state);

  if (!isLoggedIn) {
    dispatch(showLoginModal());
    return;
  }

  dispatch(cartLoading());
  const saved = await saveCartToServer(item);
  dispatch(addItem(saved));
});
```

`createAsyncThunk` (section 5.3) is the RTK way to write thunks — it handles the boilerplate.

### 6.3 redux-saga

Redux Saga uses generator functions to handle complex async flows. More powerful than thunks for:
- Debouncing user input
- Race conditions
- Complex retry logic
- Sequences of dependent API calls

```bash
npm install redux-saga
```

```tsx
import { call, put, takeLatest, takeEvery, delay, race, take } from "redux-saga/effects";

// Saga that handles login
function* loginSaga(action) {
  try {
    const { user, token } = yield call(loginApi, action.payload); // call async fn
    yield put(loginSuccess({ user, token }));                      // dispatch action
    yield put(fetchUserProfile(user.id));                          // chain action
  } catch (error) {
    yield put(loginFailed(error.message));
  }
}

// Debounce search — wait 300ms before fetching
function* searchSaga(action) {
  yield delay(300);                              // wait 300ms
  const results = yield call(searchApi, action.payload);
  yield put(setSearchResults(results));
}

// Auto-save — save every 5 seconds while typing
function* autoSaveSaga() {
  while (true) {
    yield take("editor/contentChanged");         // wait for action
    yield delay(5000);                           // wait 5s
    const content = yield select(selectContent); // read state
    yield call(saveToServer, content);           // call API
  }
}

// Race condition — cancel slow request if user navigates away
function* fetchWithCancelSaga(action) {
  const { result, cancelled } = yield race({
    result: call(fetchData, action.payload),
    cancelled: take("navigation/pageLeft"),      // user left the page
  });

  if (cancelled) return;                         // ignore stale response
  yield put(dataLoaded(result));
}

// Root saga — watch for actions
function* rootSaga() {
  yield takeLatest("auth/loginStarted", loginSaga);     // cancel prev if new fires
  yield takeEvery("search/inputChanged", searchSaga);   // run for every action
  yield takeLatest("data/fetchRequested", fetchWithCancelSaga);
}

// Register in store
import createSagaMiddleware from "redux-saga";
const sagaMiddleware = createSagaMiddleware();

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefault) => getDefault({ thunk: false }).concat(sagaMiddleware),
});

sagaMiddleware.run(rootSaga);
```

### 6.4 Writing Custom Middleware

```tsx
// middleware/logger.ts
import { Middleware } from "@reduxjs/toolkit";

export const loggerMiddleware: Middleware = (store) => (next) => (action) => {
  if (process.env.NODE_ENV === "development") {
    console.group(`Action: ${action.type}`);
    console.log("Before:", store.getState());
    console.log("Action:", action);
    const result = next(action);  // pass to next middleware / reducer
    console.log("After:", store.getState());
    console.groupEnd();
    return result;
  }
  return next(action);
};

// middleware/analytics.ts
export const analyticsMiddleware: Middleware = () => (next) => (action) => {
  // Track specific actions to analytics
  const TRACKED_ACTIONS = ["cart/addItem", "auth/login", "order/placed"];
  if (TRACKED_ACTIONS.includes(action.type)) {
    analytics.track(action.type, action.payload);
  }
  return next(action);
};

// middleware/tokenRefresh.ts — intercept 401 errors
export const tokenRefreshMiddleware: Middleware =
  (store) => (next) => async (action) => {
    if (action.type === "api/requestFailed" && action.payload?.status === 401) {
      const refreshed = await store.dispatch(refreshToken());
      if (refreshed) {
        // Retry the original request
        store.dispatch(action.meta.originalRequest);
        return;
      }
      store.dispatch(logout());
    }
    return next(action);
  };
```

---

## 7. RTK Query

RTK Query is a full data fetching layer built into RTK. Think of it as TanStack Query but tightly integrated with Redux — your server state lives in the Redux store automatically.

### 7.1 createApi

```tsx
// services/api.ts
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const api = createApi({
  reducerPath: "api",  // key in Redux store
  baseQuery: fetchBaseQuery({
    baseUrl: "/api",
    prepareHeaders: (headers, { getState }) => {
      // Attach JWT token automatically to every request
      const token = (getState() as RootState).auth.token;
      if (token) headers.set("Authorization", `Bearer ${token}`);
      return headers;
    },
  }),

  tagTypes: ["User", "Post", "Comment"],  // cache invalidation tags

  endpoints: (builder) => ({
    // Query — GET
    getUser: builder.query<User, number>({
      query: (id) => `/users/${id}`,
      providesTags: (result, error, id) => [{ type: "User", id }],
      transformResponse: (response: ApiUser) => ({
        ...response,
        fullName: `${response.firstName} ${response.lastName}`,
      }),
    }),

    getUsers: builder.query<User[], void>({
      query: () => "/users",
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: "User" as const, id })),
              { type: "User", id: "LIST" },
            ]
          : [{ type: "User", id: "LIST" }],
    }),

    getPosts: builder.query<Post[], { page: number; limit: number }>({
      query: ({ page, limit }) => `/posts?page=${page}&limit=${limit}`,
      providesTags: ["Post"],
    }),

    // Mutation — POST
    createUser: builder.mutation<User, Omit<User, "id">>({
      query: (newUser) => ({
        url: "/users",
        method: "POST",
        body: newUser,
      }),
      invalidatesTags: [{ type: "User", id: "LIST" }],
    }),

    // Mutation — PUT
    updateUser: builder.mutation<User, { id: number; updates: Partial<User> }>({
      query: ({ id, updates }) => ({
        url: `/users/${id}`,
        method: "PUT",
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: "User", id }],
    }),

    // Mutation — DELETE
    deleteUser: builder.mutation<void, number>({
      query: (id) => ({
        url: `/users/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, id) => [
        { type: "User", id },
        { type: "User", id: "LIST" },
      ],
    }),
  }),
});

// Auto-generated hooks (named use + EndpointName + Query/Mutation)
export const {
  useGetUserQuery,
  useGetUsersQuery,
  useGetPostsQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
} = api;

// Component usage
function UserList() {
  const { data: users, isLoading, isFetching, isError } = useGetUsersQuery();

  return (
    <div>
      {isFetching && <RefreshIndicator />}
      {users?.map((user) => <UserCard key={user.id} user={user} />)}
    </div>
  );
}

function UserDetail({ userId }) {
  // Automatically uses cache if available
  const { data: user } = useGetUserQuery(userId, {
    skip: !userId,               // don't fetch if no userId
    pollingInterval: 60_000,     // refresh every 60s
    refetchOnMountOrArgChange: 30, // refetch if data older than 30s
  });

  return <div>{user?.fullName}</div>;
}
```

### 7.2 Mutations + Cache Invalidation

The `tagTypes` system is how RTK Query knows what to refetch after a mutation.

```
1. getUsers query runs → stores result in cache with tag: [{ type: "User", id: "LIST" }]
2. createUser mutation runs → invalidates tag: [{ type: "User", id: "LIST" }]
3. RTK Query sees invalidation → re-runs getUsers automatically
4. UserList component updates with new user
```

```tsx
function CreateUserForm() {
  const [createUser, { isLoading, error }] = useCreateUserMutation();

  async function handleSubmit(formData) {
    try {
      const newUser = await createUser(formData).unwrap(); // .unwrap() throws on error
      toast.success(`Created ${newUser.name}`);
    } catch (err) {
      toast.error(err.data?.message ?? "Failed to create user");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <button disabled={isLoading}>
        {isLoading ? "Creating..." : "Create User"}
      </button>
    </form>
  );
}
```

### 7.3 Optimistic Updates

```tsx
updateUser: builder.mutation<User, { id: number; updates: Partial<User> }>({
  query: ({ id, updates }) => ({
    url: `/users/${id}`,
    method: "PUT",
    body: updates,
  }),

  // Runs before the request is sent
  async onQueryStarted({ id, updates }, { dispatch, queryFulfilled }) {
    // Optimistically update the cache
    const patchResult = dispatch(
      api.util.updateQueryData("getUser", id, (draft) => {
        Object.assign(draft, updates); // immer — direct mutation
      })
    );

    try {
      await queryFulfilled; // wait for server response
    } catch {
      patchResult.undo(); // server rejected — roll back
    }
  },

  invalidatesTags: (result, error, { id }) => [{ type: "User", id }],
}),
```

### 7.4 Streaming / Polling

```tsx
// Polling — refetch every N milliseconds
function LiveDashboard() {
  const { data: metrics } = useGetMetricsQuery(undefined, {
    pollingInterval: 5000, // fetch every 5 seconds
  });

  return <MetricsChart data={metrics} />;
}

// Conditional polling — only poll when tab is active
function ActivePolling() {
  const [skipPolling, setSkipPolling] = useState(false);

  useEffect(() => {
    const handleVisibility = () => setSkipPolling(document.hidden);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  const { data } = useGetLiveDataQuery(undefined, {
    pollingInterval: skipPolling ? 0 : 3000,
  });
}

// WebSocket streaming (RTK Query advanced)
const api = createApi({
  baseQuery: fetchBaseQuery({ baseUrl: "/" }),
  endpoints: (builder) => ({
    getMessages: builder.query<Message[], string>({
      query: (roomId) => `rooms/${roomId}/messages`,

      // After initial fetch, keep cache updated via WebSocket
      async onCacheEntryAdded(roomId, { updateCachedData, cacheDataLoaded, cacheEntryRemoved }) {
        const ws = new WebSocket(`wss://api.example.com/rooms/${roomId}`);

        await cacheDataLoaded; // wait for initial HTTP response

        ws.onmessage = (event) => {
          const newMessage = JSON.parse(event.data);
          updateCachedData((draft) => {
            draft.push(newMessage); // immer — add to cached list
          });
        };

        await cacheEntryRemoved; // component unmounted — clean up
        ws.close();
      },
    }),
  }),
});
```

---

## 8. React-Redux Hooks

```tsx
import { useSelector, useDispatch, useStore } from "react-redux";

// useSelector — subscribe to state, re-renders when returned value changes
const count = useSelector((state: RootState) => state.counter.value);
const user = useSelector(selectUser); // with selector function

// Equality function — prevent re-render if reference changed but value didn't
import { shallowEqual } from "react-redux";
const { name, email } = useSelector(
  (state: RootState) => ({ name: state.auth.user?.name, email: state.auth.user?.email }),
  shallowEqual // compare object properties, not reference
);

// useDispatch — get the dispatch function
const dispatch = useDispatch<AppDispatch>();
dispatch(increment());
dispatch(login(credentials));

// useStore — direct store access (rare — prefer useSelector)
const store = useStore();
store.getState();
store.subscribe(() => console.log("state changed"));

// Batching — React 18 batches all dispatches in event handlers automatically
// In React 17 and below, use unstable_batchedUpdates for manual batching
```

---

## 9. Redux DevTools

The browser extension that makes Redux debugging powerful.

**Install the browser extension:** [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools/tree/main/extension)

**What you can do:**

```
Action log:
  Every dispatched action is listed chronologically.
  Click an action to see what it changed.

State diff:
  Shows exactly what changed in state for each action.
  Green = added, red = removed, yellow = changed.

Time travel:
  Click any past action to "jump" the store back to that moment.
  The UI updates to match that historical state.

Action replay:
  Skip, reorder, or replay actions to reproduce bugs.

Import/Export:
  Share a state snapshot with teammates to reproduce a bug exactly.
```

**Configure in store:**

```tsx
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== "production"
    ? {
        name: "My App",
        maxAge: 50,          // keep last 50 actions
        trace: true,         // include stack traces
        traceLimit: 25,
      }
    : false,
});
```

---

## 10. Patterns & Best Practices

### Slice organization (feature-based)

```
src/
├── features/
│   ├── auth/
│   │   ├── authSlice.ts         ← reducer, actions, selectors
│   │   ├── authThunks.ts        ← createAsyncThunk calls
│   │   └── LoginForm.tsx        ← component that uses the slice
│   ├── cart/
│   │   ├── cartSlice.ts
│   │   └── CartPage.tsx
│   └── posts/
│       ├── postsSlice.ts
│       └── PostList.tsx
├── services/
│   └── api.ts                   ← RTK Query createApi
├── app/
│   ├── store.ts                 ← configureStore
│   └── hooks.ts                 ← useAppSelector, useAppDispatch
```

### What goes in Redux vs local state

```
Redux (global)                   Local state (useState)
──────────────────────────────   ───────────────────────────────
Auth / user session              Form input values
Shopping cart                    Modal open/close
App theme                        Tooltip visible
Notifications list               Animation state
Shared filters/search params     Controlled input
Data from API (if using RTK Q)   Component-specific loading state
```

**Rule of thumb:** If only one component needs it, keep it local. If multiple components need it, or it survives navigation, put it in Redux.

### Avoid these mistakes

```tsx
// ❌ Deriving state in reducer — store only raw data
addCase(fetchUsers.fulfilled, (state, action) => {
  state.users = action.payload;
  state.userCount = action.payload.length;    // derive in selector instead
  state.adminUsers = action.payload.filter(u => u.role === "admin"); // same
});

// ✅ Derive in selectors
export const selectUserCount = (state) => state.users.items.length;
export const selectAdminUsers = (state) =>
  state.users.items.filter((u) => u.role === "admin");

// ❌ Storing non-serializable values in Redux
state.socket = new WebSocket("...");  // WebSocket is not serializable
state.ref = someRef.current;          // DOM refs not serializable
state.date = new Date();              // store as ISO string instead

// ✅ Store ISO strings, keep non-serializable things outside Redux
state.createdAt = new Date().toISOString();

// ❌ Fetching in reducer
addCase(someAction, (state) => {
  fetch("/api/data").then(...); // side effects in reducers forbidden
});

// ✅ Side effects in thunks or sagas
export const fetchData = createAsyncThunk("data/fetch", async () => {
  return fetch("/api/data").then(r => r.json());
});
```

---

## 11. Testing Redux

### Testing reducers (pure functions — easy)

```tsx
// features/cart/cartSlice.test.ts
import cartReducer, { addItem, removeItem, clearCart } from "./cartSlice";

describe("cartSlice", () => {
  const initialState = { items: [], coupon: null };

  it("should return initial state", () => {
    expect(cartReducer(undefined, { type: "unknown" })).toEqual(initialState);
  });

  it("should add a new item", () => {
    const item = { id: 1, name: "Shirt", price: 29 };
    const state = cartReducer(initialState, addItem(item));
    expect(state.items).toHaveLength(1);
    expect(state.items[0].quantity).toBe(1);
  });

  it("should increment quantity for existing item", () => {
    const item = { id: 1, name: "Shirt", price: 29 };
    let state = cartReducer(initialState, addItem(item));
    state = cartReducer(state, addItem(item)); // add same item again
    expect(state.items).toHaveLength(1);
    expect(state.items[0].quantity).toBe(2);
  });

  it("should clear the cart", () => {
    let state = cartReducer(initialState, addItem({ id: 1, name: "Shirt", price: 29 }));
    state = cartReducer(state, clearCart());
    expect(state.items).toHaveLength(0);
  });
});
```

### Testing selectors

```tsx
import { selectCartTotal, selectCartItemCount } from "./cartSlice";

describe("cart selectors", () => {
  const state = {
    cart: {
      items: [
        { id: 1, name: "Shirt", price: 29, quantity: 2 },
        { id: 2, name: "Pants", price: 59, quantity: 1 },
      ],
    },
  };

  it("calculates total correctly", () => {
    expect(selectCartTotal(state)).toBe(29 * 2 + 59 * 1); // 117
  });

  it("counts total items", () => {
    expect(selectCartItemCount(state)).toBe(3); // 2 + 1
  });
});
```

### Testing async thunks

```tsx
import { configureStore } from "@reduxjs/toolkit";
import { login } from "./authSlice";

// Create a real store for integration testing
function createTestStore() {
  return configureStore({ reducer: { auth: authReducer } });
}

describe("login thunk", () => {
  it("sets user on successful login", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ user: { id: 1, name: "Alice" }, token: "abc" }),
    });

    const store = createTestStore();
    await store.dispatch(login({ email: "a@a.com", password: "pass" }));

    expect(store.getState().auth.user?.name).toBe("Alice");
    expect(store.getState().auth.status).toBe("succeeded");
  });

  it("sets error on failed login", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ message: "Invalid credentials" }),
    });

    const store = createTestStore();
    await store.dispatch(login({ email: "a@a.com", password: "wrong" }));

    expect(store.getState().auth.status).toBe("failed");
    expect(store.getState().auth.error).toBe("Invalid credentials");
  });
});
```

### Testing components with Redux

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";

// Helper to render component with a real store
function renderWithStore(ui, { preloadedState = {}, ...options } = {}) {
  const store = configureStore({
    reducer: { cart: cartReducer, auth: authReducer },
    preloadedState,
  });
  return {
    store,
    ...render(<Provider store={store}>{ui}</Provider>, options),
  };
}

describe("CartIcon", () => {
  it("shows item count from store", () => {
    renderWithStore(<CartIcon />, {
      preloadedState: {
        cart: { items: [{ id: 1, quantity: 3 }] },
      },
    });
    expect(screen.getByText("Cart (3)")).toBeInTheDocument();
  });
});
```

---

## 12. Redux vs Zustand vs Context — When to Use What

| Factor | Context API | Zustand | Redux Toolkit |
|---|---|---|---|
| Bundle size | 0KB (built-in) | ~1KB | ~18KB |
| Boilerplate | Low | Very low | Medium |
| DevTools | No | Basic | Excellent |
| Time-travel debugging | No | No | Yes |
| Middleware | No | Yes (custom) | Yes (built-in + saga) |
| Re-render control | Poor (all consumers) | Fine-grained | Fine-grained |
| Async patterns | Manual | Manual | createAsyncThunk, saga |
| Data fetching | No | No | RTK Query |
| Team scale | Small | Small-Medium | Medium-Large |
| Learning curve | Low | Low | Medium |

**Choose Context API when:**
- Small app with rare state changes
- Theming, locale, auth (read-heavy, infrequent writes)
- You want zero dependencies

**Choose Zustand when:**
- Medium app
- Simple global state — cart, user preferences, UI state
- You want Redux-like patterns without the boilerplate

**Choose Redux Toolkit when:**
- Large app with many developers
- Complex async workflows (sagas, sequential actions)
- You need time-travel debugging for complex bugs
- Already invested in Redux ecosystem
- You want RTK Query for server state

---

## 13. Interview Questions & Answers

**Q: What is the Redux data flow?**

> Component dispatches action → Middleware processes it → Reducer creates new state → Store notifies subscribers → React re-renders. One-directional, predictable, traceable.

**Q: Why can't you mutate state in a reducer?**

> Redux compares state references to detect changes. Mutating the existing object means the reference stays the same — Redux thinks nothing changed and skips re-renders. You must return a new object. RTK uses immer internally, which lets you write "mutations" in syntax but produces a new immutable object under the hood.

**Q: What is immer and why does RTK use it?**

> Immer is a library that lets you write code that looks like mutation (`state.items.push(item)`) but actually produces a new immutable state snapshot. RTK bundles it so you don't have to write verbose spread operators in every reducer.

**Q: What is the difference between a thunk and a saga?**

> Thunks are simple functions that receive `dispatch` and `getState`. They're good for straightforward async operations. Sagas are generator functions that can pause, cancel, race, and handle complex sequences. Use sagas when you need debouncing, race conditions, long-running background processes, or complex multi-step flows.

**Q: What is normalised state and why does it matter?**

> Instead of storing items as an array `[{id:1,...}, {id:2,...}]`, normalized state stores them as `{ ids: [1,2], entities: {1:{...}, 2:{...}} }`. Lookup by id is O(1) instead of O(n). Updates are simpler — change `entities[id]` without searching. `createEntityAdapter` generates this structure automatically.

**Q: What does `invalidatesTags` do in RTK Query?**

> It marks cache entries as stale after a mutation. When a mutation with `invalidatesTags: [{ type: "User", id: 1 }]` completes, any active query that `providesTags: [{ type: "User", id: 1 }]` automatically refetches. It's how RTK Query keeps queries and mutations in sync without manual `invalidateQueries` calls.

**Q: When would you use `setQueryData` vs `invalidatesTags`?**

> `setQueryData` (or `updateQueryData`) directly updates the cache — no network request. Use it when you already have the new data (e.g., mutation returns the full updated resource). `invalidatesTags` triggers a refetch — use it when you don't have the new data in the mutation response and need the server's latest version.

**Q: What is the purpose of `prepareHeaders` in RTK Query's `fetchBaseQuery`?**

> It runs before every request and lets you attach headers globally — typically the `Authorization: Bearer <token>` header. It receives the current Redux state via `getState()` so you can read the token from `state.auth.token` without threading it through every API call.

---

*References:*
- [Redux Toolkit Docs](https://redux-toolkit.js.org)
- [RTK Query Docs](https://redux-toolkit.js.org/rtk-query/overview)
- [Redux Style Guide](https://redux.js.org/style-guide/style-guide)
- [Immer Docs](https://immerjs.github.io/immer)
- [Redux Saga Docs](https://redux-saga.js.org)
