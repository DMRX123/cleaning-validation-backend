class LimitRationaleService:
    """
    APIC Section 4.2.6 - Rationale for different limits in pharmaceutical and chemical production
    APIC Guidance: Higher limits acceptable in chemical production due to process reductions
    """
    
    PRODUCTION_TYPE_FACTORS = {
        "pharmaceutical": 1.0,
        "api_chemical": 8.0,
        "api_physical": 1.0,
        "intermediate_early": 15.0,
        "intermediate_late": 5.0,
        "dedicated": None
    }
    
    @classmethod
    def get_factor(cls, production_type: str, has_purification_step: bool = False,
                   has_dissolution_step: bool = False, has_filtration_step: bool = False,
                   has_crystallization_step: bool = False) -> float:
        """APIC Section 4.2.6 - Factor 5-10 is scientifically justified"""
        base_factor = cls.PRODUCTION_TYPE_FACTORS.get(production_type, 1.0)
        
        if base_factor is None:
            return None
        
        if has_dissolution_step:
            base_factor *= 1.5
        if has_filtration_step:
            base_factor *= 2.0
        if has_crystallization_step:
            base_factor *= 2.0
        
        return min(base_factor, 20.0)
    
    @classmethod
    def get_rationale(cls, production_type: str, process_steps: list = None) -> dict:
        """Generate documented rationale for limit calculation"""
        
        if process_steps is None:
            process_steps = []
        
        factor = cls.get_factor(production_type)
        
        rationale = {
            "production_type": production_type,
            "applied_factor": factor,
            "justification": [],
            "references": [
                "APIC Cleaning Validation Guide Section 4.2.6",
                "EMA/CHMP/CVMP/SWP/169430/2012"
            ]
        }
        
        if production_type == "pharmaceutical":
            rationale["justification"].append(
                "In pharmaceutical production, residues on equipment surface may be "
                "100% carried over to the next product with no dilution or removal."
            )
            rationale["limit_stringency"] = "Most stringent (1x)"
            rationale["recommended_limit_ppm"] = "1-10 ppm"
        
        elif production_type == "api_chemical":
            rationale["justification"].extend([
                "Chemical processing steps include dissolution, extraction, and filtration.",
                "These steps significantly reduce any residue from previous operations.",
                f"A safety factor of {factor} is scientifically justified for API chemical production."
            ])
            rationale["limit_stringency"] = f"Less stringent ({factor}x higher)"
            rationale["recommended_limit_ppm"] = f"{int(10 * factor)}-{int(100 * factor)} ppm"
            
            if "crystallization" in process_steps:
                rationale["justification"].append(
                    "Final crystallization step provides additional purification, "
                    "removing contaminants from the final API."
                )
        
        elif production_type == "intermediate_early":
            rationale["justification"].append(
                "Early synthetic steps undergo further processing and purification. "
                f"Higher limits ({factor}x) are acceptable for early intermediates."
            )
            rationale["limit_stringency"] = f"Least stringent ({factor}x higher)"
            rationale["recommended_limit_ppm"] = f"{int(50 * factor)}-{int(500 * factor)} ppm"
        
        elif production_type == "dedicated":
            rationale["justification"].append(
                "Dedicated equipment is used for only one product. "
                "Cleaning validation focuses on degradation products and cleaning agent residues."
            )
            rationale["limit_stringency"] = "Not applicable (dedicated facility)"
            rationale["recommended_limit_ppm"] = "Visual only or limit based on degradation"
        
        if "dissolution" in process_steps:
            rationale["justification"].append("Dissolution step helps solubilize any remaining residue.")
        if "filtration" in process_steps:
            rationale["justification"].append("Filtration step removes insoluble residues.")
        if "extraction" in process_steps:
            rationale["justification"].append("Extraction step partitions residue into different phase.")
        
        rationale["conclusion"] = (
            f"Based on APIC Section 4.2.6, a factor of {factor} is applied. "
            "Higher limits in chemical production are scientifically justified due to "
            "process reductions (dissolution, filtration, crystallization)."
        )
        
        return rationale
    
    @classmethod
    def get_comparison_table(cls) -> dict:
        """Get comparison table for pharmaceutical vs chemical production limits"""
        return {
            "pharmaceutical_production": {
                "carry_over_risk": "100% direct transfer to patient",
                "typical_limit_ppm": "1-10 ppm",
                "safety_factor": "1x",
                "reasoning": "No process steps to reduce residue",
                "examples": "Tablets, capsules, injectables"
            },
            "chemical_production": {
                "carry_over_risk": "Significantly reduced by process steps",
                "typical_limit_ppm": "50-500 ppm",
                "safety_factor": "5-10x",
                "reasoning": "Dissolution, extraction, filtration, crystallization reduce residue",
                "examples": "API synthesis, intermediates, chemical reactions"
            },
            "reference": "APIC Cleaning Validation Guide Section 4.2.6 - Figure 2",
            "conclusion": "Higher limits in chemical production are scientifically justified and acceptable."
        }