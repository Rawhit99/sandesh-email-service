from __future__ import annotations

from fastapi import HTTPException
from models.models import APIKey, User
from models.schema_domains.access import APIKeyCreateResponse
from sqlalchemy.orm import Session


def _get_user(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def create_api_key(db: Session, username: str) -> APIKeyCreateResponse:
    user = _get_user(db, username)
    new_key = APIKey.generate_key()
    api_key = APIKey(
        user_id=user.id,
        key_hash=APIKey.hash_key(new_key),
        key_prefix=new_key[:20],
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return APIKeyCreateResponse(
        id=api_key.id,
        key=new_key,
        key_prefix=api_key.key_prefix,
        created_at=api_key.created_at,
    )


def list_api_keys(db: Session, username: str) -> list[APIKey]:
    user = _get_user(db, username)
    return db.query(APIKey).filter(APIKey.user_id == user.id).all()


def delete_api_key(db: Session, username: str, key_id: int) -> dict:
    user = _get_user(db, username)
    api_key = (
        db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(api_key)
    db.commit()
    return {"message": "API key deleted successfully"}
