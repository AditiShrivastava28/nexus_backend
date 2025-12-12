"""
Inbox/Approvals API routes.

This module provides endpoints for pending tasks and approvals.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.request import Request
from ..models.leave import Leave
from ..schemas.request import TaskResponse, ApprovalAction
from ..utils.deps import get_current_user, get_current_employee, require_manager_or_admin


router = APIRouter(prefix="/inbox", tags=["Inbox"])


@router.get("", response_model=List[TaskResponse])
def get_pending_tasks(
    current_user: User = Depends(require_manager_or_admin),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get pending tasks/approvals for the current user.
    
    Args:
        current_user: Authenticated manager/admin user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[TaskResponse]: List of pending tasks
    """
    # Get pending requests from team members
    if current_user.role == "admin":
        # Admin sees all pending requests
        # Admin sees all requests (approval/status removed)
        requests = db.query(Request).order_by(Request.created_at.desc()).all()
    else:
        # Manager sees requests from direct reports
        team_ids = [e.id for e in db.query(Employee).filter(
            Employee.manager_id == current_employee.id
        ).all()]
        
        requests = db.query(Request).filter(
            Request.requester_id.in_(team_ids)
        ).order_by(Request.created_at.desc()).all()
    
    result = []
    for req in requests:
        # Get requester info
        requester = db.query(Employee).filter(Employee.id == req.requester_id).first()
        requester_name = requester.user.full_name if requester and requester.user else "Unknown"
        avatar = requester.avatar_url if requester else None
        
        result.append(TaskResponse(
            id=req.id,
            type=req.request_type,
            title=req.title or req.request_type.title(),
            requester=requester_name,
            date=req.date,
            avatar=avatar,
            details=req.description
        ))
    
    return result


# Approval endpoints removed: status/approved_by fields were removed from Request model.
