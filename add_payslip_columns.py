#!/usr/bin/env python3
"""
Database Migration Script: Add Missing Payslip Columns

This script adds the missing columns to the payslips table that are defined in the model
but don't exist in the database schema.

Missing columns:
- basic_paid, basic_actual
- hra_paid, hra_actual  
- medical_allowance_paid, medical_allowance_actual
- conveyance_allowance_paid, conveyance_allowance_actual
- total_earnings_paid, total_earnings_actual
- professional_tax, total_deductions
- actual_payable_days, total_working_days, loss_of_pay_days, days_payable
- leave_deduction_amount

Run this script to fix the database schema:
python3 add_payslip_columns.py
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text

from app.config import settings


def add_missing_payslip_columns():
    """Add missing columns to the payslips table"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    

    # Define the columns to add
    columns_to_add = [
        ("basic_paid", "FLOAT DEFAULT 0"),
        ("basic_actual", "FLOAT DEFAULT 0"),
        ("hra_paid", "FLOAT DEFAULT 0"),
        ("hra_actual", "FLOAT DEFAULT 0"),
        ("medical_allowance_paid", "FLOAT DEFAULT 0"),
        ("medical_allowance_actual", "FLOAT DEFAULT 0"),
        ("conveyance_allowance_paid", "FLOAT DEFAULT 0"),
        ("conveyance_allowance_actual", "FLOAT DEFAULT 0"),
        ("total_earnings_paid", "FLOAT DEFAULT 0"),
        ("total_earnings_actual", "FLOAT DEFAULT 0"),
        ("professional_tax", "FLOAT DEFAULT 0"),
        ("total_deductions", "FLOAT DEFAULT 0"),
        ("actual_payable_days", "FLOAT DEFAULT 0"),
        ("total_working_days", "FLOAT DEFAULT 0"),
        ("loss_of_pay_days", "FLOAT DEFAULT 0"),
        ("days_payable", "FLOAT DEFAULT 0"),
        ("leave_deduction_amount", "FLOAT DEFAULT 0"),
        ("processed_at", "TIMESTAMP WITH TIME ZONE")
    ]
    
    try:
        with engine.connect() as connection:
            # Check which columns already exist
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'payslips'
            """))
            existing_columns = {row[0] for row in result.fetchall()}
            
            print(f"Existing columns in payslips table: {sorted(existing_columns)}")
            
            # Add missing columns
            added_columns = []
            for column_name, column_definition in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        # Add the column
                        sql = f"ALTER TABLE payslips ADD COLUMN {column_name} {column_definition}"
                        connection.execute(text(sql))
                        added_columns.append(column_name)
                        print(f"✓ Added column: {column_name}")
                    except Exception as e:
                        print(f"✗ Failed to add column {column_name}: {e}")
                else:
                    print(f"✓ Column already exists: {column_name}")
            
            connection.commit()
            
            if added_columns:
                print(f"\n🎉 Successfully added {len(added_columns)} columns to payslips table:")
                for col in added_columns:
                    print(f"  - {col}")
            else:
                print("\n✓ All required columns already exist in payslips table")
                
            # Verify the final schema
            print("\n📋 Final payslips table schema:")
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'payslips'
                ORDER BY ordinal_position
            """))
            
            for row in result.fetchall():
                col_name, data_type, is_nullable, default = row
                nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"  {col_name}: {data_type} {nullable_str}{default_str}")
                
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Payslip Columns Migration")
    print("=" * 50)
    
    success = add_missing_payslip_columns()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nYou can now restart your FastAPI application.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
