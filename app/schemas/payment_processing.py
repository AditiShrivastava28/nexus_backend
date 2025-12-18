"""
Payment processing related Pydantic schemas.

This module defines schemas for salary payment processing operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime




class SinglePaymentProcessRequest(BaseModel):
    """
    Schema for processing single employee payment.
    
    Note: employee_id is taken from URL path parameter, not from request body.
    Month and year are optional - defaults to current month/year if not provided.
    
    Attributes:
        month: Month for which payment is being processed (optional)
        year: Year for which payment is being processed (optional)
    """
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month (1-12), defaults to current month")
    year: Optional[int] = Field(default=None, description="Year, defaults to current year")


class SinglePaymentProcessResponse(BaseModel):
    """
    Schema for single payment processing response.
    
    Attributes:
        success: Whether the payment was processed successfully
        message: Success/error message
        employee_id: Employee ID
        employee_name: Employee name
        payslip_id: Updated payslip ID
        amount: Amount paid
        month: Month of payment
        year: Year of payment
        processed_at: Payment processing timestamp
    """
    success: bool
    message: str
    employee_id: int
    employee_name: str
    payslip_id: int
    amount: float
    month: int
    year: int
    processed_at: datetime


class BulkPaymentProcessRequest(BaseModel):
    """
    Schema for bulk payment processing request.
    
    Attributes:
        month: Month to process payments for
        year: Year to process payments for
        dry_run: Whether to just preview without actually processing
    """
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., description="Year")
    dry_run: bool = Field(default=False, description="Preview without processing")


class PaymentProcessSummary(BaseModel):
    """
    Schema for payment processing summary.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        employee_email: Employee email
        payslip_id: Payslip ID
        amount: Amount paid
        status: Payment status after processing
    """
    employee_id: int
    employee_name: str
    employee_email: str
    payslip_id: int
    amount: float
    status: str


class BulkPaymentProcessResponse(BaseModel):
    """
    Schema for bulk payment processing response.
    
    Attributes:
        success: Whether the bulk processing was successful
        message: Summary message
        total_employees: Total number of employees processed
        processed_count: Number of employees whose payments were processed
        failed_count: Number of employees who failed processing
        processed_employees: List of successfully processed employees
        failed_employees: List of failed employees with reasons
        processed_at: Processing timestamp
    """
    success: bool
    message: str
    total_employees: int
    processed_count: int
    failed_count: int
    processed_employees: List[PaymentProcessSummary]
    failed_employees: List[dict]
    processed_at: datetime


class UnpaidEmployee(BaseModel):
    """
    Schema for unpaid employee information.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee name
        employee_email: Employee email
        department: Employee department
        pending_payslips: List of pending payslips
        total_pending_amount: Total amount pending
    """
    employee_id: int
    employee_name: str
    employee_email: str
    department: str
    pending_payslips: List[dict]
    total_pending_amount: float


class UnpaidSalariesCheckResponse(BaseModel):
    """
    Schema for unpaid salaries check response.
    
    Attributes:
        total_employees: Total number of employees checked
        paid_employees: Number of employees with all payments up to date
        unpaid_employees: Number of employees with pending payments
        unpaid_employee_details: List of unpaid employees with details
        check_date: Date when the check was performed
    """
    total_employees: int
    paid_employees: int
    unpaid_employees: int
    unpaid_employee_details: List[UnpaidEmployee]
    check_date: date


class PayslipStatusUpdate(BaseModel):
    """
    Schema for payslip status update.
    
    Attributes:
        payslip_id: Payslip ID
        employee_id: Employee ID
        month: Month
        year: Year
        old_status: Previous status
        new_status: New status
        amount: Payslip amount
        updated_at: Update timestamp
    """
    payslip_id: int
    employee_id: int
    month: int
    year: int
    old_status: str
    new_status: str
    amount: float
    updated_at: datetime
