# License: MIT
# See LICENSE.
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from exceptions.handlers import register_exception_handlers
from middleware.rate_limit import limiter
from middleware.request_size_limit import RequestSizeLimitMiddleware
from middleware.request_id import RequestIdMiddleware
from middleware.security_headers import SecurityHeadersMiddleware
from models.models import Base, SessionLocal, engine
from routers.health import router as health_router
from routers.auth import router as auth_router
from routers.api_keys import router as api_keys_router
from routers.notifications import router as notifications_router
from routers.templates import router as templates_router
from routers.stats import router as stats_router
from routers.ses import router as ses_router
from routers.settings import router as settings_router
from routers.subscribers import router as subscribers_router
from routers.events import router as events_router
from routers.integrations import router as integrations_router
from routers.platform_organizations import (
    router as platform_organizations_router,
)
from routers.credentials import router as credentials_router
from services.auth_service import ensure_bootstrap_platform_admin


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Email Notification System API",
    description="API for managing email notifications and templates",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
register_exception_handlers(app)


@app.on_event("startup")
def bootstrap_platform_admin() -> None:
    db = SessionLocal()
    try:
        ensure_bootstrap_platform_admin(db)
    finally:
        db.close()

allow_origins = [
    x.strip() for x in settings.cors_allow_origins.split(",") if x.strip()
]
allow_methods = [
    x.strip() for x in settings.cors_allow_methods.split(",") if x.strip()
]
allow_headers = (
    ["*"]
    if settings.cors_allow_headers.strip() == "*"
    else [
        x.strip() for x in settings.cors_allow_headers.split(",") if x.strip()
    ]
)
trusted_hosts = [
    x.strip() for x in settings.trusted_hosts.split(",") if x.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=allow_methods
    or ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=allow_headers,
    expose_headers=["X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts or ["*"])
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)

"""Main application entry composed from routers."""

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(notifications_router)
app.include_router(templates_router)
app.include_router(stats_router)
app.include_router(ses_router)
app.include_router(settings_router)
app.include_router(subscribers_router)
app.include_router(events_router)
app.include_router(integrations_router)
app.include_router(platform_organizations_router)
app.include_router(credentials_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.api_host, port=settings.api_port, reload=True
    )
