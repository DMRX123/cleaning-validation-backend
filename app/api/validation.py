from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ValidationSession
from ..models.standard_prep import StandardPrep
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.equipment import Equipment
from ..models.product import Product
from ..services.standard import StandardService
from ..services.swab import SwabService
from ..services.rinse import RinseService
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionCreate(BaseModel):
    previous_product_id: int
    next_product_id: int
    extra_area_percentage: float = 0


class SessionUpdate(BaseModel):
    step: Optional[int] = None
    previous_product_id: Optional[int] = None
    next_product_id: Optional[int] = None
    extra_area_percentage: Optional[float] = None
    total_surface_area: Optional[float] = None
    maco_10ppm: Optional[float] = None
    maco_tdd: Optional[float] = None
    maco_ade_pde: Optional[float] = None
    lowest_maco: Optional[float] = None
    swab_limit_mg: Optional[float] = None
    swab_limit_ppm: Optional[float] = None
    rinse_limit_mg: Optional[float] = None
    rinse_limit_ppm: Optional[float] = None
    status: Optional[str] = None
    process_id: Optional[int] = None


class StandardPrepCreate(BaseModel):
    session_id: int
    wt_of_std: float
    first_dilution: float
    second_dilution: float
    third_dilution: float
    fourth_dilution: float
    fifth_dilution: float
    potency: float


class SwabResultCreate(BaseModel):
    session_id: int
    location_name: str
    absorbance_sample: float
    absorbance_std: float


class RinseResultCreate(BaseModel):
    session_id: int
    equipment_name: str
    actual_rinse_volume: float
    absorbance_sample: float
    absorbance_std: float


# ============================================
# UPDATE ENDPOINTS FOR SWAB, RINSE, STANDARD PREP
# ============================================

class SwabResultUpdate(BaseModel):
    location_name: Optional[str] = None
    absorbance_sample: Optional[float] = None
    absorbance_std: Optional[float] = None


class RinseResultUpdate(BaseModel):
    equipment_name: Optional[str] = None
    actual_rinse_volume: Optional[float] = None
    absorbance_sample: Optional[float] = None
    absorbance_std: Optional[float] = None


class StandardPrepUpdate(BaseModel):
    wt_of_std: Optional[float] = None
    first_dilution: Optional[float] = None
    second_dilution: Optional[float] = None
    third_dilution: Optional[float] = None
    fourth_dilution: Optional[float] = None
    fifth_dilution: Optional[float] = None
    potency: Optional[float] = None


@router.put("/swab-result/{result_id}")
def update_swab_result(result_id: int, data: SwabResultUpdate, db: Session = Depends(get_db)):
    """Update swab result by ID - PUBLIC"""
    try:
        result = db.query(SwabResult).filter(SwabResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Swab result not found")
        
        session = db.query(ValidationSession).filter(ValidationSession.id == result.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        prep = db.query(StandardPrep).filter(StandardPrep.session_id == result.session_id).first()
        
        update_data = data.dict(exclude_unset=True)
        
        # If absorbance values changed, recalculate result
        if 'absorbance_sample' in update_data or 'absorbance_std' in update_data:
            sample = update_data.get('absorbance_sample', result.absorbance_sample)
            std = update_data.get('absorbance_std', result.absorbance_std)
            
            if prep:
                product = session.next_product
                recovery = product.swab_recovery if product else 70
                loq = product.loq if product else 0.5
                swab_dilution = product.swab_dilution if product else 20
                
                calc_result = SwabService.calculate_result(
                    sample, std, prep.dilution_factor, swab_dilution, recovery, loq
                )
                
                result.result_mg_ml = calc_result["mg_ml"]
                result.result_ppm = calc_result["ppm_numeric"]
                result.reported = calc_result["reported"]
                result.below_loq = 1 if calc_result["below_loq"] else 0
        
        for key, value in update_data.items():
            if hasattr(result, key) and value is not None:
                setattr(result, key, value)
        
        db.commit()
        db.refresh(result)
        
        return {
            "success": True,
            "message": "Swab result updated successfully",
            "data": {
                "id": result.id,
                "location_name": result.location_name,
                "result_ppm": result.result_ppm,
                "reported": result.reported
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update swab result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rinse-result/{result_id}")
def update_rinse_result(result_id: int, data: RinseResultUpdate, db: Session = Depends(get_db)):
    """Update rinse result by ID - PUBLIC"""
    try:
        result = db.query(RinseResult).filter(RinseResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Rinse result not found")
        
        session = db.query(ValidationSession).filter(ValidationSession.id == result.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        prep = db.query(StandardPrep).filter(StandardPrep.session_id == result.session_id).first()
        
        update_data = data.dict(exclude_unset=True)
        
        # If absorbance values changed, recalculate result
        if 'absorbance_sample' in update_data or 'absorbance_std' in update_data:
            sample = update_data.get('absorbance_sample', result.absorbance_sample)
            std = update_data.get('absorbance_std', result.absorbance_std)
            
            if prep:
                product = session.next_product
                recovery = product.swab_recovery if product else 70
                loq = product.loq if product else 0.5
                
                calc_result = SwabService.calculate_result(
                    sample, std, prep.dilution_factor, 1, recovery, loq
                )
                
                result.result_mg_ml = calc_result["mg_ml"]
                result.result_ppm = calc_result["ppm_numeric"]
                result.reported = calc_result["reported"]
        
        for key, value in update_data.items():
            if hasattr(result, key) and value is not None:
                setattr(result, key, value)
        
        db.commit()
        db.refresh(result)
        
        return {
            "success": True,
            "message": "Rinse result updated successfully",
            "data": {
                "id": result.id,
                "equipment_name": result.equipment_name,
                "result_ppm": result.result_ppm,
                "reported": result.reported
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update rinse result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/standard-prep/{prep_id}")
def update_standard_prep(prep_id: int, data: StandardPrepUpdate, db: Session = Depends(get_db)):
    """Update standard preparation by ID - PUBLIC"""
    try:
        prep = db.query(StandardPrep).filter(StandardPrep.id == prep_id).first()
        if not prep:
            raise HTTPException(status_code=404, detail="Standard preparation not found")
        
        update_data = data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            if hasattr(prep, key) and value is not None:
                setattr(prep, key, value)
        
        # Recalculate dilution factor
        factor = StandardService.calculate_dilution_factor(
            prep.wt_of_std, prep.first_dilution, prep.second_dilution,
            prep.third_dilution, prep.fourth_dilution, prep.fifth_dilution,
            prep.potency
        )
        prep.dilution_factor = factor
        
        db.commit()
        db.refresh(prep)
        
        return {
            "success": True,
            "message": "Standard preparation updated successfully",
            "data": {
                "id": prep.id,
                "dilution_factor": prep.dilution_factor
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update standard prep error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SESSION CRUD - PUBLIC
# ============================================

@router.post("/session")
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new validation session - PUBLIC"""
    try:
        previous_product = db.query(Product).filter(Product.id == data.previous_product_id).first()
        next_product = db.query(Product).filter(Product.id == data.next_product_id).first()
        
        if not previous_product:
            raise HTTPException(status_code=404, detail=f"Previous product with ID {data.previous_product_id} not found")
        if not next_product:
            raise HTTPException(status_code=404, detail=f"Next product with ID {data.next_product_id} not found")
        
        session_code = f"VAL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        equipment_list = db.query(Equipment).filter(Equipment.plant == previous_product.plant).limit(5).all()
        total_surface_area = sum(eq.surface_area for eq in equipment_list) if equipment_list else 100.0
        
        if data.extra_area_percentage > 0:
            total_surface_area = total_surface_area * (1 + data.extra_area_percentage / 100)
        
        new_session = ValidationSession(
            session_code=session_code,
            previous_product_id=data.previous_product_id,
            next_product_id=data.next_product_id,
            extra_area_percentage=data.extra_area_percentage or 0,
            total_surface_area=total_surface_area,
            status="DRAFT"
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return {
            "success": True,
            "id": new_session.id,
            "session_code": new_session.session_code,
            "previous_product_id": new_session.previous_product_id,
            "next_product_id": new_session.next_product_id,
            "extra_area_percentage": new_session.extra_area_percentage,
            "total_surface_area": new_session.total_surface_area,
            "status": new_session.status,
            "created_at": new_session.created_at.isoformat() if new_session.created_at else None,
            "message": "Session created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.put("/session/{session_id}")
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    """Update validation session - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        update_data = data.model_dump(exclude_unset=True)
        
        if 'data' in update_data:
            update_data.pop('data')
        
        for key, value in update_data.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        
        if data.step and data.step > 1 and session.status == "DRAFT":
            session.status = "IN_PROGRESS"
        
        db.commit()
        db.refresh(session)
        
        return {
            "success": True,
            "id": session.id,
            "session_code": session.session_code,
            "status": session.status,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "message": "Session updated successfully"
        }
    except Exception as e:
        logger.error(f"Session update error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get validation session by ID - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "data": session}
    except Exception as e:
        logger.error(f"Get session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete validation session and all related data - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete related data
        db.query(StandardPrep).filter(StandardPrep.session_id == session_id).delete()
        db.query(SwabResult).filter(SwabResult.session_id == session_id).delete()
        db.query(RinseResult).filter(RinseResult.session_id == session_id).delete()
        
        db.delete(session)
        db.commit()
        
        return {"success": True, "message": "Session deleted successfully", "id": session_id}
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/history")
def get_validation_history(db: Session = Depends(get_db)):
    """Get all validation sessions for history/chart - PUBLIC"""
    try:
        sessions = db.query(ValidationSession).order_by(ValidationSession.created_at.desc()).all()
        return {
            "success": True,
            "count": len(sessions),
            "sessions": [
                {
                    "id": s.id,
                    "session_code": s.session_code,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "previous_product_name": s.previous_product.name if s.previous_product else None,
                    "next_product_name": s.next_product.name if s.next_product else None
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Get history error: {str(e)}")
        return {"success": False, "error": str(e), "sessions": []}


@router.delete("/all")
def delete_all_sessions(db: Session = Depends(get_db)):
    """Delete ALL validation sessions - PUBLIC"""
    try:
        db.query(StandardPrep).delete()
        db.query(SwabResult).delete()
        db.query(RinseResult).delete()
        count = db.query(ValidationSession).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} sessions", "deleted_count": count}
    except Exception as e:
        logger.error(f"Delete all sessions error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STANDARD PREP, SWAB, RINSE - PUBLIC
# ============================================

@router.post("/standard-prep")
def create_standard_prep(data: StandardPrepCreate, db: Session = Depends(get_db)):
    """Create standard preparation - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session with ID {data.session_id} not found")
        
        new_prep = StandardPrep(**data.model_dump())
        factor = StandardService.calculate_dilution_factor(
            data.wt_of_std, data.first_dilution, data.second_dilution,
            data.third_dilution, data.fourth_dilution, data.fifth_dilution,
            data.potency
        )
        new_prep.dilution_factor = factor
        db.add(new_prep)
        db.commit()
        db.refresh(new_prep)
        
        return {
            "success": True,
            "id": new_prep.id,
            "session_id": new_prep.session_id,
            "dilution_factor": new_prep.dilution_factor,
            "message": "Standard preparation created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Standard prep error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/standard-prep/{prep_id}")
def delete_standard_prep(prep_id: int, db: Session = Depends(get_db)):
    """Delete standard preparation - PUBLIC"""
    try:
        prep = db.query(StandardPrep).filter(StandardPrep.id == prep_id).first()
        if not prep:
            raise HTTPException(status_code=404, detail="Standard preparation not found")
        
        db.delete(prep)
        db.commit()
        return {"success": True, "message": "Standard preparation deleted", "id": prep_id}
    except Exception as e:
        logger.error(f"Delete standard prep error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/swab-result")
def create_swab_result(data: SwabResultCreate, db: Session = Depends(get_db)):
    """Create swab result - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
        prep = db.query(StandardPrep).filter(StandardPrep.session_id == data.session_id).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if not prep:
            raise HTTPException(status_code=404, detail="Standard preparation not found for this session")
        
        recovery = session.next_product.swab_recovery if session.next_product else 100
        loq = session.next_product.loq if session.next_product else 0
        swab_dilution = session.next_product.swab_dilution if session.next_product else 20
        
        result = SwabService.calculate_result(
            data.absorbance_sample, data.absorbance_std,
            prep.dilution_factor, swab_dilution,
            recovery, loq
        )
        
        new_result = SwabResult(
            session_id=data.session_id,
            location_name=data.location_name,
            absorbance_sample=data.absorbance_sample,
            absorbance_std=data.absorbance_std,
            result_mg_ml=result["mg_ml"],
            result_ppm=result["ppm_numeric"],
            reported=result["reported"],
            below_loq=1 if result["below_loq"] else 0
        )
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        
        return {
            "success": True,
            "id": new_result.id,
            "session_id": new_result.session_id,
            "location_name": new_result.location_name,
            "result_mg_ml": new_result.result_mg_ml,
            "result_ppm": new_result.result_ppm,
            "reported": new_result.reported,
            "below_loq": result["below_loq"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Swab result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/swab-result/{result_id}")
def delete_swab_result(result_id: int, db: Session = Depends(get_db)):
    """Delete swab result - PUBLIC"""
    try:
        result = db.query(SwabResult).filter(SwabResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Swab result not found")
        
        db.delete(result)
        db.commit()
        return {"success": True, "message": "Swab result deleted", "id": result_id}
    except Exception as e:
        logger.error(f"Delete swab result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rinse-result")
def create_rinse_result(data: RinseResultCreate, db: Session = Depends(get_db)):
    """Create rinse result - PUBLIC"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == data.session_id).first()
        prep = db.query(StandardPrep).filter(StandardPrep.session_id == data.session_id).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if not prep:
            raise HTTPException(status_code=404, detail="Standard preparation not found for this session")
        
        recovery = session.next_product.swab_recovery if session.next_product else 100
        loq = session.next_product.loq if session.next_product else 0
        
        result = SwabService.calculate_result(
            data.absorbance_sample, data.absorbance_std,
            prep.dilution_factor, 1,
            recovery, loq
        )
        
        new_result = RinseResult(
            session_id=data.session_id,
            equipment_name=data.equipment_name,
            actual_rinse_volume=data.actual_rinse_volume,
            absorbance_sample=data.absorbance_sample,
            absorbance_std=data.absorbance_std,
            result_mg_ml=result["mg_ml"],
            result_ppm=result["ppm_numeric"],
            reported=result["reported"]
        )
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        
        return {
            "success": True,
            "id": new_result.id,
            "session_id": new_result.session_id,
            "equipment_name": new_result.equipment_name,
            "result_mg_ml": new_result.result_mg_ml,
            "result_ppm": new_result.result_ppm,
            "reported": new_result.reported,
            "below_loq": result["below_loq"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rinse result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rinse-result/{result_id}")
def delete_rinse_result(result_id: int, db: Session = Depends(get_db)):
    """Delete rinse result - PUBLIC"""
    try:
        result = db.query(RinseResult).filter(RinseResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Rinse result not found")
        
        db.delete(result)
        db.commit()
        return {"success": True, "message": "Rinse result deleted", "id": result_id}
    except Exception as e:
        logger.error(f"Delete rinse result error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))