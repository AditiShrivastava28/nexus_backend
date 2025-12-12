"""
Leave management API routes.

This module provides endpoints for leave calendar and balance.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from ..models.employee import Employee
from ..models.leave import Leave, LeaveBalance
from ..models.user import User
from ..schemas.leave import LeaveCalendarItem, LeaveBalanceResponse, LeaveResponse
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get("/calendar", response_model=List[LeaveCalendarItem])
def get_leaves_calendar(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get leaves calendar showing team/org leaves.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[LeaveCalendarItem]: List of leaves for calendar
    """
    # Get leaves for the current month
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Get leaves starting/ending in or after the start of the month
    leaves = db.query(Leave).filter(
        Leave.end_date >= start_of_month
    ).all()
    
    result = []
    for leave in leaves:
        # Get employee name
        emp = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if emp:
            user = db.query(User).filter(User.id == emp.user_id).first()
            employee_name = user.full_name if user else "Unknown"
        else:
            employee_name = "Unknown"
        
        result.append(LeaveCalendarItem(
            id=leave.id,
            employee_name=employee_name,
            start_date=leave.start_date,
            end_date=leave.end_date
        ))
    
    return result


@router.get("/balance", response_model=LeaveBalanceResponse)
def get_leave_balance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get current user's leave balances.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[LeaveBalanceResponse]: Leave balances by type
    """
    current_year = date.today().year
    
    # There is a single leave balance per employee per year
    bal = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_employee.id,
        LeaveBalance.year == current_year
    ).first()

    # compute used days from actual Leave records overlapping the year
    start_of_year = date(current_year, 1, 1)
    end_of_year = date(current_year, 12, 31)
    # Only paid leaves count against the paid balance
    leaves = db.query(Leave).filter(
        Leave.employee_id == current_employee.id,
        Leave.end_date >= start_of_year,
        Leave.start_date <= end_of_year,
        Leave.leave_type == "paid"
    ).all()

    used_sum = 0.0
    for l in leaves:
        try:
            used_sum += float(l.days or 0)
        except Exception:
            continue

    # If no balance exists for the user this year, create a default of 12 days
    if not bal:
        bal = LeaveBalance(
            employee_id=current_employee.id,
            year=current_year,
            total_days=12,
            used_days=used_sum,
            remaining_days=max(12 - used_sum, 0)
        )
        db.add(bal)
    else:
        # update balance from computed used_sum
        bal.used_days = used_sum
        bal.remaining_days = max(bal.total_days - used_sum, 0)

    db.commit()
    db.refresh(bal)

    return LeaveBalanceResponse(
        total_days=float(bal.total_days),
        used_days=float(bal.used_days),
        remaining_days=float(bal.remaining_days)
    )


@router.get("/history", response_model=List[LeaveResponse])
def get_leave_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated employee's leave history (all leave records).

    Returns:
        List[LeaveResponse]: list of leave records with dates, type and reason
    """
    leaves = db.query(Leave).filter(Leave.employee_id == current_employee.id).order_by(Leave.start_date.desc()).all()
    return leaves
