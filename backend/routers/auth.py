from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from middleware.auth import get_current_user_from_token
from middleware.auth_utils import create_access_token, get_password_hash, verify_password
from middleware.rate_limit import limiter
from models.models import Organization, User, get_db
from models.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from middleware.tenant_scope import user_effective_platform_admin


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        organization_id=user.organization_id,
        organization_name=user.organization_name,
        organization_role=user.organization_role,
        is_platform_admin=user_effective_platform_admin(user),
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _assign_organization_for_new_user(
    db: Session, organization_name: Optional[str]
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    if not organization_name or not str(organization_name).strip():
        return None, None, None
    display = str(organization_name).strip()
    org = db.query(Organization).filter(Organization.name == display).first()
    if org:
        return org.id, display, "member"
    org = Organization(name=display)
    db.add(org)
    try:
        db.flush()
        return org.id, display, "admin"
    except IntegrityError:
        db.rollback()
        org = db.query(Organization).filter(Organization.name == display).first()
        if not org:
            raise HTTPException(status_code=500, detail="Could not assign organization")
        return org.id, display, "member"

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth_register)
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(user_data.password)
    org_id, org_display, org_role = _assign_organization_for_new_user(db, user_data.organization_name)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        organization_id=org_id,
        organization_name=org_display,
        organization_role=org_role,
        is_platform_admin=False,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _user_response(new_user)

@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.rate_limit_auth_login)
async def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=_user_response(user),
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user_from_token)):
    db = next(get_db())
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return _user_response(user)
    finally:
        db.close()


