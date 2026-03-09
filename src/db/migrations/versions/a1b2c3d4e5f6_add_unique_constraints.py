"""add_unique_constraints

Revision ID: a1b2c3d4e5f6
Revises: c4f9a0f42e45
Create Date: 2026-03-09 06:01:14

Adds unique constraints to prevent data duplication:
- sales_plans: (restaurant_id, date)
- stock_balances: (restaurant_id, product_id)
- product_mix: (restaurant_id, iiko_dish_id)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c4f9a0f42e45'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Deduplicate before adding constraints
    
    # 1. sales_plans: keep latest entry per (restaurant_id, date)
    op.execute("""
        DELETE FROM sales_plans a
        USING sales_plans b
        WHERE a.id < b.id
          AND a.restaurant_id = b.restaurant_id
          AND a.date = b.date
    """)
    
    op.create_unique_constraint(
        'uq_sales_plans_restaurant_date',
        'sales_plans',
        ['restaurant_id', 'date']
    )
    
    # 2. stock_balances: keep latest entry per (restaurant_id, product_id)
    op.execute("""
        DELETE FROM stock_balances a
        USING stock_balances b
        WHERE a.id < b.id
          AND a.restaurant_id = b.restaurant_id
          AND a.product_id = b.product_id
    """)
    
    op.create_unique_constraint(
        'uq_stock_balances_restaurant_product',
        'stock_balances',
        ['restaurant_id', 'product_id']
    )
    
    # 3. product_mix: keep latest entry per (restaurant_id, iiko_dish_id)
    op.execute("""
        DELETE FROM product_mix a
        USING product_mix b
        WHERE a.id < b.id
          AND a.restaurant_id = b.restaurant_id
          AND a.iiko_dish_id = b.iiko_dish_id
    """)
    
    op.create_unique_constraint(
        'uq_product_mix_restaurant_dish',
        'product_mix',
        ['restaurant_id', 'iiko_dish_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_product_mix_restaurant_dish', 'product_mix', type_='unique')
    op.drop_constraint('uq_stock_balances_restaurant_product', 'stock_balances', type_='unique')
    op.drop_constraint('uq_sales_plans_restaurant_date', 'sales_plans', type_='unique')
