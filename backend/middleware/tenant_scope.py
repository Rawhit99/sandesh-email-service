"""Resolve which User row owns tenant data (templates, integrations, sends).

Platform administrators act across customer organizations; the UI sends
``X-Sandesh-Organization-Id`` and the API scopes reads/writes to that org's
``service_user`` account. Other users continue to use their own account only.
"""

from typing import Optional, Union

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from middleware.auth import get_current_user_any
from models.models import Organization, User, get_db

ORG_HEADER = "X-Sandesh-Organization-Id"


def user_effective_platform_admin(user: User) -> bool:
    if getattr(user, "is_platform_admin", False):
        return True
    raw = (getattr(settings, "platform_admin_usernames", None) or "") or ""
    names = {n.strip().lower() for n in str(raw).split(",") if n.strip()}
    return user.username.strip().lower() in names


def _parse_org_header(request: Request) -> Optional[str]:
    raw = (
        request.headers.get(ORG_HEADER)
        or request.headers.get(ORG_HEADER.lower())
    )
    if not raw or not str(raw).strip():
        return None
    return str(raw).strip()


def tenant_user_for_organization_ref(
    db: Session,
    organization_ref: Union[int, str],
) -> User:
    org: Optional[Organization] = None
    if isinstance(organization_ref, int):
        org = (
            db.query(Organization)
            .filter(Organization.id == organization_ref)
            .first()
        )
    else:
        raw = str(organization_ref).strip()
        if raw.isdigit():
            org = (
                db.query(Organization)
                .filter(Organization.id == int(raw))
                .first()
            )
        if org is None:
            org = (
                db.query(Organization)
                .filter(Organization.org_slug == raw)
                .first()
            )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not org.service_user_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Organization has no tenant service account. "
                "Create the organization from the platform admin UI."
            ),
        )
    su = db.query(User).filter(User.id == org.service_user_id).first()
    if not su:
        raise HTTPException(
            status_code=500,
            detail="Tenant service account is missing",
        )
    return su


def _resolve_default_organization_id(db: Session) -> Optional[int]:
    """Best-effort default org resolution for platform admins.

    Priority:
    1. org_slug == "default"
    2. lowest organization id (first created)
    """
    default_org = (
        db.query(Organization)
        .filter(Organization.org_slug == "default")
        .first()
    )
    if default_org:
        return default_org.id

    first_org = db.query(Organization).order_by(Organization.id.asc()).first()
    return first_org.id if first_org else None


def get_scope_tenant_user(
    request: Request,
    user: User = Depends(get_current_user_any),
    db: Session = Depends(get_db),
) -> User:
    if not user_effective_platform_admin(user):
        # Org members should operate on their tenant service account scope so
        # templates/integrations/subscribers are shared at org level.
        if user.organization_id:
            org = (
                db.query(Organization)
                .filter(Organization.id == user.organization_id)
                .first()
            )
            if org and org.service_user_id:
                su = (
                    db.query(User)
                    .filter(User.id == org.service_user_id)
                    .first()
                )
                if su:
                    return su
        elif (user.organization_name or "").strip():
            org = (
                db.query(Organization)
                .filter(Organization.name == user.organization_name.strip())
                .first()
            )
            if org and org.service_user_id:
                su = (
                    db.query(User)
                    .filter(User.id == org.service_user_id)
                    .first()
                )
                if su:
                    return su
        return user
    oid = _parse_org_header(request)
    if oid is None:
        oid = _resolve_default_organization_id(db)
    if oid is None:
        # Bootstrap mode: before the first org exists, allow platform admins
        # to keep operating in their own user scope without tenant header.
        return user
    try:
        return tenant_user_for_organization_ref(db, oid)
    except HTTPException as exc:
        # Bootstrap mode: if the selected/default org exists but does not yet
        # have a tenant service user, keep using current user scope.
        if exc.status_code == 400:
            return user
        raise


def resolve_notification_scope_user(
    db: Session,
    request: Request,
    current_user: Optional[User],
) -> Optional[User]:
    if current_user is None:
        return None
    if not user_effective_platform_admin(current_user):
        if current_user.organization_id:
            org = (
                db.query(Organization)
                .filter(Organization.id == current_user.organization_id)
                .first()
            )
            if org and org.service_user_id:
                su = (
                    db.query(User)
                    .filter(User.id == org.service_user_id)
                    .first()
                )
                if su:
                    return su
        elif (current_user.organization_name or "").strip():
            org = (
                db.query(Organization)
                .filter(
                    Organization.name == current_user.organization_name.strip()
                )
                .first()
            )
            if org and org.service_user_id:
                su = (
                    db.query(User)
                    .filter(User.id == org.service_user_id)
                    .first()
                )
                if su:
                    return su
        return current_user
    oid = _parse_org_header(request)
    if oid is None:
        oid = _resolve_default_organization_id(db)
    if oid is None:
        # Bootstrap mode: before the first org exists, allow sends/triggers
        # to resolve to the current user without tenant header.
        return current_user
    try:
        return tenant_user_for_organization_ref(db, oid)
    except HTTPException as exc:
        if exc.status_code == 400:
            return current_user
        raise
