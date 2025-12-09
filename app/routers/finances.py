"""
Finances/Payroll API routes.

This module provides endpoints for salary and payslip information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from ..models.employee import Employee
from ..models.salary import Salary, Payslip
from ..schemas.salary import (
    SalaryDetailsResponse,
    PayCycleResponse,
    PayslipResponse,
    FinancesResponse
)
from ..utils.deps import get_current_employee


router = APIRouter(prefix="/finances", tags=["Finances"])


@router.get("/salary", response_model=FinancesResponse)
def get_salary_details(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get salary details and payslips for the current user.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        FinancesResponse: Salary details, pay cycle, and payslips
        
    Raises:
        HTTPException: 404 if salary info not found
    """
    salary = db.query(Salary).filter(
        Salary.employee_id == current_employee.id
    ).first()
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found"
        )
    
    # Calculate days to next pay
    today = date.today()
    if salary.next_pay_date:
        days_to_pay = (salary.next_pay_date - today).days
        days_to_pay = max(0, days_to_pay)
    else:
        days_to_pay = 0
    
    salary_response = SalaryDetailsResponse(
        annualCTC=salary.annual_ctc,
        monthlyGross=salary.monthly_gross,
        basic=salary.basic,
        hra=salary.hra,
        specialAllowance=salary.special_allowance,
        pfDeduction=salary.pf_deduction,
        taxDeduction=salary.tax_deduction,
        totalDeductions=salary.total_deductions,
        netPay=salary.net_pay,
        currency=salary.currency
    )
    
    pay_cycle = PayCycleResponse(
        lastPaid=salary.last_paid,
        nextPayDate=salary.next_pay_date,
        daysToPay=days_to_pay,
        nextIncrementDate=salary.next_increment_date,
        incrementCycle=salary.increment_cycle
    )
    
    # Get payslips
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == current_employee.id
    ).order_by(Payslip.year.desc(), Payslip.month.desc()).all()
    
    payslip_responses = [PayslipResponse(
        id=p.id,
        month=p.month,
        year=p.year,
        amount=p.amount,
        status=p.status
    ) for p in payslips]
    
    return FinancesResponse(
        salary=salary_response,
        payCycle=pay_cycle,
        payslips=payslip_responses
    )


@router.get("/payslips", response_model=List[PayslipResponse])
def get_payslips(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get payslip history for the current user.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        List[PayslipResponse]: List of payslips
    """
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == current_employee.id
    ).order_by(Payslip.year.desc(), Payslip.month.desc()).all()
    
    return [PayslipResponse(
        id=p.id,
        month=p.month,
        year=p.year,
        amount=p.amount,
        status=p.status
    ) for p in payslips]


@router.get("/payslips/{payslip_id}/download")
def download_payslip(
    payslip_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Download a payslip PDF.
    
    Args:
        payslip_id: Payslip ID to download
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        dict: Payslip download URL or message
        
    Raises:
        HTTPException: 404 if payslip not found
    """
    payslip = db.query(Payslip).filter(
        Payslip.id == payslip_id,
        Payslip.employee_id == current_employee.id
    ).first()
    
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    
    if payslip.file_url:
        return {"download_url": payslip.file_url}
    
    return {"message": "Payslip PDF not yet available"}
