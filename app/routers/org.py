"""
Organization API routes.

This module provides endpoints for organization documents, stats, and employee search.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta

from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.document import Document
from ..schemas.document import CompanyDocumentResponse
from ..schemas.employee import EmployeeListItem
from ..utils.deps import get_current_user


router = APIRouter(prefix="/org", tags=["Organization"])


@router.get("/documents", response_model=List[CompanyDocumentResponse])
def get_company_documents(
    db: Session = Depends(get_db)
):
    """
    Get company policy documents.
    
    Args:
        db: Database session
        
    Returns:
        List[CompanyDocumentResponse]: List of company documents
    """
    documents = db.query(Document).filter(
        Document.is_company_doc == True
    ).all()
    
    return [CompanyDocumentResponse(
        id=doc.id,
        name=doc.name,
        doc_type=doc.doc_type,
        file_url=doc.file_url
    ) for doc in documents]


@router.get("/stats")
def get_org_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization statistics.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Organization stats
    """

    # Total employees
    total_employees = db.query(Employee).filter(
        Employee.status.in_(["active", "full_time"])
    ).count()
    
    # New joiners (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    new_joiners = db.query(Employee).filter(
        Employee.join_date >= thirty_days_ago
    ).count()
    
    # Open roles (placeholder - would need a roles/jobs table)
    open_roles = 5  # Placeholder
    

    # Department breakdown
    department_stats = db.query(
        Employee.department,
        func.count(Employee.id)
    ).filter(
        Employee.status.in_(["active", "full_time"])
    ).group_by(Employee.department).all()
    
    departments = [
        {"name": dept or "Unassigned", "count": count}
        for dept, count in department_stats
    ]
    
    return {
        "totalEmployees": total_employees,
        "newJoiners": new_joiners,
        "openRoles": open_roles,
        "departments": departments
    }


@router.get("/employees/search", response_model=List[EmployeeListItem])
def search_employees(
    q: Optional[str] = Query(None, description="Search query"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Search employees.
    
    Args:
        q: Search query (name, email, employee ID)
        department: Filter by department
        db: Database session
        
    Returns:
        List[EmployeeListItem]: List of matching employees
    """
    query = db.query(Employee).join(User)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (Employee.employee_id.ilike(search_term))
        )
    
    if department:
        query = query.filter(Employee.department == department)
    
    employees = query.limit(50).all()
    
    result = []
    for emp in employees:
        # Get manager name
        manager_name = None
        if emp.manager_id:
            manager = db.query(Employee).filter(Employee.id == emp.manager_id).first()
            if manager and manager.user:
                manager_name = manager.user.full_name
        
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
            manager=manager_name
        ))
    
    return result
