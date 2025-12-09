"""
Attendance tracking models.

This module defines models for tracking employee attendance,
clock-in/clock-out times, and break periods.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Attendance(Base):
    """
    Daily attendance record.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee
        date: Attendance date
        clock_in: Clock-in timestamp
        clock_out: Clock-out timestamp
        status: Attendance status (present, absent, half_day, wfh)
        total_hours: Total working hours
        notes: Additional notes
    """
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    clock_in = Column(DateTime(timezone=True))
    clock_out = Column(DateTime(timezone=True))
    status = Column(String(50), default="present")
    total_hours = Column(String(20))
    notes = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="attendances")
    breaks = relationship("Break", back_populates="attendance", cascade="all, delete-orphan")


class Break(Base):
    """
    Break period during a workday.
    
    Attributes:
        id: Primary key
        attendance_id: Foreign key to Attendance
        start_time: Break start timestamp
        end_time: Break end timestamp
        duration_minutes: Break duration in minutes
    """
    __tablename__ = "breaks"
    
    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendances.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    
    # Relationships
    attendance = relationship("Attendance", back_populates="breaks")
