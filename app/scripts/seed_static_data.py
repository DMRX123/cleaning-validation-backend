#!/usr/bin/env python
"""Seed static data into database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models.cleaning_level import CleaningLevel, CleaningLevelEnum
from app.models.microbiological import MicrobiologicalLimit
from app.models.dosage_form import DosageForm, DosageFormEnum, PlantTypeEnum


def seed_cleaning_levels(db):
    """Seed cleaning levels data"""
    levels = [
        {
            "level": CleaningLevelEnum.LEVEL_0,
            "name": "Level 0 - Visual Only",
            "description": "Visual inspection only - low risk. Same synthetic chain immediate next step.",
            "requires_visual_inspection": True,
            "requires_analytical_testing": False,
            "requires_microbiological_testing": False,
            "requires_validation": False,
            "max_residue_ppm": None,
            "safety_factor": 1.0
        },
        {
            "level": CleaningLevelEnum.LEVEL_1,
            "name": "Level 1 - Visual + Analytical",
            "description": "Visual + analytical testing - medium risk. Different chain early steps.",
            "requires_visual_inspection": True,
            "requires_analytical_testing": True,
            "requires_microbiological_testing": False,
            "requires_validation": True,
            "max_residue_ppm": 100.0,
            "safety_factor": 5.0
        },
        {
            "level": CleaningLevelEnum.LEVEL_2,
            "name": "Level 2 - Full Validation",
            "description": "Full validation with microbiological testing - high risk. Final API/toxic compounds.",
            "requires_visual_inspection": True,
            "requires_analytical_testing": True,
            "requires_microbiological_testing": True,
            "requires_validation": True,
            "max_residue_ppm": 10.0,
            "safety_factor": 1.0
        }
    ]
    
    for level_data in levels:
        existing = db.query(CleaningLevel).filter(CleaningLevel.level == level_data["level"]).first()
        if not existing:
            level = CleaningLevel(**level_data)
            db.add(level)
            print(f"✅ Added cleaning level: {level_data['level'].value}")
        else:
            print(f"⚠️ Cleaning level already exists: {level_data['level'].value}")
    
    db.commit()
    print("✅ Cleaning levels seeded successfully!")


def seed_microbiological_limits(db):
    """Seed default microbiological limits"""
    limits = [
        {
            "equipment_id": None,
            "product_type": "oral",
            "total_germ_count_limit": 100.0,
            "yeast_mold_limit": 50.0,
            "endotoxin_limit": None,
            "sampling_method": "swab",
            "sampling_frequency": "Every batch for Level 2, Quarterly for Level 1"
        },
        {
            "equipment_id": None,
            "product_type": "parenteral",
            "total_germ_count_limit": 10.0,
            "yeast_mold_limit": 5.0,
            "endotoxin_limit": 0.25,
            "sampling_method": "rinse",
            "sampling_frequency": "Every batch"
        },
        {
            "equipment_id": None,
            "product_type": "topical",
            "total_germ_count_limit": 100.0,
            "yeast_mold_limit": 50.0,
            "endotoxin_limit": None,
            "sampling_method": "contact plate",
            "sampling_frequency": "Monthly"
        },
        {
            "equipment_id": None,
            "product_type": "biotech",
            "total_germ_count_limit": 10.0,
            "yeast_mold_limit": 5.0,
            "endotoxin_limit": 0.25,
            "sampling_method": "swab",
            "sampling_frequency": "Every batch"
        },
        {
            "equipment_id": None,
            "product_type": "inhalation",
            "total_germ_count_limit": 10.0,
            "yeast_mold_limit": 5.0,
            "endotoxin_limit": 0.25,
            "sampling_method": "rinse",
            "sampling_frequency": "Every batch"
        }
    ]
    
    for limit_data in limits:
        existing = db.query(MicrobiologicalLimit).filter(
            MicrobiologicalLimit.product_type == limit_data["product_type"]
        ).first()
        if not existing:
            limit = MicrobiologicalLimit(**limit_data)
            db.add(limit)
            print(f"✅ Added microbiological limit for: {limit_data['product_type']}")
        else:
            print(f"⚠️ Microbiological limit already exists for: {limit_data['product_type']}")
    
    db.commit()
    print("✅ Microbiological limits seeded successfully!")


def seed_dosage_forms(db):
    """Seed dosage forms data"""
    dosage_forms = [
        {"name": "Tablet", "code": DosageFormEnum.TABLET, "plant_type": PlantTypeEnum.FORMULATION_OSD,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 1000},
        {"name": "Capsule", "code": DosageFormEnum.CAPSULE, "plant_type": PlantTypeEnum.FORMULATION_OSD,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 1000},
        {"name": "Powder", "code": DosageFormEnum.POWDER, "plant_type": PlantTypeEnum.FORMULATION_OSD,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 1000},
        {"name": "Injectable", "code": DosageFormEnum.INJECTABLE, "plant_type": PlantTypeEnum.FORMULATION_STERILE,
         "requires_sterility": True, "requires_endotoxin_testing": True, "default_microbial_limit_cfu": 1, "default_endotoxin_limit_eu_ml": 0.25},
        {"name": "Oral Solution", "code": DosageFormEnum.ORAL_SOLUTION, "plant_type": PlantTypeEnum.FORMULATION_LIQUID,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 100},
        {"name": "Cream", "code": DosageFormEnum.CREAM, "plant_type": PlantTypeEnum.FORMULATION_TOPICAL,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 100},
        {"name": "Ointment", "code": DosageFormEnum.OINTMENT, "plant_type": PlantTypeEnum.FORMULATION_TOPICAL,
         "requires_sterility": False, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 100},
        {"name": "Ophthalmic", "code": DosageFormEnum.OPHTHALMIC, "plant_type": PlantTypeEnum.FORMULATION_OPHTHALMIC,
         "requires_sterility": True, "requires_endotoxin_testing": True, "default_microbial_limit_cfu": 1, "default_endotoxin_limit_eu_ml": 0.25},
        {"name": "Nasal", "code": DosageFormEnum.NASAL, "plant_type": PlantTypeEnum.FORMULATION_STERILE,
         "requires_sterility": True, "requires_endotoxin_testing": False, "default_microbial_limit_cfu": 10},
        {"name": "Inhalation", "code": DosageFormEnum.INHALATION, "plant_type": PlantTypeEnum.FORMULATION_INHALATION,
         "requires_sterility": True, "requires_endotoxin_testing": True, "default_microbial_limit_cfu": 10, "default_endotoxin_limit_eu_ml": 0.25},
    ]
    
    for df_data in dosage_forms:
        existing = db.query(DosageForm).filter(DosageForm.code == df_data["code"]).first()
        if not existing:
            dosage_form = DosageForm(**df_data, is_active=True)
            db.add(dosage_form)
            print(f"✅ Added dosage form: {df_data['name']}")
        else:
            print(f"⚠️ Dosage form already exists: {df_data['name']}")
    
    db.commit()
    print("✅ Dosage forms seeded successfully!")


def main():
    print("=" * 50)
    print("Seeding Static Data for Cleaning Validation System")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        seed_cleaning_levels(db)
        print("-" * 30)
        seed_microbiological_limits(db)
        print("-" * 30)
        seed_dosage_forms(db)
        print("-" * 30)
        print("✅ Static data seeding completed successfully!")
    except Exception as e:
        print(f"❌ Error seeding data: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()