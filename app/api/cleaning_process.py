from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .auth import get_current_user  # CHANGED
from ..models.user import User
from ..services.cleaning_process_service import CleaningProcessService
from ..services.cleaning_capability_service import CleaningCapabilityService
from ..schemas.cleaning_process import (
    CleaningProcessCreate, CleaningProcessResponse,
    CleaningParameterCreate, CleaningExecutionCreate,
    CleaningCapabilityRequest, CleaningCapabilityResponse
)

router = APIRouter(prefix="/cleaning-process", tags=["Cleaning Process Control"])

# ============================================
# CLEANING PROCESS DEFINITION
# ============================================

@router.post("/create", response_model=CleaningProcessResponse)
def create_cleaning_process(
    process_data: CleaningProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Create a new cleaning process definition
    Includes system boundaries, cleaning agents, process steps
    """
    try:
        process = CleaningProcessService.create_process(db, process_data)
        return process
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{process_id}")
def get_cleaning_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Get complete cleaning process with parameters and executions
    """
    result = CleaningProcessService.get_process_with_parameters(db, process_id)
    if not result:
        raise HTTPException(status_code=404, detail="Process not found")
    return result

# ============================================
# CLEANING PARAMETERS
# ============================================

@router.post("/{process_id}/parameters")
def add_cleaning_parameter(
    process_id: int,
    param_data: CleaningParameterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Add critical parameters to cleaning process
    (Temperature, Flow rate, Pressure, Duration, Concentration)
    """
    try:
        parameter = CleaningProcessService.add_parameter(db, process_id, param_data)
        return {
            "success": True,
            "parameter_id": parameter.id,
            "parameter_name": parameter.parameter_name,
            "message": f"Parameter {parameter.parameter_name} added successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# CLEANING EXECUTION RECORDING
# ============================================

@router.post("/execute")
def record_cleaning_execution(
    execution_data: CleaningExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Record actual cleaning execution parameters
    Validates against defined specifications
    """
    try:
        execution = CleaningProcessService.record_execution(db, execution_data)
        
        status = "PASS" if execution.all_parameters_acceptable else "FAIL"
        
        return {
            "success": True,
            "execution_id": execution.id,
            "execution_date": execution.execution_date,
            "status": status,
            "parameter_status": {
                "temperature": "OK" if execution.temperature_within_spec else "OUT OF SPEC",
                "flow_rate": "OK" if execution.flow_rate_within_spec else "OUT OF SPEC",
                "pressure": "OK" if execution.pressure_within_spec else "OUT OF SPEC",
                "duration": "OK" if execution.duration_within_spec else "OUT OF SPEC"
            },
            "all_parameters_acceptable": execution.all_parameters_acceptable,
            "message": "Execution recorded successfully" if execution.all_parameters_acceptable else "WARNING: Some parameters out of specification"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# PROCESS CAPABILITY ANALYSIS
# ============================================

@router.post("/capability", response_model=CleaningCapabilityResponse)
def analyze_process_capability(
    request: CleaningCapabilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Analyze cleaning process capability
    Calculates mean, spread, Cpk, and distance from MACO
    Determines if process is adequately controlled
    """
    result = CleaningCapabilityService.calculate_process_capability(
        db, request.process_id, request.historical_executions_count
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

# ============================================
# PROCESS HISTORY
# ============================================

@router.get("/{process_id}/executions")
def get_process_executions(
    process_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Get execution history for a cleaning process
    """
    from ..models.cleaning_process import CleaningExecution
    
    executions = db.query(CleaningExecution).filter(
        CleaningExecution.process_id == process_id
    ).order_by(CleaningExecution.execution_date.desc()).limit(limit).all()
    
    return {
        "process_id": process_id,
        "total_executions": db.query(CleaningExecution).filter(CleaningExecution.process_id == process_id).count(),
        "executions": [
            {
                "id": e.id,
                "execution_date": e.execution_date,
                "executed_by": e.executed_by,
                "temperature_c": e.actual_temperature_c,
                "flow_rate_lpm": e.actual_flow_rate_lpm,
                "pressure_bar": e.actual_pressure_bar,
                "duration_min": e.actual_duration_min,
                "all_parameters_acceptable": e.all_parameters_acceptable,
                "deviations": e.deviations
            }
            for e in executions
        ]
    }

# ============================================
# PROCESS VALIDATION STATUS
# ============================================

@router.post("/{process_id}/validate")
def validate_cleaning_process(
    process_id: int,
    validation_protocol_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Section 6.0 - Mark cleaning process as validated after successful qualification
    """
    from ..models.cleaning_process import CleaningProcess
    from datetime import datetime
    
    process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    process.is_validated = True
    process.validation_protocol_id = validation_protocol_id
    process.validation_date = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "process_id": process_id,
        "is_validated": True,
        "validation_date": process.validation_date,
        "message": "Cleaning process marked as validated"
    }