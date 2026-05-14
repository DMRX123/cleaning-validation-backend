from pydantic import BaseModel
from typing import Optional

class ADECalculationRequest(BaseModel):
    product_id: int
    noael_mg_per_kg: Optional[float] = None
    loael_mg_per_kg: Optional[float] = None
    ld50_mg_per_kg: Optional[float] = None
    body_weight_kg: float = 50.0
    uf1: float = 1.0
    uf2: float = 10.0
    uf3: float = 10.0
    uf4: float = 1.0
    uf5: float = 1.0
    modifying_factor: float = 1.0
    pk_adjustment: float = 1.0
    route: str = "oral"

class ADECalculationResponse(BaseModel):
    id: int
    product_id: int
    calculated_ade_mg_per_day: float
    calculation_method: str
    calculation_justification: str
    route: str
    is_approved: bool
    
    class Config:
        from_attributes = True