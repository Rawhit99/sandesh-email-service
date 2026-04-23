from __future__ import annotations

from typing import Any, Dict, Optional


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class ValidationError(AppError):
    def __init__(
        self, message: str, *, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message,
            status_code=422,
            code="validation_error",
            details=details,
        )


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409, code="conflict")


class BadRequestError(AppError):
    def __init__(
        self, message: str, *, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message,
            status_code=400,
            code="bad_request",
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=403, code="forbidden")


class UnauthorizedError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=401, code="unauthorized")
