from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    product_code: Optional[str] = None
    min_batch_size: float
    max_batch_size: float
    ade_pde: float
    min_dose: float
    max_dose: float
    swab_recovery: float = 70
    lod: float = 0.1
    loq: float = 0.5
    swab_dilution: float = 20
    swab_surface_area: float = 0.01
    solubility: str
    hardest_to_clean: str
    plant: str
    toxicity_class: int = 3
    potency_class: int = 3
    cleanability_rating: int = 2

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    batch_size_display: Optional[str] = None
    ade_display: Optional[str] = None
    tdd_display: Optional[str] = None
    
    class Config:
        from_attributes = True