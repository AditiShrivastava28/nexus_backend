"""
Request management model.

This module defines the Request model for handling various employee
requests (WFH, regularization, expense, help tickets).
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Request(Base):
    """
    Employee request model (WFH, expense, help, regularization).
    
    Attributes:
        id: Primary key
        requester_id: Foreign key to Employee who made request
        request_type: Type of request (wfh, expense, help, regularization)
        title: Request title
        description: Detailed description
        date: Request date or target date
        end_date: End date for multi-day requests
        amount: Amount for expense claims
        # Note: approval/status tracking removed. Approval flows are handled
        # outside this model (or removed) and are not stored on Request.
        details: Additional JSON details
    """
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    request_type = Column(String(50), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    date = Column(Date)
    end_date = Column(Date)
    amount = Column(Float)
    # status and approved_by columns removed
    
    details = Column(Text)  # JSON string for additional details
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    requester = relationship("Employee", back_populates="requests", foreign_keys=[requester_id])
    # approver relationship removed
