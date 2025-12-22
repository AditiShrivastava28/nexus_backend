
"""
Admin-specific salary API schemas for the new simplified endpoints.

This module defines schemas for the three specific APIs requested:
1. CTC breakdown for employees
2. Salary validation and generation with unpaid leaves
3. Payslip generation with leave calculations
"""


from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal


class CTCBreakdownResponse(BaseModel):
    """
    Response schema for CTC breakdown API.
    
    Shows complete cost to company breakdown for an employee with current calculations.
    """
    employee_id: int
    employee_name: str
    employee_email: str
    department: str
    designation: str
    
    # CTC Components
    annual_ctc: float
    monthly_gross: float
    
    # Salary Components (monthly)
    basic: float
    hra: float
    special_allowance: float
    
    # Deductions (monthly)
    pf_deduction: float
    tax_deduction: float
    professional_tax: float
    total_deductions: float
    
    # Net Pay
    net_pay: float
    
    # Additional breakdown
    employer_pf: float
    cost_per_day: float  # Annual CTC / 365
    
    # Calculation details
    calculation_details: Dict[str, Any]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class MonthlySalaryValidationRequest(BaseModel):
    """
    Request schema for monthly salary validation with unpaid leaves.
    
    Validates and generates salary for a specific month considering unpaid leaves.
    """
    year: int = Field(..., description="Year for salary processing")
    month: int = Field(..., ge=1, le=12, description="Month for salary processing (1-12)")
    
    # Leave information
    unpaid_leave_days: float = Field(default=0.0, ge=0, description="Number of unpaid leave days")
    half_day_leaves: float = Field(default=0.0, ge=0, description="Number of half-day leaves")
    unpaid_leave_dates: Optional[list[date]] = Field(default=None, description="Specific unpaid leave dates")
    
    # Additional options
    override_days_in_month: Optional[int] = Field(default=None, ge=28, le=31, description="Override days in month")
    custom_deduction: Optional[float] = Field(default=0.0, ge=0, description="Custom additional deduction")
    
    # Processing options
    generate_payslip: bool = Field(default=True, description="Whether to generate/update payslip")
    dry_run: bool = Field(default=False, description="Whether this is a dry run (no DB changes)")


class MonthlySalaryValidationResponse(BaseModel):
    """
    Response schema for monthly salary validation.
    
    Shows validation results and calculated salary for the month.
    """
    success: bool
    employee_id: int
    employee_name: str
    month: int
    year: int
    
    # Validation results
    is_valid: bool
    validation_issues: list[str] = Field(default_factory=list)
    
    # Month details
    days_in_month: int
    working_days: int
    unpaid_leave_days: float
    half_day_leaves: float
    payable_days: float
    
    # Salary calculations
    daily_salary: float  # Net pay / days in month
    leave_deduction: float  # unpaid_leave_days * daily_salary
    custom_deduction: float
    total_deductions: float
    final_net_salary: float  # Net pay - leave_deduction - custom_deduction
    
    # Payslip data (if generated)
    payslip_id: Optional[int] = None
    payslip_generated: bool = False
    
    # Calculation breakdown
    calculation_details: Dict[str, Any]
    processed_at: datetime
    
    class Config:
        from_attributes = True


class PayslipGenerationRequest(BaseModel):
    """
    Request schema for payslip generation with leave calculations.
    
    Generates detailed payslip for a specific month with leave-based salary calculations.
    """
    year: int = Field(..., description="Year for payslip generation")
    month: int = Field(..., ge=1, le=12, description="Month for payslip generation (1-12)")
    
    # Leave information (optional - will be calculated from leave records if not provided)
    unpaid_leave_days: Optional[float] = Field(default=None, ge=0, description="Override unpaid leave days")
    half_day_leaves: Optional[float] = Field(default=None, ge=0, description="Override half-day leaves")
    
    # Payslip options
    include_ytd: bool = Field(default=True, description="Include year-to-date information")
    detailed_breakdown: bool = Field(default=True, description="Include detailed component breakdown")
    format_type: str = Field(default="standard", description="Payslip format type")


class PayslipGenerationResponse(BaseModel):
    """
    Response schema for detailed payslip generation.
    
    Returns formatted payslip with all requested information including CTC, in-hand salary,
    total days, working days, per-day salary, unpaid leaves, salary cuts, etc.
    """
    success: bool
    employee_id: int
    employee_name: str
    employee_email: str
    department: str
    designation: str
    
    # Payslip identification
    payslip_id: Optional[int] = None
    month: int
    year: int
    pay_date: date
    
    # Employee CTC Information
    annual_ctc: float
    monthly_ctc: float
    
    # Salary Components (actual vs payable)
    basic_actual: float
    basic_payable: float
    hra_actual: float
    hra_payable: float
    special_allowance_actual: float
    special_allowance_payable: float
    total_earnings_actual: float
    total_earnings_payable: float
    
    # Deductions
    pf_deduction: float
    tax_deduction: float
    professional_tax: float
    leave_deduction: float
    other_deductions: float
    total_deductions: float
    
    # Net Salary
    gross_salary: float
    in_hand_salary: float  # Total earnings - total deductions
    
    # Leave and Days Information
    total_days_in_month: int
    total_working_days: int
    unpaid_leaves_taken: float
    half_day_leaves: float
    per_day_salary: float  # In-hand salary / total_days_in_month
    
    # Leave-based calculations
    salary_cut_for_unpaid_leaves: float  # unpaid_leaves * per_day_salary
    final_processed_salary: float  # in_hand_salary - salary_cut_for_unpaid_leaves
    
    # Additional information
    ytd_earnings: Optional[float] = None
    ytd_deductions: Optional[float] = None
    leave_balance_remaining: Optional[float] = None
    
    # Payslip metadata
    generated_at: datetime
    calculation_details: Dict[str, Any]
    
    class Config:
        from_attributes = True


class EmployeeCTCSummary(BaseModel):
    """
    Summary model for employee CTC information.
    """
    employee_id: int
    employee_name: str
    annual_ctc: float
    monthly_net: float
    department: str
    designation: str
    last_updated: datetime


class BulkSalaryValidationRequest(BaseModel):
    """
    Request schema for bulk salary validation.
    """
    year: int
    month: int
    employee_ids: Optional[list[int]] = Field(default=None, description="Specific employees to process (None = all active employees)")
    unpaid_leave_days: Optional[float] = Field(default=0.0, description="Default unpaid leave days for all employees")
    dry_run: bool = Field(default=False)


class BulkSalaryValidationResponse(BaseModel):
    """
    Response schema for bulk salary validation.
    """
    success: bool
    total_employees: int
    processed_count: int
    failed_count: int
    results: list[MonthlySalaryValidationResponse]
    processed_at: datetime
