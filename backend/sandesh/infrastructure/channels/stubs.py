import logging
from typing import Any, Dict

from sandesh.domain.enums import ChannelType
from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def _stub_send(
    channel: ChannelType, payload: Dict[str, Any]
) -> ChannelResult:
    logger.info(
        "Channel %s not wired yet; payload keys=%s",
        channel.value,
        list(payload.keys()),
    )
    return ChannelResult(ok=True, detail=f"{channel.value}_stub_accepted")
