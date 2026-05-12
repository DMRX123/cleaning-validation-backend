from sqlalchemy.orm import Session
from ..models.audit_log import AuditLog
import json
from datetime import datetime

class AuditService:
    """Log all user actions - System managed"""
    
    @staticmethod
    def log(db: Session, user_id: int, action: str, entity: str, 
            entity_id: int, old_values: dict = None, new_values: dict = None):
        """Create an audit log entry"""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str) if new_values else None,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        return log_entry
    
    @staticmethod
    def get_logs(db: Session, entity: str = None, entity_id: int = None, 
                 action: str = None, limit: int = 100, offset: int = 0):
        """Retrieve audit logs with filters"""
        query = db.query(AuditLog)
        
        if entity:
            query = query.filter(AuditLog.entity == entity)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if action:
            query = query.filter(AuditLog.action == action)
        
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_entity_history(db: Session, entity: str, entity_id: int) -> list:
        """Get complete history for a specific entity"""
        return AuditService.get_logs(db, entity=entity, entity_id=entity_id, limit=1000)
    
    @staticmethod
    def log_product_change(db: Session, user_id: int, product_id: int, 
                           old_values: dict, new_values: dict):
        """Log product creation/update/deletion"""
        action = "UPDATE"
        if not old_values:
            action = "CREATE"
        elif not new_values:
            action = "DELETE"
        
        return AuditService.log(db, user_id, action, "Product", product_id, old_values, new_values)
    
    @staticmethod
    def log_calculation(db: Session, user_id: int, session_id: int, 
                        calculation_type: str, result: dict):
        """Log calculation events (MACO, Swab, Rinse)"""
        return AuditService.log(
            db, user_id, "CALCULATE", calculation_type, session_id, 
            None, {"result": result}
        )