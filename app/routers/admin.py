"""
Admin API routes.

This module provides admin endpoints for employee management, system configuration,
and administrative operations.
"""



from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime




from ..database import get_db

from ..models.user import User
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..models.leave import Leave, LeaveBalance
from ..models.request import Request
from ..models.message import Message
from ..models.salary import Salary, Payslip, MonthlySalaryProcessing

from ..services.leave_based_salary import LeaveBasedSalaryCalculationService


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



from ..schemas.salary_admin import (
    SalaryCreate,
    SalaryUpdate,
    SalaryResponse,
    SalaryListResponse,
    SalaryCalculationRequest,
    SalaryCalculationResponse,
    SalaryCreateAdmin,
    AutoSalaryCalculationRequest,
    AutoSalaryCalculationResponse,
    SalaryCalculationOptions,
    SalaryValidationRequest,
    SalaryValidationResponse
)

from ..schemas.admin_salary_apis import (
    CTCBreakdownResponse,
    MonthlySalaryValidationResponse,
    PayslipGenerationResponse
)



from ..schemas.salary import (
    SalaryDetailsResponse,
    PayCycleResponse,
    PayslipResponse,
    FinancesResponse
)


from ..schemas.payment_processing import (
    SinglePaymentProcessRequest,
    SinglePaymentProcessResponse,
    BulkPaymentProcessRequest,
    BulkPaymentProcessResponse,
    UnpaidSalariesCheckResponse,
    ProcessedPayslipsResponse
)

from ..schemas.monthly_salary_admin import (
    MonthlySalaryDataResponse,
    MonthlySalaryFilters,
    EmployeeMonthlySalaryData,
    MonthlySalarySummaryResponse,
    EmployeeSalarySummary,
    EmployeeSalaryDetail,
    MonthlySalaryEmployeeDetailsResponse
)


from ..schemas.leave_salary_processing import (
    LeaveBasedSalaryProcessingRequest,
    LeaveBasedSalaryProcessingResponse,
    BulkLeaveProcessingRequest,
    MonthlyProcessingStatus,
    SingleEmployeeLeaveProcessingRequest,
    SingleEmployeeLeaveProcessingResponse,
    DetailedPayslipResponse,
    PayslipFormatResponse,
    LeaveBalanceCheck
)

from ..schemas.salary_processing import (
    EmployeeSalaryProcessingRequest,
    EmployeeSalaryProcessingResponse,
    PreviousPayslipInfo,
    BulkSalaryProcessingRequest,
    BulkSalaryProcessingResponse,
    BulkProcessingEmployeeResult,
    SalaryProcessingStatusCheck
)

from ..services.employee import EmployeeService
from ..services.salary_calculation import SalaryCalculationService
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
    

    total_wfh_days = sum(
        (record.end_date - record.date).days + 1 if record.date and record.end_date else 1
        for record in db.query(Request).filter(
            Request.requester_id == employee_id,
            Request.request_type == "wfh"
        ).all()
    )
    
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


# Salary Management Endpoints

def calculate_salary_components(basic: float, hra: float, special_allowance: float, 
                              pf_deduction: float, tax_deduction: float) -> tuple[float, float, float, float]:
    """
    Calculate salary components.
    
    Args:
        basic: Basic salary
        hra: House rent allowance
        special_allowance: Special allowance
        pf_deduction: PF deduction
        tax_deduction: Tax deduction
        
    Returns:
        tuple: (monthly_gross, total_deductions, net_pay, annual_ctc)
    """
    monthly_gross = basic + hra + special_allowance
    total_deductions = pf_deduction + tax_deduction
    net_pay = monthly_gross - total_deductions
    annual_ctc = monthly_gross * 12
    
    return monthly_gross, total_deductions, net_pay, annual_ctc


@router.get("/salaries", response_model=SalaryListResponse)
def get_all_salaries_admin(
    search: Optional[str] = None,
    department: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all employee salaries (admin only).
    
    Args:
        search: Optional search term for employee name/email
        department: Optional department filter
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalaryListResponse: List of salaries with pagination info
    """
    check_admin_access(current_user)
    
    # Build query for salaries with employee information
    query = db.query(Salary).join(Employee).join(User)
    
    # Apply search filter
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(
            User.full_name.ilike(search_filter) | 
            User.email.ilike(search_filter) |
            Employee.employee_id.ilike(search_filter)
        )
    
    # Apply department filter
    if department:
        query = query.filter(Employee.department == department)
    
    # Get total count
    total_records = query.count()
    
    # Apply pagination and get results
    salaries = query.order_by(User.full_name.asc()).offset(skip).limit(limit).all()
    
    # Convert to response format
    salary_responses = []
    for salary in salaries:
        salary_responses.append(SalaryResponse(
            id=salary.id,
            employee_id=salary.employee_id,
            employee_name=salary.employee.user.full_name if salary.employee.user else "Unknown",
            employee_email=salary.employee.user.email if salary.employee.user else "",
            annual_ctc=salary.annual_ctc,
            monthly_gross=salary.monthly_gross,
            basic=salary.basic,
            hra=salary.hra,
            special_allowance=salary.special_allowance,
            pf_deduction=salary.pf_deduction,
            tax_deduction=salary.tax_deduction,
            total_deductions=salary.total_deductions,
            net_pay=salary.net_pay,
            currency=salary.currency,
            last_paid=salary.last_paid,
            next_pay_date=salary.next_pay_date,
            next_increment_date=salary.next_increment_date,
            increment_cycle=salary.increment_cycle,
            created_at=salary.created_at,
            updated_at=salary.updated_at
        ))
    
    # Calculate pagination info
    pages = (total_records + limit - 1) // limit  # Ceiling division
    
    return SalaryListResponse(
        salaries=salary_responses,
        total=total_records,
        page=skip // limit + 1,
        per_page=limit,
        pages=pages
    )



@router.get("/salaries/{employee_id}", response_model=SalaryResponse)
def get_employee_salary_admin(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get salary details for specific employee (admin only).
    
    Args:
        employee_id: Employee ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalaryResponse: Employee salary details
        
    Raises:
        HTTPException: 404 if employee or salary not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get salary
    salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found for this employee"
        )
    
    return SalaryResponse(
        id=salary.id,
        employee_id=salary.employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        employee_email=employee.user.email if employee.user else "",
        annual_ctc=salary.annual_ctc,
        monthly_gross=salary.monthly_gross,
        basic=salary.basic,
        hra=salary.hra,
        special_allowance=salary.special_allowance,
        pf_deduction=salary.pf_deduction,
        tax_deduction=salary.tax_deduction,
        total_deductions=salary.total_deductions,
        net_pay=salary.net_pay,
        currency=salary.currency,
        last_paid=salary.last_paid,
        next_pay_date=salary.next_pay_date,
        next_increment_date=salary.next_increment_date,
        increment_cycle=salary.increment_cycle,
        created_at=salary.created_at,
        updated_at=salary.updated_at
    )





@router.post("/salaries/{employee_id}", response_model=SalaryResponse)
def create_or_update_employee_salary_admin(
    employee_id: int,
    salary_data: SalaryCreateAdmin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update salary record for employee (admin only).
    
    This endpoint implements auto-calculation functionality:
    - If only annual_ctc and/or monthly_gross provided → Auto-calculate all components
    - If basic components provided → Use provided values
    - If salary exists for the employee → Update existing salary
    - If salary doesn't exist → Create new salary record
    
    Args:
        employee_id: Employee ID (path parameter)
        salary_data: Salary data (without employee_id)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalaryResponse: Created or updated salary details
        
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
    
    # Check if salary already exists for this employee
    existing_salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
    


    # Track which fields were explicitly provided (not None)
    provided_fields = {}
    if salary_data.annual_ctc is not None:
        provided_fields['annual_ctc'] = salary_data.annual_ctc
    if salary_data.monthly_gross is not None:
        provided_fields['monthly_gross'] = salary_data.monthly_gross
    if salary_data.basic is not None:
        provided_fields['basic'] = salary_data.basic
    if salary_data.hra is not None:
        provided_fields['hra'] = salary_data.hra
    if salary_data.special_allowance is not None:
        provided_fields['special_allowance'] = salary_data.special_allowance
    if salary_data.pf_deduction is not None:
        provided_fields['pf_deduction'] = salary_data.pf_deduction
    if salary_data.tax_deduction is not None:
        provided_fields['tax_deduction'] = salary_data.tax_deduction
    
    # Initialize variables - use existing salary values if not provided
    if existing_salary:
        basic = salary_data.basic if salary_data.basic is not None else existing_salary.basic
        hra = salary_data.hra if salary_data.hra is not None else existing_salary.hra
        special_allowance = salary_data.special_allowance if salary_data.special_allowance is not None else existing_salary.special_allowance
        pf_deduction = salary_data.pf_deduction if salary_data.pf_deduction is not None else existing_salary.pf_deduction
        tax_deduction = salary_data.tax_deduction if salary_data.tax_deduction is not None else existing_salary.tax_deduction
        monthly_gross = salary_data.monthly_gross if salary_data.monthly_gross is not None else existing_salary.monthly_gross
        total_deductions = salary_data.total_deductions if salary_data.total_deductions is not None else existing_salary.total_deductions
        net_pay = salary_data.net_pay if salary_data.net_pay is not None else existing_salary.net_pay
        annual_ctc = salary_data.annual_ctc if salary_data.annual_ctc is not None else existing_salary.annual_ctc
        currency = salary_data.currency if salary_data.currency else existing_salary.currency
    else:
        # For new salary, use defaults
        basic = salary_data.basic if salary_data.basic is not None else 0.0
        hra = salary_data.hra if salary_data.hra is not None else 0.0
        special_allowance = salary_data.special_allowance if salary_data.special_allowance is not None else 0.0
        pf_deduction = salary_data.pf_deduction if salary_data.pf_deduction is not None else 0.0
        tax_deduction = salary_data.tax_deduction if salary_data.tax_deduction is not None else 0.0
        monthly_gross = salary_data.monthly_gross if salary_data.monthly_gross is not None else 0.0
        total_deductions = salary_data.total_deductions if salary_data.total_deductions is not None else 0.0
        net_pay = salary_data.net_pay if salary_data.net_pay is not None else 0.0
        annual_ctc = salary_data.annual_ctc if salary_data.annual_ctc is not None else 0.0
        currency = salary_data.currency
    
    # Auto-calculation logic
    use_auto_calculation = False
    
    # Explicit auto-calculation takes precedence
    if salary_data.auto_calculate:
        use_auto_calculation = True
    # Auto-calculate only if no basic components are provided and we have annual_ctc or monthly_gross
    elif (not any(field in provided_fields for field in ['basic', 'hra', 'special_allowance']) and 
          (annual_ctc > 0 or monthly_gross > 0)):
        use_auto_calculation = True
    
    try:
        calculation_service = SalaryCalculationService()
        


        if use_auto_calculation:
            # Auto-calculate all components from annual CTC or monthly gross
            # Construct options from individual fields
            options = {
                'city': salary_data.city,
                'state': salary_data.state,
                'basic_percentage': salary_data.basic_percentage,
                'include_employer_pf': False,  # This field is not in SalaryCreateAdmin
                'calculate_tax': salary_data.calculate_tax,
                'calculate_pf': salary_data.calculate_pf,
                'calculate_hra': salary_data.calculate_hra
            }
            
            # Add overrides if provided
            if salary_data.overrides:
                options['overrides'] = salary_data.overrides
            
            auto_result = calculation_service.calculate_from_annual_ctc_or_monthly_gross(
                annual_ctc=annual_ctc,
                monthly_gross=monthly_gross,
                options=options
            )
            
            # Extract calculated values
            basic = auto_result.basic
            hra = auto_result.hra
            special_allowance = auto_result.special_allowance
            pf_deduction = auto_result.pf_deduction
            tax_deduction = auto_result.tax_deduction
            monthly_gross = auto_result.monthly_gross
            total_deductions = auto_result.total_deductions
            net_pay = auto_result.net_pay
            annual_ctc = auto_result.annual_ctc
            


        else:
            # Manual calculation or selective updates
            # Handle different update scenarios:
            
            # Scenario 1: Only deductions provided (no basic components)
            if (not any(field in provided_fields for field in ['basic', 'hra', 'special_allowance', 'annual_ctc', 'monthly_gross']) and
                any(field in provided_fields for field in ['pf_deduction', 'tax_deduction'])):
                # Only update deductions and recalculate total_deductions and net_pay
                # Preserve existing basic components and gross salary
                total_deductions = pf_deduction + tax_deduction
                net_pay = monthly_gross - total_deductions
                # Keep annual_ctc unchanged unless explicitly provided
                
            # Scenario 2: Basic components provided
            elif any(field in provided_fields for field in ['basic', 'hra', 'special_allowance']):
                # Recalculate monthly_gross from basic components
                if monthly_gross == 0:
                    monthly_gross = basic + hra + special_allowance
                total_deductions = pf_deduction + tax_deduction
                net_pay = monthly_gross - total_deductions
                # Only calculate annual_ctc if not explicitly provided
                if 'annual_ctc' not in provided_fields:
                    annual_ctc = monthly_gross * 12
                    
            # Scenario 3: Only annual_ctc provided
            elif 'annual_ctc' in provided_fields and not any(field in provided_fields for field in ['basic', 'hra', 'special_allowance', 'monthly_gross']):
                # Update annual_ctc and recalculate monthly_gross, but preserve basic components
                if monthly_gross == 0:
                    monthly_gross = annual_ctc / 12
                # Only calculate basic components if they are currently 0
                if basic == 0:
                    basic = monthly_gross * 0.4  # Default 40% for basic
                if hra == 0:
                    hra = monthly_gross * 0.2   # Default 20% for HRA
                if special_allowance == 0:
                    special_allowance = monthly_gross - basic - hra
                    
                total_deductions = pf_deduction + tax_deduction
                net_pay = monthly_gross - total_deductions
                
            # Scenario 4: Mixed updates
            else:
                # Handle mixed scenarios
                if 'annual_ctc' in provided_fields and 'monthly_gross' not in provided_fields:
                    monthly_gross = annual_ctc / 12
                elif 'monthly_gross' in provided_fields and 'annual_ctc' not in provided_fields:
                    annual_ctc = monthly_gross * 12
                    
                total_deductions = pf_deduction + tax_deduction
                net_pay = monthly_gross - total_deductions
        


        # Validate the calculated/provided structure
        validation_result = calculation_service.validate_salary_structure_detailed(
            annual_ctc=annual_ctc,
            monthly_gross=monthly_gross,
            basic=basic,
            hra=hra,
            special_allowance=special_allowance,
            pf_deduction=pf_deduction,
            tax_deduction=tax_deduction
        )
        
        # Log warnings if any
        if validation_result.recommendations:
            print(f"Warning: {validation_result.recommendations}")
        
        # Update or create salary record
        if existing_salary:
            # Update existing salary
            existing_salary.annual_ctc = annual_ctc
            existing_salary.monthly_gross = monthly_gross
            existing_salary.basic = basic
            existing_salary.hra = hra
            existing_salary.special_allowance = special_allowance
            existing_salary.pf_deduction = pf_deduction
            existing_salary.tax_deduction = tax_deduction
            existing_salary.total_deductions = total_deductions
            existing_salary.net_pay = net_pay
            existing_salary.currency = salary_data.currency
            existing_salary.next_pay_date = salary_data.next_pay_date
            existing_salary.next_increment_date = salary_data.next_increment_date
            existing_salary.increment_cycle = salary_data.increment_cycle
            
            salary = existing_salary
            action = "updated"
        else:
            # Create new salary record
            salary = Salary(
                employee_id=employee_id,
                annual_ctc=annual_ctc,
                monthly_gross=monthly_gross,
                basic=basic,
                hra=hra,
                special_allowance=special_allowance,
                pf_deduction=pf_deduction,
                tax_deduction=tax_deduction,
                total_deductions=total_deductions,
                net_pay=net_pay,
                currency=salary_data.currency,
                next_pay_date=salary_data.next_pay_date,
                next_increment_date=salary_data.next_increment_date,
                increment_cycle=salary_data.increment_cycle
            )
            
            db.add(salary)
            action = "created"
        
        db.commit()
        db.refresh(salary)
        
        return SalaryResponse(
            id=salary.id,
            employee_id=salary.employee_id,
            employee_name=employee.user.full_name if employee.user else "Unknown",
            employee_email=employee.user.email if employee.user else "",
            annual_ctc=salary.annual_ctc,
            monthly_gross=salary.monthly_gross,
            basic=salary.basic,
            hra=salary.hra,
            special_allowance=salary.special_allowance,
            pf_deduction=salary.pf_deduction,
            tax_deduction=salary.tax_deduction,
            total_deductions=salary.total_deductions,
            net_pay=salary.net_pay,
            currency=salary.currency,
            last_paid=salary.last_paid,
            next_pay_date=salary.next_pay_date,
            next_increment_date=salary.next_increment_date,
            increment_cycle=salary.increment_cycle,
            created_at=salary.created_at,
            updated_at=salary.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/salaries/{employee_id}", response_model=SalaryResponse)
def update_employee_salary_admin(
    employee_id: int,
    salary_data: SalaryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update salary details for employee (admin only).
    
    Args:
        employee_id: Employee ID
        salary_data: Salary update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalaryResponse: Updated salary details
        
    Raises:
        HTTPException: 404 if employee or salary not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get existing salary
    salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found for this employee"
        )
    

    # Track which fields were explicitly provided (not None)
    provided_fields = {}
    if salary_data.annual_ctc is not None:
        provided_fields['annual_ctc'] = salary_data.annual_ctc
    if salary_data.monthly_gross is not None:
        provided_fields['monthly_gross'] = salary_data.monthly_gross
    if salary_data.basic is not None:
        provided_fields['basic'] = salary_data.basic
    if salary_data.hra is not None:
        provided_fields['hra'] = salary_data.hra
    if salary_data.special_allowance is not None:
        provided_fields['special_allowance'] = salary_data.special_allowance
    if salary_data.pf_deduction is not None:
        provided_fields['pf_deduction'] = salary_data.pf_deduction
    if salary_data.tax_deduction is not None:
        provided_fields['tax_deduction'] = salary_data.tax_deduction
    
    # Update fields that are provided
    update_data = {}
    if salary_data.annual_ctc is not None:
        update_data['annual_ctc'] = salary_data.annual_ctc
    if salary_data.monthly_gross is not None:
        update_data['monthly_gross'] = salary_data.monthly_gross
    if salary_data.basic is not None:
        update_data['basic'] = salary_data.basic
    if salary_data.hra is not None:
        update_data['hra'] = salary_data.hra
    if salary_data.special_allowance is not None:
        update_data['special_allowance'] = salary_data.special_allowance
    if salary_data.pf_deduction is not None:
        update_data['pf_deduction'] = salary_data.pf_deduction
    if salary_data.tax_deduction is not None:
        update_data['tax_deduction'] = salary_data.tax_deduction
    if salary_data.currency is not None:
        update_data['currency'] = salary_data.currency
    if salary_data.next_pay_date is not None:
        update_data['next_pay_date'] = salary_data.next_pay_date
    if salary_data.next_increment_date is not None:
        update_data['next_increment_date'] = salary_data.next_increment_date
    if salary_data.increment_cycle is not None:
        update_data['increment_cycle'] = salary_data.increment_cycle
    
    # Handle selective salary updates with smart recalculation
    if any(field in provided_fields for field in ['basic', 'hra', 'special_allowance', 'pf_deduction', 'tax_deduction']):
        # Get current values or provided values
        basic = salary_data.basic if salary_data.basic is not None else salary.basic
        hra = salary_data.hra if salary_data.hra is not None else salary.hra
        special_allowance = salary_data.special_allowance if salary_data.special_allowance is not None else salary.special_allowance
        pf_deduction = salary_data.pf_deduction if salary_data.pf_deduction is not None else salary.pf_deduction
        tax_deduction = salary_data.tax_deduction if salary_data.tax_deduction is not None else salary.tax_deduction
        
        # Handle different scenarios
        if (not any(field in provided_fields for field in ['basic', 'hra', 'special_allowance']) and
            any(field in provided_fields for field in ['pf_deduction', 'tax_deduction'])):
            # Only deductions provided - update deductions and net_pay, preserve other components
            current_basic = salary.basic
            current_hra = salary.hra
            current_special_allowance = salary.special_allowance
            current_monthly_gross = salary.monthly_gross
            
            total_deductions = pf_deduction + tax_deduction
            net_pay = current_monthly_gross - total_deductions
            annual_ctc = salary.annual_ctc  # Keep unchanged unless explicitly provided
            
            update_data['pf_deduction'] = pf_deduction
            update_data['tax_deduction'] = tax_deduction
            update_data['total_deductions'] = total_deductions
            update_data['net_pay'] = net_pay
            if 'annual_ctc' not in provided_fields:
                update_data['annual_ctc'] = annual_ctc
                
        elif any(field in provided_fields for field in ['basic', 'hra', 'special_allowance']):
            # Basic components provided - recalculate from basic components
            monthly_gross = basic + hra + special_allowance
            total_deductions = pf_deduction + tax_deduction
            net_pay = monthly_gross - total_deductions
            annual_ctc = salary.annual_ctc  # Keep existing unless explicitly provided
            
            update_data['basic'] = basic
            update_data['hra'] = hra
            update_data['special_allowance'] = special_allowance
            update_data['pf_deduction'] = pf_deduction
            update_data['tax_deduction'] = tax_deduction
            update_data['monthly_gross'] = monthly_gross
            update_data['total_deductions'] = total_deductions
            update_data['net_pay'] = net_pay
            if 'annual_ctc' not in provided_fields:
                update_data['annual_ctc'] = annual_ctc
                
        else:
            # Fallback for mixed updates
            monthly_gross, total_deductions, net_pay, annual_ctc = calculate_salary_components(
                basic, hra, special_allowance, pf_deduction, tax_deduction
            )
            update_data['monthly_gross'] = monthly_gross
            update_data['total_deductions'] = total_deductions
            update_data['net_pay'] = net_pay
            if 'annual_ctc' not in provided_fields:
                update_data['annual_ctc'] = annual_ctc
                
    elif 'annual_ctc' in provided_fields and 'monthly_gross' not in provided_fields:
        # Only annual_ctc provided - update it and recalculate monthly_gross
        monthly_gross = salary_data.annual_ctc / 12
        update_data['annual_ctc'] = salary_data.annual_ctc
        update_data['monthly_gross'] = monthly_gross
        
    elif 'monthly_gross' in provided_fields and 'annual_ctc' not in provided_fields:
        # Only monthly_gross provided - update it and recalculate annual_ctc
        annual_ctc = salary_data.monthly_gross * 12
        update_data['monthly_gross'] = salary_data.monthly_gross
        update_data['annual_ctc'] = annual_ctc
    
    # Handle explicitly provided total_deductions and net_pay
    if salary_data.total_deductions is not None:
        update_data['total_deductions'] = salary_data.total_deductions
    if salary_data.net_pay is not None:
        update_data['net_pay'] = salary_data.net_pay
    
    # Apply updates
    for field, value in update_data.items():
        setattr(salary, field, value)
    
    db.commit()
    db.refresh(salary)
    
    return SalaryResponse(
        id=salary.id,
        employee_id=salary.employee_id,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        employee_email=employee.user.email if employee.user else "",
        annual_ctc=salary.annual_ctc,
        monthly_gross=salary.monthly_gross,
        basic=salary.basic,
        hra=salary.hra,
        special_allowance=salary.special_allowance,
        pf_deduction=salary.pf_deduction,
        tax_deduction=salary.tax_deduction,
        total_deductions=salary.total_deductions,
        net_pay=salary.net_pay,
        currency=salary.currency,
        last_paid=salary.last_paid,
        next_pay_date=salary.next_pay_date,
        next_increment_date=salary.next_increment_date,
        increment_cycle=salary.increment_cycle,
        created_at=salary.created_at,
        updated_at=salary.updated_at
    )


@router.delete("/salaries/{employee_id}")
def delete_employee_salary_admin(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete salary record for employee (admin only).
    
    Args:
        employee_id: Employee ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if employee or salary not found
    """
    check_admin_access(current_user)
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get salary
    salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found for this employee"
        )
    

    # Delete salary record
    db.delete(salary)
    db.commit()



    return {"message": f"Salary record deleted successfully for employee {employee.user.full_name if employee.user else employee_id}"}


@router.post("/salaries/calculate", response_model=SalaryCalculationResponse)
def calculate_salary_components_endpoint(
    calculation_data: SalaryCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate salary components (admin only).
    
    Args:
        calculation_data: Salary calculation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SalaryCalculationResponse: Calculated salary components
    """
    check_admin_access(current_user)
    
    monthly_gross, total_deductions, net_pay, annual_ctc = calculate_salary_components(
        calculation_data.basic,
        calculation_data.hra,
        calculation_data.special_allowance,
        calculation_data.pf_deduction,
        calculation_data.tax_deduction
    )
    
    return SalaryCalculationResponse(
        monthly_gross=monthly_gross,
        total_deductions=total_deductions,
        net_pay=net_pay,
        annual_ctc=annual_ctc
    )


@router.post("/salaries/calculate/auto", response_model=AutoSalaryCalculationResponse)
def calculate_salary_auto(
    calculation_request: AutoSalaryCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Auto-calculate salary components from annual CTC or monthly gross (admin only).
    
    Args:
        calculation_request: Auto calculation request with annual_ctc or monthly_gross
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AutoSalaryCalculationResponse: Calculated salary components with breakdown
    """
    check_admin_access(current_user)
    
    try:
        calculation_service = SalaryCalculationService()
        result = calculation_service.calculate_from_annual_ctc_or_monthly_gross(
            annual_ctc=calculation_request.annual_ctc,
            monthly_gross=calculation_request.monthly_gross,
            options=calculation_request.options
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Payment Processing Endpoints


@router.get("/salary/check-unpaid", response_model=UnpaidSalariesCheckResponse)
def check_unpaid_salaries(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check for employees with unpaid salaries and list them.
    
    Args:
        month: Optional month to check (1-12). If not provided, checks current month
        year: Optional year to check. If not provided, checks current year
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UnpaidSalariesCheckResponse: List of unpaid employees
    """
    check_admin_access(current_user)
    
    # Use current month/year if not provided
    if month is None:
        month = date.today().month
    if year is None:
        year = date.today().year
    
    # Get all active employees
    employees = db.query(Employee).filter(
        Employee.status.in_(["active", "full_time", "in-probation"])
    ).all()
    
    total_employees = len(employees)
    paid_employees = 0
    unpaid_employee_details = []
    
    for employee in employees:
        # Get all payslips for the employee
        payslips = db.query(Payslip).filter(
            Payslip.employee_id == employee.id
        ).all()
        
        # Check if there are any unpaid payslips for the specified month/year
        if month and year:
            target_payslip = db.query(Payslip).filter(
                Payslip.employee_id == employee.id,
                Payslip.month == month,
                Payslip.year == year
            ).first()
            
            if target_payslip and target_payslip.status != "paid":
                # Employee has unpaid payslip for specified month/year
                unpaid_employee_details.append({
                    "employee_id": employee.id,
                    "employee_name": employee.user.full_name if employee.user else "Unknown",
                    "employee_email": employee.user.email if employee.user else "",
                    "department": employee.department,
                    "pending_payslips": [{
                        "month": target_payslip.month,
                        "year": target_payslip.year,
                        "amount": target_payslip.amount,
                        "status": target_payslip.status
                    }],
                    "total_pending_amount": target_payslip.amount
                })
            elif not target_payslip:
                # No payslip exists for specified month/year - consider as unpaid
                unpaid_employee_details.append({
                    "employee_id": employee.id,
                    "employee_name": employee.user.full_name if employee.user else "Unknown",
                    "employee_email": employee.user.email if employee.user else "",
                    "department": employee.department,
                    "pending_payslips": [{
                        "month": month,
                        "year": year,
                        "amount": employee.salary.net_pay if employee.salary else 0,
                        "status": "pending"
                    }],
                    "total_pending_amount": employee.salary.net_pay if employee.salary else 0
                })
            else:
                # Employee is paid for the specified month/year
                paid_employees += 1
        else:
            # Check all unpaid payslips
            unpaid_payslips = [p for p in payslips if p.status != "paid"]
            if unpaid_payslips:
                pending_amount = sum(p.amount for p in unpaid_payslips)
                unpaid_employee_details.append({
                    "employee_id": employee.id,
                    "employee_name": employee.user.full_name if employee.user else "Unknown",
                    "employee_email": employee.user.email if employee.user else "",
                    "department": employee.department,
                    "pending_payslips": [{
                        "month": p.month,
                        "year": p.year,
                        "amount": p.amount,
                        "status": p.status
                    } for p in unpaid_payslips],
                    "total_pending_amount": pending_amount
                })
            else:
                paid_employees += 1
    
    unpaid_employees = len(unpaid_employee_details)
    

    return UnpaidSalariesCheckResponse(
        total_employees=total_employees,
        paid_employees=paid_employees,
        unpaid_employees=unpaid_employees,
        unpaid_employee_details=unpaid_employee_details,
        check_date=date.today()
    )











# =============================================================================
# PROCESSED PAYSLIPS ENDPOINT
# =============================================================================

@router.get("/payslips/processed", response_model=ProcessedPayslipsResponse)
def get_all_processed_payslips(
    month: Optional[int] = None,
    year: Optional[int] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all processed payslips (admin only).
    
    This endpoint returns a list of all processed payslips with employee information.
    Supports filtering by month, year, department, and status.
    
    Args:
        month: Optional month filter (1-12)
        year: Optional year filter
        department: Optional department filter
        status: Optional status filter (default: "paid" for processed payslips)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records (for pagination)
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        ProcessedPayslipsResponse: List of processed payslips with pagination info
        
    Raises:
        HTTPException: 403 if not admin
    """
    check_admin_access(current_user)
    
    # Default status to "paid" for processed payslips if not specified
    if status is None:
        status = "paid"
    
    # Validate month parameter if provided
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    try:
        # Build query for processed payslips with employee and user information
        query = db.query(Payslip).join(Employee).join(User)
        
        # Apply status filter (default to "paid")
        query = query.filter(Payslip.status == status)
        
        # Apply month filter if provided
        if month is not None:
            query = query.filter(Payslip.month == month)
        
        # Apply year filter if provided
        if year is not None:
            query = query.filter(Payslip.year == year)
        
        # Apply department filter if provided
        if department is not None:
            query = query.filter(Employee.department == department)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        # Order by most recent processed date first
        processed_payslips = query.order_by(
            Payslip.processed_at.desc(),
            Payslip.id.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to response format
        processed_payslip_items = []
        for payslip in processed_payslips:
            processed_payslip_items.append({
                "employee_id": payslip.employee_id,
                "email": payslip.employee.user.email if payslip.employee.user else "",
                "amount_processed": payslip.amount,
                "status": payslip.status,
                "processed_at": payslip.processed_at
            })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        current_page = (skip // limit) + 1
        
        return ProcessedPayslipsResponse(
            success=True,
            message=f"Retrieved {len(processed_payslip_items)} processed payslips",
            processed_payslips=processed_payslip_items,
            total_count=total_count,
            page=current_page,
            per_page=limit,
            total_pages=total_pages,
            generated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving processed payslips: {str(e)}"
        )


# =============================================================================
# THREE MAIN ADMIN APIs REQUESTED BY USER
# =============================================================================

@router.get("/salary/ctc-breakdown/{employee_id}", response_model=CTCBreakdownResponse)
def get_employee_ctc_breakdown(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API 1: Get complete CTC breakdown for an employee (based on current calculations).
    
    This endpoint provides a comprehensive breakdown of an employee's Cost to Company (CTC)
    including all salary components, deductions, and calculation details.
    
    Args:
        employee_id: Employee ID
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        CTCBreakdownResponse: Complete CTC breakdown with calculation details
        
    Raises:
        HTTPException: 403 if not admin, 404 if employee not found
    """
    check_admin_access(current_user)
    
    try:
        salary_service = SalaryCalculationService()
        result = salary_service.get_ctc_breakdown_for_employee(db, employee_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting CTC breakdown: {str(e)}"
        )



@router.post("/salary/validate-monthly/{employee_id}", response_model=MonthlySalaryValidationResponse)
def validate_monthly_salary_with_leaves(
    employee_id: int,
    year: int,
    month: int,
    unpaid_leave_days: Optional[float] = None,
    half_day_leaves: Optional[float] = None,
    custom_deduction: float = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API 2: Validate and generate employee salary for a month based on unpaid leaves.
    
    This endpoint validates the salary calculation for a specific month considering
    unpaid leaves, half-day leaves, and custom deductions.
    
    Automatically fetches unpaid leaves data from the leaves model for the specified month.
    If unpaid_leave_days or half_day_leaves are not provided, they will be automatically
    fetched from the employee's leave records.
    
    Args:
        employee_id: Employee ID
        year: Year
        month: Month (1-12)
        unpaid_leave_days: Number of unpaid leave days (optional, auto-fetched if None)
        half_day_leaves: Number of half-day leaves (optional, auto-fetched if None)
        custom_deduction: Custom additional deduction
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        MonthlySalaryValidationResponse: Validation results and calculations
        
    Raises:
        HTTPException: 403 if not admin, 404 if employee not found
    """
    check_admin_access(current_user)
    
    try:
        salary_service = SalaryCalculationService()
        result = salary_service.validate_monthly_salary_with_leaves(
            db=db,
            employee_id=employee_id,
            year=year,
            month=month,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            custom_deduction=custom_deduction
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating monthly salary: {str(e)}"
        )



@router.post("/salary/generate-payslip/{employee_id}", response_model=PayslipGenerationResponse)
def generate_employee_payslip_with_leaves(
    employee_id: int,
    year: int,
    month: int,
    unpaid_leave_days: Optional[float] = None,
    half_day_leaves: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    API 3: Generate employee salary payslips based on unpaid leaves.
    
    This endpoint generates a detailed payslip with leave calculations showing:
    - CTC, in-hand salary, total days, total working days
    - Per-day salary (in-hand salary / days in month)
    - Unpaid leaves taken, salary cut = unpaid_leaves × per_day_salary
    - Total processed salary = in_hand_salary - salary_cut
    
    Automatically fetches unpaid leaves data from the leaves model for the specified month.
    If unpaid_leave_days or half_day_leaves are not provided, they will be automatically
    fetched from the employee's leave records and salary will be calculated based only
    on unpaid leaves (not paid leaves).
    
    Args:
        employee_id: Employee ID
        year: Year
        month: Month (1-12)
        unpaid_leave_days: Override unpaid leave days (optional, auto-fetched if None)
        half_day_leaves: Override half-day leaves (optional, auto-fetched if None)
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        PayslipGenerationResponse: Detailed payslip with all requested information
        
    Raises:
        HTTPException: 403 if not admin, 404 if employee not found
    """
    check_admin_access(current_user)
    
    try:
        salary_service = SalaryCalculationService()
        result = salary_service.generate_detailed_payslip_with_leaves(
            db=db,
            employee_id=employee_id,
            year=year,
            month=month,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating payslip: {str(e)}"
        )


# =============================================================================
# SALARY PROCESSING API ENDPOINT
# =============================================================================

@router.post("/salary/process/{employee_id}", response_model=EmployeeSalaryProcessingResponse)
def process_employee_salary(
    employee_id: int,
    month: int,
    year: int,
    amount: Optional[float] = None,
    custom_deductions: float = 0.0,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process employee salary with payslip generation and monthly tracking.
    
    This endpoint processes salary for a specific employee, month, and year while preventing
    duplicate payments. It creates/updates both payslip and monthly_salary_processing records.
    
    Features:
    - Prevents duplicate payments for the same employee/month/year
    - Creates or updates payslip record with status = "paid"
    - Updates MonthlySalaryProcessing record for the month/year
    - Handles custom deductions and optional notes
    - Returns detailed processing information
    
    Args:
        employee_id: Employee ID (path parameter)
        month: Month for salary processing (1-12, query parameter)
        year: Year for salary processing (query parameter)
        amount: Optional amount to process (defaults to employee's net_pay)
        custom_deductions: Additional custom deductions (default: 0.0)
        notes: Optional notes for this payment
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        EmployeeSalaryProcessingResponse: Processing results with payslip and monthly tracking info
        
    Raises:
        HTTPException: 403 if not admin, 404 if employee not found, 409 if duplicate payment
    """
    check_admin_access(current_user)
    
    # Validate month parameter
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    # Validate custom deductions
    if custom_deductions < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom deductions cannot be negative"
        )
    
    try:
        # Verify employee exists and get salary information
        employee = EmployeeService.get_employee_by_id(db, employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        if not employee.salary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary information not found for this employee"
            )
        
        # Check for existing paid payslip for duplicate prevention
        existing_payslip = db.query(Payslip).filter(
            Payslip.employee_id == employee_id,
            Payslip.month == month,
            Payslip.year == year,
            Payslip.status == "paid"
        ).first()
        
        if existing_payslip:
            # Duplicate payment detected - return error with previous payslip info
            previous_payslip_info = PreviousPayslipInfo(
                payslip_id=existing_payslip.id,
                amount=existing_payslip.amount,
                processed_at=existing_payslip.processed_at,
                status=existing_payslip.status
            )
            
            return EmployeeSalaryProcessingResponse(
                success=False,
                message=f"Salary already processed for {employee.user.full_name if employee.user else employee_id} in {month}/{year}",
                employee_id=employee_id,
                employee_name=employee.user.full_name if employee.user else "Unknown",
                employee_email=employee.user.email if employee.user else "",
                month=month,
                year=year,
                amount_processed=0.0,
                status="duplicate_prevented",
                processed_at=datetime.now(),
                duplicate_prevented=True,
                previous_payslip_info=previous_payslip_info
            )
        
        # Calculate processing amount
        base_amount = amount if amount is not None else employee.salary.net_pay
        final_amount = max(0, base_amount - custom_deductions)
        
        # Check for existing payslip (pending or other status) to update
        existing_payslip_any_status = db.query(Payslip).filter(
            Payslip.employee_id == employee_id,
            Payslip.month == month,
            Payslip.year == year
        ).first()
        
        payslip_id = None
        if existing_payslip_any_status:
            # Update existing payslip
            existing_payslip_any_status.amount = final_amount
            existing_payslip_any_status.status = "paid"
            existing_payslip_any_status.processed_at = datetime.now()
            if notes:
                existing_payslip_any_status.notes = notes
            payslip_id = existing_payslip_any_status.id
            
            payslip_details = {
                "action": "updated",
                "previous_status": existing_payslip_any_status.status,
                "previous_amount": existing_payslip_any_status.amount,
                "notes_added": notes is not None
            }
        else:
            # Create new payslip
            new_payslip = Payslip(
                employee_id=employee_id,
                month=month,
                year=year,
                amount=final_amount,
                status="paid",
                processed_at=datetime.now(),
                basic_paid=employee.salary.basic,
                basic_actual=employee.salary.basic,
                hra_paid=employee.salary.hra,
                hra_actual=employee.salary.hra,
                medical_allowance_paid=0.0,
                medical_allowance_actual=0.0,
                conveyance_allowance_paid=0.0,
                conveyance_allowance_actual=0.0,
                total_earnings_paid=employee.salary.monthly_gross,
                total_earnings_actual=employee.salary.monthly_gross,
                professional_tax=employee.salary.tax_deduction,
                total_deductions=employee.salary.total_deductions,
                actual_payable_days=22.0,  # Default working days
                total_working_days=22.0,
                loss_of_pay_days=0.0,
                days_payable=22.0,
                leave_deduction_amount=custom_deductions
            )
            db.add(new_payslip)
            db.flush()  # Get the ID without committing
            payslip_id = new_payslip.id
            
            payslip_details = {
                "action": "created",
                "basic": employee.salary.basic,
                "hra": employee.salary.hra,
                "special_allowance": employee.salary.special_allowance,
                "pf_deduction": employee.salary.pf_deduction,
                "tax_deduction": employee.salary.tax_deduction,
                "total_deductions": employee.salary.total_deductions,
                "net_pay": employee.salary.net_pay,
                "custom_deductions": custom_deductions,
                "notes": notes
            }
        
        # Update or create MonthlySalaryProcessing record
        monthly_processing = db.query(MonthlySalaryProcessing).filter(
            MonthlySalaryProcessing.month == month,
            MonthlySalaryProcessing.year == year
        ).first()
        
        monthly_processing_id = None
        if monthly_processing:
            # Update existing record
            monthly_processing.successful_payments += 1
            monthly_processing.total_processed_amount += final_amount
            monthly_processing.processed_at = datetime.now()
            monthly_processing_id = monthly_processing.id
            
            monthly_processing_details = {
                "action": "updated",
                "previous_successful_payments": monthly_processing.successful_payments - 1,
                "previous_total_amount": monthly_processing.total_processed_amount - final_amount,
                "increment": 1,
                "amount_added": final_amount
            }
        else:
            # Create new record
            new_monthly_processing = MonthlySalaryProcessing(
                month=month,
                year=year,
                processed_at=datetime.now(),
                total_employees=1,
                successful_payments=1,
                failed_payments=0,
                total_processed_amount=final_amount,
                status="completed"
            )
            db.add(new_monthly_processing)
            db.flush()  # Get the ID without committing
            monthly_processing_id = new_monthly_processing.id
            
            monthly_processing_details = {
                "action": "created",
                "total_employees": 1,
                "successful_payments": 1,
                "failed_payments": 0,
                "total_processed_amount": final_amount,
                "status": "completed"
            }
        
        # Commit all changes
        db.commit()
        
        return EmployeeSalaryProcessingResponse(
            success=True,
            message=f"Salary processed successfully for {employee.user.full_name if employee.user else employee_id}",
            employee_id=employee_id,
            employee_name=employee.user.full_name if employee.user else "Unknown",
            employee_email=employee.user.email if employee.user else "",
            month=month,
            year=year,
            amount_processed=final_amount,
            status="paid",
            processed_at=datetime.now(),
            payslip_id=payslip_id,
            monthly_processing_id=monthly_processing_id,
            duplicate_prevented=False,
            payslip_details=payslip_details,
            monthly_processing_details=monthly_processing_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing salary: {str(e)}"
        )


@router.get("/salary/check-processing-status/{employee_id}", response_model=SalaryProcessingStatusCheck)
def check_salary_processing_status(
    employee_id: int,
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check salary processing status for an employee.
    
    This endpoint checks if salary has been processed for a specific employee and month/year,
    providing information about existing payslips and monthly processing records.
    
    Args:
        employee_id: Employee ID
        month: Month to check (1-12)
        year: Year to check
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        SalaryProcessingStatusCheck: Processing status information
        
    Raises:
        HTTPException: 403 if not admin, 404 if employee not found
    """
    check_admin_access(current_user)
    
    # Validate month parameter
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    # Verify employee exists
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check for existing payslip
    existing_payslip = db.query(Payslip).filter(
        Payslip.employee_id == employee_id,
        Payslip.month == month,
        Payslip.year == year
    ).first()
    
    payslip_status = None
    if existing_payslip:
        payslip_status = {
            "has_paid_payslip": existing_payslip.status == "paid",
            "payslip_id": existing_payslip.id,
            "payslip_amount": existing_payslip.amount,
            "payslip_status": existing_payslip.status,
            "processed_at": existing_payslip.processed_at
        }
    else:
        payslip_status = {
            "has_paid_payslip": False,
            "payslip_id": None,
            "payslip_amount": None,
            "payslip_status": None,
            "processed_at": None
        }
    
    # Check for monthly processing record
    monthly_processing = db.query(MonthlySalaryProcessing).filter(
        MonthlySalaryProcessing.month == month,
        MonthlySalaryProcessing.year == year
    ).first()
    
    monthly_processing_status = {
        "monthly_processing_record_exists": monthly_processing is not None,
        "monthly_processing_id": monthly_processing.id if monthly_processing else None
    }
    
    return SalaryProcessingStatusCheck(
        employee_id=employee_id,
        month=month,
        year=year,
        **payslip_status,
        **monthly_processing_status,
        employee_name=employee.user.full_name if employee.user else "Unknown",
        employee_email=employee.user.email if employee.user else ""
    )


@router.post("/salary/bulk-process", response_model=BulkSalaryProcessingResponse)
def bulk_process_salaries(
    month: int,
    year: int,
    employee_ids: Optional[List[int]] = None,
    custom_deductions: float = 0.0,
    notes: Optional[str] = None,
    skip_duplicates: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk process salaries for multiple employees.
    
    This endpoint processes salary for multiple employees for the same month and year,
    with optional filtering by employee IDs and duplicate prevention.
    
    Args:
        month: Month for salary processing (1-12)
        year: Year for salary processing
        employee_ids: Optional list of specific employee IDs to process (None = all active employees)
        custom_deductions: Additional custom deductions for all employees
        notes: Optional notes for these payments
        skip_duplicates: Whether to skip employees who already have paid payslips
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        BulkSalaryProcessingResponse: Bulk processing results
        
    Raises:
        HTTPException: 403 if not admin, 400 for invalid parameters
    """
    check_admin_access(current_user)
    
    # Validate parameters
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    if custom_deductions < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom deductions cannot be negative"
        )
    
    try:
        # Get employees to process
        if employee_ids:
            # Process specific employees
            employees = db.query(Employee).filter(
                Employee.id.in_(employee_ids),
                Employee.status.in_(["active", "full_time", "in-probation"])
            ).all()
        else:
            # Process all active employees
            employees = db.query(Employee).filter(
                Employee.status.in_(["active", "full_time", "in-probation"])
            ).all()
        
        processed_employees = []
        failed_employees = []
        skipped_employees = []
        total_amount_processed = 0.0
        
        for employee in employees:
            try:
                # Check if employee has salary information
                if not employee.salary:
                    failed_employees.append(BulkProcessingEmployeeResult(
                        employee_id=employee.id,
                        employee_name=employee.user.full_name if employee.user else "Unknown",
                        success=False,
                        message="Salary information not found",
                        duplicate_prevented=False
                    ))
                    continue
                
                # Check for existing paid payslip if skipping duplicates
                if skip_duplicates:
                    existing_payslip = db.query(Payslip).filter(
                        Payslip.employee_id == employee.id,
                        Payslip.month == month,
                        Payslip.year == year,
                        Payslip.status == "paid"
                    ).first()
                    
                    if existing_payslip:
                        skipped_employees.append(BulkProcessingEmployeeResult(
                            employee_id=employee.id,
                            employee_name=employee.user.full_name if employee.user else "Unknown",
                            success=False,
                            message=f"Salary already processed in {month}/{year}",
                            duplicate_prevented=True
                        ))
                        continue
                
                # Calculate processing amount
                base_amount = employee.salary.net_pay
                final_amount = max(0, base_amount - custom_deductions)
                
                # Create or update payslip
                existing_payslip = db.query(Payslip).filter(
                    Payslip.employee_id == employee.id,
                    Payslip.month == month,
                    Payslip.year == year
                ).first()
                
                if existing_payslip:
                    existing_payslip.amount = final_amount
                    existing_payslip.status = "paid"
                    existing_payslip.processed_at = datetime.now()
                    if notes:
                        existing_payslip.notes = notes
                    payslip_id = existing_payslip.id
                else:
                    new_payslip = Payslip(
                        employee_id=employee.id,
                        month=month,
                        year=year,
                        amount=final_amount,
                        status="paid",
                        processed_at=datetime.now(),
                        basic_paid=employee.salary.basic,
                        basic_actual=employee.salary.basic,
                        hra_paid=employee.salary.hra,
                        hra_actual=employee.salary.hra,
                        medical_allowance_paid=0.0,
                        medical_allowance_actual=0.0,
                        conveyance_allowance_paid=0.0,
                        conveyance_allowance_actual=0.0,
                        total_earnings_paid=employee.salary.monthly_gross,
                        total_earnings_actual=employee.salary.monthly_gross,
                        professional_tax=employee.salary.tax_deduction,
                        total_deductions=employee.salary.total_deductions,
                        actual_payable_days=22.0,
                        total_working_days=22.0,
                        loss_of_pay_days=0.0,
                        days_payable=22.0,
                        leave_deduction_amount=custom_deductions
                    )
                    db.add(new_payslip)
                    db.flush()
                    payslip_id = new_payslip.id
                
                # Update monthly processing record
                monthly_processing = db.query(MonthlySalaryProcessing).filter(
                    MonthlySalaryProcessing.month == month,
                    MonthlySalaryProcessing.year == year
                ).first()
                
                if monthly_processing:
                    monthly_processing.successful_payments += 1
                    monthly_processing.total_processed_amount += final_amount
                    monthly_processing.processed_at = datetime.now()
                else:
                    new_monthly_processing = MonthlySalaryProcessing(
                        month=month,
                        year=year,
                        processed_at=datetime.now(),
                        total_employees=1,
                        successful_payments=1,
                        failed_payments=0,
                        total_processed_amount=final_amount,
                        status="completed"
                    )
                    db.add(new_monthly_processing)
                    db.flush()
                
                # Add to processed list
                processed_employees.append(BulkProcessingEmployeeResult(
                    employee_id=employee.id,
                    employee_name=employee.user.full_name if employee.user else "Unknown",
                    success=True,
                    message=f"Salary processed successfully",
                    payslip_id=payslip_id,
                    amount_processed=final_amount,
                    duplicate_prevented=False
                ))
                
                total_amount_processed += final_amount
                
            except Exception as e:
                failed_employees.append(BulkProcessingEmployeeResult(
                    employee_id=employee.id,
                    employee_name=employee.user.full_name if employee.user else "Unknown",
                    success=False,
                    message=f"Error processing: {str(e)}",
                    duplicate_prevented=False
                ))
        
        # Commit all changes
        db.commit()
        
        return BulkSalaryProcessingResponse(
            success=True,
            message=f"Bulk salary processing completed for {month}/{year}",
            total_employees=len(employees),
            processed_count=len(processed_employees),
            failed_count=len(failed_employees),
            skipped_count=len(skipped_employees),
            processed_employees=processed_employees,
            failed_employees=failed_employees,
            skipped_employees=skipped_employees,
            month=month,
            year=year,
            total_amount_processed=total_amount_processed,
            processed_at=datetime.now()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk processing: {str(e)}"
        )

@router.get("/monthly-salary-employee-details", response_model=MonthlySalaryEmployeeDetailsResponse)
def get_monthly_salary_employee_details(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get individual employee salary details for a specific month (admin only).
    
    This endpoint provides detailed information for each employee including:
    - Employee ID
    - Employee Email
    - Amount Paid (null if unpaid)
    - Status (paid or unpaid)
    
    Args:
        month: Month to check (1-12), defaults to current month
        year: Year to check, defaults to current year
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        MonthlySalaryEmployeeDetailsResponse: Individual employee salary details
        
    Raises:
        HTTPException: 403 if not admin, 400 for invalid parameters
    """
    check_admin_access(current_user)
    
    # Use current month/year if not provided
    if month is None:
        month = date.today().month
    if year is None:
        year = date.today().year
    
    # Validate month parameter
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    try:
        # Get all employees with salary information
        employees = db.query(Employee).join(User).join(Salary).all()
        
        employees_data = []
        
        for employee in employees:
            # Check if there's a payslip for this employee in the specified month/year
            payslip = db.query(Payslip).filter(
                Payslip.employee_id == employee.id,
                Payslip.month == month,
                Payslip.year == year
            ).first()
            
            if payslip and payslip.status == "paid":
                # Employee has been paid for this month
                employee_detail = EmployeeSalaryDetail(
                    employee_id=employee.id,
                    email=employee.user.email if employee.user else "",
                    amount_paid=payslip.amount,
                    status="paid"
                )
            else:
                # Employee has not been paid for this month
                employee_detail = EmployeeSalaryDetail(
                    employee_id=employee.id,
                    email=employee.user.email if employee.user else "",
                    amount_paid=None,
                    status="unpaid"
                )
            
            employees_data.append(employee_detail)
        
        return MonthlySalaryEmployeeDetailsResponse(
            success=True,
            month=month,
            year=year,
            employees=employees_data,
            generated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving employee salary details: {str(e)}"
        )
