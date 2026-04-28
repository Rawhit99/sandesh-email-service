"""RQ worker entrypoints (sync)."""

import asyncio
import logging

from models.models import Notification, SessionLocal

logger = logging.getLogger(__name__)


def process_email_notification(notification_id: int) -> None:
    from services.email_service import EmailService

    db = SessionLocal()
    try:
        row = (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        if not row:
            logger.error("Notification %s missing", notification_id)
            return
        row.status = "running"
        db.commit()

        email = EmailService()
        asyncio.run(email.send_email_async(db, notification_id))
    finally:
        db.close()
