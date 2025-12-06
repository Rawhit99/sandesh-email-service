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
    SUCCESS = "success"
    FAILED = "failed"

class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""
    template_id: str
    email: EmailStr
    cc_emails: Optional[List[EmailStr]] = None
    payload: Dict[str, Any]
    subject: Optional[str] = None
    content: Optional[str] = None

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
        if not v:
            raise ValueError("Payload cannot be empty")
        return v

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

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    """Schema for updating notification status."""
    status: NotificationStatus

class TemplateBase(BaseModel):
    """Base schema for template operations."""
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject")
    content: str = Field(..., description="HTML content of the template")
    is_active: bool = Field(default=True, description="Whether the template is active")

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

    class Config:
        from_attributes = True

class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

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
        orm_mode = True

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
    organization_name: Optional[str]
    is_active: bool
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