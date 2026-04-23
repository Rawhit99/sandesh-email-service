"""Central SlowAPI limiter (IP / X-Forwarded-For)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from config import settings


def _client_key(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip() or get_remote_address(request)
    return get_remote_address(request)


_default_limits: list[str] = []
if settings.rate_limit_enabled and settings.rate_limit_default:
    _default_limits = [settings.rate_limit_default]

limiter = Limiter(
    key_func=_client_key,
    default_limits=_default_limits,
    enabled=settings.rate_limit_enabled,
)
