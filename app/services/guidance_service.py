from typing import List, Dict
from ..schemas.guidance import GuidanceQuestionResponse, RevalidationCheckResponse

class GuidanceService:
    """
    Section 10.0 - Validation Questions (FAQ) and decision support
    """
    
    @staticmethod
    def get_all_questions() -> List[GuidanceQuestionResponse]:
        """Section 10.0 - All 17 validation questions with answers"""
        questions = [
            {
                "question_id": "Q1",
                "question": "When should a company validate/revalidate cleaning procedures?",
                "answer": "Companies should evaluate each situation individually. Revalidation is required when there are changes to cleaning procedure, equipment, product, or analytical method. Periodic evaluation (typically annually) is recommended for manual procedures.",
                "section": "7.0, 10.0"
            },
            {
                "question_id": "Q2",
                "question": "When is it appropriate to use Prospective, Concurrent or Retrospective Validation?",
                "answer": "Prospective validation is ideal. Concurrent validation may be used when few runs are manufactured. Retrospective validation of cleaning is NOT condoned by regulatory authorities.",
                "section": "9.0"
            },
            {
                "question_id": "Q3",
                "question": "What level of testing is needed after cleaning validation?",
                "answer": "Visual inspection for all levels. For Level 1 and 2, rinse/swab samples at predefined intervals. Non-specific methods (e.g., dry residue, TLC) may be used for routine verification.",
                "section": "5.3"
            },
            {
                "question_id": "Q4",
                "question": "What critical parameters need to be looked at during cleaning validation?",
                "answer": "Equipment design, product residues, cleaning agents, cleaning techniques, ruggedness, reproducibility, Dirty Hold Time (DHT), Clean Hold Time (CHT).",
                "section": "8.2"
            },
            {
                "question_id": "Q5",
                "question": "What number of cleans should be run in order to validate a cleaning procedure?",
                "answer": "Generally three consecutive successful replicates. Companies should evaluate each situation individually.",
                "section": "9.0"
            },
            {
                "question_id": "Q6",
                "question": "Is it acceptable for a validated cleaning procedure to be continued until analytical results demonstrate it is clean?",
                "answer": "NO. Regulatory authorities do not condone this practice. Investigation and root cause analysis required for failures.",
                "section": "9.0"
            },
            {
                "question_id": "Q7",
                "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be dirty before cleaning?",
                "answer": "YES. Dirty Hold Time (DHT) should be validated. Group/bracket products and validate worst case scenario.",
                "section": "9.7"
            },
            {
                "question_id": "Q8",
                "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be left clean before re-use?",
                "answer": "YES. Clean Hold Time (CHT) should be validated if there is any risk of contamination during idle time.",
                "section": "9.7"
            },
            {
                "question_id": "Q9",
                "question": "Is it necessary to include microbiological testing in cleaning validation?",
                "answer": "YES if water is used for final cleaning or for biotech/parenteral products. Reference: EMA 158/01.",
                "section": "8.1"
            },
            {
                "question_id": "Q10",
                "question": "Which analytical methods should be used in cleaning validation studies?",
                "answer": "Any method suitable for intended use (HPLC, GC, TLC, TOC, dry residue, conductivity, pH). Limit tests have less stringent validation requirements.",
                "section": "8.0"
            }
        ]
        
        return [GuidanceQuestionResponse(**q) for q in questions]
    
    @staticmethod
    def assess_revalidation(request) -> RevalidationCheckResponse:
        """Section 10.0 - Assess if change requires revalidation"""
        
        revalidation_triggers = {
            "cleaning_procedure": {
                "required": True,
                "severity": "HIGH",
                "reason": "Cleaning procedure modification may affect residue removal efficacy",
                "actions": ["Full revalidation with 3 consecutive cleans", "Verify analytical methods"]
            },
            "equipment": {
                "required": True,
                "severity": "MEDIUM",
                "reason": "Equipment modification may change surface area or cleaning difficulty",
                "actions": ["Recalculate surface area", "Verify worst-case locations", "Single verification run"]
            },
            "product": {
                "required": True,
                "severity": "HIGH",
                "reason": "New product may have different solubility or toxicity profile",
                "actions": ["Recalculate MACO for all combinations", "Worst-case re-rating"]
            },
            "detergent": {
                "required": True,
                "severity": "MEDIUM",
                "reason": "New detergent may have different residue profile",
                "actions": ["Validate detergent removal", "Rinse testing for detergent residues"]
            },
            "batch_size": {
                "required": False,
                "severity": "LOW",
                "reason": "Batch size change may affect MACO calculation",
                "actions": ["Recalculate MACO", "Document in change control"]
            }
        }
        
        trigger = revalidation_triggers.get(request.change_type, {
            "required": False,
            "severity": "LOW",
            "reason": "Change type not recognized. Assess individually.",
            "actions": ["Document change", "Review cleaning validation status"]
        })
        
        return RevalidationCheckResponse(
            revalidation_required=trigger["required"],
            severity=trigger["severity"],
            reason=trigger["reason"],
            recommended_actions=trigger["actions"]
        )