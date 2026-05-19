from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models.hold_time import DirtyHoldTime, CleanHoldTime, HoldTimeValidation
from ..models.equipment import Equipment
from ..schemas.hold_time import (
    DirtyHoldTimeCreate, DirtyHoldTimeUpdate, DirtyHoldTimeResponse,
    CleanHoldTimeCreate, CleanHoldTimeUpdate, CleanHoldTimeResponse,
    HoldTimeValidationCreate, HoldTimeValidationResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hold-times", tags=["Hold Times (APIC Section 9.7)"])


# ============================================
# DIRTY HOLD TIME (DHT) - FULL CRUD
# ============================================

@router.post("/dirty", response_model=DirtyHoldTimeResponse)
def create_dirty_hold_time(data: DirtyHoldTimeCreate, db: Session = Depends(get_db)):
    equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    actual_hours = (data.cleaning_start_time - data.end_of_batch_time).total_seconds() / 3600
    is_within_limit = actual_hours <= data.max_validated_dht_hours
    
    dht = DirtyHoldTime(
        equipment_id=data.equipment_id,
        product_name=data.product_name,
        batch_number=data.batch_number,
        end_of_batch_time=data.end_of_batch_time,
        cleaning_start_time=data.cleaning_start_time,
        actual_dht_hours=round(actual_hours, 2),
        max_validated_dht_hours=data.max_validated_dht_hours,
        is_within_limit=is_within_limit,
        created_by=data.created_by
    )
    
    db.add(dht)
    db.commit()
    db.refresh(dht)
    return dht


@router.get("/dirty", response_model=List[DirtyHoldTimeResponse])
def get_all_dirty_hold_times(
    skip: int = 0,
    limit: int = 100,
    equipment_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DirtyHoldTime)
    if equipment_id:
        query = query.filter(DirtyHoldTime.equipment_id == equipment_id)
    return query.order_by(DirtyHoldTime.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/dirty/{dht_id}", response_model=DirtyHoldTimeResponse)
def get_dirty_hold_time(dht_id: int, db: Session = Depends(get_db)):
    record = db.query(DirtyHoldTime).filter(DirtyHoldTime.id == dht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dirty Hold Time record not found")
    if record.equipment:
        record.equipment_name = record.equipment.name
    return record


@router.put("/dirty/{dht_id}", response_model=DirtyHoldTimeResponse)
def update_dirty_hold_time(dht_id: int, data: DirtyHoldTimeUpdate, db: Session = Depends(get_db)):
    record = db.query(DirtyHoldTime).filter(DirtyHoldTime.id == dht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dirty Hold Time record not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/dirty/{dht_id}")
def delete_dirty_hold_time(dht_id: int, db: Session = Depends(get_db)):
    record = db.query(DirtyHoldTime).filter(DirtyHoldTime.id == dht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dirty Hold Time record not found")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Dirty Hold Time record deleted", "id": dht_id}


@router.delete("/dirty/all")
def delete_all_dirty_hold_times(db: Session = Depends(get_db)):
    count = db.query(DirtyHoldTime).delete()
    db.commit()
    return {"success": True, "message": f"Deleted {count} Dirty Hold Time records", "deleted_count": count}


# ============================================
# CLEAN HOLD TIME (CHT) - FULL CRUD
# ============================================

@router.post("/clean", response_model=CleanHoldTimeResponse)
def create_clean_hold_time(data: CleanHoldTimeCreate, db: Session = Depends(get_db)):
    equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    actual_hours = (data.next_use_time - data.cleaning_completion_time).total_seconds() / 3600
    is_within_limit = actual_hours <= data.max_validated_cht_hours
    
    # IMPORTANT: equipment_name MAT HATHAO - model me ye column nahi hai
    cht = CleanHoldTime(
        equipment_id=data.equipment_id,
        # equipment_name REMOVED - model me nahi hai
        cleaning_completion_time=data.cleaning_completion_time,
        next_use_time=data.next_use_time,
        actual_cht_hours=round(actual_hours, 2),
        max_validated_cht_hours=data.max_validated_cht_hours,
        is_within_limit=is_within_limit,
        storage_conditions=data.storage_conditions,
        created_by=data.created_by
    )
    
    db.add(cht)
    db.commit()
    db.refresh(cht)
    
    # Manually add equipment_name for response
    if cht.equipment:
        cht.equipment_name = cht.equipment.name
    
    return cht


@router.get("/clean", response_model=List[CleanHoldTimeResponse])
def get_all_clean_hold_times(
    skip: int = 0,
    limit: int = 100,
    equipment_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CleanHoldTime)
    if equipment_id:
        query = query.filter(CleanHoldTime.equipment_id == equipment_id)
    return query.order_by(CleanHoldTime.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/clean/{cht_id}", response_model=CleanHoldTimeResponse)
def get_clean_hold_time(cht_id: int, db: Session = Depends(get_db)):
    record = db.query(CleanHoldTime).filter(CleanHoldTime.id == cht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Clean Hold Time record not found")
    return record


@router.put("/clean/{cht_id}", response_model=CleanHoldTimeResponse)
def update_clean_hold_time(cht_id: int, data: CleanHoldTimeUpdate, db: Session = Depends(get_db)):
    record = db.query(CleanHoldTime).filter(CleanHoldTime.id == cht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Clean Hold Time record not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/clean/{cht_id}")
def delete_clean_hold_time(cht_id: int, db: Session = Depends(get_db)):
    record = db.query(CleanHoldTime).filter(CleanHoldTime.id == cht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Clean Hold Time record not found")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Clean Hold Time record deleted", "id": cht_id}


@router.delete("/clean/all")
def delete_all_clean_hold_times(db: Session = Depends(get_db)):
    count = db.query(CleanHoldTime).delete()
    db.commit()
    return {"success": True, "message": f"Deleted {count} Clean Hold Time records", "deleted_count": count}


# ============================================
# HOLD TIME VALIDATION - FULL CRUD
# ============================================

@router.post("/validation", response_model=HoldTimeValidationResponse)
def create_hold_time_validation(data: HoldTimeValidationCreate, db: Session = Depends(get_db)):
    equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    validation = HoldTimeValidation(
        equipment_id=data.equipment_id,
        product_id=data.product_id,
        hold_type=data.hold_type,
        validated_hours=data.validated_hours,
        tested_hours=data.tested_hours,
        study_conditions=data.study_conditions,
        number_of_successful_runs=0,
        required_runs=3,
        is_validated=False
    )
    
    db.add(validation)
    db.commit()
    db.refresh(validation)
    return validation


@router.get("/validation", response_model=List[HoldTimeValidationResponse])
def get_all_hold_time_validations(
    skip: int = 0,
    limit: int = 100,
    equipment_id: Optional[int] = None,
    hold_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(HoldTimeValidation)
    if equipment_id:
        query = query.filter(HoldTimeValidation.equipment_id == equipment_id)
    if hold_type:
        query = query.filter(HoldTimeValidation.hold_type == hold_type)
    return query.order_by(HoldTimeValidation.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/validation/{validation_id}", response_model=HoldTimeValidationResponse)
def get_hold_time_validation(validation_id: int, db: Session = Depends(get_db)):
    record = db.query(HoldTimeValidation).filter(HoldTimeValidation.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Hold Time Validation record not found")
    return record


@router.put("/validation/{validation_id}/approve")
def approve_hold_time_validation(
    validation_id: int,
    successful_runs: int = 3,
    conclusions: Optional[str] = None,
    db: Session = Depends(get_db)
):
    record = db.query(HoldTimeValidation).filter(HoldTimeValidation.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Hold Time Validation record not found")
    
    record.number_of_successful_runs = successful_runs
    record.is_validated = successful_runs >= record.required_runs
    record.validation_date = datetime.now()
    record.conclusions = conclusions
    
    if record.is_validated:
        record.expiry_date = datetime.now() + timedelta(days=730)
    
    db.commit()
    db.refresh(record)
    
    return {
        "success": True,
        "message": f"Hold Time Validation {'approved' if record.is_validated else 'pending'}",
        "is_validated": record.is_validated,
        "successful_runs": record.number_of_successful_runs,
        "required_runs": record.required_runs
    }


@router.delete("/validation/{validation_id}")
def delete_hold_time_validation(validation_id: int, db: Session = Depends(get_db)):
    record = db.query(HoldTimeValidation).filter(HoldTimeValidation.id == validation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Hold Time Validation record not found")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Hold Time Validation record deleted", "id": validation_id}


@router.delete("/validation/all")
def delete_all_hold_time_validations(db: Session = Depends(get_db)):
    count = db.query(HoldTimeValidation).delete()
    db.commit()
    return {"success": True, "message": f"Deleted {count} Hold Time Validation records", "deleted_count": count}


# ============================================
# UTILITY ENDPOINTS
# ============================================

@router.get("/dht/check/{equipment_id}")
def check_dirty_hold_time_status(
    equipment_id: int,
    end_of_batch_time: datetime,
    cleaning_start_time: datetime,
    max_dht_hours: float = 24.0,
    db: Session = Depends(get_db)
):
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    actual_hours = (cleaning_start_time - end_of_batch_time).total_seconds() / 3600
    is_within_limit = actual_hours <= max_dht_hours
    
    result = {
        "equipment_id": equipment_id,
        "equipment_name": equipment.name,
        "end_of_batch_time": end_of_batch_time.isoformat(),
        "cleaning_start_time": cleaning_start_time.isoformat(),
        "actual_dht_hours": round(actual_hours, 2),
        "max_validated_dht_hours": max_dht_hours,
        "is_within_limit": is_within_limit,
        "status": "PASS" if is_within_limit else "FAIL"
    }
    
    if not is_within_limit:
        result["action_required"] = "RECLEAN REQUIRED: Equipment must be recleaned before use."
        result["investigation_steps"] = [
            "Review production schedule for delays",
            "Check if cleaning start time was documented correctly",
            "Assess if residue degradation occurred during extended DHT",
            "Perform additional sampling if degradation is suspected",
            "Document findings in deviation report"
        ]
    
    return result


@router.get("/cht/check/{equipment_id}")
def check_clean_hold_time_status(
    equipment_id: int,
    cleaning_completion_time: datetime,
    next_use_time: datetime,
    max_cht_hours: float = 72.0,
    db: Session = Depends(get_db)
):
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    actual_hours = (next_use_time - cleaning_completion_time).total_seconds() / 3600
    is_within_limit = actual_hours <= max_cht_hours
    
    result = {
        "equipment_id": equipment_id,
        "equipment_name": equipment.name,
        "cleaning_completion_time": cleaning_completion_time.isoformat(),
        "next_use_time": next_use_time.isoformat(),
        "actual_cht_hours": round(actual_hours, 2),
        "max_validated_cht_hours": max_cht_hours,
        "is_within_limit": is_within_limit,
        "status": "PASS" if is_within_limit else "FAIL"
    }
    
    if not is_within_limit:
        result["action_required"] = "RECLEAN REQUIRED: Equipment has exceeded validated clean hold time."
        result["microbiological_risk"] = "Extended CHT may lead to microbial growth. Recleaning and microbiological testing required."
    
    return result


@router.get("/default-limits")
def get_default_hold_time_limits():
    limits = {
        "reactor": {"dht": 24, "cht": 72, "dht_max": 48, "cht_max": 168},
        "dryer": {"dht": 12, "cht": 168, "dht_max": 24, "cht_max": 336},
        "mill": {"dht": 8, "cht": 168, "dht_max": 16, "cht_max": 336},
        "blender": {"dht": 8, "cht": 168, "dht_max": 16, "cht_max": 336},
        "filler": {"dht": 4, "cht": 24, "dht_max": 8, "cht_max": 72},
        "centrifuge": {"dht": 12, "cht": 72, "dht_max": 24, "cht_max": 168},
        "filter": {"dht": 8, "cht": 48, "dht_max": 16, "cht_max": 120},
        "tank": {"dht": 48, "cht": 168, "dht_max": 96, "cht_max": 336},
        "coater": {"dht": 8, "cht": 72, "dht_max": 16, "cht_max": 168},
        "granulator": {"dht": 12, "cht": 72, "dht_max": 24, "cht_max": 168}
    }
    
    return {
        "success": True,
        "data": limits,
        "reference": "APIC Cleaning Validation Guide Section 9.7",
        "note": "DHT = Dirty Hold Time, CHT = Clean Hold Time"
    }