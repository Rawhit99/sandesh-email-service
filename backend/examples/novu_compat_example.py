"""Novu-compatible usage example with Sandesh SDK.

Only imports change:
- from novu.api import EventApi, SubscriberApi
- from novu.dto import SubscriberDto
to:
- from sandesh.api import EventApi, SubscriberApi
- from sandesh.dto import SubscriberDto
"""

from __future__ import annotations

from typing import Any

from requests.models import HTTPError

from sandesh.api import EventApi, SubscriberApi
from sandesh.dto import SubscriberDto


class NovuConfig:
    URL = "https://api.yourdomain.com"
    API_KEY = "YOUR_API_KEY_OR_JWT"
    EMAIL_SENDER_NAME = "Your Team"
    EXTERNAL_MAIL_IDENTIFIER = "external-mail-id"


class NovuException(Exception):
    def __init__(self, message: str, context: dict[str, Any]) -> None:
        super().__init__(message)
        self.context = context


class VendorCollaboratorNotificationsMixin:
    """Collaborator notification wrappers around trigger_event."""

    def vendor_team_invite(self, sub_id, context, override):
        self.trigger_event(
            "vendor-team-invite",
            sub_id,
            context,
            override,
            external=True,
        )

    def vendor_team_invite_accepted(self, sub_id, context, override):
        self.trigger_event(
            "vendor-team-invite-accepted",
            sub_id,
            context,
            override,
        )


class NotificationService(VendorCollaboratorNotificationsMixin):
    def __init__(self, url=None, api_key=None):
        self.url = url or NovuConfig.URL
        self.api_key = api_key or NovuConfig.API_KEY
        self.subscriber_api = SubscriberApi(self.url, self.api_key)
        self.event_api = EventApi(self.url, self.api_key)

    async def create_subscriber(self, sub_id: str, name, email):
        subscriber = SubscriberDto(
            subscriber_id=sub_id,
            first_name=name,
            email=email,
        )
        try:
            self.subscriber_api.create(subscriber)
            return True
        except Exception as exc:
            raise NovuException(
                message="Error creating subscriber",
                context={"subscriber_id": sub_id, "original_error": exc},
            ) from exc

    def trigger_event(
        self,
        name,
        sub_id,
        context,
        override: dict[str, Any] | None = None,
        external: bool = False,
    ):
        override = override or {}
        override.setdefault("email", {})
        override["email"].setdefault(
            "senderName",
            NovuConfig.EMAIL_SENDER_NAME,
        )
        if external and NovuConfig.EXTERNAL_MAIL_IDENTIFIER:
            override["email"].setdefault(
                "integrationIdentifier",
                NovuConfig.EXTERNAL_MAIL_IDENTIFIER,
            )

        try:
            return self.event_api.trigger(
                name=name,
                recipients=sub_id,
                payload=context,
                overrides=override,
            )
        except HTTPError as exc:
            raise NovuException(
                message=f"Error triggering {name} event",
                context={
                    "original_error": exc,
                    "status_code": (
                        exc.response.status_code
                        if getattr(exc, "response", None) is not None
                        else None
                    ),
                },
            ) from exc


if __name__ == "__main__":
    import asyncio

    service = NotificationService()
    asyncio.run(
        service.create_subscriber(
            sub_id="vendor-123",
            name="Rohit",
            email="rohit@example.com",
        )
    )
    service.trigger_event(
        name="vendor-assessment-form-to-vendor",
        sub_id="vendor-123",
        context={
            "organisation": "Acme Corp",
            "vendor_name": "Globex",
            "assessment_name": "Vendor Review",
        },
        override={"email": {"cc": ["risk@example.com"]}},
        external=True,
    )
