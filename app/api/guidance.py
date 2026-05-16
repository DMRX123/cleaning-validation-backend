from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .auth import get_current_user
from ..services.guidance_service import GuidanceService
from ..schemas.guidance import GuidanceQuestionResponse, RevalidationCheckRequest, RevalidationCheckResponse

router = APIRouter(tags=["APIC Guidance"])

@router.get("/questions", response_model=List[GuidanceQuestionResponse])
def get_validation_questions(current_user = Depends(get_current_user)):
    return GuidanceService.get_all_questions()

@router.post("/revalidation-check", response_model=RevalidationCheckResponse)
def check_revalidation_needed(
    request: RevalidationCheckRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return GuidanceService.assess_revalidation(request)