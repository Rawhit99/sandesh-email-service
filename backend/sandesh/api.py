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

JsonDict = Dict[str, Any]


@dataclass
class _ChannelCredentials:
    device_tokens: List[str]


@dataclass
class _SubscriberChannel:
    provider_id: str
    credentials: _ChannelCredentials


class _SubscriberResource:

    def __init__(self, raw: JsonDict) -> None:
        self.raw = raw
        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        tokens = self._normalize_tokens(data.get("fcm_device_tokens"))
        self._channels = [
            _SubscriberChannel(
                provider_id="fcm",
                credentials=_ChannelCredentials(device_tokens=tokens),
            )
        ]

    @staticmethod
    def _normalize_tokens(raw: Any) -> List[str]:
        if not isinstance(raw, list):
            return []
        return [str(token).strip() for token in raw if str(token).strip()]


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
        payload: JsonDict,
        overrides: Optional[JsonDict] = None,
    ) -> JsonDict:
        subscriber_id = self._resolve_subscriber_id(recipients)
        if not subscriber_id:
            raise ValueError("recipients must contain a subscriber id")

        body: JsonDict = {
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
            raise self._http_error_from_sdk(exc) from exc

    def _trigger_legacy_from_v1(
        self,
        *,
        name: str,
        subscriber_id: str,
        payload: JsonDict,
        overrides: Optional[JsonDict],
    ) -> JsonDict:
        inferred_email = self._infer_email_for_legacy(payload, overrides)
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
                raise self._http_error_from_sdk(exc) from exc
            email = str(subscriber.get("email") or "").strip()
        if not email:
            raise HTTPError(
                (
                    "Legacy trigger fallback requires subscriber email, "
                    f"but subscriber `{subscriber_id}` has no email."
                )
            )

        email_overrides = self._email_overrides(overrides)
        legacy_body: JsonDict = {
            "template_id": name,
            "email": email,
            "payload": payload,
        }
        attachments = self._legacy_attachments_from_payload(payload)
        if attachments:
            legacy_body["attachments"] = attachments
        self._apply_legacy_email_overrides(legacy_body, email_overrides)

        try:
            return self._sdk.events_trigger_legacy(legacy_body)
        except SandeshAPIError as exc:
            raise self._http_error_from_sdk(exc) from exc

    @staticmethod
    def _infer_email_for_legacy(
        payload: JsonDict,
        overrides: Optional[JsonDict],
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

        email_overrides = EventApi._email_overrides(overrides)
        for key in ("to", "cc"):
            inferred = EventApi._first_email(email_overrides.get(key))
            if inferred:
                return inferred
        return None

    @staticmethod
    def _resolve_subscriber_id(recipients: Union[str, List[str]]) -> str:
        if isinstance(recipients, list):
            if not recipients:
                raise ValueError("recipients cannot be empty")
            return str(recipients[0]).strip()
        return str(recipients).strip()

    @staticmethod
    def _first_email(value: Any) -> Optional[str]:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if "@" in cleaned else None
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    cleaned = item.strip()
                    if "@" in cleaned:
                        return cleaned
        return None

    @staticmethod
    def _email_overrides(
        overrides: Optional[JsonDict],
    ) -> JsonDict:
        if not isinstance(overrides, dict):
            return {}
        email_overrides = overrides.get("email")
        return email_overrides if isinstance(email_overrides, dict) else {}

    @staticmethod
    def _apply_legacy_email_overrides(
        legacy_body: JsonDict, email_overrides: JsonDict
    ) -> None:
        cc = email_overrides.get("cc")
        if isinstance(cc, list) and cc:
            legacy_body["cc_emails"] = cc
        sender_name = email_overrides.get("senderName")
        if isinstance(sender_name, str) and sender_name.strip():
            legacy_body["sender_name"] = sender_name.strip()
        subject = email_overrides.get("subject")
        if isinstance(subject, str) and subject.strip():
            legacy_body["subject"] = subject.strip()
        integration_identifier = email_overrides.get("integrationIdentifier")
        if (
            isinstance(integration_identifier, str)
            and integration_identifier.strip()
            and isinstance(legacy_body.get("payload"), dict)
        ):
            legacy_body["payload"]["_integration_identifier"] = (
                integration_identifier.strip()
            )

    @staticmethod
    def _legacy_attachments_from_payload(
        payload: JsonDict,
    ) -> List[JsonDict]:
        raw_items = payload.get("attachments")
        if not isinstance(raw_items, list):
            return []
        out: List[JsonDict] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            file_b64 = item.get("file")
            filename = item.get("name")
            if not isinstance(file_b64, str) or not file_b64.strip():
                continue
            if not isinstance(filename, str) or not filename.strip():
                continue
            mime = item.get("mime")
            out.append(
                {
                    "filename": filename.strip(),
                    "content_base64": file_b64.strip(),
                    "mime_type": (
                        str(mime).strip()
                        if isinstance(mime, str) and mime.strip()
                        else "application/octet-stream"
                    ),
                }
            )
        return out

    @staticmethod
    def _http_error_from_sdk(exc: SandeshAPIError) -> HTTPError:
        response = httpx.Response(
            status_code=exc.status_code,
            request=httpx.Request(exc.request_method, exc.request_url),
        )
        return HTTPError(str(exc), response=response)


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

    def create(self, subscriber: SubscriberDto) -> JsonDict:
        return self._sdk.create_subscriber(subscriber.to_payload())

    def delete(self, subscriber_id: str) -> JsonDict:
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
    ) -> JsonDict:
        if provider_id != "fcm":
            raise ValueError("Only provider_id='fcm' is supported")
        current = self._sdk.get_subscriber(subscriber_id)
        current_data = (
            current.get("data")
            if isinstance(current.get("data"), dict)
            else {}
        )
        new_data = dict(current_data)
        new_data["fcm_device_tokens"] = _SubscriberResource._normalize_tokens(
            device_tokens
        )
        return self._sdk.update_subscriber(
            subscriber_id,
            {"data": new_data},
        )
