from sqlalchemy.orm import Session
from datetime import datetime
from ..models.change_control import ChangeControl

class ChangeControlService:
    """
    Section 10.0 - Revalidation and Change Control
    APIC Guidance: Any change to cleaning procedure, equipment, or product requires evaluation
    """
    
    @staticmethod
    def assess_cleaning_change(change_type: str, details: dict) -> dict:
        """
        Assess if a change requires revalidation
        
        Changes requiring revalidation:
        - New product introduction
        - Equipment modification
        - Cleaning procedure change
        - Detergent change
        - New harder-to-clean residue
        """
        
        revalidation_triggers = {
            "new_product": {
                "required": True,
                "severity": "HIGH",
                "action": "Full cleaning validation required for new product combination",
                "studies_required": ["MACO calculation", "Swab recovery", "3 consecutive cleans"]
            },
            "equipment_modification": {
                "required": True,
                "severity": "MEDIUM",
                "action": "Revalidate affected equipment only",
                "studies_required": ["Surface area recalculation", "Worst case location mapping"]
            },
            "cleaning_procedure_change": {
                "required": True,
                "severity": "HIGH",
                "action": "Full revalidation of modified procedure",
                "studies_required": ["3 consecutive cleans", "Analytical method verification"]
            },
            "detergent_change": {
                "required": True,
                "severity": "MEDIUM",
                "action": "Validate new detergent removal",
                "studies_required": ["Rinse testing for detergent", "Residual analysis"]
            },
            "campaign_length_change": {
                "required": True,
                "severity": "MEDIUM",
                "action": "Extend campaign validation",
                "studies_required": ["Additional sampling at extended campaign length"]
            },
            "process_parameter_change": {
                "required": False,
                "severity": "LOW",
                "action": "Verify within validated range",
                "studies_required": ["Single verification run"]
            }
        }
        
        return revalidation_triggers.get(change_type, {
            "required": False,
            "severity": "LOW",
            "action": "No revalidation required, document in log",
            "studies_required": []
        })
    
    @staticmethod
    def create_change_control(db: Session, change_data: dict) -> ChangeControl:
        """Create a change control record"""
        
        change = ChangeControl(
            change_number=f"CC-{datetime.now().strftime('%Y%m')}-{ChangeControlService._get_next_number(db)}",
            title=change_data.get("title"),
            type=change_data.get("type"),
            description=change_data.get("description"),
            reason=change_data.get("reason"),
            impact_on_cleaning=change_data.get("impact_on_cleaning"),
            impact_on_validation=change_data.get("impact_on_validation"),
            risk_assessment=change_data.get("risk_assessment"),
            equipment_id=change_data.get("equipment_id"),
            product_id=change_data.get("product_id"),
            cleaning_procedure_id=change_data.get("cleaning_procedure_id"),
            proposed_by=change_data.get("proposed_by"),
            status="PROPOSED"
        )
        
        # Assess if revalidation required
        revalidation_assessment = ChangeControlService.assess_cleaning_change(
            change_data.get("type", ""),
            change_data
        )
        
        change.revalidation_required = revalidation_assessment["required"]
        
        db.add(change)
        db.commit()
        db.refresh(change)
        
        return change
    
    @staticmethod
    def _get_next_number(db: Session) -> str:
        """Get next change control number"""
        count = db.query(ChangeControl).count()
        return f"{count + 1:04d}"