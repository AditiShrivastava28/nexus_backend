"""
Leave-related Pydantic schemas.

This module defines schemas for leave request and calendar operations.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class LeaveRequest(BaseModel):
    """
    Schema for applying for leave.
    
    Attributes:
        leave_type: Type of leave
        start_date: Leave start date
        end_date: Leave end date
        reason: Reason for leave
    """
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveResponse(BaseModel):
    """
    Leave request response.
    
    Attributes:
        id: Leave ID
        leave_type: Type of leave
        start_date: Leave start date
        end_date: Leave end date
        days: Number of leave days
        reason: Reason for leave
        status: Request status
    """
    id: int
    leave_type: str
    start_date: date
    end_date: date
    days: float
    reason: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class LeaveBalanceResponse(BaseModel):
    """
    Leave balance response.
    
    Attributes:
        leave_type: Type of leave
        total_days: Total allocated days
        used_days: Days used
        remaining_days: Days remaining
    """
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float

    class Config:
        from_attributes = True


class LeaveCalendarItem(BaseModel):
    """
    Leave calendar item for calendar view.
    
    Attributes:
        id: Leave ID
        employee_name: Employee name
        leave_type: Type of leave
        start_date: Leave start date
        end_date: Leave end date
        status: Leave status
    """
    id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    status: str

    class Config:
        from_attributes = True
