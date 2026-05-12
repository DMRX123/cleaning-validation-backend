from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ValidationSession
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..services.report import ReportService

router = APIRouter()

@router.get("/{session_id}/pdf")
def generate_report(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    swab_results = db.query(SwabResult).filter(SwabResult.session_id == session_id).all()
    rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session_id).all()
    
    maco_data = {
        "10ppm": session.maco_10ppm,
        "tdd": session.maco_tdd,
        "ade_pde": session.maco_ade_pde,
        "lowest": session.lowest_maco
    }
    
    pdf_content = ReportService.generate_validation_report(session, swab_results, rinse_results, maco_data)
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=validation_report_{session.session_code}.pdf"}
    )