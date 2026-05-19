# app/static_data/__init__.py
# Static JSON data files directory for Cleaning Validation System

"""
Static Data Package
Contains JSON configuration files for:
- Cleaning levels (Section 5.0)
- Equipment types (Section 7.2)
- Solubility classifications (Section 7.4(b))
- Cleaning difficulty ratings (Section 7.4(a))
- Hold time defaults (Section 9.7)
- Microbiological limits (Section 8.1)
- TTC values (Section 4.2.1.3)
- Worst case weights (Section 7.4)
"""

__version__ = "1.0.0"
__description__ = "Static configuration data for Cleaning Validation System"
__reference__ = "APIC Cleaning Validation Guide 2021"

# List of available JSON files in this directory
AVAILABLE_DATA_FILES = [
    "cleaning_levels.json",
    "difficulty.json",
    "equipment_types.json",
    "hold_times.json",
    "microbiological_limits.json",
    "plants.json",
    "solubility.json",
    "ttc_values.json",
    "worst_case_weights.json"
]

__all__ = ["AVAILABLE_DATA_FILES"]