from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.core.exceptions import http_401_unauthorized, http_403_forbidden
from app.database import get_db
from app.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise http_401_unauthorized("Invalid authentication token")
    
    email = payload.get("sub")
    if email is None:
        raise http_401_unauthorized("Invalid token payload")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise http_401_unauthorized("User not found")
    
    if not user.is_active:
        raise http_403_forbidden("User account is inactive")
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    """
    if not current_user.is_active:
        raise http_403_forbidden("User account is inactive")
    
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get the current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        email = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        return None