"""
Database connection and session management.

This module configures the SQLAlchemy engine, session factory,
and provides the base class for all database models.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# Create the SQLAlchemy engine with the PostgreSQL database URL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections every 5 minutes
)

# Create a configured session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    
    Yields:
        Session: A SQLAlchemy database session
        
    Note:
        The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
