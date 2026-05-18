# Kubernetes — Staff Engineer Enterprise Reference

> From cluster internals to production-grade enterprise architecture.
> Every concept explained with the why, every YAML is production-ready.
> Read top-to-bottom once; use as a reference thereafter.

---

## Table of Contents

1. [Kubernetes Architecture & Control Plane](#1-kubernetes-architecture--control-plane)
2. [Core Workload Objects](#2-core-workload-objects)
3. [Services & Networking](#3-services--networking)
4. [Storage — PV / PVC / StorageClass](#4-storage)
5. [Configuration — ConfigMaps & Secrets](#5-configuration--configmaps--secrets)
6. [RBAC & Security](#6-rbac--security)
7. [Resource Management & QoS](#7-resource-management--qos)
8. [Health Probes & Pod Lifecycle](#8-health-probes--pod-lifecycle)
9. [Autoscaling — HPA / VPA / KEDA](#9-autoscaling)
10. [Ingress & Gateway API](#10-ingress--gateway-api)
11. [Helm — Package Management](#11-helm--package-management)
12. [StatefulSets — Databases & Queues](#12-statefulsets--databases--queues)
13. [Jobs & CronJobs](#13-jobs--cronjobs)
14. [Network Policies](#14-network-policies)
15. [Service Mesh — Istio](#15-service-mesh--istio)
16. [GitOps — ArgoCD](#16-gitops--argocd)
17. [Observability — Metrics / Logs / Traces](#17-observability)
18. [Custom Resources & Operators](#18-custom-resources--operators)
19. [Multi-Tenancy & Namespace Strategy](#19-multi-tenancy--namespace-strategy)
20. [Cluster Management & Upgrades](#20-cluster-management--upgrades)
21. [Cost Optimisation](#21-cost-optimisation)
22. [Disaster Recovery & High Availability](#22-disaster-recovery--high-availability)
23. [Enterprise Production Architecture](#23-enterprise-production-architecture)
24. [Critical kubectl Commands Cheat-Sheet](#24-critical-kubectl-commands)

---

## 1. Kubernetes Architecture & Control Plane

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                             │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    CONTROL PLANE (Masters)                       │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │  API Server  │  │  Scheduler   │  │ Controller Manager   │  │  │
│  │  │  (kube-      │  │  (kube-      │  │ (kube-controller-    │  │  │
│  │  │  apiserver)  │  │  scheduler)  │  │  manager)            │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │  │
│  │         │                 │                    │                 │  │
│  │         └────────────┬────┘                    │                 │  │
│  │                      ▼                         │                 │  │
│  │              ┌──────────────┐                  │                 │  │
│  │              │     etcd     │◄─────────────────┘                 │  │
│  │              │ (distributed │                                     │  │
│  │              │  key-value)  │                                     │  │
│  │              └──────────────┘                                     │  │
│  │                                                 ┌──────────────┐ │  │
│  │                                                 │ Cloud        │ │  │
│  │                                                 │ Controller   │ │  │
│  │                                                 │ Manager      │ │  │
│  │                                                 └──────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  │
│  │     Worker Node 1  │  │     Worker Node 2  │  │     Worker Node N  │  │
│  │                   │  │                   │  │                   │  │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │
│  │  │   kubelet   │  │  │  │   kubelet   │  │  │  │   kubelet   │  │  │
│  │  └─────────────┘  │  │  └─────────────┘  │  │  └─────────────┘  │  │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │
│  │  │ kube-proxy  │  │  │  │ kube-proxy  │  │  │  │ kube-proxy  │  │  │
│  │  └─────────────┘  │  │  └─────────────┘  │  │  └─────────────┘  │  │
│  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │  ┌─────────────┐  │  │
│  │  │  Container  │  │  │  │  Container  │  │  │  │  Container  │  │  │
│  │  │  Runtime    │  │  │  │  Runtime    │  │  │  │  Runtime    │  │  │
│  │  │ (containerd)│  │  │  │ (containerd)│  │  │  │ (containerd)│  │  │
│  │  └─────────────┘  │  │  └─────────────┘  │  │  └─────────────┘  │  │
│  │                   │  │                   │  │                   │  │
│  │  [Pod] [Pod]      │  │  [Pod] [Pod]      │  │  [Pod] [Pod]      │  │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

### Control Plane Components

**kube-apiserver** — The only component that talks to etcd. All writes go through it.
```
- Validates and admits API objects (admission controllers)
- Enforces RBAC
- Serves the Kubernetes REST API
- Horizontally scalable (run 3+ for HA)
- Stateless: state lives in etcd
```

**etcd** — Distributed key-value store. The source of truth.
```
- Raft consensus protocol (odd number of members: 3 or 5)
- All cluster state persisted here
- Quorum needed: 3 nodes tolerate 1 failure, 5 tolerate 2
- Backup etcd → you can recover the entire cluster
- latency-sensitive: put on fast SSD, low-latency network
```

**kube-scheduler** — Assigns Pods to Nodes.
```
Algorithm:
  1. Filtering: eliminate nodes that cannot run the pod
     (resource requests, nodeSelector, taints, affinity)
  2. Scoring: rank remaining nodes
     (LeastRequestedPriority, BalancedResourceAllocation, NodeAffinity)
  3. Binding: write node name to Pod spec in etcd

Extensible: custom schedulers, scheduling plugins, scheduler framework
```

**kube-controller-manager** — Runs all built-in controllers as goroutines.
```
Key controllers:
  ReplicaSet controller:    ensure desired Pod count
  Deployment controller:    manage rollouts
  StatefulSet controller:   ordered, stable pod management
  Job controller:           run-to-completion workloads
  Node controller:          detect/evict pods from failed nodes
  Endpoint controller:      populate Endpoints objects for Services
  ServiceAccount controller: create default SAs and API tokens
  Namespace controller:     handle namespace deletion lifecycle
```

**Cloud Controller Manager** — Integrates with cloud provider APIs.
```
  Node controller:           detect/delete cloud VM instances
  Route controller:          set up network routes in the cloud
  Service controller:        create/update/delete cloud load balancers
```

### Worker Node Components

**kubelet** — The node agent. Talks to the API server, manages pods.
```
Responsibilities:
  - Register node with API server
  - Watch for PodSpecs assigned to this node
  - Start/stop containers via CRI (Container Runtime Interface)
  - Run liveness/readiness/startup probes
  - Report node and pod status back to API server
  - Mount volumes
  - Stream logs
```

**kube-proxy** — Network proxy. Implements Service VIP (Virtual IP).
```
Modes:
  iptables (default): insert iptables rules for DNAT; stateless, scale issues at 10k+ services
  IPVS:              kernel-level load balancing; O(1) vs O(n) for iptables; supports more LB algorithms
  eBPF (Cilium):     bypass iptables entirely; best performance, observability

kube-proxy watches Services + Endpoints and keeps rules in sync
```

**Container Runtime** — Runs containers. CRI (Container Runtime Interface) abstraction.
```
containerd (most common): Docker-compatible, battle-tested
CRI-O:                    lightweight, Kubernetes-specific
gVisor (runsc):           sandboxed containers (user-space kernel)
Kata Containers:          VM-based isolation for multi-tenant
```

### How a Pod Gets Scheduled (End-to-End)

```
1. kubectl apply → API server validates YAML, writes to etcd
2. Scheduler watches etcd for Pods with no node → scores/selects node → writes nodeName
3. kubelet on target node watches etcd → sees Pod assigned to it
4. kubelet calls CRI (containerd) to pull image and start container
5. kubelet calls CNI plugin (Calico/Cilium) to set up pod networking
6. kubelet calls CSI plugin to mount any volumes
7. kubelet runs probes; updates Pod status in etcd
8. Endpoint controller adds Pod IP to Service Endpoints
9. kube-proxy updates iptables/IPVS rules on all nodes
10. Traffic can now reach the Pod
```

---

## 2. Core Workload Objects

### Pod — The Atomic Unit

A Pod is one or more containers sharing a network namespace and volumes.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-pod
  namespace: production
  labels:
    app: api
    version: "2.0"
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
spec:
  # Init containers run to completion before app containers start
  initContainers:
  - name: migrate
    image: myapp:2.0
    command: ["python", "manage.py", "migrate"]
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: url

  containers:
  - name: api
    image: myapp:2.0
    ports:
    - containerPort: 8080
      name: http
    - containerPort: 9090
      name: metrics
    
    resources:
      requests:           # scheduler uses these for placement
        memory: "256Mi"
        cpu: "250m"
      limits:             # enforced by cgroups
        memory: "512Mi"
        cpu: "500m"
    
    env:
    - name: APP_ENV
      value: "production"
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secrets
    
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
      readOnly: true
    - name: tmp
      mountPath: /tmp

    # Security context per container
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      runAsGroup: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]

  # Sidecar containers (K8s 1.29+: native sidecar support)
  - name: log-shipper
    image: fluent-bit:latest
    restartPolicy: Always    # native sidecar: stays up while main container runs
    volumeMounts:
    - name: logs
      mountPath: /var/log

  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: tmp
    emptyDir: {}
  - name: logs
    emptyDir: {}

  # Pod-level security context
  securityContext:
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault

  # Graceful shutdown: SIGTERM, wait terminationGracePeriodSeconds, then SIGKILL
  terminationGracePeriodSeconds: 30
  
  # Restart policy: Always | OnFailure | Never
  restartPolicy: Always
  
  # Service account for IRSA / Workload Identity
  serviceAccountName: api-service-account
  
  # Prevent scheduling on same node as another instance
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values: ["api"]
          topologyKey: kubernetes.io/hostname
```

### Deployment — Stateless Apps

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app: api
spec:
  replicas: 3
  
  # How pods are selected (must match template.metadata.labels)
  selector:
    matchLabels:
      app: api
  
  # Rolling update strategy (zero-downtime deployments)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0       # never kill pods before new ones ready
      maxSurge: 1             # allow 1 extra pod during rollout
  
  # How many old ReplicaSets to keep (kubectl rollout history)
  revisionHistoryLimit: 10
  
  # Minimum seconds a pod must be ready before considered "available"
  minReadySeconds: 10
  
  template:
    metadata:
      labels:
        app: api
        version: "2.0"
    spec:
      # ... (same as Pod spec above)
      containers:
      - name: api
        image: myapp:2.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Deployment Rollout Commands:**
```bash
# Trigger rollout (update image)
kubectl set image deployment/api api=myapp:2.1 -n production

# Watch rollout progress
kubectl rollout status deployment/api -n production

# View history
kubectl rollout history deployment/api -n production

# Rollback to previous version
kubectl rollout undo deployment/api -n production

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=3 -n production

# Pause/resume rollout (useful for canary)
kubectl rollout pause deployment/api -n production
kubectl rollout resume deployment/api -n production
```

### ReplicaSet vs Deployment

```
ReplicaSet: ensures N copies of a pod template are running
Deployment: manages ReplicaSets; enables rollouts and rollbacks

Always use Deployment. Never create ReplicaSets directly.
```

### DaemonSet — One Pod Per Node

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true         # access host networking
      hostPID: true             # access host PID namespace
      tolerations:              # run on ALL nodes including masters
      - operator: Exists
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
          hostPort: 9100
        securityContext:
          privileged: true       # node-level access needed
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys

# Use cases: log collectors (Fluentd), monitoring agents (node-exporter),
#            CNI plugins, storage agents, security agents (Falco)
```

### StatefulSet — Overview (Details in Section 12)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless   # required: headless service name
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  # Pods get stable names: postgres-0, postgres-1, postgres-2
  # Ordered creation and deletion (0 first, N-1 last)
  # Stable network identity: postgres-0.postgres-headless.namespace.svc.cluster.local
  template:
    ...
  volumeClaimTemplates:            # each pod gets its own PVC
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

---

## 3. Services & Networking

### Service Types

**ClusterIP (default)** — Internal cluster access only
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: api               # routes to pods matching these labels
  ports:
  - name: http
    port: 80               # Service port
    targetPort: 8080       # Pod port (or named port)
    protocol: TCP
  - name: grpc
    port: 9090
    targetPort: 9090
# Assigned a stable VIP: e.g. 10.96.45.213
# DNS: api.production.svc.cluster.local
```

**NodePort** — Exposes on every node's IP at a static port
```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080          # 30000-32767 range
# Access: <NodeIP>:30080
# Use case: bare metal, development; avoid in production (poor LB)
```

**LoadBalancer** — Cloud provider creates an external load balancer
```yaml
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 8080
  # Cloud annotations for customisation:
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:..."
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
# Creates AWS NLB / GCP GLB / Azure LB automatically
```

**Headless Service** — No VIP, DNS returns pod IPs directly
```yaml
spec:
  clusterIP: None           # headless
  selector:
    app: postgres
# DNS: postgres-0.postgres-headless.namespace.svc.cluster.local → specific pod IP
# Use case: StatefulSets, peer discovery, client-side load balancing
```

**ExternalName** — DNS CNAME to external service
```yaml
spec:
  type: ExternalName
  externalName: rds.us-east-1.amazonaws.com
# Use case: point k8s workloads at external databases during migration
```

### DNS Resolution in Kubernetes

```
CoreDNS runs as a Deployment in kube-system namespace.

Pod DNS search domains:
  <service>.<namespace>.svc.cluster.local
  <namespace>.svc.cluster.local
  svc.cluster.local
  cluster.local

Within same namespace: curl http://api          → resolves
Cross namespace:       curl http://api.payments → resolves
FQDN:                  curl http://api.payments.svc.cluster.local → always works

Pod FQDN: 10-96-45-213.production.pod.cluster.local (dashes for dots)
StatefulSet pod: postgres-0.postgres.production.svc.cluster.local
```

### Endpoints & EndpointSlices

```bash
# Service selects pods → Endpoint controller creates Endpoints
kubectl get endpoints api -n production

# EndpointSlice (newer, scales to 1000s of pods)
kubectl get endpointslices -n production -l kubernetes.io/service-name=api
```

**Why EndpointSlices matter:** Classic Endpoints stores all pod IPs in one object → huge network updates for large deployments. EndpointSlices shard at 100 pods each → incremental updates, scales to 10k+ pods.

### Pod-to-Pod Networking (CNI)

```
Every pod gets a unique IP. Pods communicate directly without NAT.

CNI Plugins:
  Calico:    eBPF or iptables, network policy, BGP routing, IPAM
  Cilium:    eBPF-native, best observability (Hubble), L7 policies, no kube-proxy
  Flannel:   simple overlay (VXLAN), no network policy support
  WeaveNet:  overlay, supports encryption
  AWS VPC CNI: pods get VPC IPs directly (no overlay), native AWS peering

Overlay networks:
  VXLAN: encapsulate L2 in UDP (port 4789); works anywhere
  GENEVE: like VXLAN, more extensible
  BGP:   no encapsulation, route pod CIDRs via BGP; faster, requires BGP-capable network

Recommendation: Use Cilium for eBPF performance + network policy + observability
```

### Service Topology & Traffic Policy

```yaml
spec:
  # Route traffic only to pods on the same node (reduce cross-zone latency/cost)
  internalTrafficPolicy: Local        # Kubernetes 1.26+
  externalTrafficPolicy: Local        # preserve source IP, avoid double-hop
  
  # Traffic distribution (1.31+)
  trafficDistribution: PreferClose    # prefer same zone, fallback to other zones
```

---

## 4. Storage

### Storage Hierarchy

```
StorageClass (admin defines)
    → PersistentVolume (provisioned automatically or manually)
        → PersistentVolumeClaim (developer requests)
            → Pod (mounts the claim)
```

### StorageClass — Dynamic Provisioning

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: ebs.csi.aws.com          # CSI driver
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:..."
reclaimPolicy: Retain                  # Delete | Retain | Recycle
allowVolumeExpansion: true             # allow online resize
volumeBindingMode: WaitForFirstConsumer # don't provision until pod is scheduled (multi-AZ)
mountOptions:
  - noatime
  - discard
```

**Reclaim Policies:**
```
Delete: volume deleted when PVC deleted (default for cloud)
Retain: volume kept, PV enters Released state; admin must manually reclaim
```

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce          # RWO: one node at a time (block storage)
  # - ReadWriteMany        # RWX: many nodes simultaneously (NFS, EFS)
  # - ReadOnlyMany         # ROX: many nodes read-only
  # - ReadWriteOncePod     # RWOP: single pod (K8s 1.22+)
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
  # Optional: select a specific pre-provisioned PV
  # selector:
  #   matchLabels:
  #     env: production
```

### Volume Types

```yaml
# EmptyDir: ephemeral, tied to pod lifecycle
volumes:
- name: cache
  emptyDir:
    medium: Memory           # tmpfs (RAM-backed)
    sizeLimit: "512Mi"

# HostPath: mount host directory (dangerous, breaks pod portability)
- name: docker-sock
  hostPath:
    path: /var/run/docker.sock
    type: Socket

# ConfigMap as volume
- name: nginx-config
  configMap:
    name: nginx-config
    items:
    - key: nginx.conf
      path: nginx.conf

# Secret as volume (mounted as files)
- name: tls-certs
  secret:
    secretName: tls-secret
    defaultMode: 0400         # file permissions

# CSI volume (projected from secret store)
- name: vault-secrets
  csi:
    driver: secrets-store.csi.x-k8s.io
    readOnly: true
    volumeAttributes:
      secretProviderClass: vault-secrets
```

### Volume Snapshots

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-2026-04-07
spec:
  volumeSnapshotClassName: csi-aws-vsc
  source:
    persistentVolumeClaimName: postgres-data
---
# Restore from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-restore
spec:
  dataSource:
    name: postgres-snapshot-2026-04-07
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

---

## 5. Configuration — ConfigMaps & Secrets

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
  # Multi-line (file content)
  nginx.conf: |
    server {
      listen 80;
      location / {
        proxy_pass http://localhost:8080;
      }
    }
  config.yaml: |
    database:
      pool_size: 10
      timeout: 30
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: production
type: Opaque                         # or kubernetes.io/tls, kubernetes.io/dockerconfigjson
stringData:                          # plain text, auto-encoded to base64
  DB_PASSWORD: "supersecret"
  DB_URL: "postgresql://user:pass@host:5432/db"
---
# TLS secret
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-cert>
  tls.key: <base64-key>
```

**Secret Management Best Practices — Enterprise:**
```
Problem: Secrets in etcd are base64-encoded, NOT encrypted by default.

Solutions:

1. Encryption at Rest (etcd):
   Enable EncryptionConfiguration with AES-CBC or AES-GCM provider
   or KMS provider (AWS KMS, GCP CKMS, Azure Key Vault)

2. External Secrets Operator (ESO):
   Sync secrets from AWS Secrets Manager / Vault / GCP Secret Manager into K8s Secrets
   Secret lives in the external store; K8s Secret is auto-synced

3. Secrets Store CSI Driver:
   Mount secrets directly from Vault/AWS SM as volumes
   Secret never written to etcd (ephemeral)
   Works with IRSA / Workload Identity for auth

4. HashiCorp Vault Agent Injector:
   Sidecar reads from Vault and writes to shared memory volume
   App reads from /vault/secrets/...

Recommendation: ESO + AWS Secrets Manager for AWS deployments
               Vault + CSI Driver for multi-cloud / on-prem
```

### External Secrets Operator Pattern

```yaml
# ExternalSecret fetches from AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
  - secretKey: DB_PASSWORD
    remoteRef:
      key: production/db/credentials
      property: password
  - secretKey: DB_URL
    remoteRef:
      key: production/db/credentials
      property: url
```

---

## 6. RBAC & Security

### RBAC Model

```
Subject (who)   → RoleBinding / ClusterRoleBinding → Role / ClusterRole (what)

Subjects:
  User:           external user (certificate CN or OIDC claim)
  Group:          set of users (certificate O or OIDC group claim)
  ServiceAccount: in-cluster identity for pods

Scope:
  Role + RoleBinding:               namespaced (recommended)
  ClusterRole + ClusterRoleBinding: cluster-wide (use sparingly)
```

### Role & RoleBinding

```yaml
# Define what actions are allowed on which resources
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-role
  namespace: production
rules:
- apiGroups: [""]                    # "" = core API group
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: []                          # no access to secrets
---
# Bind the role to a service account
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-role-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: api-service-account
  namespace: production
roleRef:
  kind: Role
  name: api-role
  apiGroup: rbac.authorization.k8s.io
---
# Service Account for the application
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-service-account
  namespace: production
  annotations:
    # AWS: IRSA (IAM Roles for Service Accounts)
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/api-production-role
    # GCP: Workload Identity
    # iam.gke.io/gcp-service-account: api@project.iam.gserviceaccount.com
automountServiceAccountToken: false   # disable auto-mounting unless needed
```

### ClusterRole for Cross-Namespace Access

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["nodes", "pods"]
  verbs: ["get", "list"]
---
# Bind to a namespace-specific service account (common pattern for monitoring)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus-node-reader
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

### Pod Security Standards (PSS) — Replaces PodSecurityPolicy

```yaml
# Applied as namespace labels
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # enforce: block non-compliant pods
    # audit: log violations but allow
    # warn: warn but allow
    pod-security.kubernetes.io/enforce: restricted    # strictest
    pod-security.kubernetes.io/enforce-version: v1.29
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

# Levels:
#   privileged: no restrictions (system namespaces only)
#   baseline:   prevents privilege escalation, hostPath, hostNetwork
#   restricted: all baseline + runAsNonRoot, seccompProfile, drop ALL caps
```

### Admission Controllers — Enterprise Security Gates

```
Built-in important controllers:
  NamespaceLifecycle:   prevent actions in terminating namespaces
  LimitRanger:          enforce resource limits/requests
  ResourceQuota:        enforce namespace quotas
  PodSecurity:          enforce Pod Security Standards
  NodeRestriction:      restrict kubelet API access
  MutatingAdmissionWebhook: call external webhook to mutate objects
  ValidatingAdmissionWebhook: call external webhook to validate/reject

Custom admission controllers (enterprise use cases):
  OPA/Gatekeeper: policy-as-code for governance
  Kyverno:        Kubernetes-native policy engine
  Falco:          runtime security (not an admission controller, but threat detection)

Example Kyverno policy — require labels:
```

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-team-label
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-team-label
    match:
      any:
      - resources:
          kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    validate:
      message: "Workloads must have a 'team' label"
      pattern:
        metadata:
          labels:
            team: "?*"
```

### Network Security — mTLS with Istio (Preview)

```
All pod-to-pod communication encrypted with mTLS via sidecar proxies.
Zero-trust networking: every service has a cryptographic identity (SPIFFE/SPIRE).
Detailed in Section 15.
```

---

## 7. Resource Management & QoS

### Requests vs Limits

```
Requests: used by scheduler for placement; guaranteed to be available
Limits:   enforced by cgroups; hard cap

CPU behaviour:
  Below request:  pod gets its requested CPU guaranteed
  Above request:  pod gets extra CPU if node is idle (burstable)
  Above limit:    throttled (CPU cycles stolen)

Memory behaviour:
  Below request:  guaranteed
  Above limit:    OOMKilled (container killed, restarted)
  
Never set CPU limit in production (causes unnecessary throttling).
Always set memory limit (unbounded memory growth = OOMKill or node pressure).
```

### QoS Classes

```
Guaranteed:
  requests == limits for ALL containers
  Never evicted except when exceeding limits
  Highest priority during node pressure

Burstable:
  requests < limits (or limits not set)
  Evicted based on usage above requests

BestEffort:
  No requests or limits set
  First to be evicted under pressure
  Never use for production workloads

Recommendation:
  Stateful workloads (databases): Guaranteed (predictable performance)
  Stateless services: Burstable (with requests set, limits for memory only)
  Batch jobs: BestEffort or Burstable (they can be restarted)
```

### LimitRange — Namespace Defaults

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - type: Container
    default:          # applied if no limits specified
      memory: "512Mi"
      cpu: "500m"
    defaultRequest:   # applied if no requests specified
      memory: "256Mi"
      cpu: "100m"
    max:              # hard cap regardless of what pod specifies
      memory: "4Gi"
      cpu: "2"
    min:
      memory: "64Mi"
      cpu: "50m"
  - type: PersistentVolumeClaim
    max:
      storage: "100Gi"
    min:
      storage: "1Gi"
```

### ResourceQuota — Namespace Budget

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    # Compute
    requests.cpu: "20"
    limits.cpu: "40"
    requests.memory: "40Gi"
    limits.memory: "80Gi"
    
    # Object counts
    pods: "100"
    services: "20"
    services.loadbalancers: "2"
    services.nodeports: "0"
    
    # Storage
    requests.storage: "500Gi"
    persistentvolumeclaims: "20"
    fast-ssd.storageclass.storage.k8s.io/requests.storage: "200Gi"
    
    # Secrets, ConfigMaps
    secrets: "50"
    configmaps: "50"
```

### Node Taints & Tolerations

```yaml
# Taint a node (kubectl taint nodes gpu-node-1 gpu=true:NoSchedule)
# Only pods that TOLERATE this taint will be scheduled here

# Pod toleration
spec:
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"    # NoSchedule | PreferNoSchedule | NoExecute

# Common taints:
#   node.kubernetes.io/not-ready:NoExecute           (auto-applied by node controller)
#   node.kubernetes.io/unreachable:NoExecute
#   node-role.kubernetes.io/control-plane:NoSchedule (master nodes)
#   spot.kubernetes.io/interrupt:NoSchedule          (spot instance eviction warning)
```

### Node Affinity

```yaml
spec:
  affinity:
    nodeAffinity:
      # Hard requirement
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values: ["amd64"]
          - key: node.kubernetes.io/instance-type
            operator: In
            values: ["m5.xlarge", "m5.2xlarge"]
      
      # Soft preference
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values: ["us-east-1a"]
    
    # Spread pods across zones AND nodes
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: api
        topologyKey: topology.kubernetes.io/zone
```

### Topology Spread Constraints

```yaml
# Ensure even distribution across zones and nodes
spec:
  topologySpreadConstraints:
  - maxSkew: 1                    # max difference in pod count between zones
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: api
  - maxSkew: 2
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway   # soft constraint
    labelSelector:
      matchLabels:
        app: api
```

---

## 8. Health Probes & Pod Lifecycle

### Three Probe Types

```yaml
spec:
  containers:
  - name: api
    
    # startupProbe: gives slow-starting containers time to initialise
    # Disables liveness + readiness during startup
    startupProbe:
      httpGet:
        path: /healthz/startup
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 5
      failureThreshold: 30        # up to 150s (30×5) to start
      successThreshold: 1
    
    # livenessProbe: is the container alive? Failure → restart
    livenessProbe:
      httpGet:
        path: /healthz/live
        port: 8080
        httpHeaders:
        - name: Accept
          value: application/json
      initialDelaySeconds: 0      # seconds after startup before first probe
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3         # restart after 3 consecutive failures
      successThreshold: 1
    
    # readinessProbe: is the container ready to receive traffic?
    # Failure → removed from Service endpoints
    readinessProbe:
      httpGet:
        path: /healthz/ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
      successThreshold: 1
    
    # Alternative probe types:
    # TCP socket:
    # tcpSocket:
    #   port: 5432
    
    # Execute command:
    # exec:
    #   command: ["pg_isready", "-U", "postgres"]
    
    # gRPC:
    # grpc:
    #   port: 9090
    #   service: "grpc.health.v1.Health"
```

### What Each Probe Endpoint Should Do

```python
# /healthz/startup — is init complete?
@app.get("/healthz/startup")
async def startup():
    if not database_migration_complete:
        raise HTTPException(503)
    return {"status": "ok"}

# /healthz/live — is the process healthy?
# Should be FAST and check only the process itself (not dependencies)
@app.get("/healthz/live")
async def liveness():
    return {"status": "ok"}

# /healthz/ready — can this pod serve traffic?
# Check dependencies: DB connection, cache, etc.
@app.get("/healthz/ready")
async def readiness():
    try:
        await db.execute("SELECT 1")
        await cache.ping()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(503, detail=str(e))
```

### Graceful Shutdown

```
Pod deletion sequence:
1. Pod enters Terminating state
2. Endpoints controller removes pod from Service endpoints (traffic stops)
3. kubelet sends SIGTERM to PID 1
4. Pod has terminationGracePeriodSeconds (default 30s) to finish in-flight requests
5. kubelet sends SIGKILL if not exited

Problem: Step 2 and 3 happen roughly simultaneously — iptables rules may
         still route traffic after SIGTERM arrives.

Solution: Add a preStop hook with sleep to allow iptables rules to propagate:
```

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
  - name: api
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 5"]   # wait for iptables propagation
      # Or use httpGet to drain:
      # preStop:
      #   httpGet:
      #     path: /shutdown
      #     port: 8080
    # Application must:
    # 1. Stop accepting new connections on SIGTERM
    # 2. Finish in-flight requests (up to grace period - 5s)
    # 3. Close DB connections
    # 4. Exit cleanly
```

### PodDisruptionBudget — Control Voluntary Disruptions

```yaml
# Ensure at least 2 pods are always available during node drains, upgrades
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: production
spec:
  minAvailable: 2          # absolute number, or "80%" percentage
  # maxUnavailable: 1      # alternative: max pods that can be unavailable
  selector:
    matchLabels:
      app: api
# kubectl drain respects PDB — waits for pods to be rescheduled before evicting
# Critical for zero-downtime cluster upgrades
```

---

## 9. Autoscaling

### HPA — Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 50
  
  metrics:
  # CPU (built-in)
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # target 70% of request
  
  # Memory (built-in)
  - type: Resource
    resource:
      name: memory
      target:
        type: AverageValue
        averageValue: "400Mi"
  
  # Custom metric from Prometheus via adapter
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  
  # External metric (e.g., SQS queue depth)
  - type: External
    external:
      metric:
        name: sqs_queue_depth
        selector:
          matchLabels:
            queue: payment-events
      target:
        type: Value
        value: "500"
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60     # prevent flapping
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60               # add up to 4 pods per minute
      - type: Percent
        value: 100
        periodSeconds: 60               # or double, whichever is smaller
      selectPolicy: Min
    scaleDown:
      stabilizationWindowSeconds: 300   # 5 min window before scale-down
      policies:
      - type: Pods
        value: 2
        periodSeconds: 120             # remove at most 2 pods per 2 minutes
```

### VPA — Vertical Pod Autoscaler

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Off"       # Off | Initial | Recreate | Auto
    # Off:       only recommend, don't change (use for rightsizing info)
    # Initial:   set on pod creation only
    # Recreate:  evict and restart pods to apply new resources
    # Auto:      same as Recreate (in-place update in future)
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      maxAllowed:
        cpu: "4"
        memory: "8Gi"
      controlledResources: ["cpu", "memory"]
```

**VPA + HPA conflict:** Don't use VPA in Auto mode with HPA on the same resource. Use VPA for memory, HPA for CPU — or use VPA in Off mode for recommendations only.

### KEDA — Kubernetes Event-Driven Autoscaler

Scale deployments (including to zero) based on external event sources.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-scaler
  namespace: production
spec:
  scaleTargetRef:
    name: payment-worker
  minReplicaCount: 0           # scale to zero when idle!
  maxReplicaCount: 100
  cooldownPeriod: 300
  
  triggers:
  # AWS SQS
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123/payments
      queueLength: "5"         # 1 pod per 5 messages
      awsRegion: us-east-1
    authenticationRef:
      name: keda-aws-auth
  
  # Kafka
  - type: kafka
    metadata:
      bootstrapServers: kafka:9092
      consumerGroup: payment-processor
      topic: payments
      lagThreshold: "50"       # 1 pod per 50 messages of lag
  
  # Cron (scheduled scaling)
  - type: cron
    metadata:
      timezone: America/New_York
      start: 0 9 * * 1-5       # 9am weekdays
      end: 0 18 * * 1-5        # 6pm weekdays
      desiredReplicas: "10"
  
  # Prometheus
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: http_request_rate
      query: sum(rate(http_requests_total[2m]))
      threshold: "500"
```

### Cluster Autoscaler (Node Autoscaling)

```
Cluster Autoscaler watches for:
  - Unschedulable pods (scale UP: add node)
  - Underutilised nodes with evictable pods (scale DOWN: remove node)

Cloud-specific implementations:
  AWS:   Cluster Autoscaler + Auto Scaling Groups, or Karpenter (preferred)
  GCP:   GKE Autopilot or node auto-provisioning
  Azure: AKS cluster autoscaler

Karpenter (AWS — next gen):
  - Provisions ANY node type based on pod requirements (no node groups)
  - Directly calls EC2 Fleet API (faster than ASG: 2s vs 2min)
  - Automatically selects cheapest/fastest instance type
  - Consolidation: bin-packs pods, terminates underutilised nodes

Node group configuration:
  min_size: 3
  max_size: 100
  expander: least-waste | random | most-pods | priority
```

---

## 10. Ingress & Gateway API

### Ingress (Legacy but Widely Used)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: nginx
    # SSL redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "10"
    # Timeouts
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    # Rewrite
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://app.example.com"
    # WAF (with ModSecurity)
    nginx.ingress.kubernetes.io/enable-modsecurity: "true"
    # Cert-Manager (auto TLS)
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret       # cert-manager auto-populates this
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/v1(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-v1
            port:
              number: 80
      - path: /api/v2(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-v2
            port:
              number: 80
```

### Gateway API (Modern — Kubernetes SIG)

More expressive, role-oriented split: Platform team manages GatewayClass/Gateway; App team manages HTTPRoute.

```yaml
# Platform team — cluster-scoped
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: prod-gateway
  namespace: gateway-system
spec:
  gatewayClassName: istio              # or nginx, cilium, envoy
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-tls
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            gateway-access: allowed
---
# App team — namespace-scoped
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: production
spec:
  parentRefs:
  - name: prod-gateway
    namespace: gateway-system
  hostnames: ["api.example.com"]
  rules:
  # Canary: 10% to v2, 90% to v1 (traffic weighting)
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-v1
      port: 80
      weight: 90
    - name: api-v2
      port: 80
      weight: 10
  # Header-based routing (A/B testing)
  - matches:
    - headers:
      - name: X-Feature-Flag
        value: new-api
    backendRefs:
    - name: api-v2
      port: 80
```

### Cert-Manager — Automatic TLS

```yaml
# ClusterIssuer using Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: platform@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - dns01:                         # DNS-01 for wildcard certs
        route53:
          region: us-east-1
          hostedZoneID: ZXXXXX
---
# Certificate (auto-renews 30 days before expiry)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-cert
  namespace: production
spec:
  secretName: api-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.example.com
  - "*.api.example.com"
```

---

## 11. Helm — Package Management

### Why Helm

```
Problem: Kubernetes manifests are environment-specific (dev vs prod differ in replicas, images, limits)
Solution: Helm templates with values files per environment

Helm concepts:
  Chart:    package of Kubernetes manifests + templates
  Release:  deployed instance of a chart
  Values:   configuration injected into templates
  Repository: collection of charts
```

### Chart Structure

```
my-app/
├── Chart.yaml              # metadata (name, version, appVersion, dependencies)
├── values.yaml             # default values
├── values-staging.yaml     # staging overrides
├── values-production.yaml  # production overrides
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── serviceaccount.yaml
│   ├── configmap.yaml
│   ├── _helpers.tpl        # reusable template functions
│   └── NOTES.txt           # displayed after install
├── charts/                 # sub-charts (dependencies)
└── .helmignore
```

### Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: Production API service
type: application
version: 1.5.0              # chart version
appVersion: "2.0.0"         # application version
dependencies:
- name: postgresql
  version: "12.5.6"
  repository: https://charts.bitnami.com/bitnami
  condition: postgresql.enabled
- name: redis
  version: "17.11.6"
  repository: https://charts.bitnami.com/bitnami
```

### Templates with Values

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        {{- if .Values.resources }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
        {{- end }}
        env:
        {{- range .Values.env }}
        - name: {{ .name }}
          value: {{ .value | quote }}
        {{- end }}
        {{- with .Values.extraEnvFrom }}
        envFrom:
          {{- toYaml . | nindent 10 }}
        {{- end }}
```

```yaml
# values.yaml
replicaCount: 3
image:
  repository: myregistry.azurecr.io/my-app
  pullPolicy: IfNotPresent
  tag: ""   # overridden at deploy time

resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 50
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  hostname: api.example.com

env:
  - name: APP_ENV
    value: production
  - name: LOG_LEVEL
    value: info

postgresql:
  enabled: false    # use external RDS
```

### Helm Commands

```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install / Upgrade (atomic)
helm upgrade --install my-app ./my-app \
  --namespace production \
  --create-namespace \
  --values values-production.yaml \
  --set image.tag=2.0.1 \
  --atomic \                       # rollback on failure
  --timeout 5m \
  --wait

# Dry-run (see rendered YAML)
helm template my-app ./my-app --values values-production.yaml
helm install --dry-run --debug my-app ./my-app

# List releases
helm list -n production

# Rollback
helm rollback my-app 3 -n production   # rollback to revision 3

# Diff (requires helm-diff plugin)
helm diff upgrade my-app ./my-app --values values-production.yaml

# Test
helm test my-app -n production
```

### Helmfile — Multi-Chart Management

```yaml
# helmfile.yaml
repositories:
- name: bitnami
  url: https://charts.bitnami.com/bitnami

releases:
- name: my-app
  namespace: production
  chart: ./charts/my-app
  values:
  - values/production.yaml
  set:
  - name: image.tag
    value: {{ requiredEnv "IMAGE_TAG" }}

- name: postgresql
  namespace: production
  chart: bitnami/postgresql
  version: "12.5.6"
  values:
  - values/postgresql-production.yaml
```

---

## 12. StatefulSets — Databases & Queues

### StatefulSet Guarantees

```
1. Stable, unique network identity:
   postgres-0.postgres.production.svc.cluster.local
   postgres-1.postgres.production.svc.cluster.local

2. Stable, persistent storage:
   Each pod gets its own PVC (data-postgres-0, data-postgres-1)
   PVC survives pod restart and rescheduling

3. Ordered, graceful deployment:
   Create: 0, 1, 2, ... (wait for each to be Ready before next)
   Delete: N-1, N-2, ..., 0 (reverse order)
   Update: like delete + create (but can use RollingUpdate)

4. Ordered, automated rolling updates:
   Updates one pod at a time, starting from the highest ordinal
```

### Production StatefulSet Example (PostgreSQL)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres-headless
  replicas: 3
  podManagementPolicy: OrderedReady    # or Parallel (faster for non-dependent pods)
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                      # update all pods; set to N to update only pods ≥ N (canary)
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      serviceAccountName: postgres-sa
      securityContext:
        runAsUser: 999                   # postgres user
        fsGroup: 999
      
      initContainers:
      - name: init-chmod-data
        image: busybox
        command: ["sh", "-c", "chown -R 999:999 /data"]
        volumeMounts:
        - name: data
          mountPath: /data
      
      containers:
      - name: postgres
        image: postgres:15.4
        ports:
        - containerPort: 5432
        
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: PGDATA
          value: /data/pgdata
        
        # Replication env vars (for read replicas)
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.name   # postgres-0, postgres-1...
        
        resources:
          requests:
            memory: "4Gi"
            cpu: "1"
          limits:
            memory: "8Gi"              # Guaranteed QoS for primary
        
        volumeMounts:
        - name: data
          mountPath: /data
        - name: config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
        
        livenessProbe:
          exec:
            command: ["pg_isready", "-U", "$(POSTGRES_USER)", "-d", "$(POSTGRES_DB)"]
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 6
        
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "$(POSTGRES_USER)", "-d", "$(POSTGRES_DB)"]
          initialDelaySeconds: 5
          periodSeconds: 5
        
      volumes:
      - name: config
        configMap:
          name: postgres-config
  
  # Each pod gets its own PVC
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 500Gi
---
# Headless service for stable DNS
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: production
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
---
# Regular service for the primary (write endpoint)
apiVersion: v1
kind: Service
metadata:
  name: postgres-primary
  namespace: production
spec:
  selector:
    app: postgres
    role: primary           # requires pod to label itself
  ports:
  - port: 5432
```

### Operators for Stateful Workloads

For production databases, use an Operator instead of raw StatefulSets:

| Workload | Recommended Operator |
|---------|---------------------|
| PostgreSQL | CloudNative PG (CNPG), Crunchy Postgres |
| MySQL | Percona Operator for MySQL |
| Redis | Redis Operator (spotahome), Redis Cluster Operator |
| Kafka | Strimzi Kafka Operator |
| Elasticsearch | ECK (Elastic Cloud on Kubernetes) |
| Cassandra | K8ssandra Operator |
| MongoDB | MongoDB Community Operator |
| Zookeeper | ZooKeeper Operator |

---

## 13. Jobs & CronJobs

### Job — Run to Completion

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: production
spec:
  completions: 1               # number of successful completions needed
  parallelism: 1               # pods running in parallel
  backoffLimit: 3              # retries on failure
  activeDeadlineSeconds: 600   # fail if not complete in 10 minutes
  ttlSecondsAfterFinished: 3600  # clean up 1 hour after completion
  
  # For parallel work (indexed jobs)
  # completionMode: Indexed    # pods get JOB_COMPLETION_INDEX env var
  
  template:
    spec:
      restartPolicy: OnFailure  # Never | OnFailure (not Always)
      containers:
      - name: migration
        image: myapp:2.0
        command: ["python", "manage.py", "migrate", "--run-syncdb"]
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
```

### CronJob — Scheduled Jobs

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: report-generator
  namespace: production
spec:
  schedule: "0 2 * * *"          # daily at 2am UTC
  timeZone: "America/New_York"   # K8s 1.27+
  concurrencyPolicy: Forbid      # Allow | Forbid | Replace
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  startingDeadlineSeconds: 300   # if missed, skip if >5min late
  
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600
      template:
        spec:
          restartPolicy: OnFailure
          serviceAccountName: report-sa
          containers:
          - name: reporter
            image: reports:latest
            command: ["python", "generate_report.py"]
            env:
            - name: REPORT_DATE
              value: "yesterday"
            resources:
              requests:
                memory: "1Gi"
                cpu: "500m"
```

---

## 14. Network Policies

By default, all pods can talk to all pods. Network Policies restrict this.

```yaml
# Deny all ingress and egress for namespace (start from zero-trust)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}             # selects all pods
  policyTypes:
  - Ingress
  - Egress
---
# Allow API pods to receive traffic from ingress controller only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  # From ingress controller namespace
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  # From monitoring (Prometheus scraping)
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: monitoring
    ports:
    - protocol: TCP
      port: 9090
---
# Allow API pods egress to database only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Egress
  egress:
  # To database
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  # To Redis
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # To DNS (always needed)
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
  # To external APIs
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8       # block internal IPs not explicitly allowed
    ports:
    - protocol: TCP
      port: 443
```

**Cilium Network Policy (L7):**
```yaml
# Cilium extends with L7 HTTP policies
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-http-policy
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/api/.*"
        - method: POST
          path: "/api/orders"
          # Only GET /api/* and POST /api/orders allowed
```

---

## 15. Service Mesh — Istio

### Why a Service Mesh?

```
Problem without service mesh:
  - mTLS requires every app to implement TLS client/server
  - Retries, circuit breaking, timeouts in every client library
  - Distributed tracing requires manual header propagation
  - Traffic splitting requires code changes for canary deploys

Service mesh solution: transparent proxy (Envoy sidecar) handles all this
  - App code doesn't change
  - All network behaviour configured via CRDs
```

### Istio Architecture

```
Data Plane: Envoy sidecars injected into every pod
Control Plane: istiod (Pilot, Citadel, Galley in one binary)

istiod:
  - Pilot: pushes routing rules to Envoy (xDS protocol)
  - Citadel: issues SPIFFE X.509 certs (mTLS identities)
  - Galley: config validation
```

### Enable Istio Injection

```bash
# Namespace auto-injection
kubectl label namespace production istio-injection=enabled

# Per-pod control
metadata:
  annotations:
    sidecar.istio.io/inject: "false"   # disable for this pod
```

### Traffic Management

```yaml
# VirtualService: routing rules for requests to a service
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: api
  namespace: production
spec:
  hosts:
  - api                    # Kubernetes service name
  - api.example.com        # or external hostname
  http:
  # Header-based routing (A/B test)
  - match:
    - headers:
        x-user-type:
          exact: beta
    route:
    - destination:
        host: api
        subset: v2
  
  # Weighted routing (canary: 10% to v2)
  - route:
    - destination:
        host: api
        subset: v1
      weight: 90
    - destination:
        host: api
        subset: v2
      weight: 10
    
    # Timeout
    timeout: 10s
    
    # Retry policy
    retries:
      attempts: 3
      perTryTimeout: 3s
      retryOn: "gateway-error,connect-failure,retriable-4xx"
    
    # Fault injection (chaos engineering)
    fault:
      delay:
        percentage:
          value: 5.0
        fixedDelay: 2s
      abort:
        percentage:
          value: 1.0
        httpStatus: 503
---
# DestinationRule: define subsets and load balancing
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: api
  namespace: production
spec:
  host: api
  
  # mTLS for all traffic to this service
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL        # mTLS
    
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 1000
    
    # Circuit breaker (outlier detection)
    outlierDetection:
      consecutiveGatewayErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50     # never eject more than 50% of hosts
  
  subsets:
  - name: v1
    labels:
      version: "1.0"
  - name: v2
    labels:
      version: "2.0"
---
# PeerAuthentication: enforce mTLS for entire namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT            # STRICT | PERMISSIVE | DISABLE
---
# AuthorizationPolicy: L7 access control
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: api
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/frontend-sa"]  # SPIFFE identity
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]
```

---

## 16. GitOps — ArgoCD

### GitOps Principles

```
1. Declarative: entire system state described in Git
2. Versioned: Git is the source of truth, with full audit history
3. Automatic: approved changes are automatically applied
4. Continuously reconciled: agents detect and correct drift
```

### ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Git Repository                          │
│   manifests/production/*.yaml                                │
│   helm/values-production.yaml                                │
└────────────────────────────┬────────────────────────────────┘
                             │ (poll or webhook)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    ArgoCD (in cluster)                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  API Server  │  │  Repository  │  │  Application       │ │
│  │  (UI/API)    │  │  Server      │  │  Controller        │ │
│  └──────────────┘  └──────────────┘  └────────────────────┘ │
│                                               │              │
│                                    Compares desired (git)    │
│                                    vs live (cluster state)   │
│                                    Syncs automatically       │
└─────────────────────────────────────────────────────────────┘
```

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-production
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io  # cascade delete
spec:
  project: production
  
  source:
    repoURL: https://github.com/myorg/k8s-config
    targetRevision: main
    path: apps/my-app/production
    
    # Or Helm source:
    # chart: my-app
    # repoURL: https://charts.myorg.com
    # targetRevision: 1.5.0
    # helm:
    #   valueFiles: ["values-production.yaml"]
    #   parameters:
    #   - name: image.tag
    #     value: "2.0.1"
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    automated:
      prune: true           # delete resources removed from git
      selfHeal: true        # revert manual changes to cluster
      allowEmpty: false     # never sync empty app (safety)
    
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - ApplyOutOfSyncOnly=true   # only apply changed resources
    
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  
  # Health/sync status checks
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas    # ignore HPA-managed replica count
```

### ApplicationSet — Multi-Cluster/Multi-Env

```yaml
# Deploy to all clusters matching a pattern
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
  namespace: argocd
spec:
  generators:
  - clusters:
      selector:
        matchLabels:
          environment: production
  template:
    metadata:
      name: "my-app-{{name}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/k8s-config
        targetRevision: main
        path: "apps/my-app/{{metadata.labels.environment}}"
      destination:
        server: "{{server}}"
        namespace: production
```

### Image Updater

```yaml
# ArgoCD Image Updater: automatically update image tags in git
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: myapp=myregistry.io/myapp
    argocd-image-updater.argoproj.io/myapp.update-strategy: semver
    argocd-image-updater.argoproj.io/myapp.allow-tags: regexp:^[0-9]+\.[0-9]+\.[0-9]+$
    argocd-image-updater.argoproj.io/write-back-method: git
```

---

## 17. Observability

### The Three Pillars

```
Metrics:  numeric time-series (CPU %, req/sec, error rate, latency p99)
Logs:     structured text events (what happened and when)
Traces:   request flow across services (where time was spent)

+  Profiles (continuous profiling — flame graphs)
+  Events (Kubernetes events: FailedScheduling, OOMKilled)
```

### Prometheus Stack

```yaml
# Prometheus scrapes /metrics endpoints
# ServiceMonitor tells Prometheus what to scrape

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-monitor
  namespace: monitoring
  labels:
    release: prometheus      # must match Prometheus selector
spec:
  selector:
    matchLabels:
      app: api
  namespaceSelector:
    matchNames: ["production"]
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
    # Auth if needed
    # bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
---
# PrometheusRule: alerting rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: monitoring
spec:
  groups:
  - name: api.rules
    interval: 30s
    rules:
    # Recording rule (precompute expensive query)
    - record: job:http_requests:rate5m
      expr: sum(rate(http_requests_total[5m])) by (job, status)
    
    # Alert: error rate
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
        /
        sum(rate(http_requests_total[5m])) by (service)
        > 0.05
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High error rate on {{ $labels.service }}"
        description: "Error rate is {{ $value | humanizePercentage }}"
        runbook: https://wiki.example.com/runbooks/high-error-rate
    
    # Alert: pod restart loop
    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 * 5 > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping"
```

### Grafana Dashboard as Code

```yaml
# ConfigMap with Grafana dashboard JSON (auto-loaded via sidecar)
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"    # picked up by Grafana sidecar
data:
  api-dashboard.json: |
    {
      "title": "API Service",
      "panels": [...]
    }
```

### Structured Logging

```python
# Always emit JSON structured logs — queryable in Loki/CloudWatch/Datadog
import structlog
logger = structlog.get_logger()

logger.info("request.processed",
    method="POST",
    path="/api/orders",
    status=201,
    duration_ms=45,
    trace_id="abc123",
    user_id="u-456",
    order_id="ord-789")
```

```yaml
# Fluent Bit DaemonSet config to ship to Loki
[INPUT]
    Name tail
    Path /var/log/containers/*.log
    Parser docker
    Tag kube.*
    Mem_Buf_Limit 50MB

[FILTER]
    Name kubernetes
    Match kube.*
    Merge_Log On
    Keep_Log Off
    K8S-Logging.Parser On

[OUTPUT]
    Name loki
    Match *
    Host loki.monitoring.svc.cluster.local
    Port 3100
    Labels job=fluentbit, namespace=$kubernetes['namespace_name']
```

### Distributed Tracing — OpenTelemetry

```python
# Instrument your application
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

tracer = trace.get_tracer(__name__)

@app.post("/api/orders")
async def create_order(order: OrderRequest):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("user.id", order.user_id)
        span.set_attribute("order.amount", order.amount)
        result = await order_service.create(order)
        span.set_attribute("order.id", result.id)
        return result
```

```yaml
# OpenTelemetry Collector (DaemonSet or Deployment)
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
  namespace: monitoring
spec:
  mode: DaemonSet
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    
    processors:
      batch:
        timeout: 5s
      memory_limiter:
        limit_percentage: 80
    
    exporters:
      otlp:
        endpoint: jaeger.monitoring.svc.cluster.local:4317
      prometheus:
        endpoint: 0.0.0.0:8889
    
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [otlp]
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [prometheus]
```

### Golden Signals (SRE Framework)

```
Latency:    time to serve a request (p50, p95, p99, p999)
Traffic:    requests per second
Errors:     rate of failed requests (5xx, timeouts)
Saturation: how "full" the service is (CPU %, memory %, queue depth)

SLI: measured value (e.g., p99 latency)
SLO: target (e.g., p99 latency < 500ms, 99.9% of time over 30 days)
SLA: contract (SLO + consequences for breach)
Error Budget: 1 - SLO = how much failure you can afford

Error budget depletion → freeze deployments, focus on reliability
Error budget healthy → invest in features
```

---

## 18. Custom Resources & Operators

### Custom Resource Definition (CRD)

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.myorg.io
spec:
  group: myorg.io
  versions:
  - name: v1alpha1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: ["engine", "size"]
            properties:
              engine:
                type: string
                enum: ["postgres", "mysql"]
              size:
                type: string
                enum: ["small", "medium", "large"]
              replicas:
                type: integer
                minimum: 1
                maximum: 5
                default: 1
          status:
            type: object
            properties:
              phase:
                type: string
              endpoint:
                type: string
    subresources:
      status: {}          # enable status subresource (separate update)
    additionalPrinterColumns:
    - name: Engine
      type: string
      jsonPath: .spec.engine
    - name: Size
      type: string
      jsonPath: .spec.size
    - name: Phase
      type: string
      jsonPath: .status.phase
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames: ["db"]
```

### Operator Pattern with controller-runtime (Go)

```go
// Reconciler: the core of an operator
type DatabaseReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}

func (r *DatabaseReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := log.FromContext(ctx)
    
    // 1. Fetch the custom resource
    db := &myorgv1alpha1.Database{}
    if err := r.Get(ctx, req.NamespacedName, db); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // 2. Add finalizer for cleanup
    if !controllerutil.ContainsFinalizer(db, "myorg.io/finalizer") {
        controllerutil.AddFinalizer(db, "myorg.io/finalizer")
        return ctrl.Result{}, r.Update(ctx, db)
    }
    
    // 3. Handle deletion
    if !db.DeletionTimestamp.IsZero() {
        return r.reconcileDelete(ctx, db)
    }
    
    // 4. Reconcile desired state
    statefulSet := r.buildStatefulSet(db)
    if err := ctrl.SetControllerReference(db, statefulSet, r.Scheme); err != nil {
        return ctrl.Result{}, err
    }
    
    // CreateOrUpdate: idempotent reconciliation
    op, err := ctrl.CreateOrUpdate(ctx, r.Client, statefulSet, func() error {
        statefulSet.Spec.Replicas = &db.Spec.Replicas
        return nil
    })
    log.Info("StatefulSet reconciled", "operation", op)
    
    // 5. Update status
    db.Status.Phase = "Running"
    db.Status.Endpoint = fmt.Sprintf("%s.%s.svc.cluster.local", db.Name, db.Namespace)
    return ctrl.Result{RequeueAfter: time.Minute}, r.Status().Update(ctx, db)
}

// Register with controller-runtime
func (r *DatabaseReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&myorgv1alpha1.Database{}).
        Owns(&appsv1.StatefulSet{}).    // watch owned resources
        Owns(&corev1.Service{}).
        WithOptions(controller.Options{MaxConcurrentReconciles: 5}).
        Complete(r)
}
```

### Operator Maturity Levels

```
Level 1 — Basic Install:     automate installation
Level 2 — Seamless Upgrades: handle version upgrades
Level 3 — Full Lifecycle:    backup, restore, failure recovery
Level 4 — Deep Insights:     metrics, alerts, dashboards
Level 5 — Auto Pilot:        auto-scaling, auto-tune, auto-remediation
```

---

## 19. Multi-Tenancy & Namespace Strategy

### Namespace Patterns

```
Pattern 1 — Namespace per environment (simple):
  development, staging, production
  
  Pros:  simple, easy RBAC
  Cons:  all teams share production namespace, blast radius is large

Pattern 2 — Namespace per team (recommended for enterprise):
  payments-production, orders-production, users-production
  
  Pros:  team isolation, separate quotas, clear ownership
  Cons:  cross-team service discovery requires FQDN

Pattern 3 — Namespace per service:
  Very fine-grained, high operational overhead
  Use only if strong isolation is required (PCI, HIPAA)

Pattern 4 — Virtual clusters (vCluster):
  Each team gets a full API server (virtual), shares physical nodes
  Best isolation, higher overhead
```

### Namespace Bootstrap Template

```yaml
# Automated with a Kustomize base or Helm chart
---
apiVersion: v1
kind: Namespace
metadata:
  name: payments-production
  labels:
    team: payments
    environment: production
    cost-center: "42"
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: payments-quota
  namespace: payments-production
spec:
  hard:
    requests.cpu: "10"
    limits.cpu: "20"
    requests.memory: "20Gi"
    limits.memory: "40Gi"
    pods: "50"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: payments-limits
  namespace: payments-production
spec:
  limits:
  - type: Container
    default: {memory: "512Mi", cpu: "500m"}
    defaultRequest: {memory: "256Mi", cpu: "100m"}
---
# RBAC for team
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: payments-team-binding
  namespace: payments-production
subjects:
- kind: Group
  name: payments-team        # OIDC group
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit                 # built-in: create/update/delete most resources
  apiGroup: rbac.authorization.k8s.io
```

### Hierarchical Namespace Controller (HNC)

```bash
# HNC: namespace hierarchy with policy inheritance
kubectl hns create payments-staging -n payments
kubectl hns create payments-production -n payments

# NetworkPolicy, RBAC, ResourceQuota propagates down from parent
```

---

## 20. Cluster Management & Upgrades

### Node Management

```bash
# Drain a node (safely evict all pods before maintenance)
kubectl drain node-1 \
  --ignore-daemonsets \        # DaemonSet pods remain
  --delete-emptydir-data \     # allow eviction of emptyDir pods
  --grace-period=120 \         # give pods time to shut down
  --timeout=300s

# Make node unschedulable (without evicting)
kubectl cordon node-1

# Restore after maintenance
kubectl uncordon node-1

# Check node resource usage
kubectl top nodes

# Describe node (see allocatable resources, taints, conditions)
kubectl describe node node-1
```

### Cluster Upgrade Strategy (Zero Downtime)

```
Kubernetes version format: Major.Minor.Patch (e.g., 1.29.3)
Skew policy: kubelet can be at most 2 minor versions behind API server
             API server must be upgraded before nodes

Recommended upgrade order:
1. Take etcd snapshot (backup)
2. Upgrade control plane (API server, controller manager, scheduler)
   - HA cluster: upgrade one control plane node at a time
   - Cloud managed (EKS/GKE/AKS): point-and-click or one command
3. Upgrade node groups (rolling, one group at a time)
   - Cordon node → drain → upgrade OS + kubelet + kubectl → uncordon
   - Or: create new node group with new version, migrate workloads, delete old
4. Upgrade add-ons (CoreDNS, kube-proxy, CNI, metrics-server)

PodDisruptionBudget + minReadySeconds ensure no downtime during node drain.

EKS blue-green upgrade:
  Create new node group (v1.30)
  Label old nodes: kubectl taint nodes -l eks.amazonaws.com/nodegroup=v129 upgrade=true:NoSchedule
  Pods reschedule to new nodes automatically
  Delete old node group when empty
```

### etcd Backup & Restore

```bash
# Snapshot etcd (run on a control plane node)
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify snapshot
etcdctl snapshot status /backup/etcd-backup.db --write-out=table

# Restore (stops etcd, replaces data dir)
etcdctl snapshot restore /backup/etcd-backup.db \
  --data-dir=/var/lib/etcd-restore \
  --initial-cluster=master-1=https://10.0.0.1:2380
```

---

## 21. Cost Optimisation

### Spot / Preemptible Instances

```yaml
# Use Spot instances for fault-tolerant workloads (70-90% cheaper)
# Node group with Spot (EKS)
# Karpenter NodePool with spot preference:
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: spot-pool
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]    # prefer spot, fallback to on-demand
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["m5.xlarge", "m5.2xlarge", "m4.xlarge", "m4.2xlarge"]  # diversify!
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 1m
  limits:
    cpu: 1000
    memory: 4000Gi
```

**Spot best practices:**
```
- Diversify instance types across multiple families (never single instance type)
- Use Spot interruption handlers (AWS Node Termination Handler)
- Deploy across 3+ AZs
- Use PodDisruptionBudgets to limit simultaneous evictions
- Good for: batch workers, ML training, stateless services
- Avoid for: databases, single-replica critical services
```

### Rightsizing

```bash
# Use VPA recommendations to find proper requests
kubectl describe vpa api-vpa -n production
# Or use Goldilocks (wrapper around VPA)
helm install goldilocks fairwinds-stable/goldilocks
kubectl label namespace production goldilocks.fairwinds.com/enabled=true
# Visit Goldilocks dashboard for recommendations

# Kubecost: cost allocation per namespace/workload
helm install kubecost cost-analyzer/cost-analyzer --namespace kubecost
```

### Namespace Cost Allocation

```yaml
# Label everything for cost allocation
metadata:
  labels:
    team: payments
    environment: production
    cost-center: "42"
    product: checkout

# Kubecost uses these labels to attribute cloud costs to teams
```

### Common Cost Savings

```
1. Rightsizing: reduce overprovisioned requests (average ~60% overprovisioned)
2. Spot instances: 70-90% cheaper for appropriate workloads
3. Scale to zero: KEDA scale deployments to 0 pods when idle
4. Arm64 (Graviton): 20-40% cheaper per vCPU on AWS
5. Reserved instances: commit 1-3 years for baseline compute
6. Delete unused resources: orphaned PVs, load balancers, old images
7. Compress container images: use distroless or Alpine base images
8. Egress optimisation: prefer same-AZ traffic (avoid cross-AZ data transfer)
```

---

## 22. Disaster Recovery & High Availability

### Multi-AZ HA Design

```
Control Plane HA:
  - 3 control plane nodes across 3 AZs
  - etcd with 3 members (quorum: needs 2)
  - API server load balanced (cloud LB or Keepalived + VIP)

Worker Node HA:
  - Node groups in 3+ AZs
  - topologySpreadConstraints to spread pods across AZs
  - PodDisruptionBudgets to prevent AZ loss from killing all replicas

Data HA:
  - PostgreSQL: primary + replica across AZs, automated failover (Patroni/CNPG)
  - Redis: Redis Cluster (3 primary + 3 replica, across AZs)
  - S3/GCS/Azure Blob: naturally multi-AZ (zone-redundant)
```

### Velero — Cluster Backup

```bash
# Install Velero with AWS S3 backend
velero install \
  --provider aws \
  --bucket my-velero-backup \
  --region us-east-1 \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1

# Scheduled backup (entire cluster, daily)
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --ttl 720h \
  --include-namespaces production \
  --snapshot-volumes true

# On-demand backup
velero backup create pre-upgrade-backup --include-namespaces production

# Restore
velero restore create --from-backup pre-upgrade-backup \
  --include-namespaces production \
  --namespace-mappings production:production-restore
```

### Multi-Cluster Strategy

```
Pattern 1 — Active-Passive DR:
  Primary cluster active, standby warm (hourly synced)
  RTO: 30-60 minutes, RPO: 1 hour
  Use: Velero restore to standby cluster

Pattern 2 — Active-Active:
  Traffic split across clusters with global LB (Route53, Cloudflare, GFE)
  Each cluster independent, data replicated
  RTO: seconds (DNS failover), RPO: near zero
  Use: mission-critical applications

Pattern 3 — Active-Active-Active (Multi-Region):
  Clusters in us-east-1, eu-west-1, ap-southeast-1
  Per-region primary, cross-region replication
  Latency-based routing (serve from nearest region)

Tools:
  Submariner: pod-to-pod networking across clusters
  Cilium ClusterMesh: cross-cluster service discovery + network policy
  Admiral (Istio): multi-cluster traffic management
  Argo Rollouts: cross-cluster canary deployments
```

### Chaos Engineering

```bash
# Chaos Mesh — inject failures to test resilience
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: api-pod-kill
  namespace: production
spec:
  action: pod-kill
  mode: random-max-percent
  value: "30"              # kill 30% of matching pods
  selector:
    namespaces: ["production"]
    labelSelectors:
      app: api
  scheduler:
    cron: "0 10 * * 1"    # every Monday at 10am
EOF

# Other chaos types: NetworkChaos, IOChaos, StressChaos, TimeChaos
```

---

## 23. Enterprise Production Architecture

### Reference Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE KUBERNETES PLATFORM                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     Developer Experience Layer                      │  │
│  │  CI/CD Pipeline    ArgoCD (GitOps)    Developer Portal (Backstage) │  │
│  └─────────────────────────────┬──────────────────────────────────────┘  │
│                                │                                         │
│  ┌─────────────────────────────▼──────────────────────────────────────┐  │
│  │                      Traffic Management Layer                        │  │
│  │  CloudFront / CDN → AWS NLB → Nginx Ingress / Istio Gateway        │  │
│  │  WAF, DDoS protection, Rate Limiting, TLS Termination               │  │
│  └─────────────────────────────┬──────────────────────────────────────┘  │
│                                │                                         │
│  ┌─────────────────────────────▼──────────────────────────────────────┐  │
│  │                      Service Mesh (Istio)                            │  │
│  │  mTLS everywhere, Circuit Breaking, Retries, Distributed Tracing    │  │
│  └─────────────────────────────┬──────────────────────────────────────┘  │
│                                │                                         │
│  ┌──────────┐ ┌──────────┐ ┌──▼────────┐ ┌──────────┐ ┌────────────┐  │
│  │ payments │ │ orders   │ │ users     │ │ inventory│ │ shipping   │  │
│  │ namespace│ │ namespace│ │ namespace │ │ namespace│ │ namespace  │  │
│  │          │ │          │ │           │ │          │ │            │  │
│  │ HPA+KEDA │ │ HPA+KEDA │ │ HPA+KEDA  │ │ HPA+KEDA │ │ HPA+KEDA   │  │
│  │ Spot+OD  │ │ Spot+OD  │ │ Spot+OD   │ │ Spot+OD  │ │ Spot+OD    │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬──────┘  │
│       └─────────────┴─────────────┴─────────────┴─────────────┘         │
│                                   │                                      │
│  ┌─────────────────────────────────▼──────────────────────────────────┐  │
│  │                     Data Platform Layer                              │  │
│  │  RDS (CNPG operator)    ElastiCache (Redis)    MSK (Kafka)          │  │
│  │  S3 (via IRSA)          DynamoDB               OpenSearch           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     Platform Services                                │  │
│  │  Prometheus + Grafana (metrics)    Loki (logs)    Tempo (traces)    │  │
│  │  Cert-Manager    External Secrets  Kyverno (policy)  Velero (backup)│  │
│  │  Karpenter (nodes)    KEDA (scaling)    ArgoCD (GitOps)             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Deployment Patterns

**Blue-Green:**
```yaml
# Two identical environments; switch traffic between them
# blue = current production, green = new version

# Switch: update Service selector from blue to green
kubectl patch service api -p '{"spec":{"selector":{"version":"green"}}}'
# Rollback: switch back
kubectl patch service api -p '{"spec":{"selector":{"version":"blue"}}}'
```

**Canary (Argo Rollouts):**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: api-canary
      stableService: api-stable
      trafficRouting:
        istio:
          virtualService:
            name: api-vs
      steps:
      - setWeight: 5            # 5% to canary
      - pause: {duration: 10m}
      - analysis:               # automated analysis
          templates:
          - templateName: success-rate
      - setWeight: 20
      - pause: {duration: 10m}
      - setWeight: 50
      - pause: {duration: 10m}
      - setWeight: 100
      
  analysis:
    successCondition: result[0] >= 0.95
    failureCondition: result[0] < 0.90
```

### CI/CD Pipeline Integration

```yaml
# GitHub Actions → build → push → update GitOps repo → ArgoCD syncs
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Build and push image
      run: |
        docker build -t $ECR_REGISTRY/$IMAGE:${{ github.sha }} .
        docker push $ECR_REGISTRY/$IMAGE:${{ github.sha }}
    
    - name: Update GitOps repo
      run: |
        git clone https://github.com/myorg/k8s-config
        cd k8s-config
        # Update image tag in values file
        yq -i '.image.tag = "${{ github.sha }}"' \
          apps/my-app/production/values.yaml
        git commit -am "Update my-app to ${{ github.sha }}"
        git push
    
    # ArgoCD detects change and syncs automatically
```

---

## 24. Critical kubectl Commands

### Debugging

```bash
# Get all resources in namespace
kubectl get all -n production

# Describe (events are at the bottom — check these first)
kubectl describe pod <pod> -n production
kubectl describe node <node>

# Logs
kubectl logs <pod> -n production -c <container>
kubectl logs <pod> -n production --previous       # crashed container logs
kubectl logs -l app=api -n production --tail=100  # all pods with label
kubectl logs <pod> -n production -f               # follow

# Exec into pod
kubectl exec -it <pod> -n production -- /bin/sh

# Copy files to/from pod
kubectl cp <pod>:/etc/config /tmp/config -n production
kubectl cp /tmp/script.sh <pod>:/tmp/script.sh -n production

# Port forward (local debugging)
kubectl port-forward pod/<pod> 8080:8080 -n production
kubectl port-forward svc/api 8080:80 -n production

# Check resource usage
kubectl top pods -n production --sort-by=memory
kubectl top nodes

# Events (sorted by time)
kubectl get events -n production --sort-by='.lastTimestamp'
kubectl get events -n production --field-selector reason=OOMKilled

# Resource diff
kubectl diff -f deployment.yaml
```

### Troubleshooting Patterns

```bash
# Pod stuck in Pending
kubectl describe pod <pod> | grep -A 10 Events
# Check: insufficient resources, node selector mismatch, PVC not bound, taints

# Pod stuck in CrashLoopBackOff
kubectl logs <pod> --previous          # check crash reason
kubectl describe pod <pod>             # check exit code, OOM reason

# Pod stuck in ImagePullBackOff
kubectl describe pod <pod>             # check image name, pull secret

# Service not reaching pods
kubectl get endpoints <service> -n production    # should have pod IPs
kubectl run -it --rm debug --image=busybox -- nslookup api.production.svc.cluster.local

# Network policy blocking traffic
kubectl run -it --rm debug --image=nicolaka/netshoot -- bash
# curl, nslookup, tcpdump, netstat available in netshoot

# Etcd health
kubectl get cs                         # component status (deprecated but useful)
ETCDCTL_API=3 etcdctl endpoint health

# Check admission webhooks (can block pod creation)
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations
```

### Advanced kubectl

```bash
# JSONPath output
kubectl get pods -n production \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Custom columns
kubectl get pods -n production \
  -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName'

# Watch with wide output
kubectl get pods -n production -w -o wide

# Get all pods NOT running
kubectl get pods -n production --field-selector status.phase!=Running

# Force delete stuck pod (use carefully)
kubectl delete pod <pod> -n production --force --grace-period=0

# Patch (inline update)
kubectl patch deployment api -n production \
  -p '{"spec":{"replicas":5}}'

# Annotate (add annotation without full apply)
kubectl annotate deployment api -n production \
  kubernetes.io/change-cause="Deploy version 2.0.1"

# Label
kubectl label node node-1 gpu=true

# Rollout restart (restart all pods without changing spec)
kubectl rollout restart deployment/api -n production

# Scale
kubectl scale deployment api -n production --replicas=10

# Apply server-side (preferred for large CRDs)
kubectl apply --server-side -f manifest.yaml

# Prune (delete resources not in files)
kubectl apply -f . --prune -l app=api

# Generate YAML from running resource
kubectl get deployment api -n production -o yaml > backup.yaml
```

### Useful Aliases & Tools

```bash
# Essential aliases
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kdp='kubectl describe pod'
alias kl='kubectl logs'
alias kex='kubectl exec -it'

# kubectx + kubens: switch clusters and namespaces quickly
kubectx production-cluster
kubens production

# k9s: terminal UI for Kubernetes
k9s -n production

# Stern: multi-pod log tailing
stern -n production -l app=api --tail=50

# kustomize: template-free YAML overlay
kustomize build overlays/production | kubectl apply -f -

# kubecolor: colorised kubectl output
kubecolor get pods

# kubectl-neat: clean up kubectl get -o yaml output
kubectl get deployment api -o yaml | kubectl neat

# Popeye: scan cluster for misconfigurations
popeye -n production

# Pluto: detect deprecated API versions
pluto detect-files -d manifests/

# Trivy: scan images for CVEs
trivy image myapp:2.0
```

---

*Last updated: 2026. Covers Kubernetes 1.29–1.32, Istio 1.20+, ArgoCD 2.10+, Helm 3.x.*
*Tested architectures: AWS EKS, GKE Autopilot, AKS.*
