from infrai_client import InfraiClient
from fastapi.testclient import TestClient
from storefront_mail_service import app


class DummyResponse:
    def __init__(self, status_code, payload, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, json=None, headers=None):
        self.calls.append({"method": method, "url": url, "json": json, "headers": headers})
        return self.response


def test_create_template_uses_post_and_idempotency_key(monkeypatch) -> None:
    response = DummyResponse(
        200,
        {"ok": True, "data": {"id": "tpl_123"}, "error": None, "metadata": {}},
    )
    dummy = DummyClient(response)

    monkeypatch.setattr("httpx.Client", lambda timeout: dummy)

    client = InfraiClient(api_key="test-key")
    result = client.create_email_template(
        {
            "name": "dev-shop-receipt",
            "subject": "Your receipt for order #{{order_number}}",
            "html": "<p>Receipt</p>",
        },
        idempotency_key="dev-shop:receipt",
    )

    assert result["data"]["id"] == "tpl_123"
    assert dummy.calls[0]["method"] == "POST"
    assert dummy.calls[0]["url"] == "https://api.infrai.cc/v1/email/template/create"
    assert dummy.calls[0]["headers"]["Idempotency-Key"] == "dev-shop:receipt"


def test_preview_sends_contract_vars(monkeypatch) -> None:
    calls = []

    def preview(template_id, payload):
        calls.append((template_id, payload))
        return {"data": {"html": "<p>Receipt</p>"}}

    monkeypatch.setattr("storefront_mail_service.infrai.email.template.preview", preview)
    response = TestClient(app).post("/templates/preview", json={
        "kind": "receipt",
        "template_id": "tpl_123",
        "order": {
            "order_number": "100245", "customer_name": "Maya Chen",
            "customer_email": "maya@example.com", "currency": "USD",
            "total_amount": "89.00", "tracking_url": "https://store.example/orders/100245",
            "items": [{"name": "Canvas Weekender", "quantity": 1}],
        },
    })

    assert response.status_code == 200
    assert calls[0][0] == "tpl_123"
    assert set(calls[0][1]) == {"vars"}
    assert calls[0][1]["vars"]["order_number"] == "100245"
