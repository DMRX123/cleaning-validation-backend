from fastapi import APIRouter, Depends, HTTPException
from .auth import get_current_user
from ..models.user import User
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
def get_plants(current_user: User = Depends(get_current_user)):
    """Get all plants - FIXED with authentication"""
    return PLANTS


@router.get("/solubility")
def get_solubility(current_user: User = Depends(get_current_user)):
    """Get solubility classes - FIXED with authentication"""
    return SOLUBILITY


@router.get("/difficulty")
def get_difficulty(current_user: User = Depends(get_current_user)):
    """Get cleaning difficulty levels - FIXED with authentication"""
    return CLEANING_DIFFICULTY


@router.get("/equipment-types")
def get_equipment_types(current_user: User = Depends(get_current_user)):
    """Get equipment types - FIXED with authentication"""
    return EQUIPMENT_TYPES