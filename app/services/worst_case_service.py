from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.bracketing import BracketingGroup, BracketingProduct

class WorstCaseService:
    """
    Section 7.4 - Worst Case Rating with 4 criteria:
    a) Hardest to clean (experience from production)
    b) Solubility in cleaning solvent
    c) ADE/PDE (toxicity)
    d) Therapeutic dose
    """
    
    SOLUBILITY_RATINGS = {
        "Very Soluble": 1, "Freely Soluble": 1,
        "Soluble": 2, "Sparingly Soluble": 2,
        "Slightly Soluble": 3, "Very Slightly Soluble": 3,
        "Practically Insoluble": 3, "Insoluble": 3
    }
    
    DIFFICULTY_RATINGS = {
        "Very Easy": 1, "Easy": 1,
        "Medium": 2, "Difficult": 3, "Very Difficult": 3
    }
    
    @classmethod
    def get_toxicity_rating(cls, ade_pde_ug_per_day: float) -> int:
        """Rating based on ADE/PDE values (lower ADE = higher rating = worse case)"""
        if ade_pde_ug_per_day < 1:
            return 5
        elif ade_pde_ug_per_day < 10:
            return 4
        elif ade_pde_ug_per_day < 100:
            return 3
        elif ade_pde_ug_per_day < 500:
            return 2
        else:
            return 1
    
    @classmethod
    def get_dose_rating(cls, min_dose_mg: float) -> int:
        """Rating based on minimum therapeutic dose (lower dose = higher rating = worse case)"""
        if min_dose_mg < 1:
            return 5
        elif min_dose_mg < 10:
            return 4
        elif min_dose_mg < 100:
            return 3
        elif min_dose_mg < 1000:
            return 2
        else:
            return 1
    
    @classmethod
    def calculate_product_rating(cls, product) -> dict:
        """Calculate worst case rating using all 4 criteria"""
        
        # Criterion 1: Hardest to clean (experience)
        difficulty_rating = cls.DIFFICULTY_RATINGS.get(product.hardest_to_clean, 2)
        
        # Criterion 2: Solubility in cleaning solvent
        solubility_rating = cls.SOLUBILITY_RATINGS.get(product.solubility, 2)
        
        # Criterion 3: Toxicity (ADE/PDE)
        toxicity_rating = cls.get_toxicity_rating(product.ade_pde)
        
        # Criterion 4: Therapeutic dose
        dose_rating = cls.get_dose_rating(product.min_dose)
        
        # Total rating (higher = worse case)
        total_rating = difficulty_rating + solubility_rating + toxicity_rating + dose_rating
        
        return {
            "product_id": product.id,
            "product_name": product.name,
            "difficulty_rating": difficulty_rating,
            "solubility_rating": solubility_rating,
            "toxicity_rating": toxicity_rating,
            "dose_rating": dose_rating,
            "total_rating": total_rating,
            "hardest_to_clean": product.hardest_to_clean,
            "solubility": product.solubility,
            "ade_pde_ug": product.ade_pde,
            "min_dose_mg": product.min_dose
        }
    
    @classmethod
    def select_worst_case(cls, products) -> Product:
        """Select worst case product based on highest total rating"""
        if not products:
            return None
        
        rated_products = [cls.calculate_product_rating(p) for p in products]
        worst_case_data = max(rated_products, key=lambda x: x["total_rating"])
        
        for p in products:
            if p.id == worst_case_data["product_id"]:
                return p
        
        return None
    
    @classmethod
    def get_worst_case_ranking(cls, products) -> list:
        """Get all products ranked by worst-case criteria"""
        if not products:
            return []
        
        rated = [cls.calculate_product_rating(p) for p in products]
        return sorted(rated, key=lambda x: x["total_rating"], reverse=True)
    
    @classmethod
    def get_rating_explanation(cls, product) -> dict:
        """Get detailed explanation of rating for documentation"""
        rating = cls.calculate_product_rating(product)
        
        explanations = {
            "difficulty_rating": f"Cleaning difficulty: {product.hardest_to_clean} (rating {rating['difficulty_rating']}/3)",
            "solubility_rating": f"Solubility: {product.solubility} (rating {rating['solubility_rating']}/3 - higher means harder to clean)",
            "toxicity_rating": f"ADE/PDE: {product.ade_pde} µg/day (rating {rating['toxicity_rating']}/5 - lower ADE = higher rating)",
            "dose_rating": f"Minimum dose: {product.min_dose} mg (rating {rating['dose_rating']}/5 - lower dose = higher rating)"
        }
        
        return {
            "product_name": product.name,
            "ratings": rating,
            "explanations": explanations,
            "total_score": rating["total_rating"],
            "worst_case_rank": "High" if rating["total_rating"] >= 10 else "Medium" if rating["total_rating"] >= 7 else "Low"
        }