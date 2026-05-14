from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class CleaningTypeEnum(str, Enum):
    MANUAL = "manual"
    AUTOMATED_CIP = "automated_cip"
    AUTOMATED_COP = "automated_cop"
    SEMI_AUTOMATED = "semi_automated"

class CleaningStep(BaseModel):
    step: int
    action: str
    duration_min: float
    temperature_c: Optional[float] = None
    flow_rate_lpm: Optional[float] = None

class CleaningAgent(BaseModel):
    name: str
    concentration_percent: float
    volume_l: float

class CleaningProcessCreate(BaseModel):
    process_code: str
    name: str
    description: Optional[str] = None
    cleaning_type: CleaningTypeEnum
    system_boundaries: Optional[str] = None
    cleaning_agents: Optional[List[Dict]] = None
    solvents_used: Optional[List[str]] = None
    process_steps: Optional[List[CleaningStep]] = None
    equipment_ids: Optional[List[int]] = None
    has_in_process_analysis: bool = False
    in_process_analysis_methods: Optional[List[str]] = None
    min_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None
    min_flow_rate_lpm: Optional[float] = None
    max_flow_rate_lpm: Optional[float] = None
    min_pressure_bar: Optional[float] = None
    max_pressure_bar: Optional[float] = None
    min_duration_min: Optional[float] = None
    max_duration_min: Optional[float] = None
    sop_reference: Optional[str] = None
    sop_version: Optional[str] = None
    training_required: bool = True
    created_by: Optional[str] = None

class CleaningParameterCreate(BaseModel):
    parameter_name: str
    parameter_unit: str
    target_value: Optional[float] = None
    min_acceptable: float
    max_acceptable: float
    is_critical: bool = True
    is_controlled_automatically: bool = False
    measurement_method: Optional[str] = None
    measurement_frequency: Optional[str] = None

class CleaningExecutionCreate(BaseModel):
    process_id: int
    session_id: Optional[int] = None
    executed_by: str
    actual_temperature_c: Optional[float] = None
    actual_flow_rate_lpm: Optional[float] = None
    actual_pressure_bar: Optional[float] = None
    actual_duration_min: Optional[float] = None
    actual_concentration_percent: Optional[float] = None
    deviations: Optional[str] = None
    deviation_justification: Optional[str] = None
    in_process_results: Optional[Dict] = None

class CleaningProcessResponse(BaseModel):
    id: int
    process_code: str
    name: str
    cleaning_type: str
    is_validated: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CleaningCapabilityRequest(BaseModel):
    process_id: int
    historical_executions_count: int = 10

class CleaningCapabilityResponse(BaseModel):
    process_id: int
    process_name: str
    mean_effectiveness: float
    standard_deviation: float
    capability_index: float  # Cpk
    distance_from_maco: float
    risk_level: str  # LOW, MEDIUM, HIGH
    recommendation: str