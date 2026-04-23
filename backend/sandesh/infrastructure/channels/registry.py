import logging
from typing import Any, Dict, List

from sandesh.domain.enums import ChannelType
from sandesh.infrastructure.channels.base import ChannelResult
from sandesh.infrastructure.channels import stubs
from sandesh.infrastructure.channels import (
    fcm_delivery,
    slack_delivery,
    sns_delivery,
    teams_delivery,
    whatsapp_twilio,
)

logger = logging.getLogger(__name__)


async def dispatch_channel(
    channel: ChannelType, payload: Dict[str, Any]
) -> ChannelResult:
    if channel == ChannelType.EMAIL:
        return ChannelResult(ok=True, detail="email_delegated")
    if channel == ChannelType.SLACK:
        return await slack_delivery.deliver_slack(payload)
    if channel == ChannelType.MS_TEAMS:
        return await teams_delivery.deliver_teams(payload)
    if channel == ChannelType.PUSH_FCM:
        return await fcm_delivery.deliver_fcm(payload)
    if channel == ChannelType.PUSH_SNS:
        return await sns_delivery.deliver_sns(payload)
    if channel == ChannelType.WHATSAPP:
        return await whatsapp_twilio.deliver_whatsapp_twilio(payload)
    return await stubs._stub_send(channel, payload)


async def dispatch_all(
    channels: List[ChannelType], payload: Dict[str, Any]
) -> List[ChannelResult]:
    out: List[ChannelResult] = []
    for ch in channels:
        out.append(await dispatch_channel(ch, payload))
    return out
