from exceptions import ValidationError
from fastapi import APIRouter, Depends, Query
from models.models import get_db
from services.email_service import EmailService
from services.ses_service import (
    get_ses_quota as get_ses_quota_service,
)
from services.ses_service import (
    get_verified_emails as get_verified_emails_service,
)
from services.ses_service import (
    verify_email as verify_email_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["ses"])
email_service = EmailService()


@router.get("/v1/ses/quota")
async def get_ses_quota(db: Session = Depends(get_db)):
    _ = db
    return get_ses_quota_service()


@router.post("/ses/verify-email")
async def verify_email_address(
    email: str = Query(..., description="Email address to verify"),
    db: Session = Depends(get_db),
):
    _ = db
    try:
        return verify_email_service(email_service, email)
    except ValueError as exc:
        raise ValidationError(str(exc))


@router.get("/v1/verified-emails")
async def get_verified_emails(db: Session = Depends(get_db)):
    _ = db
    return get_verified_emails_service()
