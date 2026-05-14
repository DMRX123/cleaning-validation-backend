# app/models/equipment.py - COMPLETE FIXED VERSION with timestamps
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    equipment_id = Column(String, unique=True, nullable=False)
    capacity = Column(Float, nullable=True)
    surface_area = Column(Float, nullable=False)  # m²
    used_for = Column(String, nullable=False)
    cleaning_procedure = Column(String, nullable=False)
    plant = Column(String, nullable=False)
    
    # Timestamp columns
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())