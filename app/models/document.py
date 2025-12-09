"""
Document management model.

This module defines the Document model for storing employee
documents (ID proofs, certificates, etc.) and company policies.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Document(Base):
    """
    Employee or company document.
    
    Attributes:
        id: Primary key
        employee_id: Foreign key to Employee (null for company docs)
        name: Document name
        doc_type: Type of document
        file_url: URL to the document file
        status: Verification status (pending, verified, rejected)
        verified_by: Employee ID who verified
        verified_date: Date of verification
        is_company_doc: Whether this is a company policy document
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    name = Column(String(255), nullable=False)
    doc_type = Column(String(100))
    file_url = Column(String(500))
    status = Column(String(50), default="pending")
    verified_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    verified_date = Column(Date)
    is_company_doc = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="documents", foreign_keys=[employee_id])
    verifier = relationship("Employee", foreign_keys=[verified_by])
