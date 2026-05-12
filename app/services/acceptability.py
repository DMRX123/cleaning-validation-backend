class AcceptabilityService:
    """AND/OR condition checker - Excel: =IF(AND(M3<L3,I3<L3,K3<L3),"Acceptable","Not Acceptable")"""
    
    @staticmethod
    def check_and_condition(conditions: list[bool]) -> str:
        """All conditions must be True for Acceptable"""
        if all(conditions):
            return "Acceptable"
        return "Not Acceptable"
    
    @staticmethod
    def check_or_condition(conditions: list[bool]) -> str:
        """Any condition True for Acceptable"""
        if any(conditions):
            return "Acceptable"
        return "Not Acceptable"
    
    @staticmethod
    def check_swab_acceptability(actual_ppm: float, limit_ppm: float, loq_ppm: float) -> dict:
        """
        Check if swab result is acceptable
        Acceptable if: actual_ppm < limit_ppm OR actual_ppm < loq_ppm? 
        Excel logic: Acceptable if within limit
        """
        if limit_ppm <= 0:
            return {"acceptable": "Cannot Determine", "reason": "No limit defined"}
        
        is_acceptable = actual_ppm <= limit_ppm
        
        return {
            "acceptable": "Acceptable" if is_acceptable else "Not Acceptable",
            "actual_ppm": actual_ppm,
            "limit_ppm": limit_ppm,
            "loq_ppm": loq_ppm,
            "below_limit": actual_ppm <= limit_ppm,
            "below_loq": actual_ppm <= loq_ppm
        }
    
    @staticmethod
    def check_rinse_acceptability(actual_ppm: float, limit_ppm: float, 
                                  actual_volume_l: float, limit_volume_l: float) -> dict:
        """
        Check if rinse result is acceptable
        Excel: =IF(AND(ActualVol<LimitVol, ActualPPM<LimitPPM), "Acceptable", "Not Acceptable")
        """
        conditions = []
        
        if limit_volume_l > 0:
            volume_ok = actual_volume_l <= limit_volume_l
            conditions.append(volume_ok)
        else:
            volume_ok = True
        
        if limit_ppm > 0:
            ppm_ok = actual_ppm <= limit_ppm
            conditions.append(ppm_ok)
        else:
            ppm_ok = True
        
        is_acceptable = all(conditions) if conditions else False
        
        return {
            "acceptable": "Acceptable" if is_acceptable else "Not Acceptable",
            "volume_ok": volume_ok,
            "ppm_ok": ppm_ok,
            "actual_ppm": actual_ppm,
            "limit_ppm": limit_ppm,
            "actual_volume_l": actual_volume_l,
            "limit_volume_l": limit_volume_l
        }
    
    @staticmethod
    def check_three_way_condition(value1: float, limit1: float, 
                                  value2: float, limit2: float,
                                  value3: float, limit3: float) -> str:
        """
        Excel: =IF(AND(M3<L3, I3<L3, K3<L3), "Acceptable", "Not Acceptable")
        Three conditions all must be true
        """
        conditions = [
            value1 < limit1 if limit1 > 0 else True,
            value2 < limit2 if limit2 > 0 else True,
            value3 < limit3 if limit3 > 0 else True
        ]
        return "Acceptable" if all(conditions) else "Not Acceptable"