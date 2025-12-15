"""
Employee service.

This module provides employee-related business logic.
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from ..models.user import User
from ..models.employee import Employee, EmployeeJob
from ..models.salary import Salary
from ..models.leave import LeaveBalance
from .auth import AuthService


class EmployeeService:
    """
    Service class for employee operations.
    
    Provides methods for employee CRUD and profile management.
    """
    
    @staticmethod
    def create_employee(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        employee_id: str,
        role: str = "employee",
        department: str = None,
        designation: str = None,
        join_date: date = None,
        location: str = None,
        manager_id: int = None
    ) -> Employee:
        """
        Create a new employee with user account.
        
        Args:
            db: Database session
            email: Work email
            password: Initial password
            full_name: Full name
            employee_id: Company employee ID
            role: User role
            department: Department
            designation: Job title
            join_date: Date of joining
            location: Work location
            manager_id: Manager's employee ID
            
        Returns:
            Employee: Created employee object
        """
        # Create user account first
        user = AuthService.create_user(db, email, password, full_name, role)
        
        # Create employee profile
        employee = Employee(
            user_id=user.id,
            employee_id=employee_id,
            department=department,
            designation=designation,
            join_date=join_date or date.today(),
            location=location,
            manager_id=manager_id,
            status="active"
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        # Create default salary structure
        salary = Salary(
            employee_id=employee.id,
            annual_ctc=0,
            monthly_gross=0,
            basic=0,
            hra=0,
            special_allowance=0,
            pf_deduction=0,
            tax_deduction=0,
            total_deductions=0,
            net_pay=0
        )
        db.add(salary)
        

        # Create a single default leave balance (12 days/year) for current year
        current_year = date.today().year
        
        # Check if balance already exists for this year (to avoid duplicates)
        existing_balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == current_year
        ).first()
        

        if not existing_balance:
            balance = LeaveBalance(
                employee_id=employee.id,
                year=current_year,
                total_days=12,
                used_days=0,
                remaining_days=12,
                leave_type="paid"  # Default to paid leave balance
            )
            db.add(balance)
        
        db.commit()
        db.refresh(employee)
        return employee
    
    @staticmethod
    def get_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
        """
        Get an employee by internal ID.
        
        Args:
            db: Database session
            employee_id: Internal employee ID
            
        Returns:
            Optional[Employee]: Employee if found, None otherwise
        """
        return db.query(Employee).filter(Employee.id == employee_id).first()
    
    @staticmethod
    def get_employee_by_user_id(db: Session, user_id: int) -> Optional[Employee]:
        """
        Get an employee by user ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[Employee]: Employee if found, None otherwise
        """
        return db.query(Employee).filter(Employee.user_id == user_id).first()
    
    @staticmethod
    def get_all_employees(
        db: Session, 
        search: str = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Employee]:
        """
        Get all employees with optional search filter.
        
        Args:
            db: Database session
            search: Optional search term for name/email
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Employee]: List of employees
        """
        query = db.query(Employee).join(User)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (Employee.employee_id.ilike(search_term))
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_employee_profile(
        db: Session,
        employee: Employee,
        **kwargs
    ) -> Employee:
        """
        Update employee profile fields.
        
        Args:
            db: Database session
            employee: Employee to update
            **kwargs: Fields to update
            
        Returns:
            Employee: Updated employee
        """
        for key, value in kwargs.items():
            if hasattr(employee, key) and value is not None:
                setattr(employee, key, value)
        
        db.commit()
        db.refresh(employee)
        return employee
    
    @staticmethod
    def get_team_members(db: Session, manager_id: int) -> List[Employee]:
        """
        Get team members for a manager.
        
        Args:
            db: Database session
            manager_id: Manager's employee ID
            
        Returns:
            List[Employee]: List of team members
        """
        return db.query(Employee).filter(
            Employee.manager_id == manager_id
        ).all()
    
    @staticmethod
    def delete_employee(db: Session, employee: Employee) -> bool:
        """
        Delete an employee and their user account.
        
        Args:
            db: Database session
            employee: Employee to delete
            
        Returns:
            bool: True if successful
        """
        user = employee.user
        db.delete(employee)
        if user:
            db.delete(user)
        db.commit()
        return True
