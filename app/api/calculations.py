from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.product import Product
from ..models.session import ValidationSession
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