# Kubernetes Internals — How Everything Actually Works

> This doc answers: "But what happens UNDER THE HOOD?"
> Trace every packet, every API call, every scheduling decision.
> Read this after the beginner guide to build deep conceptual understanding.

---

## Table of Contents

1. [What Happens When You Run kubectl apply](#1-what-happens-when-you-run-kubectl-apply)
2. [How a Pod Gets Scheduled — The Full Journey](#2-how-a-pod-gets-scheduled)
3. [How Networking Works — Packet by Packet](#3-how-networking-works)
4. [How a Request Reaches Your App — End to End](#4-how-a-request-reaches-your-app)
5. [How DNS Works Inside Kubernetes](#5-how-dns-works)
6. [How Services Work — iptables, IPVS, and eBPF](#6-how-services-work)
7. [How Scaling Actually Happens](#7-how-scaling-actually-happens)
8. [How Rolling Updates Work — Step by Step](#8-how-rolling-updates-work)
9. [How Self-Healing Works](#9-how-self-healing-works)
10. [How Storage Gets Attached](#10-how-storage-gets-attached)
11. [How etcd Stores Everything](#11-how-etcd-stores-everything)
12. [The Controller Pattern — The Heart of Kubernetes](#12-the-controller-pattern)
13. [How Networking Across Nodes Works — CNI Deep Dive](#13-cni-deep-dive)
14. [How Ingress Actually Routes Traffic](#14-how-ingress-routes-traffic)
15. [How Pod-to-Pod Communication Works](#15-pod-to-pod-communication)
16. [How Resource Scheduling Decisions Are Made](#16-resource-scheduling)
17. [The Full Lifecycle of a Pod — Birth to Death](#17-full-pod-lifecycle)
18. [How the Control Plane Stays Alive](#18-control-plane-ha)

---

## 1. What Happens When You Run kubectl apply

You type `kubectl apply -f deployment.yaml` and hit Enter. Here's every step:

```
Your Terminal                         Kubernetes Cluster
─────────────                         ──────────────────

1. kubectl reads deployment.yaml
   Parses YAML into JSON
   
2. kubectl checks: ~/.kube/config
   Finds: API server address, auth token/cert
   
3. kubectl sends HTTPS POST to API server
   POST https://api-server:6443/apis/apps/v1/namespaces/default/deployments
   Body: { the deployment JSON }
   Headers: Authorization: Bearer <token>
   
                                      4. API SERVER receives request
                                      
                                      5. AUTHENTICATION
                                         "Who is this?"
                                         Checks: X.509 cert, bearer token, 
                                         or OIDC token
                                         Result: "This is user: kjana"
                                      
                                      6. AUTHORIZATION (RBAC)
                                         "Can kjana create deployments 
                                          in namespace default?"
                                         Checks Role/ClusterRole bindings
                                         Result: "Yes, allowed"
                                      
                                      7. ADMISSION CONTROLLERS
                                         Mutating webhooks run first:
                                           - Add default labels
                                           - Inject sidecar (Istio)
                                           - Set default resource limits
                                         
                                         Validation:
                                           - Schema validation (valid YAML?)
                                           - Required fields present?
                                         
                                         Validating webhooks:
                                           - Kyverno: "Does it have team label?"
                                           - OPA: "Is the image from allowed registry?"
                                         
                                         Any rejection → 403 back to kubectl
                                      
                                      8. WRITE TO ETCD
                                         API server writes the Deployment 
                                         object to etcd with a resourceVersion
                                      
                                      9. API server returns 201 Created
   
10. kubectl prints:
    "deployment.apps/my-app created"
    
                                      10. WHAT HAPPENS NEXT (async):
                                          See section 2...
```

### The Key Insight

```
kubectl does NOT create Pods.
kubectl does NOT talk to nodes.
kubectl ONLY talks to the API server.

The API server ONLY writes to etcd.
It doesn't start containers or schedule anything.

Everything else happens through CONTROLLERS watching etcd for changes.
This is called the "watch-and-reconcile" pattern.
```

---

## 2. How a Pod Gets Scheduled

After the Deployment object lands in etcd, here's what happens:

```
TIME    COMPONENT                ACTION
────    ─────────                ──────

0ms     API Server               Deployment object written to etcd
                                 Event: "Deployment my-app ADDED"

10ms    Deployment Controller    Watching for Deployment events
                                 Sees: "my-app wants 3 replicas"
                                 Creates: ReplicaSet object
                                 Writes: ReplicaSet to etcd via API server

20ms    ReplicaSet Controller    Watching for ReplicaSet events  
                                 Sees: "ReplicaSet wants 3 Pods, has 0"
                                 Creates: 3 Pod objects (with NO nodeName)
                                 Writes: 3 Pods to etcd via API server

30ms    Scheduler                Watching for Pods with nodeName=""
                                 Sees: 3 unscheduled Pods
                                 For EACH Pod:

        ┌─────────────────────────────────────────────────────────┐
        │              SCHEDULING CYCLE (per Pod)                   │
        │                                                          │
        │  STEP 1: FILTERING (which nodes CAN run this Pod?)      │
        │    ✓ Node has enough CPU?     (check resource requests) │
        │    ✓ Node has enough memory?                            │
        │    ✓ Node matches nodeSelector?                         │
        │    ✓ Pod tolerates node taints?                         │
        │    ✓ Node affinity satisfied?                           │
        │    ✓ PVC available in node's zone?                      │
        │    ✓ Port not already in use?                           │
        │                                                          │
        │    Input:  5 nodes                                       │
        │    Output: 3 feasible nodes (2 filtered out)            │
        │                                                          │
        │  STEP 2: SCORING (which node is BEST?)                  │
        │    Score each feasible node 0-100:                      │
        │    - LeastRequestedPriority: prefer less loaded nodes   │
        │    - BalancedResourceAllocation: prefer balanced CPU/mem│
        │    - InterPodAffinity: prefer/avoid certain pods nearby │
        │    - TopologySpread: spread evenly across zones         │
        │                                                          │
        │    Node A: 85 points                                     │
        │    Node B: 72 points                                     │
        │    Node C: 91 points  ← WINNER                          │
        │                                                          │
        │  STEP 3: BINDING                                         │
        │    Write: Pod.spec.nodeName = "Node C"                  │
        │    Write to etcd via API server                         │
        └─────────────────────────────────────────────────────────┘

50ms    kubelet (on Node C)      Watching for Pods assigned to "Node C"
                                 Sees: "Pod my-app-abc assigned to me"

60ms    kubelet                  Calls CRI (Container Runtime Interface)
                                 → containerd: "Pull image myapp:2.0"

        containerd               Pulls image layers from registry
                                 (if not already cached)
                                 Could take 1-30 seconds depending on size

5s      kubelet                  Calls CRI → containerd
                                 "Create and start container"
                                 containerd → runc → starts the process

5.1s    kubelet                  Calls CNI (Container Network Interface)
                                 → Calico/Cilium/AWS VPC CNI
                                 "Give this Pod an IP address"
                                 
                                 CNI plugin:
                                   1. Creates a veth pair (virtual ethernet)
                                   2. Attaches one end to Pod network namespace
                                   3. Attaches other end to host bridge/interface
                                   4. Assigns IP: 10.244.3.15
                                   5. Sets up routing rules

5.2s    kubelet                  Calls CSI (Container Storage Interface)
                                 "Mount any volumes this Pod needs"
                                 → EBS CSI driver attaches the disk

5.5s    kubelet                  Runs STARTUP PROBE (if configured)
                                 HTTP GET http://10.244.3.15:8080/healthz
                                 Waits until it passes...

8s      kubelet                  Startup probe passed!
                                 Starts LIVENESS and READINESS probes

8.5s    kubelet                  Readiness probe passes
                                 Updates Pod status: Ready=True
                                 Writes status to API server → etcd

8.6s    Endpoint Controller      Watching for Pod status changes
                                 Sees: "Pod 10.244.3.15 is Ready"
                                 Adds IP to Endpoints for the Service
                                 Writes to API server → etcd

8.7s    kube-proxy (all nodes)   Watching for Endpoint changes
                                 Sees: "New endpoint 10.244.3.15 for service my-app"
                                 Updates iptables/IPVS rules on EVERY node
                                 Now traffic to Service VIP → includes this Pod

9s      DONE                     Pod is running, healthy, and receiving traffic
```

### The Key Insight

```
Nobody "starts" the Pod directly. 
It's a chain of controllers, each doing one small job:

  Deployment controller  → creates ReplicaSet
  ReplicaSet controller  → creates Pods
  Scheduler              → assigns Pod to a node
  kubelet                → starts the container
  Endpoint controller    → adds Pod to Service
  kube-proxy             → updates routing rules

Each controller watches etcd and reacts to changes.
They don't talk to each other directly.
They communicate through etcd (via the API server).
```

---

## 3. How Networking Works

### The Fundamental Rules

```
Kubernetes networking has 3 simple rules:

  1. Every Pod gets its own unique IP address
  2. Pods can talk to any other Pod using its IP (no NAT)
  3. Pods on the same node and different nodes can communicate

This is different from Docker:
  Docker: containers on different hosts can't talk without port mapping
  K8s:    ANY pod can reach ANY other pod by IP, on ANY node
```

### Network Namespaces

```
Each Pod gets its own Linux network namespace.
Think of it as a private little network for that Pod.

┌──────────── Node (Host) ────────────────────────────┐
│                                                       │
│  Host Network Namespace                              │
│  eth0: 192.168.1.10 (node IP)                       │
│                                                       │
│  ┌─── Pod A Namespace ───┐  ┌─── Pod B Namespace ───┐│
│  │ eth0: 10.244.0.5      │  │ eth0: 10.244.0.6      ││
│  │                       │  │                       ││
│  │ [container 1]         │  │ [container 1]         ││
│  │ [container 2]         │  │ [container 2]         ││
│  │ (share localhost)     │  │ (share localhost)     ││
│  └───────┬───────────────┘  └───────┬───────────────┘│
│          │veth pair                  │veth pair       │
│          └──────────┬───────────────┘                │
│                     │                                 │
│              ┌──────▼──────┐                         │
│              │  cbr0/cni0  │  ← bridge               │
│              │  (or eBPF)  │                         │
│              └─────────────┘                         │
└──────────────────────────────────────────────────────┘

Inside a Pod:
  - All containers share the SAME network namespace
  - Container 1 can reach container 2 on localhost:port
  - They share the same IP address (10.244.0.5)

Between Pods on the SAME node:
  - Packet goes: Pod A → veth → bridge → veth → Pod B
  - It's just a bridge hop (very fast, microseconds)
```

### Cross-Node Communication

```
Pod A on Node 1 (10.244.0.5) wants to reach Pod B on Node 2 (10.244.1.8):

Node 1 (192.168.1.10)                    Node 2 (192.168.1.11)
┌──────────────────────┐                 ┌──────────────────────┐
│                      │                 │                      │
│  Pod A               │                 │  Pod B               │
│  10.244.0.5          │                 │  10.244.1.8          │
│     │                │                 │     ▲                │
│     ▼                │                 │     │                │
│  veth → bridge       │                 │  bridge → veth       │
│     │                │                 │     ▲                │
│     ▼                │                 │     │                │
│  routing table:      │                 │  routing table:      │
│  10.244.1.0/24       │                 │  decapsulate         │
│  → via 192.168.1.11  │                 │  → deliver to bridge │
│     │                │                 │     ▲                │
│     ▼                │                 │     │                │
│  ENCAPSULATE         │    network      │  DECAPSULATE         │
│  (VXLAN/GENEVE/IPinIP│ ──────────────► │  unwrap original     │
│   wrap in outer pkt) │                 │  packet              │
│     │                │                 │     ▲                │
│     ▼                │                 │     │                │
│  eth0: 192.168.1.10  │                 │  eth0: 192.168.1.11  │
└──────────────────────┘                 └──────────────────────┘

The overlay network (VXLAN example):
  Original packet: src=10.244.0.5 dst=10.244.1.8
  
  Gets wrapped in an outer packet:
  ┌─────────────────────────────────────────────────┐
  │ Outer IP: src=192.168.1.10  dst=192.168.1.11   │
  │ UDP port 4789 (VXLAN)                           │
  │ ┌───────────────────────────────────────────┐   │
  │ │ Inner: src=10.244.0.5  dst=10.244.1.8    │   │
  │ │ TCP port 8080                              │   │
  │ │ HTTP GET /api/orders                       │   │
  │ └───────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────┘
  
  Node 2 decapsulates → delivers the inner packet to Pod B.

Alternative (no overlay): BGP routing
  Each node advertises: "I own 10.244.1.0/24"
  Network routers learn these routes
  No encapsulation overhead — faster
  Requires BGP-capable network (Calico BGP mode)
```

---

## 4. How a Request Reaches Your App

A user at `https://api.myapp.com/orders` hits Enter. Trace every hop:

```
USER'S BROWSER
    │
    │ 1. DNS LOOKUP: api.myapp.com → 52.14.88.100 (cloud LB IP)
    │    (Route53 / Cloudflare / etc.)
    │
    ▼
CLOUD LOAD BALANCER (AWS ALB / NLB)
    │  IP: 52.14.88.100
    │
    │ 2. TLS TERMINATION
    │    Decrypt HTTPS → HTTP
    │    (using ACM certificate)
    │
    │ 3. HEALTH CHECK
    │    ALB knows which target nodes are healthy
    │    (checks NodePort or target Pod IP)
    │
    │ 4. FORWARD TO NODE
    │    Picks a healthy node: 192.168.1.10:30080 (NodePort)
    │    OR directly to Pod IP: 10.244.0.5:8080 (target type: ip)
    │
    ▼
NODE (192.168.1.10)
    │
    │ 5. IPTABLES / IPVS (kube-proxy rules)
    │    The packet arrives at the Service's NodePort (30080)
    │    iptables rule: "NodePort 30080 → Service VIP 10.96.45.123"
    │    
    │    DNAT (Destination NAT):
    │    Original:  dst=192.168.1.10:30080
    │    Rewritten: dst=10.244.2.8:8080 (a random healthy Pod IP)
    │    
    │    How the Pod was chosen:
    │    iptables -t nat -L KUBE-SVC-xxx
    │    → 33% chance: Pod 10.244.0.5:8080
    │    → 33% chance: Pod 10.244.1.3:8080
    │    → 33% chance: Pod 10.244.2.8:8080  ← selected
    │
    │ 6. ROUTING
    │    Is 10.244.2.8 on this node? No.
    │    Routing table: 10.244.2.0/24 via 192.168.1.12 (Node 3)
    │    Encapsulate and forward to Node 3
    │
    ▼
NODE 3 (192.168.1.12)
    │
    │ 7. DECAPSULATE
    │    Strip outer packet headers
    │    Inner packet: dst=10.244.2.8:8080
    │
    │ 8. BRIDGE ROUTING
    │    10.244.2.8 is a local Pod
    │    Forward via veth pair to Pod's network namespace
    │
    ▼
POD (10.244.2.8)
    │
    │ 9. ISTIO SIDECAR (if service mesh enabled)
    │    Envoy proxy intercepts (iptables redirect port 15006)
    │    mTLS decryption
    │    L7 routing rules (VirtualService)
    │    Metrics collected
    │    Forward to localhost:8080
    │
    ▼
YOUR APPLICATION CONTAINER
    │
    │ 10. APP PROCESSES REQUEST
    │     GET /orders → query database → return JSON
    │
    │ 11. RESPONSE TRAVELS BACK
    │     Same path in reverse:
    │     App → (Envoy) → Pod net ns → veth → bridge → 
    │     encapsulate → Node 1 → un-DNAT → cloud LB → 
    │     TLS encrypt → user's browser
    │
    ▼
USER SEES: {"orders": [...]}

Total time: 5-50ms (depending on network and app latency)
```

### With Cilium (eBPF) — The Fast Path

```
With Cilium replacing kube-proxy, steps 5-6 change:

Instead of:
  Packet → iptables chain traversal (O(n) rules) → DNAT → routing

It becomes:
  Packet → eBPF program in kernel (O(1) hash lookup) → DNAT → routing

For a cluster with 10,000 services:
  iptables: traverse ~30,000 rules per packet
  eBPF:     single hash table lookup

That's why FAANG companies use Cilium at scale.
```

---

## 5. How DNS Works

### CoreDNS — The Cluster DNS Server

```
CoreDNS runs as a Deployment in kube-system namespace (usually 2 replicas).
Every Pod is configured to use CoreDNS for DNS resolution.

When a Pod starts, kubelet injects this into /etc/resolv.conf:
  nameserver 10.96.0.10          ← CoreDNS Service IP
  search default.svc.cluster.local svc.cluster.local cluster.local
  options ndots:5
```

### DNS Resolution Step by Step

```
Your app runs: curl http://payment-service

Step 1: App calls getaddrinfo("payment-service")
Step 2: Resolver reads /etc/resolv.conf
Step 3: ndots:5 → "payment-service" has 0 dots (< 5)
        So it's treated as a relative name
Step 4: Resolver appends search domains and tries IN ORDER:

  Query 1: payment-service.default.svc.cluster.local  → FOUND! 10.96.80.45
  (if not found, would try:)
  Query 2: payment-service.svc.cluster.local
  Query 3: payment-service.cluster.local
  Query 4: payment-service  (absolute, forward to upstream DNS)

Step 5: CoreDNS receives the query
        Checks its in-memory cache of all Services
        Finds: Service "payment-service" in namespace "default"
        Returns: A record → 10.96.80.45 (ClusterIP)

Step 6: App now has the IP, makes TCP connection to 10.96.80.45:80
```

### DNS for Different Object Types

```
Regular Service (ClusterIP):
  payment-service.default.svc.cluster.local → 10.96.80.45 (VIP)
  
Headless Service (clusterIP: None):
  postgres.default.svc.cluster.local → 10.244.0.5, 10.244.1.3, 10.244.2.8
  Returns ALL Pod IPs (client-side load balancing)

StatefulSet Pod:
  postgres-0.postgres.default.svc.cluster.local → 10.244.0.5
  postgres-1.postgres.default.svc.cluster.local → 10.244.1.3
  Each Pod gets a STABLE DNS name

ExternalName Service:
  my-database.default.svc.cluster.local → CNAME → rds.amazonaws.com
  DNS alias to an external service

SRV Records:
  _http._tcp.payment-service.default.svc.cluster.local
  Returns: port 80, host payment-service.default.svc.cluster.local
  Used by: gRPC client-side load balancing
```

### The ndots Problem

```
ndots:5 means: if a name has fewer than 5 dots, try search domains first.

curl http://api.stripe.com  (2 dots, < 5)
  Query 1: api.stripe.com.default.svc.cluster.local       → NXDOMAIN
  Query 2: api.stripe.com.svc.cluster.local                → NXDOMAIN
  Query 3: api.stripe.com.cluster.local                    → NXDOMAIN
  Query 4: api.stripe.com                                  → FOUND!

That's 4 wasted DNS queries for every external domain!
At scale (1000s of pods), this adds significant DNS load.

Fix: Use FQDN with trailing dot:
  curl http://api.stripe.com.    ← trailing dot = absolute name
  Only 1 query, directly to api.stripe.com

Fix 2: Reduce ndots in Pod spec:
  dnsConfig:
    options:
    - name: ndots
      value: "2"
```

---

## 6. How Services Work

### ClusterIP — Under the Hood

```
When you create a Service:

apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080

Kubernetes:
  1. Allocates a Virtual IP (VIP): 10.96.45.123
     This IP doesn't belong to any interface — it's "virtual"
  2. Creates an Endpoints object listing all matching Pod IPs
  3. kube-proxy on EVERY node creates iptables/IPVS rules

The VIP 10.96.45.123 doesn't actually exist on any node.
It only exists in iptables rules that intercept and redirect packets.
```

### iptables Mode (Default)

```
kube-proxy creates these iptables rules (simplified):

# 1. Intercept packets to Service VIP
-A KUBE-SERVICES -d 10.96.45.123/32 -p tcp --dport 80 \
  -j KUBE-SVC-XXXXXX

# 2. Load balance across Pods (random probability)
-A KUBE-SVC-XXXXXX -m statistic --mode random --probability 0.33333 \
  -j KUBE-SEP-AAAAAA    # → Pod 1

-A KUBE-SVC-XXXXXX -m statistic --mode random --probability 0.50000 \
  -j KUBE-SEP-BBBBBB    # → Pod 2

-A KUBE-SVC-XXXXXX \
  -j KUBE-SEP-CCCCCC    # → Pod 3 (catch-all)

# 3. DNAT (rewrite destination IP to Pod IP)
-A KUBE-SEP-AAAAAA -p tcp \
  -j DNAT --to-destination 10.244.0.5:8080

-A KUBE-SEP-BBBBBB -p tcp \
  -j DNAT --to-destination 10.244.1.3:8080

-A KUBE-SEP-CCCCCC -p tcp \
  -j DNAT --to-destination 10.244.2.8:8080

What happens when a packet arrives:
  Packet: src=10.244.3.1 dst=10.96.45.123:80
  → Match KUBE-SERVICES rule
  → Random: picks KUBE-SEP-BBBBBB (Pod 2)
  → DNAT: rewrite dst to 10.244.1.3:8080
  → Packet: src=10.244.3.1 dst=10.244.1.3:8080
  → Routed to Pod 2

The reverse (response):
  Packet: src=10.244.1.3:8080 dst=10.244.3.1
  → conntrack table remembers the DNAT
  → un-DNAT: rewrite src to 10.96.45.123:80
  → Packet: src=10.96.45.123:80 dst=10.244.3.1
  → Client sees response from the Service VIP (never knows about Pod 2)
```

### IPVS Mode (Better at Scale)

```
IPVS (IP Virtual Server): kernel-level Layer 4 load balancer

Instead of iptables chains:
  IPVS creates a virtual server entry:
    VIP 10.96.45.123:80 → rr (round-robin)
      → 10.244.0.5:8080  weight=1
      → 10.244.1.3:8080  weight=1
      → 10.244.2.8:8080  weight=1

Why IPVS is better:
  iptables: O(n) — traverses chains linearly. 10,000 services = 30,000+ rules
  IPVS:     O(1) — hash table lookup. 10,000 services = same speed

  iptables: only random/round-robin
  IPVS:     supports rr, lc (least connections), wrr (weighted), sh (source hash)

Enable: kube-proxy --proxy-mode=ipvs
```

### eBPF Mode (Cilium — Fastest)

```
eBPF bypasses the entire iptables/netfilter stack.

An eBPF program is attached to the TC (traffic control) hook
or socket hooks in the kernel.

When a packet arrives:
  1. eBPF program runs IN THE KERNEL
  2. Looks up Service VIP in an eBPF map (hash table)
  3. Rewrites destination to Pod IP
  4. Forwards packet directly
  
No iptables traversal. No IPVS. Just a kernel program.

Performance comparison for 10,000 services:
  iptables:  ~5ms overhead per connection setup
  IPVS:     ~0.5ms overhead
  eBPF:     ~0.05ms overhead (100x faster than iptables)
```

---

## 7. How Scaling Actually Happens

### HPA Decision Loop

```
Every 15 seconds (configurable), the HPA controller runs:

┌──────────────────────────────────────────────────────────────┐
│                     HPA CONTROL LOOP                          │
│                                                               │
│  1. COLLECT METRICS                                           │
│     Query metrics-server API:                                │
│     GET /apis/metrics.k8s.io/v1beta1/pods?labelSelector=app=api
│                                                               │
│     Response:                                                 │
│       Pod api-abc: CPU 180m (of 250m request = 72%)          │
│       Pod api-def: CPU 210m (of 250m request = 84%)          │
│       Pod api-ghi: CPU 195m (of 250m request = 78%)          │
│                                                               │
│  2. CALCULATE DESIRED REPLICAS                                │
│                                                               │
│     currentMetricValue = avg(72%, 84%, 78%) = 78%            │
│     targetUtilization = 70%                                   │
│                                                               │
│     desiredReplicas = ceil(currentReplicas × (current/target))│
│     desiredReplicas = ceil(3 × (78/70))                      │
│     desiredReplicas = ceil(3 × 1.114)                        │
│     desiredReplicas = ceil(3.34)                             │
│     desiredReplicas = 4                                       │
│                                                               │
│  3. APPLY STABILIZATION                                       │
│     Scale UP window:   60s  (must want more for 60s)         │
│     Scale DOWN window: 300s (must want fewer for 5 min)      │
│                                                               │
│     Scale down is slow (avoid flapping).                      │
│     Scale up is fast (respond to load).                       │
│                                                               │
│  4. APPLY POLICIES                                            │
│     Max scale-up per minute: 4 pods OR 100%                  │
│     Max scale-down per 2 min: 2 pods                         │
│                                                               │
│  5. APPLY BOUNDS                                              │
│     desiredReplicas = max(minReplicas, min(maxReplicas, 4))  │
│     desiredReplicas = max(3, min(20, 4)) = 4                 │
│                                                               │
│  6. SCALE                                                     │
│     PATCH /apis/apps/v1/deployments/api                      │
│     {"spec": {"replicas": 4}}                                │
│                                                               │
│  7. NEW POD CREATION (same flow as Section 2)                │
│     Deployment controller → ReplicaSet → Scheduler →          │
│     kubelet → container starts → probes pass →                │
│     Endpoint added → iptables updated → traffic arrives       │
│                                                               │
│     Time from scale decision to serving traffic: 5-30 seconds │
└──────────────────────────────────────────────────────────────┘
```

### Where Metrics Come From

```
kubelet (on each node)
    │
    │ cAdvisor (built into kubelet) collects container metrics:
    │   CPU usage (from cgroups)
    │   Memory usage (from cgroups)
    │   Network I/O
    │   Disk I/O
    │
    ▼
metrics-server (cluster-wide)
    │
    │ Scrapes /stats/summary from every kubelet every 15s
    │ Stores last few minutes in memory (not persistent)
    │ Exposes via Kubernetes API:
    │   /apis/metrics.k8s.io/v1beta1/pods
    │   /apis/metrics.k8s.io/v1beta1/nodes
    │
    ▼
HPA controller
    │
    │ Queries metrics-server every 15s
    │ Calculates desired replicas
    │ Patches Deployment
    
For custom metrics (HTTP requests/sec, queue depth):
  App → Prometheus → prometheus-adapter → 
  /apis/custom.metrics.k8s.io → HPA

For external metrics (SQS queue depth, CloudWatch):
  AWS → KEDA → ScaledObject → HPA
```

### Cluster Autoscaler / Karpenter — Node Scaling

```
Pod scaling (HPA) happens FIRST.
Node scaling happens SECOND, triggered by unschedulable Pods.

Timeline:
  0s:   HPA decides to scale from 5 → 15 Pods
  1s:   Deployment creates 10 new Pods
  2s:   Scheduler tries to place 10 new Pods
        Can place 6 on existing nodes
        4 Pods are Pending (not enough resources)
  
  5s:   Cluster Autoscaler / Karpenter sees Pending Pods
  
  Cluster Autoscaler (traditional):
    Checks ASG configs → which ASG can fit these Pods?
    Calls AWS ASG API: "Scale up ASG from 5 → 7 nodes"
    AWS launches 2 new EC2 instances
    Instances boot, install kubelet, join cluster
    Time to ready: 2-5 minutes
  
  Karpenter (modern):
    Analyzes Pod requirements (CPU, memory, GPU, arch)
    Calls EC2 Fleet API directly (skips ASG)
    Selects cheapest instance type that fits
    Provisions node
    Time to ready: 30-90 seconds (much faster)

  Once new nodes join:
    Scheduler places the 4 Pending Pods on new nodes
    They start, pass probes, get Endpoints, receive traffic
```

---

## 8. How Rolling Updates Work

```
Current state: Deployment "api" with replicas=3, image=v1

You run: kubectl set image deployment/api web=myapp:v2

┌──────────────────────────────────────────────────────────────────┐
│                     ROLLING UPDATE SEQUENCE                        │
│                                                                   │
│  maxUnavailable: 0  (never kill a pod before new one is ready)   │
│  maxSurge: 1        (allow 1 extra pod during rollout)           │
│                                                                   │
│  Time  ReplicaSet-v1   ReplicaSet-v2   Total Ready  Traffic      │
│  ────  ──────────────  ──────────────  ───────────  ──────────── │
│                                                                   │
│  0s    [v1] [v1] [v1]                 3/3          100% → v1     │
│        Deployment sees image changed.                             │
│        Creates NEW ReplicaSet-v2 (replicas=1)                    │
│                                                                   │
│  1s    [v1] [v1] [v1]  [v2 starting]  3/3          100% → v1     │
│        v2 Pod is starting (pulling image, running init)          │
│                                                                   │
│  8s    [v1] [v1] [v1]  [v2 ✓ ready]   4/4          75%→v1 25%→v2│
│        v2 Pod passes readiness probe!                            │
│        Deployment scales down v1: replicas 3→2                   │
│                                                                   │
│  9s    [v1] [v1]        [v2 ✓]         3/3          66%→v1 33%→v2│
│        One v1 Pod terminating (gets SIGTERM, drains connections) │
│        Deployment scales up v2: replicas 1→2                     │
│                                                                   │
│  17s   [v1] [v1]        [v2 ✓] [v2 ✓]  4/4         50%→v1 50%→v2│
│        New v2 Pod ready. Scale down v1: 2→1                      │
│                                                                   │
│  18s   [v1]             [v2 ✓] [v2 ✓]  3/3         33%→v1 66%→v2│
│        Scale up v2: 2→3                                          │
│                                                                   │
│  26s   [v1]        [v2 ✓] [v2 ✓] [v2 ✓] 4/4       25%→v1 75%→v2│
│        v2 ready. Scale down v1: 1→0                              │
│                                                                   │
│  27s                [v2 ✓] [v2 ✓] [v2 ✓] 3/3       100% → v2    │
│        DONE! Old ReplicaSet kept (for rollback) but has 0 Pods.  │
│                                                                   │
│  What happens during "terminating":                               │
│    1. Pod marked Terminating                                      │
│    2. Endpoints controller removes Pod IP from Service            │
│    3. preStop hook runs (sleep 5 — wait for iptables propagation)│
│    4. SIGTERM sent to PID 1                                       │
│    5. App has terminationGracePeriodSeconds to finish requests    │
│    6. If not exited → SIGKILL                                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. How Self-Healing Works

### Node Failure

```
Node 2 loses power at T=0.

0s      Node 2 goes offline
        kubelet stops sending heartbeats to API server
        
40s     Node controller notices: "Node 2 missed heartbeat"
        Marks node: condition=NotReady
        (default: node-monitor-grace-period = 40s)

5m      Node controller adds taint:
        node.kubernetes.io/unreachable:NoExecute
        (default: pod-eviction-timeout = 5m)
        
        All Pods on Node 2 that DON'T tolerate this taint
        are marked for eviction.

5m 1s   ReplicaSet controller sees: 
        "I want 3 Pods, but only 2 are healthy"
        Creates new Pod (assigned to Node 1 or Node 3 by scheduler)

5m 10s  New Pod starts, passes probes, gets traffic.
        Service Endpoints updated.
        Users never noticed (other 2 Pods were serving traffic).

Note: Pods with tolerationSeconds on the unreachable taint
      can wait longer before eviction (useful for transient network issues).
```

### Container Crash

```
App process exits with code 1 (crash) at T=0.

0ms     Container exits. 
        kubelet detects: containerStatuses.state = Terminated

0ms     kubelet applies restartPolicy:
        - Always:     restart immediately (Deployments)
        - OnFailure:  restart because exit code != 0 (Jobs)
        - Never:      don't restart (debug pods)

100ms   kubelet restarts container using CRI (containerd)
        Same Pod, same IP, same node, same volumes.
        restartCount increments.

500ms   Container starts.
        Startup probe begins.

5s      Probes pass. Pod is Ready again.
        (If readiness was failing, Endpoints were removed during crash)
        Endpoints restored. Traffic resumes.

Crash Loop:
  If container keeps crashing, kubelet applies exponential backoff:
  Restart 1: immediate
  Restart 2: wait 10s
  Restart 3: wait 20s
  Restart 4: wait 40s
  Restart 5: wait 80s
  ...
  Max: wait 5 minutes between restarts
  
  Status shows: CrashLoopBackOff
  
  kubelet never gives up. It keeps trying forever.
  (Until you fix the bug or delete the Pod.)
```

### Liveness Probe Failure

```
App is alive but deadlocked (thread pool exhausted, infinite loop, etc.)

Every 10s: kubelet sends: GET /healthz → timeout (no response)

0s:   Probe attempt 1 → timeout (fail)
10s:  Probe attempt 2 → timeout (fail)
20s:  Probe attempt 3 → timeout (fail)  ← failureThreshold: 3

20s:  kubelet KILLS the container (not the Pod)
      Container restarted within the same Pod (same IP, same volumes)
      
25s:  Container starts, fresh process
      Application initializes, connections restored

30s:  Readiness probe passes → traffic resumes
```

---

## 10. How Storage Gets Attached

```
Pod with PVC starts on Node 2.

1. Scheduler sees Pod needs PVC "my-data"
   Checks: is PVC bound? Is the PV in a zone Node 2 can access?
   (WaitForFirstConsumer: PV provisioned in same zone as Pod)

2. CSI controller (external-provisioner) sees unbound PVC
   Calls cloud API: aws ec2 create-volume --size 100 --type gp3 --az us-east-1a
   Creates PV object representing the EBS volume

3. PV controller binds PVC to PV
   PVC status: Bound

4. kubelet on Node 2 sees Pod needs volume
   Calls CSI driver: ControllerPublishVolume
   → aws ec2 attach-volume (attaches EBS to EC2 instance)

5. kubelet calls CSI: NodeStageVolume
   → formats the block device (mkfs.ext4) if first time
   → mounts to a staging directory

6. kubelet calls CSI: NodePublishVolume
   → bind-mounts from staging to Pod's container directory
   → /var/lib/kubelet/pods/<pod-id>/volumes/ → container sees /app/data

7. Pod container starts with volume mounted at /app/data
   Data persists across container restarts.
   Data persists if Pod is rescheduled to SAME node.
   
   If Pod moves to another node:
   1. Volume detaches from old node
   2. Attaches to new node
   3. Mounts in new Pod
   (This is why ReadWriteOnce = only one node at a time for block storage)
```

---

## 11. How etcd Stores Everything

```
etcd is a distributed key-value store.
EVERY Kubernetes object is a key in etcd.

Key format: /registry/<resource-type>/<namespace>/<name>

Examples:
  /registry/pods/default/my-app-abc-123
  /registry/deployments/production/api
  /registry/services/specs/default/my-app
  /registry/secrets/production/db-password
  /registry/configmaps/default/app-config

Value: the full JSON of the Kubernetes object

Size:
  Typical cluster: 100MB - 2GB in etcd
  Max object size: 1.5MB (etcd limit)
  Max total size: recommended < 8GB

How watches work:
  Client: "Watch /registry/pods/default/ starting from revision 4521"
  etcd:   sends events for every change after revision 4521
          ADDED, MODIFIED, DELETED
  
  This is how controllers stay in sync without polling.
  
  If a controller restarts:
    1. List all objects (GET /registry/pods/)
    2. Note the resourceVersion
    3. Watch from that version (incremental updates)
    No data missed, no duplicates.

Consistency:
  etcd uses Raft consensus (majority must agree)
  3 etcd nodes: 2 must agree (tolerates 1 failure)
  5 etcd nodes: 3 must agree (tolerates 2 failures)
  
  All reads from the leader (linearizable)
  OR from followers (slightly stale but faster)
  API server uses leader reads for writes, follower reads for watches.
```

---

## 12. The Controller Pattern

```
EVERY automation in Kubernetes follows this pattern:

┌─────────────────────────────────────────────────────────┐
│                    CONTROLLER LOOP                        │
│                                                          │
│  1. OBSERVE: Watch for events (via API server / etcd)   │
│                                                          │
│  2. COMPARE: desired state vs actual state               │
│     desired state = what's in the spec                   │
│     actual state  = what's running in the cluster        │
│                                                          │
│  3. ACT: take action to close the gap                    │
│     Too few pods? Create more.                           │
│     Too many pods? Delete some.                          │
│     Wrong version? Start rollout.                        │
│     Pod unhealthy? Restart it.                           │
│                                                          │
│  4. REPEAT: forever                                      │
└─────────────────────────────────────────────────────────┘

This is also called "reconciliation" or "level-triggered" (not edge-triggered).
The controller doesn't care HOW we got into the current state.
It only asks: "Is actual == desired? If not, fix it."

This makes Kubernetes SELF-HEALING:
  - Delete a Pod manually → controller creates a new one
  - Node crashes → controller creates replacements
  - Edit the Deployment → controller starts a rollout

Built-in controllers (all running in kube-controller-manager):
  Deployment controller    → manages ReplicaSets
  ReplicaSet controller    → manages Pod count
  StatefulSet controller   → manages ordered Pods
  Job controller           → manages run-to-completion Pods
  DaemonSet controller     → manages one-Pod-per-node
  Node controller          → detects/evicts from failed nodes
  Endpoint controller      → populates Service endpoints
  SA controller            → creates default ServiceAccounts
  Namespace controller     → cleanup on namespace deletion
  PV controller            → binds PVCs to PVs
  
  + custom controllers (operators) for CRDs

They all follow the same watch → compare → act → repeat pattern.
```

---

## 13. CNI Deep Dive

### What CNI Does

```
CNI (Container Network Interface) is a specification.
It answers: "How does each Pod get an IP and connect to the network?"

When kubelet creates a Pod:
  kubelet → calls CNI plugin → plugin configures networking → returns IP

The plugin must:
  1. Create a network namespace for the Pod
  2. Create a virtual ethernet (veth) pair
  3. Assign an IP address from the Pod CIDR
  4. Set up routing so the Pod can reach other Pods
  5. Set up any network policies
```

### CNI Plugin Comparison

```
Plugin          Data Path       Network Policy   Speed    Complexity
──────          ─────────       ──────────────   ─────    ──────────
Flannel         VXLAN overlay   None             Medium   Low
Calico          BGP or VXLAN    L3/L4            Fast     Medium
Cilium          eBPF            L3/L4/L7         Fastest  Medium
AWS VPC CNI     Native VPC      Security Groups  Fast     Low (AWS only)
WeaveNet        Overlay+encrypt L3/L4            Medium   Low

AWS VPC CNI is special:
  Pods get REAL VPC IP addresses (not overlay)
  Pod 10.0.5.23 is a real IP in your VPC
  No encapsulation overhead
  Security Groups work on Pod IPs
  Limitation: IPs per node limited by ENI count
  
  Prefix delegation: assign /28 prefixes instead of individual IPs
  → 16x more Pod IPs per ENI → more Pods per node
```

---

## 14. How Ingress Routes Traffic

```
Ingress Controller = a reverse proxy running inside the cluster.

Deployment:  nginx-ingress-controller (or Traefik, HAProxy, etc.)
It watches:  Ingress objects in etcd
It does:     reconfigures nginx.conf dynamically

┌──────────────────────────────────────────────────────────────┐
│  Ingress Controller Pod (nginx)                               │
│                                                               │
│  Watches Ingress objects → builds nginx.conf:                │
│                                                               │
│  server {                                                     │
│    server_name api.myapp.com;                                │
│    location /orders { proxy_pass http://order-svc-upstream; }│
│    location /users  { proxy_pass http://user-svc-upstream; } │
│  }                                                            │
│                                                               │
│  Upstream pools auto-populated from Endpoints:               │
│  upstream order-svc-upstream {                                │
│    server 10.244.0.5:8080;                                   │
│    server 10.244.1.3:8080;                                   │
│    server 10.244.2.8:8080;                                   │
│  }                                                            │
│                                                               │
│  When Pods change (scale up/down, crash/restart):            │
│  Endpoints change → Ingress controller reconfigures          │
│  → nginx reloaded (or updated dynamically via Lua/OpenResty) │
└──────────────────────────────────────────────────────────────┘

The Ingress Controller itself is exposed via:
  type: LoadBalancer Service → creates a cloud LB (AWS NLB/ALB)
  
  Internet → Cloud LB → Ingress Controller Pod → backend Service/Pod
```

---

## 15. Pod-to-Pod Communication

### Same Node

```
Pod A (10.244.0.5) → Pod B (10.244.0.6) on the same node.

1. App in Pod A: connect(10.244.0.6, 8080)
2. Packet enters Pod A's network namespace
3. Routing: 10.244.0.0/24 is local (via bridge)
4. Packet goes: eth0 (Pod A) → veth-A → bridge (cbr0) → veth-B → eth0 (Pod B)
5. Pod B receives packet

Latency: ~0.1ms (just a bridge hop in kernel memory)
```

### Different Nodes

```
Pod A (10.244.0.5, Node 1) → Pod C (10.244.2.8, Node 3)

1. App in Pod A: connect(10.244.2.8, 8080)
2. Packet enters Pod A's network namespace
3. Routing: 10.244.2.0/24 not local → send to gateway
4. Packet exits Pod, hits host routing table on Node 1
5. Host route: 10.244.2.0/24 via Node 3 (192.168.1.12)
6. CNI encapsulates: wrap in VXLAN (outer dst = 192.168.1.12)
7. Packet travels over physical network: Node 1 → Node 3
8. Node 3 decapsulates VXLAN
9. Inner packet: dst=10.244.2.8 → local bridge → veth → Pod C
10. Pod C receives packet

Latency: ~0.5-2ms (network hop + encapsulation overhead)
```

---

## 16. Resource Scheduling

### How the Scheduler Picks a Node

```
Simplified scoring for a Pod requesting 500m CPU, 512Mi memory:

Node A: 8 CPU total, 6 CPU used, 16Gi mem, 10Gi used
  Available: 2 CPU, 6Gi mem → CAN fit the Pod
  LeastRequested score: (2000m - 500m) / 8000m × 100 = 18.7

Node B: 4 CPU total, 1 CPU used, 8Gi mem, 2Gi used
  Available: 3 CPU, 6Gi mem → CAN fit the Pod
  LeastRequested score: (3000m - 500m) / 4000m × 100 = 62.5  ← higher

Node C: 4 CPU total, 3.8 CPU used, 8Gi mem, 7.5Gi used
  Available: 0.2 CPU, 0.5Gi mem → CANNOT fit → FILTERED OUT

Winner: Node B (highest score = most available resources)

But with topology spread constraints:
  If Node B already has 3 Pods of this app and Node A has 0,
  the topology score might override and pick Node A for better spread.
```

### What "Requests" Actually Do

```
requests.cpu: 500m means:
  1. Scheduler: "Only place this Pod on a node with 500m CPU free"
  2. kubelet: "Reserve 500m CPU via cgroups cpu.shares"
  3. cgroups: "This container gets at least 500m worth of CPU time"
             If node is idle, it can use MORE than 500m (bursting)
             If node is busy, it's guaranteed 500m

requests.memory: 512Mi means:
  1. Scheduler: "Only place on a node with 512Mi memory free"
  2. kubelet: "This is the guaranteed memory"
  3. OOM scorer: "Low priority for OOM kill" (because it's within request)

limits.memory: 1Gi means:
  1. cgroups: memory.limit_in_bytes = 1Gi
  2. If the process uses > 1Gi → OOMKilled (kernel kills the process)
  3. Container restarts
```

---

## 17. Full Pod Lifecycle

```
PHASE 1: CREATION
──────────────────
  kubectl apply → API server → etcd
  Deployment controller → ReplicaSet → Pod object created
  Pod status: Pending

PHASE 2: SCHEDULING
───────────────────
  Scheduler: filter → score → bind
  Pod.spec.nodeName = "node-3"
  Pod status: Pending (scheduled)

PHASE 3: CONTAINER STARTUP
──────────────────────────
  kubelet pulls image (if not cached)
  kubelet creates container via CRI
  CNI assigns IP address
  CSI mounts volumes
  Pod status: Running (containers starting)

  Init containers run (if any):
    init-container-1 → runs to completion → exits
    init-container-2 → runs to completion → exits
    (sequential, must all succeed)

  Sidecar init containers start (restartPolicy: Always):
    vault-agent → starts, keeps running
    istio-proxy → starts, keeps running

  Main containers start:
    app → starts

PHASE 4: PROBING
────────────────
  Startup probe runs first:
    Pass → move to liveness + readiness
    Fail (after threshold) → kill and restart container

  Liveness probe:
    Pass → container is alive
    Fail (3x) → kill and restart container

  Readiness probe:
    Pass → add to Service Endpoints (receives traffic)
    Fail → remove from Endpoints (no traffic, but not restarted)

  Pod status: Running, Ready=True
  Pod condition: ContainersReady=True, Ready=True

PHASE 5: RUNNING
────────────────
  Container runs indefinitely
  Probes continue checking
  Metrics collected by cAdvisor
  Logs written to stdout/stderr → collected by node log agent

PHASE 6: TERMINATION
─────────────────────
  Triggered by: scaling down, rolling update, kubectl delete, node drain

  T+0ms:   API server sets deletionTimestamp
           Pod enters "Terminating" state
  
  T+0ms:   (PARALLEL — these happen simultaneously)
           A) Endpoint controller: removes Pod from Service Endpoints
              kube-proxy: updates iptables (may take 1-5 seconds)
           B) kubelet: sees Pod is Terminating

  T+0ms:   kubelet runs preStop hook (if configured)
           preStop: exec: ["sleep", "5"]
           This gives iptables time to propagate
           (so no new traffic arrives while we're shutting down)

  T+5s:    preStop finishes
           kubelet sends SIGTERM to PID 1 in each container

  T+5s:    Application receives SIGTERM
           Should: stop accepting new connections
                   finish in-flight requests
                   close database connections
                   flush buffers
                   exit cleanly

  T+60s:   terminationGracePeriodSeconds reached (default 30s)
           kubelet sends SIGKILL (uncatchable, immediate death)
           Container is forcefully killed

  T+60s:   kubelet removes container, releases resources
           CSI unmounts volumes
           CNI releases IP address

  T+60s:   kubelet updates Pod status: Succeeded or Failed
           Pod object eventually garbage collected from etcd
```

---

## 18. Control Plane HA

### How the API Server Stays Available

```
Production setup: 3 control plane nodes, each running:
  - kube-apiserver
  - kube-controller-manager  
  - kube-scheduler
  - etcd

Load Balancer (NLB or HAProxy)
    │
    ├──► API Server 1 (active)
    ├──► API Server 2 (active)     ← all active, all serve requests
    └──► API Server 3 (active)

API servers are STATELESS — they read/write from etcd.
All 3 can handle any request simultaneously.
Load balancer distributes kubectl/kubelet requests across them.

If API Server 2 crashes:
  Load balancer health check fails → removes from pool
  Requests go to 1 and 3
  Users don't notice (maybe a brief reconnect)
```

### How Controllers Avoid Conflicts

```
Only ONE instance of each controller should be active
(otherwise: 2 Deployment controllers both create ReplicaSets = chaos)

Solution: LEADER ELECTION

Controller Manager 1: "I'll try to acquire the leader lock"
  Creates Lease object: kube-controller-manager
  holderIdentity: "controller-manager-1"
  leaseDurationSeconds: 15
  renewTime: <now>

Controller Manager 2: "Lock exists, someone else is leader. I'll wait."
Controller Manager 3: "Lock exists, someone else is leader. I'll wait."

Every 10s: Controller Manager 1 renews the lease

If Controller Manager 1 crashes:
  Lease not renewed for 15 seconds
  Controller Manager 2: "Lease expired! I'll take over."
  Acquires the lease, becomes the new leader
  Starts running all controllers
  
  Failover time: 15-30 seconds (lease expiry + acquire)

Same pattern for kube-scheduler (only 1 schedules at a time).
```

### etcd Consensus

```
3-node etcd cluster using Raft protocol:

  Leader: etcd-1 (elected by majority vote)
  Followers: etcd-2, etcd-3

Write path:
  1. Client sends write to leader (etcd-1)
  2. Leader appends to its log
  3. Leader replicates to followers (etcd-2, etcd-3)
  4. When MAJORITY (2 of 3) have the entry → committed
  5. Leader responds: "write successful"

  Quorum = (N/2) + 1
  3 nodes: quorum = 2 (tolerate 1 failure)
  5 nodes: quorum = 3 (tolerate 2 failures)

If leader dies:
  Followers notice: no heartbeat for 150ms
  etcd-2 starts election: "I nominate myself"
  etcd-3 votes: "I agree"
  etcd-2 becomes new leader
  
  Election time: 150-300ms
  During election: reads still work (from any node)
                   writes are blocked (brief pause)
  
  API server reconnects to new leader automatically.
  Total disruption: < 1 second.
```

---

*This doc is the conceptual backbone. Read it alongside the beginner guide.*
*After this, the KUBERNETES.md production reference will make much more sense.*
