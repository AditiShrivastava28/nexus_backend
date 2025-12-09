"""
Attendance API routes.

This module provides endpoints for clock-in/out and break management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from ..database import get_db
from ..models.employee import Employee
from ..models.attendance import Attendance, Break
from ..schemas.attendance import (
    AttendanceResponse,
    ClockInResponse,
    ClockOutResponse,
    BreakStartResponse,
    BreakEndResponse,
    BreakResponse
)
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/attendance", tags=["Attendance"])


def calculate_hours(clock_in: datetime, clock_out: datetime) -> str:
    """
    Calculate total working hours between clock-in and clock-out.
    
    Args:
        clock_in: Clock-in timestamp
        clock_out: Clock-out timestamp
        
    Returns:
        str: Formatted hours string (e.g., "8h 30m")
    """
    if not clock_in or not clock_out:
        return "0h 0m"
    
    diff = clock_out - clock_in
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"


@router.get("/today", response_model=AttendanceResponse)
def get_today_attendance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get today's attendance record for the current user.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        AttendanceResponse: Today's attendance data
    """
    today = date.today()
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance:
        # Return empty attendance
        return AttendanceResponse(
            id=0,
            date=today,
            clock_in=None,
            clock_out=None,
            status=None,
            total_hours=None,
            breaks=[],
            is_on_break=False
        )
    
    # Check if currently on break
    is_on_break = any(
        b.end_time is None for b in attendance.breaks
    )
    
    breaks = [BreakResponse(
        id=b.id,
        start_time=b.start_time,
        end_time=b.end_time,
        duration_minutes=b.duration_minutes
    ) for b in attendance.breaks]
    
    return AttendanceResponse(
        id=attendance.id,
        date=attendance.date,
        clock_in=attendance.clock_in,
        clock_out=attendance.clock_out,
        status=attendance.status,
        total_hours=attendance.total_hours,
        breaks=breaks,
        is_on_break=is_on_break
    )


@router.post("/clock-in", response_model=ClockInResponse)
def clock_in(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Clock in for the day.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        ClockInResponse: Clock-in confirmation
        
    Raises:
        HTTPException: 400 if already clocked in
    """
    today = date.today()
    now = datetime.now()
    
    # Check if already clocked in today
    existing = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()
    
    if existing and existing.clock_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked in for today"
        )
    
    attendance = Attendance(
        employee_id=current_employee.id,
        date=today,
        clock_in=now,
        status="present"
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return ClockInResponse(
        message="Clocked in successfully",
        clock_in=now,
        attendance_id=attendance.id
    )


@router.post("/clock-out", response_model=ClockOutResponse)
def clock_out(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Clock out for the day.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        ClockOutResponse: Clock-out confirmation with total hours
        
    Raises:
        HTTPException: 400 if not clocked in or already clocked out
    """
    today = date.today()
    now = datetime.now()
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance or not attendance.clock_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not clocked in yet"
        )
    
    if attendance.clock_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked out for today"
        )
    
    # End any active break
    active_break = db.query(Break).filter(
        Break.attendance_id == attendance.id,
        Break.end_time == None
    ).first()
    
    if active_break:
        active_break.end_time = now
        diff = now - active_break.start_time
        active_break.duration_minutes = int(diff.total_seconds() // 60)
    
    attendance.clock_out = now
    attendance.total_hours = calculate_hours(attendance.clock_in, now)
    
    db.commit()
    db.refresh(attendance)
    
    return ClockOutResponse(
        message="Clocked out successfully",
        clock_out=now,
        total_hours=attendance.total_hours
    )


@router.post("/break/start", response_model=BreakStartResponse)
def start_break(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Start a break.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        BreakStartResponse: Break start confirmation
        
    Raises:
        HTTPException: 400 if not clocked in or already on break
    """
    today = date.today()
    now = datetime.now()
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance or not attendance.clock_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not clocked in yet"
        )
    
    if attendance.clock_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already clocked out for today"
        )
    
    # Check if already on break
    active_break = db.query(Break).filter(
        Break.attendance_id == attendance.id,
        Break.end_time == None
    ).first()
    
    if active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already on a break"
        )
    
    new_break = Break(
        attendance_id=attendance.id,
        start_time=now
    )
    db.add(new_break)
    db.commit()
    
    return BreakStartResponse(
        message="Break started",
        break_start=now
    )


@router.post("/break/end", response_model=BreakEndResponse)
def end_break(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    End the current break.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        BreakEndResponse: Break end confirmation with duration
        
    Raises:
        HTTPException: 400 if not on a break
    """
    today = date.today()
    now = datetime.now()
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No attendance record for today"
        )
    
    active_break = db.query(Break).filter(
        Break.attendance_id == attendance.id,
        Break.end_time == None
    ).first()
    
    if not active_break:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not on a break"
        )
    
    active_break.end_time = now
    diff = now - active_break.start_time
    active_break.duration_minutes = int(diff.total_seconds() // 60)
    
    db.commit()
    db.refresh(active_break)
    
    return BreakEndResponse(
        message="Break ended",
        break_end=now,
        duration_minutes=active_break.duration_minutes
    )
