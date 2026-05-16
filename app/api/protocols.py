from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..database import get_db
from ..models.validation_protocol import ValidationProtocol, ProtocolExecutionResult
from ..models.equipment import Equipment
from ..models.product import Product
from ..services.protocol_service import ProtocolService
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Validation Protocols"])

class CreateProtocolRequest(BaseModel):
    equipment_id: int
    previous_product_id: int
    next_product_id: int
    cleaning_procedure_id: str
    prepared_by: str

class ExecuteProtocolRequest(BaseModel):
    protocol_id: int
    execution_number: int
    visual_result: str
    chemical_result_ppm: float
    microbiological_result: Optional[float] = None
    deviations: Optional[str] = None
    investigator: str


@router.post("/create")
def create_protocol(request: CreateProtocolRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating protocol for equipment {request.equipment_id}")
        
        equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
        if not equipment:
            logger.error(f"Equipment {request.equipment_id} not found")
            raise HTTPException(status_code=404, detail=f"Equipment {request.equipment_id} not found")
        
        previous = db.query(Product).filter(Product.id == request.previous_product_id).first()
        if not previous:
            logger.error(f"Previous product {request.previous_product_id} not found")
            raise HTTPException(status_code=404, detail=f"Previous product {request.previous_product_id} not found")
        
        next_product = db.query(Product).filter(Product.id == request.next_product_id).first()
        if not next_product:
            logger.error(f"Next product {request.next_product_id} not found")
            raise HTTPException(status_code=404, detail=f"Next product {request.next_product_id} not found")
        
        protocol = ProtocolService.create_protocol(
            db,
            request.equipment_id,
            request.previous_product_id,
            request.next_product_id,
            request.cleaning_procedure_id,
            request.prepared_by
        )
        
        logger.info(f"Protocol created successfully with ID {protocol.id}")
        
        return {
            "id": protocol.id,
            "protocol_number": protocol.protocol_number,
            "title": protocol.title,
            "status": protocol.status,
            "message": "Protocol created successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Protocol creation error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create protocol: {str(e)}")


@router.get("/{protocol_id}")
def get_protocol(protocol_id: int, db: Session = Depends(get_db)):
    try:
        protocol = db.query(ValidationProtocol).filter(ValidationProtocol.id == protocol_id).first()
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")
        return protocol
    except Exception as e:
        logger.error(f"Get protocol error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get protocol: {str(e)}")


@router.get("/{protocol_id}/pdf")
def download_protocol_pdf(protocol_id: int, db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    
    try:
        protocol = db.query(ValidationProtocol).filter(ValidationProtocol.id == protocol_id).first()
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        equipment = db.query(Equipment).filter(Equipment.id == protocol.equipment_id).first()
        if not equipment:
            raise HTTPException(status_code=400, detail=f"Equipment not found for protocol {protocol_id}")
        
        previous = db.query(Product).filter(Product.id == protocol.previous_product_id).first()
        if not previous:
            raise HTTPException(status_code=400, detail=f"Previous product not found for protocol {protocol_id}")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30, textColor=colors.HexColor('#1a472a'))
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=12, spaceAfter=12, textColor=colors.HexColor('#2d6a4f'))
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10)
        
        story = []
        
        story.append(Paragraph(f"Cleaning Validation Protocol", title_style))
        story.append(Paragraph(f"Protocol Number: {protocol.protocol_number}", normal_style))
        story.append(Paragraph(f"Version: {protocol.version}", normal_style))
        story.append(Paragraph(f"Status: {protocol.status}", normal_style))
        story.append(Spacer(1, 20))
        
        approval_data = [
            ["Prepared By:", protocol.prepared_by or "Not specified", "Date:", protocol.prepared_date.strftime('%Y-%m-%d') if protocol.prepared_date else "Not specified"],
            ["Reviewed By:", protocol.reviewed_by or "Pending", "Date:", protocol.reviewed_date.strftime('%Y-%m-%d') if protocol.reviewed_date else "Pending"],
            ["Approved By:", protocol.approved_by or "Pending", "Date:", protocol.approved_date.strftime('%Y-%m-%d') if protocol.approved_date else "Pending"],
        ]
        approval_table = Table(approval_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
        approval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(approval_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("1.0 BACKGROUND", heading_style))
        story.append(Paragraph(protocol.background or "Not specified", normal_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("2.0 PURPOSE", heading_style))
        story.append(Paragraph(protocol.purpose or "Not specified", normal_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("3.0 SCOPE", heading_style))
        story.append(Paragraph(protocol.scope or "Not specified", normal_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("4.0 EQUIPMENT INFORMATION", heading_style))
        equipment_data = [
            ["Equipment ID", "Cleaning Procedure", "Visual Acceptance"],
            [equipment.name or "N/A", protocol.cleaning_procedure_id or "N/A", protocol.visual_acceptance],
        ]
        equipment_table = Table(equipment_data, colWidths=[2*inch, 2*inch, 3*inch])
        equipment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(equipment_table)
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("5.0 ACCEPTANCE CRITERIA", heading_style))
        criteria_data = [
            ["Parameter", "Acceptance Criteria"],
            ["Visual Inspection", protocol.visual_acceptance],
            ["Chemical Residue", f"≤ {protocol.chemical_acceptance_ppm} ppm" if protocol.chemical_acceptance_ppm else "Not specified"],
            ["Microbiological", f"≤ {protocol.microbiological_acceptance} CFU/dm²" if protocol.microbiological_acceptance else "Not specified"],
        ]
        criteria_table = Table(criteria_data, colWidths=[2.5*inch, 4.5*inch])
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(criteria_table)
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("6.0 HOLD TIMES", heading_style))
        hold_data = [
            ["Parameter", "Validated Time"],
            ["Dirty Hold Time (DHT)", f"{protocol.dirty_hold_time_hours} hours" if protocol.dirty_hold_time_hours else "Not specified"],
            ["Clean Hold Time (CHT)", f"{protocol.clean_hold_time_hours} hours" if protocol.clean_hold_time_hours else "Not specified"],
        ]
        hold_table = Table(hold_data, colWidths=[2.5*inch, 4.5*inch])
        hold_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(hold_table)
        
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=validation_protocol_{protocol.protocol_number}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
    except Exception as e:
        logger.error(f"PDF generation error for protocol {protocol_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/execute")
def execute_protocol(request: ExecuteProtocolRequest, db: Session = Depends(get_db)):
    try:
        protocol = db.query(ValidationProtocol).filter(ValidationProtocol.id == request.protocol_id).first()
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        chemical_pass = request.chemical_result_ppm <= (protocol.chemical_acceptance_ppm or 999999)
        visual_pass = request.visual_result == "PASS"
        
        microbiological_pass = True
        if protocol.microbiological_acceptance and request.microbiological_result is not None:
            microbiological_pass = request.microbiological_result <= protocol.microbiological_acceptance
        elif protocol.microbiological_acceptance and request.microbiological_result is None:
            microbiological_pass = False
        
        overall = "PASS" if (visual_pass and chemical_pass and microbiological_pass) else "FAIL"
        
        result = ProtocolExecutionResult(
            protocol_id=request.protocol_id,
            execution_number=request.execution_number,
            execution_date=datetime.now(),
            visual_result=request.visual_result,
            chemical_result_ppm=request.chemical_result_ppm,
            microbiological_result=request.microbiological_result,
            overall_result=overall,
            deviations=request.deviations,
            investigator=request.investigator
        )
        
        db.add(result)
        
        existing_results = db.query(ProtocolExecutionResult).filter(
            ProtocolExecutionResult.protocol_id == request.protocol_id
        ).count()
        
        if existing_results + 1 >= 3:
            protocol.status = "EXECUTED"
            all_results = db.query(ProtocolExecutionResult).filter(
                ProtocolExecutionResult.protocol_id == request.protocol_id
            ).all()
            all_passed = all(r.overall_result == "PASS" for r in all_results) and overall == "PASS"
            if all_passed:
                protocol.status = "APPROVED"
        
        db.commit()
        
        return {
            "execution_result": {
                "id": result.id,
                "execution_number": result.execution_number,
                "overall_result": result.overall_result,
                "execution_date": result.execution_date.isoformat()
            },
            "protocol_status": protocol.status,
            "replicates_completed": existing_results + 1,
            "replicates_required": 3,
            "validation_complete": protocol.status == "APPROVED"
        }
        
    except Exception as e:
        logger.error(f"Execute protocol error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute protocol: {str(e)}")


@router.get("/{protocol_id}/results")
def get_protocol_results(protocol_id: int, db: Session = Depends(get_db)):
    try:
        protocol = db.query(ValidationProtocol).filter(ValidationProtocol.id == protocol_id).first()
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")
        results = db.query(ProtocolExecutionResult).filter(
            ProtocolExecutionResult.protocol_id == protocol_id
        ).order_by(ProtocolExecutionResult.execution_number).all()
        return {
            "protocol": {
                "id": protocol.id,
                "protocol_number": protocol.protocol_number,
                "status": protocol.status
            },
            "executions": [
                {
                    "execution_number": r.execution_number,
                    "execution_date": r.execution_date.isoformat(),
                    "visual_result": r.visual_result,
                    "chemical_result_ppm": r.chemical_result_ppm,
                    "microbiological_result": r.microbiological_result,
                    "overall_result": r.overall_result,
                    "deviations": r.deviations,
                    "investigator": r.investigator
                }
                for r in results
            ],
            "validation_passed": protocol.status == "APPROVED"
        }
    except Exception as e:
        logger.error(f"Get protocol results error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


# Add missing import at the top
import traceback