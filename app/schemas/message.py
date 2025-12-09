"""
Message-related Pydantic schemas.

This module defines schemas for team messaging operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """
    Schema for sending a message.
    
    Attributes:
        content: Message content
    """
    content: str


class MessageResponse(BaseModel):
    """
    Message response schema.
    
    Attributes:
        id: Message ID
        sender_id: Sender employee ID
        receiver_id: Receiver employee ID
        content: Message content
        is_read: Whether read
        sent_at: Timestamp
        sender_name: Sender's name
    """
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    sent_at: datetime
    sender_name: Optional[str] = None

    class Config:
        from_attributes = True
