from pydantic import BaseModel
from typing import Optional

class SwabResultCreate(BaseModel):
    session_id: int
    location_name: str
    absorbance_sample: float
    absorbance_std: float

class RinseResultCreate(BaseModel):
    session_id: int
    equipment_name: str
    actual_rinse_volume: float
    absorbance_sample: float
    absorbance_std: float

class ResultResponse(BaseModel):
    id: int
    session_id: int
    result_mg_ml: Optional[float] = None
    result_ppm: Optional[float] = None
    reported: Optional[str] = None
    
    class Config:
        from_attributes = True