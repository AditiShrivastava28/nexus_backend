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
        start_date: Leave start date
        end_date: Leave end date
        days: Number of leave days
        half_day: Whether this is a half-day leave
        half_day_type: Type of half-day leave ('first_half' or 'second_half')
        reason: Reason for leave
            # Approval/status tracking removed from this model.
    """
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    # Simple leave record with dates and days; leave_type (DB column)
    # will be removed via migration and is not used by the API.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Float, default=1.0)
    # leave_type indicates whether this is a 'paid' or 'unpaid' leave.
    # Paid leaves are counted against the yearly allocation (12 days).
    # Unpaid leaves are not deducted from the paid balance.
    leave_type = Column(String, nullable=False)
    reason = Column(Text)
    # Half-day leave support
    half_day = Column(String, default="false")  # Store as string for SQLite compatibility
    half_day_type = Column(String, nullable=True)  # 'first_half' or 'second_half' when half_day is true
    # Note: simple leave record with dates and days. Approval/status is not tracked here.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="leaves", foreign_keys=[employee_id])



class LeaveBalance(Base):
    """
    Leave balance for each employee for a given year.

    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        year: Year for the balance
        total_days: Total allocated days
        used_days: Days already used
        remaining_days: Days remaining
        leave_type: Type of leave balance (e.g., 'paid', 'unpaid')
    """
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    # We track a single leave balance per employee per year (no per-type breakdown)
    year = Column(Integer, nullable=False)
    # Default allocation is 12 days per year
    total_days = Column(Float, default=12)
    used_days = Column(Float, default=0)
    remaining_days = Column(Float, default=12)
    # Leave type for the balance (default to 'paid' as this is the main balance type)
    leave_type = Column(String, default="paid", nullable=False)
    

    # Relationships
    employee = relationship("Employee", back_populates="leave_balances")

    # paid_remaining helper removed -- use remaining_days directly



class CorporateLeave(Base):
    """
    Corporate leave model for office-wide holidays and official leaves.
    
    Attributes:
        id: Primary key
        name: Name/occasion of the corporate leave
        date: Date of the corporate leave
        leave_type: Type of leave (National Holiday, Festival, etc.)
        is_recurring: Whether this is a recurring annual leave
        created_by: Admin user who created this leave
        created_at: Creation timestamp
    """
    __tablename__ = "corporate_leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    leave_type = Column(String, nullable=False, default="National Holiday")
    is_recurring = Column(String, default="true", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
