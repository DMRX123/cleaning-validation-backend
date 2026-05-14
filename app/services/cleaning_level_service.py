from sqlalchemy.orm import Session
from ..models.cleaning_level import CleaningLevel, CleaningLevelEnum, CleaningLevelAssignment
from ..models.product import Product

class CleaningLevelService:
    """
    Section 5.0 - Levels of Cleaning
    APIC Guidance: Three levels of cleaning based on risk assessment
    """
    
    @staticmethod
    def determine_level(previous_product: Product, next_product: Product,
                        same_synthetic_chain: bool = False,
                        previous_step: int = None, next_step: int = None) -> CleaningLevelEnum:
        """
        Determine cleaning level based on:
        - Same synthetic chain
        - Step proximity
        - Toxicity of previous product
        - Final API status
        """
        
        # Level 0: Same synthetic chain, next step is immediate next
        if same_synthetic_chain and previous_step and next_step:
            if next_step == previous_step + 1:
                return CleaningLevelEnum.LEVEL_0
        
        # Level 2: Different product lines or final API steps
        if hasattr(previous_product, 'plant') and hasattr(next_product, 'plant'):
            if previous_product.plant != next_product.plant:
                return CleaningLevelEnum.LEVEL_2
        
        # Check if either product is final API (based on name or flag)
        if hasattr(previous_product, 'is_final_api') and previous_product.is_final_api:
            return CleaningLevelEnum.LEVEL_2
        if hasattr(next_product, 'is_final_api') and next_product.is_final_api:
            return CleaningLevelEnum.LEVEL_2
        
        # Check toxicity - high toxicity requires Level 2
        if previous_product.ade_pde < 10:  # Less than 10 µg/day
            return CleaningLevelEnum.LEVEL_2
        
        # Default to Level 1
        return CleaningLevelEnum.LEVEL_1
    
    @staticmethod
    def get_level_requirements(level: CleaningLevelEnum) -> dict:
        """Get testing requirements for each cleaning level"""
        
        requirements = {
            CleaningLevelEnum.LEVEL_0: {
                "visual_inspection": True,
                "analytical_testing": False,
                "microbiological_testing": False,
                "validation_required": False,
                "verification_frequency": None,
                "max_residue_ppm": None,
                "description": "Visual inspection only - low risk"
            },
            CleaningLevelEnum.LEVEL_1: {
                "visual_inspection": True,
                "analytical_testing": True,
                "microbiological_testing": False,
                "validation_required": True,
                "verification_frequency": "Periodic (quarterly)",
                "max_residue_ppm": 100,
                "description": "Visual + analytical - medium risk"
            },
            CleaningLevelEnum.LEVEL_2: {
                "visual_inspection": True,
                "analytical_testing": True,
                "microbiological_testing": True,
                "validation_required": True,
                "verification_frequency": "Every batch",
                "max_residue_ppm": 10,
                "description": "Full validation - high risk"
            }
        }
        
        return requirements.get(level, requirements[CleaningLevelEnum.LEVEL_1])
    
    @staticmethod
    def get_level_justification(level: CleaningLevelEnum, previous: Product, next_product: Product) -> str:
        """Generate justification for cleaning level selection"""
        justifications = {
            CleaningLevelEnum.LEVEL_0: f"Level 0 selected because {previous.name} and {next_product.name} are in the same synthetic chain. Carryover of {previous.name} is covered by the impurity profile of {next_product.name}.",
            CleaningLevelEnum.LEVEL_1: f"Level 1 selected because {previous.name} and {next_product.name} are in different product lines but neither is a final API. The ADE/PDE of {previous.name} is {previous.ade_pde} µg/day, which is above the threshold for Level 2.",
            CleaningLevelEnum.LEVEL_2: f"Level 2 selected because {previous.name} has high toxicity (ADE/PDE: {previous.ade_pde} µg/day) and/or {next_product.name} is a final API product. Full validation with analytical and microbiological testing is required."
        }
        return justifications.get(level, "Level selected based on risk assessment per APIC Guidance Section 5.0")
    
    @staticmethod
    def get_level_for_scenario(scenario: dict) -> dict:
        """
        Get cleaning level for typical product changeover scenarios
        Based on Figure 1 in APIC Guidance
        """
        
        scenarios = {
            "same_chain_immediate": {"level": "LEVEL_0", "factor": 1.0},
            "same_chain_non_immediate": {"level": "LEVEL_1", "factor": 5.0},
            "different_chain_early_step": {"level": "LEVEL_1", "factor": 5.0},
            "different_chain_final_api": {"level": "LEVEL_2", "factor": 1.0},
            "toxic_compound": {"level": "LEVEL_2", "factor": 1.0},
            "campaign_change": {"level": "LEVEL_1", "factor": 5.0}
        }
        
        scenario_key = f"{scenario.get('chain_type', 'different')}_{scenario.get('step_type', 'final')}"
        return scenarios.get(scenario_key, scenarios["different_chain_final_api"])
    
    @staticmethod
    def get_verification_requirements(level: CleaningLevelEnum, product_type: str = "api") -> dict:
        """
        Section 5.3 - Cleaning Verification vs Validation requirements per level
        """
        base_requirements = {
            CleaningLevelEnum.LEVEL_0: {
                "visual_inspection_required": True,
                "analytical_testing_required": False,
                "microbiological_testing_required": False,
                "validation_required": False,
                "verification_frequency": None,
                "max_residue_ppm": None,
                "can_release_without_testing": True,
                "description": "Visual inspection only - no analytical testing needed"
            },
            CleaningLevelEnum.LEVEL_1: {
                "visual_inspection_required": True,
                "analytical_testing_required": True,
                "microbiological_testing_required": False,
                "validation_required": True,
                "verification_frequency": "Periodic (quarterly)",
                "max_residue_ppm": 100,
                "can_release_without_testing": False,
                "description": "Visual + analytical testing required"
            },
            CleaningLevelEnum.LEVEL_2: {
                "visual_inspection_required": True,
                "analytical_testing_required": True,
                "microbiological_testing_required": True,
                "validation_required": True,
                "verification_frequency": "Every batch",
                "max_residue_ppm": 10,
                "can_release_without_testing": False,
                "description": "Full validation with microbiological testing"
            }
        }
        
        # Adjust for biotech/parenteral products
        if product_type in ["biotech", "parenteral", "inhalation"]:
            if base_requirements.get(level):
                base_requirements[level]["microbiological_testing_required"] = True
                base_requirements[level]["verification_frequency"] = "Every batch"
        
        return base_requirements.get(level, base_requirements.get(CleaningLevelEnum.LEVEL_1))