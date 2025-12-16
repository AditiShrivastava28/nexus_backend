"""
Employee model and related employment data.

This module defines the Employee model which stores employee profile
information and employment history.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Employee(Base):
    """
    Employee profile model.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User table
        employee_id: Company-assigned employee ID
        department: Department name
        designation: Job title/designation
        join_date: Date of joining
        location: Work location
        manager_id: Foreign key to manager's Employee record
        dob: Date of birth
        gender: Gender
        marital_status: Marital status
        blood_group: Blood group
        address: Residential address
        personal_email: Personal email address
        mobile: Mobile phone number
        avatar_url: Profile picture URL
        status: Employment status (active, on_leave, terminated)
    """
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100))
    designation = Column(String(100))
    join_date = Column(Date)
    location = Column(String(100))
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Personal information
    dob = Column(Date)
    gender = Column(String(20))
    marital_status = Column(String(50))
    blood_group = Column(String(10))
    address = Column(Text)
    personal_email = Column(String(255))
    mobile = Column(String(20))

    avatar_url = Column(String(500))
    status = Column(String(50), default="in-probation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employee")
    manager = relationship("Employee", remote_side=[id], backref="team_members")
    jobs = relationship("EmployeeJob", back_populates="employee", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="employee", foreign_keys="Document.employee_id", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="employee", foreign_keys="Leave.employee_id", cascade="all, delete-orphan")
    leave_balances = relationship("LeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    salary = relationship("Salary", back_populates="employee", uselist=False)
    payslips = relationship("Payslip", back_populates="employee", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    requests = relationship("Request", foreign_keys="Request.requester_id", back_populates="requester")


class EmployeeJob(Base):
    """
    Employment history / past jobs.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        company: Company name
        designation: Job title
        start_date: Start date of employment
        end_date: End date of employment
        description: Job description
    """
    __tablename__ = "employee_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    company = Column(String(255), nullable=False)
    designation = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="jobs")
