from __future__ import annotations

from exceptions import NotFoundError
from models.schema_domains.templates import (
    TemplateCreate,
    TemplatePreview,
    TemplateResponse,
    TemplateUpdate,
)
from sqlalchemy.orm import Session

from services.template_service import TemplateService


def list_templates(
    template_service: TemplateService,
    db: Session,
    user_id: int,
    limit: int,
    offset: int,
    active_only: bool,
) -> list[TemplateResponse]:
    return template_service.get_templates(
        db=db,
        limit=limit,
        offset=offset,
        active_only=active_only,
        scope_user_id=user_id,
    )


def preview_template(
    template_service: TemplateService,
    body: TemplatePreview,
) -> dict:
    return {
        "preview": template_service.preview_template(
            body.content, body.variables
        )
    }


def validate_template(
    template_service: TemplateService,
    body: TemplateCreate,
) -> dict:
    body.variables = TemplateCreate.extract_variables(
        body.content, body.subject
    )
    return template_service.validate_template_syntax(body.content)


def create_template(
    template_service: TemplateService,
    db: Session,
    user_id: int,
    body: TemplateCreate,
) -> TemplateResponse:
    body.variables = TemplateCreate.extract_variables(
        body.content, body.subject
    )
    return template_service.create_template(db, body, owner_user_id=user_id)


def get_template(
    template_service: TemplateService,
    db: Session,
    user_id: int,
    template_id: str,
) -> TemplateResponse:
    template = template_service.get_template_by_id(
        db=db,
        template_id=template_id,
        scope_user_id=user_id,
    )
    if not template:
        raise NotFoundError("Template not found")
    return template


def update_template(
    template_service: TemplateService,
    db: Session,
    user_id: int,
    template_id: str,
    body: TemplateUpdate,
) -> TemplateResponse:
    existing = template_service.get_template_by_id(
        db=db,
        template_id=template_id,
        scope_user_id=user_id,
    )
    if not existing:
        raise NotFoundError("Template not found")
    return template_service.update_template(
        db=db,
        template_id=template_id,
        template=body,
        scope_user_id=user_id,
    )


def delete_template(
    template_service: TemplateService,
    db: Session,
    user_id: int,
    template_id: str,
) -> dict:
    ok = template_service.delete_template(
        db=db,
        template_id=template_id,
        scope_user_id=user_id,
    )
    if not ok:
        raise NotFoundError("Template not found")
    return {"message": "Template deleted successfully"}
