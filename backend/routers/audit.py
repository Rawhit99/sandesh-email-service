from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from models.models import AuditLog, get_db
from models.schemas import AuditLogResponse
from middleware.auth import get_current_user_from_token

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit-logs"])

@router.get("", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    audit_logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    return audit_logs


