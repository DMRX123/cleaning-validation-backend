from typing import Tuple, List, Dict, Any

def validate_product(product_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate product data before saving"""
    errors = []
    
    # Required fields
    required_fields = ["name", "min_batch_size", "max_batch_size", "ade_pde", "min_dose", "max_dose"]
    for field in required_fields:
        if not product_data.get(field):
            errors.append(f"{field} is required")
    
    # Batch size validation
    if product_data.get("min_batch_size", 0) > product_data.get("max_batch_size", 0):
        errors.append("Min batch size cannot be greater than max batch size")
    
    if product_data.get("min_batch_size", 0) <= 0:
        errors.append("Min batch size must be greater than 0")
    
    # Dose validation
    if product_data.get("min_dose", 0) > product_data.get("max_dose", 0):
        errors.append("Min dose cannot be greater than max dose")
    
    # Recovery validation
    recovery = product_data.get("swab_recovery", 0)
    if recovery <= 0 or recovery > 150:
        errors.append("Swab recovery should be between 1% and 150%")
    
    # LOQ/LOD validation
    lod = product_data.get("lod", 0)
    loq = product_data.get("loq", 0)
    if loq <= 0:
        errors.append("LOQ must be greater than 0")
    if lod <= 0:
        errors.append("LOD must be greater than 0")
    if loq <= lod:
        errors.append("LOQ should be greater than LOD (typically 3-5x)")
    
    # Dilution validation
    if product_data.get("swab_dilution", 0) <= 0:
        errors.append("Swab dilution volume must be greater than 0")
    
    return len(errors) == 0, errors


def validate_equipment(equipment_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate equipment data"""
    errors = []
    
    if not equipment_data.get("name"):
        errors.append("Equipment name is required")
    
    if not equipment_data.get("equipment_id"):
        errors.append("Equipment ID is required")
    
    surface_area = equipment_data.get("surface_area", 0)
    if surface_area <= 0:
        errors.append("Surface area must be greater than 0")
    
    return len(errors) == 0, errors


def validate_session(session_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate validation session"""
    errors = []
    
    if not session_data.get("previous_product_id"):
        errors.append("Previous product is required")
    
    if not session_data.get("next_product_id"):
        errors.append("Next product is required")
    
    extra_percentage = session_data.get("extra_area_percentage", 0)
    if extra_percentage < 0 or extra_percentage > 100:
        errors.append("Extra area percentage must be between 0 and 100")
    
    return len(errors) == 0, errors


def validate_swab_result(result_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate swab result entry"""
    errors = []
    
    if not result_data.get("location_name"):
        errors.append("Location name is required")
    
    absorbance_sample = result_data.get("absorbance_sample", 0)
    if absorbance_sample < 0:
        errors.append("Absorbance cannot be negative")
    
    absorbance_std = result_data.get("absorbance_std", 0)
    if absorbance_std <= 0:
        errors.append("Standard absorbance must be greater than 0")
    
    return len(errors) == 0, errors


def validate_rinse_result(result_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate rinse result entry"""
    errors = []
    
    if not result_data.get("equipment_name"):
        errors.append("Equipment name is required")
    
    rinse_volume = result_data.get("actual_rinse_volume", 0)
    if rinse_volume <= 0:
        errors.append("Rinse volume must be greater than 0")
    
    absorbance_std = result_data.get("absorbance_std", 0)
    if absorbance_std <= 0:
        errors.append("Standard absorbance must be greater than 0")
    
    return len(errors) == 0, errors


def validate_standard_prep(prep_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate standard preparation data"""
    errors = []
    
    wt_std = prep_data.get("wt_of_std", 0)
    if wt_std <= 0:
        errors.append("Weight of standard must be greater than 0")
    
    for i in range(1, 6):
        dilution = prep_data.get(f"dilution_{i}", 0)
        if dilution <= 0:
            errors.append(f"Dilution {i} volume must be greater than 0")
    
    potency = prep_data.get("potency", 0)
    if potency <= 0 or potency > 100:
        errors.append("Potency must be between 1% and 100%")
    
    return len(errors) == 0, errors