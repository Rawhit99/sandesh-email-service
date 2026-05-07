# License: MIT
# See LICENSE.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SubscriberDto:

    subscriber_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self) -> None:
        self.subscriber_id = str(self.subscriber_id or "").strip()
        self.email = str(self.email or "").strip()
        self.first_name = (
            str(self.first_name).strip()
            if self.first_name is not None
            else None
        )
        self.last_name = (
            str(self.last_name).strip() if self.last_name is not None else None
        )
        if not self.subscriber_id:
            raise ValueError("subscriber_id is required")
        if not self.email or "@" not in self.email:
            raise ValueError("email must be a valid email address")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "subscriberId": self.subscriber_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
        }
