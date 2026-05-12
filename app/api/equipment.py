# app/api/equipment.py - COMPLETE FIXED VERSION
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.equipment import Equipment
from ..schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from ..services.audit import AuditService
from ..api.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[EquipmentResponse])
def get_equipment(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all equipment"""
    equipment = db.query(Equipment).offset(skip).limit(limit).all()
    return equipment  # Returns empty list [] if no equipment, which is valid

@router.post("/", response_model=EquipmentResponse)
def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new equipment"""
    # Check if equipment_id already exists
    existing = db.query(Equipment).filter(Equipment.equipment_id == equipment.equipment_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Equipment ID already exists")
    
    new_equipment = Equipment(**equipment.dict())
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    # Log audit
    AuditService.log(
        db, current_user.id, "CREATE", "Equipment", 
        new_equipment.id, None, new_equipment.__dict__
    )
    
    return new_equipment

@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get equipment by ID"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment

@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update equipment"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    old_values = equipment.__dict__.copy()
    
    for key, value in equipment_data.dict().items():
        setattr(equipment, key, value)
    
    db.commit()
    db.refresh(equipment)
    
    # Log audit
    AuditService.log(
        db, current_user.id, "UPDATE", "Equipment", 
        equipment.id, old_values, equipment.__dict__
    )
    
    return equipment

@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete equipment"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    old_values = equipment.__dict__.copy()
    db.delete(equipment)
    db.commit()
    
    # Log audit
    AuditService.log(
        db, current_user.id, "DELETE", "Equipment", 
        equipment_id, old_values, None
    )
    
    return {"message": "Equipment deleted successfully"}

@router.get("/plant/{plant_name}", response_model=List[EquipmentResponse])
def get_equipment_by_plant(
    plant_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get equipment by plant name"""
    equipment = db.query(Equipment).filter(Equipment.plant == plant_name).all()
    return equipment