from config import settings
from fastapi import APIRouter, Depends, Request, status
from middleware.auth import get_current_user_from_token
from middleware.rate_limit import limiter
from models.models import get_db
from models.schema_domains.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from services.auth_service import (
    get_user_by_username,
    login_user,
    register_user,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit(settings.rate_limit_auth_register)
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    _ = request
    return register_user(db, user_data)


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.rate_limit_auth_login)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    _ = request
    return login_user(db, credentials)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    return get_user_by_username(db, current_user["sub"])
