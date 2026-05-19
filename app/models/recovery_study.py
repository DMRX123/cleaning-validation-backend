from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class RecoveryStudy(Base):
    """Section 8.3 - Recovery study data for different MOCs"""
    __tablename__ = "recovery_studies"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_of_construction = Column(String, nullable=False)
    recovery_percent = Column(Float, nullable=False)
    correction_factor = Column(Float, nullable=False)
    study_date = Column(DateTime, nullable=False)
    report_reference = Column(String, nullable=True)
    is_valid = Column(Boolean, default=True)
    valid_until = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", foreign_keys=[product_id])