from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db
from ..models.product import Product
from ..models.equipment import Equipment
from ..models.session import ValidationSession
from ..models.audit_log import AuditLog
from .auth import get_current_user
from ..models.user import User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get dashboard statistics - FIXED"""
    try:
        # Simple counts that should always work
        products_count = db.query(Product).count()
        equipment_count = db.query(Equipment).count()
        active_sessions = db.query(ValidationSession).filter(
            ValidationSession.status.in_(["DRAFT", "IN_PROGRESS"])
        ).count()
        
        # Completed sessions and pass rate
        completed_sessions = db.query(ValidationSession).filter(
            ValidationSession.status == "COMPLETED"
        ).all()
        
        passed_sessions = 0
        for s in completed_sessions:
            # Check if swab results exist and are acceptable
            from ..models.swab_result import SwabResult
            swab_results = db.query(SwabResult).filter(SwabResult.session_id == s.id).all()
            if swab_results:
                all_passed = all(r.result_ppm <= (s.swab_limit_ppm or 999999) for r in swab_results)
                if all_passed:
                    passed_sessions += 1
            elif s.swab_limit_ppm and s.swab_limit_ppm > 0:
                passed_sessions += 1
        
        total_completed = len(completed_sessions)
        pass_rate = round((passed_sessions / total_completed) * 100) if total_completed > 0 else 0
        
        return {
            "success": True,
            "data": {
                "products": products_count,
                "equipment": equipment_count,
                "active_sessions": active_sessions,
                "pass_rate": pass_rate,
                "total_sessions": total_completed,
                "trends": {
                    "products": "0",
                    "equipment": "0",
                    "sessions": "0",
                    "pass_rate": "0%"
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
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get recent activity logs - FIXED"""
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