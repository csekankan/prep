"""
One token bucket per tenant id.

WHY per-tenant limits:
- Noisy neighbor protection — one customer's batch eval should not evict another's
  KV cache indirectly by saturating decode slots.
- Enterprise SLAs map cleanly to tenant id + API key metadata.
"""

from __future__ import annotations

import threading

from llm_serving_gateway.config import Settings, get_settings
from llm_serving_gateway.rate_limit.token_bucket import TokenBucket


class TenantRateLimiter:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._lock = threading.Lock()
        self._buckets: dict[str, TokenBucket] = {}

    def _bucket_for(self, tenant_id: str) -> TokenBucket:
        with self._lock:
            bucket = self._buckets.get(tenant_id)
            if bucket is None:
                bucket = TokenBucket.create(
                    capacity=self._settings.rate_limit_capacity,
                    refill_rate=self._settings.rate_limit_refill_per_sec,
                )
                self._buckets[tenant_id] = bucket
            return bucket

    def check(self, tenant_id: str, cost: float = 1.0) -> tuple[bool, float]:
        """
        Returns (allowed, retry_after_seconds).
        """
        bucket = self._bucket_for(tenant_id)
        if bucket.allow(cost):
            return True, 0.0
        return False, bucket.retry_after_seconds(cost)
