# app/models/product.py - COMPLETE FINAL VERSION

from sqlalchemy import Column, Integer, String, Float, Boolean, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index('idx_products_plant', 'plant'),
        Index('idx_products_product_code', 'product_code'),
        Index('idx_products_plant_code', 'plant', 'product_code'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    product_code = Column(String, nullable=True)  # N, S3A, RI1A, HS10B
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
    
    # APIC Rating Fields
    toxicity_class = Column(Integer, default=3)
    potency_class = Column(Integer, default=3)
    cleanability_rating = Column(Integer, default=2)
    
    # Relationships
    sessions_as_previous = relationship(
        "ValidationSession", 
        foreign_keys="ValidationSession.previous_product_id"
    )
    sessions_as_next = relationship(
        "ValidationSession", 
        foreign_keys="ValidationSession.next_product_id"
    )
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
    
    @property
    def batch_size_display(self):
        if self.min_batch_size == self.max_batch_size:
            return f"{self.min_batch_size} Kg"
        return f"{self.min_batch_size} ± {self.max_batch_size - self.min_batch_size} Kg"
    
    @property
    def ade_display(self):
        return f"{self.ade_pde} µg"
    
    @property
    def tdd_display(self):
        return f"{self.min_dose} - {self.max_dose} mg"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "product_code": self.product_code,
            "batch_size_kg": self.min_batch_size,
            "ade_pde_ug": self.ade_pde,
            "min_dose_mg": self.min_dose,
            "max_dose_mg": self.max_dose,
            "solubility": self.solubility,
            "hardest_to_clean": self.hardest_to_clean,
            "plant": self.plant
        }