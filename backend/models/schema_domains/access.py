from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: int
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    id: int
    key: str
    key_prefix: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    email_to: Optional[str]
    template_id: Optional[str]
    payload: Optional[Dict[str, Any]]
    status: Optional[str]
    error_message: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
