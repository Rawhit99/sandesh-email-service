from __future__ import annotations

from datetime import datetime, timedelta

from models.models import EmailTemplate, Notification
from models.schema_domains.notifications import (
    NotificationSummary,
    StatsResponse,
)
from sqlalchemy import func
from sqlalchemy.orm import Session


def get_stats(db: Session, user_id: int) -> StatsResponse:
    total_notifications = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id)
        .scalar()
        or 0
    )
    total_templates = (
        db.query(func.count(EmailTemplate.id))
        .filter(EmailTemplate.user_id == user_id)
        .scalar()
        or 0
    )
    status_rows = (
        db.query(Notification.status, func.count(Notification.id))
        .filter(Notification.user_id == user_id)
        .group_by(Notification.status)
        .all()
    )
    status_counts = {row[0]: row[1] for row in status_rows}
    last_24h = datetime.utcnow() - timedelta(days=1)
    notifications_24h = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.user_id == user_id,
            Notification.created_at >= last_24h,
        )
        .scalar()
        or 0
    )
    success_count = status_counts.get("success", 0)
    failed_count = status_counts.get("failed", 0)
    pending_count = sum(
        status_counts.get(s, 0) for s in ("pending", "queued", "running")
    )
    success_rate = (
        (success_count / total_notifications * 100)
        if total_notifications > 0
        else 0
    )
    recent_notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
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
        recent_notifications=[
            NotificationSummary.from_orm(n) for n in recent_notifications
        ],
    )
