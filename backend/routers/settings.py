from fastapi import APIRouter, Depends, HTTPException
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from services.email_service import EmailService
from services.settings_service import (
    get_email_settings as get_email_settings_service,
)
from services.settings_service import (
    get_ses_settings as get_ses_settings_service,
)
from services.settings_service import (
    test_email_settings as test_email_settings_service,
)
from services.settings_service import (
    update_email_settings as update_email_settings_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["settings"])
email_service = EmailService()


@router.get("/v1/settings/ses")
async def get_ses_settings():
    try:
        return get_ses_settings_service()
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching SES settings")


@router.get("/v1/settings/email")
async def get_email_settings(user: User = Depends(get_scope_tenant_user)):
    """Per-user email delivery (Integrations UI). Legacy path; prefer GET /api/v1/integrations/me."""
    try:
        return get_email_settings_service(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/v1/settings/email")
async def update_email_settings(
    payload: dict,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    try:
        return update_email_settings_service(db, user, payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/settings/email/test")
async def test_email_settings(test_settings: dict):
    try:
        return test_email_settings_service(email_service, test_settings)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
