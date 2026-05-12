class AMVWarningService:
    """Missing data detection - Excel: 'If AMV details not mentioned' warning"""
    
    @staticmethod
    def check_product_amv_details(product) -> list[dict]:
        """Check if any AMV (Analytical Method Validation) details are missing"""
        warnings = []
        
        checks = [
            ("swab_recovery", product.swab_recovery, "Swab Recovery %", "Should be between 50-150%"),
            ("lod", product.lod, "LOD (Limit of Detection)", "Should be > 0"),
            ("loq", product.loq, "LOQ (Limit of Quantification)", "Should be > LOD"),
            ("swab_dilution", product.swab_dilution, "Swab Dilution volume", "Should be > 0"),
            ("swab_surface_area", product.swab_surface_area, "Swab Surface Area", "Should be > 0")
        ]
        
        for field_name, value, display_name, advice in checks:
            if not value or value <= 0:
                warnings.append({
                    "field": field_name,
                    "display_name": display_name,
                    "value": value,
                    "advice": advice,
                    "severity": "high" if field_name in ["loq", "swab_recovery"] else "medium"
                })
        
        # Additional validation: LOQ should be greater than LOD
        if product.lod > 0 and product.loq > 0 and product.loq <= product.lod:
            warnings.append({
                "field": "loq_lod_relation",
                "display_name": "LOQ vs LOD",
                "value": f"LOQ={product.loq}, LOD={product.lod}",
                "advice": "LOQ should be greater than LOD (typically 3-5x)",
                "severity": "high"
            })
        
        return warnings
    
    @staticmethod
    def has_warnings(product) -> bool:
        """Check if any warnings exist"""
        return len(AMVWarningService.check_product_amv_details(product)) > 0
    
    @staticmethod
    def get_warning_summary(product) -> dict:
        """Get warning summary with counts"""
        warnings = AMVWarningService.check_product_amv_details(product)
        return {
            "has_warnings": len(warnings) > 0,
            "warning_count": len(warnings),
            "high_severity_count": len([w for w in warnings if w.get("severity") == "high"]),
            "warnings": warnings
        }
    
    @staticmethod
    def get_missing_fields_message(product) -> str:
        """Get user-friendly message about missing AMV details"""
        warnings = AMVWarningService.check_product_amv_details(product)
        if not warnings:
            return "All AMV details are complete."
        
        missing_fields = [w["display_name"] for w in warnings]
        return f"Warning: Missing or invalid AMV details for: {', '.join(missing_fields)}. Please update before validation."