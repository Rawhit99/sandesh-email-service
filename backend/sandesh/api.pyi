# License: MIT
# Typing stubs for sandesh.api (implementation may be compiled).
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from sandesh.dto import SubscriberDto


class SubscriberResource:
    """Resource returned by SubscriberApi.get()."""

    raw: Dict[str, Any]

    def __init__(self, raw: Dict[str, Any]) -> None: ...


class EventApi:
    def __init__(
        self, url: str, api_key: str, *, timeout: float = 60.0
    ) -> None: ...
    def trigger(
        self,
        *,
        name: str,
        recipients: Union[str, List[str]],
        payload: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...


class SubscriberApi:
    def __init__(
        self, url: str, api_key: str, *, timeout: float = 60.0
    ) -> None: ...
    def create(self, subscriber: SubscriberDto) -> Dict[str, Any]: ...
    def delete(self, subscriber_id: str) -> Dict[str, Any]: ...
    def get(self, subscriber_id: str) -> SubscriberResource: ...
    def credentials(
        self,
        *,
        subscriber_id: str,
        provider_id: str,
        device_tokens: List[str],
    ) -> Dict[str, Any]: ...
