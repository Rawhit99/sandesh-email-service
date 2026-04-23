from fastapi import APIRouter, Depends
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.notifications import StatsResponse
from services.stats_service import get_stats as get_stats_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return get_stats_service(db, user.id)
