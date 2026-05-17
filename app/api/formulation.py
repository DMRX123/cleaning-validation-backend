# app/api/formulation.py - COMPLETE ERROR-FREE VERSION

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from .auth import get_current_user
from ..models.user import User
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession  # IMPORTANT: Added missing import
from ..models.dosage_form import DosageForm, DosageFormEnum, PlantTypeEnum, ProductDosageForm
from ..models.sampling_methods import SamplingLocation, SamplingMethodEnum, SamplingResult
from ..models.formulation_equipment import FormulationEquipment, EquipmentCategoryEnum
from ..services.formulation_service import FormulationService

router = APIRouter(prefix="/formulation", tags=["Formulation Plants"])

# ==================== SCHEMAS ====================

class DosageFormCreate(BaseModel):
    name: str
    code: DosageFormEnum
    plant_type: PlantTypeEnum
    requires_sterility: bool = False
    requires_endotoxin_testing: bool = False
    requires_particle_count: bool = False
    default_microbial_limit_cfu: Optional[float] = None
    default_endotoxin_limit_eu_ml: Optional[float] = None
    description: Optional[str] = None

class DosageFormResponse(BaseModel):
    id: int
    name: str
    code: str
    plant_type: str
    requires_sterility: bool
    requires_endotoxin_testing: bool
    default_microbial_limit_cfu: Optional[float]
    default_endotoxin_limit_eu_ml: Optional[float]
    
    class Config:
        from_attributes = True

class ProductDosageFormCreate(BaseModel):
    product_id: int
    dosage_form_id: int
    batch_quantity: Optional[float] = None
    batch_unit: str = "kg"
    min_daily_dose: Optional[float] = None
    max_daily_dose: Optional[float] = None
    dose_unit: str = "mg"

class SamplingLocationCreate(BaseModel):
    equipment_id: int
    location_name: str
    location_description: Optional[str] = None
    surface_area_cm2: Optional[float] = None
    is_hard_to_clean: bool = False
    is_worst_case: bool = False
    priority: int = 3
    recommended_method: SamplingMethodEnum = SamplingMethodEnum.SWAB
    recovery_factor_percent: float = 100.0

class SamplingResultCreate(BaseModel):
    session_id: int
    location_id: Optional[int] = None
    sampling_method: SamplingMethodEnum
    sample_code: str
    sampling_date: datetime
    sampled_by: str
    swab_area_cm2: Optional[float] = None
    rinse_volume_ml: Optional[float] = None
    contact_plate_size_cm2: Optional[float] = None
    dilution_factor: float = 1.0
    absorbance_sample: Optional[float] = None
    absorbance_std: Optional[float] = None
    total_germ_count: Optional[float] = None
    yeast_mold_count: Optional[float] = None
    endotoxin_value: Optional[float] = None
    deviations: Optional[str] = None

class FormulationEquipmentCreate(BaseModel):
    equipment_id: int
    category: EquipmentCategoryEnum
    contact_parts: Optional[str] = None
    has_cip: bool = False
    has_sip: bool = False
    sampling_points_count: int = 0
    worst_case_sampling_points: Optional[str] = None

# ==================== DOSAGE FORM ENDPOINTS ====================

@router.get("/dosage-forms", response_model=List[DosageFormResponse])
def get_all_dosage_forms(
    plant_type: Optional[PlantTypeEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all dosage forms, optionally filtered by plant type"""
    query = db.query(DosageForm)
    if plant_type:
        query = query.filter(DosageForm.plant_type == plant_type)
    return query.all()


@router.get("/dosage-forms/{dosage_form_id}", response_model=DosageFormResponse)
def get_dosage_form(
    dosage_form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
    if not dosage_form:
        raise HTTPException(404, "Dosage form not found")
    return dosage_form


@router.post("/dosage-forms", response_model=DosageFormResponse)
def create_dosage_form(
    data: DosageFormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new dosage form (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    existing = db.query(DosageForm).filter(DosageForm.code == data.code).first()
    if existing:
        raise HTTPException(400, "Dosage form with this code already exists")
    
    dosage_form = DosageForm(**data.dict())
    db.add(dosage_form)
    db.commit()
    db.refresh(dosage_form)
    return dosage_form


@router.post("/product-dosage-form")
def link_product_to_dosage_form(
    data: ProductDosageFormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a product to a dosage form"""
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    
    dosage_form = db.query(DosageForm).filter(DosageForm.id == data.dosage_form_id).first()
    if not dosage_form:
        raise HTTPException(404, "Dosage form not found")
    
    existing = db.query(ProductDosageForm).filter(
        ProductDosageForm.product_id == data.product_id,
        ProductDosageForm.dosage_form_id == data.dosage_form_id
    ).first()
    if existing:
        raise HTTPException(400, "Product already linked to this dosage form")
    
    link = ProductDosageForm(**data.dict())
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return {
        "success": True,
        "message": f"Product {product.name} linked to {dosage_form.name}",
        "product_id": product.id,
        "dosage_form_id": dosage_form.id
    }


@router.get("/product/{product_id}/dosage-form")
def get_product_dosage_form(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dosage form information for a product"""
    link = db.query(ProductDosageForm).filter(
        ProductDosageForm.product_id == product_id
    ).first()
    
    if not link:
        return {"message": "Product not linked to any dosage form"}
    
    dosage_form = db.query(DosageForm).filter(DosageForm.id == link.dosage_form_id).first()
    requirements = FormulationService.get_dosage_form_requirements(dosage_form.code.value)
    
    return {
        "product_id": product_id,
        "dosage_form": dosage_form.to_dict() if dosage_form else None,
        "batch_quantity": link.batch_quantity,
        "batch_unit": link.batch_unit,
        "daily_dose_range": {
            "min": link.min_daily_dose,
            "max": link.max_daily_dose,
            "unit": link.dose_unit
        },
        "cleaning_requirements": requirements,
        "cleaning_level": "LEVEL_2" if dosage_form and dosage_form.requires_sterility else "LEVEL_1"
    }


# ==================== SAMPLING LOCATION ENDPOINTS ====================

@router.get("/equipment/{equipment_id}/sampling-locations")
def get_equipment_sampling_locations(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sampling locations for an equipment"""
    locations = db.query(SamplingLocation).filter(
        SamplingLocation.equipment_id == equipment_id,
        SamplingLocation.is_active == True
    ).order_by(SamplingLocation.priority).all()
    
    return {
        "equipment_id": equipment_id,
        "total_locations": len(locations),
        "locations": [
            {
                "id": loc.id,
                "name": loc.location_name,
                "description": loc.location_description,
                "surface_area_cm2": loc.surface_area_cm2,
                "is_hard_to_clean": loc.is_hard_to_clean,
                "is_worst_case": loc.is_worst_case,
                "priority": loc.priority,
                "recommended_method": loc.recommended_method.value,
                "recovery_factor_percent": loc.recovery_factor_percent
            }
            for loc in locations
        ]
    }


@router.post("/sampling-locations")
def create_sampling_location(
    data: SamplingLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a sampling location for an equipment"""
    equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
    if not equipment:
        raise HTTPException(404, "Equipment not found")
    
    location = SamplingLocation(**data.dict())
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return {
        "success": True,
        "location_id": location.id,
        "location_name": location.location_name,
        "message": f"Sampling location created for {equipment.name}"
    }


@router.post("/sampling-results")
def record_sampling_result(
    data: SamplingResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a sampling result"""
    session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
    if not session:
        raise HTTPException(404, "Validation session not found")
    
    result = SamplingResult(**data.dict())
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return {
        "success": True,
        "result_id": result.id,
        "sample_code": result.sample_code,
        "message": "Sampling result recorded successfully"
    }


# ==================== FORMULATION EQUIPMENT ENDPOINTS ====================

@router.post("/equipment/categorize")
def categorize_equipment(
    data: FormulationEquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Categorize equipment for formulation plants"""
    equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
    if not equipment:
        raise HTTPException(404, "Equipment not found")
    
    existing = db.query(FormulationEquipment).filter(
        FormulationEquipment.equipment_id == data.equipment_id
    ).first()
    
    if existing:
        # Update existing
        for key, value in data.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return {"success": True, "message": "Equipment categorization updated", "id": existing.id}
    else:
        # Create new
        formulation_eq = FormulationEquipment(**data.dict())
        db.add(formulation_eq)
        db.commit()
        db.refresh(formulation_eq)
        return {"success": True, "message": "Equipment categorized successfully", "id": formulation_eq.id}


@router.get("/equipment/category/{category}")
def get_equipment_by_category(
    category: EquipmentCategoryEnum,
    plant: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all equipment of a specific category"""
    query = db.query(FormulationEquipment).filter(
        FormulationEquipment.category == category
    )
    
    # Join with equipment to filter by plant
    results = []
    for fe in query.all():
        eq = db.query(Equipment).filter(Equipment.id == fe.equipment_id).first()
        if eq and (not plant or eq.plant == plant):
            results.append({
                "id": fe.id,
                "equipment_id": fe.equipment_id,
                "equipment_name": eq.name,
                "category": fe.category.value,
                "has_cip": fe.has_cip,
                "has_sip": fe.has_sip,
                "sampling_points_count": fe.sampling_points_count
            })
    
    return results


# ==================== PLANT TYPE VALIDATION ====================

@router.get("/plant-type/{plant_type}/validation-requirements")
def get_plant_type_validation_requirements(
    plant_type: PlantTypeEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cleaning validation requirements for a specific plant type"""
    requirements = FormulationService.get_plant_type_requirements(plant_type.value)
    
    # Get all dosage forms for this plant type
    dosage_forms = db.query(DosageForm).filter(
        DosageForm.plant_type == plant_type
    ).all()
    
    return {
        "plant_type": plant_type.value,
        "requirements": requirements,
        "dosage_forms_in_plant": [
            {"id": df.id, "name": df.name, "code": df.code.value}
            for df in dosage_forms
        ],
        "reference_guidelines": [
            "APIC Cleaning Validation Guide 2021",
            "PDA TR 29 - Cleaning Validation",
            "EMA/CHMP/CVMP/SWP/169430/2012",
            "USP <1072> Disinfectants and Antiseptics"
        ]
    }


@router.post("/sterile-limit-calculator")
def calculate_sterile_limit(
    maco_mg: float = Query(..., description="MACO in mg"),
    equipment_area_m2: float = Query(..., description="Equipment surface area in m²"),
    endotoxin_factor: float = Query(1.0, description="Endotoxin safety factor"),
    current_user: User = Depends(get_current_user)
):
    """Calculate stricter limits for sterile/injectable products"""
    result = FormulationService.calculate_sterile_limit(
        maco_mg, equipment_area_m2, endotoxin_factor
    )
    return result


# ==================== INITIALIZE DOSAGE FORMS (Run once) ====================

@router.post("/initialize-dosage-forms")
def initialize_dosage_forms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize all dosage forms (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    count = 0
    for code, req in FormulationService.DOSAGE_FORM_REQUIREMENTS.items():
        existing = db.query(DosageForm).filter(DosageForm.code == code).first()
        if not existing:
            dosage_form = DosageForm(
                name=code.replace("_", " ").title(),
                code=code,
                plant_type=req["plant_type"],
                requires_sterility=req.get("requires_sterility", False),
                requires_endotoxin_testing=req.get("requires_endotoxin_testing", False),
                default_microbial_limit_cfu=req.get("microbial_limit_cfu"),
                default_endotoxin_limit_eu_ml=req.get("endotoxin_limit_eu_ml"),
                recommended_sampling_method=req.get("sampling_method", "swab")
            )
            db.add(dosage_form)
            count += 1
    
    db.commit()
    return {"success": True, "message": f"Initialized {count} dosage forms"}