"""
Leave management API routes.

This module provides endpoints for leave calendar and balance.
"""



from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from ..models.employee import Employee
from ..models.leave import Leave, LeaveBalance
from ..models.user import User

from ..schemas.leave import LeaveCalendarItem, LeaveBalanceResponse, LeaveResponse, CorporateLeaveCalendarResponse
from ..utils.deps import get_current_employee
from ..models.leave import CorporateLeave
from ..services.corporate_leave import CorporateLeaveAIService


router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get("/calendar", response_model=List[LeaveCalendarItem])
def get_leaves_calendar(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get leaves calendar showing team/org leaves.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[LeaveCalendarItem]: List of leaves for calendar
    """
    # Get leaves for the current month
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Get leaves starting/ending in or after the start of the month
    leaves = db.query(Leave).filter(
        Leave.end_date >= start_of_month
    ).all()
    

    result = []
    for leave in leaves:
        # Get employee name
        emp = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if emp:
            user = db.query(User).filter(User.id == emp.user_id).first()
            employee_name = user.full_name if user else "Unknown"
        else:
            employee_name = "Unknown"
        
        result.append(LeaveCalendarItem(
            id=leave.id,
            employee_name=employee_name,
            start_date=leave.start_date,
            end_date=leave.end_date,
            leave_type=leave.leave_type,
            half_day=leave.half_day == "true" if leave.half_day else False,
            half_day_type=leave.half_day_type
        ))
    
    return result



@router.get("/balance", response_model=LeaveBalanceResponse)
def get_leave_balance(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get current user's leave balances.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[LeaveBalanceResponse]: Leave balances by type
    """
    current_year = date.today().year
    
    try:
        # There is a single leave balance per employee per year
        bal = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == current_employee.id,
            LeaveBalance.year == current_year
        ).first()

        # compute used days from actual Leave records overlapping the year
        start_of_year = date(current_year, 1, 1)
        end_of_year = date(current_year, 12, 31)
        # Only paid leaves count against the paid balance
        leaves = db.query(Leave).filter(
            Leave.employee_id == current_employee.id,
            Leave.end_date >= start_of_year,
            Leave.start_date <= end_of_year,
            Leave.leave_type == "paid"
        ).all()

        used_sum = 0.0
        for l in leaves:
            try:
                used_sum += float(l.days or 0)
            except Exception:
                continue


        # If no balance exists for the user this year, create a default of 12 days
        if not bal:
            bal = LeaveBalance(
                employee_id=current_employee.id,
                year=current_year,
                total_days=12,
                used_days=used_sum,
                remaining_days=max(12 - used_sum, 0),
                leave_type="paid"  # Default to paid leave balance
            )
            db.add(bal)
            db.commit()
            db.refresh(bal)
        else:
            # update balance from computed used_sum
            bal.used_days = used_sum
            bal.remaining_days = max(bal.total_days - used_sum, 0)
            db.commit()

        return LeaveBalanceResponse(
            total_days=float(bal.total_days),
            used_days=float(bal.used_days),
            remaining_days=float(bal.remaining_days)
        )
    except Exception as e:
        # In case of any error, return default values
        db.rollback()
        return LeaveBalanceResponse(
            total_days=12.0,
            used_days=0.0,
            remaining_days=12.0
        )




@router.get("/history", response_model=List[LeaveResponse])
def get_leave_history(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated employee's leave history (all leave records).

    Returns:
        List[LeaveResponse]: list of leave records with dates, type and reason
    """
    try:
        # Get all leave records for the employee, ordered by start date (most recent first)
        leaves = db.query(Leave).filter(Leave.employee_id == current_employee.id).order_by(Leave.start_date.desc()).all()
        
        # Convert leaves to response format with half-day support
        result = []
        for leave in leaves:
            result.append(LeaveResponse(
                id=leave.id,
                start_date=leave.start_date,
                end_date=leave.end_date,
                days=leave.days,
                reason=leave.reason,
                leave_type=leave.leave_type,
                half_day=leave.half_day == "true" if leave.half_day else False,
                half_day_type=leave.half_day_type
            ))
        
        return result

    except Exception as e:
        # In case of any error, return empty list
        return []



@router.get("/corporate-calendar", response_model=List[CorporateLeaveCalendarResponse])
def get_corporate_calendar(
    year: Optional[int] = Query(None, description="Year to get calendar for (default: current year)"),
    region: str = Query("general", description="Region for AI-generated holidays (general, india, uk)"),
    include_ai_generated: bool = Query(True, description="Include AI-generated holidays if no manual ones exist"),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get corporate leave calendar with AI-generated holidays.
    
    This endpoint returns all corporate leaves for the specified year.
    It combines manually added corporate leaves with AI-generated official holidays.
    
    Args:
        year: Year for calendar (default: current year)
        region: Region for AI-generated holidays
        include_ai_generated: Whether to include AI-generated holidays when no manual ones exist
        current_employee: Current employee
        db: Database session
        
    Returns:
        List[CorporateLeaveCalendarResponse]: Corporate leave calendar
    """
    if year is None:
        year = date.today().year
    
    # Get manually added corporate leaves for the year
    corporate_leaves = db.query(CorporateLeave).filter(
        CorporateLeave.date >= date(year, 1, 1),
        CorporateLeave.date <= date(year, 12, 31)
    ).all()
    
    result = []
    
    # Add manually added corporate leaves
    for leave in corporate_leaves:
        result.append(CorporateLeaveCalendarResponse(
            date=leave.date,
            occasion=leave.name,
            type=leave.leave_type,
            is_ai_generated=False
        ))
    
    # If no manual leaves exist and AI generation is enabled, generate holidays
    if not corporate_leaves and include_ai_generated:
        generated_leaves = CorporateLeaveAIService.generate_corporate_leaves(year, region)
        
        for leave_data in generated_leaves:
            result.append(CorporateLeaveCalendarResponse(
                date=leave_data["date"],
                occasion=leave_data["name"],
                type=leave_data["type"],
                is_ai_generated=True
            ))
    
    # Sort by date
    result.sort(key=lambda x: x.date)
    
    return result


@router.get("/corporate-calendar/multi-year")
def get_multi_year_corporate_calendar(
    start_year: Optional[int] = Query(None, description="Start year (default: current year)"),
    end_year: Optional[int] = Query(None, description="End year (default: current year + 2)"),
    region: str = Query("general", description="Region for AI-generated holidays"),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get corporate leave calendar for multiple years.
    
    This endpoint returns corporate leaves for a range of years.
    Automatically generates AI holidays for years without manual entries.
    
    Args:
        start_year: Start year (default: current year)
        end_year: End year (default: current year + 2)
        region: Region for AI-generated holidays
        current_employee: Current employee
        db: Database session
        
    Returns:
        Dictionary with multi-year calendar data
    """
    current_year = date.today().year
    
    if start_year is None:
        start_year = current_year
    
    if end_year is None:
        end_year = current_year + 2
    
    if start_year > end_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start year must be less than or equal to end year"
        )
    
    all_results = {}
    
    for year in range(start_year, end_year + 1):
        # Get corporate leaves for this year
        corporate_leaves = db.query(CorporateLeave).filter(
            CorporateLeave.date >= date(year, 1, 1),
            CorporateLeave.date <= date(year, 12, 31)
        ).all()
        
        year_result = []
        
        # Add manually added corporate leaves
        for leave in corporate_leaves:
            year_result.append(CorporateLeaveCalendarResponse(
                date=leave.date,
                occasion=leave.name,
                type=leave.leave_type,
                is_ai_generated=False
            ))
        
        # If no manual leaves exist, generate AI-based corporate leaves
        if not corporate_leaves:
            generated_leaves = CorporateLeaveAIService.generate_corporate_leaves(year, region)
            
            for leave_data in generated_leaves:
                year_result.append(CorporateLeaveCalendarResponse(
                    date=leave_data["date"],
                    occasion=leave_data["name"],
                    type=leave_data["type"],
                    is_ai_generated=True
                ))
        
        # Sort by date
        year_result.sort(key=lambda x: x.date)
        all_results[str(year)] = year_result
    
    return {
        "year_range": f"{start_year}-{end_year}",
        "region": region,
        "calendar_data": all_results,
        "total_years": end_year - start_year + 1
    }


@router.get("/corporate-calendar/years-available")
def get_available_calendar_years(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get list of years for which corporate holidays are available.
    
    Args:
        current_employee: Current employee
        db: Database session
        
    Returns:
        Dictionary with available years and statistics
    """
    # Get all unique years from corporate leaves
    all_holidays = db.query(CorporateLeave).all()
    
    years_set = set()
    type_stats = {}
    total_count = len(all_holidays)
    
    for holiday in all_holidays:
        year = holiday.date.year
        years_set.add(year)
        
        leave_type = holiday.leave_type
        if leave_type not in type_stats:
            type_stats[leave_type] = 0
        type_stats[leave_type] += 1
    
    # Get current year and suggest range
    current_year = date.today().year
    suggested_years = list(range(current_year, current_year + 3))  # Current + 2 future years
    
    return {
        "available_years": sorted(list(years_set)),
        "current_year": current_year,
        "suggested_years": suggested_years,
        "total_holidays": total_count,
        "holiday_types": type_stats,
        "has_current_year": current_year in years_set,
        "missing_years": [year for year in suggested_years if year not in years_set]
    }
