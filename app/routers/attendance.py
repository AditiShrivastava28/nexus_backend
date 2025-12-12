"""
Attendance API routes.

This module provides endpoints for clock-in/out and break management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, timezone
from typing import List

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



def calculate_hours(clock_in: datetime, clock_out: datetime, breaks: List[Break] = None) -> str:
    """
    Calculate total working hours between clock-in and clock-out, subtracting break time.
    
    Args:
        clock_in: Clock-in timestamp
        clock_out: Clock-out timestamp
        breaks: List of Break objects to subtract from total time
        
    Returns:
        str: Formatted hours string (e.g., "8h 30m")
    """
    if not clock_in or not clock_out:
        return "0h 0m"

    # Normalize datetimes to UTC-naive for safe subtraction when some
    # datetimes may be timezone-aware and others naive.
    def _normalize(dt: datetime) -> datetime:
        if dt is None:
            return dt
        if dt.tzinfo is None:
            return dt
        # convert to UTC then drop tzinfo
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    ci = _normalize(clock_in)
    co = _normalize(clock_out)

    diff = co - ci
    

    # Calculate total break time in minutes
    total_break_minutes = 0
    if breaks:
        for break_obj in breaks:
            if break_obj.duration_minutes:
                total_break_minutes += break_obj.duration_minutes
    
    # Convert total work time to minutes, subtract break time
    total_minutes = int(diff.total_seconds() // 60)
    net_minutes = total_minutes - total_break_minutes
    
    if net_minutes < 0:
        net_minutes = 0  # In case of data inconsistency
    
    hours = net_minutes // 60
    minutes = net_minutes % 60
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
    
    # Calculate total hours if clocked out and total_hours is not set or is "0h 0m"
    total_hours = attendance.total_hours
    if attendance.clock_in and attendance.clock_out and (not total_hours or total_hours == "0h 0m"):
        total_hours = calculate_hours(attendance.clock_in, attendance.clock_out, attendance.breaks)
        # Update the database
        attendance.total_hours = total_hours
        db.commit()
    
    return AttendanceResponse(
        id=attendance.id,
        date=attendance.date,
        clock_in=attendance.clock_in,
        clock_out=attendance.clock_out,
        status=attendance.status,
        total_hours=total_hours,
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
    now = datetime.now(timezone.utc)

    # Check if an attendance row already exists for today
    existing = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date == today
    ).first()

    if existing:
        if existing.clock_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already clocked in for today"
            )
        # update existing attendance row instead of creating duplicate
        existing.clock_in = now
        existing.status = "present"
        db.commit()
        db.refresh(existing)

        return ClockInResponse(
            message="Clocked in successfully",
            clock_in=now,
            attendance_id=existing.id
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
    now = datetime.now(timezone.utc)
    
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
        # normalize before subtracting
        try:
            diff = (active_break.end_time.astimezone(timezone.utc).replace(tzinfo=None)
                    - active_break.start_time.astimezone(timezone.utc).replace(tzinfo=None))
        except Exception:
            diff = now - active_break.start_time
        active_break.duration_minutes = int(diff.total_seconds() // 60)
    

    attendance.clock_out = now
    # Get all breaks for this attendance to calculate total working time
    attendance_breaks = db.query(Break).filter(Break.attendance_id == attendance.id).all()
    attendance.total_hours = calculate_hours(attendance.clock_in, now, attendance_breaks)
    
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
    now = datetime.now(timezone.utc)
    
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
    now = datetime.now(timezone.utc)
    
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
    try:
        diff = (active_break.end_time.astimezone(timezone.utc).replace(tzinfo=None)
                - active_break.start_time.astimezone(timezone.utc).replace(tzinfo=None))
    except Exception:
        diff = now - active_break.start_time
    active_break.duration_minutes = int(diff.total_seconds() // 60)
    
    db.commit()
    db.refresh(active_break)
    
    return BreakEndResponse(
        message="Break ended",
        break_end=now,
        duration_minutes=active_break.duration_minutes
    )



@router.get("/logs", response_model=List[AttendanceResponse])
def get_attendance_logs(
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    per_page: int = 7,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get datewise attendance logs for the current user with pagination and zero-filled days.

    Query parameters:
    - start_date (optional): ISO date string (YYYY-MM-DD). If omitted, defaults to 7 days before today.
    - end_date (optional): ISO date string (YYYY-MM-DD). If omitted, defaults to today.
    - page (optional): page number (1-indexed). Default 1.
    - per_page (optional): number of days per page. Default 7. Max 90.

    The endpoint returns one entry per date in the requested page. Dates without
    an attendance record will be returned with null clock_in/clock_out and
    total_hours (zero-filled days) so the UI can render continuous date ranges.
    """
    today = date.today()
    if not end_date:
        end_date = today
    if not start_date:
        start_date = today - timedelta(days=6)  # default to last 7 days

    # Validate range and pagination params
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be <= end_date")

    if page < 1:
        page = 1

    # enforce sensible per_page bounds
    max_per_page = 90
    if per_page < 1:
        per_page = 1
    if per_page > max_per_page:
        per_page = max_per_page

    # Compute page window (dates)
    offset_days = (page - 1) * per_page
    page_start = start_date + timedelta(days=offset_days)
    if page_start > end_date:
        return []
    remaining_days = (end_date - page_start).days + 1
    page_span = min(per_page, remaining_days)
    page_end = page_start + timedelta(days=page_span - 1)

    # Fetch attendance records for the page window
    records = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id,
        Attendance.date >= page_start,
        Attendance.date <= page_end
    ).order_by(Attendance.date.asc()).all()

    # Map records by date for quick lookup
    records_by_date = {r.date: r for r in records}

    result: List[AttendanceResponse] = []
    for day_offset in range((page_end - page_start).days + 1):
        d = page_start + timedelta(days=day_offset)
        attendance = records_by_date.get(d)
        if not attendance:
            # zero-filled entry for dates without records
            result.append(AttendanceResponse(
                id=0,
                date=d,
                clock_in=None,
                clock_out=None,
                status=None,
                total_hours=None,
                breaks=[],
                is_on_break=False
            ))
            continue


        is_on_break = any(b.end_time is None for b in attendance.breaks)
        breaks = [BreakResponse(
            id=b.id,
            start_time=b.start_time,
            end_time=b.end_time,
            duration_minutes=b.duration_minutes
        ) for b in attendance.breaks]

        total_hours = attendance.total_hours
        if not total_hours and attendance.clock_in and attendance.clock_out:
            total_hours = calculate_hours(attendance.clock_in, attendance.clock_out, attendance.breaks)

        result.append(AttendanceResponse(
            id=attendance.id,
            date=attendance.date,
            clock_in=attendance.clock_in,
            clock_out=attendance.clock_out,
            status=attendance.status,
            total_hours=total_hours,
            breaks=breaks,
            is_on_break=is_on_break
        ))

    return result


@router.get("/history", response_model=List[AttendanceResponse])
def get_attendance_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get full attendance history for the current user.
    
    Returns:
        List[AttendanceResponse]: List of all attendance records
    """
    records = db.query(Attendance).filter(
        Attendance.employee_id == current_employee.id
    ).order_by(Attendance.date.desc()).all()
    
    result = []
    for attendance in records:
        is_on_break = any(b.end_time is None for b in attendance.breaks)
        breaks = [BreakResponse(
            id=b.id,
            start_time=b.start_time,
            end_time=b.end_time,
            duration_minutes=b.duration_minutes
        ) for b in attendance.breaks]


        # Always re-calculate total_hours if clock_in and clock_out are present
        total_hours = attendance.total_hours
        if attendance.clock_in and attendance.clock_out:
            calculated_hours = calculate_hours(attendance.clock_in, attendance.clock_out, attendance.breaks)
            # If database value is missing or "0h 0m", update it with calculated value
            if not total_hours or total_hours == "0h 0m":
                total_hours = calculated_hours
                attendance.total_hours = total_hours
                db.add(attendance) # Stage for update

        result.append(AttendanceResponse(
            id=attendance.id,
            date=attendance.date,
            clock_in=attendance.clock_in,
            clock_out=attendance.clock_out,
            status=attendance.status,
            total_hours=total_hours,
            breaks=breaks,
            is_on_break=is_on_break
        ))
    
    # Commit any updates to total_hours
    db.commit()
    
    return result
