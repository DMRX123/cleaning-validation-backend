# app/models/dosage_form.py - COMPLETE NEW FILE

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class DosageFormEnum(str, enum.Enum):
    """All dosage forms as per USP/EP"""
    # Solid Dosage Forms
    TABLET = "tablet"
    CAPSULE = "capsule"
    POWDER = "powder"
    GRANULE = "granule"
    PELLET = "pellet"
    
    # Liquid Dosage Forms
    ORAL_SOLUTION = "oral_solution"
    ORAL_SUSPENSION = "oral_suspension"
    SYRUP = "syrup"
    ELIXIR = "elixir"
    DROPS = "drops"
    
    # Semi-Solid Dosage Forms
    CREAM = "cream"
    OINTMENT = "ointment"
    GEL = "gel"
    LOTION = "lotion"
    PASTE = "paste"
    
    # Sterile Dosage Forms
    INJECTABLE = "injectable"
    INFUSION = "infusion"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    NASAL = "nasal"
    INHALATION = "inhalation"
    
    # Other
    TRANSDERMAL = "transdermal"
    SUPPOSITORY = "suppository"
    VACCINE = "vaccine"

class PlantTypeEnum(str, enum.Enum):
    API_PLANT = "api_plant"
    FORMULATION_OSD = "formulation_osd"
    FORMULATION_STERILE = "formulation_sterile"
    FORMULATION_LIQUID = "formulation_liquid"
    FORMULATION_OPHTHALMIC = "formulation_ophthalmic"
    FORMULATION_TOPICAL = "formulation_topical"
    FORMULATION_INHALATION = "formulation_inhalation"
    BIOTECH = "biotech"

class DosageForm(Base):
    """Dosage form master data with specific cleaning requirements"""
    __tablename__ = "dosage_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(SQLEnum(DosageFormEnum), unique=True, nullable=False)
    plant_type = Column(SQLEnum(PlantTypeEnum), nullable=False)
    
    # Cleaning requirements
    requires_sterility = Column(Boolean, default=False)
    requires_endotoxin_testing = Column(Boolean, default=False)
    requires_particle_count = Column(Boolean, default=False)
    requires_visual_inspection = Column(Boolean, default=True)
    requires_microbiological_testing = Column(Boolean, default=True)
    
    # Limits specific to dosage form
    default_microbial_limit_cfu = Column(Float, nullable=True)
    default_endotoxin_limit_eu_ml = Column(Float, nullable=True)
    default_particle_limit = Column(Float, nullable=True)
    
    # Sampling method
    recommended_sampling_method = Column(String, default="swab")  # swab, rinse, contact_plate
    
    # Description
    description = Column(Text, nullable=True)
    reference = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    products = relationship("ProductDosageForm", back_populates="dosage_form")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code.value if self.code else None,
            "plant_type": self.plant_type.value if self.plant_type else None,
            "requires_sterility": self.requires_sterility,
            "requires_endotoxin_testing": self.requires_endotoxin_testing,
            "requires_microbiological_testing": self.requires_microbiological_testing,
            "default_microbial_limit_cfu": self.default_microbial_limit_cfu,
            "default_endotoxin_limit_eu_ml": self.default_endotoxin_limit_eu_ml
        }


class ProductDosageForm(Base):
    """Link between products and dosage forms"""
    __tablename__ = "product_dosage_forms"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    dosage_form_id = Column(Integer, ForeignKey("dosage_forms.id"), nullable=False)
    
    # Batch size in product-specific units
    batch_quantity = Column(Float, nullable=True)
    batch_unit = Column(String, default="kg")  # kg, L, tablets, units
    
    # Daily dose range
    min_daily_dose = Column(Float, nullable=True)
    max_daily_dose = Column(Float, nullable=True)
    dose_unit = Column(String, default="mg")
    
    # Patient population
    is_pediatric = Column(Boolean, default=False)
    is_geriatric = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    dosage_form = relationship("DosageForm", back_populates="products")