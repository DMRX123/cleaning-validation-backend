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
        sa.ForeignKeyConstraint(['next_product_id'], ['products.id'],),
        sa.ForeignKeyConstraint(['previous_product_id'], ['products.id'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_code')
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
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'],),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create swab_results table
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
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'],),
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
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'],),
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
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'],),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'],),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('session_equipment')
    op.drop_table('users')
    op.drop_table('audit_logs')
    op.drop_table('rinse_results')
    op.drop_table('swab_results')
    op.drop_table('standard_preps')
    op.drop_table('validation_sessions')
    op.drop_table('equipment')
    op.drop_table('products')