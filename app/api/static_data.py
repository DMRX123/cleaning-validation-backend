from fastapi import APIRouter, Depends, HTTPException
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

STATIC_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static_data")


def load_json_file(filename: str):
    """Load JSON file from static_data directory"""
    file_path = os.path.join(STATIC_DATA_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {filename}: {str(e)}")
        return None


plants_data = load_json_file("plants.json")
solubility_data = load_json_file("solubility.json")
difficulty_data = load_json_file("difficulty.json")
equipment_types_data = load_json_file("equipment_types.json")
cleaning_levels_data = load_json_file("cleaning_levels.json")
hold_times_data = load_json_file("hold_times.json")
microbiological_limits_data = load_json_file("microbiological_limits.json")
ttc_values_data = load_json_file("ttc_values.json")
worst_case_weights_data = load_json_file("worst_case_weights.json")

PLANTS = plants_data.get("plants", ["Plant-1", "Plant-2", "Plant-3", "Plant-4"]) if plants_data else ["Plant-1", "Plant-2", "Plant-3", "Plant-4"]

SOLUBILITY = solubility_data.get("solubility", []) if solubility_data else []
SOLUBILITY_WEIGHTS = solubility_data.get("weights", {}) if solubility_data else {}

CLEANING_DIFFICULTY = difficulty_data.get("cleaning_difficulty", []) if difficulty_data else []
DIFFICULTY_WEIGHTS = difficulty_data.get("weights", {}) if difficulty_data else {}

EQUIPMENT_TYPES = [eq.get("name") for eq in equipment_types_data.get("equipment_types", [])] if equipment_types_data else []
EQUIPMENT_TYPES_DETAILS = equipment_types_data.get("equipment_types", []) if equipment_types_data else []

CLEANING_LEVELS = cleaning_levels_data.get("levels", {}) if cleaning_levels_data else {}
HOLD_TIMES = hold_times_data.get("default_hold_times_hours", {}) if hold_times_data else {}
MICROBIOLOGICAL_LIMITS = microbiological_limits_data.get("limits_by_product_type", {}) if microbiological_limits_data else {}
TTC_VALUES = ttc_values_data.get("ttc_values_mg_per_day", {}) if ttc_values_data else {}
WORST_CASE_WEIGHTS = worst_case_weights_data if worst_case_weights_data else {}


# ============================================
# API ENDPOINTS - NO AUTHENTICATION REQUIRED
# ============================================

@router.get("/plants")
def get_plants():
    """Get all plants - PUBLIC"""
    return {"success": True, "data": PLANTS, "count": len(PLANTS)}


@router.get("/solubility")
def get_solubility():
    """Get solubility classes - PUBLIC"""
    return {"success": True, "data": SOLUBILITY, "count": len(SOLUBILITY)}


@router.get("/solubility/weights")
def get_solubility_weights():
    """Get solubility weights - PUBLIC"""
    return {"success": True, "data": SOLUBILITY_WEIGHTS}


@router.get("/difficulty")
def get_difficulty():
    """Get cleaning difficulty levels - PUBLIC"""
    return {"success": True, "data": CLEANING_DIFFICULTY, "count": len(CLEANING_DIFFICULTY)}


@router.get("/difficulty/weights")
def get_difficulty_weights():
    """Get difficulty weights - PUBLIC"""
    return {"success": True, "data": DIFFICULTY_WEIGHTS}


@router.get("/equipment-types")
def get_equipment_types():
    """Get equipment types list - PUBLIC"""
    return {"success": True, "data": EQUIPMENT_TYPES, "count": len(EQUIPMENT_TYPES)}


@router.get("/equipment-types/details")
def get_equipment_types_details():
    """Get detailed equipment types - PUBLIC"""
    return {"success": True, "data": EQUIPMENT_TYPES_DETAILS, "count": len(EQUIPMENT_TYPES_DETAILS)}


@router.get("/cleaning-levels")
def get_cleaning_levels():
    """Get cleaning levels configuration - PUBLIC"""
    return {"success": True, "data": CLEANING_LEVELS}


@router.get("/hold-times")
def get_hold_times():
    """Get default hold times - PUBLIC"""
    return {"success": True, "data": HOLD_TIMES}


@router.get("/microbiological-limits")
def get_microbiological_limits():
    """Get microbiological limits - PUBLIC"""
    return {"success": True, "data": MICROBIOLOGICAL_LIMITS}


@router.get("/ttc-values")
def get_ttc_values():
    """Get TTC values - PUBLIC"""
    return {"success": True, "data": TTC_VALUES}


@router.get("/worst-case-weights")
def get_worst_case_weights():
    """Get worst case calculation weights - PUBLIC"""
    return {"success": True, "data": WORST_CASE_WEIGHTS}


@router.get("/all")
def get_all_static_data():
    """Get all static data in one request - PUBLIC"""
    return {
        "success": True,
        "data": {
            "plants": PLANTS,
            "solubility": SOLUBILITY,
            "solubility_weights": SOLUBILITY_WEIGHTS,
            "cleaning_difficulty": CLEANING_DIFFICULTY,
            "difficulty_weights": DIFFICULTY_WEIGHTS,
            "equipment_types": EQUIPMENT_TYPES,
            "equipment_types_details": EQUIPMENT_TYPES_DETAILS,
            "cleaning_levels": CLEANING_LEVELS,
            "hold_times": HOLD_TIMES,
            "microbiological_limits": MICROBIOLOGICAL_LIMITS,
            "ttc_values": TTC_VALUES,
            "worst_case_weights": WORST_CASE_WEIGHTS,
        },
        "reference": "APIC Cleaning Validation Guide 2021"
    }