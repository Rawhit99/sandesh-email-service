from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime
from typing import List

from exceptions import BadRequestError, ConflictError, NotFoundError
from middleware.auth_utils import get_password_hash
from models.models import EmailTemplate, Organization, OrgTemplateSetting, User
from models.schema_domains.org_template_scope import (
    OrgTemplateBulkUpdate,
    OrgTemplateSettingOut,
    OrgTemplateSettingUpdate,
)
from models.schema_domains.organizations import (
    PlatformOrganizationCreate,
    PlatformOrganizationOut,
    PlatformOrganizationUpdate,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _org_to_out(o: Organization, db: Session) -> PlatformOrganizationOut:
    su = (
        db.query(User).filter(User.id == o.service_user_id).first()
        if o.service_user_id
        else None
    )
    return PlatformOrganizationOut(
        id=o.id,
        name=o.name,
        org_slug=o.org_slug,
        service_username=su.username if su else None,
        has_tenant_account=bool(o.service_user_id),
    )


def list_organizations(db: Session) -> List[PlatformOrganizationOut]:
    rows = db.query(Organization).order_by(Organization.name.asc()).all()
    return [_org_to_out(o, db) for o in rows]


def create_organization(
    db: Session, body: PlatformOrganizationCreate
) -> PlatformOrganizationOut:
    name = body.name.strip()
    if len(name) < 2:
        raise BadRequestError(
            "Organization name must be at least 2 characters"
        )
    if db.query(Organization).filter(Organization.name == name).first():
        raise ConflictError("An organization with this name already exists")

    raw_slug = (
        body.org_slug
        or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    )
    slug = raw_slug or "org"
    if db.query(Organization).filter(Organization.org_slug == slug).first():
        raise ConflictError(f"Organization ID '{slug}' is already taken")

    org = Organization(name=name, org_slug=slug)
    db.add(org)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            "An organization with this name or ID already exists"
        )

    svc = User(
        username=f"tenant-{slug}-{uuid.uuid4().hex[:12]}",
        password_hash=get_password_hash(secrets.token_urlsafe(24)),
        organization_id=org.id,
        organization_name=name,
        organization_role=None,
        is_platform_admin=False,
        is_active=True,
    )
    db.add(svc)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise BadRequestError(
            "Could not create tenant service account; "
            "retry with a different organization name."
        )
    org.service_user_id = svc.id
    db.add(org)
    db.commit()
    db.refresh(org)
    return _org_to_out(org, db)


def update_organization(
    db: Session,
    org_id: int,
    body: PlatformOrganizationUpdate,
) -> PlatformOrganizationOut:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NotFoundError("Organization not found")

    if body.name is not None:
        new_name = body.name.strip()
        existing = (
            db.query(Organization)
            .filter(
                Organization.name == new_name,
                Organization.id != org_id,
            )
            .first()
        )
        if existing:
            raise ConflictError(
                "An organization with this name already exists"
            )
        org.name = new_name
        if org.service_user_id:
            svc = db.query(User).filter(User.id == org.service_user_id).first()
            if svc:
                svc.organization_name = new_name

    if body.org_slug is not None:
        new_slug = body.org_slug.strip()
        if new_slug:
            existing = (
                db.query(Organization)
                .filter(
                    Organization.org_slug == new_slug,
                    Organization.id != org_id,
                )
                .first()
            )
            if existing:
                raise ConflictError(
                    f"Organization ID '{new_slug}' is already taken"
                )
            org.org_slug = new_slug

    try:
        db.commit()
        db.refresh(org)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Conflict updating organization")
    return _org_to_out(org, db)


def _get_org_or_404(org_id: int, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NotFoundError("Organization not found")
    return org


def _settings_map(org_id: int, template_ids: List[str], db: Session) -> dict:
    rows = (
        db.query(OrgTemplateSetting)
        .filter(
            OrgTemplateSetting.organization_id == org_id,
            OrgTemplateSetting.template_id.in_(template_ids),
        )
        .all()
    )
    return {r.template_id: r for r in rows}


def list_org_template_scope(
    db: Session, org_id: int
) -> List[OrgTemplateSettingOut]:
    _get_org_or_404(org_id, db)
    templates = (
        db.query(EmailTemplate).order_by(EmailTemplate.name.asc()).all()
    )
    latest_by_template_id = {}
    for row in templates:
        if row.template_id not in latest_by_template_id:
            latest_by_template_id[row.template_id] = row
    template_rows = list(latest_by_template_id.values())
    template_ids = [t.template_id for t in template_rows]
    smap = _settings_map(org_id, template_ids, db) if template_ids else {}
    return [
        OrgTemplateSettingOut(
            template_id=t.template_id,
            template_name=t.name,
            subject=t.subject,
            is_active=t.is_active,
            is_enabled=smap.get(t.template_id).is_enabled
            if smap.get(t.template_id)
            else True,
        )
        for t in template_rows
    ]


def update_org_template_scope(
    db: Session,
    org_id: int,
    template_id: str,
    body: OrgTemplateSettingUpdate,
) -> dict:
    _get_org_or_404(org_id, db)
    tpl = (
        db.query(EmailTemplate)
        .filter(
            EmailTemplate.template_id == template_id,
        )
        .first()
    )
    if not tpl:
        raise NotFoundError("Template not found for this organisation")

    setting = (
        db.query(OrgTemplateSetting)
        .filter(
            OrgTemplateSetting.organization_id == org_id,
            OrgTemplateSetting.template_id == template_id,
        )
        .first()
    )
    if setting:
        setting.is_enabled = body.is_enabled
        setting.updated_at = datetime.utcnow()
    else:
        db.add(
            OrgTemplateSetting(
                organization_id=org_id,
                template_id=template_id,
                is_enabled=body.is_enabled,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
    db.commit()
    return {"template_id": template_id, "is_enabled": body.is_enabled}


def bulk_update_org_template_scope(
    db: Session,
    org_id: int,
    body: OrgTemplateBulkUpdate,
) -> dict:
    _get_org_or_404(org_id, db)
    q = db.query(EmailTemplate)
    if body.template_ids:
        q = q.filter(EmailTemplate.template_id.in_(body.template_ids))
    templates = q.all()
    # Multiple template rows can exist for the same template_id; scope updates
    # should run once per logical template.
    unique_templates = {}
    for row in templates:
        if row.template_id not in unique_templates:
            unique_templates[row.template_id] = row
    templates = list(unique_templates.values())
    tids = [t.template_id for t in templates]
    smap = _settings_map(org_id, tids, db) if tids else {}
    for t in templates:
        setting = smap.get(t.template_id)
        if setting:
            setting.is_enabled = body.is_enabled
            setting.updated_at = datetime.utcnow()
        else:
            new_setting = OrgTemplateSetting(
                organization_id=org_id,
                template_id=t.template_id,
                is_enabled=body.is_enabled,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_setting)
            smap[t.template_id] = new_setting
    db.commit()
    return {"updated": len(templates), "is_enabled": body.is_enabled}
