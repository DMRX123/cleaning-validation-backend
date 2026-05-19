"""
Section 6.0 - Cleaning Process Control Constants
"""

# Default cleaning parameter limits
DEFAULT_CLEANING_PARAMETERS = {
    "temperature": {
        "unit": "°C",
        "min": 20,
        "max": 80,
        "target": 60,
        "is_critical": True
    },
    "flow_rate": {
        "unit": "L/min",
        "min": 100,
        "max": 500,
        "target": 300,
        "is_critical": True
    },
    "pressure": {
        "unit": "bar",
        "min": 2,
        "max": 6,
        "target": 4,
        "is_critical": True
    },
    "duration": {
        "unit": "min",
        "min": 15,
        "max": 60,
        "target": 30,
        "is_critical": True
    },
    "concentration": {
        "unit": "%",
        "min": 1,
        "max": 5,
        "target": 2,
        "is_critical": True
    }
}

# Capability index thresholds (Section 6.0 Figure 2)
CAPABILITY_THRESHOLDS = {
    "excellent": 1.33,
    "acceptable": 1.00,
    "marginal": 0.67,
    "unacceptable": 0.00
}

# Risk levels based on capability
RISK_LEVELS = {
    "LOW": {
        "cpk_min": 1.33,
        "margin_percent_min": 50,
        "action": "Continue routine monitoring",
        "frequency": "Quarterly"
    },
    "MEDIUM": {
        "cpk_min": 1.00,
        "margin_percent_min": 25,
        "action": "Monitor closely, consider optimization",
        "frequency": "Monthly"
    },
    "HIGH": {
        "cpk_min": 0.67,
        "margin_percent_min": 10,
        "action": "Review and optimize cleaning parameters",
        "frequency": "Every batch"
    },
    "CRITICAL": {
        "cpk_min": 0.00,
        "margin_percent_min": 0,
        "action": "Immediate review and revalidation required",
        "frequency": "Immediate"
    }
}

# Cleaning types with requirements
CLEANING_TYPE_REQUIREMENTS = {
    "manual": {
        "requires_detailed_sop": True,
        "requires_training_certification": True,
        "requires_dual_verification": True,
        "parameter_control": "Operator dependent",
        "typical_validation_effort": "High"
    },
    "automated_cip": {
        "requires_detailed_sop": True,
        "requires_training_certification": True,
        "requires_dual_verification": False,
        "parameter_control": "Automated with sensors",
        "typical_validation_effort": "Medium"
    },
    "automated_cop": {
        "requires_detailed_sop": True,
        "requires_training_certification": True,
        "requires_dual_verification": False,
        "parameter_control": "Automated with timers",
        "typical_validation_effort": "Medium"
    },
    "semi_automated": {
        "requires_detailed_sop": True,
        "requires_training_certification": True,
        "requires_dual_verification": True,
        "parameter_control": "Partially automated",
        "typical_validation_effort": "Medium-High"
    }
}