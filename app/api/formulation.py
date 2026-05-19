from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ..database import get_db
from ..models.dosage_form import DosageForm, DosageFormEnum, PlantTypeEnum, ProductDosageForm
from ..models.sampling_methods import SamplingLocation, SamplingMethodEnum, SamplingResult
from ..models.formulation_equipment import FormulationEquipment, EquipmentCategoryEnum
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession
from ..services.formulation_service import FormulationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Formulation Plants"])


# ============================================
# SCHEMAS
# ============================================

class DosageFormCreate(BaseModel):
    name: str
    code: str
    plant_type: str
    requires_sterility: bool = False
    requires_endotoxin_testing: bool = False
    requires_particle_count: bool = False
    default_microbial_limit_cfu: Optional[float] = None
    default_endotoxin_limit_eu_ml: Optional[float] = None
    description: Optional[str] = None


class DosageFormUpdate(BaseModel):
    name: Optional[str] = None
    requires_sterility: Optional[bool] = None
    requires_endotoxin_testing: Optional[bool] = None
    default_microbial_limit_cfu: Optional[float] = None
    default_endotoxin_limit_eu_ml: Optional[float] = None
    is_active: Optional[bool] = None


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
    recommended_method: str = "swab"
    recovery_factor_percent: float = 100.0


class SamplingLocationUpdate(BaseModel):
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    is_hard_to_clean: Optional[bool] = None
    is_worst_case: Optional[bool] = None
    priority: Optional[int] = None
    recovery_factor_percent: Optional[float] = None
    is_active: Optional[bool] = None


class SamplingResultCreate(BaseModel):
    session_id: int
    location_id: Optional[int] = None
    sampling_method: str
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
    category: str
    contact_parts: Optional[str] = None
    has_cip: bool = False
    has_sip: bool = False
    sampling_points_count: int = 0
    worst_case_sampling_points: Optional[str] = None


class FormulationEquipmentUpdate(BaseModel):
    category: Optional[str] = None
    has_cip: Optional[bool] = None
    has_sip: Optional[bool] = None
    sampling_points_count: Optional[int] = None
    is_validated_for_cleaning: Optional[bool] = None


# ============================================
# DOSAGE FORMS CRUD - PUBLIC
# ============================================

@router.get("/dosage-forms")
def get_all_dosage_forms(plant_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all dosage forms - PUBLIC"""
    try:
        query = db.query(DosageForm).filter(DosageForm.is_active == True)
        if plant_type:
            query = query.filter(DosageForm.plant_type == plant_type)
        forms = query.all()
        return {"success": True, "count": len(forms), "data": forms}
    except Exception as e:
        logger.error(f"Error getting dosage forms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dosage-forms/all")
def get_all_dosage_forms_including_inactive(db: Session = Depends(get_db)):
    """Get ALL dosage forms (including inactive) - PUBLIC"""
    try:
        forms = db.query(DosageForm).all()
        return {"success": True, "count": len(forms), "data": forms}
    except Exception as e:
        logger.error(f"Error getting all dosage forms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dosage-forms/{dosage_form_id}")
def get_dosage_form(dosage_form_id: int, db: Session = Depends(get_db)):
    """Get dosage form by ID - PUBLIC"""
    try:
        dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
        if not dosage_form:
            raise HTTPException(404, "Dosage form not found")
        return {"success": True, "data": dosage_form}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dosage form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dosage-forms")
def create_dosage_form(data: DosageFormCreate, db: Session = Depends(get_db)):
    """Create new dosage form - PUBLIC (Returns existing if duplicate)"""
    try:
        existing = db.query(DosageForm).filter(DosageForm.code == data.code).first()
        if existing:
            # Return existing instead of error
            return {"success": True, "message": "Dosage form already exists", "data": existing, "already_exists": True}
        
        dosage_form = DosageForm(**data.dict(), is_active=True)
        db.add(dosage_form)
        db.commit()
        db.refresh(dosage_form)
        return {"success": True, "message": "Dosage form created", "data": dosage_form, "already_exists": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/dosage-forms/{dosage_form_id}")
def update_dosage_form(dosage_form_id: int, data: DosageFormUpdate, db: Session = Depends(get_db)):
    """Update dosage form - PUBLIC"""
    try:
        dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
        if not dosage_form:
            raise HTTPException(404, "Dosage form not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(dosage_form, key, value)
        
        db.commit()
        db.refresh(dosage_form)
        return {"success": True, "message": "Dosage form updated", "data": dosage_form}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/dosage-forms/{dosage_form_id}")
def delete_dosage_form(dosage_form_id: int, db: Session = Depends(get_db)):
    """Delete dosage form - PUBLIC"""
    try:
        dosage_form = db.query(DosageForm).filter(DosageForm.id == dosage_form_id).first()
        if not dosage_form:
            raise HTTPException(404, "Dosage form not found")
        
        db.delete(dosage_form)
        db.commit()
        return {"success": True, "message": "Dosage form deleted", "id": dosage_form_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/dosage-forms/all")
def delete_all_dosage_forms(db: Session = Depends(get_db)):
    """Delete ALL dosage forms - PUBLIC"""
    try:
        count = db.query(DosageForm).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} dosage forms", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all dosage forms: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PRODUCT DOSAGE FORM LINKS - PUBLIC
# ============================================

@router.post("/product-dosage-form")
def link_product_to_dosage_form(data: ProductDosageFormCreate, db: Session = Depends(get_db)):
    """Link product to dosage form - PUBLIC"""
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
        
        link = ProductDosageForm(**data.dict())
        db.add(link)
        db.commit()
        db.refresh(link)
        
        return {
            "success": True,
            "message": f"Product {product.name} linked to {dosage_form.name}",
            "link_id": link.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking product to dosage form: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/product-dosage-form/{link_id}")
def delete_product_dosage_form_link(link_id: int, db: Session = Depends(get_db)):
    """Delete product-dosage form link - PUBLIC"""
    try:
        link = db.query(ProductDosageForm).filter(ProductDosageForm.id == link_id).first()
        if not link:
            raise HTTPException(404, "Link not found")
        
        db.delete(link)
        db.commit()
        return {"success": True, "message": "Link deleted", "id": link_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting link: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{product_id}/dosage-form")
def get_product_dosage_form(product_id: int, db: Session = Depends(get_db)):
    """Get dosage form for a product - PUBLIC"""
    try:
        link = db.query(ProductDosageForm).filter(ProductDosageForm.product_id == product_id).first()
        if not link:
            return {"success": True, "message": "Product not linked to any dosage form", "data": None}
        
        dosage_form = db.query(DosageForm).filter(DosageForm.id == link.dosage_form_id).first()
        requirements = FormulationService.get_dosage_form_requirements(dosage_form.code.value) if dosage_form else {}
        
        return {
            "success": True,
            "data": {
                "product_id": product_id,
                "dosage_form": dosage_form.to_dict() if dosage_form else None,
                "batch_quantity": link.batch_quantity,
                "batch_unit": link.batch_unit,
                "daily_dose_range": {
                    "min": link.min_daily_dose,
                    "max": link.max_daily_dose,
                    "unit": link.dose_unit
                },
                "cleaning_requirements": requirements
            }
        }
    except Exception as e:
        logger.error(f"Error getting product dosage form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SAMPLING LOCATIONS CRUD - PUBLIC
# ============================================

@router.get("/equipment/{equipment_id}/sampling-locations")
def get_equipment_sampling_locations(equipment_id: int, db: Session = Depends(get_db)):
    """Get sampling locations for equipment - PUBLIC"""
    try:
        locations = db.query(SamplingLocation).filter(
            SamplingLocation.equipment_id == equipment_id,
            SamplingLocation.is_active == True
        ).order_by(SamplingLocation.priority).all()
        
        return {
            "success": True,
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
                    "recommended_method": loc.recommended_method.value if loc.recommended_method else "swab",
                    "recovery_factor_percent": loc.recovery_factor_percent
                }
                for loc in locations
            ]
        }
    except Exception as e:
        logger.error(f"Error getting sampling locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sampling-locations/all")
def get_all_sampling_locations(db: Session = Depends(get_db)):
    """Get all sampling locations - PUBLIC"""
    try:
        locations = db.query(SamplingLocation).all()
        return {"success": True, "count": len(locations), "data": locations}
    except Exception as e:
        logger.error(f"Error getting all sampling locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sampling-locations")
def create_sampling_location(data: SamplingLocationCreate, db: Session = Depends(get_db)):
    """Create sampling location - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise HTTPException(404, "Equipment not found")
        
        location = SamplingLocation(**data.dict(), is_active=True)
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


@router.put("/sampling-locations/{location_id}")
def update_sampling_location(location_id: int, data: SamplingLocationUpdate, db: Session = Depends(get_db)):
    """Update sampling location - PUBLIC"""
    try:
        location = db.query(SamplingLocation).filter(SamplingLocation.id == location_id).first()
        if not location:
            raise HTTPException(404, "Sampling location not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(location, key, value)
        
        db.commit()
        db.refresh(location)
        
        return {"success": True, "message": "Sampling location updated", "data": location}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sampling location: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sampling-locations/{location_id}")
def delete_sampling_location(location_id: int, db: Session = Depends(get_db)):
    """Delete sampling location - PUBLIC"""
    try:
        location = db.query(SamplingLocation).filter(SamplingLocation.id == location_id).first()
        if not location:
            raise HTTPException(404, "Sampling location not found")
        
        db.delete(location)
        db.commit()
        return {"success": True, "message": "Sampling location deleted", "id": location_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sampling location: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sampling-locations/all")
def delete_all_sampling_locations(db: Session = Depends(get_db)):
    """Delete ALL sampling locations - PUBLIC"""
    try:
        count = db.query(SamplingLocation).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} sampling locations", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all sampling locations: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SAMPLING RESULTS - PUBLIC
# ============================================

@router.post("/sampling-results")
def record_sampling_result(data: SamplingResultCreate, db: Session = Depends(get_db)):
    """Record sampling result - PUBLIC"""
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording sampling result: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sampling-results/session/{session_id}")
def get_sampling_results_by_session(session_id: int, db: Session = Depends(get_db)):
    """Get all sampling results for a session - PUBLIC"""
    try:
        results = db.query(SamplingResult).filter(SamplingResult.session_id == session_id).all()
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        logger.error(f"Error getting sampling results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sampling-results/{result_id}")
def delete_sampling_result(result_id: int, db: Session = Depends(get_db)):
    """Delete sampling result - PUBLIC"""
    try:
        result = db.query(SamplingResult).filter(SamplingResult.id == result_id).first()
        if not result:
            raise HTTPException(404, "Sampling result not found")
        
        db.delete(result)
        db.commit()
        return {"success": True, "message": "Sampling result deleted", "id": result_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sampling result: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FORMULATION EQUIPMENT - PUBLIC
# ============================================

@router.post("/equipment/categorize")
def categorize_equipment(data: FormulationEquipmentCreate, db: Session = Depends(get_db)):
    """Categorize equipment for formulation - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise HTTPException(404, "Equipment not found")
        
        existing = db.query(FormulationEquipment).filter(
            FormulationEquipment.equipment_id == data.equipment_id
        ).first()
        
        if existing:
            for key, value in data.dict().items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return {"success": True, "message": "Equipment categorization updated", "id": existing.id}
        else:
            formulation_eq = FormulationEquipment(**data.dict())
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


@router.put("/formulation-equipment/{fe_id}")
def update_formulation_equipment(fe_id: int, data: FormulationEquipmentUpdate, db: Session = Depends(get_db)):
    """Update formulation equipment - PUBLIC"""
    try:
        fe = db.query(FormulationEquipment).filter(FormulationEquipment.id == fe_id).first()
        if not fe:
            raise HTTPException(404, "Formulation equipment not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(fe, key, value)
        
        db.commit()
        db.refresh(fe)
        return {"success": True, "message": "Formulation equipment updated", "data": fe}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating formulation equipment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/formulation-equipment/{fe_id}")
def delete_formulation_equipment(fe_id: int, db: Session = Depends(get_db)):
    """Delete formulation equipment record - PUBLIC"""
    try:
        fe = db.query(FormulationEquipment).filter(FormulationEquipment.id == fe_id).first()
        if not fe:
            raise HTTPException(404, "Formulation equipment not found")
        
        db.delete(fe)
        db.commit()
        return {"success": True, "message": "Formulation equipment deleted", "id": fe_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting formulation equipment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment/category/{category}")
def get_equipment_by_category(category: str, plant: Optional[str] = None, db: Session = Depends(get_db)):
    """Get equipment by category - PUBLIC"""
    try:
        query = db.query(FormulationEquipment).filter(FormulationEquipment.category == category)
        
        results = []
        for fe in query.all():
            eq = db.query(Equipment).filter(Equipment.id == fe.equipment_id).first()
            if eq and (not plant or eq.plant == plant):
                results.append({
                    "id": fe.id,
                    "equipment_id": fe.equipment_id,
                    "equipment_name": eq.name,
                    "category": fe.category.value if hasattr(fe.category, 'value') else fe.category,
                    "has_cip": fe.has_cip,
                    "has_sip": fe.has_sip,
                    "sampling_points_count": fe.sampling_points_count
                })
        
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        logger.error(f"Error getting equipment by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formulation-equipment/all")
def get_all_formulation_equipment(db: Session = Depends(get_db)):
    """Get all formulation equipment - PUBLIC"""
    try:
        records = db.query(FormulationEquipment).all()
        return {"success": True, "count": len(records), "data": records}
    except Exception as e:
        logger.error(f"Error getting all formulation equipment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/formulation-equipment/all")
def delete_all_formulation_equipment(db: Session = Depends(get_db)):
    """Delete ALL formulation equipment - PUBLIC"""
    try:
        count = db.query(FormulationEquipment).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} formulation equipment records", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all formulation equipment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PLANT TYPE VALIDATION - PUBLIC
# ============================================

@router.get("/plant-type/{plant_type}/validation-requirements")
def get_plant_type_validation_requirements(plant_type: str, db: Session = Depends(get_db)):
    """Get validation requirements for plant type - PUBLIC"""
    try:
        requirements = FormulationService.get_plant_type_requirements(plant_type)
        
        dosage_forms = db.query(DosageForm).filter(
            DosageForm.plant_type == plant_type
        ).all()
        
        return {
            "success": True,
            "plant_type": plant_type,
            "requirements": requirements,
            "dosage_forms_in_plant": [
                {"id": df.id, "name": df.name, "code": df.code.value if df.code else None}
                for df in dosage_forms
            ],
            "reference_guidelines": [
                "APIC Cleaning Validation Guide 2021",
                "PDA TR 29 - Cleaning Validation",
                "EMA/CHMP/CVMP/SWP/169430/2012"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting plant type requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STERILE LIMIT CALCULATOR - PUBLIC
# ============================================

@router.post("/sterile-limit-calculator")
def calculate_sterile_limit_post(
    maco_mg: float = Query(..., description="MACO in mg", gt=0),
    equipment_area_m2: float = Query(..., description="Equipment surface area in m²", gt=0),
    endotoxin_factor: float = Query(1.0, description="Endotoxin safety factor", ge=0.1, le=10)
):
    """Calculate stricter limits for sterile/injectable products - PUBLIC"""
    try:
        if maco_mg <= 0:
            raise HTTPException(status_code=400, detail="MACO must be greater than 0")
        if equipment_area_m2 <= 0:
            raise HTTPException(status_code=400, detail="Equipment area must be greater than 0")
        
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


@router.get("/sterile-limit-calculator")
def calculate_sterile_limit_get(
    maco_mg: float = Query(..., description="MACO in mg", gt=0),
    equipment_area_m2: float = Query(..., description="Equipment surface area in m²", gt=0),
    endotoxin_factor: float = Query(1.0, description="Endotoxin safety factor", ge=0.1, le=10)
):
    """Calculate stricter limits for sterile/injectable products (GET) - PUBLIC"""
    return calculate_sterile_limit_post(maco_mg, equipment_area_m2, endotoxin_factor)


# ============================================
# INITIALIZE DOSAGE FORMS - PUBLIC
# ============================================

@router.post("/initialize-dosage-forms")
def initialize_dosage_forms(db: Session = Depends(get_db)):
    """Initialize all dosage forms - PUBLIC"""
    try:
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
                    is_active=True
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
    except Exception as e:
        logger.error(f"Error initializing dosage forms: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))