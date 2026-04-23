"""Firebase Cloud Messaging — payload must include fcm_device_token (or device_token)."""

import logging
from typing import Any, Dict

from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def deliver_fcm(payload: Dict[str, Any]) -> ChannelResult:
    from config import settings

    cred_path = (
        (payload.get("_firebase_credentials_path") or settings.firebase_credentials_path or "")
    ).strip()
    token = (payload.get("fcm_device_token") or payload.get("device_token") or "").strip()
    if not cred_path:
        return ChannelResult(ok=False, detail="fcm_credentials_not_configured")
    if not token:
        return ChannelResult(ok=False, detail="fcm_device_token_missing_in_payload")

    def _send() -> None:
        import firebase_admin
        from firebase_admin import credentials, messaging

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        title = str(payload.get("title") or "Alert")[:200]
        body = str(payload.get("text") or payload.get("plain") or "")[:2000]
        messaging.send(
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=token,
            )
        )

    try:
        import asyncio

        await asyncio.to_thread(_send)
        return ChannelResult(ok=True, detail="fcm_ok")
    except Exception as exc:
        logger.exception("FCM send failed")
        return ChannelResult(ok=False, detail=str(exc)[:500])
