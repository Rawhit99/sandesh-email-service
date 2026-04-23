from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from middleware.auth import get_current_user_optional
from middleware.rate_limit import limiter
from models.models import User, get_db
from models.schemas import EventTriggerRequest, NotificationResponse
from services.email_service import EmailService
from services.notification_trigger import trigger_email_notification

router = APIRouter(prefix="/api", tags=["events"])
email_service = EmailService()


@router.post("/v1/events/trigger", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def trigger_event(
    body: EventTriggerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """SDK-style entrypoint; same semantics as POST /api/notifications."""
    try:
        return await trigger_email_notification(
            db=db,
            request=request,
            notification=body,
            email_service=email_service,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
