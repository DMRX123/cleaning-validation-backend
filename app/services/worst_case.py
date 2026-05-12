from ..models.product import Product

class WorstCaseService:
    """Find hardest to clean product (Next Worst Case) - Excel logic"""
    
    # Solubility weights (higher number = harder to clean)
    SOLUBILITY_WEIGHTS = {
        "Very Soluble": 1,
        "Freely Soluble": 2,
        "Soluble": 3,
        "Sparingly Soluble": 4,
        "Slightly Soluble": 5,
        "Very Slightly Soluble": 6,
        "Practically Insoluble": 7
    }
    
    # Cleaning difficulty weights (higher number = harder to clean)
    DIFFICULTY_WEIGHTS = {
        "Very Easy": 1,
        "Easy": 2,
        "Medium": 3,
        "Difficult": 4,
        "Very Difficult": 5
    }
    
    @classmethod
    def get_solubility_weight(cls, solubility: str) -> int:
        return cls.SOLUBILITY_WEIGHTS.get(solubility, 3)
    
    @classmethod
    def get_difficulty_weight(cls, difficulty: str) -> int:
        return cls.DIFFICULTY_WEIGHTS.get(difficulty, 3)
    
    @classmethod
    def find_worst_case(cls, products: list[Product]) -> Product:
        """
        Find product with:
        1. Lowest solubility (highest weight)
        2. Highest cleaning difficulty (highest weight)
        3. Lowest ADE/PDE (most toxic - optional)
        
        Returns the product that is hardest to clean
        """
        if not products:
            return None
        
        def score(product: Product) -> tuple:
            solubility_score = cls.get_solubility_weight(product.solubility)
            difficulty_score = cls.get_difficulty_weight(product.hardest_to_clean)
            # Negative because we want higher solubility weight and difficulty weight
            return (-solubility_score, -difficulty_score, product.ade_pde)
        
        return min(products, key=score)
    
    @classmethod
    def get_worst_case_rankings(cls, products: list[Product]) -> list[dict]:
        """Get all products ranked by worst-case criteria"""
        if not products:
            return []
        
        ranked = []
        for product in products:
            ranked.append({
                "id": product.id,
                "name": product.name,
                "solubility": product.solubility,
                "solubility_weight": cls.get_solubility_weight(product.solubility),
                "difficulty": product.hardest_to_clean,
                "difficulty_weight": cls.get_difficulty_weight(product.hardest_to_clean),
                "ade_pde": product.ade_pde,
                "score": (-cls.get_solubility_weight(product.solubility), 
                         -cls.get_difficulty_weight(product.hardest_to_clean))
            })
        
        return sorted(ranked, key=lambda x: (x["solubility_weight"], x["difficulty_weight"]), reverse=True)