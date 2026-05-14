from pydantic import BaseModel
from typing import Optional, List

class GuidanceQuestionResponse(BaseModel):
    question_id: str
    question: str
    answer: str
    guideline_section: str

class RevalidationCheckRequest(BaseModel):
    protocol_id: int
    change_type: str  # "cleaning_procedure", "equipment", "product", "detergent"
    change_description: str

class RevalidationCheckResponse(BaseModel):
    revalidation_required: bool
    severity: str  # HIGH, MEDIUM, LOW
    reason: str
    recommended_actions: List[str]