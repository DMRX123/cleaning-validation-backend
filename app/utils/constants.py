# Excel Constants
PPM_FACTOR = 10  # 10 ppm standard
SAFETY_FACTOR = 1000  # for mg to mcg conversion
DEFAULT_SWAB_AREA = 0.01  # m²

# Solubility weights for worst case calculation (higher = harder to clean)
SOLUBILITY_WEIGHTS = {
    "Very Soluble": 1,
    "Freely Soluble": 2,
    "Soluble": 3,
    "Sparingly Soluble": 4,
    "Slightly Soluble": 5,
    "Very Slightly Soluble": 6,
    "Practically Insoluble": 7
}

# Cleaning difficulty weights (higher = harder to clean)
DIFFICULTY_WEIGHTS = {
    "Very Easy": 1,
    "Easy": 2,
    "Medium": 3,
    "Difficult": 4,
    "Very Difficult": 5
}

# Plant list (static from Excel)
PLANTS = ["Plant-1", "Plant-2", "Plant-3", "Plant-4"]

# Solubility list (static from Excel)
SOLUBILITY_LIST = [
    "Very Soluble",
    "Freely Soluble",
    "Soluble",
    "Sparingly Soluble",
    "Slightly Soluble",
    "Very Slightly Soluble",
    "Practically Insoluble"
]

# Cleaning difficulty list (static from Excel)
DIFFICULTY_LIST = [
    "Very Easy",
    "Easy",
    "Medium",
    "Difficult",
    "Very Difficult"
]

# MACO calculation constants
MACO_10PPM_FACTOR = 0.00001  # 10 ppm = 0.00001 (mg of residue per mg of product)
MACO_SAFETY_FACTOR = 1000  # Standard safety factor for TDD method

# Unit conversions
KG_TO_MG_FACTOR = 1000000
G_TO_MG_FACTOR = 1000
UG_TO_MG_FACTOR = 0.001

# Swab constants
SWAB_RESULT_PPM_CONVERSION = 1000  # mg/ml to ppm

# Rinse constants
RINSE_10PPM_VOLUME_FACTOR = 10  # Volume = Limit / 10

# Validation limits
MIN_SWAB_RECOVERY = 50  # %
MAX_SWAB_RECOVERY = 150  # %
DEFAULT_LOQ_LOD_RATIO = 3  # LOQ should be at least 3x LOD