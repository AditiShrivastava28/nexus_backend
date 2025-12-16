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
        leave_type: Type of leave ('paid' or 'unpaid')
        half_day: Whether this is a half-day leave
        half_day_type: Type of half-day leave ('first_half' or 'second_half') - required if half_day is True
    """
    start_date: date
    end_date: date
    reason: Optional[str] = None
    # Leave type: 'paid' or 'unpaid'. This field is required in the request.
    leave_type: Literal["paid", "unpaid"]
    # Half-day leave support
    half_day: bool = False
    half_day_type: Optional[Literal["first_half", "second_half"]] = None


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
        leave_taken: Number of leave days deducted (float, supports half-day)
        reason: Reason for leave
        leave_type: Type of leave ('paid' or 'unpaid')
        total_leaves: Total allocated leaves for the year
        remaining_leaves: Remaining leaves after this request
        half_day: Whether this is a half-day leave
        half_day_type: Type of half-day leave ('first_half' or 'second_half')
    """
    start_date: date
    end_date: date
    leave_taken: float
    reason: Optional[str] = None
    leave_type: str
    total_leaves: int
    remaining_leaves: float
    half_day: bool = False
    half_day_type: Optional[str] = None

    class Config:
        from_attributes = True



class LeaveBalanceUpdate(BaseModel):
    """
    Schema for admin updating leave allocation (total days) for an employee/year.
    """
    total_days: int

    class Config:
        from_attributes = True


# Corporate Leave Schemas
class CorporateLeaveCreate(BaseModel):
    """
    Schema for creating a new corporate leave.
    
    Attributes:
        name: Name/occasion of the corporate leave
        date: Date of the corporate leave
        leave_type: Type of leave (National Holiday, Festival, etc.)
        is_recurring: Whether this is a recurring annual leave
    """
    name: str
    date: date
    leave_type: str = "National Holiday"
    is_recurring: bool = True

    class Config:
        from_attributes = True


class CorporateLeaveResponse(BaseModel):
    """
    Schema for corporate leave response.
    
    Attributes:
        id: Corporate leave ID
        name: Name/occasion of the corporate leave
        date: Date of the corporate leave
        leave_type: Type of leave
        is_recurring: Whether this is recurring annually
        created_at: Creation timestamp
    """
    id: int
    name: str
    date: date
    leave_type: str
    is_recurring: bool
    created_at: Optional[date] = None

    class Config:
        from_attributes = True


class CorporateLeaveUpdate(BaseModel):
    """
    Schema for updating a corporate leave.
    
    Attributes:
        name: Name/occasion of the corporate leave
        date: Date of the corporate leave
        leave_type: Type of leave
        is_recurring: Whether this is recurring annually
    """
    name: Optional[str] = None
    date: Optional[date] = None
    leave_type: Optional[str] = None
    is_recurring: Optional[bool] = None

    class Config:
        from_attributes = True


class CorporateLeaveCalendarResponse(BaseModel):
    """
    Schema for corporate leave calendar response.
    
    Attributes:
        date: Date of the corporate leave
        occasion: Name/occasion of the corporate leave
        type: Type of leave
        is_ai_generated: Whether this was AI generated or manually added
    """
    date: date
    occasion: str
    type: str
    is_ai_generated: bool = False

    class Config:
        from_attributes = True
