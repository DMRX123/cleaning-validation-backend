from app.database import engine, Base
from app.models import *
from app.models.cleaning_level import CleaningLevel
from app.models.microbiological import MicrobiologicalLimit
from app.models.hold_time import DirtyHoldTime, CleanHoldTime, HoldTimeValidation
from app.models.bracketing import BracketingGroup, BracketingProduct, BracketingWorstCase
from app.models.validation_protocol import ValidationProtocol, ProtocolExecutionResult
from app.models.change_control import ChangeControl
from app.models.training import TrainingModule, TrainingRecord
from app.models.user import User
from app.models.product import Product
from app.models.equipment import Equipment
from app.models.session import ValidationSession
from app.models.standard_prep import StandardPrep
from app.models.swab_result import SwabResult
from app.models.rinse_result import RinseResult
from app.models.session_equipment import SessionEquipment
from app.models.audit_log import AuditLog

print('Creating all tables...')
Base.metadata.create_all(bind=engine)
print('✅ Tables created successfully!')
