# migrations/versions/004_add_formulation_tables.py

"""add_formulation_tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create ENUM types
    dosage_form_enum = ENUM('tablet', 'capsule', 'powder', 'granule', 'pellet',
                            'oral_solution', 'oral_suspension', 'syrup', 'elixir', 'drops',
                            'cream', 'ointment', 'gel', 'lotion', 'paste',
                            'injectable', 'infusion', 'ophthalmic', 'otic', 'nasal', 'inhalation',
                            'transdermal', 'suppository', 'vaccine',
                            name='dosageformenum', create_type=True)
    dosage_form_enum.create(op.get_bind(), checkfirst=True)
    
    plant_type_enum = ENUM('api_plant', 'formulation_osd', 'formulation_sterile',
                           'formulation_liquid', 'formulation_ophthalmic', 'formulation_topical',
                           'formulation_inhalation', 'biotech',
                           name='planttypeenum', create_type=True)
    plant_type_enum.create(op.get_bind(), checkfirst=True)
    
    sampling_method_enum = ENUM('swab', 'rinse', 'contact_plate', 'direct_inoculation', 'air_sampling',
                                name='samplingmethodenum', create_type=True)
    sampling_method_enum.create(op.get_bind(), checkfirst=True)
    
    equipment_category_enum = ENUM('sifter', 'granulator', 'dryer', 'mill', 'blender',
                                   'tablet_press', 'coater', 'capsule_filler',
                                   'mixing_tank', 'storage_tank', 'filling_machine', 'capping_machine',
                                   'autoclave', 'laminar_airflow', 'vial_filler', 'lyophilizer', 'rabs', 'isolator',
                                   'transfer_line', 'hopper', 'scoop', 'container',
                                   name='equipmentcategoryenum', create_type=True)
    equipment_category_enum.create(op.get_bind(), checkfirst=True)
    
    # Create dosage_forms table
    op.create_table(
        'dosage_forms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.Enum('tablet', 'capsule', 'powder', 'granule', 'pellet',
                                  'oral_solution', 'oral_suspension', 'syrup', 'elixir', 'drops',
                                  'cream', 'ointment', 'gel', 'lotion', 'paste',
                                  'injectable', 'infusion', 'ophthalmic', 'otic', 'nasal', 'inhalation',
                                  'transdermal', 'suppository', 'vaccine',
                                  name='dosageformenum'), nullable=False),
        sa.Column('plant_type', sa.Enum('api_plant', 'formulation_osd', 'formulation_sterile',
                                        'formulation_liquid', 'formulation_ophthalmic', 'formulation_topical',
                                        'formulation_inhalation', 'biotech',
                                        name='planttypeenum'), nullable=False),
        sa.Column('requires_sterility', sa.Boolean(), nullable=True),
        sa.Column('requires_endotoxin_testing', sa.Boolean(), nullable=True),
        sa.Column('requires_particle_count', sa.Boolean(), nullable=True),
        sa.Column('requires_visual_inspection', sa.Boolean(), nullable=True),
        sa.Column('requires_microbiological_testing', sa.Boolean(), nullable=True),
        sa.Column('default_microbial_limit_cfu', sa.Float(), nullable=True),
        sa.Column('default_endotoxin_limit_eu_ml', sa.Float(), nullable=True),
        sa.Column('default_particle_limit', sa.Float(), nullable=True),
        sa.Column('recommended_sampling_method', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name')
    )
    
    # Create product_dosage_forms table
    op.create_table(
        'product_dosage_forms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('dosage_form_id', sa.Integer(), nullable=False),
        sa.Column('batch_quantity', sa.Float(), nullable=True),
        sa.Column('batch_unit', sa.String(), nullable=True),
        sa.Column('min_daily_dose', sa.Float(), nullable=True),
        sa.Column('max_daily_dose', sa.Float(), nullable=True),
        sa.Column('dose_unit', sa.String(), nullable=True),
        sa.Column('is_pediatric', sa.Boolean(), nullable=True),
        sa.Column('is_geriatric', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dosage_form_id'], ['dosage_forms.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create formulation_equipment table
    op.create_table(
        'formulation_equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('sifter', 'granulator', 'dryer', 'mill', 'blender',
                                      'tablet_press', 'coater', 'capsule_filler',
                                      'mixing_tank', 'storage_tank', 'filling_machine', 'capping_machine',
                                      'autoclave', 'laminar_airflow', 'vial_filler', 'lyophilizer', 'rabs', 'isolator',
                                      'transfer_line', 'hopper', 'scoop', 'container',
                                      name='equipmentcategoryenum'), nullable=False),
        sa.Column('contact_parts', sa.Text(), nullable=True),
        sa.Column('non_contact_parts', sa.Text(), nullable=True),
        sa.Column('hard_to_clean_locations', sa.Text(), nullable=True),
        sa.Column('has_cip', sa.Boolean(), nullable=True),
        sa.Column('has_sip', sa.Boolean(), nullable=True),
        sa.Column('cip_parameters', sa.Text(), nullable=True),
        sa.Column('sampling_points_count', sa.Integer(), nullable=True),
        sa.Column('worst_case_sampling_points', sa.Text(), nullable=True),
        sa.Column('is_validated_for_cleaning', sa.Boolean(), nullable=True),
        sa.Column('last_validation_date', sa.DateTime(), nullable=True),
        sa.Column('validation_due_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create sampling_locations table
    op.create_table(
        'sampling_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('location_name', sa.String(), nullable=False),
        sa.Column('location_description', sa.Text(), nullable=True),
        sa.Column('surface_area_cm2', sa.Float(), nullable=True),
        sa.Column('is_hard_to_clean', sa.Boolean(), nullable=True),
        sa.Column('is_worst_case', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('recommended_method', sa.Enum('swab', 'rinse', 'contact_plate', 'direct_inoculation', 'air_sampling',
                                                name='samplingmethodenum'), nullable=True),
        sa.Column('recovery_factor_percent', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create sampling_results table
    op.create_table(
        'sampling_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('sampling_method', sa.Enum('swab', 'rinse', 'contact_plate', 'direct_inoculation', 'air_sampling',
                                             name='samplingmethodenum'), nullable=False),
        sa.Column('sample_code', sa.String(), nullable=False),
        sa.Column('sampling_date', sa.DateTime(), nullable=False),
        sa.Column('sampled_by', sa.String(), nullable=False),
        sa.Column('swab_area_cm2', sa.Float(), nullable=True),
        sa.Column('rinse_volume_ml', sa.Float(), nullable=True),
        sa.Column('contact_plate_size_cm2', sa.Float(), nullable=True),
        sa.Column('dilution_factor', sa.Float(), nullable=True),
        sa.Column('absorbance_sample', sa.Float(), nullable=True),
        sa.Column('absorbance_std', sa.Float(), nullable=True),
        sa.Column('result_ppm', sa.Float(), nullable=True),
        sa.Column('result_ug_per_swab', sa.Float(), nullable=True),
        sa.Column('result_cfu_per_plate', sa.Float(), nullable=True),
        sa.Column('total_germ_count', sa.Float(), nullable=True),
        sa.Column('yeast_mold_count', sa.Float(), nullable=True),
        sa.Column('endotoxin_value', sa.Float(), nullable=True),
        sa.Column('is_acceptable', sa.Boolean(), nullable=True),
        sa.Column('reported_value', sa.String(), nullable=True),
        sa.Column('below_loq', sa.Boolean(), nullable=True),
        sa.Column('deviations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['sampling_locations.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['validation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_product_dosage_form_product', 'product_dosage_forms', ['product_id'])
    op.create_index('idx_product_dosage_form_dosage', 'product_dosage_forms', ['dosage_form_id'])
    op.create_index('idx_sampling_locations_equipment', 'sampling_locations', ['equipment_id'])
    op.create_index('idx_sampling_results_session', 'sampling_results', ['session_id'])
    op.create_index('idx_formulation_equipment_eq', 'formulation_equipment', ['equipment_id'])
    op.create_index('idx_formulation_equipment_category', 'formulation_equipment', ['category'])


def downgrade() -> None:
    op.drop_index('idx_formulation_equipment_category')
    op.drop_index('idx_formulation_equipment_eq')
    op.drop_index('idx_sampling_results_session')
    op.drop_index('idx_sampling_locations_equipment')
    op.drop_index('idx_product_dosage_form_dosage')
    op.drop_index('idx_product_dosage_form_product')
    
    op.drop_table('sampling_results')
    op.drop_table('sampling_locations')
    op.drop_table('formulation_equipment')
    op.drop_table('product_dosage_forms')
    op.drop_table('dosage_forms')
    
    # Drop ENUM types
    op.execute('DROP TYPE equipmentcategoryenum')
    op.execute('DROP TYPE samplingmethodenum')
    op.execute('DROP TYPE planttypeenum')
    op.execute('DROP TYPE dosageformenum')