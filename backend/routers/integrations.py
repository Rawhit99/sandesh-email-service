"""Integration status and per-user DB-backed settings."""

from fastapi import APIRouter, Depends
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.integrations import (
    IntegrationMeResponse,
    IntegrationMeUpdate,
)
from services.integration_service import (
    get_integration_me as get_integration_me_service,
)
from services.integration_service import (
    get_integration_status as get_integration_status_service,
)
from services.integration_service import (
    update_integration_me as update_integration_me_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["integrations"])


@router.get("/integrations/status")
def get_integration_status() -> dict:
    return get_integration_status_service()


@router.get("/integrations/me", response_model=IntegrationMeResponse)
def get_integration_me(user: User = Depends(get_scope_tenant_user)):
    return get_integration_me_service(user)


@router.put("/integrations/me", response_model=IntegrationMeResponse)
def put_integration_me(
    body: IntegrationMeUpdate,
    user: User = Depends(get_scope_tenant_user),
    db: Session = Depends(get_db),
):
    return update_integration_me_service(db, user, body)
