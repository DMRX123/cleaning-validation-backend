import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    logger.info(f"🔍 DATABASE_URL from os.getenv: {DATABASE_URL[:50] if DATABASE_URL else 'EMPTY!'}...")
    
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL is EMPTY! Check Render environment variables.")
    
    # Security Configuration - MANDATORY in production
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Production security check
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    if ENVIRONMENT == "production" and not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY environment variable is REQUIRED in production!")
    
    # Fallback for development only
    if not SECRET_KEY and ENVIRONMENT != "production":
        SECRET_KEY = "dev-secret-key-do-not-use-in-production"
        logger.warning("⚠️ Using development SECRET_KEY. DO NOT use in production!")
    
    # Environment Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", ".xlsx,.xls,.csv").split(","))
    
    # API Configuration
    API_VERSION = os.getenv("API_VERSION", "2.0.0")
    API_TITLE = os.getenv("API_TITLE", "Cleaning Validation API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "APIC Guideline Compliant Cleaning Validation System")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

config = Config()