from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProtocolBase(BaseModel):
    title: str
    protocol_number: str
    version: int = 1
    status: str = "DRAFT"
    
    # Section 9.1 - Background
    background: Optional[str] = None
    
    # Section 9.2 - Purpose
    purpose: Optional[str] = None
    
    # Section 9.3 - Scope
    scope: Optional[str] = None
    
    # Equipment and products
    equipment_id: int
    cleaning_procedure_id: str
    previous_product_id: int
    next_product_id: int
    
    # Section 9.7 - Acceptance Criteria
    visual_acceptance: str = "No visible residue"
    chemical_acceptance_ppm: Optional[float] = None
    microbiological_acceptance: Optional[float] = None
    
    # Sampling Plan (Section 9.5)
    sampling_locations: Optional[List[dict]] = None
    rinse_volume: Optional[float] = None
    
    # Hold Times (Section 9.7)
    dirty_hold_time_hours: Optional[float] = None
    clean_hold_time_hours: Optional[float] = None
    
    # Approvals
    prepared_by: str
    prepared_date: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None

class ProtocolCreate(ProtocolBase):
    pass

class ProtocolUpdate(ProtocolBase):
    pass

class ProtocolResponse(ProtocolBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProtocolExecutionBase(BaseModel):
    protocol_id: int
    execution_number: int
    visual_result: str
    chemical_result_ppm: float
    microbiological_result: Optional[float] = None
    deviations: Optional[str] = None
    investigator: str

class ProtocolExecutionCreate(ProtocolExecutionBase):
    pass

class ProtocolExecutionResponse(ProtocolExecutionBase):
    id: int
    execution_date: datetime
    overall_result: str
    
    class Config:
        from_attributes = True