# License: MIT
# Typing stubs for sandesh.dto (implementation may be compiled).
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class SubscriberDto:
    subscriber_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self) -> None: ...
    def to_payload(self) -> Dict[str, Any]: ...
