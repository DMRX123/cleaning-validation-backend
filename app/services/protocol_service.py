from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from ..models.validation_protocol import ValidationProtocol, ProtocolExecutionResult
from ..models.product import Product
from ..models.equipment import Equipment
from ..services.maco import MACOService
from .swab import SwabService
from ..services.rinse import RinseService

class ProtocolService:
    """
    Section 9.0 - Cleaning Validation Protocol
    """
    
    @staticmethod
    def generate_protocol_number() -> str:
        """Generate unique protocol number"""
        return f"CV-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    
    @staticmethod
    def create_protocol(db: Session,
                        equipment_id: int,
                        previous_product_id: int,
                        next_product_id: int,
                        cleaning_procedure_id: str,
                        prepared_by: str) -> ValidationProtocol:
        """Create a complete validation protocol"""
        
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        previous = db.query(Product).filter(Product.id == previous_product_id).first()
        next_product = db.query(Product).filter(Product.id == next_product_id).first()
        
        # Calculate MACO
        maco_result = MACOService.calculate_all(previous, next_product)
        
        # Calculate swab limit
        swab_limit = SwabService.calculate_swab_limit_for_product(previous, next_product, equipment.surface_area)
        
        protocol = ValidationProtocol(
            protocol_number=ProtocolService.generate_protocol_number(),
            title=f"Cleaning Validation Protocol for {previous.name} to {next_product.name}",
            version=1,
            status="DRAFT",
            
            # Section 9.1 - Background
            background=ProtocolService._generate_background(equipment, previous),
            
            # Section 9.2 - Purpose
            purpose=ProtocolService._generate_purpose(previous, next_product),
            
            # Section 9.3 - Scope
            scope=ProtocolService._generate_scope(equipment),
            
            # Equipment and products
            equipment_id=equipment_id,
            cleaning_procedure_id=cleaning_procedure_id,
            previous_product_id=previous_product_id,
            next_product_id=next_product_id,
            
            # Section 9.7 - Acceptance Criteria
            visual_acceptance="No visible residue when equipment is dry and inspected under adequate lighting",
            chemical_acceptance_ppm=swab_limit.get("ppm", 50),
            microbiological_acceptance=100,  # CFU/dm²
            
            # Section 9.5 - Sampling Plan
            sampling_locations=ProtocolService._get_sampling_locations(equipment),
            rinse_volume=ProtocolService._calculate_rinse_volume(equipment),
            
            # Section 9.6 - Testing Plan
            analytical_methods=ProtocolService._get_analytical_methods(previous),
            
            # Section 9.4 - Responsibilities
            responsibilities=ProtocolService._get_responsibilities(),
            
            # Section 9.8 - Training Requirements
            training_requirements=ProtocolService._get_training_requirements(),
            
            # Section 9.7 - Hold Times
            dirty_hold_time_hours=24,  # Default
            clean_hold_time_hours=168,  # Default (7 days)
            
            prepared_by=prepared_by,
            prepared_date=datetime.now()
        )
        
        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        
        return protocol
    
    @staticmethod
    def _generate_background(equipment: Equipment, product: Product) -> str:
        return f"""
        Equipment {equipment.name} (ID: {equipment.equipment_id}) is routinely cleaned after 
        production of {product.name} according to cleaning procedure SOP-{equipment.cleaning_procedure}.
        
        This equipment is used for multi-purpose manufacturing of Active Pharmaceutical Ingredients (APIs).
        The cleaning procedure involves {equipment.used_for} operations followed by solvent rinsing.
        """
    
    @staticmethod
    def _generate_purpose(previous: Product, next_product: Product) -> str:
        return f"""
        The purpose of this study is to demonstrate that remaining product residues of {previous.name}
        in the equipment are always within the established acceptance criteria when the equipment 
        is cleaned by the defined cleaning procedure prior to manufacturing {next_product.name}.
        """
    
    @staticmethod
    def _generate_scope(equipment: Equipment) -> str:
        return f"""
        A visual test and chemical evaluation of the equipment {equipment.name} will be performed 
        after cleaning to demonstrate that product residues and cleaning agent residues have been 
        removed to levels within the acceptance criteria.
        
        The equipment cleanliness will be proven by testing and evaluation of samples from 
        three (3) consecutive cleans as per this protocol.
        """
    
    @staticmethod
    def _get_sampling_locations(equipment: Equipment) -> list:
        """Define sampling locations based on equipment type"""
        return [
            {"location": "Manhole area", "surface_type": "Stainless Steel", "area_dm2": 1},
            {"location": "Bottom discharge valve", "surface_type": "Stainless Steel", "area_dm2": 0.5},
            {"location": "Agitator blades", "surface_type": "Stainless Steel", "area_dm2": 2},
            {"location": "Baffles", "surface_type": "Stainless Steel", "area_dm2": 1}
        ]
    
    @staticmethod
    def _calculate_rinse_volume(equipment: Equipment) -> float:
        """Calculate minimum rinse volume to cover all surfaces"""
        # Simple calculation: 5L per m² of surface area
        return round(equipment.surface_area * 5, 1)
    
    @staticmethod
    def _get_analytical_methods(product: Product) -> list:
        return [
            {
                "test": f"Residual {product.name} quantification",
                "method": "HPLC-UV",
                "lod": product.lod,
                "loq": product.loq,
                "acceptance_criteria": f"< {product.loq} ppm"
            },
            {
                "test": "Total Organic Carbon (TOC)",
                "method": "TOC Analyzer",
                "lod": 0.05,
                "loq": 0.1,
                "acceptance_criteria": "< 0.5 ppm"
            },
            {
                "test": "Conductivity",
                "method": "Conductivity Meter",
                "acceptance_criteria": "< 1 µS/cm"
            }
        ]
    
    @staticmethod
    def _get_responsibilities() -> dict:
        return {
            "Scheduling": "Manufacturing, QA, QC, Engineering",
            "Cleaning of equipment": "Manufacturing",
            "Removal of samples": "QA",
            "Testing of samples": "QC",
            "Review of data and approval": "Validation / Manufacturing / QC"
        }
    
    @staticmethod
    def _get_training_requirements() -> list:
        return [
            "Cleaning of equipment (SOP)",
            "Visual inspection of equipment",
            "Sampling techniques (swab and rinse)",
            "Analytical methods used",
            "Deviations and investigation procedures"
        ]
    
    @staticmethod
    def check_consecutive_success(db: Session, protocol_id: int) -> dict:
        """
        Section 5.3.2 - Track consecutive successful cleans
        Returns dict with validation status and required actions
        """
        from ..models.validation_protocol import ValidationProtocol, ProtocolExecutionResult
        
        protocol = db.query(ValidationProtocol).filter(ValidationProtocol.id == protocol_id).first()
        if not protocol:
            return {"error": "Protocol not found"}
        
        # Get all results in order
        results = db.query(ProtocolExecutionResult).filter(
            ProtocolExecutionResult.protocol_id == protocol_id
        ).order_by(ProtocolExecutionResult.execution_number).all()
        
        if not results:
            return {
                "consecutive_passes": 0,
                "required_passes": protocol.consecutive_passes_required,
                "validation_complete": False,
                "status": "No executions yet"
            }
        
        # Count consecutive passes from most recent
        consecutive_passes = 0
        for result in reversed(results):
            if result.overall_result == "PASS":
                consecutive_passes += 1
            else:
                break
        
        validation_complete = consecutive_passes >= protocol.consecutive_passes_required
        
        # Update protocol
        protocol.consecutive_passes_achieved = consecutive_passes
        if validation_complete and protocol.status != "APPROVED":
            protocol.status = "APPROVED"
        elif not validation_complete and protocol.status == "APPROVED":
            protocol.status = "EXECUTED"  # Reset if validation broken
        
        db.commit()
        
        return {
            "consecutive_passes": consecutive_passes,
            "required_passes": protocol.consecutive_passes_required,
            "validation_complete": validation_complete,
            "status": protocol.status,
            "message": f"Validation {'complete' if validation_complete else f'in progress - need {protocol.consecutive_passes_required - consecutive_passes} more passes'}"
        }