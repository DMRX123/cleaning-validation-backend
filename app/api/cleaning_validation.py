from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from .auth import get_current_user
from ..models.cleaning_level import CleaningLevelEnum
from ..models.product import Product
from ..models.equipment import Equipment
from ..services.cleaning_level_service import CleaningLevelService
from ..services.hold_time_service import HoldTimeService
from ..services.microbiological_service import MicrobiologicalService
from ..services.bracketing_service import BracketingService
from ..services.limit_rationale_service import LimitRationaleService
from ..services.maco import MACOService
from ..services.worst_case_service import WorstCaseService as NewWorstCaseService
from ..services.ade_service import ADEService
from ..schemas.ade import ADECalculationRequest, ADECalculationResponse

router = APIRouter(tags=["Cleaning Validation"])

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

class BracketingRequest(BaseModel):
    equipment_type: str
    product_ids: List[int]

class CleaningLevelRequest(BaseModel):
    previous_product_id: int
    next_product_id: int
    same_synthetic_chain: bool = False

@router.post("/determine-cleaning-level")
def determine_cleaning_level(
    request: CleaningLevelRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    previous = db.query(Product).filter(Product.id == request.previous_product_id).first()
    next_product = db.query(Product).filter(Product.id == request.next_product_id).first()
    if not previous or not next_product:
        raise HTTPException(status_code=404, detail="Product not found")
    level = CleaningLevelService.determine_level(previous, next_product, request.same_synthetic_chain)
    requirements = CleaningLevelService.get_level_requirements(level)
    justification = CleaningLevelService.get_level_justification(level, previous, next_product)
    return {
        "success": True,
        "cleaning_level": level.value,
        "requirements": requirements,
        "justification": justification
    }

@router.post("/validate-dirty-hold-time")
def validate_dirty_hold_time(
    request: HoldTimeRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
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
    return {"success": True, "data": result}

@router.post("/validate-clean-hold-time")
def validate_clean_hold_time(
    request: CleanHoldTimeRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
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
    return {"success": True, "data": result}

@router.post("/bracketing-matrix")
def create_bracketing_matrix(
    request: BracketingRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not request.product_ids:
        raise HTTPException(status_code=400, detail="product_ids cannot be empty")
    products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    matrix_result = BracketingService.create_bracketing_matrix(products)
    worst_case = BracketingService.select_worst_case(products)
    return {
        "success": True,
        "bracketing_matrix": matrix_result.get("bracketing_matrix", []),
        "worst_case_product": {"id": worst_case.id, "name": worst_case.name} if worst_case else None,
        "recommendation": f"Select {worst_case.name} as the worst case for validation" if worst_case else "No products to validate",
        "total_products_in_bracket": len(products)
    }

@router.get("/microbiological-limits/{product_type}")
def get_microbiological_limits(
    product_type: str,
    current_user = Depends(get_current_user)
):
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

@router.post("/calculate-ade", response_model=ADECalculationResponse)
def calculate_ade(
    request: ADECalculationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = ADEService.calculate_and_save(db, request)
    return result