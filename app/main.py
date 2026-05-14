from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import os
import subprocess
import sys

from .api import auth

from .api import (
    products, equipment, calculations, validation, 
    reports, static_data, dashboard, cleaning_validation, protocols
)
from .database import init_db, get_db
from .config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cleaning Validation API",
    description="APIC Guideline Compliant Cleaning Validation System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# ==================== MIDDLEWARE ====================

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# CORS Middleware
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,https://cleaning-validation-frontend.vercel.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ==================== AUTO DATABASE SETUP FUNCTION ====================

def setup_database_on_startup():
    """Auto-create tables, seed data, and create admin user on first startup"""
    try:
        from app.database import SessionLocal
        from app.services.auth import AuthService
        from app.models.user import User
        from app.models.cleaning_level import CleaningLevel
        
        db = SessionLocal()
        
        # Check if tables are empty and setup needed
        try:
            # Check if users table has any data
            user_count = db.query(User).count()
            
            if user_count == 0:
                logger.info("📦 Database is empty. Running initial setup...")
                
                # Create admin user
                admin = User(
                    username='admin',
                    email='admin@cleaning-validation.com',
                    hashed_password=AuthService.get_password_hash('Admin@123'),
                    is_active=True,
                    is_admin=True
                )
                db.add(admin)
                db.commit()
                logger.info("✅ Admin user created: admin / Admin@123")
                
                # Run seed script for static data
                try:
                    seed_script = os.path.join(os.path.dirname(__file__), "..", "scripts", "seed_static_data.py")
                    if os.path.exists(seed_script):
                        result = subprocess.run(
                            [sys.executable, seed_script], 
                            capture_output=True, 
                            text=True
                        )
                        if result.returncode == 0:
                            logger.info("✅ Static data seeded successfully")
                        else:
                            logger.warning(f"⚠️ Seed warning: {result.stderr}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not run seed script: {e}")
            else:
                logger.info(f"✅ Database already has {user_count} users. Skipping setup.")
                
        except Exception as e:
            logger.warning(f"⚠️ Setup check warning: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Auto-setup error: {e}")

# ==================== LIFESPAN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Cleaning Validation API...")
    try:
        # Initialize database (creates tables if not exist)
        init_db()
        logger.info("✅ Database tables ready")
        
        # Run auto setup for data
        setup_database_on_startup()
        
        logger.info("🚀 Cleaning Validation API is ready!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Cleaning Validation API...")

# ==================== HEALTH & ROOT ENDPOINTS ====================

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database status"""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.warning(f"Database health check failed: {str(e)}")
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "2.0.0",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
def root():
    return {
        "message": "Cleaning Validation API is running",
        "status": "healthy",
        "version": "2.0.0",
        "documentation": "/docs",
        "apic_compliance": "100%"
    }

# ==================== ROUTERS ====================

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(calculations.router, prefix="/api/calculations", tags=["Calculations"])
app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(static_data.router, prefix="/api/static", tags=["Static Data"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(cleaning_validation.router, prefix="/api/cleaning-validation", tags=["APIC Guidelines"])
app.include_router(protocols.router, prefix="/api/protocols", tags=["Validation Protocols"])

# ==================== API INFO ENDPOINT ====================

@app.get("/api/info")
def api_info():
    return {
        "name": "Cleaning Validation System API",
        "version": "2.0.0",
        "description": "Complete APIC Guideline Compliant Cleaning Validation System",
        "status": "production_ready",
        "guideline_compliance": {
            "section_4.2.1": "ADE/PDE Calculation",
            "section_4.2.1.3": "TTC (Threshold of Toxicological Concern)",
            "section_4.2.2": "10 ppm General Limit",
            "section_4.2.3": "Therapeutic Macromolecules (1/1000th dose)",
            "section_4.2.4": "Swab Limits with Recovery",
            "section_4.2.5": "Rinse Limits with Volume Calculation",
            "section_4.2.6": "Different Limits Rationale",
            "section_5.0": "Levels of Cleaning (0,1,2)",
            "section_7.0": "Bracketing & Worst Case Rating",
            "section_8.1": "Microbiological Limits",
            "section_8.2": "Analytical Validation (LOQ/LOD/Recovery)",
            "section_8.3": "Sampling Methods (Swab/Rinse)",
            "section_9.0": "Validation Protocol",
            "section_9.7": "Dirty/Clean Hold Time",
            "section_10.0": "Revalidation & Change Control"
        },
        "endpoints": {
            "auth": "/api/auth",
            "products": "/api/products",
            "equipment": "/api/equipment",
            "calculations": "/api/calculations",
            "validation": "/api/validation",
            "reports": "/api/reports",
            "static": "/api/static",
            "dashboard": "/api/dashboard",
            "cleaning_validation": "/api/cleaning-validation",
            "protocols": "/api/protocols",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    }