from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from config import settings as app_settings
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from services.email_service import EmailService
from services.user_integration import mask_email_delivery_for_api, merged_email_delivery_settings

router = APIRouter(prefix="/api", tags=["settings"])
email_service = EmailService()


@router.get("/v1/settings/ses")
async def get_ses_settings():
    try:
        return {
            "aws_access_key_id": app_settings.aws_access_key_id,
            "aws_region": app_settings.aws_region,
            "ses_sender_email": app_settings.ses_sender_email,
            "ses_configuration_set": app_settings.ses_configuration_set,
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching SES settings")


@router.get("/v1/settings/email")
async def get_email_settings(user: User = Depends(get_scope_tenant_user)):
    """Per-user email delivery (Integrations UI). Legacy path; prefer GET /api/v1/integrations/me."""
    try:
        raw = merged_email_delivery_settings(user)
        if raw:
            return {"success": True, "data": mask_email_delivery_for_api(raw)}
        return {"success": True, "data": {"email_provider": app_settings.email_provider}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/v1/settings/email")
async def update_email_settings(payload: dict, user: User = Depends(get_scope_tenant_user), db: Session = Depends(get_db)):
    try:
        cur = dict(user.email_delivery_settings or {})
        for k, v in payload.items():
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "********":
                continue
            if isinstance(v, str) and not v.strip():
                cur.pop(k, None)
            else:
                cur[k] = v
        prov = str(cur.get("email_provider") or "").lower().strip()
        if prov and prov not in ("ses", "smtp"):
            raise HTTPException(status_code=400, detail="email_provider must be ses or smtp")
        user.email_delivery_settings = cur or None
        db.add(user)
        db.commit()
        return {"success": True, "message": "Settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/settings/email/test")
async def test_email_settings(test_settings: dict):
    try:
        success = email_service.test_email_settings(test_settings)
        if success:
            return {"success": True, "message": "Test successful"}
        else:
            raise HTTPException(status_code=400, detail="Test failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
