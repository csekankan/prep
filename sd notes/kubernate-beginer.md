# Kubernetes for Beginners — Zero to Confident

> You know Docker. Now learn Kubernetes.
> This guide explains **why** before **how**, uses plain English,
> and builds every concept on top of the previous one.
> Follow it top-to-bottom on Day 1.

---

## Table of Contents

1. [Why Kubernetes Exists](#1-why-kubernetes-exists)
2. [The Mental Model — What K8s Actually Does](#2-the-mental-model)
3. [Setup — Get a Cluster Running in 5 Minutes](#3-setup)
4. [Pods — The Smallest Unit](#4-pods)
5. [Deployments — The Real Way to Run Apps](#5-deployments)
6. [Services — How Pods Talk to Each Other](#6-services)
7. [Namespaces — Organizing Your Cluster](#7-namespaces)
8. [ConfigMaps & Secrets — Configuration Management](#8-configmaps--secrets)
9. [Health Checks — Probes](#9-health-checks--probes)
10. [Resource Limits — CPU & Memory](#10-resource-limits)
11. [Scaling — More Copies When Busy](#11-scaling)
12. [Ingress — Exposing to the Internet](#12-ingress)
13. [Volumes — Persistent Data](#13-volumes)
14. [Labels & Selectors — How Everything Connects](#14-labels--selectors)
15. [kubectl Cheat Sheet — The Only Commands You Need](#15-kubectl-cheat-sheet)
16. [Debugging — When Things Go Wrong](#16-debugging)
17. [Your First Real Deployment — Step by Step](#17-your-first-real-deployment)
18. [What to Learn Next](#18-what-to-learn-next)

---

## 1. Why Kubernetes Exists

### The Problem

```
Without Kubernetes, deploying looks like this:

You:     "I'll run my app on Server A."
Server A: *crashes at 3am*
You:     "Okay, I'll start it on Server B manually."
Boss:    "We need 10 copies for Black Friday."
You:     "Let me SSH into 10 servers and start them one by one..."
Boss:    "New version is ready. Deploy with zero downtime."
You:     *cries*
```

### What Kubernetes Does

```
Kubernetes is a CONTAINER ORCHESTRATOR. You tell it:

  "I want 5 copies of my app running at all times."

Kubernetes handles:
  ✓ Which servers (nodes) to put them on
  ✓ Restarting them if they crash
  ✓ Rolling out new versions without downtime
  ✓ Scaling up/down based on traffic
  ✓ Load balancing between copies
  ✓ Networking between services

You describe WHAT you want → Kubernetes figures out HOW.
This is called "declarative configuration."
```

### Docker vs Kubernetes

```
Docker:      runs ONE container on ONE machine
Kubernetes:  runs MANY containers across MANY machines, keeps them healthy

Docker:      "Run this container"
Kubernetes:  "Make sure 5 of these containers are always running somewhere"

You still use Docker to BUILD images.
Kubernetes RUNS them at scale.
```

---

## 2. The Mental Model

### The Cluster

```
A Kubernetes cluster has two parts:

┌─────────────────────────────────────────────────┐
│  CONTROL PLANE  (the brain)                       │
│                                                   │
│  Decides WHERE to run things.                     │
│  You never run your apps here.                    │
│  Think of it as the "manager."                    │
└────────────────────┬──────────────────────────────┘
                     │  talks to
┌────────────────────▼──────────────────────────────┐
│  WORKER NODES  (the muscle)                        │
│                                                    │
│  Node 1: [App A] [App B]                          │
│  Node 2: [App A] [App C]                          │
│  Node 3: [App B] [App C]                          │
│                                                    │
│  Your containers actually run here.               │
└────────────────────────────────────────────────────┘
```

### The Key Objects (Just 5 to Start)

```
Pod         →  a running container (or group of containers)
Deployment  →  "keep N copies of this Pod running"
Service     →  "give these Pods a stable address"
ConfigMap   →  "here's some configuration data"
Secret      →  "here's some sensitive data (passwords)"

That's it. Everything else builds on these five.
```

### How You Talk to Kubernetes

```
You write YAML files describing what you want.
You run: kubectl apply -f my-file.yaml
Kubernetes reads it and makes it happen.

kubectl = the command-line tool to talk to Kubernetes
YAML    = the language Kubernetes speaks
```

---

## 3. Setup

### Option 1: Docker Desktop (Easiest — Mac/Windows)

```bash
# Already have Docker Desktop?
# Go to Settings → Kubernetes → Enable Kubernetes → Apply & Restart
# Wait 2 minutes. Done.

# Verify:
kubectl cluster-info
kubectl get nodes
# You should see 1 node (your laptop)
```

### Option 2: minikube (Linux/Mac/Windows)

```bash
# Install minikube
brew install minikube    # Mac
# or: https://minikube.sigs.k8s.io/docs/start/

# Start a cluster
minikube start

# Verify
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   1m    v1.31.0
```

### Option 3: kind (Kubernetes in Docker)

```bash
# Install kind
brew install kind

# Create a cluster
kind create cluster --name my-first-cluster

# Verify
kubectl get nodes
```

### Verify Your Setup

```bash
# If this works, you're ready:
kubectl get nodes
# Should show at least 1 node with STATUS = Ready

# Quick test: run nginx
kubectl run hello --image=nginx --port=80
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# hello   1/1     Running   0          10s

# Clean up
kubectl delete pod hello
```

---

## 4. Pods

### What is a Pod?

```
A Pod is the SMALLEST thing Kubernetes manages.

Pod = 1 or more containers that:
  - share the same network (localhost works between them)
  - share the same storage
  - are always scheduled together on the same node
  - live and die together

99% of the time: 1 Pod = 1 container.
```

### Your First Pod

```yaml
# Save this as pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-first-pod
  labels:
    app: hello
spec:
  containers:
  - name: web
    image: nginx:latest
    ports:
    - containerPort: 80
```

```bash
# Create the Pod
kubectl apply -f pod.yaml

# See it running
kubectl get pods
# NAME           READY   STATUS    RESTARTS   AGE
# my-first-pod   1/1     Running   0          5s

# See more details
kubectl describe pod my-first-pod

# See the logs
kubectl logs my-first-pod

# Go inside the container (like docker exec)
kubectl exec -it my-first-pod -- /bin/bash

# Delete it
kubectl delete pod my-first-pod
```

### Understanding the YAML

```yaml
apiVersion: v1          # which API to use (v1 = core, stable)
kind: Pod               # what type of object (Pod, Deployment, Service, etc.)
metadata:
  name: my-first-pod    # unique name for this pod
  labels:               # key-value tags (used for selection — very important!)
    app: hello
spec:                   # the actual specification — what you want
  containers:
  - name: web           # name of this container
    image: nginx:latest # Docker image to run
    ports:
    - containerPort: 80 # what port the container listens on
```

### Why You Should NEVER Create Pods Directly

```
If a Pod crashes → it's gone forever. Nobody restarts it.
If the node dies → all Pods on it are gone.

Pods are like cattle, not pets.
You don't create Pods. You create Deployments (which create Pods for you).
```

---

## 5. Deployments

### What is a Deployment?

```
A Deployment says: "I want 3 copies of this Pod. Keep them running."

If a Pod crashes    → Deployment creates a new one
If a node dies      → Deployment moves Pods to healthy nodes
If you update image → Deployment rolls out new version with zero downtime

This is what you use 95% of the time.
```

### Your First Deployment

```yaml
# Save as deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3                  # I want 3 copies
  selector:
    matchLabels:
      app: my-app              # manage Pods with this label
  template:                    # template for the Pods
    metadata:
      labels:
        app: my-app            # MUST match selector above
    spec:
      containers:
      - name: web
        image: nginx:1.25
        ports:
        - containerPort: 80
```

```bash
# Create the Deployment
kubectl apply -f deployment.yaml

# Watch it create 3 Pods
kubectl get pods
# NAME                      READY   STATUS    RESTARTS   AGE
# my-app-6d8f7b5d4f-abc12   1/1     Running   0          5s
# my-app-6d8f7b5d4f-def34   1/1     Running   0          5s
# my-app-6d8f7b5d4f-ghi56   1/1     Running   0          5s

# See the Deployment
kubectl get deployments
# NAME     READY   UP-TO-DATE   AVAILABLE   AGE
# my-app   3/3     3            3           10s
```

### Update Your App (Rolling Update)

```bash
# Change the image version
kubectl set image deployment/my-app web=nginx:1.26

# Watch the rollout (new Pods created, old ones terminated)
kubectl rollout status deployment/my-app

# See the history
kubectl rollout history deployment/my-app

# Oops, new version is broken? Rollback!
kubectl rollout undo deployment/my-app

# Rollback to a specific version
kubectl rollout undo deployment/my-app --to-revision=2
```

### How Rolling Updates Work

```
Starting state: [v1] [v1] [v1]

Step 1: Create new Pod     [v1] [v1] [v1] [v2]  (1 extra)
Step 2: New Pod is ready   [v1] [v1] [v1] [v2]  ✓
Step 3: Kill old Pod       [v1] [v1] [v2]        (back to 3)
Step 4: Create new Pod     [v1] [v1] [v2] [v2]
Step 5: Kill old Pod       [v1] [v2] [v2]
Step 6: Create new Pod     [v1] [v2] [v2] [v2]
Step 7: Kill old Pod       [v2] [v2] [v2]        Done!

At no point were there 0 Pods running. That's zero-downtime deployment.
```

### Try This: Kill a Pod and Watch It Come Back

```bash
# List pods
kubectl get pods

# Delete one (copy any pod name from above)
kubectl delete pod my-app-6d8f7b5d4f-abc12

# Immediately check again
kubectl get pods
# A NEW pod is already being created! The Deployment noticed
# one Pod died and immediately created a replacement.
# This is self-healing.
```

---

## 6. Services

### The Problem Services Solve

```
You have 3 Pods running your app. Each has a different IP address.

Pod 1: 10.244.0.5
Pod 2: 10.244.1.8
Pod 3: 10.244.2.3

Problems:
  1. These IPs change every time a Pod restarts
  2. How does another app know which IP to use?
  3. How do you load-balance between them?

Solution: A SERVICE gives Pods a single, stable address.
```

### Service = Stable Address + Load Balancer

```
             ┌──────────────┐
             │   Service    │
             │  my-app:80   │  ← stable DNS name + IP
             └──────┬───────┘
                    │ load balances to:
         ┌──────────┼──────────┐
         │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
    │ Pod 1  │ │ Pod 2  │ │ Pod 3  │
    │ :8080  │ │ :8080  │ │ :8080  │
    └────────┘ └────────┘ └────────┘
```

### Your First Service

```yaml
# Save as service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app            # find Pods with label app=my-app
  ports:
  - port: 80               # the Service listens on port 80
    targetPort: 80          # forward to Pod's port 80
  type: ClusterIP           # internal only (default)
```

```bash
# Create the Service
kubectl apply -f service.yaml

# See it
kubectl get services
# NAME             TYPE        CLUSTER-IP      PORT(S)   AGE
# my-app-service   ClusterIP   10.96.45.123    80/TCP    5s

# Now any Pod in the cluster can reach your app at:
#   http://my-app-service          (within same namespace)
#   http://my-app-service.default  (from other namespaces)
```

### Service Types — When to Use What

```
ClusterIP (default):
  Internal only. Other Pods can reach it, but NOT the outside world.
  Use for: backend services, databases, internal APIs.

NodePort:
  Opens a port (30000-32767) on EVERY node.
  Use for: quick testing, development.

LoadBalancer:
  Creates a real cloud load balancer (AWS ALB/NLB, GCP GLB).
  Use for: production traffic from the internet.

ExternalName:
  DNS alias to an external service.
  Use for: pointing to an external database during migration.
```

### Quick Test: Access Your Service

```bash
# Port-forward to test from your laptop
kubectl port-forward service/my-app-service 8080:80

# Now open: http://localhost:8080
# You'll see the nginx welcome page!
# Press Ctrl+C to stop
```

---

## 7. Namespaces

### What Are Namespaces?

```
Namespaces are like FOLDERS for your cluster.

They let you:
  - Separate different teams/projects
  - Separate environments (dev, staging, production)
  - Apply different resource limits per namespace
  - Control who can access what

Default namespaces:
  default         → where your stuff goes if you don't specify
  kube-system     → Kubernetes system components (don't touch)
  kube-public     → public data (rarely used)
```

### Using Namespaces

```bash
# See all namespaces
kubectl get namespaces

# Create a namespace
kubectl create namespace my-project

# Run a command in a specific namespace
kubectl get pods -n my-project
kubectl get pods --namespace=my-project

# Set your default namespace (so you don't type -n every time)
kubectl config set-context --current --namespace=my-project

# Deploy to a specific namespace
kubectl apply -f deployment.yaml -n my-project
```

```yaml
# Or specify namespace in the YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: my-project      # deployed here
spec:
  ...
```

### Cross-Namespace Communication

```bash
# Within same namespace, just use the service name:
curl http://my-app-service

# From a different namespace, use the full name:
curl http://my-app-service.my-project
# Or fully qualified:
curl http://my-app-service.my-project.svc.cluster.local
```

---

## 8. ConfigMaps & Secrets

### ConfigMap — Non-Sensitive Configuration

```
Problem: You don't want to rebuild your Docker image just because
         a config value changed (like LOG_LEVEL or DATABASE_URL).

Solution: Store config in a ConfigMap, inject it into your Pod.
```

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
```

```yaml
# Use it in your Deployment
spec:
  containers:
  - name: web
    image: myapp:1.0
    env:
    # Single value from ConfigMap
    - name: APP_ENV
      valueFrom:
        configMapKeyRef:
          name: my-config
          key: APP_ENV
    # Or inject ALL values from the ConfigMap as env vars
    envFrom?»e5r4a:
    - configMapRef:
        name: my-config
```

### Secret — Sensitive Data

```
Secrets are like ConfigMaps, but for passwords, API keys, tokens.
They're base64-encoded (NOT encrypted by default — just obscured).
```

```bash
# Create a Secret from command line
kubectl create secret generic db-password \
  --from-literal=password=supersecret123

# Or from a file
kubectl create secret generic tls-cert \
  --from-file=tls.crt=./cert.pem \
  --from-file=tls.key=./key.pem
```

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-password
type: Opaque
stringData:              # plain text (auto-encoded to base64)
  password: "supersecret123"
  username: "admin"
```

```yaml
# Use it in your Deployment
spec:
  containers:
  - name: web
    image: myapp:1.0
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-password
          key: password
```

### When to Use What

```
ConfigMap:  app settings, feature flags, config files
            LOG_LEVEL=info, FEATURE_X=true, nginx.conf

Secret:     passwords, API keys, TLS certificates, tokens
            DB_PASSWORD, STRIPE_KEY, JWT_SECRET
```

---

## 9. Health Checks — Probes

### Why Probes Matter

```
Without probes:
  - Kubernetes thinks your Pod is healthy just because the PROCESS is running
  - But your app might be stuck, deadlocked, or still starting up
  - Traffic gets routed to a Pod that can't handle it → errors for users

With probes:
  - Kubernetes CHECKS if your app is actually working
  - Removes unhealthy Pods from the load balancer
  - Restarts stuck Pods automatically
```

### Three Types of Probes

```yaml
spec:
  containers:
  - name: web
    image: myapp:1.0

    # STARTUP PROBE: "Has the app finished starting?"
    # Runs first. Other probes don't start until this passes.
    # Use for slow-starting apps.
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 5         # check every 5 seconds
      failureThreshold: 30     # give up after 30 failures (= 150 seconds to start)

    # LIVENESS PROBE: "Is the app alive?"
    # If it fails → Kubernetes RESTARTS the container
    # Should be simple — just "is the process okay?"
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 10        # check every 10 seconds
      failureThreshold: 3      # restart after 3 failures

    # READINESS PROBE: "Can the app handle traffic?"
    # If it fails → Pod is REMOVED from the Service (no traffic)
    # But NOT restarted. Use to check dependencies (DB, cache).
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
      failureThreshold: 3
```

### Probe Methods

```yaml
# Method 1: HTTP GET (most common for web apps)
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080

# Method 2: TCP socket (good for databases)
livenessProbe:
  tcpSocket:
    port: 5432

# Method 3: Run a command
livenessProbe:
  exec:
    command: ["pg_isready", "-U", "postgres"]
```

### The Golden Rule

```
Liveness probe:   check ONLY the process itself (fast, no dependencies)
                  "Am I alive?"  →  return 200 OK

Readiness probe:  check dependencies (database, cache, etc.)
                  "Can I serve traffic?"  →  check DB connection, then 200 OK

If you only add ONE probe: add a readiness probe.
```

---

## 10. Resource Limits

### Why Set Resources?

```
1
```

### Requests vs Limits

```yaml
spec:
  containers:
  - name: web
    image: myapp:1.0
    resources:
      requests:              # MINIMUM guaranteed
        cpu: "100m"          # 100 millicores = 0.1 CPU core
        memory: "128Mi"      # 128 megabytes
      limits:                # MAXIMUM allowed
        memory: "256Mi"      # will be killed (OOMKilled) if exceeds this
```

### Understanding CPU & Memory Units

```
CPU:
  1     = 1 full CPU core
  500m  = 500 millicores = 0.5 core = half a CPU
  100m  = 100 millicores = 0.1 core = 10% of a CPU
  250m  = a good starting point for a small web server

Memory:
  Mi = Mebibytes (like megabytes)
  Gi = Gibibytes (like gigabytes)
  128Mi  = ~128 MB (small microservice)
  256Mi  = ~256 MB (typical web server)
  1Gi    = ~1 GB (Java apps, databases)

Tip: Start small, monitor actual usage, then adjust.
```

### What Happens When Limits Are Hit

```
CPU limit hit:    Pod is THROTTLED (slowed down, but not killed)
Memory limit hit: Pod is KILLED (OOMKilled) and restarted

This is why:
  - Always set a memory limit (prevent runaway memory leaks)
  - Some people skip CPU limits (throttling can cause latency spikes)
  - Always set both requests (helps scheduler place Pods correctly)
```

---

## 11. Scaling

### Manual Scaling

```bash
# Scale to 10 replicas
kubectl scale deployment my-app --replicas=10

# Scale back to 3
kubectl scale deployment my-app --replicas=3

# Scale to 0 (all pods removed, no traffic served)
kubectl scale deployment my-app --replicas=0
```

### Auto Scaling (HPA — Horizontal Pod Autoscaler)

```yaml
# hpa.yaml — automatically scale based on CPU usage
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2           # never go below 2
  maxReplicas: 20          # never go above 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # add Pods when CPU > 70%
```

```bash
# Apply it
kubectl apply -f hpa.yaml

# Watch it in action
kubectl get hpa
# NAME         REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS
# my-app-hpa   Deployment/my-app  45%/70%   2         20        3
```

### How HPA Works

```
Every 15 seconds, HPA checks:
  "What is the average CPU across all Pods?"

If avg CPU > 70% → add more Pods (scale up)
If avg CPU < 70% → remove some Pods (scale down, slowly)

Example:
  3 Pods at 90% CPU → HPA adds 2 more → 5 Pods at ~54% CPU → stable

Important: HPA needs resource REQUESTS set on your Pods to work!
(70% of WHAT? It needs to know the denominator.)
```

---

## 12. Ingress

### The Problem

```
Services with type: ClusterIP are internal only.
Services with type: LoadBalancer create ONE load balancer per service ($$$).

If you have 10 services, that's 10 load balancers = expensive.

Ingress: ONE load balancer that routes to multiple services based on URL/hostname.
```

### How Ingress Works

```
Internet
    │
    ▼
┌────────────────────────────┐
│   Ingress Controller       │  ← 1 load balancer
│   (nginx, traefik, etc.)   │
└──────────┬─────────────────┘
           │
    ┌──────┼──────────────────┐
    │      │                  │
    ▼      ▼                  ▼
 /api   /images            /auth
    │      │                  │
    ▼      ▼                  ▼
 api-svc  images-svc       auth-svc
```

### Your First Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  # Route by hostname
  - host: api.myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  # Route by path
  - host: myapp.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Setting Up Ingress Locally

```bash
# On minikube:
minikube addons enable ingress

# On Docker Desktop:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Verify ingress controller is running
kubectl get pods -n ingress-nginx
```

---

## 13. Volumes

### The Problem

```
Containers are EPHEMERAL. When a container restarts, all data is LOST.

Problem: Your database container restarts → all data gone.
Solution: Mount a VOLUME that persists beyond the container's life.
```

### Volume Types (Beginner-Friendly)

```yaml
# Type 1: emptyDir — temporary shared storage between containers
# Deleted when the Pod is deleted. Good for caches, temp files.
spec:
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: cache
      mountPath: /tmp/cache
  volumes:
  - name: cache
    emptyDir: {}

# Type 2: hostPath — mount a directory from the node
# Only for development! Data tied to one specific node.
  volumes:
  - name: data
    hostPath:
      path: /data/myapp

# Type 3: PersistentVolumeClaim — real persistent storage
# This is what you use in production. Survives Pod restarts.
```

### PersistentVolumeClaim (PVC) — Production Storage

```yaml
# Step 1: Request storage
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-data
spec:
  accessModes:
  - ReadWriteOnce        # one Pod can read/write at a time
  resources:
    requests:
      storage: 10Gi       # I need 10 GB

---
# Step 2: Use it in your Pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: web
        image: myapp:1.0
        volumeMounts:
        - name: data
          mountPath: /app/data     # appears here inside the container
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: my-data       # reference the PVC
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc
# NAME      STATUS   VOLUME         CAPACITY   ACCESS MODES   AGE
# my-data   Bound    pvc-abc-123    10Gi       RWO            5s
# STATUS = Bound means storage was provisioned. Ready to use!
```

---

## 14. Labels & Selectors

### The Glue That Holds Everything Together

```
Labels are KEY-VALUE TAGS on any Kubernetes object.
Selectors FIND objects by their labels.

This is how:
  - Deployments know which Pods to manage
  - Services know which Pods to route traffic to
  - HPA knows which Deployment to scale

Without labels, nothing is connected.
```

### How It All Connects

```yaml
# Deployment creates Pods with label: app=my-app
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app          # "I manage Pods with this label"
  template:
    metadata:
      labels:
        app: my-app        # Pods get this label

---
# Service routes traffic to Pods with label: app=my-app
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app            # "I send traffic to Pods with this label"
  ports:
  - port: 80
```

```
The chain:
  Deployment (selector: app=my-app)
      │ creates
      ▼
  Pods (labels: app=my-app)
      ▲ routes to
      │
  Service (selector: app=my-app)
```

### Common Labels

```yaml
labels:
  app: order-service       # which application
  version: "2.0"           # which version
  team: payments           # which team owns it
  environment: production  # which environment
```

### Using Labels with kubectl

```bash
# Show labels
kubectl get pods --show-labels

# Filter by label
kubectl get pods -l app=my-app
kubectl get pods -l "app=my-app,environment=production"

# Add a label
kubectl label pod my-pod version=2.0

# Remove a label
kubectl label pod my-pod version-
```

---

## 15. kubectl Cheat Sheet

### The Essentials

```bash
# ─── SEE THINGS ──────────────────────────────────────────

kubectl get pods                      # list pods
kubectl get pods -o wide              # list pods with node + IP
kubectl get deployments               # list deployments
kubectl get services                  # list services
kubectl get all                       # list everything

kubectl describe pod <name>           # detailed info (check Events section!)
kubectl describe deployment <name>

# ─── CREATE / UPDATE ─────────────────────────────────────

kubectl apply -f file.yaml            # create or update from YAML
kubectl apply -f folder/              # apply all YAML files in folder

# ─── LOGS ────────────────────────────────────────────────

kubectl logs <pod-name>               # show logs
kubectl logs <pod-name> -f            # follow logs (like tail -f)
kubectl logs <pod-name> --previous    # logs from crashed container

# ─── GO INSIDE ───────────────────────────────────────────

kubectl exec -it <pod-name> -- /bin/sh       # shell into a pod
kubectl exec -it <pod-name> -- /bin/bash     # bash (if available)

# ─── DELETE ──────────────────────────────────────────────

kubectl delete -f file.yaml           # delete what the YAML describes
kubectl delete pod <name>             # delete a specific pod
kubectl delete deployment <name>      # delete deployment + all its pods

# ─── SCALE ───────────────────────────────────────────────

kubectl scale deployment <name> --replicas=5

# ─── ROLLOUT ─────────────────────────────────────────────

kubectl rollout status deployment/<name>     # watch update progress
kubectl rollout undo deployment/<name>       # rollback
kubectl rollout history deployment/<name>    # see versions

# ─── PORT FORWARD (testing) ─────────────────────────────

kubectl port-forward pod/<name> 8080:80      # localhost:8080 → pod:80
kubectl port-forward svc/<name> 8080:80      # localhost:8080 → service:80

# ─── NAMESPACE ───────────────────────────────────────────

kubectl get pods -n <namespace>              # list pods in a namespace
kubectl get pods --all-namespaces            # list pods in ALL namespaces
kubectl config set-context --current --namespace=<ns>  # change default ns
```

### Speed Up Your Life

```bash
# Set up aliases (add to ~/.bashrc or ~/.zshrc)
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias kaf='kubectl apply -f'

# Now: kgp instead of kubectl get pods
```

---

## 16. Debugging

### Pod is in "Pending" State

```bash
kubectl describe pod <name>
# Look at the Events section at the bottom:

# "Insufficient cpu" → node doesn't have enough CPU
#   Fix: reduce resource requests, or add more nodes

# "Insufficient memory" → node doesn't have enough memory

# "no nodes match pod topology spread" → constraints too strict

# "Unschedulable" → all nodes are full or tainted
```

### Pod is in "CrashLoopBackOff"

```bash
# Your container starts but keeps crashing
kubectl logs <pod-name>               # see current logs
kubectl logs <pod-name> --previous    # see logs from LAST crash

# Common causes:
#   - App crashes on startup (check your code!)
#   - Missing environment variable
#   - Wrong command in Dockerfile
#   - Database not reachable
#   - File not found
```

### Pod is in "ImagePullBackOff"

```bash
kubectl describe pod <name>
# "Failed to pull image: image not found"

# Common causes:
#   - Typo in image name
#   - Image doesn't exist in the registry
#   - Private registry needs authentication
#   - Wrong tag
```

### Service Not Working

```bash
# Check if Service has endpoints (Pod IPs)
kubectl get endpoints <service-name>
# If "none" → selector doesn't match any Pods!
# Check: do your Pod labels match the Service selector?

# Test from inside the cluster
kubectl run debug --image=busybox --rm -it -- /bin/sh
# Then inside:
wget -qO- http://my-app-service
nslookup my-app-service
```

### The Debug Checklist

```
1. kubectl get pods                    → is the Pod running?
2. kubectl describe pod <name>         → check Events section
3. kubectl logs <name>                 → check application logs
4. kubectl logs <name> --previous      → check crash logs
5. kubectl get endpoints <svc>         → does Service find Pods?
6. kubectl exec -it <pod> -- /bin/sh   → go inside and debug
```

---

## 17. Your First Real Deployment

Let's deploy a real web app step by step.

### Step 1: Create a Namespace

```bash
kubectl create namespace my-web-app
```

### Step 2: Create All Resources

```yaml
# Save as my-web-app.yaml

# --- ConfigMap for environment variables ---
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-config
  namespace: my-web-app
data:
  APP_ENV: "production"
  APP_PORT: "80"

---
# --- Deployment ---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: my-web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: web-config
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            memory: "128Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /
            port: 80
          periodSeconds: 10

---
# --- Service ---
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: my-web-app
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80

---
# --- HPA ---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web
  namespace: my-web-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Step 3: Deploy It

```bash
# Apply everything
kubectl apply -f my-web-app.yaml

# Watch it come up
kubectl get all -n my-web-app

# Test it
kubectl port-forward -n my-web-app svc/web 8080:80
# Open http://localhost:8080

# See the pods
kubectl get pods -n my-web-app

# Check the HPA
kubectl get hpa -n my-web-app

# Update the image
kubectl set image deployment/web nginx=nginx:1.26 -n my-web-app

# Watch the rolling update
kubectl rollout status deployment/web -n my-web-app

# Clean up when done
kubectl delete namespace my-web-app
```

---

## 18. What to Learn Next

### Your Learning Path

```
You Are Here ──────────────────────────────────────────────────►

Week 1-2: (this guide)
  ✓ Pods, Deployments, Services
  ✓ ConfigMaps, Secrets
  ✓ Probes, Resources, HPA
  ✓ Namespaces, Labels
  ✓ kubectl commands
  ✓ Basic debugging

Week 3-4: (read KUBERNETES.md sections 1-8)
  □ Kubernetes architecture (how it works under the hood)
  □ DaemonSets, StatefulSets, Jobs
  □ Storage (PV, PVC, StorageClass)
  □ RBAC (who can do what)
  □ Network Policies

Week 5-6: (read KUBERNETES.md sections 9-14)
  □ Helm (package manager)
  □ Ingress deep dive
  □ Kustomize
  □ Pod security

Month 2: (read KUBERNETES.md sections 15-24)
  □ Istio service mesh
  □ ArgoCD (GitOps)
  □ Observability (Prometheus, Grafana)
  □ Autoscaling (HPA, VPA, KEDA)

Month 3+: (read KUBERNETES_ADVANCED.md)
  □ Custom operators
  □ eBPF / Cilium
  □ Multi-cluster
  □ Supply chain security
  □ Scheduler plugins
```

### Recommended Practice

```
1. Deploy your own app (not just nginx)
   - Build a Docker image of any app you've written
   - Push it to Docker Hub
   - Deploy it on Kubernetes with a Deployment + Service

2. Break things on purpose
   - Delete a Pod, watch it recreate
   - Set memory limit too low, see OOMKill
   - Set wrong image name, debug ImagePullBackOff
   - Crash your app, read the logs

3. Try the 01-basic-microservice project
   - It's a real FastAPI app with probes, metrics, and graceful shutdown
   - Deploy it with Kustomize (staging overlay)
   - Deploy it with Helm

4. Use k9s (terminal UI for Kubernetes)
   brew install k9s
   k9s
   # Makes navigating your cluster much easier
```

### Key Concepts Glossary

```
Cluster:        a set of machines running Kubernetes
Node:           one machine in the cluster
Pod:            one or more containers running together
Deployment:     manages Pods (scaling, updates, self-healing)
Service:        stable address + load balancer for Pods
Namespace:      logical group (like a folder)
ConfigMap:      configuration data (non-sensitive)
Secret:         sensitive data (passwords, keys)
Label:          key-value tag on any object
Selector:       filter to find objects by label
Probe:          health check
HPA:            auto-scaler based on metrics
Ingress:        HTTP routing (host/path → Service)
PVC:            request for persistent storage
kubectl:        CLI tool to interact with Kubernetes
YAML:           the file format Kubernetes uses
```

---

*This guide covers everything you need for Week 1-2.*
*When you're comfortable, graduate to KUBERNETES.md for the deep stuff.*
