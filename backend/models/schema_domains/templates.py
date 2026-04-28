import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class TemplateBase(BaseModel):
    """Base schema for template operations."""

    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject")
    content: str = Field(..., description="HTML content of the template")
    is_active: bool = Field(
        default=True, description="Whether the template is active"
    )
    default_attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional default attachments "
            "[{filename, content_base64, mime_type}]"
        ),
    )


class TemplateValidationRequest(TemplateBase):
    """Schema for template validation request."""

    template_id: Optional[str] = None
    variables: Union[Dict[str, str], List[str]] = Field(
        default=[],
        description="Template variables",
    )


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""

    template_id: str = Field(
        ...,
        description="Unique template identifier provided by user",
    )
    variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Template variables",
    )

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Template ID cannot be empty")
        if not re.match(r"^[a-zA-Z0-9_-]+$", value.strip()):
            raise ValueError(
                "Template ID can only contain letters, numbers, "
                "hyphens, and underscores"
            )
        return value.strip()

    @classmethod
    def extract_variables(cls, content: str, subject: str) -> Dict[str, str]:
        variables = set()
        content_vars = re.findall(r"\{\{\s*(\w+)\s*\}\}", content)
        variables.update(content_vars)
        subject_vars = re.findall(r"\{\{\s*(\w+)\s*\}\}", subject)
        variables.update(subject_vars)
        return {var: "" for var in variables}

    @classmethod
    def from_validation_request(
        cls, request: TemplateValidationRequest
    ) -> "TemplateCreate":
        variables_dict: Dict[str, str] = {}
        if isinstance(request.variables, list):
            variables_dict = {var: "" for var in request.variables}
        elif isinstance(request.variables, dict):
            variables_dict = request.variables

        return cls(
            name=request.name,
            subject=request.subject,
            content=request.content,
            variables=variables_dict,
            is_active=request.is_active,
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Name cannot be empty")
        return value.strip() if value is not None else value

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Subject cannot be empty")
        return value.strip() if value is not None else value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Content cannot be empty")
        return value.strip() if value is not None else value


class TemplatePreview(BaseModel):
    content: str
    variables: Dict[str, str]
