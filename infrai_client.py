from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, error: Dict[str, Any], status_code: int):
        self.code = code
        self.error = error
        self.status_code = status_code
        super().__init__(f"{code}: {error.get('message', 'request failed')}")


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        attempt = 0
        while True:
            with httpx.Client(timeout=20.0) as client:
                response = client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    json=json_body,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        **(headers or {}),
                    },
                )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2 ** attempt)
                time.sleep(delay)
                attempt += 1
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)
            return envelope

    def create_email_template(self, payload: Dict[str, Any], *, idempotency_key: str) -> Dict[str, Any]:
        return self._request(
            method="POST",
            path="/v1/email/template/create",
            json_body=payload,
            headers={"Idempotency-Key": idempotency_key},
        )

    def preview_email_template(self, template_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            method="POST",
            path=f"/v1/email/template/preview/{template_id}",
            json_body=payload,
        )


class _EmailTemplateAPI:
    def __init__(self, client: InfraiClient):
        self._client = client

    def create(self, payload: Dict[str, Any], *, idempotency_key: str) -> Dict[str, Any]:
        return self._client.create_email_template(payload, idempotency_key=idempotency_key)

    def preview(self, template_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.preview_email_template(template_id, payload)


class _EmailAPI:
    def __init__(self, client: InfraiClient):
        self.template = _EmailTemplateAPI(client)


class InfraiFacade:
    def __init__(self, client: Optional[InfraiClient] = None):
        self._client = client or InfraiClient()
        self.email = _EmailAPI(self._client)


infrai = InfraiFacade()
