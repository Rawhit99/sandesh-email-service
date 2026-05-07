# License: MIT
# See LICENSE.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx
from requests.models import HTTPError

from sandesh.dto import SubscriberDto
from sandesh.sdk.client import Sandesh
from sandesh.sdk.exceptions import SandeshAPIError


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
        except SandeshAPIError as exc:
            if exc.status_code in {404, 422}:
                return self._trigger_legacy_from_v1(
                    name=name,
                    subscriber_id=subscriber_id,
                    payload=payload or {},
                    overrides=overrides,
                )
            response = httpx.Response(
                status_code=exc.status_code,
                request=httpx.Request(exc.request_method, exc.request_url),
            )
            raise HTTPError(str(exc), response=response) from exc

    def _trigger_legacy_from_v1(
        self,
        *,
        name: str,
        subscriber_id: str,
        payload: Dict[str, Any],
        overrides: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        inferred_email = self._infer_email_for_legacy(payload, overrides)
        # Optimized fallback: if we can infer an email directly from v1-style
        # payload/overrides, avoid subscriber lookup entirely.
        email = inferred_email or ""
        if not email:
            try:
                subscriber = self._sdk.get_subscriber(subscriber_id)
            except SandeshAPIError as exc:
                if exc.status_code == 404:
                    raise HTTPError(
                        (
                            "Legacy trigger fallback requires an existing subscriber, "
                            f"but `{subscriber_id}` was not found at "
                            "`/api/v1/subscribers/{subscriber_id}`, and no recipient "
                            "email could be inferred from payload/overrides. "
                            "Provide one of: payload.email, payload.vendor_email, "
                            "payload.recipient_email, payload.to_email, "
                            "payload.user_email, overrides.email.to, "
                            "or overrides.email.cc."
                        ),
                        response=httpx.Response(
                            status_code=404,
                            request=httpx.Request(
                                "GET",
                                f"{self._sdk._base}/api/v1/subscribers/{subscriber_id}",
                            ),
                        ),
                    ) from exc
                response = httpx.Response(
                    status_code=exc.status_code,
                    request=httpx.Request(exc.request_method, exc.request_url),
                )
                raise HTTPError(str(exc), response=response) from exc
            email = str(subscriber.get("email") or "").strip()
        if not email:
            raise HTTPError(
                (
                    "Legacy trigger fallback requires subscriber email, "
                    f"but subscriber `{subscriber_id}` has no email."
                )
            )

        email_overrides: Dict[str, Any] = {}
        if isinstance(overrides, dict):
            maybe_email = overrides.get("email")
            if isinstance(maybe_email, dict):
                email_overrides = maybe_email

        legacy_body: Dict[str, Any] = {
            "template_id": name,
            "email": email,
            "payload": payload,
        }
        cc = email_overrides.get("cc")
        if isinstance(cc, list) and cc:
            legacy_body["cc_emails"] = cc
        sender_name = email_overrides.get("senderName")
        if isinstance(sender_name, str) and sender_name.strip():
            legacy_body["sender_name"] = sender_name.strip()
        subject = email_overrides.get("subject")
        if isinstance(subject, str) and subject.strip():
            legacy_body["subject"] = subject.strip()

        try:
            return self._sdk.events_trigger_legacy(legacy_body)
        except SandeshAPIError as exc:
            response = httpx.Response(
                status_code=exc.status_code,
                request=httpx.Request(exc.request_method, exc.request_url),
            )
            raise HTTPError(str(exc), response=response) from exc

    @staticmethod
    def _infer_email_for_legacy(
        payload: Dict[str, Any],
        overrides: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        candidate_keys = (
            "email",
            "vendor_email",
            "recipient_email",
            "to_email",
            "user_email",
        )
        for key in candidate_keys:
            raw = payload.get(key)
            if isinstance(raw, str) and "@" in raw and raw.strip():
                return raw.strip()

        if isinstance(overrides, dict):
            email_overrides = overrides.get("email")
            if isinstance(email_overrides, dict):
                to_value = email_overrides.get("to")
                if isinstance(to_value, str) and "@" in to_value and to_value.strip():
                    return to_value.strip()
                if isinstance(to_value, list):
                    for item in to_value:
                        if isinstance(item, str) and "@" in item and item.strip():
                            return item.strip()
                cc_value = email_overrides.get("cc")
                if isinstance(cc_value, str):
                    if "@" in cc_value and cc_value.strip():
                        return cc_value.strip()
                if isinstance(cc_value, list):
                    for item in cc_value:
                        if isinstance(item, str) and "@" in item and item.strip():
                            return item.strip()
        return None


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
