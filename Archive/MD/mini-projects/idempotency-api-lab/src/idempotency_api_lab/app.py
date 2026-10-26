"""
Minimal payment API demonstrating idempotent POST /charges.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from idempotency_api_lab.store import IdempotencyStore

app = FastAPI(title="Idempotency API Lab")
store = IdempotencyStore()

# Simulated ledger — in production this is your transactional DB
_charges: dict[str, dict[str, Any]] = {}


class ChargeRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: str = "usd"
    customer_id: str


class ChargeResponse(BaseModel):
    id: str
    amount_cents: int
    currency: str
    status: str = "succeeded"


@app.post("/v1/charges", response_model=ChargeResponse)
def create_charge(
    body: ChargeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ChargeResponse:
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header required")

    payload = body.model_dump()
    try:
        cached = store.begin(idempotency_key, payload)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except RuntimeError:
        raise HTTPException(409, "Another request with this key is in progress")

    if cached and cached.response_body:
        return ChargeResponse(**cached.response_body)

    # --- "Payment engine" (slow on purpose to show in-flight duplicates) ---
    time.sleep(0.05)
    charge_id = f"ch_{uuid.uuid4().hex[:12]}"
    resp = ChargeResponse(id=charge_id, amount_cents=body.amount_cents, currency=body.currency)
    _charges[charge_id] = resp.model_dump()
    store.complete(idempotency_key, 200, resp.model_dump())
    return resp


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
