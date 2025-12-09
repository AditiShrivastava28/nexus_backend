"""
Asset-related Pydantic schemas.

This module defines schemas for asset management operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class AssetCreate(BaseModel):
    """
    Schema for assigning an asset.
    
    Attributes:
        name: Asset name
        asset_type: Type of asset
        serial_number: Serial number
    """
    name: str
    asset_type: Optional[str] = None
    serial_number: Optional[str] = None


class AssetResponse(BaseModel):
    """
    Asset response schema.
    
    Attributes:
        id: Asset ID
        name: Asset name
        type: Asset type
        serial: Serial number
        assignedDate: Date assigned
    """
    id: int
    name: str
    type: Optional[str] = None
    serial: Optional[str] = None
    assignedDate: Optional[date] = None

    class Config:
        from_attributes = True
