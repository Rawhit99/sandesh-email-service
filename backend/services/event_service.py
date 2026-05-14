from __future__ import annotations

from typing import Optional

from api.contracts.events import EventTriggerRequestV1
from api.mappers.event_mapper import (
    infer_email_for_v1_trigger,
    to_notification_create,
)
from config import settings
from fastapi import Request
from middleware.tenant_scope import resolve_notification_scope_user
from models.models import Subscriber, User
from models.schema_domains.notifications import NotificationResponse
from sqlalchemy.orm import Session

from services.email_service import EmailService
from services.notification_trigger import trigger_email_notification
from services.subscriber_service import ensure_subscriber_for_send


async def trigger_event_v1(
    *,
    db: Session,
    request: Request,
    body: EventTriggerRequestV1,
    current_user: Optional[User],
    email_service: EmailService,
) -> NotificationResponse:
    scope_user = resolve_notification_scope_user(db, request, current_user)
    if settings.subscriber_required and scope_user:
        sid = body.to.subscriberId.strip()
        exists = (
            db.query(Subscriber)
            .filter(
                Subscriber.subscriber_id == sid,
                Subscriber.user_id == scope_user.id,
                Subscriber.is_active.is_(True),
            )
            .first()
        )
        if not exists:
            inferred = infer_email_for_v1_trigger(body)
            if inferred:
                ensure_subscriber_for_send(
                    db,
                    scope_user,
                    subscriber_id=sid,
                    email=inferred,
                )
    notification = to_notification_create(db, body, scope_user)
    return await trigger_email_notification(
        db=db,
        request=request,
        notification=notification,
        email_service=email_service,
        current_user=current_user,
    )
