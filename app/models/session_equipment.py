from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class SessionEquipment(Base):
    __tablename__ = "session_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    rinse_volume_applied = Column(Float, nullable=True)
    
    session = relationship("ValidationSession", back_populates="session_equipment")
    equipment = relationship("Equipment")