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

    def to_payload(self) -> Dict[str, Any]:
        return {
            "subscriberId": self.subscriber_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
        }
