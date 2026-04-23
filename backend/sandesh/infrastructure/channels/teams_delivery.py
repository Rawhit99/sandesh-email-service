"""Microsoft Teams Incoming Webhook (MessageCard)."""

import logging
from typing import Any, Dict

import httpx

from config import settings
from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def deliver_teams(payload: Dict[str, Any]) -> ChannelResult:
    url = (payload.get("_teams_webhook_url") or settings.ms_teams_incoming_webhook_url or "").strip()
    if not url:
        return ChannelResult(ok=False, detail="teams_webhook_not_configured")
    title = str(payload.get("title") or "Notification")
    text = str(payload.get("text") or payload.get("plain") or "")[:8000]
    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": title,
        "sections": [{"activityTitle": title, "text": text}],
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.post(url, json=card)
            r.raise_for_status()
        return ChannelResult(ok=True, detail="teams_ok")
    except Exception as exc:
        logger.exception("Teams webhook failed")
        return ChannelResult(ok=False, detail=str(exc)[:500])
