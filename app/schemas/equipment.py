from pydantic import BaseModel
from typing import Optional

class EquipmentBase(BaseModel):
    name: str
    equipment_id: str
    capacity: Optional[float] = None
    surface_area: float
    used_for: str
    cleaning_procedure: str
    plant: str

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(EquipmentBase):
    pass

class EquipmentResponse(EquipmentBase):
    id: int
    
    class Config:
        from_attributes = True