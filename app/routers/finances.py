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
from ..models.leave import Leave


from ..schemas.salary import (
    SalaryDetailsResponse,
    PayCycleResponse,
    PayslipResponse,
    FinancesResponse,
    CTCBreakupResponse,
    EmployeePayslipListResponse,
    EmployeePayslipDetailResponse,
    MonthlySalaryLogsResponse
)
from ..utils.deps import get_current_employee
from ..services.salary_calculation import SalaryCalculationService


router = APIRouter(prefix="/finances", tags=["Finances"])




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


@router.get("/payslips", response_model=list[EmployeePayslipListResponse])
def get_employee_payslips(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get list of employee's monthly payslips.
    
    Args:
        current_employee: Current authenticated employee
        db: Database session
        
    Returns:
        List of EmployeePayslipListResponse: Employee's payslip history
    """
    # Get all payslips for the current employee
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == current_employee.id
    ).order_by(Payslip.year.desc(), Payslip.month.desc()).all()
    
    return payslips


@router.get("/payslips/{year}/{month}", response_model=EmployeePayslipDetailResponse)
def get_employee_payslip_detail(
    year: int,
    month: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get detailed payslip for specific month.
    
    Args:
        year: Year of the payslip
        month: Month of the payslip (1-12)
        current_employee: Current authenticated employee
        db: Database session
        
    Returns:
        EmployeePayslipDetailResponse: Detailed payslip information
        
    Raises:
        HTTPException: 404 if payslip not found
    """
    # Get the specific payslip for the employee
    payslip = db.query(Payslip).filter(
        Payslip.employee_id == current_employee.id,
        Payslip.year == year,
        Payslip.month == month
    ).first()
    
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payslip not found for {year}-{month:02d}"
        )
    
    # Get employee salary information for CTC details
    salary = db.query(Salary).filter(
        Salary.employee_id == current_employee.id
    ).first()
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found"
        )
    
    # Calculate additional fields
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    
    # Get employee name and email
    employee_name = current_employee.user.full_name if current_employee.user else ""
    employee_email = current_employee.user.email if current_employee.user else ""
    
    # Calculate per-day salary
    per_day_salary = salary.net_pay / days_in_month if days_in_month > 0 else 0
    
    # Calculate leave deductions
    leave_deduction = payslip.leave_deduction_amount if payslip.leave_deduction_amount else 0
    salary_cut_for_unpaid_leaves = payslip.loss_of_pay_days * per_day_salary if payslip.loss_of_pay_days else 0
    
    # Calculate final processed salary
    final_processed_salary = payslip.amount
    
    # Build detailed response
    payslip_detail = EmployeePayslipDetailResponse(
        employee_id=current_employee.id,
        employee_name=employee_name,
        employee_email=employee_email,
        department=current_employee.department or "",
        designation=current_employee.designation or "",
        
        # Payslip identification
        payslip_id=payslip.id,
        month=payslip.month,
        year=payslip.year,
        pay_date=None,  # Could be added to Payslip model if needed
        
        # CTC Information
        annual_ctc=salary.annual_ctc,
        monthly_ctc=salary.annual_ctc / 12,
        
        # Salary Components (actual vs payable)
        basic_actual=payslip.basic_actual if payslip.basic_actual else salary.basic,
        basic_payable=payslip.basic_paid if payslip.basic_paid else salary.basic,
        hra_actual=payslip.hra_actual if payslip.hra_actual else salary.hra,
        hra_payable=payslip.hra_paid if payslip.hra_paid else salary.hra,
        medical_allowance_actual=payslip.medical_allowance_actual or 0,
        medical_allowance_payable=payslip.medical_allowance_paid or 0,
        conveyance_allowance_actual=payslip.conveyance_allowance_actual or 0,
        conveyance_allowance_payable=payslip.conveyance_allowance_paid or 0,
        total_earnings_actual=payslip.total_earnings_actual if payslip.total_earnings_actual else salary.monthly_gross,
        total_earnings_payable=payslip.total_earnings_paid if payslip.total_earnings_paid else salary.monthly_gross,
        
        # Deductions
        pf_deduction=salary.pf_deduction,
        tax_deduction=salary.tax_deduction,
        professional_tax=payslip.professional_tax or 0,
        leave_deduction=leave_deduction,
        total_deductions=payslip.total_deductions if payslip.total_deductions else salary.total_deductions,
        
        # Net Salary
        gross_salary=salary.monthly_gross,
        in_hand_salary=payslip.amount,
        
        # Leave and Days Information
        total_days_in_month=days_in_month,
        total_working_days=payslip.total_working_days or days_in_month,
        unpaid_leaves_taken=payslip.loss_of_pay_days or 0,
        half_day_leaves=0,  # Could be calculated from leave records
        per_day_salary=per_day_salary,
        days_payable=payslip.days_payable if payslip.days_payable else days_in_month,
        
        # Leave-based calculations
        salary_cut_for_unpaid_leaves=salary_cut_for_unpaid_leaves,
        final_processed_salary=final_processed_salary,
        
        # Additional information
        ytd_earnings=None,  # Could be calculated from year-to-date payslips
        ytd_deductions=None,  # Could be calculated from year-to-date payslips
        
        # Metadata
        generated_at=payslip.created_at,
        calculation_details={
            "payable_days": payslip.days_payable,
            "total_working_days": payslip.total_working_days,
            "loss_of_pay_days": payslip.loss_of_pay_days,
            "leave_deduction_amount": payslip.leave_deduction_amount,
            "per_day_salary": per_day_salary,
            "base_net_pay": salary.net_pay
        }
    )
    
    return payslip_detail


@router.get("/monthly-salary-logs", response_model=MonthlySalaryLogsResponse)
def get_monthly_salary_logs(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """
    Get monthly salary logs for current and previous month with leave information.
    
    This endpoint shows employee salary data including:
    - Current month: Expected salary, leave data, payment status
    - Previous month: Actual paid salary, leave data, payment status
    - Leave information (paid/unpaid leaves) for both months
    - Leave deductions and net salary calculations
    - Payment dates and amounts
    
    Args:
        current_employee: Current authenticated employee
        db: Database session
        
    Returns:
        MonthlySalaryLogsResponse: Current and previous month salary logs with leave data
        
    Raises:
        HTTPException: 404 if salary information not found
    """
    from datetime import datetime, timedelta
    from calendar import monthrange
    import calendar
    
    # Get current date and calculate current/previous month
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Calculate previous month
    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year
    
    # Get employee salary information
    salary = db.query(Salary).filter(
        Salary.employee_id == current_employee.id
    ).first()
    
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary information not found"
        )
    
    # Get employee basic info
    employee_name = current_employee.user.full_name if current_employee.user else ""
    employee_email = current_employee.user.email if current_employee.user else ""
    
    # Function to get leave data for a specific month
    def get_leave_data_for_month(year, month):
        """Get leave data for specific month"""
        # Get all leaves for the employee in this month
        leaves = db.query(Leave).filter(
            Leave.employee_id == current_employee.id
        ).filter(
            Leave.start_date >= datetime(year, month, 1).date()
        ).filter(
            Leave.start_date <= datetime(year, month, monthrange(year, month)[1]).date()
        ).all()
        
        paid_leaves = 0.0
        unpaid_leaves = 0.0
        
        for leave in leaves:
            if leave.leave_type == 'paid':
                paid_leaves += leave.days
            elif leave.leave_type == 'unpaid':
                unpaid_leaves += leave.days
        
        return paid_leaves, unpaid_leaves
    
    # Function to calculate salary for a month
    def calculate_monthly_salary(year, month, is_current_month=False):
        """Calculate salary data for a specific month"""
        # Get payslip for this month if it exists
        payslip = db.query(Payslip).filter(
            Payslip.employee_id == current_employee.id,
            Payslip.year == year,
            Payslip.month == month
        ).first()
        
        # Get leave data from Leave records
        paid_leaves, unpaid_leaves = get_leave_data_for_month(year, month)
        
        # Calculate total days and working days
        total_days = monthrange(year, month)[1]
        
        if payslip:
            # Use actual payslip data
            salary_amount = payslip.amount + (payslip.leave_deduction_amount or 0)  # Add back leave deduction to show full salary
            net_salary = payslip.amount
            paid_status = payslip.status
            payment_date = payslip.processed_date.date() if payslip.processed_date else None
            
            # Use payslip data for working days and leave information
            working_days = payslip.days_payable if payslip.days_payable is not None else total_days
            unpaid_leaves = payslip.loss_of_pay_days if payslip.loss_of_pay_days is not None else unpaid_leaves
            leave_deduction = payslip.leave_deduction_amount if payslip.leave_deduction_amount is not None else 0
            
        else:
            # No payslip found - calculate expected values
            salary_amount = salary.net_pay
            net_salary = salary.net_pay
            paid_status = "unpaid" if is_current_month else "not_processed"
            payment_date = None
            
            # Calculate leave deduction for unpaid leaves
            per_day_salary = salary.net_pay / total_days if total_days > 0 else 0
            leave_deduction = unpaid_leaves * per_day_salary
            working_days = total_days - unpaid_leaves
        
        return {
            "month": month,
            "year": year,
            "salary_amount": salary_amount,
            "paid_status": paid_status,
            "payment_date": payment_date,
            "total_days": total_days,
            "working_days": working_days,
            "paid_leaves": paid_leaves,
            "unpaid_leaves": unpaid_leaves,
            "leave_deduction": leave_deduction,
            "net_salary": net_salary,
            "description": f"Salary for {calendar.month_name[month]} {year}"
        }
    
    # Calculate data for current and previous month
    current_month_data = calculate_monthly_salary(current_year, current_month, is_current_month=True)
    previous_month_data = calculate_monthly_salary(previous_year, previous_month, is_current_month=False)
    
    # Build final response
    response = MonthlySalaryLogsResponse(
        employee_id=current_employee.id,
        employee_name=employee_name,
        employee_email=employee_email,
        department=current_employee.department or "",
        designation=current_employee.designation or "",
        current_month=current_month_data,
        previous_month=previous_month_data,
        generated_at=datetime.now()
    )
    
    return response
