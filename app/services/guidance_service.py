from typing import List
from ..schemas.guidance import GuidanceQuestionResponse, RevalidationCheckResponse

class GuidanceService:
    """Section 10.0 - Validation Questions (FAQ) and decision support"""
    
    @staticmethod
    def get_all_questions() -> List[GuidanceQuestionResponse]:
        """Section 10.0 - All 17 validation questions with answers"""
        questions = [
            {
                "question_id": "Q1",
                "question": "When should a company validate/revalidate cleaning procedures?",
                "answer": "Companies should evaluate each situation individually. Revalidation is required when there are changes to cleaning procedure, equipment, product, or analytical method. Periodic evaluation (typically annually) is recommended for manual procedures.",
                "guideline_section": "7.0, 10.0"
            },
            {
                "question_id": "Q2",
                "question": "When is it appropriate to use Prospective, Concurrent or Retrospective Validation?",
                "answer": "Prospective validation is ideal. Concurrent validation may be used when few runs are manufactured. Retrospective validation of cleaning is NOT condoned by regulatory authorities.",
                "guideline_section": "9.0"
            },
            {
                "question_id": "Q3",
                "question": "What level of testing is needed after cleaning validation?",
                "answer": "Visual inspection for all levels. For Level 1 and 2, rinse/swab samples at predefined intervals. Non-specific methods (e.g., dry residue, TLC) may be used for routine verification.",
                "guideline_section": "5.3"
            },
            {
                "question_id": "Q4",
                "question": "What critical parameters need to be looked at during cleaning validation?",
                "answer": "Equipment design, product residues, cleaning agents, cleaning techniques, ruggedness, reproducibility, Dirty Hold Time (DHT), Clean Hold Time (CHT).",
                "guideline_section": "8.2"
            },
            {
                "question_id": "Q5",
                "question": "What number of cleans should be run in order to validate a cleaning procedure?",
                "answer": "Generally three consecutive successful replicates. Companies should evaluate each situation individually.",
                "guideline_section": "9.0"
            },
            {
                "question_id": "Q6",
                "question": "Is it acceptable for a validated cleaning procedure to be continued until analytical results demonstrate it is clean?",
                "answer": "NO. Regulatory authorities do not condone this practice. Investigation and root cause analysis required for failures.",
                "guideline_section": "9.0"
            },
            {
                "question_id": "Q7",
                "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be dirty before cleaning?",
                "answer": "YES. Dirty Hold Time (DHT) should be validated. Group/bracket products and validate worst case scenario.",
                "guideline_section": "9.7"
            },
            {
                "question_id": "Q8",
                "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be left clean before re-use?",
                "answer": "YES. Clean Hold Time (CHT) should be validated if there is any risk of contamination during idle time.",
                "guideline_section": "9.7"
            },
            {
                "question_id": "Q9",
                "question": "Is it necessary to include microbiological testing in cleaning validation?",
                "answer": "YES if water is used for final cleaning or for biotech/parenteral products. Reference: EMA 158/01.",
                "guideline_section": "8.1"
            },
            {
                "question_id": "Q10",
                "question": "Which analytical methods should be used in cleaning validation studies?",
                "answer": "Any method suitable for intended use (HPLC, GC, TLC, TOC, dry residue, conductivity, pH). Limit tests have less stringent validation requirements.",
                "guideline_section": "8.0"
            },
            {
                "question_id": "Q11",
                "question": "Do we have to wait for swab and rinse samples to be approved prior using the equipment for production?",
                "answer": "During cleaning validation studies it is recommended to wait for completion of all planned tests. In routine operations, release pending testing results could be done with defined responsibilities.",
                "guideline_section": "10.0"
            },
            {
                "question_id": "Q12",
                "question": "Is it necessary to validate time limits for cleaning if equipment is not used frequently?",
                "answer": "Yes, if there is any risk of contamination during idle time after cleaning, validation should be considered.",
                "guideline_section": "9.7"
            },
            {
                "question_id": "Q13",
                "question": "What is the maximum time allowed after cleaning with water as last rinse?",
                "answer": "Equipment should not be left with water in it after cleaning. The last step should involve drying with solvent or flushing with Nitrogen.",
                "guideline_section": "9.7"
            },
            {
                "question_id": "Q14",
                "question": "Is it possible that deterioration of equipment may take place over time, invalidating original validation results?",
                "answer": "Yes, equipment materials should be evaluated for durability over time as part of preventative maintenance program.",
                "guideline_section": "8.2"
            },
            {
                "question_id": "Q15",
                "question": "If a company has validated a worst case scenario, should they also validate a 'less' worst case?",
                "answer": "For operational reasons it may be beneficial to validate a 'less' stringent cleaning procedure for some products.",
                "guideline_section": "7.0"
            },
            {
                "question_id": "Q16",
                "question": "In a case of a dedicated plant with no degradants, is there a need to validate?",
                "answer": "Companies should consider each situation individually. In dedicated facilities, there may not be a need for cross-contamination validation.",
                "guideline_section": "7.0"
            },
            {
                "question_id": "Q17",
                "question": "Should cleaning validation be part of a development programme?",
                "answer": "If equipment after development product is used for commercial product or human use, it is essential to verify cleanliness prior to re-use.",
                "guideline_section": "9.0"
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