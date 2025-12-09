"""
Employee requests API routes.

This module provides endpoints for WFH, expense, help, and regularization requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
import json

from ..database import get_db
from ..models.employee import Employee
from ..models.request import Request
from ..schemas.request import (
    WFHRequest,
    RegularizationRequest,
    ExpenseRequest,
    HelpRequest,
    RequestResponse
)
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("/wfh", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def request_wfh(
    wfh_data: WFHRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Submit a Work From Home request.
    
    Args:
        wfh_data: WFH request details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        RequestResponse: Created request
    """
    request = Request(
        requester_id=current_employee.id,
        request_type="wfh",
        title="Work From Home Request",
        description=wfh_data.reason,
        date=wfh_data.date,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return RequestResponse(
        id=request.id,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        date=request.date,
        status=request.status,
        created_at=request.created_at
    )


@router.post("/leave", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    leave_data: dict,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Apply for leave.
    
    Args:
        leave_data: Leave request details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        RequestResponse: Created request
    """
    from ..models.leave import Leave
    
    # Create leave record
    leave = Leave(
        employee_id=current_employee.id,
        leave_type=leave_data.get("leave_type", "casual"),
        start_date=leave_data.get("start_date"),
        end_date=leave_data.get("end_date"),
        days=leave_data.get("days", 1),
        reason=leave_data.get("reason"),
        status="pending"
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    # Also create a request for the inbox
    request = Request(
        requester_id=current_employee.id,
        request_type="leave",
        title=f"Leave Request: {leave_data.get('leave_type', 'casual').title()}",
        description=leave_data.get("reason"),
        date=leave_data.get("start_date"),
        end_date=leave_data.get("end_date"),
        status="pending",
        details=json.dumps({"leave_id": leave.id})
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return RequestResponse(
        id=request.id,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        date=request.date,
        status=request.status,
        created_at=request.created_at
    )


@router.post("/regularization", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def request_regularization(
    reg_data: RegularizationRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Submit an attendance regularization request.
    
    Args:
        reg_data: Regularization request details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        RequestResponse: Created request
    """
    details = {
        "clock_in": reg_data.clock_in,
        "clock_out": reg_data.clock_out
    }
    
    request = Request(
        requester_id=current_employee.id,
        request_type="regularization",
        title="Attendance Regularization",
        description=reg_data.reason,
        date=reg_data.date,
        status="pending",
        details=json.dumps(details)
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return RequestResponse(
        id=request.id,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        date=request.date,
        status=request.status,
        created_at=request.created_at
    )


@router.post("/expense", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def submit_expense(
    expense_data: ExpenseRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Submit an expense claim.
    
    Args:
        expense_data: Expense claim details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        RequestResponse: Created request
    """
    request = Request(
        requester_id=current_employee.id,
        request_type="expense",
        title=expense_data.title,
        description=expense_data.description,
        date=expense_data.date or date.today(),
        amount=expense_data.amount,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return RequestResponse(
        id=request.id,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        date=request.date,
        status=request.status,
        amount=request.amount,
        created_at=request.created_at
    )


@router.post("/help", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def raise_help_ticket(
    help_data: HelpRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Raise a help ticket.
    
    Args:
        help_data: Help ticket details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        RequestResponse: Created request
    """
    request = Request(
        requester_id=current_employee.id,
        request_type="help",
        title=help_data.title,
        description=help_data.description,
        date=date.today(),
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return RequestResponse(
        id=request.id,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        date=request.date,
        status=request.status,
        created_at=request.created_at
    )
