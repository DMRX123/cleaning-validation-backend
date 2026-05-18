# app/api/formulation.py - COMPLETE FIXED VERSION

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..database import get_db
from .auth import get_current_user
from ..models.user import User
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession
from ..models.dosage_form import DosageForm, DosageFormEnum, PlantTypeEnum, ProductDosageForm
from ..models.sampling_methods import SamplingLocation, SamplingMethodEnum, SamplingResult
from ..models.formulation_equipment import FormulationEquipment, EquipmentCategoryEnum
from ..services.formulation_service import FormulationService

logger = logging.getLogger(__name__)

# FIXED: Removed prefix from here - will be added in main.py
router = APIRouter(tags=["Formulation Plants"])

# ==================== SCHEMAS ====================

class DosageFormCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: DosageFormEnum
    plant_type: PlantTypeEnum
    requires_sterility: bool = False
    requires_endotoxin_testing: bool = False
    requires_particle_count: bool = False
    default_microbial_limit_cfu: Optional[float] = Field(None, ge=0)
    default_endotoxin_limit_eu_ml: Optional[float] = Field(None, ge=0)
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
    product_id: int = Field(..., gt=0)
    dosage_form_id: int = Field(..., gt=0)
    batch_quantity: Optional[float] = Field(None, gt=0)
    batch_unit: str = "kg"
    min_daily_dose: Optional[float] = Field(None, ge=0)
    max_daily_dose: Optional[float] = Field(None, ge=0)
    dose_unit: str = "mg"

class SamplingLocationCreate(BaseModel):
    equipment_id: int = Field(..., gt=0)
    location_name: str = Field(..., min_length=1, max_length=200)
    location_description: Optional[str] = None
    surface_area_cm2: Optional[float] = Field(None, ge=0)
    is_hard_to_clean: bool = False
    is_worst_case: bool = False
    priority: int = Field(3, ge=1, le=5)
    recommended_method: SamplingMethodEnum = SamplingMethodEnum.SWAB
    recovery_factor_percent: float = Field(100.0, ge=0, le=200)

class SamplingResultCreate(BaseModel):
    session_id: int = Field(..., gt=0)
    location_id: Optional[int] = Field(None, gt=0)
    sampling_method: SamplingMethodEnum
    sample_code: str = Field(..., min_length=1, max_length=50)
    sampling_date: datetime
    sampled_by: str = Field(..., min_length=1)
    swab_area_cm2: Optional[float] = Field(None, ge=0)
    rinse_volume_ml: Optional[float] = Field(None, ge=0)
    contact_plate_size_cm2: Optional[float] = Field(None, ge=0)
    dilution_factor: float = Field(1.0, ge=0)
    absorbance_sample: Optional[float] = Field(None, ge=0)
    absorbance_std: Optional[float] = Field(None, gt=0)
    total_germ_count: Optional[float] = Field(None, ge=0)
    yeast_mold_count: Optional[float] = Field(None, ge=0)
    endotoxin_value: Optional[float] = Field(None, ge=0)
    deviations: Optional[str] = None

class FormulationEquipmentCreate(BaseModel):
    equipment_id: int = Field(..., gt=0)
    category: EquipmentCategoryEnum
    contact_parts: Optional[str] = None
    has_cip: bool = False
    has_sip: bool = False
    sampling_points_count: int = Field(0, ge=0)
    worst_case_sampling_points: Optional[str] = None

# ==================== DOSAGE FORM ENDPOINTS ====================

@router.get("/dosage-forms", response_model=List[DosageFormResponse])
def get_all_dosage_forms(
    plant_type: Optional[PlantTypeEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all dosage forms, optionally filtered by plant type"""
    try:
        query = db.query(DosageForm)
        if plant_type:
            query = query.filter(DosageForm.plant_type == plant_type)
        return query.all()
    except Exception as e:
        logger.error(f"Error getting dosage forms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dosage-forms/{dosage_form_id}", response_model=DosageFormResponse)
def get_dosage_form(
    dosage_form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dosage form by ID"""
    try:
        dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
        if not dosage_form:
            raise HTTPException(404, "Dosage form not found")
        return dosage_form
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dosage form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dosage-forms", response_model=DosageFormResponse)
def create_dosage_form(
    data: DosageFormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new dosage form (Admin only)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(403, "Admin access required")
        
        existing = db.query(DosageForm).filter(DosageForm.code == data.code).first()
        if existing:
            raise HTTPException(400, "Dosage form with this code already exists")
        
        dosage_form = DosageForm(**data.model_dump())
        db.add(dosage_form)
        db.commit()
        db.refresh(dosage_form)
        return dosage_form
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product-dosage-form")
def link_product_to_dosage_form(
    data: ProductDosageFormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a product to a dosage form"""
    try:
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
        
        link = ProductDosageForm(**data.model_dump())
        db.add(link)
        db.commit()
        db.refresh(link)
        
        return {
            "success": True,
            "message": f"Product {product.name} linked to {dosage_form.name}",
            "product_id": product.id,
            "dosage_form_id": dosage_form.id,
            "link_id": link.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking product to dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{product_id}/dosage-form")
def get_product_dosage_form(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dosage form information for a product"""
    try:
        link = db.query(ProductDosageForm).filter(
            ProductDosageForm.product_id == product_id
        ).first()
        
        if not link:
            return {"message": "Product not linked to any dosage form"}
        
        dosage_form = db.query(DosageForm).filter(DosageForm.id == link.dosage_form_id).first()
        requirements = FormulationService.get_dosage_form_requirements(dosage_form.code.value) if dosage_form else {}
        
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
    except Exception as e:
        logger.error(f"Error getting product dosage form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SAMPLING LOCATION ENDPOINTS ====================

@router.get("/equipment/{equipment_id}/sampling-locations")
def get_equipment_sampling_locations(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sampling locations for an equipment"""
    try:
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
    except Exception as e:
        logger.error(f"Error getting sampling locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sampling-locations")
def create_sampling_location(
    data: SamplingLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a sampling location for an equipment"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise HTTPException(404, "Equipment not found")
        
        location = SamplingLocation(**data.model_dump())
        db.add(location)
        db.commit()
        db.refresh(location)
        
        return {
            "success": True,
            "location_id": location.id,
            "location_name": location.location_name,
            "message": f"Sampling location created for {equipment.name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sampling location: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sampling-results")
def record_sampling_result(
    data: SamplingResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a sampling result"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
        if not session:
            raise HTTPException(404, "Validation session not found")
        
        result = SamplingResult(**data.model_dump())
        db.add(result)
        db.commit()
        db.refresh(result)
        
        return {
            "success": True,
            "result_id": result.id,
            "sample_code": result.sample_code,
            "message": "Sampling result recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording sampling result: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FORMULATION EQUIPMENT ENDPOINTS ====================

@router.post("/equipment/categorize")
def categorize_equipment(
    data: FormulationEquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Categorize equipment for formulation plants"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise HTTPException(404, "Equipment not found")
        
        existing = db.query(FormulationEquipment).filter(
            FormulationEquipment.equipment_id == data.equipment_id
        ).first()
        
        if existing:
            # Update existing
            for key, value in data.model_dump().items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return {"success": True, "message": "Equipment categorization updated", "id": existing.id}
        else:
            # Create new
            formulation_eq = FormulationEquipment(**data.model_dump())
            db.add(formulation_eq)
            db.commit()
            db.refresh(formulation_eq)
            return {"success": True, "message": "Equipment categorized successfully", "id": formulation_eq.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error categorizing equipment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment/category/{category}")
def get_equipment_by_category(
    category: EquipmentCategoryEnum,
    plant: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all equipment of a specific category"""
    try:
        query = db.query(FormulationEquipment).filter(
            FormulationEquipment.category == category
        )
        
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
    except Exception as e:
        logger.error(f"Error getting equipment by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PLANT TYPE VALIDATION ====================

@router.get("/plant-type/{plant_type}/validation-requirements")
def get_plant_type_validation_requirements(
    plant_type: PlantTypeEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cleaning validation requirements for a specific plant type"""
    try:
        requirements = FormulationService.get_plant_type_requirements(plant_type.value)
        
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
    except Exception as e:
        logger.error(f"Error getting plant type requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STERILE LIMIT CALCULATOR (FIXED) ====================

@router.post("/sterile-limit-calculator")
def calculate_sterile_limit(
    maco_mg: float = Query(..., description="MACO in mg", gt=0),
    equipment_area_m2: float = Query(..., description="Equipment surface area in m²", gt=0),
    endotoxin_factor: float = Query(1.0, description="Endotoxin safety factor", ge=0.1, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate stricter limits for sterile/injectable products
    
    - Normal limit: Standard limit for non-sterile products
    - Sterile limit: 10x stricter limit for sterile/injectable products
    - Endotoxin limit: EU/ml limit for endotoxin testing
    
    Reference: PDA TR 29, EMA/CHMP/CVMP/SWP/169430/2012
    """
    try:
        # Input validation
        if maco_mg <= 0:
            raise HTTPException(status_code=400, detail="MACO must be greater than 0")
        if equipment_area_m2 <= 0:
            raise HTTPException(status_code=400, detail="Equipment area must be greater than 0")
        
        # Calculate limits
        result = FormulationService.calculate_sterile_limit(
            maco_mg, equipment_area_m2, endotoxin_factor
        )
        
        return {
            "success": True,
            "maco_mg": maco_mg,
            "equipment_area_m2": equipment_area_m2,
            "endotoxin_factor": endotoxin_factor,
            "normal_limit_ppm": result.get("normal_limit_ppm", 0),
            "sterile_limit_ppm": result.get("sterile_limit_ppm", 0),
            "endotoxin_limit_eu_ml": result.get("endotoxin_limit_eu_ml", 0.25),
            "recommendation": result.get("recommendation", "Use sterile_limit_ppm for injectable products"),
            "reference": result.get("reference", "PDA TR 29, EMA/CHMP/CVMP/SWP/169430/2012")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sterile limit calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ==================== ALTERNATIVE GET METHOD FOR STERILE LIMIT (Backward Compatibility) ====================

@router.get("/sterile-limit-calculator")
def calculate_sterile_limit_get(
    maco_mg: float = Query(..., description="MACO in mg", gt=0),
    equipment_area_m2: float = Query(..., description="Equipment surface area in m²", gt=0),
    endotoxin_factor: float = Query(1.0, description="Endotoxin safety factor", ge=0.1, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate stricter limits for sterile/injectable products (GET method for backward compatibility)
    """
    return calculate_sterile_limit(maco_mg, equipment_area_m2, endotoxin_factor, current_user)


# ==================== INITIALIZE DOSAGE FORMS (Run once) ====================

@router.post("/initialize-dosage-forms")
def initialize_dosage_forms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize all dosage forms (Admin only)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(403, "Admin access required")
        
        count = 0
        created_forms = []
        
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
                created_forms.append(code)
                count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Initialized {count} dosage forms",
            "created_forms": created_forms,
            "total_forms": len(FormulationService.DOSAGE_FORM_REQUIREMENTS)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing dosage forms: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))