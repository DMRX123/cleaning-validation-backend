from ..models.standard_prep import StandardPrep

class StandardService:
    """Dilution factor calculation - Excel formula from Std. Prep Details sheet"""
    
    @staticmethod
    def calculate_dilution_factor(wt_std: float, first_dil_vol: float, 
                                  second_dil_vol: float, third_dil_vol: float,
                                  fourth_dil_vol: float, fifth_dil_vol: float,
                                  potency: float) -> float:
        """
        Excel formula from Std. Prep Details sheet:
        Dilution of Standard = (Wt of Std / 1st Dilution) x (1st Pipete out / 1st Dilution) 
                              x (2nd Pipete out / 2nd Dilution) x (3rd Pipete out / 3rd Dilution)
                              x (4th Pipete out / 4th Dilution) x (5th Pipete out / 5th Dilution)
        
        Note: In typical Excel, pipette out volume equals dilution volume when doing serial dilutions
        So (Pipette out / Dilution) = 1 for each step
        """
        if any(v == 0 for v in [first_dil_vol, second_dil_vol, third_dil_vol, fourth_dil_vol, fifth_dil_vol]):
            return 0
        
        # Step 1: First dilution
        step1 = wt_std / first_dil_vol
        
        # Each subsequent step: pipette_volume / dilution_volume
        # In standard serial dilution, these are equal so factor = 1
        step2 = second_dil_vol / second_dil_vol if second_dil_vol > 0 else 1
        step3 = third_dil_vol / third_dil_vol if third_dil_vol > 0 else 1
        step4 = fourth_dil_vol / fourth_dil_vol if fourth_dil_vol > 0 else 1
        step5 = fifth_dil_vol / fifth_dil_vol if fifth_dil_vol > 0 else 1
        
        factor = step1 * step2 * step3 * step4 * step5
        
        # Apply potency (percentage)
        potency_factor = potency / 100 if potency > 0 else 1
        factor = factor * potency_factor
        
        return round(factor, 6)
    
    @staticmethod
    def from_model(prep: StandardPrep) -> float:
        """Calculate dilution factor from StandardPrep model"""
        return StandardService.calculate_dilution_factor(
            prep.wt_of_std, 
            prep.first_dilution, 
            prep.second_dilution,
            prep.third_dilution, 
            prep.fourth_dilution, 
            prep.fifth_dilution,
            prep.potency
        )
    
    @staticmethod
    def get_dilution_steps_description(prep: StandardPrep) -> dict:
        """Return human-readable dilution steps"""
        return {
            "step1": f"Weigh {prep.wt_of_std} mg standard, dilute to {prep.first_dilution} ml",
            "step2": f"Take {prep.first_dilution} ml, dilute to {prep.second_dilution} ml",
            "step3": f"Take {prep.second_dilution} ml, dilute to {prep.third_dilution} ml",
            "step4": f"Take {prep.third_dilution} ml, dilute to {prep.fourth_dilution} ml",
            "step5": f"Take {prep.fourth_dilution} ml, dilute to {prep.fifth_dilution} ml",
            "final_dilution_factor": StandardService.from_model(prep),
            "potency": f"{prep.potency}%"
        }