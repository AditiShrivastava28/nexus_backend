"""
Authentication API routes.

This module provides endpoints for user login and registration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import UserCreate, UserLogin, LoginResponse, UserResponse
from ..services.auth import AuthService
from ..services.employee import EmployeeService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Args:
        login_data: Email and password credentials
        db: Database session
        
    Returns:
        LoginResponse: Access token and user data
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_token_for_user(user)
    
    # Get employee profile for additional data
    employee = EmployeeService.get_employee_by_user_id(db, user.id)
    
    user_response = UserResponse(
        id=user.id,
        name=user.full_name,
        role=user.role,
        avatarUrl=employee.avatar_url if employee else None,
        employeeId=employee.employee_id if employee else None,
        department=employee.department if employee else None
    )
    
    return LoginResponse(access_token=access_token, user=user_response)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 if email already registered
    """
    # Check if user already exists
    existing_user = AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user and employee profile
    # Generate a unique employee ID
    import random
    employee_id = f"EMP{random.randint(10000, 99999)}"
    
    EmployeeService.create_employee(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        employee_id=employee_id
    )
    
    return {"message": "User registered successfully"}
