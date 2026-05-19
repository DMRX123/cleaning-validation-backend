# Backend app package
__version__ = "3.0.0"
__description__ = "APIC Guideline Compliant Cleaning Validation API (2021) - Full CRUD"
__author__ = "Cleaning Validation Team"

from .main import app

from .api import (
    auth, products, equipment, calculations, validation,
    # reports,  # REMOVED - Old report system deleted
    static_data, dashboard,
    # protocols,  # REMOVED - Old protocol system deleted
    guidance, cleaning_process, training, formulation, comprehensive,
    hold_times, protocol_generator, report_generator  # ADDED report_generator
)

from .models import (
    Product, Equipment, ValidationSession, User, 
    ValidationProtocol, CleaningLevelEnum,
    CleaningProcess, CleaningParameter, CleaningExecution,
    DosageForm, DosageFormEnum, PlantTypeEnum,
    SamplingLocation, SamplingResult, SamplingMethodEnum,
    FormulationEquipment, EquipmentCategoryEnum,
    ValidationReport  # ADDED
)

from .services import (
    MACOService, SwabService, RinseService, CleaningLevelService,
    HoldTimeService, BracketingService, ADEService, GuidanceService,
    CleaningProcessService, CleaningCapabilityService, FormulationService,
    ProtocolGeneratorService, ReportGeneratorService  # ADDED
)

__all__ = [
    "app",
    "auth", "products", "equipment", "calculations", "validation",
    # "reports",  # REMOVED
    "static_data", "dashboard",
    # "protocols",  # REMOVED
    "guidance", "cleaning_process", "training", "formulation", "comprehensive",
    "hold_times", "protocol_generator", "report_generator",  # ADDED report_generator
    "Product", "Equipment", "ValidationSession", "User", "ValidationProtocol",
    "CleaningLevelEnum", "CleaningProcess", "CleaningParameter", "CleaningExecution",
    "DosageForm", "DosageFormEnum", "PlantTypeEnum", "SamplingLocation",
    "SamplingResult", "SamplingMethodEnum", "FormulationEquipment", "EquipmentCategoryEnum",
    "ValidationReport",  # ADDED
    "MACOService", "SwabService", "RinseService", "CleaningLevelService",
    "HoldTimeService", "BracketingService", "ADEService", "GuidanceService",
    "CleaningProcessService", "CleaningCapabilityService", "FormulationService",
    "ProtocolGeneratorService", "ReportGeneratorService",  # ADDED
]