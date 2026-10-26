# Migration Execution: Schema, Backfills, and Verification

> Mechanisms for changing **shape** and **location** of data under live traffic: online DDL, terabyte backfills, and verification when you cannot eyeball billions of rows.

---

## Table of Contents

1. [Online schema changes](#online-schema-changes)
2. [Backfills at terabyte scale](#backfills-at-terabyte-scale)
3. [Verifying data you cannot eyeball](#verifying-data-you-cannot-eyeball)

---

## Online schema changes

Most schema outages are not “slow DDL”—they are **fast DDL that had to wait** behind a long transaction.

### The lock queue (Postgres and MySQL)

In Postgres, `ALTER TABLE` needs **ACCESS EXCLUSIVE**. While it waits, new `SELECT`s queue behind it—one idle-in-transaction session can block the whole table.

**Pool exhaustion:** if table gets λ qps and pool has P connections, pools empty in ~**P/λ** seconds; then **unrelated endpoints** fail too.

```sql
-- Session settings for migration (Postgres)
SET lock_timeout = '300ms';
SET statement_timeout = '30min';
-- Retry ALTER with exponential backoff + jitter
```

| Default | Risk |
|---------|------|
| `lock_timeout = 0` (Postgres) | Wait forever |
| `lock_wait_timeout` ≈ 1 year (MySQL MDL) | Same |

Size `lock_timeout` **below P/λ** on hot tables (often 100–500ms), not habitually 5s.

### What rewrites cost

| Change | Postgres | MySQL 8 InnoDB |
|--------|----------|----------------|
| Add nullable column | Cheap metadata | INSTANT (version-dependent) |
| Add column with default | PG11+ often metadata; volatile defaults rewrite | INSTANT for constants |
| Drop column | Cheap metadata | INSTANT 8.0.29+ |
| `int` → `bigint` | Full rewrite + indexes | COPY |
| Add index | `CREATE INDEX CONCURRENTLY` | INPLACE; replicas lag full build |
| `SET NOT NULL` | Scan unless valid CHECK exists | Often rebuild |

**MySQL traps:**

- `VARCHAR` widening measured in **bytes**—utf8mb4 (63)→(64) can trigger full copy.
- `innodb_online_alter_log_max_size` (128MB default)—overflow fails at end of long ALTER.
- **INSTANT** row-version cap (64)—eventually forced rebuild.

Estimate rewrites: **max**(heap copy, index rebuild, **replica replay**)—teams that only estimate heap miss by 4×.

### Shadow-table tools (gh-ost vs pt-osc)

Both: empty shadow → chunk copy → capture concurrent changes → atomic swap.

| | pt-online-schema-change | gh-ost |
|--|-------------------------|--------|
| Capture | Triggers in app txn | Binlog (ROW, full images) |
| Write path cost | ~2× work, deadlocks | Async apply |
| Pause | Copy pauses; triggers fire | Full pause possible |
| FKs | Supported | Not supported |

**Convergence:** if mean write rate &gt; apply rate, backlog never reaches zero—no cut-over window. Measure apply at 30% and 60% complete.

**Cut-over:** gh-ost uses sentry table + lock ordering so failed locker → safe abort. Budget stall: lock acquisition + **residual backlog / apply rate** must fit tightest client write timeout.

### Postgres without gh-ost

Pattern: **weak lock for long work, strong lock for ms swap.**

```sql
-- Expand: add column (brief ACCESS EXCLUSIVE)
ALTER TABLE orders ADD COLUMN id_new bigint;

-- Sync trigger (brief lock to create)
CREATE OR REPLACE FUNCTION sync_id_new() RETURNS trigger AS $$
BEGIN
  NEW.id_new := NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Backfill in batches (row locks, WAL)—NOT one big txn
UPDATE orders SET id_new = id
WHERE id BETWEEN $1 AND $2 AND id_new IS NULL;

-- Index + prove NOT NULL under weak locks
CREATE UNIQUE INDEX CONCURRENTLY orders_id_new_idx ON orders (id_new);
ALTER TABLE orders ADD CONSTRAINT orders_id_new_nn
  CHECK (id_new IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_id_new_nn;

-- Swap: single short txn with lock_timeout
BEGIN;
  -- drop old PK, set NOT NULL, add PK USING INDEX, renames...
COMMIT;
```

`CREATE INDEX CONCURRENTLY` pins **xmin** for whole database during scans—watch dead tuples on unrelated tables.

### Expand/contract at the database layer

| Phase | Schema | Roll back one step? |
|-------|--------|-------------------|
| Expand | +nullable column | Yes |
| Dual-write | Both columns written | Yes |
| Backfill | New column complete | Yes |
| Switch reads | Reads new | Only while old writes continue |
| Stop old writes | Old column stale | **One-way for data** |
| Contract | Drop old column | Permanent |

**Live code** includes: old pods, cron, BI, CDC, mobile—phase 4 is often the real data PONR, not the DROP.

```ruby
# Rails: stop ORM knowing about column before DROP
class Order < ApplicationRecord
  self.ignored_columns = %i[legacy_status]
end
```

### Blast radius beyond primary

- Replicas replay locks and WAL volume; cross-region RPO degrades for hours.
- Logical replication / CDC: **DDL order**—add on subscribers first, drop on publisher first.
- Broken connector → slot lag → **primary disk full** (`max_slot_wal_keep_size`).

**Pre-flight gates (runner should refuse):**

| Signal | Stop if |
|--------|---------|
| Oldest txn on DB | &gt; 30–60s |
| Anti-wraparound vacuum | Running on target |
| P/λ vs lock_timeout | Timeout &gt; drain time |
| Replica lag | &gt; RPO/2 |
| Slot retained WAL | &gt; 25% free WAL disk |
| Free disk | &lt; 1.3× peak need |
| Apply vs write rate | &lt; 1.2× (shadow won't converge) |

---

## Backfills at terabyte scale

A backfill is a **new sustained write workload** on production—not “600 GB logical change.”

### Blast radius of one UPDATE row

| Effect | Who gets paged |
|--------|----------------|
| Heap + dead tuple + all secondary indexes | DBA |
| WAL / FPI after checkpoint | Replicas, archive |
| CDC / `updated_at` | Warehouse, search, webhooks |
| Buffer pool eviction | Other teams' p99 |
| Long snapshot | **Entire DB** vacuum/purge stall |

**Rate limit in WAL bytes/s**, not rows/s. Make updates **HOT-eligible** (don't index backfill column until done).

```sql
-- Tag backfill origin so consumers can filter
SET LOCAL application_name = 'backfill:migration-2026-orders';
-- Prefer SQL without ORM callbacks bumping updated_at
```

### Chunking

- Target **chunk duration** (50–500ms), not fixed row count.
- **Keyset** pagination—never `OFFSET`.
- **Newest-first** backfill enables early read cutover for recent data; fix `max(id)` at start after live path runs.
- Parallel workers: split by **key quantiles**, not equal ranges—steal work from stragglers.

### Throttling (AIMD)

Closed-loop on: replica heartbeat lag, p99, `Threads_running`, **slot lag bytes**, snapshot age.

```text
While all signals OK:  rate += small step
On any breach:       rate *= 0.5 (or stop)
Ramp no faster than sensor delay (~1 lag period)
Ceiling ~55–70% of bottleneck utilization (failover headroom)
```

> **Backfill spends the service error budget**—when SLO policy says freeze deploys, pause the backfill too.

### Idempotent and resumable

**Anti-pattern:** `WHERE new_col IS NULL LIMIT 1000`—quadratic re-walk; partial index on `IS NULL` kills HOT.

**Pattern:** high-water mark per range in control table, advanced in **same txn** as chunk (same DB) or after durable idempotent write (cross-store).

```sql
INSERT INTO target_orders AS t (id, status, src_version, ...)
VALUES ($1, $2, $3, ...)
ON CONFLICT (id) DO UPDATE SET
  status = EXCLUDED.status,
  src_version = EXCLUDED.src_version,
  ...
WHERE t.src_version < EXCLUDED.src_version;
```

Deterministic transforms: `UUIDv5(old_key)`, copy timestamps—**run backfill twice, diff targets**.

Poison rows → bisect chunk → **dead-letter table** with owner before cutover.

### Rows that change mid-copy

Backfill must **never win** against newer live write:

| Strategy at apply time | Stale overwrite? |
|----------------------|------------------|
| Blind upsert | Yes |
| `ON CONFLICT DO NOTHING` | Safe only if live path writes **full rows** |
| Version-conditional upsert | Preferred |
| Read+write same source txn | Safe; contends with app |

Tombstones for deletes; retention ≥ max rewind of CDC offsets.

### Duration estimate (honest)

| Multiplier | Why |
|------------|-----|
| ~60% duty cycle | Throttle at peak |
| ~2× | Index cliff on target |
| +15% | Pauses, failovers |
| ×2.5 runs | First run finds poison classes |

**Structural wins:** load without secondary indexes then sort-build; **physical clone + log catch-up** when source cannot take scan load.

### Six copy mechanisms (pick in order)

1. Can source take load at peak? If no → clone/export.
2. Transform in SQL vs app code?
3. CDC pipeline exists? → one writer, watermarks.
4. Target fastest ingest path?

---

## Verifying data you cannot eyeball

Verification is the migration's **spec written as code**.

### Equivalence function

| Rule type | Example | Danger if "fixed" silently |
|-----------|---------|----------------------------|
| Representation | Compare float bits | OK |
| Semantic | Trim trailing space | Hides duplicate tenants |

```python
def canonical_row(row: dict) -> bytes:
    """Length-prefixed, null-marked encoding—never naive CONCAT_WS."""
    parts = []
    for col in SCHEMA_ORDER:
        v = row.get(col)
        if v is None:
            parts.append(b"\x00")
        else:
            parts.append(len_prefix(encode(col, v)))
    return b"".join(parts)
```

Version the function; relaxing rules requires **full re-sweep**.

### Checksums at scale

- Push-down hash per **key range** on each side; only digests cross the wire.
- **Full outer join** on keys—detect rows only on new side.
- Prefer **sum of row hashes mod 2^64 + COUNT** over XOR for migration defects (retries change multiplicity).

```sql
-- Illustrative per-chunk aggregate (concept)
SELECT count(*) AS cnt,
       sum(hashtextextended(canonical_text, 0))::numeric AS h
FROM orders
WHERE id >= $lo AND id < $hi;
```

One **short txn per chunk**—never one 28-hour snapshot (pins xmin cluster-wide).

### Comparing a moving target

| Technique | Cost | Hot keys |
|-----------|------|----------|
| Recheck after 2× p99 lag | Low | Fails |
| Version-gated compare | Medium | Good |
| Frozen-point (replica at LSN) | High | Gold standard |
| Quiesce slice at cutover | Per slice | Exact |

**Report exclusion set** (in-flight, undecoded rows) beside mismatch count.

### Sampling vs full

Sampling estimates **rate**; migration needs **which rows**. Defects cluster by provenance—use **stratified** samples (era, source system), not only `TABLESAMPLE SYSTEM` on pages.

### Reconciliation report

Watch **unexplained mismatch count trend**, not only "zero today." Send divergent ranges back through **idempotent range re-run** from backfill tooling.

### Evidence file before decommission

Frozen-point compare results, equivalence function version, sign-off on semantic rules, last reverse-sync verification timestamp.

---

## Execution checklist

| Area | Question |
|------|----------|
| DDL | P/λ vs lock_timeout? Rehearsed on prod charset/version? |
| Shadow copy | Apply rate vs peak write rate? Cut-over window hours? |
| Backfill | Throttle on slot lag bytes? Progress store? Version on upsert? |
| Verify | Equivalence rules classified? Multiset hash? Exclusions reported? |

---

## Key takeaways

1. **Bound lock wait** and retry—nullable `ALTER` can still take production down.
2. **Expand/contract** is a contract with every code version and cache TTL.
3. Backfills are **controllers** on harm signals, not fixed rows/s loops.
4. **Verification** is the real spec—too-lax rules launder bugs; too-strict rules train teams to ignore reports.
5. Finishing the backfill means the job exited—not that data is correct. Verify, then cut over (see `migration-cutover.md`).

---

## Senior Pitfalls

| Mistake | Impact | Fix |
|---------|--------|-----|
| Bulk copy without throttling on production source | OLTP P99 collapse during backfill | Rate limits, off-peak windows, read replicas as source, change-data-capture instead of dump |
| Shadow traffic compared only on aggregates | Row-level mismatches slip into cutover | Per-key sampling, checksum jobs, reconciliation reports with escalation thresholds |
| Feature flag at 100% without draining old code paths | Latent callers still hit legacy | Static analysis + access logs + enforce 404 on old endpoints after deadline |
| Incremental sync lag ignored during write cutover | Users see stale reads post-flip | Gate cutover on max lag SLO; read-your-writes tests from prod-like clients |
| Runbook steps that assume manual heroics | On-call burnout; extended outage | Automate fence, drain, verify; game-day the runbook quarterly |
| Data validation only on schema, not semantics | Money amounts correct type but wrong currency scale | Domain invariants, shadow billing totals, finance sign-off on sample periods |

---

## Production-grade Practice

1. **Throttled backfill:** Run initial load at 3 throttle levels; plot source DB CPU and replication lag; pick max safe rate and document kill switch criteria.
2. **Shadow diff pipeline:** Stream 1% of production writes to both systems; build automated diff report with top 10 mismatch categories and owner routing.
3. **Flag ramp postmortem prep:** Design a 1% → 10% → 50% ramp with automatic rollback on error-rate burn; implement metrics hooks before first ramp.
4. **Reconciliation job:** Nightly compare row counts and sum(checksum) between old and new for one domain; tune tolerance and alert when drift accelerates.

---

## FAANG Interview Deep Dive

### Real-world examples

**GitHub gh-ost on massive MySQL tables**  
GitHub popularized **gh-ost** for **online DDL** on **multi-TB** tables—chunk copy with **binlog tailing**, **throttle on replication lag**. A single **`ALTER`** without tooling can **block MDL** for hours—**pool exhaustion** in **P/λ seconds** takes down unrelated APIs.

**Stripe schema expand/contract**  
API migrations use **expand → dual write → backfill → contract** so **old and new code** coexist for **weeks**. Interview depth: **nullable column** deploy is not enough—you need **versioned readers** until **contract** phase.

**Meta/Instagram-scale backfills**  
Terabyte backfills run as **controllers**: throttle when **replica lag > X MB**, **checkpoint** progress store, **idempotent upsert** with **`src_version`**. Fixed **10k rows/s** loops **double** load during **peak**—harm-based throttle is mandatory.

```sql
-- Bound lock wait (Postgres migration session)
SET lock_timeout = '300ms';
SET statement_timeout = '30min';
-- Retry ALTER with jittered backoff
```

### Interview Q&A

### Q: Why did a “cheap” nullable column ALTER take production down?
**A:** **Lock queue**: `ACCESS EXCLUSIVE` waits behind long transactions; **queued SELECTs** block new work. **lock_timeout** must be **< pool drain time P/λ**. Idle **idle-in-transaction** session is a classic root cause.

### Q: gh-ost vs pt-osc?
**A:** Both shadow-table copy. **gh-ost**: **no triggers**, binlog stream, GitHub-hardened. **pt-osc**: triggers, mature on older MySQL. Choose based on **binlog privileges**, **trigger policy**, **cutover atomicity** requirements.

### Q: How fast can you backfill 5TB?
**A:** **Not** “disk read speed”—limited by **replica replay**, **index maintenance**, **contention on hot keys**. If safe sustained **50MB/s** apply → **5TB ≈ 28 hours** minimum; plan **2–5×** for lag throttling and **rehearsal**.

### Q: Verification at billion-row scale?
**A:** **Multiset hashes** per **key range**, **equivalence functions** (normalize timestamps, JSON order), **trend of mismatch count** not binary zero. **Too-strict** rules train teams to ignore reports; **too-lax** launder bugs.

### Q: Expand/contract with caches?
**A:** Cache keys include **schema version** or **TTL < contract window**; otherwise **old shape** served after contract deploy causes **500s** or silent corruption.

### Common mistakes candidates make

- Estimating rewrite time from **heap only**, ignoring **index rebuild + replica lag**.
- **INSTANT** DDL assumptions without checking **MySQL version/row versions**.
- Backfill **without version column**—cannot merge concurrent updates safely.
- **Stopping verification** at “zero mismatches today” ignoring **drift trend**.
- **VARCHAR(63)→(64)** utf8mb4 triggering **full copy** surprise.

### Decision framework

| Change type | Postgres | MySQL 8 |
|-------------|----------|---------|
| Add nullable col | Often metadata | INSTANT (check version) |
| Add index | CONCURRENTLY | INPLACE + lag watch |
| Type widen | Rewrite | Often COPY |

**Pool drain:** λ = **1000 qps**, P = **50** connections → drain in **~50ms** if each holds conn—set **lock_timeout ~100–300ms** on hot tables.

### Backfill controller signals

| Signal | Throttle action |
|--------|-----------------|
| Replica lag > 100 MB | Halve batch size |
| p99 API up 20% | Pause backfill |
| Slot lag (CDC) | Stop apply, alert |

```python
# Harm-based throttle (pseudo)
while rows_remaining:
    batch = min(max_batch, lag_controller.current_cap())
    apply(batch)
    sleep(jitter(0.1, 0.5))
```

**Staff signal:** gh-ost on **TB tables**—explain **cut-over window** in **hours** and **replication lag** as the real limiter, not disk bandwidth alone.
