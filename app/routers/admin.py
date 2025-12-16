"""
Admin API routes.

This module provides admin endpoints for employee management, system configuration,
and administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date


from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..models.leave import Leave, LeaveBalance
from ..models.request import Request
from ..models.message import Message


from ..schemas.employee import (
    EmployeeCreate, 
    EmployeeUpdate, 
    EmployeeListItem, 
    EmployeeProfile,
    EmployeeStatusUpdate,
    ManagerInfo
)
from ..schemas.admin import (
    AttendanceHistoryResponse,
    WFHHistoryResponse,
    LeaveHistoryResponse,
    EarlyLateHistoryResponse,
    HelpTicketsHistoryResponse,
    CompleteLogHistoryResponse,
    EmployeeLogFilters,
    LogHistoryType
)
from ..services.employee import EmployeeService
from ..utils.deps import get_current_user


router = APIRouter(prefix="/admin", tags=["Admin"])


def check_admin_access(current_user: User):
    """Check if current user has admin privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.get("/employees", response_model=List[EmployeeListItem])
def get_all_employees_admin(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all employees (admin only).
    
    Args:
        search: Optional search term
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[EmployeeListItem]: List of employees
    """
    check_admin_access(current_user)
    
    employees = EmployeeService.get_all_employees(db, search, skip, limit)
    

    result = []
    for emp in employees:
        # Get manager object
        manager_info = None
        if emp.manager_id:
            manager = db.query(Employee).filter(Employee.id == emp.manager_id).first()
            if manager and manager.user:
                manager_info = ManagerInfo(
                    id=manager.id,
                    employeeId=manager.employee_id,
                    name=manager.user.full_name,
                    email=manager.user.email,
                    designation=manager.designation,
                    department=manager.department
                )
        
        # Get salary for monthly pay
        salary = emp.salary.net_pay if emp.salary else None
        
        result.append(EmployeeListItem(
            id=emp.id,
            name=emp.user.full_name if emp.user else "Unknown",
            role=emp.designation,
            department=emp.department,
            salary=salary,
            email=emp.user.email if emp.user else "",
            status=emp.status,
            avatar=emp.avatar_url,
            joinDate=emp.join_date,
            location=emp.location,
            manager=manager_info.name if manager_info else None
        ))
    
    return result



@router.get("/employees/available-managers", response_model=List[EmployeeListItem])
def get_available_managers(
    exclude_employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employees who can be assigned as managers.
    
    Args:
        exclude_employee_id: Optional employee ID to exclude from managers list
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[EmployeeListItem]: List of potential managers
    """
    check_admin_access(current_user)
    
    # Get active employees who could be managers
    available_employees = EmployeeService.get_available_managers(db, exclude_employee_id)
    

    result = []
    for emp in available_employees:
        # Get manager object for this potential manager
        manager_info = None
        if emp.manager_id:
            manager = db.query(Employee).filter(Employee.id == emp.manager_id).first()
            if manager and manager.user:
                manager_info = ManagerInfo(
                    id=manager.id,
                    employeeId=manager.employee_id,
                    name=manager.user.full_name,
                    email=manager.user.email,
                    designation=manager.designation,
                    department=manager.department
                )
        
        result.append(EmployeeListItem(
            id=emp.id,
            name=emp.user.full_name if emp.user else "Unknown",
            role=emp.designation,
            department=emp.department,
            salary=emp.salary.net_pay if emp.salary else None,
            email=emp.user.email if emp.user else "",
            status=emp.status,
            avatar=emp.avatar_url,
            joinDate=emp.join_date,
            location=emp.location,
            manager=manager_info.name if manager_info else None
        ))
    
    return result


@router.get("/employees/{employee_id}", response_model=EmployeeProfile)
def get_employee_admin(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee details (admin only).
    
    Args:
        employee_id: Employee ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        EmployeeProfile: Employee details
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    

    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get manager object
    manager_info = None
    if employee.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if manager and manager.user:
            manager_info = ManagerInfo(
                id=manager.id,
                employeeId=manager.employee_id,
                name=manager.user.full_name,
                email=manager.user.email,
                designation=manager.designation,
                department=manager.department
            )
    
    return EmployeeProfile(
        id=employee.id,
        employeeId=employee.employee_id,
        name=employee.user.full_name if employee.user else "Unknown",
        email=employee.user.email if employee.user else "",
        department=employee.department,
        designation=employee.designation,
        joinDate=employee.join_date,
        location=employee.location,
        manager=manager_info,
        dob=employee.dob,
        gender=employee.gender,
        marital_status=employee.marital_status,
        blood_group=employee.blood_group,
        address=employee.address,
        personal_email=employee.personal_email,
        mobile=employee.mobile,
        avatar_url=employee.avatar_url,
        status=employee.status
    )


@router.post("/employees", response_model=EmployeeProfile, status_code=status.HTTP_201_CREATED)
def create_employee_admin(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new employee (admin only).
    
    Args:
        employee_data: Employee creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        EmployeeProfile: Created employee details
        
    Raises:
        HTTPException: 400 if validation fails
    """

    check_admin_access(current_user)
    
    # Handle manager_id conversion (convert 0 to None for default null behavior)
    manager_id = employee_data.manager_id
    if manager_id == 0:
        manager_id = None

    # Validate manager_id if provided (and not None)
    if manager_id:
        try:
            EmployeeService.validate_manager_assignment(
                db, None, manager_id  # employee_id is None for new employee
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    

    # Check for duplicate employee ID only if one is provided
    if employee_data.employee_id:
        existing_employee = db.query(Employee).filter(
            Employee.employee_id == employee_data.employee_id
        ).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )

    # Create employee (auto-generate employee_id if not provided)
    employee = EmployeeService.create_employee(
        db=db,
        email=employee_data.email,
        password=employee_data.password,
        full_name=employee_data.full_name,
        employee_id=employee_data.employee_id,  # None means auto-generate
        role=employee_data.role,
        department=employee_data.department,
        designation=employee_data.designation,
        join_date=employee_data.join_date,
        location=employee_data.location,
        manager_id=manager_id
    )
    

    # Return created employee details
    manager_info = None
    if employee.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if manager and manager.user:
            manager_info = ManagerInfo(
                id=manager.id,
                employeeId=manager.employee_id,
                name=manager.user.full_name,
                email=manager.user.email,
                designation=manager.designation,
                department=manager.department
            )
    
    return EmployeeProfile(
        id=employee.id,
        employeeId=employee.employee_id,
        name=employee.user.full_name if employee.user else "Unknown",
        email=employee.user.email if employee.user else "",
        department=employee.department,
        designation=employee.designation,
        joinDate=employee.join_date,
        location=employee.location,
        manager=manager_info,
        dob=employee.dob,
        gender=employee.gender,
        marital_status=employee.marital_status,
        blood_group=employee.blood_group,
        address=employee.address,
        personal_email=employee.personal_email,
        mobile=employee.mobile,
        avatar_url=employee.avatar_url,
        status=employee.status
    )


@router.put("/employees/{employee_id}", response_model=EmployeeProfile)
def update_employee_admin(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee details (admin only).
    
    Args:
        employee_id: Employee ID
        employee_data: Employee update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        EmployeeProfile: Updated employee details
        
    Raises:
        HTTPException: 404 if employee not found, 400 if validation fails
    """
    check_admin_access(current_user)
    
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    

    # Validate manager_id if provided
    if employee_data.manager_id is not None:
        if employee_data.manager_id == 0:
            # Clear manager assignment
            employee_data.manager_id = None
        elif employee_data.manager_id != employee.manager_id:
            # Validate manager assignment using the service method
            try:
                EmployeeService.validate_manager_assignment(
                    db, employee.id, employee_data.manager_id
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
    
    # Prepare update data
    update_data = {}
    if employee_data.full_name is not None:
        update_data['user.full_name'] = employee_data.full_name
    if employee_data.department is not None:
        update_data['department'] = employee_data.department
    if employee_data.designation is not None:
        update_data['designation'] = employee_data.designation
    if employee_data.location is not None:
        update_data['location'] = employee_data.location
    if employee_data.manager_id is not None:
        update_data['manager_id'] = employee_data.manager_id
    if employee_data.status is not None:
        update_data['status'] = employee_data.status
    
    # Update employee profile
    if update_data:
        EmployeeService.update_employee_profile(db, employee, **update_data)
    

    # Update user name if needed
    if employee_data.full_name and employee.user:
        employee.user.full_name = employee_data.full_name
        db.commit()
        db.refresh(employee)
    
    # Get updated manager object
    manager_info = None
    if employee.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if manager and manager.user:
            manager_info = ManagerInfo(
                id=manager.id,
                employeeId=manager.employee_id,
                name=manager.user.full_name,
                email=manager.user.email,
                designation=manager.designation,
                department=manager.department
            )
    
    return EmployeeProfile(
        id=employee.id,
        employeeId=employee.employee_id,
        name=employee.user.full_name if employee.user else "Unknown",
        email=employee.user.email if employee.user else "",
        department=employee.department,
        designation=employee.designation,
        joinDate=employee.join_date,
        location=employee.location,
        manager=manager_info,
        dob=employee.dob,
        gender=employee.gender,
        marital_status=employee.marital_status,
        blood_group=employee.blood_group,
        address=employee.address,
        personal_email=employee.personal_email,
        mobile=employee.mobile,
        avatar_url=employee.avatar_url,
        status=employee.status
    )


@router.patch("/employees/{employee_id}/status", response_model=EmployeeProfile)
def update_employee_status(
    employee_id: int,
    status_data: EmployeeStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee status (admin only).
    
    Args:
        employee_id: Employee ID
        status_data: Status update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        EmployeeProfile: Updated employee details
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    

    # Validate status
    valid_statuses = ["full_time", "in-probation", "notice-period", "trainee", "active", "on_leave", "terminated"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    

    # Update status
    employee.status = status_data.status
    db.commit()
    db.refresh(employee)
    
    # Get manager object
    manager_info = None
    if employee.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if manager and manager.user:
            manager_info = ManagerInfo(
                id=manager.id,
                employeeId=manager.employee_id,
                name=manager.user.full_name,
                email=manager.user.email,
                designation=manager.designation,
                department=manager.department
            )
    
    return EmployeeProfile(
        id=employee.id,
        employeeId=employee.employee_id,
        name=employee.user.full_name if employee.user else "Unknown",
        email=employee.user.email if employee.user else "",
        department=employee.department,
        designation=employee.designation,
        joinDate=employee.join_date,
        location=employee.location,
        manager=manager_info,
        dob=employee.dob,
        gender=employee.gender,
        marital_status=employee.marital_status,
        blood_group=employee.blood_group,
        address=employee.address,
        personal_email=employee.personal_email,
        mobile=employee.mobile,
        avatar_url=employee.avatar_url,
        status=employee.status
    )


@router.delete("/employees/{employee_id}")
def delete_employee_admin(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete employee (admin only).
    
    Args:
        employee_id: Employee ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check if employee has team members
    team_members = EmployeeService.get_team_members(db, employee_id)
    if team_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete employee who has team members. Reassign team members first."
        )
    

    # Delete employee
    EmployeeService.delete_employee(db, employee)
    
    return {"message": "Employee deleted successfully"}


# Employee Log History Endpoints

@router.get("/employees/{employee_id}/attendance-history", response_model=AttendanceHistoryResponse)
def get_employee_attendance_history(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee attendance history (admin only).
    
    Args:
        employee_id: Employee ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AttendanceHistoryResponse: Employee attendance history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for attendance history
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    
    # Apply date filters
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    # Apply pagination
    total_records = query.count()
    attendance_records = query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    attendance_data = []
    for record in attendance_records:
        attendance_data.append({
            "date": record.date,
            "clock_in": record.clock_in,
            "clock_out": record.clock_out,
            "status": record.status,
            "total_hours": record.total_hours,
            "notes": record.notes,
            "created_at": record.created_at
        })
    
    # Calculate summary statistics
    total_attendance_records = db.query(Attendance).filter(Attendance.employee_id == employee_id).count()
    present_days = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.status == "present"
    ).count()
    wfh_days = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.status == "wfh"
    ).count()
    absent_days = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.status == "absent"
    ).count()
    
    summary = {
        "total_records": total_attendance_records,
        "present_days": present_days,
        "wfh_days": wfh_days,
        "absent_days": absent_days,
        "attendance_rate": round((present_days / total_attendance_records * 100) if total_attendance_records > 0 else 0, 2)
    }
    
    return AttendanceHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_records=total_records,
        attendance_data=attendance_data,
        summary=summary
    )


@router.get("/employees/{employee_id}/wfh-history", response_model=WFHHistoryResponse)
def get_employee_wfh_history(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee WFH history (admin only).
    
    Args:
        employee_id: Employee ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        WFHHistoryResponse: Employee WFH history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for WFH requests
    query = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "wfh"
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(Request.date >= start_date)
    if end_date:
        query = query.filter(Request.date <= end_date)
    
    # Apply pagination
    total_records = query.count()
    wfh_records = query.order_by(Request.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    wfh_data = []
    for record in wfh_records:
        # Calculate days between start and end date
        days = 1
        if record.date and record.end_date:
            days = (record.end_date - record.date).days + 1
        
        wfh_data.append({
            "id": record.id,
            "start_date": record.date,
            "end_date": record.end_date,
            "days": days,
            "reason": record.description,
            "created_at": record.created_at
        })
    
    # Calculate summary statistics
    total_wfh_requests = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "wfh"
    ).count()
    
    total_wfh_days = sum(record.days for record in db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "wfh"
    ).all())
    
    summary = {
        "total_requests": total_wfh_requests,
        "total_wfh_days": total_wfh_days,
        "average_days_per_request": round(total_wfh_days / total_wfh_requests, 2) if total_wfh_requests > 0 else 0
    }
    
    return WFHHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_requests=total_records,
        wfh_data=wfh_data,
        summary=summary
    )


@router.get("/employees/{employee_id}/leave-history", response_model=LeaveHistoryResponse)
def get_employee_leave_history(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee leave history (admin only).
    
    Args:
        employee_id: Employee ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        LeaveHistoryResponse: Employee leave history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for leave history
    query = db.query(Leave).filter(Leave.employee_id == employee_id)
    
    # Apply date filters
    if start_date:
        query = query.filter(Leave.start_date >= start_date)
    if end_date:
        query = query.filter(Leave.end_date <= end_date)
    
    # Apply pagination
    total_records = query.count()
    leave_records = query.order_by(Leave.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    leave_data = []
    for record in leave_records:
        leave_data.append({
            "id": record.id,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "days": record.days,
            "leave_type": record.leave_type,
            "reason": record.reason,
            "half_day": record.half_day == "true" if record.half_day else False,
            "half_day_type": record.half_day_type,
            "created_at": record.created_at
        })
    
    # Calculate summary statistics
    total_leaves = db.query(Leave).filter(Leave.employee_id == employee_id).count()
    paid_leaves = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.leave_type == "paid"
    ).count()
    unpaid_leaves = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.leave_type == "unpaid"
    ).count()
    
    total_leave_days = sum(record.days for record in db.query(Leave).filter(
        Leave.employee_id == employee_id
    ).all())
    
    summary = {
        "total_leave_requests": total_leaves,
        "paid_leaves": paid_leaves,
        "unpaid_leaves": unpaid_leaves,
        "total_leave_days": total_leave_days,
        "average_days_per_request": round(total_leave_days / total_leaves, 2) if total_leaves > 0 else 0
    }
    
    # Get current leave balance
    current_year = date.today().year
    leave_balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == current_year
    ).first()
    
    current_balance = {
        "total_days": leave_balance.total_days if leave_balance else 12,
        "used_days": leave_balance.used_days if leave_balance else 0,
        "remaining_days": leave_balance.remaining_days if leave_balance else 12,
        "year": current_year
    }
    
    return LeaveHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_leaves=total_records,
        leave_data=leave_data,
        summary=summary,
        current_balance=current_balance
    )


@router.get("/employees/{employee_id}/early-late-history", response_model=EarlyLateHistoryResponse)
def get_employee_early_late_history(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee early/late history (admin only).
    
    Args:
        employee_id: Employee ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        EarlyLateHistoryResponse: Employee early/late history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for early/late requests
    query = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type.in_(["early_going", "late_coming"])
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(Request.date >= start_date)
    if end_date:
        query = query.filter(Request.date <= end_date)
    
    # Apply pagination
    total_records = query.count()
    early_late_records = query.order_by(Request.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    early_late_data = []
    for record in early_late_records:
        # Extract details from description or use default
        details = {}
        if record.description:
            try:
                details = eval(record.description) if record.description.startswith('{') else {}
            except:
                details = {}
        
        duration = details.get('duration', 1.0) if isinstance(details, dict) else 1.0
        
        early_late_data.append({
            "id": record.id,
            "date": record.date,
            "type": record.request_type,
            "duration": duration,
            "reason": record.description,
            "created_at": record.created_at
        })
    
    # Calculate summary statistics
    total_requests = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type.in_(["early_going", "late_coming"])
    ).count()
    
    early_going_requests = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "early_going"
    ).count()
    
    late_coming_requests = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "late_coming"
    ).count()
    
    summary = {
        "total_requests": total_requests,
        "early_going_requests": early_going_requests,
        "late_coming_requests": late_coming_requests,
        "most_common_type": "early_going" if early_going_requests > late_coming_requests else "late_coming"
    }
    
    return EarlyLateHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_requests=total_records,
        early_late_data=early_late_data,
        summary=summary
    )


@router.get("/employees/{employee_id}/help-tickets-history", response_model=HelpTicketsHistoryResponse)
def get_employee_help_tickets_history(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee help tickets history (admin only).
    
    Args:
        employee_id: Employee ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HelpTicketsHistoryResponse: Employee help tickets history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for help ticket requests
    query = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "help"
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(Request.date >= start_date)
    if end_date:
        query = query.filter(Request.date <= end_date)
    
    # Apply pagination
    total_records = query.count()
    help_records = query.order_by(Request.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    tickets_data = []
    for record in help_records:
        # Extract details from description
        details = {}
        if record.description:
            try:
                details = eval(record.description) if record.description.startswith('{') else {}
            except:
                details = {}
        
        category = details.get('category', 'Other') if isinstance(details, dict) else 'Other'
        recipients = details.get('recipients', []) if isinstance(details, dict) else []
        
        # Get recipient names
        recipient_names = []
        if recipients:
            recipient_employees = db.query(Employee).filter(Employee.id.in_(recipients)).all()
            recipient_names = [emp.user.full_name for emp in recipient_employees if emp.user]
        
        tickets_data.append({
            "id": record.id,
            "subject": record.title or "Help Request",
            "message_body": record.description or "",
            "category": category,
            "recipients": recipient_names,
            "date": record.date,
            "created_at": record.created_at
        })
    
    # Calculate summary statistics
    total_tickets = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "help"
    ).count()
    
    # Count by category
    all_help_requests = db.query(Request).filter(
        Request.requester_id == employee_id,
        Request.request_type == "help"
    ).all()
    
    category_counts = {}
    for request in all_help_requests:
        details = {}
        if request.description:
            try:
                details = eval(request.description) if request.description.startswith('{') else {}
            except:
                details = {}
        
        category = details.get('category', 'Other') if isinstance(details, dict) else 'Other'
        category_counts[category] = category_counts.get(category, 0) + 1
    
    summary = {
        "total_tickets": total_tickets,
        "category_breakdown": category_counts,
        "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "None"
    }
    
    return HelpTicketsHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_tickets=total_records,
        tickets_data=tickets_data,
        summary=summary
    )


@router.get("/employees/{employee_id}/complete-log-history", response_model=CompleteLogHistoryResponse)
def get_employee_complete_log_history(
    employee_id: int,
    filters: Optional[EmployeeLogFilters] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete employee log history (admin only).
    
    Args:
        employee_id: Employee ID
        filters: Optional filters for log history
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CompleteLogHistoryResponse: Complete employee log history
        
    Raises:
        HTTPException: 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Use provided filters or create default
    if filters is None:
        filters = EmployeeLogFilters()
    
    log_data = []
    total_records = 0
    
    # Get attendance records
    if filters.types is None or LogHistoryType.ATTENDANCE in filters.types:
        attendance_query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
        
        if filters.start_date:
            attendance_query = attendance_query.filter(Attendance.date >= filters.start_date)
        if filters.end_date:
            attendance_query = attendance_query.filter(Attendance.date <= filters.end_date)
        
        attendance_records = attendance_query.order_by(Attendance.date.desc()).offset(filters.offset).limit(filters.limit // 4 if filters.types is None else filters.limit).all()
        
        for record in attendance_records:
            log_data.append({
                "id": record.id,
                "type": "attendance",
                "date": record.date,
                "title": f"Attendance - {record.status.title()}",
                "description": f"Clock in: {record.clock_in}, Clock out: {record.clock_out}, Hours: {record.total_hours}",
                "status": record.status,
                "metadata": {"clock_in": record.clock_in, "clock_out": record.clock_out, "total_hours": record.total_hours},
                "created_at": record.created_at
            })
    
    # Get leave records
    if filters.types is None or LogHistoryType.LEAVE in filters.types:
        leave_query = db.query(Leave).filter(Leave.employee_id == employee_id)
        
        if filters.start_date:
            leave_query = leave_query.filter(Leave.start_date >= filters.start_date)
        if filters.end_date:
            leave_query = leave_query.filter(Leave.end_date <= filters.end_date)
        
        leave_records = leave_query.order_by(Leave.created_at.desc()).offset(filters.offset).limit(filters.limit // 4 if filters.types is None else filters.limit).all()
        
        for record in leave_records:
            log_data.append({
                "id": record.id,
                "type": "leave",
                "date": record.start_date,
                "title": f"Leave - {record.leave_type.title()}",
                "description": f"{record.days} days leave. Reason: {record.reason or 'No reason provided'}",
                "status": record.leave_type,
                "metadata": {"days": record.days, "end_date": record.end_date, "reason": record.reason},
                "created_at": record.created_at
            })
    
    # Get WFH records
    if filters.types is None or LogHistoryType.WFH in filters.types:
        wfh_query = db.query(Request).filter(
            Request.requester_id == employee_id,
            Request.request_type == "wfh"
        )
        
        if filters.start_date:
            wfh_query = wfh_query.filter(Request.date >= filters.start_date)
        if filters.end_date:
            wfh_query = wfh_query.filter(Request.date <= filters.end_date)
        
        wfh_records = wfh_query.order_by(Request.created_at.desc()).offset(filters.offset).limit(filters.limit // 4 if filters.types is None else filters.limit).all()
        
        for record in wfh_records:
            days = 1
            if record.date and record.end_date:
                days = (record.end_date - record.date).days + 1
            
            log_data.append({
                "id": record.id,
                "type": "wfh",
                "date": record.date,
                "title": "Work From Home",
                "description": f"{days} days WFH. Reason: {record.description or 'No reason provided'}",
                "status": "approved",
                "metadata": {"days": days, "end_date": record.end_date, "reason": record.description},
                "created_at": record.created_at
            })
    
    # Get early/late records
    if filters.types is None or LogHistoryType.EARLY_LATE in filters.types:
        early_late_query = db.query(Request).filter(
            Request.requester_id == employee_id,
            Request.request_type.in_(["early_going", "late_coming"])
        )
        
        if filters.start_date:
            early_late_query = early_late_query.filter(Request.date >= filters.start_date)
        if filters.end_date:
            early_late_query = early_late_query.filter(Request.date <= filters.end_date)
        
        early_late_records = early_late_query.order_by(Request.created_at.desc()).offset(filters.offset).limit(filters.limit // 4 if filters.types is None else filters.limit).all()
        
        for record in early_late_records:
            details = {}
            if record.description:
                try:
                    details = eval(record.description) if record.description.startswith('{') else {}
                except:
                    details = {}
            
            duration = details.get('duration', 1.0) if isinstance(details, dict) else 1.0
            
            log_data.append({
                "id": record.id,
                "type": "early_late",
                "date": record.date,
                "title": record.request_type.replace("_", " ").title(),
                "description": f"Duration: {duration} hours. Reason: {record.description or 'No reason provided'}",
                "status": "approved",
                "metadata": {"duration": duration, "type": record.request_type},
                "created_at": record.created_at
            })
    
    # Get help ticket records
    if filters.types is None or LogHistoryType.HELP_TICKET in filters.types:
        help_query = db.query(Request).filter(
            Request.requester_id == employee_id,
            Request.request_type == "help"
        )
        
        if filters.start_date:
            help_query = help_query.filter(Request.date >= filters.start_date)
        if filters.end_date:
            help_query = help_query.filter(Request.date <= filters.end_date)
        
        help_records = help_query.order_by(Request.created_at.desc()).offset(filters.offset).limit(filters.limit // 4 if filters.types is None else filters.limit).all()
        
        for record in help_records:
            details = {}
            if record.description:
                try:
                    details = eval(record.description) if record.description.startswith('{') else {}
                except:
                    details = {}
            
            category = details.get('category', 'Other') if isinstance(details, dict) else 'Other'
            
            log_data.append({
                "id": record.id,
                "type": "help_ticket",
                "date": record.date,
                "title": f"Help Ticket - {category}",
                "description": f"Subject: {record.title or 'No subject'}. {record.description or 'No description'}",
                "status": "open",
                "metadata": {"category": category, "subject": record.title},
                "created_at": record.created_at
            })
    
    # Sort all log data by date (most recent first)
    log_data.sort(key=lambda x: x["date"], reverse=True)
    
    # Apply final pagination
    total_records = len(log_data)
    log_data = log_data[filters.offset:filters.offset + filters.limit]
    
    # Calculate comprehensive summary
    summary = {
        "attendance_records": db.query(Attendance).filter(Attendance.employee_id == employee_id).count(),
        "leave_records": db.query(Leave).filter(Leave.employee_id == employee_id).count(),
        "wfh_requests": db.query(Request).filter(Request.requester_id == employee_id, Request.request_type == "wfh").count(),
        "early_late_requests": db.query(Request).filter(Request.requester_id == employee_id, Request.request_type.in_(["early_going", "late_coming"])).count(),
        "help_tickets": db.query(Request).filter(Request.requester_id == employee_id, Request.request_type == "help").count(),
        "date_range": {
            "start": filters.start_date.isoformat() if filters.start_date else "All time",
            "end": filters.end_date.isoformat() if filters.end_date else "All time"
        }
    }
    
    pagination = {
        "total_records": total_records,
        "offset": filters.offset,
        "limit": filters.limit,
        "has_more": filters.offset + filters.limit < total_records
    }
    
    return CompleteLogHistoryResponse(
        employee_id=employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        total_records=len(log_data),
        log_data=log_data,
        summary=summary,
        pagination=pagination
    )
