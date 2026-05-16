from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ValidationSession
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.session_equipment import SessionEquipment
from ..models.product import Product
from ..models.equipment import Equipment
from ..services.report import ReportService
from .auth import get_current_user
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

# Helper function to safely get value
def safe_value(value, default=0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default='N/A'):
    if value is None:
        return default
    return str(value)


@router.get("/{session_id}/pdf")
def generate_report(
    session_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate PDF report for validation session"""
    try:
        logger.info(f"Generating PDF report for session {session_id}")
        
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"Session found: {session.session_code}")
        
        swab_results = db.query(SwabResult).filter(SwabResult.session_id == session_id).all()
        logger.info(f"Found {len(swab_results)} swab results")
        
        rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session_id).all()
        logger.info(f"Found {len(rinse_results)} rinse results")
        
        session_equipment = db.query(SessionEquipment).filter(SessionEquipment.session_id == session_id).all()
        equipment_list = []
        for se in session_equipment:
            if se.equipment:
                equipment_list.append(se.equipment)
        logger.info(f"Found {len(equipment_list)} equipment items")
        
        maco_data = {
            "10ppm": safe_value(session.maco_10ppm, 0),
            "tdd": safe_value(session.maco_tdd, 0),
            "ade_pde": safe_value(session.maco_ade_pde, 0),
            "lowest": safe_value(session.lowest_maco, 0)
        }
        logger.info(f"MACO data: {maco_data}")
        
        pdf_content = ReportService.generate_validation_report(
            session, swab_results, rinse_results, maco_data, equipment_list
        )
        
        if not pdf_content:
            logger.error("PDF generation returned empty content")
            raise HTTPException(status_code=500, detail="PDF generation failed - empty content")
        
        logger.info(f"PDF generated successfully for session {session_id}")
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=validation_report_{session.session_code}.pdf",
                "Content-Length": str(len(pdf_content)),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed for session {session_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{session_id}/json")
def export_json(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export validation data as JSON"""
    try:
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        swab_results = db.query(SwabResult).filter(SwabResult.session_id == session_id).all()
        rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session_id).all()
        
        data = {
            "session": {
                "id": session.id,
                "session_code": safe_str(session.session_code),
                "status": safe_str(session.status),
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "extra_area_percentage": safe_value(session.extra_area_percentage, 0),
                "total_surface_area": safe_value(session.total_surface_area, 0)
            },
            "previous_product": None,
            "next_product": None,
            "maco_calculations": {
                "method_10ppm": safe_value(session.maco_10ppm, 0),
                "method_tdd": safe_value(session.maco_tdd, 0),
                "method_ade_pde": safe_value(session.maco_ade_pde, 0),
                "lowest_maco": safe_value(session.lowest_maco, 0)
            },
            "limits": {
                "swab_limit_mg": safe_value(session.swab_limit_mg, 0),
                "swab_limit_ppm": safe_value(session.swab_limit_ppm, 0),
                "rinse_limit_mg": safe_value(session.rinse_limit_mg, 0),
                "rinse_limit_ppm": safe_value(session.rinse_limit_ppm, 0)
            },
            "swab_results": [
                {
                    "location_name": safe_str(r.location_name),
                    "absorbance_sample": safe_value(r.absorbance_sample, 0),
                    "absorbance_std": safe_value(r.absorbance_std, 0),
                    "result_mg_ml": safe_value(r.result_mg_ml, 0),
                    "result_ppm": safe_value(r.result_ppm, 0),
                    "reported": safe_str(r.reported, "0")
                }
                for r in swab_results
            ],
            "rinse_results": [
                {
                    "equipment_name": safe_str(r.equipment_name),
                    "actual_rinse_volume": safe_value(r.actual_rinse_volume, 0),
                    "absorbance_sample": safe_value(r.absorbance_sample, 0),
                    "absorbance_std": safe_value(r.absorbance_std, 0),
                    "result_mg_ml": safe_value(r.result_mg_ml, 0),
                    "result_ppm": safe_value(r.result_ppm, 0),
                    "reported": safe_str(r.reported, "0")
                }
                for r in rinse_results
            ]
        }
        
        if session.previous_product:
            data["previous_product"] = {
                "id": session.previous_product.id,
                "name": safe_str(session.previous_product.name),
                "min_batch_size": safe_value(session.previous_product.min_batch_size, 0),
                "max_batch_size": safe_value(session.previous_product.max_batch_size, 0),
                "ade_pde": safe_value(session.previous_product.ade_pde, 0)
            }
        
        if session.next_product:
            data["next_product"] = {
                "id": session.next_product.id,
                "name": safe_str(session.next_product.name),
                "min_batch_size": safe_value(session.next_product.min_batch_size, 0),
                "max_batch_size": safe_value(session.next_product.max_batch_size, 0),
                "solubility": safe_str(session.next_product.solubility)
            }
        
        return JSONResponse(
            content=data,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON export failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JSON export failed: {str(e)}")


@router.get("/{session_id}/excel")
def export_excel(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export validation data as Excel"""
    try:
        from ..utils.excel_export import export_results_to_excel
        
        session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        buffer = export_results_to_excel(db, session_id)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=validation_data_{session.session_code}.xlsx",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel export failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")


# OPTIONS handler for CORS preflight requests
@router.options("/{session_id}/pdf")
@router.options("/{session_id}/json")
@router.options("/{session_id}/excel")
def options_handler():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600"
        }
    )