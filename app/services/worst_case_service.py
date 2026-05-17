from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.bracketing import BracketingGroup, BracketingProduct
import logging

logger = logging.getLogger(__name__)

class WorstCaseService:
    """
    Section 7.4 - Worst Case Rating with 4 criteria (APIC Guideline)
    Rating = Hardest_to_clean × Solubility × Toxicity × Potency
    
    Reference: IPCA Laboratories Impact Assessment Document
    """
    
    # Solubility Ratings (as per PDF - Group 1,2,3)
    SOLUBILITY_RATINGS = {
        # Group 1: Very Soluble, Freely Soluble
        "Very Soluble": 1,
        "Freely Soluble": 1,
        # Group 2: Soluble, Sparingly Soluble
        "Soluble": 2,
        "Sparingly Soluble": 2,
        # Group 3: Slightly Soluble, Very Slightly Soluble, Practically Insoluble
        "Slightly Soluble": 3,
        "Very Slightly Soluble": 3,
        "Practically Insoluble": 3,
        "Insoluble": 3
    }
    
    # Cleaning Difficulty Ratings (as per PDF)
    DIFFICULTY_RATINGS = {
        "Very Easy": 1,
        "Easy": 1,
        "Medium": 2,
        "Difficult": 3,
        "Very Difficult": 3
    }
    
    # Toxicity Ratings based on ADE/PDE (µg/day) - as per PDF
    @staticmethod
    def get_toxicity_rating(ade_pde_ug_per_day: float) -> int:
        """Rating based on ADE/PDE values (lower ADE = higher rating = worse case)"""
        if ade_pde_ug_per_day < 1:
            return 5  # Most toxic
        elif ade_pde_ug_per_day < 10:
            return 4
        elif ade_pde_ug_per_day < 100:
            return 3
        elif ade_pde_ug_per_day < 500:
            return 2
        else:
            return 1  # Least toxic
    
    # Potency Ratings based on Min Therapeutic Dose (mg) - as per PDF
    @staticmethod
    def get_potency_rating(min_dose_mg: float) -> int:
        """Rating based on minimum therapeutic dose (lower dose = higher rating = worse case)"""
        if min_dose_mg < 1:
            return 5  # Most potent
        elif min_dose_mg < 10:
            return 4
        elif min_dose_mg < 100:
            return 3
        elif min_dose_mg < 1000:
            return 2
        else:
            return 1  # Least potent
    
    @classmethod
    def calculate_product_rating(cls, product) -> dict:
        """
        Calculate worst case rating using 4 criteria (MULTIPLICATION method as per PDF)
        WCR = Hardest_to_clean × Solubility × Toxicity × Potency
        """
        
        # Criterion 1: Hardest to clean (experience from production)
        difficulty_rating = cls.DIFFICULTY_RATINGS.get(product.hardest_to_clean, 2)
        
        # Criterion 2: Solubility in cleaning solvent
        solubility_rating = cls.SOLUBILITY_RATINGS.get(product.solubility, 2)
        
        # Criterion 3: Toxicity (ADE/PDE)
        toxicity_rating = cls.get_toxicity_rating(product.ade_pde)
        
        # Criterion 4: Potency (Therapeutic Daily Dose)
        potency_rating = cls.get_potency_rating(product.min_dose)
        
        # Total rating (MULTIPLICATION as per PDF)
        total_rating = difficulty_rating * solubility_rating * toxicity_rating * potency_rating
        
        return {
            "product_id": product.id,
            "product_name": product.name,
            "product_code": getattr(product, 'product_code', product.name[:6]),
            "batch_size_kg": product.min_batch_size,
            "ade_pde_ug": product.ade_pde,
            "min_dose_mg": product.min_dose,
            "max_dose_mg": product.max_dose,
            "solubility": product.solubility,
            "hardest_to_clean": product.hardest_to_clean,
            "difficulty_rating": difficulty_rating,
            "solubility_rating": solubility_rating,
            "toxicity_rating": toxicity_rating,
            "potency_rating": potency_rating,
            "total_rating": total_rating,
            "worst_case_rank": "HIGH" if total_rating >= 24 else "MEDIUM" if total_rating >= 12 else "LOW"
        }
    
    @classmethod
    def select_worst_case(cls, products, return_details: bool = False):
        """
        Select worst case product based on highest total rating
        As per PDF: Higher the rating, more difficult to clean
        """
        if not products:
            return None if not return_details else (None, [])
        
        rated_products = [cls.calculate_product_rating(p) for p in products]
        worst_case_data = max(rated_products, key=lambda x: x["total_rating"])
        
        for p in products:
            if p.id == worst_case_data["product_id"]:
                if return_details:
                    return p, rated_products
                return p
        
        return None if not return_details else (None, rated_products)
    
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
            "potency_rating": f"Minimum dose: {product.min_dose} mg (rating {rating['potency_rating']}/5 - lower dose = higher rating)"
        }
        
        return {
            "product_name": product.name,
            "ratings": rating,
            "explanations": explanations,
            "total_score": rating["total_rating"],
            "calculation_method": "WCR = Difficulty × Solubility × Toxicity × Potency",
            "worst_case_rank": "High" if rating["total_rating"] >= 24 else "Medium" if rating["total_rating"] >= 12 else "Low",
            "reference": "APIC Cleaning Validation Guide Section 7.4 & IPCA Impact Assessment"
        }