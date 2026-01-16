"""
Authentication API endpoints
Login, registration, token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models import User, ActivityLog
from schemas import (
    UserCreate, UserResponse, Token, LoginRequest,
    SuccessResponse
)
from auth import (
    authenticate_user, create_access_token, get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============================================================================
# Registration
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user

    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Minimum 8 characters
    - **full_name**: Optional full name
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new user
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        role="user",  # Default role
        is_active=True,
        is_verified=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Log registration
    log = ActivityLog(
        user_id=db_user.id,
        action="register",
        resource_type="user",
        resource_id=db_user.id,
        details={"email": user.email}
    )
    db.add(log)
    db.commit()

    return db_user

# ============================================================================
# Login
# ============================================================================

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login

    - **username**: User's email address (OAuth2 spec uses 'username')
    - **password**: User's password

    Returns JWT access token
    """
    # OAuth2 spec uses 'username' field, but we authenticate with email
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Log login
    log = ActivityLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id
    )
    db.add(log)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    JSON-based login (alternative to OAuth2 form)

    - **email**: User's email
    - **password**: User's password

    Returns JWT access token
    """
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Log login
    log = ActivityLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id
    )
    db.add(log)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

# ============================================================================
# Current User
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    Requires authentication (Bearer token)
    """
    return current_user

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user

    Note: JWT tokens can't be invalidated server-side
    Client should discard the token
    This endpoint logs the logout action for audit purposes
    """
    # Log logout
    log = ActivityLog(
        user_id=current_user.id,
        action="logout",
        resource_type="user",
        resource_id=current_user.id
    )
    db.add(log)
    db.commit()

    return SuccessResponse(
        success=True,
        message="Logged out successfully"
    )
