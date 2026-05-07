from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from models.models import Subscriber, User
from models.schema_domains.notifications import (
    AttachmentItem,
    NotificationCreate,
)
from sqlalchemy.orm import Session

from api.contracts.events import EventTriggerRequestV1


def _resolve_recipient_email(
    db: Session,
    subscriber_id: str,
    current_user: Optional[User],
) -> str:
    q = db.query(Subscriber).filter(Subscriber.subscriber_id == subscriber_id)
    if current_user is not None:
        q = q.filter(Subscriber.user_id == current_user.id)
    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return row.email


def to_notification_create(
    db: Session,
    body: EventTriggerRequestV1,
    current_user: Optional[User],
) -> NotificationCreate:
    payload_dict = body.payload.model_dump()
    raw_attachments = payload_dict.pop("attachments", None) or []
    attachments = [
        AttachmentItem(
            filename=item.name,
            content_base64=item.file,
            mime_type=item.mime,
        )
        for item in raw_attachments
    ]

    email_override = body.overrides.email if body.overrides else None
    if email_override and email_override.integrationIdentifier:
        payload_dict["_integration_identifier"] = (
            email_override.integrationIdentifier.strip()
        )
    return NotificationCreate(
        template_id=body.name.strip(),
        email=_resolve_recipient_email(db, body.to.subscriberId, current_user),
        cc_emails=email_override.cc if email_override else None,
        payload=payload_dict,
        subject=email_override.subject if email_override else None,
        subscriber_external_id=body.to.subscriberId.strip(),
        sender_name=email_override.senderName if email_override else None,
        attachments=attachments or None,
    )
