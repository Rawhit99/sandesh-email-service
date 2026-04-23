from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime
import os
from config import settings
from sqlalchemy.orm import Session
from models.models import get_db, APIKey, User
from middleware.auth_utils import decode_access_token

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

class APIKeyAuth:
    def __init__(self):
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> set:
        """Load API keys from environment variables"""
        api_keys = set()
        
        # Load from environment variable (comma-separated)
        env_keys = os.getenv("API_KEYS", "")
        if env_keys:
            api_keys.update(key.strip() for key in env_keys.split(",") if key.strip())
        
        # Load from individual environment variables
        for i in range(1, 11):  # Support up to 10 API keys
            key = os.getenv(f"API_KEY_{i}")
            if key:
                api_keys.add(key.strip())
        
        return api_keys
    
    def verify_api_key(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
        """Verify API key from Authorization header"""
        api_key = credentials.credentials
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return api_key

# Create auth instance
auth = APIKeyAuth()

# Dependency for protected routes
def get_current_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    return auth.verify_api_key(credentials)

# New authentication dependencies
def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def get_current_user_from_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from API key"""
    api_key = credentials.credentials
    
    # First check environment API keys
    if api_key in auth.api_keys:
        # Return a system user or None for env keys
        return None
    
    # Check database API keys
    api_key_obj = db.query(APIKey).filter(
        APIKey.is_active == True
    ).all()
    
    for key_obj in api_key_obj:
        if APIKey.verify_key(api_key, key_obj.key_hash):
            # Update last used
            key_obj.last_used_at = datetime.utcnow()
            db.commit()
            
            # Get the user
            user = db.query(User).filter(User.id == key_obj.user_id).first()
            return user
    
    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def resolve_user_from_bearer_token(db: Session, token: str) -> Optional[User]:
    """Resolve tenant user from JWT or database API key. Env-only API keys return None."""
    if not token or not str(token).strip():
        return None
    t = str(token).strip()
    payload = decode_access_token(t)
    if payload and payload.get("sub"):
        user = db.query(User).filter(User.username == payload["sub"]).first()
        if user:
            return user
    if t in auth.api_keys:
        return None
    for key_obj in db.query(APIKey).filter(APIKey.is_active.is_(True)).all():
        if APIKey.verify_key(t, key_obj.key_hash):
            key_obj.last_used_at = datetime.utcnow()
            db.commit()
            return db.query(User).filter(User.id == key_obj.user_id).first()
    return None


def _extract_auth_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    if credentials and credentials.credentials:
        return credentials.credentials
    raw = request.headers.get("Authorization") or request.headers.get("authorization")
    if not raw:
        return None
    parts = str(raw).strip().split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme in {"bearer", "apikey"} and token:
        return token
    return None


def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Resolve user from JWT (dashboard) or database API key (optional)."""
    token = _extract_auth_token(request, credentials)
    if token is None:
        return None
    return resolve_user_from_bearer_token(db, token)


def get_current_user_any(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_optional),
    db: Session = Depends(get_db),
) -> User:
    """Require a logged-in user (JWT) or a database-linked API key."""
    token = _extract_auth_token(request, credentials)
    user = resolve_user_from_bearer_token(db, token or "")
    if user is not None:
        return user
    raise HTTPException(
        status_code=401,
        detail="Use a database API key from API Keys, or sign in with JWT",
    )
