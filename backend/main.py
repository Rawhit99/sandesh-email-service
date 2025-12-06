from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from config import settings
from models.models import Base, engine
from routers.health import router as health_router
from routers.auth import router as auth_router
from routers.api_keys import router as api_keys_router
from routers.audit import router as audit_router
from routers.notifications import router as notifications_router
from routers.templates import router as templates_router
from routers.stats import router as stats_router
from routers.ses import router as ses_router
from routers.settings import router as settings_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Email Notification System API",
    description="API for managing email notifications and templates",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Main application entry, now composed from routers without changing behavior."""

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(audit_router)
app.include_router(notifications_router)
app.include_router(templates_router)
app.include_router(stats_router)
app.include_router(ses_router)
app.include_router(settings_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )