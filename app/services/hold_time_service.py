from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.hold_time import DirtyHoldTime, CleanHoldTime, HoldTimeValidation
from ..models.equipment import Equipment

class HoldTimeService:
    """
    Section 9.7 - Dirty Hold Time (DHT) and Clean Hold Time (CHT)
    APIC Guidance: Hold times should be validated as part of cleaning validation
    """
    
    # Default hold times by equipment type (hours)
    DEFAULT_HOLD_TIMES = {
        "reactor": {"dht": 24, "cht": 72, "dht_max": 48, "cht_max": 168},
        "dryer": {"dht": 12, "cht": 168, "dht_max": 24, "cht_max": 336},
        "mill": {"dht": 8, "cht": 168, "dht_max": 16, "cht_max": 336},
        "blender": {"dht": 8, "cht": 168, "dht_max": 16, "cht_max": 336},
        "filler": {"dht": 4, "cht": 24, "dht_max": 8, "cht_max": 72},
        "centrifuge": {"dht": 12, "cht": 72, "dht_max": 24, "cht_max": 168},
        "filter": {"dht": 8, "cht": 48, "dht_max": 16, "cht_max": 120},
        "tank": {"dht": 48, "cht": 168, "dht_max": 96, "cht_max": 336}
    }
    
    @classmethod
    def get_default_limits(cls, equipment_type: str) -> dict:
        """Get recommended default hold time limits"""
        return cls.DEFAULT_HOLD_TIMES.get(equipment_type.lower(), {"dht": 24, "cht": 72, "dht_max": 48, "cht_max": 168})
    
    @classmethod
    def validate_dirty_hold_time(cls, equipment_id: int, product_name: str,
                                  end_of_batch_time: datetime,
                                  cleaning_start_time: datetime,
                                  max_dht_hours: float = None) -> dict:
        """Validate Dirty Hold Time"""
        
        actual_hours = (cleaning_start_time - end_of_batch_time).total_seconds() / 3600
        
        if max_dht_hours is None:
            max_dht_hours = cls.DEFAULT_HOLD_TIMES.get("reactor", {"dht": 24})["dht"]
        
        is_within_limit = actual_hours <= max_dht_hours
        
        result = {
            "equipment_id": equipment_id,
            "product_name": product_name,
            "end_of_batch_time": end_of_batch_time.isoformat(),
            "cleaning_start_time": cleaning_start_time.isoformat(),
            "actual_dht_hours": round(actual_hours, 2),
            "max_validated_dht_hours": max_dht_hours,
            "is_within_limit": is_within_limit,
            "status": "PASS" if is_within_limit else "FAIL"
        }
        
        if not is_within_limit:
            result["action_required"] = "RECLEAN REQUIRED: Equipment must be recleaned before use. Investigation needed."
            result["investigation_steps"] = [
                "1. Review production schedule for delays",
                "2. Check if cleaning start time was documented correctly",
                "3. Assess if residue degradation occurred during extended DHT",
                "4. Perform additional sampling if degradation is suspected",
                "5. Document findings in deviation report"
            ]
            result["risk_assessment"] = "Extended DHT may lead to dried/hardened residues that are更难 to clean. Recleaning is mandatory."
        
        return result
    
    @classmethod
    def validate_clean_hold_time(cls, equipment_id: int,
                                  cleaning_completion_time: datetime,
                                  next_use_time: datetime,
                                  max_cht_hours: float = None,
                                  storage_conditions: str = "Covered, dry, room temperature") -> dict:
        """Validate Clean Hold Time"""
        
        actual_hours = (next_use_time - cleaning_completion_time).total_seconds() / 3600
        
        if max_cht_hours is None:
            max_cht_hours = cls.DEFAULT_HOLD_TIMES.get("reactor", {"cht": 72})["cht"]
        
        is_within_limit = actual_hours <= max_cht_hours
        
        result = {
            "equipment_id": equipment_id,
            "cleaning_completion_time": cleaning_completion_time.isoformat(),
            "next_use_time": next_use_time.isoformat(),
            "actual_cht_hours": round(actual_hours, 2),
            "max_validated_cht_hours": max_cht_hours,
            "storage_conditions": storage_conditions,
            "is_within_limit": is_within_limit,
            "status": "PASS" if is_within_limit else "FAIL"
        }
        
        if not is_within_limit:
            result["action_required"] = "RECLEAN REQUIRED: Equipment has exceeded validated clean hold time."
            result["microbiological_risk"] = "Extended CHT may lead to microbial growth. Recleaning and microbiological testing required."
        
        return result
    
    @classmethod
    def extend_hold_time(cls, equipment_id: int, hold_type: str, current_max: float, requested_max: float, justification: str) -> dict:
        """
        Extend validated hold time with proper justification
        Requires additional validation studies
        """
        
        if requested_max > current_max * 1.5:
            return {
                "approved": False,
                "message": f"Extension from {current_max} to {requested_max} hours exceeds 50% increase. Requires full revalidation.",
                "required_studies": [
                    "Perform 3 consecutive cleans with extended DHT/CHT",
                    "Collect swab samples at extended time points",
                    "Perform microbiological testing at extended CHT",
                    "Document results in validation report"
                ]
            }
        
        return {
            "approved": True,
            "new_validated_hours": requested_max,
            "justification": justification,
            "condition": "Monitor first 5 batches after extension",
            "requires_approval": ["QA", "Validation"]
        }