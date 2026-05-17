# app/models/formulation_equipment.py - COMPLETE ERROR-FREE VERSION

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class EquipmentCategoryEnum(str, enum.Enum):
    # OSD Equipment
    SIFTER = "sifter"
    GRANULATOR = "granulator"
    DRYER = "dryer"
    MILL = "mill"
    BLENDER = "blender"
    TABLET_PRESS = "tablet_press"
    COATER = "coater"
    CAPSULE_FILLER = "capsule_filler"
    
    # Liquid Equipment
    MIXING_TANK = "mixing_tank"
    STORAGE_TANK = "storage_tank"
    FILLING_MACHINE = "filling_machine"
    CAPPING_MACHINE = "capping_machine"
    
    # Sterile Equipment
    AUTOCLAVE = "autoclave"
    LAMINAR_AIRFLOW = "laminar_airflow"
    VIAL_FILLER = "vial_filler"
    LYOPHILIZER = "lyophilizer"
    RABS = "rabs"
    ISOLATOR = "isolator"
    
    # Common Equipment
    TRANSFER_LINE = "transfer_line"
    HOPPER = "hopper"
    SCOOP = "scoop"
    CONTAINER = "container"

class FormulationEquipment(Base):
    """Equipment with formulation-specific attributes"""
    __tablename__ = "formulation_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    category = Column(SQLEnum(EquipmentCategoryEnum), nullable=False)
    
    # Equipment specifics
    contact_parts = Column(Text, nullable=True)  # JSON list of contact parts
    non_contact_parts = Column(Text, nullable=True)  # JSON list of non-contact parts
    hard_to_clean_locations = Column(Text, nullable=True)  # JSON list
    
    # CIP/SIP capabilities
    has_cip = Column(Boolean, default=False)
    has_sip = Column(Boolean, default=False)
    cip_parameters = Column(Text, nullable=True)  # JSON of CIP parameters
    
    # Sampling points
    sampling_points_count = Column(Integer, default=0)
    worst_case_sampling_points = Column(Text, nullable=True)
    
    # Validation status
    is_validated_for_cleaning = Column(Boolean, default=False)
    last_validation_date = Column(DateTime, nullable=True)
    validation_due_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment", foreign_keys=[equipment_id])