from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from sqlalchemy import func
from models.models import get_db, EmailTemplate, Notification, AuditLog
from middleware.auth import get_current_user_optional
from models.schemas import (
    NotificationCreate, NotificationResponse, NotificationUpdate
)
from services.email_service import EmailService

router = APIRouter(prefix="/api", tags=["notifications"])
email_service = EmailService()

@router.get("/v1/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    status: Optional[str] = Query(None, description="Filter by status: pending, success, failed"),
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    email: Optional[str] = Query(None, description="Filter by email"),
    limit: int = Query(100, ge=1, le=1000, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
):
    try:
        notifications = email_service.get_notifications(
            db=db, status=status, template_id=template_id,
            email=email, limit=limit, offset=offset
        )
        return notifications
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_id == notification.template_id
        ).first()
        if not template:
            template = EmailTemplate(
                template_id=notification.template_id,
                name=notification.template_id,
                subject=notification.subject or "No Subject",
                content=notification.content or "",
                is_active=True
            )
            db.add(template)
            db.commit()
            db.refresh(template)

        payload = notification.payload.copy()
        if notification.cc_emails:
            payload['cc_emails'] = notification.cc_emails

        db_notification = Notification(
            template_id=notification.template_id,
            email=notification.email,
            payload=payload,
            status="pending"
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        # Try to capture user if available (optional)
        user = None
        try:
            user = await get_current_user_optional(request, None, db)
        except Exception:
            pass

        audit_log = AuditLog(
            user_id=user.id if user else None,
            action="email_triggered",
            email_to=notification.email,
            template_id=notification.template_id,
            payload=notification.payload,
            status="pending",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(audit_log)
        db.commit()

        await email_service.send_email_async(db, db_notification.id)
        return NotificationResponse.from_orm(db_notification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/v1/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    update_data: NotificationUpdate,
    db: Session = Depends(get_db)
):
    try:
        notification = email_service.update_notification_status(
            db=db, notification_id=notification_id, status=update_data.status
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: Session = Depends(get_db)):
    try:
        notification = email_service.get_notification_by_id(db=db, notification_id=notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/v1/notifications/{notification_id}/retry")
async def retry_notification(notification_id: int, db: Session = Depends(get_db)):
    try:
        success = await email_service.retry_notification(db, notification_id)
        if success:
            return {"message": "Notification retry initiated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retry notification")

@router.post("/v1/notifications/{notification_id}/resend")
async def resend_notification(notification_id: int, db: Session = Depends(get_db)):
    try:
        # Resend uses the same logic as retry
        success = await email_service.retry_notification(db, notification_id)
        if success:
            return {"message": "Notification resend initiated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to resend notification")

