from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from middleware.tenant_scope import get_scope_tenant_user
from models.models import EmailTemplate, get_db, Notification, User
from models.schemas import StatsResponse, NotificationSummary

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    try:
        total_notifications = (
            db.query(func.count(Notification.id)).filter(Notification.user_id == user.id).scalar() or 0
        )

        total_templates = (
            db.query(func.count(EmailTemplate.id)).filter(EmailTemplate.user_id == user.id).scalar() or 0
        )

        status_rows = (
            db.query(Notification.status, func.count(Notification.id))
            .filter(Notification.user_id == user.id)
            .group_by(Notification.status)
            .all()
        )
        status_counts = {row[0]: row[1] for row in status_rows}

        last_24h = datetime.utcnow() - timedelta(days=1)
        notifications_24h = (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user.id, Notification.created_at >= last_24h)
            .scalar()
            or 0
        )

        success_count = status_counts.get("success", 0)
        failed_count = status_counts.get("failed", 0)
        pending_count = sum(status_counts.get(s, 0) for s in ("pending", "queued", "running"))
        success_rate = (success_count / total_notifications * 100) if total_notifications > 0 else 0

        recent_notifications = (
            db.query(Notification)
            .filter(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )

        return StatsResponse(
            total_notifications=total_notifications,
            total_templates=total_templates,
            notifications_24h=notifications_24h,
            success_rate=round(success_rate, 2),
            status_counts=status_counts,
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            recent_notifications=[NotificationSummary.from_orm(n) for n in recent_notifications],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")
