
"""
Request-related Pydantic schemas.

This module defines schemas for various employee requests
(WFH, help, regularization).
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
