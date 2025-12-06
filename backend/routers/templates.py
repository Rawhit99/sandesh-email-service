from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from models.models import get_db
from models.schemas import (
    TemplateCreate, TemplateResponse, TemplateUpdate, TemplatePreview
)
from services.template_service import TemplateService

router = APIRouter(prefix="/api", tags=["templates"])
template_service = TemplateService()

@router.get("/v1/templates", response_model=list[TemplateResponse])
async def get_templates(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False, description="Filter to show only active templates"),
    db: Session = Depends(get_db)
):
    try:
        templates = template_service.get_templates(
            db=db,
            limit=limit,
            offset=offset,
            active_only=active_only
        )
        return templates
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/v1/templates/preview")
async def preview_template(template: TemplatePreview, db: Session = Depends(get_db)):
    try:
        preview = template_service.preview_template(template.content, template.variables)
        return {"preview": preview}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error previewing template")

@router.post("/v1/templates/validate")
async def validate_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        extracted_vars = TemplateCreate.extract_variables(template.content, template.subject)
        template.variables = extracted_vars
        validation = template_service.validate_template_syntax(template.content)
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error validating template")

@router.post("/v1/templates", response_model=TemplateResponse)
async def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        extracted_vars = TemplateCreate.extract_variables(template.content, template.subject)
        template.variables = extracted_vars
        return template_service.create_template(db, template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: Session = Depends(get_db)):
    try:
        template = template_service.get_template_by_id(db=db, template_id=template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/v1/templates/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, template: TemplateUpdate, db: Session = Depends(get_db)):
    try:
        existing_template = template_service.get_template_by_id(db=db, template_id=template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template_service.update_template(db=db, template_id=template_id, template=template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/v1/templates/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    try:
        success = template_service.delete_template(db=db, template_id=template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


