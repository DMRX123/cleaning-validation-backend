"""
API Routes for Cleaning Validation System
All endpoints are organized by functionality
"""

from . import auth
from . import products
from . import equipment
from . import calculations
from . import validation
from . import reports
from . import static_data
from . import dashboard
from . import cleaning_validation
from . import protocols
from . import guidance
from . import cleaning_process

__all__ = [
    "auth",
    "products",
    "equipment",
    "calculations",
    "validation",
    "reports",
    "static_data",
    "dashboard",
    "cleaning_validation",
    "protocols",
    "guidance",
    "cleaning_process",
]