from fastapi.testclient import TestClient

from idempotency_api_lab.app import app

client = TestClient(app)


def test_retry_returns_same_charge_id() -> None:
    headers = {"Idempotency-Key": "order_abc_1"}
    body = {"amount_cents": 5000, "currency": "usd", "customer_id": "cus_1"}
    r1 = client.post("/v1/charges", json=body, headers=headers)
    r2 = client.post("/v1/charges", json=body, headers=headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_same_key_different_body_rejected() -> None:
    headers = {"Idempotency-Key": "order_abc_2"}
    client.post("/v1/charges", json={"amount_cents": 100, "currency": "usd", "customer_id": "c"}, headers=headers)
    r = client.post("/v1/charges", json={"amount_cents": 200, "currency": "usd", "customer_id": "c"}, headers=headers)
    assert r.status_code == 422
