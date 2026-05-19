from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..models.training import TrainingModule, TrainingRecord
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Training"])


# ============================================
# SCHEMAS
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


class TrainingRecordCreate(BaseModel):
    user_id: int
    module_id: int
    training_date: datetime
    expiry_date: Optional[datetime] = None
    trainer: Optional[str] = None
    score: Optional[float] = None
    is_passed: bool = False


class TrainingRecordUpdate(BaseModel):
    training_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    trainer: Optional[str] = None
    score: Optional[float] = None
    is_passed: Optional[bool] = None
    certificate_issued: Optional[bool] = None


# ============================================
# TRAINING MODULES CRUD - PUBLIC
# ============================================

@router.get("/modules")
def get_training_modules(db: Session = Depends(get_db)):
    """Get all active training modules - PUBLIC"""
    try:
        modules = db.query(TrainingModule).filter(TrainingModule.is_active == True).all()
        return {
            "success": True,
            "count": len(modules),
            "modules": [
                {
                    "id": m.id,
                    "module_code": m.module_code,
                    "title": m.title,
                    "description": m.description,
                    "category": m.category,
                    "version": m.version,
                    "is_active": m.is_active
                }
                for m in modules
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching training modules: {str(e)}")
        return {"success": False, "error": str(e), "modules": []}


@router.get("/modules/all")
def get_all_training_modules(db: Session = Depends(get_db)):
    """Get ALL training modules (including inactive) - PUBLIC"""
    try:
        modules = db.query(TrainingModule).all()
        return {
            "success": True,
            "count": len(modules),
            "modules": [
                {
                    "id": m.id,
                    "module_code": m.module_code,
                    "title": m.title,
                    "description": m.description,
                    "category": m.category,
                    "version": m.version,
                    "is_active": m.is_active
                }
                for m in modules
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching all training modules: {str(e)}")
        return {"success": False, "error": str(e), "modules": []}


@router.get("/modules/{module_id}")
def get_training_module(module_id: int, db: Session = Depends(get_db)):
    """Get training module by ID - PUBLIC"""
    try:
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        return {
            "success": True,
            "id": module.id,
            "module_code": module.module_code,
            "title": module.title,
            "description": module.description,
            "category": module.category,
            "version": module.version,
            "is_active": module.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching training module: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modules")
def create_training_module(data: TrainingModuleCreate, db: Session = Depends(get_db)):
    """Create a new training module - PUBLIC"""
    try:
        existing = db.query(TrainingModule).filter(TrainingModule.module_code == data.module_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Module code already exists")
        
        module = TrainingModule(
            module_code=data.module_code,
            title=data.title,
            description=data.description,
            category=data.category,
            version=data.version,
            is_active=True
        )
        db.add(module)
        db.commit()
        db.refresh(module)
        
        return {
            "success": True,
            "message": "Training module created successfully",
            "module": {
                "id": module.id,
                "module_code": module.module_code,
                "title": module.title,
                "category": module.category,
                "version": module.version
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating training module: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modules/{module_id}")
def update_training_module(module_id: int, data: TrainingModuleUpdate, db: Session = Depends(get_db)):
    """Update training module - PUBLIC"""
    try:
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(module, key, value)
        
        db.commit()
        db.refresh(module)
        
        return {
            "success": True,
            "message": "Training module updated successfully",
            "module": {
                "id": module.id,
                "module_code": module.module_code,
                "title": module.title,
                "category": module.category,
                "version": module.version,
                "is_active": module.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating training module: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/modules/{module_id}")
def delete_training_module(module_id: int, db: Session = Depends(get_db)):
    """Delete training module - PUBLIC"""
    try:
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        
        db.delete(module)
        db.commit()
        
        return {"success": True, "message": "Training module deleted successfully", "id": module_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting training module: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/modules/all")
def delete_all_training_modules(db: Session = Depends(get_db)):
    """Delete ALL training modules - PUBLIC"""
    try:
        count = db.query(TrainingModule).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} training modules", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all training modules: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TRAINING RECORDS CRUD - PUBLIC
# ============================================

@router.get("/records")
def get_training_records(db: Session = Depends(get_db)):
    """Get all training records - PUBLIC"""
    try:
        records = db.query(TrainingRecord).all()
        return {
            "success": True,
            "count": len(records),
            "records": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "module_id": r.module_id,
                    "training_date": r.training_date.isoformat() if r.training_date else None,
                    "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
                    "trainer": r.trainer,
                    "score": r.score,
                    "is_passed": r.is_passed,
                    "certificate_issued": r.certificate_issued
                }
                for r in records
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching training records: {str(e)}")
        return {"success": False, "error": str(e), "records": []}


@router.get("/records/user/{user_id}")
def get_user_training_records(user_id: int, db: Session = Depends(get_db)):
    """Get training records for specific user - PUBLIC"""
    try:
        records = db.query(TrainingRecord).filter(TrainingRecord.user_id == user_id).all()
        return {
            "success": True,
            "user_id": user_id,
            "count": len(records),
            "records": [
                {
                    "id": r.id,
                    "module_id": r.module_id,
                    "training_date": r.training_date.isoformat() if r.training_date else None,
                    "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
                    "trainer": r.trainer,
                    "score": r.score,
                    "is_passed": r.is_passed,
                    "certificate_issued": r.certificate_issued
                }
                for r in records
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching user training records: {str(e)}")
        return {"success": False, "error": str(e), "records": []}


@router.post("/records")
def create_training_record(data: TrainingRecordCreate, db: Session = Depends(get_db)):
    """Create a new training record - PUBLIC"""
    try:
        record = TrainingRecord(**data.dict())
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "success": True,
            "message": "Training record created successfully",
            "record": {
                "id": record.id,
                "user_id": record.user_id,
                "module_id": record.module_id,
                "training_date": record.training_date.isoformat() if record.training_date else None,
                "is_passed": record.is_passed
            }
        }
    except Exception as e:
        logger.error(f"Error creating training record: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/records/{record_id}")
def update_training_record(record_id: int, data: TrainingRecordUpdate, db: Session = Depends(get_db)):
    """Update training record - PUBLIC"""
    try:
        record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Training record not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(record, key, value)
        
        db.commit()
        db.refresh(record)
        
        return {
            "success": True,
            "message": "Training record updated successfully",
            "record": {
                "id": record.id,
                "user_id": record.user_id,
                "module_id": record.module_id,
                "training_date": record.training_date.isoformat() if record.training_date else None,
                "is_passed": record.is_passed
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating training record: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/{record_id}")
def delete_training_record(record_id: int, db: Session = Depends(get_db)):
    """Delete training record - PUBLIC"""
    try:
        record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Training record not found")
        
        db.delete(record)
        db.commit()
        
        return {"success": True, "message": "Training record deleted successfully", "id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting training record: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/all")
def delete_all_training_records(db: Session = Depends(get_db)):
    """Delete ALL training records - PUBLIC"""
    try:
        count = db.query(TrainingRecord).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} training records", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting all training records: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))