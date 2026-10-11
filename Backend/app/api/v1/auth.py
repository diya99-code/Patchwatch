from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    validate_password,
)
from app.core.exceptions import http_400_bad_request, http_401_unauthorized
from app.database import get_db
from app.models import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise http_400_bad_request("Email is already registered")
    
    # Validate password
    password_errors = validate_password(user_data.password)
    if password_errors:
        raise http_400_bad_request(f"Password validation failed: {', '.join(password_errors)}")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        created_at=db_user.created_at.isoformat(),
        updated_at=db_user.updated_at.isoformat(),
    )


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    User login and JWT token generation.
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise http_401_unauthorized("Invalid email or password")
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise http_401_unauthorized("Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise http_401_unauthorized("User account is inactive")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat(),
    )