"""Compatibility re-export module for all Pydantic schemas."""

from models.schema_domains.access import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    AuditLogResponse,
)
from models.schema_domains.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from models.schema_domains.integrations import (
    SUPPORTED_CHANNELS,
    IntegrationCredentialCreate,
    IntegrationCredentialOut,
    IntegrationCredentialUpdate,
    IntegrationEnvStatus,
    IntegrationMeResponse,
    IntegrationMeUpdate,
)
from models.schema_domains.notifications import (
    AttachmentItem,
    EventTriggerRequest,
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationSummary,
    NotificationUpdate,
    StatsResponse,
)
from models.schema_domains.organizations import (
    OrganizationCreate,
    OrganizationMemberOut,
    OrganizationMeResponse,
    OrganizationSummary,
    OrganizationUpdate,
    PlatformOrganizationCreate,
    PlatformOrganizationOut,
    PlatformOrganizationUpdate,
)
from models.schema_domains.org_template_scope import (
    OrgTemplateBulkUpdate,
    OrgTemplateSettingOut,
    OrgTemplateSettingUpdate,
)
from models.schema_domains.subscribers import (
    SubscriberCreate,
    SubscriberResponse,
    SubscriberUpdate,
)
from models.schema_domains.templates import (
    TemplateBase,
    TemplateCreate,
    TemplatePreview,
    TemplateResponse,
    TemplateUpdate,
    TemplateValidationRequest,
)

__all__ = [
    "APIKeyCreate",
    "APIKeyCreateResponse",
    "APIKeyResponse",
    "AttachmentItem",
    "AuditLogResponse",
    "EventTriggerRequest",
    "IntegrationCredentialCreate",
    "IntegrationCredentialOut",
    "IntegrationCredentialUpdate",
    "IntegrationEnvStatus",
    "IntegrationMeResponse",
    "IntegrationMeUpdate",
    "LoginRequest",
    "LoginResponse",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationStatus",
    "NotificationSummary",
    "NotificationUpdate",
    "OrgTemplateBulkUpdate",
    "OrgTemplateSettingOut",
    "OrgTemplateSettingUpdate",
    "OrganizationCreate",
    "OrganizationMemberOut",
    "OrganizationMeResponse",
    "OrganizationSummary",
    "OrganizationUpdate",
    "PlatformOrganizationCreate",
    "PlatformOrganizationOut",
    "PlatformOrganizationUpdate",
    "StatsResponse",
    "SubscriberCreate",
    "SubscriberResponse",
    "SubscriberUpdate",
    "SUPPORTED_CHANNELS",
    "TemplateBase",
    "TemplateCreate",
    "TemplatePreview",
    "TemplateResponse",
    "TemplateUpdate",
    "TemplateValidationRequest",
    "UserCreate",
    "UserResponse",
]
