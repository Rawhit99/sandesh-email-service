import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def is_queue_enabled() -> bool:
    return bool((getattr(settings, "redis_url", None) or "").strip())


def enqueue_email_delivery(notification_id: int) -> Optional[str]:
    """Return RQ job id when queued; None if queue disabled."""
    if not is_queue_enabled():
        return None
    import redis
    from rq import Queue

    conn = redis.from_url(
        settings.redis_url,
        socket_timeout=settings.redis_socket_timeout_seconds,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
    )
    q = Queue(settings.queue_name, connection=conn)
    job = q.enqueue(
        "services.worker_tasks.process_email_notification",
        notification_id,
        job_timeout=settings.queue_job_timeout,
        result_ttl=settings.queue_result_ttl_seconds,
        failure_ttl=settings.queue_failure_ttl_seconds,
    )
    logger.info("Queued notification %s as job %s", notification_id, job.id)
    return job.id
