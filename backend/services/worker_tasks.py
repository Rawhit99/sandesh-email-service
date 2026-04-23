"""RQ worker entrypoints (sync). Keep small — DB session + status transitions."""

import asyncio
import logging

from models.models import SessionLocal, Notification
from services.email_service import EmailService

logger = logging.getLogger(__name__)


def process_email_notification(notification_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.query(Notification).filter(Notification.id == notification_id).first()
        if not row:
            logger.error("Notification %s missing", notification_id)
            return
        row.status = "running"
        db.commit()

        email = EmailService()
        asyncio.run(email.send_email_async(db, notification_id))
    finally:
        db.close()
