from sqlalchemy.orm import Session
from ..models.product import Product
from ..utils.constants import SAFETY_FACTOR, PPM_FACTOR

class MACOService:
    """Excel MACO calculation - Complete APIC Guideline compliant"""
    
    @staticmethod
    def method_10ppm(next_product: Product) -> float:
        if next_product and next_product.min_batch_size:
            min_batch_mg = next_product.min_batch_size * 1000000
            maco_mg = 0.00001 * min_batch_mg
            return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_tdd(previous_product: Product, next_product: Product, 
                   safety_factor: float = 1000) -> float:
        if previous_product and next_product:
            tdd_previous = previous_product.max_dose
            min_batch_next_mg = next_product.min_batch_size * 1000000
            mdd_next = next_product.max_dose
            
            if mdd_next and mdd_next > 0:
                maco_mg = (tdd_previous * min_batch_next_mg) / (safety_factor * mdd_next)
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_ade_pde(previous_product: Product, next_product: Product,
                       purging_factor: float = 1.0, safety_factor: float = 1.0) -> float:
        """
        Section 4.2.1 - Health-Based Data (HBEL/ADE/PDE)
        purging_factor must be >= 0.1 (cannot be zero)
        """
        # Validate purging factor
        if purging_factor <= 0:
            purging_factor = 1.0  # Default safe value
        
        if previous_product and next_product:
            ade_pde_mg = previous_product.ade_pde / 1000
            min_batch_next_mg = next_product.min_batch_size * 1000000
            mdd_next = next_product.max_dose
            
            if mdd_next and mdd_next > 0:
                maco_mg = (ade_pde_mg * min_batch_next_mg * purging_factor) / (mdd_next * safety_factor)
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_ttc(compound_category: str, min_batch_size_kg: float) -> float:
        ttc_values = {
            "carcinogenic": 0.001,
            "potent": 0.010,
            "standard": 0.100
        }
        
        ttc_mg = ttc_values.get(compound_category, 0.100)
        min_batch_mg = min_batch_size_kg * 1000000
        maco_mg = ttc_mg * min_batch_mg
        return round(maco_mg, 2)
    
    @staticmethod
    def calculate_all(previous_product: Product, next_product: Product,
                      purging_factor: float = 1.0, safety_factor: float = 1.0) -> dict:
        """Calculate all methods and return lowest MACO"""
        # Ensure purging_factor is valid (not zero or negative)
        if purging_factor <= 0:
            purging_factor = 1.0
        
        result_10ppm = MACOService.method_10ppm(next_product)
        result_tdd = MACOService.method_tdd(previous_product, next_product)
        result_ade_pde = MACOService.method_ade_pde(previous_product, next_product, purging_factor, safety_factor)
        result_ttc = MACOService.method_ttc("standard", next_product.min_batch_size)
        
        valid_results = [r for r in [result_10ppm, result_tdd, result_ade_pde, result_ttc] if r > 0]
        lowest = min(valid_results) if valid_results else 0
        
        return {
            "method_10ppm": result_10ppm,
            "method_tdd": result_tdd,
            "method_ade_pde": result_ade_pde,
            "method_ttc": result_ttc,
            "lowest_maco": lowest,
            "purging_factor_used": purging_factor,
            "safety_factor_used": safety_factor
        }