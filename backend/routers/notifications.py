from typing import List, Optional

from config import settings
from fastapi import APIRouter, Depends, Query, Request
from middleware.auth import get_current_user_optional
from middleware.rate_limit import limiter
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from services.email_service import EmailService
from services.notification_service import (
    create_notification as create_notification_service,
)
from services.notification_service import (
    get_notification as get_notification_service,
)
from services.notification_service import (
    list_notifications,
    mark_seen,
    mark_unseen,
    update_notification_status,
)
from services.notification_service import (
    retry_notification as retry_notification_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["notifications"])
email_service = EmailService()


@router.get("/v1/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    status: Optional[str] = Query(
        None,
        description=("Filter by status: pending, queued, running, success, failed"),
    ),
    template_id: Optional[str] = Query(
        None,
        description="Filter by template ID",
    ),
    email: Optional[str] = Query(None, description="Filter by email"),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Number of notifications to return",
    ),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return list_notifications(
        email_service=email_service,
        db=db,
        user=user,
        status=status,
        template_id=template_id,
        email=email,
        limit=limit,
        offset=offset,
    )


@router.post("/notifications", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def create_notification(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return await create_notification_service(
        email_service=email_service,
        db=db,
        request=request,
        notification=notification,
        current_user=current_user,
    )


@router.post("/v1/notifications", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def create_notification_v1(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    return await create_notification_service(
        email_service=email_service,
        db=db,
        request=request,
        notification=notification,
        current_user=current_user,
    )


@router.patch("/v1/notifications/{notification_id}/seen")
async def mark_notification_seen(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return mark_seen(db, user, notification_id)


@router.patch("/v1/notifications/{notification_id}/unseen")
async def mark_notification_unseen(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return mark_unseen(db, user, notification_id)


@router.put(
    "/v1/notifications/{notification_id}",
    response_model=NotificationResponse,
)
async def update_notification(
    notification_id: int,
    update_data: NotificationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return update_notification_status(
        email_service=email_service,
        db=db,
        user=user,
        notification_id=notification_id,
        update_data=update_data,
    )


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return get_notification_service(
        email_service=email_service,
        db=db,
        user=user,
        notification_id=notification_id,
    )


@router.post("/v1/notifications/{notification_id}/retry")
async def retry_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return await retry_notification_service(
        email_service=email_service,
        db=db,
        user=user,
        notification_id=notification_id,
    )


@router.post("/v1/notifications/{notification_id}/resend")
async def resend_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return await retry_notification_service(
        email_service=email_service,
        db=db,
        user=user,
        notification_id=notification_id,
    )
