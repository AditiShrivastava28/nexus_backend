"""
Admin API routes.

This module provides endpoints for employee management by admins.
"""


from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

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



from ..models.leave import LeaveBalance, CorporateLeave
from ..schemas.leave import LeaveBalanceUpdate, CorporateLeaveCreate, CorporateLeaveResponse, CorporateLeaveUpdate
from ..services.corporate_leave import CorporateLeaveAIService
from ..services.holiday_scanner import HolidayScannerService


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


# Corporate Leave Management Endpoints

@router.post("/corporate-leaves/generate")
def generate_corporate_leaves(
    year: int,
    region: str = "general",
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Generate AI-based corporate leaves for a given year.
    
    Args:
        year: Year for which to generate corporate leaves
        region: Region for specific holidays (general, india, uk)
        admin: Admin user
        db: Database session
        
    Returns:
        dict: Generated leaves count and message
    """
    # Generate corporate leaves using AI service
    generated_leaves = CorporateLeaveAIService.generate_corporate_leaves(year, region)
    
    created_count = 0
    skipped_count = 0
    
    for leave_data in generated_leaves:
        # Check if a corporate leave with same date already exists
        existing_leave = db.query(CorporateLeave).filter(
            CorporateLeave.date == leave_data["date"]
        ).first()
        
        if not existing_leave:
            # Create new corporate leave
            corporate_leave = CorporateLeave(
                name=leave_data["name"],
                date=leave_data["date"],
                leave_type=leave_data["type"],
                is_recurring=str(leave_data["is_recurring"]).lower(),
                created_by=admin.id
            )
            db.add(corporate_leave)
            created_count += 1
        else:
            skipped_count += 1
    
    db.commit()
    
    return {
        "message": f"Corporate leaves generated successfully",
        "year": year,
        "region": region,
        "created": created_count,
        "skipped": skipped_count,
        "total_generated": len(generated_leaves)
    }


@router.get("/corporate-leaves", response_model=List[CorporateLeaveResponse])
def get_corporate_leaves(
    year: Optional[int] = Query(None, description="Filter by year"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all corporate leaves, optionally filtered by year.
    
    Args:
        year: Optional year filter
        admin: Admin user
        db: Database session
        
    Returns:
        List[CorporateLeaveResponse]: List of corporate leaves
    """
    query = db.query(CorporateLeave)
    
    if year:
        query = query.filter(CorporateLeave.date >= date(year, 1, 1))
        query = query.filter(CorporateLeave.date <= date(year, 12, 31))
    
    corporate_leaves = query.order_by(CorporateLeave.date).all()
    
    result = []
    for leave in corporate_leaves:
        result.append(CorporateLeaveResponse(
            id=leave.id,
            name=leave.name,
            date=leave.date,
            leave_type=leave.leave_type,
            is_recurring=leave.is_recurring == "true",
            created_at=leave.created_at.date() if leave.created_at else None
        ))
    
    return result


@router.post("/corporate-leaves", response_model=CorporateLeaveResponse, status_code=status.HTTP_201_CREATED)
def create_corporate_leave(
    leave_data: CorporateLeaveCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new corporate leave.
    
    Args:
        leave_data: Corporate leave data
        admin: Admin user
        db: Database session
        
    Returns:
        CorporateLeaveResponse: Created corporate leave
        
    Raises:
        HTTPException: 400 if leave already exists on the same date
    """
    # Check if a corporate leave with same date already exists
    existing_leave = db.query(CorporateLeave).filter(
        CorporateLeave.date == leave_data.date
    ).first()
    
    if existing_leave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corporate leave already exists on {leave_data.date}"
        )
    
    corporate_leave = CorporateLeave(
        name=leave_data.name,
        date=leave_data.date,
        leave_type=leave_data.leave_type,
        is_recurring=str(leave_data.is_recurring).lower(),
        created_by=admin.id
    )
    
    db.add(corporate_leave)
    db.commit()
    db.refresh(corporate_leave)
    
    return CorporateLeaveResponse(
        id=corporate_leave.id,
        name=corporate_leave.name,
        date=corporate_leave.date,
        leave_type=corporate_leave.leave_type,
        is_recurring=corporate_leave.is_recurring == "true",
        created_at=corporate_leave.created_at.date() if corporate_leave.created_at else None
    )


@router.put("/corporate-leaves/{leave_id}", response_model=CorporateLeaveResponse)
def update_corporate_leave(
    leave_id: int,
    update_data: CorporateLeaveUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a corporate leave.
    
    Args:
        leave_id: Corporate leave ID
        update_data: Fields to update
        admin: Admin user
        db: Database session
        
    Returns:
        CorporateLeaveResponse: Updated corporate leave
        
    Raises:
        HTTPException: 404 if corporate leave not found
    """
    corporate_leave = db.query(CorporateLeave).filter(CorporateLeave.id == leave_id).first()
    
    if not corporate_leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate leave not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if key == "is_recurring" and value is not None:
            value = str(value).lower()
        if hasattr(corporate_leave, key):
            setattr(corporate_leave, key, value)
    
    db.commit()
    db.refresh(corporate_leave)
    
    return CorporateLeaveResponse(
        id=corporate_leave.id,
        name=corporate_leave.name,
        date=corporate_leave.date,
        leave_type=corporate_leave.leave_type,
        is_recurring=corporate_leave.is_recurring == "true",
        created_at=corporate_leave.created_at.date() if corporate_leave.created_at else None
    )


@router.delete("/corporate-leaves/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corporate_leave(
    leave_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a corporate leave.
    
    Args:
        leave_id: Corporate leave ID to delete
        admin: Admin user
        db: Database session
        
    Raises:
        HTTPException: 404 if corporate leave not found
    """
    corporate_leave = db.query(CorporateLeave).filter(CorporateLeave.id == leave_id).first()
    
    if not corporate_leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corporate leave not found"
        )
    

    db.delete(corporate_leave)
    db.commit()


# Dynamic Holiday Scanner Endpoints

@router.post("/holidays/scan-current")
def scan_current_year_holidays(
    regions: List[str] = Query(["general", "india", "uk"], description="Regions to include"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Scan and update holidays for current year only.
    
    Args:
        regions: List of regions to include in scanning
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with scan results
    """
    result = HolidayScannerService.scan_current_year_holidays(db, admin, regions)
    return result


@router.post("/holidays/scan-range")
def scan_holidays_in_range(
    start_year: int = Query(..., description="Start year for scanning"),
    end_year: int = Query(..., description="End year for scanning"),
    regions: List[str] = Query(["general", "india", "uk"], description="Regions to include"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Scan and update holidays for specified year range.
    
    Args:
        start_year: Starting year for scanning
        end_year: Ending year for scanning
        regions: List of regions to include in scanning
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with scan results
    """
    if start_year > end_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start year must be less than or equal to end year"
        )
    
    result = HolidayScannerService.scan_and_update_holidays(
        db, admin, regions, (start_year, end_year)
    )
    return result


@router.post("/holidays/scan-future")
def scan_future_years_holidays(
    years_ahead: int = Query(2, description="Number of years ahead to scan"),
    regions: List[str] = Query(["general", "india", "uk"], description="Regions to include"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Scan and update holidays for current + future years.
    
    Args:
        years_ahead: Number of years ahead to scan
        regions: List of regions to include in scanning
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with scan results
    """
    if years_ahead < 1 or years_ahead > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Years ahead must be between 1 and 10"
        )
    
    result = HolidayScannerService.scan_future_years_holidays(db, admin, regions, years_ahead)
    return result


@router.post("/holidays/cleanup")
def cleanup_old_holidays(
    keep_years_back: int = Query(1, description="Number of years back to keep"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Clean up holidays from years before the specified threshold.
    
    Args:
        keep_years_back: Number of years back to keep
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with cleanup results
    """
    if keep_years_back < 0 or keep_years_back > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keep years back must be between 0 and 10"
        )
    
    result = HolidayScannerService.cleanup_old_holidays(db, keep_years_back)
    return result


@router.get("/holidays/statistics")
def get_holiday_statistics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get statistics about current holidays in the database.
    
    Args:
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with holiday statistics
    """
    result = HolidayScannerService.get_holiday_statistics(db)
    return result


@router.get("/holidays/conflicts")
def detect_holiday_conflicts(
    year: Optional[int] = Query(None, description="Year to filter conflicts (optional)"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Detect potential holiday conflicts in the database.
    
    Args:
        year: Optional year to filter conflicts
        admin: Admin user
        db: Database session
        
    Returns:
        List of potential conflicts
    """
    result = HolidayScannerService.detect_holiday_conflicts(db, year)
    return {
        "conflicts_found": len(result),
        "conflicts": result
    }


@router.post("/holidays/auto-update")
def auto_update_holidays(
    regions: List[str] = Query(["general", "india", "uk"], description="Regions to include"),
    years_ahead: int = Query(2, description="Number of years ahead to maintain"),
    keep_years_back: int = Query(1, description="Number of years back to keep"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Automatically update holidays: clean old ones and scan current + future years.
    
    Args:
        regions: List of regions to include
        years_ahead: Number of years ahead to maintain
        keep_years_back: Number of years back to keep
        admin: Admin user
        db: Database session
        
    Returns:
        Dictionary with complete update results
    """
    current_year = datetime.now().year
    
    # Clean up old holidays first
    cleanup_result = HolidayScannerService.cleanup_old_holidays(db, keep_years_back)
    
    # Scan and update current + future years
    scan_result = HolidayScannerService.scan_future_years_holidays(
        db, admin, regions, years_ahead
    )
    
    return {
        "message": "Auto-update completed successfully",
        "current_year": current_year,
        "regions": regions,
        "years_ahead": years_ahead,
        "keep_years_back": keep_years_back,
        "cleanup": cleanup_result,
        "scan": scan_result,
        "summary": {
            "total_deleted": cleanup_result["deleted_count"],
            "total_created": scan_result["created"],
            "total_skipped": scan_result["skipped"],
            "years_processed": scan_result["years_processed"]
        }
    }
