from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class OperatorQualification(Base):
    """Section 11 - Operator qualification records"""
    __tablename__ = "operator_qualifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Eyesight requirements
    eyesight_certified = Column(Boolean, default=False)
    eyesight_certified_date = Column(DateTime, nullable=True)
    eyesight_certified_by = Column(String, nullable=True)
    left_eye_vision = Column(String, nullable=True)
    right_eye_vision = Column(String, nullable=True)
    
    # Color blindness
    color_blindness_test_passed = Column(Boolean, default=False)
    color_blindness_test_date = Column(DateTime, nullable=True)
    color_blindness_test_type = Column(String, default="Ishihara")
    
    # Training
    training_completed = Column(Boolean, default=False)
    training_date = Column(DateTime, nullable=True)
    training_duration_hours = Column(Float, nullable=True)
    trainer_name = Column(String, nullable=True)
    training_scores = Column(Float, nullable=True)
    
    # Practical demonstration
    practical_demo_passed = Column(Boolean, default=False)
    practical_demo_date = Column(DateTime, nullable=True)
    practical_demo_equipment = Column(Text, nullable=True)
    assessed_by = Column(String, nullable=True)
    
    # Qualification validity
    qualification_valid_until = Column(DateTime, nullable=True)
    qualified_by = Column(String, nullable=True)
    qualification_certificate_no = Column(String, nullable=True)
    
    # Re-qualification
    last_requalification_date = Column(DateTime, nullable=True)
    requalification_due_date = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id])