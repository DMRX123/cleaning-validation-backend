from sqlalchemy.orm import Session
from ..models.ade_calculation import ADECalculation
from ..models.product import Product
from ..schemas.ade import ADECalculationRequest

class ADEService:
    """Section 4.2.1.1 - ADE/PDE calculation from toxicology data"""
    
    @staticmethod
    def calculate_from_noael(noael_mg_per_kg: float, bw_kg: float, 
                             uf1: float, uf2: float, uf3: float, 
                             uf4: float, uf5: float, pk: float = 1.0) -> float:
        """
        ADE = (NOAEL x BW) / (F1 x F2 x F3 x F4 x F5) x PK
        """
        denominator = uf1 * uf2 * uf3 * uf4 * uf5
        if denominator <= 0:
            return 0
        ade = (noael_mg_per_kg * bw_kg) / denominator
        ade = ade * pk
        return round(ade, 4)
    
    @staticmethod
    def calculate_from_loael(loael_mg_per_kg: float, bw_kg: float,
                              uf1: float, uf2: float, uf3: float,
                              uf4: float, uf5: float, pk: float = 1.0) -> float:
        """
        LOAEL to ADE: Add extra factor of 3-10 for LOAEL to NOAEL extrapolation
        """
        uf_loael = 3.0  # Standard factor for LOAEL to NOAEL
        denominator = uf1 * uf2 * uf3 * uf4 * uf5 * uf_loael
        if denominator <= 0:
            return 0
        ade = (loael_mg_per_kg * bw_kg) / denominator
        ade = ade * pk
        return round(ade, 4)
    
    @staticmethod
    def calculate_from_ld50(ld50_mg_per_kg: float, bw_kg: float,
                             safety_factor: float = 2000) -> float:
        """
        LD50 to ADE: ADE = (LD50 x BW) / SF
        Standard safety factor: 2000 (for conversion to daily exposure)
        """
        if safety_factor <= 0:
            safety_factor = 2000
        ade = (ld50_mg_per_kg * bw_kg) / safety_factor
        return round(ade, 4)
    
    @staticmethod
    def calculate_ttc(compound_category: str) -> float:
        """
        Section 4.2.1.3 - Threshold of Toxicological Concern
        """
        ttc_values = {
            "carcinogenic": 0.001,      # 1 µg/day
            "potent": 0.010,            # 10 µg/day
            "standard": 0.100,          # 100 µg/day
            "genotoxic": 0.001,         # 1 µg/day for genotoxic
        }
        return ttc_values.get(compound_category.lower(), 0.100)
    
    @staticmethod
    def calculate_and_save(db: Session, request: ADECalculationRequest) -> ADECalculation:
        """Calculate ADE based on available data and save to database"""
        
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        ade_value = None
        method = None
        justification = []
        
        # Priority: NOAEL > LOAEL > LD50 > TTC
        if request.noael_mg_per_kg and request.noael_mg_per_kg > 0:
            ade_value = ADEService.calculate_from_noael(
                request.noael_mg_per_kg, request.body_weight_kg,
                request.uf1, request.uf2, request.uf3, request.uf4, request.uf5,
                request.pk_adjustment
            )
            method = "NOAEL"
            justification.append(f"Calculated from NOAEL = {request.noael_mg_per_kg} mg/kg/day")
        
        elif request.loael_mg_per_kg and request.loael_mg_per_kg > 0:
            ade_value = ADEService.calculate_from_loael(
                request.loael_mg_per_kg, request.body_weight_kg,
                request.uf1, request.uf2, request.uf3, request.uf4, request.uf5,
                request.pk_adjustment
            )
            method = "LOAEL"
            justification.append(f"Calculated from LOAEL = {request.loael_mg_per_kg} mg/kg/day with UF=3")
        
        elif request.ld50_mg_per_kg and request.ld50_mg_per_kg > 0:
            ade_value = ADEService.calculate_from_ld50(request.ld50_mg_per_kg, request.body_weight_kg)
            method = "LD50"
            justification.append(f"Calculated from LD50 = {request.ld50_mg_per_kg} mg/kg with SF=2000")
        
        else:
            # Default to TTC standard
            ade_value = ADEService.calculate_ttc("standard")
            method = "TTC"
            justification.append("No toxicology data available. Using TTC standard value (100 µg/day)")
        
        # Apply route adjustment
        if request.route == "parenteral" and method != "TTC":
            # Parenteral route is more stringent (typically 1/10th of oral)
            ade_value = ade_value / 10
            justification.append(f"Parenteral route: ADE reduced by factor 10")
        
        # Create record
        ade_calc = ADECalculation(
            product_id=request.product_id,
            noael_mg_per_kg=request.noael_mg_per_kg,
            loael_mg_per_kg=request.loael_mg_per_kg,
            ld50_mg_per_kg=request.ld50_mg_per_kg,
            body_weight_kg=request.body_weight_kg,
            uf1=request.uf1,
            uf2=request.uf2,
            uf3=request.uf3,
            uf4=request.uf4,
            uf5=request.uf5,
            modifying_factor=request.modifying_factor,
            pk_adjustment=request.pk_adjustment,
            calculated_ade_mg_per_day=ade_value,
            calculation_method=method,
            calculation_justification=" | ".join(justification),
            route=request.route
        )
        
        # Update product's ADE/PDE if approved
        if ade_value and ade_value > 0:
            product.ade_pde = ade_value * 1000  # Convert to µg/day
            
        db.add(ade_calc)
        db.commit()
        db.refresh(ade_calc)
        
        return ade_calc