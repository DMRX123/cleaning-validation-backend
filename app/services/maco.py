from sqlalchemy.orm import Session
from ..models.product import Product
from ..models.dosage_form import DosageForm, ProductDosageForm
import logging

logger = logging.getLogger(__name__)


class MACOService:
    """
    MACO Calculation as per APIC Guideline 2021 & IPCA Impact Assessment
    Six methods: 10ppm, 100ppm, TDD, ADE/PDE, LD50, TTC
    
    Safety Factors based on Dosage Form (Route of Administration):
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ Dosage Form        │ Safety Factor │ Justification                         │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ Oral               │ 1,000         │ 10×10×10 (Standard)                   │
    │ Parenteral         │ 10,000-100,000│ Direct bloodstream, no dilution       │
    │ Ophthalmic         │ 10,000        │ Direct eye contact                    │
    │ Topical            │ 100-1,000     │ Skin barrier provides protection      │
    │ Inhalation         │ 10,000-100,000│ Direct lung exposure                  │
    │ Nasal              │ 10,000        │ Direct mucosal absorption             │
    │ Biotech            │ 10,000-100,000│ Immunogenicity concerns               │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    Reference: APIC Cleaning Validation Guide 2021 Section 4.2.2
    EMA Guideline on Setting Health-Based Exposure Limits
    """
    
    # Base safety factor for oral products
    BASE_SAFETY_FACTOR_ORAL = 1000
    
    # Dosage form specific safety factors
    SAFETY_FACTORS = {
        # Solid Dosage Forms
        "tablet": 1000,
        "capsule": 1000,
        "powder": 1000,
        "granule": 1000,
        "pellet": 1000,
        
        # Liquid Dosage Forms (Oral)
        "oral_solution": 1000,
        "oral_suspension": 1000,
        "syrup": 1000,
        "elixir": 1000,
        "drops": 1000,
        
        # Sterile/Parenteral Dosage Forms (MORE STRINGENT)
        "injectable": 10000,      # 10x stricter than oral
        "infusion": 10000,        # 10x stricter than oral
        "ophthalmic": 10000,      # 10x stricter than oral
        "otic": 5000,             # 5x stricter than oral
        "nasal": 10000,           # 10x stricter than oral
        "inhalation": 20000,      # 20x stricter than oral
        
        # Topical Dosage Forms (LESS STRINGENT)
        "cream": 500,             # 2x less stringent than oral
        "ointment": 500,          # 2x less stringent than oral
        "gel": 500,               # 2x less stringent than oral
        "lotion": 500,            # 2x less stringent than oral
        "paste": 500,             # 2x less stringent than oral
        
        # Other
        "transdermal": 1000,      # Similar to oral
        "suppository": 1000,      # Similar to oral (rectal)
        "vaccine": 100000,        # Most stringent (immunogenicity)
    }
    
    # LD50 Safety Factor (as per APIC 2021 Section 4.2.1.2)
    LD50_SAFETY_FACTOR = 2000
    
    # Standard human body weight (as per EMA guideline)
    HUMAN_BODY_WEIGHT_KG = 50
    
    @staticmethod
    def get_safety_factor_for_product(product: Product, db: Session = None) -> int:
        """
        Get appropriate safety factor based on product's dosage form
        
        Justification: Different routes of administration have different
        absorption rates and safety margins. Parenteral products require
        stricter limits because they bypass the body's natural barriers.
        """
        if not db or not product:
            return MACOService.BASE_SAFETY_FACTOR_ORAL
        
        try:
            # Get the dosage form linked to this product
            dosage_form_link = db.query(ProductDosageForm).filter(
                ProductDosageForm.product_id == product.id
            ).first()
            
            if dosage_form_link and dosage_form_link.dosage_form:
                dosage_form_code = dosage_form_link.dosage_form.code.value if hasattr(dosage_form_link.dosage_form.code, 'value') else str(dosage_form_link.dosage_form.code)
                safety_factor = MACOService.SAFETY_FACTORS.get(dosage_form_code, MACOService.BASE_SAFETY_FACTOR_ORAL)
                
                # For parenteral products, apply additional factor if product is highly potent
                if dosage_form_code in ["injectable", "infusion", "vaccine"]:
                    if product.ade_pde and product.ade_pde < 10:  # Highly potent
                        safety_factor = safety_factor * 10  # 10x stricter
                
                return safety_factor
        except Exception as e:
            logger.warning(f"Could not get dosage form for product {product.id}: {str(e)}")
        
        return MACOService.BASE_SAFETY_FACTOR_ORAL
    
    @staticmethod
    def get_safety_factor_justification(product: Product, db: Session = None) -> dict:
        """Get justification for safety factor selection"""
        
        safety_factor = MACOService.get_safety_factor_for_product(product, db)
        
        # Get dosage form info
        dosage_form_name = "Unknown"
        if db and product:
            try:
                dosage_form_link = db.query(ProductDosageForm).filter(
                    ProductDosageForm.product_id == product.id
                ).first()
                if dosage_form_link and dosage_form_link.dosage_form:
                    dosage_form_name = dosage_form_link.dosage_form.name
            except:
                pass
        
        # Generate justification based on safety factor
        if safety_factor >= 100000:
            justification = (
                f"Safety factor of {safety_factor} is applied because {dosage_form_name} "
                f"is a parenteral/biotech product with direct systemic exposure. "
                f"This comprises: 10× for interspecies, 10× for interindividual, "
                f"10× for acute to chronic, and additional 10× for parenteral route."
            )
        elif safety_factor >= 10000:
            justification = (
                f"Safety factor of {safety_factor} is applied because {dosage_form_name} "
                f"is a parenteral/ophthalmic/inhalation product. "
                f"This comprises: 10× for interspecies, 10× for interindividual, "
                f"10× for acute to chronic, and additional 10× for non-oral route."
            )
        elif safety_factor >= 1000:
            justification = (
                f"Safety factor of {safety_factor} is applied for oral {dosage_form_name}. "
                f"This comprises: 10× for interspecies, 10× for interindividual, "
                f"and 10× for extrapolation from therapeutic dose."
            )
        elif safety_factor >= 500:
            justification = (
                f"Safety factor of {safety_factor} is applied for topical {dosage_form_name}. "
                f"This is less stringent because skin barrier provides natural protection."
            )
        else:
            justification = f"Safety factor of {safety_factor} is applied based on risk assessment."
        
        return {
            "safety_factor": safety_factor,
            "dosage_form": dosage_form_name,
            "justification": justification,
            "reference": "APIC Cleaning Validation Guide 2021 Section 4.2.2"
        }
    
    @staticmethod
    def method_10ppm(next_product: Product) -> float:
        """
        Method 1: 10 ppm approach (General Limit)
        Formula: MACO = 0.001% × MBS (mg)
        MACO = 0.00001 × MBS
        """
        if next_product and next_product.min_batch_size:
            min_batch_mg = next_product.min_batch_size * 1000000
            maco_mg = 0.00001 * min_batch_mg
            return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_100ppm(next_product: Product) -> float:
        """
        Method 2: 100 ppm approach (Alternative General Limit)
        Formula: MACO = 0.01% × MBS (mg)
        MACO = 0.0001 × MBS
        """
        if next_product and next_product.min_batch_size:
            min_batch_mg = next_product.min_batch_size * 1000000
            maco_mg = 0.0001 * min_batch_mg
            return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_tdd(previous_product: Product, next_product: Product, 
                   safety_factor: float = None, db: Session = None) -> float:
        """
        Method 3: TDD (Therapeutic Daily Dose) approach
        Formula: MACO = (Min TDD of Previous × MBS of Next) / (SF × Max TDD of Next)
        
        Safety Factor is determined based on next product's dosage form.
        Because the safety factor protects the patient receiving the next product.
        """
        # Get safety factor based on next product's dosage form
        if safety_factor is None:
            safety_factor = MACOService.get_safety_factor_for_product(next_product, db)
        
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
        Method 4: ADE/PDE approach (Health-Based Exposure Limit)
        Formula: MACO = (ADE of Previous × MBS of Next) / (Max TDD of Next)
        """
        if previous_product and next_product:
            ade_mg = previous_product.ade_pde / 1000
            max_tdd_next = next_product.max_dose
            min_batch_next_mg = next_product.min_batch_size * 1000000
            
            if max_tdd_next and max_tdd_next > 0:
                maco_mg = (ade_mg * min_batch_next_mg) / max_tdd_next
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_ld50(previous_product: Product, next_product: Product,
                    ld50_mg_per_kg: float = None, db: Session = None) -> float:
        """
        Method 5: LD50 approach (for detergents or chemicals without ADE)
        Formula: MACO = (LD50 × 50 kg × MBS) / (SF × TDD_next)
        
        Safety Factor: 2000 base × dosage form factor
        """
        # Base LD50 safety factor
        base_ld50_sf = MACOService.LD50_SAFETY_FACTOR
        
        # Additional factor based on dosage form
        dosage_factor = 1
        if db and next_product:
            sf_info = MACOService.get_safety_factor_for_product(next_product, db)
            # For parenteral products, apply stricter factor
            if sf_info >= 10000:
                dosage_factor = 10
        
        total_safety_factor = base_ld50_sf * dosage_factor
        
        if ld50_mg_per_kg is None:
            ld50_mg_per_kg = 500
        
        if previous_product and next_product:
            max_tdd_next = next_product.max_dose
            min_batch_next_mg = next_product.min_batch_size * 1000000
            
            if max_tdd_next and max_tdd_next > 0:
                maco_mg = (ld50_mg_per_kg * MACOService.HUMAN_BODY_WEIGHT_KG * min_batch_next_mg) / (total_safety_factor * max_tdd_next)
                return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def method_ttc(next_product: Product, ttc_category: str = "standard") -> float:
        """
        Method 6: TTC (Threshold of Toxicological Concern) approach
        Formula: MACO = TTC × MBS
        
        TTC Values:
        - Carcinogenic: 1 µg/day
        - Potent: 10 µg/day
        - Standard: 100 µg/day
        """
        ttc_values = {
            "carcinogenic": 0.001,
            "potent": 0.010,
            "standard": 0.100,
            "genotoxic": 0.001,
        }
        
        ttc_mg = ttc_values.get(ttc_category.lower(), 0.100)
        
        if next_product and next_product.min_batch_size:
            min_batch_next_mg = next_product.min_batch_size * 1000000
            maco_mg = ttc_mg * min_batch_next_mg
            return round(maco_mg, 2)
        return 0
    
    @staticmethod
    def calculate_all(previous_product: Product, next_product: Product,
                      ld50_mg_per_kg: float = None,
                      ttc_category: str = "standard",
                      db: Session = None) -> dict:
        """
        Calculate all MACO methods and return lowest
        Safety factors are automatically determined based on next product's dosage form
        """
        result_10ppm = MACOService.method_10ppm(next_product)
        result_100ppm = MACOService.method_100ppm(next_product)
        result_tdd = MACOService.method_tdd(previous_product, next_product, db=db)
        result_ade_pde = MACOService.method_ade_pde(previous_product, next_product)
        result_ld50 = MACOService.method_ld50(previous_product, next_product, ld50_mg_per_kg, db)
        result_ttc = MACOService.method_ttc(next_product, ttc_category)
        
        valid_results = [
            r for r in [
                result_10ppm, result_100ppm, result_tdd, 
                result_ade_pde, result_ld50, result_ttc
            ] if r > 0
        ]
        lowest = min(valid_results) if valid_results else 0
        
        # Get safety factor justification
        sf_info = MACOService.get_safety_factor_justification(next_product, db)
        
        return {
            "method_10ppm": result_10ppm,
            "method_100ppm": result_100ppm,
            "method_tdd": result_tdd,
            "method_ade_pde": result_ade_pde,
            "method_ld50": result_ld50,
            "method_ttc": result_ttc,
            "lowest_maco": lowest,
            "selected_method": "TDD" if result_tdd == lowest else "ADE/PDE" if result_ade_pde == lowest else "10ppm",
            "safety_factor_used": sf_info["safety_factor"],
            "safety_factor_dosage_form": sf_info["dosage_form"],
            "safety_factor_justification": sf_info["justification"],
            "reference": "APIC Cleaning Validation Guide 2021 Section 4.2.2"
        }