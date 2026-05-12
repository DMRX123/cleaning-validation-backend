from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.session import ValidationSession

class SwabService:
    """Excel Swab Limit & Results calculation - Exact Excel formulas"""
    
    @staticmethod
    def calculate_mg_per_swab(maco_mg: float, swab_surface_area: float, 
                              total_surface_area: float, recovery_percent: float) -> float:
        """
        Excel Formula from Swab Limit sheet:
        = MACO x Swab Surface Area / Total Product Contact Surface Area
        With recovery correction
        """
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
        """
        Excel Formula from Swab Limit sheet:
        = (MACO x Swab Surface Area x 1000) / (Total Surface Area x Swab Dilution)
        With recovery correction
        """
        if total_surface_area <= 0 or maco_mg <= 0 or swab_dilution_ml <= 0:
            return 0
        
        result = (maco_mg * swab_surface_area * 1000) / (total_surface_area * swab_dilution_ml)
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        
        if recovery_factor > 0:
            result = result / recovery_factor
        
        return round(result, 2)
    
    @staticmethod
    def calculate_swab_limit(session: ValidationSession, total_surface_area: float) -> dict:
        """Calculate both mg/swab and ppm from session data"""
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
        """Calculate swab limit directly from products without session"""
        from .maco import MACOService
        maco_result = MACOService.calculate_all(previous_product, next_product)
        maco = maco_result["lowest_maco"]
        
        # Assume total area = equipment area (simplified)
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
        Excel Formula from Swab Result sheet:
        Result mg/ml = (Abs Sample / Abs Std) x Dilution Factor x Swab Dilution / (Recovery/100) x (100 / Potency)
        """
        if absorbance_std == 0:
            return {"mg_ml": 0, "ppm": 0, "reported": "Error - Std Abs zero"}
        
        # Main calculation as per Excel
        mg_ml = (absorbance_sample / absorbance_std) * dilution_factor * swab_dilution_ml
        
        # Apply recovery correction
        recovery_factor = recovery_percent / 100 if recovery_percent > 0 else 1
        if recovery_factor > 0:
            mg_ml = mg_ml / recovery_factor
        
        # Apply potency correction
        potency_factor = potency / 100 if potency > 0 else 1
        if potency_factor > 0:
            mg_ml = mg_ml * (100 / potency)  # Excel: *100/'Std. Prep Details'!$D$10
        
        # Convert to ppm (mg/ml * 1000 = ppm)
        ppm = mg_ml * 1000
        
        # Check against LOQ - Excel: =IF(F3>='Selelct Previous Product'!$K$4,F3,"Below LOQ")
        if ppm < loq_ppm:
            reported = "Below LOQ"
        else:
            reported = round(ppm, 2)
        
        return {
            "mg_ml": round(mg_ml, 6),
            "ppm": round(ppm, 2),
            "reported": reported
        }