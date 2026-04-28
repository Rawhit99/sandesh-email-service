"""Deliver non-email channels after primary email succeeds."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from models.models import Notification
from sandesh.application.integration_webhooks import (
    merge_user_webhooks_into_payload,
)
from sandesh.domain.enums import ChannelType
from sandesh.infrastructure.channels.registry import dispatch_channel

logger = logging.getLogger(__name__)

_ALIAS: Dict[str, ChannelType] = {
    "slack": ChannelType.SLACK,
    "ms_teams": ChannelType.MS_TEAMS,
    "teams": ChannelType.MS_TEAMS,
    "whatsapp": ChannelType.WHATSAPP,
    "push_fcm": ChannelType.PUSH_FCM,
    "fcm": ChannelType.PUSH_FCM,
    "push_sns": ChannelType.PUSH_SNS,
    "sns": ChannelType.PUSH_SNS,
}


def _plain(html: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html or "")
    return " ".join(t.split())[:4000]


async def deliver_auxiliary_channels(
    db: Session, notification: Notification, subject: str, html: str
) -> None:
    raw: List[Any] = notification.channels_requested or ["email"]
    names = [str(c).lower().strip() for c in raw]
    plain = _plain(html)
    payload: Dict[str, Any] = {
        "title": subject,
        "text": plain,
        "plain": plain,
        "html": html,
        "to_email": notification.email,
        **(notification.payload or {}),
    }
    payload = merge_user_webhooks_into_payload(
        db, getattr(notification, "user_id", None), payload
    )
    for name in names:
        if name == "email":
            continue
        ch = _ALIAS.get(name)
        if ch is None:
            logger.warning("Unknown auxiliary channel: %s", name)
            continue
        try:
            res = await dispatch_channel(ch, payload)
            logger.info("channel=%s ok=%s detail=%s", name, res.ok, res.detail)
        except Exception:
            logger.exception("channel=%s failed", name)
