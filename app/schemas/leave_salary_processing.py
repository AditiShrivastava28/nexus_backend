"""
Leave-based salary processing Pydantic schemas.

This module defines schemas for salary processing with leave deductions
and detailed payslip generation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from decimal import Decimal


class LeaveDeductionRequest(BaseModel):
    """
    Schema for leave deduction request.
    
    Attributes:
        employee_id: Employee ID
        month: Month for calculation
        year: Year for calculation
        unpaid_leave_days: Number of unpaid leave days
        half_day_leaves: Number of half-day unpaid leaves
    """
    employee_id: int
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., description="Year")
    unpaid_leave_days: float = Field(default=0.0, ge=0.0, description="Number of full unpaid leave days")
    half_day_leaves: float = Field(default=0.0, ge=0.0, description="Number of half-day unpaid leaves")


class MonthlySalaryCalculation(BaseModel):
    """
    Schema for monthly salary calculation with leave deductions.
    
    Attributes:
        employee_id: Employee ID
        month: Month
        year: Year
        basic_salary: Basic salary amount
        hra: House rent allowance
        medical_allowance: Medical allowance
        conveyance_allowance: Conveyance allowance
        total_earnings: Total earnings before deductions
        daily_salary: Daily salary calculation
        unpaid_leave_days: Number of unpaid leave days
        leave_deduction: Amount deducted for unpaid leaves
        net_payable_amount: Final payable amount after deductions
        total_working_days: Total working days in month
        days_payable: Net payable days
    """
    employee_id: int
    month: int
    year: int
    basic_salary: float
    hra: float
    medical_allowance: float
    conveyance_allowance: float
    total_earnings: float
    daily_salary: float
    unpaid_leave_days: float
    half_day_leaves: float
    leave_deduction: float
    net_payable_amount: float
    total_working_days: int
    days_payable: float
    professional_tax: float = 0.0
    total_deductions: float = 0.0


class DetailedPayslipResponse(BaseModel):
    """
    Schema for detailed payslip response with leave calculations.
    
    Attributes:
        id: Payslip ID
        employee_id: Employee ID
        employee_name: Employee name
        month: Month
        year: Year
        earnings: Earnings breakdown with paid and actual amounts
        taxes_deductions: Taxes and deductions breakdown
        working_days: Working days calculations
        final_amount: Final payable amount
        processed_date: Processing timestamp
    """
    id: int
    employee_id: int
    employee_name: str
    month: int
    year: int
    earnings: Dict[str, Dict[str, float]]
    taxes_deductions: Dict[str, float]
    working_days: Dict[str, float]
    final_amount: float
    status: str
    processed_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeaveBasedSalaryProcessingRequest(BaseModel):
    """
    Schema for processing salary with leave deductions.
    
    Attributes:
        month: Month to process
        year: Year to process
        employee_ids: Specific employee IDs to process (optional, for bulk processing)
        dry_run: Whether to preview without actually processing
    """
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., description="Year")
    employee_ids: Optional[List[int]] = Field(default=None, description="Specific employee IDs to process")
    dry_run: bool = Field(default=False, description="Preview without processing")


class LeaveBasedSalaryProcessingResponse(BaseModel):
    """
    Schema for leave-based salary processing response.
    
    Attributes:
        success: Whether processing was successful
        message: Success/error message
        processed_count: Number of employees processed
        failed_count: Number of employees failed
        total_amount: Total amount processed
        processed_employees: List of processed employees with details
        failed_employees: List of failed employees with reasons
        processed_date: Processing timestamp
    """
    success: bool
    message: str
    month: int
    year: int
    processed_count: int
    failed_count: int
    total_amount: float
    processed_employees: List[Dict]
    failed_employees: List[Dict]
    processed_date: datetime


class SingleEmployeeLeaveProcessingRequest(BaseModel):
    """
    Schema for processing single employee salary with leave deductions.
    
    Attributes:
        unpaid_leave_days: Number of unpaid leave days
        half_day_leaves: Number of half-day unpaid leaves
        month: Month (optional, defaults to current)
        year: Year (optional, defaults to current)
    """
    unpaid_leave_days: float = Field(default=0.0, ge=0.0, description="Number of full unpaid leave days")
    half_day_leaves: float = Field(default=0.0, ge=0.0, description="Number of half-day unpaid leaves")
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month (1-12), defaults to current month")
    year: Optional[int] = Field(default=None, description="Year, defaults to current year")


class SingleEmployeeLeaveProcessingResponse(BaseModel):
    """
    Schema for single employee leave processing response.
    
    Attributes:
        success: Whether processing was successful
        message: Success/error message
        employee_id: Employee ID
        employee_name: Employee name
        payslip_id: Generated payslip ID
        calculation_details: Detailed calculation breakdown
        final_amount: Final payable amount
        month: Month of processing
        year: Year of processing
        processed_date: Processing timestamp
    """
    success: bool
    message: str
    employee_id: int
    employee_name: str
    payslip_id: Optional[int] = None
    calculation_details: Dict
    final_amount: float
    month: int
    year: int
    processed_date: datetime


class LeaveBalanceCheck(BaseModel):
    """
    Schema for checking employee leave balance for a month.
    
    Attributes:
        employee_id: Employee ID
        month: Month
        year: Year
        total_leave_days: Total leave days taken in month
        paid_leave_days: Paid leave days
        unpaid_leave_days: Unpaid leave days
        half_day_leaves: Half-day leaves
        leave_balance_remaining: Remaining leave balance
    """
    employee_id: int
    month: int
    year: int
    total_leave_days: float
    paid_leave_days: float
    unpaid_leave_days: float
    half_day_leaves: float
    leave_balance_remaining: float


class PayslipFormatResponse(BaseModel):
    """
    Schema for payslip in the exact format requested.
    
    Attributes:
        employee_name: Employee name
        month_year: Month and year
        earnings: Earnings section with paid and actual amounts
        taxes_deductions: Taxes and deductions
        working_days_summary: Working days summary
        net_payable: Final net payable amount
    """
    employee_name: str
    month_year: str
    earnings: Dict[str, Dict[str, str]]  # Format: {"Basic": {"paid": "12,292.00", "actual": "12,500.00"}}
    taxes_deductions: Dict[str, str]
    working_days_summary: Dict[str, str]
    net_payable: str

    class Config:
        from_attributes = True


class BulkLeaveProcessingRequest(BaseModel):
    """
    Schema for bulk leave processing with individual leave data.
    
    Attributes:
        month: Month to process
        year: Year to process
        employee_leave_data: List of employee leave data
        dry_run: Whether to preview without processing
    """
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., description="Year")
    employee_leave_data: List[Dict] = Field(..., description="List of employee leave data")
    dry_run: bool = Field(default=False, description="Preview without processing")


class MonthlyProcessingStatus(BaseModel):
    """
    Schema for monthly processing status.
    
    Attributes:
        month: Month
        year: Year
        status: Processing status
        total_employees: Total employees
        processed_employees: Processed employees
        pending_employees: Pending employees
        total_amount: Total processed amount
        last_updated: Last update timestamp
    """
    month: int
    year: int
    status: str
    total_employees: int
    processed_employees: int
    pending_employees: int
    total_amount: float
    last_updated: datetime
