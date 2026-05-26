# Kubernetes — Advanced & Bleeding-Edge Topics

> Deep-dive into areas beyond the core reference.
> Scheduler internals, eBPF, supply chain security, multi-cluster federation,
> and the newest KEPs (Kubernetes Enhancement Proposals).

---

## Table of Contents

1. [Scheduler Framework & Custom Plugins](#1-scheduler-framework--custom-plugins)
2. [API Priority & Fairness](#2-api-priority--fairness)
3. [In-Place Pod Vertical Scaling](#3-in-place-pod-vertical-scaling)
4. [Sidecar Containers KEP (Native Sidecars)](#4-sidecar-containers-kep)
5. [Writing Admission Webhooks from Scratch](#5-writing-admission-webhooks-from-scratch)
6. [eBPF Deep Dive — Cilium Internals](#6-ebpf-deep-dive--cilium-internals)
7. [Multi-Cluster Federation](#7-multi-cluster-federation)
8. [Supply Chain Security](#8-supply-chain-security)
9. [Pod Security Admission — Advanced Customisation](#9-pod-security-admission--advanced-customisation)
10. [Gateway API — Advanced Routes & Policies](#10-gateway-api--advanced-routes--policies)
11. [Kubernetes Internals — Deep Mechanics](#11-kubernetes-internals--deep-mechanics)
12. [FinOps & Advanced Cost Engineering](#12-finops--advanced-cost-engineering)

---

## 1. Scheduler Framework & Custom Plugins

### Scheduling Framework Architecture

```
The scheduler is a pipeline of extension points.
Each extension point can host multiple plugins.

┌──────────────────────────────────────────────────────────────┐
│                    Scheduling Cycle (per Pod)                   │
│                                                                │
│  PreEnqueue → QueueSort → PreFilter → Filter → PostFilter     │
│  → PreScore → Score → NormalizeScore → Reserve → Permit       │
│                                                                │
│                    Binding Cycle                                │
│  PreBind → Bind → PostBind                                     │
└──────────────────────────────────────────────────────────────┘

Filter:     "can this node run this pod?"  (nodeSelector, taints, resources)
Score:      "rank eligible nodes"          (bin-packing, spread, affinity)
Reserve:    "tentatively claim resources"
Permit:     "wait/approve/deny" (gang scheduling, co-scheduling)
Bind:       "write node assignment to etcd"
```

### Writing a Custom Scheduler Plugin (Go)

```go
package main

import (
    "context"
    "fmt"

    v1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/kubernetes/pkg/scheduler/framework"
)

const PluginName = "GPUBinPack"

type GPUBinPack struct {
    handle framework.Handle
}

var _ framework.ScorePlugin = &GPUBinPack{}

func (g *GPUBinPack) Name() string { return PluginName }

func (g *GPUBinPack) Score(
    ctx context.Context,
    state *framework.CycleState,
    pod *v1.Pod,
    nodeName string,
) (int64, *framework.Status) {
    nodeInfo, err := g.handle.SnapshotSharedLister().NodeInfos().Get(nodeName)
    if err != nil {
        return 0, framework.AsStatus(err)
    }

    // Prefer nodes with more GPUs already allocated (bin-packing)
    allocatedGPU := nodeInfo.Requested.ScalarResources["nvidia.com/gpu"]
    allocatableGPU := nodeInfo.Allocatable.ScalarResources["nvidia.com/gpu"]

    if allocatableGPU == 0 {
        return 0, nil
    }

    // Higher score = more GPUs already in use (pack tightly)
    score := int64((float64(allocatedGPU) / float64(allocatableGPU)) * 100)
    return score, nil
}

func (g *GPUBinPack) ScoreExtensions() framework.ScoreExtensions {
    return nil
}

func New(obj runtime.Object, h framework.Handle) (framework.Plugin, error) {
    return &GPUBinPack{handle: h}, nil
}
```

### Registering the Plugin

```go
package main

import (
    "os"
    "k8s.io/kubernetes/cmd/kube-scheduler/app"
)

func main() {
    command := app.NewSchedulerCommand(
        app.WithPlugin(PluginName, New),
    )
    if err := command.Execute(); err != nil {
        os.Exit(1)
    }
}
```

### Scheduler Configuration (KubeSchedulerConfiguration)

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: gpu-scheduler
  plugins:
    score:
      enabled:
      - name: GPUBinPack
        weight: 10
      disabled:
      - name: NodeResourcesBalancedAllocation
    filter:
      enabled:
      - name: NodeResourcesFit

  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: MostAllocated    # bin-packing instead of spreading
        resources:
        - name: nvidia.com/gpu
          weight: 10
        - name: cpu
          weight: 1
        - name: memory
          weight: 1
```

### Multi-Scheduler Setup

```yaml
# Pod spec: use custom scheduler
spec:
  schedulerName: gpu-scheduler    # default: "default-scheduler"
```

### Scheduler Extenders (Legacy — prefer Framework)

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
extenders:
- urlPrefix: "https://my-extender.svc:443"
  filterVerb: "filter"
  prioritizeVerb: "prioritize"
  weight: 5
  enableHTTPS: true
  httpTimeout: 5s
  managedResources:
  - name: "example.com/custom-resource"
    ignoredByScheduler: true
```

### Coscheduling / Gang Scheduling

```yaml
# Schedule a group of pods together or not at all (ML training, Spark jobs)
# Uses the Coscheduling plugin (scheduler-plugins project)
apiVersion: scheduling.sigs.k8s.io/v1alpha1
kind: PodGroup
metadata:
  name: training-job
spec:
  minMember: 4              # all 4 pods must be schedulable simultaneously
  scheduleTimeoutSeconds: 600
  minResources:
    cpu: "16"
    memory: "64Gi"
    nvidia.com/gpu: "4"
```

---

## 2. API Priority & Fairness

### Why It Matters

```
Problem: A misbehaving controller or a runaway script floods the API server
         with requests → all other clients (kubelet, scheduler, kubectl) starve.

Solution: API Priority & Fairness (APF) replaces max-in-flight with a
          fine-grained queuing system.

Every request is classified into a FlowSchema → PriorityLevelConfiguration.
Each priority level gets a guaranteed share of API server capacity.
Within a priority level, requests are fair-queued by flow distinguisher.
```

### FlowSchema

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: ci-cd-pipeline
spec:
  priorityLevelConfiguration:
    name: workload-low
  distinguisherMethod:
    type: ByUser
  matchingPrecedence: 1000           # lower = matched first
  rules:
  - subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: argocd-application-controller
        namespace: argocd
    resourceRules:
    - verbs: ["get", "list", "watch"]
      apiGroups: ["*"]
      resources: ["*"]
      namespaces: ["*"]
```

### PriorityLevelConfiguration

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: PriorityLevelConfiguration
metadata:
  name: workload-low
spec:
  type: Limited
  limited:
    nominalConcurrencyShares: 10     # relative weight (vs other levels)
    lendablePercent: 50              # can lend 50% of seats to other levels
    limitResponse:
      type: Queue
      queuing:
        queues: 64
        handSize: 6                  # shuffle-sharding width
        queueLengthLimit: 50
```

### Built-in Priority Levels

```
system          — kubelet, kube-proxy (exempt from throttling)
leader-election — controller manager, scheduler leader election
workload-high   — core workloads (namespace controllers, etc.)
workload-low    — general API requests
global-default  — catch-all
exempt          — never throttled (system:masters group)

Monitoring:
  apiserver_flowcontrol_dispatched_requests_total
  apiserver_flowcontrol_rejected_requests_total
  apiserver_flowcontrol_current_inqueue_requests
```

### Debugging APF Issues

```bash
# See all flow schemas and their priority levels
kubectl get flowschema -o wide

# Check which flow schema a request matches
kubectl get --raw /debug/api_priority_and_fairness/dump_priority_levels
kubectl get --raw /debug/api_priority_and_fairness/dump_queues

# Check if requests are being queued/rejected
kubectl get --raw /metrics | grep apiserver_flowcontrol
```

---

## 3. In-Place Pod Vertical Scaling

### Feature Gate (K8s 1.32+ Beta)

```
InPlacePodVerticalScaling: resize CPU/memory without restarting the pod.

Before: change resources → pod killed → rescheduled → downtime
After:  change resources → cgroups updated in-place → no downtime

Perfect for: databases, stateful services, long-running ML inference pods
```

### Usage

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
  - name: api
    image: myapp:2.0
    resources:
      requests:
        cpu: "250m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired     # resize without restart
    - resourceName: memory
      restartPolicy: RestartContainer # memory resize needs restart (Linux limitation)
```

### Resize in Action

```bash
# Patch pod resources (no delete/recreate)
kubectl patch pod api --subresource resize --patch \
  '{"spec":{"containers":[{"name":"api","resources":{"requests":{"cpu":"500m"},"limits":{"cpu":"1"}}}]}}'

# Check resize status
kubectl get pod api -o jsonpath='{.status.resize}'
# Values: Proposed | InProgress | Deferred | Infeasible

# View allocated vs requested
kubectl get pod api -o jsonpath='{.status.containerStatuses[0].allocatedResources}'
```

### VPA Integration with In-Place Resize

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "InPlace"       # new mode: uses in-place resize instead of eviction
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      maxAllowed:
        cpu: "4"
        memory: "8Gi"
```

### Limitations

```
- Memory increase beyond node capacity → Infeasible (pod stays at current size)
- Memory decrease is best-effort (kernel may not reclaim immediately)
- Not all runtimes support it (containerd 1.7+ required)
- Guaranteed QoS pods: requests must stay == limits
- Feature gate must be enabled on kubelet AND API server
```

---

## 4. Sidecar Containers KEP

### Native Sidecar Support (K8s 1.29+ Stable)

```
Problem with classic sidecars:
  - Sidecar in containers[] gets SIGTERM at same time as main container
  - No way to guarantee sidecar outlives main container
  - Init containers run sequentially → sidecar-style init (e.g., Vault agent)
    blocks startup until it exits

Solution: restartPolicy: Always on init containers = native sidecar

Lifecycle:
  1. Regular init containers run to completion (sequentially)
  2. Sidecar init containers start and keep running
  3. Main containers start
  4. On pod termination: main containers get SIGTERM first,
     sidecar init containers get SIGTERM after main exits
```

### Declaration

```yaml
spec:
  initContainers:
  # Regular init: runs to completion, then exits
  - name: db-migrate
    image: myapp:2.0
    command: ["python", "migrate.py"]

  # Native sidecar: starts and keeps running alongside main containers
  - name: vault-agent
    image: hashicorp/vault:latest
    restartPolicy: Always          # this makes it a sidecar
    args: ["agent", "-config=/etc/vault/agent.hcl"]
    volumeMounts:
    - name: vault-secrets
      mountPath: /vault/secrets
    resources:
      requests:
        cpu: "50m"
        memory: "64Mi"
      limits:
        memory: "128Mi"

  - name: istio-proxy
    image: istio/proxyv2:latest
    restartPolicy: Always
    ports:
    - containerPort: 15090
      name: http-envoy-prom

  containers:
  - name: app
    image: myapp:2.0
    volumeMounts:
    - name: vault-secrets
      mountPath: /vault/secrets
      readOnly: true
```

### Startup / Shutdown Ordering

```
Startup:
  1. db-migrate (init) → runs to completion → exits
  2. vault-agent (sidecar init, restartPolicy: Always) → starts, stays running
  3. istio-proxy (sidecar init, restartPolicy: Always) → starts, stays running
  4. app (main container) → starts after all init containers have started

Shutdown:
  1. app receives SIGTERM → terminates
  2. After app exits → istio-proxy receives SIGTERM (reverse init order)
  3. After istio-proxy exits → vault-agent receives SIGTERM
  
This solves the long-standing problem of Istio proxy dying before the app
finishes draining connections.
```

### Sidecar Probes

```yaml
- name: istio-proxy
  restartPolicy: Always
  startupProbe:
    httpGet:
      path: /healthz/ready
      port: 15021
    periodSeconds: 1
    failureThreshold: 30
  # Main containers won't start until sidecar's startup probe passes
  # This guarantees the mesh proxy is ready before the app starts
```

---

## 5. Writing Admission Webhooks from Scratch

### Architecture

```
kubectl apply → API Server → Authentication → Authorization
  → Mutating Admission Webhooks (modify objects)
  → Schema Validation
  → Validating Admission Webhooks (accept/reject)
  → etcd write

Webhook: an HTTPS server that receives AdmissionReview requests
         and returns AdmissionReview responses.
```

### Validating Webhook Server (Go)

```go
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"

    admissionv1 "k8s.io/api/admission/v1"
    appsv1 "k8s.io/api/apps/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/apimachinery/pkg/runtime/serializer"
)

var (
    scheme = runtime.NewScheme()
    codecs = serializer.NewCodecFactory(scheme)
)

func validate(w http.ResponseWriter, r *http.Request) {
    body, _ := io.ReadAll(r.Body)

    var admissionReview admissionv1.AdmissionReview
    codecs.UniversalDeserializer().Decode(body, nil, &admissionReview)

    req := admissionReview.Request
    var deployment appsv1.Deployment
    json.Unmarshal(req.Object.Raw, &deployment)

    allowed := true
    message := "OK"

    // Policy: all deployments must have a "team" label
    if _, ok := deployment.Labels["team"]; !ok {
        allowed = false
        message = "Deployment must have a 'team' label"
    }

    // Policy: production deployments must have >= 2 replicas
    if deployment.Namespace == "production" {
        if deployment.Spec.Replicas != nil && *deployment.Spec.Replicas < 2 {
            allowed = false
            message = "Production deployments must have at least 2 replicas"
        }
    }

    // Policy: resource requests must be set
    for _, c := range deployment.Spec.Template.Spec.Containers {
        if c.Resources.Requests.Cpu().IsZero() || c.Resources.Requests.Memory().IsZero() {
            allowed = false
            message = fmt.Sprintf("Container %s must have CPU and memory requests", c.Name)
        }
    }

    response := admissionv1.AdmissionReview{
        TypeMeta: metav1.TypeMeta{APIVersion: "admission.k8s.io/v1", Kind: "AdmissionReview"},
        Response: &admissionv1.AdmissionResponse{
            UID:     req.UID,
            Allowed: allowed,
            Result: &metav1.Status{
                Message: message,
            },
        },
    }

    respBytes, _ := json.Marshal(response)
    w.Header().Set("Content-Type", "application/json")
    w.Write(respBytes)
}

func main() {
    http.HandleFunc("/validate", validate)
    http.ListenAndServeTLS(":8443", "/certs/tls.crt", "/certs/tls.key", nil)
}
```

### Mutating Webhook Server (Go — JSON Patch)

```go
func mutate(w http.ResponseWriter, r *http.Request) {
    body, _ := io.ReadAll(r.Body)

    var admissionReview admissionv1.AdmissionReview
    codecs.UniversalDeserializer().Decode(body, nil, &admissionReview)

    req := admissionReview.Request
    var pod corev1.Pod
    json.Unmarshal(req.Object.Raw, &pod)

    var patches []map[string]interface{}

    // Inject default labels if missing
    if pod.Labels == nil {
        patches = append(patches, map[string]interface{}{
            "op":    "add",
            "path":  "/metadata/labels",
            "value": map[string]string{},
        })
    }

    // Add managed-by label
    patches = append(patches, map[string]interface{}{
        "op":    "add",
        "path":  "/metadata/labels/app.kubernetes.io~1managed-by",
        "value": "platform-team",
    })

    // Inject resource defaults if missing
    for i, c := range pod.Spec.Containers {
        if c.Resources.Requests == nil {
            patches = append(patches, map[string]interface{}{
                "op":   "add",
                "path": fmt.Sprintf("/spec/containers/%d/resources/requests", i),
                "value": map[string]string{
                    "cpu":    "100m",
                    "memory": "128Mi",
                },
            })
        }
    }

    patchBytes, _ := json.Marshal(patches)
    patchType := admissionv1.PatchTypeJSONPatch

    response := admissionv1.AdmissionReview{
        TypeMeta: metav1.TypeMeta{APIVersion: "admission.k8s.io/v1", Kind: "AdmissionReview"},
        Response: &admissionv1.AdmissionResponse{
            UID:       req.UID,
            Allowed:   true,
            Patch:     patchBytes,
            PatchType: &patchType,
        },
    }

    respBytes, _ := json.Marshal(response)
    w.Header().Set("Content-Type", "application/json")
    w.Write(respBytes)
}
```

### Webhook Registration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: deployment-validator
  annotations:
    cert-manager.io/inject-ca-from: platform/webhook-cert
webhooks:
- name: validate.deployments.platform.io
  admissionReviewVersions: ["v1"]
  sideEffects: None
  timeoutSeconds: 5
  failurePolicy: Fail             # Fail | Ignore (Ignore = allow if webhook down)
  matchPolicy: Equivalent
  reinvocationPolicy: Never
  clientConfig:
    service:
      name: webhook-server
      namespace: platform
      path: /validate
      port: 443
    # caBundle auto-injected by cert-manager annotation above
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["apps"]
    apiVersions: ["v1"]
    resources: ["deployments"]
    scope: Namespaced
  namespaceSelector:
    matchExpressions:
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system", "platform"]    # skip system namespaces
  objectSelector:
    matchLabels:
      validate: "true"                       # opt-in per resource
---
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-defaulter
webhooks:
- name: mutate.pods.platform.io
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Ignore           # don't block pods if webhook is down
  reinvocationPolicy: IfNeeded    # re-run if other mutating webhooks changed the object
  clientConfig:
    service:
      name: webhook-server
      namespace: platform
      path: /mutate
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
```

### ValidatingAdmissionPolicy (K8s 1.30+ — No Webhook Needed)

```yaml
# CEL-based validation directly in the API server — no external webhook
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-resource-requests
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      resources: ["deployments"]
      operations: ["CREATE", "UPDATE"]
  validations:
  - expression: >
      object.spec.template.spec.containers.all(c,
        has(c.resources) && has(c.resources.requests) &&
        has(c.resources.requests.cpu) && has(c.resources.requests.memory)
      )
    message: "All containers must have CPU and memory requests"
    reason: Invalid
  - expression: >
      object.spec.replicas >= 2 || object.metadata.namespace != 'production'
    message: "Production deployments must have at least 2 replicas"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-resource-requests-binding
spec:
  policyName: require-resource-requests
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchExpressions:
      - key: kubernetes.io/metadata.name
        operator: NotIn
        values: ["kube-system"]
```

---

## 6. eBPF Deep Dive — Cilium Internals

### What is eBPF?

```
eBPF (extended Berkeley Packet Filter): programs that run inside the Linux kernel,
attached to hooks (network, syscalls, tracepoints).

Traditional networking: Packet → netfilter → iptables → kube-proxy rules → pod
eBPF networking:        Packet → eBPF program → pod  (bypasses iptables entirely)

Benefits:
  - O(1) lookup vs O(n) iptables chain traversal
  - No kube-proxy needed (Cilium replaces it)
  - Programmable L3/L4/L7 network policies
  - Kernel-level observability (no sidecar needed for basic metrics)
  - XDP (eXpress Data Path): process packets before they enter the kernel stack
```

### Cilium Architecture

```
┌──────────────────────────────────────────────────┐
│                  Cilium Agent (per node)            │
│                                                    │
│  ┌────────────────┐  ┌────────────────────────┐  │
│  │  Cilium API     │  │  eBPF Map Manager       │  │
│  │  (watches K8s   │  │  (compiles & loads       │  │
│  │   CRDs/Services │  │   eBPF programs)         │  │
│  │   /Endpoints)   │  │                          │  │
│  └────────┬───────┘  └──────────┬─────────────┘  │
│           │                      │                  │
│           └──────────┬───────────┘                  │
│                      ▼                              │
│  ┌──────────────────────────────────────────────┐  │
│  │              Linux Kernel                      │  │
│  │                                                │  │
│  │  TC (Traffic Control) hooks                   │  │
│  │  XDP hooks                                    │  │
│  │  Socket hooks (connect, sendmsg, recvmsg)     │  │
│  │  cgroup hooks                                 │  │
│  │                                                │  │
│  │  eBPF Maps: Service → Backend Pod             │  │
│  │            Identity → Policy Verdict          │  │
│  │            Connection Tracking (CT)            │  │
│  │            NAT table                          │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌────────────────────────────────────────────┐    │
│  │           Hubble (Observability)             │    │
│  │  Reads eBPF events → flow logs, metrics     │    │
│  │  L3/L4/L7 visibility without sidecars       │    │
│  └────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### Cilium — Replacing kube-proxy

```bash
# Install Cilium without kube-proxy
helm install cilium cilium/cilium --version 1.16.0 \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=${API_SERVER_IP} \
  --set k8sServicePort=6443 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set bpf.masquerade=true \
  --set loadBalancer.algorithm=maglev    # consistent hashing for LB

# Verify kube-proxy replacement
cilium status
cilium connectivity test
```

### eBPF-Based Network Policy

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: l7-api-policy
spec:
  endpointSelector:
    matchLabels:
      app: payment-api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: order-service
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: POST
          path: "/api/v1/payments"
          headers:
          - 'X-Request-ID: .*'        # require request ID header
        - method: GET
          path: "/api/v1/payments/[0-9]+"
        # All other HTTP methods/paths → DENIED
  - fromEndpoints:
    - matchLabels:
        app: prometheus
    toPorts:
    - ports:
      - port: "9090"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/metrics"

  egress:
  - toFQDNs:
    - matchName: "stripe.com"              # DNS-based egress policy
    - matchPattern: "*.amazonaws.com"
    toPorts:
    - ports:
      - port: "443"
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: ANY
      rules:
        dns:
        - matchPattern: "*"               # allow DNS resolution
```

### Hubble — eBPF Observability

```bash
# Observe real-time network flows
hubble observe --namespace production --protocol http
hubble observe --from-label app=frontend --to-label app=api
hubble observe --verdict DROPPED   # see blocked traffic

# Flow metrics (Prometheus)
# hubble_flows_processed_total
# hubble_dns_queries_total
# hubble_http_requests_total{method, status, destination}

# Hubble UI: visual service map with L7 flow data
kubectl port-forward -n kube-system svc/hubble-ui 12000:80
```

### Cilium Cluster Mesh (Multi-Cluster)

```bash
# Enable ClusterMesh on both clusters
cilium clustermesh enable --context cluster1
cilium clustermesh enable --context cluster2

# Connect clusters
cilium clustermesh connect --context cluster1 --destination-context cluster2

# Services with same name+namespace are automatically load-balanced across clusters
# Pods can reach services in other clusters via standard DNS
```

### XDP (eXpress Data Path)

```
XDP processes packets at the earliest point in the network stack
(before sk_buff allocation). Used for:
  - DDoS mitigation at line rate
  - Load balancing without DNAT overhead
  - Packet filtering before kernel overhead

Cilium uses XDP for:
  - NodePort acceleration
  - DSR (Direct Server Return) load balancing
  - Prefilter (drop malicious traffic before it reaches pod network)
```

---

## 7. Multi-Cluster Federation

### Federation Options Comparison

```
Tool             Use Case                         Networking    Complexity
─────────────────────────────────────────────────────────────────────────
Cilium ClusterMesh  Cross-cluster service discovery    eBPF tunnel   Medium
Submariner          Pod-to-pod across clusters         IPsec/WG      Medium
Istio Multi-Cluster Multi-cluster service mesh         mTLS          High
KubeFed (CNCF)     Federated API (propagate resources) N/A          High
Liqo                Virtual node (offload pods)        VPN tunnel    Medium
Admiralty            Multi-cluster scheduling           Agent-based   Medium
Skupper              Application-level connectivity     L7 proxy      Low
```

### Cilium ClusterMesh

```yaml
# Global service: load-balanced across clusters
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
  annotations:
    io.cilium/global-service: "true"           # discoverable across clusters
    io.cilium/shared-service: "true"           # share endpoints with remote
    # io.cilium/service-affinity: "local"      # prefer local cluster, fallback remote
spec:
  selector:
    app: api
  ports:
  - port: 80
```

### Submariner

```bash
# Install Submariner broker on a management cluster
subctl deploy-broker --kubeconfig broker.kubeconfig

# Join clusters to the broker
subctl join --kubeconfig cluster1.kubeconfig broker-info.subm \
  --clusterid cluster1 --natt=false

subctl join --kubeconfig cluster2.kubeconfig broker-info.subm \
  --clusterid cluster2 --natt=false

# Export a service for cross-cluster discovery
subctl export service api --namespace production

# Access from other cluster via:
#   api.production.svc.clusterset.local
```

### Istio Multi-Cluster (Primary-Remote)

```yaml
# Cluster 1 (Primary): runs istiod
# Cluster 2 (Remote): connects to Cluster 1's istiod

# On primary cluster
istioctl install --set values.global.meshID=mesh1 \
  --set values.global.multiCluster.clusterName=cluster1 \
  --set values.global.network=network1

# On remote cluster
istioctl install --set values.global.meshID=mesh1 \
  --set values.global.multiCluster.clusterName=cluster2 \
  --set values.global.network=network2 \
  --set values.global.remotePilotAddress=${CLUSTER1_ISTIOD_IP}

# Create cross-cluster secret
istioctl create-remote-secret --context=cluster2 --name=cluster2 | \
  kubectl apply -f - --context=cluster1
```

### KubeFed — Federated Resources

```yaml
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: api
  namespace: production
spec:
  template:
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: api
      template:
        spec:
          containers:
          - name: api
            image: myapp:2.0
  placement:
    clusters:
    - name: us-east
    - name: eu-west
    - name: ap-southeast
  overrides:
  - clusterName: us-east
    clusterOverrides:
    - path: "/spec/replicas"
      value: 5                     # more replicas in primary region
  - clusterName: ap-southeast
    clusterOverrides:
    - path: "/spec/replicas"
      value: 2
```

### Liqo — Virtual Nodes

```bash
# Liqo creates virtual nodes representing remote clusters
# Pods scheduled on virtual nodes run on the remote cluster transparently

kubectl get nodes
# NAME                  STATUS   ROLES
# worker-1              Ready    <none>
# worker-2              Ready    <none>
# liqo-cluster2         Ready    liqo.io/remote    ← virtual node

# Schedule pods to remote cluster via node affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: liqo.io/type
            operator: In
            values: ["virtual-node"]
```

---

## 8. Supply Chain Security

### The Problem

```
Attack vectors:
  1. Compromised base image (malicious layer in Docker Hub image)
  2. Tampered build (CI pipeline injects malicious code)
  3. Registry substitution (image tag points to attacker-controlled image)
  4. Vulnerable dependencies (CVE in OS packages or libraries)

Defense layers:
  Image signing → provenance attestation → vulnerability scanning → admission enforcement
```

### Sigstore / Cosign — Image Signing

```bash
# Generate a key pair (or use keyless with OIDC)
cosign generate-key-pair

# Sign an image after build
cosign sign --key cosign.key myregistry.io/myapp:2.0

# Keyless signing (uses OIDC identity — GitHub Actions, Google, etc.)
cosign sign myregistry.io/myapp:2.0
# Opens browser for OIDC auth, signature stored in Rekor transparency log

# Verify signature
cosign verify --key cosign.pub myregistry.io/myapp:2.0

# Attach SBOM (Software Bill of Materials)
cosign attach sbom --sbom sbom.spdx myregistry.io/myapp:2.0

# Attest build provenance (SLSA)
cosign attest --predicate provenance.json --type slsaprovenance \
  myregistry.io/myapp:2.0
```

### SLSA (Supply-chain Levels for Software Artifacts)

```
Level 0: No guarantees
Level 1: Build process documented (build script exists)
Level 2: Signed provenance (build metadata signed, tamper-evident)
Level 3: Hardened builds (builds run on isolated, ephemeral infrastructure)
Level 4: Two-party review (all changes reviewed before build)

GitHub Actions + SLSA generator:
```

```yaml
# .github/workflows/slsa.yaml
name: SLSA Build
on: push
jobs:
  build:
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.0.0
    with:
      image: myregistry.io/myapp
      digest: ${{ needs.build.outputs.digest }}
    secrets:
      registry-username: ${{ secrets.REGISTRY_USER }}
      registry-password: ${{ secrets.REGISTRY_PASS }}
```

### Kyverno Image Verification Policy

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
  - name: verify-cosign-signature
    match:
      any:
      - resources:
          kinds: ["Pod"]
    verifyImages:
    - imageReferences:
      - "myregistry.io/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
      # Or keyless verification with OIDC identity
      # - keyless:
      #     subject: "https://github.com/myorg/*"
      #     issuer: "https://token.actions.githubusercontent.com"

  - name: verify-sbom-attestation
    match:
      any:
      - resources:
          kinds: ["Pod"]
    verifyImages:
    - imageReferences:
      - "myregistry.io/*"
      attestations:
      - type: https://spdx.dev/Document
        conditions:
        - all:
          - key: "{{ creationInfo.created }}"
            operator: NotEquals
            value: ""
```

### Trivy — Vulnerability Scanning in CI + Admission

```yaml
# Scan in CI pipeline
- name: Scan image
  run: |
    trivy image --exit-code 1 --severity CRITICAL,HIGH \
      --ignore-unfixed myregistry.io/myapp:${{ github.sha }}

# Trivy Operator: continuous scanning inside cluster
# Generates VulnerabilityReport CRDs
apiVersion: aquasecurity.github.io/v1alpha1
kind: VulnerabilityReport
metadata:
  name: pod-api-myapp
status:
  vulnerabilities:
  - vulnerabilityID: CVE-2024-1234
    severity: CRITICAL
    installedVersion: "1.2.3"
    fixedVersion: "1.2.4"
```

### Image Policy — Only Allow Trusted Registries

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: Enforce
  rules:
  - name: validate-registries
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "Images must come from approved registries"
      pattern:
        spec:
          containers:
          - image: "myregistry.io/* | gcr.io/my-project/*"
          initContainers:
          - image: "myregistry.io/* | gcr.io/my-project/*"
  - name: disallow-latest-tag
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "Images must use a specific tag, not :latest"
      pattern:
        spec:
          containers:
          - image: "!*:latest"
```

---

## 9. Pod Security Admission — Advanced Customisation

### Custom Exemptions

```yaml
# Configure PodSecurity admission controller to exempt specific users/namespaces/runtimes
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "restricted"
      enforce-version: "latest"
      audit: "restricted"
      audit-version: "latest"
      warn: "restricted"
      warn-version: "latest"
    exemptions:
      usernames:
      - "system:serviceaccount:kube-system:replicaset-controller"
      runtimeClasses:
      - "kata-containers"        # VM-isolated containers can run privileged
      - "gvisor"
      namespaces:
      - "kube-system"
      - "istio-system"
      - "monitoring"             # Prometheus needs host access
```

### Per-Namespace Override

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    pod-security.kubernetes.io/enforce: baseline       # relaxed for monitoring
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted        # but audit at restricted
    pod-security.kubernetes.io/warn: restricted
```

### Migration Strategy from PodSecurityPolicy

```
1. Enable PSA in warn+audit mode across all namespaces
2. Review audit logs for violations
3. Fix workloads that violate restricted/baseline
4. Switch to enforce mode namespace-by-namespace
5. Remove PSP resources after full migration

Useful command:
  kubectl label --dry-run=server --overwrite ns production \
    pod-security.kubernetes.io/enforce=restricted
  # Shows which pods would be rejected
```

---

## 10. Gateway API — Advanced Routes & Policies

### GRPCRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-route
  namespace: production
spec:
  parentRefs:
  - name: prod-gateway
    namespace: gateway-system
  hostnames: ["grpc.example.com"]
  rules:
  - matches:
    - method:
        service: "myapp.OrderService"
        method: "CreateOrder"
    backendRefs:
    - name: order-service
      port: 9090
  - matches:
    - method:
        service: "myapp.OrderService"
        method: "GetOrder"
    backendRefs:
    - name: order-service-readonly
      port: 9090
```

### TLSRoute (Passthrough)

```yaml
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TLSRoute
metadata:
  name: postgres-tls
  namespace: production
spec:
  parentRefs:
  - name: prod-gateway
    sectionName: postgres-tls
  hostnames: ["db.example.com"]
  rules:
  - backendRefs:
    - name: postgres-primary
      port: 5432
```

### TCPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TCPRoute
metadata:
  name: redis-tcp
  namespace: production
spec:
  parentRefs:
  - name: prod-gateway
    sectionName: redis
  rules:
  - backendRefs:
    - name: redis-master
      port: 6379
```

### BackendTLSPolicy

```yaml
# Configure TLS from gateway to backend (backend mTLS)
apiVersion: gateway.networking.k8s.io/v1alpha3
kind: BackendTLSPolicy
metadata:
  name: api-backend-tls
  namespace: production
spec:
  targetRefs:
  - group: ""
    kind: Service
    name: api
  validation:
    caCertificateRefs:
    - name: api-ca-cert
      group: ""
      kind: ConfigMap
    hostname: api.production.svc.cluster.local
```

### HTTPRoute Advanced Features

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-advanced
  namespace: production
spec:
  parentRefs:
  - name: prod-gateway
  hostnames: ["api.example.com"]
  rules:
  # Request mirroring (shadow traffic for testing)
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1
    backendRefs:
    - name: api-v1
      port: 80
    filters:
    - type: RequestMirror
      requestMirror:
        backendRef:
          name: api-v2-shadow     # receives copy of all requests
          port: 80

  # URL rewrite
  - matches:
    - path:
        type: PathPrefix
        value: /old-api
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /api/v2

  # Request header modification
  - matches:
    - path:
        type: PathPrefix
        value: /api
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
        - name: X-Forwarded-Proto
          value: https
        remove: ["X-Debug-Header"]
    backendRefs:
    - name: api
      port: 80

  # Response header modification
  - matches:
    - path:
        type: PathPrefix
        value: /
    filters:
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        set:
        - name: Strict-Transport-Security
          value: "max-age=31536000; includeSubDomains"
        - name: X-Content-Type-Options
          value: "nosniff"
    backendRefs:
    - name: api
      port: 80
```

---

## 11. Kubernetes Internals — Deep Mechanics

### Watch & Informer Pattern

```
Every K8s controller follows this pattern:

1. List all resources (GET /api/v1/pods)
2. Watch for changes (GET /api/v1/pods?watch=true&resourceVersion=N)
3. On event (ADDED/MODIFIED/DELETED):
   a. Update local cache (Informer store)
   b. Enqueue item in work queue
   c. Worker picks item → calls Reconcile()
   d. Reconcile compares desired state vs actual → makes changes

SharedInformer: single connection to API server shared across controllers
  (avoids N controllers each watching the same resource = N connections)

Informer Cache:
  - In-memory, indexed store of all watched objects
  - Reads served from cache (no API server call)
  - Writes go to API server → watch event updates cache
```

### Garbage Collection & Owner References

```yaml
# When a Deployment is deleted, its ReplicaSets are garbage collected
# Because ReplicaSet has ownerReferences pointing to the Deployment

metadata:
  ownerReferences:
  - apiVersion: apps/v1
    kind: Deployment
    name: api
    uid: d1234-5678-abcd
    controller: true
    blockOwnerDeletion: true

# Propagation policies (on delete):
#   Foreground:  delete children first, then owner (blocking)
#   Background:  delete owner immediately, GC deletes children later (default)
#   Orphan:      delete owner, leave children (they become standalone)

kubectl delete deployment api --cascade=foreground   # wait for all pods to die
kubectl delete deployment api --cascade=orphan        # leave ReplicaSets alive
```

### Resource Versioning & Optimistic Concurrency

```
Every K8s object has:
  metadata.resourceVersion: "12345"

Updates require the current resourceVersion (optimistic locking):
  1. Client reads object (rv=100)
  2. Client modifies object, sends update with rv=100
  3. API server checks: is rv still 100?
     Yes → accept update, set rv=101
     No  → reject with 409 Conflict ("the object has been modified")
  4. Client retries: read again (rv=105), apply changes, send with rv=105

This prevents lost updates in concurrent controllers.
Operators must handle 409 Conflict by re-reading and retrying.
```

### Finalizers — Prevent Deletion Until Cleanup

```yaml
metadata:
  finalizers:
  - myorg.io/cleanup-external-resources

# Deletion flow with finalizers:
# 1. User runs kubectl delete myresource foo
# 2. API server sets metadata.deletionTimestamp (object enters "terminating" state)
# 3. Object is NOT deleted from etcd (finalizer blocks it)
# 4. Controller sees deletionTimestamp is set → runs cleanup logic
#    (delete external LB, remove DNS records, clean S3 bucket, etc.)
# 5. Controller removes the finalizer from the object
# 6. No more finalizers → API server deletes object from etcd

# Stuck finalizer (object won't delete):
kubectl patch myresource foo -p '{"metadata":{"finalizers":null}}' --type=merge
```

### Leader Election

```
Controllers that must run as a single instance use leader election:
  - Write a Lease object to a well-known name
  - Holder renews lease every N seconds
  - If lease expires → another instance takes over

Lease object:
  apiVersion: coordination.k8s.io/v1
  kind: Lease
  metadata:
    name: my-controller-leader
    namespace: my-system
  spec:
    holderIdentity: "pod-abc-123"
    leaseDurationSeconds: 15
    renewTime: "2026-05-07T12:00:00Z"
    acquireTime: "2026-05-07T11:55:00Z"
    leaseTransitions: 3

Used by: kube-controller-manager, kube-scheduler, custom operators
```

### API Server Request Flow (Complete)

```
Client → Load Balancer → API Server
  1. TLS termination
  2. Authentication (X.509 cert, Bearer token, OIDC, Webhook)
  3. Authorization (RBAC, Webhook, Node)
  4. Admission (mutating webhooks → validation → validating webhooks)
  5. etcd read/write (with resourceVersion check)
  6. Response

Aggregated API servers:
  API Server → delegates /apis/metrics.k8s.io → metrics-server
  API Server → delegates /apis/custom.metrics → prometheus-adapter
  Registered via APIService objects
```

---

## 12. FinOps & Advanced Cost Engineering

### Kubecost Deep Configuration

```yaml
# Kubecost cost allocation by team/namespace
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubecost-cost-model
data:
  # Shared cost allocation
  # Distribute cluster overhead (control plane, monitoring) proportionally
  shareTenancyCosts: "true"
  shareNamespaces: "kube-system,monitoring,istio-system"
  
  # Custom pricing (if not auto-detected from cloud billing)
  CPU_COST: "0.031611"        # $/hr per CPU
  RAM_COST: "0.004237"        # $/hr per GB
  GPU_COST: "0.95"            # $/hr per GPU
  STORAGE_COST: "0.00005479"  # $/hr per GB
```

### OpenCost (CNCF — Open Source)

```bash
# OpenCost: vendor-neutral cost monitoring
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set opencost.prometheus.internal.enabled=true

# API queries
curl http://opencost.opencost.svc:9003/allocation/compute?window=7d&aggregate=namespace
curl http://opencost.opencost.svc:9003/allocation/compute?window=24h&aggregate=label:team
```

### Savings Estimation Queries

```bash
# Rightsizing savings (compare requests vs actual usage over 7 days)
# If avg CPU usage is 20% of request → 80% potential savings on CPU request

# Prometheus query: actual vs requested CPU
sum(rate(container_cpu_usage_seconds_total{namespace="production"}[7d])) by (pod)
/
sum(kube_pod_container_resource_requests{resource="cpu",namespace="production"}) by (pod)

# Memory waste
sum(container_memory_working_set_bytes{namespace="production"}) by (pod)
/
sum(kube_pod_container_resource_requests{resource="memory",namespace="production"}) by (pod)
```

### Karpenter Consolidation (Advanced)

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64", "arm64"]     # include Graviton for savings
      nodeClassRef:
        name: default
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s
    # Karpenter will:
    # 1. Find underutilized nodes
    # 2. Attempt to bin-pack pods onto fewer nodes
    # 3. Terminate empty/underused nodes
    # 4. Replace expensive nodes with cheaper ones
    
    budgets:
    - nodes: "10%"        # max 10% of nodes disrupted simultaneously
    - nodes: "0"
      schedule: "0 9 * * 1-5"   # no disruption during business hours
      duration: 8h

  limits:
    cpu: 1000
    memory: 4000Gi
  
  # Expire nodes after 720h to pick up latest AMI / instance pricing
  disruption:
    expireAfter: 720h

---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2023
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-cluster
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 100Gi
      volumeType: gp3
      encrypted: true
```

### FinOps Maturity Model for Kubernetes

```
Level 1 — Crawl:
  - Basic cost visibility (Kubecost/OpenCost installed)
  - Cost per namespace/team reports
  - Identify top cost drivers

Level 2 — Walk:
  - Rightsizing recommendations applied
  - Spot instances for stateless workloads
  - Autoscaling (HPA/VPA/KEDA) enabled
  - Chargeback reports to team leads

Level 3 — Run:
  - Automated rightsizing (VPA in Auto mode for non-critical)
  - Karpenter consolidation with budget constraints
  - Reserved/Savings Plans for baseline
  - Real-time anomaly detection on spend
  - Cost as CI gate (block deploys that exceed budget)
  - Arm64/Graviton for compute savings
  - Cross-AZ traffic optimization
```

---

*Companion to KUBERNETES.md. Covers Kubernetes 1.29–1.32 advanced features.*
*Topics: Scheduler plugins, eBPF/Cilium, multi-cluster, supply chain security, Gateway API advanced routes.*
