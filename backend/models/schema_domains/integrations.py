from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator

SUPPORTED_CHANNELS = [
    "aws_ses",
    "smtp",
    "sns",
    "slack",
    "ms_teams",
    "firebase",
    "twilio_whatsapp",
    "redis_queue",
]


class IntegrationMeUpdate(BaseModel):
    """Partial update for user-owned integrations."""

    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    firebase_credentials_path: Optional[str] = None
    sns_push_topic_arn: Optional[str] = None
    sns_access_key_id: Optional[str] = None
    sns_secret_access_key: Optional[str] = None
    sns_session_token: Optional[str] = None
    sns_region: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None
    redis_url: Optional[str] = None
    email_delivery: Optional[Dict[str, Any]] = None

    @field_validator(
        "slack_webhook_url",
        "teams_webhook_url",
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
        mode="before",
    )
    @classmethod
    def strip_optional(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class IntegrationEnvStatus(BaseModel):
    slack_incoming_webhook: bool
    ms_teams_incoming_webhook: bool
    firebase: bool
    sns: bool
    twilio_whatsapp: bool
    redis_queue: bool
    subscriber_required: bool
    email_ses: bool
    email_smtp: bool


class IntegrationMeResponse(BaseModel):
    slack_user_configured: bool
    slack_user_hint: Optional[str] = None
    teams_user_configured: bool
    teams_user_hint: Optional[str] = None
    environment: IntegrationEnvStatus
    email_delivery: Optional[Dict[str, Any]] = None


class IntegrationCredentialCreate(BaseModel):
    channel: str
    name: str
    config: Dict[str, Any] = {}
    is_default: bool = False

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, value: str) -> str:
        if value not in SUPPORTED_CHANNELS:
            allowed = ", ".join(SUPPORTED_CHANNELS)
            raise ValueError(f"channel must be one of: {allowed}")
        return value

    @field_validator("name")
    @classmethod
    def validate_cred_name(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 1 or len(stripped) > 120:
            raise ValueError("Credential name must be 1-120 characters")
        return stripped


class IntegrationCredentialUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class IntegrationCredentialOut(BaseModel):
    id: int
    channel: str
    name: str
    config: Dict[str, Any]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
