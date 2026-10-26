"""Tenant-scoped rate limiting at the API edge."""

from llm_serving_gateway.rate_limit.tenant_limiter import TenantRateLimiter

__all__ = ["TenantRateLimiter"]
