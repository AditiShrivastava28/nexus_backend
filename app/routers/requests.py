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
from ..models.user import User, UserRole


from typing import List



from ..schemas.request import (
    WFHRequest,
    HelpRequest,
    RequestResponse,
    WFHApplyResponse,
    WFHHistoryItem,
    HelpTicketResponse,
    EarlyLateRequest,
    EarlyLateResponse,
    HelpTicketHistoryItem,
    EarlyLateHistoryItem
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


@router.get("/help", response_model=List[HelpTicketHistoryItem])
def get_help_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get help ticket history for the current employee.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[HelpTicketHistoryItem]: List of help tickets
    """
    requests = db.query(Request).filter(
        Request.requester_id == current_employee.id,
        Request.request_type == "help"
    ).order_by(Request.date.desc()).all()

    history = []
    for req in requests:
        try:
            details = json.loads(req.details)
            recipient_ids = details.get("recipients", [])
            category = details.get("category", "Other")
        except (json.JSONDecodeError, TypeError):
            recipient_ids = []
            category = "Other"
            
        # Get recipient names
        recipient_names = []
        if recipient_ids:
            recipients = db.query(Employee).filter(Employee.id.in_(recipient_ids)).all()
            for recipient in recipients:
                if recipient.user:
                    recipient_names.append(recipient.user.full_name)
            
        history.append(HelpTicketHistoryItem(
            subject=req.title or "Help Ticket",
            message_body=req.description or "",
            category=category,
            recipients=recipient_names,
            date=req.date
        ))
        
    return history


@router.get("/early-late", response_model=List[EarlyLateHistoryItem])
def get_early_late_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get early going/late coming request history for the current employee.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[EarlyLateHistoryItem]: List of early/late requests
    """
    requests = db.query(Request).filter(
        Request.requester_id == current_employee.id,
        Request.request_type == "early_late"
    ).order_by(Request.date.desc()).all()

    history = []
    for req in requests:
        try:
            details = json.loads(req.details)
            request_type = details.get("type", "early_going")
            duration = details.get("duration", 0.0)
        except (json.JSONDecodeError, TypeError):
            request_type = "early_going"
            duration = 0.0
            
        history.append(EarlyLateHistoryItem(
            date=req.date,
            type=request_type,
            duration=duration,
            reason=req.description or ""
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





@router.post("/help", response_model=HelpTicketResponse, status_code=status.HTTP_201_CREATED)
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
        HelpTicketResponse: Created request
    """

    from datetime import date
    
    # Auto-generate date
    today = date.today()
    
    # Get all admins
    admins = db.query(Employee).join(User).filter(User.role == UserRole.ADMIN.value).all()
    admin_ids = [admin.id for admin in admins]
    
    # Merge provided recipients with admins (ensure uniqueness)
    final_recipient_ids = set(help_data.recipients) if help_data.recipients else set()
    final_recipient_ids.update(admin_ids)
    
    # Fetch recipient names
    recipient_names = []
    if final_recipient_ids:
        recipients = db.query(Employee).filter(Employee.id.in_(final_recipient_ids)).all()
        # Create a map for order preservation or just list them
        # We need to access the associated User to get full_name
        for recipient in recipients:
            if recipient.user:
                recipient_names.append(recipient.user.full_name)
    
    request = Request(
        requester_id=current_employee.id,
        request_type="help",
        title=help_data.subject,
        description=help_data.message_body,
        date=today,
        # help tickets don't necessarily have an end_date in this new format, 
        # but the model might require it or it can be nullable. 

        # Assuming end_date is nullable or we can set it to same day.
        end_date=today, 
        details=json.dumps({
            "recipients": list(final_recipient_ids),
            "category": help_data.category.value
        })
    )
    db.add(request)

    db.commit()
    db.refresh(request)
    
    return HelpTicketResponse(
        message="Ticket sent successfully",
        recipients=recipient_names,
        date=today,
        category=help_data.category
    )



@router.post("/early-late", response_model=EarlyLateResponse, status_code=status.HTTP_201_CREATED)
def request_early_late(
    request_data: EarlyLateRequest,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Request Early Going or Late Coming.
    Limit: 2 requests per month.
    
    Args:
        request_data: Request details
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        EarlyLateResponse: Status and remaining quota
    """
    from datetime import date
    import calendar
    
    # Calculate month range
    today = date.today()
    req_date = request_data.date
    
    # Validation: Cannot request for past months (optional, but good practice)
    # Ensure req_date is within current month or future? 
    # User requirement is just "2 days allowed in a month". 
    # We will check the count for the month of the requested date.
    
    start_of_month = date(req_date.year, req_date.month, 1)
    last_day = calendar.monthrange(req_date.year, req_date.month)[1]
    end_of_month = date(req_date.year, req_date.month, last_day)
    
    # Check count of existing requests for this month
    # We use request_type="early_late"
    existing_count = db.query(Request).filter(
        Request.requester_id == current_employee.id,
        Request.request_type == "early_late",
        Request.date >= start_of_month,
        Request.date <= end_of_month
    ).count()
    
    if existing_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monthly limit of 2 Early Going / Late Coming requests reached for this month."
        )
        
    # Create request

    request = Request(
        requester_id=current_employee.id,
        request_type="early_late",
        title=f"{request_data.type.replace('_', ' ').title()} Request",
        description=request_data.reason,
        date=request_data.date,
        end_date=request_data.date,
        details=json.dumps({
            "type": request_data.type,
            "duration": request_data.duration
        })
    )
    db.add(request)

    db.commit()
    db.refresh(request)
    
    return EarlyLateResponse(
        message=f"{request_data.type.replace('_', ' ').title()} request submitted successfully",
        remaining_quota=2 - (existing_count + 1)
    )


