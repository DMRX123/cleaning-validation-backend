from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class DirtyHoldTimeCreate(BaseModel):
    equipment_id: int
    product_name: str
    batch_number: str
    end_of_batch_time: datetime
    cleaning_start_time: datetime
    max_validated_dht_hours: float = 24.0
    created_by: Optional[str] = None
    
    @field_validator('cleaning_start_time')
    def validate_times(cls, v, info):
        values = info.data
        if 'end_of_batch_time' in values and v <= values['end_of_batch_time']:
            raise ValueError('cleaning_start_time must be after end_of_batch_time')
        return v


class DirtyHoldTimeUpdate(BaseModel):
    cleaning_start_time: Optional[datetime] = None
    investigation_required: Optional[bool] = None
    investigation_notes: Optional[str] = None
    corrective_action: Optional[str] = None


class DirtyHoldTimeResponse(BaseModel):
    id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    product_name: str
    batch_number: str
    end_of_batch_time: datetime
    cleaning_start_time: datetime
    actual_dht_hours: float
    max_validated_dht_hours: float
    is_within_limit: bool
    investigation_required: bool = False
    investigation_notes: Optional[str] = None
    corrective_action: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CleanHoldTimeCreate(BaseModel):
    equipment_id: int
    cleaning_completion_time: datetime
    next_use_time: datetime
    max_validated_cht_hours: float = 72.0
    storage_conditions: str = "Covered, dry, room temperature"
    created_by: Optional[str] = None
    
    @field_validator('next_use_time')
    def validate_times(cls, v, info):
        values = info.data
        if 'cleaning_completion_time' in values and v <= values['cleaning_completion_time']:
            raise ValueError('next_use_time must be after cleaning_completion_time')
        return v


class CleanHoldTimeUpdate(BaseModel):
    next_use_time: Optional[datetime] = None
    storage_conditions: Optional[str] = None
    microbiological_testing_done: Optional[bool] = None
    microbiological_result: Optional[str] = None


class CleanHoldTimeResponse(BaseModel):
    id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    cleaning_completion_time: datetime
    next_use_time: datetime
    actual_cht_hours: float
    max_validated_cht_hours: float
    is_within_limit: bool
    storage_conditions: str
    microbiological_testing_done: bool = False
    microbiological_result: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HoldTimeValidationCreate(BaseModel):
    equipment_id: int
    product_id: Optional[int] = None
    hold_type: str  # "DHT" or "CHT"
    validated_hours: float
    tested_hours: Optional[float] = None
    study_conditions: Optional[str] = None
    
    @field_validator('hold_type')
    def validate_hold_type(cls, v):
        if v not in ["DHT", "CHT"]:
            raise ValueError("hold_type must be 'DHT' or 'CHT'")
        return v


class HoldTimeValidationResponse(BaseModel):
    id: int
    equipment_id: int
    product_id: Optional[int]
    hold_type: str
    validated_hours: float
    tested_hours: Optional[float]
    number_of_successful_runs: int
    required_runs: int
    is_validated: bool
    validation_date: Optional[datetime]
    expiry_date: Optional[datetime]
    study_conditions: Optional[str]
    conclusions: Optional[str]
    
    class Config:
        from_attributes = True