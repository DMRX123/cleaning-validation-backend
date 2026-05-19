from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class FMEARiskAssessment(Base):
    """Section 8.1 - FMEA risk assessment for sampling points"""
    __tablename__ = "fmea_risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    failure_mode = Column(String, nullable=False)
    location_description = Column(String, nullable=True)
    severity = Column(Integer, nullable=False)
    occurrence = Column(Integer, nullable=False)
    detection = Column(Integer, nullable=False)
    rpn = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    is_sampling_point = Column(Boolean, default=False)
    sampling_method = Column(String, default="swab")
    sampling_area_cm2 = Column(Float, default=100.0)
    justification = Column(Text, nullable=True)
    mitigation_controls = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    equipment = relationship("Equipment", foreign_keys=[equipment_id])