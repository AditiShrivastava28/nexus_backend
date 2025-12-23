"""
Salary calculation service based on Indian salary laws.

This module provides comprehensive salary calculation functionality including
PF, income tax, professional tax calculations following Indian regulations.
"""


from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from datetime import date

# Import the response models
from ..schemas.admin_salary_apis import (
    CTCBreakdownResponse,
    MonthlySalaryValidationResponse,
    PayslipGenerationResponse
)


@dataclass
class SalaryComponents:
    """Data class to hold all salary components."""
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
    calculation_details: Dict[str, any]


class IndianSalaryCalculator:
    """
    Calculator for Indian salary components based on current laws and regulations.
    
    Implements calculations for:
    - Basic salary (percentage of CTC)
    - HRA (city-based percentage)
    - PF deductions (with cap)
    - Income tax (current slabs)
    - Professional tax (state-based)
    """
    
    # Constants for calculations
    BASIC_PERCENTAGE = 0.45  # 45% of CTC for basic salary
    HRA_METRO_PERCENTAGE = 0.50  # 50% for metro cities
    HRA_NON_METRO_PERCENTAGE = 0.40  # 40% for non-metro cities
    PF_EMPLOYEE_RATE = 0.12  # 12% employee contribution
    PF_EMPLOYER_RATE = 0.12  # 12% employer contribution
    PF_CAP = 15000  # ₹15,000 cap for PF calculation
    STANDARD_DEDUCTION = 50000  # ₹50,000 standard deduction
    PROFESSIONAL_TAX_CAP = 2500  # ₹2,500 annual cap
    
    # Income Tax Slabs for FY 2023-24
    TAX_SLABS = [
        (250000, 0.00),      # Up to ₹2.5L: 0%
        (500000, 0.05),      # ₹2.5L - ₹5L: 5%
        (1000000, 0.20),     # ₹5L - ₹10L: 20%
        (float('inf'), 0.30) # Above ₹10L: 30%
    ]
    
    # Section 87A rebate
    REBATE_LIMIT = 500000  # ₹5L limit for rebate
    REBATE_AMOUNT = 12500  # ₹12,500 rebate
    
    # Metro cities in India
    METRO_CITIES = {
        'delhi', 'mumbai', 'chennai', 'kolkata', 
        'bangalore', 'hyderabad', 'pune', 'gurgaon', 
        'noida', 'faridabad', 'ghaziabad'
    }
    
    # Professional tax by state
    PROFESSIONAL_TAX_BY_STATE = {
        'maharashtra': 2500,
        'karnataka': 2500,
        'west bengal': 2500,
        'bihar': 2500,
        'assam': 2500,
        'kerala': 2500,
        'odisha': 2500,
        'punjab': 2500,
        'rajasthan': 2500,
        'tamil nadu': 2500,
        'telangana': 2500,
        'uttar pradesh': 2500,
        'madhya pradesh': 2500,
        'gujarat': 2400,
        'andhra pradesh': 2400,
        'haryana': 2000,
        'jharkhand': 2000,
        'uttarakhand': 2000,
        'chhattisgarh': 2000,
        'goa': 1200,
        'default': 2400
    }

    @classmethod
    def calculate_from_ctc(
        cls,
        annual_ctc: float,
        city: str = "default",
        state: str = "default",
        basic_percentage: Optional[float] = None,
        include_employer_pf: bool = False
    ) -> SalaryComponents:
        """
        Calculate all salary components from annual CTC.
        
        Args:
            annual_ctc: Annual Cost to Company
            city: City name for HRA calculation
            state: State name for professional tax
            basic_percentage: Custom basic percentage (optional)
            include_employer_pf: Whether to include employer PF in CTC
            
        Returns:
            SalaryComponents: Calculated salary components
        """
        # Validate input
        if annual_ctc <= 0:
            raise ValueError("Annual CTC must be positive")
        
        # Calculate basic salary
        basic_percentage = basic_percentage or cls.BASIC_PERCENTAGE
        basic = (annual_ctc * basic_percentage) / 12
        
        # Calculate HRA based on city type
        city_lower = city.lower() if city else "default"
        hra_percentage = cls.HRA_METRO_PERCENTAGE if city_lower in cls.METRO_CITIES else cls.HRA_NON_METRO_PERCENTAGE
        hra = (basic * hra_percentage)
        
        # Calculate employer PF contribution
        basic_for_pf = min(basic, cls.PF_CAP)
        employer_pf = basic_for_pf * cls.PF_EMPLOYER_RATE
        
        # Calculate special allowance (remainder after basic, HRA, and employer PF if included)
        if include_employer_pf:
            special_allowance = annual_ctc - (basic * 12) - (hra * 12) - (employer_pf * 12)
        else:
            special_allowance = annual_ctc - (basic * 12) - (hra * 12)
        
        special_allowance = special_allowance / 12  # Convert to monthly
        
        # Calculate monthly gross
        monthly_gross = basic + hra + special_allowance
        
        # Calculate PF deduction
        pf_deduction = basic_for_pf * cls.PF_EMPLOYEE_RATE
        
        # Calculate income tax
        annual_gross = monthly_gross * 12
        tax_deduction = cls._calculate_income_tax(annual_gross)
        tax_deduction = tax_deduction / 12  # Convert to monthly
        
        # Calculate professional tax
        professional_tax = cls._calculate_professional_tax(state)
        
        # Calculate total deductions
        total_deductions = pf_deduction + tax_deduction + professional_tax
        
        # Calculate net pay
        net_pay = monthly_gross - total_deductions
        
        # Prepare calculation details for transparency
        calculation_details = {
            "basic_percentage": basic_percentage,
            "hra_percentage": hra_percentage,
            "city_classification": "metro" if city_lower in cls.METRO_CITIES else "non-metro",
            "pf_cap_applied": basic > cls.PF_CAP,
            "standard_deduction_applied": True,
            "professional_tax_state": state,
            "annual_gross_income": annual_gross,
            "tax_slab_applied": cls._get_tax_slab(annual_gross)
        }
        
        return SalaryComponents(
            annual_ctc=annual_ctc,
            monthly_gross=monthly_gross,
            basic=basic,
            hra=hra,
            special_allowance=special_allowance,
            pf_deduction=pf_deduction,
            tax_deduction=tax_deduction,
            professional_tax=professional_tax,
            total_deductions=total_deductions,
            net_pay=net_pay,
            employer_pf=employer_pf,
            calculation_details=calculation_details
        )

    @classmethod
    def calculate_tax_only(cls, annual_income: float) -> Tuple[float, Dict]:
        """
        Calculate only income tax for given annual income.
        
        Args:
            annual_income: Annual gross income
            
        Returns:
            Tuple[float, Dict]: (annual_tax, calculation_details)
        """
        tax, details = cls._calculate_income_tax_with_details(annual_income)
        return tax, details

    @classmethod
    def calculate_pf_only(cls, basic_salary: float) -> Tuple[float, float]:
        """
        Calculate only PF deductions.
        
        Args:
            basic_salary: Basic salary amount
            
        Returns:
            Tuple[float, float]: (employee_pf, employer_pf)
        """
        basic_for_pf = min(basic_salary, cls.PF_CAP)
        employee_pf = basic_for_pf * cls.PF_EMPLOYEE_RATE
        employer_pf = basic_for_pf * cls.PF_EMPLOYER_RATE
        
        return employee_pf, employer_pf

    @classmethod
    def _calculate_income_tax(cls, annual_income: float) -> float:
        """Calculate annual income tax."""
        tax, _ = cls._calculate_income_tax_with_details(annual_income)
        return tax

    @classmethod
    def _calculate_income_tax_with_details(cls, annual_income: float) -> Tuple[float, Dict]:
        """Calculate income tax with detailed breakdown."""
        # Apply standard deduction
        taxable_income = max(0, annual_income - cls.STANDARD_DEDUCTION)
        
        tax = 0
        previous_limit = 0
        
        for limit, rate in cls.TAX_SLABS:
            if taxable_income > limit:
                # Full slab applies
                slab_amount = limit - previous_limit
                tax += slab_amount * rate
                previous_limit = limit
            else:
                # Partial slab applies
                slab_amount = taxable_income - previous_limit
                tax += slab_amount * rate
                break
        
        # Apply rebate under Section 87A
        rebate = 0
        if taxable_income <= cls.REBATE_LIMIT:
            rebate = min(tax, cls.REBATE_AMOUNT)
        
        tax = max(0, tax - rebate)
        
        details = {
            "annual_income": annual_income,
            "taxable_income": taxable_income,
            "standard_deduction": cls.STANDARD_DEDUCTION,
            "gross_tax": tax + rebate,
            "rebate_applied": rebate,
            "net_tax": tax,
            "rebate_limit": cls.REBATE_LIMIT,
            "rebate_amount": cls.REBATE_AMOUNT
        }
        
        return tax, details

    @classmethod
    def _calculate_professional_tax(cls, state: str) -> float:
        """Calculate monthly professional tax."""
        state_lower = state.lower() if state else "default"
        annual_tax = cls.PROFESSIONAL_TAX_BY_STATE.get(state_lower, cls.PROFESSIONAL_TAX_BY_STATE['default'])
        return annual_tax / 12  # Convert to monthly

    @classmethod
    def _get_tax_slab(cls, annual_income: float) -> str:
        """Get the applicable tax slab description."""
        if annual_income <= 250000:
            return "0% (Up to ₹2.5L)"
        elif annual_income <= 500000:
            return "5% (₹2.5L - ₹5L)"
        elif annual_income <= 1000000:
            return "20% (₹5L - ₹10L)"
        else:
            return "30% (Above ₹10L)"

    @classmethod
    def is_metro_city(cls, city: str) -> bool:
        """Check if a city is classified as metro."""
        return city.lower() in cls.METRO_CITIES if city else False

    @classmethod
    def get_supported_cities(cls) -> list:
        """Get list of supported metro cities."""
        return list(cls.METRO_CITIES)

    @classmethod
    def get_supported_states(cls) -> list:
        """Get list of supported states for professional tax."""
        return list(cls.PROFESSIONAL_TAX_BY_STATE.keys())



class SalaryCalculationService:
    """
    Service class that provides salary calculation functionality.
    
    This class wraps the IndianSalaryCalculator and provides additional
    convenience methods and validation.
    """
    
    def __init__(self):
        self.calculator = IndianSalaryCalculator()
    
    def auto_calculate_from_ctc(
        self,
        annual_ctc: float,
        city: str = "default",
        state: str = "default",
        overrides: Optional[Dict[str, float]] = None
    ) -> SalaryComponents:
        """
        Auto-calculate salary from CTC with optional overrides.
        
        Args:
            annual_ctc: Annual CTC
            city: City for HRA calculation
            state: State for professional tax
            overrides: Dictionary of values to override (e.g., {'basic': 30000})
            
        Returns:
            SalaryComponents: Calculated components
        """
        # Get base calculation
        components = self.calculator.calculate_from_ctc(annual_ctc, city, state)
        
        # Apply overrides if provided
        if overrides:
            for field, value in overrides.items():
                if hasattr(components, field) and value is not None:
                    setattr(components, field, value)
            
            # Recalculate dependent fields if basic components changed
            if any(field in overrides for field in ['basic', 'hra', 'special_allowance']):
                components.monthly_gross = components.basic + components.hra + components.special_allowance
            
            if any(field in overrides for field in ['pf_deduction', 'tax_deduction', 'professional_tax']):
                components.total_deductions = components.pf_deduction + components.tax_deduction + components.professional_tax
            
            # Recalculate net pay
            components.net_pay = components.monthly_gross - components.total_deductions
        
        return components
    
    def _validate_salary_structure_internal(self, components: SalaryComponents) -> Tuple[bool, list]:
        """
        Internal validation method that takes SalaryComponents object.
        
        Args:
            components: SalaryComponents to validate
            
        Returns:
            Tuple[bool, list]: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if basic salary is reasonable (40-50% of CTC)
        basic_percentage = (components.basic * 12) / components.annual_ctc
        if basic_percentage < 0.35:
            issues.append("Basic salary is less than 35% of CTC (unusual)")
        elif basic_percentage > 0.60:
            issues.append("Basic salary is more than 60% of CTC (unusual)")
        
        # Check if HRA is reasonable
        if components.hra > 0:
            hra_percentage = components.hra / components.basic
            if hra_percentage > 0.60:
                issues.append("HRA is more than 60% of basic salary (unusual)")
        
        # Check if net pay is positive
        if components.net_pay <= 0:
            issues.append("Net pay is not positive")
        
        # Check PF deduction
        if components.pf_deduction > components.basic * 0.12:
            issues.append("PF deduction exceeds 12% of basic salary")
        
        return len(issues) == 0, issues
    
    def validate_salary_structure(self, components: SalaryComponents) -> Tuple[bool, list]:
        """
        Validate salary structure for compliance.
        
        Args:
            components: Salary components to validate
            
        Returns:
            Tuple[bool, list]: (is_valid, list_of_issues)
        """
        return self._validate_salary_structure_internal(components)


    def calculate_from_annual_ctc_or_monthly_gross(
        self,
        annual_ctc: float = 0,
        monthly_gross: float = 0,
        options: Optional[Dict] = None
    ):
        """
        Auto-calculate salary components from annual CTC or monthly gross.
        
        This method provides a convenient interface for auto-calculation
        from either annual CTC or monthly gross salary.
        
        Args:
            annual_ctc: Annual Cost to Company (preferred if both provided)
            monthly_gross: Monthly gross salary
            options: Additional calculation options (city, state, etc.)
            
        Returns:
            AutoSalaryCalculationResponse: Calculated components
        """
        from ..schemas.salary_admin import AutoSalaryCalculationResponse
        
        if options is None:
            options = {}
        
        # Get calculation parameters from options
        city = options.get('city', 'default')
        state = options.get('state', 'default')
        basic_percentage = options.get('basic_percentage')
        include_employer_pf = options.get('include_employer_pf', False)
        
        # Determine primary calculation input
        if annual_ctc > 0:
            # Calculate from annual CTC
            components = self.calculator.calculate_from_ctc(
                annual_ctc=annual_ctc,
                city=city,
                state=state,
                basic_percentage=basic_percentage,
                include_employer_pf=include_employer_pf
            )
        elif monthly_gross > 0:
            # Convert monthly gross to annual CTC and calculate
            annual_ctc_from_monthly = monthly_gross * 12
            components = self.calculator.calculate_from_ctc(
                annual_ctc=annual_ctc_from_monthly,
                city=city,
                state=state,
                basic_percentage=basic_percentage,
                include_employer_pf=include_employer_pf
            )
        else:
            raise ValueError("Either annual_ctc or monthly_gross must be provided and greater than 0")
        
        # Apply any manual overrides if provided in options
        overrides = options.get('overrides', {})
        if overrides:
            for field, value in overrides.items():
                if hasattr(components, field) and value is not None:
                    setattr(components, field, value)
            
            # Recalculate dependent fields if basic components changed
            if any(field in overrides for field in ['basic', 'hra', 'special_allowance']):
                components.monthly_gross = components.basic + components.hra + components.special_allowance
            
            if any(field in overrides for field in ['pf_deduction', 'tax_deduction', 'professional_tax']):
                components.total_deductions = components.pf_deduction + components.tax_deduction + components.professional_tax
            
            # Recalculate net pay
            components.net_pay = components.monthly_gross - components.total_deductions
            
            # Recalculate annual CTC
            components.annual_ctc = components.monthly_gross * 12
        
        # Validate the components
        validation_issues = []
        is_valid, validation_messages = self._validate_salary_structure_internal(components)
        if not is_valid:
            validation_issues = validation_messages
        
        # Get formatted breakdown
        formatted_breakdown = self.format_salary_breakdown(components)
        
        # Create and return the response object
        return AutoSalaryCalculationResponse(
            annual_ctc=components.annual_ctc,
            monthly_gross=components.monthly_gross,
            basic=components.basic,
            hra=components.hra,
            special_allowance=components.special_allowance,
            pf_deduction=components.pf_deduction,
            tax_deduction=components.tax_deduction,
            professional_tax=components.professional_tax,
            total_deductions=components.total_deductions,
            net_pay=components.net_pay,
            employer_pf=components.employer_pf,
            calculation_details=components.calculation_details,
            validation_issues=validation_issues,
            formatted_breakdown=formatted_breakdown
        )
    
    def validate_salary_structure_detailed(
        self,
        annual_ctc: float,
        monthly_gross: float,
        basic: float,
        hra: float,
        special_allowance: float,
        pf_deduction: float,
        tax_deduction: float
    ):
        """
        Validate salary structure against legal compliance with detailed response.
        
        Args:
            annual_ctc: Annual CTC
            monthly_gross: Monthly gross salary
            basic: Basic salary
            hra: House rent allowance
            special_allowance: Special allowance
            pf_deduction: PF deduction
            tax_deduction: Tax deduction
            
        Returns:
            SalaryValidationResponse: Validation results
        """
        from ..schemas.salary_admin import SalaryValidationResponse
        
        # Create temporary components object for validation
        total_deductions = pf_deduction + tax_deduction
        professional_tax = 0  # This would need to be calculated separately
        net_pay = monthly_gross - total_deductions
        
        components = SalaryComponents(
            annual_ctc=annual_ctc,
            monthly_gross=monthly_gross,
            basic=basic,
            hra=hra,
            special_allowance=special_allowance,
            pf_deduction=pf_deduction,
            tax_deduction=tax_deduction,
            professional_tax=professional_tax,
            total_deductions=total_deductions,
            net_pay=net_pay,
            employer_pf=0,  # Would need additional calculation
            calculation_details={}
        )
        
        # Perform validation
        is_valid, issues = self._validate_salary_structure_internal(components)
        
        # Calculate additional metrics for the response
        basic_percentage = (basic * 12) / annual_ctc if annual_ctc > 0 else 0
        hra_percentage = hra / basic if basic > 0 else 0
        deductions_percentage = (total_deductions * 12) / annual_ctc if annual_ctc > 0 else 0
        

        # Generate recommendations
        recommendations = []
        if basic_percentage < 0.35:
            recommendations.append("Consider increasing basic salary to at least 35% of CTC")
        elif basic_percentage > 0.60:
            recommendations.append("Consider reducing basic salary to no more than 60% of CTC")
        
        if hra_percentage > 0.60:
            recommendations.append("HRA seems unusually high compared to basic salary")
        
        if net_pay <= 0:
            recommendations.append("Net pay should be positive")
        
        # Calculate compliance score
        compliance_score = 100.0
        if issues:
            compliance_score -= len(issues) * 15  # Deduct 15 points per issue
        if recommendations:
            compliance_score -= len(recommendations) * 5  # Deduct 5 points per recommendation
        compliance_score = max(0, compliance_score)  # Don't go below 0
        
        return SalaryValidationResponse(
            is_valid=is_valid,
            issues=issues,
            recommendations=recommendations,
            compliance_score=compliance_score,
            basic_percentage=basic_percentage,
            hra_percentage=hra_percentage,
            deductions_percentage=deductions_percentage
        )
    

    def format_salary_breakdown(self, components: SalaryComponents) -> Dict:
        """
        Format salary breakdown for display.
        
        Args:
            components: Salary components
            
        Returns:
            Dict: Formatted breakdown
        """
        return {
            "annual_ctc": round(components.annual_ctc, 2),
            "monthly_components": {
                "basic": round(components.basic, 2),
                "hra": round(components.hra, 2),
                "special_allowance": round(components.special_allowance, 2),
                "gross": round(components.monthly_gross, 2)
            },
            "deductions": {
                "pf": round(components.pf_deduction, 2),
                "tax": round(components.tax_deduction, 2),
                "professional_tax": round(components.professional_tax, 2),
                "total": round(components.total_deductions, 2)
            },
            "net_pay": round(components.net_pay, 2),
            "employer_contributions": {
                "pf": round(components.employer_pf, 2)
            },
            "calculation_details": components.calculation_details
        }


    # New methods for the three specific admin APIs
    
    def _fetch_unpaid_leaves_for_month(self, db, employee_id: int, year: int, month: int) -> dict:
        """
        Fetch unpaid leaves data from leaves model for a specific month.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month (1-12)
            
        Returns:
            dict: Contains unpaid_leave_days, half_day_leaves, and detailed breakdown
        """
        from ..models.leave import Leave
        from datetime import date, datetime
        import calendar
        
        # Calculate start and end dates for the month
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        
        # Query for unpaid leaves in the specified month
        unpaid_leaves = db.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.leave_type == 'unpaid',
            Leave.start_date >= start_date,
            Leave.end_date <= end_date
        ).all()
        
        unpaid_leave_days = 0.0
        half_day_leaves = 0.0
        leave_breakdown = []
        
        for leave in unpaid_leaves:
            if leave.half_day == "true":
                # Half day leaves count as 0.5 days
                if leave.half_day_type in ['first_half', 'second_half']:
                    half_day_leaves += 0.5
                    leave_breakdown.append({
                        'leave_id': leave.id,
                        'days': 0.5,
                        'type': 'half_day',
                        'half_day_type': leave.half_day_type,
                        'start_date': leave.start_date.isoformat(),
                        'end_date': leave.end_date.isoformat(),
                        'reason': leave.reason
                    })
                else:
                    # Generic half-day without specific type
                    half_day_leaves += 0.5
                    leave_breakdown.append({
                        'leave_id': leave.id,
                        'days': 0.5,
                        'type': 'half_day',
                        'half_day_type': 'unspecified',
                        'start_date': leave.start_date.isoformat(),
                        'end_date': leave.end_date.isoformat(),
                        'reason': leave.reason
                    })
            else:
                # Full day leaves
                unpaid_leave_days += leave.days
                leave_breakdown.append({
                    'leave_id': leave.id,
                    'days': leave.days,
                    'type': 'full_day',
                    'start_date': leave.start_date.isoformat(),
                    'end_date': leave.end_date.isoformat(),
                    'reason': leave.reason
                })
        
        return {
            'unpaid_leave_days': unpaid_leave_days,
            'half_day_leaves': half_day_leaves,
            'total_unpaid_leave_days': unpaid_leave_days + half_day_leaves,
            'leave_breakdown': leave_breakdown,
            'query_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_leave_records_found': len(unpaid_leaves)
        }

    def get_ctc_breakdown_for_employee(self, db, employee_id: int):
        """
        Get complete CTC breakdown for an employee.
        
        Args:
            db: Database session
            employee_id: Employee ID
            
        Returns:
            CTCBreakdownResponse: Complete CTC breakdown
        """
        from ..models.employee import Employee
        from ..models.salary import Salary
        from ..models.user import User
        from datetime import datetime
        
        # Get employee with salary information
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
        if not salary:
            raise ValueError("Salary information not found for employee")
        
        # Calculate professional tax dynamically (Salary model doesn't have this field)
        # Default to 'default' state if no specific state information is available
        state = getattr(employee, 'state', 'default') or 'default'
        professional_tax = self.calculator._calculate_professional_tax(state)
        
        # Calculate additional metrics
        cost_per_day = salary.annual_ctc / 365
        employer_pf = min(salary.basic, self.calculator.PF_CAP) * self.calculator.PF_EMPLOYER_RATE
        
        # Get calculation details
        calculation_details = {
            "basic_percentage": round((salary.basic * 12) / salary.annual_ctc, 4) if salary.annual_ctc > 0 else 0,
            "hra_percentage": round(salary.hra / salary.basic, 4) if salary.basic > 0 else 0,
            "professional_tax_calculation": f"Monthly professional tax for {state}: {professional_tax:.2f}",
            "cost_per_day_calculation": f"{salary.annual_ctc} / 365 = {cost_per_day:.2f}",
            "employer_pf_calculation": f"min({salary.basic}, {self.calculator.PF_CAP}) * {self.calculator.PF_EMPLOYER_RATE} = {employer_pf:.2f}",
            "last_calculated": datetime.now().isoformat()
        }
        
        return CTCBreakdownResponse(
            employee_id=employee.id,
            employee_name=employee.user.full_name if employee.user else "Unknown",
            employee_email=employee.user.email if employee.user else "",
            department=employee.department,
            designation=employee.designation,
            annual_ctc=salary.annual_ctc,
            monthly_gross=salary.monthly_gross,
            basic=salary.basic,
            hra=salary.hra,
            special_allowance=salary.special_allowance,
            pf_deduction=salary.pf_deduction,
            tax_deduction=salary.tax_deduction,
            professional_tax=professional_tax,
            total_deductions=salary.total_deductions,
            net_pay=salary.net_pay,
            employer_pf=employer_pf,
            cost_per_day=cost_per_day,
            calculation_details=calculation_details,
            last_updated=datetime.now()
        )
    

    def validate_monthly_salary_with_leaves(
        self,
        db,
        employee_id: int,
        year: int,
        month: int,
        unpaid_leave_days: float = None,
        half_day_leaves: float = None,
        custom_deduction: float = 0
    ):
        """
        Validate and generate salary for a month with unpaid leaves.
        
        Automatically fetches unpaid leaves data from leaves model for the specified month.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month (1-12)
            unpaid_leave_days: Number of unpaid leave days (optional, auto-fetched if None)
            half_day_leaves: Number of half-day leaves (optional, auto-fetched if None)
            custom_deduction: Custom additional deduction
            
        Returns:
            MonthlySalaryValidationResponse: Validation results and calculations
        """
        from ..models.employee import Employee
        from ..models.salary import Salary
        from ..models.leave import Leave
        from datetime import datetime, date
        import calendar
        
        # Get employee with salary information
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
        if not salary:
            raise ValueError("Salary information not found for employee")
        
        # Calculate days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Automatically fetch unpaid leaves data from leaves model
        unpaid_leave_data = self._fetch_unpaid_leaves_for_month(db, employee_id, year, month)
        
        # Use provided values or auto-fetched values
        if unpaid_leave_days is None:
            unpaid_leave_days = unpaid_leave_data['unpaid_leave_days']
        if half_day_leaves is None:
            half_day_leaves = unpaid_leave_data['half_day_leaves']
        
        # Get working days (excluding weekends) - simplified calculation
        # In a real implementation, you'd exclude holidays and weekends
        working_days = int(days_in_month * 0.71)  # Rough approximation
        
        # Calculate payable days
        unpaid_leave_days = max(0, unpaid_leave_days)
        half_day_leaves = max(0, half_day_leaves)
        payable_days = days_in_month - unpaid_leave_days - (half_day_leaves * 0.5)
        payable_days = max(0, payable_days)
        
        # Calculate daily salary (per day salary)
        daily_salary = salary.net_pay / days_in_month
        
        # Calculate deductions based on unpaid leaves only
        leave_deduction = unpaid_leave_days * daily_salary
        total_deductions = salary.total_deductions + leave_deduction + custom_deduction
        final_net_salary = salary.net_pay - leave_deduction - custom_deduction
        
        # Validation
        validation_issues = []
        if final_net_salary < 0:
            validation_issues.append("Final salary would be negative after deductions")
            is_valid = False
        else:
            is_valid = True
        
        if payable_days < days_in_month * 0.5:  # Less than 50% attendance
            validation_issues.append("Payable days are less than 50% of total days")
            is_valid = False
        
        calculation_details = {
            "days_in_month": days_in_month,
            "working_days": working_days,
            "daily_salary_calculation": f"{salary.net_pay} / {days_in_month} = {daily_salary:.2f}",
            "leave_deduction_calculation": f"{unpaid_leave_days} * {daily_salary:.2f} = {leave_deduction:.2f}",
            "final_salary_calculation": f"{salary.net_pay} - {leave_deduction:.2f} - {custom_deduction:.2f} = {final_net_salary:.2f}",
            "payable_days_ratio": round(payable_days / days_in_month, 4),
            "auto_fetched_leave_data": unpaid_leave_data
        }
        
        return MonthlySalaryValidationResponse(
            success=is_valid,
            employee_id=employee.id,
            employee_name=employee.user.full_name if employee.user else "Unknown",
            month=month,
            year=year,
            is_valid=is_valid,
            validation_issues=validation_issues,
            days_in_month=days_in_month,
            working_days=working_days,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            payable_days=payable_days,
            daily_salary=daily_salary,
            leave_deduction=leave_deduction,
            custom_deduction=custom_deduction,
            total_deductions=total_deductions,
            final_net_salary=final_net_salary,
            payslip_id=None,  # Would be set if payslip is generated
            payslip_generated=False,
            calculation_details=calculation_details,
            processed_date=datetime.now()
        )
    

    def generate_detailed_payslip_with_leaves(
        self,
        db,
        employee_id: int,
        year: int,
        month: int,
        unpaid_leave_days: Optional[float] = None,
        half_day_leaves: Optional[float] = None
    ):
        """
        Generate detailed payslip with leave calculations.
        
        Automatically fetches unpaid leaves data from leaves model for the specified month.
        
        This returns exactly the payslip format requested:
        - CTC, in-hand salary, total days, working days
        - Per-day salary (in-hand salary / days in month)
        - Unpaid leaves taken, salary cut = unpaid_leaves × per_day_salary
        - Total processed salary = in_hand_salary - salary_cut
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month (1-12)
            unpaid_leave_days: Override unpaid leave days (optional, auto-fetched if None)
            half_day_leaves: Override half-day leaves (optional, auto-fetched if None)
            
        Returns:
            PayslipGenerationResponse: Detailed payslip with all requested information
        """
        from ..models.employee import Employee
        from ..models.salary import Salary
        from ..models.leave import Leave
        from datetime import datetime, date
        import calendar
        
        # Get employee with salary information
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
        if not salary:
            raise ValueError("Salary information not found for employee")
        
        # Calculate days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Automatically fetch unpaid leaves data from leaves model
        unpaid_leave_data = self._fetch_unpaid_leaves_for_month(db, employee_id, year, month)
        
        # Use provided values or auto-fetched values
        if unpaid_leave_days is None:
            unpaid_leave_days = unpaid_leave_data['unpaid_leave_days']
        if half_day_leaves is None:
            half_day_leaves = unpaid_leave_data['half_day_leaves']
        
        # Calculate total working days (simplified - would exclude weekends/holidays)
        total_working_days = int(days_in_month * 0.71)  # Rough approximation
        
        # Calculate per-day salary (in-hand salary / days in month)
        in_hand_salary = salary.net_pay
        per_day_salary = in_hand_salary / days_in_month
        
        # Calculate salary cut for unpaid leaves (unpaid leaves only)
        salary_cut_for_unpaid_leaves = unpaid_leave_days * per_day_salary
        
        # Calculate final processed salary
        final_processed_salary = in_hand_salary - salary_cut_for_unpaid_leaves
        
        # Payslip components (actual vs payable)
        basic_actual = salary.basic
        hra_actual = salary.hra
        special_allowance_actual = salary.special_allowance
        total_earnings_actual = salary.monthly_gross
        
        # For this simplified version, assume payable = actual
        # In a real implementation, you'd prorate based on payable days
        basic_payable = basic_actual
        hra_payable = hra_actual
        special_allowance_payable = special_allowance_actual
        total_earnings_payable = total_earnings_actual
        

        # Deductions
        pf_deduction = salary.pf_deduction
        tax_deduction = salary.tax_deduction
        # Calculate professional tax dynamically (Salary model doesn't have this field)
        state = getattr(employee, 'state', 'default') or 'default'
        professional_tax = self.calculator._calculate_professional_tax(state)
        leave_deduction = salary_cut_for_unpaid_leaves
        other_deductions = 0
        total_deductions = salary.total_deductions + leave_deduction
        
        # Additional payslip details
        ytd_earnings = None  # Would be calculated from historical payslips
        ytd_deductions = None  # Would be calculated from historical payslips
        leave_balance_remaining = None  # Would be calculated from leave balance
        
        calculation_details = {
            "per_day_salary_calculation": f"{in_hand_salary} / {days_in_month} = {per_day_salary:.2f}",
            "salary_cut_calculation": f"{unpaid_leave_days} * {per_day_salary:.2f} = {salary_cut_for_unpaid_leaves:.2f}",
            "final_salary_calculation": f"{in_hand_salary} - {salary_cut_for_unpaid_leaves:.2f} = {final_processed_salary:.2f}",
            "total_working_days_estimation": f"{days_in_month} * 0.71 ≈ {total_working_days} days",
            "generated_for_month": f"{month}/{year}",
            "leave_processing_note": "Half day leaves counted as 0.5 days each",
            "auto_fetched_leave_data": unpaid_leave_data
        }
        
        return PayslipGenerationResponse(
            success=True,
            employee_id=employee.id,
            employee_name=employee.user.full_name if employee.user else "Unknown",
            employee_email=employee.user.email if employee.user else "",
            department=employee.department,
            designation=employee.designation,
            payslip_id=None,  # Would be set if saved to DB
            month=month,
            year=year,
            pay_date=date.today(),
            annual_ctc=salary.annual_ctc,
            monthly_ctc=salary.monthly_gross,
            basic_actual=basic_actual,
            basic_payable=basic_payable,
            hra_actual=hra_actual,
            hra_payable=hra_payable,
            special_allowance_actual=special_allowance_actual,
            special_allowance_payable=special_allowance_payable,
            total_earnings_actual=total_earnings_actual,
            total_earnings_payable=total_earnings_payable,
            pf_deduction=pf_deduction,
            tax_deduction=tax_deduction,
            professional_tax=professional_tax,
            leave_deduction=leave_deduction,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            gross_salary=total_earnings_payable,
            in_hand_salary=in_hand_salary,
            total_days_in_month=days_in_month,
            total_working_days=total_working_days,
            unpaid_leaves_taken=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            per_day_salary=per_day_salary,
            salary_cut_for_unpaid_leaves=salary_cut_for_unpaid_leaves,
            final_processed_salary=final_processed_salary,
            ytd_earnings=ytd_earnings,
            ytd_deductions=ytd_deductions,
            leave_balance_remaining=leave_balance_remaining,
            generated_at=datetime.now(),
            calculation_details=calculation_details
        )
