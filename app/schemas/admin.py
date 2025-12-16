"""
Admin-specific Pydantic schemas.

This module defines schemas for admin operations including employee log history,
attendance tracking, and comprehensive employee monitoring.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class AttendanceStatus(str, Enum):
    """Attendance status options."""
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    WFH = "wfh"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


class AttendanceHistoryItem(BaseModel):
    """
    Single attendance history item.
    
    Attributes:
        date: Attendance date
        clock_in: Clock-in timestamp
        clock_out: Clock-out timestamp
        status: Attendance status
        total_hours: Total working hours
        notes: Additional notes
        created_at: Record creation timestamp
    """
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: str
    total_hours: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceHistoryResponse(BaseModel):
    """
    Response schema for employee attendance history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_records: Total number of records
        attendance_data: List of attendance records
        summary: Attendance summary statistics
    """
    employee_id: int
    employee_name: str
    total_records: int
    attendance_data: List[AttendanceHistoryItem]
    summary: dict

    class Config:
        from_attributes = True


class WFHHistoryItem(BaseModel):
    """
    Single WFH history item.
    
    Attributes:
        id: Request ID
        start_date: WFH start date
        end_date: WFH end date
        days: Number of WFH days
        reason: Reason for WFH
        status: Request status
        created_at: Creation timestamp
    """
    id: int
    start_date: date
    end_date: date
    days: int
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WFHHistoryResponse(BaseModel):
    """
    Response schema for employee WFH history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_requests: Total number of WFH requests
        wfh_data: List of WFH records
        summary: WFH summary statistics
    """
    employee_id: int
    employee_name: str
    total_requests: int
    wfh_data: List[WFHHistoryItem]
    summary: dict

    class Config:
        from_attributes = True


class LeaveHistoryItem(BaseModel):
    """
    Single leave history item.
    
    Attributes:
        id: Leave ID
        start_date: Leave start date
        end_date: Leave end date
        days: Number of leave days
        leave_type: Type of leave (paid/unpaid)
        reason: Reason for leave
        half_day: Whether this is a half-day leave
        half_day_type: Type of half-day leave
        created_at: Creation timestamp
    """
    id: int
    start_date: date
    end_date: date
    days: float
    leave_type: str
    reason: Optional[str] = None
    half_day: bool = False
    half_day_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveHistoryResponse(BaseModel):
    """
    Response schema for employee leave history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_leaves: Total number of leave records
        leave_data: List of leave records
        summary: Leave summary statistics
        current_balance: Current leave balance
    """
    employee_id: int
    employee_name: str
    total_leaves: int
    leave_data: List[LeaveHistoryItem]
    summary: dict
    current_balance: dict

    class Config:
        from_attributes = True


class EarlyLateType(str, Enum):
    """Early/Late request types."""
    EARLY_GOING = "early_going"
    LATE_COMING = "late_coming"


class EarlyLateHistoryItem(BaseModel):
    """
    Single early/late history item.
    
    Attributes:
        id: Request ID
        date: Request date
        type: Type (early_going or late_coming)
        duration: Duration in hours
        reason: Reason
        status: Request status
        created_at: Creation timestamp
    """
    id: int
    date: date
    type: EarlyLateType
    duration: float
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class EarlyLateHistoryResponse(BaseModel):
    """
    Response schema for employee early/late history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_requests: Total number of requests
        early_late_data: List of early/late records
        summary: Early/late summary statistics
    """
    employee_id: int
    employee_name: str
    total_requests: int
    early_late_data: List[EarlyLateHistoryItem]
    summary: dict

    class Config:
        from_attributes = True


class HelpCategory(str, Enum):
    """Help ticket categories."""
    IT_SUPPORT = "IT Support"
    HR_QUERY = "HR Query"
    PAYROLL = "Payroll"
    ADMIN_FACILITIES = "Admin/Facilities"
    OTHER = "Other"


class HelpTicketHistoryItem(BaseModel):
    """
    Single help ticket history item.
    
    Attributes:
        id: Ticket ID
        subject: Ticket subject
        message_body: Message content
        category: Ticket category
        recipients: List of recipient names
        date: Ticket date
        status: Ticket status
        created_at: Creation timestamp
    """
    id: int
    subject: str
    message_body: str
    category: HelpCategory
    recipients: List[str]
    date: date
    created_at: datetime

    class Config:
        from_attributes = True


class HelpTicketsHistoryResponse(BaseModel):
    """
    Response schema for employee help tickets history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_tickets: Total number of help tickets
        tickets_data: List of help ticket records
        summary: Help tickets summary statistics
    """
    employee_id: int
    employee_name: str
    total_tickets: int
    tickets_data: List[HelpTicketHistoryItem]
    summary: dict

    class Config:
        from_attributes = True


class LogHistoryType(str, Enum):
    """Types of log history."""
    ATTENDANCE = "attendance"
    WFH = "wfh"
    LEAVE = "leave"
    EARLY_LATE = "early_late"
    HELP_TICKET = "help_ticket"


class LogHistoryItem(BaseModel):
    """
    Single log history item across all types.
    
    Attributes:
        id: Record ID
        type: Type of log
        date: Date of the log
        title: Title or summary
        description: Detailed description
        status: Status information
        metadata: Additional metadata
        created_at: Creation timestamp
    """
    id: int
    type: LogHistoryType
    date: date
    title: str
    description: str
    status: str
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


class CompleteLogHistoryResponse(BaseModel):
    """
    Response schema for complete employee log history.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        total_records: Total number of log records
        log_data: List of all log records
        summary: Comprehensive summary statistics
        pagination: Pagination information
    """
    employee_id: int
    employee_name: str
    total_records: int
    log_data: List[LogHistoryItem]
    summary: dict
    pagination: dict

    class Config:
        from_attributes = True


class EmployeeLogFilters(BaseModel):
    """
    Schema for filtering employee log history.
    
    Attributes:
        start_date: Start date for filtering
        end_date: End date for filtering
        types: List of log types to include
        status: Status to filter by
        limit: Maximum number of records
        offset: Number of records to skip
    """
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    types: Optional[List[LogHistoryType]] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0

    class Config:
        from_attributes = True
