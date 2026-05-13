from typing import Any
from sandesh.api import EventApi, SubscriberApi
from sandesh.dto import SubscriberDto
from requests.models import HTTPError
from utils.config import NovuConfig
from logging import getLogger

from utils.debug import dprint
from utils.exceptions.common import NovuException

logger = getLogger(__name__)


class VendorCollaboratorNotificationsMixin:
    """Novu event triggers for vendor team collaboration.
    SRP: all collaborator notifications in one place.
    OCP: NotificationService is extended, not modified."""

    def vendor_team_invite(self, sub_id, context, override):
        """Send invitation email to a new vendor team member."""
        self.trigger_event(
            "vendor-team-invite", sub_id, context, override, external=True
        )  # type: ignore[attr-defined]

    def vendor_team_invite_accepted(self, sub_id, context, override):
        """Notify the inviter that their invite was accepted."""
        self.trigger_event("vendor-team-invite-accepted", sub_id, context, override)  # type: ignore[attr-defined]

    def vendor_member_removed(self, sub_id, context, override):
        """Notify a vendor team member that they were removed."""
        self.trigger_event(
            "vendor-member-removed", sub_id, context, override, external=True
        )  # type: ignore[attr-defined]

    def vendor_member_mention(self, sub_id, context, override):
        """Notify a vendor team member they were @mentioned in an internal comment."""
        self.trigger_event(
            "vendor-internal-mention", sub_id, context, override, external=True
        )  # type: ignore[attr-defined]

    def vendor_team_deadline_reminder(self, sub_id, context, override):
        """Remind vendor team of an approaching assessment deadline."""
        self.trigger_event(
            "vendor-team-deadline", sub_id, context, override, external=True
        )


class NotificationService(VendorCollaboratorNotificationsMixin):
    def __init__(self, url=None, api_key=None):
        self.url = url or NovuConfig.URL
        self.api_key = api_key or NovuConfig.API_KEY
        self.subscriber_api = SubscriberApi(self.url, self.api_key)
        self.event_api = EventApi(self.url, self.api_key)

    async def create_subscriber(
        self, sub_id: str, name, email, device_tokens: list[str] | None = None
    ):
        subscriber_instance = SubscriberDto(
            subscriber_id=sub_id, first_name=name, email=email
        )
        try:
            _ = self.subscriber_api.create(subscriber_instance)
            if device_tokens:
                await self.update_subscriber_fcm_credentials(sub_id, device_tokens)
            return True
        except Exception as e:
            raise NovuException(
                message="Error creating subscriber",
                context={"subscriber_id": sub_id, "original_error": e},
            ) from e

    async def delete_subscriber(self, sub_id):
        try:
            self.subscriber_api.delete(sub_id)
        except Exception as e:
            raise NovuException(
                message="Error deleting subscriber",
                context={"subscriber_id": sub_id, "original_error": e},
            ) from e

    async def update_subscriber_fcm_credentials(
        self, subscriber_id, device_tokens: list[str]
    ):
        try:
            if not all(isinstance(token, str) and token for token in device_tokens):
                raise ValueError("Invalid device tokens provided")
            self.subscriber_api.credentials(
                subscriber_id=subscriber_id,
                provider_id="fcm",
                device_tokens=device_tokens,
            )
            return True
        except Exception as e:
            raise NovuException(
                "Error updating FCM credentials", context={"original_error": e}
            ) from e

    async def remove_device_token(self, subscriber_id: str, device_token: str) -> bool:
        try:
            subscriber = self.subscriber_api.get(subscriber_id)
            fcm_channels = [
                channel
                for channel in subscriber._channels
                if channel.provider_id == "fcm"
            ]
            if not fcm_channels:
                dprint(f"No FCM channels found for subscriber {subscriber_id}")
                return False
            fcm_channel = fcm_channels[0]

            current_tokens = fcm_channel.credentials.device_tokens
            if device_token not in current_tokens:
                dprint(f"Device token {device_token} not found in current tokens")
                return False

            updated_tokens = [
                token for token in current_tokens if token != device_token
            ]
            self.subscriber_api.credentials(
                subscriber_id=subscriber_id,
                provider_id="fcm",
                device_tokens=updated_tokens,
            )
            return True
        except Exception as e:
            raise NovuException(
                message="Error deleting device token", context={"original_error": e}
            ) from e

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
        override["email"].setdefault("senderName", NovuConfig.EMAIL_SENDER_NAME)
        if external and (emi := NovuConfig.EXTERNAL_MAIL_IDENTIFIER):
            override["email"].setdefault("integrationIdentifier", emi)

        try:
            event = self.event_api.trigger(
                name=name,
                recipients=sub_id,
                payload=context,
                overrides=override,
            )

            return event
        except HTTPError as e:
            raise NovuException(
                message=f"error triggering {name} event",
                context={
                    "original_error": e,
                    "API response status code": e.response.status_code,
                },
            ) from e

    def send_vendor_assigned(self, sub_id, context, override):
        self.trigger_event("vendor-assigned", sub_id, context, override)

    def vendor_spoc_assigned(self, sub_id, context, override):
        self.trigger_event(
            "vendor-spoc-assignment", sub_id, context, override, external=True
        )

    def vendor_assessment_form_to_vendor(self, sub_id, context, override):
        self.trigger_event(
            "vendor-assessment-form-to-vendor", sub_id, context, override, external=True
        )

    def vendor_risk_assessment_form_to_vendor(self, sub_id, context, override):
        self.trigger_event(
            "vendor-risk-assessment-form-to-vendor",
            sub_id,
            context,
            override,
            external=True,
        )

    def vendor_onboarding_rejected(self, sub_id, context, override):
        self.trigger_event(
            "vendor-onboarding-rejected", sub_id, context, override, external=True
        )

    def vendor_onboarded(self, sub_id, context, override):
        self.trigger_event("vendor-onboarded", sub_id, context, override, external=True)

    def risk_created(self, sub_id, context, override):
        self.trigger_event("risk-created", sub_id, context, override)

    def risk_due_reminder(self, sub_id, context, override):
        self.trigger_event("risk-due-reminder", sub_id, context, override)

    def on_submit_assessment_vendor(self, sub_id, context, override):
        self.trigger_event("assessment-submit", sub_id, context, override)

    def on_submit_risk_assessment_vendor(self, sub_id, context, override):
        self.trigger_event("risk-evaluation-submit", sub_id, context, override)

    def vendor_assessment_otp(self, sub_id, context, override):
        self.trigger_event(
            "send-assessment-otp", sub_id, context, override, external=True
        )

    def vendor_team_member_otp(self, sub_id, context, override):
        """Send OTP to vendor team member. Reuses send-assessment-otp workflow (same content)."""
        self.trigger_event(
            "send-assessment-otp", sub_id, context, override, external=True
        )

    def vendor_risk_assessment_otp(self, sub_id, context, override):
        self.trigger_event(
            "send-risk-assessment-otp", sub_id, context, override, external=True
        )

    def vendor_assessment_review(self, sub_id, context, override):
        self.trigger_event(
            "assessment-review", sub_id, context, override, external=True
        )

    def vendor_detailed_report(self, sub_id, context, override):
        self.trigger_event("vendor-detailed-report", sub_id, context, override)

    def send_vendor_updated(self, sub_id, context, override):
        self.trigger_event("vendor-updated", sub_id, context, override)

    def vendor_document_approval_status(self, sub_id, context, override):
        self.trigger_event(
            "vendor-document-approval-status", sub_id, context, override, external=True
        )

    def comment_mention(self, sub_id, context, override):
        """Send notification to mentioned users in internal comments"""
        self.trigger_event(
            "comment-mention",
            sub_id,
            context,
            override=override,
        )

    def vendor_comment_external(self, sub_id, context, override):
        """Send notification to vendor SPOC for external comments"""
        self.trigger_event(
            "vendor-comment-external",
            sub_id,
            context,
            override=override,
            external=True,
        )
