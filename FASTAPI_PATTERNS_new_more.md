# FastAPI — From Beginner to Staff Engineer

> Covers architecture, internals, patterns, security, performance, testing, and production at depth.
> Every section includes code that compiles and runs.
> **New to FastAPI or backend dev?** Start with [Section 0](#0-beginner-primer--read-this-first) — every later
> section opens with a plain-language "Beginner recap" before diving into the advanced material.

---

## Table of Contents

1. [Beginner Primer — Read This First](#0-beginner-primer--read-this-first)
2. [Core Architecture & Internals](#1-core-architecture--internals)
3. [Routing & Path Operations](#2-routing--path-operations)
4. [Request & Response Models (Pydantic v2)](#3-request--response-models-pydantic-v2)
5. [Dependency Injection System](#4-dependency-injection-system)
6. [Authentication & Authorization](#5-authentication--authorization)
7. [Middleware & Lifecycle](#6-middleware--lifecycle)
8. [Database Integration (Async SQLAlchemy)](#7-database-integration-async-sqlalchemy)
9. [Background Tasks & Celery](#8-background-tasks--celery)
10. [WebSockets & Server-Sent Events](#9-websockets--server-sent-events)
11. [Error Handling & Custom Exceptions](#10-error-handling--custom-exceptions)
12. [Testing Strategy](#11-testing-strategy)
13. [Performance & Scalability](#12-performance--scalability)
14. [Security Best Practices](#13-security-best-practices)
15. [Caching Patterns](#14-caching-patterns)
16. [Observability: Logging, Tracing, Metrics](#15-observability-logging-tracing-metrics)
17. [Production Deployment](#16-production-deployment)
18. [Advanced Patterns (CQRS, Event-Driven, DDD)](#17-advanced-patterns-cqrs-event-driven-ddd)
19. [Staff Engineer Interview: Critical Questions](#18-staff-engineer-interview-critical-questions)

---

## 0. Beginner Primer — Read This First

If terms like "ASGI", "async def", "dependency injection", or "middleware" feel unfamiliar, read this section
first. Everything else in this doc builds on these ideas.

### What is a web API, really?

```
Your phone/browser (CLIENT)                Your server (API)
──────────────────────                     ──────────────────
"Hey, give me user #5"   ──── request ───→  looks up user #5 in database
                          ←─── response ──  "here's user #5: {name: Alice, ...}"
```

An API is just a program that sits and waits for requests over the network, does some work (usually reading/writing
a database), and sends back an answer. FastAPI is a **framework** — it's the plumbing that listens for requests,
figures out which of your Python functions should handle each one, and converts your function's return value into
a proper HTTP response. You write the business logic; FastAPI handles the network/HTTP boilerplate.

### JSON — the language APIs speak

Almost all modern APIs send data as **JSON** (JavaScript Object Notation) — plain text that looks like a Python
dict:

```json
{"id": 5, "name": "Alice", "is_active": true}
```

When you `return {"id": 5, "name": "Alice"}` from a FastAPI function, FastAPI automatically converts that Python
dict into JSON text and sends it over the network. You almost never write JSON by hand — Pydantic models (Section 3)
do this conversion for you, with validation.

### HTTP methods and status codes (the vocabulary)

```
GET     /users/5        → "give me user 5"           (read, no side effects)
POST    /users          → "create a new user"        (body has the new user's data)
PUT     /users/5        → "replace user 5 entirely"
PATCH   /users/5        → "update part of user 5"
DELETE  /users/5        → "delete user 5"

Status codes (the 3-digit number in every response):
  2xx = success           200 OK, 201 Created
  4xx = client's mistake   400 Bad Request, 401 Unauthorized, 404 Not Found, 422 Validation Error
  5xx = server's mistake   500 Internal Server Error
```

### Type hints — Python's way of documenting what a variable should be

```python
def greet(name: str) -> str:
    return f"Hello {name}"

# name: str          → this parameter SHOULD be a string
# -> str             → this function SHOULD return a string
```

Type hints don't stop you from passing the wrong type at plain runtime — Python itself ignores them. But FastAPI
**reads** these hints and uses them to automatically validate incoming request data, convert types (e.g. a URL
string "5" → the Python `int` 5), and generate interactive API docs. This is the foundation of almost every FastAPI
feature you'll see in this doc.

### Decorators — what does `@app.get(...)` actually do?

```python
@app.get("/users/{id}")
async def get_user(id: int):
    return {"id": id}
```

A decorator (`@something`) is a Python feature that wraps a function to add extra behavior, without changing the
function's own code. Think of `@app.get("/users/{id}")` as saying: *"Hey FastAPI, whenever a GET request arrives at
`/users/{id}`, please call this function below and send its return value back as the response."* You're not calling
`get_user()` yourself — FastAPI calls it for you, at the right time, with the right arguments extracted from the
request.

### `async def` vs `def` — the short version

```python
def normal_function():
    result = some_slow_operation()   # the WHOLE program waits here
    return result

async def async_function():
    result = await some_slow_operation()   # OTHER requests can be handled while waiting
    return result
```

Regular Python code runs one thing at a time, top to bottom, and if something is slow (like waiting for a database
reply), the whole program just sits there waiting. `async`/`await` lets a **single process** juggle many requests at
once: while one request is waiting on the database, the same program can start working on a different request. This
matters a lot for a web server, which needs to serve many users at the same time. Section 1 covers this in depth
with the concept of an "event loop."

```
Without async (blocking):              With async (non-blocking):
  Request A: 100ms waiting on DB          Request A: starts, hands off wait to event loop
  Request B: waits for A to finish        Request B: starts immediately, doesn't wait for A
  Request C: waits for A and B            Request C: starts immediately too
  (serves 1 request at a time)            (serves many requests "at once")
```

### Dependency Injection (DI) in one sentence

"Instead of a function creating the things it needs by itself (like a database connection), FastAPI hands those
things to the function as arguments, automatically." This is what `Depends(...)` means — you'll see it constantly.
Section 4 covers it in full, but you can read every other section without fully understanding it first; just know
that `Depends(get_db)` means "FastAPI will get me a database session and pass it in here for me."

### How to read this document

Every numbered section below has this shape:

```
## N. Topic Name

  ↳ (starting from Section 1) a short "Beginner recap" paragraph
     explaining the concept in plain words

  ↳ then progressively more advanced code and patterns,
     the kind you'd see in a real production codebase
```

You can read top to bottom, or jump straight to whatever topic you need — each section's beginner recap gives you
enough context to follow the code that comes after it.

---

## 1. Core Architecture & Internals

**Beginner recap:** This section explains what actually happens, layer by layer, between "a browser sends a
request" and "your Python function runs." FastAPI itself doesn't listen to the network directly — it relies on
other libraries underneath it. Knowing this stack helps you understand error messages and performance behavior
later on.

### What FastAPI actually is

```
HTTP Request
    │
    ▼
Uvicorn/Hypercorn (ASGI server)  ← runs the event loop
    │
    ▼
Starlette (routing, middleware, WebSocket, SSE, static files)
    │
    ▼
FastAPI layer (Pydantic validation, OpenAPI schema, DI resolution)
    │
    ▼
Your route handler (async def or sync def)
```

- **ASGI** (Asynchronous Server Gateway Interface) is the successor to WSGI.
- FastAPI is built **on top of Starlette** — it IS a Starlette application.
- Pydantic v2 (Rust core) does serialization/validation.
- The `app` object is a `Starlette` subclass; you can pass it directly to any ASGI runner.

### Sync vs Async handlers

```python
# async: runs directly on the event loop — never block it
@app.get("/async")
async def async_endpoint():
    result = await some_io_bound_coroutine()
    return result

# sync: FastAPI runs this in a ThreadPoolExecutor automatically
# Use for CPU-bound or legacy blocking libraries (SQLAlchemy sync, etc.)
@app.get("/sync")
def sync_endpoint():
    return {"data": blocking_db_call()}
```

**Key rule**: If you `await` nothing inside an `async def`, you're blocking the event loop for I/O. Use `asyncio.to_thread()` or `run_in_executor` for truly blocking work inside async handlers.

### Application factory pattern

```python
# app/main.py
from contextlib import asynccontextmanager          # used to build the startup/shutdown "lifespan" block below
from fastapi import FastAPI                          # the main FastAPI application class
from app.api.v1.router import api_v1_router          # the combined router from Section 2 (health+users+orders)
from app.core.config import Settings                 # your app's settings/config class (env vars, secrets, etc.)
from app.db.session import engine                    # the SQLAlchemy async engine (DB connection pool)
from app.db.base import Base                          # base class that all your DB models inherit from

def create_app(settings: Settings | None = None) -> FastAPI:
    # "factory" function — instead of creating `app` at import time directly,
    # wrap creation in a function so tests can call create_app() repeatedly
    # with different settings, without any global state leaking between tests.
    cfg = settings or Settings()                      # use passed-in settings, or build the default ones

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Everything BEFORE `yield` runs ONCE, when the server starts up.
        # startup
        async with engine.begin() as conn:
            # create all DB tables if they don't exist yet (dev/demo convenience;
            # production apps normally use Alembic migrations instead — see Section 7)
            await conn.run_sync(Base.metadata.create_all)
        yield                                          # ← the app runs and serves requests while paused here
        # Everything AFTER `yield` runs ONCE, when the server is shutting down.
        # shutdown
        await engine.dispose()                         # cleanly close all pooled DB connections

    app = FastAPI(
        title=cfg.project_name,                        # shown as the API's title in the /docs page
        version=cfg.version,                           # shown in /docs; also returned in the OpenAPI schema
        docs_url="/docs" if cfg.debug else None,        # disable in prod — hide interactive docs from the public
        redoc_url=None,                                 # disable the alternative ReDoc docs page entirely
        lifespan=lifespan,                              # wire up the startup/shutdown function defined above
    )
    app.include_router(api_v1_router, prefix="/api/v1") # mount ALL v1 routes under the "/api/v1" URL prefix
    return app                                          # hand back the fully configured FastAPI app

app = create_app()   # the actual app object that Uvicorn/Gunicorn will run (e.g. `uvicorn app.main:app`)
```

---

## 2. Routing & Path Operations

**Beginner recap:** "Routing" just means matching an incoming request (its HTTP method + URL) to the correct Python
function. `@router.get("/{user_id}")` means "if someone does a GET request to something like `/users/42`, run this
function and pass `42` in as `user_id`." An `APIRouter` is a way to group related routes (e.g. all `/users/...`
routes) into their own file, instead of putting every route directly on the main `app` object — this keeps large
apps organized.

### Router organization (Blueprint pattern)

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, orders, health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(users.router,  prefix="/users",  tags=["Users"])
api_v1_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
```

**Line by line:**

```python
from fastapi import APIRouter
```
Imports the `APIRouter` class from FastAPI. Think of `APIRouter` as a "mini FastAPI app" — it can hold routes
(`@router.get(...)`, `@router.post(...)`, etc.) just like the main `app` object can, but it isn't running a server by
itself. It's just a container you fill up with routes, which you then attach to the real `app` later.

```python
from app.api.v1.endpoints import users, orders, health
```
Imports three **other Python files** — `users.py`, `orders.py`, `health.py` — that live in the
`app/api/v1/endpoints/` folder. Each of those files is expected to define its own `router = APIRouter()` with its
own routes inside (e.g. `users.py` might have `@router.get("/{user_id}")`, `@router.post("/")`, etc. — the very
routes shown in the next code block). This import line doesn't run any routes yet — it just makes those three
modules available to use below.

```python
api_v1_router = APIRouter()
```
Creates ONE new, empty router — call it "the v1 router." Nothing is inside it yet. It exists to become a container
that groups every route under version 1 of your API (`/api/v1/...`).

```python
api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
```
This line takes ALL the routes already defined inside `health.py`'s own `router` object, and copies them into
`api_v1_router`, with two extra things applied to every one of them:

```
prefix="/health"   → every route inside health.router gets "/health" stuck in front of its path.
                      e.g. if health.py has @router.get("/live"), it becomes reachable at "/health/live"
                      (not just "/live") once merged in here.

tags=["Health"]     → purely cosmetic — groups these routes under a "Health" heading
                      in the auto-generated API docs (Swagger UI at /docs). Doesn't
                      affect behavior at all, just makes the docs page organized.
```

```python
api_v1_router.include_router(users.router,  prefix="/users",  tags=["Users"])
api_v1_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
```
Same idea, repeated for the `users` and `orders` modules. After these three lines run, `api_v1_router` now contains
every route from `health.router`, `users.router`, and `orders.router`, each correctly prefixed.

### Where does this all actually connect to the running server?

This is the missing piece that makes the whole thing click — look back at the **Application factory pattern**
code above in Section 1:

```python
app.include_router(api_v1_router, prefix="/api/v1")
```

This one line (in `app/main.py`) takes `api_v1_router` — which by now contains ALL the health/users/orders routes —
and mounts it onto the real, running `app`, adding ANOTHER prefix: `/api/v1`.

### The full picture — how one route's final URL gets built

```
users.py:              @router.get("/{user_id}")             ← defines path "/{user_id}"
                              │
router.py:             include_router(users.router, prefix="/users")
                              │                                 prepends "/users"
                              ▼
                        path is now "/users/{user_id}"
                              │
main.py:                app.include_router(api_v1_router, prefix="/api/v1")
                              │                                 prepends "/api/v1"
                              ▼
                        FINAL URL: "/api/v1/users/{user_id}"
```

**Why bother with this nesting instead of just writing `/api/v1/users/{user_id}` directly in `users.py`?** Because
it keeps each file only responsible for its own small piece:

```
users.py    only ever needs to know about "/{user_id}", "/", etc. — never repeats "/api/v1/users" everywhere
router.py   only needs to know "users stuff lives under /users"
main.py     only needs to know "everything v1 lives under /api/v1"
```

If you ever need a `/api/v2/`, you just write a new `router.py` for v2 and reuse the same `users.py` logic — nothing
inside `users.py` has to change. This is the entire point of the "Blueprint pattern" mentioned above: each layer
adds one small, isolated piece of the final URL.

### Path parameters, query params, body

```python
from fastapi import APIRouter, Path, Query, Body, status
from uuid import UUID

router = APIRouter()

@router.get(
    "/{user_id}",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    responses={
        404: {"model": ErrorDetail, "description": "User not found"},
        422: {"description": "Validation error"},
    },
)
async def get_user(
    user_id: UUID = Path(..., description="User UUID"),
    include_deleted: bool = Query(False),
    service: UserService = Depends(get_user_service),
) -> UserOut:
    return await service.get_by_id(user_id, include_deleted=include_deleted)
```

**Line by line — the `@router.get(...)` decorator arguments:**

Every one of these is a **keyword argument you're passing to the `.get(...)` decorator itself** — they configure
metadata and behavior for this one route, separately from the actual function logic below. None of them are
required except the path string; the rest are optional extras that make the route more correct and self-documenting.

```python
@router.get(
    "/{user_id}",
```
The **path** this route responds to, relative to whatever prefix gets added later (see the routing walkthrough
above — this becomes `/api/v1/users/{user_id}`). The `{user_id}` part is a **placeholder** — FastAPI will capture
whatever value appears there in the real URL (e.g. `42` in `/users/42`) and pass it into your function as the
`user_id` parameter, matched by name.

```python
    response_model=UserOut,
```
Tells FastAPI: "no matter what Python object my function returns, convert/filter it through the `UserOut` Pydantic
model before sending the response." This does two things — (1) **validates** your own return value matches the
shape you promised, catching bugs where you accidentally return the wrong data, and (2) **strips out any extra
fields** not defined on `UserOut` (e.g. if your database object also has a `password_hash` field, it will NOT be
included in the response, even if you forgot to remove it yourself). It's also used to generate the "Response"
example shown in the `/docs` page.

```python
    status_code=status.HTTP_200_OK,
```
Sets what HTTP status code to return when this route succeeds. `status.HTTP_200_OK` is just a readable constant
equal to the plain number `200` (imported from `fastapi.status` so you don't have to memorize magic numbers).
For a `GET` request 200 is already the default, so writing it here is mostly for **explicitness/documentation** —
but for something like a `POST` that creates a resource, you'd set `status_code=201` since that's the correct code
for "something was created," which FastAPI would NOT infer on its own.

```python
    summary="Get user by ID",
```
A short, human-readable title for this endpoint — purely for documentation. It shows up as the bolded title of this
route in the Swagger UI (`/docs` page). Doesn't affect any runtime behavior at all.

```python
    responses={
        404: {"model": ErrorDetail, "description": "User not found"},
        422: {"description": "Validation error"},
    },
)
```
This documents **other possible outcomes besides the success case**, for the auto-generated API docs. It does NOT
make your function actually return a 404 or 422 — that still happens elsewhere (e.g. your service raising a
`NotFoundError`, which a global exception handler turns into an actual 404 response, as covered in Section 10). All
this `responses={...}` dict does is add extra entries to the `/docs` page saying "by the way, this endpoint might
also respond with a 404 (shaped like `ErrorDetail`) or a 422" — so anyone reading the docs (including
frontend developers integrating with your API) knows what error shapes to expect, without you writing separate
prose documentation by hand.

```
Concretely, in the Swagger UI, this route's docs page would show:

  200  Success           → shaped like UserOut
  404  User not found     → shaped like ErrorDetail   ← from your responses={} dict
  422  Validation error   → (default shape FastAPI always documents for input validation failures)
```

**Now the function signature underneath:**

```python
async def get_user(
    user_id: UUID = Path(..., description="User UUID"),
```
`user_id` is declared as type `UUID` (so FastAPI will try to parse/validate the `{user_id}` piece of the URL as a
UUID, rejecting the request with a 422 automatically if it isn't one). Wrapping it in `Path(...)` lets you attach
extra metadata (here, just a `description` for the docs) to a path parameter. The `...` (called "Ellipsis") as the
first argument to `Path(...)` means "this parameter is required — there is no default value." Since `user_id` is
part of the URL path itself, it's always required anyway; `Path(...)` here is mainly being used just to attach the
`description` text.

```python
    include_deleted: bool = Query(False),
```
This is a **query parameter** — something appended to the URL after a `?`, like `/users/42?include_deleted=true`.
`Query(False)` means "if the client doesn't provide `include_deleted` in the URL at all, default it to `False`."
Declared as `bool`, so FastAPI automatically converts the string `"true"`/`"false"` from the URL into a real Python
`True`/`False`.

```python
    service: UserService = Depends(get_user_service),
```
This is the dependency injection pattern from Section 4: "before calling this function, call `get_user_service()`
and pass its return value in here as `service`." You never call `get_user_service()` yourself — FastAPI does it
automatically, per request.

```python
) -> UserOut:
```
This is the function's own **return type hint** (not a decorator argument — this is plain Python syntax, separate
from the `response_model=UserOut` above). It's good practice to keep it consistent with `response_model`, but note
they serve different purposes: `response_model` is what FastAPI actually uses at runtime to validate/filter the
response; `-> UserOut` here is mostly for your editor's autocomplete and static type checkers (like `mypy`) — FastAPI
does not strictly enforce this return annotation the way it enforces `response_model`.

```python
    return await service.get_by_id(user_id, include_deleted=include_deleted)
```
Calls the service layer (business logic, no HTTP knowledge — see Section 10's beginner notes on why) with the two
values FastAPI already extracted and validated for us, and returns whatever it gives back. FastAPI then runs that
return value through `response_model=UserOut` before actually sending it to the client.

### Response model projection

```python
# Separate input/output models — never expose internal fields
class UserCreate(BaseModel):
    email: EmailStr
    password: str          # raw password, hash before storing

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)   # Pydantic v2

# response_model strips extra fields automatically
@router.post("/", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, svc: UserService = Depends()):
    return await svc.create(body)
```

---

## 3. Request & Response Models (Pydantic v2)

**Beginner recap:** Pydantic models are Python classes that describe **the shape of your data** — like a form with
labeled, typed fields. When a request comes in, FastAPI uses your Pydantic model to check "does this JSON body
actually have an `email` field that's a valid email, and an `amount` field that's a positive number?" If not, it
automatically responds with a `422` error explaining what's wrong — you never write that validation code by hand.
The same models are also used to shape your **output**: you define one model for "what a client is allowed to send
in" (e.g. `UserCreate`, including a raw password) and a different one for "what a client is allowed to see back"
(e.g. `UserOut`, excluding the password) — this prevents accidentally leaking sensitive fields.

### Model configuration (v2 syntax)

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic import EmailStr, AnyHttpUrl
from typing import Annotated
from decimal import Decimal
import re

# A reusable "type alias": anywhere you write PositiveAmount, Pydantic will
# require a Decimal that is > 0 and has at most 2 decimal places. Saves you
# from repeating Field(gt=0, decimal_places=2) on every money field in the app.
PositiveAmount = Annotated[Decimal, Field(gt=0, decimal_places=2)]

class OrderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,   # auto .strip() every string field (removes accidental leading/trailing spaces)
        validate_assignment=True,    # re-run validation if code does `order.amount = -5` AFTER creation, not just at creation
        populate_by_name=True,       # accept both aliases (e.g. "orderAmount") AND the real field name ("amount")
        json_schema_extra={"example": {"amount": "19.99", "currency": "USD"}},   # shown as a sample in /docs
    )

    amount: PositiveAmount                                             # must be a positive Decimal, 2 decimal places
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")   # exactly 3 uppercase letters, e.g. "USD"
    callback_url: AnyHttpUrl | None = None                             # optional; must be a valid URL if provided

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        # runs AFTER the basic type/pattern check above, for ONE specific field ("currency").
        # lets a client send "usd" and have it auto-corrected to "USD" instead of rejected outright.
        return v.upper()

    @model_validator(mode="after")
    def validate_callback_for_large_orders(self) -> "OrderCreate":
        # runs AFTER all individual fields have already passed their own checks — used here
        # because this rule needs to look at TWO fields together (amount AND callback_url),
        # which a single @field_validator (scoped to one field) can't do.
        if self.amount > 10000 and self.callback_url is None:
            raise ValueError("callback_url required for orders > 10000")   # → becomes a 422 error automatically
        return self   # must return self (or the modified object) — that's what "after" validators require
```

### Generic pagination response

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Sequence

T = TypeVar("T")   # a placeholder type — "T" means "whatever type you plug in later", like a blank in a template

class Page(BaseModel, Generic[T]):
    # Generic[T] means Page can be reused for ANY item type: Page[UserOut], Page[OrderOut], etc.,
    # instead of writing a separate "UserPage", "OrderPage" class for every model you paginate.
    items: Sequence[T]   # the actual list of results for this page — typed as "a sequence of whatever T is"
    total: int           # total number of items across ALL pages (not just this page)
    page: int            # which page number this is (e.g. 1, 2, 3...)
    size: int            # how many items per page
    pages: int           # total number of pages available

    @classmethod
    def create(cls, items: Sequence[T], total: int, page: int, size: int) -> "Page[T]":
        # a small factory method so callers don't have to compute "pages" themselves every time
        return cls(items=items, total=total, page=page, size=size, pages=-(-total // size))
        # -(-total // size) is a common trick for "ceiling division" without importing math.ceil,
        # e.g. 45 items at size 20 → -(-45 // 20) = -(-3) = 3 pages (not 2, which floor division would give)

# Usage
@router.get("/", response_model=Page[UserOut])   # tells FastAPI: response is a Page whose "items" are UserOut objects
async def list_users(page: int = 1, size: int = Query(20, le=100)):   # size capped at 100 via le=100 (le = "less than or equal")
    users, total = await svc.paginate(page=page, size=size)   # ask the service layer for one page of users + the total count
    return Page.create(users, total, page, size)               # wrap it all into the standard Page shape
```

### Custom serializers

```python
from pydantic import field_serializer

class PaymentOut(BaseModel):
    amount: Decimal
    created_at: datetime

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"

    @field_serializer("created_at")
    def serialize_dt(self, v: datetime) -> str:
        return v.isoformat()
```

---

## 4. Dependency Injection System

**Beginner recap:** Imagine every route needed a database connection. Without DI, every single function would have
to write code like `db = connect_to_database()` at the top — repetitive, and hard to swap out for tests. With DI,
you instead write a small function (e.g. `get_db()`) that knows how to create that connection, and tell FastAPI
"this route needs a `db` argument — please call `get_db()` and hand me the result" via `db: AsyncSession = Depends(get_db)`. FastAPI calls `get_db()` for you, automatically, per request. The benefit: in tests, you can tell
FastAPI "use THIS fake `get_db()` instead" without touching the route code at all (see Section 11).

### How DI works internally

FastAPI inspects the route function signature at **import time** using `inspect.signature()`. For each parameter annotated with `Depends(...)`, it builds a **dependency graph** (DAG), resolves sub-dependencies recursively, and caches results **per request** by default.

```
Depends(get_db)
    │
    └─ Depends(get_settings)   ← resolved once, cached for lifetime of request
```

### Dependency scopes

```python
from fastapi import Depends
from functools import lru_cache
from app.core.config import Settings

# --- Application-scoped (singleton) ---
@lru_cache                   # Python's built-in memoization decorator: the FIRST call actually
                              # runs the function and remembers the result; every later call
                              # (from any request) just returns that same cached object instantly.
def get_settings() -> Settings:
    return Settings()        # reads env vars once — no need to re-parse them on every request

# --- Request-scoped (default) ---
async def get_db(settings: Settings = Depends(get_settings)):
    # note: get_db itself depends on get_settings — dependencies can be nested/chained,
    # and FastAPI resolves the whole chain automatically (the "dependency graph" mentioned above)
    async with AsyncSessionLocal() as session:   # open one new DB session for this request
        try:
            yield session                         # ← hand the session to the route; pauses HERE while the route runs
            await session.commit()                # after the route finishes successfully, save all DB changes
        except Exception:
            await session.rollback()              # if the route raised an error, undo any partial DB changes
            raise                                  # re-raise so the error still reaches FastAPI's exception handlers
        finally:
            await session.close()                 # ALWAYS release the session back to the pool, success or failure

# --- Reusable class-based dependency ---
class Pagination:
    # a class can be a dependency too — FastAPI calls Pagination(...) like a function,
    # extracting page/size from the URL's query params using the same Query(...) syntax as before
    def __init__(self, page: int = 1, size: int = Query(20, le=100)):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size   # precompute the DB "OFFSET" value once, so routes don't repeat this math

@router.get("/")
async def list_items(
    p: Pagination = Depends(),        # note: Depends() with NO argument — FastAPI infers "use the Pagination class itself"
    db: AsyncSession = Depends(get_db),
):
    ...
```

### Dependency for permission checking

```python
from fastapi import Security
from fastapi.security import SecurityScopes

def require_scope(*scopes: str):
    # *scopes means this function accepts any number of string arguments, e.g.
    # require_scope("admin:write", "admin:read") — collected into a tuple called `scopes`.
    """Factory that returns a dependency enforcing OAuth2 scopes."""
    async def _check(
        # Security() is like Depends() but specifically for auth — it also lets FastAPI
        # document which "scopes" (permissions) this route requires, in the OpenAPI schema.
        token_data: TokenData = Security(get_current_user, scopes=list(scopes)),
    ) -> TokenData:
        return token_data   # if we reach this line, get_current_user already verified the scopes; just pass it through
    return _check   # require_scope(...) itself returns a NEW dependency function, ready to be used with Depends(...)

# Usage on route
@router.delete("/{id}", dependencies=[Depends(require_scope("admin:write"))])
# dependencies=[...] (as opposed to a named parameter) means: "run this check before the route,
# but I don't need its return value inside my function" — a pure gate/guard.
async def delete_user(id: UUID): ...
```

### use_cache=False — when to disable caching

```python
# Two different DB sessions needed in one handler — disable caching
@router.post("/transfer")
async def transfer(
    src_db: AsyncSession = Depends(get_db),                    # 1st call to get_db() — result gets cached for this request
    dst_db: AsyncSession = Depends(get_db, use_cache=False),    # 2nd call — normally FastAPI would just REUSE src_db's
                                                                  # cached session here (same dependency function = same
                                                                  # result, by default). use_cache=False forces a brand
                                                                  # new, independent session instead — needed here because
                                                                  # transferring money between two accounts genuinely
                                                                  # requires two separate DB sessions.
):
    ...
```

---

## 5. Authentication & Authorization

**Beginner recap:** *Authentication* answers "who are you?" (logging in). *Authorization* answers "are you allowed
to do this?" (permissions). A common pattern: when a user logs in with a password, the server gives back a **JWT**
(JSON Web Token) — a signed, tamper-proof string containing info like "this is user #42, valid until 3pm." On every
future request, the client sends that token back (usually in an `Authorization: Bearer <token>` header), and the
server verifies its signature instead of asking for the password again. "Refresh tokens" exist because access
tokens are made short-lived on purpose (so a stolen one expires fast); the refresh token is a longer-lived,
more carefully protected token used only to get a new access token.

**Used in production?** Yes, extremely widely — JWT access + refresh token pairs are the industry-standard
auth pattern for APIs at companies of every size (this is essentially what you get by default from Auth0,
AWS Cognito, Supabase Auth, and Firebase Auth under the hood). `httpOnly` cookies for storing the refresh
token specifically (shown below) is the current best-practice recommendation from OWASP for browser-based
apps, because it's inaccessible to JavaScript and therefore immune to token theft via XSS.

### JWT with refresh tokens (production pattern)

```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError                        # python-jose: encodes/decodes/verifies JWTs
from passlib.context import CryptContext              # passlib: safely hashes and checks passwords
from fastapi import HTTPException, status

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
# bcrypt is a slow-by-design hashing algorithm — intentionally slow so that even if your password
# database leaks, brute-forcing every hash takes an impractically long time.

SECRET_KEY = "change-me-use-vault"     # NEVER hardcode this in real code — load from env vars / a secrets manager
ALGORITHM = "HS256"                     # the signing algorithm used to make the JWT tamper-proof
ACCESS_TOKEN_EXPIRE  = timedelta(minutes=15)   # short-lived on purpose — limits damage if one leaks
REFRESH_TOKEN_EXPIRE = timedelta(days=7)       # longer-lived, but stored more carefully (httpOnly cookie, below)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)   # turns "mypassword123" into an irreversible hash string to store in the DB

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)   # re-hashes `plain` internally and compares — never decrypts `hashed`

def create_token(subject: str, expires: timedelta, token_type: str = "access") -> str:
    payload = {
        "sub": subject,                                  # "subject" — WHO this token is about, e.g. the user's id
        "type": token_type,                               # "access" or "refresh" — lets decode_token tell them apart
        "exp": datetime.now(timezone.utc) + expires,      # "expiry" — the exact time this token stops being valid
        "iat": datetime.now(timezone.utc),                # "issued at" — when this token was created
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # jwt.encode signs `payload` with SECRET_KEY, producing a string like "xxxxx.yyyyy.zzzzz".
    # Anyone can READ the payload (it's just base64, not encrypted!) but nobody can MODIFY it
    # without knowing SECRET_KEY — that's what makes it "tamper-proof", not "secret".

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # jwt.decode both verifies the signature (raises JWTError if it's been tampered with or
        # expired) AND parses the payload back into a Python dict, in one call.
        if payload.get("type") != "access":
            # defends against someone trying to use a "refresh" token where an "access" token
            # is expected — even though both are signed by the same key, we still check the `type`
            raise HTTPException(status_code=401, detail="Wrong token type")
        return payload
    except JWTError:
        # covers: signature invalid, token expired, malformed token, wrong algorithm, etc.
        raise HTTPException(status_code=401, detail="Invalid token")
```

```python
# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
# this object doesn't do the actual login — it's a DEPENDENCY that, on every protected route,
# reads the "Authorization: Bearer <token>" header and hands you back just the raw token string.
# tokenUrl="/api/v1/auth/token" is only used to tell the Swagger UI where the "login" button should POST to.

@router.post("/token")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),   # auto-parses standard OAuth2 form fields: username, password
    svc: AuthService = Depends(get_auth_service),
    response: Response = None,                      # inject the raw Response object so we can set a cookie on it
):
    user = await svc.authenticate(form.username, form.password)   # verify credentials, raises if wrong
    access  = create_token(str(user.id), ACCESS_TOKEN_EXPIRE)               # short-lived token, sent back in the body
    refresh = create_token(str(user.id), REFRESH_TOKEN_EXPIRE, "refresh")   # long-lived token, sent as a cookie instead

    # Refresh token in httpOnly cookie — not in body
    response.set_cookie(
        key="refresh_token", value=refresh,
        httponly=True,    # JavaScript in the browser CANNOT read this cookie — blocks XSS attacks from stealing it
        secure=True,       # only ever sent over HTTPS, never plain HTTP
        samesite="lax",    # browser won't send this cookie on most cross-site requests — mitigates CSRF
        max_age=int(REFRESH_TOKEN_EXPIRE.total_seconds()),   # cookie auto-expires in the browser after 7 days
    )
    return {"access_token": access, "token_type": "bearer"}
    # only the ACCESS token goes in the response body — the client stores it (e.g. in memory)
    # and sends it as "Authorization: Bearer <access_token>" on every future request.

async def get_current_user(
    token: str = Depends(oauth2_scheme),   # extracts the token string from the Authorization header
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)                          # verify signature + expiry, get back {"sub": "...", ...}
    user = await db.get(User, UUID(payload["sub"]))         # look up the actual user row using the id stored in "sub"
    if not user or not user.is_active:
        raise HTTPException(401, "Inactive user")            # token was valid, but the user doesn't exist / was disabled
    return user   # any route that does `Depends(get_current_user)` now gets the real, verified User object
```

### Role-based access control (RBAC)

```python
from enum import StrEnum

class Role(StrEnum):
    # a fixed set of allowed role names — using an Enum instead of raw strings prevents typos
    # like "Admin" vs "admin" from silently creating a role that doesn't match anything
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN  = "admin"

ROLE_HIERARCHY = {Role.VIEWER: 0, Role.EDITOR: 1, Role.ADMIN: 2}
# gives each role a numeric rank, so "is this role at least as powerful as that role?"
# becomes a simple number comparison instead of listing every valid combination by hand

def require_role(minimum: Role):
    # a "dependency factory" — a function that BUILDS and returns a dependency,
    # customized by the `minimum` argument you pass in (same pattern as require_scope earlier)
    async def _check(current: User = Depends(get_current_user)) -> User:
        # first, get_current_user() runs — proving the request has a valid, logged-in user at all
        if ROLE_HIERARCHY[current.role] < ROLE_HIERARCHY[minimum]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current   # role check passed — hand back the user object in case the route wants it
    return _check

@router.delete("/{id}", dependencies=[Depends(require_role(Role.ADMIN))])
# require_role(Role.ADMIN) is called ONCE, here, to build the specific "must be ADMIN" checker,
# which is then wrapped in Depends(...) and runs before delete_item on every request to this route
async def delete_item(id: UUID): ...
```

### API key authentication

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
# reads whatever value the client sent in the "X-API-Key" request header.
# auto_error=False means: if the header is MISSING, don't immediately throw a 403 —
# instead let `api_key` come through as None, so our own code below can decide how to respond.

async def get_api_client(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> ApiClient:
    if not api_key:
        raise HTTPException(401, "API key required")   # header was missing entirely
    client = await db.scalar(select(ApiClient).where(ApiClient.hashed_key == hash_key(api_key)))
    # NOTE: we hash the incoming key and compare hashes in the DB — the raw API key is
    # never stored anywhere, same principle as password hashing above.
    if not client or not client.is_active:
        raise HTTPException(403, "Invalid API key")     # header was present, but didn't match any active client
    return client   # a valid, active API client — routes can use this to identify WHO is calling, for rate limits etc.
```

---

## 6. Middleware & Lifecycle

**Beginner recap:** Middleware is code that runs on **every single request**, before it reaches your route function
(and often again on the way out, before the response is sent to the client) — like a security checkpoint every
request must pass through. Common uses: logging every request, adding CORS headers, timing how long each request
took, or rejecting requests from disallowed domains. "Lifecycle" (or `lifespan`) refers to code that runs once when
the server **starts up** (e.g. connect to the database) and once when it **shuts down** (e.g. close those
connections) — not per-request, just once for the whole app's lifetime.

### Custom middleware (Starlette BaseHTTPMiddleware)

```python
import time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # `dispatch` is called for EVERY incoming request, before it reaches any route.
        # Whatever runs BEFORE `call_next(request)` happens on the way IN;
        # whatever runs AFTER it happens on the way OUT, once the route has finished.
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        # reuse the client's own request id if they sent one (useful for distributed tracing
        # across multiple services), otherwise generate a fresh unique one
        request.state.request_id = request_id
        # `request.state` is a scratch space attached to this one request — anything you put here
        # is readable later by the route handler, other middleware, or exception handlers
        request.state.start_time = time.perf_counter()   # a high-precision clock reading, to measure duration

        response = await call_next(request)
        # this is the line that actually runs the matching route function (and any middleware
        # registered "closer" to it) — execution pauses here until the route returns its response

        elapsed = (time.perf_counter() - request.state.start_time) * 1000   # milliseconds elapsed
        response.headers["X-Request-Id"] = request_id          # send the same id back so client/logs can correlate
        response.headers["X-Response-Time"] = f"{elapsed:.2f}ms"   # helpful for debugging slow requests in prod
        return response   # this is what actually gets sent back to the client

app.add_middleware(RequestContextMiddleware)   # registers it — FastAPI now runs this for every request automatically
```

### CORS (critical for production)

```python
from fastapi.middleware.cors import CORSMiddleware
# CORS = Cross-Origin Resource Sharing. Browsers block a webpage on domain-a.com from calling
# an API on domain-b.com UNLESS that API explicitly says "yes, domain-a.com is allowed to call me."
# This middleware is what sends those "yes, allowed" headers.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,    # the exact list of frontend domains allowed to call this API;
                                             # never ["*"] (allow everyone) in prod if allow_credentials=True — security risk
    allow_credentials=True,                 # allow the browser to send cookies/auth headers along with cross-origin requests
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],   # which HTTP methods cross-origin callers may use
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],   # which request headers they're allowed to send
    expose_headers=["X-Request-Id", "X-Response-Time"],        # which RESPONSE headers JS is allowed to read
                                                                  # (browsers hide most response headers from JS by default)
    max_age=600,   # browsers cache the "is this allowed?" preflight check for 600 seconds, reducing extra round-trips
)
```

### GZip & Trusted Host

```python
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
# automatically compresses any response body bigger than 1000 bytes before sending it —
# smaller payloads over the network, at the cost of a little CPU time to compress/decompress

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.internal"])
# rejects any request whose "Host" header doesn't match this allowlist (protects against
# certain cache-poisoning / host-header-injection attacks where a request claims to be for a
# different domain than the one actually running)
```

### Rate limiting (slowapi)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
# key_func decides HOW to group requests for counting — here, by client IP address.
# default_limits applies to every route unless overridden: max 200 requests/minute per IP.
app.state.limiter = limiter                       # store it on app.state so it's reachable from anywhere
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# registers a handler (same @app.exception_handler idea from Section 10) so that when the
# limit IS exceeded, the client gets a clean 429 "Too Many Requests" response automatically

@router.get("/")
@limiter.limit("10/minute")    # per-route override — this specific route is stricter (10/min) than the app default (200/min)
async def sensitive_endpoint(request: Request): ...
```

### Lifespan events (preferred over @app.on_event)

```python
from contextlib import asynccontextmanager
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup --- (runs once, before the app starts accepting any requests)
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    # one shared HTTP client, reused across ALL requests — much cheaper than creating
    # a new client (and its own connection pool) inside every single route handler
    app.state.redis = await aioredis.from_url(settings.redis_url)
    yield
    # the app runs and serves requests while paused here, exactly like the DB session pattern earlier
    # --- shutdown --- (runs once, after the app stops accepting new requests)
    await app.state.http_client.aclose()   # release the HTTP client's connections cleanly
    await app.state.redis.aclose()          # release the Redis connection cleanly

app = FastAPI(lifespan=lifespan)   # wire this whole startup/shutdown block into the app
```

---

## 7. Database Integration (Async SQLAlchemy)

**Beginner recap:** SQLAlchemy is an ORM (Object-Relational Mapper) — it lets you work with database rows as Python
objects (`user.email`) instead of writing raw SQL strings everywhere. A "session" is a temporary workspace for one
request's worth of database work: you `add()` objects to it, and `commit()` saves everything at once (or
`rollback()` undoes everything if something failed). "Async" SQLAlchemy just means the database calls use
`await`, so the server can handle other requests while waiting on the database (see the async explanation in
Section 0). The "Repository pattern" further down just means: put all your raw database queries inside a dedicated
class (e.g. `UserRepository`), so your business logic (services) never has to know SQL/SQLAlchemy details directly.

**Used in production?** Yes — async SQLAlchemy 2.0 is the mainstream choice for async Python APIs (it's what's
recommended in FastAPI's own official docs). The Repository pattern specifically is common in medium-to-large
codebases (it makes swapping databases or unit-testing business logic without a real DB much easier), but plenty
of smaller production services skip it and call SQLAlchemy directly from the service layer — it's a
complexity/flexibility trade-off, not a hard requirement.

### Session factory

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    settings.database_url,          # postgresql+asyncpg://... — the connection string, including which async driver to use
    pool_size=20,                    # keep 20 database connections open and ready to reuse, instead of opening a
                                      # fresh TCP connection to Postgres on every single request (that's slow)
    max_overflow=10,                 # if all 20 are busy, temporarily allow up to 10 EXTRA connections during traffic spikes
    pool_pre_ping=True,              # detect stale connections — before handing out a pooled connection, send a
                                      # tiny test query first, in case the DB silently closed it (e.g. after a network blip)
    pool_recycle=3600,               # force-close and replace any connection older than 1 hour (avoids issues with
                                      # DB servers or load balancers that kill very long-lived connections)
    echo=settings.db_echo,           # if True, prints every SQL statement to the console — useful in dev, noisy in prod
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,         # normally, after commit(), SQLAlchemy "expires" objects so accessing their
                                      # attributes triggers a fresh DB query. False keeps them usable in memory
                                      # after commit — important since we often return the object right after saving it.
    class_=AsyncSession,             # use the async-flavored Session class (so all its methods are awaitable)
)
```

### Base model with audit fields

```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, DateTime
from uuid import UUID, uuid4
import datetime

class Base(DeclarativeBase):
    # every table/model class in the app will inherit from this — SQLAlchemy uses it
    # to track all your models together (e.g. for Base.metadata.create_all(...) earlier)
    pass

class TimestampMixin:
    # a "mixin" — a reusable chunk of columns you can add to ANY model via multiple inheritance,
    # e.g. `class User(Base, TimestampMixin): ...` gives User both created_at and updated_at for free
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
        # server_default=func.now() means the DATABASE itself fills this in at insert time
        # (using its own clock), rather than relying on the Python app's clock
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False   # onupdate=func.now() re-stamps this column automatically on every UPDATE
    )

class UUIDMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # default=uuid4 means a random UUID is generated in Python BEFORE insert (as opposed to
    # server_default, which would ask the database to generate it) — either works, this is just one choice
```

### Repository pattern

```python
# app/repositories/user_repo.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from uuid import UUID

class UserRepository:
    # this class's ONLY job is talking to the `users` table — no business rules live here,
    # just "how do I fetch/save a User row" (business rules belong in the service layer, Section 10)
    def __init__(self, db: AsyncSession):
        self.db = db   # the session is handed in from outside (via Depends chain below) — not created here

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)
        # `.get()` is SQLAlchemy's shortcut for "look up by primary key" — returns None if not found,
        # instead of raising an error

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)   # builds a SQL query object: SELECT * FROM users WHERE email = :email
        return await self.db.scalar(stmt)
        # `.scalar()` executes the query and returns just the FIRST matching row (or None) —
        # use this when you expect at most one result, like a unique email lookup

    async def paginate(self, page: int, size: int) -> tuple[list[User], int]:
        offset = (page - 1) * size                          # e.g. page=3, size=20 → skip the first 40 rows
        stmt = select(User).offset(offset).limit(size)       # SELECT ... OFFSET 40 LIMIT 20 — one page of results
        count_stmt = select(func.count()).select_from(User)  # a SEPARATE query: SELECT COUNT(*) FROM users
        users  = list((await self.db.scalars(stmt)).all())
        # `.scalars()` (plural) returns MULTIPLE rows, unlike `.scalar()` above; `.all()` collects them into a list
        total  = await self.db.scalar(count_stmt)             # total row count across ALL pages, not just this page
        return users, total or 0   # `total or 0` guards against None if the table is somehow empty

    async def create(self, user: User) -> User:
        self.db.add(user)          # stage the new User object to be inserted (not written to the DB yet)
        await self.db.flush()      # get the DB-generated id before commit
        # flush() sends the pending INSERT to the database NOW (so `user.id` becomes available if the
        # DB generates it), but does NOT yet make it permanent — that still requires commit()
        # (commit() itself happens later, in get_db()'s try/except block from Section 4)
        return user

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
    # this is itself a dependency — a route can write `repo: UserRepository = Depends(get_user_repo)`
    # and FastAPI will resolve get_db() first, then pass its session into UserRepository automatically
```

### Alembic migrations (async)

```ini
# alembic.ini
script_location = alembic
sqlalchemy.url = driver://  # overridden in env.py
```

```python
# alembic/env.py  — async pattern
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.base import Base
import asyncio

config = context.config
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        url=settings.database_url,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

---

## 8. Background Tasks & Celery

**Beginner recap:** Sometimes you want to respond to the client immediately, but still do some extra work
afterward — e.g. "user was created successfully" should be returned right away, while "send them a welcome email"
can happen a moment later without making the client wait for the email to actually send. `BackgroundTasks` is
FastAPI's simplest tool for this: schedule a function to run right after the response is sent, in the same process.
Celery is a more robust (but heavier to set up) system for this same idea — it runs the task in a **completely
separate process** (a "worker"), so it survives even if your API server restarts, and it can automatically retry on
failure. Rule of thumb: quick, low-stakes tasks → `BackgroundTasks`; anything that must not be lost or takes a while
→ Celery (or a similar task queue).

**Used in production?** Both, but for different scales. `BackgroundTasks` is genuinely fine in production for
truly fire-and-forget, low-stakes work (analytics pings, cache warming) where losing a task occasionally is
acceptable. Celery (or ARQ/Dramatiq) is what's actually running behind almost every production app that does
"real" async work at scale — e.g. sending emails, processing uploaded files, generating reports, ML inference
jobs — specifically BECAUSE it survives server restarts and retries automatically, which `BackgroundTasks`
cannot do (if the server crashes mid-task, that task is just gone).

### FastAPI BackgroundTasks (lightweight, in-process)

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str):
    # runs after the response is sent — still in same process/loop
    await email_client.send(to=email, subject="Welcome!", body=f"Hi {name}")

@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    bg: BackgroundTasks,   # FastAPI injects a fresh BackgroundTasks collector for this one request automatically
    svc: UserService = Depends(get_user_service),
):
    user = await svc.create(body)                              # do the important work FIRST — save the user
    bg.add_task(send_welcome_email, user.email, user.name)
    # this does NOT run send_welcome_email right now — it just REMEMBERS "run this function,
    # with these arguments, after the response has been sent." Note there's no `await` here;
    # you're not calling the function, just registering it.
    return user   # client gets this response immediately; send_welcome_email runs right after, in the background
```

**Limitations**: dies with the process, no retry, no queue visibility. Use Celery for anything critical.

### Celery with Redis (production pattern)

```python
# app/worker/celery_app.py
from celery import Celery

celery = Celery(
    "app",
    broker=settings.redis_url,          # Redis is where pending tasks get stored, waiting to be picked up
    backend=settings.redis_url,          # also use Redis to store each task's RESULT/status after it finishes
    include=["app.worker.tasks"],        # tells Celery which module(s) contain @celery.task-decorated functions
)
celery.conf.update(
    task_serializer="json",              # tasks' arguments are serialized as JSON when sent to Redis
    result_serializer="json",
    accept_content=["json"],             # only accept JSON-encoded tasks (security: rejects unsafe formats like pickle)
    timezone="UTC",
    task_track_started=True,             # record a "started" state, not just "pending"/"finished" — useful for monitoring
    task_acks_late=True,              # ack only after success — at-least-once
    # "ack" (acknowledge) tells Redis "this task is done, remove it from the queue."
    # acks_late means: only send that ack AFTER the task finishes successfully. If the worker
    # crashes mid-task, the un-acked task goes back on the queue and another worker retries it.
    worker_prefetch_multiplier=1,     # fair dispatch
    # by default a worker grabs several tasks ahead of time; setting this to 1 means it only
    # takes ONE task at a time, so a slow task doesn't hog work that other idle workers could do
    task_routes={"app.worker.tasks.send_email": {"queue": "email"}},
    # sends this specific task to its own dedicated "email" queue, instead of the default queue —
    # lets you scale/monitor email-sending workers independently from other task types
)

# app/worker/tasks.py
from app.worker.celery_app import celery

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
# bind=True gives the function access to `self` (the task instance itself), needed to call self.retry(...) below
def send_email_task(self, to: str, subject: str, body: str):
    # note: this is a regular `def`, not `async def` — Celery workers run in their own separate
    # process, so blocking calls here don't affect your FastAPI server's event loop at all
    try:
        email_client.send_sync(to, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)
        # instead of letting the task fail permanently, ask Celery to try again later
        # (up to max_retries=3 times, waiting default_retry_delay=60 seconds between attempts)

# Dispatching from FastAPI
@router.post("/notify")
async def notify(body: NotifyRequest):
    send_email_task.apply_async(
        args=[body.email, body.subject, body.message],   # the arguments send_email_task will be called with
        countdown=0,   # run it as soon as a worker is free (0 seconds delay) — could be set higher to "schedule for later"
    )
    # apply_async() just pushes the task description onto the Redis queue and returns immediately —
    # it does NOT wait for send_email_task to actually run
    return {"status": "queued"}   # client gets an instant response; the actual email send happens in a separate worker process
```

---

## 9. WebSockets & Server-Sent Events

**Beginner recap:** Normal HTTP is a one-shot exchange: client asks, server answers, connection closes. That's not
great for things like a chat app, where the server needs to push new messages to the client at any moment, without
the client having to keep asking "anything new? anything new?" **WebSockets** open a persistent, two-way connection
— both client and server can send messages to each other at any time, for as long as the connection stays open.
**Server-Sent Events (SSE)** are a simpler, one-way alternative: the server can keep pushing updates to the client
over time (e.g. progress updates), but the client can't send messages back over that same connection. Use
WebSockets for true two-way real-time communication (chat, live collaboration); use SSE for simpler "stream updates
to the client" cases (progress bars, live feeds).

### WebSocket connection manager

```python
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import json

class ConnectionManager:
    # tracks WHICH open WebSocket connections belong to WHICH "room" (e.g. a chat channel),
    # so a message from one user can be broadcast to everyone else in the same room
    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # defaultdict(set) means: accessing self._rooms["new_room"] for the first time
        # automatically creates an empty set() for it, instead of raising a KeyError

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()                 # completes the WebSocket "handshake" — required before sending/receiving
        self._rooms[room].add(ws)          # remember this connection as part of `room`

    def disconnect(self, ws: WebSocket, room: str):
        self._rooms[room].discard(ws)      # `.discard()` (unlike `.remove()`) doesn't error if `ws` isn't in the set

    async def broadcast(self, room: str, message: dict):
        dead = set()
        for ws in self._rooms[room]:                  # loop over every connection currently in this room
            try:
                await ws.send_json(message)             # push this message out to that one client
            except Exception:
                dead.add(ws)   # sending failed — that connection is broken/closed; mark it for removal
        self._rooms[room] -= dead   # clean up any dead connections we found while broadcasting

manager = ConnectionManager()   # one shared instance for the whole app, tracking every room/connection

@router.websocket("/ws/{room_id}")   # a DIFFERENT decorator from @router.get/.post — sets up a WebSocket route, not plain HTTP
async def websocket_endpoint(
    ws: WebSocket,
    room_id: str,
    token: str = Query(...),          # auth via query param for WS
    # WebSockets can't send custom Authorization headers as easily as normal HTTP requests
    # from a browser, so auth info is commonly passed as a query param instead: /ws/room1?token=xyz
):
    user = await authenticate_ws_token(token)     # verify the token BEFORE accepting the connection
    await manager.connect(ws, room_id)             # accept the connection and register it in this room
    try:
        while True:   # keep listening for as long as the connection stays open
            data = await ws.receive_json()                                     # wait for the next message from THIS client
            await manager.broadcast(room_id, {"user": str(user.id), **data})
            # re-send it out to EVERYONE in the room (including tagging who sent it) —
            # `**data` unpacks the dict so its keys sit alongside "user" in the final message
    except WebSocketDisconnect:
        # this exception is automatically raised when the client closes the connection or disconnects
        manager.disconnect(ws, room_id)   # clean up so this dead connection doesn't get broadcast to anymore
```

### Server-Sent Events (SSE)

```python
from starlette.responses import StreamingResponse
import asyncio

async def event_generator(topic: str):
    # a generator function (uses `yield`, not `return`) — instead of computing one final
    # value and finishing, it can produce a stream of values over time, on demand
    while True:
        event = await pubsub.get(topic)          # wait for next event
        # blocks here until something publishes a new event on this topic — while waiting,
        # the event loop is free to serve other requests (same non-blocking await behavior as always)
        yield f"data: {event.json()}\n\n"
        # SSE has a required text format: each message starts with "data: " and ends with
        # a blank line (\n\n) — that's how the browser's EventSource API knows one message ends
        if event.type == "done":
            break   # stop the stream entirely — no more events will be sent, connection closes

@router.get("/stream/{topic}")
async def stream(topic: str, current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        event_generator(topic),                  # pass in the generator — FastAPI will pull values from it over time
        media_type="text/event-stream",           # tells the browser "this is an SSE stream," triggering EventSource-style handling
        headers={
            "Cache-Control": "no-cache",           # don't let browsers/proxies cache a live event stream
            "X-Accel-Buffering": "no",   # disable nginx buffering
            # without this, nginx (a common reverse proxy) might wait to accumulate a full
            # buffer of data before forwarding it to the client, defeating the whole point
            # of "streaming" — this header tells nginx to forward chunks immediately instead
        },
    )
```

---

## 10. Error Handling & Custom Exceptions

### 10.0 First Principles: What Actually Happens When Code Raises an Error?

Before any FastAPI-specific code, understand the base mechanics:

```
Normal flow:
  route handler runs line by line
  → returns a value
  → FastAPI serializes it to JSON
  → client gets 200 OK

Error flow:
  route handler hits a `raise SomeError(...)`
  → Python STOPS executing the rest of that function immediately
  → the exception "bubbles up" the call stack (service → route → FastAPI)
  → FastAPI looks for something that knows how to handle THIS exception type
  → that handler decides what status code + body to send back
```

The key idea: **raising an exception is just a way of saying "stop, and let someone up the chain deal with this."** In web APIs, "dealing with it" means turning the Python exception into an HTTP response (a status code + a JSON body).

### 10.1 The Simplest Possible Way: `HTTPException`

FastAPI ships with a built-in exception you can raise directly from a route:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

fake_users_db = {1: {"name": "Alice"}, 2: {"name": "Bob"}}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_users_db[user_id]
```

What happens when you call `GET /users/99`:

```
1. user_id = 99, not in fake_users_db
2. raise HTTPException(status_code=404, detail="User not found")
3. FastAPI catches this automatically (it has a BUILT-IN handler for HTTPException)
4. Response sent to client:

   HTTP/1.1 404 Not Found
   {"detail": "User not found"}
```

This is enough for small apps/prototypes. `raise HTTPException(...)` short-circuits the function immediately — no `return` needed, nothing after it runs.

```python
@app.get("/divide/{a}/{b}")
async def divide(a: float, b: float):
    if b == 0:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    return {"result": a / b}   # only reached if b != 0
```

### 10.2 The Problem With Using `HTTPException` Everywhere

As an app grows, this gets messy:

```python
# app/services/user_service.py  — a "service" is just business logic, no web stuff
from fastapi import HTTPException     # ← problem: business logic importing a web framework!

class UserService:
    async def get_by_id(self, user_id: int):
        user = await self.repo.find(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")  # ← knows about HTTP
        return user
```

Why this is bad in a real codebase:

```
1. Your business logic (UserService) now depends on FastAPI.
   If tomorrow you reuse UserService in a CLI script, a scheduled job,
   or a gRPC service — it doesn't make sense to "raise a 404" there.
   404 is an HTTP concept, not a business concept.

2. It's inconsistent. Different developers pick different status codes
   or wording for the same kind of error, because it's typed by hand
   every time.

3. You can't easily test "was this the right business error?"
   without also checking the exact HTTP status/string.
```

The fix: **separate "what went wrong" (a domain exception) from "what HTTP status to send" (a translation step).**

### 10.3 Custom Exceptions: Your Own Vocabulary for Errors

Instead of the generic `HTTPException`, define exceptions that describe **business** situations, using plain Python classes:

```python
# app/core/exceptions.py

class AppException(Exception):
    """Base class for every error our application knows about."""
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        # self.__class__.detail = the DEFAULT detail set on whichever
        # subclass was actually instantiated (see explanation below)
        self.detail = detail or self.__class__.detail


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource already exists"


class BusinessRuleError(AppException):
    status_code = 422
    detail = "Business rule violation"
```

**Beginner note — why does `AppException` extend `Exception`?** In Python, ANY class that inherits from the built-in `Exception` can be used with `raise` and `except`. This is not FastAPI magic — it's plain Python:

```python
class MyError(Exception):
    pass

raise MyError("something broke")   # works with zero web framework involved
```

**Beginner note — why don't `NotFoundError`/`ConflictError` define their own `__init__`?** Because they don't need to change how the object is constructed — they only override the *default* `detail` text as a class attribute. Python automatically reuses the parent's `__init__` if a subclass doesn't define one. That's why there's no `super().__init__()` call anywhere here: nothing is being overridden.

Now the service layer looks like this — **no FastAPI import at all**:

```python
# app/services/user_service.py
from app.core.exceptions import NotFoundError

class UserService:
    async def get_by_id(self, user_id: int):
        user = await self.repo.find(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user
```

This class could be dropped into a CLI tool, a test, or a worker process, and it would behave identically. It has no idea what "404" even means.

### 10.4 Translating Exceptions into HTTP Responses: `exception_handler`

So if `UserService` doesn't know about HTTP, **something** still has to turn `NotFoundError` into a `404 Not Found` HTTP response. That "something" is an **exception handler** — a function you register once, globally, that FastAPI calls automatically whenever a given exception type is raised anywhere in your app.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

app = FastAPI()

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "detail": exc.detail},
    )
```

How this connects, step by step:

```
1. Route calls service.get_by_id(99)
2. Service raises NotFoundError("User 99 not found")
3. Python has NO try/except in the route — the exception just propagates upward
4. FastAPI's routing machinery catches it BEFORE it crashes the server
5. FastAPI checks: "is there a handler registered for NotFoundError,
   or any of its parent classes?"
   → NotFoundError → AppException  ✓ found a handler for AppException!
   (this works because NotFoundError IS-A AppException, via inheritance)
6. app_exception_handler(request, exc) runs
7. Its return value (a JSONResponse) becomes the actual HTTP response
```

This is the payoff of the class hierarchy: **you only need to register a handler for the base `AppException` once**, and it automatically handles `NotFoundError`, `ConflictError`, `BusinessRuleError`, and any future subclass you add — because Python's exception matching checks the whole inheritance chain, not just the exact type.

```
                     AppException  ← handler registered HERE
                    /      |       \
          NotFoundError ConflictError BusinessRuleError  ← all route through the same handler
```

### 10.5 Handling Multiple Kinds of Errors

A real app has more than one category of failure. Register one handler per category:

```python
from fastapi.exceptions import RequestValidationError

def install_exception_handlers(app: FastAPI) -> None:

    # Category 1: our own business/domain errors (expected, safe to show detail)
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # Category 2: request body/query params failed Pydantic validation
    # (e.g. client sent a string where an int was expected)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "detail": exc.errors(),   # a list of {"loc": ..., "msg": ...} entries
                "body": exc.body,
            },
        )

    # Category 3: the safety net — anything we did NOT anticipate.
    # Without this, an unexpected bug (e.g. a typo causing AttributeError)
    # would leak a raw Python traceback to the client and expose internals.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)   # full traceback in logs
        return JSONResponse(status_code=500, content={"error": "InternalServerError"})
```

**Beginner note — why is `Exception` (the catch-all) listed last conceptually but matches everything?** `Exception` is the ancestor of nearly every error type in Python (including `AppException`, since it also extends `Exception`). FastAPI resolves handlers from the *most specific* match first — so a raised `NotFoundError` will hit the `AppException` handler, not accidentally fall into the generic `Exception` handler. The catch-all only fires for truly unexpected errors (bugs, `KeyError`, `ZeroDivisionError`, a database driver crashing, etc.) that don't have a more specific handler registered.

**Beginner note — why is this "safety net" so important?** Without it, an unhandled bug crashes with Python's default behavior — often surfacing a full stack trace (file paths, variable values, sometimes secrets) directly in the HTTP response. That's an information leak and looks unprofessional. The catch-all guarantees every possible error, known or not, produces a clean, consistent JSON response.

### 10.6 Production-Grade Additions

Once the basics above click, real systems typically add a few more things on top:

**a) Stable `error_code` strings, not just HTTP status codes.** A status code like 409 is too coarse — "email already exists" and "cannot delete the last admin" are both 409s but need different handling on the frontend:

```python
class AppException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"   # machine-readable, safe to branch logic on
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, **extra):
        self.detail = detail or self.__class__.detail
        self.extra = extra                # extra structured context, e.g. {"user_id": 99}
```

**b) Exceptions that need their own arguments DO need `super().__init__()`** — this is the one case where you must call it, because you're overriding the parent's `__init__` and still need its logic to run:

```python
class UserNotFoundError(NotFoundError):
    error_code = "user_not_found"

    def __init__(self, user_id: int):
        super().__init__(detail=f"User {user_id} not found", user_id=user_id)
        # ↑ without super().__init__(), self.detail would never get set!
```

**c) Never leak the real error message for unexpected exceptions** — log it internally with a correlation ID, but show the client something generic:

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logger.exception("Unhandled exception [%s]", error_id, exc_info=exc)
    # exc's real message (e.g. a DB connection string) NEVER goes in the response
    return JSONResponse(
        status_code=500,
        content={"error_code": "internal_error", "detail": "Unexpected error", "error_id": error_id},
    )
```

**d) Consistent response shape across every error type**, so the frontend can rely on one contract:

```json
{
  "error_code": "user_not_found",
  "detail": "User 123 not found",
  "request_id": "a1b2c3d4-...",
  "extra": {"user_id": 123}
}
```

**e) Don't `try/except` inside route handlers to hide domain exceptions** — let them bubble up to the global handlers, otherwise you bypass the whole system above and end up back at inconsistent, hand-rolled error responses:

```python
# BAD — silences the exception hierarchy, returns 200 even on failure
@app.post("/users/")
async def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    try:
        return await service.create(data)
    except Exception as e:
        return {"error": str(e)}          # wrong status code, leaks str(e), skips handlers

# GOOD — let it propagate, the registered handler takes care of it
@app.post("/users/", status_code=201)
async def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create(data)      # raises EmailAlreadyExistsError → caught globally
```

### Summary: Beginner → Advanced Path

```
Level 1 (prototype):     raise HTTPException(status_code=404, detail="...")
                         directly inside the route function

Level 2 (small app):     custom exceptions (class NotFoundError(Exception))
                         + one @app.exception_handler per exception type

Level 3 (production):    exception hierarchy (AppException base class)
                         + error_code strings + structured "extra" context
                         + logging with correlation/request IDs
                         + catch-all handler that never leaks internals
                         + service layer has ZERO knowledge of HTTP at all
```

---

## 11. Testing Strategy

**Beginner recap:** Tests are just code that checks other code behaves correctly, automatically, so you don't have
to manually click through your app after every change. There are two flavors here: **unit tests** call a single
function (e.g. `UserService.create`) directly, replacing its dependencies (like the database) with fake "mock"
objects, so the test runs fast and doesn't need a real database. **Integration tests** spin up the actual FastAPI
app and send real HTTP requests to it (via a test HTTP client), checking the full request → response flow, usually
against a real (but temporary/test) database. `dependency_overrides` is how you swap a real dependency (like
`get_db`) for a fake one during tests, using the same DI mechanism from Section 4.

### Test setup with pytest + httpx

```python
# tests/conftest.py
# conftest.py is a special pytest filename — any "fixture" defined here becomes automatically
# available to every test file in the project, without needing to import it manually.
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import create_app          # the factory function from Section 1 — NOT the already-built `app`
from app.db.base import Base
from app.api.deps import get_db

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"
# use a lightweight SQLite file for tests instead of a real Postgres server — fast, and each
# test run starts from a clean, disposable database

@pytest_asyncio.fixture(scope="session")
# a "fixture" is a function that SETS UP something a test needs, then (optionally) tears it down.
# scope="session" means this runs ONCE for the entire test run, not once per individual test —
# creating a whole DB engine per test would be wasteful.
async def engine():
    _engine = create_async_engine(TEST_DB_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # build all tables fresh, once, before any test runs
    yield _engine   # hand the engine to whichever tests need it; test run happens here
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)      # after ALL tests finish, drop every table (cleanup)
    await _engine.dispose()                              # close the engine's connections entirely

@pytest_asyncio.fixture
# no scope= specified → defaults to scope="function", meaning this runs freshly for EVERY test
async def db(engine):
    # `engine` here is the fixture defined above — pytest automatically "injects" it by name,
    # the same dependency-by-parameter-name idea as FastAPI's own Depends()
    async with engine.begin() as conn:
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session      # this specific test runs here, using `session` as its DB
        await session.rollback()       # isolate each test
        # undo ANY changes this test made, so the next test starts from a clean slate,
        # regardless of whether this test passed or failed

@pytest_asyncio.fixture
async def client(db):
    app = create_app()   # build a fresh FastAPI app instance for this test
    app.dependency_overrides[get_db] = lambda: db
    # THIS is the key trick: normally routes call Depends(get_db) to get a real DB session.
    # dependency_overrides tells FastAPI "whenever a route asks for get_db, give it THIS
    # test session instead" — without touching a single line of route code.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # ASGITransport lets httpx talk directly to your FastAPI app in-memory —
        # no real network socket, no need to actually run `uvicorn` for tests to work
        yield ac   # `ac` behaves just like a real HTTP client: ac.get("/users/1"), ac.post(...), etc.
```

### Unit testing services (mock repositories)

```python
# tests/unit/test_user_service.py
from unittest.mock import AsyncMock
import pytest
from app.services.user_service import UserService
from app.schemas.user import UserCreate

@pytest.mark.asyncio   # tells pytest this test function is async and needs to be run inside an event loop
async def test_create_user_sends_email():
    repo    = AsyncMock()   # a fake object that pretends to be UserRepository — records what's called on it
    emailer = AsyncMock()   # a fake EmailService — we don't want a REAL email sent during a unit test
    svc     = UserService(repo=repo, emailer=emailer)
    # inject the FAKE repo/emailer into the real UserService — this is dependency injection again,
    # just done manually in a test instead of via FastAPI's Depends()

    repo.get_by_email.return_value = None       # no existing user
    # tells the mock: "whenever someone calls repo.get_by_email(...), pretend it returned None"
    repo.create.return_value = FakeUser(id=uuid4(), email="a@b.com")
    # tells the mock: "whenever repo.create(...) is called, pretend it returned this fake user"

    await svc.create(UserCreate(email="a@b.com", password="secret"))
    # run the REAL UserService.create logic — but every DB/email call inside it hits our fakes, not real systems

    repo.create.assert_called_once()
    # assertion: verify repo.create WAS actually called (exactly once) — proves the service tried to save the user
    emailer.send_welcome.assert_called_once_with("a@b.com")
    # assertion: verify send_welcome was called with EXACTLY this email — proves the "send welcome email"
    # side effect actually happened, without needing a real email provider in the test
```

### Integration tests

```python
# tests/integration/test_users_api.py
import pytest

@pytest.mark.asyncio
async def test_create_and_get_user(client, auth_headers):
    # `client` and `auth_headers` are both fixtures — pytest automatically finds and injects them
    # by matching these parameter names against fixtures defined in conftest.py
    payload = {"email": "new@example.com", "password": "S3cur3!"}
    r = await client.post("/api/v1/users/", json=payload, headers=auth_headers)
    # sends a REAL (in-memory, via ASGITransport) HTTP POST request through the entire app —
    # routing, DI, Pydantic validation, the service layer, the test database — all of it actually runs
    assert r.status_code == 201                     # verify the API responded with "Created"
    uid = r.json()["id"]                              # pull the newly created user's id out of the JSON response

    r2 = await client.get(f"/api/v1/users/{uid}", headers=auth_headers)
    # now fetch that same user back, to prove it was actually persisted (not just returned once and lost)
    assert r2.status_code == 200
    assert r2.json()["email"] == payload["email"]     # confirm the data round-tripped correctly
```

### pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    unit: mark test as unit test
    integration: mark test as integration test
    slow: mark test as slow
```

---

## 12. Performance & Scalability

**Beginner recap:** "Performance" is about making each request fast; "scalability" is about handling more requests
at once (often by running more copies of your server). A **connection pool** is a set of already-open database
connections that get reused across requests — opening a brand new database connection for every single request is
slow, so instead the app keeps, say, 20 connections ready and "checks one out" per request. **Streaming** a response
means sending data to the client in chunks as it's produced, instead of building the entire response in memory
first — important for large files/exports. **Workers** are separate copies of your app process (each with its own
Python interpreter) running in parallel to use multiple CPU cores, since a single Python process can only use one
core effectively for CPU-bound work.

### Connection pool tuning

```python
engine = create_async_engine(
    url,
    pool_size=20,          # persistent connections
    max_overflow=40,       # burst capacity (total max = pool_size + max_overflow)
    # under heavy load, up to 20 + 40 = 60 connections can be open at once;
    # sizing this too high can overwhelm the DATABASE server itself, so this is tuned
    # against Postgres's own `max_connections` setting divided across all app instances
    pool_timeout=30,       # wait for connection before error
    # if all 60 connections are busy and a new request needs one, wait up to 30 seconds
    # before giving up and raising an error, rather than waiting forever
    pool_recycle=1800,     # recycle connections older than 30 min
    pool_pre_ping=True,    # send SELECT 1 before checkout — detect stale
)
```

### Streaming large responses

```python
from fastapi.responses import StreamingResponse
import csv, io

async def stream_csv(query_result):
    # this is a generator (has `yield`) — it produces CSV text piece by piece,
    # instead of building the ENTIRE csv file in memory before sending anything
    buffer = io.StringIO()                                    # an in-memory "fake file" to write CSV text into
    writer = csv.writer(buffer)
    writer.writerow(["id", "email", "created_at"])            # write the header row into the buffer
    yield buffer.getvalue()                                    # send just the header row to the client right away
    buffer.seek(0); buffer.truncate()                          # empty the buffer out so it's ready for the next chunk

    async for row in query_result:
        # streams rows from the database one at a time, instead of loading the WHOLE
        # query result into memory first — critical if `users` has millions of rows
        writer.writerow([row.id, row.email, row.created_at])
        yield buffer.getvalue()          # send this one row to the client immediately
        buffer.seek(0); buffer.truncate()   # reset the buffer for the next row

@router.get("/export/users.csv")
async def export_users(db: AsyncSession = Depends(get_db)):
    result = await db.stream(select(User))
    # `.stream()` (instead of `.scalars()`) tells SQLAlchemy: don't fetch every row into
    # memory at once — hand rows back to us lazily, as we ask for each one
    return StreamingResponse(
        stream_csv(result),                # FastAPI will pull chunks from this generator as the client downloads them
        media_type="text/csv",             # tells the browser "this is a CSV file," not plain text or JSON
        headers={"Content-Disposition": "attachment; filename=users.csv"},
        # tells the browser to trigger a "Save As users.csv" download, instead of trying to display it inline
    )
```

### Uvicorn production settings

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \              # CPU cores; use Gunicorn+uvicorn workers instead
  --loop uvloop \            # faster event loop
  --http httptools \         # faster HTTP parser
  --no-access-log            # use middleware for structured logs
```

### Gunicorn + Uvicorn workers (recommended)

```bash
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5
```

### Profiling slow endpoints

```python
import cProfile, pstats, io
from fastapi import Request

@app.middleware("http")
async def profile_middleware(request: Request, call_next):
    if "X-Profile" not in request.headers:
        return await call_next(request)
    pr = cProfile.Profile()
    pr.enable()
    response = await call_next(request)
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(20)
    print(s.getvalue())
    return response
```

---

## 13. Security Best Practices

**Beginner recap:** This section is a checklist of common attacks and how to prevent them. **Security headers** tell
the browser to enforce extra protections (e.g. "never let this page be loaded inside an iframe" prevents
clickjacking). **Input sanitization** means cleaning up user-submitted text before storing or displaying it, so a
malicious user can't inject harmful HTML/JavaScript into your app (XSS attack). **SQL injection** is when a user's
input is inserted directly into a raw SQL string, letting an attacker manipulate your query (e.g. typing something
that deletes your whole table) — the fix is to always use "parameterized queries" where the database driver keeps
user input strictly separate from the SQL command itself. **Secrets** (passwords, API keys, DB credentials) should
never be hardcoded or committed to git — they should come from environment variables or a secrets manager, so they
can be rotated without a code change.

### Security headers middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)     # let the actual route run first, then add headers to its response
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            # stops the browser from "guessing" a file's type differently than what the
            # server declared — prevents a malicious file disguised as an image from executing as a script
            "X-Frame-Options": "DENY",
            # forbids this page from ever being loaded inside an <iframe> on another site —
            # prevents "clickjacking" (tricking users into clicking something invisible)
            "X-XSS-Protection": "1; mode=block",
            # legacy header telling older browsers to block detected reflected XSS attacks (modern
            # browsers rely on CSP below instead, but this is kept for backwards compatibility)
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            # tells the browser "always use HTTPS for this domain for the next 2 years (63072000 seconds),
            # even if the user types http:// — never downgrade to plain, unencrypted HTTP"
            "Content-Security-Policy": "default-src 'self'",
            # tells the browser to only load scripts/images/styles/etc. from this SAME domain —
            # blocks a large class of XSS attacks that try to load malicious code from elsewhere
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # controls how much of THIS page's URL gets leaked to external sites when a user clicks a link away
            "Permissions-Policy": "geolocation=(), microphone=()",
            # explicitly disables browser features (like location/mic access) this site never needs,
            # reducing what a compromised script could ever do even if it got injected somehow
        })
        return response
```

### Input sanitization

```python
import bleach
from pydantic import field_validator

class CommentCreate(BaseModel):
    content: str = Field(max_length=2000)   # cap length to prevent absurdly large payloads (also a mini DoS protection)

    @field_validator("content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        allowed_tags = ["b", "i", "em", "strong", "a"]
        # only these specific HTML tags survive — anything else (like <script>) gets stripped out entirely
        return bleach.clean(v, tags=allowed_tags, strip=True)
        # `strip=True` means disallowed tags are REMOVED rather than shown as escaped text (e.g. &lt;script&gt;)
        # runs automatically every time a CommentCreate is built from incoming request data
```

### SQL injection prevention

```python
# ALWAYS use parameterized queries — never f-string SQL
# GOOD — SQLAlchemy ORM / Core with bound parameters
stmt = select(User).where(User.email == email)           # safe
# SQLAlchemy sends `email` to the database as a SEPARATE parameter, not glued into the SQL text —
# so even if `email` contained something like `' OR '1'='1`, the database treats it as literal
# data to search for, never as part of the SQL command itself.

# GOOD — raw SQL with parameters
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),      # `:email` is a placeholder, not string interpolation
    {"email": email},                                        # the actual value is passed separately, here
)

# BAD — never do this
result = await db.execute(f"SELECT * FROM users WHERE email = '{email}'")
# an f-string builds the SQL command AND the user's raw input into ONE string before sending it.
# if `email` were something like `x' OR '1'='1' --`, the resulting query would return EVERY
# user in the table (or worse, be crafted to delete data) — this is the classic SQL injection attack.
```

### Secrets management

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # BaseSettings is a special Pydantic model that automatically reads its field values
    # from environment variables (or a .env file) instead of you writing them in code
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    # tells it WHERE to load values from: a local .env file, useful in development
    # (in production, real env vars set by your deployment platform take priority)

    database_url: SecretStr          # .get_secret_value() to use
    # SecretStr is a Pydantic type that wraps a string so it never accidentally gets
    # printed in logs, error messages, or `repr()` output — it shows as "**********" instead.
    # You must explicitly call .get_secret_value() to get the real string back when you need it.
    jwt_secret: SecretStr
    redis_url: str = "redis://localhost:6379"    # has a default — doesn't have to be set via env var
    debug: bool = False

# SecretStr never appears in logs / repr — critical for security
# e.g. if a stack trace accidentally logs `settings`, the database password won't leak into your log files
```

---

## 14. Caching Patterns

**Beginner recap:** Caching means storing the result of expensive work (a slow database query, an external API
call) somewhere fast (like Redis, an in-memory data store), so the next time the same result is needed, you can
return the stored copy instead of redoing the work. The tricky part is always **invalidation** — knowing when the
cached value is stale and needs to be refreshed or deleted (e.g. after the underlying data changes). A `ttl`
("time to live") is how long a cached value is kept before it automatically expires, even if nothing tells the cache
to invalidate it.

**Used in production?** Yes, universally — Redis specifically is one of the most widely deployed pieces of
infrastructure in web backends (used at essentially every company with meaningful traffic: for caching, session
storage, rate limiting, and as the broker for Celery/ARQ task queues from Section 8). The cache-decorator pattern
shown below is a common in-house approach; larger orgs sometimes reach for a dedicated caching layer library
instead, but the underlying idea (hash the inputs → cache key, check cache before doing real work, `setex` with
a TTL) is exactly what's really happening either way.

### Redis cache decorator

```python
import json, hashlib
from functools import wraps
from typing import Callable, Any
import redis.asyncio as aioredis

def cache(ttl: int = 300, key_prefix: str = ""):
    # this is a "decorator factory" — @cache(ttl=60) itself returns the REAL decorator below,
    # letting you customize ttl/key_prefix per function (same pattern as require_scope in Section 5)
    """Decorator that caches the result of an async function in Redis."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        # @wraps preserves `fn`'s original name/docstring on the wrapper — without it, tools
        # like debuggers would confusingly show every cached function as just "wrapper"
        async def wrapper(*args, **kwargs):
            redis: aioredis.Redis = app.state.redis
            raw = f"{key_prefix}:{fn.__name__}:{args}:{sorted(kwargs.items())}"
            # builds a unique string identifying THIS specific call — same function + same
            # arguments = same string, so it can be looked up again next time
            cache_key = hashlib.sha256(raw.encode()).hexdigest()
            # hash it — keeps the actual Redis key short and safe, regardless of how long/weird
            # the original arguments were

            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)   # cache HIT — skip calling fn() entirely, just return the stored result

            result = await fn(*args, **kwargs)   # cache MISS — actually run the (possibly slow) function
            await redis.setex(cache_key, ttl, json.dumps(result, default=str))
            # setex = "SET with EXpiry" — store the result AND make it auto-delete itself after `ttl` seconds
            return result
        return wrapper
    return decorator

@cache(ttl=60, key_prefix="user")
async def get_user_profile(user_id: str) -> dict:
    return await db_fetch_profile(user_id)
    # the first call for a given user_id actually hits the database; every call for the
    # same user_id within the next 60 seconds returns the cached result instead
```

### HTTP response caching

```python
from fastapi import Response

@router.get("/config")
async def get_public_config(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
    # tells BROWSERS/CDNs (not your server) to cache this response for 300 seconds themselves,
    # so repeat requests don't even reach your API at all; stale-while-revalidate=60 means
    # "even after it expires, it's OK to serve the old cached copy for another 60s while
    # fetching a fresh one in the background" — keeps things feeling instant
    response.headers["ETag"] = compute_config_hash()
    # a fingerprint of the current content — a client can send this back later as
    # "If-None-Match", and if it hasn't changed the server can reply "304 Not Modified"
    # with an empty body instead of resending the whole thing
    return config_data
```

### Cache invalidation with tags

```python
async def invalidate_user_cache(user_id: str, redis: aioredis.Redis):
    """Scan and delete all cache keys for a user."""
    pattern = f"user:*:{user_id}*"           # matches every cache key that mentions this user_id, e.g. "user:profile:42"
    cursor = 0
    # Redis's SCAN command doesn't return everything at once (which could be slow/blocking
    # for huge datasets) — instead it returns a batch of keys plus a "cursor" pointing to
    # where to continue from, so you loop until the cursor comes back to 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        if keys:
            await redis.delete(*keys)    # delete this batch of matching keys
        if cursor == 0:
            break   # 0 means the scan has gone all the way around — we're done
```

---

## 15. Observability: Logging, Tracing, Metrics

**Beginner recap:** "Observability" means being able to understand what your running application is doing without
attaching a debugger — essential once an app is deployed and you can't just print things and re-run it. **Logging**
is writing out text records of events as they happen ("user 42 logged in at 3:05pm"); "structured" logging means
writing them as JSON instead of free text, so log-analysis tools can search/filter them easily. **Tracing** follows
a single request's full journey across multiple services/functions (e.g. API → database → cache), so you can see
exactly which step was slow. **Metrics** are numeric measurements collected over time (requests per second, average
response time) that get graphed on dashboards. A **health check** endpoint (`/health`) is a simple route that
returns "ok" so infrastructure tools (like Kubernetes) can automatically detect if your app has crashed or is stuck.

### Structured logging (structlog)

```python
# app/core/logging.py
import structlog, logging, sys

def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),         # JSON for log aggregators
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

logger = structlog.get_logger()

# In middleware — bind request_id to all subsequent log calls in this request
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        structlog.contextvars.bind_contextvars(
            request_id=request.state.request_id,
            method=request.method,
            path=request.url.path,
        )
        response = await call_next(request)
        structlog.contextvars.unbind_contextvars("request_id", "method", "path")
        return response
```

### OpenTelemetry tracing

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(app: FastAPI, settings: Settings) -> None:
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
```

### Prometheus metrics (prometheus-fastapi-instrumentator)

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_group_untemplated=True,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```

### Health check endpoint

```python
@router.get("/health/live")
async def liveness():
    return {"status": "ok"}
    # "liveness" answers ONE narrow question: "is the Python process itself still running and
    # able to respond at all?" It deliberately does NOT check the database or Redis — if it did,
    # a temporary database blip would cause Kubernetes to needlessly kill and restart a perfectly
    # healthy app process, which wouldn't fix the actual database problem.

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db), request: Request = None):
    # "readiness" answers a DIFFERENT question: "is this instance ready to accept real traffic
    # right now?" — checking its actual dependencies (DB, cache), since a request would fail anyway
    # if those are down, even though the process itself (checked above) is technically alive.
    checks = {}
    try:
        await db.execute(text("SELECT 1"))   # the simplest possible query — just proves the DB connection works
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"          # capture the failure reason instead of crashing this endpoint

    try:
        await request.app.state.redis.ping()   # same idea, for the Redis connection
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    # `all(...)` returns True only if EVERY value in checks is exactly the string "ok"
    return JSONResponse(
        status_code=200 if all_ok else 503,
        # 503 "Service Unavailable" tells Kubernetes (or a load balancer) "stop sending me
        # traffic for now" — it will retry this check periodically and route traffic back
        # automatically once it starts returning 200 again
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
```

---

## 16. Production Deployment

**Beginner recap:** "Deployment" is the process of getting your code running on a real server that users can reach,
instead of just on your laptop. **Docker** packages your app plus everything it needs (Python version, libraries,
system dependencies) into a single portable "image," so it runs identically everywhere — no more "works on my
machine" problems. **Kubernetes** is a system for running many containers (copies of your app) across many
machines, automatically restarting ones that crash, and routing traffic to healthy ones — the "liveness/readiness
probes" below are how Kubernetes checks whether a given copy of your app is healthy. "Zero-downtime deployment"
means rolling out a new version of your code without any user-facing outage, usually by gradually replacing old
instances with new ones while both versions briefly run side by side.

### Dockerfile (multi-stage, minimal)

```dockerfile
# ---- builder ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN adduser --system --group app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", "--timeout", "120"]
```

### Kubernetes readiness/liveness probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

### Environment-based config

```
.env.development   → debug=true, echo SQL
.env.staging       → debug=false, real DBs
.env.production    → pulled from Vault/AWS Secrets Manager at runtime
```

### Zero-downtime deployments

- **Rolling update**: Kubernetes default — gradually replaces pods
- **Blue/Green**: route traffic at load balancer level
- **Canary**: Argo Rollouts or Istio — send N% traffic to new version
- Always ensure your `/health/ready` returns 503 while DB migrations run

---

## 17. Advanced Patterns (CQRS, Event-Driven, DDD)

**Beginner recap:** These are architectural patterns for **large, complex** applications — you generally don't need
them for a small app, and introducing them too early adds unnecessary complexity. **CQRS** (Command Query
Responsibility Segregation) means splitting "code that changes data" (commands, e.g. "create an order") from "code
that reads data" (queries, e.g. "get order summary") into separate code paths, since they often have very different
performance needs. **Event-driven** architecture means different parts of a system communicate by publishing
"something happened" events (e.g. "OrderCreated") rather than calling each other directly — other parts of the
system can react to that event independently. **DDD** (Domain-Driven Design) is about organizing code around
business concepts ("Order", "Payment") and their rules, keeping that logic cleanly separated from technical details
like databases and HTTP. If these ideas feel abstract, it's fine to treat this section as "read when your app
actually grows to need it," rather than something to apply from day one.

### CQRS — Commands vs Queries

```python
# Commands mutate state, Queries read state — separate handlers

class CreateOrderCommand(BaseModel):
    # a "command" is just a Pydantic model describing an INTENT to change something —
    # "please create an order with these items for this user"
    user_id: UUID
    items: list[OrderItemCreate]

class OrderCommandHandler:
    # this class ONLY handles requests that CHANGE data (create/update/delete) —
    # never used for simple reads, which go through OrderQueryHandler instead
    def __init__(self, repo: OrderRepository, event_bus: EventBus):
        self.repo = repo
        self.event_bus = event_bus   # a mechanism for publishing "something happened" events (see outbox pattern below)

    async def handle_create(self, cmd: CreateOrderCommand) -> UUID:
        order = Order.create(user_id=cmd.user_id, items=cmd.items)   # build the domain object with business rules applied
        await self.repo.save(order)                                   # persist it to the database
        await self.event_bus.publish(OrderCreatedEvent(order_id=order.id))
        # tell the REST of the system "an order was just created" — other parts (e.g. sending
        # a confirmation email, updating analytics) can react to this WITHOUT this handler
        # needing to know or care who's listening
        return order.id

class OrderQueryHandler:
    # a COMPLETELY separate class for reading data — note it takes `read_db`, which could even
    # be a different database connection (e.g. a read replica) than the one commands write to
    def __init__(self, read_db: AsyncSession):
        self.db = read_db

    async def get_order_summary(self, order_id: UUID) -> OrderSummaryDTO:
        # Can query a read replica / materialized view
        # queries are often optimized very differently from the write side — here it reads from
        # a pre-computed "order_summaries" view instead of joining live orders+items+users tables,
        # which would be slower and unnecessary just to display a summary
        stmt = text("SELECT * FROM order_summaries WHERE id = :id")
        row = await self.db.execute(stmt, {"id": order_id})
        return OrderSummaryDTO.model_validate(row.mappings().one())
        # `.mappings().one()` gets the single matching row back as a dict-like object;
        # `.model_validate(...)` converts that raw row into a proper Pydantic model to return
```

### Domain events + outbox pattern

```python
# Guarantees at-least-once event delivery without 2-phase commit
class OutboxEntry(Base):
    # the PROBLEM this solves: if you save an order to Postgres, THEN separately publish an
    # "OrderCreated" event to Kafka, there's a gap between those two steps where the app could
    # crash — leaving an order saved but the event never sent (or vice versa). The outbox
    # pattern avoids that by writing the event into the SAME database, in the SAME transaction.
    __tablename__ = "outbox"
    id: Mapped[UUID]
    event_type: Mapped[str]           # e.g. "OrderCreated" — identifies what kind of event this is
    payload: Mapped[dict]   # JSON column
    published_at: Mapped[datetime | None]
    # stays NULL until a separate background process actually publishes it to Kafka/RabbitMQ;
    # once published, it gets stamped with a timestamp so it isn't sent again

# Within the same DB transaction as the business operation:
async def create_order_with_outbox(cmd, db: AsyncSession):
    order = Order(...)
    outbox = OutboxEntry(
        event_type="OrderCreated",
        payload={"order_id": str(order.id), "user_id": str(cmd.user_id)},
        # store just enough info in the JSON payload for whatever reads this later to know what happened
    )
    db.add(order)                     # stage the order for insert...
    db.add(outbox)                    # ...and stage the outbox row for insert, in the SAME session
    await db.commit()      # atomic: order + event saved or neither
    # a single commit() either saves BOTH rows together, or (if something fails) saves NEITHER —
    # there's no possible in-between state where one exists but not the other

# Separate poller publishes outbox entries to Kafka/RabbitMQ
# a background worker periodically does: "SELECT * FROM outbox WHERE published_at IS NULL",
# sends each one to Kafka, then marks it published — decoupled from the original request entirely
```

### Service layer vs repository layer

```
API Layer (FastAPI routes)
    │  validates HTTP, extracts auth, calls service
    ▼
Service Layer (business logic, orchestration, domain rules)
    │  calls repositories, raises domain exceptions
    ▼
Repository Layer (data access, ORM, raw SQL)
    │
    ▼
Database
```

### Dependency inversion for testability

```python
from abc import ABC, abstractmethod
# ABC (Abstract Base Class) lets you define a "contract" — a class that CANNOT be instantiated
# directly, only used as a template that other classes must fully implement

class IUserRepository(ABC):
    # the "I" prefix (a common convention) signals "this is an Interface" — it defines WHAT
    # methods a user repository must have, without saying HOW they work
    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None: ...
    # `...` (Ellipsis) as the body just means "no implementation here — subclasses must provide one"
    @abstractmethod
    async def create(self, user: User) -> User: ...

class SqlUserRepository(IUserRepository):
    # the REAL implementation, used in production — talks to an actual SQL database
    def __init__(self, db: AsyncSession): self.db = db
    async def get_by_id(self, id: UUID): return await self.db.get(User, id)
    async def create(self, user: User):
        self.db.add(user); await self.db.flush(); return user

class InMemoryUserRepository(IUserRepository):
    # a FAKE implementation, used only in tests — stores users in a plain Python dict instead
    # of a real database. Because both classes implement the SAME interface (IUserRepository),
    # any code written against IUserRepository works with EITHER one, unchanged.
    def __init__(self): self._store: dict[UUID, User] = {}
    async def get_by_id(self, id): return self._store.get(id)
    async def create(self, user): self._store[user.id] = user; return user

# Tests use InMemory; production uses Sql — zero DB overhead in unit tests
# this is "dependency inversion": UserService depends on the ABSTRACT IUserRepository,
# never on SqlUserRepository directly — so swapping implementations (real DB ↔ fake) requires
# zero changes to UserService itself, only to what gets passed into it
```

---

## 18. Staff Engineer Interview: Critical Questions

**Beginner recap:** This last section is a rapid-fire Q&A format meant for interview prep at a senior/staff level —
it assumes you're already comfortable with everything in Sections 0–17. If a question or answer below references a
term you don't recognize, it's very likely explained earlier in this document; use Ctrl+F / search for the term to
jump back to its full explanation.

### Architecture questions

**Q: How would you design a FastAPI service to handle 100k req/s?**

- Stateless horizontal scaling behind a load balancer
- Read replicas for query-heavy endpoints
- Redis cache for hot data (user sessions, config, product catalog)
- CDN for static + semi-static responses
- Async throughout — zero blocking calls in event loop
- Connection pooling tuned per pod (pool_size = DB max_connections / num_pods)
- Circuit breakers for downstream services (tenacity / resilience libraries)

**Q: How does FastAPI's DI differ from Spring/NestJS?**

- Python DI is function-signature-based, not class/decorator based
- No IoC container — FastAPI builds the graph at routing time via inspection
- Scopes are simpler: singleton via `lru_cache`, request-scoped via `Depends` with `yield`
- No proxy beans — you get the actual resolved object

**Q: When would you choose FastAPI over Django REST Framework?**


| Criterion         | FastAPI                          | DRF                      |
| ----------------- | -------------------------------- | ------------------------ |
| Async I/O         | Native                           | Bolted on (ASGI mode)    |
| Schema generation | Automatic (OpenAPI 3.1)          | Manual / drf-spectacular |
| Performance       | Higher (uvloop, no ORM overhead) | Lower                    |
| Admin interface   | No                               | Yes                      |
| Auth batteries    | Minimal                          | Rich (session, token)    |
| Learning curve    | Lower                            | Higher                   |


### Performance questions

**Q: Your async endpoint is slow. How do you debug it?**

1. Check if you're blocking the event loop with sync code inside `async def`
2. Profile with `py-spy` (`py-spy top --pid <pid>`) or `cProfile` middleware
3. Check DB query count with `SQLAlchemy echo=True` — N+1 problem?
4. Check if connection pool is exhausted (`pool_size` too low)
5. Use OpenTelemetry traces to find the slow span

**Q: What is the N+1 problem and how do you fix it in SQLAlchemy async?**

```python
# N+1: fetching orders, then 1 query per order for items
orders = await db.scalars(select(Order))   # query #1 — fetch, say, 50 orders
for o in orders:
    items = await db.scalars(select(Item).where(Item.order_id == o.id))  # N queries!
    # this line runs INSIDE the loop — once per order. For 50 orders, that's 50 MORE
    # separate round-trips to the database (queries #2 through #51), just to fetch each
    # order's items one at a time. Hence "N+1": 1 initial query + N follow-up queries.

# Fix: eager load with selectin or joined load
stmt = select(Order).options(selectinload(Order.items))   # 2 queries total
# selectinload tells SQLAlchemy: "when you fetch these orders, ALSO fetch all their items,
# but do it as ONE extra bulk query (SELECT * FROM items WHERE order_id IN (1,2,3,...50))
# instead of 50 separate ones." Total queries: 1 for orders + 1 for all items = 2, regardless
# of how many orders there are.
orders = await db.scalars(stmt)
```

### Security questions

**Q: How do you prevent JWT token theft?**

- Keep access token short-lived (15 min)
- Store refresh token in httpOnly, Secure, SameSite=Lax cookie (XSS-proof)
- Implement token rotation — issue new refresh token on every refresh
- Maintain a server-side refresh token allowlist in Redis
- Bind access token to a client fingerprint (IP + UA hash for sensitive ops)

**Q: How do you handle secrets in production?**

- Never commit secrets to git
- Use `SecretStr` (Pydantic) so they don't appear in logs
- Inject via environment variables from Vault / AWS Secrets Manager / K8s Secrets
- Rotate secrets without downtime via dual-valid-key period

### Reliability questions

**Q: How do you ensure exactly-once processing for critical operations?**

- Idempotency keys: client sends `X-Idempotency-Key`, server stores result in Redis for 24h
- Outbox pattern: write event atomically with business data, poll and publish separately
- For payments: delegate to payment provider's idempotency (Stripe idempotency_key)

**Q: How do you do zero-downtime DB schema migrations?**

1. **Expand**: Add new nullable column (no lock on Postgres with `ADD COLUMN ... DEFAULT NULL`)
2. **Migrate**: Backfill data in batches (never `UPDATE` all rows at once)
3. **Switch**: Deploy new code reading from new column
4. **Contract**: Drop old column once all traffic uses new column

---

## Quick Reference Cheatsheet

```
startup/shutdown   → lifespan context manager
config             → pydantic-settings + SecretStr
routing            → APIRouter + include_router
validation         → Pydantic v2 BaseModel + field_validator + model_validator
DI scoping         → lru_cache (singleton), Depends(yield) (request), use_cache=False (fresh)
auth               → OAuth2PasswordBearer + JWT + httpOnly refresh cookie
middleware         → BaseHTTPMiddleware (simple) | pure ASGI (no overhead)
DB                 → asyncpg + SQLAlchemy 2.x async + Repository pattern
migrations         → Alembic async env.py
cache              → Redis + sha256 key + tag-based invalidation
bg tasks           → FastAPI BackgroundTasks (fire-forget) | Celery (reliable)
websockets         → manager per room, auth via query param
errors             → domain exception hierarchy + global exception_handler
testing            → httpx.AsyncClient + ASGITransport + dependency_overrides
logging            → structlog JSON + contextvars for request_id
tracing            → OpenTelemetry + OTLP exporter
metrics            → prometheus-fastapi-instrumentator
deploy             → Gunicorn + UvicornWorker, multi-stage Dockerfile, K8s probes
security headers   → BaseHTTPMiddleware (HSTS, CSP, X-Frame-Options, nosniff)
secrets            → pydantic SecretStr + Vault / AWS Secrets Manager
```

---

*Study path: Core → DI → Auth → DB → Testing → Performance → Observability → Advanced patterns*