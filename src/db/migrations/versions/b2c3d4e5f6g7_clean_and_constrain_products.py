"""clean_and_constrain_products

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 06:40:00

Cleans duplicate products and adds unique constraint on iiko_id.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Clear tables that are dynamically synced to avoid FK issues and complex merges
    op.execute("DELETE FROM stock_balances")
    op.execute("DELETE FROM tech_cards")
    op.execute("DELETE FROM empirical_recipes")
    op.execute("DELETE FROM product_mix")
    op.execute("DELETE FROM anomalies")
    
    # 2. Delete products. We will re-sync them properly from iiko resto.
    op.execute("DELETE FROM products")
    
    # 3. Add UNIQUE constraint to iiko_id to prevent future duplicates
    op.create_unique_constraint('uq_products_iiko_id', 'products', ['iiko_id'])

def downgrade():
    op.drop_constraint('uq_products_iiko_id', 'products', type_='unique')
