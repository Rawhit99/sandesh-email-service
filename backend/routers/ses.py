from fastapi import APIRouter, Depends, HTTPException, Query
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
    try:
        _ = db
        return get_ses_quota_service()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error fetching SES quota information",
        )


@router.post("/ses/verify-email")
async def verify_email_address(
    email: str = Query(..., description="Email address to verify"),
    db: Session = Depends(get_db),
):
    try:
        _ = db
        return verify_email_service(email_service, email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/verified-emails")
async def get_verified_emails(db: Session = Depends(get_db)):
    try:
        _ = db
        return get_verified_emails_service()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Error fetching verified emails. "
                "Please check AWS credentials and permissions."
            ),
        )
