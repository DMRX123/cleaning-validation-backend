from ..models.session import ValidationSession

class RinseService:
    """APIC Section 4.2.5 - Rinse Sampling Calculations"""
    
    @staticmethod
    def calculate_rinse_limit(maco_mg: float, equipment_surface_area: float, 
                              total_surface_area: float) -> float:
        """APIC Section 4.2.5 - Target value = MACO(mg) / Volume of rinse(L)"""
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
        """Convert limit mg to ppm (mg/L = ppm)"""
        if rinse_volume_l is None or rinse_volume_l <= 0:
            return 0.0
        if limit_mg is None or limit_mg <= 0:
            return 0.0
        
        ppm = float(limit_mg) / float(rinse_volume_l)
        return round(ppm, 2)
    
    @staticmethod
    def calculate_volume_by_loq(limit_mg: float, loq_ppm: float):
        """APIC Section 8.2.3 - Volume required to reach LOQ"""
        if loq_ppm is None or loq_ppm <= 0:
            return {"volume_l": 0.0, "warning": "LOQ not defined - please set LOQ value"}
        if limit_mg is None or limit_mg <= 0:
            return {"volume_l": 0.0, "warning": "MACO not calculated - please calculate MACO first"}
        
        volume_l = float(limit_mg) / float(loq_ppm)
        volume_l = round(volume_l, 2)
        
        warning = None
        if volume_l > 5000:
            warning = f"Required rinse volume ({volume_l} L) exceeds practical limit of 5000 L. Consider increasing LOQ or reducing MACO."
        elif volume_l > 1000:
            warning = f"Required rinse volume ({volume_l} L) is very high. Verify LOQ and MACO calculations."
        elif volume_l <= 0:
            warning = "Calculated volume is zero or negative. Check input values."
        
        return {"volume_l": volume_l, "warning": warning}
    
    @staticmethod
    def calculate_volume_by_10ppm(limit_mg: float) -> float:
        """Volume required to achieve 10 ppm concentration"""
        if limit_mg is None or limit_mg <= 0:
            return 0.0
        
        volume_l = float(limit_mg) / 10.0
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_amv(swab_dilution_ml: float, swab_surface_area_m2: float, 
                                equipment_surface_area_m2: float) -> float:
        """AMV (Analytical Method Validation) based volume"""
        if swab_surface_area_m2 is None or swab_surface_area_m2 <= 0:
            return 0.0
        if swab_dilution_ml is None or swab_dilution_ml <= 0:
            return 0.0
        if equipment_surface_area_m2 is None or equipment_surface_area_m2 <= 0:
            return 0.0
        
        volume_l = (float(swab_dilution_ml) / float(swab_surface_area_m2)) * float(equipment_surface_area_m2) / 1000
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_carry_over(concentration_mg_per_l: float, volume_l: float,
                             blank_mg_per_l: float = 0.0) -> dict:
        """APIC Section 8.3.2 - Equation 5: CO = V × (C - Cb)"""
        if volume_l is None or volume_l <= 0:
            return {
                "carry_over_mg": 0,
                "status": "Invalid volume",
                "warning": "Rinse volume must be greater than 0",
                "sample_concentration_mg_l": 0,
                "blank_concentration_mg_l": 0,
                "net_concentration_mg_l": 0,
                "rinse_volume_l": 0
            }
        
        c_val = float(concentration_mg_per_l) if concentration_mg_per_l else 0.0
        b_val = float(blank_mg_per_l) if blank_mg_per_l else 0.0
        net_concentration = max(0.0, c_val - b_val)
        carry_over_mg = net_concentration * float(volume_l)
        
        warning = None
        if b_val > c_val * 0.5 and c_val > 0:
            warning = "Blank value is high relative to sample. Consider using different solvent lot."
        elif c_val <= 0:
            warning = "Sample concentration is zero or negative. Check analytical results."
        
        status = "PASS" if carry_over_mg <= 0 else "FAIL" if carry_over_mg > 1 else "REVIEW"
        
        return {
            "carry_over_mg": round(carry_over_mg, 4),
            "sample_concentration_mg_l": round(c_val, 4),
            "blank_concentration_mg_l": round(b_val, 4),
            "net_concentration_mg_l": round(net_concentration, 4),
            "rinse_volume_l": float(volume_l),
            "warning": warning,
            "status": status
        }
    
    @staticmethod
    def check_acceptability(actual_ppm: float, limit_ppm: float, volume_l: float, 
                           volume_limit_l: float, loq_ppm: float) -> dict:
        """Check if rinse results meet acceptance criteria"""
        volume_ok = volume_l <= volume_limit_l if volume_limit_l and volume_limit_l > 0 else True
        ppm_ok = actual_ppm <= limit_ppm if limit_ppm and limit_ppm > 0 else True
        loq_ok = volume_l <= volume_limit_l if volume_limit_l and volume_limit_l > 0 else True
        
        is_acceptable = all([volume_ok, ppm_ok, loq_ok])
        
        return {
            "acceptable": "Acceptable" if is_acceptable else "Not Acceptable",
            "conditions": {
                "volume_ok": volume_ok,
                "ppm_ok": ppm_ok,
                "loq_volume_ok": loq_ok
            },
            "actual_ppm": actual_ppm,
            "limit_ppm": limit_ppm,
            "actual_volume_l": volume_l,
            "limit_volume_l": volume_limit_l,
            "loq_ppm": loq_ppm
        }