"""
Authentication service.

This module provides authentication-related business logic.
"""

from sqlalchemy.orm import Session
from typing import Optional

from ..models.user import User
from ..models.employee import Employee
from ..utils.security import verify_password, get_password_hash, create_access_token


class AuthService:
    """
    Service class for authentication operations.
    
    Provides methods for user registration, login, and password management.
    """
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            Optional[User]: User object if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_user(
        db: Session, 
        email: str, 
        password: str, 
        full_name: str,
        role: str = "employee"
    ) -> User:
        """
        Create a new user account.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password to hash
            full_name: User's full name
            role: User role (default: employee)
            
        Returns:
            User: The created user object
        """
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def reset_password(db: Session, user: User, new_password: str) -> User:
        """
        Reset a user's password.
        
        Args:
            db: Database session
            user: User object to update
            new_password: New plain text password
            
        Returns:
            User: Updated user object
        """
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_token_for_user(user: User) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user: User object
            
        Returns:
            str: JWT access token
        """
        return create_access_token(data={"sub": str(user.id), "email": user.email})
