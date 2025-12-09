"""
User-related Pydantic schemas.

This module defines schemas for user authentication and profile operations.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """
    Base user schema with common fields.
    
    Attributes:
        email: User's email address
        full_name: User's full name
    """
    email: str
    full_name: str


class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    Attributes:
        email: User's email address
        password: Plain text password
        full_name: User's full name
    """
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    """
    Schema for user login.
    
    Attributes:
        email: User's email address
        password: Plain text password
    """
    email: str
    password: str


class Token(BaseModel):
    """
    JWT token response schema.
    
    Attributes:
        access_token: JWT access token
        token_type: Token type (bearer)
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Data extracted from JWT token.
    
    Attributes:
        user_id: User's ID
        email: User's email
    """
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """
    User data in API responses.
    
    Attributes:
        id: User ID
        name: User's full name
        role: User role
        avatarUrl: Profile picture URL
        employeeId: Company employee ID
        department: Department name
    """
    id: int
    name: str
    role: str
    avatarUrl: Optional[str] = None
    employeeId: Optional[str] = None
    department: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """
    Login API response.
    
    Attributes:
        access_token: JWT access token
        user: User data
    """
    access_token: str
    user: UserResponse
