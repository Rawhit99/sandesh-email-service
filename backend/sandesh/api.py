from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx
from requests.models import HTTPError

from sandesh.dto import SubscriberDto
from sandesh.sdk.client import Sandesh


@dataclass
class _ChannelCredentials:
    device_tokens: List[str]


@dataclass
class _SubscriberChannel:
    provider_id: str
    credentials: _ChannelCredentials


class _SubscriberResource:

    def __init__(self, raw: Dict[str, Any]) -> None:
        self.raw = raw
        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        tokens = data.get("fcm_device_tokens", [])
        if not isinstance(tokens, list):
            tokens = []
        self._channels = [
            _SubscriberChannel(
                provider_id="fcm",
                credentials=_ChannelCredentials(
                    device_tokens=[
                        str(token).strip()
                        for token in tokens
                        if str(token).strip()
                    ]
                ),
            )
        ]


class EventApi:

    def __init__(
        self,
        url: str,
        api_key: str,
        *,
        timeout: float = 60.0,
    ) -> None:
        self._sdk = Sandesh(
            base_url=url,
            bearer_token=api_key,
            timeout=timeout,
        )

    def trigger(
        self,
        *,
        name: str,
        recipients: Union[str, List[str]],
        payload: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if isinstance(recipients, list):
            if not recipients:
                raise ValueError("recipients cannot be empty")
            subscriber_id = str(recipients[0]).strip()
        else:
            subscriber_id = str(recipients).strip()
        if not subscriber_id:
            raise ValueError("recipients must contain a subscriber id")

        body: Dict[str, Any] = {
            "name": name,
            "to": {"subscriberId": subscriber_id},
            "payload": payload or {},
        }
        if overrides is not None:
            body["overrides"] = overrides
        try:
            return self._sdk.events_trigger(body)
        except httpx.HTTPStatusError as exc:
            # Keep Novu-style callsites working, which catch requests.HTTPError.
            raise HTTPError(str(exc), response=exc.response) from exc


class SubscriberApi:

    def __init__(
        self,
        url: str,
        api_key: str,
        *,
        timeout: float = 60.0,
    ) -> None:
        self._sdk = Sandesh(
            base_url=url,
            bearer_token=api_key,
            timeout=timeout,
        )

    def create(self, subscriber: SubscriberDto) -> Dict[str, Any]:
        return self._sdk.create_subscriber(subscriber.to_payload())

    def delete(self, subscriber_id: str) -> Dict[str, Any]:
        return self._sdk.deactivate_subscriber(subscriber_id)

    def get(self, subscriber_id: str) -> _SubscriberResource:
        raw = self._sdk.get_subscriber(subscriber_id)
        return _SubscriberResource(raw)

    def credentials(
        self,
        *,
        subscriber_id: str,
        provider_id: str,
        device_tokens: List[str],
    ) -> Dict[str, Any]:
        if provider_id != "fcm":
            raise ValueError("Only provider_id='fcm' is supported")
        current = self._sdk.get_subscriber(subscriber_id)
        current_data = (
            current.get("data")
            if isinstance(current.get("data"), dict)
            else {}
        )
        new_data = dict(current_data)
        new_data["fcm_device_tokens"] = [
            str(token).strip()
            for token in device_tokens
            if str(token).strip()
        ]
        return self._sdk.update_subscriber(
            subscriber_id,
            {"data": new_data},
        )
