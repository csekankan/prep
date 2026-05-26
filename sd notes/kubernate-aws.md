# AWS EKS — Hands-On Tutorial

> From zero to a running production EKS cluster.
> Every AWS service explained, every command runnable.
> Follow top-to-bottom as a tutorial, reference later.

---

## Table of Contents

1. [EKS vs Self-Managed Kubernetes](#1-eks-vs-self-managed)
2. [AWS Services You'll Use with EKS](#2-aws-services-map)
3. [Prerequisites — Tools Setup](#3-prerequisites)
4. [Create Your First EKS Cluster (Console + CLI)](#4-create-your-first-cluster)
5. [Create EKS Cluster with eksctl](#5-eksctl)
6. [Understand Node Groups — Managed, Self-Managed, Fargate](#6-node-groups)
7. [IRSA — IAM Roles for Service Accounts](#7-irsa)
8. [AWS Load Balancer Controller — ALB & NLB](#8-aws-load-balancer-controller)
9. [EBS CSI Driver — Persistent Storage](#9-ebs-csi-driver)
10. [EFS CSI Driver — Shared Storage](#10-efs-csi-driver)
11. [External Secrets Operator — AWS Secrets Manager](#11-external-secrets)
12. [ECR — Container Registry](#12-ecr)
13. [Karpenter — Smart Node Scaling](#13-karpenter)
14. [Cluster Autoscaler — Traditional Node Scaling](#14-cluster-autoscaler)
15. [cert-manager + ACM — TLS Certificates](#15-cert-manager)
16. [ExternalDNS — Automatic Route53 Records](#16-external-dns)
17. [CloudWatch — Logs and Metrics](#17-cloudwatch)
18. [VPC Design for EKS](#18-vpc-design)
19. [EKS Security Best Practices](#19-security)
20. [EKS Cost Optimization](#20-cost)
21. [EKS Upgrades — Step by Step](#21-upgrades)
22. [Terraform — Full EKS Setup](#22-terraform)
23. [Common EKS Gotchas](#23-gotchas)
24. [Full End-to-End Walkthrough](#24-walkthrough)

---

## 1. EKS vs Self-Managed

### What AWS Manages For You

```
┌─────────────────────────────────────────────────────────────┐
│                        EKS                                    │
│                                                              │
│  AWS manages:                      You manage:               │
│  ─────────────                     ────────────              │
│  ✓ Control plane (API server,      ✓ Worker nodes            │
│    etcd, scheduler, controllers)   ✓ Your applications       │
│  ✓ Control plane HA (3 AZs)       ✓ Add-ons (CNI, CSI, etc.)│
│  ✓ etcd backups                    ✓ Networking (VPC, SGs)   │
│  ✓ Kubernetes version upgrades     ✓ IAM roles & policies    │
│  ✓ Security patches                ✓ Monitoring & logging    │
│  ✓ API server scaling              ✓ Cost management         │
│                                                              │
│  Cost: $0.10/hour per cluster = $73/month                   │
│  (plus EC2 instance costs for worker nodes)                  │
└─────────────────────────────────────────────────────────────┘
```

### When to Use EKS

```
Use EKS when:
  ✓ You're on AWS and need Kubernetes
  ✓ You want managed control plane (no etcd headaches)
  ✓ You need AWS integrations (ALB, IAM, Secrets Manager)
  ✓ Team size > 2 engineers

Consider alternatives:
  ECS Fargate:  simpler, no Kubernetes knowledge needed, less flexibility
  EKS Fargate:  serverless Kubernetes (no nodes to manage), higher cost per pod
  EKS Anywhere: on-premises Kubernetes managed by EKS
  kOps:         self-managed Kubernetes on AWS (more control, more work)
```

---

## 2. AWS Services Map

```
Every AWS service and how it plugs into EKS:

┌──────────────────────────────────────────────────────────────┐
│                      NETWORKING                                │
│                                                               │
│  VPC            → cluster lives here                         │
│  Subnets        → private (nodes) + public (load balancers)  │
│  Security Groups→ firewall for nodes and pods                │
│  NAT Gateway    → outbound internet for private nodes        │
│  Route53        → DNS for your apps                          │
│  CloudFront     → CDN in front of your apps                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      COMPUTE                                   │
│                                                               │
│  EC2            → worker nodes (managed node groups)         │
│  Fargate        → serverless pods (no nodes)                 │
│  Graviton       → ARM instances (20-40% cheaper)             │
│  Spot Instances → up to 90% cheaper (interruptible)          │
│  Karpenter      → auto-provisions optimal instances          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      STORAGE                                   │
│                                                               │
│  EBS (gp3/io2)  → block storage (ReadWriteOnce per pod)     │
│  EFS            → file storage (ReadWriteMany shared)        │
│  S3             → object storage (app-level, via IRSA)       │
│  FSx            → high-performance file systems              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      SECURITY & CONFIG                         │
│                                                               │
│  IAM            → who can access what                        │
│  IRSA           → pod-level IAM roles (most important!)      │
│  KMS            → encryption (etcd, EBS, secrets)            │
│  Secrets Manager→ external secret storage                    │
│  ACM            → free TLS certificates                      │
│  WAF            → web application firewall (attach to ALB)   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      DATABASES (managed)                       │
│                                                               │
│  RDS            → PostgreSQL, MySQL (don't run DBs in K8s)   │
│  ElastiCache    → Redis, Memcached                           │
│  DynamoDB       → NoSQL (serverless)                         │
│  MSK            → managed Kafka                              │
│  OpenSearch     → managed Elasticsearch                      │
│  SQS            → message queue (trigger KEDA scaling)       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY                             │
│                                                               │
│  CloudWatch     → logs + metrics + alarms                    │
│  X-Ray          → distributed tracing                        │
│  Prometheus     → metrics (self-hosted or Amazon Managed)    │
│  Grafana        → dashboards (Amazon Managed Grafana)        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      CI/CD                                     │
│                                                               │
│  ECR            → container image registry                   │
│  CodePipeline   → CI/CD (or GitHub Actions, more common)     │
│  ArgoCD         → GitOps (deploy from git, most popular)     │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Prerequisites

### Install Required Tools

```bash
# 1. AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
# Or: brew install awscli

# Configure
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output: json

# Verify
aws sts get-caller-identity

# 2. kubectl
brew install kubectl
# Or: https://kubernetes.io/docs/tasks/tools/

# 3. eksctl (easiest way to create EKS clusters)
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl

# 4. Helm
brew install helm

# 5. Optional but recommended
brew install k9s              # terminal UI
brew install kubectx           # switch clusters/namespaces fast
```

### AWS Permissions You Need

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:*",
        "ec2:*",
        "iam:*",
        "cloudformation:*",
        "autoscaling:*",
        "elasticloadbalancing:*",
        "ecr:*",
        "logs:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 4. Create Your First Cluster

### Option A: AWS Console (Visual, Good for Learning)

```
1. Go to: AWS Console → EKS → Create cluster
2. Fill in:
   Name: my-first-cluster
   Kubernetes version: 1.31
   Cluster service role: (create one — see below)
   
3. Networking:
   VPC: default VPC (for testing) or create new
   Subnets: select at least 2 AZs
   Security group: default (for testing)
   Cluster endpoint: Public and private
   
4. Add-ons:
   ✓ Amazon VPC CNI
   ✓ CoreDNS
   ✓ kube-proxy
   
5. Create → wait 10-15 minutes

6. Add nodes:
   EKS → my-first-cluster → Compute → Add Node Group
   Name: workers
   Instance type: t3.medium (2 vCPU, 4 GB)
   Desired: 2, Min: 2, Max: 4
```

### Create the Cluster Service Role First

```bash
# EKS needs an IAM role to manage resources on your behalf

# Create trust policy
cat > eks-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name myEKSClusterRole \
  --assume-role-policy-document file://eks-trust-policy.json

# Attach required policies
aws iam attach-role-policy \
  --role-name myEKSClusterRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
```

### Option B: AWS CLI

```bash
# Create cluster
aws eks create-cluster \
  --name my-first-cluster \
  --role-arn arn:aws:iam::ACCOUNT:role/myEKSClusterRole \
  --kubernetes-version 1.31 \
  --resources-vpc-config \
    subnetIds=subnet-abc123,subnet-def456,subnet-ghi789,\
    securityGroupIds=sg-12345,\
    endpointPublicAccess=true,\
    endpointPrivateAccess=true

# Wait for cluster (10-15 min)
aws eks wait cluster-active --name my-first-cluster

# Configure kubectl
aws eks update-kubeconfig --name my-first-cluster --region us-east-1

# Verify
kubectl get nodes    # (empty — no nodes yet)
kubectl get svc      # should see kubernetes ClusterIP service
```

---

## 5. eksctl

### The Fastest Way to Create a Cluster

```bash
# Simple cluster (one command, creates VPC + everything)
eksctl create cluster \
  --name my-cluster \
  --version 1.31 \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Takes about 15 minutes
# Creates: VPC, subnets, NAT gateway, EKS cluster, node group

# Verify
kubectl get nodes
# NAME                             STATUS   ROLES    AGE   VERSION
# ip-192-168-1-100.ec2.internal    Ready    <none>   2m    v1.31.0
# ip-192-168-2-200.ec2.internal    Ready    <none>   2m    v1.31.0
# ip-192-168-3-50.ec2.internal     Ready    <none>   2m    v1.31.0
```

### eksctl Config File (Production-Ready)

```yaml
# cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-east-1
  version: "1.31"

# Dedicated VPC
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: HighlyAvailable    # one NAT per AZ (production)

# Availability zones
availabilityZones:
  - us-east-1a
  - us-east-1b
  - us-east-1c

# OIDC provider (required for IRSA)
iam:
  withOIDC: true

# Managed node groups
managedNodeGroups:
  # System workloads (monitoring, ArgoCD, etc.)
  - name: system
    instanceType: m7g.large      # Graviton (ARM) for savings
    desiredCapacity: 2
    minSize: 2
    maxSize: 4
    labels:
      node-role: system
    taints:
    - key: CriticalAddonsOnly
      value: "true"
      effect: NoSchedule
    iam:
      attachPolicyARNs:
        - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
        - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
        - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
    tags:
      Environment: production

  # General workloads
  - name: general
    instanceTypes:
      - m5.xlarge
      - m5.2xlarge
      - m6i.xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 20
    spot: true                   # use Spot for cost savings
    labels:
      node-role: general
      capacity-type: spot
    tags:
      Environment: production

# Add-ons
addons:
  - name: vpc-cni
    version: latest
    configurationValues: |
      env:
        ENABLE_PREFIX_DELEGATION: "true"
        WARM_PREFIX_TARGET: "1"
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# Encryption
secretsEncryption:
  keyARN: arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID

# Logging
cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
      - controllerManager
      - scheduler
```

```bash
# Create from config
eksctl create cluster -f cluster.yaml

# Delete cluster (when done)
eksctl delete cluster -f cluster.yaml
```

---

## 6. Node Groups

### Three Options

```
┌─────────────────────────────────────────────────────────────┐
│  1. MANAGED NODE GROUPS (recommended for most)               │
│                                                              │
│  AWS manages: EC2 instances, AMI updates, health checks      │
│  You manage:  instance type, scaling config, labels          │
│                                                              │
│  Pros:  automatic AMI updates, graceful drains, easy         │
│  Cons:  limited instance type flexibility per group          │
│                                                              │
│  Use for: standard workloads                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2. SELF-MANAGED NODE GROUPS                                  │
│                                                              │
│  You manage: everything (launch templates, AMIs, ASGs)       │
│                                                              │
│  Pros:  full control, custom AMIs, GPU instances             │
│  Cons:  more operational burden                              │
│                                                              │
│  Use for: custom AMIs, Windows nodes, special hardware       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  3. FARGATE (serverless)                                      │
│                                                              │
│  AWS manages: everything (no EC2 instances at all)           │
│                                                              │
│  Pros:  zero node management, pay per pod                    │
│  Cons:  no DaemonSets, no GPU, no hostPort, slower start    │
│         no persistent volumes (EBS), only EFS                │
│         higher cost per vCPU/hour than EC2                    │
│                                                              │
│  Use for: batch jobs, low-traffic services, experimentation  │
└─────────────────────────────────────────────────────────────┘
```

### Fargate Profile

```bash
# Create a Fargate profile (pods matching namespace+labels run on Fargate)
eksctl create fargateprofile \
  --cluster my-cluster \
  --name batch-profile \
  --namespace batch \
  --labels workload-type=batch

# Now any pod in namespace "batch" with label workload-type=batch
# runs serverlessly on Fargate (no EC2 instance needed)
```

### Instance Types Cheat Sheet

```
For EKS, these are the best value instances:

General Purpose:
  m7g.large    2 vCPU, 8 GiB   Graviton3 (ARM)  ~$0.0816/hr   BEST VALUE
  m6i.large    2 vCPU, 8 GiB   Intel             ~$0.096/hr
  m5.large     2 vCPU, 8 GiB   Intel (older)     ~$0.096/hr

Compute Optimized:
  c7g.large    2 vCPU, 4 GiB   Graviton3         ~$0.0725/hr
  c6i.large    2 vCPU, 4 GiB   Intel             ~$0.085/hr

Memory Optimized (databases, caching):
  r7g.large    2 vCPU, 16 GiB  Graviton3         ~$0.1008/hr

GPU (ML inference):
  g5.xlarge    4 vCPU, 16 GiB, 1 A10G GPU        ~$1.006/hr

Tip: Use Graviton (ARM) instances for 20-40% cost savings.
     Your Docker images need to support linux/arm64.
     Multi-arch builds: docker buildx build --platform linux/amd64,linux/arm64
```

---

## 7. IRSA — IAM Roles for Service Accounts

### The Most Important EKS Concept

```
Problem: Your app in Kubernetes needs to access AWS services
         (S3, RDS, Secrets Manager, SQS, etc.)

Bad solutions:
  ✗ Hardcode AWS credentials in env vars (security nightmare)
  ✗ Mount credentials as secrets (manual rotation, shared keys)
  ✗ Use node instance role (ALL pods on the node get ALL permissions)

Good solution: IRSA
  ✓ Each Pod gets its OWN IAM role
  ✓ Least privilege: order-service only accesses order tables
  ✓ No credentials to manage — uses short-lived STS tokens
  ✓ Automatic rotation
  ✓ Works via Kubernetes ServiceAccount + IAM trust policy

How it works:
  1. Pod has a Kubernetes ServiceAccount
  2. ServiceAccount is annotated with an IAM role ARN
  3. AWS SDK in the pod auto-discovers the role
  4. Calls STS AssumeRoleWithWebIdentity
  5. Gets temporary credentials (15 min - 12 hr)
  6. Uses those to call AWS APIs
```

### Step-by-Step Setup

```bash
# Step 1: Enable OIDC provider (one time per cluster)
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# Step 2: Create IAM policy (what the app can do)
cat > s3-read-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ]
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name MyAppS3ReadPolicy \
  --policy-document file://s3-read-policy.json

# Step 3: Create IAM role + K8s ServiceAccount (eksctl does both)
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace production \
  --name my-app-sa \
  --attach-policy-arn arn:aws:iam::ACCOUNT:policy/MyAppS3ReadPolicy \
  --approve

# This creates:
#   1. IAM Role: eksctl-my-cluster-addon-iamserviceaccount-...
#      with trust policy allowing the K8s ServiceAccount to assume it
#   2. K8s ServiceAccount: my-app-sa in namespace production
#      annotated with: eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/...
```

### Use in Your Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
spec:
  template:
    spec:
      serviceAccountName: my-app-sa     # the IRSA-annotated SA
      containers:
      - name: app
        image: myapp:1.0
        # No AWS credentials needed in env vars!
        # The AWS SDK automatically uses IRSA.
        # boto3 (Python), AWS SDK (Go/Java/Node) all support it.
```

### Verify It Works

```bash
# Check the ServiceAccount annotation
kubectl get sa my-app-sa -n production -o yaml
# annotations:
#   eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/...

# Exec into the pod and check
kubectl exec -it deployment/my-app -n production -- bash
env | grep AWS
# AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/...
# AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token

# Test S3 access
python3 -c "import boto3; print(boto3.client('s3').list_buckets())"
```

### Common IRSA Roles You'll Need

```
Service                 Needs IRSA for
─────────────────────── ─────────────────────────────────────
AWS Load Balancer Ctrl  Create/manage ALBs and NLBs
External Secrets        Read from Secrets Manager
cert-manager            Create Route53 DNS records (for ACME)
ExternalDNS             Create Route53 DNS records
EBS CSI Driver          Create/attach EBS volumes
Karpenter               Launch/terminate EC2 instances
Loki                    Write logs to S3
Tempo                   Write traces to S3
Your app                Whatever AWS APIs it needs (S3, SQS, etc.)
```

---

## 8. AWS Load Balancer Controller

### What It Does

```
The AWS Load Balancer Controller watches for:
  Ingress objects       → creates ALBs (Application Load Balancer)
  Service type: LB      → creates NLBs (Network Load Balancer)

Without it: K8s creates Classic Load Balancers (old, limited)
With it:    You get modern ALB/NLB with full AWS features
```

### Install

```bash
# Create IRSA
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::ACCOUNT:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install via Helm
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### ALB Ingress (HTTP/HTTPS)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: production
  annotations:
    # Use ALB (not nginx)
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip        # route directly to Pod IPs

    # TLS with ACM certificate
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"

    # Health check
    alb.ingress.kubernetes.io/healthcheck-path: /healthz/ready
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"

    # WAF (optional)
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:...

    # Group multiple Ingresses into one ALB (cost savings)
    alb.ingress.kubernetes.io/group.name: my-app
    alb.ingress.kubernetes.io/group.order: "10"
spec:
  ingressClassName: alb
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

### NLB Service (TCP/gRPC)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-grpc-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: external
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: my-grpc-service
  ports:
  - port: 443
    targetPort: 9090
    protocol: TCP
```

### ALB vs NLB

```
ALB (Application Load Balancer):
  Layer 7 (HTTP/HTTPS)
  URL-based routing, host-based routing
  WebSocket support
  WAF integration
  Slow (7-10s to register new targets)
  Use for: web apps, REST APIs

NLB (Network Load Balancer):
  Layer 4 (TCP/UDP)
  Ultra-low latency
  Static IP / Elastic IP support
  Fast (instant target registration)
  Millions of requests/sec
  Use for: gRPC, databases, high-throughput
```

---

## 9. EBS CSI Driver

### Persistent Block Storage for Pods

```bash
# Usually installed as an EKS add-on (done in eksctl config above)
# If not, install manually:

eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace kube-system \
  --name ebs-csi-controller-sa \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::ACCOUNT:role/...
```

### StorageClass + PVC

```yaml
# StorageClass (usually create once)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer   # provision in same AZ as Pod
allowVolumeExpansion: true
---
# PVC (per application)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce            # EBS = one node at a time
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi
```

```
EBS limitations:
  - ReadWriteOnce only (one node at a time)
  - Cannot be shared between pods on different nodes
  - AZ-locked (volume in us-east-1a can only attach to nodes in 1a)
  - WaitForFirstConsumer solves this (provisions in same AZ as pod)

For shared storage across pods/nodes → use EFS (Section 10)
```

---

## 10. EFS CSI Driver

### Shared File Storage (ReadWriteMany)

```bash
# Install EFS CSI driver
helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver/
helm install aws-efs-csi-driver aws-efs-csi-driver/aws-efs-csi-driver \
  -n kube-system
```

```yaml
# StorageClass for EFS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap         # EFS Access Points
  fileSystemId: fs-12345abcde      # your EFS filesystem ID
  directoryPerms: "700"
---
# PVC — can be mounted by MANY pods simultaneously
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
  - ReadWriteMany                  # shared across pods + nodes
  storageClassName: efs
  resources:
    requests:
      storage: 50Gi
```

```
EBS vs EFS:
  EBS:  fast, block storage, one pod at a time, AZ-locked
  EFS:  slower, file storage, many pods, multi-AZ, auto-scaling
  
  Use EBS for: databases, single-pod apps
  Use EFS for: shared config, ML model files, CMS uploads
```

---

## 11. External Secrets

### Sync AWS Secrets Manager → K8s Secrets

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace

# Create IRSA for it
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace external-secrets \
  --name external-secrets \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve
```

```yaml
# ClusterSecretStore (one per cluster)
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
---
# ExternalSecret (per secret you need)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets
    kind: ClusterSecretStore
  target:
    name: db-credentials    # K8s Secret that gets created
  data:
  - secretKey: password
    remoteRef:
      key: production/database/credentials
      property: password
  - secretKey: host
    remoteRef:
      key: production/database/credentials
      property: host
```

```bash
# Verify
kubectl get externalsecret -n production
# NAME       STORE         REFRESH   STATUS
# db-creds   aws-secrets   1h        SecretSynced

kubectl get secret db-credentials -n production
# NAME              TYPE     DATA   AGE
# db-credentials    Opaque   2      5s
```

---

## 12. ECR — Container Registry

```bash
# Create a repository
aws ecr create-repository --repository-name my-app

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build, tag, push
docker build -t my-app:v1.0 .
docker tag my-app:v1.0 ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0

# Use in Kubernetes (EKS nodes can pull from ECR automatically via instance role)
image: ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0

# Image scanning (find CVEs)
aws ecr start-image-scan \
  --repository-name my-app \
  --image-id imageTag=v1.0

# Lifecycle policy (auto-delete old images)
aws ecr put-lifecycle-policy \
  --repository-name my-app \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": { "type": "expire" }
    }]
  }'
```

---

## 13. Karpenter

### Why Karpenter > Cluster Autoscaler

```
Cluster Autoscaler:
  - Works with predefined ASGs (fixed instance types)
  - Slow: 2-5 minutes to add a node
  - Can't mix instance types within a group
  
Karpenter:
  - No ASGs — calls EC2 Fleet API directly
  - Fast: 30-90 seconds to add a node
  - Picks the CHEAPEST instance type that fits
  - Mixes Spot + On-Demand, x86 + ARM automatically
  - Consolidates underused nodes (bin-packing)
```

### Install Karpenter

```bash
# Karpenter needs its own IAM setup (complex — use Terraform or eksctl)
# Simplified version:

helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version 1.0.0 \
  --namespace karpenter --create-namespace \
  --set settings.clusterName=my-cluster \
  --set settings.clusterEndpoint=$(aws eks describe-cluster --name my-cluster --query "cluster.endpoint" --output text) \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::ACCOUNT:role/KarpenterControllerRole
```

### NodePool + EC2NodeClass

```yaml
# What kinds of nodes to create
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: general
spec:
  template:
    spec:
      requirements:
      # Mix Spot + On-Demand (Spot preferred for cost)
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      # Allow both x86 and ARM (Graviton)
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64", "arm64"]
      # Instance families
      - key: karpenter.k8s.aws/instance-category
        operator: In
        values: ["m", "c", "r"]
      # Minimum generation
      - key: karpenter.k8s.aws/instance-generation
        operator: Gt
        values: ["5"]
      nodeClassRef:
        name: default
  limits:
    cpu: 500         # max 500 vCPUs total
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 60s
---
# EC2 configuration
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2023
  role: "KarpenterNodeRole"
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
  metadataOptions:
    httpTokens: required     # IMDSv2 only (security)
```

```
How Karpenter works:
  1. You deploy a Pod → scheduler can't place it (no room)
  2. Karpenter sees: "Unschedulable Pod needs 2 CPU, 4Gi, linux/arm64"
  3. Karpenter: "Cheapest instance: m7g.medium (Spot, $0.016/hr)"
  4. Calls EC2 Fleet API → launches instance in 30s
  5. Node joins cluster → scheduler places Pod

Consolidation:
  1. Karpenter continuously monitors node utilization
  2. Node A: 15% utilized, Node B: 20% utilized
  3. Karpenter: "I can fit all pods from A onto B"
  4. Cordons Node A → drains Pods → terminates EC2 instance
  5. Saves money automatically
```

---

## 14. Cluster Autoscaler

### Traditional Approach (If Not Using Karpenter)

```bash
# Install Cluster Autoscaler
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=my-cluster \
  --set awsRegion=us-east-1 \
  --set rbac.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::ACCOUNT:role/ClusterAutoscalerRole
```

---

## 15. cert-manager + ACM

### Option A: ACM (Zero Config, AWS-Only)

```
ACM (AWS Certificate Manager) provides FREE TLS certificates.
Automatically renewed. Works with ALB and NLB.

Just reference the ACM ARN in your Ingress annotation:
  alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...

No cert-manager needed for ALB/NLB!
```

### Option B: cert-manager (For In-Cluster TLS)

```bash
# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  -n cert-manager --create-namespace \
  --set installCRDs=true

# Create IRSA for Route53 access (DNS-01 challenge)
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace cert-manager \
  --name cert-manager \
  --attach-policy-arn arn:aws:iam::ACCOUNT:policy/CertManagerRoute53Policy \
  --approve
```

```yaml
# ClusterIssuer with Route53 DNS-01
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: platform@mycompany.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        route53:
          region: us-east-1
          hostedZoneID: Z1234567890
```

---

## 16. ExternalDNS

### Auto-Create Route53 Records from Ingress/Service

```bash
# Install ExternalDNS
helm install external-dns bitnami/external-dns \
  -n external-dns --create-namespace \
  --set provider=aws \
  --set aws.region=us-east-1 \
  --set domainFilters[0]=myapp.com \
  --set policy=sync \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::ACCOUNT:role/ExternalDNSRole
```

```
Now when you create:
  Ingress with host: api.myapp.com
  
ExternalDNS automatically:
  Creates Route53 A record: api.myapp.com → ALB DNS name
  
When you delete the Ingress:
  Deletes the Route53 record

No manual DNS management!
```

---

## 17. CloudWatch

### EKS Control Plane Logs

```bash
# Enable control plane logging
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# View in CloudWatch:
# Log group: /aws/eks/my-cluster/cluster
```

### Container Insights (Node + Pod Metrics)

```bash
# Install CloudWatch agent as DaemonSet
# Sends node/pod/container metrics to CloudWatch

FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonSet/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | \
  sed "s/{{cluster_name}}/my-cluster/;s/{{region_name}}/us-east-1/;s/{{http_server_toggle}}/On/;s/{{http_server_port}}/$FluentBitHttpPort/;s/{{read_from_head}}/$FluentBitReadFromHead/" | \
  kubectl apply -f -

# View in CloudWatch:
# Namespace: ContainerInsights
# Metrics: pod_cpu_utilization, pod_memory_utilization, node_cpu_utilization
```

### ADOT — AWS Distro for OpenTelemetry

```bash
# Better alternative: ADOT collector for metrics + traces
aws eks create-addon --cluster-name my-cluster --addon-name adot

# Sends to: CloudWatch, X-Ray, Prometheus (AMP), or any OTLP endpoint
```

---

## 18. VPC Design

```
Best practice VPC for EKS:

┌─────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16 (65,536 IPs)                              │
│                                                              │
│  ┌─── AZ: us-east-1a ──┐  ┌─── AZ: us-east-1b ──┐         │
│  │                      │  │                      │         │
│  │ Public: 10.0.0.0/20  │  │ Public: 10.0.16.0/20│         │
│  │ (4,096 IPs)          │  │ (4,096 IPs)         │         │
│  │ ALB, NAT Gateway     │  │ ALB, NAT Gateway    │         │
│  │                      │  │                      │         │
│  │ Private: 10.0.32.0/19│  │ Private: 10.0.64.0/19        │
│  │ (8,192 IPs)          │  │ (8,192 IPs)         │         │
│  │ EKS nodes + pods     │  │ EKS nodes + pods    │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  ┌─── AZ: us-east-1c ──┐                                   │
│  │                      │                                   │
│  │ Public: 10.0.96.0/20 │                                   │
│  │ Private: 10.0.128.0/19                                   │
│  └──────────────────────┘                                   │
│                                                              │
│  Why /19 for private subnets?                               │
│  VPC CNI: each pod gets a real VPC IP                       │
│  100 nodes × 50 pods = 5,000 IPs needed                    │
│  /19 = 8,192 IPs per AZ → plenty of room                   │
│  With prefix delegation: 16x more IPs → almost unlimited    │
└─────────────────────────────────────────────────────────────┘

Required subnet tags:
  Public subnets:
    kubernetes.io/role/elb = 1
  Private subnets:
    kubernetes.io/role/internal-elb = 1
    karpenter.sh/discovery = my-cluster
```

---

## 19. Security Best Practices

```
1. IRSA everywhere (never use node instance role for apps)
2. Private API endpoint (disable public if possible)
3. KMS encryption for etcd secrets
4. IMDSv2 only (httpTokens: required) — prevents SSRF attacks
5. Pod Security Standards: restricted mode on all namespaces
6. Network Policies: default-deny, explicit allow
7. ECR image scanning: block deploys with CRITICAL CVEs
8. Control plane logging: enable audit logs
9. RBAC: no cluster-admin for developers
10. Secrets: use External Secrets, not kubectl create secret
11. Multi-AZ: spread across 3 AZs minimum
12. Security groups: restrict node-to-node and pod traffic
```

---

## 20. Cost Optimization

```
1. Graviton instances: 20-40% cheaper for same performance
   Use m7g instead of m5/m6i

2. Spot instances: 60-90% cheaper
   Use for stateless services (NOT databases)
   Diversify instance types to avoid interruption

3. Karpenter consolidation: auto-terminates underused nodes
   consolidationPolicy: WhenUnderutilized

4. Right-size pods: set accurate resource requests
   Use VPA in recommendation mode → read suggestions → apply

5. Scale to zero: use KEDA for event-driven workloads
   No traffic? 0 pods. No cost.

6. EBS: use gp3 (cheaper than gp2 with better performance)
   Delete unused PVCs

7. NAT Gateway: $0.045/hr + $0.045/GB
   Use VPC endpoints for S3, ECR, STS (avoid NAT costs)

8. ALB: share one ALB across services (IngressGroup)
   Each ALB costs ~$22/month + traffic

9. Reserved Instances or Savings Plans for baseline compute
   3-year commitment = up to 60% savings

10. Fargate for bursty/batch: no idle node cost
    But higher per-vCPU cost for sustained workloads
```

---

## 21. Upgrades

### EKS Upgrade Process

```bash
# Check current version
kubectl version --short

# Check available updates
aws eks describe-cluster --name my-cluster \
  --query "cluster.version"

# Step 1: Update control plane (AWS manages this)
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-version 1.32

# Wait for update (15-30 minutes)
aws eks wait cluster-active --name my-cluster

# Step 2: Update add-ons
aws eks update-addon --cluster-name my-cluster \
  --addon-name vpc-cni --resolve-conflicts OVERWRITE

aws eks update-addon --cluster-name my-cluster \
  --addon-name coredns --resolve-conflicts OVERWRITE

aws eks update-addon --cluster-name my-cluster \
  --addon-name kube-proxy --resolve-conflicts OVERWRITE

# Step 3: Update node groups
# Option A: Rolling update (in-place)
aws eks update-nodegroup-version \
  --cluster-name my-cluster \
  --nodegroup-name workers

# Option B: Blue-green (create new group, drain old)
eksctl create nodegroup -f cluster.yaml --include='workers-v132'
eksctl delete nodegroup -f cluster.yaml --include='workers-v131'

# Step 4: Verify
kubectl get nodes
kubectl get pods --all-namespaces
```

---

## 22. Terraform

### Minimal Production EKS

```hcl
# main.tf
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
}

provider "aws" { region = "us-east-1" }

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.32.0/19", "10.0.64.0/19", "10.0.96.0/19"]
  public_subnets  = ["10.0.0.0/20", "10.0.16.0/20", "10.0.128.0/20"]

  enable_nat_gateway = true
  single_nat_gateway = false
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "my-cluster"
  cluster_version = "1.31"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      instance_types = ["m7g.large"]
      ami_type       = "AL2023_ARM_64_STANDARD"
      capacity_type  = "SPOT"
      min_size       = 3
      max_size       = 20
      desired_size   = 3
    }
  }
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --name my-cluster --region us-east-1"
}
```

```bash
terraform init
terraform plan
terraform apply
# Follow the output to configure kubectl
```

---

## 23. Common Gotchas

```
1. "Pods stuck in Pending — no IP addresses"
   VPC CNI ran out of IPs. Enable prefix delegation:
   ENABLE_PREFIX_DELEGATION=true on VPC CNI add-on

2. "Can't pull from ECR"
   Node IAM role needs AmazonEC2ContainerRegistryReadOnly policy

3. "ALB not created from Ingress"
   AWS Load Balancer Controller not installed, or IRSA missing
   Check: kubectl logs -n kube-system deployment/aws-load-balancer-controller

4. "PVC stuck in Pending"
   EBS CSI driver not installed, or missing IRSA
   EBS is AZ-locked: use WaitForFirstConsumer storage class

5. "Pod can't reach the internet"
   Private subnet without NAT Gateway? Check route tables
   Security Group blocking outbound? Check node SG rules

6. "IRSA not working — AccessDenied"
   Check: is the OIDC provider associated?
   Check: does the ServiceAccount annotation match the IAM role?
   Check: trust policy on IAM role allows the service account?

7. "Karpenter not scaling up"
   Check: SecurityGroup and Subnet tags match karpenter.sh/discovery
   Check: Instance profile / role has correct permissions

8. "kubectl timeout after cluster create"
   If private endpoint only: need VPN or bastion to reach API
   Run: aws eks update-kubeconfig --name cluster --region region

9. "Node NotReady after upgrade"
   kubelet version must be within 2 minor versions of API server
   Upgrade nodes after control plane

10. "Cross-AZ data transfer costs too high"
    Use topology-aware routing:
    service.spec.internalTrafficPolicy: Local
    service.spec.trafficDistribution: PreferClose
```

---

## 24. Full End-to-End Walkthrough

### Deploy a Real App on EKS in 15 Minutes

```bash
# 1. Create cluster (15 min)
eksctl create cluster \
  --name demo \
  --version 1.31 \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 2 \
  --managed

# 2. Verify
kubectl get nodes

# 3. Create namespace
kubectl create namespace demo

# 4. Deploy nginx
kubectl create deployment web --image=nginx:1.25 --replicas=3 -n demo

# 5. Expose it
kubectl expose deployment web --port=80 --target-port=80 --type=LoadBalancer -n demo

# 6. Get the URL (wait 2 minutes for NLB)
kubectl get svc web -n demo
# NAME   TYPE           CLUSTER-IP    EXTERNAL-IP                          PORT(S)
# web    LoadBalancer   10.100.5.23   a1b2c3-1234.us-east-1.elb.amazonaws.com   80:31234/TCP

# 7. Open in browser
curl a1b2c3-1234.us-east-1.elb.amazonaws.com
# <!DOCTYPE html> <html> <head><title>Welcome to nginx!</title>...

# 8. Scale it
kubectl scale deployment web --replicas=5 -n demo

# 9. Update it
kubectl set image deployment/web nginx=nginx:1.26 -n demo
kubectl rollout status deployment/web -n demo

# 10. Clean up
kubectl delete namespace demo
eksctl delete cluster --name demo
```

### Production Deploy (with ALB + TLS)

```bash
# 1. Install AWS LB Controller (see Section 8)

# 2. Create ACM certificate
aws acm request-certificate \
  --domain-name "*.myapp.com" \
  --validation-method DNS

# 3. Validate (add DNS record AWS gives you to Route53)

# 4. Deploy your app with ALB Ingress
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/api:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  namespace: production
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  ingressClassName: alb
  rules:
  - host: api.myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF

# 5. Point DNS to ALB
# In Route53: api.myapp.com → ALIAS → ALB DNS name

# 6. Test
curl https://api.myapp.com/healthz
```

---

*This is the AWS EKS companion to the Kubernetes docs.*
*Read KUBERNETES_BEGINNER.md first, then this, then tackle the 03-aws-eks-production project.*
