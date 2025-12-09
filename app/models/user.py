"""
User model for authentication and authorization.

This module defines the User model which handles authentication
credentials and role-based access control.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    """
    Enumeration of user roles in the system.
    
    Attributes:
        ADMIN: Administrator with full access
        MANAGER: Manager with team management capabilities
        EMPLOYEE: Regular employee with limited access
    """
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    """
    User model for authentication.
    
    Attributes:
        id: Primary key
        email: Unique email address for login
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (admin, manager, employee)
        is_active: Whether the user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.EMPLOYEE.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
