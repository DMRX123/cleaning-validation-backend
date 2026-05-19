from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class NitrosamineRiskAssessment(Base):
    """Section 13 - Nitrosamine risk assessment"""
    __tablename__ = "nitrosamine_risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Raw materials assessment
    secondary_amine_present = Column(Boolean, default=False)
    tertiary_amine_present = Column(Boolean, default=False)
    primary_amine_present = Column(Boolean, default=False)
    nitrite_in_raw_materials = Column(Boolean, default=False)
    recovered_solvents_used = Column(Boolean, default=False)
    
    # Process conditions
    nitrosating_agents_used = Column(Boolean, default=False)
    low_ph_conditions = Column(Boolean, default=False)
    high_temperature_used = Column(Boolean, default=False)
    temperature_threshold_c = Column(Float, nullable=True)
    
    # Water system
    water_nitrite_level_ppm = Column(Float, nullable=True)
    chloramines_in_water = Column(Boolean, default=False)
    water_source = Column(String, nullable=True)
    
    # Equipment
    shared_with_nitrosating_products = Column(Boolean, default=False)
    shared_equipment_ids = Column(Text, nullable=True)
    
    # Structural alert details
    amine_type = Column(String, nullable=True)
    has_nitro_group = Column(Boolean, default=False)
    has_amide_group = Column(Boolean, default=False)
    
    # Risk conclusion
    overall_risk_level = Column(String, default="Low")
    risk_justification = Column(Text, nullable=True)
    requires_confirmatory_testing = Column(Boolean, default=False)
    mitigation_plan = Column(Text, nullable=True)
    control_strategy = Column(Text, nullable=True)
    
    # Assessment metadata
    assessment_date = Column(DateTime, nullable=False)
    assessed_by = Column(String, nullable=False)
    reviewer = Column(String, nullable=True)
    report_reference = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", foreign_keys=[product_id])