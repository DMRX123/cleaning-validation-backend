# app/models/product.py - COMPLETE FIXED VERSION
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from ..database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    min_batch_size = Column(Float, nullable=False)
    max_batch_size = Column(Float, nullable=False)
    ade_pde = Column(Float, nullable=False)
    min_dose = Column(Float, nullable=False)
    max_dose = Column(Float, nullable=False)
    swab_recovery = Column(Float, nullable=False)
    lod = Column(Float, nullable=False)
    loq = Column(Float, nullable=False)
    swab_dilution = Column(Float, nullable=False)
    swab_surface_area = Column(Float, default=0.01)
    solubility = Column(String, nullable=False)
    hardest_to_clean = Column(String, nullable=False)
    plant = Column(String, nullable=False)
    
    # Simple relationships without back_populates to avoid circular imports
    sessions_as_previous = relationship(
        "ValidationSession", 
        foreign_keys="ValidationSession.previous_product_id"
    )
    sessions_as_next = relationship(
        "ValidationSession", 
        foreign_keys="ValidationSession.next_product_id"
    )
    
    # Bracketing relationships
    bracketing_products = relationship("BracketingProduct", back_populates="product")
    
    def get_min_batch_max_dose_ratio(self):
        if self.max_dose and self.max_dose > 0:
            return (self.min_batch_size * 1000000) / self.max_dose
        return None
    
    def get_swab_limit_mg(self, maco_mg: float, total_surface_area: float) -> float:
        if total_surface_area > 0 and maco_mg and maco_mg > 0:
            result = (maco_mg * self.swab_surface_area) / total_surface_area
            recovery_factor = self.swab_recovery / 100 if self.swab_recovery > 0 else 1
            if recovery_factor > 0:
                result = result / recovery_factor
            return round(result, 6)
        return 0
    
    def get_swab_limit_ppm(self, maco_mg: float, total_surface_area: float) -> float:
        if total_surface_area > 0 and maco_mg and maco_mg > 0 and self.swab_dilution > 0:
            result = (maco_mg * self.swab_surface_area * 1000) / (total_surface_area * self.swab_dilution)
            recovery_factor = self.swab_recovery / 100 if self.swab_recovery > 0 else 1
            if recovery_factor > 0:
                result = result / recovery_factor
            return round(result, 2)
        return 0