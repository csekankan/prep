"""
FastAPI application factory and uvicorn entrypoint.

WHY assemble dependencies on app.state:
- Integration tests swap in small worker pools and aggressive circuit thresholds
  without patching global singletons.
"""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from llm_serving_gateway.config import Settings, get_settings
from llm_serving_gateway.idempotency import IdempotencyStore
from llm_serving_gateway.logging_setup import configure_logging
from llm_serving_gateway.middleware import RequestIdMiddleware
from llm_serving_gateway.rate_limit import TenantRateLimiter
from llm_serving_gateway.routes.chat import router as chat_router
from llm_serving_gateway.upstream_pool import UpstreamPool

logger = logging.getLogger("llm_serving_gateway.app")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(json_logs=settings.log_json)

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.add_middleware(RequestIdMiddleware)

    app.state.settings = settings
    app.state.tenant_limiter = TenantRateLimiter(settings)
    app.state.upstream_pool = UpstreamPool(settings=settings)
    app.state.idempotency_store = IdempotencyStore(ttl_seconds=settings.idempotency_ttl_seconds)

    app.include_router(chat_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "llm_serving_gateway.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
