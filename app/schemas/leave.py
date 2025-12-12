"""
Leave-related Pydantic schemas.

This module defines schemas for leave request and calendar operations.
"""

from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import date


class LeaveRequest(BaseModel):
    """
    Schema for applying for leave.
    
    Attributes:
        start_date: Leave start date
        end_date: Leave end date
        reason: Reason for leave
    """
    start_date: date
    end_date: date
    reason: Optional[str] = None
    # Leave type: 'paid' or 'unpaid'. This field is required in the request.
    leave_type: Literal["paid", "unpaid"]


class LeaveResponse(BaseModel):
    """
    Leave request response.
    
    Attributes:
        id: Leave ID
        start_date: Leave start date
        end_date: Leave end date
    days: Number of leave days
    reason: Reason for leave
    """
    id: int
    start_date: date
    end_date: date
    days: float
    reason: Optional[str] = None
    leave_type: str

    class Config:
        from_attributes = True


class LeaveBalanceResponse(BaseModel):
    """
    Leave balance response for the current year.
    
    Attributes:
        total_days: Total allocated days for the year
        used_days: Days used so far
        remaining_days: Days remaining
    """
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
        start_date: Leave start date
        end_date: Leave end date
    """
    id: int
    employee_name: str
    start_date: date
    end_date: date
    leave_type: str

    class Config:
        from_attributes = True


class LeaveApplyResponse(BaseModel):
    """
    Response returned when a leave is applied.

    Attributes:
        start_date: Leave start date
        end_date: Leave end date
        leave_taken: Number of leave days deducted (always 1)
        reason: Reason for leave
        total_leaves: Total allocated leaves for the year
    """
    start_date: date
    end_date: date
    leave_taken: int
    reason: Optional[str] = None
    leave_type: str
    total_leaves: int
    remaining_leaves: int

    class Config:
        from_attributes = True


class LeaveBalanceUpdate(BaseModel):
    """
    Schema for admin updating leave allocation (total days) for an employee/year.
    """
    total_days: int

    class Config:
        from_attributes = True
