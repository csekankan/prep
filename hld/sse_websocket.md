# SSE & WebSocket — Scalable Real-Time Systems (Facebook/Google Level)

> Covers protocol internals, architecture patterns, load balancing, pub/sub fan-out, presence systems,
> practical issues, and production-grade code at depth.
> Every section includes runnable code and explains the "why" behind each design choice.
> **If you're new to real-time:** Start with [Section 0](#0-foundations--how-real-time-web-communication-works) first.

---

## Table of Contents

1. [Foundations — How Real-Time Web Communication Works](#0-foundations--how-real-time-web-communication-works)
2. [The HTTP Request-Response Limitation](#1-the-http-request-response-limitation)
3. [Server-Sent Events (SSE) — Deep Dive](#2-server-sent-events-sse--deep-dive)
4. [WebSocket — Deep Dive](#3-websocket--deep-dive)
5. [SSE vs WebSocket — When to Use What](#4-sse-vs-websocket--when-to-use-what)
6. [The Connection Lifecycle — Every Byte Explained](#5-the-connection-lifecycle--every-byte-explained)
7. [Scaling Challenge — Why Single Server Breaks](#6-scaling-challenge--why-single-server-breaks)
8. [Pub/Sub Architecture — The Fan-Out Pattern](#7-pubsub-architecture--the-fan-out-pattern)
9. [Load Balancers for Persistent Connections](#8-load-balancers-for-persistent-connections)
10. [Connection Management at Scale](#9-connection-management-at-scale)
11. [Presence Systems (Online/Offline/Typing)](#10-presence-systems-onlineofflinetyping)
12. [Message Ordering & Delivery Guarantees](#11-message-ordering--delivery-guarantees)
13. [Backpressure & Flow Control](#12-backpressure--flow-control)
14. [Reconnection Strategies & Gap Recovery](#13-reconnection-strategies--gap-recovery)
15. [Security at Scale](#14-security-at-scale)
16. [Monitoring, Observability & Debugging](#15-monitoring-observability--debugging)
17. [Production Architecture — Facebook/Google Patterns](#16-production-architecture--facebookgoogle-patterns)
18. [Complete Implementation — Chat System](#17-complete-implementation--chat-system)
19. [Complete Implementation — Live Dashboard with SSE](#18-complete-implementation--live-dashboard-with-sse)
20. [Common Pitfalls & War Stories](#19-common-pitfalls--war-stories)
21. [Interview Deep-Dive Questions](#20-interview-deep-dive-questions)
22. [Appendix — Web Workers for Offloading Client-Side Work](#21-appendix--web-workers-for-offloading-client-side-work)

---

## 0. Foundations — How Real-Time Web Communication Works

### The core problem

Traditional HTTP is **pull-based**: the client asks, the server answers. But modern apps need the
server to **push** data to clients the moment something happens:

```
Traditional HTTP (Pull):
  Client ──request──→ Server
  Client ←─response── Server
  (connection closed — server can't send anything else)

Real-Time (Push):
  Client ←── "new message from Alice" ──── Server  (at any time!)
  Client ←── "Bob is typing..." ────────── Server  (at any time!)
  Client ←── "Stock AAPL: $185.42" ──────── Server (at any time!)
```

### Evolution of real-time on the web

```
1995-2005: Polling        → Client asks every N seconds. Wasteful.
2005-2010: Long Polling   → Client asks, server HOLDS request until data arrives.
2006+:     SSE            → Server pushes over a single long-lived HTTP response.
2011+:     WebSocket      → Full-duplex TCP tunnel through HTTP upgrade.
```

### Why not just use polling?

At Facebook scale (2B+ users), polling is catastrophic:

```
Polling math at Facebook scale:
- 500M concurrent users
- Poll every 5 seconds
- = 100M requests/second just for "anything new?"
- 99% of responses: "nope, nothing"
- Wasted bandwidth: ~50 TB/day of empty responses
- Wasted server CPU: millions of DB queries returning empty
```

This is why persistent connections (SSE/WebSocket) exist — they eliminate the constant "anything new?" chatter.

### TCP/IP stack refresher (why this matters)

Every SSE/WebSocket connection ultimately sits on a TCP connection:

```
┌─────────────────────────────────────────────┐
│  Application Layer                           │
│  ┌─────────────────────────────────────┐    │
│  │  WebSocket / SSE / HTTP             │    │  ← Your code lives here
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  Transport Layer                             │
│  ┌─────────────────────────────────────┐    │
│  │  TCP (reliable, ordered, flow ctrl) │    │  ← Guarantees bytes arrive in order
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  Network Layer                               │
│  ┌─────────────────────────────────────┐    │
│  │  IP (routing, addressing)           │    │  ← Finds path between machines
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  Link Layer (Ethernet, WiFi)                 │
└─────────────────────────────────────────────┘
```

**Critical insight:** Each TCP connection consumes:
- A file descriptor on the server (Linux default limit: 1024, tunable to ~1M)
- ~3.5 KB of kernel memory for TCP buffers (per connection)
- Application-level state (user info, subscriptions, message queues)

At 1M concurrent connections: ~3.5 GB just for kernel TCP state, plus your app's per-connection memory.

---

## 1. The HTTP Request-Response Limitation

### Why HTTP/1.1 can't do real-time natively

HTTP/1.1 is fundamentally **half-duplex** within a single request:
1. Client sends a complete request (headers + body)
2. Server sends a complete response (headers + body)
3. Connection is either closed or reused for the NEXT request

The server **cannot** spontaneously send data outside of a response to a client's request.

### Long Polling — The hack before SSE/WebSocket

```python
# Server-side long polling (the "hack" era)
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
message_queues: dict[str, asyncio.Queue] = {}

@app.get("/poll/{user_id}")
async def long_poll(user_id: str, request: Request):
    """
    Client sends GET /poll/alice
    Server HOLDS the connection open (doesn't respond)
    When a message arrives for alice → respond immediately
    If 30 seconds pass with nothing → respond with empty, client re-polls
    """
    if user_id not in message_queues:
        message_queues[user_id] = asyncio.Queue()

    queue = message_queues[user_id]

    try:
        message = await asyncio.wait_for(queue.get(), timeout=30.0)
        return JSONResponse({"message": message})
    except asyncio.TimeoutError:
        return JSONResponse({"message": None})  # client will immediately re-poll
```

**Problems with long polling at scale:**

| Problem | Impact at Facebook Scale |
|---------|------------------------|
| Thundering herd | 500M clients all re-poll simultaneously after timeout |
| Head-of-line blocking | Intermediate proxies may buffer the response |
| Connection churn | TCP handshake + TLS overhead per re-poll (~100ms) |
| Load balancer state | Can't predict which server holds which user's pending poll |
| Message ordering | Messages during re-poll gap get lost |

---

## 2. Server-Sent Events (SSE) — Deep Dive

### What is SSE?

SSE is a **W3C standard** (part of HTML5) that allows the server to push events to the client over a
**single long-lived HTTP response**. The key insight: the server never "finishes" sending the response body.

### The protocol — every byte explained

```
CLIENT REQUEST:
GET /events HTTP/1.1
Host: api.example.com
Accept: text/event-stream        ← "I want SSE"
Cache-Control: no-cache          ← Don't cache this stream
Last-Event-ID: 42               ← Resume from event 42 (reconnection!)

SERVER RESPONSE:
HTTP/1.1 200 OK
Content-Type: text/event-stream  ← "This is an SSE stream"
Cache-Control: no-cache          ← Proxies: don't buffer this!
Connection: keep-alive           ← Don't close after "response"
X-Accel-Buffering: no           ← Nginx: don't buffer this!
Transfer-Encoding: chunked       ← No Content-Length (stream is infinite)

data: {"user": "alice", "msg": "hello"}    ← Event 1

event: typing                               ← Named event
data: {"user": "bob"}                       ← Event 2

id: 43                                      ← Event ID (for resume)
event: message
data: {"user": "charlie", "msg": "hey"}     ← Event 3
data: {"continues": "on next line"}         ← Multi-line data

retry: 5000                                 ← Tell client to reconnect after 5s

: this is a comment (heartbeat)             ← Keep-alive (ignored by EventSource)

```

### SSE message format rules

```
Each message consists of one or more lines, each starting with a field name:
  - "data:"    → The payload (can span multiple lines)
  - "event:"   → Event type (default is "message" if omitted)
  - "id:"      → Unique event ID (sent as Last-Event-ID on reconnect)
  - "retry:"   → Reconnection time in milliseconds
  - ":"        → Comment (useful as heartbeat to prevent proxy timeouts)

Messages are separated by TWO newlines (\n\n).
Within a message, fields are separated by ONE newline (\n).
```

### FastAPI SSE implementation — production-grade

```python
import asyncio
import json
import time
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

class SSEConnectionManager:
    """Manages SSE connections with heartbeat and graceful shutdown."""

    def __init__(self):
        self.active_connections: dict[str, asyncio.Queue] = {}
        self.connection_metadata: dict[str, dict] = {}
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self):
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    def connect(self, client_id: str, last_event_id: str | None = None) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.active_connections[client_id] = queue
        self.connection_metadata[client_id] = {
            "connected_at": time.time(),
            "last_event_id": last_event_id,
            "events_sent": 0,
        }
        return queue

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        self.connection_metadata.pop(client_id, None)

    async def send_event(
        self,
        client_id: str,
        data: dict,
        event_type: str = "message",
        event_id: str | None = None,
    ):
        queue = self.active_connections.get(client_id)
        if queue is None:
            return False

        try:
            queue.put_nowait({"data": data, "event": event_type, "id": event_id})
            self.connection_metadata[client_id]["events_sent"] += 1
            return True
        except asyncio.QueueFull:
            # Backpressure: client is too slow. Drop or disconnect.
            self.disconnect(client_id)
            return False

    async def broadcast(self, data: dict, event_type: str = "message"):
        disconnected = []
        for client_id in list(self.active_connections.keys()):
            success = await self.send_event(client_id, data, event_type)
            if not success:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)

    async def _heartbeat_loop(self):
        """Send heartbeat comments every 15 seconds to prevent proxy timeouts."""
        while True:
            await asyncio.sleep(15)
            for client_id, queue in list(self.active_connections.items()):
                try:
                    queue.put_nowait({"heartbeat": True})
                except asyncio.QueueFull:
                    self.disconnect(client_id)


sse_manager = SSEConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await sse_manager.start()
    yield
    await sse_manager.stop()

app = FastAPI(lifespan=lifespan)


def format_sse_message(event_data: dict) -> str:
    """Format a dict into the SSE wire protocol."""
    if event_data.get("heartbeat"):
        return ": heartbeat\n\n"

    lines = []
    if event_data.get("id"):
        lines.append(f"id: {event_data['id']}")
    if event_data.get("event") and event_data["event"] != "message":
        lines.append(f"event: {event_data['event']}")

    payload = json.dumps(event_data["data"])
    for line in payload.split("\n"):
        lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


async def event_stream(client_id: str, request: Request) -> AsyncGenerator[str, None]:
    """Generator that yields SSE-formatted events until client disconnects."""
    last_event_id = request.headers.get("Last-Event-ID")
    queue = sse_manager.connect(client_id, last_event_id)

    # If client is resuming, replay missed events
    if last_event_id:
        missed_events = await replay_missed_events(client_id, last_event_id)
        for event in missed_events:
            yield format_sse_message(event)

    try:
        while True:
            # Check if client disconnected (ASGI disconnect event)
            if await request.is_disconnected():
                break

            try:
                event_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield format_sse_message(event_data)
            except asyncio.TimeoutError:
                continue  # loop back to check is_disconnected
    finally:
        sse_manager.disconnect(client_id)


@app.get("/events/{client_id}")
async def sse_endpoint(client_id: str, request: Request):
    """SSE endpoint with proper headers for proxies and browsers."""
    return StreamingResponse(
        event_stream(client_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",       # Nginx: disable buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


async def replay_missed_events(client_id: str, last_event_id: str) -> list[dict]:
    """
    Fetch events that the client missed during disconnection.
    In production, this queries Redis Streams or a database.
    """
    # events = await redis.xrange(f"events:{client_id}", min=last_event_id, count=1000)
    return []
```

### Client-side SSE — The EventSource API

```javascript
class RobustEventSource {
  constructor(url, options = {}) {
    this.url = url;
    this.maxRetries = options.maxRetries || Infinity;
    this.retryCount = 0;
    this.baseDelay = 1000;
    this.maxDelay = 30000;
    this.lastEventId = null;
    this.handlers = {};
    this.connect();
  }

  connect() {
    // EventSource automatically sends Last-Event-ID header on reconnect
    this.source = new EventSource(this.url);

    this.source.onopen = () => {
      console.log('SSE connected');
      this.retryCount = 0;  // Reset on successful connection
    };

    // Default "message" event
    this.source.onmessage = (event) => {
      this.lastEventId = event.lastEventId;
      const data = JSON.parse(event.data);
      this.emit('message', data);
    };

    // Named events
    this.source.addEventListener('typing', (event) => {
      this.emit('typing', JSON.parse(event.data));
    });

    this.source.addEventListener('presence', (event) => {
      this.emit('presence', JSON.parse(event.data));
    });

    this.source.onerror = (error) => {
      // EventSource automatically reconnects, but we add exponential backoff
      this.source.close();
      this.retryCount++;

      if (this.retryCount > this.maxRetries) {
        this.emit('fatal_error', { message: 'Max retries exceeded' });
        return;
      }

      const delay = Math.min(
        this.baseDelay * Math.pow(2, this.retryCount) + Math.random() * 1000,
        this.maxDelay
      );

      console.log(`SSE reconnecting in ${delay}ms (attempt ${this.retryCount})`);
      setTimeout(() => this.connect(), delay);
    };
  }

  on(event, handler) {
    if (!this.handlers[event]) this.handlers[event] = [];
    this.handlers[event].push(handler);
  }

  emit(event, data) {
    (this.handlers[event] || []).forEach(handler => handler(data));
  }

  close() {
    this.source.close();
  }
}

// Usage
const events = new RobustEventSource('/events/user_123');
events.on('message', (data) => console.log('New message:', data));
events.on('typing', (data) => console.log('Typing:', data));
```

### SSE limitations (important for architecture decisions)

| Limitation | Detail | Impact |
|-----------|--------|--------|
| Unidirectional | Server → Client only | Client must use separate HTTP requests to send data |
| 6 connection limit | Browsers limit to 6 SSE connections per domain (HTTP/1.1) | Use HTTP/2 (multiplexed) or single multiplexed stream |
| Text only | No binary frames | Must base64-encode binary data (33% overhead) |
| No custom headers on reconnect | EventSource only sends Last-Event-ID | Auth tokens must be in URL or cookies |
| Proxy buffering | Intermediate proxies may buffer chunked responses | Need X-Accel-Buffering: no, proxy_buffering off |

### HTTP/2 removes the 6-connection limit

```
HTTP/1.1: Each SSE stream = 1 TCP connection (max 6 per domain)
HTTP/2:   All SSE streams multiplex over 1 TCP connection (no practical limit)

┌─────── HTTP/1.1 ───────┐       ┌────────── HTTP/2 ──────────┐
│ TCP Conn 1: SSE /chat  │       │ Single TCP Connection:     │
│ TCP Conn 2: SSE /notif │       │   Stream 1: SSE /chat      │
│ TCP Conn 3: SSE /prices│       │   Stream 3: SSE /notif     │
│ TCP Conn 4: SSE /typing│       │   Stream 5: SSE /prices    │
│ TCP Conn 5: (regular)  │       │   Stream 7: SSE /typing    │
│ TCP Conn 6: (regular)  │       │   Stream 9: GET /api/...   │
│ ❌ No more available!  │       │   Stream 11: POST /api/... │
└────────────────────────┘       │   ... (thousands possible) │
                                  └────────────────────────────┘
```

---

## 3. WebSocket — Deep Dive

### What is WebSocket?

WebSocket is a **full-duplex, bidirectional** communication protocol that starts as an HTTP request
and then **upgrades** to a persistent TCP connection where both client and server can send messages
at any time.

### The WebSocket handshake — every header explained

```
CLIENT REQUEST (HTTP Upgrade):
GET /ws/chat HTTP/1.1
Host: api.example.com
Upgrade: websocket                              ← "I want to upgrade to WebSocket"
Connection: Upgrade                             ← "This is an upgrade request"
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==   ← Random base64 (anti-cache, not security)
Sec-WebSocket-Version: 13                       ← WebSocket protocol version
Sec-WebSocket-Protocol: chat, superchat        ← Subprotocols client supports
Sec-WebSocket-Extensions: permessage-deflate   ← Compression extension
Origin: https://example.com                     ← For CORS validation

SERVER RESPONSE (101 Switching Protocols):
HTTP/1.1 101 Switching Protocols
Upgrade: websocket                              ← Confirming upgrade
Connection: Upgrade                             ← Confirming upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=  ← Proves server understands WS
Sec-WebSocket-Protocol: chat                    ← Selected subprotocol
Sec-WebSocket-Extensions: permessage-deflate   ← Agreed extension

── After this, the TCP connection is now WebSocket ──
── HTTP is GONE. Only WebSocket frames flow. ──
```

### How Sec-WebSocket-Accept is calculated

```python
import base64
import hashlib

def compute_accept_key(client_key: str) -> str:
    """
    The server MUST concatenate the client's key with the magic GUID,
    SHA-1 hash it, and base64-encode the result. This proves the server
    understands the WebSocket protocol (not a regular HTTP server).
    """
    magic_guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = client_key + magic_guid
    sha1_hash = hashlib.sha1(combined.encode()).digest()
    return base64.b64encode(sha1_hash).decode()

# Example:
# Client sends: Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
# Server responds: Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### WebSocket frame format (the wire protocol)

After the handshake, data flows as **frames**:

```
 0               1               2               3
 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S| (4)   |A|     (7)     |          (16/64)              |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|    Extended payload length continued, if payload len == 127    |
+-------------------------------+-------------------------------+
|                Masking-key (0 or 4 bytes)                      |
+-------------------------------+-------------------------------+
|                        Payload Data                            |
|                     (extension data + application data)        |
+---------------------------------------------------------------+

FIN (1 bit):   1 = final frame of message, 0 = more fragments coming
Opcode (4 bits):
  0x0 = continuation frame
  0x1 = text frame (UTF-8)
  0x2 = binary frame
  0x8 = connection close
  0x9 = ping
  0xA = pong
MASK (1 bit):  1 = payload is masked (client→server MUST mask, server→client MUST NOT)
Payload length:
  0-125:   length is this value
  126:     following 2 bytes are the length (uint16)
  127:     following 8 bytes are the length (uint64)
```

### Why clients MUST mask frames

```
Problem: WebSocket traffic traverses HTTP proxies that may interpret raw bytes as
HTTP requests. An attacker could craft WebSocket payload that looks like a valid
HTTP request, poisoning proxy caches.

Solution: Client XORs every payload byte with a random 4-byte masking key.
Proxies can't accidentally interpret masked data as HTTP.

The mask is NOT encryption — server can trivially unmask. It's purely to prevent
proxy cache poisoning attacks discovered in 2010.
```

### FastAPI WebSocket — production-grade implementation

```python
import asyncio
import json
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from dataclasses import dataclass, field

app = FastAPI()


@dataclass
class WebSocketConnection:
    websocket: WebSocket
    client_id: str
    user_id: str
    connected_at: float = field(default_factory=time.time)
    rooms: set[str] = field(default_factory=set)
    last_pong: float = field(default_factory=time.time)
    message_count: int = 0


class ConnectionManager:
    """
    Production WebSocket connection manager.
    Handles rooms, heartbeats, graceful shutdown, and per-connection state.
    """

    def __init__(self):
        self.connections: dict[str, WebSocketConnection] = {}
        self.rooms: dict[str, set[str]] = {}  # room_name → set of client_ids
        self.user_connections: dict[str, set[str]] = {}  # user_id → set of client_ids
        self._ping_task: asyncio.Task | None = None

    async def start(self):
        self._ping_task = asyncio.create_task(self._ping_loop())

    async def stop(self):
        if self._ping_task:
            self._ping_task.cancel()
        for conn in list(self.connections.values()):
            await self._close_connection(conn, code=1001, reason="Server shutting down")

    async def connect(self, websocket: WebSocket, user_id: str) -> WebSocketConnection:
        await websocket.accept()

        client_id = str(uuid.uuid4())
        conn = WebSocketConnection(websocket=websocket, client_id=client_id, user_id=user_id)

        self.connections[client_id] = conn

        # Track user's connections (one user can have multiple tabs/devices)
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)

        return conn

    def disconnect(self, client_id: str):
        conn = self.connections.pop(client_id, None)
        if conn is None:
            return

        for room in conn.rooms:
            self.rooms.get(room, set()).discard(client_id)
            if not self.rooms.get(room):
                self.rooms.pop(room, None)

        user_conns = self.user_connections.get(conn.user_id, set())
        user_conns.discard(client_id)
        if not user_conns:
            self.user_connections.pop(conn.user_id, None)

    async def join_room(self, client_id: str, room: str):
        conn = self.connections.get(client_id)
        if conn is None:
            return
        conn.rooms.add(room)
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(client_id)

    async def leave_room(self, client_id: str, room: str):
        conn = self.connections.get(client_id)
        if conn is None:
            return
        conn.rooms.discard(room)
        self.rooms.get(room, set()).discard(client_id)

    async def send_to_client(self, client_id: str, message: dict):
        conn = self.connections.get(client_id)
        if conn is None:
            return
        try:
            await conn.websocket.send_json(message)
            conn.message_count += 1
        except Exception:
            self.disconnect(client_id)

    async def send_to_user(self, user_id: str, message: dict):
        """Send to ALL connections of a user (multiple devices/tabs)."""
        client_ids = self.user_connections.get(user_id, set())
        tasks = [self.send_to_client(cid, message) for cid in client_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_room(self, room: str, message: dict, exclude: str | None = None):
        client_ids = self.rooms.get(room, set())
        tasks = [self.send_to_client(cid, message) for cid in client_ids if cid != exclude]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _ping_loop(self):
        """
        Server-initiated ping every 30 seconds.
        If a client doesn't pong within 10 seconds, it's dead — disconnect it.
        """
        while True:
            await asyncio.sleep(30)
            now = time.time()
            dead_connections = []

            for client_id, conn in list(self.connections.items()):
                if now - conn.last_pong > 40:  # 30s interval + 10s grace
                    dead_connections.append(client_id)
                else:
                    try:
                        await conn.websocket.send_json({"type": "ping", "ts": now})
                    except Exception:
                        dead_connections.append(client_id)

            for client_id in dead_connections:
                await self._close_connection(self.connections[client_id], code=1001, reason="Ping timeout")
                self.disconnect(client_id)

    async def _close_connection(self, conn: WebSocketConnection, code: int, reason: str):
        try:
            await conn.websocket.close(code=code, reason=reason)
        except Exception:
            pass


manager = ConnectionManager()


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = Query(...)):
    # Authenticate before accepting
    user_id = await authenticate_websocket(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    conn = await manager.connect(websocket, user_id)
    await manager.join_room(conn.client_id, room_id)

    # Notify room that user joined
    await manager.broadcast_to_room(room_id, {
        "type": "user_joined",
        "user_id": user_id,
        "timestamp": time.time(),
    }, exclude=conn.client_id)

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            await handle_message(conn, room_id, message)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await conn.websocket.close(code=1011, reason=str(exc)[:120])
    finally:
        manager.disconnect(conn.client_id)
        await manager.broadcast_to_room(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": time.time(),
        })


async def handle_message(conn: WebSocketConnection, room_id: str, message: dict):
    """Route incoming messages by type."""
    msg_type = message.get("type")

    if msg_type == "chat":
        await manager.broadcast_to_room(room_id, {
            "type": "chat",
            "user_id": conn.user_id,
            "content": message["content"],
            "timestamp": time.time(),
            "message_id": str(uuid.uuid4()),
        }, exclude=conn.client_id)

    elif msg_type == "typing":
        await manager.broadcast_to_room(room_id, {
            "type": "typing",
            "user_id": conn.user_id,
        }, exclude=conn.client_id)

    elif msg_type == "pong":
        conn.last_pong = time.time()


async def authenticate_websocket(token: str) -> str | None:
    """Validate JWT/session token. Returns user_id or None."""
    # jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return "user_from_token"  # placeholder
```

### WebSocket close codes (you MUST know these)

```
1000  Normal Closure         Both sides agreed to close
1001  Going Away             Server shutting down, client navigating away
1002  Protocol Error         Invalid frame received
1003  Unsupported Data       Received data type that can't be handled
1006  Abnormal Closure       Connection lost without close frame (TCP died)
1007  Invalid Payload        Text frame with invalid UTF-8
1008  Policy Violation       Auth failed, message too large, rate limit
1009  Message Too Big        Message exceeds server's max size
1011  Unexpected Condition   Server error (like HTTP 500)
1012  Service Restart        Server restarting, client should reconnect
1013  Try Again Later        Server overloaded, client should back off
1014  Bad Gateway            Upstream server returned invalid response

4000-4999: Application-specific codes (define your own)
```

---

## 4. SSE vs WebSocket — When to Use What

### Decision matrix

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SSE                    │         WebSocket             │
├──────────────────────────────────────────┼───────────────────────────────┤
│ Server → Client only                     │ Bidirectional                 │
│ Automatic reconnection (browser built-in)│ Manual reconnection logic     │
│ Works with HTTP/2 multiplexing           │ Separate TCP per connection   │
│ Text only (UTF-8)                        │ Text + Binary frames          │
│ Simple (just HTTP with special headers)  │ Complex (upgrade + framing)   │
│ Works through ALL HTTP proxies           │ Some proxies block upgrades   │
│ Last-Event-ID for gap recovery (free!)   │ Must implement gap recovery   │
│ Standard HTTP auth (cookies, headers)    │ Auth only during handshake    │
│ Cacheable/loggable by HTTP tools         │ Opaque to HTTP infrastructure │
├──────────────────────────────────────────┼───────────────────────────────┤
│ USE FOR:                                 │ USE FOR:                      │
│ • News feeds                             │ • Chat / messaging            │
│ • Stock tickers                          │ • Multiplayer games           │
│ • Live dashboards                        │ • Collaborative editing       │
│ • Notifications                          │ • Video/audio signaling       │
│ • CI/CD build logs                       │ • Interactive terminals       │
│ • Progress bars                          │ • Bidirectional streaming     │
└──────────────────────────────────────────┴───────────────────────────────┘
```

### What Facebook/Google actually use

| Company | Feature | Technology | Why |
|---------|---------|-----------|-----|
| Facebook | Chat (Messenger) | MQTT over WebSocket | Bidirectional, low overhead, mobile-friendly |
| Facebook | News Feed updates | Long polling → SSE | Unidirectional, simple |
| Google | Gmail push | WebSocket (via Channel API) | Need to send read receipts back |
| Google | Google Docs | WebSocket + OT/CRDT | Real-time collaborative editing |
| Slack | Messages | WebSocket | Bidirectional messaging |
| Discord | Voice + Text | WebSocket + WebRTC | Chat + real-time audio |
| Twitter/X | Live feed | SSE | Unidirectional timeline updates |
| Uber | Driver location | WebSocket | Bidirectional location + dispatch |

---

## 5. The Connection Lifecycle — Every Byte Explained

### WebSocket full lifecycle

```
Time →

CLIENT                                      SERVER
  │                                           │
  │──── TCP SYN ──────────────────────────────→│  1. TCP handshake begins
  │←─── TCP SYN-ACK ─────────────────────────│
  │──── TCP ACK ──────────────────────────────→│  2. TCP established (~1 RTT)
  │                                           │
  │──── TLS ClientHello ──────────────────────→│  3. TLS handshake (if wss://)
  │←─── TLS ServerHello + Cert ───────────────│     (~1-2 RTT for TLS 1.3)
  │──── TLS Finished ────────────────────────→│
  │←─── TLS Finished ────────────────────────│  4. TLS established
  │                                           │
  │──── HTTP GET /ws (Upgrade headers) ───────→│  5. WebSocket handshake request
  │←─── HTTP 101 Switching Protocols ────────│  6. Server agrees to upgrade
  │                                           │
  │════════ WebSocket tunnel open ═════════════│  7. Full-duplex communication
  │                                           │
  │──── [MASKED] Text Frame: "hello" ────────→│  8. Client sends (masked)
  │←─── Text Frame: "hi back" ───────────────│  9. Server sends (unmasked)
  │                                           │
  │←─── Ping Frame ──────────────────────────│  10. Server healthcheck
  │──── Pong Frame ──────────────────────────→│  11. Client responds
  │                                           │
  │──── Close Frame (code=1000) ─────────────→│  12. Client initiates close
  │←─── Close Frame (code=1000) ─────────────│  13. Server confirms
  │                                           │
  │──── TCP FIN ─────────────────────────────→│  14. TCP teardown
  │←─── TCP FIN-ACK ────────────────────────│
  │──── TCP ACK ─────────────────────────────→│  15. Connection fully closed

Total setup time: ~3-5 RTTs (TCP + TLS + HTTP upgrade)
After setup: Messages flow with just 2-14 bytes of framing overhead
(vs. ~800+ bytes of HTTP headers per request/response)
```

### SSE full lifecycle

```
CLIENT                                      SERVER
  │                                           │
  │──── TCP + TLS (same as above) ────────────→│  1-4. Same TCP+TLS setup
  │                                           │
  │──── GET /events HTTP/1.1                  →│  5. Standard HTTP request
  │     Accept: text/event-stream             │
  │     Last-Event-ID: 42                     │
  │                                           │
  │←─── HTTP/1.1 200 OK                      │  6. Server starts response
  │     Content-Type: text/event-stream       │     (never "finishes" it)
  │     Transfer-Encoding: chunked            │
  │                                           │
  │←─── data: {"msg": "hello"}\n\n ──────────│  7. Events flow server→client
  │←─── data: {"msg": "world"}\n\n ──────────│
  │←─── : heartbeat\n\n ─────────────────────│  8. Keep-alive comment
  │                                           │
  │──── (wants to send data) ─────────────────│  9. Client must open SEPARATE
  │──── POST /messages {"text":"hi"} ────────→│     HTTP request to send!
  │←─── 201 Created ────────────────────────│
  │                                           │
  │←─── id: 43\ndata: {"msg":"hi"}\n\n ─────│  10. Server pushes on SSE stream
  │                                           │
  │  ✕  (network drops / tab closed)          │  11. Connection lost
  │                                           │
  │──── GET /events                           →│  12. Browser AUTO-reconnects!
  │     Last-Event-ID: 43   ← resumes here!  │      (built into EventSource)
```

---

## 6. Scaling Challenge — Why Single Server Breaks

### The fundamental problem

```
Scenario: User A (connected to Server 1) sends message to User B (connected to Server 2)

┌─────────┐         ┌──────────┐
│ User A  │─────ws──│ Server 1 │  ← User A's WS connection is HERE
└─────────┘         └──────────┘
                         ???
┌─────────┐         ┌──────────┐
│ User B  │─────ws──│ Server 2 │  ← User B's WS connection is HERE
└─────────┘         └──────────┘

Problem: Server 1 received User A's message, but User B's WebSocket
lives on Server 2. How does the message get to User B?

Single-server solutions DON'T WORK:
  ❌ Broadcasting to all local connections (User B isn't local!)
  ❌ Storing in DB and waiting for User B to poll (defeats real-time!)
  ❌ Sticky sessions (what if User B is chatting with User C on Server 3?)
```

### Connection distribution at scale

```
Facebook Messenger Architecture (simplified):

                    ┌─────────────────────────────┐
                    │        Load Balancer         │
                    │    (Layer 4 / Layer 7)       │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
              ┌────────────┤      │      ├────────────┐
              │            │      │      │            │
        ┌─────▼──┐   ┌────▼───┐  │  ┌───▼────┐  ┌───▼────┐
        │ WS     │   │ WS     │  │  │ WS     │  │ WS     │
        │ Server │   │ Server │  │  │ Server │  │ Server │
        │ 1      │   │ 2      │  │  │ 3      │  │ N      │
        │ 250K   │   │ 250K   │  │  │ 250K   │  │ 250K   │
        │ conns  │   │ conns  │  │  │ conns  │  │ conns  │
        └───┬────┘   └───┬────┘  │  └───┬────┘  └───┬────┘
            │             │       │      │            │
            └─────────────┴───────┼──────┴────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    Message Bus / Pub-Sub    │
                    │  (Redis Cluster / Kafka /   │
                    │   NATS / Custom)            │
                    └────────────────────────────┘

Each WS Server: ~250K concurrent connections
Total (1000 servers): ~250M concurrent connections
Message Bus: Routes messages between servers
```

---

## 7. Pub/Sub Architecture — The Fan-Out Pattern

### Why pub/sub solves the multi-server problem

```
The solution: Every WS server SUBSCRIBES to a message bus for the users it's serving.
When Server 1 gets a message for User B, it PUBLISHES to the bus.
Server 2 (which has User B) RECEIVES the published message and forwards to User B.

┌──────────┐    publish     ┌───────────────┐    deliver    ┌──────────┐
│ Server 1 │ ──────────────→│  Redis Pub/Sub │──────────────→│ Server 2 │
│ (has A)  │                │  Channel:      │               │ (has B)  │
│           │                │  "user:B"     │               │          │──ws──→ User B
└──────────┘                └───────────────┘               └──────────┘
```

### Redis Pub/Sub implementation

```python
import asyncio
import json
import redis.asyncio as redis

class RedisPubSubBridge:
    """
    Bridges local WebSocket connections with Redis Pub/Sub for cross-server messaging.
    Each server instance subscribes to channels for its connected users.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_pub: redis.Redis | None = None      # For publishing
        self.redis_sub: redis.Redis | None = None      # For subscribing
        self.pubsub: redis.client.PubSub | None = None
        self.subscriptions: dict[str, set[str]] = {}   # channel → set of client_ids
        self._listener_task: asyncio.Task | None = None

    async def start(self):
        self.redis_pub = redis.from_url(self.redis_url, decode_responses=True)
        self.redis_sub = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub = self.redis_sub.pubsub()
        self._listener_task = asyncio.create_task(self._listen())

    async def stop(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_pub:
            await self.redis_pub.close()
        if self.redis_sub:
            await self.redis_sub.close()

    async def subscribe_user(self, user_id: str, client_id: str):
        """Called when a user connects to THIS server."""
        channel = f"user:{user_id}"
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
            await self.pubsub.subscribe(channel)
        self.subscriptions[channel].add(client_id)

    async def unsubscribe_user(self, user_id: str, client_id: str):
        """Called when a user disconnects from THIS server."""
        channel = f"user:{user_id}"
        clients = self.subscriptions.get(channel, set())
        clients.discard(client_id)
        if not clients:
            self.subscriptions.pop(channel, None)
            await self.pubsub.unsubscribe(channel)

    async def subscribe_room(self, room_id: str, client_id: str):
        """Subscribe to room-level messages."""
        channel = f"room:{room_id}"
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
            await self.pubsub.subscribe(channel)
        self.subscriptions[channel].add(client_id)

    async def publish_to_user(self, user_id: str, message: dict):
        """Publish a message that will reach the user wherever they're connected."""
        channel = f"user:{user_id}"
        await self.redis_pub.publish(channel, json.dumps(message))

    async def publish_to_room(self, room_id: str, message: dict):
        """Publish a message to all users in a room across all servers."""
        channel = f"room:{room_id}"
        await self.redis_pub.publish(channel, json.dumps(message))

    async def _listen(self):
        """Background task: receive messages from Redis and forward to local WebSockets."""
        while True:
            try:
                async for raw_message in self.pubsub.listen():
                    if raw_message["type"] != "message":
                        continue

                    channel = raw_message["channel"]
                    data = json.loads(raw_message["data"])

                    # Forward to all local clients subscribed to this channel
                    client_ids = self.subscriptions.get(channel, set())
                    for client_id in list(client_ids):
                        await manager.send_to_client(client_id, data)
            except asyncio.CancelledError:
                break
            except redis.ConnectionError:
                await asyncio.sleep(1)  # Reconnect after brief delay
```

### Redis Pub/Sub limitations at extreme scale

```
Problem: Redis Pub/Sub is FIRE-AND-FORGET.
- If no subscriber is listening → message is LOST
- If Redis crashes → all in-flight messages LOST
- No message persistence, no replay, no acknowledgment
- Single Redis node: ~100K messages/second throughput

For Facebook/Google scale, you need something stronger.
```

### Redis Streams — Persistent pub/sub with replay

```python
import redis.asyncio as redis
import json

class RedisStreamBridge:
    """
    Uses Redis Streams instead of Pub/Sub for guaranteed delivery.
    Streams persist messages and support consumer groups for fan-out.
    """

    def __init__(self, redis_url: str, server_id: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.server_id = server_id  # Unique ID for this WS server instance

    async def publish_message(self, room_id: str, message: dict):
        """Add message to room's stream with automatic ID (timestamp-based)."""
        stream_key = f"stream:room:{room_id}"
        entry_id = await self.redis.xadd(
            stream_key,
            {"payload": json.dumps(message)},
            maxlen=10000,  # Keep last 10K messages (auto-trim older ones)
        )
        return entry_id  # e.g., "1691234567890-0" (timestamp-sequence)

    async def replay_from(self, room_id: str, last_id: str) -> list[dict]:
        """
        Replay all messages after last_id — called when client reconnects.
        This is what makes streams superior to pub/sub for gap recovery.
        """
        stream_key = f"stream:room:{room_id}"
        entries = await self.redis.xrange(stream_key, min=f"({last_id}", count=1000)
        return [
            {"id": entry_id, **json.loads(fields["payload"])}
            for entry_id, fields in entries
        ]

    async def create_consumer_group(self, room_id: str):
        """
        Consumer groups allow multiple WS servers to process the same stream
        WITHOUT duplicating messages. Each message goes to exactly ONE consumer
        in the group (for processing), while ALL consumers get ALL messages
        (for broadcasting to local connections).

        For fan-out to all servers: each server creates its OWN consumer group.
        """
        stream_key = f"stream:room:{room_id}"
        group_name = f"ws-server-{self.server_id}"
        try:
            await self.redis.xgroup_create(stream_key, group_name, id="$", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def consume_messages(self, room_id: str):
        """
        Continuously read new messages from the stream.
        Each server has its own consumer group so ALL servers get ALL messages.
        """
        stream_key = f"stream:room:{room_id}"
        group_name = f"ws-server-{self.server_id}"
        consumer_name = f"consumer-{self.server_id}"

        while True:
            entries = await self.redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_key: ">"},  # ">" means only new messages
                count=100,
                block=5000,  # Block up to 5 seconds waiting for messages
            )

            for stream, messages in entries:
                for msg_id, fields in messages:
                    data = json.loads(fields["payload"])
                    # Forward to all local WebSocket connections in this room
                    await manager.broadcast_to_room(room_id, data)
                    # Acknowledge processing
                    await self.redis.xack(stream_key, group_name, msg_id)
```

### Kafka — The nuclear option for extreme scale

```python
# When to use Kafka over Redis:
# - > 1M messages/second sustained throughput
# - Need multi-day message retention (replay entire conversation history)
# - Need exactly-once semantics
# - Multi-datacenter replication
# - Need message ordering guarantees within a partition
#
# Facebook uses a Kafka-like system for Messenger's backend pipeline.

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json

class KafkaMessageBridge:
    """
    Kafka-backed message routing for extreme scale.

    Topic design:
      - "chat.messages" partitioned by room_id → ordered per room
      - "presence.updates" → user online/offline events
      - "typing.indicators" → ephemeral, can lose some

    Partition strategy:
      - Partition by room_id → all messages for a room go to same partition
      - This guarantees ordering within a room (Kafka guarantee: ordered within partition)
    """

    def __init__(self, bootstrap_servers: str, server_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.server_id = server_id
        self.producer: AIOKafkaProducer | None = None
        self.consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode(),
            acks="all",                # Wait for all replicas to acknowledge
            enable_idempotence=True,   # Exactly-once producer semantics
            compression_type="lz4",    # Compress messages (40-60% reduction)
            linger_ms=5,                # Batch messages for 5ms (throughput vs latency)
            batch_size=65536,           # 64KB batches
        )
        await self.producer.start()

        self.consumer = AIOKafkaConsumer(
            "chat.messages",
            bootstrap_servers=self.bootstrap_servers,
            group_id=f"ws-server-{self.server_id}",
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="latest",
            enable_auto_commit=False,  # Manual commit for exactly-once
        )
        await self.consumer.start()

    async def publish_message(self, room_id: str, message: dict):
        """
        Publish with room_id as key → all messages for same room go to same partition
        → ordering guaranteed within a room.
        """
        await self.producer.send_and_wait(topic="chat.messages", key=room_id, value=message)

    async def consume_loop(self):
        """Process messages from Kafka and forward to local WebSocket connections."""
        async for msg in self.consumer:
            room_id = msg.key.decode()
            data = msg.value

            # Only forward if we have local connections for this room
            if room_id in manager.rooms:
                await manager.broadcast_to_room(room_id, data)

            # Manual commit after successful delivery
            await self.consumer.commit()
```

### NATS — Lightweight alternative for microservices

```python
# NATS is lighter than Kafka, faster than Redis Pub/Sub, with optional persistence (JetStream).
# Good middle ground for most real-time applications.
#
# Comparison:
#   Redis Pub/Sub:  ~100K msg/s, no persistence, simplest
#   NATS Core:      ~10M msg/s, no persistence, lightweight
#   NATS JetStream: ~1M msg/s, persistent, replay, exactly-once
#   Kafka:          ~1M msg/s, persistent, multi-DC, heaviest

import nats
from nats.js.api import StreamConfig

class NATSMessageBridge:
    def __init__(self, nats_url: str, server_id: str):
        self.nats_url = nats_url
        self.server_id = server_id
        self.nc = None
        self.js = None  # JetStream context

    async def start(self):
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()

        # Create stream for chat messages (if not exists)
        await self.js.add_stream(
            StreamConfig(
                name="CHAT",
                subjects=["chat.>"],            # Wildcard: chat.room1, chat.room2, etc.
                retention="limits",
                max_msgs_per_subject=10000,     # Keep 10K messages per room
                max_age=86400 * 7,              # 7 days retention
                storage="file",
                num_replicas=3,
            )
        )

    async def publish(self, room_id: str, message: dict):
        await self.js.publish(f"chat.{room_id}", json.dumps(message).encode())

    async def subscribe_room(self, room_id: str):
        """
        Durable consumer: NATS tracks last delivered message.
        On reconnect, picks up where it left off (gap recovery for free).
        """
        consumer = await self.js.subscribe(
            f"chat.{room_id}",
            durable=f"ws-{self.server_id}-{room_id}",
            deliver_policy="new",
        )

        async for msg in consumer.messages:
            data = json.loads(msg.data.decode())
            if room_id in manager.rooms:
                await manager.broadcast_to_room(room_id, data)
            await msg.ack()
```

---

## 8. Load Balancers for Persistent Connections

### The load balancer challenge

```
Regular HTTP: Request → LB picks server → Response → Done (stateless)
WebSocket:    Upgrade → LB picks server → Connection stays open for HOURS
SSE:          GET → LB picks server → Response streams for HOURS

Problems:
1. LB can't redistribute connections (they're "stuck" on one server)
2. New servers get no connections; old servers are overloaded
3. Health checks: connection is open but server might be degraded
4. Upgrades: how to drain connections during deploy?
```

### Layer 4 vs Layer 7 load balancing

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 4 (Transport/TCP)                                              │
├─────────────────────────────────────────────────────────────────────┤
│ • Operates on TCP connections (IP + port)                           │
│ • Cannot inspect HTTP headers, URL paths, or WebSocket frames       │
│ • Simply forwards TCP bytes between client and backend              │
│ • Lower latency (no parsing), higher throughput                     │
│ • Cannot route based on URL (/ws/room1 vs /ws/room2)               │
│ • Cannot insert headers (X-Real-IP, etc.)                           │
│ • Examples: AWS NLB, HAProxy (TCP mode), Linux IPVS                 │
│ • Best for: Raw throughput, when all backends are equivalent         │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 7 (Application/HTTP)                                           │
├─────────────────────────────────────────────────────────────────────┤
│ • Understands HTTP: can inspect headers, URL, cookies               │
│ • CAN handle WebSocket upgrade (passes through after upgrade)       │
│ • Can route /ws/chat → chat-servers, /ws/game → game-servers       │
│ • Can add headers (X-Forwarded-For, X-Request-ID)                   │
│ • Can terminate TLS (offload crypto from backends)                  │
│ • Higher latency (must parse HTTP), but more flexible                │
│ • Examples: AWS ALB, Nginx, Envoy, HAProxy (HTTP mode), Traefik    │
│ • Best for: Path-based routing, TLS termination, header injection   │
└─────────────────────────────────────────────────────────────────────┘
```

### Load balancer comparison for WebSocket/SSE

| Load Balancer | WebSocket | SSE | Best For | Max Concurrent | Notes |
|--------------|-----------|-----|----------|----------------|-------|
| **Nginx** | ✅ | ✅ | General purpose | ~500K per instance | Needs `proxy_buffering off` for SSE |
| **HAProxy** | ✅ | ✅ | High performance | ~1M+ per instance | Best connection handling |
| **Envoy** | ✅ | ✅ | Service mesh (Istio) | ~500K per instance | gRPC + WS + HTTP/2 native |
| **AWS ALB** | ✅ | ✅ | AWS native | Unlimited (managed) | 4000 targets, idle timeout 4000s |
| **AWS NLB** | ✅ | ✅ | Raw TCP, high throughput | Unlimited (managed) | Layer 4 only, no path routing |
| **Traefik** | ✅ | ✅ | Kubernetes ingress | ~200K per instance | Auto-discovery, less raw perf |
| **Cloudflare** | ✅ | ✅ | Edge/CDN + WS | Unlimited (managed) | 100s timeout (configurable) |

### Nginx configuration for WebSocket + SSE

```nginx
# /etc/nginx/conf.d/realtime.conf

# Connection upgrade map (needed for WebSocket)
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream websocket_backends {
    # Use least_conn for WebSocket: sends new connections to the server
    # with fewest active connections (important because WS connections are long-lived)
    least_conn;

    server ws-server-1:8000;
    server ws-server-2:8000;
    server ws-server-3:8000;

    # Passive health checks: mark server as down after 3 failures
    server ws-server-4:8000 max_fails=3 fail_timeout=30s;

    # Keep TCP connections to backends open (connection pooling)
    keepalive 64;
}

upstream sse_backends {
    least_conn;
    server sse-server-1:8000;
    server sse-server-2:8000;
}

server {
    listen 443 ssl http2;  # HTTP/2 for SSE multiplexing
    server_name realtime.example.com;

    ssl_certificate     /etc/ssl/certs/realtime.crt;
    ssl_certificate_key /etc/ssl/private/realtime.key;

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://websocket_backends;
        proxy_http_version 1.1;

        # These two headers trigger the WebSocket upgrade
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Pass real client IP to backend
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;

        # CRITICAL: Timeouts for WebSocket
        # proxy_read_timeout: how long Nginx waits for data FROM backend
        # Set high because WebSocket connections can be idle for minutes
        proxy_read_timeout 3600s;  # 1 hour (reset on each frame)
        proxy_send_timeout 3600s;

        # Don't buffer WebSocket frames
        proxy_buffering off;

        # TCP optimizations
        proxy_socket_keepalive on;
        tcp_nodelay on;  # Disable Nagle's algorithm (low latency)
    }

    # SSE endpoint
    location /events/ {
        proxy_pass http://sse_backends;
        proxy_http_version 1.1;

        # CRITICAL for SSE: disable ALL buffering
        proxy_buffering off;            # Nginx internal buffering
        proxy_cache off;                # No caching of stream
        proxy_set_header Connection ''; # Remove hop-by-hop Connection header

        # SSE-specific headers
        proxy_set_header X-Accel-Buffering no;

        # Chunked transfer (SSE uses this)
        chunked_transfer_encoding on;

        # Long timeout (SSE connections live for hours)
        proxy_read_timeout 86400s;  # 24 hours

        # Pass client info
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

### HAProxy configuration — optimal for high connection counts

```
# /etc/haproxy/haproxy.cfg

global
    maxconn 1000000          # 1M max connections (tune OS limits too)
    nbthread 8               # Match CPU cores

    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    tune.ssl.default-dh-param 2048

    tune.bufsize 16384       # 16KB buffer per connection
    tune.maxrewrite 1024

defaults
    mode http
    timeout connect 5s       # Time to establish connection to backend
    timeout client 3600s     # Client idle timeout (1 hour for WS/SSE)
    timeout server 3600s     # Backend idle timeout
    timeout tunnel 86400s    # WebSocket tunnel timeout (24 hours!)
    timeout http-keep-alive 30s

    option httplog
    option dontlognull
    option http-server-close

# WebSocket frontend
frontend ws_frontend
    bind *:443 ssl crt /etc/ssl/realtime.pem alpn h2,http/1.1

    # Route WebSocket upgrades to WS backend
    acl is_websocket hdr(Upgrade) -i websocket
    acl is_ws_path path_beg /ws/

    use_backend ws_servers if is_websocket is_ws_path

    # Route SSE to SSE backend
    acl is_sse_path path_beg /events/
    acl accepts_sse hdr(Accept) -i text/event-stream

    use_backend sse_servers if is_sse_path accepts_sse

    # Everything else to regular HTTP servers
    default_backend http_servers

# WebSocket backend
backend ws_servers
    balance leastconn        # Best for long-lived connections

    # Health check: actual WebSocket handshake test
    option httpchk GET /health HTTP/1.1\r\nHost:\ realtime.example.com
    http-check expect status 200

    server ws1 10.0.1.1:8000 check inter 5s fall 3 rise 2 maxconn 250000
    server ws2 10.0.1.2:8000 check inter 5s fall 3 rise 2 maxconn 250000
    server ws3 10.0.1.3:8000 check inter 5s fall 3 rise 2 maxconn 250000
    server ws4 10.0.1.4:8000 check inter 5s fall 3 rise 2 maxconn 250000

# SSE backend
backend sse_servers
    balance leastconn

    # No buffering for SSE
    option httpchk GET /health
    http-check expect status 200

    # Long server timeout for SSE streams
    timeout server 86400s
    timeout tunnel 86400s

    server sse1 10.0.2.1:8000 check inter 5s fall 3 rise 2 maxconn 200000
    server sse2 10.0.2.2:8000 check inter 5s fall 3 rise 2 maxconn 200000
```

### Envoy configuration — for Kubernetes/service mesh

```yaml
# envoy.yaml - Modern choice for Kubernetes + gRPC + WebSocket
static_resources:
  listeners:
    - name: realtime_listener
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8443
      filter_chains:
        - transport_socket:
            name: envoy.transport_sockets.tls
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
              common_tls_context:
                tls_certificates:
                  - certificate_chain: { filename: "/etc/ssl/cert.pem" }
                    private_key: { filename: "/etc/ssl/key.pem" }
          filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: realtime
                # CRITICAL: Allow WebSocket upgrades
                upgrade_configs:
                  - upgrade_type: websocket
                    enabled: true
                codec_type: AUTO
                route_config:
                  virtual_hosts:
                    - name: realtime
                      domains: ["realtime.example.com"]
                      routes:
                        - match:
                            prefix: "/ws/"
                          route:
                            cluster: ws_cluster
                            timeout: 0s  # No timeout for WebSocket
                            idle_timeout: 3600s
                        - match:
                            prefix: "/events/"
                          route:
                            cluster: sse_cluster
                            timeout: 0s
                            idle_timeout: 86400s
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: ws_cluster
      type: EDS  # Endpoint Discovery Service (auto-discovers pods in K8s)
      lb_policy: LEAST_REQUEST
      circuit_breakers:
        thresholds:
          - max_connections: 250000
            max_pending_requests: 1000
            max_retries: 3
      health_checks:
        - timeout: 5s
          interval: 10s
          unhealthy_threshold: 3
          healthy_threshold: 2
          http_health_check:
            path: /health

    - name: sse_cluster
      type: EDS
      lb_policy: LEAST_REQUEST
      circuit_breakers:
        thresholds:
          - max_connections: 200000
```

### Which load balancer to choose? (Decision flowchart)

```
START
  │
  ├── Are you on AWS?
  │     ├── YES: Need path-based routing?
  │     │         ├── YES → AWS ALB (managed, auto-scales, supports WS+SSE)
  │     │         └── NO  → AWS NLB (Layer 4, higher throughput, lower latency)
  │     └── NO: Continue ↓
  │
  ├── Running Kubernetes + service mesh?
  │     └── YES → Envoy (via Istio or standalone) — native WS, gRPC, HTTP/2
  │
  ├── Need maximum raw connections (>500K per LB)?
  │     └── YES → HAProxy (battle-tested, lowest memory per connection)
  │
  ├── Need simple setup + widely understood config?
  │     └── YES → Nginx (most documented, large ecosystem)
  │
  ├── Need automatic service discovery + Let's Encrypt?
  │     └── YES → Traefik (best for Docker/K8s auto-discovery)
  │
  └── Need edge/CDN + DDoS protection + WS?
        └── YES → Cloudflare (global edge, managed)

For Facebook/Google scale:
  → Custom L4 load balancer + Envoy as sidecar
  → Facebook uses "Proxygen" (custom C++ HTTP framework)
  → Google uses custom L7 LB built on Maglev (software L4) + Envoy
```

---

## 9. Connection Management at Scale

### OS-level tuning for millions of connections

```bash
# /etc/sysctl.conf — Linux kernel tuning for high connection counts

# Maximum file descriptors (each connection = 1 fd)
fs.file-max = 2097152                    # 2M system-wide
fs.nr_open = 2097152                     # 2M per-process max

# TCP memory (min, pressure, max) in pages (4KB each)
net.ipv4.tcp_mem = 786432 1048576 1572864   # ~3GB-6GB for TCP buffers
net.ipv4.tcp_rmem = 4096 87380 16777216     # Per-socket read buffer
net.ipv4.tcp_wmem = 4096 65536 16777216     # Per-socket write buffer

# Allow more connections in TIME_WAIT (after close)
net.ipv4.tcp_tw_reuse = 1               # Reuse TIME_WAIT sockets
net.ipv4.tcp_fin_timeout = 15           # Reduce FIN-WAIT-2 timeout

# Increase connection tracking
net.netfilter.nf_conntrack_max = 2097152
net.ipv4.tcp_max_syn_backlog = 65536    # SYN queue size
net.core.somaxconn = 65536              # Listen backlog

# Ephemeral port range (for outbound connections from LB to backends)
net.ipv4.ip_local_port_range = 1024 65535  # ~64K ports

# Keep-alive settings (detect dead connections faster)
net.ipv4.tcp_keepalive_time = 60        # Start probes after 60s idle
net.ipv4.tcp_keepalive_intvl = 10       # Probe every 10s
net.ipv4.tcp_keepalive_probes = 6       # Give up after 6 probes (60s total)

# Network queue sizes
net.core.netdev_max_backlog = 65536
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
```

```bash
# /etc/security/limits.conf — Per-process limits
*    soft    nofile    1048576
*    hard    nofile    1048576
```

### Memory budget per connection

```
Breakdown for 1M WebSocket connections:

Kernel TCP state:        ~3.5 KB × 1M = 3.5 GB
TLS session state:       ~5 KB × 1M   = 5.0 GB  (if TLS termination at app)
Application state:       ~1-10 KB × 1M = 1-10 GB (user info, subscriptions)
Read/Write buffers:      ~8 KB × 1M   = 8.0 GB  (can be reduced)
─────────────────────────────────────────────────
Total per server:        ~18-27 GB for 1M connections

Facebook approach: TLS termination at L4 LB (not app servers)
  → Saves 5 GB per server
  → App servers only see plain TCP
```

### Connection draining during deploys

```python
import asyncio
import signal
import time

class GracefulShutdown:
    """
    During deployment, we need to:
    1. Stop accepting NEW connections
    2. Let existing connections finish naturally (or timeout)
    3. Send "reconnect" signal to clients
    4. Wait for all connections to drain
    5. Then exit
    """

    def __init__(self, manager, drain_timeout: int = 30):
        self.manager = manager
        self.drain_timeout = drain_timeout
        self.is_draining = False

    def setup_signals(self):
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        asyncio.create_task(self.drain())

    async def drain(self):
        """Gracefully drain all connections."""
        self.is_draining = True

        # 1. Tell load balancer we're unhealthy (health endpoint now returns 503)

        # 2. Send "please reconnect" to all connected clients
        # Clients will reconnect to a DIFFERENT (new) server
        for conn in list(self.manager.connections.values()):
            try:
                await conn.websocket.send_json({
                    "type": "system",
                    "action": "reconnect",
                    "reason": "server_restart",
                    "delay_ms": 1000,  # Stagger reconnections
                })
                # Close with 1012 (Service Restart) — tells client to reconnect
                await conn.websocket.close(code=1012, reason="Server restarting")
            except Exception:
                pass

        # 3. Wait for connections to drain (with timeout)
        start = time.time()
        while self.manager.connections and (time.time() - start) < self.drain_timeout:
            await asyncio.sleep(0.5)

        # 4. Force-close any remaining connections
        for conn in list(self.manager.connections.values()):
            try:
                await conn.websocket.close(code=1001, reason="Server shutdown")
            except Exception:
                pass
```

### Horizontal scaling strategy

```
Tier 1: Single server (0-50K connections)
  └── Just run your app. No pub/sub needed.

Tier 2: Multiple servers with Redis (50K-500K connections)
  └── Redis Pub/Sub for cross-server messaging
  └── Any L7 load balancer (Nginx, ALB)
  └── 2-5 app servers

Tier 3: High scale (500K-5M connections)
  └── Redis Cluster or NATS JetStream
  └── HAProxy or dedicated L4 LB
  └── 10-50 app servers
  └── Connection registry (know which server has which user)

Tier 4: Extreme scale (5M-100M+ connections)
  └── Kafka/custom message bus
  └── Multi-layer LB (L4 → L7)
  └── 100-1000+ app servers
  └── Sharded connection routing
  └── Multi-datacenter replication
  └── Custom protocols (Facebook's MQTT, Discord's Elixir)
```

---

## 10. Presence Systems (Online/Offline/Typing)

### The presence problem at scale

```
"Who is online right now?" sounds simple but is one of the hardest problems at scale.

Challenge 1: A user might have 5 devices connected simultaneously
Challenge 2: "Offline" detection requires ABSENCE of signal (hard to distribute)
Challenge 3: At 500M users, even 1% online = 5M presence updates/second
Challenge 4: Network blips ≠ user going offline (need debouncing)
Challenge 5: Must propagate to all friends (fan-out of 500+ for average user)
```

### Facebook's presence architecture (simplified)

```
┌────────────────────────────────────────────────────────────────────┐
│                        PRESENCE SYSTEM                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐     ┌─────────────┐     ┌──────────────────┐         │
│  │  WS     │────→│  Presence   │────→│  Presence        │         │
│  │  Server │     │  Aggregator │     │  Storage         │         │
│  │         │←────│  (per-DC)   │←────│  (Redis Cluster) │         │
│  └─────────┘     └──────┬──────┘     └──────────────────┘         │
│                          │                                          │
│                          ▼                                          │
│                  ┌───────────────┐                                  │
│                  │  Fan-out      │  "Alice went online"             │
│                  │  Service      │  → notify all Alice's friends    │
│                  └───────────────┘                                  │
│                                                                     │
│  Key Design Decisions:                                              │
│  • Heartbeat-based (not connection-based)                          │
│  • 30-second heartbeat interval                                     │
│  • "Online" = received heartbeat in last 60 seconds                │
│  • Aggregation: merge multiple devices into single status           │
│  • Lazy fan-out: only notify friends who are ALSO online           │
│  • Suppress flapping: wait 30s before declaring "offline"          │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Production presence implementation

```python
import asyncio
import time
import redis.asyncio as redis
from enum import Enum

class PresenceStatus(str, Enum):
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"

class PresenceService:
    """
    Distributed presence tracking using Redis sorted sets.

    Strategy:
    - Each device sends heartbeats every 30s
    - Sorted set score = last heartbeat timestamp
    - "Online" = heartbeat within 60s
    - ZRANGEBYSCORE to find all currently online users
    - Offline detection: periodic sweep of expired heartbeats
    """

    HEARTBEAT_INTERVAL = 30    # Seconds between heartbeats
    ONLINE_THRESHOLD = 60      # Seconds before considering offline
    OFFLINE_GRACE = 30         # Extra wait before declaring offline (debounce)

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._sweep_task: asyncio.Task | None = None

    async def start(self):
        self._sweep_task = asyncio.create_task(self._offline_sweep())

    async def heartbeat(self, user_id: str, device_id: str):
        """Called every 30 seconds by each connected device."""
        now = time.time()
        pipe = self.redis.pipeline()

        pipe.zadd(f"presence:devices:{user_id}", {device_id: now})
        pipe.zadd("presence:online", {user_id: now})
        pipe.expire(f"presence:devices:{user_id}", self.ONLINE_THRESHOLD * 2)

        await pipe.execute()

    async def get_status(self, user_id: str) -> PresenceStatus:
        """Get current presence status for a user."""
        now = time.time()
        threshold = now - self.ONLINE_THRESHOLD

        latest_heartbeat = await self.redis.zscore("presence:online", user_id)

        if latest_heartbeat is None:
            return PresenceStatus.OFFLINE
        if latest_heartbeat >= threshold:
            return PresenceStatus.ONLINE
        if latest_heartbeat >= (threshold - self.OFFLINE_GRACE):
            return PresenceStatus.AWAY
        return PresenceStatus.OFFLINE

    async def get_online_friends(self, user_id: str, friend_ids: list[str]) -> list[str]:
        """Efficiently check which friends are online using a pipeline."""
        now = time.time()
        threshold = now - self.ONLINE_THRESHOLD

        pipe = self.redis.pipeline()
        for friend_id in friend_ids:
            pipe.zscore("presence:online", friend_id)

        scores = await pipe.execute()

        online_friends = []
        for friend_id, score in zip(friend_ids, scores):
            if score is not None and score >= threshold:
                online_friends.append(friend_id)

        return online_friends

    async def disconnect(self, user_id: str, device_id: str):
        """Called when a device disconnects."""
        await self.redis.zrem(f"presence:devices:{user_id}", device_id)

        remaining = await self.redis.zcard(f"presence:devices:{user_id}")

        if remaining == 0:
            # No devices left — schedule offline notification
            # (don't immediately declare offline — device might reconnect)
            await self.redis.setex(f"presence:pending_offline:{user_id}", self.OFFLINE_GRACE, "1")

    async def _offline_sweep(self):
        """Periodically scan for users who went offline using ZRANGEBYSCORE."""
        while True:
            await asyncio.sleep(10)  # Sweep every 10 seconds

            now = time.time()
            threshold = now - self.ONLINE_THRESHOLD - self.OFFLINE_GRACE

            expired_users = await self.redis.zrangebyscore(
                "presence:online", min="-inf", max=threshold, start=0, num=1000,
            )

            if expired_users:
                await self.redis.zrem("presence:online", *expired_users)

                for user_id in expired_users:
                    await self._notify_friends_offline(user_id)

    async def _notify_friends_offline(self, user_id: str):
        """Fan-out offline notification to user's friends."""
        friend_ids = await self._get_friend_ids(user_id)
        online_friends = await self.get_online_friends(user_id, friend_ids)

        for friend_id in online_friends:
            await pubsub_bridge.publish_to_user(friend_id, {
                "type": "presence",
                "user_id": user_id,
                "status": "offline",
            })

    async def _get_friend_ids(self, user_id: str) -> list[str]:
        """Fetch friend list from the social graph service."""
        return []


class TypingIndicator:
    """
    Typing indicators are EPHEMERAL — they expire quickly and can be lost.
    No persistence needed. Use simple pub/sub (no streams).

    Design:
    - Client sends "typing" event every 3 seconds while typing
    - Server broadcasts to room
    - Recipients show "typing..." for 5 seconds after last received event
    - If no event for 5s → indicator disappears
    """

    TYPING_TTL = 5  # Seconds before "typing" expires on recipient's UI

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def set_typing(self, room_id: str, user_id: str):
        """Mark user as typing in a room. Auto-expires."""
        key = f"typing:{room_id}"
        await self.redis.hset(key, user_id, str(time.time()))
        await self.redis.expire(key, self.TYPING_TTL)

        # Broadcast to room (via pub/sub — ephemeral, loss is OK)
        await pubsub_bridge.publish_to_room(room_id, {
            "type": "typing",
            "user_id": user_id,
            "expires_in_ms": self.TYPING_TTL * 1000,
        })

    async def get_typing_users(self, room_id: str) -> list[str]:
        """Get list of users currently typing in a room."""
        key = f"typing:{room_id}"
        typing_data = await self.redis.hgetall(key)

        now = time.time()
        active_typers = [
            user_id for user_id, timestamp in typing_data.items()
            if now - float(timestamp) < self.TYPING_TTL
        ]
        return active_typers
```

---

## 11. Message Ordering & Delivery Guarantees

### The ordering problem

```
Scenario: Alice sends "Hello" then "World" in quick succession.

Without ordering guarantee:
  Server 1 receives "Hello" → publishes to Kafka partition 1
  Server 2 receives "World" → publishes to Kafka partition 2
  Consumer reads partition 2 first → Bob sees "World" then "Hello" ❌

With ordering guarantee (key-based partitioning):
  Both messages keyed by room_id → same Kafka partition
  Partition guarantees FIFO → Bob sees "Hello" then "World" ✅
```

### Delivery semantics

```
At-most-once:  Fire and forget. Message might be lost. Fast.
               Use for: typing indicators, mouse positions, ephemeral data

At-least-once: Retry until acknowledged. Message might be delivered twice.
               Use for: chat messages (client deduplicates by message_id)

Exactly-once:  Hardest. Requires idempotency + acknowledgment + deduplication.
               Use for: payments, order confirmations (usually overkill for chat)
```

### Implementing at-least-once delivery for chat

```python
import asyncio
import uuid
import time
from dataclasses import dataclass

@dataclass
class PendingMessage:
    message_id: str
    payload: dict
    created_at: float
    retry_count: int = 0
    max_retries: int = 5
    next_retry_at: float = 0


class ReliableDelivery:
    """
    Guarantees message delivery to WebSocket clients with acknowledgment.

    Flow:
    1. Server sends message with unique ID
    2. Client receives → sends ACK with message ID
    3. If no ACK within timeout → server retries
    4. Client deduplicates by message ID (idempotent receive)
    """

    def __init__(self):
        self.pending: dict[str, dict[str, PendingMessage]] = {}  # client_id → {msg_id: pending}
        self._retry_task: asyncio.Task | None = None

    async def start(self):
        self._retry_task = asyncio.create_task(self._retry_loop())

    async def send_reliable(self, client_id: str, payload: dict) -> str:
        """Send a message that MUST be delivered (with retries)."""
        message_id = str(uuid.uuid4())

        message = {**payload, "_msg_id": message_id, "_ts": time.time(), "_requires_ack": True}

        pending = PendingMessage(
            message_id=message_id,
            payload=message,
            created_at=time.time(),
            next_retry_at=time.time() + 3.0,  # Retry after 3 seconds
        )

        self.pending.setdefault(client_id, {})[message_id] = pending

        await manager.send_to_client(client_id, message)
        return message_id

    async def handle_ack(self, client_id: str, message_id: str):
        """Client acknowledged receipt. Remove from pending."""
        client_pending = self.pending.get(client_id, {})
        client_pending.pop(message_id, None)
        if not client_pending:
            self.pending.pop(client_id, None)

    async def _retry_loop(self):
        """Retry unacknowledged messages with exponential backoff."""
        while True:
            await asyncio.sleep(1)
            now = time.time()

            for client_id in list(self.pending.keys()):
                messages = self.pending.get(client_id, {})
                for msg_id in list(messages.keys()):
                    pending = messages[msg_id]

                    if now < pending.next_retry_at:
                        continue

                    if pending.retry_count >= pending.max_retries:
                        # Give up — store for offline delivery later
                        await self._store_for_offline(client_id, pending.payload)
                        messages.pop(msg_id, None)
                        continue

                    # Retry with exponential backoff
                    pending.retry_count += 1
                    backoff = min(3.0 * (2 ** pending.retry_count), 30.0)
                    pending.next_retry_at = now + backoff

                    await manager.send_to_client(client_id, pending.payload)

    async def _store_for_offline(self, client_id: str, payload: dict):
        """Store message for delivery when client reconnects."""
        # await redis.rpush(f"offline:{client_id}", json.dumps(payload))
        pass
```

### Client-side deduplication

```javascript
class DeduplicatingMessageHandler {
  constructor(maxIds = 10000) {
    this.seenIds = new Set();
    this.maxIds = maxIds;
    this.idQueue = [];  // FIFO to evict old IDs
  }

  handleMessage(message) {
    // If message requires ACK, send it
    if (message._requires_ack) {
      this.ws.send(JSON.stringify({
        type: 'ack',
        message_id: message._msg_id
      }));
    }

    // Deduplicate
    if (message._msg_id) {
      if (this.seenIds.has(message._msg_id)) {
        return;  // Already processed — server must have retried
      }
      this.seenIds.add(message._msg_id);
      this.idQueue.push(message._msg_id);

      // Evict old IDs to prevent unbounded memory growth
      while (this.idQueue.length > this.maxIds) {
        const oldId = this.idQueue.shift();
        this.seenIds.delete(oldId);
      }
    }

    // Process the message (render in UI, etc.)
    this.onMessage(message);
  }
}
```

---

## 12. Backpressure & Flow Control

### What is backpressure?

```
Problem: Server produces messages FASTER than client can consume them.

Example: Stock ticker sends 10,000 price updates/second.
         Client on slow 3G connection can only handle 100/second.

Without backpressure:
  → Server queues messages in memory → OOM crash
  → Or network buffers fill up → TCP window shrinks → affects OTHER connections

Backpressure = signaling "slow down!" back to the producer
```

### Backpressure strategies

```python
import asyncio
from enum import Enum

class BackpressureStrategy(str, Enum):
    DROP_OLDEST = "drop_oldest"    # Drop oldest queued message (news feed)
    DROP_NEWEST = "drop_newest"    # Drop incoming message (stock ticker)
    BLOCK = "block"                # Block producer until consumer catches up
    SAMPLE = "sample"              # Send every Nth message
    AGGREGATE = "aggregate"        # Combine multiple updates into one


class BackpressureQueue:
    """
    Per-connection message queue with configurable backpressure.

    At Facebook scale, you CANNOT let a slow client OOM your server.
    """

    def __init__(
        self,
        max_size: int = 1000,
        strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST,
        high_watermark: int = 800,   # Warn at 80% full
        low_watermark: int = 200,    # Resume at 20% full
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.is_congested = False
        self.dropped_count = 0
        self.total_sent = 0

    async def put(self, message: dict) -> bool:
        """Try to enqueue a message. Returns False if dropped."""
        if self.queue.qsize() >= self.high_watermark:
            self.is_congested = True

        if self.queue.full():
            return self._handle_full(message)

        await self.queue.put(message)
        self.total_sent += 1
        return True

    def _handle_full(self, message: dict) -> bool:
        """Handle queue-full condition based on strategy."""
        if self.strategy == BackpressureStrategy.DROP_NEWEST:
            self.dropped_count += 1
            return False

        elif self.strategy == BackpressureStrategy.DROP_OLDEST:
            try:
                self.queue.get_nowait()  # Remove oldest
                self.dropped_count += 1
            except asyncio.QueueEmpty:
                pass
            try:
                self.queue.put_nowait(message)  # Add newest
                return True
            except asyncio.QueueFull:
                return False

        elif self.strategy == BackpressureStrategy.SAMPLE:
            # Only accept every 10th message when congested
            self.dropped_count += 1
            if self.dropped_count % 10 == 0:
                try:
                    self.queue.get_nowait()
                    self.queue.put_nowait(message)
                    return True
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    return False
            return False

        return False

    async def get(self) -> dict:
        """Get next message to send to client."""
        message = await self.queue.get()

        if self.queue.qsize() <= self.low_watermark:
            self.is_congested = False

        return message

    def get_stats(self) -> dict:
        return {
            "queue_size": self.queue.qsize(),
            "max_size": self.max_size,
            "is_congested": self.is_congested,
            "dropped_count": self.dropped_count,
            "total_sent": self.total_sent,
            "drop_rate": self.dropped_count / max(self.total_sent + self.dropped_count, 1),
        }


class AdaptiveRateLimiter:
    """
    Dynamically adjust message rate based on client's consumption speed.

    If client is slow (ACKs come late) → reduce send rate.
    If client is fast (ACKs come quickly) → increase send rate.
    """

    def __init__(self, initial_rate: int = 100, min_rate: int = 1, max_rate: int = 10000):
        self.current_rate = initial_rate  # Messages per second
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.ack_latencies: list[float] = []
        self.window_size = 20

    def record_ack(self, sent_at: float, acked_at: float):
        """Record how long it took client to ACK a message."""
        latency = acked_at - sent_at
        self.ack_latencies.append(latency)

        if len(self.ack_latencies) > self.window_size:
            self.ack_latencies.pop(0)

        self._adjust_rate()

    def _adjust_rate(self):
        """AIMD (Additive Increase, Multiplicative Decrease) — like TCP congestion control."""
        if len(self.ack_latencies) < 5:
            return

        avg_latency = sum(self.ack_latencies) / len(self.ack_latencies)

        if avg_latency < 0.1:  # Client is fast (< 100ms ACK)
            self.current_rate = min(self.current_rate + 10, self.max_rate)
        elif avg_latency > 1.0:  # Client is slow (> 1s ACK)
            self.current_rate = max(self.current_rate // 2, self.min_rate)

    @property
    def interval(self) -> float:
        """Seconds between sends."""
        return 1.0 / self.current_rate
```

---

## 13. Reconnection Strategies & Gap Recovery

### Why reconnection is critical

```
Real-world connection drops:
- Mobile user enters elevator (30s network blip)
- WiFi → cellular handoff (2-5s gap)
- Server deploys (planned, ~10s drain period)
- ISP route change (rare, 1-2s)
- Client device sleeps (mobile background, 5min-8hr)

During a drop, messages sent by the server are LOST unless you have a
gap-recovery mechanism. The two building blocks are:
1. Exponential backoff with jitter (don't hammer the server on reconnect)
2. A resumable stream position (Last-Event-ID for SSE, custom cursor for WS)
```

### Exponential backoff with jitter (client side)

```javascript
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.attempt = 0;
    this.lastMessageId = null;   // Cursor for gap recovery
    this.ws = null;
    this.connect();
  }

  connect() {
    const url = this.lastMessageId
      ? `${this.url}?resume_from=${this.lastMessageId}`
      : this.url;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.attempt = 0;  // Reset backoff on success
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message._msg_id) this.lastMessageId = message._msg_id;
      this.onMessage?.(message);
    };

    this.ws.onclose = (event) => {
      // Codes 1000 (normal) and 1001 (going away, expected) don't need backoff jitter
      const isExpected = event.code === 1000;
      if (!isExpected) this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws.close();
    };
  }

  scheduleReconnect() {
    this.attempt++;
    // Exponential backoff: 1s, 2s, 4s, 8s... capped at maxDelay
    // Jitter (random 0-1000ms) prevents thundering herd when many clients
    // reconnect after the SAME server restart at the SAME time
    const exponential = Math.min(this.baseDelay * 2 ** this.attempt, this.maxDelay);
    const jitter = Math.random() * 1000;
    const delay = exponential + jitter;

    console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${this.attempt})`);
    setTimeout(() => this.connect(), delay);
  }

  send(data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
```

### Why jitter matters at Facebook scale

```
Without jitter:
  Server crashes → 250,000 clients ALL reconnect after exactly 4s
  → Thundering herd → new server instantly overloaded → crashes again
  → "Reconnect storm" death spiral

With jitter:
  250,000 clients reconnect spread across a 1-second window
  → Smooth, manageable ramp-up
```

### Server-side gap recovery — the resume protocol

```python
import time

async def websocket_endpoint_with_resume(websocket, room_id: str, resume_from: str | None):
    """
    resume_from is a client-supplied cursor (last message ID it saw).
    On reconnect, replay everything the client missed BEFORE accepting new traffic.
    """
    await websocket.accept()

    if resume_from:
        missed = await stream_bridge.replay_from(room_id, resume_from)
        for message in missed:
            await websocket.send_json(message)
        # Only after replay is caller safe to move on to live traffic
```

---

## 14. Security at Scale

### Authentication challenges unique to persistent connections

```
Regular HTTP: Auth header/cookie checked on EVERY request. Easy.
WebSocket:    Auth happens ONCE during handshake. Connection lives for hours.
              → If token expires mid-connection, what happens?
SSE:          Same problem, but EventSource can't send custom headers at all
              (only cookies or query params — cookies preferred, safer).
```

### Authentication patterns

```python
import time
import jwt
from fastapi import WebSocket, Query, status

SECRET_KEY = "use-env-variable-in-production"

async def authenticate_and_track_expiry(websocket: WebSocket, token: str = Query(...)):
    """
    Pattern: validate on handshake, then re-validate periodically
    (or force reconnect when the token is close to expiring).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="token_expired")
        return None
    except jwt.InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_token")
        return None

    user_id = payload["sub"]
    expires_at = payload["exp"]

    return user_id, expires_at


async def enforce_token_expiry_loop(websocket: WebSocket, expires_at: float):
    """
    Background task: force the client to reconnect with a fresh token
    BEFORE the current one expires, rather than abruptly dying mid-session.
    """
    import asyncio
    seconds_until_expiry = expires_at - time.time()
    warn_before = 60  # give the client 60s notice

    await asyncio.sleep(max(seconds_until_expiry - warn_before, 0))
    await websocket.send_json({"type": "system", "action": "refresh_token"})

    await asyncio.sleep(warn_before)
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="token_expired")
```

### Preventing common attacks

| Attack | Description | Mitigation |
|--------|-------------|-----------|
| **Origin spoofing** | Malicious site opens WS to your server | Validate `Origin` header against allowlist |
| **Connection flooding** | Attacker opens millions of connections | Per-IP connection limits, rate limiting at LB |
| **Message flooding** | Client sends messages faster than allowed | Per-connection token bucket rate limiter |
| **Oversized messages** | Client sends huge payloads to exhaust memory | Enforce `max_size` on frames (e.g. 64KB) |
| **Slow-loris on SSE** | Client opens many streams, sends nothing back | Idle timeout per connection |
| **Cache poisoning** | Malformed frames confuse intermediate proxies | Enforced by WebSocket's mandatory masking |
| **Token replay** | Stolen JWT reused after user logs out | Short-lived tokens + server-side revocation list |
| **CSWSH (Cross-Site WebSocket Hijacking)** | No CSRF-equivalent protection on WS handshake | Validate Origin + require custom auth token (not just cookies) |

### Rate limiting per connection

```python
import time

class TokenBucketRateLimiter:
    """
    Token bucket: refills at a fixed rate, each message consumes one token.
    Simple, memory-efficient, per-connection.
    """

    def __init__(self, rate: float = 10, burst: int = 20):
        self.rate = rate            # Tokens added per second
        self.burst = burst          # Max tokens (allows short bursts)
        self.tokens = burst
        self.last_refill = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


async def receive_with_rate_limit(websocket, limiter: TokenBucketRateLimiter):
    while True:
        raw = await websocket.receive_text()
        if not limiter.allow():
            await websocket.send_json({"type": "error", "reason": "rate_limited"})
            continue
        yield raw
```

### Origin validation (CSWSH protection)

```python
from fastapi import WebSocket, status

ALLOWED_ORIGINS = {"https://example.com", "https://app.example.com"}

async def validate_origin(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_origin")
        return False
    return True
```

---

## 15. Monitoring, Observability & Debugging

### Metrics you MUST track

```
Connection metrics:
  - active_connections (gauge)               → current open connections per server
  - connections_opened_total (counter)        → rate of new connections
  - connections_closed_total{code} (counter)  → closes broken down by close code
  - connection_duration_seconds (histogram)   → how long connections typically last

Message metrics:
  - messages_sent_total (counter)
  - messages_received_total (counter)
  - message_size_bytes (histogram)
  - message_send_latency_seconds (histogram)  → time from enqueue to socket write
  - messages_dropped_total{reason} (counter)  → backpressure drops

Health metrics:
  - ping_pong_latency_seconds (histogram)     → round-trip health of each connection
  - reconnects_total{room} (counter)          → how often clients need to resume
  - queue_depth (gauge)                       → per-connection backlog
  - pubsub_lag_seconds (histogram)            → delay between publish and local delivery
```

### Prometheus instrumentation

```python
from prometheus_client import Counter, Gauge, Histogram

active_connections = Gauge("ws_active_connections", "Currently open WebSocket connections")
connections_opened = Counter("ws_connections_opened_total", "Total connections opened")
connections_closed = Counter("ws_connections_closed_total", "Total connections closed", ["code"])
messages_sent = Counter("ws_messages_sent_total", "Total messages sent")
messages_dropped = Counter("ws_messages_dropped_total", "Total messages dropped", ["reason"])
message_latency = Histogram(
    "ws_message_latency_seconds",
    "Time from enqueue to delivery",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5],
)


async def instrumented_connect(websocket, user_id):
    active_connections.inc()
    connections_opened.inc()
    conn = await manager.connect(websocket, user_id)
    return conn


def instrumented_disconnect(client_id, close_code: int):
    active_connections.dec()
    connections_closed.labels(code=str(close_code)).inc()
    manager.disconnect(client_id)
```

### Debugging a production incident — a runbook

```
Symptom: Users report messages arriving late or not at all.

Step 1: Check active_connections per server — is one server overloaded
        while others are idle? (Indicates load balancer imbalance.)

Step 2: Check pubsub_lag_seconds — is the message bus (Redis/Kafka) backed up?
        If yes → check consumer group lag, scale consumers.

Step 3: Check messages_dropped_total{reason="queue_full"} — are per-connection
        queues overflowing? Indicates slow clients or undersized queues.

Step 4: Check reconnects_total — spike indicates network issues or a
        recent deploy causing mass disconnects.

Step 5: Check ping_pong_latency_seconds — high values indicate network
        congestion or CPU starvation on the server (event loop blocked).

Step 6: grep server logs for close code 1006 (abnormal closure) —
        high volume indicates infrastructure issue (LB timeout, OOM kills).

Common root causes ranked by frequency:
  1. Blocking call in the event loop (sync DB call, CPU-heavy JSON parse)
  2. Load balancer idle timeout shorter than app's heartbeat interval
  3. Redis/Kafka consumer lag during traffic spike
  4. Memory pressure causing OOM-killed pods (check kubectl top pods)
  5. Proxy buffering re-enabled by a config change (SSE only)
```

### Distributed tracing for a message's journey

```python
import time
import uuid

async def traced_publish(room_id: str, message: dict):
    """
    Attach a trace_id so you can follow a single message across:
    client → WS server A → pub/sub → WS server B → client
    """
    trace_id = str(uuid.uuid4())
    message["_trace"] = {"id": trace_id, "published_at": time.time()}

    await stream_bridge.publish_message(room_id, message)
    return trace_id

# In logs, search for trace_id to see the full path and compute per-hop latency:
#   [server-A] published trace=abc123 at t=0.000
#   [redis]    delivered  trace=abc123 at t=0.012   (12ms pub/sub hop)
#   [server-B] forwarded  trace=abc123 at t=0.014   (2ms local dispatch)
#   [client]   received   trace=abc123 at t=0.089   (75ms network to client)
```

---

## 16. Production Architecture — Facebook/Google Patterns

### Facebook Messenger's real architecture (public knowledge, simplified)

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  Mobile/Web Client                                                    │
│       │                                                                │
│       │ MQTT over WebSocket (persistent, low overhead)                │
│       ▼                                                                │
│  ┌─────────────┐                                                      │
│  │  Edge Proxy │  (Facebook: "Proxygen" — custom C++ HTTP framework)  │
│  │  (L4/L7 LB) │                                                      │
│  └──────┬──────┘                                                      │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────────┐                                                  │
│  │  MQTT Gateway    │  Terminates MQTT, holds the persistent          │
│  │  (stateful)      │  connection, translates to internal RPC          │
│  └────────┬─────────┘                                                  │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐        ┌──────────────────┐                     │
│  │  Message Service  │──────│  Iris (delivery    │                     │
│  │  (business logic) │      │  tracking system)  │                     │
│  └────────┬──────────┘      └──────────────────┘                     │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐                                                  │
│  │  Storage (sharded  │  Messages persisted before ack'd to sender    │
│  │  MySQL/RocksDB)   │                                                 │
│  └───────────────────┘                                                 │
│                                                                        │
│  Why MQTT instead of raw WebSocket?                                   │
│  - MQTT has built-in QoS levels (0=at-most-once, 1=at-least-once,     │
│    2=exactly-once) — solves delivery guarantees at the protocol level │
│  - Much smaller framing overhead than HTTP-based WebSocket messages   │
│  - Native support for offline message queuing                        │
│  - Designed for unreliable mobile networks from the start             │
└──────────────────────────────────────────────────────────────────────┘
```

### Google Docs' real-time collaboration pattern

```
Google Docs doesn't just broadcast messages — it needs to MERGE concurrent edits.

┌───────────────────────────────────────────────────────────────────┐
│  Client A types "Hello" at position 5                              │
│  Client B types "World" at position 5 (SAME TIME)                  │
│                                                                     │
│  Naive broadcast: last-write-wins → one edit is LOST                │
│                                                                     │
│  Google's approach: Operational Transformation (OT) / CRDTs        │
│                                                                     │
│  1. Each edit is an OPERATION, not a snapshot:                     │
│     op_A = {type: "insert", pos: 5, text: "Hello", client: A}      │
│     op_B = {type: "insert", pos: 5, text: "World", client: B}      │
│                                                                     │
│  2. Server receives both, TRANSFORMS them against each other        │
│     so both edits are preserved and applied in a consistent order  │
│     (e.g. op_B's position is shifted by len(op_A) if op_A applied  │
│     first)                                                          │
│                                                                     │
│  3. Server broadcasts the TRANSFORMED operations back to all       │
│     clients (via WebSocket), each client replays ops locally        │
│                                                                     │
│  This is why collaborative editing NEEDS bidirectional WebSocket   │
│  (not SSE) — clients must send their own operations upstream too.  │
└───────────────────────────────────────────────────────────────────┘
```

### Discord's approach (Elixir/Erlang — a different scaling philosophy)

```
Discord uses Elixir (built on Erlang/OTP) instead of a thread-per-connection
or async-event-loop model.

Key idea: the "Actor Model" — each WebSocket connection is an isolated,
lightweight process (not an OS thread — Erlang processes cost ~300 bytes
and you can run millions on one machine).

┌────────────────────────────────────────────────────────┐
│  BEAM VM (Erlang virtual machine)                        │
│                                                          │
│   Process 1 (User A's WS) ←→ mailbox ←→ message         │
│   Process 2 (User B's WS) ←→ mailbox ←→ message         │
│   Process 3 (Guild/Room)  ←→ mailbox ←→ message         │
│   ...millions of lightweight processes...                │
│                                                          │
│  Benefits over thread-per-connection:                    │
│  - Processes crash independently (one bad connection      │
│    doesn't take down others — "let it crash" philosophy) │
│  - Built-in distribution across machines (no need for     │
│    external pub/sub — Erlang's distribution IS the bus)  │
│  - Preemptive scheduling — one slow process can't starve   │
│    the whole VM (unlike a blocking call in an event loop)  │
└──────────────────────────────────────────────────────────┘

Lesson for non-Erlang stacks: use asyncio/goroutines per connection
(cheap, lightweight), never OS threads (expensive) for millions of
connections, and isolate failures so one bad connection can't crash others.
```

### General principles used across all three companies

```
1. TLS/connection termination at the edge, not the application tier
   → App servers handle plaintext, edge handles crypto (huge CPU savings)

2. Stateless-ish app servers + externalized connection registry
   → Any app server instance can be killed/replaced without losing the
     ABILITY to route to that user (registry says which server currently
     holds them — used for routing, not for correctness)

3. Separate "hot path" (message delivery) from "cold path" (history,
   search, analytics) — hot path optimized for latency, cold path for
   durability/completeness

4. Aggressive use of ephemeral/lossy channels for non-critical data
   (typing indicators, presence, cursor positions) vs. durable channels
   for critical data (messages, transactions)

5. Circuit breakers everywhere — a struggling downstream service (DB,
   pub/sub) must not cause cascading WebSocket disconnects
```

---

## 17. Complete Implementation — Chat System

A minimal but production-shaped chat backend combining everything above:
connection management, Redis pub/sub fan-out, presence, and reliable delivery.

```python
"""
main.py — Scalable chat backend.
Run multiple instances behind an L7 load balancer (Nginx/HAProxy/ALB)
with `least_conn` balancing. All instances share state via Redis.
"""
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status

REDIS_URL = "redis://localhost:6379"
SERVER_ID = str(uuid.uuid4())[:8]


@dataclass
class Connection:
    websocket: WebSocket
    client_id: str
    user_id: str
    rooms: set[str] = field(default_factory=set)
    last_pong: float = field(default_factory=time.time)


class ChatServer:
    def __init__(self):
        self.connections: dict[str, Connection] = {}
        self.rooms: dict[str, set[str]] = {}
        self.redis: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self._tasks.append(asyncio.create_task(self._pubsub_listener()))
        self._tasks.append(asyncio.create_task(self._ping_loop()))

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        for conn in list(self.connections.values()):
            await conn.websocket.close(code=1001, reason="Server shutting down")
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def connect(self, websocket: WebSocket, user_id: str) -> Connection:
        await websocket.accept()
        conn = Connection(websocket=websocket, client_id=str(uuid.uuid4()), user_id=user_id)
        self.connections[conn.client_id] = conn
        return conn

    async def disconnect(self, conn: Connection):
        for room in conn.rooms:
            await self.leave_room(conn, room)
        self.connections.pop(conn.client_id, None)

    async def join_room(self, conn: Connection, room_id: str):
        conn.rooms.add(room_id)
        self.rooms.setdefault(room_id, set()).add(conn.client_id)
        channel = f"room:{room_id}"
        if not await self._has_local_subscribers(channel):
            await self.pubsub.subscribe(channel)

    async def leave_room(self, conn: Connection, room_id: str):
        conn.rooms.discard(room_id)
        clients = self.rooms.get(room_id, set())
        clients.discard(conn.client_id)
        if not clients:
            self.rooms.pop(room_id, None)
            await self.pubsub.unsubscribe(f"room:{room_id}")

    async def _has_local_subscribers(self, channel: str) -> bool:
        room_id = channel.removeprefix("room:")
        return bool(self.rooms.get(room_id))

    async def publish(self, room_id: str, message: dict):
        """Publish to Redis — every server instance subscribed will receive it,
        including this one, guaranteeing consistent fan-out regardless of
        which server the sender is connected to."""
        await self.redis.publish(f"room:{room_id}", json.dumps(message))

    async def _pubsub_listener(self):
        async for raw in self.pubsub.listen():
            if raw["type"] != "message":
                continue
            room_id = raw["channel"].removeprefix("room:")
            data = json.loads(raw["data"])
            await self._local_broadcast(room_id, data)

    async def _local_broadcast(self, room_id: str, message: dict):
        client_ids = self.rooms.get(room_id, set())
        for client_id in list(client_ids):
            conn = self.connections.get(client_id)
            if conn is None:
                continue
            try:
                await conn.websocket.send_json(message)
            except Exception:
                await self.disconnect(conn)

    async def _ping_loop(self):
        while True:
            await asyncio.sleep(30)
            now = time.time()
            for conn in list(self.connections.values()):
                if now - conn.last_pong > 40:
                    await conn.websocket.close(code=1001, reason="ping_timeout")
                    await self.disconnect(conn)
                else:
                    try:
                        await conn.websocket.send_json({"type": "ping"})
                    except Exception:
                        await self.disconnect(conn)


chat = ChatServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await chat.start()
    yield
    await chat.stop()

app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/{room_id}")
async def ws_chat(websocket: WebSocket, room_id: str, token: str = Query(...)):
    user_id = await authenticate(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    conn = await chat.connect(websocket, user_id)
    await chat.join_room(conn, room_id)
    await chat.publish(room_id, {"type": "user_joined", "user_id": user_id, "ts": time.time()})

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "pong":
                conn.last_pong = time.time()
                continue

            if data.get("type") == "chat":
                await chat.publish(room_id, {
                    "type": "chat",
                    "user_id": user_id,
                    "content": data["content"],
                    "message_id": str(uuid.uuid4()),
                    "ts": time.time(),
                })
    except WebSocketDisconnect:
        pass
    finally:
        await chat.disconnect(conn)
        await chat.publish(room_id, {"type": "user_left", "user_id": user_id, "ts": time.time()})


async def authenticate(token: str) -> str | None:
    # Replace with real JWT validation
    return f"user_{token[:8]}" if token else None


@app.get("/health")
async def health():
    return {"status": "ok", "server_id": SERVER_ID, "connections": len(chat.connections)}
```

---

## 18. Complete Implementation — Live Dashboard with SSE

A metrics dashboard that pushes updates to thousands of viewers, using Redis Streams
so late-joining or reconnecting dashboards can catch up on recent history.

```python
"""
dashboard.py — SSE-based live metrics dashboard.
Multiple app servers publish metrics; every connected browser stays in sync.
"""
import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

REDIS_URL = "redis://localhost:6379"
STREAM_KEY = "stream:metrics"


class MetricsPublisher:
    """Call this from anywhere in your app (background jobs, request handlers, etc.)
    to push a new metric snapshot to every connected dashboard."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def publish(self, metric: dict):
        await self.redis.xadd(
            STREAM_KEY,
            {"payload": json.dumps({**metric, "ts": time.time()})},
            maxlen=5000,  # Keep the last 5000 snapshots; older ones auto-trimmed
        )


redis_client: redis.Redis | None = None
publisher: MetricsPublisher | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, publisher
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    publisher = MetricsPublisher(redis_client)
    yield
    await redis_client.close()

app = FastAPI(lifespan=lifespan)


def format_sse(event_id: str, data: dict) -> str:
    return f"id: {event_id}\ndata: {json.dumps(data)}\n\n"


async def metrics_stream(request: Request, last_event_id: str | None) -> AsyncGenerator[str, None]:
    # Gap recovery: replay everything since the client's last known event ID
    start_id = last_event_id or "0"
    entries = await redis_client.xrange(STREAM_KEY, min=f"({start_id}" if last_event_id else "-", count=1000)
    for entry_id, fields in entries:
        yield format_sse(entry_id, json.loads(fields["payload"]))
        start_id = entry_id

    heartbeat_deadline = time.time() + 15
    while True:
        if await request.is_disconnected():
            break

        entries = await redis_client.xread({STREAM_KEY: start_id}, count=100, block=1000)
        if entries:
            for _, messages in entries:
                for entry_id, fields in messages:
                    yield format_sse(entry_id, json.loads(fields["payload"]))
                    start_id = entry_id
                    heartbeat_deadline = time.time() + 15
        elif time.time() >= heartbeat_deadline:
            yield ": heartbeat\n\n"
            heartbeat_deadline = time.time() + 15


@app.get("/dashboard/events")
async def dashboard_events(request: Request):
    last_event_id = request.headers.get("Last-Event-ID")
    return StreamingResponse(
        metrics_stream(request, last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/internal/metrics")
async def push_metric(metric: dict):
    """Internal endpoint (or call publisher.publish() directly from app code)."""
    await publisher.publish(metric)
    return {"status": "published"}
```

```html
<!-- dashboard.html — client side -->
<script>
  const source = new EventSource('/dashboard/events');

  source.onmessage = (event) => {
    const metric = JSON.parse(event.data);
    updateChart(metric);   // your rendering logic
  };

  source.onerror = () => {
    // EventSource auto-reconnects and automatically sends Last-Event-ID
    console.warn('Dashboard stream interrupted, browser will auto-reconnect');
  };
</script>
```

---

## 19. Common Pitfalls & War Stories

### Pitfall 1: Load balancer idle timeout shorter than app heartbeat

```
Symptom: Connections silently die every ~60 seconds, clients reconnect constantly.

Root cause: AWS ALB defaults to a 60-second idle timeout. If your app sends
heartbeats every 30s but there's jitter/delay, or your app doesn't heartbeat
at all, the ALB kills the "idle" TCP connection without telling either side
cleanly (client sees 1006 abnormal closure).

Fix: Set ALB idle_timeout to at least 2x your heartbeat interval, AND set
heartbeat interval well below whatever the shortest hop's timeout is.
  aws elbv2 modify-load-balancer-attributes \
    --load-balancer-arn <arn> \
    --attributes Key=idle_timeout.timeout_seconds,Value=120
```

### Pitfall 2: Blocking the event loop kills ALL connections on that server

```
Symptom: Occasional multi-second freezes where EVERY client on one server
stops receiving messages simultaneously, then catches up in a burst.

Root cause: A synchronous call (e.g. a blocking DB query, `time.sleep()`,
CPU-heavy JSON encoding of a huge payload, or a synchronous requests.get())
inside an async handler blocks the entire asyncio event loop — which is
shared by ALL connections on that process.

Fix:
  - Never call blocking I/O without asyncio.to_thread() or an async driver
  - Move CPU-heavy work (image processing, large serialization) to a
    process pool via loop.run_in_executor()
  - Add event-loop-lag monitoring (measure how late a scheduled callback
    actually runs) to catch this in production before users complain
```

### Pitfall 3: Nginx buffering silently breaks SSE

```
Symptom: SSE works perfectly in local dev, but in production events arrive
in big delayed bursts instead of immediately (or never arrive until the
connection closes).

Root cause: Nginx buffers proxied responses by default (`proxy_buffering on`).
It waits to accumulate a full buffer (or wait for the response to finish)
before forwarding to the client — completely defeating the purpose of a
streaming response.

Fix: `proxy_buffering off;` AND `X-Accel-Buffering: no` response header AND
disable gzip for the event-stream content type (gzip also buffers).
```

### Pitfall 4: Reconnect storms after a rolling deploy

```
Symptom: A routine deploy causes a spike in DB load and CPU across the
entire fleet minutes after the deploy finishes — looks like an unrelated
incident.

Root cause: Rolling restart disconnects, say, 200K clients over 2 minutes.
All 200K clients reconnect with NO backoff or with synchronized backoff
(no jitter) → they hit the auth service and DB simultaneously.

Fix: Server sends an explicit "please reconnect within the next N seconds,
staggered randomly" instruction (close code 1012 + a delay hint) BEFORE
closing, so clients spread out their reconnects instead of all detecting
the drop at the same instant via TCP RST.
```

### Pitfall 5: Memory growth from unbounded per-connection queues

```
Symptom: Server memory grows steadily over hours/days, eventually OOM-kills.

Root cause: A per-connection outgoing queue (e.g. asyncio.Queue()) created
WITHOUT a maxsize. A single slow or stalled client (phone in a dead zone,
tab in background throttled by the OS) accumulates messages forever because
nothing ever bounds the queue or evicts stale entries.

Fix: ALWAYS set maxsize on per-connection queues, and apply an explicit
backpressure strategy (drop-oldest, disconnect, or sample) — see Section 12.
```

### Pitfall 6: Assuming WebSocket = one message = one frame

```
Symptom: Rare corrupted/garbled messages under high load or with large payloads.

Root cause: Some WebSocket libraries (and the protocol itself) allow a
single logical message to be split across multiple frames (fragmentation),
or allow multiple small messages to be coalesced depending on library
internals. Code that reads raw bytes and assumes "one receive = one
complete JSON object" occasionally breaks.

Fix: Always use your library's high-level message API (e.g. FastAPI's
`receive_text()`/`receive_json()`), which already handles frame
reassembly — don't hand-parse frames unless you're building the library
itself.
```

### Pitfall 7: Forgetting that horizontal scale-up doesn't happen automatically for stateful connections

```
Symptom: Auto-scaling adds new pods/instances under load, but the new
instances sit nearly idle while the old ones stay pegged at 100% CPU.

Root cause: Existing WebSocket connections are "stuck" to whichever server
accepted them — Kubernetes HPA or your load balancer can't move existing
persistent connections to new instances. Scale-up only helps NEW connections.

Fix: For fast relief during an incident, trigger a rolling restart (see
Pitfall 4, done carefully with jitter) to redistribute existing connections
across the now-larger fleet — new connections alone won't rebalance load.
```

### Pitfall 8: Uncontrolled intermediary proxies silently buffer SSE for minutes (real incident)

```
Symptom: A handful of users on corporate/industrial/older networks report
the app is "slow" — not broken, just slow. One reported a 20-MINUTE delay
between an action and the corresponding SSE-delivered result. Every
internal metric (server load, DB latency, queue depth) looks completely
normal. It cannot be reproduced from the office or any monitored network.

Root cause: SSE streams never send a Content-Length (the stream is
theoretically infinite), so they're sent with Transfer-Encoding: chunked.
Per the HTTP spec, chunked transfer encoding is only a promise between
TWO ADJACENT HOPS — it is legal for any intermediary proxy sitting between
your server and the client to buffer every chunk it receives and withhold
all of it until the stream closes (or its own buffer limit is hit), then
flush everything to the client at once. Some corporate/legacy proxies do
exactly this — often because they don't special-case text/event-stream
and default to "wait until I know how much data there's going to be."

There is NO HTTP header that can force a downstream proxy you don't
control to stop doing this. Disabling buffering on your own reverse proxy
(nginx `proxy_buffering off`, `X-Accel-Buffering: no`) only fixes YOUR hop
— it does nothing for other proxies further down the chain (ISP-level,
corporate network egress, older hardware) that you have no access to.

The reason it "mostly works" despite this: EventSource's built-in
auto-reconnect (plus Last-Event-ID replay) periodically re-establishes the
stream, which forces the buffering proxy to flush and deliver everything
it was holding — so events DO eventually arrive, just batched and delayed
by however long the proxy holds the connection open before you reconnect.

Fix (defense in depth, from real production experience):
  1. Require an application-level ACK from the client shortly after the
     SSE connection opens (a plain HTTP POST, not an SSE feature). If no
     ACK arrives within ~10s, treat this client as "behind a buffering
     proxy."
  2. For those clients, have the SERVER deliberately close the SSE stream
     after every single event (or after a short debounce), forcing the
     client's EventSource to reconnect immediately. Closing the stream is
     what forces a buffering proxy to flush — this effectively turns SSE
     into long polling for just the affected clients, while everyone else
     keeps a normal persistent stream.
  3. Prefer HTTPS + HTTP/2 end-to-end where possible — most legacy proxies
     that buffer plaintext HTTP/1.1 either can't intercept encrypted
     traffic at all, or don't support HTTP/2, so this class of proxy is
     avoided entirely for those users (does not guarantee safety, but
     measurably reduces exposure).
  4. Never use SSE as the ONLY delivery path for anything the user is
     actively waiting on (e.g. "your login is processing, result coming
     any second"). Reserve bare SSE for auxiliary/advisory pushes (e.g.
     "you have new notifications, go fetch them") where a multi-minute
     delay degrades gracefully instead of looking like a hang.

Relevant spec text (buried, easy to miss):
  "Authors are also cautioned that HTTP chunking can have unexpected
  negative effects on the reliability of this protocol. Where possible,
  chunking should be disabled for serving event streams unless the rate
  of messages is high enough for this not to matter."
  — the phrase "where possible" is the tell: it's not always possible,
  because you don't control every hop between you and the client.
```

---

## 20. Interview Deep-Dive Questions

```
Q: Why can't a single WebSocket server broadcast a message to a user
   connected to a different server?
A: Each server only has a local, in-process reference to the WebSocket
   objects it accepted. There's no shared memory across processes, so
   Server A publishing "send to user B" is meaningless unless something
   (a message bus) routes it to whichever server holds User B's actual
   connection object.

Q: SSE reconnects automatically via the browser's EventSource — why would
   you still need Last-Event-ID / gap recovery on the server?
A: EventSource reconnecting means a NEW TCP+HTTP request; it does not
   replay messages sent while disconnected. Last-Event-ID lets the server
   know where the client left off so it can replay anything published
   during the gap, typically from a Redis Stream or similar log.

Q: Why use `least_conn` instead of round-robin for WebSocket load balancing?
A: Round-robin distributes NEW connections evenly, but says nothing about
   how many are STILL open on each backend. Because WS/SSE connections are
   long-lived, round-robin can leave one backend with far more concurrent
   connections than another over time. `least_conn` actively considers
   current connection counts.

Q: Why is masking required for client→server WebSocket frames but not
   server→client?
A: It's a security fix (2010) against proxy cache poisoning: an attacker
   controlling client-side JS could otherwise craft WebSocket payloads that
   look like valid HTTP requests to a misbehaving intermediary. Only the
   client is untrusted from the proxy's point of view, so only client
   frames must be masked.

Q: How would you design exactly-once message delivery for a chat app, and
   is it actually necessary?
A: True exactly-once is very expensive (requires transactional writes tied
   to delivery acknowledgment). Most chat systems use at-least-once
   delivery + idempotent client-side deduplication by message_id, which is
   operationally simpler and functionally indistinguishable to the user.
   Reserve true exactly-once for financial/critical operations.

Q: A customer reports messages arriving out of order. How do you debug it
   at scale, and how do you prevent it architecturally?
A: Check whether messages for the same room/conversation are being
   partitioned consistently in your message bus (e.g. keyed by room_id in
   Kafka so they land on the same partition, preserving order). If using
   Redis Pub/Sub with multiple publishers, there's no ordering guarantee
   across publishers at all — you'd need to route all writes for a given
   room through a single owner or use a stream-based approach with a
   single writer/sequence number per room.

Q: Why might Facebook use MQTT-over-WebSocket instead of raw WebSocket
   with JSON?
A: MQTT provides QoS levels (delivery guarantees) as a protocol primitive,
   has a far smaller binary framing overhead than repeated JSON envelopes,
   and has first-class support for offline queuing — all of which would
   otherwise need to be hand-rolled on top of raw WebSocket.

Q: How do you prevent a thundering herd when a WebSocket server restarts
   and 250K clients need to reconnect?
A: Two techniques combined: (1) the server sends an explicit
   "please reconnect, staggered" signal with a random delay hint before
   closing, rather than letting clients discover the drop via a hard
   TCP reset; (2) clients independently apply exponential backoff with
   random jitter on every reconnect attempt, regardless of cause.

Q: What's the tradeoff between Redis Pub/Sub, Redis Streams, NATS, and
   Kafka for cross-server message routing?
A: Redis Pub/Sub is simplest and fastest but fire-and-forget (no
   persistence, no replay — a disconnected subscriber loses messages).
   Redis Streams adds persistence and replay via consumer groups at some
   throughput cost. NATS Core matches Pub/Sub's simplicity with much
   higher throughput; NATS JetStream adds persistence similar to Streams.
   Kafka is the heaviest but offers the strongest ordering/retention/
   multi-datacenter guarantees — appropriate once you need days of replay
   history or exactly-once semantics across services.
```

---

## 21. Appendix — Web Workers for Offloading Client-Side Work

This is unrelated to the SSE/WebSocket protocols themselves, but it's a
genuinely useful companion tool: once your client is receiving a high
volume of real-time messages (chat, live prices, telemetry), the work of
**parsing and processing every incoming message can itself become a
bottleneck on the main thread** — and that's exactly the kind of CPU-bound
work a Web Worker is built to offload.

### The problem it solves

```
Without a worker:
  WebSocket/SSE message arrives → onmessage handler runs ON THE MAIN THREAD
  → parses JSON, transforms data, maybe does heavy computation
  → if this is slow or messages arrive fast enough, the UI thread gets
    congested → scrolling/clicking/animations start to lag or freeze,
    even though the network layer itself is fine

With a worker:
  WebSocket/SSE message arrives → immediately handed off to a Worker
  → worker parses/processes it off the main thread
  → worker posts back only the FINAL, ready-to-render result
  → main thread stays free for UI the entire time
```

### What a Web Worker actually is (quick recap)

A Web Worker runs a separate JS file on its own OS thread. It has **no
DOM access** and does not share memory with the main thread — the two
communicate only by passing messages (data gets copied across the
boundary via `postMessage`/`onmessage`).

```
┌─────────────────────┐      postMessage()      ┌─────────────────────┐
│    Main Thread        │ ─────────────────────→  │   Worker Thread        │
│  - Renders UI          │                          │  - No DOM access        │
│  - WebSocket/SSE         │                          │  - Parses/processes     │
│    connection lives      │ ←─────────────────────  │    incoming messages    │
│    here (Workers can't   │      postMessage()      │  - Never blocks the      │
│    hold a WebSocket in   │                          │    UI, no matter how     │
│    older browsers, but   │                          │    much work it does     │
│    modern browsers DO    │                          │                          │
│    support WebSocket     │                          │                          │
│    inside a Worker too)  │                          │                          │
└─────────────────────┘                          └─────────────────────┘
```

### Practical use case — offloading heavy message processing for a live chat/ticker

Imagine a stock-ticker or chat app receiving hundreds of WebSocket
messages per second, where each message needs non-trivial processing
(e.g. recalculating derived stats, running a diff against previous state,
or decompressing a payload) before it's ready to render.

**Main thread — owns the WebSocket, hands off processing to the worker:**

```javascript
// main.js
const worker = new Worker('processor.js');
const socket = new WebSocket('wss://example.com/prices');

socket.onmessage = (event) => {
  // Hand the raw message straight to the worker instead of processing
  // it here — this line is nearly instant, so the main thread never
  // stalls no matter how heavy the processing turns out to be.
  worker.postMessage(event.data);
};

worker.onmessage = (event) => {
  // The worker sends back only the FINAL, ready-to-render result.
  renderPriceUpdate(event.data);
};

function renderPriceUpdate(data) {
  document.getElementById('price').textContent = data.formattedPrice;
}
```

**Worker — does the actual heavy lifting off the main thread:**

```javascript
// processor.js
self.onmessage = (event) => {
  const raw = JSON.parse(event.data);

  // Simulate non-trivial processing: recompute derived stats,
  // apply business logic, format for display, etc.
  const result = {
    symbol: raw.symbol,
    formattedPrice: `$${raw.price.toFixed(2)}`,
    changePercent: computeChangePercent(raw),
  };

  self.postMessage(result);
};

function computeChangePercent(raw) {
  // Any CPU-heavy calculation goes here — it runs on the worker's
  // thread, so however long it takes, the page stays responsive.
  return ((raw.price - raw.previousClose) / raw.previousClose) * 100;
}
```

### Practical use case — a worker holding a SharedWorker-based single connection across tabs

If a user opens the same chat/dashboard in multiple browser tabs, each
tab opening its OWN WebSocket/SSE connection wastes server connections
and can hit the browser's per-domain limits. A `SharedWorker` lets ALL
tabs share a single underlying connection:

```javascript
// shared-connection-worker.js — runs ONCE, shared by every open tab
const ports = [];
let socket = null;

self.onconnect = (event) => {
  const port = event.ports[0];
  ports.push(port);
  port.start();

  if (!socket) {
    socket = new WebSocket('wss://example.com/prices');
    socket.onmessage = (event) => {
      // Broadcast every incoming message to ALL connected tabs
      for (const p of ports) p.postMessage(event.data);
    };
  }
};
```

```javascript
// main.js — in EVERY tab
const worker = new SharedWorker('shared-connection-worker.js');
worker.port.start();
worker.port.onmessage = (event) => {
  renderPriceUpdate(JSON.parse(event.data));
};
```

This means 10 open tabs from the same user result in exactly ONE
WebSocket connection to your server, not ten — directly helping the
"connection distribution at scale" problem discussed in Section 6, but
from the client side instead of the server side.

### When it's actually worth doing

```
Use a worker for incoming real-time messages when:
  ✅ Per-message processing is genuinely CPU-heavy (not just "parse a
     small JSON blob" — that alone is too cheap to bother offloading)
  ✅ Message volume is high enough that cumulative processing time on
     the main thread visibly competes with UI responsiveness
  ✅ You want to share a single connection across multiple tabs
     (SharedWorker) to reduce total server-side connection count

Skip it when:
  ❌ Messages are small/infrequent and processing is trivial — the
     postMessage thread-hop overhead can exceed the cost of just doing
     it inline on the main thread
  ❌ The processing needs to touch the DOM mid-computation (workers have
     no DOM access — they can only hand back a final result for the
     main thread to render)
```

For the full deep dive on Web Workers — message batching, Transferable
objects, `SharedArrayBuffer`, debugging, and common misconceptions — see
the dedicated `WEB_WORKERS_MULTITHREADING_new_more.md` reference doc.

