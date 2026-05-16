from ..models.session import ValidationSession

class RinseService:
    
    @staticmethod
    def calculate_rinse_limit(maco_mg: float, equipment_surface_area: float, 
                              total_surface_area: float) -> float:
        if total_surface_area is None or total_surface_area <= 0:
            return 0.0
        if maco_mg is None or maco_mg <= 0:
            return 0.0
        if equipment_surface_area is None or equipment_surface_area <= 0:
            return 0.0
        
        limit_mg = (float(maco_mg) * float(equipment_surface_area)) / float(total_surface_area)
        return round(limit_mg, 4)
    
    @staticmethod
    def calculate_ppm_from_limit(limit_mg: float, rinse_volume_l: float) -> float:
        if rinse_volume_l is None or rinse_volume_l <= 0:
            return 0.0
        if limit_mg is None or limit_mg <= 0:
            return 0.0
        
        ppm = float(limit_mg) / float(rinse_volume_l)
        return round(ppm, 2)
    
    @staticmethod
    def calculate_volume_by_loq(limit_mg: float, loq_ppm: float):
        if loq_ppm is None or loq_ppm <= 0:
            return {"volume_l": 0.0, "warning": None}
        if limit_mg is None or limit_mg <= 0:
            return {"volume_l": 0.0, "warning": None}
        
        volume_l = float(limit_mg) / float(loq_ppm)
        volume_l = round(volume_l, 2)
        
        warning = None
        if volume_l > 5000:
            warning = f"Required rinse volume ({volume_l} L) exceeds practical limit of 5000 L. Consider increasing LOQ or reducing MACO."
        elif volume_l > 1000:
            warning = f"Required rinse volume ({volume_l} L) is very high. Verify LOQ and MACO calculations."
        
        return {"volume_l": volume_l, "warning": warning}
    
    @staticmethod
    def calculate_volume_by_10ppm(limit_mg: float) -> float:
        if limit_mg is None or limit_mg <= 0:
            return 0.0
        
        volume_l = float(limit_mg) / 10
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_amv(swab_dilution_ml: float, swab_surface_area_m2: float, 
                                equipment_surface_area_m2: float) -> float:
        if swab_surface_area_m2 is None or swab_surface_area_m2 <= 0:
            return 0.0
        if swab_dilution_ml is None or swab_dilution_ml <= 0:
            return 0.0
        if equipment_surface_area_m2 is None or equipment_surface_area_m2 <= 0:
            return 0.0
        
        volume_l = (float(swab_dilution_ml) / float(swab_surface_area_m2)) * float(equipment_surface_area_m2) / 1000
        return round(volume_l, 2)
    
    @staticmethod
    def check_acceptability(actual_ppm: float, limit_ppm: float, volume_l: float, 
                           volume_limit_l: float, loq_ppm: float) -> dict:
        conditions = [
            volume_l <= volume_limit_l if volume_limit_l and volume_limit_l > 0 else True,
            actual_ppm <= limit_ppm if limit_ppm and limit_ppm > 0 else True,
            volume_l <= volume_limit_l if volume_limit_l and volume_limit_l > 0 else True
        ]
        
        is_acceptable = all(conditions)
        
        return {
            "acceptable": "Acceptable" if is_acceptable else "Not Acceptable",
            "conditions": {
                "volume_ok": conditions[0],
                "ppm_ok": conditions[1],
                "loq_volume_ok": conditions[2]
            }
        }
    
    @staticmethod
    def calculate_carry_over_with_blank(concentration_mg_per_l: float, 
                                         volume_l: float,
                                         blank_mg_per_l: float = 0.0) -> dict:
        if volume_l is None or volume_l <= 0:
            return {
                "carry_over_mg": 0,
                "status": "Invalid volume",
                "warning": "Rinse volume must be greater than 0"
            }
        
        c_val = float(concentration_mg_per_l) if concentration_mg_per_l else 0.0
        b_val = float(blank_mg_per_l) if blank_mg_per_l else 0.0
        net_concentration = max(0.0, c_val - b_val)
        carry_over_mg = net_concentration * float(volume_l)
        
        warning = None
        if b_val > c_val * 0.5 and c_val > 0:
            warning = "Blank value is high relative to sample. Consider using different solvent lot."
        
        return {
            "carry_over_mg": round(carry_over_mg, 4),
            "sample_concentration_mg_l": c_val,
            "blank_concentration_mg_l": b_val,
            "net_concentration_mg_l": round(net_concentration, 4),
            "rinse_volume_l": float(volume_l),
            "warning": warning
        }