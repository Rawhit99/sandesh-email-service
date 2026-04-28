from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SubscriberCreateRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscriberId: str = Field(..., min_length=1, max_length=255)
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: EmailStr
