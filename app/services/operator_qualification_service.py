from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models.operator_qualification import OperatorQualification
from ..models.user import User


class OperatorQualificationService:
    """Section 11 - Operator qualification management"""
    
    @staticmethod
    def create_qualification(db: Session, user_id: int, qualified_by: str) -> OperatorQualification:
        """Create new operator qualification record"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        qualification = OperatorQualification(
            user_id=user_id,
            qualification_valid_until=datetime.now() + timedelta(days=730),  # 2 years
            qualified_by=qualified_by,
            is_active=True
        )
        
        db.add(qualification)
        db.commit()
        db.refresh(qualification)
        return qualification
    
    @staticmethod
    def update_qualification(db: Session, qualification_id: int, **kwargs) -> OperatorQualification:
        """Update qualification record"""
        
        qualification = db.query(OperatorQualification).filter(
            OperatorQualification.id == qualification_id
        ).first()
        
        if not qualification:
            raise ValueError(f"Qualification with ID {qualification_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(qualification, key):
                setattr(qualification, key, value)
        
        db.commit()
        db.refresh(qualification)
        return qualification
    
    @staticmethod
    def get_qualified_operators(db: Session) -> list:
        """Get list of currently qualified operators"""
        return db.query(OperatorQualification).filter(
            OperatorQualification.is_active == True,
            OperatorQualification.qualification_valid_until > datetime.now(),
            OperatorQualification.practical_demo_passed == True
        ).all()
    
    @staticmethod
    def get_operator_table(db: Session) -> list:
        """Get operator qualification data for protocol table"""
        qualifications = db.query(OperatorQualification).all()
        
        result = []
        for q in qualifications:
            user = q.user if q.user else None
            result.append({
                "operator_name": user.username if user else "N/A",
                "eyesight": "✅" if q.eyesight_certified else "❌",
                "color_blindness": "✅" if q.color_blindness_test_passed else "❌",
                "training_date": q.training_date.strftime('%d/%m/%Y') if q.training_date else "N/A",
                "qualified": "✅" if q.practical_demo_passed else "❌",
                "valid_until": q.qualification_valid_until.strftime('%d/%m/%Y') if q.qualification_valid_until else "N/A"
            })
        
        return result