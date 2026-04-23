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

    def events_trigger(self, body: Dict[str, Any]) -> Dict[str, Any]:
        with self._client() as c:
            r = c.post("/api/v1/events/trigger", json=body)
            r.raise_for_status()
            return r.json()

    def create_subscriber(self, body: Dict[str, Any]) -> Dict[str, Any]:
        with self._client() as c:
            r = c.post("/api/v1/subscribers", json=body)
            r.raise_for_status()
            return r.json()

    def update_subscriber(
        self, subscriber_id: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        with self._client() as c:
            r = c.patch(f"/api/v1/subscribers/{subscriber_id}", json=body)
            r.raise_for_status()
            return r.json()

    def get_subscriber(self, subscriber_id: str) -> Dict[str, Any]:
        with self._client() as c:
            r = c.get(f"/api/v1/subscribers/{subscriber_id}")
            r.raise_for_status()
            return r.json()

    def list_subscribers(self) -> List[Dict[str, Any]]:
        with self._client() as c:
            r = c.get("/api/v1/subscribers")
            r.raise_for_status()
            return r.json()

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
        with self._client() as c:
            r = c.get("/api/v1/notifications", params=params)
            r.raise_for_status()
            return r.json()

    def mark_notification_seen(self, notification_id: int) -> Dict[str, Any]:
        with self._client() as c:
            r = c.patch(f"/api/v1/notifications/{notification_id}/seen")
            r.raise_for_status()
            return r.json()

    def mark_notification_unseen(self, notification_id: int) -> Dict[str, Any]:
        with self._client() as c:
            r = c.patch(f"/api/v1/notifications/{notification_id}/unseen")
            r.raise_for_status()
            return r.json()

    def integrations_status(self) -> Dict[str, Any]:
        with self._client() as c:
            r = c.get("/api/v1/integrations/status")
            r.raise_for_status()
            return r.json()

    def integrations_me(self) -> Dict[str, Any]:
        with self._client() as c:
            r = c.get("/api/v1/integrations/me")
            r.raise_for_status()
            return r.json()

    def integrations_me_update(self, body: Dict[str, Any]) -> Dict[str, Any]:
        with self._client() as c:
            r = c.put("/api/v1/integrations/me", json=body)
            r.raise_for_status()
            return r.json()
