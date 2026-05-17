from sqlalchemy.orm import Session
from ..models.product import Product
import logging

logger = logging.getLogger(__name__)

class MACOService:
    """
    MACO Calculation as per APIC Guideline & IPCA Impact Assessment
    Three methods: ADE, TDD, 10ppm
    """
    
    # Safety factor for oral products (as per PDF)
    SAFETY_FACTOR_ORAL = 1000
    
    @staticmethod
    def method_10ppm(next_product: Product) -> float:
        """
        Method 1: 10 ppm approach
        Formula: MACO = 0.001% × MBS (mg)
        MACO = (0.001 × MBS) / 100 = 0.00001 × MBS
        """
        if next_product and next_product.min_batch_size:
            min_batch_mg = next_product.min_batch_size * 1000000  # Convert kg to mg
            maco_mg = 0.00001 * min_batch_mg
            return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_tdd(previous_product: Product, next_product: Product, 
                   safety_factor: float = None) -> float:
        """
        Method 2: TDD (Therapeutic Daily Dose) approach
        Formula: MACO = (Min TDD of Previous × MBS of Next) / (SF × Max TDD of Next)
        As per PDF: SF = 1000 for oral products
        """
        if safety_factor is None:
            safety_factor = MACOService.SAFETY_FACTOR_ORAL
        
        if previous_product and next_product:
            min_tdd_prev = previous_product.min_dose
            max_tdd_next = next_product.max_dose
            min_batch_next_mg = next_product.min_batch_size * 1000000
            
            if max_tdd_next and max_tdd_next > 0 and safety_factor > 0:
                maco_mg = (min_tdd_prev * min_batch_next_mg) / (safety_factor * max_tdd_next)
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_ade_pde(previous_product: Product, next_product: Product) -> float:
        """
        Method 3: ADE/PDE approach
        Formula: MACO = (ADE of Previous × MBS of Next) / (Max TDD of Next)
        """
        if previous_product and next_product:
            ade_mg = previous_product.ade_pde / 1000  # Convert µg to mg
            max_tdd_next = next_product.max_dose
            min_batch_next_mg = next_product.min_batch_size * 1000000
            
            if max_tdd_next and max_tdd_next > 0:
                maco_mg = (ade_mg * min_batch_next_mg) / max_tdd_next
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def calculate_all(previous_product: Product, next_product: Product) -> dict:
        """
        Calculate all MACO methods and return lowest
        As per PDF: Minimum MACO is used for further calculations
        """
        result_10ppm = MACOService.method_10ppm(next_product)
        result_tdd = MACOService.method_tdd(previous_product, next_product)
        result_ade_pde = MACOService.method_ade_pde(previous_product, next_product)
        
        valid_results = [r for r in [result_10ppm, result_tdd, result_ade_pde] if r > 0]
        lowest = min(valid_results) if valid_results else 0
        
        return {
            "method_10ppm": result_10ppm,
            "method_tdd": result_tdd,
            "method_ade_pde": result_ade_pde,
            "lowest_maco": lowest,
            "selected_method": "10ppm" if result_10ppm == lowest else "TDD" if result_tdd == lowest else "ADE/PDE"
        }
    
    @staticmethod
    def calculate_maco_matrix(products: list, target_product: Product = None) -> dict:
        """
        Calculate complete MACO matrix for all product combinations
        As per PDF Table format
        """
        if not products:
            return {"error": "No products provided"}
        
        matrix = []
        product_names = [p.name for p in products]
        
        for previous in products:
            row = {
                "previous_product": previous.name,
                "previous_product_code": getattr(previous, 'product_code', previous.name[:6]),
                "ade_mg": previous.ade_pde / 1000,
                "min_tdd_mg": previous.min_dose,
                "max_tdd_mg": previous.max_dose,
                "batch_size_kg": previous.min_batch_size,
                "batch_size_mg": previous.min_batch_size * 1000000,
                "next_products": {}
            }
            
            for next_prod in products:
                if previous.id == next_prod.id:
                    continue
                
                maco_ade = MACOService.method_ade_pde(previous, next_prod)
                maco_tdd = MACOService.method_tdd(previous, next_prod)
                maco_10ppm = MACOService.method_10ppm(next_prod)
                
                lowest = min([m for m in [maco_ade, maco_tdd, maco_10ppm] if m > 0] or [0])
                
                row["next_products"][next_prod.name] = {
                    "ade_based": maco_ade,
                    "tdd_based": maco_tdd,
                    "10ppm_based": maco_10ppm,
                    "lowest_maco": lowest
                }
            
            matrix.append(row)
        
        # Calculate product-wise minimum MACO
        product_min_maco = {}
        for product in products:
            min_values = []
            for row in matrix:
                if row["previous_product"] != product.name:
                    for next_name, values in row["next_products"].items():
                        if next_name == product.name:
                            min_values.append(values["lowest_maco"])
            
            product_min_maco[product.name] = min(min_values) if min_values else 0
        
        return {
            "matrix": matrix,
            "product_min_maco": product_min_maco,
            "total_products": len(products),
            "reference": "APIC Cleaning Validation Guide Section 4.2"
        }