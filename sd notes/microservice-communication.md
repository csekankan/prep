# Microservices Communication in Kubernetes

> How do a frontend, two backends, and a database actually talk to each other?
> Every pattern explained, every packet traced, every pitfall covered.

---

## Table of Contents

1. [The Big Picture](#1-the-big-picture)
2. [Service Discovery — How Services Find Each Other](#2-service-discovery)
3. [Synchronous Communication — REST & gRPC](#3-sync-communication)
4. [Asynchronous Communication — Events & Queues](#4-async-communication)
5. [Frontend → Backend — Ingress Routing](#5-frontend-to-backend)
6. [Backend → Backend — Internal Calls](#6-backend-to-backend)
7. [DNS Deep Dive — What Happens When You Call Another Service](#7-dns-deep-dive)
8. [Circuit Breaking & Retries](#8-circuit-breaking)
9. [Service Mesh — When You Need More Control](#9-service-mesh)
10. [Authentication Between Services](#10-auth)
11. [Tracing a Request Across Services](#11-tracing)
12. [Common Patterns](#12-patterns)
13. [Common Mistakes](#13-mistakes)
14. [Full Architecture Reference](#14-architecture)

---

## 1. The Big Picture

### Our Example System

```
                    ┌──────────────────────────────┐
                    │         INTERNET              │
                    └──────────────┬───────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Ingress Controller        │
                    │   (NGINX / ALB)             │
                    └──┬────────────────────┬────┘
                       │                    │
            ┌──────────▼───────┐  ┌────────▼────────┐
            │   Frontend       │  │  API Gateway     │
            │   (React SPA)    │  │  /api/*          │
            │   static files   │  │  routes to       │
            │   served by NGINX│  │  backends        │
            └──────────────────┘  └──┬──────────┬───┘
                                     │          │
                          ┌──────────▼──┐ ┌─────▼──────────┐
                          │ Order       │ │ Product        │
                          │ Service     │ │ Service        │
                          │ (FastAPI)   │ │ (FastAPI)      │
                          └──┬──────┬──┘ └────────┬───────┘
                             │      │             │
                    ┌────────▼┐  ┌──▼──────┐  ┌──▼──────┐
                    │ Redis   │  │ Postgres│  │ Postgres│
                    │ (events)│  │ (orders)│  │(products│
                    └─────────┘  └─────────┘  └─────────┘

How they communicate:
  Browser     → Ingress    : HTTPS (external)
  Ingress     → Frontend   : HTTP (ClusterIP Service)
  Ingress     → Order Svc  : HTTP (ClusterIP Service, path /api/orders)
  Ingress     → Product Svc: HTTP (ClusterIP Service, path /api/products)
  Order Svc   → Product Svc: HTTP (ClusterIP DNS: product-service.production.svc.cluster.local)
  Order Svc   → Redis      : TCP  (ClusterIP DNS: redis.production.svc.cluster.local)
  Product Svc ← Redis      : TCP  (subscribes to events)
```

### Why This Matters

```
In a monolith:     function call → instant, same process
In microservices:  network call → latency, failure, serialization

You MUST handle:
  1. How do services find each other?        → Service Discovery
  2. What if the other service is down?       → Circuit Breaking
  3. How do I avoid tight coupling?           → Async Events
  4. How does the frontend reach backends?    → Ingress
  5. How do I trace a request across all?     → Distributed Tracing
  6. How do I secure internal traffic?        → mTLS / Auth
```

---

## 2. Service Discovery

### Kubernetes Does It For You

```
When you create a Kubernetes Service, you get:
  1. A stable DNS name
  2. A stable ClusterIP (virtual IP)
  3. Automatic load balancing across Pods

This IS your service discovery. No Consul, no Eureka, no custom registry.
```

### How DNS Names Work

```
Full DNS format:
  <service-name>.<namespace>.svc.cluster.local

Examples:
  order-service.production.svc.cluster.local
  product-service.production.svc.cluster.local
  redis.production.svc.cluster.local
  postgres.databases.svc.cluster.local

Shortcuts (within the SAME namespace):
  order-service              → works if caller is also in "production"
  order-service.production   → works from any namespace
```

### Creating a Service

```yaml
# This creates DNS entry: product-service.production.svc.cluster.local
apiVersion: v1
kind: Service
metadata:
  name: product-service
  namespace: production
spec:
  selector:
    app: product-service      # routes to Pods with this label
  ports:
  - port: 80                  # the port other services use
    targetPort: 8000          # the port your container listens on
```

### Calling Another Service (From Code)

```python
# In order-service, calling product-service:
import httpx

# Same namespace — just use the service name
response = httpx.get("http://product-service/api/products/123")

# Different namespace — include it
response = httpx.get("http://product-service.production/api/products/123")

# Full DNS (most explicit, always works)
response = httpx.get("http://product-service.production.svc.cluster.local/api/products/123")
```

```
Which form should you use?
  "product-service"                                → simple, only within same namespace
  "product-service.production"                     → safe, works cross-namespace
  "product-service.production.svc.cluster.local"   → full form, for configs/env vars
  
Recommendation: use "product-service.production" — explicit but concise.
```

---

## 3. Synchronous Communication

### REST (HTTP/JSON) — Most Common

```
Service A sends HTTP request → waits → gets HTTP response

Pros:
  ✓ Simple, everyone knows it
  ✓ Easy to debug (curl, Postman)
  ✓ Human-readable (JSON)
  ✓ Works with any language

Cons:
  ✗ Blocking (caller waits for response)
  ✗ Tight coupling (caller must know the API)
  ✗ Cascade failures (A calls B calls C — if C is slow, all slow)
  ✗ JSON serialization overhead
```

```python
# order-service calling product-service via REST

async def create_order(order: OrderRequest):
    # Validate product exists by calling product-service
    async with httpx.AsyncClient(
        base_url="http://product-service.production",
        timeout=httpx.Timeout(5.0, connect=2.0),
    ) as client:
        response = await client.get(f"/api/products/{order.product_id}")
        
        if response.status_code == 404:
            raise HTTPException(404, "Product not found")
        if response.status_code != 200:
            raise HTTPException(502, "Product service unavailable")
            
        product = response.json()
    
    # Create the order with product info
    new_order = Order(
        product_id=product["id"],
        product_name=product["name"],
        price=product["price"],
        quantity=order.quantity,
    )
    db.add(new_order)
    return new_order
```

### gRPC — High Performance

```
Service A sends protobuf message → waits → gets protobuf response

Pros:
  ✓ 2-10x faster than REST (binary, HTTP/2)
  ✓ Strongly typed (protobuf schema)
  ✓ Streaming (server-stream, client-stream, bidirectional)
  ✓ Auto-generated clients in any language

Cons:
  ✗ Harder to debug (not human-readable)
  ✗ Requires protobuf toolchain
  ✗ Browser can't call gRPC directly (needs grpc-web)

When to use:
  Internal service-to-service: gRPC
  External API (browser/mobile): REST
```

```protobuf
// product.proto
syntax = "proto3";
package product;

service ProductService {
  rpc GetProduct(GetProductRequest) returns (Product);
  rpc ListProducts(ListProductsRequest) returns (stream Product);
}

message GetProductRequest {
  string id = 1;
}

message Product {
  string id = 1;
  string name = 2;
  double price = 3;
  int32 stock = 4;
}
```

---

## 4. Asynchronous Communication

### Why Async?

```
Problem with sync:
  Order Service → Product Service → Inventory Service → Payment Service
  If Payment is slow (2s), the ENTIRE chain is slow (2s+)
  If Payment is DOWN, the ENTIRE chain FAILS

Solution: async events
  Order Service publishes "OrderCreated" event
  Payment Service subscribes and processes independently
  Inventory Service subscribes and processes independently
  
  If Payment is slow? Order Service doesn't care — it already returned 201.
  If Payment is down? Event waits in queue, processed when it recovers.
```

### Pattern: Event-Driven with Redis Pub/Sub

```
Simple, built into Redis, good for:
  - Notifications
  - Cache invalidation
  - Non-critical events

Limitation: messages are LOST if no subscriber is listening (fire-and-forget)
```

```python
# order-service: PUBLISH event after creating order
import redis.asyncio as redis

redis_client = redis.from_url("redis://redis.production:6379")

async def create_order(order: OrderRequest):
    new_order = await save_order(order)
    
    # Publish event (non-blocking, don't wait for consumers)
    await redis_client.publish("orders", json.dumps({
        "event": "order.created",
        "order_id": str(new_order.id),
        "product_id": order.product_id,
        "quantity": order.quantity,
        "timestamp": datetime.utcnow().isoformat(),
    }))
    
    return new_order
```

```python
# notification-service: SUBSCRIBE and react to events
import redis.asyncio as redis

async def listen_for_orders():
    r = redis.from_url("redis://redis.production:6379")
    pubsub = r.pubsub()
    await pubsub.subscribe("orders")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            event = json.loads(message["data"])
            if event["event"] == "order.created":
                await send_confirmation_email(event["order_id"])
```

### Pattern: Message Queue with Redis Streams (Durable)

```
Unlike Pub/Sub, Redis Streams are DURABLE:
  - Messages persist even if no consumer is listening
  - Consumer groups track what each consumer has processed
  - Failed messages can be retried
  
Use for: anything that MUST NOT be lost (payments, inventory updates)
```

```python
# order-service: ADD to stream
await redis_client.xadd("order-events", {
    "event": "order.created",
    "order_id": str(new_order.id),
    "product_id": order.product_id,
    "quantity": str(order.quantity),
})

# product-service: READ from stream (consumer group)
# Create consumer group (once)
try:
    await redis_client.xgroup_create("order-events", "product-service", id="0")
except redis.ResponseError:
    pass  # group already exists

# Read and process
while True:
    messages = await redis_client.xreadgroup(
        groupname="product-service",
        consumername="instance-1",
        streams={"order-events": ">"},
        count=10,
        block=5000,
    )
    for stream, entries in messages:
        for msg_id, data in entries:
            await update_stock(data["product_id"], -int(data["quantity"]))
            await redis_client.xack("order-events", "product-service", msg_id)
```

### When to Use What

```
                    REST        gRPC        Pub/Sub     Message Queue
                    ────        ────        ───────     ─────────────
Speed               Slow        Fast        Fastest     Fast
Coupling            Tight       Tight       Loose       Loose
Reliability         Sync        Sync        Fire&Forget Guaranteed
Debugging           Easy        Medium      Medium      Medium
Browser support     Yes         No          No          No

Use REST when:      external APIs, simple CRUD, browser-facing
Use gRPC when:      internal high-throughput, streaming, strong types
Use Pub/Sub when:   notifications, cache invalidation, non-critical
Use Queue when:     payments, inventory, anything that must not be lost
```

---

## 5. Frontend → Backend

### How the Browser Reaches Your Services

```
Browser: https://myapp.com
  │
  ▼
Ingress Controller (NGINX / ALB / Traefik)
  │
  ├── /              → frontend (serves React build)
  ├── /api/orders/*  → order-service
  └── /api/products/*→ product-service

This is called "path-based routing" — one domain, multiple backends.
The frontend and backends share the SAME domain → no CORS issues.
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.com
    http:
      paths:
      # API routes go to backend services
      - path: /api/orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /api/products
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 80
      # Everything else goes to frontend
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Frontend Calling Backend (Same Origin)

```javascript
// In React — since frontend and APIs share the same domain,
// no CORS configuration needed

// Fetch products
const products = await fetch('/api/products').then(r => r.json());

// Create order
const order = await fetch('/api/orders', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ product_id: '123', quantity: 2 }),
}).then(r => r.json());
```

### Why Same-Origin Matters

```
If frontend is at myapp.com and API is at api.myapp.com:
  → Different origins → browser blocks requests (CORS)
  → You need CORS headers on every backend
  → More complexity, more bugs

If both are at myapp.com (frontend at /, API at /api):
  → Same origin → browser allows all requests
  → No CORS needed
  → Simpler, more secure

Ingress path-based routing gives you this for free.
```

---

## 6. Backend → Backend

### The Call Flow

```
User clicks "Buy":
  
  Browser
    │
    │  POST /api/orders { product_id: "abc", quantity: 2 }
    ▼
  Ingress
    │
    ▼
  Order Service
    │
    │  1. GET http://product-service/api/products/abc  ← sync REST call
    │     "Does this product exist? Is it in stock?"
    │     Response: { id: "abc", name: "Widget", price: 29.99, stock: 50 }
    │
    │  2. Save order to database
    │
    │  3. PUBLISH to Redis: { event: "order.created", ... }  ← async event
    │     (Don't wait for consumers)
    │
    │  4. Return 201 Created to browser
    ▼
  Product Service (async, later):
    │
    │  Receives "order.created" event from Redis
    │  Decrements stock: stock = 50 - 2 = 48
    │
    ▼
  (done independently, user already has their 201 response)
```

### Handling Failures Between Services

```python
# order-service: calling product-service with retry + fallback

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=5),
)
async def get_product(product_id: str) -> dict:
    async with httpx.AsyncClient(
        base_url="http://product-service.production",
        timeout=3.0,
    ) as client:
        response = await client.get(f"/api/products/{product_id}")
        response.raise_for_status()
        return response.json()

async def create_order(order: OrderRequest):
    try:
        product = await get_product(order.product_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(404, "Product not found")
        raise HTTPException(502, "Product service error")
    except Exception:
        raise HTTPException(503, "Product service unavailable")
    
    # proceed with order...
```

---

## 7. DNS Deep Dive

### What Happens When Order Service Calls Product Service

```
Code: httpx.get("http://product-service/api/products/123")

Step 1: DNS Resolution
  order-service Pod → CoreDNS
  Query: "product-service" (short name)
  CoreDNS appends search domains from /etc/resolv.conf:
    - product-service.production.svc.cluster.local → FOUND!
    Returns: 10.100.45.67 (ClusterIP)

Step 2: iptables/IPVS
  Pod sends packet to 10.100.45.67:80
  kube-proxy rules on the node intercept:
    10.100.45.67 → DNAT to one of:
      10.244.1.5:8000 (Pod 1)
      10.244.2.8:8000 (Pod 2)
      10.244.3.3:8000 (Pod 3)
  Round-robin selection → picks 10.244.2.8

Step 3: Network
  Packet goes: order Pod → node → (CNI routing) → product Pod
  If same node: stays local
  If different node: VXLAN/Geneve tunnel or direct route

Step 4: Response
  product Pod processes request → sends HTTP 200 back
  iptables connection tracking → response goes to same order Pod
```

### /etc/resolv.conf Inside a Pod

```bash
kubectl exec -it order-service-pod -- cat /etc/resolv.conf

# nameserver 10.96.0.10           ← CoreDNS ClusterIP
# search production.svc.cluster.local svc.cluster.local cluster.local
# options ndots:5

# "ndots:5" means: if the name has fewer than 5 dots,
# try appending each search domain before querying as-is.

# "product-service" has 0 dots (< 5), so DNS tries:
#   product-service.production.svc.cluster.local  → found!
#   (stops here, doesn't try the others)
```

---

## 8. Circuit Breaking

### The Cascading Failure Problem

```
Without circuit breaking:
  
  Order Service → Product Service → Inventory Service
                                         │
                                         ▼ DOWN
  
  What happens:
  1. Inventory is down
  2. Product Service calls Inventory, waits 30s, timeout
  3. Product Service threads pile up (all waiting on Inventory)
  4. Product Service runs out of memory/threads → goes down
  5. Order Service calls Product, waits 30s, timeout
  6. Order Service goes down
  7. Everything is dead (cascade failure)
```

### Solution: Circuit Breaker Pattern

```
Circuit breaker has 3 states:

  CLOSED (normal):
    All requests pass through
    Track failure count
    If failures > threshold → switch to OPEN

  OPEN (blocking):
    All requests fail IMMEDIATELY (no waiting)
    After timeout period → switch to HALF-OPEN

  HALF-OPEN (testing):
    Allow ONE request through
    If it succeeds → switch to CLOSED
    If it fails → switch back to OPEN

  Result: fast failure, no cascade, auto-recovery
```

```python
# Simple circuit breaker implementation
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise ServiceUnavailable("Circuit open — failing fast")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
product_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def get_product(product_id: str):
    return await product_breaker.call(_fetch_product, product_id)
```

### Istio Circuit Breaking (Zero Code Changes)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: product-service
spec:
  host: product-service.production.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

---

## 9. Service Mesh

### When Do You Need One?

```
Without service mesh (fine for most teams):
  App code handles: retries, timeouts, circuit breaking, auth
  You implement: each in your app code

With service mesh (Istio/Linkerd):
  Sidecar proxy handles: retries, timeouts, circuit breaking, mTLS
  Your app just: makes HTTP calls and doesn't worry about resilience

Use a service mesh when:
  ✓ Many services (10+)
  ✓ Multiple languages (can't share retry libraries)
  ✓ Strict security requirements (mTLS everywhere)
  ✓ Need traffic shifting (canary, A/B testing)
  ✓ Need detailed traffic metrics without code changes

Don't use when:
  ✗ Fewer than 5 services
  ✗ Single language/framework (share libraries instead)
  ✗ Team is small (mesh is complex)
```

### How It Works

```
Without mesh:
  [Order Pod] ──HTTP──▶ [Product Pod]

With mesh (Istio):
  [Order Pod] → [Envoy Proxy] ──mTLS──▶ [Envoy Proxy] → [Product Pod]
                 sidecar                   sidecar

  The Envoy sidecars automatically:
  ✓ Encrypt traffic (mTLS)
  ✓ Retry failed requests
  ✓ Enforce timeouts
  ✓ Circuit break unhealthy backends
  ✓ Report metrics (latency, error rate)
  ✓ Distribute traces
  ✓ Enforce authorization policies

  Your app code: just calls http://product-service/ — unchanged.
```

---

## 10. Authentication Between Services

### Option A: Kubernetes Network Policies (L3/L4)

```yaml
# Only allow order-service to talk to product-service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: product-service-allow
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: product-service
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: order-service
    ports:
    - port: 8000
```

### Option B: Service-to-Service Tokens

```python
# Shared secret (simple, for small teams)
# Each service has an API key in a K8s Secret

INTERNAL_API_KEY = os.environ["INTERNAL_API_KEY"]

# Caller adds header
response = httpx.get(
    "http://product-service/api/products/123",
    headers={"X-Internal-Auth": INTERNAL_API_KEY},
)

# Receiver validates
@app.middleware("http")
async def validate_internal_auth(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        token = request.headers.get("X-Internal-Auth")
        if token != os.environ["INTERNAL_API_KEY"]:
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
    return await call_next(request)
```

### Option C: mTLS via Service Mesh (Best)

```
With Istio PeerAuthentication:
  Every service gets a TLS certificate automatically
  Every connection is encrypted and authenticated
  No code changes needed

  Order Service ─mTLS─▶ Product Service
  Both sides verified by certificate
  Istio handles certificate rotation automatically
```

---

## 11. Tracing a Request Across Services

### Why Distributed Tracing?

```
User reports: "order creation is slow"

Without tracing: which service is slow? No idea.

With tracing:
  Request ID: abc-123
  ├── [Ingress]         2ms
  ├── [Order Service]   
  │   ├── validate      1ms
  │   ├── GET product   150ms  ← slow!
  │   ├── save order    5ms
  │   └── publish event 1ms
  └── Total: 160ms

  Now you know: product-service is the bottleneck (150ms).
```

### Propagate Trace Context

```python
# The key: pass trace headers between services
# If using OpenTelemetry, the SDK does this automatically.
# If doing it manually:

TRACE_HEADERS = [
    "x-request-id",
    "x-b3-traceid",
    "x-b3-spanid",
    "x-b3-parentspanid",
    "x-b3-sampled",
    "traceparent",
    "tracestate",
]

async def call_product_service(product_id: str, request: Request):
    # Forward trace headers from incoming request to outgoing call
    headers = {
        h: request.headers[h]
        for h in TRACE_HEADERS
        if h in request.headers
    }
    
    async with httpx.AsyncClient() as client:
        return await client.get(
            f"http://product-service/api/products/{product_id}",
            headers=headers,
        )
```

---

## 12. Common Patterns

### API Gateway Pattern

```
Instead of Ingress routing directly to each service,
put a gateway in front:

  Browser → Ingress → API Gateway → order-service
                                   → product-service

Gateway handles:
  - Authentication (verify JWT once)
  - Rate limiting
  - Request aggregation (combine responses from multiple services)
  - API versioning

In K8s: Kong, Ambassador, or just a custom FastAPI gateway service
```

### BFF (Backend for Frontend) Pattern

```
Different clients need different data shapes:

  Mobile app:  needs minimal data (bandwidth matters)
  Web app:     needs full data
  Admin panel: needs everything + metadata

Solution: separate BFF for each:
  Browser → Ingress → web-bff     → order-service, product-service
  Mobile  → Ingress → mobile-bff  → order-service, product-service

Each BFF aggregates/transforms data for its client.
```

### Saga Pattern (Distributed Transactions)

```
Problem: Create an order that requires:
  1. Reserve inventory (product-service)
  2. Charge payment (payment-service)  
  3. Create order record (order-service)

If step 2 fails, you must UNDO step 1.

Saga: a sequence of local transactions with compensating actions.

  Step 1: Reserve inventory
    → Success → Step 2
    → Fail → DONE (nothing to undo)

  Step 2: Charge payment
    → Success → Step 3
    → Fail → Compensate: Release inventory

  Step 3: Create order
    → Success → DONE
    → Fail → Compensate: Refund payment → Release inventory

Implement via:
  Choreography: each service publishes events, others react
  Orchestration: a "saga coordinator" tells each service what to do
```

### CQRS (Command Query Responsibility Segregation)

```
Problem: order-service needs product data for display,
         but calling product-service on every read is slow.

Solution: each service keeps a LOCAL READ COPY of data it needs.

  product-service: publishes "product.updated" events
  order-service:   subscribes, keeps local product cache
  
  Reads:   from local cache (fast, no network call)
  Writes:  go to the owning service (product-service)

Trade-off: eventual consistency (data might be stale by seconds)
```

---

## 13. Common Mistakes

```
1. SYNCHRONOUS EVERYTHING
   Bad:  Order → Product → Inventory → Payment (all sync REST)
   Good: Order → Product (sync, need response) → publish event (async)
   Rule: sync for queries, async for commands that don't need immediate response

2. NO TIMEOUTS
   Bad:  httpx.get("http://product-service/api/products/123")
   Good: httpx.get(..., timeout=3.0)
   Without timeout: one slow service blocks your entire thread pool

3. NO RETRIES (OR TOO MANY)
   Bad:  retry 10 times, no backoff → hammers the failing service
   Good: retry 3 times, exponential backoff (0.5s, 1s, 2s)

4. CHATTY SERVICES
   Bad:  for each order item → call product-service separately (N+1 calls)
   Good: batch call → GET /api/products?ids=abc,def,ghi (1 call)

5. SHARED DATABASE
   Bad:  order-service and product-service both write to the same DB
   Good: each service owns its database, communicates via API/events
   Shared DB = tight coupling, schema changes break everything

6. HARDCODED URLS
   Bad:  PRODUCT_URL = "http://10.244.1.5:8000"  ← IP changes on restart
   Good: PRODUCT_URL = "http://product-service"   ← DNS, always resolves

7. NO HEALTH CHECKS ON DEPENDENCIES
   Bad:  readiness probe only checks own server
   Good: readiness probe checks DB connection + critical dependencies

8. NOT PROPAGATING TRACE CONTEXT
   Bad:  each service starts a new trace → can't correlate requests
   Good: pass traceparent/x-request-id headers between services

9. USING LATEST TAG
   Bad:  image: myapp:latest → which version is running? no idea
   Good: image: myapp:v1.2.3-abc1234 → exact commit, easy rollback

10. NOT HANDLING PARTIAL FAILURES
    Bad:  if product-service is slow → order-service OOMs
    Good: circuit breaker + timeout + graceful degradation
```

---

## 14. Full Architecture Reference

### Production Microservices on Kubernetes

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Ingress Controller (NGINX / ALB)                                  │
│ TLS termination, rate limiting, path routing                      │
└────┬───────────────────────┬──────────────────────┬─────────────┘
     │                       │                      │
     │ /                     │ /api/orders/*         │ /api/products/*
     ▼                       ▼                      ▼
┌─────────┐          ┌──────────────┐       ┌──────────────┐
│Frontend │          │ Order Svc    │       │ Product Svc  │
│ NGINX   │          │ (FastAPI)    │       │ (FastAPI)    │
│ serves  │          │              │       │              │
│ React   │          │ Calls ──────────────▶│              │
│ build   │          │ product-svc  │ sync  │              │
│         │          │              │       │              │
│         │          │ Publishes ──▶│ Redis │◀── Subscribes│
│         │          │ events       │       │   to events  │
└─────────┘          └──────┬───────┘       └──────┬───────┘
                            │                      │
                     ┌──────▼───────┐       ┌──────▼───────┐
                     │ PostgreSQL   │       │ PostgreSQL   │
                     │ (orders DB)  │       │ (products DB)│
                     │ own database │       │ own database │
                     └──────────────┘       └──────────────┘

Key Rules:
  1. Each service owns its database (never shared)
  2. Services communicate via HTTP (sync) or events (async)
  3. Frontend only talks to backends through Ingress (same origin)
  4. Internal services use ClusterIP (not exposed to internet)
  5. Trace context propagated on every inter-service call
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│                    COMMUNICATION CHEAT SHEET                   │
├───────────────────┬──────────────────────────────────────────┤
│ Browser → Backend │ Ingress (path-based routing)             │
│ Svc → Svc (sync) │ HTTP via ClusterIP DNS                   │
│ Svc → Svc (async)│ Redis Streams / SQS / Kafka              │
│ Find a service    │ <name>.<namespace>.svc.cluster.local     │
│ Same namespace    │ just use the service name                │
│ Cross namespace   │ <name>.<other-namespace>                 │
│ Timeout           │ ALWAYS set (2-5s for internal calls)     │
│ Retries           │ 3 attempts, exponential backoff          │
│ Circuit breaker   │ Open after 5 failures, reset after 30s   │
│ Auth (simple)     │ shared API key in K8s Secret             │
│ Auth (production) │ mTLS via Istio / Linkerd                 │
│ Tracing           │ propagate traceparent header             │
│ DB per service    │ ALWAYS (never share databases)           │
└───────────────────┴──────────────────────────────────────────┘
```

---

*This is the companion guide to project `04-microservices-fullstack/`.*
*Build the project to see all these patterns in action.*
