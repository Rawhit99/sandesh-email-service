from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class NotificationStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class AttachmentItem(BaseModel):
    filename: str
    content_base64: str
    mime_type: str = "application/octet-stream"


class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""

    template_id: str
    email: EmailStr
    cc_emails: Optional[List[EmailStr]] = None
    payload: Dict[str, Any]
    subject: Optional[str] = None
    content: Optional[str] = None
    subscriber_external_id: Optional[str] = None
    channels: Optional[List[str]] = None
    from_email: Optional[str] = None
    sender_name: Optional[str] = None
    attachments: Optional[List[AttachmentItem]] = None

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Template ID cannot be empty")
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Email cannot be empty")
        return value.strip()

    @field_validator("payload")
    @classmethod
    def validate_payload(
        cls, value: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if value is None:
            raise ValueError("Payload cannot be None")
        return value if isinstance(value, dict) else {}

    @field_validator("cc_emails")
    @classmethod
    def validate_cc_emails(
        cls, value: Optional[List[EmailStr]]
    ) -> Optional[List[EmailStr]]:
        if value and len(value) > 10:
            raise ValueError("Maximum 10 CC emails allowed")
        return value


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: int
    template_id: str
    email: str
    payload: Dict[str, Any]
    executed_at: datetime
    status: NotificationStatus
    execution_run_id: Optional[str] = None
    subscriber_external_id: Optional[str] = None
    seen_at: Optional[datetime] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Schema for updating notification status."""

    status: NotificationStatus


class EventTriggerRequest(NotificationCreate):
    """SDK-style trigger body.

    Same as notification plus an optional workflow label.
    """

    workflow_name: Optional[str] = Field(
        default=None,
        description="Logical workflow name for observability",
    )


class NotificationSummary(BaseModel):
    id: int
    template_id: str
    email: str
    status: str
    created_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_notifications: int
    total_templates: int
    notifications_24h: int
    success_rate: float
    status_counts: Dict[str, int]
    success_count: int
    failed_count: int
    pending_count: int
    recent_notifications: List[NotificationSummary]

    class Config:
        from_attributes = True
