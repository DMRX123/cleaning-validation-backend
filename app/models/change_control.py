from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ChangeControl(Base):
    __tablename__ = "change_controls"
    
    id = Column(Integer, primary_key=True, index=True)
    change_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "Cleaning Procedure", "Equipment", "Product", "Analytical Method"
    
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    
    # Impact assessment
    impact_on_cleaning = Column(String, nullable=True)
    impact_on_validation = Column(String, nullable=True)
    risk_assessment = Column(String, nullable=True)
    
    # Related entities
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    cleaning_procedure_id = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="PROPOSED")  # PROPOSED, REVIEW, APPROVED, IMPLEMENTED, CLOSED, REJECTED
    
    # Approvals
    proposed_by = Column(String, nullable=True)
    proposed_date = Column(DateTime, server_default=func.now())
    reviewed_by = Column(String, nullable=True)
    reviewed_date = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    
    # Implementation
    implementation_date = Column(DateTime, nullable=True)
    revalidation_required = Column(Boolean, default=False)
    revalidation_completed = Column(Boolean, default=False)
    
    closure_notes = Column(Text, nullable=True)
    closed_by = Column(String, nullable=True)
    closed_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    equipment = relationship("Equipment")
    product = relationship("Product")