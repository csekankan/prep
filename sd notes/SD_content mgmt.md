# CMS System Design — End-to-End Architecture
### Financial Times · CNN · Wikipedia · NDTV Scale
### Frontend · Backend · Infrastructure · Monitoring

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Requirements — RADIO Pattern](#2-requirements--radio-pattern)
3. [Mental Model & Architecture Philosophy](#3-mental-model--architecture-philosophy)
4. [Headless CMS Layer](#4-headless-cms-layer)
5. [Concurrent Editing (OT in Practice)](#5-concurrent-editing-ot-in-practice)
6. [Versioning & Audit Trail](#6-versioning--audit-trail)
7. [Approval Workflow](#7-approval-workflow)
8. [Incremental Builds & 1-Hour SLA](#8-incremental-builds--1-hour-sla)
9. [Frontend Architecture (Next.js)](#9-frontend-architecture-nextjs)
10. [SEO & LLM Accessibility](#10-seo--llm-accessibility)
11. [Caching Strategies](#11-caching-strategies)
12. [Performance Optimizations](#12-performance-optimizations)
13. [Backend Architecture](#13-backend-architecture)
14. [Infrastructure & Hosting](#14-infrastructure--hosting)
15. [Monitoring, SLA & Error Handling](#15-monitoring-sla--error-handling)
16. [DDoS & Bot Handling](#16-ddos--bot-handling)
17. [Incident Triage](#17-incident-triage)
18. [Interview Cheatsheet](#18-interview-cheatsheet)

---

## 1. Problem Statement

```
Design a CMS with more than 10,000 pages.
Content is stored in Markdown.
Only a few people will edit it.

Requirements:
  ✓ Updated/new content available globally within 1 hour
  ✓ Handle 10 RPS average, 40 RPS max, 100 RPS burst (bots)
  ✓ SEO friendly
  ✓ Content accessible to LLMs for training
  ✓ Design frontend, backend, and infrastructure architecture

Follow-up questions:
  ✓ Monitoring for page crash, DDoS, error handling
  ✓ How severity is decided and configuration done
  ✓ How to triage for impacted user base
  ✓ Cache invalidation approaches

Constraints:
  ✗ Cannot contradict your own claims mid-interview
  ✓ System designed from frontend perspective, directing backend + infra
```

**Real-world equivalents:** Financial Times, CNN, Wikipedia, NDTV

---

## 2. Requirements — RADIO Pattern

RADIO = **R**esearch · **A**rchitecture · **D**ata Model · **I**nterface API · **O**ptimization

### Clarifying Questions to Ask Upfront

```
Content & Editors:
  Q: How many concurrent editors at peak?
  A: 3 to 4 (only a few editors)

  Q: Do editors collaborate on the same document simultaneously?
  A: Yes — real-time concurrent editing required

  Q: Is there an approval/review workflow?
  A: Yes — review before publishing for content sanitization

  Q: Schedule content for future publish dates?
  A: No

  Q: What media types — images, video, PDFs?
  A: Yes, all of the above

Content Structure:
  Q: All 10k pages same type or mixed?
  A: Mixture (articles, product pages, landing pages, FAQs)

  Q: Localized / multilingual?
  A: Yes

  Q: Who controls page templates — editors or developers?
  A: Editors, but single template layout for now

Access Control:
  Q: Flat team or hierarchical?
  A: Hierarchical (junior/senior/admin)

  Q: Some editors only access certain sections?
  A: Yes — section-based access control required
```

### Why These Questions Matter

```
Without answers:                   With answers:
  Pick any CMS                       Must support concurrent editing → Sanity
  Simple deploy pipeline             Must have approval workflow → role system
  Basic cache                        Multilingual → i18n routing, hreflang tags
  No auth                            Hierarchical access → RBAC in CMS
```

---

## 3. Mental Model & Architecture Philosophy

### Product-First, Not Engineering-First

> **Never design for technical users. Design for non-technical users.**
> As a frontend engineer, it is your responsibility to give the best
> user experience.

**Engineering-first (wrong approach):**

```
Tempting idea: Git-based CMS
  Editors commit Markdown to Git
  GitHub Actions converts to HTML
  Deploy to CDN

Pros:
  ✓ Versioning via Git
  ✓ CI/CD via GitHub Actions
  ✓ Markdown → HTML pipeline simple

Cons:
  ✗ Concurrent editing impossible
  ✗ Only technical people can edit
  ✗ Non-technical editors cannot use it
  → Works for internal wikis, NOT for news publishing platforms
```

**Product-first (correct approach):**

```
Editor experience = Google Docs feel
  Rich text, image upload, drag and drop
  Never see Markdown, JSON, or technical formats

"Publish once, serve everywhere" system
  Optimize heavily for reads
  Limited editors for writing
  By the time a user requests a page:
    - No database query
    - No server rendering
    - Just a file served from 200ms away
```

### High-Level Flow

```
┌──────────────┐     draft      ┌─────────────┐   webhook   ┌─────────────┐
│   Editor     │ ─────────────► │  Headless   │ ──────────► │   Build     │
│  (Sanity UI) │                │    CMS      │             │  Pipeline   │
└──────────────┘                └─────────────┘             └──────┬──────┘
                                      │                            │
                                  review                    regenerate HTML
                                      │                            │
                                      ▼                            ▼
                               ┌─────────────┐             ┌─────────────┐
                               │   Senior    │             │   Purge     │
                               │  Approves   │             │    CDN      │
                               └─────────────┘             └──────┬──────┘
                                                                   │
                                                                   ▼
                                                          ┌─────────────────┐
                                                          │  User requests  │
                                                          │  fresh page     │
                                                          │  from CDN edge  │
                                                          └─────────────────┘
```

### Detailed System Layers

```
┌────────────────────────────────────────────────────────────────────┐
│  Layer 1 — Content Authoring                                       │
│  Headless CMS (Sanity) + OT for concurrent editing                 │
│  Draft → Review → Publish workflow                                 │
│  Markdown storage + versioning in DB                               │
├────────────────────────────────────────────────────────────────────┤
│  Layer 2 — Build & Deploy Pipeline                                 │
│  Webhook → Next.js ISR revalidation → CDN cache purge              │
│  Full rebuild nightly, incremental per publish                     │
├────────────────────────────────────────────────────────────────────┤
│  Layer 3 — Frontend Delivery                                       │
│  Next.js SSG → pre-rendered HTML at CDN edge                       │
│  Service Worker for offline, lazy loading, responsive images       │
├────────────────────────────────────────────────────────────────────┤
│  Layer 4 — CDN & Edge                                              │
│  Cloudflare 200+ PoPs, DDoS protection, cache at edge              │
│  Rate limiting, bot management, WAF rules                          │
├────────────────────────────────────────────────────────────────────┤
│  Layer 5 — Observability                                           │
│  Sentry (app) + Datadog (infra) + Cloudflare (CDN) + Checkly      │
│  PagerDuty for on-call routing                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Headless CMS Layer

### Editor Experience Requirements

```
✓ Rich text editing (bold, italic, headings, tables)
✓ Image upload with drag and drop
✓ Concurrent editing (multiple editors in same doc)
✓ Version history with diff view
✓ Approval workflow (draft → review → published)
✓ Role-based access control
✓ Slack/email notifications
✓ Stores content as Markdown
```

### CMS Comparison

| CMS | Concurrent Editing | Versioning | Self-hosted | Why / Why Not |
|---|---|---|---|---|
| **Contentful** | Yes, with conflict detection | Full history + who changed what | No (SaaS) | Best-in-class editor UX, expensive at scale |
| **Sanity** | Yes, real-time multiplayer (like Figma) | Full audit log | No (SaaS) | Best for concurrent editing specifically |
| **Strapi** | Limited | Yes | Yes | Good if you want control over infra |
| **Payload CMS** | No (last-write-wins) | Yes (via plugins) | Yes | Code-first, great DX for devs, not editors |
| **Directus** | No | Yes | Yes | More of a data platform than a CMS |

### Why Sanity for This Use Case

```
Concurrent editing → first-class feature, not an afterthought
  Multiple editors in same document simultaneously
  See each other's cursors — exactly like Google Docs
  Technically hard to build — Sanity solves it natively

OT (Operational Transformation) under the hood:
  Same technique as Google Docs
  Every keystroke = operation broadcast to all clients + server
  Server merges operations in order → no work is lost

Practical editor experience:
  ✓ Presence indicators (avatars) showing who else is editing
  ✓ Real-time changes appearing as others type
  ✓ Lock on certain field types (slug) to prevent conflicts
  ✓ Warning if editing a document someone just published
```

---

## 5. Concurrent Editing (OT in Practice)

### The Problem

```
Editor A types "Hello" at position 0
Editor B types "World" at position 0 simultaneously

Without OT:  Last write wins → "Hello" is lost ✗
With OT:     Server sees both operations
             Transforms them relative to each other
             → "HelloWorld" or "WorldHello" (timestamp decides)
             Both edits preserved ✓
```

### How OT Works (Simplified)

```
State: "ab"

Alice: insert('c', pos=2)   baseRevision=0
Bob:   insert('d', pos=0)   baseRevision=0

Server receives Alice first:
  Applies Alice → "abc"  revision=1

Server transforms Bob against Alice:
  Bob wants: insert('d', pos=0)
  Alice inserted at pos=2 — Bob's pos=0 is BEFORE pos=2 → unchanged
  Applies Bob → "dabc"  revision=2

Clients converge: "dabc" ✓
```

### OT Transform Function Rules

```python
transform_insert_insert(op1, op2):
  if op2.pos < op1.pos:   return Insert(op1.pos + 1, op1.char)  # shift right
  if op2.pos == op1.pos:  tie-break by client_id
  else:                   return op1  # no change

transform_insert_delete(op1, op2):
  if op2.pos < op1.pos:   return Insert(op1.pos - 1, op1.char)  # shift left
  else:                   return op1

transform_delete_insert(op1, op2):
  if op2.pos <= op1.pos:  return Delete(op1.pos + 1)  # shift right
  else:                   return op1

transform_delete_delete(op1, op2):
  if op2.pos < op1.pos:   return Delete(op1.pos - 1)  # shift left
  if op2.pos == op1.pos:  return NoOp()  # same char, nothing to do
  else:                   return op1
```

> For a deep dive on OT vs CRDT, see `COLLABORATIVE_TEXT_EDITOR_DESIGN.md`

---

## 6. Versioning & Audit Trail

### What the Version System Must Answer

```
✓ What changed  (diff of content)
✓ Who changed it (editor identity)
✓ When          (timestamp)
✓ Why           (optional: publish notes/comments)
✓ Rollback to any previous version
```

### Editor View of Version History

```
v12 — Published by Sarah Chen, 14 Feb 2026 11:32am  ← current
v11 — Edited by Rahul Mehta, 14 Feb 2026 10:01am
v10 — Published by Sarah Chen, 13 Feb 2026 4:45pm
v9  — Edited by Rahul Mehta, 13 Feb 2026 2:30pm
...

Click any version → see GitHub-style diff in readable prose
One-click restore → no technical knowledge needed
Auto-save on every change → nothing is ever lost
```

### Files vs Database for Versions

**Why files fail at scale:**

```
Naive approach:
  /content/blog/my-post/
    v1_2026-01-01_sarah.md
    v2_2026-01-15_rahul.md
    v3_2026-02-01_sarah.md   ← current

10k pages × 20 versions = 200k files

Problems:
  ✗ File system lookups become slow at this scale
  ✗ No atomic writes — failed save leaves corrupt state
  ✗ Race conditions with concurrent editors
  ✗ No metadata (who changed, approval status) without separate manifest
  ✗ Diffing and restore logic is entirely your problem to build

Rule: Files for versioning only if Git IS your versioning layer.
      For human editors in a CMS → always use a database.
```

### Database Versioning — Two Flavors

**Flavor A: Full Snapshots (Recommended)**

```sql
-- content_versions table
id          | document_id | content (JSON) | editor  | status
uuid-v1     | post-abc    | {full doc}     | sarah   | published
uuid-v2     | post-abc    | {full doc}     | rahul   | draft
uuid-v3     | post-abc    | {full doc}     | sarah   | published
```

```
Pros:
  ✓ Restore = single row fetch, no reconstruction
  ✓ Simple to reason about
  ✓ Metadata attached to every row

Cons:
  50KB article × 50 versions = 2.5MB per article
  At 10k pages → ~25GB total
  Cost: ~$2–5/month in managed Postgres — NOT the bottleneck
```

**Flavor B: Delta / Diff Storage**

```
version 1: {full document}   ← base
version 2: [{op: "replace", path: "/title", value: "New Title"}]
version 3: [{op: "replace", path: "/body/2", value: "Updated para"}]

Pros:  Very storage efficient
Cons:
  ✗ Reconstruct version 50 = apply 1 through 49 in sequence
  ✗ If any delta corrupt → all subsequent versions broken
  ✗ Fragile by design — avoid for data integrity
```

### The Hybrid Approach (What to Actually Build)

```
Every save    → full snapshot row in DB
Current draft → separate "working" row, not versioned yet
On publish    → working row promoted to published snapshot
Older than 12 months + no activity → archived to S3 cold storage
Always keep last N versions in hot DB

Key insight:
  Diffs are for DISPLAY (pre-computed, stored separately)
  Full snapshots are for RESTORE (never depend on diffs for integrity)
```

### Database Schema

```sql
-- Live current state of each document
CREATE TABLE documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug              TEXT UNIQUE NOT NULL,
    type              TEXT NOT NULL,
    current_version_id UUID,
    locale            TEXT DEFAULT 'en',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Every version ever saved
CREATE TABLE document_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id),
    content         JSONB NOT NULL,
    editor_id       UUID NOT NULL,
    editor_name     TEXT NOT NULL,
    status          TEXT NOT NULL,       -- 'draft' | 'in_review' | 'published' | 'archived'
    change_summary  TEXT,                -- "Updated intro paragraph"
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    published_at    TIMESTAMPTZ,
    approved_by     UUID REFERENCES users(id)
);

-- Pre-computed diffs — for display only, NOT for restore
CREATE TABLE document_diffs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_version_id UUID REFERENCES document_versions(id),
    to_version_id   UUID REFERENCES document_versions(id),
    diff            JSONB NOT NULL
);

-- Media assets — stored by reference, NOT by value
-- Images, videos, PDFs → S3 / Cloudflare R2
-- Database stores URL + metadata only
CREATE TABLE media_assets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    url         TEXT NOT NULL,
    type        TEXT NOT NULL,     -- 'image' | 'video' | 'pdf'
    alt_text    TEXT,
    width       INTEGER,
    height      INTEGER,
    size_bytes  INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

> **Rule:** Never store a 4MB image as a JSONB blob in Postgres.
> Images, videos, PDFs → object storage (S3, Cloudflare R2).
> Database stores the URL and metadata only.

---

## 7. Approval Workflow

### Role Hierarchy

```
Junior Editor  → can only create drafts, cannot publish
Senior Editor  → can approve and publish
Admin          → can do everything (unpublish, delete, manage users)
```

### Draft → Review → Published Flow

```
┌─────────────┐   submits    ┌──────────────┐   approves   ┌─────────────┐
│   Junior    │ ──────────► │   In Review   │ ──────────► │  Published  │
│   Editor    │              │              │              │  (live)     │
└─────────────┘              └──────────────┘              └─────────────┘
                                    │                            │
                              email + Slack                triggers
                              notification                 webhook →
                              to Senior Editor             build pipeline

Rejection flow:
  Senior rejects with comment → back to Draft + notification to Junior
  Rejection reason stored in audit log

Audit log entry:
  { action: "approved", by: "sarah.chen", at: "2026-02-14T11:32:00Z",
    document: "article-abc123", from_version: "v11", to_version: "v12" }
```

---

## 8. Incremental Builds & 1-Hour SLA

### Why Full Rebuilds Fail

```
10k pages full rebuild → 30–40 minutes
Content freshness SLA  → 1 hour

Remaining budget after full rebuild: 20–30 minutes
CDN propagation alone: 3–5 minutes
Not enough margin → incremental builds required
```

### Webhook-Triggered Incremental Build

When an article is published, CMS fires a webhook:

```json
{
  "documentId": "article-abc123",
  "slug": "/blog/my-updated-post",
  "updatedAt": "2026-02-14T11:32:00Z",
  "editor": "sarah.chen@company.com"
}
```

Build pipeline on receiving webhook:

```
1. Receive webhook
2. Fetch ONLY that document from CMS API
3. Run Next.js ISR revalidation for that specific path
4. Call Cloudflare purge API for that URL
5. CDN re-fetches fresh page from origin

Total time: 2–4 minutes per page ✓
```

```typescript
// pages/api/revalidate.ts — Next.js on-demand revalidation endpoint
export default async function handler(req, res) {
    const { secret, slug } = req.query;

    if (secret !== process.env.REVALIDATE_SECRET) {
        return res.status(401).json({ message: 'Invalid token' });
    }

    await res.revalidate(`/${slug}`);

    await fetch(
        `https://api.cloudflare.com/client/v4/zones/${process.env.CF_ZONE_ID}/purge_cache`,
        {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.CF_API_TOKEN}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                files: [`https://yourdomain.com/${slug}`]
            }),
        }
    );

    return res.json({ revalidated: true });
}
```

### Content Freshness Timeline

```
Editor publishes             →  0 min
Webhook fires                →  0–2 min   (webhook latency)
ISR revalidation triggers    →  +1 min
Next.js page regenerated     →  +2–4 min  (just one page, not all 10k)
Cloudflare purge API called  →  +1 min
CDN propagates globally      →  +3–5 min
Content live everywhere      →  ~10–15 min total  ✓ well within 1-hour SLA
```

---

## 9. Frontend Architecture (Next.js)

### Why Next.js

```
✓ generateStaticParams() pre-renders all 10k pages at build time
✓ Each page = plain HTML file on CDN → zero compute at request time
✓ ISR (Incremental Static Regeneration) for pages that update
✓ On-demand revalidation API for webhook-triggered rebuilds
✓ Built-in image optimization (AVIF/WebP)
✓ Automatic code splitting
```

### Project Structure

```
src/
├── app/
│   ├── [slug]/
│   │   └── page.tsx          # Dynamic routes for all CMS pages
│   ├── layout.tsx             # Root layout (nav, footer)
│   ├── sitemap.ts             # Auto-generated sitemap.xml
│   └── robots.ts              # robots.txt generation
├── content/                   # Markdown pulled from CMS at build time
├── lib/
│   ├── cms.ts                 # CMS API client (Sanity SDK)
│   ├── mdx.ts                 # Markdown parser + sanitizer
│   ├── search-index.ts        # Build-time search index generation
│   └── structured-data.ts     # JSON-LD schema generation
└── components/
    ├── MDXRenderer.tsx         # Renders sanitized HTML from Markdown
    ├── TableOfContents.tsx     # Auto-generated from headings
    ├── ErrorBoundary.tsx       # Catches React crashes per section
    └── SkeletonLoader.tsx      # Perceived performance
```

### Static Generation at Build Time

```typescript
// app/[slug]/page.tsx

export async function generateStaticParams() {
    const slugs = await getAllSlugs();
    return slugs.map((slug) => ({ slug }));
}

export default async function ArticlePage({ params }) {
    const post = await getContent(params.slug);
    return (
        <article>
            <MDXRenderer content={post.content} />
            <TableOfContents headings={post.headings} />
        </article>
    );
}

export const revalidate = 300; // fallback: revalidate every 5 min
```

### Multilingual Routing

```typescript
// middleware.ts — detect locale, redirect
export function middleware(request: NextRequest) {
    const locale = detectLocale(request);
    const { pathname } = request.nextUrl;

    if (!pathname.startsWith(`/${locale}`)) {
        return NextResponse.redirect(
            new URL(`/${locale}${pathname}`, request.url)
        );
    }
}

// Generates paths for ALL locales × ALL slugs
export async function generateStaticParams() {
    const locales = ['en', 'hi', 'de', 'fr'];
    const slugs = await getAllSlugs();
    return locales.flatMap(locale =>
        slugs.map(slug => ({ locale, slug }))
    );
}
```

---

## 10. SEO & LLM Accessibility

### Meta Tags & Open Graph (Auto-generated)

```typescript
export async function generateMetadata({ params }) {
    const post = await getContent(params.slug);
    return {
        title:       post.frontmatter.title,
        description: post.frontmatter.description,
        openGraph: {
            title:         post.frontmatter.title,
            description:   post.frontmatter.description,
            type:          'article',
            publishedTime: post.frontmatter.publishedAt,
            authors:       [post.frontmatter.author],
            images:        [{ url: post.frontmatter.coverImage }],
        },
        alternates: {
            canonical: `https://yourdomain.com/${params.slug}`,
            languages: {
                'en': `/en/${params.slug}`,
                'hi': `/hi/${params.slug}`,
            },
        },
    };
}
```

### Structured Data (JSON-LD) for Google & LLMs

```typescript
export function generateArticleSchema(post) {
    return {
        '@context':    'https://schema.org',
        '@type':       'Article',
        headline:      post.title,
        description:   post.description,
        datePublished: post.publishedAt,
        dateModified:  post.updatedAt,
        author: {
            '@type': 'Person',
            name:    post.author.name,
            url:     post.author.profileUrl,
        },
        publisher: {
            '@type': 'Organization',
            name:    'Your Company',
            logo: { '@type': 'ImageObject', url: '/logo.png' },
        },
        image:           post.coverImage,
        url:             `https://yourdomain.com/${post.slug}`,
        mainEntityOfPage: `https://yourdomain.com/${post.slug}`,
    };
}
```

### LLM Accessibility Best Practices

```
Clean semantic HTML:
  ✓ No JS-dependent rendering for content
  ✓ Full article text in HTML at request time (SSG, not CSR)
  ✓ Proper heading hierarchy (h1 → h2 → h3)

robots.txt — allow reputable AI crawlers:
  User-agent: GPTBot
  Allow: /

  User-agent: ClaudeBot
  Allow: /

  User-agent: *
  Disallow: /admin/
  Disallow: /api/

/llms.txt file (emerging standard):
  Lists all content URLs with brief description
  Helps LLMs discover and prioritize content

/raw endpoint for pure Markdown:
  GET /blog/my-post/raw → returns raw Markdown
  LLMs prefer clean text over parsed HTML

sitemap.xml with <lastmod> dates:
  Crawlers prioritize fresh content
  Auto-generated from CMS updatedAt timestamps
```

---

## 11. Caching Strategies

### Overview: Six Approaches

```
Each serves a different invalidation need.

Approach 1: Purge by URL          → surgical, one page
Approach 2: Purge by Cache Tag    → relational content
Approach 3: Wildcard/Prefix Purge → section-wide changes
Approach 4: Full Cache Purge      → nuclear option
Approach 5: Versioned URLs        → static assets (JS/CSS)
Approach 6: Stale-While-Revalidate → background freshness
```

### Approach 1: Purge by URL (Surgical)

```bash
# Cloudflare API — invalidate one specific page after edit
curl -X POST \
  "https://api.cloudflare.com/client/v4/zones/{zone}/purge_cache" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"files": ["https://yourdomain.com/blog/my-updated-post"]}'
```

```
Pros: Fast, targeted, no collateral disruption
Cons: Must know exact URLs to purge
Use for: Single-page content edits (triggered by webhook)
```

### Approach 2: Purge by Cache Tag (Relational Content)

```
Each response served with a header:
  Cache-Tag: post-123, author-jane, category-engineering

When Jane updates her bio:
  Purge tag: author-jane
  → Every page tagged with "author-jane" invalidated automatically
  → Article pages, author profile, category pages — all at once

Use for: Author updates, category renames, shared widget changes
```

```typescript
function getCacheTags(post) {
    return [
        `post-${post.id}`,
        `author-${post.author.id}`,
        `category-${post.category}`,
        `locale-${post.locale}`,
    ].join(', ');
}

res.setHeader('Cache-Tag', getCacheTags(post));
```

### Approach 3: Wildcard / Prefix Purge

```
Purge: /blog/*  → clears all blog pages
Purge: /docs/*  → clears all docs
Purge: /hi/*    → clears all Hindi locale pages

Use for:
  - Template / layout changes
  - Shared component updates (nav, footer)
  - Section-wide content policy changes
```

### Approach 4: Full Cache Purge (Last Resort)

```
When to use:
  - Major site redesign
  - Security vulnerability in cached content
  - CDN configuration change

Risk: All origin traffic spikes as CDN re-populates

Mitigation — Cache Warming Script:
  After purge, immediately crawl sitemap
  Pre-populate CDN before real users arrive
  Priority: homepage → top 100 pages by traffic → rest
```

```bash
# Cache warming: crawl sitemap in parallel after purge
curl -s https://yourdomain.com/sitemap.xml \
  | grep -oP '(?<=<loc>)[^<]+' \
  | xargs -P 20 -I{} curl -s -o /dev/null {}
```

### Approach 5: Versioned URLs / Cache Busting (Static Assets)

```
Build output with content hash in filename:
  main.a3f9c2.js
  styles.b8e1d4.css

Cache-Control: public, max-age=31536000, immutable
  → Cache forever (1 year)
  → Old URLs stay cached (existing users unaffected)
  → New hash = new URL = always fresh

Note: For JS/CSS/images — NOT for HTML pages
```

### Approach 6: Stale-While-Revalidate

```
Cache-Control: max-age=300, stale-while-revalidate=86400

Behaviour:
  Within 5 min:  serve from cache instantly
  After 5 min:   serve stale instantly + fetch fresh in background
  After 24 hours: must have fresh copy

Perfect for this CMS:
  1-hour staleness is acceptable (within SLA)
  User never waits for cache miss
  Content is eventually consistent
```

### Cache Headers Per Asset Type

```
HTML pages:       Cache-Control: public, max-age=300, stale-while-revalidate=3600
Images (hashed):  Cache-Control: public, max-age=31536000, immutable
JS/CSS (hashed):  Cache-Control: public, max-age=31536000, immutable
Fonts:            Cache-Control: public, max-age=31536000, immutable
API responses:    Cache-Control: private, max-age=60
```

### Recommended Combination

```
Static assets              → Versioned URLs (permanent cache)
Single page updated        → Purge by URL + cache tags
Template/layout changed    → Wildcard purge + cache warm
Author/category update     → Purge by cache tag
Emergency / all stale      → Full purge + immediate cache warming
```

---

## 12. Performance Optimizations

### The Core Problem

```
User in rural area on 2G requesting page with:
  - 4MB hero image
  - 3 embedded videos
  - 20 article images

Without optimization:
  30+ seconds to load
  Half-loaded on network drop
  Burns mobile data

With optimization:
  ~300KB instead of 8MB
  ~4 seconds on 3G
```

### Layer 1: CDN — Serve from Nearest Edge

```
User in Mumbai      → Cloudflare Mumbai PoP     (5ms latency)
User in rural MP    → Cloudflare Delhi PoP      (40ms latency)
User in Germany     → Cloudflare Frankfurt PoP  (3ms latency)

vs. serving from origin in US-East:
User in Mumbai      → 180ms latency
User in rural MP    → 220ms latency

Cloudflare:
  ✓ 200+ PoPs globally
  ✓ Cache invalidation API
  ✓ DDoS protection built in
  ✓ Workers for edge logic without cold starts
```

### Layer 2: Images — The Biggest Win

**Serve the right format:**

```
Browser supports AVIF? → serve .avif (50% smaller than JPEG)
Browser supports WebP? → serve .webp (30% smaller than JPEG)
Neither?               → serve .jpg (fallback)

Next.js <Image> handles this automatically
CDN converts on first request, caches converted version
```

**Serve the right size (responsive images):**

```html
<img
  srcset="
    /hero-400w.jpg  400w,
    /hero-800w.jpg  800w,
    /hero-1200w.jpg 1200w,
    /hero-2000w.jpg 2000w
  "
  sizes="
    (max-width: 480px)  400px,
    (max-width: 768px)  800px,
    (max-width: 1200px) 1200px,
    2000px
  "
  src="/hero-800w.jpg"
/>
<!-- 2000px hero at 4MB → 400px for mobile at 120KB = 33× reduction -->
```

**Network-adaptive image quality:**

```javascript
const connection = navigator.connection;
const quality = {
    'slow-2g': 40,
    '2g':      50,
    '3g':      65,
    '4g':      80,
    'wifi':    85,
}[connection?.effectiveType] ?? 75;

const imageUrl = `/cdn-cgi/image/quality=${quality},format=auto/${imagePath}`;
```

**Lazy loading with priority hints:**

```jsx
// Above the fold — load immediately, high priority
<Image src="/hero.jpg" priority fetchpriority="high" />

// Below the fold — defer until user scrolls near
<Image src="/article-image.jpg" loading="lazy" />
```

**Blur placeholder (LQIP — Low Quality Image Placeholder):**

```jsx
// At build time: generate 20×20px version (200 bytes) → base64
// Page renders instantly with blurred placeholder
// Full image fades in when loaded
// Layout never shifts (CLS = 0)
<Image
  src="/hero.jpg"
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,/9j/4AAQ..."
/>
```

### Layer 3: Video

**Poster + lazy load — zero bytes until user clicks play:**

```html
<video poster="/video-thumbnail.jpg" preload="none" loading="lazy">
  <source src="/video.av1.mp4" type="video/mp4; codecs=av1">
  <source src="/video.h264.mp4" type="video/mp4">
</video>
```

**Adaptive Bitrate Streaming (HLS) for long videos:**

```
Single 1080p MP4:  800MB download regardless of connection

HLS with ABR:
  Video split into 6-second chunks at multiple quality levels
  Player monitors network speed between chunks
  User on 2G  → 360p without buffering
  User on WiFi → 1080p
  Network drops → seamlessly drops to lower quality

AWS MediaConvert or Cloudflare Stream handles HLS packaging
Upload one master video → they produce quality ladder + chunks
```

**YouTube/Vimeo Facade (saves 500KB per page load):**

```jsx
const VideoFacade = ({ videoId }) => {
    const [activated, setActivated] = useState(false);

    if (!activated) return (
        <div onClick={() => setActivated(true)} style={{ cursor: 'pointer' }}>
            <img
                src={`https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`}
                alt="Video thumbnail"
            />
            <PlayButton />
        </div>
    );

    return <iframe src={`https://youtube.com/embed/${videoId}?autoplay=1`} />;
};
// Standard <iframe> loads ~500KB of YouTube JS immediately
// Facade: thumbnail + play button, load iframe on click
```

### Layer 4: HTML / CSS / JS Delivery

**Critical CSS inlining:**

```html
<head>
  <!-- Inline only CSS for above-the-fold (~10–15KB) -->
  <style>
    /* critical path CSS — header, hero, fonts, layout */
  </style>

  <!-- Load rest of CSS asynchronously — doesn't block render -->
  <link rel="stylesheet" href="/main.css" media="print" onload="this.media='all'">
</head>
```

**Resource hints:**

```html
<head>
  <link rel="dns-prefetch" href="//fonts.googleapis.com">
  <link rel="dns-prefetch" href="//cdn.yourdomain.com">
  <link rel="preconnect" href="https://cdn.yourdomain.com">
  <link rel="preload" href="/hero.jpg" as="image">
  <link rel="preload" href="/fonts/Inter.woff2" as="font" crossorigin>
</head>
```

**Font strategy:**

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter.woff2') format('woff2');
  font-display: swap;               /* System font first, swap when loaded */
  unicode-range: U+0000-00FF;       /* Only Latin characters — smaller file */
}
```

### Layer 5: Service Worker — Offline & Flaky Network

```javascript
// service-worker.js using Workbox

// HTML pages — StaleWhileRevalidate
workbox.routing.registerRoute(
    ({ request }) => request.destination === 'document',
    new workbox.strategies.StaleWhileRevalidate({ cacheName: 'pages-cache' })
);

// Images — CacheFirst with 30-day expiry
workbox.routing.registerRoute(
    ({ request }) => request.destination === 'image',
    new workbox.strategies.CacheFirst({
        cacheName: 'images-cache',
        plugins: [new workbox.expiration.ExpirationPlugin({
            maxEntries: 200,
            maxAgeSeconds: 30 * 24 * 60 * 60,
        })],
    })
);

// API calls — NetworkFirst with 3s timeout, fall back to cache
workbox.routing.registerRoute(
    ({ url }) => url.pathname.startsWith('/api/'),
    new workbox.strategies.NetworkFirst({
        cacheName: 'api-cache',
        networkTimeoutSeconds: 3,
    })
);

// Offline fallback page
workbox.precaching.precacheAndRoute([{ url: '/offline.html', revision: '1' }]);
workbox.routing.setCatchHandler(({ event }) => {
    if (event.request.destination === 'document') {
        return caches.match('/offline.html');
    }
});
```

**What this means for flaky networks:**

```
1. User visits on good connection → pages + images cached
2. Goes underground on metro → loses signal
3. Navigates to cached page → loads perfectly
4. Visits new page → friendly offline page (not browser error)
5. Signal returns → cache updates silently in background
```

### Layer 6: Perceived Performance

**Skeleton screens instead of spinners:**

```
Users perceive skeleton layouts as faster — page doesn't look empty.
Show the layout shape of content while it loads.
```

**Prefetch on hover — next page loads before click:**

```javascript
document.querySelectorAll('a[href^="/"]').forEach(link => {
    link.addEventListener('mouseenter', () => {
        const prefetch = document.createElement('link');
        prefetch.rel  = 'prefetch';
        prefetch.href = link.href;
        document.head.appendChild(prefetch);
    }, { once: true });
});
```

### End-to-End Request Journey (3G User in Rural Area)

```
1.  HTML served from Cloudflare edge 40ms away (not 200ms origin)
2.  Critical CSS inlined → page renders layout in ~100ms
3.  System font shows immediately (font-display: swap)
4.  Hero image: 400px WebP at quality=65 for 3G → 45KB not 4MB
5.  Below-fold images: not downloaded yet (lazy loading)
6.  Service worker activates, begins caching assets
7.  Network drops for 10 seconds
8.  User scrolls — cached images from previous visits load instantly
9.  Network returns → service worker syncs silently
10. Custom font swaps in — user barely notices
11. User hovers next link → prefetch starts
12. User clicks → page loads instantly from prefetch cache

Total data: ~300KB instead of 8MB
Load time on 3G: ~4 seconds instead of 30 seconds ✓
```

---

## 13. Backend Architecture

### API Layer

```
REST API (content delivery):
  GET  /api/documents/:slug        → fetch published document
  GET  /api/documents/:slug/raw    → fetch raw Markdown (for LLMs)
  GET  /api/search?q=              → full-text search
  POST /api/webhook/publish        → CMS webhook trigger

CMS API (internal, editor-facing):
  Managed by Sanity — all CRUD via Sanity SDK
  Protected by CMS auth, not exposed publicly

Webhook receiver (secured):
  POST /api/webhook/publish
  Headers: { X-Sanity-Webhook-Secret: env.WEBHOOK_SECRET }
  Body: { documentId, slug, updatedAt, editor }
  Action: trigger ISR revalidation + Cloudflare purge
```

### Search Architecture

```
For read-heavy CMS with 10k pages:

Option A — Algolia (hosted search):
  Build-time indexing: each page → { title, description, body, slug, tags }
  Search API call → Algolia (no origin load for search queries)
  Fast, managed, costs money at scale

Option B — Pagefind (static search, zero API cost):
  Runs at build time, generates search index as static files
  Ships to CDN, search runs entirely in browser
  No server needed for search — perfect for read-heavy CMS
```

### Build Pipeline

```
Trigger: CMS webhook (on publish) OR scheduled (nightly full rebuild)

Pipeline steps:
  1.  Receive webhook with { slug, documentId }
  2.  Validate webhook secret
  3.  Fetch document from Sanity API
  4.  Parse Markdown → HTML
  5.  Generate structured data (JSON-LD)
  6.  Generate meta tags
  7.  Call Next.js revalidatePath(slug)
  8.  Call Cloudflare purge API for that URL
  9.  Update search index for that document
  10. Post completion to Slack channel

Full rebuild (nightly at 2am UTC):
  generateStaticParams() fetches all slugs from CMS
  Builds all 10k pages in parallel
  ~15–25 min build time
  Deployed to Vercel / Netlify / self-hosted
```

---

## 14. Infrastructure & Hosting

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      GLOBAL INFRASTRUCTURE                        │
│                                                                   │
│  Editors                                                          │
│  └── Sanity Studio (SaaS) ─────────────────────────────────┐     │
│                                                            │     │
│  Webhook ──────────────────────────────────────────┐       │     │
│                                                    │       │     │
│                                                    ▼       ▼     │
│  GitHub ──► GitHub Actions (CI/CD)        Build Server           │
│             └── Build Next.js app   ◄─────(Vercel / self-host)   │
│             └── Run tests                         │              │
│             └── Deploy to origin                  │              │
│                                                   ▼              │
│                                          ┌─────────────┐         │
│                                          │   Origin    │         │
│                                          │  (Next.js   │         │
│                                          │   server)   │         │
│                                          └──────┬──────┘         │
│                                                 │                │
│                                    ┌────────────▼──────────┐     │
│                                    │   Cloudflare CDN      │     │
│                                    │   200+ PoPs globally  │     │
│                                    │   DDoS protection     │     │
│                                    │   Cache at edge       │     │
│                                    └───────────┬───────────┘     │
│                                                │                 │
│                           ┌────────────────────┼───────────────┐ │
│                        Mumbai              Delhi          Frankfurt│
│                        (5ms)               (40ms)          (3ms)  │
│                           └────────────────────┼───────────────┘ │
│                                                │                 │
│                                            End Users             │
└──────────────────────────────────────────────────────────────────┘
```

### Hosting Options

```
Option A: Vercel (Recommended for quick start)
  ✓ Native Next.js support
  ✓ ISR and on-demand revalidation out-of-box
  ✓ Automatic CDN at 100+ edge locations
  ✓ Preview deployments per branch
  ✗ Cost can be high at scale
  ✗ Vendor lock-in

Option B: Self-hosted on AWS/GCP
  ✓ Full control over infra
  ✓ Cost-efficient at high scale
  ✓ No vendor lock-in
  ✗ More DevOps overhead
  ✗ Must set up CDN, caching, CI/CD separately

Recommended combo:
  Vercel for Next.js origin
  + Cloudflare CDN in front (Vercel as upstream origin)
  + Cloudflare for WAF, DDoS, rate limiting, cache headers
```

### Rate Limiting Config

```
Traffic profile:
  Average: 10 RPS
  Peak:    40 RPS
  Burst:   100 RPS (bots)

Cloudflare rate limiting rules:
  Known bot user-agents:   100 RPS token bucket, then 429
  Regular users:           40 RPS per IP, sliding window
  Editor IPs (allowlist):  no rate limit
  DDoS threshold:          auto-challenge at 150+ RPS from single IP
  ASN burst:               Under Attack mode at 500+ RPS from single ASN
```

---

## 15. Monitoring, SLA & Error Handling

### The Observability Stack (Four Layers)

```
Layer 1 — Application (JS errors, crashes, performance):
  Tool:   Sentry
  Covers: React crashes, unhandled exceptions, Core Web Vitals,
          performance traces, source maps

Layer 2 — Infrastructure (server health, build pipeline):
  Tool:   Datadog or Grafana Cloud
  Covers: Origin server CPU/memory, build pipeline duration,
          CMS API latency, database query times

Layer 3 — CDN (edge latency, cache, bots):
  Tool:   Cloudflare Analytics + Logpush → S3 → Grafana
  Covers: Cache hit rate, edge latency by PoP, bot traffic,
          DDoS signals, bandwidth usage

Layer 4 — Uptime / Synthetic:
  Tool:   Checkly or Better Uptime
  Covers: Real Chromium browser tests every 60s from multiple regions
          Alerts if page content changes unexpectedly

Alerting / On-call:
  Tool:   PagerDuty
  Routes: Alerts to correct person based on severity + schedule

Why each layer separately:
  Sentry   → TypeError in Munich
  CF       → 3,000 Munich requests hitting origin instead of cache
  Checkly  → /de/pricing returning 500
  Without all three → archaeology instead of debugging
```

### Page Crash Detection

**Client-side (React Error Boundaries):**

```jsx
class ErrorBoundary extends React.Component {
    componentDidCatch(error, info) {
        Sentry.captureException(error, {
            contexts: { react: { componentStack: info.componentStack } }
        });
    }

    render() {
        if (this.state.hasError) {
            return <FallbackUI />;
        }
        return this.props.children;
    }
}

// Granular boundaries — section crash doesn't kill whole page:
<ErrorBoundary><NavBar /></ErrorBoundary>
<ErrorBoundary><ArticleBody /></ErrorBoundary>
<ErrorBoundary><CommentWidget /></ErrorBoundary>
// Article still loads if comment widget crashes
```

**SSR crashes (Next.js):**

```typescript
// pages/_error.tsx
export async function getInitialProps({ res, err }) {
    Sentry.captureException(err);
    return { statusCode: res?.statusCode ?? 500 };
}

// Second line of defence: Cloudflare custom error pages
// If origin returns 500 → Cloudflare serves:
//   cached stale version (stale-while-revalidate)
//   OR branded error page (not raw server error)
```

**Automated crash alerts (alert on RATE, not every error):**

```yaml
- name: "SEV-1 crash rate"
  condition: error_rate > 20% of sessions in 5 minutes
  action: PagerDuty SEV-1 — wake people up

- name: "SEV-2 elevated errors"
  condition: error_rate > 5% of sessions in 5 minutes
  action: PagerDuty SEV-2

- name: "New issue with broad impact"
  condition: new_issue AND affected_users > 50 in 10 minutes
  action: PagerDuty SEV-2 page

# A ResizeObserver loop error ≠ 3am page
# 500 users seeing blank article body = SEV-2
```

### SLA Definitions

| SLA Type | Target | Meaning |
|---|---|---|
| **Content freshness** | < 30 min | Published content live globally within 30 min |
| **Page availability** | 99.9% | Max ~44 min downtime/month |
| **API availability** | 99.5% | CMS APIs (search, forms, comments) |
| **P95 page load** | < 1.5s | 95th percentile load time globally |
| **Build pipeline** | < 25 min | Full 10k-page build completes in under 25 min |

### Content Freshness Pipeline Breakdown

```
Editor publishes           →  0 min
Webhook fires              →  0–2 min    (webhook latency)
Incremental build (1 page) →  +2–4 min
ISR revalidation           →  +1 min
Cloudflare purge           →  +1 min
CDN propagation globally   →  +3–5 min
Content live everywhere    →  ~10–15 min total ✓

Full rebuild (10k pages)   →  15–25 min (nightly or on template change)
```

### Severity Levels

| Severity | Definition | Example | Response |
|---|---|---|---|
| **SEV-1** | Site down or >20% users impacted | CDN outage, origin unreachable | 15 min — wake people up |
| **SEV-2** | Core feature broken for some users | Search broken, 10% of pages 500ing | 1 hour, business hours |
| **SEV-3** | Degraded experience, workaround exists | Slow load, one page erroring | Next business day |
| **SEV-4** | Minor bug, no user impact | Broken link, copy typo | Backlog |

**Automated severity config:**

```yaml
- name: "SEV-1 auto-trigger"
  condition: error_rate > 20% for 3 minutes
  action:
    - page on-call via PagerDuty
    - post to #incidents channel
    - open incident on statuspage.io

- name: "SEV-2 auto-trigger"
  condition:
    - error_rate > 5% for 5 minutes
    - OR CDN origin error rate > 1%
    - OR P95 latency > 3s for 5 minutes
  action:
    - alert on-call
    - post to #incidents

- name: "SEV-3 auto-trigger"
  condition:
    - single-page error rate > 10%
    - OR build pipeline failed
    - OR P95 LCP > 4s for 10 minutes
  action:
    - post to #eng-alerts (no page)
```

### Core Web Vitals as Continuous SLA

```
Metric     Target     Alert Threshold
LCP        < 2.5s     > 4s for P75 in any region
CLS        < 0.1      > 0.25 for P75
FID/INP    < 200ms    > 500ms for P75

Two data sources:
  Lab / Synthetic:  Checkly runs Chromium every 60s
  Field / RUM:      Sentry or Datadog — real user monitoring
                    Segmented by geography, device, connection

P95 LCP regression to 4s after deploy = SEV-3
Shows up in morning report, fixed that day.
```

---

## 16. DDoS & Bot Handling

### Defence Layers

```
Layer 3/4 DDoS   →  Cloudflare absorbs automatically
                    (300+ Tbps capacity, no config needed)

Layer 7 DDoS     →  Cloudflare WAF rules + rate limiting
                    (configure thresholds per endpoint)

Scraper flood    →  Cloudflare Bot Fight Mode
                    JS challenge → CAPTCHA → block (progressive)

Known bots       →  Token bucket rate limiting
(GPTBot, etc)       100 RPS allowed, then 429
```

### Rate Limiting Rules

```
Rule 1: Normal users
  Match: all requests
  Rate:  40 requests / 10 seconds per IP (sliding window)
  Action: 429 after limit

Rule 2: Known bot user-agents
  Match: User-Agent contains "GPTBot" OR "ClaudeBot" OR "Googlebot"
  Rate:  100 requests / 10 seconds per IP
  Action: 429 after limit

Rule 3: Editor IPs
  Match: IP in allowlist
  Action: skip all rate limiting

Rule 4: DDoS auto-challenge
  Match: > 150 requests / 1 second from single IP
  Action: Cloudflare Turnstile challenge

Rule 5: ASN burst (most effective for coordinated attacks)
  Match: > 500 requests / 60 seconds from single ASN
  Action: enable Under Attack Mode
          (JS challenge for every visitor — kills bots, humans pass in 3–5s)
```

### Why ASN-Level Blocking

```
Bots rotate IPs but stay within the same autonomous system (ASN)
One ASN block = hundreds of IPs blocked in one rule

IP-level:  200 different IPs → 200 rules
ASN-level: all 200 IPs in ASN 12345 → 1 rule
```

---

## 17. Incident Triage

### Goal: "Who is affected?" BEFORE "How do we fix it?"

### Step 1 — Check Cloudflare Analytics (2 minutes)

```
→ Is this one region?           (datacenter / PoP issue)
→ Is this one URL pattern?      (content/build issue vs. origin issue)
→ Is request volume spiking?    (DDoS or traffic event)
→ What's the cache hit rate?    (drop in cache hit = more origin load)
```

### Step 2 — Check Sentry (3 minutes)

```
Filter by:
  → URL:          which pages are erroring?
  → Browser/OS:   device-specific bug?
  → Country:      regional CDN / ISP issue?
  → Release:      did this start after today's deploy?

Actionable output:
  "10k users in Germany seeing TypeError on /pricing"
  = regional + specific page + likely build/content issue
```

### Step 3 — Check RUM (Real User Monitoring) (3 minutes)

```
Segment by: geography, device type, ISP, connection speed

Example insight:
  "Mobile users in India on 4G seeing P95 > 6s"
  = performance regression, not a crash — different response
```

### Step 4 — Update Status Page Immediately

```
Within 10 minutes of identifying an issue, post:

"We are investigating elevated error rates for users in the EU.
 Our team is actively working on a resolution.
 Next update in 30 minutes."

Update every 30 minutes until resolved.
Silence during an incident = users assume the worst
→ support ticket flood → compounds the problem
```

### Triage Decision Tree

```
Alert fires
  │
  ├── Error rate > 20%?
  │     → SEV-1: wake everyone up, open war room
  │
  ├── Error rate 5–20%?
  │     → SEV-2: alert on-call, start investigation
  │     → Check: specific region? specific page? specific browser?
  │
  ├── Error rate < 5%, P95 latency > 3s?
  │     → SEV-3: log for morning
  │     → Check: recent deploy? CDN change? image size regression?
  │
  └── Single page erroring?
        → SEV-3: check content for bad Markdown / broken image
        → Editor can fix in CMS → ask to fix and republish
        → Code issue → hot patch + redeploy
```

### Rollback Strategies

```
Content issue (bad article):
  Editor in Sanity → restore previous version → republish
  → Webhook fires → ISR → CDN purged → fixed in ~5 min

Code/template issue (deploy broke pages):
  Vercel → Rollback to previous deployment (one click)
  → Full CDN purge of affected paths
  → Cache warming for top pages

CDN configuration issue:
  Cloudflare → revert last rule change
  → Instant (Cloudflare propagates config in < 30s)

Database issue (CMS API down):
  CDN continues serving cached pages (stale-while-revalidate)
  Users see up to 5-minute-old content — acceptable per SLA
  Fix CMS → content refreshes within SLA window
```

---

## 18. Interview Cheatsheet

### Requirements to Clarify

```
Always ask before designing:
  ✓ How many concurrent editors?
  ✓ Concurrent editing on same doc?
  ✓ Approval workflow needed?
  ✓ Content types (articles only, or mixed)?
  ✓ Multilingual / localized?
  ✓ Who controls templates — editors or devs?
  ✓ Bot traffic profile (RPS)?
  ✓ Freshness SLA (how soon must content go live)?
  ✓ SEO requirements?
  ✓ LLM accessibility / crawlability?
```

### The RADIO Framework

```
R — Research:     Requirements + clarifying questions
A — Architecture: High-level system diagram, CMS choice, CDN layer
D — Data Model:   Document schema, version table, media storage
I — Interface:    Webhook contract, REST API, cache headers
O — Optimization: Images, video, service worker, cache strategies
```

### Key Decisions & Trade-offs

```
CMS choice:
  SaaS (Sanity):       faster to ship, concurrent editing native, recurring cost
  Self-hosted (Strapi): control over infra, more DevOps overhead

Rendering strategy:
  SSG:  best for read-heavy, pre-generate all pages
  ISR:  best for partial updates without full rebuild
  SSR:  avoid — adds latency, no benefit for published content

Cache invalidation:
  Purge by URL:   surgical, for single page edits
  Purge by tag:   relational, for author/category updates
  Wildcard:       section-wide, for template changes
  Full + warm:    last resort, with cache warming script

Versioning storage:
  Full snapshots in DB for restore (not delta/diff)
  Pre-computed diffs only for UI display
  Media in S3/R2, URL reference in DB
```

### Key Numbers

```
Content freshness SLA:      < 30 min (incremental build + CDN propagation)
Incremental build (1 page): 2–4 minutes
Full build (10k pages):     15–25 minutes
CDN propagation globally:   3–5 minutes after purge
Cache TTL for HTML:         5 minutes (stale-while-revalidate 1 hour)
Cache TTL for assets:       1 year (immutable, versioned URL)
Image quality on 3G:        quality=65 (via Network Information API)
Heartbeat interval:         30 seconds
SEV-1 response time:        15 minutes
SEV-2 response time:        1 hour
Status page update:         every 30 minutes during incident
Page load target (3G):      < 4 seconds
Data per page load:         ~300KB (optimized) vs 8MB (unoptimized)
```

### One-Liners for Each Concept

```
Headless CMS:           "Content in DB, delivered via API, rendered by your frontend"
Webhook + ISR:          "Publish → rebuild one page → purge one URL → live in 5 min"
Cache tags:             "Tag responses with metadata, purge by tag to invalidate related pages"
Stale-while-revalidate: "Serve old, fetch new in background — user never waits"
LQIP:                   "20px blurred placeholder → full image fades in → zero layout shift"
Service worker:         "Browser-side proxy — serve cached pages when network drops"
OT (in CMS):            "Every keystroke is an operation, server transforms concurrent edits"
SEV-1:                  "> 20% users impacted — wake people up"
ASN block:              "One rule blocks hundreds of bot IPs in same autonomous system"
Error boundary:         "Isolate crashes per section — comment crash ≠ article crash"
Cache warming:          "Pre-populate CDN after purge — script crawls sitemap first"
```

### Common Interview Mistakes to Avoid

```
❌ Engineering-first:    "Use Git for editing" — non-technical editors can't use it
❌ Jumping to code:      Clarify requirements before any solution
❌ Full rebuild always:  Use incremental builds + ISR
❌ Images in database:   Use object storage (S3/R2), store URL reference
❌ Monolithic monitoring: Need all 4 layers (app + infra + CDN + synthetic)
❌ Alert on every error: Alert on rate and blast radius
❌ Ignoring offline:     Service worker + stale-while-revalidate
❌ Ignoring bots:        Design rate limiting for 100 RPS bursts from day one
❌ Full purge for 1 edit: Use purge-by-URL instead
❌ Contradicting yourself: Pick one approach per decision, stick with it
```

### Summary by Experience Level

```
1–3 years:
  Start with Sentry. Learn error boundaries, stack traces, alert rules.
  Everything else builds on this foundation.

3–6 years:
  Focus on build pipeline SLA. Incremental builds, cache invalidation,
  content freshness latency. A CMS editors think is "slow to publish"
  is a CMS they work around — which creates consistency problems.

6–10 years:
  The interesting work is triage playbooks and severity automation.
  Systematically replace human judgment calls with automated rules —
  so the on-call engineer's job becomes "verify and communicate"
  rather than "investigate from scratch at 3am."
```

---

*Covers: Financial Times / CNN / Wikipedia / NDTV scale CMS.
Technologies: Sanity CMS, Next.js ISR, Cloudflare CDN + WAF, Sentry, Datadog,
Checkly, PagerDuty, Workbox, Algolia/Pagefind, S3/Cloudflare R2, GitHub Actions, Vercel.*
