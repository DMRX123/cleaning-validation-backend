"""initial_migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('min_batch_size', sa.Float(), nullable=False),
        sa.Column('max_batch_size', sa.Float(), nullable=False),
        sa.Column('ade_pde', sa.Float(), nullable=False),
        sa.Column('min_dose', sa.Float(), nullable=False),
        sa.Column('max_dose', sa.Float(), nullable=False),
        sa.Column('swab_recovery', sa.Float(), nullable=False),
        sa.Column('lod', sa.Float(), nullable=False),
        sa.Column('loq', sa.Float(), nullable=False),
        sa.Column('swab_dilution', sa.Float(), nullable=False),
        sa.Column('swab_surface_area', sa.Float(), nullable=False),
        sa.Column('solubility', sa.String(), nullable=False),
        sa.Column('hardest_to_clean', sa.String(), nullable=False),
        sa.Column('plant', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create equipment table
    op.create_table(
        'equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('equipment_id', sa.String(), nullable=False),
        sa.Column('capacity', sa.Float(), nullable=True),
        sa.Column('surface_area', sa.Float(), nullable=False),
        sa.Column('used_for', sa.String(), nullable=False),
        sa.Column('cleaning_procedure', sa.String(), nullable=False),
        sa.Column('plant', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('equipment_id')
    )
    
    # Create cleaning_processes table
    op.create_table(
        'cleaning_processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('process_code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cleaning_type', sa.String(), nullable=False),
        sa.Column('system_boundaries', sa.Text(), nullable=True),
        sa.Column('cleaning_agents', sa.Text(), nullable=True),
        sa.Column('solvents_used', sa.Text(), nullable=True),
        sa.Column('process_steps', sa.Text(), nullable=True),
        sa.Column('equipment_ids', sa.Text(), nullable=True),
        sa.Column('has_in_process_analysis', sa.Boolean(), nullable=True),
        sa.Column('in_process_analysis_methods', sa.Text(), nullable=True),
        sa.Column('min_temperature_c', sa.Float(), nullable=True),
        sa.Column('max_temperature_c', sa.Float(), nullable=True),
        sa.Column('min_flow_rate_lpm', sa.Float(), nullable=True),
        sa.Column('max_flow_rate_lpm', sa.Float(), nullable=True),
        sa.Column('min_pressure_bar', sa.Float(), nullable=True),
        sa.Column('max_pressure_bar', sa.Float(), nullable=True),
        sa.Column('min_duration_min', sa.Float(), nullable=True),
        sa.Column('max_duration_min', sa.Float(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('validation_protocol_id', sa.Integer(), nullable=True),
        sa.Column('validation_date', sa.DateTime(), nullable=True),
        sa.Column('sop_reference', sa.String(), nullable=True),
        sa.Column('sop_version', sa.String(), nullable=True),
        sa.Column('training_required', sa.Boolean(), nullable=True),
        sa.Column('training_module_ids', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('process_code')
    )
    
    # Create cleaning_parameters table
    op.create_table(
        'cleaning_parameters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('parameter_name', sa.String(), nullable=False),
        sa.Column('parameter_unit', sa.String(), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('min_acceptable', sa.Float(), nullable=False),
        sa.Column('max_acceptable', sa.Float(), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=True),
        sa.Column('is_controlled_automatically', sa.Boolean(), nullable=True),
        sa.Column('measurement_method', sa.String(), nullable=True),
        sa.Column('measurement_frequency', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['cleaning_processes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create validation_sessions table
    op.create_table(
        'validation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_code', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('extra_area_percentage', sa.Float(), nullable=True),
        sa.Column('total_surface_area', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('previous_product_id', sa.Integer(), nullable=True),
        sa.Column('next_product_id', sa.Integer(), nullable=True),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('maco_10ppm', sa.Float(), nullable=True),
        sa.Column('maco_tdd', sa.Float(), nullable=True),
        sa.Column('maco_ade_pde', sa.Float(), nullable=True),
        sa.Column('lowest_maco', sa.Float(), nullable=True),
        sa.Column('swab_limit_mg', sa.Float(), nullable=True),
        sa.Column('swab_limit_ppm', sa.Float(), nullable=True),
        sa.Column('rinse_limit_mg', sa.Float(), nullable=True),
        sa.Column('rinse_limit_ppm', sa.Float(), nullable=True),
        sa.Column('rinse_volume_loq', sa.Float(), nullable=True),
        sa.Column('rinse_volume_10ppm', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['next_product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['previous_product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['process_id'], ['cleaning_processes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_code')
    )
    
    # Create cleaning_executions table
    op.create_table(
        'cleaning_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('execution_date', sa.DateTime(), nullable=False),
        sa.Column('executed_by', sa.String(), nullable=False),
        sa.Column('actual_temperature_c', sa.Float(), nullable=True),
        sa.Column('actual_flow_rate_lpm', sa.Float(), nullable=True),
        sa.Column('actual_pressure_bar', sa.Float(), nullable=True),
        sa.Column('actual_duration_min', sa.Float(), nullable=True),
        sa.Column('actual_concentration_percent', sa.Float(), nullable=True),
        sa.Column('temperature_within_spec', sa.Boolean(), nullable=True),
        sa.Column('flow_rate_within_spec', sa.Boolean(), nullable=True),
        sa.Column('pressure_within_spec', sa.Boolean(), nullable=True),
        sa.Column('duration_within_spec', sa.Boolean(), nullable=True),
        sa.Column('all_parameters_acceptable', sa.Boolean(), nullable=True),
        sa.Column('deviations', sa.Text(), nullable=True),
        sa.Column('deviation_justification', sa.Text(), nullable=True),
        sa.Column('in_process_results', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['cleaning_processes.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create standard_preps table
    op.create_table(
        'standard_preps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('wt_of_std', sa.Float(), nullable=False),
        sa.Column('first_dilution', sa.Float(), nullable=False),
        sa.Column('second_dilution', sa.Float(), nullable=False),
        sa.Column('third_dilution', sa.Float(), nullable=False),
        sa.Column('fourth_dilution', sa.Float(), nullable=False),
        sa.Column('fifth_dilution', sa.Float(), nullable=False),
        sa.Column('potency', sa.Float(), nullable=False),
        sa.Column('dilution_factor', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create swab_results table with below_loq column
    op.create_table(
        'swab_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('location_name', sa.String(), nullable=False),
        sa.Column('absorbance_sample', sa.Float(), nullable=False),
        sa.Column('absorbance_std', sa.Float(), nullable=False),
        sa.Column('result_mg_ml', sa.Float(), nullable=True),
        sa.Column('result_ppm', sa.Float(), nullable=True),
        sa.Column('reported', sa.String(), nullable=True),
        sa.Column('below_loq', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create rinse_results table
    op.create_table(
        'rinse_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('equipment_name', sa.String(), nullable=False),
        sa.Column('actual_rinse_volume', sa.Float(), nullable=False),
        sa.Column('absorbance_sample', sa.Float(), nullable=False),
        sa.Column('absorbance_std', sa.Float(), nullable=False),
        sa.Column('result_mg_ml', sa.Float(), nullable=True),
        sa.Column('result_ppm', sa.Float(), nullable=True),
        sa.Column('reported', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create session_equipment table
    op.create_table(
        'session_equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('rinse_volume_applied', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_sessions_previous_product', 'validation_sessions', ['previous_product_id'])
    op.create_index('idx_validation_sessions_next_product', 'validation_sessions', ['next_product_id'])
    op.create_index('idx_validation_sessions_process', 'validation_sessions', ['process_id'])
    op.create_index('idx_swab_results_session', 'swab_results', ['session_id'])
    op.create_index('idx_rinse_results_session', 'rinse_results', ['session_id'])
    op.create_index('idx_session_equipment_session', 'session_equipment', ['session_id'])
    op.create_index('idx_session_equipment_equipment', 'session_equipment', ['equipment_id'])
    op.create_index('idx_cleaning_parameters_process', 'cleaning_parameters', ['process_id'])
    op.create_index('idx_cleaning_executions_process', 'cleaning_executions', ['process_id'])
    op.create_index('idx_cleaning_executions_session', 'cleaning_executions', ['session_id'])

def downgrade() -> None:
    op.drop_index('idx_cleaning_executions_session')
    op.drop_index('idx_cleaning_executions_process')
    op.drop_index('idx_cleaning_parameters_process')
    op.drop_index('idx_session_equipment_equipment')
    op.drop_index('idx_session_equipment_session')
    op.drop_index('idx_rinse_results_session')
    op.drop_index('idx_swab_results_session')
    op.drop_index('idx_validation_sessions_process')
    op.drop_index('idx_validation_sessions_next_product')
    op.drop_index('idx_validation_sessions_previous_product')
    op.drop_table('session_equipment')
    op.drop_table('users')
    op.drop_table('audit_logs')
    op.drop_table('rinse_results')
    op.drop_table('swab_results')
    op.drop_table('standard_preps')
    op.drop_table('cleaning_executions')
    op.drop_table('validation_sessions')
    op.drop_table('cleaning_parameters')
    op.drop_table('cleaning_processes')
    op.drop_table('equipment')
    op.drop_table('products')