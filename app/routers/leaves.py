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
from ..schemas.leave import LeaveCalendarItem, LeaveBalanceResponse
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
    
    # Get approved leaves
    leaves = db.query(Leave).filter(
        Leave.status == "approved",
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
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            status=leave.status
        ))
    
    return result


@router.get("/balance", response_model=List[LeaveBalanceResponse])
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
    
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_employee.id,
        LeaveBalance.year == current_year
    ).all()

    # If no balances exist for the user this year, create sensible defaults
    if not balances:
        defaults = {
            "casual": 12,
            "sick": 10,
            "annual": 15,
            "personal": 5
        }
        for lt, total in defaults.items():
            bal = LeaveBalance(
                employee_id=current_employee.id,
                leave_type=lt,
                year=current_year,
                total_days=total,
                used_days=0,
                remaining_days=total
            )
            db.add(bal)
        db.commit()
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == current_employee.id,
            LeaveBalance.year == current_year
        ).all()

    return [LeaveBalanceResponse(
        leave_type=bal.leave_type,
        total_days=bal.total_days,
        used_days=bal.used_days,
        remaining_days=bal.remaining_days
    ) for bal in balances]
