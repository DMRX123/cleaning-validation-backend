from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ValidationSession
from ..models.standard_prep import StandardPrep
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.equipment import Equipment
from ..services.standard import StandardService
from ..services.swab import SwabService
from ..services.rinse import RinseService
from ..services.acceptability import AcceptabilityService
from ..services.extra_area import ExtraAreaService
from ..services.equipment_filter import EquipmentFilterService
from .auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

router = APIRouter()

class SessionCreate(BaseModel):
    previous_product_id: int
    next_product_id: int
    extra_area_percentage: float = 0

class SessionUpdate(BaseModel):
    step: Optional[int] = None
    data: Optional[dict] = None
    previous_product_id: Optional[int] = None
    next_product_id: Optional[int] = None
    extra_area_percentage: Optional[float] = None
    total_surface_area: Optional[float] = None
    maco_10ppm: Optional[float] = None
    maco_tdd: Optional[float] = None
    maco_ade_pde: Optional[float] = None
    lowest_maco: Optional[float] = None
    swab_limit_mg: Optional[float] = None
    swab_limit_ppm: Optional[float] = None
    rinse_limit_mg: Optional[float] = None
    rinse_limit_ppm: Optional[float] = None
    status: Optional[str] = None

class StandardPrepCreate(BaseModel):
    session_id: int
    wt_of_std: float
    first_dilution: float
    second_dilution: float
    third_dilution: float
    fourth_dilution: float
    fifth_dilution: float
    potency: float

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

@router.post("/session")
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    session_code = f"VAL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    
    new_session = ValidationSession(
        session_code=session_code,
        previous_product_id=data.previous_product_id,
        next_product_id=data.next_product_id,
        extra_area_percentage=data.extra_area_percentage,
        status="DRAFT"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.put("/session/{session_id}")
def update_session(
    session_id: int, 
    data: SessionUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update validation session - FIXED: Added this endpoint"""
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = data.dict(exclude_unset=True)
    
    # Remove 'data' field if present as it's for nested storage
    if 'data' in update_data:
        update_data.pop('data')
    
    for key, value in update_data.items():
        if hasattr(session, key) and value is not None:
            setattr(session, key, value)
    
    # If step is provided and status is DRAFT, update to IN_PROGRESS
    if data.step and data.step > 1 and session.status == "DRAFT":
        session.status = "IN_PROGRESS"
    
    db.commit()
    db.refresh(session)
    return session


@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/history")
def get_validation_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get all validation sessions for history/chart"""
    sessions = db.query(ValidationSession).order_by(ValidationSession.created_at.desc()).all()
    return sessions


@router.post("/standard-prep")
def create_standard_prep(data: StandardPrepCreate, db: Session = Depends(get_db)):
    new_prep = StandardPrep(**data.dict())
    factor = StandardService.calculate_dilution_factor(
        data.wt_of_std, data.first_dilution, data.second_dilution,
        data.third_dilution, data.fourth_dilution, data.fifth_dilution,
        data.potency
    )
    new_prep.dilution_factor = factor
    db.add(new_prep)
    db.commit()
    db.refresh(new_prep)
    return new_prep


@router.post("/swab-result")
def create_swab_result(data: SwabResultCreate, db: Session = Depends(get_db)):
    """
    Create swab result with proper numeric handling
    result_ppm is ALWAYS a number (0 if below LOQ) - safe for frontend toFixed()
    """
    session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
    prep = db.query(StandardPrep).filter(StandardPrep.session_id == data.session_id).first()
    
    if not session or not prep:
        raise HTTPException(status_code=404, detail="Session or Standard Prep not found")
    
    recovery = session.next_product.swab_recovery if session.next_product else 100
    loq = session.next_product.loq if session.next_product else 0
    swab_dilution = session.next_product.swab_dilution if session.next_product else 20
    
    result = SwabService.calculate_result(
        data.absorbance_sample, data.absorbance_std,
        prep.dilution_factor, swab_dilution,
        recovery, loq
    )
    
    new_result = SwabResult(
        session_id=data.session_id,
        location_name=data.location_name,
        absorbance_sample=data.absorbance_sample,
        absorbance_std=data.absorbance_std,
        result_mg_ml=result["mg_ml"],
        result_ppm=result["ppm_numeric"],
        reported=result["reported"]
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    # Return enhanced response with both numeric and display values
    return {
        "id": new_result.id,
        "session_id": new_result.session_id,
        "location_name": new_result.location_name,
        "absorbance_sample": new_result.absorbance_sample,
        "absorbance_std": new_result.absorbance_std,
        "result_mg_ml": new_result.result_mg_ml,
        "result_ppm": new_result.result_ppm,
        "result_ppm_display": result["ppm_display"],
        "reported": new_result.reported,
        "below_loq": result["below_loq"]
    }


@router.post("/rinse-result")
def create_rinse_result(data: RinseResultCreate, db: Session = Depends(get_db)):
    """
    Create rinse result with proper numeric handling
    result_ppm is ALWAYS a number (0 if below LOQ) - safe for frontend toFixed()
    """
    session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
    prep = db.query(StandardPrep).filter(StandardPrep.session_id == data.session_id).first()
    
    if not session or not prep:
        raise HTTPException(status_code=404, detail="Session or Standard Prep not found")
    
    recovery = session.next_product.swab_recovery if session.next_product else 100
    loq = session.next_product.loq if session.next_product else 0
    
    result = SwabService.calculate_result(
        data.absorbance_sample, data.absorbance_std,
        prep.dilution_factor, 1,  # Rinse has different dilution
        recovery, loq
    )
    
    new_result = RinseResult(
        session_id=data.session_id,
        equipment_name=data.equipment_name,
        actual_rinse_volume=data.actual_rinse_volume,
        absorbance_sample=data.absorbance_sample,
        absorbance_std=data.absorbance_std,
        result_mg_ml=result["mg_ml"],
        result_ppm=result["ppm_numeric"],
        reported=result["reported"]
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    return {
        "id": new_result.id,
        "session_id": new_result.session_id,
        "equipment_name": new_result.equipment_name,
        "actual_rinse_volume": new_result.actual_rinse_volume,
        "result_mg_ml": new_result.result_mg_ml,
        "result_ppm": new_result.result_ppm,
        "result_ppm_display": result["ppm_display"],
        "reported": new_result.reported,
        "below_loq": result["below_loq"]
    }