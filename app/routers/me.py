"""
User profile (Me) API routes.

This module provides endpoints for the current user's profile,
job history, documents, and assets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..models.employee import Employee, EmployeeJob
from ..models.document import Document
from ..models.asset import Asset
from ..schemas.employee import (
    EmployeeProfile, 
    EmployeeProfileUpdate, 
    EmployeeJobCreate, 
    EmployeeJobResponse
)
from ..schemas.asset import AssetResponse
from ..schemas.document import DocumentResponse
from ..utils.deps import get_current_user, get_current_employee


router = APIRouter(prefix="/me", tags=["My Profile"])


@router.get("", response_model=EmployeeProfile)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile.
    
    Args:
        current_user: Authenticated user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        EmployeeProfile: Current user's profile data
    """
    # Get manager name if exists
    manager_name = None
    if current_employee.manager_id:
        manager = db.query(Employee).filter(
            Employee.id == current_employee.manager_id
        ).first()
        if manager:
            manager_name = manager.user.full_name
    
    return EmployeeProfile(
        id=current_employee.id,
        employeeId=current_employee.employee_id,
        name=current_user.full_name,
        email=current_user.email,
        department=current_employee.department,
        designation=current_employee.designation,
        joinDate=current_employee.join_date,
        location=current_employee.location,
        manager=manager_name,
        dob=current_employee.dob,
        gender=current_employee.gender,
        marital_status=current_employee.marital_status,
        blood_group=current_employee.blood_group,
        address=current_employee.address,
        personal_email=current_employee.personal_email,
        mobile=current_employee.mobile,
        avatar_url=current_employee.avatar_url,
        status=current_employee.status
    )


@router.put("", response_model=EmployeeProfile)
def update_my_profile(
    profile_data: EmployeeProfileUpdate,
    current_user: User = Depends(get_current_user),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    
    Args:
        profile_data: Profile fields to update
        current_user: Authenticated user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        EmployeeProfile: Updated profile data
    """
    # Update allowed fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(current_employee, key):
            setattr(current_employee, key, value)
    
    db.commit()
    db.refresh(current_employee)
    
    return get_my_profile(current_user, current_employee, db)


@router.get("/jobs", response_model=List[EmployeeJobResponse])
def get_my_jobs(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the current user's job history.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[EmployeeJobResponse]: List of past jobs
    """
    jobs = db.query(EmployeeJob).filter(
        EmployeeJob.employee_id == current_employee.id
    ).order_by(EmployeeJob.start_date.desc()).all()
    
    return [EmployeeJobResponse(
        id=job.id,
        company=job.company,
        designation=job.designation,
        start_date=job.start_date,
        end_date=job.end_date,
        description=job.description
    ) for job in jobs]


@router.post("/jobs", response_model=EmployeeJobResponse, status_code=status.HTTP_201_CREATED)
def add_job(
    job_data: EmployeeJobCreate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Add a job entry to employment history.
    
    Args:
        job_data: Job entry data
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        EmployeeJobResponse: Created job entry
    """
    job = EmployeeJob(
        employee_id=current_employee.id,
        company=job_data.company,
        designation=job_data.designation,
        start_date=job_data.start_date,
        end_date=job_data.end_date,
        description=job_data.description
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return EmployeeJobResponse(
        id=job.id,
        company=job.company,
        designation=job.designation,
        start_date=job.start_date,
        end_date=job.end_date,
        description=job.description
    )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Delete a job entry from employment history.
    
    Args:
        job_id: Job entry ID to delete
        current_employee: User's employee profile
        db: Database session
        
    Raises:
        HTTPException: 404 if job not found
    """
    job = db.query(EmployeeJob).filter(
        EmployeeJob.id == job_id,
        EmployeeJob.employee_id == current_employee.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job entry not found"
        )
    
    db.delete(job)
    db.commit()


@router.get("/documents", response_model=List[DocumentResponse])
def get_my_documents(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the current user's documents.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[DocumentResponse]: List of user's documents
    """
    documents = db.query(Document).filter(
        Document.employee_id == current_employee.id
    ).all()
    
    return [DocumentResponse(
        id=doc.id,
        name=doc.name,
        status=doc.status,
        date=doc.verified_date or doc.created_at.date() if doc.created_at else None
    ) for doc in documents]


@router.post("/documents/{doc_id}/upload", response_model=DocumentResponse)
def upload_document(
    doc_id: int,
    file_url: str,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Upload/update a document.
    
    Args:
        doc_id: Document ID to update
        file_url: URL of uploaded file
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        DocumentResponse: Updated document
        
    Raises:
        HTTPException: 404 if document not found
    """
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.employee_id == current_employee.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document.file_url = file_url
    document.status = "pending"  # Reset to pending for re-verification
    db.commit()
    db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        name=document.name,
        status=document.status,
        date=document.verified_date
    )


@router.get("/assets", response_model=List[AssetResponse])
def get_my_assets(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get assets assigned to the current user.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[AssetResponse]: List of assigned assets
    """
    assets = db.query(Asset).filter(
        Asset.employee_id == current_employee.id
    ).all()
    
    return [AssetResponse(
        id=asset.id,
        name=asset.name,
        type=asset.asset_type,
        serial=asset.serial_number,
        assignedDate=asset.assigned_date
    ) for asset in assets]
