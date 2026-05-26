# Capability-Driven Design — Staff Engineer Guide

**Audience:** Staff+ engineers aligning **engineering delivery** with **business capabilities** at portfolio and platform scale.  
**Scope:** What “capability-driven” means in industry practice, **API and platform design**, contrasts with DDD and other planning lenses, and **failure modes**.

---

## 1. Objective and definitions

### 1.1 What we mean by “capability-driven”

In enterprise and platform engineering, **business capability** usually means: a **stable, business-meaningful** ability the organization needs (e.g., “capture customer order,” “calculate tax,” “authorize payment,” “publish product catalog,” “manage entitlement”).

**Capability-driven design** (as used in practice—not a single academic book like DDD) means:

1. **Structuring discovery, funding, and roadmaps** around **capabilities** (and outcomes), not only around apps, projects, or org silos.  
2. **Mapping applications, data, and APIs** to **which capabilities** they implement or enable—so redundancy and gaps are visible.  
3. **Organizing engineering assets** (repos, services, teams) so that **delivery units** align to **coherent capability slices** where possible—while accepting that **one capability may span multiple bounded contexts** technically.

**Objective for a staff engineer:** Make **tradeoffs explicit**: where capabilities are **shared platforms**, where they are **duplicated** (and why), and how **API surfaces** expose **stable capability contracts** to consumers without leaking every team’s internal model.

---

## 2. Industry-scale problem example

### Scenario: “Digital core” for a multinational (retail + wholesale + marketplace)

**Symptoms without a capability lens:**

- **150+ “customer” APIs** built by different programs; each claims to be “the” customer API.
- **Duplicate** capabilities: three tax engines, four entitlement stores, two loyalty ledgers—because each program optimized for **local velocity**.
- **Roadmaps** are project-based (“2026 replatform”) with **no map** of which **business abilities** are strengthened, retired, or left as **gaps**.
- **Integration chaos:** partners get a different API per region or brand; no **published** capability tier.

**Capability-driven response (conceptual):**

1. **Capability map** (business architecture): e.g., “Product information,” “Pricing,” “Inventory availability,” “Order capture,” “Fulfillment orchestration,” “Returns,” “Customer identity,” “Payments,” “Regulatory reporting.”  
2. **Heat-map** each capability: maturity, risk, duplication, ownership.  
3. **Decide platform vs local:** e.g., one **published** “Product information” capability API (open-host style) with SLAs; regional extensions only via **documented** extensions or separate **bounded** APIs—not forks.  
4. **API portfolio governance:** naming, lifecycle, deprecation, **consumer tiers** (internal vs partner vs public).

This is **portfolio and platform design** at scale—not the same problem as “modeling one context’s aggregates,” though the two **meet** at API boundaries.

---

## 3. Capability vs other decomposition axes

| Axis | Question it answers | Typical artifact |
|------|---------------------|----------------|
| **Capability** | **What** must the business be able to do? | Capability map, heat maps, investment themes |
| **Domain (DDD)** | **How** do we model and bound **language + consistency** for a slice of the problem? | Bounded contexts, ubiquitous language, aggregates |
| **Org / team topology** | **Who** owns delivery? | Team APIs, Conway considerations |
| **Technical layer** | **Where** does code run? | UI, BFF, services, data planes |

**Key staff-level insight:** A **single business capability** often **spans multiple DDD bounded contexts**. Example: “Capture order” touches **checkout**, **pricing**, **tax**, **inventory reservation**, **fraud**—each may be its own **context** with its own model.

- **Capability-driven** answers: *which outcomes we fund and which platform services we expose*.  
- **DDD** answers: *how we keep models honest inside each slice and how we integrate without semantic collapse*.

They are **complementary**, not competing religions.

---

## 4. Engineering structure: capability-aligned delivery

### 4.1 Repo and service layout (pattern)

A common pattern (including **capability-rooted monorepos**):

```text
capabilities/
  <capability-name>/
    apps/          # UIs, mobile, etc.
    api/           # public or application API for this capability slice
    domain/        # core model (often DDD-friendly modules)
    infra/         # IaC, pipelines specific to this slice
```

**Intent:** Onboard engineers around **business meaning**, reduce “everything in one bag” layouts, and make **ownership** negotiable per capability.

**Staff caveat:** Do not **force** one deployable per capability if **consistency** or **release cadence** doesn’t split that way—use **modules** and **clear APIs** first.

### 4.2 Internal reference (Nike CPI)

- [Technical Design: Capability Driven Folder Structure](https://confluence.nike.com/pages/viewpage.action?pageId=1416270749) — describes a **capability-driven** folder approach with `capabilities/<capability-name>/` and subprojects for app(s), API/backend, infra.

---

## 5. API design in a capability-driven world

### 5.1 Capability API vs context API

| Concept | Role |
|---------|------|
| **Context API (DDD)** | Speaks **one bounded context’s** ubiquitous language; enforces that context’s invariants. |
| **Capability API (portfolio)** | Presents a **coherent business ability** to consumers—may **orchestrate** multiple contexts behind the scenes. |

**Staff-level pattern:**

- **Stable façade** (BFF or capability API gateway) for **consumer-aligned** operations: `submitOrder`, `getOrderStatusForCustomer`.  
- **Internal context APIs** remain **narrow** and **owned**: `pricing.quote`, `inventory.reserve`, `payments.authorize`.

**Risk:** the façade becomes a **god orchestrator** with all rules. Mitigation: **domain services** in the right context, **sagas/process managers** with explicit state machines, **published events** for cross-context facts.

### 5.2 Published capability contracts

Treat **certain** APIs as **products**:

- **SLAs, versioning, deprecation policy**, consumer registration, changelog.  
- **Documentation** in **business** terms (capability) with **technical** appendix (schemas).

Align with ideas similar to **Open Host Service** / **published language** in DDD—but the **driver** here is **enterprise consumption**, not only one team’s model.

### 5.3 Example: “Product information” capability API (sketch)

**Consumer-facing (partner / channel):**

- `GET /products/{id}` — stable read model; eventual consistency explicit.  
- `POST /products:batchLookup` — bulk for storefronts.

**Behind the scenes:**

- Aggregates **catalog**, **media**, **compliance attributes** from **different contexts**; **ACL** at integration edges so **source systems** can change without breaking consumers.

### 5.4 Anti-patterns

- **Single enterprise data model** exposed as CRUD for every table—“capability” is only PowerPoint.  
- **Anonymous REST** resources named after DB tables (`/skus`, `/sku_attributes`, `/sku_prices`) with no **use-case** cohesion.  
- **Chameleon API** that changes meaning per consumer without versioning.

---

## 6. How capability-driven differs from DDD (and from “features”)

| Topic | Capability-driven | DDD |
|--------|-------------------|-----|
| **Primary question** | What abilities does the business need? What do we standardize vs allow duplicate? | Where are model boundaries? What is the language? |
| **Granularity** | Coarser, **business-stable** units | Finer **semantic** boundaries inside problem space |
| **API** | Portfolio-level **products** and **platform** surfaces | Context-local **truth** and **invariants** |
| **Success metric** | Reduced duplication, clear ownership, roadmap alignment | Reduced ambiguity, correct invariants, evolvable models |

**Vs feature-driven roadmaps:** Features are **time-boxed** deliverables. Capabilities are **durable** functions of the business. Staff engineers use capabilities to ask: *“After this feature ships, which capability maturity moved—and did we create new duplication?”*

---

## 7. Integration with other enterprise practices

- **Business capability maps** (EA) ↔ **DDD context maps** (engineering): link **capability** entries to **one or more** bounded contexts and **platform services**.  
- **Team Topologies** (stream-aligned, platform, enabling): platform teams often **own** cross-cutting **capability APIs** (e.g., identity, notifications).  
- **FinOps / portfolio:** capabilities help **justify** spend (“we run two payments stacks—map to same capability—consolidation case”).

---

## 8. Failure modes (staff-level)

1. **Capability theater** — maps on walls; code still organized by legacy app names only.  
2. **Capability = microservice** — forced 1:1 mapping creates wrong boundaries and distributed monoliths.  
3. **Ignoring DDD inside** — stable capability API hides a **ball of mud**; invariants break under load.  
4. **No product discipline** — “shared” APIs without owners, SLAs, or versioning.  
5. **Conflating capability with org** — reorg redraws lines; **business abilities** should outlive reorgs if the model is good.

---

## 9. Practical checklist (before you pitch an architecture)

- [ ] Can you name the **business capabilities** this system advances (not only Jira epics)?  
- [ ] For each **public** API, who is the **product owner** and what is the **deprecation** policy?  
- [ ] Which parts are **platform** (many consumers) vs **local** (one program)?  
- [ ] For each capability slice, have you identified **one or more DDD contexts** and **integration** style (ACL, events, open host)?  
- [ ] Do you have a plan for **read** vs **write** scaling that matches **capability** SLAs?

---

## 10. Suggested reading directions

- Business architecture / capability mapping (organizational sources vary by company—use your EA standards).  
- *Team Topologies* (Skelton & Pais) — capability alignment with team types.  
- DDD materials for **inside** each capability slice (Evans, Vernon).  

---

## 11. Nike Confluence pointers (internal)

- [Technical Design: Capability Driven Folder Structure](https://confluence.nike.com/pages/viewpage.action?pageId=1416270749) (CPI)  
- [Domain Driven Design and Capabilities for Product Creation](https://confluence.nike.com/pages/viewpage.action?pageId=284652437) (MTP) — links capability analysis with domain modeling themes  
- [CP&I Architecture - FY26 Goal candidates - Search](https://confluence.nike.com/pages/viewpage.action?pageId=1284478534) (CPI) — example language tying search capability to UX-driven APIs  

---

## 12. One-page summary

**Capability-driven design** helps **enterprises** invest and **structure platforms** around **durable business abilities** and **coherent API products**. **DDD** helps **teams** keep **models and boundaries** correct **inside** those abilities. Staff engineers need **both lenses**: capabilities for **portfolio truth**, DDD for **semantic truth**—and explicit **mapping** between them.

---

*Document purpose: give staff engineers vocabulary and patterns for capability-based platform and API design, and clear differentiation from DDD and project-only planning.*
