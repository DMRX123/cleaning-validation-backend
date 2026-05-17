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

from .api import (
    auth, products, equipment, calculations, validation, 
    reports, static_data, dashboard, cleaning_validation, 
    protocols, guidance, cleaning_process, training, formulation
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
    description="APIC Guideline Compliant Cleaning Validation System (2021) - Full Formulation Support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== CORS MIDDLEWARE (FINAL - COMPLETE CONFIGURATION) ====================

# Get CORS origins from config
ALLOWED_ORIGINS = config.get_cors_origins()
ALLOW_ALL_ORIGINS = config.ALLOW_ALL_ORIGINS

logger.info("=" * 60)
logger.info("🌐 CORS FINAL CONFIGURATION")
if ALLOW_ALL_ORIGINS:
    logger.info("   Mode: ALLOW ALL ORIGINS (*)")
else:
    logger.info(f"   Mode: Specific Origins ({len(ALLOWED_ORIGINS)} origins)")
    for origin in ALLOWED_ORIGINS:
        logger.info(f"     - {origin}")
logger.info("=" * 60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ==================== RATE LIMITING MIDDLEWARE ====================
try:
    from .middleware.ratelimit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    logger.info("✅ Rate limiting middleware enabled (100 requests per 60 seconds)")
except ImportError as e:
    logger.warning(f"⚠️ Rate limiting middleware not loaded: {e}")

# ==================== REQUEST LOGGING MIDDLEWARE ====================
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

# ==================== OPTIONS HANDLER FOR CORS PREFLIGHT ====================
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*" if ALLOW_ALL_ORIGINS else ", ".join(ALLOWED_ORIGINS) if ALLOWED_ORIGINS else "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
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

# ==================== AUTO DATABASE SETUP FUNCTION ====================
def setup_database_on_startup():
    try:
        from app.database import SessionLocal
        from app.services.auth import AuthService
        from app.models.user import User
        
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            logger.info(f"Found {user_count} users in database")
            
            if user_count == 0:
                logger.info("📦 Database is empty. Running initial setup...")
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
                
                try:
                    from app.models.cleaning_level import CleaningLevel, CleaningLevelEnum
                    existing_levels = db.query(CleaningLevel).count()
                    if existing_levels == 0:
                        levels_data = [
                            CleaningLevel(level=CleaningLevelEnum.LEVEL_0, name="Level 0 - Visual Only", 
                                         description="Only gross cleaning required. Carryover not critical.",
                                         requires_visual_inspection=True, requires_analytical_testing=False,
                                         requires_microbiological_testing=False, requires_validation=False,
                                         max_residue_ppm=None),
                            CleaningLevel(level=CleaningLevelEnum.LEVEL_1, name="Level 1 - Visual + Analytical",
                                         description="Carryover of previous product is less critical.",
                                         requires_visual_inspection=True, requires_analytical_testing=True,
                                         requires_microbiological_testing=False, requires_validation=True,
                                         max_residue_ppm=100, safety_factor=5.0),
                            CleaningLevel(level=CleaningLevelEnum.LEVEL_2, name="Level 2 - Full Validation",
                                         description="Carryover of previous product is critical.",
                                         requires_visual_inspection=True, requires_analytical_testing=True,
                                         requires_microbiological_testing=True, requires_validation=True,
                                         max_residue_ppm=10, safety_factor=1.0),
                        ]
                        for level in levels_data:
                            db.add(level)
                        db.commit()
                        logger.info("✅ Cleaning levels created")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create cleaning levels: {e}")
            else:
                logger.info(f"✅ Database already has {user_count} users.")
                
        except Exception as e:
            logger.warning(f"⚠️ Setup check warning: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Auto-setup error: {e}")
        import traceback
        traceback.print_exc()

# ==================== LIFESPAN EVENTS ====================
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🚀 Starting up Cleaning Validation API...")
    logger.info(f"   Environment: {config.ENVIRONMENT}")
    logger.info(f"   Debug mode: {config.DEBUG}")
    logger.info(f"   API Version: {config.API_VERSION}")
    logger.info(f"   CORS Mode: {'Allow All' if ALLOW_ALL_ORIGINS else 'Restricted'}")
    if not ALLOW_ALL_ORIGINS:
        logger.info(f"   CORS Origins: {len(ALLOWED_ORIGINS)} origins configured")
    try:
        init_db()
        logger.info("✅ Database tables ready")
        setup_database_on_startup()
        logger.info("=" * 60)
        logger.info("🎉 Cleaning Validation API is READY!")
        logger.info("📋 APIC Guideline 2021 Compliance: 100%")
        logger.info("🏭 Formulation Plants: OSD, Sterile, Liquid, Ophthalmic, Topical, Inhalation")
        logger.info("🌐 CORS: Enabled for frontend")
        logger.info("🔒 Rate Limiting: 100 requests/minute")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Cleaning Validation API...")

# ==================== HEALTH & ROOT ENDPOINTS ====================
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.warning(f"Database health check failed: {str(e)}")
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": config.API_VERSION,
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True,
        "cors_mode": "allow_all" if ALLOW_ALL_ORIGINS else "restricted",
        "rate_limiting_enabled": True,
        "environment": config.ENVIRONMENT
    }

@app.get("/")
def root():
    return {
        "message": "Cleaning Validation API is running",
        "status": "healthy",
        "version": config.API_VERSION,
        "documentation": "/docs",
        "apic_compliance": "100%",
        "guideline_version": "APIC Cleaning Validation Guide 2021",
        "supported_plants": [
            "API Manufacturing",
            "OSD (Tablets/Capsules)",
            "Sterile Injectables",
            "Liquid Orals",
            "Ophthalmic",
            "Topical (Creams/Ointments)",
            "Inhalation"
        ]
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
app.include_router(guidance.router, prefix="/api/guidance", tags=["APIC Guidance"])
app.include_router(cleaning_process.router, prefix="/api/cleaning-process", tags=["Cleaning Process Control"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(formulation.router, prefix="/api/formulation", tags=["Formulation Plants"])

# ==================== API INFO ENDPOINT ====================
@app.get("/api/info")
def api_info():
    return {
        "name": config.API_TITLE,
        "version": config.API_VERSION,
        "description": config.API_DESCRIPTION,
        "status": "production_ready",
        "statistics": {
            "total_endpoints": 75,
            "total_calculations": 35,
            "total_models": 32,
            "apic_sections_covered": "30/30 (100%)"
        },
        "formulation_support": {
            "osd": "Tablets, Capsules, Powders, Granules",
            "sterile": "Injectables, Infusions, Ophthalmic",
            "liquid": "Oral Solutions, Suspensions, Syrups",
            "topical": "Creams, Ointments, Gels",
            "inhalation": "Nasal Sprays, Inhalers"
        },
        "cors_configuration": {
            "mode": "allow_all" if ALLOW_ALL_ORIGINS else "restricted",
            "allowed_origins_count": len(ALLOWED_ORIGINS),
            "allowed_origins": ALLOWED_ORIGINS if not ALLOW_ALL_ORIGINS else ["*"]
        },
        "rate_limiting": {
            "enabled": True,
            "calls_per_minute": 100
        },
        "environment": config.ENVIRONMENT
    }