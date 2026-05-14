from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not config.DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set")
    raise ValueError("DATABASE_URL environment variable is not set")

db_url_masked = config.DATABASE_URL.split('@')[-1] if '@' in config.DATABASE_URL else 'database'
logger.info(f"Connecting to database: {db_url_masked}")

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency function with retry logic for database session"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        db = SessionLocal()
        try:
            # Test connection
            db.execute(text("SELECT 1"))
            yield db
            break
        except Exception as e:
            db.close()
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"All {max_retries} connection attempts failed")
                raise
        finally:
            db.close()

def init_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_engine():
    return engine

def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False