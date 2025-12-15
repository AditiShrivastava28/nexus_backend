#!/usr/bin/env python3
"""
Migration script to assign default leave balances to existing employees.

This script ensures that all employees in the system have a 12-day leave balance
for the current year if they don't already have one.
"""

import sys
import os
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.employee import Employee
from app.models.leave import LeaveBalance
from app.database import Base


def migrate_leave_balances():
    """
    Assign 12-day leave balances to all employees who don't have them for the current year.
    """
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///./hrms.db")
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        current_year = date.today().year
        
        # Get all employees
        all_employees = db.query(Employee).all()
        print(f"Found {len(all_employees)} employees in the system")
        
        # Get all existing leave balances for current year
        existing_balances = db.query(LeaveBalance).filter(LeaveBalance.year == current_year).all()
        employees_with_balances = {balance.employee_id for balance in existing_balances}
        print(f"Found {len(existing_balances)} employees with leave balances for {current_year}")
        
        # Find employees without balances
        employees_needing_balances = []
        for employee in all_employees:
            if employee.id not in employees_with_balances:
                employees_needing_balances.append(employee)
        
        print(f"Found {len(employees_needing_balances)} employees without leave balances")
        
        # Create balances for employees who need them
        created_balances = 0
        for employee in employees_needing_balances:
            # Check if employee has any leave records
            has_leaves = len(employee.leaves) > 0 if hasattr(employee, 'leaves') else False
            
            # Calculate used days from existing leave records (if any)
            used_days = 0.0
            if has_leaves:
                for leave in employee.leaves:
                    if (leave.start_date.year <= current_year and 
                        leave.end_date.year >= current_year and 
                        leave.leave_type == "paid"):
                        try:
                            used_days += float(leave.days or 0)
                        except (ValueError, TypeError):
                            continue
            

            # Create the balance
            balance = LeaveBalance(
                employee_id=employee.id,
                year=current_year,
                total_days=12,
                used_days=used_days,
                remaining_days=max(12 - used_days, 0),
                leave_type="paid"  # Default to paid leave balance
            )
            db.add(balance)
            created_balances += 1
            
            print(f"Created balance for employee {employee.id} - Used: {used_days}, Remaining: {max(12 - used_days, 0)}")
        
        # Commit all changes
        db.commit()
        print(f"\nMigration completed successfully!")
        print(f"Created {created_balances} new leave balances")
        print(f"Total employees now have leave balances: {len(all_employees)}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting leave balance migration...")
    migrate_leave_balances()
    print("Migration script completed.")
