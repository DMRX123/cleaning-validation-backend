from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class CleaningLevelEnum(str, enum.Enum):
    LEVEL_0 = "LEVEL_0"  # Visual inspection only
    LEVEL_1 = "LEVEL_1"  # Visual + recommended analytical
    LEVEL_2 = "LEVEL_2"  # Visual + mandatory analytical

class CleaningLevel(Base):
    __tablename__ = "cleaning_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(SQLEnum(CleaningLevelEnum), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    # Requirements
    requires_visual_inspection = Column(Boolean, default=True)
    requires_analytical_testing = Column(Boolean, default=False)
    requires_microbiological_testing = Column(Boolean, default=False)
    requires_validation = Column(Boolean, default=False)
    
    # Limits
    max_residue_ppm = Column(Float, nullable=True)
    safety_factor = Column(Float, default=1.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignments = relationship("CleaningLevelAssignment", back_populates="level")

class CleaningLevelAssignment(Base):
    __tablename__ = "cleaning_level_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("cleaning_levels.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    
    # Context
    previous_step = Column(Integer, nullable=True)  # Synthetic step number
    next_step = Column(Integer, nullable=True)
    same_synthetic_chain = Column(Boolean, default=False)
    
    justification = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    level = relationship("CleaningLevel", back_populates="assignments")
    product = relationship("Product")
    equipment = relationship("Equipment")