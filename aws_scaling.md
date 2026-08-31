# Horizontal Scaling: Handling Millions of Requests Per Second

> A practical, AWS-focused guide to multi-location, multi-region, auto-scaling,
> and manual scaling strategies for extreme throughput.

---

## Table of Contents

1. [The Core Problem](#1-the-core-problem)
2. [Vertical vs Horizontal Scaling](#2-vertical-vs-horizontal-scaling)
3. [Multi-Location Architecture](#3-multi-location-architecture)
4. [Multi-Region Architecture](#4-multi-region-architecture)
5. [Auto-Scaling Deep Dive](#5-auto-scaling-deep-dive)
6. [Manual Scaling Playbook](#6-manual-scaling-playbook)
7. [Real AWS Configuration Examples](#7-real-aws-configuration-examples)
8. [Data Layer Scaling](#8-data-layer-scaling)
9. [Caching at Every Layer](#9-caching-at-every-layer)
10. [Load Balancing Strategies](#10-load-balancing-strategies)
11. [Real-World Architecture: 1M RPS System](#11-real-world-architecture-1m-rps-system)
12. [Cost Optimization](#12-cost-optimization)
13. [Monitoring and Observability](#13-monitoring-and-observability)
14. [Common Pitfalls](#14-common-pitfalls)
15. [Checklist: Are You Ready for 1M RPS?](#15-checklist-are-you-ready-for-1m-rps)

---

## 1. The Core Problem

When a single server handles ~1,000-10,000 requests per second (depending on workload),
reaching **1,000,000 RPS** means you need **100-1000 servers** working in concert.

But it's not just about adding servers. You need to solve:

- **Traffic distribution** — How do requests reach the right server?
- **State management** — Where does shared state live?
- **Data consistency** — How do 1000 servers agree on truth?
- **Failure isolation** — One region dies, does everything die?
- **Latency** — Users in Tokyo shouldn't wait for a server in Virginia.
- **Cost** — Running 1000 servers 24/7 is expensive if traffic peaks for 2 hours.

---

## 2. Vertical vs Horizontal Scaling

```
Vertical Scaling (Scale Up)          Horizontal Scaling (Scale Out)
┌─────────────────────┐              ┌──────┐ ┌──────┐ ┌──────┐
│                     │              │Server│ │Server│ │Server│
│   BIGGER SERVER     │              │  1   │ │  2   │ │  3   │
│   128 CPU / 512GB   │              └──────┘ └──────┘ └──────┘
│                     │              ┌──────┐ ┌──────┐ ┌──────┐
│   Single point of   │              │Server│ │Server│ │Server│
│   failure           │              │  4   │ │  5   │ │  6   │
└─────────────────────┘              └──────┘ └──────┘ └──────┘

Max: ~10K RPS                        Max: Unlimited (add more boxes)
Cost: Exponential                    Cost: Linear
Failure: Catastrophic                Failure: Graceful degradation
```

**Why horizontal wins at scale:**

| Factor          | Vertical              | Horizontal                  |
|-----------------|-----------------------|-----------------------------|
| Upper limit     | Hardware ceiling      | No theoretical limit        |
| Cost curve      | Exponential           | Linear                      |
| Availability    | Single point failure  | N-1 tolerance               |
| Deployment      | Downtime required     | Rolling updates              |
| Geo-distribution| Impossible            | Native                      |

---

## 3. Multi-Location Architecture

### What "Multi-Location" Means

Multiple **Availability Zones (AZs)** within the **same region**. Each AZ is a
physically separate data center with independent power, cooling, and networking,
connected via low-latency links (~1-2ms).

### Why You Need It

A single AZ can go down (fire, power outage, network cut). Multi-AZ gives you
**high availability** within a region.

### Architecture Pattern

```
                    Region: us-east-1
    ┌─────────────────────────────────────────┐
    │                                         │
    │    ┌─── AZ-1a ───┐  ┌─── AZ-1b ───┐   │
    │    │  App × 10    │  │  App × 10    │   │
    │    │  Cache Node  │  │  Cache Node  │   │
    │    │  DB Primary  │  │  DB Replica  │   │
    │    └──────────────┘  └──────────────┘   │
    │                                         │
    │    ┌─── AZ-1c ───┐                      │
    │    │  App × 10    │                      │
    │    │  Cache Node  │                      │
    │    │  DB Replica  │                      │
    │    └──────────────┘                      │
    │                                         │
    │    ┌─────────────────────────┐           │
    │    │  ALB (Application Load  │           │
    │    │  Balancer) — spans all  │           │
    │    │  3 AZs automatically    │           │
    │    └─────────────────────────┘           │
    └─────────────────────────────────────────┘
```

### Real AWS Setup: Multi-AZ ECS Service

```json
// ECS Service definition (Terraform)
resource "aws_ecs_service" "api" {
  name            = "api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 30  // 10 per AZ

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 70
    base              = 10  // guaranteed minimum
  }
  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 30  // save money on burst capacity
  }

  network_configuration {
    subnets = [
      aws_subnet.private_az1a.id,  // us-east-1a
      aws_subnet.private_az1b.id,  // us-east-1b
      aws_subnet.private_az1c.id,  // us-east-1c
    ]
    security_groups = [aws_security_group.api.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }
}
```

### Key Design Decisions

- **Spread across 3 AZs minimum** — survives loss of any single AZ
- **Equal capacity per AZ** — if one AZ dies, remaining two handle 100% load
- **This means you run at ~66% capacity normally** — the "cost of availability"
- **Cross-AZ data transfer costs $0.01/GB** — minimize chatty cross-AZ calls

---

## 4. Multi-Region Architecture

### What "Multi-Region" Means

Deploying your application across **geographically separate AWS regions**
(e.g., us-east-1, eu-west-1, ap-southeast-1). Regions are hundreds/thousands
of miles apart with 50-200ms latency between them.

### Why You Need It

1. **Latency** — Serve users from the nearest region (50ms vs 300ms)
2. **Disaster recovery** — Entire region can fail (rare but catastrophic)
3. **Compliance** — GDPR requires EU data to stay in EU
4. **Blast radius** — Limit the impact of bad deployments

### Architecture Patterns

#### Pattern 1: Active-Passive (Pilot Light)

One region handles all traffic. The other region has minimal infrastructure
running, ready to scale up if the primary fails.

```
             Normal Traffic Flow
                    │
                    ▼
        ┌───────────────────┐
        │   us-east-1       │
        │   (ACTIVE)        │
        │   100 instances   │
        │   Primary DB      │
        └───────────────────┘
                    │
              Async replication
                    │
                    ▼
        ┌───────────────────┐
        │   eu-west-1       │
        │   (PASSIVE)       │
        │   2 instances     │    ← Pilot light: minimal, ready to scale
        │   Read replica    │
        └───────────────────┘

RTO: 15-30 minutes  |  RPO: seconds to minutes
Cost: ~110% of single region
```

#### Pattern 2: Active-Active (Multi-Master)

Both regions handle traffic simultaneously. This is what you need for 1M RPS.

```
        Users in Americas          Users in Europe/Africa
              │                           │
              ▼                           ▼
    ┌──── Route 53 (Latency-Based Routing) ────┐
    │                                           │
    ▼                                           ▼
┌─────────────────┐                 ┌─────────────────┐
│   us-east-1     │                 │   eu-west-1     │
│   (ACTIVE)      │◄──────────────►│   (ACTIVE)      │
│   200 instances │  Bi-directional │   200 instances │
│   DynamoDB      │  replication    │   DynamoDB      │
│   Global Table  │                 │   Global Table  │
└─────────────────┘                 └─────────────────┘
         │                                   │
    Users in Asia                            │
         │                                   │
         ▼                                   │
┌─────────────────┐                          │
│ ap-southeast-1  │◄─────────────────────────┘
│   (ACTIVE)      │
│   150 instances  │
│   DynamoDB      │
│   Global Table  │
└─────────────────┘

RTO: ~0 (automatic)  |  RPO: ~0 (eventual consistency)
Cost: ~300% of single region (but you need it anyway for the capacity)
```

### Real AWS Config: Route 53 Latency Routing

```json
// Terraform — Route 53 latency-based routing
resource "aws_route53_record" "api_us" {
  zone_id        = aws_route53_zone.main.zone_id
  name           = "api.myservice.com"
  type           = "A"
  set_identifier = "us-east-1"

  alias {
    name                   = aws_lb.api_us.dns_name
    zone_id                = aws_lb.api_us.zone_id
    evaluate_target_health = true  // critical: skip unhealthy regions
  }

  latency_routing_policy {
    region = "us-east-1"
  }
}

resource "aws_route53_record" "api_eu" {
  zone_id        = aws_route53_zone.main.zone_id
  name           = "api.myservice.com"
  type           = "A"
  set_identifier = "eu-west-1"

  alias {
    name                   = aws_lb.api_eu.dns_name
    zone_id                = aws_lb.api_eu.zone_id
    evaluate_target_health = true
  }

  latency_routing_policy {
    region = "eu-west-1"
  }
}

// Health check — Route 53 won't send traffic to dead regions
resource "aws_route53_health_check" "api_us" {
  fqdn              = aws_lb.api_us.dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 10  // check every 10 seconds

  regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
}
```

### Multi-Region Data Strategy

This is the **hardest part**. Options:

| Strategy | Consistency | Latency | Complexity | Use Case |
|----------|------------|---------|------------|----------|
| DynamoDB Global Tables | Eventual (~1s) | Low | Low | User profiles, sessions |
| Aurora Global Database | Eventual (read), Strong (write to primary) | Medium | Medium | Transactional data |
| CockroachDB / Spanner | Strong | Higher | High | Financial transactions |
| Event Sourcing + CQRS | Eventual | Low | Very High | Event-driven systems |
| Region-local + async sync | Eventual | Lowest | Medium | Region-specific data |

### DynamoDB Global Table Setup

```json
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"  // auto-scales, no capacity planning
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  // Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  // Enable streams for global replication
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  // Replicate to other regions
  replica {
    region_name = "eu-west-1"
  }
  replica {
    region_name = "ap-southeast-1"
  }
}
```

---

## 5. Auto-Scaling Deep Dive

### Theory: What Auto-Scaling Solves

```
Traffic Pattern (typical):

RPS
1M ─           ┌──────┐
    │          │      │
    │         │        │
    │        │          │
500K─       │            │
    │      │              │
    │     │                │
    │    │                  │          ┌───┐
100K────┘                    └────────┘   └───
    └──────────────────────────────────────────
    00:00  06:00  12:00  18:00  00:00  06:00

Without auto-scaling: Run 1000 servers 24/7 → $$$$$
With auto-scaling:    Run 100-1000 servers as needed → $$
```

### AWS Auto Scaling Mechanisms

#### 5.1 EC2 Auto Scaling Groups (ASG)

The classic approach for EC2-based workloads.

```json
resource "aws_autoscaling_group" "api" {
  name                = "api-asg"
  vpc_zone_identifier = [
    aws_subnet.private_1a.id,
    aws_subnet.private_1b.id,
    aws_subnet.private_1c.id,
  ]

  min_size         = 30   // never go below this (handles base load)
  max_size         = 500  // hard ceiling
  desired_capacity = 50   // starting point

  // Use mixed instances for cost savings
  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 30   // guaranteed
      on_demand_percentage_above_base_capacity = 20   // 20% on-demand, 80% spot
      spot_allocation_strategy                 = "capacity-optimized"
    }
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.api.id
        version            = "$Latest"
      }
      override {
        instance_type = "c6i.2xlarge"   // primary
      }
      override {
        instance_type = "c6a.2xlarge"   // fallback
      }
      override {
        instance_type = "c5.2xlarge"    // fallback
      }
    }
  }

  // Warm pool: pre-initialized instances ready to go
  warm_pool {
    pool_state                  = "Stopped"
    min_size                    = 20
    max_group_prepared_capacity = 100
  }

  health_check_type         = "ELB"
  health_check_grace_period = 120

  // Instance refresh for zero-downtime deploys
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 80
    }
  }

  tag {
    key                 = "Service"
    value               = "api"
    propagate_at_launch = true
  }
}
```

#### 5.2 Target Tracking Scaling (Recommended Default)

"Keep CPU at 60%" — AWS figures out how many instances are needed.

```json
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 60.0

    // How fast to scale
    // Scale out fast, scale in slow (avoid flapping)
  }
}

// Also track request count per target
resource "aws_autoscaling_policy" "request_count" {
  name                   = "request-count-tracking"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.api.arn_suffix}/${aws_lb_target_group.api.arn_suffix}"
    }
    target_value = 1000.0  // 1000 RPS per instance
  }
}
```

#### 5.3 Step Scaling (Fine-Grained Control)

Define exact scaling actions for specific thresholds.

```json
resource "aws_autoscaling_policy" "step_scale_out" {
  name                   = "step-scale-out"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type            = "StepScaling"
  adjustment_type        = "PercentChangeInCapacity"

  step_adjustment {
    // CPU 60-70%: add 20% more instances
    scaling_adjustment          = 20
    metric_interval_lower_bound = 0
    metric_interval_upper_bound = 10
  }
  step_adjustment {
    // CPU 70-85%: add 50% more instances
    scaling_adjustment          = 50
    metric_interval_lower_bound = 10
    metric_interval_upper_bound = 25
  }
  step_adjustment {
    // CPU > 85%: add 100% more instances (DOUBLE)
    scaling_adjustment          = 100
    metric_interval_lower_bound = 25
  }
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "api-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2       // 2 consecutive periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60      // 1-minute periods
  statistic           = "Average"
  threshold           = 60
  alarm_actions       = [aws_autoscaling_policy.step_scale_out.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.api.name
  }
}
```

#### 5.4 Predictive Scaling (ML-Based)

AWS analyzes your traffic patterns and pre-scales **before** the spike hits.

```json
resource "aws_autoscaling_policy" "predictive" {
  name                   = "predictive-scaling"
  autoscaling_group_name = aws_autoscaling_group.api.name
  policy_type            = "PredictiveScaling"

  predictive_scaling_configuration {
    metric_specification {
      target_value = 60  // target CPU

      predefined_scaling_metric_specification {
        predefined_metric_type = "ASGAverageCPUUtilization"
        resource_label         = ""
      }
      predefined_load_metric_specification {
        predefined_metric_type = "ASGTotalCPUUtilization"
        resource_label         = ""
      }
    }

    mode                          = "ForecastAndScale"  // actually act on predictions
    scheduling_buffer_time        = 300                  // 5 min buffer before predicted spike
    max_capacity_breach_behavior  = "HonorMaxCapacity"
  }
}
```

#### 5.5 ECS Service Auto Scaling (For Containers)

```json
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 500
  min_capacity       = 30
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "ecs-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 60
    scale_in_cooldown  = 300   // wait 5 min before removing instances
    scale_out_cooldown = 60    // but scale out fast (1 min)
  }
}

// Custom metric: scale on queue depth
resource "aws_appautoscaling_policy" "ecs_queue" {
  name               = "ecs-queue-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"
      dimensions {
        name  = "QueueName"
        value = "order-processing"
      }
    }
    target_value = 100  // 100 messages per task
  }
}
```

### Auto-Scaling Timing Reality

This is what people get wrong. Scaling is **not instant**:

```
Event Timeline for EC2 Auto Scaling:

00:00  Traffic spike detected
00:01  CloudWatch alarm triggers (1-min evaluation period)
00:02  ASG launches new instances
00:03  EC2 instance booting (AMI loading, OS starting)
00:04  Application starting, dependencies loading
00:05  Health check passing
00:05  Instance registered with ALB
00:06  ALB draining connections to new instance
       ─────────────────────────────────────────
       TOTAL: 5-6 minutes from spike to serving traffic

With Warm Pools:
00:00  Traffic spike detected
00:01  CloudWatch alarm triggers
00:01  Warm pool instance starting (already booted)
00:02  Application resuming from hibernation
00:02  Health check passing, registered with ALB
       ─────────────────────────────────────────
       TOTAL: 2 minutes

With ECS Fargate:
00:00  Traffic spike detected
00:01  CloudWatch alarm triggers
00:02  New tasks launching (container pulling)
00:03  Container starting, health check passing
       ─────────────────────────────────────────
       TOTAL: 3 minutes

With Pre-provisioned capacity (Fargate capacity providers):
00:00  Traffic spike detected
00:01  New tasks launching (image cached)
00:01  Container starting
00:02  Health check passing
       ─────────────────────────────────────────
       TOTAL: 1-2 minutes
```

**Key insight**: You must **over-provision by 20-30%** to absorb spikes during
the scaling lag.

---

## 6. Manual Scaling Playbook

### When Manual Scaling Is Necessary

Auto-scaling reacts. Sometimes you need to **proactively** scale:

- **Planned events** — Black Friday, product launch, Super Bowl ad
- **Marketing campaigns** — Email blast to 10M users at 9 AM
- **Known traffic patterns** — Daily peak you can predict exactly
- **Emergency scaling** — Auto-scaling too slow, need capacity NOW

### 6.1 Scheduled Scaling

Pre-configure scaling actions for known events.

```json
// Scale up every weekday at 8 AM EST, down at 10 PM EST
resource "aws_autoscaling_schedule" "morning_scale_up" {
  scheduled_action_name  = "morning-scale-up"
  autoscaling_group_name = aws_autoscaling_group.api.name
  min_size               = 100
  max_size               = 500
  desired_capacity       = 150
  recurrence             = "0 13 * * MON-FRI"  // 8 AM EST = 13:00 UTC
}

resource "aws_autoscaling_schedule" "evening_scale_down" {
  scheduled_action_name  = "evening-scale-down"
  autoscaling_group_name = aws_autoscaling_group.api.name
  min_size               = 30
  max_size               = 200
  desired_capacity       = 50
  recurrence             = "0 3 * * MON-FRI"   // 10 PM EST = 03:00 UTC
}

// Black Friday special: 5x normal capacity
resource "aws_autoscaling_schedule" "black_friday_pre_scale" {
  scheduled_action_name  = "black-friday-prescale"
  autoscaling_group_name = aws_autoscaling_group.api.name
  min_size               = 500
  max_size               = 2000
  desired_capacity       = 800
  start_time             = "2026-11-27T06:00:00Z"  // 6 hours before event
  end_time               = "2026-11-30T06:00:00Z"  // keep for 3 days
}
```

### 6.2 AWS CLI — Emergency Manual Scaling

When things are on fire:

```bash
# EMERGENCY: Scale to 500 instances NOW
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name api-asg \
  --desired-capacity 500

# Raise the ceiling first if max is too low
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name api-asg \
  --max-size 1000 \
  --desired-capacity 500

# For ECS:
aws ecs update-service \
  --cluster production \
  --service api-service \
  --desired-count 500

# Check current state
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-name api-asg \
  --query 'AutoScalingGroups[0].{
    Desired:DesiredCapacity,
    Min:MinSize,
    Max:MaxSize,
    Running:length(Instances[?LifecycleState==`InService`])
  }'
```

### 6.3 Pre-Warming Load Balancers

ALBs auto-scale internally, but they can't handle a sudden 10x spike.
For planned events, you must pre-warm:

```bash
# Contact AWS Support to pre-warm your ALB
# You need to provide:
# - Expected peak RPS
# - Expected request/response sizes
# - Date and time of the event
# - Duration

# Or use NLB (Network Load Balancer) which handles sudden spikes better
# NLB scales to millions of RPS without pre-warming
```

### 6.4 Real-World Manual Scaling Runbook

```markdown
## Pre-Event Scaling Runbook (T minus 6 hours)

### T-6h: Preparation
- [ ] Verify AMI/container images are latest stable
- [ ] Check AWS service limits (EC2, ECS, ENIs, EIPs)
- [ ] Request limit increases if needed (takes minutes to hours)
- [ ] Verify all regions healthy

### T-4h: Scale Infrastructure
- [ ] Scale RDS to larger instance: db.r6g.4xlarge → db.r6g.16xlarge
- [ ] Add RDS read replicas: 2 → 6
- [ ] Scale ElastiCache: r6g.xlarge → r6g.4xlarge
- [ ] Pre-warm DynamoDB: switch to provisioned, set 100K WCU / 500K RCU

### T-2h: Scale Compute
- [ ] Set ASG min=500, desired=500 in us-east-1
- [ ] Set ASG min=300, desired=300 in eu-west-1
- [ ] Wait for all instances to pass health checks
- [ ] Verify ALB has all targets healthy

### T-1h: Validate
- [ ] Run load test at 50% expected peak
- [ ] Verify latency P99 < 200ms
- [ ] Verify error rate < 0.1%
- [ ] Verify all monitoring dashboards working
- [ ] Brief on-call team

### T-0: Event Start
- [ ] Monitor dashboards
- [ ] Keep scaling CLI commands ready
- [ ] Watch for: CPU > 70%, memory > 80%, 5xx > 0.5%, latency P99 > 500ms

### T+4h: Scale Down (Gradual)
- [ ] Reduce desired by 20% every 30 minutes
- [ ] Never scale down more than 20% at once (connection draining)
- [ ] Return to normal capacity over 2-3 hours
```

---

## 7. Real AWS Configuration Examples

### 7.1 Complete VPC for Multi-AZ Deployment

```json
// VPC spanning 3 AZs with public/private subnets
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

// Public subnets (for ALB)
resource "aws_subnet" "public" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet("10.0.0.0/16", 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true
}

// Private subnets (for application servers)
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet("10.0.0.0/16", 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

// NAT Gateway in each AZ (for outbound internet from private subnets)
resource "aws_nat_gateway" "main" {
  count         = 3  // one per AZ for high availability
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}
```

### 7.2 Application Load Balancer

```json
resource "aws_lb" "api" {
  name               = "api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2               = true

  // Access logs for debugging
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "api-alb"
    enabled = true
  }
}

resource "aws_lb_target_group" "api" {
  name        = "api-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  // for ECS Fargate

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 15
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    timeout             = 5
    unhealthy_threshold = 3
  }

  // Slow start: ramp up traffic to new instances over 60s
  slow_start = 60

  // Sticky sessions (only if needed — breaks even distribution)
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600
    enabled         = false  // disable for stateless APIs
  }

  // Deregistration delay: allow in-flight requests to complete
  deregistration_delay = 30
}
```

### 7.3 CloudFront for Global Edge Caching

```json
resource "aws_cloudfront_distribution" "api" {
  enabled = true
  aliases = ["api.myservice.com"]

  origin {
    domain_name = aws_lb.api.dns_name
    origin_id   = "api-alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_keepalive_timeout = 60
      origin_read_timeout      = 30
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api-alb"

    // Cache GET requests, forward everything else
    cache_policy_id          = aws_cloudfront_cache_policy.api.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  // Static assets: cache aggressively
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api-alb"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl                = 86400     // 1 day
    default_ttl            = 604800    // 7 days
    max_ttl                = 31536000  // 1 year
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.api.arn
    ssl_support_method  = "sni-only"
  }
}
```

---

## 8. Data Layer Scaling

The database is almost always the bottleneck. Here's how to scale it.

### 8.1 Read Replicas (Read-Heavy Workloads)

Most applications are 90%+ reads.

```
                    ┌──────────────────┐
                    │   Application    │
                    └────────┬─────────┘
                             │
                   ┌─────────┴──────────┐
                   │                     │
              Writes (10%)          Reads (90%)
                   │                     │
                   ▼                     ▼
          ┌──────────────┐     ┌─────────────────┐
          │   Primary    │     │  Read Replica    │
          │   Writer     │────►│  Pool            │
          │   Instance   │     │                  │
          └──────────────┘     │  ┌────────────┐  │
                               │  │ Replica 1  │  │
                               │  │ Replica 2  │  │
                               │  │ Replica 3  │  │
                               │  │ Replica 4  │  │
                               │  │ Replica 5  │  │
                               │  └────────────┘  │
                               └─────────────────┘
```

```json
// Aurora with auto-scaling read replicas
resource "aws_rds_cluster" "main" {
  cluster_identifier = "api-db"
  engine             = "aurora-postgresql"
  engine_version     = "15.4"
  database_name      = "app"

  // Writer instance
  master_username = "admin"
  master_password = var.db_password

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"

  // Performance Insights
  performance_insights_enabled = true
}

// Writer instance
resource "aws_rds_cluster_instance" "writer" {
  identifier         = "api-db-writer"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.r6g.4xlarge"  // 16 vCPU, 128GB RAM
  engine             = "aurora-postgresql"
}

// Read replicas (start with 2, auto-scale to 15)
resource "aws_rds_cluster_instance" "reader" {
  count              = 2
  identifier         = "api-db-reader-${count.index}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.r6g.2xlarge"
  engine             = "aurora-postgresql"
}

// Auto-scale read replicas based on CPU
resource "aws_appautoscaling_target" "aurora_replicas" {
  service_namespace  = "rds"
  scalable_dimension = "rds:cluster:ReadReplicaCount"
  resource_id        = "cluster:${aws_rds_cluster.main.id}"
  min_capacity       = 2
  max_capacity       = 15
}

resource "aws_appautoscaling_policy" "aurora_cpu" {
  name               = "aurora-cpu-scaling"
  service_namespace  = "rds"
  scalable_dimension = "rds:cluster:ReadReplicaCount"
  resource_id        = "cluster:${aws_rds_cluster.main.id}"
  policy_type        = "TargetTrackingScaling"

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "RDSReaderAverageCPUUtilization"
    }
    target_value       = 60
    scale_in_cooldown  = 600
    scale_out_cooldown = 120
  }
}
```

### 8.2 Sharding (Write-Heavy Workloads)

When a single writer can't keep up, split data across multiple databases.

```
             ┌─────────────────────────────┐
             │      Routing Layer          │
             │  shard = hash(user_id) % 4  │
             └──────────┬──────────────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
    ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
    │  Shard 0  │ │  Shard 1  │ │  Shard 2  │ ...
    │ users 0-  │ │ users 25- │ │ users 50- │
    │ 24.99%    │ │ 49.99%    │ │ 74.99%    │
    │           │ │           │ │           │
    │ Writer +  │ │ Writer +  │ │ Writer +  │
    │ 2 Readers │ │ 2 Readers │ │ 2 Readers │
    └───────────┘ └───────────┘ └───────────┘

    Each shard handles 1/N of the writes
    Total write capacity = N × single_shard_capacity
```

### 8.3 DynamoDB for Infinite Scale

DynamoDB is purpose-built for horizontal scaling with no operational overhead.

```json
resource "aws_dynamodb_table" "orders" {
  name         = "orders"
  billing_mode = "PAY_PER_REQUEST"  // auto-scales writes/reads

  hash_key  = "customer_id"  // partition key (determines which shard)
  range_key = "order_id"     // sort key

  attribute {
    name = "customer_id"
    type = "S"
  }
  attribute {
    name = "order_id"
    type = "S"
  }

  // Global secondary index for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  // For known traffic: use provisioned mode with auto-scaling
  // billing_mode = "PROVISIONED"
  // read_capacity  = 50000
  // write_capacity = 25000
}

// DynamoDB auto-scaling (if using provisioned mode)
resource "aws_appautoscaling_target" "dynamodb_reads" {
  max_capacity       = 500000  // 500K RCU
  min_capacity       = 10000
  resource_id        = "table/orders"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_read_policy" {
  name               = "dynamodb-read-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_reads.resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_reads.scalable_dimension
  service_namespace  = "dynamodb"

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = 70
  }
}
```

---

## 9. Caching at Every Layer

Caching is the single most effective way to reduce load. At 1M RPS, caching
can turn 1M backend calls into 50K.

```
Request Flow with Caching:

User → CloudFront Edge (Layer 1: CDN cache)
         ↓ miss
     → API Gateway (Layer 2: API response cache)
         ↓ miss
     → Application Server
         → ElastiCache Redis (Layer 3: application cache)
              ↓ miss
         → Database (Layer 4: query result cache / buffer pool)
              ↓ miss
         → Disk

Hit rates at each layer:
  CDN:         60-80% of GET requests never reach your servers
  API Cache:   20-40% of remaining
  App Cache:   70-90% of remaining
  DB Cache:    95%+ from buffer pool

Net result: 1M RPS at CDN = ~10K RPS at database
```

### ElastiCache Redis Cluster

```json
resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "api-cache"
  description          = "API response cache"
  node_type            = "cache.r6g.2xlarge"  // 52GB RAM

  // Cluster mode: shard data across multiple nodes
  num_node_groups         = 6   // 6 shards
  replicas_per_node_group = 2   // 2 replicas per shard (total 18 nodes)

  // Spread across AZs
  automatic_failover_enabled = true
  multi_az_enabled           = true

  // Performance
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  engine_version             = "7.0"

  // Auto-scaling (ElastiCache for Redis supports shard scaling)
  parameter_group_name = aws_elasticache_parameter_group.main.name

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.cache.id]
}

// Total cache capacity: 6 shards × 52GB = 312GB
// Total read throughput: 18 nodes × ~100K RPS = ~1.8M cache reads/sec
```

### Caching Strategy in Code

```python
import redis
import json
import hashlib
from functools import wraps

redis_cluster = redis.RedisCluster(
    startup_nodes=[{"host": "api-cache.xyz.clustercfg.use1.cache.amazonaws.com", "port": 6379}],
    decode_responses=True,
    skip_full_coverage_check=True,
)

def cached(ttl_seconds=300, prefix="api"):
    """Cache decorator with automatic key generation and stampede protection."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{func.__name__}:{_make_key(args, kwargs)}"

            # Try cache first
            cached_value = redis_cluster.get(cache_key)
            if cached_value is not None:
                return json.loads(cached_value)

            # Cache miss — acquire lock to prevent thundering herd
            lock_key = f"lock:{cache_key}"
            lock = redis_cluster.lock(lock_key, timeout=5, blocking_timeout=2)

            if lock.acquire(blocking=True):
                try:
                    # Double-check after acquiring lock
                    cached_value = redis_cluster.get(cache_key)
                    if cached_value is not None:
                        return json.loads(cached_value)

                    result = await func(*args, **kwargs)
                    redis_cluster.setex(cache_key, ttl_seconds, json.dumps(result))
                    return result
                finally:
                    lock.release()
            else:
                # Couldn't get lock, another request is computing — use stale value
                stale = redis_cluster.get(f"stale:{cache_key}")
                if stale:
                    return json.loads(stale)
                # No stale value, compute anyway
                return await func(*args, **kwargs)

        return wrapper
    return decorator

def _make_key(args, kwargs):
    """Create a deterministic cache key from function arguments."""
    raw = json.dumps({"a": str(args), "k": str(sorted(kwargs.items()))})
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

---

## 10. Load Balancing Strategies

### Layer 4 (Network) vs Layer 7 (Application)

```
Layer 4 (NLB):                    Layer 7 (ALB):
- TCP/UDP level                   - HTTP/HTTPS level
- No request inspection           - Path/header/cookie routing
- Ultra-low latency (<100μs)      - Higher latency (~1ms)
- Millions of RPS easily          - Hundreds of thousands RPS
- Static IP support               - No static IP (use Global Accelerator)
- No WAF integration              - WAF integration

Use NLB when:                     Use ALB when:
- Maximum performance needed      - Need path-based routing
- gRPC / WebSocket / non-HTTP     - Multiple services behind one LB
- Need static IPs                 - Need WAF / auth offloading
```

### Global Accelerator (Static IP + Global Routing)

```json
resource "aws_globalaccelerator_accelerator" "api" {
  name            = "api-accelerator"
  ip_address_type = "IPV4"
  enabled         = true

  attributes {
    flow_logs_enabled   = true
    flow_logs_s3_bucket = aws_s3_bucket.flow_logs.id
    flow_logs_s3_prefix = "ga-flow-logs/"
  }
}

resource "aws_globalaccelerator_listener" "api" {
  accelerator_arn = aws_globalaccelerator_accelerator.api.id
  protocol        = "TCP"
  port_range {
    from_port = 443
    to_port   = 443
  }
}

// Route to US and EU endpoints
resource "aws_globalaccelerator_endpoint_group" "us" {
  listener_arn          = aws_globalaccelerator_listener.api.id
  endpoint_group_region = "us-east-1"
  traffic_dial_percentage = 100

  endpoint_configuration {
    endpoint_id = aws_lb.api_us.arn
    weight      = 100
  }

  health_check_path             = "/health"
  health_check_interval_seconds = 10
  threshold_count               = 3
}

resource "aws_globalaccelerator_endpoint_group" "eu" {
  listener_arn          = aws_globalaccelerator_listener.api.id
  endpoint_group_region = "eu-west-1"
  traffic_dial_percentage = 100

  endpoint_configuration {
    endpoint_id = aws_lb.api_eu.arn
    weight      = 100
  }

  health_check_path             = "/health"
  health_check_interval_seconds = 10
  threshold_count               = 3
}
```

---

## 11. Real-World Architecture: 1M RPS System

### Full Architecture Diagram

```
                         Internet
                            │
                    ┌───────┴────────┐
                    │  CloudFront    │  450+ edge locations worldwide
                    │  (CDN + WAF)   │  Handles 600K RPS via cache
                    └───────┬────────┘
                            │
                    ┌───────┴────────┐
                    │  Route 53      │  Latency-based routing
                    │  (DNS)         │  Health-check failover
                    └───┬───────┬───┘
                        │       │
            ┌───────────┘       └───────────┐
            │                               │
    ┌───────┴────────┐             ┌────────┴───────┐
    │  us-east-1     │             │  eu-west-1     │
    │                │             │                │
    │ ┌────────────┐ │             │ ┌────────────┐ │
    │ │ NLB        │ │             │ │ NLB        │ │
    │ │ (static IP)│ │             │ │ (static IP)│ │
    │ └─────┬──────┘ │             │ └─────┬──────┘ │
    │       │        │             │       │        │
    │ ┌─────┴──────┐ │             │ ┌─────┴──────┐ │
    │ │ ALB        │ │             │ │ ALB        │ │
    │ │ (routing)  │ │             │ │ (routing)  │ │
    │ └─────┬──────┘ │             │ └─────┬──────┘ │
    │       │        │             │       │        │
    │ ┌─────┴──────┐ │             │ ┌─────┴──────┐ │
    │ │ ECS Fargate│ │             │ │ ECS Fargate│ │
    │ │ 200 tasks  │ │             │ │ 200 tasks  │ │
    │ │ (3 AZs)    │ │             │ │ (3 AZs)    │ │
    │ └──┬────┬────┘ │             │ └──┬────┬────┘ │
    │    │    │      │             │    │    │      │
    │ ┌──┴┐ ┌┴───┐  │             │ ┌──┴┐ ┌┴───┐  │
    │ │Red│ │Aur- │  │◄──────────►│ │Red│ │Aur- │  │
    │ │is │ │ora  │  │  Global    │ │is │ │ora  │  │
    │ │   │ │Glbl │  │  Tables    │ │   │ │Glbl │  │
    │ └───┘ └─────┘  │             │ └───┘ └─────┘  │
    └────────────────┘             └────────────────┘
```

### Request Flow Walkthrough (1M RPS)

```
1,000,000 RPS arrives at CloudFront
    │
    ├── 600,000 served from CDN edge cache (60% hit rate)
    │
    400,000 RPS reaches origin
    │
    ├── Route 53: 240K → us-east-1, 160K → eu-west-1
    │
    240,000 RPS → us-east-1 ALB
    │
    ├── 200 ECS tasks (each handles ~1,200 RPS)
    │
    ├── 216,000 served from Redis cache (90% hit rate)
    │
    24,000 RPS → Aurora PostgreSQL
    │
    ├── 1 writer handles 4K writes/sec
    ├── 5 readers handle 20K reads/sec (4K each)
    │
    └── Done. DB sees 24K RPS, not 1M.
```

### Capacity Math

```
Target: 1,000,000 RPS total

CDN Layer:
  CloudFront: effectively unlimited (AWS manages this)
  Cache hit rate: 60%
  Origin RPS: 400,000

Compute Layer (per region, 2 regions):
  Per-task capacity: 1,200 RPS (benchmarked)
  Tasks needed per region: 400,000 ÷ 2 ÷ 1,200 = 167 → round to 200
  Task size: 2 vCPU, 4GB RAM (Fargate)
  Total per region: 400 vCPU, 800GB RAM
  With 20% headroom: 240 tasks per region

Cache Layer (per region):
  Redis cluster: 6 shards × 3 nodes = 18 nodes
  Per-node capacity: ~100K reads/sec
  Total: 1.8M reads/sec (plenty of headroom)

Database Layer (per region):
  Origin RPS after cache: ~24K per region
  Reads: ~20K/sec → 5 read replicas
  Writes: ~4K/sec → 1 writer (r6g.4xlarge handles ~10K writes/sec)
```

---

## 12. Cost Optimization

### Cost Breakdown for 1M RPS (Monthly Estimate)

```
Component                     Monthly Cost (approx.)
─────────────────────────────────────────────────────
CloudFront (1M RPS)           $15,000 - $25,000
  - 2.6T requests/month
  - Data transfer ~500TB

Compute (480 Fargate tasks)   $35,000 - $45,000
  - 2 regions × 240 tasks
  - 2 vCPU / 4GB each
  - Mix of on-demand + Spot

Redis (36 nodes total)        $18,000 - $22,000
  - 2 regions × 18 nodes
  - r6g.2xlarge

Aurora (2 clusters)           $12,000 - $18,000
  - 2 writers + 10 readers
  - r6g.2xlarge instances

NLB + ALB (4 total)           $2,000 - $3,000

Route 53 + Health Checks      $500

Monitoring (CloudWatch)       $3,000 - $5,000

Data Transfer                 $8,000 - $15,000
  - Cross-AZ, cross-region
─────────────────────────────────────────────────────
TOTAL                         $95,000 - $135,000/month

That's $0.000003 - $0.000005 per request.
```

### Cost Reduction Strategies

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Fargate Spot for 60% of tasks | 30-40% compute | Interruptions (need graceful handling) |
| Reserved Instances (1yr) | 30-40% compute | Commitment |
| Savings Plans (3yr) | 50-60% compute | Longer commitment |
| Increase cache hit rate 60→80% | 50% origin cost | More cache RAM needed |
| Use ARM instances (Graviton) | 20% compute | Must compile for ARM |
| Compress responses (gzip/brotli) | 40% data transfer | Slight CPU increase |
| Move static to S3 + CloudFront | 80% for static assets | Deployment change |

---

## 13. Monitoring and Observability

### The Four Golden Signals at Scale

```
1. LATENCY (How long requests take)
   ─────────────────────────────────
   Track: P50, P95, P99, P99.9
   Alert: P99 > 500ms
   Dashboard: Latency heatmap by endpoint

2. TRAFFIC (How many requests)
   ─────────────────────────────────
   Track: RPS by region, endpoint, status code
   Alert: Sudden drop > 30% (likely outage)
   Dashboard: RPS timeseries with region overlay

3. ERRORS (How many failures)
   ─────────────────────────────────
   Track: 5xx rate, 4xx rate, timeout rate
   Alert: 5xx > 0.1% of traffic
   Dashboard: Error rate + top error endpoints

4. SATURATION (How full is the system)
   ─────────────────────────────────
   Track: CPU, memory, connections, queue depth
   Alert: Any resource > 80%
   Dashboard: Resource utilization heatmap
```

### CloudWatch Dashboard (Terraform)

```json
resource "aws_cloudwatch_dashboard" "scaling" {
  dashboard_name = "horizontal-scaling"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Request Rate (RPS)"
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.api.arn_suffix,
             { stat = "Sum", period = 60, label = "us-east-1" }],
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "api-eu-alb",
             { stat = "Sum", period = 60, label = "eu-west-1", region = "eu-west-1" }]
          ]
          view    = "timeSeries"
          region  = "us-east-1"
          period  = 60
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Active Task Count"
          metrics = [
            ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", "production",
             "ServiceName", "api-service", { stat = "Average" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Response Latency"
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.api.arn_suffix,
             { stat = "p50", label = "P50" }],
            ["...", { stat = "p95", label = "P95" }],
            ["...", { stat = "p99", label = "P99" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "5xx Error Rate"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer",
             aws_lb.api.arn_suffix, { stat = "Sum", period = 60 }]
          ]
        }
      }
    ]
  })
}
```

### Key Alerts

```json
// Alert: Scaling is hitting max capacity
resource "aws_cloudwatch_metric_alarm" "at_max_capacity" {
  alarm_name          = "CRITICAL-at-max-scaling-capacity"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "DesiredCapacity"
  namespace           = "AWS/AutoScaling"
  period              = 60
  statistic           = "Maximum"
  threshold           = 480  // 96% of max 500
  alarm_actions       = [aws_sns_topic.pager.arn]

  dimensions = {
    AutoScalingGroupName = "api-asg"
  }
}

// Alert: Error rate spike
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "HIGH-5xx-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 0.5  // 0.5% error rate

  metric_query {
    id          = "error_rate"
    expression  = "(errors / total) * 100"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "HTTPCode_Target_5XX_Count"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "Sum"
      dimensions  = { LoadBalancer = aws_lb.api.arn_suffix }
    }
  }

  metric_query {
    id = "total"
    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "Sum"
      dimensions  = { LoadBalancer = aws_lb.api.arn_suffix }
    }
  }

  alarm_actions = [aws_sns_topic.pager.arn]
}
```

---

## 14. Common Pitfalls

### Pitfall 1: Stateful Servers

```
WRONG:                                RIGHT:
┌──────────┐                          ┌──────────┐
│ Server 1 │ ← session in memory      │ Server 1 │
│ user: Bob│                          │ stateless │──┐
└──────────┘                          └──────────┘  │
     ↑ Bob must always go here             ↑        │
     │ (sticky sessions)                   │        │
     │                                     │     ┌──┴──────┐
   If Server 1 dies,                    Any      │  Redis   │
   Bob's session is GONE              server     │  Session │
                                      works      │  Store   │
                                                 └─────────┘
```

**Rule**: Store sessions in Redis/DynamoDB, not in application memory.

### Pitfall 2: Database Connection Exhaustion

```
200 application instances × 20 connections each = 4,000 connections
PostgreSQL max_connections default: 100 😱

Solution: Connection pooling with PgBouncer or RDS Proxy

┌──────────────────────────────────────────────────┐
│  200 App Instances                               │
│  (4,000 total connections)                       │
└─────────────────────┬────────────────────────────┘
                      │
            ┌─────────┴──────────┐
            │  RDS Proxy         │
            │  Pools connections  │
            │  4,000 → 200       │
            └─────────┬──────────┘
                      │
            ┌─────────┴──────────┐
            │  Aurora PostgreSQL  │
            │  200 connections    │
            └────────────────────┘
```

```json
resource "aws_db_proxy" "main" {
  name                   = "api-db-proxy"
  debug_logging          = false
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 1800
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_security_group_ids = [aws_security_group.db_proxy.id]
  vpc_subnet_ids         = aws_subnet.private[*].id

  auth {
    auth_scheme = "SECRETS"
    iam_auth    = "DISABLED"
    secret_arn  = aws_secretsmanager_secret.db_credentials.arn
  }
}
```

### Pitfall 3: Thundering Herd on Cache Miss

When a popular cache key expires, 1000 servers all hit the database simultaneously.

```
Cache expires at T=0

T=0.001  Server 1: cache miss → query DB
T=0.002  Server 2: cache miss → query DB
T=0.003  Server 3: cache miss → query DB
...
T=0.050  Server 200: cache miss → query DB

200 identical queries hit DB at once!

Solution: Cache stampede protection (see caching section)
- Distributed lock: only 1 server recomputes
- Stale-while-revalidate: serve old value while refreshing
- Probabilistic early expiration: randomize TTL so keys don't expire together
```

### Pitfall 4: Not Testing at Scale

```
Dev testing:     10 RPS   → "works great!"
Staging:         1K RPS   → "looks good!"
Production:      100K RPS → everything on fire 🔥

Hidden at low scale:
- Memory leaks (crash after hours, not minutes)
- Connection pool exhaustion
- Lock contention
- DNS resolution bottlenecks
- Kernel TCP tuning (somaxconn, backlog)
- File descriptor limits
- Garbage collection pauses

Load test BEFORE production:
  $ k6 run --vus 10000 --duration 30m load_test.js
  $ locust --headless -u 50000 -r 1000 --run-time 1h
```

### Pitfall 5: Ignoring DNS TTL

```
Route 53 failover happens, but clients cache old DNS for 5 minutes.
5 minutes of errors during a region failover.

Fix: Set low TTL on failover records
  TTL = 60 seconds (1 minute)
  Trade-off: More DNS queries, but faster failover

For internal service discovery, use:
  - AWS Cloud Map (1-second health checks)
  - ECS Service Connect
  - App Mesh
```

---

## 15. Checklist: Are You Ready for 1M RPS?

### Architecture

- [ ] Application is fully stateless (no in-memory sessions)
- [ ] Deployed across 3+ AZs per region
- [ ] Active-active in 2+ regions
- [ ] All data replicated across regions
- [ ] Circuit breakers on all downstream calls
- [ ] Retry with exponential backoff + jitter
- [ ] Graceful degradation when dependencies fail
- [ ] Feature flags to disable non-critical features under load

### Scaling

- [ ] Auto-scaling configured on compute (ECS/EC2/EKS)
- [ ] Auto-scaling configured on database read replicas
- [ ] Auto-scaling configured on cache cluster
- [ ] Warm pools or pre-provisioned capacity
- [ ] Predictive scaling enabled for known patterns
- [ ] Manual scaling runbook documented and tested
- [ ] AWS service limits reviewed and increased

### Data

- [ ] Read replicas handle 90%+ of read traffic
- [ ] Connection pooling (RDS Proxy / PgBouncer)
- [ ] DynamoDB or similar for infinite-scale tables
- [ ] Cache hit rate > 80% for hot data
- [ ] Cache stampede protection implemented
- [ ] Async processing for non-critical writes (SQS/Kinesis)

### Networking

- [ ] CloudFront CDN for static + cacheable dynamic content
- [ ] ALB pre-warmed for events (contact AWS Support)
- [ ] Route 53 health checks with failover
- [ ] Global Accelerator for static IP + anycast
- [ ] TLS termination at load balancer (not application)

### Observability

- [ ] P50/P95/P99 latency tracked per endpoint
- [ ] Error rate alerted at 0.1% threshold
- [ ] Scaling events tracked (when and how many)
- [ ] Capacity alerts before hitting max
- [ ] Region-level health dashboard
- [ ] Runbook for every alert

### Testing

- [ ] Load tested at 120% of expected peak
- [ ] Chaos tested: kill an AZ, kill a region
- [ ] Tested failover time (< 60 seconds)
- [ ] Tested scale-out time (< 5 minutes to 2x)
- [ ] Tested scale-in (no request drops)
- [ ] Game day conducted with full team

---

## Quick Reference: AWS Services for Each Concern

| Concern | AWS Service | Alternative |
|---------|-------------|-------------|
| Global DNS routing | Route 53 | Cloudflare DNS |
| CDN / Edge cache | CloudFront | Fastly, Cloudflare |
| DDoS protection | AWS Shield + WAF | Cloudflare |
| Load balancing (L7) | ALB | Nginx, Envoy |
| Load balancing (L4) | NLB | HAProxy |
| Compute (containers) | ECS Fargate | EKS, Lambda |
| Compute (VMs) | EC2 + ASG | — |
| Compute (serverless) | Lambda | — |
| Cache | ElastiCache Redis | Memcached, Momento |
| Relational DB | Aurora PostgreSQL | RDS, PlanetScale |
| NoSQL DB | DynamoDB | MongoDB Atlas, ScyllaDB |
| Message queue | SQS | RabbitMQ, Kafka (MSK) |
| Event streaming | Kinesis / MSK | Confluent |
| Service mesh | App Mesh | Istio, Linkerd |
| Secrets | Secrets Manager | HashiCorp Vault |
| Monitoring | CloudWatch | Datadog, Grafana |
| Tracing | X-Ray | Jaeger, Honeycomb |

---

> **Bottom line**: Reaching 1M RPS is not about any single trick. It's the
> combination of CDN caching, multi-region deployment, auto-scaling compute,
> distributed caching, database read replicas, connection pooling, and
> asynchronous processing — all working together, monitored carefully, and
> tested ruthlessly.
