"""WhatsApp via Twilio (sandbox or approved sender)."""

import logging
from typing import Any, Dict

import httpx

from config import settings
from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def deliver_whatsapp_twilio(payload: Dict[str, Any]) -> ChannelResult:
    sid = (payload.get("_twilio_account_sid") or settings.twilio_account_sid or "").strip()
    auth = (payload.get("_twilio_auth_token") or settings.twilio_auth_token or "").strip()
    from_wa = (payload.get("_twilio_whatsapp_from") or settings.twilio_whatsapp_from or "").strip()
    to = (payload.get("whatsapp_to") or payload.get("to_whatsapp") or "").strip()
    if not sid or not auth or not from_wa:
        return ChannelResult(ok=False, detail="twilio_not_configured")
    if not to:
        return ChannelResult(ok=False, detail="whatsapp_to_missing_in_payload")
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    body_text = str(payload.get("text") or payload.get("plain") or "")[:1500]
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {"From": from_wa, "To": to, "Body": body_text or (payload.get("title") or "Notification")}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, data=data, auth=(sid, auth))
            r.raise_for_status()
        return ChannelResult(ok=True, detail="twilio_whatsapp_ok")
    except Exception as exc:
        logger.exception("Twilio WhatsApp failed")
        return ChannelResult(ok=False, detail=str(exc)[:500])
