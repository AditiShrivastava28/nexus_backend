
"""
Leave-based salary calculation service.

This module provides functionality for calculating salaries with leave deductions
and generating detailed pay slips.
"""

import calendar
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from dataclasses import dataclass

from ..models.employee import Employee
from ..models.salary import Salary, Payslip
from ..models.leave import Leave, LeaveBalance

from ..schemas.leave_salary_processing import (
    DetailedPayslipResponse,
    PayslipFormatResponse,
    LeaveBalanceCheck
)


@dataclass
class MonthlySalaryCalculation:
    """
    Data class for monthly salary calculation with leave deductions.
    
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
        half_day_leaves: Number of half-day leaves
        leave_deduction: Amount deducted for unpaid leaves
        net_payable_amount: Final payable amount after deductions
        total_working_days: Total working days in month
        days_payable: Net payable days
        professional_tax: Professional tax amount
        total_deductions: Total deductions amount
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


class LeaveBasedSalaryCalculationService:
    """
    Service for calculating salaries with leave deductions.
    
    This service handles:
    - Calculating daily salary from monthly salary
    - Deducting salary for unpaid leaves
    - Generating detailed pay slips
    - Tracking working days and loss of pay days
    """
    
    def __init__(self):
        self.medical_allowance_percentage = 0.25  # 25% of basic salary
        self.conveyance_allowance_percentage = 0.25  # 25% of basic salary
        self.professional_tax_default = 200  # ₹200 professional tax
    
    def calculate_days_in_month(self, year: int, month: int) -> int:
        """Calculate total days in a month."""
        return calendar.monthrange(year, month)[1]
    
    def get_employee_unpaid_leaves(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int
    ) -> Tuple[float, float]:
        """
        Get unpaid leave details for an employee in a specific month.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            
        Returns:
            Tuple[float, float]: (unpaid_leave_days, half_day_leaves)
        """
        # Get first and last date of the month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Query leaves for the month
        leaves = db.query(Leave).filter(
            and_(
                Leave.employee_id == employee_id,
                Leave.start_date >= first_day,
                Leave.end_date <= last_day,
                Leave.leave_type == "unpaid"
            )
        ).all()
        
        unpaid_leave_days = 0.0
        half_day_leaves = 0.0
        
        for leave in leaves:
            if leave.half_day == "true":
                half_day_leaves += leave.days
            else:
                unpaid_leave_days += leave.days
        
        return unpaid_leave_days, half_day_leaves
    
    def calculate_leave_deduction(
        self,
        monthly_salary: float,
        unpaid_leave_days: float,
        half_day_leaves: float,
        total_working_days: int
    ) -> Tuple[float, float]:
        """
        Calculate leave deduction amount.
        
        Args:
            monthly_salary: Monthly salary amount
            unpaid_leave_days: Number of full unpaid leave days
            half_day_leaves: Number of half-day unpaid leaves
            total_working_days: Total working days in month
            
        Returns:
            Tuple[float, float]: (leave_deduction_amount, days_payable)
        """
        # Calculate daily salary
        daily_salary = monthly_salary / total_working_days if total_working_days > 0 else 0
        
        # Calculate total leave days (full days + half days as 0.5)
        total_leave_days = unpaid_leave_days + (half_day_leaves * 0.5)
        
        # Calculate deduction
        leave_deduction = daily_salary * total_leave_days
        
        # Calculate payable days
        days_payable = total_working_days - total_leave_days
        
        return leave_deduction, days_payable
    
    def calculate_salary_components(
        self,
        basic_salary: float,
        unpaid_leave_days: float = 0,
        half_day_leaves: float = 0,
        total_working_days: int = 30
    ) -> MonthlySalaryCalculation:
        """
        Calculate monthly salary with leave deductions.
        
        Args:
            basic_salary: Basic salary amount
            unpaid_leave_days: Number of unpaid leave days
            half_day_leaves: Number of half-day unpaid leaves
            total_working_days: Total working days in month
            
        Returns:
            MonthlySalaryCalculation: Calculated salary components
        """
        # Calculate allowances
        hra = basic_salary * 0.5  # 50% of basic as HRA
        medical_allowance = basic_salary * self.medical_allowance_percentage
        conveyance_allowance = basic_salary * self.conveyance_allowance_percentage
        
        # Calculate total earnings
        total_earnings = basic_salary + hra + medical_allowance + conveyance_allowance
        
        # Calculate leave deduction
        leave_deduction, days_payable = self.calculate_leave_deduction(
            total_earnings, unpaid_leave_days, half_day_leaves, total_working_days
        )
        
        # Calculate net payable amount
        professional_tax = self.professional_tax_default
        total_deductions = leave_deduction + professional_tax
        net_payable_amount = total_earnings - total_deductions
        
        # Calculate daily salary for reference
        daily_salary = total_earnings / total_working_days if total_working_days > 0 else 0
        
        return MonthlySalaryCalculation(
            employee_id=0,  # Will be set by caller
            month=0,  # Will be set by caller
            year=0,  # Will be set by caller
            basic_salary=basic_salary,
            hra=hra,
            medical_allowance=medical_allowance,
            conveyance_allowance=conveyance_allowance,
            total_earnings=total_earnings,
            daily_salary=daily_salary,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            leave_deduction=leave_deduction,
            net_payable_amount=net_payable_amount,
            total_working_days=total_working_days,
            days_payable=days_payable,
            professional_tax=professional_tax,
            total_deductions=total_deductions
        )
    
    def process_employee_salary_with_leaves(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int,
        unpaid_leave_days: float = 0,
        half_day_leaves: float = 0,
        dry_run: bool = False
    ) -> MonthlySalaryCalculation:
        """
        Process salary for an employee with leave deductions.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            unpaid_leave_days: Number of unpaid leave days
            half_day_leaves: Number of half-day unpaid leaves
            dry_run: Whether to preview without saving
            
        Returns:
            MonthlySalaryCalculation: Calculated salary with leave deductions
            
        Raises:
            ValueError: If employee salary information not found
        """
        # Get employee and salary information
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        salary = db.query(Salary).filter(Salary.employee_id == employee_id).first()
        if not salary:
            raise ValueError(f"Salary information not found for employee {employee_id}")
        
        # Calculate total working days in month
        total_working_days = self.calculate_days_in_month(year, month)
        
        # If not provided, get leave data from database
        if unpaid_leave_days == 0 and half_day_leaves == 0:
            unpaid_leave_days, half_day_leaves = self.get_employee_unpaid_leaves(
                db, employee_id, year, month
            )
        
        # Calculate salary components
        calculation = self.calculate_salary_components(
            basic_salary=salary.basic,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            total_working_days=total_working_days
        )
        
        # Set employee-specific details
        calculation.employee_id = employee_id
        calculation.month = month
        calculation.year = year
        
        # Save to database if not dry run
        if not dry_run:
            self.save_payslip(db, employee_id, year, month, calculation, salary)
        
        return calculation
    
    def save_payslip(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int,
        calculation: MonthlySalaryCalculation,
        salary: Salary
    ):
        """
        Save payslip to database.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            calculation: Calculated salary components
            salary: Employee salary information
        """
        # Check if payslip already exists
        existing_payslip = db.query(Payslip).filter(
            and_(
                Payslip.employee_id == employee_id,
                Payslip.year == year,
                Payslip.month == month
            )
        ).first()
        
        if existing_payslip:
            # Update existing payslip
            payslip = existing_payslip
        else:
            # Create new payslip
            payslip = Payslip(
                employee_id=employee_id,
                year=year,
                month=month
            )
            db.add(payslip)
        
        # Update payslip with calculated values
        # Earnings (Actual amounts)
        payslip.basic_actual = calculation.basic_salary
        payslip.hra_actual = calculation.hra
        payslip.medical_allowance_actual = calculation.medical_allowance
        payslip.conveyance_allowance_actual = calculation.conveyance_allowance
        payslip.total_earnings_actual = calculation.total_earnings
        
        # Earnings (Paid amounts - adjusted for leaves)
        payslip.basic_paid = calculation.basic_salary * (calculation.days_payable / calculation.total_working_days)
        payslip.hra_paid = calculation.hra * (calculation.days_payable / calculation.total_working_days)
        payslip.medical_allowance_paid = calculation.medical_allowance * (calculation.days_payable / calculation.total_working_days)
        payslip.conveyance_allowance_paid = calculation.conveyance_allowance * (calculation.days_payable / calculation.total_working_days)
        payslip.total_earnings_paid = calculation.net_payable_amount + calculation.leave_deduction
        
        # Deductions
        payslip.professional_tax = calculation.professional_tax
        payslip.total_deductions = calculation.total_deductions
        
        # Working days
        payslip.total_working_days = calculation.total_working_days
        payslip.actual_payable_days = calculation.days_payable
        payslip.loss_of_pay_days = calculation.unpaid_leave_days + (calculation.half_day_leaves * 0.5)
        payslip.days_payable = calculation.days_payable
        payslip.leave_deduction_amount = calculation.leave_deduction
        
        # Final amount
        payslip.amount = calculation.net_payable_amount
        payslip.status = "processed"
        payslip.processed_at = datetime.now()
        
        db.commit()
    
    def generate_detailed_payslip(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int
    ) -> Optional[DetailedPayslipResponse]:
        """
        Generate detailed payslip response.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            
        Returns:
            DetailedPayslipResponse: Detailed payslip information
            
        Raises:
            ValueError: If payslip not found
        """
        # Get payslip from database
        payslip = db.query(Payslip).filter(
            and_(
                Payslip.employee_id == employee_id,
                Payslip.year == year,
                Payslip.month == month
            )
        ).first()
        
        if not payslip:
            raise ValueError(f"Payslip not found for employee {employee_id}, {year}-{month}")
        
        # Get employee information
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Build earnings breakdown
        earnings = {
            "Basic": {
                "paid": payslip.basic_paid,
                "actual": payslip.basic_actual
            },
            "HRA": {
                "paid": payslip.hra_paid,
                "actual": payslip.hra_actual
            },
            "Medical Allowance": {
                "paid": payslip.medical_allowance_paid,
                "actual": payslip.medical_allowance_actual
            },
            "Conveyance Allowance": {
                "paid": payslip.conveyance_allowance_paid,
                "actual": payslip.conveyance_allowance_actual
            }
        }
        
        # Build taxes and deductions
        taxes_deductions = {
            "Professional Tax": payslip.professional_tax,
            "Leave Deduction": payslip.leave_deduction_amount,
            "Total Taxes & Deductions (B)": payslip.total_deductions
        }
        
        # Build working days summary
        working_days = {
            "Actual Payable Days": payslip.actual_payable_days,
            "Total Working Days": payslip.total_working_days,
            "Loss Of Pay Days": payslip.loss_of_pay_days,
            "Days Payable": payslip.days_payable
        }
        
        return DetailedPayslipResponse(
            id=payslip.id,
            employee_id=employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            month=month,
            year=year,
            earnings=earnings,
            taxes_deductions=taxes_deductions,
            working_days=working_days,
            final_amount=payslip.amount,
            status=payslip.status,
            processed_at=payslip.processed_at
        )
    
    def generate_formatted_payslip(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int
    ) -> Optional[PayslipFormatResponse]:
        """
        Generate payslip in the exact format requested.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            
        Returns:
            PayslipFormatResponse: Formatted payslip
        """
        try:
            detailed_payslip = self.generate_detailed_payslip(db, employee_id, year, month)
            if not detailed_payslip:
                return None
            
            # Format amounts with commas
            def format_amount(amount: float) -> str:
                return f"{amount:,.2f}"
            
            # Build earnings with formatted amounts
            earnings = {}
            for component, amounts in detailed_payslip.earnings.items():
                earnings[component] = {
                    "paid": format_amount(amounts["paid"]),
                    "actual": format_amount(amounts["actual"])
                }
            
            # Add total earnings
            total_earnings_paid = sum(amounts["paid"] for amounts in detailed_payslip.earnings.values())
            total_earnings_actual = sum(amounts["actual"] for amounts in detailed_payslip.earnings.values())
            earnings["Total Earnings (A)"] = {
                "paid": format_amount(total_earnings_paid),
                "actual": format_amount(total_earnings_actual)
            }
            
            # Format taxes and deductions
            taxes_deductions = {}
            for item, amount in detailed_payslip.taxes_deductions.items():
                if item != "Total Taxes & Deductions (B)":
                    taxes_deductions[item] = format_amount(amount)
            
            # Add total taxes and deductions
            total_taxes = detailed_payslip.taxes_deductions.get("Total Taxes & Deductions (B)", 0)
            taxes_deductions["Total Taxes & Deductions (B)"] = format_amount(total_taxes)
            
            # Format working days summary
            working_days_summary = {}
            for item, days in detailed_payslip.working_days.items():
                working_days_summary[item] = f"{days:.1f}"
            
            # Get employee name
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            employee_name = f"{employee.first_name} {employee.last_name}" if employee else "Unknown"
            
            # Format month-year
            month_year = datetime(year, month, 1).strftime("%B %Y")
            
            return PayslipFormatResponse(
                employee_name=employee_name,
                month_year=month_year,
                earnings=earnings,
                taxes_deductions=taxes_deductions,
                working_days_summary=working_days_summary,
                net_payable=format_amount(detailed_payslip.final_amount)
            )
            
        except Exception as e:
            # Log error and return None
            print(f"Error generating formatted payslip: {str(e)}")
            return None
    
    def check_leave_balance(
        self,
        db: Session,
        employee_id: int,
        year: int,
        month: int
    ) -> Optional[LeaveBalanceCheck]:
        """
        Check employee leave balance for a specific month.
        
        Args:
            db: Database session
            employee_id: Employee ID
            year: Year
            month: Month
            
        Returns:
            LeaveBalanceCheck: Leave balance information
        """
        # Get leave balance for the year
        leave_balance = db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year
            )
        ).first()
        
        if not leave_balance:
            return None
        
        # Get leave details for the month
        unpaid_leave_days, half_day_leaves = self.get_employee_unpaid_leaves(db, employee_id, year, month)
        
        # Get paid leave days (total leave - unpaid leave)
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        total_leaves = db.query(func.sum(Leave.days)).filter(
            and_(
                Leave.employee_id == employee_id,
                Leave.start_date >= first_day,
                Leave.end_date <= last_day
            )
        ).scalar() or 0
        
        paid_leave_days = total_leaves - unpaid_leave_days
        
        return LeaveBalanceCheck(
            employee_id=employee_id,
            month=month,
            year=year,
            total_leave_days=total_leaves,
            paid_leave_days=paid_leave_days,
            unpaid_leave_days=unpaid_leave_days,
            half_day_leaves=half_day_leaves,
            leave_balance_remaining=leave_balance.remaining_days
        )
