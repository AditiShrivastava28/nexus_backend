"""
Salary-related Pydantic schemas.

This module defines schemas for salary and payslip operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


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
    """
    id: int
    month: int
    year: int
    amount: float
    status: str

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
