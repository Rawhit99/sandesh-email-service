from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from exceptions.app_errors import AppError

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "") or "")


def _error_payload(
    *,
    message: str,
    code: str,
    request_id: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "message": message,
            "code": code,
            "request_id": request_id,
            "details": details or {},
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(
        request: Request, exc: AppError
    ) -> JSONResponse:
        rid = _request_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                message=exc.message,
                code=exc.code,
                request_id=rid,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        rid = _request_id(request)
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                message="Request validation failed",
                code="validation_error",
                request_id=rid,
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        rid = _request_id(request)
        message = (
            exc.detail if isinstance(exc.detail, str) else "Request failed"
        )
        details = exc.detail if isinstance(exc.detail, dict) else {}
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                message=message,
                code="http_error",
                request_id=rid,
                details=details,
            ),
            headers=exc.headers,
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        rid = _request_id(request)
        logger.exception("Database error request_id=%s", rid, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                message="Database operation failed",
                code="database_error",
                request_id=rid,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        rid = _request_id(request)
        logger.exception(
            "Unhandled exception request_id=%s", rid, exc_info=exc
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                message="Internal server error",
                code="internal_error",
                request_id=rid,
            ),
        )
