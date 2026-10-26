# Acme Cloud — Product FAQ (Sample)

## What is Acme Cloud?

Acme Cloud is a **managed event streaming platform**. Teams publish events to **topics**; other services subscribe with **consumer groups** for horizontal scale.

## Pricing tiers

| Tier | Throughput | Retention | Price |
|------|------------|-----------|-------|
| Starter | 5 MB/s | 7 days | $99/mo |
| Growth | 50 MB/s | 30 days | $499/mo |
| Enterprise | Custom | Up to 1 year | Contact sales |

## SLAs

- **Starter / Growth:** 99.9% monthly uptime.
- **Enterprise:** 99.95% with financially backed credits.
- **Support response:** Starter 24h, Growth 8h business hours, Enterprise 1h for P1.

## Common limits

- **Max message size:** 1 MB (configurable to 4 MB on Enterprise).
- **Max partitions per topic:** 64 on Starter, 256 on Growth, unlimited on Enterprise.
- **API rate limit:** 1,000 requests/min per API key on Growth; burst to 2,000 for 60 seconds.

## Getting started

1. Create a project in the console.
2. Generate an **API key** (rotate keys every **90 days**).
3. Create a topic named `orders` with **3 partitions** for dev.
4. Use the **Acme SDK** (`pip install acme-stream`) to produce and consume.

## Troubleshooting lag

If consumer lag grows:

- Increase **consumer instances** in the same consumer group.
- Check for **slow handlers** (p95 handler time should stay under 100ms).
- Verify **partition count** is at least equal to peak parallel consumers.
