# 23. Testing React Applications

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [React Testing Library (RTL) Fundamentals](#react-testing-library-fundamentals)
3. [Queries: getBy vs queryBy vs findBy](#queries)
4. [user-event vs fireEvent](#user-event-vs-fireevent)
5. [Testing Async Operations](#testing-async-operations)
6. [Mocking](#mocking)
7. [Testing Custom Hooks](#testing-custom-hooks)
8. [Snapshot Testing](#snapshot-testing)
9. [Testing Spectrum: Unit vs Integration vs E2E](#testing-spectrum)
10. [Testing Patterns (Arrange-Act-Assert)](#testing-patterns)
11. [Testing Context Providers](#testing-context-providers)
12. [Testing Error Boundaries](#testing-error-boundaries)
13. [Full Test Examples](#full-test-examples)
14. [Scenario-Based Interview Questions](#scenario-based-interview-questions)

---

## Testing Philosophy

### Test Behavior, Not Implementation

The core principle of React Testing Library:

> "The more your tests resemble the way your software is used, the more confidence they can give you." -- Kent C. Dodds

**Bad test (testing implementation):**

```jsx
test('increments counter state', () => {
  const { result } = renderHook(() => useState(0));
  act(() => result.current[1](1));
  expect(result.current[0]).toBe(1);
});
```

This test verifies internal state. If you refactor from `useState` to `useReducer`, the test breaks even though the behavior is identical.

**Good test (testing behavior):**

```jsx
test('displays incremented count when + button is clicked', () => {
  render(<Counter />);
  const button = screen.getByRole('button', { name: '+' });

  fireEvent.click(button);

  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

This test survives any internal refactor. It only breaks if user-facing behavior changes.

### The Testing Trophy

```
            /\
           /  \
          / E2E \         Few, critical user journeys
         /--------\
        /           \
       / Integration  \   Most of your tests
      /----------------\
     /                   \
    /      Unit Tests      \  Pure logic, utilities
   /------------------------\
  /                           \
 /      Static Analysis        \  TypeScript, ESLint
/------------------------------\
```

Unlike the traditional testing pyramid (many unit, few integration), the "testing trophy" favors **integration tests** that test components with their dependencies (context, routes, child components).

---

## React Testing Library Fundamentals

### Setup

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom
```

### render and screen

```jsx
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Greeting from './Greeting';

test('renders greeting message', () => {
  render(<Greeting name="Alice" />);

  expect(screen.getByText('Hello, Alice!')).toBeInTheDocument();
});
```

**`render` returns:** An object with container, unmount, rerender, and query methods. However, prefer using `screen` for queries (it is bound to `document.body` and produces better error messages).

### cleanup

RTL automatically calls `cleanup` after each test (in Jest with `afterEach`). This unmounts components and removes the rendered DOM.

---

## Queries

### Query Types and When to Use Each

| Type | No Match | 1 Match | >1 Match | Async? |
|------|----------|---------|----------|--------|
| `getBy` | Throws | Returns element | Throws | No |
| `queryBy` | Returns `null` | Returns element | Throws | No |
| `findBy` | Throws (after timeout) | Returns element | Throws | Yes (returns Promise) |
| `getAllBy` | Throws | Returns array | Returns array | No |
| `queryAllBy` | Returns `[]` | Returns array | Returns array | No |
| `findAllBy` | Throws (after timeout) | Returns array | Returns array | Yes |

### Query Priority (Most to Least Preferred)

```
1. getByRole        -- accessible queries (what screen readers see)
2. getByLabelText   -- form fields
3. getByPlaceholderText -- when no label exists
4. getByText        -- non-interactive elements
5. getByDisplayValue -- filled-in form elements
6. getByAltText     -- images
7. getByTitle       -- title attribute
8. getByTestId      -- last resort (data-testid)
```

### Practical Examples

```jsx
function LoginForm({ onSubmit }) {
  return (
    <form onSubmit={onSubmit}>
      <label htmlFor="email">Email</label>
      <input id="email" type="email" placeholder="you@example.com" />

      <label htmlFor="password">Password</label>
      <input id="password" type="password" />

      <button type="submit">Sign In</button>
      <p className="helper-text">Forgot your password?</p>
    </form>
  );
}

test('query examples', () => {
  render(<LoginForm onSubmit={jest.fn()} />);

  // getByRole -- best for buttons, links, headings
  screen.getByRole('button', { name: 'Sign In' });

  // getByLabelText -- best for form inputs
  screen.getByLabelText('Email');
  screen.getByLabelText('Password');

  // getByPlaceholderText -- acceptable fallback
  screen.getByPlaceholderText('you@example.com');

  // getByText -- for static text content
  screen.getByText('Forgot your password?');

  // queryBy -- asserting something is NOT present
  expect(screen.queryByText('Error')).not.toBeInTheDocument();
});
```

### Common Pitfall: getBy vs queryBy for Absence

```jsx
// WRONG: getBy throws if element doesn't exist
expect(screen.getByText('Error')).not.toBeInTheDocument(); // throws before assertion!

// CORRECT: queryBy returns null if element doesn't exist
expect(screen.queryByText('Error')).not.toBeInTheDocument();
```

---

## user-event vs fireEvent

### fireEvent: Low-Level DOM Events

`fireEvent` dispatches a single DOM event. It does not simulate the full browser interaction.

```jsx
import { fireEvent } from '@testing-library/react';

fireEvent.click(button);        // dispatches one click event
fireEvent.change(input, { target: { value: 'hello' } });
```

### user-event: Realistic User Interactions

`user-event` simulates the full sequence of events a real user would trigger.

```jsx
import userEvent from '@testing-library/user-event';

test('typing fires correct events', async () => {
  const user = userEvent.setup();
  render(<input />);

  const input = screen.getByRole('textbox');
  await user.type(input, 'hello');
  // Fires for EACH character: keyDown, keyPress, keyUp, input, change
  // Also handles focus events

  expect(input).toHaveValue('hello');
});
```

### Key Differences

| Behavior | fireEvent | user-event |
|----------|-----------|------------|
| Click | 1 event | pointerDown + mouseDown + pointerUp + mouseUp + click |
| Type "ab" | 1 change event | 2x (keyDown + keyPress + input + keyUp) |
| Focus management | Manual | Automatic (clicks focus the element) |
| Disabled element | Still fires | Does NOT fire (like a real browser) |
| API style | Synchronous | Async (always await) |

**Rule of thumb:** Always use `user-event` unless you have a specific reason to use `fireEvent` (e.g., testing a drag-and-drop where you need fine-grained control over individual events).

---

## Testing Async Operations

### waitFor

Retries a callback until it passes or times out (default: 1000ms):

```jsx
import { render, screen, waitFor } from '@testing-library/react';

test('loads and displays data', async () => {
  render(<UserProfile userId="1" />);

  // Wait for loading to finish
  await waitFor(() => {
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

### findBy (Preferred for Single Element)

`findBy` is a combination of `getBy` + `waitFor`. Use it when you are waiting for an element to appear.

```jsx
test('loads and displays data', async () => {
  render(<UserProfile userId="1" />);

  // Cleaner than waitFor + getBy
  const name = await screen.findByText('John Doe');
  expect(name).toBeInTheDocument();
});
```

### Testing Loading States

```jsx
test('shows loading spinner then data', async () => {
  render(<UserProfile userId="1" />);

  // Loading state appears immediately
  expect(screen.getByText('Loading...')).toBeInTheDocument();

  // Data appears after fetch
  await screen.findByText('John Doe');

  // Loading state is gone
  expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
});
```

### Common Pitfall: Not Awaiting Async Operations

```jsx
// BUG: Test passes even if assertion would fail
test('loads data', () => {
  render(<UserProfile userId="1" />);
  screen.findByText('John Doe'); // Promise ignored!
});

// FIX: Always await findBy and waitFor
test('loads data', async () => {
  render(<UserProfile userId="1" />);
  await screen.findByText('John Doe');
});
```

---

## Mocking

### jest.mock for Modules

```jsx
// api.js
export async function fetchUser(id) {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
}

// UserProfile.test.jsx
import { render, screen } from '@testing-library/react';
import UserProfile from './UserProfile';
import { fetchUser } from './api';

jest.mock('./api');

test('displays user data', async () => {
  fetchUser.mockResolvedValue({ name: 'Alice', email: 'alice@test.com' });

  render(<UserProfile userId="1" />);

  expect(await screen.findByText('Alice')).toBeInTheDocument();
  expect(screen.getByText('alice@test.com')).toBeInTheDocument();
  expect(fetchUser).toHaveBeenCalledWith('1');
});

test('displays error on failure', async () => {
  fetchUser.mockRejectedValue(new Error('Network error'));

  render(<UserProfile userId="1" />);

  expect(await screen.findByText('Failed to load user')).toBeInTheDocument();
});
```

### MSW (Mock Service Worker) for API Mocking

MSW intercepts network requests at the service worker level. Tests use real fetch calls, providing higher confidence than `jest.mock`.

```jsx
// mocks/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Alice',
      email: 'alice@test.com',
    });
  }),

  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '123', ...body }, { status: 201 });
  }),
];

// mocks/server.js
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// jest.setup.js
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// UserProfile.test.jsx
import { server } from './mocks/server';
import { http, HttpResponse } from 'msw';

test('displays user data', async () => {
  render(<UserProfile userId="1" />);

  expect(await screen.findByText('Alice')).toBeInTheDocument();
});

test('displays error when API fails', async () => {
  // Override handler for this specific test
  server.use(
    http.get('/api/users/:id', () => {
      return new HttpResponse(null, { status: 500 });
    })
  );

  render(<UserProfile userId="1" />);

  expect(await screen.findByText('Failed to load user')).toBeInTheDocument();
});
```

**MSW advantages over jest.mock:**
- Tests the real fetch/axios call chain.
- Same mock definitions work in tests, Storybook, and development.
- Catches issues in request construction (headers, body format).

---

## Testing Custom Hooks

### renderHook

```jsx
// useCounter.js
import { useState, useCallback } from 'react';

export function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);

  const increment = useCallback(() => setCount(c => c + 1), []);
  const decrement = useCallback(() => setCount(c => c - 1), []);
  const reset = useCallback(() => setCount(initialValue), [initialValue]);

  return { count, increment, decrement, reset };
}

// useCounter.test.js
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

test('initializes with default value', () => {
  const { result } = renderHook(() => useCounter());
  expect(result.current.count).toBe(0);
});

test('initializes with custom value', () => {
  const { result } = renderHook(() => useCounter(10));
  expect(result.current.count).toBe(10);
});

test('increments counter', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});

test('decrements counter', () => {
  const { result } = renderHook(() => useCounter(5));

  act(() => {
    result.current.decrement();
  });

  expect(result.current.count).toBe(4);
});

test('resets to initial value', () => {
  const { result } = renderHook(() => useCounter(10));

  act(() => {
    result.current.increment();
    result.current.increment();
  });

  expect(result.current.count).toBe(12);

  act(() => {
    result.current.reset();
  });

  expect(result.current.count).toBe(10);
});
```

### Testing Hooks That Need Providers

```jsx
// useTheme.js
import { useContext } from 'react';
import { ThemeContext } from './ThemeProvider';

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}

// useTheme.test.js
import { renderHook } from '@testing-library/react';
import { ThemeProvider } from './ThemeProvider';
import { useTheme } from './useTheme';

test('returns theme from provider', () => {
  const wrapper = ({ children }) => (
    <ThemeProvider defaultTheme="dark">{children}</ThemeProvider>
  );

  const { result } = renderHook(() => useTheme(), { wrapper });

  expect(result.current.theme).toBe('dark');
});

test('throws when used outside provider', () => {
  // Suppress console.error for expected error
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

  expect(() => {
    renderHook(() => useTheme());
  }).toThrow('useTheme must be used within ThemeProvider');

  spy.mockRestore();
});
```

---

## Snapshot Testing

### When to Use

- Testing component **structure** that should not change accidentally (design system components).
- Quick regression detection for simple, presentational components.

### When to Avoid

- Complex components with dynamic data (snapshots become large and unreadable).
- Components that change frequently (constant snapshot updates make them meaningless).
- As the primary testing strategy (prefer behavior-based tests).

### Example

```jsx
import { render } from '@testing-library/react';
import Button from './Button';

test('renders primary button correctly', () => {
  const { container } = render(
    <Button variant="primary" size="large">
      Click Me
    </Button>
  );

  expect(container.firstChild).toMatchSnapshot();
});

// Inline snapshot (stored in the test file)
test('renders badge', () => {
  const { container } = render(<Badge count={5} />);
  expect(container.firstChild).toMatchInlineSnapshot(`
    <span class="badge">5</span>
  `);
});
```

**Pitfall:** Developers blindly updating snapshots with `--updateSnapshot` without reviewing changes. This defeats the purpose of snapshot testing.

---

## Testing Spectrum

```
+------------+----------------+-----------------+
| Unit       | Integration    | E2E             |
+------------+----------------+-----------------+
| Fast       | Medium speed   | Slow            |
| Isolated   | Some deps      | Full system     |
| Pure logic | Components +   | Browser + API   |
|            | context/hooks  | + database      |
| Jest       | RTL + Jest     | Playwright/     |
|            |                | Cypress         |
+------------+----------------+-----------------+

Unit: formatCurrency(), validateEmail(), custom hooks
Integration: LoginForm (with validation, API mocking, routing)
E2E: "User can sign up, create a post, and log out"
```

**Where to invest:**
- **Unit tests** for utility functions, pure logic, data transformations.
- **Integration tests** for component behavior with user interactions (the bulk of React tests).
- **E2E tests** for critical user journeys (login, checkout, payment).

---

## Testing Patterns

### Arrange-Act-Assert (AAA)

```jsx
test('submits form with user input', async () => {
  // ARRANGE: set up the component and dependencies
  const handleSubmit = jest.fn();
  const user = userEvent.setup();
  render(<ContactForm onSubmit={handleSubmit} />);

  // ACT: simulate user behavior
  await user.type(screen.getByLabelText('Name'), 'Alice');
  await user.type(screen.getByLabelText('Email'), 'alice@test.com');
  await user.type(screen.getByLabelText('Message'), 'Hello there');
  await user.click(screen.getByRole('button', { name: 'Send' }));

  // ASSERT: verify the expected outcome
  expect(handleSubmit).toHaveBeenCalledWith({
    name: 'Alice',
    email: 'alice@test.com',
    message: 'Hello there',
  });
});
```

### Custom Render with Providers

```jsx
// test-utils.jsx
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './ThemeProvider';
import { AuthProvider } from './AuthProvider';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function AllProviders({ children }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            {children}
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export function renderWithProviders(ui, options = {}) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from '@testing-library/react';
export { renderWithProviders as render };
```

---

## Testing Context Providers

```jsx
// NotificationContext.jsx
import { createContext, useContext, useState } from 'react';

const NotificationContext = createContext();

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 3000);
  };

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <NotificationContext.Provider value={{ notifications, addNotification, dismissNotification }}>
      {children}
    </NotificationContext.Provider>
  );
}

export const useNotifications = () => useContext(NotificationContext);

// NotificationContext.test.jsx
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationProvider, useNotifications } from './NotificationContext';

function TestComponent() {
  const { notifications, addNotification, dismissNotification } = useNotifications();
  return (
    <div>
      <button onClick={() => addNotification('Test message', 'success')}>
        Add Notification
      </button>
      {notifications.map(n => (
        <div key={n.id} data-testid="notification">
          <span>{n.message}</span>
          <button onClick={() => dismissNotification(n.id)}>Dismiss</button>
        </div>
      ))}
    </div>
  );
}

test('adds and displays notifications', async () => {
  const user = userEvent.setup();
  render(
    <NotificationProvider>
      <TestComponent />
    </NotificationProvider>
  );

  await user.click(screen.getByText('Add Notification'));

  expect(screen.getByText('Test message')).toBeInTheDocument();
});

test('dismisses a notification', async () => {
  const user = userEvent.setup();
  render(
    <NotificationProvider>
      <TestComponent />
    </NotificationProvider>
  );

  await user.click(screen.getByText('Add Notification'));
  expect(screen.getByText('Test message')).toBeInTheDocument();

  await user.click(screen.getByText('Dismiss'));
  expect(screen.queryByText('Test message')).not.toBeInTheDocument();
});

test('auto-removes notification after timeout', async () => {
  jest.useFakeTimers();

  render(
    <NotificationProvider>
      <TestComponent />
    </NotificationProvider>
  );

  await act(async () => {
    screen.getByText('Add Notification').click();
  });

  expect(screen.getByText('Test message')).toBeInTheDocument();

  act(() => {
    jest.advanceTimersByTime(3000);
  });

  expect(screen.queryByText('Test message')).not.toBeInTheDocument();

  jest.useRealTimers();
});
```

---

## Testing Error Boundaries

```jsx
// ErrorBoundary.jsx
import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}

// ErrorBoundary.test.jsx
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

function BrokenComponent() {
  throw new Error('Crash!');
}

function WorkingComponent() {
  return <p>Everything is fine</p>;
}

test('renders children when no error', () => {
  render(
    <ErrorBoundary>
      <WorkingComponent />
    </ErrorBoundary>
  );

  expect(screen.getByText('Everything is fine')).toBeInTheDocument();
});

test('renders fallback when child throws', () => {
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

  render(
    <ErrorBoundary fallback={<p>Oops! Something broke.</p>}>
      <BrokenComponent />
    </ErrorBoundary>
  );

  expect(screen.getByText('Oops! Something broke.')).toBeInTheDocument();
  expect(screen.queryByText('Everything is fine')).not.toBeInTheDocument();

  spy.mockRestore();
});

test('calls onError callback', () => {
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  const onError = jest.fn();

  render(
    <ErrorBoundary onError={onError}>
      <BrokenComponent />
    </ErrorBoundary>
  );

  expect(onError).toHaveBeenCalledTimes(1);
  expect(onError.mock.calls[0][0].message).toBe('Crash!');

  spy.mockRestore();
});
```

---

## Full Test Examples

### Example 1: Testing a Form Component

```jsx
// ContactForm.jsx
import { useState } from 'react';

export function ContactForm({ onSubmit }) {
  const [values, setValues] = useState({ name: '', email: '', message: '' });
  const [errors, setErrors] = useState({});

  function validate() {
    const newErrors = {};
    if (!values.name.trim()) newErrors.name = 'Name is required';
    if (!values.email.includes('@')) newErrors.email = 'Invalid email';
    if (values.message.length < 10) newErrors.message = 'Message must be at least 10 characters';
    return newErrors;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    onSubmit(values);
  }

  function handleChange(e) {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" name="name" value={values.name} onChange={handleChange} />
        {errors.name && <span role="alert">{errors.name}</span>}
      </div>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" value={values.email} onChange={handleChange} />
        {errors.email && <span role="alert">{errors.email}</span>}
      </div>
      <div>
        <label htmlFor="message">Message</label>
        <textarea id="message" name="message" value={values.message} onChange={handleChange} />
        {errors.message && <span role="alert">{errors.message}</span>}
      </div>
      <button type="submit">Send</button>
    </form>
  );
}

// ContactForm.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContactForm } from './ContactForm';

describe('ContactForm', () => {
  const user = userEvent.setup();

  test('submits form with valid data', async () => {
    const handleSubmit = jest.fn();
    render(<ContactForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'Alice Smith');
    await user.type(screen.getByLabelText('Email'), 'alice@test.com');
    await user.type(screen.getByLabelText('Message'), 'Hello, this is a test message');
    await user.click(screen.getByRole('button', { name: 'Send' }));

    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'Alice Smith',
      email: 'alice@test.com',
      message: 'Hello, this is a test message',
    });
  });

  test('shows validation errors for empty fields', async () => {
    const handleSubmit = jest.fn();
    render(<ContactForm onSubmit={handleSubmit} />);

    await user.click(screen.getByRole('button', { name: 'Send' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Invalid email')).toBeInTheDocument();
    expect(screen.getByText('Message must be at least 10 characters')).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  test('clears error when user starts typing', async () => {
    render(<ContactForm onSubmit={jest.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Send' }));
    expect(screen.getByText('Name is required')).toBeInTheDocument();

    await user.type(screen.getByLabelText('Name'), 'A');
    expect(screen.queryByText('Name is required')).not.toBeInTheDocument();
  });

  test('validates email format', async () => {
    render(<ContactForm onSubmit={jest.fn()} />);

    await user.type(screen.getByLabelText('Name'), 'Alice');
    await user.type(screen.getByLabelText('Email'), 'not-an-email');
    await user.type(screen.getByLabelText('Message'), 'A long enough message');
    await user.click(screen.getByRole('button', { name: 'Send' }));

    expect(screen.getByText('Invalid email')).toBeInTheDocument();
  });
});
```

### Example 2: Testing a Data-Fetching Component

```jsx
// UserProfile.jsx
import { useState, useEffect } from 'react';

export function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`/api/users/${userId}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then(data => {
        if (!cancelled) {
          setUser(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <p>Loading profile...</p>;
  if (error) return <p role="alert">Error: {error}</p>;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <p>Joined: {user.joinDate}</p>
    </div>
  );
}

// UserProfile.test.jsx (using MSW)
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { UserProfile } from './UserProfile';

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'Alice Johnson',
      email: 'alice@example.com',
      joinDate: '2023-01-15',
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UserProfile', () => {
  test('shows loading state initially', () => {
    render(<UserProfile userId="1" />);
    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  test('displays user data after loading', async () => {
    render(<UserProfile userId="1" />);

    expect(await screen.findByText('Alice Johnson')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('Joined: 2023-01-15')).toBeInTheDocument();
    expect(screen.queryByText('Loading profile...')).not.toBeInTheDocument();
  });

  test('shows error when API fails', async () => {
    server.use(
      http.get('/api/users/:id', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    render(<UserProfile userId="1" />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Error: Failed to fetch');
  });

  test('refetches when userId changes', async () => {
    const { rerender } = render(<UserProfile userId="1" />);

    await screen.findByText('Alice Johnson');

    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json({
          id: '2',
          name: 'Bob Smith',
          email: 'bob@example.com',
          joinDate: '2024-03-20',
        });
      })
    );

    rerender(<UserProfile userId="2" />);

    expect(await screen.findByText('Bob Smith')).toBeInTheDocument();
  });
});
```

### Example 3: Testing a Custom Hook

```jsx
// useDebounce.js
import { useState, useEffect } from 'react';

export function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// useDebounce.test.js
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from './useDebounce';

describe('useDebounce', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  test('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500));
    expect(result.current).toBe('hello');
  });

  test('does not update value before delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    rerender({ value: 'world', delay: 500 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('hello');
  });

  test('updates value after delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    rerender({ value: 'world', delay: 500 });

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe('world');
  });

  test('resets timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 500 } }
    );

    rerender({ value: 'ab', delay: 500 });
    act(() => jest.advanceTimersByTime(200));

    rerender({ value: 'abc', delay: 500 });
    act(() => jest.advanceTimersByTime(200));

    rerender({ value: 'abcd', delay: 500 });
    act(() => jest.advanceTimersByTime(200));

    // Only 200ms since last change, should still show 'a'
    expect(result.current).toBe('a');

    act(() => jest.advanceTimersByTime(300));

    // Now 500ms since last change
    expect(result.current).toBe('abcd');
  });
});
```

---

## Scenario-Based Interview Questions

### Q1: You inherit a React app with 500 snapshot tests that fail on every PR. What do you do?

**Answer:**

Snapshot tests that fail constantly provide negative value -- they slow down development and train developers to blindly update snapshots.

**Step-by-step plan:**

1. **Audit:** Categorize the snapshots. How many are on leaf/presentational components vs complex containers?

2. **Delete snapshots on complex components.** A snapshot of a 200-line component tree is unreadable and changes with every feature. Replace with behavior-based tests.

3. **Keep snapshots on stable, leaf components** (design system: `Button`, `Badge`, `Avatar`). These change rarely and snapshots catch unintended visual regressions.

4. **Convert the rest to integration tests** using RTL. For a `LoginForm`, instead of snapshotting HTML, test: "user types email, types password, clicks submit, onSubmit is called with correct values."

5. **Use inline snapshots** for small, stable outputs (a formatted date, a className string). They are easier to review in diffs than external `.snap` files.

6. **Set a team guideline:** Snapshots are only for leaf components in the design system. Everything else uses behavior tests.

---

### Q2: How would you test a component that uses `useContext`, `react-router`, and makes API calls?

**Answer:**

Create a custom render function that wraps the component with all required providers:

```jsx
function renderWithProviders(ui, { route = '/', ...options } = {}) {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <AuthProvider initialUser={{ id: '1', name: 'Test User' }}>
          <MemoryRouter initialEntries={[route]}>
            {children}
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    ),
    ...options,
  });
}
```

For API calls, use MSW to mock the server at the network level. This approach:
- Does not mock implementation details (no `jest.mock` for hooks or context).
- Tests the full integration of component + providers + API layer.
- Is resilient to refactoring.

---

### Q3: A test passes in isolation but fails when run with the full suite. How do you debug this?

**Answer:**

This is almost always caused by **shared mutable state between tests**.

**Common causes and fixes:**

1. **Global state not reset.** A previous test modifies a module-level variable or singleton. Fix: ensure proper cleanup in `afterEach`.

2. **Timer leaks.** A previous test uses `jest.useFakeTimers()` without calling `jest.useRealTimers()`. Fix: always restore timers.

3. **MSW handler leaks.** A test adds a handler with `server.use()` but `server.resetHandlers()` is not called. Fix: ensure `afterEach(() => server.resetHandlers())` is in setup.

4. **DOM leaks.** A portal or modal attached to `document.body` is not cleaned up. Fix: RTL's automatic `cleanup` handles most cases, but manually appended elements need manual removal.

**Debugging technique:** Run the failing test in isolation (`jest --testPathPattern=MyComponent`). If it passes, run it with the test that runs immediately before it. Use `--verbose` to see the test order and identify the contaminating test.

---

### Q4: You need to test a component that renders differently based on screen size (responsive design). How?

**Answer:**

**Approach 1: Mock window.matchMedia** (most common for unit/integration tests)

```jsx
function createMatchMedia(width) {
  return (query) => ({
    matches: mediaQuery.match(query, { width }),
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  });
}

test('renders mobile layout on small screen', () => {
  window.matchMedia = createMatchMedia(375);

  render(<ResponsiveNav />);

  expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument();
  expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
});

test('renders desktop layout on large screen', () => {
  window.matchMedia = createMatchMedia(1024);

  render(<ResponsiveNav />);

  expect(screen.getByRole('navigation')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Menu' })).not.toBeInTheDocument();
});
```

**Approach 2: Test the hook/logic separately.** If the component uses a `useMediaQuery` hook, test the hook with `renderHook` and mock `matchMedia`. Test the component with the hook's return value as a prop.

**Approach 3: E2E with Playwright** for full visual regression testing:

```js
test('mobile layout', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible();
});
```

The right approach depends on what you are testing. For unit/integration, mock `matchMedia`. For visual accuracy, use Playwright or Cypress.
