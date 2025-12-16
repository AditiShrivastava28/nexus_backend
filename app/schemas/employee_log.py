"""
Employee log-related Pydantic schemas.

This module defines schemas for employee log/status operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class EmployeeLog(BaseModel):
    """
    Employee log response showing current status.
    
    Attributes:
        id: Employee ID
        employee_id: Company employee ID
        name: Full name
        email: Work email
        department: Department
        designation: Job title
        avatar_url: Profile picture URL
        status: Current status (on_leave, wfh, in, out, not_in_yet)
        status_display: Human-readable status display
        last_activity: Last clock-in time if available
        current_time: Current time when status was determined
        is_wfh: Whether employee is working from home
        is_on_leave: Whether employee is on leave
        leave_reason: Leave reason if on leave
    """
    id: int
    employee_id: str
    name: str
    email: str
    department: Optional[str] = None
    designation: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    status_display: str
    last_activity: Optional[datetime] = None
    current_time: datetime
    is_wfh: bool = False
    is_on_leave: bool = False
    leave_reason: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeLogResponse(BaseModel):
    """
    Response model for employee logs API.
    
    Attributes:
        logs: List of employee logs
        total_count: Total number of employees
        timestamp: When the status was determined
    """
    logs: list[EmployeeLog]
    total_count: int
    timestamp: datetime

    class Config:
        from_attributes = True
