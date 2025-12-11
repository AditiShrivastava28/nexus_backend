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
        requests = db.query(Request).filter(
            Request.status == "pending"
        ).order_by(Request.created_at.desc()).all()
    else:
        # Manager sees requests from direct reports
        team_ids = [e.id for e in db.query(Employee).filter(
            Employee.manager_id == current_employee.id
        ).all()]
        
        requests = db.query(Request).filter(
            Request.status == "pending",
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


@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    action: ApprovalAction = None,
    current_user: User = Depends(require_manager_or_admin),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Approve a pending request.
    
    Args:
        request_id: Request ID to approve
        action: Optional approval comments
        current_user: Authenticated manager/admin user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if request not found
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    request.status = "approved"
    request.approved_by = current_employee.id
    
    # If it's a leave request, also update the Leave record
    if request.request_type == "leave" and request.details:
        import json
        details = json.loads(request.details)
        leave_id = details.get("leave_id")
        if leave_id:
            leave = db.query(Leave).filter(Leave.id == leave_id).first()
            if leave:
                leave.status = "approved"
                leave.approved_by = current_employee.id
                
                # Update leave balance
                from ..models.leave import LeaveBalance
                from datetime import date as date_type
                balance = db.query(LeaveBalance).filter(
                    LeaveBalance.employee_id == leave.employee_id,
                    LeaveBalance.leave_type == leave.leave_type,
                    LeaveBalance.year == date_type.today().year
                ).first()
                # If no balance exists, create a default one
                if not balance:
                    defaults = {"casual": 12, "sick": 10, "annual": 15, "personal": 5}
                    total = defaults.get(leave.leave_type, 12)
                    balance = LeaveBalance(
                        employee_id=leave.employee_id,
                        leave_type=leave.leave_type,
                        year=date_type.today().year,
                        total_days=total,
                        used_days=0,
                        remaining_days=total
                    )
                    db.add(balance)
                    db.commit()
                    db.refresh(balance)

                balance.used_days += leave.days
                balance.remaining_days = balance.total_days - balance.used_days
    
    db.commit()
    
    return {"message": "Request approved successfully"}


@router.post("/{request_id}/reject")
def reject_request(
    request_id: int,
    action: ApprovalAction = None,
    current_user: User = Depends(require_manager_or_admin),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Reject a pending request.
    
    Args:
        request_id: Request ID to reject
        action: Optional rejection comments
        current_user: Authenticated manager/admin user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if request not found
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    request.status = "rejected"
    request.approved_by = current_employee.id
    
    # If it's a leave request, also update the Leave record
    if request.request_type == "leave" and request.details:
        import json
        details = json.loads(request.details)
        leave_id = details.get("leave_id")
        if leave_id:
            leave = db.query(Leave).filter(Leave.id == leave_id).first()
            if leave:
                leave.status = "rejected"
                leave.approved_by = current_employee.id
    
    db.commit()
    
    return {"message": "Request rejected"}
