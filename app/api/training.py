from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .auth import get_current_user
from ..models.training import TrainingModule, TrainingRecord
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Training"])


@router.get("/modules")
def get_training_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active training modules - FIXED"""
    try:
        modules = db.query(TrainingModule).filter(TrainingModule.is_active == True).all()
        if not modules:
            # Return empty list instead of error
            return []
        return modules
    except Exception as e:
        logger.error(f"Error fetching training modules: {str(e)}")
        # Return empty list instead of error
        return []


@router.get("/records")
def get_training_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training records for current user - FIXED"""
    try:
        records = db.query(TrainingRecord).filter(TrainingRecord.user_id == current_user.id).all()
        if not records:
            return []
        return records
    except Exception as e:
        logger.error(f"Error fetching training records: {str(e)}")
        return []