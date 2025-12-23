"""
Monthly salary admin schemas for viewing employee salary data.

This module defines schemas for admin endpoints to view monthly salary data
including employee salary status and payment amounts.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime


class EmployeeMonthlySalaryData(BaseModel):
    """
    Schema for individual employee monthly salary data.
    
    Attributes:
        employee_id: Employee ID
        employee_name: Employee full name
        employee_email: Employee email
        employee_department: Employee department
        employee_designation: Employee designation
        net_salary: Employee's net monthly salary
        current_month_status: Payment status for current month
        current_month_amount: Amount paid for current month
        current_month_payslip_id: Payslip ID for current month
        last_paid_month: Last month where salary was paid
        last_paid_amount: Amount paid in last paid month
        total_paid_amount: Total amount paid across all months
        unpaid_months: List of months with unpaid salary
        pending_amount: Total pending amount across unpaid months
    """
    employee_id: int
    employee_name: str
    employee_email: str
    employee_department: str
    employee_designation: str
    net_salary: float
    
    # Current month data
    current_month_status: str  # "paid", "pending", "no_record"
    current_month_amount: Optional[float] = None
    current_month_payslip_id: Optional[int] = None
    
    # Historical data
    last_paid_month: Optional[int] = None
    last_paid_year: Optional[int] = None
    last_paid_amount: Optional[float] = None
    total_paid_amount: float = 0.0
    
    # Pending/unpaid data
    unpaid_months: List[dict] = Field(default_factory=list)  # [{"month": 1, "year": 2024, "amount": 50000}]
    pending_amount: float = 0.0
    
    # Additional info
    salary_exists: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class MonthlySalaryDataResponse(BaseModel):
    """
    Response schema for monthly salary data endpoint.
    
    Provides comprehensive monthly salary information for all employees
    including payment status and amounts.
    """
    success: bool
    message: str
    
    # Summary statistics
    total_employees: int
    paid_current_month: int
    pending_current_month: int
    no_salary_record: int
    total_pending_amount: float
    total_paid_amount: float
    
    # Employee data
    employees_data: List[EmployeeMonthlySalaryData]
    
    # Request details
    month: int
    year: int
    check_date: datetime
    
    class Config:
        from_attributes = True


class MonthlySalaryFilters(BaseModel):
    """
    Schema for filtering monthly salary data.
    
    Attributes:
        month: Month to filter (1-12), defaults to current month
        year: Year to filter, defaults to current year
        department: Filter by department
        status: Filter by payment status ("paid", "pending", "all")
        search: Search by employee name or email
    """
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month to filter (1-12)")
    year: Optional[int] = Field(default=None, description="Year to filter")
    department: Optional[str] = Field(default=None, description="Filter by department")
    status: Optional[str] = Field(default="all", description="Filter by status: paid, pending, all")
    search: Optional[str] = Field(default=None, description="Search by employee name or email")
    
    class Config:
        from_attributes = True


class EmployeeSalarySummary(BaseModel):
    """
    Schema for individual employee salary summary data.
    
    Attributes:
        employee_id: Employee ID
        employee_email: Employee email
        amount_paid: Amount paid for the month (null if unpaid)
        status: Payment status ("paid", "unpaid")
    """
    employee_id: int
    employee_email: str
    amount_paid: Optional[float] = None
    status: str  # "paid" or "unpaid"
    
    class Config:
        from_attributes = True


class MonthlySalarySummaryResponse(BaseModel):
    """
    Enhanced response schema for monthly salary summary endpoint.
    
    Provides both summary statistics and individual employee details.
    """
    success: bool
    summary: dict  # Keep existing summary structure for backward compatibility
    
    # Individual employee details
    employees: List[EmployeeSalarySummary]
    
    # Request details
    month: int
    year: int
    generated_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeSalaryDetail(BaseModel):
    """
    Schema for individual employee salary detail.
    
    Provides focused employee salary information including:
    - Employee ID
    - Employee Email
    - Amount Paid (null if unpaid)
    - Status (paid or unpaid)
    
    Attributes:
        employee_id: Employee ID
        email: Employee email address
        amount_paid: Amount paid for the month (null if unpaid)
        status: Payment status ("paid" or "unpaid")
    """
    employee_id: int
    email: str
    amount_paid: Optional[float] = None
    status: str  # "paid" or "unpaid"
    
    class Config:
        from_attributes = True


class MonthlySalaryEmployeeDetailsResponse(BaseModel):
    """
    Response schema for monthly salary employee details endpoint.
    
    Provides individual employee salary details with minimal information
    focused on employee identification and payment status.
    """
    success: bool
    month: int
    year: int
    employees: List[EmployeeSalaryDetail]
    generated_at: datetime
    
    class Config:
        from_attributes = True
