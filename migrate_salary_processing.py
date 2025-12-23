"""
Database migration script for salary processing functionality.

This script adds new columns to the payslips table and creates the 
monthly_salary_processing table for the leave-based salary processing feature.
"""

import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime


def migrate_database():
    """
    Run migration to add new columns for salary processing.
    """
    # Get database path from environment or use default
    db_path = os.getenv("DATABASE_URL", "sqlite:///./nexus_hr.db")
    
    # Remove sqlite:// prefix if present
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(payslips)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # List of new columns to add to payslips table
        new_columns = [
            ("basic_paid", "REAL DEFAULT 0"),
            ("basic_actual", "REAL DEFAULT 0"),
            ("hra_paid", "REAL DEFAULT 0"),
            ("hra_actual", "REAL DEFAULT 0"),
            ("medical_allowance_paid", "REAL DEFAULT 0"),
            ("medical_allowance_actual", "REAL DEFAULT 0"),
            ("conveyance_allowance_paid", "REAL DEFAULT 0"),
            ("conveyance_allowance_actual", "REAL DEFAULT 0"),
            ("total_earnings_paid", "REAL DEFAULT 0"),
            ("total_earnings_actual", "REAL DEFAULT 0"),
            ("professional_tax", "REAL DEFAULT 0"),
            ("total_deductions", "REAL DEFAULT 0"),
            ("actual_payable_days", "REAL DEFAULT 0"),
            ("total_working_days", "REAL DEFAULT 0"),
            ("loss_of_pay_days", "REAL DEFAULT 0"),
            ("days_payable", "REAL DEFAULT 0"),
            ("leave_deduction_amount", "REAL DEFAULT 0"),
            ("processed_date", "DATETIME")
        ]
        
        # Add missing columns
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE payslips ADD COLUMN {column_name} {column_def}")
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"Column {column_name} already exists")
                    else:
                        raise e
        
        # Check if monthly_salary_processing table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_salary_processing'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # Create monthly_salary_processing table
            create_table_sql = """
            CREATE TABLE monthly_salary_processing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                processed_date DATETIME,
                total_employees INTEGER DEFAULT 0,
                successful_payments INTEGER DEFAULT 0,
                failed_payments INTEGER DEFAULT 0,
                total_processed_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_sql)
            print("Created table: monthly_salary_processing")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show summary
        cursor.execute("PRAGMA table_info(payslips)")
        columns_after = cursor.fetchall()
        print(f"\nPayslips table now has {len(columns_after)} columns:")
        for column in columns_after:
            print(f"  - {column[1]} ({column[2]})")
        
        # Show monthly_salary_processing table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_salary_processing'")
        if cursor.fetchone():
            print("\nMonthly salary processing table created successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def verify_migration():
    """
    Verify that migration was successful by checking database structure.
    """
    db_path = os.getenv("DATABASE_URL", "sqlite:///./nexus_hr.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check payslips table structure
        cursor.execute("PRAGMA table_info(payslips)")
        payslip_columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # Check required columns
        required_columns = [
            "basic_paid", "basic_actual", "hra_paid", "hra_actual",
            "medical_allowance_paid", "medical_allowance_actual",
            "conveyance_allowance_paid", "conveyance_allowance_actual",
            "total_earnings_paid", "total_earnings_actual",
            "professional_tax", "total_deductions",
            "actual_payable_days", "total_working_days", "loss_of_pay_days",
            "days_payable", "leave_deduction_amount", "processed_date"
        ]
        
        missing_columns = [col for col in required_columns if col not in payslip_columns]
        
        if missing_columns:
            print(f"Missing columns in payslips table: {missing_columns}")
            return False
        
        # Check monthly_salary_processing table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_salary_processing'")
        if not cursor.fetchone():
            print("monthly_salary_processing table not found")
            return False
        
        print("Migration verification passed!")
        print(f"All {len(required_columns)} required columns found in payslips table")
        print("monthly_salary_processing table exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False


if __name__ == "__main__":
    print("Starting database migration for salary processing...")
    
    # Run migration
    if migrate_database():
        print("\nMigration successful!")
        
        # Verify migration
        if verify_migration():
            print("\nDatabase is ready for salary processing!")
        else:
            print("\nMigration verification failed!")
    else:
        print("\nMigration failed!")
