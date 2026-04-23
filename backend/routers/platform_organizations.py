"""List/create/edit customer organizations (platform administrators only)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import get_current_user_any
from middleware.tenant_scope import user_effective_platform_admin
from models.models import User, get_db
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
from services.platform_organization_service import (
    bulk_update_org_template_scope as bulk_update_scope_service,
)
from services.platform_organization_service import (
    create_organization as create_organization_service,
)
from services.platform_organization_service import (
    list_org_template_scope as list_org_template_scope_service,
)
from services.platform_organization_service import (
    list_organizations as list_organizations_service,
)
from services.platform_organization_service import (
    update_org_template_scope as update_scope_service,
)
from services.platform_organization_service import (
    update_organization as update_organization_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def _require_platform_admin(
    user: User = Depends(get_current_user_any),
) -> User:
    if not user_effective_platform_admin(user):
        raise HTTPException(
            status_code=403,
            detail=("Platform administrator access is required for this operation."),
        )
    return user


@router.get("/organizations", response_model=List[PlatformOrganizationOut])
def list_organizations(
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return list_organizations_service(db)


@router.post("/organizations", response_model=PlatformOrganizationOut)
def create_organization(
    body: PlatformOrganizationCreate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return create_organization_service(db, body)


@router.put("/organizations/{org_id}", response_model=PlatformOrganizationOut)
def update_organization(
    org_id: int,
    body: PlatformOrganizationUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return update_organization_service(db, org_id, body)


@router.get(
    "/organizations/{org_id}/templates",
    response_model=List[OrgTemplateSettingOut],
)
def list_org_template_scope(
    org_id: int,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return list_org_template_scope_service(db, org_id)


@router.put("/organizations/{org_id}/templates/{template_id}")
def update_org_template_scope(
    org_id: int,
    template_id: str,
    body: OrgTemplateSettingUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return update_scope_service(db, org_id, template_id, body)


@router.post("/organizations/{org_id}/templates/bulk")
def bulk_update_org_template_scope(
    org_id: int,
    body: OrgTemplateBulkUpdate,
    _: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return bulk_update_scope_service(db, org_id, body)
