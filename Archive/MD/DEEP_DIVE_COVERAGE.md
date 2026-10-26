# Deep Dive Coverage Index

> **Purpose:** Navigate the Markdown curriculum (~83 topic files under `MD/`).  
> **PDFs:** None in repo; `.md` files are the source of truth (many cite Algoroq in footers).

---

## How depth is organized

| Tier | What it is | Where |
|------|------------|--------|
| **Topic guides** | Focused chapters + often `## FAANG Interview Deep Dive` | `caching-and-performance/`, `observability/`, `event-driven-architecture/`, etc. |
| **Compendiums** | Full interview banks (500–2,800 lines); use section headers as depth | `interview-questions/*.md` (17 files) |
| **HLD / LLD designs** | End-to-end designs with per-problem `### Interview Q&A` | `system-design-problems/*.md` (7 files) |
| **AWS track** | Cloud-native architecture (not separate labs) | `cloud-ops/*.md` |
| **Insider craft** | Cross-cutting “what seniors know” (one place only) | [`FAANG_INSIDER_KNOWLEDGE.md`](./FAANG_INSIDER_KNOWLEDGE.md) |

**Note:** Guides in `distributed-systems/`, `advanced-system-design/`, `performance-engineering/`, `databases-internals/`, `cloud-ops/`, and `sre-reliability/` rely on **in-body `Interview Q&A`** rather than a separate FAANG footer—that is intentional after cleanup of duplicate appendices.

---

## Study order by track

### Distributed + events
1. `distributed-systems/` (3) → `event-driven-architecture/` (6) → `reliability-and-resilience/` (6)

### Performance + caching
1. `performance-engineering/` (2) → `caching-and-performance/` (5)

### Data + databases
1. `databases-internals/` (3) → `database-comparisons/` (4) → `data-engineering/` (2)

### Observability + SRE
1. `observability/` (4) → `sre-reliability/` (2) → `reliability-and-resilience/03-slis-slos-error-budgets.md`

### HLD + patterns
1. `architecture-judgement/architecture-thinking.md` → `system-design-problems/` → `architectural-patterns/` → `advanced-system-design/`

### AI / LLM
1. **`ai-engineering-curriculum/`** (15 modules) — agent/RAG course track (LangChain → capstones)  
2. `llm-ops/` (2) → `interview-questions/ai-ml-and-llm.md` → `interview-questions/rag-and-vector-search.md`

### Cloud (AWS)
1. `cloud-ops/` (2) — primary AWS narrative; inline `### AWS service map` tables in topic guides where relevant

---

## Guides with full `## FAANG Interview Deep Dive` block

`architectural-patterns/01`–`06`, `architecture-judgement/` (except thin thinking guide), `caching-and-performance/01`–`05`, `data-engineering/*`, `database-comparisons/*`, `event-driven-architecture/01`–`06`, `large-scale-migrations/*`, `llm-ops/*`, `observability/01`–`04`, `reliability-and-resilience/01`–`06`

---

## How to study

1. Read the guide through **Key Takeaways** (and any **AWS service map** if present).
2. For FAANG-footer guides: do **Interview Q&A** without peeking at answers.
3. For compendiums / tier-B guides: use the file’s **Interview Q&A** sections the same way.
4. Skim [`FAANG_INSIDER_KNOWLEDGE.md`](./FAANG_INSIDER_KNOWLEDGE.md) for production pitfalls that tutorials skip.
5. Whiteboard **back-of-envelope** numbers on every design.

---

## Maintenance

- **Strip duplicate FAANG appendices:** `python3 scripts/strip_duplicate_faang.py` (only removes blocks marked capstone / “full study guide”).
- **Do not** re-run bulk auto-append scripts; add depth manually where a guide is thin.

---

## Restoring lost PDF context

1. Git history / backups on your machine for `*.pdf`.
2. `grep -r "Source: Algoroq" MD/` for chapter mapping.
