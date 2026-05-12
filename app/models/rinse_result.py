from sqlalchemy import Column, Integer, String, Float, ForeignKey  # Add Float
from sqlalchemy.orm import relationship
from ..database import Base

class RinseResult(Base):
    __tablename__ = "rinse_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"))
    equipment_name = Column(String, nullable=False)
    actual_rinse_volume = Column(Float, nullable=False)  # L
    absorbance_sample = Column(Float, nullable=False)
    absorbance_std = Column(Float, nullable=False)
    result_mg_ml = Column(Float, nullable=True)
    result_ppm = Column(Float, nullable=True)
    reported = Column(String, nullable=True)
    
    session = relationship("ValidationSession", back_populates="rinse_results")
