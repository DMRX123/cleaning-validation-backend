from sqlalchemy.orm import Session
from ..models.bracketing import BracketingGroup, BracketingProduct, BracketingWorstCase
from ..models.product import Product

class BracketingService:
    SOLUBILITY_RATINGS = {
        "Very Soluble": 1, "Freely Soluble": 1, "Soluble": 2,
        "Sparingly Soluble": 2, "Slightly Soluble": 3,
        "Very Slightly Soluble": 3, "Practically Insoluble": 3, "Insoluble": 3
    }
    
    DIFFICULTY_RATINGS = {
        "Very Easy": 1, "Easy": 1, "Medium": 2, "Difficult": 3, "Very Difficult": 3
    }
    
    @classmethod
    def calculate_product_rating(cls, product):
        difficulty_rating = cls.DIFFICULTY_RATINGS.get(product.hardest_to_clean, 2)
        solubility_rating = cls.SOLUBILITY_RATINGS.get(product.solubility, 2)
        
        if product.ade_pde > 500: toxicity_rating = 1
        elif product.ade_pde > 100: toxicity_rating = 2
        elif product.ade_pde > 10: toxicity_rating = 3
        elif product.ade_pde > 1: toxicity_rating = 4
        else: toxicity_rating = 5
        
        if product.min_dose > 1000: dose_rating = 1
        elif product.min_dose > 100: dose_rating = 2
        elif product.min_dose > 10: dose_rating = 3
        elif product.min_dose > 1: dose_rating = 4
        else: dose_rating = 5
        
        total_rating = difficulty_rating + solubility_rating + toxicity_rating + dose_rating
        
        return {
            "product_id": product.id,
            "product_name": product.name,
            "total_rating": total_rating,
            "ratings": {
                "hardest_to_clean": difficulty_rating,
                "solubility": solubility_rating,
                "toxicity": toxicity_rating,
                "dose": dose_rating
            }
        }
    
    @classmethod
    def create_bracketing_matrix(cls, products):
        matrix = []
        for product in products:
            rating = cls.calculate_product_rating(product)
            matrix.append({
                "Substance": product.name,
                "Cleaning Method Class": cls._get_cleaning_class(product),
                "a) Hardest to clean": rating["ratings"]["hardest_to_clean"],
                "b) Solubility": rating["ratings"]["solubility"],
                "c) ADE/PDE": rating["ratings"]["toxicity"],
                "d) Therapeutic dose": rating["ratings"]["dose"],
                "Total Rating": rating["total_rating"]
            })
        
        sorted_matrix = sorted(matrix, key=lambda x: x["Total Rating"], reverse=True)
        worst_case = sorted_matrix[0] if sorted_matrix else None
        
        return {
            "bracketing_matrix": sorted_matrix,
            "worst_case_product": worst_case,
            "total_products_in_bracket": len(products),
            "recommendation": f"Select {worst_case['Substance']} as the worst case for validation" if worst_case else "No products to validate"
        }
    
    @staticmethod
    def _get_cleaning_class(product):
        if product.solubility in ["Very Soluble", "Freely Soluble"]:
            return "Class I (Water soluble)"
        elif product.solubility in ["Soluble", "Sparingly Soluble"]:
            return "Class II (Methanol soluble)"
        elif product.solubility in ["Slightly Soluble"]:
            return "Class III (Acetone soluble)"
        else:
            return "Class IV (Special procedure)"
