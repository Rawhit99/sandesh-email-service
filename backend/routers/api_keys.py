from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import APIKey, User, get_db
from models.schemas import APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
from middleware.auth import get_current_user_from_token

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])

@router.post("", response_model=APIKeyCreateResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_key = APIKey.generate_key()
    key_hash = APIKey.hash_key(new_key)
    key_prefix = new_key[:20]

    api_key_obj = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        is_active=True
    )
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    return APIKeyCreateResponse(
        id=api_key_obj.id,
        key=new_key,
        key_prefix=key_prefix,
        created_at=api_key_obj.created_at
    )

@router.get("", response_model=list[APIKeyResponse])
async def get_api_keys(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    api_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return api_keys

@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user.id
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}


