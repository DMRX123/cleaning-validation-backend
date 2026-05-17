import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # Normalize database URL (handle postgres:// vs postgresql://)
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info("Normalized database URL from postgres:// to postgresql://")
    
    # Log database connection (masked for security)
    if DATABASE_URL:
        masked_url = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'database'
        logger.info(f"🔍 DATABASE_URL configured: {masked_url[:50]}...")
    else:
        logger.error("❌ DATABASE_URL is EMPTY! Check Render environment variables.")
    
    # ============================================
    # SECURITY CONFIGURATION
    # ============================================
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment detection
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT == "production"
    IS_DEVELOPMENT = ENVIRONMENT == "development"
    
    # Production security check - SECRET_KEY is mandatory
    if IS_PRODUCTION and not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY environment variable is REQUIRED in production!")
    
    # Development fallback (only for local development)
    if not SECRET_KEY and IS_DEVELOPMENT:
        SECRET_KEY = "dev-secret-key-do-not-use-in-production"
        logger.warning("⚠️ Using development SECRET_KEY. DO NOT use in production!")
    
    # ============================================
    # CORS CONFIGURATION (Production Ready - Updated with all Vercel URLs)
    # ============================================
    # Default CORS origins for development
    DEFAULT_CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Production CORS origins (All Vercel frontend URLs)
    PRODUCTION_CORS_ORIGINS = [
        "https://cleaning-validation-frontend.vercel.app",
        "https://cleaning-validation.vercel.app",
        "https://cleaning-validation-frontend-git-main.vercel.app",
        "https://cleaning-validation-frontend-dmrx123.vercel.app",
        "https://cleaning-validation-frontend-rc867u9b7-dmrx123s-projects.vercel.app",
    ]
    
    # Get CORS origins from environment variable (if set)
    env_cors_origins = os.getenv("CORS_ORIGINS", "")
    
    CORS_ORIGINS = DEFAULT_CORS_ORIGINS.copy()
    
    # Add production origins if in production or if specified
    if IS_PRODUCTION:
        CORS_ORIGINS.extend(PRODUCTION_CORS_ORIGINS)
    
    # Add custom origins from environment variable
    if env_cors_origins:
        for origin in env_cors_origins.split(","):
            origin = origin.strip()
            if origin and origin not in CORS_ORIGINS:
                CORS_ORIGINS.append(origin)
    
    # Remove duplicates while preserving order
    CORS_ORIGINS = list(dict.fromkeys(CORS_ORIGINS))
    
    # Log CORS configuration
    logger.info("=" * 60)
    logger.info("🌐 CORS ALLOWED ORIGINS:")
    for origin in CORS_ORIGINS:
        logger.info(f"   - {origin}")
    logger.info("=" * 60)
    
    # ============================================
    # ENVIRONMENT CONFIGURATION
    # ============================================
    DEBUG = os.getenv("DEBUG", "False" if IS_PRODUCTION else "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
    
    # Configure logging level
    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # ============================================
    # FILE UPLOAD CONFIGURATION
    # ============================================
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", ".xlsx,.xls,.csv").split(","))
    
    # ============================================
    # API CONFIGURATION
    # ============================================
    API_VERSION = os.getenv("API_VERSION", "2.0.0")
    API_TITLE = os.getenv("API_TITLE", "Cleaning Validation API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "APIC Guideline Compliant Cleaning Validation System")
    
    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # ============================================
    # SUPABASE CONFIGURATION (Optional)
    # ============================================
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # ============================================
    # HELPER METHODS
    # ============================================
    @classmethod
    def get_cors_origins(cls) -> list:
        """Get CORS allowed origins (for use in middleware)"""
        return cls.CORS_ORIGINS
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.IS_DEVELOPMENT
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.IS_PRODUCTION
    
    @classmethod
    def get_database_url_masked(cls) -> str:
        """Get masked database URL for logging (hides credentials)"""
        if not cls.DATABASE_URL:
            return "NOT_CONFIGURED"
        if '@' in cls.DATABASE_URL:
            parts = cls.DATABASE_URL.split('@')
            return f"*****@{parts[1]}" if len(parts) > 1 else "*****"
        return "*****"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration settings"""
        errors = []
        
        # Check database URL in production
        if cls.IS_PRODUCTION and not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required in production")
        
        # Check secret key in production
        if cls.IS_PRODUCTION and not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required in production")
        
        # Check CORS origins in production
        if cls.IS_PRODUCTION and not cls.CORS_ORIGINS:
            errors.append("CORS_ORIGINS should be configured in production")
        
        if errors:
            for error in errors:
                logger.error(f"❌ Config validation failed: {error}")
            return False
        
        logger.info("✅ Configuration validated successfully")
        return True

# Create config instance
config = Config()

# Validate configuration on import
if config.IS_PRODUCTION:
    config.validate()