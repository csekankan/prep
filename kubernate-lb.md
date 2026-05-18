# Ingress & Load Balancing — Deep Dive

> How traffic actually reaches your Pods, every hop explained.
> What the industry uses and why.

---

## Table of Contents

1. [The Full Picture — Every Hop From Browser to Pod](#1-full-picture)
2. [Service Types — Deep Mechanics](#2-service-types)
3. [ClusterIP — How It Actually Works](#3-clusterip)
4. [NodePort — What Really Happens](#4-nodeport)
5. [LoadBalancer — The Cloud Integration](#5-loadbalancer)
6. [Ingress Controller — The Reverse Proxy Inside K8s](#6-ingress-controller)
7. [Ingress vs LoadBalancer vs NodePort — When to Use What](#7-comparison)
8. [NGINX Ingress Controller — How It Works Inside](#8-nginx-internals)
9. [AWS ALB Ingress — How It Works Differently](#9-alb)
10. [Gateway API — The Future Replacing Ingress](#10-gateway-api)
11. [TLS Termination — Where HTTPS Ends](#11-tls)
12. [Session Affinity & Sticky Sessions](#12-sticky-sessions)
13. [Rate Limiting & WAF](#13-rate-limiting)
14. [Health Checks at Every Layer](#14-health-checks)
15. [kube-proxy Modes — iptables vs IPVS vs eBPF](#15-kube-proxy)
16. [Industry Practice — What FAANG Actually Uses](#16-industry)
17. [Common Failures & Debugging](#17-debugging)
18. [Full Production Setup — Step by Step](#18-production)

---

## 1. The Full Picture

### Every Hop, Numbered

```
User types: https://api.myapp.com/orders

Hop 1: DNS
  Browser → DNS resolver → "api.myapp.com = 54.231.10.5"
  (This IP belongs to a cloud load balancer: ALB, NLB, or GCE LB)

Hop 2: Cloud Load Balancer (outside Kubernetes)
  Packet arrives at 54.231.10.5:443
  TLS terminated here (HTTPS → HTTP)
  LB picks a healthy node → forwards to Node IP:NodePort
  e.g., 10.0.1.100:30080

Hop 3: Node (kube-proxy rules)
  Packet arrives at node 10.0.1.100:30080
  iptables/IPVS rules intercept
  DNAT to a Pod IP → e.g., 10.244.2.15:8080
  (This Pod is the Ingress Controller — nginx)

Hop 4: Ingress Controller Pod (nginx)
  Receives HTTP request: GET /orders Host: api.myapp.com
  Looks up Ingress rules:
    host=api.myapp.com, path=/orders → Service: order-service:80
  Resolves order-service endpoints: [10.244.1.5, 10.244.3.8, 10.244.2.12]
  Picks one (round-robin) → proxies to 10.244.1.5:8000

Hop 5: Application Pod
  order-service Pod at 10.244.1.5 receives:
    GET /orders HTTP/1.1
    Host: api.myapp.com
    X-Forwarded-For: 203.0.113.50  (real user IP)
    X-Forwarded-Proto: https
  Processes request → returns HTTP 200

Hop 6: Response goes back the same path (reversed)
  Pod → Ingress Controller → Node → Cloud LB → User
```

### The Same Picture Visually

```
┌──────────┐     ┌──────────────────┐     ┌──────────────────────────────────────┐
│ Internet │────▶│  Cloud Load      │────▶│  Kubernetes Cluster                  │
│          │     │  Balancer        │     │                                      │
│ User at  │     │  (ALB/NLB/GCE)  │     │  ┌─────────── Node 1 ──────────┐   │
│ browser  │     │                  │     │  │ :30080                       │   │
│          │     │  54.231.10.5:443 │     │  │  ┌──────────────────┐       │   │
│          │     │  TLS termination │─────│──│─▶│ Ingress Pod      │       │   │
│          │     │  health checks   │     │  │  │ (nginx)          │       │   │
│          │     │                  │     │  │  │ reads Ingress    │       │   │
│          │     └──────────────────┘     │  │  │ rules, proxies   │──┐    │   │
│          │                              │  │  └──────────────────┘  │    │   │
│          │                              │  │                        │    │   │
│          │                              │  │  ┌──────────────────┐  │    │   │
│          │                              │  │  │ order-svc Pod    │◀─┘    │   │
│          │                              │  │  │ 10.244.1.5:8000  │       │   │
│          │                              │  │  └──────────────────┘       │   │
│          │                              │  └─────────────────────────────┘   │
│          │                              │                                      │
│          │                              │  ┌─────────── Node 2 ──────────┐   │
│          │                              │  │  ┌──────────────────┐       │   │
│          │                              │  │  │ order-svc Pod    │       │   │
│          │                              │  │  │ 10.244.3.8:8000  │       │   │
│          │                              │  │  └──────────────────┘       │   │
│          │                              │  └─────────────────────────────┘   │
└──────────┘                              └──────────────────────────────────────┘
```

---

## 2. Service Types

### The 4 Types and What They Actually Create

```
ClusterIP (default)
  Creates: virtual IP inside the cluster
  Accessible from: inside the cluster only
  Use case: service-to-service communication
  
  Just iptables/IPVS rules. No real network interface.
  No external access.

NodePort
  Creates: ClusterIP + opens a port (30000-32767) on EVERY node
  Accessible from: anyone who can reach any node IP
  Use case: development, or behind your own load balancer
  
  Every node listens on that port, even if the Pod isn't on that node.
  Traffic gets forwarded across nodes via kube-proxy rules.

LoadBalancer
  Creates: ClusterIP + NodePort + cloud load balancer
  Accessible from: the internet (via the LB's public IP)
  Use case: single service exposed externally
  
  Calls cloud API: "Create an ALB/NLB pointing at my NodePorts"
  One LB per Service = expensive if you have many services.

ExternalName
  Creates: a DNS CNAME record
  No proxying, no port, no IP.
  Just: my-db.production → mydb.rds.amazonaws.com
  Use case: point to external services (RDS, managed Redis)
```

### How They Stack

```
ExternalName:  DNS alias only (different from the others)

ClusterIP:     [iptables rules] → Pod IPs
                    ▲
NodePort:      [port on every node] → ClusterIP → Pod IPs
                    ▲
LoadBalancer:  [cloud LB] → NodePort → ClusterIP → Pod IPs

Each type INCLUDES everything below it.
LoadBalancer = cloud LB + NodePort + ClusterIP
```

---

## 3. ClusterIP — How It Actually Works

```
You create:
  Service: order-service, ClusterIP: 10.100.45.67, port: 80 → targetPort: 8000
  
  3 Pods with label app=order-service:
    Pod A: 10.244.1.5
    Pod B: 10.244.2.8
    Pod C: 10.244.3.3

What K8s creates (on EVERY node):

  iptables rules (simplified):
  
  # Any packet going to 10.100.45.67:80 → randomly pick a Pod
  -A KUBE-SERVICES -d 10.100.45.67/32 -p tcp --dport 80 -j KUBE-SVC-XXXX

  # KUBE-SVC-XXXX → random selection (probability-based)
  -A KUBE-SVC-XXXX -m statistic --mode random --probability 0.33 -j KUBE-SEP-AAA
  -A KUBE-SVC-XXXX -m statistic --mode random --probability 0.50 -j KUBE-SEP-BBB
  -A KUBE-SVC-XXXX -j KUBE-SEP-CCC

  # Each KUBE-SEP → DNAT to a real Pod IP
  -A KUBE-SEP-AAA -p tcp -j DNAT --to-destination 10.244.1.5:8000
  -A KUBE-SEP-BBB -p tcp -j DNAT --to-destination 10.244.2.8:8000
  -A KUBE-SEP-CCC -p tcp -j DNAT --to-destination 10.244.3.3:8000

So 10.100.45.67 is NEVER assigned to any interface.
It's a "virtual" IP that only exists in iptables rules.
The kernel intercepts packets at the netfilter level and rewrites them.
```

```
What happens when Pod X calls http://order-service:80:

  1. DNS: order-service → 10.100.45.67
  2. Pod sends packet: src=10.244.4.1 dst=10.100.45.67:80
  3. Packet hits iptables on the node
  4. DNAT: dst rewritten to 10.244.2.8:8000 (randomly chosen)
  5. Packet routed to Pod B
  6. Connection tracking remembers: this flow → Pod B
  7. All future packets in this connection → Pod B (no flip-flopping)
  8. Response: src=10.244.2.8 → SNAT back to 10.100.45.67
  9. Pod X sees response from 10.100.45.67 (never knows about Pod B)
```

---

## 4. NodePort — What Really Happens

```
Service type: NodePort, nodePort: 30080

What K8s does:
  1. Creates ClusterIP (same as above)
  2. On EVERY node, opens port 30080
  3. Adds iptables rule: packets to :30080 → same Pod selection

Cluster has 3 nodes:
  Node 1: 10.0.1.100
  Node 2: 10.0.1.101
  Node 3: 10.0.1.102

ALL of these work, even if the Pod is only on Node 1:
  curl 10.0.1.100:30080  → works (Pod is here, stays local)
  curl 10.0.1.101:30080  → works (forwarded to Node 1's Pod)
  curl 10.0.1.102:30080  → works (forwarded to Node 1's Pod)
```

### The Extra Hop Problem

```
Request hits Node 2 (no Pod here):

  Node 2 :30080
    │
    │  iptables: DNAT to Pod on Node 1
    │
    ▼
  Node 1 → Pod (10.244.1.5:8000)
    │
    │  Response goes back through Node 2
    │
    ▼
  Client

Problems:
  1. Extra network hop (latency)
  2. Source IP is lost (Pod sees Node 2's IP, not client IP)

Fix: externalTrafficPolicy: Local
```

### externalTrafficPolicy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: NodePort
  externalTrafficPolicy: Local    # ← the fix
  ports:
  - port: 80
    nodePort: 30080
  selector:
    app: my-app
```

```
With externalTrafficPolicy: Cluster (default):
  ANY node can receive traffic → forwards to any Pod
  Extra hops, source IP lost
  Even distribution across all Pods

With externalTrafficPolicy: Local:
  Node only routes to Pods ON THAT NODE
  No extra hops, source IP preserved
  But: if no Pod on the node → connection refused
  Load balancer health check catches this → stops sending to that node

  Node 1 (has Pod)  → receives traffic ✓
  Node 2 (no Pod)   → LB health check fails → no traffic sent here
  Node 3 (has Pod)  → receives traffic ✓
```

---

## 5. LoadBalancer — The Cloud Integration

### What Happens When You Create type: LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-api
spec:
  type: LoadBalancer
  selector:
    app: my-api
  ports:
  - port: 443
    targetPort: 8000
```

```
1. K8s creates ClusterIP + NodePort (say 30080)

2. Cloud controller manager (runs in control plane) sees this Service

3. Calls cloud API:
   AWS:   CreateLoadBalancer (Classic LB or NLB)
   GCP:   Create Network Load Balancer
   Azure: Create Azure Load Balancer

4. Cloud LB is configured:
   Frontend: 0.0.0.0:443 (public IP)
   Backend:  all node IPs on port 30080
   Health check: TCP 30080 every 10s

5. K8s updates Service status with the LB's external IP/hostname:
   status:
     loadBalancer:
       ingress:
       - hostname: abc123.us-east-1.elb.amazonaws.com

6. DNS: you point api.myapp.com → that hostname
```

### Why One-LB-Per-Service Is Expensive

```
AWS pricing (approximate):
  ALB: $22/month + $0.008 per LCU-hour
  NLB: $22/month + $0.006 per NLCU-hour
  Classic: $18/month + $0.008/GB

If you have 15 microservices with type: LoadBalancer:
  15 × $22 = $330/month just for idle load balancers
  Plus data transfer costs

With Ingress (1 LB routing to all services):
  1 × $22 = $22/month
  
  Savings: $308/month → $3,700/year
  
This is the #1 reason Ingress exists.
```

---

## 6. Ingress Controller

### It's Just a Reverse Proxy Running Inside K8s

```
An Ingress Controller is:
  1. A Deployment running nginx (or envoy, traefik, HAProxy)
  2. Exposed via a single LoadBalancer Service
  3. Watches Ingress resources and auto-configures itself

It is NOT built into Kubernetes. You install it separately.
The Ingress YAML is just configuration — the controller does the work.
```

### How It Sets Up

```
Step 1: Install the Ingress Controller (once)

  kubectl apply -f nginx-ingress-controller.yaml

  This creates:
    Namespace: ingress-nginx
    Deployment: ingress-nginx-controller (runs nginx Pods)
    Service: ingress-nginx-controller (type: LoadBalancer)
      → Cloud creates ONE load balancer
      → This LB handles ALL your Ingress rules

Step 2: Create Ingress resources (per app)

  Each Ingress YAML = a set of routing rules.
  The controller watches for Ingress changes
  and rebuilds its nginx.conf automatically.
```

### The Controller's nginx.conf (What It Generates)

```
When you create this Ingress:

  rules:
  - host: api.myapp.com
    paths:
    - path: /orders   → order-service:80
    - path: /products → product-service:80
  - host: admin.myapp.com
    paths:
    - path: /         → admin-service:80

The controller generates (simplified):

  # nginx.conf (auto-generated, don't edit)
  
  server {
    listen 80;
    server_name api.myapp.com;
    
    location /orders {
      proxy_pass http://upstream_order_service;
      # upstream_order_service resolves to Pod IPs:
      # 10.244.1.5:8000, 10.244.2.8:8000, 10.244.3.3:8000
    }
    
    location /products {
      proxy_pass http://upstream_product_service;
    }
  }
  
  server {
    listen 80;
    server_name admin.myapp.com;
    
    location / {
      proxy_pass http://upstream_admin_service;
    }
  }

When Pods scale up/down, the controller updates upstreams automatically.
When you create/delete Ingress resources, it reloads nginx.conf.
```

### How the Controller Discovers Pod IPs

```
Two modes:

1. Service-based (default):
   Controller → Service ClusterIP → kube-proxy → Pod
   Extra hop through iptables
   
2. Endpoint-based (better, most controllers support this):
   Controller reads the Endpoints object directly
   Gets real Pod IPs: [10.244.1.5, 10.244.2.8, 10.244.3.3]
   Proxies directly to Pod IPs, skipping kube-proxy
   
   NGINX Ingress: enabled by default (uses endpoints, not ClusterIP)
   AWS ALB:       always uses Pod IPs (target-type: ip)
```

---

## 7. When to Use What

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DECISION TREE                                      │
│                                                                      │
│  Is the service internal only (svc-to-svc)?                         │
│    YES → ClusterIP (done)                                           │
│                                                                      │
│  Is it a single TCP/UDP service (database, gRPC, game server)?      │
│    YES → LoadBalancer (type: NLB)                                   │
│    (only 1 service, so 1 LB is fine)                                │
│                                                                      │
│  Is it HTTP/HTTPS with multiple services on one domain?             │
│    YES → Ingress (1 LB, path/host routing)                         │
│                                                                      │
│  Do you need advanced routing (header-based, mirroring, gRPC)?      │
│    YES → Gateway API (the future)                                   │
│                                                                      │
│  Are you on AWS and want native ALB features (WAF, Cognito)?        │
│    YES → AWS LB Controller with ALB Ingress                        │
│                                                                      │
│  Development/testing only?                                           │
│    → NodePort (simple, no cloud LB needed)                          │
│    → port-forward (kubectl port-forward)                            │
└──────────────────────────────────────────────────────────────────────┘
```

```
Industry usage (from surveys + FAANG talks):

  82% use Ingress (NGINX most popular)
  45% use cloud-native LB (AWS ALB, GCP GCLB)
  30% use service mesh (Istio) as the edge proxy
  15% adopting Gateway API
  
  Nobody uses NodePort in production.
  Nobody uses plain LoadBalancer for HTTP services.
```

---

## 8. NGINX Ingress Controller Internals

### Architecture

```
┌────────────────────────────────────────────────────────┐
│  ingress-nginx-controller Pod                           │
│                                                        │
│  ┌───────────────────┐    ┌─────────────────────┐     │
│  │  Controller        │    │  NGINX process      │     │
│  │  (Go binary)       │    │  (worker processes)  │     │
│  │                    │    │                      │     │
│  │  Watches:          │    │  Serves traffic:     │     │
│  │  - Ingress objects │───▶│  - listen :80 :443   │     │
│  │  - Services        │    │  - proxy_pass        │     │
│  │  - Endpoints       │    │  - upstream pools    │     │
│  │  - Secrets (TLS)   │    │  - rate limiting     │     │
│  │                    │    │  - access logs       │     │
│  │  Generates:        │    │                      │     │
│  │  - nginx.conf      │    │  Hot reload:         │     │
│  │  - upstream lists  │    │  - no dropped conns  │     │
│  └───────────────────┘    └─────────────────────┘     │
└────────────────────────────────────────────────────────┘

The Controller process watches K8s API for changes.
When Ingress/Endpoints change → regenerates nginx.conf → signals NGINX to reload.
Reload is graceful: in-flight requests complete on old workers.
```

### Key Annotations You'll Use

```yaml
metadata:
  annotations:
    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"

    # Body size (file uploads)
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"

    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/limit-connections: "5"

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://myapp.com"

    # Redirect HTTP → HTTPS
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

    # URL rewrite
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    # with path: /api(/|$)(.*)

    # WebSocket support
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"

    # Custom NGINX config snippet
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";

    # Load balancing algorithm
    nginx.ingress.kubernetes.io/upstream-hash-by: "$remote_addr"
```

---

## 9. AWS ALB Ingress

### Fundamentally Different from NGINX Ingress

```
NGINX Ingress:
  nginx Pods run INSIDE your cluster
  Cloud LB (NLB) → NodePort → nginx Pod → app Pod
  Routing: done by nginx (inside cluster)
  4 hops

AWS ALB Ingress:
  ALB runs OUTSIDE your cluster (AWS managed)
  ALB → directly to Pod IPs (no nginx in the middle)
  Routing: done by ALB itself (AWS infrastructure)
  2 hops (faster)

  ┌──────────┐      ┌─────────────────────┐
  │  ALB     │─────▶│  Pod (10.244.1.5)   │
  │ (AWS     │      │  Pod (10.244.2.8)   │
  │ managed) │─────▶│  Pod (10.244.3.3)   │
  └──────────┘      └─────────────────────┘
  
  ALB knows Pod IPs because the AWS LB Controller
  registers them as "IP targets" in the ALB target group.
```

### How ALB Controller Works

```
1. You create an Ingress with class: alb
2. AWS LB Controller (running in your cluster) sees it
3. Controller calls AWS API:
   - CreateLoadBalancer (ALB)
   - CreateTargetGroup (with Pod IPs as targets)
   - CreateListener (port 443, forward to target group)
   - CreateRule (host/path matching)
4. When Pods scale → controller updates target group
5. When Ingress changes → controller updates ALB rules

You never run a reverse proxy Pod. AWS does it all.
```

### NGINX Ingress vs ALB — Comparison

```
                        NGINX Ingress           AWS ALB Ingress
                        ─────────────           ───────────────
Runs where:             Inside cluster          AWS managed service
Your infra cost:        nginx Pods (CPU/RAM)    $22/month per ALB
Hops:                   LB → Node → nginx → Pod LB → Pod (2 hops)
Latency:                Higher (more hops)      Lower
TLS termination:        At nginx Pod            At ALB (ACM, free certs)
WAF:                    ModSecurity (complex)   AWS WAF ($5/month + rules)
WebSocket:              ✓                       ✓
gRPC:                   ✓                       ✓ (ALB supports gRPC)
Custom routing:         ✓ (full nginx power)    Limited to ALB rules
Multi-cloud:            ✓ (portable)            AWS only
Sticky sessions:        ✓ (cookie-based)        ✓ (ALB native)
Auth:                   External (OAuth proxy)  Built-in (Cognito, OIDC)

Industry pick:
  AWS shops        → ALB (native, less infra to manage)
  Multi-cloud      → NGINX or Envoy (portable)
  Service mesh     → Istio Gateway (Envoy-based)
```

---

## 10. Gateway API

### Why It's Replacing Ingress

```
Ingress problems:
  1. All config via annotations → not type-safe, varies per controller
  2. No standard for TCP/UDP routing
  3. No traffic splitting (canary)
  4. No header-based routing
  5. Single resource = tangled ownership (platform team + app team)

Gateway API fixes all of this:
  1. Typed resources (no annotation hacks)
  2. TCP, UDP, gRPC, HTTP all supported
  3. Traffic splitting built-in
  4. Header/query matching built-in
  5. Split into roles: GatewayClass → Gateway → HTTPRoute
```

### The Role Split

```
Platform team creates:
  GatewayClass: "which controller" (like IngressClass)
  Gateway: "which ports, which TLS certs, which IPs"

App team creates:
  HTTPRoute: "my app's routing rules"

  This separation is key for large orgs.
  Platform team controls the infrastructure.
  App teams self-serve their routing.
```

```yaml
# Platform team: create the Gateway (once)
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production
  namespace: gateway-system
spec:
  gatewayClassName: nginx    # or aws-alb, istio, envoy, etc.
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-cert
    allowedRoutes:
      namespaces:
        from: All            # any namespace can attach routes
---
# App team: create HTTPRoute (per service)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: order-service
  namespace: production
spec:
  parentRefs:
  - name: production
    namespace: gateway-system
  hostnames:
  - "api.myapp.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/orders
    backendRefs:
    - name: order-service
      port: 80
      weight: 90              # 90% to stable
    - name: order-service-canary
      port: 80
      weight: 10              # 10% to canary (built-in!)
```

---

## 11. TLS Termination

### Where HTTPS Gets Decrypted

```
Option 1: At the Cloud Load Balancer (most common)
  
  Browser ──HTTPS──▶ ALB ──HTTP──▶ Ingress Pod ──HTTP──▶ App Pod
                     ▲ TLS ends here
  
  Pros: free certs (ACM), offloads crypto from your cluster
  Cons: traffic inside cluster is unencrypted

Option 2: At the Ingress Controller
  
  Browser ──HTTPS──▶ NLB ──TCP──▶ Ingress Pod ──HTTP──▶ App Pod
                                   ▲ TLS ends here
  
  Pros: see real TLS details, use custom certs (cert-manager)
  Cons: Ingress Pod does the crypto work (CPU)

Option 3: End-to-end (mTLS, with service mesh)
  
  Browser ──HTTPS──▶ ALB ──HTTPS──▶ Ingress ──mTLS──▶ App Pod
                     ▲               ▲                  ▲
                     TLS             re-encrypt          Istio sidecar
  
  Pros: encrypted everywhere, zero trust
  Cons: complexity, CPU overhead

Industry practice:
  Most teams: Option 1 (ALB termination) + Option 3 for internal (Istio mTLS)
  Compliance-heavy: Option 3 everywhere
```

### Setting Up TLS on NGINX Ingress

```yaml
# cert-manager auto-provisions the TLS cert
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.myapp.com
    secretName: api-myapp-tls    # cert-manager creates this Secret
  rules:
  - host: api.myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
```

---

## 12. Session Affinity

### When You Need Same-User → Same-Pod

```
Stateless (normal, preferred):
  Request 1 → Pod A
  Request 2 → Pod C
  Request 3 → Pod B
  Doesn't matter — all Pods give the same result.

Stateful (WebSocket, file upload, shopping cart in memory):
  Request 1 → Pod A (starts upload)
  Request 2 → must also go to Pod A (to continue upload)

Solutions:
  1. Don't be stateful (use Redis/DB for shared state) ← best
  2. Service sessionAffinity
  3. Ingress cookie-based affinity
```

```yaml
# Kubernetes Service level (IP-based, sticky for 10800s)
apiVersion: v1
kind: Service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
---
# NGINX Ingress level (cookie-based, more reliable)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/affinity-mode: "persistent"
    nginx.ingress.kubernetes.io/session-cookie-name: "SERVERID"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "3600"
```

---

## 13. Rate Limiting & WAF

### Rate Limiting at Ingress

```yaml
# NGINX Ingress: 10 requests/second per client IP
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"
    # Allows burst of 50 (10 × 5), then throttles to 10/s
    nginx.ingress.kubernetes.io/limit-whitelist: "10.0.0.0/8"
    # Internal IPs exempt from rate limiting
```

```yaml
# AWS ALB: use WAF for rate limiting
# Attach WAF via Ingress annotation:
metadata:
  annotations:
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:...

# WAF rule: rate-limit to 2000 requests per 5 minutes per IP
# Configured in AWS WAF console or Terraform, not in K8s YAML
```

---

## 14. Health Checks at Every Layer

```
There are health checks at FOUR different layers:

Layer 1: Cloud Load Balancer → Node
  "Is this node alive?"
  ALB sends HTTP GET to NodePort every 15s
  If 3 failures → stop sending traffic to this node
  Configured: in LB settings (or Ingress annotations)

Layer 2: Ingress Controller → Backend Pods
  "Is this upstream Pod alive?"
  NGINX checks Pod endpoints, removes unhealthy ones
  Passive: if a Pod returns 5xx, temporarily remove it
  Active: periodic health checks (configurable)

Layer 3: Kubernetes → Pod (readiness probe)
  "Should this Pod receive traffic?"
  kubelet checks readiness probe every 5s
  If unhealthy → removed from Service endpoints
  Ingress controller sees updated endpoints automatically

Layer 4: Kubernetes → Pod (liveness probe)
  "Is this Pod's process stuck?"
  kubelet checks liveness probe every 10s
  If unhealthy → restart the container

All four layers work together:
  LB ensures healthy NODES receive traffic
  Ingress ensures healthy PODS receive traffic
  Readiness ensures READY Pods are in endpoints
  Liveness ensures STUCK Pods get restarted
```

---

## 15. kube-proxy Modes

### How ClusterIP Load Balancing Actually Runs

```
iptables mode (default):
  Every Service → ~10 iptables rules
  1000 Services → ~10,000 rules
  Every packet: walks rules linearly (O(n) for probability chains)
  
  Pros:  simple, reliable, battle-tested
  Cons:  slow rule updates at scale, no real load balancing (random only)
  Good for: clusters under 1000 Services

IPVS mode:
  Uses Linux kernel IPVS (IP Virtual Server)
  Hash-table lookup (O(1)) instead of iptables chain walking
  Real load balancing algorithms: round-robin, least-connections, weighted
  
  Pros:  much faster at scale, better algorithms
  Cons:  slightly more complex, needs ipvs kernel modules
  Good for: clusters over 1000 Services
  
  Enable: kube-proxy --proxy-mode=ipvs

eBPF mode (Cilium):
  Replaces kube-proxy entirely
  XDP: processes packets before they even reach the network stack
  No iptables, no IPVS, no conntrack overhead
  
  Pros:  fastest possible, per-connection load balancing, DSR support
  Cons:  requires Cilium CNI, newer technology
  Good for: high-performance, large-scale clusters
  
  What FAANG uses: Meta, Google, Cloudflare all use eBPF-based networking
```

```
Scale comparison (10,000 Services):

  iptables:  ~100,000 rules, seconds to update, linear chain walk
  IPVS:      hash table, milliseconds to update, O(1) lookup
  eBPF:      XDP hooks, microseconds, zero overhead
```

---

## 16. Industry Practice

### What Companies Actually Use

```
FAANG / Large Scale:

  Google:     GKE + Gateway API + Envoy (they built it)
  Meta:       Custom eBPF (Katran LB) + custom control plane
  Netflix:    EKS + custom Zuul gateway + Envoy sidecar
  Amazon:     EKS + ALB + internal custom L7 proxy
  Uber:       Custom mesh (Peloton) + Envoy sidecars
  Stripe:     Envoy as edge proxy + service mesh
  Airbnb:     EKS + Istio + AWS ALB
  Shopify:    GKE + Nginx Ingress + custom middleware
  Spotify:    GKE + Envoy + custom routing

Mid-size (Series B-D startups, 50-500 engineers):

  Most common: NGINX Ingress Controller
  AWS shops:   AWS ALB Ingress Controller
  GCP shops:   GKE built-in Ingress (GCLB)
  With mesh:   Istio Gateway (replaces Ingress)
  Growing:     Gateway API adoption

Small teams (< 20 engineers):

  NGINX Ingress (free, simple, well documented)
  Traefik (auto-discovery, simpler config)
  Caddy (automatic HTTPS)
```

### Production Architecture (Recommended)

```
For most teams, this is the battle-tested setup:

┌─────────────────────────────────────────────────────────────┐
│  EDGE                                                        │
│                                                              │
│  CloudFlare / AWS CloudFront (CDN + DDoS protection)        │
│       │                                                      │
│       ▼                                                      │
│  AWS WAF (rate limiting, IP blocking, SQL injection)         │
│       │                                                      │
│       ▼                                                      │
│  AWS ALB (TLS termination with ACM, host/path routing)      │
│       │                                                      │
└───────│─────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│  CLUSTER                                                      │
│                                                              │
│  Option A: ALB targets Pod IPs directly                      │
│     ALB → Pod (simplest, lowest latency)                    │
│                                                              │
│  Option B: ALB → NGINX Ingress → Pod                        │
│     When you need: custom routing, WebSocket, rewrite rules │
│                                                              │
│  Option C: ALB → Istio Gateway → Pod (with mesh)            │
│     When you need: mTLS, canary, traffic mirroring          │
│                                                              │
│  Internal (svc-to-svc): ClusterIP only                      │
│  With mesh: Istio sidecars handle retries, mTLS, tracing    │
└─────────────────────────────────────────────────────────────┘
```

### What NOT to Do

```
✗  NodePort in production (no TLS, no routing, ports 30000+)
✗  One LoadBalancer per service (expensive, unmanageable)
✗  Ingress without TLS (even internal should be HTTPS or mTLS)
✗  No rate limiting at edge (you WILL get DDoSed)
✗  No WAF (SQL injection, XSS, etc.)
✗  Running nginx Ingress with 1 replica (single point of failure)
✗  Not setting externalTrafficPolicy (losing client IPs)
✗  Ignoring health checks at the LB layer
```

---

## 17. Debugging

### Traffic Not Reaching Your Pod

```bash
# Step 1: Is the Pod running and ready?
kubectl get pods -n production
# If not Ready → check readiness probe

# Step 2: Is the Service selecting the right Pods?
kubectl get endpoints order-service -n production
# Should show Pod IPs. Empty = selector doesn't match labels.

# Step 3: Is the Ingress configured correctly?
kubectl get ingress -n production
kubectl describe ingress my-ingress -n production
# Check: host, path, backend service name/port

# Step 4: Is the Ingress Controller running?
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Step 5: Can you reach the service directly? (bypass Ingress)
kubectl port-forward svc/order-service -n production 8080:80
curl http://localhost:8080/api/orders
# If this works → problem is in Ingress/LB, not your app

# Step 6: Can you reach via Ingress? (bypass cloud LB)
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8443:443
curl -k -H "Host: api.myapp.com" https://localhost:8443/api/orders
# If this works → problem is in cloud LB or DNS

# Step 7: Check the cloud LB
# AWS: check target group health in ALB console
# Target status: healthy/unhealthy/draining

# Step 8: DNS
dig api.myapp.com
# Should resolve to cloud LB IP/hostname
```

### Common Error Messages

```
"502 Bad Gateway"
  → Ingress can't reach backend Pod
  → Check: is the Pod running? Is targetPort correct? 
  → Check: kubectl get endpoints (empty = broken selector)

"503 Service Temporarily Unavailable"
  → No healthy backends
  → Check: readiness probe failing? All Pods not ready?

"404 Not Found" (from nginx)
  → No Ingress rule matches this host/path
  → Check: Host header matches? Path is correct?

"Connection refused"
  → NodePort but no Pod on that node + externalTrafficPolicy: Local
  → LB health check should catch this

"SSL handshake failed"
  → TLS cert doesn't match hostname
  → cert-manager not ready? ACM cert pending validation?
```

---

## 18. Full Production Setup

### Everything Together

```yaml
# 1. Ingress Controller (install once)
# helm install ingress-nginx ingress-nginx/ingress-nginx \
#   --namespace ingress-nginx --create-namespace \
#   --set controller.replicaCount=3 \
#   --set controller.service.externalTrafficPolicy=Local \
#   --set controller.metrics.enabled=true \
#   --set controller.podAntiAffinity=hard

# 2. Your Ingress resource
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: production-ingress
  namespace: production
  annotations:
    # TLS
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    
    # Security
    nginx.ingress.kubernetes.io/limit-rps: "20"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "Strict-Transport-Security: max-age=31536000";
    
    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.com
    - api.myapp.com
    secretName: myapp-tls
  rules:
  - host: myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
  - host: api.myapp.com
    http:
      paths:
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 80
```

```
Production checklist:

  ✓ Ingress Controller: 3+ replicas, anti-affinity across nodes
  ✓ externalTrafficPolicy: Local (preserve client IPs)
  ✓ TLS everywhere (cert-manager or ACM)
  ✓ Rate limiting at Ingress
  ✓ Security headers (HSTS, X-Frame-Options, CSP)
  ✓ Timeout tuning (don't use defaults)
  ✓ Body size limits (prevent abuse)
  ✓ Monitoring: Ingress metrics → Prometheus → Grafana
  ✓ CDN in front (CloudFront/CloudFlare) for static assets + DDoS
  ✓ WAF for application-layer attacks
  ✓ PodDisruptionBudget on Ingress Controller (survive node drains)
```

---

*Companion to KUBERNETES_BEGINNER.md and MICROSERVICES_COMMUNICATION.md.*
*For AWS-specific load balancer setup, see AWS_EKS_TUTORIAL.md section 8.*
