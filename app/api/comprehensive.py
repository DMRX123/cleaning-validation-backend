"""
Unified CRUD API - Complete Create, Read, Update, Delete for all entities
NO AUTHENTICATION REQUIRED
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession
from ..models.standard_prep import StandardPrep
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.bracketing import BracketingGroup, BracketingProduct, BracketingWorstCase
from ..models.change_control import ChangeControl
from ..models.training import TrainingModule, TrainingRecord
from ..models.dosage_form import DosageForm, ProductDosageForm
from ..models.sampling_methods import SamplingLocation, SamplingResult
from ..models.formulation_equipment import FormulationEquipment
from ..models.cleaning_process import CleaningProcess, CleaningParameter, CleaningExecution
from ..models.microbiological import MicrobiologicalLimit, MicrobiologicalResult
from ..models.hold_time import DirtyHoldTime, CleanHoldTime
from ..models.user import User

router = APIRouter(prefix="/api/crud", tags=["Comprehensive CRUD"])

# ============================================
# HELPER FUNCTIONS
# ============================================

class DeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int = 0
    deleted_ids: List[int] = []

def success_response(data=None, message="Success", status_code=200):
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    }

def error_response(error: str, status_code: int = 400):
    return {
        "success": False,
        "error": error,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# PRODUCTS - Full CRUD
# ============================================

@router.delete("/products/{product_id}", response_model=DeleteResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return DeleteResponse(success=True, message="Product deleted successfully", deleted_count=1, deleted_ids=[product_id])

@router.delete("/products/all")
def delete_all_products(db: Session = Depends(get_db)):
    count = db.query(Product).delete()
    db.commit()
    return success_response(message=f"Deleted {count} products", data={"deleted_count": count})

@router.get("/products/all")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return success_response(data=products, message=f"Found {len(products)} products")

# ============================================
# EQUIPMENT - Full CRUD
# ============================================

@router.delete("/equipment/{equipment_id}", response_model=DeleteResponse)
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db.delete(equipment)
    db.commit()
    return DeleteResponse(success=True, message="Equipment deleted successfully", deleted_count=1, deleted_ids=[equipment_id])

@router.delete("/equipment/all")
def delete_all_equipment(db: Session = Depends(get_db)):
    count = db.query(Equipment).delete()
    db.commit()
    return success_response(message=f"Deleted {count} equipment", data={"deleted_count": count})

@router.get("/equipment/all")
def get_all_equipment(db: Session = Depends(get_db)):
    equipment = db.query(Equipment).all()
    return success_response(data=equipment, message=f"Found {len(equipment)} equipment")

# ============================================
# VALIDATION SESSIONS - Full CRUD
# ============================================

class SessionUpdate(BaseModel):
    status: Optional[str] = None
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

@router.put("/sessions/{session_id}")
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(session, key, value)
    
    db.commit()
    db.refresh(session)
    return success_response(data=session, message="Session updated")

@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.query(StandardPrep).filter(StandardPrep.session_id == session_id).delete()
    db.query(SwabResult).filter(SwabResult.session_id == session_id).delete()
    db.query(RinseResult).filter(RinseResult.session_id == session_id).delete()
    
    db.delete(session)
    db.commit()
    return DeleteResponse(success=True, message="Session and related data deleted", deleted_count=1, deleted_ids=[session_id])

@router.delete("/sessions/all")
def delete_all_sessions(db: Session = Depends(get_db)):
    db.query(StandardPrep).delete()
    db.query(SwabResult).delete()
    db.query(RinseResult).delete()
    count = db.query(ValidationSession).delete()
    db.commit()
    return success_response(message=f"Deleted {count} sessions", data={"deleted_count": count})

@router.get("/sessions/all")
def get_all_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ValidationSession).order_by(ValidationSession.created_at.desc()).all()
    return success_response(data=sessions, message=f"Found {len(sessions)} sessions")

# ============================================
# DOSAGE FORMS - Full CRUD
# ============================================

class DosageFormCreate(BaseModel):
    name: str
    code: str
    plant_type: str
    requires_sterility: bool = False
    requires_endotoxin_testing: bool = False
    default_microbial_limit_cfu: Optional[float] = None
    default_endotoxin_limit_eu_ml: Optional[float] = None

class DosageFormUpdate(BaseModel):
    name: Optional[str] = None
    requires_sterility: Optional[bool] = None
    requires_endotoxin_testing: Optional[bool] = None
    default_microbial_limit_cfu: Optional[float] = None
    default_endotoxin_limit_eu_ml: Optional[float] = None

@router.post("/dosage-forms")
def create_dosage_form(data: DosageFormCreate, db: Session = Depends(get_db)):
    existing = db.query(DosageForm).filter(DosageForm.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dosage form already exists")
    
    dosage_form = DosageForm(**data.dict())
    db.add(dosage_form)
    db.commit()
    db.refresh(dosage_form)
    return success_response(data=dosage_form, message="Dosage form created")

@router.put("/dosage-forms/{dosage_form_id}")
def update_dosage_form(dosage_form_id: int, data: DosageFormUpdate, db: Session = Depends(get_db)):
    dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
    if not dosage_form:
        raise HTTPException(status_code=404, detail="Dosage form not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(dosage_form, key, value)
    
    db.commit()
    db.refresh(dosage_form)
    return success_response(data=dosage_form, message="Dosage form updated")

@router.delete("/dosage-forms/{dosage_form_id}", response_model=DeleteResponse)
def delete_dosage_form(dosage_form_id: int, db: Session = Depends(get_db)):
    dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
    if not dosage_form:
        raise HTTPException(status_code=404, detail="Dosage form not found")
    
    db.delete(dosage_form)
    db.commit()
    return DeleteResponse(success=True, message="Dosage form deleted", deleted_count=1, deleted_ids=[dosage_form_id])

@router.delete("/dosage-forms/all")
def delete_all_dosage_forms(db: Session = Depends(get_db)):
    count = db.query(DosageForm).delete()
    db.commit()
    return success_response(message=f"Deleted {count} dosage forms", data={"deleted_count": count})

@router.get("/dosage-forms/all")
def get_all_dosage_forms(db: Session = Depends(get_db)):
    forms = db.query(DosageForm).all()
    return success_response(data=forms, message=f"Found {len(forms)} dosage forms")

# ============================================
# SAMPLING LOCATIONS - Full CRUD
# ============================================

class SamplingLocationCreate(BaseModel):
    equipment_id: int
    location_name: str
    location_description: Optional[str] = None
    surface_area_cm2: Optional[float] = None
    is_hard_to_clean: bool = False
    is_worst_case: bool = False
    priority: int = 3
    recommended_method: str = "swab"
    recovery_factor_percent: float = 100.0

class SamplingLocationUpdate(BaseModel):
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    is_hard_to_clean: Optional[bool] = None
    is_worst_case: Optional[bool] = None
    priority: Optional[int] = None
    recovery_factor_percent: Optional[float] = None

@router.post("/sampling-locations")
def create_sampling_location(data: SamplingLocationCreate, db: Session = Depends(get_db)):
    location = SamplingLocation(**data.dict())
    db.add(location)
    db.commit()
    db.refresh(location)
    return success_response(data=location, message="Sampling location created")

@router.put("/sampling-locations/{location_id}")
def update_sampling_location(location_id: int, data: SamplingLocationUpdate, db: Session = Depends(get_db)):
    location = db.query(SamplingLocation).filter(SamplingLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Sampling location not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(location, key, value)
    
    db.commit()
    db.refresh(location)
    return success_response(data=location, message="Sampling location updated")

@router.delete("/sampling-locations/{location_id}", response_model=DeleteResponse)
def delete_sampling_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(SamplingLocation).filter(SamplingLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Sampling location not found")
    
    db.delete(location)
    db.commit()
    return DeleteResponse(success=True, message="Sampling location deleted", deleted_count=1, deleted_ids=[location_id])

@router.delete("/sampling-locations/all")
def delete_all_sampling_locations(db: Session = Depends(get_db)):
    count = db.query(SamplingLocation).delete()
    db.commit()
    return success_response(message=f"Deleted {count} sampling locations", data={"deleted_count": count})

@router.get("/sampling-locations/all")
def get_all_sampling_locations(db: Session = Depends(get_db)):
    locations = db.query(SamplingLocation).all()
    return success_response(data=locations, message=f"Found {len(locations)} sampling locations")

# ============================================
# TRAINING MODULES - Full CRUD
# ============================================

class TrainingModuleCreate(BaseModel):
    module_code: str
    title: str
    description: Optional[str] = None
    category: str
    version: int = 1

class TrainingModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None

@router.post("/training-modules")
def create_training_module(data: TrainingModuleCreate, db: Session = Depends(get_db)):
    existing = db.query(TrainingModule).filter(TrainingModule.module_code == data.module_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Module code already exists")
    
    module = TrainingModule(**data.dict(), is_active=True)
    db.add(module)
    db.commit()
    db.refresh(module)
    return success_response(data=module, message="Training module created")

@router.put("/training-modules/{module_id}")
def update_training_module(module_id: int, data: TrainingModuleUpdate, db: Session = Depends(get_db)):
    module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(module, key, value)
    
    db.commit()
    db.refresh(module)
    return success_response(data=module, message="Training module updated")

@router.delete("/training-modules/{module_id}", response_model=DeleteResponse)
def delete_training_module(module_id: int, db: Session = Depends(get_db)):
    module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found")
    
    db.delete(module)
    db.commit()
    return DeleteResponse(success=True, message="Training module deleted", deleted_count=1, deleted_ids=[module_id])

@router.delete("/training-modules/all")
def delete_all_training_modules(db: Session = Depends(get_db)):
    count = db.query(TrainingModule).delete()
    db.commit()
    return success_response(message=f"Deleted {count} training modules", data={"deleted_count": count})

@router.get("/training-modules/all")
def get_all_training_modules(db: Session = Depends(get_db)):
    modules = db.query(TrainingModule).all()
    return success_response(data=modules, message=f"Found {len(modules)} training modules")

# ============================================
# TRAINING RECORDS - Full CRUD
# ============================================

class TrainingRecordCreate(BaseModel):
    user_id: int
    module_id: int
    training_date: datetime
    expiry_date: Optional[datetime] = None
    trainer: Optional[str] = None
    score: Optional[float] = None
    is_passed: bool = False

@router.post("/training-records")
def create_training_record(data: TrainingRecordCreate, db: Session = Depends(get_db)):
    record = TrainingRecord(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return success_response(data=record, message="Training record created")

@router.put("/training-records/{record_id}")
def update_training_record(record_id: int, data: dict, db: Session = Depends(get_db)):
    record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    
    for key, value in data.items():
        if hasattr(record, key):
            setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    return success_response(data=record, message="Training record updated")

@router.delete("/training-records/{record_id}", response_model=DeleteResponse)
def delete_training_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    
    db.delete(record)
    db.commit()
    return DeleteResponse(success=True, message="Training record deleted", deleted_count=1, deleted_ids=[record_id])

@router.delete("/training-records/all")
def delete_all_training_records(db: Session = Depends(get_db)):
    count = db.query(TrainingRecord).delete()
    db.commit()
    return success_response(message=f"Deleted {count} training records", data={"deleted_count": count})

@router.get("/training-records/all")
def get_all_training_records(db: Session = Depends(get_db)):
    records = db.query(TrainingRecord).all()
    return success_response(data=records, message=f"Found {len(records)} training records")

# ============================================
# CLEANING PROCESSES - Full CRUD
# ============================================

class CleaningProcessCreate(BaseModel):
    process_code: str
    name: str
    cleaning_type: str
    description: Optional[str] = None

class CleaningProcessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_validated: Optional[bool] = None
    is_active: Optional[bool] = None

@router.post("/cleaning-processes")
def create_cleaning_process(data: CleaningProcessCreate, db: Session = Depends(get_db)):
    existing = db.query(CleaningProcess).filter(CleaningProcess.process_code == data.process_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Process code already exists")
    
    process = CleaningProcess(**data.dict(), is_active=True, is_validated=False)
    db.add(process)
    db.commit()
    db.refresh(process)
    return success_response(data=process, message="Cleaning process created")

@router.put("/cleaning-processes/{process_id}")
def update_cleaning_process(process_id: int, data: CleaningProcessUpdate, db: Session = Depends(get_db)):
    process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Cleaning process not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(process, key, value)
    
    db.commit()
    db.refresh(process)
    return success_response(data=process, message="Cleaning process updated")

@router.delete("/cleaning-processes/{process_id}", response_model=DeleteResponse)
def delete_cleaning_process(process_id: int, db: Session = Depends(get_db)):
    process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Cleaning process not found")
    
    db.query(CleaningParameter).filter(CleaningParameter.process_id == process_id).delete()
    db.query(CleaningExecution).filter(CleaningExecution.process_id == process_id).delete()
    
    db.delete(process)
    db.commit()
    return DeleteResponse(success=True, message="Cleaning process deleted", deleted_count=1, deleted_ids=[process_id])

@router.delete("/cleaning-processes/all")
def delete_all_cleaning_processes(db: Session = Depends(get_db)):
    db.query(CleaningParameter).delete()
    db.query(CleaningExecution).delete()
    count = db.query(CleaningProcess).delete()
    db.commit()
    return success_response(message=f"Deleted {count} cleaning processes", data={"deleted_count": count})

@router.get("/cleaning-processes/all")
def get_all_cleaning_processes(db: Session = Depends(get_db)):
    processes = db.query(CleaningProcess).all()
    return success_response(data=processes, message=f"Found {len(processes)} cleaning processes")

# ============================================
# CHANGE CONTROL - Full CRUD
# ============================================

class ChangeControlCreate(BaseModel):
    change_number: str
    title: str
    type: str
    description: str
    reason: str
    proposed_by: str

class ChangeControlUpdate(BaseModel):
    status: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    revalidation_required: Optional[bool] = None
    closure_notes: Optional[str] = None

@router.post("/change-controls")
def create_change_control(data: ChangeControlCreate, db: Session = Depends(get_db)):
    existing = db.query(ChangeControl).filter(ChangeControl.change_number == data.change_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Change number already exists")
    
    cc = ChangeControl(**data.dict(), status="PROPOSED")
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return success_response(data=cc, message="Change control created")

@router.put("/change-controls/{cc_id}")
def update_change_control(cc_id: int, data: ChangeControlUpdate, db: Session = Depends(get_db)):
    cc = db.query(ChangeControl).filter(ChangeControl.id == cc_id).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(cc, key, value)
    
    db.commit()
    db.refresh(cc)
    return success_response(data=cc, message="Change control updated")

@router.delete("/change-controls/{cc_id}", response_model=DeleteResponse)
def delete_change_control(cc_id: int, db: Session = Depends(get_db)):
    cc = db.query(ChangeControl).filter(ChangeControl.id == cc_id).first()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found")
    
    db.delete(cc)
    db.commit()
    return DeleteResponse(success=True, message="Change control deleted", deleted_count=1, deleted_ids=[cc_id])

@router.delete("/change-controls/all")
def delete_all_change_controls(db: Session = Depends(get_db)):
    count = db.query(ChangeControl).delete()
    db.commit()
    return success_response(message=f"Deleted {count} change controls", data={"deleted_count": count})

@router.get("/change-controls/all")
def get_all_change_controls(db: Session = Depends(get_db)):
    controls = db.query(ChangeControl).order_by(ChangeControl.created_at.desc()).all()
    return success_response(data=controls, message=f"Found {len(controls)} change controls")

# ============================================
# BRACKETING GROUPS - Full CRUD
# ============================================

class BracketingGroupCreate(BaseModel):
    name: str
    equipment_type: str
    cleaning_procedure_class: str
    description: Optional[str] = None

class BracketingGroupUpdate(BaseModel):
    name: Optional[str] = None
    equipment_type: Optional[str] = None
    cleaning_procedure_class: Optional[str] = None
    description: Optional[str] = None

@router.post("/bracketing-groups")
def create_bracketing_group(data: BracketingGroupCreate, db: Session = Depends(get_db)):
    group = BracketingGroup(**data.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    return success_response(data=group, message="Bracketing group created")

@router.put("/bracketing-groups/{group_id}")
def update_bracketing_group(group_id: int, data: BracketingGroupUpdate, db: Session = Depends(get_db)):
    group = db.query(BracketingGroup).filter(BracketingGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Bracketing group not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return success_response(data=group, message="Bracketing group updated")

@router.delete("/bracketing-groups/{group_id}", response_model=DeleteResponse)
def delete_bracketing_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(BracketingGroup).filter(BracketingGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Bracketing group not found")
    
    db.delete(group)
    db.commit()
    return DeleteResponse(success=True, message="Bracketing group deleted", deleted_count=1, deleted_ids=[group_id])

@router.delete("/bracketing-groups/all")
def delete_all_bracketing_groups(db: Session = Depends(get_db)):
    db.query(BracketingProduct).delete()
    db.query(BracketingWorstCase).delete()
    count = db.query(BracketingGroup).delete()
    db.commit()
    return success_response(message=f"Deleted {count} bracketing groups", data={"deleted_count": count})

@router.get("/bracketing-groups/all")
def get_all_bracketing_groups(db: Session = Depends(get_db)):
    groups = db.query(BracketingGroup).all()
    return success_response(data=groups, message=f"Found {len(groups)} bracketing groups")

# ============================================
# MICROBIOLOGICAL LIMITS - Full CRUD
# ============================================

class MicrobiologicalLimitCreate(BaseModel):
    equipment_id: Optional[int] = None
    product_type: str
    total_germ_count_limit: float
    yeast_mold_limit: Optional[float] = None
    endotoxin_limit: Optional[float] = None
    sampling_method: str
    sampling_frequency: str

@router.post("/microbiological-limits")
def create_microbiological_limit(data: MicrobiologicalLimitCreate, db: Session = Depends(get_db)):
    limit = MicrobiologicalLimit(**data.dict())
    db.add(limit)
    db.commit()
    db.refresh(limit)
    return success_response(data=limit, message="Microbiological limit created")

@router.put("/microbiological-limits/{limit_id}")
def update_microbiological_limit(limit_id: int, data: dict, db: Session = Depends(get_db)):
    limit = db.query(MicrobiologicalLimit).filter(MicrobiologicalLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Microbiological limit not found")
    
    for key, value in data.items():
        if hasattr(limit, key):
            setattr(limit, key, value)
    
    db.commit()
    db.refresh(limit)
    return success_response(data=limit, message="Microbiological limit updated")

@router.delete("/microbiological-limits/{limit_id}", response_model=DeleteResponse)
def delete_microbiological_limit(limit_id: int, db: Session = Depends(get_db)):
    limit = db.query(MicrobiologicalLimit).filter(MicrobiologicalLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Microbiological limit not found")
    
    db.delete(limit)
    db.commit()
    return DeleteResponse(success=True, message="Microbiological limit deleted", deleted_count=1, deleted_ids=[limit_id])

@router.delete("/microbiological-limits/all")
def delete_all_microbiological_limits(db: Session = Depends(get_db)):
    count = db.query(MicrobiologicalLimit).delete()
    db.commit()
    return success_response(message=f"Deleted {count} microbiological limits", data={"deleted_count": count})

@router.get("/microbiological-limits/all")
def get_all_microbiological_limits(db: Session = Depends(get_db)):
    limits = db.query(MicrobiologicalLimit).all()
    return success_response(data=limits, message=f"Found {len(limits)} microbiological limits")

# ============================================
# HOLD TIMES - Full CRUD
# ============================================

@router.delete("/dirty-hold-times/{dht_id}", response_model=DeleteResponse)
def delete_dirty_hold_time(dht_id: int, db: Session = Depends(get_db)):
    record = db.query(DirtyHoldTime).filter(DirtyHoldTime.id == dht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dirty hold time record not found")
    
    db.delete(record)
    db.commit()
    return DeleteResponse(success=True, message="Dirty hold time deleted", deleted_count=1, deleted_ids=[dht_id])

@router.delete("/dirty-hold-times/all")
def delete_all_dirty_hold_times(db: Session = Depends(get_db)):
    count = db.query(DirtyHoldTime).delete()
    db.commit()
    return success_response(message=f"Deleted {count} dirty hold times", data={"deleted_count": count})

@router.delete("/clean-hold-times/{cht_id}", response_model=DeleteResponse)
def delete_clean_hold_time(cht_id: int, db: Session = Depends(get_db)):
    record = db.query(CleanHoldTime).filter(CleanHoldTime.id == cht_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Clean hold time record not found")
    
    db.delete(record)
    db.commit()
    return DeleteResponse(success=True, message="Clean hold time deleted", deleted_count=1, deleted_ids=[cht_id])

@router.delete("/clean-hold-times/all")
def delete_all_clean_hold_times(db: Session = Depends(get_db)):
    count = db.query(CleanHoldTime).delete()
    db.commit()
    return success_response(message=f"Deleted {count} clean hold times", data={"deleted_count": count})

# ============================================
# FORMULATION EQUIPMENT - Full CRUD
# ============================================

class FormulationEquipmentCreate(BaseModel):
    equipment_id: int
    category: str
    has_cip: bool = False
    has_sip: bool = False
    sampling_points_count: int = 0

@router.post("/formulation-equipment")
def create_formulation_equipment(data: FormulationEquipmentCreate, db: Session = Depends(get_db)):
    existing = db.query(FormulationEquipment).filter(FormulationEquipment.equipment_id == data.equipment_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Equipment already categorized")
    
    fe = FormulationEquipment(**data.dict())
    db.add(fe)
    db.commit()
    db.refresh(fe)
    return success_response(data=fe, message="Formulation equipment created")

@router.put("/formulation-equipment/{fe_id}")
def update_formulation_equipment(fe_id: int, data: dict, db: Session = Depends(get_db)):
    fe = db.query(FormulationEquipment).filter(FormulationEquipment.id == fe_id).first()
    if not fe:
        raise HTTPException(status_code=404, detail="Formulation equipment not found")
    
    for key, value in data.items():
        if hasattr(fe, key):
            setattr(fe, key, value)
    
    db.commit()
    db.refresh(fe)
    return success_response(data=fe, message="Formulation equipment updated")

@router.delete("/formulation-equipment/{fe_id}", response_model=DeleteResponse)
def delete_formulation_equipment(fe_id: int, db: Session = Depends(get_db)):
    fe = db.query(FormulationEquipment).filter(FormulationEquipment.id == fe_id).first()
    if not fe:
        raise HTTPException(status_code=404, detail="Formulation equipment not found")
    
    db.delete(fe)
    db.commit()
    return DeleteResponse(success=True, message="Formulation equipment deleted", deleted_count=1, deleted_ids=[fe_id])

@router.delete("/formulation-equipment/all")
def delete_all_formulation_equipment(db: Session = Depends(get_db)):
    count = db.query(FormulationEquipment).delete()
    db.commit()
    return success_response(message=f"Deleted {count} formulation equipment records", data={"deleted_count": count})

@router.get("/formulation-equipment/all")
def get_all_formulation_equipment(db: Session = Depends(get_db)):
    records = db.query(FormulationEquipment).all()
    return success_response(data=records, message=f"Found {len(records)} formulation equipment records")

# ============================================
# USERS - Full CRUD
# ============================================

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.is_admin is False and user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove last admin user")
    
    for key, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return success_response(data=user, message="User updated")

@router.delete("/users/{user_id}", response_model=DeleteResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete last admin user")
    
    db.delete(user)
    db.commit()
    return DeleteResponse(success=True, message="User deleted", deleted_count=1, deleted_ids=[user_id])

@router.delete("/users/all")
def delete_all_users(db: Session = Depends(get_db)):
    admin_count = db.query(User).filter(User.is_admin == True).count()
    if admin_count <= 1:
        return error_response("Cannot delete last admin user", status_code=400)
    
    count = db.query(User).delete()
    db.commit()
    return success_response(message=f"Deleted {count} users", data={"deleted_count": count})

@router.get("/users/all")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return success_response(data=users, message=f"Found {len(users)} users")