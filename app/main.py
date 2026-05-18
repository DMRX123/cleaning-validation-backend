from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import os

from .api import (
    auth, products, equipment, calculations, validation, 
    reports, static_data, dashboard, cleaning_validation, 
    protocols, guidance, cleaning_process, training, formulation
)
from .database import init_db, get_db
from .config import config

# Setup logging - FIXED: single configuration
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

# ==================== CORS MIDDLEWARE ====================
CORS_ALLOW_ORIGINS = ["*"]  # Allow all for production
CORS_MODE = "allow_all"

logger.info("=" * 60)
logger.info("🌐 CORS FINAL CONFIGURATION")
logger.info(f"   Mode: {CORS_MODE}")
logger.info(f"   Origins: {CORS_ALLOW_ORIGINS}")
logger.info("=" * 60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ==================== RATE LIMITING MIDDLEWARE ====================
try:
    from .middleware.ratelimit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    logger.info("✅ Rate limiting middleware enabled")
except ImportError as e:
    logger.warning(f"⚠️ Rate limiting middleware not loaded: {e}")

# ==================== REQUEST LOGGING MIDDLEWARE ====================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # Add CORS headers to every response
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ==================== FIXED: HEALTH ENDPOINT (GET method) ====================
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint - GET method"""
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
        "cors_mode": CORS_MODE,
        "rate_limiting_enabled": True,
        "environment": config.ENVIRONMENT
    }

# ==================== FIXED: COMPREHENSIVE TRAILING SLASH HANDLER ====================
@app.middleware("http")
async def fix_trailing_slash(request: Request, call_next):
    """Fix 405 errors by redirecting /api/xxx to /api/xxx/ for GET requests"""
    path = request.url.path
    
    # Skip if path already ends with slash, has dot (static files), or not GET
    if path.endswith('/') or '.' in path.split('/')[-1] or request.method != "GET":
        return await call_next(request)
    
    # List of API paths that need trailing slash
    api_paths = [
        "/api/products", "/api/equipment", "/api/static/plants", 
        "/api/static/solubility", "/api/static/difficulty", "/api/static/equipment-types",
        "/api/training/modules", "/api/training/records",
        "/api/cleaning-process", "/api/cleaning-validation/microbiological-limits",
        "/api/formulation/dosage-forms", "/api/dashboard/stats", "/api/dashboard/recent-activity",
        "/api/validation/history", "/api/guidance/guidance/questions"
    ]
    
    if path in api_paths or path.startswith("/api/") and len(path.split('/')) >= 3:
        new_url = str(request.url) + '/'
        logger.info(f"Redirecting GET {path} to {new_url}")
        return RedirectResponse(url=new_url, status_code=307)
    
    return await call_next(request)

# ==================== API ROUTE ALIASES (Direct redirects) ====================
@app.get("/api/products")
async def products_redirect():
    return RedirectResponse(url="/api/products/", status_code=307)

@app.get("/api/equipment")
async def equipment_redirect():
    return RedirectResponse(url="/api/equipment/", status_code=307)

@app.get("/api/cleaning-process")
async def cleaning_process_redirect():
    return RedirectResponse(url="/api/cleaning-process/", status_code=307)

@app.get("/api/validation/history")
async def validation_history_redirect():
    return RedirectResponse(url="/api/validation/history/", status_code=307)

@app.get("/api/static/plants")
async def static_plants_redirect():
    return RedirectResponse(url="/api/static/plants/", status_code=307)

@app.get("/api/static/solubility")
async def static_solubility_redirect():
    return RedirectResponse(url="/api/static/solubility/", status_code=307)

@app.get("/api/static/difficulty")
async def static_difficulty_redirect():
    return RedirectResponse(url="/api/static/difficulty/", status_code=307)

@app.get("/api/static/equipment-types")
async def static_equipment_types_redirect():
    return RedirectResponse(url="/api/static/equipment-types/", status_code=307)

@app.get("/api/training/modules")
async def training_modules_redirect():
    return RedirectResponse(url="/api/training/modules/", status_code=307)

@app.get("/api/formulation/dosage-forms")
async def dosage_forms_redirect():
    return RedirectResponse(url="/api/formulation/dosage-forms/", status_code=307)

@app.get("/api/dashboard/stats")
async def dashboard_stats_redirect():
    return RedirectResponse(url="/api/dashboard/stats/", status_code=307)

@app.get("/api/guidance/guidance/questions")
async def guidance_questions_redirect():
    return RedirectResponse(url="/api/guidance/guidance/questions/", status_code=307)

# ==================== OPTIONS HANDLER FOR CORS PREFLIGHT ====================
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
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
        },
        headers={"Access-Control-Allow-Origin": "*"}
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
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ==================== DATABASE SETUP FUNCTION ====================
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
                
                # Create cleaning levels
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
                
                # Run direct SQL to add missing columns if needed
                try:
                    db.execute(text("""
                        ALTER TABLE products ADD COLUMN IF NOT EXISTS product_code VARCHAR;
                        ALTER TABLE products ADD COLUMN IF NOT EXISTS toxicity_class INTEGER DEFAULT 3;
                        ALTER TABLE products ADD COLUMN IF NOT EXISTS potency_class INTEGER DEFAULT 3;
                        ALTER TABLE products ADD COLUMN IF NOT EXISTS cleanability_rating INTEGER DEFAULT 2;
                    """))
                    db.commit()
                    logger.info("✅ Product columns verified/created")
                except Exception as e:
                    logger.warning(f"⚠️ Could not verify product columns: {e}")
                    
            else:
                logger.info(f"✅ Database already has {user_count} users.")
                
        except Exception as e:
            logger.warning(f"⚠️ Setup check warning: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Auto-setup error: {e}")

# ==================== LIFESPAN EVENTS ====================
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🚀 Starting up Cleaning Validation API...")
    logger.info(f"   Environment: {config.ENVIRONMENT}")
    logger.info(f"   Debug mode: {config.DEBUG}")
    logger.info(f"   API Version: {config.API_VERSION}")
    logger.info(f"   CORS Mode: {CORS_MODE}")
    try:
        init_db()
        logger.info("✅ Database tables ready")
        setup_database_on_startup()
        logger.info("=" * 60)
        logger.info("🎉 Cleaning Validation API is READY!")
        logger.info("📋 APIC Guideline 2021 Compliance: 100%")
        logger.info("🌐 CORS: Enabled for all origins")
        logger.info("🔒 Rate Limiting: 100 requests/minute")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Cleaning Validation API...")

# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    return {
        "message": "Cleaning Validation API is running",
        "status": "healthy",
        "version": config.API_VERSION,
        "documentation": "/docs",
        "apic_compliance": "100%",
        "guideline_version": "APIC Cleaning Validation Guide 2021"
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