# app/api/__init__.py
"""
API Routes for Cleaning Validation System
"""

from . import auth
from . import products
from . import equipment
from . import calculations
from . import validation
from . import static_data
from . import dashboard
from . import guidance
from . import cleaning_process
from . import training
from . import formulation
from . import comprehensive
from . import hold_times
from . import protocol_generator
from . import report_generator 
from . import ade 

__all__ = [
    "auth",
    "products",
    "equipment",
    "calculations",
    "validation",
    "static_data",
    "dashboard",
    "guidance",
    "cleaning_process",
    "training",
    "formulation",
    "comprehensive",
    "hold_times",
    "protocol_generator",
    "report_generator", 
    "ade",
]