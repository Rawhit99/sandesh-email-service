"""Redis queue worker with ThreadPoolExecutor (no RQ dependency)."""

from __future__ import annotations

import json
import logging
import signal
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime
from typing import Any, Dict

import redis
from redis.exceptions import RedisError

from config import settings
from services.worker_tasks import process_email_notification

logger = logging.getLogger(__name__)


def _queue_key() -> str:
    return settings.queue_name


def _retry_key() -> str:
    return f"{settings.queue_name}:retry"


def _connect() -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        socket_timeout=settings.redis_socket_timeout_seconds,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
        decode_responses=True,
    )


def _encode_message(notification_id: int, attempt: int = 0) -> str:
    return json.dumps(
        {
            "id": str(uuid.uuid4()),
            "notification_id": notification_id,
            "attempt": attempt,
            "queued_at": datetime.utcnow().isoformat(),
        }
    )


def enqueue(notification_id: int) -> str:
    """Enqueue notification and return queue message id."""
    conn = _connect()
    encoded = _encode_message(notification_id, attempt=0)
    conn.rpush(_queue_key(), encoded)
    msg = json.loads(encoded)
    return str(msg["id"])


def _decode_message(raw: str) -> Dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Queue payload must be a dict")
    return data


def _flush_due_retries(conn: redis.Redis) -> None:
    now = int(time.time())
    due_items = conn.zrangebyscore(_retry_key(), min=0, max=now)
    if not due_items:
        return
    pipe = conn.pipeline()
    for item in due_items:
        pipe.rpush(_queue_key(), item)
        pipe.zrem(_retry_key(), item)
    pipe.execute()


def _schedule_retry(conn: redis.Redis, payload: Dict[str, Any]) -> None:
    attempt = int(payload.get("attempt", 0)) + 1
    if attempt > settings.queue_max_retries:
        logger.error(
            "Dropping notification %s after %s attempts",
            payload.get("notification_id"),
            attempt - 1,
        )
        return
    payload["attempt"] = attempt
    delay = settings.queue_retry_backoff_seconds * (2 ** (attempt - 1))
    run_at = int(time.time()) + delay
    conn.zadd(_retry_key(), {json.dumps(payload): run_at})
    logger.warning(
        "Scheduled retry %s for notification %s in %ss",
        attempt,
        payload.get("notification_id"),
        delay,
    )


def _handle_payload(conn: redis.Redis, payload: Dict[str, Any]) -> None:
    nid = int(payload["notification_id"])
    process_email_notification(nid)


def run_worker_loop() -> None:
    """Run queue worker loop until SIGINT/SIGTERM."""
    conn = _connect()
    should_run = True

    def _stop(*_: object) -> None:
        nonlocal should_run
        should_run = False
        logger.info("Shutdown requested; draining in-flight tasks")

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    logger.info(
        "Queue worker started queue=%s concurrency=%s",
        _queue_key(),
        settings.queue_worker_concurrency,
    )
    in_flight: Dict[Future[Any], Dict[str, Any]] = {}
    with ThreadPoolExecutor(
        max_workers=settings.queue_worker_concurrency
    ) as executor:
        while should_run or in_flight:
            try:
                _flush_due_retries(conn)
            except RedisError:
                logger.exception("Failed moving retry items; continuing")

            while should_run and len(in_flight) < settings.queue_worker_concurrency:
                try:
                    popped = conn.blpop(
                        _queue_key(),
                        timeout=settings.queue_poll_timeout_seconds,
                    )
                except RedisError:
                    logger.exception("Redis pop error; backing off")
                    time.sleep(1)
                    break
                if not popped:
                    break
                _, raw = popped
                try:
                    payload = _decode_message(raw)
                    fut = executor.submit(_handle_payload, conn, payload)
                    in_flight[fut] = payload
                except Exception:
                    logger.exception("Invalid queue payload dropped")

            if not in_flight:
                continue

            done, _ = wait(
                in_flight.keys(),
                timeout=1.0,
                return_when=FIRST_COMPLETED,
            )
            for fut in done:
                payload = in_flight.pop(fut)
                try:
                    fut.result()
                except Exception:
                    logger.exception(
                        "Worker task failed notification=%s",
                        payload.get("notification_id"),
                    )
                    try:
                        _schedule_retry(conn, payload)
                    except RedisError:
                        logger.exception("Could not schedule retry")

    logger.info("Queue worker stopped")
