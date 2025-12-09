"""
FastAPI dependencies.

This module provides dependency injection functions for
authentication and database access.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from .security import decode_access_token


# HTTP Bearer token security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the currently authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_employee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Employee:
    """
    Dependency to get the employee profile of the current user.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Employee: The employee profile object
        
    Raises:
        HTTPException: 404 if employee profile not found
    """
    employee = db.query(Employee).filter(
        Employee.user_id == current_user.id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )
    
    return employee


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_manager_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require manager or admin role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The manager or admin user
        
    Raises:
        HTTPException: 403 if user is not a manager or admin
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required"
        )
    return current_user
