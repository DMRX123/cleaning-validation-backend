from ..models.equipment import Equipment
from ..models.product import Product

class EquipmentFilterService:
    """Filter equipment based on previous product and plant - Excel logic"""
    
    @staticmethod
    def filter_by_plant(equipment_list: list[Equipment], plant_name: str) -> list[Equipment]:
        """Show only equipment used in specified plant"""
        if not plant_name:
            return equipment_list
        return [eq for eq in equipment_list if eq.plant == plant_name]
    
    @staticmethod
    def filter_by_previous_product(equipment_list: list[Equipment], 
                                   previous_product: Product) -> list[Equipment]:
        """
        Filter equipment that are common for previous product
        In Excel, equipment are listed based on previous worst case product
        """
        if not previous_product or not previous_product.plant:
            return equipment_list
        
        # Filter by plant of previous product
        return EquipmentFilterService.filter_by_plant(equipment_list, previous_product.plant)
    
    @staticmethod
    def calculate_total_surface_area(equipment_list: list[Equipment]) -> float:
        """Sum all equipment surface areas - Excel SUM function"""
        return sum(eq.surface_area for eq in equipment_list)
    
    @staticmethod
    def get_equipment_by_ids(equipment_list: list[Equipment], ids: list[int]) -> list[Equipment]:
        """Get specific equipment by IDs"""
        id_set = set(ids)
        return [eq for eq in equipment_list if eq.id in id_set]
    
    @staticmethod
    def get_worst_case_equipment(equipment_list: list[Equipment]) -> Equipment:
        """Get equipment with largest surface area (worst case)"""
        if not equipment_list:
            return None
        return max(equipment_list, key=lambda eq: eq.surface_area)
    
    @staticmethod
    def format_equipment_table(equipment_list: list[Equipment]) -> list[dict]:
        """Format equipment for display - matches Excel table format"""
        return [
            {
                "sr_no": idx + 1,
                "eq_name": eq.name,
                "eq_id": eq.equipment_id,
                "capacity": eq.capacity,
                "surface_area_m2": eq.surface_area,
                "used_for": eq.used_for,
                "cleaning_procedure": eq.cleaning_procedure
            }
            for idx, eq in enumerate(equipment_list)
        ]