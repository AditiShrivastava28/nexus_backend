
"""
Request-related Pydantic schemas.

This module defines schemas for various employee requests
(WFH, help, regularization).
"""


from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

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



class WFHRequest(BaseModel):
    """
    Schema for WFH request.
    
    Attributes:
        start_date: Start date for WFH
        end_date: End date for WFH
        reason: Reason for WFH
    """
    start_date: date
    end_date: date
    reason: Optional[str] = None



class WFHApplyResponse(BaseModel):
    """
    Response schema for WFH application.
    """
    msg: str
    start_date: date
    end_date: date
    number_of_days_applied_for: int



class WFHHistoryItem(BaseModel):
    """
    Schema for WFH history item.
    """
    start_date: date
    end_date: date
    number_of_days: int
    reason: Optional[str] = None


class HelpCategory(str, Enum):
    IT_SUPPORT = "IT Support"
    HR_QUERY = "HR Query"
    PAYROLL = "Payroll"
    ADMIN_FACILITIES = "Admin/Facilities"
    OTHER = "Other"


class HelpRequest(BaseModel):
    """
    Schema for help ticket.
    
    Attributes:
        subject: Ticket subject
        message_body: Ticket message body
        category: Ticket category
        recipients: List of recipient employee IDs
    """
    subject: str
    message_body: str
    category: HelpCategory
    recipients: List[int]


class HelpTicketResponse(BaseModel):
    """
    Response schema for help ticket.
    
    Attributes:
        message: Success message
        recipients: List of recipient names
        date: Date of the ticket
        category: Ticket category
    """
    message: str
    recipients: List[str]
    date: date
    category: HelpCategory



class EarlyLateType(str, Enum):
    EARLY_GOING = "early_going"
    LATE_COMING = "late_coming"


class EarlyLateRequest(BaseModel):
    """
    Schema for Early Going / Late Coming request.
    

    Attributes:
        date: Date of the request
        type: Type (early_going or late_coming)
        reason: Reason
        duration: Duration in hours (e.g., 1.5)
    """
    date: date
    type: EarlyLateType
    reason: str
    duration: float



class EarlyLateResponse(BaseModel):

    """
    Response schema for Early/Late request.
    """
    message: str
    remaining_quota: int


class HelpTicketHistoryItem(BaseModel):
    """
    Schema for help ticket history item.
    """
    subject: str
    message_body: str
    category: HelpCategory
    recipients: List[str]
    date: date


class EarlyLateHistoryItem(BaseModel):
    """
    Schema for early/late request history item.
    """
    date: date
    type: EarlyLateType
    duration: float
    reason: str


class LeaveRequest(BaseRequest):

    """
    Schema for applying leaves. Inherits from BaseRequest and adds reason.
    """
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
        created_at: Creation timestamp
    """
    id: int
    request_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
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
