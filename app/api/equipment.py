from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.equipment import Equipment
from ..schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[EquipmentResponse])
def get_equipment(
    skip: int = 0, 
    limit: int = 100,
    plant: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all equipment - PUBLIC"""
    try:
        query = db.query(Equipment)
        if plant:
            query = query.filter(Equipment.plant == plant)
        equipment = query.offset(skip).limit(limit).all()
        return equipment
    except Exception as e:
        logger.error(f"Get equipment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plant/{plant_name}", response_model=List[EquipmentResponse])
def get_equipment_by_plant(plant_name: str, db: Session = Depends(get_db)):
    """Get equipment by plant - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.plant == plant_name).all()
        return equipment
    except Exception as e:
        logger.error(f"Get equipment by plant error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=EquipmentResponse)
def create_equipment(equipment: EquipmentCreate, db: Session = Depends(get_db)):
    """Create new equipment - PUBLIC"""
    try:
        existing = db.query(Equipment).filter(Equipment.equipment_id == equipment.equipment_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Equipment ID already exists")
        
        new_equipment = Equipment(**equipment.dict())
        db.add(new_equipment)
        db.commit()
        db.refresh(new_equipment)
        
        return new_equipment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create equipment error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(equipment_id: int, db: Session = Depends(get_db)):
    """Get equipment by ID - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        return equipment
    except Exception as e:
        logger.error(f"Get equipment by ID error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(equipment_id: int, equipment_data: EquipmentUpdate, db: Session = Depends(get_db)):
    """Update equipment - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        for key, value in equipment_data.dict().items():
            if value is not None:
                setattr(equipment, key, value)
        
        db.commit()
        db.refresh(equipment)
        
        return equipment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update equipment error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{equipment_id}")
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """Delete equipment - PUBLIC"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        db.delete(equipment)
        db.commit()
        
        return {"message": "Equipment deleted successfully", "id": equipment_id, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete equipment error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/all")
def delete_all_equipment(db: Session = Depends(get_db)):
    """Delete ALL equipment - PUBLIC"""
    try:
        count = db.query(Equipment).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} equipment", "deleted_count": count}
    except Exception as e:
        logger.error(f"Delete all equipment error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all/details")
def get_all_equipment_detailed(db: Session = Depends(get_db)):
    """Get all equipment with full details - PUBLIC"""
    try:
        equipment = db.query(Equipment).all()
        return {
            "success": True,
            "count": len(equipment),
            "equipment": [
                {
                    "id": e.id,
                    "name": e.name,
                    "equipment_id": e.equipment_id,
                    "capacity": e.capacity,
                    "surface_area_m2": e.surface_area,
                    "used_for": e.used_for,
                    "cleaning_procedure": e.cleaning_procedure,
                    "plant": e.plant
                }
                for e in equipment
            ]
        }
    except Exception as e:
        logger.error(f"Get all equipment detailed error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))