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
    FinancesResponse,
    CTCBreakupResponse
)
from ..utils.deps import get_current_employee
from ..services.salary_calculation import SalaryCalculationService


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


@router.get("/ctc-breakup", response_model=CTCBreakupResponse)
def get_ctc_breakup(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get detailed CTC (Cost to Company) breakdown with analysis.
    
    This endpoint provides comprehensive breakdown of salary components,
    percentage analysis, tax implications, compliance validation, and
    formatted human-readable breakdown.
    
    Args:
        current_employee: User's employee profile
        db: Database session
        
    Returns:
        CTCBreakupResponse: Detailed CTC breakdown with analysis
        
    Raises:
        HTTPException: 404 if salary info not found
    """
    # Get salary information
    salary = db.query(Salary).filter(
        Salary.employee_id == current_employee.id
    ).first()
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found"
        )
    
    # Initialize salary calculation service
    calculation_service = SalaryCalculationService()
    
    # Get detailed calculation with current salary data
    components = calculation_service.auto_calculate_from_ctc(
        annual_ctc=salary.annual_ctc,
        city="default",  # Could be enhanced to use employee location
        state="default",  # Could be enhanced to use employee state
        overrides={
            "basic": salary.basic,
            "hra": salary.hra,
            "special_allowance": salary.special_allowance,
            "pf_deduction": salary.pf_deduction,
            "tax_deduction": salary.tax_deduction
        }
    )
    
    # Perform detailed validation
    validation_result = calculation_service.validate_salary_structure_detailed(
        annual_ctc=salary.annual_ctc,
        monthly_gross=salary.monthly_gross,
        basic=salary.basic,
        hra=salary.hra,
        special_allowance=salary.special_allowance,
        pf_deduction=salary.pf_deduction,
        tax_deduction=salary.tax_deduction
    )
    
    # Calculate percentages
    percentages = {
        "basic_percentage": round((salary.basic * 12 / salary.annual_ctc) * 100, 2) if salary.annual_ctc > 0 else 0,
        "hra_percentage": round((salary.hra / salary.basic) * 100, 2) if salary.basic > 0 else 0,
        "special_allowance_percentage": round((salary.special_allowance * 12 / salary.annual_ctc) * 100, 2) if salary.annual_ctc > 0 else 0,
        "deductions_percentage": round((salary.total_deductions * 12 / salary.annual_ctc) * 100, 2) if salary.annual_ctc > 0 else 0,
        "net_pay_percentage": round((salary.net_pay * 12 / salary.annual_ctc) * 100, 2) if salary.annual_ctc > 0 else 0
    }
    
    # Build comprehensive response
    ctc_breakup = CTCBreakupResponse(
        annual_ctc=salary.annual_ctc,
        monthly_ctc=salary.annual_ctc / 12,
        components={
            "basic": {
                "monthly": salary.basic,
                "annual": salary.basic * 12,
                "percentage_of_ctc": percentages["basic_percentage"]
            },
            "hra": {
                "monthly": salary.hra,
                "annual": salary.hra * 12,
                "percentage_of_basic": percentages["hra_percentage"]
            },
            "special_allowance": {
                "monthly": salary.special_allowance,
                "annual": salary.special_allowance * 12,
                "percentage_of_ctc": percentages["special_allowance_percentage"]
            },
            "gross_salary": {
                "monthly": salary.monthly_gross,
                "annual": salary.monthly_gross * 12
            }
        },
        percentages=percentages,
        deductions={
            "pf_deduction": {
                "monthly": salary.pf_deduction,
                "annual": salary.pf_deduction * 12,
                "percentage_of_basic": round((salary.pf_deduction / salary.basic) * 100, 2) if salary.basic > 0 else 0
            },
            "tax_deduction": {
                "monthly": salary.tax_deduction,
                "annual": salary.tax_deduction * 12,
                "percentage_of_gross": round((salary.tax_deduction / salary.monthly_gross) * 100, 2) if salary.monthly_gross > 0 else 0
            },
            "total_deductions": {
                "monthly": salary.total_deductions,
                "annual": salary.total_deductions * 12,
                "percentage_of_ctc": percentages["deductions_percentage"]
            }
        },
        employer_contributions={
            "pf_contribution": {
                "monthly": components.employer_pf,
                "annual": components.employer_pf * 12,
                "percentage_of_basic": round((components.employer_pf / salary.basic) * 100, 2) if salary.basic > 0 else 0
            },
            "total_employer_contribution": {
                "monthly": components.employer_pf,
                "annual": components.employer_pf * 12
            }
        },
        tax_analysis={
            "annual_gross_income": salary.monthly_gross * 12,
            "annual_taxable_income": max(0, (salary.monthly_gross * 12) - 50000),  # Standard deduction
            "estimated_annual_tax": salary.tax_deduction * 12,
            "estimated_monthly_tax": salary.tax_deduction,
            "tax_slab": components.calculation_details.get("tax_slab_applied", "Unknown"),
            "effective_tax_rate": round((salary.tax_deduction * 12 / (salary.monthly_gross * 12)) * 100, 2) if salary.monthly_gross > 0 else 0
        },
        compliance={
            "is_compliant": validation_result.is_valid,
            "compliance_score": validation_result.compliance_score,
            "issues": validation_result.issues,
            "recommendations": validation_result.recommendations,
            "basic_percentage": validation_result.basic_percentage * 100,
            "hra_percentage": validation_result.hra_percentage * 100 if validation_result.hra_percentage else 0,
            "deductions_percentage": validation_result.deductions_percentage * 100
        },
        calculation_details=components.calculation_details,
        formatted_breakdown=calculation_service.format_salary_breakdown(components)
    )
    
    return ctc_breakup
