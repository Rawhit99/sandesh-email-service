from typing import Optional

from api.contracts.events import EventTriggerRequestV1
from config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from middleware.auth import get_current_user_optional
from middleware.rate_limit import limiter
from models.models import User, get_db
from models.schema_domains.notifications import (
    EventTriggerRequest,
    NotificationResponse,
)
from services.email_service import EmailService
from services.event_service import trigger_event_v1
from services.notification_trigger import trigger_email_notification
from sqlalchemy.orm import Session

router = APIRouter(tags=["events"])
email_service = EmailService()


@router.post("/api/v1/events/trigger", response_model=NotificationResponse)
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


@router.post("/v1/events/trigger", response_model=NotificationResponse)
@limiter.limit(settings.rate_limit_send)
async def trigger_event_contract_v1(
    body: EventTriggerRequestV1,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Strict event trigger contract: name/to/payload/overrides."""
    try:
        return await trigger_event_v1(
            db=db,
            request=request,
            body=body,
            current_user=current_user,
            email_service=email_service,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
