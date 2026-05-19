from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class ValidationReport(Base):
    """Store generated validation reports with actual results"""
    __tablename__ = "validation_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String, unique=True, nullable=False)
    session_id = Column(Integer, ForeignKey("validation_sessions.id"), nullable=False)
    
    # Report metadata
    report_date = Column(DateTime, nullable=False)
    prepared_by = Column(String, nullable=False)
    reviewed_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    
    # Summary statistics
    total_swab_samples = Column(Integer, default=0)
    total_rinse_samples = Column(Integer, default=0)
    passed_swab_samples = Column(Integer, default=0)
    passed_rinse_samples = Column(Integer, default=0)
    overall_pass = Column(Boolean, default=False)
    
    # Actual results summary (JSON)
    swab_results_summary = Column(JSON, nullable=True)
    rinse_results_summary = Column(JSON, nullable=True)
    
    # Conclusions
    conclusion = Column(Text, nullable=True)
    deviations = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="DRAFT")
    pdf_path = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    session = relationship("ValidationSession", foreign_keys=[session_id])