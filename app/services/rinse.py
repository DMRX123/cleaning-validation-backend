from ..models.session import ValidationSession

class RinseService:
    """Excel Rinse Limit & Volume calculation - Exact Excel formulas"""
    
    @staticmethod
    def calculate_rinse_limit(maco_mg: float, equipment_surface_area: float, 
                              total_surface_area: float) -> float:
        """
        Excel Formula from Rinse Limit & Rinse Volume sheet:
        = MACO x Equipment Surface Area / Total Product Contact Surface Area
        """
        if total_surface_area <= 0 or maco_mg <= 0:
            return 0
        
        limit_mg = (maco_mg * equipment_surface_area) / total_surface_area
        return round(limit_mg, 4)
    
    @staticmethod
    def calculate_ppm_from_limit(limit_mg: float, rinse_volume_l: float) -> float:
        """
        Convert mg limit to ppm based on rinse volume
        ppm = (mg/L) = mg / (L * 1000) * 1000 = mg / L
        """
        if rinse_volume_l <= 0 or limit_mg <= 0:
            return 0
        
        ppm = limit_mg / rinse_volume_l
        return round(ppm, 2)
    
    @staticmethod
    def calculate_volume_by_loq(limit_mg: float, loq_ppm: float) -> float:
        """
        Excel Formula from Rinse Limit & Rinse Volume sheet:
        = Limit (mg) / LOQ (ppm)
        Minimum rinse volume required to detect at LOQ
        """
        if loq_ppm <= 0 or limit_mg <= 0:
            return 0
        
        volume_l = limit_mg / loq_ppm
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_10ppm(limit_mg: float) -> float:
        """
        Excel Formula from Rinse Limit & Rinse Volume sheet:
        = Limit (mg) / 10
        Volume in L based on 10 ppm standard
        """
        if limit_mg <= 0:
            return 0
        
        volume_l = limit_mg / 10
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_amv(swab_dilution_ml: float, swab_surface_area_m2: float, 
                                equipment_surface_area_m2: float) -> float:
        """
        Excel Formula from Rinse Limit & Rinse Volume sheet:
        = (Swab Dilution / Swab Surface Area) x Equipment Surface Area / 1000
        Rinse Volume in L as per AMV
        """
        if swab_surface_area_m2 <= 0:
            return 0
        
        volume_l = (swab_dilution_ml / swab_surface_area_m2) * equipment_surface_area_m2 / 1000
        return round(volume_l, 2)
    
    @staticmethod
    def calculate_volume_by_loq_recovery(limit_mg: float, loq_ppm: float) -> float:
        """
        Excel Formula from Rinse Limit & Rinse Volume sheet:
        = Limit (mg) / LOQ (ppm)
        Rinse Volume in L as per LOQ if recovery performed at LOQ
        """
        if loq_ppm <= 0 or limit_mg <= 0:
            return 0
        
        volume_l = limit_mg / loq_ppm
        return round(volume_l, 2)
    
    @staticmethod
    def check_acceptability(actual_ppm: float, limit_ppm: float, volume_l: float, 
                           volume_limit_l: float, loq_ppm: float) -> dict:
        """
        Excel Formula: =IF(AND(ActualRinseVol<LimitVol, LimitPPM<ActualPPM, VolumeByLOQ<ActualVol), 
                        "Acceptable", "Not Acceptable")
        """
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