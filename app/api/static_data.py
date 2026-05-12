from fastapi import APIRouter
import json
import os

router = APIRouter()

# Static data as defined in Excel
PLANTS = ["Plant-1", "Plant-2", "Plant-3", "Plant-4"]

SOLUBILITY = [
    "Very Soluble",
    "Freely Soluble", 
    "Soluble",
    "Sparingly Soluble",
    "Slightly Soluble",
    "Very Slightly Soluble",
    "Practically Insoluble"
]

CLEANING_DIFFICULTY = [
    "Very Easy",
    "Easy",
    "Medium",
    "Difficult",
    "Very Difficult"
]

EQUIPMENT_TYPES = [
    "Sifter", "Granulator", "Dryer", "Blender/Lubricator",
    "Compression", "Coater", "Packaging", "Sampler"
]

@router.get("/plants")
def get_plants():
    return PLANTS

@router.get("/solubility")
def get_solubility():
    return SOLUBILITY

@router.get("/difficulty")
def get_difficulty():
    return CLEANING_DIFFICULTY

@router.get("/equipment-types")
def get_equipment_types():
    return EQUIPMENT_TYPES