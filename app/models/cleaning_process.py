from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class CleaningTypeEnum(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATED_CIP = "automated_cip"
    AUTOMATED_COP = "automated_cop"
    SEMI_AUTOMATED = "semi_automated"

class CleaningProcess(Base):
    """
    Section 6.0 - Control of Cleaning Process
    Tracks complete cleaning process definition and parameters
    """
    __tablename__ = "cleaning_processes"
    
    id = Column(Integer, primary_key=True, index=True)
    process_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Cleaning type
    cleaning_type = Column(SQLEnum(CleaningTypeEnum), nullable=False)
    
    # System boundaries (Section 6.0 point 1)
    system_boundaries = Column(Text, nullable=True)  # JSON string of equipment included
    
    # Cleaning agents/solvents (Section 6.0 point 2)
    cleaning_agents = Column(Text, nullable=True)  # JSON: [{"name": "Water", "concentration": 100, "volume_l": 500}]
    solvents_used = Column(Text, nullable=True)    # JSON list of solvents
    
    # Process steps sequence (Section 6.0 point 5)
    process_steps = Column(Text, nullable=True)    # JSON: [{"step": 1, "action": "pre-rinse", "duration_min": 10}, ...]
    
    # Equipment used
    equipment_ids = Column(Text, nullable=True)    # JSON list of equipment IDs
    
    # Control measures
    has_in_process_analysis = Column(Boolean, default=False)
    in_process_analysis_methods = Column(Text, nullable=True)  # JSON list
    
    # Parameter limits
    min_temperature_c = Column(Float, nullable=True)
    max_temperature_c = Column(Float, nullable=True)
    min_flow_rate_lpm = Column(Float, nullable=True)
    max_flow_rate_lpm = Column(Float, nullable=True)
    min_pressure_bar = Column(Float, nullable=True)
    max_pressure_bar = Column(Float, nullable=True)
    min_duration_min = Column(Float, nullable=True)
    max_duration_min = Column(Float, nullable=True)
    
    # Validation status
    is_validated = Column(Boolean, default=False)
    validation_protocol_id = Column(Integer, nullable=True)
    validation_date = Column(DateTime, nullable=True)
    
    # SOP reference
    sop_reference = Column(String, nullable=True)
    sop_version = Column(String, nullable=True)
    
    # Training requirements
    training_required = Column(Boolean, default=True)
    training_module_ids = Column(Text, nullable=True)  # JSON list
    
    # Status
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parameters = relationship("CleaningParameter", back_populates="process")
    executions = relationship("CleaningExecution", back_populates="process")


class CleaningParameter(Base):
    """
    Section 6.0 - Critical cleaning parameters tracking
    """
    __tablename__ = "cleaning_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("cleaning_processes.id"))
    
    parameter_name = Column(String, nullable=False)  # temperature, flow_rate, pressure, duration, concentration
    parameter_unit = Column(String, nullable=False)  # °C, L/min, bar, min, %
    
    target_value = Column(Float, nullable=True)
    min_acceptable = Column(Float, nullable=False)
    max_acceptable = Column(Float, nullable=False)
    
    is_critical = Column(Boolean, default=True)
    is_controlled_automatically = Column(Boolean, default=False)
    
    # For manual cleaning
    measurement_method = Column(String, nullable=True)
    measurement_frequency = Column(String, nullable=True)  # every batch, daily, weekly
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    process = relationship("CleaningProcess", back_populates="parameters")


class CleaningExecution(Base):
    """
    Section 6.0 - Actual cleaning execution records
    """
    __tablename__ = "cleaning_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("cleaning_processes.id"))
    session_id = Column(Integer, ForeignKey("validation_sessions.id"), nullable=True)
    
    execution_date = Column(DateTime, nullable=False)
    executed_by = Column(String, nullable=False)
    
    # Actual parameters recorded
    actual_temperature_c = Column(Float, nullable=True)
    actual_flow_rate_lpm = Column(Float, nullable=True)
    actual_pressure_bar = Column(Float, nullable=True)
    actual_duration_min = Column(Float, nullable=True)
    actual_concentration_percent = Column(Float, nullable=True)
    
    # Parameter status
    temperature_within_spec = Column(Boolean, default=True)
    flow_rate_within_spec = Column(Boolean, default=True)
    pressure_within_spec = Column(Boolean, default=True)
    duration_within_spec = Column(Boolean, default=True)
    
    # Overall status
    all_parameters_acceptable = Column(Boolean, default=True)
    
    # Deviations
    deviations = Column(Text, nullable=True)
    deviation_justification = Column(Text, nullable=True)
    
    # In-process analysis results
    in_process_results = Column(Text, nullable=True)  # JSON
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    process = relationship("CleaningProcess", back_populates="executions")