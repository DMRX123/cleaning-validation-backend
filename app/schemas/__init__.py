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
]