"""
Admin API routes.

This module provides endpoints for employee management by admins.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.asset import Asset
from ..models.document import Document
from ..schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeListItem,
    EmployeeProfile,
    EmployeeStatusUpdate
)
from ..schemas.asset import AssetCreate, AssetResponse
from ..schemas.document import DocumentResponse
from ..services.employee import EmployeeService
from ..services.auth import AuthService
from ..utils.deps import require_admin, get_db
from ..models.leave import LeaveBalance
from ..schemas.leave import LeaveBalanceUpdate


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/employees", response_model=List[EmployeeListItem])
def list_employees(
    search: Optional[str] = Query(None, description="Search query"),
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all employees with optional search.
    
    Args:
        search: Optional search term
        skip: Number of records to skip
        limit: Maximum records to return
        admin: Admin user
        db: Database session
        
    Returns:
        List[EmployeeListItem]: List of employees
    """
    employees = EmployeeService.get_all_employees(db, search, skip, limit)
    
    result = []
    for emp in employees:
        # Get manager name
        manager_name = None
        if emp.manager_id:
            manager = db.query(Employee).filter(Employee.id == emp.manager_id).first()
            if manager and manager.user:
                manager_name = manager.user.full_name
        
        # Get salary
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
            manager=manager_name
        ))
    
    return result


@router.post("/employees", response_model=EmployeeListItem, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new employee.
    
    Args:
        employee_data: New employee data
        admin: Admin user
        db: Database session
        
    Returns:
        EmployeeListItem: Created employee
        
    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    if AuthService.get_user_by_email(db, employee_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    employee = EmployeeService.create_employee(
        db=db,
        email=employee_data.email,
        password=employee_data.password,
        full_name=employee_data.full_name,
        employee_id=employee_data.employee_id,
        role=employee_data.role,
        department=employee_data.department,
        designation=employee_data.designation,
        join_date=employee_data.join_date,
        location=employee_data.location,
        manager_id=employee_data.manager_id
    )
    
    return EmployeeListItem(
        id=employee.id,
        name=employee.user.full_name,
        role=employee.designation,
        department=employee.department,
        salary=None,
        email=employee.user.email,
        status=employee.status,
        avatar=employee.avatar_url,
        joinDate=employee.join_date,
        location=employee.location,
        manager=None
    )


@router.get("/employees/{employee_id}", response_model=EmployeeProfile)
def get_employee(
    employee_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get employee details.
    
    Args:
        employee_id: Employee ID
        admin: Admin user
        db: Database session
        
    Returns:
        EmployeeProfile: Employee details
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get manager name
    manager_name = None
    if employee.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.manager_id).first()
        if manager and manager.user:
            manager_name = manager.user.full_name
    
    return EmployeeProfile(
        id=employee.id,
        employeeId=employee.employee_id,
        name=employee.user.full_name if employee.user else "Unknown",
        email=employee.user.email if employee.user else "",
        department=employee.department,
        designation=employee.designation,
        joinDate=employee.join_date,
        location=employee.location,
        manager=manager_name,
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
def update_employee(
    employee_id: int,
    update_data: EmployeeUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update employee information.
    
    Args:
        employee_id: Employee ID
        update_data: Fields to update
        admin: Admin user
        db: Database session
        
    Returns:
        EmployeeProfile: Updated employee
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if "full_name" in update_dict and employee.user:
        employee.user.full_name = update_dict.pop("full_name")
    
    for key, value in update_dict.items():
        if hasattr(employee, key):
            setattr(employee, key, value)
    
    db.commit()
    db.refresh(employee)
    
    return get_employee(employee_id, admin, db)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an employee.
    
    Args:
        employee_id: Employee ID to delete
        admin: Admin user
        db: Database session
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    EmployeeService.delete_employee(db, employee)


@router.post("/employees/{employee_id}/reset-password")
def reset_employee_password(
    employee_id: int,
    new_password: str = "Welcome@123",
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Reset an employee's password.
    
    Args:
        employee_id: Employee ID
        new_password: New password (default: Welcome@123)
        admin: Admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee or not employee.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    AuthService.reset_password(db, employee.user, new_password)
    
    return {"message": "Password reset successfully"}


@router.put("/employees/{employee_id}/status")
def update_employee_status(
    employee_id: int,
    status_data: EmployeeStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update employee status.
    
    Args:
        employee_id: Employee ID
        status_data: New status
        admin: Admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    employee.status = status_data.status
    
    # If deactivated, also deactivate user
    if status_data.status in ["terminated", "inactive"]:
        if employee.user:
            employee.user.is_active = False
    elif status_data.status == "active":
        if employee.user:
            employee.user.is_active = True
    
    db.commit()
    
    return {"message": f"Employee status updated to {status_data.status}"}


@router.get("/employees/{employee_id}/assets", response_model=List[AssetResponse])
def get_employee_assets(
    employee_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get assets assigned to an employee.
    
    Args:
        employee_id: Employee ID
        admin: Admin user
        db: Database session
        
    Returns:
        List[AssetResponse]: List of assets
    """
    assets = db.query(Asset).filter(Asset.employee_id == employee_id).all()
    
    return [AssetResponse(
        id=asset.id,
        name=asset.name,
        type=asset.asset_type,
        serial=asset.serial_number,
        assignedDate=asset.assigned_date
    ) for asset in assets]


@router.get("/employees/{employee_id}/leave-balance/{year}")
def get_leave_balance(
    employee_id: int,
    year: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get leave balance for an employee for a given year (admin only)."""
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year
    ).first()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave balance not found")
    return {
        "total_leaves": 12,
        "leaves_left": int(balance.remaining_days),
        "used_leaves": int(balance.used_days)
    }



@router.put("/employees/{employee_id}/leave-balance/{year}")
def update_leave_balance(
    employee_id: int,
    year: int,
    payload: LeaveBalanceUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update total allocated leave days for an employee for a given year (admin only)."""
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year
    ).first()
    # Business rule: total_days must remain 12. Reject other values.
    if payload.total_days != 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="total_days must be 12")


    if not balance:
        # create new balance record with default 12
        balance = LeaveBalance(
            employee_id=employee_id,
            year=year,
            total_days=12,
            used_days=0,
            remaining_days=12,
            leave_type="paid"  # Default to paid leave balance
        )
        db.add(balance)
    else:
        # Keep total at 12 and recompute remaining
        balance.total_days = 12
        balance.remaining_days = max(12 - balance.used_days, 0)

    db.commit()
    db.refresh(balance)

    return {"message": "Leave allocation updated", "total_days": int(balance.total_days), "remaining_days": int(balance.remaining_days)}


@router.post("/employees/{employee_id}/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def assign_asset(
    employee_id: int,
    asset_data: AssetCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Assign an asset to an employee.
    
    Args:
        employee_id: Employee ID
        asset_data: Asset details
        admin: Admin user
        db: Database session
        
    Returns:
        AssetResponse: Assigned asset
        
    Raises:
        HTTPException: 404 if employee not found
    """
    employee = EmployeeService.get_employee_by_id(db, employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    asset = Asset(
        employee_id=employee_id,
        name=asset_data.name,
        asset_type=asset_data.asset_type,
        serial_number=asset_data.serial_number,
        assigned_date=date.today(),
        status="assigned"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(
        id=asset.id,
        name=asset.name,
        type=asset.asset_type,
        serial=asset.serial_number,
        assignedDate=asset.assigned_date
    )


@router.delete("/employees/{employee_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_asset(
    employee_id: int,
    asset_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Revoke an asset from an employee.
    
    Args:
        employee_id: Employee ID
        asset_id: Asset ID to revoke
        admin: Admin user
        db: Database session
        
    Raises:
        HTTPException: 404 if asset not found
    """
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.employee_id == employee_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    db.delete(asset)
    db.commit()


@router.get("/employees/{employee_id}/documents", response_model=List[DocumentResponse])
def get_employee_documents(
    employee_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get documents for an employee.
    
    Args:
        employee_id: Employee ID
        admin: Admin user
        db: Database session
        
    Returns:
        List[DocumentResponse]: List of documents
    """
    documents = db.query(Document).filter(
        Document.employee_id == employee_id
    ).all()
    
    return [DocumentResponse(
        id=doc.id,
        name=doc.name,
        status=doc.status,
        date=doc.verified_date or (doc.created_at.date() if doc.created_at else None)
    ) for doc in documents]


@router.post("/employees/{employee_id}/documents/{doc_id}/verify")
def verify_document(
    employee_id: int,
    doc_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Verify an employee's document.
    
    Args:
        employee_id: Employee ID
        doc_id: Document ID to verify
        admin: Admin user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if document not found
    """
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.employee_id == employee_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get admin's employee profile
    admin_employee = db.query(Employee).filter(Employee.user_id == admin.id).first()
    
    document.status = "verified"
    document.verified_by = admin_employee.id if admin_employee else None
    document.verified_date = date.today()
    
    db.commit()
    
    return {"message": "Document verified successfully"}
