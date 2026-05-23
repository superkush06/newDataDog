import hashlib
import hmac

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import webhooks


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(webhooks.router, prefix="/api/webhooks")
    return TestClient(app)


def _signature(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(webhooks, "secret_for_platform", lambda platform: "test-secret")
    body = b'{"data":{"id":"1","text":"hello"}}'

    response = _client().post(
        "/api/webhooks/x?brand_id=brand_1",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=wrong"},
    )

    assert response.status_code == 401


def test_webhook_accepts_valid_signature_and_normalizes(monkeypatch):
    queued = []

    async def fake_enqueue(payload):
        queued.append(payload)
        return {"status": "enqueued"}

    monkeypatch.setattr(webhooks, "secret_for_platform", lambda platform: "test-secret")
    monkeypatch.setattr(webhooks, "enqueue_monitor_job", fake_enqueue)
    body = b'{"data":{"id":"tw_1","text":"hello","author_handle":"acme_user"}}'

    response = _client().post(
        "/api/webhooks/x?brand_id=brand_1",
        content=body,
        headers={"X-Hub-Signature-256": _signature(body, "test-secret")},
    )

    assert response.status_code == 200
    assert response.json()["normalized"] == 1
    assert queued[0]["brand_id"] == "brand_1"
    assert queued[0]["post"]["external_id"] == "tw_1"
    assert queued[0]["post"]["text"] == "hello"


def test_webhook_returns_skipped_queue_when_queue_missing(monkeypatch):
    monkeypatch.setattr(webhooks, "secret_for_platform", lambda platform: "test-secret")
    monkeypatch.setattr(webhooks, "_track1_enqueue", None)
    body = b'{"items":[{"platform":"reddit","id":"r1","text":"broken"}]}'

    response = _client().post(
        "/api/webhooks/nimble?brand_id=brand_1",
        content=body,
        headers={"X-Hub-Signature-256": _signature(body, "test-secret")},
    )

    assert response.status_code == 200
    assert response.json()["queue"] == [{"status": "skipped", "reason": "missing_queue"}]


def test_webhook_rejects_unknown_platform_after_valid_signature(monkeypatch):
    monkeypatch.setattr(webhooks, "secret_for_platform", lambda platform: "test-secret")
    body = b'{"data":{"id":"1","text":"hello"}}'

    response = _client().post(
        "/api/webhooks/unknown?brand_id=brand_1",
        content=body,
        headers={"X-Hub-Signature-256": _signature(body, "test-secret")},
    )

    assert response.status_code == 400
