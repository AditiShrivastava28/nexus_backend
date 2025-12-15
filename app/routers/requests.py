"""

Employee requests API routes.

This module provides endpoints for WFH, help, and regularization requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
import json

from ..database import get_db
from ..models.employee import Employee
from ..models.request import Request


from typing import List
from ..schemas.request import (
    WFHRequest,
    HelpRequest,
    RequestResponse,
    WFHApplyResponse,
    WFHHistoryItem
)
from ..schemas.leave import LeaveRequest, LeaveApplyResponse
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/requests", tags=["Requests"])


@router.get("/wfh", response_model=List[WFHHistoryItem])
def get_wfh_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get WFH request history for the current employee.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[WFHHistoryItem]: List of WFH requests
    """
    requests = db.query(Request).filter(
        Request.requester_id == current_employee.id,
        Request.request_type == "wfh"
    ).order_by(Request.date.desc()).all()

    history = []
    for req in requests:
        try:
            details = json.loads(req.details)
            total_days = details.get("total", 0)
        except (json.JSONDecodeError, TypeError):
            total_days = 0
            
        history.append(WFHHistoryItem(
            start_date=req.date,
            end_date=req.end_date,
            number_of_days=total_days,
            reason=req.description
        ))
        
    return history


@router.post("/wfh", response_model=WFHApplyResponse, status_code=status.HTTP_201_CREATED)
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
        WFHApplyResponse: Created request
    """
    # Validate dates and compute inclusive days
    if wfh_data.start_date > wfh_data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be on or before end_date")
    
    # Inclusive day count
    delta = (wfh_data.end_date - wfh_data.start_date).days + 1
    total_days = int(max(1, delta))

    # create request record with from/to/total enforced by schema
    details = {"reason": wfh_data.reason, "total": total_days}
    request = Request(
        requester_id=current_employee.id,
        request_type="wfh",
        title="Work From Home Request",
        description=wfh_data.reason,
        date=wfh_data.start_date,
        end_date=wfh_data.end_date,
        details=json.dumps(details)
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    return WFHApplyResponse(
        msg="Request sent",
        start_date=wfh_data.start_date,
        end_date=wfh_data.end_date,
        number_of_days_applied_for=total_days
    )



@router.post("/leave", response_model=LeaveApplyResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    leave_data: LeaveRequest,
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
    from ..models.leave import Leave, LeaveBalance
    from datetime import date as date_type
    
    # Validate dates and compute days
    if leave_data.start_date > leave_data.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be on or before end_date")

    # Half-day validation
    if leave_data.half_day:
        # For half-day leaves, start_date and end_date must be the same
        if leave_data.start_date != leave_data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Half-day leaves must have the same start_date and end_date"
            )
        # half_day_type is required for half-day requests
        if not leave_data.half_day_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="half_day_type is required for half-day leaves (must be 'first_half' or 'second_half')"
            )
        if leave_data.half_day_type not in ["first_half", "second_half"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="half_day_type must be either 'first_half' or 'second_half'"
            )
        days_to_deduct = 0.5
    else:
        # Full day leave - inclusive day count
        delta = (leave_data.end_date - leave_data.start_date).days + 1
        days_to_deduct = float(max(1, delta))

    # Immediately check/update the employee's yearly balance (12 days per year)
    current_year = date_type.today().year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_employee.id,
        LeaveBalance.year == current_year
    ).first()

    if not balance:
        balance = LeaveBalance(
            employee_id=current_employee.id,
            year=current_year,
            total_days=12,
            used_days=0,
            remaining_days=12,
            leave_type="paid"  # Default to paid leave balance
        )
        db.add(balance)
        db.commit()
        db.refresh(balance)

    # Prevent duplicate/overlapping leave applications (any type)
    overlapping = db.query(Leave).filter(
        Leave.employee_id == current_employee.id,
        Leave.start_date <= leave_data.end_date,
        Leave.end_date >= leave_data.start_date
    ).first()
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave already exists for the given date(s)"
        )

    # The leave_type field is required in the request schema
    requested_type = leave_data.leave_type
    if requested_type == "paid":
        if balance.remaining_days < days_to_deduct:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"Insufficient paid leave balance. You have {balance.remaining_days} "
                        f"paid leave(s) remaining this year. Consider unpaid leave for the rest."),
            )

    # Create leave record with calculated days and leave_type
    leave = Leave(
        employee_id=current_employee.id,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        days=days_to_deduct,
        reason=leave_data.reason,
        leave_type=requested_type,
        half_day="true" if leave_data.half_day else "false",
        half_day_type=leave_data.half_day_type if leave_data.half_day else None,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    # If paid, deduct the calculated number of days from the balance
    if requested_type == "paid":
        balance.used_days += days_to_deduct
        balance.remaining_days = max(balance.total_days - balance.used_days, 0)
        db.commit()

    # Create a request/audit record for traceability
    request = Request(
        requester_id=current_employee.id,
        request_type="leave",
        title="Leave Request",
        description=leave_data.reason,
        date=leave_data.start_date,
        end_date=leave_data.end_date,
        details=json.dumps({"leave_id": leave.id})
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Return a compact summary (matches the front-end expectations)
    # total_leaves is fixed at 12 for the year (business rule)
    return LeaveApplyResponse(
        start_date=leave.start_date,
        end_date=leave.end_date,
        leave_taken=leave.days,
        reason=leave.reason,
        leave_type=leave.leave_type,
        total_leaves=12,
        remaining_leaves=balance.remaining_days,
        half_day=leave_data.half_day,
        half_day_type=leave_data.half_day_type,
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
        date=help_data.from_date,
        end_date=help_data.end_date,
        details=json.dumps({"total": help_data.total})
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
        created_at=request.created_at,
        total_days=help_data.total,
        message="Request sent"
    )
