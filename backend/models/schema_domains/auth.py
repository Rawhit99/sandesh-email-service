from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    password: str
    organization_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")

        has_alpha = any(char.isalpha() for char in value)
        has_digit = any(char.isdigit() for char in value)
        has_special = any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value)

        if not (has_alpha and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one letter, one number, and one special character"
            )
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    organization_id: Optional[int] = None
    organization_name: Optional[str]
    organization_role: Optional[str] = None
    is_platform_admin: bool = False
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
