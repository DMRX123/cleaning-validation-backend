from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, CALCULATE
    entity = Column(String, nullable=False)  # Product, Equipment, Session
    entity_id = Column(Integer, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())