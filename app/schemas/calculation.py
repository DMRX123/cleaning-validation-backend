from pydantic import BaseModel
from typing import Optional


# ============================================
# MACO CALCULATION SCHEMAS
# ============================================

class MACORequest(BaseModel):
    """
    Request schema for MACO calculation
    
    Supports 6 methods:
    - 10 ppm method
    - 100 ppm method
    - TDD method (with SF=1000)
    - ADE/PDE method
    - LD50 method (for detergents/chemicals)
    - TTC method (for limited toxicology data)
    """
    previous_product_id: int
    next_product_id: int
    ld50_mg_per_kg: Optional[float] = None  # For LD50 method (default: 500 mg/kg)
    ttc_category: Optional[str] = "standard"  # Options: carcinogenic, potent, standard, genotoxic


class MACOResponse(BaseModel):
    """Response schema for MACO calculation"""
    method_10ppm: float = 0
    method_100ppm: float = 0  # NEW
    method_tdd: float = 0
    method_ade_pde: float = 0
    method_ld50: float = 0  # NEW
    method_ttc: float = 0  # NEW
    lowest_maco: float = 0
    selected_method: str = "N/A"
    selected_method_justification: Optional[str] = None
    safety_factor_tdd: Optional[int] = 1000
    safety_factor_ld50: Optional[int] = 2000
    human_body_weight_kg: Optional[int] = 50
    reference: Optional[str] = "APIC Cleaning Validation Guide 2021 Section 4.2"
    
    class Config:
        from_attributes = True


# ============================================
# SWAB LIMIT CALCULATION SCHEMAS
# ============================================

class SwabLimitRequest(BaseModel):
    """Request schema for swab limit calculation"""
    session_id: int
    total_surface_area: float


class SwabLimitResponse(BaseModel):
    """Response schema for swab limit calculation"""
    mg_per_swab: float = 0
    ppm: float = 0
    maco_mg_used: Optional[float] = None
    surface_area_used: Optional[float] = None
    recovery_used: Optional[float] = None
    formula: Optional[str] = None
    reference: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# RINSE LIMIT CALCULATION SCHEMAS
# ============================================

class RinseLimitRequest(BaseModel):
    """Request schema for rinse limit calculation"""
    session_id: int
    equipment_id: int
    rinse_volume: float
    total_surface_area: float


class RinseLimitResponse(BaseModel):
    """Response schema for rinse limit calculation"""
    limit_mg: float = 0
    limit_ppm: float = 0
    volume_loq: float = 0
    volume_10ppm: float = 0
    volume_amv: Optional[float] = 0
    maco_mg: Optional[float] = 0
    equipment_surface_area: Optional[float] = None
    rinse_volume_used: Optional[float] = None
    loq_used: Optional[float] = None
    formula: Optional[str] = None
    reference: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# WORST CASE CALCULATION SCHEMAS
# ============================================

class WorstCaseRequest(BaseModel):
    """Request schema for worst case calculation"""
    plant: Optional[str] = None


class WorstCaseResponse(BaseModel):
    """Response schema for worst case calculation"""
    success: bool = True
    id: Optional[int] = None
    name: Optional[str] = None
    product_code: Optional[str] = None
    solubility: Optional[str] = None
    hardest_to_clean: Optional[str] = None
    ade_pde: Optional[float] = None
    min_dose: Optional[float] = None
    total_rating: Optional[int] = None
    plant: Optional[str] = None
    rating_details: Optional[dict] = None
    message: Optional[str] = None
    reference: Optional[str] = None
    
    class Config:
        from_attributes = True