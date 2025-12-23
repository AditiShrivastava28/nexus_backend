"""
Salary processing schemas for employee salary payment processing.

This module defines schemas for processing employee salary payments with payslip generation
and monthly salary tracking to prevent duplicate payments.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EmployeeSalaryProcessingRequest(BaseModel):
    """
    Request schema for processing employee salary payment.
    
    This schema is used for processing salary for a specific employee, month, and year
    while preventing duplicate payments for the same period.
    """
    month: int = Field(..., ge=1, le=12, description="Month for salary processing (1-12)")
    year: int = Field(..., description="Year for salary processing")
    amount: Optional[float] = Field(default=None, ge=0, description="Amount to process (defaults to employee's net pay)")
    custom_deductions: Optional[float] = Field(default=0.0, ge=0, description="Additional custom deductions")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes for this payment")


class PreviousPayslipInfo(BaseModel):
    """
    Schema for previous payslip information when duplicate is detected.
    """
    payslip_id: int
    amount: float
    processed_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class EmployeeSalaryProcessingResponse(BaseModel):
    """
    Response schema for employee salary processing.
    
    Returns detailed information about the salary processing including
    payslip generation, monthly processing record, and duplicate prevention status.
    """
    success: bool
    message: str
    
    # Employee information
    employee_id: int
    employee_name: str
    employee_email: str
    
    # Processing details
    month: int
    year: int
    amount_processed: float
    status: str  # "paid", "error", "duplicate_prevented"
    processed_at: datetime
    
    # Record IDs
    payslip_id: Optional[int] = None
    monthly_processing_id: Optional[int] = None
    
    # Duplicate prevention
    duplicate_prevented: bool = False
    previous_payslip_info: Optional[PreviousPayslipInfo] = None
    
    # Additional details
    payslip_details: Optional[dict] = None
    monthly_processing_details: Optional[dict] = None
    
    class Config:
        from_attributes = True


class BulkSalaryProcessingRequest(BaseModel):
    """
    Request schema for bulk salary processing for multiple employees.
    
    Process salary for multiple employees for the same month and year.
    """
    month: int = Field(..., ge=1, le=12, description="Month for salary processing (1-12)")
    year: int = Field(..., description="Year for salary processing")
    employee_ids: Optional[list[int]] = Field(default=None, description="Specific employee IDs to process (None = all active employees)")
    custom_deductions: Optional[float] = Field(default=0.0, ge=0, description="Additional custom deductions for all employees")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes for this bulk payment")
    skip_duplicates: bool = Field(default=True, description="Skip employees who already have paid payslips for this month/year")


class BulkProcessingEmployeeResult(BaseModel):
    """
    Schema for individual employee result in bulk processing.
    """
    employee_id: int
    employee_name: str
    success: bool
    message: str
    payslip_id: Optional[int] = None
    amount_processed: Optional[float] = None
    duplicate_prevented: bool = False
    
    class Config:
        from_attributes = True


class BulkSalaryProcessingResponse(BaseModel):
    """
    Response schema for bulk salary processing.
    
    Returns summary and individual results for bulk salary processing operations.
    """
    success: bool
    message: str
    
    # Summary statistics
    total_employees: int
    processed_count: int
    failed_count: int
    skipped_count: int  # Employees skipped due to duplicates
    
    # Individual results
    processed_employees: list[BulkProcessingEmployeeResult]
    failed_employees: list[BulkProcessingEmployeeResult]
    skipped_employees: list[BulkProcessingEmployeeResult]  # Duplicates
    
    # Processing details
    month: int
    year: int
    total_amount_processed: float
    processed_at: datetime
    
    class Config:
        from_attributes = True


class SalaryProcessingStatusCheck(BaseModel):
    """
    Schema for checking salary processing status for an employee.
    
    Check if salary has been processed for a specific employee and month/year.
    """
    employee_id: int
    month: int
    year: int
    
    # Status information
    has_paid_payslip: bool = False
    payslip_id: Optional[int] = None
    payslip_amount: Optional[float] = None
    payslip_status: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    # Monthly processing status
    monthly_processing_record_exists: bool = False
    monthly_processing_id: Optional[int] = None
    
    # Employee details
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    
    class Config:
        from_attributes = True
