from fastapi import APIRouter, Depends, HTTPException, Query
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.templates import (
    TemplateCreate,
    TemplatePreview,
    TemplateResponse,
    TemplateUpdate,
)
from services.template_api_service import (
    create_template as create_template_service,
)
from services.template_api_service import (
    delete_template as delete_template_service,
)
from services.template_api_service import (
    get_template as get_template_service,
)
from services.template_api_service import (
    list_templates,
)
from services.template_api_service import (
    preview_template as preview_template_service,
)
from services.template_api_service import (
    update_template as update_template_service,
)
from services.template_api_service import (
    validate_template as validate_template_service,
)
from services.template_service import TemplateService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["templates"])
template_service = TemplateService()


@router.get("/v1/templates", response_model=list[TemplateResponse])
async def get_templates(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(
        False, description="Filter to show only active templates"
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        return list_templates(
            template_service=template_service,
            db=db,
            user_id=user.id,
            limit=limit,
            offset=offset,
            active_only=active_only,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/v1/templates/preview")
async def preview_template(template: TemplatePreview, db: Session = Depends(get_db)):
    try:
        _ = db
        return preview_template_service(template_service, template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error previewing template")


@router.post("/v1/templates/validate")
async def validate_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        _ = db
        return validate_template_service(template_service, template)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error validating template: {str(e)}"
        )


@router.post("/v1/templates", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        return create_template_service(template_service, db, user.id, template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        return get_template_service(template_service, db, user.id, template_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/v1/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template: TemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        return update_template_service(
            template_service,
            db,
            user.id,
            template_id,
            template,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/v1/templates/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        return delete_template_service(
            template_service,
            db,
            user.id,
            template_id,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
