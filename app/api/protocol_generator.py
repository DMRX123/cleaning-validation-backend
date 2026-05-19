from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from ..database import get_db
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.protocol_template import CleaningValidationProtocol
from ..services.protocol_generator_service import ProtocolGeneratorService
from ..services.maco import MACOService
from ..services.worst_case_service import WorstCaseService

router = APIRouter(prefix="/api/protocol", tags=["Protocol Generator"])


@router.post("/generate")
def generate_protocol(
    product_id: int = Body(...),
    protocol_number: str = Body(...),
    revision: str = Body("R00"),
    prepared_by: str = Body(...),
    location: str = Body("Indore"),
    campaign_max_batches: int = Body(10),
    campaign_max_days: int = Body(30),
    dht_hours: float = Body(24.0),
    cht_days: int = Body(14),
    db: Session = Depends(get_db)
):
    """Generate complete validation protocol PDF - 50+ pages"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    existing = db.query(CleaningValidationProtocol).filter(
        CleaningValidationProtocol.protocol_number == protocol_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Protocol number already exists")
    
    protocol = CleaningValidationProtocol(
        protocol_number=protocol_number,
        revision=revision,
        product_id=product_id,
        date_of_issue=datetime.now(),
        location=location,
        manufacturing_block=product.plant,
        batch_size_range=f"{product.min_batch_size} ± {product.max_batch_size - product.min_batch_size} Kg",
        prepared_by=prepared_by,
        prepared_date=datetime.now(),
        campaign_max_batches=campaign_max_batches,
        campaign_max_days=campaign_max_days,
        dht_hours=dht_hours,
        cht_days=cht_days,
        status="DRAFT",
        created_by=prepared_by
    )
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    
    try:
        pdf_bytes = ProtocolGeneratorService.generate_protocol(db, protocol.id)
        
        protocol.pdf_generated_at = datetime.now()
        protocol.pdf_path = f"/generated_protocols/{protocol_number}.pdf"
        db.commit()
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=validation_protocol_{protocol_number}.pdf",
                "X-Protocol-ID": str(protocol.id)
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/preview")
def preview_protocol(
    product_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Preview protocol data before generation"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    equipment_list = db.query(Equipment).filter(Equipment.plant == product.plant).all()
    all_products = db.query(Product).filter(Product.plant == product.plant).all()
    worst_case = WorstCaseService.select_worst_case(all_products)
    maco_result = MACOService.calculate_all(worst_case, product) if worst_case else {}
    
    total_surface_area = sum(eq.surface_area for eq in equipment_list)
    swab_limit = (maco_result.get("lowest_maco", 0) * 0.01) / total_surface_area if total_surface_area > 0 else 0
    
    preview_data = {
        "product": {
            "id": product.id,
            "name": product.name,
            "product_code": product.product_code,
            "plant": product.plant,
            "batch_size_min": product.min_batch_size,
            "batch_size_max": product.max_batch_size,
            "ade_pde": product.ade_pde,
            "solubility": product.solubility
        },
        "equipment": [
            {
                "id": eq.id,
                "name": eq.name,
                "equipment_id": eq.equipment_id,
                "surface_area": eq.surface_area
            }
            for eq in equipment_list
        ],
        "total_surface_area": total_surface_area,
        "worst_case_product": {
            "name": worst_case.name if worst_case else None,
            "ade_pde": worst_case.ade_pde if worst_case else None
        },
        "maco_calculations": {
            "method_10ppm": maco_result.get("method_10ppm", 0),
            "method_tdd": maco_result.get("method_tdd", 0),
            "method_ade_pde": maco_result.get("method_ade_pde", 0),
            "lowest_maco": maco_result.get("lowest_maco", 0)
        },
        "swab_limit_mg": round(swab_limit, 6),
        "estimated_page_count": 50
    }
    
    return JSONResponse(content={"success": True, "data": preview_data})


@router.get("/protocols")
def get_all_protocols(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all generated protocols"""
    
    query = db.query(CleaningValidationProtocol)
    if status:
        query = query.filter(CleaningValidationProtocol.status == status)
    
    protocols = query.order_by(
        CleaningValidationProtocol.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return JSONResponse(content={
        "success": True,
        "count": len(protocols),
        "data": [
            {
                "id": p.id,
                "protocol_number": p.protocol_number,
                "revision": p.revision,
                "product_name": p.product.name if p.product else None,
                "date_of_issue": p.date_of_issue.isoformat() if p.date_of_issue else None,
                "status": p.status,
                "pdf_path": p.pdf_path
            }
            for p in protocols
        ]
    })


@router.get("/protocols/{protocol_id}")
def get_protocol(protocol_id: int, db: Session = Depends(get_db)):
    """Get protocol details by ID"""
    
    protocol = db.query(CleaningValidationProtocol).filter(
        CleaningValidationProtocol.id == protocol_id
    ).first()
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return JSONResponse(content={
        "success": True,
        "data": {
            "id": protocol.id,
            "protocol_number": protocol.protocol_number,
            "revision": protocol.revision,
            "product": {
                "id": protocol.product.id,
                "name": protocol.product.name
            } if protocol.product else None,
            "date_of_issue": protocol.date_of_issue.isoformat() if protocol.date_of_issue else None,
            "prepared_by": protocol.prepared_by,
            "status": protocol.status,
            "pdf_path": protocol.pdf_path,
            "campaign_max_batches": protocol.campaign_max_batches,
            "dht_hours": protocol.dht_hours,
            "cht_days": protocol.cht_days
        }
    })


@router.put("/protocols/{protocol_id}/status")
def update_protocol_status(
    protocol_id: int,
    status: str = Body(...),
    db: Session = Depends(get_db)
):
    """Update protocol status"""
    
    protocol = db.query(CleaningValidationProtocol).filter(
        CleaningValidationProtocol.id == protocol_id
    ).first()
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    valid_statuses = ["DRAFT", "ACTIVE", "ARCHIVED", "OBSOLETE"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    protocol.status = status
    db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": f"Protocol status updated to {status}"
    })


@router.delete("/protocols/{protocol_id}")
def delete_protocol(protocol_id: int, db: Session = Depends(get_db)):
    """Delete a protocol draft (only DRAFT status allowed)"""
    
    protocol = db.query(CleaningValidationProtocol).filter(
        CleaningValidationProtocol.id == protocol_id
    ).first()
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT protocols can be deleted")
    
    db.delete(protocol)
    db.commit()
    
    return JSONResponse(content={
        "success": True,
        "message": f"Protocol {protocol.protocol_number} deleted successfully"
    })