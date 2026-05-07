# License: MIT
# See LICENSE.
"""HTTP SDK for Sandesh API (Bearer token = JWT or API key)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import httpx

from sandesh.sdk.exceptions import SandeshAPIError, SandeshNetworkError

JsonDict = Dict[str, Any]


class Sandesh:
    """Synchronous API client for Sandesh."""

    def __init__(
        self, base_url: str, bearer_token: str, timeout: float = 60.0
    ) -> None:
        base = str(base_url or "").strip()
        token = str(bearer_token or "").strip()
        if not base:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("bearer_token is required")
        self._base = self._normalize_base_url(base)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "sandesh-sdk/python",
        }
        self._timeout = timeout
        self._client_instance: Optional[httpx.Client] = None

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        known_suffixes = (
            "/v1/events/trigger",
            "/api/v1/events/trigger",
        )
        lowered = normalized.lower()
        for suffix in known_suffixes:
            if lowered.endswith(suffix):
                normalized = normalized[: -len(suffix)].rstrip("/")
                break
        return normalized

    def _client(self) -> httpx.Client:
        if self._client_instance is None:
            self._client_instance = httpx.Client(
                base_url=self._base,
                headers=self._headers,
                timeout=self._timeout,
            )
        return self._client_instance

    def close(self) -> None:
        if self._client_instance is not None:
            self._client_instance.close()
            self._client_instance = None

    def __enter__(self) -> "Sandesh":
        self._client()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[JsonDict] = None,
    ) -> Any:
        normalized_path = path if path.startswith("/") else f"/{path}"
        client = self._client()
        try:
            response = client.request(
                method,
                normalized_path,
                params=params,
                json=json,
            )
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            try:
                body: Any = exc.response.json()
            except Exception:
                body = exc.response.text
            raise SandeshAPIError(
                message=(
                    f"{exc.request.method} {exc.request.url} failed "
                    f"with status {exc.response.status_code}"
                ),
                status_code=exc.response.status_code,
                response_body=body,
                request_method=exc.request.method,
                request_url=str(exc.request.url),
            ) from exc
        except httpx.HTTPError as exc:
            req = getattr(exc, "request", None)
            raise SandeshNetworkError(
                message=str(exc),
                request_method=req.method if req else None,
                request_url=str(req.url) if req else None,
            ) from exc

    # Events
    def events_trigger(self, body: JsonDict) -> JsonDict:
        """Strict contract trigger endpoint (`/v1/events/trigger`)."""
        try:
            return self._request("POST", "/v1/events/trigger", json=body)
        except SandeshAPIError as exc:
            if exc.status_code != 404:
                raise
            # Backward-compatible fallback for deployments exposing only
            # `/api/v1/events/trigger`.
            try:
                return self._request(
                    "POST", "/api/v1/events/trigger", json=body
                )
            except SandeshAPIError as fallback_exc:
                if fallback_exc.status_code != 422:
                    raise
                raise SandeshAPIError(
                    message=(
                        "Backend does not support Event API v1 contract at "
                        "`/v1/events/trigger`, and legacy endpoint "
                        "`/api/v1/events/trigger` rejected the payload "
                        "(422). Upgrade backend to a version that exposes "
                        "`/v1/events/trigger`, or use a legacy payload "
                        "shape for `/api/v1/events/trigger` "
                        "(template_id/email/payload)."
                    ),
                    status_code=fallback_exc.status_code,
                    response_body=fallback_exc.response_body,
                    request_method=fallback_exc.request_method,
                    request_url=fallback_exc.request_url,
                ) from fallback_exc

    def events_trigger_legacy(self, body: JsonDict) -> JsonDict:
        """Legacy SDK endpoint (`/api/v1/events/trigger`)."""
        return self._request("POST", "/api/v1/events/trigger", json=body)

    # Subscribers
    def create_subscriber(self, body: JsonDict) -> JsonDict:
        try:
            return self._request("POST", "/v1/subscribers", json=body)
        except SandeshAPIError as exc:
            if exc.status_code != 404:
                raise
            # Backward-compatible fallback for deployments exposing only
            # `/api/v1/subscribers`.
            legacy_body: JsonDict = dict(body or {})
            if "subscriberId" in legacy_body and "subscriber_id" not in legacy_body:
                legacy_body["subscriber_id"] = legacy_body.get("subscriberId")
            if "firstName" in legacy_body and "first_name" not in legacy_body:
                legacy_body["first_name"] = legacy_body.get("firstName")
            if "lastName" in legacy_body and "last_name" not in legacy_body:
                legacy_body["last_name"] = legacy_body.get("lastName")
            return self._request("POST", "/api/v1/subscribers", json=legacy_body)

    def update_subscriber(
        self, subscriber_id: str, body: JsonDict
    ) -> JsonDict:
        return self._request(
            "PATCH", f"/api/v1/subscribers/{subscriber_id}", json=body
        )

    def get_subscriber(self, subscriber_id: str) -> JsonDict:
        return self._request("GET", f"/api/v1/subscribers/{subscriber_id}")

    def list_subscribers(self) -> List[JsonDict]:
        return self._request("GET", "/api/v1/subscribers")

    def deactivate_subscriber(self, subscriber_id: str) -> JsonDict:
        return self._request(
            "PATCH", f"/api/v1/subscribers/{subscriber_id}/deactivate"
        )

    # Notifications
    def get_notifications(
        self,
        *,
        status: Optional[str] = None,
        template_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JsonDict]:
        params: JsonDict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if template_id:
            params["template_id"] = template_id
        if email:
            params["email"] = email
        return self._request("GET", "/api/v1/notifications", params=params)

    def create_notification(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/notifications", json=body)

    def create_notification_v1(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/notifications", json=body)

    def get_notification(self, notification_id: int) -> JsonDict:
        return self._request("GET", f"/api/notifications/{notification_id}")

    def mark_notification_seen(self, notification_id: int) -> JsonDict:
        return self._request(
            "PATCH", f"/api/v1/notifications/{notification_id}/seen"
        )

    def mark_notification_unseen(self, notification_id: int) -> JsonDict:
        return self._request(
            "PATCH", f"/api/v1/notifications/{notification_id}/unseen"
        )

    def retry_notification(self, notification_id: int) -> JsonDict:
        return self._request(
            "POST", f"/api/v1/notifications/{notification_id}/retry"
        )

    def resend_notification(self, notification_id: int) -> JsonDict:
        return self._request(
            "POST", f"/api/v1/notifications/{notification_id}/resend"
        )

    # Integrations
    def integrations_status(self) -> JsonDict:
        return self._request("GET", "/api/v1/integrations/status")

    def integrations_me(self) -> JsonDict:
        return self._request("GET", "/api/v1/integrations/me")

    def integrations_me_update(self, body: JsonDict) -> JsonDict:
        return self._request("PUT", "/api/v1/integrations/me", json=body)

    # Templates
    def list_templates(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False,
    ) -> List[JsonDict]:
        params: JsonDict = {
            "limit": limit,
            "offset": offset,
            "active_only": active_only,
        }
        return self._request("GET", "/api/v1/templates", params=params)

    def create_template(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/templates", json=body)

    def get_template(self, template_id: str) -> JsonDict:
        return self._request("GET", f"/api/templates/{template_id}")

    def update_template(self, template_id: str, body: JsonDict) -> JsonDict:
        return self._request(
            "PUT", f"/api/v1/templates/{template_id}", json=body
        )

    def delete_template(self, template_id: str) -> JsonDict:
        return self._request("DELETE", f"/api/v1/templates/{template_id}")

    def preview_template(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/templates/preview", json=body)

    def validate_template(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/templates/validate", json=body)

    # Credentials
    def list_credentials(
        self, *, channel: Optional[str] = None
    ) -> List[JsonDict]:
        params = {"channel": channel} if channel else None
        return self._request("GET", "/api/v1/credentials", params=params)

    def create_credential(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/credentials", json=body)

    def get_credential(self, cred_id: int) -> JsonDict:
        return self._request("GET", f"/api/v1/credentials/{cred_id}")

    def update_credential(self, cred_id: int, body: JsonDict) -> JsonDict:
        return self._request(
            "PUT", f"/api/v1/credentials/{cred_id}", json=body
        )

    def set_default_credential(self, cred_id: int) -> JsonDict:
        return self._request(
            "PATCH", f"/api/v1/credentials/{cred_id}/set-default"
        )

    def delete_credential(self, cred_id: int) -> JsonDict:
        return self._request("DELETE", f"/api/v1/credentials/{cred_id}")

    # Settings, SES, stats, health
    def get_email_settings(self) -> JsonDict:
        return self._request("GET", "/api/v1/settings/email")

    def update_email_settings(self, body: JsonDict) -> JsonDict:
        return self._request("PUT", "/api/v1/settings/email", json=body)

    def test_email_settings(self, body: JsonDict) -> JsonDict:
        return self._request("POST", "/api/v1/settings/email/test", json=body)

    def get_ses_settings(self) -> JsonDict:
        return self._request("GET", "/api/v1/settings/ses")

    def get_ses_quota(self) -> JsonDict:
        return self._request("GET", "/api/v1/ses/quota")

    def get_verified_emails(self) -> JsonDict:
        return self._request("GET", "/api/v1/verified-emails")

    def verify_email(self, email: str) -> JsonDict:
        return self._request(
            "POST",
            "/api/ses/verify-email",
            params={"email": email},
        )

    def get_stats(self) -> JsonDict:
        return self._request("GET", "/api/v1/stats")

    def health(self) -> JsonDict:
        return self._request("GET", "/health")
