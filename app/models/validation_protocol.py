from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ValidationProtocol(Base):
    __tablename__ = "validation_protocols"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    version = Column(Integer, default=1)
    status = Column(String, default="DRAFT")  # DRAFT, APPROVED, EXECUTED, CLOSED
    
    # Background (Section 9.1)
    background = Column(Text, nullable=True)
    
    # Purpose (Section 9.2)
    purpose = Column(Text, nullable=True)
    
    # Scope (Section 9.3)
    scope = Column(Text, nullable=True)
    
    # Equipment details
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    cleaning_procedure_id = Column(String, nullable=True)
    
    # Products
    previous_product_id = Column(Integer, ForeignKey("products.id"))
    next_product_id = Column(Integer, ForeignKey("products.id"))
    
    # Acceptance Criteria (Section 9.7)
    visual_acceptance = Column(String, default="No visible residue")
    chemical_acceptance_ppm = Column(Float, nullable=True)
    microbiological_acceptance = Column(Float, nullable=True)
    
    # Sampling Plan (Section 9.5)
    sampling_locations = Column(JSON, nullable=True)  # List of swab locations
    rinse_volume = Column(Float, nullable=True)  # Liters
    
    # Testing Plan (Section 9.6)
    analytical_methods = Column(JSON, nullable=True)
    
    # Responsibilities (Section 9.4)
    responsibilities = Column(JSON, nullable=True)
    
    # Training requirements (Section 9.8)
    training_requirements = Column(JSON, nullable=True)
    
    # Dirty/Clean Hold Times (Section 9.7)
    dirty_hold_time_hours = Column(Float, nullable=True)
    clean_hold_time_hours = Column(Float, nullable=True)
    
    # Approvals
    prepared_by = Column(String, nullable=True)
    prepared_date = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_date = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    
    # Section 9.9 - Deviations at protocol level
    protocol_deviations = Column(JSON, nullable=True)  # List of deviations
    
    # Section 9.10 - Revalidation strategy
    revalidation_strategy = Column(Text, nullable=True)
    revalidation_frequency_months = Column(Integer, default=12)
    last_revalidation_date = Column(DateTime, nullable=True)
    
    # Consecutive success tracking (Section 5.3.2)
    consecutive_passes_required = Column(Integer, default=3)
    consecutive_passes_achieved = Column(Integer, default=0)
    last_fail_date = Column(DateTime, nullable=True)
    validation_reset_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    equipment = relationship("Equipment")
    previous_product = relationship("Product", foreign_keys=[previous_product_id])
    next_product = relationship("Product", foreign_keys=[next_product_id])
    results = relationship("ProtocolExecutionResult", back_populates="protocol")

class ProtocolExecutionResult(Base):
    __tablename__ = "protocol_execution_results"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("validation_protocols.id"))
    execution_number = Column(Integer, nullable=False)  # 1, 2, 3 for replicates
    execution_date = Column(DateTime, nullable=False)
    
    # Results
    visual_result = Column(String, nullable=True)  # PASS/FAIL
    chemical_result_ppm = Column(Float, nullable=True)
    microbiological_result = Column(Float, nullable=True)
    
    overall_result = Column(String, nullable=True)  # PASS/FAIL
    
    deviations = Column(Text, nullable=True)
    investigator = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    protocol = relationship("ValidationProtocol", back_populates="results")