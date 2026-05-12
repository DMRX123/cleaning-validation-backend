from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean  # Add Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class DirtyHoldTime(Base):
    __tablename__ = "dirty_hold_times"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    product_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=False)
    
    end_of_batch_time = Column(DateTime, nullable=False)
    cleaning_start_time = Column(DateTime, nullable=False)
    actual_dht_hours = Column(Float, nullable=False)
    
    max_validated_dht_hours = Column(Float, nullable=False)
    is_within_limit = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    
    investigation_required = Column(Boolean, default=False)
    investigation_notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment")

class CleanHoldTime(Base):
    __tablename__ = "clean_hold_times"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    
    cleaning_completion_time = Column(DateTime, nullable=False)
    next_use_time = Column(DateTime, nullable=False)
    actual_cht_hours = Column(Float, nullable=False)
    
    max_validated_cht_hours = Column(Float, nullable=False)
    is_within_limit = Column(Boolean, default=False)
    is_validated = Column(Boolean, default=False)
    
    storage_conditions = Column(String, nullable=True)  # e.g., "Covered, dry, room temp"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment")

class HoldTimeValidation(Base):
    __tablename__ = "hold_time_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    hold_type = Column(String, nullable=False)  # "DHT" or "CHT"
    validated_hours = Column(Float, nullable=False)
    
    validation_protocol_id = Column(Integer, nullable=True)
    validation_report_id = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True)
    expiry_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment")
    product = relationship("Product")
