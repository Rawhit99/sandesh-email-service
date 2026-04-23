from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Request
from models.models import Notification, User
from models.schema_domains.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from sqlalchemy.orm import Session

from services.email_service import EmailService
from services.notification_trigger import trigger_email_notification


def list_notifications(
    *,
    email_service: EmailService,
    db: Session,
    user: User,
    status: Optional[str],
    template_id: Optional[str],
    email: Optional[str],
    limit: int,
    offset: int,
) -> List[NotificationResponse]:
    return email_service.get_notifications(
        db=db,
        status=status,
        template_id=template_id,
        email=email,
        limit=limit,
        offset=offset,
        scope_user_id=user.id,
    )


async def create_notification(
    *,
    email_service: EmailService,
    db: Session,
    request: Request,
    notification: NotificationCreate,
    current_user: Optional[User],
) -> NotificationResponse:
    return await trigger_email_notification(
        db=db,
        request=request,
        notification=notification,
        email_service=email_service,
        current_user=current_user,
    )


def _owned_notification(
    db: Session,
    notification_id: int,
    user: User,
) -> Notification:
    row = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row


def mark_seen(db: Session, user: User, notification_id: int) -> dict:
    row = _owned_notification(db, notification_id, user)
    row.seen_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "notification_id": notification_id}


def mark_unseen(db: Session, user: User, notification_id: int) -> dict:
    row = _owned_notification(db, notification_id, user)
    row.seen_at = None
    db.commit()
    return {"ok": True, "notification_id": notification_id}


def update_notification_status(
    *,
    email_service: EmailService,
    db: Session,
    user: User,
    notification_id: int,
    update_data: NotificationUpdate,
) -> NotificationResponse:
    row = email_service.update_notification_status(
        db=db,
        notification_id=notification_id,
        status=update_data.status,
        scope_user_id=user.id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row


def get_notification(
    *,
    email_service: EmailService,
    db: Session,
    user: User,
    notification_id: int,
) -> NotificationResponse:
    row = email_service.get_notification_by_id(
        db=db,
        notification_id=notification_id,
        scope_user_id=user.id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row


async def retry_notification(
    *,
    email_service: EmailService,
    db: Session,
    user: User,
    notification_id: int,
) -> dict:
    ok = await email_service.retry_notification(
        db,
        notification_id,
        scope_user_id=user.id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification retry initiated successfully"}
