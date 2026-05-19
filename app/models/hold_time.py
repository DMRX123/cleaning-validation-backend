from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class DirtyHoldTime(Base):
    """APIC Section 9.7 - Dirty Hold Time (DHT)"""
    __tablename__ = "dirty_hold_times"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    # equipment_name REMOVED - use equipment relationship instead
    product_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=False)
    
    end_of_batch_time = Column(DateTime, nullable=False)
    cleaning_start_time = Column(DateTime, nullable=False)
    actual_dht_hours = Column(Float, nullable=False)
    
    max_validated_dht_hours = Column(Float, nullable=False)
    is_within_limit = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    
    investigation_required = Column(Boolean, default=False)
    investigation_notes = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    equipment = relationship("Equipment", foreign_keys=[equipment_id])


class CleanHoldTime(Base):
    """APIC Section 9.7 - Clean Hold Time (CHT)"""
    __tablename__ = "clean_hold_times"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    # equipment_name REMOVED
    cleaning_completion_time = Column(DateTime, nullable=False)
    next_use_time = Column(DateTime, nullable=False)
    actual_cht_hours = Column(Float, nullable=False)
    
    max_validated_cht_hours = Column(Float, nullable=False)
    is_within_limit = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    
    storage_conditions = Column(String, default="Covered, dry, room temperature")
    microbiological_testing_done = Column(Boolean, default=False)
    microbiological_result = Column(String, nullable=True)
    
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    equipment = relationship("Equipment", foreign_keys=[equipment_id])


class HoldTimeValidation(Base):
    """APIC Section 9.7 - Hold Time Validation Records"""
    __tablename__ = "hold_time_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    hold_type = Column(String, nullable=False)  # "DHT" or "CHT"
    validated_hours = Column(Float, nullable=False)
    tested_hours = Column(Float, nullable=True)
    
    validation_protocol_id = Column(Integer, nullable=True)
    validation_report_id = Column(Integer, nullable=True)
    
    number_of_successful_runs = Column(Integer, default=0)
    required_runs = Column(Integer, default=3)
    is_validated = Column(Boolean, default=False)
    
    validation_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    study_conditions = Column(Text, nullable=True)
    conclusions = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    equipment = relationship("Equipment", foreign_keys=[equipment_id])
    product = relationship("Product", foreign_keys=[product_id])