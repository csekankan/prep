# Intelligent Caching — Complete Reference

> Based on *Intelligent Caching* by Tom Barker (O'Reilly, 2017) — expanded with
> backend caching patterns, Redis strategies, and production practices.
> From 500M page views/month to your first cache header.

---

## Table of Contents

1. [Why Caching Matters](#1-why-caching-matters)
2. [The Caching Layers — Browser to Database](#2-caching-layers)
3. [Hot, Warm, and Cold Cache](#3-hot-warm-cold)
4. [Cache Freshness and TTL](#4-cache-freshness)
5. [HTTP Cache-Control — Every Directive Explained](#5-cache-control)
6. [Browser Caching](#6-browser-caching)
7. [CDN and Edge Caching](#7-cdn-edge)
8. [Reverse Proxy Caching (Nginx / Varnish)](#8-reverse-proxy)
9. [Application-Level Caching](#9-application-cache)
10. [Distributed Caching — Redis & Memcached](#10-distributed-cache)
11. [Caching Patterns — Cache-Aside, Write-Through, Write-Behind, Read-Through](#11-caching-patterns)
12. [Caching Personalized Content](#12-personalized)
13. [Cache Invalidation — The Hard Problem](#13-invalidation)
14. [Cache Stampede (Thundering Herd)](#14-stampede)
15. [Common Problems and Solutions](#15-common-problems)
16. [Cache Warming](#16-warming)
17. [Measuring Cache Effectiveness](#17-measuring)
18. [Getting Started — Evaluate and Implement](#18-getting-started)
19. [Production Recipes](#19-recipes)
20. [Caching in Microservices and Kubernetes](#20-microservices)

---

## 1. Why Caching Matters

### The Scale Problem

```
Without caching (every request hits the backend):

  User → Load Balancer → App Server → Database
  
  100M requests/day = 1,157 requests/second
  Each request: 50-200ms (DB query + processing)
  
  Result:
    - Need 50+ app servers
    - Database under crushing load
    - Latency: 200ms+ per request
    - Cost: $$$$

With intelligent caching:

  User → CDN (cache hit, 90%)     → done in 5ms
  User → CDN (miss) → App (hit)  → done in 20ms
  User → CDN (miss) → App (miss) → DB → 200ms (only 1-5% of traffic)
  
  Result:
    - Need 5-10 app servers (10x fewer)
    - Database load reduced by 95%
    - Average latency: 10ms
    - Cost: $
```

### The Numbers (From Barker's Experience at Comcast)

```
500 million page views per month
~16.7 million per day
~193 requests per second (sustained)
Peaks: 5-10x average → ~1,900 req/s

Without frontend caching: impossible to serve
With frontend caching: most requests never reach the backend

Rule of thumb:
  90% of requests should be served from cache
  9% from application-level cache
  1% actually hits the database
```

---

## 2. The Caching Layers

### Every Layer, From User to Database

```
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 1: BROWSER CACHE                                               │
│  Where: user's device                                                │
│  Latency: 0ms (instant, from disk/memory)                            │
│  What: static assets (JS, CSS, images, fonts)                       │
│  TTL: 1 hour – 1 year                                                │
│  Controlled by: Cache-Control headers from your server               │
│  Hit rate target: 85-95% for static assets                          │
└──────────────────────────────────────────────────────────────────────┘
         │ (cache miss)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 2: CDN / EDGE CACHE                                            │
│  Where: edge servers worldwide (CloudFront, Cloudflare, Fastly)      │
│  Latency: 1-20ms (nearby PoP)                                       │
│  What: HTML pages, API responses, static assets                      │
│  TTL: 5 minutes – 24 hours                                          │
│  Controlled by: Cache-Control s-maxage, CDN rules                    │
│  Hit rate target: 80-95%                                             │
└──────────────────────────────────────────────────────────────────────┘
         │ (cache miss)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 3: REVERSE PROXY CACHE                                         │
│  Where: your infrastructure (Nginx, Varnish, HAProxy)                │
│  Latency: 1-5ms                                                      │
│  What: full HTTP responses, API responses                            │
│  TTL: 30 seconds – 5 minutes                                        │
│  Controlled by: proxy config + backend Cache-Control headers         │
│  Hit rate target: 70-90%                                             │
└──────────────────────────────────────────────────────────────────────┘
         │ (cache miss)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 4: APPLICATION CACHE (in-process)                              │
│  Where: app server memory (Python dict, Guava, lru-cache)            │
│  Latency: <0.1ms (same process)                                     │
│  What: computed values, config, session data, hot objects             │
│  TTL: 30 seconds – 5 minutes                                        │
│  Controlled by: your code                                            │
│  Hit rate target: 60-80%                                             │
└──────────────────────────────────────────────────────────────────────┘
         │ (cache miss)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 5: DISTRIBUTED CACHE (shared)                                  │
│  Where: Redis Cluster, Memcached                                     │
│  Latency: 1-5ms (network hop)                                       │
│  What: DB query results, API responses, sessions, computed results   │
│  TTL: 5 minutes – 1 hour                                            │
│  Controlled by: your code                                            │
│  Hit rate target: 85-95%                                             │
└──────────────────────────────────────────────────────────────────────┘
         │ (cache miss)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 6: DATABASE QUERY CACHE                                        │
│  Where: database engine (materialized views, query cache)            │
│  Latency: 5-20ms                                                     │
│  What: expensive queries, aggregations                               │
│  TTL: varies                                                         │
│  Controlled by: DB config, materialized view refresh                 │
└──────────────────────────────────────────────────────────────────────┘
         │ (all misses)
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Layer 7: DATABASE (source of truth)                                  │
│  Latency: 10-100ms+                                                  │
│  Only 1-5% of original traffic reaches here                          │
└──────────────────────────────────────────────────────────────────────┘
```

### Each Layer Absorbs Traffic

```
1,000 requests/second arrive

  Browser cache:  850 served instantly (85%)        → 150 pass through
  CDN cache:      127 served at edge (85% of 150)   → 23 pass through
  Proxy cache:    18 served by Nginx (80% of 23)    → 5 pass through
  App cache:      3 served from memory (60% of 5)   → 2 pass through
  Redis cache:    1.7 served from Redis (85% of 2)  → 0.3 pass through
  Database:       0.3 requests/second actually hit DB

  1,000 req/s → 0.3 req/s at the database = 99.97% reduction
```

---

## 3. Hot, Warm, and Cold Cache

### Cache Temperature States

```
COLD CACHE
  Cache is empty or expired.
  Every request = cache MISS → goes to origin.
  Highest latency, highest backend load.
  
  When does this happen?
    - Fresh deploy / server restart
    - After a cache purge
    - TTL expired on all content
    - New CDN edge node with no data

WARM CACHE
  Requests are coming in, cache is filling up.
  Mix of hits and misses.
  Latency improving, backend load decreasing.
  
  Duration: depends on traffic volume.
    High traffic site: warm in seconds
    Low traffic site: warm in hours

HOT CACHE
  All frequently requested content is cached and fresh.
  Almost every request = cache HIT.
  Lowest latency, lowest backend load.
  This is the ideal state.
```

### The Warming and Cooling Cycle

```
Cache         Cold        Warming        Hot          Cooling       Cold
State:        ────────── ────────────── ──────────── ──────────── ──────────
Hits:         0%          increasing      90%+         decreasing   0%
              │           │               │            │            │
              ▼           ▼               ▼            ▼            ▼
Timeline:   Deploy    Traffic ramps    Steady state  TTLs expire  All expired
              ├──────────┼───────────────┼────────────┼────────────┤
              0          5 min           hours         TTL expiry   

The cycle repeats:
  Hot → content starts expiring (TTL) → cold → traffic warms it up → hot again

Problem: if ALL content expires at the same time → cold cache → stampede
Solution: stagger TTLs, add jitter, use stale-while-revalidate
```

---

## 4. Cache Freshness and TTL

### Time To Live (TTL)

```
TTL = how long a cached response is considered "fresh"

  max-age: 3600   →  cached for 1 hour
  
  Timeline:
    0s: response cached (fresh)
    1800s: still fresh (30 min in)
    3599s: still fresh (1 second left)
    3600s: STALE (expired)
    3601s: next request → must revalidate or fetch new

After TTL expires:
  Option 1: fetch entirely new response from origin
  Option 2: revalidate (ask origin "did it change?")
             If not changed → origin returns 304 Not Modified → extend TTL
             If changed → origin returns 200 with new content
```

### Choosing TTL Values

```
Content Type                     Recommended TTL     Why
──────────────────────────────── ──────────────────── ────────────────────
Static assets (JS, CSS, images)  1 year (31536000s)  Filename has hash (main.abc123.js)
                                                     New deploy = new filename = new cache
Fonts                            1 year              Never change
Favicon, logos                   1 week              Rarely change
HTML pages (static)              5 min – 1 hour      Content updates infrequently
HTML pages (dynamic)             0 (no-cache)        Must always be fresh
API responses (public data)      1 min – 5 min       Depends on staleness tolerance
API responses (user-specific)    0 (private)         Never cache on shared caches
Config / feature flags           30s – 2 min         Needs quick propagation
Real-time data (stock prices)    0                   Must be live
```

---

## 5. HTTP Cache-Control

### Every Directive Explained

```
Cache-Control is THE header that controls caching.
Sent by your server in the HTTP response.
Read by: browser, CDN, proxy — everyone in the chain.
```

### Storage Directives — WHO Can Cache

```
public
  ANY cache can store this (browser, CDN, proxy, everything).
  Use for: static assets, public API responses.
  
  Cache-Control: public, max-age=3600

private
  ONLY the user's browser can cache this. CDN/proxy must NOT.
  Use for: user-specific content (profile, dashboard, account).
  
  Cache-Control: private, max-age=300

no-store
  NOBODY can cache this. Period. Not even the browser.
  Use for: passwords, credit card forms, bank transactions.
  
  Cache-Control: no-store
```

### Freshness Directives — HOW LONG to Cache

```
max-age=N
  Cache for N seconds. Applies to ALL caches (browser + CDN).
  
  Cache-Control: max-age=3600     → cache for 1 hour everywhere

s-maxage=N
  Cache for N seconds, but ONLY on shared caches (CDN, proxy).
  OVERRIDES max-age for shared caches. Browser still uses max-age.
  
  Cache-Control: max-age=60, s-maxage=3600
  → Browser: cache 60 seconds
  → CDN: cache 1 hour
  
  This is the most important directive for CDN strategies.
  Short browser cache (user gets fresh quickly on reload)
  + long CDN cache (reduces origin load)
```

### Revalidation Directives — WHAT TO DO When Expired

```
no-cache
  ⚠️  DOES NOT MEAN "don't cache"!
  It means: cache it, but ALWAYS revalidate before serving.
  Every request → ask origin "did it change?" (conditional request).
  If 304 → serve from cache. If 200 → update cache.
  
  Cache-Control: no-cache
  
  Use for: HTML pages where you want instant updates on change
  but still benefit from 304 (no body transfer).

must-revalidate
  After max-age expires, you MUST revalidate. Cannot serve stale.
  Without this, caches are allowed to serve stale during origin outage.
  
  Cache-Control: max-age=3600, must-revalidate

proxy-revalidate
  Same as must-revalidate, but only for shared caches (CDN/proxy).
  Browser can still serve stale.
```

### Stale Serving Directives — GRACEFUL DEGRADATION

```
stale-while-revalidate=N
  After max-age expires, serve stale for up to N more seconds
  WHILE refreshing in the background.
  
  Cache-Control: max-age=60, stale-while-revalidate=300
  
  0-60s:    serve from cache (fresh)
  60-360s:  serve stale, trigger background refresh
  360s+:    must fetch new (fully expired)
  
  User never waits. Gets a response instantly, even if slightly stale.
  This is THE directive for high-availability caching.

stale-if-error=N
  If origin returns 5xx or is unreachable,
  serve stale content for up to N seconds.
  
  Cache-Control: max-age=60, stale-if-error=86400
  
  Origin is down? Serve yesterday's data instead of an error page.
  This SAVES YOUR SITE during outages.

immutable
  This content will NEVER change (until a new URL).
  Browser: don't even revalidate on reload.
  
  Cache-Control: public, max-age=31536000, immutable
  
  Use for: versioned static assets (main.abc123.js)
  The hash in the filename IS the version. If content changes, 
  the filename changes, so the old cached version is never wrong.
```

### The Full Header Anatomy

```
Cache-Control: public, max-age=60, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=604800

Breaking it down:
  public                         → CDN and browser can cache
  max-age=60                     → browser: fresh for 60 seconds
  s-maxage=3600                  → CDN: fresh for 1 hour
  stale-while-revalidate=86400   → after expiry, serve stale for 1 day while refreshing
  stale-if-error=604800          → if origin is down, serve stale for 7 days
```

---

## 6. Browser Caching

### How the Browser Cache Works

```
First visit to myapp.com:

  Browser → Server: GET /main.abc123.js
  Server → Browser: 200 OK
    Cache-Control: public, max-age=31536000, immutable
    ETag: "abc123"
    Content: (file contents)
  
  Browser stores in disk cache.

Second visit (within max-age):

  Browser checks cache: /main.abc123.js → found, still fresh
  Serves from disk. No network request at all.
  Latency: 0ms.

After max-age expires (without immutable):

  Browser → Server: GET /main.abc123.js
    If-None-Match: "abc123"            ← "I have this version, changed?"
  
  Server checks ETag:
    Same?  → 304 Not Modified (no body, just headers, ~200 bytes)
    Changed? → 200 OK (full new content)

  304 saves bandwidth: no content transferred, just confirmation.
```

### ETag vs Last-Modified

```
ETag (preferred):
  Server generates a hash/version string for the content.
  Response: ETag: "abc123def456"
  Next request: If-None-Match: "abc123def456"
  Server compares hashes.

Last-Modified (older):
  Server sends the file's modification timestamp.
  Response: Last-Modified: Wed, 15 May 2026 10:30:00 GMT
  Next request: If-Modified-Since: Wed, 15 May 2026 10:30:00 GMT
  Server compares timestamps.

ETag is more precise (catches changes that don't update timestamps).
Use both for maximum compatibility.
```

### Vary Header — Cache Keying

```
Problem: same URL returns different content for different clients.
  /api/products → JSON (Accept: application/json)
  /api/products → HTML (Accept: text/html)

Solution: Vary header tells caches to key on specific request headers.

  Vary: Accept
  → CDN caches TWO versions: one for JSON, one for HTML

  Vary: Accept-Encoding
  → CDN caches separate versions for gzip, brotli, identity

  Vary: Accept, Accept-Encoding, Accept-Language
  → many combinations → cache fragmentation → lower hit rate

Rule: keep Vary as minimal as possible.
  Vary: Cookie → effectively uncacheable (every user has different cookies)
```

---

## 7. CDN and Edge Caching

### How a CDN Works

```
Without CDN:
  User in Tokyo → Server in Virginia → 200ms round trip (16,000 km)

With CDN:
  User in Tokyo → CDN edge in Tokyo (cache hit) → 5ms
  
  CDN has hundreds of "Points of Presence" (PoPs) worldwide.
  Each PoP caches your content.
  Users hit the nearest PoP.

First request to a PoP:
  User → Tokyo PoP → cache MISS → origin server → 200ms
  PoP stores the response.

Subsequent requests to same PoP:
  User → Tokyo PoP → cache HIT → 5ms
  Origin never contacted.
```

### CDN Cache Behavior

```
CDN respects these headers from your origin:
  s-maxage          → CDN-specific TTL (overrides max-age for CDN)
  Cache-Control     → general caching rules
  Surrogate-Control → CDN-specific (Fastly, Varnish)
  CDN-Cache-Control → newer standard, CDN-only

Priority (what CDN uses):
  1. CDN-Cache-Control (if supported)
  2. Surrogate-Control (if supported)
  3. s-maxage (standard)
  4. max-age (fallback)

CDN ignores:
  private           → CDN will NOT cache
  no-store          → CDN will NOT cache
  Authorization header present → CDN will NOT cache (unless public)
```

### CDN Purging / Invalidation

```
Problem: you cached content for 24 hours but need to update NOW.

Solutions:

1. Purge by URL
   CloudFront: aws cloudfront create-invalidation --paths "/api/products/*"
   Cloudflare: curl -X POST .../purge_cache --data '{"files":["https://myapp.com/page"]}'
   
   Limitation: doesn't scale (can't purge 1M URLs)

2. Purge by tag (Surrogate Key)
   Your origin sends: Surrogate-Key: product-123 product-list
   Purge all content tagged "product-123":
     curl -X POST .../purge/product-123
   
   Only supported by Fastly, Cloudflare (Cache Tags), Varnish.
   Best approach for dynamic content.

3. Version in URL
   /api/v2/products → change to /api/v3/products
   Old version naturally expires. New version cached fresh.
   
   Works everywhere but changes your API URLs.

4. Cache-busting query string
   /styles.css?v=12345 → /styles.css?v=12346
   Works but some CDNs ignore query strings by default.

Best practice:
  Static assets: hash in filename (main.abc123.js) — never need to purge
  API responses: short TTL + stale-while-revalidate — purge rarely
  Emergency: CDN purge API + cache warming
```

---

## 8. Reverse Proxy Caching

### Nginx as a Cache

```
Nginx sits between the CDN and your application servers.
It can cache responses so your app isn't called on every request.

            CDN miss
               │
               ▼
         ┌───────────┐
         │   Nginx    │  ← checks its local cache first
         │   Cache    │     if hit → return immediately
         └─────┬─────┘     if miss → forward to app
               │
               ▼
         ┌───────────┐
         │  App       │
         │  Server    │
         └───────────┘
```

### Nginx Cache Configuration

```nginx
# Define cache zone
proxy_cache_path /var/cache/nginx
  levels=1:2
  keys_zone=app_cache:100m     # 100MB for keys in memory
  max_size=10g                  # 10GB on disk
  inactive=60m                  # remove if not accessed for 60min
  use_temp_path=off;

server {
    location /api/ {
        proxy_cache app_cache;
        proxy_cache_valid 200 302 10m;        # cache 200/302 for 10 min
        proxy_cache_valid 404 1m;              # cache 404 for 1 min
        proxy_cache_use_stale error timeout updating http_500 http_502;
        proxy_cache_background_update on;      # refresh in background
        proxy_cache_lock on;                   # prevent stampede
        proxy_cache_lock_timeout 5s;

        # Show cache status in response header
        add_header X-Cache-Status $upstream_cache_status;
        # Values: MISS, HIT, STALE, UPDATING, BYPASS

        proxy_pass http://app_backend;
    }
}
```

### Varnish — Dedicated HTTP Cache

```
Varnish is a purpose-built HTTP cache (faster than Nginx for caching).

Used by: Wikipedia, The Guardian, NY Times, Twitch.

Key feature: VCL (Varnish Configuration Language) lets you write
custom caching logic:

  sub vcl_recv {
    # Strip cookies for static assets (make them cacheable)
    if (req.url ~ "\.(css|js|png|jpg|gif)$") {
      unset req.http.Cookie;
    }
    
    # Don't cache POST requests
    if (req.method == "POST") {
      return(pass);
    }
  }
  
  sub vcl_backend_response {
    # Cache API responses for 5 minutes
    if (bereq.url ~ "^/api/") {
      set beresp.ttl = 5m;
      set beresp.grace = 1h;    # serve stale for 1h during origin failure
    }
  }
```

---

## 9. Application-Level Caching

### In-Process Cache (L1)

```
The fastest cache: data stored in your app's memory.
No network hop. Sub-microsecond access.

Problem: each app instance has its own cache (not shared).
         If you have 10 instances, 10 separate caches.

Use for:
  - Config/feature flags (small, rarely changes)
  - Hot data (top 100 products, trending items)
  - Computed values (expensive calculations)
```

### Python Examples

```python
# 1. Simple TTL cache with functools
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def get_product(product_id: str):
    return db.query("SELECT * FROM products WHERE id = %s", product_id)

# Problem: no TTL, no invalidation except clearing entire cache

# 2. TTL cache with cachetools
from cachetools import TTLCache
from cachetools import cached

product_cache = TTLCache(maxsize=10000, ttl=300)  # 5 min TTL

@cached(cache=product_cache)
def get_product(product_id: str):
    return db.query("SELECT * FROM products WHERE id = %s", product_id)

# Invalidate a specific key:
product_cache.pop("product-123", None)

# 3. FastAPI with in-memory cache
from fastapi import FastAPI
from cachetools import TTLCache

app = FastAPI()
cache = TTLCache(maxsize=5000, ttl=60)

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    if product_id in cache:
        return cache[product_id]     # cache hit: <0.1ms
    
    product = await db.fetch_product(product_id)  # cache miss: 20-50ms
    cache[product_id] = product
    return product
```

---

## 10. Distributed Caching — Redis & Memcached

### Redis as a Cache Layer

```
Redis sits between your app and database.
Shared across ALL app instances.
Sub-5ms latency. Handles millions of operations/second.

App Instance 1 ─┐
App Instance 2 ─┼──▶ Redis ──▶ Database
App Instance 3 ─┘    (shared)
```

### Redis Caching in Practice

```python
import redis.asyncio as aioredis
import json

redis = aioredis.from_url("redis://redis:6379", decode_responses=True)

async def get_product(product_id: str) -> dict:
    # 1. Check cache
    cached = await redis.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)    # cache hit: ~2ms
    
    # 2. Cache miss → query database
    product = await db.fetch_product(product_id)  # 20-50ms
    
    # 3. Store in cache with TTL
    await redis.set(
        f"product:{product_id}",
        json.dumps(product),
        ex=300,                      # expire in 5 minutes
    )
    
    return product


async def update_product(product_id: str, data: dict):
    # Update database
    await db.update_product(product_id, data)
    
    # Invalidate cache (next read will fetch fresh from DB)
    await redis.delete(f"product:{product_id}")
    
    # Also invalidate list cache
    await redis.delete("products:all")
```

### Redis vs Memcached

```
                    Redis                   Memcached
                    ─────                   ─────────
Data structures     strings, hashes,        strings only
                    lists, sets, sorted
                    sets, streams
Persistence         yes (RDB, AOF)          no (memory only)
Replication         yes (primary/replica)   no
Pub/Sub             yes                     no
Lua scripting       yes                     no
Max value size      512MB                   1MB
Clustering          Redis Cluster           client-side
Memory efficiency   less efficient          more efficient (slab allocator)
Threads             single (6.0+ I/O)       multi-threaded

Use Redis:    when you need more than simple key-value (99% of cases)
Use Memcached: pure caching, massive key-value, simpler operations
```

---

## 11. Caching Patterns

### Cache-Aside (Lazy Loading) — Most Common

```
App is responsible for reading/writing cache.

  READ:
    1. App checks cache
    2. Cache hit → return
    3. Cache miss → query DB → store in cache → return

  WRITE:
    1. App writes to DB
    2. App invalidates (deletes) cache key

  ┌─────┐  1.check  ┌───────┐
  │ App │──────────▶│ Cache │
  │     │◀──────────│       │
  │     │  2.hit    └───────┘
  │     │
  │     │  3.miss   ┌───────┐
  │     │──────────▶│  DB   │
  │     │◀──────────│       │
  └─────┘  4.result └───────┘
       │
       │ 5. store result in cache

Pros:  only requested data is cached (memory efficient)
       cache failure doesn't break the app (just slower)
Cons:  first request for every key is slow (cache miss)
       data can be stale between DB write and cache invalidation
```

### Write-Through

```
Every write goes to cache AND database, synchronously.
Cache is always consistent with DB.

  WRITE:
    1. App writes to cache
    2. Cache writes to DB (synchronously)
    3. Both updated → return to client

  READ:
    1. Always from cache (it's always up-to-date)

  ┌─────┐  write  ┌───────┐  write  ┌───────┐
  │ App │────────▶│ Cache │────────▶│  DB   │
  │     │◀────────│       │◀────────│       │
  └─────┘  ack    └───────┘  ack    └───────┘

Pros:  cache is never stale (strong consistency)
       reads are always fast (always from cache)
Cons:  write latency is HIGHER (write to two places)
       caches data that may never be read (waste of memory)
```

### Write-Behind (Write-Back)

```
Writes go to cache ONLY. Cache flushes to DB asynchronously.

  WRITE:
    1. App writes to cache
    2. Return to client immediately (fast!)
    3. Cache batches writes and flushes to DB periodically

  ┌─────┐  write  ┌───────┐   async   ┌───────┐
  │ App │────────▶│ Cache │──────────▶│  DB   │
  │     │◀────────│       │  (batch)   │       │
  └─────┘  ack    └───────┘           └───────┘
       (instant)        └─ flushes every 5s or 100 writes

Pros:  lowest write latency (returns before DB write)
       batching reduces DB write load
Cons:  DATA LOSS if cache crashes before flushing
       complexity (must handle flush failures)
       
Use for: analytics, view counts, non-critical writes
Never for: payments, orders, anything you can't lose
```

### Read-Through

```
Cache itself fetches from DB on miss (app never talks to DB directly).

  READ:
    1. App asks cache for key
    2. Cache hit → return
    3. Cache miss → cache fetches from DB → stores → returns

  ┌─────┐  read   ┌───────┐  fetch   ┌───────┐
  │ App │────────▶│ Cache │─────────▶│  DB   │
  │     │◀────────│       │◀─────────│       │
  └─────┘ result  └───────┘  result  └───────┘

App only talks to cache. Cache handles DB interaction.
Simpler app code, but cache needs DB access.
```

### Comparison

```
Pattern          Consistency    Write Speed    Read Speed    Data Loss Risk
───────────────  ────────────   ───────────    ──────────    ──────────────
Cache-Aside      Eventual       Fast (DB)      Slow 1st     None
Write-Through    Strong         Slow (2 writes)Always fast   None
Write-Behind     Eventual       Fastest        Always fast   YES
Read-Through     Eventual       N/A            Slow 1st      None

Most teams: Cache-Aside for reads + direct DB writes + Redis.
FAANG: multi-layer (cache-aside + write-behind for analytics).
```

---

## 12. Caching Personalized Content

### The Challenge

```
Public content:     /homepage → same for everyone → easy to cache
Personalized:       /dashboard → different for every user → hard to cache

If you set Cache-Control: public on personalized content:
  User A sees User B's dashboard → security disaster

If you set Cache-Control: no-store on everything:
  No caching at all → back to square one
```

### Strategies

```
Strategy 1: Separate Public Shell + Private Data

  Page shell (HTML layout, CSS, JS) → public, cached at CDN
  User data (name, orders, etc.)    → private, fetched via AJAX

  Browser loads cached shell (instant)
  Then fetches personalized data (async, private, no CDN cache)

  Cache-Control for shell: public, max-age=3600
  Cache-Control for API:   private, no-cache

  This is what every FAANG site does.
  Facebook, Twitter, Amazon: the page structure loads from cache,
  then personal content fills in via API calls.

Strategy 2: Edge-Side Includes (ESI)

  CDN assembles the page from cached fragments:
    <esi:include src="/header" />          ← cached, same for all
    <esi:include src="/user-greeting" />   ← private, per user
    <esi:include src="/product-list" />    ← cached, same for all

  CDN caches the public parts, fetches private parts from origin.
  Supported by Varnish, Akamai, Fastly.

Strategy 3: Cache Per User (Redis)

  Cache key includes user ID:
    cache_key = f"user:{user_id}:dashboard"
  
  Each user's data cached separately in Redis.
  Works for app-level cache, NOT for CDN (too many variations).

Strategy 4: Vary by Cookie/Token (CDN — careful!)

  Vary: Cookie → CDN caches different versions per cookie
  Problem: millions of users = millions of cache entries = terrible hit rate
  Almost never the right approach at CDN level.
```

---

## 13. Cache Invalidation

### "The Two Hard Things in Computer Science"

```
"There are only two hard things in Computer Science:
 cache invalidation and naming things."
 — Phil Karlton

Why it's hard:
  You have data in 6 places (browser, CDN, proxy, app, Redis, DB).
  DB changes → all 6 places have stale data.
  How do you update all of them instantly? You can't.
```

### Invalidation Strategies

```
1. TTL-BASED (time expiry)
   Set it and forget it. Data expires after N seconds.
   
   Pros: simple, no coordination needed
   Cons: data is stale until expiry
   Best for: product catalogs, articles, config
   
   redis.set("product:123", data, ex=300)  # expires in 5 min

2. EVENT-DRIVEN (on write)
   When data changes, immediately invalidate cache.
   
   Pros: minimal staleness
   Cons: need to know all cache keys affected by a change
   Best for: user profiles, inventory counts
   
   def update_product(product_id, data):
       db.update(product_id, data)
       redis.delete(f"product:{product_id}")
       redis.delete("products:all")
       cdn.purge(f"/api/products/{product_id}")

3. VERSION-BASED
   Include a version number in the cache key.
   Increment version to invalidate everything at once.
   
   version = redis.get("products:version")  # "7"
   cache_key = f"products:v{version}:list"
   
   # Invalidate all product caches:
   redis.incr("products:version")  # now "8", all old keys miss

4. TAG-BASED (Surrogate Keys)
   Associate cache entries with tags.
   Purge all entries with a specific tag.
   
   # Cache entry tagged: ["product:123", "category:electronics"]
   # Purge "category:electronics" → invalidates all electronics products
   
   Supported by Fastly, Cloudflare, Varnish.
```

---

## 14. Cache Stampede (Thundering Herd)

### The Problem

```
Popular cache key "homepage" cached with TTL=60s.
Key is requested 10,000 times/second.

Second 60: TTL expires.
Second 60.001: 10,000 requests arrive simultaneously.
All see "cache miss" → all query the database.
Database: 10,000 identical queries at once → CRASH.

This is a cache stampede.
```

### Solutions

```
1. LOCKING (only one request refreshes)

   async def get_with_lock(key):
       value = await redis.get(key)
       if value:
           return json.loads(value)
       
       # Try to acquire lock
       lock_acquired = await redis.set(f"lock:{key}", "1", nx=True, ex=5)
       
       if lock_acquired:
           # I won the lock → I fetch from DB
           value = await db.fetch(key)
           await redis.set(key, json.dumps(value), ex=300)
           await redis.delete(f"lock:{key}")
           return value
       else:
           # Someone else is fetching → wait briefly, then retry
           await asyncio.sleep(0.1)
           return await get_with_lock(key)

2. STALE-WHILE-REVALIDATE (serve stale, refresh in background)

   Don't let the key fully expire.
   Serve the old value while ONE background task fetches new.
   
   Cache-Control: max-age=60, stale-while-revalidate=300
   
   In Redis: store expiry timestamp in the value
   
   async def get_with_background_refresh(key, ttl=60, stale_ttl=300):
       raw = await redis.get(key)
       if raw:
           data = json.loads(raw)
           if data["expires_at"] < time.time():
               # Stale — trigger background refresh (don't block)
               asyncio.create_task(refresh_cache(key, ttl, stale_ttl))
           return data["value"]
       
       # True miss — must fetch synchronously
       return await refresh_cache(key, ttl, stale_ttl)

3. PROBABILISTIC EARLY REFRESH (XFetch)

   Each request has a small probability of refreshing BEFORE expiry.
   As expiry approaches, probability increases.
   One request triggers refresh early → no stampede.
   
   remaining_ttl = await redis.ttl(key)
   probability = max(0, 1 - (remaining_ttl / original_ttl))
   if random.random() < probability:
       refresh_cache(key)
   
   Result: refresh happens naturally, ~1 request before expiry.
   No locking, no coordination.

4. NGINX proxy_cache_lock

   proxy_cache_lock on;
   # Only ONE request fetches from backend.
   # All others wait for that ONE to complete, then get cached response.
```

---

## 15. Common Problems and Solutions

### Problem 1: Bad Response Cached

```
What happened:
  1. Product API returns 500 error temporarily
  2. Your frontend caches the error page with TTL=7 days
  3. Now every user sees the error for 7 DAYS
  4. The actual API recovered in 2 minutes

Why no alarms?
  CDN is serving the cached error → origin sees zero traffic → looks healthy
  APM sees no errors → cached 500 is served by CDN, not your app

Solutions:
  1. NEVER cache error responses
     proxy_cache_valid 200 302 10m;    # only cache successful responses
     proxy_cache_valid 500 502 0;       # never cache errors
  
  2. Validate response before caching
     Only cache if response body looks correct (has expected fields)
  
  3. Short TTL for dynamic content
     max-age=60 instead of max-age=604800
     If bad response is cached, it's gone in 60 seconds
  
  4. Emergency purge procedure
     Have a "purge everything" button/script ready
     aws cloudfront create-invalidation --paths "/*"
```

### Problem 2: Stale Content After Deploy

```
What happened:
  Deploy v2 of your app. HTML references new JS/CSS files.
  But CDN still serves old HTML (cached) → references old JS files.
  Old JS files → might be gone or incompatible.

Solution: content-hashed filenames + short HTML TTL
  CSS/JS: main.abc123.css (hash in name, cache forever)
  HTML:   Cache-Control: no-cache (always revalidate)
  
  Deploy v2: HTML changes to reference main.def456.css
  Browser gets fresh HTML → loads new CSS file → correct version
  Old CSS file stays in cache but nobody references it anymore.
```

### Problem 3: Cache Poisoning

```
What happened:
  Attacker sends: GET /page HTTP/1.1, Host: evil.com
  CDN caches the response keyed on URL (not Host header)
  Now all users requesting /page get the version rendered for evil.com

Solution:
  1. CDN should key on Host header (most do by default)
  2. Validate Host header in your app
  3. Normalize cache keys
```

### Problem 4: Personal Data Leaked via Cache

```
What happened:
  User A's profile page cached without "private" directive
  CDN caches it → User B sees User A's data

Solution:
  ALWAYS set private for user-specific responses:
  Cache-Control: private, no-cache
  
  OR separate public shell from private data (Strategy 1 in Section 12)
```

---

## 16. Cache Warming

### Pre-Filling Cache After Purge or Deploy

```
After a deploy or cache purge, cache is COLD.
First users hit origin → slow, high load.

Warming = proactively filling the cache before users arrive.
```

### Strategies

```
1. Priority URL list
   Crawl your top 1000 URLs immediately after deploy:
   
   #!/bin/bash
   while read url; do
     curl -s -o /dev/null "$url" &
   done < priority-urls.txt
   wait

2. Traffic replay
   Capture recent access logs → replay requests against new deploy:
   
   zcat access.log.gz | awk '{print $7}' | sort -u | head -10000 | \
     xargs -P 20 -I{} curl -s -o /dev/null "https://myapp.com{}"

3. Synthetic warming on startup
   App fetches and caches hot data on boot:
   
   @app.on_event("startup")
   async def warm_cache():
       top_products = await db.fetch("SELECT * FROM products ORDER BY views DESC LIMIT 1000")
       for product in top_products:
           await redis.set(f"product:{product.id}", json.dumps(product), ex=300)
       logger.info("Cache warmed with %d products", len(top_products))

4. Staggered TTLs (prevent future cold cache)
   Don't set all TTLs to exactly 300s.
   Add jitter: ttl = 300 + random.randint(0, 60)
   Result: keys expire at different times → no mass expiry → no cold cache
```

---

## 17. Measuring Cache Effectiveness

### Key Metrics

```
1. HIT RATE (most important)
   hit_rate = cache_hits / (cache_hits + cache_misses)
   
   Target:
     Browser cache:  85-95%
     CDN:           80-95%
     Redis:         85-95%
   
   Below 70% = something is wrong (bad TTLs, too many Vary headers,
   cache key includes something unique per request)

2. MISS RATE
   miss_rate = 1 - hit_rate
   Every miss = load on origin

3. LATENCY
   p50 latency with cache: ~5ms
   p50 latency without cache: ~200ms
   If p50 is high → cache isn't helping

4. ORIGIN OFFLOAD
   origin_offload = 1 - (origin_requests / total_requests)
   Target: 90%+ (only 10% of traffic hits origin)

5. EVICTION RATE
   How often cache removes items due to memory pressure.
   High eviction = cache too small, thrashing.

6. STALE SERVE RATE
   How often stale content is served (stale-while-revalidate).
   Some is fine. Too much = TTLs too short.
```

### Tools

```
Browser:   DevTools → Network tab → look for "(disk cache)" and "304"
CDN:       CloudFront/Cloudflare dashboard → cache hit ratio
Nginx:     X-Cache-Status header (HIT/MISS/STALE/BYPASS/EXPIRED)
Redis:     redis-cli INFO stats → keyspace_hits, keyspace_misses
App:       Prometheus metrics → cache_hits_total, cache_misses_total
Web perf:  webpagetest.org → lists uncached assets

# Redis hit rate
redis-cli INFO stats | grep keyspace
# keyspace_hits:483920112
# keyspace_misses:12984
# hit rate = 483920112 / (483920112 + 12984) = 99.997%
```

---

## 18. Getting Started

### Barker's Approach: Evaluate First

```
Step 1: EVALUATE YOUR ARCHITECTURE
  
  Open DevTools → Network tab → load your page.
  
  Questions:
    - How many requests go to origin on page load?
    - Do you see any 304 status codes? (If not → no caching at all)
    - Are static assets (JS, CSS) cached? (Check Cache-Control header)
    - Are API responses cached?
    - Does every click cause a full page refresh?
  
  If your app is a traditional server-rendered page-per-click:
    First modernize to async API calls + cached static shell.
    Then cache the APIs.

Step 2: CACHE YOUR STATIC CONTENT
  
  Add to your web server:
  
  # Nginx
  location ~* \.(js|css|png|jpg|gif|ico|woff2|svg)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
      access_log off;
  }
  
  Use content-hashed filenames (Webpack, Vite do this automatically):
    main.abc123.js → safe to cache forever

Step 3: CACHE YOUR API RESPONSES
  
  Add Cache-Control headers to your API:
  
  # Public data
  Cache-Control: public, max-age=60, s-maxage=300
  
  # User-specific data
  Cache-Control: private, max-age=60
  
  # Never cache
  Cache-Control: no-store

Step 4: ADD A CDN
  
  Put CloudFront/Cloudflare in front of your app.
  It reads your Cache-Control headers automatically.
  Instant global performance improvement.

Step 5: ADD REDIS FOR APP-LEVEL CACHING
  
  Cache expensive DB queries in Redis.
  Start with the slowest/most frequent queries.

Step 6: MEASURE
  
  Monitor hit rates. Target 90%+ at each layer.
  Use webpagetest.org monthly to catch regression.
```

---

## 19. Production Recipes

### Static Assets (JS, CSS, Images, Fonts)

```
Cache-Control: public, max-age=31536000, immutable

Use content-hashed filenames.
Cache forever. Never invalidate. New deploy = new filename.
```

### HTML Pages (Static/Blog)

```
Cache-Control: public, max-age=0, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=604800

Browser: always revalidate (max-age=0)
CDN: cache 1 hour, serve stale 1 day while refreshing, serve stale 7 days on error
```

### Public API Responses

```
Cache-Control: public, max-age=60, s-maxage=300, must-revalidate

Browser: 1 minute
CDN: 5 minutes
After expiry: must revalidate (don't serve stale)
```

### User-Specific API Responses

```
Cache-Control: private, max-age=300, must-revalidate

Only browser caches. CDN never sees it.
5-minute freshness.
```

### Real-Time Data

```
Cache-Control: no-store

Never cached anywhere. WebSocket or SSE instead.
```

### FastAPI Response Headers

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/api/products")
async def list_products(response: Response):
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=300"
    response.headers["Vary"] = "Accept"
    return {"products": [...]}

@app.get("/api/me")
async def get_profile(response: Response):
    response.headers["Cache-Control"] = "private, max-age=300"
    return {"name": "Alice", ...}

@app.get("/api/products/{id}")
async def get_product(id: str, response: Response):
    product = await cache_or_fetch(id)
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=300"
    response.headers["ETag"] = f'"{product["version"]}"'
    return product
```

---

## 20. Caching in Microservices and Kubernetes

### Where Caching Layers Map to K8s

```
┌──────────────────────────────────────────────────┐
│  OUTSIDE CLUSTER                                  │
│                                                  │
│  Browser Cache  → user's device                  │
│  CDN           → CloudFront / Cloudflare         │
└──────────────────────────┬───────────────────────┘
                           │
┌──────────────────────────▼───────────────────────┐
│  INSIDE CLUSTER                                    │
│                                                  │
│  Ingress (Nginx) → can cache (proxy_cache)       │
│       │                                          │
│       ├── order-service                          │
│       │     └── in-process cache (TTLCache)      │
│       │     └── Redis (shared cache)             │
│       │     └── PostgreSQL                       │
│       │                                          │
│       ├── product-service                        │
│       │     └── in-process cache (TTLCache)      │
│       │     └── Redis (same cluster)             │
│       │     └── PostgreSQL                       │
│       │                                          │
│  Redis Deployment (or AWS ElastiCache)           │
│       ClusterIP: redis.production:6379           │
└──────────────────────────────────────────────────┘

Cache hierarchy in K8s:
  1. Browser (Cache-Control headers from your API)
  2. CDN (s-maxage headers)
  3. Ingress Nginx (proxy_cache, optional)
  4. App in-process (TTLCache, per Pod)
  5. Redis (shared, ClusterIP Service)
  6. Database
```

### Redis in Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--maxmemory", "256mb", "--maxmemory-policy", "allkeys-lru"]
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            memory: 300Mi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
```

```
maxmemory-policy options:
  allkeys-lru      → evict least recently used (best for cache)
  volatile-lru     → evict LRU among keys with TTL set
  allkeys-random   → random eviction
  noeviction       → return error when full (NOT for cache use)
```

---

## Quick Reference

```
Header                              Meaning
────────────────────────────────── ────────────────────────────────────────
Cache-Control: public               anyone can cache
Cache-Control: private              only browser can cache
Cache-Control: no-store             nobody can cache
Cache-Control: no-cache             cache but revalidate every time
Cache-Control: max-age=N            fresh for N seconds (all caches)
Cache-Control: s-maxage=N           fresh for N seconds (CDN/proxy only)
Cache-Control: must-revalidate      don't serve stale after expiry
Cache-Control: immutable            never revalidate (use with hashed filenames)
Cache-Control: stale-while-revalidate=N  serve stale N seconds while refreshing
Cache-Control: stale-if-error=N     serve stale N seconds if origin is down
ETag: "abc123"                      version fingerprint for conditional requests
Vary: Accept                        cache separate versions per Accept header
```

```
Pattern           When to Use                        Consistency
───────────────── ────────────────────────────────── ──────────────
Cache-Aside       read-heavy, can tolerate staleness  eventual
Write-Through     must always read fresh data          strong
Write-Behind      write-heavy, can lose recent writes  eventual
Read-Through      simplify app code                    eventual
```

```
Problem              Solution
──────────────────── ─────────────────────────────────────
Cache stampede       locking, stale-while-revalidate, XFetch
Bad response cached  never cache 5xx, short TTLs, emergency purge
Stale after deploy   content-hashed filenames + no-cache HTML
Personal data leak   Cache-Control: private on user-specific responses
Cold cache           cache warming (URL list, traffic replay, jitter TTLs)
Cache too small      monitor evictions, increase maxmemory, check hit rate
```

---

*Covers concepts from "Intelligent Caching" by Tom Barker (O'Reilly, 2017),*
*expanded with backend patterns, Redis, and Kubernetes integration.*
