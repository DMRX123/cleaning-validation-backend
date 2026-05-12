from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    min_batch_size: float
    max_batch_size: float
    ade_pde: float
    min_dose: float
    max_dose: float
    swab_recovery: float
    lod: float
    loq: float
    swab_dilution: float
    swab_surface_area: float = 0.01
    solubility: str
    hardest_to_clean: str
    plant: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    min_batch_max_dose_ratio: Optional[float] = None
    
    class Config:
        from_attributes = True