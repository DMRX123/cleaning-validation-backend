from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class SwabResult(Base):
    __tablename__ = "swab_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"))
    location_name = Column(String, nullable=False)
    absorbance_sample = Column(Float, nullable=False)
    absorbance_std = Column(Float, nullable=False)
    result_mg_ml = Column(Float, nullable=True)
    result_ppm = Column(Float, nullable=True)      # ← ALWAYS NUMBER (0 if below LOQ)
    reported = Column(String, nullable=True)        # ← "Below LOQ" or value as string
    below_loq = Column(Integer, default=0)          # ← NEW: 1 if below LOQ, 0 otherwise
    
    session = relationship("ValidationSession", back_populates="swab_results")