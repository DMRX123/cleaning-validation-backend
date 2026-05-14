from sqlalchemy.orm import Session
from datetime import datetime
import json
from ..models.cleaning_process import CleaningProcess, CleaningParameter, CleaningExecution
from ..schemas.cleaning_process import CleaningProcessCreate, CleaningParameterCreate

class CleaningProcessService:
    """
    Section 6.0 - Control of Cleaning Process
    """
    
    @staticmethod
    def create_process(db: Session, process_data: CleaningProcessCreate) -> CleaningProcess:
        """Create a new cleaning process definition"""
        
        # Convert complex fields to JSON
        cleaning_agents_json = json.dumps(process_data.cleaning_agents) if process_data.cleaning_agents else None
        solvents_json = json.dumps(process_data.solvents_used) if process_data.solvents_used else None
        process_steps_json = json.dumps([step.dict() for step in process_data.process_steps]) if process_data.process_steps else None
        equipment_ids_json = json.dumps(process_data.equipment_ids) if process_data.equipment_ids else None
        analysis_methods_json = json.dumps(process_data.in_process_analysis_methods) if process_data.in_process_analysis_methods else None
        
        process = CleaningProcess(
            process_code=process_data.process_code,
            name=process_data.name,
            description=process_data.description,
            cleaning_type=process_data.cleaning_type,
            system_boundaries=process_data.system_boundaries,
            cleaning_agents=cleaning_agents_json,
            solvents_used=solvents_json,
            process_steps=process_steps_json,
            equipment_ids=equipment_ids_json,
            has_in_process_analysis=process_data.has_in_process_analysis,
            in_process_analysis_methods=analysis_methods_json,
            min_temperature_c=process_data.min_temperature_c,
            max_temperature_c=process_data.max_temperature_c,
            min_flow_rate_lpm=process_data.min_flow_rate_lpm,
            max_flow_rate_lpm=process_data.max_flow_rate_lpm,
            min_pressure_bar=process_data.min_pressure_bar,
            max_pressure_bar=process_data.max_pressure_bar,
            min_duration_min=process_data.min_duration_min,
            max_duration_min=process_data.max_duration_min,
            sop_reference=process_data.sop_reference,
            sop_version=process_data.sop_version,
            training_required=process_data.training_required,
            created_by=process_data.created_by,
            is_validated=False
        )
        
        db.add(process)
        db.commit()
        db.refresh(process)
        return process
    
    @staticmethod
    def add_parameter(db: Session, process_id: int, param_data: CleaningParameterCreate) -> CleaningParameter:
        """Add a critical parameter to a cleaning process"""
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
        if not process:
            raise ValueError("Process not found")
        
        parameter = CleaningParameter(
            process_id=process_id,
            parameter_name=param_data.parameter_name,
            parameter_unit=param_data.parameter_unit,
            target_value=param_data.target_value,
            min_acceptable=param_data.min_acceptable,
            max_acceptable=param_data.max_acceptable,
            is_critical=param_data.is_critical,
            is_controlled_automatically=param_data.is_controlled_automatically,
            measurement_method=param_data.measurement_method,
            measurement_frequency=param_data.measurement_frequency
        )
        
        db.add(parameter)
        db.commit()
        db.refresh(parameter)
        return parameter
    
    @staticmethod
    def record_execution(db: Session, execution_data) -> CleaningExecution:
        """Record actual cleaning execution parameters"""
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == execution_data.process_id).first()
        if not process:
            raise ValueError("Process not found")
        
        # Check each parameter against specifications
        temp_ok = True
        flow_ok = True
        pressure_ok = True
        duration_ok = True
        
        if execution_data.actual_temperature_c is not None:
            if process.min_temperature_c and execution_data.actual_temperature_c < process.min_temperature_c:
                temp_ok = False
            if process.max_temperature_c and execution_data.actual_temperature_c > process.max_temperature_c:
                temp_ok = False
        
        if execution_data.actual_flow_rate_lpm is not None:
            if process.min_flow_rate_lpm and execution_data.actual_flow_rate_lpm < process.min_flow_rate_lpm:
                flow_ok = False
            if process.max_flow_rate_lpm and execution_data.actual_flow_rate_lpm > process.max_flow_rate_lpm:
                flow_ok = False
        
        if execution_data.actual_pressure_bar is not None:
            if process.min_pressure_bar and execution_data.actual_pressure_bar < process.min_pressure_bar:
                pressure_ok = False
            if process.max_pressure_bar and execution_data.actual_pressure_bar > process.max_pressure_bar:
                pressure_ok = False
        
        if execution_data.actual_duration_min is not None:
            if process.min_duration_min and execution_data.actual_duration_min < process.min_duration_min:
                duration_ok = False
            if process.max_duration_min and execution_data.actual_duration_min > process.max_duration_min:
                duration_ok = False
        
        all_ok = temp_ok and flow_ok and pressure_ok and duration_ok
        
        execution = CleaningExecution(
            process_id=execution_data.process_id,
            session_id=execution_data.session_id,
            execution_date=datetime.now(),
            executed_by=execution_data.executed_by,
            actual_temperature_c=execution_data.actual_temperature_c,
            actual_flow_rate_lpm=execution_data.actual_flow_rate_lpm,
            actual_pressure_bar=execution_data.actual_pressure_bar,
            actual_duration_min=execution_data.actual_duration_min,
            actual_concentration_percent=execution_data.actual_concentration_percent,
            temperature_within_spec=temp_ok,
            flow_rate_within_spec=flow_ok,
            pressure_within_spec=pressure_ok,
            duration_within_spec=duration_ok,
            all_parameters_acceptable=all_ok,
            deviations=execution_data.deviations,
            deviation_justification=execution_data.deviation_justification,
            in_process_results=json.dumps(execution_data.in_process_results) if execution_data.in_process_results else None
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution
    
    @staticmethod
    def get_process_with_parameters(db: Session, process_id: int) -> dict:
        """Get complete process definition with all parameters"""
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
        if not process:
            return None
        
        parameters = db.query(CleaningParameter).filter(CleaningParameter.process_id == process_id).all()
        executions = db.query(CleaningExecution).filter(CleaningExecution.process_id == process_id).order_by(
            CleaningExecution.execution_date.desc()
        ).limit(10).all()
        
        return {
            "process": process,
            "parameters": parameters,
            "recent_executions": executions,
            "total_executions": db.query(CleaningExecution).filter(CleaningExecution.process_id == process_id).count()
        }