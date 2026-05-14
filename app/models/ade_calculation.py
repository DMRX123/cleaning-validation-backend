from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ADECalculation(Base):
    """Section 4.2.1.1 - ADE/PDE calculation from toxicology data"""
    __tablename__ = "ade_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Input parameters
    noael_mg_per_kg = Column(Float, nullable=True)  # NOAEL in mg/kg/day
    loael_mg_per_kg = Column(Float, nullable=True)  # LOAEL in mg/kg/day
    ld50_mg_per_kg = Column(Float, nullable=True)   # LD50 in mg/kg
    body_weight_kg = Column(Float, default=50.0)    # Standard adult body weight
    
    # Uncertainty factors (F1-F5)
    uf1 = Column(Float, default=1.0)  # Interspecies extrapolation
    uf2 = Column(Float, default=10.0) # Interindividual variability
    uf3 = Column(Float, default=10.0) # Subchronic to chronic
    uf4 = Column(Float, default=1.0)  # Severity of effect
    uf5 = Column(Float, default=1.0)  # Database completeness
    
    # Modifying factor
    modifying_factor = Column(Float, default=1.0)
    
    # Pharmacokinetic adjustment
    pk_adjustment = Column(Float, default=1.0)
    
    # Calculated values
    calculated_ade_mg_per_day = Column(Float, nullable=True)
    calculation_method = Column(String, nullable=True)  # NOAEL, LOAEL, LD50, TTC
    calculation_justification = Column(Text, nullable=True)
    
    # Route of administration
    route = Column(String, default="oral")  # oral, parenteral, topical
    
    # Status
    is_approved = Column(Integer, default=0)
    reviewed_by = Column(String, nullable=True)
    reviewed_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id])