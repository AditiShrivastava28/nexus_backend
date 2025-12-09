"""
Attendance-related Pydantic schemas.

This module defines schemas for attendance tracking operations.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class BreakResponse(BaseModel):
    """
    Break period response schema.
    
    Attributes:
        id: Break ID
        start_time: Break start timestamp
        end_time: Break end timestamp
        duration_minutes: Duration in minutes
    """
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class AttendanceResponse(BaseModel):
    """
    Today's attendance response.
    
    Attributes:
        id: Attendance ID
        date: Attendance date
        clock_in: Clock-in timestamp
        clock_out: Clock-out timestamp
        status: Attendance status
        total_hours: Total working hours
        breaks: List of break periods
        is_on_break: Whether currently on break
    """
    id: int
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: Optional[str] = None
    total_hours: Optional[str] = None
    breaks: List[BreakResponse] = []
    is_on_break: bool = False

    class Config:
        from_attributes = True


class ClockInResponse(BaseModel):
    """
    Clock-in API response.
    
    Attributes:
        message: Success message
        clock_in: Clock-in timestamp
        attendance_id: Created attendance ID
    """
    message: str
    clock_in: datetime
    attendance_id: int


class ClockOutResponse(BaseModel):
    """
    Clock-out API response.
    
    Attributes:
        message: Success message
        clock_out: Clock-out timestamp
        total_hours: Total working hours
    """
    message: str
    clock_out: datetime
    total_hours: str


class BreakStartResponse(BaseModel):
    """
    Break start API response.
    
    Attributes:
        message: Success message
        break_start: Break start timestamp
    """
    message: str
    break_start: datetime


class BreakEndResponse(BaseModel):
    """
    Break end API response.
    
    Attributes:
        message: Success message
        break_end: Break end timestamp
        duration_minutes: Break duration in minutes
    """
    message: str
    break_end: datetime
    duration_minutes: int
