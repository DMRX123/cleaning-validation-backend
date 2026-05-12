from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey  # Add Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class StandardPrep(Base):
    __tablename__ = "standard_preps"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"))
    wt_of_std = Column(Float, nullable=False)  # mg
    first_dilution = Column(Float, nullable=False)  # ml
    second_dilution = Column(Float, nullable=False)  # ml
    third_dilution = Column(Float, nullable=False)  # ml
    fourth_dilution = Column(Float, nullable=False)  # ml
    fifth_dilution = Column(Float, nullable=False)  # ml
    potency = Column(Float, nullable=False)  # %
    dilution_factor = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ValidationSession", back_populates="standard_prep")
    
    def calculate_dilution_factor(self):
        """Excel formula: =wtStd/firstDil * firstPip/firstDil * ..."""
        if any(v == 0 for v in [self.first_dilution, self.second_dilution, self.third_dilution, self.fourth_dilution, self.fifth_dilution]):
            return 0
        
        factor = (self.wt_of_std / self.first_dilution) * \
                 (self.first_dilution / self.first_dilution) * \
                 (self.second_dilution / self.second_dilution) * \
                 (self.third_dilution / self.third_dilution) * \
                 (self.fourth_dilution / self.fourth_dilution) * \
                 (self.fifth_dilution / self.fifth_dilution)
        
        factor = factor * (self.potency / 100)
        self.dilution_factor = round(factor, 6)
        return self.dilution_factor
