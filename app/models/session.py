from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
from ..models.cleaning_process import CleaningProcess
from ..models.product import Product
from ..models.standard_prep import StandardPrep
from ..models.swab_result import SwabResult
from ..models.rinse_result import RinseResult
from ..models.session_equipment import SessionEquipment


class ValidationSession(Base):
    __tablename__ = "validation_sessions"
    __table_args__ = (
        Index('idx_validation_sessions_previous_product', 'previous_product_id'),
        Index('idx_validation_sessions_next_product', 'next_product_id'),
        Index('idx_validation_sessions_process', 'process_id'),
        Index('idx_validation_sessions_status', 'status'),
        Index('idx_validation_sessions_code', 'session_code'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String, unique=True, nullable=False)
    status = Column(String, default="DRAFT")
    extra_area_percentage = Column(Float, default=0)
    total_surface_area = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    previous_product_id = Column(Integer, ForeignKey("products.id"))
    next_product_id = Column(Integer, ForeignKey("products.id"))
    
    # NEW: process_id for cleaning process relationship
    process_id = Column(Integer, ForeignKey("cleaning_processes.id"), nullable=True)
    
    previous_product = relationship("Product", foreign_keys=[previous_product_id])
    next_product = relationship("Product", foreign_keys=[next_product_id])
    process = relationship("CleaningProcess", foreign_keys=[process_id])
    
    maco_10ppm = Column(Float, nullable=True)
    maco_tdd = Column(Float, nullable=True)
    maco_ade_pde = Column(Float, nullable=True)
    lowest_maco = Column(Float, nullable=True)
    
    swab_limit_mg = Column(Float, nullable=True)
    swab_limit_ppm = Column(Float, nullable=True)
    
    rinse_limit_mg = Column(Float, nullable=True)
    rinse_limit_ppm = Column(Float, nullable=True)
    rinse_volume_loq = Column(Float, nullable=True)
    rinse_volume_10ppm = Column(Float, nullable=True)
    
    standard_prep = relationship("StandardPrep", back_populates="session", uselist=False)
    swab_results = relationship("SwabResult", back_populates="session")
    rinse_results = relationship("RinseResult", back_populates="session")
    session_equipment = relationship("SessionEquipment", back_populates="session")