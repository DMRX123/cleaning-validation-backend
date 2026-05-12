from sqlalchemy.orm import Session
from ..models.microbiological import MicrobiologicalLimit, MicrobiologicalResult

class MicrobiologicalService:
    """
    Section 8.1 - Microbiological Testing in Cleaning Validation
    APIC Guidance: Required when water is used for final cleaning or for biotech products
    """
    
    # Reference: EMA 158/01 'Note for Guidance on Quality of Water for Pharmaceutical Use'
    DEFAULT_LIMITS = {
        "oral": {
            "total_germ_count": 100,      # CFU/dm²
            "yeast_mold": 50,             # CFU/dm²
            "endotoxin": None,            # EU/ml
            "sampling_method": "swab",
            "reference": "EP 2.6.12"
        },
        "parenteral": {
            "total_germ_count": 10,       # CFU/dm²
            "yeast_mold": 5,              # CFU/dm²
            "endotoxin": 0.25,            # EU/ml
            "sampling_method": "rinse",
            "reference": "EP 2.6.14"
        },
        "topical": {
            "total_germ_count": 100,      # CFU/dm²
            "yeast_mold": 50,             # CFU/dm²
            "endotoxin": None,
            "sampling_method": "contact plate",
            "reference": "EP 2.6.12"
        },
        "biotech": {
            "total_germ_count": 10,       # CFU/dm²
            "yeast_mold": 5,              # CFU/dm²
            "endotoxin": 0.25,            # EU/ml
            "sampling_method": "swab",
            "reference": "PDA TR No. 29"
        },
        "inhalation": {
            "total_germ_count": 10,       # CFU/dm²
            "yeast_mold": 5,              # CFU/dm²
            "endotoxin": 0.25,            # EU/ml
            "sampling_method": "rinse",
            "reference": "Ph.Eur. 2.6.12"
        }
    }
    
    @classmethod
    def get_default_limits(cls, product_type: str) -> dict:
        """Get default microbiological limits based on product type"""
        return cls.DEFAULT_LIMITS.get(product_type.lower(), cls.DEFAULT_LIMITS["oral"])
    
    @classmethod
    def evaluate_microbiological_result(cls, result: MicrobiologicalResult, limit: MicrobiologicalLimit) -> dict:
        """Evaluate microbiological test results against limits"""
        
        evaluation = {
            "sample_location": result.sample_location,
            "sample_date": result.sample_date.isoformat() if result.sample_date else None,
            "total_germ_count": result.total_germ_count,
            "total_germ_limit": limit.total_germ_count_limit,
            "total_germ_acceptable": result.total_germ_count <= limit.total_germ_count_limit if result.total_germ_count else False,
            "status": "PASS"
        }
        
        if limit.yeast_mold_limit and result.yeast_mold_count is not None:
            evaluation["yeast_mold_count"] = result.yeast_mold_count
            evaluation["yeast_mold_limit"] = limit.yeast_mold_limit
            evaluation["yeast_mold_acceptable"] = result.yeast_mold_count <= limit.yeast_mold_limit
            if not evaluation["yeast_mold_acceptable"]:
                evaluation["status"] = "FAIL"
        
        if limit.endotoxin_limit and result.endotoxin_value is not None:
            evaluation["endotoxin_value"] = result.endotoxin_value
            evaluation["endotoxin_limit"] = limit.endotoxin_limit
            evaluation["endotoxin_acceptable"] = result.endotoxin_value <= limit.endotoxin_limit
            if not evaluation["endotoxin_acceptable"]:
                evaluation["status"] = "FAIL"
        
        if not evaluation.get("total_germ_acceptable", True):
            evaluation["status"] = "FAIL"
        
        evaluation["overall_acceptable"] = evaluation["status"] == "PASS"
        evaluation["reported"] = evaluation["status"]
        evaluation["action_if_fail"] = cls._get_failure_action(evaluation["status"])
        
        return evaluation
    
    @classmethod
    def _get_failure_action(cls, status: str) -> str:
        if status == "FAIL":
            return "Investigate source of contamination. Rec equipotent. Perform root cause analysis. Document in deviation report."
        return "No action required"
    
    @classmethod
    def get_sampling_frequency(cls, cleaning_level: str, product_type: str, risk_level: str = "MEDIUM") -> str:
        """Determine sampling frequency based on cleaning level, product type, and risk"""
        
        if cleaning_level == "LEVEL_0":
            return "Not required"
        
        frequencies = {
            ("LEVEL_2", "parenteral", "HIGH"): "Every batch",
            ("LEVEL_2", "parenteral", "MEDIUM"): "Every 5 batches",
            ("LEVEL_2", "biotech", "HIGH"): "Every batch",
            ("LEVEL_2", "biotech", "MEDIUM"): "Every 5 batches",
            ("LEVEL_2", "oral", "HIGH"): "Monthly",
            ("LEVEL_2", "oral", "MEDIUM"): "Quarterly",
            ("LEVEL_1", "ANY", "HIGH"): "Monthly",
            ("LEVEL_1", "ANY", "MEDIUM"): "Quarterly",
            ("LEVEL_1", "ANY", "LOW"): "Annually"
        }
        
        key = (cleaning_level, product_type, risk_level)
        if key not in frequencies:
            key = (cleaning_level, "ANY", risk_level)
        
        return frequencies.get(key, "Quarterly")