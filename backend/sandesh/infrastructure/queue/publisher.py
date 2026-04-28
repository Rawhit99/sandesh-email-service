import logging
from typing import Optional

from redis.exceptions import RedisError

from config import settings
from sandesh.infrastructure.queue.executor import enqueue

logger = logging.getLogger(__name__)


def is_queue_enabled() -> bool:
    return bool((getattr(settings, "redis_url", None) or "").strip())


def enqueue_email_delivery(notification_id: int) -> Optional[str]:
    """Return queue message id when queued; None if queue disabled."""
    if not is_queue_enabled():
        return None
    try:
        message_id = enqueue(notification_id)
        logger.info(
            "Queued notification %s as message %s",
            notification_id,
            message_id,
        )
        return message_id
    except RedisError as exc:
        raise RuntimeError("Queue enqueue failed") from exc
