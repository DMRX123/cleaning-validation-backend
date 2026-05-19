import os
from dotenv import load_dotenv
import logging

# Force load .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    # DATABASE CONFIGURATION
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cleaning_validation.db")
    
    # Normalize database URL
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Fix for Render PostgreSQL - ensure sslmode is correct
    if DATABASE_URL and "render.com" in DATABASE_URL:
        if "sslmode=require" not in DATABASE_URL and "?" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"
        elif "sslmode=require" not in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
    
    # For local development with remote PostgreSQL (disable this check for production)
    if DATABASE_URL and "postgresql" in DATABASE_URL and "localhost" not in DATABASE_URL:
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.warning("⚠️ Switching from remote PostgreSQL to local SQLite for development")
            DATABASE_URL = "sqlite:///./cleaning_validation.db"
    
    # SECURITY CONFIGURATION
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-do-not-use-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT == "production"
    IS_DEVELOPMENT = ENVIRONMENT == "development"
    
    # CORS CONFIGURATION
    ALLOW_ALL_ORIGINS = os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true"
    
    # ENVIRONMENT CONFIGURATION
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # API CONFIGURATION
    API_VERSION = os.getenv("API_VERSION", "3.0.0")
    API_TITLE = os.getenv("API_TITLE", "Cleaning Validation API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "APIC Guideline Compliant Cleaning Validation System")
    
    # RATE LIMITING
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    @classmethod
    def get_cors_origins(cls) -> list:
        if cls.ALLOW_ALL_ORIGINS:
            return ["*"]
        cors_origins = os.getenv("CORS_ORIGINS", "")
        return [origin.strip() for origin in cors_origins.split(",") if origin.strip()] or ["*"]
    
    @classmethod
    def is_development(cls) -> bool:
        return cls.IS_DEVELOPMENT
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.IS_PRODUCTION


config = Config()