"""
Team management API routes.

This module provides endpoints for team members and messaging.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db

from ..models.user import User
from ..models.employee import Employee
from ..models.message import Message
from ..schemas.employee import TeamMemberResponse, TeammateResponse
from ..schemas.message import MessageCreate, MessageResponse
from ..utils.deps import get_current_user, get_current_employee



router = APIRouter(prefix="/team", tags=["Team"])


@router.get("", response_model=List[TeamMemberResponse])
def get_team_members(
    current_user: User = Depends(get_current_user),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get team members for the current user.
    
    Args:
        current_user: Authenticated user
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[TeamMemberResponse]: List of team members
    """
    # If manager, get direct reports
    # Otherwise, get colleagues (same manager or department)
    team = []
    
    if current_user.role in ["admin", "manager"]:
        # Get direct reports
        direct_reports = db.query(Employee).filter(
            Employee.manager_id == current_employee.id
        ).all()
        team.extend(direct_reports)
    
    # Get colleagues in same department
    if current_employee.department:
        colleagues = db.query(Employee).filter(
            Employee.department == current_employee.department,
            Employee.id != current_employee.id
        ).limit(20).all()
        
        # Add colleagues not already in team
        existing_ids = {e.id for e in team}
        for colleague in colleagues:
            if colleague.id not in existing_ids:
                team.append(colleague)
    

    return [TeamMemberResponse(
        id=emp.id,
        name=emp.user.full_name if emp.user else "Unknown",
        role=emp.designation,
        status=emp.status,
        location=emp.location,
        img=emp.avatar_url,
        isOnline=False  # Would need real-time status tracking
    ) for emp in team]


@router.get("/members", response_model=List[TeammateResponse])
def get_all_teammates_details(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get detailed list of all registered users/employees for the teammates page.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[TeammateResponse]: List of all employees with details
    """
    # Fetch all employees joined with users to ensure they are registered
    # You might want to filter by status="active" depending on requirements
    employees = db.query(Employee).join(User).filter(Employee.status == "active").all()
    
    result = []
    for emp in employees:
        result.append(TeammateResponse(
            id=emp.id,
            name=emp.user.full_name,
            designation=emp.designation,
            department=emp.department,
            join_date=emp.join_date,
            status=emp.status,
            location=emp.location,
            avatar_url=emp.avatar_url,
            email=emp.user.email, # Use login email or personal_email if preferred
            mobile=emp.mobile
        ))
        
    return result


@router.get("/{member_id}/messages", response_model=List[MessageResponse])

def get_messages(
    member_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get messages between current user and a team member.
    
    Args:
        member_id: Team member's employee ID
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[MessageResponse]: List of messages
    """
    messages = db.query(Message).filter(
        ((Message.sender_id == current_employee.id) & (Message.receiver_id == member_id)) |
        ((Message.sender_id == member_id) & (Message.receiver_id == current_employee.id))
    ).order_by(Message.sent_at.asc()).all()
    
    result = []
    for msg in messages:
        # Get sender name
        sender = db.query(Employee).filter(Employee.id == msg.sender_id).first()
        sender_name = sender.user.full_name if sender and sender.user else "Unknown"
        
        result.append(MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            content=msg.content,
            is_read=msg.is_read,
            sent_at=msg.sent_at,
            sender_name=sender_name
        ))
    
    # Mark messages as read
    db.query(Message).filter(
        Message.sender_id == member_id,
        Message.receiver_id == current_employee.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return result


@router.post("/{member_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    member_id: int,
    message_data: MessageCreate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Send a message to a team member.
    
    Args:
        member_id: Receiver's employee ID
        message_data: Message content
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        MessageResponse: Sent message
        
    Raises:
        HTTPException: 404 if receiver not found
    """
    # Verify receiver exists
    receiver = db.query(Employee).filter(Employee.id == member_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    message = Message(
        sender_id=current_employee.id,
        receiver_id=member_id,
        content=message_data.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_read=message.is_read,
        sent_at=message.sent_at,
        sender_name=current_employee.user.full_name if current_employee.user else "Unknown"
    )
