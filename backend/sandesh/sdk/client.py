"""HTTP SDK for Sandesh API (Bearer token = JWT or API key)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class Sandesh:
    def __init__(
        self, base_url: str, bearer_token: str, timeout: float = 60.0
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base, headers=self._headers, timeout=self._timeout
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        with self._client() as c:
            r = c.request(method, path, params=params, json=json)
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()

    # Events
    def events_trigger(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Strict contract trigger endpoint (`/v1/events/trigger`)."""
        return self._request("POST", "/v1/events/trigger", json=body)

    def events_trigger_legacy(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy SDK endpoint (`/api/v1/events/trigger`)."""
        return self._request("POST", "/api/v1/events/trigger", json=body)

    # Subscribers
    def create_subscriber(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/subscribers", json=body)

    def update_subscriber(
        self, subscriber_id: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "PATCH", f"/api/v1/subscribers/{subscriber_id}", json=body
        )

    def get_subscriber(self, subscriber_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/subscribers/{subscriber_id}")

    def list_subscribers(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/v1/subscribers")

    def deactivate_subscriber(self, subscriber_id: str) -> Dict[str, Any]:
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
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if template_id:
            params["template_id"] = template_id
        if email:
            params["email"] = email
        return self._request("GET", "/api/v1/notifications", params=params)

    def create_notification(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/notifications", json=body)

    def create_notification_v1(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/notifications", json=body)

    def get_notification(self, notification_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/notifications/{notification_id}")

    def mark_notification_seen(self, notification_id: int) -> Dict[str, Any]:
        return self._request(
            "PATCH", f"/api/v1/notifications/{notification_id}/seen"
        )

    def mark_notification_unseen(self, notification_id: int) -> Dict[str, Any]:
        return self._request(
            "PATCH", f"/api/v1/notifications/{notification_id}/unseen"
        )

    def retry_notification(self, notification_id: int) -> Dict[str, Any]:
        return self._request(
            "POST", f"/api/v1/notifications/{notification_id}/retry"
        )

    def resend_notification(self, notification_id: int) -> Dict[str, Any]:
        return self._request(
            "POST", f"/api/v1/notifications/{notification_id}/resend"
        )

    # Integrations
    def integrations_status(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/integrations/status")

    def integrations_me(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/integrations/me")

    def integrations_me_update(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", "/api/v1/integrations/me", json=body)

    # Templates
    def list_templates(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "active_only": active_only,
        }
        return self._request("GET", "/api/v1/templates", params=params)

    def create_template(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/templates", json=body)

    def get_template(self, template_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/templates/{template_id}")

    def update_template(
        self, template_id: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "PUT", f"/api/v1/templates/{template_id}", json=body
        )

    def delete_template(self, template_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/templates/{template_id}")

    def preview_template(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/templates/preview", json=body)

    def validate_template(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/templates/validate", json=body)

    # Credentials
    def list_credentials(
        self, *, channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"channel": channel} if channel else None
        return self._request("GET", "/api/v1/credentials", params=params)

    def create_credential(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/credentials", json=body)

    def get_credential(self, cred_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/credentials/{cred_id}")

    def update_credential(
        self, cred_id: int, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "PUT", f"/api/v1/credentials/{cred_id}", json=body
        )

    def set_default_credential(self, cred_id: int) -> Dict[str, Any]:
        return self._request(
            "PATCH", f"/api/v1/credentials/{cred_id}/set-default"
        )

    def delete_credential(self, cred_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/credentials/{cred_id}")

    # Settings, SES, stats, health
    def get_email_settings(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/settings/email")

    def update_email_settings(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", "/api/v1/settings/email", json=body)

    def test_email_settings(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/settings/email/test", json=body)

    def get_ses_settings(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/settings/ses")

    def get_ses_quota(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/ses/quota")

    def get_verified_emails(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/verified-emails")

    def verify_email(self, email: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/api/ses/verify-email",
            params={"email": email},
        )

    def get_stats(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/stats")

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")
