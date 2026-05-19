from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class ProtocolTemplate(Base):
    """Store protocol templates - Section wise templates"""
    __tablename__ = "protocol_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String, unique=True, nullable=False)
    template_section = Column(String, nullable=False)
    content_html = Column(Text, nullable=True)
    content_json = Column(JSON, nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CleaningValidationProtocol(Base):
    """Master protocol record - stores generated protocol data"""
    __tablename__ = "cleaning_validation_protocols"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    revision = Column(String, default="R00")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    date_of_issue = Column(DateTime, nullable=False)
    location = Column(String, default="Indore")
    manufacturing_block = Column(String, nullable=True)
    batch_size_range = Column(String, nullable=True)
    
    prepared_by = Column(String, nullable=False)
    prepared_date = Column(DateTime, nullable=True)
    checked_by_production = Column(String, nullable=True)
    checked_by_production_date = Column(DateTime, nullable=True)
    checked_by_ppa = Column(String, nullable=True)
    checked_by_ppa_date = Column(DateTime, nullable=True)
    checked_by_engineering = Column(String, nullable=True)
    checked_by_engineering_date = Column(DateTime, nullable=True)
    checked_by_qc = Column(String, nullable=True)
    checked_by_qc_date = Column(DateTime, nullable=True)
    checked_by_qa = Column(String, nullable=True)
    checked_by_qa_date = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    
    campaign_max_batches = Column(Integer, default=10)
    campaign_max_days = Column(Integer, default=30)
    dht_hours = Column(Float, default=24.0)
    cht_days = Column(Integer, default=14)
    apply_recovery_correction = Column(Boolean, default=True)
    
    custom_introduction = Column(Text, nullable=True)
    custom_objective = Column(Text, nullable=True)
    custom_scope = Column(Text, nullable=True)
    custom_responsibilities = Column(Text, nullable=True)
    
    status = Column(String, default="DRAFT")
    pdf_path = Column(String, nullable=True)
    pdf_generated_at = Column(DateTime, nullable=True)
    
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", foreign_keys=[product_id])