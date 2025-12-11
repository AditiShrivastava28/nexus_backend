"""
Request-related Pydantic schemas.

This module defines schemas for various employee requests
(WFH, expense, help, regularization).
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class BaseRequest(BaseModel):
    """
    Base request fields required for all request types.

    Attributes:
        from_date: Start date for the request
        end_date: End date for the request
        total: Total days (integer)
    """
    from_date: date
    end_date: date
    total: int


class WFHRequest(BaseRequest):
    """
    Schema for WFH request.
    
    Attributes:
        reason: Reason for WFH
    """
    reason: Optional[str] = None


class RegularizationRequest(BaseRequest):
    """
    Schema for attendance regularization request.
    
    Attributes:
        clock_in: Corrected clock-in time
        clock_out: Corrected clock-out time
        reason: Reason for regularization
    """
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    reason: Optional[str] = None


class ExpenseRequest(BaseRequest):
    """
    Schema for expense claim request.
    
    Attributes:
        title: Expense title
        amount: Expense amount
        description: Expense description
        description: Expense description
    """
    title: str
    amount: float
    description: Optional[str] = None



class HelpRequest(BaseRequest):
    """
    Schema for help ticket.
    
    Attributes:
        title: Ticket title
        description: Issue description
    """
    title: str
    description: str


class LeaveRequest(BaseRequest):
    """
    Schema for applying leaves. Inherits from BaseRequest and adds leave_type and reason.
    """
    leave_type: Optional[str] = "casual"
    reason: Optional[str] = None


class RequestResponse(BaseModel):
    """
    Request response schema.
    
    Attributes:
        id: Request ID
        request_type: Type of request
        title: Request title
        description: Description
        date: Request date
        status: Request status
        amount: Amount (for expenses)
        created_at: Creation timestamp
    """
    id: int
    request_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    status: str
    amount: Optional[float] = None
    created_at: Optional[datetime] = None
    # Total days applied (if applicable)
    total_days: Optional[int] = None
    # Informational message (e.g., "Request sent")
    message: Optional[str] = None

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """
    Task/inbox item response for approvals.
    
    Attributes:
        id: Task ID
        type: Task type
        title: Task title
        requester: Requester name
        date: Request date
        avatar: Requester avatar
        details: Additional details
    """
    id: int
    type: str
    title: str
    requester: str
    date: Optional[date] = None
    avatar: Optional[str] = None
    details: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    """
    Schema for approval/rejection action.
    
    Attributes:
        comments: Optional comments
    """
    comments: Optional[str] = None


class ResumeData(BaseModel):
    """
    Schema for resume builder data.
    
    Attributes:
        personal: Personal information
        experience: Work experience
        education: Education history
        skills: Skills list
        projects: Projects
    """
    personal: Optional[dict] = None
    experience: Optional[list] = None
    education: Optional[list] = None
    skills: Optional[list] = None
    projects: Optional[list] = None
