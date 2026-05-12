from pydantic import BaseModel
from typing import Optional

class MACORequest(BaseModel):
    previous_product_id: int
    next_product_id: int

class MACOResponse(BaseModel):
    method_10ppm: float
    method_tdd: float
    method_ade_pde: float
    lowest_maco: float

class SwabLimitRequest(BaseModel):
    session_id: int
    total_surface_area: float

class SwabLimitResponse(BaseModel):
    mg_per_swab: float
    ppm: float

class RinseLimitRequest(BaseModel):
    session_id: int
    equipment_surface_area: float

class RinseLimitResponse(BaseModel):
    limit_mg: float
    limit_ppm: float
    volume_loq: float
    volume_10ppm: float

class WorstCaseRequest(BaseModel):
    plant: Optional[str] = None