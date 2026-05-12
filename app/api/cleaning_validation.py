from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from ..api.dependencies import get_current_user
from ..models.cleaning_level import CleaningLevelEnum
from ..models.product import Product
from ..models.equipment import Equipment
from ..services.cleaning_level_service import CleaningLevelService
from ..services.hold_time_service import HoldTimeService
from ..services.microbiological_service import MicrobiologicalService
from ..services.bracketing_service import BracketingService
from ..services.limit_rationale_service import LimitRationaleService
from ..services.maco import MACOService

router = APIRouter(prefix="/cleaning-validation", tags=["Cleaning Validation"])

# Request Models
class HoldTimeRequest(BaseModel):
    equipment_id: int
    end_of_batch_time: datetime
    cleaning_start_time: datetime
    max_dht_hours: float = 24

class CleanHoldTimeRequest(BaseModel):
    equipment_id: int
    cleaning_completion_time: datetime
    next_use_time: datetime
    max_cht_hours: float = 72
    storage_conditions: str = "Covered, dry, room temperature"

class MACORequestAdvanced(BaseModel):
    previous_product_id: int
    next_product_id: int
    purging_factor: float = 1.0
    safety_factor: float = 1.0
    production_type: str = "api_chemical"

class BracketingRequest(BaseModel):
    equipment_type: str
    product_ids: List[int]

# ============================================
# CLEANING LEVEL ENDPOINTS
# ============================================

@router.post("/determine-cleaning-level")
def determine_cleaning_level(
    previous_product_id: int, 
    next_product_id: int,
    same_synthetic_chain: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Section 5.0 - Determine cleaning level based on risk"""
    previous = db.query(Product).filter(Product.id == previous_product_id).first()
    next_product = db.query(Product).filter(Product.id == next_product_id).first()
    
    if not previous or not next_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    level = CleaningLevelService.determine_level(previous, next_product, same_synthetic_chain)
    requirements = CleaningLevelService.get_level_requirements(level)
    justification = CleaningLevelService.get_level_justification(level, previous, next_product)
    
    return {
        "success": True,
        "cleaning_level": level.value,
        "requirements": requirements,
        "justification": justification
    }

# ============================================
# HOLD TIME ENDPOINTS
# ============================================

@router.post("/validate-dirty-hold-time")
def validate_dirty_hold_time(
    request: HoldTimeRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Section 9.7 - Validate Dirty Hold Time"""
    equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    result = HoldTimeService.validate_dirty_hold_time(
        request.equipment_id,
        f"Product on {equipment.name}",
        request.end_of_batch_time,
        request.cleaning_start_time,
        request.max_dht_hours
    )
    
    return {
        "success": True,
        "data": result
    }

@router.post("/validate-clean-hold-time")
def validate_clean_hold_time(
    request: CleanHoldTimeRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Section 9.7 - Validate Clean Hold Time"""
    equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    result = HoldTimeService.validate_clean_hold_time(
        request.equipment_id,
        request.cleaning_completion_time,
        request.next_use_time,
        request.max_cht_hours,
        request.storage_conditions
    )
    
    return {
        "success": True,
        "data": result
    }

@router.post("/extend-hold-time")
def extend_hold_time(
    equipment_id: int,
    hold_type: str,
    current_max: float,
    requested_max: float,
    justification: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Extend validated hold time with justification"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    if hold_type not in ["DHT", "CHT"]:
        raise HTTPException(status_code=400, detail="hold_type must be DHT or CHT")
    
    result = HoldTimeService.extend_hold_time(equipment_id, hold_type, current_max, requested_max, justification)
    
    return {
        "success": True,
        "data": result
    }

# ============================================
# MACO CALCULATION ENDPOINTS
# ============================================

@router.post("/maco-advanced")
def calculate_maco_advanced(
    request: MACORequestAdvanced, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Section 4.2.1 - Advanced MACO with PF, SF, and production type factor"""
    previous = db.query(Product).filter(Product.id == request.previous_product_id).first()
    next_product = db.query(Product).filter(Product.id == request.next_product_id).first()
    
    if not previous or not next_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Apply production type factor (Section 4.2.6)
    factor = LimitRationaleService.get_factor(request.production_type)
    
    result = MACOService.calculate_all(
        previous, next_product,
        purging_factor=request.purging_factor * factor,
        safety_factor=request.safety_factor
    )
    
    # Add rationale
    result["rationale"] = LimitRationaleService.get_rationale(request.production_type, [])
    result["production_type_factor_applied"] = factor
    
    return {
        "success": True,
        "data": result
    }

# ============================================
# BRACKETING MATRIX ENDPOINT (FIXED - Replace only this)
# ============================================

@router.post("/bracketing-matrix")
def create_bracketing_matrix(
    request: BracketingRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Section 7.5 - Create worst case rating matrix"""
    if not request.product_ids:
        raise HTTPException(status_code=400, detail="product_ids cannot be empty")
    
    products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
    
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    
    # Get bracketing matrix from service
    matrix_result = BracketingService.create_bracketing_matrix(products)
    
    # Get worst case product
    worst_case = BracketingService.select_worst_case(products)
    
    return {
        "success": True,
        "bracketing_matrix": matrix_result.get("bracketing_matrix", []),
        "worst_case_product": {
            "id": worst_case.id,
            "name": worst_case.name
        } if worst_case else None,
        "recommendation": f"Select {worst_case.name} as the worst case for validation" if worst_case else "No products to validate",
        "total_products_in_bracket": len(products)
    }

# ============================================
# MICROBIOLOGICAL ENDPOINTS
# ============================================

@router.get("/microbiological-limits/{product_type}")
def get_microbiological_limits(
    product_type: str,
    current_user = Depends(get_current_user)
):
    """Section 8.1 - Get microbiological limits by product type"""
    valid_types = ["oral", "parenteral", "topical", "biotech", "inhalation"]
    if product_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid product_type. Must be one of: {valid_types}")
    
    limits = MicrobiologicalService.get_default_limits(product_type)
    sampling_frequency = MicrobiologicalService.get_sampling_frequency("LEVEL_2", product_type)
    
    return {
        "success": True,
        "product_type": product_type,
        "limits": limits,
        "sampling_frequency": sampling_frequency,
        "reference": "APIC Cleaning Validation Guide Section 8.1 - EMA 158/01"
    }

# ============================================
# LIMIT RATIONALE ENDPOINTS
# ============================================

@router.get("/limit-rationale/{production_type}")
def get_limit_rationale(
    production_type: str, 
    has_purification: bool = False,
    current_user = Depends(get_current_user)
):
    """Section 4.2.6 - Get scientific rationale for different limits"""
    valid_types = ["pharmaceutical", "api_chemical", "api_physical", "intermediate_early", "intermediate_late", "dedicated"]
    if production_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid production_type. Must be one of: {valid_types}")
    
    process_steps = ["crystallization"] if has_purification else []
    rationale = LimitRationaleService.get_rationale(production_type, process_steps)
    
    return {
        "success": True,
        "data": rationale
    }

# ============================================
# HOLD TIME DEFAULTS ENDPOINTS
# ============================================

@router.get("/hold-time-defaults/{equipment_type}")
def get_hold_time_defaults(
    equipment_type: str,
    current_user = Depends(get_current_user)
):
    """Get default hold time limits for equipment type"""
    defaults = HoldTimeService.get_default_limits(equipment_type)
    
    return {
        "success": True,
        "equipment_type": equipment_type,
        "default_dirty_hold_time_hours": defaults.get("dht", 24),
        "default_clean_hold_time_hours": defaults.get("cht", 72),
        "max_dirty_hold_time_hours": defaults.get("dht_max", defaults.get("dht", 24) * 2),
        "max_clean_hold_time_hours": defaults.get("cht_max", defaults.get("cht", 72) * 2),
        "reference": "APIC Cleaning Validation Guide Section 9.7"
    }