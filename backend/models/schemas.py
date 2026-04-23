from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, JSON, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum
import re

Base = declarative_base()

class NotificationStatus(enum.Enum):
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

    @field_validator('template_id')
    def validate_template_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Template ID cannot be empty")
        return v.strip()

    @field_validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        return v.strip()

    @field_validator('payload')
    def validate_payload(cls, v):
        if v is None:
            raise ValueError("Payload cannot be None")
        return v if isinstance(v, dict) else {}

    @field_validator('cc_emails')
    def validate_cc_emails(cls, v):
        if v and len(v) > 10:
            raise ValueError("Maximum 10 CC emails allowed")
        return v

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
    """SDK-style trigger body (same as notification + optional workflow label)."""

    workflow_name: Optional[str] = Field(default=None, description="Logical workflow name for observability")


class SubscriberCreate(BaseModel):
    subscriber_id: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None


class SubscriberResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    subscriber_id: str
    email: str
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriberUpdate(BaseModel):
    email: Optional[EmailStr] = None
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class IntegrationMeUpdate(BaseModel):
    """Partial update for user-owned integrations (stored in DB). Omitted unchanged; empty string clears."""

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
    def strip_optional(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return v


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


class TemplateBase(BaseModel):
    """Base schema for template operations."""
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject")
    content: str = Field(..., description="HTML content of the template")
    is_active: bool = Field(default=True, description="Whether the template is active")
    default_attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional default attachments [{filename, content_base64, mime_type}]",
    )

class TemplateValidationRequest(TemplateBase):
    """Schema for template validation request."""
    template_id: Optional[str] = None
    variables: Union[Dict[str, str], List[str]] = Field(default=[], description="Template variables")

class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""
    template_id: str = Field(..., description="Unique template identifier provided by user")
    variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")

    @field_validator('template_id')
    def validate_template_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Template ID cannot be empty")
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError("Template ID can only contain letters, numbers, hyphens, and underscores")
        return v.strip()

    @classmethod
    def extract_variables(cls, content: str, subject: str) -> Dict[str, str]:
        """Extract variables from content and subject."""
        variables = set()
        
        # Extract variables from content
        content_vars = re.findall(r'\{\{\s*(\w+)\s*\}\}', content)
        variables.update(content_vars)
        
        # Extract variables from subject
        subject_vars = re.findall(r'\{\{\s*(\w+)\s*\}\}', subject)
        variables.update(subject_vars)
        
        # Convert to dictionary with empty string values
        return {var: "" for var in variables}

    @classmethod
    def from_validation_request(cls, request: TemplateValidationRequest) -> 'TemplateCreate':
        """Convert validation request to create request."""
        variables_dict = {}
        if isinstance(request.variables, list):
            variables_dict = {var: "" for var in request.variables}
        elif isinstance(request.variables, dict):
            variables_dict = request.variables
        
        return cls(
            name=request.name,
            subject=request.subject,
            content=request.content,
            variables=variables_dict,
            is_active=request.is_active
        )

class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: int
    template_id: str
    name: str
    subject: str
    content: str
    variables: Dict[str, str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    preview_url: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    default_attachments: Optional[List[Dict[str, Any]]] = None

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip() if v is not None else v

    @field_validator('subject')
    def validate_subject(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Subject cannot be empty")
        return v.strip() if v is not None else v

    @field_validator('content')
    def validate_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip() if v is not None else v

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

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, index=True)
    email = Column(String)
    payload = Column(JSON)
    executed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.FAILED)

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, unique=True, index=True)
    subject = Column(String)
    body = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class EmailRequest(BaseModel):
    """Email request model with simplified structure."""
    template_id: str
    email: EmailStr
    cc_emails: Optional[List[EmailStr]] = []
    payload: Dict[str, Any]
    
    @field_validator('template_id')
    def validate_template_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Template ID cannot be empty")
        return v.strip()
    
    @field_validator('cc_emails')
    def validate_cc_emails(cls, v):
        if v and len(v) > 10:
            raise ValueError("Maximum 10 CC emails allowed")
        return v or []


class EmailResponse(BaseModel):
    """Email response model."""
    message_id: str
    status: str
    recipient_email: str
    cc_emails: List[str]
    template_id: str
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    aws_region: str
    ses_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TemplateInfo(BaseModel):
    """Template information model."""
    template_id: str
    name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]

class TemplatePreview(BaseModel):
    content: str
    variables: Dict[str, str]

# Authentication Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    organization_name: Optional[str] = None
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Check for alphanumeric characters
        has_alpha = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_alpha and has_digit and has_special):
            raise ValueError("Password must contain at least one letter, one number, and one special character")
        
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    organization_id: Optional[int] = None
    organization_name: Optional[str]
    organization_role: Optional[str] = None
    is_platform_admin: bool = False
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlatformOrganizationOut(BaseModel):
    id: int
    name: str
    org_slug: Optional[str] = None
    service_username: Optional[str] = None
    has_tenant_account: bool = False


class PlatformOrganizationCreate(BaseModel):
    name: str
    org_slug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = str(v).strip()
        if len(s) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(s) > 255:
            raise ValueError("Organization name is too long")
        return s

    @field_validator("org_slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip().lower()
        import re
        s = re.sub(r"[^a-z0-9\-_]", "-", s).strip("-")
        if s and (len(s) < 2 or len(s) > 60):
            raise ValueError("Organization ID must be 2-60 characters")
        return s or None


class PlatformOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    org_slug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        if len(s) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(s) > 255:
            raise ValueError("Organization name is too long")
        return s


class OrganizationSummary(BaseModel):
    id: int
    name: str
    member_count: int


class OrganizationMeResponse(BaseModel):
    has_organization: bool
    my_role: Optional[str] = None
    organization: Optional[OrganizationSummary] = None


class OrganizationCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_org_name(cls, v: str) -> str:
        s = str(v).strip()
        if len(s) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(s) > 255:
            raise ValueError("Organization name is too long")
        return s


class OrganizationUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_org_rename(cls, v: str) -> str:
        s = str(v).strip()
        if len(s) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(s) > 255:
            raise ValueError("Organization name is too long")
        return s


class OrganizationMemberOut(BaseModel):
    id: int
    username: str
    organization_role: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class APIKeyCreate(BaseModel):
    name: Optional[str] = None

class APIKeyResponse(BaseModel):
    id: int
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    id: int
    key: str  # Only returned once when created
    key_prefix: str
    created_at: datetime

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    email_to: Optional[str]
    template_id: Optional[str]
    payload: Optional[Dict[str, Any]]
    status: Optional[str]
    error_message: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ── Integration Credentials ──────────────────────────────────────────────────

SUPPORTED_CHANNELS = [
    "aws_ses", "smtp", "sns", "slack", "ms_teams",
    "firebase", "twilio_whatsapp", "redis_queue",
]


class IntegrationCredentialCreate(BaseModel):
    channel: str
    name: str
    config: Dict[str, Any] = {}
    is_default: bool = False

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        if v not in SUPPORTED_CHANNELS:
            raise ValueError(f"channel must be one of: {', '.join(SUPPORTED_CHANNELS)}")
        return v

    @field_validator("name")
    @classmethod
    def validate_cred_name(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 1 or len(s) > 120:
            raise ValueError("Credential name must be 1–120 characters")
        return s


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


# ── Org Template Scope ──────────────────────────────────────────────────────

class OrgTemplateSettingOut(BaseModel):
    """One template's enabled/disabled status within an organisation context."""
    template_id:   str
    template_name: str
    subject:       str
    is_active:     bool   # template's own active flag
    is_enabled:    bool   # org-level override (True = accessible to this org)

    class Config:
        from_attributes = True


class OrgTemplateSettingUpdate(BaseModel):
    is_enabled: bool


class OrgTemplateBulkUpdate(BaseModel):
    is_enabled:   bool
    template_ids: Optional[List[str]] = None  # None → apply to ALL templates in the org