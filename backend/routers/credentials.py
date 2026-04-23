"""Per-user named integration credentials — CRUD + default management."""

from typing import List, Optional

from fastapi import APIRouter, Depends
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.integrations import (
    IntegrationCredentialCreate,
    IntegrationCredentialOut,
    IntegrationCredentialUpdate,
)
from services.credential_service import (
    create_credential as create_credential_service,
)
from services.credential_service import (
    delete_credential as delete_credential_service,
)
from services.credential_service import (
    get_credential as get_credential_service,
)
from services.credential_service import (
    list_credentials as list_credentials_service,
)
from services.credential_service import (
    set_default_credential as set_default_credential_service,
)
from services.credential_service import (
    update_credential as update_credential_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])

# ── endpoints ─────────────────────────────────────────────────────────────────


@router.get("", response_model=List[IntegrationCredentialOut])
def list_credentials(
    channel: Optional[str] = None,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return list_credentials_service(db, user.id, channel)


@router.post("", response_model=IntegrationCredentialOut, status_code=201)
def create_credential(
    body: IntegrationCredentialCreate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return create_credential_service(db, user.id, body)


@router.get("/{cred_id}", response_model=IntegrationCredentialOut)
def get_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return get_credential_service(db, user.id, cred_id)


@router.put("/{cred_id}", response_model=IntegrationCredentialOut)
def update_credential(
    cred_id: int,
    body: IntegrationCredentialUpdate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return update_credential_service(db, user.id, cred_id, body)


@router.patch("/{cred_id}/set-default", response_model=IntegrationCredentialOut)
def set_default_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return set_default_credential_service(db, user.id, cred_id)


@router.delete("/{cred_id}", status_code=204)
def delete_credential(
    cred_id: int,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    delete_credential_service(db, user.id, cred_id)
    return None
