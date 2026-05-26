# Domain-Driven Design (DDD) — Staff Engineer Guide

**Audience:** Staff+ engineers shaping systems at organizational or industry scale.  
**Scope:** Strategic and tactical DDD, API design at context boundaries, tradeoffs, and how DDD differs from common alternatives.

This version uses **plain language first**, then ties back to the usual DDD terms.

---

## 1. Objective (plain English)

**Goal:** Build software so that **names, rules, and team boundaries** match how the business really works. That way:

- Teams don’t step on each other’s meaning for the same word.
- Big changes stay **local** where possible.
- You can explain behavior to a product or ops partner without translating through the database.

**What often breaks at scale:**

- The **same word, two meanings** (e.g. “Material” in design vs in a factory BOM)—systems look integrated but silently misunderstand each other.
- **Rules that contradict** because every team added their own logic to one shared “thing.”
- Trying to **lock everything in one database transaction** across checkout, warehouse, and payment—slow, fragile, hard to reason about.

DDD is **not** “microservices,” **not** “always event sourcing,” and **not** “every row is an entity.” It is **deliberate modeling and drawing boundaries**.

---

## 2. Plain language: terms that confuse people

### 2.1 “Rules that must always stay true” (DDD: *invariants*)

**Meaning:** Business rules that should **never** be broken inside a given model.

**Tiny example — shopping cart:**

- Rule: “Quantity is never negative.”
- Rule: “You can’t checkout with an empty cart.”

If one API allows negative quantity and another doesn’t, those APIs **don’t share the same model**—they **disagree on the rules** (DDD: *disagree on invariants*).

### 2.2 “Same word, different meaning” (DDD: *accidental homonyms*)

**Homonym** = same word, different meaning (like “bank” river vs money).

**Example — “Material”:**

- **Design / PLM:** “Material” = style substance (fabric, leather, what designers specify).
- **Manufacturing:** “Material” = plant stock item (SKU tied to a site, MRP, shelf life).

Both say “material,” but **identity, lifecycle, and rules differ**. If two services both expose `/materials/{id}` but mean different things, that is a **naming accident**—not one shared concept (DDD: *accidental homonyms*).

**Fix:** use **different names** in APIs where meanings differ, e.g. `DesignMaterial`, `PlantMaterial`, or separate base paths `/plm/...` vs `/erp/...`, **or** one well-owned **translation layer** at the boundary (see ACL below).

### 2.3 “Shared vocabulary in one slice” (*ubiquitous language*)

Inside **one** bounded area, everyone (PM, designer, engineer) agrees: **this term = this meaning**.

Example: In **checkout**, “Order” means “customer commitment we are trying to fulfill”—not “warehouse pick wave.”

### 2.4 “One model fits here; don’t assume it fits there” (*bounded context*)

A **bounded context** is a place where **one consistent model** applies. Outside that line, another team may use the **same English word** with a **different model**.

---

## 3. How to find the business domain and segregate slices (practical playbook)

When everyone says **“material domain”** but means **material**, **supplied material**, **vendor material**, **plant material**, it feels chaotic. Use this playbook to agree on **one umbrella** and **named slices** instead of one overloaded word.

### 3.1 How do you get the “business domain”?

The **business domain** is the **whole problem the company is paying the program to solve**—not a database, not one microservice, not one team’s Jira board.

**Questions that work in workshops with PMs and SMEs:**

1. **What is the outcome in one sentence?**  
   e.g. *“We define and evolve what products and materials are before they’re made and sold.”* → umbrella is **product creation / PLM**.  
   e.g. *“We sell online and handle pay, ship, and support.”* → umbrella is **commerce / order-to-cash**.

2. **What does leadership say this org *owns end-to-end*?**  
   That charter is usually your **top-level domain** label.

3. **Where is the money, risk, or regulation?**  
   Those areas are often **core** subdomains—spend modeling effort there.

4. **What would still be true if we replaced our current apps?**  
   The stable answer is **domain**; the apps are implementations.

You **do not** discover the domain by counting tables or services. You discover it from **business intent** and **expert language**.

### 3.2 Why “material domain” confuses everyone

**“Material” names many different jobs:** definition (what it is), sourcing (who supplies it), usage on a structure (BOM), plant stock, compliance view, etc. Each has **different owners, lifecycles, and rules**.

When someone says **“the material domain,”** ask: **Which job do you mean?** If they need five minutes to explain, you need **separate bounded names**—not a bigger “material” monolith.

### 3.3 How to segregate: four tests (concrete)

Treat each candidate area as its **own bounded context** (and usually its **own write model / API owner**) when **vocabulary, write ownership, lifecycle, or consistency** do not line up:

| Test | Question | Material-flavored example |
|------|----------|---------------------------|
| **A. Vocabulary** | Same **nouns and rules** without “but in our team we mean…”? | **Supplied material** adds **supplier + commercial** meaning → usually **not** the same model as **material specification** alone. |
| **B. Owner of writes** | Who is **allowed to change the truth**? | Design owns spec; procurement owns supplier link; plant owns stock rules—**different write owners** → different contexts. |
| **C. Lifecycle** | Same **start / change / end** story? | Spec can be approved long before a **specific supplier** is chosen. |
| **D. Consistency** | Must these facts stay **atomically** true together? | “BOM references material id” and “supplier price” often **do not** need one giant transaction. |

**Rule of thumb:** If two groups would **fight in a meeting** over who is allowed to edit the same row, you probably have **two contexts** linked by **ids and contracts**, not one shared “material” service.

### 3.4 Naming: stop saying “domain” for every box

Use a **fixed pattern** in docs and APIs:

| Layer | Pattern | Example |
|-------|---------|--------|
| **Umbrella** | One phrase for the whole program | *Product creation (PLM)* |
| **Bounded slice** | **Role + concept**—not bare “Material” | *Material specification*, *Supplied / sourced material*, *Plant material*, *BOM / material usage* |
| **Integration** | **Stable id + event/API contract** | `materialSpecificationId` on BOM line, supplied-material record, etc. |

In HTTP APIs, prefer **explicit** paths or resource names (`/material-specifications`, `/supplied-materials`, `/products/.../bom`) instead of one `/materials` that means everything.

### 3.5 Mini example: material vs supplied material

- **Material specification** (*definition context*): *What* the material is—attributes, approvals, revisions. Truth owned by **design / engineering / PLM spec** side.  
- **Supplied material** (*sourcing context*): Binds that spec (or article) to **supplier**, commercial data, lead times. Truth owned by **procurement / supply**.

**Link between them:** supplied material carries **`materialSpecificationId`** (or your platform’s equivalent)—**two contexts, one linking id** (same idea as BOM + material in **§5.6**).

### 3.6 What to produce from a workshop (so confusion stops)

Aim for a **one-pager** everyone can point to:

1. **One sentence** — the top-level business domain.  
2. **A table** — columns: *bounded context name*, *what noun it owns*, *who owns writes*, *example API or package boundary*.  
3. **Explicit links** — “Context B references Context A with field X”—no anonymous “material.”

Use that page as the **agreed vocabulary**; diagrams and services should **match** it.

---

## 4. Industry-scale example: order fulfillment

### Scenario: retail / marketplace

**Different concerns:**

- **Checkout:** customer promise, fraud, promotions.
- **Warehouse:** physical pick, ship, damage, partials.
- **Payments:** auth, capture, refunds—regulated, retries, idempotency.
- **Support:** cases, returns, goodwill—not the same as “edit checkout order.”

**Aren’t checkout, warehouse, payments, and support all “domains”?**

Yes—in **everyday language** people call each one a “domain” (“the payments domain,” “the fulfillment domain”). That is reasonable.

In **DDD vocabulary** it helps to be a bit more precise so the words don’t pile up:

| Level | What to call it here | Example |
|--------|----------------------|---------|
| **One big domain** | The overall problem you’re in | **Retail / marketplace commerce** (sell, pay, fulfill, support)—one umbrella. |
| **Areas inside it** | Often **subdomains** | Checkout, warehouse, payments, support are **subdomains** of that bigger domain. |
| **Where one model fits** | **Bounded context** | Frequently **one bounded context per subdomain** here, because **language and rules differ** (e.g. “order” at checkout vs “shipment” in the warehouse). |

So: **they are all part of the same top-level domain**, and each line is a **major concern** that DDD usually treats as its own **subdomain** and often its own **bounded context**. The earlier list was not saying “only one of these is the domain”—it was listing **different slices** that need **separate models**, not one merged “Order” blob.

**Without boundaries:**

- One giant `orders` table and one “Order” API: every team adds fields; **rules fight each other**; “cancel order” means different things in each department.
- Huge distributed transactions “because it’s one order.”

**With DDD (strategic):**

- **Several bounded contexts**, each with its own words and rules where needed.
- **Consistency** where the **business** actually needs it (e.g. payment vs pick), not everywhere at once.
- **Clear integration** between contexts (events, stable APIs, translation layers).

---

## 5. Worked example: Nike Flex / PLM-style “Material” (many things connected)

*Illustrative pattern for product creation / PLM—not a claim about one specific Nike schema name.*

In PLM, **many concepts plug into “material”**: substance library, colorways, supplier specs, compliance (restricted substances), where-used in BOMs, costing snapshots, regional approvals. Everything **connects**, but **not everything should be one model or one API**.

### 5.1 Step 1 — Name the big area (*domain*)

Ask: “What problem space are we in?”

**Example:** **Product creation / PLM** (how we define what a product is before or while it is made and sold).

That is the **domain** in the large sense: the whole messy problem family.

### 5.2 Step 2 — Split the problem into “themes” (*subdomains*)

Subdomains are **areas of the problem**, not org charts. Classify them:

| Type | Question | PLM-style examples (illustrative) |
|------|-----------|-----------------------------------|
| **Core** | Where do we win or differentiate? | How we define and evolve **product + material** truth for Nike; speed and quality of creation. |
| **Supporting** | Needed, but not unique | Workflow tasks, generic approvals, some reporting. |
| **Generic** | Commodity | Identity (SSO), email, generic file storage—**buy or share**, don’t custom-build for fun. |

**Staff move:** invest modeling time in **core**; integrate **generic**; keep **supporting** “good enough.”

### 5.3 Step 3 — Find where the **model must change** (*bounded contexts*)

Ask, for each cluster of features:

1. **Who owns the truth?** (one team’s system of record.)
2. **Do the words and rules stay the same** end-to-end? If **no** → different context.
3. **What must update together in one go?** (candidate for one **aggregate** / one transaction—see tactical section.)

**PLM-style splits that are *common* in industry (your names may differ):**

| Bounded context (example name) | Owns | Different “Material” meaning? |
|--------------------------------|------|-------------------------------|
| **Material definition** | What designers/engineers mean by a material: family, attributes, test data hooks | **Design material** identity |
| **Color / appearance** | Palettes, color naming, approvals tied to appearance | Often **separate language** from “base material” |
| **Sourcing / supplier** | Who supplies what, lead times, quotes | **Supplier material** ≠ design-only view |
| **Compliance** | Restricted substances, regions, certificates | Rules and **readiness** are their own world |
| **BOM / product structure** | Where-used, alternates, effectivity | **Usage** of a material, not the material’s full definition |
| **Manufacturing / plant** | What the factory orders and consumes | **Plant material** / SKU at a site |

These areas **link** to each other (IDs, events, APIs), but **collapsing** them into one “Material” aggregate usually creates **slow writes, team fights, and unclear ownership**.

### 5.4 Step 4 — Draw APIs that match boundaries

**Principle:** Public APIs should sound like **that context’s** language and **that team’s** promises—not expose every internal table.

**Example API shapes (illustrative):**

- **Material definition context**  
  - `GET /material-specifications/{id}`  
  - `PATCH /material-specifications/{id}/attributes` (rules about what can change together live **here**)

- **BOM / structure context**  
  - `GET /products/{productId}/bom`  
  - `POST /products/{productId}/bom/lines` (references material **by stable id** from definition context)

- **Compliance context**  
  - `GET /material-specifications/{id}/compliance-status` **or** compliance listens to events and exposes `GET /compliance/substances/...`  
  - Avoid forcing compliance rules into every unrelated CRUD if that team owns certification logic.

- **“Give me everything for a screen” (read)**  
  - A **read** API or BFF can **combine** data for UX; that layer **does not** have to be the **system of record**. Writes still go to the **owning** context.

**Golden rule:** If two teams would **argue forever** about who breaks a rule, they probably need **separate write models** and a **clear link** (ID + contract), not one shared write API.

### 5.5 Quick checklist: “Is this the same bounded context?”

- Can **one product owner** describe the rules without saying “depends on five teams’ spreadsheets”?  
- Do updates **usually** belong to **one** backlog and **one** on-call rotation?  
- Would forcing **one** database transaction across both sides create **political** and **technical** pain?

Three “no” answers → strong hint you have **two contexts** and should integrate with **events or explicit APIs**, not one mega-aggregate.

### 5.6 Domain vs bounded context — and linking with IDs (BOM + material)

**They are not the same thing.**

| Term | Plain meaning |
|------|----------------|
| **Domain** | The **big** problem space you work in (e.g. *product creation / PLM*). |
| **Bounded context** | A **smaller slice** inside that world where **one model and one shared vocabulary** hold (e.g. *material definition*, *BOM / product structure*). |

In hallway talk people say **“the material domain.”** Often they mean **the material bounded context** (or the **material part** of the problem). That is fine verbally; for architecture, be precise: **domain = whole picture**, **context = a specific model boundary**.

**Your example — BOM context and material context:**

- **Material definition context** is usually the **owner of truth** for *what* a material is (attributes, approvals, revisions). It defines a **stable identifier** users and systems agree on, e.g. `materialSpecificationId` (exact name varies by system).
- **BOM / product structure context** **references** that id on each BOM line. Its job is **where-used, structure, effectivity, alternates**, not redefining the material from scratch.

So **yes:** the BOM side **stores or exposes a link** — typically **`materialSpecificationId` (foreign reference)** — not a second competing source of truth for the full material definition.

**What is OK:**

- BOM line holds **`materialSpecificationId`** + maybe **read-only copies** of a few fields (code, display name) for fast screens, updated by **events** or sync — as long as everyone agrees **edits to definition** still go through the **material** context.

**What to avoid:**

- BOM (or any consumer) keeping a **full, editable** duplicate of material master data. Then you have **two models** and **two truths**; the id alone does not fix that.

**Summary:** Bounded context **does not “become”** the domain — it **sits inside** it. Contexts **cooperate** using **stable ids**, **contracts** (APIs/events), and clear **ownership** of writes.

---

## 6. Strategic design (DDD names, plain explanations)

### 6.1 Ubiquitous language

Shared terms **inside one bounded context** between engineers and business partners.

**Practice:** small glossary per context; avoid useless names like `DataResponse` in external APIs.

### 6.2 Bounded context

A line around **one** consistent model. Outside, assumptions may fail.

**Note:** One context can be **multiple services** or **one modular monolith**—what matters is **shared meaning and ownership**, not box count.

### 6.3 Subdomains (core / supporting / generic)

See §5.2. Use this to **decide where to spend modeling energy**.

### 6.4 How contexts talk (*context mapping* — shortened)

| Pattern | Plain English |
|---------|----------------|
| **Partnership** | Two teams evolve two models together. |
| **Customer–supplier** | Upstream prioritizes downstream’s needs. |
| **Conformist** | Downstream takes upstream’s shape as-is (little leverage). |
| **Anti-corruption layer (ACL)** | A **translator** at the edge so foreign names/rules don’t infect your core model. |
| **Open host service** | A **stable, shared** API many consumers use (with versioning). |
| **Published language** | Agreed **event or schema** for handoffs (e.g. `MaterialDefinitionPublished`). |

---

## 7. Tactical design (building blocks)

Here **invariant** again means **“rules that must stay true”** for a cluster of data.

| Block | Plain English | Typical mistake |
|-------|----------------|-----------------|
| **Entity** | Thing with **identity** over time (this row = “that” material revision) | Giving everything an ID “because SQL” |
| **Value object** | Defined only by values (money amount + currency); often **immutable** | Passing raw `string` / `decimal` everywhere |
| **Aggregate** | **One** cluster that updates together; **one front door** (root) | One giant cluster owned by three teams |
| **Domain event** | “Something business-meaningful happened” (`MaterialApproved`) | `record_updated` with no meaning |
| **Repository** | How we **load/save** an aggregate without leaking SQL everywhere | ORM calls scattered in controllers |
| **Domain service** | Rule that doesn’t fit a single entity | “`MaterialService`” with 200 methods |
| **Factory** | Safe, consistent **creation** when birth is complicated | 20 optional constructor args |

**Rule of thumb:** If two pieces **don’t need to be instantly consistent**, they probably **shouldn’t live in one aggregate** (and maybe not one write transaction).

---

## 8. API design under DDD

### 8.1 APIs are **contracts of a context**

- Names and operations should match **that** context’s language.
- Prefer **verbs that match use cases** (`submitForComplianceReview`) over **CRUD mirrors** of every table—unless the job is truly “dumb storage.”

### 8.2 Heavy reads vs careful writes (*CQRS* — when people mention it)

- **Writes:** enforce **rules** (invariants).
- **Reads:** often **denormalized** or **joined for screens**; may lag slightly.

**Symptom CQRS might help:** GET needs endless joins and breaks constantly; POST has real rules.

**Cost:** more pipelines and operational story—use **where** reads hurt most.

### 8.3 Cross-context communication (preference order—depends on case)

1. **Events** + clear payload contract (loose coupling).
2. **Stable internal API** with versioning.
3. **Sync calls** when latency and failure budgets allow—use a **translator (ACL)** if their words differ from yours.

### 8.4 Versioning

- Prefer **adding** fields over changing meaning.
- **Behavior** changes (same field, new rule) can break clients even if JSON “shape” looks the same.

### 8.5 Short example: checkout vs warehouse (APIs)

- **Checkout:** `POST /checkout-sessions/{id}/submit` → customer-facing reference; emits `OrderPlaced`.
- **Warehouse:** owns **Shipment**; reacts to `OrderPlaced`; does **not** pretend its shipment is the same aggregate as checkout’s order.
- **Support:** may work in **cases** and compensations, not “silent edit” of checkout.

---

## 9. How DDD differs from other approaches

| Approach | What it optimizes | Contrast with DDD |
|----------|-------------------|-------------------|
| **Database-first / CRUD APIs** | Tables and forms | Ignores **rules** and **word clashes** |
| **Three-tier without a domain layer** | Screens and SQL | Rules end up in random “services” |
| **Microservices by org chart** | Team boxes | Helps only if **meanings** align; else **distributed monolith** |
| **Event-driven** | Plumbing | **Fits DDD** if events are **business facts** with clear owners |
| **Capability-driven planning** | Business abilities portfolio | **Complements** DDD—see companion doc `capability-driven-design-staff-engineer-guide.md` |

**One line:** DDD is **getting boundaries and language right**; it doesn’t dictate how many servers you run.

---

## 10. Failure modes (plain)

1. **Diagram only** — pretty boxes; one shared database and one “Material” god table.
2. **No translators** — every team imports everyone else’s DTOs; meanings leak everywhere.
3. **Noise events** — floods of `updated` messages with no business meaning.
4. **Empty entities** — all logic in `*Service` classes.
5. **CQRS/events before boundaries** — can’t explain to the business **what is true when**.

---

## 11. When to invest

**Strong fit:** complex rules, many teams, long-lived system, high cost of mistakes (money, safety, regulations).

**Lighter touch:** small app, one team, simple CRUD, short life—still avoid **same path / two meanings**.

---

## 12. Further reading (classic)

- Eric Evans — *Domain-Driven Design*  
- Vaughn Vernon — *Implementing Domain-Driven Design*  
- Martin Fowler — *Patterns of Enterprise Application Architecture*  
- CQRS/event material — **after** boundaries are clear  

---

## 13. Nike Confluence pointers (internal)

- [Domain Driven Design in a Hurry](https://confluence.nike.com/pages/viewpage.action?pageId=1416271464) (CPI)  
- [Domain-Driven Design: Tactical Design Deep Dive](https://confluence.nike.com/pages/viewpage.action?pageId=1416271483) (CPI)  
- [DDD Definitions](https://confluence.nike.com/pages/viewpage.action?pageId=244926348) (NEA)  
- [Why Domain Driven Design? How does it get applied?](https://confluence.nike.com/pages/viewpage.action?pageId=243301342) (NEA)  
- [Domain Driven Design and Capabilities for Product Creation](https://confluence.nike.com/pages/viewpage.action?pageId=284652437) (MTP) — capability + domain framing for product data  

---

*Purpose: help staff engineers discover the business domain, segregate overlapping terms (e.g. material vs supplied material), and align APIs—plus a PLM/material worked pattern.*
