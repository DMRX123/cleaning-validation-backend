"""add_guideline_tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create cleaning_levels table
    op.create_table(
        'cleaning_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Enum('LEVEL_0', 'LEVEL_1', 'LEVEL_2', name='cleaninglevelenum'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('requires_visual_inspection', sa.Boolean(), nullable=True),
        sa.Column('requires_analytical_testing', sa.Boolean(), nullable=True),
        sa.Column('requires_microbiological_testing', sa.Boolean(), nullable=True),
        sa.Column('requires_validation', sa.Boolean(), nullable=True),
        sa.Column('max_residue_ppm', sa.Float(), nullable=True),
        sa.Column('safety_factor', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create cleaning_level_assignments table
    op.create_table(
        'cleaning_level_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('previous_step', sa.Integer(), nullable=True),
        sa.Column('next_step', sa.Integer(), nullable=True),
        sa.Column('same_synthetic_chain', sa.Boolean(), nullable=True),
        sa.Column('justification', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['level_id'], ['cleaning_levels.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create dirty_hold_times table
    op.create_table(
        'dirty_hold_times',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('batch_number', sa.String(), nullable=False),
        sa.Column('end_of_batch_time', sa.DateTime(), nullable=False),
        sa.Column('cleaning_start_time', sa.DateTime(), nullable=False),
        sa.Column('actual_dht_hours', sa.Float(), nullable=False),
        sa.Column('max_validated_dht_hours', sa.Float(), nullable=False),
        sa.Column('is_within_limit', sa.Boolean(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('investigation_required', sa.Boolean(), nullable=True),
        sa.Column('investigation_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create clean_hold_times table
    op.create_table(
        'clean_hold_times',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('cleaning_completion_time', sa.DateTime(), nullable=False),
        sa.Column('next_use_time', sa.DateTime(), nullable=False),
        sa.Column('actual_cht_hours', sa.Float(), nullable=False),
        sa.Column('max_validated_cht_hours', sa.Float(), nullable=False),
        sa.Column('is_within_limit', sa.Boolean(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('storage_conditions', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create microbiological_limits table
    op.create_table(
        'microbiological_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('product_type', sa.String(), nullable=False),
        sa.Column('total_germ_count_limit', sa.Float(), nullable=False),
        sa.Column('yeast_mold_limit', sa.Float(), nullable=True),
        sa.Column('endotoxin_limit', sa.Float(), nullable=True),
        sa.Column('sampling_method', sa.String(), nullable=False),
        sa.Column('sampling_frequency', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bracketing_groups table
    op.create_table(
        'bracketing_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('equipment_type', sa.String(), nullable=False),
        sa.Column('cleaning_procedure_class', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bracketing_products table
    op.create_table(
        'bracketing_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('rating_hardest_to_clean', sa.Integer(), nullable=True),
        sa.Column('rating_solubility', sa.Integer(), nullable=True),
        sa.Column('rating_toxicity', sa.Integer(), nullable=True),
        sa.Column('rating_dose', sa.Integer(), nullable=True),
        sa.Column('total_rating', sa.Integer(), nullable=True),
        sa.Column('is_worst_case', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['bracketing_groups.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create validation_protocols table
    op.create_table(
        'validation_protocols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol_number', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('background', sa.Text(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('cleaning_procedure_id', sa.String(), nullable=True),
        sa.Column('previous_product_id', sa.Integer(), nullable=True),
        sa.Column('next_product_id', sa.Integer(), nullable=True),
        sa.Column('visual_acceptance', sa.String(), nullable=True),
        sa.Column('chemical_acceptance_ppm', sa.Float(), nullable=True),
        sa.Column('microbiological_acceptance', sa.Float(), nullable=True),
        sa.Column('sampling_locations', JSON(), nullable=True),
        sa.Column('rinse_volume', sa.Float(), nullable=True),
        sa.Column('analytical_methods', JSON(), nullable=True),
        sa.Column('responsibilities', JSON(), nullable=True),
        sa.Column('training_requirements', JSON(), nullable=True),
        sa.Column('dirty_hold_time_hours', sa.Float(), nullable=True),
        sa.Column('clean_hold_time_hours', sa.Float(), nullable=True),
        sa.Column('prepared_by', sa.String(), nullable=True),
        sa.Column('prepared_date', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_date', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['next_product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['previous_product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('protocol_number')
    )
    
    # Create change_controls table
    op.create_table(
        'change_controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('change_number', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('impact_on_cleaning', sa.String(), nullable=True),
        sa.Column('impact_on_validation', sa.String(), nullable=True),
        sa.Column('risk_assessment', sa.String(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('cleaning_procedure_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('proposed_by', sa.String(), nullable=True),
        sa.Column('proposed_date', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_date', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_date', sa.DateTime(), nullable=True),
        sa.Column('implementation_date', sa.DateTime(), nullable=True),
        sa.Column('revalidation_required', sa.Boolean(), nullable=True),
        sa.Column('revalidation_completed', sa.Boolean(), nullable=True),
        sa.Column('closure_notes', sa.Text(), nullable=True),
        sa.Column('closed_by', sa.String(), nullable=True),
        sa.Column('closed_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('change_number')
    )

def downgrade() -> None:
    op.drop_table('change_controls')
    op.drop_table('validation_protocols')
    op.drop_table('bracketing_products')
    op.drop_table('bracketing_groups')
    op.drop_table('microbiological_limits')
    op.drop_table('clean_hold_times')
    op.drop_table('dirty_hold_times')
    op.drop_table('cleaning_level_assignments')
    op.drop_table('cleaning_levels')
    op.execute('DROP TYPE cleaninglevelenum')