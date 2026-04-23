from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class SubscriberCreate(BaseModel):
    subscriber_id: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None


class SubscriberResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    subscriber_id: str
    email: str
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriberUpdate(BaseModel):
    email: Optional[EmailStr] = None
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None
