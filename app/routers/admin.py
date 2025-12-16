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

from ..schemas.employee import (
    EmployeeCreate, 
    EmployeeUpdate, 
    EmployeeListItem, 
    EmployeeProfile,
    EmployeeStatusUpdate,
    ManagerInfo
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
    valid_statuses = ["active", "on_leave", "terminated", "suspended"]
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
