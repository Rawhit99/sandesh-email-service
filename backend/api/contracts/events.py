from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class EventOverrideEmail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to: Optional[EmailStr] = None
    cc: Optional[List[EmailStr]] = None
    subject: Optional[str] = None
    senderName: Optional[str] = None
    integrationIdentifier: Optional[str] = None


class EventOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Optional[EventOverrideEmail] = None


class EventAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: str
    name: str
    mime: str = "application/octet-stream"


class EventTo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscriberId: str


class EventPayload(BaseModel):
    # Dynamic template variables are allowed.
    model_config = ConfigDict(extra="allow")
    attachments: Optional[List[EventAttachment]] = None


class EventTriggerRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    to: EventTo
    payload: EventPayload
    overrides: Optional[EventOverrides] = None
