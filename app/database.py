from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log database connection (hide password)
db_url_for_log = config.DATABASE_URL
if "@" in db_url_for_log:
    parts = db_url_for_log.split("@")
    if len(parts) > 1:
        db_url_for_log = f"{parts[0].split(':')[0]}:***@{parts[1]}"
logger.info(f"📁 Connecting to database: {db_url_for_log}")

# Create engine based on database type
if "sqlite" in config.DATABASE_URL:
    engine = create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # PostgreSQL connection
    connect_args = {}
    if "render.com" in config.DATABASE_URL:
        connect_args = {"sslmode": "require"}
    
    engine = create_engine(
        config.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
        pool_recycle=3600,
        connect_args=connect_args
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency function for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection verified")
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