# FastAPI — Staff Engineer Interview Cheat Sheet

> Covers architecture, internals, patterns, security, performance, testing, and production at depth.
> Every section includes code that compiles and runs.

---

## Table of Contents

1. [Core Architecture & Internals](#1-core-architecture--internals)
2. [Routing & Path Operations](#2-routing--path-operations)
3. [Request & Response Models (Pydantic v2)](#3-request--response-models-pydantic-v2)
4. [Dependency Injection System](#4-dependency-injection-system)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Middleware & Lifecycle](#6-middleware--lifecycle)
7. [Database Integration (Async SQLAlchemy)](#7-database-integration-async-sqlalchemy)
8. [Background Tasks & Celery](#8-background-tasks--celery)
9. [WebSockets & Server-Sent Events](#9-websockets--server-sent-events)
10. [Error Handling & Custom Exceptions](#10-error-handling--custom-exceptions)
11. [Testing Strategy](#11-testing-strategy)
12. [Performance & Scalability](#12-performance--scalability)
13. [Security Best Practices](#13-security-best-practices)
14. [Caching Patterns](#14-caching-patterns)
15. [Observability: Logging, Tracing, Metrics](#15-observability-logging-tracing-metrics)
16. [Production Deployment](#16-production-deployment)
17. [Advanced Patterns (CQRS, Event-Driven, DDD)](#17-advanced-patterns-cqrs-event-driven-ddd)
18. [Staff Engineer Interview: Critical Questions](#18-staff-engineer-interview-critical-questions)

---

## 1. Core Architecture & Internals

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
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import api_v1_router
from app.core.config import Settings
from app.db.session import engine
from app.db.base import Base

def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        # shutdown
        await engine.dispose()

    app = FastAPI(
        title=cfg.project_name,
        version=cfg.version,
        docs_url="/docs" if cfg.debug else None,  # disable in prod
        redoc_url=None,
        lifespan=lifespan,
    )
    app.include_router(api_v1_router, prefix="/api/v1")
    return app

app = create_app()
```

---

## 2. Routing & Path Operations

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

### Model configuration (v2 syntax)

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic import EmailStr, AnyHttpUrl
from typing import Annotated
from decimal import Decimal
import re

PositiveAmount = Annotated[Decimal, Field(gt=0, decimal_places=2)]

class OrderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,   # accept both alias and field name
        json_schema_extra={"example": {"amount": "19.99", "currency": "USD"}},
    )

    amount: PositiveAmount
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    callback_url: AnyHttpUrl | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def validate_callback_for_large_orders(self) -> "OrderCreate":
        if self.amount > 10000 and self.callback_url is None:
            raise ValueError("callback_url required for orders > 10000")
        return self
```

### Generic pagination response

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Sequence

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: Sequence[T], total: int, page: int, size: int) -> "Page[T]":
        return cls(items=items, total=total, page=page, size=size, pages=-(-total // size))

# Usage
@router.get("/", response_model=Page[UserOut])
async def list_users(page: int = 1, size: int = Query(20, le=100)):
    users, total = await svc.paginate(page=page, size=size)
    return Page.create(users, total, page, size)
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
@lru_cache                   # called once per process
def get_settings() -> Settings:
    return Settings()

# --- Request-scoped (default) ---
async def get_db(settings: Settings = Depends(get_settings)):
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# --- Reusable class-based dependency ---
class Pagination:
    def __init__(self, page: int = 1, size: int = Query(20, le=100)):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size

@router.get("/")
async def list_items(
    p: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
):
    ...
```

### Dependency for permission checking

```python
from fastapi import Security
from fastapi.security import SecurityScopes

def require_scope(*scopes: str):
    """Factory that returns a dependency enforcing OAuth2 scopes."""
    async def _check(
        token_data: TokenData = Security(get_current_user, scopes=list(scopes)),
    ) -> TokenData:
        return token_data
    return _check

# Usage on route
@router.delete("/{id}", dependencies=[Depends(require_scope("admin:write"))])
async def delete_user(id: UUID): ...
```

### use_cache=False — when to disable caching

```python
# Two different DB sessions needed in one handler — disable caching
@router.post("/transfer")
async def transfer(
    src_db: AsyncSession = Depends(get_db),
    dst_db: AsyncSession = Depends(get_db, use_cache=False),  # fresh session
):
    ...
```

---

## 5. Authentication & Authorization

### JWT with refresh tokens (production pattern)

```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "change-me-use-vault"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE  = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(subject: str, expires: timedelta, token_type: str = "access") -> str:
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Wrong token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

```python
# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@router.post("/token")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: AuthService = Depends(get_auth_service),
    response: Response = None,
):
    user = await svc.authenticate(form.username, form.password)
    access  = create_token(str(user.id), ACCESS_TOKEN_EXPIRE)
    refresh = create_token(str(user.id), REFRESH_TOKEN_EXPIRE, "refresh")

    # Refresh token in httpOnly cookie — not in body
    response.set_cookie(
        key="refresh_token", value=refresh,
        httponly=True, secure=True, samesite="lax",
        max_age=int(REFRESH_TOKEN_EXPIRE.total_seconds()),
    )
    return {"access_token": access, "token_type": "bearer"}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user = await db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "Inactive user")
    return user
```

### Role-based access control (RBAC)

```python
from enum import StrEnum

class Role(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN  = "admin"

ROLE_HIERARCHY = {Role.VIEWER: 0, Role.EDITOR: 1, Role.ADMIN: 2}

def require_role(minimum: Role):
    async def _check(current: User = Depends(get_current_user)) -> User:
        if ROLE_HIERARCHY[current.role] < ROLE_HIERARCHY[minimum]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current
    return _check

@router.delete("/{id}", dependencies=[Depends(require_role(Role.ADMIN))])
async def delete_item(id: UUID): ...
```

### API key authentication

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_client(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> ApiClient:
    if not api_key:
        raise HTTPException(401, "API key required")
    client = await db.scalar(select(ApiClient).where(ApiClient.hashed_key == hash_key(api_key)))
    if not client or not client.is_active:
        raise HTTPException(403, "Invalid API key")
    return client
```

---

## 6. Middleware & Lifecycle

### Custom middleware (Starlette BaseHTTPMiddleware)

```python
import time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.perf_counter()

        response = await call_next(request)

        elapsed = (time.perf_counter() - request.state.start_time) * 1000
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed:.2f}ms"
        return response

app.add_middleware(RequestContextMiddleware)
```

### CORS (critical for production)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,    # never ["*"] in prod with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    expose_headers=["X-Request-Id", "X-Response-Time"],
    max_age=600,
)
```

### GZip & Trusted Host

```python
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.internal"])
```

### Rate limiting (slowapi)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/")
@limiter.limit("10/minute")    # per-route override
async def sensitive_endpoint(request: Request): ...
```

### Lifespan events (preferred over @app.on_event)

```python
from contextlib import asynccontextmanager
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    app.state.redis = await aioredis.from_url(settings.redis_url)
    yield
    # --- shutdown ---
    await app.state.http_client.aclose()
    await app.state.redis.aclose()

app = FastAPI(lifespan=lifespan)
```

---

## 7. Database Integration (Async SQLAlchemy)

### Session factory

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    settings.database_url,          # postgresql+asyncpg://...
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,             # detect stale connections
    pool_recycle=3600,
    echo=settings.db_echo,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,         # keep objects usable after commit
    class_=AsyncSession,
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
    pass

class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

class UUIDMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
```

### Repository pattern

```python
# app/repositories/user_repo.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from uuid import UUID

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.db.scalar(stmt)

    async def paginate(self, page: int, size: int) -> tuple[list[User], int]:
        offset = (page - 1) * size
        stmt = select(User).offset(offset).limit(size)
        count_stmt = select(func.count()).select_from(User)
        users  = list((await self.db.scalars(stmt)).all())
        total  = await self.db.scalar(count_stmt)
        return users, total or 0

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()   # get the DB-generated id before commit
        return user

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
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

### FastAPI BackgroundTasks (lightweight, in-process)

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str):
    # runs after the response is sent — still in same process/loop
    await email_client.send(to=email, subject="Welcome!", body=f"Hi {name}")

@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    bg: BackgroundTasks,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.create(body)
    bg.add_task(send_welcome_email, user.email, user.name)
    return user
```

**Limitations**: dies with the process, no retry, no queue visibility. Use Celery for anything critical.

### Celery with Redis (production pattern)

```python
# app/worker/celery_app.py
from celery import Celery

celery = Celery(
    "app",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,              # ack only after success — at-least-once
    worker_prefetch_multiplier=1,     # fair dispatch
    task_routes={"app.worker.tasks.send_email": {"queue": "email"}},
)

# app/worker/tasks.py
from app.worker.celery_app import celery

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to: str, subject: str, body: str):
    try:
        email_client.send_sync(to, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)

# Dispatching from FastAPI
@router.post("/notify")
async def notify(body: NotifyRequest):
    send_email_task.apply_async(
        args=[body.email, body.subject, body.message],
        countdown=0,
    )
    return {"status": "queued"}
```

---

## 9. WebSockets & Server-Sent Events

### WebSocket connection manager

```python
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import json

class ConnectionManager:
    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self._rooms[room].add(ws)

    def disconnect(self, ws: WebSocket, room: str):
        self._rooms[room].discard(ws)

    async def broadcast(self, room: str, message: dict):
        dead = set()
        for ws in self._rooms[room]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._rooms[room] -= dead

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    ws: WebSocket,
    room_id: str,
    token: str = Query(...),          # auth via query param for WS
):
    user = await authenticate_ws_token(token)
    await manager.connect(ws, room_id)
    try:
        while True:
            data = await ws.receive_json()
            await manager.broadcast(room_id, {"user": str(user.id), **data})
    except WebSocketDisconnect:
        manager.disconnect(ws, room_id)
```

### Server-Sent Events (SSE)

```python
from starlette.responses import StreamingResponse
import asyncio

async def event_generator(topic: str):
    while True:
        event = await pubsub.get(topic)          # wait for next event
        yield f"data: {event.json()}\n\n"
        if event.type == "done":
            break

@router.get("/stream/{topic}")
async def stream(topic: str, current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        event_generator(topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )
```

---

## 10. Error Handling & Custom Exceptions

### Domain exception hierarchy

```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
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

### Global exception handlers

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

def install_exception_handlers(app: FastAPI) -> None:

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

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "detail": exc.errors(),
                "body": exc.body,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content={"error": "InternalServerError"})
```

---

## 11. Testing Strategy

### Test setup with pytest + httpx

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import create_app
from app.db.base import Base
from app.api.deps import get_db

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DB_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()

@pytest_asyncio.fixture
async def db(engine):
    async with engine.begin() as conn:
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.rollback()       # isolate each test

@pytest_asyncio.fixture
async def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
```

### Unit testing services (mock repositories)

```python
# tests/unit/test_user_service.py
from unittest.mock import AsyncMock
import pytest
from app.services.user_service import UserService
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_create_user_sends_email():
    repo    = AsyncMock()
    emailer = AsyncMock()
    svc     = UserService(repo=repo, emailer=emailer)

    repo.get_by_email.return_value = None       # no existing user
    repo.create.return_value = FakeUser(id=uuid4(), email="a@b.com")

    await svc.create(UserCreate(email="a@b.com", password="secret"))

    repo.create.assert_called_once()
    emailer.send_welcome.assert_called_once_with("a@b.com")
```

### Integration tests

```python
# tests/integration/test_users_api.py
import pytest

@pytest.mark.asyncio
async def test_create_and_get_user(client, auth_headers):
    payload = {"email": "new@example.com", "password": "S3cur3!"}
    r = await client.post("/api/v1/users/", json=payload, headers=auth_headers)
    assert r.status_code == 201
    uid = r.json()["id"]

    r2 = await client.get(f"/api/v1/users/{uid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["email"] == payload["email"]
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

### Connection pool tuning

```python
engine = create_async_engine(
    url,
    pool_size=20,          # persistent connections
    max_overflow=40,       # burst capacity (total max = pool_size + max_overflow)
    pool_timeout=30,       # wait for connection before error
    pool_recycle=1800,     # recycle connections older than 30 min
    pool_pre_ping=True,    # send SELECT 1 before checkout — detect stale
)
```

### Streaming large responses

```python
from fastapi.responses import StreamingResponse
import csv, io

async def stream_csv(query_result):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "email", "created_at"])
    yield buffer.getvalue()
    buffer.seek(0); buffer.truncate()

    async for row in query_result:
        writer.writerow([row.id, row.email, row.created_at])
        yield buffer.getvalue()
        buffer.seek(0); buffer.truncate()

@router.get("/export/users.csv")
async def export_users(db: AsyncSession = Depends(get_db)):
    result = await db.stream(select(User))
    return StreamingResponse(
        stream_csv(result),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
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

### Security headers middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=()",
        })
        return response
```

### Input sanitization

```python
import bleach
from pydantic import field_validator

class CommentCreate(BaseModel):
    content: str = Field(max_length=2000)

    @field_validator("content")
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        allowed_tags = ["b", "i", "em", "strong", "a"]
        return bleach.clean(v, tags=allowed_tags, strip=True)
```

### SQL injection prevention

```python
# ALWAYS use parameterized queries — never f-string SQL
# GOOD — SQLAlchemy ORM / Core with bound parameters
stmt = select(User).where(User.email == email)           # safe

# GOOD — raw SQL with parameters
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email},
)

# BAD — never do this
result = await db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### Secrets management

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: SecretStr          # .get_secret_value() to use
    jwt_secret: SecretStr
    redis_url: str = "redis://localhost:6379"
    debug: bool = False

# SecretStr never appears in logs / repr — critical for security
```

---

## 14. Caching Patterns

### Redis cache decorator

```python
import json, hashlib
from functools import wraps
from typing import Callable, Any
import redis.asyncio as aioredis

def cache(ttl: int = 300, key_prefix: str = ""):
    """Decorator that caches the result of an async function in Redis."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            redis: aioredis.Redis = app.state.redis
            raw = f"{key_prefix}:{fn.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.sha256(raw.encode()).hexdigest()

            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)

            result = await fn(*args, **kwargs)
            await redis.setex(cache_key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

@cache(ttl=60, key_prefix="user")
async def get_user_profile(user_id: str) -> dict:
    return await db_fetch_profile(user_id)
```

### HTTP response caching

```python
from fastapi import Response

@router.get("/config")
async def get_public_config(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
    response.headers["ETag"] = compute_config_hash()
    return config_data
```

### Cache invalidation with tags

```python
async def invalidate_user_cache(user_id: str, redis: aioredis.Redis):
    """Scan and delete all cache keys for a user."""
    pattern = f"user:*:{user_id}*"
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break
```

---

## 15. Observability: Logging, Tracing, Metrics

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

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db), request: Request = None):
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"

    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
```

---

## 16. Production Deployment

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

### CQRS — Commands vs Queries

```python
# Commands mutate state, Queries read state — separate handlers

class CreateOrderCommand(BaseModel):
    user_id: UUID
    items: list[OrderItemCreate]

class OrderCommandHandler:
    def __init__(self, repo: OrderRepository, event_bus: EventBus):
        self.repo = repo
        self.event_bus = event_bus

    async def handle_create(self, cmd: CreateOrderCommand) -> UUID:
        order = Order.create(user_id=cmd.user_id, items=cmd.items)
        await self.repo.save(order)
        await self.event_bus.publish(OrderCreatedEvent(order_id=order.id))
        return order.id

class OrderQueryHandler:
    def __init__(self, read_db: AsyncSession):
        self.db = read_db

    async def get_order_summary(self, order_id: UUID) -> OrderSummaryDTO:
        # Can query a read replica / materialized view
        stmt = text("SELECT * FROM order_summaries WHERE id = :id")
        row = await self.db.execute(stmt, {"id": order_id})
        return OrderSummaryDTO.model_validate(row.mappings().one())
```

### Domain events + outbox pattern

```python
# Guarantees at-least-once event delivery without 2-phase commit
class OutboxEntry(Base):
    __tablename__ = "outbox"
    id: Mapped[UUID]
    event_type: Mapped[str]
    payload: Mapped[dict]   # JSON column
    published_at: Mapped[datetime | None]

# Within the same DB transaction as the business operation:
async def create_order_with_outbox(cmd, db: AsyncSession):
    order = Order(...)
    outbox = OutboxEntry(
        event_type="OrderCreated",
        payload={"order_id": str(order.id), "user_id": str(cmd.user_id)},
    )
    db.add(order)
    db.add(outbox)
    await db.commit()      # atomic: order + event saved or neither

# Separate poller publishes outbox entries to Kafka/RabbitMQ
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

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None: ...
    @abstractmethod
    async def create(self, user: User) -> User: ...

class SqlUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession): self.db = db
    async def get_by_id(self, id: UUID): return await self.db.get(User, id)
    async def create(self, user: User):
        self.db.add(user); await self.db.flush(); return user

class InMemoryUserRepository(IUserRepository):
    def __init__(self): self._store: dict[UUID, User] = {}
    async def get_by_id(self, id): return self._store.get(id)
    async def create(self, user): self._store[user.id] = user; return user

# Tests use InMemory; production uses Sql — zero DB overhead in unit tests
```

---

## 18. Staff Engineer Interview: Critical Questions

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

| Criterion | FastAPI | DRF |
|-----------|---------|-----|
| Async I/O | Native | Bolted on (ASGI mode) |
| Schema generation | Automatic (OpenAPI 3.1) | Manual / drf-spectacular |
| Performance | Higher (uvloop, no ORM overhead) | Lower |
| Admin interface | No | Yes |
| Auth batteries | Minimal | Rich (session, token) |
| Learning curve | Lower | Higher |

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
orders = await db.scalars(select(Order))
for o in orders:
    items = await db.scalars(select(Item).where(Item.order_id == o.id))  # N queries!

# Fix: eager load with selectin or joined load
stmt = select(Order).options(selectinload(Order.items))   # 2 queries total
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
