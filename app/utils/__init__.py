"""
Utility Functions for Cleaning Validation System
Includes Excel import/export, formula parsing, validators, constants, and guideline helpers
"""

# Excel Utilities
from .excel_import import import_products_from_excel, import_equipment_from_excel
from .excel_export import export_products_to_excel, export_results_to_excel

# Formula Utilities (Excel-like calculations)
from .formula_parser import parse_excel_formula, evaluate_formula, evaluate_expression, excel_like_calculation

# Validators
from .validators import (
    validate_product, validate_equipment, validate_session,
    validate_swab_result, validate_rinse_result, validate_standard_prep
)

# Constants (Excel-based)
from .constants import (
    PPM_FACTOR, SAFETY_FACTOR, DEFAULT_SWAB_AREA,
    SOLUBILITY_WEIGHTS, DIFFICULTY_WEIGHTS,
    PLANTS, SOLUBILITY_LIST, DIFFICULTY_LIST,
    MACO_10PPM_FACTOR, MACO_SAFETY_FACTOR,
    KG_TO_MG_FACTOR, G_TO_MG_FACTOR, UG_TO_MG_FACTOR,
    SWAB_RESULT_PPM_CONVERSION, RINSE_10PPM_VOLUME_FACTOR,
    MIN_SWAB_RECOVERY, MAX_SWAB_RECOVERY, DEFAULT_LOQ_LOD_RATIO
)

# APIC Guideline Helpers (Sections 4.2.1, 4.2.1.3, 4.2.4, 4.2.5, 5.2, 7.4)
from .guideline_helpers import (
    calculate_ade_pde,
    calculate_ttc,
    calculate_maco_ade,
    calculate_maco_10ppm,
    calculate_maco_ttc,
    calculate_swab_limit,
    calculate_rinse_limit,
    calculate_carry_over_swab,
    calculate_carry_over_rinse,
    get_cleaning_level,
    get_worst_case_rating
)

__all__ = [
    # Excel Utilities
    "import_products_from_excel",
    "import_equipment_from_excel",
    "export_products_to_excel",
    "export_results_to_excel",
    
    # Formula Utilities
    "parse_excel_formula",
    "evaluate_formula",
    "evaluate_expression",
    "excel_like_calculation",
    
    # Validators
    "validate_product",
    "validate_equipment",
    "validate_session",
    "validate_swab_result",
    "validate_rinse_result",
    "validate_standard_prep",
    
    # Constants
    "PPM_FACTOR",
    "SAFETY_FACTOR",
    "DEFAULT_SWAB_AREA",
    "SOLUBILITY_WEIGHTS",
    "DIFFICULTY_WEIGHTS",
    "PLANTS",
    "SOLUBILITY_LIST",
    "DIFFICULTY_LIST",
    "MACO_10PPM_FACTOR",
    "MACO_SAFETY_FACTOR",
    "KG_TO_MG_FACTOR",
    "G_TO_MG_FACTOR",
    "UG_TO_MG_FACTOR",
    "SWAB_RESULT_PPM_CONVERSION",
    "RINSE_10PPM_VOLUME_FACTOR",
    "MIN_SWAB_RECOVERY",
    "MAX_SWAB_RECOVERY",
    "DEFAULT_LOQ_LOD_RATIO",
    
    # APIC Guideline Helpers
    "calculate_ade_pde",           # Section 4.2.1.1
    "calculate_ttc",               # Section 4.2.1.3
    "calculate_maco_ade",          # Section 4.2.1
    "calculate_maco_10ppm",        # Section 4.2.2
    "calculate_maco_ttc",          # Section 4.2.1.3
    "calculate_swab_limit",        # Section 4.2.4
    "calculate_rinse_limit",       # Section 4.2.5
    "calculate_carry_over_swab",   # Section 4.2.4
    "calculate_carry_over_rinse",  # Section 8.3.2
    "get_cleaning_level",          # Section 5.2
    "get_worst_case_rating",       # Section 7.4
]