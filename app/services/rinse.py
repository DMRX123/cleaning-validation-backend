from ..models.session import ValidationSession

class RinseService:
    
    @staticmethod
    def calculate_rinse_limit(maco_mg: float, equipment_surface_area: float, 
                              total_surface_area: float) -> float:
        if total_surface_area <= 0 or maco_mg <= 0:
            return 0
        
        limit_mg = (maco_mg * equipment_surface_area) / total_surface_area
        return round(limit_mg, 4)
    
    @staticmethod
    def calculate_ppm_from_limit(limit_mg: float, rinse_volume_l: float) -> float:
        if rinse_volume_l <= 0 or limit_mg <= 0:
            return 0
        
        ppm = limit_mg / rinse_volume_l
        return round(ppm, 2)
    
    @staticmethod
    def calculate_volume_by_loq(limit_mg: float, loq_ppm: float) -> dict:
        """
        Returns volume with warning if volume is impractically large
        """
        if loq_ppm <= 0 or limit_mg <= 0:
            return {"volume_l": 0, "warning": None}
        
        volume_l = limit_mg / loq_ppm
        volume_l = round(volume_l, 2)
        
        warning = None
        if volume_l > 5000:
            warning = f"Required rinse volume ({volume_l} L) exceeds practical limit of 5000 L. Consider increasing LOQ or reducing MACO."
        elif volume_l > 1000:
            warning = f"Required rinse volume ({volume_l} L) is very high. Verify LOQ and MACO calculations."
        
        return {"volume_l": volume_l, "warning": warning}
    
    @staticmethod
    def calculate_volume_by_10ppm(limit_mg: float) -> float:
        if limit_mg <= 0:
            return 0
        
        volume_l = limit_mg / 10
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_amv(swab_dilution_ml: float, swab_surface_area_m2: float, 
                                equipment_surface_area_m2: float) -> float:
        if swab_surface_area_m2 <= 0:
            return 0
        
        volume_l = (swab_dilution_ml / swab_surface_area_m2) * equipment_surface_area_m2 / 1000
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_loq_recovery(limit_mg: float, loq_ppm: float) -> float:
        if loq_ppm <= 0 or limit_mg <= 0:
            return 0
        
        volume_l = limit_mg / loq_ppm
        return round(volume_l, 2)
    
    @staticmethod
    def check_acceptability(actual_ppm: float, limit_ppm: float, volume_l: float, 
                           volume_limit_l: float, loq_ppm: float) -> dict:
        conditions = [
            volume_l <= volume_limit_l if volume_limit_l > 0 else True,
            actual_ppm <= limit_ppm if limit_ppm > 0 else True,
            volume_l <= volume_limit_l if volume_limit_l > 0 else True
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
        """
        Section 4.2.5 - Equation 5
        CO = V x (C - Cb)
        
        Args:
            concentration_mg_per_l: Sample concentration in mg/L
            volume_l: Rinse volume in liters
            blank_mg_per_l: Blank concentration in mg/L
        
        Returns:
            Dict with carry-over amount and status
        """
        if volume_l <= 0:
            return {
                "carry_over_mg": 0,
                "status": "Invalid volume",
                "warning": "Rinse volume must be greater than 0"
            }
        
        net_concentration = max(0, concentration_mg_per_l - blank_mg_per_l)
        carry_over_mg = net_concentration * volume_l
        
        warning = None
        if blank_mg_per_l > concentration_mg_per_l * 0.5:
            warning = "Blank value is high relative to sample. Consider using different solvent lot."
        
        return {
            "carry_over_mg": round(carry_over_mg, 4),
            "sample_concentration_mg_l": concentration_mg_per_l,
            "blank_concentration_mg_l": blank_mg_per_l,
            "net_concentration_mg_l": round(net_concentration, 4),
            "rinse_volume_l": volume_l,
            "warning": warning
        }