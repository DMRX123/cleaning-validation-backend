from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class SwabSamplingArea(Base):
    """Section 4.2.4 - Equipment segmentation for swab sampling"""
    __tablename__ = "swab_sampling_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"), nullable=True)
    
    area_name = Column(String, nullable=False)  # e.g., "Manhole area", "Bottom valve"
    surface_type = Column(String, nullable=False)  # Stainless steel, Glass lined, Teflon
    surface_area_dm2 = Column(Float, nullable=False)  # Area in dm²
    
    # Recovery factor for this specific surface type
    recovery_percent = Column(Float, default=100.0)
    
    # Is this a worst-case location?
    is_worst_case = Column(Integer, default=0)
    
    # Swab result for this area (if sampled)
    swab_result_id = Column(Integer, ForeignKey("swab_results.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment")
    session = relationship("ValidationSession")
    swab_result = relationship("SwabResult", foreign_keys=[swab_result_id])