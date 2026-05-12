from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class MicrobiologicalLimit(Base):
    __tablename__ = "microbiological_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    product_type = Column(String, nullable=False)  # "oral", "parenteral", "topical"
    
    total_germ_count_limit = Column(Float, nullable=False)  # CFU/dm² or CFU/ml
    yeast_mold_limit = Column(Float, nullable=True)  # CFU/dm²
    endotoxin_limit = Column(Float, nullable=True)  # EU/ml (for parenteral)
    
    sampling_method = Column(String, nullable=False)  # "swab", "rinse", "contact plate"
    sampling_frequency = Column(String, nullable=False)  # "every batch", "weekly", "monthly"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment")
    results = relationship("MicrobiologicalResult", back_populates="limit")

class MicrobiologicalResult(Base):
    __tablename__ = "microbiological_results"
    
    id = Column(Integer, primary_key=True, index=True)
    limit_id = Column(Integer, ForeignKey("microbiological_limits.id"))
    session_id = Column(Integer, ForeignKey("validation_sessions.id"))
    
    sample_location = Column(String, nullable=False)
    sample_date = Column(DateTime, nullable=False)
    
    total_germ_count = Column(Float, nullable=True)
    yeast_mold_count = Column(Float, nullable=True)
    endotoxin_value = Column(Float, nullable=True)
    
    is_acceptable = Column(Boolean, default=False)
    reported = Column(String, nullable=True)
    
    analyst = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    limit = relationship("MicrobiologicalLimit", back_populates="results")
    session = relationship("ValidationSession")