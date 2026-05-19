from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.session import ValidationSession
from ..services.maco import MACOService


class SwabService:
    """APIC Section 4.2.4 - Swab Sampling Calculations"""
    
    @staticmethod
    def calculate_mg_per_swab(maco_mg: float, swab_surface_area: float, 
                              total_surface_area: float, recovery_percent: float) -> float:
        """APIC Section 4.2.4 - Target value = (MACO × Swab Area) / (Total Area × Recovery)"""
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
        """Calculate ppm from swab results"""
        if total_surface_area <= 0 or maco_mg <= 0 or swab_dilution_ml <= 0:
            return 0
        
        result = (maco_mg * swab_surface_area * 1000) / (total_surface_area * swab_dilution_ml)
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        
        if recovery_factor > 0:
            result = result / recovery_factor
        
        return round(result, 2)
    
    @staticmethod
    def calculate_swab_limit(session: ValidationSession, total_surface_area: float) -> dict:
        """Calculate swab limits for a validation session"""
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
        """Calculate swab limits for a product pair"""
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
        APIC Section 8.2.3 - Calculate residue from absorbance values
        
        Returns:
            mg_ml: Numeric value in mg/ml
            ppm_numeric: ALWAYS a number (0 if below LOQ)
            ppm_display: String for display ("Below LOQ" or value)
            reported: Same as ppm_display
            below_loq: Boolean flag
        """
        if absorbance_sample < 0:
            return {
                "mg_ml": 0, 
                "ppm_numeric": 0, 
                "ppm_display": "Error - Negative sample absorbance",
                "reported": "Error - Negative sample absorbance",
                "below_loq": True,
                "ppm": 0
            }
        if absorbance_std <= 0:
            return {
                "mg_ml": 0, 
                "ppm_numeric": 0, 
                "ppm_display": "Error - Std Abs zero or negative",
                "reported": "Error - Std Abs zero or negative",
                "below_loq": True,
                "ppm": 0
            }
        
        mg_ml = (absorbance_sample / absorbance_std) * dilution_factor * swab_dilution_ml
        
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        if recovery_factor > 0:
            mg_ml = mg_ml / recovery_factor
        
        if potency > 0 and potency != 100:
            mg_ml = mg_ml * (100 / potency)
        
        ppm = mg_ml * 1000
        ppm_numeric = round(ppm, 2)
        below_loq = ppm < loq_ppm
        
        if below_loq:
            ppm_display = "Below LOQ"
            ppm_numeric = 0.0
        else:
            ppm_display = str(ppm_numeric)
        
        return {
            "mg_ml": round(mg_ml, 6),
            "ppm_numeric": ppm_numeric,
            "ppm_display": ppm_display,
            "reported": ppm_display,
            "below_loq": below_loq,
            "ppm": ppm_numeric
        }
    
    @staticmethod
    def calculate_total_carry_over(swab_results: list, sampling_areas: list, 
                                    total_surface_area_dm2: float, 
                                    recovery_factor: float = 1.0) -> dict:
        """
        APIC Section 4.2.4 - Equation 4.2.5-II
        CO = Σ(Ai x mi)
        """
        if not swab_results or not sampling_areas:
            return {
                "total_carry_over_mg": 0,
                "status": "No data",
                "details": []
            }
        
        total_carry_over = 0.0
        details = []
        
        for idx, area in enumerate(sampling_areas):
            if idx < len(swab_results):
                result = swab_results[idx]
                if hasattr(result, 'result_ppm'):
                    residue_per_area = result.result_ppm or 0
                elif isinstance(result, dict):
                    residue_per_area = result.get('result_ppm', 0)
                else:
                    residue_per_area = 0
                
                area_dm2 = getattr(area, 'surface_area_dm2', 1.0)
                contribution = area_dm2 * residue_per_area
                total_carry_over += contribution
                
                details.append({
                    "area_name": getattr(area, 'area_name', f"Area_{idx}"),
                    "surface_area_dm2": area_dm2,
                    "residue_ppm": residue_per_area,
                    "contribution_mg": round(contribution, 4),
                    "surface_type": getattr(area, 'surface_type', 'Unknown')
                })
        
        if recovery_factor > 0:
            total_carry_over = total_carry_over / recovery_factor
        
        status = "PASS" if total_carry_over <= 1.0 else "FAIL"
        
        return {
            "total_carry_over_mg": round(total_carry_over, 4),
            "total_surface_area_dm2": total_surface_area_dm2,
            "recovery_factor_used": recovery_factor,
            "status": status,
            "details": details
        }