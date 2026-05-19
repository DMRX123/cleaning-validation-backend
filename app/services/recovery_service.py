from sqlalchemy.orm import Session
from datetime import datetime
from ..models.recovery_study import RecoveryStudy
from ..models.product import Product


class RecoveryService:
    """Section 8.3 - Recovery study management"""
    
    @staticmethod
    def create_recovery_study(db: Session, product_id: int, material_of_construction: str,
                              recovery_percent: float, study_date: datetime = None,
                              report_reference: str = None, notes: str = None) -> RecoveryStudy:
        """Create a new recovery study record"""
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Calculate correction factor
        correction_factor = 100 / recovery_percent if recovery_percent > 0 else 1.0
        
        recovery_study = RecoveryStudy(
            product_id=product_id,
            material_of_construction=material_of_construction,
            recovery_percent=recovery_percent,
            correction_factor=round(correction_factor, 3),
            study_date=study_date or datetime.now(),
            report_reference=report_reference,
            is_valid=True,
            valid_until=datetime(datetime.now().year + 5, 12, 31),
            notes=notes
        )
        
        db.add(recovery_study)
        db.commit()
        db.refresh(recovery_study)
        return recovery_study
    
    @staticmethod
    def get_recovery_by_moc(db: Session, material_of_construction: str) -> RecoveryStudy:
        """Get recovery study for specific material of construction"""
        return db.query(RecoveryStudy).filter(
            RecoveryStudy.material_of_construction == material_of_construction,
            RecoveryStudy.is_valid == True
        ).first()
    
    @staticmethod
    def apply_correction(measured_value: float, recovery_percent: float) -> float:
        """Apply recovery correction factor"""
        if recovery_percent <= 0:
            return measured_value
        return round(measured_value / (recovery_percent / 100), 6)
    
    @staticmethod
    def get_recovery_table(db: Session) -> list:
        """Get all recovery studies for protocol table"""
        studies = db.query(RecoveryStudy).filter(
            RecoveryStudy.is_valid == True
        ).all()
        
        return [
            {
                "material": s.material_of_construction,
                "recovery_percent": s.recovery_percent,
                "correction_factor": s.correction_factor,
                "acceptable": "✅ Yes" if s.recovery_percent >= 50 else "❌ No"
            }
            for s in studies
        ]