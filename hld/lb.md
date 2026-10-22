# Software Load Balancer Architecture (Maglev-Inspired)

> Reference: *Maglev: A Fast and Reliable Software Network Load Balancer* — Google, 2016

---

## Problem Statement

Distribute millions of requests per second across backend servers reliably, with zero single points of failure, low latency, and seamless horizontal scaling.

**Key Questions to Ask First:**
- What is the expected QPS (queries per second)?
- What are the latency SLAs? (e.g., p99 < 10ms for LB hop)
- What failure modes must we tolerate? (server crash, network partition, rolling deploys)
- Do we need session affinity / sticky routing?
- What consistency guarantees are needed for config propagation?

---

## High-Level Architecture

```
                         ┌──────────┐
                         │ Core DNS │
                         └────┬─────┘
                              │ resolves lb.payments.google.com → 10.0.0.1 (VIP)
                              ▼
                      ┌───────────────┐
          End Users → │  LB Servers   │ ← (cluster behind VIP via ECMP/BGP)
                      │  (Maglev)     │
                      └───┬───┬───┬───┘
                          │   │   │
                ┌─────────┘   │   └─────────┐
                ▼             ▼             ▼
          ┌──────────┐ ┌──────────┐ ┌──────────┐
          │ Backend  │ │ Backend  │ │ Backend  │
          │ Server 1 │ │ Server 2 │ │ Server N │
          └──────────┘ └──────────┘ └──────────┘

                    CONTROL PLANE
          ┌─────────────────────────────────┐
          │         Orchestrator            │
          │      (leader election)          │
          └──────┬──────────────┬───────────┘
                 │              │
          heartbeats        updates
                 │              │
          ┌──────▼──────┐  ┌───▼────────────┐
          │ LB Servers  │  │ Backend Servers │
          └─────────────┘  └────────────────┘

                 OBSERVABILITY
          ┌──────────────────────────────────┐
          │  Prometheus  ←── CPU, Mem, N/w   │
          │      ↑                           │
          │    Query (Grafana)               │
          │      ↓                           │
          │  Autoscaling                     │
          └──────────────────────────────────┘

                 ASYNC PROPAGATION
          ┌──────────────────────────────────┐
          │  DB ──CDC──→ Redis PubSub        │
          │                  ↓               │
          │         LB Servers subscribe     │
          └──────────────────────────────────┘

                 DEVELOPER INTERFACE
          ┌──────────────────────────────────┐
          │  LB Console / APIs               │
          │  Developer → Console → DB → CDC  │
          └──────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Core DNS

**Role:** Translates the human-readable domain (`lb.payments.google.com`) into a Virtual IP (VIP) like `10.0.0.1`.

**Why a VIP, not a real server IP?**
- Decouples users from actual infrastructure. If a server dies, the VIP stays the same.
- Multiple LB machines can share the same VIP via BGP anycast or ECMP.
- Users never need to know (or cache) a real server address.

**What is a VIP (Virtual IP)?**
```
Think of VIP like a company's reception desk phone number.

Real scenario:
  Company reception: 1800-123-4567  (this is the VIP)
  Behind it: 5 actual phone lines (actual servers)

  - Customer dials 1800-123-4567
  - The PBX system routes the call to one of 5 actual phones
  - If phone #3 breaks, the number still works — calls go to the other 4
  - Customer never knew phone #3 existed

In networking:
  VIP: 10.0.0.1               (the address clients connect to)
  Real IPs: 10.0.0.10,        (LB server 1)
            10.0.0.11,        (LB server 2)
            10.0.0.12         (LB server 3)

  - Client sends packet to 10.0.0.1
  - Network infrastructure routes it to one of the real LB servers
  - If 10.0.0.11 dies, traffic goes to the other two
  - Client never knew about 10.0.0.10/11/12
```

**DNS-level considerations:**
- Low TTL so clients pick up changes quickly during failovers
- Multiple A records or anycast for geographic distribution
- Health-checked DNS (Route53-style) as an optional outer layer

---

### 2. LB Servers (Data Plane)

**Role:** Receive every inbound packet on the VIP and decide which backend handles it.

**How multiple LBs share one VIP:**
- **ECMP (Equal-Cost Multi-Path):** The router upstream of the LBs treats all LB machines as equal next-hops for the VIP. Packets are spread across them using a 5-tuple hash.
- **BGP Anycast:** Each LB advertises the same VIP prefix. The network routes packets to the nearest one.

#### ECMP — Explained Simply

```
ECMP = "The router has multiple equal paths to the same destination,
        so it spreads packets across all of them."

Without ECMP (single path):
  Client → Router → [LB-1] → Backends
                     ^^^^
                     bottleneck & SPOF

With ECMP (multiple equal paths):
  Client → Router ──→ LB-1 → Backends
                  ├──→ LB-2 → Backends
                  └──→ LB-3 → Backends

How the router decides which LB gets each packet:
  It hashes the packet's "5-tuple":
    (source IP, dest IP, source port, dest port, protocol)
  hash("192.168.1.5, 10.0.0.1, 52431, 443, TCP") % 3 = 1  → LB-2
  hash("192.168.1.9, 10.0.0.1, 38712, 443, TCP") % 3 = 0  → LB-1

  Same connection always goes to the same LB (because 5-tuple is stable).
  Different connections spread across LBs.
```

**How it's set up (cloud-independent):**
1. All LB servers are connected to the same **Top-of-Rack (ToR) router**
2. Each LB is configured as a **next-hop** for the VIP `10.0.0.1`
3. The router sees: "I have 3 equal-cost routes to `10.0.0.1`"
4. It automatically load-balances across them using 5-tuple hashing

**The catch:** When an LB is added or removed, the router's hash changes. Some connections may get rerouted to a different LB (which doesn't have their connection table entry). Maglev's consistent hashing minimizes this disruption.

#### BGP Anycast — Explained Simply

```
BGP = Border Gateway Protocol (how routers on the internet learn paths)
Anycast = "Multiple servers advertise the same IP; network picks the closest"

Real-world analogy:
  Imagine 3 Domino's outlets in a city, all with the same phone number.
  When you call, the phone system routes you to the NEAREST outlet.
  Each outlet is independent. If one closes, calls go to the next nearest.

In networking:
  LB in Mumbai    advertises: "I can handle traffic for 10.0.0.1"
  LB in Singapore advertises: "I can handle traffic for 10.0.0.1"
  LB in Frankfurt advertises: "I can handle traffic for 10.0.0.1"

  User in India → packet goes to Mumbai LB (closest)
  User in Japan → packet goes to Singapore LB (closest)

  If Mumbai LB dies:
    It stops advertising the route via BGP
    Within seconds, routers converge
    Indian users now route to Singapore (next closest)
```

**Key difference from ECMP:**

| | ECMP | BGP Anycast |
|---|---|---|
| **Scope** | Within one data center (same router) | Across data centers / globally |
| **Routing decision** | Hash-based (spread evenly) | Proximity-based (nearest server) |
| **Use case** | Spread traffic across LBs in one location | Geographic distribution |
| **Setup** | Router config (static routes) | Each LB runs a BGP daemon (e.g., BIRD, ExaBGP) |

**In practice, you use both together:**
```
Global level:  BGP Anycast routes user to nearest data center
                        ↓
Data center:   ECMP spreads traffic across LB servers in that DC
                        ↓
LB server:     Maglev hashing picks the backend
```

**Backend Selection — Maglev Consistent Hashing:**
```
Traditional hashing:   backend = hash(flow) % N
  Problem: adding/removing a server reshuffles almost every flow

Maglev hashing:        build a lookup table where each backend "claims" slots
  Benefit: adding/removing a server only disrupts ~1/N of flows
  Table size: prime number (e.g., 65537) for even distribution
```

**Connection Tracking:**
- Even with consistent hashing, a connection mid-flight during a backend change could get rerouted.
- LBs maintain a **connection table** (flow → backend mapping) so existing connections stick to their assigned backend.
- New connections use the hash table; existing ones use the connection table.

**Packet Forwarding Modes:**
| Mode | How It Works | Pros | Cons |
|------|-------------|------|------|
| **DSR (Direct Server Return)** | LB rewrites destination MAC, backend replies directly to client | LB only sees inbound traffic; massive throughput | Backend must be on same L2 or use IP-in-IP tunneling |
| **NAT (DNAT)** | LB rewrites destination IP to backend's real IP | Simple, works across networks | LB sees both request and response (bottleneck) |
| **Tunneling (GRE/IP-in-IP)** | LB encapsulates packet, backend decapsulates and replies directly | DSR across L3 boundaries | Overhead of encapsulation, MTU concerns |

Maglev uses **GRE encapsulation** with Direct Server Return.

---

### 3. Backend Servers

**Role:** Handle the actual business logic (e.g., `/pay/api` for payment processing).

**Design Principles:**
- **Stateless:** No local session state. Any backend can handle any request. State lives in external stores (Redis, DB).
- **Horizontally scalable:** Add more instances behind the LB to handle more load.
- **Health endpoints:** Expose `/health` or `/ready` for the orchestrator to probe.

**Graceful Shutdown:**
1. Backend signals "draining" to orchestrator
2. Orchestrator tells LBs to stop sending new connections
3. Backend finishes in-flight requests
4. Backend shuts down cleanly

---

### 4. Orchestrator (Control Plane)

**Role:** The brain that manages LB and backend membership, detects failures, and propagates routing updates.

**Leader Election:**
- Only one orchestrator is active at a time (the leader)
- Uses consensus protocols: **Raft**, **Paxos**, or a coordination service like **ZooKeeper** / **etcd**
- Followers are hot standbys; if the leader dies, a new one is elected in seconds

**Heartbeat Mechanism:**
```
Orchestrator ──heartbeat──→ LB Servers     (are you alive?)
Backend Servers ──heartbeat──→ Orchestrator (I'm alive, here's my load)
```

- **Failure detection:** If an LB or backend misses N consecutive heartbeats, mark it as down.
- **Tuning tradeoff:** Short intervals = fast detection but more network traffic. Typical: 1-5 second intervals, 3 missed = dead.

**What the Orchestrator Manages:**
| Responsibility | Mechanism |
|---|---|
| Backend membership | Heartbeat-based health checks |
| LB routing table updates | Push updates when backends join/leave |
| Backend weights | Adjust based on capacity/health signals |
| Draining coordination | Signal LBs to stop routing to a draining backend |
| Config distribution | Propagate routing rules, rate limits, etc. |

---

### 5. Observability Stack

#### Prometheus (Metrics Collection)

**What it collects from backends:**
- **CPU utilization** — are backends saturated?
- **Memory usage** — approaching OOM?
- **Network I/O** — bandwidth bottlenecks?
- **Application metrics** — request latency, error rates, queue depths

**Pull vs Push model:**
- Prometheus uses **pull**: it scrapes `/metrics` endpoints on each backend at regular intervals.
- This is simpler (backends don't need to know where to push) and naturally handles backend failures (scrape fails = alert).

#### Query Layer (Grafana)

- Dashboards for real-time visibility
- PromQL for ad-hoc investigation
- Alert rules (e.g., `rate(http_errors_total[5m]) > 0.01` → page on-call)

#### Autoscaling

**Reactive scaling based on metrics:**
```
IF avg(cpu_usage) > 70% for 5 minutes → scale up (+2 backends)
IF avg(cpu_usage) < 30% for 15 minutes → scale down (-1 backend)
```

**Scaling flow:**
1. Prometheus detects high CPU across backends
2. Autoscaler triggers (Kubernetes HPA, custom controller, or cloud ASG)
3. New backend instance starts, registers with orchestrator
4. Orchestrator pushes updated backend list to LB servers
5. LB servers update their Maglev hash table (minimal disruption)

**Predictive scaling (advanced):**
- Use historical patterns (e.g., traffic spikes at 9 AM) to pre-scale
- ML-based forecasting for gradual ramp-ups

---

### 6. Async Communication — CDC + Redis PubSub

**Problem:** Config changes (new backends, routing rules, rate limits) are stored in a DB. How do LB servers learn about them without polling?

**Solution: Change Data Capture → Redis PubSub**

```
Developer makes change via Console
        ↓
    DB write (source of truth)
        ↓
    CDC captures the change (e.g., Debezium on Postgres WAL)
        ↓
    Publishes to Redis PubSub channel
        ↓
    LB Servers (subscribers) receive the update in real-time
        ↓
    LB Servers update their in-memory routing tables
```

**Why CDC instead of direct events from the Console?**
- DB remains the single source of truth
- No dual-write problem (write to DB + publish event = risk of inconsistency)
- CDC is reliable — it reads from the DB's own transaction log (WAL/binlog)
- Works even for changes made directly to the DB (migrations, manual fixes)

**Why Redis PubSub?**
- Low latency (~sub-millisecond delivery)
- Simple pub/sub semantics
- LBs subscribe to specific channels (e.g., `config:routing`, `config:backends`)

**Caveat:** Redis PubSub is fire-and-forget. If an LB is temporarily disconnected, it misses messages. Mitigations:
- On reconnect, LB fetches the full current config from DB
- Use Redis Streams instead of PubSub for at-least-once delivery with consumer groups

---

### 7. LB Console & APIs (Developer Interface)

**Role:** Management interface for operators and developers.

**Capabilities:**
- Register/deregister backend servers
- Set routing rules (path-based, header-based, weighted)
- View real-time health and traffic dashboards
- Configure rate limits and circuit breakers
- Trigger draining for maintenance

**Change Flow:**
```
Developer → Console UI / API call
    → Writes to DB
    → CDC picks up the change
    → Redis PubSub notifies LB servers
    → LBs update routing in-memory
```

This is fully **async and decoupled**. The developer gets an instant acknowledgment (DB write succeeded), and the change propagates within milliseconds.

---

## Thought Process Framework

### How to approach designing a system like this:

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: CLARIFY THE PROBLEM                                 │
│ ├── Scale: QPS, bandwidth, number of backends               │
│ ├── Latency SLA: how fast must the LB forward packets?      │
│ ├── Failure tolerance: what can break without user impact?   │
│ └── Consistency: how fast must config changes take effect?   │
├──────────────────────────────────────────────────────────────┤
│ STEP 2: DESIGN THE DATA PLANE (the fast path)               │
│ ├── Request flow: User → DNS → VIP → LB → Backend           │
│ ├── Backend selection: consistent hashing (Maglev)           │
│ ├── Forwarding mode: DSR / NAT / Tunneling                  │
│ ├── Connection tracking: sticky for existing connections     │
│ └── No SPOF: multiple LBs behind ECMP/BGP                   │
├──────────────────────────────────────────────────────────────┤
│ STEP 3: DESIGN THE CONTROL PLANE (the brain)                │
│ ├── Failure detection: heartbeats from backends              │
│ ├── Config propagation: CDC → PubSub (async, decoupled)     │
│ ├── Coordination: leader election for orchestrator HA        │
│ └── Graceful operations: draining, rolling updates           │
├──────────────────────────────────────────────────────────────┤
│ STEP 4: ADD OBSERVABILITY (the eyes)                         │
│ ├── Metrics: CPU, Memory, Network, App-level (Prometheus)    │
│ ├── Dashboards: Grafana for real-time visibility             │
│ ├── Alerting: threshold-based and anomaly detection          │
│ └── Autoscaling: reactive + predictive                       │
├──────────────────────────────────────────────────────────────┤
│ STEP 5: DEVELOPER EXPERIENCE (the interface)                 │
│ ├── Console/API for management                               │
│ ├── Change flow: Console → DB → CDC → PubSub → LBs          │
│ └── Audit trail: who changed what, when                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

| Principle | Where It Appears | Why It Matters |
|---|---|---|
| **No Single Point of Failure** | Multiple LBs behind VIP, leader election for orchestrator | Any single component can die without user impact |
| **Separation of Data & Control Plane** | LB servers (data) vs Orchestrator (control) | Data plane is optimized for speed; control plane for correctness |
| **Async Propagation** | CDC → Redis PubSub | Decouples producers from consumers; no blocking on config changes |
| **Consistent Hashing** | Maglev hash table for backend selection | Minimal disruption when backends are added/removed |
| **Observability-Driven Scaling** | Prometheus → Autoscaler | Decisions based on real data, not guesses |
| **Indirection via VIP** | DNS resolves to VIP, not real IPs | Infrastructure changes are invisible to clients |
| **Graceful Degradation** | Connection tracking, draining, health checks | Existing users aren't disrupted during changes |

---

## Failure Scenarios & Handling

| Failure | Detection | Recovery |
|---|---|---|
| **Backend crashes** | Heartbeat timeout (orchestrator) | Orchestrator removes it from backend list → pushes update to LBs → Maglev table rebuilt |
| **LB server crashes** | Router detects via BGP/health check | ECMP removes the LB; traffic redistributed to remaining LBs. Connection table entries on that LB are lost; consistent hashing re-routes those flows |
| **Orchestrator leader dies** | Follower detects missing heartbeat | New leader elected via Raft/Paxos. Brief delay in control plane operations; data plane (LBs) continues unaffected |
| **Redis PubSub down** | Orchestrator/LB health check | LBs fall back to periodic DB polling or serve stale config (safe: backends are still health-checked) |
| **DB goes down** | Application-level health check | Console writes fail (degraded management). LBs continue with in-memory config. CDC resumes from WAL position after DB recovery |
| **Network partition** | Split-brain detection | Orchestrator leader on minority side steps down. LBs on each side continue serving with their last-known config |

---

## Maglev-Specific Concepts

### Maglev Hashing Algorithm

```python
# Simplified Maglev hash table construction
def build_maglev_table(backends, table_size):
    """
    Each backend generates a preference list (permutation) of table slots.
    Backends take turns claiming their next preferred slot.
    Result: a lookup table where each slot maps to exactly one backend.
    """
    permutations = {}
    for backend in backends:
        offset = hash1(backend.name) % table_size
        skip = hash2(backend.name) % (table_size - 1) + 1
        permutations[backend] = [
            (offset + i * skip) % table_size
            for i in range(table_size)
        ]

    table = [None] * table_size
    filled = 0
    pointers = {b: 0 for b in backends}

    while filled < table_size:
        for backend in backends:
            while table[permutations[backend][pointers[backend]]] is not None:
                pointers[backend] += 1
            slot = permutations[backend][pointers[backend]]
            table[slot] = backend
            pointers[backend] += 1
            filled += 1
            if filled == table_size:
                break

    return table
```

**Properties:**
- Table size is a **prime number** (e.g., 65537) for even distribution
- Adding a backend only changes ~`1/N` of the table entries
- Lookup is O(1) — just `table[hash(5-tuple) % table_size]`

### Per-Packet vs Per-Connection

- **First packet** of a new connection → Maglev hash table lookup → result stored in connection table
- **Subsequent packets** of the same connection → connection table lookup (faster, stable)
- **Connection table miss** (e.g., after LB restart) → fall back to hash table (consistent hashing ensures likely same backend)

---

## Autoscaling the Load Balancers Themselves (Cloud-Independent)

> Autoscaling backends is well understood. But who scales the LBs? This is the harder problem.

### Why LB Autoscaling Is Tricky

Backends are stateless — spin one up, register it, done. LBs are different:
- Each LB holds a **connection table** (active flows mapped to backends)
- Adding/removing an LB changes the ECMP hash → some flows get rerouted
- LBs sit at the **network edge** — you can't just swap them like app containers

### The Architecture for LB Autoscaling

```
                    ┌──────────────────────────┐
                    │     LB Orchestrator       │
                    │  (control plane + scaler) │
                    └─────┬──────────┬──────────┘
                          │          │
                   metrics│          │provision / drain
                          │          │
            ┌─────────────▼──┐   ┌───▼──────────────┐
            │  Metrics Store  │   │  Provisioner      │
            │  (Prometheus /  │   │  (Ansible/Salt/   │
            │   VictoriaM)   │   │   custom daemon)  │
            └────────────────┘   └───────────────────┘
                    ▲                      │
         scrape /   │              provision│ / drain
         push       │                      ▼
            ┌───────┴────┬────────────┬──────────┐
            │  LB-1      │  LB-2      │  LB-N    │
            │  (active)  │  (active)  │  (new)   │
            └────────────┴────────────┴──────────┘
                    ▲
                    │  ECMP / BGP
                    │
               ┌────┴─────┐
               │  Router   │
               └───────────┘
```

### Step-by-Step: How It Works

#### Step 1 — Decide WHEN to scale (Metrics-Driven)

Each LB exports metrics that signal saturation:

```
LB-Level Metrics:
  ├── packets_per_second          (approaching NIC line rate?)
  ├── connections_active          (connection table filling up?)
  ├── cpu_utilization             (packet processing saturated?)
  ├── memory_usage                (connection table + hash table fit in RAM?)
  ├── drops_per_second            (packets being dropped? CRITICAL)
  └── latency_added_by_lb        (forwarding delay increasing?)
```

**Scaling triggers (example policy):**
```
SCALE UP when ANY of:
  - avg(packets_per_second) > 80% of NIC capacity for 2 min
  - avg(cpu_utilization) > 70% for 3 min
  - drops_per_second > 0 for 30 sec   ← most urgent
  - connections_active > 80% of table size

SCALE DOWN when ALL of:
  - avg(packets_per_second) < 30% of NIC capacity for 15 min
  - avg(cpu_utilization) < 25% for 15 min
  - connections_active < 30% of table size
  - (AND at least N_min LBs remain — never go below minimum)
```

**Why asymmetric thresholds?** Scale up aggressively (80%, 2 min), scale down conservatively (30%, 15 min). Scaling down disrupts connections; scaling up doesn't.

#### Step 2 — Provision the new LB (Cloud-Independent)

You need a **Provisioner** that works without AWS/GCP-specific APIs:

```
Option A: Pre-provisioned warm pool
  ┌─────────────────────────────────────────┐
  │ Warm Pool: 3 LB machines sitting idle,  │
  │ OS + software installed, config synced  │
  │ Just not advertising the VIP yet        │
  └─────────────────────────────────────────┘
  Scale up = tell warm pool machine to start advertising VIP via BGP
  Fastest option: seconds to activate

Option B: VM/Container provisioning via orchestration tools
  ┌──────────────────────────────────────────────────┐
  │ Provisioner (Ansible / SaltStack / custom daemon) │
  │   1. Spin up VM from LB image (libvirt/QEMU/ESXi)│
  │   2. Apply config (Ansible playbook)              │
  │   3. Start LB software                           │
  │   4. Health check passes                          │
  │   5. Tell router to add as ECMP next-hop          │
  └──────────────────────────────────────────────────┘
  Slower: 30s-2min depending on infra

Option C: Bare-metal with PXE boot (large scale)
  ┌────────────────────────────────────────────────┐
  │ Rack of spare servers, PXE-boot with LB image  │
  │ Used by Google/Facebook for Maglev-class scale │
  └────────────────────────────────────────────────┘
  Slowest to start: minutes. But highest throughput per node.
```

**Config Sync:** New LB needs the current backend list + routing rules before it starts:
```
New LB boots up
    → Pulls full config from DB (or config service like etcd/Consul)
    → Builds Maglev hash table in memory
    → Starts empty connection table (no problem — consistent hashing
      ensures correct backend for new flows)
    → Announces VIP via BGP / gets added to ECMP
    → Starts receiving traffic
```

#### Step 3 — Integrate with the network (the critical part)

This is what makes LB scaling different from backend scaling:

```
Adding an LB to ECMP:
  ┌──────────────────────────────────────────────────────┐
  │ BEFORE (2 LBs):                                      │
  │   Router hash: flow % 2                              │
  │     Connection A → LB-1                              │
  │     Connection B → LB-2                              │
  │                                                      │
  │ AFTER (3 LBs):                                       │
  │   Router hash: flow % 3                              │
  │     Connection A → LB-1  ← SAME (lucky)             │
  │     Connection B → LB-3  ← MOVED! (was LB-2)        │
  │                                                      │
  │ Connection B is now at LB-3, which has no connection │
  │ table entry for it.                                  │
  │                                                      │
  │ FIX: LB-3 uses Maglev consistent hashing.           │
  │ Since the hash table gives the same answer as LB-2's │
  │ table did, the packet goes to the correct backend.   │
  │ The TCP connection survives!                          │
  └──────────────────────────────────────────────────────┘
```

**For BGP-based setups (using BIRD / ExaBGP / FRRouting):**
```
# On the new LB, start advertising the VIP:
# /etc/bird/bird.conf

protocol static {
    route 10.0.0.1/32 via "lo";      # VIP bound to loopback
}

protocol bgp upstream {
    neighbor 10.0.1.1 as 65000;       # ToR router
    export where net = 10.0.0.1/32;   # advertise VIP
}

# Router sees the new BGP announcement
# Adds it as another equal-cost path → ECMP now includes new LB
```

#### Step 4 — Draining an LB (scale down)

Removing an LB is more delicate than adding one:

```
WRONG way:
  Just kill the LB → all its active connections break instantly

RIGHT way (graceful drain):
  1. Orchestrator decides to remove LB-3
  2. LB-3 stops advertising VIP via BGP
     └── Router removes LB-3 from ECMP within seconds
     └── No NEW traffic goes to LB-3
  3. LB-3 continues processing in-flight connections
     └── Set a drain timeout (e.g., 30 seconds)
  4. After timeout, remaining connections are RST'd
     └── Clients reconnect → hit LB-1 or LB-2
  5. LB-3 shuts down cleanly
     └── Returns to warm pool or gets deprovisioned
```

**Timeline:**
```
t=0s    Orchestrator: "scale down, drain LB-3"
t=1s    LB-3 withdraws BGP route
t=3s    Router converges, no new traffic to LB-3
t=3-33s LB-3 finishes existing connections
t=33s   LB-3 sends RST for any remaining connections
t=35s   LB-3 shut down → back to warm pool
```

### Full Autoscaling Loop (Cloud-Independent)

```
┌─────────────────────────────────────────────────────────────┐
│                   LB AUTOSCALING LOOP                       │
│                                                             │
│   ┌───────────┐    scrape    ┌──────────────┐              │
│   │ LB-1..LB-N│ ──────────→ │  Prometheus   │              │
│   └───────────┘              └──────┬───────┘              │
│                                     │ query                 │
│                              ┌──────▼───────┐              │
│                              │  Orchestrator │              │
│                              │  (ScaleLogic) │              │
│                              └──┬─────────┬─┘              │
│                                 │         │                 │
│                          scale up│    scale│down            │
│                                 ▼         ▼                 │
│                          ┌──────────┐ ┌────────────┐       │
│                          │Provision │ │  Drain LB   │       │
│                          │ new LB   │ │  withdraw   │       │
│                          │ from pool│ │  BGP route  │       │
│                          └────┬─────┘ └─────┬──────┘       │
│                               │             │               │
│                          sync │config  wait │for drain      │
│                               │             │               │
│                          ┌────▼─────┐ ┌─────▼──────┐       │
│                          │Announce  │ │  Return to  │       │
│                          │VIP (BGP) │ │  warm pool  │       │
│                          └──────────┘ └────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Key Tooling (No Cloud Vendor Lock-in)

| Function | Cloud-Independent Tool | What It Does |
|---|---|---|
| **VM Provisioning** | libvirt + QEMU, OpenStack Nova, Proxmox | Create/destroy VMs on bare metal |
| **Config Management** | Ansible, SaltStack, Puppet | Install LB software, push configs |
| **Service Discovery** | Consul, etcd | LBs register themselves; orchestrator discovers them |
| **BGP Daemon** | BIRD, FRRouting, ExaBGP | Advertise/withdraw VIP routes |
| **Metrics** | Prometheus + Alertmanager | Collect LB metrics, fire scaling alerts |
| **Orchestration** | Nomad, Kubernetes (bare-metal), custom | Schedule LB workloads, manage lifecycle |
| **Image Building** | Packer | Pre-bake LB machine images for fast boot |

### Connection Resilience During Scaling

```
Why connections DON'T break when LBs are added/removed:

Layer 1: ECMP hash changes → some flows move to a different LB
Layer 2: New LB has no connection table entry for moved flow
Layer 3: LB falls back to Maglev hash table lookup
Layer 4: Maglev consistent hashing gives the SAME backend as before
          (because the backend set hasn't changed)
Layer 5: Packet reaches correct backend → TCP connection continues

The ONLY case connections break:
  - Backend was removed AND the flow moved to a new LB simultaneously
  - Extremely rare; Maglev hash minimizes both probabilities
```

---

## Comparison: Hardware vs Software Load Balancer

| Aspect | Hardware LB (F5, Citrix) | Software LB (Maglev, LVS, Envoy) |
|---|---|---|
| **Cost** | $$$$ (proprietary appliances) | $ (commodity servers) |
| **Scalability** | Vertical (buy a bigger box) | Horizontal (add more servers) |
| **Flexibility** | Vendor-locked features | Fully customizable |
| **Deployment** | Physical rack-and-stack | Container/VM, instant spin-up |
| **Throughput** | High (ASICs) | Very high (kernel bypass, DPDK) |
| **Failure domain** | Single appliance = SPOF unless HA pair | N machines, lose any subset |

---

## Further Reading

- **Maglev Paper:** *Maglev: A Fast and Reliable Software Network Load Balancer* (Google, NSDI 2016)
- **Consistent Hashing:** Karger et al., 1997 — the foundation for Maglev hashing
- **ECMP:** RFC 2992 — how routers distribute traffic across equal-cost paths
- **BGP Anycast:** How CDNs and DNS providers route to nearest server
- **DPDK:** Data Plane Development Kit — kernel bypass for line-rate packet processing
- **Envoy Proxy:** Modern L7 load balancer (complements L4 Maglev)
