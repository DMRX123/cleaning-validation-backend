from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession
from ..models.audit_log import AuditLog
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics - PUBLIC"""
    try:
        products_count = db.query(Product).count()
        equipment_count = db.query(Equipment).count()
        active_sessions = db.query(ValidationSession).filter(
            ValidationSession.status.in_(["DRAFT", "IN_PROGRESS"])
        ).count()
        
        completed_sessions = db.query(ValidationSession).filter(
            ValidationSession.status == "COMPLETED"
        ).all()
        
        passed_sessions = 0
        for s in completed_sessions:
            swab_results = db.query(SwabResult).filter(SwabResult.session_id == s.id).all()
            rinse_results = db.query(RinseResult).filter(RinseResult.session_id == s.id).all()
            
            all_swab_pass = True
            limit_swab = s.swab_limit_ppm if s.swab_limit_ppm else float('inf')
            for r in swab_results:
                if r.result_ppm and r.result_ppm > limit_swab:
                    all_swab_pass = False
                    break
            
            all_rinse_pass = True
            limit_rinse = s.rinse_limit_ppm if s.rinse_limit_ppm else float('inf')
            for r in rinse_results:
                if r.result_ppm and r.result_ppm > limit_rinse:
                    all_rinse_pass = False
                    break
            
            if all_swab_pass and all_rinse_pass:
                passed_sessions += 1
        
        total_completed = len(completed_sessions)
        pass_rate = round((passed_sessions / total_completed) * 100) if total_completed > 0 else 0
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # FIXED: Product.created_at doesn't exist, using id-based recent count
        recent_products = db.query(Product).filter(
            Product.id.in_(
                db.query(Product.id).order_by(Product.id.desc()).limit(5)
            )
        ).count()
        
        recent_equipment = db.query(Equipment).filter(
            Equipment.id.in_(
                db.query(Equipment.id).order_by(Equipment.id.desc()).limit(5)
            )
        ).count()
        
        recent_sessions = db.query(ValidationSession).filter(
            ValidationSession.created_at >= thirty_days_ago
        ).count()
        
        return {
            "success": True,
            "data": {
                "products": products_count,
                "equipment": equipment_count,
                "active_sessions": active_sessions,
                "pass_rate": pass_rate,
                "total_sessions": total_completed,
                "trends": {
                    "products": f"+{recent_products}" if recent_products > 0 else "0",
                    "equipment": f"+{recent_equipment}" if recent_equipment > 0 else "0",
                    "sessions": f"+{recent_sessions}" if recent_sessions > 0 else "0",
                    "pass_rate": f"{pass_rate}%"
                }
            }
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "products": 0,
                "equipment": 0,
                "active_sessions": 0,
                "pass_rate": 0,
                "total_sessions": 0,
                "trends": {
                    "products": "0",
                    "equipment": "0",
                    "sessions": "0",
                    "pass_rate": "0%"
                }
            }
        }


@router.get("/recent-activity")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent activity logs - PUBLIC"""
    try:
        recent_audits = db.query(AuditLog).order_by(
            desc(AuditLog.created_at)
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": a.id,
                    "action": a.action,
                    "entity": a.entity,
                    "entity_id": a.entity_id,
                    "user_id": a.user_id,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in recent_audits
            ]
        }
    except Exception as e:
        logger.error(f"Recent activity error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get complete dashboard summary - PUBLIC"""
    try:
        stats = get_stats(db)
        recent = get_recent_activity(5, db)
        
        return {
            "success": True,
            "stats": stats.get("data", {}),
            "recent_activity": recent.get("data", []),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "stats": {},
            "recent_activity": []
        }


@router.get("/charts-data")
def get_charts_data(db: Session = Depends(get_db)):
    """Get data for dashboard charts - PUBLIC"""
    try:
        from sqlalchemy import extract
        
        status_counts = db.query(
            ValidationSession.status, 
            func.count(ValidationSession.id)
        ).group_by(ValidationSession.status).all()
        
        monthly_sessions = db.query(
            extract('year', ValidationSession.created_at).label('year'),
            extract('month', ValidationSession.created_at).label('month'),
            func.count(ValidationSession.id)
        ).group_by('year', 'month').order_by('year', 'month').limit(12).all()
        
        products_by_plant = db.query(
            Product.plant,
            func.count(Product.id)
        ).group_by(Product.plant).all()
        
        return {
            "success": True,
            "data": {
                "sessions_by_status": [{"status": s[0] or "UNKNOWN", "count": s[1]} for s in status_counts],
                "monthly_sessions": [{"month": f"{int(m[1])}/{int(m[0])}", "count": m[2]} for m in monthly_sessions if m[0] and m[1]],
                "products_by_plant": [{"plant": p[0] or "Unknown", "count": p[1]} for p in products_by_plant]
            }
        }
    except Exception as e:
        logger.error(f"Charts data error: {str(e)}")
        return {"success": False, "error": str(e), "data": {}}