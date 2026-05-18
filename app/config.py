import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class Config:
    # DATABASE CONFIGURATION
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info("Normalized database URL")
    
    if DATABASE_URL:
        masked_url = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'database'
        logger.info(f"🔍 DATABASE_URL configured: {masked_url[:50]}...")
    else:
        logger.error("❌ DATABASE_URL is EMPTY!")
    
    # SECURITY CONFIGURATION
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT == "production"
    IS_DEVELOPMENT = ENVIRONMENT == "development"
    
    if IS_PRODUCTION and not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY is REQUIRED in production!")
    
    if not SECRET_KEY and IS_DEVELOPMENT:
        SECRET_KEY = "dev-secret-key-do-not-use-in-production"
        logger.warning("⚠️ Using development SECRET_KEY")
    
    # CORS CONFIGURATION
    ALLOW_ALL_ORIGINS = os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true"
    
    # ENVIRONMENT CONFIGURATION
    DEBUG = os.getenv("DEBUG", "False" if IS_PRODUCTION else "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
    
    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # FILE UPLOAD CONFIGURATION
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", ".xlsx,.xls,.csv").split(","))
    
    # API CONFIGURATION
    API_VERSION = os.getenv("API_VERSION", "2.0.0")
    API_TITLE = os.getenv("API_TITLE", "Cleaning Validation API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "APIC Guideline Compliant Cleaning Validation System")
    
    # RATE LIMITING
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # SUPABASE CONFIGURATION
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    @classmethod
    def get_cors_origins(cls) -> list:
        if cls.ALLOW_ALL_ORIGINS:
            return ["*"]
        return ["*"]  # Default to allow all
    
    @classmethod
    def is_development(cls) -> bool:
        return cls.IS_DEVELOPMENT
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.IS_PRODUCTION
    
    @classmethod
    def validate(cls) -> bool:
        errors = []
        if cls.IS_PRODUCTION and not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required in production")
        if cls.IS_PRODUCTION and not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required in production")
        if errors:
            for error in errors:
                logger.error(f"❌ Config validation failed: {error}")
            return False
        logger.info("✅ Configuration validated successfully")
        return True


config = Config()

if config.IS_PRODUCTION:
    config.validate()