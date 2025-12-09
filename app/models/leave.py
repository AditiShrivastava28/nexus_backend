"""
Leave management models.

This module defines models for tracking employee leave requests,
balances, and leave calendar.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Leave(Base):
    """
    Leave request model.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        leave_type: Type of leave (casual, sick, annual, etc.)
        start_date: Leave start date
        end_date: Leave end date
        days: Number of leave days
        reason: Reason for leave
        status: Request status (pending, approved, rejected)
        approved_by: Employee ID who approved/rejected
    """
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Float, default=1.0)
    reason = Column(Text)
    status = Column(String(50), default="pending")
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="leaves", foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approved_by])


class LeaveBalance(Base):
    """
    Leave balance for each employee per leave type.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        leave_type: Type of leave
        year: Year for the balance
        total_days: Total allocated days
        used_days: Days already used
        remaining_days: Days remaining
    """
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    total_days = Column(Float, default=0)
    used_days = Column(Float, default=0)
    remaining_days = Column(Float, default=0)
    
    # Relationships
    employee = relationship("Employee", back_populates="leave_balances")
