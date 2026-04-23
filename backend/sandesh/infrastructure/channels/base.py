from dataclasses import dataclass
from typing import Any, Dict, Protocol

from sandesh.domain.enums import ChannelType


@dataclass
class ChannelResult:
    ok: bool
    detail: str = ""


class Channel(Protocol):
    """Pluggable outbound channel (Slack, Teams, FCM, …)."""

    name: ChannelType

    async def send(self, payload: Dict[str, Any]) -> ChannelResult:
        ...
