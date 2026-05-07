# License: MIT
# See LICENSE.
"""Typed exceptions raised by the Sandesh SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SandeshError(Exception):
    """Base class for all SDK errors."""

    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class SandeshAPIError(SandeshError):
    """Raised when API responds with a non-2xx status code."""

    status_code: int
    response_body: Any
    request_method: str
    request_url: str


@dataclass
class SandeshNetworkError(SandeshError):
    """Raised for transport/network-level failures."""

    request_method: Optional[str] = None
    request_url: Optional[str] = None
