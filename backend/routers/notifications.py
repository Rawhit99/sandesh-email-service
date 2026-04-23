from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from config import settings
from middleware.auth import get_current_user_optional
from middleware.tenant_scope import get_scope_tenant_user
from middleware.rate_limit import limiter
from models.models import Notification, User, get_db
from models.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from services.email_service import EmailService
from services.notification_trigger import trigger_email_notification

router = APIRouter(prefix="/api", tags=["notifications"])
email_service = EmailService()


def _owned_notification(db: Session, notification_id: int, user: User) -> Notification:
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row


@router.get("/v1/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    status: Optional[str] = Query(
        None, description="Filter by status: pending, queued, running, success, failed"
    ),
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    email: Optional[str] = Query(None, description="Filter by email"),
    limit: int = Query(100, ge=1, le=1000, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        notifications = email_service.get_notifications(
            db=db,
            status=status,
            template_id=template_id,
            email=email,
            limit=limit,
            offset=offset,
            scope_user_id=user.id,
        )
        return notifications
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


async def _create_notification_handler(
    notification: NotificationCreate,
    request: Request,
    db: Session,
    current_user: Optional[User],
) -> NotificationResponse:
    try:
        return await trigger_email_notification(
            db=db,
            request=request,
            notification=notification,
            email_service=email_service,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/notifications", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def create_notification(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return await _create_notification_handler(notification, request, db, current_user)


@router.post("/v1/notifications", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def create_notification_v1(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return await _create_notification_handler(notification, request, db, current_user)


@router.patch("/v1/notifications/{notification_id}/seen")
async def mark_notification_seen(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    row = _owned_notification(db, notification_id, user)
    row.seen_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "notification_id": notification_id}


@router.patch("/v1/notifications/{notification_id}/unseen")
async def mark_notification_unseen(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    row = _owned_notification(db, notification_id, user)
    row.seen_at = None
    db.commit()
    return {"ok": True, "notification_id": notification_id}


@router.put("/v1/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    update_data: NotificationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        notification = email_service.update_notification_status(
            db=db,
            notification_id=notification_id,
            status=update_data.status,
            scope_user_id=user.id,
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        notification = email_service.get_notification_by_id(
            db=db, notification_id=notification_id, scope_user_id=user.id
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/v1/notifications/{notification_id}/retry")
async def retry_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        success = await email_service.retry_notification(db, notification_id, scope_user_id=user.id)
        if success:
            return {"message": "Notification retry initiated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retry notification")


@router.post("/v1/notifications/{notification_id}/resend")
async def resend_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        success = await email_service.retry_notification(db, notification_id, scope_user_id=user.id)
        if success:
            return {"message": "Notification resend initiated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to resend notification")
