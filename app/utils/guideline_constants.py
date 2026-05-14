"""
APIC Guideline 2021 Constants and Lookup Tables
"""

# Section 4.2.1.1 - Uncertainty factors
UNCERTAINTY_FACTORS = {
    "F1": {"description": "Interspecies extrapolation", "default": 1.0},
    "F2": {"description": "Interindividual variability", "default": 10.0},
    "F3": {"description": "Subchronic to chronic", "default": 10.0},
    "F4": {"description": "Severity of effect", "default": 1.0},
    "F5": {"description": "Database completeness", "default": 1.0},
}

# Section 4.2.1.3 - TTC values (µg/day)
TTC_VALUES_UG_PER_DAY = {
    "carcinogenic": 1.0,
    "potent": 10.0,
    "standard": 100.0,
    "genotoxic": 1.0,
}

# Section 5.2 - Cleaning levels
CLEANING_LEVELS = {
    "LEVEL_0": {
        "name": "Visual Only",
        "risk": "Low",
        "validation_required": False,
        "max_residue_ppm": None,
        "description": "Only gross cleaning required. Carryover not critical."
    },
    "LEVEL_1": {
        "name": "Visual + Analytical",
        "risk": "Medium",
        "validation_required": True,
        "max_residue_ppm": 100,
        "description": "Carryover of previous product is less critical."
    },
    "LEVEL_2": {
        "name": "Full Validation",
        "risk": "High",
        "validation_required": True,
        "max_residue_ppm": 10,
        "description": "Carryover of previous product is critical."
    }
}

# Section 7.4 - Worst case rating weights
WORST_CASE_WEIGHTS = {
    "solubility": {
        "Very Soluble": 1, "Freely Soluble": 1,
        "Soluble": 2, "Sparingly Soluble": 2,
        "Slightly Soluble": 3, "Very Slightly Soluble": 3,
        "Practically Insoluble": 3, "Insoluble": 3
    },
    "difficulty": {
        "Very Easy": 1, "Easy": 1,
        "Medium": 2, "Difficult": 3, "Very Difficult": 3
    },
    "toxicity": {
        ">500 ug": 1,
        "100-500 ug": 2,
        "10-99 ug": 3,
        "1-9 ug": 4,
        "<1 ug": 5
    },
    "dose": {
        ">1000 mg": 1,
        "100-1000 mg": 2,
        "10-99 mg": 3,
        "1-9 mg": 4,
        "<1 mg": 5
    }
}

# Section 8.1 - Microbiological limits (CFU/dm²)
MICROBIOLOGICAL_LIMITS = {
    "oral": {"total_germ": 100, "yeast_mold": 50},
    "parenteral": {"total_germ": 10, "yeast_mold": 5},
    "topical": {"total_germ": 100, "yeast_mold": 50},
    "biotech": {"total_germ": 10, "yeast_mold": 5},
    "inhalation": {"total_germ": 10, "yeast_mold": 5}
}

# Section 9.7 - Hold time defaults (hours)
HOLD_TIME_DEFAULTS = {
    "reactor": {"dht": 24, "cht": 72},
    "dryer": {"dht": 12, "cht": 168},
    "blender": {"dht": 8, "cht": 168},
    "filter": {"dht": 8, "cht": 48},
    "tank": {"dht": 48, "cht": 168},
    "centrifuge": {"dht": 12, "cht": 72},
    "mill": {"dht": 8, "cht": 168},
    "coater": {"dht": 8, "cht": 72},
    "granulator": {"dht": 12, "cht": 72},
    "packaging": {"dht": 4, "cht": 24}
}

# Section 4.2.6 - Production type factors
PRODUCTION_TYPE_FACTORS = {
    "pharmaceutical": 1.0,
    "api_chemical": 8.0,
    "api_physical": 1.0,
    "intermediate_early": 15.0,
    "intermediate_late": 5.0,
    "dedicated": None
}