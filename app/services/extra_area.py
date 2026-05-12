class ExtraAreaService:
    """X% extra surface area for worst case - Excel formula"""
    
    @staticmethod
    def calculate_with_extra(base_area: float, extra_percentage: float) -> float:
        """
        Excel formula from Equipment Details sheet:
        = BaseArea + (BaseArea * ExtraPercentage/100)
        or = BaseArea * (1 + ExtraPercentage/100)
        """
        if extra_percentage < 0:
            extra_percentage = 0
        result = base_area * (1 + extra_percentage / 100)
        return round(result, 4)
    
    @staticmethod
    def apply_extra_to_total(total_area: float, extra_percentage: float) -> float:
        """Apply extra percentage to total surface area"""
        return ExtraAreaService.calculate_with_extra(total_area, extra_percentage)
    
    @staticmethod
    def get_worst_case_area(equipment_areas: list[float], extra_percentage: float) -> float:
        """Apply extra area to worst case equipment only"""
        if not equipment_areas:
            return 0
        
        max_area = max(equipment_areas)
        return ExtraAreaService.calculate_with_extra(max_area, extra_percentage)
    
    @staticmethod
    def calculate_individual_extra_areas(equipment_list: list, extra_percentage: float) -> list[dict]:
        """Calculate extra area for each equipment"""
        result = []
        for eq in equipment_list:
            result.append({
                "name": eq.name,
                "original_area": eq.surface_area,
                "extra_percentage": extra_percentage,
                "area_with_extra": ExtraAreaService.calculate_with_extra(eq.surface_area, extra_percentage),
                "increase": ExtraAreaService.calculate_with_extra(eq.surface_area, extra_percentage) - eq.surface_area
            })
        return result