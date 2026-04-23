from fastapi import APIRouter, Depends
from middleware.auth import get_current_user_from_token
from models.models import get_db
from models.schema_domains.access import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
)
from services.api_key_service import (
    create_api_key as create_api_key_service,
    delete_api_key as delete_api_key_service,
    list_api_keys as list_api_keys_service,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyCreateResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    _ = api_key_data
    return create_api_key_service(db, current_user["sub"])


@router.get("", response_model=list[APIKeyResponse])
async def get_api_keys(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    return list_api_keys_service(db, current_user["sub"])


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    return delete_api_key_service(db, current_user["sub"], key_id)
