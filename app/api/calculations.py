from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.product import Product
from ..models.session import ValidationSession
from ..models.equipment import Equipment
from ..services.maco import MACOService
from ..services.swab import SwabService
from ..services.rinse import RinseService
from ..services.worst_case_service import WorstCaseService
from ..services.equipment_filter import EquipmentFilterService
from .auth import get_current_user
from ..models.user import User
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
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
    total_surface_area: float


@router.post("/maco")
def calculate_maco(
    request: MACORequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate MACO (Maximum Allowable Carry Over) between two products"""
    try:
        previous = db.query(Product).filter(Product.id == request.previous_product_id).first()
        next_product = db.query(Product).filter(Product.id == request.next_product_id).first()
        
        if not previous:
            raise HTTPException(status_code=404, detail=f"Previous product with ID {request.previous_product_id} not found")
        if not next_product:
            raise HTTPException(status_code=404, detail=f"Next product with ID {request.next_product_id} not found")
        
        result = MACOService.calculate_all(previous, next_product)
        
        return {
            "method_10ppm": float(result.get("method_10ppm", 0)),
            "method_tdd": float(result.get("method_tdd", 0)),
            "method_ade_pde": float(result.get("method_ade_pde", 0)),
            "method_ttc": float(result.get("method_ttc", 0)),
            "lowest_maco": float(result.get("lowest_maco", 0)),
            "selected_method": result.get("selected_method", "N/A")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MACO calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MACO calculation failed: {str(e)}")


@router.post("/swab-limit")
def calculate_swab_limit(
    request: SwabLimitRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate swab limit for validation session"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session with ID {request.session_id} not found")
        
        # Get MACO value
        if session.lowest_maco and session.lowest_maco > 0:
            maco_mg = session.lowest_maco
        else:
            previous = session.previous_product
            next_product = session.next_product
            if not previous or not next_product:
                raise HTTPException(status_code=404, detail="Products not found in session")
            maco_result = MACOService.calculate_all(previous, next_product)
            maco_mg = maco_result.get("lowest_maco", 0)
        
        product = session.next_product
        if not product:
            raise HTTPException(status_code=404, detail="Next product not found")
        
        if request.total_surface_area <= 0:
            raise HTTPException(status_code=400, detail="Total surface area must be greater than 0")
        
        mg_per_swab = SwabService.calculate_mg_per_swab(
            maco_mg=maco_mg,
            swab_surface_area=product.swab_surface_area,
            total_surface_area=request.total_surface_area,
            recovery_percent=product.swab_recovery
        )
        
        ppm = SwabService.calculate_ppm(
            maco_mg=maco_mg,
            swab_surface_area=product.swab_surface_area,
            total_surface_area=request.total_surface_area,
            swab_dilution_ml=product.swab_dilution,
            recovery_percent=product.swab_recovery
        )
        
        return {
            "mg_per_swab": float(mg_per_swab) if mg_per_swab is not None else 0.0,
            "ppm": float(ppm) if ppm is not None else 0.0,
            "maco_mg_used": float(maco_mg),
            "surface_area_used": request.total_surface_area,
            "recovery_used": product.swab_recovery
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Swab limit calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/rinse-limit")
def calculate_rinse_limit(
    request: RinseLimitRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate rinse limit for equipment"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session with ID {request.session_id} not found")
        
        equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail=f"Equipment with ID {request.equipment_id} not found")
        
        previous_product = session.previous_product
        next_product = session.next_product
        
        if not previous_product or not next_product:
            raise HTTPException(status_code=404, detail="Products not found in session")
        
        # Get MACO
        if session.lowest_maco and session.lowest_maco > 0:
            maco_mg = float(session.lowest_maco)
        else:
            maco_result = MACOService.calculate_all(previous_product, next_product)
            maco_mg = float(maco_result.get("lowest_maco", 0))
        
        equipment_surface_area = float(equipment.surface_area) if equipment.surface_area else 0.0
        total_surface_area = float(request.total_surface_area) if request.total_surface_area else 0.0
        rinse_volume = float(request.rinse_volume) if request.rinse_volume else 25.0
        
        if total_surface_area <= 0:
            raise HTTPException(status_code=400, detail="Total surface area must be greater than 0")
        
        # Calculate rinse limit
        limit_mg = RinseService.calculate_rinse_limit(
            maco_mg=maco_mg,
            equipment_surface_area=equipment_surface_area,
            total_surface_area=total_surface_area
        )
        
        limit_ppm = RinseService.calculate_ppm_from_limit(
            limit_mg=limit_mg,
            rinse_volume_l=rinse_volume
        )
        
        loq = float(next_product.loq) if next_product.loq else 0.1
        volume_loq_result = RinseService.calculate_volume_by_loq(
            limit_mg=limit_mg,
            loq_ppm=loq
        )
        volume_loq = volume_loq_result.get("volume_l", 0.0) if isinstance(volume_loq_result, dict) else float(volume_loq_result)
        
        volume_10ppm = RinseService.calculate_volume_by_10ppm(limit_mg=limit_mg)
        
        swab_dilution = float(next_product.swab_dilution) if next_product.swab_dilution else 20.0
        swab_area = float(next_product.swab_surface_area) if next_product.swab_surface_area else 0.01
        volume_amv = RinseService.calculate_volume_by_amv(
            swab_dilution_ml=swab_dilution,
            swab_surface_area_m2=swab_area,
            equipment_surface_area_m2=equipment_surface_area
        )
        
        response_data = {
            "limit_mg": float(limit_mg),
            "limit_ppm": float(limit_ppm),
            "volume_loq": float(volume_loq),
            "volume_10ppm": float(volume_10ppm),
            "volume_amv": float(volume_amv),
            "maco_mg": float(maco_mg),
            "equipment_surface_area": equipment_surface_area,
            "rinse_volume_used": rinse_volume,
            "loq_used": loq
        }
        
        logger.info(f"Rinse limit calculated: {response_data}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in rinse-limit calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/worst-case")
def find_worst_case(
    plant: str = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find worst case product for a plant"""
    try:
        query = db.query(Product)
        if plant:
            query = query.filter(Product.plant == plant)
        
        products = query.all()
        
        if not products:
            return {"message": "No products found"}
        
        worst_case = WorstCaseService.select_worst_case(products)
        
        if worst_case:
            rating = WorstCaseService.calculate_product_rating(worst_case)
            return {
                "id": worst_case.id,
                "name": worst_case.name,
                "product_code": worst_case.product_code,
                "solubility": worst_case.solubility,
                "hardest_to_clean": worst_case.hardest_to_clean,
                "ade_pde": worst_case.ade_pde,
                "min_dose": worst_case.min_dose,
                "total_rating": rating.get("total_rating", 0),
                "plant": worst_case.plant
            }
        return {"message": "Could not determine worst case product"}
        
    except Exception as e:
        logger.error(f"Worst case calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))