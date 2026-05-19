"""
Dynamic Report Generator API - Past Tense Validation Report
Answers: "Humne KYA kiya, KYUN kiya, aur KYA results aaye"
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models.session import ValidationSession
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.validation_report import ValidationReport
from ..services.report_generator_service import ReportGeneratorService

# ONLY ONE ROUTER DEFINITION - NO DUPLICATE TAGS
router = APIRouter(prefix="/api/report", tags=["Report Generator"])


@router.post("/generate/{session_id}")
def generate_report(
    session_id: int,
    report_number: str = Body(...),
    prepared_by: str = Body(...),
    reviewed_by: Optional[str] = Body(None),
    approved_by: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Generate VALIDATION REPORT (Past Tense) from actual session results"""
    
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    swab_results = db.query(SwabResult).filter(SwabResult.session_id == session_id).all()
    rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session_id).all()
    
    total_swab = len(swab_results)
    passed_swab = sum(1 for r in swab_results if r.result_ppm and session.swab_limit_ppm and r.result_ppm <= session.swab_limit_ppm)
    total_rinse = len(rinse_results)
    passed_rinse = sum(1 for r in rinse_results if r.result_ppm and session.rinse_limit_ppm and r.result_ppm <= session.rinse_limit_ppm)
    overall_pass = (passed_swab == total_swab if total_swab > 0 else True) and \
                   (passed_rinse == total_rinse if total_rinse > 0 else True)
    
    # Check if report exists
    existing = db.query(ValidationReport).filter(
        ValidationReport.session_id == session_id,
        ValidationReport.report_number == report_number
    ).first()
    
    if existing:
        report = existing
        report.report_date = datetime.now()
        report.prepared_by = prepared_by
        report.reviewed_by = reviewed_by
        report.approved_by = approved_by
        report.total_swab_samples = total_swab
        report.total_rinse_samples = total_rinse
        report.passed_swab_samples = passed_swab
        report.passed_rinse_samples = passed_rinse
        report.overall_pass = overall_pass
        report.swab_results_summary = [
            {"location": r.location_name, "result_ppm": r.result_ppm, "limit_ppm": session.swab_limit_ppm, "passed": r.result_ppm <= session.swab_limit_ppm if session.swab_limit_ppm else False}
            for r in swab_results
        ]
        report.rinse_results_summary = [
            {"equipment": r.equipment_name, "result_ppm": r.result_ppm, "limit_ppm": session.rinse_limit_ppm, "passed": r.result_ppm <= session.rinse_limit_ppm if session.rinse_limit_ppm else False}
            for r in rinse_results
        ]
        report.conclusion = ReportGeneratorService.generate_conclusion(session, overall_pass, passed_swab, total_swab)
        report.status = "FINAL"
    else:
        report = ValidationReport(
            report_number=report_number,
            session_id=session_id,
            report_date=datetime.now(),
            prepared_by=prepared_by,
            reviewed_by=reviewed_by,
            approved_by=approved_by,
            total_swab_samples=total_swab,
            total_rinse_samples=total_rinse,
            passed_swab_samples=passed_swab,
            passed_rinse_samples=passed_rinse,
            overall_pass=overall_pass,
            swab_results_summary=[
                {"location": r.location_name, "result_ppm": r.result_ppm, "limit_ppm": session.swab_limit_ppm, "passed": r.result_ppm <= session.swab_limit_ppm if session.swab_limit_ppm else False}
                for r in swab_results
            ],
            rinse_results_summary=[
                {"equipment": r.equipment_name, "result_ppm": r.result_ppm, "limit_ppm": session.rinse_limit_ppm, "passed": r.result_ppm <= session.rinse_limit_ppm if session.rinse_limit_ppm else False}
                for r in rinse_results
            ],
            conclusion=ReportGeneratorService.generate_conclusion(session, overall_pass, passed_swab, total_swab),
            status="FINAL"
        )
        db.add(report)
    
    db.commit()
    db.refresh(report)
    
    pdf_bytes = ReportGeneratorService.generate_report(db, report.id)
    
    report.pdf_path = f"/generated_reports/{report_number}.pdf"
    db.commit()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=validation_report_{report_number}.pdf",
            "X-Report-ID": str(report.id),
            "X-Overall-Pass": str(overall_pass)
        }
    )


@router.get("/preview/{session_id}")
def preview_report(session_id: int, db: Session = Depends(get_db)):
    """Preview report data before generation"""
    
    session = db.query(ValidationSession).filter(ValidationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    swab_results = db.query(SwabResult).filter(SwabResult.session_id == session_id).all()
    rinse_results = db.query(RinseResult).filter(RinseResult.session_id == session_id).all()
    
    total_swab = len(swab_results)
    passed_swab = sum(1 for r in swab_results if r.result_ppm and session.swab_limit_ppm and r.result_ppm <= session.swab_limit_ppm)
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "session": {"id": session.id, "session_code": session.session_code, "status": session.status},
            "previous_product": {"name": session.previous_product.name if session.previous_product else None},
            "next_product": {"name": session.next_product.name if session.next_product else None},
            "maco_used": session.lowest_maco,
            "swab_limit_ppm": session.swab_limit_ppm,
            "rinse_limit_ppm": session.rinse_limit_ppm,
            "swab_results": [
                {"location": r.location_name, "result_ppm": r.result_ppm, "passed": r.result_ppm <= session.swab_limit_ppm if session.swab_limit_ppm else False}
                for r in swab_results
            ],
            "statistics": {
                "total_swab_samples": total_swab,
                "passed_swab_samples": passed_swab,
                "pass_rate": round((passed_swab / total_swab) * 100, 2) if total_swab > 0 else 0
            }
        }
    })


@router.get("/reports")
def get_all_reports(
    skip: int = 0,
    limit: int = 50,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all generated reports"""
    
    query = db.query(ValidationReport)
    if session_id:
        query = query.filter(ValidationReport.session_id == session_id)
    
    reports = query.order_by(ValidationReport.report_date.desc()).offset(skip).limit(limit).all()
    
    return JSONResponse(content={
        "success": True,
        "count": len(reports),
        "data": [
            {
                "id": r.id,
                "report_number": r.report_number,
                "session_id": r.session_id,
                "report_date": r.report_date.isoformat(),
                "overall_pass": r.overall_pass,
                "status": r.status,
                "pdf_path": r.pdf_path
            }
            for r in reports
        ]
    })


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get report details by ID"""
    
    report = db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "id": report.id,
            "report_number": report.report_number,
            "session_id": report.session_id,
            "report_date": report.report_date.isoformat(),
            "prepared_by": report.prepared_by,
            "total_swab_samples": report.total_swab_samples,
            "passed_swab_samples": report.passed_swab_samples,
            "overall_pass": report.overall_pass,
            "conclusion": report.conclusion,
            "status": report.status,
            "pdf_path": report.pdf_path
        }
    })


@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report"""
    
    report = db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db.delete(report)
    db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": f"Report deleted successfully"
    })


@router.delete("/reports/all")
def delete_all_reports(db: Session = Depends(get_db)):
    """Delete all reports"""
    
    count = db.query(ValidationReport).delete()
    db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": f"Deleted {count} reports",
        "deleted_count": count
    })


@router.put("/reports/{report_id}/approve")
def approve_report(report_id: int, approved_by: str = Body(...), db: Session = Depends(get_db)):
    """Approve a report"""
    
    report = db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = "APPROVED"
    report.approved_by = approved_by
    db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": f"Report approved by {approved_by}"
    })