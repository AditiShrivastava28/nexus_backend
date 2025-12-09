"""
Document-related Pydantic schemas.

This module defines schemas for document management operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class DocumentResponse(BaseModel):
    """
    Document response schema.
    
    Attributes:
        id: Document ID
        name: Document name
        status: Verification status
        date: Upload/verification date
    """
    id: int
    name: str
    status: str
    date: Optional[date] = None

    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """
    Schema for document upload.
    
    Attributes:
        name: Document name
        doc_type: Document type
        file_url: File URL
    """
    name: str
    doc_type: Optional[str] = None
    file_url: str


class CompanyDocumentResponse(BaseModel):
    """
    Company policy document response.
    
    Attributes:
        id: Document ID
        name: Document name
        doc_type: Document type
        file_url: File URL
    """
    id: int
    name: str
    doc_type: Optional[str] = None
    file_url: Optional[str] = None

    class Config:
        from_attributes = True
