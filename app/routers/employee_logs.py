"""
Employee Logs API routes.

This module provides endpoints for viewing employee status logs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from typing import List

from ..database import get_db
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..models.leave import Leave
from ..schemas.employee_log import EmployeeLog, EmployeeLogResponse
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/employee-logs", tags=["Employee Logs"])


def get_employee_status(
    employee: Employee, 
    today: date, 
    db: Session
) -> tuple[str, str, bool, bool, str, datetime]:
    """
    Determine employee status based on leave and attendance data.
    
    Returns:
        tuple: (status, status_display, is_wfh, is_on_leave, leave_reason, last_activity)
    """
    current_time = datetime.now(timezone.utc)
    
    # Check if employee has active leave covering today
    active_leave = db.query(Leave).filter(
        Leave.employee_id == employee.id,
        Leave.start_date <= today,
        Leave.end_date >= today
    ).first()
    
    if active_leave:
        status_display = f"On Leave - {active_leave.reason or 'Annual Leave'}"
        return "on_leave", status_display, False, True, active_leave.reason, None
    
    # Check today's attendance
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance:
        return "not_in_yet", "Not In Yet", False, False, None, None
    
    # Employee has attendance record, determine status based on attendance data
    if attendance.status == "wfh":
        status_display = "Working From Home"
        last_activity = attendance.clock_in if attendance.clock_in else None
        return "wfh", status_display, True, False, None, last_activity
    elif attendance.clock_in and not attendance.clock_out:
        status_display = "In"
        last_activity = attendance.clock_in
        return "in", status_display, False, False, None, last_activity
    elif attendance.clock_in and attendance.clock_out:
        status_display = "Out"
        last_activity = attendance.clock_in
        return "out", status_display, False, False, None, last_activity
    else:
        return "not_in_yet", "Not In Yet", False, False, None, None


@router.get("/", response_model=EmployeeLogResponse)
def get_employee_logs(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get employee logs showing current status of all employees.
    
    Returns:
        EmployeeLogResponse: List of all employees with their current status
    """
    # Get today's date
    today = date.today()
    current_time = datetime.now(timezone.utc)
    
    # Get all active employees (you might want to filter by department/organization)
    employees = db.query(Employee).filter(
        Employee.status != "terminated"
    ).all()
    
    employee_logs = []
    
    for employee in employees:
        status, status_display, is_wfh, is_on_leave, leave_reason, last_activity = get_employee_status(
            employee, today, db
        )
        
        employee_log = EmployeeLog(
            id=employee.id,
            employee_id=employee.employee_id,
            name=employee.user.full_name if employee.user else "Unknown",
            email=employee.user.email if employee.user else "",
            department=employee.department,
            designation=employee.designation,
            avatar_url=employee.avatar_url,
            status=status,
            status_display=status_display,
            last_activity=last_activity,
            current_time=current_time,
            is_wfh=is_wfh,
            is_on_leave=is_on_leave,
            leave_reason=leave_reason
        )
        employee_logs.append(employee_log)
    
    return EmployeeLogResponse(
        logs=employee_logs,
        total_count=len(employee_logs),
        timestamp=current_time
    )


@router.get("/my-status", response_model=EmployeeLog)
def get_my_status(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get current user's own status.
    
    Returns:
        EmployeeLog: Current user's status information
    """
    today = date.today()
    current_time = datetime.now(timezone.utc)
    
    status, status_display, is_wfh, is_on_leave, leave_reason, last_activity = get_employee_status(
        current_employee, today, db
    )
    
    return EmployeeLog(
        id=current_employee.id,
        employee_id=current_employee.employee_id,
        name=current_employee.user.full_name if current_employee.user else "Unknown",
        email=current_employee.user.email if current_employee.user else "",
        department=current_employee.department,
        designation=current_employee.designation,
        avatar_url=current_employee.avatar_url,
        status=status,
        status_display=status_display,
        last_activity=last_activity,
        current_time=current_time,
        is_wfh=is_wfh,
        is_on_leave=is_on_leave,
        leave_reason=leave_reason
    )


@router.get("/by-department/{department}", response_model=EmployeeLogResponse)
def get_employee_logs_by_department(
    department: str,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get employee logs filtered by department.
    
    Args:
        department: Department name to filter by
        
    Returns:
        EmployeeLogResponse: List of employees in the specified department with their current status
    """
    today = date.today()
    current_time = datetime.now(timezone.utc)
    
    # Get employees in the specified department
    employees = db.query(Employee).filter(
        Employee.department == department,
        Employee.status != "terminated"
    ).all()
    
    employee_logs = []
    
    for employee in employees:
        status, status_display, is_wfh, is_on_leave, leave_reason, last_activity = get_employee_status(
            employee, today, db
        )
        
        employee_log = EmployeeLog(
            id=employee.id,
            employee_id=employee.employee_id,
            name=employee.user.full_name if employee.user else "Unknown",
            email=employee.user.email if current_employee.user else "",
            department=employee.department,
            designation=employee.designation,
            avatar_url=employee.avatar_url,
            status=status,
            status_display=status_display,
            last_activity=last_activity,
            current_time=current_time,
            is_wfh=is_wfh,
            is_on_leave=is_on_leave,
            leave_reason=leave_reason
        )
        employee_logs.append(employee_log)
    
    return EmployeeLogResponse(
        logs=employee_logs,
        total_count=len(employee_logs),
        timestamp=current_time
    )
