from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.session import ValidationSession

class SwabService:
    
    @staticmethod
    def calculate_mg_per_swab(maco_mg: float, swab_surface_area: float, 
                              total_surface_area: float, recovery_percent: float) -> float:
        if total_surface_area <= 0 or maco_mg <= 0:
            return 0
        
        result = (maco_mg * swab_surface_area) / total_surface_area
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        
        if recovery_factor > 0:
            result = result / recovery_factor
        
        return round(result, 6)
    
    @staticmethod
    def calculate_ppm(maco_mg: float, swab_surface_area: float, total_surface_area: float,
                     swab_dilution_ml: float, recovery_percent: float) -> float:
        if total_surface_area <= 0 or maco_mg <= 0 or swab_dilution_ml <= 0:
            return 0
        
        result = (maco_mg * swab_surface_area * 1000) / (total_surface_area * swab_dilution_ml)
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        
        if recovery_factor > 0:
            result = result / recovery_factor
        
        return round(result, 2)
    
    @staticmethod
    def calculate_swab_limit(session: ValidationSession, total_surface_area: float) -> dict:
        if not session.next_product or not session.lowest_maco:
            return {"mg_per_swab": 0, "ppm": 0}
        
        product = session.next_product
        
        mg_per_swab = SwabService.calculate_mg_per_swab(
            session.lowest_maco, product.swab_surface_area, total_surface_area, product.swab_recovery
        )
        
        ppm = SwabService.calculate_ppm(
            session.lowest_maco, product.swab_surface_area, total_surface_area, 
            product.swab_dilution, product.swab_recovery
        )
        
        return {"mg_per_swab": mg_per_swab, "ppm": ppm}
    
    @staticmethod
    def calculate_swab_limit_for_product(previous_product: Product, next_product: Product, equipment_area: float) -> dict:
        from .maco import MACOService
        maco_result = MACOService.calculate_all(previous_product, next_product)
        maco = maco_result["lowest_maco"]
        total_area = equipment_area
        
        mg_per_swab = SwabService.calculate_mg_per_swab(
            maco, next_product.swab_surface_area, total_area, next_product.swab_recovery
        )
        
        ppm = SwabService.calculate_ppm(
            maco, next_product.swab_surface_area, total_area, 
            next_product.swab_dilution, next_product.swab_recovery
        )
        
        return {"mg_per_swab": mg_per_swab, "ppm": ppm}
    
    @staticmethod
    def calculate_result(absorbance_sample: float, absorbance_std: float, 
                        dilution_factor: float, swab_dilution_ml: float, 
                        recovery_percent: float, loq_ppm: float, potency: float = 100) -> dict:
        """
        Excel Formula from Swab Result sheet
        Validates that absorbance values are non-negative
        """
        # Validation: absorbance values must be >= 0
        if absorbance_sample < 0:
            return {"mg_ml": 0, "ppm": 0, "reported": "Error - Negative sample absorbance"}
        if absorbance_std <= 0:
            return {"mg_ml": 0, "ppm": 0, "reported": "Error - Std Abs zero or negative"}
        
        mg_ml = (absorbance_sample / absorbance_std) * dilution_factor * swab_dilution_ml
        
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        if recovery_factor > 0:
            mg_ml = mg_ml / recovery_factor
        
        potency_factor = potency / 100 if potency > 0 else 1
        if potency_factor > 0:
            mg_ml = mg_ml * (100 / potency)
        
        ppm = mg_ml * 1000
        
        if ppm < loq_ppm:
            reported = "Below LOQ"
        else:
            reported = round(ppm, 2)
        
        return {
            "mg_ml": round(mg_ml, 6),
            "ppm": round(ppm, 2),
            "reported": reported
        }
    
    @staticmethod
    def calculate_total_carry_over(swab_results: list, sampling_areas: list, 
                                    total_surface_area_dm2: float, 
                                    recovery_factor: float = 1.0) -> dict:
        """
        Section 4.2.4 - Equation 4.2.5-II
        CO = Σ(Ai x mi)
        
        Also includes recovery correction:
        True CO = (1/WF) x [Ftot x Σ((Mi/Fi)/N)]
        
        Args:
            swab_results: List of SwabResult objects or dicts with result_ppm
            sampling_areas: List of SwabSamplingArea objects with surface_area_dm2
            total_surface_area_dm2: Total equipment surface area
            recovery_factor: Overall recovery factor (WF)
        
        Returns:
            Dict with total carry-over, status, and per-area breakdown
        """
        if not swab_results or not sampling_areas:
            return {
                "total_carry_over_mg": 0,
                "status": "No data",
                "details": []
            }
        
        total_carry_over = 0.0
        details = []
        
        # Build mapping of result to area (by index or location)
        for idx, area in enumerate(sampling_areas):
            if idx < len(swab_results):
                result = swab_results[idx]
                # Convert ppm to mg per dm²
                # ppm = mg/L, but for swab: result_ppm is mg per swab area (dm²)
                # Assume result_ppm is already in mg per swab area (dm²)
                residue_per_area = result.result_ppm if hasattr(result, 'result_ppm') else result.get('result_ppm', 0)
                
                # Per-area contribution
                contribution = area.surface_area_dm2 * residue_per_area
                total_carry_over += contribution
                
                details.append({
                    "area_name": area.area_name,
                    "surface_area_dm2": area.surface_area_dm2,
                    "residue_ppm": residue_per_area,
                    "contribution_mg": round(contribution, 4),
                    "surface_type": area.surface_type
                })
        
        # Apply recovery correction (Equation 6 style)
        if recovery_factor > 0:
            total_carry_over = total_carry_over / recovery_factor
        
        return {
            "total_carry_over_mg": round(total_carry_over, 4),
            "total_surface_area_dm2": total_surface_area_dm2,
            "recovery_factor_used": recovery_factor,
            "status": "PASS" if total_carry_over <= 1.0 else "FAIL",  # Threshold configurable
            "details": details
        }