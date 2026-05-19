from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..services.guidance_service import GuidanceService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["APIC Guidance"])


# ============================================
# SCHEMAS
# ============================================

class GuidanceQuestionResponse(BaseModel):
    question_id: str
    question: str
    answer: str
    guideline_section: str


class RevalidationCheckRequest(BaseModel):
    protocol_id: int
    change_type: str
    change_description: str


class RevalidationCheckResponse(BaseModel):
    revalidation_required: bool
    severity: str
    reason: str
    recommended_actions: List[str]


# ============================================
# GUIDANCE ENDPOINTS - PUBLIC
# ============================================

@router.get("/questions")
def get_validation_questions():
    """Section 10.0 - Get all validation FAQs with answers - PUBLIC"""
    try:
        questions = GuidanceService.get_all_questions()
        return {
            "success": True,
            "count": len(questions),
            "data": questions
        }
    except Exception as e:
        logger.error(f"Error getting guidance questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{question_id}")
def get_validation_question_by_id(question_id: str):
    """Get specific validation FAQ by ID - PUBLIC"""
    try:
        questions = GuidanceService.get_all_questions()
        for q in questions:
            if q.question_id == question_id:
                return {"success": True, "data": q}
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guidance question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revalidation-check")
def check_revalidation_needed(request: RevalidationCheckRequest, db: Session = Depends(get_db)):
    """Section 10.0 - Assess if a change requires revalidation - PUBLIC"""
    try:
        result = GuidanceService.assess_revalidation(request)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error checking revalidation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revalidation-triggers")
def get_revalidation_triggers():
    """Get all revalidation triggers and their requirements - PUBLIC"""
    triggers = {
        "cleaning_procedure": {
            "revalidation_required": True,
            "severity": "HIGH",
            "action": "Full revalidation with 3 consecutive cleans",
            "studies_required": ["MACO recalculation", "3 consecutive cleans", "Analytical method verification"]
        },
        "equipment": {
            "revalidation_required": True,
            "severity": "MEDIUM",
            "action": "Revalidate affected equipment only",
            "studies_required": ["Surface area recalculation", "Worst case location mapping", "Single verification run"]
        },
        "product": {
            "revalidation_required": True,
            "severity": "HIGH",
            "action": "Full revalidation for new product combination",
            "studies_required": ["MACO recalculation for all combinations", "Worst case re-rating", "3 consecutive cleans"]
        },
        "detergent": {
            "revalidation_required": True,
            "severity": "MEDIUM",
            "action": "Validate new detergent removal",
            "studies_required": ["Rinse testing for detergent", "Residual analysis", "Single verification run"]
        },
        "campaign_length": {
            "revalidation_required": True,
            "severity": "MEDIUM",
            "action": "Extend campaign validation",
            "studies_required": ["Additional sampling at extended campaign length", "Microbiological testing"]
        },
        "process_parameter": {
            "revalidation_required": False,
            "severity": "LOW",
            "action": "Verify within validated range",
            "studies_required": ["Single verification run", "Documentation"]
        }
    }
    return {"success": True, "data": triggers}


@router.get("/cleaning-levels-guidance")
def get_cleaning_levels_guidance():
    """Section 5.0 - Get cleaning levels guidance - PUBLIC"""
    levels = {
        "LEVEL_0": {
            "name": "Visual Only",
            "risk": "Low",
            "when_to_use": "Same synthetic chain - immediate next step",
            "requirements": ["Visual inspection only"],
            "verification_frequency": None
        },
        "LEVEL_1": {
            "name": "Visual + Analytical",
            "risk": "Medium",
            "when_to_use": "Different synthetic chain - early steps, Same chain non-immediate",
            "requirements": ["Visual inspection", "Analytical testing"],
            "verification_frequency": "Quarterly"
        },
        "LEVEL_2": {
            "name": "Full Validation",
            "risk": "High",
            "when_to_use": "Different product lines, Final API steps, Toxic compounds",
            "requirements": ["Visual inspection", "Analytical testing", "Microbiological testing"],
            "verification_frequency": "Every batch"
        }
    }
    return {"success": True, "data": levels, "reference": "APIC Cleaning Validation Guide Section 5.0"}


@router.get("/hold-times-guidance")
def get_hold_times_guidance():
    """Section 9.7 - Get hold times guidance - PUBLIC"""
    hold_times = {
        "dirty_hold_time": {
            "description": "Time between end of batch and start of cleaning",
            "typical_values_hours": {"reactor": 24, "dryer": 12, "tank": 48, "filler": 4},
            "validation_requirements": "Must be validated with 3 consecutive cleans",
            "action_if_exceeded": "RECLEAN REQUIRED - Investigation needed"
        },
        "clean_hold_time": {
            "description": "Time between cleaning completion and next use",
            "typical_values_hours": {"reactor": 72, "dryer": 168, "tank": 168, "filler": 24},
            "validation_requirements": "Must be validated with microbiological testing",
            "action_if_exceeded": "RECLEAN REQUIRED - Microbiological testing required"
        }
    }
    return {"success": True, "data": hold_times, "reference": "APIC Cleaning Validation Guide Section 9.7"}


@router.get("/maco-guidance")
def get_maco_guidance():
    """Section 4.2 - Get MACO calculation guidance - PUBLIC"""
    methods = {
        "10ppm": {
            "formula": "MACO = 0.00001 × MBS (mg)",
            "when_to_use": "General limit when no toxicology data available",
            "safety_factor": "10 ppm"
        },
        "TDD": {
            "formula": "MACO = (Min TDD Previous × MBS Next) / (SF × Max TDD Next)",
            "when_to_use": "When therapeutic daily dose is known",
            "safety_factor": "1000 for oral products"
        },
        "ADE_PDE": {
            "formula": "MACO = (ADE Previous × MBS Next) / (Max TDD Next)",
            "when_to_use": "When toxicology data is available",
            "safety_factor": "Based on NOAEL/LOAEL"
        }
    }
    return {"success": True, "data": methods, "reference": "APIC Cleaning Validation Guide Section 4.2"}


@router.get("/faq")
def get_all_faq():
    """Get all FAQs with answers - PUBLIC"""
    faqs = [
        {"id": "Q1", "question": "When should a company validate/revalidate cleaning procedures?", 
         "answer": "Revalidation is required when there are changes to cleaning procedure, equipment, product, or analytical method. Periodic evaluation (typically annually) is recommended."},
        {"id": "Q2", "question": "What number of cleans should be run in order to validate a cleaning procedure?",
         "answer": "Generally three consecutive successful replicates are required."},
        {"id": "Q3", "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be dirty before cleaning?",
         "answer": "YES. Dirty Hold Time (DHT) should be validated."},
        {"id": "Q4", "question": "Is it necessary to validate a maximum time allowed for a piece of equipment to be left clean before re-use?",
         "answer": "YES. Clean Hold Time (CHT) should be validated if there is any risk of contamination."},
        {"id": "Q5", "question": "Is it necessary to include microbiological testing in cleaning validation?",
         "answer": "YES if water is used for final cleaning or for biotech/parenteral products."},
        {"id": "Q6", "question": "Which analytical methods should be used in cleaning validation studies?",
         "answer": "Any method suitable for intended use (HPLC, GC, TLC, TOC, dry residue, conductivity, pH)."},
        {"id": "Q7", "question": "Do we have to wait for swab and rinse samples to be approved prior using the equipment for production?",
         "answer": "During cleaning validation studies it is recommended to wait for completion of all planned tests."},
        {"id": "Q8", "question": "What is the maximum time allowed after cleaning with water as last rinse?",
         "answer": "Equipment should not be left with water in it after cleaning."},
        {"id": "Q9", "question": "Is it possible that deterioration of equipment may take place over time, invalidating original validation results?",
         "answer": "Yes, equipment materials should be evaluated for durability over time as part of preventative maintenance program."},
        {"id": "Q10", "question": "If a company has validated a worst case scenario, should they also validate a 'less' worst case?",
         "answer": "For operational reasons it may be beneficial to validate a 'less' stringent cleaning procedure for some products."}
    ]
    return {"success": True, "count": len(faqs), "data": faqs}