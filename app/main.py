"""
NexusHR FastAPI Application.

This is the main entry point for the NexusHR HR Management System API.
It configures the FastAPI application, includes all routers, and sets up
middleware and event handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routers import (
    auth_router,
    me_router,
    attendance_router,
    team_router,
    finances_router,
    org_router,
    inbox_router,
    admin_router,
    resume_router,
    requests_router,
    leaves_router,
)


def create_tables():
    """
    Create all database tables.
    
    This function creates all tables defined in the SQLAlchemy models
    if they don't already exist.
    """
    Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="NexusHR - Professional HR Management System API",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include all routers with API prefix
    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(me_router, prefix=settings.API_V1_PREFIX)
    app.include_router(attendance_router, prefix=settings.API_V1_PREFIX)
    app.include_router(requests_router, prefix=settings.API_V1_PREFIX)
    app.include_router(leaves_router, prefix=settings.API_V1_PREFIX)
    app.include_router(team_router, prefix=settings.API_V1_PREFIX)
    app.include_router(finances_router, prefix=settings.API_V1_PREFIX)
    app.include_router(org_router, prefix=settings.API_V1_PREFIX)
    app.include_router(inbox_router, prefix=settings.API_V1_PREFIX)
    app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
    app.include_router(resume_router, prefix=settings.API_V1_PREFIX)
    
    @app.on_event("startup")
    async def startup_event():
        """
        Application startup event handler.
        
        Creates database tables and seeds initial data if needed.
        """
        create_tables()
        seed_initial_data()
    
    @app.get("/")
    async def root():
        """
        Root endpoint.
        
        Returns:
            dict: Welcome message and API version
        """
        return {
            "message": "Welcome to NexusHR API",
            "version": settings.VERSION,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint.
        
        Returns:
            dict: Health status
        """
        return {"status": "healthy"}
    
    return app


def seed_initial_data():
    """
    Seed initial data for testing.
    
    Creates an admin user and sample employees if the database is empty.
    """
    from sqlalchemy.orm import Session
    from .database import SessionLocal
    from .models.user import User
    from .models.employee import Employee
    from .models.salary import Salary, Payslip
    from .models.leave import LeaveBalance
    from .models.document import Document
    from .utils.security import get_password_hash
    from datetime import date, timedelta
    
    db = SessionLocal()
    
    try:
        # Check if we already have users
        existing_users = db.query(User).count()
        if existing_users > 0:
            return
        
        # Create admin user
        admin_user = User(
            email="admin@nexushr.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create admin employee profile
        admin_employee = Employee(
            user_id=admin_user.id,
            employee_id="EMP001",
            department="Human Resources",
            designation="HR Director",
            join_date=date.today() - timedelta(days=365),
            location="Headquarters",
            status="active"
        )
        db.add(admin_employee)
        db.commit()
        db.refresh(admin_employee)
        
        # Create salary for admin
        admin_salary = Salary(
            employee_id=admin_employee.id,
            annual_ctc=2400000,
            monthly_gross=200000,
            basic=100000,
            hra=40000,
            special_allowance=30000,
            pf_deduction=12000,
            tax_deduction=18000,
            total_deductions=30000,
            net_pay=170000,
            currency="INR",
            last_paid=date.today() - timedelta(days=5),
            next_pay_date=date.today() + timedelta(days=25),
            next_increment_date=date.today() + timedelta(days=180),
            increment_cycle="annual"
        )
        db.add(admin_salary)
        
        # Create sample manager
        manager_user = User(
            email="manager@nexushr.com",
            hashed_password=get_password_hash("manager123"),
            full_name="John Manager",
            role="manager",
            is_active=True
        )
        db.add(manager_user)
        db.commit()
        db.refresh(manager_user)
        
        manager_employee = Employee(
            user_id=manager_user.id,
            employee_id="EMP002",
            department="Engineering",
            designation="Engineering Manager",
            join_date=date.today() - timedelta(days=300),
            location="Headquarters",
            manager_id=admin_employee.id,
            status="active"
        )
        db.add(manager_employee)
        db.commit()
        db.refresh(manager_employee)
        
        # Create salary for manager
        manager_salary = Salary(
            employee_id=manager_employee.id,
            annual_ctc=1800000,
            monthly_gross=150000,
            basic=75000,
            hra=30000,
            special_allowance=25000,
            pf_deduction=9000,
            tax_deduction=11000,
            total_deductions=20000,
            net_pay=130000,
            currency="INR",
            last_paid=date.today() - timedelta(days=5),
            next_pay_date=date.today() + timedelta(days=25),
            next_increment_date=date.today() + timedelta(days=180)
        )
        db.add(manager_salary)
        
        # Create sample employee
        employee_user = User(
            email="employee@nexushr.com",
            hashed_password=get_password_hash("employee123"),
            full_name="Jane Employee",
            role="employee",
            is_active=True
        )
        db.add(employee_user)
        db.commit()
        db.refresh(employee_user)
        
        sample_employee = Employee(
            user_id=employee_user.id,
            employee_id="EMP003",
            department="Engineering",
            designation="Software Engineer",
            join_date=date.today() - timedelta(days=100),
            location="Headquarters",
            manager_id=manager_employee.id,
            status="active",
            dob=date(1995, 5, 15),
            gender="Female",
            mobile="+1234567890"
        )
        db.add(sample_employee)
        db.commit()
        db.refresh(sample_employee)
        
        # Create salary for employee
        emp_salary = Salary(
            employee_id=sample_employee.id,
            annual_ctc=1200000,
            monthly_gross=100000,
            basic=50000,
            hra=20000,
            special_allowance=15000,
            pf_deduction=6000,
            tax_deduction=9000,
            total_deductions=15000,
            net_pay=85000,
            currency="INR",
            last_paid=date.today() - timedelta(days=5),
            next_pay_date=date.today() + timedelta(days=25),
            next_increment_date=date.today() + timedelta(days=265)
        )
        db.add(emp_salary)
        
        # Create leave balances for all employees
        current_year = date.today().year
        leave_types = [
            ("casual", 12),
            ("sick", 10),
            ("annual", 15),
            ("personal", 5)
        ]
        
        for emp in [admin_employee, manager_employee, sample_employee]:
            for leave_type, days in leave_types:
                balance = LeaveBalance(
                    employee_id=emp.id,
                    leave_type=leave_type,
                    year=current_year,
                    total_days=days,
                    used_days=0,
                    remaining_days=days
                )
                db.add(balance)
        
        # Create sample payslips
        for emp in [admin_employee, manager_employee, sample_employee]:
            salary = db.query(Salary).filter(Salary.employee_id == emp.id).first()
            if salary:
                for month in range(1, date.today().month + 1):
                    payslip = Payslip(
                        employee_id=emp.id,
                        month=month,
                        year=current_year,
                        amount=salary.net_pay,
                        status="paid" if month < date.today().month else "processing"
                    )
                    db.add(payslip)
        
        # Create company documents
        company_docs = [
            ("Employee Handbook", "policy"),
            ("Code of Conduct", "policy"),
            ("Leave Policy", "policy"),
            ("IT Security Guidelines", "guidelines"),
            ("Expense Reimbursement Policy", "policy")
        ]
        
        for name, doc_type in company_docs:
            doc = Document(
                name=name,
                doc_type=doc_type,
                is_company_doc=True,
                status="verified",
                file_url=f"/docs/{name.lower().replace(' ', '-')}.pdf"
            )
            db.add(doc)
        
        db.commit()
        print("Initial data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


# Create the FastAPI application instance
app = create_app()
