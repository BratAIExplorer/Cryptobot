"""
User management API endpoints
Admin operations for user CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, ActivityLog
from schemas import (
    UserResponse, UserCreate, UserUpdate,
    SuccessResponse, ActivityLogResponse
)
from auth import get_current_user, require_admin, get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

# ============================================================================
# User Management (Admin Only)
# ============================================================================

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)

    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID

    - Users can only view their own profile
    - Admins can view any profile
    """
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information

    - Users can only update their own profile
    - Admins can update any profile
    """
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Log update
    log = ActivityLog(
        user_id=current_user.id,
        action="update_user",
        resource_type="user",
        resource_id=user_id,
        details={"fields_updated": list(update_data.keys())}
    )
    db.add(log)
    db.commit()

    return user

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user (Admin only)

    Soft delete by setting is_active = False
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    user.is_active = False
    db.commit()

    # Log deletion
    log = ActivityLog(
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=user_id
    )
    db.add(log)
    db.commit()

    return SuccessResponse(
        success=True,
        message=f"User {user.email} deleted successfully"
    )

# ============================================================================
# Activity Logs
# ============================================================================

@router.get("/{user_id}/activity", response_model=List[ActivityLogResponse])
async def get_user_activity(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user activity log

    - Users can only view their own activity
    - Admins can view any user's activity
    """
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's activity"
        )

    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return activities
