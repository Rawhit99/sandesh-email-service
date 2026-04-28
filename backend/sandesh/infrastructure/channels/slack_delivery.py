"""Slack Incoming Webhook delivery."""

import logging
from typing import Any, Dict

import httpx

from config import settings
from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def deliver_slack(payload: Dict[str, Any]) -> ChannelResult:
    url = (
        payload.get("_slack_webhook_url")
        or settings.slack_incoming_webhook_url
        or ""
    ).strip()
    if not url:
        return ChannelResult(ok=False, detail="slack_webhook_not_configured")
    title = str(payload.get("title") or "Notification")
    text = str(payload.get("text") or payload.get("plain") or "")[:2800]
    body = {"text": f"*{title}*\n{text}"}
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
        return ChannelResult(ok=True, detail="slack_ok")
    except Exception as exc:
        logger.exception("Slack webhook failed")
        return ChannelResult(ok=False, detail=str(exc)[:500])
