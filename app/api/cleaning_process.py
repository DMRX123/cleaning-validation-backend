from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..services.cleaning_process_service import CleaningProcessService
from ..services.cleaning_capability_service import CleaningCapabilityService
from ..schemas.cleaning_process import (
    CleaningProcessCreate, CleaningProcessResponse,
    CleaningParameterCreate, CleaningExecutionCreate,
    CleaningCapabilityRequest, CleaningCapabilityResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cleaning Process Control"])


# ============================================
# ADDITIONAL SCHEMAS
# ============================================

class CleaningProcessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_validated: Optional[bool] = None
    is_active: Optional[bool] = None
    min_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None
    min_duration_min: Optional[float] = None
    max_duration_min: Optional[float] = None


# ============================================
# UPDATE ENDPOINTS FOR PARAMETERS & EXECUTIONS
# ============================================

class CleaningParameterUpdate(BaseModel):
    parameter_name: Optional[str] = None
    parameter_unit: Optional[str] = None
    target_value: Optional[float] = None
    min_acceptable: Optional[float] = None
    max_acceptable: Optional[float] = None
    is_critical: Optional[bool] = None
    measurement_method: Optional[str] = None
    measurement_frequency: Optional[str] = None


class CleaningExecutionUpdate(BaseModel):
    actual_temperature_c: Optional[float] = None
    actual_flow_rate_lpm: Optional[float] = None
    actual_pressure_bar: Optional[float] = None
    actual_duration_min: Optional[float] = None
    actual_concentration_percent: Optional[float] = None
    deviations: Optional[str] = None
    deviation_justification: Optional[str] = None


@router.put("/parameters/{parameter_id}")
def update_cleaning_parameter(parameter_id: int, data: CleaningParameterUpdate, db: Session = Depends(get_db)):
    """Update cleaning parameter by ID - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningParameter
        
        parameter = db.query(CleaningParameter).filter(CleaningParameter.id == parameter_id).first()
        if not parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(parameter, key, value)
        
        db.commit()
        db.refresh(parameter)
        
        return {
            "success": True,
            "message": "Parameter updated successfully",
            "data": parameter
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update parameter error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/execution/{execution_id}")
def update_cleaning_execution(execution_id: int, data: CleaningExecutionUpdate, db: Session = Depends(get_db)):
    """Update cleaning execution by ID - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningExecution, CleaningProcess
        
        execution = db.query(CleaningExecution).filter(CleaningExecution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution record not found")
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == execution.process_id).first()
        
        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(execution, key, value)
        
        # Re-validate parameters if values changed
        if process:
            temp_ok = True
            flow_ok = True
            pressure_ok = True
            duration_ok = True
            
            if execution.actual_temperature_c is not None:
                if process.min_temperature_c and execution.actual_temperature_c < process.min_temperature_c:
                    temp_ok = False
                if process.max_temperature_c and execution.actual_temperature_c > process.max_temperature_c:
                    temp_ok = False
            
            if execution.actual_flow_rate_lpm is not None:
                if process.min_flow_rate_lpm and execution.actual_flow_rate_lpm < process.min_flow_rate_lpm:
                    flow_ok = False
                if process.max_flow_rate_lpm and execution.actual_flow_rate_lpm > process.max_flow_rate_lpm:
                    flow_ok = False
            
            if execution.actual_pressure_bar is not None:
                if process.min_pressure_bar and execution.actual_pressure_bar < process.min_pressure_bar:
                    pressure_ok = False
                if process.max_pressure_bar and execution.actual_pressure_bar > process.max_pressure_bar:
                    pressure_ok = False
            
            if execution.actual_duration_min is not None:
                if process.min_duration_min and execution.actual_duration_min < process.min_duration_min:
                    duration_ok = False
                if process.max_duration_min and execution.actual_duration_min > process.max_duration_min:
                    duration_ok = False
            
            execution.temperature_within_spec = temp_ok
            execution.flow_rate_within_spec = flow_ok
            execution.pressure_within_spec = pressure_ok
            execution.duration_within_spec = duration_ok
            execution.all_parameters_acceptable = temp_ok and flow_ok and pressure_ok and duration_ok
        
        db.commit()
        db.refresh(execution)
        
        return {
            "success": True,
            "message": "Execution record updated successfully",
            "data": execution
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update execution error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GET ALL CLEANING PROCESSES - PUBLIC
# ============================================

@router.get("/")
def get_cleaning_processes(db: Session = Depends(get_db)):
    """Get all cleaning processes - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess
        processes = db.query(CleaningProcess).filter(CleaningProcess.is_active == True).all()
        return {
            "success": True,
            "count": len(processes),
            "processes": processes
        }
    except Exception as e:
        logger.error(f"Get cleaning processes error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
def get_all_cleaning_processes_including_inactive(db: Session = Depends(get_db)):
    """Get ALL cleaning processes (including inactive) - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess
        processes = db.query(CleaningProcess).all()
        return {
            "success": True,
            "count": len(processes),
            "processes": processes
        }
    except Exception as e:
        logger.error(f"Get all cleaning processes error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CLEANING PROCESS DEFINITION - PUBLIC
# ============================================

@router.post("/create", response_model=CleaningProcessResponse)
def create_cleaning_process(process_data: CleaningProcessCreate, db: Session = Depends(get_db)):
    """Create a new cleaning process - PUBLIC"""
    try:
        process = CleaningProcessService.create_process(db, process_data)
        return process
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{process_id}")
def get_cleaning_process(process_id: int, db: Session = Depends(get_db)):
    """Get cleaning process details - PUBLIC"""
    try:
        result = CleaningProcessService.get_process_with_parameters(db, process_id)
        if not result:
            raise HTTPException(status_code=404, detail="Process not found")
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cleaning process error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{process_id}")
def update_cleaning_process(process_id: int, data: CleaningProcessUpdate, db: Session = Depends(get_db)):
    """Update cleaning process - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(process, key, value)
        
        db.commit()
        db.refresh(process)
        
        return {"success": True, "message": "Process updated successfully", "process": process}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update cleaning process error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{process_id}")
def delete_cleaning_process(process_id: int, db: Session = Depends(get_db)):
    """Delete cleaning process and all related data - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess, CleaningParameter, CleaningExecution
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Delete related data
        db.query(CleaningParameter).filter(CleaningParameter.process_id == process_id).delete()
        db.query(CleaningExecution).filter(CleaningExecution.process_id == process_id).delete()
        
        db.delete(process)
        db.commit()
        
        return {"success": True, "message": "Cleaning process deleted successfully", "id": process_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete cleaning process error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/all")
def delete_all_cleaning_processes(db: Session = Depends(get_db)):
    """Delete ALL cleaning processes - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess, CleaningParameter, CleaningExecution
        
        db.query(CleaningParameter).delete()
        db.query(CleaningExecution).delete()
        count = db.query(CleaningProcess).delete()
        db.commit()
        
        return {"success": True, "message": f"Deleted {count} cleaning processes", "deleted_count": count}
    except Exception as e:
        logger.error(f"Delete all cleaning processes error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CLEANING PARAMETERS - PUBLIC
# ============================================

@router.post("/{process_id}/parameters")
def add_cleaning_parameter(process_id: int, param_data: CleaningParameterCreate, db: Session = Depends(get_db)):
    """Add cleaning parameter - PUBLIC"""
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


@router.delete("/parameters/{parameter_id}")
def delete_cleaning_parameter(parameter_id: int, db: Session = Depends(get_db)):
    """Delete cleaning parameter - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningParameter
        
        parameter = db.query(CleaningParameter).filter(CleaningParameter.id == parameter_id).first()
        if not parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        db.delete(parameter)
        db.commit()
        
        return {"success": True, "message": "Parameter deleted successfully", "id": parameter_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete parameter error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CLEANING EXECUTION RECORDING - PUBLIC
# ============================================

@router.post("/execute")
def record_cleaning_execution(execution_data: CleaningExecutionCreate, db: Session = Depends(get_db)):
    """Record cleaning execution - PUBLIC"""
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


@router.delete("/execution/{execution_id}")
def delete_cleaning_execution(execution_id: int, db: Session = Depends(get_db)):
    """Delete cleaning execution record - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningExecution
        
        execution = db.query(CleaningExecution).filter(CleaningExecution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution record not found")
        
        db.delete(execution)
        db.commit()
        
        return {"success": True, "message": "Execution record deleted", "id": execution_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete execution error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PROCESS CAPABILITY ANALYSIS - PUBLIC
# ============================================

@router.post("/capability")
def analyze_process_capability(request: CleaningCapabilityRequest, db: Session = Depends(get_db)):
    """Analyze cleaning process capability - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess
        
        # Check if process exists
        process = db.query(CleaningProcess).filter(CleaningProcess.id == request.process_id).first()
        if not process:
            return {
                "success": False,
                "error": f"Process with ID {request.process_id} not found",
                "message": "Please create a cleaning process first before analyzing capability",
                "suggestion": "Use POST /api/cleaning-process/create to create a process"
            }
        
        result = CleaningCapabilityService.calculate_process_capability(
            db, request.process_id, request.historical_executions_count
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "message": "Insufficient data for capability analysis",
                "suggestion": "Ensure at least 3 cleaning executions with validation results exist"
            }
        
        return {
            "success": True,
            "data": result,
            "message": "Process capability calculated successfully"
        }
    except Exception as e:
        logger.error(f"Process capability analysis error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to calculate process capability"
        }


# ============================================
# PROCESS HISTORY - PUBLIC
# ============================================

@router.get("/{process_id}/executions")
def get_process_executions(process_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Get process execution history - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningExecution
        
        executions = db.query(CleaningExecution).filter(
            CleaningExecution.process_id == process_id
        ).order_by(CleaningExecution.execution_date.desc()).limit(limit).all()
        
        return {
            "success": True,
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
    except Exception as e:
        logger.error(f"Get process executions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PROCESS VALIDATION STATUS - PUBLIC
# ============================================

@router.post("/{process_id}/validate")
def validate_cleaning_process(process_id: int, validation_protocol_id: int, db: Session = Depends(get_db)):
    """Mark cleaning process as validated - PUBLIC"""
    try:
        from ..models.cleaning_process import CleaningProcess
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate process error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))