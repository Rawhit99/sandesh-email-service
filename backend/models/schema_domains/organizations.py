import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


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
    def validate_name(cls, value: str) -> str:
        stripped = str(value).strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(stripped) > 255:
            raise ValueError("Organization name is too long")
        return stripped

    @field_validator("org_slug")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = str(value).strip().lower()
        normalized = re.sub(r"[^a-z0-9\-_]", "-", stripped).strip("-")
        if normalized and (len(normalized) < 2 or len(normalized) > 60):
            raise ValueError("Organization ID must be 2-60 characters")
        return normalized or None


class PlatformOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    org_slug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = str(value).strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(stripped) > 255:
            raise ValueError("Organization name is too long")
        return stripped


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
    def validate_org_name(cls, value: str) -> str:
        stripped = str(value).strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(stripped) > 255:
            raise ValueError("Organization name is too long")
        return stripped


class OrganizationUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_org_rename(cls, value: str) -> str:
        stripped = str(value).strip()
        if len(stripped) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(stripped) > 255:
            raise ValueError("Organization name is too long")
        return stripped


class OrganizationMemberOut(BaseModel):
    id: int
    username: str
    organization_role: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
