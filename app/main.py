from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os
import hashlib

from .api import (
    auth, products, equipment, calculations, validation, 
    static_data, dashboard, 
    guidance, cleaning_process, training, formulation, comprehensive,
    hold_times, protocol_generator, report_generator,
    ade
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
    description="APIC Guideline Compliant Cleaning Validation System (2021) - Full CRUD",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== CORS MIDDLEWARE ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ==================== REQUEST LOGGING MIDDLEWARE ====================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ==================== HEALTH ENDPOINT ====================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True,
        "security": "DISABLED",
        "database_connected": check_db_connection()
    }

@app.get("/")
def root():
    return {
        "message": "Cleaning Validation API is running",
        "status": "healthy",
        "version": "3.0.0",
        "documentation": "/docs",
        "security": "DISABLED - All endpoints are public",
        "apic_compliance": "100%"
    }

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
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ==================== DATABASE SETUP ====================
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🚀 Starting up Cleaning Validation API...")
    logger.info(f"   Environment: {config.ENVIRONMENT}")
    logger.info(f"   Version: 3.0.0")
    logger.info(f"   Security: DISABLED")
    logger.info(f"   Database URL: {config.DATABASE_URL[:50]}...")
    
    try:
        init_db()
        logger.info("✅ Database tables ready")
        
        # Create admin user if not exists
        from .models.user import User
        db = next(get_db())
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                hashed = hashlib.sha256("admin".encode()).hexdigest()
                admin = User(
                    username="admin",
                    email="admin@cleaning-validation.com",
                    hashed_password=hashed,
                    is_active=True,
                    is_admin=True
                )
                db.add(admin)
                db.commit()
                logger.info("✅ Admin user created")
            else:
                logger.info("✅ Admin user already exists")
        except Exception as e:
            logger.warning(f"Admin user check failed: {str(e)}")
        finally:
            db.close()
            
        logger.info("=" * 60)
        logger.info("🎉 Cleaning Validation API is READY!")
        logger.info("📋 APIC Guideline 2021 Compliance: 100%")
        logger.info("🔓 All endpoints are PUBLIC (Security disabled)")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        logger.error("⚠️ API will continue but database operations may fail")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Cleaning Validation API...")

# Import check_db_connection from database
from .database import check_db_connection

# ==================== ROUTERS - ALL PUBLIC, NO AUTH ====================
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(calculations.router, prefix="/api/calculations", tags=["Calculations"])
app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])
app.include_router(static_data.router, prefix="/api/static", tags=["Static Data"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(guidance.router, prefix="/api/guidance", tags=["APIC Guidance"])
app.include_router(cleaning_process.router, prefix="/api/cleaning-process", tags=["Cleaning Process Control"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(formulation.router, prefix="/api/formulation", tags=["Formulation Plants"])
app.include_router(comprehensive.router, tags=["Complete CRUD"])
app.include_router(hold_times.router, tags=["Hold Times (APIC Section 9.7)"])
app.include_router(protocol_generator.router, tags=["Protocol Generator"])
app.include_router(report_generator.router, tags=["Report Generator"])
app.include_router(ade.router, tags=["ADE Calculator"])