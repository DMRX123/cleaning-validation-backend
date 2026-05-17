from sqlalchemy.orm import Session
from sqlalchemy import func
import math
from ..models.cleaning_process import CleaningProcess, CleaningExecution
from ..models.session import ValidationSession

class CleaningCapabilityService:
    """
    Section 6.0 - Cleaning process capability analysis
    Mean effectiveness vs spread vs MACO
    """
    
    @staticmethod
    def calculate_process_capability(db: Session, process_id: int, 
                                      historical_executions: int = 10) -> dict:
        """
        Calculate cleaning process capability
        Determines if mean + spread is adequately below MACO
        """
        
        process = db.query(CleaningProcess).filter(CleaningProcess.id == process_id).first()
        if not process:
            return {"error": "Process not found"}
        
        # Get recent executions with validation results
        executions = db.query(CleaningExecution).filter(
            CleaningExecution.process_id == process_id,
            CleaningExecution.session_id.isnot(None)
        ).order_by(CleaningExecution.execution_date.desc()).limit(historical_executions).all()
        
        if len(executions) < 3:
            return {
                "process_id": process_id,
                "process_name": process.name,
                "error": f"Insufficient data. Need at least 3 executions, found {len(executions)}"
            }
        
        # Get residue results from validation sessions
        residue_results = []
        for exec_record in executions:
            if exec_record.session_id:
                session = db.query(ValidationSession).filter(
                    ValidationSession.id == exec_record.session_id
                ).first()
                if session:
                    # Get actual residue from swab results
                    from ..models.swab_result import SwabResult
                    
                    swab_results = db.query(SwabResult).filter(
                        SwabResult.session_id == session.id
                    ).all()
                    
                    if swab_results:
                        max_residue = max([r.result_ppm or 0 for r in swab_results])
                        residue_results.append(max_residue)
        
        if len(residue_results) < 3:
            return {
                "process_id": process_id,
                "process_name": process.name,
                "error": "Insufficient residue data from validation sessions"
            }
        
        # Calculate statistics
        mean_residue = sum(residue_results) / len(residue_results)
        
        # Calculate standard deviation
        variance = sum((x - mean_residue) ** 2 for x in residue_results) / len(residue_results)
        std_dev = math.sqrt(variance)
        
        # Get MACO from validation sessions (dynamic calculation, not hardcoded)
        sessions = db.query(ValidationSession).filter(
            ValidationSession.process_id == process_id
        ).all()
        
        # Calculate MACO limit from sessions - use the lowest MACO found
        maco_limit = 100.0  # Default fallback
        valid_macos = []
        for session in sessions:
            if session.lowest_maco and session.lowest_maco > 0:
                valid_macos.append(session.lowest_maco)
        
        if valid_macos:
            maco_limit = min(valid_macos)
        else:
            # Try to get from any session without process_id filter
            any_session = db.query(ValidationSession).filter(
                ValidationSession.lowest_maco.isnot(None)
            ).first()
            if any_session and any_session.lowest_maco:
                maco_limit = any_session.lowest_maco
        
        # Calculate capability index (Cpk)
        # Cpk = min(USL - mean, mean - LSL) / (3 * std_dev)
        usl = maco_limit
        lsl = 0.0
        
        cpk_upper = (usl - mean_residue) / (3 * std_dev) if std_dev > 0 else 999
        cpk_lower = (mean_residue - lsl) / (3 * std_dev) if std_dev > 0 and mean_residue > lsl else 999
        cpk = min(cpk_upper, cpk_lower)
        
        # Calculate distance from MACO (margin)
        distance_from_maco = maco_limit - mean_residue
        margin_percent = (distance_from_maco / maco_limit) * 100 if maco_limit > 0 else 0
        
        # Determine risk level
        if cpk >= 1.33 and margin_percent > 50:
            risk_level = "LOW"
            recommendation = "Process is capable. Continue routine monitoring."
        elif cpk >= 1.0 and margin_percent > 25:
            risk_level = "MEDIUM"
            recommendation = "Process is acceptable but monitor closely. Consider optimization."
        elif cpk > 0.67:
            risk_level = "HIGH"
            recommendation = "Process capability is borderline. Review and optimize cleaning parameters."
        else:
            risk_level = "CRITICAL"
            recommendation = "Process is not capable. Immediate review and revalidation required."
        
        # Visual representation (text-based)
        capability_chart = CleaningCapabilityService._generate_chart(
            mean_residue, std_dev, maco_limit
        )
        
        return {
            "process_id": process_id,
            "process_name": process.name,
            "mean_residue_ppm": round(mean_residue, 2),
            "standard_deviation_ppm": round(std_dev, 2),
            "maco_limit_ppm": round(maco_limit, 2),
            "distance_from_maco_ppm": round(distance_from_maco, 2),
            "margin_percent": round(margin_percent, 1),
            "capability_index_cpk": round(cpk, 2),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "data_points_used": len(residue_results),
            "capability_chart": capability_chart,
            "reference": "APIC Cleaning Validation Guide Section 6.0 - Figure 2"
        }
    
    @staticmethod
    def _generate_chart(mean: float, std_dev: float, usl: float, width: int = 50) -> str:
        """Generate text-based capability chart"""
        
        # Simple visual representation
        chart_lines = []
        chart_lines.append(f"\nCapability Chart (mean = {mean:.1f}, σ = {std_dev:.1f}, USL = {usl:.1f})")
        chart_lines.append("-" * width)
        
        # Normal distribution approximation
        positions = []
        for i in range(-3, 4):
            pos = mean + (i * std_dev)
            if pos > 0:
                positions.append(pos)
        
        # Mark positions on chart
        line = [" "] * width
        center_idx = width // 2
        
        for pos in positions:
            if pos <= usl * 1.5:
                idx = int(center_idx + (pos - mean) / (usl * 2) * width)
                if 0 <= idx < width:
                    line[idx] = "●"
        
        # Mark USL
        usl_idx = int(center_idx + (usl - mean) / (usl * 2) * width)
        if 0 <= usl_idx < width:
            line[usl_idx] = "|"
        
        chart_lines.append("".join(line))
        chart_lines.append("")
        chart_lines.append(f"Mean: {mean:.1f} ppm | USL: {usl:.1f} ppm | Margin: {usl - mean:.1f} ppm")
        
        return "\n".join(chart_lines)