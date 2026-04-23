"""Single entry for creating an email delivery (queue or inline)."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from config import settings
from exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from fastapi import Request
from middleware.tenant_scope import resolve_notification_scope_user
from models.models import (
    AuditLog,
    EmailTemplate,
    Notification,
    OrgTemplateSetting,
    Subscriber,
    User,
)
from models.schema_domains.notifications import (
    NotificationCreate,
    NotificationResponse,
)
from sandesh.infrastructure.queue.publisher import (
    enqueue_email_delivery,
    is_queue_enabled,
)
from sqlalchemy.orm import Session

from services.email_service import EmailService
from services.template_service import resolve_email_template_row

logger = logging.getLogger(__name__)


async def trigger_email_notification(
    *,
    db: Session,
    request: Request,
    notification: NotificationCreate,
    email_service: EmailService,
    current_user: Optional[User],
) -> NotificationResponse:
    scope_user = resolve_notification_scope_user(db, request, current_user)
    uid = scope_user.id if scope_user else None

    if settings.subscriber_required:
        sid = notification.subscriber_external_id
        if not sid:
            raise BadRequestError("subscriber_external_id is required")
        if uid is None:
            raise UnauthorizedError(
                "Authentication required for subscriber-gated sends"
            )
        exists = (
            db.query(Subscriber)
            .filter(
                Subscriber.subscriber_id == sid,
                Subscriber.user_id == uid,
                Subscriber.is_active.is_(True),
            )
            .first()
        )
        if not exists:
            raise NotFoundError("Subscriber not found")

    template = resolve_email_template_row(db, notification.template_id, uid)

    # Org-level template scope check.
    if template and scope_user and scope_user.organization_id:
        scope_setting = (
            db.query(OrgTemplateSetting)
            .filter(
                OrgTemplateSetting.organization_id
                == scope_user.organization_id,
                OrgTemplateSetting.template_id == notification.template_id,
            )
            .first()
        )
        if scope_setting is not None and not scope_setting.is_enabled:
            raise ForbiddenError(
                f"Template '{notification.template_id}' is disabled "
                "for this organisation."
            )

    if not template:
        template = EmailTemplate(
            template_id=notification.template_id,
            name=notification.template_id,
            subject=notification.subject or "No Subject",
            content=notification.content or "",
            variables={},
            is_active=True,
            user_id=uid,
        )
        db.add(template)
        db.commit()
        db.refresh(template)

    run_id = str(uuid.uuid4())
    payload = notification.payload.copy()
    if notification.cc_emails:
        payload["cc_emails"] = notification.cc_emails
    if notification.from_email:
        payload["_from_email"] = notification.from_email
    if notification.sender_name:
        payload["_sender_name"] = notification.sender_name
    if notification.attachments:
        payload["_attachments"] = [
            a.model_dump() for a in notification.attachments
        ]

    channels = notification.channels or ["email"]

    use_queue = is_queue_enabled()
    initial_status = "queued" if use_queue else "pending"
    db_row = Notification(
        template_id=notification.template_id,
        email=str(notification.email),
        payload=payload,
        status=initial_status,
        subscriber_external_id=notification.subscriber_external_id,
        execution_run_id=run_id,
        channels_requested=channels,
        from_email_override=notification.from_email,
        sender_display_name=notification.sender_name,
        attachments=[a.model_dump() for a in notification.attachments]
        if notification.attachments
        else None,
        user_id=uid,
    )
    db.add(db_row)
    db.commit()
    db.refresh(db_row)

    audit_log = AuditLog(
        user_id=uid,
        action="email_triggered",
        email_to=str(notification.email),
        template_id=notification.template_id,
        payload=notification.payload,
        status=db_row.status,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit_log)
    db.commit()

    if not use_queue:
        await email_service.send_email_async(db, db_row.id)
        db.refresh(db_row)
        return NotificationResponse.from_orm(db_row)

    job_id = None
    try:
        job_id = enqueue_email_delivery(db_row.id)
    except (ConnectionError, TimeoutError, OSError, RuntimeError, ValueError):
        logger.exception("Queue enqueue failed")
    if not job_id:
        if settings.queue_inline_fallback:
            db_row.status = "pending"
            db.commit()
            await email_service.send_email_async(db, db_row.id)
        else:
            db_row.status = "failed"
            db_row.error_message = "Queue enqueue failed"
            db.commit()
    db.refresh(db_row)
    return NotificationResponse.from_orm(db_row)
