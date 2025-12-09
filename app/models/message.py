"""
Messaging model for team communication.

This module defines the Message model for internal team messaging.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Message(Base):
    """
    Message between employees.
    
    Attributes:
        id: Primary key
        sender_id: Foreign key to sender Employee
        receiver_id: Foreign key to receiver Employee
        content: Message content
        is_read: Whether message has been read
        sent_at: Timestamp when message was sent
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("Employee", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("Employee", foreign_keys=[receiver_id], back_populates="received_messages")
