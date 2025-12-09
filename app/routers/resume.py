"""
Resume Builder API routes.

This module provides endpoints for resume data storage and retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json

from ..database import get_db
from ..models.employee import Employee
from ..schemas.request import ResumeData
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/resume", tags=["Resume"])

# In-memory storage for resume data (would use a proper table in production)
_resume_storage = {}


@router.get("", response_model=ResumeData)
def get_resume(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the current user's resume data.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        ResumeData: User's resume data
    """
    # Check if we have stored resume data
    if current_employee.id in _resume_storage:
        return ResumeData(**_resume_storage[current_employee.id])
    
    # Build resume data from employee profile
    personal = {
        "name": current_employee.user.full_name if current_employee.user else "",
        "email": current_employee.user.email if current_employee.user else "",
        "phone": current_employee.mobile or "",
        "address": current_employee.address or "",
        "title": current_employee.designation or ""
    }
    
    # Get job history
    experience = []
    for job in current_employee.jobs:
        experience.append({
            "company": job.company,
            "title": job.designation,
            "startDate": str(job.start_date) if job.start_date else "",
            "endDate": str(job.end_date) if job.end_date else "",
            "description": job.description or ""
        })
    
    return ResumeData(
        personal=personal,
        experience=experience,
        education=[],
        skills=[],
        projects=[]
    )


@router.put("", response_model=ResumeData)
def save_resume(
    resume_data: ResumeData,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Save the current user's resume data.
    
    Args:
        resume_data: Resume data to save
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        ResumeData: Saved resume data
    """
    # Store resume data
    _resume_storage[current_employee.id] = resume_data.model_dump()
    
    return resume_data
