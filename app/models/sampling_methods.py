# app/models/sampling_methods.py - COMPLETE ERROR-FREE VERSION

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class SamplingMethodEnum(str, enum.Enum):
    SWAB = "swab"
    RINSE = "rinse"
    CONTACT_PLATE = "contact_plate"
    DIRECT_INOCULATION = "direct_inoculation"
    AIR_SAMPLING = "air_sampling"

class SamplingLocation(Base):
    """Equipment sampling locations - critical for validation"""
    __tablename__ = "sampling_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    location_name = Column(String, nullable=False)
    location_description = Column(Text, nullable=True)
    
    # Location details
    surface_area_cm2 = Column(Float, nullable=True)
    is_hard_to_clean = Column(Boolean, default=False)
    is_worst_case = Column(Boolean, default=False)
    priority = Column(Integer, default=3)  # 1=highest, 5=lowest
    
    # Sampling method recommended
    recommended_method = Column(SQLEnum(SamplingMethodEnum), default=SamplingMethodEnum.SWAB)
    
    # Recovery factor for this specific location
    recovery_factor_percent = Column(Float, default=100.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    equipment = relationship("Equipment", foreign_keys=[equipment_id])
    sampling_results = relationship("SamplingResult", back_populates="location", cascade="all, delete-orphan")


class SamplingResult(Base):
    """Individual sampling results with method-specific data"""
    __tablename__ = "sampling_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("sampling_locations.id"), nullable=True)
    
    # Sampling details
    sampling_method = Column(SQLEnum(SamplingMethodEnum), nullable=False)
    sample_code = Column(String, nullable=False)
    sampling_date = Column(DateTime, nullable=False)
    sampled_by = Column(String, nullable=False)
    
    # Method-specific data
    swab_area_cm2 = Column(Float, nullable=True)
    rinse_volume_ml = Column(Float, nullable=True)
    contact_plate_size_cm2 = Column(Float, nullable=True)
    dilution_factor = Column(Float, default=1.0)
    
    # Analytical results
    absorbance_sample = Column(Float, nullable=True)
    absorbance_std = Column(Float, nullable=True)
    result_ppm = Column(Float, nullable=True)
    result_ug_per_swab = Column(Float, nullable=True)
    result_cfu_per_plate = Column(Float, nullable=True)
    
    # Microbiological results
    total_germ_count = Column(Float, nullable=True)
    yeast_mold_count = Column(Float, nullable=True)
    endotoxin_value = Column(Float, nullable=True)
    
    # Status
    is_acceptable = Column(Boolean, default=False)
    reported_value = Column(String, nullable=True)
    below_loq = Column(Boolean, default=False)
    
    # Deviations
    deviations = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ValidationSession", foreign_keys=[session_id])
    location = relationship("SamplingLocation", back_populates="sampling_results")