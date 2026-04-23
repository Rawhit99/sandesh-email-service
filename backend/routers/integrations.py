"""Integration status and per-user DB-backed settings (Slack, Teams, FCM, SNS, Twilio, email delivery)."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schemas import IntegrationEnvStatus, IntegrationMeResponse, IntegrationMeUpdate
from services.user_integration import (
    effective_integration_flags,
    mask_email_delivery_for_api,
    merged_email_delivery_settings,
    merged_integration_settings,
)

router = APIRouter(prefix="/api/v1", tags=["integrations"])


def _env_ses_ready() -> bool:
    return settings.email_provider.lower() == "ses" and bool(
        (settings.aws_access_key_id or "").strip()
        and (settings.aws_secret_access_key or "").strip()
        and (settings.ses_sender_email or "").strip()
    )


def _env_smtp_ready() -> bool:
    return settings.email_provider.lower() == "smtp" and bool(
        (settings.smtp_host or "").strip()
        and (settings.smtp_username or "").strip()
        and (settings.smtp_sender_email or "").strip()
    )


def _env_status_dict() -> Dict[str, Any]:
    """Server defaults only (no user row)."""
    return {
        "slack_incoming_webhook": bool((settings.slack_incoming_webhook_url or "").strip()),
        "ms_teams_incoming_webhook": bool((settings.ms_teams_incoming_webhook_url or "").strip()),
        "firebase": bool((settings.firebase_credentials_path or "").strip()),
        "sns": bool((settings.sns_push_topic_arn or "").strip()),
        "twilio_whatsapp": bool(
            (settings.twilio_account_sid or "").strip()
            and (settings.twilio_auth_token or "").strip()
            and (settings.twilio_whatsapp_from or "").strip()
        ),
        "redis_queue": bool((settings.redis_url or "").strip()),
        "subscriber_required": settings.subscriber_required,
        "email_ses": _env_ses_ready(),
        "email_smtp": _env_smtp_ready(),
    }


def _hint(url: str) -> Optional[str]:
    u = (url or "").strip()
    if len(u) <= 4:
        return None
    tail = u[-12:] if len(u) > 12 else u[-4:]
    return f"…{tail}"


def _as_hooks(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}


@router.get("/integrations/status")
def get_integration_status() -> dict:
    return _env_status_dict()


@router.get("/integrations/me", response_model=IntegrationMeResponse)
def get_integration_me(user: User = Depends(get_scope_tenant_user)):
    cfg = merged_integration_settings(user)
    slack_u = (cfg.get("slack_webhook_url") or "").strip()
    teams_u = (cfg.get("teams_webhook_url") or "").strip()
    eff = effective_integration_flags(user)
    email_raw = merged_email_delivery_settings(user)
    email_masked = mask_email_delivery_for_api(email_raw) if email_raw else None
    return IntegrationMeResponse(
        slack_user_configured=bool(slack_u),
        slack_user_hint=_hint(slack_u),
        teams_user_configured=bool(teams_u),
        teams_user_hint=_hint(teams_u),
        environment=IntegrationEnvStatus(**eff),
        email_delivery=email_masked,
    )


def _apply_integration_settings_merge(user: User, key: str, value: Optional[str]) -> None:
    cur = dict(user.integration_settings or {})
    if value is None:
        return
    v = value.strip() if isinstance(value, str) else str(value).strip()
    if not v:
        cur.pop(key, None)
    else:
        cur[key] = v
    user.integration_settings = cur or None


@router.put("/integrations/me", response_model=IntegrationMeResponse)
def put_integration_me(
    body: IntegrationMeUpdate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    hooks = dict(_as_hooks(user.channel_webhooks))

    for url_key in ("slack_webhook_url", "teams_webhook_url"):
        if url_key not in data:
            continue
        val = data[url_key]
        if val is None:
            continue
        if val == "":
            hooks.pop(url_key, None)
            _apply_integration_settings_merge(user, url_key, "")
            continue
        if not str(val).startswith("https://"):
            raise HTTPException(status_code=400, detail=f"{url_key} must be an https URL")
        s = str(val).strip()
        hooks[url_key] = s
        _apply_integration_settings_merge(user, url_key, s)

    for key in (
        "firebase_credentials_path",
        "sns_push_topic_arn",
        "sns_access_key_id",
        "sns_secret_access_key",
        "sns_session_token",
        "sns_region",
        "twilio_account_sid",
        "twilio_auth_token",
        "twilio_whatsapp_from",
        "redis_url",
    ):
        if key not in data:
            continue
        val = data[key]
        if val is None:
            continue
        if val == "":
            _apply_integration_settings_merge(user, key, "")
        else:
            _apply_integration_settings_merge(user, key, str(val).strip())

    if "email_delivery" in data and data["email_delivery"] is not None:
        patch = data["email_delivery"]
        if not isinstance(patch, dict):
            raise HTTPException(status_code=400, detail="email_delivery must be an object")
        cur = dict(user.email_delivery_settings or {})
        for k, v in patch.items():
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

    user.channel_webhooks = hooks or {}
    db.add(user)
    db.commit()
    db.refresh(user)

    return get_integration_me(user)
