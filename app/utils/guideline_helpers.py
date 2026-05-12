"""
APIC Cleaning Validation Guide - Helper Functions
Contains all formula implementations from the guideline
"""

def calculate_ade_pde(noael: float, bw: float = 50, 
                      uf1: float = 1, uf2: float = 10, 
                      uf3: float = 10, uf4: float = 1, uf5: float = 1) -> float:
    """
    Section 4.2.1.1 - Calculate ADE/PDE
    PDE = (NOAEL x BW) / (F1 x F2 x F3 x F4 x F5)
    """
    return (noael * bw) / (uf1 * uf2 * uf3 * uf4 * uf5)

def calculate_ttc(compound_type: str) -> float:
    """
    Section 4.2.1.3 - Threshold of Toxicological Concern
    Returns value in mg/day
    """
    ttc_values = {
        "carcinogenic": 0.001,
        "potent": 0.010,
        "standard": 0.100
    }
    return ttc_values.get(compound_type, 0.100)

def calculate_maco_ade(ade_mg: float, min_batch_mg: float, 
                       max_dose_mg: float, pf: float = 1.0, sf: float = 1.0) -> float:
    """
    Section 4.2.1 - MACO using ADE/PDE
    MACO = (ADE x MBS x PF) / (TDD x SF)
    """
    return (ade_mg * min_batch_mg * pf) / (max_dose_mg * sf)

def calculate_maco_10ppm(min_batch_kg: float) -> float:
    """
    Section 4.2.2 - MACO using 10 ppm general limit
    MACO = 0.00001 x MBS (mg)
    """
    return 0.00001 * (min_batch_kg * 1000000)

def calculate_maco_ttc(ttc_mg: float, min_batch_kg: float) -> float:
    """
    Section 4.2.1.3 - MACO using TTC
    MACO = TTC x MBS
    """
    return ttc_mg * (min_batch_kg * 1000000)

def calculate_swab_limit(maco_mg: float, swab_area_dm2: float, 
                         total_area_dm2: float, recovery_percent: float) -> float:
    """
    Section 4.2.4 - Swab Limit
    Limit = (MACO x Swab Area) / (Total Area x Recovery)
    """
    if total_area_dm2 <= 0:
        return 0
    limit = (maco_mg * swab_area_dm2) / total_area_dm2
    recovery = recovery_percent / 100 if recovery_percent > 0 else 1
    return limit / recovery if recovery > 0 else 0

def calculate_rinse_limit(maco_mg: float, equipment_area_dm2: float, 
                          total_area_dm2: float, rinse_volume_l: float) -> tuple:
    """
    Section 4.2.5 - Rinse Limit
    Returns (limit_mg, limit_ppm)
    """
    if total_area_dm2 <= 0:
        return (0, 0)
    limit_mg = (maco_mg * equipment_area_dm2) / total_area_dm2
    limit_ppm = limit_mg / rinse_volume_l if rinse_volume_l > 0 else 0
    return (limit_mg, limit_ppm)

def calculate_carry_over_swab(swab_results: list, areas: list, 
                              recovery_factors: list) -> float:
    """
    Section 4.2.4 - Total Carry Over from swab results
    CO = Σ(Ai x mi / Ri)
    """
    total = 0
    for result, area, recovery in zip(swab_results, areas, recovery_factors):
        total += (area * result) / recovery if recovery > 0 else 0
    return total

def calculate_carry_over_rinse(concentration_mg_l: float, volume_l: float, 
                               blank_mg_l: float = 0) -> float:
    """
    Section 8.3.2 - Carry Over from rinse samples
    CO = V x (C - Cb)
    """
    return volume_l * (concentration_mg_l - blank_mg_l)

def get_cleaning_level(previous_step: int, next_step: int, 
                       same_chain: bool, is_toxic: bool) -> str:
    """
    Section 5.2 - Determine cleaning level
    Returns: "LEVEL_0", "LEVEL_1", or "LEVEL_2"
    """
    if same_chain and next_step == previous_step + 1:
        return "LEVEL_0"
    if is_toxic or not same_chain:
        return "LEVEL_2"
    return "LEVEL_1"

def get_worst_case_rating(solubility: str, difficulty: str, 
                          ade_pde: float, min_dose: float) -> int:
    """
    Section 7.4 - Calculate worst case rating
    Higher score = worse case
    """
    solubility_scores = {
        "Very Soluble": 1, "Freely Soluble": 1,
        "Soluble": 2, "Sparingly Soluble": 2,
        "Slightly Soluble": 3, "Practically Insoluble": 3
    }
    difficulty_scores = {
        "Very Easy": 1, "Easy": 1,
        "Medium": 2, "Difficult": 3, "Very Difficult": 3
    }
    
    score = solubility_scores.get(solubility, 2)
    score += difficulty_scores.get(difficulty, 2)
    
    if ade_pde < 10:
        score += 5
    elif ade_pde < 100:
        score += 3
    elif ade_pde < 500:
        score += 2
    else:
        score += 1
    
    if min_dose < 1:
        score += 5
    elif min_dose < 10:
        score += 3
    elif min_dose < 100:
        score += 2
    else:
        score += 1
    
    return score