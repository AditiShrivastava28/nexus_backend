"""
Salary-related Pydantic schemas.

This module defines schemas for salary and payslip operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class SalaryDetailsResponse(BaseModel):
    """
    Salary details response.
    
    Attributes:
        annualCTC: Annual cost to company
        monthlyGross: Monthly gross salary
        basic: Basic salary
        hra: House rent allowance
        specialAllowance: Special allowance
        pfDeduction: PF deduction
        taxDeduction: Tax deduction
        totalDeductions: Total deductions
        netPay: Net take-home pay
        currency: Currency code
    """
    annualCTC: float
    monthlyGross: float
    basic: float
    hra: float
    specialAllowance: float
    pfDeduction: float
    taxDeduction: float
    totalDeductions: float
    netPay: float
    currency: str

    class Config:
        from_attributes = True


class PayCycleResponse(BaseModel):
    """
    Pay cycle information response.
    
    Attributes:
        lastPaid: Last payment date
        nextPayDate: Next payment date
        daysToPay: Days until next payment
        nextIncrementDate: Next increment date
        incrementCycle: Increment cycle
    """
    lastPaid: Optional[date] = None
    nextPayDate: Optional[date] = None
    daysToPay: int
    nextIncrementDate: Optional[date] = None
    incrementCycle: Optional[str] = None

    class Config:
        from_attributes = True


class PayslipResponse(BaseModel):
    """
    Payslip response schema.
    
    Attributes:
        id: Payslip ID
        month: Month number
        year: Year
        amount: Net amount
        status: Payment status
        file_url: URL to payslip PDF
    """
    id: int
    month: int
    year: int
    amount: float
    status: str
    file_url: Optional[str] = None
    processed_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class CTCBreakupResponse(BaseModel):
    """
    CTC (Cost to Company) breakdown response with detailed analysis.
    
    Provides comprehensive breakdown of salary components, percentages,
    tax implications, and compliance validation.
    
    Attributes:
        annual_ctc: Annual cost to company
        monthly_ctc: Monthly cost to company
        components: Detailed breakdown of salary components
        percentages: Percentage analysis of each component
        deductions: Detailed deductions breakdown
        employer_contributions: Employer-side contributions
        tax_analysis: Income tax calculation and breakdown
        compliance: Compliance validation and recommendations
        calculation_details: Technical calculation methodology
        formatted_breakdown: Human-readable formatted breakdown
    """
    annual_ctc: float
    monthly_ctc: float
    components: dict
    percentages: dict
    deductions: dict
    employer_contributions: dict
    tax_analysis: dict
    compliance: dict
    calculation_details: dict
    formatted_breakdown: dict

    class Config:
        from_attributes = True


class FinancesResponse(BaseModel):
    """
    Complete finances response.
    
    Attributes:
        salary: Salary details
        payCycle: Pay cycle info
        payslips: List of payslips
    """
    salary: SalaryDetailsResponse
    payCycle: PayCycleResponse
    payslips: list[PayslipResponse]

    class Config:
        from_attributes = True


class EmployeePayslipListResponse(BaseModel):
    """
    Employee payslip list response.
    
    Attributes:
        id: Payslip ID
        month: Month number (1-12)
        year: Year
        amount: Net amount paid
        status: Payment status
        file_url: URL to payslip PDF
        processed_date: Processing date
    """
    id: int
    month: int
    year: int
    amount: float
    status: str
    file_url: Optional[str] = None
    processed_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeePayslipDetailResponse(BaseModel):
    """
    Employee payslip detailed response matching admin format.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee full name
        employee_email: Employee email
        department: Employee department
        designation: Employee designation
        
        # Payslip identification
        payslip_id: Payslip ID
        month: Month number
        year: Year
        pay_date: Payment date
        
        # CTC Information
        annual_ctc: Annual cost to company
        monthly_ctc: Monthly cost to company
        
        # Salary Components (actual vs payable)
        basic_actual: Basic salary actual amount
        basic_payable: Basic salary payable amount
        hra_actual: HRA actual amount
        hra_payable: HRA payable amount
        medical_allowance_actual: Medical allowance actual amount
        medical_allowance_payable: Medical allowance payable amount
        conveyance_allowance_actual: Conveyance allowance actual amount
        conveyance_allowance_payable: Conveyance allowance payable amount
        total_earnings_actual: Total earnings actual amount
        total_earnings_payable: Total earnings payable amount
        
        # Deductions
        pf_deduction: PF deduction amount
        tax_deduction: Tax deduction amount
        professional_tax: Professional tax deduction
        leave_deduction: Leave deduction amount
        total_deductions: Total deductions
        
        # Net Salary
        gross_salary: Gross salary amount
        in_hand_salary: In-hand salary amount
        
        # Leave and Days Information
        total_days_in_month: Total days in the month
        total_working_days: Total working days
        unpaid_leaves_taken: Number of unpaid leaves taken
        half_day_leaves: Number of half-day leaves
        per_day_salary: Per day salary calculation
        days_payable: Net payable days
        
        # Leave-based calculations
        salary_cut_for_unpaid_leaves: Salary cut for unpaid leaves
        final_processed_salary: Final processed salary
        
        # Additional information
        ytd_earnings: Year-to-date earnings
        ytd_deductions: Year-to-date deductions
        
        # Metadata
        generated_at: Generation timestamp
        calculation_details: Detailed calculation breakdown
    """
    employee_id: int
    employee_name: str
    employee_email: str
    department: str
    designation: str
    
    # Payslip identification
    payslip_id: int
    month: int
    year: int
    pay_date: Optional[date] = None
    
    # CTC Information
    annual_ctc: float
    monthly_ctc: float
    
    # Salary Components (actual vs payable)
    basic_actual: float
    basic_payable: float
    hra_actual: float
    hra_payable: float
    medical_allowance_actual: float
    medical_allowance_payable: float
    conveyance_allowance_actual: float
    conveyance_allowance_payable: float
    total_earnings_actual: float
    total_earnings_payable: float
    
    # Deductions
    pf_deduction: float
    tax_deduction: float
    professional_tax: float
    leave_deduction: float
    total_deductions: float
    
    # Net Salary
    gross_salary: float
    in_hand_salary: float
    
    # Leave and Days Information
    total_days_in_month: int
    total_working_days: int
    unpaid_leaves_taken: float
    half_day_leaves: float
    per_day_salary: float
    days_payable: float
    
    # Leave-based calculations
    salary_cut_for_unpaid_leaves: float
    final_processed_salary: float
    
    # Additional information
    ytd_earnings: Optional[float] = None
    ytd_deductions: Optional[float] = None
    
    # Metadata
    generated_at: datetime
    calculation_details: dict

    class Config:
        from_attributes = True


class MonthlySalaryLog(BaseModel):
    """
    Monthly salary log data for employee.
    
    Attributes:
        month: Month number (1-12)
        year: Year
        salary_amount: Expected or actual salary amount
        paid_status: Payment status (paid/unpaid/processing)
        payment_date: Date when salary was paid or will be paid
        total_days: Total days in the month
        working_days: Total working days in the month
        paid_leaves: Number of paid leaves taken
        unpaid_leaves: Number of unpaid leaves taken
        leave_deduction: Amount deducted for unpaid leaves
        net_salary: Net salary after leave deductions
        description: Additional description or notes
    """
    month: int
    year: int
    salary_amount: float
    paid_status: str
    payment_date: Optional[date] = None
    total_days: int
    working_days: int
    paid_leaves: float
    unpaid_leaves: float
    leave_deduction: float
    net_salary: float
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MonthlySalaryLogsResponse(BaseModel):
    """
    Employee monthly salary logs response.
    
    Shows current month and previous month salary data with leave information
    and payment status for employee self-service.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee full name
        employee_email: Employee email
        department: Employee department
        designation: Employee designation
        current_month: Current month salary data
        previous_month: Previous month salary data
        generated_at: Response generation timestamp
    """
    employee_id: int
    employee_name: str
    employee_email: str
    department: str
    designation: str
    current_month: MonthlySalaryLog
    previous_month: MonthlySalaryLog
    generated_at: datetime

    class Config:
        from_attributes = True
