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
    """
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, default=0)
    status = Column(String(50), default="processing")
    file_url = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="payslips")
