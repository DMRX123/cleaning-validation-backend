from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.product import Product
from ..models.session import ValidationSession
from ..models.equipment import Equipment
from ..services.maco import MACOService
from ..services.swab import SwabService
from ..services.rinse import RinseService
from ..services.worst_case import WorstCaseService
from ..services.equipment_filter import EquipmentFilterService
from pydantic import BaseModel

router = APIRouter()

class MACORequest(BaseModel):
    previous_product_id: int
    next_product_id: int

class SwabLimitRequest(BaseModel):
    session_id: int
    total_surface_area: float

class RinseLimitRequest(BaseModel):
    session_id: int
    equipment_id: int
    rinse_volume: float
    total_surface_area: float  # Total product contact surface area

@router.post("/maco")
def calculate_maco(request: MACORequest, db: Session = Depends(get_db)):
    previous = db.query(Product).filter(Product.id == request.previous_product_id).first()
    next_product = db.query(Product).filter(Product.id == request.next_product_id).first()
    
    if not previous or not next_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    result = MACOService.calculate_all(previous, next_product)
    return result

@router.post("/swab-limit")
def calculate_swab_limit(request: SwabLimitRequest, db: Session = Depends(get_db)):
    session = db.query(ValidationSession).filter(ValidationSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = SwabService.calculate_swab_limit(session, request.total_surface_area)
    return result

@router.post("/rinse-limit")
def calculate_rinse_limit(request: RinseLimitRequest, db: Session = Depends(get_db)):
    """Calculate rinse limit for equipment"""
    # Get session
    session = db.query(ValidationSession).filter(ValidationSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get equipment
    equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Get MACO value from session (assuming it's stored or calculate it)
    # For now, get from session or previous/next product
    previous_product = session.previous_product
    next_product = session.next_product
    
    if not previous_product or not next_product:
        raise HTTPException(status_code=404, detail="Products not found in session")
    
    # Calculate MACO
    maco_result = MACOService.calculate_all(previous_product, next_product)
    maco_mg = maco_result.get("maco_mg", 0)
    
    # Calculate rinse limit using RinseService
    limit_mg = RinseService.calculate_rinse_limit(
        maco_mg=maco_mg,
        equipment_surface_area=equipment.surface_area,
        total_surface_area=request.total_surface_area
    )
    
    # Calculate ppm from limit
    limit_ppm = RinseService.calculate_ppm_from_limit(
        limit_mg=limit_mg,
        rinse_volume_l=request.rinse_volume
    )
    
    # Calculate volume by LOQ
    loq = next_product.loq if next_product.loq else 0.1
    volume_loq = RinseService.calculate_volume_by_loq(
        limit_mg=limit_mg,
        loq_ppm=loq
    )
    
    # Calculate volume by 10ppm
    volume_10ppm = RinseService.calculate_volume_by_10ppm(limit_mg=limit_mg)
    
    # Calculate volume by AMV
    swab_dilution = next_product.swab_dilution if next_product.swab_dilution else 20
    swab_area = next_product.swab_area if next_product.swab_area else 0.01
    volume_amv = RinseService.calculate_volume_by_amv(
        swab_dilution_ml=swab_dilution,
        swab_surface_area_m2=swab_area,
        equipment_surface_area_m2=equipment.surface_area
    )
    
    return {
        "limit_mg": limit_mg,
        "limit_ppm": limit_ppm,
        "volume_loq": volume_loq,
        "volume_10ppm": volume_10ppm,
        "volume_amv": volume_amv,
        "maco_mg": maco_mg
    }

@router.post("/worst-case")
def find_worst_case(plant: str = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if plant:
        query = query.filter(Product.plant == plant)
    
    products = query.all()
    worst_case = WorstCaseService.find_worst_case(products)
    
    if worst_case:
        return {"id": worst_case.id, "name": worst_case.name, "solubility": worst_case.solubility}
    return {"message": "No products found"}