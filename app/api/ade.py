# app/api/ade.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.ade_calculation import ADECalculation
from ..services.ade_service import ADEService
from datetime import datetime

router = APIRouter(prefix="/api/ade", tags=["ADE Calculator"])

# ============================================
# REQUEST SCHEMA (Must match the one in schemas/ade.py)
# ============================================

class ADECalculationRequest(BaseModel):
    product_id: int
    noael_mg_per_kg: Optional[float] = None
    loael_mg_per_kg: Optional[float] = None
    ld50_mg_per_kg: Optional[float] = None
    body_weight_kg: float = 50.0
    uf1: float = 1.0
    uf2: float = 10.0
    uf3: float = 10.0
    uf4: float = 1.0
    uf5: float = 1.0
    modifying_factor: float = 1.0
    pk_adjustment: float = 1.0
    route: str = "oral"

class ADECalculationResponse(BaseModel):
    id: int
    product_id: int
    calculated_ade_mg_per_day: float
    calculation_method: str
    calculation_justification: str
    route: str
    is_approved: bool
    
    class Config:
        from_attributes = True

# ============================================
# API ENDPOINTS
# ============================================

@router.post("/calculate", response_model=ADECalculationResponse)
def calculate_ade(
    request: ADECalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate ADE/PDE based on toxicology data
    APIC Section 4.2.1.1 - Health-Based Exposure Limits (HBEL)
    
    Priority: NOAEL > LOAEL > LD50 > TTC
    
    Example Request:
    {
        "product_id": 1,
        "noael_mg_per_kg": 100,
        "body_weight_kg": 50,
        "uf1": 1,
        "uf2": 10,
        "uf3": 10,
        "uf4": 1,
        "uf5": 1,
        "route": "oral"
    }
    """
    try:
        result = ADEService.calculate_and_save(db, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

@router.get("/calculate")
def calculate_ade_get(
    product_id: int,
    noael_mg_per_kg: Optional[float] = None,
    loael_mg_per_kg: Optional[float] = None,
    ld50_mg_per_kg: Optional[float] = None,
    body_weight_kg: float = 50.0,
    uf1: float = 1.0,
    uf2: float = 10.0,
    uf3: float = 10.0,
    uf4: float = 1.0,
    uf5: float = 1.0,
    route: str = "oral",
    db: Session = Depends(get_db)
):
    """Calculate ADE/PDE using GET method (for quick calculations)"""
    request = ADECalculationRequest(
        product_id=product_id,
        noael_mg_per_kg=noael_mg_per_kg,
        loael_mg_per_kg=loael_mg_per_kg,
        ld50_mg_per_kg=ld50_mg_per_kg,
        body_weight_kg=body_weight_kg,
        uf1=uf1,
        uf2=uf2,
        uf3=uf3,
        uf4=uf4,
        uf5=uf5,
        route=route
    )
    return calculate_ade(request, db)

@router.get("/history/{product_id}")
def get_ade_history(
    product_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get ADE calculation history for a product"""
    calculations = db.query(ADECalculation).filter(
        ADECalculation.product_id == product_id
    ).order_by(ADECalculation.created_at.desc()).limit(limit).all()
    
    return {
        "success": True,
        "count": len(calculations),
        "data": calculations
    }

@router.get("/latest/{product_id}")
def get_latest_ade(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get the latest ADE calculation for a product"""
    calculation = db.query(ADECalculation).filter(
        ADECalculation.product_id == product_id
    ).order_by(ADECalculation.created_at.desc()).first()
    
    if not calculation:
        raise HTTPException(status_code=404, detail="No ADE calculation found for this product")
    
    return calculation

@router.post("/approve/{calculation_id}")
def approve_ade_calculation(
    calculation_id: int,
    reviewed_by: str,
    db: Session = Depends(get_db)
):
    """Approve an ADE calculation for use in MACO"""
    from sqlalchemy import func
    
    calculation = db.query(ADECalculation).filter(ADECalculation.id == calculation_id).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    calculation.is_approved = 1
    calculation.reviewed_by = reviewed_by
    calculation.reviewed_date = func.now()
    
    # Update product's ADE/PDE value
    product = db.query(Product).filter(Product.id == calculation.product_id).first()
    if product:
        product.ade_pde = calculation.calculated_ade_mg_per_day * 1000  # Convert to µg/day
    
    db.commit()
    
    return {
        "success": True,
        "message": "ADE calculation approved",
        "product_ade_updated": product.ade_pde if product else None
    }