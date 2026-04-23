"""Per-user integration + email delivery stored on User (JSONB)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config import settings
from models.models import IntegrationCredential, User


def _as_dict(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def merged_integration_settings(user: User) -> Dict[str, str]:
    """Slack/Teams/Firebase/SNS/Twilio strings merged from integration_settings + legacy channel_webhooks."""
    cfg: Dict[str, Any] = {}
    cfg.update(_as_dict(user.integration_settings))
    hooks = _as_dict(user.channel_webhooks)
    for hook_key in ("slack_webhook_url", "teams_webhook_url"):
        cur = (cfg.get(hook_key) or "").strip()
        if not cur:
            v = (hooks.get(hook_key) or "").strip()
            if v:
                cfg[hook_key] = v
    out: Dict[str, str] = {}
    for k, v in cfg.items():
        if isinstance(v, str):
            out[k] = v.strip()
        elif v is not None:
            out[k] = str(v).strip()
    return out


def resolve_named_credential(
    db: Session,
    user_id: int,
    credential_name: str,
) -> Optional[Dict[str, Any]]:
    """Look up a named IntegrationCredential and return its config dict, or None if not found."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.name == credential_name,
        )
        .first()
    )
    if cred is None:
        return None
    result = dict(cred.config or {})
    result["_credential_channel"] = cred.channel
    result["_credential_name"] = cred.name
    return result


def merge_channel_overrides_into_payload(
    db: Session, user_id: Optional[int], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Inject _slack_webhook_url, _teams_*, Twilio/SNS/FCM overrides for auxiliary channels.

    If the payload contains ``credential_name``, the matching IntegrationCredential is looked
    up and its config values are injected alongside the regular JSONB-based overrides.
    """
    out = dict(payload)

    # ── Named credential lookup ──────────────────────────────────────────────
    cred_name = (out.get("credential_name") or "").strip()
    if cred_name and user_id:
        named = resolve_named_credential(db, user_id, cred_name)
        if named:
            channel = named.get("_credential_channel", "")
            cfg = {k: v for k, v in named.items() if not k.startswith("_")}
            # Inject channel-specific keys with the internal _ prefix
            if channel == "aws_ses":
                if cfg.get("aws_access_key_id"):
                    out["_aws_access_key_id"] = cfg["aws_access_key_id"]
                if cfg.get("aws_secret_access_key"):
                    out["_aws_secret_access_key"] = cfg["aws_secret_access_key"]
                if cfg.get("aws_session_token"):
                    out["_aws_session_token"] = cfg["aws_session_token"]
                if cfg.get("aws_region"):
                    out["_aws_region"] = cfg["aws_region"]
                if cfg.get("ses_sender_email"):
                    out["_ses_sender_email"] = cfg["ses_sender_email"]
            elif channel == "sns":
                if cfg.get("aws_access_key_id"):
                    out["_sns_access_key_id"] = cfg["aws_access_key_id"]
                if cfg.get("aws_secret_access_key"):
                    out["_sns_secret_access_key"] = cfg["aws_secret_access_key"]
                if cfg.get("aws_session_token"):
                    out["_sns_session_token"] = cfg["aws_session_token"]
                if cfg.get("aws_region"):
                    out["_sns_region"] = cfg["aws_region"]
                if cfg.get("sns_push_topic_arn"):
                    out["_sns_push_topic_arn"] = cfg["sns_push_topic_arn"]
            elif channel == "slack":
                if cfg.get("webhook_url"):
                    out["_slack_webhook_url"] = cfg["webhook_url"]
            elif channel == "ms_teams":
                if cfg.get("webhook_url"):
                    out["_teams_webhook_url"] = cfg["webhook_url"]
            elif channel == "twilio_whatsapp":
                if cfg.get("account_sid"):
                    out["_twilio_account_sid"] = cfg["account_sid"]
                if cfg.get("auth_token"):
                    out["_twilio_auth_token"] = cfg["auth_token"]
                if cfg.get("from"):
                    out["_twilio_whatsapp_from"] = cfg["from"]
            elif channel == "smtp":
                for k in ("smtp_host", "smtp_port", "smtp_username", "smtp_password", "smtp_from"):
                    if cfg.get(k):
                        out[f"_{k}"] = cfg[k]
            elif channel == "firebase":
                if cfg.get("credentials_path"):
                    out["_firebase_credentials_path"] = cfg["credentials_path"]
    if not user_id:
        return out
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return out
    cfg = merged_integration_settings(user)
    slack = (cfg.get("slack_webhook_url") or "").strip()
    if slack:
        out["_slack_webhook_url"] = slack
    teams = (cfg.get("teams_webhook_url") or "").strip()
    if teams:
        out["_teams_webhook_url"] = teams
    fp = (cfg.get("firebase_credentials_path") or "").strip()
    if fp:
        out["_firebase_credentials_path"] = fp
    topic = (cfg.get("sns_push_topic_arn") or "").strip()
    if topic:
        out["_sns_push_topic_arn"] = topic
    sns_key = (cfg.get("sns_access_key_id") or "").strip()
    sns_secret = (cfg.get("sns_secret_access_key") or "").strip()
    sns_token = (cfg.get("sns_session_token") or "").strip()
    sns_region = (cfg.get("sns_region") or "").strip()
    if sns_key:
        out["_sns_access_key_id"] = sns_key
    if sns_secret:
        out["_sns_secret_access_key"] = sns_secret
    if sns_token:
        out["_sns_session_token"] = sns_token
    if sns_region:
        out["_sns_region"] = sns_region
    sid = (cfg.get("twilio_account_sid") or "").strip()
    tok = (cfg.get("twilio_auth_token") or "").strip()
    frm = (cfg.get("twilio_whatsapp_from") or "").strip()
    if sid:
        out["_twilio_account_sid"] = sid
    if tok:
        out["_twilio_auth_token"] = tok
    if frm:
        out["_twilio_whatsapp_from"] = frm
    return out


def effective_integration_flags(user: Optional[User]) -> Dict[str, Any]:
    """Which integrations are on (user DB and/or server env)."""
    ucfg: Dict[str, str] = merged_integration_settings(user) if user else {}

    def on_slack() -> bool:
        return bool(ucfg.get("slack_webhook_url") or (settings.slack_incoming_webhook_url or "").strip())

    def on_teams() -> bool:
        return bool(ucfg.get("teams_webhook_url") or (settings.ms_teams_incoming_webhook_url or "").strip())

    def on_firebase() -> bool:
        return bool(ucfg.get("firebase_credentials_path") or (settings.firebase_credentials_path or "").strip())

    def on_sns() -> bool:
        return bool(ucfg.get("sns_push_topic_arn") or (settings.sns_push_topic_arn or "").strip())

    def on_twilio() -> bool:
        if all(
            (
                (ucfg.get("twilio_account_sid") or "").strip(),
                (ucfg.get("twilio_auth_token") or "").strip(),
                (ucfg.get("twilio_whatsapp_from") or "").strip(),
            )
        ):
            return True
        return bool(
            (settings.twilio_account_sid or "").strip()
            and (settings.twilio_auth_token or "").strip()
            and (settings.twilio_whatsapp_from or "").strip()
        )

    def on_redis() -> bool:
        return bool((ucfg.get("redis_url") or "").strip() or (settings.redis_url or "").strip())

    def on_email_ses() -> bool:
        ed = merged_email_delivery_settings(user) if user else None
        if ed and str(ed.get("email_provider") or "").lower() == "ses":
            return bool(
                (str(ed.get("ses_sender_email") or "").strip())
                and (str(ed.get("aws_access_key_id") or "").strip())
            )
        return bool(
            settings.email_provider.lower() == "ses"
            and (settings.aws_access_key_id or "").strip()
            and (settings.aws_secret_access_key or "").strip()
            and (settings.ses_sender_email or "").strip()
        )

    def on_email_smtp() -> bool:
        ed = merged_email_delivery_settings(user) if user else None
        if ed and str(ed.get("email_provider") or "").lower() == "smtp":
            return bool(
                (str(ed.get("smtp_host") or "").strip())
                and (str(ed.get("smtp_username") or "").strip())
                and (str(ed.get("smtp_sender_email") or "").strip()
                     or str(ed.get("smtp_username") or "").strip())
            )
        return bool(
            settings.email_provider.lower() == "smtp"
            and (settings.smtp_host or "").strip()
            and (settings.smtp_username or "").strip()
            and (settings.smtp_sender_email or "").strip()
        )

    return {
        "slack_incoming_webhook": on_slack(),
        "ms_teams_incoming_webhook": on_teams(),
        "firebase": on_firebase(),
        "sns": on_sns(),
        "twilio_whatsapp": on_twilio(),
        "redis_queue": on_redis(),
        "subscriber_required": settings.subscriber_required,
        "email_ses": on_email_ses(),
        "email_smtp": on_email_smtp(),
    }


def merged_email_delivery_settings(user: User) -> Optional[Dict[str, Any]]:
    raw = user.email_delivery_settings
    if not isinstance(raw, dict) or not raw.get("email_provider"):
        return None
    return dict(raw)


def mask_email_delivery_for_api(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)
    if out.get("aws_secret_access_key"):
        out["aws_secret_access_key"] = "********"
    if out.get("smtp_password"):
        out["smtp_password"] = "********"
    return out
