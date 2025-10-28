from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import get_db
from services.email_service import EmailService
from config import settings as app_settings

router = APIRouter(prefix="/api", tags=["settings"])
email_service = EmailService()

@router.get("/v1/settings/ses")
async def get_ses_settings(db: Session = Depends(get_db)):
    try:
        return {
            "aws_access_key_id": app_settings.aws_access_key_id,
            "aws_region": app_settings.aws_region,
            "ses_sender_email": app_settings.ses_sender_email,
            "ses_configuration_set": app_settings.ses_configuration_set
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching SES settings")

@router.post("/settings/ses")
async def update_ses_settings(settings: dict, db: Session = Depends(get_db)):
    try:
        success = email_service.update_ses_settings(settings)
        if success:
            return {"message": "SES settings updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update SES settings")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update SES settings")

@router.post("/settings/ses/test")
async def test_ses_settings(settings: dict, db: Session = Depends(get_db)):
    try:
        success = email_service.test_ses_settings(settings)
        if success:
            return {"message": "SES settings test successful"}
        else:
            raise HTTPException(status_code=400, detail="SES settings test failed")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to test SES settings")

@router.get("/v1/settings/email")
async def get_email_settings():
    try:
        settings = email_service.get_email_settings()
        return {"success": True, "data": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/v1/settings/email")
async def update_email_settings(settings: dict):
    try:
        success = email_service.update_email_settings(settings)
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/v1/settings/email/test")
async def test_email_settings(settings: dict):
    try:
        success = email_service.test_email_settings(settings)
        if success:
            return {"success": True, "message": "Test successful"}
        else:
            raise HTTPException(status_code=400, detail="Test failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


