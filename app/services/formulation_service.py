# app/services/formulation_service.py - COMPLETE NEW FILE

from sqlalchemy.orm import Session
from ..models.dosage_form import DosageForm, DosageFormEnum, PlantTypeEnum, ProductDosageForm
from ..models.product import Product
from ..models.sampling_methods import SamplingLocation, SamplingMethodEnum
from ..models.formulation_equipment import FormulationEquipment, EquipmentCategoryEnum
import logging

logger = logging.getLogger(__name__)

class FormulationService:
    """
    Service for Formulation Plant cleaning validation
    Supports OSD, Sterile Injectables, Liquid Orals, Ophthalmic, etc.
    """
    
    # Dosage form specific cleaning requirements
    DOSAGE_FORM_REQUIREMENTS = {
        # Solid Dosage Forms
        "tablet": {
            "plant_type": PlantTypeEnum.FORMULATION_OSD,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 1000,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 10
        },
        "capsule": {
            "plant_type": PlantTypeEnum.FORMULATION_OSD,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 1000,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 8
        },
        
        # Liquid Dosage Forms
        "oral_solution": {
            "plant_type": PlantTypeEnum.FORMULATION_LIQUID,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 15
        },
        "oral_suspension": {
            "plant_type": PlantTypeEnum.FORMULATION_LIQUID,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 15
        },
        "syrup": {
            "plant_type": PlantTypeEnum.FORMULATION_LIQUID,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 12
        },
        
        # Sterile Dosage Forms - MOST STRINGENT
        "injectable": {
            "plant_type": PlantTypeEnum.FORMULATION_STERILE,
            "requires_sterility": True,
            "requires_endotoxin_testing": True,
            "microbial_limit_cfu": 1,
            "endotoxin_limit_eu_ml": 0.25,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 5
        },
        "infusion": {
            "plant_type": PlantTypeEnum.FORMULATION_STERILE,
            "requires_sterility": True,
            "requires_endotoxin_testing": True,
            "microbial_limit_cfu": 1,
            "endotoxin_limit_eu_ml": 0.25,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 8
        },
        "ophthalmic": {
            "plant_type": PlantTypeEnum.FORMULATION_OPHTHALMIC,
            "requires_sterility": True,
            "requires_endotoxin_testing": True,
            "microbial_limit_cfu": 1,
            "endotoxin_limit_eu_ml": 0.25,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 3
        },
        "nasal": {
            "plant_type": PlantTypeEnum.FORMULATION_STERILE,
            "requires_sterility": True,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 10,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 4
        },
        "inhalation": {
            "plant_type": PlantTypeEnum.FORMULATION_INHALATION,
            "requires_sterility": True,
            "requires_endotoxin_testing": True,
            "microbial_limit_cfu": 10,
            "endotoxin_limit_eu_ml": 0.25,
            "sampling_method": "rinse",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 4
        },
        
        # Semi-solid Dosage Forms
        "cream": {
            "plant_type": PlantTypeEnum.FORMULATION_TOPICAL,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 20
        },
        "ointment": {
            "plant_type": PlantTypeEnum.FORMULATION_TOPICAL,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 20
        },
        "gel": {
            "plant_type": PlantTypeEnum.FORMULATION_TOPICAL,
            "requires_sterility": False,
            "requires_endotoxin_testing": False,
            "microbial_limit_cfu": 100,
            "sampling_method": "swab",
            "visual_inspection_critical": True,
            "typical_surface_area_m2": 18
        }
    }
    
    @classmethod
    def get_dosage_form_requirements(cls, dosage_form_code: str) -> dict:
        """Get cleaning requirements for a specific dosage form"""
        return cls.DOSAGE_FORM_REQUIREMENTS.get(
            dosage_form_code,
            cls.DOSAGE_FORM_REQUIREMENTS["tablet"]  # Default
        )
    
    @classmethod
    def get_plant_type_requirements(cls, plant_type: str) -> dict:
        """Get plant type specific requirements"""
        plant_requirements = {
            "api_plant": {
                "cleaning_level": "LEVEL_1",
                "validation_required": True,
                "microbial_testing": False,
                "endotoxin_testing": False,
                "sampling_frequency": "Quarterly"
            },
            "formulation_osd": {
                "cleaning_level": "LEVEL_1",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": False,
                "sampling_frequency": "Monthly"
            },
            "formulation_sterile": {
                "cleaning_level": "LEVEL_2",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": True,
                "sampling_frequency": "Every Batch"
            },
            "formulation_liquid": {
                "cleaning_level": "LEVEL_1",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": False,
                "sampling_frequency": "Every Batch"
            },
            "formulation_ophthalmic": {
                "cleaning_level": "LEVEL_2",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": True,
                "sampling_frequency": "Every Batch"
            },
            "formulation_topical": {
                "cleaning_level": "LEVEL_1",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": False,
                "sampling_frequency": "Monthly"
            },
            "formulation_inhalation": {
                "cleaning_level": "LEVEL_2",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": True,
                "sampling_frequency": "Every Batch"
            },
            "biotech": {
                "cleaning_level": "LEVEL_2",
                "validation_required": True,
                "microbial_testing": True,
                "endotoxin_testing": True,
                "sampling_frequency": "Every Batch"
            }
        }
        return plant_requirements.get(plant_type, plant_requirements["api_plant"])
    
    @classmethod
    def calculate_sterile_limit(cls, maco_mg: float, equipment_area_m2: float, 
                                endotoxin_factor: float = 1.0) -> dict:
        """
        Calculate stricter limits for sterile/injectable products
        As per PDA TR 29 and EMA guidelines
        """
        # Normal limit
        normal_limit_ppm = (maco_mg * 1000) / (equipment_area_m2 * 10000)
        
        # Sterile limit is 10x stricter
        sterile_limit_ppm = normal_limit_ppm / 10
        
        # Endotoxin limit (EU/ml) typically 0.25 for injectables
        endotoxin_limit = 0.25 * endotoxin_factor
        
        return {
            "normal_limit_ppm": round(normal_limit_ppm, 2),
            "sterile_limit_ppm": round(sterile_limit_ppm, 2),
            "endotoxin_limit_eu_ml": endotoxin_limit,
            "recommendation": "Use sterile_limit_ppm for injectable products",
            "reference": "PDA TR 29, EMA/CHMP/CVMP/SWP/169430/2012"
        }
    
    @classmethod
    def get_sampling_locations_for_equipment(cls, equipment_category: str) -> list:
        """Get recommended sampling locations based on equipment category"""
        
        sampling_locations = {
            "tablet_press": [
                {"location": "Hopper", "area_cm2": 100, "priority": 1},
                {"location": "Feed frame", "area_cm2": 50, "priority": 1},
                {"location": "Dies", "area_cm2": 25, "priority": 2},
                {"location": "Punches", "area_cm2": 10, "priority": 2},
                {"location": "Outlet chute", "area_cm2": 30, "priority": 3}
            ],
            "coater": [
                {"location": "Spray guns", "area_cm2": 5, "priority": 1},
                {"location": "Pan baffles", "area_cm2": 200, "priority": 2},
                {"location": "Air inlet", "area_cm2": 50, "priority": 2},
                {"location": "Outlet filter", "area_cm2": 100, "priority": 3}
            ],
            "vial_filler": [
                {"location": "Filling needles", "area_cm2": 1, "priority": 1},
                {"location": "Product tank", "area_cm2": 100, "priority": 1},
                {"location": "Transfer lines", "area_cm2": 20, "priority": 1},
                {"location": "Stoppering station", "area_cm2": 30, "priority": 2}
            ],
            "mixing_tank": [
                {"location": "Top head", "area_cm2": 500, "priority": 2},
                {"location": "Agitator blades", "area_cm2": 200, "priority": 1},
                {"location": "Bottom valve", "area_cm2": 50, "priority": 1},
                {"location": "Manhole gasket", "area_cm2": 10, "priority": 1},
                {"location": "Sampling port", "area_cm2": 5, "priority": 2}
            ],
            "filling_machine": [
                {"location": "Filling nozzles", "area_cm2": 2, "priority": 1},
                {"location": "Product hopper", "area_cm2": 80, "priority": 2},
                {"location": "Tube guide", "area_cm2": 10, "priority": 2},
                {"location": "Capping station", "area_cm2": 40, "priority": 3}
            ]
        }
        
        return sampling_locations.get(equipment_category, [])