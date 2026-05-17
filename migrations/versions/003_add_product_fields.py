# migrations/versions/003_add_product_fields.py

"""add_product_fields

Revision ID: 003
Revises: 002
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to products table
    op.add_column('products', sa.Column('product_code', sa.String(), nullable=True))
    op.add_column('products', sa.Column('toxicity_class', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('products', sa.Column('potency_class', sa.Integer(), nullable=True, server_default='3'))
    op.add_column('products', sa.Column('cleanability_rating', sa.Integer(), nullable=True, server_default='2'))
    
    # Create indexes
    op.create_index('idx_products_product_code', 'products', ['product_code'])
    op.create_index('idx_products_plant_code', 'products', ['plant', 'product_code'])
    op.create_index('idx_products_toxicity', 'products', ['toxicity_class'])
    
    # Update existing products with default product_code from name
    op.execute("""
        UPDATE products 
        SET product_code = UPPER(SUBSTRING(name, 1, 6)) 
        WHERE product_code IS NULL
    """)


def downgrade() -> None:
    op.drop_index('idx_products_toxicity')
    op.drop_index('idx_products_plant_code')
    op.drop_index('idx_products_product_code')
    op.drop_column('products', 'cleanability_rating')
    op.drop_column('products', 'potency_class')
    op.drop_column('products', 'toxicity_class')
    op.drop_column('products', 'product_code')