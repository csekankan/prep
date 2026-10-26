# Acme Cloud — On-Call Runbook (Sample)

## Severity definitions

- **P1:** Full regional outage or data loss risk. Page immediately.
- **P2:** Partial outage or SLA at risk. Respond within 15 minutes.
- **P3:** Degraded performance, workaround exists. Next business day.

## Incident commander checklist

1. Open a **#incident-** Slack channel and pin the timeline.
2. Assign roles: **IC**, **comms**, **scribe**.
3. Capture **customer impact** (regions, tiers, error rate).
4. Every 30 minutes, post a **status update** until resolved.

## Kafka-compatible broker restart

> Internal codename: **Broker "Nova"**

Safe rolling restart procedure:

1. Confirm **under-replicated partitions** = 0 in Grafana dashboard `nova/cluster`.
2. Restart one broker at a time; wait until `ActiveControllerCount` is stable.
3. Never restart more than **25%** of brokers in a cluster within 30 minutes.

## Elevated produce latency

Symptoms: p99 produce latency > 500ms, disk utilization < 70%.

1. Check **Zookeeper/KRaft** health (`zk_ok` metric).
2. Inspect **hot partitions** — single partition > 40% of traffic.
3. If hot partition: split topic (new topic + dual-write) — requires change window.

## Rollback a bad release

1. `kubectl rollout undo deployment/ingest-api -n production`
2. Verify error rate in Datadog drops within **5 minutes**.
3. File a postmortem if customer-visible > **10 minutes**.

## Secrets rotation

API signing keys rotate via **Vault** path `secret/acme/api-signing`. Dual-sign window is **24 hours** — both old and new signatures accepted during migration.
