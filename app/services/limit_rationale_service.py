class LimitRationaleService:
    """
    Section 4.2.6 - Rationale for different limits in pharmaceutical and chemical production
    APIC Guidance: Higher limits acceptable in chemical production due to process reductions
    """
    
    # Factors for different production types
    PRODUCTION_TYPE_FACTORS = {
        "pharmaceutical": 1.0,      # Direct carry-over to patient
        "api_chemical": 8.0,        # Chemical processing reduces residue (5-10x)
        "api_physical": 1.0,        # Drying, milling - no reduction
        "intermediate_early": 15.0,  # Early steps - further purification
        "intermediate_late": 5.0,    # Late steps - less purification
        "dedicated": None            # No limit needed for dedicated equipment
    }
    
    @classmethod
    def get_factor(cls, production_type: str, has_purification_step: bool = False,
                   has_dissolution_step: bool = False, has_filtration_step: bool = False,
                   has_crystallization_step: bool = False) -> float:
        """
        Calculate safety factor based on production type and process steps
        
        Chemical production processes include:
        - Dissolution: residue goes into solution (reduction)
        - Extraction: residue removed with solvent (significant reduction)
        - Filtration: insoluble residue removed (significant reduction)
        - Crystallization: API purified (significant reduction)
        
        Therefore, carry-over risk is much lower than pharmaceutical production
        """
        base_factor = cls.PRODUCTION_TYPE_FACTORS.get(production_type, 1.0)
        
        if base_factor is None:
            return None
        
        # Additional reduction factors for chemical processes
        if has_dissolution_step:
            base_factor *= 1.5
        if has_filtration_step:
            base_factor *= 2.0
        if has_crystallization_step:
            base_factor *= 2.0
        
        # Cap at 20x (as per APIC guidance)
        return min(base_factor, 20.0)
    
    @classmethod
    def get_rationale(cls, production_type: str, process_steps: list = None) -> dict:
        """Generate documented rationale for limit calculation"""
        
        if process_steps is None:
            process_steps = []
        
        rationale = {
            "production_type": production_type,
            "applied_factor": cls.get_factor(production_type),
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
            rationale["limit_stringency"] = "Most stringent"
        
        elif production_type == "api_chemical":
            rationale["justification"].extend([
                "Chemical processing steps include dissolution, extraction, and filtration.",
                "These steps significantly reduce any residue from previous operations.",
                "A safety factor of 5-10 is scientifically justified for API chemical production."
            ])
            rationale["limit_stringency"] = "Less stringent (5-10x higher)"
            
            if "crystallization" in process_steps:
                rationale["justification"].append(
                    "Final crystallization step provides additional purification, "
                    "removing contaminants from the final API."
                )
        
        elif production_type == "intermediate_early":
            rationale["justification"].append(
                "Early synthetic steps undergo further processing and purification. "
                "Higher limits (10-20x) are acceptable for early intermediates."
            )
            rationale["limit_stringency"] = "Least stringent (10-20x higher)"
        
        elif production_type == "dedicated":
            rationale["justification"].append(
                "Dedicated equipment is used for only one product. "
                "Cleaning validation focuses on degradation products and cleaning agent residues."
            )
            rationale["limit_stringency"] = "Not applicable (dedicated facility)"
        
        # Add process step specific justifications
        if "dissolution" in process_steps:
            rationale["justification"].append("Dissolution step helps solubilize any remaining residue.")
        if "filtration" in process_steps:
            rationale["justification"].append("Filtration step removes insoluble residues.")
        if "extraction" in process_steps:
            rationale["justification"].append("Extraction step partitions residue into different phase.")
        
        return rationale
    
    @classmethod
    def get_comparison_table(cls) -> dict:
        """Get comparison table for pharmaceutical vs chemical production limits"""
        return {
            "pharmaceutical_production": {
                "carry_over_risk": "100% direct transfer to patient",
                "typical_limit_ppm": "1-10 ppm",
                "safety_factor": "1x",
                "reasoning": "No process steps to reduce residue"
            },
            "chemical_production": {
                "carry_over_risk": "Significantly reduced by process steps",
                "typical_limit_ppm": "50-500 ppm",
                "safety_factor": "5-10x",
                "reasoning": "Dissolution, extraction, filtration, crystallization reduce residue"
            },
            "reference": "APIC Cleaning Validation Guide Section 4.2.6 - Figure 2"
        }