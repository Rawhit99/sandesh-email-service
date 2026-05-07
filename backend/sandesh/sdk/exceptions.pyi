# License: MIT
# Typing stubs for sandesh.sdk.exceptions (implementation may be compiled).
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class SandeshError(Exception):
    message: str

    def __str__(self) -> str: ...

@dataclass
class SandeshAPIError(SandeshError):
    status_code: int
    response_body: Any
    request_method: str
    request_url: str

@dataclass
class SandeshNetworkError(SandeshError):
    request_method: Optional[str] = None
    request_url: Optional[str] = None
