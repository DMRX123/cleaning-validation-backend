"""
Pydantic Schemas for Request/Response Validation
All schemas are used by FastAPI endpoints
"""

from .product import ProductCreate, ProductUpdate, ProductResponse
from .equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from .calculation import (
    MACORequest, MACOResponse, 
    SwabLimitRequest, SwabLimitResponse,
    RinseLimitRequest, RinseLimitResponse,
    WorstCaseRequest
)
from .result import SwabResultCreate, RinseResultCreate, ResultResponse
from .protocol import (
    ProtocolCreate, ProtocolUpdate, ProtocolResponse,
    ProtocolExecutionCreate, ProtocolExecutionResponse
)
from .ade import ADECalculationRequest, ADECalculationResponse
from .guidance import GuidanceQuestionResponse, RevalidationCheckRequest, RevalidationCheckResponse
from .cleaning_process import (
    CleaningProcessCreate, CleaningProcessResponse,
    CleaningParameterCreate, CleaningExecutionCreate,
    CleaningCapabilityRequest, CleaningCapabilityResponse,
    CleaningTypeEnum, CleaningStep, CleaningAgent
)

__all__ = [
    # Product Schemas
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    
    # Equipment Schemas
    "EquipmentCreate",
    "EquipmentUpdate",
    "EquipmentResponse",
    
    # Calculation Schemas
    "MACORequest",
    "MACOResponse",
    "SwabLimitRequest",
    "SwabLimitResponse",
    "RinseLimitRequest",
    "RinseLimitResponse",
    "WorstCaseRequest",
    
    # Result Schemas
    "SwabResultCreate",
    "RinseResultCreate",
    "ResultResponse",
    
    # Protocol Schemas (Section 9.0)
    "ProtocolCreate",
    "ProtocolUpdate",
    "ProtocolResponse",
    "ProtocolExecutionCreate",
    "ProtocolExecutionResponse",
    
    # ADE Calculation Schemas (Section 4.2.1.1)
    "ADECalculationRequest",
    "ADECalculationResponse",
    
    # Guidance Schemas (Section 10.0)
    "GuidanceQuestionResponse",
    "RevalidationCheckRequest",
    "RevalidationCheckResponse",
    
    # Cleaning Process Schemas (Section 6.0)
    "CleaningProcessCreate",
    "CleaningProcessResponse",
    "CleaningParameterCreate",
    "CleaningExecutionCreate",
    "CleaningCapabilityRequest",
    "CleaningCapabilityResponse",
    "CleaningTypeEnum",
    "CleaningStep",
    "CleaningAgent",
]