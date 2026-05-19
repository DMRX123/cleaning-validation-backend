from sqlalchemy.orm import Session
from datetime import datetime
from ..models.nitrosamine import NitrosamineRiskAssessment
from ..models.product import Product


class NitrosamineService:
    """Section 13 - Nitrosamine risk assessment"""
    
    @staticmethod
    def create_assessment(db: Session, product_id: int, assessed_by: str,
                         secondary_amine_present: bool = False,
                         tertiary_amine_present: bool = False,
                         primary_amine_present: bool = False,
                         nitrite_in_raw_materials: bool = False,
                         nitrosating_agents_used: bool = False) -> NitrosamineRiskAssessment:
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Determine overall risk
        overall_risk = "Low"
        if secondary_amine_present and nitrosating_agents_used:
            overall_risk = "High"
        elif secondary_amine_present or tertiary_amine_present:
            overall_risk = "Medium"
        
        assessment = NitrosamineRiskAssessment(
            product_id=product_id,
            secondary_amine_present=secondary_amine_present,
            tertiary_amine_present=tertiary_amine_present,
            primary_amine_present=primary_amine_present,
            nitrite_in_raw_materials=nitrite_in_raw_materials,
            nitrosating_agents_used=nitrosating_agents_used,
            overall_risk_level=overall_risk,
            assessment_date=datetime.now(),
            assessed_by=assessed_by,
            requires_confirmatory_testing=(overall_risk == "High")
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment
    
    @staticmethod
    def get_assessment(db: Session, product_id: int) -> NitrosamineRiskAssessment:
        """Get nitrosamine risk assessment for a product"""
        return db.query(NitrosamineRiskAssessment).filter(
            NitrosamineRiskAssessment.product_id == product_id
        ).first()
    
    @staticmethod
    def get_risk_summary(db: Session, product_id: int) -> dict:
        """Get formatted risk summary for protocol"""
        assessment = NitrosamineService.get_assessment(db, product_id)
        
        if not assessment:
            return {
                "risk_level": "Not Assessed",
                "justification": "Assessment pending",
                "requires_testing": True
            }
        
        return {
            "risk_level": assessment.overall_risk_level,
            "justification": f"Secondary amine: {assessment.secondary_amine_present}, "
                           f"Nitrosating agents: {assessment.nitrosating_agents_used}",
            "requires_testing": assessment.requires_confirmatory_testing
        }