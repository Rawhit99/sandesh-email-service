"""List/create/edit customer organizations (platform administrators only)."""

import re
import secrets
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from middleware.auth import get_current_user_any
from middleware.auth_utils import get_password_hash
from middleware.tenant_scope import user_effective_platform_admin
from models.models import EmailTemplate, Organization, OrgTemplateSetting, User, get_db
from models.schemas import (
    OrgTemplateBulkUpdate,
    OrgTemplateSettingOut,
    OrgTemplateSettingUpdate,
    PlatformOrganizationCreate,
    PlatformOrganizationOut,
    PlatformOrganizationUpdate,
)

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def _require_platform_admin(user: User = Depends(get_current_user_any)) -> User:
    if not user_effective_platform_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Platform administrator access is required for this operation.",
        )
    return user


def _org_to_out(o: Organization, db: Session) -> PlatformOrganizationOut:
    su = db.query(User).filter(User.id == o.service_user_id).first() if o.service_user_id else None
    return PlatformOrganizationOut(
        id=o.id,
        name=o.name,
        org_slug=o.org_slug,
        service_username=su.username if su else None,
        has_tenant_account=bool(o.service_user_id),
    )


@router.get("/organizations", response_model=List[PlatformOrganizationOut])
def list_organizations(
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(Organization).order_by(Organization.name.asc()).all()
    return [_org_to_out(o, db) for o in rows]


@router.post("/organizations", response_model=PlatformOrganizationOut)
def create_organization(
    body: PlatformOrganizationCreate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Organization name must be at least 2 characters")
    if db.query(Organization).filter(Organization.name == name).first():
        raise HTTPException(status_code=409, detail="An organization with this name already exists")

    # Build slug: prefer provided org_slug, otherwise derive from name
    raw_slug = body.org_slug or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    slug = raw_slug or "org"
    if db.query(Organization).filter(Organization.org_slug == slug).first():
        raise HTTPException(status_code=409, detail=f"Organization ID '{slug}' is already taken")

    org = Organization(name=name, org_slug=slug)
    db.add(org)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An organization with this name or ID already exists")

    uname = f"tenant-{slug}-{uuid.uuid4().hex[:12]}"
    svc = User(
        username=uname,
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
        raise HTTPException(
            status_code=500,
            detail="Could not create tenant service account; retry with a different organization name.",
        )
    org.service_user_id = svc.id
    db.add(org)
    db.commit()
    db.refresh(org)
    return _org_to_out(org, db)


@router.put("/organizations/{org_id}", response_model=PlatformOrganizationOut)
def update_organization(
    org_id: int,
    body: PlatformOrganizationUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if body.name is not None:
        new_name = body.name.strip()
        existing = db.query(Organization).filter(
            Organization.name == new_name, Organization.id != org_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="An organization with this name already exists")
        org.name = new_name
        # Keep service user's organization_name in sync
        if org.service_user_id:
            svc = db.query(User).filter(User.id == org.service_user_id).first()
            if svc:
                svc.organization_name = new_name

    if body.org_slug is not None:
        new_slug = body.org_slug.strip()
        if new_slug:
            existing = db.query(Organization).filter(
                Organization.org_slug == new_slug, Organization.id != org_id
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"Organization ID '{new_slug}' is already taken")
            org.org_slug = new_slug

    try:
        db.commit()
        db.refresh(org)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict updating organization")

    return _org_to_out(org, db)


# ── Template scope management ────────────────────────────────────────────────

def _get_org_or_404(org_id: int, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _settings_map(org_id: int, template_ids: List[str], db: Session) -> dict:
    """Return {template_id: OrgTemplateSetting} for the given org and template IDs."""
    rows = (
        db.query(OrgTemplateSetting)
        .filter(
            OrgTemplateSetting.organization_id == org_id,
            OrgTemplateSetting.template_id.in_(template_ids),
        )
        .all()
    )
    return {r.template_id: r for r in rows}


@router.get("/organizations/{org_id}/templates", response_model=List[OrgTemplateSettingOut])
def list_org_template_scope(
    org_id: int,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """Return all templates that belong to this org, with their per-org enabled status."""
    org = _get_org_or_404(org_id, db)

    templates = (
        db.query(EmailTemplate)
        .filter(EmailTemplate.user_id == org.service_user_id)
        .order_by(EmailTemplate.name.asc())
        .all()
    )

    tids = [t.template_id for t in templates]
    smap = _settings_map(org_id, tids, db) if tids else {}

    # Use template's own is_active as the canonical enabled state so that
    # changes made from the Templates page are always visible here too.
    return [
        OrgTemplateSettingOut(
            template_id=t.template_id,
            template_name=t.name,
            subject=t.subject,
            is_active=t.is_active,
            is_enabled=t.is_active,
        )
        for t in templates
    ]


@router.put("/organizations/{org_id}/templates/{template_id}")
def update_org_template_scope(
    org_id: int,
    template_id: str,
    body: OrgTemplateSettingUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """Enable or disable a single template for the given organisation."""
    org = _get_org_or_404(org_id, db)

    tpl = (
        db.query(EmailTemplate)
        .filter(
            EmailTemplate.template_id == template_id,
            EmailTemplate.user_id == org.service_user_id,
        )
        .first()
    )
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found for this organisation")

    setting = (
        db.query(OrgTemplateSetting)
        .filter(
            OrgTemplateSetting.organization_id == org_id,
            OrgTemplateSetting.template_id == template_id,
        )
        .first()
    )
    # Sync is_enabled with the template's own is_active so both views stay in sync.
    tpl.is_active = body.is_enabled

    if setting:
        setting.is_enabled = body.is_enabled
        setting.updated_at = datetime.utcnow()
    else:
        setting = OrgTemplateSetting(
            organization_id=org_id,
            template_id=template_id,
            is_enabled=body.is_enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(setting)

    db.commit()
    return {"template_id": template_id, "is_enabled": body.is_enabled}


@router.post("/organizations/{org_id}/templates/bulk")
def bulk_update_org_template_scope(
    org_id: int,
    body: OrgTemplateBulkUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """Bulk-enable or bulk-disable templates for an organisation.

    If ``template_ids`` is provided, only those templates are affected.
    If ``template_ids`` is ``None`` or empty, ALL templates for the org are affected.
    """
    org = _get_org_or_404(org_id, db)

    q = db.query(EmailTemplate).filter(EmailTemplate.user_id == org.service_user_id)
    if body.template_ids:
        q = q.filter(EmailTemplate.template_id.in_(body.template_ids))
    templates = q.all()

    tids = [t.template_id for t in templates]
    smap = _settings_map(org_id, tids, db) if tids else {}

    for t in templates:
        # Sync template's own is_active so Templates page always reflects the change.
        t.is_active = body.is_enabled
        setting = smap.get(t.template_id)
        if setting:
            setting.is_enabled = body.is_enabled
            setting.updated_at = datetime.utcnow()
        else:
            db.add(OrgTemplateSetting(
                organization_id=org_id,
                template_id=t.template_id,
                is_enabled=body.is_enabled,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))

    db.commit()
    return {"updated": len(templates), "is_enabled": body.is_enabled}
