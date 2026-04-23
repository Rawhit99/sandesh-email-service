"""Per-user named integration credentials — CRUD + default management."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from middleware.auth import get_current_user_any
from middleware.tenant_scope import get_scope_tenant_user
from models.models import IntegrationCredential, User, get_db
from models.schemas import (
    IntegrationCredentialCreate,
    IntegrationCredentialOut,
    IntegrationCredentialUpdate,
)

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_or_404(cred_id: int, user_id: int, db: Session) -> IntegrationCredential:
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.id == cred_id,
            IntegrationCredential.user_id == user_id,
        )
        .first()
    )
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[IntegrationCredentialOut])
def list_credentials(
    channel: Optional[str] = None,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    """List all stored credential profiles for the current user, optionally filtered by channel."""
    q = db.query(IntegrationCredential).filter(IntegrationCredential.user_id == user.id)
    if channel:
        q = q.filter(IntegrationCredential.channel == channel)
    return q.order_by(IntegrationCredential.channel, IntegrationCredential.name).all()


@router.post("", response_model=IntegrationCredentialOut, status_code=201)
def create_credential(
    body: IntegrationCredentialCreate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    """Create a named credential profile for a channel."""
    # Check uniqueness per (user, channel, name)
    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user.id,
            IntegrationCredential.channel == body.channel,
            IntegrationCredential.name == body.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A credential named '{body.name}' already exists for channel '{body.channel}'",
        )

    now = datetime.utcnow()
    cred = IntegrationCredential(
        user_id=user.id,
        channel=body.channel,
        name=body.name,
        config=body.config,
        is_default=body.is_default,
        created_at=now,
        updated_at=now,
    )
    db.add(cred)

    # If this is flagged as default, unset default on all other same-channel creds
    if body.is_default:
        _clear_other_defaults(user.id, body.channel, None, db)

    db.commit()
    db.refresh(cred)
    return cred


@router.get("/{cred_id}", response_model=IntegrationCredentialOut)
def get_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return _get_or_404(cred_id, user.id, db)


@router.put("/{cred_id}", response_model=IntegrationCredentialOut)
def update_credential(
    cred_id: int,
    body: IntegrationCredentialUpdate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    cred = _get_or_404(cred_id, user.id, db)

    if body.name is not None:
        # Check uniqueness
        clash = (
            db.query(IntegrationCredential)
            .filter(
                IntegrationCredential.user_id == user.id,
                IntegrationCredential.channel == cred.channel,
                IntegrationCredential.name == body.name,
                IntegrationCredential.id != cred_id,
            )
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=409,
                detail=f"A credential named '{body.name}' already exists for this channel",
            )
        cred.name = body.name

    if body.config is not None:
        cred.config = body.config

    if body.is_default is not None:
        cred.is_default = body.is_default
        if body.is_default:
            _clear_other_defaults(user.id, cred.channel, cred_id, db)

    cred.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)
    return cred


@router.patch("/{cred_id}/set-default", response_model=IntegrationCredentialOut)
def set_default_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    """Mark a credential as the default for its channel and unset all others."""
    cred = _get_or_404(cred_id, user.id, db)
    _clear_other_defaults(user.id, cred.channel, cred_id, db)
    cred.is_default = True
    cred.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)
    return cred


@router.delete("/{cred_id}", status_code=204)
def delete_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    cred = _get_or_404(cred_id, user.id, db)
    db.delete(cred)
    db.commit()
    return None


# ── internal helper ─────────────────────────────────────────────────────────

def _clear_other_defaults(user_id: int, channel: str, exclude_id: Optional[int], db: Session):
    q = db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == user_id,
        IntegrationCredential.channel == channel,
        IntegrationCredential.is_default == True,
    )
    if exclude_id is not None:
        q = q.filter(IntegrationCredential.id != exclude_id)
    for c in q.all():
        c.is_default = False
