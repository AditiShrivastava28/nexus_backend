"""
Salary and payroll models.

This module defines models for salary structure and payslips.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Salary(Base):
    """
    Employee salary structure.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        annual_ctc: Annual cost to company
        monthly_gross: Monthly gross salary
        basic: Basic salary component
        hra: House rent allowance
        special_allowance: Special allowance
        pf_deduction: Provident fund deduction
        tax_deduction: Tax deduction
        total_deductions: Total deductions
        net_pay: Net take-home pay
        currency: Currency code
        last_paid: Last payment date
        next_pay_date: Next payment date
        next_increment_date: Next increment date
        increment_cycle: Increment cycle (annual, biannual)
    """
    __tablename__ = "salaries"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    annual_ctc = Column(Float, default=0)
    monthly_gross = Column(Float, default=0)
    basic = Column(Float, default=0)
    hra = Column(Float, default=0)
    special_allowance = Column(Float, default=0)
    pf_deduction = Column(Float, default=0)
    tax_deduction = Column(Float, default=0)
    total_deductions = Column(Float, default=0)
    net_pay = Column(Float, default=0)
    currency = Column(String(10), default="INR")
    last_paid = Column(Date)
    next_pay_date = Column(Date)
    next_increment_date = Column(Date)
    increment_cycle = Column(String(50), default="annual")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="salary")



class Payslip(Base):
    """
    Monthly payslip record.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        month: Month (1-12)
        year: Year
        amount: Net amount paid
        status: Payment status (paid, processing)
        file_url: URL to payslip PDF
        basic_paid: Basic salary paid amount
        basic_actual: Basic salary actual amount
        hra_paid: HRA paid amount
        hra_actual: HRA actual amount
        medical_allowance_paid: Medical allowance paid
        medical_allowance_actual: Medical allowance actual
        conveyance_allowance_paid: Conveyance allowance paid
        conveyance_allowance_actual: Conveyance allowance actual
        total_earnings_paid: Total earnings paid
        total_earnings_actual: Total earnings actual
        professional_tax: Professional tax deduction
        total_deductions: Total deductions
        actual_payable_days: Days actually payable
        total_working_days: Total working days in month
        loss_of_pay_days: Loss of pay days
        days_payable: Net payable days
        leave_deduction_amount: Amount deducted for unpaid leaves
    """
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, default=0)
    status = Column(String(50), default="processing")
    file_url = Column(String(500))
    
    # Salary components for detailed payslip
    basic_paid = Column(Float, default=0)
    basic_actual = Column(Float, default=0)
    hra_paid = Column(Float, default=0)
    hra_actual = Column(Float, default=0)
    medical_allowance_paid = Column(Float, default=0)
    medical_allowance_actual = Column(Float, default=0)
    conveyance_allowance_paid = Column(Float, default=0)
    conveyance_allowance_actual = Column(Float, default=0)
    total_earnings_paid = Column(Float, default=0)
    total_earnings_actual = Column(Float, default=0)
    professional_tax = Column(Float, default=0)
    total_deductions = Column(Float, default=0)
    
    # Working days calculations
    actual_payable_days = Column(Float, default=0)
    total_working_days = Column(Float, default=0)
    loss_of_pay_days = Column(Float, default=0)
    days_payable = Column(Float, default=0)
    leave_deduction_amount = Column(Float, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    employee = relationship("Employee", back_populates="payslips")


class MonthlySalaryProcessing(Base):
    """
    Monthly salary processing tracking.
    
    Attributes:
        id: Primary key
        month: Month (1-12)
        year: Year
        processed_date: When the processing was done
        total_employees: Total employees processed
        successful_payments: Number of successful payments
        failed_payments: Number of failed payments
        total_processed_amount: Total amount processed
        status: Processing status (pending, completed, failed)
    """
    __tablename__ = "monthly_salary_processing"
    
    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    processed_date = Column(DateTime(timezone=True))
    total_employees = Column(Integer, default=0)
    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)
    total_processed_amount = Column(Float, default=0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
