from __future__ import annotations

from config import settings as app_settings
from exceptions import BadRequestError
from models.models import User
from sqlalchemy.orm import Session

from services.email_service import EmailService
from services.user_integration import (
    mask_email_delivery_for_api,
    merged_email_delivery_settings,
)


def get_ses_settings() -> dict:
    return {
        "aws_access_key_id": app_settings.aws_access_key_id,
        "aws_region": app_settings.aws_region,
        "ses_sender_email": app_settings.ses_sender_email,
        "ses_configuration_set": app_settings.ses_configuration_set,
    }


def get_email_settings(user: User) -> dict:
    raw = merged_email_delivery_settings(user)
    if raw:
        return {"success": True, "data": mask_email_delivery_for_api(raw)}
    return {
        "success": True,
        "data": {"email_provider": app_settings.email_provider},
    }


def update_email_settings(db: Session, user: User, payload: dict) -> dict:
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
        raise BadRequestError("email_provider must be ses or smtp")
    user.email_delivery_settings = cur or None
    db.add(user)
    db.commit()
    return {"success": True, "message": "Settings updated successfully"}


def test_email_settings(
    email_service: EmailService, settings_payload: dict
) -> dict:
    if not email_service.test_email_settings(settings_payload):
        raise BadRequestError("Test failed")
    return {"success": True, "message": "Test successful"}
