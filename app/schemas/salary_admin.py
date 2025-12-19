
"""
Admin-specific salary-related Pydantic schemas.

This module defines schemas for admin salary CRUD operations.
"""


from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class SalaryCreate(BaseModel):
    """
    Schema for creating employee salary.
    
    Attributes:
        employee_id: Employee ID (required)
        annual_ctc: Annual cost to company
        monthly_gross: Monthly gross salary
        basic: Basic salary component
        hra: House rent allowance
        special_allowance: Special allowance
        pf_deduction: Provident fund deduction
        tax_deduction: Tax deduction
        total_deductions: Total deductions (auto-calculated if not provided)
        net_pay: Net take-home pay (auto-calculated if not provided)
        currency: Currency code
        next_pay_date: Next payment date
        next_increment_date: Next increment date
        increment_cycle: Increment cycle (annual, biannual)
    """
    employee_id: int = Field(..., description="Employee ID")
    annual_ctc: float = Field(default=0.0, description="Annual cost to company")
    monthly_gross: float = Field(default=0.0, description="Monthly gross salary")
    basic: float = Field(default=0.0, description="Basic salary component")
    hra: float = Field(default=0.0, description="House rent allowance")
    special_allowance: float = Field(default=0.0, description="Special allowance")
    pf_deduction: float = Field(default=0.0, description="Provident fund deduction")
    tax_deduction: float = Field(default=0.0, description="Tax deduction")
    total_deductions: Optional[float] = Field(default=None, description="Total deductions (auto-calculated if not provided)")
    net_pay: Optional[float] = Field(default=None, description="Net take-home pay (auto-calculated if not provided)")
    currency: str = Field(default="INR", description="Currency code")
    next_pay_date: Optional[date] = Field(default=None, description="Next payment date")
    next_increment_date: Optional[date] = Field(default=None, description="Next increment date")
    increment_cycle: str = Field(default="annual", description="Increment cycle")




class SalaryUpdate(BaseModel):
    """
    Schema for updating employee salary.
    
    All fields are optional for partial updates.
    
    Attributes:
        annual_ctc: Annual cost to company (None = not provided, 0 = explicitly set to 0)
        monthly_gross: Monthly gross salary (None = not provided, 0 = explicitly set to 0)
        basic: Basic salary component (None = not provided, 0 = explicitly set to 0)
        hra: House rent allowance (None = not provided, 0 = explicitly set to 0)
        special_allowance: Special allowance (None = not provided, 0 = explicitly set to 0)
        pf_deduction: Provident fund deduction (None = not provided, 0 = explicitly set to 0)
        tax_deduction: Tax deduction (None = not provided, 0 = explicitly set to 0)
        total_deductions: Total deductions (None = not provided, 0 = explicitly set to 0)
        net_pay: Net take-home pay (None = not provided, 0 = explicitly set to 0)
        currency: Currency code
        next_pay_date: Next payment date
        next_increment_date: Next increment date
        increment_cycle: Increment cycle
    """
    annual_ctc: Optional[float] = Field(default=None, description="Annual cost to company (None = not provided, 0 = explicitly set to 0)")
    monthly_gross: Optional[float] = Field(default=None, description="Monthly gross salary (None = not provided, 0 = explicitly set to 0)")
    basic: Optional[float] = Field(default=None, description="Basic salary component (None = not provided, 0 = explicitly set to 0)")
    hra: Optional[float] = Field(default=None, description="House rent allowance (None = not provided, 0 = explicitly set to 0)")
    special_allowance: Optional[float] = Field(default=None, description="Special allowance (None = not provided, 0 = explicitly set to 0)")
    pf_deduction: Optional[float] = Field(default=None, description="Provident fund deduction (None = not provided, 0 = explicitly set to 0)")
    tax_deduction: Optional[float] = Field(default=None, description="Tax deduction (None = not provided, 0 = explicitly set to 0)")
    total_deductions: Optional[float] = Field(default=None, description="Total deductions (None = not provided, 0 = explicitly set to 0)")
    net_pay: Optional[float] = Field(default=None, description="Net take-home pay (None = not provided, 0 = explicitly set to 0)")
    currency: Optional[str] = Field(default=None, description="Currency code")
    next_pay_date: Optional[date] = Field(default=None, description="Next payment date")
    next_increment_date: Optional[date] = Field(default=None, description="Next increment date")
    increment_cycle: Optional[str] = Field(default=None, description="Increment cycle")

class SalaryResponse(BaseModel):
    """
    Schema for salary response.
    
    Attributes:
        id: Salary record ID
        employee_id: Employee ID
        employee_name: Employee name
        employee_email: Employee email
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
        increment_cycle: Increment cycle
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    id: int
    employee_id: int
    employee_name: str
    employee_email: str
    annual_ctc: float
    monthly_gross: float
    basic: float
    hra: float
    special_allowance: float
    pf_deduction: float
    tax_deduction: float
    total_deductions: float
    net_pay: float
    currency: str
    last_paid: Optional[date] = None
    next_pay_date: Optional[date] = None
    next_increment_date: Optional[date] = None
    increment_cycle: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalaryListResponse(BaseModel):
    """
    Schema for salary list response with pagination.
    
    Attributes:
        salaries: List of salary records
        total: Total number of salary records
        page: Current page number
        per_page: Records per page
        pages: Total number of pages
    """
    salaries: list[SalaryResponse]
    total: int
    page: int
    per_page: int
    pages: int

    class Config:
        from_attributes = True


class SalaryCalculationRequest(BaseModel):
    """
    Schema for salary calculation requests.
    
    Attributes:
        basic: Basic salary
        hra: House rent allowance
        special_allowance: Special allowance
        pf_deduction: PF deduction
        tax_deduction: Tax deduction
    """
    basic: float
    hra: float
    special_allowance: float
    pf_deduction: float
    tax_deduction: float



class SalaryCalculationResponse(BaseModel):
    """
    Schema for salary calculation response.
    
    Attributes:
        monthly_gross: Calculated monthly gross
        total_deductions: Calculated total deductions
        net_pay: Calculated net pay
        annual_ctc: Calculated annual CTC
    """
    monthly_gross: float
    total_deductions: float
    net_pay: float
    annual_ctc: float





class SalaryCreateAdmin(BaseModel):
    """
    Schema for creating/updating employee salary by admin.
    
    This schema is used for the upsert endpoint where employee_id is passed as path parameter.
    
    Attributes:
        annual_ctc: Annual cost to company (None = not provided)
        monthly_gross: Monthly gross salary (None = not provided)
        basic: Basic salary component (None = not provided, 0 = explicitly set to 0)
        hra: House rent allowance (None = not provided, 0 = explicitly set to 0)
        special_allowance: Special allowance (None = not provided, 0 = explicitly set to 0)
        pf_deduction: Provident fund deduction (None = not provided, 0 = explicitly set to 0)
        tax_deduction: Tax deduction (None = not provided, 0 = explicitly set to 0)
        total_deductions: Total deductions (auto-calculated if not provided)
        net_pay: Net take-home pay (auto-calculated if not provided)
        currency: Currency code
        next_pay_date: Next payment date
        next_increment_date: Next increment date
        increment_cycle: Increment cycle (annual, biannual)
        auto_calculate: Enable auto-calculation from annual CTC
        city: City for HRA calculation (metro/non-metro)
        state: State for professional tax calculation
        basic_percentage: Custom basic salary percentage (optional)
        calculate_tax: Whether to auto-calculate income tax
        calculate_pf: Whether to auto-calculate PF deduction
        calculate_hra: Whether to auto-calculate HRA
        overrides: Manual overrides for specific components
    """
    annual_ctc: Optional[float] = Field(default=None, description="Annual cost to company (None = not provided)")
    monthly_gross: Optional[float] = Field(default=None, description="Monthly gross salary (None = not provided)")
    basic: Optional[float] = Field(default=None, description="Basic salary component (None = not provided, 0 = explicitly set to 0)")
    hra: Optional[float] = Field(default=None, description="House rent allowance (None = not provided, 0 = explicitly set to 0)")
    special_allowance: Optional[float] = Field(default=None, description="Special allowance (None = not provided, 0 = explicitly set to 0)")
    pf_deduction: Optional[float] = Field(default=None, description="Provident fund deduction (None = not provided, 0 = explicitly set to 0)")
    tax_deduction: Optional[float] = Field(default=None, description="Tax deduction (None = not provided, 0 = explicitly set to 0)")
    total_deductions: Optional[float] = Field(default=None, description="Total deductions (auto-calculated if not provided)")
    net_pay: Optional[float] = Field(default=None, description="Net take-home pay (auto-calculated if not provided)")
    currency: str = Field(default="INR", description="Currency code")
    next_pay_date: Optional[date] = Field(default=None, description="Next payment date")
    next_increment_date: Optional[date] = Field(default=None, description="Next increment date")
    increment_cycle: str = Field(default="annual", description="Increment cycle")
    
    # Auto-calculation fields
    auto_calculate: bool = Field(default=False, description="Enable auto-calculation from annual CTC")
    city: str = Field(default="default", description="City for HRA calculation (metro/non-metro)")
    state: str = Field(default="default", description="State for professional tax calculation")
    basic_percentage: Optional[float] = Field(default=None, description="Custom basic salary percentage (0.0-1.0)")
    calculate_tax: bool = Field(default=True, description="Whether to auto-calculate income tax")
    calculate_pf: bool = Field(default=True, description="Whether to auto-calculate PF deduction")
    calculate_hra: bool = Field(default=True, description="Whether to auto-calculate HRA")
    overrides: Optional[dict] = Field(default=None, description="Manual overrides for specific components")


class AutoSalaryCalculationRequest(BaseModel):
    """
    Schema for auto-calculation request from annual CTC.
    
    Attributes:
        annual_ctc: Annual cost to company
        city: City for HRA calculation
        state: State for professional tax calculation
        basic_percentage: Custom basic salary percentage
        include_employer_pf: Whether to include employer PF in CTC calculation
    """
    annual_ctc: float = Field(..., gt=0, description="Annual cost to company")
    city: str = Field(default="default", description="City for HRA calculation")
    state: str = Field(default="default", description="State for professional tax calculation")
    basic_percentage: Optional[float] = Field(default=None, ge=0.3, le=0.6, description="Basic salary percentage (0.3-0.6)")
    include_employer_pf: bool = Field(default=False, description="Include employer PF in CTC calculation")


class AutoSalaryCalculationResponse(BaseModel):
    """
    Schema for auto-calculation response.
    
    Attributes:
        calculated_components: All calculated salary components
        calculation_details: Detailed breakdown of calculations
        validation_issues: Any validation issues found
        formatted_breakdown: Human-readable breakdown
    """
    annual_ctc: float
    monthly_gross: float
    basic: float
    hra: float
    special_allowance: float
    pf_deduction: float
    tax_deduction: float
    professional_tax: float
    total_deductions: float
    net_pay: float
    employer_pf: float
    calculation_details: dict
    validation_issues: list[str] = Field(default_factory=list)
    formatted_breakdown: dict


class SalaryCalculationOptions(BaseModel):
    """
    Schema for salary calculation configuration options.
    
    Attributes:
        city: City classification
        state: State for professional tax
        basic_percentage: Basic salary percentage
        include_employer_pf: Include employer PF in CTC
        calculation_policies: Custom calculation policies
    """
    city: str = Field(default="default", description="City for HRA calculation")
    state: str = Field(default="default", description="State for professional tax calculation")
    basic_percentage: float = Field(default=0.45, ge=0.3, le=0.6, description="Basic salary percentage")
    include_employer_pf: bool = Field(default=False, description="Include employer PF in CTC")
    calculation_policies: Optional[dict] = Field(default=None, description="Custom calculation policies")


class SalaryValidationRequest(BaseModel):
    """
    Schema for salary structure validation request.
    
    Attributes:
        basic: Basic salary
        hra: House rent allowance
        special_allowance: Special allowance
        pf_deduction: PF deduction
        tax_deduction: Tax deduction
        annual_ctc: Annual CTC for validation
    """
    basic: float = Field(..., ge=0, description="Basic salary")
    hra: float = Field(default=0, ge=0, description="House rent allowance")
    special_allowance: float = Field(default=0, ge=0, description="Special allowance")
    pf_deduction: float = Field(default=0, ge=0, description="PF deduction")
    tax_deduction: float = Field(default=0, ge=0, description="Tax deduction")
    annual_ctc: float = Field(..., gt=0, description="Annual CTC")


class SalaryValidationResponse(BaseModel):
    """
    Schema for salary validation response.
    
    Attributes:
        is_valid: Whether the salary structure is valid
        issues: List of validation issues
        recommendations: Suggested improvements
        compliance_score: Compliance score (0-100)
    """
    is_valid: bool
    issues: list[str]
    recommendations: list[str] = Field(default_factory=list)
    compliance_score: float = Field(ge=0, le=100)
    basic_percentage: float
    hra_percentage: Optional[float] = None
    deductions_percentage: float
