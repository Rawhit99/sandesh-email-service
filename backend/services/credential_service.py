from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from exceptions import ConflictError, NotFoundError
from models.models import IntegrationCredential
from models.schema_domains.integrations import (
    IntegrationCredentialCreate,
    IntegrationCredentialOut,
    IntegrationCredentialUpdate,
)
from sqlalchemy.orm import Session


def _get_or_404(
    cred_id: int, user_id: int, db: Session
) -> IntegrationCredential:
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.id == cred_id,
            IntegrationCredential.user_id == user_id,
        )
        .first()
    )
    if not cred:
        raise NotFoundError("Credential not found")
    return cred


def _clear_other_defaults(
    user_id: int,
    channel: str,
    exclude_id: Optional[int],
    db: Session,
) -> None:
    q = db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == user_id,
        IntegrationCredential.channel == channel,
        IntegrationCredential.is_default.is_(True),
    )
    if exclude_id is not None:
        q = q.filter(IntegrationCredential.id != exclude_id)
    for c in q.all():
        c.is_default = False


def list_credentials(
    db: Session,
    user_id: int,
    channel: Optional[str],
) -> List[IntegrationCredentialOut]:
    q = db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == user_id
    )
    if channel:
        q = q.filter(IntegrationCredential.channel == channel)
    return q.order_by(
        IntegrationCredential.channel, IntegrationCredential.name
    ).all()


def create_credential(
    db: Session,
    user_id: int,
    body: IntegrationCredentialCreate,
) -> IntegrationCredentialOut:
    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.channel == body.channel,
            IntegrationCredential.name == body.name,
        )
        .first()
    )
    if existing:
        raise ConflictError(
            f"A credential named '{body.name}' already exists "
            f"for channel '{body.channel}'"
        )

    now = datetime.utcnow()
    cred = IntegrationCredential(
        user_id=user_id,
        channel=body.channel,
        name=body.name,
        config=body.config,
        is_default=body.is_default,
        created_at=now,
        updated_at=now,
    )
    db.add(cred)
    if body.is_default:
        _clear_other_defaults(user_id, body.channel, None, db)
    db.commit()
    db.refresh(cred)
    return cred


def get_credential(
    db: Session, user_id: int, cred_id: int
) -> IntegrationCredentialOut:
    return _get_or_404(cred_id, user_id, db)


def update_credential(
    db: Session,
    user_id: int,
    cred_id: int,
    body: IntegrationCredentialUpdate,
) -> IntegrationCredentialOut:
    cred = _get_or_404(cred_id, user_id, db)
    if body.name is not None:
        clash = (
            db.query(IntegrationCredential)
            .filter(
                IntegrationCredential.user_id == user_id,
                IntegrationCredential.channel == cred.channel,
                IntegrationCredential.name == body.name,
                IntegrationCredential.id != cred_id,
            )
            .first()
        )
        if clash:
            raise ConflictError(
                f"A credential named '{body.name}' already exists "
                "for this channel"
            )
        cred.name = body.name
    if body.config is not None:
        cred.config = body.config
    if body.is_default is not None:
        cred.is_default = body.is_default
        if body.is_default:
            _clear_other_defaults(user_id, cred.channel, cred_id, db)
    cred.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)
    return cred


def set_default_credential(
    db: Session, user_id: int, cred_id: int
) -> IntegrationCredentialOut:
    cred = _get_or_404(cred_id, user_id, db)
    _clear_other_defaults(user_id, cred.channel, cred_id, db)
    cred.is_default = True
    cred.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)
    return cred


def delete_credential(db: Session, user_id: int, cred_id: int) -> None:
    cred = _get_or_404(cred_id, user_id, db)
    db.delete(cred)
    db.commit()
