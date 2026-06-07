# Frontend System Design

## The System Design Interview Framework

Every frontend system design interview should be approached with a structured framework. Interviewers evaluate your ability to think holistically, not just code a component.

### Step-by-Step Framework

**1. Requirements Gathering (3-5 minutes)**

- Functional requirements: What does the user see and do?
- Non-functional requirements: Performance, accessibility, offline support, SEO, i18n?
- Constraints: Browser support, mobile-first, existing design system?
- Scale: How many users? How much data? How frequent are updates?

**2. Component Architecture (5-8 minutes)**

- Break the UI into a component tree
- Identify shared/reusable components vs page-specific ones
- Determine component boundaries and responsibilities
- Decide on controlled vs uncontrolled components

**3. Data Flow (5-8 minutes)**

- Where does state live? Local, lifted, or global?
- What is the data fetching strategy?
- How do components communicate?
- What is the caching strategy?

**4. API Design (3-5 minutes)**

- What endpoints are needed?
- Request/response shapes
- Pagination strategy
- Error responses

**5. Performance (3-5 minutes)**

- Lazy loading, code splitting
- Virtualization for long lists
- Debouncing/throttling
- Memoization strategy

**6. Edge Cases & Error Handling (2-3 minutes)**

- Network failures, retry logic
- Race conditions
- Empty states, loading states
- Concurrent modifications

---

## Design Patterns

### Container / Presentational Pattern

Separates data-fetching logic from rendering logic. The container handles state and side effects; the presentational component is a pure function of props.

```tsx
// Container: owns data fetching and state
function UserListContainer() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers().then((data) => {
      setUsers(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <Skeleton count={5} />;
  return <UserList users={users} />;
}

// Presentational: pure rendering, easily testable
function UserList({ users }: { users: User[] }) {
  return (
    <ul>
      {users.map((u) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}
```

**Tradeoff:** With hooks, the boundary between container and presentational blurs. Custom hooks now often replace container components. The pattern is still valuable for complex UIs where you want strict separation for testing.

### Compound Components

Allows a parent component to implicitly share state with its children, giving consumers flexible composition while the parent controls coordination.

```tsx
const Tabs = ({ children, defaultIndex = 0 }) => {
  const [activeIndex, setActiveIndex] = useState(defaultIndex);
  return (
    <TabsContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div role="tablist">{children}</div>
    </TabsContext.Provider>
  );
};

const Tab = ({ index, children }) => {
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
};

const TabPanel = ({ index, children }) => {
  const { activeIndex } = useContext(TabsContext);
  if (activeIndex !== index) return null;
  return <div role="tabpanel">{children}</div>;
};

// Usage: flexible composition
<Tabs defaultIndex={0}>
  <Tab index={0}>Profile</Tab>
  <Tab index={1}>Settings</Tab>
  <TabPanel index={0}><ProfilePage /></TabPanel>
  <TabPanel index={1}><SettingsPage /></TabPanel>
</Tabs>
```

**Pitfall:** If you rely solely on `React.Children.map` to inject props, it breaks when consumers wrap children in fragments or intermediate elements. Context-based compound components avoid this problem entirely.

### Render Props

A component takes a function as a prop (or as `children`) and calls it with internal state, delegating rendering decisions to the consumer.

```tsx
function MouseTracker({ children }: { children: (pos: { x: number; y: number }) => ReactNode }) {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const handleMove = (e: MouseEvent) => {
    setPos({ x: e.clientX, y: e.clientY });
  };

  return <div onMouseMove={handleMove}>{children(pos)}</div>;
}

// Usage
<MouseTracker>
  {({ x, y }) => <Tooltip style={{ left: x, top: y }}>Here!</Tooltip>}
</MouseTracker>
```

**Tradeoff:** Render props can cause "callback hell" when nested. Custom hooks are generally preferred today, but render props remain useful when you need to share behavior that is tightly coupled with a specific DOM subtree.

### Higher-Order Components (HOC)

A function that takes a component and returns a new enhanced component.

```tsx
function withAuth<P extends object>(WrappedComponent: ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { user, loading } = useAuth();

    if (loading) return <Spinner />;
    if (!user) return <Navigate to="/login" />;

    return <WrappedComponent {...props} />;
  };
}

const ProtectedDashboard = withAuth(Dashboard);
```

**Pitfalls:**
- Props collision: if the HOC and the wrapped component both expect a prop named `data`, one overwrites the other.
- Ref forwarding: HOCs swallow refs unless you explicitly use `React.forwardRef`.
- Debugging: The component tree shows the wrapper name, not the original. Use `displayName` to fix.
- Static methods on the original component are lost unless copied with `hoist-non-react-statics`.

### Hooks Pattern

Custom hooks extract reusable stateful logic without changing component hierarchy.

```tsx
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

function useIntersectionObserver(
  ref: RefObject<Element>,
  options?: IntersectionObserverInit
) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, options]);

  return isIntersecting;
}
```

---

## Component Library Design

### API Design Principles

A well-designed component API should be:

- **Minimal but sufficient:** Expose only the props consumers actually need. Avoid god-components with 30+ props.
- **Consistent:** Similar components should have similar prop names (`size`, `variant`, `disabled`).
- **Composable:** Prefer composition over configuration. Instead of `<Card showHeader showFooter headerTitle="..." />`, use `<Card><Card.Header>...</Card.Header><Card.Body>...</Card.Body></Card>`.
- **Accessible by default:** ARIA attributes should be handled internally. Consumers should not need to remember to add `role` or `aria-label` for standard interactions.

```tsx
// Bad: configuration-heavy API
<Select
  options={options}
  isMulti
  isSearchable
  isClearable
  menuPlacement="top"
  closeMenuOnSelect={false}
  hideSelectedOptions
  formatOptionLabel={customFormatter}
/>

// Better: composable API
<Select value={value} onChange={onChange} multiple>
  <Select.Trigger>
    <Select.Value placeholder="Choose..." />
  </Select.Trigger>
  <Select.Content position="top">
    {options.map((opt) => (
      <Select.Item key={opt.value} value={opt.value}>
        {opt.label}
      </Select.Item>
    ))}
  </Select.Content>
</Select>
```

### Accessibility in Component Libraries

Every interactive component must:

1. Be operable via keyboard alone (Tab, Enter, Space, Escape, Arrow keys)
2. Have proper ARIA roles and states (`aria-expanded`, `aria-selected`, `aria-disabled`)
3. Manage focus correctly (trap focus in modals, return focus on close)
4. Announce dynamic content changes via live regions (`aria-live`)

```tsx
function Dialog({ open, onClose, title, children }) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      previousFocus.current = document.activeElement as HTMLElement;
      dialogRef.current?.focus();
    } else {
      previousFocus.current?.focus();
    }
  }, [open]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") trapFocus(e, dialogRef.current);
    };
    if (open) document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="dialog-overlay" onClick={onClose}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>{title}</h2>
        {children}
      </div>
    </div>,
    document.body
  );
}
```

---

## Data Flow Architecture

### Unidirectional Data Flow

React enforces unidirectional data flow: data flows down via props, events flow up via callbacks. This makes state changes predictable and debuggable.

```
  [App State]
      |
      v (props)
  [Parent Component]
      |         ^
      v (props) | (callbacks)
  [Child Component]
```

### Flux / Redux Pattern

The Flux pattern formalizes unidirectional flow:

```
Action -> Dispatcher -> Store -> View -> Action
```

In Redux: `dispatch(action) -> reducer(state, action) -> newState -> re-render`.

**When to use Redux (or Zustand, Jotai):**
- Multiple unrelated components need the same data
- State changes need to be auditable/replayable
- Complex state transitions with many edge cases

**When NOT to use global state:**
- Data is only used by one component subtree (use local state)
- Server state (use React Query / SWR instead)
- URL-derived state (use the router)

---

## Caching Strategies

### HTTP Cache Headers

```
Cache-Control: public, max-age=31536000, immutable  (static assets with hash)
Cache-Control: no-cache                              (always revalidate)
Cache-Control: private, max-age=0, must-revalidate   (user-specific, always fresh)
ETag: "abc123"                                        (conditional requests)
```

### Stale-While-Revalidate (SWR Pattern)

Serve stale data instantly while fetching fresh data in the background.

```tsx
function useQuery<T>(key: string, fetcher: () => Promise<T>) {
  const cache = useRef<Map<string, T>>(new Map());
  const [data, setData] = useState<T | undefined>(cache.current.get(key));
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsValidating(true);

    fetcher().then((result) => {
      if (!cancelled) {
        cache.current.set(key, result);
        setData(result);
        setIsValidating(false);
      }
    });

    return () => { cancelled = true; };
  }, [key]);

  return { data, isValidating, isLoading: !data && isValidating };
}
```

### Optimistic Updates

Update the UI immediately before the server confirms, rolling back on failure.

```tsx
async function toggleLike(postId: string) {
  // Optimistic: update UI immediately
  setPost((prev) => ({
    ...prev,
    liked: !prev.liked,
    likeCount: prev.liked ? prev.likeCount - 1 : prev.likeCount + 1,
  }));

  try {
    await api.toggleLike(postId);
  } catch (error) {
    // Rollback on failure
    setPost((prev) => ({
      ...prev,
      liked: !prev.liked,
      likeCount: prev.liked ? prev.likeCount - 1 : prev.likeCount + 1,
    }));
    toast.error("Failed to update. Please try again.");
  }
}
```

**Pitfall:** Optimistic updates can conflict with server-pushed updates. If the server sends a WebSocket update between the optimistic write and the confirmation, you may overwrite the server's version. Use a version counter or timestamp to detect and resolve conflicts.

---

## Real-Time Updates

### WebSocket

Full-duplex persistent connection. Best for high-frequency bidirectional data (chat, collaborative editing, live games).

```tsx
function useWebSocket(url: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number>();

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };

    ws.onclose = () => {
      reconnectTimeout.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  return { messages, send };
}
```

### Server-Sent Events (SSE)

Unidirectional server-to-client stream over HTTP. Simpler than WebSocket, built-in reconnection, works with HTTP/2.

```tsx
function useSSE(url: string) {
  const [data, setData] = useState(null);

  useEffect(() => {
    const source = new EventSource(url);

    source.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, [url]);

  return data;
}
```

### Polling

Simplest approach. Use short polling for low-frequency updates when WebSocket/SSE infrastructure is unavailable.

```tsx
function usePolling<T>(fetcher: () => Promise<T>, intervalMs: number) {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      const result = await fetcher();
      if (active) setData(result);
    };

    poll();
    const id = setInterval(poll, intervalMs);

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [fetcher, intervalMs]);

  return data;
}
```

**Comparison Table:**

| Mechanism | Direction | Latency | Complexity | Use Case |
|-----------|-----------|---------|------------|----------|
| WebSocket | Bidirectional | ~ms | High | Chat, games, collab editing |
| SSE | Server -> Client | ~ms | Low | Notifications, feeds |
| Polling | Request/Response | interval | Low | Dashboards, status checks |

---

## Internationalization (i18n)

Key concerns: text translation, date/number formatting, RTL layout, pluralization.

```tsx
// Using react-intl / FormatJS
const messages = {
  en: {
    "cart.items": "{count, plural, one {# item} other {# items}} in cart",
    "cart.total": "Total: {total, number, currency}",
  },
  ja: {
    "cart.items": "カートに{count}個の商品",
    "cart.total": "合計: {total, number, currency}",
  },
};

function CartSummary({ count, total }) {
  const intl = useIntl();
  return (
    <p>
      {intl.formatMessage({ id: "cart.items" }, { count })}
      {" - "}
      {intl.formatMessage({ id: "cart.total" }, { total })}
    </p>
  );
}
```

**Pitfalls:**
- String concatenation breaks in languages with different word order. Always use parameterized messages.
- CSS assumptions (left alignment, padding direction) break for RTL languages. Use logical properties (`margin-inline-start` instead of `margin-left`).
- Date formats vary wildly. Never hardcode formats; use `Intl.DateTimeFormat`.

---

## Error Handling Strategy

### Error Boundaries

```tsx
class ErrorBoundary extends React.Component<
  { fallback: ReactNode; children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    reportToErrorTracking(error, info.componentStack);
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

// Granular boundaries: isolate failures to the smallest reasonable subtree
<ErrorBoundary fallback={<p>Feed failed to load.</p>}>
  <NewsFeed />
</ErrorBoundary>
<ErrorBoundary fallback={<p>Sidebar unavailable.</p>}>
  <Sidebar />
</ErrorBoundary>
```

### Retry Logic with Exponential Backoff

```tsx
async function fetchWithRetry(url: string, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      const delay = Math.min(1000 * 2 ** attempt, 10000);
      const jitter = delay * (0.5 + Math.random() * 0.5);
      await new Promise((resolve) => setTimeout(resolve, jitter));
    }
  }
}
```

### Graceful Degradation

Show partial UI when a non-critical service fails rather than a blank page. If the recommendation engine is down, still show the main content. If analytics fail, do not block the user flow.

---

## System Design Walkthrough 1: Autocomplete / Typeahead

### Requirements

- User types in an input; suggestions appear after a short delay
- Support keyboard navigation (arrow keys, Enter to select, Escape to close)
- Handle high-traffic: debounce requests, cancel stale requests
- Accessible: ARIA combobox pattern
- Support both synchronous (local filter) and asynchronous (API) data sources

### Component Tree

```
<Autocomplete>
  <Input />
  <SuggestionList>
    <SuggestionItem />
    <SuggestionItem />
    ...
  </SuggestionList>
</Autocomplete>
```

### State Management

```tsx
interface AutocompleteState {
  query: string;
  suggestions: string[];
  highlightedIndex: number;
  isOpen: boolean;
  isLoading: boolean;
}
```

State lives in the `Autocomplete` component. `useReducer` is preferred over multiple `useState` calls because state transitions are interdependent (e.g., changing query should reset highlightedIndex).

### Implementation

```tsx
function Autocomplete({ fetchSuggestions, onSelect }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debouncedQuery = useDebounce(state.query, 300);

  useEffect(() => {
    if (!debouncedQuery) {
      dispatch({ type: "CLEAR" });
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    dispatch({ type: "LOADING" });
    fetchSuggestions(debouncedQuery, controller.signal)
      .then((results) => dispatch({ type: "SUCCESS", payload: results }))
      .catch((err) => {
        if (err.name !== "AbortError") dispatch({ type: "ERROR" });
      });
  }, [debouncedQuery, fetchSuggestions]);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        dispatch({ type: "HIGHLIGHT_NEXT" });
        break;
      case "ArrowUp":
        e.preventDefault();
        dispatch({ type: "HIGHLIGHT_PREV" });
        break;
      case "Enter":
        if (state.highlightedIndex >= 0) {
          onSelect(state.suggestions[state.highlightedIndex]);
          dispatch({ type: "SELECT" });
        }
        break;
      case "Escape":
        dispatch({ type: "CLOSE" });
        inputRef.current?.blur();
        break;
    }
  };

  return (
    <div role="combobox" aria-expanded={state.isOpen} aria-haspopup="listbox">
      <input
        ref={inputRef}
        value={state.query}
        onChange={(e) => dispatch({ type: "QUERY", payload: e.target.value })}
        onKeyDown={handleKeyDown}
        aria-autocomplete="list"
        aria-controls="suggestions-listbox"
        aria-activedescendant={
          state.highlightedIndex >= 0
            ? `suggestion-${state.highlightedIndex}`
            : undefined
        }
      />
      {state.isOpen && (
        <ul id="suggestions-listbox" role="listbox">
          {state.suggestions.map((item, i) => (
            <li
              key={item}
              id={`suggestion-${i}`}
              role="option"
              aria-selected={i === state.highlightedIndex}
              onClick={() => {
                onSelect(item);
                dispatch({ type: "SELECT" });
              }}
            >
              <HighlightMatch text={item} query={state.query} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### API Design

```
GET /api/suggestions?q=reac&limit=10
Response: { results: ["React", "React Native", "React Router"], total: 3 }
```

### Edge Cases

- Empty query: Clear suggestions, do not make API call
- Very fast typing: Debounce prevents flood; AbortController cancels stale requests
- Network failure: Show inline error, allow retry
- No results: Show "No matches found" rather than empty dropdown
- XSS: Sanitize suggestion text before rendering, especially if highlighting matches with `dangerouslySetInnerHTML`
- Click outside: Close dropdown (use `useClickOutside` hook)
- Mobile: Dropdown should not overflow viewport; consider positioning logic

---

## System Design Walkthrough 2: Infinite Scroll Feed (Twitter-like)

### Requirements

- Load posts in pages as user scrolls
- New posts appear at top without disrupting scroll position
- Support like, retweet, reply actions with optimistic updates
- Virtualize the list for memory efficiency
- Handle images, videos, embedded content

### Component Tree

```
<FeedPage>
  <NewPostBanner count={3} onClick={scrollToTop} />
  <VirtualizedList>
    <FeedItem>
      <PostHeader />
      <PostContent />
      <PostMedia />
      <PostActions />
    </FeedItem>
    ...
  </VirtualizedList>
  <LoadingSpinner />
</FeedPage>
```

### State Management

Use React Query (TanStack Query) for server state with infinite query support.

```tsx
function useFeed() {
  return useInfiniteQuery({
    queryKey: ["feed"],
    queryFn: ({ pageParam = null }) => fetchFeed({ cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}

function Feed() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useFeed();
  const observerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { rootMargin: "200px" }
    );

    if (observerRef.current) observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const posts = data?.pages.flatMap((page) => page.posts) ?? [];

  return (
    <>
      <VirtualizedList items={posts} estimateSize={() => 280}>
        {(post) => <FeedItem key={post.id} post={post} />}
      </VirtualizedList>
      <div ref={observerRef} />
      {isFetchingNextPage && <Spinner />}
    </>
  );
}
```

### API Design

```
GET /api/feed?cursor=abc123&limit=20
Response: {
  posts: [...],
  nextCursor: "def456",   // null when no more pages
  newPostCount: 3          // posts created since last fetch
}
```

Cursor-based pagination is preferred over offset-based because new posts at the top do not shift page boundaries.

### Edge Cases

- New posts while scrolling: Show a "3 new posts" banner at top; do not auto-insert (disrupts scroll position)
- Deleted posts: Remove from cache via query invalidation or optimistic removal
- Duplicate posts across pages: Deduplicate by post ID when flattening pages
- Variable-height items: Virtualization library must support dynamic measurement (`react-virtuoso`, `@tanstack/react-virtual`)
- Image loading: Use `loading="lazy"` and placeholder aspect-ratio boxes to prevent layout shift
- Memory: With thousands of posts, even virtualized lists can accumulate data. Consider dropping old pages from cache after a threshold.

---

## System Design Walkthrough 3: Real-Time Chat Application

### Requirements

- 1:1 and group messaging
- Real-time message delivery via WebSocket
- Message status (sent, delivered, read)
- Typing indicators
- Offline support: queue messages, sync on reconnect
- Media attachments (images, files)

### Component Tree

```
<ChatApp>
  <ConversationList>
    <ConversationItem />
  </ConversationList>
  <ChatWindow>
    <MessageList>
      <MessageBubble />
    </MessageList>
    <TypingIndicator />
    <MessageInput>
      <AttachmentButton />
      <SendButton />
    </MessageInput>
  </ChatWindow>
</ChatApp>
```

### State Management

```tsx
interface ChatState {
  conversations: Map<string, Conversation>;
  activeConversationId: string | null;
  messages: Map<string, Message[]>;     // keyed by conversationId
  pendingMessages: Message[];           // queued while offline
  typingUsers: Map<string, string[]>;   // conversationId -> userIds
  connectionStatus: "connected" | "reconnecting" | "offline";
}
```

Use Zustand or a dedicated chat store. Messages are too high-frequency for Redux middleware chains.

### WebSocket Protocol

```json
// Client -> Server
{ "type": "message", "conversationId": "c1", "content": "Hello", "clientId": "uuid" }
{ "type": "typing", "conversationId": "c1", "isTyping": true }
{ "type": "read", "conversationId": "c1", "lastReadMessageId": "m42" }

// Server -> Client
{ "type": "message", "conversationId": "c1", "message": { ... } }
{ "type": "typing", "conversationId": "c1", "userId": "u2", "isTyping": true }
{ "type": "status", "messageId": "m42", "status": "delivered" }
```

### Offline Support

```tsx
function useSendMessage() {
  const { connectionStatus, addPendingMessage, removePendingMessage } = useChatStore();

  return useCallback(async (conversationId: string, content: string) => {
    const clientId = crypto.randomUUID();
    const optimisticMsg = {
      id: clientId,
      conversationId,
      content,
      status: "sending",
      timestamp: Date.now(),
    };

    addPendingMessage(optimisticMsg);

    if (connectionStatus === "connected") {
      ws.send(JSON.stringify({ type: "message", conversationId, content, clientId }));
    }
    // If offline, message stays in pendingMessages and will be sent on reconnect
  }, [connectionStatus, addPendingMessage]);
}
```

### Edge Cases

- Message ordering: Use server timestamps for display order, but keep client timestamps for optimistic ordering during sends
- Reconnection: On WebSocket reconnect, fetch messages since the last known server timestamp to fill gaps
- Large groups: Throttle typing indicators (send at most once per 3 seconds)
- Media uploads: Upload file to object storage first, then send message with the URL. Show upload progress in the message bubble.
- Scroll position: When viewing older messages and new messages arrive, do not auto-scroll. Show "New messages" indicator instead.

---

## System Design Walkthrough 4: Form Builder

### Requirements

- Drag-and-drop interface to create forms
- Field types: text, number, select, checkbox, date, file upload, rich text
- Validation rules configurable per field (required, min/max, regex, custom)
- Conditional logic (show field B only if field A equals "yes")
- Preview mode and publish
- Form responses collection and basic analytics

### Component Tree

```
<FormBuilder>
  <FieldPalette />              // draggable field type cards
  <FormCanvas>                  // drop target, renders field editors
    <FieldEditor>               // configurable field with drag handle
      <FieldPreview />
      <FieldConfig />           // side panel: label, validation, conditions
    </FieldEditor>
  </FormCanvas>
  <FormPreview />               // renders the form as end users would see it
</FormBuilder>
```

### Data Model

```tsx
interface FormSchema {
  id: string;
  title: string;
  fields: FormField[];
}

interface FormField {
  id: string;
  type: "text" | "number" | "select" | "checkbox" | "date" | "file" | "richtext";
  label: string;
  placeholder?: string;
  required: boolean;
  validation?: ValidationRule[];
  options?: { label: string; value: string }[];   // for select, checkbox
  conditions?: Condition[];                         // conditional visibility
  order: number;
}

interface ValidationRule {
  type: "minLength" | "maxLength" | "min" | "max" | "pattern" | "custom";
  value: string | number;
  message: string;
}

interface Condition {
  fieldId: string;
  operator: "equals" | "notEquals" | "contains" | "greaterThan";
  value: string | number;
}
```

### State Management

```tsx
function useFormBuilder() {
  const [schema, setSchema] = useState<FormSchema>(initialSchema);

  const addField = (type: FormField["type"], atIndex: number) => {
    const newField: FormField = {
      id: crypto.randomUUID(),
      type,
      label: `New ${type} field`,
      required: false,
      order: atIndex,
    };
    setSchema((prev) => ({
      ...prev,
      fields: insertAt(prev.fields, atIndex, newField).map((f, i) => ({
        ...f,
        order: i,
      })),
    }));
  };

  const moveField = (fromIndex: number, toIndex: number) => {
    setSchema((prev) => ({
      ...prev,
      fields: reorder(prev.fields, fromIndex, toIndex).map((f, i) => ({
        ...f,
        order: i,
      })),
    }));
  };

  const updateField = (fieldId: string, updates: Partial<FormField>) => {
    setSchema((prev) => ({
      ...prev,
      fields: prev.fields.map((f) =>
        f.id === fieldId ? { ...f, ...updates } : f
      ),
    }));
  };

  return { schema, addField, moveField, updateField };
}
```

### API Design

```
POST   /api/forms                    - Create form
GET    /api/forms/:id                - Get form schema
PUT    /api/forms/:id                - Update form schema
POST   /api/forms/:id/publish        - Publish form
GET    /api/forms/:id/responses      - Get form responses (paginated)
POST   /api/forms/:id/submit         - Submit a response
```

### Edge Cases

- Circular conditions: Field A depends on Field B which depends on Field A. Detect cycles when saving conditions.
- Drag-and-drop accessibility: Provide keyboard-based reordering (move up/down buttons) as an alternative to drag-and-drop.
- Large forms: If a form has 100+ fields, the editor must virtualize the field list.
- Undo/Redo: Maintain a history stack of schema snapshots. Limit stack depth (e.g., 50 entries) to avoid memory bloat.
- Concurrent editing: If two admins edit the same form, use optimistic locking (version field on the schema) to prevent overwrites.
- Validation on render: The form renderer must evaluate conditions and validations dynamically. Use a dependency graph to determine which fields to show/validate.

---

## Interview Questions

### Q1: How would you design a performant data table that supports sorting, filtering, pagination, and column resizing for 100,000 rows?

**Answer:** Use virtualization (only render visible rows + buffer). Sorting and filtering should happen server-side if the dataset exceeds a few thousand rows. For client-side operations on moderate datasets, use Web Workers to avoid blocking the main thread. Column resizing uses pointer events and updates column widths stored in state. Pagination with cursor-based API is preferred. Memoize row rendering with `React.memo` and stable keys. Consider a headless table library like TanStack Table that separates logic from rendering.

### Q2: Explain the tradeoffs between WebSocket, SSE, and long polling for a notifications system.

**Answer:** For a notifications system where updates are infrequent (a few per minute) and unidirectional (server to client), SSE is the best fit. It auto-reconnects, works natively with HTTP/2 multiplexing, and requires no special server infrastructure. WebSocket is overkill for one-way infrequent data. Long polling wastes server resources holding open connections. However, if you already have WebSocket infrastructure for other features (e.g., chat), piggybacking notifications on the same connection reduces complexity.

### Q3: You are building a collaborative document editor. How do you handle concurrent edits?

**Answer:** Use Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs). OT transforms operations against concurrent operations to preserve intent (used by Google Docs). CRDTs are data structures that can be merged without conflicts (used by Figma). For a React implementation: maintain a local document state, send operations to the server via WebSocket, receive transformed operations from other users, and apply them. Use a library like Yjs (CRDT-based) with a React binding. The key challenge is cursor/selection management when remote edits shift text positions.

### Q4: How would you implement skeleton loading states that match the actual content layout?

**Answer:** Create skeleton variants of each component that match the dimensions and layout of the real content. Use CSS `aspect-ratio` for images and fixed heights for text lines. Animate with a shimmer gradient using CSS `@keyframes`. Colocate skeleton and real component to ensure they stay in sync. For dynamic layouts, the skeleton can use `width: random(60%, 90%)` for text lines to look natural. Avoid layout shift by ensuring the skeleton occupies the exact same space as the loaded content.

### Q5: Describe how you would implement a feature flag system for a React application.

**Answer:** Feature flags decouple deployment from release. Architecture: a React context provider fetches flag values from a backend service on mount, caching them in memory. A `useFeatureFlag('flag-name')` hook reads from context. For SSR, flags must be available at request time (fetched server-side and serialized into the initial HTML). Considerations: flag evaluation should be synchronous after initial load to avoid flicker. Support percentage rollouts by hashing `userId + flagName` to a deterministic 0-100 value. Stale flags (flags that are fully rolled out) should be cleaned up regularly to prevent "flag debt."

### Q6: How would you design the architecture for a micro-frontend dashboard where different teams own different widgets?

**Answer:** Use Module Federation (Webpack 5) or import maps to load widget bundles at runtime. Each widget is an independently deployable application that exposes a React component. A shell application handles routing, authentication, and layout. Shared dependencies (React, design system) are configured as singletons in Module Federation to avoid duplication. Communication between widgets uses a custom event bus or a shared lightweight store. CSS isolation via CSS Modules or Shadow DOM prevents style conflicts. The key challenge is versioning: if Widget A needs React 18.2 and Widget B needs 18.3, the singleton approach forces alignment. Establish a shared dependency version contract across teams.
