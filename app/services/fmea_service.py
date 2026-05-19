from sqlalchemy.orm import Session
from ..models.fmea_risk import FMEARiskAssessment
from ..models.equipment import Equipment


class FMEAService:
    """Section 8.1 - FMEA risk assessment for sampling points"""
    
    @staticmethod
    def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
        """Calculate Risk Priority Number"""
        return severity * occurrence * detection
    
    @staticmethod
    def get_risk_level(rpn: int) -> str:
        """Determine risk level based on RPN"""
        if rpn < 70:
            return "Low"
        elif rpn <= 150:
            return "Medium"
        else:
            return "High"
    
    @staticmethod
    def create_fmea_record(db: Session, equipment_id: int, failure_mode: str,
                           severity: int, occurrence: int, detection: int,
                           location_description: str = None,
                           is_sampling_point: bool = False) -> FMEARiskAssessment:
        """Create FMEA risk assessment record"""
        
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise ValueError(f"Equipment with ID {equipment_id} not found")
        
        rpn = FMEAService.calculate_rpn(severity, occurrence, detection)
        risk_level = FMEAService.get_risk_level(rpn)
        
        fmea = FMEARiskAssessment(
            equipment_id=equipment_id,
            failure_mode=failure_mode,
            location_description=location_description,
            severity=severity,
            occurrence=occurrence,
            detection=detection,
            rpn=rpn,
            risk_level=risk_level,
            is_sampling_point=is_sampling_point
        )
        
        db.add(fmea)
        db.commit()
        db.refresh(fmea)
        return fmea
    
    @staticmethod
    def get_sampling_points(db: Session, equipment_id: int = None) -> list:
        """Get FMEA-based sampling points"""
        query = db.query(FMEARiskAssessment).filter(
            FMEARiskAssessment.is_sampling_point == True
        )
        if equipment_id:
            query = query.filter(FMEARiskAssessment.equipment_id == equipment_id)
        
        return query.all()
    
    @staticmethod
    def get_fmea_table(db: Session) -> list:
        """Get FMEA data for protocol table"""
        assessments = db.query(FMEARiskAssessment).all()
        
        return [
            {
                "equipment": a.equipment.name if a.equipment else "N/A",
                "failure_mode": a.failure_mode,
                "severity": a.severity,
                "occurrence": a.occurrence,
                "detection": a.detection,
                "rpn": a.rpn,
                "risk_level": a.risk_level,
                "sampling_point": "✅ Yes" if a.is_sampling_point else "❌ No"
            }
            for a in assessments
        ]