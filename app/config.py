"""
Configuration settings for the NexusHR application.

This module handles loading environment variables and defining
application configuration settings.
"""

import os
from typing import Optional


class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        DATABASE_URL: PostgreSQL connection string
        SECRET_KEY: Secret key for JWT token signing
        ALGORITHM: Algorithm used for JWT encoding
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
    """
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT configuration
    SECRET_KEY: str = os.getenv("SESSION_SECRET", "nexushr-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Application settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "NexusHR API"
    VERSION: str = "1.0.0"


settings = Settings()
