from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, Float, Float  # Add Float here
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class TrainingModule(Base):
    __tablename__ = "training_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    module_code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # "Cleaning", "Sampling", "Analytical", "Safety"
    
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrainingRecord(Base):
    __tablename__ = "training_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(Integer, ForeignKey("training_modules.id"))
    
    training_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    
    trainer = Column(String, nullable=True)
    score = Column(Float, nullable=True)  # Now Float is defined
    is_passed = Column(Boolean, default=False)
    
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    module = relationship("TrainingModule")
