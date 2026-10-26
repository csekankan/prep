# Large-Scale Engineering Best Practices

> A structured study path for designing, operating, and shipping systems at FAANG scale—estimation, traffic control, deployments, incidents, cost, security, and real architectures.

---

## Who This Is For

You are building (or interviewing for) systems that serve millions to billions of users. These modules connect **back-of-the-envelope math**, **production patterns**, and **how big tech actually runs**—without assuming you already work at a hyperscaler.

## How to Use These Guides

1. Read one module end-to-end (45–90 minutes).
2. Run the code examples locally.
3. Answer the three interview questions out loud.
4. Complete the exercises before moving on.

## Module Roadmap

| # | Module | Status | Focus |
|---|--------|--------|--------|
| 01 | [Capacity Planning and Estimation](./01-capacity-planning-and-estimation.md) | Available | QPS, storage, bandwidth, latency numbers, headroom, load testing |
| 02 | [Traffic Management at Scale](./02-traffic-management-at-scale.md) | Available | Rate limits, circuit breakers, backpressure, load shedding |
| 03 | [Deployment Strategies at Scale](./03-deployment-strategies-at-scale.md) | Available | Blue-green, canary, GitOps, migrations, feature flags |
| 04 | Operational Excellence and Incident Management | Planned | SLOs, on-call, postmortems, runbooks, chaos engineering |
| 05 | Cost Engineering and FinOps | Planned | Unit economics, rightsizing, spot, reserved capacity |
| 06 | Testing at Scale | Planned | Load, soak, fault injection, release gates |
| 07 | Security Best Practices at Scale | Planned | Zero trust, secrets, supply chain, abuse prevention |
| 08 | Data Governance and Compliance | Planned | Retention, PII, audit trails, regional data |
| 09 | Team Topologies and Platform Engineering | Planned | Platform teams, golden paths, internal developer portals |
| 10 | Real-World Large-Scale Architectures | Planned | Case studies: feed, search, payments, streaming |

## Prerequisites

- Basic HTTP, SQL, and one scripting language (Python examples throughout).
- Familiarity with Kubernetes and cloud concepts helps for modules 02–03.
- Optional: prior system design interview prep (this series goes deeper on **operations**).

## Related Paths in This Repo

- Event-driven and streaming patterns under `MD/event-driven-architecture/`
- Inference and serving at scale under `MD/inference-engineering/`

---

*Last updated: October 2026*
