from __future__ import annotations

import re
import secrets
import uuid
from typing import Optional, Tuple

from fastapi import HTTPException
from middleware.auth_utils import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from middleware.tenant_scope import user_effective_platform_admin
from models.models import Organization, User
from models.schema_domains.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        organization_id=user.organization_id,
        organization_name=user.organization_name,
        organization_role=user.organization_role,
        is_platform_admin=user_effective_platform_admin(user),
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _build_org_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    return base or "org"


def _ensure_unique_org_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.org_slug == slug).first():
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug


def _create_org_with_service_user(
    db: Session,
    organization_name: str,
) -> Organization:
    org = Organization(
        name=organization_name,
        org_slug=_ensure_unique_org_slug(db, _build_org_slug(organization_name)),
    )
    db.add(org)
    db.flush()

    service_username = f"tenant-{org.org_slug}-{uuid.uuid4().hex[:10]}"
    service_user = User(
        username=service_username,
        password_hash=get_password_hash(secrets.token_urlsafe(24)),
        organization_id=org.id,
        organization_name=organization_name,
        organization_role=None,
        is_platform_admin=False,
        is_active=True,
    )
    db.add(service_user)
    db.flush()
    org.service_user_id = service_user.id
    db.add(org)
    return org


def _assign_org_for_registration(
    db: Session,
    organization_name: Optional[str],
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    if not organization_name or not str(organization_name).strip():
        return None, None, None

    display = str(organization_name).strip()
    existing_org = db.query(Organization).filter(Organization.name == display).first()
    if existing_org:
        return existing_org.id, display, "member"

    new_org = _create_org_with_service_user(db, display)
    return new_org.id, display, "admin"


def register_user(db: Session, user_data: UserCreate) -> UserResponse:
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        org_id, org_display, org_role = _assign_org_for_registration(
            db,
            user_data.organization_name,
        )
        user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            organization_id=org_id,
            organization_name=org_display,
            organization_role=org_role,
            is_platform_admin=False,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return to_user_response(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflict while creating user")


def login_user(db: Session, credentials: LoginRequest) -> LoginResponse:
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=to_user_response(user),
    )


def get_user_by_username(db: Session, username: str) -> UserResponse:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return to_user_response(user)
