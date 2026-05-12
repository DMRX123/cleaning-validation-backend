# app/models/bracketing.py - FIXED
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class BracketingGroup(Base):
    __tablename__ = "bracketing_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)
    cleaning_procedure_class = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    products = relationship("BracketingProduct", back_populates="group")
    worst_case = relationship("BracketingWorstCase", back_populates="group", uselist=False)

class BracketingProduct(Base):
    __tablename__ = "bracketing_products"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("bracketing_groups.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    rating_hardest_to_clean = Column(Integer, default=1)
    rating_solubility = Column(Integer, default=1)
    rating_toxicity = Column(Integer, default=1)
    rating_dose = Column(Integer, default=1)
    
    total_rating = Column(Integer, default=0)
    is_worst_case = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("BracketingGroup", back_populates="products")
    product = relationship("Product", back_populates="bracketing_products")

class BracketingWorstCase(Base):
    __tablename__ = "bracketing_worst_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("bracketing_groups.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    selection_justification = Column(String, nullable=False)
    validation_completed = Column(Boolean, default=False)
    validation_session_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("BracketingGroup", back_populates="worst_case")
    product = relationship("Product")