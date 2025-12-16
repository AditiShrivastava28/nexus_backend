"""
Database Migration: Create Corporate Leaves Table

This script creates the corporate_leaves table for the leave calendar API.
Run this after deploying the code to ensure the database schema is updated.
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def create_corporate_leaves_table():
    """Create the corporate_leaves table in the database."""
    
    # Get database URL from environment or config
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try to import from config
        try:
            sys.path.append('/home/tw/Downloads/backend')
            from app.config import DATABASE_URL
            database_url = DATABASE_URL
        except:
            print("❌ DATABASE_URL not found. Please set the DATABASE_URL environment variable.")
            return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # SQL to create corporate_leaves table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS corporate_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            date DATE NOT NULL,
            leave_type VARCHAR NOT NULL DEFAULT 'National Holiday',
            is_recurring VARCHAR NOT NULL DEFAULT 'true',
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        );
        """
        
        # Create indexes for better performance
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_corporate_leaves_date ON corporate_leaves (date);",
            "CREATE INDEX IF NOT EXISTS idx_corporate_leaves_created_by ON corporate_leaves (created_by);"
        ]
        
        with engine.connect() as connection:
            # Create table
            print("🔄 Creating corporate_leaves table...")
            connection.execute(text(create_table_sql))
            
            # Create indexes
            for index_sql in create_indexes_sql:
                print(f"🔄 Creating index: {index_sql.split('idx_')[1].split(' ')[0]}")
                connection.execute(text(index_sql))
            
            connection.commit()
            
        print("✅ Corporate leaves table created successfully!")
        print("📋 Table Details:")
        print("   - Name: corporate_leaves")
        print("   - Primary Key: id")
        print("   - Key Fields: name, date, leave_type, is_recurring")
        print("   - Foreign Key: created_by -> users(id)")
        print("   - Indexes: date, created_by")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating corporate_leaves table: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Corporate Leaves Table Creation...")
    print("=" * 50)
    
    success = create_corporate_leaves_table()
    
    print("=" * 50)
    if success:
        print("🎉 Migration completed successfully!")
        print("\n📝 Next Steps:")
        print("1. Test the API endpoints")
        print("2. Generate corporate leaves using admin endpoint")
        print("3. Access the calendar API for employees")
    else:
        print("❌ Migration failed. Please check the error messages above.")
    
    print("\n🔗 API Endpoints to Test:")
    print("   - POST /admin/corporate-leaves/generate")
    print("   - GET /admin/corporate-leaves")
    print("   - GET /leaves/corporate-calendar")
