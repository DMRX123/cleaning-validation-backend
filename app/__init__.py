# Backend app package
# FastAPI application for Cleaning Validation System

__version__ = "2.0.0"
__description__ = "APIC Guideline Compliant Cleaning Validation API (2021)"
__author__ = "Cleaning Validation Team"

# Export main app for easy import
from .main import app

# Export all major components for easy access
from .api import (
    auth, products, equipment, calculations, validation,
    reports, static_data, dashboard, cleaning_validation, 
    protocols, guidance, cleaning_process
)
from .models import (
    Product, Equipment, ValidationSession, User, 
    ValidationProtocol, CleaningLevelEnum,
    CleaningProcess, CleaningParameter, CleaningExecution
)
from .services import (
    MACOService, SwabService, RinseService, CleaningLevelService,
    HoldTimeService, BracketingService, ADEService, GuidanceService,
    CleaningProcessService, CleaningCapabilityService
)

__all__ = [
    "app",
    "auth",
    "products", 
    "equipment",
    "calculations",
    "validation",
    "reports",
    "static_data", 
    "dashboard",
    "cleaning_validation",
    "protocols",
    "guidance",
    "cleaning_process",
    "Product",
    "Equipment", 
    "ValidationSession",
    "User",
    "ValidationProtocol",
    "CleaningLevelEnum",
    "CleaningProcess",
    "CleaningParameter",
    "CleaningExecution",
    "MACOService",
    "SwabService", 
    "RinseService",
    "CleaningLevelService",
    "HoldTimeService",
    "BracketingService",
    "ADEService",
    "GuidanceService",
    "CleaningProcessService",
    "CleaningCapabilityService",
]