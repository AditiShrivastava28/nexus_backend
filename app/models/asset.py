"""
Asset management model.

This module defines the Asset model for tracking company assets
assigned to employees (laptops, phones, etc.).
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Asset(Base):
    """
    Company asset assigned to an employee.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        name: Asset name
        asset_type: Type of asset (laptop, phone, etc.)
        serial_number: Serial number
        assigned_date: Date when asset was assigned
        status: Asset status (assigned, returned, damaged)
    """
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100))
    serial_number = Column(String(100), unique=True)
    assigned_date = Column(Date)
    status = Column(String(50), default="assigned")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="assets")
