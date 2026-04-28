from __future__ import annotations

from typing import Optional

from api.contracts.events import EventTriggerRequestV1
from api.mappers.event_mapper import to_notification_create
from fastapi import Request
from models.models import User
from models.schema_domains.notifications import NotificationResponse
from sqlalchemy.orm import Session

from services.email_service import EmailService
from services.notification_trigger import trigger_email_notification


async def trigger_event_v1(
    *,
    db: Session,
    request: Request,
    body: EventTriggerRequestV1,
    current_user: Optional[User],
    email_service: EmailService,
) -> NotificationResponse:
    notification = to_notification_create(db, body, current_user)
    return await trigger_email_notification(
        db=db,
        request=request,
        notification=notification,
        email_service=email_service,
        current_user=current_user,
    )
